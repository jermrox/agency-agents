"""Association career-center adapter tests.

There is no outbound network here, so every test drives the adapter through a
fake ``fetch`` over payload shapes matching what YourMembership / Community
Brands, Naylor CareerHub, and Boxwood emit -- the same feed and JSON envelopes
the NSCA, NATA, ACSM, CSCCa, AASP, APTA and SCAN boards run on.
"""

from __future__ import annotations

import io
import sys
import tokenize
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from tactical_jobs.sources.boards import (  # noqa: E402
    ASSOCIATION_BOARDS,
    BOARD_SOURCES,
    DEFAULT_DETAIL_LIMIT,
    DEFAULT_MAX_ITEMS,
    DETAIL_RETRIES,
    AssociationBoardSource,
    KnownBoardsSource,
    detect_payload_kind,
    extract_detail_text,
    json_records,
    local_name,
    looks_like_location,
    parse_listing_title,
)

FEED_URL = "https://careers.nsca.com/jobs/feed"
JSON_URL = "https://careers.nsca.com/jobs/search/results?format=json"
DETAIL_URL = "https://careers.nsca.com/jobs/12345/detail"


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------


def _item(
    title,
    *,
    link=DETAIL_URL,
    guid=None,
    description="<p>See the full posting for details.</p>",
    pub="Mon, 20 Jul 2026 14:05:00 GMT",
    extra="",
):
    guid_xml = f'<guid isPermaLink="false">{guid}</guid>' if guid else ""
    link_xml = f"<link>{link}</link>" if link else ""
    title_xml = f"<title>{title}</title>" if title else ""
    return (
        "<item>"
        f"{title_xml}{link_xml}{guid_xml}"
        f"<pubDate>{pub}</pubDate>"
        f"<description><![CDATA[{description}]]></description>"
        f"{extra}"
        "</item>"
    )


def _rss(*items):
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<rss version="2.0" '
        'xmlns:content="http://purl.org/rss/1.0/modules/content/" '
        'xmlns:dc="http://purl.org/dc/elements/1.1/"><channel>'
        "<title>NSCA Career Center</title>"
        "<link>https://careers.nsca.com/jobs</link>"
        + "".join(items)
        + "</channel></rss>"
    ).encode()


ATOM = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    '<feed xmlns="http://www.w3.org/2005/Atom">'
    "<title>NATA Career Center</title>"
    "<entry>"
    "<title>Athletic Trainer - Camp Lejeune MCCS - Jacksonville, NC</title>"
    '<link rel="alternate" href="https://careers.nata.org/job/778"/>'
    "<id>urn:nata:778</id>"
    "<updated>2026-07-11T09:00:00Z</updated>"
    "<summary>Support Marine Corps tactical athletes. BOC certification required.</summary>"
    "</entry>"
    "</feed>"
).encode()


JSON_PAYLOAD = b"""
{
  "totalResults": 2,
  "pageSize": 25,
  "results": [
    {
      "jobId": 88231,
      "jobTitle": "Human Performance Program Manager",
      "companyName": "Leidos",
      "city": "Fort Bragg",
      "state": "NC",
      "jobUrl": "/jobs/88231/human-performance-program-manager",
      "postedDate": "2026-07-18T00:00:00",
      "jobDescription": "<p>Lead an embedded USASOC THOR3 team.</p>",
      "requirements": "<ul><li>CSCS required</li><li>Active Secret clearance</li></ul>",
      "category": "Tactical Strength and Conditioning",
      "salaryRange": "$95,000 - $120,000"
    },
    {
      "jobId": 88232,
      "jobTitle": "Performance Dietitian",
      "companyName": "Naval Special Warfare Command",
      "location": "Coronado, CA",
      "jobUrl": "https://careers.nsca.com/jobs/88232/performance-dietitian",
      "postedDate": "2026-07-19T00:00:00",
      "jobDescription": "<p>RD/RDN supporting NSW operators.</p>"
    }
  ]
}
"""


def _detail_page(body, *, marker='class="job-description"'):
    return (
        "<html><head><title>Job detail</title>"
        '<script>var t = {"id": 1};</script></head><body>'
        "<nav><a href='/'>Home</a> <a href='/login'>Sign in</a> Create account</nav>"
        "<header>NSCA Career Center</header>"
        f"<div {marker}>{body}</div>"
        "<footer>Copyright 2026 NSCA. All rights reserved.</footer>"
        "</body></html>"
    ).encode()


FULL_BODY = (
    "<p>The Tactical Strength and Conditioning Coach embeds with an urban fire "
    "department and delivers daily physical training.</p>"
    "<ul><li>CSCS and TSAC-F required</li>"
    "<li>Master's degree in exercise physiology preferred</li>"
    "<li>Must pass a Secret clearance investigation</li></ul>"
    "<p>Salary commensurate with experience.</p>"
)


def _install(monkeypatch, pages, *, log=None):
    """Replace the module's ``fetch`` with a lookup over captured responses."""

    def fake_fetch(url, **kwargs):
        if log is not None:
            log.append(url)
        try:
            body = pages[url]
        except KeyError:
            raise RuntimeError(f"unmocked url {url}")
        if isinstance(body, Exception):
            raise body
        return body

    monkeypatch.setattr("tactical_jobs.sources.boards.fetch", fake_fetch)


def _run(monkeypatch, pages, options, *, name="nsca", log=None):
    _install(monkeypatch, pages, log=log)
    return list(AssociationBoardSource(name, options).fetch())


NO_DETAIL = {"fetch_details": False}


# ---------------------------------------------------------------------------
# format auto-detection
# ---------------------------------------------------------------------------


def test_rss_payload_is_detected_and_parsed(monkeypatch):
    feed = _rss(_item("Tactical Strength Coach - Austin Fire - Austin, TX", guid="ym-1"))
    postings = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})
    assert len(postings) == 1
    assert postings[0].source == "assocboard:nsca"
    assert postings[0].source_id == "ym-1"
    assert postings[0].url == DETAIL_URL


