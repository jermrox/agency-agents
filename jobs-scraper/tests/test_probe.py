"""Probe-plan module tests.

``tactical_jobs.probe`` performs no network IO by design, so nothing here
needs monkeypatching -- the assertions are about slug derivation parity with
santifer/career-ops discover-ats.mjs, SLUG_RE enforcement, probe-URL exactness
against the career-ops provider recipes, the Workday blind-probe exclusion,
and TOML snippet validity.
"""

from __future__ import annotations

import dataclasses
import sys
import tomllib
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.probe import (  # noqa: E402
    SLUG_RE,
    WORKDAY_INSTANCES,
    WORKDAY_SEGMENT_RE,
    ProbeCandidate,
    derive_slugs,
    probe_urls,
    render_probe_plan,
    workday_probe,
)


# --- derive_slugs: parity with career-ops deriveSlug() -----------------------
# The first candidate must be exactly what discover-ats.mjs deriveSlug()
# produces (its self-test cases are reused verbatim).


def test_derive_slugs_multiword_matches_career_ops():
    assert derive_slugs("Trade Republic")[0] == "trade-republic"


def test_derive_slugs_trims_and_strips_punctuation():
    # discover-ats self-test: deriveSlug('  N8N!  ') === 'n8n'
    assert derive_slugs("  N8N!  ")[0] == "n8n"


def test_derive_slugs_simple_name_lowercases_and_dedupes():
    # "Adyen": hyphenated == joined == first token, and the case-preserved
    # variant is suppressed (no uppercase past position 0), so exactly one
    # candidate survives dedupe.
    assert derive_slugs("Adyen") == ["adyen"]


def test_derive_slugs_alphanumeric_company_emits_documented_extras():
    assert derive_slugs("O2X Human Performance") == [
        "o2x-human-performance",   # career-ops deriveSlug rule
        "o2xhumanperformance",     # documented extra: joined
        "O2XHumanPerformance",     # documented extra: case-preserved (Ashby)
        "o2x",                     # documented extra: first token
    ]


def test_derive_slugs_camelcase_variant_preserved_for_ashby():
    # career-ops notes camelCase Ashby boards (AlephAlpha) are missed by its
    # lowercasing deriveSlug; the case-preserved extra recovers them.
    assert "AlephAlpha" in derive_slugs("Aleph Alpha")


def test_derive_slugs_unicode_ports_the_js_replacement_rule():
    # JS: 'café zürich'.replace(/[^a-z0-9]+/g, '-') -> 'caf-z-rich'; the
    # accented characters are outside [a-z0-9] and become separators.
    slugs = derive_slugs("Café Zürich")
    assert slugs[0] == "caf-z-rich"
    assert all(SLUG_RE.fullmatch(s) for s in slugs)


def test_derive_slugs_hostile_name_yields_only_safe_slugs():
    slugs = derive_slugs("../../etc/passwd?x=1&y=2#frag")
    assert slugs  # the letter/digit runs survive as hyphenated tokens
    assert all(SLUG_RE.fullmatch(s) for s in slugs)
    for slug in slugs:
        assert "/" not in slug and "?" not in slug and "#" not in slug


def test_derive_slugs_empty_and_garbage_names():
    assert derive_slugs("") == []
    assert derive_slugs("   ") == []
    assert derive_slugs("!!! ???") == []
    assert derive_slugs(None) == []  # type: ignore[arg-type]


# --- SLUG_RE enforcement -----------------------------------------------------


def test_slug_re_accepts_the_career_ops_charset():
    for slug in ("AlephAlpha", "monzo-bank", "o2x", "a.b_c-d", "DeepL"):
        assert SLUG_RE.fullmatch(slug), slug


@pytest.mark.parametrize(
    "bad",
    ["bad/slug", "a b", "a?b", "a#b", "a@b", "", "a/../b", "café", "a&b", "a\nb"],
)
def test_slug_re_rejects_injection_attempts(bad):
    assert SLUG_RE.fullmatch(bad) is None


