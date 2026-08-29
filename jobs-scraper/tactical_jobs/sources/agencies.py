"""Federal, service-specific, and NAF agency job boards.

WHY THIS EXISTS
USAJOBS is not the whole federal picture, and a project that stops there
misses a large share of the tactical human performance market:

UNVERIFIED, ON PURPOSE: everything in the list below is the *reason* this
adapter exists, not a checked claim. This module was written with no outbound
network, so no board named here was opened, no coverage overlap with USAJOBS
was measured, and no endpoint was confirmed to exist. Treat each line as a
lead to check, not as fact.

``Non-appropriated fund (NAF) hiring``
    Installation MWR / Fitness, Sports and Aquatics programs staff fitness
    specialists, sports directors, aquatics coordinators, and personal
    trainers through NAF. Some NAF vacancies are also cross-posted to
    USAJOBS and some appear only on service-run boards (Army NAF, Navy MWR,
    Air Force NAF, MCCS); which way any given installation goes was not
    verified here. The overlap is the thing worth measuring first.
``Service civilian career sites``
    Army, Navy, Air Force and DoD components each front their own civilian
    careers site. Whether any given one exposes a JSON endpoint its own
    front end calls is exactly what the operator has to check in the browser
    network tab -- it is assumed nowhere in this code.
``Defense Health Agency and VA``
    DHA staffs the military treatment facilities where physical therapists,
    athletic trainers, and dietitians assigned to operational units are
    likely to sit. VA runs its own recruitment site alongside its USAJOBS
    listings. Neither was inspected.
``State and territorial guard / emergency management boards``
    Same pattern, smaller scale.

WHY THIS IS CONFIGURABLE RATHER THAN A SCRAPER PER SITE
These sites have nothing in common except that they answer with JSON. Each
one wraps its records under a different key, names its fields differently,
and paginates differently. Writing one hardcoded module per site produces a
dozen brittle scrapers that break silently and separately, and none of them
could be verified here anyway -- this module was written with no outbound
network, so guessing at exact URLs and key names would have shipped a dozen
confident lies.

So the adapter is *declarative*. The operator opens the careers page with the
browser network tab open, copies the JSON request the page makes, and writes
down where the records and fields live::

    [[sources]]
    kind = "agencyboard"
    name = "example-naf"
    url = "https://example.gov/api/vacancies"
    records_path = "data.results"
    base_url = "https://example.gov"
    page_param = "page"
    max_pages = 5
    [sources.field_map]
    title = "position.title"
    url = "links.detail"
    source_id = "vacancyId"
    location = ["location.display", "installation.name"]
    description = ["summary", "duties", "qualifications"]
    posted_at = "openDate"
    compensation = "payPlan.display"

Nothing here needs an API key, an account, or an OAuth flow. Every option is
a URL and a path; if a board requires a credential it does not belong in this
project at all.

THE EXAMPLES IN THIS FILE ARE SHAPES, NOT VERIFIED ENDPOINTS. No URL here has
been confirmed against a live host. Open the target board, watch the request
its own front end makes, and paste that URL and those paths.

TWO ADAPTERS
``agencyboard``
    The declarative JSON reader described above. GET or POST, paginated,
    with an optional bounded detail fetch for boards whose list endpoint
    carries only a teaser.
``sitemapjobs``
    A deliberately low-information *discovery* adapter. See its docstring:
    it exists to find URLs, not to publish jobs.
"""

from __future__ import annotations

import gzip
import json
import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Iterable
from urllib.parse import unquote, urlencode, urljoin, urlparse

from ..http import FetchError, fetch, fetch_json, post_json
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

# Reused rather than re-implemented: these two are the project's existing
# answers to "an option arrived as junk" and "this field could be a string, an
# object, or a list of either", and a second copy of them would drift.
from .govjobs import as_int, flatten

log = logging.getLogger(__name__)

DEFAULT_MAX_PAGES = 5
DEFAULT_DETAIL_LIMIT = 25
DEFAULT_DETAIL_MIN_CHARS = 400
"""A list description shorter than this triggers the detail fetch.

Agency list endpoints publish a one-line teaser. The certifications (CSCS,
TSAC-F, ATC, RD), the clearance line, and the installation all live in the
full posting, so a teaser-length description is treated as "not the real
description yet".
"""

