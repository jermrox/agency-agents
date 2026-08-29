"""Structured facts pulled out of job-description prose.

The classifier answers "is this one of ours?". This module answers everything
else the market-analysis layer wants to know, and it exists because the answers
are only ever available as a wall of unstructured text. A posting arrives as
900 words of boilerplate; nobody can query that. Certifications, clearance,
salary, education, installation, branch, and program are all *in* there, and
turning them into fields is what makes questions like "what does the market
actually pay a CSCS at a SOF unit versus a conventional H2F brigade" answerable
at all.

Three rules shape every extractor here:

* **Never guess.** No signal means ``None`` or ``[]``. A wrong salary poisons
  every aggregate computed downstream; a missing one only shrinks the sample.
* **Never crash.** Enrichment is best-effort metadata on a posting we already
  decided to publish. A weird description must not take down the run.
* **Demand a reason.** Every extracted number has to be attached to evidence
  that it means what we think it means. "$500,000" next to "budget" is not a
  salary; "3 years" without "experience" nearby is not a requirement.

Case sensitivity is used deliberately as a disambiguator. Credentials are
written in capitals in real postings, and their lowercase forms are usually
different words entirely -- ``lat`` is a muscle, ``Rd.`` is a road, ``atc``
is nothing. So the ambiguous acronyms (RD, LAT, ATC, BOC, GED, SMART) only
match uppercase, while unambiguous ones (CSCS, TSAC-F, CISSN, DPT) match in
any case. Case alone is not always enough -- an all-capitals street address
defeats it -- so the worst offenders additionally have to prove themselves
with nearby vocabulary.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .models import JobPosting

# --------------------------------------------------------------------------
# Input normalization
# --------------------------------------------------------------------------
# Descriptions arrive as text extracted from HTML, so they are full of the
# typographic characters a word processor inserts: curly apostrophes, en and
# em dashes, non-breaking spaces. Folding them to their ASCII equivalents once,
# up front, means no downstream pattern has to enumerate the variants -- and
# it is what makes "Master’s degree" parse the same as "Master's degree",
# which it previously did not.
#
# Every entry is a single character mapped to a single character, so the
# translation preserves length. That matters: the salary extractor works in
# character offsets, and a substitution that shifted them would silently
# corrupt every window it inspects.
_NORMALIZE = str.maketrans(
    {
        "‘": "'",  # left single quote
        "’": "'",  # right single quote -- the "Master's" killer
        "ʼ": "'",  # modifier letter apostrophe
        "´": "'",  # acute accent used as an apostrophe
        "“": '"',
        "”": '"',
        "‐": "-",  # hyphen
        "‑": "-",  # non-breaking hyphen
        "‒": "-",  # figure dash
        "–": "-",  # en dash
        "—": "-",  # em dash
        "―": "-",  # horizontal bar
        "−": "-",  # minus sign
        "­": "-",  # soft hyphen
        " ": " ",  # non-breaking space
        " ": " ",  # figure space
        " ": " ",  # narrow no-break space
        "﻿": " ",  # byte order mark pasted mid-document
    }
)

# Possessive whitespace, used wherever several optional groups sit back to
# back. A plain ``\s*`` in that position lets the engine redistribute one run
# of spaces across every gap in turn, which is polynomial: a description with
# a 400-space run took fifteen seconds to reject, and an 800-space run never
# finished. Nothing that can follow a gap here begins with whitespace, so
# handing characters back is never useful and forbidding it costs nothing.
_GAP = r"(?>\s*)"

# --------------------------------------------------------------------------
# Certifications
# --------------------------------------------------------------------------
# Every credential normalizes to one label so that counting them is possible.
# "RDN", "RD", and "Registered Dietitian Nutritionist" are one credential with
# three spellings; if they stay distinct the demand signal is split three ways.
@dataclass(frozen=True, slots=True)
class _CertRule:
    """One spelling of one credential, plus the evidence it needs.

    ``veto`` is a same-neighborhood disqualifier for acronyms that collide with
    unrelated military vocabulary (ATC is also Air Traffic Control).
    ``require`` is the opposite and is reserved for acronyms that are also
    ordinary text: the match is discarded *unless* supporting vocabulary sits
    beside it.
    """

    label: str
    pattern: re.Pattern[str]
    veto: re.Pattern[str] | None = None
    require: re.Pattern[str] | None = None


# Bare "RD" is a road as often as it is a dietitian. Upper-casing is not the
# defense it looks like, because federal postings print facility addresses in
# full capitals ("BLDG 4-2817 REILLY RD, FORT BRAGG"). So the two-letter form
# -- and only the two-letter form; "RDN" is unambiguous -- has to be standing
# next to nutrition or credentialing vocabulary to count.
_RD_CONTEXT_RE = re.compile(
    r"\b(?:dietitian|dietician|dietetics?|nutrition\w*|credential\w*|certif\w+|"
    r"registered|licens\w+|eligib\w+|required|require|preferred|prefer|CDR)\b",
    re.I,
)

_CERT_RULES: tuple[_CertRule, ...] = (
    # Strength and conditioning.
    _CertRule("CSCS", re.compile(r"\bCSCS\b", re.I)),
    _CertRule(
        "CSCS",
        re.compile(r"\bcertified\s+strength\s+(?:and|&)\s+conditioning\s+specialist\b", re.I),
    ),
    # TSAC-F only -- bare "TSAC" is the NSCA's program and journal name, not a
    # credential, and it shows up in postings that require nothing at all.
    _CertRule("TSAC-F", re.compile(r"\bTSAC[\s\-]?F\b", re.I)),
    _CertRule("TSAC-F", re.compile(r"\bTSAC[\s\-]?Facilitator\b", re.I)),
    _CertRule(
        "TSAC-F",
        re.compile(r"\btactical\s+strength\s+(?:and|&)\s+conditioning\s+facilitator\b", re.I),
    ),
    # Athletic training. BOC is the certifying body; "BOC certified" is how
    # half the market writes ATC, so it normalizes to the same label.
    _CertRule("ATC", re.compile(r"\bATC\b"), veto=re.compile(r"\bair\s+traffic\b", re.I)),
    _CertRule("ATC", re.compile(r"\bBOC\b")),
    _CertRule("ATC", re.compile(r"\bboard\s+of\s+certification\b", re.I)),
    _CertRule("ATC", re.compile(r"\bcertified\s+athletic\s+trainer\b", re.I)),
    _CertRule("ATC", re.compile(r"\bathletic\s+trainer[,\s]+certified\b", re.I)),
    _CertRule("LAT", re.compile(r"\bLAT\b")),
    _CertRule("LAT", re.compile(r"\blicensed\s+athletic\s+trainer\b", re.I)),
    # Nutrition.
    _CertRule("RD", re.compile(r"\bRDN\b")),
    _CertRule("RD", re.compile(r"\bRD\b"), require=_RD_CONTEXT_RE),
    _CertRule("RD", re.compile(r"\bregistered\s+dietitian(?:\s+nutritionist)?\b", re.I)),
    _CertRule("CISSN", re.compile(r"\bCISSN\b", re.I)),
    _CertRule("CISSN", re.compile(r"\bcertified\s+sports\s+nutritionist\b", re.I)),
    # Rehab.
    _CertRule("DPT", re.compile(r"\bDPT\b", re.I)),
    _CertRule("DPT", re.compile(r"\bdoctor(?:ate)?\s+of\s+physical\s+therapy\b", re.I)),
    # Other NSCA credentials. Bare "CPT" is never matched: in this domain it is
    # far more often a Captain than a Certified Personal Trainer.
    _CertRule("NSCA-CPT", re.compile(r"\bNSCA[\s\-]?CPT\b", re.I)),
    _CertRule("NSCA-CPT", re.compile(r"\bNSCA\s+certified\s+personal\s+trainer\b", re.I)),
    _CertRule("CSPS", re.compile(r"\bCSPS\b", re.I)),
    _CertRule("CSPS", re.compile(r"\bcertified\s+special\s+population\s+specialist\b", re.I)),
    # Research credential -- distinct from the *education* level, because a
    # posting can require a doctorate without wanting a PhD specifically.
    _CertRule("PhD", re.compile(r"\bPh\.?\s?D\.?\b", re.I)),
    _CertRule("PhD", re.compile(r"\bdoctor\s+of\s+philosophy\b", re.I)),
)

_CERT_VETO_WINDOW = 40
_CERT_CONTEXT_WINDOW = 60
"""Wider than the veto window: supporting vocabulary is often a clause away."""

# --------------------------------------------------------------------------
# Security clearance
# --------------------------------------------------------------------------
# Ranked so the highest mentioned level wins. A posting that says "Secret
# required, TS/SCI preferred" is a TS/SCI-adjacent billet and should be
# counted as the ceiling it names, not the floor.
_CLEARANCE_RANK: dict[str, int] = {
    "Public Trust": 1,
    "Secret": 2,
    "Top Secret": 3,
    "TS/SCI": 4,
}

_TS_SCI_RE = re.compile(
    r"\bTS\s*[/\-]\s*SCI\b"
    r"|\btop\s+secret\s*[/\-]\s*SCI\b"
    r"|\btop\s+secret\s+(?:with\s+)?(?:access\s+to\s+)?SCI\b"
    r"|\bsensitive\s+compartmented\s+information\b",
    re.I,
)
_TOP_SECRET_RE = re.compile(r"\btop\s+secret\b|\bTS\s+clearance\b", re.I)
_SECRET_RE = re.compile(r"\bsecret\b", re.I)
_PUBLIC_TRUST_RE = re.compile(r"\bpublic\s+trust\b", re.I)

# "Secret" and "public trust" are ordinary English. They only count as
# clearances when clearance vocabulary sits next to them -- otherwise
# "maintains the public trust of the community", which appears in nearly every
# law-enforcement posting, would tag half the board as cleared work.
_CLEARANCE_CONTEXT_RE = re.compile(
    r"\b(?:clearance|clearances|cleared|clearable|eligibility|eligible|"
    r"investigation|adjudicat\w*|obtain|obtainable|maintain|hold|holds|"
    r"possess|active|current|interim|favorable|background|suitability|"
    r"security|level)\b",
    re.I,
)
_SECRET_VETO_RE = re.compile(r"\btrade\s+secret\b|\bsecret\s+sauce\b", re.I)

# "Public trust" needs a narrower context than "Secret" does. Every law
# enforcement posting talks about maintaining the public trust of the
# community, and those sentences are full of words like "maintain" and
# "hold" that legitimately signal a Secret clearance elsewhere.
_PUBLIC_TRUST_CONTEXT_RE = re.compile(
    r"\b(?:clearance|position|investigation|background|suitability|"
    r"eligibility|determination|designation|level|required|requires|require)\b",
    re.I,
)
_CLEARANCE_WINDOW = 70

# --------------------------------------------------------------------------
# Salary
# --------------------------------------------------------------------------
# A number in a job description is almost never money. These bounds and guards
# are what keep "supervise 300 Soldiers" and "$1.2M equipment budget" out of
# the pay data.
_HOURLY_FLOOR = 5.0
_HOURLY_CEILING = 500.0
"""Above this an "hourly rate" is really an annual figure with a bad label."""

_ANNUAL_FLOOR = 10_000.0
"""Below this an "annual salary" is really a stipend, a year, or a typo."""

_ANNUAL_CEILING = 2_000_000.0

_AMOUNT_RE = re.compile(
    r"(?P<dollar>\$\s?)?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?P<k>\s?[Kk])?\b"
)

# The currency tokens on both sides catch the two ways an ATS renders the same
# band: "USD 90,000 - USD 115,000" hangs the second marker off the separator,
# "90,000 USD - 115,000 USD" hangs the first one there. Missing the leading
# form cost the whole ceiling -- the range collapsed to its floor.
#
# "and" is here for "between $80,000 and $95,000", which is how prose states a
# band. It is safe because the separator has to be the *entire* gap between two
# money-shaped numbers, so "$85,000 and relocation of $10,000" is not a range.
#
# The gaps are possessive for the same reason they are in ``_YEARS_RE``: this
# pattern is matched against the *whole* span between two numbers, which can be
# thousands of characters of whitespace in a badly extracted description, and
# two plain ``\s*`` either side of an optional token is quadratic.
#
# The optional period suffix covers "$75,000/yr - $95,000/yr", where each
# endpoint carries its own label. Without it the separator does not match and
# the band collapses to its floor -- which is worse than finding nothing,
# because it reports a real-looking ceiling that is 20k too low.
_RANGE_SEP_RE = re.compile(
    rf"^{_GAP}(?:USD|CAD|EUR|GBP)?"
    rf"{_GAP}(?:/\s*(?:yr|year|hr|hour)|per\s+(?:year|annum|hour)|annually|yearly|hourly)?"
    rf"{_GAP}(?:-|--|–|—|to|through|up\s+to|and)"
    rf"{_GAP}(?:USD|CAD|EUR|GBP)?{_GAP}$",
    re.I,
)

# Number immediately followed by a counting noun: a headcount, a duration, a
# distance. Never money.
# The separator is optional AND may be a hyphen, because a compound adjective
# writes the unit without a space: Serco's H2F postings advertise "80-hour pay
# periods (generally 40-hour work weeks)". With only "\s*" here, the 80 sailed
# past this veto, "pay" two words later satisfied the salary cue, and every one
# of those coaching jobs published a floor of $80/hr -> $166,400 a year, about
# a hundred thousand above what the role actually pays.
_UNIT_NOUN_RE = re.compile(
    r"^[\s\-\u2010-\u2015]*(?:%|percent|hours?|hrs?|days?|weeks?|months?|years?|yrs?|minutes?|"
    r"mins?|miles?|lbs?|pounds?|kgs?|kilograms?|reps?|sets?|sessions?|clients?|"
    r"patients?|athletes?|soldiers?|sailors?|airmen|marines?|operators?|"
    r"personnel|people|employees?|students?|staff|members?|participants?|"
    r"beds?|units?|square|sq|million|billion|degrees?)\b",
    re.I,
)

# Money-shaped nouns that mean the figure belongs to an org, not a person.
_VETO_WORDS = (
    r"budget|grant|award|endowment|equipment|facility|renovation|donation|"
    r"scholarship|prize|revenue|portfolio|inventory|deficit|debt|fundraising"
)

# One-time payments. These are money paid to a person, which is why the org
# vetoes above do not catch them, but they are not the pay rate -- and a
# "sign-on bonus of $10,000 - $15,000" is *range*-shaped, so it outranks the
# real salary and wins outright unless it is vetoed here.
_ONE_TIME_WORDS = r"relocation|signing|sign[\s-]?on|severance|referral|retention"

# "hiring" labels a payment only when it is touching the figure. It is absent
# from the *before* list on purpose: "hiring range is $85,000 - $95,000" is
# real ATS phrasing for the actual salary band.
_VETO_BEFORE_RE = re.compile(
    rf"\b(?:{_VETO_WORDS}|{_ONE_TIME_WORDS}|bonus(?:es)?|"
    rf"manages?|managing|oversees?|supervis\w+)\b[^.\n]{{0,20}}$",
    re.I,
)

# Two distances, for two different reasons. An org-money noun can sit a few
# words past the figure ("$250,000 renovation grant for the center"), but a
# one-time-payment label has to be touching it: "$15,000 relocation bonus" is
# a bonus, while "$85,000 per year and relocation of $10,000" is a salary that
# merely mentions one. "bonus" itself is in neither after-list -- it trails a
# genuine salary constantly ("$85,000 per year plus an annual bonus").
_VETO_AFTER_RE = re.compile(
    rf"^(?:[^.\n]{{0,15}}\b(?:{_VETO_WORDS})\b"
    rf"|[\s(]{{0,3}}(?:{_ONE_TIME_WORDS}|hiring)\b)",
    re.I,
)

# Retirement plans are the single worst salary false positive: "401k" parses
# as $401,000 a year and "401(k)" as $401 an hour, and both sit right next to
# the word "compensation" in the benefits paragraph.
_RETIREMENT_RE = re.compile(rf"\b(?:401|403|457){_GAP}\(?{_GAP}[kb]{_GAP}\)?", re.I)

# This is the ONLY gate on a number carrying neither a currency symbol nor a
# "k" suffix, so every word in it has to be one that does not appear in
# ordinary benefits prose. The earlier list included bare "pay", "paid",
# "rate", "range" and "band", which a benefits section says constantly:
#
#     "Support your work/life balance with 10 paid Federal Holidays"
#     "...and 80-hour pay periods (generally 40-hour work weeks)"
#
# Both sat in the same Serco H2F posting, and between them published a
# strength and conditioning coach at $80/hr and then $10/hr. A missing salary
# is an admitted gap; a wrong one is the number a candidate negotiates
# against, so this list is deliberately narrow.
#
# "pay" and "rate" survive only bound to an explicit money phrase -- "rate of
# pay", "pay of", "hourly rate" -- never standing alone.
_SALARY_CUE_RE = re.compile(
    r"\b(?:salary|salaries|salaried|wage|wages|compensation|remuneration|"
    r"stipend|earnings|"
    r"hourly|annually|annualized|yearly|per\s+year|per\s+hour|per\s+annum|"
    r"rate\s+of\s+pay|pay\s+rate|hourly\s+rate|pay\s+of|salary\s+of)\b",
    re.I,
)
_SALARY_CUE_BEFORE = 120
_SALARY_CUE_AFTER = 60

_PERIOD_YEAR_RE = re.compile(
    r"per\s+year|per\s+annum|annually|annualized|annual|yearly|/\s*yr\b|/\s*year\b",
    re.I,
)
_PERIOD_HOUR_RE = re.compile(
    r"per\s+hour|per\s+hr\b|hourly|an\s+hour|/\s*hr\b|/\s*hour\b|hour(?:ly)?\s+rate",
    re.I,
)

# Only one endpoint is stated: "starting at $75,000" is a floor with no
# ceiling, and inventing the missing side would fabricate a range.
_MIN_ONLY_RE = re.compile(
    r"(?:starting\s+(?:at|salary(?:\s+of)?)|beginning\s+at|from|"
    r"minimum\s+of|at\s+least|no\s+less\s+than)\s*[:\s]?\s*$",
    re.I,
)
_MAX_ONLY_RE = re.compile(
    r"(?:up\s+to|not\s+to\s+exceed|maximum\s+of|as\s+much\s+as|as\s+high\s+as)\s*[:\s]?\s*$",
    re.I,
)
_CUE_LOOKBACK = 28

# Magnitude is the last resort when no period word is present. The dead zone
# between them is deliberate: a bare "$800" is more likely a weekly stipend or
# a per-diem than either a wage or a salary, so it is dropped entirely.
_MAGNITUDE_YEAR_FLOOR = 1_000.0
_MAGNITUDE_HOUR_CEILING = 200.0

# --------------------------------------------------------------------------
# Education
# --------------------------------------------------------------------------
# Ranked so the *lowest* level found can be reported. Postings state a floor
# and then an aspiration -- "Bachelor's required, Master's preferred" -- and
# the floor is what actually gates applicants. Taking the maximum would
# systematically overstate the barrier to entry across the whole board.
_EDUCATION_RANK: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    (
        "High School",
        (
            # "high school" alone is a *population* in this domain (coaches who
            # came from high school athletics), so a diploma word is required.
            re.compile(r"\bhigh\s+school\s+(?:diploma|graduate|equivalen\w*)\b", re.I),
            re.compile(r"\bGED\b"),
        ),
    ),
    (
        "Associate",
        (
            re.compile(r"\bassociate(?:'?s)?\s+degree\b", re.I),
            re.compile(r"\bassociate\s+of\s+(?:science|arts|applied\s+science)\b", re.I),
            re.compile(r"\btwo[\s-]year\s+degree\b", re.I),
        ),
    ),
    (
        "Bachelor",
        (
            re.compile(r"\bbachelor(?:'?s)?\b", re.I),
            re.compile(r"\bbaccalaureate\b", re.I),
            re.compile(r"\bundergraduate\s+degree\b", re.I),
            re.compile(r"\bfour[\s-]year\s+degree\b", re.I),
            re.compile(r"\bB\.\s?[SA]\.\b"),
            re.compile(r"\bB[SA]\b(?=\s+(?:in|degree))"),
        ),
    ),
    (
        "Master",
        (
            # Possessive or "of science" only: "Master Resilience Trainer" and
            # "master trainer" are Army job titles, not degrees.
            re.compile(r"\bmaster'?s\b", re.I),
            re.compile(r"\bmaster\s+of\s+(?:science|arts|public\s+health|education)\b", re.I),
            re.compile(r"\bgraduate\s+degree\b", re.I),
            re.compile(r"\bM\.\s?[SA]\.\b"),
            re.compile(r"\bM[SA]\b(?=\s+(?:in|degree))"),
            re.compile(r"\bMPH\b"),
        ),
    ),
    (
        "Doctorate",
        (
            re.compile(r"\bdoctora(?:te|l)\b", re.I),
            re.compile(r"\bPh\.?\s?D\.?\b", re.I),
            re.compile(r"\bDPT\b", re.I),
            re.compile(r"\bEd\.?D\.?\b"),
            re.compile(
                r"\bdoctor\s+of\s+(?:physical\s+therapy|philosophy|education|science)\b", re.I
            ),
            re.compile(r"\bterminal\s+degree\b", re.I),
        ),
    ),
)

# --------------------------------------------------------------------------
# Years of experience
# --------------------------------------------------------------------------
_NUMBER_WORDS: dict[str, int] = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "fifteen": 15,
    "twenty": 20,
}
_WORD_ALT = "|".join(_NUMBER_WORDS)

# Handles "5+ years", "at least 2 years", "minimum of three (3) years",
# "5-7 years", and "three (3) to five (5) years" with one pass. The leading
# number is always the one captured, because a range's floor is the
# requirement and its ceiling is a wish.
#
# Every gap is possessive. Six optional groups separated by plain ``\s*`` gave
# the engine six places to split one run of whitespace, and "5" followed by a
# few hundred spaces and no "years" took minutes to reject.
_YEARS_RE = re.compile(
    rf"\b(?:(?P<word>{_WORD_ALT})|(?P<num>\d{{1,2}}))"
    rf"{_GAP}(?:\({_GAP}\d{{1,2}}{_GAP}\))?"
    rf"{_GAP}(?:\+|plus)?"
    rf"{_GAP}(?:(?:-|--|–|—|to|through){_GAP}(?:{_WORD_ALT}|\d{{1,2}})"
    rf"{_GAP}(?:\({_GAP}\d{{1,2}}{_GAP}\))?{_GAP})?"
    rf"(?:\+|plus)?{_GAP}"
    r"(?:years?|yrs?)\b",
    re.I,
)
_EXPERIENCE_RE = re.compile(r"\bexperience|\bexp\b|\bbackground\s+in\b", re.I)
_EXPERIENCE_BEFORE = 45
_EXPERIENCE_AFTER = 90
_MAX_REASONABLE_YEARS = 40

# --------------------------------------------------------------------------
# Employment type
# --------------------------------------------------------------------------
# "Contract" is deliberately narrow. Nearly every tactical human performance
# billet is funded by a government contract, so bare "contract" says nothing
# about the worker's status; only phrases that describe the *engagement* count.
_EMPLOYMENT_RULES: tuple[tuple[str, re.Pattern[str], re.Pattern[str] | None], ...] = (
    (
        "Per-diem",
        re.compile(r"\bper[\s-]?diem\b", re.I),
        # Travel per diem is reimbursement, not a schedule.
        re.compile(r"\b(?:travel|lodging|meals?|allowance|reimburse\w*|expenses?|rates?)\b", re.I),
    ),
    ("Per-diem", re.compile(r"\bPRN\b"), None),
    ("Part-time", re.compile(r"\bpart[\s-]?time\b", re.I), None),
    ("Full-time", re.compile(r"\bfull[\s-]?time\b", re.I), None),
    (
        "Contract",
        re.compile(
            r"\b(?:1099|independent\s+contractor|contract[\s-]to[\s-]hire|"
            r"contract(?:or)?\s+(?:position|role|employee|basis|assignment|opportunity)|"
            r"on\s+a\s+contract\s+basis|temporary\s+(?:position|assignment|role))\b",
            re.I,
        ),
        None,
    ),
)
_EMPLOYMENT_VETO_WINDOW = 40

# --------------------------------------------------------------------------
# Installations
# --------------------------------------------------------------------------
# Canonical names are the traditional ones. Several posts were renamed in 2023
# and renamed back in 2025, so "Fort Bragg" is simultaneously the current
# official name, the name in every pre-2023 posting, and the name practitioners
# actually use. "Fort Liberty" and the other interim names are kept as aliases
# so the 2023-2025 archive does not fragment into two separate installations.
def _fort(*names: str) -> tuple[str, ...]:
    """Patterns for "Fort X" / "Ft. X" / "Ft X"."""
    return tuple(rf"\b(?:fort|ft\.?)\s+{name}\b" for name in names)


_INSTALLATIONS_RAW: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    # Army -- the bulk of H2F and THOR3 hiring.
    ("Fort Bragg", "Army", _fort("bragg", "liberty")),
    ("Fort Campbell", "Army", _fort("campbell")),
    ("Fort Carson", "Army", _fort("carson")),
    ("Fort Benning", "Army", _fort("benning", "moore")),
    ("Fort Stewart", "Army", _fort("stewart")),
    ("Fort Drum", "Army", _fort("drum")),
    ("Fort Hood", "Army", _fort("hood", "cavazos")),
    ("Fort Bliss", "Army", _fort("bliss")),
    ("Fort Riley", "Army", _fort("riley")),
    ("Fort Knox", "Army", _fort("knox")),
    ("Fort Gordon", "Army", _fort("gordon", "eisenhower")),
    ("Fort Polk", "Army", _fort("polk", "johnson")),
    ("Fort Rucker", "Army", _fort("rucker", "novosel")),
    ("Fort Leonard Wood", "Army", _fort(r"leonard\s+wood")),
    ("Fort Sill", "Army", _fort("sill")),
    ("Fort Jackson", "Army", _fort("jackson")),
    ("Fort Irwin", "Army", _fort("irwin")),
    ("Fort Belvoir", "Army", _fort("belvoir")),
    ("Fort Meade", "Army", _fort("meade")),
    ("Fort Huachuca", "Army", _fort("huachuca")),
    ("Fort Wainwright", "Army", _fort("wainwright")),
    ("Schofield Barracks", "Army", (r"\bschofield\s+barracks\b",)),
    # Joint bases.
    ("JBLM", "Joint", (r"\bJBLM\b", r"\bjoint\s+base\s+lewis[\s-]?mcchord\b", r"\bfort\s+lewis\b")),
    ("JBSA", "Joint", (r"\bJBSA\b", r"\bjoint\s+base\s+san\s+antonio\b")),
    ("JBER", "Joint", (r"\bJBER\b", r"\bjoint\s+base\s+elmendorf[\s-]?richardson\b")),
    ("Joint Base Langley-Eustis", "Joint", (r"\bjoint\s+base\s+langley[\s-]?eustis\b",)),
    ("Pearl Harbor", "Joint", (r"\bjoint\s+base\s+pearl\s+harbor\b", r"\bJBPHH\b")),
    # Marine Corps.
    ("Camp Lejeune", "Marine Corps", (r"\bcamp\s+lejeune\b", r"\bMCB\s+lejeune\b")),
    ("Camp Pendleton", "Marine Corps", (r"\bcamp\s+pendleton\b",)),
    ("Quantico", "Marine Corps", (r"\bquantico\b",)),
    ("Twentynine Palms", "Marine Corps", (r"\btwentynine\s+palms\b", r"\b29\s+palms\b")),
    # Navy / Naval Special Warfare.
    ("Coronado", "Navy", (r"\bcoronado\b",)),
    ("Little Creek", "Navy", (r"\blittle\s+creek\b",)),
    ("Dam Neck", "Navy", (r"\bdam\s+neck\b",)),
    ("Naval Station Norfolk", "Navy", (r"\bnaval\s+station\s+norfolk\b", r"\bNAS\s+norfolk\b")),
    # Air Force.
    ("Hurlburt Field", "Air Force", (r"\bhurlburt\s+field\b", r"\bhurlburt\b")),
    ("Cannon AFB", "Air Force", (r"\bcannon\s+(?:AFB|air\s+force\s+base)\b",)),
    ("Eglin AFB", "Air Force", (r"\beglin\s+(?:AFB|air\s+force\s+base)\b", r"\beglin\b")),
    ("MacDill AFB", "Air Force", (r"\bmacdill\s*(?:AFB|air\s+force\s+base)?\b",)),
    ("Nellis AFB", "Air Force", (r"\bnellis\s+(?:AFB|air\s+force\s+base)\b",)),
    ("Fairchild AFB", "Air Force", (r"\bfairchild\s+(?:AFB|air\s+force\s+base)\b",)),
    # Space Force.
    ("Peterson SFB", "Space Force", (r"\bpeterson\s+(?:SFB|AFB|space\s+force\s+base)\b",)),
    ("Schriever SFB", "Space Force", (r"\bschriever\s+(?:SFB|AFB|space\s+force\s+base)\b",)),
    ("Buckley SFB", "Space Force", (r"\bbuckley\s+(?:SFB|AFB|space\s+force\s+base)\b",)),
    ("Vandenberg SFB", "Space Force", (r"\bvandenberg\s+(?:SFB|AFB|space\s+force\s+base)\b",)),
)

_INSTALLATIONS: tuple[tuple[str, str, tuple[re.Pattern[str], ...]], ...] = tuple(
    (name, branch, tuple(re.compile(pattern, re.I) for pattern in patterns))
    for name, branch, patterns in _INSTALLATIONS_RAW
)

# --------------------------------------------------------------------------
# Service branch
# --------------------------------------------------------------------------
# Weighted rather than first-match: an Army H2F posting routinely name-drops
# SOCOM and the Marine Corps, and the branch that owns the billet is the one
# with the most evidence behind it, not the one mentioned first.
_BRANCH_TERMS: dict[str, dict[str, float]] = {
    "Army": {
        "army": 3.0,
        "usasoc": 3.0,
        "thor3": 3.0,
        "h2f": 3.0,
        "holistic health and fitness": 3.0,
        "soldier": 2.0,
        "soldiers": 2.0,
        "green beret": 2.5,
        "special forces group": 2.5,
        "ranger regiment": 2.5,
        "airborne division": 2.0,
        "infantry division": 2.0,
        "national guard": 1.5,
    },
    "Navy": {
        "navy": 3.0,
        "naval special warfare": 3.0,
        "nswc": 2.0,
        "sailor": 2.0,
        "sailors": 2.0,
        "navy seal": 2.5,
        "seal team": 2.5,
        "swcc": 2.5,
        "usn": 2.0,
        "naval": 1.5,
    },
    "Air Force": {
        "air force": 3.0,
        "usaf": 3.0,
        "afsoc": 3.0,
        "airman": 2.0,
        "airmen": 2.0,
        "air commando": 2.5,
        "pararescue": 2.5,
        "special tactics": 2.0,
        "special warfare airman": 3.0,
    },
    "Marine Corps": {
        "marine corps": 3.0,
        "usmc": 3.0,
        "marsoc": 3.0,
        "marine raider": 2.5,
        "marines": 2.0,
        "force fitness": 2.0,
        "sports medicine and reconditioning": 2.5,
    },
    "Coast Guard": {
        "coast guard": 3.0,
        "uscg": 3.0,
    },
    "Space Force": {
        "space force": 3.0,
        "ussf": 2.5,
    },
    "Joint": {
        "socom": 2.0,
        "ussocom": 2.0,
        "jsoc": 2.0,
        "joint special operations": 2.5,
        "joint task force": 2.0,
        "potff": 2.0,
        "preservation of the force": 2.0,
        "joint base": 1.5,
        "defense health agency": 1.5,
        "all branches": 1.5,
    },
}

_INSTALLATION_BRANCH_WEIGHT = 1.2
"""Weak on purpose: an installation hints at a branch, explicit words prove it."""

# --------------------------------------------------------------------------
# Named programs
# --------------------------------------------------------------------------
# Ordered most-specific-unit first. A posting under both THOR3 and POTFF is a
# THOR3 billet described by its parent program, not the other way around.
_PROGRAM_RULES: tuple[tuple[str, tuple[re.Pattern[str], ...]], ...] = (
    (
        "THOR3",
        (
            re.compile(r"\bthor\s?3\b", re.I),
            re.compile(r"\bthor[\s-]?iii\b", re.I),
            re.compile(r"\btactical\s+human\s+optimization\b", re.I),
        ),
    ),
    (
        "POTFF",
        (
            re.compile(r"\bpotff\b", re.I),
            re.compile(r"\bpreservation\s+of\s+the\s+force\s+and\s+family\b", re.I),
        ),
    ),
    (
        "SMART",
        (
            # SMART must be capitalized *and* qualified. "SMART goals" is in
            # every coaching job description ever written; the Marine Corps
            # Sports Medicine and Reconditioning Team is not. The acronym is
            # case-sensitive, the noun after it is not.
            re.compile(r"\bSMART\s+(?i:center|centre|team|clinic|site|program|facilit\w+)\b"),
            re.compile(r"\bsports\s+medicine\s+and\s+reconditioning\s+team\b", re.I),
        ),
    ),
    (
        "H2F",
        (
            re.compile(r"\bh2f\b", re.I),
            re.compile(r"\bholistic\s+health\s+and\s+fitness\b", re.I),
        ),
    ),
)


@dataclass(slots=True)
class Enrichment:
    """Structured facts extracted from one posting.

    Every field defaults to "unknown" so that an unparseable posting produces
    a valid, empty ``Enrichment`` rather than an exception or a fabricated
    value. Downstream aggregates must treat ``None`` as "not stated", never as
    a zero.
    """

    certifications: list[str] = field(default_factory=list)
    clearance: str | None = None
    salary_min: float | None = None
    salary_max: float | None = None
    salary_period: str | None = None
    education: str | None = None
    years_experience_min: int | None = None
    employment_type: str | None = None
    installation: str | None = None
    service_branch: str | None = None
    program: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Stable JSON shape. Every key is always present.

        The archive is read by tooling that groups and counts; a key that
        appears only when a value was found would force every consumer to
        write ``.get()`` defensively.
        """
        return {
            "certifications": list(self.certifications),
            "clearance": self.clearance,
            "salary_min": self.salary_min,
            "salary_max": self.salary_max,
            "salary_period": self.salary_period,
            "education": self.education,
            "years_experience_min": self.years_experience_min,
            "employment_type": self.employment_type,
            "installation": self.installation,
            "service_branch": self.service_branch,
            "program": self.program,
        }


