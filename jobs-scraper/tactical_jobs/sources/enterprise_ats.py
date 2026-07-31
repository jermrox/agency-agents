"""Adapters for the enterprise ATS vendors defense primes actually run.

iCIMS, SAP SuccessFactors, Cornerstone OnDemand, Oracle Cloud Recruiting,
Jobvite, and Radancy host the career sites of the government-contractor tier
this project cares most about, and none of them had an adapter until now.
The endpoint knowledge here is ported from santifer/career-ops (MIT), which
ships live-verified recipes for each vendor; every class below names the
exact ``.mjs`` file it was ported from.

All six recipes are public and keyless: no login, no session cookies, no API
key, no JavaScript rendering. Two of them (iCIMS, Radancy) read server-
rendered HTML rather than JSON, and SuccessFactors' older RMK variant reads
an HTML fragment endpoint -- that is genuinely how those vendors publish
their boards, so the parsing lives here rather than being replaced with an
invented "cleaner" endpoint. CSOD's search API wants a bearer token, but the
token is an *anonymous* JWT embedded in the public careers page itself; the
recipe extracts it with one extra GET and no credential of any sort.

Two recipes (iCIMS, Oracle) send a browser-like User-Agent because the
career-ops project verified live that vendor WAFs serve interstitials to
unfamiliar agents. That header is part of the ported recipe, and it is the
one place these adapters diverge from :data:`tactical_jobs.http.USER_AGENT`.

Honesty rules observed throughout: a field the response does not state is
emitted as ``None``/``""`` -- list pages without dates yield undated
postings, list pages without descriptions yield empty descriptions, and the
employer always comes from configuration, never from parsing a string.
"""

from __future__ import annotations

import html
import json
import logging
import re
import time
from datetime import datetime, timezone
from typing import Any, Iterable
from urllib.parse import parse_qs, quote, unquote, urlencode, urljoin, urlparse

from ..http import FetchError, fetch, fetch_json, post_json
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

log = logging.getLogger(__name__)

# Shared browser-like UA, ported from career-ops providers/_http.mjs
# (BROWSER_LIKE_USER_AGENT) and providers/oraclecloud.mjs (BROWSER_UA).
# Sent only where the recipe documents a WAF that blocks unfamiliar agents.
_BROWSER_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
)


# ---------------------------------------------------------------------------
# small shared helpers
# ---------------------------------------------------------------------------


def _int_option(options: dict[str, Any], key: str, default: int) -> int:
    """Read an int option, falling back to the default on junk.

    Config is hand-edited TOML; one mistyped value must degrade to the
    default rather than take a whole employer's board out of the run.
    """
    value = options.get(key, default)
    try:
        return int(value)
    except (TypeError, ValueError):
        log.warning("enterprise_ats: ignoring non-numeric %s=%r, using %r", key, value, default)
        return default


def _float_option(options: dict[str, Any], key: str, default: float) -> float:
    value = options.get(key, default)
    try:
        return float(value)
    except (TypeError, ValueError):
        log.warning("enterprise_ats: ignoring non-numeric %s=%r, using %r", key, value, default)
        return default


def _strip_tags(raw: Any) -> str:
    """Tags to spaces, entities decoded, whitespace collapsed.

    Mirrors the ``clean()`` helper career-ops uses for titles and locations:
    strip markup first, decode entities second (so a literal ``&lt;b&gt;`` in
    the text stays visible as text), collapse all whitespace last.
    """
    if raw is None:
        return ""
    text = re.sub(r"<[^>]*>", " ", str(raw))
    return re.sub(r"\s+", " ", html.unescape(text)).strip()


def _fetch_text(url: str, headers: dict[str, str] | None = None) -> str:
    """GET a URL and decode the body as text."""
    return fetch(url, headers=headers).decode("utf-8", "replace")


def _post_json_dict(url: str, payload: Any, headers: dict[str, str] | None = None) -> dict[str, Any]:
    """POST JSON and parse the byte response ``post_json`` hands back."""
    body: Any = post_json(url, payload, headers=headers)
    if isinstance(body, (bytes, bytearray)):
        body = body.decode("utf-8", "replace")
    if isinstance(body, str):
        try:
            body = json.loads(body)
        except json.JSONDecodeError as exc:
            raise FetchError(f"POST {url} returned non-JSON body: {exc}") from exc
    return body if isinstance(body, dict) else {}