DEFAULT_MAX_URLS = 300
DEFAULT_MAX_SITEMAPS = 10

MAP_TOKEN = "[]"
"""Path segment meaning "apply the rest of this path to every list element"."""


def _require_text(source: Source, key: str) -> str:
    """A required option that must be a non-empty string.

    ``Source.require`` only checks that the key is present, so ``url = ""``
    or a key whose value came back ``None`` used to survive ``str(...)`` as
    the literal text ``"None"``. The board then "worked": it made a request
    that failed to resolve, every record's relative link failed to join, and
    the source reported zero jobs forever with no error anywhere. A silent
    zero is the one failure mode this project cannot afford, so a blank
    required option is an error.
    """
    value = source.require(key)
    text = "" if value is None else str(value).strip()
    if not text:
        raise KeyError(
            f"source '{source.name}' ({source.kind}) requires a non-empty '{key}'"
        )
    return text


# ---------------------------------------------------------------------------
# dot paths
# ---------------------------------------------------------------------------

_BRACKETS = re.compile(r"\[\s*\]")


def _segments(path: str) -> list[str]:
    """Split a dot path into segments, tolerating bracket-attached maps.

    ``sections[].text`` and ``sections.[].text`` are the same path; operators
    write both. Empty segments (``a..b``, a leading or trailing dot) are
    dropped rather than treated as a lookup for the empty-string key.
    """
    text = _BRACKETS.sub(f".{MAP_TOKEN}.", str(path))
    return [segment.strip() for segment in text.split(".") if segment.strip()]


def _walk(value: Any, parts: list[str]) -> Any:
    for position, part in enumerate(parts):
        if value is None:
            return None

        if part == MAP_TOKEN:
            if not isinstance(value, (list, tuple)):
                # "[]" against a scalar or an object is a config error, not a
                # crash: the board changed shape and this source now finds
                # nothing, which the review queue will show.
                return None
            rest = parts[position + 1 :]
            if not rest:
                return list(value)
            mapped: list[Any] = []
            for item in value:
                found = _walk(item, rest)
                if found in (None, "", [], {}):
                    continue
                # Flatten one level so "a[].b[].c" yields a flat list rather
                # than a list of lists nobody downstream would know to unpack.
                if isinstance(found, list):
                    mapped.extend(found)
                else:
                    mapped.append(found)
            return mapped

        if isinstance(value, dict):
            if part in value:
                value = value[part]
                continue
            return None

        if isinstance(value, (list, tuple)):
            stripped = part[1:] if part.startswith("-") else part
            if not stripped.isdigit():
                return None
            try:
                value = value[int(part)]
            except IndexError:
                return None
            continue

        # A scalar with path left to walk.
        return None
    return value


def resolve_path(payload: Any, path: str | None) -> Any:
    """Walk a dot path such as ``data.jobs.0.title`` or ``sections[].body``.

    Three rules, all of them chosen so that a board quietly dropping a field
    costs one empty column rather than the whole run:

    * An empty path (or ``None``) means "the payload itself" -- how a
      response whose root *is* the array of records is configured.
    * A missing intermediate key returns ``None`` instead of raising.
    * A numeric segment indexes a list (``-1`` counts from the end), and
      ``[]`` maps the remainder of the path over every element.
    """
    if path is None or str(path).strip() == "":
        return payload
    return _walk(payload, _segments(path))


# ---------------------------------------------------------------------------
# small coercions
# ---------------------------------------------------------------------------

_TRUTHY = {"true", "yes", "y", "1", "remote", "virtual"}  # not "telework"


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        return value.strip().lower() in _TRUTHY or looks_remote(value)
    return bool(value)


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
        parts = (
            _blob(v, depth + 1) for k, v in value.items() if not str(k).startswith("@")
        )
        return "\n".join(part for part in parts if part)
    return ""