def test_slug_re_is_anchored_like_the_js_original():
    # discover-ats.mjs SLUG_RE is /^[A-Za-z0-9._-]+$/ (anchored). The port must
    # stay fail-safe even for a consumer that reaches for .match()/.search()
    # instead of .fullmatch() -- a partial hit on "bad/slug" would let the
    # unsafe remainder ride along into a URL.
    assert SLUG_RE.match("bad/slug") is None
    assert SLUG_RE.search("x?y") is None
    assert WORKDAY_SEGMENT_RE.match("wd5/../evil") is None
    assert WORKDAY_SEGMENT_RE.search("Ext ernal") is None
    # \Z (not $) so a trailing newline cannot sneak past the anchor.
    assert SLUG_RE.match("ok-slug\n") is None
    assert WORKDAY_SEGMENT_RE.match("wd5\n") is None


def test_probe_urls_drops_unsafe_extra_slugs():
    candidates = probe_urls("Acme", extra_slugs=("evil/../path", "ok-slug", 7))
    slugs = {c.slug for c in candidates}
    assert "ok-slug" in slugs
    assert not any("/" in c.slug for c in candidates)
    # Nothing outside the safe charset ever reaches a URL path.
    assert not any("evil" in c.probe_url for c in candidates)


# --- probe_urls: URL exactness against the .mjs recipes ----------------------


def _by_vendor(candidates, vendor, slug):
    return next(c for c in candidates if c.vendor == vendor and c.slug == slug)


def test_greenhouse_probe_url_matches_provider_recipe():
    # providers/greenhouse.mjs resolveApiUrl / discover-ats VENDORS.gh.api
    cand = _by_vendor(probe_urls("Adyen"), "greenhouse", "adyen")
    assert cand.probe_url == "https://boards-api.greenhouse.io/v1/boards/adyen/jobs"


def test_lever_probe_url_matches_provider_recipe():
    # providers/lever.mjs resolveApiUrl
    cand = _by_vendor(probe_urls("Adyen"), "lever", "adyen")
    assert cand.probe_url == "https://api.lever.co/v0/postings/adyen"


def test_ashby_probe_url_matches_provider_recipe():
    # providers/ashby.mjs resolveApiUrl (includeCompensation query included)
    cand = _by_vendor(probe_urls("Adyen"), "ashby", "adyen")
    assert cand.probe_url == (
        "https://api.ashbyhq.com/posting-api/job-board/adyen?includeCompensation=true"
    )


def test_probe_urls_vendor_order_matches_discover_ats():
    # discover-ats VENDOR_ORDER = gh, ashby, lever -- per slug, first match wins.
    vendors = [c.vendor for c in probe_urls("Adyen")]
    assert vendors == ["greenhouse", "ashby", "lever"]


def test_ashby_slug_case_is_preserved_end_to_end():
    candidates = probe_urls("DeepL Translate", extra_slugs=("DeepL",))
    cand = _by_vendor(candidates, "ashby", "DeepL")
    assert cand.probe_url == (
        "https://api.ashbyhq.com/posting-api/job-board/DeepL?includeCompensation=true"
    )


def test_probe_candidate_is_frozen():
    cand = probe_urls("Adyen")[0]
    assert isinstance(cand, ProbeCandidate)
    with pytest.raises(dataclasses.FrozenInstanceError):
        cand.slug = "other"  # type: ignore[misc]


def test_probe_urls_empty_name_yields_nothing():
    assert probe_urls("") == []
    assert probe_urls("!!!") == []


# --- Workday: excluded from blind probing, explicit helper works -------------


def test_workday_never_appears_in_blind_probes():
    for name in ("Adyen", "Leidos", "O2X Human Performance", "Nvidia"):
        assert all(c.vendor != "workday" for c in probe_urls(name))


def test_workday_probe_builds_the_cxs_endpoint():
    # providers/workday.mjs resolveEndpoint:
    # https://<tenant>.<instance>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs
    cand = workday_probe("leidos", "wd5", "External")
    assert cand.vendor == "workday"
    assert cand.slug == "leidos"
    assert cand.probe_url == (
        "https://leidos.wd5.myworkdayjobs.com/wday/cxs/leidos/External/jobs"
    )


@pytest.mark.parametrize(
    "tenant,data_center,site",
    [
        ("bad/tenant", "wd5", "External"),
        ("leidos", "wd5?", "External"),
        ("leidos", "wd5", "Ext ernal"),
        ("", "wd5", "External"),
        ("leidos", "wd5", "site#frag"),
    ],
)
def test_workday_probe_rejects_unsafe_segments(tenant, data_center, site):
    with pytest.raises(ValueError):
        workday_probe(tenant, data_center, site)


