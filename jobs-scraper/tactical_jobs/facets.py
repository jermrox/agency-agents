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
    # Country NAMES are only safe here when they are not also American place
    # names, which rules out most of Latin America: Peru, Lima, Panama City and
    # Cairo are all US towns. Only distinctive or multi-word ones go in.
    # "panama" needs the guard because Panama City and Panama City Beach are
    # both in Florida, and one of them is on this board.
    r"colombia|honduras|el\s+salvador|guatemala|costa\s+rica|belize|"
    r"panama(?!\s+city)|"
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

# Bare country codes in a delimited list ("JP; IT; DE; KY, US"). DE collides
# with Delaware; a US state code is always written "DE, US" so the negative
# lookahead resolves it.
#
# Both ISO-2 and ISO-3 are needed. Workday tenants write ISO-3: GDIT's Korea
# postings arrive as "Camp Casey, KOR", which matched nothing here and left
# the posting unclassified -- and an unclassified location used to show under
# every location chip, including Remote. No ISO-3 code below collides with a
# US state abbreviation, so no lookahead is needed for them.
_OCONUS_COUNTRY_CODE_RE = re.compile(
    r"(?:^|[;,]\s*|\s)"
    r"(?:JP|KR|DE|IT|GB|ES|PT|BE|NL|PL|RO|BG|GR|TR|NO|QA|KW|BH|AE|SA|JO|IQ|"
    r"AF|DJ|KE|AU|NZ|PH|TH|SG|HN)"
    r"(?!\s*,\s*(?:US|USA)\b)(?![A-Za-z])"
)
# CO (Colombia) and PA (Panama) are deliberately absent above. Both are US
# state abbreviations first -- "Colorado Springs, CO" and "Indiana, PA" were
# being published as OCONUS -- and the ", US" lookahead does not save them,
# because a bare "City, ST" string is how nearly every US location on this
# board is written. Colombia and Panama are reached by name instead. DE stays
# only because Delaware is always written "DE, US" in the one feed that uses
# the delimited form.

