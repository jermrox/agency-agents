"""Discovery tests.

The employer watchlist is only useful if a human will actually read it, so
these lean hard on precision: an off-topic document must contribute nothing,
and instruments/tests must never be mistaken for employers.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.discover import (  # noqa: E402
    discover,
    extract_employers,
    extract_vocabulary,
    is_relevant,
    render_watchlist,
)

TACTICAL_DOC = """
Navy Human Performance is Coming. Leaders from Naval Special Warfare Command and the
Naval Health Research Center. Comparisons to Army H2F and USASOC THOR3. Coaches who
worked with MARSOC. We discuss ACFT preparation, the OPAT, and DEXA scanning.
Mentioned: o2x.com and teamexos.com careers pages.
"""

OFF_TOPIC_DOC = """
We review the best espresso machines of 2026. The Breville Barista Express remains our
top pick. La Marzocco Systems makes a premium option. Visit coffeegear.com for pricing
and check the Coffee Research Institute for tasting notes.
"""


# --------------------------------------------------------------------------
# Relevance gate
# --------------------------------------------------------------------------

def test_is_relevant_accepts_tactical_text():
    assert is_relevant(TACTICAL_DOC)


def test_is_relevant_rejects_off_topic_text():
    assert not is_relevant(OFF_TOPIC_DOC)


def test_off_topic_document_yields_no_employers():
    assert extract_employers(OFF_TOPIC_DOC) == []


def test_off_topic_document_yields_no_vocabulary():
    assert extract_vocabulary(OFF_TOPIC_DOC, min_mentions=1) == []


def test_off_topic_domain_never_reaches_the_watchlist():
    """Regression: a sponsor domain in an unrelated ad read must not leak."""
    result = discover([TACTICAL_DOC, OFF_TOPIC_DOC], min_mentions=1)
    domains = {entry["value"] for entry in result["domains"]}
    assert "coffeegear.com" not in domains
    assert "o2x.com" in domains


def test_off_topic_organization_never_reaches_the_watchlist():
    result = discover([TACTICAL_DOC, OFF_TOPIC_DOC], min_mentions=1)
    names = " ".join(entry["value"] for entry in result["employers"])
    assert "Marzocco" not in names
    assert "Coffee Research Institute" not in names


# --------------------------------------------------------------------------
# Employer extraction
# --------------------------------------------------------------------------

def test_finds_multiword_organizations():
    names = {c.value for c in extract_employers(TACTICAL_DOC)}
    assert "Naval Special Warfare Command" in names
    assert "Naval Health Research Center" in names


def test_recognizes_known_org_acronyms():
    assert any(c.value == "MARSOC" for c in extract_employers(TACTICAL_DOC))


def test_instruments_are_not_employers():
    """ACFT, OPAT, and DEXA are tests, not organizations to scrape."""
    names = {c.value.upper() for c in extract_employers(TACTICAL_DOC)}
    for instrument in ("ACFT", "OPAT", "DEXA"):
        assert instrument not in names


def test_capitalized_run_stops_at_sentence_boundary():
    """Regression: '.' inside the token class swallowed the next sentence."""
    text = (
        "Coaches worked with the Institute for Human and Machine Cognition. "
        "We discuss military readiness and strength and conditioning."
    )
    for candidate in extract_employers(text):
        assert "." not in candidate.value
        assert not candidate.value.endswith("We")


def test_domains_are_captured_with_ats_hints():
    text = (
        "Military human performance roles are posted at "
        "boards.greenhouse.io and jobs.lever.co for these units."
    )
    hints = {c.value: c.ats_hint for c in extract_employers(text)}
    assert hints.get("boards.greenhouse.io") == "greenhouse"
    assert hints.get("jobs.lever.co") == "lever"


def test_mil_and_edu_domains_are_skipped():
    """Reference links, not employers with a scrapable board."""
    text = "See army.mil and usuhs.edu for military human performance policy."
    values = {c.value for c in extract_employers(text)}
    assert "army.mil" not in values and "usuhs.edu" not in values


def test_mentions_accumulate_across_documents():
    doc = "Naval Special Warfare Command runs military human performance programs."
    result = discover([doc, doc, doc], min_mentions=2)
    entry = next(
        e for e in result["employers"] if e["value"] == "Naval Special Warfare Command"
    )
    assert entry["mentions"] == 3


def test_min_mentions_filters_one_off_noise():
    doc = "Naval Special Warfare Command supports military human performance."
    assert discover([doc], min_mentions=2)["employers"] == []
    assert discover([doc], min_mentions=1)["employers"]


# --------------------------------------------------------------------------
# Vocabulary extraction
# --------------------------------------------------------------------------

def test_finds_unknown_acronyms():
    values = {c.value for c in extract_vocabulary(TACTICAL_DOC, min_mentions=1)}
    assert "DEXA" in values


def test_skips_acronyms_the_classifier_already_knows():
    """ACFT and OPAT are already scored terms; re-suggesting them is noise."""
    values = {c.value.upper() for c in extract_vocabulary(TACTICAL_DOC, min_mentions=1)}
    assert "ACFT" not in values
    assert "OPAT" not in values


def test_rejects_sentence_fragments_as_vocabulary():
    """Regression: 'the only authorized standard' is grammar, not a term."""
    text = (
        "Waist-to-height ratio is now the only authorized standard for soldiers "
        "and the same authorized standard applies to military readiness."
    )
    values = {c.value for c in extract_vocabulary(text, min_mentions=1)}
    assert not any(v.split()[0] in {"the", "and", "same"} for v in values)


def test_finds_multiword_terms_of_art():
    text = (
        "Soldiers complete the occupational physical assessment test and a new "
        "combat readiness assessment. The combat readiness assessment is scored."
    )
    values = {c.value for c in extract_vocabulary(text, min_mentions=2)}
    assert any("combat readiness assessment" in v for v in values)


# --------------------------------------------------------------------------
# Rendering
# --------------------------------------------------------------------------

def test_watchlist_renders_sections():
    output = render_watchlist(discover([TACTICAL_DOC], min_mentions=1))
    assert "Candidate employers" in output
    assert "Referenced domains" in output
    assert "o2x.com" in output


def test_watchlist_handles_empty_discovery():
    output = render_watchlist(discover([], min_mentions=1))
    assert "Nothing discovered" in output


def test_watchlist_escapes_pipes_so_tables_do_not_break():
    text = "Military | Performance | Group runs strength and conditioning for soldiers."
    output = render_watchlist(discover([text, text], min_mentions=1))
    for line in output.splitlines():
        if line.startswith("|") and "---" not in line:
            # A row must not gain extra columns from unescaped content.
            assert line.count("|") - line.count("\\|") <= 4


def test_discover_counts_documents_and_skips_blanks():
    result = discover([TACTICAL_DOC, "", "   ", None or ""], min_mentions=1)
    assert result["documents"] == 1


def test_discover_returns_wellformed_empty_structure():
    result = discover([], min_mentions=1)
    for key in ("documents", "employers", "domains", "ats_boards", "vocabulary"):
        assert key in result
    assert result["documents"] == 0