def enrich(posting: JobPosting) -> Enrichment:
    """Extract facts from ``posting`` and stamp them onto ``posting.enrichment``.

    Mirrors :func:`classify.classify`: annotate in place *and* return, so a
    caller can use whichever is convenient. The in-place write is what makes
    ``to_public_dict``/``to_archive_dict`` carry enrichment without the
    pipeline having to know this module's shape.
    """
    result = enrich_text(
        title=posting.title or "",
        description=posting.description or "",
        location=posting.location or "",
        compensation=posting.compensation or "",
    )
    posting.enrichment = result.to_dict()
    return result


def enrich_text(
    title: str, description: str, location: str = "", compensation: str = ""
) -> Enrichment:
    """Pure extraction over raw strings. The testable core of :func:`enrich`.

    Kept separate from :func:`enrich` so callers that hold text but not a
    :class:`JobPosting` (a re-analysis pass over the archive, for instance)
    do not have to fabricate one.
    """
    # ``or ""`` rather than a type check: a source that hands us ``None`` for a
    # missing field is normal, and enrichment is never the place to raise.
    title = (title or "").translate(_NORMALIZE)
    description = (description or "").translate(_NORMALIZE)
    location = (location or "").translate(_NORMALIZE)
    compensation = (compensation or "").translate(_NORMALIZE)

    body = f"{title}\n{description}"
    salary_min, salary_max, salary_period = _extract_salary(compensation, description, title)
    installation, installation_branch = _extract_installation(title, location, description)

    return Enrichment(
        certifications=_extract_certifications(body),
        clearance=_extract_clearance(body),
        salary_min=salary_min,
        salary_max=salary_max,
        salary_period=salary_period,
        education=_extract_education(body),
        years_experience_min=_extract_years(body),
        employment_type=_extract_employment_type(title, description),
        installation=installation,
        service_branch=_extract_branch(
            f"{title}\n{location}\n{description}", installation_branch
        ),
        program=_extract_program(title, description),
    )


