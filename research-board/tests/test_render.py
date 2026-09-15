"""The rendered board.

Written against what would embarrass us in public: markup smuggled in through a
fetched headline, a removed field drifting back, a filter button that matches
the wrong tag by substring, and the visible cap silently swallowing the month.
"""

from __future__ import annotations

import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_research.models import BoardItem  # noqa: E402
from tactical_research.render import (  # noqa: E402
    VISIBLE_CAP,
    render_archive,
    render_board,
    render_card,
)

TODAY = date(2026, 9, 13)


def item(**kwargs):
    base = dict(
        headline="Army reissues the fitness test standard",
        blurb="What happened, who it affects, and why it matters.",
        primary_url="https://armypubs.army.mil/aft",
        date_published="2026-09-10",
        type="Policy",
        sector="MIL",
        tags=["Standards and tests"],
    )
    base.update(kwargs)
    return BoardItem(**base)


class TestCard:
    def test_shows_every_field_section_four_lists(self):
        html = render_card(item(coverage_urls=["https://www.militarytimes.com/a"]))
        assert "Army reissues the fitness test standard" in html
        assert "What happened, who it affects" in html
        assert "Standards and tests" in html
        assert ">Policy<" in html and ">MIL<" in html
        assert "10 Sep 2026" in html
        assert "https://armypubs.army.mil/aft" in html
        assert "Reporting (1 article)" in html

    def test_coverage_is_collapsed_not_listed_flat(self):
        html = render_card(item(coverage_urls=["https://www.police1.com/a", "https://www.ems1.com/b"]))
        assert "<details" in html and "Reporting (2 articles)" in html

    def test_no_coverage_means_no_reporting_block(self):
        assert "Reporting" not in render_card(item())

    def test_supersedes_links_back_to_the_earlier_item(self):
        html = render_card(item(supersedes="https://armypubs.army.mil/old"))
        assert "armypubs.army.mil/old" in html and "Replaces an earlier item" in html

    def test_a_headline_cannot_smuggle_markup_onto_the_page(self):
        # Headlines are written from documents fetched off the open internet.
        html = render_card(item(headline='<script>alert(1)</script>'))
        assert "<script>alert(1)</script>" not in html
        assert "&lt;script&gt;" in html

    def test_a_url_cannot_break_out_of_its_attribute(self):
        html = render_card(item(primary_url='https://x.mil/a" onmouseover="steal()'))
        assert 'onmouseover="steal()"' not in html
        assert "&quot;" in html

    def test_tags_are_separated_so_a_filter_cannot_match_a_substring(self):
        # "Men's health" is a substring of "Women's health". The separator is
        # what stops the men's filter from matching every women's health item.
        html = render_card(item(tags=["Women's health"]))
        values = re.search(r'data-tag="([^"]*)"', html).group(1)
        assert values.split("|") == ["Women&#x27;s health"]


class TestRemovedFields:
    """The brief removed these. They are the kind of thing that creeps back."""

    def test_page_carries_no_grades_caveats_or_counters(self):
        html = render_board([item()], today=TODAY)
        lowered = html.lower()
        for banned in ("evidence grade", "verify before citing", "secondary", "fetch-verified"):
            assert banned not in lowered


class TestBoardPage:
    def test_hot_block_comes_before_the_feed(self):
        items = [item(headline=f"h{n}", tags=["Sleep and fatigue"]) for n in range(3)]
        html = render_board(items, today=TODAY)
        assert html.index("Hot this month") < html.index("This month")

    def test_a_quiet_month_says_so_rather_than_inventing_a_trend(self):
        html = render_board([item()], today=TODAY)
        assert "No topic drew three or more independent items" in html

    def test_window_keeps_the_board_a_month_deep(self):
        fresh, stale = item(headline="fresh"), item(headline="stale", date_published="2026-01-02")
        html = render_board([fresh, stale], today=TODAY)
        assert "fresh" in html and "stale" not in html

    def test_feed_is_newest_first(self):
        old = item(headline="older", date_published="2026-09-01")
        new = item(headline="newer", date_published="2026-09-12")
        html = render_board([old, new], today=TODAY)
        assert html.index("newer") < html.index("older")

    def test_show_all_appears_only_past_the_cap(self):
        few = [item(headline=f"h{n}") for n in range(VISIBLE_CAP)]
        many = [item(headline=f"h{n}") for n in range(VISIBLE_CAP + 1)]
        # The script always mentions data-more; the button is what matters.
        assert 'class="more" data-more' not in render_board(few, today=TODAY)
        assert 'class="more" data-more' in render_board(many, today=TODAY)

    def test_every_item_is_in_the_dom_even_past_the_cap(self):
        # The cap is visual. Filtering has to reach the whole month, so the
        # overflow stays in the page rather than behind a second request.
        many = [item(headline=f"headline-{n}") for n in range(VISIBLE_CAP + 5)]
        html = render_board(many, today=TODAY)
        assert all(f"headline-{n}" in html for n in range(VISIBLE_CAP + 5))

    def test_filters_offer_only_values_the_month_actually_has(self):
        html = render_board([item(sector="MIL", type="Policy")], today=TODAY)
        assert 'data-value="MIL"' in html
        assert 'data-value="EMS"' not in html
        assert 'data-value="Research"' not in html

    def test_filters_cover_tag_type_and_sector(self):
        html = render_board([item()], today=TODAY)
        for facet in ("tag", "type", "sector"):
            assert f'data-facet="{facet}"' in html


class TestArchivePage:
    def test_holds_what_left_the_board_and_not_what_is_on_it(self):
        fresh = item(headline="fresh")
        old = item(headline="older", date_published="2026-06-01")
        html = render_archive([fresh, old], today=TODAY)
        assert "older" in html and "fresh" not in html

    def test_filterable_by_tag_and_month(self):
        old = item(headline="older", date_published="2026-06-01")
        html = render_archive([old], today=TODAY)
        assert 'data-facet="month"' in html and 'data-value="2026-06"' in html
        assert 'data-facet="tag"' in html

    def test_uncapped_because_the_archive_is_what_you_came_for(self):
        old = [item(headline=f"h{n}", date_published="2026-06-01") for n in range(VISIBLE_CAP + 5)]
        html = render_archive(old, today=TODAY)
        assert 'data-cap="0"' in html and 'class="more" data-more' not in html

    def test_beyond_twelve_months_falls_out_of_both_pages(self):
        ancient = item(headline="ancient", date_published="2024-01-01")
        assert "ancient" not in render_archive([ancient], today=TODAY)
        assert "ancient" not in render_board([ancient], today=TODAY)
