"""Parsing helpers and end-to-end pipeline wiring."""

from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

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
    assert looks_remote(None, "Telework eligible")
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
        sources=[SourceConfig(kind="stub", name="stub")], state_path=tmp_path / "seen.json"
    )
    report = run(config)
    assert report.rejected == 1 and report.review == []
