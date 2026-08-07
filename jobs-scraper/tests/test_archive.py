"""Archive corpus tests: idempotency, revision history, and corruption tolerance."""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.archive import ARCHIVED_AT, Archive  # noqa: E402
from tactical_jobs.models import JobPosting  # noqa: E402


def make(
    source: str = "greenhouse:o2x",
    source_id: str = "1",
    title: str = "Tactical Strength and Conditioning Coach",
    employer: str = "O2X Human Performance",
    location: str = "Fort Liberty, NC",
    description: str = "CSCS and TSAC-F required. Embedded with a THOR3 team.",
    **extra,
) -> JobPosting:
    return JobPosting(
        source=source,
        source_id=source_id,
        url=f"https://example.invalid/{source}/{source_id}",
        title=title,
        employer=employer,
        location=location,
        description=description,
        **extra,
    )


def lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").split("\n") if line]


# --------------------------------------------------------------------------
# Missing file: an empty corpus is the normal first-run state, not an error.
# --------------------------------------------------------------------------


def test_load_missing_file_does_not_raise_or_create(tmp_path):
    path = tmp_path / "archive.jsonl"
    archive = Archive.load(path)
    assert archive.path == path
    assert not path.exists()


def test_records_on_missing_file_returns_empty_list(tmp_path):
    assert Archive.load(tmp_path / "nope.jsonl").records() == []


def test_latest_by_identity_on_missing_file_is_empty(tmp_path):
    assert Archive.load(tmp_path / "nope.jsonl").latest_by_identity() == {}


def test_stats_on_missing_file_is_zeroed(tmp_path):
    stats = Archive.load(tmp_path / "nope.jsonl").stats()
    assert stats["exists"] is False
    assert stats["records"] == 0
    assert stats["identities"] == 0
    assert stats["bytes"] == 0
    assert stats["first_archived_at"] is None
    assert stats["top_employers"] == []


# --------------------------------------------------------------------------
# Writing
# --------------------------------------------------------------------------


def test_append_writes_one_line_per_posting(tmp_path):
    path = tmp_path / "archive.jsonl"
    archive = Archive.load(path)
    written = archive.append([make(source_id="1"), make(source_id="2")])
    assert written == 2
    assert len(lines(path)) == 2


def test_append_creates_parent_directories(tmp_path):
    path = tmp_path / "deep" / "nested" / "archive.jsonl"
    Archive.load(path).append([make()])
    assert path.exists()


def test_append_of_empty_batch_writes_nothing(tmp_path):
    path = tmp_path / "archive.jsonl"
    assert Archive.load(path).append([]) == 0
    assert not path.exists()


def test_every_line_is_an_independent_json_object(tmp_path):
    """The JSONL contract: no enclosing array, one whole record per line."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id=str(n)) for n in range(5)])
    for line in lines(path):
        assert isinstance(json.loads(line), dict)


def test_record_is_archive_dict_plus_archived_at(tmp_path):
    path = tmp_path / "archive.jsonl"
    posting = make()
    Archive.load(path).append([posting])
    record = json.loads(lines(path)[0])
    assert set(record) == set(posting.to_archive_dict()) | {ARCHIVED_AT}


def test_archived_at_is_a_parseable_utc_timestamp(tmp_path):
    path = tmp_path / "archive.jsonl"
    before = datetime.now(timezone.utc)
    Archive.load(path).append([make()])
    stamp = datetime.fromisoformat(json.loads(lines(path)[0])[ARCHIVED_AT])
    assert stamp.tzinfo is not None
    assert before - timedelta(seconds=5) <= stamp <= datetime.now(timezone.utc)


def test_enrichment_and_tags_survive_the_round_trip(tmp_path):
    path = tmp_path / "archive.jsonl"
    posting = make()
    posting.tags = ["sof", "strength-conditioning"]
    posting.enrichment = {
        "certifications": ["CSCS", "TSAC-F"],
        "clearance": "TS/SCI",
        "installation": "Fort Liberty",
    }
    Archive.load(path).append([posting])
    record = Archive.load(path).records()[0]
    assert record["tags"] == ["sof", "strength-conditioning"]
    assert record["enrichment"]["clearance"] == "TS/SCI"


def test_non_ascii_text_is_stored_unescaped(tmp_path):
    """ensure_ascii=False keeps the corpus greppable by a human."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(employer="Fuerza Aérea Performance")])
    assert "Aérea" in path.read_text(encoding="utf-8")
    assert Archive.load(path).records()[0]["employer"] == "Fuerza Aérea Performance"


