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
    # No "telework" -- see REMOTE_HINTS in sources/base.py. It means occasional
    # work from home from an on-base job, not a remote position.
    # telecommut\w* rather than a bare stem: the trailing \b in this pattern
    # can never match between the "t" of "telecommut" and the "e" of
    # "telecommute", so the bare stem matched nothing at all.
    r"\b(?:remote|work\s+from\s+home|telecommut\w*|virtual|anywhere)\b",
    re.I,
)
_REMOTE_VETO_RE = re.compile(
    r"\b(?:not\s+remote|no\s+remote|remote\s+work\s+is\s+not|non-remote|"
    r"cannot\s+be\s+performed\s+remotely)\b",
    re.I,
)


UNSPECIFIED_LOCATION = "unspecified"
TELEWORK_LOCATION = "telework"

# Telework is its own answer, deliberately NOT folded into ``remote``.
#
# Measured against 271 live federal postings matching this board's keywords:
#
#     RemoteIndicator=True,  TeleworkEligible=False  ->    1
#     RemoteIndicator=False, TeleworkEligible=True   ->  124
#     RemoteIndicator=False, TeleworkEligible=False  ->  146
#
# Every one of those 124 has a real duty station -- a nurse at Fort Knox, an HR
# administrator in Grand Rapids. Telework-eligible means the postholder may be
# approved for a day a week at home, from a job that is otherwise on the
# installation. Calling that "Remote" is what put a Cannon AFB social worker in
# front of candidates filtering for work from home, and folding it in now would
# do the same thing to 124 postings instead of three.
#
# So a candidate who wants flexibility can find these, and a candidate who wants
# an actually-remote job is not lied to. The value is ADDITIVE: a telework post
# at Fort Knox stays CONUS, and no posting's existing remote/CONUS/OCONUS
# answer changes because of it.
_TELEWORK_FLAG_RE = re.compile(r"telework\s+eligible:\s*(true|yes|false|no)\b", re.I)


def looks_telework(location: str, description: str = "") -> bool:
    """Whether the POSTING SAYS it offers telework. Nothing inferred.

    Only an explicit statement counts -- the agency's own telework-eligible
    field, or a posting writing that field out in words. A bare mention of the
    word somewhere in the text does not, and used to: the first version matched
    "telework" or "telecommute" anywhere in a description, so a job that merely
    listed telework among an agency's general benefits was published as a
    telework job it never claimed to be. Deciding that a posting "is really"
    telework on evidence it did not state is a guess, and a guess here is a
    candidate applying for something that does not exist.

    The value is read from the statement, so a posting saying "Telework
    eligible: False." answers False rather than being caught by its own denial.
    """
    blob = f"{location or ''} {description or ''}"
    flag = _TELEWORK_FLAG_RE.search(blob)
    return bool(flag) and flag.group(1).lower() in {"true", "yes"}


def location_classes(
    location: str, remote_flag: bool = False, telework_flag: bool = False
) -> frozenset[str]:
    """Any of ``remote`` / ``conus`` / ``oconus``, else ``{unspecified}``.

    Never returns an empty set. That is deliberate and load-bearing: a board
    reading this feed has to decide what to do with a posting it cannot place,
    and the obvious reading of an empty set -- "no constraint, so it matches
    every filter" -- is the wrong one. It put a Serco requisition spanning many
    installations and a GDIT pipeline req with no site yet under **Remote**, in
    front of candidates who had filtered for work from home.

    Naming the gap instead of leaving a hole means a consumer cannot fall into
    that reading by accident, and it gives the board an honest chip to render:
    "location not stated" is a real answer a candidate can act on, where a
    silent guess of CONUS is not.
    """
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
    # Added last, and never on its own account: telework says how you work, not
    # where the job is. A telework post still has to earn CONUS/OCONUS from its
    # location, and a posting with nothing but telework is still unplaced.
    placed = frozenset(found) or frozenset({UNSPECIFIED_LOCATION})
    if telework_flag:
        return placed | {TELEWORK_LOCATION}
    return placed


