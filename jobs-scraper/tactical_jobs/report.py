"""Human-readable renderings of the corpus insights.

``insights.build_insights`` answers the questions; it does not answer them to
anybody. Its output is a nested dict of counts, shares, and percentiles, and
``insights.render_summary`` flattens that into a fixed-width block for cron mail.
Neither is what you forward to the people who actually run a tactical human
performance community: one is JSON, the other is a terminal artifact.

This module is the presentation layer, and it exists because presentation has
requirements that analytics deliberately refuses to take on.

*The reader is skimming.* A community manager opens this between meetings and
wants four things inside ten seconds: is the market up or down, who is hiring,
what credential is being asked for, and what it pays. So both renderers lead
with headline numbers and month-over-month movement, and every section below
that is ordered by how often somebody asks about it -- not by the order the keys
happen to sit in the insights dict.

*The HTML must be one file with no network.* The digest gets emailed, dropped in
a Slack message, committed to a repo, and opened from a laptop on an
installation network that blocks most of the internet. A CDN stylesheet or a
web font turns that into a broken page at exactly the moment somebody is trying
to read it. Everything -- CSS, charts, the whole document -- is inline, and there
is no ``script``, ``link``, ``img``, ``iframe``, ``src``, or ``href`` anywhere in
the output. The charts are therefore hand-built CSS bars and one inline SVG
sparkline computed from the data rather than handed to a charting library.

*Titles and employer names are hostile input.* They arrive from third-party ATS
feeds and USAJOBS. A posting titled ``Strength Coach <script>`` or an employer
named ``Smith & Sons "Tactical"`` is not hypothetical -- angle brackets and
ampersands show up in real feeds through bad HTML stripping upstream. Every
dynamic string in the HTML goes through :func:`html.escape` with ``quote=True``,
and no third-party string is ever interpolated into a ``style`` attribute: only
numbers this module computed itself reach CSS.

*The input may be anything.* The insights dict can be an older schema, a
hand-edited file, a partial write, or ``{}``. Nothing here raises: an unreadable
value is dropped, a section with no data is omitted rather than printed as a
heading over nothing, and a corpus with no jobs renders a deliberate "no data
yet" state instead of a page of zeros or broken markup.

The tolerant readers below duplicate a handful of private helpers in
``insights.py`` on purpose. Importing another module's underscore-prefixed
internals would couple the report to implementation detail it has no business
knowing, and the report has to survive input that ``build_insights`` did not
produce -- which is exactly the case where sharing the analytics module's
assumptions would be wrong.

Omitted-when-empty follows ``render_summary``'s rule and for the same reason: a
heading over an empty list reads as "the field has none of this", when what it
almost always means is "nothing enriched it".
"""

from __future__ import annotations

import html
import math
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

# --------------------------------------------------------------------------
# Vocabulary
# --------------------------------------------------------------------------

DISCIPLINE_LABELS: dict[str, str] = {
    "strength-conditioning": "Strength & Conditioning",
    "sports-medicine": "Sports Medicine",
    "nutrition": "Performance Nutrition",
    "cognitive": "Cognitive Performance",
    "research": "Research & Analytics",
    "leadership": "Program Leadership",
}
"""Display names for the discipline slugs ``classify.py`` assigns.

Slugs are good keys and bad prose. Anything not listed falls back to a
title-cased version of its slug, so a new discipline reads acceptably on the
day it is added and gets a real label whenever somebody gets round to it.
"""

DOMAIN_LABELS: dict[str, str] = {
    "military": "Military",
    "sof": "Special Operations",
    "first-responder": "Fire / EMS / Law Enforcement",
}

DISCIPLINE_ORDER: tuple[str, ...] = (
    "strength-conditioning",
    "sports-medicine",
    "nutrition",
    "cognitive",
    "research",
    "leadership",
)
"""Fixed hue order for disciplines.

Color follows the entity, never its rank: sports medicine is the same hue in
the discipline mix and in the salary bands, and stays that hue when a filtered
corpus drops it to fourth place. A reader who learned "orange is sports
medicine" in the first chart must not have to relearn it in the third.
"""

SERIES_LIGHT: tuple[str, ...] = (
    "#2a78d6",  # blue
    "#eb6834",  # orange
    "#1baf7a",  # aqua
    "#eda100",  # yellow
    "#e87ba4",  # magenta
    "#008300",  # green
)
SERIES_DARK: tuple[str, ...] = (
    "#3987e5",
    "#d95926",
    "#199e70",
    "#c98500",
    "#d55181",
    "#008300",
)
"""Categorical hues, stepped separately for each surface rather than flipped.

Validated as a set on both surfaces: every step sits inside the lightness band
and above the chroma floor, and every adjacent pair clears the
colorblind-separation and normal-vision floors.

Four of the light steps fall below 3:1 against ``--track``, which is the
contrast that actually matters -- a bar fill is read against the track it sits
in, not against the card behind it. That is legal only with a second channel,
which is why every colored mark in this report carries a visible text label
beside it: the discipline name to its left and the exact count to its right.
Color is never the only thing identifying a bar. Darkening those steps enough to
clear 3:1 would push them out of the lightness band the categorical scheme
depends on, so the label is the fix, not a heavier hue.

These are the single source of truth for the shipped CSS: :func:`_tokens` writes
them into the stylesheet rather than the stylesheet repeating them.
"""

RECENT_MONTHS = 12
"""How much of the timeline the month bars show. The sparkline shows all of it."""

TOP_ROWS = 10
"""Longest ranked list any one section renders.

The insights dict is already trimmed by its own ``top_n``; this is a second,
tighter cap for a document meant to be skimmed. Past ten rows a reader stops
reading rows and starts scrolling past them.
"""

MIN_BAR_PERCENT = 1.6
"""Floor on bar width, in percent.

A count of one against a peak of two hundred rounds to a zero-width bar, which
reads as "no data" rather than "one". The distortion is bounded and always in
the direction of visibility, and the exact count is printed beside every bar.
"""


# --------------------------------------------------------------------------
# Tolerant readers. Nothing below this line raises on bad input.
# --------------------------------------------------------------------------


