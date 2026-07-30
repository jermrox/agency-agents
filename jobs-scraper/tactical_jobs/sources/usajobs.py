"""USAJOBS adapter -- federal civilian and DoD-civilian postings.

This is the single highest-value source for this niche. Army H2F, Navy and
Air Force human performance billets, and VA/DoD sports-medicine roles are
posted here first and often nowhere else.

Requires a free API key: https://developer.usajobs.gov/apirequest/
Set ``USAJOBS_API_KEY`` and ``USAJOBS_USER_AGENT`` (your registered email).
"""

from __future__ import annotations

from typing import Any, Iterable

from ..http import fetch_json
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

API_URL = "https://data.usajobs.gov/api/search"

DEFAULT_KEYWORDS = (
    "human performance",
    "strength and conditioning",
    "athletic trainer",
    "exercise physiologist",
    "performance dietitian",
    "cognitive performance",
    "holistic health and fitness",
)
"""Server-side keyword filter.

USAJOBS holds hundreds of thousands of postings, so pulling everything and
filtering locally is wasteful. These queries cast a wide net and the local
classifier does the precision work.
"""


class USAJobsSource(Source):
    kind = "usajobs"

    def fetch(self) -> Iterable[JobPosting]:
        api_key = self.require("api_key")
        user_agent = self.require("user_agent")
        keywords = self.options.get("keywords") or list(DEFAULT_KEYWORDS)
        results_per_page = int(self.options.get("results_per_page", 250))
        max_pages = int(self.options.get("max_pages", 4))

        headers = {
            "Host": "data.usajobs.gov",
            "User-Agent": user_agent,
            "Authorization-Key": api_key,
        }

        seen_ids: set[str] = set()
        for keyword in keywords:
            for page in range(1, max_pages + 1):
                payload = fetch_json(
                    API_URL,
                    headers=headers,
                    params={
                        "Keyword": keyword,
                        "ResultsPerPage": results_per_page,
                        "Page": page,
                        "WhoMayApply": self.options.get("who_may_apply", "All"),
                    },
                )
                result = payload.get("SearchResult", {})
                items = result.get("SearchResultItems", [])
                for item in items:
                    posting = self._to_posting(item)
                    if posting and posting.source_id not in seen_ids:
                        seen_ids.add(posting.source_id)
                        yield posting
                # Stop as soon as a page comes back short -- there is no next one.
                if len(items) < results_per_page:
                    break

    def _to_posting(self, item: dict[str, Any]) -> JobPosting | None:
        descriptor = item.get("MatchedObjectDescriptor")
        if not descriptor:
            return None

        details = (descriptor.get("UserArea") or {}).get("Details") or {}
        summary_parts = [
            descriptor.get("QualificationSummary") or "",
            details.get("JobSummary") or "",
            details.get("MajorDuties") and " ".join(details["MajorDuties"]) or "",
        ]
        description = html_to_text(" ".join(part for part in summary_parts if part))

        compensation = None
        remuneration = descriptor.get("PositionRemuneration") or []
        if remuneration:
            first = remuneration[0]
            minimum, maximum = first.get("MinimumRange"), first.get("MaximumRange")
            interval = first.get("RateIntervalCode", "")
            if minimum and maximum:
                compensation = f"${minimum} - ${maximum} {interval}".strip()

        location = descriptor.get("PositionLocationDisplay", "") or ""
        organization = descriptor.get("OrganizationName", "") or ""
        department = descriptor.get("DepartmentName")

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=str(
                item.get("MatchedObjectId") or descriptor.get("PositionID") or ""
            ),
            url=descriptor.get("PositionURI", ""),
            title=descriptor.get("PositionTitle", ""),
            # The hiring org is the useful employer label; the parent
            # department ("Department of the Army") lands in `department`.
            employer=organization or department or "U.S. Federal Government",
            location=location,
            description=description,
            posted_at=parse_timestamp(descriptor.get("PublicationStartDate")),
            remote=looks_remote(location, details.get("TeleworkEligible") and "telework"),
            department=department,
            compensation=compensation,
            raw=descriptor,
        )
