"""Adapters for the applicant tracking systems that publish public job APIs.

Every endpoint used here is the vendor's own documented public job-board API --
the same JSON that powers the employer's own careers page. That keeps the
project on defensible ground and, just as importantly, keeps it reliable:
these return clean structured data and do not change layout every quarter the
way scraped HTML does.

Deliberately **not** included: Indeed, ZipRecruiter, LinkedIn, Glassdoor.
Their terms prohibit automated collection, and they actively block it. If you
want that inventory, license it -- do not scrape it.
"""

from __future__ import annotations

from typing import Any, Iterable

from ..http import fetch_json
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp


class GreenhouseSource(Source):
    """Greenhouse job boards.

    Docs: https://developers.greenhouse.io/job-board.html
    Board token is the slug in ``boards.greenhouse.io/<token>``.
    """

    kind = "greenhouse"

    def fetch(self) -> Iterable[JobPosting]:
        token = self.require("board_token")
        employer = self.options.get("employer", token)
        payload = fetch_json(
            f"https://boards-api.greenhouse.io/v1/boards/{token}/jobs",
            params={"content": "true"},
        )
        for job in payload.get("jobs", []):
            location = (job.get("location") or {}).get("name", "")
            description = html_to_text(job.get("content"))
            departments = job.get("departments") or []
            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=str(job.get("id")),
                url=job.get("absolute_url", ""),
                title=job.get("title", ""),
                employer=employer,
                location=location,
                description=description,
                posted_at=parse_timestamp(job.get("updated_at") or job.get("created_at")),
                remote=looks_remote(location, job.get("title")),
                department=departments[0].get("name") if departments else None,
                raw=job,
            )


class LeverSource(Source):
    """Lever postings API. Docs: https://github.com/lever/postings-api"""

    kind = "lever"

    def fetch(self) -> Iterable[JobPosting]:
        token = self.require("board_token")
        employer = self.options.get("employer", token)
        payload = fetch_json(
            f"https://api.lever.co/v0/postings/{token}", params={"mode": "json"}
        )
        for job in payload:
            categories = job.get("categories") or {}
            location = categories.get("location", "") or ""
            description = html_to_text(
                job.get("descriptionPlain") or job.get("description")
            )
            extras = " ".join(
                html_to_text(item.get("content"))
                for item in (job.get("lists") or [])
                if isinstance(item, dict)
            )
            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=str(job.get("id")),
                url=job.get("hostedUrl") or job.get("applyUrl", ""),
                title=job.get("text", ""),
                employer=employer,
                location=location,
                description=f"{description}\n\n{extras}".strip(),
                posted_at=parse_timestamp(job.get("createdAt")),
                remote=looks_remote(location, categories.get("commitment")),
                department=categories.get("team"),
                raw=job,
            )


class AshbySource(Source):
    """Ashby job board API. Docs: https://developers.ashbyhq.com/docs/public-job-posting-api"""

    kind = "ashby"

    def fetch(self) -> Iterable[JobPosting]:
        token = self.require("board_token")
        employer = self.options.get("employer", token)
        payload = fetch_json(
            f"https://api.ashbyhq.com/posting-api/job-board/{token}",
            params={"includeCompensation": "true"},
        )
        for job in payload.get("jobs", []):
            location = job.get("location", "") or ""
            compensation = None
            summary = job.get("compensationTierSummary")
            if isinstance(summary, str) and summary.strip():
                compensation = summary.strip()
            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=str(job.get("id")),
                url=job.get("jobUrl", ""),
                title=job.get("title", ""),
                employer=employer,
                location=location,
                description=html_to_text(
                    job.get("descriptionPlain") or job.get("descriptionHtml")
                ),
                posted_at=parse_timestamp(job.get("publishedAt")),
                remote=bool(job.get("isRemote")) or looks_remote(location),
                department=job.get("department") or job.get("team"),
                compensation=compensation,
                raw=job,
            )


