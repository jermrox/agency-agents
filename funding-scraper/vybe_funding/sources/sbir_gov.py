"""SBIR.gov solicitations -- every federal SBIR/STTR agency in one call.

WHY THIS SOURCE CARRIES THE MOST WEIGHT
SBIR.gov aggregates open solicitations across all eleven participating
agencies (NSF, NIH, DoD, DOE, NASA, DHS, USDA, and the rest). One keyless
endpoint therefore replaces eleven separate agency scrapes, and -- the point
of this project -- it carries the *current* close date for each, so a
solicitation that closed yesterday shows as closed today instead of sitting on
the board as a live opportunity.

API: https://api.www.sbir.gov/public/api/solicitations
Open, no key, no account. Documented at https://www.sbir.gov/api

FIELD NAMES: DOCUMENTED VS DEFENSIVE
``solicitation_title``, ``agency``, ``close_date``, ``open_date``,
``solicitation_agency_url`` are the documented response keys. Everything in
the ``_*_KEYS`` tuples below is a defensive alternate spelling -- names the
same data carries on adjacent SBIR.gov surfaces -- kept because the asymmetry
favours them: an unexpected rename costs one dict lookup to survive, but
costs a silently empty board if unhandled. They are NOT confirmed responses.
"""

from __future__ import annotations

import logging
from typing import Any, Iterable

from ..http import fetch_json
from ..models import Opportunity, parse_date
from .base import Source, first_key, strip_html

log = logging.getLogger(__name__)

ENDPOINT = "https://api.www.sbir.gov/public/api/solicitations"

_TITLE_KEYS = ("solicitation_title", "title", "solicitationTitle")
_AGENCY_KEYS = ("agency", "agency_name", "agencyName")
_CLOSE_KEYS = ("close_date", "closeDate", "current_close_date", "proposal_close_date")
_OPEN_KEYS = ("open_date", "openDate", "release_date", "proposal_open_date")
_URL_KEYS = ("solicitation_agency_url", "sbir_solicitation_link", "url", "link")
_SUMMARY_KEYS = ("description", "summary", "solicitation_description")
_NUMBER_KEYS = ("solicitation_number", "solicitationNumber", "number")


class SBIRGovSource(Source):
    """Open federal SBIR/STTR solicitations, filtered to relevant keywords."""

    kind = "sbir_gov"

    def fetch(self) -> Iterable[Opportunity]:
        rows = int(self.options.get("rows", 200))
        keywords = [k.lower() for k in self.options.get("keywords", [])]
        agencies = {a.lower() for a in self.options.get("agencies", [])}

        # `open=1` asks the API for currently-open solicitations only. We still
        # re-derive status from close_date locally, because "open" upstream and
        # "open as of this run" are not guaranteed to agree.
        url = f"{ENDPOINT}?open=1&rows={rows}&format=json"
        payload = fetch_json(url)

        records = payload if isinstance(payload, list) else payload.get("data", payload.get("results", []))
        if not isinstance(records, list):
            log.warning("sbir.gov returned an unexpected shape: %r", type(payload))
            return

        for record in records:
            if not isinstance(record, dict):
                continue
            title = first_key(record, _TITLE_KEYS)
            if not title:
                continue

            agency = first_key(record, _AGENCY_KEYS)
            if agencies and agency.lower() not in agencies:
                continue

            summary = strip_html(first_key(record, _SUMMARY_KEYS))
            if keywords and not self._matches(keywords, title, summary):
                continue

            number = first_key(record, _NUMBER_KEYS)
            yield Opportunity(
                source="sbir.gov",
                name=title if not number else f"{title} ({number})",
                url=first_key(record, _URL_KEYS) or "https://www.sbir.gov/solicitations",
                agency=agency,
                amount=self.options.get("default_amount", "Phase I scale"),
                summary=summary[:400],
                open_date=parse_date(first_key(record, _OPEN_KEYS)),
                close_date=parse_date(first_key(record, _CLOSE_KEYS)),
                pillar=2,
                kind="grant",
                eligibility="US small business, <500 employees, majority US-owned",
                raw=record,
            )

    @staticmethod
    def _matches(keywords: list[str], *fields: str) -> bool:
        haystack = " ".join(fields).lower()
        return any(keyword in haystack for keyword in keywords)