# --------------------------------------------------------------------------
# Full fidelity: the archive is the one place nothing is excerpted.
# --------------------------------------------------------------------------


def test_full_description_survives_at_full_length(tmp_path):
    path = tmp_path / "archive.jsonl"
    body = "POTFF human performance duties. " * 200
    body = (body + "x" * 5000)[:5000]
    assert len(body) == 5000

    Archive.load(path).append([make(description=body)])
    record = Archive.load(path).records()[0]

    assert record["description"] == body
    assert len(record["description"]) == 5000
    assert record["description_chars"] == 5000


def test_source_id_is_preserved_for_re_fetching(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id="USAJOBS-8827311")])
    assert Archive.load(path).records()[0]["source_id"] == "USAJOBS-8827311"


# --------------------------------------------------------------------------
# Idempotency and the revision rule
# --------------------------------------------------------------------------


def test_repeat_within_one_batch_writes_one_line(tmp_path):
    path = tmp_path / "archive.jsonl"
    posting = make()
    assert Archive.load(path).append([posting, posting]) == 1
    assert len(lines(path)) == 1


def test_repeat_within_one_open_archive_writes_nothing(tmp_path):
    path = tmp_path / "archive.jsonl"
    archive = Archive.load(path)
    archive.append([make()])
    assert archive.append([make()]) == 0
    assert len(lines(path)) == 1


def test_repeat_across_reloads_writes_nothing(tmp_path):
    """The nightly case: yesterday's open jobs are re-fetched unchanged."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make()])
    assert Archive.load(path).append([make()]) == 0
    assert len(lines(path)) == 1


def test_distinct_identities_are_both_archived(tmp_path):
    path = tmp_path / "archive.jsonl"
    archive = Archive.load(path)
    archive.append([make(source="greenhouse:o2x", source_id="1")])
    assert archive.append([make(source="usajobs:fed", source_id="1")]) == 1
    assert len(lines(path)) == 2


def test_changed_description_writes_a_new_line(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(description="CSCS required.")])
    assert Archive.load(path).append([make(description="CSCS and TSAC-F required.")]) == 1

    records = Archive.load(path).records()
    assert len(records) == 2
    assert records[0]["id"] == records[1]["id"]
    assert records[1]["description"] == "CSCS and TSAC-F required."


def test_changed_compensation_writes_a_new_line(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(compensation="$75,000 - $85,000")])
    assert Archive.load(path).append([make(compensation="$85,000 - $95,000")]) == 1
    assert len(lines(path)) == 2


def test_changed_enrichment_writes_a_new_line(tmp_path):
    """A clearance quietly appearing later is exactly the signal we keep."""
    path = tmp_path / "archive.jsonl"
    first = make()
    first.enrichment = {"clearance": None}
    second = make()
    second.enrichment = {"clearance": "Secret"}

    Archive.load(path).append([first])
    assert Archive.load(path).append([second]) == 1
    assert len(lines(path)) == 2


def test_reverted_content_writes_a_third_line(tmp_path):
    """A -> B -> A is three lines: history, not a set of versions seen."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(description="A")])
    Archive.load(path).append([make(description="B")])
    assert Archive.load(path).append([make(description="A")]) == 1

    records = Archive.load(path).records()
    assert [r["description"] for r in records] == ["A", "B", "A"]


