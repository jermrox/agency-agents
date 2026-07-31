"""The tactical human performance employer landscape, as reviewable data.

THE PROBLEM THIS SOLVES
This project ships nineteen working source adapters and that was never the
bottleneck. Knowing *who to point them at* is. An adapter with no employer
behind it fetches nothing; the scarce resource in this niche is the list of
organizations that actually embed strength coaches, athletic trainers,
physical therapists, performance dietitians, and cognitive performance
specialists with military units, police departments, and fire services.

That list has been living in comments inside a TOML file, which is the worst
possible home for it. Comments cannot be tested, cannot be filtered, cannot be
counted, and cannot record *why* an entry is there or how sure anyone is about
it. So the list moves here, into ordinary Python data with a dataclass around
it, and becomes something a test suite can hold to a standard.

WHAT THIS MODULE IS NOT
It is not a source adapter and it does not fetch anything. It never edits
``sources.toml``. It emits a *proposal* -- TOML you read, verify, and paste --
in the same spirit as :mod:`tactical_jobs.discover` and
:mod:`tactical_jobs.contracts`, which produce candidates a human acts on rather
than configuration that silently goes live.

THE HONESTY PROBLEM, AND WHY EVERY ENTRY IS UNVERIFIED
An ATS board token is a fact about the world. ``boards-api.greenhouse.io`` either
answers for ``o2x`` or it does not, and the only way to know is to ask it. This
module was written in an environment with **no outbound network**, so nothing
here has been asked. Every single entry therefore carries ``verified=False``,
and :func:`to_toml` emits unverified entries **commented out**.

That last part is the load-bearing design decision. A wrong board token is the
worst failure mode this project has: it does not crash, it returns an empty list
forever, and an empty list is indistinguishable from "that employer is not
hiring right now". Comment-by-default converts a silent, permanent miss into a
thirty-second copy-paste a human performs while looking at the endpoint's actual
response. The cost of that friction is one minute per employer. The cost of
skipping it is not noticing for six months.

The registry distinguishes three grades of uncertainty, and the ``notes`` field
always says which one applies:

  * **Guessed vendor, guessed token.** Workday tenants are conventionally the
    company name (``leidos``, ``boozallen``), so the guess is principled -- but
    it is still a guess, and ``data_center`` in particular (``wd1`` vs ``wd5``)
    is not derivable from anything.
  * **Guessed vendor, unknown token.** The option holds a ``PASTE_...``
    placeholder. Obviously not a real value, and :func:`placeholder_options`
    reports it.
  * **Vendor unknown.** ``ats`` is ``None``. No source table is emitted at all
    and :meth:`Employer.to_source_config` refuses to invent one.

WHY THE PRIMES ARE HERE BUT ARE NOT THE WHOLE STORY
The obvious defense primes -- Leidos, Booz Allen, CACI, SAIC -- are reasonable
places to look and are included. But the research recorded in ``EMPLOYERS.md``
turned up something more useful: the firms that actually won the big Army H2F
and USSOCOM POTFF vehicles are Serco, KBR, and GAP Solutions, plus the Team
Serco subcontractors. Those awards are cited and verifiable; they are the
highest-yield entries in this file and they are not names anyone would have
guessed. Both groups are listed, with the difference stated in the notes,
because "we guessed" and "we have a press release" are different claims and the
registry should never blur them.
"""

from __future__ import annotations

import re
import textwrap
from dataclasses import dataclass, field
from typing import Any, Iterator, Sequence

__all__ = [
    "CATEGORIES",
    "CREDENTIALED_KINDS",
    "Employer",
    "KEYLESS_KINDS",
    "PLACEHOLDER_PREFIX",
    "REGISTRY",
    "SOURCE_KINDS",
    "all_employers",
    "by_category",
    "by_slug",
    "match_employer",
    "placeholder_options",
    "to_toml",
    "used_kinds",
    "verification_hint",
    "verified_count",
]


CATEGORIES: tuple[str, ...] = (
    "prime",
    "specialist",
    "federal",
    "state-local",
    "association",
    "academic",
    "nonprofit",
)
"""Every category an :class:`Employer` may claim.

The split is by *hiring behaviour*, not by size or sector, because that is what
changes how you reach them. A prime posts to a commercial ATS and hires in
bursts tied to award dates. A federal command posts to USAJOBS and hires on a
fiscal calendar. An association does not hire at all -- it runs a career centre
where everyone else's postings land, which makes it the densest single source
of relevant listings anywhere in this niche.
"""

SOURCE_KINDS: frozenset[str] = frozenset(
    {
        "ashby",
        "assocboard",
        "bamboohr",
        "breezy",
        "genericjson",
        "governmentjobs",
        "greenhouse",
        "jazzhr",
        "jobsrss",
        "jsonld",
        "knownboards",
        "lever",
        "personio",
        "recruitee",
        "rippling",
        "rss",
        "smartrecruiters",
        "teamtailor",
        "usajobs",
        "workable",
        "workday",
    }
)
"""Adapter ``kind`` strings this project ships.

Duplicated deliberately rather than imported from ``sources``: this module is a
data file about the outside world and importing the adapter registry would make
every employer lookup drag in urllib, the HTML parsers, and every adapter class.
The test suite cross-checks the two so the duplication cannot drift silently.
"""

CREDENTIALED_KINDS: frozenset[str] = frozenset({"usajobs", "jazzhr", "teamtailor"})
"""Adapters that need an API key. Mirrors ``sources.CREDENTIALED_KINDS``.

No entry in this registry may use one. The operator this project is built for
has no credentials and cannot obtain any, so an entry pointing at a
key-requiring adapter is not a lead -- it is a dead end that looks like a lead.
"""

KEYLESS_KINDS: frozenset[str] = SOURCE_KINDS - CREDENTIALED_KINDS

PLACEHOLDER_PREFIX = "PASTE_"
"""Marks an option value nobody has filled in yet.

Shouting in capitals beats a plausible-looking dummy value. ``"acme"`` as a
board token looks like configuration; ``"PASTE_GREENHOUSE_BOARD_TOKEN_HERE"``
cannot be mistaken for one, and it survives a careless copy-paste as an obvious
error rather than a silent empty fetch.
"""


# ---------------------------------------------------------------------------
# name normalization
# ---------------------------------------------------------------------------

