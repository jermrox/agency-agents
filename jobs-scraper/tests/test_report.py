"""Report tests: escaping, self-containment, well-formedness, and degradation.

The bar for this module is not "produces a page" -- it is "produces a page that
cannot be broken by its input and cannot phone home". Everything it renders came
from a third-party job feed, and the document gets opened on networks that block
most of the internet, so the tests concentrate on the four ways a naive
implementation goes wrong:

* an employer named ``Smith & Sons "Tactical" <script>`` turning into markup,
* a CDN stylesheet or web font silently making the page depend on the network,
* an empty or half-written insights dict producing broken markup or a crash,
* a section heading printed over data that is not there.

Well-formedness is checked with a real XML parser rather than a substring
search, because "the tag I expected is in the string" is not the same claim as
"a parser can read this document".
"""

from __future__ import annotations

import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.report import (  # noqa: E402
    DISCIPLINE_LABELS,
    RECENT_MONTHS,
    SERIES_DARK,
    SERIES_LIGHT,
    render_html,
    render_markdown,
)

# --------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------

HOSTILE_TITLE = 'Tactical S&C Coach <script>alert("xss")</script>'
HOSTILE_EMPLOYER = 'Smith & Sons "Tactical" <b>Performance</b>'


def insights(**overrides: Any) -> dict[str, Any]:
    """A fully-populated insights dict in the shape ``build_insights`` returns.

    Deliberately complete: the section-presence tests need every facet
    populated, because the renderer omits a section rather than printing an
    empty heading over it.
    """
    data: dict[str, Any] = {
        "generated_at": "2026-07-31T12:00:00+00:00",
        "totals": {
            "postings": 412,
            "employers": 34,
            "unique_jobs": 268,
            "with_salary": 190,
            "date_span": {
                "earliest": "2025-08-01T00:00:00+00:00",
                "latest": "2026-07-28T00:00:00+00:00",
            },
        },
        "by_employer": [
            {
                "name": "O2X Human Performance",
                "count": 41,
                "disciplines": ["strength-conditioning", "sports-medicine"],
                "median_salary": 92000.0,
            },
            {
                "name": "USASOC THOR3",
                "count": 22,
                "disciplines": ["sports-medicine"],
                "median_salary": None,
            },
        ],
        "by_discipline": [
            {
                "name": "strength-conditioning",
                "count": 120,
                "share": 0.48,
                "median_salary": 88000.0,
            },
            {
                "name": "sports-medicine",
                "count": 70,
                "share": 0.28,
                "median_salary": 95000.0,
            },
            {"name": "nutrition", "count": 30, "share": 0.12, "median_salary": 78000.0},
        ],
        "by_domain": [
            {"name": "military", "count": 180, "share": 0.70},
            {"name": "sof", "count": 90, "share": 0.35},
            {"name": "first-responder", "count": 24, "share": 0.09},
        ],
        "by_branch": [{"name": "Army", "count": 140}, {"name": "Navy", "count": 40}],
        "by_installation": [
            {"name": "Fort Liberty", "count": 38},
            {"name": "Joint Base Lewis-McChord", "count": 21},
            {"name": "Camp Lejeune", "count": 14},
        ],
        "by_state": [{"code": "NC", "count": 52}, {"code": "WA", "count": 30}],
        "certifications": [
            {"name": "CSCS", "count": 150, "share": 0.72},
            {"name": "TSAC-F", "count": 60, "share": 0.29},
            {"name": "ATC", "count": 44, "share": 0.21},
        ],
        "clearances": [
            {"name": "Secret", "count": 70},
            {"name": "TS/SCI", "count": 12},
        ],
        "salary": {
            "count": 190,
            "min": 42000.0,
            "max": 185000.0,
            "median": 89000.0,
            "p25": 76000.0,
            "p75": 104000.0,
            "by_discipline": {
                "strength-conditioning": {
                    "count": 100,
                    "min": 50000,
                    "max": 140000,
                    "median": 86000,
                    "p25": 74000,
                    "p75": 98000,
                },
                "sports-medicine": {
                    "count": 50,
                    "min": 60000,
                    "max": 160000,
                    "median": 98000,
                    "p25": 85000,
                    "p75": 115000,
                },
            },
        },
        "remote": {"count": 18, "share": 0.067},
        # Fourteen months, deliberately longer than the twelve the month bars
        # show, so the full-span sparkline has something extra to say.
        "timeline": [
            {"month": month, "count": count}
            for month, count in zip(
                [f"2025-{m:02d}" for m in range(6, 13)]
                + [f"2026-{m:02d}" for m in range(1, 8)],
                [2, 3, 4, 6, 5, 11, 8, 10, 14, 9, 22, 18, 25, 31],
            )
        ],
        "trends": {
            "window_days": 90,
            "pivot": "2026-04-29T00:00:00+00:00",
            "fastest_growing_employers": [
                {
                    "name": "O2X Human Performance",
                    "recent": 14,
                    "previous": 6,
                    "change": 8,
                }
            ],
            "emerging_certifications": [
                {"name": "TSAC-F", "recent": 22, "previous": 11, "change": 11}
            ],
        },
        "top_titles": [
            {"title": "Tactical Strength and Conditioning Facilitator", "count": 44},
            {"title": "Athletic Trainer", "count": 31},
        ],
    }
    data.update(overrides)
    return data