_OCONUS_COUNTRY_CODE3_RE = re.compile(
    r"(?:^|[;,]\s*|\s)"
    r"(?:JPN|KOR|DEU|ITA|GBR|ESP|PRT|BEL|NLD|POL|ROU|BGR|GRC|TUR|NOR|QAT|"
    r"KWT|BHR|ARE|SAU|JOR|IRQ|AFG|DJI|KEN|AUS|NZL|PHL|THA|SGP|COL|HND|PAN|"
    r"SLV|GTM|CRI|PER|CHL|BRA|ARG|EGY|ISR|OMN|CYP|GRL|ISL)"
    r"(?![A-Za-z])"
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
    if (
        _OCONUS_RE.search(text)
        or _OCONUS_COUNTRY_CODE_RE.search(text)
        or _OCONUS_COUNTRY_CODE3_RE.search(text)
    ):
        found.add("oconus")
    if _CONUS_STATE_RE.search(text) or _CONUS_STATE_NAMES_RE.search(text):
        found.add("conus")
    return frozenset(found)


# --- Service branch ---------------------------------------------------------
#
# Which service a candidate would actually be embedded with. It is the question
# behind "is this an H2F job or a SEAL job", and nothing in a posting states it
# as a field -- it has to be read out of the employer name, the program name,
# or the installation.
#
# Returned as a SET, not one value, because plenty of these postings genuinely
# serve more than one service. GDIT lists a single strength-and-conditioning
# requisition across Fort Bragg, Coronado, Fort Campbell, Hurlburt Field and
# JBLM in one go -- Army, Navy, and Air Force in the same req. Collapsing that
# to a single branch would be a lie in whichever direction it fell.
#
# Ordered most-specific evidence first within each branch. Every pattern below
# was chosen against postings actually seen from Serco, GDIT, KBR, Geneva and
# USAJOBS, not from a general list of bases.
BRANCHES: tuple[tuple[str, str], ...] = (
    ("army", "Army"),
    ("navy", "Navy"),
    ("air-force", "Air Force"),
    ("marine-corps", "Marine Corps"),
    ("space-force", "Space Force"),
    ("coast-guard", "Coast Guard"),
    ("joint", "Joint / DoD-wide"),
)

BRANCH_LABELS: dict[str, str] = dict(BRANCHES)

_BRANCH_RES: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "army",
        re.compile(
            # Service and command names.
            r"\b(?:U\.?S\.?\s*)?Army\b|\bDepartment\s+of\s+the\s+Army\b|"
            r"\bUSARPAC\b|\bFORSCOM\b|\bUSASOC\b|\bTRADOC\b|\bAMEDD\b|"
            r"\bSFAB\b|\bSWCS\b|\b75th\s+Ranger\b|\bSpecial\s+Forces\s+Group\b|"
            # Programs that exist only in the Army.
            r"\bH2F\b|\bH2FIT\b|\bHolistic\s+Health\s+and\s+Fitness\b|"
            r"\bTHOR3\b|\bR2PC\b|\bReady\s+and\s+Resilient\b|"
            r"\bMaster\s+Resilience\s+Trainer\b|\bSoldier\b|\bSoldiers\b|"
            # "Fort X" is an Army post; the Air Force and Navy do not use it.
            # Fort Meade and Fort Belvoir are joint tenants, but the Army is
            # the host in both cases, so this stays correct there too.
            #
            # The lookahead is not optional. A good few American cities are
            # named Fort-something and have no post in them at all, and a VA
            # hospital in Fort Lauderdale was being labelled Army because of
            # it. These are the populous ones, which is where the health-care
            # postings that reach this board actually are.
            r"\bFort\s+(?!Worth|Lauderdale|Collins|Myers|Wayne|Smith|Pierce|"
            r"Dodge|Walton|Payne|Mill|Madison|Scott|Atkinson|Thomas|Washington)"
            r"[A-Za-z]+|"
            r"\bFt\.?\s+(?!Worth|Lauderdale|Collins|Myers|Wayne|Smith|Pierce)"
            r"[A-Za-z]+|"
            r"\bSchofield\s+Barracks\b|\bCamp\s+Casey\b|\bCamp\s+Humphreys\b|"
            r"\bGrafenwoehr\b|\bVilseck\b|\bHohenfels\b|\bAnsbach\b",
            re.I,
        ),
    ),
    (
        "navy",
        re.compile(
            r"\b(?:U\.?S\.?\s*)?Navy\b|\bNaval\b|\bDepartment\s+of\s+the\s+Navy\b|"
            r"\bCNIC\b|\bNavy\s+Installations\s+Command\b|\bBUMED\b|"
            r"\bNSW\b|\bNaval\s+Special\s+Warfare\b|\bSEAL\b|\bSWCC\b|"
            r"\bNAVSTA\b|\bNAS\s+[A-Z]|\bNSA\s+[A-Z][a-z]+|"
            r"\bSailor\b|\bSailors\b|\bMWR\b|"
            r"\bCoronado\b|\bDam\s+Neck\b|\bLittle\s+Creek\b|\bGreat\s+Lakes\b|"
            r"\bPoint\s+Mugu\b|\bSigonella\b|\bRota\b",
            re.I,
        ),
    ),
    (
        "air-force",
        re.compile(
            r"\b(?:U\.?S\.?\s*)?Air\s+Force\b|\bUSAF\b|\bAFSOC\b|\bACC\b|"
            r"\bAir\s+Force\s+Base\b|\bAFB\b|\bAir\s+Base\b|\bAirman\b|"
            r"\bAirmen\b|\bAFCENT\b|\bAMC\b|"
            r"\bHurlburt\s+Field\b|\bCannon\s+AFB\b|\bEglin\b|\bMacDill\b|"
            r"\bKadena\b|\bYokota\b|\bMisawa\b|\bOsan\b|\bRamstein\b|"
            r"\bAviano\b|\bLakenheath\b|\bMildenhall\b|\bRAF\s+\w+",
            re.I,
        ),
    ),
    (
        "marine-corps",
        re.compile(
            r"\b(?:U\.?S\.?\s*)?Marine\s+Corps\b|\bUSMC\b|\bMARSOC\b|"
            r"\bMarine\s+Raider\b|\bMarines\b|\bMCB\b|\bMCAS\b|\bMCRD\b|"
            # HITT is the Marine Corps' own human performance program, and it
            # is the single strongest tell in this whole table.
            r"\bHITT\b|\bHigh\s+Intensity\s+Tactical\s+Training\b|"
            r"\bForce\s+Fitness\b|"
            r"\bCamp\s+Lejeune\b|\bCamp\s+Pendleton\b|\bQuantico\b|"
            r"\bTwentynine\s+Palms\b|\b29\s+Palms\b|\bCamp\s+Foster\b|"
            r"\bCamp\s+Schwab\b|\bCamp\s+Courtney\b|\bOkinawa\b|"
            r"\bCherry\s+Point\b|\bParris\s+Island\b",
            re.I,
        ),
    ),
    (
        "space-force",
        re.compile(
            r"\b(?:U\.?S\.?\s*)?Space\s+Force\b|\bUSSF\b|\bGuardian\s+Resilience\b|"
            r"\bSpace\s+Systems\s+Command\b|\bSchriever\b|\bBuckley\s+(?:AFB|SFB)\b|"
            r"\bPeterson\s+(?:AFB|SFB)\b|\bPatrick\s+(?:AFB|SFB)\b|\bVandenberg\b",
            re.I,
        ),
    ),
    (
        "coast-guard",
        re.compile(
            r"\b(?:U\.?S\.?\s*)?Coast\s+Guard\b|\bUSCG\b|\bCoast\s+Guardsman\b",
            re.I,
        ),
    ),
    (
        "joint",
        re.compile(
            r"\bUSSOCOM\b|\bSOCOM\b|\bJSOC\b|\bSOF\b|\bPOTFF\b|"
            r"\bSpecial\s+Operations\s+Command\b|"
            r"\bPreservation\s+of\s+the\s+Force\b|"
            r"\bJoint\s+Base\b|\bJoint\s+Task\s+Force\b|"
            r"\bDefense\s+Health\s+Agency\b|\bDHA\b|\bDoD\b|"
            r"\bDepartment\s+of\s+Defense\b|\bTri-?Service\b",
            re.I,
        ),
    ),
)