_LEGAL_SUFFIXES = frozenset(
    {
        "inc",
        "incorporated",
        "llc",
        "ltd",
        "limited",
        "corp",
        "corporation",
        "co",
        "plc",
        "lp",
        "llp",
    }
)


def _normalize(value: str) -> str:
    """Case, punctuation, and spacing folded away.

    ``&`` becomes ``and`` before punctuation is stripped, otherwise "Marsh &
    McLennan" and "Marsh and McLennan" normalize to different keys.
    """
    lowered = value.lower().replace("&", " and ")
    return " ".join(re.sub(r"[^a-z0-9]+", " ", lowered).split())


def _loose(value: str) -> str:
    """A second, more forgiving key: leading article and legal suffixes gone.

    Kept separate from :func:`_normalize` and tried only after it, so an exact
    match always wins. Collapsing "The Geneva Foundation" and "Geneva
    Foundation" is desirable; doing it *first* would let a loose collision
    outrank a name someone typed exactly right.
    """
    words = _normalize(value).split()
    if words and words[0] == "the":
        words = words[1:]
    while words and words[-1] in _LEGAL_SUFFIXES:
        words = words[:-1]
    return " ".join(words)


# ---------------------------------------------------------------------------
# the record
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class Employer:
    """One organization worth pointing a source adapter at."""

    slug: str
    """Stable identifier. Also the ``name`` of the emitted source block, which
    is what shows up in run summaries and in the ``source`` field of a posting."""

    name: str
    """Display name, as the organization writes it."""

    category: str
    """One of :data:`CATEGORIES`."""

    ats: str | None
    """A kind from :data:`SOURCE_KINDS`, or ``None`` when the vendor is unknown.

    ``None`` is a real answer and appears throughout this registry on purpose.
    Some of these employers run bespoke or unidentified career sites, and
    recording "we do not know" is more useful than recording a guess that reads
    like knowledge.
    """

    options: dict[str, Any]
    """The options the emitted source table carries, adapter-specific."""

    verified: bool = False
    """Has this configuration actually been confirmed against the live endpoint?

    False for every shipped entry. Flipping one to True is a claim that somebody
    ran the request and read the response; the test suite enforces that claim
    rather than trusting it.
    """

    notes: str = ""
    """Why this entry exists, how confident it is, and how to confirm it."""

    aliases: tuple[str, ...] = ()
    """Other names this organization goes by -- acronyms, former names, the
    program name people actually say out loud (THOR3, POTFF, H2F)."""

    def to_source_config(self) -> dict[str, Any]:
        """Render as a ``[[source]]`` table: ``kind``, ``name``, then options.

        ``employer`` is filled in from :attr:`name` when the options do not set
        it. Nearly every adapter falls back to its own source name for the
        employer label, which produces postings attributed to ``booz-allen``
        rather than ``Booz Allen Hamilton`` -- fine for a log line, wrong on a
        public jobs page.

        Raises ``ValueError`` when :attr:`ats` is ``None``. There is no
        defensible default kind, and picking one would manufacture exactly the
        false confidence this module exists to prevent.
        """
        if self.ats is None:
            raise ValueError(
                f"employer '{self.slug}' has no known ATS: its careers vendor was "
                f"never identified, so no source table can be built. Open the "
                f"organization's careers page, note which platform it redirects "
                f"to, then set 'ats' to the matching adapter kind."
            )
        config: dict[str, Any] = {"kind": self.ats, "name": self.slug}
        config.update(self.options)
        config.setdefault("employer", self.name)
        return config

    def search_keys(self) -> tuple[str, ...]:
        """Every string :func:`match_employer` should recognize this entry by."""
        return (self.slug, self.name, *self.aliases)


# ---------------------------------------------------------------------------
# how to confirm each vendor
# ---------------------------------------------------------------------------

VERIFICATION_HINTS: dict[str, str] = {
    "greenhouse": (
        'curl -s "https://boards-api.greenhouse.io/v1/boards/<board_token>/jobs" '
        "| head -c 300"
    ),
    "lever": (
        'curl -s "https://api.lever.co/v0/postings/<board_token>?mode=json" | head -c 300'
    ),
    "ashby": (
        "open https://jobs.ashbyhq.com/<board_token> and confirm the board loads"
    ),
    "workable": 'curl -s "https://apply.workable.com/api/v1/widget/accounts/<board_token>"',
    "smartrecruiters": 'curl -s "https://api.smartrecruiters.com/v1/companies/<company_id>/postings"',
    "recruitee": 'curl -s "https://<board_token>.recruitee.com/api/offers/"',
    "bamboohr": 'curl -s "https://<subdomain>.bamboohr.com/careers/list"',
    "breezy": 'curl -s "https://<company>.breezy.hr/json"',
    "personio": "open https://<company>.jobs.personio.de and confirm the board loads",
    "rippling": "open the employer careers page and confirm the Rippling board token in the URL",
    "workday": (
        "open the careers page and read tenant/data_center/site straight out of "
        "https://{tenant}.{data_center}.myworkdayjobs.com/{site}"
    ),
    "governmentjobs": (
        "open the agency page on governmentjobs.com and take the agency slug out "
        "of https://www.governmentjobs.com/careers/<agency>"
    ),
    "jsonld": (
        "open one job detail page, view source, and confirm a "
        '<script type="application/ld+json"> block with "@type": "JobPosting"'
    ),
    "rss": "fetch the feed URL in a browser and confirm it returns XML with recent items",
    "jobsrss": "fetch the feed URL in a browser and confirm it returns XML with recent items",
    "assocboard": "fetch the board URL and confirm it returns JSON or RSS, not an HTML login wall",
    "knownboards": "run with --dry-run and read which of the bundled boards answered",
    "genericjson": "fetch the URL and confirm the JSON shape still matches field_map",
}


def verification_hint(ats: str | None) -> str:
    """The one-line check that turns a guess into a fact."""
    if ats is None:
        return (
            "ATS unknown -- open the organization's careers page and note which "
            "platform it redirects to"
        )
    return VERIFICATION_HINTS.get(
        ats, "confirm the endpoint answers before enabling this source"
    )