def _origin(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


# ---------------------------------------------------------------------------
# iCIMS
# ---------------------------------------------------------------------------

# Endpoint recipe ported from santifer/career-ops providers/icims.mjs (MIT).

_ICIMS_MAX_PAGES = 30  # ~20 postings/page; larger tenants are rare on iCIMS
_ICIMS_HEADERS = {
    # career-ops verified live that iCIMS serves 200 to a browser-like UA
    # while unfamiliar agents risk WAF interstitials.
    "User-Agent": _BROWSER_UA,
    "Accept-Language": "en-US,en;q=0.9",
}

_ICIMS_HREF = re.compile(r'href="([^"]*/jobs/\d+/[^"/]+/job[^"]*)"')
_ICIMS_TITLE = re.compile(r"<h3\b[^>]*>\s*(.*?)</h3>", re.S)
# `field-label` must be a whole token in a themed class list; the lookarounds
# keep `field-label-inline` from counting as a match (see icims.mjs).
_ICIMS_LOCATION = re.compile(
    r'<span\b[^>]*class=["\'][^"\']*(?<![\w-])field-label(?![\w-])[^"\']*["\'][^>]*>'
    r"\s*Location\s*</span>\s*<span\b[^>]*>\s*(.*?)</span>",
    re.S,
)
# `type` is not reliably the first script attribute (CSP nonces come first on
# some tenants), so allow attributes before it -- see icims.mjs enrichDate.
_ICIMS_LDJSON = re.compile(
    r'<script\b[^>]*?(?<![\w-])type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
    re.I | re.S,
)


def _icims_origin(raw: str) -> str:
    """Validate and normalize a hosted-portal URL to its origin."""
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not host.endswith(".icims.com"):
        raise ValueError(f"icims: careers_url must be an https *.icims.com portal, got {raw!r}")
    return f"https://{parsed.netloc}"


def _parse_icims_search_page(page_html: str, origin: str) -> list[dict[str, Any]]:
    """Parse one iCIMS search-results page into raw rows.

    Postings are ``<li class="iCIMS_JobCardItem">`` cards: posting URL in an
    href of shape ``/jobs/{id}/{slug}/job`` (query stripped), title in the
    card's ``<h3>``, location in the span after the "Location" field label.
    Cards whose href resolves off-origin are dropped.
    """
    rows: list[dict[str, Any]] = []
    for card in page_html.split("iCIMS_JobCardItem")[1:]:
        href = _ICIMS_HREF.search(card)
        if not href:
            continue
        # Resolve relative hrefs against the portal origin; some tenants emit
        # them, and dropping them all would silently return zero jobs.
        resolved = urlparse(urljoin(f"{origin}/", html.unescape(href.group(1))))
        if f"{resolved.scheme}://{resolved.netloc}" != origin:
            continue
        title = _ICIMS_TITLE.search(card)
        if not title or not _strip_tags(title.group(1)):
            continue
        location = _ICIMS_LOCATION.search(card)
        job_id = re.search(r"/jobs/(\d+)/", resolved.path)
        rows.append(
            {
                "id": job_id.group(1) if job_id else resolved.path,
                "title": _strip_tags(title.group(1)),
                # Query stripped: the tracking params vary per render and
                # would break dedupe.
                "url": f"{origin}{resolved.path}",
                "location": _strip_tags(location.group(1)) if location else "",
            }
        )
    return rows


def _pick_date_posted(nodes: list[Any]) -> Any:
    """datePosted of the first JSON-LD JobPosting node, else the first node
    carrying a datePosted at all (icims.mjs pickDatePosted)."""
    fallback = None
    for node in nodes:
        if not isinstance(node, dict):
            continue
        date = node.get("datePosted")
        if not date:
            continue
        node_type = node.get("@type")
        if node_type == "JobPosting" or (isinstance(node_type, list) and "JobPosting" in node_type):
            return date
        if fallback is None:
            fallback = date
    return fallback


class ICIMSSource(Source):
    """iCIMS hosted portals (``careers-<tenant>.icims.com``).

    Endpoint recipe ported from santifer/career-ops providers/icims.mjs (MIT).

    The list pages carry title/location/URL but **no posted date and no
    description**; both are emitted empty rather than guessed. Dates live
    only in each posting's detail-page JSON-LD, so ``detail_limit`` (default
    0) bounds an optional per-posting date-enrichment fetch -- the same
    filtered-candidates-only policy career-ops applies to its enrichDate
    hook.
    """

    kind = "icims"

    def fetch(self) -> Iterable[JobPosting]:
        origin = _icims_origin(str(self.require("careers_url")))
        employer = str(self.options.get("employer") or self.name)
        max_pages = min(max(1, _int_option(self.options, "max_pages", _ICIMS_MAX_PAGES)), _ICIMS_MAX_PAGES)
        detail_limit = max(0, _int_option(self.options, "detail_limit", 0))
        delay = max(0.0, _float_option(self.options, "delay_seconds", 0.0))

        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        prev_first_url: str | None = None
        reached_end = False
        for page in range(max_pages):
            if delay and page:
                time.sleep(delay)
            # in_iframe=1 selects the lighter portal-only markup; pr is the
            # 0-based page number.
            url = f"{origin}/jobs/search?ss=1&pr={page}&in_iframe=1"
            try:
                page_html = _fetch_text(url, headers=_ICIMS_HEADERS)
            except Exception:
                if page == 0:
                    raise  # a dead portal must not look like an empty board
                log.warning("icims: page %d failed for %s; keeping %d rows", page, self.name, len(rows))
                break
            page_rows = _parse_icims_search_page(page_html, origin)
            if not page_rows:
                reached_end = True  # past the last page
                break
            # Some tenants serve the last real page again for an out-of-range
            # pr -- a repeated first URL means we're looping.
            if page_rows[0]["url"] == prev_first_url:
                reached_end = True
                break
            prev_first_url = page_rows[0]["url"]
            for row in page_rows:
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                rows.append(row)
        if not reached_end and rows:
            log.warning("icims: %s stopped at the %d-page cap; later postings not fetched", self.name, max_pages)

        for index, row in enumerate(rows):
            posted_at = None
            if index < detail_limit:
                if delay:
                    time.sleep(delay)
                posted_at = self._detail_date(row["url"])
            try:
                yield JobPosting(
                    source=f"{self.kind}:{self.name}",
                    source_id=str(row["id"]),
                    url=row["url"],
                    title=row["title"],
                    employer=employer,
                    location=row["location"],
                    # The list page states no description; emit none.
                    description="",
                    posted_at=posted_at,
                    remote=looks_remote(row["location"], row["title"]),
                    raw=row,
                )
            except Exception as exc:  # pragma: no cover - defensive
                log.warning("skipping malformed icims posting %s: %s", row.get("url"), exc)

    def _detail_date(self, url: str) -> datetime | None:
        """Posted date from the detail page's JSON-LD, or None on any failure."""
        sep = "&" if "?" in url else "?"
        try:
            page_html = _fetch_text(f"{url}{sep}in_iframe=1", headers=_ICIMS_HEADERS)
        except Exception as exc:
            log.debug("icims: date enrichment failed for %s: %s", url, exc)
            return None
        nodes: list[Any] = []
        for match in _ICIMS_LDJSON.finditer(page_html):
            try:
                data = json.loads(match.group(1))
            except json.JSONDecodeError:
                continue
            # Flatten the JSON-LD shapes iCIMS emits: a bare JobPosting
            # object, an array of nodes, or a graph document.
            if isinstance(data, list):
                nodes.extend(data)
            elif isinstance(data, dict) and isinstance(data.get("@graph"), list):
                nodes.extend(data["@graph"])
            else:
                nodes.append(data)
        return parse_timestamp(_pick_date_posted(nodes))


# ---------------------------------------------------------------------------
# SAP SuccessFactors (RMK tile boards + CSB JSON API)
# ---------------------------------------------------------------------------

# Endpoint recipe ported from santifer/career-ops providers/successfactors.mjs
# (MIT).

_SF_RMK_MAX_PAGES = 40  # fixed safety cap on the tile pagination (per recipe)
_SF_MAX_JOBS = 1000  # cap total postings pulled per site (both strategies)
_CSB_PAGE_SIZE = 10  # fixed by the /services/recruiting/v1/jobs API
_CSB_MAX_PAGES_PER_LOCALE = 100
_CSB_MAX_LOCALES = 16
_CSB_DEFAULT_LOCALES = ("de_DE", "en_US")
_CSB_LOCALE_PRIORITY = ("de_DE", "en_US", "en_GB", "en_EN")

_SF_TILE = re.compile(r'<li class="job-tile job-id-(\d+)\b.*?</li>', re.S)
_SF_DATA_URL = re.compile(r'data-url="([^"]+)"')
_SF_TITLE = re.compile(r'class="jobTitle-link[^"]*"[^>]*>(.*?)</a>', re.S)
# Anchor on the -section-city-value div; the sibling label span references the
# same id via aria-describedby, so a looser match would swallow the label too.
_SF_CITY = re.compile(r'id="[^"]*-section-city-value">(.*?)</div>', re.S)
_SF_LOCALE = re.compile(r"locale=([a-z]{2}_[A-Z]{2})\b")


def _sf_config(raw: str) -> dict[str, str]:
    """Resolve the RMK/CSB endpoints from a careers URL.

    Preserves a brand/tenant path prefix (shared RMK instances disambiguate
    acquired brands with a path segment) while stripping a trailing known
    endpoint segment so all spellings collapse to one brand-scoped base.
    """
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"successfactors: cannot resolve origin from careers_url {raw!r}")
    path = re.sub(
        r"/(?:search|tile-search-results|services/recruiting/v1/jobs)/?$", "", parsed.path, flags=re.I
    )
    path = re.sub(r"/+$", "", path)
    origin = f"{parsed.scheme}://{parsed.netloc}"
    base = origin + path
    return {
        "origin": origin,
        "base": base,
        "tile_api": f"{base}/tile-search-results/",
        # RMK tile data-url paths already carry the brand segment, so job
        # URLs resolve against the bare origin (see successfactors.mjs).
        "job_base": origin,
        "jobs_api": f"{base}/services/recruiting/v1/jobs",
        "search_page": f"{base}/search/",
    }