# --- Region: the second level of the location filter -------------------------
#
# CONUS/OCONUS answers "roughly where", and the next question is always "where
# exactly". These are the labels behind that second click: a US state for a
# CONUS posting, a country or non-contiguous state for an OCONUS one.
#
# The five shapes below are all real strings from the live board, which is why
# nothing here assumes a format:
#
#     "Fort Sill, Oklahoma, USA; Oklahoma, USA"      state spelled out
#     "USA NC Fort Bragg; USA CA San Diego"          GDIT: country, code, place
#     "Bethesda, Maryland"                           plain
#     "KS; HI; MO; SC; OK; TX; WA; JP"               bare codes
#     "Camp Casey, KOR"                              ISO-3
#
# Alaska and Hawaii appear as OCONUS regions rather than states, because that
# is what they are under the DoD definition this board already uses, and it is
# the answer a candidate filtering OCONUS is looking for.

_STATE_NAME_BY_CODE = {
    "AL": "Alabama", "AR": "Arkansas", "AZ": "Arizona", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DC": "District of Columbia",
    "DE": "Delaware", "FL": "Florida", "GA": "Georgia", "IA": "Iowa",
    "ID": "Idaho", "IL": "Illinois", "IN": "Indiana", "KS": "Kansas",
    "KY": "Kentucky", "LA": "Louisiana", "MA": "Massachusetts",
    "MD": "Maryland", "ME": "Maine", "MI": "Michigan", "MN": "Minnesota",
    "MO": "Missouri", "MS": "Mississippi", "MT": "Montana",
    "NC": "North Carolina", "ND": "North Dakota", "NE": "Nebraska",
    "NH": "New Hampshire", "NJ": "New Jersey", "NM": "New Mexico",
    "NV": "Nevada", "NY": "New York", "OH": "Ohio", "OK": "Oklahoma",
    "OR": "Oregon", "PA": "Pennsylvania", "RI": "Rhode Island",
    "SC": "South Carolina", "SD": "South Dakota", "TN": "Tennessee",
    "TX": "Texas", "UT": "Utah", "VA": "Virginia", "VT": "Vermont",
    "WA": "Washington", "WI": "Wisconsin", "WV": "West Virginia",
    "WY": "Wyoming",
}
_STATE_CODE_BY_NAME = {v.lower(): k for k, v in _STATE_NAME_BY_CODE.items()}

_STATE_NAME_RE = re.compile(
    r"\b(" + "|".join(re.escape(n) for n in sorted(_STATE_NAME_BY_CODE.values(), key=len, reverse=True)) + r")\b",
    re.I,
)

def _region_pattern(names: str, *codes: str) -> re.Pattern[str]:
    """A region matcher: place names case-insensitively, codes exactly.

    The two halves need different sensitivity. Place names arrive in every
    casing a recruiter felt like using ("Hawaii", "HAWAII", "hawaii"), so they
    have to be folded. Country and state codes must NOT be -- ``IT``, ``ES``,
    ``PR`` and ``BE`` are also the ordinary English words "it", "es", "pr" and
    "be", and a case-insensitive code would file a job in Italy on the strength
    of the word "it" appearing in its location line.
    """
    parts = [f"(?i:{names})"]
    if codes:
        parts.append(r"(?:^|[;,]\s*|\s)(?:" + "|".join(codes) + r")(?![A-Za-z])")
    return re.compile("|".join(parts))


