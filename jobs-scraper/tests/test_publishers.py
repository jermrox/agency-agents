"""Publisher tests, with emphasis on feed accumulation across runs."""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
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