def placeholder_options(employer: Employer) -> tuple[str, ...]:
    """Option keys still holding a ``PASTE_...`` placeholder.

    Lets a caller -- or a test -- tell "we guessed the token" apart from "nobody
    has supplied a token", which are very different amounts of work remaining.
    """
    return tuple(
        key
        for key, value in sorted(employer.options.items())
        if isinstance(value, str) and value.startswith(PLACEHOLDER_PREFIX)
    )


# ---------------------------------------------------------------------------
# the registry
#
# Ordered by category, and within a category by how much is actually known
# about the entry. Cited contract winners come before guessed primes because
# that is the order someone working the list should work it in.
# ---------------------------------------------------------------------------

REGISTRY: tuple[Employer, ...] = (
    # -- primes and contractors: cited award holders first ------------------
    Employer(
        slug="serco",
        name="Serco",
        category="prime",
        ats="workday",
        options={"tenant": "serco", "site": "Serco", "data_center": "wd3"},
        notes=(
            "Highest-value entry in this file. Serco announced a US Army H2F award "
            "worth up to $247M in January 2025, planning to hire over 350 certified "
            "strength and conditioning coaches in the base year across 45 brigades "
            "at 15 CONUS locations (see EMPLOYERS.md). The award is cited; the ATS "
            "is a guess -- Serco North America appears to recruit through Workday "
            "and the tenant is assumed to be the company name. Confirm by opening "
            "the Serco careers page and reading tenant, data_center, and site out "
            "of the myworkdayjobs.com URL before enabling."
        ),
        aliases=("Serco Inc", "Serco North America", "Team Serco"),
    ),
    Employer(
        slug="kbr",
        name="KBR",
        category="prime",
        ats="jsonld",
        options={
            "sitemap": "PASTE_KBR_CAREERS_SITEMAP_URL_HERE",
            "url_include": ["/job/"],
            "max_urls": 300,
        },
        notes=(
            "Holds the USSOCOM POTFF contract (~$500M) staffing psychologists, "
            "social workers, physical therapists, athletic trainers, dietitians, "
            "and strength coaches -- cited in EMPLOYERS.md. Unusually, KBR runs a "
            "dedicated POTFF careers page at careers.kbr.com/us/en/potff2, which is "
            "worth watching directly. That site is not one of the JSON ATS vendors "
            "this project speaks, so JSON-LD over the careers sitemap is the "
            "keyless route. Confirm by opening a KBR job detail page, viewing "
            "source, and checking for a JobPosting ld+json block, then find the "
            "sitemap URL and replace the placeholder."
        ),
        aliases=("KBRwyle", "Kellogg Brown and Root"),
    ),
    Employer(
        slug="gap-solutions",
        name="GAP Solutions",
        category="prime",
        ats=None,
        options={},
        notes=(
            "Received a $100M+ Army H2F contract award (cited in EMPLOYERS.md), so "
            "the hiring is real even though the plumbing is not known. The careers "
            "vendor was not identified and is deliberately left as None rather than "
            "guessed. Confirm by opening gapsi.com, following the careers link, and "
            "noting which ATS the URL lands on; if it is one of this project's "
            "adapters set ats accordingly, otherwise try jsonld."
        ),
        aliases=("GAP Solutions Inc", "GAPSI"),
    ),
    Employer(
        slug="higherechelon",
        name="HigherEchelon",
        category="prime",
        ats="greenhouse",
        options={"board_token": "PASTE_GREENHOUSE_BOARD_TOKEN_HERE"},
        notes=(
            "Team Serco subcontractor on the Army H2F award. Vendor is a guess -- "
            "Greenhouse is the common choice for firms this size -- and the token "
            "is unknown, hence the placeholder. Confirm by opening the "
            "HigherEchelon careers page: a Greenhouse board shows job URLs under "
            "boards.greenhouse.io/<token>, and that token goes in board_token."
        ),
        aliases=("Higher Echelon",),
    ),
    Employer(
        slug="hyperion-biotechnology",
        name="Hyperion Biotechnology",
        category="prime",
        ats=None,
        options={},
        notes=(
            "Team Serco subcontractor on the Army H2F award. A small firm with no "
            "publicly known ATS, so ats stays None. Confirm by opening the "
            "company's careers page and identifying the platform before adding a "
            "kind."
        ),
        aliases=("Hyperion Biotechnology Inc",),
    ),
    Employer(
        slug="resolution-think",
        name="Resolution Think",
        category="prime",
        ats=None,
        options={},
        notes=(
            "Team Serco subcontractor on the Army H2F award. ATS not identified. "
            "Confirm by locating the careers page and noting the vendor; jsonld is "
            "the fallback when no JSON API exists."
        ),
        aliases=("Resolution Think LLC",),
    ),
    Employer(
        slug="leidos",
        name="Leidos",
        category="prime",
        ats="workday",
        options={
            "tenant": "leidos",
            "site": "External",
            "data_center": "wd5",
            "search_terms": [
                "human performance",
                "strength and conditioning",
                "athletic trainer",
            ],
        },
        notes=(
            "A guessed prime, not a cited H2F winner -- included because Leidos "
            "carries large DoD health and readiness portfolios, not because any "
            "specific tactical human performance award was found. Workday is "
            "well established as the vendor; tenant/site/data_center match the "
            "values already sitting unverified in sources.keyless.toml. Confirm by "
            "opening the Leidos careers page and reading the myworkdayjobs.com URL."
        ),
        aliases=("Leidos Holdings", "Leidos Inc"),
    ),
    Employer(
        slug="booz-allen-hamilton",
        name="Booz Allen Hamilton",
        category="prime",
        ats="workday",
        options={
            "tenant": "boozallen",
            "site": "BoozAllen",
            "data_center": "wd1",
            "search_terms": [
                "human performance",
                "athletic trainer",
                "physical therapist",
            ],
        },
        notes=(
            "A guessed prime rather than a cited award holder. Workday is the "
            "known vendor; the tenant and site are the values already carried "
            "unverified in sources.keyless.toml. Confirm by opening the Booz Allen "
            "careers page and reading tenant, data_center, and site out of the URL."
        ),
        aliases=("Booz Allen", "BAH"),
    ),
    Employer(
        slug="amentum",
        name="Amentum",
        category="prime",
        ats="workday",
        options={"tenant": "amentum", "site": "Amentum", "data_center": "wd1"},
        notes=(
            "Guessed prime. Amentum holds broad DoD base-operations and training "
            "support work that has historically included fitness and readiness "
            "staffing. Workday is the assumed vendor with the tenant guessed from "
            "the company name; data_center is not derivable and wd1 is a default. "
            "Confirm both from the careers page URL before enabling."
        ),
        aliases=("Amentum Services",),
    ),
    Employer(
        slug="caci",
        name="CACI International",
        category="prime",
        ats="workday",
        options={"tenant": "caci", "site": "External", "data_center": "wd1"},
        notes=(
            "Guessed prime and a lower-confidence vendor guess than Leidos or Booz "
            "Allen: CACI's careers site may not be Workday at all. Confirm first "
            "that careers.caci.com redirects to a myworkdayjobs.com URL; if it does "
            "not, switch this entry to jsonld and point it at the careers sitemap."
        ),
        aliases=("CACI", "CACI International Inc"),
    ),
    Employer(
        slug="saic",
        name="SAIC",
        category="prime",
        ats="workday",
        options={"tenant": "saic", "site": "External", "data_center": "wd1"},
        notes=(
            "Guessed prime. Workday assumed with the tenant guessed from the "
            "company name; site and data_center are defaults, not observations. "
            "Confirm all three from the careers page URL."
        ),
        aliases=("Science Applications International Corporation",),
    ),
    Employer(
        slug="parsons",
        name="Parsons Corporation",
        category="prime",
        ats="workday",
        options={"tenant": "parsons", "site": "Parsons", "data_center": "wd5"},
        notes=(
            "Guessed prime with a guessed Workday tenant. Confirm tenant, site, and "
            "data_center from the careers page URL before enabling."
        ),
        aliases=("Parsons",),
    ),
    Employer(
        slug="magellan-federal",
        name="Magellan Federal",
        category="prime",
        ats="workday",
        options={"tenant": "PASTE_WORKDAY_TENANT_HERE", "site": "External"},
        notes=(
            "One of the longest-running providers of military human performance and "
            "resilience staffing, which makes it a high-value target. Complicated by "
            "corporate history: Magellan Federal was acquired into Acuity "
            "International, so postings may live on either careers site. Vendor is a "
            "guess and the tenant is genuinely unknown, hence the placeholder. "
            "Confirm by checking both the Magellan Federal and Acuity International "
            "careers pages and reading the tenant out of whichever is Workday."
        ),
        aliases=("Magellan Health Federal", "Acuity International"),
    ),
    Employer(
        slug="icf",
        name="ICF International",
        category="prime",
        ats="workday",
        options={"tenant": "icf", "site": "ICF_External", "data_center": "wd5"},
        notes=(
            "Guessed prime holding federal health and human services work. Workday "
            "assumed; tenant guessed from the company name and the site string is a "
            "convention, not an observation. Confirm from the careers page URL."
        ),
        aliases=("ICF", "ICF Consulting"),
    ),
    Employer(
        slug="chenega",
        name="Chenega Corporation",
        category="prime",
        ats="jsonld",
        options={
            "sitemap": "PASTE_CHENEGA_CAREERS_SITEMAP_URL_HERE",
            "url_include": ["/job", "/careers/"],
            "max_urls": 300,
        },
        notes=(
            "Alaska Native Corporation holding substantial DoD services work, "
            "including medical and base support that carries fitness and readiness "
            "roles. Its careers site appears to be iCIMS, for which this project "
            "ships no JSON adapter, so JSON-LD over the sitemap is the keyless "
            "route. Confirm by opening a job detail page and checking for a "
            "JobPosting ld+json block, then supply the sitemap URL."
        ),
        aliases=("Chenega MIOS", "Chenega Corp"),
    ),
    Employer(
        slug="alutiiq",
        name="Alutiiq",
        category="prime",
        ats="jsonld",
        options={
            "sitemap": "PASTE_ALUTIIQ_CAREERS_SITEMAP_URL_HERE",
            "url_include": ["/job", "/careers/"],
            "max_urls": 300,
        },
        notes=(
            "Alaska Native Corporation (Afognak family) with DoD services and "
            "training support contracts. Vendor is unconfirmed and likely iCIMS, so "
            "jsonld is the assumed route. Confirm by checking a job detail page for "
            "JobPosting ld+json markup and then locating the sitemap."
        ),
        aliases=("Afognak Native Corporation", "Alutiiq LLC"),
    ),
    Employer(
        slug="akima",
        name="Akima",
        category="prime",
        ats="jsonld",
        options={
            "sitemap": "PASTE_AKIMA_CAREERS_SITEMAP_URL_HERE",
            "url_include": ["/job", "/careers/"],
            "max_urls": 300,
        },
        notes=(
            "Alaska Native Corporation operating many subsidiaries across DoD "
            "services; postings are frequently branded by subsidiary rather than by "
            "Akima, which is worth knowing before judging the employer field. "
            "Vendor unconfirmed, jsonld assumed. Confirm by inspecting a job detail "
            "page for ld+json markup."
        ),
        aliases=("Akima LLC", "NANA Regional Corporation"),
    ),
    Employer(
        slug="aptive",
        name="Aptive Resources",
        category="prime",
        ats="greenhouse",
        options={"board_token": "PASTE_GREENHOUSE_BOARD_TOKEN_HERE"},
        notes=(
            "Mid-size federal consultancy with VA health work. Greenhouse is a "
            "vendor guess based on company size and sector; the token is unknown. "
            "Confirm by opening the Aptive careers page and reading the token out "
            "of a boards.greenhouse.io/<token> job URL."
        ),
        aliases=("Aptive",),
    ),
    # -- specialists: human performance is the whole business ---------------
    Employer(
        slug="o2x",
        name="O2X Human Performance",
        category="specialist",
        ats="greenhouse",
        options={"board_token": "o2x"},
        notes=(
            "The archetypal specialist: tactical human performance for military and "
            "first responders, so essentially every posting is relevant and the "
            "classifier has little work to do. Greenhouse with board_token 'o2x' is "
            "the value already carried unverified in sources.keyless.toml -- a "
            "guess derived from the brand name, not a confirmed token. Confirm with "
            "the greenhouse curl check before enabling."
        ),
        aliases=("O2X", "O2X Human Performance LLC"),
    ),
    Employer(
        slug="exos",
        name="EXOS",
        category="specialist",
        ats="lever",
        options={"board_token": "teamexos"},
        notes=(
            "Performance training firm with long-standing military and government "
            "contracts. Lever with board_token 'teamexos' mirrors the unverified "
            "value in sources.keyless.toml. Confirm with the lever curl check; if "
            "it 404s, try the company's careers page and re-read the vendor."
        ),
        aliases=("Team EXOS", "Athletes Performance"),
    ),
    Employer(
        slug="psi",
        name="PSI",
        category="specialist",
        ats="jsonld",
        options={
            "sitemap": "PASTE_ATHLETICTRAINERJOB_SITEMAP_URL_HERE",
            "url_include": ["/job"],
            "max_urls": 200,
        },
        notes=(
            "Places athletic trainers directly with US military units and posts "
            "through athletictrainerjob.com, which makes it unusually concentrated "
            "for this niche. The site is not a known JSON ATS, so jsonld is the "
            "assumed route and the sitemap URL is unknown. Confirm by opening a "
            "posting on athletictrainerjob.com and checking for JobPosting ld+json "
            "markup; if absent, the rss adapter against any feed the site offers is "
            "the fallback."
        ),
        aliases=("Professional Sports Institute", "athletictrainerjob.com"),
    ),
    Employer(
        slug="sword-performance",
        name="Sword Performance",
        category="specialist",
        ats=None,
        options={},
        notes=(
            "Tactical performance company working with military and first responder "
            "populations. No ATS identified and none guessed. Confirm by opening "
            "the company site, following any careers link, and recording the vendor "
            "before setting ats."
        ),
        aliases=("Sword Performance Inc",),
    ),
    Employer(
        slug="fit-for-duty",
        name="Fit For Duty",
        category="specialist",
        ats=None,
        options={},
        notes=(
            "Provides fitness and wellness programming to public safety agencies -- "
            "fire, EMS, and law enforcement -- which is the half of this market that "
            "the defense-focused sources miss entirely. ATS not identified. Confirm "
            "by locating the careers page and noting the platform."
        ),
        aliases=("Fit for Duty LLC", "FitForDuty"),
    ),
    Employer(
        slug="tactical-athlete-program",
        name="Tactical Athlete Program providers",
        category="specialist",
        ats=None,
        options={},
        notes=(
            "Deliberately not a company. 'Tactical Athlete Program' names a class of "
            "unit-level programs delivered by a rotating set of small contractors, "
            "so there is no single corporate entity and no single careers board to "
            "point an adapter at. Kept as a registry entry because it is a search "
            "term worth carrying and a reminder that this segment exists. Confirm "
            "individual providers as they surface -- discover.py and contracts.py "
            "are the intended way to find them -- then add each as its own entry."
        ),
        aliases=("TAP", "Tactical Athlete Programs"),
    ),
    Employer(
        slug="sparta-science",
        name="Sparta Science",
        category="specialist",
        ats="greenhouse",
        options={"board_token": "PASTE_GREENHOUSE_BOARD_TOKEN_HERE"},
        notes=(
            "Force-plate movement-health company with DoD and special operations "
            "deployments; hires sport scientists and data-facing performance staff. "
            "Greenhouse is a vendor guess typical of a company this size and the "
            "token is unknown. Confirm from the careers page URL."
        ),
        aliases=("Sparta Performance Science",),
    ),
    # -- federal, direct ----------------------------------------------------
    Employer(
        slug="army-h2f",
        name="U.S. Army Holistic Health and Fitness (H2F)",
        category="federal",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "The single largest tactical human performance hiring program in "
            "existence: every H2F-enabled brigade fields strength coaches, athletic "
            "trainers, physical therapists, dietitians, and cognitive performance "
            "specialists, and a share of those billets are government civilian "
            "rather than contractor. The structured USAJOBS API needs a key this "
            "project will not use, so the keyless route is the RSS/export link that "
            "a USAJOBS search offers. Confirm by running the search in a browser "
            "-- keyword 'Holistic Health and Fitness', agency Department of the "
            "Army -- and pasting the export URL over the placeholder."
        ),
        aliases=("H2F", "Holistic Health and Fitness", "Department of the Army", "U.S. Army"),
    ),
    Employer(
        slug="defense-health-agency",
        name="Defense Health Agency",
        category="federal",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "Hires sports medicine, physical therapy, and rehabilitation staff "
            "across the military health system. Same keyless route as the other "
            "federal entries: build the search on USAJOBS and paste its RSS/export "
            "link over the placeholder. Confirm the feed returns recent items "
            "before enabling."
        ),
        aliases=("DHA", "Military Health System"),
    ),
    Employer(
        slug="department-of-veterans-affairs",
        name="Department of Veterans Affairs",
        category="federal",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "Large employer of physical therapists, kinesiotherapists, and whole "
            "health coaches. Lower tactical density than the operational commands, "
            "so expect the classifier to reject much of the volume -- that is the "
            "correct outcome, not a broken source. Confirm the USAJOBS export URL "
            "in a browser before pasting it over the placeholder."
        ),
        aliases=("VA", "Veterans Affairs", "Veterans Health Administration", "VHA"),
    ),
    Employer(
        slug="naval-special-warfare",
        name="Naval Special Warfare Command",
        category="federal",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "Concentrates sports medicine physicians, physical therapists, strength "
            "coaches, dietitians, and cognitive performance specialists under one "
            "command, which makes almost every relevant posting a direct hit. Some "
            "billets are contractor-held and will surface through the primes "
            "instead. Confirm the USAJOBS export URL and paste it over the "
            "placeholder."
        ),
        aliases=("NSW", "WARCOM", "Naval Special Warfare", "NSWC"),
    ),
    Employer(
        slug="usasoc",
        name="U.S. Army Special Operations Command",
        category="federal",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "Runs THOR3, the tactical human optimization program that predates H2F "
            "and set much of its template. Search THOR3 as well as the spelled-out "
            "command name -- postings use both. Confirm the USAJOBS export URL "
            "before pasting it over the placeholder."
        ),
        aliases=("USASOC", "THOR3", "Army Special Operations Command"),
    ),
    Employer(
        slug="afsoc",
        name="Air Force Special Operations Command",
        category="federal",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "Fields human performance teams supporting special tactics and aircrew "
            "populations. Confirm the USAJOBS export URL in a browser and paste it "
            "over the placeholder before enabling."
        ),
        aliases=("AFSOC", "Air Force Special Operations"),
    ),
    Employer(
        slug="marsoc",
        name="Marine Forces Special Operations Command",
        category="federal",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "Fields performance and human optimization staff for Marine Raider "
            "units. Confirm the USAJOBS export URL before pasting it over the "
            "placeholder."
        ),
        aliases=("MARSOC", "Marine Raider Regiment", "MARSOC HP"),
    ),
    Employer(
        slug="socom-potff",
        name="USSOCOM Preservation of the Force and Family",
        category="federal",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "POTFF is the SOCOM-wide human performance and resilience program; much "
            "of its staffing is contractor-held (see the KBR entry) but government "
            "billets also exist. Search 'Preservation of the Force' as well as the "
            "acronym. Confirm the USAJOBS export URL before pasting it over the "
            "placeholder."
        ),
        aliases=("POTFF", "USSOCOM", "SOCOM", "Preservation of the Force and Family"),
    ),
    Employer(
        slug="usmc-human-performance-branch",
        name="USMC Human Performance Branch",
        category="federal",
        ats=None,
        options={},
        notes=(
            "Quantico-based branch publishing through fitness.marines.mil and the "
            "Marine Corps Community Services NAF hiring system rather than through "
            "USAJOBS, which is exactly why it is easy to miss. No adapter fits "
            "until someone identifies the platform. Confirm by opening the MCCS "
            "careers portal and recording which system it runs on; a JobPosting "
            "ld+json block would make jsonld viable."
        ),
        aliases=("Semper Fit", "Marine Corps Human Performance", "MCCS"),
    ),
    # -- state and local: fire, police, EMS ---------------------------------
    Employer(
        slug="los-angeles-fire-department",
        name="Los Angeles Fire Department",
        category="state-local",
        ats="governmentjobs",
        options={"agency": "PASTE_NEOGOV_AGENCY_SLUG_HERE"},
        notes=(
            "Large metropolitan fire departments hire wellness coordinators, peer "
            "fitness trainers, and increasingly embedded athletic trainers, and "
            "they post to NEOGOV rather than to any commercial ATS. The vendor is "
            "near-certain; the agency slug is not. Confirm by finding the "
            "department on governmentjobs.com and taking the slug out of "
            "https://www.governmentjobs.com/careers/<agency>."
        ),
        aliases=("LAFD", "City of Los Angeles Fire"),
    ),
    Employer(
        slug="phoenix-fire-department",
        name="Phoenix Fire Department",
        category="state-local",
        ats="governmentjobs",
        options={"agency": "PASTE_NEOGOV_AGENCY_SLUG_HERE"},
        notes=(
            "Municipal fire department with an established health and wellness "
            "program. NEOGOV is the assumed vendor; the agency slug is unknown. "
            "Confirm from the governmentjobs.com careers URL for the City of "
            "Phoenix."
        ),
        aliases=("City of Phoenix Fire",),
    ),
    Employer(
        slug="texas-dps",
        name="Texas Department of Public Safety",
        category="state-local",
        ats="governmentjobs",
        options={"agency": "PASTE_NEOGOV_AGENCY_SLUG_HERE"},
        notes=(
            "State law enforcement agencies run fitness and wellness programs and "
            "occasionally hire performance staff outright. NEOGOV assumed, slug "
            "unknown. Confirm from the agency's governmentjobs.com URL; note that "
            "some Texas agencies use the state's own portal instead, in which case "
            "switch this entry to jsonld."
        ),
        aliases=("Texas DPS", "TxDPS"),
    ),
    Employer(
        slug="fdny",
        name="Fire Department of the City of New York",
        category="state-local",
        ats=None,
        options={},
        notes=(
            "Included as the counterexample: NYC hires through its own city careers "
            "portal, not NEOGOV, so the obvious governmentjobs guess would have been "
            "wrong and would have failed silently. ats is left None until someone "
            "checks. Confirm by opening the NYC jobs portal and testing a posting "
            "for JobPosting ld+json markup, which would make jsonld the route."
        ),
        aliases=("FDNY", "New York City Fire Department"),
    ),
    # -- association career centres -----------------------------------------
    Employer(
        slug="nsca",
        name="NSCA Career Center",
        category="association",
        ats="jobsrss",
        options={"url": "https://careers.nsca.com/jobs/feed", "employer_from": "title"},
        notes=(
            "Highest signal-per-posting source in this entire niche: nearly every "
            "listing is a strength coach role, and the NSCA's TSAC program means a "
            "meaningful share are explicitly tactical. The feed URL follows the "
            "YourMembership convention and matches the unverified value already in "
            "sources/boards.py -- it is a pattern, not a confirmed endpoint. "
            "Confirm by fetching the URL and checking it returns XML with recent "
            "items rather than an HTML page."
        ),
        aliases=(
            "National Strength and Conditioning Association",
            "NSCA",
            "TSAC",
        ),
    ),
    Employer(
        slug="nata",
        name="NATA Career Center",
        category="association",
        ats="jobsrss",
        options={"url": "https://careers.nata.org/jobs/feed", "employer_from": "title"},
        notes=(
            "Athletic trainer postings, including the military and public safety "
            "placements that are hard to reach any other way. Feed URL follows the "
            "YourMembership convention and is unverified. Confirm it returns XML "
            "with recent items before enabling."
        ),
        aliases=("National Athletic Trainers Association", "NATA"),
    ),
    Employer(
        slug="acsm",
        name="ACSM Career Center",
        category="association",
        ats="jobsrss",
        options={"url": "https://careers.acsm.org/jobs/feed", "employer_from": "title"},
        notes=(
            "Exercise physiology and clinical performance roles. Feed URL is a "
            "convention-based guess. Confirm it returns XML with recent items."
        ),
        aliases=("American College of Sports Medicine", "ACSM"),
    ),
    Employer(
        slug="cscca",
        name="CSCCa Job Board",
        category="association",
        ats="jobsrss",
        options={"url": "https://careers.cscca.org/jobs/feed", "employer_from": "title"},
        notes=(
            "Collegiate strength coaching board; relevant because the collegiate and "
            "tactical talent pools overlap heavily and SCCC-certified coaches move "
            "between them. Feed URL unverified. Confirm it returns XML."
        ),
        aliases=(
            "Collegiate Strength and Conditioning Coaches Association",
            "CSCCa",
            "SCCC",
        ),
    ),
    Employer(
        slug="aasp",
        name="AASP Career Center",
        category="association",
        ats="jobsrss",
        options={
            "url": "https://careers.appliedsportpsych.org/jobs/feed",
            "employer_from": "title",
        },
        notes=(
            "The place cognitive performance specialist roles surface -- a "
            "discipline the defense primes hire for constantly and that no general "
            "job board indexes well. Feed URL unverified. Confirm it returns XML "
            "with recent items."
        ),
        aliases=("Association for Applied Sport Psychology", "AASP"),
    ),
    Employer(
        slug="apta",
        name="APTA Career Center",
        category="association",
        ats="jobsrss",
        options={"url": "https://careers.apta.org/jobs/feed", "employer_from": "title"},
        notes=(
            "Physical therapy postings, including the embedded military and public "
            "safety roles. Feed URL is a convention-based guess. Confirm it returns "
            "XML with recent items."
        ),
        aliases=("American Physical Therapy Association", "APTA"),
    ),
    Employer(
        slug="scan",
        name="SCAN Career Center",
        category="association",
        ats="jobsrss",
        options={"url": "https://careers.scandpg.org/jobs/feed", "employer_from": "title"},
        notes=(
            "Sports and human performance nutrition practice group; the best route "
            "to performance dietitian roles, which the defense primes hire for on "
            "every H2F and POTFF team. Feed URL unverified. Confirm it returns XML."
        ),
        aliases=(
            "Sports and Human Performance Nutrition",
            "SCAN",
            "SCAN Dietetic Practice Group",
        ),
    ),
    # -- academic and research ----------------------------------------------
    Employer(
        slug="usuhs",
        name="Uniformed Services University of the Health Sciences",
        category="academic",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "Home of CHAMP and the Human Performance Resources output that much of "
            "this field cites. Hires researchers and performance staff, mostly "
            "through federal channels. Confirm the USAJOBS export URL in a browser "
            "before pasting it over the placeholder; some USU roles run through "
            "affiliated foundations instead, so check the HJF entry too."
        ),
        aliases=("USU", "USUHS", "CHAMP", "HPRC", "Consortium for Health and Military Performance"),
    ),
    Employer(
        slug="usariem",
        name="U.S. Army Research Institute of Environmental Medicine",
        category="academic",
        ats="rss",
        options={"url": "PASTE_USAJOBS_RSS_URL_HERE"},
        notes=(
            "Produces the physiology research underpinning Army fitness standards "
            "and hires exercise physiologists and research scientists. Federal "
            "hiring, so the same keyless USAJOBS export route applies. Confirm the "
            "URL before pasting it over the placeholder."
        ),
        aliases=("USARIEM", "Army Research Institute of Environmental Medicine"),
    ),
    Employer(
        slug="pitt-nmrl",
        name="University of Pittsburgh Neuromuscular Research Laboratory",
        category="academic",
        ats=None,
        options={},
        notes=(
            "Long-running tactical research partnerships with special operations "
            "units; hires research staff and embedded performance personnel. "
            "University hiring runs through Pitt's own Talent Center, which is not "
            "one of this project's adapters, so ats stays None. Confirm by checking "
            "whether Pitt job pages carry JobPosting ld+json markup -- if they do, "
            "jsonld with a url_include filter is the route."
        ),
        aliases=("NMRL", "Pitt NMRL", "Neuromuscular Research Laboratory"),
    ),
    # -- nonprofit and research foundations ---------------------------------
    Employer(
        slug="geneva-foundation",
        name="The Geneva Foundation",
        category="nonprofit",
        ats=None,
        options={},
        notes=(
            "Team Serco subcontractor on the Army H2F award and a long-running "
            "military medical research nonprofit that places research and clinical "
            "staff at military treatment facilities. ATS not identified and not "
            "guessed. Confirm by opening the foundation's careers page and noting "
            "the platform."
        ),
        aliases=("Geneva Foundation", "Geneva USA"),
    ),
    Employer(
        slug="henry-jackson-foundation",
        name="Henry M. Jackson Foundation for the Advancement of Military Medicine",
        category="nonprofit",
        ats="jsonld",
        options={
            "sitemap": "PASTE_HJF_CAREERS_SITEMAP_URL_HERE",
            "url_include": ["/job", "/careers/"],
            "max_urls": 300,
        },
        notes=(
            "Staffs a large share of military medical research, including human "
            "performance work at USU and at military treatment facilities, and "
            "posts athletic trainer and exercise physiologist roles that never "
            "reach USAJOBS. Careers site is unconfirmed and likely iCIMS, so jsonld "
            "is the assumed route. Confirm by checking a job detail page for "
            "JobPosting ld+json markup, then supply the sitemap URL."
        ),
        aliases=("HJF", "Henry Jackson Foundation"),
    ),
)