def test_json_payload_is_detected_and_parsed(monkeypatch):
    postings = _run(monkeypatch, {JSON_URL: JSON_PAYLOAD}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.source_id for p in postings] == ["88231", "88232"]


def test_json_body_served_from_a_feed_path_is_still_parsed(monkeypatch):
    """The path says RSS; the tenant answered with JSON. The body decides."""
    postings = _run(monkeypatch, {FEED_URL: JSON_PAYLOAD}, {"url": FEED_URL, **NO_DETAIL})
    assert [p.title for p in postings] == [
        "Human Performance Program Manager",
        "Performance Dietitian",
    ]


def test_xml_body_served_from_a_json_path_is_still_parsed(monkeypatch):
    """format=json that the tenant does not implement returns the feed."""
    feed = _rss(_item("Athletic Trainer - Denver Fire - Denver, CO", guid="ym-9"))
    postings = _run(monkeypatch, {JSON_URL: feed}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.employer for p in postings] == ["Denver Fire"]


def test_bom_and_leading_whitespace_do_not_defeat_detection(monkeypatch):
    body = "﻿\n  " + JSON_PAYLOAD.decode()
    postings = _run(monkeypatch, {JSON_URL: body.encode()}, {"url": JSON_URL, **NO_DETAIL})
    assert len(postings) == 2


def test_bare_json_array_root_is_parsed(monkeypatch):
    body = b'[{"jobId": 7, "title": "Strength Coach", "url": "https://x.test/7"}]'
    postings = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.source_id for p in postings] == ["7"]


@pytest.mark.parametrize(
    "body, expected",
    [
        (b'{"results": []}', "json"),
        (b"  \n[1, 2]", "json"),
        (b'<?xml version="1.0"?><rss/>', "xml"),
        (b"\n<feed/>", "xml"),
        ("﻿{}".encode(), "json"),
        (b"Service Unavailable", "unknown"),
        (b"", "unknown"),
    ],
)
def test_detect_payload_kind(body, expected):
    assert detect_payload_kind(body) == expected


def test_a_body_that_is_neither_json_nor_xml_raises(monkeypatch):
    """Reporting an error page as zero jobs would hide a dead board."""
    with pytest.raises(RuntimeError) as excinfo:
        _run(monkeypatch, {FEED_URL: b"Service Unavailable"}, {"url": FEED_URL})
    assert "neither JSON nor a readable RSS/Atom feed" in str(excinfo.value)


def test_a_well_formed_html_error_page_raises(monkeypatch):
    """404 pages parse as XML. Silently reporting zero jobs would hide them."""
    page = b"<html><body><h1>404 Not Found</h1></body></html>"
    with pytest.raises(RuntimeError) as excinfo:
        _run(monkeypatch, {FEED_URL: page}, {"url": FEED_URL})
    assert "HTML page" in str(excinfo.value)


def test_a_login_wall_raises_rather_than_reporting_an_empty_board(monkeypatch):
    page = (
        b'<html><head><title>Sign in</title></head><body>'
        b"<form><input name='user'/></form></body></html>"
    )
    with pytest.raises(RuntimeError):
        _run(monkeypatch, {FEED_URL: page}, {"url": FEED_URL})


# ---------------------------------------------------------------------------
# title patterns
# ---------------------------------------------------------------------------


def test_dash_pattern_splits_title_employer_and_location(monkeypatch):
    feed = _rss(
        _item(
            "Tactical Strength and Conditioning Coach - Austin Fire Department - Austin, TX",
            guid="ym-1",
        )
    )
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.title == "Tactical Strength and Conditioning Coach"
    assert posting.employer == "Austin Fire Department"
    assert posting.location == "Austin, TX"


def test_at_pattern_splits_title_employer_and_location(monkeypatch):
    feed = _rss(_item("Athletic Trainer at Boston Police Department (Boston, MA)", guid="ym-2"))
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.title == "Athletic Trainer"
    assert posting.employer == "Boston Police Department"
    assert posting.location == "Boston, MA"


def test_colon_pattern_splits_employer_first(monkeypatch):
    feed = _rss(
        _item("Fort Bragg Fire Department: Peer Fitness Trainer (Fayetteville, NC)", guid="ym-3")
    )
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.title == "Peer Fitness Trainer"
    assert posting.employer == "Fort Bragg Fire Department"
    assert posting.location == "Fayetteville, NC"


def test_unparseable_title_falls_back_to_the_employer_option(monkeypatch):
    feed = _rss(_item("Cognitive Performance Specialist", guid="ym-4"))
    posting = _run(
        monkeypatch,
        {FEED_URL: feed},
        {"url": FEED_URL, "employer": "NSCA Career Center", **NO_DETAIL},
    )[0]
    assert posting.title == "Cognitive Performance Specialist"
    assert posting.employer == "NSCA Career Center"
    assert posting.location == ""


def test_employer_fallback_defaults_to_the_source_name(monkeypatch):
    feed = _rss(_item("Exercise Physiologist", guid="ym-5"))
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.employer == "nsca"


@pytest.mark.parametrize(
    "raw, expected",
    [
        (
            "Strength and Conditioning Coach - THOR3 - Fort Campbell, KY",
            ("Strength and Conditioning Coach", "THOR3", "Fort Campbell, KY"),
        ),
        (
            "Performance Dietitian at Amentum (Coronado, CA)",
            ("Performance Dietitian", "Amentum", "Coronado, CA"),
        ),
        (
            "University of Texas at Austin: Sports Performance Dietitian (Austin, TX)",
            ("Sports Performance Dietitian", "University of Texas at Austin", "Austin, TX"),
        ),
        ("Human Performance Specialist", ("Human Performance Specialist", "", "")),
        # A colon that is a qualifier, not an employer: fail closed.
        ("Athletic Trainer: Per Diem", ("Athletic Trainer: Per Diem", "", "")),
        # A trailing fragment that is not a real state is not a location.
        (
            "Head Coach - Strength and Conditioning, Football",
            ("Head Coach", "Strength and Conditioning, Football", ""),
        ),
        (
            "Physical Therapist | Naval Special Warfare | Virginia Beach, VA",
            ("Physical Therapist", "Naval Special Warfare", "Virginia Beach, VA"),
        ),
        ("Tactical Strength Coach - Remote", ("Tactical Strength Coach", "", "Remote")),
        ("", ("", "", "")),
    ],
)
def test_parse_listing_title(raw, expected):
    assert parse_listing_title(raw) == expected


