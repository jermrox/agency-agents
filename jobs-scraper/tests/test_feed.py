"""Feed normalization tests.

The rows below are copied from the live board so the conversion is pinned
against real data rather than a convenient invention.
"""

from __future__ import annotations

import pytest

import json

from tactical_jobs.feed import (
    CONFIDENCE_DEFINITIONS,
    FEED_VERSION,
    confidence_of,
    normalize_feed,
    normalize_file,
    normalize_row,
)

LEGACY_ROW = {
    "rank": 1,
    "validity": "verified",
    "title": "Human Performance Advisor",
    "employer": "GDIT",
    "program": "SOF Human Performance (Air Force / SOCOM support)",
    "location": "Fort Bragg, NC / Hurlburt Field, FL / Coronado, CA",
    "salary": "$96,569 - $130,651",
    "notes": (
        "Re-verified active 2026-08-03 on GDIT careers. Contingent posting, "
        "expected 2026 start. Master's + 5 yrs, ATC/CSCS/PT/CPS/RD cert, "
        "TS clearance, US citizen."
    ),
    "url": "https://www.gdit.com/careers/job/603057d08/human-performance-advisor/",
}


def test_legacy_row_gains_facets_without_being_retyped():
    entry = normalize_row(LEGACY_ROW)
    facets = entry["facets"]
    assert facets["discipline"] == "human-performance"
    assert facets["location_classes"] == ["conus"]
    # The whole point of the contingency filter: this posting says so in words.
    assert facets["contingency"] == "contingent"
    assert entry["title"] == LEGACY_ROW["title"]
    assert entry["url"] == LEGACY_ROW["url"]


def test_legacy_curated_rank_survives():
    # Without it the board tie-breaks alphabetically by employer.
    assert normalize_row(LEGACY_ROW)["rank"] == 1
    assert "rank" not in normalize_row({**LEGACY_ROW, "rank": None})


def test_legacy_salary_string_is_preserved_verbatim():
    # The candidate sees the employer's own words, not our reconstruction.
    assert normalize_row(LEGACY_ROW)["compensation"] == "$96,569 - $130,651"


def test_legacy_validity_maps_onto_the_published_vocabulary():
    assert confidence_of({**LEGACY_ROW, "validity": "verified"}) == "verified"
    assert confidence_of({**LEGACY_ROW, "validity": "high"}) == "listed"
    assert confidence_of({**LEGACY_ROW, "validity": "aggregator"}) == "aggregator"


def test_a_live_liveness_verdict_outranks_the_stored_validity():
    row = {**LEGACY_ROW, "validity": "aggregator", "liveness": {"state": "live"}}
    assert confidence_of(row) == "verified"


def test_an_unconfirmed_first_party_source_is_listed_not_verified():
    row = {"id": "abc", "source": "workday:kbr", "url": "u", "title": "t"}
    assert confidence_of(row) == "listed"


def test_an_unconfirmed_third_party_source_is_only_an_aggregator_lead():
    row = {"id": "abc", "source": "searchresults:google", "url": "u", "title": "t"}
    assert confidence_of(row) == "aggregator"


def test_native_rows_pass_through_and_gain_facets():
    row = {
        "id": "deadbeef",
        "source": "workday:kbr",
        "url": "https://kbr.example.invalid/job/R2127121",
        "title": "Special Operations Certified Athletic Trainer",
        "employer": "KBR",
        "location": "Southern Pines, NC",
        "description": "Support AFSOC POTFF.",
        "enrichment": {"salary_min": 78000, "salary_period": "year"},
    }
    entry = normalize_row(row)
    assert entry["id"] == "deadbeef"
    assert entry["facets"]["discipline"] == "athletic-training"
    assert entry["facets"]["salary_floor_annual"] == 78000


def test_normalize_feed_publishes_the_badge_definitions():
    out = normalize_feed({"generated": "2026-08-03", "jobs": [LEGACY_ROW]})
    assert out["version"] == FEED_VERSION
    assert out["count"] == 1
    # The board renders these strings; shipping them with the data is what
    # keeps the definition and the value from drifting apart.
    assert out["definitions"]["confidence"] == CONFIDENCE_DEFINITIONS
    assert "contingent" in out["definitions"]["contingency"]


