"""Corpus analytics: what the archive knows about the field as a whole.

The board answers "what is open right now". The archive answers "what did this
posting say in March". Neither answers the questions the people running a
tactical human performance community actually ask: who is hiring, where, for
which credentials, and at what pay.

Three specific problems stand between those questions and the corpus, and this
module exists to solve them.

*Syndication.* One job posted to an employer's ATS and to USAJOBS, re-archived
every time its description is edited, is many records and one job. Counting
records would claim a single Fort Liberty contract is the busiest hiring market
in the country. Everything per-job here is computed over one row per
``fingerprint`` -- the newest revision winning -- so a job counts once no matter
how loudly the boards repeat it. The gap between ``postings`` and
``unique_jobs`` is kept and reported, because that gap *is* the syndication and
re-posting rate, which is worth knowing on its own.

*Incommensurable pay.* Federal listings quote an hourly rate, contractors quote
an annual band, a few quote a monthly figure. Dropping $45/hr into the same
median as $95,000/yr yields a number that describes nothing. Every salary is
annualized before it is compared -- see :data:`PERIOD_FACTORS`.

*Absent and malformed data.* The corpus is scraped, so any field can be missing,
null, or the wrong type on any record. An analytics layer that raises on one bad
row is useless against real input, so nothing here raises: an unreadable value
is not counted, and an empty corpus produces a fully-formed report of zeros.

Extraction is deliberately *not* done here. Salary, certifications, clearance,
and installation are read out of ``enrichment`` exactly as ``enrich.py`` left
them; this module counts, it does not mine description text. That keeps one
owner for "what does this posting say" and a different one for "what does the
corpus mean". A corpus whose records were never enriched therefore reports zero
salaries rather than quietly re-deriving them by a second, divergent set of
rules.

A note on shares
----------------
Every ``share`` is a fraction of the population that *could* have that value,
not of the whole corpus: certification share is out of jobs listing any
certification, discipline share is out of jobs carrying any discipline tag.
Sharing out of the whole corpus would make every number a statement about
enrichment coverage rather than about the field. Because a job can carry several
disciplines or certifications, shares within one facet may total more than 1.0.
"""

from __future__ import annotations

import math
import re
import statistics
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping, Sequence

from .archive import ARCHIVED_AT

HOURS_PER_YEAR = 2080.0
"""40 hours x 52 weeks. The conversion the whole salary section rests on."""

PERIOD_FACTORS: dict[str, float] = {
    "hour": HOURS_PER_YEAR,
    "hourly": HOURS_PER_YEAR,
    "hr": HOURS_PER_YEAR,
    "day": 260.0,  # working days, not calendar days
    "daily": 260.0,
    "week": 52.0,
    "weekly": 52.0,
    "biweekly": 26.0,
    "semimonthly": 24.0,
    "month": 12.0,
    "monthly": 12.0,
    "year": 1.0,
    "yearly": 1.0,
    "annual": 1.0,
    "annually": 1.0,
    "salary": 1.0,
}
"""Multiplier that turns a figure quoted for one period into an annual figure.

Exact spellings only. Anything else goes through :data:`_PERIOD_PATTERNS`,
which is where the ordering that this table cannot express lives.
"""

_PERIOD_PATTERNS: tuple[tuple[re.Pattern[str], float], ...] = (
    # Ordered by specificity rather than by frequency, because several of these
    # labels contain each other and the containing one is always the wrong
    # answer. "bi-weekly" contains "weekly" (reading it as weekly doubles the
    # figure), "semi-monthly" contains "monthly", and "salary per hour" -- which
    # real feeds do emit -- contains "salary". The precise period therefore has
    # to be tested before the term it is spelled with.
    (re.compile(r"\bbi[\s\-]?weekly\b|\bfortnight\w*\b|\bevery\s+two\s+weeks\b"), 26.0),
    (re.compile(r"\bsemi[\s\-]?monthly\b|\btwice\s+(?:a|per)\s+month\b"), 24.0),
    (re.compile(r"\bhours?\b|\bhourly\b|\bhrs?\b"), HOURS_PER_YEAR),
    (re.compile(r"\bdays?\b|\bdaily\b|\bdiem\b"), 260.0),
    (re.compile(r"\bweeks?\b|\bweekly\b"), 52.0),
    (re.compile(r"\bmonths?\b|\bmonthly\b"), 12.0),
    (
        re.compile(
            r"\byears?\b|\byearly\b|\byrs?\b|\bannual\w*\b|\bannum\b|\bsalar(?:y|ied)\b"
        ),
        1.0,
    ),
)
"""Period spellings that the exact table cannot hold, most specific first."""

HOURLY_CEILING = 250.0
"""Below this, an unlabeled figure is read as an hourly rate.

Federal postings routinely omit the period. Nobody in this field is paid $95 a
year and nobody is paid $95,000 an hour, so magnitude is a safe tiebreaker --
but only in that one direction, which is why an unlabeled figure above the
ceiling is assumed annual rather than guessed at further.
"""