def test_archived_at_alone_does_not_count_as_a_change(tmp_path):
    """Otherwise every run would look like an edit and bury the real ones."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make()])
    for _ in range(3):
        Archive.load(path).append([make()])
    assert len(lines(path)) == 1


# --------------------------------------------------------------------------
# Corruption tolerance: a killed process must not wedge the corpus.
# --------------------------------------------------------------------------


def test_corrupt_line_is_skipped_on_read(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id="1")])
    with path.open("a", encoding="utf-8") as handle:
        handle.write('{"id": "half-written", "descrip\n')
    Archive.load(path).append([make(source_id="2")])

    records = Archive.load(path).records()
    assert len(records) == 2
    assert {r["source_id"] for r in records} == {"1", "2"}


def test_blank_lines_are_ignored(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make()])
    with path.open("a", encoding="utf-8") as handle:
        handle.write("\n\n   \n")
    assert len(Archive.load(path).records()) == 1


def test_non_object_json_line_is_skipped(tmp_path):
    """A bare scalar or array is not a record, however valid its JSON."""
    path = tmp_path / "archive.jsonl"
    path.write_text('[1, 2, 3]\n"loose string"\n42\n', encoding="utf-8")
    assert Archive.load(path).records() == []


def test_corrupt_line_does_not_break_the_dedupe_index(tmp_path):
    """Garbage in the file must not cause a good posting to be re-archived."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make()])
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{ this is not json at all\n")
    assert Archive.load(path).append([make()]) == 0


def test_truncated_tail_line_does_not_corrupt_the_next_append(tmp_path):
    """A half-written last line has no newline; the next record must not fuse to it."""
    path = tmp_path / "archive.jsonl"
    path.write_text('{"id": "abc", "title": "Perfor', encoding="utf-8")

    assert Archive.load(path).append([make()]) == 1

    records = Archive.load(path).records()
    assert len(records) == 1
    assert records[0]["title"] == "Tactical Strength and Conditioning Coach"
    assert path.read_text(encoding="utf-8").endswith("\n")


def test_undecodable_bytes_do_not_raise(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make()])
    with path.open("ab") as handle:
        handle.write(b'{"id": "trunc", "description": "Fort Bra\xff\xfe\n')
    assert len(Archive.load(path).records()) == 1


# --------------------------------------------------------------------------
# latest_by_identity
# --------------------------------------------------------------------------


def test_latest_by_identity_returns_one_entry_per_job(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id="1"), make(source_id="2")])
    Archive.load(path).append([make(source_id="1", description="revised")])

    latest = Archive.load(path).latest_by_identity()
    assert len(latest) == 2
    assert len(Archive.load(path).records()) == 3


def test_latest_by_identity_picks_the_newest_revision(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(description="first")])
    Archive.load(path).append([make(description="second")])
    Archive.load(path).append([make(description="third")])

    latest = Archive.load(path).latest_by_identity()
    assert [r["description"] for r in latest.values()] == ["third"]


def test_latest_by_identity_uses_timestamps_not_file_order(tmp_path):
    """Lines can land out of order; archived_at is the authority."""
    path = tmp_path / "archive.jsonl"
    newest = {"id": "abc", "description": "newest", ARCHIVED_AT: "2026-06-01T00:00:00+00:00"}
    oldest = {"id": "abc", "description": "oldest", ARCHIVED_AT: "2025-01-01T00:00:00+00:00"}
    path.write_text(json.dumps(newest) + "\n" + json.dumps(oldest) + "\n", encoding="utf-8")

    assert Archive.load(path).latest_by_identity()["abc"]["description"] == "newest"


def test_latest_by_identity_keys_are_posting_identities(tmp_path):
    path = tmp_path / "archive.jsonl"
    posting = make()
    Archive.load(path).append([posting])
    assert set(Archive.load(path).latest_by_identity()) == {posting.identity}


def test_latest_by_identity_prefers_a_dated_record_over_an_undated_one(tmp_path):
    path = tmp_path / "archive.jsonl"
    undated = {"id": "abc", "description": "undated"}
    dated = {"id": "abc", "description": "dated", ARCHIVED_AT: "2026-06-01T00:00:00+00:00"}
    path.write_text(json.dumps(dated) + "\n" + json.dumps(undated) + "\n", encoding="utf-8")

    assert Archive.load(path).latest_by_identity()["abc"]["description"] == "dated"