def hostile_insights() -> dict[str, Any]:
    """The same report where every third-party string is trying to be markup."""
    return insights(
        by_employer=[
            {
                "name": HOSTILE_EMPLOYER,
                "count": 41,
                "disciplines": ["strength-conditioning"],
                "median_salary": 92000.0,
            }
        ],
        top_titles=[{"title": HOSTILE_TITLE, "count": 44}],
        certifications=[{"name": "CSCS & TSAC-F", "count": 12, "share": 0.5}],
        by_installation=[{"name": 'Fort <Liberty> "Bragg"', "count": 9}],
        clearances=[{"name": 'Secret "or higher"', "count": 7}],
        by_branch=[{"name": "Army & Navy", "count": 5}],
    )


class _Collector(HTMLParser):
    """Minimal HTML parser: records tags and attributes for self-containment checks."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.tags: list[str] = []
        self.attrs: list[tuple[str, str, str]] = []
        self.text: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.tags.append(tag)
        for name, value in attrs:
            self.attrs.append((tag, name, value or ""))

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)

    def handle_data(self, data: str) -> None:
        self.text.append(data)


def parsed(markup: str) -> _Collector:
    collector = _Collector()
    collector.feed(markup)
    collector.close()
    return collector


def element_tree(markup: str) -> ET.Element:
    """Parse with a strict XML parser. Raises on anything malformed."""
    return ET.fromstring(markup)


def all_attrs(root: ET.Element) -> list[tuple[str, str, str]]:
    return [
        (element.tag, name, value)
        for element in root.iter()
        for name, value in element.attrib.items()
    ]


# --------------------------------------------------------------------------
# Well-formedness
# --------------------------------------------------------------------------


def test_html_parses_as_xml():
    """A strict parser must be able to read the whole document, doctype and all."""
    root = element_tree(render_html(insights()))
    assert root.tag == "html"


def test_html_parses_with_html_parser():
    collector = parsed(render_html(insights()))
    assert "html" in collector.tags
    assert "style" in collector.tags


def test_hostile_input_still_parses_as_xml():
    """The escaping claim only means something if a parser agrees with it."""
    root = element_tree(render_html(hostile_insights()))
    assert root.tag == "html"


def test_empty_insights_parses_as_xml():
    assert element_tree(render_html({})).tag == "html"


def test_head_declares_charset_and_viewport():
    root = element_tree(render_html(insights()))
    metas = {
        tuple(sorted(element.attrib.items()))
        for element in root.iter("meta")
    }
    charsets = [element.get("charset") for element in root.iter("meta")]
    viewports = [
        element.get("content")
        for element in root.iter("meta")
        if element.get("name") == "viewport"
    ]
    assert "utf-8" in charsets
    assert any("width=device-width" in (value or "") for value in viewports)
    assert metas  # sanity: the head is not empty


def test_document_starts_with_doctype_and_ends_with_html():
    markup = render_html(insights())
    assert markup.startswith("<!DOCTYPE html>")
    assert markup.rstrip().endswith("</html>")


def test_title_appears_in_head_and_masthead():
    markup = render_html(insights(), title="THOR3 Market Brief")
    root = element_tree(markup)
    assert root.find("./head/title").text == "THOR3 Market Brief"
    headings = [element.text for element in root.iter("h1")]
    assert "THOR3 Market Brief" in headings


def test_custom_title_is_escaped():
    markup = render_html(insights(), title='Brief & "Notes" <b>')
    assert "<b>" not in markup
    root = element_tree(markup)
    # The parser round-trips the escaped text back to the original characters.
    assert root.find("./head/title").text == 'Brief & "Notes" <b>'


# --------------------------------------------------------------------------
# Escaping
# --------------------------------------------------------------------------


def test_hostile_title_is_not_emitted_as_a_script_tag():
    markup = render_html(hostile_insights())
    assert "<script" not in markup.lower()
    assert "&lt;script&gt;" in markup
    assert "script" not in parsed(markup).tags


def test_hostile_employer_name_survives_as_text():
    markup = render_html(hostile_insights())
    root = element_tree(markup)
    texts = [element.text or "" for element in root.iter()]
    assert any(HOSTILE_EMPLOYER in text for text in texts)


def test_hostile_employer_does_not_create_a_bold_element():
    """``<b>Performance</b>`` in a feed must stay characters, not become markup."""
    assert "b" not in parsed(render_html(hostile_insights())).tags


def test_ampersands_are_escaped():
    markup = render_html(hostile_insights())
    # Every bare "&" must be the start of an entity reference, never a raw one.
    for match in re.finditer(r"&(?!amp;|lt;|gt;|quot;|#\d+;|#x[0-9a-fA-F]+;)", markup):
        pytest.fail(f"unescaped ampersand at offset {match.start()}")


def test_discipline_label_ampersand_is_escaped_not_raw():
    """The built-in labels contain an ampersand too, not just the feed data."""
    assert "&" in DISCIPLINE_LABELS["strength-conditioning"]
    markup = render_html(insights())
    assert "Strength &amp; Conditioning" in markup
    assert "Strength & Conditioning" not in markup


def test_quotes_in_attribute_values_cannot_break_out():
    """A double quote in a name must not close the title attribute it lands in."""
    markup = render_html(hostile_insights())
    root = element_tree(markup)
    titles = [value for _, name, value in all_attrs(root) if name == "title"]
    assert any('"Bragg"' in value for value in titles)
    # If breakout had happened, the parser would have invented extra attributes.
    assert all(name.isidentifier() or "-" in name for _, name, _ in all_attrs(root))


def test_angle_brackets_in_installation_name_are_escaped():
    markup = render_html(hostile_insights())
    assert "Fort <Liberty>" not in markup
    assert "Fort &lt;Liberty&gt;" in markup
    assert "&quot;Bragg&quot;" in markup


def test_style_attributes_never_contain_third_party_text():
    """Only numbers this module computed itself are allowed into CSS."""
    root = element_tree(render_html(hostile_insights()))
    styles = [value for _, name, value in all_attrs(root) if name == "style"]
    assert styles  # the bars exist
    allowed = re.compile(
        r"^(?:(?:width|height|left|background):\s*[-0-9a-z.%()\s]+;?)+$"
    )
    for style in styles:
        assert allowed.match(style), style


# --------------------------------------------------------------------------
# Self-containment: the document must never touch the network
# --------------------------------------------------------------------------


def test_no_absolute_urls_anywhere_in_the_document():
    markup = render_html(insights())
    assert "http://" not in markup
    assert "https://" not in markup


def test_no_absolute_urls_in_the_empty_state_either():
    markup = render_html({})
    assert "http://" not in markup
    assert "https://" not in markup


def test_no_fetching_attributes_exist():
    """No src, href, or any other attribute a browser would resolve."""
    root = element_tree(render_html(insights()))
    fetching = {
        "src",
        "srcset",
        "href",
        "action",
        "data",
        "poster",
        "background",
        "formaction",
        "ping",
        "codebase",
    }
    offenders = [
        (tag, name, value)
        for tag, name, value in all_attrs(root)
        if name.split("}")[-1].lower() in fetching
    ]
    assert offenders == []


def test_no_remote_capable_elements_exist():
    tags = set(parsed(render_html(insights())).tags)
    assert tags.isdisjoint({"script", "link", "iframe", "img", "object", "embed", "video", "audio", "form"})


def test_a_url_inside_feed_text_stays_inert_text():
    """Feeds do put URLs in titles. Text is not a fetch -- but it must stay text.

    The blanket "no http:// in the document" assertion cannot apply here, so
    this checks the guarantee that actually matters: nothing in the document
    resolves, whatever the feed put in it.
    """
    linky = insights(
        top_titles=[{"title": "Coach - apply at https://evil.example/x", "count": 4}],
        by_employer=[
            {
                "name": '<a href="https://evil.example">O2X</a>',
                "count": 3,
                "disciplines": [],
                "median_salary": None,
            }
        ],
    )
    markup = render_html(linky)
    root = element_tree(markup)
    assert "a" not in parsed(markup).tags
    assert [
        (tag, name)
        for tag, name, _ in all_attrs(root)
        if name.split("}")[-1].lower() in {"src", "href", "action", "poster", "ping"}
    ] == []
    assert "&lt;a href=&quot;https://evil.example&quot;&gt;" in markup


def test_stylesheet_has_no_imports_or_url_references():
    markup = render_html(insights())
    assert "@import" not in markup
    assert "url(" not in markup
    assert "@font-face" not in markup


def test_stylesheet_is_inline_and_present():
    root = element_tree(render_html(insights()))
    styles = list(root.iter("style"))
    assert len(styles) == 1
    assert ".bar-fill" in (styles[0].text or "")


# --------------------------------------------------------------------------
# Theme, responsiveness, palette
# --------------------------------------------------------------------------


def test_dark_mode_is_supported_by_media_query_and_theme_attribute():
    css = element_tree(render_html(insights())).find(".//style").text or ""
    assert "@media (prefers-color-scheme: dark)" in css
    assert '[data-theme="dark"]' in css
    assert '[data-theme="light"]' in css


def hex_tokens(css: str) -> list[str]:
    """Every hex color in the stylesheet, expanded to six digits.

    Matching on ``#000\\b`` misses ``#0000`` -- a digit is a word character, so
    the boundary never fires -- which is exactly the shape a careless edit
    produces. Tokenize and normalize instead of pattern-matching a prefix.
    """
    out = []
    for token in re.findall(r"#([0-9a-fA-F]{3,8})\b", css):
        digits = token.lower()
        if len(digits) in (3, 4):
            digits = "".join(char * 2 for char in digits)
        out.append(digits[:6])
    return out


def test_no_pure_black_or_pure_white_in_the_palette():
    """Pure #000 on #fff is the harshest possible pairing; the brief forbids it."""
    css = element_tree(render_html(insights())).find(".//style").text or ""
    tokens = hex_tokens(css)
    assert tokens, "no colors found -- the tokenizer, not the palette, is broken"
    assert "000000" not in tokens
    assert "ffffff" not in tokens


