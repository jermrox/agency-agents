"""Federal contract awards as a leading indicator of tactical HP hiring.

THE PROBLEM THIS SOLVES
Every other source in this project reads job postings, which means every other
source is looking at the *end* of a process. By the time an H2F strength coach
requisition appears on a contractor's Greenhouse board, the contract that pays
for it was signed weeks or months earlier, the incumbent staff have already
been poached, and half the roles are spoken for.

The award itself is public the moment it is signed. When a contractor wins an
H2F, POTFF, or THOR3 vehicle they have to staff it -- routinely ten to forty
coaches, athletic trainers, dietitians, and cognitive performance specialists,
against a performance start date they cannot move. So an award tells you three
things before any board does:

  1. who is about to hire,
  2. roughly how much hiring (award value is the only public proxy for
     headcount on a services contract),
  3. which ATS boards are suddenly worth watching.

That last one is the point of contact with the rest of this project: the output
here feeds the same human-reviewed watchlist that ``discover.py`` feeds. This
module never edits ``sources.toml`` and never invents a board token. Finding an
employer's ATS takes a human thirty seconds; a guessed board token silently
returns nothing forever.

WHY USASPENDING
https://api.usaspending.gov is completely open -- no key, no account, no OAuth,
no signup, no rate-limit token. That matters because this project is designed
to run in a bare CI container with zero credentials. SAM.gov's opportunity API
would cover pre-award solicitations, but it requires a registered API key, so
it is deliberately not used here.

WHY THE FIELD PICKER IS TOLERANT
The v2 search endpoint takes a list of human-readable field *labels* ("Award
ID", "Recipient Name") and echoes them back as the result keys. Across versions
and across mirrors of that payload, those keys have come back as the labels
themselves, as snake_case (``recipient_name``), and as camelCase
(``recipientName``) -- and the underlying award record exposes several of the
same values under entirely different names (``piid``, ``total_obligation``,
``period_of_performance_start_date``). A single hard-coded key spelling means
the module returns a list of empty awards the day the casing changes, with no
error to notice. So :func:`pick_field` takes several candidate keys per field,
compares them with case and punctuation normalized away, and returns the first
present non-empty one. Casing variants collapse to one normalized key; the
genuinely different names are listed out.

WHAT IS DELIBERATELY THROWN AWAY
A defense prime wins hundreds of contracts a year and almost none of them are
human performance work. An award whose description carries no human performance
signal at all is dropped, not ranked low -- a briefing that lists every janitor
and IT-refresh contract Booz Allen won is a briefing nobody reads twice.
Scoring looks at the award *description* only, never at the recipient's name:
an employer called "Human Performance Solutions LLC" would otherwise have every
contract it holds, including the ones for facilities maintenance, flagged as a
coaching lead.
"""

from __future__ import annotations

import json
import logging
import math
import re
from dataclasses import dataclass
from datetime import date, timedelta
from typing import Any, Sequence

from .http import FetchError, post_json

log = logging.getLogger(__name__)

USASPENDING_ENDPOINT = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
"""The award search endpoint. Open: no key, no account, no signup."""

AWARD_TYPE_CODES: tuple[str, ...] = ("A", "B", "C", "D")
"""Contract award types: BPA calls, purchase orders, delivery orders, and
definitive contracts. Grants, loans, and direct payments are excluded -- they
do not staff a performance team."""

REQUEST_FIELDS: tuple[str, ...] = (
    "Award ID",
    "Recipient Name",
    "Award Amount",
    "Description",
    "Awarding Agency",
    "Awarding Sub Agency",
    "Start Date",
    "End Date",
    "Place of Performance State Code",
)

DEFAULT_KEYWORDS: tuple[str, ...] = (
    "h2f",
    "holistic health and fitness",
    "human performance",
    "POTFF",
    "THOR3",
    "tactical strength and conditioning",
    "athletic training services",
    "performance dietitian",
    "sports medicine services",
)
"""Keywords sent to the API's own full-text search.

Deliberately broader than what :func:`score_award` will accept. The API's
keyword search is the cheap coarse filter that keeps the download small; the
scorer is the precise one that decides what reaches a human. Reversing that --
narrow query, permissive scoring -- misses awards whose description spells the
program differently than the query did.
"""

