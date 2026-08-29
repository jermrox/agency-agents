"""Public-sector boards, association career centers, and arbitrary JSON.

Three adapters for the inventory the ATS adapters structurally cannot see:

``governmentjobs``
    NEOGOV / governmentjobs.com. Fire departments, police departments,
    sheriff's offices, county EMS, and state agencies hire wellness
    coordinators, peer fitness trainers, and embedded athletic trainers --
    and they post to NEOGOV, not to Greenhouse or Workday. Municipal hiring
    is a whole population of tactical human performance work that is
    otherwise invisible to this project.

``jobsrss``
    The professional-association career centers (NSCA, NATA, ACSM, CSCCa,
    AASP) that run on YourMembership, Community Brands, and Naylor. They all
    emit RSS, but they cram the employer and the city into the item *title*
    instead of using structured fields, so the generic ``rss`` adapter labels
    every posting with the feed name and no location. This one takes those
    titles apart.

``genericjson``
    A configuration-only escape hatch for a career page that returns JSON in
    a shape nobody else uses. Rather than write a throwaway module per
    employer, point ``field_map`` at the paths and move on.

A note on tolerance. NEOGOV is a tenant-hosted product and its JSON envelope
key names genuinely differ between tenants -- ``items`` vs ``jobs``, ``id``
vs ``jobId``, ``datePosted`` vs ``date_posted`` vs ``PostedDate``. The
alternative to a tolerant field-picker is a per-tenant adapter, which does
not scale past the first three cities. So :func:`pick_field` takes a list of
candidate keys, compares them with punctuation and case normalized away, and
returns the first present non-empty one. That tolerance is deliberate, not
sloppiness: it is the whole reason one adapter can cover many tenants.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Iterable
from urllib.parse import urljoin

from ..http import fetch, fetch_json
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

log = logging.getLogger(__name__)

GOVERNMENTJOBS_HOST = "https://www.governmentjobs.com"


# ---------------------------------------------------------------------------
# tolerant field access
# ---------------------------------------------------------------------------


def normalize_key(key: Any) -> str:
    """Fold a key to its comparable form.

    ``jobTitle``, ``job_title``, ``Job Title`` and ``JOBTITLE`` are the same
    field as far as any tenant is concerned, so they must be the same key as
    far as this module is concerned.
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


_DISPLAY_KEYS = (
    "name", "value", "label", "text", "descriptor", "title", "display",
    "displayName",
    # Link objects (``{"href": "/careers/x/jobs/1"}``) are how several tenants
    # emit the detail link. Without these a record whose only link is an
    # object resolves to no url at all, and the posting is dropped outright.
    "href", "url", "link", "uri",
)

_CITY_KEYS = ("city", "cityName", "locality", "town")
_REGION_KEYS = ("state", "stateProvince", "stateCode", "region", "province")


