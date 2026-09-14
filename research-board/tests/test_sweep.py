"""The sweep's non-network behaviour.

Fetching is not tested here — that is what the CI run exercises against real
hosts. What is tested is the part that decides, and above all the gate: the
board must not render from data that does not validate, because a malformed
item on a public page is worse than a page that did not update.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import sweep as sweep_module  # noqa: E402
from tactical_research.cluster import Item  # noqa: E402
from tactical_research.identifiers import primary_identifier  # noqa: E402

VALID = {
    "headline": "Army reissues the fitness test standard",
    "blurb": "The Army published an updated standard. It changes scoring for "
             "combat arms roles. Programs built on last year's tables need rework.",
    "primary_url": "https://armypubs.army.mil/aft",
    "date_published": "2026-09-10",
    "type": "Policy",
    "sector": "MIL",
    "tags": ["Standards and tests"],
}


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    """Point the sweep's paths at a scratch directory."""
    monkeypatch.setattr(sweep_module, "FINDINGS", tmp_path / "findings.json")
    monkeypatch.setattr(sweep_module, "OUT", tmp_path / "site")
    return tmp_path


def write(workspace, *items):
    (workspace / "findings.json").write_text(json.dumps({"items": list(items)}), encoding="utf-8")


class TestRenderGate:
    def test_renders_both_pages_from_valid_findings(self, workspace):
        write(workspace, VALID)
        assert sweep_module.render() == 0
        assert (workspace / "site" / "board.html").exists()
        assert (workspace / "site" / "archive.html").exists()

    def test_refuses_to_render_an_invalid_item(self, workspace):
        write(workspace, {**VALID, "tags": ["Not a real tag"]})
        assert sweep_module.render() == 1
        assert not (workspace / "site").exists()

    def test_one_bad_item_stops_the_whole_render(self, workspace):
        # Publishing the good half of a batch would quietly drop items and make
        # the board look complete when it is not.
        write(workspace, VALID, {**VALID, "type": "Opinion"})
        assert sweep_module.render() == 1

    def test_missing_findings_is_reported_not_crashed(self, workspace):
        assert sweep_module.render() == 1


class TestDocumentReading:
    """read_documents is where an unreadable page must not become an item."""

    def item(self, url="https://armypubs.army.mil/doc", published=""):
        return Item(
            key="k", primary_url=url,
            identifier=primary_identifier("AR 350-1"),
            title="Source listing title", published=published,
        )

    def readable(self):
        return "<html><body><h1>A Real Document</h1><p>" + ("finding " * 60) + "</p></body></html>"

    def test_a_readable_document_becomes_a_candidate(self, monkeypatch):
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (self.readable(), 200))
        candidates, tally = sweep_module.read_documents([self.item()], date(2026, 9, 13))
        assert len(candidates) == 1 and tally["fetched"] == 1
        assert candidates[0]["document_title"] == "A Real Document"
        assert candidates[0]["excerpt"]

    def test_an_unreadable_page_never_becomes_a_candidate(self, monkeypatch):
        # A 200 that yielded nothing. Writing a blurb from this would mean
        # writing it from the headline, which is the failure the brief names.
        shell = '<html><head><title>Loading…</title></head><body><div id="root"></div></body></html>'
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (shell, 200))
        candidates, tally = sweep_module.read_documents([self.item()], date(2026, 9, 13))
        assert candidates == [] and tally["unreadable"] == 1

    def test_a_refused_document_is_counted_not_invented(self, monkeypatch):
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (None, 403))
        candidates, tally = sweep_module.read_documents([self.item()], date(2026, 9, 13))
        assert candidates == [] and tally["refused"] == 1

    def test_an_item_far_outside_the_lookback_is_skipped(self, monkeypatch):
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (self.readable(), 200))
        old = self.item(published="2024-01-01")
        candidates, tally = sweep_module.read_documents([old], date(2026, 9, 13))
        assert candidates == [] and tally["stale"] == 1

    def test_a_non_allowlisted_url_is_not_fetched_as_a_document(self, monkeypatch):
        # The allowlist is the trust boundary for what a blurb may be written
        # from. Coverage reaches the page as a Reporting link, never as a source.
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (self.readable(), 200))
        trade = self.item(url="https://www.militarytimes.com/story")
        candidates, _ = sweep_module.read_documents([trade], date(2026, 9, 13))
        assert candidates == []

    def test_the_sweep_never_writes_a_blurb(self, monkeypatch):
        """The one invariant worth a test of its own."""
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (self.readable(), 200))
        candidates, _ = sweep_module.read_documents([self.item()], date(2026, 9, 13))
        assert "blurb" not in candidates[0]