MAX_API_LIMIT = 100
"""USAspending caps ``limit`` at 100 per page. Asking for more is an error."""


# ---------------------------------------------------------------------------
# scoring vocabulary
# ---------------------------------------------------------------------------
# Same two-axis idea as ``classify.py``, adapted to the fact that a contract
# description is a terse all-caps line and not a job ad. There is no title to
# weight, and no repetition to cap, so a term counts once.

PROGRAM_TERMS: dict[str, float] = {
    # Named DoD human performance programs. These phrases exist nowhere else in
    # federal contracting, so a hit is essentially proof.
    "holistic health and fitness": 6.0,
    "h2f": 5.5,
    "thor3": 6.0,
    "thor 3": 6.0,
    "potff": 6.0,
    "preservation of the force": 6.0,
    "preservation of the force and family": 6.0,
    "human performance program": 4.5,
    "human performance optimization": 4.5,
    "sports medicine and reconditioning": 5.0,
    "operator performance": 4.5,
    "tactical athlete": 4.5,
    "warfighter performance": 4.5,
    "performance triad": 4.0,
}

DISCIPLINE_TERMS: dict[str, float] = {
    # What the contract actually buys. An explicit discipline is a real lead
    # even when the program is unnamed, which is common on task orders.
    "tactical strength and conditioning": 5.0,
    "strength and conditioning": 4.0,
    "strength coach": 4.0,
    "human performance": 4.0,
    "athletic training services": 4.0,
    "athletic training": 3.5,
    "athletic trainer": 3.5,
    "sports medicine services": 4.0,
    "sports medicine": 3.5,
    "performance dietitian": 4.5,
    "registered dietitian": 3.5,
    "sports nutrition": 3.5,
    "dietitian services": 3.5,
    "exercise physiologist": 4.0,
    "exercise physiology": 3.5,
    "physical therapy services": 3.5,
    "physical therapist": 3.0,
    "physical therapy": 3.0,
    "occupational therapist": 2.5,
    "cognitive performance": 4.5,
    "mental performance": 4.0,
    "sport psychology": 3.5,
    "performance psychology": 3.5,
    "reconditioning": 3.0,
    "injury prevention": 2.5,
    "physical readiness": 2.5,
    "strength and conditioning coach": 4.5,
    "sport scientist": 3.5,
    "sport science": 3.0,
}

CONTEXT_TERMS: dict[str, float] = {
    # Population signal. A bonus, never a qualifier: on its own, "ARMY SUPPORT
    # SERVICES" is not a human performance award and must not be reported as
    # one. This is why these are scored separately from the two axes above.
    "special operations": 1.5,
    "special warfare": 1.5,
    "naval special warfare": 1.5,
    "socom": 1.5,
    "ussocom": 1.5,
    "usasoc": 1.5,
    "marsoc": 1.5,
    "afsoc": 1.5,
    "warfighter": 1.25,
    "soldier": 1.0,
    "airman": 1.0,
    "military": 0.75,
    "army": 0.5,
    "navy": 0.5,
    "air force": 0.5,
    "marine corps": 0.75,
    "brigade": 0.75,
    "battalion": 0.75,
    "readiness": 0.5,
    "installation": 0.25,
    "law enforcement": 1.0,
    "firefighter": 1.0,
    "first responder": 1.0,
}

CONTEXT_CAP = 3.0
"""Ceiling on the context bonus.

Federal descriptions stack population words ("ARMY SOLDIER READINESS BRIGADE
INSTALLATION SUPPORT") in a way that has nothing to do with how much human
performance work the contract buys. Without a cap, a verbose vehicle mentioning
one discipline in passing outranks a named H2F award, which inverts the entire
point of the briefing.
"""


# ---------------------------------------------------------------------------
# tolerant field access
# ---------------------------------------------------------------------------