def flatten(value: Any) -> str:
    """Flatten a scalar-ish value to display text.

    Vendors emit the same logical field as a bare string, as a small object
    (``{"name": ...}``), as an address object (``{"city": ..., "state": ...}``),
    as a link object (``{"href": ...}``), or as a list of any of those. One
    flattener here keeps that mess out of the mapping code.
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
        # An address object carries no single display key, so compose one.
        # Location drives the location filter and the remote heuristic, and a
        # silently empty location reads downstream as "location unknown".
        city = next(
            (t for t in (flatten(index.get(normalize_key(k))) for k in _CITY_KEYS) if t),
            "",
        )
        region = next(
            (t for t in (flatten(index.get(normalize_key(k))) for k in _REGION_KEYS) if t),
            "",
        )
        return ", ".join(part for part in (city, region) if part)
    if isinstance(value, (list, tuple)):
        parts = [flatten(item) for item in value]
        return ", ".join(part for part in parts if part)
    return ""


def as_int(value: Any, default: int) -> int:
    """Coerce a config option to an int, falling back to ``default``.

    Options arrive from TOML, from JSON, and from operators editing by hand,
    so a blank or mistyped numeric option is normal. Aborting the whole
    source over it -- which ``int(None)`` does -- is not.
    """
    if isinstance(value, bool) or value is None:
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        log.warning("ignoring non-numeric option value %r, using %d", value, default)
        return default


def pick_field(record: Any, *candidates: str, default: str = "") -> str:
    """First present, non-empty candidate key wins, compared normalized.

    Returns display text. Use :func:`pick_raw` when the caller needs the
    untouched value (timestamps, booleans, nested structures).
    """
    index = _index(record)
    for candidate in candidates:
        if normalize_key(candidate) in index:
            text = flatten(index[normalize_key(candidate)])
            if text:
                return text
    return default


def pick_raw(record: Any, *candidates: str) -> Any:
    """Like :func:`pick_field` but returns the raw value, or ``None``."""
    index = _index(record)
    for candidate in candidates:
        if normalize_key(candidate) in index:
            value = index[normalize_key(candidate)]
            if value not in (None, "", [], {}):
                return value
    return None


def _blob(value: Any, depth: int = 0) -> str:
    """Flatten an arbitrary value into description text, markup intact."""
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, (list, tuple)):
        return "\n".join(part for part in (_blob(v, depth + 1) for v in value) if part)
    if isinstance(value, dict):
        if depth > 2:
            return ""
        parts = (_blob(v, depth + 1) for k, v in value.items() if not str(k).startswith("@"))
        return "\n".join(part for part in parts if part)
    return ""


# ---------------------------------------------------------------------------
# dot paths
# ---------------------------------------------------------------------------


def resolve_path(payload: Any, path: str | None) -> Any:
    """Walk a dot path such as ``data.jobs.0.title``.

    An empty path (or ``None``) means "the payload itself", which is how a
    response whose root *is* the array of records is configured. A missing
    intermediate key returns ``None`` rather than raising, because a career
    page that dropped one optional field must not take down the run. Numeric
    segments index into lists.
    """
    if path is None or str(path).strip() == "":
        return payload

    current = payload
    for part in str(path).strip().split("."):
        if current is None:
            return None
        if isinstance(current, dict):
            if part in current:
                current = current[part]
                continue
            return None
        if isinstance(current, (list, tuple)):
            stripped = part[1:] if part.startswith("-") else part
            if not stripped.isdigit():
                return None
            try:
                current = current[int(part)]
            except IndexError:
                return None
            continue
        return None
    return current


# ---------------------------------------------------------------------------
# NEOGOV / governmentjobs.com
# ---------------------------------------------------------------------------

_ENVELOPE_KEYS = (
    "items", "jobs", "results", "postings", "openings", "records",
    "jobPostings", "positions", "data", "content", "list",
)

_ID_KEYS = (
    "id", "jobId", "postingId", "recruitmentId", "positionId",
    "jobPostingId", "reqId", "requisitionId",
)
_TITLE_KEYS = ("title", "jobTitle", "positionTitle", "classTitle", "name", "position")
_LINK_KEYS = (
    "detailUrl", "jobDetailUrl", "jobUrl", "detailLink", "url", "link",
    "href", "permalink", "applyUrl",
)
_LOCATION_KEYS = ("location", "jobLocation", "locationName", "workLocation", "locations")
_DEPARTMENT_KEYS = (
    "department", "departmentName", "division", "bureau", "agency",
    "agencyName", "office",
)
_JOB_TYPE_KEYS = ("jobType", "employmentType", "positionType", "jobStatus", "schedule", "type")
_DATE_KEYS = (
    "datePosted", "postedDate", "openDate", "publishDate", "postingDate",
    "dateOpened", "firstPublishedDate", "createdAt",
)
_CLOSING_KEYS = ("closingDate", "closeDate", "dateClosed", "endDate", "applicationDeadline")
_SALARY_KEYS = (
    "salaryDisplay", "salary", "salaryRange", "salaryText", "payRange",
    "compensation", "salaryInfo",
)
_SALARY_MIN_KEYS = ("salaryMin", "minSalary", "salaryFrom", "salaryLow", "payMin")
_SALARY_MAX_KEYS = ("salaryMax", "maxSalary", "salaryTo", "salaryHigh", "payMax")
_SALARY_UNIT_KEYS = ("salaryFrequency", "payFrequency", "salaryUnit", "salaryPer", "rateOfPay")

_NARRATIVE_KEYS = (
    "description", "jobDescription", "definition", "jobSummary", "summary",
    "essentialFunctions", "exampleOfDuties", "examplesOfDuties",
    "typicalQualifications", "minimumQualifications", "preferredQualifications",
    "knowledgeSkillsAbilities", "supplementalInformation", "benefits",
    "requirements", "jobDetails", "body",
)
"""Every free-text field NEOGOV tenants use.