# ---------------------------------------------------------------------------
# lookup
# ---------------------------------------------------------------------------


def _build_index() -> dict[str, Employer]:
    """Map every recognizable spelling to its employer.

    Strict keys are inserted before loose ones so an exact name always beats a
    suffix-stripped near-match, and the first entry to claim a key keeps it --
    registry order is the tie-breaker, which keeps lookups deterministic
    regardless of how the table grows.
    """
    index: dict[str, Employer] = {}
    for employer in REGISTRY:
        for key in employer.search_keys():
            index.setdefault(_normalize(key), employer)
    for employer in REGISTRY:
        for key in employer.search_keys():
            loose = _loose(key)
            if loose:
                index.setdefault(loose, employer)
    return index


_INDEX: dict[str, Employer] = _build_index()


def all_employers() -> tuple[Employer, ...]:
    """Every registry entry, in curated order."""
    return REGISTRY


def by_category(category: str) -> tuple[Employer, ...]:
    """Entries in one category. An unknown category yields an empty tuple."""
    wanted = category.strip().lower()
    return tuple(e for e in REGISTRY if e.category == wanted)


def by_slug(slug: str) -> Employer | None:
    """Exact slug lookup."""
    target = slug.strip().lower()
    return next((e for e in REGISTRY if e.slug == target), None)


