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
from typing import Iterable

from ..http import post_json
from ..models import Opportunity, parse_date
from .base import Source, first_key, strip_html

log = logging.getLogger(__name__)

ENDPOINT = "https://api.grants.gov/v1/api/search2"

_TITLE_KEYS = ("title", "opportunityTitle", "oppTitle")
_NUMBER_KEYS = ("number", "opportunityNumber", "oppNumber")
_AGENCY_KEYS = ("agency", "agencyName", "agencyCode", "topAgencyCode")
_CLOSE_KEYS = ("closeDate", "closeDateStr", "archiveDate")
_OPEN_KEYS = ("openDate", "postedDate", "openDateStr")
_ID_KEYS = ("id", "opportunityId", "oppId")


class GrantsGovSource(Source):
    """Federal grant opportunities matching a keyword set."""

    kind = "grants_gov"

    def fetch(self) -> Iterable[Opportunity]:
        keyword = self.require("keyword")
        rows = int(self.options.get("rows", 50))
        statuses = self.options.get("statuses", "forecasted|posted")

        payload = post_json(
            ENDPOINT,
            {
                "keyword": keyword,
                "rows": rows,
                "oppStatuses": statuses,
            },
        )

        data = payload.get("data") if isinstance(payload, dict) else None
        hits = (data or {}).get("oppHits", []) if isinstance(data, dict) else []
        if not isinstance(hits, list):
            log.warning("grants.gov returned an unexpected shape for %r", keyword)
            return

        for record in hits:
            if not isinstance(record, dict):
                continue
            title = first_key(record, _TITLE_KEYS)
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
                agency=first_key(record, _AGENCY_KEYS),
                amount=self.options.get("default_amount", "see solicitation"),
                summary=strip_html(first_key(record, ("description", "synopsis")))[:400],
                open_date=parse_date(first_key(record, _OPEN_KEYS)),
                close_date=parse_date(first_key(record, _CLOSE_KEYS)),
                pillar=2,
                kind="grant",
                eligibility=self.options.get("eligibility", ""),
                raw=record,
            )