# A description is long and full of incidental mentions -- a Serco H2F posting
# names the Air Force once in a benefits paragraph. Title, employer and
# location are declarative about who the job serves; the description is only
# consulted when those three say nothing at all.
_BRANCH_BODY_CAP = 600


def branches_of(
    title: str, employer: str = "", location: str = "", description: str = ""
) -> frozenset[str]:
    """Which service branches a posting serves. Empty means undetermined."""
    # An employer that names a service IS the answer, and it outranks the
    # installation. USAJOBS posts these as "United States Space Force" at
    # "Schriever AFB" -- a base the Space Force inherited and whose legacy name
    # still says Air Force. Reading both would file a Space Force job under
    # Air Force. Contractors (Serco, GDIT, KBR) match nothing here, so they
    # fall through to the combined read below, which is what they need.
    by_employer = {slug for slug, pattern in _BRANCH_RES if pattern.search(employer or "")}
    if by_employer:
        return frozenset(by_employer)

    strong = " \n".join(part for part in (title, employer, location) if part)
    found = {slug for slug, pattern in _BRANCH_RES if pattern.search(strong)}
    if found:
        return frozenset(found)

    body = (description or "")[:_BRANCH_BODY_CAP]
    if not body:
        return frozenset()
    return frozenset(
        slug for slug, pattern in _BRANCH_RES if pattern.search(body)
    )


def branch_labels(slugs: "frozenset[str] | set[str] | list[str]") -> list[str]:
    """Display labels for branch slugs, in the canonical BRANCHES order."""
    return [label for slug, label in BRANCHES if slug in set(slugs)]


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
    branches = branches_of(
        posting.title, posting.employer, posting.location, posting.description
    )
    return {
        "discipline": slug,
        "discipline_label": discipline_label(slug),
        "lead": is_lead(posting.title),
        "branches": sorted(branches),
        "branch_labels": branch_labels(branches),
        "location_classes": sorted(
            location_classes(posting.location, posting.remote)
        ),
        "contingency": contingency_of(
            posting.title, posting.description, posting.compensation or ""
        ),
        "salary_floor_annual": salary_floor_annual(posting.enrichment),
    }
