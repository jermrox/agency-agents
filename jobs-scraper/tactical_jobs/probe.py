"""Candidate ATS-board derivation and probe planning. NO NETWORK IO HAPPENS HERE.

THE PROBLEM THIS SOLVES
This project's worst recurring failure was guessed board tokens presented as
configuration: a plausible-looking ``board_token`` that was never checked
against the vendor's API, silently returning nothing forever. career-ops
(santifer/career-ops, MIT) solves the same problem in discover-ats.mjs by
deriving candidate slugs from a company name, probing each vendor's public
API, and accepting a board only when it exists AND currently lists at least
one job. This module ports that DERIVATION and URL-CONSTRUCTION layer into
this project's idiom.

WHAT THIS MODULE DOES NOT DO
**THIS MODULE PERFORMS NO NETWORK IO.** It prepares verification -- candidate
slugs, the exact probe URLs, a human-workable checklist, and ready-to-paste
config snippets -- but it never performs the verification itself. Every
candidate it emits is UNVERIFIED by construction, every config snippet carries
a ``# VERIFIED LIVE:`` line that only a human (or a networked CI job) may
complete after a live check, and NOTHING this module outputs may be enabled in
``sources.toml`` without that live check. A board "verifies" only when the
probe URL answers AND currently lists >= 1 job (career-ops's acceptance rule).

Ported from santifer/career-ops (MIT):
  - discover-ats.mjs        -- SLUG_RE guard, deriveSlug(), vendor probe
                               registry and order, the Workday exclusion rule,
                               WORKDAY_SEGMENT_RE, WORKDAY_INSTANCES
  - providers/greenhouse.mjs -- boards-api probe URL shape
  - providers/ashby.mjs      -- posting-api probe URL shape (case-sensitive slugs)
  - providers/lever.mjs      -- postings probe URL shape
  - providers/workday.mjs    -- CXS jobs endpoint shape (POST, coordinates)
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

__all__ = [
    "SLUG_RE",
    "WORKDAY_SEGMENT_RE",
    "WORKDAY_INSTANCES",
    "ProbeCandidate",
    "derive_slugs",
    "probe_urls",
    "workday_probe",
    "render_probe_plan",
]

# Safe charset for a slug that will be interpolated into an ATS URL. Guard
# ported from santifer/career-ops discover-ats.mjs SLUG_RE (MIT):
# /^[A-Za-z0-9._-]+$/ -- a tampered or malformed company name can never inject
# unexpected characters ('/', '?', '#', '@', spaces...) into a URL. Mixed case
# is intentional: Ashby boards are case-sensitive (AlephAlpha, DeepL).
# Anchored with \A...\Z like the JS original so the guard holds even for a
# caller using .match()/.search() instead of .fullmatch().
SLUG_RE = re.compile(r"\A[A-Za-z0-9._-]+\Z")

# Coordinate token guard for the Workday tenant/instance/site segments.
# Ported from santifer/career-ops discover-ats.mjs WORKDAY_SEGMENT_RE (MIT):
# /^[A-Za-z0-9_-]+$/ -- site names contain letters, digits, '_' and '-'
# (NVIDIAExternalCareerSite, External_Career_Site); instances are wdNN.
# Anchored with \A...\Z for the same fail-safe reason as SLUG_RE.
WORKDAY_SEGMENT_RE = re.compile(r"\A[A-Za-z0-9_-]+\Z")

# Workday instance subdomains, most common first. Reference list for a human
# hunting the data center of a known tenant+site -- NOT probed here. Ported
# from santifer/career-ops discover-ats.mjs WORKDAY_INSTANCES (MIT).
WORKDAY_INSTANCES: tuple[str, ...] = (
    "wd1", "wd2", "wd3", "wd5", "wd10", "wd12", "wd101", "wd103",
)

# Blind-probe vendors, in career-ops's probe order (discover-ats.mjs
# VENDOR_ORDER: gh, ashby, lever -- first live match wins). Workday is
# deliberately NOT here: see workday_probe below.
_BLIND_VENDORS: tuple[str, ...] = ("greenhouse", "ashby", "lever")

_VERIFIED_LIVE_PLACEHOLDER = (
    "# VERIFIED LIVE: <fill date + evidence, e.g. 2026-01-15 -- probe returned 12 jobs>"
)


@dataclass(frozen=True, slots=True)
class ProbeCandidate:
    """One vendor+slug combination worth a live check. Unverified by definition."""

    vendor: str
    """Adapter kind this candidate maps to (``greenhouse``/``ashby``/``lever``/``workday``)."""

    slug: str
    """The board token being tried. For workday this is the tenant."""

    probe_url: str
    """The vendor's public API URL that settles "exists?" and "lists >= 1 job?"."""

    config_snippet: str
    """The exact ``[[source]]`` TOML to paste IF (and only if) the probe succeeds.

    Carries a ``# VERIFIED LIVE:`` line the human completes with date and
    evidence. This module never fills that line -- it cannot know.
    """