@pytest.mark.parametrize(
    "text, expected",
    [
        ("Austin, TX", True),
        ("Fort Campbell, Kentucky", True),
        ("Coronado, CA, USA", True),
        ("Remote", True),
        ("Work From Home", True),
        ("Strength and Conditioning, Football", False),
        ("Virtual Reality Program", False),
        ("", False),
    ],
)
def test_looks_like_location(text, expected):
    assert looks_like_location(text) is expected


def test_the_original_title_is_kept_in_the_description(monkeypatch):
    """A qualifier trimmed off the title must still reach the classifier."""
    feed = _rss(_item("Strength Coach - Ohio State - Columbus, OH", guid="ym-6"))
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert "Listed as: Strength Coach - Ohio State - Columbus, OH" in posting.description


def test_a_remote_listing_is_flagged(monkeypatch):
    feed = _rss(_item("Performance Analyst - O2X - Remote", guid="ym-7"))
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.remote is True
    assert posting.location == "Remote"


# ---------------------------------------------------------------------------
# detail pages
# ---------------------------------------------------------------------------


def test_detail_fetch_enriches_the_description(monkeypatch):
    feed = _rss(_item("Tactical Strength Coach - Austin Fire - Austin, TX", guid="ym-1"))
    pages = {FEED_URL: feed, DETAIL_URL: _detail_page(FULL_BODY)}
    posting = _run(monkeypatch, pages, {"url": FEED_URL})[0]
    assert "CSCS and TSAC-F required" in posting.description
    assert "Secret clearance" in posting.description
    # Block tags become separators rather than gluing words together.
    assert "requiredMaster" not in posting.description


def test_detail_fetch_excludes_page_chrome(monkeypatch):
    feed = _rss(_item("Tactical Strength Coach - Austin Fire - Austin, TX", guid="ym-1"))
    pages = {FEED_URL: feed, DETAIL_URL: _detail_page(FULL_BODY)}
    posting = _run(monkeypatch, pages, {"url": FEED_URL})[0]
    assert "Create account" not in posting.description
    assert "All rights reserved" not in posting.description
    assert "var t" not in posting.description


def test_detail_failure_keeps_the_record(monkeypatch):
    feed = _rss(_item("Athletic Trainer - Denver Fire - Denver, CO", guid="ym-8"))
    pages = {FEED_URL: feed, DETAIL_URL: RuntimeError("HTTP 503")}
    postings = _run(monkeypatch, pages, {"url": FEED_URL})
    assert len(postings) == 1
    assert "See the full posting" in postings[0].description
    assert postings[0].employer == "Denver Fire"


def test_detail_limit_bounds_the_fan_out(monkeypatch):
    items = [
        _item(f"Strength Coach {n} - Unit {n} - Fort Carson, CO", link=f"https://x.test/{n}", guid=f"g{n}")
        for n in range(5)
    ]
    pages = {FEED_URL: _rss(*items)}
    for n in range(5):
        pages[f"https://x.test/{n}"] = _detail_page(FULL_BODY)
    requested = []
    postings = _run(
        monkeypatch, pages, {"url": FEED_URL, "detail_limit": 2}, log=requested
    )
    assert len(postings) == 5
    assert len([u for u in requested if u.startswith("https://x.test/")]) == 2
    assert "CSCS and TSAC-F required" in postings[0].description
    assert "CSCS and TSAC-F required" not in postings[4].description


def test_fetch_details_false_makes_no_detail_requests(monkeypatch):
    feed = _rss(_item("Strength Coach - Unit - Fort Carson, CO", guid="g1"))
    requested = []
    postings = _run(
        monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, "fetch_details": False}, log=requested
    )
    assert requested == [FEED_URL]
    assert len(postings) == 1


def test_a_long_feed_body_skips_the_detail_request(monkeypatch):
    body = "<p>" + ("Full posting text with every requirement spelled out. " * 20) + "</p>"
    feed = _rss(_item("Strength Coach - Unit - Fort Carson, CO", guid="g1", description=body))
    requested = []
    postings = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL}, log=requested)
    assert requested == [FEED_URL]
    assert "every requirement spelled out" in postings[0].description


def test_a_thinner_detail_page_does_not_replace_the_feed_body(monkeypatch):
    body = "<p>" + ("Feed body sentence that is reasonably long. " * 6) + "</p>"
    feed = _rss(_item("Strength Coach - Unit - Fort Carson, CO", guid="g1", description=body))
    pages = {FEED_URL: feed, DETAIL_URL: b"<html><body><p>tiny</p></body></html>"}
    posting = _run(monkeypatch, pages, {"url": FEED_URL})[0]
    assert "Feed body sentence" in posting.description
    assert "tiny" not in posting.description


def test_extract_detail_text_prefers_the_marked_description_region():
    text = extract_detail_text(_detail_page(FULL_BODY))
    assert text.startswith("The Tactical Strength and Conditioning Coach")
    assert "Home" not in text
    assert "Copyright 2026" not in text


def test_extract_detail_text_falls_back_to_the_page_body():
    page = (
        "<html><body><nav>Home Sign in</nav>"
        "<h1>Human Performance Coach</h1>"
        "<p>Deliver strength and conditioning to a SOCOM POTFF team. CSCS required.</p>"
        "<footer>Copyright 2026</footer></body></html>"
    )
    text = extract_detail_text(page)
    assert "SOCOM POTFF" in text
    assert "Sign in" not in text
    assert "Copyright 2026" not in text


def test_extract_detail_text_survives_unclosed_tags():
    page = (
        '<html><body><div class="jobDescription"><p>First line'
        "<li>CSCS required<li>TSAC-F preferred</div></body></html>"
    )
    text = extract_detail_text(page)
    assert "CSCS required" in text
    assert "TSAC-F preferred" in text
    assert "requiredTSAC" not in text