def _city_from_slug(data_url: str, title: str) -> str:
    """Recover the city RMK encodes as the leading job-path slug segment.

    RMK paths are ``/job/{City-Words}-{Title-Words}-{reqCode}/{id}/``. When
    the tenant renders no dedicated city field, the city is still *stated* in
    the path -- this strips the title (anchored on its first two words) off
    the slug to expose it. Anything ambiguous yields "" rather than a guess.
    """
    path = unquote(data_url)
    match = re.search(r"/job/([^/]+)/", path)
    if not match:
        return ""
    slug = match.group(1).lower()
    words = re.findall(r"[^\W_]+", title.lower())
    if not words:
        return ""
    # Allow ANY run of non-alphanumerics between the two anchor words: in the
    # slug they may be joined by "-", "-amp-" (a decoded "&"), or several
    # hyphens, none of which survive the title's word split.
    anchor = r"[\W_]+".join(re.escape(word) for word in words[:2])
    hit = re.search(anchor, slug)
    if not hit or hit.start() <= 0:
        return ""
    city_words = [word for word in re.split(r"[\W_]+", slug[: hit.start()]) if word]
    return " ".join(word[:1].upper() + word[1:] for word in city_words)


def _parse_sf_tiles(fragment_html: str, job_base: str) -> list[dict[str, Any]]:
    """Parse one RMK tile fragment into raw rows."""
    rows: list[dict[str, Any]] = []
    for match in _SF_TILE.finditer(fragment_html):
        job_id = match.group(1)
        block = match.group(0)
        url_match = _SF_DATA_URL.search(block)
        if not url_match:
            continue
        title_match = _SF_TITLE.search(block)
        title = _strip_tags(title_match.group(1)) if title_match else ""
        if not title:
            continue
        # data-url is an HTML attribute, so "&" arrives as &amp;. Decode
        # entities but not percent-encoding before URL building and slug
        # parsing.
        path = html.unescape(url_match.group(1))
        city_match = _SF_CITY.search(block)
        city = _strip_tags(city_match.group(1)) if city_match else _city_from_slug(path, title)
        if re.match(r"^https?://", path, re.I):
            url = path
        else:
            url = job_base + (path if path.startswith("/") else f"/{path}")
        rows.append({"id": job_id, "title": title, "url": url, "location": city, "posted_at": None, "raw": {"data_url": path}})
    return rows


def _extract_locales(page_html: str) -> list[str]:
    """The tenant's advertised locales from its /search/ language switcher."""
    found = sorted(set(_SF_LOCALE.findall(page_html)))

    def priority(locale: str) -> int:
        try:
            return _CSB_LOCALE_PRIORITY.index(locale)
        except ValueError:
            return len(_CSB_LOCALE_PRIORITY)

    found.sort(key=lambda locale: (priority(locale), locale))
    return found[:_CSB_MAX_LOCALES]


def _parse_csb_date(raw: Any) -> datetime | None:
    """CSB short dates: US ``M/D/YY`` with slashes, European ``D.M.YY`` with
    dots. A 2-digit year is 20YY; anything unexpected yields None."""
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{2,4})", text)
    if match:
        month, day, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    else:
        match = re.fullmatch(r"(\d{1,2})\.(\d{1,2})\.(\d{2,4})", text)
        if not match:
            return None
        day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
    if year < 100:
        year += 2000
    try:
        return datetime(year, month, day, tzinfo=timezone.utc)
    except ValueError:
        return None


def _csb_location(raw: Any) -> str:
    """jobLocationShort entries like ``"Karlovy Vary, CZE, 36004<br/>"`` --
    strip markup, drop empties, join multiple work locations with " / "."""
    parts = raw if isinstance(raw, list) else [] if raw is None else [raw]
    cleaned: list[str] = []
    for part in parts:
        text = _strip_tags(part)
        if text and text not in cleaned:
            cleaned.append(text)
    return " / ".join(cleaned)


def _parse_csb_jobs(payload: dict[str, Any], cfg: dict[str, str], locale: str) -> list[dict[str, Any]]:
    """Map one CSB jobs-API response page to raw rows.

    Records nest the useful fields under ``.response``; a record without an
    id or a title is skipped (no stable dedup key, no meaningful listing).
    """
    results = payload.get("jobSearchResult")
    rows: list[dict[str, Any]] = []
    for item in results if isinstance(results, list) else []:
        record = item.get("response") if isinstance(item, dict) else None
        if not isinstance(record, dict):
            continue
        job_id = str(record["id"]) if record.get("id") is not None else ""
        title = _strip_tags(record.get("unifiedStandardTitle") or record.get("jobTitle") or "")
        if not job_id or not title:
            continue
        # The slug is cosmetic (the server keys on the {id}-{locale} tail)
        # but tenants render it inconsistently: decode entities, then drop
        # URL-structural chars a raw entity would inject into the path.
        slug = html.unescape(str(record.get("unifiedUrlTitle") or record.get("urlTitle") or "job"))
        slug = re.sub(r"-{2,}", "-", re.sub(r"[?#&]+", "-", slug))
        rows.append(
            {
                "id": job_id,
                "title": title,
                "url": f"{cfg['base']}/job/{slug}/{job_id}-{locale}",
                "location": _csb_location(record.get("jobLocationShort")),
                "posted_at": _parse_csb_date(record.get("unifiedStandardStart")),
                "raw": record,
            }
        )
    return rows


