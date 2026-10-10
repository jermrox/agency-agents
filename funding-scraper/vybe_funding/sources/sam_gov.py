"""SAM.gov Contract Opportunities -- federal solicitations, BAAs and notices.

WHY THIS SOURCE
grants.gov carries federal *grants*. A large share of federal money for a
wearable company -- DoD and DHS BAAs, xTech and AFWERX solicitations, VA and
HHS research contracts, sources-sought notices that precede an award -- is
posted as a *contract* opportunity on SAM.gov instead, and never reaches
grants.gov at all.

Every row from here is ``sam = "required"``: a contract award needs an active
SAM.gov registration, and the board must say so.

API: GET https://api.sam.gov/opportunities/v2/search
Needs an API key (free, from a SAM.gov account). The key is read from the
``SAM_API_KEY`` environment variable and nowhere else: it is a secret, so it
lives in the GitHub Actions secret store, never in sources.toml.

THE KEY NEVER LEAVES THE PROCESS
It is sent as the ``X-Api-Key`` header rather than the ``api_key`` query
parameter, so it cannot appear in a URL, and every error raised from here has
the key scrubbed out. Source errors are written into the public funding.json,
so a key inside an error message would be published on the live site.

RATE LIMIT
A personal SAM.gov key allows few requests per day. One request per keyword,
so keep ``keywords`` short; a 429 is reported as a source error like any other
failure and the rest of the board still publishes.
"""

from __future__ import annotations

import logging
import os
import urllib.parse
from datetime import date, timedelta
from typing import Iterable

from ..http import fetch_json
from ..models import Opportunity, parse_date
from .base import Source, SourceError, strip_html

log = logging.getLogger(__name__)

ENDPOINT = "https://api.sam.gov/opportunities/v2/search"
KEY_ENV = "SAM_API_KEY"

# o = solicitation, k = combined synopsis/solicitation, p = presolicitation,
# r = sources sought. Award notices and justifications are not opportunities.
DEFAULT_TYPES = "o,k,p,r"


class SAMGovSource(Source):
    """Federal contract opportunities whose title matches a keyword."""

    kind = "sam_gov"

    def _get(self, params: dict[str, str], key: str) -> dict:
        url = f"{ENDPOINT}?{urllib.parse.urlencode(params)}"
        try:
            payload = fetch_json(url, headers={"X-Api-Key": key}, retries=2)
        except Exception as exc:  # noqa: BLE001 - re-raised scrubbed
            raise SourceError(str(exc).replace(key, "***")) from None
        if not isinstance(payload, dict):
            raise SourceError("SAM.gov returned an unexpected response shape")
        return payload

    def fetch(self) -> Iterable[Opportunity]:
        key = os.environ.get(KEY_ENV, "").strip()
        if not key:
            # Not an error: the source is opt-in through the secret. Reporting
            # it as a failure would put "1 source unreachable" on the live
            # board every day until someone adds a key.
            log.warning("%s not set; skipping SAM.gov contract opportunities", KEY_ENV)
            return

        keywords = [str(k) for k in self.require("keywords")]
        days = int(self.options.get("posted_within_days", 90))
        limit = min(int(self.options.get("rows", 100)), 1000)
        today = date.today()
        posted_from = (today - timedelta(days=days)).strftime("%m/%d/%Y")
        posted_to = today.strftime("%m/%d/%Y")

        seen: set[str] = set()
        for keyword in keywords:
            payload = self._get(
                {
                    "postedFrom": posted_from,
                    "postedTo": posted_to,
                    "ptype": str(self.options.get("types", DEFAULT_TYPES)),
                    "title": keyword,
                    "limit": str(limit),
                    "offset": "0",
                },
                key,
            )
            records = payload.get("opportunitiesData") or []
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue
                notice_id = str(record.get("noticeId") or "")
                if not notice_id or notice_id in seen:
                    continue
                # Archived and inactive notices are not things anyone can bid.
                if str(record.get("active", "Yes")).lower() not in ("yes", "true"):
                    continue
                seen.add(notice_id)
                yield self._row(record, notice_id)

    def _row(self, record: dict, notice_id: str) -> Opportunity:
        title = strip_html(record.get("title"))
        number = str(record.get("solicitationNumber") or "").strip()
        agency = strip_html(record.get("fullParentPathName") or record.get("department"))
        # "DEPT OF DEFENSE.DEPT OF THE ARMY.AMC..." -- keep the top two levels.
        if "." in agency:
            agency = " / ".join(part.title() for part in agency.split(".")[:2])
        notice_type = strip_html(record.get("type"))
        set_aside = strip_html(record.get("typeOfSetAsideDescription"))

        summary_bits = [notice_type]
        if set_aside:
            summary_bits.append(f"set-aside: {set_aside}")
        if record.get("naicsCode"):
            summary_bits.append(f"NAICS {record['naicsCode']}")

        eligibility = "Federal contract: an active SAM.gov registration (UEI) is required to be awarded."
        if set_aside:
            eligibility = f"{set_aside}. {eligibility}"

        return Opportunity(
            source="sam.gov",
            name=f"{title} ({number})" if number else title,
            url=str(record.get("uiLink") or f"https://sam.gov/opp/{notice_id}/view"),
            agency=agency,
            amount=self.options.get("default_amount", "see solicitation"),
            summary=" · ".join(b for b in summary_bits if b)[:400],
            open_date=parse_date(record.get("postedDate")),
            close_date=parse_date(record.get("responseDeadLine")),
            pillar=2,
            kind="grant",
            eligibility=eligibility,
            sam="required",
            raw={"noticeId": notice_id},
        )
