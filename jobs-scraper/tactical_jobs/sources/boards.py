"""Professional association career centers.

WHY THIS SOURCE MATTERS MORE THAN ITS VOLUME SUGGESTS
A general job site is 99% noise for this project: one embedded strength coach
posting per ten thousand warehouse jobs. The NSCA, NATA, ACSM, CSCCa, AASP,
APTA and SCAN career centers invert that ratio. Practically every listing on
them is a strength coach, athletic trainer, physical therapist, performance
dietitian, or sport scientist -- the exact populations that get embedded with
Army H2F brigades, USASOC THOR3, SOCOM POTFF, Naval Special Warfare, and the
larger fire and police departments. Signal per fetched byte is the highest of
any source this project has.

THE PLATFORMS -- **UNVERIFIED**
Associations do not build job boards; they rent them. Three vendors cover
almost the whole field. Nothing in this section was confirmed against a live
server -- this module was written with no outbound network -- so read the
vendor names, the hostnames and especially the paths as the starting
hypothesis they are, not as observed fact:

* YourMembership / Community Brands (``careers.<association>.org``).
  Understood to serve RSS at ``/jobs/feed`` or
  ``/jobseeker/search/results/rss`` and JSON at
  ``/jobs/search/results?format=json``.
* Naylor CareerHub.
* Boxwood / CareerWebsite.

What is *not* a guess: none of these vendors requires a key, an account, an
OAuth grant, or a signup for the public listing feed, and this module sends no
credential of any kind. The adapter is also written not to care which vendor
answers -- it sniffs the payload and reads feeds by element local name -- so a
wrong guess above costs a corrected URL, not a rewrite.

WHY AUTO-DETECTION RATHER THAN A FORMAT OPTION
Those vendors serve *both* formats from confusingly similar paths, tenants
move between paths on redesigns, and a ``format=json`` query parameter that a
tenant does not implement quietly returns the XML feed instead. Hardcoding a
parser -- or making the operator declare one -- turns a vendor's routine
config change into a silently empty source. So the response body decides:

    The first non-whitespace character of the body selects the parser.
    ``{`` or ``[`` means JSON, ``<`` means RSS/Atom XML. If the selected
    parser then fails, the other one is tried before giving up, which covers
    the tenants that serve JSON under an XML content type. A body that is
    neither raises, because "neither JSON nor XML" is an HTML error page or a
    login wall, and reporting that as zero jobs would hide a dead board.

WHY THE DETAIL PAGE IS FETCHED
These feeds carry a one-paragraph teaser. Every certification requirement
(CSCS, TSAC-F, ATC, RD/RDN, CSCCa SCCC), every clearance line, and every
"must be able to deploy" clause lives in the body of the posting, not the
teaser. A title-only record from this source is close to worthless, so the
adapter follows the item link and mines the full page -- bounded, because a
board with 800 listings must not turn into 800 requests.

WHY THE TITLE IS TAKEN APART
These boards aggregate hundreds of employers into one feed and encode the
employer and the city in the item *title* rather than in structured fields.
Without parsing it, every posting lands with the feed's name as the employer
and no location at all, which breaks the location filter and the fuzzy
dedupe at the same time.
"""

from __future__ import annotations

import json
import logging
import re
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any, Iterable
from urllib.parse import urljoin

from ..http import fetch
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

log = logging.getLogger(__name__)

DEFAULT_MAX_ITEMS = 200
DEFAULT_DETAIL_LIMIT = 40
DEFAULT_DETAIL_MIN_CHARS = 600
"""A feed body already longer than this is treated as the full posting.

Some tenants publish the complete text in ``content:encoded``; spending a
detail request on those buys nothing and costs the budget a posting that
actually needs one.
"""

MIN_REGION_CHARS = 120
"""Below this a "description" region on a detail page is a label, not a body."""

DETAIL_RETRIES = 1
"""Detail pages get one attempt; the feed keeps the full retry budget.

The feed request is load-bearing -- lose it and the board contributes nothing,
so it is worth retrying. A detail page is enrichment on a record we already
have. At the default budget of 40 detail pages, letting each one exhaust the
three attempts and backoff that :func:`~tactical_jobs.http.fetch` defaults to
means a single unresponsive host can hold a nightly run for the better part of
an hour, and the reward for winning that wait is one description.
"""

# ---------------------------------------------------------------------------
# option coercion
#
# Options arrive from TOML and from operators editing by hand, so a blank or
# mistyped value is normal. Aborting a source over it is not.
# ---------------------------------------------------------------------------


def _as_int(value: Any, default: int) -> int:
    """A non-negative bound, or ``default``.

    A negative bound is always a typo, and it is the expensive kind: a
    ``max_items = -1`` makes the source yield nothing while reporting a clean
    run, which is indistinguishable from a quiet board. Falling back to the
    documented default and saying so in the log is the only safe reading.
    """
    if isinstance(value, bool) or value is None:
        return default
    try:
        number = int(value)
    except (TypeError, ValueError):
        log.warning("ignoring non-numeric option value %r, using %d", value, default)
        return default
    if number < 0:
        log.warning("ignoring negative option value %r, using %d", value, default)
        return default
    return number


