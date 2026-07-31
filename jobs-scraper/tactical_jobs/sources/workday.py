"""Workday adapter -- the single biggest pool of tactical human performance jobs.

Nearly every defense prime holding an Army H2F, SOCOM POTFF, or USASOC THOR3
contract recruits on Workday: Leidos, Booz Allen, Amentum, KBR, CACI, SAIC,
Parsons. Without this adapter the scraper misses most of the market.

A Workday career site is a React front end talking to a JSON API on the same
host. This adapter calls exactly the endpoints that front end calls, with the
same payload shape it sends:

    POST https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs
         {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": "..."}
    GET  https://{tenant}.{dc}.myworkdayjobs.com/wday/cxs/{tenant}/{site}{externalPath}

The search response is title-and-location only. Everything this project exists
to mine -- certifications (CSCS, TSAC-F, ATC, RD), clearance level,
installation, salary language -- lives in the detail response's
``jobDescription``, so every unique posting gets a second request. That
fan-out is bounded by ``detail_limit``, and a detail request that fails
downgrades the posting to its list-level fields instead of dropping it.

Tenants run in different Workday data centers (``wd1``, ``wd3``, ``wd5``...).
The value is visible in the careers-page hostname; ``data_center`` sets it.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any, Iterable

from ..http import FetchError, fetch_json, post_json
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

log = logging.getLogger(__name__)

DEFAULT_SEARCH_TERMS = (
    "human performance",
    "strength and conditioning",
    "athletic trainer",
    "physical therapist",
    "performance dietitian",
    "cognitive performance",
    "holistic health and fitness",
)
"""Server-side keyword filter.