def match_employer(name: str) -> Employer | None:
    """Find an employer by any spelling of its name.

    Deliberately fuzzy but not *guessy*. Case, punctuation, ``&`` vs ``and``,
    a leading article, and a trailing legal suffix are all noise -- job postings
    spell the same organization four different ways across four boards, and a
    lookup that fails on "Booz Allen Hamilton, Inc." is useless for reconciling
    a scraped ``employer`` field back to this registry.

    What it will *not* do is substring or prefix matching. "Army" must not
    resolve to "U.S. Army Holistic Health and Fitness", because a wrong match
    here attributes a posting to the wrong organization, which is worse than no
    match at all.
    """
    if not name or not name.strip():
        return None
    found = _INDEX.get(_normalize(name))
    if found is not None:
        return found
    loose = _loose(name)
    return _INDEX.get(loose) if loose else None


def verified_count() -> tuple[int, int]:
    """``(verified, total)``.

    Exists so the number is impossible to avoid looking at. Today the verified
    side is zero, and that ratio is the honest state of this file.
    """
    return sum(1 for e in REGISTRY if e.verified), len(REGISTRY)


def used_kinds() -> tuple[str, ...]:
    """Every adapter kind the registry actually points at, sorted."""
    return tuple(sorted({e.ats for e in REGISTRY if e.ats is not None}))