def test_generated_timestamp_is_preserved_from_either_key():
    assert normalize_feed({"generated": "2026-08-03", "jobs": []})["generated_at"] == "2026-08-03"
    assert normalize_feed({"generated_at": "2026-08-04", "jobs": []})["generated_at"] == "2026-08-04"


def test_curated_extras_are_carried_through():
    out = normalize_feed(
        {"jobs": [], "live_feeds": [{"name": "NSCA", "url": "https://x.invalid"}]}
    )
    assert out["live_feeds"][0]["name"] == "NSCA"


def test_malformed_rows_are_skipped_not_fatal():
    out = normalize_feed({"jobs": [LEGACY_ROW, "not a dict", None]})
    assert out["count"] == 1


def test_normalizing_an_already_normalized_feed_is_stable():
    once = normalize_feed({"generated": "2026-08-03", "jobs": [LEGACY_ROW]})
    twice = normalize_feed(once)
    assert twice["jobs"][0]["id"] == once["jobs"][0]["id"]
    assert twice["jobs"][0]["facets"] == once["jobs"][0]["facets"]
    assert twice["count"] == once["count"]


def test_normalize_file_round_trips(tmp_path):
    source = tmp_path / "in.json"
    source.write_text(json.dumps({"generated": "2026-08-03", "jobs": [LEGACY_ROW]}))
    destination = tmp_path / "nested" / "out.json"
    normalize_file(source, destination)
    written = json.loads(destination.read_text())
    assert written["count"] == 1
    assert written["jobs"][0]["facets"]["contingency"] == "contingent"


# --- salary display ---------------------------------------------------------


@pytest.mark.parametrize(
    "compensation,expected",
    [
        # The two shapes that actually appear on the board, both USAJOBS.
        ("$102415 - $133142 PA", "$102,415 - $133,142 /yr"),
        ("$89508 - $116362 PA", "$89,508 - $116,362 /yr"),
        # A flat rate arrives as an identical pair; one number reads faster.
        ("$16.92 - $16.92 PH", "$16.92 /hr"),
        # Hourly keeps cents, and pads them: "$19.5" is not a price.
        ("$19.5 - $21 PH", "$19.50 - $21.00 /hr"),
        # The same field spells the interval out on some announcements.
        ("$63312 - $85658 Per Year", "$63,312 - $85,658 /yr"),
        ("$45.00 - $45.00 Per Hour", "$45.00 /hr"),
        ("$88,520 - $115,079 Annually", "$88,520 - $115,079 /yr"),
        ("$75000", "$75,000"),
    ],
)
def test_a_real_salary_is_formatted_for_a_human(compensation, expected):
    """PA and PH are USAJOBS rate-interval codes, not something to publish."""
    from tactical_jobs.feed import salary_display

    assert salary_display(compensation, None) == expected


def test_a_derived_floor_says_it_is_a_floor():
    from tactical_jobs.feed import salary_display

    assert salary_display(None, 63312.0) == "from $63,312"
    assert salary_display("", 50226.03) == "from $50,226"


def test_no_salary_says_so_rather_than_going_blank():
    """A blank line cannot be told apart from "the board did not bother".

    81 of the 137 postings on the board state no pay at all. Saying that, and
    pointing at the employer's own listing, is the honest answer -- and it is
    the one thing that must never be filled in with a guess.
    """
    from tactical_jobs.feed import SALARY_UNAVAILABLE, salary_display

    assert SALARY_UNAVAILABLE == (
        "Salary Unavailable: Click View posting for more information"
    )
    for compensation, floor in ((None, None), ("", None), (None, 0), ("", False)):
        assert salary_display(compensation, floor) == SALARY_UNAVAILABLE


@pytest.mark.parametrize(
    "compensation",
    ["Competitive DOE", "$120000 Without Compensation", "Negotiable, DOE"],
)
def test_wording_we_cannot_parse_is_kept_verbatim(compensation):
    """The employer's own words beat discarding a figure we cannot read."""
    from tactical_jobs.feed import salary_display

    assert salary_display(compensation, None) == compensation