def normalize_key(key: Any) -> str:
    """Fold a key to its comparable form.

    ``Award ID``, ``award_id``, ``awardId`` and ``AWARDID`` are the same field
    as far as the API is concerned, so they are the same key here.
    """
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _index(record: Any) -> dict[str, Any]:
    """Map a record's keys to their normalized form, first occurrence wins."""
    if not isinstance(record, dict):
        return {}
    index: dict[str, Any] = {}
    for key, value in record.items():
        index.setdefault(normalize_key(key), value)
    return index


_DISPLAY_KEYS = ("name", "value", "label", "text", "code", "abbreviation", "toptier_name")


def flatten(value: Any) -> str:
    """Flatten a scalar-ish value to display text.

    Most of these fields are plain strings, but the agency fields have come
    back as ``{"name": ...}`` objects in some shapes of this payload, and the
    place-of-performance block is sometimes a list. One flattener keeps that
    out of the mapping code.
    """
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        index = _index(value)
        for key in _DISPLAY_KEYS:
            inner = flatten(index.get(normalize_key(key)))
            if inner:
                return inner
        return ""
    if isinstance(value, (list, tuple)):
        parts = [flatten(item) for item in value]
        return ", ".join(part for part in parts if part)
    return ""


def pick_field(record: Any, *candidates: str, default: str = "") -> str:
    """First present, non-empty candidate key wins, compared normalized.

    Returns display text. Use :func:`pick_raw` when the caller needs the
    untouched value.
    """
    index = _index(record)
    for candidate in candidates:
        key = normalize_key(candidate)
        if key in index:
            text = flatten(index[key])
            if text:
                return text
    return default


def pick_raw(record: Any, *candidates: str) -> Any:
    """Like :func:`pick_field` but returns the raw value, or ``None``."""
    index = _index(record)
    for candidate in candidates:
        key = normalize_key(candidate)
        if key in index:
            value = index[key]
            if value not in (None, "", [], {}):
                return value
    return None


# Candidate keys per field. Casing variants collapse under ``normalize_key``,
# so what is listed here are the genuinely different names the same value has
# appeared under: the request label, and the underlying award record's own
# column name.
_AWARD_ID_KEYS = ("Award ID", "piid", "generated_internal_id", "internal_id", "id")
_RECIPIENT_KEYS = ("Recipient Name", "recipient", "recipient_name_raw", "Recipient")
_AMOUNT_KEYS = (
    "Award Amount",
    "total_obligation",
    "obligated_amount",
    "Total Outlays",
    "base_and_all_options_value",
)
_DESCRIPTION_KEYS = (
    "Description",
    "award_description",
    "transaction_description",
    "prime_award_base_transaction_description",
)
_AGENCY_KEYS = ("Awarding Agency", "awarding_toptier_agency_name", "awarding_agency_name")
_SUB_AGENCY_KEYS = (
    "Awarding Sub Agency",
    "awarding_subtier_agency_name",
    "awarding_sub_agency_name",
)
_START_KEYS = ("Start Date", "period_of_performance_start_date", "action_date")
_END_KEYS = (
    "End Date",
    "period_of_performance_current_end_date",
    "period_of_performance_potential_end_date",
)
_STATE_KEYS = (
    "Place of Performance State Code",
    "pop_state_code",
    "place_of_performance_state_code",
    "primary_place_of_performance_state_code",
    "State Code",
)

_RESULTS_KEYS = ("results", "Results", "data", "records")
_METADATA_KEYS = ("page_metadata", "pageMetadata", "page_meta_data")
_HAS_NEXT_KEYS = ("hasNext", "has_next", "hasNextPage", "next")


# ---------------------------------------------------------------------------
# value readers
# ---------------------------------------------------------------------------

_ISO_DATE = re.compile(r"^(\d{4})-(\d{2})-(\d{2})")


def parse_amount(value: Any) -> float | None:
    """Read a dollar figure out of a number or a string like ``"$1,234,567"``.

    The API has emitted this field as a JSON number, as a formatted string, and
    as ``null`` for awards whose value is not published. All three are normal,
    so none of them raises. A bool is rejected outright: ``bool`` is an ``int``
    subclass, and a flag is not an amount.
    """
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value) if math.isfinite(float(value)) else None
    if isinstance(value, str):
        # Strip currency symbols, thousands separators, and stray whitespace.
        # Parentheses are dropped rather than read as a negative -- this feed
        # writes deobligations with a leading minus, and guessing the
        # accounting convention on a scraped string is worse than not.
        stripped = re.sub(r"[^0-9.\-]", "", value)
        if not stripped or stripped in {"-", ".", "-.", "."}:
            return None
        try:
            parsed = float(stripped)
        except ValueError:
            return None
        return parsed if math.isfinite(parsed) else None
    return None