# --------------------------------------------------------------------------
# stats
# --------------------------------------------------------------------------


def test_stats_counts_records_identities_and_revisions(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id="1"), make(source_id="2")])
    Archive.load(path).append([make(source_id="1", description="revised")])

    stats = Archive.load(path).stats()
    assert stats["records"] == 3
    assert stats["identities"] == 2
    assert stats["revisions"] == 1


def test_stats_counts_distinct_employers_and_sources(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append(
        [
            make(source="greenhouse:o2x", source_id="1", employer="O2X Human Performance"),
            make(source="usajobs:fed", source_id="2", employer="US Army H2F"),
            make(source="usajobs:fed", source_id="3", employer="US Army H2F"),
        ]
    )
    stats = Archive.load(path).stats()
    assert stats["employers"] == 2
    assert stats["sources"] == 2
    assert stats["top_employers"][0] == {"employer": "US Army H2F", "records": 2}


def test_stats_bytes_matches_the_file_on_disk(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id=str(n)) for n in range(3)])
    assert Archive.load(path).stats()["bytes"] == path.stat().st_size


def test_stats_reports_the_archived_date_span(tmp_path):
    path = tmp_path / "archive.jsonl"
    rows = [
        {"id": "a", ARCHIVED_AT: "2025-01-01T00:00:00+00:00"},
        {"id": "b", ARCHIVED_AT: "2026-06-01T00:00:00+00:00"},
        {"id": "c", ARCHIVED_AT: "2025-09-09T00:00:00+00:00"},
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    stats = Archive.load(path).stats()
    assert stats["first_archived_at"] == "2025-01-01T00:00:00+00:00"
    assert stats["last_archived_at"] == "2026-06-01T00:00:00+00:00"


def test_stats_reports_the_posted_date_span(tmp_path):
    path = tmp_path / "archive.jsonl"
    old = make(source_id="1", posted_at=datetime(2025, 3, 1, tzinfo=timezone.utc))
    new = make(source_id="2", posted_at=datetime(2026, 4, 15, tzinfo=timezone.utc))
    Archive.load(path).append([old, new])

    stats = Archive.load(path).stats()
    assert stats["first_posted_at"].startswith("2025-03-01")
    assert stats["last_posted_at"].startswith("2026-04-15")


def test_stats_sums_description_characters(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append(
        [make(source_id="1", description="x" * 1200), make(source_id="2", description="y" * 800)]
    )
    assert Archive.load(path).stats()["description_chars"] == 2000


def test_stats_ignores_corrupt_lines(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make()])
    with path.open("a", encoding="utf-8") as handle:
        handle.write("{ truncated\n")
    assert Archive.load(path).stats()["records"] == 1


def test_stats_is_json_serializable(tmp_path):
    """It gets embedded in run reports and status pages verbatim."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make()])
    assert json.loads(json.dumps(Archive.load(path).stats()))["records"] == 1


def test_stats_revisions_not_inflated_by_records_without_an_id(tmp_path):
    """A stray id-less line is a record, but it is not somebody's second version."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make()])
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps({"title": "no id here"}) + "\n")

    stats = Archive.load(path).stats()
    assert stats["records"] == 2
    assert stats["identities"] == 1
    assert stats["revisions"] == 0


