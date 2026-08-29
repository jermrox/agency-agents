"""Generic schema.org ``JobPosting`` (JSON-LD) extractor.

Google will not show a job in Google Jobs unless the career page embeds
schema.org ``JobPosting`` markup as JSON-LD, so effectively every employer
that wants to be found publishes it -- iCIMS, Taleo, SuccessFactors,
Workday-fronted marketing sites, and the long tail of custom career pages
this project will never justify a bespoke adapter for. One generic reader
therefore unlocks far more inventory than any single vendor adapter.

Two ways to point it at pages:

* ``urls``    -- an explicit list of job (or listing) pages.
* ``sitemap`` -- a sitemap URL. ``<loc>`` entries are collected, filtered by
  ``url_include``, capped at ``max_urls``, then read the same way. Sitemap
  *index* files are followed one level down, which is the shape most large
  career sites publish.

Everything here degrades quietly: a page that will not fetch, a script block
that is not valid JSON, or a node that is not a ``JobPosting`` is skipped with
a log line rather than taking down the run.

Script blocks are located with :mod:`html.parser` rather than a regex. Regex
over HTML looks fine until the first page with a ``<script>`` string inside an
attribute, and these pages are written by hundreds of different vendors.
"""

from __future__ import annotations

import html
import json
import logging
import re
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import Any, Iterable
from urllib.parse import urljoin, urlparse

from ..http import fetch
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

log = logging.getLogger(__name__)

DEFAULT_MAX_URLS = 200
DEFAULT_MAX_SITEMAPS = 10
"""How many child sitemaps an index file may fan out to.

Large employers publish dozens of shards; without a bound one config line
could turn into thousands of requests.
"""

_NARRATIVE_KEYS = (
    "description",
    "responsibilities",
    "qualifications",
    "skills",
    "experienceRequirements",
    "educationRequirements",
    "jobBenefits",
    "incentiveCompensation",
    "workHours",
    "specialCommitments",
)
"""Every free-text field schema.org defines on ``JobPosting``.

The certification, clearance, and degree language this project mines is
routinely split across ``qualifications`` and ``educationRequirements``
rather than sitting in ``description``, so all of them are captured.
"""

_LABELLED_KEYS = (
    ("Employment type:", "employmentType"),
    ("Security clearance:", "securityClearanceRequirement"),
    ("Job category:", "occupationalCategory"),
    ("Industry:", "industry"),
)