def _clean(value: Any) -> str:
    """Collapse whitespace in a string-ish value; anything else becomes ""."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _as_float(value: Any) -> float | None:
    """Read a finite number, refusing bools (a flag is not a count).

    ``float()`` is called inside the guard rather than trusted: a JSON document
    can hold an integer with more magnitude than a float can represent, and
    ``math.isfinite(10 ** 400)`` raises ``OverflowError`` rather than returning
    ``False``. A number nothing can represent is an unreadable value, which is
    the case this whole layer exists to swallow.
    """
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float, str)):
        if isinstance(value, str):
            value = value.replace(",", "").replace("$", "").strip()
        try:
            parsed = float(value)
        except (ValueError, OverflowError):
            return None
        return parsed if math.isfinite(parsed) else None
    return None


def _as_int(value: Any) -> int:
    number = _as_float(value)
    return int(number) if number is not None else 0


def _as_count(value: Any) -> int:
    """Read a count: a whole number that cannot be negative.

    Every ``count`` in the insights dict is a tally, so a negative one is
    corrupt input rather than a small number. Clamping here rather than at each
    use site keeps the arithmetic downstream honest: a negative count would
    otherwise produce a bar wider than its track and, in the sparkline, a path
    drawn outside the ``viewBox`` entirely.
    """
    return max(0, _as_int(value))


def _as_mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _rows(value: Any) -> list[Mapping[str, Any]]:
    """Read a list-of-entries section, skipping anything that is not a mapping."""
    if not isinstance(value, (list, tuple)):
        return []
    return [entry for entry in value if isinstance(entry, Mapping)]


def _slugs(value: Any) -> list[str]:
    """Read a list of slugs out of a field that may not be a list at all.

    A bare string has to be special-cased before the generic iteration: ``str``
    is iterable, so a field holding ``"strength-conditioning"`` instead of
    ``["strength-conditioning"]`` would otherwise be read as twenty-two
    single-letter slugs and rendered as "S, T". Anything not iterable at all
    (an int, ``None``) is dropped rather than raising.
    """
    if isinstance(value, str):
        cleaned = _clean(value)
        return [cleaned] if cleaned else []
    if not isinstance(value, (list, tuple, set, frozenset)):
        return []
    return [cleaned for cleaned in (_clean(item) for item in value) if cleaned]


def _label(slug: str, table: Mapping[str, str]) -> str:
    """Human name for a slug, degrading to a title-cased version of the slug."""
    cleaned = _clean(slug)
    if not cleaned:
        return ""
    known = table.get(cleaned.casefold())
    if known:
        return known
    return " ".join(word.capitalize() for word in cleaned.replace("_", "-").split("-"))


def _money(value: Any) -> str:
    number = _as_float(value)
    return f"${number:,.0f}" if number is not None else "n/a"


def _percent(value: Any, digits: int = 0) -> str:
    number = _as_float(value)
    return f"{number * 100:.{digits}f}%" if number is not None else "-"


def _plural(count: int, singular: str, plural: str | None = None) -> str:
    return singular if count == 1 else (plural or f"{singular}s")


def _day(stamp: Any) -> str:
    """The date half of an ISO timestamp. Time of day is noise in a briefing."""
    return _clean(stamp)[:10]


# --------------------------------------------------------------------------
# The flattened view both renderers read
# --------------------------------------------------------------------------


@dataclass(slots=True)
class _Entry:
    """One ranked row: a name, how many, and optionally what share of what."""

    label: str
    count: int
    share: float | None = None
    note: str = ""
    color_index: int | None = None


@dataclass(slots=True)
class _Employer:
    name: str
    count: int
    median_salary: float | None
    focus: str


@dataclass(slots=True)
class _Band:
    """A p25-median-p75 pay band for one discipline."""

    label: str
    low: float
    mid: float
    high: float
    count: int
    color_index: int


@dataclass(slots=True)
class _Movement:
    """Month-over-month change in postings: the number a reader looks for first."""

    month: str
    previous_month: str
    count: int
    previous: int

    @property
    def change(self) -> int:
        return self.count - self.previous

    @property
    def ratio(self) -> float | None:
        """Fractional change, or None when the prior month was zero.

        Growth from zero is not a percentage. Reporting it as one produces the
        infinite-percent headline that makes a briefing untrustworthy.
        """
        return (self.change / self.previous) if self.previous else None

    @property
    def direction(self) -> str:
        if self.change > 0:
            return "up"
        if self.change < 0:
            return "down"
        return "flat"


@dataclass(slots=True)
class _Digest:
    """Everything both renderers need, read out of the insights dict exactly once.

    Flattened up front so that a malformed input is handled in one place rather
    than in thirty, and so the Markdown and HTML renderings can never disagree
    about what the corpus says.
    """

    generated_at: str = ""
    postings: int = 0
    unique_jobs: int = 0
    employers: int = 0
    with_salary: int = 0
    earliest: str = ""
    latest: str = ""
    remote_count: int = 0
    remote_share: float | None = None
    salary: Mapping[str, Any] = field(default_factory=dict)
    bands: list[_Band] = field(default_factory=list)
    disciplines: list[_Entry] = field(default_factory=list)
    domains: list[_Entry] = field(default_factory=list)
    employer_rows: list[_Employer] = field(default_factory=list)
    certifications: list[_Entry] = field(default_factory=list)
    clearances: list[_Entry] = field(default_factory=list)
    states: list[_Entry] = field(default_factory=list)
    installations: list[_Entry] = field(default_factory=list)
    branches: list[_Entry] = field(default_factory=list)
    titles: list[_Entry] = field(default_factory=list)
    timeline: list[tuple[str, int]] = field(default_factory=list)
    growing: list[tuple[str, int, int]] = field(default_factory=list)
    emerging: list[tuple[str, int, int]] = field(default_factory=list)
    window_days: int = 0

    @property
    def has_data(self) -> bool:
        """Whether there is anything at all worth rendering sections for.

        Deliberately not ``unique_jobs > 0``: a partial or older insights dict
        can carry populated rankings with a missing ``totals`` block, and
        throwing that away to show "no data yet" would be the renderer lying
        about the corpus rather than reporting it.
        """
        if self.postings > 0 or self.unique_jobs > 0:
            return True
        # Salary and remote counts are corpus facts in their own right. A dict
        # carrying a pay distribution and nothing else is a thin report, not an
        # empty one, and printing "no data yet" over it would throw away the
        # only thing it knows.
        if _as_count(self.salary.get("count")) or self.remote_count:
            return True
        return any(
            (
                self.disciplines,
                self.domains,
                self.employer_rows,
                self.certifications,
                self.clearances,
                self.states,
                self.installations,
                self.branches,
                self.titles,
                self.timeline,
                self.bands,
            )
        )

    @property
    def syndicated(self) -> int:
        """Records beyond one per job: the syndication and re-post rate."""
        return max(0, self.postings - self.unique_jobs)

    @property
    def movement(self) -> _Movement | None:
        """The two most recent timeline buckets, or None if there are not two."""
        if len(self.timeline) < 2:
            return None
        month, count = self.timeline[-1]
        previous_month, previous = self.timeline[-2]
        return _Movement(
            month=month, previous_month=previous_month, count=count, previous=previous
        )

    @property
    def recent_months(self) -> list[tuple[str, int]]:
        return self.timeline[-RECENT_MONTHS:]


def _color_index(slug: str) -> int:
    """Stable hue slot for a discipline, by vocabulary position not by rank."""
    cleaned = _clean(slug).casefold()
    if cleaned in DISCIPLINE_ORDER:
        return DISCIPLINE_ORDER.index(cleaned)
    # An unknown discipline still needs a deterministic slot: hashing the name
    # keeps it the same hue across every section of one report and across reruns.
    return sum(ord(char) for char in cleaned) % len(SERIES_LIGHT)


def _entries(
    value: Any,
    *,
    key: str = "name",
    labels: Mapping[str, str] | None = None,
    color: bool = False,
    limit: int = TOP_ROWS,
) -> list[_Entry]:
    """Read one ranked section into ``_Entry`` rows, dropping unusable ones."""
    result: list[_Entry] = []
    for row in _rows(value):
        raw = _clean(row.get(key))
        if not raw:
            continue
        result.append(
            _Entry(
                label=_label(raw, labels) if labels is not None else raw,
                count=_as_count(row.get("count")),
                share=_as_float(row.get("share")),
                color_index=_color_index(raw) if color else None,
            )
        )
        if len(result) >= limit:
            break
    return result


def _growth_pairs(value: Any, limit: int = 5) -> list[tuple[str, int, int]]:
    """(name, previous, recent) triples out of a trends list."""
    pairs: list[tuple[str, int, int]] = []
    for row in _rows(value)[:limit]:
        name = _clean(row.get("name"))
        if not name:
            continue
        pairs.append(
            (name, _as_count(row.get("previous")), _as_count(row.get("recent")))
        )
    return pairs


def _read(insights: Any) -> _Digest:
    """Flatten an insights dict into a ``_Digest``. Never raises."""
    data = _as_mapping(insights)
    totals = _as_mapping(data.get("totals"))
    span = _as_mapping(totals.get("date_span"))
    remote = _as_mapping(data.get("remote"))
    salary = _as_mapping(data.get("salary"))
    trends = _as_mapping(data.get("trends"))

    timeline: list[tuple[str, int]] = []
    for row in _rows(data.get("timeline")):
        month = _clean(row.get("month"))
        if month:
            timeline.append((month, _as_count(row.get("count"))))

    employer_rows: list[_Employer] = []
    for row in _rows(data.get("by_employer"))[:TOP_ROWS]:
        name = _clean(row.get("name"))
        if not name:
            continue
        focus = [
            _label(slug, DISCIPLINE_LABELS)
            for slug in _slugs(row.get("disciplines"))
        ]
        employer_rows.append(
            _Employer(
                name=name,
                count=_as_count(row.get("count")),
                median_salary=_as_float(row.get("median_salary")),
                focus=", ".join(focus[:2]),
            )
        )

    return _Digest(
        generated_at=_clean(data.get("generated_at")),
        postings=_as_count(totals.get("postings")),
        unique_jobs=_as_count(totals.get("unique_jobs")),
        employers=_as_count(totals.get("employers")),
        with_salary=_as_count(totals.get("with_salary")),
        earliest=_day(span.get("earliest")),
        latest=_day(span.get("latest")),
        remote_count=_as_count(remote.get("count")),
        remote_share=_as_float(remote.get("share")),
        salary=salary,
        bands=_salary_bands(salary),
        disciplines=_entries(
            data.get("by_discipline"), labels=DISCIPLINE_LABELS, color=True
        ),
        domains=_entries(data.get("by_domain"), labels=DOMAIN_LABELS),
        employer_rows=employer_rows,
        certifications=_entries(data.get("certifications")),
        clearances=_entries(data.get("clearances")),
        states=_entries(data.get("by_state"), key="code"),
        installations=_entries(data.get("by_installation")),
        branches=_entries(data.get("by_branch")),
        titles=_entries(data.get("top_titles"), key="title"),
        timeline=timeline,
        growing=_growth_pairs(trends.get("fastest_growing_employers")),
        emerging=_growth_pairs(trends.get("emerging_certifications")),
        window_days=_as_count(trends.get("window_days")),
    )


def _salary_bands(salary: Mapping[str, Any]) -> list[_Band]:
    """Per-discipline pay bands, widest first, skipping incoherent ones.

    A band needs p25, median, and p75 to mean anything. A discipline that
    published only a median is dropped rather than drawn as a zero-width band
    at an arbitrary position, which would read as certainty the data does not
    have. It also needs a name: an unnamed band is a colored stripe a reader
    cannot attribute to anything, which is worse than one fewer row.
    """
    bands: list[_Band] = []
    for slug, stats in _as_mapping(salary.get("by_discipline")).items():
        values = _as_mapping(stats)
        label = _label(slug, DISCIPLINE_LABELS)
        if not label:
            continue
        low = _as_float(values.get("p25"))
        mid = _as_float(values.get("median"))
        high = _as_float(values.get("p75"))
        if low is None or mid is None or high is None:
            continue
        if not low <= mid <= high:
            continue  # a scrambled record, not a distribution
        bands.append(
            _Band(
                label=label,
                low=low,
                mid=mid,
                high=high,
                count=_as_count(values.get("count")),
                color_index=_color_index(slug),
            )
        )
    bands.sort(key=lambda band: (-band.mid, band.label))
    return bands


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------


def _cell(text: str) -> str:
    """Make a string safe inside a Markdown table cell.

    An unescaped pipe in an employer name -- "Fire | Rescue Systems" is a real
    shape -- silently splits the row into an extra column and misaligns
    everything after it.
    """
    return text.replace("|", r"\|")


def _md_table(headers: Sequence[str], rows: Sequence[Sequence[str]]) -> list[str]:
    lines = [
        "| " + " | ".join(headers) + " |",
        "|" + "|".join("---" for _ in headers) + "|",
    ]
    for row in rows:
        lines.append("| " + " | ".join(_cell(str(cell)) for cell in row) + " |")
    return lines


def _md_movement(movement: _Movement) -> str:
    """One sentence about month-over-month direction, honest about small numbers."""
    if movement.direction == "flat":
        return (
            f"Postings held flat at **{movement.count}** in {movement.month}, "
            f"the same as {movement.previous_month}."
        )
    word = "up" if movement.direction == "up" else "down"
    ratio = movement.ratio
    delta = f"{movement.change:+d}"
    if ratio is None:
        tail = f"from none in {movement.previous_month}"
    else:
        tail = f"{abs(ratio) * 100:.0f}% against {movement.previous_month}"
    return (
        f"Postings are **{word} {delta}** in {movement.month} "
        f"({movement.previous} to {movement.count}), {tail}."
    )


def render_markdown(insights: dict[str, Any]) -> str:
    """A briefing-style digest of :func:`insights.build_insights`.

    Written for somebody who runs a tactical human performance community and is
    skimming: headline numbers first, then who is hiring, what credentials are
    being asked for, what it pays, where the work is, and what moved. Sections
    with no data are omitted entirely rather than printed empty.

    Never raises. A missing, partial, or empty ``insights`` produces a short and
    truthful document rather than an exception or a wall of zeros.
    """
    digest = _read(insights)
    stamp = _day(digest.generated_at) or "an unknown date"
    lines: list[str] = ["# Tactical Human Performance Job Market", ""]

    if not digest.has_data:
        lines += [
            f"*Briefing generated {stamp}.*",
            "",
            "## No data yet",
            "",
            "Nothing has been archived, so there is nothing to report. Run the",
            "pipeline at least once and the next briefing will have numbers in it.",
            "",
        ]
        return "\n".join(lines).rstrip() + "\n"

    lines += [f"*Briefing generated {stamp}.*", "", "## Headline", ""]
    lines += _md_headline(digest)
    lines += _md_movement_section(digest)
    lines += _md_employers(digest)
    lines += _md_disciplines(digest)
    lines += _md_credentials(digest)
    lines += _md_salary(digest)
    lines += _md_geography(digest)
    lines += _md_titles(digest)
    return "\n".join(lines).rstrip() + "\n"


def _md_headline(digest: _Digest) -> list[str]:
    jobs = digest.unique_jobs or digest.postings
    lines = [
        f"- **{jobs:,} open {_plural(jobs, 'job')}** from "
        f"**{digest.employers:,} {_plural(digest.employers, 'employer')}**."
    ]
    if digest.earliest or digest.latest:
        lines.append(
            f"- Posted between **{digest.earliest or 'unknown'}** and "
            f"**{digest.latest or 'unknown'}**."
        )
    salary_count = _as_count(digest.salary.get("count"))
    if salary_count:
        lines.append(
            f"- **{_money(digest.salary.get('median'))} median** annualized pay "
            f"across the {salary_count:,} {_plural(salary_count, 'posting')} that "
            f"publish one -- {_money(digest.salary.get('p25'))} to "
            f"{_money(digest.salary.get('p75'))} covers the middle half."
        )
    if digest.remote_share is not None:
        lines.append(
            f"- **{_percent(digest.remote_share)} remote-friendly** "
            f"({digest.remote_count:,} {_plural(digest.remote_count, 'job')})."
        )
    if digest.syndicated:
        lines.append(
            f"- {digest.syndicated:,} of {digest.postings:,} archived records are "
            "cross-board copies or re-posts, not separate jobs."
        )
    if digest.domains:
        mix = ", ".join(f"{row.label} {row.count:,}" for row in digest.domains)
        lines.append(f"- Populations served: {mix}.")
    lines.append("")
    return lines


def _md_movement_section(digest: _Digest) -> list[str]:
    movement = digest.movement
    if movement is None and not digest.growing and not digest.emerging:
        return []
    lines = ["## Month over month", ""]
    if movement is not None:
        lines += [_md_movement(movement), ""]
    recent = digest.recent_months
    if recent:
        peak = max(count for _, count in recent) or 1
        lines += ["```"]
        for month, count in recent:
            bar = "#" * max(1 if count else 0, round(count / peak * 28))
            lines.append(f"{month}  {count:>4}  {bar}")
        lines += ["```", ""]
    if digest.growing:
        window = digest.window_days or 90
        lines.append(
            f"**Hiring faster** (last {window} days against the {window} before):"
        )
        lines.append("")
        for name, previous, current in digest.growing:
            lines.append(f"- {name}: {previous} to {current}")
        lines.append("")
    if digest.emerging:
        lines.append("**Credentials appearing more often:**")
        lines.append("")
        for name, previous, current in digest.emerging:
            lines.append(f"- {name}: {previous} to {current}")
        lines.append("")
    return lines


def _md_employers(digest: _Digest) -> list[str]:
    if not digest.employer_rows:
        return []
    rows = [
        [
            row.name,
            f"{row.count:,}",
            _money(row.median_salary) if row.median_salary else "-",
            row.focus or "-",
        ]
        for row in digest.employer_rows
    ]
    return (
        ["## Who is hiring", ""]
        + _md_table(["Employer", "Jobs", "Median pay", "Focus"], rows)
        + [""]
    )


def _md_disciplines(digest: _Digest) -> list[str]:
    if not digest.disciplines:
        return []
    rows = [
        [row.label, f"{row.count:,}", _percent(row.share)] for row in digest.disciplines
    ]
    return (
        ["## Discipline mix", ""]
        + _md_table(["Discipline", "Jobs", "Share"], rows)
        + [
            "",
            "Share is out of jobs carrying any discipline tag, and a job can carry",
            "more than one, so these do not sum to 100%.",
            "",
        ]
    )


def _md_credentials(digest: _Digest) -> list[str]:
    if not digest.certifications and not digest.clearances:
        return []
    lines = ["## Credentials in demand", ""]
    if digest.certifications:
        rows = [
            [row.label, f"{row.count:,}", _percent(row.share)]
            for row in digest.certifications
        ]
        lines += _md_table(["Certification", "Jobs", "Share"], rows)
        lines += [
            "",
            "Share is out of jobs that name any certification at all.",
            "",
        ]
    if digest.clearances:
        chips = ", ".join(f"{row.label} ({row.count:,})" for row in digest.clearances)
        lines += [f"**Clearances requested:** {chips}", ""]
    return lines


def _md_salary(digest: _Digest) -> list[str]:
    if not _as_count(digest.salary.get("count")):
        return []
    lines = ["## What it pays", ""]
    lines += [
        f"- Median **{_money(digest.salary.get('median'))}**, "
        f"middle half {_money(digest.salary.get('p25'))} to "
        f"{_money(digest.salary.get('p75'))}.",
        f"- Full range {_money(digest.salary.get('min'))} to "
        f"{_money(digest.salary.get('max'))}.",
        "",
    ]
    if digest.bands:
        rows = [
            [
                band.label,
                f"{band.count:,}",
                _money(band.low),
                _money(band.mid),
                _money(band.high),
            ]
            for band in digest.bands
        ]
        lines += _md_table(
            ["Discipline", "n", "25th", "Median", "75th"],
            rows,
        )
        lines.append("")
    lines += [
        "Every figure is annualized before comparison -- hourly federal rates and",
        "annual contractor bands are not otherwise comparable.",
        "",
    ]
    return lines


def _md_geography(digest: _Digest) -> list[str]:
    if not digest.states and not digest.installations and not digest.branches:
        return []
    lines = ["## Where the work is", ""]
    if digest.states:
        chips = ", ".join(f"{row.label} ({row.count:,})" for row in digest.states)
        lines += [f"**States:** {chips}", ""]
    if digest.installations:
        rows = [[row.label, f"{row.count:,}"] for row in digest.installations]
        lines += _md_table(["Installation", "Jobs"], rows) + [""]
    if digest.branches:
        chips = ", ".join(f"{row.label} ({row.count:,})" for row in digest.branches)
        lines += [f"**Branches and services:** {chips}", ""]
    return lines


def _md_titles(digest: _Digest) -> list[str]:
    if not digest.titles:
        return []
    rows = [[row.label, f"{row.count:,}"] for row in digest.titles]
    return ["## Most common titles", ""] + _md_table(["Title", "Jobs"], rows) + [""]


# --------------------------------------------------------------------------
# HTML
# --------------------------------------------------------------------------


def _esc(value: Any) -> str:
    """Escape a third-party string for text or attribute use.

    ``quote=True`` matters: these strings land in ``title`` and ``aria-label``
    attributes as well as in text, and a double quote in an employer name would
    otherwise close the attribute and let the rest of the name become markup.
    """
    return html.escape(_clean(value), quote=True)


def _pct(part: float, whole: float) -> float:
    """A width in percent, clamped to something a browser and a reader accept."""
    if whole <= 0:
        return 0.0
    return max(0.0, min(100.0, part / whole * 100.0))


def _series_var(index: int | None) -> str:
    """CSS variable for a hue slot. Only ever a number this module computed."""
    if index is None:
        return "var(--accent)"
    return f"var(--s{index % len(SERIES_LIGHT) + 1})"


def _bar_rows(entries: Sequence[_Entry], *, unit: str = "job") -> list[str]:
    """Horizontal magnitude bars: name, track, count.

    One hue for the whole chart unless the entries carry their own slot, because
    coloring each bar by its own value would double-encode length as hue and
    burn the only free channel on information the bar already shows.
    """
    if not entries:
        return []
    peak = max((entry.count for entry in entries), default=0)
    out = ['<div class="bars">']
    for entry in entries:
        width = max(MIN_BAR_PERCENT, _pct(entry.count, peak)) if entry.count else 0.0
        # A literal middle dot, not "&middot;": named HTML entities are undefined
        # in XML, and this document has to survive a strict parser as well as a
        # browser. Only the five XML-standard names ever appear, via html.escape.
        share = f" · {_percent(entry.share)}" if entry.share is not None else ""
        hint = f"{entry.label}: {entry.count:,} {_plural(entry.count, unit)}"
        if entry.share is not None:
            hint = f"{hint}, {_percent(entry.share)} share"
        out.append(
            '<div class="bar">'
            f'<span class="bar-name">{_esc(entry.label)}</span>'
            f'<span class="bar-track" title="{_esc(hint)}">'
            f'<span class="bar-fill" style="width:{width:.2f}%;'
            f"background:{_series_var(entry.color_index)}\"></span>"
            "</span>"
            f'<span class="bar-note">{entry.count:,}{share}</span>'
            "</div>"
        )
    out.append("</div>")
    return out


def _tile(value: str, label: str, note: str = "", tone: str = "") -> str:
    """One headline stat. The number is the chart; a one-bar bar chart is not."""
    klass = f"tile tile-{tone}" if tone else "tile"
    body = [
        f'<div class="{klass}">',
        f'<div class="tile-value">{_esc(value)}</div>',
        f'<div class="tile-label">{_esc(label)}</div>',
    ]
    if note:
        body.append(f'<div class="tile-note">{_esc(note)}</div>')
    body.append("</div>")
    return "".join(body)


def _section(section_id: str, heading: str, blurb: str, body: Sequence[str]) -> list[str]:
    """Wrap a rendered body in a titled card, or emit nothing if it is empty."""
    if not body:
        return []
    out = [
        f'<section class="card" id="{_esc(section_id)}">',
        f"<h2>{_esc(heading)}</h2>",
    ]
    if blurb:
        out.append(f'<p class="blurb">{_esc(blurb)}</p>')
    out.extend(body)
    out.append("</section>")
    return out


def _sparkline(timeline: Sequence[tuple[str, int]]) -> list[str]:
    """Inline SVG area+line over the whole month series.

    Hand-built rather than handed to a library because this document is not
    allowed to fetch anything. ``preserveAspectRatio="none"`` lets the shape
    stretch to any container width; ``vector-effect="non-scaling-stroke"`` keeps
    the line one weight while it does, and there is no text inside the SVG for
    the stretch to distort -- the labels live in HTML beside it.
    """
    counts = [count for _, count in timeline]
    if not counts:
        return []
    peak = max(counts) or 1
    top, bottom = 1.0, 29.0
    span = len(counts) - 1
    points = []
    for index, count in enumerate(counts):
        x = (index / span * 100.0) if span else 50.0
        y = bottom - (count / peak) * (bottom - top)
        points.append(f"{x:.2f},{y:.2f}")
    line = " ".join(points)
    area = f"M0,{bottom:.2f} L{line.replace(' ', ' L')} L100,{bottom:.2f} Z"
    if not span:
        # A single month has no line to draw; a flat rule across the box says
        # "one bucket" honestly, where a lone dot at x=50 reads as noise.
        area = f"M0,{bottom:.2f} L0,{points[0].split(',')[1]} L100,{points[0].split(',')[1]} L100,{bottom:.2f} Z"
        line = f"0,{points[0].split(',')[1]} 100,{points[0].split(',')[1]}"
    first_month, last_month = timeline[0][0], timeline[-1][0]
    return [
        '<div class="spark">',
        '<svg class="spark-svg" viewBox="0 0 100 30" preserveAspectRatio="none" '
        f'role="img" aria-label="Postings per month from {_esc(first_month)} to '
        f'{_esc(last_month)}, peak {peak:,}">',
        f"<title>Postings per month, {_esc(first_month)} to {_esc(last_month)}</title>",
        f'<path class="spark-area" d="{area}"></path>',
        f'<polyline class="spark-line" points="{line}" '
        'vector-effect="non-scaling-stroke"></polyline>',
        "</svg>",
        '<div class="spark-axis">',
        f'<span>{_esc(first_month)}</span><span>peak {peak:,}</span>'
        f"<span>{_esc(last_month)}</span>",
        "</div>",
        "</div>",
    ]


def _month_columns(months: Sequence[tuple[str, int]]) -> list[str]:
    """Vertical CSS bars for the recent months, labeled by month number.

    Only the month number is printed under each column: twelve four-digit years
    collide on a phone, and the year is already stated in the caption above.
    """
    if not months:
        return []
    peak = max((count for _, count in months), default=0) or 1
    out = ['<div class="months">']
    for month, count in months:
        height = max(MIN_BAR_PERCENT, _pct(count, peak)) if count else 0.0
        short = month.split("-")[-1] if "-" in month else month
        out.append(
            f'<div class="month" title="{_esc(month)}: {count:,} '
            f'{_plural(count, "posting")}">'
            '<span class="month-bar">'
            f'<span class="month-fill" style="height:{height:.2f}%"></span>'
            "</span>"
            f'<span class="month-label">{_esc(short)}</span>'
            "</div>"
        )
    out.append("</div>")
    return out


def _band_rows(bands: Sequence[_Band]) -> list[str]:
    """Pay bands on one shared axis: p25 to p75, with the median marked.

    A shared axis is the point -- separate per-row scales would make every
    discipline look identically paid. The axis floor is the lowest p25 and the
    ceiling the highest p75, so the drawn range is the range that exists rather
    than an arbitrary zero-anchored one.
    """
    if not bands:
        return []
    floor = min(band.low for band in bands)
    ceiling = max(band.high for band in bands)
    width = ceiling - floor
    if width <= 0:
        # Every discipline lands on one figure. A shared axis has nothing to
        # say about that, so give each band a nominal width and let the numbers
        # printed beside it carry the meaning.
        width = max(1.0, ceiling * 0.1)
        floor = ceiling - width
    out = ['<div class="bands">']
    for band in bands:
        left = _pct(band.low - floor, width)
        right = _pct(band.high - floor, width)
        mark = _pct(band.mid - floor, width)
        # The minimum-width floor can push a band that starts near the right
        # edge past 100%, which bleeds outside the rounded track. Slide it left
        # instead of widening past the axis.
        extent = max(MIN_BAR_PERCENT, right - left)
        left = min(left, 100.0 - extent)
        hint = (
            f"{band.label}: 25th {_money(band.low)}, median {_money(band.mid)}, "
            f"75th {_money(band.high)} (n={band.count:,})"
        )
        out.append(
            '<div class="band">'
            f'<span class="band-name">{_esc(band.label)}</span>'
            f'<span class="band-track" title="{_esc(hint)}">'
            f'<span class="band-range" style="left:{left:.2f}%;width:{extent:.2f}%;'
            f'background:{_series_var(band.color_index)}"></span>'
            f'<span class="band-mark" style="left:{mark:.2f}%"></span>'
            "</span>"
            f'<span class="band-note">{_esc(_money(band.mid))}</span>'
            "</div>"
        )
    out.append(
        '<div class="band-axis">'
        f'<span>{_esc(_money(floor))}</span>'
        "<span>annualized</span>"
        f"<span>{_esc(_money(ceiling))}</span>"
        "</div>"
    )
    out.append("</div>")
    return out


def _salary_figures(digest: _Digest) -> list[str]:
    """The corpus-wide pay distribution as five labeled figures.

    The per-discipline bands below only exist for disciplines that had salaried
    postings, and a corpus can easily publish pay without publishing a
    discipline tag alongside it. Rendering the bands alone therefore threw away
    the whole pay section exactly when it was the only pay evidence there was --
    and made the HTML say less than the Markdown about the same corpus, which
    the single-read ``_Digest`` exists to prevent.

    Five numbers are not a chart. A distribution this small is read faster as
    figures than as a shape, and the shape is drawn per discipline below anyway.
    """
    if not _as_count(digest.salary.get("count")):
        return []
    wanted = (
        ("Lowest", "min"),
        ("25th", "p25"),
        ("Median", "median"),
        ("75th", "p75"),
        ("Highest", "max"),
    )
    cells = [
        (label, _money(digest.salary.get(key)))
        for label, key in wanted
        if _as_float(digest.salary.get(key)) is not None
    ]
    if not cells:
        return []
    out = ['<ul class="figures">']
    for label, value in cells:
        out.append(
            '<li class="figure">'
            f'<span class="figure-value">{_esc(value)}</span>'
            f'<span class="figure-label">{_esc(label)}</span>'
            "</li>"
        )
    out.append("</ul>")
    return out


def _chips(entries: Sequence[_Entry]) -> list[str]:
    if not entries:
        return []
    out = ['<ul class="chips">']
    for entry in entries:
        out.append(
            f'<li class="chip">{_esc(entry.label)}'
            f'<span class="chip-count">{entry.count:,}</span></li>'
        )
    out.append("</ul>")
    return out


def _employer_table(rows: Sequence[_Employer]) -> list[str]:
    """Employers as a table, because four attributes per row is a table.

    Wrapped in its own scroll container: on a phone this is wider than the
    viewport, and a table that scrolls itself is far better than a page that
    scrolls sideways.
    """
    if not rows:
        return []
    peak = max((row.count for row in rows), default=0)
    out = [
        '<div class="scroll">',
        '<table class="grid">',
        "<thead><tr>"
        '<th scope="col">Employer</th>'
        '<th scope="col" class="num">Jobs</th>'
        '<th scope="col">Relative volume</th>'
        '<th scope="col" class="num">Median pay</th>'
        '<th scope="col">Focus</th>'
        "</tr></thead>",
        "<tbody>",
    ]
    for row in rows:
        width = max(MIN_BAR_PERCENT, _pct(row.count, peak)) if row.count else 0.0
        out.append(
            "<tr>"
            f'<th scope="row">{_esc(row.name)}</th>'
            f'<td class="num">{row.count:,}</td>'
            '<td class="cell-bar">'
            f'<span class="bar-track"><span class="bar-fill" '
            f'style="width:{width:.2f}%"></span></span>'
            "</td>"
            f'<td class="num">{_esc(_money(row.median_salary) if row.median_salary else "-")}</td>'
            f'<td class="muted">{_esc(row.focus or "-")}</td>'
            "</tr>"
        )
    out += ["</tbody>", "</table>", "</div>"]
    return out


def _movement_tile(digest: _Digest) -> str:
    movement = digest.movement
    if movement is None:
        return ""
    tone = {"up": "up", "down": "down", "flat": ""}[movement.direction]
    ratio = movement.ratio
    if ratio is None:
        note = f"from none in {movement.previous_month}"
    else:
        note = f"{ratio * 100:+.0f}% vs {movement.previous_month}"
    return _tile(
        f"{movement.change:+d}",
        f"Postings in {movement.month}",
        note,
        tone=tone,
    )


def _headline_tiles(digest: _Digest) -> list[str]:
    jobs = digest.unique_jobs or digest.postings
    tiles = [
        _tile(f"{jobs:,}", "Open jobs", "deduplicated across boards"),
        _tile(
            f"{digest.employers:,}",
            _plural(digest.employers, "Employer"),
            f"{digest.syndicated:,} records are re-posts" if digest.syndicated else "",
        ),
    ]
    salary_count = _as_count(digest.salary.get("count"))
    if salary_count:
        tiles.append(
            _tile(
                _money(digest.salary.get("median")),
                "Median annual pay",
                f"n={salary_count:,} of {jobs:,}",
            )
        )
    if digest.remote_share is not None:
        tiles.append(
            _tile(
                _percent(digest.remote_share),
                "Remote-friendly",
                f"{digest.remote_count:,} {_plural(digest.remote_count, 'job')}",
            )
        )
    moved = _movement_tile(digest)
    if moved:
        tiles.append(moved)
    return ['<div class="tiles">', *tiles, "</div>"]


def _trend_lists(digest: _Digest) -> list[str]:
    if not digest.growing and not digest.emerging:
        return []
    window = digest.window_days or 90
    out = ['<div class="split">']
    for heading, pairs in (
        (f"Hiring faster (last {window} days)", digest.growing),
        ("Credentials appearing more", digest.emerging),
    ):
        if not pairs:
            continue
        out.append('<div class="split-col">')
        out.append(f"<h3>{_esc(heading)}</h3>")
        out.append('<ul class="movers">')
        for name, previous, current in pairs:
            out.append(
                f'<li><span class="mover-name">{_esc(name)}</span>'
                f'<span class="mover-delta">{previous:,} to {current:,}</span></li>'
            )
        out.append("</ul>")
        out.append("</div>")
    out.append("</div>")
    return out


_LIGHT_TOKENS = """\
  color-scheme: light dark;
  --plane: #f4f4f1;
  --surface: #fcfcfb;
  --ink: #1b1b19;
  --ink-2: #52514e;
  --muted: #6e6c67;
  --rule: #e1e0d9;
  --track: #e9e7e0;
  --edge: rgba(27, 27, 25, 0.10);
  --accent: #2a78d6;
  --up: #006300;
  --down: #a3241f;"""