The certifications (CSCS, TSAC-F, ATC, RD), the peer-fitness-trainer
language, and the salary schedule are routinely split across
``minimumQualifications`` and ``supplementalInformation`` rather than sitting
in ``description``, so all of them are captured and concatenated.
"""

_DETAIL_WRAPPER_KEYS = ("job", "posting", "jobPosting", "jobDetail", "result", "data", "item")


def envelope_records(payload: Any, depth: int = 0) -> list[Any]:
    """Find the array of job records inside a tenant's JSON envelope.

    Handles the root-is-an-array case, the flat ``{"items": [...]}`` case,
    and the wrapped ``{"data": {"jobs": [...]}}`` case that some tenants
    return. Only arrays sitting under a known envelope key count, so a stray
    list of facet values is never mistaken for the job list.
    """
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict) or depth > 3:
        return []

    index = _index(payload)
    for key in _ENVELOPE_KEYS:
        value = index.get(normalize_key(key))
        if isinstance(value, list):
            return value

    for value in payload.values():
        if isinstance(value, dict):
            nested = envelope_records(value, depth + 1)
            if nested:
                return nested
    return []


def _detail_record(payload: Any) -> dict[str, Any]:
    """Unwrap a detail response, merging any wrapper object into the root."""
    if isinstance(payload, list):
        # Some tenants answer a detail request with a one-element array. The
        # request has already been made and the budget already spent, so
        # throwing the body away would ship a title-only record for no reason.
        payload = next((item for item in payload if isinstance(item, dict)), None)
    if not isinstance(payload, dict):
        return {}
    merged = dict(payload)
    for key in _DETAIL_WRAPPER_KEYS:
        nested = pick_raw(payload, key)
        if isinstance(nested, dict):
            merged.update(nested)
            break
    return merged


def _narrative(record: Any) -> str:
    """Concatenate every free-text field present, in a stable order."""
    index = _index(record)
    parts: list[str] = []
    for key in _NARRATIVE_KEYS:
        text = html_to_text(_blob(index.get(normalize_key(key))))
        if text and text not in parts:
            parts.append(text)
    return "\n\n".join(parts)


def _range(scope: Any, extra_min: tuple[str, ...] = (), extra_max: tuple[str, ...] = (),
           extra_unit: tuple[str, ...] = ()) -> str:
    low = pick_field(scope, *_SALARY_MIN_KEYS, *extra_min)
    high = pick_field(scope, *_SALARY_MAX_KEYS, *extra_max)
    unit = pick_field(scope, *_SALARY_UNIT_KEYS, *extra_unit)
    if low and high:
        return f"{low} - {high} {unit}".strip()
    return (low or high or "").strip()


def _compensation(record: Any) -> str:
    """A rendered pay string, from a display field, min/max fields, or an object.

    Pay is the field operators most often ask about, and the third shape --
    ``{"salary": {"min": 62000, "max": 78000, "frequency": "Annually"}}`` --
    has no display key at all, so reading only the flat fields loses it
    entirely for those tenants.
    """
    display = pick_field(record, *_SALARY_KEYS)
    if display:
        return display

    flat = _range(record)
    if flat:
        return flat

    container = pick_raw(record, *_SALARY_KEYS)
    if isinstance(container, dict):
        # Inside a salary object the bare keys are unambiguous; at the top
        # level of a record they are not, which is why they live only here.
        nested = _range(
            container,
            extra_min=("min", "from", "low", "start", "amount"),
            extra_max=("max", "to", "high", "end"),
            extra_unit=("frequency", "unit", "per", "period", "interval"),
        )
        if nested:
            return nested
    return ""


def _absolute(url: str, base: str = GOVERNMENTJOBS_HOST) -> str:
    """Resolve a link that may be absolute, root-relative, or path-relative."""
    if not url:
        return ""
    if url.startswith(("http://", "https://")):
        return url
    return urljoin(base, url)


class GovernmentJobsSource(Source):
    """One NEOGOV / governmentjobs.com careers site.

    Options
    -------
    agency
        The careers slug, i.e. ``austintx`` in
        ``governmentjobs.com/careers/austintx``. Required unless ``url`` is
        given.
    url
        Full list-endpoint override. NEOGOV tenants vary enough that an
        operator sometimes has to paste the exact URL their tenant answers
        on; that always wins over the slug.
    employer
        Display employer. Defaults to the agency slug, then the source name.
    max_pages
        Pages of the list endpoint to walk. Default 5.
    detail_limit
        How many detail requests one run may spend. Default 50.
    detail_min_chars
        A list description shorter than this triggers a detail fetch.
        Default 400 -- NEOGOV list payloads carry a one-line teaser, and the
        analysis layer needs the full posting.
    """

    kind = "governmentjobs"

    def fetch(self) -> Iterable[JobPosting]:
        list_url = self._list_url()
        agency = str(self.options.get("agency") or "").strip().strip("/")
        employer = self.options.get("employer") or agency or self.name
        max_pages = max(1, as_int(self.options.get("max_pages"), 5))
        detail_budget = as_int(self.options.get("detail_limit"), 50)
        min_chars = as_int(self.options.get("detail_min_chars"), 400)
        # Relative tenant links resolve against the endpoint actually in use.
        # With a ``url`` override that is a different host entirely, resolving
        # them against governmentjobs.com would point the detail fetch -- and
        # the fallback public url -- at the wrong site.
        link_base = list_url

        seen: set[str] = set()
        for page in range(1, max_pages + 1):
            try:
                payload = fetch_json(list_url, params=self._params(list_url, page))
            except Exception as exc:
                # A first page that will not load is a broken config, not a
                # flaky page: surface it rather than reporting zero jobs as
                # a successful run.
                if page == 1:
                    raise
                log.warning("%s: governmentjobs page %d failed: %s", self.name, page, exc)
                break

            records = envelope_records(payload)
            if not records:
                break

            fresh = 0
            for record in records:
                if not isinstance(record, dict):
                    log.debug("%s: skipping non-object record %r", self.name, record)
                    continue
                try:
                    posting, spent = self._to_posting(
                        record, employer, detail_budget > 0, min_chars, link_base
                    )
                except Exception as exc:  # pragma: no cover - defensive
                    # One unusable record must never cost us the rest of the board.
                    log.warning("%s: skipping malformed record: %s", self.name, exc)
                    continue
                if spent:
                    detail_budget -= 1
                if posting is None or posting.source_id in seen:
                    continue
                seen.add(posting.source_id)
                fresh += 1
                yield posting

            if not fresh:
                # A tenant that ignores ``page`` returns page 1 forever.
                break
            # ``totalPages`` arrives as a JSON number from some tenants and as
            # a string from others; honouring only the number would keep
            # requesting pages the tenant already said do not exist.
            total_pages = as_int(
                pick_raw(payload, "totalPages", "pageCount", "pages", "numberOfPages"), 0
            )
            if total_pages > 0 and page >= total_pages:
                break

    # -- request construction --------------------------------------------

    def _list_url(self) -> str:
        override = str(self.options.get("url") or "").strip()
        if override:
            return override
        agency = str(self.require("agency")).strip().strip("/")
        return f"{GOVERNMENTJOBS_HOST}/careers/{agency}"

    def _params(self, url: str, page: int) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if "format=" not in url:
            params["format"] = "json"
        params["page"] = page
        return params

    def _detail(self, url: str) -> dict[str, Any]:
        """Fetch one posting's detail JSON, or ``{}`` if it is unavailable."""
        if not url:
            return {}
        params = None if "format=" in url else {"format": "json"}
        try:
            payload = fetch_json(url, params=params)
        except Exception as exc:
            log.debug("%s: detail fetch failed for %s: %s", self.name, url, exc)
            return {}
        return _detail_record(payload)

    # -- mapping ----------------------------------------------------------

    def _to_posting(
        self,
        record: dict[str, Any],
        employer: str,
        may_fetch_detail: bool,
        min_chars: int,
        link_base: str = GOVERNMENTJOBS_HOST,
    ) -> tuple[JobPosting | None, bool]:
        job_id = pick_field(record, *_ID_KEYS)
        title = pick_field(record, *_TITLE_KEYS)
        link = _absolute(pick_field(record, *_LINK_KEYS), link_base)
        # The canonical public permalink; the tenant's own link is only a
        # fallback for records that carry no id.
        url = f"{GOVERNMENTJOBS_HOST}/jobs/{job_id}" if job_id else link
        if not title or not url:
            log.debug("%s: skipping record without a title or url: %r", self.name, record)
            return None, False

        description = _narrative(record)
        detail: dict[str, Any] = {}
        spent_detail = False
        if may_fetch_detail and len(description) < min_chars:
            detail = self._detail(link or url)
            # The attempt is what costs a request, so the attempt is what the
            # budget counts -- otherwise a tenant whose detail pages all 404
            # would fan out without limit.
            spent_detail = True
            detail_text = _narrative(detail)
            if len(detail_text) > len(description):
                description = detail_text

        merged: dict[str, Any] = {**record, **detail} if detail else record

        location = pick_field(merged, *_LOCATION_KEYS)
        if not location:
            city = pick_field(merged, "city", "cityName")
            state = pick_field(merged, "state", "stateProvince", "region")
            location = ", ".join(part for part in (city, state) if part)

        job_type = pick_field(merged, *_JOB_TYPE_KEYS)
        compensation = _compensation(merged)
        department = pick_field(merged, *_DEPARTMENT_KEYS)
        closing = pick_field(merged, *_CLOSING_KEYS)

        # Fold the structured facts into the text so the classifier and the
        # enrichment layer see them without special-casing this schema.
        facts = [
            f"{label} {value}."
            for label, value in (
                ("Job type:", job_type),
                ("Salary:", compensation),
                ("Department:", department),
                ("Closing date:", closing),
            )
            if value
        ]
        if facts:
            description = f"{description}\n\n{' '.join(facts)}".strip()

        raw: dict[str, Any] = {"listing": record}
        if detail:
            raw["detail"] = detail

        return (
            JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=job_id or url,
                url=url,
                title=title,
                employer=employer,
                location=location,
                description=description,
                posted_at=parse_timestamp(pick_raw(merged, *_DATE_KEYS)),
                remote=looks_remote(location, title, job_type),
                department=department or None,
                compensation=compensation or None,
                raw=raw,
            ),
            spent_detail,
        )