class SuccessFactorsSource(Source):
    """SAP SuccessFactors career sites (RMK tile boards and CSB JSON API).

    Endpoint recipe ported from santifer/career-ops
    providers/successfactors.mjs (MIT).

    ``variant = "csb"`` forces the newer Career Site Builder JSON API;
    otherwise the RMK tile fragment scraper runs first and falls back to CSB
    automatically when it yields zero postings (the CSB empty-shell
    signature). RMK states no posting date, so RMK rows are undated; CSB
    carries a real date. Neither endpoint states a description.
    """

    kind = "successfactors"

    def fetch(self) -> Iterable[JobPosting]:
        cfg = _sf_config(str(self.require("careers_url")))
        employer = str(self.options.get("employer") or self.name)
        delay = max(0.0, _float_option(self.options, "delay_seconds", 0.0))
        csb_max_pages = min(
            max(1, _int_option(self.options, "max_pages", _CSB_MAX_PAGES_PER_LOCALE)),
            _CSB_MAX_PAGES_PER_LOCALE,
        )

        if str(self.options.get("variant") or "").lower() == "csb":
            rows = self._fetch_csb(cfg, csb_max_pages, delay, forced=True)
        else:
            rmk_error: Exception | None = None
            try:
                rows = self._fetch_rmk(cfg, delay)
            except Exception as exc:
                rows, rmk_error = [], exc
            if not rows:
                try:
                    rows = self._fetch_csb(cfg, csb_max_pages, delay, forced=False)
                except Exception as exc:
                    log.debug("successfactors: CSB fallback failed for %s: %s", self.name, exc)
                    rows = []
                if not rows and rmk_error is not None:
                    raise rmk_error

        for row in rows:
            try:
                yield JobPosting(
                    source=f"{self.kind}:{self.name}",
                    source_id=str(row["id"]),
                    url=row["url"],
                    title=row["title"],
                    employer=employer,
                    location=row["location"],
                    description="",  # neither endpoint states one
                    posted_at=row["posted_at"],
                    remote=looks_remote(row["location"], row["title"]),
                    raw=row["raw"],
                )
            except Exception as exc:  # pragma: no cover - defensive
                log.warning("skipping malformed successfactors posting %s: %s", row.get("url"), exc)

    def _fetch_rmk(self, cfg: dict[str, str], delay: float) -> list[dict[str, Any]]:
        """RMK strategy: page the /tile-search-results/ HTML fragment.

        ``startrow`` is a plain row offset with a tenant-specific page size,
        so each loop advances by the number of tiles actually returned and a
        per-id dedup set guards against overlap or an ignored offset.
        """
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        startrow = 0
        for page in range(_SF_RMK_MAX_PAGES):
            if delay and page:
                time.sleep(delay)
            try:
                fragment = _fetch_text(f"{cfg['tile_api']}?startrow={startrow}", headers={"Accept": "text/html"})
            except Exception:
                if page == 0:
                    raise
                log.warning("successfactors: RMK page %d failed for %s; keeping %d rows", page, self.name, len(rows))
                break
            tiles = _parse_sf_tiles(fragment, cfg["job_base"])
            if not tiles:
                break
            fresh = 0
            for tile in tiles:
                if tile["id"] in seen:
                    continue
                seen.add(tile["id"])
                fresh += 1
                rows.append(tile)
            if fresh == 0:
                break  # server ignored the offset (or we've looped)
            if len(rows) >= _SF_MAX_JOBS:
                break
            startrow += len(tiles)
        return rows[:_SF_MAX_JOBS]

    def _fetch_csb(
        self, cfg: dict[str, str], max_pages: int, delay: float, *, forced: bool
    ) -> list[dict[str, Any]]:
        """CSB strategy: discover locales, page the JSON jobs API per locale.

        The API only returns a posting under a locale it was published in, so
        a hardcoded locale would miss entire tenants -- locales are read from
        the /search/ language switcher and every one is queried, deduped by
        job id.
        """
        locales = list(_CSB_DEFAULT_LOCALES)
        try:
            discovered = _extract_locales(_fetch_text(cfg["search_page"], headers={"Accept": "text/html"}))
            if discovered:
                locales = discovered
        except Exception as exc:
            log.debug("successfactors: locale discovery failed for %s: %s", self.name, exc)

        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        failures: list[Exception] = []
        requests_made = 0
        for locale in locales:
            if len(rows) >= _SF_MAX_JOBS:
                break
            total: int | None = None
            for page in range(max_pages):
                if delay and requests_made:
                    time.sleep(delay)
                requests_made += 1
                try:
                    payload = _post_json_dict(
                        cfg["jobs_api"],
                        {"keywords": "", "locale": locale, "location": "", "pageNumber": page, "sortBy": "recent"},
                        headers={"Accept": "application/json"},
                    )
                except Exception as exc:
                    failures.append(exc)
                    break  # this locale failed -- try the next
                if total is None:
                    reported = payload.get("totalJobs")
                    if isinstance(reported, int) and not isinstance(reported, bool):
                        total = reported
                # Fullness checks use the raw response count, not the parsed
                # row count: parsing drops id/title-less records, and a full
                # page with a few dropped records must not stop pagination.
                results = payload.get("jobSearchResult")
                raw_count = len(results) if isinstance(results, list) else 0
                if raw_count == 0:
                    break
                for row in _parse_csb_jobs(payload, cfg, locale):
                    if row["id"] in seen:
                        continue
                    seen.add(row["id"])
                    rows.append(row)
                    if len(rows) >= _SF_MAX_JOBS:
                        break
                if len(rows) >= _SF_MAX_JOBS:
                    break
                if total is not None and (page + 1) * _CSB_PAGE_SIZE >= total:
                    break
                if raw_count < _CSB_PAGE_SIZE:
                    break
        if forced and not rows and failures:
            # Explicitly-CSB tenants must not report a dead endpoint as an
            # empty board.
            raise failures[0]
        return rows


# ---------------------------------------------------------------------------
# Cornerstone OnDemand (CSOD)
# ---------------------------------------------------------------------------

# Endpoint recipe ported from santifer/career-ops providers/csod.mjs (MIT).

_CSOD_PAGE_SIZE = 25  # server default; csod.mjs verified its tenant serves 25/page
_CSOD_MAX_PAGES = 40
_CSOD_MAX_JOBS = 1000
_CSOD_TOKEN = re.compile(r'"token"\s*:\s*"([A-Za-z0-9._-]+)"')


def _csod_config(raw: str) -> dict[str, Any]:
    """Parse tenant origin / site id / corp name out of a careersite URL."""
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme not in ("http", "https") or (host != "csod.com" and not host.endswith(".csod.com")):
        raise ValueError(f"csod: careers_url must be a *.csod.com careersite URL, got {raw!r}")
    match = re.search(r"/ux/ats/careersite/(\d+)(?:/|$)", parsed.path, re.I)
    if not match:
        raise ValueError(f"csod: careers_url carries no /ux/ats/careersite/<id> path, got {raw!r}")
    site_id = int(match.group(1))
    corp_name = (parse_qs(parsed.query).get("c") or [""])[0] or host.split(".")[0]
    origin = f"{parsed.scheme}://{parsed.netloc}"
    return {
        "origin": origin,
        "site_id": site_id,
        "corp_name": corp_name,
        "home_url": f"{origin}/ux/ats/careersite/{site_id}/home?c={quote(corp_name, safe='')}",
        "search_api": f"{origin}/services/x/career-site/v1/search",
    }


def _parse_csod_date(raw: Any) -> datetime | None:
    """postingEffectiveDate is US-format ``M/D/YYYY``; impossible dates
    (4/31, 2/30) yield None rather than rolling over."""
    if not isinstance(raw, str):
        return None
    match = re.fullmatch(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw.strip())
    if not match:
        return None
    try:
        return datetime(int(match.group(3)), int(match.group(1)), int(match.group(2)), tzinfo=timezone.utc)
    except ValueError:
        return None


def _csod_locations(raw: Any) -> str:
    """locations is ``[{city, state, country}]``; render "City, CC" per work
    location and join multiples with " / "."""
    parts: list[str] = []
    for entry in raw if isinstance(raw, list) else []:
        if not isinstance(entry, dict):
            continue
        city = str(entry.get("city") or "").strip()
        country = str(entry.get("country") or "").strip()
        text = f"{city}, {country}" if city and country else city or country
        if text and text not in parts:
            parts.append(text)
    return " / ".join(parts)


