"""Publisher tests, with emphasis on feed accumulation across runs."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.models import JobPosting  # noqa: E402
from tactical_jobs.publishers.files import (  # noqa: E402
    JSONFeedPublisher,
    RSSPublisher,
    ReviewQueuePublisher,
    _excerpt,
)


def make(source_id: str, title: str = "Tactical S&C Coach") -> JobPosting:
    return JobPosting(
        source="test",
        source_id=source_id,
        url=f"https://example.invalid/{source_id}",
        title=title,
        employer="USASOC",
        location="Fort Bragg, NC",
        description="THOR3 human performance program. " * 40,
        posted_at=datetime.now(timezone.utc),
        tags=["sof", "strength-conditioning"],
    )


def test_excerpt_trims_on_word_boundary():
    text = "alpha bravo charlie delta echo foxtrot"
    trimmed = _excerpt(text, limit=20)
    assert len(trimmed) <= 21
    assert "charl" not in trimmed or trimmed.endswith("…")


def test_jsonfeed_excerpts_rather_than_republishing_full_text(tmp_path):
    path = tmp_path / "jobs.json"
    JSONFeedPublisher({"path": str(path)}).publish([make("1")])
    entry = json.loads(path.read_text())["jobs"][0]
    assert len(entry["description"]) <= 401


def test_jsonfeed_accumulates_across_runs(tmp_path):
    path = tmp_path / "jobs.json"
    publisher = JSONFeedPublisher({"path": str(path)})
    publisher.publish([make("1")])
    publisher.publish([make("2")])
    feed = json.loads(path.read_text())
    assert feed["count"] == 2


def test_jsonfeed_empty_run_preserves_the_board(tmp_path):
    """A run with no new jobs must not blank the live board."""
    path = tmp_path / "jobs.json"
    publisher = JSONFeedPublisher({"path": str(path)})
    publisher.publish([make("1")])
    publisher.publish([])
    assert json.loads(path.read_text())["count"] == 1


def test_jsonfeed_ages_out_old_entries(tmp_path):
    path = tmp_path / "jobs.json"
    JSONFeedPublisher({"path": str(path)}).publish([make("1")])

    stale = json.loads(path.read_text())
    stale["jobs"][0]["listed_at"] = "2020-01-01T00:00:00+00:00"
    path.write_text(json.dumps(stale))

    JSONFeedPublisher({"path": str(path), "retain_days": 45}).publish([make("2")])
    remaining = json.loads(path.read_text())
    assert remaining["count"] == 1
    assert remaining["jobs"][0]["id"] == make("2").identity


def test_jsonfeed_recovers_from_corrupt_file(tmp_path):
    path = tmp_path / "jobs.json"
    path.write_text("{ not json")
    JSONFeedPublisher({"path": str(path)}).publish([make("1")])
    assert json.loads(path.read_text())["count"] == 1


def test_rss_renders_the_whole_board_not_just_new_items(tmp_path):
    """The regression that motivated source_feed: run 2 must not empty the feed."""
    board = tmp_path / "jobs.json"
    feed = tmp_path / "jobs.xml"
    json_publisher = JSONFeedPublisher({"path": str(board)})
    rss_publisher = RSSPublisher({"path": str(feed), "source_feed": str(board)})

    json_publisher.publish([make("1"), make("2", title="Athletic Trainer")])
    rss_publisher.publish([make("1"), make("2", title="Athletic Trainer")])
    assert len(ET.fromstring(feed.read_text()).findall(".//item")) == 2

    # Second run finds nothing new -- the feed must still list both jobs.
    json_publisher.publish([])
    rss_publisher.publish([])
    assert len(ET.fromstring(feed.read_text()).findall(".//item")) == 2


def test_rss_falls_back_to_postings_without_a_board(tmp_path):
    feed = tmp_path / "jobs.xml"
    RSSPublisher(
        {"path": str(feed), "source_feed": str(tmp_path / "absent.json")}
    ).publish([make("1")])
    assert len(ET.fromstring(feed.read_text()).findall(".//item")) == 1


def test_rss_is_well_formed_with_ampersands_in_titles(tmp_path):
    feed = tmp_path / "jobs.xml"
    RSSPublisher(
        {"path": str(feed), "source_feed": str(tmp_path / "absent.json")}
    ).publish([make("1", title="Strength & Conditioning Coach <Tier 1>")])
    root = ET.fromstring(feed.read_text())  # raises if escaping is wrong
    assert "Strength & Conditioning" in root.find(".//item/title").text


def test_rss_respects_limit(tmp_path):
    board = tmp_path / "jobs.json"
    feed = tmp_path / "jobs.xml"
    JSONFeedPublisher({"path": str(board)}).publish([make(str(i)) for i in range(10)])
    RSSPublisher({"path": str(feed), "source_feed": str(board), "limit": 3}).publish([])
    assert len(ET.fromstring(feed.read_text()).findall(".//item")) == 3


def test_review_queue_prepends_newest_run(tmp_path):
    path = tmp_path / "review.md"
    publisher = ReviewQueuePublisher({"path": str(path)})
    publisher.publish([make("1", title="First Role")])
    publisher.publish([make("2", title="Second Role")])
    text = path.read_text()
    assert text.index("Second Role") < text.index("First Role")


def test_review_queue_handles_an_empty_run(tmp_path):
    path = tmp_path / "review.md"
    ReviewQueuePublisher({"path": str(path)}).publish([])
    assert "No new postings" in path.read_text()


def test_jsonfeed_excerpt_chars_zero_keeps_full_description(tmp_path):
    """"We need all the information" -- excerpt_chars = 0 disables truncation."""
    path = tmp_path / "jobs.json"
    posting = make("1")
    JSONFeedPublisher({"path": str(path), "excerpt_chars": 0}).publish([posting])
    entry = json.loads(path.read_text())["jobs"][0]
    assert len(entry["description"]) == len(posting.description)


def test_jsonfeed_excerpt_chars_is_configurable(tmp_path):
    path = tmp_path / "jobs.json"
    JSONFeedPublisher({"path": str(path), "excerpt_chars": 50}).publish([make("1")])
    entry = json.loads(path.read_text())["jobs"][0]
    assert len(entry["description"]) <= 51


def test_a_posting_already_on_the_board_is_refreshed_not_frozen(tmp_path):
    """The board used to keep whatever a posting was FIRST published with.

    A job already listed is re-fetched and re-derived on every run, then
    dropped at the dedupe step, so its published entry never changed again.
    That made every extraction fix apply only to jobs the board had never
    seen: three KBR SOF postings stayed flagged Remote after the fix that
    corrected them, purely because they were already listed.
    """
    path = tmp_path / "jobs.json"
    first = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()

    title = "Special Operations Physical Therapist (Onsite - Fort Bragg, NC)"
    corrected = JobPosting(
        source="workday:kbr",
        source_id="R2128061",
        url="https://kbr.example/job/R2128061",
        title=title,
        employer="KBR",
        location="Fayetteville, North Carolina",
    )
    # Same identity, published earlier with the wrong location.
    stale = corrected.to_public_dict()
    stale["location"] = "Fayetteville, North Carolina; Remote - U.S."
    stale["listed_at"] = first
    path.write_text(json.dumps({"version": 1, "count": 1, "jobs": [stale]}))
    JSONFeedPublisher({"path": str(path)}).publish([corrected])

    board = json.loads(path.read_text())["jobs"]
    entry = next(j for j in board if j["location"].startswith("Fayetteville"))
    assert "Remote" not in entry["location"]
    # The retention clock must not restart, or a refreshed job never ages out.
    assert entry["listed_at"] == first


def test_refreshing_does_not_duplicate_the_entry(tmp_path):
    path = tmp_path / "jobs.json"
    posting = JobPosting(
        source="workday:kbr",
        source_id="R1",
        url="https://kbr.example/job/R1",
        title="Coach",
        employer="KBR",
        location="Fort Bragg, NC",
    )
    publisher = JSONFeedPublisher({"path": str(path)})
    publisher.publish([posting])
    publisher.publish([posting])
    assert len(json.loads(path.read_text())["jobs"]) == 1


def test_the_same_posting_under_two_ids_is_collapsed(tmp_path):
    """identity is sha256(source + source_id), and source_id can drift.

    The Workday adapter falls back to the URL path when a detail fetch fails,
    so one flaky night gives a posting a second id. The board then carried it
    twice and a refresh could only ever reach one of them: a real KBR
    requisition sat on the board under an August 7 id still reading
    "Joint Base Lewis-McChord, Washington; Remote - U.S." right next to its
    own corrected August 29 twin, and would have stayed for the full 45-day
    retention window.
    """
    path = tmp_path / "jobs.json"
    url = "https://kbr.wd5.myworkdayjobs.com/KBR_Careers/job/JBLM/Dietitian_R2128060"
    old_listed = (datetime.now(timezone.utc) - timedelta(days=22)).isoformat()
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "count": 1,
                "jobs": [
                    {
                        "id": "1d05eb08ff68ccdf4d9d",
                        "title": "Special Operations Performance Dietitian",
                        "location": "Joint Base Lewis-McChord, Washington; Remote - U.S.",
                        "url": url,
                        "listed_at": old_listed,
                    }
                ],
            }
        )
    )

    corrected = JobPosting(
        source="workday:kbr",
        source_id="R2128060",
        url=url,
        title="Special Operations Performance Dietitian",
        employer="KBR",
        location="Joint Base Lewis-McChord, Washington",
    )
    JSONFeedPublisher({"path": str(path)}).publish([corrected])

    board = json.loads(path.read_text())["jobs"]
    assert len(board) == 1, "one URL is one job"
    assert "Remote" not in board[0]["location"]
    # Collapsing keeps the EARLIEST listing date, so retention is not reset.
    assert board[0]["listed_at"] == old_listed


def test_entries_without_a_url_are_never_collapsed_together(tmp_path):
    path = tmp_path / "jobs.json"
    path.write_text(
        json.dumps(
            {
                "version": 1,
                "count": 2,
                "jobs": [
                    {"id": "a", "title": "One", "url": "", "listed_at": "2026-08-01T00:00:00+00:00"},
                    {"id": "b", "title": "Two", "url": "", "listed_at": "2026-08-02T00:00:00+00:00"},
                ],
            }
        )
    )
    JSONFeedPublisher({"path": str(path)}).publish([])
    assert len(json.loads(path.read_text())["jobs"]) == 2
