"""Phenom People adapter -- the career-site platform behind Serco's H2F board.

Serco runs careers.serco-na.com on Phenom People, and Serco holds the $247M
Army H2F contract -- the largest single concentration of tactical strength and
conditioning hiring in the country. Many other large employers run the same
"CareerConnect" front end on their own branded hosts.

The search SPA on those sites talks to a public, no-auth JSON widget endpoint
on the branded host itself:

    POST {origin}/widgets
    Content-Type: application/json
    {"lang": "en_global", "country": "global", "ddoKey": "refineSearch",
     "pageName": "search-results", "siteType": "external", "jobs": true,
     "counts": true, "from": 0, "size": 100, "keywords": "",
     "selected_fields": {...facet filters...}, "all_fields": [...], ...}

    -> {"refineSearch": {"status": 200, "totalHits": N,
          "data": {"jobs": [{"jobId": "98098", "title": ..., "city": ...,
            "state": ..., "country": ..., "location": ...,
            "postedDate": "...ISO instant...", "applyUrl": ...}]}}}

``from`` is a 0-based offset; ``size`` maxes out at 100 per page. The public
job page the SPA links to is ``{origin}/{url_prefix}/job/{jobId}/{slug}`` --
the slug is cosmetic (Phenom keys on jobId), so it is rebuilt by slugifying
the title. ``applyUrl`` points at the downstream ATS behind the career site,
NOT the public listing, so it is never used as the job URL.

Endpoint recipe ported from santifer/career-ops providers/phenom.mjs (MIT).

Honesty notes: the widget search response carries no posting body, so the
description here is assembled only from the fields the response does state
(title, location, category) and ``raw`` records that it is a search-result
summary. ``postedDate`` absent means ``posted_at`` is ``None`` -- never a
guessed date. v1 deliberately does not fetch the job page for the full text;
that keeps the adapter simple and CI-verifiable.
"""

from __future__ import annotations

import json
import logging
import re
import time
import unicodedata
import urllib.parse
from typing import Any, Iterable

from ..http import FetchError, post_json
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

log = logging.getLogger(__name__)

MAX_PAGE_SIZE = 100
"""The most jobs the widget serves per page (verified upstream in career-ops)."""

_TAG = re.compile(r"<[^>]*>")
_WS = re.compile(r"\s+")
_NON_ALNUM = re.compile(r"[^a-zA-Z0-9]+")


def slugify(title: str) -> str:
    """Build the cosmetic job-page slug the way Phenom does.

    NFKD-decompose, strip combining marks (so ``ü`` becomes ``u`` rather
    than a hyphen), collapse every other non-alphanumeric run to a single
    hyphen, and trim. Case is preserved -- Phenom's own slugs keep it.
    Ported from santifer/career-ops providers/phenom.mjs (MIT).
    """
    decomposed = unicodedata.normalize("NFKD", str(title))
    # U+0300..U+036F, the same combining-diacritics range the upstream strips.
    stripped = "".join(ch for ch in decomposed if not ("\u0300" <= ch <= "\u036f"))
    return _NON_ALNUM.sub("-", stripped).strip("-") or "job"


def _clean(value: Any) -> str:
    """Strip markup and collapse whitespace in a scalar response field."""
    if value is None or isinstance(value, bool):
        return ""
    text = value if isinstance(value, str) else str(value)
    return _WS.sub(" ", _TAG.sub(" ", text)).strip()


def _job_location(job: dict[str, Any]) -> str:
    """Prefer the widget's flat ``location`` string, else assemble one.

    The response states location several ways; the explicit ``location`` (or
    ``cityStateCountry``/``cityState``) wins, else city/state/country are
    joined -- deduplicated, because tenants repeat values across those fields.
    Ported from santifer/career-ops providers/phenom.mjs (MIT).
    """
    for key in ("location", "cityStateCountry", "cityState"):
        direct = _clean(job.get(key))
        if direct:
            return direct
    parts: list[str] = []
    for key in ("city", "state", "country"):
        text = _clean(job.get(key))
        if text and text not in parts:
            parts.append(text)
    return ", ".join(parts)


def _int_option(options: dict[str, Any], key: str, default: int) -> int:
    """Read an int option, falling back to the default on junk.

    Config is hand-edited TOML. One mistyped value must degrade to the default
    rather than take the largest H2F employer out of the nightly run.
    """
    value = options.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        log.warning("phenom: ignoring non-numeric %s=%r, using %r", key, value, default)
        return default


def _float_option(options: dict[str, Any], key: str, default: float) -> float:
    value = options.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        log.warning("phenom: ignoring non-numeric %s=%r, using %r", key, value, default)
        return default