def _with_query(url: str, params: dict[str, Any]) -> str:
    """Append ``params`` to ``url``'s query string, preserving what is there."""
    if not params:
        return url
    separator = "&" if urlparse(url).query else "?"
    return f"{url}{separator}{urlencode(params)}"


def _mapping(value: Any, source: str, kind: str, option: str) -> dict[str, Any]:
    """Validate that a table-shaped option really is a table.

    ``params = "page=1"`` or ``detail_field_map = ["title", "url"]`` are easy
    things to type into TOML. Left unchecked they either blow up deep inside
    ``urlencode`` with ``dictionary update sequence element #0 has length 1``
    -- which names neither the source nor the option -- or, worse, raise
    ``AttributeError`` once per record inside the per-record guard, so the
    board reports zero jobs and no error at all. Failing here names the
    source and the option.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise TypeError(
            f"source '{source}' ({kind}) needs option '{option}' to be a table, "
            f"got {type(value).__name__}"
        )
    return dict(value)


def _absolute(candidate: Any, base: str) -> str:
    """Resolve a possibly relative link against ``base``.

    Agency boards emit ``/vacancy/12345``, ``//host/vacancy/12345``, and full
    URLs interchangeably, sometimes within one response. A posting whose url
    cannot be clicked is worse than no posting at all, so anything that does
    not resolve to http(s) comes back empty and the record is dropped.
    """
    text = str(candidate or "").strip()
    if not text:
        return ""
    if text.startswith(("http://", "https://")):
        return text
    if text.startswith("//"):
        scheme = urlparse(base).scheme or "https"
        return f"{scheme}:{text}"
    if not base:
        return ""
    try:
        resolved = urljoin(base, text)
    except ValueError:
        return ""
    return resolved if urlparse(resolved).scheme in ("http", "https") else ""


def _decode(body: Any) -> Any:
    """Parse a POST response body.

    ``http.post_json`` returns raw bytes rather than parsed JSON, so the
    decoding happens here. An already-parsed value passes through.
    """
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", "replace")
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError as exc:
            raise FetchError(f"agency board returned non-JSON body: {exc}") from exc
    return body


class _TemplateFields(dict):
    """Format mapping that renders unknown placeholders as empty text.

    ``detail_url_template`` is operator-written and a typo in a placeholder
    must not raise mid-fetch.
    """

    def __missing__(self, key: str) -> str:  # pragma: no cover - trivial
        return ""


_FIELDS = (
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
    "job_type",
)


# ---------------------------------------------------------------------------
# declarative JSON board
# ---------------------------------------------------------------------------


class AgencyBoardSource(Source):
    """One agency job board, described entirely in configuration.

    Options
    -------
    url
        Endpoint returning JSON. Required.
    method
        ``"GET"`` (default) or ``"POST"``. A POST sends ``json_body``.
    json_body
        Request body for POST mode. The page value is written into a copy of
        it, so the configured table is never mutated between pages.
    params / headers
        Passed through to the request. In POST mode ``params`` still goes on
        the query string, since boards that POST a search body often want
        both. Both must be tables; so must ``json_body`` and
        ``detail_field_map``, and all four are checked before the first
        request rather than failing per-record later.
    records_path
        Dot path to the array of records. ``""`` (the default) means the root
        of the response is itself the array. A single object resolves as a
        one-record list.
    field_map
        JobPosting field name -> dot path within one record. ``title`` and
        ``url`` are required; everything else is optional. A value may be a
        list of paths, in which case the first non-empty one wins -- except
        for ``description``, where every path is concatenated, because the
        qualifications block is exactly where the certifications and
        clearances live.
    base_url
        Base for relative links. Defaults to ``url``.
    employer
        Employer label when the map has no ``employer`` path.
    page_param, page_start, page_step, max_pages, total_pages_path
        Pagination. Without ``page_param`` exactly one request is made. With
        it, page values run ``page_start``, ``page_start + page_step``, ...
        for at most ``max_pages`` requests (default 5), stopping early on an
        empty page, on a page with nothing new, or when ``total_pages_path``
        says there are no more.
    detail_url_template, detail_id_field, detail_records_path,
    detail_field_map, detail_limit, detail_min_chars
        Optional second request per record for boards whose list endpoint
        carries only a teaser. The template is rendered from the record --
        ``{id}`` is ``detail_id_field`` resolved against the record, and any
        top-level scalar key is available by name. Bounded by
        ``detail_limit`` (default 25) and only attempted when the list
        description is shorter than ``detail_min_chars`` (default 400).
    """

    kind = "agencyboard"

    def fetch(self) -> Iterable[JobPosting]:
        url = _require_text(self, "url")
        field_map = self._field_map()
        # Validated up front, before a single request: a mistyped table option
        # must name itself here rather than fail per-record later, where the
        # per-record guard would turn it into a silent zero-job run.
        for option in ("params", "headers", "json_body", "detail_field_map"):
            _mapping(self.options.get(option), self.name, self.kind, option)
        employer_default = self.options.get("employer") or self.name
        records_path = self.options.get("records_path", "")
        base_url = str(self.options.get("base_url") or "").strip() or url

        page_param = str(self.options.get("page_param") or "").strip()
        page_start = as_int(self.options.get("page_start"), 1)
        page_step = max(1, as_int(self.options.get("page_step"), 1))
        max_pages = max(1, as_int(self.options.get("max_pages"), DEFAULT_MAX_PAGES))
        pages = max_pages if page_param else 1

        detail_budget = max(0, as_int(self.options.get("detail_limit"), DEFAULT_DETAIL_LIMIT))
        min_chars = as_int(self.options.get("detail_min_chars"), DEFAULT_DETAIL_MIN_CHARS)

        seen: set[str] = set()
        for index in range(pages):
            page = page_start + index * page_step
            try:
                payload = self._request(url, page_param, page)
            except Exception as exc:
                # A first page that will not load is a broken config or a dead
                # board, not a flaky page: surface it rather than reporting a
                # zero-job run as a success.
                if index == 0:
                    raise
                log.warning("%s: page %s failed: %s", self.name, page, exc)
                break

            records = self._records(payload, records_path)
            if not records:
                break

            fresh = 0
            for record in records:
                try:
                    posting, spent = self._to_posting(
                        record,
                        base_url,
                        field_map,
                        employer_default,
                        detail_budget > 0,
                        min_chars,
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
                # A board that ignores the page parameter returns page 1
                # forever; without this it would be fetched max_pages times.
                break

            # Probed only when configured: an unset path resolves to the whole
            # payload, and coercing that would log a "non-numeric option"
            # warning on every page of every source that does not use it.
            total_pages_path = str(self.options.get("total_pages_path") or "").strip()
            if total_pages_path:
                total_pages = as_int(resolve_path(payload, total_pages_path), 0)
                if total_pages > 0 and (index + 1) >= total_pages:
                    break

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

    # -- requests ---------------------------------------------------------

    def _request(self, url: str, page_param: str, page: int) -> Any:
        method = str(self.options.get("method") or "GET").strip().upper()
        headers = _mapping(self.options.get("headers"), self.name, self.kind, "headers")
        params = _mapping(self.options.get("params"), self.name, self.kind, "params")

        if method == "POST":
            body = _mapping(
                self.options.get("json_body"), self.name, self.kind, "json_body"
            )
            if page_param:
                body[page_param] = page
            # ``post_json`` takes no params argument, but boards that POST a
            # search body routinely still want query-string parameters (a
            # locale, a tenant id). Dropping them silently would send a
            # request the operator did not configure, so they go on the URL.
            return _decode(
                post_json(
                    _with_query(url, params),
                    body,
                    headers={"Accept": "application/json", **headers},
                )
            )

        if method != "GET":
            log.warning("%s: unsupported method %r, using GET", self.name, method)
        if page_param:
            params[page_param] = page
        return fetch_json(url, params=params or None, headers=headers or None)

    def _records(self, payload: Any, records_path: Any) -> list[Any]:
        records = resolve_path(payload, records_path)
        if isinstance(records, dict):
            # A single-record response is a list of one, not an error.
            return [records]
        if isinstance(records, tuple):
            return list(records)
        if isinstance(records, list):
            return records
        if records is not None:
            log.warning(
                "%s: records_path %r did not resolve to a list", self.name, records_path
            )
        return []

    def _detail(self, url: str) -> Any:
        try:
            return fetch_json(url, headers=self.options.get("headers") or None)
        except Exception as exc:
            # A single unavailable detail page must not drop the posting; the
            # list-level fields may still be enough for the review queue.
            log.debug("%s: detail fetch failed for %s: %s", self.name, url, exc)
            return None

    def _detail_url(self, record: Any, field_map: dict[str, Any], base_url: str) -> str:
        template = str(self.options.get("detail_url_template") or "").strip()
        if not template:
            return ""

        id_path = self.options.get("detail_id_field") or field_map.get("detail_id") or ""
        identifier = flatten(resolve_path(record, str(id_path))) if id_path else ""
        if "{id}" in template and not identifier:
            # Rendering "{id}" empty would spend a request on the board's index
            # page and attach its text to this posting.
            log.debug("%s: no detail id for record, skipping detail fetch", self.name)
            return ""

        fields = _TemplateFields()
        if isinstance(record, dict):
            for key, value in record.items():
                if not isinstance(value, (dict, list, tuple)):
                    fields[str(key)] = flatten(value)
        fields["id"] = identifier

        try:
            rendered = template.format_map(fields)
        except (AttributeError, IndexError, KeyError, TypeError, ValueError) as exc:
            log.warning(
                "%s: detail_url_template %r could not be rendered: %s",
                self.name,
                template,
                exc,
            )
            return ""
        return _absolute(rendered, base_url)

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
        the half of the posting this project actually mines.
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

    # -- mapping ----------------------------------------------------------

    def _to_posting(
        self,
        record: Any,
        base_url: str,
        field_map: dict[str, Any],
        employer_default: str,
        may_fetch_detail: bool,
        min_chars: int,
    ) -> tuple[JobPosting | None, bool]:
        if not isinstance(record, (dict, list)):
            log.debug("%s: skipping scalar record %r", self.name, record)
            return None, False

        values = {field: self._resolve(record, field_map, field) for field in _FIELDS}
        title = flatten(values["title"])
        url = _absolute(flatten(values["url"]), base_url)
        if not title or not url:
            log.debug("%s: record missing a title or url, skipping", self.name)
            return None, False

        description = self._describe(record, field_map)

        detail_record: Any = None
        spent_detail = False
        # The detail pass is an enrichment, never a precondition. Anything it
        # raises -- a template that will not render, a detail_field_map the
        # board does not match, a payload shaped unlike the list -- must cost
        # the extra text and nothing else. Before this guard, one bad
        # detail_field_map made every posting on the board disappear with no
        # error: the enrichment failed inside the caller's per-record
        # try/except, which dropped the already-valid posting with it.
        if may_fetch_detail and len(description) < min_chars:
            try:
                detail_url = self._detail_url(record, field_map, base_url)
                if detail_url:
                    # The attempt is what costs a request, so the attempt is
                    # what the budget counts -- otherwise a board whose detail
                    # pages all 404 would fan out without limit.
                    spent_detail = True
                    detail_record = self._detail_record(self._detail(detail_url))
            except Exception as exc:
                log.warning("%s: detail pass failed, keeping list record: %s", self.name, exc)
                detail_record = None

        if detail_record is not None:
            try:
                detail_map = self.options.get("detail_field_map") or field_map
                detail_text = self._describe(detail_record, detail_map)
                if len(detail_text) > len(description):
                    description = detail_text
                for field in _FIELDS:
                    if field in ("title", "url", "description"):
                        continue
                    if not values.get(field):
                        values[field] = self._resolve(detail_record, detail_map, field)
            except Exception as exc:
                log.warning("%s: detail merge failed, keeping list record: %s", self.name, exc)

        location = flatten(values["location"])
        job_type = flatten(values["job_type"])
        compensation = flatten(values["compensation"])
        department = flatten(values["department"])
        remote = (
            _truthy(values["remote"])
            if "remote" in field_map
            else looks_remote(location, title, job_type)
        )

        # Fold the structured facts back into the text so the classifier and
        # the enrichment layer see them without special-casing this schema.
        facts = [
            f"{label} {value}."
            for label, value in (
                ("Job type:", job_type),
                ("Salary:", compensation),
                ("Department:", department),
            )
            if value
        ]
        if facts:
            description = f"{description}\n\n{' '.join(facts)}".strip()

        raw: dict[str, Any] = {"listing": record}
        if detail_record is not None:
            raw["detail"] = detail_record

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
                department=department or None,
                compensation=compensation or None,
                raw=raw,
            ),
            spent_detail,
        )

    def _detail_record(self, payload: Any) -> Any:
        if payload is None:
            return None
        record = resolve_path(payload, self.options.get("detail_records_path", ""))
        if isinstance(record, list):
            # Some boards answer a detail request with a one-element array.
            record = next((item for item in record if isinstance(item, dict)), None)
        return record


# ---------------------------------------------------------------------------
# sitemap discovery
# ---------------------------------------------------------------------------


def _local_name(tag: Any) -> str:
    return str(tag).rsplit("}", 1)[-1].lower()


def _gunzip(body: Any) -> Any:
    """Transparently decompress a ``.xml.gz`` sitemap.

    ``http.fetch`` decompresses responses served with ``Content-Encoding:
    gzip``, but large sites publish sitemaps as *files* that are gzipped --
    the bytes are compressed and the header says nothing about it.
    """
    if isinstance(body, (bytes, bytearray)) and bytes(body[:2]) == b"\x1f\x8b":
        try:
            return gzip.decompress(bytes(body))
        except (OSError, EOFError):
            return body
    return body


_EXTENSION = re.compile(r"\.(?:html?|aspx?|php|jsp|do|xml|json)$", re.IGNORECASE)
_SEPARATORS = re.compile(r"[-_+]+")

_ACRONYMS = frozenset(
    {
        # Programs and commands this project exists to track.
        "h2f", "thor3", "potff", "usasoc", "socom", "marsoc", "afsoc", "jsoc",
        "sof", "nsw", "mwr", "naf", "mccs", "dha", "dod", "va", "ems", "emt",
        # Credentials that show up in slugs.
        "cscs", "tsac", "atc", "nsca", "acsm",
    }
)
"""Slug tokens rendered in full caps rather than title case.

