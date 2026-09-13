"""The board's schema, from section 7.1 of the brief.

One dataclass, deliberately flat: an item is a document plus what the sweep
worked out about it. Everything the old board carried and the brief removed —
evidence grades, secondary caveats, the fetch-verified counter — is absent on
purpose, not forgotten.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta

# Filters only. An item carries one to three; they never structure the page,
# because the brief's whole layout argument is that sections force readers to
# learn our sorting before they can find anything.
TAGS = (
    "MSK injury",
    "Standards and tests",
    "Body composition",
    "Sleep and fatigue",
    "Nutrition",
    "Brain health",
    "Behavioral health",
    "Women's health",
    "Men's health",
    "Wearables",
    "Environment",
    "Load and PPE",
    "Programs and funding",
    "Events",
)

TYPES = ("Research", "Policy", "News")

# CROSS is not a fallback for "unsure" — it means the item genuinely lands on
# more than one sector, which is common for federal rulemaking and surveillance.
SECTORS = ("MIL", "FIRE", "EMS", "LE", "CROSS")

WINDOW_DAYS = 30
ARCHIVE_MONTHS = 12


@dataclass
class BoardItem:
    """One document on the board."""

    headline: str                      # plain English, not the document title
    blurb: str                         # two to four sentences, from the document
    primary_url: str
    date_published: str                # ISO date
    type: str = "News"
    sector: str = "CROSS"
    tags: list[str] = field(default_factory=list)
    first_seen: str = ""
    identifier: str = ""               # DOI, PMID, issuance number, docket, GAO
    coverage_urls: list[str] = field(default_factory=list)
    score: float = 0.0
    supersedes: str = ""               # primary_url of the item this replaces

    def validate(self) -> list[str]:
        """Every problem with this item, in reading order. Empty means valid."""
        problems: list[str] = []
        if not self.headline.strip():
            problems.append("headline is empty")
        if not self.blurb.strip():
            problems.append("blurb is empty")
        if not self.primary_url.strip():
            problems.append("primary_url is empty")
        if self.type not in TYPES:
            problems.append(f"type {self.type!r} is not one of {TYPES}")
        if self.sector not in SECTORS:
            problems.append(f"sector {self.sector!r} is not one of {SECTORS}")
        if not self.tags:
            problems.append("no tags: the brief requires one to three")
        if len(self.tags) > 3:
            problems.append(f"{len(self.tags)} tags: the brief allows at most three")
        for tag in self.tags:
            if tag not in TAGS:
                problems.append(f"tag {tag!r} is not in the vocabulary")
        if not _is_iso_date(self.date_published):
            problems.append(f"date_published {self.date_published!r} is not an ISO date")
        return problems

    def age_days(self, today: date | None = None) -> int:
        """Days since publication. Negative for a future date, which happens."""
        published = _parse(self.date_published)
        if published is None:
            return 10**6          # undated sorts to the archive, never the board
        return (_today(today) - published).days

    def on_board(self, today: date | None = None) -> bool:
        """True while the item belongs on the 30-day board."""
        return self.age_days(today) <= WINDOW_DAYS

    def in_archive(self, today: date | None = None) -> bool:
        """True while the item belongs in the 12-month archive."""
        age = self.age_days(today)
        return WINDOW_DAYS < age <= ARCHIVE_MONTHS * 31

    def to_dict(self) -> dict:
        return asdict(self)


def _today(today: date | None) -> date:
    return today or datetime.utcnow().date()


def _parse(value: str) -> date | None:
    try:
        return datetime.strptime((value or "")[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def _is_iso_date(value: str) -> bool:
    return _parse(value) is not None


def split_window(items: list[BoardItem], today: date | None = None) -> tuple[list[BoardItem], list[BoardItem]]:
    """(board, archive), each newest first.

    Nothing is deleted — the brief is explicit — but the main board is never
    more than a month deep. Anything past the archive horizon falls out of both.
    """
    board = [i for i in items if i.on_board(today)]
    archive = [i for i in items if i.in_archive(today)]
    key = lambda i: i.date_published  # noqa: E731
    return sorted(board, key=key, reverse=True), sorted(archive, key=key, reverse=True)


def load(path) -> list[BoardItem]:
    """Read items from a findings JSON file."""
    with open(path, encoding="utf-8") as handle:
        data = json.load(handle)
    return [BoardItem(**row) for row in data.get("items", [])]


def dump(items: list[BoardItem], path, generated: str = "") -> None:
    """Write items to a findings JSON file."""
    payload = {
        "generated": generated or datetime.utcnow().isoformat(timespec="seconds") + "Z",
        "window_days": WINDOW_DAYS,
        "items": [i.to_dict() for i in items],
    }
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")
