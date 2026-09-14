"""Grants.gov search2 -- every federal grant posting, keyword-filtered.

WHY THIS SOURCE
SBIR.gov covers the SBIR/STTR programs. Grants.gov covers everything else the
federal government posts: ARPA-H solicitations, NIH notices outside the SBIR
omnibus, NSF programs, DoD BAAs. Between the two, the federal layer of the
board maintains itself.

API: POST https://api.grants.gov/v1/api/search2
Open, no key, no account. Documented at https://www.grants.gov/api

FIELD NAMES: DOCUMENTED VS DEFENSIVE
``title``, ``number``, ``agency``, ``closeDate``, ``openDate``, ``id`` are the
documented keys on ``data.oppHits[]``. The ``_*_KEYS`` alternates are
defensive, for the same asymmetric-cost reason documented in sbir_gov.py, and
are NOT confirmed responses.

CLOSED OPPORTUNITIES ARE REQUESTED ON PURPOSE
``oppStatuses`` includes "closed" so the board can show a just-closed program
as closed-with-a-date rather than having it vanish. A program that silently
disappears looks like it was never found; one shown as closed tells you to
watch for the next cycle.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from ..http import post_json
from ..models import Opportunity, parse_date
from .base import Source, first_key, strip_html

log = logging.getLogger(__name__)

ENDPOINT = "https://api.grants.gov/v1/api/search2"
# search2 returns titles and dates and nothing else -- every federal row on the
# board came through with no description, no eligibility and "see solicitation"
# for the amount, including the one closing soonest. fetchOpportunity is the
# public, keyless detail call that carries the synopsis, the award floor and
# ceiling, and the applicant types.
DETAIL_ENDPOINT = "https://api.grants.gov/v1/api/fetchOpportunity"

_SYNOPSIS_KEYS = ("synopsis", "synopsisDesc", "description", "opportunityDesc")
_CEILING_KEYS = ("awardCeiling", "award_ceiling")
_FLOOR_KEYS = ("awardFloor", "award_floor")
_APPLICANT_KEYS = ("applicantTypes", "applicant_types", "eligibility")

_TITLE_KEYS = ("title", "opportunityTitle", "oppTitle")
_NUMBER_KEYS = ("number", "opportunityNumber", "oppNumber")
_AGENCY_KEYS = ("agency", "agencyName", "agencyCode", "topAgencyCode")
_CLOSE_KEYS = ("closeDate", "closeDateStr", "archiveDate")
_OPEN_KEYS = ("openDate", "postedDate", "openDateStr")
_ID_KEYS = ("id", "opportunityId", "oppId")


class GrantsGovSource(Source):
    """Federal grant opportunities matching a keyword set."""

    kind = "grants_gov"

    def _page(self, keyword: str, rows: int, statuses: str, start: int) -> list[dict]:
        """One page of hits, or [] if the shape is not what we expect."""
        body: dict[str, Any] = {
            "keyword": keyword,
            "rows": rows,
            "oppStatuses": statuses,
            "startRecordNum": start,
        }
        # Vybe is a for-profit small business. Without this filter the board
        # fills with programs restricted to universities and 501(c)(3)s -- rows
        # that read as opportunities but that Vybe cannot legally win, which is
        # a worse failure than a short board. "22" is grants.gov's for-profit
        # eligibility code; leave it unset to search every applicant type.
        eligibilities = self.options.get("eligibilities")
        if eligibilities:
            body["eligibilities"] = str(eligibilities)
        agencies = self.options.get("agencies")
        if agencies:
            body["agencies"] = str(agencies)

        payload = post_json(ENDPOINT, body)
        data = payload.get("data") if isinstance(payload, dict) else None
        hits = (data or {}).get("oppHits", []) if isinstance(data, dict) else []
        if not isinstance(hits, list):
            log.warning("grants.gov returned an unexpected shape for %r", keyword)
            return []
        return [h for h in hits if isinstance(h, dict)]

    def fetch(self) -> Iterable[Opportunity]:
        keyword = self.require("keyword")
        # The API caps a page at 100. One page of 40 was leaving whole pages of
        # real solicitations unread -- the board was short because it never
        # asked, not because the opportunities were not there.
        rows = min(int(self.options.get("rows", 100)), 100)
        statuses = self.options.get("statuses", "forecasted|posted")
        max_pages = int(self.options.get("pages", 3))

        records: list[dict] = []
        seen_ids: set[str] = set()
        for page in range(max_pages):
            hits = self._page(keyword, rows, statuses, page * rows)
            if not hits:
                break
            # Stop on a page that adds nothing new: some queries repeat the
            # last page forever rather than returning empty.
            fresh = [h for h in hits if first_key(h, _ID_KEYS) not in seen_ids]
            if not fresh:
                break
            seen_ids.update(first_key(h, _ID_KEYS) for h in fresh)
            records.extend(fresh)
            if len(hits) < rows:
                break

        for record in records:
            if not isinstance(record, dict):
                continue
            # Titles arrive HTML-escaped ("Alzheimer&rsquo;s"). The dashboard
            # escapes everything it renders, so an entity left in here reaches
            # the page as the literal text "&rsquo;". Decode at the boundary,
            # the same treatment the summary already gets.
            title = strip_html(first_key(record, _TITLE_KEYS))
            if not title:
                continue

            opp_id = first_key(record, _ID_KEYS)
            number = first_key(record, _NUMBER_KEYS)
            url = (
                f"https://www.grants.gov/search-results-detail/{opp_id}"
                if opp_id
                else "https://www.grants.gov/search-grants"
            )

            yield Opportunity(
                source="grants.gov",
                name=f"{title} ({number})" if number else title,
                url=url,
                agency=strip_html(first_key(record, _AGENCY_KEYS)),
                amount=self.options.get("default_amount", "see solicitation"),
                summary=strip_html(first_key(record, ("description", "synopsis")))[:400],
                open_date=parse_date(first_key(record, _OPEN_KEYS)),
                close_date=parse_date(first_key(record, _CLOSE_KEYS)),
                pillar=2,
                kind="grant",
                eligibility=self.options.get("eligibility", ""),
                raw=record,
            )

    def enrich(self, opportunity: Opportunity) -> None:
        """Pull the synopsis, award range and applicant types for one row.

        Every field is filled only when it is currently empty, so a curated
        value is never overwritten by an API one. A detail call that fails
        leaves the row exactly as the search returned it -- a thinner row is a
        far better outcome than a dead sweep.
        """
        opp_id = (opportunity.raw or {}).get("id") or first_key(
            opportunity.raw or {}, _ID_KEYS
        )
        if not opp_id:
            return

        # One attempt, short timeout. Detail is optional and this runs once per
        # row on the board, so the default three retries with linear backoff
        # turn one slow endpoint into minutes of dead sweep -- the cost of a
        # miss here is a thinner row, which is not worth waiting for.
        payload = post_json(
            DETAIL_ENDPOINT,
            {"opportunityId": str(opp_id)},
            retries=1,
            timeout=6,
        )
        data = payload.get("data") if isinstance(payload, dict) else None
        if not isinstance(data, dict):
            return
        # The detail body nests most of what we want under a synopsis object.
        synopsis = data.get("synopsis") if isinstance(data.get("synopsis"), dict) else {}
        merged: dict[str, Any] = {**data, **synopsis}

        if not opportunity.summary:
            text = strip_html(first_key(merged, _SYNOPSIS_KEYS))
            if text:
                opportunity.summary = text[:400]

        if not opportunity.eligibility:
            applicants = merged.get("applicantTypes")
            if isinstance(applicants, list):
                names = [
                    strip_html(a.get("description") or a.get("name") or "")
                    if isinstance(a, dict)
                    else strip_html(a)
                    for a in applicants
                ]
                joined = "; ".join(n for n in names if n)
                if joined:
                    opportunity.eligibility = joined[:300]
            else:
                text = strip_html(first_key(merged, _APPLICANT_KEYS))
                if text:
                    opportunity.eligibility = text[:300]

        if opportunity.amount in ("", "see solicitation"):
            ceiling = first_key(merged, _CEILING_KEYS)
            floor = first_key(merged, _FLOOR_KEYS)

            def _money(value: str) -> str:
                try:
                    return f"${int(float(value)):,}"
                except (TypeError, ValueError):
                    return ""

            hi, lo = _money(ceiling), _money(floor)
            if hi and lo and hi != lo:
                opportunity.amount = f"{lo} - {hi}"
            elif hi:
                opportunity.amount = f"up to {hi}"
            elif lo:
                opportunity.amount = f"from {lo}"