# --------------------------------------------------------------------------
# Field extractors
# --------------------------------------------------------------------------

def _extract_certifications(text: str) -> list[str]:
    """Every credential named anywhere in the posting, normalized and deduped."""
    found: set[str] = set()
    for rule in _CERT_RULES:
        if rule.label in found:
            continue
        for match in rule.pattern.finditer(text):
            if rule.veto is not None and rule.veto.search(
                _window(text, match, _CERT_VETO_WINDOW)
            ):
                continue
            if rule.require is not None and not rule.require.search(
                _window(text, match, _CERT_CONTEXT_WINDOW)
            ):
                continue
            found.add(rule.label)
            break
    return sorted(found)


def _window(text: str, match: re.Match[str], radius: int) -> str:
    """The neighbourhood a match has to justify itself in."""
    return text[max(0, match.start() - radius) : match.end() + radius]


def _extract_clearance(text: str) -> str | None:
    """Highest clearance level named, or ``None``."""
    levels: list[str] = []
    if _TS_SCI_RE.search(text):
        levels.append("TS/SCI")
    if _TOP_SECRET_RE.search(text):
        levels.append("Top Secret")
    if _has_clearance_context(text, _SECRET_RE, veto=_SECRET_VETO_RE):
        levels.append("Secret")
    if _has_clearance_context(
        text, _PUBLIC_TRUST_RE, veto=None, context=_PUBLIC_TRUST_CONTEXT_RE
    ):
        levels.append("Public Trust")
    if not levels:
        return None
    return max(levels, key=lambda level: _CLEARANCE_RANK[level])


