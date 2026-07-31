"""Adapter for saved search-engine result sets.

WHY THIS EXISTS
A search engine reaches far more of this market than any single job board. One
query for "tactical strength and conditioning coach" surfaces employer career
hubs, aggregator listings, and association boards all at once -- which is how a
person finds these jobs, and it should be how the scraper finds them too.

This adapter consumes a saved result set (Title / URL / Published / Highlights
records) and turns it into postings **in code**. It applies the same rule as
capture.py: a field the result set does not state is emitted as nothing, never
as a plausible value.

The important work here is not parsing -- it is REJECTION. A search for job
postings returns career-advice articles, company "about" pages, certification
explainers, and LinkedIn company profiles alongside the actual openings. Those
are not jobs, and letting them through would inflate a count that someone is
going to quote. :func:`looks_like_posting` is deliberately strict, and
:func:`rejection_reason` records why each discarded row was discarded so the
filter can be audited rather than trusted.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable
from urllib.parse import urlparse

from ..models import JobPosting
from .base import Source, html_to_text

log = logging.getLogger(__name__)

_FIELD = re.compile(r"^(?P<key>Title|URL|Published|Author|Highlights):\s*(?P<value>.*)$")

# NO HOST ALLOWLIST. An earlier version required the host to appear in a fixed
# list of ~20 job sites, and that single condition discarded 57 of 75 results --
# almost all of them real openings. This market is syndicated across a long tail
# of boards (nexxt, trabajo, lensa, jobs-cast, clearedcareers, dejobs,
# careerwebsite, university career portals, paylocity...), and any hand-written
# list will always be missing most of them. Real Serco H2F roles at Fort Drum,
# Fort Irwin, Fort Polk, Fort Sill and Hawaii, plus GDIT, Battelle, Loyal
# Source, Tanaq and T3i openings, were all being thrown away.
#
# So the test is the URL's SHAPE -- does it address one posting -- plus a title
# that is not editorial. That generalizes to hosts nobody has seen yet, which is
# the entire point of harvesting from a search engine.

# A path that addresses an individual posting: a jobs-ish segment followed by a
# slug or id. The trailing part must be substantial, which is what separates
# "/jobs/h2fit-coach-fort-drum" from a bare "/jobs/" index.
#
# The separator is [-/], not just "/": some boards mint "/job-5003-<hash>"
# rather than "/job/<slug>". Requiring a slash silently dropped every posting on
# those hosts -- caught by the long-tail regression test, which is exactly the
# failure mode this whole filter has already been wrong about once.
_JOB_PATH = re.compile(
    r"/(?:job|jobs|job-details|job-v1|careers|career|opening|openings|vacanc\w*|"
    r"position|posting|workspread|recruiting)s?[-/][^/?#]{4,}", re.I
)

# Some boards mint a posting URL with no jobs-ish segment at all --
# "serco-na.dejobs.org/quantico-va/h2fit-strength-conditioning-coach/9AD0EFD"
# is <location>/<slug>/<id>. Path shape alone therefore cannot be the whole
# test. When the HOST itself announces that the site is a job board, a
# substantial slug in the path is enough. This is a hint, not an allowlist: it
# is a property of the hostname, so it generalizes to boards nobody has listed.
_JOB_HOST_HINT = re.compile(r"(?:job|career|hiring|recruit|talent|employ|vacanc)", re.I)
_SLUG = re.compile(r"/[^/?#]{8,}")

# Sites whose terms prohibit automated collection. Excluded from the harvest
# even though a search engine surfaced them -- consistent with the rest of this
# project, which never scrapes them.
_TOS_EXCLUDED = ("indeed.com", "ziprecruiter.com", "glassdoor.com", "linkedin.com")

# A result whose URL ends at a bare index is a listing page, not one posting.
_INDEX_PATH = re.compile(
    r"/(?:jobs|careers|openings|search-results|job-category|category|search)/?$", re.I
)

# Titles that mark editorial content rather than an opening.
_ARTICLE_TITLE = re.compile(
    r"\b(?:a career overview|career overview|how to (?:get|become)|guide to|what is|"
    r"why |top \d+|best \d+|\d+ (?:tips|ways|things)|overview|explained|"
    r"vs\.?\s|comparison|salary guide|certification|exam|course|webinar|podcast|"
    r"blog|news|press release|announces|awarded)\b", re.I
)

# Social and directory pages that are never a posting.
_SOCIAL = re.compile(r"^https?://(?:[a-z0-9-]+\.)?(?:linkedin|facebook|x|twitter|"
                     r"instagram|youtube|reddit|glassdoor|indeed|ziprecruiter)\.com/", re.I)


@dataclass(slots=True)
class SearchResult:
    title: str = ""
    url: str = ""
    published: str | None = None
    author: str | None = None
    highlights: list[str] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "\n".join(self.highlights).strip()


def parse_results(text: str) -> list[SearchResult]:
    """Parse a saved result set into records.

    A record starts at a ``Title:`` line and runs until the next one, so
    multi-line Highlights blocks stay attached to the result they belong to.
    """
    results: list[SearchResult] = []
    current: SearchResult | None = None
    in_highlights = False

    for line in text.splitlines():
        match = _FIELD.match(line)
        if match:
            key, value = match.group("key"), match.group("value").strip()
            if key == "Title":
                if current and current.url:
                    results.append(current)
                current = SearchResult(title=value)
                in_highlights = False
                continue
            if current is None:
                continue
            in_highlights = False
            if key == "URL":
                current.url = value
            elif key == "Published":
                current.published = value or None
            elif key == "Author":
                current.author = value or None
            elif key == "Highlights":
                in_highlights = True
                if value:
                    current.highlights.append(value)
            continue

        if current and in_highlights and line.strip() and line.strip() != "...":
            current.highlights.append(line.strip())

    if current and current.url:
        results.append(current)
    return results


def rejection_reason(result: SearchResult) -> str | None:
    """Why this result is not an individual job posting, or None if it is.

    Returning the reason rather than a bool is deliberate: the filter drops the
    large majority of every result set, and a count nobody can audit is a count
    nobody should quote.
    """
    url = (result.url or "").strip()
    if not url or not result.title.strip():
        return "missing url or title"
    if _SOCIAL.match(url):
        return "social or excluded aggregator"
    if _ARTICLE_TITLE.search(result.title):
        return "editorial or announcement, not a posting"
    if any(host in url.lower() for host in _TOS_EXCLUDED):
        return "terms prohibit automated collection"
    if _INDEX_PATH.search(url.split("?")[0]):
        return "listing index, not one posting"
    if _JOB_PATH.search(url):
        return None
    # Fall back to the host hint: a job-board hostname plus a substantial slug.
    parsed = urlparse(url)
    if _JOB_HOST_HINT.search(parsed.netloc) and _SLUG.search(parsed.path):
        return None
    return "no individual-posting path"


def looks_like_posting(result: SearchResult) -> bool:
    return rejection_reason(result) is None


def _parse_published(value: str | None) -> datetime | None:
    if not value:
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


class SearchResultsSource(Source):
    """Reads saved search result sets from a directory and yields postings."""

    kind = "searchresults"

    def fetch(self) -> Iterable[JobPosting]:
        directory = Path(self.require("directory"))
        pattern = self.options.get("pattern", "*.txt")
        if not directory.exists():
            log.warning("%s: directory %s does not exist", self.name, directory)
            return

        seen: set[str] = set()
        for path in sorted(directory.glob(pattern)):
            try:
                results = parse_results(path.read_text(errors="replace"))
            except OSError as exc:
                log.warning("%s: skipping %s: %s", self.name, path.name, exc)
                continue

            for result in results:
                reason = rejection_reason(result)
                if reason:
                    log.debug("%s: dropped %r (%s)", self.name, result.title[:60], reason)
                    continue
                url = result.url.split("#")[0]
                if url in seen:
                    continue
                seen.add(url)

                yield JobPosting(
                    source=f"{self.kind}:{self.name}",
                    source_id=url,
                    url=url,
                    title=result.title.strip(),
                    # Employer is left EMPTY on purpose, twice over.
                    #
                    # The title cannot give it: search titles append site names
                    # ("... - Serco | Apply Today at CareerBuilder"), so any
                    # split is a guess. Nor can the result's author field --
                    # that is page metadata about the SITE, and using it
                    # produced an employer table reading "N/A" (71 rows),
                    # "Site built by: Career.com", "The Escape" and "xpatjobs".
                    # A search result simply does not carry the employer as a
                    # field; the posting page does. The classifier still reads
                    # it out of the highlight text.
                    employer="",
                    location="",
                    description=html_to_text(result.text),
                    posted_at=_parse_published(result.published),
                    raw={"result_file": path.name, "published_raw": result.published},
                )


SEARCH_SOURCES: tuple[type[Source], ...] = (SearchResultsSource,)