class _LDScriptCollector(HTMLParser):
    """Collect the body of every ``<script type="application/ld+json">``."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[str] = []
        self._capturing = False
        self._buffer: list[str] = []

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag != "script":
            return
        attributes = {key.lower(): (value or "") for key, value in attrs}
        script_type = attributes.get("type", "").strip().lower()
        # Vendors write "application/ld+json" and, occasionally,
        # "application/ld+json; charset=utf-8".
        self._capturing = script_type.startswith("application/ld+json")
        self._buffer = []

    def handle_endtag(self, tag: str) -> None:
        if tag != "script" or not self._capturing:
            return
        self._capturing = False
        text = "".join(self._buffer).strip()
        self._buffer = []
        if text:
            self.blocks.append(text)

    def handle_data(self, data: str) -> None:
        if self._capturing:
            self._buffer.append(data)


def _clean_block(text: str) -> str:
    """Strip the CDATA/comment wrappers some CMS templates emit."""
    cleaned = text.strip()
    for opener in ("//<![CDATA[", "<![CDATA[", "/*<![CDATA[*/", "<!--"):
        if cleaned.startswith(opener):
            cleaned = cleaned[len(opener):].strip()
    for closer in ("//]]>", "]]>", "/*]]>*/", "-->"):
        if cleaned.endswith(closer):
            cleaned = cleaned[: -len(closer)].strip()
    return cleaned


def _decode_block(text: str) -> Any:
    """Decode one script block, tolerating the two common breakages.

    ``strict=False`` lets raw newlines inside hand-templated strings through,
    and a second pass through :func:`html.unescape` recovers the blocks that
    template engines HTML-escape wholesale (``&quot;@type&quot;: ...``), which
    is a surprisingly common CMS bug.
    """
    cleaned = _clean_block(text)
    try:
        return json.loads(cleaned, strict=False)
    except (ValueError, TypeError):
        unescaped = html.unescape(cleaned)
        if unescaped == cleaned:
            raise
        return json.loads(unescaped, strict=False)


def _iter_ld_nodes(payload: Any, depth: int = 0) -> Iterable[dict[str, Any]]:
    """Walk a decoded JSON-LD document and yield every object node.

    Covers the four shapes seen in the wild: a bare object, a top-level list,
    an ``@graph`` container, and list containers such as ``itemListElement``.
    """
    if depth > 6:
        return
    if isinstance(payload, list):
        for item in payload:
            yield from _iter_ld_nodes(item, depth + 1)
        return
    if not isinstance(payload, dict):
        return
    yield payload
    for container in ("@graph", "itemListElement", "mainEntity", "item"):
        nested = payload.get(container)
        if isinstance(nested, (list, dict)):
            yield from _iter_ld_nodes(nested, depth + 1)


def _type_names(node: dict[str, Any]) -> list[str]:
    raw = node.get("@type", node.get("type"))
    values = raw if isinstance(raw, list) else [raw]
    names = []
    for value in values:
        if isinstance(value, str):
            # Accept "JobPosting", "schema:JobPosting", "https://schema.org/JobPosting".
            names.append(value.strip().rstrip("/").split("/")[-1].split(":")[-1].lower())
    return names


def is_job_posting(node: Any) -> bool:
    """True when a JSON-LD node declares itself a schema.org JobPosting."""
    return isinstance(node, dict) and "jobposting" in _type_names(node)


# -- option coercion ------------------------------------------------------
#
# Config arrives from YAML/JSON written by hand, so an option can plausibly be
# a bare string, a null, or a number. None of those should be a traceback.


def _as_list(value: Any) -> list[str]:
    """Coerce a list-ish option into a clean list of non-empty strings."""
    if value is None:
        return []
    if isinstance(value, str):
        items: list[Any] = [value]
    elif isinstance(value, (list, tuple)):
        items = list(value)
    else:
        items = [value]
    return [str(item).strip() for item in items if str(item).strip()]


def _as_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _as_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


# -- URL handling ---------------------------------------------------------

_SCHEME = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def _slug(text: str, limit: int = 80) -> str:
    return _SLUG_STRIP.sub("-", text.lower()).strip("-")[:limit]


def _absolute_url(candidate: str, base: str, fallback: str | None = None) -> str:
    """Resolve a JSON-LD/sitemap URL against the document it came from.

    Career pages routinely emit ``/careers/job/123`` or ``//host/job/123``,
    and ``@id`` is just as often an opaque URN or a blank node rather than a
    link. A posting whose ``url`` cannot be clicked is worse than useless
    downstream, so anything that does not resolve to http(s) falls back.
    """
    if fallback is None:
        fallback = base
    text = (candidate or "").strip()
    if not text or text.startswith(("#", "_:")):
        return fallback
    if text.startswith("//"):
        text = f"{urlparse(base).scheme or 'https'}:{text}"
    if _SCHEME.match(text) and not text.lower().startswith(("http://", "https://")):
        # urn:, mailto:, javascript:, tag: ... not a job page.
        return fallback
    try:
        resolved = urljoin(base, text)
    except ValueError:
        return fallback
    return resolved if urlparse(resolved).scheme in ("http", "https") else fallback


def _plain(value: Any) -> str:
    """Flatten the str / {"name": ...} / list forms schema.org allows."""
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in ("name", "value", "@value", "alternateName", "identifier"):
            text = _plain(value.get(key))
            if text:
                return text
        return ""
    if isinstance(value, list):
        parts = [_plain(item) for item in value]
        return ", ".join(part for part in parts if part)
    return ""


def _blob(value: Any, depth: int = 0) -> str:
    """Flatten an arbitrary schema.org value into text for the description."""
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, list):
        return " ".join(part for part in (_blob(v, depth + 1) for v in value) if part)
    if isinstance(value, dict):
        if depth > 3:
            return ""
        parts = (
            _blob(v, depth + 1) for k, v in value.items() if not str(k).startswith("@")
        )
        return " ".join(part for part in parts if part)
    return ""


def _number(value: Any) -> str:
    """Render a salary figure without the ``.0`` JSON floats pick up."""
    if isinstance(value, bool) or value is None:
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    if isinstance(value, (int, float)):
        return str(value)
    return str(value).strip()


def _place_text(node: Any) -> str:
    """Turn one ``jobLocation`` entry into a display string."""
    if isinstance(node, str):
        return node.strip()
    if not isinstance(node, dict):
        return ""
    address = node.get("address")
    if isinstance(address, list):
        address = next((item for item in address if item), None)
    if isinstance(address, str):
        return address.strip()
    if isinstance(address, dict):
        parts = [
            _plain(address.get("addressLocality")),
            _plain(address.get("addressRegion")),
            _plain(address.get("addressCountry")),
        ]
        text = ", ".join(part for part in parts if part)
        if text:
            return text
        return _plain(address.get("name")) or _plain(node.get("name"))
    return _plain(node.get("name"))


DEFAULT_MAX_LOCATIONS = 8
"""Above this many ``jobLocation`` entries, the list is SEO padding, not truth.