Real career-site slugs are lowercase, so the "leave words that already carry
an uppercase letter alone" rule never fires on them: ``athletic-trainer-h2f``
came out as "Athletic Trainer H2f". This is presentation only -- the
classifier lowercases before matching, so nothing about scoring depends on
it -- but the review queue is read by a human, and "H2f" and "Potff" read as
typos in the one column that is supposed to say what the job is.
"""

_GENERIC_SEGMENTS = frozenset(
    {
        "job", "jobs", "career", "careers", "vacancy", "vacancies",
        "position", "positions", "opening", "openings", "listing", "listings",
        "posting", "postings", "opportunity", "opportunities",
        "detail", "details", "view", "search", "apply", "index", "home",
        "page", "en", "en us", "us en", "content",
    }
)
"""Path segments that describe the site's routing, never the job."""


def _titleize(text: str) -> str:
    """Capitalize a de-slugified string without flattening acronyms."""
    words = []
    for word in text.split():
        if word.lower() in _ACRONYMS:
            words.append(word.upper())
        elif any(character.isupper() for character in word):
            words.append(word)
        else:
            words.append(word[:1].upper() + word[1:])
    return " ".join(words)


def deslugify(url: str) -> str:
    """Derive a display title from a job URL's path.

    ``/careers/jobs/tactical-strength-and-conditioning-coach-fort-bragg`` is
    a perfectly readable title once the hyphens come out. A purely numeric
    final segment (``/vacancy/948213``) is not, so an earlier *descriptive*
    segment wins instead -- which recovers a usable title from the
    ``/jobs/athletic-trainer/948213`` shape many boards use.

    "Descriptive" has to exclude the site's own routing words. Scanning back
    for merely "the last segment containing letters" turned every URL on a
    ``/jobs/<id>`` board into the title "Jobs" -- one identical, meaningless
    title for the entire board, which is strictly worse than the id, because
    the id at least distinguishes the rows in the review queue. So a generic
    segment is skipped too, and if nothing descriptive is left the final
    segment is used verbatim, number and all.
    """
    path = urlparse(str(url or "")).path
    segments = [segment for segment in path.split("/") if segment.strip()]
    if not segments:
        return ""

    cleaned: list[str] = []
    for segment in segments:
        text = _EXTENSION.sub("", unquote(segment))
        text = _SEPARATORS.sub(" ", text)
        text = re.sub(r"\s+", " ", text).strip()
        cleaned.append(text)

    chosen = next(
        (
            text
            for text in reversed(cleaned)
            if text
            and any(character.isalpha() for character in text)
            and text.lower() not in _GENERIC_SEGMENTS
        ),
        "",
    )
    chosen = chosen or next((text for text in reversed(cleaned) if text), "")
    return _titleize(chosen)