def _parse_csod_requisitions(payload: dict[str, Any], cfg: dict[str, Any]) -> list[dict[str, Any]]:
    data = payload.get("data") if isinstance(payload, dict) else None
    requisitions = data.get("requisitions") if isinstance(data, dict) else None
    rows: list[dict[str, Any]] = []
    for req in requisitions if isinstance(requisitions, list) else []:
        if not isinstance(req, dict):
            continue
        req_id = str(req["requisitionId"]) if req.get("requisitionId") is not None else ""
        title = _strip_tags(req.get("displayJobTitle"))
        if not req_id or not title:
            continue
        rows.append(
            {
                "id": req_id,
                "title": title,
                "url": (
                    f"{cfg['origin']}/ux/ats/careersite/{cfg['site_id']}/home/requisition/"
                    f"{req_id}?c={quote(cfg['corp_name'], safe='')}"
                ),
                "location": _csod_locations(req.get("locations")),
                "posted_at": _parse_csod_date(req.get("postingEffectiveDate")),
                "raw": req,
            }
        )
    return rows


class CornerstoneSource(Source):
    """Cornerstone OnDemand hosted career sites.

    Endpoint recipe ported from santifer/career-ops providers/csod.mjs (MIT).

    The search API is public but wants a bearer token -- an *anonymous* JWT
    embedded in the careersite home page (no login, no cookies). One GET
    extracts it, then the JSON search endpoint pages through requisitions.
    The search response states no description, so descriptions are empty.
    """

    kind = "csod"

    def fetch(self) -> Iterable[JobPosting]:
        cfg = _csod_config(str(self.require("careers_url")))
        employer = str(self.options.get("employer") or self.name)
        max_pages = min(max(1, _int_option(self.options, "max_pages", _CSOD_MAX_PAGES)), _CSOD_MAX_PAGES)
        delay = max(0.0, _float_option(self.options, "delay_seconds", 0.0))

        home_html = _fetch_text(cfg["home_url"], headers={"Accept": "text/html"})
        token_match = _CSOD_TOKEN.search(home_html)
        if not token_match:
            raise FetchError(f"csod: no anonymous token on {cfg['home_url']}")
        token = token_match.group(1)

        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        total: int | None = None
        for page in range(1, max_pages + 1):  # pageNumber is 1-based
            if delay and page > 1:
                time.sleep(delay)
            try:
                payload = _post_json_dict(
                    cfg["search_api"],
                    self._search_body(cfg["site_id"], page),
                    headers={"Accept": "application/json", "Authorization": f"Bearer {token}"},
                )
            except Exception:
                if page == 1:
                    raise
                log.warning("csod: page %d failed for %s; keeping %d rows", page, self.name, len(rows))
                break
            if total is None:
                data = payload.get("data")
                reported = data.get("totalCount") if isinstance(data, dict) else None
                if isinstance(reported, int) and not isinstance(reported, bool):
                    total = reported
            page_rows = _parse_csod_requisitions(payload, cfg)
            if not page_rows:
                break
            fresh = 0
            for row in page_rows:
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                fresh += 1
                rows.append(row)
                if len(rows) >= _CSOD_MAX_JOBS:
                    break
            if fresh == 0:
                break  # server ignored the page number (or we've looped)
            if len(rows) >= _CSOD_MAX_JOBS:
                break
            if total is not None and page * _CSOD_PAGE_SIZE >= total:
                break
            if len(page_rows) < _CSOD_PAGE_SIZE:
                break

        for row in rows:
            try:
                yield JobPosting(
                    source=f"{self.kind}:{self.name}",
                    source_id=str(row["id"]),
                    url=row["url"],
                    title=row["title"],
                    employer=employer,
                    location=row["location"],
                    description="",  # the search response states none
                    posted_at=row["posted_at"],
                    remote=looks_remote(row["location"], row["title"]),
                    raw=row["raw"],
                )
            except Exception as exc:  # pragma: no cover - defensive
                log.warning("skipping malformed csod posting %s: %s", row.get("url"), exc)

    @staticmethod
    def _search_body(site_id: int, page: int) -> dict[str, Any]:
        """The exact payload the career-site front end sends (csod.mjs)."""
        return {
            "careerSiteId": site_id,
            "careerSitePageId": site_id,
            "pageNumber": page,
            "pageSize": _CSOD_PAGE_SIZE,
            "cultureId": 1,
            "cultureName": "en-US",
            "searchText": "",
            "states": [],
            "countryCodes": [],
            "cities": [],
            "placeID": "",
            "radius": None,
            "postingsWithinDays": None,
            "customFieldCheckboxKeys": [],
            "customFieldDropdowns": [],
            "customFieldRadios": [],
        }


# ---------------------------------------------------------------------------
# Oracle Cloud Recruiting (ORC / Fusion Candidate Experience)
# ---------------------------------------------------------------------------

# Endpoint recipe ported from santifer/career-ops providers/oraclecloud.mjs
# (MIT).

_ORACLE_PAGE_SIZE = 200
_ORACLE_MAX_PAGES = 25
_ORACLE_HOST = re.compile(r"^[a-z0-9-]+\.fa\.(?:[a-z0-9-]+\.)?(?:ocs\.)?oraclecloud\.com$", re.I)
# facetsList is a fixed constant on the finder; %3B is the encoded ';'.
_ORACLE_FACETS = (
    "LOCATIONS%3BWORK_LOCATIONS%3BWORKPLACE_TYPES%3BTITLES%3BCATEGORIES"
    "%3BORGANIZATIONS%3BPOSTING_DATES%3BFLEX_FIELDS"
)
# Browser-like UA reduces WAF friction (Imperva 403s unfamiliar agents on
# some tenants); the requisitions API itself needs no auth.
_ORACLE_HEADERS = {"User-Agent": _BROWSER_UA, "Accept": "application/json"}


def _oracle_site(raw: str, site_number: Any = None, location_id: Any = None) -> dict[str, Any]:
    """Resolve ORC coordinates from a CandidateExperience careers URL."""
    parsed = urlparse(raw)
    host = (parsed.hostname or "").lower()
    if parsed.scheme != "https" or not _ORACLE_HOST.match(host):
        raise ValueError(
            f"oraclecloud: careers_url host must match *.fa[.<region>][.ocs].oraclecloud.com, got {raw!r}"
        )
    segments = [segment for segment in parsed.path.split("/") if segment]
    lang = "en"
    if "CandidateExperience" in segments:
        index = segments.index("CandidateExperience")
        if index + 1 < len(segments):
            lang = segments[index + 1]
    site_from_url = None
    if "sites" in segments:
        index = segments.index("sites")
        if index + 1 < len(segments):
            site_from_url = segments[index + 1]
    return {
        "host": host,
        "lang": lang,
        "site_number": str(site_number) if site_number else (site_from_url or "CX_1"),
        "location_id": str(location_id) if location_id not in (None, "") else None,
    }


