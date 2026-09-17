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
"""

from __future__ import annotations

import logging
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
_DESC_KEYS = ("objective", "description", "topicObjective", "shortDescription")
_ID_KEYS = ("topicId", "id", "noticeId")


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

    def fetch(self) -> Iterable[Opportunity]:
        payload = None
        failures: list[str] = []
        for method, url, body in CANDIDATES:
            try:
                payload = (post_json(url, body, retries=1, timeout=20) if method == "POST"
                           else fetch_json(url, retries=1, timeout=20))
                if _rows(payload):
                    log.info("dod_sbir: %s %s answered with %d records",
                             method, url, len(_rows(payload)))
                    break
                failures.append(f"{url}: returned no recognisable topic list")
                payload = None
            except Exception as exc:  # noqa: BLE001 - try the next candidate
                failures.append(str(exc))
        if payload is None:
            raise SourceError("; ".join(failures))

        for record in _rows(payload):
            title = strip_html(first_key(record, _TITLE_KEYS))
            if not title:
                continue
            code = first_key(record, _CODE_KEYS)
            topic_id = first_key(record, _ID_KEYS)
            url = (f"https://www.dodsbirsttr.mil/topics-app/?topicId={topic_id}"
                   if topic_id else "https://www.dodsbirsttr.mil/topics-app/")
            component = strip_html(first_key(record, _COMPONENT_KEYS))

            yield Opportunity(
                source="dod-sbir",
                name=f"{title} ({code})" if code else title,
                url=url,
                agency=f"DoD — {component}" if component else "Department of Defense",
                amount=self.options.get("default_amount", "SBIR Phase I scale"),
                summary=strip_html(first_key(record, _DESC_KEYS))[:400],
                open_date=parse_date(first_key(record, _OPEN_KEYS)),
                close_date=parse_date(first_key(record, _CLOSE_KEYS)),
                pillar=2,
                kind="grant",
                eligibility="Small businesses; US-owned and independently operated",
                raw=record,
            )