# ---------------------------------------------------------------------------
# TOML rendering
# ---------------------------------------------------------------------------

_HEADER = """\
# =============================================================================
# TACTICAL HUMAN PERFORMANCE EMPLOYER REGISTRY
# Generated by tactical_jobs.registry.to_toml() -- do not hand-edit in place;
# edit tactical_jobs/registry.py and regenerate.
#
# !! EVERY UNVERIFIED ENTRY BELOW IS COMMENTED OUT ON PURPOSE !!
#
# None of these board tokens, tenants, agency slugs, or feed URLs has been
# confirmed against a live endpoint. They are researched guesses. A wrong token
# does not raise -- it returns an empty list forever, which is indistinguishable
# from "this employer is not hiring". So nothing goes live until a human has
# looked at an actual response.
#
# TO ENABLE ONE ENTRY
#   1. Run the check printed above its block.
#   2. Replace any PASTE_... placeholder with the real value.
#   3. Uncomment the block.
#   4. Re-run with --dry-run and confirm a non-zero count in the summary.
#
# The generic checks:
#   curl -s "https://boards-api.greenhouse.io/v1/boards/<token>/jobs" | head -c 300
#   curl -s "https://api.lever.co/v0/postings/<token>?mode=json"      | head -c 300
#   Workday: read tenant/data_center/site out of
#            https://{tenant}.{data_center}.myworkdayjobs.com/{site}
#   NEOGOV:  read the slug out of
#            https://www.governmentjobs.com/careers/<agency>
# =============================================================================
"""