def _oracle_api_url(site: dict[str, Any], offset: int, limit: int = _ORACLE_PAGE_SIZE) -> str:
    """Build the requisitions API URL.

    limit/offset are set in BOTH the finder segment and top-level because
    some tenants only honor one. The ``expand`` is REQUIRED: without it the
    API returns TotalJobsCount but an empty requisitionList.
    """
    # Finder grammar: `findReqs;key=val,key=val,...` -- a ';' after the
    # finder name, then comma-separated pairs (a comma after findReqs 400s).
    finder_params = [
        f"siteNumber={site['site_number']}",
        f"facetsList={_ORACLE_FACETS}",
        f"limit={limit}",
        "sortBy=POSTING_DATES_DESC",
        f"offset={offset}",
    ]
    if site.get("location_id"):
        finder_params.append(f"locationId={site['location_id']}")
    finder = "findReqs;" + ",".join(finder_params)
    expand = quote("requisitionList.workLocation,requisitionList.secondaryLocations", safe="")
    return (
        f"https://{site['host']}/hcmRestApi/resources/latest/recruitingCEJobRequisitions"
        f"?onlyData=true&expand={expand}&finder={finder}&limit={limit}&offset={offset}"
    )


def _oracle_job_url(site: dict[str, Any], req_id: str) -> str:
    return (
        f"https://{site['host']}/hcmUI/CandidateExperience/{site['lang']}"
        f"/sites/{site['site_number']}/job/{req_id}"
    )


def _oracle_location(req: dict[str, Any]) -> str:
    """PrimaryLocation, else the expanded workLocation object, else ""."""
    primary = req.get("PrimaryLocation")
    if isinstance(primary, str) and primary.strip():
        return primary.strip()
    work = req.get("workLocation")
    if isinstance(work, list) and work and isinstance(work[0], dict):
        parts = [
            str(work[0].get(key)).strip()
            for key in ("TownOrCity", "Region", "Country")
            if isinstance(work[0].get(key), str) and str(work[0].get(key)).strip()
        ]
        return ", ".join(parts)
    return ""


def _parse_oracle_requisitions(payload: Any, site: dict[str, Any]) -> list[dict[str, Any]]:
    """Rows from ``items[0].requisitionList``; rows with no resolvable URL
    are dropped (no dedup key, nothing to link to)."""
    items = payload.get("items") if isinstance(payload, dict) else None
    item = items[0] if isinstance(items, list) and items else None
    requisitions = item.get("requisitionList") if isinstance(item, dict) else None
    rows: list[dict[str, Any]] = []
    for req in requisitions if isinstance(requisitions, list) else []:
        if not isinstance(req, dict):
            continue
        if req.get("Id") is not None:
            req_id = str(req["Id"])
        elif req.get("RequisitionNumber") is not None:
            req_id = str(req["RequisitionNumber"])
        else:
            req_id = ""
        external = req.get("ExternalURL")
        external = external.strip() if isinstance(external, str) else ""
        url = external or (_oracle_job_url(site, req_id) if req_id else "")
        if not url:
            continue
        rows.append(
            {
                "id": req_id or url,
                "title": req.get("Title") if isinstance(req.get("Title"), str) else "",
                "url": url,
                "location": _oracle_location(req),
                "posted_at": parse_timestamp(req.get("PostedDate")),
                "description": (
                    html_to_text(req["ShortDescriptionStr"])
                    if isinstance(req.get("ShortDescriptionStr"), str)
                    else ""
                ),
                "workplace_type": req.get("WorkplaceTypeCode"),
                "raw": req,
            }
        )
    return rows


class OracleCloudSource(Source):
    """Oracle Recruiting Cloud / Fusion Candidate Experience sites.

    Endpoint recipe ported from santifer/career-ops providers/oraclecloud.mjs
    (MIT). Zero-auth GET against the public recruitingCEJobRequisitions REST
    API. ``ShortDescriptionStr`` is the only description the API states, so
    that (converted to text) is the whole description -- nothing is fetched
    or invented beyond it.
    """

    kind = "oraclecloud"

    def fetch(self) -> Iterable[JobPosting]:
        site = _oracle_site(
            str(self.require("careers_url")),
            site_number=self.options.get("site_number"),
            location_id=self.options.get("location_id"),
        )
        employer = str(self.options.get("employer") or self.name)
        max_pages = min(max(1, _int_option(self.options, "max_pages", _ORACLE_MAX_PAGES)), _ORACLE_MAX_PAGES)
        delay = max(0.0, _float_option(self.options, "delay_seconds", 0.0))

        rows: list[dict[str, Any]] = []
        total: int | None = None
        for page in range(max_pages):
            offset = page * _ORACLE_PAGE_SIZE
            if delay and page:
                time.sleep(delay)
            try:
                payload = fetch_json(_oracle_api_url(site, offset), headers=_ORACLE_HEADERS)
            except Exception:
                if page == 0:
                    raise
                log.warning("oraclecloud: page %d failed for %s; keeping %d rows", page, self.name, len(rows))
                break
            rows.extend(_parse_oracle_requisitions(payload, site))

            items = payload.get("items") if isinstance(payload, dict) else None
            item = items[0] if isinstance(items, list) and items else None
            if total is None and isinstance(item, dict):
                reported = item.get("TotalJobsCount")
                if isinstance(reported, int) and not isinstance(reported, bool):
                    total = reported
            req_list = item.get("requisitionList") if isinstance(item, dict) else None
            list_len = len(req_list) if isinstance(req_list, list) else 0

            # `hasMore` is unreliable (some tenants return false on every
            # page with thousands of jobs left), so it is deliberately NOT a
            # stop signal. The authoritative signals are the returned list
            # length and TotalJobsCount.
            if list_len == 0 or list_len < _ORACLE_PAGE_SIZE:
                break
            if total is not None and offset + _ORACLE_PAGE_SIZE >= total:
                break

        for row in rows:
            try:
                yield JobPosting(
                    source=f"{self.kind}:{self.name}",
                    source_id=str(row["id"]),
                    url=row["url"],
                    title=row["title"],
                    employer=employer,
                    location=row["location"],
                    description=row["description"],
                    posted_at=row["posted_at"],
                    # ORA_REMOTE is the API's own remote marker.
                    remote=row["workplace_type"] == "ORA_REMOTE"
                    or looks_remote(row["location"], row["title"]),
                    raw=row["raw"],
                )
            except Exception as exc:  # pragma: no cover - defensive
                log.warning("skipping malformed oraclecloud posting %s: %s", row.get("url"), exc)


# ---------------------------------------------------------------------------
# Jobvite
# ---------------------------------------------------------------------------

# Endpoint recipe ported from santifer/career-ops providers/jobvite.mjs (MIT).

_JOBVITE_HOST = "jobs.jobvite.com"


def _jobvite_company_id(raw: str) -> str:
    """Extract the companyId slug from a jobs.jobvite.com URL.

    Accepted forms::

        https://jobs.jobvite.com/{slug}
        https://jobs.jobvite.com/{slug}/jobs
        https://jobs.jobvite.com/api/company/{slug}/jobs
    """
    parsed = urlparse(raw)
    if parsed.scheme != "https" or (parsed.hostname or "").lower() != _JOBVITE_HOST:
        raise ValueError(f"jobvite: careers_url must be an https {_JOBVITE_HOST} URL, got {raw!r}")
    segments = [segment for segment in parsed.path.split("/") if segment]
    if "company" in segments:
        index = segments.index("company")
        if index + 1 < len(segments):
            return segments[index + 1]
    if segments and segments[0] != "api":
        return segments[0]
    raise ValueError(f"jobvite: cannot derive a company id from careers_url {raw!r}")