class TestQuietSources:
    """A source contributing nothing must say so.

    The first live run crawled NFPA and the OSHA docket successfully and got
    zero links from both — they render their listings client-side. Counted as
    "crawled", they look identical to a quiet week, which is how a registry
    rots while every run stays green.
    """

    SOURCES = [{"name": "NFPA", "url": "https://www.nfpa.org/"}]

    def test_a_source_yielding_no_links_is_named(self, monkeypatch):
        shell = '<html><body><div id="root"></div></body></html>'
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (shell, 200))
        _, tally = sweep_module.gather(self.SOURCES)
        assert tally["empty"] == 1
        assert tally["quiet_sources"] == ["NFPA (0 links)"]

    def test_a_refused_source_is_named_too(self, monkeypatch):
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (None, 403))
        _, tally = sweep_module.gather(self.SOURCES)
        assert tally["refused"] == 1 and tally["gone"] == 0
        assert tally["quiet_sources"] == ["NFPA (refused: HTTP 403)"]

    def test_a_dead_source_is_reported_as_gone_not_refused(self, monkeypatch):
        """Different problems, different fixes.

        A 404 needs the registry entry repointed; a 403 is the host declining
        the robot and the entry may be perfectly correct. Collapsing the two —
        which the first version of this did — is how a dead entry hides behind
        a bot filter and never gets fixed.
        """
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (None, 404))
        _, tally = sweep_module.gather(self.SOURCES)
        assert tally["gone"] == 1 and tally["refused"] == 0
        assert "gone" in tally["quiet_sources"][0]

    def test_a_source_that_never_answered_is_refused_not_gone(self, monkeypatch):
        # A timeout says nothing about whether the page exists.
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (None, None))
        _, tally = sweep_module.gather(self.SOURCES)
        assert tally["refused"] == 1 and tally["gone"] == 0
        assert "no response" in tally["quiet_sources"][0]

    def test_a_working_source_is_not_named(self, monkeypatch):
        page = '<html><body><a href="/r">Firefighter fatalities report 2026</a></body></html>'
        monkeypatch.setattr(sweep_module, "fetch", lambda url: (page, 200))
        sightings, tally = sweep_module.gather(self.SOURCES)
        assert tally["quiet_sources"] == [] and len(sightings) == 1


class TestSourcesWithNoUrl:
    """A registry entry with no URL is never crawled.

    Two entries — the event pages and the trade press — name several sites each
    and carry no single URL. Skipped in silence, they let the registry claim 17
    sources when 15 is the real number.
    """

    def test_a_source_without_a_url_is_counted_and_named(self):
        sightings, tally = sweep_module.gather([{"name": "Event pages: several", "url": ""}])
        assert sightings == [] and tally["no_url"] == 1
        assert tally["quiet_sources"] == ["Event pages: several (no URL to crawl)"]

    def test_it_is_not_mistaken_for_a_refusal(self):
        # Nothing was requested, so nothing refused. Reporting it as a refusal
        # would send someone hunting for a bot filter that does not exist.
        _, tally = sweep_module.gather([{"name": "Event pages: several", "url": ""}])
        assert tally["refused"] == 0 and tally["gone"] == 0
