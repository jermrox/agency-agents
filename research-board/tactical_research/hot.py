"""Hot this month: the front door of the site.

Reuses the rule the old board's watch list already ran on — a topic earns a
line when three or more *independent* items land on it inside the window. Two
is a note, not a trend, and the threshold is the whole point: without it the
block fills with whatever the sweep happened to find twice.

Independence is what stops one document with heavy coverage from looking like a
trend. Coverage is already folded into its item by the clustering step, so an
item is one voice here no matter how many outlets wrote it up.
"""

from __future__ import annotations

from dataclasses import dataclass

from .models import BoardItem

MIN_ITEMS = 3


@dataclass
class HotTopic:
    """A tag that three or more independent items landed on this window."""

    tag: str
    items: list[BoardItem]

    @property
    def count(self) -> int:
        return len(self.items)

    @property
    def sectors(self) -> list[str]:
        """Which sectors converged, in board order. Named in the line."""
        seen = []
        for item in self.items:
            if item.sector not in seen:
                seen.append(item.sector)
        return seen

    @property
    def types(self) -> list[str]:
        """Which kinds of item converged — policy plus research plus news is
        the signal worth a reader's attention, three studies less so."""
        seen = []
        for item in self.items:
            if item.type not in seen:
                seen.append(item.type)
        return seen


def hot_topics(items: list[BoardItem], min_items: int = MIN_ITEMS) -> list[HotTopic]:
    """Topics that cleared the bar, strongest first.

    Strength is the count, then the spread of types: a tag carrying policy and
    research and news is a live topic, three papers on it is a literature.
    """
    by_tag: dict[str, list[BoardItem]] = {}
    for item in items:
        for tag in item.tags:
            by_tag.setdefault(tag, []).append(item)

    topics = [HotTopic(tag=tag, items=group) for tag, group in by_tag.items() if len(group) >= min_items]
    topics.sort(key=lambda t: (t.count, len(t.types)), reverse=True)
    return topics


def stale_notes(notes: dict[str, str], cites: dict[str, list[str]], board: list[BoardItem]) -> list[str]:
    """Every reason a written hot-topic paragraph no longer matches the window.

    A paragraph names specific items. Items age out of the 30-day window every
    day, and a paragraph still quoting one reads as current when it is not. So
    each paragraph lists the primary_urls it relies on, and any that has left
    the board — or a paragraph that lists none — is a problem to fix in the data.
    """
    on_board = {item.primary_url for item in board}
    problems = []
    for tag in notes:
        listed = cites.get(tag, [])
        if not listed:
            problems.append(f"{tag}: paragraph lists no cited items")
        for url in listed:
            if url not in on_board:
                problems.append(f"{tag}: cites an item no longer in the window: {url}")
    return problems