def _has_clearance_context(
    text: str,
    pattern: re.Pattern[str],
    veto: re.Pattern[str] | None,
    context: re.Pattern[str] | None = None,
) -> bool:
    """True when ``pattern`` fires with clearance vocabulary beside it."""
    context = context or _CLEARANCE_CONTEXT_RE
    for match in pattern.finditer(text):
        window = text[
            max(0, match.start() - _CLEARANCE_WINDOW) : match.end() + _CLEARANCE_WINDOW
        ]
        if veto is not None and veto.search(window):
            continue
        if context.search(window):
            return True
    return False


def _extract_education(text: str) -> str | None:
    """Lowest education level stated -- the floor an applicant must clear."""
    for level, patterns in _EDUCATION_RANK:
        if any(pattern.search(text) for pattern in patterns):
            return level
    return None


def _extract_years(text: str) -> int | None:
    """Smallest stated experience requirement, in whole years."""
    best: int | None = None
    for match in _YEARS_RE.finditer(text):
        before = text[max(0, match.start() - _EXPERIENCE_BEFORE) : match.start()]
        after = text[match.end() : match.end() + _EXPERIENCE_AFTER]
        # Without this guard "a 5 year contract" and "within 2 years of hire"
        # both read as hiring requirements.
        if not (_EXPERIENCE_RE.search(before) or _EXPERIENCE_RE.search(after)):
            continue
        word = match.group("word")
        value = _NUMBER_WORDS[word.lower()] if word else int(match.group("num"))
        if value > _MAX_REASONABLE_YEARS:
            continue
        if best is None or value < best:
            best = value
    return best


