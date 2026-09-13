"""The two hand-edited data files.

The standards panel is edited by a person on purpose — the brief is explicit
that the bot must not edit it. That makes a typo the likely failure, so these
check shape rather than content: a row that loses its URL stops the weekly
page-change watch silently, which is the failure that matters.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_research.identifiers import is_fetchable  # noqa: E402
from tactical_research.models import SECTORS  # noqa: E402

PKG = Path(__file__).resolve().parents[1] / "tactical_research"
SOURCES = json.loads((PKG / "sources.json").read_text(encoding="utf-8"))
STANDARDS = json.loads((PKG / "standards.json").read_text(encoding="utf-8"))


class TestSources:
    def test_every_source_has_a_name_sector_and_purpose(self):
        for source in SOURCES["sources"]:
            assert source["name"].strip()
            assert source["gives"].strip()
            assert source["sector"] in SECTORS, source["name"]

    def test_every_sector_the_brief_adds_is_covered(self):
        """The old board was military only; the brief brings in fire, EMS and LE."""
        covered = {s["sector"] for s in SOURCES["sources"]}
        assert {"FIRE", "EMS", "LE", "CROSS"} <= covered

    def test_trade_press_is_marked_coverage_only(self):
        """It may fill a Reporting list; it may never become an item."""
        trade = [s for s in SOURCES["sources"] if "FireRescue1" in s["name"]]
        assert trade and all(s.get("coverage_only") for s in trade)

    def test_search_vocabulary_is_populated(self):
        vocab = SOURCES["search_vocabulary"]
        groups = [k for k in vocab if not k.startswith("_")]
        assert set(groups) == {
            "people", "pubmed_mesh", "standards_and_tests", "health", "programs_and_funding"
        }
        assert all(vocab[g] for g in groups)


class TestStandardsPanel:
    def test_the_rows_the_brief_names_are_present(self):
        names = " | ".join(r["name"] for r in STANDARDS["rows"])
        for expected in ("AFT", "Body Composition", "Air Force", "Navy", "Marine Corps",
                         "Space Force", "1308.03", "NFPA 1580", "CPAT",
                         "Work Capacity Test", "POST", "FBI"):
            assert expected in names, expected

    def test_every_row_has_a_url_to_watch(self):
        """A row without a URL silently drops out of the weekly change watch."""
        for row in STANDARDS["rows"]:
            assert row["url"].startswith("https://"), row["name"]

    def test_every_row_has_a_sector_and_a_verified_date(self):
        for row in STANDARDS["rows"]:
            assert row["sector"] in SECTORS, row["name"]
            assert row["last_verified"], row["name"]

    def test_rows_point_at_official_hosts(self):
        """A standard sourced from trade press is not a standard.

        This asserts an official host rather than the brief's fetch allowlist,
        because the two serve different purposes. The allowlist governs writing
        a blurb *from* a document; the panel's job is to watch a page for change.
        They also disagree in practice: the Army Fitness Test page is at
        army.mil/aft/, and the brief allowlists armypubs.army.mil but not bare
        army.mil — even though it allowlists af.mil and spaceforce.mil whole.
        """
        official = (".mil", ".gov", "iaff.org", "nfpa.org")
        for row in STANDARDS["rows"]:
            host = row["url"].split("/")[2].lower()
            assert any(host.endswith(suffix) for suffix in official), row["name"]

    def test_no_duplicate_rows(self):
        names = [r["name"] for r in STANDARDS["rows"]]
        assert len(names) == len(set(names))