def test_detail_region_shorter_than_a_label_does_not_win():
    """``<span class="description">Description</span>`` is a label, not a body."""
    page = (
        '<html><body><span class="description">Description</span>'
        "<p>Embedded athletic trainer supporting a Ranger battalion. "
        "BOC certification and a current EMT card are required for this role.</p>"
        "</body></html>"
    )
    text = extract_detail_text(page)
    assert "Ranger battalion" in text


# ---------------------------------------------------------------------------
# bounds and bad records
# ---------------------------------------------------------------------------


def test_max_items_caps_the_postings(monkeypatch):
    items = [
        _item(f"Coach {n} - Unit - Fort Carson, CO", link=f"https://x.test/{n}", guid=f"g{n}")
        for n in range(10)
    ]
    postings = _run(
        monkeypatch, {FEED_URL: _rss(*items)}, {"url": FEED_URL, "max_items": 3, **NO_DETAIL}
    )
    assert len(postings) == 3
    assert [p.source_id for p in postings] == ["g0", "g1", "g2"]


def test_max_items_also_caps_detail_requests(monkeypatch):
    items = [
        _item(f"Coach {n} - Unit - Fort Carson, CO", link=f"https://x.test/{n}", guid=f"g{n}")
        for n in range(10)
    ]
    pages = {FEED_URL: _rss(*items)}
    for n in range(10):
        pages[f"https://x.test/{n}"] = _detail_page(FULL_BODY)
    requested = []
    postings = _run(
        monkeypatch, pages, {"url": FEED_URL, "max_items": 2}, log=requested
    )
    assert len(postings) == 2
    assert len([u for u in requested if u.startswith("https://x.test/")]) == 2


def test_an_item_without_a_title_or_link_is_skipped(monkeypatch):
    feed = _rss(
        _item("", guid="no-title"),
        _item("Coach - Unit - Fort Carson, CO", link="", guid="no-link"),
        _item("Athletic Trainer - Denver Fire - Denver, CO", guid="good"),
    )
    postings = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})
    assert [p.source_id for p in postings] == ["good"]


def test_a_malformed_json_record_is_skipped_not_fatal(monkeypatch):
    body = (
        b'{"results": ["a bare string", 42, null, '
        b'{"jobId": 5, "jobTitle": "Strength Coach", "jobUrl": "https://x.test/5"}]}'
    )
    postings = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.source_id for p in postings] == ["5"]


def test_a_json_record_without_a_title_is_skipped(monkeypatch):
    body = b'{"jobs": [{"jobId": 1, "jobUrl": "https://x.test/1"}, {"jobId": 2, "title": "Coach"}]}'
    postings = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.source_id for p in postings] == ["2"]


def test_duplicate_ids_are_emitted_once(monkeypatch):
    feed = _rss(
        _item("Coach - Unit - Fort Carson, CO", guid="same"),
        _item("Coach - Unit - Fort Carson, CO", guid="same"),
    )
    postings = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})
    assert len(postings) == 1


def test_an_empty_feed_yields_nothing(monkeypatch):
    postings = _run(monkeypatch, {FEED_URL: _rss()}, {"url": FEED_URL, **NO_DETAIL})
    assert postings == []


def test_json_payload_with_no_recognizable_envelope_yields_nothing(monkeypatch):
    body = b'{"status": "ok", "facets": {"state": ["TX", "NC"]}}'
    assert _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL}) == []


def test_missing_url_option_raises_a_useful_key_error():
    with pytest.raises(KeyError) as excinfo:
        list(AssociationBoardSource("nsca", {}).fetch())
    assert "url" in str(excinfo.value)


@pytest.mark.parametrize(
    "options",
    [
        {"max_items": None},
        {"max_items": "lots"},
        {"detail_limit": None},
        {"detail_limit": "some"},
        {"detail_min_chars": "many"},
        {"fetch_details": "false"},
        {"fetch_details": "yes"},
    ],
)
def test_junk_option_values_fall_back_to_defaults(monkeypatch, options):
    feed = _rss(_item("Athletic Trainer - Denver Fire - Denver, CO", guid="g1"))
    pages = {FEED_URL: feed, DETAIL_URL: _detail_page(FULL_BODY)}
    postings = _run(monkeypatch, pages, {"url": FEED_URL, **options})
    assert [p.employer for p in postings] == ["Denver Fire"]


# ---------------------------------------------------------------------------
# JSON mapping
# ---------------------------------------------------------------------------


def test_json_maps_every_core_field(monkeypatch):
    postings = _run(monkeypatch, {JSON_URL: JSON_PAYLOAD}, {"url": JSON_URL, **NO_DETAIL})
    posting = postings[0]
    assert posting.title == "Human Performance Program Manager"
    assert posting.employer == "Leidos"
    assert posting.location == "Fort Bragg, NC"
    assert posting.url == "https://careers.nsca.com/jobs/88231/human-performance-program-manager"
    assert posting.compensation == "$95,000 - $120,000"
    assert posting.posted_at is not None and posting.posted_at.year == 2026
    assert posting.raw["jobId"] == 88231


def test_json_description_concatenates_every_narrative_field(monkeypatch):
    """The certifications live in ``requirements``, not ``jobDescription``."""
    posting = _run(monkeypatch, {JSON_URL: JSON_PAYLOAD}, {"url": JSON_URL, **NO_DETAIL})[0]
    assert "USASOC THOR3" in posting.description
    assert "CSCS required" in posting.description
    assert "Active Secret clearance" in posting.description
    assert "<p>" not in posting.description


@pytest.mark.parametrize(
    "body",
    [
        b'{"results": [{"jobId": 3, "title": "Coach", "url": "https://x.test/3"}]}',
        b'{"jobs": [{"jobId": 3, "title": "Coach", "url": "https://x.test/3"}]}',
        b'{"items": [{"jobId": 3, "title": "Coach", "url": "https://x.test/3"}]}',
        b'{"data": {"listings": [{"jobId": 3, "title": "Coach", "url": "https://x.test/3"}]}}',
        b'[{"jobId": 3, "title": "Coach", "url": "https://x.test/3"}]',
    ],
)
def test_json_envelope_variants_all_resolve(monkeypatch, body):
    postings = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.source_id for p in postings] == ["3"]