Some career platforms pad ``jobLocation`` with every city in a recruiting
radius so the posting ranks for all of them. Serco's H2F postings are the case
this was written against: "H2Fit: Strength & Conditioning Coach - Fort Bragg,
NC" carries **120** entries, running from Alexandria VA to Buffalo NY, and the
very first one is an empty locality with a Washington DC postal code. There is
no in-band marker for which entry is real, so no amount of picking-the-first
recovers it -- and publishing all 120 would put a screenful of wrong cities on
a board whose whole value is telling a candidate where the job is.

So past the cap the enumeration is discarded rather than trusted or sampled.
The title is then the honest remaining source, and for this shape of posting it
is the reliable one: the place is right there in the title text.
"""

_TITLE_PLACE_RE = re.compile(
    # A trailing " - Fort Bragg, NC" / " - Camp Casey, Korea" / " (Ft. Drum, NY)".
    #
    # The comma is required: it is what separates a real place from a trailing
    # qualifier like "- Level II" or "- Full Time", which have no comma.
    #
    # The dash must be surrounded by space. Without that guard the hyphen
    # inside a hyphenated place name splits it, and "Joint Base
    # Langley-Eustis, VA" is published as "Eustis, VA".
    r"(?:\s[-–—]\s*|\(\s*)([A-Z][A-Za-z.'\s-]{2,40},\s*[A-Z][A-Za-z.\s]{1,20})\s*\)?\s*$"
)


def _location_from_title(title: str) -> str:
    """Recover a place from a title that ends with one. '' when it does not."""
    match = _TITLE_PLACE_RE.search((title or "").strip())
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


_REGION_ONLY_RE = re.compile(r"^([A-Z]{2,3})(?:,\s*(?:US|USA))?$")


def _regions(places: list[str]) -> list[str]:
    """The distinct state/country tokens behind a list of place strings.

    A long enumeration is not automatically noise. Serco publishes one Army
    H2F requisition across sixteen installations as bare region codes with no
    locality at all -- KS, HI, MO, JP, IT, DE and more -- which is a true
    statement about a genuinely multi-site job, not padding.
    """
    out: list[str] = []
    for place in places:
        # Drop a trailing country before taking the last segment, or every US
        # entry collapses to the useless token "US" instead of its state.
        text = re.sub(r",\s*(?:US|USA|United\s+States)\s*$", "", place.strip(), flags=re.I)
        match = _REGION_ONLY_RE.match(text)
        token = match.group(1) if match else text.rsplit(",", 1)[-1].strip()
        if token and token.upper() not in {"US", "USA", "UNITED STATES"} and token not in out:
            out.append(token)
    return out


def _locations(
    node: dict[str, Any],
    max_locations: int = DEFAULT_MAX_LOCATIONS,
    title: str = "",
) -> str:
    raw = node.get("jobLocation")
    entries = raw if isinstance(raw, list) else [raw]
    seen: list[str] = []
    for entry in entries:
        text = _place_text(entry)
        if text and text not in seen:
            seen.append(text)
    if max_locations < 0 or len(seen) <= max_locations:
        return "; ".join(seen)

    # Over the cap. The title is the better source when it names a place --
    # that is the 120-city Fort Bragg posting, where one real site is padded
    # out with a whole recruiting radius.
    from_title = _location_from_title(title)
    if from_title:
        return from_title

    # No place in the title either. Falling through to "" used to be the
    # answer, and it was the wrong one: it threw away sixteen real locations
    # on the Serco H2FIT req and left the posting unplaceable, which put it
    # in front of candidates filtering for remote work. Collapsing to the
    # distinct regions keeps what is certainly true, stays short enough to
    # read, and degrades a genuine radius-pad to its handful of states rather
    # than to nothing.
    regions = _regions(seen)
    return "; ".join(regions[:max_locations]) if regions else ""


def _is_telecommute(node: dict[str, Any]) -> bool:
    raw = node.get("jobLocationType")
    values = raw if isinstance(raw, list) else [raw]
    return any(
        isinstance(value, str) and value.strip().upper() == "TELECOMMUTE"
        for value in values
    )


def _one_salary(base: Any) -> str | None:
    """Render a single ``MonetaryAmount`` (or bare number) as text."""
    if isinstance(base, (int, float)) and not isinstance(base, bool):
        return f"${_number(base)}"
    if isinstance(base, str) and base.strip():
        return base.strip()
    if not isinstance(base, dict):
        return None

    value = base.get("value")
    if isinstance(value, list):
        # Some feeds publish one QuantitativeValue per pay period.
        value = next((item for item in value if item not in (None, "", {}, [])), None)
    currency = _plain(base.get("currency")) or _plain(base.get("currencyCode"))

    if isinstance(value, (int, float, str)) and not isinstance(value, bool):
        amount = _number(value)
        amounts = [amount] if amount else []
        unit = _plain(base.get("unitText"))
    elif isinstance(value, dict):
        currency = currency or _plain(value.get("currency"))
        minimum = _number(value.get("minValue"))
        maximum = _number(value.get("maxValue"))
        single = _number(value.get("value"))
        amounts = [part for part in (minimum, maximum) if part] or (
            [single] if single else []
        )
        unit = _plain(value.get("unitText")) or _plain(base.get("unitText"))
    else:
        return None

    if not amounts:
        return None

    currency = currency.upper()
    if currency and currency != "USD":
        rendered = f"{' - '.join(amounts)} {currency}"
    else:
        rendered = " - ".join(f"${amount}" for amount in amounts)
    return f"{rendered} per {unit}".strip() if unit else rendered


def _salary(node: dict[str, Any]) -> str | None:
    """Render ``baseSalary`` as a human-readable compensation string.

    ``baseSalary`` is occasionally a list (one entry per pay period), so the
    first entry that renders wins rather than the whole field being dropped.
    """
    base = node.get("baseSalary")
    candidates = base if isinstance(base, list) else [base]
    for candidate in candidates:
        rendered = _one_salary(candidate)
        if rendered:
            return rendered
    return None


class JSONLDSource(Source):
    """Read schema.org ``JobPosting`` JSON-LD off arbitrary career pages.

    Options
    -------
    urls
        List of page URLs to read (a single string is accepted too).
    sitemap
        Sitemap (or sitemap index) URL whose ``<loc>`` entries are read.
        At least one of ``urls`` / ``sitemap`` is required.
    employer
        Fallback employer label when the markup omits ``hiringOrganization``.
    url_include
        Substrings a URL must contain to be fetched, e.g. ``["/job/"]``.
    max_urls
        Cap on pages fetched per run. Default 200.
    delay_seconds
        Pause between page fetches. Default 0.0.
    """

    kind = "jsonld"

    def fetch(self) -> Iterable[JobPosting]:
        employer_default = self.options.get("employer") or self.name
        delay = _as_float(self.options.get("delay_seconds"), 0.0)

        seen_ids: set[str] = set()
        for index, page_url in enumerate(self._target_urls()):
            if delay > 0 and index:
                time.sleep(delay)
            markup = self._read_page(page_url)
            if markup is None:
                continue
            for posting in self._postings_from_markup(markup, page_url, employer_default):
                if posting.source_id in seen_ids:
                    continue
                seen_ids.add(posting.source_id)
                yield posting

    # -- URL selection ----------------------------------------------------

    def _target_urls(self) -> list[str]:
        configured = _as_list(self.options.get("urls"))
        sitemap = str(self.options.get("sitemap") or "").strip()

        if not configured and not sitemap:
            if "urls" not in self.options:
                # Produces the standard "requires option" message.
                self.require("urls")
            raise KeyError(
                f"source '{self.name}' ({self.kind}) requires a non-empty "
                "'urls' or 'sitemap' option"
            )

        candidates = list(configured)
        if sitemap:
            candidates.extend(self._sitemap_urls(sitemap))

        includes = _as_list(self.options.get("url_include"))
        if includes:
            candidates = [
                url for url in candidates if any(fragment in url for fragment in includes)
            ]

        ordered: list[str] = []
        for url in candidates:
            if url not in ordered:
                ordered.append(url)

        max_urls = _as_int(self.options.get("max_urls"), DEFAULT_MAX_URLS)
        return ordered[:max_urls] if max_urls >= 0 else ordered

    def _sitemap_urls(self, sitemap_url: str) -> list[str]:
        """Collect page URLs from a sitemap, following an index one level."""
        pages, children = self._read_sitemap(sitemap_url)
        if children:
            limit = _as_int(self.options.get("max_sitemaps"), DEFAULT_MAX_SITEMAPS)
            visited = {sitemap_url}
            fetched = 0
            for child in children:
                if fetched >= limit:
                    break
                if child in visited:
                    # An index that repeats (or self-references) a shard must
                    # not cost a second request.
                    continue
                visited.add(child)
                fetched += 1
                child_pages, _ = self._read_sitemap(child)
                pages.extend(child_pages)
        return pages

    def _read_sitemap(self, sitemap_url: str) -> tuple[list[str], list[str]]:
        """Return ``(page_urls, child_sitemap_urls)`` for one sitemap file."""
        try:
            body = fetch(sitemap_url)
        except Exception as exc:
            log.warning("%s: sitemap %s unavailable: %s", self.name, sitemap_url, exc)
            return [], []
        try:
            root = ET.fromstring(body)
        except (ET.ParseError, ValueError, TypeError) as exc:
            log.warning("%s: sitemap %s is not valid XML: %s", self.name, sitemap_url, exc)
            return [], []

        # ElementTree has no parent pointers, so the root tag decides how the
        # <loc> entries are read: a <sitemapindex> lists other sitemaps, a
        # <urlset> lists pages.
        is_index = root.tag.rsplit("}", 1)[-1].lower() == "sitemapindex"

        pages: list[str] = []
        children: list[str] = []
        for element in root.iter():
            if element.tag.rsplit("}", 1)[-1] != "loc":
                continue
            # <loc> is required to be absolute, but plenty of generators emit
            # a site-root path anyway.
            location = _absolute_url((element.text or "").strip(), sitemap_url, "")
            if not location:
                continue
            (children if is_index else pages).append(location)
        return pages, children

    # -- page reading -----------------------------------------------------

    def _read_page(self, page_url: str) -> str | None:
        try:
            body = fetch(page_url)
        except Exception as exc:
            log.warning("%s: skipping %s: %s", self.name, page_url, exc)
            return None
        if isinstance(body, (bytes, bytearray)):
            return body.decode("utf-8", "replace")
        return str(body)

    def _postings_from_markup(
        self, markup: str, page_url: str, employer_default: str
    ) -> Iterable[JobPosting]:
        collector = _LDScriptCollector()
        try:
            collector.feed(markup)
            collector.close()
        except Exception as exc:  # pragma: no cover - defensive
            log.warning("%s: could not parse %s: %s", self.name, page_url, exc)
            return

        for block in collector.blocks:
            try:
                payload = _decode_block(block)
            except (ValueError, TypeError) as exc:
                # Hand-templated JSON-LD is frequently invalid. One bad block
                # must not cost us the valid blocks on the same page.
                log.warning("%s: bad ld+json block on %s: %s", self.name, page_url, exc)
                continue
            for node in _iter_ld_nodes(payload):
                if not is_job_posting(node):
                    continue
                try:
                    posting = self._to_posting(node, page_url, employer_default)
                except Exception as exc:  # pragma: no cover - defensive
                    log.warning("%s: bad JobPosting on %s: %s", self.name, page_url, exc)
                    continue
                if posting is not None:
                    yield posting

    # -- mapping ----------------------------------------------------------

    def _to_posting(
        self, node: dict[str, Any], page_url: str, employer_default: str
    ) -> JobPosting | None:
        title = _plain(node.get("title")) or _plain(node.get("name"))
        if not title:
            # Without a title there is nothing to classify or publish.
            log.debug("%s: JobPosting without a title on %s", self.name, page_url)
            return None

        # The human-facing link, never a relative path or a bare URN.
        declared_url = _plain(node.get("url")) or _plain(node.get("@id"))
        url = _absolute_url(declared_url, page_url)

        location = _locations(
            node,
            _as_int(self.options.get("max_locations"), DEFAULT_MAX_LOCATIONS),
            title,
        )
        if not location:
            location = _location_from_title(title)
        telecommute = _is_telecommute(node)
        applicant_requirements = node.get("applicantLocationRequirements")
        if applicant_requirements is not None:
            telecommute = True
        if telecommute and not location:
            scope = _plain(applicant_requirements)
            location = f"Remote - {scope}" if scope else "Remote"

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=self._source_id(node, title, location, url, page_url),
            url=url,
            title=title,
            employer=_plain(node.get("hiringOrganization")) or employer_default,
            location=location,
            description=self._description(node),
            posted_at=parse_timestamp(
                node.get("datePosted") or node.get("dateCreated") or node.get("dateModified")
            ),
            remote=telecommute or looks_remote(location, title),
            department=(
                _plain(node.get("occupationalCategory"))
                or _plain(node.get("department"))
                or _plain(node.get("industry"))
                or None
            ),
            compensation=_salary(node),
            # The whole node is kept, so validThrough, directApply, and the
            # vendor's own extensions stay available for debugging.
            raw={**node, "sourcePageUrl": page_url},
        )

    def _source_id(
        self,
        node: dict[str, Any],
        title: str,
        location: str,
        url: str,
        page_url: str,
    ) -> str:
        """Stable per-job id.

        The last fallback deliberately mixes in the title and location: a
        listing page routinely embeds several JobPosting nodes that carry
        neither ``identifier`` nor a per-job ``url``, and keying those on the
        page URL alone would collapse every one of them into a single record.
        """
        identifier = node.get("identifier")
        if isinstance(identifier, list):
            identifier = next((item for item in identifier if _plain(item)), None)
        if isinstance(identifier, dict):
            found = _plain(identifier.get("value")) or _plain(identifier.get("name"))
        else:
            found = _plain(identifier)
        if found:
            return found

        if url and url != page_url:
            return url

        suffix = _slug(f"{title} {location}".strip())
        return f"{page_url}#{suffix}" if suffix else page_url

    def _description(self, node: dict[str, Any]) -> str:
        parts = [_blob(node.get(key)) for key in _NARRATIVE_KEYS]
        for label, key in _LABELLED_KEYS:
            value = _plain(node.get(key)) or _blob(node.get(key))
            if value:
                parts.append(f"{label} {value}.")
        return html_to_text("\n\n".join(part for part in parts if part.strip()))


JSONLD_SOURCES: tuple[type[Source], ...] = (JSONLDSource,)