_DARK_TOKENS = """\
  --plane: #101012;
  --surface: #17171a;
  --ink: #f2f1ec;
  --ink-2: #c3c2b7;
  --muted: #93918a;
  --rule: #2c2c2e;
  --track: #26262a;
  --edge: rgba(242, 241, 236, 0.12);
  --accent: #3987e5;
  --up: #0ca30c;
  --down: #f08b8b;"""


def _tokens(base: str, series: Sequence[str], indent: str = "  ") -> str:
    """One custom-property block: the surface tokens plus the series hues.

    The series steps are written out of :data:`SERIES_LIGHT` and
    :data:`SERIES_DARK` rather than hand-copied into the CSS. Hand-copying is
    how a palette that was validated once stops matching the palette that ships:
    the constants and the stylesheet drift, and nothing fails until somebody
    notices two charts disagreeing about which hue means sports medicine.
    """
    lines = [line.strip() for line in base.splitlines()]
    lines += [f"--s{index}: {value};" for index, value in enumerate(series, 1)]
    return "\n".join(indent + line for line in lines)


# Dark mode is declared twice on purpose. The media query serves the reader's
# own system preference; the ``[data-theme]`` attribute lets a host page force
# either mode and win, in both directions -- hence the ``:not`` guard on the
# media-query rule, without which a host forcing light would still be overridden
# by a dark system preference.
_PALETTE = (
    ":root {\n"
    + _tokens(_LIGHT_TOKENS, SERIES_LIGHT)
    + "\n}\n"
    '@media (prefers-color-scheme: dark) {\n  :root:not([data-theme="light"]) {\n'
    + _tokens(_DARK_TOKENS, SERIES_DARK, "    ")
    + "\n  }\n}\n"
    ':root[data-theme="dark"] {\n'
    + _tokens(_DARK_TOKENS, SERIES_DARK)
    + "\n}\n"
)

