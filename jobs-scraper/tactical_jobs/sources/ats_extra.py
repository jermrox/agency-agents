"""Second-tier ATS adapters: the platforms mid-size employers actually use.

``ats.py`` covers the boards the venture-funded end of the market runs on.
This module covers everything else, and for this niche "everything else" is
most of the market: a 40-person tactical performance firm, a county fire
department, a municipal police wellness program, or a regional sports-medicine
group is far more likely to be on BambooHR, Breezy, JazzHR, Teamtailor,
Personio, or Rippling than on Greenhouse.

Same rules as ``ats.py``: every endpoint here is the vendor's own public
job-board API -- the JSON (or XML) that powers the employer's own careers
page. Nothing here scrapes a rendered page, and nothing here touches an
aggregator whose terms forbid collection.

Two behaviors are load-bearing across all six adapters:

* **Full descriptions.** The classifier and the enrichment layer mine the
  complete text for certifications (CSCS, TSAC-F, ATC, RD), clearance level,
  installation, and salary language. A title-only record is nearly worthless
  here, so where a list endpoint omits the description (BambooHR) the adapter
  spends a second request per posting, bounded by ``detail_limit``.
* **Per-record isolation.** One unusable record must never cost the rest of
  the board, so each posting is built inside its own try/except and a failure
  is logged and skipped.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from typing import Any, Iterable
from urllib.parse import quote, urljoin

from ..http import fetch, fetch_json
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

log = logging.getLogger(__name__)

JSON_HEADERS = {"Accept": "application/json"}

_LABEL_KEYS = ("label", "name", "title", "value", "text", "descriptor")


def _label(value: Any) -> str:
    """Flatten the several shapes these vendors use for one scalar field.

    The same logical field arrives as a bare string, as ``{"label": ...}`` or
    ``{"name": ...}``, or as a list of either, depending on the vendor and the
    endpoint. Normalizing once here keeps that mess out of the mapping code --
    and keeps a surprise dict from crashing an adapter.
    """
    if value is None or isinstance(value, bool):
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, dict):
        for key in _LABEL_KEYS:
            text = _label(value.get(key))
            if text:
                return text
        return ""
    if isinstance(value, (list, tuple)):
        return ", ".join(part for part in (_label(item) for item in value) if part)
    return ""


def _join(*parts: Any) -> str:
    """Comma-join the parts that carry text, in order, without repeats."""
    kept: list[str] = []
    for part in parts:
        text = _label(part)
        if text and text not in kept:
            kept.append(text)
    return ", ".join(kept)


def _first_text(record: dict[str, Any], keys: Iterable[str]) -> str:
    """First key in ``keys`` that flattens to a non-empty string."""
    if not isinstance(record, dict):
        return ""
    for key in keys:
        text = _label(record.get(key))
        if text:
            return text
    return ""


def _first_timestamp(record: dict[str, Any], keys: Iterable[str]):
    """First key in ``keys`` that parses as a timestamp.

    Vendors disagree about which field means "posted": ``published_date``,
    ``createdAt``, ``original_open_date``. Trying them in order beats guessing.
    """
    if not isinstance(record, dict):
        return None
    for key in keys:
        stamp = parse_timestamp(record.get(key))
        if stamp is not None:
            return stamp
    return None


def _records(payload: Any, *container_keys: str) -> list[Any]:
    """Normalize a list-or-envelope payload into a list of records.

    Some of these APIs return a bare array, some wrap it (``{"result": []}``),
    and several return a lone object rather than a one-element array when the
    board has exactly one opening -- which is a very common state for the small
    employers this module targets.
    """
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in container_keys:
            inner = payload.get(key)
            if isinstance(inner, list):
                return inner
            if isinstance(inner, dict):
                return [inner]
        if any(key in payload for key in ("id", "uuid")):
            return [payload]
    return []


def _humanize(value: str) -> str:
    """``FULL_TIME`` -> ``Full Time``. Vendors shout enums; prose reads better."""
    if value and (value.isupper() or "_" in value):
        return value.replace("_", " ").title()
    return value


def _with_facts(description: str, facts: Iterable[tuple[str, Any]]) -> str:
    """Fold structured list fields into the description text.

    The classifier and the enrichment layer read one blob of prose. Folding
    employment type, department, and location into it means neither has to
    special-case a vendor schema to see them.
    """
    lines = [f"{label}: {text}." for label, value in facts if (text := _label(value))]
    if not lines:
        return description
    return f"{description}\n\n{' '.join(lines)}".strip()


def _xml_text(element: ET.Element | None) -> str:
    """Text of an XML element, including any nested markup it wraps."""
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


def _int_option(options: dict[str, Any], key: str, default: int, *, minimum: int = 0) -> int:
    """Read a numeric option without letting a typo kill the whole source.

    Options come out of a hand-edited TOML file, so ``detail_limit = "50"`` or
    a stray ``detail_limit =`` is a realistic operator mistake. Bounding the
    fan-out is a safety rail; a bad value for the rail must not be fatal.
    """
    value = options.get(key, default)
    try:
        number = int(value)
    except (TypeError, ValueError):
        log.warning("option %r is not a number (%r); falling back to %d", key, value, default)
        number = default
    return max(minimum, number)


def _host_label(value: Any) -> str:
    """Reduce a board/company option to something legal in a hostname.

    The JazzHR apply URL puts this straight into the host, so an employer name
    like ``Acme Performance Group`` would otherwise produce
    ``https://Acme Performance Group.applytojob.com/...`` -- a link the
    pipeline happily publishes and no browser can open.
    """
    text = _label(value).strip().lower()
    if not text:
        return ""
    text = text.split("//")[-1].split("/")[0].split(".")[0]
    return re.sub(r"[^a-z0-9-]+", "-", text).strip("-")


def _require_dict(record: Any, kind: str) -> dict[str, Any]:
    if not isinstance(record, dict):
        raise TypeError(f"{kind} record is {type(record).__name__}, expected an object")
    return record


class BambooHRSource(Source):
    """A BambooHR-hosted careers page.

    Docs: the endpoints below are what ``{subdomain}.bamboohr.com/careers``
    calls to render itself.

    The list endpoint returns title, location, department, and employment
    status -- but no description, and the description is where every
    certification, clearance, and salary line lives. So each posting gets a
    second request against the detail endpoint, bounded by ``detail_limit``.
    A detail request that fails downgrades that posting to its list-level
    fields instead of dropping it.

    Options: ``subdomain`` (required), ``employer``, ``detail_limit``.
    """

    kind = "bamboohr"

    def fetch(self) -> Iterable[JobPosting]:
        subdomain = str(self.require("subdomain")).strip().strip("/")
        employer = self.options.get("employer") or subdomain
        detail_limit = _int_option(self.options, "detail_limit", 50)
        base_url = f"https://{subdomain}.bamboohr.com/careers"

        payload = fetch_json(f"{base_url}/list", headers=JSON_HEADERS)
        for index, record in enumerate(_records(payload, "result", "jobs")):
            try:
                posting = self._to_posting(
                    record,
                    base_url=base_url,
                    employer=employer,
                    want_detail=index < detail_limit,
                )
            except Exception as exc:
                log.warning("skipping malformed bamboohr record: %s", exc)
                continue
            if posting is not None:
                yield posting

    def _detail(self, base_url: str, job_id: str) -> dict[str, Any]:
        """The per-posting record, or ``{}`` when it is unavailable."""
        try:
            payload = fetch_json(
                f"{base_url}/{quote(job_id, safe='')}/detail", headers=JSON_HEADERS
            )
        except Exception as exc:
            log.debug("bamboohr detail fetch failed for %s: %s", job_id, exc)
            return {}
        result = payload.get("result") if isinstance(payload, dict) else None
        if not isinstance(result, dict):
            return {}
        opening = result.get("jobOpening")
        return opening if isinstance(opening, dict) else result

    def _to_posting(
        self,
        record: Any,
        *,
        base_url: str,
        employer: str,
        want_detail: bool,
    ) -> JobPosting:
        record = _require_dict(record, self.kind)
        job_id = _label(record.get("id"))
        if not job_id:
            raise ValueError("bamboohr record has no id")

        location = record.get("location")
        if isinstance(location, dict):
            location_text = _join(
                location.get("city"),
                location.get("state"),
                location.get("country") or location.get("addressCountry"),
            )
        else:
            location_text = _label(location)

        title = _first_text(record, ("jobOpeningName", "title", "name"))
        department = _first_text(record, ("departmentLabel", "department"))
        employment = _first_text(record, ("employmentStatusLabel", "employmentStatus"))

        detail = self._detail(base_url, job_id) if want_detail else {}
        description = html_to_text(
            _first_text(detail, ("description", "jobSummary", "jobDescription"))
        )
        if not description:
            # Thin, but a title plus the structured fields below is enough for
            # the review queue to decide whether a human should open the link.
            description = html_to_text(title)
        description = _with_facts(
            description,
            (
                ("Department", department),
                ("Employment type", employment),
                ("Location", location_text),
            ),
        )

        raw: dict[str, Any] = {"listing": record}
        if detail:
            raw["detail"] = detail

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=job_id,
            url=f"{base_url}/{quote(job_id, safe='')}",
            title=title,
            employer=employer,
            location=location_text,
            description=description,
            posted_at=_first_timestamp(record, ("datePosted", "postedDate", "createdDate"))
            or _first_timestamp(detail, ("datePosted", "postedDate", "createdDate")),
            remote=bool(record.get("isRemote")) or looks_remote(location_text, title),
            department=department or None,
            compensation=_first_text(detail, ("compensation", "compensationRange", "payRange"))
            or None,
            raw=raw,
        )


class BreezySource(Source):
    """A Breezy HR careers page.

    ``https://{company}.breezy.hr/json`` is the same feed the public board
    renders from, and it carries the full HTML description inline, so one
    request is enough.

    Options: ``company`` (required), ``employer``.
    """

    kind = "breezy"

    def fetch(self) -> Iterable[JobPosting]:
        company = str(self.require("company")).strip().strip("/")
        employer = self.options.get("employer") or company

        payload = fetch_json(f"https://{company}.breezy.hr/json", headers=JSON_HEADERS)
        for record in _records(payload, "positions", "jobs"):
            try:
                posting = self._to_posting(record, company=company, employer=employer)
            except Exception as exc:
                log.warning("skipping malformed breezy record: %s", exc)
                continue
            if posting is not None:
                yield posting

    def _to_posting(self, record: Any, *, company: str, employer: str) -> JobPosting:
        record = _require_dict(record, self.kind)
        job_id = _first_text(record, ("id", "_id", "friendly_id"))
        if not job_id:
            raise ValueError("breezy record has no id")

        location = record.get("location")
        location = location if isinstance(location, dict) else {}
        # ``name`` is already the display string ("Fort Bragg, NC"); the parts
        # are only assembled when it is missing.
        location_text = _label(location.get("name")) or _join(
            location.get("city"), location.get("state"), location.get("country")
        )
        title = _first_text(record, ("name", "title"))
        department = _first_text(record, ("department", "team"))
        employment = _label(record.get("type"))

        description = _with_facts(
            html_to_text(_first_text(record, ("description", "content"))),
            (("Department", department), ("Employment type", employment)),
        )

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=job_id,
            url=_label(record.get("url"))
            or f"https://{company}.breezy.hr/p/{quote(job_id, safe='')}",
            title=title,
            employer=employer,
            location=location_text,
            description=description,
            posted_at=_first_timestamp(
                record, ("published_date", "creation_date", "updated_date")
            ),
            remote=bool(location.get("is_remote"))
            or looks_remote(location_text, title, employment),
            department=department or None,
            raw=record,
        )


class JazzHRSource(Source):
    """JazzHR's Resumator API.

    Docs: https://www.resumatorapi.com/v1/ -- the key is a board-scoped read
    key the employer generates, not a user credential.

    The feed includes closed, filled, and draft requisitions, so anything not
    explicitly open is dropped here rather than published. A record with no
    status at all is kept: a missing field is not evidence that a job closed.

    Options: ``api_key`` (required), ``board``, ``employer``.
    """

    kind = "jazzhr"

    OPEN_STATUSES = frozenset({"open", "opened", "active"})

    def fetch(self) -> Iterable[JobPosting]:
        api_key = str(self.require("api_key")).strip()
        board_option = self.options.get("board")
        employer = self.options.get("employer") or _label(board_option) or self.name
        # The board slug lands inside a hostname, so it is slugified rather
        # than interpolated raw; a display name with spaces would otherwise
        # produce an unopenable link that still passes the pipeline's
        # "has a url" check.
        board = _host_label(board_option or employer)
        if not board:
            # Nothing usable to build the public apply URL from: report it the
            # same way any other missing option is reported.
            board = _host_label(self.require("board"))

        payload = fetch_json(
            "https://api.resumatorapi.com/v1/jobs",
            params={"apikey": api_key},
            headers=JSON_HEADERS,
        )
        for record in _records(payload, "jobs"):
            try:
                posting = self._to_posting(record, board=board, employer=employer)
            except Exception as exc:
                log.warning("skipping malformed jazzhr record: %s", exc)
                continue
            if posting is not None:
                yield posting

    def _to_posting(self, record: Any, *, board: str, employer: str) -> JobPosting | None:
        record = _require_dict(record, self.kind)
        job_id = _first_text(record, ("id", "board_code"))
        if not job_id:
            raise ValueError("jazzhr record has no id")

        status = _first_text(record, ("status", "job_status"))
        if status and status.lower() not in self.OPEN_STATUSES:
            log.debug("skipping jazzhr job %s with status %r", job_id, status)
            return None

        location_text = _join(record.get("city"), record.get("state"), record.get("country"))
        title = _first_text(record, ("title", "job_title"))
        department = _label(record.get("department"))
        employment = _first_text(record, ("type", "employment_type"))

        description = _with_facts(
            html_to_text(_first_text(record, ("description", "job_description"))),
            (("Department", department), ("Employment type", employment)),
        )

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=job_id,
            url=f"https://{board}.applytojob.com/apply/{quote(job_id, safe='')}",
            title=title,
            employer=employer,
            location=location_text,
            description=description,
            posted_at=_first_timestamp(
                record, ("original_open_date", "open_date", "created_date")
            ),
            remote=looks_remote(location_text, title, employment),
            department=department or None,
            raw=record,
        )


class TeamtailorSource(Source):
    """Teamtailor's JSON:API job endpoint.

    Docs: https://docs.teamtailor.com/ -- the API is versioned by header, and
    an unversioned request is rejected, so ``X-Api-Version`` is not optional.

    The response is paginated by ``links.next``; that link is followed rather
    than page numbers being synthesized, because Teamtailor's cursor carries
    filter state. ``max_pages`` bounds the walk so a large board cannot turn
    one nightly run into a thousand requests.

    Locations and departments are relationships, not attributes, so the
    request asks for them to be side-loaded and they are resolved out of
    ``included``.

    Options: ``api_key`` (required), ``employer``, ``max_pages``, ``page_size``.
    """

    kind = "teamtailor"

    API_URL = "https://api.teamtailor.com/v1/jobs"
    API_VERSION = "20210218"

    # Statuses that mean "not on the public career site". Deliberately a
    # deny-list: an unrecognized status should publish, not silently vanish.
    HIDDEN_STATUSES = frozenset({"draft", "archived", "unlisted", "closed"})

    def fetch(self) -> Iterable[JobPosting]:
        api_key = str(self.require("api_key")).strip()
        employer = self.options.get("employer") or self.name
        max_pages = _int_option(self.options, "max_pages", 5, minimum=1)
        page_size = _int_option(self.options, "page_size", 30, minimum=1)

        headers = {
            "Authorization": f"Token token={api_key}",
            "X-Api-Version": self.API_VERSION,
            **JSON_HEADERS,
        }

        url = str(self.options.get("url") or self.API_URL)
        params: dict[str, Any] | None = {
            "page[size]": page_size,
            "include": "department,locations",
        }
        seen_pages: set[str] = set()

        for page in range(max_pages):
            if url in seen_pages:
                # A vendor bug that points ``next`` back at the current page
                # would otherwise loop until max_pages, wasting requests.
                break
            seen_pages.add(url)
            try:
                payload = (
                    self._first_page(url, headers, params)
                    if page == 0
                    else fetch_json(url, headers=headers, params=params)
                )
            except Exception as exc:
                # Failing on the first page is a broken key or slug: report it
                # rather than returning zero jobs and calling that success.
                if page == 0:
                    raise
                log.warning("teamtailor pagination stopped at %s: %s", url, exc)
                break
            params = None  # links.next already carries the query string.

            if not isinstance(payload, dict):
                break
            index = _jsonapi_index(payload)
            # ``data`` is a list for a collection, but JSON:API also allows a
            # lone resource object, which a one-opening board does return --
            # iterating that directly would walk its keys and drop the job.
            for record in _records(payload, "data"):
                try:
                    posting = self._to_posting(record, index=index, employer=employer)
                except Exception as exc:
                    log.warning("skipping malformed teamtailor record: %s", exc)
                    continue
                if posting is not None:
                    yield posting

            following = _next_link(payload)
            if not following:
                break
            # ``next`` is documented as absolute but is sometimes served as a
            # path; resolving against the current URL makes both work, where a
            # bare path would raise "unknown url type" inside urllib.
            url = urljoin(url, following)

    def _first_page(
        self, url: str, headers: dict[str, str], params: dict[str, Any] | None
    ) -> Any:
        """Open the walk, retrying once without the side-loading query.

        Asking for ``included`` resources is an enhancement, not a
        requirement: a tenant whose API version rejects the parameter should
        still yield postings (minus location and department) rather than
        failing the whole source.
        """
        try:
            return fetch_json(url, headers=headers, params=params)
        except Exception as exc:
            if not params:
                raise
            log.debug("teamtailor rejected the side-loading query (%s); retrying bare", exc)
            return fetch_json(url, headers=headers)

    def _to_posting(
        self,
        record: Any,
        *,
        index: dict[tuple[str, str], dict[str, Any]],
        employer: str,
    ) -> JobPosting | None:
        record = _require_dict(record, self.kind)
        job_id = _label(record.get("id"))
        if not job_id:
            raise ValueError("teamtailor record has no id")

        attributes = record.get("attributes")
        attributes = attributes if isinstance(attributes, dict) else {}

        status = _label(attributes.get("status"))
        if status and status.lower() in self.HIDDEN_STATUSES:
            log.debug("skipping teamtailor job %s with status %r", job_id, status)
            return None

        title = _first_text(attributes, ("title", "internal-name"))
        remote_status = _label(attributes.get("remote-status"))
        locations = _jsonapi_related(record, index, "locations")
        location_text = "; ".join(locations) or _first_text(
            attributes, ("location", "city")
        )
        departments = _jsonapi_related(record, index, "department")
        department = "; ".join(departments) or _label(attributes.get("department"))

        # ``pitch`` is the short teaser above the body; it is often where the
        # unit or program name appears, so it is kept rather than dropped.
        description = html_to_text(
            "\n".join(
                part
                for part in (_label(attributes.get("pitch")), _label(attributes.get("body")))
                if part
            )
        )
        description = _with_facts(
            description,
            (
                ("Department", department),
                ("Remote status", _humanize(remote_status)),
            ),
        )

        # The career-site link lives in ``attributes`` on some API versions and
        # in the resource's own ``links`` object on others. ``links.self`` is
        # deliberately never used: it is the API resource, not a page a human
        # can open, and a posting with no public URL is dropped downstream
        # rather than published with a dead link.
        record_links = record.get("links")
        record_links = record_links if isinstance(record_links, dict) else {}
        public_url = _first_text(
            attributes, ("careersite-job-url", "careersite-job-apply-url", "url")
        ) or _first_text(record_links, ("careersite-job-url", "careersite-job-apply-url"))

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=job_id,
            url=public_url,
            title=title,
            employer=employer,
            location=location_text,
            description=description,
            posted_at=_first_timestamp(attributes, ("published-at", "created-at")),
            # "hybrid" is not remote work; only a fully remote req counts.
            remote=remote_status.lower() == "fully"
            or looks_remote(location_text, title),
            department=department or None,
            compensation=_first_text(attributes, ("salary-range", "compensation")) or None,
            raw=record,
        )


def _jsonapi_index(payload: dict[str, Any]) -> dict[tuple[str, str], dict[str, Any]]:
    """Index a JSON:API ``included`` array by ``(type, id)``."""
    index: dict[tuple[str, str], dict[str, Any]] = {}
    for item in payload.get("included") or []:
        if not isinstance(item, dict):
            continue
        attributes = item.get("attributes")
        index[(_label(item.get("type")), _label(item.get("id")))] = (
            attributes if isinstance(attributes, dict) else {}
        )
    return index


def _jsonapi_related(
    record: dict[str, Any],
    index: dict[tuple[str, str], dict[str, Any]],
    relationship: str,
) -> list[str]:
    """Names of the side-loaded resources one relationship points at."""
    relationships = record.get("relationships")
    if not isinstance(relationships, dict):
        return []
    entry = relationships.get(relationship)
    if not isinstance(entry, dict):
        return []
    data = entry.get("data")
    items = data if isinstance(data, list) else [data]

    names: list[str] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        attributes = index.get((_label(item.get("type")), _label(item.get("id"))))
        if not attributes:
            continue
        name = _first_text(attributes, ("name", "title", "headline", "city"))
        if name and name not in names:
            names.append(name)
    return names


def _next_link(payload: dict[str, Any]) -> str:
    """The ``links.next`` URL, tolerating both the string and object forms."""
    links = payload.get("links")
    if not isinstance(links, dict):
        return ""
    nxt = links.get("next")
    if isinstance(nxt, dict):
        nxt = nxt.get("href")
    return nxt.strip() if isinstance(nxt, str) else ""


class PersonioSource(Source):
    """Personio's XML job feed.

    Docs: https://developer.personio.de/docs/job-xml-feed -- served at
    ``https://{company}.jobs.personio.de/xml``.

    Personio splits a posting into named sections (``Your mission``, ``Your
    profile``, ``Why us?``), each its own ``jobDescription`` element. Only
    reading the first one would throw away exactly the section that lists
    certifications and clearance, so every section is concatenated, keeping
    its heading.

    Options: ``company`` (required), ``employer``.
    """

    kind = "personio"

    def fetch(self) -> Iterable[JobPosting]:
        company = str(self.require("company")).strip().strip("/")
        employer = self.options.get("employer") or company
        base_url = f"https://{company}.jobs.personio.de"

        body = fetch(f"{base_url}/xml", headers={"Accept": "application/xml"})
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise RuntimeError(f"{base_url}/xml is not valid XML: {exc}") from exc

        for position in root.iter("position"):
            try:
                posting = self._to_posting(position, base_url=base_url, employer=employer)
            except Exception as exc:
                log.warning("skipping malformed personio position: %s", exc)
                continue
            if posting is not None:
                yield posting

    def _to_posting(
        self, position: ET.Element, *, base_url: str, employer: str
    ) -> JobPosting:
        job_id = _xml_text(position.find("id"))
        title = _xml_text(position.find("name"))
        if not job_id or not title:
            raise ValueError("personio position is missing id or name")

        office = _xml_text(position.find("office"))
        department = _xml_text(position.find("department"))
        employment = _xml_text(position.find("employmentType"))
        schedule = _xml_text(position.find("schedule"))
        seniority = _xml_text(position.find("seniority"))

        sections: list[str] = []
        raw_sections: list[dict[str, str]] = []
        for block in position.iter("jobDescription"):
            heading = _xml_text(block.find("name"))
            value = html_to_text(_xml_text(block.find("value")))
            raw_sections.append({"name": heading, "value": value})
            if not value:
                continue
            sections.append(f"{heading}\n{value}" if heading else value)

        description = _with_facts(
            "\n\n".join(sections),
            (
                ("Department", department),
                ("Employment type", _humanize(employment)),
                ("Schedule", _humanize(schedule)),
                ("Seniority", _humanize(seniority)),
            ),
        )

        raw: dict[str, Any] = {
            child.tag: _xml_text(child)
            for child in position
            if child.tag != "jobDescriptions"
        }
        raw["jobDescriptions"] = raw_sections

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=job_id,
            url=f"{base_url}/job/{quote(job_id, safe='')}",
            title=title,
            employer=employer,
            location=office,
            description=description,
            posted_at=parse_timestamp(_xml_text(position.find("createdAt"))),
            remote=looks_remote(office, title, employment, schedule),
            department=department or None,
            raw=raw,
        )


class RipplingSource(Source):
    """Rippling's ATS job-board API.

    ``https://api.rippling.com/platform/api/ats/v1/board/{token}/jobs`` is the
    feed behind a Rippling-hosted board, and it ships the full description
    HTML inline, so one request covers a whole employer.

    Options: ``board_token`` (required), ``employer``.
    """

    kind = "rippling"

    def fetch(self) -> Iterable[JobPosting]:
        token = str(self.require("board_token")).strip().strip("/")
        employer = self.options.get("employer") or token

        payload = fetch_json(
            "https://api.rippling.com/platform/api/ats/v1/board/"
            f"{quote(token, safe='')}/jobs",
            headers=JSON_HEADERS,
        )
        for record in _records(payload, "jobs", "results", "data"):
            try:
                posting = self._to_posting(record, token=token, employer=employer)
            except Exception as exc:
                log.warning("skipping malformed rippling record: %s", exc)
                continue
            if posting is not None:
                yield posting

    def _to_posting(self, record: Any, *, token: str, employer: str) -> JobPosting:
        record = _require_dict(record, self.kind)
        job_id = _first_text(record, ("uuid", "id"))
        if not job_id:
            raise ValueError("rippling record has no uuid")

        title = _first_text(record, ("name", "title"))
        location_text = _label(record.get("workLocation") or record.get("workLocations"))
        department = _label(record.get("department"))
        employment = _humanize(_label(record.get("employmentType")))
        location_type = _humanize(_label(record.get("workLocationType")))

        description = _with_facts(
            html_to_text(_first_text(record, ("descriptionHtml", "description"))),
            (
                ("Department", department),
                ("Employment type", employment),
                ("Work location type", location_type),
            ),
        )

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=job_id,
            url=_label(record.get("url"))
            or f"https://ats.rippling.com/{quote(token, safe='')}/jobs/{quote(job_id, safe='')}",
            title=title,
            employer=employer,
            location=location_text,
            description=description,
            posted_at=_first_timestamp(
                record, ("publishedAt", "postedAt", "createdAt", "updatedAt")
            ),
            remote=looks_remote(location_text, title, location_type),
            department=department or None,
            compensation=_first_text(
                record, ("compensationDescription", "salaryDescription", "compensation")
            )
            or None,
            raw=record,
        )


ATS_EXTRA_SOURCES: tuple[type[Source], ...] = (
    BambooHRSource,
    BreezySource,
    JazzHRSource,
    TeamtailorSource,
    PersonioSource,
    RipplingSource,
)