# ---------------------------------------------------------------------------
# association career-center feeds
# ---------------------------------------------------------------------------

_NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}

_STATE_ABBREVIATIONS = frozenset(
    "AL AK AZ AR CA CO CT DE DC FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN "
    "MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA "
    "WV WI WY PR GU VI AS MP".split()
)
_STATE_NAMES = frozenset(
    name.lower()
    for name in (
        "Alabama", "Alaska", "Arizona", "Arkansas", "California", "Colorado",
        "Connecticut", "Delaware", "District of Columbia", "Florida", "Georgia",
        "Hawaii", "Idaho", "Illinois", "Indiana", "Iowa", "Kansas", "Kentucky",
        "Louisiana", "Maine", "Maryland", "Massachusetts", "Michigan",
        "Minnesota", "Mississippi", "Missouri", "Montana", "Nebraska", "Nevada",
        "New Hampshire", "New Jersey", "New Mexico", "New York",
        "North Carolina", "North Dakota", "Ohio", "Oklahoma", "Oregon",
        "Pennsylvania", "Rhode Island", "South Carolina", "South Dakota",
        "Tennessee", "Texas", "Utah", "Vermont", "Virginia", "Washington",
        "West Virginia", "Wisconsin", "Wyoming", "Puerto Rico", "Guam",
    )
)
"""Locations are validated against real states.

Association titles are full of comma-separated fragments -- "Coach, Football"
-- and treating every one of them as a city/state pair would fill the
location column with nonsense. Requiring a genuine state keeps the parser
honest and lets it fail closed.
"""