_RULES = """\
*, *::before, *::after { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  padding: 1.25rem 1rem 3rem;
  background: var(--plane);
  color: var(--ink);
  font-family: system-ui, -apple-system, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  font-size: 16px;
  line-height: 1.5;
  overflow-wrap: break-word;
}
.wrap { max-width: 60rem; margin: 0 auto; }
.masthead { margin-bottom: 1.25rem; }
.masthead h1 { font-size: 1.6rem; line-height: 1.2; margin: 0 0 .3rem; letter-spacing: -0.01em; }
.masthead .sub { margin: 0; color: var(--muted); font-size: .88rem; }
.card {
  background: var(--surface);
  border: 1px solid var(--edge);
  border-radius: .75rem;
  padding: 1.1rem 1.1rem 1.25rem;
  margin: 0 0 1rem;
}
.card h2 { font-size: 1.02rem; margin: 0 0 .2rem; letter-spacing: .01em; }
.card h3 { font-size: .82rem; margin: 0 0 .5rem; color: var(--ink-2); font-weight: 600; }
.blurb { margin: 0 0 .9rem; color: var(--muted); font-size: .82rem; }
.tiles {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: .75rem;
}
.tile {
  background: var(--surface);
  border: 1px solid var(--edge);
  border-radius: .75rem;
  padding: .85rem .9rem;
}
.tile-value { font-size: 1.65rem; line-height: 1.1; font-weight: 650; letter-spacing: -0.02em; }
.tile-label { font-size: .8rem; color: var(--ink-2); margin-top: .2rem; }
.tile-note { font-size: .72rem; color: var(--muted); margin-top: .15rem; }
.tile-up .tile-value { color: var(--up); }
.tile-down .tile-value { color: var(--down); }
.bars { display: flex; flex-direction: column; gap: .4rem; }
.bar {
  display: grid;
  grid-template-columns: minmax(0, 10rem) minmax(0, 1fr) minmax(0, 7rem);
  gap: .3rem .75rem;
  align-items: center;
}
.bar-name { font-size: .85rem; min-width: 0; }
.bar-track {
  position: relative;
  display: block;
  height: .55rem;
  border-radius: .3rem;
  background: var(--track);
  min-width: 2rem;
}
.bar-fill {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  border-radius: .3rem;
  background: var(--accent);
}
.bar-note {
  font-size: .78rem;
  color: var(--ink-2);
  text-align: right;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.scroll { overflow-x: auto; }
table.grid { border-collapse: collapse; width: 100%; min-width: 34rem; font-size: .85rem; }
table.grid th, table.grid td {
  text-align: left;
  padding: .45rem .6rem .45rem 0;
  border-bottom: 1px solid var(--rule);
  vertical-align: middle;
}
table.grid thead th {
  font-size: .72rem;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--muted);
  font-weight: 600;
}
table.grid tbody th { font-weight: 600; }
table.grid .num { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
table.grid .muted { color: var(--muted); }
.cell-bar { width: 30%; min-width: 5rem; }
.bands { display: flex; flex-direction: column; gap: .5rem; }
.band {
  display: grid;
  grid-template-columns: minmax(0, 10rem) minmax(0, 1fr) minmax(0, 5.5rem);
  gap: .3rem .75rem;
  align-items: center;
}
.band-name { font-size: .85rem; min-width: 0; }
.band-track {
  position: relative;
  display: block;
  height: .8rem;
  border-radius: .4rem;
  background: var(--track);
  min-width: 2rem;
}
.band-range { position: absolute; top: 0; bottom: 0; border-radius: .4rem; }
.band-mark {
  position: absolute;
  top: -.15rem;
  bottom: -.15rem;
  width: 2px;
  margin-left: -1px;
  border-radius: 1px;
  background: var(--surface);
}
.band-note {
  font-size: .78rem;
  text-align: right;
  color: var(--ink-2);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.band-axis {
  display: flex;
  justify-content: space-between;
  font-size: .72rem;
  color: var(--muted);
  margin-top: .35rem;
  gap: .5rem;
}
.spark { margin-bottom: .9rem; }
.spark-svg { display: block; width: 100%; height: 4.5rem; }
.spark-area { fill: var(--accent); fill-opacity: .16; stroke: none; }
.spark-line { fill: none; stroke: var(--accent); stroke-width: 2; stroke-linejoin: round; }
.spark-axis {
  display: flex;
  justify-content: space-between;
  font-size: .72rem;
  color: var(--muted);
  gap: .5rem;
}
.months { display: flex; align-items: stretch; gap: .3rem; }
.month { flex: 1 1 0; min-width: 0; display: flex; flex-direction: column; gap: .25rem; }
.month-bar {
  position: relative;
  display: block;
  height: 4rem;
  background: var(--track);
  border-radius: .2rem;
}
.month-fill {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  background: var(--accent);
  border-radius: .2rem;
}
.month-label {
  font-size: .66rem;
  color: var(--muted);
  text-align: center;
  font-variant-numeric: tabular-nums;
}
.figures {
  list-style: none;
  margin: 0 0 1rem;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(6.5rem, 1fr));
  gap: .5rem .75rem;
}
.figure { display: flex; flex-direction: column; min-width: 0; }
.figure-value { font-size: 1.02rem; font-weight: 650; font-variant-numeric: tabular-nums; }
.figure-label {
  font-size: .68rem;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--muted);
}
.chips { list-style: none; margin: 0; padding: 0; display: flex; flex-wrap: wrap; gap: .35rem; }
.chip {
  border: 1px solid var(--edge);
  border-radius: 999px;
  padding: .15rem .6rem;
  font-size: .78rem;
  color: var(--ink-2);
  display: inline-flex;
  gap: .4rem;
  align-items: baseline;
}
.chip-count { color: var(--muted); font-variant-numeric: tabular-nums; }
.split { display: grid; grid-template-columns: repeat(auto-fit, minmax(15rem, 1fr)); gap: 1rem; }
.movers { list-style: none; margin: 0; padding: 0; }
.movers li {
  display: flex;
  justify-content: space-between;
  gap: .75rem;
  font-size: .82rem;
  padding: .25rem 0;
  border-bottom: 1px solid var(--rule);
}
.mover-name { min-width: 0; }
.mover-delta { color: var(--muted); font-variant-numeric: tabular-nums; white-space: nowrap; }
.stack { display: flex; flex-direction: column; gap: 1.1rem; }
.sub-head {
  font-size: .72rem;
  text-transform: uppercase;
  letter-spacing: .04em;
  color: var(--muted);
  margin: 0 0 .4rem;
  font-weight: 600;
}
.empty { text-align: center; padding: 2.5rem 1rem; }
.empty h2 { margin-bottom: .4rem; }
.empty p { color: var(--muted); margin: 0 auto; max-width: 32rem; font-size: .9rem; }
.colophon { color: var(--muted); font-size: .74rem; margin: 1.25rem 0 0; }
@media (max-width: 34rem) {
  .bar, .band { display: flex; flex-wrap: wrap; align-items: center; gap: .2rem .5rem; }
  .bar-name, .band-name { flex: 1 1 auto; min-width: 0; }
  .bar-note, .band-note { flex: 0 0 auto; order: 2; }
  .bar-track, .band-track { flex: 1 1 100%; order: 3; }
  .tile-value { font-size: 1.4rem; }
}
@media print {
  body { padding: 0; }
  .card, .tile { break-inside: avoid; }
}
"""