def _extract_employment_type(title: str, description: str) -> str | None:
    """Schedule/engagement type, preferring what the title says.

    Earliest mention wins within each field. A posting leads with the thing it
    is; caveats and comparisons come later.
    """
    for text in (title, description):
        if not text:
            continue
        best: tuple[int, str] | None = None
        for label, pattern, veto in _EMPLOYMENT_RULES:
            for match in pattern.finditer(text):
                if veto is not None and veto.search(
                    text[match.end() : match.end() + _EMPLOYMENT_VETO_WINDOW]
                ):
                    continue
                if best is None or match.start() < best[0]:
                    best = (match.start(), label)
                break
        if best is not None:
            return best[1]
    return None


def _extract_installation(
    title: str, location: str, description: str
) -> tuple[str | None, str | None]:
    """Canonical installation plus the branch that owns it.

    Searched title, then location, then description: the location field is
    structured data straight from the source, while the description may
    mention a dozen posts the role merely coordinates with.
    """
    for text in (title, location, description):
        if not text:
            continue
        best: tuple[int, str, str] | None = None
        for name, branch, patterns in _INSTALLATIONS:
            for pattern in patterns:
                match = pattern.search(text)
                if match is None:
                    continue
                if best is None or match.start() < best[0]:
                    best = (match.start(), name, branch)
                break
        if best is not None:
            return best[1], best[2]
    return None, None