MIN_PLAUSIBLE_ANNUAL = 5_000.0
MAX_PLAUSIBLE_ANNUAL = 2_000_000.0
"""Bounds that reject parse artifacts, not low or high salaries.

A "$1.00" placeholder or a phone number scraped as a salary would drag a median
much further than any real outlier can. The band is deliberately wide: the job
here is to drop garbage, not to editorialize about what a coach should earn.
"""

TREND_WINDOW_DAYS = 90
"""Half of the trend comparison, in days.

Long enough that one busy week does not read as a hiring surge, short enough
that a new contract award still shows up inside a quarter.
"""

MIN_TREND_JOBS = 3
"""Below this many dated jobs, trends are suppressed entirely.

"Fastest growing employer" computed off two data points is not a trend, it is a
coin flip presented with a decimal point.
"""

MAX_TIMELINE_MONTHS = 120
"""Cap on timeline length. One bad 1970 date would otherwise emit 600 buckets."""

DISCIPLINE_TAGS: tuple[str, ...] = (
    "strength-conditioning",
    "sports-medicine",
    "nutrition",
    "cognitive",
    "sport-science",
    "research",
    "leadership",
)
"""Discipline facets, mirroring the tag vocabulary ``classify.py`` assigns.

Duplicated rather than imported because ``classify`` builds these inside its
tagging function; if that vocabulary grows, this tuple is the one place here
that needs to follow it. Keep it in sync with ``classify._derive_tags`` --
a slug missing here is not merely absent from ``by_discipline``, it is also
absent from the *denominator* every discipline share is taken over, so
forgetting one silently inflates the numbers for all the others.
"""

DOMAIN_TAGS: tuple[str, ...] = ("military", "sof", "first-responder", "training-pipeline")
"""Population facets. A job can be several -- an H2F role at a SOF unit is both.

Same sync obligation as :data:`DISCIPLINE_TAGS`. ``remote`` is deliberately not
here: ``classify`` emits it alongside these, but it is a work arrangement rather
than a population, and it already has its own top-level section.
"""

US_STATES: dict[str, str] = {
    "alabama": "AL",
    "alaska": "AK",
    "arizona": "AZ",
    "arkansas": "AR",
    "california": "CA",
    "colorado": "CO",
    "connecticut": "CT",
    "delaware": "DE",
    "district of columbia": "DC",
    "florida": "FL",
    "georgia": "GA",
    "hawaii": "HI",
    "idaho": "ID",
    "illinois": "IL",
    "indiana": "IN",
    "iowa": "IA",
    "kansas": "KS",
    "kentucky": "KY",
    "louisiana": "LA",
    "maine": "ME",
    "maryland": "MD",
    "massachusetts": "MA",
    "michigan": "MI",
    "minnesota": "MN",
    "mississippi": "MS",
    "missouri": "MO",
    "montana": "MT",
    "nebraska": "NE",
    "nevada": "NV",
    "new hampshire": "NH",
    "new jersey": "NJ",
    "new mexico": "NM",
    "new york": "NY",
    "north carolina": "NC",
    "north dakota": "ND",
    "ohio": "OH",
    "oklahoma": "OK",
    "oregon": "OR",
    "pennsylvania": "PA",
    "rhode island": "RI",
    "south carolina": "SC",
    "south dakota": "SD",
    "tennessee": "TN",
    "texas": "TX",
    "utah": "UT",
    "vermont": "VT",
    "virginia": "VA",
    "washington": "WA",
    "west virginia": "WV",
    "wisconsin": "WI",
    "wyoming": "WY",
    # Territories carry real installations (Fort Buchanan, Andersen AFB).
    "puerto rico": "PR",
    "guam": "GU",
    "virgin islands": "VI",
    "american samoa": "AS",
    "northern mariana islands": "MP",
}

STATE_CODES: frozenset[str] = frozenset(US_STATES.values())

# Longest first, so "west virginia" is not read as "virginia" and
# "district of columbia" is not read as "columbia".
_STATE_NAME_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = tuple(
    (re.compile(rf"\b{re.escape(name)}\b"), US_STATES[name])
    for name in sorted(US_STATES, key=lambda name: (-len(name), name))
)

# Two uppercase letters standing alone. Case matters: matching case-insensitively
# anywhere in the string turns "Remote in US" into Indiana and "hiring or not"
# into Oregon, because half the state codes are also English words.
_UPPER_CODE = re.compile(r"\b[A-Z]{2}\b")

# What may legitimately follow a state code: end of field, the next comma, a ZIP,
# or a country. This is what separates "Fort Bragg NC USA" from the "OR" in
# "REMOTE - US OR CANADA" -- an all-caps field makes every English preposition
# look like a state code, so position, not just casing, has to carry the weight.
_TRAILING_NOISE = re.compile(r"^(?:,|\d{5}(?:-\d{4})?\b|USA?\b|United\s+States\b)", re.I)

# Strings that mean "no" when a scraper writes a boolean as text. Bare bool()
# would read "false" as True, which would report the entire corpus as remote.
_FALSEY_TEXT: frozenset[str] = frozenset({"", "false", "f", "no", "n", "0", "none", "null", "off"})