_STYLESHEET = "\n" + _PALETTE + _RULES


def render_html(
    insights: dict[str, Any],
    *,
    title: str = "Tactical Human Performance Job Market",
) -> str:
    """A single self-contained HTML document summarizing the corpus.

    The output fetches nothing: no scripts, no stylesheets, no fonts, no images,
    and no ``src``/``href`` attribute of any kind. Charts are CSS bars and one
    inline SVG sparkline computed here from the data. It reads correctly on a
    phone, in light mode and in dark, and every dynamic string in it is escaped.

    Never raises. An empty or unusable ``insights`` renders a deliberate "no
    data yet" page rather than a broken or all-zero one.
    """
    digest = _read(insights)
    safe_title = _esc(title) or "Tactical Human Performance Job Market"
    stamp = _day(digest.generated_at)

    body: list[str] = [
        '<main class="wrap">',
        '<header class="masthead">',
        f"<h1>{safe_title}</h1>",
        f'<p class="sub">{_esc(_masthead_line(digest, stamp))}</p>',
        "</header>",
    ]

    if not digest.has_data:
        body += [
            '<section class="card empty" id="empty-state">',
            "<h2>No data yet</h2>",
            "<p>Nothing has been archived, so there is nothing to report. "
            "Run the pipeline at least once and this page will fill in.</p>",
            "</section>",
        ]
    else:
        body += _section(
            "overview",
            "Headline",
            "One row per job: syndicated copies of the same posting are counted once.",
            _headline_tiles(digest),
        )
        body += _section(
            "movement",
            "Month over month",
            _movement_blurb(digest),
            # The sparkline earns its space only when it shows something the
            # month bars below it cannot. When the whole archive fits in the
            # last twelve months the two charts are the same data drawn twice,
            # which costs the reader attention and tells them nothing new.
            (_sparkline(digest.timeline) if len(digest.timeline) > RECENT_MONTHS else [])
            + _month_columns(digest.recent_months)
            + _trend_lists(digest),
        )
        body += _section(
            "employers",
            "Who is hiring",
            "Bar length is jobs relative to the busiest employer shown.",
            _employer_table(digest.employer_rows),
        )
        body += _section(
            "disciplines",
            "Discipline mix",
            "Share is out of jobs carrying any discipline tag. A job can carry "
            "several, so these do not sum to 100%.",
            _bar_rows(digest.disciplines) + _domain_block(digest),
        )
        body += _section(
            "credentials",
            "Credentials in demand",
            "Share is out of jobs that name any certification at all.",
            _bar_rows(digest.certifications) + _clearance_block(digest),
        )
        body += _section(
            "salary",
            "What it pays",
            _salary_blurb(digest),
            _salary_figures(digest) + _band_rows(digest.bands),
        )
        body += _section(
            "geography",
            "Where the work is",
            "States are read from the posting location; installations and "
            "branches come from the description.",
            _geography_block(digest),
        )
        body += _section(
            "titles",
            "Most common titles",
            "Titles as the employers wrote them, deduplicated case-insensitively.",
            _bar_rows(digest.titles),
        )

    body += [
        f'<p class="colophon">{_esc(_colophon(digest))}</p>',
        "</main>",
    ]

    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8"/>\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1"/>\n'
        '<meta name="color-scheme" content="light dark"/>\n'
        f"<title>{safe_title}</title>\n"
        f"<style>{_STYLESHEET}</style>\n"
        "</head>\n"
        "<body>\n"
        + "\n".join(body)
        + "\n</body>\n</html>\n"
    )