def _extract_branch(text: str, installation_branch: str | None) -> str | None:
    """Owning service, or ``Joint`` when the evidence genuinely spans services."""
    flat = _flatten(text)
    scores: dict[str, float] = {}
    for branch, terms in _BRANCH_TERMS.items():
        total = sum(weight for term, weight in terms.items() if f" {term} " in flat)
        if total:
            scores[branch] = total
    if installation_branch:
        scores[installation_branch] = (
            scores.get(installation_branch, 0.0) + _INSTALLATION_BRANCH_WEIGHT
        )
    if not scores:
        return None
    top = max(scores.values())
    leaders = [branch for branch, score in scores.items() if score == top]
    if len(leaders) > 1:
        # Two services with equal evidence is the definition of a joint billet.
        return "Joint"
    return leaders[0]


def _extract_program(title: str, description: str) -> str | None:
    """Named human performance program, title first."""
    for text in (title, description):
        if not text:
            continue
        for label, patterns in _PROGRAM_RULES:
            if any(pattern.search(text) for pattern in patterns):
                return label
    return None


def _flatten(text: str) -> str:
    """Lowercase, punctuation to spaces, padded -- so ``in`` is a word match.

    Same trick the classifier uses, so "H2F," "H2F." and "(H2F)" are one term.
    """
    collapsed = re.sub(r"[^a-z0-9]+", " ", text.lower().replace("&", " and ")).strip()
    return f" {collapsed} "


