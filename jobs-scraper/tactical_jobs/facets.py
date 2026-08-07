"""Filter facets: the handful of questions a candidate actually asks.

``classify.py`` answers "does this belong on the board at all". This module
answers the next four questions, which are the ones a person standing in front
of the board wants filtered:

    1. Is this my job?        -> discipline
    2. Can I live there?      -> location class (remote / CONUS / OCONUS)
    3. Is the job real?       -> contingency
    4. Does it pay enough?    -> salary floor

Each is deliberately conservative. A facet that guesses wrong is worse than a
facet that returns "unknown", because a wrong guess *hides* a job from the one
person who wanted it -- a filtered-out posting is invisible, and the candidate
never learns they were filtered. So every function here returns an explicit
unknown rather than a plausible default, and the board treats unknown as
"always show".
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import JobPosting

# ---------------------------------------------------------------------------
# 1. DISCIPLINE
#
# The primary filter. A physical therapist does not care what strength coach
# jobs exist, so this must be a clean partition rather than a tag cloud.
#
# Two rules make it a partition instead of a mess:
#
#   * The TITLE decides. Descriptions on these contracts list every discipline
#     on the embedded team ("works alongside the ATC, RD, and CPS..."), so
#     scoring a description hands every job every label. The description is
#     consulted only when the title is silent.
#   * Seniority is NOT a discipline. "Installation Lead Strength & Conditioning
#     Coach" is a strength job that happens to be a lead role. Filing it under
#     "leadership" would hide it from every strength coach browsing the board,
#     which is exactly the failure this module exists to avoid. Lead-ness is a
#     separate boolean.
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class Discipline:
    slug: str
    label: str
    patterns: tuple[re.Pattern[str], ...]


def _rx(*sources: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(s, re.I) for s in sources)


# Order is significant: the first match wins, so the most specific and least
# ambiguous disciplines come first. "human-performance" is deliberately LAST
# because "human performance" appears in the title of nearly every job on this
# board -- it is the catch-all for genuine generalist roles only.
DISCIPLINES: tuple[Discipline, ...] = (
    Discipline(
        "cognitive-performance",
        "Cognitive Performance",
        _rx(
            r"\bcognitive\s+performance\b",
            r"\bmental\s+performance\b",
            r"\bperformance\s+psycholog",
            r"\bsport\s+psycholog",
            r"\bCPS\b",
            # R2PC is the Army's Ready and Resilient Performance Center, whose
            # "Performance Experts" deliver mental-skills training. The program
            # name is unambiguous; the bare job title is not, so only the
            # program acronym routes here.
            r"\bR2PC\b",
            r"\bmaster\s+resilience\s+trainer\b",
        ),
    ),
    Discipline(
        "behavioral-health",
        "Behavioral Health",
        _rx(
            r"\blicensed\s+clinical\s+social\s+worker\b",
            r"(?<![A-Za-z])LCSW(?![A-Za-z])",
            r"\bbehavioral\s+health\b",
            r"\bclinical\s+psycholog",
            r"\bmental\s+health\s+(?:counselor|clinician|provider)\b",
            r"\bsubstance\s+abuse\s+counselor\b",
        ),
    ),
    Discipline(
        "nutrition",
        "Performance Nutrition",
        _rx(
            r"\bdietit", r"\bdietic", r"\bnutrition",
            # "RD" and "RDN" only as standalone credentials, never inside a word.
            r"(?<![A-Za-z])RDN?(?![A-Za-z])",
        ),
    ),
    Discipline(
        "physical-therapy",
        "Physical Therapy",
        _rx(
            r"\bphysical\s+therap", r"\bphysiotherap",
            r"(?<![A-Za-z])DPT(?![A-Za-z])",
            r"\bPT\s*/\s*", r"\brehabilitation\s+specialist\b",
        ),
    ),
    Discipline(
        "occupational-therapy",
        "Occupational Therapy",
        _rx(r"\boccupational\s+therap", r"(?<![A-Za-z])OTR?/?L?(?![A-Za-z])"),
    ),
    Discipline(
        "athletic-training",
        "Athletic Training",
        _rx(
            r"\bathletic\s+train",
            # ATC as a credential. Excluded when it is part of a longer token
            # so "MATCH" or "PATCH" in a title cannot trigger it.
            r"(?<![A-Za-z])ATC(?![A-Za-z])",
        ),
    ),
    Discipline(
        "strength-conditioning",
        "Strength & Conditioning",
        _rx(
            r"\bstrength\s*(?:and|&)\s*conditioning\b",
            r"\bstrength\s+coach\b",
            r"\bconditioning\s+coach\b",
            r"(?<![A-Za-z])CSCS(?![A-Za-z])",
            r"(?<![A-Za-z])TSAC(?:-F)?(?![A-Za-z])",
            r"\bS\s*&\s*C\b",
        ),
    ),
    Discipline(
        "sport-science",
        "Sport Science",
        _rx(
            r"\bsports?\s+scien", r"\bbiomechan", r"\bexercise\s+physiolog",
            r"\bphysiologist\b", r"\bperformance\s+analyst\b",
            r"\bkinesiolog", r"\bdata\s+scientist\b",
        ),
    ),
    # The generalist bucket. On these contracts "Human Performance Advisor" is
    # a real, distinct senior role -- one person holding any of ATC/CSCS/PT/
    # CPS/RD who runs the embedded team -- not a vague title, so it earns its
    # own filter rather than being dumped into "other".
    Discipline(
        "human-performance",
        "Human Performance (generalist)",
        _rx(
            r"\bhuman\s+performance\b", r"\bperformance\s+specialist\b",
            r"\bperformance\s+coach\b", r"\bHPO\b", r"\bH2F\b",
            # "Performance Expert" without a program acronym is genuinely
            # generic, so it lands in the generalist bucket rather than being
            # guessed into a specialty a candidate is filtering on.
            r"\bperformance\s+expert\b", r"\bperformance\s+advisor\b",
        ),
    ),
)

_DISCIPLINE_BY_SLUG = {d.slug: d for d in DISCIPLINES}

# Seniority markers. Kept separate from discipline on purpose -- see above.
_LEAD_RE = re.compile(
    r"\b(?:lead|senior|sr\.?|principal|head|chief|director|manager|supervisor|"
    r"coordinator|program\s+manager|installation\s+lead)\b",
    re.I,
)


def discipline_of(title: str, description: str = "") -> str:
    """Return the discipline slug for a posting, or ``"other"``.

    The title is authoritative. The description is a fallback that only runs
    when no discipline appears in the title at all, and even then it reads
    only the first 400 characters -- far enough in to catch a role summary,
    not far enough to reach the "you will work alongside our RD, ATC and CPS"
    paragraph that would otherwise match everything.
    """
    for discipline in DISCIPLINES:
        if any(p.search(title) for p in discipline.patterns):
            return discipline.slug
    head = description[:400]
    if head:
        for discipline in DISCIPLINES:
            if any(p.search(head) for p in discipline.patterns):
                return discipline.slug
    return "other"


def discipline_label(slug: str) -> str:
    d = _DISCIPLINE_BY_SLUG.get(slug)
    return d.label if d else "Other"


def is_lead(title: str) -> bool:
    return bool(_LEAD_RE.search(title))


# ---------------------------------------------------------------------------
# 2. LOCATION CLASS
#
# CONUS / OCONUS use the DoD definition, not the colloquial one: CONUS is the
# 48 contiguous states plus DC. Alaska, Hawaii, and the territories are OCONUS.
# That surprises people who read "continental US" as "the whole country", so
# the board states the definition next to the filter rather than assuming it.
#
# Returns a SET, because these postings routinely span several installations
# ("Fort Bragg NC / Kadena AB Japan") and collapsing that to one value would
# hide the job from half the people it applies to.
# ---------------------------------------------------------------------------

_CONUS_STATES = (
    "AL AR AZ CA CO CT DC DE FL GA IA ID IL IN KS KY LA MA MD ME MI MN MO MS "
    "MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY"
).split()

# Anchored on a delimiter OR the start of the string: a semicolon-delimited
# list can open with a bare state code ("DE, US; KY, US"), and requiring
# preceding whitespace silently dropped the first entry.
_CONUS_STATE_RE = re.compile(
    r"(?:^|[;,]\s*|\s)(?:" + "|".join(_CONUS_STATES) + r")(?![A-Za-z])"
)

_CONUS_STATE_NAMES_RE = re.compile(
    r"\b(?:alabama|arizona|arkansas|california|colorado|connecticut|delaware|"
    r"florida|georgia|idaho|illinois|indiana|iowa|kansas|kentucky|louisiana|"
    r"maine|maryland|massachusetts|michigan|minnesota|mississippi|missouri|"
    r"montana|nebraska|nevada|new\s+hampshire|new\s+jersey|new\s+mexico|"
    r"new\s+york|north\s+carolina|north\s+dakota|ohio|oklahoma|oregon|"
    r"pennsylvania|rhode\s+island|south\s+carolina|south\s+dakota|tennessee|"
    r"texas|utah|vermont|virginia|washington|west\s+virginia|wisconsin|"
    r"wyoming|district\s+of\s+columbia|\bCONUS\b)\b",
    re.I,
)

# Overseas. Country and territory names, the overseas-base vocabulary these
# contracts actually use, and the military mail prefixes.
_OCONUS_RE = re.compile(
    r"\b(?:OCONUS|overseas|"
    r"germany|deutschland|italy|italia|spain|portugal|belgium|netherlands|"
    r"poland|romania|bulgaria|hungary|greece|turkey|t(?:ü|u)rkiye|norway|"
    r"united\s+kingdom|england|scotland|wales|northern\s+ireland|\bUK\b|"
    r"japan|okinawa|korea|republic\s+of\s+korea|\bROK\b|philippines|thailand|"
    r"singapore|australia|new\s+zealand|"
    r"kuwait|qatar|bahrain|\bUAE\b|united\s+arab\s+emirates|saudi|jordan|"
    r"iraq|afghanistan|djibouti|kenya|somalia|"
    r"colombia|honduras|panama|"
    r"guam|puerto\s+rico|virgin\s+islands|american\s+samoa|"
    r"alaska|hawaii|"
    r"\bRAF\s+\w+|\bAPO\b|\bFPO\b|\bAE\b\s*\d|"
    r"kadena|yokota|misawa|camp\s+humphreys|osan|"
    r"ramstein|grafenwoehr|grafenw(?:ö|o)hr|vilseck|baumholder|stuttgart|"
    r"wiesbaden|vicenza|aviano|sigonella|rota|lakenheath|mildenhall|"
    r"landstuhl|ansbach|hohenfels|panzer\s+kaserne|"
    r"(?:,\s*|\s)(?:AK|HI|GU|PR|VI|AS|MP)(?![A-Za-z])"
    r")",
    re.I,
)

# Some boards list multi-country roles as bare ISO-2 codes in a delimited list
# -- the NSCA board publishes the Serco H2FIT role as
# "JP; IT; DE; KY, US; AZ, US; ... HI, US". Without this, the overseas half of
# that posting is invisible to an OCONUS filter.
#
# Exactly one code is ambiguous: DE is both Germany and Delaware. The list
# format distinguishes them itself -- a US state is always written "DE, US" --
# so the lookahead requires the code NOT be followed by a US marker. Every
# other code here collides with no US state abbreviation.
_OCONUS_COUNTRY_CODE_RE = re.compile(
    r"(?:^|[;,]\s*|\s)"
    r"(?:JP|KR|DE|IT|GB|ES|PT|BE|NL|PL|RO|BG|GR|TR|NO|QA|KW|BH|AE|SA|JO|IQ|"
    r"AF|DJ|KE|AU|NZ|PH|TH|SG|CO|HN|PA)"
    r"(?!\s*,\s*(?:US|USA)\b)(?![A-Za-z])"
)

# Genuinely location-independent work. "Various (travel)" and "placement
# determined after hire" are NOT remote -- they are unknown-location on-site
# work, and calling them remote would put a traveling workshop instructor in
# front of someone who needs to work from home.
_REMOTE_RE = re.compile(
    r"\b(?:remote|work\s+from\s+home|telework|telecommut|virtual|anywhere)\b",
    re.I,
)
_REMOTE_VETO_RE = re.compile(
    r"\b(?:not\s+remote|no\s+remote|remote\s+work\s+is\s+not|non-remote|"
    r"cannot\s+be\s+performed\s+remotely)\b",
    re.I,
)


def location_classes(location: str, remote_flag: bool = False) -> frozenset[str]:
    """Classify a location string into any of ``remote`` / ``conus`` / ``oconus``.

    An empty set means "could not tell" and the board shows the job under
    every location filter rather than none.
    """
    found: set[str] = set()
    text = location or ""

    if remote_flag or (_REMOTE_RE.search(text) and not _REMOTE_VETO_RE.search(text)):
        found.add("remote")
    if _OCONUS_RE.search(text) or _OCONUS_COUNTRY_CODE_RE.search(text):
        found.add("oconus")
    # A two-letter state code check runs against the raw string, but only after
    # OCONUS has had its say: "Kadena AB, Okinawa, Japan" must not be read as
    # CONUS because some substring looked like a state abbreviation.
    if _CONUS_STATE_RE.search(text) or _CONUS_STATE_NAMES_RE.search(text):
        found.add("conus")
    return frozenset(found)


# ---------------------------------------------------------------------------
# 3. CONTINGENCY
#
# The one that actually costs candidates something. A "contingent" posting is
# a resume collector: the employer has bid on a contract and is building a
# pipeline in case they win it. People apply, interview, and then hear nothing
# for a year -- so this gets its own filter and its own badge.
#
# The hard part is that the word "contingent" appears in near-universal offer
# boilerplate ("employment is contingent upon a background check"). Matching
# the bare word would flag essentially every posting in the corpus. So the
# match is a two-part test: the word, plus what follows it within a short
# window.
# ---------------------------------------------------------------------------

_CONTINGENT_WINDOW = 80

# What makes a contingency real: it hangs on winning work, not on onboarding.
_AWARD_CONTEXT_RE = re.compile(
    r"\b(?:award|contract|task\s+order|re-?compete|recompete|proposal|bid|"
    r"funding|funded|solicitation|\bRFP\b|capture|win|program\s+start|"
    # "This position is contingent upon a vacancy at this location" -- KBR's
    # wording on R2PC reqs. The seat may not exist, which is the same problem
    # for a candidate as an unawarded contract even though no contract is
    # mentioned. Found by reading live postings, not by imagining phrasings.
    r"vacancy|headcount|position\s+availability|billet)\b",
    re.I,
)

# Ordinary pre-employment conditions. These are NOT contingent postings.
_ONBOARDING_CONTEXT_RE = re.compile(
    r"\b(?:background|drug|screen|physical\s+exam|reference|E-?Verify|I-?9|"
    r"credential|licensure|fingerprint|medical\s+exam|security\s+clearance\s+"
    r"adjudicat|successful\s+completion)\b",
    re.I,
)

_CONTINGENT_WORD_RE = re.compile(r"\bcontingen(?:t|cy)\b", re.I)

# "Contingent" attached directly to a noun for the listing itself -- "this is a
# contingent posting", "contingency hire". In government contracting that is a
# term of art meaning the seat depends on winning the work, and it needs no
# further context to be conclusive.
#
# This is the distinction that makes the whole filter work. Boilerplate always
# takes the form "contingent UPON <onboarding step>"; a real contract
# contingency describes the listing itself. Requiring award vocabulary in both
# cases silently let the three GDIT roles through as "unknown" even though
# their postings say "Contingent posting" in as many words.
_CONTINGENT_NOUN_RE = re.compile(
    r"\bcontingen(?:t|cy)\s+"
    r"(?:posting|position|role|opening|requisition|opportunit|vacanc|job|"
    r"listing|hire|hiring|billet|seat|award)",
    re.I,
)

# Phrases that mean the same thing without using the word at all.
_PIPELINE_RE = re.compile(
    r"\b(?:talent\s+(?:pool|pipeline|community)|resume\s+(?:pool|bank)|"
    r"pipeline\s+requisition|future\s+(?:opening|opportunit|consideration)|"
    r"anticipated\s+(?:opening|award|need|requirement)|"
    r"pending\s+(?:contract\s+)?award|"
    r"proposal\s+(?:effort|pending)|not\s+yet\s+awarded|"
    r"should\s+we\s+be\s+awarded|if\s+awarded|upon\s+award|"
    r"pre-?award|expression\s+of\s+interest)\b",
    re.I,
)

# Explicit reassurance that the seat exists and is paid for.
_FUNDED_RE = re.compile(
    r"\b(?:currently\s+funded|fully\s+funded|funded\s+(?:position|requisition|"
    r"seat|billet)|immediate\s+(?:fill|hire|opening|need)|position\s+is\s+"
    r"(?:open|active)|active\s+contract|awarded\s+contract|contract\s+has\s+"
    r"been\s+awarded)\b",
    re.I,
)


def contingency_of(*texts: str) -> str:
    """``"contingent"``, ``"funded"``, or ``"unknown"``.

    ``contingent`` wins ties: telling someone a resume-collector might be real
    is a smaller harm than telling them a real job might be a resume-collector.
    """
    blob = "\n".join(t for t in texts if t)
    if not blob:
        return "unknown"

    if _PIPELINE_RE.search(blob) or _CONTINGENT_NOUN_RE.search(blob):
        return "contingent"

    for match in _CONTINGENT_WORD_RE.finditer(blob):
        window = blob[match.end() : match.end() + _CONTINGENT_WINDOW]
        if _ONBOARDING_CONTEXT_RE.search(window):
            continue  # "contingent upon a background check" -- boilerplate.
        if _AWARD_CONTEXT_RE.search(window):
            return "contingent"
        # A bare "contingent" with neither context is genuinely ambiguous.
        # Falling through to unknown keeps it visible.

    if _FUNDED_RE.search(blob):
        return "funded"
    return "unknown"


# ---------------------------------------------------------------------------
# 4. SALARY FLOOR
#
# Only ever read from enrich.py, never re-parsed here. That parser already
# carries the veto rules that stop "Travel: 10-15%" becoming "$10-$15/hr" and
# stop a 401(k) match becoming a salary, and duplicating a weaker version of
# it here is how the board ends up publishing two different numbers for the
# same job.
# ---------------------------------------------------------------------------

_HOURS_PER_YEAR = 2080  # 40h x 52w, the federal full-time convention.


def salary_floor_annual(enrichment: dict[str, Any]) -> float | None:
    """Lowest advertised annual figure, or ``None`` if nothing was extracted.

    Reads the flat ``salary_min`` / ``salary_max`` / ``salary_period`` keys that
    :func:`enrich.enrich` writes. Hourly rates are annualized so a single
    numeric filter can span both; any other period (weekly, daily, per-diem)
    returns ``None`` rather than being converted on an assumed schedule.
    """
    data = enrichment or {}
    low = data.get("salary_min")
    if not isinstance(low, (int, float)):
        low = data.get("salary_max")
    if not isinstance(low, (int, float)) or isinstance(low, bool):
        return None
    period = str(data.get("salary_period") or "").lower()
    if period.startswith("hour"):
        return float(low) * _HOURS_PER_YEAR
    if period.startswith(("year", "annual")):
        return float(low)
    return None


# ---------------------------------------------------------------------------
# Assembly
# ---------------------------------------------------------------------------


def facets_for(posting: JobPosting) -> dict[str, Any]:
    """Every facet for one posting, in the shape the feed publishes."""
    slug = discipline_of(posting.title, posting.description)
    return {
        "discipline": slug,
        "discipline_label": discipline_label(slug),
        "lead": is_lead(posting.title),
        "location_classes": sorted(
            location_classes(posting.location, posting.remote)
        ),
        "contingency": contingency_of(
            posting.title, posting.description, posting.compensation or ""
        ),
        "salary_floor_annual": salary_floor_annual(posting.enrichment),
    }