_FALSEY = {"", "0", "false", "no", "n", "off", "none", "null"}


def _as_bool(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return str(value).strip().lower() not in _FALSEY


def _as_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        items: list[Any] = [value]
    elif isinstance(value, (list, tuple, set)):
        items = list(value)
    else:
        items = [value]
    return [str(item).strip() for item in items if str(item).strip()]


def _decode(body: Any) -> str:
    """Bytes from :func:`fetch`, or a str from a caching wrapper around it."""
    if isinstance(body, (bytes, bytearray)):
        return body.decode("utf-8", "replace")
    return str(body)


# ---------------------------------------------------------------------------
# payload sniffing
# ---------------------------------------------------------------------------

_LEADING = "﻿ \t\r\n"


def detect_payload_kind(body: Any) -> str:
    """``"json"``, ``"xml"``, or ``"unknown"`` for a response body.

    The rule is deliberately the cheapest one that works: the first
    non-whitespace character after any byte-order mark. ``{``/``[`` is JSON,
    ``<`` is XML (which covers both ``<?xml ...?>`` declarations and a bare
    ``<rss>``/``<feed>`` root). Anything else -- an HTML login wall that
    somehow lost its doctype, a plain-text error -- is unknown, and the caller
    decides what to do about it.
    """
    text = _decode(body).lstrip(_LEADING)
    if not text:
        return "unknown"
    if text[0] in "{[":
        return "json"
    if text[0] == "<":
        return "xml"
    return "unknown"


# ---------------------------------------------------------------------------
# tolerant JSON field access
#
# The same logical field is named differently by every tenant of every one of
# these platforms (``jobTitle`` / ``job_title`` / ``Title``). Comparing keys
# with case and punctuation normalized away is what lets one adapter cover
# them all instead of one adapter per association.
# ---------------------------------------------------------------------------


def _norm_key(key: Any) -> str:
    return re.sub(r"[^a-z0-9]", "", str(key).lower())


def _index(record: Any) -> dict[str, Any]:
    if not isinstance(record, dict):
        return {}
    index: dict[str, Any] = {}
    for key, value in record.items():
        index.setdefault(_norm_key(key), value)
    return index


_DISPLAY_KEYS = ("name", "value", "label", "text", "title", "display", "href", "url", "link")
_CITY_KEYS = ("city", "cityname", "locality", "town")
_REGION_KEYS = ("state", "stateprovince", "statecode", "region", "province")


def _flatten(value: Any) -> str:
    """Flatten a scalar, a ``{"name": ...}`` wrapper, an address, or a list."""
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        index = _index(value)
        for key in _DISPLAY_KEYS:
            inner = _flatten(index.get(key))
            if inner:
                return inner
        city = next((t for t in (_flatten(index.get(k)) for k in _CITY_KEYS) if t), "")
        region = next((t for t in (_flatten(index.get(k)) for k in _REGION_KEYS) if t), "")
        return ", ".join(part for part in (city, region) if part)
    if isinstance(value, (list, tuple)):
        parts = [_flatten(item) for item in value]
        return ", ".join(part for part in parts if part)
    return ""


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


def _pick(record: Any, *candidates: str, default: str = "") -> str:
    index = _index(record)
    for candidate in candidates:
        if _norm_key(candidate) in index:
            text = _flatten(index[_norm_key(candidate)])
            if text:
                return text
    return default


def _pick_raw(record: Any, *candidates: str) -> Any:
    index = _index(record)
    for candidate in candidates:
        if _norm_key(candidate) in index:
            value = index[_norm_key(candidate)]
            if value not in (None, "", [], {}):
                return value
    return None


_ENVELOPE_KEYS = (
    "results", "jobs", "items", "listings", "postings", "records", "rows",
    "joblist", "searchresults", "data", "d", "content",
)

_ID_KEYS = (
    "id", "jobId", "jobID", "listingId", "postingId", "jobPostingId",
    "recordId", "jobKey", "guid", "key",
)
_TITLE_KEYS = ("title", "jobTitle", "positionTitle", "position", "jobName", "name")
_EMPLOYER_KEYS = (
    "employer", "employerName", "company", "companyName", "organization",
    "organizationName", "orgName", "hiringOrganization", "institution",
    "accountName", "memberName", "recruiter",
)
_LOCATION_KEYS = (
    "location", "jobLocation", "locationName", "displayLocation",
    "locationDisplay", "locations", "geoLocation", "address",
)
_URL_KEYS = (
    "url", "jobUrl", "detailUrl", "jobDetailUrl", "permalink", "link",
    "href", "viewUrl", "jobLink", "applyUrl",
)
_DESCRIPTION_KEYS = (
    "description", "jobDescription", "fullDescription", "jobSummary",
    "summary", "body", "content", "details", "responsibilities",
    "requirements", "qualifications", "benefits", "text",
)
"""Every free-text field these platforms use.

Certifications and clearances are routinely split across ``requirements`` and
``qualifications`` rather than sitting in ``description``, so all of them are
captured and concatenated instead of first-one-wins.
"""

_DATE_KEYS = (
    "postedDate", "datePosted", "publishDate", "publishedDate", "postDate",
    "createdDate", "createdOn", "pubDate", "activeDate", "startDate",
)
_CATEGORY_KEYS = (
    "category", "jobCategory", "categoryName", "department", "jobFunction",
    "discipline", "industry", "specialty",
)
_SALARY_KEYS = (
    "salary", "salaryRange", "salaryDisplay", "compensation", "payRange", "wage",
)


def json_records(payload: Any, depth: int = 0) -> list[Any]:
    """Find the array of listings inside a tenant's JSON envelope.

    Handles the root-is-an-array case, the flat ``{"results": [...]}`` case,
    and the wrapped ``{"data": {"jobs": [...]}}`` case. Only arrays sitting
    under a known envelope key count, so a stray list of facet values is never
    mistaken for the listings.

    A *populated* envelope always beats an empty one. Several of these tenants
    answer with more than one known key -- ``{"results": [], "jobs": [...]}``
    from a saved-search wrapper, for instance -- and returning the first key
    that happens to be a list would report the board as empty while the
    listings sat in the next key along.
    """
    if isinstance(payload, list):
        return payload
    if not isinstance(payload, dict) or depth > 3:
        return []
    index = _index(payload)
    for key in _ENVELOPE_KEYS:
        value = index.get(key)
        if isinstance(value, list) and value:
            return value
    for value in payload.values():
        if isinstance(value, dict):
            nested = json_records(value, depth + 1)
            if nested:
                return nested
    return []


def _narrative(record: Any) -> str:
    index = _index(record)
    parts: list[str] = []
    for key in _DESCRIPTION_KEYS:
        text = html_to_text(_blob(index.get(_norm_key(key))))
        if text and text not in parts:
            parts.append(text)
    return "\n\n".join(parts)


# ---------------------------------------------------------------------------
# title parsing
# ---------------------------------------------------------------------------

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
"""A trailing fragment must resolve to a real state to count as a location.

Association titles are full of comma-separated qualifiers ("Coach, Football"),
and treating every one of them as a city/state pair would fill the location
column with nonsense and mislabel the employer at the same time.
"""

# "telework" belongs here and nowhere else. These lists answer "does this
# fragment read as a LOCATION?" for title parsing -- "Coach - Telework (CONUS)"
# has a location in the tail, not an employer. Whether the job is actually
# remote is a different question, answered by REMOTE_HINTS in base.py and
# _REMOTE_RE in facets.py, and telework is deliberately absent from both.
_REMOTE_LABELS = frozenset(
    {
        "remote", "fully remote", "remote us", "remote usa", "us remote",
        "remote united states", "remote nationwide", "virtual", "telework",
        "telecommute", "work from home", "work at home", "anywhere",
        "nationwide", "multiple locations", "various locations",
    }
)


def _is_remote_label(text: str) -> bool:
    """True only when the fragment *is* a remote label, not merely contains one.

    Substring matching here is a trap: "Coach - Virtual Reality Program" would
    be read as a location, losing the employer and mislabelling the posting as
    remote in one move.
    """
    tokens = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()
    return tokens in _REMOTE_LABELS


_COUNTRY_SUFFIX = re.compile(r",\s*(?:usa|u\.?s\.?a?\.?|united states)$", re.IGNORECASE)


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


_ROLE_WORDS = frozenset(
    """
    coach coaches trainer trainers therapist therapists dietitian dietician
    nutritionist physiologist psychologist specialist scientist analyst
    director manager coordinator supervisor instructor educator intern
    internship fellow fellowship assistant associate consultant practitioner
    technician technologist researcher clinician physician nurse chiropractor
    counselor counsellor lead officer aide apprentice resident preceptor
    """.split()
)
"""Vocabulary used only to disambiguate ``Employer: Title`` from a title that
happens to contain a colon. See :func:`parse_listing_title`."""


def _looks_like_role(text: str) -> bool:
    tokens = re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).split()
    return any(token in _ROLE_WORDS for token in tokens)