def test_stats_description_chars_ignores_a_boolean(tmp_path):
    """bool is an int in Python, so `true` would otherwise silently add 1."""
    path = tmp_path / "archive.jsonl"
    rows = [
        {"id": "a", "description_chars": True},
        {"id": "b", "description_chars": -5},
        {"id": "c", "description_chars": 700},
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
    assert Archive.load(path).stats()["description_chars"] == 700


def test_stats_top_employers_is_capped_and_ordered(tmp_path):
    path = tmp_path / "archive.jsonl"
    postings = []
    for rank in range(12):
        # Employer 0 gets 12 records, employer 11 gets one: a strict ordering.
        for copy in range(12 - rank):
            postings.append(make(source_id=f"{rank}-{copy}", employer=f"Employer {rank:02d}"))
    Archive.load(path).append(postings)

    top = Archive.load(path).stats()["top_employers"]
    assert len(top) == 10
    assert [entry["records"] for entry in top] == [12, 11, 10, 9, 8, 7, 6, 5, 4, 3]
    assert top[0]["employer"] == "Employer 00"


def test_stats_breaks_employer_ties_by_name(tmp_path):
    """Stable output matters: this dict gets committed into a status file."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append(
        [
            make(source_id="1", employer="Zulu Performance"),
            make(source_id="2", employer="Alpha Performance"),
        ]
    )
    top = Archive.load(path).stats()["top_employers"]
    assert [entry["employer"] for entry in top] == ["Alpha Performance", "Zulu Performance"]


# --------------------------------------------------------------------------
# Hostile content. Descriptions are scraped HTML; they contain anything.
# --------------------------------------------------------------------------


def test_lone_surrogate_in_description_does_not_crash_the_append(tmp_path):
    """Regression: json.dumps emits a raw surrogate that UTF-8 cannot encode.

    Badly decoded scraped HTML yields these, and an unhandled UnicodeEncodeError
    here would take down the whole archive stage of a nightly run.
    """
    path = tmp_path / "archive.jsonl"
    assert Archive.load(path).append([make(description="Fort Bragg \ud800 coach")]) == 1

    records = Archive.load(path).records()
    assert len(records) == 1
    assert records[0]["description"].startswith("Fort Bragg ")


def test_lone_surrogate_stays_idempotent_across_a_reload(tmp_path):
    """Scrubbing has to happen before the hash, or the fix trades a crash for a leak."""
    path = tmp_path / "archive.jsonl"
    posting = make(description="THOR3 \udfff human performance")
    Archive.load(path).append([posting])
    assert Archive.load(path).append([make(description="THOR3 \udfff human performance")]) == 0
    assert len(lines(path)) == 1


def test_lone_surrogate_in_employer_and_title_does_not_crash(tmp_path):
    path = tmp_path / "archive.jsonl"
    written = Archive.load(path).append(
        [make(employer="O2X \ud83d", title="Coach \udc00", location="Coronado \ud800")]
    )
    assert written == 1
    assert len(Archive.load(path).records()) == 1


def test_integer_keyed_enrichment_does_not_re_archive_every_run(tmp_path):
    """Regression: int keys sort numerically in memory and lexically off disk.

    Hashing the in-memory shape made 9/10 order one way and "10"/"9" the other,
    so an unchanged posting grew a bogus revision on every single run.
    """
    path = tmp_path / "archive.jsonl"

    def posting() -> JobPosting:
        job = make()
        job.enrichment = {"salary_by_year": {9: 91000, 10: 102000, 2: 82000}}
        return job

    assert Archive.load(path).append([posting()]) == 1
    assert Archive.load(path).append([posting()]) == 0
    assert Archive.load(path).append([posting()]) == 0
    assert len(lines(path)) == 1


def test_mixed_key_types_in_enrichment_do_not_crash(tmp_path):
    """Regression: sort_keys over {1: ..., "b": ...} raises TypeError."""
    path = tmp_path / "archive.jsonl"
    posting = make()
    posting.enrichment = {"scores": {1: "one", "b": "two"}}
    assert Archive.load(path).append([posting]) == 1
    assert Archive.load(path).records()[0]["enrichment"]["scores"]["b"] == "two"


def test_unserializable_key_type_in_enrichment_does_not_crash(tmp_path):
    """A tuple key is dropped, not raised. Losing one oddity beats losing the run."""
    path = tmp_path / "archive.jsonl"
    posting = make()
    posting.enrichment = {"pairs": {("CSCS", "TSAC-F"): 3, "flat": 1}}
    assert Archive.load(path).append([posting]) == 1
    assert Archive.load(path).records()[0]["enrichment"]["pairs"] == {"flat": 1}


def test_datetime_in_enrichment_stringifies_and_stays_idempotent(tmp_path):
    path = tmp_path / "archive.jsonl"

    def posting() -> JobPosting:
        job = make()
        job.enrichment = {"closes_at": datetime(2026, 9, 1, tzinfo=timezone.utc)}
        return job

    assert Archive.load(path).append([posting()]) == 1
    assert Archive.load(path).append([posting()]) == 0
    assert isinstance(Archive.load(path).records()[0]["enrichment"]["closes_at"], str)


def test_tuple_in_enrichment_stays_idempotent_across_a_reload(tmp_path):
    """A tuple becomes a list off disk; the hash must not notice the difference."""
    path = tmp_path / "archive.jsonl"

    def posting() -> JobPosting:
        job = make()
        job.enrichment = {"certifications": ("CSCS", "TSAC-F")}
        return job

    assert Archive.load(path).append([posting()]) == 1
    assert Archive.load(path).append([posting()]) == 0
    assert Archive.load(path).records()[0]["enrichment"]["certifications"] == ["CSCS", "TSAC-F"]


def test_newlines_in_a_description_stay_on_one_line(tmp_path):
    """The JSONL contract dies if a description's newlines reach the file raw."""
    path = tmp_path / "archive.jsonl"
    body = "Duties:\nH2F squad.\r\nCSCS required.\n\n\tTS/SCI. Fort Carson."
    Archive.load(path).append([make(description=body)])

    assert len(lines(path)) == 1
    assert Archive.load(path).records()[0]["description"] == body


def test_a_description_that_looks_like_json_stays_one_record(tmp_path):
    path = tmp_path / "archive.jsonl"
    body = '{"id": "injected", "employer": "Fake"}\n{"id": "injected2"}'
    Archive.load(path).append([make(description=body)])

    records = Archive.load(path).records()
    assert len(records) == 1
    assert records[0]["description"] == body


def test_empty_strings_and_none_fields_round_trip(tmp_path):
    path = tmp_path / "archive.jsonl"
    posting = make(description="", location="", employer="", title="")
    Archive.load(path).append([posting])

    record = Archive.load(path).records()[0]
    assert record["description"] == ""
    assert record["description_chars"] == 0
    assert record["department"] is None
    assert record["compensation"] is None
    assert record["posted_at"] is None


def test_a_blank_posting_is_still_deduped(tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(description="", location="")])
    assert Archive.load(path).append([make(description="", location="")]) == 0