def _clean(value: Any) -> str:
    """Collapse whitespace in a string-ish value; anything else becomes ""."""
    if not isinstance(value, str):
        return ""
    return " ".join(value.split())


def _iso_date(value: Any) -> str | None:
    """Normalize a date to ``YYYY-MM-DD``, or keep the text, or ``None``.

    Dates are kept as strings on purpose: nothing here does date arithmetic,
    the briefing prints them verbatim, and ISO strings already sort correctly.
    Parsing them into ``datetime`` would only create a way for one malformed
    field to take down a run.
    """
    text = _clean(flatten(value))
    if not text:
        return None
    match = _ISO_DATE.match(text)
    return match.group(0) if match else text


def _sortable_date(value: str | None) -> str:
    """Sort key for a date string; unparseable dates sort before real ones."""
    text = _clean(value)
    return text if _ISO_DATE.match(text) else ""


# ---------------------------------------------------------------------------
# the award
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class ContractAward:
    """One federal contract action, read as a hiring signal.

    Every field defaults, because every field of this payload has been observed
    absent on some award, and a lead with a recipient and a description is
    still a usable lead without a place of performance.
    """

    award_id: str = ""
    recipient: str = ""
    amount: float | None = None
    description: str = ""
    agency: str | None = None
    sub_agency: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    state: str | None = None
    relevance: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "award_id": self.award_id,
            "recipient": self.recipient,
            "amount": self.amount,
            "description": self.description,
            "agency": self.agency,
            "sub_agency": self.sub_agency,
            "start_date": self.start_date,
            "end_date": self.end_date,
            "state": self.state,
            "relevance": self.relevance,
        }


def to_award(record: Any) -> ContractAward | None:
    """Map one API result to a :class:`ContractAward`, scored.

    Returns ``None`` for anything that is not a usable record -- a scalar, a
    null, or an award with no recipient. An award with no recipient names
    nobody, and "who is about to hire" is the only question this module asks.
    """
    if not isinstance(record, dict):
        return None

    recipient = pick_field(record, *_RECIPIENT_KEYS)
    if not recipient:
        return None

    award = ContractAward(
        award_id=pick_field(record, *_AWARD_ID_KEYS),
        recipient=recipient,
        amount=parse_amount(pick_raw(record, *_AMOUNT_KEYS)),
        description=pick_field(record, *_DESCRIPTION_KEYS),
        agency=pick_field(record, *_AGENCY_KEYS) or None,
        sub_agency=pick_field(record, *_SUB_AGENCY_KEYS) or None,
        start_date=_iso_date(pick_raw(record, *_START_KEYS)),
        end_date=_iso_date(pick_raw(record, *_END_KEYS)),
        state=pick_field(record, *_STATE_KEYS) or None,
    )
    award.relevance = score_award(award)
    return award


# ---------------------------------------------------------------------------
# scoring
# ---------------------------------------------------------------------------


def _haystack(text: str) -> str:
    """Lowercase, punctuation flattened to spaces, padded for whole-word tests."""
    return f" {re.sub(r'[^a-z0-9]+', ' ', str(text).lower()).strip()} "


def _axis(terms: dict[str, float], haystack: str) -> tuple[float, list[str]]:
    """Score one vocabulary against a prepared haystack.

    A term counts once no matter how often it appears. Contract descriptions
    are one terse line, so repetition carries no extra information -- unlike a
    job ad, where ``classify.py`` counts up to :data:`classify.DESCRIPTION_CAP`.
    """
    total = 0.0
    hits: list[str] = []
    for term, weight in terms.items():
        needle = f" {re.sub(r'[^a-z0-9]+', ' ', term).strip()} "
        if needle in haystack:
            hits.append(term)
            total += weight
    return total, hits