_SEPARATOR = re.compile(r"\s+[-–—|]\s+")
_PARENTHETICAL = re.compile(r"\(([^()]+)\)\s*$")
_AT_PATTERN = re.compile(r"^(?P<title>.+?)\s+(?:at|@)\s+(?P<employer>.+)$", re.IGNORECASE)


def parse_listing_title(text: str) -> tuple[str, str, str]:
    """Split a board listing title into ``(title, employer, location)``.

    Handles the three shapes these platforms emit::

        Tactical Strength and Conditioning Coach - Austin Fire - Austin, TX
        Athletic Trainer at Boston Police Department (Boston, MA)
        Fort Bragg Fire Department: Peer Fitness Trainer (Fayetteville, NC)

    Applied in that order, most-structured first, and every step is optional:
    a plain title comes back unchanged in the first slot with the other two
    empty, which is the correct answer and lets the caller fall back to the
    configured employer.

    The colon form is the ambiguous one -- "Athletic Trainer: Per Diem" is a
    title, not an employer -- so it is applied only when the tail reads as a
    job role and the head does not. That fails closed: an unsplit title costs
    a location, whereas a wrongly split one invents an employer and silently
    corrupts the fuzzy dedupe for every board carrying the same job.
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
        # The colon form is tried before the "at" form on purpose: an employer
        # name may itself contain "at" ("University of Texas at Austin: Sports
        # Performance Dietitian"), and letting the weaker marker win there
        # splits the string in the middle of the employer.
        head, separator, tail = title.partition(":")
        head, tail = head.strip(), tail.strip()
        if separator and head and tail and _looks_like_role(tail) and not _looks_like_role(head):
            title, employer = tail, head

    if not employer:
        at_match = _AT_PATTERN.match(title)
        if at_match:
            candidate = at_match.group("employer").strip()
            # A runaway match ("...experience at a minimum of three sites")
            # would swallow half the title; real employer names are short.
            if candidate and len(candidate.split()) <= 10:
                title = at_match.group("title").strip()
                employer = candidate

    return title, employer, location


# ---------------------------------------------------------------------------
# detail page text
# ---------------------------------------------------------------------------

_VOID_TAGS = frozenset(
    "br img input hr meta link source col area base embed param track wbr".split()
)
_SKIP_TAGS = frozenset(
    "script style nav header footer form select noscript template svg".split()
)
_BLOCK_TAGS = frozenset(
    """p div br li ul ol tr td th table h1 h2 h3 h4 h5 h6 section article
    blockquote pre dl dt dd""".split()
)

_DESCRIPTION_HINTS = (
    "jobdescription", "jobdetail", "jobbody", "jobcontent", "jobsummary",
    "jobad", "jobpost", "postingbody", "postingdetail", "vacancydetail",
    "description", "maincontent", "contentbody", "detailbody",
)
"""Class/id/itemprop fragments that mark the posting body on these platforms.

