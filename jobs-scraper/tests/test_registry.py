"""Employer registry tests.

Most of this file is not testing code -- it is testing *claims about the world*.
The registry asserts that certain organizations hire tactical human performance
staff and that certain board tokens will reach them, and the whole value of the
module rests on those claims being labelled with the right confidence.

So the tests here are mostly integrity guards. The important one is
:func:`test_every_entry_is_unverified`: this module was written with no network
access, nothing in it has been confirmed against a live endpoint, and if someone
later flips ``verified=True`` on an entry that guard must fail loudly and force
them to say so. It is a tripwire, not a regression test, and a failure means
"prove it", not "revert it".
"""

from __future__ import annotations

import sys
import tomllib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from tactical_jobs.registry import (  # noqa: E402
    CATEGORIES,
    CREDENTIALED_KINDS,
    KEYLESS_KINDS,
    PLACEHOLDER_PREFIX,
    REGISTRY,
    SOURCE_KINDS,
    Employer,
    all_employers,
    by_category,
    by_slug,
    match_employer,
    placeholder_options,
    to_toml,
    used_kinds,
    verification_hint,
    verified_count,
)


def _uncommented(text: str) -> list[str]:
    """Lines that a TOML parser would actually act on."""
    return [line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")]


# ---------------------------------------------------------------------------
# structural integrity
# ---------------------------------------------------------------------------


def test_registry_is_not_empty():
    assert len(REGISTRY) >= 24


def test_all_employers_returns_the_registry():
    assert all_employers() == REGISTRY


def test_every_slug_is_unique():
    slugs = [employer.slug for employer in REGISTRY]
    duplicates = sorted({slug for slug in slugs if slugs.count(slug) > 1})
    assert duplicates == [], f"duplicate slugs would collide in by_slug: {duplicates}"


def test_every_slug_is_config_safe():
    """Slugs become the ``name`` of a source block and show up in run summaries."""
    for employer in REGISTRY:
        assert employer.slug == employer.slug.lower()
        assert " " not in employer.slug
        assert employer.slug.replace("-", "").isalnum(), employer.slug


def test_every_name_is_present():
    for employer in REGISTRY:
        assert employer.name.strip(), employer.slug


def test_every_category_is_known():
    for employer in REGISTRY:
        assert employer.category in CATEGORIES, f"{employer.slug}: {employer.category}"


def test_every_category_is_populated():
    """A category nobody uses is a category that should not exist."""
    for category in CATEGORIES:
        assert by_category(category), f"no employers in category {category!r}"


def test_every_ats_is_none_or_a_real_source_kind():
    for employer in REGISTRY:
        assert employer.ats is None or employer.ats in SOURCE_KINDS, (
            f"{employer.slug} points at unknown adapter kind {employer.ats!r}"
        )


def test_no_entry_requires_an_api_key():
    """The operator has no credentials, so a credentialed kind is a dead end."""
    for employer in REGISTRY:
        assert employer.ats not in CREDENTIALED_KINDS, (
            f"{employer.slug} uses {employer.ats}, which needs an API key"
        )


def test_source_kinds_matches_the_shipped_adapters():
    """Guard against SOURCE_KINDS drifting from the real adapter registry.

    The constant is duplicated on purpose (see the module docstring), so
    something has to notice when the two disagree. This asserts set *equality*,
    not containment: containment only proves the kinds already in use are real,
    and it happily tolerated this constant omitting ``agencyboard`` and
    ``sitemapjobs`` -- two shipped adapters made invisible to anyone choosing an
    ``ats`` value by reading registry.py.
    """
    from tactical_jobs.sources import available_kinds

    assert SOURCE_KINDS == set(available_kinds())


def test_credentialed_kinds_matches_the_source_package():
    """The no-API-key rule is only enforceable if this list is the real one."""
    from tactical_jobs.sources import CREDENTIALED_KINDS as shipped

    assert CREDENTIALED_KINDS == shipped


def test_keyless_kinds_excludes_every_credentialed_kind():
    assert KEYLESS_KINDS.isdisjoint(CREDENTIALED_KINDS)
    assert KEYLESS_KINDS | CREDENTIALED_KINDS == SOURCE_KINDS


def test_every_entry_has_notes():
    for employer in REGISTRY:
        assert employer.notes.strip(), f"{employer.slug} has no notes"


def test_every_entry_says_how_to_confirm_itself():
    """The honesty requirement: notes must carry the verification step."""
    for employer in REGISTRY:
        assert "confirm" in employer.notes.lower(), (
            f"{employer.slug} notes do not say how to confirm the entry"
        )


def test_aliases_are_tuples_not_strings():
    """A bare string would iterate character by character and poison the index."""
    for employer in REGISTRY:
        assert isinstance(employer.aliases, tuple), employer.slug


def test_options_are_dicts():
    for employer in REGISTRY:
        assert isinstance(employer.options, dict), employer.slug


def test_entries_without_an_ats_carry_no_options():
    """No adapter means no option shape to fill in; stray options would mislead."""
    for employer in REGISTRY:
        if employer.ats is None:
            assert employer.options == {}, employer.slug


# ---------------------------------------------------------------------------
# the honesty guard
# ---------------------------------------------------------------------------


def test_every_entry_is_unverified():
    """Tripwire. Nothing here was ever checked against a live endpoint.

    If this fails, somebody set ``verified=True``. That is allowed -- but only
    after actually running the check in that entry's notes and seeing a real
    response. Update this test deliberately, with the evidence, rather than
    loosening it.
    """
    unverified = [e.slug for e in REGISTRY if e.verified]
    assert unverified == [], (
        f"these claim to be verified: {unverified}. Nothing in this registry has "
        "been confirmed against a live endpoint."
    )


def test_verified_count_reports_zero_of_everything():
    verified, total = verified_count()
    assert total == len(REGISTRY)
    assert verified == 0


def test_verified_count_arithmetic_tracks_the_flag(monkeypatch):
    """The counter must count, not return a hardcoded pair."""
    import tactical_jobs.registry as registry_module

    faked = (
        Employer(slug="a", name="A", category="prime", ats=None, options={}, verified=True),
        Employer(slug="b", name="B", category="prime", ats=None, options={}),
        Employer(slug="c", name="C", category="prime", ats=None, options={}, verified=True),
    )
    monkeypatch.setattr(registry_module, "REGISTRY", faked)
    assert registry_module.verified_count() == (2, 3)


_HEDGES = (
    "guess",
    "assum",
    "unverif",
    "unconfirm",
    "convention",
    "not identified",
    "not known",
    "not confirmed",
    "hypothes",
    "may not",
)


def test_every_concrete_token_is_labelled_as_a_guess():
    """A real-looking value is the dangerous kind of entry.

    ``board_token = "o2x"`` and ``tenant = "leidos"`` read as knowledge in a way
    that ``PASTE_...`` never can. Nobody has run those requests, so the notes
    beside them have to say so in words -- otherwise the file quietly promotes a
    plausible guess to a fact, which is the one thing this module is for.
    """
    for employer in REGISTRY:
        concrete = [
            key
            for key, value in employer.options.items()
            if isinstance(value, str) and not value.startswith(PLACEHOLDER_PREFIX)
        ]
        if employer.ats is None or not concrete:
            continue
        assert any(hedge in employer.notes.lower() for hedge in _HEDGES), (
            f"{employer.slug} ships concrete values {concrete} with no hedge in "
            "its notes -- it reads as confirmed"
        )


def test_usajobs_backed_entries_flag_that_the_feed_is_an_assumption():
    """Eleven entries rest on USAJOBS publishing a keyless feed. Nobody checked.

    The route was originally written as settled fact. It is the first thing to
    verify, not the given, and the notes must say which.
    """
    federal_feeds = [
        e for e in REGISTRY
        if e.ats == "rss" and str(e.options.get("url", "")).startswith(PLACEHOLDER_PREFIX)
    ]
    assert federal_feeds
    for employer in federal_feeds:
        lowered = employer.notes.lower()
        assert "assume" in lowered or "assumed" in lowered, employer.slug
        assert "keyless feed" in lowered, employer.slug


def test_no_entry_points_at_the_credentialed_usajobs_adapter_as_a_fallback():
    """Suggesting the keyed adapter as plan B would be a dead end, not a lead."""
    for employer in REGISTRY:
        lowered = employer.notes.lower()
        if "usajobs adapter" in lowered:
            assert "api key" in lowered and "out of scope" in lowered, employer.slug


def test_placeholder_options_flags_unfilled_values():
    employer = Employer(
        slug="x",
        name="X",
        category="prime",
        ats="greenhouse",
        options={"board_token": f"{PLACEHOLDER_PREFIX}TOKEN_HERE", "employer": "X"},
    )
    assert placeholder_options(employer) == ("board_token",)


def test_placeholder_options_is_empty_when_everything_is_filled():
    employer = Employer(
        slug="x", name="X", category="prime", ats="greenhouse", options={"board_token": "x"}
    )
    assert placeholder_options(employer) == ()


def test_placeholders_only_appear_where_an_adapter_is_named():
    """A placeholder is a fill-in-the-blank for a known option, not a shrug."""
    for employer in REGISTRY:
        if placeholder_options(employer):
            assert employer.ats is not None, employer.slug


# ---------------------------------------------------------------------------
# to_source_config
# ---------------------------------------------------------------------------


def test_to_source_config_round_trip():
    employer = Employer(
        slug="acme",
        name="Acme Performance",
        category="specialist",
        ats="greenhouse",
        options={"board_token": "acme"},
    )
    config = employer.to_source_config()
    assert config["kind"] == "greenhouse"
    assert config["name"] == "acme"
    assert config["board_token"] == "acme"


def test_to_source_config_fills_employer_from_the_display_name():
    employer = Employer(
        slug="acme", name="Acme Performance", category="specialist",
        ats="lever", options={"board_token": "acme"},
    )
    assert employer.to_source_config()["employer"] == "Acme Performance"


def test_to_source_config_keeps_an_explicit_employer_option():
    employer = Employer(
        slug="acme", name="Acme Performance", category="specialist",
        ats="lever", options={"board_token": "acme", "employer": "Acme Corp"},
    )
    assert employer.to_source_config()["employer"] == "Acme Corp"


def test_to_source_config_does_not_alias_the_options_dict():
    """A caller mutating the returned table must not edit the registry."""
    employer = Employer(
        slug="acme", name="Acme", category="specialist",
        ats="lever", options={"board_token": "acme"},
    )
    config = employer.to_source_config()
    config["board_token"] = "tampered"
    assert employer.options["board_token"] == "acme"


def test_to_source_config_does_not_alias_nested_option_values():
    """A shallow copy looks safe and is not.

    Several entries carry list options, and with a shallow copy a caller
    appending to the returned ``search_terms`` edits the module-level REGISTRY
    for the rest of the process -- one caller's tweak leaking into every later
    lookup, with nothing in the traceback pointing back here.
    """
    employer = Employer(
        slug="acme", name="Acme", category="prime", ats="workday",
        options={"tenant": "acme", "site": "External", "search_terms": ["a"],
                 "field_map": {"title": "name"}},
    )
    config = employer.to_source_config()
    config["search_terms"].append("tampered")
    config["field_map"]["title"] = "tampered"
    assert employer.options["search_terms"] == ["a"]
    assert employer.options["field_map"] == {"title": "name"}


def test_registry_entries_survive_a_config_round_trip_unmutated():
    """The same guard, against the real table rather than a fixture."""
    before = {e.slug: repr(e.options) for e in REGISTRY}
    for employer in REGISTRY:
        if employer.ats is None:
            continue
        config = employer.to_source_config()
        for value in config.values():
            if isinstance(value, list):
                value.append("tampered")
            elif isinstance(value, dict):
                value["tampered"] = True
    assert {e.slug: repr(e.options) for e in REGISTRY} == before


def test_to_source_config_refuses_when_the_ats_is_unknown():
    employer = Employer(slug="mystery", name="Mystery", category="prime", ats=None, options={})
    with pytest.raises(ValueError, match="no known ATS"):
        employer.to_source_config()


def test_every_configurable_entry_builds_a_source_config():
    for employer in REGISTRY:
        if employer.ats is None:
            continue
        config = employer.to_source_config()
        assert config["kind"] == employer.ats
        assert config["name"] == employer.slug
        assert set(employer.options).issubset(config)


def test_workday_entries_carry_the_options_the_adapter_requires():
    """WorkdaySource calls require('tenant') and require('site')."""
    for employer in REGISTRY:
        if employer.ats == "workday":
            config = employer.to_source_config()
            assert "tenant" in config and "site" in config, employer.slug


def test_feed_entries_carry_a_url():
    """The rss and jobsrss adapters both call require('url')."""
    for employer in REGISTRY:
        if employer.ats in ("rss", "jobsrss"):
            assert employer.to_source_config().get("url"), employer.slug


def test_greenhouse_and_lever_entries_carry_a_board_token():
    for employer in REGISTRY:
        if employer.ats in ("greenhouse", "lever"):
            assert employer.to_source_config().get("board_token"), employer.slug


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------


def test_by_slug_finds_a_known_entry():
    found = by_slug("o2x")
    assert found is not None
    assert found.name == "O2X Human Performance"


def test_by_slug_misses_cleanly():
    assert by_slug("not-a-real-employer") is None


def test_by_category_filters():
    associations = by_category("association")
    assert associations
    assert all(e.category == "association" for e in associations)
    assert {e.slug for e in associations} >= {"nsca", "nata", "acsm", "cscca", "aasp"}


def test_by_category_partitions_the_registry():
    total = sum(len(by_category(category)) for category in CATEGORIES)
    assert total == len(REGISTRY)


def test_by_category_returns_empty_for_an_unknown_category():
    assert by_category("aerospace") == ()


def test_match_employer_exact_name():
    found = match_employer("Booz Allen Hamilton")
    assert found is not None and found.slug == "booz-allen-hamilton"


def test_match_employer_is_case_insensitive():
    assert match_employer("bOoZ aLlEn HaMiLtOn").slug == "booz-allen-hamilton"


def test_match_employer_ignores_punctuation_and_legal_suffixes():
    assert match_employer("Booz Allen Hamilton, Inc.").slug == "booz-allen-hamilton"


def test_match_employer_ignores_a_leading_article():
    assert match_employer("Geneva Foundation").slug == "geneva-foundation"


def test_match_employer_finds_an_alias():
    assert match_employer("BAH").slug == "booz-allen-hamilton"


def test_match_employer_finds_a_program_alias():
    """People say the program name, not the command name."""
    assert match_employer("THOR3").slug == "usasoc"
    assert match_employer("POTFF").slug == "socom-potff"


def test_match_employer_accepts_a_slug():
    assert match_employer("naval-special-warfare").slug == "naval-special-warfare"


def test_match_employer_handles_a_long_official_name():
    found = match_employer("Fire Department of the City of New York")
    assert found is not None and found.slug == "fdny"


def test_normalization_folds_ampersands_to_and():
    """'Marsh & McLennan' and 'Marsh and McLennan' must land on one key."""
    from tactical_jobs.registry import _normalize

    assert _normalize("Health & Fitness, Inc.") == _normalize("health and fitness inc")


def test_normalization_strips_legal_suffixes_and_leading_article():
    from tactical_jobs.registry import _loose

    assert _loose("The Example Group, LLC") == "example group"
    assert _loose("Example Corp.") == "example"


def test_match_employer_misses_cleanly():
    assert match_employer("Northwind Logistics") is None


def test_match_employer_handles_empty_input():
    assert match_employer("") is None
    assert match_employer("   ") is None


def test_match_employer_does_not_substring_match():
    """A wrong attribution is worse than no attribution."""
    assert match_employer("Army") is None


def test_every_registry_entry_resolves_to_itself():
    """Not merely *a* hit -- the right one.

    The original assertion was ``is not None``, which passes even when two
    entries collide on a normalized key and one of them permanently shadows the
    other. "Found something" is not the property that matters here; "found the
    organization whose posting this is" is.
    """
    for employer in REGISTRY:
        by_name = match_employer(employer.name)
        assert by_name is not None and by_name.slug == employer.slug, employer.slug
        assert match_employer(employer.slug).slug == employer.slug, employer.slug


def test_every_alias_resolves_to_its_own_entry():
    for employer in REGISTRY:
        for alias in employer.aliases:
            found = match_employer(alias)
            assert found is not None and found.slug == employer.slug, (
                f"{employer.slug} alias {alias!r} resolved to "
                f"{found.slug if found else None}"
            )


def test_no_two_entries_claim_the_same_lookup_key():
    """A shadowed name is a silent, permanent mis-attribution."""
    from tactical_jobs.registry import _loose, _normalize

    for keyfn in (_normalize, _loose):
        seen: dict[str, str] = {}
        for employer in REGISTRY:
            for raw in employer.search_keys():
                key = keyfn(raw)
                if not key:
                    continue
                owner = seen.setdefault(key, employer.slug)
                assert owner == employer.slug, (
                    f"{keyfn.__name__} key {key!r} is claimed by both {owner} "
                    f"and {employer.slug}"
                )


def test_parent_companies_are_not_aliases():
    """A parent owns unrelated subsidiaries; folding its name in mis-attributes them.

    NANA owns far more than Akima and Afognak far more than Alutiiq, so a
    posting from a sibling subsidiary must not resolve here. Acuity is the same
    shape of relationship for Magellan Federal. These belong in ``notes``, which
    a human reads, not in ``aliases``, which a lookup acts on.
    """
    for parent in (
        "NANA Regional Corporation",
        "Afognak Native Corporation",
        "Acuity International",
    ):
        assert match_employer(parent) is None, parent


def test_unsourced_acronym_expansions_are_not_aliases():
    """EMPLOYERS.md records 'PSI' and no expansion of it.

    Inventing one and shipping it as an alias would resolve real postings to an
    organization nobody has evidence exists under that name -- the exact failure
    this module is built to refuse.
    """
    assert match_employer("Professional Sports Institute") is None


def test_lookup_helpers_treat_a_non_string_as_a_miss():
    """These are fed scraped employer strings; a None must not raise."""
    for bad in (None, 123, object(), b"o2x"):
        assert by_slug(bad) is None
        assert by_category(bad) == ()
        assert match_employer(bad) is None


def test_match_employer_reflects_the_current_registry(monkeypatch):
    """The name index must not be frozen at import while by_slug reads live.

    Two lookups answering from two different tables is the sort of split brain
    that costs an afternoon, so the index is keyed on the registry it was built
    from.
    """
    import tactical_jobs.registry as registry_module

    faked = (
        Employer(
            slug="northwind",
            name="Northwind Logistics",
            category="prime",
            ats=None,
            options={},
            aliases=("Northwind",),
        ),
    )
    monkeypatch.setattr(registry_module, "REGISTRY", faked)
    assert registry_module.match_employer("Northwind Logistics").slug == "northwind"
    assert registry_module.match_employer("Northwind").slug == "northwind"
    assert registry_module.by_slug("northwind") is not None
    assert registry_module.match_employer("O2X") is None


# ---------------------------------------------------------------------------
# to_toml
# ---------------------------------------------------------------------------


def test_to_toml_emits_a_header():
    text = to_toml(REGISTRY)
    assert "EMPLOYER REGISTRY" in text
    assert "COMMENTED OUT ON PURPOSE" in text


def test_to_toml_header_explains_the_verification_step():
    text = to_toml(REGISTRY)
    lowered = text.lower()
    assert "--dry-run" in lowered
    assert "boards-api.greenhouse.io" in lowered
    assert "myworkdayjobs.com" in lowered


def test_to_toml_comments_out_every_unverified_entry():
    text = to_toml(REGISTRY)
    for line in text.splitlines():
        if "[[source]]" in line:
            assert line.lstrip().startswith("#"), f"live source block leaked: {line!r}"


def test_to_toml_of_unverified_entries_parses_as_empty_toml():
    """The strongest form of the guard: a paste of this file configures nothing."""
    parsed = tomllib.loads(to_toml(REGISTRY))
    assert parsed == {}


def test_to_toml_emits_no_uncommented_lines_while_nothing_is_verified():
    assert _uncommented(to_toml(REGISTRY)) == []


def test_to_toml_excluding_unverified_yields_no_source_blocks():
    text = to_toml(REGISTRY, include_unverified=False)
    assert "[[source]]" not in text
    assert "EMPLOYER REGISTRY" in text


def test_to_toml_excluding_unverified_explains_the_emptiness():
    text = to_toml(REGISTRY, include_unverified=False)
    assert "no employer in this selection has been verified" in text.lower()


def test_to_toml_emits_a_live_block_for_a_verified_entry():
    employer = Employer(
        slug="acme",
        name="Acme Performance",
        category="specialist",
        ats="greenhouse",
        options={"board_token": "acme"},
        verified=True,
        notes="Confirmed against the live board.",
    )
    text = to_toml([employer])
    parsed = tomllib.loads(text)
    assert parsed["source"][0]["kind"] == "greenhouse"
    assert parsed["source"][0]["name"] == "acme"
    assert parsed["source"][0]["board_token"] == "acme"
    assert parsed["source"][0]["employer"] == "Acme Performance"


def test_to_toml_keeps_verified_entries_when_unverified_are_excluded():
    verified = Employer(
        slug="acme", name="Acme", category="specialist", ats="lever",
        options={"board_token": "acme"}, verified=True, notes="Confirm: done.",
    )
    unverified = Employer(
        slug="beta", name="Beta", category="specialist", ats="lever",
        options={"board_token": "beta"}, notes="Confirm before enabling.",
    )
    text = to_toml([verified, unverified], include_unverified=False)
    parsed = tomllib.loads(text)
    assert [block["name"] for block in parsed["source"]] == ["acme"]


def test_to_toml_renders_list_options_as_toml_arrays():
    employer = Employer(
        slug="acme", name="Acme", category="prime", ats="workday",
        options={"tenant": "acme", "site": "External", "search_terms": ["a", "b"]},
        verified=True, notes="Confirmed.",
    )
    parsed = tomllib.loads(to_toml([employer]))
    assert parsed["source"][0]["search_terms"] == ["a", "b"]


def test_to_toml_renders_numbers_and_booleans_correctly():
    employer = Employer(
        slug="acme", name="Acme", category="prime", ats="jsonld",
        options={"urls": ["https://example.com/job/1"], "max_urls": 300, "flag": False},
        verified=True, notes="Confirmed.",
    )
    parsed = tomllib.loads(to_toml([employer]))
    block = parsed["source"][0]
    assert block["max_urls"] == 300
    assert block["flag"] is False


def test_to_toml_escapes_quotes_in_values():
    employer = Employer(
        slug="acme", name='Acme "Tactical" Inc', category="prime", ats="lever",
        options={"board_token": "acme"}, verified=True, notes="Confirmed.",
    )
    parsed = tomllib.loads(to_toml([employer]))
    assert parsed["source"][0]["employer"] == 'Acme "Tactical" Inc'


def test_to_toml_notes_entries_with_no_known_ats():
    text = to_toml([e for e in REGISTRY if e.ats is None])
    assert "NO SOURCE BLOCK" in text
    assert "[[source]]" not in text


def test_to_toml_flags_placeholder_options():
    text = to_toml(REGISTRY)
    assert "FILL IN before enabling" in text
    assert PLACEHOLDER_PREFIX in text


def test_to_toml_includes_every_selected_employer_name():
    subset = by_category("association")
    text = to_toml(subset)
    for employer in subset:
        assert employer.name in text


def test_to_toml_groups_by_category():
    text = to_toml(REGISTRY)
    for category in CATEGORIES:
        assert f"# {category.upper()}" in text


def test_to_toml_reports_the_verified_ratio():
    verified, total = verified_count()
    assert f"{verified} of {total} verified" in to_toml(REGISTRY)


def test_to_toml_of_an_empty_selection_still_returns_the_header():
    text = to_toml([])
    assert "EMPLOYER REGISTRY" in text
    assert "[[source]]" not in text


def test_to_toml_output_ends_with_a_newline():
    assert to_toml(REGISTRY).endswith("\n")


# ---------------------------------------------------------------------------
# the comment-out guard, adversarially
#
# to_toml()'s one hard promise is that an unverified entry cannot become live
# configuration. Everything below tries to break that promise with hostile field
# content rather than trusting the happy path.
# ---------------------------------------------------------------------------

_BREAKOUT_CHARS = ["\r", "\n", "\r\n", "\x0b", "\x0c", "\x85", " ", " "]


@pytest.mark.parametrize("char", _BREAKOUT_CHARS)
def test_a_line_break_in_any_field_cannot_escape_the_comment(char):
    """``\\r`` was the hole: splitlines treats it as a line boundary.

    A value containing one used to render a second physical line with no ``#``
    prefix -- live TOML inside a block that was supposed to be inert, which is
    the single failure this module exists to make impossible.
    """
    payload = f"X{char}live = 1"
    employer = Employer(
        slug="x",
        name=payload,
        category="prime",
        ats="lever",
        options={"board_token": payload},
        notes=f"Confirm.{char}also_live = 2",
        aliases=(payload,),
    )
    text = to_toml([employer])
    assert _uncommented(text) == []
    assert tomllib.loads(text) == {}


@pytest.mark.parametrize("char", _BREAKOUT_CHARS)
def test_a_line_break_in_a_verified_entry_stays_inside_its_string(char):
    """The live path has to survive the same input, as valid parseable TOML."""
    employer = Employer(
        slug="x", name="Acme", category="prime", ats="lever",
        options={"board_token": f"a{char}b"}, verified=True, notes="Confirmed.",
    )
    parsed = tomllib.loads(to_toml([employer]))
    assert parsed["source"][0]["board_token"] == f"a{char}b"


def test_every_c0_control_character_is_escaped():
    from tactical_jobs.registry import _escape

    for code in list(range(0x20)) + [0x7F]:
        rendered = _escape(chr(code))
        assert chr(code) not in rendered, hex(code)
        parsed = tomllib.loads(f'v = "{rendered}"')
        assert parsed["v"] == chr(code), hex(code)


def test_unicode_survives_the_round_trip():
    employer = Employer(
        slug="x", name="Ejercito Espanol — Fuerza Ágil 人", category="prime",
        ats="lever", options={"board_token": "tést"}, verified=True, notes="Confirmed.",
    )
    parsed = tomllib.loads(to_toml([employer]))
    assert parsed["source"][0]["employer"] == "Ejercito Espanol — Fuerza Ágil 人"
    assert parsed["source"][0]["board_token"] == "tést"


def test_very_long_text_does_not_break_the_comment_guard():
    employer = Employer(
        slug="x", name="A" * 5000, category="prime", ats="lever",
        options={"board_token": "b" * 5000}, notes=("word " * 3000) + "Confirm.",
        aliases=("C" * 5000,),
    )
    text = to_toml([employer])
    assert _uncommented(text) == []
    assert tomllib.loads(text) == {}


def test_a_dict_option_renders_as_an_inline_table():
    """``field_map`` is a dict, and str() of one is a Python repr, not TOML.

    No seeded entry needs a field_map yet; the renderer should not be waiting to
    silently mangle the first one that does into a quoted string the adapter
    cannot use.
    """
    employer = Employer(
        slug="x", name="Acme", category="prime", ats="genericjson",
        options={"url": "https://example.com/api", "field_map": {"title": "name", "a b": "c"}},
        verified=True, notes="Confirmed.",
    )
    parsed = tomllib.loads(to_toml([employer]))
    assert parsed["source"][0]["field_map"] == {"title": "name", "a b": "c"}


def test_an_empty_dict_option_renders_as_an_empty_table():
    employer = Employer(
        slug="x", name="Acme", category="prime", ats="genericjson",
        options={"url": "https://example.com/api", "headers": {}},
        verified=True, notes="Confirmed.",
    )
    assert tomllib.loads(to_toml([employer]))["source"][0]["headers"] == {}


def test_a_none_option_is_omitted_rather_than_stringified():
    """TOML has no null. Emitting one produced the string "None"."""
    employer = Employer(
        slug="x", name="Acme", category="prime", ats="lever",
        options={"board_token": "acme", "location": None},
        verified=True, notes="Confirmed.",
    )
    text = to_toml([employer])
    block = tomllib.loads(text)["source"][0]
    assert "location" not in block
    assert "None" not in str(block.values())
    assert "omitted (no TOML null)" in text


def test_a_verified_entry_with_a_placeholder_is_not_emitted_live():
    """Verified plus an unfilled blank is a contradiction, not a green light.

    The naive rule would resolve it by shipping board_token = "PASTE_..." as
    live config -- a fetch against a nonsense token, which is worse than an
    entry that stayed commented.
    """
    employer = Employer(
        slug="x", name="Acme", category="prime", ats="greenhouse",
        options={"board_token": f"{PLACEHOLDER_PREFIX}TOKEN_HERE"},
        verified=True, notes="Confirm.",
    )
    text = to_toml([employer])
    assert tomllib.loads(text) == {}
    assert "NOT EMITTED LIVE" in text


def test_a_verified_entry_without_placeholders_still_goes_live():
    """The guard above must not swallow the case it is not about."""
    employer = Employer(
        slug="x", name="Acme", category="prime", ats="greenhouse",
        options={"board_token": "acme"}, verified=True, notes="Confirmed.",
    )
    assert tomllib.loads(to_toml([employer]))["source"][0]["board_token"] == "acme"


def test_an_option_key_needing_quotes_round_trips():
    employer = Employer(
        slug="x", name="Acme", category="prime", ats="genericjson",
        options={"url": "https://example.com", "odd key": 1},
        verified=True, notes="Confirmed.",
    )
    assert tomllib.loads(to_toml([employer]))["source"][0]["odd key"] == 1


def test_to_toml_carries_every_option_value_into_the_output():
    """Guards a renderer that quietly drops options -- or returns a constant."""
    for employer in REGISTRY:
        if employer.ats is None:
            continue
        text = to_toml([employer])
        for key, value in employer.options.items():
            assert f"{key} = " in text, f"{employer.slug}: {key} missing"
            if isinstance(value, str):
                assert value in text, f"{employer.slug}: {key} value missing"


def test_to_toml_header_is_honest_about_both_failure_modes():
    """A nonexistent token errors loudly; a wrong-but-alive one returns zero.

    The header used to claim the first case was silent, which is false -- http
    raises FetchError on a 404 and the pipeline logs an ERROR line. Overstating
    it invites a reader who knows better to distrust the rest of the file.
    """
    text = to_toml(REGISTRY)
    assert "ERROR line" in text
    assert "wrong but alive" in text
    assert "zero postings" in text


def test_to_toml_header_states_the_checks_need_no_credentials():
    assert "no API key, no account, no signup" in to_toml(REGISTRY)


# ---------------------------------------------------------------------------
# verification hints
# ---------------------------------------------------------------------------


def test_verification_hint_covers_every_kind_in_use():
    for kind in used_kinds():
        hint = verification_hint(kind)
        assert hint and "confirm the endpoint" not in hint, kind


def test_verification_hint_handles_an_unknown_ats():
    assert "ATS unknown" in verification_hint(None)


def test_verification_hint_falls_back_for_an_unmapped_kind():
    """And the fallback is distinguishable from a real hint, not a constant."""
    fallback = verification_hint("some-future-vendor")
    assert fallback
    assert fallback != verification_hint("greenhouse")
    assert fallback != verification_hint(None)


def test_verification_hint_is_specific_per_vendor():
    """A hint that reads the same for every kind is a hint nobody can act on."""
    hints = {kind: verification_hint(kind) for kind in used_kinds()}
    assert len(set(hints.values())) == len(hints), hints


# ---------------------------------------------------------------------------
# coverage of the landscape
# ---------------------------------------------------------------------------


def test_the_cited_award_holders_are_present():
    """EMPLOYERS.md documents these with sources; they are the highest-yield leads."""
    for slug in ("serco", "kbr", "gap-solutions"):
        assert by_slug(slug) is not None, slug


def test_the_named_specialists_are_present():
    for slug in ("o2x", "exos", "sword-performance", "fit-for-duty"):
        assert by_slug(slug) is not None, slug


def test_the_named_primes_are_present():
    for slug in (
        "leidos",
        "booz-allen-hamilton",
        "amentum",
        "kbr",
        "caci",
        "saic",
        "parsons",
        "magellan-federal",
        "icf",
        "chenega",
        "alutiiq",
        "akima",
        "aptive",
    ):
        assert by_slug(slug) is not None, slug


def test_the_named_federal_commands_are_present():
    for slug in (
        "army-h2f",
        "defense-health-agency",
        "department-of-veterans-affairs",
        "naval-special-warfare",
        "usasoc",
        "afsoc",
        "marsoc",
    ):
        assert by_slug(slug) is not None, slug


def test_the_named_associations_are_present():
    for slug in ("nsca", "nata", "acsm", "cscca", "aasp"):
        assert by_slug(slug) is not None, slug