class JobviteSource(Source):
    """Jobvite per-tenant public jobs JSON API.

    Endpoint recipe ported from santifer/career-ops providers/jobvite.mjs
    (MIT). ``GET https://jobs.jobvite.com/api/company/{companyId}/jobs``
    returns ``{"jobs": [{id, title, category, location, country, jobType,
    date, applyURL}]}``. ``applyURL`` is the posting URL and commonly points
    at a branded company domain; postings without a valid https applyURL or
    without a title are dropped (nothing to link to / nothing to list).
    """

    kind = "jobvite"

    def fetch(self) -> Iterable[JobPosting]:
        company_id = _jobvite_company_id(str(self.require("careers_url")))
        employer = str(self.options.get("employer") or self.name)
        payload = fetch_json(
            f"https://{_JOBVITE_HOST}/api/company/{quote(company_id, safe='')}/jobs",
            headers={"Accept": "application/json"},
        )
        jobs = payload.get("jobs") if isinstance(payload, dict) else None
        for job in jobs if isinstance(jobs, list) else []:
            if not isinstance(job, dict):
                continue
            try:
                title = job.get("title")
                title = title.strip() if isinstance(title, str) else ""
                if not title:
                    continue
                raw_url = job.get("applyURL")
                raw_url = raw_url.strip() if isinstance(raw_url, str) else ""
                if not raw_url or urlparse(raw_url).scheme != "https" or not urlparse(raw_url).netloc:
                    continue
                location = job.get("location")
                location = location.strip() if isinstance(location, str) else ""
                if not location:
                    country = job.get("country")
                    location = country.strip() if isinstance(country, str) else ""
                category = job.get("category")
                category = category.strip() if isinstance(category, str) else ""
                yield JobPosting(
                    source=f"{self.kind}:{self.name}",
                    source_id=str(job["id"]) if job.get("id") is not None else raw_url,
                    url=raw_url,
                    title=title,
                    employer=employer,
                    location=location,
                    description="",  # the list response states none
                    posted_at=parse_timestamp(job.get("date")),
                    remote=looks_remote(location, title),
                    department=category or None,
                    raw=job,
                )
            except Exception as exc:  # pragma: no cover - defensive
                log.warning("skipping malformed jobvite posting: %s", exc)


# ---------------------------------------------------------------------------
# Radancy (TalentBrew)
# ---------------------------------------------------------------------------

# Endpoint recipe ported from santifer/career-ops providers/radancy.mjs (MIT).

_RADANCY_MAX_PAGES = 200
_RADANCY_DEFAULT_MAX_JOBS = 2000
_RADANCY_RECORDS_PER_PAGE = 100  # radancy.mjs verified the fragment endpoint honors 100
_RADANCY_FRAGMENT_HEADERS = {"Accept": "application/json", "X-Requested-With": "XMLHttpRequest"}

_RADANCY_MODERN_LINK = re.compile(
    r'search-results-list__job-link[^"]*"[^>]*href="([^"]+)"[^>]*>(.*?)</a>', re.S
)
_RADANCY_MODERN_LOC = re.compile(r"__job-info--location.*?<span>(.*?)</span>", re.S)
_RADANCY_ANCHOR = re.compile(r"<a\b([^>]*)>(.*?)</a>", re.I | re.S)
_RADANCY_HEADING = re.compile(r"<h[1-6][^>]*>(.*?)</h[1-6]>", re.I | re.S)
_RADANCY_LEGACY_LOC = re.compile(r'class="[^"]*job-location[^"]*"[^>]*>(.*?)</span>', re.I | re.S)


def _radancy_list_url(raw: str) -> str:
    """Resolve the search-jobs list URL from a careers URL; default /en."""
    parsed = urlparse(raw)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValueError(f"radancy: cannot resolve a search-jobs URL from careers_url {raw!r}")
    origin = f"{parsed.scheme}://{parsed.netloc}"
    if re.search(r"/search-jobs/?$", parsed.path):
        return f"{origin}{parsed.path.rstrip('/')}"
    lang_match = re.match(r"^/([a-z]{2})(/|$)", parsed.path)
    lang = lang_match.group(1) if lang_match else "en"
    return f"{origin}/{lang}/search-jobs"


def _radancy_fragment_url(list_url: str, page: int, records: int = _RADANCY_RECORDS_PER_PAGE) -> str:
    """The JSON results-fragment URL the page's own JS uses.

    SearchResultsModuleName MUST be sent (without it the server returns an
    empty results string); SearchFiltersModuleName MUST BE OMITTED (sending
    it re-attaches a multi-megabyte facet blob to every page).
    """
    query = urlencode(
        {
            "ActiveFacetID": "0",
            "CurrentPage": str(page),
            "RecordsPerPage": str(records),
            "Distance": "50",
            "RadiusUnitType": "0",
            "Keywords": "",
            "Location": "",
            "ShowRadius": "False",
            "IsPagination": "True",
            "CustomFacetName": "",
            "FacetTerm": "",
            "FacetType": "0",
            "SearchResultsModuleName": "Search Results",
            "SortCriteria": "0",
            "SortDirection": "0",
            "SearchType": "5",
        }
    )
    return f"{list_url}/results?{query}"


def _radancy_totals(fragment_html: str) -> tuple[int | None, int | None]:
    """The server's own result/page totals from a results fragment."""

    def number(pattern: str) -> int | None:
        match = re.search(pattern, fragment_html)
        return int(match.group(1)) if match else None

    return number(r'data-total-results="(\d+)"'), number(r'data-total-pages="(\d+)"')