def derive_slugs(company_name: str) -> list[str]:
    """Candidate board slugs for a company name, safest-bet first.

    The primary rule is ported verbatim from santifer/career-ops
    discover-ats.mjs deriveSlug() (MIT): lowercase, collapse every non-[a-z0-9]
    run to a single hyphen, strip leading/trailing hyphens ("Trade Republic"
    -> "trade-republic"). career-ops notes that this lowercasing misses
    camelCase Ashby boards (AlephAlpha, DeepL), which there require an
    explicit slug; the documented extras below recover the common cases:

      - joined:          hyphens dropped ("o2xhumanperformance") -- many
        boards register the bare concatenation rather than the hyphenation.
      - case-preserved:  non-alphanumerics stripped, original case kept
        ("O2XHumanPerformance", "AlephAlpha") -- only emitted when the result
        has an uppercase letter past position 0, i.e. when it could actually
        differ on a case-sensitive Ashby board.
      - first token:     the leading word alone ("o2x") -- companies commonly
        register just the brand name, not the full legal name.

    Every candidate is checked against SLUG_RE before it is returned, so a
    malformed or hostile name can never smuggle URL characters downstream.
    Deduped, order-preserving. A name with no safe candidate yields ``[]``.
    """
    name = str(company_name or "").strip()
    lowered = name.lower()

    hyphenated = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    joined = re.sub(r"[^a-z0-9]+", "", lowered)
    case_preserved = re.sub(r"[^A-Za-z0-9]+", "", name)
    if not any(ch.isupper() for ch in case_preserved[1:]):
        # Indistinguishable from ``joined`` on every case-insensitive vendor
        # and pointless on Ashby too ("Adyen" vs "adyen" is not a camelCase
        # board name) -- emitting it would just double the checklist.
        case_preserved = ""
    first_token = hyphenated.split("-", 1)[0] if hyphenated else ""

    candidates: list[str] = []
    for slug in (hyphenated, joined, case_preserved, first_token):
        if slug and SLUG_RE.fullmatch(slug) and slug not in candidates:
            candidates.append(slug)
    return candidates


# TOML basic-string escapes with shorthand forms; every other control
# character (U+0000..U+001F, U+007F) gets a \uXXXX escape below. Without
# this a company name carrying an interior newline or tab would render an
# invalid snippet that tomllib rejects -- breaking the module's contract
# that every config_snippet round-trips through tomllib.loads.
_TOML_ESCAPES = {
    "\\": "\\\\",
    '"': '\\"',
    "\b": "\\b",
    "\t": "\\t",
    "\n": "\\n",
    "\f": "\\f",
    "\r": "\\r",
}


def _toml_string(value: str) -> str:
    """Quote a value as a TOML basic string (escaping controls too)."""
    out: list[str] = []
    for ch in value:
        if ch in _TOML_ESCAPES:
            out.append(_TOML_ESCAPES[ch])
        elif ord(ch) < 0x20 or ord(ch) == 0x7F:
            out.append(f"\\u{ord(ch):04X}")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