def score_award(award: ContractAward) -> float:
    """How strongly this award predicts tactical human performance hiring.

    Zero means "not a lead" and callers drop it. That is a rejection, not a low
    rank: the description has to name a program or a discipline. Population
    words alone ("ARMY", "SOLDIER SUPPORT SERVICES") never qualify an award,
    because a prime's unrelated contracts are full of them and listing those is
    what makes an award briefing useless.
    """
    haystack = _haystack(getattr(award, "description", "") or "")
    if not haystack.strip():
        return 0.0

    program_score, program_hits = _axis(PROGRAM_TERMS, haystack)
    discipline_score, discipline_hits = _axis(DISCIPLINE_TERMS, haystack)
    if not program_hits and not discipline_hits:
        return 0.0

    context_score, _ = _axis(CONTEXT_TERMS, haystack)
    return round(program_score + discipline_score + min(context_score, CONTEXT_CAP), 2)


# ---------------------------------------------------------------------------
# fetching
# ---------------------------------------------------------------------------


def _decode(body: Any) -> Any:
    """Parse whatever the POST helper handed back.

    ``http.post_json`` returns raw bytes, so the normal path is a decode. A
    caller (or a test double) that already holds parsed JSON is passed through
    unchanged rather than being re-serialized just to be parsed again.
    """
    if isinstance(body, (bytes, bytearray)):
        body = bytes(body).decode("utf-8", "replace")
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise FetchError(f"{USASPENDING_ENDPOINT} returned non-JSON body: {exc}") from exc
    return body


def build_request(
    keywords: Sequence[str], *, since_days: int, limit: int, page: int
) -> dict[str, Any]:
    """The exact POST body for one page of the award search.

    Exposed so an operator can paste it into curl and see the same thing this
    module sees -- the endpoint takes no key, so that reproduction is free.
    """
    end = date.today()
    start = end - timedelta(days=max(1, since_days))
    return {
        "filters": {
            "keywords": list(keywords),
            "award_type_codes": list(AWARD_TYPE_CODES),
            "time_period": [
                {"start_date": start.isoformat(), "end_date": end.isoformat()}
            ],
        },
        "fields": list(REQUEST_FIELDS),
        "page": page,
        "limit": limit,
        "sort": "Award Amount",
        "order": "desc",
    }


def fetch_awards(
    *,
    keywords: Sequence[str] | None = None,
    since_days: int = 365,
    limit: int = 100,
    max_pages: int = 5,
) -> list[ContractAward]:
    """Search USAspending and return the awards that read as hiring signals.

    Keyless: the endpoint needs no token, no account, and no signup.

    Pagination follows ``page_metadata.hasNext`` and stops at ``max_pages``
    regardless -- a broken ``hasNext`` that is always true would otherwise walk
    the entire federal contract corpus one hundred rows at a time.

    A failure on page 1 propagates. A first page that will not load is a broken
    endpoint or a broken query, and reporting that as "no awards found" would
    look exactly like a quiet quarter. A failure on a later page is logged and
    ends the walk with the awards already collected, which are real.
    """
    terms = [str(term) for term in (keywords if keywords else DEFAULT_KEYWORDS) if str(term).strip()]
    if not terms:
        terms = list(DEFAULT_KEYWORDS)
    page_size = max(1, min(int(limit), MAX_API_LIMIT))
    pages = max(1, int(max_pages))

    awards: list[ContractAward] = []
    seen: set[str] = set()

    for page in range(1, pages + 1):
        request = build_request(terms, since_days=since_days, limit=page_size, page=page)
        try:
            payload = _decode(post_json(USASPENDING_ENDPOINT, request))
        except Exception as exc:
            if page == 1:
                raise
            log.warning("usaspending page %d failed: %s", page, exc)
            break

        results = pick_raw(payload, *_RESULTS_KEYS)
        if not isinstance(results, list) or not results:
            break

        for record in results:
            try:
                award = to_award(record)
            except Exception as exc:  # pragma: no cover - defensive
                # One unusable record must never cost us the rest of the page.
                log.warning("skipping malformed award record: %s", exc)
                continue
            if award is None:
                log.debug("skipping unusable award record %r", record)
                continue
            if award.relevance <= 0:
                # Not a near miss -- no human performance signal at all.
                continue
            key = award.award_id or f"{award.recipient}|{award.start_date}|{award.description[:80]}"
            if key in seen:
                continue
            seen.add(key)
            awards.append(award)

        metadata = pick_raw(payload, *_METADATA_KEYS)
        if not _as_bool(pick_raw(metadata, *_HAS_NEXT_KEYS)):
            break

    awards.sort(
        key=lambda award: (-award.relevance, -(award.amount or 0.0), award.recipient.casefold())
    )
    return awards