def test_palette_css_is_generated_from_the_python_constants():
    """The validated palette and the shipped stylesheet must not be able to drift.

    Hand-copying the hues into the CSS is how a palette that passed the
    colorblind checks once stops being the palette that ships.
    """
    css = element_tree(render_html(insights())).find(".//style").text or ""
    light = css.split("@media", 1)[0]
    dark = css.split(':root[data-theme="dark"]', 1)[1]
    for index, value in enumerate(SERIES_LIGHT, 1):
        assert f"--s{index}: {value};" in light
    for index, value in enumerate(SERIES_DARK, 1):
        assert f"--s{index}: {value};" in dark
    # And the count matches: no orphan slot the constants no longer define.
    assert len(re.findall(r"--s\d+:", light)) == len(SERIES_LIGHT)


def test_wide_table_scrolls_in_its_own_container():
    markup = render_html(insights())
    css = element_tree(markup).find(".//style").text or ""
    assert ".scroll { overflow-x: auto; }" in css
    root = element_tree(markup)
    tables = [
        element
        for element in root.iter("table")
    ]
    assert tables
    for table in tables:
        # Every table must sit inside a scroll container, or a phone gets a
        # sideways-scrolling page instead of a sideways-scrolling table.
        parents = [
            element
            for element in root.iter()
            if table in list(element)
        ]
        assert any("scroll" in (parent.get("class") or "") for parent in parents)