def test_a_very_long_description_survives_intact(tmp_path):
    """Well past the 5000-char case: the archive has no truncation anywhere."""
    path = tmp_path / "archive.jsonl"
    body = "".join(f"Requirement {n}: CSCS, TSAC-F, ATC, RD. " for n in range(6000))
    assert len(body) > 200_000

    Archive.load(path).append([make(description=body)])
    record = Archive.load(path).records()[0]
    assert record["description"] == body
    assert record["description_chars"] == len(body)
    assert len(lines(path)) == 1


def test_emoji_and_astral_characters_survive(tmp_path):
    path = tmp_path / "archive.jsonl"
    body = "Coach \U0001f3cb\U0001f3fd training 体力 at JBLM"
    Archive.load(path).append([make(description=body)])
    assert Archive.load(path).records()[0]["description"] == body


# --------------------------------------------------------------------------
# Malformed timestamps must not abort a read.
# --------------------------------------------------------------------------


def test_out_of_range_archived_at_does_not_crash_latest_by_identity(tmp_path):
    """Regression: shifting a year-1 stamp to UTC raises OverflowError, not ValueError."""
    path = tmp_path / "archive.jsonl"
    rows = [
        {"id": "abc", "description": "overflowing", ARCHIVED_AT: "0001-01-01T00:00:00+05:00"},
        {"id": "abc", "description": "sane", ARCHIVED_AT: "2026-06-01T00:00:00+00:00"},
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    assert Archive.load(path).latest_by_identity()["abc"]["description"] == "sane"


def test_garbage_archived_at_values_do_not_crash(tmp_path):
    path = tmp_path / "archive.jsonl"
    rows = [
        {"id": "a", ARCHIVED_AT: "not a timestamp"},
        {"id": "b", ARCHIVED_AT: ""},
        {"id": "c", ARCHIVED_AT: 17},
        {"id": "d", ARCHIVED_AT: None},
        {"id": "e", ARCHIVED_AT: "2026-13-45T99:00:00"},
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    assert len(Archive.load(path).latest_by_identity()) == 5
    assert Archive.load(path).stats()["records"] == 5


def test_naive_archived_at_is_treated_as_utc(tmp_path):
    path = tmp_path / "archive.jsonl"
    rows = [
        {"id": "abc", "description": "naive-newer", ARCHIVED_AT: "2026-06-02T00:00:00"},
        {"id": "abc", "description": "aware-older", ARCHIVED_AT: "2026-06-01T00:00:00+00:00"},
    ]
    path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")

    assert Archive.load(path).latest_by_identity()["abc"]["description"] == "naive-newer"


# --------------------------------------------------------------------------
# The memory contract: the corpus is allowed to outgrow RAM.
# --------------------------------------------------------------------------


def test_load_does_not_materialize_the_corpus(monkeypatch, tmp_path):
    """Regression: load() went through records(), holding every line in memory.

    The dedupe index is 20 bytes per job by design. Building it by first
    listing the entire corpus put a ceiling on a file that is supposed to have
    none, so load() must not depend on records() at all.
    """
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id=str(n)) for n in range(3)])

    def forbidden(self):
        raise AssertionError("load() must stream, not materialize the corpus")

    monkeypatch.setattr(Archive, "records", forbidden)
    archive = Archive.load(path)
    assert archive.append([make(source_id="0")]) == 0
    assert archive.append([make(source_id="99")]) == 1