def test_json_relative_url_is_resolved_against_the_endpoint(monkeypatch):
    posting = _run(monkeypatch, {JSON_URL: JSON_PAYLOAD}, {"url": JSON_URL, **NO_DETAIL})[0]
    assert posting.url.startswith("https://careers.nsca.com/jobs/88231/")


def test_json_title_is_parsed_when_no_employer_field_exists(monkeypatch):
    body = (
        b'{"results": [{"id": "x1", '
        b'"title": "Strength Coach - Charlotte Fire Department - Charlotte, NC", '
        b'"url": "https://x.test/x1"}]}'
    )
    posting = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})[0]
    assert posting.title == "Strength Coach"
    assert posting.employer == "Charlotte Fire Department"
    assert posting.location == "Charlotte, NC"


def test_a_structured_employer_field_beats_the_title_heuristic(monkeypatch):
    body = (
        b'{"results": [{"id": "x2", "title": "Strength Coach - Tactical Division", '
        b'"employer": "Charlotte Fire Department", "location": "Charlotte, NC", '
        b'"url": "https://x.test/x2"}]}'
    )
    posting = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})[0]
    assert posting.employer == "Charlotte Fire Department"
    assert posting.title == "Strength Coach - Tactical Division"


def test_json_detail_page_is_fetched_when_the_record_has_no_body(monkeypatch):
    body = b'{"results": [{"jobId": 9, "title": "Strength Coach", "jobUrl": "https://x.test/9"}]}'
    pages = {JSON_URL: body, "https://x.test/9": _detail_page(FULL_BODY)}
    posting = _run(monkeypatch, pages, {"url": JSON_URL})[0]
    assert "CSCS and TSAC-F required" in posting.description


def test_association_option_is_recorded_in_department(monkeypatch):
    feed = _rss(_item("Coach - Unit - Fort Carson, CO", guid="g1"))
    posting = _run(
        monkeypatch,
        {FEED_URL: feed},
        {"url": FEED_URL, "association": "NSCA Career Center", **NO_DETAIL},
    )[0]
    assert posting.department == "NSCA Career Center"


def test_department_falls_back_to_the_json_category(monkeypatch):
    posting = _run(monkeypatch, {JSON_URL: JSON_PAYLOAD}, {"url": JSON_URL, **NO_DETAIL})[0]
    assert posting.department == "Tactical Strength and Conditioning"


def test_atom_feed_is_parsed(monkeypatch):
    postings = _run(monkeypatch, {FEED_URL: ATOM}, {"url": FEED_URL, **NO_DETAIL}, name="nata")
    assert len(postings) == 1
    posting = postings[0]
    assert posting.title == "Athletic Trainer"
    assert posting.employer == "Camp Lejeune MCCS"
    assert posting.location == "Jacksonville, NC"
    assert posting.url == "https://careers.nata.org/job/778"
    assert posting.source_id == "urn:nata:778"
    assert "BOC certification" in posting.description
    assert posting.posted_at is not None and posting.posted_at.month == 7


def test_a_relative_item_link_is_resolved_against_the_feed(monkeypatch):
    feed = _rss(_item("Coach - Unit - Fort Carson, CO", link="/jobs/55/coach", guid="g1"))
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.url == "https://careers.nsca.com/jobs/55/coach"


def test_content_encoded_wins_over_a_truncated_description(monkeypatch):
    extra = (
        "<content:encoded><![CDATA[<p>Full posting body naming CSCS, TSAC-F, "
        "and an active Secret clearance requirement.</p>]]></content:encoded>"
    )
    feed = _rss(
        _item("Coach - Unit - Fort Carson, CO", guid="g1", description="Teaser...", extra=extra)
    )
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert "TSAC-F" in posting.description


# ---------------------------------------------------------------------------
# KnownBoardsSource
# ---------------------------------------------------------------------------


def _board_url(slug):
    return ASSOCIATION_BOARDS[slug]["url"]


def _known(monkeypatch, pages, options, *, name="assoc", log=None):
    _install(monkeypatch, pages, log=log)
    return list(KnownBoardsSource(name, options).fetch())


def test_known_boards_runs_each_configured_board(monkeypatch):
    pages = {
        _board_url("nsca"): _rss(_item("Coach - Austin Fire - Austin, TX", guid="n1")),
        _board_url("nata"): _rss(_item("Athletic Trainer - Denver Fire - Denver, CO", guid="t1")),
    }
    postings = _known(
        monkeypatch, pages, {"boards": ["nsca", "nata"], "fetch_details": False}
    )
    assert [p.source_id for p in postings] == ["n1", "t1"]
    assert [p.source for p in postings] == ["knownboards:assoc:nsca", "knownboards:assoc:nata"]


def test_one_dead_board_does_not_abort_the_run(monkeypatch):
    pages = {
        _board_url("nata"): RuntimeError("HTTP 404 for careers.nata.org"),
        _board_url("nsca"): _rss(_item("Coach - Austin Fire - Austin, TX", guid="n1")),
    }
    postings = _known(
        monkeypatch, pages, {"boards": ["nata", "nsca"], "fetch_details": False}
    )
    assert [p.source_id for p in postings] == ["n1"]


def test_a_board_returning_an_error_page_does_not_abort_the_run(monkeypatch):
    pages = {
        _board_url("acsm"): b"<html><body>Temporarily unavailable</body></html>",
        _board_url("nsca"): _rss(_item("Coach - Austin Fire - Austin, TX", guid="n1")),
    }
    postings = _known(
        monkeypatch, pages, {"boards": ["acsm", "nsca"], "fetch_details": False}
    )
    assert [p.source_id for p in postings] == ["n1"]