def _snippet(
    vendor: str,
    slug: str,
    probe_url: str,
    *,
    recipe: str,
    employer: str = "",
    extra_lines: tuple[str, ...] = (),
    probe_note: str = "",
) -> str:
    """Render the ``[[source]]`` TOML block a successful probe would unlock."""
    lines = [
        f"# Endpoint recipe ported from santifer/career-ops {recipe} (MIT).",
        f"# Probe URL{probe_note}: {probe_url}",
        "# Accept ONLY if the probe answered AND listed >= 1 job. Until then this",
        "# block must not be pasted into sources.toml.",
        _VERIFIED_LIVE_PLACEHOLDER,
        "[[source]]",
        f"kind = {_toml_string(vendor)}",
        f"name = {_toml_string(slug)}",
    ]
    lines.extend(extra_lines)
    if employer:
        # The company name exactly as the caller supplied it -- input echoed
        # back, never a value inferred from any API response.
        lines.append(f"employer = {_toml_string(employer)}")
    return "\n".join(lines) + "\n"


def _greenhouse_candidate(slug: str, employer: str) -> ProbeCandidate:
    # Endpoint recipe ported from santifer/career-ops providers/greenhouse.mjs
    # resolveApiUrl() and discover-ats.mjs VENDORS.gh.api (MIT):
    # https://boards-api.greenhouse.io/v1/boards/<slug>/jobs
    probe_url = f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"
    return ProbeCandidate(
        vendor="greenhouse",
        slug=slug,
        probe_url=probe_url,
        config_snippet=_snippet(
            "greenhouse",
            slug,
            probe_url,
            recipe="providers/greenhouse.mjs",
            employer=employer,
            extra_lines=(f"board_token = {_toml_string(slug)}",),
        ),
    )


def _ashby_candidate(slug: str, employer: str) -> ProbeCandidate:
    # Endpoint recipe ported from santifer/career-ops providers/ashby.mjs
    # resolveApiUrl() (MIT):
    # https://api.ashbyhq.com/posting-api/job-board/<slug>?includeCompensation=true
    # Slug case is preserved end-to-end: Ashby boards are case-sensitive.
    probe_url = (
        f"https://api.ashbyhq.com/posting-api/job-board/{slug}?includeCompensation=true"
    )
    return ProbeCandidate(
        vendor="ashby",
        slug=slug,
        probe_url=probe_url,
        config_snippet=_snippet(
            "ashby",
            slug,
            probe_url,
            recipe="providers/ashby.mjs",
            employer=employer,
            extra_lines=(f"board_token = {_toml_string(slug)}",),
        ),
    )


def _lever_candidate(slug: str, employer: str) -> ProbeCandidate:
    # Endpoint recipe ported from santifer/career-ops providers/lever.mjs
    # resolveApiUrl() (MIT): https://api.lever.co/v0/postings/<slug>
    probe_url = f"https://api.lever.co/v0/postings/{slug}"
    return ProbeCandidate(
        vendor="lever",
        slug=slug,
        probe_url=probe_url,
        config_snippet=_snippet(
            "lever",
            slug,
            probe_url,
            recipe="providers/lever.mjs",
            employer=employer,
            extra_lines=(f"board_token = {_toml_string(slug)}",),
        ),
    )


_CANDIDATE_BUILDERS = {
    "greenhouse": _greenhouse_candidate,
    "ashby": _ashby_candidate,
    "lever": _lever_candidate,
}


def probe_urls(company_name: str, extra_slugs: Iterable[str] = ()) -> list[ProbeCandidate]:
    """Every blind-probe candidate for one company: greenhouse, ashby, lever.

    Workday is deliberately absent. career-ops's rule (discover-ats.mjs):
    a Workday board lives at ``<tenant>.<instance>.myworkdayjobs.com/<site>``
    -- three coordinates, only one of which (tenant) is even approximately
    derivable from a name. The site segment in particular is unguessable
    ("NVIDIAExternalCareerSite" vs "External_Career_Site"), so blind-probing
    Workday from a name is exactly the token-guessing this module exists to
    kill. Use :func:`workday_probe` with coordinates read off the employer's
    real careers URL instead.

    ``extra_slugs`` carries explicit human-supplied slugs (career-ops's
    ``slug:`` input field -- required there for camelCase Ashby boards).
    Every slug, derived or explicit, must pass SLUG_RE or it is dropped:
    no URL is ever built from an unsafe string.
    """
    slugs: list[str] = list(derive_slugs(company_name))
    for slug in extra_slugs:
        if (
            isinstance(slug, str)
            and SLUG_RE.fullmatch(slug)
            and slug not in slugs
        ):
            slugs.append(slug)

    employer = str(company_name or "").strip()
    candidates: list[ProbeCandidate] = []
    for slug in slugs:
        for vendor in _BLIND_VENDORS:
            candidates.append(_CANDIDATE_BUILDERS[vendor](slug, employer))
    return candidates


