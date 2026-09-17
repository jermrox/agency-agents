"""DoD SBIR/STTR topics from the DSIP portal.

WHY THIS SOURCE EXISTS
DoD SBIR and STTR topics are not posted to grants.gov, and SBIR.gov -- the one
documented aggregator that carries them -- has been refusing every request since
the programs' 2025-26 authorization lapse. That leaves the single most relevant
federal layer for a warfighter-facing wearable completely invisible to this
board: DARPA, Army, Navy, Air Force and DHA topics, none of which show up in any
other source configured here.

WHY THE ENDPOINTS ARE GUESSES
The DSIP topics app at dodsbirsttr.mil/topics-app is a single-page application,
so a backend serves it JSON, but that backend is not publicly documented. The
candidates below are the conventional shapes for such an app. Each costs one
request on the failure path and the source fails loudly naming every one it
tried, which is what a future fix starts from. Nothing here can put a wrong row
on the board -- a shape we do not recognise yields zero opportunities, not junk.

THE SCHEMA, READ OFF A LIVE RESPONSE
The first live run returned records keyed:

    topicId topicCode topicTitle topicStatus component command program
    cycleName solicitationNumber solicitationTitle releaseNumber
    topicStartDate topicEndDate topicPreReleaseStartDate topicPreReleaseEndDate
    topicQAStartDate topicQAEndDate topicQAStatus ...

Two things follow, and both cost a release to learn:

1. The dates are epoch milliseconds, not strings. ``parse_date`` reads text
   formats, so every close date came back None and every topic rendered as
   "Rolling" -- an expired topic sitting on the board looking open, which is
   the failure this board exists to prevent. ``_epoch_date`` below handles it.

2. There is no description, objective or abstract field anywhere in the search
   response; the full topic text lives behind a per-topic detail page. So the
   summary here is assembled from what the record actually carries rather than
   left empty, and no text is invented.

A row with no close date is dropped outright. For this source that is not a
"rolling" opportunity -- DoD topics always close -- it means the date did not
parse, and a row we cannot date is a row we cannot honestly publish.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Iterable

from ..http import fetch_json, post_json
from ..models import Opportunity, parse_date
from .base import Source, SourceError, first_key, strip_html

log = logging.getLogger(__name__)

# (method, url, body) -- body is None for GET.
CANDIDATES: tuple[tuple[str, str, dict[str, Any] | None], ...] = (
    ("POST", "https://www.dodsbirsttr.mil/topics/api/public/topics/search",
     {"searchParam": {"searchText": None, "components": None, "programYear": None,
                      "solicitationCycleNames": ["openTopics"], "releaseNumbers": [],
                      "topicReleaseStatus": [591], "modernizationPriorities": [],
                      "sortBy": "finalTopicCode,asc", "technologyAreaIds": [],
                      "component": None, "program": None}, "size": 100, "page": 0}),
    ("GET", "https://www.dodsbirsttr.mil/topics/api/public/topics/search?size=100&page=0", None),
    ("GET", "https://www.dodsbirsttr.mil/topics/api/public/topics", None),
)

_TITLE_KEYS = ("topicTitle", "title", "finalTopicTitle")
_CODE_KEYS = ("topicCode", "finalTopicCode", "topicNumber", "number")
_COMPONENT_KEYS = ("component", "componentName", "agency", "command")
_CLOSE_KEYS = ("topicEndDate", "closeDate", "endDate", "topicCloseDate")
_OPEN_KEYS = ("topicStartDate", "openDate", "startDate", "topicOpenDate")
_ID_KEYS = ("topicId", "id", "noticeId")
_STATUS_KEYS = ("topicStatus", "status")
_PROGRAM_KEYS = ("program",)
_CYCLE_KEYS = ("cycleName", "solicitationTitle", "solicitationNumber")

# Statuses that mean "you can still act on this". Anything else -- Closed,
# Archived, a status we have never seen -- is dropped, because the safe default
# for an unrecognised status is to leave the row off the board rather than
# guess it is live.
_ACTIONABLE_STATUSES = ("open", "pre-release", "prerelease")


def _epoch_date(value: Any):
    """Parse a DSIP timestamp: epoch milliseconds, seconds, or a date string.

    Kept local rather than folded into ``parse_date`` because a bare number is
    ambiguous in general -- ``20250131`` is a plausible date string and a
    plausible epoch second. Here the field is known to be a Java timestamp, so
    the ambiguity does not exist and the narrow reading is the correct one.
    """
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        return None
    number: float | None = None
    if isinstance(value, (int, float)):
        number = float(value)
    elif isinstance(value, str) and value.strip().lstrip("-").isdigit():
        number = float(value.strip())
    if number is not None:
        # Milliseconds past ~2001; seconds past ~2001. Below that it is not a
        # timestamp we should be guessing at.
        if abs(number) >= 1e11:
            number /= 1000.0
        elif abs(number) < 1e8:
            return None
        try:
            return datetime.fromtimestamp(number, tz=timezone.utc).date()
        except (OverflowError, OSError, ValueError):
            return None
    return parse_date(value)


def _record_id(record: dict) -> str:
    """Identity for cross-page dedup, falling back to the title."""
    return str(record.get("topicId") or record.get("topicCode")
               or record.get("topicTitle") or id(record))


def _rows(payload: Any) -> list[dict]:
    """Pull the record list out of whatever envelope the API uses."""
    if isinstance(payload, list):
        return [r for r in payload if isinstance(r, dict)]
    if not isinstance(payload, dict):
        return []
    for key in ("data", "content", "topics", "results", "items", "_embedded"):
        value = payload.get(key)
        if isinstance(value, list):
            return [r for r in value if isinstance(r, dict)]
        if isinstance(value, dict):
            nested = _rows(value)
            if nested:
                return nested
    return []


class DodSbirSource(Source):
    """Open DoD SBIR/STTR topics."""

    kind = "dod_sbir"

    def _records(self) -> list[dict]:
        """Every topic record the portal will give us.

        The filtered POST returns HTTP 500 -- the body shape it wants is not
        something we can guess, and a 500 is the server rejecting us, not a
        transient fault. The plain GET works and honours `size` and `page`, so
        the open topics are found by walking the whole list and filtering on
        the `topicStatus` each record carries. That is more requests, but it
        relies only on behaviour that has actually been observed.
        """
        working: tuple[str, str, dict | None] | None = None
        failures: list[str] = []

        for method, url, body in CANDIDATES:
            try:
                payload = (post_json(url, body, retries=1, timeout=20) if method == "POST"
                           else fetch_json(url, retries=1, timeout=20))
                rows = _rows(payload)
                if rows:
                    log.info("dod_sbir: %s %s answered with %d records",
                             method, url, len(rows))
                    working = (method, url, body)
                    break
                failures.append(f"{url}: returned no recognisable topic list")
                log.info("dod_sbir: %s %s returned no recognisable topic list", method, url)
            except Exception as exc:  # noqa: BLE001 - try the next candidate
                failures.append(str(exc))
                # Logged as it happens, not only when every candidate fails.
                # The first live run fell through to the unfiltered GET and the
                # reason the filtered POST was rejected never appeared anywhere
                # -- so the board silently showed page 0 of a closed-topic list
                # instead of the open topics the POST asks for.
                log.info("dod_sbir: %s %s failed: %s", method, url, exc)

        if working is None:
            raise SourceError("; ".join(failures))

        method, url, body = working
        records: list[dict] = list(rows)
        if method != "GET" or "page=0" not in url:
            return records

        # Walk the rest. Stop on a short page, a page that adds nothing new, or
        # the page budget -- the same three stopping conditions the grants.gov
        # source uses, so a change upstream cannot turn this into a long loop.
        seen = {_record_id(r) for r in records}
        max_pages = int(self.options.get("pages", 40))
        for page in range(1, max_pages):
            try:
                payload = fetch_json(url.replace("page=0", f"page={page}"),
                                     retries=1, timeout=20)
            except Exception as exc:  # noqa: BLE001 - keep what we already have
                log.warning("dod_sbir: page %d failed, keeping %d records: %s",
                            page, len(records), exc)
                break
            rows = _rows(payload)
            if not rows:
                break
            fresh = [r for r in rows if _record_id(r) not in seen]
            if not fresh:
                break
            seen.update(_record_id(r) for r in fresh)
            records.extend(fresh)
            if len(rows) < 100:
                break

        log.info("dod_sbir: %d topic records across %d page(s)",
                 len(records), 1 + (len(records) - 1) // 100 if records else 0)
        return records

    def fetch(self) -> Iterable[Opportunity]:
        records = self._records()

        statuses: dict[str, int] = {}
        undated = 0
        not_actionable = 0

        for record in records:
            title = strip_html(first_key(record, _TITLE_KEYS))
            if not title:
                continue

            status = first_key(record, _STATUS_KEYS)
            statuses[status or "(none)"] = statuses.get(status or "(none)", 0) + 1
            if status and not any(s in status.lower() for s in _ACTIONABLE_STATUSES):
                not_actionable += 1
                continue

            close_date = _epoch_date(record.get("topicEndDate")) or _epoch_date(
                first_key(record, _CLOSE_KEYS))
            if close_date is None:
                # Not "rolling". DoD topics always close, so a missing close
                # date means the field did not parse, and an undated row would
                # render as permanently open. Drop it and say how many.
                undated += 1
                continue

            code = first_key(record, _CODE_KEYS)
            topic_id = first_key(record, _ID_KEYS)
            url = (f"https://www.dodsbirsttr.mil/topics-app/?topicId={topic_id}"
                   if topic_id else "https://www.dodsbirsttr.mil/topics-app/")
            component = strip_html(first_key(record, _COMPONENT_KEYS))

            # The search response carries no description field, so the summary
            # is assembled from what the record actually holds. Nothing here is
            # invented: every part is a value the API returned.
            parts = [
                p for p in (
                    first_key(record, _PROGRAM_KEYS),
                    strip_html(first_key(record, _CYCLE_KEYS)),
                    f"status {status}" if status else "",
                ) if p
            ]
            summary = " · ".join(parts)
            if summary:
                summary += ". Full topic text is on the DSIP topic page."

            yield Opportunity(
                source="dod-sbir",
                name=f"{title} ({code})" if code else title,
                url=url,
                agency=f"DoD — {component}" if component else "Department of Defense",
                amount=self.options.get("default_amount", "SBIR Phase I scale"),
                summary=summary[:400],
                open_date=_epoch_date(record.get("topicStartDate")) or _epoch_date(
                    first_key(record, _OPEN_KEYS)),
                close_date=close_date,
                pillar=2,
                kind="grant",
                eligibility="Small businesses; US-owned and independently operated",
                documents=["SAM.gov UEI", "SBIR.gov SBC control number"],
                raw=record,
            )

        # A silent filter is indistinguishable from a dead API, so say what was
        # dropped and on what grounds.
        log.info("dod_sbir: statuses seen: %s",
                 ", ".join(f"{k}={v}" for k, v in sorted(statuses.items())))
        if not_actionable:
            log.info("dod_sbir: %d dropped as not open or pre-release", not_actionable)
        if undated:
            log.warning("dod_sbir: %d dropped with an unparseable close date", undated)