class WorkableSource(Source):
    """Workable's public job widget API."""

    kind = "workable"

    def fetch(self) -> Iterable[JobPosting]:
        token = self.require("board_token")
        employer = self.options.get("employer", token)
        payload = fetch_json(
            f"https://apply.workable.com/api/v1/widget/accounts/{token}",
            params={"details": "true"},
        )
        for job in payload.get("jobs", []):
            location = ", ".join(
                part
                for part in (job.get("city"), job.get("state"), job.get("country"))
                if part
            )
            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=str(job.get("shortcode") or job.get("id")),
                url=job.get("url") or job.get("application_url", ""),
                title=job.get("title", ""),
                employer=employer,
                location=location,
                description=html_to_text(
                    job.get("description", "") + " " + (job.get("requirements") or "")
                ),
                posted_at=parse_timestamp(job.get("published_on") or job.get("created_at")),
                remote=bool(job.get("telecommuting")) or looks_remote(location),
                department=job.get("department"),
                raw=job,
            )


class SmartRecruitersSource(Source):
    """SmartRecruiters posting API.

    The list endpoint omits the job description, and the description is where
    almost all of the tactical-domain signal lives, so each posting is fetched
    individually. ``detail_limit`` bounds that fan-out for large employers.
    """

    kind = "smartrecruiters"

    def fetch(self) -> Iterable[JobPosting]:
        token = self.require("company_id")
        employer = self.options.get("employer", token)
        limit = int(self.options.get("detail_limit", 100))

        payload = fetch_json(
            f"https://api.smartrecruiters.com/v1/companies/{token}/postings",
            params={"limit": min(limit, 100)},
        )
        for job in payload.get("content", [])[:limit]:
            job_id = str(job.get("id"))
            location_data = job.get("location") or {}
            location = ", ".join(
                part
                for part in (
                    location_data.get("city"),
                    location_data.get("region"),
                    location_data.get("country"),
                )
                if part
            )
            description = ""
            try:
                detail = fetch_json(
                    f"https://api.smartrecruiters.com/v1/companies/{token}/postings/{job_id}"
                )
                sections = ((detail.get("jobAd") or {}).get("sections") or {})
                description = html_to_text(
                    " ".join(
                        (sections.get(key) or {}).get("text", "")
                        for key in ("jobDescription", "qualifications", "companyDescription")
                    )
                )
            except Exception:
                # A single unavailable detail page should not drop the posting;
                # the title alone may still be enough for the review queue.
                description = job.get("name", "")

            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=job_id,
                url=(job.get("ref") or "").replace("api.smartrecruiters.com/v1", "jobs.smartrecruiters.com")
                or f"https://jobs.smartrecruiters.com/{token}/{job_id}",
                title=job.get("name", ""),
                employer=employer,
                location=location,
                description=description,
                posted_at=parse_timestamp(job.get("releasedDate")),
                remote=bool(location_data.get("remote")) or looks_remote(location),
                department=(job.get("department") or {}).get("label"),
                raw=job,
            )


class RecruiteeSource(Source):
    """Recruitee careers API."""

    kind = "recruitee"

    def fetch(self) -> Iterable[JobPosting]:
        token = self.require("board_token")
        employer = self.options.get("employer", token)
        payload = fetch_json(f"https://{token}.recruitee.com/api/offers/")
        for job in payload.get("offers", []):
            location = ", ".join(
                part
                for part in (job.get("city"), job.get("state_name"), job.get("country"))
                if part
            )
            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=str(job.get("id")),
                url=job.get("careers_url") or job.get("careers_apply_url", ""),
                title=job.get("title", ""),
                employer=employer,
                location=location,
                description=html_to_text(
                    (job.get("description") or "") + " " + (job.get("requirements") or "")
                ),
                posted_at=parse_timestamp(job.get("published_at") or job.get("created_at")),
                remote=looks_remote(location, job.get("remote") and "remote"),
                department=job.get("department"),
                raw=job,
            )


ATS_SOURCES: tuple[type[Source], ...] = (
    GreenhouseSource,
    LeverSource,
    AshbySource,
    WorkableSource,
    SmartRecruitersSource,
    RecruiteeSource,
)