def test_responsive_breakpoint_exists():
    css = element_tree(render_html(insights())).find(".//style").text or ""
    assert "@media (max-width:" in css


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------

REQUIRED_SECTIONS = (
    "overview",
    "movement",
    "employers",
    "disciplines",
    "credentials",
    "salary",
    "geography",
    "titles",
)


@pytest.mark.parametrize("section_id", REQUIRED_SECTIONS)
def test_each_required_section_is_present(section_id: str):
    root = element_tree(render_html(insights()))
    ids = {element.get("id") for element in root.iter("section")}
    assert section_id in ids


def test_headline_tiles_carry_the_top_line_numbers():
    markup = render_html(insights())
    assert "268" in markup  # unique jobs, not the 412 archived records
    assert "$89,000" in markup  # median annualized pay
    assert "34" in markup  # employers


def test_discipline_bars_use_a_stable_hue_per_discipline():
    """The same discipline is the same hue in the mix chart and the pay bands."""
    root = element_tree(render_html(insights()))
    styles = [value for _, name, value in all_attrs(root) if name == "style"]
    hues = {
        match.group(1)
        for style in styles
        for match in [re.search(r"background:var\((--s\d)\)", style)]
        if match
    }
    # Three disciplines in the mix, two of which also have pay bands, so the
    # colored marks must resolve to exactly three distinct slots.
    assert len(hues) == 3