def _decode(body: Any) -> dict[str, Any]:
    """Parse a /widgets response body.

    ``http.post_json`` returns the raw bytes rather than parsed JSON, so the
    decoding happens here. An already-parsed mapping is passed through so the
    helper stays honest about what it received.
    """
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", "replace")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError as exc:
            raise FetchError(f"phenom /widgets returned non-JSON body: {exc}") from exc
    return body if isinstance(body, dict) else {}


class PhenomSource(Source):
    """One Phenom People career site, addressed by its branded origin.

    ``url`` is the careers-site origin (a full careers URL is fine; only the
    scheme and host are used): ``https://careers.serco-na.com``. The widget
    body and public-URL prefix are tenant configuration:

    - ``lang`` / ``country``: widget locale and scope (``en_global``/``global``)
    - ``url_prefix``: public job-page path prefix (default ``global/en``)
    - ``keywords``: list of server-side searches, deduped by jobId
    - ``selected_fields``: facet filter dict, human-readable values
      (e.g. ``{"country": ["United States of America"]}``)
    """

    kind = "phenom"

    def fetch(self) -> Iterable[JobPosting]:
        origin = self._origin()
        url_prefix = str(self.options.get("url_prefix") or "global/en").strip("/")
        employer = self.options.get("employer") or self.name
        lang = str(self.options.get("lang") or "en_global")
        country = str(self.options.get("country") or "global")
        selected_fields = self.options.get("selected_fields")
        if not isinstance(selected_fields, dict):
            if selected_fields is not None:
                log.warning(
                    "phenom: selected_fields=%r is not a dict, ignoring", selected_fields
                )
            selected_fields = {}
        size = min(MAX_PAGE_SIZE, max(1, _int_option(self.options, "size", MAX_PAGE_SIZE)))
        max_pages = max(1, _int_option(self.options, "max_pages", 5))
        delay = max(0.0, _float_option(self.options, "delay_seconds", 0.5))

        collected = self._collect(
            origin=origin,
            keywords=self._keywords(),
            lang=lang,
            country=country,
            selected_fields=selected_fields,
            size=size,
            max_pages=max_pages,
            delay=delay,
        )

        for job_id, job in collected.items():
            try:
                yield self._to_posting(
                    job_id, job, employer=employer, origin=origin, url_prefix=url_prefix
                )
            except Exception as exc:  # pragma: no cover - defensive
                # One unusable record must never cost us the rest of the board.
                log.warning("skipping malformed phenom posting %s: %s", job_id, exc)

    def _origin(self) -> str:
        """Reduce the configured URL to its origin (scheme + host)."""
        raw = str(self.require("url")).strip()
        parts = urllib.parse.urlsplit(raw)
        if parts.scheme not in ("http", "https") or not parts.netloc:
            raise ValueError(
                f"source '{self.name}' ({self.kind}) cannot resolve an origin from url={raw!r}"
            )
        return f"{parts.scheme}://{parts.netloc}"

    def _keywords(self) -> list[str]:
        """Configured search keywords; the default is one unfiltered search.

        The widget treats ``keywords: ""`` as "everything", which is the right
        default for a board like Serco's where the local classifier does the
        precision work.
        """
        configured = self.options.get("keywords")
        if configured is None:
            return [""]
        if isinstance(configured, str):
            return [configured]
        if not isinstance(configured, (list, tuple, set, frozenset)):
            log.warning("phenom: keywords=%r is not a list, searching unfiltered", configured)
            return [""]

        terms: list[str] = []
        for term in configured:
            # ``None`` in the list is a config slip, not a request to search
            # for the literal string "None".
            if term is None or isinstance(term, bool):
                continue
            text = term if isinstance(term, str) else str(term)
            # A repeated keyword would double the request count for no new jobs.
            if text not in terms:
                terms.append(text)
        return terms or [""]

    def _collect(
        self,
        *,
        origin: str,
        keywords: list[str],
        lang: str,
        country: str,
        selected_fields: dict[str, Any],
        size: int,
        max_pages: int,
        delay: float,
    ) -> dict[str, dict[str, Any]]:
        """Run every keyword search and dedupe by ``jobId``.

        Overlapping keywords are the norm -- "human performance" and "strength
        and conditioning" both hit the same H2F req. Insertion order is
        preserved so earlier (more relevant) keywords win the slot.
        """
        collected: dict[str, dict[str, Any]] = {}
        failures: list[Exception] = []
        requests_made = 0

        for keyword in keywords:
            # Loop detection is per keyword: a page with no ids that are new
            # *to this keyword's own scan* means the server ignored ``from``.
            # (Global ``collected`` cannot serve here -- a later keyword may
            # legitimately return a first page of already-seen jobs and still
            # have fresh ones behind it.)
            keyword_seen: set[str] = set()
            for page in range(max_pages):
                if delay and requests_made:
                    time.sleep(delay)
                requests_made += 1
                try:
                    refine = self._search(
                        origin=origin,
                        keyword=keyword,
                        offset=page * size,
                        size=size,
                        lang=lang,
                        country=country,
                        selected_fields=selected_fields,
                    )
                except Exception as exc:
                    # A failed page costs this keyword the rest of its pages,
                    # but never the keywords around it -- and never the pages
                    # already collected.
                    log.warning(
                        "phenom search failed for %r at offset %d: %s",
                        keyword,
                        page * size,
                        exc,
                    )
                    failures.append(exc)
                    break

                total = refine.get("totalHits")
                if isinstance(total, bool) or not isinstance(total, int):
                    total = None
                data = refine.get("data")
                rows = data.get("jobs") if isinstance(data, dict) else None
                if not isinstance(rows, list) or not rows:
                    break

                fresh = 0
                for job in rows:
                    if not isinstance(job, dict):
                        log.debug("skipping non-dict phenom record: %r", job)
                        continue
                    raw_id = job.get("jobId")
                    job_id = "" if raw_id is None else str(raw_id).strip()
                    # No jobId means no stable dedupe key and no public URL;
                    # no title means no meaningful listing. Skip, don't abort.
                    if not job_id or not _clean(job.get("title")):
                        log.debug("skipping phenom record without jobId/title: %r", job)
                        continue
                    if job_id not in keyword_seen:
                        keyword_seen.add(job_id)
                        fresh += 1
                    collected.setdefault(job_id, job)

                if fresh == 0:
                    break  # server ignored ``from`` (or the page was all junk)
                if total is not None and (page + 1) * size >= total:
                    break

        if not collected and failures:
            # Every search either errored or found nothing, and at least one
            # errored. That is a dead host or a broken config, so surface it
            # instead of reporting a zero-job run as a success.
            raise failures[0]

        return collected

    def _search(
        self,
        *,
        origin: str,
        keyword: str,
        offset: int,
        size: int,
        lang: str,
        country: str,
        selected_fields: dict[str, Any],
    ) -> dict[str, Any]:
        """POST one refineSearch page and return the ``refineSearch`` block.

        Body ported field-for-field from santifer/career-ops
        providers/phenom.mjs (MIT) -- this is the exact payload the search SPA
        sends, which is what makes the no-auth endpoint answer.
        """
        body = post_json(
            f"{origin}/widgets",
            {
                "lang": lang,
                "deviceType": "desktop",
                "country": country,
                "pageName": "search-results",
                "ddoKey": "refineSearch",
                "sortBy": "",
                "subsearch": "",
                "from": offset,
                "jobs": True,
                "counts": True,
                "all_fields": ["category", "country", "city"],
                "size": size,
                "clearAll": False,
                "jdsource": "facets",
                "isSliderEnable": False,
                "pageId": "page10",
                "siteType": "external",
                "keywords": keyword,
                "global": country == "global",
                "selected_fields": selected_fields,
                "locationData": {},
            },
            headers={"Accept": "application/json"},
        )
        payload = _decode(body)
        refine = payload.get("refineSearch")
        if not isinstance(refine, dict):
            raise FetchError(f"phenom {origin}/widgets response has no refineSearch block")
        status = refine.get("status")
        if status is not None and status != 200:
            raise FetchError(f"phenom {origin}/widgets reported refineSearch status {status}")
        return refine

    def _to_posting(
        self,
        job_id: str,
        job: dict[str, Any],
        *,
        employer: str,
        origin: str,
        url_prefix: str,
    ) -> JobPosting:
        title = _clean(job.get("title"))
        location = _job_location(job)
        category = _clean(job.get("category"))

        # The widget search response has no posting body. The description is
        # therefore only what the response actually states -- title, location,
        # category -- and ``raw`` records that limitation. It is never padded
        # with text the API did not return.
        parts = [title, location]
        if category:
            parts.append(f"Job category: {category}.")
        description = html_to_text(" ".join(part for part in parts if part))

        return JobPosting(
            source=f"{self.kind}:{self.name}",
            source_id=job_id,
            # The public listing lives on the branded host. applyUrl points at
            # the downstream ATS and is deliberately never used here.
            url=(
                f"{origin}/{url_prefix}/job/"
                f"{urllib.parse.quote(job_id, safe='')}/{slugify(title)}"
            ),
            title=title,
            employer=employer,
            location=location,
            description=description,
            posted_at=parse_timestamp(job.get("postedDate") or job.get("dateCreated")),
            remote=looks_remote(location, title),
            department=category or None,
            raw={
                "job": job,
                "description_note": (
                    "search-result summary only; the /widgets response does not "
                    "include the posting body"
                ),
            },
        )


PHENOM_SOURCES: tuple[type[Source], ...] = (PhenomSource,)