Compared with punctuation removed, so ``job-description``, ``job_description``
and ``jobDescription`` are one hint rather than three.
"""


def _clean_text(raw: str) -> str:
    text = re.sub(r"[ \t\r\f\v]+", " ", raw)
    text = re.sub(r"\n\s*\n\s*", "\n\n", text)
    return text.strip()


class _RegionExtractor(HTMLParser):
    """Pull the posting body out of a rendered detail page.

    Career pages are 90% chrome. Flattening the whole document would bury the
    posting in navigation, and the enrichment layer would happily mine the
    site footer for certifications. So elements whose id/class/itemprop names
    them as the description are captured separately, and script, style, nav,
    header, footer and form subtrees are dropped entirely.

    Tag nesting is tracked with an explicit stack rather than a depth counter
    because this markup is hand-written and routinely leaves ``<p>`` and
    ``<li>`` unclosed; an unmatched end tag is ignored instead of unwinding
    the wrong element.
    """

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._stack: list[str] = []
        self._skip_depth: int | None = None
        self._captures: list[tuple[int, list[str]]] = []
        self._page: list[str] = []
        self.regions: list[str] = []

    # -- capture bookkeeping ---------------------------------------------

    def _emit(self, text: str) -> None:
        self._page.append(text)
        for _, parts in self._captures:
            parts.append(text)

    @property
    def page_text(self) -> str:
        """The whole document minus script, style, nav, header, and footer."""
        return _clean_text("".join(self._page))

    def _settle(self) -> None:
        depth = len(self._stack)
        if self._skip_depth is not None and self._skip_depth > depth:
            self._skip_depth = None
        while self._captures and self._captures[-1][0] > depth:
            _, parts = self._captures.pop()
            text = _clean_text("".join(parts))
            if text:
                self.regions.append(text)

    @staticmethod
    def _is_hint(attrs: Any) -> bool:
        for key, value in attrs:
            if str(key).lower() not in ("class", "id", "itemprop"):
                continue
            folded = re.sub(r"[^a-z0-9]", "", str(value or "").lower())
            if any(hint in folded for hint in _DESCRIPTION_HINTS):
                return True
        return False

    # -- parser callbacks -------------------------------------------------

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in _VOID_TAGS:
            if tag == "br" and self._skip_depth is None:
                self._emit("\n")
            return
        self._stack.append(tag)
        if self._skip_depth is not None:
            return
        if tag in _SKIP_TAGS:
            self._skip_depth = len(self._stack)
            return
        if tag in _BLOCK_TAGS:
            self._emit("\n")
        if self._is_hint(attrs):
            self._captures.append((len(self._stack), []))

    def handle_endtag(self, tag: str) -> None:
        if tag in _VOID_TAGS:
            return
        if tag in self._stack:
            index = len(self._stack) - 1 - self._stack[::-1].index(tag)
            del self._stack[index:]
        self._settle()
        if self._skip_depth is None and tag in _BLOCK_TAGS:
            self._emit("\n")

    def handle_data(self, data: str) -> None:
        if self._skip_depth is None:
            self._emit(data)

    def close(self) -> None:
        super().close()
        # Flush regions left open by a truncated or unbalanced document.
        self._stack.clear()
        self._settle()


def extract_detail_text(markup: Any) -> str:
    """The fullest description a detail page offers.

    A marked-up description region wins when one exists and carries real
    prose; otherwise the page body (still minus nav, header, footer, script
    and style) is used, because a page with no recognizable container still
    beats shipping a title-only record.
    """
    text = _decode(markup)
    parser = _RegionExtractor()
    try:
        parser.feed(text)
        parser.close()
    except Exception as exc:  # pragma: no cover - defensive
        log.debug("detail page could not be parsed: %s", exc)
        return html_to_text(text)

    best = max(parser.regions, key=len, default="")
    if len(best) >= MIN_REGION_CHARS:
        return best
    return max((parser.page_text, best), key=len)


# ---------------------------------------------------------------------------
# feed helpers
# ---------------------------------------------------------------------------


def _element_text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def local_name(tag: Any) -> str:
    """The tag with any XML namespace stripped, lowercased.

    Feeds are read by local name rather than by namespace-qualified path
    because the namespace is the least stable thing about them. RSS 1.0 puts
    ``item`` in ``http://purl.org/rss/1.0/``, Atom 0.3 and Atom 1.0 use two
    different namespaces for ``entry``, and a tenant that wraps RSS 2.0 in a
    default namespace changes every path in the document without changing a
    single element name. Matching on the qualified path means those feeds find
    zero items and the board reports a clean run with no jobs -- forever, and
    with nothing in the log to notice.
    """
    if not isinstance(tag, str):  # comments and processing instructions
        return ""
    return tag.rsplit("}", 1)[-1].lower()


def _children(element: ET.Element) -> dict[str, list[ET.Element]]:
    grouped: dict[str, list[ET.Element]] = {}
    for node in element:
        grouped.setdefault(local_name(node.tag), []).append(node)
    return grouped


def _child_text(element: ET.Element, *names: str) -> str:
    """Text of the first direct child matching one of ``names`` by local name.

    ``names`` are local names, so ``"date"`` matches ``<dc:date>`` and
    ``"pubdate"`` matches ``<pubDate>``.
    """
    grouped = _children(element)
    for name in names:
        for node in grouped.get(name.lower(), ()):
            text = _element_text(node)
            if text:
                return text
    return ""


def _resolve(value: str, base: str) -> str:
    """Absolutize a feed/JSON link, or return "" when it is not a link at all."""
    value = (value or "").strip()
    if value.startswith(("http://", "https://")):
        return value
    if value.startswith("//"):
        return f"https:{value}"
    if not base or not value.startswith(("/", "./", "../")):
        # A bare guid such as "nsca-8891" is an identifier, not a URL.
        return ""
    return urljoin(base, value)


def _entry_link(element: ET.Element, base: str) -> str:
    grouped = _children(element)
    for node in grouped.get("link", ()):
        href = (node.get("href") or "").strip()
        rel = (node.get("rel") or "alternate").strip().lower()
        if href and rel == "alternate":
            resolved = _resolve(href, base)
            if resolved:
                return resolved
        text = "".join(node.itertext()).strip()
        if text:
            resolved = _resolve(text, base)
            if resolved:
                return resolved
    for name in ("guid", "id"):
        value = _child_text(element, name)
        if value.startswith(("http://", "https://")):
            return value
    return ""


def _entry_description(entry: ET.Element) -> str:
    """The fullest body the feed offers.

    ``content:encoded`` usually holds the whole posting while ``description``
    holds a teaser -- but not always, and some tenants populate only one.
    Taking whichever renders longer avoids guessing which the platform chose.
    """
    grouped = _children(entry)
    candidates = [
        html_to_text(_element_text(node))
        for name in ("encoded", "description", "content", "summary")
        for node in grouped.get(name, ())
    ]
    return max(candidates, key=len, default="")


# ---------------------------------------------------------------------------
# adapters
# ---------------------------------------------------------------------------


class AssociationBoardSource(Source):
    """One professional association career center, RSS or JSON.

    Options
    -------
    url
        Feed or JSON endpoint. Required. The format is detected from the
        response body, so the same option covers ``/jobs/feed`` and
        ``/jobs/search/results?format=json``.
    employer
        Fallback employer, used when the listing title carries no employer
        and the payload has no employer field. Defaults to the source name.
    association
        Human label for the board itself ("NSCA Career Center"). Recorded on
        every posting's ``department`` so the review queue can see which
        association surfaced a job.
    max_items
        Cap on postings yielded per run. Default 200.
    detail_limit
        Cap on detail-page requests per run. Default 40.
    fetch_details
        Follow the item link and mine the full posting. Default true; turning
        it off makes the source fast and nearly worthless, because the
        certifications live on the detail page.
    detail_min_chars
        A feed body at least this long is treated as the complete posting and
        skips its detail request. Default 600.
    location
        Fallback location for a listing whose title encodes none.
    """

    kind = "assocboard"

    def fetch(self) -> Iterable[JobPosting]:
        url = str(self.require("url"))
        employer_default = str(self.options.get("employer") or self.name)
        association = str(self.options.get("association") or "").strip()
        max_items = _as_int(self.options.get("max_items"), DEFAULT_MAX_ITEMS)
        detail_budget = (
            _as_int(self.options.get("detail_limit"), DEFAULT_DETAIL_LIMIT)
            if _as_bool(self.options.get("fetch_details"), True)
            else 0
        )
        min_chars = _as_int(self.options.get("detail_min_chars"), DEFAULT_DETAIL_MIN_CHARS)

        body = _decode(fetch(url))
        payload_kind, listings = self._parse(body, url)
        build = self._from_entry if payload_kind == "xml" else self._from_record

        seen: set[str] = set()
        emitted = 0
        for listing in listings:
            if emitted >= max_items:
                break
            try:
                posting, spent = build(
                    listing, url, employer_default, association, detail_budget, min_chars
                )
            except Exception as exc:  # pragma: no cover - defensive
                # One unusable listing must never cost us the rest of the board.
                log.warning("%s: skipping malformed listing: %s", self.name, exc)
                continue
            if spent:
                detail_budget -= 1
            if posting is None or posting.source_id in seen:
                continue
            seen.add(posting.source_id)
            emitted += 1
            yield posting

    # -- format detection -------------------------------------------------

    def _parse(self, body: str, url: str) -> tuple[str, list[Any]]:
        """Return ``(payload_kind, listings)`` for a response body.

        ``listings`` are XML elements or JSON records depending on the kind,
        and :meth:`fetch` picks the matching mapper, so the two payload shapes
        converge on one loop.
        """
        detected = detect_payload_kind(body)
        # Both parsers choke on a leading byte-order mark, and these tenants
        # emit one often enough that it has to be stripped rather than sniffed
        # past. Leading blank lines come from templated feed wrappers.
        text = body.lstrip(_LEADING)
        order = ("json", "xml") if detected == "json" else ("xml", "json")

        first_error: Exception | None = None
        for attempt in order:
            try:
                if attempt == "json":
                    return "json", self._json_listings(json.loads(text), url)
                return "xml", self._xml_listings(ET.fromstring(text))
            except (ValueError, TypeError, ET.ParseError) as exc:
                # A tenant that serves JSON under an XML content type (or the
                # reverse) is common enough that one failure is not an answer.
                if first_error is None:
                    first_error = exc
                log.debug("%s: %s parse of %s failed: %s", self.name, attempt, url, exc)

        raise RuntimeError(
            f"{url} returned neither JSON nor a readable RSS/Atom feed "
            f"(detected {detected!r}): {first_error}"
        )

    # -- RSS / Atom -------------------------------------------------------

    @staticmethod
    def _xml_listings(root: ET.Element) -> list[ET.Element]:
        # An HTML error page or login wall is frequently well-formed enough to
        # parse as XML, and it contains no <item> elements -- so without this
        # check a dead board reports a clean run with zero jobs, which is the
        # single most expensive failure mode this project has.
        if local_name(root.tag) == "html":
            raise ValueError("response is an HTML page, not an RSS/Atom feed")
        # Matched by local name, not by namespace-qualified path. RSS 1.0
        # (``<rdf:RDF>`` with items in the RSS 1.0 namespace), Atom 0.3, and
        # any RSS 2.0 served under a default namespace all carry ordinary
        # ``item``/``entry`` elements that a qualified ``.//item`` misses
        # completely -- and missing them looks exactly like an empty board.
        items: list[ET.Element] = []
        entries: list[ET.Element] = []
        for node in root.iter():
            if node is root:
                continue
            name = local_name(node.tag)
            if name == "item":
                items.append(node)
            elif name == "entry":
                entries.append(node)
        return items or entries

    def _from_entry(
        self,
        entry: ET.Element,
        feed_url: str,
        employer_default: str,
        association: str,
        detail_budget: int,
        min_chars: int,
    ) -> tuple[JobPosting | None, bool]:
        raw_title = _child_text(entry, "title")
        link = _entry_link(entry, feed_url)
        if not (raw_title and link):
            log.debug("%s: feed item without a title or link", self.name)
            return None, False

        title, employer, location = parse_listing_title(raw_title)
        description = _entry_description(entry)

        description, spent = self._with_detail(
            description, link, detail_budget, min_chars
        )
        # Nothing parsed off the title is thrown away: the original string goes
        # back into the text so a discarded qualifier ("Part Time", "Sworn")
        # still reaches the classifier.
        if title != raw_title.strip():
            description = f"{description}\n\nListed as: {raw_title.strip()}".strip()

        posted = _child_text(entry, "pubdate", "date", "published", "updated")
        identifier = _child_text(entry, "guid", "id") or link

        return (
            JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=identifier,
                url=link,
                title=title,
                employer=employer or employer_default,
                location=location or str(self.options.get("location") or ""),
                description=description,
                posted_at=parse_timestamp(posted),
                remote=looks_remote(location, title, raw_title),
                department=association or None,
                raw={"title": raw_title, "link": link, "association": association},
            ),
            spent,
        )

    # -- JSON -------------------------------------------------------------

    def _json_listings(self, payload: Any, url: str) -> list[Any]:
        records = json_records(payload)
        if not records:
            log.debug("%s: no listings found in the JSON payload from %s", self.name, url)
        return records

    def _from_record(
        self,
        record: Any,
        base_url: str,
        employer_default: str,
        association: str,
        detail_budget: int,
        min_chars: int,
    ) -> tuple[JobPosting | None, bool]:
        if not isinstance(record, dict):
            log.debug("%s: skipping non-object listing %r", self.name, record)
            return None, False

        title = _pick(record, *_TITLE_KEYS)
        link = _resolve(_pick(record, *_URL_KEYS), base_url)
        if not title:
            log.debug("%s: skipping listing without a title", self.name)
            return None, False

        employer = _pick(record, *_EMPLOYER_KEYS)
        location = _pick(record, *_LOCATION_KEYS)
        if not location:
            city = _pick(record, "city", "cityName")
            state = _pick(record, "state", "stateProvince", "region")
            location = ", ".join(part for part in (city, state) if part)

        # A JSON board still encodes the employer in the title often enough
        # that parsing it is worth doing -- but only where the structured
        # field is missing, since a real field always beats a heuristic.
        parsed_title, parsed_employer, parsed_location = parse_listing_title(title)
        if not employer and parsed_employer:
            title, employer = parsed_title, parsed_employer
        if not location and parsed_location:
            location = parsed_location

        description = _narrative(record)
        description, spent = self._with_detail(
            description, link, detail_budget, min_chars
        )

        # The last-resort identifier carries the employer and the location as
        # well as the title. :meth:`fetch` suppresses repeated ``source_id``
        # values, and a board that publishes no ids and no links would
        # otherwise collapse every "Athletic Trainer" on it into one posting --
        # dropping real jobs at different employers with no error anywhere.
        identifier = (
            _pick(record, *_ID_KEYS)
            or link
            or "|".join(part for part in (title, employer, location) if part)
        )
        category = _pick(record, *_CATEGORY_KEYS)
        compensation = _pick(record, *_SALARY_KEYS)

        return (
            JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=identifier,
                url=link,
                title=title,
                employer=employer or employer_default,
                location=location,
                description=description,
                posted_at=parse_timestamp(_pick_raw(record, *_DATE_KEYS)),
                remote=looks_remote(location, title),
                department=association or category or None,
                compensation=compensation or None,
                raw=record,
            ),
            spent,
        )

    # -- detail pages -----------------------------------------------------

    def _with_detail(
        self, description: str, link: str, detail_budget: int, min_chars: int
    ) -> tuple[str, bool]:
        """Enrich ``description`` from the detail page. Returns ``(text, spent)``.

        The *attempt* is what costs a request, so the attempt is what the
        budget counts -- otherwise a board whose detail pages all 404 would
        fan out without limit. A failed or thinner detail page leaves the feed
        text in place; losing a record because its detail page is down would
        be strictly worse than shipping the teaser.
        """
        if detail_budget <= 0 or not link or len(description) >= min_chars:
            return description, False
        try:
            body = fetch(link, retries=DETAIL_RETRIES)
        except Exception as exc:
            log.debug("%s: detail fetch failed for %s: %s", self.name, link, exc)
            return description, True
        try:
            detail = extract_detail_text(body)
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("%s: could not read detail page %s: %s", self.name, link, exc)
            return description, True
        return (detail if len(detail) > len(description) else description), True


# ---------------------------------------------------------------------------
# known boards
#
# EVERY URL IN ASSOCIATION_BOARDS IS **UNVERIFIED**.
#
# This module was written with no outbound network, so nothing below could be
# confirmed against a live server. Each entry is the documented path
# convention of the platform the association is understood to run
# (YourMembership/Community Brands serves RSS at ``/jobs/feed``) applied to
# that association's career-center hostname. Treat them as starting points:
# open each in a browser, confirm it returns a feed or JSON, and correct the
# table. A wrong URL is logged and skipped, which means it looks exactly like
# a quiet week on that board -- check the run summary, not the job count.
#
# All of them are keyless: no account, no OAuth, no API key.
# ---------------------------------------------------------------------------

ASSOCIATION_BOARDS: dict[str, dict[str, str]] = {
    "nsca": {
        "name": "NSCA Career Center",
        # UNVERIFIED
        "url": "https://careers.nsca.com/jobs/feed",
        "employer_hint": "NSCA Career Center",
    },
    "nsca-tsac": {
        "name": "NSCA TSAC (tactical) Career Center",
        # UNVERIFIED -- same board, filtered to the tactical program.
        "url": "https://careers.nsca.com/jobs/feed?keywords=tactical",
        "employer_hint": "NSCA TSAC Career Center",
    },
    "nata": {
        "name": "NATA Career Center",
        # UNVERIFIED
        "url": "https://careers.nata.org/jobs/feed",
        "employer_hint": "NATA Career Center",
    },
    "acsm": {
        "name": "ACSM Career Center",
        # UNVERIFIED
        "url": "https://careers.acsm.org/jobs/feed",
        "employer_hint": "ACSM Career Center",
    },
    "cscca": {
        "name": "CSCCa Job Board",
        # UNVERIFIED
        "url": "https://careers.cscca.org/jobs/feed",
        "employer_hint": "CSCCa Job Board",
    },
    "aasp": {
        "name": "AASP Career Center",
        # UNVERIFIED
        "url": "https://careers.appliedsportpsych.org/jobs/feed",
        "employer_hint": "AASP Career Center",
    },
    "apta": {
        "name": "APTA Career Center",
        # UNVERIFIED
        "url": "https://careers.apta.org/jobs/feed",
        "employer_hint": "APTA Career Center",
    },
    "scan": {
        "name": "SCAN (Sports and Human Performance Nutrition) Career Center",
        # UNVERIFIED
        "url": "https://careers.scandpg.org/jobs/feed",
        "employer_hint": "SCAN Career Center",
    },
}

_SHARED_OPTIONS = ("max_items", "detail_limit", "fetch_details", "detail_min_chars", "location")


class KnownBoardsSource(Source):
    """Convenience wrapper over :data:`ASSOCIATION_BOARDS`.

    Configuring eight association boards by hand means eight nearly identical
    config blocks, and the URLs are the part most likely to be typed wrong.
    This turns the whole set into one line::

        kind = "knownboards"
        boards = ["nsca", "nsca-tsac", "nata", "cscca"]

    Options
    -------
    boards
        Slugs from :data:`ASSOCIATION_BOARDS`. Omit the option entirely to run
        every board; setting it to an empty list runs none, since that is an
        operator naming no boards rather than asking for all of them. Repeated
        slugs are fetched once. Unknown slugs are logged and skipped rather
        than raising, because a typo in one slug must not cost the operator
        the other seven.
    employer / association
        Override the per-board defaults for every board in the set.
    max_items / detail_limit / fetch_details / detail_min_chars / location
        Passed straight through to each board.

    A board that fails -- dead host, moved path, HTML error page -- is logged
    and skipped. These URLs are unverified, so some of them *will* fail, and
    the whole point of the wrapper is that the surviving boards still run.
    """

    kind = "knownboards"

    def fetch(self) -> Iterable[JobPosting]:
        # Only an *absent* ``boards`` key means "every board". A key that is
        # present but empty is an operator naming no boards, and quietly
        # fanning out to all eight hosts instead would be the opposite of what
        # was asked for.
        if "boards" in self.options:
            requested = _as_list(self.options["boards"])
            if not requested:
                log.warning("%s: 'boards' is set but names no board; nothing to do", self.name)
                return
        else:
            requested = list(ASSOCIATION_BOARDS)

        shared = {
            key: self.options[key] for key in _SHARED_OPTIONS if key in self.options
        }

        # Listing a board twice must not fetch it twice; order is preserved so
        # the run reads the way the operator wrote it.
        slugs: list[str] = []
        for slug in requested:
            if slug.strip().lower() not in {s.strip().lower() for s in slugs}:
                slugs.append(slug)

        for slug in slugs:
            key = slug.strip().lower()
            board = ASSOCIATION_BOARDS.get(key)
            if board is None:
                log.warning(
                    "%s: unknown board slug %r (known: %s)",
                    self.name,
                    slug,
                    ", ".join(sorted(ASSOCIATION_BOARDS)),
                )
                continue

            child = AssociationBoardSource(
                f"{self.name}.{key}",
                {
                    **shared,
                    "url": board["url"],
                    "employer": self.options.get("employer") or board["employer_hint"],
                    "association": self.options.get("association") or board["name"],
                },
            )
            # Re-stamped so the archive records which board a posting came
            # from; the child would otherwise label all eight identically.
            label = f"{self.kind}:{self.name}:{key}"
            try:
                for posting in child.fetch():
                    posting.source = label
                    yield posting
            except Exception as exc:
                log.warning("%s: board %r unavailable: %s", self.name, key, exc)
                continue


BOARD_SOURCES: tuple[type[Source], ...] = (
    AssociationBoardSource,
    KnownBoardsSource,
)