A prime like Leidos lists thousands of openings, the overwhelming majority of
them engineering. Pulling the whole board to throw away 99% of it is rude to
the host and slow for us, so these queries cast a wide net server-side and the
local classifier does the precision work. Set ``search_terms = []`` to pull an
entire (small) board unfiltered instead.
"""


def _descriptor(value: Any) -> str:
    """Flatten the several shapes Workday uses for one scalar field.

    The same logical field arrives as a bare string, as ``{"descriptor": ...}``,
    or as a list of either, depending on tenant and endpoint. Normalizing once
    here keeps that mess out of the mapping code.
    """
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("descriptor", "name", "label", "value", "text", "title"):
            inner = value.get(key)
            if isinstance(inner, str) and inner.strip():
                return inner.strip()
        return ""
    if isinstance(value, (list, tuple)):
        parts = [_descriptor(item) for item in value]
        return ", ".join(part for part in parts if part)
    return ""


def _external_path(record: Any) -> str | None:
    """The posting's path within the site, normalized to a leading slash.

    This is both the detail-endpoint key and the dedupe key. A record without
    one has no stable identity and no reachable URL, so it is not salvageable.
    """
    if not isinstance(record, dict):
        return None
    path = _descriptor(record.get("externalPath"))
    if not path:
        return None
    return path if path.startswith("/") else f"/{path}"


def _decode(body: Any) -> dict[str, Any]:
    """Parse a search response body.

    ``http.post_json`` returns the raw bytes rather than parsed JSON, so the
    decoding happens here. An already-parsed mapping is passed through so the
    helper stays honest about what it received.
    """
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", "replace")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError as exc:
            raise FetchError(f"workday search returned non-JSON body: {exc}") from exc
    return body if isinstance(body, dict) else {}


def _location(listing: dict[str, Any], info: dict[str, Any]) -> str:
    """Prefer the detail location; the list only has a display string.

    ``locationsText`` collapses multi-site reqs to things like "2 Locations",
    which is useless for a location filter. The detail endpoint names them.
    """
    candidates: list[Any] = [info.get("location")]
    extra = info.get("additionalLocations")
    if isinstance(extra, (list, tuple)):
        candidates.extend(extra)

    names: list[str] = []
    for candidate in candidates:
        text = _descriptor(candidate)
        if text and text not in names:
            names.append(text)
    if names:
        return "; ".join(names)
    return _descriptor(listing.get("locationsText"))


def _posted_at(listing: dict[str, Any], info: dict[str, Any]):
    """First parseable timestamp wins.

    ``postedOn`` is rendered for humans ("Posted 30+ Days Ago") and almost
    never parses, so the detail record's ``startDate`` is tried first.
    """
    for value in (
        info.get("startDate"),
        info.get("postedOnDate"),
        info.get("postedOn"),
        listing.get("postedOn"),
    ):
        if isinstance(value, bool):
            continue
        stamp = parse_timestamp(value)
        if stamp is not None:
            return stamp
    return None


def _department(info: dict[str, Any]) -> str:
    for key in (
        "jobFamilyGroup",
        "jobFamily",
        "jobCategory",
        "supervisoryOrganization",
        "department",
    ):
        text = _descriptor(info.get(key))
        if text:
            return text
    return ""


def _compensation(info: dict[str, Any]) -> str:
    """Pull a pay range when the tenant publishes one as structured data.

    Pay-transparency states force this field into the API for a growing share
    of postings; where it is absent the enrichment layer still mines the
    description text.
    """
    for key in ("payRangeText", "compensation", "salaryRange"):
        text = _descriptor(info.get(key))
        if text:
            return text

    pay = info.get("payRange")
    if not isinstance(pay, dict):
        return ""
    low = next(
        (_descriptor(pay.get(k)) for k in ("minimum", "min", "start") if _descriptor(pay.get(k))),
        "",
    )
    high = next(
        (_descriptor(pay.get(k)) for k in ("maximum", "max", "end") if _descriptor(pay.get(k))),
        "",
    )
    frequency = next(
        (
            _descriptor(pay.get(k))
            for k in ("frequency", "frequencyLabel", "rateFrequency")
            if _descriptor(pay.get(k))
        ),
        "",
    )
    if low and high:
        return f"{low} - {high} {frequency}".strip()
    return (low or high or "").strip()


def _list_summary(listing: dict[str, Any]) -> str:
    """Fallback description built from list-level fields only.

    Used when the detail request fails or is over budget. Thin, but a title
    plus location plus the bullet fields is enough for the review queue to
    decide whether a human should open the link.
    """
    parts = [_descriptor(listing.get("title")), _descriptor(listing.get("locationsText"))]
    bullets = listing.get("bulletFields")
    if isinstance(bullets, (list, tuple)):
        parts.extend(_descriptor(bullet) for bullet in bullets)
    return html_to_text(" ".join(part for part in parts if part))


class WorkdaySource(Source):
    """One Workday career site (a tenant plus a site slug).

    ``tenant`` and ``site`` come straight out of the careers URL:
    ``https://leidos.wd5.myworkdayjobs.com/External`` is tenant ``leidos``,
    data center ``wd5``, site ``External``.
    """

    kind = "workday"

    def fetch(self) -> Iterable[JobPosting]:
        tenant = str(self.require("tenant")).strip().strip("/")
        site = str(self.require("site")).strip().strip("/")
        data_center = str(self.options.get("data_center") or "wd1").strip().strip(".")
        employer = self.options.get("employer") or tenant
        limit = max(1, int(self.options.get("limit", 20)))
        max_pages = max(1, int(self.options.get("max_pages", 5)))
        detail_limit = int(self.options.get("detail_limit", 50))
        delay = float(self.options.get("delay_seconds", 0.0))

        base_url = f"https://{tenant}.{data_center}.myworkdayjobs.com"
        api_url = f"{base_url}/wday/cxs/{tenant}/{site}"

        listings = self._collect(api_url, self._search_terms(), limit, max_pages, delay)

        for index, (path, listing) in enumerate(listings.items()):
            info: dict[str, Any] = {}
            if index < detail_limit:
                if delay:
                    time.sleep(delay)
                info = self._detail(f"{api_url}{path}")
            try:
                yield self._to_posting(
                    path, listing, info, employer=employer, base_url=base_url, site=site
                )
            except Exception as exc:  # pragma: no cover - defensive
                # One unusable record must never cost us the rest of the board.
                log.warning("skipping malformed workday posting %s: %s", path, exc)

    def _search_terms(self) -> list[str]:
        """Configured search terms, with an explicit empty list meaning "all".

        ``search_terms = []`` is a deliberate instruction to pull the board
        unfiltered, so it must not silently fall back to the defaults.
        """
        configured = self.options.get("search_terms")
        if configured is None:
            return list(DEFAULT_SEARCH_TERMS)
        if isinstance(configured, str):
            return [configured]
        terms = [str(term) for term in configured]
        return terms or [""]

    def _collect(
        self,
        api_url: str,
        terms: list[str],
        limit: int,
        max_pages: int,
        delay: float,
    ) -> dict[str, dict[str, Any]]:
        """Run every search term and dedupe by ``externalPath``.

        Overlapping terms are the norm -- "human performance" and "strength and
        conditioning" both hit the same H2F req -- and each duplicate would
        otherwise cost an extra detail request. Insertion order is preserved so
        the detail budget is spent on the earliest, most relevant terms.
        """
        listings: dict[str, dict[str, Any]] = {}
        first_request = True

        for term in terms:
            offset = 0
            for _ in range(max_pages):
                if delay and not first_request:
                    time.sleep(delay)
                try:
                    payload = self._search(f"{api_url}/jobs", term, offset, limit)
                except Exception as exc:
                    # A board that is unreachable on the very first request is a
                    # broken config, not a flaky page: report it rather than
                    # returning zero jobs and calling that success.
                    if first_request:
                        raise
                    log.warning(
                        "workday search failed for %r at offset %d: %s", term, offset, exc
                    )
                    break
                finally:
                    first_request = False

                records = payload.get("jobPostings")
                if not isinstance(records, list) or not records:
                    break

                for record in records:
                    path = _external_path(record)
                    if path is None:
                        log.debug("skipping workday record without externalPath: %r", record)
                        continue
                    listings.setdefault(path, record)

                offset += limit
                total = payload.get("total")
                if isinstance(total, (int, float)) and not isinstance(total, bool):
                    if offset >= total:
                        break
                if len(records) < limit:
                    break

        return listings

    def _search(self, url: str, term: str, offset: int, limit: int) -> dict[str, Any]:
        body = post_json(
            url,
            {"appliedFacets": {}, "limit": limit, "offset": offset, "searchText": term},
            headers={"Accept": "application/json"},
        )
        return _decode(body)

    def _detail(self, url: str) -> dict[str, Any]:
        """Fetch one posting's detail record, or ``{}`` if it is unavailable."""
        try:
            payload = fetch_json(url, headers={"Accept": "application/json"})
        except Exception as exc:
            log.debug("workday detail fetch failed for %s: %s", url, exc)
            return {}
        if not isinstance(payload, dict):
            return {}
        info = payload.get("jobPostingInfo")
        return info if isinstance(info, dict) else {}

    def _to_posting(
        self,
        path: str,
        listing: dict[str, Any],
        info: dict[str, Any],
        *,
        employer: str,
        base_url: str,
        site: str,
    ) -> JobPosting:
        title = _descriptor(listing.get("title")) or _descriptor(info.get("title"))
        location = _location(listing, info)
        remote_type = _descriptor(info.get("remoteType"))
        req_id = _descriptor(info.get("jobReqId"))

        description = html_to_text(info.get("jobDescription"))
        if not description:
            description = _list_summary(listing)

        # Fold the structured facts into the text as well, so classification
        # and enrichment see them without special-casing this source's schema.
        facts = [
            f"{label} {value}."
            for label, value in (
                ("Job requisition id:", req_id),
                ("Time type:", _descriptor(info.get("timeType"))),
                ("Remote type:", remote_type),
            )
            if value
        ]
        if facts:
            description = f"{description}\n\n{' '.join(facts)}".strip()

        raw: dict[str, Any] = {"jobPosting": listing}
        if info:
            raw["jobPostingInfo"] = info

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            # jobReqId is what recruiters, the employer's own site, and any
            # syndicated copy all use; the path is only a fallback identity.
            source_id=req_id or path,
            # The human-facing URL, never the /wday/cxs API path.
            url=f"{base_url}/{site}{path}",
            title=title,
            employer=employer,
            location=location,
            description=description,
            posted_at=_posted_at(listing, info),
            remote=looks_remote(location, remote_type, _descriptor(listing.get("locationsText"))),
            department=_department(info) or None,
            compensation=_compensation(info) or None,
            raw=raw,
        )


WORKDAY_SOURCES: tuple[type[Source], ...] = (WorkdaySource,)