# --------------------------------------------------------------------------
# Salary extraction
# --------------------------------------------------------------------------

@dataclass(slots=True)
class _Amount:
    """One money-shaped number and the evidence attached to it."""

    value: float
    start: int
    end: int
    dollar: bool
    kilo: bool


def _extract_salary(
    compensation: str, description: str, title: str
) -> tuple[float | None, float | None, str | None]:
    """Pay range from the most trustworthy field that has one.

    The compensation field is structured output from the source: if it holds a
    number, that number is the pay, so no supporting cue is demanded. Free text
    gets the opposite treatment -- a figure in prose must prove it is money.
    """
    for text, require_cue in ((compensation, False), (description, True), (title, True)):
        if not text or not text.strip():
            continue
        found = _salary_from_text(text, require_cue=require_cue)
        if found is not None:
            return found
    return None, None, None


def _salary_from_text(
    text: str, require_cue: bool
) -> tuple[float | None, float | None, str | None] | None:
    """Best salary reading of ``text``, or ``None`` if nothing survives."""
    amounts = _money_candidates(text, require_cue=require_cue)
    if not amounts:
        return None

    # (rank, position) -- ranges outrank single figures because "$75K-$95K" is
    # a pay band while a lone "$95,000" is as likely to be a ceiling mentioned
    # in passing.
    best: tuple[int, int, float | None, float | None, str] | None = None
    index = 0
    while index < len(amounts):
        low = amounts[index]
        high = amounts[index + 1] if index + 1 < len(amounts) else None
        if high is not None and _RANGE_SEP_RE.match(text[low.end : high.start]):
            reading = _range_reading(text, low, high)
            index += 2
            rank = 0
        else:
            reading = _single_reading(text, low)
            index += 1
            rank = 1
        if reading is None:
            continue
        candidate = (rank, low.start, reading[0], reading[1], reading[2])
        if best is None or (candidate[0], candidate[1]) < (best[0], best[1]):
            best = candidate
    if best is None:
        return None
    return best[2], best[3], best[4]