_FALSEY_TEXT = frozenset({"", "false", "f", "no", "n", "0", "none", "null"})


def _as_bool(value: Any) -> bool:
    """Truthiness that survives an API writing its booleans as strings."""
    if isinstance(value, str):
        return _clean(value).casefold() not in _FALSEY_TEXT
    return bool(value)


# ---------------------------------------------------------------------------
# aggregation
# ---------------------------------------------------------------------------


def _agency_label(award: ContractAward) -> str:
    parts = [_clean(award.agency), _clean(award.sub_agency)]
    return " / ".join(part for part in parts if part)


def rank_recipients(
    awards: Sequence[ContractAward], *, top_n: int = 25
) -> list[dict[str, Any]]:
    """Roll awards up to the employer -- the unit a job hunter can act on.

    One contractor holding four task orders is one employer to watch, not four.
    Recipients are merged case-insensitively (the same prime is written "ACME
    CORPORATION" on one action and "Acme Corporation" on the next) with the
    first spelling seen kept for display.

    Ranked by total award value: on a services contract, dollars are the only
    public proxy for headcount, and headcount is what turns into postings. Ties
    break on award count, then name, so a committed briefing does not churn.

    ``top_n`` of zero or less means "everything".
    """
    groups: dict[str, dict[str, Any]] = {}

    for award in awards:
        recipient = _clean(getattr(award, "recipient", ""))
        if not recipient:
            continue
        key = recipient.casefold()
        entry = groups.get(key)
        if entry is None:
            entry = {
                "recipient": recipient,
                "awards": 0,
                "total_amount": 0.0,
                "awards_missing_amount": 0,
                "agencies": [],
                "states": [],
                "award_ids": [],
                "latest_award_date": None,
                "top_relevance": 0.0,
                "top_description": "",
            }
            groups[key] = entry

        entry["awards"] += 1
        amount = getattr(award, "amount", None)
        if amount is None:
            entry["awards_missing_amount"] += 1
        else:
            entry["total_amount"] += float(amount)

        agency = _agency_label(award)
        if agency and agency not in entry["agencies"]:
            entry["agencies"].append(agency)
        state = _clean(getattr(award, "state", ""))
        if state and state not in entry["states"]:
            entry["states"].append(state)
        award_id = _clean(getattr(award, "award_id", ""))
        if award_id and award_id not in entry["award_ids"]:
            entry["award_ids"].append(award_id)

        start = getattr(award, "start_date", None)
        if _sortable_date(start) > _sortable_date(entry["latest_award_date"]):
            entry["latest_award_date"] = _clean(start) or None

        relevance = float(getattr(award, "relevance", 0.0) or 0.0)
        if relevance > entry["top_relevance"] or not entry["top_description"]:
            entry["top_relevance"] = max(relevance, entry["top_relevance"])
            entry["top_description"] = _clean(getattr(award, "description", ""))

    ranked = sorted(
        groups.values(),
        key=lambda entry: (
            -entry["total_amount"],
            -entry["awards"],
            entry["recipient"].casefold(),
        ),
    )
    for entry in ranked:
        entry["total_amount"] = round(entry["total_amount"], 2)
        entry["agencies"] = sorted(entry["agencies"])
        entry["states"] = sorted(entry["states"])
    return ranked if top_n <= 0 else ranked[:top_n]


# ---------------------------------------------------------------------------
# the briefing
# ---------------------------------------------------------------------------


def _money(value: Any) -> str:
    amount = parse_amount(value)
    return f"${amount:,.0f}" if amount is not None else "not published"