# Sorts before any real timestamp, so an undated record loses to a dated one
# instead of poisoning the comparison.
_UNDATED = datetime(1, 1, 1, tzinfo=timezone.utc)


# --------------------------------------------------------------------------
# Tolerant readers. Every one of these takes "anything at all" and returns
# either a usable value or nothing -- no exceptions leave this section.
# --------------------------------------------------------------------------


def _clean(value: Any) -> str:
    """Collapse whitespace in a string-ish value; anything else becomes ""."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _as_float(value: Any) -> float | None:
    """Read a number out of an int, float, or a string like ``"$95,000"``."""
    if isinstance(value, bool):  # bool is an int subclass; a flag is not a salary
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(value) else None
    if isinstance(value, str):
        stripped = re.sub(r"[^0-9.\-]", "", value)
        if not stripped or stripped in {"-", ".", "-."}:
            return None
        try:
            return float(stripped)
        except ValueError:
            return None
    return None


def _as_strings(value: Any) -> list[str]:
    """Read a list-of-strings field, tolerating a bare string or junk entries."""
    if isinstance(value, str):
        cleaned = _clean(value)
        return [cleaned] if cleaned else []
    if isinstance(value, (list, tuple, set)):
        return [_clean(item) for item in value if _clean(item)]
    return []


def _as_mapping(value: Any) -> Mapping[str, Any]:
    """``enrichment`` is free-form and frequently absent. Never let it be None."""
    return value if isinstance(value, Mapping) else {}


def _as_records(value: Any) -> Sequence[Any]:
    """A corpus is a sequence of rows; anything else is an empty corpus.

    ``Archive.records()`` returns a list, but a caller reading a status file
    that failed to parse holds ``None``, and "the report is empty" is a far more
    useful answer there than a ``TypeError`` out of a loop header.
    """
    return value if isinstance(value, (list, tuple)) else []


def _as_bool(value: Any) -> bool:
    """Truthiness that survives a scraper writing its booleans as strings."""
    if isinstance(value, str):
        return _clean(value).casefold() not in _FALSEY_TEXT
    return bool(value)


def _unique_labels(values: Iterable[str]) -> tuple[str, ...]:
    """Dedupe labels case-insensitively, keeping the first spelling seen.

    Upper-casing instead would be simpler and wrong: ``enrich.py`` emits
    canonical, deliberately mixed-case credentials -- ``PhD``, ``TSAC-F``,
    ``NSCA-CPT`` -- and normalizing them here would print ``PHD`` in every
    report the module feeds. The comparison still has to ignore case, because a
    description naming "CSCS" in the requirements and "cscs" in the preferred
    section is asking for one credential, not two.
    """
    seen: dict[str, str] = {}
    for value in values:
        seen.setdefault(value.casefold(), value)
    return tuple(sorted(seen.values(), key=lambda label: (label.casefold(), label)))


def _parse_when(value: Any) -> datetime | None:
    """Parse an ISO timestamp to UTC, returning None for anything unusable."""
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    try:
        stamp = datetime.fromisoformat(text)
    except ValueError:
        # Dates arrive from a dozen feeds; a leading date is better than nothing.
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", text)
        if not match:
            return None
        try:
            stamp = datetime(int(match[1]), int(match[2]), int(match[3]))
        except ValueError:
            return None
    if stamp.tzinfo is None:
        stamp = stamp.replace(tzinfo=timezone.utc)
    try:
        return stamp.astimezone(timezone.utc)
    except (OverflowError, OSError):
        # A year-1 or year-9999 stamp carrying a UTC offset cannot be shifted
        # into UTC without leaving the representable range, and the error it
        # raises is OverflowError rather than ValueError. ``archive.py`` guards
        # the identical call; one absurd date in one feed row must not be able
        # to take down the whole report.
        return None


# --------------------------------------------------------------------------
# Salary
# --------------------------------------------------------------------------


def annualized_salary(enrichment: Mapping[str, Any] | None) -> float | None:
    """Annual-equivalent pay for one job, or None if it did not publish any.

    Uses the midpoint when a band is given, because the midpoint is what a
    reader means by "what does this pay" -- taking the minimum would understate
    every banded federal posting relative to a contractor quoting one number.

    Exposed publicly (rather than kept private to :func:`build_insights`)
    because "annualize this posting" is the single assumption the whole salary
    section rests on, and a caller comparing two individual jobs needs to apply
    exactly the same rule.
    """
    data = _as_mapping(enrichment)
    low = _as_float(data.get("salary_min"))
    high = _as_float(data.get("salary_max"))
    quoted = [value for value in (low, high) if value is not None and value > 0]
    if not quoted:
        return None

    midpoint = sum(quoted) / len(quoted)
    factor = _period_factor(data.get("salary_period"), midpoint)
    annual = midpoint * factor
    if not MIN_PLAUSIBLE_ANNUAL <= annual <= MAX_PLAUSIBLE_ANNUAL:
        return None
    return round(annual, 2)


def _period_factor(period: Any, midpoint: float) -> float:
    """Multiplier to annualize ``midpoint``, inferring the period if unlabeled.

    Exact spelling first, then :data:`_PERIOD_PATTERNS` most-specific-first.
    Scanning left to right for the first recognizable *word* -- the obvious
    implementation -- gets "salary per hour" wrong by a factor of 2080 and
    "bi-weekly" wrong by a factor of two, because in both the misleading term
    comes first.
    """
    text = _clean(period).lower()
    if text in PERIOD_FACTORS:
        return PERIOD_FACTORS[text]
    for pattern, factor in _PERIOD_PATTERNS:
        if pattern.search(text):
            return factor
    return HOURS_PER_YEAR if midpoint < HOURLY_CEILING else 1.0


def _percentile(values: Sequence[float], quantile: float) -> float:
    """Linear-interpolated percentile, the inclusive method.

    Written out rather than taken from ``statistics.quantiles`` because that
    function raises on a single data point, and a corpus with exactly one
    salary is a completely normal state for a young board -- reporting that one
    number as the whole distribution is more useful than an exception.
    """
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * quantile
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    weight = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * weight


def _salary_stats(values: Sequence[float]) -> dict[str, Any]:
    """Distribution summary for a set of already-annualized figures."""
    if not values:
        return {"count": 0, "min": None, "max": None, "median": None, "p25": None, "p75": None}
    return {
        "count": len(values),
        "min": round(min(values), 2),
        "max": round(max(values), 2),
        "median": round(_percentile(values, 0.5), 2),
        "p25": round(_percentile(values, 0.25), 2),
        "p75": round(_percentile(values, 0.75), 2),
    }


def _median_or_none(values: Sequence[float]) -> float | None:
    return round(statistics.median(values), 2) if values else None


# --------------------------------------------------------------------------
# Location
# --------------------------------------------------------------------------


def state_code(location: Any) -> str | None:
    """Two-letter US state for a free-text location, or None.

    Handles the three shapes real boards emit -- ``"Fort Bragg, NC"``,
    ``"Coronado, CA 92118"``, ``"Fayetteville, North Carolina"`` -- and refuses
    to guess on the rest. ``"Remote"`` has no state and must not acquire one.

    The passes run code-first on purpose: ``"Washington, DC"`` is the District,
    not Washington state, and only the trailing code says so.
    """
    text = _clean(location).replace(".", "")
    if not text:
        return None

    # 1. An uppercase code in a position a state code actually occupies,
    #    rightmost first: "Fort Bragg, NC 28310, US" is NC, and a leading
    #    "JB Lewis-McChord" must not beat the real state. Position is required
    #    as well as casing because an all-caps field ("REMOTE - US OR CANADA")
    #    turns every English preposition into a candidate.
    anchored = _anchored_codes(text)
    if anchored:
        return anchored[-1]

    # 2. A spelled-out state name, searching comma segments right to left. The
    #    trailing segment is where a location puts its state, and taking the
    #    longest name found anywhere instead reads "New York Life, Dallas,
    #    Texas" as New York. Within a segment the longest name still wins, so
    #    "West Virginia" is not read as Virginia.
    segments = [segment for segment in text.lower().split(",") if segment.strip()]
    for segment in reversed(segments):
        for pattern, code in _STATE_NAME_PATTERNS:
            if pattern.search(segment):
                return code

    # 3. A lowercase code, but only as the final word of the final segment.
    #    Scanning further left would read "remote in us" as Indiana.
    words = re.findall(r"[a-z]+", segments[-1]) if segments else []
    if words and len(words[-1]) == 2 and words[-1].upper() in STATE_CODES:
        return words[-1].upper()
    return None


def _anchored_codes(text: str) -> list[str]:
    """Uppercase state codes sitting where a state code belongs, in order.

    A code qualifies when a comma introduces it ("Fort Bragg, NC") or when only
    a ZIP, a country, or nothing at all follows it ("Fort Bragg NC 28310").
    Everything else is a two-letter word that happens to be spelled like a
    state, which is most of them: OR, IN, ME, HI, OK, AS, DE and PA are all
    ordinary English or abbreviations of something else.
    """
    codes: list[str] = []
    for match in _UPPER_CODE.finditer(text):
        token = match.group()
        if token not in STATE_CODES:
            continue
        before = text[: match.start()].rstrip()
        after = text[match.end() :].strip()
        if before.endswith(",") or not after or _TRAILING_NOISE.match(after):
            codes.append(token)
    return codes


# --------------------------------------------------------------------------
# The deduplicated view of one job
# --------------------------------------------------------------------------


@dataclass(slots=True)
class _Job:
    """One job as the analytics layer sees it: read once, counted many times.

    Flattened out of the archive record up front so that no counting pass below
    has to re-do the tolerant-reading work, and so a malformed record fails in
    exactly one place instead of in fifteen.
    """

    key: str
    employer: str
    title: str
    location: str
    state: str | None
    remote: bool
    posted_at: datetime | None
    disciplines: tuple[str, ...]
    domains: tuple[str, ...]
    certifications: tuple[str, ...] = ()
    clearance: str = ""
    installation: str = ""
    branch: str = ""
    salary: float | None = None


def _record_key(record: Mapping[str, Any], index: int) -> str:
    """Dedupe key: fingerprint, falling back so nothing silently merges.

    ``fingerprint`` is the whole point -- it is what makes one job posted to two
    boards one job. When it is missing the record still must not be collapsed
    into an unrelated one, so identity, then url, then position stand in.
    """
    for candidate in (record.get("fingerprint"), record.get("id"), record.get("url")):
        cleaned = _clean(candidate)
        if cleaned:
            return cleaned
    return f"#{index}"


def _to_job(record: Mapping[str, Any], key: str) -> _Job:
    enrichment = _as_mapping(record.get("enrichment"))
    tags = {tag.lower() for tag in _as_strings(record.get("tags"))}
    location = _clean(record.get("location"))
    # Certifications are deduped inside one job: a description listing "CSCS"
    # in the requirements and again in the preferred section is one job asking
    # for CSCS, not two. Spelling is left as enrich.py canonicalized it.
    certifications = _unique_labels(_as_strings(enrichment.get("certifications")))
    return _Job(
        key=key,
        employer=_clean(record.get("employer")),
        title=_clean(record.get("title")),
        location=location,
        state=state_code(location),
        remote=_as_bool(record.get("remote")),
        posted_at=_parse_when(record.get("posted_at")),
        disciplines=tuple(tag for tag in DISCIPLINE_TAGS if tag in tags),
        domains=tuple(tag for tag in DOMAIN_TAGS if tag in tags),
        certifications=certifications,
        clearance=_clean(enrichment.get("clearance")),
        installation=_clean(enrichment.get("installation")),
        branch=_clean(enrichment.get("service_branch")),
        salary=annualized_salary(enrichment),
    )


def _unique_jobs(records: Sequence[Mapping[str, Any]]) -> list[_Job]:
    """Collapse the corpus to one row per job, newest archived revision winning.

    Matches ``Archive.latest_by_identity`` in spirit but keys on *fingerprint*
    rather than identity, because two syndicated copies of one job have two
    identities and must still count once.
    """
    chosen: dict[str, tuple[datetime, int, Mapping[str, Any]]] = {}
    for index, record in enumerate(records):
        key = _record_key(record, index)
        when = _parse_when(record.get(ARCHIVED_AT)) or _UNDATED
        current = chosen.get(key)
        # File order breaks ties: append order is the only other thing the
        # archive actually records about which revision came last.
        if current is not None and (when, index) < (current[0], current[1]):
            continue
        chosen[key] = (when, index, record)
    return [_to_job(record, key) for key, (_, _, record) in chosen.items()]


# --------------------------------------------------------------------------
# Counting helpers
# --------------------------------------------------------------------------


def _tally(values: Iterable[str]) -> list[tuple[str, int]]:
    """Count case-insensitively, display the first spelling seen.

    Two boards will write "US Army H2F" and "US ARMY H2F" for the same employer;
    counting them apart would split the one number a reader came here for.
    Sorted by count then name so a committed report does not churn on ties.
    """
    counts: Counter[str] = Counter()
    display: dict[str, str] = {}
    for value in values:
        cleaned = _clean(value)
        if not cleaned:
            continue
        key = cleaned.casefold()
        display.setdefault(key, cleaned)
        counts[key] += 1
    return sorted(
        ((display[key], count) for key, count in counts.items()),
        key=lambda item: (-item[1], item[0]),
    )


def _top(items: list[Any], top_n: int) -> list[Any]:
    """Trim a ranked list. A non-positive ``top_n`` means "everything"."""
    return items if top_n <= 0 else items[:top_n]


def _share(count: int, denominator: int) -> float:
    return round(count / denominator, 4) if denominator else 0.0


def _month(stamp: datetime) -> str:
    return f"{stamp.year:04d}-{stamp.month:02d}"


def _month_range(first: datetime, last: datetime) -> list[str]:
    """Every month from ``first`` to ``last`` inclusive, gaps included.

    A month in which nobody hired is a fact about the field, not a missing row,
    and a consumer plotting this needs an even x-axis to see it.

    Trimmed to the most recent :data:`MAX_TIMELINE_MONTHS`. One posting misdated
    to 1970 -- and feeds do emit those -- would otherwise generate six hundred
    empty buckets ahead of the data anybody wanted to look at. The recent end is
    the end that gets read, so that is the end that survives.
    """
    span = (last.year - first.year) * 12 + (last.month - first.month)
    months: list[str] = []
    for offset in range(max(0, span - MAX_TIMELINE_MONTHS + 1), span + 1):
        years, month = divmod(first.month - 1 + offset, 12)
        months.append(f"{first.year + years:04d}-{month + 1:02d}")
    return months


# --------------------------------------------------------------------------
# The report
# --------------------------------------------------------------------------


def build_insights(records: list[dict[str, Any]], *, top_n: int = 15) -> dict[str, Any]:
    """Summarize an archived corpus. Never raises; JSON-serializable throughout.

    ``records`` are archive rows as produced by ``JobPosting.to_archive_dict``.
    ``top_n`` trims the long-tail rankings (employers, installations, titles);
    pass 0 or less for untrimmed. The timeline is never trimmed -- a truncated
    time series is a misleading one.
    """
    usable = [record for record in _as_records(records) if isinstance(record, Mapping)]
    jobs = _unique_jobs(usable)

    salaries = [job.salary for job in jobs if job.salary is not None]
    dated = [job for job in jobs if job.posted_at is not None]
    posted = sorted(job.posted_at for job in dated)  # type: ignore[misc]

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "postings": len(usable),
            "employers": len({job.employer.casefold() for job in jobs if job.employer}),
            "unique_jobs": len(jobs),
            "with_salary": len(salaries),
            "date_span": {
                "earliest": posted[0].isoformat() if posted else None,
                "latest": posted[-1].isoformat() if posted else None,
            },
        },
        "by_employer": _by_employer(jobs, top_n),
        "by_discipline": _by_facet(jobs, DISCIPLINE_TAGS, "disciplines", top_n),
        # Domains get no median_salary: "what does military pay" is a question
        # about a population, not a job, and the answer would be the corpus
        # median wearing a disguise.
        "by_domain": _by_facet(jobs, DOMAIN_TAGS, "domains", top_n, with_salary=False),
        "by_branch": [
            {"name": name, "count": count}
            for name, count in _top(_tally(job.branch for job in jobs), top_n)
        ],
        "by_installation": [
            {"name": name, "count": count}
            for name, count in _top(_tally(job.installation for job in jobs), top_n)
        ],
        "by_state": [
            {"code": code, "count": count}
            for code, count in _top(_tally(job.state or "" for job in jobs), top_n)
        ],
        "certifications": _certifications(jobs, top_n),
        "clearances": [
            {"name": name, "count": count}
            for name, count in _top(_tally(job.clearance for job in jobs), top_n)
        ],
        "salary": _salary_section(jobs, salaries),
        "remote": {
            "count": sum(1 for job in jobs if job.remote),
            "share": _share(sum(1 for job in jobs if job.remote), len(jobs)),
        },
        "timeline": _timeline(dated),
        "trends": _trends(dated, top_n),
        "top_titles": [
            {"title": title, "count": count}
            for title, count in _top(_tally(job.title for job in jobs), top_n)
        ],
    }


def _by_employer(jobs: Sequence[_Job], top_n: int) -> list[dict[str, Any]]:
    """Who is hiring, what they hire for, and what they pay."""
    groups: dict[str, list[_Job]] = {}
    display: dict[str, str] = {}
    for job in jobs:
        if not job.employer:
            continue
        key = job.employer.casefold()
        display.setdefault(key, job.employer)
        groups.setdefault(key, []).append(job)

    entries = [
        {
            "name": display[key],
            "count": len(members),
            "disciplines": [
                name
                for name, _ in _tally(
                    discipline for member in members for discipline in member.disciplines
                )
            ],
            "median_salary": _median_or_none(
                [member.salary for member in members if member.salary is not None]
            ),
        }
        for key, members in groups.items()
    ]
    entries.sort(key=lambda entry: (-entry["count"], entry["name"]))
    return _top(entries, top_n)


def _by_facet(
    jobs: Sequence[_Job],
    vocabulary: Sequence[str],
    attribute: str,
    top_n: int,
    *,
    with_salary: bool = True,
) -> list[dict[str, Any]]:
    """Count a multi-valued tag facet, sharing out of jobs that carry any of it."""
    tagged = [job for job in jobs if getattr(job, attribute)]
    entries: list[dict[str, Any]] = []
    for name in vocabulary:
        members = [job for job in jobs if name in getattr(job, attribute)]
        if not members:
            continue
        entry: dict[str, Any] = {
            "name": name,
            "count": len(members),
            "share": _share(len(members), len(tagged)),
        }
        if with_salary:
            entry["median_salary"] = _median_or_none(
                [member.salary for member in members if member.salary is not None]
            )
        entries.append(entry)
    entries.sort(key=lambda entry: (-entry["count"], entry["name"]))
    return _top(entries, top_n)


def _certifications(jobs: Sequence[_Job], top_n: int) -> list[dict[str, Any]]:
    """Which credentials the field is actually asking for.

    Shared out of jobs that name *any* certification, so the number answers
    "when an employer states requirements, how often is CSCS one of them" rather
    than "how much of the corpus has been enriched".
    """
    with_any = sum(1 for job in jobs if job.certifications)
    counts = _tally(cert for job in jobs for cert in job.certifications)
    return _top(
        [
            {"name": name, "count": count, "share": _share(count, with_any)}
            for name, count in counts
        ],
        top_n,
    )


def _salary_section(jobs: Sequence[_Job], salaries: Sequence[float]) -> dict[str, Any]:
    """Annualized pay overall and per discipline."""
    section = _salary_stats(salaries)
    by_discipline: dict[str, Any] = {}
    for name in DISCIPLINE_TAGS:
        values = [
            job.salary
            for job in jobs
            if name in job.disciplines and job.salary is not None
        ]
        if values:
            by_discipline[name] = _salary_stats(values)
    section["by_discipline"] = by_discipline
    return section


def _timeline(dated: Sequence[_Job]) -> list[dict[str, Any]]:
    """Jobs per calendar month of ``posted_at``, oldest first, gaps filled."""
    if not dated:
        return []
    stamps = [job.posted_at for job in dated if job.posted_at is not None]
    counts = Counter(_month(stamp) for stamp in stamps)
    return [
        {"month": month, "count": counts.get(month, 0)}
        for month in _month_range(min(stamps), max(stamps))
    ]


def _trends(dated: Sequence[_Job], top_n: int) -> dict[str, Any]:
    """What is accelerating: employers posting more, credentials appearing more.

    Compares the most recent :data:`TREND_WINDOW_DAYS` against the window before
    it, anchored to the newest posting in the corpus rather than to wall-clock
    now. Anchoring to now would report a historical corpus as universally
    collapsing simply because it was analyzed later.
    """
    empty: dict[str, Any] = {
        "window_days": TREND_WINDOW_DAYS,
        "pivot": None,
        "fastest_growing_employers": [],
        "emerging_certifications": [],
    }
    if len(dated) < MIN_TREND_JOBS:
        return empty

    stamps = [job.posted_at for job in dated if job.posted_at is not None]
    pivot = max(stamps) - timedelta(days=TREND_WINDOW_DAYS)
    start = pivot - timedelta(days=TREND_WINDOW_DAYS)
    recent = [job for job in dated if job.posted_at is not None and job.posted_at >= pivot]
    prior = [
        job for job in dated if job.posted_at is not None and start <= job.posted_at < pivot
    ]

    return {
        "window_days": TREND_WINDOW_DAYS,
        "pivot": pivot.isoformat(),
        "fastest_growing_employers": _growth(
            [job.employer for job in recent],
            [job.employer for job in prior],
            top_n,
        ),
        "emerging_certifications": _growth(
            [cert for job in recent for cert in job.certifications],
            [cert for job in prior for cert in job.certifications],
            top_n,
        ),
    }


def _growth(recent: Iterable[str], prior: Iterable[str], top_n: int) -> list[dict[str, Any]]:
    """Names that appear more in ``recent`` than in ``prior``, biggest gain first.

    The two windows are joined on the casefolded name, not on the spelling
    ``_tally`` chose to display. Joining on the display spelling looks correct
    and quietly invents growth: a board that wrote "US ARMY H2F" in February and
    "US Army H2F" in June would find no prior row for the June spelling and be
    reported as the fastest-growing employer in the corpus on a flat headcount.
    """
    now = _tally(recent)
    before = {name.casefold(): count for name, count in _tally(prior)}
    entries = [
        {
            "name": name,
            "recent": count,
            "previous": before.get(name.casefold(), 0),
            "change": count - before.get(name.casefold(), 0),
        }
        for name, count in now
        if count > before.get(name.casefold(), 0)
    ]
    entries.sort(key=lambda entry: (-entry["change"], -entry["recent"], entry["name"]))
    return _top(entries, top_n)


# --------------------------------------------------------------------------
# Terminal digest
# --------------------------------------------------------------------------

_BAR_WIDTH = 24
"""Widest timeline bar. Keeps every line inside an 80-column terminal."""

_RECENT_MONTHS = 12
"""How much of the timeline the digest shows. The JSON keeps all of it."""


def _money(value: Any) -> str:
    number = _as_float(value)
    return f"${number:,.0f}" if number is not None else "n/a"


def _percent(value: Any) -> str:
    number = _as_float(value)
    return f"{number * 100:.0f}%" if number is not None else "-"


def render_summary(insights: dict[str, Any]) -> str:
    """Compact plain-text digest of :func:`build_insights`, for a terminal.

    ASCII only and no color: this ends up in cron mail, CI logs, and terminals
    whose encoding nobody controls. Written defensively against its own input
    so that a partial report still prints the parts that are there.
    """
    data = insights if isinstance(insights, Mapping) else {}
    totals = _as_mapping(data.get("totals"))
    span = _as_mapping(totals.get("date_span"))
    lines: list[str] = [
        "TACTICAL HUMAN PERFORMANCE JOB INSIGHTS",
        f"generated {_clean(data.get('generated_at')) or 'unknown'}",
        "=" * 60,
        "",
    ]

    postings = int(_as_float(totals.get("postings")) or 0)
    unique = int(_as_float(totals.get("unique_jobs")) or 0)
    if not postings and not unique:
        lines.append("Corpus is empty -- nothing archived yet.")
        return "\n".join(lines) + "\n"

    lines.append("CORPUS")
    lines.append(
        f"  {postings} postings | {unique} unique jobs | "
        f"{int(_as_float(totals.get('employers')) or 0)} employers | "
        f"{int(_as_float(totals.get('with_salary')) or 0)} with salary"
    )
    earliest = _clean(span.get("earliest"))[:10]
    latest = _clean(span.get("latest"))[:10]
    if earliest or latest:
        lines.append(f"  posted between {earliest or '?'} and {latest or '?'}")
    remote = _as_mapping(data.get("remote"))
    lines.append(
        f"  remote-friendly {int(_as_float(remote.get('count')) or 0)} "
        f"({_percent(remote.get('share'))})"
    )
    # postings > unique is the syndication/re-post rate, not an error.
    if postings > unique:
        lines.append(f"  {postings - unique} records are re-posts or cross-board copies")
    lines.append("")

    salary = _as_mapping(data.get("salary"))
    if _as_float(salary.get("count")):
        lines.append(f"SALARY (annualized, n={int(_as_float(salary.get('count')) or 0)})")
        lines.append(
            f"  p25 {_money(salary.get('p25'))} | median {_money(salary.get('median'))} | "
            f"p75 {_money(salary.get('p75'))}"
        )
        lines.append(f"  range {_money(salary.get('min'))} - {_money(salary.get('max'))}")
        lines.append("")

    lines.extend(
        _block(
            "TOP EMPLOYERS",
            [
                (
                    _clean(entry.get("name")),
                    int(_as_float(entry.get("count")) or 0),
                    _money(entry.get("median_salary")) if entry.get("median_salary") else "",
                )
                for entry in _rows(data.get("by_employer"))
            ],
        )
    )
    lines.extend(
        _block(
            "DISCIPLINES",
            [
                (
                    _clean(entry.get("name")),
                    int(_as_float(entry.get("count")) or 0),
                    _percent(entry.get("share")),
                )
                for entry in _rows(data.get("by_discipline"))
            ],
        )
    )
    lines.extend(
        _block(
            "POPULATIONS",
            [
                (
                    _clean(entry.get("name")),
                    int(_as_float(entry.get("count")) or 0),
                    _percent(entry.get("share")),
                )
                for entry in _rows(data.get("by_domain"))
            ],
        )
    )
    lines.extend(
        _block(
            "CERTIFICATIONS",
            [
                (
                    _clean(entry.get("name")),
                    int(_as_float(entry.get("count")) or 0),
                    _percent(entry.get("share")),
                )
                for entry in _rows(data.get("certifications"))
            ],
        )
    )
    lines.extend(
        _block(
            "CLEARANCES",
            [
                (_clean(entry.get("name")), int(_as_float(entry.get("count")) or 0), "")
                for entry in _rows(data.get("clearances"))
            ],
        )
    )
    lines.extend(
        _block(
            "STATES",
            [
                (_clean(entry.get("code")), int(_as_float(entry.get("count")) or 0), "")
                for entry in _rows(data.get("by_state"))
            ],
        )
    )
    lines.extend(
        _block(
            "INSTALLATIONS",
            [
                (_clean(entry.get("name")), int(_as_float(entry.get("count")) or 0), "")
                for entry in _rows(data.get("by_installation"))
            ],
        )
    )
    lines.extend(
        _block(
            "TOP TITLES",
            [
                (_clean(entry.get("title")), int(_as_float(entry.get("count")) or 0), "")
                for entry in _rows(data.get("top_titles"))
            ],
        )
    )

    timeline = _rows(data.get("timeline"))[-_RECENT_MONTHS:]
    if timeline:
        counts = [int(_as_float(entry.get("count")) or 0) for entry in timeline]
        peak = max(counts) or 1
        lines.append(f"POSTINGS BY MONTH (last {len(timeline)})")
        for entry, count in zip(timeline, counts):
            bar = "#" * max(1 if count else 0, round(count / peak * _BAR_WIDTH))
            lines.append(f"  {_clean(entry.get('month')):<8}{count:>4}  {bar}")
        lines.append("")

    trends = _as_mapping(data.get("trends"))
    growing = _rows(trends.get("fastest_growing_employers"))
    emerging = _rows(trends.get("emerging_certifications"))
    if growing or emerging:
        window = int(_as_float(trends.get("window_days")) or 0)
        lines.append(f"TRENDING (last {window} days vs the {window} before)")
        for entry in growing[:5]:
            lines.append(
                f"  employer  {_clean(entry.get('name')):<32}"
                f"{int(_as_float(entry.get('previous')) or 0)} -> "
                f"{int(_as_float(entry.get('recent')) or 0)}"
            )
        for entry in emerging[:5]:
            lines.append(
                f"  cert      {_clean(entry.get('name')):<32}"
                f"{int(_as_float(entry.get('previous')) or 0)} -> "
                f"{int(_as_float(entry.get('recent')) or 0)}"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _rows(value: Any) -> list[Mapping[str, Any]]:
    """Read a list-of-entries section, skipping anything that is not a mapping."""
    if not isinstance(value, list):
        return []
    return [entry for entry in value if isinstance(entry, Mapping)]


def _block(heading: str, rows: Sequence[tuple[str, int, str]], limit: int = 8) -> list[str]:
    """One aligned section, or nothing at all if there is no data for it.

    Printing an empty heading tells the reader the corpus has that facet and it
    is zero, which is not true -- it usually means nothing enriched it.
    """
    usable = [row for row in rows if row[0]]
    if not usable:
        return []
    lines = [heading]
    for name, count, note in usable[:limit]:
        trimmed = name if len(name) <= 38 else name[:37] + "-"
        lines.append(f"  {count:>4}  {trimmed:<38}{note}".rstrip())
    lines.append("")
    return lines
