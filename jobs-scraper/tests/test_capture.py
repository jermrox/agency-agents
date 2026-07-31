"""Capture-adapter tests.

The point of this module is restraint: it must extract what a listing page
actually states and refuse to invent the rest. Most of these tests assert an
ABSENCE, which is unusual but is exactly the property that matters here.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.sources.capture import (  # noqa: E402
    CaptureSource,
    Listing,
    parse_capture,
)

HEADER = "SOURCE_URL: https://example.invalid/jobs/\nRETRIEVED: 2026-07-31\n---\n"

PAGE = HEADER + """
# Athletic Trainer Jobs

Showing 1-3 of 641 jobs

## Athletic Trainer

West Virginia University Health System Camden, NJ Full-Time Athletic Trainer ● Posted 14 hours ago

## Assistant Athletic Trainer

Southern Utah University Cedar City, UT Full-Time Athletic Trainer ● Posted 2 days ago

## Tactical Strength and Conditioning Coach

O2X Human Performance Eagle Pass, TX Full-Time Strength & Conditioning Coach $65,000-$70,000● Posted 3 months ago
"""


def parse(text: str = PAGE) -> list[Listing]:
    return parse_capture(text)[2]


# --------------------------------------------------------------------------
# Header
# --------------------------------------------------------------------------

def test_header_yields_source_url_and_date():
    url, retrieved, _ = parse_capture(PAGE)
    assert url == "https://example.invalid/jobs/"
    assert retrieved.date().isoformat() == "2026-07-31"


def test_capture_without_a_header_is_rejected():
    with pytest.raises(ValueError):
        parse_capture("## Some Job\n\nAcme Corp Austin, TX Full-Time\n")


# --------------------------------------------------------------------------
# What it extracts
# --------------------------------------------------------------------------

def test_extracts_every_listing_row():
    assert len(parse()) == 3


def test_titles_are_verbatim():
    titles = [row.title for row in parse()]
    assert titles == [
        "Athletic Trainer",
        "Assistant Athletic Trainer",
        "Tactical Strength and Conditioning Coach",
    ]


def test_pay_is_extracted_only_when_stated():
    rows = parse()
    assert rows[0].pay is None and rows[1].pay is None
    assert rows[2].pay == "$65,000-$70,000"


def test_state_is_extracted():
    assert [row.location for row in parse()] == ["NJ", "UT", "TX"]


def test_employment_type_is_extracted():
    assert all(row.employment_type == "Full-Time" for row in parse())


# --------------------------------------------------------------------------
# What it REFUSES to extract -- the load-bearing behaviour
# --------------------------------------------------------------------------

def test_employer_is_never_guessed():
    """A listing row has no delimiter between employer and city.

    Both are capitalized runs, so any split is a guess. Earlier heuristics
    produced "Health System Camden" as a city and "O2" as an employer -- wrong
    in a way a reader cannot detect. The parser must decline instead.
    """
    assert all(row.employer is None for row in parse())


def test_city_is_never_guessed():
    """Only the state is claimed; "Cedar City" vs "Camden" cannot be resolved."""
    for row in parse():
        assert row.location is None or len(row.location) == 2


def test_meta_line_is_preserved_verbatim():
    """The information the typed fields decline to claim is not thrown away."""
    row = parse()[0]
    assert row.raw_meta == (
        "West Virginia University Health System Camden, NJ Full-Time "
        "Athletic Trainer ● Posted 14 hours ago"
    )


# --------------------------------------------------------------------------
# Dates: derived, and flagged as derived
# --------------------------------------------------------------------------

def test_relative_ages_are_marked_approximate():
    assert all(row.posted_approximate for row in parse() if row.posted_at)


def test_relative_ages_are_computed_from_the_retrieval_date():
    rows = parse()
    assert rows[0].posted_at.date().isoformat() == "2026-07-30"   # 14 hours
    assert rows[1].posted_at.date().isoformat() == "2026-07-29"   # 2 days
    assert rows[2].posted_at.date().isoformat() == "2026-05-02"   # 3 months


def test_a_row_with_no_age_gets_no_date():
    """No published age means no date -- not today's date as a stand-in."""
    row = parse(HEADER + "## Coach\n\nAcme Corp Austin, TX Full-Time Coach\n")[0]
    assert row.posted_at is None
    assert row.posted_approximate is False


def test_unparseable_age_yields_no_date():
    row = parse(HEADER + "## Coach\n\nAcme Austin, TX Full-Time ● Posted recently\n")[0]
    assert row.posted_at is None


# --------------------------------------------------------------------------
# Robustness
# --------------------------------------------------------------------------

def test_row_without_a_meta_line_still_yields_a_title():
    rows = parse(HEADER + "## Lonely Title\n\n## Another Title\n\nAcme Austin, TX Full-Time\n")
    assert rows[0].title == "Lonely Title"
    assert rows[0].raw_meta is None
    assert rows[0].employer is None and rows[0].pay is None


def test_page_with_no_listings_yields_nothing():
    assert parse(HEADER + "\nNo results found.\n") == []


def test_source_reads_a_directory(tmp_path):
    (tmp_path / "a.txt").write_text(PAGE)
    postings = list(CaptureSource("board", {"directory": str(tmp_path)}).fetch())
    assert len(postings) == 3
    assert all(p.url == "https://example.invalid/jobs/" for p in postings)


def test_source_records_provenance_in_raw(tmp_path):
    (tmp_path / "a.txt").write_text(PAGE)
    posting = list(CaptureSource("board", {"directory": str(tmp_path)}).fetch())[0]
    assert posting.raw["source_url"] == "https://example.invalid/jobs/"
    assert posting.raw["retrieved"] == "2026-07-31"
    assert posting.raw["posted_approximate"] is True
    assert "West Virginia University" in posting.raw["raw_meta"]


def test_source_description_carries_the_meta_line(tmp_path):
    """The classifier still sees the employer text, even though no field claims it."""
    (tmp_path / "a.txt").write_text(PAGE)
    posting = list(CaptureSource("board", {"directory": str(tmp_path)}).fetch())[0]
    assert "West Virginia University Health System" in posting.description


def test_missing_directory_is_survivable():
    assert list(CaptureSource("board", {"directory": "/nonexistent/xyz"}).fetch()) == []


def test_malformed_capture_file_is_skipped_not_fatal(tmp_path):
    (tmp_path / "bad.txt").write_text("no header here")
    (tmp_path / "good.txt").write_text(PAGE)
    assert len(list(CaptureSource("board", {"directory": str(tmp_path)}).fetch())) == 3


def test_source_ids_are_stable_and_unique(tmp_path):
    (tmp_path / "a.txt").write_text(PAGE)
    ids = [p.source_id for p in CaptureSource("board", {"directory": str(tmp_path)}).fetch()]
    assert len(set(ids)) == len(ids)
    again = [p.source_id for p in CaptureSource("board", {"directory": str(tmp_path)}).fetch()]
    assert ids == again
