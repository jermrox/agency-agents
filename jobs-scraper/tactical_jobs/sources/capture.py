"""Adapter for job-board listing pages captured as text.

WHY THIS EXISTS
Some environments cannot reach a board directly -- a locked-down CI runner, an
air-gapped review box, or a sandbox whose egress policy blocks the host. The
listing still has to be turned into postings by code rather than by hand.

This adapter reads a captured listing page from disk and parses it. The
important property is that **every field is derived here, by this parser**. A
capture file carries only the source URL, the retrieval date, and the page text
exactly as it was returned. If a listing does not state a value, the parser
emits nothing for it -- it never fills a gap with a plausible-looking guess.

That rule is not decorative. An earlier attempt at this project hand-wrote a
"live" dataset and invented posting dates, two URLs, and three descriptions to
fill gaps, then labelled the result verified. Filling gaps is worse than leaving
them empty, because it destroys the reader's ability to tell which fields are
real. Hence :meth:`_parse_age` returning an explicit ``approximate`` flag rather
than a clean-looking timestamp, and hence the parser refusing to emit a posting
that has no title.

CAPTURE FORMAT
    SOURCE_URL: <the url the text came from>
    RETRIEVED: <YYYY-MM-DD>
    ---
    <page text, verbatim>

LISTING GRAMMAR (WP Job Manager renders every row this way)
    ## <title>
    <employer> <location> <employment type> <category>[ $<pay>]● Posted <age>
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from ..models import JobPosting
from .base import Source

log = logging.getLogger(__name__)

_HEADER = re.compile(r"^SOURCE_URL:\s*(?P<url>\S+)\s*\nRETRIEVED:\s*(?P<date>[\d-]+)\s*\n---\s*\n",
                     re.MULTILINE)

# "## Some Job Title" -- a listing row's heading.
_TITLE = re.compile(r"^##\s+(?P<title>.+?)\s*$", re.MULTILINE)

# The meta line that follows a title. Pay and the posted-age are both optional
# because plenty of rows carry neither.
_META = re.compile(
    r"^(?P<body>.+?)"
    r"(?:\s*(?P<pay>\$[\d,]+(?:\.\d+)?(?:\s*[-–]\s*\$?[\d,]+(?:\.\d+)?)?(?:\s*/\s*\w+)?))?"
    r"(?:\s*●\s*Posted\s+(?P<age>[^●\n]+?))?\s*$"
)

_TYPES = ("Full-Time", "Part-Time", "Full Time", "Part Time", "Contract", "Internship",
          "Temporary", "Seasonal", "Freelance")

# WHAT THIS GRAMMAR CANNOT GIVE US, AND WHY WE SAY SO
#
# A listing row reads "<employer> <city>, <ST> <type> <category>". There is no
# delimiter between the employer and the city, and both are capitalized runs, so
# the split is genuinely ambiguous from the text alone:
#
#   "West Virginia University Health System Camden, NJ"
#        -> employer "West Virginia University Health System", city "Camden"
#   "Southern Utah University Cedar City, UT"
#        -> employer "Southern Utah University",              city "Cedar City"
#
# One-word and two-word cities both occur, so no fixed lookback is correct, and
# every heuristic tried here produced confident nonsense ("Health System Camden"
# as a city, "O2" as an employer). The state is the only piece the row pins
# down unambiguously.
#
# So the parser emits the STATE and keeps the meta line verbatim, and leaves
# employer and city as None. That is the whole point: a listing page does not
# carry these fields reliably, the per-posting page does, and a plausible guess
# in an employer column is worse than a blank one because nobody can tell it is
# wrong. Postings from this source score low on purpose and land in review.
_STATE = re.compile(r",\s*(?P<state>[A-Z]{2})\b")

_AGE = re.compile(r"^(?P<n>\d+)\s+(?P<unit>hour|day|week|month|year)s?\s+ago$", re.I)
_UNIT_DAYS = {"hour": 1 / 24, "day": 1, "week": 7, "month": 30, "year": 365}


@dataclass(slots=True)
class Listing:
    """One parsed row. Absent fields stay None -- never a substituted value."""

    title: str
    employer: str | None = None
    location: str | None = None
    employment_type: str | None = None
    pay: str | None = None
    posted_at: datetime | None = None
    raw_meta: str | None = None
    """The meta line exactly as the page rendered it.

    Kept because employer and city cannot be split out of it reliably; this is
    the honest carrier for information the typed fields decline to claim.
    """

    posted_approximate: bool = False
    """True when the date was derived from a relative age ("2 days ago").

    The board does not publish an exact timestamp for these, so the value is a
    computed approximation and must be labelled as one wherever it is shown.
    """


def _parse_age(age: str, retrieved: datetime) -> tuple[datetime | None, bool]:
    match = _AGE.match(age.strip())
    if not match:
        return None, False
    days = int(match.group("n")) * _UNIT_DAYS[match.group("unit").lower()]
    return retrieved - timedelta(days=days), True


def _split_meta(body: str) -> tuple[str | None, str | None, str | None]:
    """Pull employer, location and employment type out of the meta line.

    Order matters: the employment type is removed first because it sits between
    the location and the category, then the location is matched, and whatever
    precedes it is the employer.
    """
    employment_type = None
    for candidate in _TYPES:
        if candidate in body:
            employment_type = candidate
            body = body.replace(candidate, "|TYPE|", 1)
            break

    # Employer is deliberately NOT derived -- see the note above _STATE. Only
    # the state is unambiguous, so that is all that is claimed.
    state = _STATE.search(body)
    location = state.group("state") if state else None
    return None, location, employment_type


def parse_capture(text: str) -> tuple[str, datetime, list[Listing]]:
    """Parse a capture file into (source_url, retrieved_at, listings)."""
    header = _HEADER.search(text)
    if not header:
        raise ValueError("capture is missing its SOURCE_URL/RETRIEVED header")
    source_url = header.group("url")
    retrieved = datetime.fromisoformat(header.group("date")).replace(tzinfo=timezone.utc)

    body = text[header.end():]
    lines = body.splitlines()

    listings: list[Listing] = []
    for index, line in enumerate(lines):
        title_match = _TITLE.match(line)
        if not title_match:
            continue
        title = title_match.group("title").strip()
        if not title:
            continue

        # The meta line is the next non-blank line; if there is none, the row
        # still yields a posting with a title and nothing else invented.
        meta_line = ""
        for following in lines[index + 1:]:
            if following.strip():
                meta_line = following.strip()
                break
            if following == "" and meta_line:
                break
        if meta_line.startswith("##"):
            meta_line = ""

        listing = Listing(title=title, raw_meta=meta_line or None)
        if meta_line:
            meta = _META.match(meta_line)
            if meta:
                employer, location, employment_type = _split_meta(meta.group("body") or "")
                listing.employer = employer
                listing.location = location
                listing.employment_type = employment_type
                listing.pay = (meta.group("pay") or "").strip() or None
                if meta.group("age"):
                    listing.posted_at, listing.posted_approximate = _parse_age(
                        meta.group("age"), retrieved
                    )
        listings.append(listing)

    return source_url, retrieved, listings


class CaptureSource(Source):
    """Reads captured listing pages from a directory and yields postings."""

    kind = "capture"

    def fetch(self) -> Iterable[JobPosting]:
        directory = Path(self.require("directory"))
        pattern = self.options.get("pattern", "*.txt")
        if not directory.exists():
            log.warning("%s: capture directory %s does not exist", self.name, directory)
            return

        for path in sorted(directory.glob(pattern)):
            try:
                source_url, retrieved, listings = parse_capture(path.read_text())
            except (OSError, ValueError) as exc:
                log.warning("%s: skipping %s: %s", self.name, path.name, exc)
                continue

            for index, listing in enumerate(listings):
                # A listing page gives a title and a meta line, not a full
                # description. The description therefore carries only what the
                # page actually said -- deliberately thin, so these score low
                # and land in review rather than being published as if the
                # full posting had been read.
                # The verbatim meta line is the description. It holds the
                # employer and city that the parser refuses to split, so the
                # information is preserved for a human and for the classifier
                # without any field claiming to be something it is not.
                parts = [listing.title]
                if listing.raw_meta:
                    parts.append(listing.raw_meta)

                yield JobPosting(
                    source=f"{self.kind}:{self.name}",
                    source_id=f"{path.stem}#{index}",
                    url=source_url,       # the listing page; no per-row URL is published
                    title=listing.title,
                    employer=listing.employer or self.options.get("employer", ""),
                    location=listing.location or "",
                    description=" · ".join(parts),
                    compensation=listing.pay,
                    posted_at=listing.posted_at,
                    raw={
                        "capture_file": path.name,
                        "source_url": source_url,
                        "retrieved": retrieved.date().isoformat(),
                        "posted_approximate": listing.posted_approximate,
                        "raw_meta": listing.raw_meta,
                        "meta_parsed": {
                            "employer": listing.employer,
                            "state": listing.location,
                            "employment_type": listing.employment_type,
                            "pay": listing.pay,
                        },
                    },
                )


CAPTURE_SOURCES: tuple[type[Source], ...] = (CaptureSource,)