def _parse_radancy_modern(page_html: str, origin: str) -> list[dict[str, Any]]:
    """MODERN markup: ``<li class="search-results-list__item">`` cards with a
    ``search-results-list__job-link`` anchor (the stable TalentBrew prefix)."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for block in re.split(r'<li class="search-results-list__item', page_html)[1:]:
        link = _RADANCY_MODERN_LINK.search(block)
        if not link:
            continue
        href = html.unescape(link.group(1))
        id_match = re.search(r'data-job-id="([^"]+)"', block)
        if id_match:
            job_id = id_match.group(1)
        else:
            numbers = re.findall(r"/(\d+)(?=[/?#]|$)", href)
            job_id = numbers[-1] if numbers else href
        if job_id in seen:
            continue
        title = _strip_tags(link.group(2))
        if not title:
            continue
        loc = _RADANCY_MODERN_LOC.search(block)
        seen.add(job_id)
        rows.append(
            {
                "id": job_id,
                "title": title,
                "url": urljoin(f"{origin}/", href),
                "location": _strip_tags(loc.group(1)) if loc else "",
            }
        )
    return rows


def _parse_radancy_legacy(page_html: str, origin: str) -> list[dict[str, Any]]:
    """LEGACY markup: the anchor IS the row, anchored on ``<a>`` carrying
    both data-job-id and a /job/ href so the sibling save-job ``<button>``
    (which repeats data-job-id) cannot produce a phantom row."""
    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for anchor in _RADANCY_ANCHOR.finditer(page_html):
        attrs, inner = anchor.group(1), anchor.group(2)
        id_match = re.search(r'data-job-id="([^"]+)"', attrs, re.I)
        if not id_match:
            continue
        href_match = re.search(r'href="([^"]+)"', attrs, re.I)
        if not href_match:
            continue
        href = html.unescape(href_match.group(1))
        if "/job/" not in href:
            continue
        job_id = id_match.group(1)
        if job_id in seen:
            continue
        # Title lives in the heading; falling back to the anchor's full text
        # would swallow the req-number and location spans, so strip element
        # content first and only then accept bare text.
        heading = _RADANCY_HEADING.search(inner)
        if heading:
            title = _strip_tags(heading.group(1))
        else:
            title = _strip_tags(re.sub(r"<span.*?</span>", " ", inner, flags=re.I | re.S))
        if not title:
            continue
        loc = _RADANCY_LEGACY_LOC.search(inner)
        seen.add(job_id)
        rows.append(
            {
                "id": job_id,
                "title": title,
                "url": urljoin(f"{origin}/", href),
                "location": _strip_tags(loc.group(1)) if loc else "",
            }
        )
    return rows


def _parse_radancy_results(page_html: str, origin: str) -> list[dict[str, Any]]:
    modern = _parse_radancy_modern(page_html, origin)
    return modern if modern else _parse_radancy_legacy(page_html, origin)


class RadancySource(Source):
    """Radancy (TalentBrew) hosted career sites.

    Endpoint recipe ported from santifer/career-ops providers/radancy.mjs
    (MIT). The JSON results-fragment endpoint is preferred (the plain
    ``?p=N`` HTML pages carry a multi-megabyte facet blob per page on legacy
    tenants); any fragment failure falls back to the HTML page walk. Neither
    transport states a posting date or description, so both are emitted
    empty.
    """

    kind = "radancy"

    def fetch(self) -> Iterable[JobPosting]:
        list_url = _radancy_list_url(str(self.require("careers_url")))
        origin = _origin(list_url)
        employer = str(self.options.get("employer") or self.name)
        max_pages = min(max(1, _int_option(self.options, "max_pages", _RADANCY_MAX_PAGES)), _RADANCY_MAX_PAGES)
        max_jobs = max(1, _int_option(self.options, "max_jobs", _RADANCY_DEFAULT_MAX_JOBS))
        delay = max(0.0, _float_option(self.options, "delay_seconds", 0.0))

        rows = self._fetch_fragments(list_url, origin, max_pages, max_jobs, delay)
        if rows is None:
            rows = self._fetch_pages(list_url, origin, max_pages, max_jobs, delay)

        for row in rows[:max_jobs]:
            try:
                yield JobPosting(
                    source=f"{self.kind}:{self.name}",
                    source_id=str(row["id"]),
                    url=row["url"],
                    title=row["title"],
                    employer=employer,
                    location=row["location"],
                    description="",  # the list markup states none
                    posted_at=None,  # neither transport carries a date
                    remote=looks_remote(row["location"], row["title"]),
                    raw=row,
                )
            except Exception as exc:  # pragma: no cover - defensive
                log.warning("skipping malformed radancy posting %s: %s", row.get("url"), exc)

    def _fetch_fragments(
        self, list_url: str, origin: str, max_pages: int, max_jobs: int, delay: float
    ) -> list[dict[str, Any]] | None:
        """The JSON fragment transport; None means "fall back to HTML"."""
        try:
            payload = fetch_json(_radancy_fragment_url(list_url, 1), headers=_RADANCY_FRAGMENT_HEADERS)
        except Exception as exc:
            log.debug("radancy: fragment endpoint unavailable for %s: %s", self.name, exc)
            return None
        first_html = payload.get("results") if isinstance(payload, dict) else None
        if not isinstance(first_html, str) or not first_html:
            return None
        first_rows = _parse_radancy_results(first_html, origin)
        if not first_rows:
            return None

        total_results, total_pages = _radancy_totals(first_html)
        # Bound by the server's own page count when it gives one; the local
        # caps still apply so a bogus total can't drive an unbounded walk.
        # radancy.mjs uses `totalPages ?? maxPages`: only a MISSING total
        # falls back to the cap -- a stated total of 0 means "no more pages",
        # so the falsy-0 case must not restart an unbounded walk.
        last_page = min(total_pages if total_pages is not None else max_pages, max_pages)

        rows: list[dict[str, Any]] = []
        seen: set[str] = set()

        def push(new_rows: list[dict[str, Any]]) -> int:
            fresh = 0
            for row in new_rows:
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                fresh += 1
                rows.append(row)
            return fresh

        push(first_rows)
        for page in range(2, last_page + 1):
            if len(rows) >= max_jobs:
                break
            if delay:
                time.sleep(delay)
            try:
                payload = fetch_json(_radancy_fragment_url(list_url, page), headers=_RADANCY_FRAGMENT_HEADERS)
                fragment = payload.get("results") if isinstance(payload, dict) else None
                page_rows = (
                    _parse_radancy_results(fragment, origin)
                    if isinstance(fragment, str) and fragment
                    else []
                )
            except Exception:
                # A mid-walk blip must not discard earlier pages.
                log.warning("radancy: fragment page %d failed for %s; keeping %d rows", page, self.name, len(rows))
                break
            if not page_rows:
                break
            if push(page_rows) == 0:
                break  # server clamped the page -- stop

        # Never truncate silently: report the count actually returned.
        returned = min(len(rows), max_jobs)
        if total_results and returned < total_results:
            log.warning(
                "radancy: %s truncated at %d of %d postings -- raise max_jobs/max_pages for more",
                self.name,
                returned,
                total_results,
            )
        return rows

    def _fetch_pages(
        self, list_url: str, origin: str, max_pages: int, max_jobs: int, delay: float
    ) -> list[dict[str, Any]]:
        """The plain ``?p=N`` HTML walk (1-based; past-the-end is empty)."""
        rows: list[dict[str, Any]] = []
        seen: set[str] = set()
        for page in range(1, max_pages + 1):
            if delay and page > 1:
                time.sleep(delay)
            try:
                page_html = _fetch_text(f"{list_url}?p={page}", headers={"Accept": "text/html"})
            except Exception:
                if page == 1 and not rows:
                    raise  # a dead site must not look like an empty board
                log.warning("radancy: page %d failed for %s; keeping %d rows", page, self.name, len(rows))
                break
            page_rows = _parse_radancy_results(page_html, origin)
            if not page_rows:
                break  # past the last page
            fresh = 0
            for row in page_rows:
                if row["id"] in seen:
                    continue
                seen.add(row["id"])
                fresh += 1
                rows.append(row)
            if fresh == 0:
                break  # server clamped ?p= to the last page (or looped)
            if len(rows) >= max_jobs:
                break
        return rows


ENTERPRISE_SOURCES: tuple[type[Source], ...] = (
    ICIMSSource,
    SuccessFactorsSource,
    CornerstoneSource,
    OracleCloudSource,
    JobviteSource,
    RadancySource,
)