def _masthead_line(digest: _Digest, stamp: str) -> str:
    parts: list[str] = []
    if stamp:
        parts.append(f"Generated {stamp}")
    if digest.earliest and digest.latest:
        parts.append(f"postings dated {digest.earliest} to {digest.latest}")
    if digest.postings:
        parts.append(
            f"{digest.postings:,} archived {_plural(digest.postings, 'record')}"
        )
    return " · ".join(parts) if parts else "No archived postings yet"


def _movement_blurb(digest: _Digest) -> str:
    """Describe the charts rather than restate the delta.

    The headline tile immediately above already says how far postings moved and
    against which month. Repeating it here would spend the one line a reader
    gives a caption on something they read four seconds ago.
    """
    recent = digest.recent_months
    if not recent:
        return "No dated postings yet, so there is no month-over-month view."
    # The columns are labeled with the month number only -- twelve four-digit
    # years collide on a phone -- so the caption has to carry the year, or a
    # window that straddles a new year is unreadable.
    span = (
        f"{recent[0][0]} to {recent[-1][0]}"
        if len(recent) > 1
        else str(recent[0][0])
    )
    parts = [f"Postings per calendar month, {span}."]
    if len(digest.timeline) > RECENT_MONTHS:
        parts.append(
            f"The line above spans all {len(digest.timeline):,} archived months, "
            f"from {digest.timeline[0][0]}."
        )
    return " ".join(parts)