# "telework" belongs here and nowhere else. These lists answer "does this
# fragment read as a LOCATION?" for title parsing -- "Coach - Telework (CONUS)"
# has a location in the tail, not an employer. Whether the job is actually
# remote is a different question, answered by REMOTE_HINTS in base.py and
# _REMOTE_RE in facets.py, and telework is deliberately absent from both.
_REMOTE_LOCATION_HINTS = (
    "work from home", "work at home", "multiple locations", "remote", "nationwide",
    "virtual", "telework", "telecommute", "anywhere",
)
_REMOTE_QUALIFIERS = frozenset(
    {
        "", "us", "usa", "u s a", "united states", "national", "nationwide",
        "conus", "oconus", "statewide", "anywhere", "worldwide", "global",
        "various", "various locations", "multiple locations", "any location",
        "location flexible", "flexible", "hybrid", "optional", "eligible",
        "or hybrid", "work", "position", "based",
    }
)


def _is_remote_label(candidate: str) -> bool:
    """True only when the fragment *is* a remote label, not merely contains one.

    Substring matching here was a trap: "Coach - Virtual Reality Program"
    would be read as a location, which both loses the employer and mislabels
    the posting as remote. The hint has to open the fragment and whatever
    follows has to be a recognizable qualifier or a real state.
    """
    tokens = re.sub(r"[^a-z0-9]+", " ", (candidate or "").lower()).strip()
    if not tokens:
        return False
    for hint in _REMOTE_LOCATION_HINTS:
        if tokens == hint:
            return True
        if tokens.startswith(f"{hint} "):
            rest = tokens[len(hint) :].strip()
            if (
                rest in _REMOTE_QUALIFIERS
                or rest.upper() in _STATE_ABBREVIATIONS
                or rest in _STATE_NAMES
            ):
                return True
    return False

_SEPARATOR = re.compile(r"\s+[-–—|]\s+")
_PARENTHETICAL = re.compile(r"\(([^()]+)\)\s*$")
_AT_PATTERN = re.compile(r"^(?P<title>.+?)\s+(?:at|@)\s+(?P<employer>.+)$", re.IGNORECASE)
_COUNTRY_SUFFIX = re.compile(r",\s*(?:usa|u\.?s\.?a?\.?|united states)$", re.IGNORECASE)

_EMPLOYER_LABEL = re.compile(
    r"^[ \t>*-]*(?:employer|company|organization|organisation|institution|"
    r"hiring organization|posted by)\s*[:\-]\s*(?P<value>.+)$",
    re.IGNORECASE | re.MULTILINE,
)
_LOCATION_LABEL = re.compile(
    r"^[ \t>*-]*(?:location|job location|worksite|work location|city)\s*[:\-]\s*(?P<value>.+)$",
    re.IGNORECASE | re.MULTILINE,
)


def looks_like_location(text: str) -> bool:
    """True when a fragment reads as a US city/state pair or a remote label."""
    candidate = (text or "").strip().rstrip(".").strip()
    if not candidate or len(candidate) > 80:
        return False
    if _is_remote_label(candidate):
        return True
    candidate = _COUNTRY_SUFFIX.sub("", candidate).strip()
    if "," not in candidate:
        return False
    tail = candidate.rsplit(",", 1)[1].strip().rstrip(".")
    return tail.upper() in _STATE_ABBREVIATIONS or tail.lower() in _STATE_NAMES


