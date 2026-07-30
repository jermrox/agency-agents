"""Dedupe and state-persistence tests."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.models import JobPosting  # noqa: E402
from tactical_jobs.store import Store  # noqa: E402


def make(source: str, source_id: str, title: str, employer: str, location: str = "Fort Bragg, NC"):
    return JobPosting(
        source=source,
        source_id=source_id,
        url=f"https://example.invalid/{source_id}",
        title=title,
        employer=employer,
        location=location,
    )


def test_identity_is_stable_and_source_scoped():
    a = make("greenhouse:o2x", "1", "Coach", "O2X")
    b = make("greenhouse:o2x", "1", "Coach", "O2X")
    c = make("lever:o2x", "1", "Coach", "O2X")
    assert a.identity == b.identity
    assert a.identity != c.identity


def test_fingerprint_matches_across_sources():
    """The same job on two boards must collapse to one fingerprint."""
    a = make("greenhouse:o2x", "1", "Strength and Conditioning Coach", "O2X")
    b = make("usajobs:fed", "99", "Strength and Conditioning Coach", "O2X")
    assert a.fingerprint == b.fingerprint


def test_fingerprint_normalizes_abbreviations():
    a = make("a", "1", "Sr. Human Performance Coach", "O2X")
    b = make("b", "2", "Senior Human Performance Coach", "O2X")
    assert a.fingerprint == b.fingerprint


def test_fingerprint_separates_different_locations():
    a = make("a", "1", "Coach", "O2X", location="Fort Bragg, NC")
    b = make("a", "2", "Coach", "O2X", location="Coronado, CA")
    assert a.fingerprint != b.fingerprint


def test_filter_new_suppresses_within_batch(tmp_path):
    store = Store.load(tmp_path / "seen.json")
    postings = [
        make("greenhouse:o2x", "1", "Coach", "O2X"),
        make("usajobs:fed", "99", "Coach", "O2X"),  # same fingerprint
    ]
    assert len(store.filter_new(postings)) == 1


def test_filter_new_suppresses_across_runs(tmp_path):
    path = tmp_path / "seen.json"
    posting = make("greenhouse:o2x", "1", "Coach", "O2X")

    first = Store.load(path)
    assert first.filter_new([posting]) == [posting]
    first.mark(posting, "published")
    first.save()

    second = Store.load(path)
    assert second.filter_new([posting]) == []


def test_mark_preserves_first_seen(tmp_path):
    path = tmp_path / "seen.json"
    posting = make("greenhouse:o2x", "1", "Coach", "O2X")
    store = Store.load(path)
    store.mark(posting, "review")
    original = store.records[posting.identity].first_seen

    store.mark(posting, "published")
    assert store.records[posting.identity].first_seen == original
    assert store.records[posting.identity].status == "published"


def test_corrupt_state_file_starts_clean(tmp_path):
    """A truncated state file must not wedge the pipeline."""
    path = tmp_path / "seen.json"
    path.write_text("{ this is not json")
    store = Store.load(path)
    assert store.records == {}


def test_save_is_atomic_and_leaves_no_temp_file(tmp_path):
    path = tmp_path / "nested" / "seen.json"
    store = Store.load(path)
    store.mark(make("greenhouse:o2x", "1", "Coach", "O2X"), "published")
    store.save()
    assert path.exists()
    assert not path.with_suffix(".json.tmp").exists()
    assert json.loads(path.read_text())["schema"] == 1


def test_prune_drops_stale_records(tmp_path):
    store = Store.load(tmp_path / "seen.json")
    posting = make("greenhouse:o2x", "1", "Coach", "O2X")
    store.mark(posting, "published")
    old = (datetime.now(timezone.utc) - timedelta(days=200)).isoformat()
    store.records[posting.identity].last_seen = old

    assert store.prune(90) == 1
    assert store.records == {}
    # The fingerprint index must be released too, or the job could never
    # be re-published after it ages out.
    assert store.filter_new([posting]) == [posting]


def test_prune_keeps_recent_records(tmp_path):
    store = Store.load(tmp_path / "seen.json")
    store.mark(make("greenhouse:o2x", "1", "Coach", "O2X"), "published")
    assert store.prune(90) == 0
    assert len(store.records) == 1