def test_salary_bands_share_one_axis():
    """A per-row scale would make every discipline look identically paid."""
    markup = render_html(insights())
    root = element_tree(markup)
    ranges = [
        element
        for element in root.iter("span")
        if "band-range" in (element.get("class") or "")
    ]
    assert len(ranges) == 2
    lefts = {element.get("style") for element in ranges}
    assert len(lefts) == 2  # the two bands do not start in the same place


def test_timeline_renders_one_column_per_recent_month():
    root = element_tree(render_html(insights()))
    months = [
        element
        for element in root.iter("div")
        if (element.get("class") or "") == "month"
    ]
    assert len(months) == RECENT_MONTHS


def svg_count(markup: str) -> int:
    """SVG elements actually rendered -- not CSS rules mentioning their classes."""
    return len(list(element_tree(markup).iter("svg")))


def test_sparkline_is_omitted_when_it_would_duplicate_the_month_bars():
    short = insights(
        timeline=[{"month": f"2026-{m:02d}", "count": m} for m in range(1, 6)]
    )
    assert svg_count(render_html(short)) == 0
    assert svg_count(render_html(insights())) == 1


def test_sparkline_is_a_local_svg_with_no_namespace_url():
    markup = render_html(insights())
    svg = element_tree(markup).find(".//svg")
    assert svg is not None
    assert svg.find("polyline") is not None
    assert "xmlns" not in markup  # a namespace URL would smuggle a URL into the page


def test_trend_lists_report_before_and_after():
    markup = render_html(insights())
    assert "6 to 14" in markup  # employer posting rate
    assert "11 to 22" in markup  # emerging certification


# --------------------------------------------------------------------------
# Degradation
# --------------------------------------------------------------------------


def test_empty_dict_renders_the_no_data_state():
    markup = render_html({})
    root = element_tree(markup)
    ids = {element.get("id") for element in root.iter("section")}
    assert ids == {"empty-state"}
    assert "No data yet" in markup


def test_zeroed_insights_renders_the_no_data_state():
    zeroed = {
        "generated_at": "2026-07-31T12:00:00+00:00",
        "totals": {
            "postings": 0,
            "employers": 0,
            "unique_jobs": 0,
            "with_salary": 0,
            "date_span": {"earliest": None, "latest": None},
        },
        "by_employer": [],
        "by_discipline": [],
        "by_domain": [],
        "by_branch": [],
        "by_installation": [],
        "by_state": [],
        "certifications": [],
        "clearances": [],
        "salary": {
            "count": 0,
            "min": None,
            "max": None,
            "median": None,
            "p25": None,
            "p75": None,
            "by_discipline": {},
        },
        "remote": {"count": 0, "share": 0.0},
        "timeline": [],
        "trends": {
            "window_days": 90,
            "pivot": None,
            "fastest_growing_employers": [],
            "emerging_certifications": [],
        },
        "top_titles": [],
    }
    markup = render_html(zeroed)
    assert element_tree(markup).tag == "html"
    assert "No data yet" in markup
    assert "No data yet" in render_markdown(zeroed)


def test_sections_with_no_data_are_omitted_rather_than_printed_empty():
    """An empty heading reads as "the field has none", which is not what it means."""
    thin = insights(certifications=[], clearances=[], by_state=[], by_installation=[], by_branch=[])
    root = element_tree(render_html(thin))
    ids = {element.get("id") for element in root.iter("section")}
    assert "credentials" not in ids
    assert "geography" not in ids
    assert "employers" in ids  # the sections that do have data survive


def test_partial_insights_without_totals_still_renders_its_sections():
    """An older or hand-edited dict must not be mistaken for an empty corpus."""
    partial = {"by_employer": [{"name": "POTFF", "count": 3, "disciplines": []}]}
    markup = render_html(partial)
    assert element_tree(markup).tag == "html"
    assert "POTFF" in markup
    assert "No data yet" not in markup