def workday_probe(tenant: str, data_center: str, site: str) -> ProbeCandidate:
    """Workday probe candidate from EXPLICIT coordinates -- never from a name.

    The coordinates come straight off the employer's careers URL:
    ``https://leidos.wd5.myworkdayjobs.com/External`` is tenant ``leidos``,
    data center ``wd5``, site ``External``. If the data center is unknown,
    ``WORKDAY_INSTANCES`` lists the common ones to try, most common first
    (ported from discover-ats.mjs); each guess is a separate call here.

    Endpoint recipe ported from santifer/career-ops providers/workday.mjs
    resolveEndpoint() (MIT):
    ``https://<tenant>.<instance>.myworkdayjobs.com/wday/cxs/<tenant>/<site>/jobs``
    Note the probe is a POST (the CXS API rejects GET) with body
    ``{"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""}``.

    Raises :class:`ValueError` on any segment failing WORKDAY_SEGMENT_RE, so a
    malformed coordinate can never reach a URL.
    """
    segments = {"tenant": tenant, "data_center": data_center, "site": site}
    for label, value in segments.items():
        if not isinstance(value, str) or not WORKDAY_SEGMENT_RE.fullmatch(value):
            raise ValueError(
                f"workday_probe: unsafe {label} {value!r} -- must match [A-Za-z0-9_-]+"
            )

    probe_url = (
        f"https://{tenant}.{data_center}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs"
    )
    snippet = _snippet(
        "workday",
        tenant,
        probe_url,
        recipe="providers/workday.mjs",
        probe_note=(
            ' (POST {"appliedFacets": {}, "limit": 20, "offset": 0, "searchText": ""})'
        ),
        extra_lines=(
            f"tenant = {_toml_string(tenant)}",
            f"site = {_toml_string(site)}",
            f"data_center = {_toml_string(data_center)}",
        ),
    )
    return ProbeCandidate(
        vendor="workday", slug=tenant, probe_url=probe_url, config_snippet=snippet
    )


def render_probe_plan(companies: list[str]) -> str:
    """Markdown checklist a human (or a networked CI job) works through.

    One section per company, one entry per candidate, two checkboxes per
    entry: "board exists?" and "lists >= 1 job?". Both boxes must check
    before the candidate's config snippet may be completed and pasted.
    This function only PLANS the verification -- it performs none of it.
    """
    lines = [
        "# ATS board probe plan",
        "",
        "Prepared by `tactical_jobs.probe`, which performs **no network IO**.",
        "Every candidate below is **unverified**. Work the checklist with a",
        "browser or `curl`; a candidate passes only when BOTH boxes check:",
        "the probe URL answers (not a 404), and the response currently lists",
        ">= 1 job. An existing-but-empty board is NOT a pass (career-ops",
        "acceptance rule). Only then complete the `# VERIFIED LIVE:` line in",
        "that candidate's `[[source]]` snippet and paste it into sources.toml.",
        "",
        "Workday is excluded from blind probing: tenant, data center, and site",
        "cannot be derived from a company name (the site segment is",
        "unguessable). For a known Workday employer, read the coordinates off",
        "its careers URL and use `tactical_jobs.probe.workday_probe(tenant,",
        "data_center, site)` instead.",
        "",
    ]

    for raw_name in companies:
        display = str(raw_name or "").strip()
        lines.append(f"## {display or '(unnamed company)'}")
        lines.append("")
        candidates = probe_urls(raw_name)
        if not candidates:
            lines.append(
                "- no URL-safe slug is derivable from this name; find the board"
                " by hand and re-run with an explicit slug"
            )
        for cand in candidates:
            lines.append(f"- {cand.vendor} `{cand.slug}` -- `{cand.probe_url}`")
            lines.append("  - [ ] board exists? (probe URL answers, not 404)")
            lines.append("  - [ ] lists >= 1 job?")
        lines.append("")

    return "\n".join(lines).rstrip("\n") + "\n"