def split_listing_title(text: str) -> tuple[str, str, str]:
    """Split an association feed title into ``(title, employer, location)``.

    Handles the two shapes these platforms actually emit::

        Tactical Strength and Conditioning Coach - Austin Fire - Austin, TX
        Athletic Trainer at Boston Police Department (Boston, MA)

    Everything is optional: a title with no recognizable employer or location
    comes back unchanged in the first slot and empty in the others, which is
    the correct answer for a plain title.
    """
    raw = re.sub(r"\s+", " ", text or "").strip()
    if not raw:
        return "", "", ""

    location = ""
    parenthetical = _PARENTHETICAL.search(raw)
    if parenthetical and looks_like_location(parenthetical.group(1)):
        location = parenthetical.group(1).strip()
        raw = raw[: parenthetical.start()].strip()

    parts = [part.strip() for part in _SEPARATOR.split(raw) if part.strip()]
    if not location and len(parts) >= 2 and looks_like_location(parts[-1]):
        location = parts[-1]
        parts = parts[:-1]

    title = parts[0] if parts else raw
    employer = " - ".join(parts[1:]) if len(parts) > 1 else ""

    if not employer:
        at_match = _AT_PATTERN.match(title)
        if at_match:
            title = at_match.group("title").strip()
            employer = at_match.group("employer").strip()

    return title, employer, location


def _labelled(text: str, pattern: re.Pattern[str]) -> str:
    """Pull a ``Label: value`` line out of a description body."""
    match = pattern.search(text or "")
    if not match:
        return ""
    return match.group("value").split("\n")[0].strip(" .;,\t")


def _element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _find_text(element: ET.Element, *paths: str) -> str:
    for path in paths:
        text = _element_text(element.find(path, _NAMESPACES))
        if text:
            return text
    return ""


def _entry_link(element: ET.Element, base: str = "") -> str:
    """The human-facing URL, across RSS ``<link>`` and Atom ``<link href>``.

    ``base`` is the feed's own URL. Several association platforms publish
    root-relative or protocol-relative item links; resolving them is the
    difference between importing those postings and dropping every one of
    them for having "no link".
    """
    for path in ("link", "atom:link"):
        for node in element.findall(path, _NAMESPACES):
            href = (node.get("href") or "").strip()
            rel = (node.get("rel") or "alternate").strip().lower()
            if href and rel == "alternate":
                return _resolve_link(href, base)
            text = "".join(node.itertext()).strip()
            if text:
                resolved = _resolve_link(text, base)
                if resolved:
                    return resolved
    for path in ("guid", "atom:id"):
        value = _find_text(element, path)
        if value.startswith(("http://", "https://")):
            return value
    return ""


def _resolve_link(value: str, base: str) -> str:
    """Absolutize a feed link, or return "" when it is not a link at all."""
    value = (value or "").strip()
    if value.startswith(("http://", "https://")):
        return value
    if not base or not value.startswith(("/", "./", "../")):
        # A bare ``guid`` such as "nsca-8891" is an identifier, not a URL.
        return ""
    return urljoin(base, value)


