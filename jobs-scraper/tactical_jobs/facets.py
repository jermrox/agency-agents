"""Filter facets: discipline, location class, contingency, salary floor.

Every function returns an explicit unknown rather than a guess, and the board
treats unknown as "always show" -- a filtered-out posting is invisible, so a
wrong guess costs more than an admitted gap.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from .models import JobPosting


@dataclass(frozen=True, slots=True)
class Discipline:
    slug: str
    label: str
    patterns: tuple[re.Pattern[str], ...]


def _rx(*sources: str) -> tuple[re.Pattern[str], ...]:
    return tuple(re.compile(s, re.I) for s in sources)


# First match wins, so specific disciplines come before "human-performance",
# which is the generalist catch-all and appears in nearly every title here.
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
            r"\bR2PC\b",  # Army Ready and Resilient Performance Center
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
    Discipline(
        "human-performance",
        "Human Performance (generalist)",
        _rx(
            r"\bhuman\s+performance\b", r"\bperformance\s+specialist\b",
            r"\bperformance\s+coach\b", r"\bHPO\b", r"\bH2F\b",
            r"\bperformance\s+expert\b", r"\bperformance\s+advisor\b",
        ),
    ),
)

_DISCIPLINE_BY_SLUG = {d.slug: d for d in DISCIPLINES}

_LEAD_RE = re.compile(
    r"\b(?:lead|senior|sr\.?|principal|head|chief|director|manager|supervisor|"
    r"coordinator|program\s+manager|installation\s+lead)\b",
    re.I,
)


def discipline_of(title: str, description: str = "") -> str:
    """Title decides; description is a fallback read only to its first 400 chars."""
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


# DoD definition: CONUS is the 48 contiguous states + DC. AK, HI, and the
# territories are OCONUS.
_CONUS_STATES = (
    "AL AR AZ CA CO CT DC DE FL GA IA ID IL IN KS KY LA MA MD ME MI MN MO MS "
    "MT NC ND NE NH NJ NM NV NY OH OK OR PA RI SC SD TN TX UT VA VT WA WI WV WY"
).split()

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

# Bare ISO-2 codes in a delimited list ("JP; IT; DE; KY, US"). DE collides
# with Delaware; a US state code is always written "DE, US" so the negative
# lookahead resolves it.
_OCONUS_COUNTRY_CODE_RE = re.compile(
    r"(?:^|[;,]\s*|\s)"
    r"(?:JP|KR|DE|IT|GB|ES|PT|BE|NL|PL|RO|BG|GR|TR|NO|QA|KW|BH|AE|SA|JO|IQ|"
    r"AF|DJ|KE|AU|NZ|PH|TH|SG|CO|HN|PA)"
    r"(?!\s*,\s*(?:US|USA)\b)(?![A-Za-z])"
)

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
    """Any of ``remote`` / ``conus`` / ``oconus``. Empty means unknown."""
    found: set[str] = set()
    text = location or ""

    if remote_flag or (_REMOTE_RE.search(text) and not _REMOTE_VETO_RE.search(text)):
        found.add("remote")
    if _OCONUS_RE.search(text) or _OCONUS_COUNTRY_CODE_RE.search(text):
        found.add("oconus")
    if _CONUS_STATE_RE.search(text) or _CONUS_STATE_NAMES_RE.search(text):
        found.add("conus")
    return frozenset(found)


_CONTINGENT_WINDOW = 80

_AWARD_CONTEXT_RE = re.compile(
    r"\b(?:award|contract|task\s+order|re-?compete|recompete|proposal|bid|"
    r"funding|funded|solicitation|\bRFP\b|capture|win|program\s+start|"
    r"vacancy|headcount|position\s+availability|billet)\b",
    re.I,
)

_ONBOARDING_CONTEXT_RE = re.compile(
    r"\b(?:background|drug|screen|physical\s+exam|reference|E-?Verify|I-?9|"
    r"credential|licensure|fingerprint|medical\s+exam|security\s+clearance\s+"
    r"adjudicat|successful\s+completion)\b",
    re.I,
)

_CONTINGENT_WORD_RE = re.compile(r"\bcontingen(?:t|cy)\b", re.I)

# "Contingent posting" needs no award vocabulary nearby to be conclusive --
# it's a term of art. Distinguishes from "contingent upon a background check".
_CONTINGENT_NOUN_RE = re.compile(
    r"\bcontingen(?:t|cy)\s+"
    r"(?:posting|position|role|opening|requisition|opportunit|vacanc|job|"
    r"listing|hire|hiring|billet|seat|award)",
    re.I,
)

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

_FUNDED_RE = re.compile(
    r"\b(?:currently\s+funded|fully\s+funded|funded\s+(?:position|requisition|"
    r"seat|billet)|immediate\s+(?:fill|hire|opening|need)|position\s+is\s+"
    r"(?:open|active)|active\s+contract|awarded\s+contract|contract\s+has\s+"
    r"been\s+awarded)\b",
    re.I,
)


def contingency_of(*texts: str) -> str:
    """``"contingent"``, ``"funded"``, or ``"unknown"``. Contingent wins ties."""
    blob = "\n".join(t for t in texts if t)
    if not blob:
        return "unknown"

    if _PIPELINE_RE.search(blob) or _CONTINGENT_NOUN_RE.search(blob):
        return "contingent"

    for match in _CONTINGENT_WORD_RE.finditer(blob):
        window = blob[match.end() : match.end() + _CONTINGENT_WINDOW]
        if _ONBOARDING_CONTEXT_RE.search(window):
            continue
        if _AWARD_CONTEXT_RE.search(window):
            return "contingent"

    if _FUNDED_RE.search(blob):
        return "funded"
    return "unknown"


_HOURS_PER_YEAR = 2080


def salary_floor_annual(enrichment: dict[str, Any]) -> float | None:
    """Reads enrich.py's flat salary keys; hourly annualized at 2080h."""
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