def test_an_unknown_slug_is_skipped_not_fatal(monkeypatch, caplog):
    pages = {_board_url("nsca"): _rss(_item("Coach - Austin Fire - Austin, TX", guid="n1"))}
    with caplog.at_level("WARNING"):
        postings = _known(
            monkeypatch, pages, {"boards": ["nsca-typo", "nsca"], "fetch_details": False}
        )
    assert [p.source_id for p in postings] == ["n1"]
    assert "unknown board slug" in caplog.text


def test_known_boards_defaults_to_every_board(monkeypatch):
    pages = {
        entry["url"]: _rss(_item("Coach - Employer - Austin, TX", guid=slug))
        for slug, entry in ASSOCIATION_BOARDS.items()
    }
    postings = _known(monkeypatch, pages, {"fetch_details": False})
    assert {p.source_id for p in postings} == set(ASSOCIATION_BOARDS)
    assert len({p.source for p in postings}) == len(ASSOCIATION_BOARDS)


def test_known_boards_supplies_the_board_label_and_employer_hint(monkeypatch):
    pages = {_board_url("cscca"): _rss(_item("Head Strength Coach", guid="c1"))}
    posting = _known(monkeypatch, pages, {"boards": ["cscca"], "fetch_details": False})[0]
    assert posting.employer == ASSOCIATION_BOARDS["cscca"]["employer_hint"]
    assert posting.department == ASSOCIATION_BOARDS["cscca"]["name"]


def test_known_boards_passes_bounds_through(monkeypatch):
    items = [
        _item(f"Coach {n} - Unit - Austin, TX", link=f"https://x.test/{n}", guid=f"g{n}")
        for n in range(6)
    ]
    pages = {_board_url("aasp"): _rss(*items)}
    requested = []
    postings = _known(
        monkeypatch,
        pages,
        {"boards": ["aasp"], "max_items": 2, "fetch_details": False},
        log=requested,
    )
    assert len(postings) == 2
    assert requested == [_board_url("aasp")]


def test_known_boards_accepts_a_single_slug_string(monkeypatch):
    pages = {_board_url("apta"): _rss(_item("Physical Therapist - NSW - Coronado, CA", guid="p1"))}
    postings = _known(monkeypatch, pages, {"boards": "apta", "fetch_details": False})
    assert [p.source_id for p in postings] == ["p1"]


def test_known_boards_employer_override_wins(monkeypatch):
    pages = {_board_url("scan"): _rss(_item("Performance Dietitian", guid="s1"))}
    postings = _known(
        monkeypatch,
        pages,
        {"boards": ["scan"], "employer": "SCAN DPG", "fetch_details": False},
    )
    assert postings[0].employer == "SCAN DPG"


def test_association_boards_table_is_complete_and_well_formed():
    required = {"nsca", "nsca-tsac", "nata", "acsm", "cscca", "aasp", "apta", "scan"}
    assert required <= set(ASSOCIATION_BOARDS)
    for slug, entry in ASSOCIATION_BOARDS.items():
        assert set(entry) == {"name", "url", "employer_hint"}, slug
        assert entry["url"].startswith("https://"), slug
        assert entry["name"] and entry["employer_hint"], slug
    # Every board must be reachable without a credential of any kind.
    for entry in ASSOCIATION_BOARDS.values():
        blob = entry["url"].lower()
        assert "api_key" not in blob and "apikey" not in blob and "token" not in blob


def test_module_exports_the_source_tuple():
    assert BOARD_SOURCES == (AssociationBoardSource, KnownBoardsSource)
    assert AssociationBoardSource.kind == "assocboard"
    assert KnownBoardsSource.kind == "knownboards"
    assert len({cls.kind for cls in BOARD_SOURCES}) == len(BOARD_SOURCES)


# ---------------------------------------------------------------------------
# namespaced feeds
#
# The vendors serve more than one feed dialect, and a namespace-qualified
# lookup finds nothing in most of them. That failure is silent -- zero items,
# no exception -- which is indistinguishable from a board with no openings, so
# each dialect gets a test.
# ---------------------------------------------------------------------------


RSS1 = (
    '<?xml version="1.0"?>'
    '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#" '
    'xmlns="http://purl.org/rss/1.0/" '
    'xmlns:dc="http://purl.org/dc/elements/1.1/">'
    '<channel rdf:about="https://careers.nsca.com/jobs"><title>NSCA</title></channel>'
    '<item rdf:about="https://careers.nsca.com/job/1">'
    "<title>Strength Coach - Austin Fire - Austin, TX</title>"
    "<link>https://careers.nsca.com/job/1</link>"
    "<description>CSCS and TSAC-F required for this tactical role.</description>"
    "<dc:date>2026-07-20</dc:date>"
    "</item>"
    "</rdf:RDF>"
).encode()


def test_rss_1_0_namespaced_items_are_parsed(monkeypatch):
    """An RSS 1.0 board must not read as an empty board."""
    posting = _run(monkeypatch, {FEED_URL: RSS1}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.title == "Strength Coach"
    assert posting.employer == "Austin Fire"
    assert posting.location == "Austin, TX"
    assert posting.url == "https://careers.nsca.com/job/1"
    assert "TSAC-F" in posting.description
    assert posting.posted_at is not None and posting.posted_at.day == 20


def test_rss_2_0_under_a_default_namespace_is_parsed(monkeypatch):
    feed = (
        '<rss xmlns="http://backend.userland.com/rss2" version="2.0"><channel><item>'
        "<title>Athletic Trainer - Denver Fire - Denver, CO</title>"
        "<link>https://x.test/1</link><guid>g1</guid>"
        "<description>BOC certification required.</description>"
        "</item></channel></rss>"
    ).encode()
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.employer == "Denver Fire"
    assert posting.source_id == "g1"
    assert "BOC certification" in posting.description


def test_atom_0_3_namespace_is_parsed(monkeypatch):
    feed = (
        '<feed xmlns="http://purl.org/atom/ns#"><entry>'
        "<title>Coach - Fort Carson Garrison - Colorado Springs, CO</title>"
        '<link rel="alternate" href="https://x.test/a3"/>'
        "<id>urn:aasp:a3</id><summary>H2F cohort support.</summary>"
        "</entry></feed>"
    ).encode()
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.url == "https://x.test/a3"
    assert posting.source_id == "urn:aasp:a3"
    assert posting.employer == "Fort Carson Garrison"


def test_a_namespaced_atom_link_rel_self_is_not_used_as_the_job_url(monkeypatch):
    feed = (
        '<feed xmlns="http://www.w3.org/2005/Atom"><entry>'
        "<title>Coach - Unit - Austin, TX</title>"
        '<link rel="self" href="https://x.test/feed"/>'
        '<link rel="alternate" href="https://x.test/job/7"/>'
        "<id>7</id></entry></feed>"
    ).encode()
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.url == "https://x.test/job/7"


@pytest.mark.parametrize(
    "tag, expected",
    [
        ("item", "item"),
        ("{http://purl.org/rss/1.0/}item", "item"),
        ("{http://www.w3.org/2005/Atom}Entry", "entry"),
        (None, ""),
        (object, ""),
    ],
)
def test_local_name(tag, expected):
    assert local_name(tag) == expected


# ---------------------------------------------------------------------------
# silent-emptiness guards
# ---------------------------------------------------------------------------


def test_a_populated_envelope_beats_an_empty_one(monkeypatch):
    """``{"results": [], "jobs": [...]}`` must not report an empty board."""
    body = (
        b'{"results": [], "jobs": [{"jobId": 4, "title": "Strength Coach", '
        b'"jobUrl": "https://x.test/4"}]}'
    )
    postings = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.source_id for p in postings] == ["4"]