class JobsRSSSource(Source):
    """Association career-center RSS/Atom, with the title taken apart.

    The generic ``rss`` adapter is deliberately dumb: title, link, body. That
    is right for an employer's own feed, where the employer is a constant and
    the location is in the body. It is wrong for NSCA, NATA, ACSM, CSCCa and
    AASP job boards, which aggregate hundreds of employers into one feed and
    encode the employer and city in the title. Without this parsing every
    posting from those feeds lands with the wrong employer and no location,
    which breaks dedupe and the location filter at the same time.

    Options
    -------
    url
        Feed URL. Required.
    employer_from
        ``"title"`` (default), ``"description"``, or ``"fixed"``. Chooses
        where the employer comes from; it never affects location parsing.
    fixed_employer / employer
        Explicit employer, used by ``"fixed"`` mode and as the fallback for
        the other two when nothing could be parsed.
    location
        Fallback location for feeds that publish neither.
    """

    kind = "jobsrss"

    _MODES = ("title", "description", "fixed")

    def fetch(self) -> Iterable[JobPosting]:
        url = self.require("url")
        mode = str(self.options.get("employer_from") or "title").strip().lower()
        if mode not in self._MODES:
            log.warning(
                "%s: unknown employer_from %r, falling back to 'title'", self.name, mode
            )
            mode = "title"

        body = fetch(url)
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise RuntimeError(f"{url} is not valid XML: {exc}") from exc

        entries = root.findall(".//item")
        if not entries:
            entries = root.findall(".//atom:entry", _NAMESPACES) or root.findall(".//entry")

        for entry in entries:
            try:
                posting = self._to_posting(entry, mode, str(url))
            except Exception as exc:  # pragma: no cover - defensive
                log.warning("%s: skipping malformed feed item: %s", self.name, exc)
                continue
            if posting is not None:
                yield posting

    # -- mapping ----------------------------------------------------------

    def _to_posting(
        self, entry: ET.Element, mode: str, feed_url: str = ""
    ) -> JobPosting | None:
        raw_title = _find_text(entry, "title", "atom:title")
        link = _entry_link(entry, feed_url)
        if not (raw_title and link):
            log.debug("%s: feed item without a title or link", self.name)
            return None

        description = self._description(entry)
        title, parsed_employer, parsed_location = split_listing_title(raw_title)

        employer = self._employer(mode, parsed_employer, description)
        location = (
            parsed_location
            or _labelled(description, _LOCATION_LABEL)
            or str(self.options.get("location") or "")
        )

        # Nothing parsed off the title is thrown away: the original string
        # goes back into the text so a discarded qualifier ("Part Time",
        # "Sworn") still reaches the classifier.
        if title != raw_title.strip():
            description = f"{description}\n\nListed as: {raw_title.strip()}".strip()

        published = _find_text(
            entry, "pubDate", "dc:date", "atom:published", "atom:updated", "published", "updated"
        )
        identifier = _find_text(entry, "guid", "atom:id", "id") or link

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=identifier,
            url=link,
            title=title,
            employer=employer,
            location=location,
            description=description,
            posted_at=parse_timestamp(published),
            remote=looks_remote(location, title, raw_title),
            department=None,
            compensation=None,
            raw={"title": raw_title, "link": link, "employer_from": mode},
        )

    def _description(self, entry: ET.Element) -> str:
        """The fullest body the feed offers.

        ``content:encoded`` usually holds the whole posting while
        ``description`` holds a truncated teaser -- but not always, and some
        platforms populate only one. Taking whichever renders longer gets the
        complete text without assuming which field the platform chose.
        """
        candidates = [
            html_to_text(_element_text(node))
            for path in (
                "content:encoded",
                "description",
                "atom:content",
                "atom:summary",
                "summary",
            )
            for node in entry.findall(path, _NAMESPACES)
        ]
        return max(candidates, key=len, default="")

    def _employer(self, mode: str, parsed_employer: str, description: str) -> str:
        explicit = str(self.options.get("employer") or "")
        fixed = str(self.options.get("fixed_employer") or "")

        if mode == "fixed":
            return fixed or explicit or self.name
        if mode == "description":
            parsed = _labelled(description, _EMPLOYER_LABEL)
            if not parsed:
                first_line = next(
                    (line for line in description.splitlines() if line.strip()), ""
                )
                parsed = split_listing_title(first_line)[1]
            return parsed or explicit or fixed or self.name
        return parsed_employer or explicit or fixed or self.name


# ---------------------------------------------------------------------------
# arbitrary JSON
# ---------------------------------------------------------------------------

_GENERIC_FIELDS = (
    "title",
    "url",
    "source_id",
    "employer",
    "location",
    "description",
    "posted_at",
    "department",
    "compensation",
    "remote",
    "detail_url",
)

_TRUTHY = {"true", "yes", "y", "1", "remote", "virtual"}  # not "telework"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in _TRUTHY or looks_remote(value)
    return bool(value)