def _toml_value(value: Any) -> str:
    """Render a Python value as a TOML scalar or array.

    ``bool`` is checked before ``int`` because ``True`` is an ``int`` in Python
    and would otherwise render as ``1``, which TOML reads back as a number.
    """
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    text = (
        str(value)
        .replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\t", "\\t")
    )
    return f'"{text}"'


def _comment_lines(text: str, *, width: int = 74) -> Iterator[str]:
    for paragraph in text.split("\n"):
        wrapped = textwrap.wrap(paragraph.strip(), width=width) or [""]
        for line in wrapped:
            yield f"# {line}".rstrip()


def _render(employer: Employer) -> list[str]:
    """One employer as TOML lines, commented out unless verified."""
    status = "VERIFIED" if employer.verified else "UNVERIFIED -- confirm before enabling"
    lines = [f"# {employer.name}  [{employer.category}]  {status}"]

    if employer.aliases:
        lines.extend(_comment_lines(f"also known as: {', '.join(employer.aliases)}"))
    if employer.notes:
        lines.extend(_comment_lines(employer.notes))
    lines.extend(_comment_lines(f"check: {verification_hint(employer.ats)}"))

    if employer.ats is None:
        lines.extend(
            _comment_lines(
                "NO SOURCE BLOCK: the careers platform for this organization has "
                "not been identified, so there is nothing to paste yet."
            )
        )
        return lines

    missing = placeholder_options(employer)
    if missing:
        lines.extend(
            _comment_lines(f"FILL IN before enabling: {', '.join(missing)}")
        )

    config = employer.to_source_config()
    body = ["[[source]]"]
    body.append(f"kind = {_toml_value(config['kind'])}")
    body.append(f"name = {_toml_value(config['name'])}")
    body.extend(
        f"{key} = {_toml_value(value)}"
        for key, value in config.items()
        if key not in ("kind", "name")
    )

    prefix = "" if employer.verified else "# "
    lines.extend(prefix + line for line in body)
    return lines