def test_workday_segment_re_allows_underscore_site_names():
    # Real-world shapes from discover-ats: NVIDIAExternalCareerSite,
    # External_Career_Site; instances are wdNN.
    for segment in ("NVIDIAExternalCareerSite", "External_Career_Site", "wd12"):
        assert WORKDAY_SEGMENT_RE.fullmatch(segment)


def test_workday_instances_list_ported_in_order():
    assert WORKDAY_INSTANCES[0] == "wd1"
    assert "wd5" in WORKDAY_INSTANCES


# --- config snippets ---------------------------------------------------------


def test_snippets_round_trip_through_tomllib():
    for cand in probe_urls("O2X Human Performance"):
        parsed = tomllib.loads(cand.config_snippet)
        (entry,) = parsed["source"]
        assert entry["kind"] == cand.vendor
        assert entry["board_token"] == cand.slug
        assert entry["name"] == cand.slug
        assert entry["employer"] == "O2X Human Performance"


def test_workday_snippet_round_trips_with_coordinates():
    cand = workday_probe("leidos", "wd5", "External")
    parsed = tomllib.loads(cand.config_snippet)
    (entry,) = parsed["source"]
    assert entry["kind"] == "workday"
    assert entry["tenant"] == "leidos"
    assert entry["site"] == "External"
    assert entry["data_center"] == "wd5"
    # No employer invented from the tenant string.
    assert "employer" not in entry


def test_snippets_never_claim_verification():
    for cand in (*probe_urls("Adyen"), workday_probe("leidos", "wd5", "External")):
        assert "# VERIFIED LIVE: <fill" in cand.config_snippet
        assert "2026-07-31" not in cand.config_snippet  # no auto-filled "today"


def test_snippet_escapes_awkward_employer_names():
    cand = probe_urls('Say "Go" Fitness \\ Co')[0]
    parsed = tomllib.loads(cand.config_snippet)
    assert parsed["source"][0]["employer"] == 'Say "Go" Fitness \\ Co'


def test_snippet_escapes_control_characters_in_employer():
    # A name with an interior newline/tab must still yield valid TOML -- the
    # module's contract is that every config_snippet round-trips through
    # tomllib.loads, and a raw control character inside a basic string is a
    # TOML parse error.
    for cand in probe_urls("Acme\nCorp\tIndustries"):
        parsed = tomllib.loads(cand.config_snippet)
        assert parsed["source"][0]["employer"] == "Acme\nCorp\tIndustries"


def test_snippet_carries_attribution_and_probe_url():
    cand = _by_vendor(probe_urls("Adyen"), "greenhouse", "adyen")
    assert "santifer/career-ops" in cand.config_snippet
    assert cand.probe_url in cand.config_snippet


# --- render_probe_plan -------------------------------------------------------


def test_probe_plan_lists_every_candidate_with_both_checkboxes():
    plan = render_probe_plan(["O2X Human Performance", "Adyen"])
    assert "## O2X Human Performance" in plan
    assert "## Adyen" in plan
    for cand in probe_urls("O2X Human Performance"):
        assert cand.probe_url in plan
    assert plan.count("- [ ] board exists?") == plan.count("- [ ] lists >= 1 job?")
    assert plan.count("- [ ] board exists?") > 0


def test_probe_plan_states_it_did_no_network_io():
    plan = render_probe_plan(["Adyen"])
    assert "no network IO" in plan
    assert "unverified" in plan


def test_probe_plan_states_workday_exclusion():
    plan = render_probe_plan(["Nvidia"])
    assert "Workday is excluded from blind probing" in plan
    assert "workday_probe" in plan


def test_probe_plan_flags_underivable_names_instead_of_dropping_them():
    plan = render_probe_plan(["!!!", "Adyen"])
    assert "no URL-safe slug is derivable" in plan
    assert "## Adyen" in plan


def test_probe_plan_empty_board_is_not_a_pass():
    # career-ops acceptance rule: exists AND currently lists >= 1 job.
    plan = render_probe_plan(["Adyen"])
    assert "existing-but-empty board is NOT a pass" in plan