def _money_candidates(text: str, require_cue: bool) -> list[_Amount]:
    """Numbers in ``text`` that could plausibly be money, in document order."""
    retirement_spans = [m.span() for m in _RETIREMENT_RE.finditer(text)]
    candidates: list[_Amount] = []
    for match in _AMOUNT_RE.finditer(text):
        start, end = match.span()
        if any(span[0] < end and start < span[1] for span in retirement_spans):
            continue
        if _UNIT_NOUN_RE.match(text[end : end + 24]):
            continue
        if _VETO_BEFORE_RE.search(text[max(0, start - 40) : start]):
            continue
        if _VETO_AFTER_RE.match(text[end : end + 30]):
            continue

        dollar = match.group("dollar") is not None
        kilo = match.group("k") is not None
        raw = match.group("num")
        try:
            value = float(raw.replace(",", ""))
        except ValueError:  # pragma: no cover - regex cannot produce this
            continue
        if kilo:
            value *= 1000.0
        if require_cue and not (dollar or kilo):
            window = text[max(0, start - _SALARY_CUE_BEFORE) : end + _SALARY_CUE_AFTER]
            if not _SALARY_CUE_RE.search(window):
                continue
        candidates.append(_Amount(value, start, end, dollar, kilo))
    return candidates


def _range_reading(
    text: str, low: _Amount, high: _Amount
) -> tuple[float, float, str] | None:
    """Validate a two-sided range, or reject it."""
    low_value, high_value = low.value, high.value
    # "$75-$95K" abbreviates both sides but only marks the second.
    if high.kilo and not low.kilo and low_value < 1000:
        low_value *= 1000.0
    if low.kilo and not high.kilo and high_value < 1000:
        high_value *= 1000.0
    if low_value > high_value:
        low_value, high_value = high_value, low_value

    period = _period_for(text, low.start, high.end) or _period_from_magnitude(high_value)
    if period is None:
        return None
    if not (_in_bounds(low_value, period) and _in_bounds(high_value, period)):
        return None
    return round(low_value, 2), round(high_value, 2), period


def _single_reading(
    text: str, amount: _Amount
) -> tuple[float | None, float | None, str] | None:
    """Validate a lone figure, honouring "starting at" / "up to" phrasing.

    An unqualified single figure fills both ends of the range. It is a real
    data point about what the job pays, and a degenerate range keeps every
    downstream average from having to special-case ``None``.
    """
    period = _period_for(text, amount.start, amount.end) or _period_from_magnitude(amount.value)
    if period is None or not _in_bounds(amount.value, period):
        return None
    value = round(amount.value, 2)
    before = text[max(0, amount.start - _CUE_LOOKBACK) : amount.start]
    if _MAX_ONLY_RE.search(before):
        return None, value, period
    if _MIN_ONLY_RE.search(before):
        return value, None, period
    return value, value, period


def _period_for(text: str, start: int, end: int) -> str | None:
    """Pay period from the nearest period word, if any.

    Nearest rather than first: "$45.00/hour ($93,600 annually)" mentions both,
    and each figure belongs to the label sitting against it.
    """
    window_start = max(0, start - 100)
    window = text[window_start : end + 50]
    best: tuple[int, str] | None = None
    for period, pattern in (("year", _PERIOD_YEAR_RE), ("hour", _PERIOD_HOUR_RE)):
        for match in pattern.finditer(window):
            position = window_start + match.start()
            if start <= position <= end:
                distance = 0
            else:
                distance = min(abs(position - end), abs(start - position))
            if best is None or distance < best[0]:
                best = (distance, period)
    return best[1] if best else None


def _period_from_magnitude(value: float) -> str | None:
    """Last-resort period inference. Ambiguous magnitudes are dropped."""
    if value >= _MAGNITUDE_YEAR_FLOOR:
        return "year"
    if value <= _MAGNITUDE_HOUR_CEILING:
        return "hour"
    return None


def _in_bounds(value: float, period: str) -> bool:
    """Reject figures that cannot be pay at the stated period.

    This is the guard that kills a bare "2026" (a fiscal year, not a salary),
    a "$1,200/hour" typo, and a "$45 annually" mislabel.
    """
    if period == "hour":
        return _HOURLY_FLOOR <= value <= _HOURLY_CEILING
    return _ANNUAL_FLOOR <= value <= _ANNUAL_CEILING