def _salary_blurb(digest: _Digest) -> str:
    count = _as_count(digest.salary.get("count"))
    if not count:
        return ""
    return (
        f"Every figure annualized before comparison. Bars span the 25th to 75th "
        f"percentile with the median marked; n={count:,} postings published pay."
    )


def _domain_block(digest: _Digest) -> list[str]:
    if not digest.domains:
        return []
    return ['<p class="sub-head">Populations served</p>'] + _chips(digest.domains)


def _clearance_block(digest: _Digest) -> list[str]:
    if not digest.clearances:
        return []
    return ['<p class="sub-head">Clearances requested</p>'] + _chips(digest.clearances)


def _geography_block(digest: _Digest) -> list[str]:
    out: list[str] = []
    if digest.states:
        out.append('<p class="sub-head">States</p>')
        out += _bar_rows(digest.states)
    if digest.installations:
        out.append('<p class="sub-head">Installations</p>')
        out += _bar_rows(digest.installations)
    if digest.branches:
        out.append('<p class="sub-head">Branches and services</p>')
        out += _chips(digest.branches)
    return ['<div class="stack">', *out, "</div>"] if out else []


def _colophon(digest: _Digest) -> str:
    """The footnote that keeps a reader from over-reading the numbers."""
    base = (
        "Counts are one row per job, deduplicated by employer, title, and location "
        "across every board. Pay is annualized from whatever period the posting "
        "quoted. Certification and clearance figures reflect only postings that "
        "state requirements."
    )
    if digest.syndicated:
        return (
            f"{base} {digest.syndicated:,} of {digest.postings:,} archived records "
            "are cross-board copies or re-posts."
        )
    return base