# Ordered longest-first so "South Korea" is not read as "Korea" twice, and so
# a country name wins over a bare code sitting inside it.
_OCONUS_REGIONS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("Alaska", _region_pattern(r"\balaska\b|\bfort\s+wainwright\b|\belmendorf\b", "AK")),
    ("Hawaii", _region_pattern(r"\bhawaii\b|\bschofield\b|\bpearl\s+harbor\b|\bwahiawa\b", "HI")),
    ("Japan", _region_pattern(r"\bjapan\b|\bokinawa\b|\bkadena\b|\byokota\b|\bmisawa\b|\bcamp\s+zama\b", "JP", "JPN")),
    ("South Korea", _region_pattern(r"\bkorea\b|\bcamp\s+humphreys\b|\bcamp\s+casey\b|\bosan\b|\byongsan\b", "KR", "KOR", "ROK")),
    ("Germany", _region_pattern(r"\bgermany\b|\bdeutschland\b|\bramstein\b|\bstuttgart\b|\bgrafenw|\bvilseck\b|\bbaumholder\b|\bwiesbaden\b|\bansbach\b|\bhohenfels\b", "DEU")),
    ("Italy", _region_pattern(r"\bitaly\b|\bitalia\b|\bvicenza\b|\baviano\b|\bsigonella\b|\bnaples\b", "IT", "ITA")),
    ("United Kingdom", _region_pattern(r"\bengland\b|\bscotland\b|\bwales\b|\bunited\s+kingdom\b|\blakenheath\b|\bmildenhall\b|\bsuffolk\b", "UK", "GBR")),
    ("El Salvador", _region_pattern(r"\bel\s+salvador\b", "SLV")),
    ("Guam", _region_pattern(r"\bguam\b", "GU", "GUM")),
    ("Puerto Rico", _region_pattern(r"\bpuerto\s+rico\b", "PR", "PRI")),
    ("Kuwait", _region_pattern(r"\bkuwait\b|\barifjan\b", "KW", "KWT")),
    ("Qatar", _region_pattern(r"\bqatar\b|\bal\s+udeid\b", "QA", "QAT")),
    ("Spain", _region_pattern(r"\bspain\b|\brota\b|\bmoron\b", "ES", "ESP")),
    ("Belgium", _region_pattern(r"\bbelgium\b|\bchievres\b", "BE", "BEL")),
    ("Poland", _region_pattern(r"\bpoland\b", "PL", "POL")),
    ("Honduras", _region_pattern(r"\bhonduras\b|\bsoto\s+cano\b", "HN", "HND")),
    ("Colombia", _region_pattern(r"\bcolombia\b", "COL")),
)

_STATE_CODE_RE = re.compile(
    r"(?:^|[;,]\s*|\s)(" + "|".join(_CONUS_STATES) + r")(?![A-Za-z])"
)


def location_regions(
    location: str, classes: frozenset[str] | set[str]
) -> dict[str, list[str]]:
    """The state and country labels behind a CONUS/OCONUS pill.

    Grouped by the class they belong to, because the board draws them as a
    second level under whichever pill was clicked and a flat list could not say
    which pill a label sits beneath. A posting can appear under both: one GDIT
    requisition covers "KS; HI; MO; SC; OK; TX; WA; JP", which is five states
    under CONUS and Hawaii plus Japan under OCONUS.

    A class with nothing resolvable is left out entirely rather than mapped to
    an empty list, which is the honest answer -- a second-level filter that
    invents a state is worse than one that admits it cannot place the job.
    """
    text = location or ""
    out: dict[str, list[str]] = {}

    if "oconus" in classes:
        found = [label for label, pattern in _OCONUS_REGIONS if pattern.search(text)]
        if found:
            out["oconus"] = sorted(set(found))

    if "conus" in classes:
        codes: list[str] = []
        for match in _STATE_NAME_RE.finditer(text):
            code = _STATE_CODE_BY_NAME.get(match.group(1).lower())
            if code and code not in codes:
                codes.append(code)
        for match in _STATE_CODE_RE.finditer(text):
            code = match.group(1).upper()
            if code not in codes:
                codes.append(code)
        names = sorted({_STATE_NAME_BY_CODE[c] for c in codes if c in _STATE_NAME_BY_CODE})
        if names:
            out["conus"] = names

    return out


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
    classes = location_classes(
        posting.location,
        posting.remote,
        # The field is authoritative -- it was decided upstream against the
        # full posting. The text check only still runs so a posting built by
        # hand, or one whose description has not been trimmed yet, is not
        # silently read as non-telework.
        posting.telework or looks_telework(posting.location, posting.description),
    )
    return {
        "discipline": slug,
        "discipline_label": discipline_label(slug),
        "lead": is_lead(posting.title),
        "branches": sorted(branches),
        "branch_labels": branch_labels(branches),
        "location_classes": sorted(classes),
        "location_regions": location_regions(posting.location, classes),
        "contingency": contingency_of(
            posting.title, posting.description, posting.compensation or ""
        ),
        "salary_floor_annual": salary_floor_annual(posting.enrichment),
    }