def test_json_records_prefers_the_populated_envelope():
    assert json_records({"results": [], "jobs": [{"title": "Coach"}]}) == [{"title": "Coach"}]
    assert json_records({"results": [], "jobs": []}) == []
    assert json_records({"nothing": "here"}) == []


def test_two_id_less_records_at_different_employers_both_survive(monkeypatch):
    """A board with no ids and no links must not collapse onto the title."""
    body = (
        b'{"results": ['
        b'{"title": "Athletic Trainer", "employer": "Alpha Fire", "location": "Austin, TX"},'
        b'{"title": "Athletic Trainer", "employer": "Bravo Fire", "location": "Dallas, TX"}]}'
    )
    postings = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.employer for p in postings] == ["Alpha Fire", "Bravo Fire"]
    assert len({p.source_id for p in postings}) == 2


def test_a_truly_repeated_id_less_record_is_still_deduped(monkeypatch):
    body = (
        b'{"results": ['
        b'{"title": "Athletic Trainer", "employer": "Alpha Fire", "location": "Austin, TX"},'
        b'{"title": "Athletic Trainer", "employer": "Alpha Fire", "location": "Austin, TX"}]}'
    )
    assert len(_run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})) == 1


# ---------------------------------------------------------------------------
# option bounds
# ---------------------------------------------------------------------------


def test_a_negative_max_items_falls_back_to_the_default(monkeypatch, caplog):
    """``max_items = -1`` yielding nothing would look exactly like a quiet board."""
    items = [_item(f"Coach {n} - Unit - Austin, TX", guid=f"g{n}") for n in range(4)]
    with caplog.at_level("WARNING"):
        postings = _run(
            monkeypatch, {FEED_URL: _rss(*items)}, {"url": FEED_URL, "max_items": -1, **NO_DETAIL}
        )
    assert len(postings) == 4
    assert "negative option value" in caplog.text


def test_a_negative_detail_limit_falls_back_to_the_default(monkeypatch):
    feed = _rss(_item("Coach - Unit - Austin, TX", guid="g1"))
    pages = {FEED_URL: feed, DETAIL_URL: _detail_page(FULL_BODY)}
    posting = _run(monkeypatch, pages, {"url": FEED_URL, "detail_limit": -5})[0]
    assert "CSCS and TSAC-F required" in posting.description


def test_an_explicit_zero_max_items_is_still_honoured(monkeypatch):
    """Zero is a deliberate "off"; only a negative value is treated as a typo."""
    feed = _rss(_item("Coach - Unit - Austin, TX", guid="g1"))
    assert _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, "max_items": 0, **NO_DETAIL}) == []


def test_documented_defaults_match_the_spec():
    assert (DEFAULT_MAX_ITEMS, DEFAULT_DETAIL_LIMIT) == (200, 40)


def test_the_default_max_items_actually_bounds_the_run(monkeypatch):
    items = [
        _item(f"Coach {n} - Unit - Austin, TX", guid=f"g{n}")
        for n in range(DEFAULT_MAX_ITEMS + 25)
    ]
    postings = _run(monkeypatch, {FEED_URL: _rss(*items)}, {"url": FEED_URL, **NO_DETAIL})
    assert len(postings) == DEFAULT_MAX_ITEMS


def test_the_default_detail_limit_actually_bounds_the_fan_out(monkeypatch):
    items = [
        _item(f"Coach {n} - Unit - Austin, TX", link=f"https://x.test/{n}", guid=f"g{n}")
        for n in range(DEFAULT_DETAIL_LIMIT + 15)
    ]
    pages = {FEED_URL: _rss(*items)}
    for n in range(DEFAULT_DETAIL_LIMIT + 15):
        pages[f"https://x.test/{n}"] = _detail_page(FULL_BODY)
    requested = []
    _run(monkeypatch, pages, {"url": FEED_URL}, log=requested)
    assert len([u for u in requested if u.startswith("https://x.test/")]) == DEFAULT_DETAIL_LIMIT


def test_detail_pages_do_not_get_the_full_retry_budget(monkeypatch):
    """40 dead detail pages at three attempts each would stall a nightly run."""
    feed = _rss(_item("Coach - Unit - Austin, TX", guid="g1"))
    seen = {}

    def fake_fetch(url, **kwargs):
        seen[url] = kwargs
        return feed if url == FEED_URL else _detail_page(FULL_BODY)

    monkeypatch.setattr("tactical_jobs.sources.boards.fetch", fake_fetch)
    list(AssociationBoardSource("nsca", {"url": FEED_URL}).fetch())
    assert seen[DETAIL_URL]["retries"] == DETAIL_RETRIES
    assert DETAIL_RETRIES < 3
    # The feed itself keeps the default budget -- losing it costs the board.
    assert "retries" not in seen[FEED_URL]