class GenericJSONSource(Source):
    """Read any JSON career endpoint via a configured field map.

    The long tail of custom career pages is not worth a module each, but it
    *is* worth a config block each. Point ``records_path`` at the array and
    ``field_map`` at the fields inside one record::

        records_path = "data.jobs"
        field_map = { title = "name", url = "links.self",
                      description = "content.html" }

    Options
    -------
    url
        Endpoint returning JSON. Required.
    records_path
        Dot path to the array of records. ``""`` (the default) means the
        root of the response is itself the array.
    field_map
        JobPosting field name -> dot path in one record. ``title`` and
        ``url`` are required; every other key is optional. A value may be a
        list of paths, in which case the first non-empty one wins -- except
        for ``description``, where every path is concatenated, because the
        point of this project is the complete text.
    detail_field_map / detail_records_path / detail_limit
        When ``field_map`` includes ``detail_url`` and a record has no
        description, that URL is fetched and read with ``detail_field_map``
        (defaulting to ``field_map``). Bounded by ``detail_limit``,
        default 25.
    employer
        Fallback employer when the map has no ``employer`` path.
    params / headers
        Passed through to the request.
    """

    kind = "genericjson"

    def fetch(self) -> Iterable[JobPosting]:
        url = str(self.require("url"))
        field_map = self._field_map()
        records_path = self.options.get("records_path", "")
        employer_default = self.options.get("employer") or self.name
        detail_budget = as_int(self.options.get("detail_limit"), 25)

        payload = fetch_json(
            url,
            params=self.options.get("params") or None,
            headers=self.options.get("headers") or None,
        )
        records = resolve_path(payload, records_path)
        if isinstance(records, dict):
            # A single-record response is a list of one, not an error.
            records = [records]
        if not isinstance(records, list):
            log.warning(
                "%s: records_path %r did not resolve to a list", self.name, records_path
            )
            return

        seen: set[str] = set()
        for record in records:
            try:
                posting, spent = self._to_posting(
                    record, url, field_map, employer_default, detail_budget > 0
                )
            except Exception as exc:  # pragma: no cover - defensive
                log.warning("%s: skipping malformed record: %s", self.name, exc)
                continue
            if spent:
                detail_budget -= 1
            if posting is None or posting.source_id in seen:
                continue
            seen.add(posting.source_id)
            yield posting

    # -- configuration ----------------------------------------------------

    def _field_map(self) -> dict[str, Any]:
        field_map = self.require("field_map")
        if not isinstance(field_map, dict):
            raise TypeError(
                f"source '{self.name}' ({self.kind}) needs field_map to be a table"
            )
        for key in ("title", "url"):
            if not field_map.get(key):
                raise KeyError(
                    f"source '{self.name}' ({self.kind}) requires field_map key '{key}'"
                )
        return field_map

    # -- resolution -------------------------------------------------------

    def _resolve(self, record: Any, field_map: dict[str, Any], field: str) -> Any:
        paths = field_map.get(field)
        if paths is None:
            return None
        if isinstance(paths, (list, tuple)):
            for path in paths:
                found = resolve_path(record, str(path))
                if found not in (None, "", [], {}):
                    return found
            return None
        return resolve_path(record, str(paths))

    def _describe(self, record: Any, field_map: dict[str, Any]) -> str:
        """Concatenate every configured description path.

        First-wins is right for a scalar such as ``location``; for the
        description it would silently drop the qualifications block, which is
        exactly where the certifications and clearances live.
        """
        paths = field_map.get("description")
        if paths is None:
            return ""
        if not isinstance(paths, (list, tuple)):
            paths = [paths]
        parts: list[str] = []
        for path in paths:
            text = html_to_text(_blob(resolve_path(record, str(path))))
            if text and text not in parts:
                parts.append(text)
        return "\n\n".join(parts)

    def _detail(self, url: str) -> Any:
        try:
            return fetch_json(url, headers=self.options.get("headers") or None)
        except Exception as exc:
            log.debug("%s: detail fetch failed for %s: %s", self.name, url, exc)
            return None

    # -- mapping ----------------------------------------------------------

    def _to_posting(
        self,
        record: Any,
        base_url: str,
        field_map: dict[str, Any],
        employer_default: str,
        may_fetch_detail: bool,
    ) -> tuple[JobPosting | None, bool]:
        if not isinstance(record, (dict, list)):
            log.debug("%s: skipping scalar record %r", self.name, record)
            return None, False

        values = {
            field: self._resolve(record, field_map, field) for field in _GENERIC_FIELDS
        }
        title = flatten(values["title"])
        url = _absolute(flatten(values["url"]), base_url)
        if not title or not url:
            log.debug("%s: record missing a title or url, skipping", self.name)
            return None, False

        description = self._describe(record, field_map)
        spent_detail = False
        detail_ref = flatten(values["detail_url"])
        if may_fetch_detail and detail_ref and not description:
            spent_detail = True
            detail_map = self.options.get("detail_field_map") or field_map
            payload = self._detail(_absolute(detail_ref, base_url))
            detail_record = resolve_path(
                payload, self.options.get("detail_records_path", "")
            )
            if detail_record is not None:
                description = self._describe(detail_record, detail_map)
                for field in ("employer", "location", "department", "compensation", "posted_at"):
                    if not values.get(field):
                        values[field] = self._resolve(detail_record, detail_map, field)

        location = flatten(values["location"])
        remote = (
            _truthy(values["remote"])
            if "remote" in field_map
            else looks_remote(location, title)
        )

        return (
            JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=flatten(values["source_id"]) or url,
                url=url,
                title=title,
                employer=flatten(values["employer"]) or employer_default,
                location=location,
                description=description,
                posted_at=parse_timestamp(values["posted_at"]),
                remote=remote,
                department=flatten(values["department"]) or None,
                compensation=flatten(values["compensation"]) or None,
                raw=record if isinstance(record, dict) else {"record": record},
            ),
            spent_detail,
        )


GOV_SOURCES: tuple[type[Source], ...] = (
    GovernmentJobsSource,
    JobsRSSSource,
    GenericJSONSource,
)
