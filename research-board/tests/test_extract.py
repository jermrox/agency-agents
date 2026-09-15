"""Reading listing pages and primary documents.

The sweep's quality is decided here. A generous link reader fills the board with
navigation chrome; a generous date reader lands items in the wrong month; and a
generous readability check invents blurbs for pages that returned nothing.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_research.extract import EXCERPT_CHARS, document, links  # noqa: E402

BASE = "https://www.usfa.fema.gov/news/"


def listing(*anchors):
    return "<html><body>" + "".join(anchors) + "</body></html>"


class TestLinks:
    def test_resolves_relative_hrefs_against_the_source(self):
        html = listing('<a href="/reports/firefighter-fatalities-2026">Firefighter fatalities report 2026</a>')
        found = links(html, BASE)
        assert found[0].url == "https://www.usfa.fema.gov/reports/firefighter-fatalities-2026"

    def test_drops_navigation_chrome(self):
        html = listing(
            '<a href="/a">Skip to main content</a>',
            '<a href="/b">Accessibility statement here</a>',
            '<a href="/c">Firefighter fatalities report 2026</a>',
        )
        assert [link.title for link in links(html, BASE)] == ["Firefighter fatalities report 2026"]

    def test_drops_links_too_short_to_be_a_headline(self):
        html = listing('<a href="/a">More</a>', '<a href="/b">Wildland pack test standard revised</a>')
        assert len(links(html, BASE)) == 1

    def test_ignores_anchors_mailto_and_javascript(self):
        html = listing(
            '<a href="#main">Jump to the main content area</a>',
            '<a href="mailto:x@y.gov">Email the program office today</a>',
            '<a href="javascript:void(0)">Open the menu for more options</a>',
        )
        assert links(html, BASE) == []

    def test_refuses_plain_http(self):
        html = listing('<a href="http://insecure.example.com/x">A report about firefighter injuries</a>')
        assert links(html, BASE) == []

    def test_one_link_listed_twice_is_one_link(self):
        html = listing(
            '<a href="/a">Firefighter fatalities report 2026</a>',
            '<a href="/a">Firefighter fatalities report 2026</a>',
        )
        assert len(links(html, BASE)) == 1

    def test_strips_markup_out_of_link_text(self):
        html = listing('<a href="/a"><span>Firefighter</span> fatalities report 2026</a>')
        assert links(html, BASE)[0].title == "Firefighter fatalities report 2026"


class TestDocument:
    def test_prefers_the_heading_over_the_tab_title(self):
        # A tab title carries the site name; the h1 is the document's own.
        html = "<html><head><title>USFA | Reports</title></head><body><h1>Firefighter Fatalities in 2026</h1></body></html>"
        assert document(html).title == "Firefighter Fatalities in 2026"

    def test_falls_back_to_the_tab_title(self):
        html = "<html><head><title>Firefighter Fatalities in 2026</title></head><body><p>x</p></body></html>"
        assert document(html).title == "Firefighter Fatalities in 2026"

    def test_reads_a_publication_date_from_metadata(self):
        html = '<html><head><meta property="article:published_time" content="2026-09-01T12:00:00Z"></head><body></body></html>'
        assert document(html).published == "2026-09-01"

    def test_reads_a_date_from_a_time_tag(self):
        html = '<html><body><time datetime="2026-09-01">1 September 2026</time></body></html>'
        assert document(html).published == "2026-09-01"

    def test_an_unreadable_date_is_left_blank_rather_than_guessed(self):
        # A wrong date lands the item in the wrong month. Blank sends it to the
        # archive, which is recoverable; a guess is not.
        html = '<html><body><time datetime="sometime last spring">x</time></body></html>'
        assert document(html).published == ""

    def test_a_nonsense_year_is_rejected(self):
        html = '<html><body><time datetime="0001-01-01">x</time></body></html>'
        assert document(html).published == ""

    def test_strips_scripts_styles_and_chrome_from_the_excerpt(self):
        html = (
            "<html><body><nav>Home Contact About</nav>"
            "<script>var tracking = 'nav noise';</script>"
            "<h1>Title</h1><p>The actual finding.</p><footer>Privacy</footer></body></html>"
        )
        excerpt = document(html).excerpt
        assert "The actual finding." in excerpt
        assert "tracking" not in excerpt and "Privacy" not in excerpt

    def test_excerpt_is_capped(self):
        html = "<html><body><h1>T</h1><p>" + ("word " * 5000) + "</p></body></html>"
        assert len(document(html).excerpt) <= EXCERPT_CHARS


class TestReadability:
    """The check that stops a blurb being written from nothing."""

    def test_a_real_document_is_readable(self):
        html = "<html><body><h1>Firefighter Fatalities in 2026</h1><p>" + ("finding " * 60) + "</p></body></html>"
        assert document(html).is_readable

    def test_a_javascript_shell_is_not(self):
        html = '<html><head><title>Loading…</title></head><body><div id="root"></div><script>go()</script></body></html>'
        assert not document(html).is_readable

    def test_a_page_with_a_title_and_no_body_is_not(self):
        html = "<html><head><title>Report</title></head><body><p>See attached.</p></body></html>"
        assert not document(html).is_readable

    def test_a_page_with_body_and_no_title_is_not(self):
        html = "<html><body><p>" + ("text " * 60) + "</p></body></html>"
        assert not document(html).is_readable