def test_stats_does_not_materialize_the_corpus(monkeypatch, tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id=str(n)) for n in range(3)])

    def forbidden(self):
        raise AssertionError("stats() must stream, not materialize the corpus")

    archive = Archive.load(path)
    monkeypatch.setattr(Archive, "records", forbidden)
    assert archive.stats()["records"] == 3


def test_latest_by_identity_does_not_materialize_the_corpus(monkeypatch, tmp_path):
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id=str(n)) for n in range(3)])

    def forbidden(self):
        raise AssertionError("latest_by_identity() must stream")

    archive = Archive.load(path)
    monkeypatch.setattr(Archive, "records", forbidden)
    assert len(archive.latest_by_identity()) == 3


# --------------------------------------------------------------------------
# Durability
# --------------------------------------------------------------------------


def test_appends_accumulate_rather_than_rewrite(tmp_path):
    """Append-only: an earlier line is never touched by a later run."""
    path = tmp_path / "archive.jsonl"
    Archive.load(path).append([make(source_id="1")])
    first_line = lines(path)[0]

    for n in range(2, 6):
        Archive.load(path).append([make(source_id=str(n))])

    assert lines(path)[0] == first_line
    assert len(lines(path)) == 5


def test_file_always_ends_with_a_newline_after_append(tmp_path):
    path = tmp_path / "archive.jsonl"
    archive = Archive.load(path)
    for n in range(3):
        archive.append([make(source_id=str(n))])
        assert path.read_text(encoding="utf-8").endswith("\n")


def test_a_dangling_line_is_only_healed_when_there_is_something_to_write(tmp_path):
    """A no-op run must not rewrite the file at all."""
    path = tmp_path / "archive.jsonl"
    path.write_text('{"id": "abc", "title": "Perfor', encoding="utf-8")
    before = path.read_text(encoding="utf-8")

    assert Archive.load(path).append([]) == 0
    assert path.read_text(encoding="utf-8") == before