def _cell(value: Any, width: int = 70) -> str:
    """A value safe to drop in a Markdown table cell."""
    text = _clean(flatten(value)).replace("|", "\\|")
    return text if len(text) <= width else text[: width - 1] + "…"


def render_leads(awards: Sequence[ContractAward], *, top_n: int = 25) -> str:
    """A Markdown briefing whose next action is obvious on every line.

    The artifact is for a human, and the only useful thing a human can do with
    an award is go find the winner's job board. So every recipient block ends
    with that instruction and a search string, and nothing here writes config:
    a wrong board token fails silently forever, which is far worse than a
    thirty-second lookup.
    """
    recipients = rank_recipients(awards, top_n=top_n)
    usable = [award for award in awards if _clean(getattr(award, "recipient", ""))]

    lines = [
        "# Contract award leads — who is about to hire",
        "",
        "A contract award is public the day it is signed, which is weeks to months "
        "before the first requisition appears on any job board. Every recipient "
        "below has work to staff and no postings up yet.",
        "",
    ]

    if not recipients:
        lines += [
            "_No relevant awards found._",
            "",
            "Either nothing scored above the human performance floor in this window, "
            "or the search window is too short. Widen `since_days` before concluding "
            "the market is quiet.",
            "",
        ]
        return "\n".join(lines) + "\n"

    total_value = sum(entry["total_amount"] for entry in recipients)
    lines += [
        f"**{len(usable)} relevant award(s)** across **{len(recipients)} recipient(s)** "
        f"shown, worth **{_money(total_value)}** in published value.",
        "",
        "---",
        "",
    ]

    for position, entry in enumerate(recipients, start=1):
        name = entry["recipient"]
        lines += [
            f"## {position}. {name}",
            "",
            f"- **Total award value:** {_money(entry['total_amount'])} "
            f"across {entry['awards']} award(s)",
        ]
        if entry["awards_missing_amount"]:
            lines.append(
                f"- **Note:** {entry['awards_missing_amount']} of those award(s) "
                "publish no dollar value, so the total understates the work"
            )
        lines.append(
            "- **Agencies:** " + (", ".join(entry["agencies"]) or "not published")
        )
        if entry["states"]:
            lines.append("- **Place of performance:** " + ", ".join(entry["states"]))
        lines.append(
            f"- **Latest award start:** {entry['latest_award_date'] or 'not published'}"
        )
        if entry["top_description"]:
            lines.append(
                f"- **Strongest signal** (relevance {entry['top_relevance']:.1f}): "
                f"{_cell(entry['top_description'], 200)}"
            )
        if entry["award_ids"]:
            shown = ", ".join(f"`{award_id}`" for award_id in entry["award_ids"][:5])
            lines.append(f"- **Award IDs:** {shown}")
        lines += [
            "",
            f"- **Next step: find this employer's ATS board.** Search "
            f"`\"{name}\" careers greenhouse OR lever OR workday OR icims`, confirm the "
            "board token, then add it to `sources.toml` and to the discovery "
            "watchlist. Do not guess the token — a wrong one returns nothing, "
            "silently, forever.",
            "",
        ]

    shown_awards = sorted(
        usable,
        key=lambda award: (
            -float(getattr(award, "relevance", 0.0) or 0.0),
            -(getattr(award, "amount", None) or 0.0),
        ),
    )[: top_n if top_n > 0 else len(usable)]

    lines += [
        "---",
        "",
        "## Awards behind these leads",
        "",
        "| Award | Recipient | Amount | Agency | Start | State | Score |",
        "|---|---|---:|---|---|---|---:|",
    ]
    for award in shown_awards:
        lines.append(
            "| {award_id} | {recipient} | {amount} | {agency} | {start} | {state} | {score:.1f} |".format(
                award_id=_cell(award.award_id, 24) or "—",
                recipient=_cell(award.recipient, 40),
                amount=_money(award.amount),
                agency=_cell(_agency_label(award), 40) or "—",
                start=_cell(award.start_date, 12) or "—",
                state=_cell(award.state, 8) or "—",
                score=float(getattr(award, "relevance", 0.0) or 0.0),
            )
        )
    lines.append("")

    return "\n".join(lines) + "\n"