@pytest.mark.parametrize(
    "junk",
    [
        None,
        [],
        "not a dict",
        0,
        {"totals": "wrong type", "by_employer": "wrong type", "timeline": 7},
        {"by_discipline": [None, 42, {"name": None}], "salary": None},
        {"totals": {"postings": "many", "unique_jobs": float("nan")}},
        # An integer with more magnitude than a float can hold. json.load
        # produces these happily, and math.isfinite raises rather than
        # returning False on them.
        {"totals": {"postings": 10**400, "unique_jobs": 3}},
        {"by_employer": [{"name": "X", "count": 10**400, "disciplines": []}]},
        {"timeline": [{"month": "2026-01", "count": 10**400}]},
        {"by_discipline": [{"name": "nutrition", "count": 1, "share": 10**400}]},
        # ``disciplines`` arriving as something that is not a list of slugs.
        {"by_employer": [{"name": "X", "count": 2, "disciplines": 5}]},
        {"by_employer": [{"name": "X", "count": 2, "disciplines": None}]},
        {"by_employer": [{"name": "X", "count": 2, "disciplines": [["a"], 3, None]}]},
        {"salary": {"count": 2, "by_discipline": {7: {"p25": 1, "median": 2, "p75": 3}}}},
        {"salary": {"count": 2, "by_discipline": [1, 2, 3]}},
        {"remote": {"count": "lots", "share": "some"}},
        {"trends": {"window_days": -5, "fastest_growing_employers": "nope"}},
    ],
)
def test_junk_input_never_raises(junk: Any):
    markup = render_html(junk)
    assert element_tree(markup).tag == "html"
    assert render_markdown(junk).startswith("# ")


def test_astronomical_integers_are_dropped_rather_than_crashing():
    """json.load returns unbounded ints; float() cannot hold them."""
    huge = insights(totals={"postings": 10**400, "unique_jobs": 10**400, "employers": 4})
    markup = render_html(huge)
    assert element_tree(markup).tag == "html"
    # Unreadable totals fall back to zero, but the rest of the corpus survives.
    assert "O2X Human Performance" in markup


def test_a_bare_string_of_disciplines_is_one_slug_not_a_list_of_letters():
    """``str`` is iterable; iterating it yields characters, not slugs."""
    text = render_markdown(
        insights(
            by_employer=[
                {
                    "name": "POTFF",
                    "count": 2,
                    "disciplines": "strength-conditioning",
                    "median_salary": None,
                }
            ]
        )
    )
    row = next(line for line in text.splitlines() if line.startswith("| POTFF"))
    assert "Strength &amp; Conditioning" not in row
    assert "Strength & Conditioning" in row
    assert ", T" not in row  # "S, T" is what per-character iteration produces


def test_negative_counts_never_draw_outside_the_chart():
    """A negative tally is corrupt input, not a small number."""
    corrupt = insights(
        by_discipline=[{"name": "nutrition", "count": -5, "share": -0.2}],
        timeline=[{"month": f"2026-{m:02d}", "count": -m} for m in range(1, 14)],
    )
    markup = render_html(corrupt)
    root = element_tree(markup)
    for value in [v for _, name, v in all_attrs(root) if name == "style"]:
        for number in re.findall(r"(?:width|height|left):\s*(-?[\d.]+)%", value):
            assert 0.0 <= float(number) <= 100.0, value
    for points in [
        element.get("points") or "" for element in root.iter("polyline")
    ]:
        for pair in points.split():
            x, y = (float(part) for part in pair.split(","))
            assert 0.0 <= x <= 100.0 and 0.0 <= y <= 30.0, pair


def test_bar_widths_stay_within_the_track_on_ordinary_data():
    root = element_tree(render_html(insights()))
    widths = [
        float(match.group(1))
        for _, name, value in all_attrs(root)
        if name == "style"
        for match in [re.search(r"width:\s*([\d.]+)%", value)]
        if match
    ]
    assert widths
    assert all(0.0 <= width <= 100.0 for width in widths)
    assert max(widths) == pytest.approx(100.0)  # the peak fills its track


def test_pay_section_survives_a_corpus_with_no_per_discipline_bands():
    """by_discipline is empty whenever salaried postings carry no discipline tag.

    Dropping the whole section then hides the only pay evidence there is.
    """
    no_bands = insights(
        salary={
            "count": 190,
            "min": 42000.0,
            "max": 185000.0,
            "median": 89000.0,
            "p25": 76000.0,
            "p75": 104000.0,
            "by_discipline": {},
        }
    )
    markup = render_html(no_bands)
    ids = {element.get("id") for element in element_tree(markup).iter("section")}
    assert "salary" in ids
    for figure in ("$42,000", "$76,000", "$89,000", "$104,000", "$185,000"):
        assert figure in markup


def test_html_and_markdown_agree_on_the_pay_spread():
    """One corpus, two renderings: they must not state different distributions."""
    data = insights()
    text, markup = render_markdown(data), render_html(data)
    for figure in ("$42,000", "$76,000", "$89,000", "$104,000", "$185,000"):
        assert figure in text, figure
        assert figure in markup, figure