def to_toml(employers: Sequence[Employer], *, include_unverified: bool = True) -> str:
    """Render employers as a pasteable ``sources.toml`` fragment.

    Unverified entries are emitted **commented out**. That is the whole point:
    the output is a worksheet, not configuration, and a careless copy-paste of
    the whole file must not silently enable fifty guessed tokens at once.

    Pass ``include_unverified=False`` to emit only entries somebody has actually
    confirmed. Today that produces a header and nothing else, which is the
    correct and useful answer -- it makes the verification debt impossible to
    overlook.
    """
    selected = [e for e in employers if include_unverified or e.verified]
    lines = [_HEADER.rstrip("\n"), ""]

    if not selected:
        lines.extend(
            _comment_lines(
                "Nothing to emit: no employer in this selection has been verified "
                "against a live endpoint yet. Confirm one, set verified=True on its "
                "registry entry, and it will appear here as live configuration."
            )
        )
        return "\n".join(lines) + "\n"

    current_category: str | None = None
    for employer in selected:
        if employer.category != current_category:
            current_category = employer.category
            lines.extend(
                [
                    "",
                    "# " + "-" * 74,
                    f"# {current_category.upper()}",
                    "# " + "-" * 74,
                ]
            )
        lines.append("")
        lines.extend(_render(employer))

    verified, total = verified_count()
    lines.extend(
        [
            "",
            "# " + "-" * 74,
            f"# {len(selected)} entr{'y' if len(selected) == 1 else 'ies'} rendered. "
            f"Registry-wide: {verified} of {total} verified.",
            "# " + "-" * 74,
        ]
    )
    return "\n".join(lines) + "\n"
