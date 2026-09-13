"""Identifier recognition and the fetch allowlist.

The cases are the ones the brief names, plus the ways each goes wrong in real
text: a renamed department, an identifier inside a sentence, a lookalike host.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_research.identifiers import (  # noqa: E402
    find_identifiers,
    host_of,
    is_fetchable,
    primary_identifier,
)


class TestIssuances:
    def test_dodi_and_dowi_are_the_same_document(self):
        """The department was renamed; a reissue must not split into two items."""
        a = primary_identifier("DoDI 1308.03 governs the fitness program")
        b = primary_identifier("DoWI 1308.03 update released")
        assert a.key == b.key == "dodi:1308.03"

    def test_dodi_resolves_to_the_official_host(self):
        ident = primary_identifier("DoWI 1308.03")
        assert "esd.whs.mil" in ident.url
        assert is_fetchable(ident.url)

    def test_spacing_and_case_do_not_create_new_identities(self):
        keys = {primary_identifier(t).key for t in ("DoDI1308.03", "dodi 1308.03", "DoDI  1308.03")}
        assert keys == {"dodi:1308.03"}

    def test_directive_and_instruction_are_distinct(self):
        assert primary_identifier("DoDD 1308.03").key != primary_identifier("DoDI 1308.03").key


class TestServiceMessages:
    def test_maradmin(self):
        ident = primary_identifier("MARADMIN 613/25 announces the change")
        assert ident.key == "maradmin:613/25"
        assert is_fetchable(ident.url)

    def test_navadmin(self):
        assert primary_identifier("NAVADMIN 264/25").key == "navadmin:264/25"

    def test_army_directive(self):
        ident = primary_identifier("Army Directive 2026-07, Army Physical Fitness Standards")
        assert ident.key == "army-directive:2026-07"
        assert "armypubs.army.mil" in ident.url


class TestLiterature:
    def test_pmid(self):
        assert primary_identifier("PMID: 41833285").key == "pmid:41833285"

    def test_doi_with_trailing_prose(self):
        ident = primary_identifier("see doi:10.1093/milmed/usaa123 for detail")
        assert ident.kind == "doi"
        assert ident.value.startswith("10.1093/milmed/usaa123")

    def test_pmcid(self):
        ident = primary_identifier("PMC12530864")
        assert ident.key == "pmcid:PMC12530864"
        assert "pmc.ncbi.nlm.nih.gov" in ident.url


class TestCrossSector:
    def test_nfpa(self):
        assert primary_identifier("NFPA 1580 was revised").key == "nfpa:1580"

    def test_osha_docket(self):
        assert primary_identifier("docket OSHA-2024-0002").key == "docket:OSHA-2024-0002"

    def test_gao(self):
        ident = primary_identifier("GAO-26-107979")
        assert ident.key == "gao:26-107979"
        assert "gao.gov" in ident.url


class TestPrecedence:
    def test_issuance_beats_a_doi_it_cites(self):
        """An item citing both is the issuance; the DOI is something it references."""
        text = "DoWI 1308.03 cites the trial at doi:10.1093/milmed/usaa123"
        assert primary_identifier(text).kind == "dodi"

    def test_no_identifier_returns_none(self):
        assert primary_identifier("Army opens a new performance facility") is None

    def test_empty_text_is_safe(self):
        assert primary_identifier("") is None
        assert find_identifiers("") == []

    def test_repeated_mention_yields_one_identifier(self):
        text = "DoWI 1308.03 ... as DoDI 1308.03 states ... per DoWI 1308.03"
        assert len(find_identifiers(text)) == 1


class TestAllowlist:
    def test_allowlisted_host(self):
        assert is_fetchable("https://www.esd.whs.mil/Portals/54/x.pdf")

    def test_subdomain_of_allowlisted_host(self):
        assert is_fetchable("https://static.af.mil/x")

    def test_lookalike_suffix_is_rejected(self):
        """af.mil.example.com must not pass for af.mil."""
        assert not is_fetchable("https://af.mil.example.com/x")

    def test_trade_press_is_not_fetchable(self):
        assert not is_fetchable("https://www.firerescue1.com/story")
        assert not is_fetchable("https://taskandpurpose.com/news/x")

    def test_garbage_url_is_safe(self):
        assert not is_fetchable("")
        assert not is_fetchable("not a url")

    def test_host_of_strips_www(self):
        assert host_of("https://www.gao.gov/products/x") == "gao.gov"