def test_a_corpus_with_only_salary_data_is_not_called_empty():
    only_pay = {
        "salary": {
            "count": 5,
            "min": 30000,
            "max": 90000,
            "median": 50000,
            "p25": 40000,
            "p75": 60000,
            "by_discipline": {},
        }
    }
    markup = render_html(only_pay)
    assert "No data yet" not in markup
    assert "$50,000" in markup
    assert "No data yet" not in render_markdown(only_pay)


def test_a_corpus_with_only_remote_data_is_not_called_empty():
    markup = render_html({"remote": {"count": 4, "share": 0.5}})
    assert "No data yet" not in markup
    assert "50%" in markup


def test_salary_band_without_a_usable_name_is_dropped():
    """A colored stripe a reader cannot attribute to anything is worse than none."""
    nameless = insights(
        salary={
            "count": 4,
            "median": 90000,
            "p25": 80000,
            "p75": 100000,
            "by_discipline": {
                "   ": {"count": 4, "p25": 80000, "median": 90000, "p75": 100000}
            },
        }
    )
    root = element_tree(render_html(nameless))
    assert [
        element
        for element in root.iter("span")
        if "band-range" in (element.get("class") or "")
    ] == []


def test_month_caption_names_the_span_the_column_labels_omit():
    """Columns are labeled "07"; without a year a window across New Year is unreadable."""
    markup = render_html(insights())
    blurbs = [
        element.text or ""
        for element in element_tree(markup).iter("p")
        if "blurb" in (element.get("class") or "")
    ]
    caption = next(blurb for blurb in blurbs if "calendar month" in blurb)
    assert "2025-08" in caption and "2026-07" in caption


def test_unicode_names_round_trip_intact():
    exotic = insights(
        by_employer=[
            {
                "name": "Fördé Tactisk Ytelse — Пример",
                "count": 3,
                "disciplines": ["nutrition"],
                "median_salary": None,
            }
        ]
    )
    markup = render_html(exotic)
    root = element_tree(markup)
    texts = [element.text or "" for element in root.iter()]
    assert any("Fördé Tactisk Ytelse" in text for text in texts)
    assert "Fördé Tactisk Ytelse" in render_markdown(exotic)


def test_very_long_names_do_not_break_the_document():
    monster = "Strength " * 4000
    huge = insights(
        by_employer=[
            {"name": monster, "count": 3, "disciplines": [], "median_salary": None}
        ],
        top_titles=[{"title": monster, "count": 1}],
    )
    markup = render_html(huge)
    assert element_tree(markup).tag == "html"
    assert render_markdown(huge).count("\n") > 10


def test_salary_band_with_scrambled_percentiles_is_dropped():
    """p75 below p25 is a corrupt record, not a distribution worth drawing."""
    scrambled = insights(
        salary={
            "count": 4,
            "min": 1,
            "max": 2,
            "median": 90000,
            "p25": 120000,
            "p75": 60000,
            "by_discipline": {
                "nutrition": {"count": 4, "median": 90000, "p25": 120000, "p75": 60000}
            },
        }
    )
    root = element_tree(render_html(scrambled))
    drawn = [
        element
        for element in root.iter("span")
        if "band-range" in (element.get("class") or "")
    ]
    assert drawn == []


def test_single_month_timeline_does_not_crash_or_claim_movement():
    single = insights(timeline=[{"month": "2026-07", "count": 5}])
    markup = render_html(single)
    assert element_tree(markup).tag == "html"
    assert "Month over month" in markup
    assert "against 2026-06" not in markup


def test_growth_from_zero_is_not_reported_as_a_percentage():
    """A jump from zero is not a percentage; claiming one destroys credibility."""
    from_zero = insights(
        timeline=[{"month": "2026-06", "count": 0}, {"month": "2026-07", "count": 9}]
    )
    markup = render_html(from_zero)
    assert "from none in 2026-06" in markup
    assert "inf" not in markup.lower()
    assert "from none in 2026-06" in render_markdown(from_zero)


def test_all_zero_timeline_renders_without_dividing_by_zero():
    flat = insights(
        timeline=[{"month": f"2026-{m:02d}", "count": 0} for m in range(1, 8)]
    )
    markup = render_html(flat)
    root = element_tree(markup)
    columns = [
        element
        for element in root.iter("div")
        if (element.get("class") or "") == "month"
    ]
    assert len(columns) == 7
    # Every bar computes to a real zero height rather than a NaN or a crash.
    heights = [
        element.get("style")
        for element in root.iter("span")
        if "month-fill" in (element.get("class") or "")
    ]
    assert heights == ["height:0.00%"] * 7
    assert "nan" not in markup.lower()


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------


def test_markdown_has_a_single_top_level_heading():
    lines = render_markdown(insights()).splitlines()
    assert [line for line in lines if line.startswith("# ")] == [
        "# Tactical Human Performance Job Market"
    ]


