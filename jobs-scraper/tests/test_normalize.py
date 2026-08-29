"""Parsing helpers and end-to-end pipeline wiring."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.classify import Thresholds  # noqa: E402
from tactical_jobs.config import Config, ConfigError, SourceConfig  # noqa: E402
from tactical_jobs.models import JobPosting  # noqa: E402
from tactical_jobs.pipeline import run  # noqa: E402
from tactical_jobs.sources.base import html_to_text, looks_remote, parse_timestamp  # noqa: E402


# --------------------------------------------------------------------------
# html_to_text
# --------------------------------------------------------------------------

def test_html_to_text_inserts_boundaries_between_blocks():
    """Naive tag-stripping would glue 'experience' to 'CSCS' and break matching."""
    html = "<ul><li>5 years experience</li><li>CSCS required</li></ul>"
    text = html_to_text(html)
    assert "experienceCSCS" not in text
    assert "experience" in text and "CSCS" in text


def test_html_to_text_drops_script_and_style():
    html = "<div>Real text</div><script>var x = 'hidden';</script><style>.a{}</style>"
    text = html_to_text(html)
    assert "Real text" in text
    assert "hidden" not in text and ".a{}" not in text


def test_html_to_text_unescapes_entities():
    assert "Strength & Conditioning" in html_to_text("<p>Strength &amp; Conditioning</p>")


def test_html_to_text_passes_through_plain_text():
    assert html_to_text("Just  plain   text") == "Just plain text"


def test_html_to_text_handles_none_and_empty():
    assert html_to_text(None) == ""
    assert html_to_text("") == ""


# --------------------------------------------------------------------------
# parse_timestamp
# --------------------------------------------------------------------------

def test_parse_timestamp_iso_with_z():
    parsed = parse_timestamp("2026-03-04T10:00:00Z")
    assert parsed == datetime(2026, 3, 4, 10, 0, tzinfo=timezone.utc)


def test_parse_timestamp_date_only():
    assert parse_timestamp("2026-03-04").year == 2026


def test_parse_timestamp_rfc822_from_rss():
    parsed = parse_timestamp("Wed, 04 Mar 2026 10:00:00 +0000")
    assert parsed is not None and parsed.year == 2026


def test_parse_timestamp_distinguishes_seconds_from_milliseconds():
    seconds = parse_timestamp(1_772_000_000)
    millis = parse_timestamp(1_772_000_000_000)
    assert seconds is not None and millis is not None
    assert abs((seconds - millis).total_seconds()) < 1


def test_parse_timestamp_returns_none_on_garbage():
    assert parse_timestamp("not a date") is None
    assert parse_timestamp(None) is None
    assert parse_timestamp("") is None


def test_parse_timestamp_always_timezone_aware():
    assert parse_timestamp("2026-03-04T10:00:00").tzinfo is not None


def test_looks_remote():
    assert looks_remote("Remote - US")
    # "Telework eligible" must NOT read as remote: in federal usage it means
    # occasional work from home from a job that is otherwise on the
    # installation. Across 25 live USAJOBS announcements it was true on 10
    # while the actual remote flag was true on none, so treating it as a
    # synonym put on-base jobs in front of people filtering for remote work.
    assert not looks_remote(None, "Telework eligible")
    assert not looks_remote("Cannon AFB, New Mexico", "telework eligible")
    assert looks_remote(None, "Fully remote")
    assert not looks_remote("Fort Bragg, NC")


# --------------------------------------------------------------------------
# Config
# --------------------------------------------------------------------------

def test_config_expands_environment_variables(tmp_path, monkeypatch):
    monkeypatch.setenv("TEST_WEBHOOK", "https://example.invalid/hook")
    config_file = tmp_path / "sources.toml"
    config_file.write_text(
        '[[publisher]]\nkind = "webhook"\nurl = "${TEST_WEBHOOK}"\n'
    )
    config = Config.load(config_file)
    assert config.publishers[0].options["url"] == "https://example.invalid/hook"


def test_config_missing_env_var_fails_loudly(tmp_path, monkeypatch):
    monkeypatch.delenv("ABSENT_TOKEN", raising=False)
    config_file = tmp_path / "sources.toml"
    config_file.write_text('[[source]]\nkind = "greenhouse"\nboard_token = "${ABSENT_TOKEN}"\n')
    try:
        Config.load(config_file)
    except ConfigError as exc:
        assert "ABSENT_TOKEN" in str(exc)
    else:  # pragma: no cover
        raise AssertionError("expected ConfigError")


def test_an_optional_source_is_dropped_when_its_credential_is_absent(tmp_path, monkeypatch):
    # This is what lets the USAJOBS source live in sources.keyless.toml: an
    # operator with no key still gets every other source, instead of a run
    # that dies at startup.
    monkeypatch.delenv("ABSENT_TOKEN", raising=False)
    config_file = tmp_path / "sources.toml"
    config_file.write_text(
        '[[source]]\nkind = "usajobs"\nname = "federal"\noptional = true\n'
        'api_key = "${ABSENT_TOKEN}"\n\n'
        '[[source]]\nkind = "rss"\nname = "keyless"\nurl = "https://example.invalid/feed"\n'
    )
    config = Config.load(config_file)
    assert [source.name for source in config.sources] == ["keyless"]


def test_an_optional_source_still_loads_when_its_credential_is_present(tmp_path, monkeypatch):
    monkeypatch.setenv("PRESENT_TOKEN", "real-key")
    config_file = tmp_path / "sources.toml"
    config_file.write_text(
        '[[source]]\nkind = "usajobs"\nname = "federal"\noptional = true\n'
        'api_key = "${PRESENT_TOKEN}"\n'
    )
    config = Config.load(config_file)
    assert config.sources[0].options["api_key"] == "real-key"
    # `optional` is loader bookkeeping and must not reach the adapter.
    assert "optional" not in config.sources[0].options


def test_a_source_without_optional_still_fails_loudly(tmp_path, monkeypatch):
    # The leniency above is opt-in only. Everything else keeps the old
    # behaviour, because a publisher silently posting nowhere is the bug the
    # loud failure exists to prevent.
    monkeypatch.delenv("ABSENT_TOKEN", raising=False)
    config_file = tmp_path / "sources.toml"
    config_file.write_text(
        '[[source]]\nkind = "greenhouse"\nname = "x"\nboard_token = "${ABSENT_TOKEN}"\n'
    )
    with pytest.raises(ConfigError):
        Config.load(config_file)


def test_a_publisher_is_never_made_optional(tmp_path, monkeypatch):
    monkeypatch.delenv("ABSENT_TOKEN", raising=False)
    config_file = tmp_path / "sources.toml"
    config_file.write_text(
        '[[publisher]]\nkind = "webhook"\noptional = true\nurl = "${ABSENT_TOKEN}"\n'
    )
    with pytest.raises(ConfigError):
        Config.load(config_file)


def test_config_auto_publish_defaults_to_off(tmp_path):
    config_file = tmp_path / "sources.toml"
    config_file.write_text("[runtime]\n")
    assert Config.load(config_file).auto_publish is False


# --------------------------------------------------------------------------
# Pipeline
# --------------------------------------------------------------------------

class _StubSource:
    """Registered under a fake kind so run() exercises the real code path."""

    kind = "stub"
    postings: list[JobPosting] = []

    def __init__(self, name, options):
        self.name = name

    def fetch(self):
        return list(self.postings)


class _BrokenSource:
    kind = "broken"

    def __init__(self, name, options):
        self.name = name

    def fetch(self):
        raise RuntimeError("career page is down")


def _register_stubs(monkeypatch, postings):
    from tactical_jobs import sources

    _StubSource.postings = postings
    monkeypatch.setitem(sources._REGISTRY, "stub", _StubSource)
    monkeypatch.setitem(sources._REGISTRY, "broken", _BrokenSource)


def _tactical_posting(source_id: str = "1") -> JobPosting:
    return JobPosting(
        source="stub",
        source_id=source_id,
        url=f"https://example.invalid/{source_id}",
        title="Tactical Strength and Conditioning Coach",
        employer="USASOC",
        location="Fort Bragg, NC",
        description="THOR3 human performance program supporting special operations soldiers. CSCS required.",
        posted_at=datetime.now(timezone.utc),
    )


def test_pipeline_routes_to_review_when_auto_publish_off(tmp_path, monkeypatch):
    _register_stubs(monkeypatch, [_tactical_posting()])
    config = Config(
        sources=[SourceConfig(kind="stub", name="stub")],
        publishers=[],
        thresholds=Thresholds(),
        state_path=tmp_path / "seen.json",
        archive_path=tmp_path / "corpus.jsonl",
        insights_dir=tmp_path / "insights",
        auto_publish=False,
    )
    report = run(config)
    assert len(report.review) == 1
    assert report.approved == []


def test_pipeline_auto_publishes_when_enabled(tmp_path, monkeypatch):
    _register_stubs(monkeypatch, [_tactical_posting()])
    config = Config(
        sources=[SourceConfig(kind="stub", name="stub")],
        publishers=[],
        state_path=tmp_path / "seen.json",
        archive_path=tmp_path / "corpus.jsonl",
        insights_dir=tmp_path / "insights",
        auto_publish=True,
    )
    report = run(config)
    assert len(report.approved) == 1
    assert report.review == []


def test_pipeline_second_run_finds_no_new_jobs(tmp_path, monkeypatch):
    _register_stubs(monkeypatch, [_tactical_posting()])
    config = Config(
        sources=[SourceConfig(kind="stub", name="stub")],
        state_path=tmp_path / "seen.json",
        archive_path=tmp_path / "corpus.jsonl",
        insights_dir=tmp_path / "insights",
    )
    assert len(run(config).review) == 1
    second = run(config)
    assert second.review == [] and second.duplicates == 1


def test_pipeline_survives_a_broken_source(tmp_path, monkeypatch):
    """One dead career page must not take down the run."""
    _register_stubs(monkeypatch, [_tactical_posting()])
    config = Config(
        sources=[
            SourceConfig(kind="broken", name="dead-board"),
            SourceConfig(kind="stub", name="stub"),
        ],
        state_path=tmp_path / "seen.json",
        archive_path=tmp_path / "corpus.jsonl",
        insights_dir=tmp_path / "insights",
    )
    report = run(config)
    assert len(report.review) == 1
    assert len(report.errors) == 1
    assert "career page is down" in str(report.errors[0])


def test_pipeline_drops_stale_postings(tmp_path, monkeypatch):
    old = _tactical_posting()
    old.posted_at = datetime.now(timezone.utc) - timedelta(days=400)
    _register_stubs(monkeypatch, [old])
    config = Config(
        sources=[SourceConfig(kind="stub", name="stub")],
        state_path=tmp_path / "seen.json",
        archive_path=tmp_path / "corpus.jsonl",
        insights_dir=tmp_path / "insights",
        max_age_days=45,
    )
    report = run(config)
    assert report.stale == 1 and report.review == []


def test_dry_run_writes_no_state(tmp_path, monkeypatch):
    _register_stubs(monkeypatch, [_tactical_posting()])
    state = tmp_path / "seen.json"
    config = Config(sources=[SourceConfig(kind="stub", name="stub")], state_path=state)
    report = run(config, dry_run=True)
    assert len(report.review) == 1
    assert not state.exists()


def test_pipeline_skips_postings_without_a_url(tmp_path, monkeypatch):
    broken = _tactical_posting()
    broken.url = ""
    _register_stubs(monkeypatch, [broken])
    config = Config(
        sources=[SourceConfig(kind="stub", name="stub")],
        state_path=tmp_path / "seen.json",
        archive_path=tmp_path / "corpus.jsonl",
        insights_dir=tmp_path / "insights",
    )
    report = run(config)
    assert report.rejected == 1 and report.review == []


def test_pipeline_writes_nothing_outside_its_configured_paths(tmp_path, monkeypatch):
    """Regression: archive_path and insights_dir default to REPO-RELATIVE paths.

    A test that overrode only state_path left the pipeline writing a synthetic
    corpus and dashboard into the working tree, and those artifacts were then
    committed as if they were real scraped data.
    """
    _register_stubs(monkeypatch, [_tactical_posting()])
    scratch = tmp_path / "run"
    scratch.mkdir()
    monkeypatch.chdir(scratch)

    config = Config(
        sources=[SourceConfig(kind="stub", name="stub")],
        state_path=tmp_path / "seen.json",
        archive_path=tmp_path / "corpus.jsonl",
        insights_dir=tmp_path / "insights",
    )
    run(config)

    assert list(scratch.iterdir()) == [], f"leaked into cwd: {list(scratch.iterdir())}"


def test_archiving_can_be_disabled(tmp_path, monkeypatch):
    _register_stubs(monkeypatch, [_tactical_posting()])
    config = Config(
        sources=[SourceConfig(kind="stub", name="stub")],
        state_path=tmp_path / "seen.json",
        archive_path=None,
        insights_dir=None,
    )
    report = run(config)
    assert report.archived == 0
    assert not (tmp_path / "corpus.jsonl").exists()
