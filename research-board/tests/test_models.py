"""Schema and the 30-day window."""

from __future__ import annotations

import json
import sys
import tempfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_research.models import (  # noqa: E402
    SECTORS, TAGS, TYPES, BoardItem, dump, load, split_window,
)

TODAY = date(2026, 9, 13)


def item(**kw) -> BoardItem:
    base = dict(
        headline="Army raises the combat standard",
        blurb="Two to four sentences, written from the directive.",
        primary_url="https://armypubs.army.mil/a.pdf",
        date_published="2026-09-01",
        type="Policy",
        sector="MIL",
        tags=["Standards and tests"],
    )
    base.update(kw)
    return BoardItem(**base)


class TestValidation:
    def test_a_good_item_has_no_problems(self):
        assert item().validate() == []

    def test_every_missing_field_is_reported_not_just_the_first(self):
        problems = BoardItem(headline="", blurb="", primary_url="", date_published="x").validate()
        assert len(problems) >= 4

    def test_type_and_sector_are_closed_vocabularies(self):
        assert any("type" in p for p in item(type="Opinion").validate())
        assert any("sector" in p for p in item(sector="ARMY").validate())

    def test_tag_must_be_in_the_vocabulary(self):
        assert any("vocabulary" in p for p in item(tags=["Vibes"]).validate())

    def test_at_least_one_tag(self):
        assert any("no tags" in p for p in item(tags=[]).validate())

    def test_at_most_three_tags(self):
        four = list(TAGS[:4])
        assert any("at most three" in p for p in item(tags=four).validate())

    def test_three_tags_is_fine(self):
        assert item(tags=list(TAGS[:3])).validate() == []

    def test_the_brief_vocabularies_are_present(self):
        """Men's health was a real gap on the old board; the brief lists it."""
        assert "Men's health" in TAGS and "Women's health" in TAGS
        assert TYPES == ("Research", "Policy", "News")
        assert set(SECTORS) == {"MIL", "FIRE", "EMS", "LE", "CROSS"}


class TestWindow:
    def test_todays_item_is_on_the_board(self):
        assert item(date_published="2026-09-13").on_board(TODAY)

    def test_exactly_thirty_days_is_still_on_the_board(self):
        assert item(date_published="2026-08-14").on_board(TODAY)

    def test_thirty_one_days_falls_to_the_archive(self):
        older = item(date_published="2026-08-13")
        assert not older.on_board(TODAY)
        assert older.in_archive(TODAY)

    def test_a_future_date_still_shows(self):
        """Embargoed and post-dated issuances exist; they are not archived."""
        assert item(date_published="2026-09-20").on_board(TODAY)

    def test_an_undated_item_never_reaches_the_board(self):
        assert not item(date_published="").on_board(TODAY)

    def test_beyond_the_archive_horizon_falls_out_of_both(self):
        ancient = item(date_published="2020-01-01")
        assert not ancient.on_board(TODAY)
        assert not ancient.in_archive(TODAY)

    def test_split_returns_both_newest_first(self):
        items = [
            item(date_published="2026-09-01"),
            item(date_published="2026-09-10"),
            item(date_published="2026-05-01"),
        ]
        board, archive = split_window(items, TODAY)
        assert [i.date_published for i in board] == ["2026-09-10", "2026-09-01"]
        assert [i.date_published for i in archive] == ["2026-05-01"]

    def test_nothing_is_deleted_by_splitting(self):
        """The brief: nothing is deleted, the board is just never a month deep."""
        items = [item(date_published="2026-09-10"), item(date_published="2026-05-01")]
        board, archive = split_window(items, TODAY)
        assert len(board) + len(archive) == len(items)


class TestRoundTrip:
    def test_dump_then_load_preserves_items(self):
        items = [item(), item(headline="Second", tags=["Sleep and fatigue"])]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "findings.json"
            dump(items, path)
            assert json.loads(path.read_text())["window_days"] == 30
            assert [i.headline for i in load(path)] == [i.headline for i in items]

    def test_the_removed_fields_are_absent(self):
        """Grades, caveats and the fetch-verified counter are gone by design."""
        keys = set(item().to_dict())
        assert not keys & {"grade", "caveat", "secondary", "verified", "fetch_verified"}
