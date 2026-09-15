"""Hot this month: three or more independent items, or it is not a trend."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_research.hot import hot_topics  # noqa: E402
from tactical_research.models import BoardItem  # noqa: E402


def item(tags, type_="Research", sector="MIL", headline="x"):
    return BoardItem(
        headline=headline, blurb="b", primary_url="https://armypubs.army.mil/x",
        date_published="2026-09-01", type=type_, sector=sector, tags=tags,
    )


class TestThreshold:
    def test_two_items_is_a_note_not_a_trend(self):
        items = [item(["Sleep and fatigue"]), item(["Sleep and fatigue"])]
        assert hot_topics(items) == []

    def test_three_items_earns_a_line(self):
        items = [item(["Sleep and fatigue"]) for _ in range(3)]
        topics = hot_topics(items)
        assert len(topics) == 1 and topics[0].tag == "Sleep and fatigue"

    def test_coverage_does_not_inflate_a_topic(self):
        """Clustering already folded coverage into its item, so one document with
        thirty articles is one voice here — the reason the threshold means
        anything."""
        loud = item(["Standards and tests"])
        loud.coverage_urls = [f"https://outlet{n}.com/x" for n in range(30)]
        assert hot_topics([loud]) == []


class TestRanking:
    def test_bigger_topics_rank_first(self):
        items = [item(["MSK injury"]) for _ in range(5)] + [item(["Nutrition"]) for _ in range(3)]
        assert [t.tag for t in hot_topics(items)] == ["MSK injury", "Nutrition"]

    def test_a_spread_of_types_outranks_a_single_type_at_equal_count(self):
        """Policy plus research plus news is a live topic; three papers is a
        literature."""
        mixed = [
            item(["Brain health"], type_="Policy"),
            item(["Brain health"], type_="Research"),
            item(["Brain health"], type_="News"),
        ]
        flat = [item(["Nutrition"], type_="Research") for _ in range(3)]
        ranked = hot_topics(mixed + flat)
        assert ranked[0].tag == "Brain health"


class TestReporting:
    def test_a_topic_names_the_sectors_that_converged(self):
        items = [
            item(["MSK injury"], sector="MIL"),
            item(["MSK injury"], sector="FIRE"),
            item(["MSK injury"], sector="MIL"),
        ]
        assert hot_topics(items)[0].sectors == ["MIL", "FIRE"]

    def test_an_item_with_several_tags_counts_toward_each(self):
        items = [item(["MSK injury", "Load and PPE"]) for _ in range(3)]
        assert {t.tag for t in hot_topics(items)} == {"MSK injury", "Load and PPE"}

    def test_empty_input(self):
        assert hot_topics([]) == []