class SitemapJobsSource(Source):
    """Walk a sitemap and emit one low-information record per job URL.

    THIS IS A DISCOVERY ADAPTER, NOT A PUBLISHING ONE.
    ---------------------------------------------------
    It produces records that carry a URL and a title guessed from the URL
    slug, and **nothing else** -- no description, no employer beyond the
    configured label, no location, no date. That is not a shortcoming to be
    fixed; it is the entire design:

    * Those records score low, because there is almost no text to score.
    * A low score routes them to the review queue rather than to publication.
    * The review queue is a list of *URLs a human should look at* -- which is
      exactly the artifact wanted from a board whose JSON API has not been
      found yet.

    The intended workflow is therefore: point this at a career site's
    sitemap, read the review queue, confirm the URL pattern the real postings
    use, then point the ``jsonld`` adapter (or ``agencyboard``, if the site
    has a JSON endpoint) at those URLs to get the full text. Using this
    adapter's output as the finished product would flood the site with
    title-only stubs, so it is deliberately not built to do that.

    Nothing here auto-applies anything: a discovered URL becomes a candidate
    for a human to confirm, the same contract the employer discovery module
    keeps.

    Options
    -------
    sitemap
        Sitemap or sitemap-index URL. Required. An index is followed one
        level down, which is the shape large career sites publish.
    url_include / url_exclude
        Substrings a URL must / must not contain, e.g.
        ``url_include = ["/job/"]``. Without ``url_include`` every page in
        the sitemap becomes a record, which is rarely what anyone wants.
    max_urls
        Cap on records emitted per run. Default 300.
    max_sitemaps
        Cap on child sitemaps read from an index. Default 10.
    employer
        Employer label for every record. Defaults to the source name.
    """

    kind = "sitemapjobs"

    def fetch(self) -> Iterable[JobPosting]:
        sitemap = _require_text(self, "sitemap")
        employer = self.options.get("employer") or self.name
        includes = _as_list(self.options.get("url_include"))
        excludes = _as_list(self.options.get("url_exclude"))
        # Clamped, not just coerced. A negative value used to switch the cap
        # off entirely, which is the opposite of what an option named
        # "max_urls" should ever do on an adapter that walks a stranger's
        # whole sitemap.
        max_urls = max(0, as_int(self.options.get("max_urls"), DEFAULT_MAX_URLS))
        max_sitemaps = max(0, as_int(self.options.get("max_sitemaps"), DEFAULT_MAX_SITEMAPS))

        entries, children = self._read_sitemap(sitemap, required=True)
        if children:
            visited = {sitemap}
            fetched = 0
            for child in children:
                if fetched >= max_sitemaps:
                    log.debug("%s: sitemap index truncated at %d children", self.name, max_sitemaps)
                    break
                if child in visited:
                    # An index that repeats (or self-references) a shard must
                    # not cost a second request.
                    continue
                visited.add(child)
                fetched += 1
                # Only one level of nesting is followed on purpose: an index of
                # indexes is rare, and unbounded recursion over a stranger's
                # sitemap tree is not something to do politely.
                child_entries, _ = self._read_sitemap(child, required=False)
                entries.extend(child_entries)

        seen: set[str] = set()
        emitted = 0
        for url, lastmod in entries:
            if url in seen:
                continue
            seen.add(url)
            if includes and not any(fragment in url for fragment in includes):
                continue
            if excludes and any(fragment in url for fragment in excludes):
                continue
            if emitted >= max_urls:
                break
            posting = self._to_posting(url, lastmod, employer)
            if posting is None:
                continue
            emitted += 1
            yield posting

    # -- sitemap reading --------------------------------------------------

    def _read_sitemap(
        self, sitemap_url: str, *, required: bool
    ) -> tuple[list[tuple[str, str]], list[str]]:
        """Return ``(entries, child_sitemap_urls)`` for one sitemap file.

        ``required`` marks the sitemap the operator configured. If *that* one
        cannot be read the source is broken, and reporting zero jobs would
        hide a dead configuration; a child shard failing is a partial result
        worth keeping.
        """
        try:
            body = _gunzip(fetch(sitemap_url))
        except Exception as exc:
            if required:
                raise RuntimeError(f"sitemap {sitemap_url} could not be read: {exc}") from exc
            log.warning("%s: sitemap %s unavailable: %s", self.name, sitemap_url, exc)
            return [], []

        try:
            root = ET.fromstring(body)
        except (ET.ParseError, ValueError, TypeError) as exc:
            if required:
                raise RuntimeError(f"sitemap {sitemap_url} is not valid XML: {exc}") from exc
            log.warning("%s: sitemap %s is not valid XML: %s", self.name, sitemap_url, exc)
            return [], []

        # ElementTree has no parent pointers, so the root tag decides how the
        # <loc> entries are read: a <sitemapindex> lists other sitemaps, a
        # <urlset> lists pages.
        is_index = _local_name(root.tag) == "sitemapindex"

        entries: list[tuple[str, str]] = []
        children: list[str] = []
        matched = False

        for node in root:
            if _local_name(node.tag) not in ("url", "sitemap"):
                continue
            matched = True
            location = ""
            lastmod = ""
            for child in node:
                name = _local_name(child.tag)
                if name == "loc" and not location:
                    location = (child.text or "").strip()
                elif name == "lastmod" and not lastmod:
                    lastmod = (child.text or "").strip()
            # <loc> is required to be absolute, but plenty of generators emit
            # a site-root path anyway.
            resolved = _absolute(location, sitemap_url)
            if not resolved:
                continue
            if is_index:
                children.append(resolved)
            else:
                entries.append((resolved, lastmod))

        if not matched:
            # A generator that nests <loc> somewhere unexpected still gets read.
            for element in root.iter():
                if _local_name(element.tag) != "loc":
                    continue
                resolved = _absolute((element.text or "").strip(), sitemap_url)
                if not resolved:
                    continue
                if is_index:
                    children.append(resolved)
                else:
                    entries.append((resolved, ""))

        return entries, children

    # -- mapping ----------------------------------------------------------

    def _to_posting(self, url: str, lastmod: str, employer: str) -> JobPosting | None:
        title = deslugify(url) or urlparse(url).netloc
        if not title:
            log.debug("%s: no usable title for %s", self.name, url)
            return None

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=url,
            url=url,
            title=title,
            employer=employer,
            location="",
            # Left empty on purpose. Guessing a description from a URL would
            # manufacture text the classifier would then score, and a
            # confidently wrong score is worse than a low one.
            description="",
            # <lastmod> is when the page changed, not when the job was posted.
            # Treating it as posted_at would make every re-crawled page look
            # freshly posted, so it stays in raw for a human to interpret.
            posted_at=None,
            remote=looks_remote(title),
            department=None,
            compensation=None,
            raw={"sitemapUrl": url, "lastmod": lastmod, "discovery": True},
        )


AGENCY_SOURCES: tuple[type[Source], ...] = (
    AgencyBoardSource,
    SitemapJobsSource,
)