def test_markdown_sections_are_second_level_headings():
    headings = [
        line for line in render_markdown(insights()).splitlines() if line.startswith("## ")
    ]
    assert headings[0] == "## Headline"
    for expected in (
        "## Month over month",
        "## Who is hiring",
        "## Discipline mix",
        "## Credentials in demand",
        "## What it pays",
        "## Where the work is",
        "## Most common titles",
    ):
        assert expected in headings


def test_markdown_tables_are_well_formed():
    """Every table needs a header row, a delimiter row, and consistent arity."""
    lines = render_markdown(insights()).splitlines()
    tables = 0
    for index, line in enumerate(lines):
        if not re.fullmatch(r"\|(?:---\|)+", line):
            continue
        tables += 1
        columns = line.count("|") - 1
        header = lines[index - 1]
        assert header.startswith("| ") and header.count("|") - 1 == columns
        for row in lines[index + 1 :]:
            if not row.startswith("|"):
                break
            assert row.count("|") - 1 == columns
    assert tables >= 5


def test_markdown_escapes_pipes_in_third_party_names():
    """A pipe in an employer name would otherwise split the row into a new column."""
    piped = insights(
        by_employer=[
            {
                "name": "Fire | Rescue Systems",
                "count": 3,
                "disciplines": [],
                "median_salary": None,
            }
        ]
    )
    text = render_markdown(piped)
    assert r"Fire \| Rescue Systems" in text
    row = next(line for line in text.splitlines() if "Rescue Systems" in line)
    assert row.count("|") - row.count(r"\|") - 1 == 4


def test_markdown_leads_with_headline_numbers():
    text = render_markdown(insights())
    headline = text.split("## Headline", 1)[1].split("## ", 1)[0]
    assert "268" in headline
    assert "34" in headline
    assert "$89,000" in headline


def test_markdown_reports_month_over_month_movement():
    text = render_markdown(insights())
    assert "up +6" in text
    assert "25 to 31" in text


def test_markdown_includes_a_timeline_bar_block():
    text = render_markdown(insights())
    assert text.count("```") == 2
    block = text.split("```")[1]
    assert "2026-07" in block
    assert "#" in block


def test_markdown_annualization_caveat_is_stated():
    """A median that silently mixes hourly and annual pay is worse than none."""
    assert "annualized" in render_markdown(insights())


def test_markdown_states_the_share_denominator():
    text = render_markdown(insights())
    assert "do not sum to 100%" in text
    assert "out of jobs that name any certification" in text


def test_markdown_ends_with_exactly_one_newline():
    text = render_markdown(insights())
    assert text.endswith("\n")
    assert not text.endswith("\n\n")


def test_markdown_omits_sections_with_no_data():
    thin = insights(top_titles=[], certifications=[], clearances=[])
    text = render_markdown(thin)
    assert "## Most common titles" not in text
    assert "## Credentials in demand" not in text
    assert "## Who is hiring" in text


def test_markdown_collapses_newlines_inside_a_table_cell():
    """A newline in a scraped employer name would end the table row early."""
    wrapped = insights(
        by_employer=[
            {
                "name": "O2X\nHuman\r\nPerformance",
                "count": 3,
                "disciplines": [],
                "median_salary": None,
            }
        ]
    )
    text = render_markdown(wrapped)
    row = next(
        line for line in text.splitlines() if line.startswith("| O2X")
    )
    assert row == "| O2X Human Performance | 3 | - | - |"


def test_hostile_strings_do_not_corrupt_markdown_table_structure():
    """Brackets and quotes stay literal in Markdown, but must not shift columns."""
    text = render_markdown(hostile_insights())
    assert HOSTILE_EMPLOYER in text
    row = next(line for line in text.splitlines() if "Smith & Sons" in line)
    assert row.count("|") - row.count(r"\|") - 1 == 4


def test_markdown_reports_the_syndication_gap():
    text = render_markdown(insights())
    assert "144 of 412" in text  # 412 records collapse to 268 jobs


def test_renderers_agree_on_the_headline_numbers():
    """Two renderings of one corpus must never state different totals."""
    data = insights()
    text = render_markdown(data)
    markup = render_html(data)
    for number in ("268", "34", "$89,000"):
        assert number in text
        assert number in markup


def test_no_emoji_in_either_rendering():
    """House rule, and a briefing forwarded to a .mil inbox should stay plain."""
    for output in (render_markdown(insights()), render_html(insights())):
        assert not any(ord(char) > 0x2100 for char in output), "non-plain glyph emitted"
