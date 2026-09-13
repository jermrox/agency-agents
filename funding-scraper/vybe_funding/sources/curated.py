"""Hand-verified opportunities that no open API exposes.

WHY A CURATED LAYER EXISTS AT ALL
Most of the highest-value opportunities for a hardware startup are not in any
machine-readable index: state programs (NYSTAR, FuzeHub), university vehicles
(Cornell CAT), cloud credit programs, and accelerators all publish a web page
and nothing else. Scraping each one's bespoke HTML is brittle -- a layout
change silently drops the row. Declaring them in TOML with a human-verified
close date is honest about what it is: a fact checked by a person on a date,
carried forward until rechecked.

``verified`` is therefore mandatory on every entry. ``vybe_funding report``
flags any entry whose verification is older than the staleness window, so the
curated layer ages visibly instead of rotting silently -- which is the whole
failure this project exists to prevent.
"""

from __future__ import annotations

import logging
from datetime import date
from typing import Iterable

from ..models import Opportunity, parse_date
from .base import Source, SourceError

log = logging.getLogger(__name__)


class CuratedSource(Source):
    """Opportunities declared inline in sources.toml."""

    kind = "curated"

    def fetch(self) -> Iterable[Opportunity]:
        entries = self.options.get("entry", [])
        if not isinstance(entries, list):
            raise SourceError("curated source expects an array of [[curated.entry]] tables")

        for entry in entries:
            name = entry.get("name")
            url = entry.get("url")
            if not name or not url:
                log.warning("curated entry missing name or url, skipping: %r", entry)
                continue

            verified = parse_date(entry.get("verified"))
            if verified is None:
                raise SourceError(
                    f"curated entry {name!r} has no `verified` date -- every hand-entered "
                    "opportunity must record when a human last checked it"
                )

            yield Opportunity(
                source="curated",
                name=name,
                url=url,
                agency=entry.get("agency", ""),
                amount=entry.get("amount", ""),
                summary=entry.get("note", ""),
                open_date=parse_date(entry.get("open_date")),
                close_date=parse_date(entry.get("close_date")),
                pillar=int(entry.get("pillar", 2)),
                kind=entry.get("kind", "grant"),
                eligibility=entry.get("eligibility", ""),
                documents=list(entry.get("documents", [])),
                raw={"verified": verified.isoformat()},
            )


def stale_entries(opportunities: Iterable[Opportunity], today: date, max_age_days: int) -> list[tuple[str, int]]:
    """Curated rows whose human verification has aged past the window."""
    stale: list[tuple[str, int]] = []
    for opp in opportunities:
        if opp.source != "curated":
            continue
        verified = parse_date(opp.raw.get("verified"))
        if verified is None:
            continue
        age = (today - verified).days
        if age > max_age_days:
            stale.append((opp.name, age))
    return sorted(stale, key=lambda item: -item[1])