# ---------------------------------------------------------------------------
# hostile and empty records
# ---------------------------------------------------------------------------


def test_records_full_of_nulls_do_not_crash(monkeypatch):
    body = (
        b'{"results": [{"jobId": null, "title": null, "employer": null, "location": null, '
        b'"description": null, "postedDate": null, "url": null}, '
        b'{"jobId": 6, "title": "Coach", "employer": null, "location": null, '
        b'"description": null, "postedDate": null, "url": "https://x.test/6"}]}'
    )
    postings = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})
    assert [p.source_id for p in postings] == ["6"]
    assert postings[0].location == ""
    assert postings[0].posted_at is None


def test_a_nested_json_shape_is_flattened(monkeypatch):
    body = (
        b'{"results": [{"id": "z1", "title": "Coach", "employer": {"name": "Leidos"}, '
        b'"location": {"city": "Fort Bragg", "state": "NC"}, '
        b'"url": "https://x.test/z1", '
        b'"description": {"sections": {"body": "CSCS required"}}}]}'
    )
    posting = _run(monkeypatch, {JSON_URL: body}, {"url": JSON_URL, **NO_DETAIL})[0]
    assert posting.employer == "Leidos"
    assert posting.location == "Fort Bragg, NC"
    assert "CSCS required" in posting.description


def test_unicode_survives_the_round_trip(monkeypatch):
    feed = _rss(
        _item(
            "Entraîneur — Pompiers de Montréal — Austin, TX",
            guid="u1",
            description="Préparation physique. Certification requise — CSCS.",
        )
    )
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert posting.title == "Entraîneur"
    assert posting.employer == "Pompiers de Montréal"
    assert "Préparation physique" in posting.description


def test_a_very_long_description_is_kept_whole(monkeypatch):
    """The analysis layer mines the complete text, so nothing is truncated."""
    long_body = "Requirement sentence naming CSCS. " * 5000
    feed = _rss(_item("Coach - Unit - Austin, TX", guid="g1", description=long_body))
    posting = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL, **NO_DETAIL})[0]
    assert len(posting.description) > 100_000


def test_a_non_http_item_link_is_not_followed(monkeypatch):
    """A feed must not be able to steer the fetcher at a non-web scheme."""
    feed = _rss(_item("Coach - Unit - Austin, TX", link="javascript:alert(1)", guid="g1"))
    requested = []
    postings = _run(monkeypatch, {FEED_URL: feed}, {"url": FEED_URL}, log=requested)
    assert requested == [FEED_URL]
    assert postings == []


# ---------------------------------------------------------------------------
# KnownBoardsSource slug handling
# ---------------------------------------------------------------------------


def test_an_explicitly_empty_boards_list_runs_nothing(monkeypatch):
    """Naming no boards must not quietly fan out to all eight hosts."""
    pages = {entry["url"]: _rss() for entry in ASSOCIATION_BOARDS.values()}
    requested = []
    postings = _known(monkeypatch, pages, {"boards": [], "fetch_details": False}, log=requested)
    assert postings == []
    assert requested == []


def test_a_repeated_slug_is_fetched_once(monkeypatch):
    pages = {_board_url("nsca"): _rss(_item("Coach - Austin Fire - Austin, TX", guid="n1"))}
    requested = []
    postings = _known(
        monkeypatch,
        pages,
        {"boards": ["nsca", "NSCA", "nsca"], "fetch_details": False},
        log=requested,
    )
    assert [p.source_id for p in postings] == ["n1"]
    assert requested == [_board_url("nsca")]


# ---------------------------------------------------------------------------
# keyless and unverified-claim guards
# ---------------------------------------------------------------------------


_MODULE_PATH = Path(__file__).resolve().parents[1] / "tactical_jobs" / "sources" / "boards.py"
_MODULE_SOURCE = _MODULE_PATH.read_text(encoding="utf-8")


def _executable_source(text):
    """The module's code with comments and string literals removed.

    Prose is allowed to say "no OAuth"; code is not allowed to do OAuth. The
    scan below would otherwise be defeated by its own documentation.
    """
    kept = []
    for token in tokenize.generate_tokens(io.StringIO(text).readline):
        if token.type in (tokenize.COMMENT, tokenize.STRING):
            continue
        kept.append(token.string)
    return " ".join(kept).lower()


def test_every_seeded_board_url_is_marked_unverified():
    """These URLs could not be confirmed without network access.

    A confidently wrong URL is the worst failure this source can have: it is
    logged and skipped, which reads as a quiet board rather than a broken one.
    The marker is what tells the next reader to check before trusting it.
    """
    lines = _MODULE_SOURCE.splitlines()
    for slug, entry in ASSOCIATION_BOARDS.items():
        index = next(i for i, line in enumerate(lines) if f'"{entry["url"]}"' in line)
        preceding = " ".join(lines[max(0, index - 3):index]).upper()
        assert "UNVERIFIED" in preceding, slug


def test_the_source_needs_no_credential_of_any_kind(monkeypatch):
    """No key, no account, no OAuth -- the operator has none and can get none."""
    feed = _rss(_item("Coach - Austin Fire - Austin, TX", guid="n1"))
    sent = {}

    def fake_fetch(url, **kwargs):
        sent.update(kwargs)
        return feed

    monkeypatch.setattr("tactical_jobs.sources.boards.fetch", fake_fetch)
    postings = list(AssociationBoardSource("nsca", {"url": FEED_URL, **NO_DETAIL}).fetch())
    assert len(postings) == 1
    assert "headers" not in sent
    code = _executable_source(_MODULE_SOURCE)
    for forbidden in ("api_key", "apikey", "authorization", "bearer", "oauth", "client_secret"):
        assert forbidden not in code, forbidden
    # Only ``url`` is required; nothing credential-shaped is.
    with pytest.raises(KeyError) as excinfo:
        list(AssociationBoardSource("nsca", {}).fetch())
    assert "'url'" in str(excinfo.value)
