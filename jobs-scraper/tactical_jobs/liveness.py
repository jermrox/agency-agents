"""Re-check whether a published posting still exists.

A job is removed only on unambiguous evidence: 404/410, or the page itself
says the posting is closed. Everything else -- 403, timeout, 5xx, an
unexpected redirect -- returns ``unknown`` and the job stays published.
"""

from __future__ import annotations

import logging
import re
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from .http import USER_AGENT

log = logging.getLogger(__name__)

LIVE = "live"
GONE = "gone"
UNKNOWN = "unknown"

_MAX_BODY_BYTES = 400_000
_DEFAULT_TIMEOUT = 20
_DEFAULT_WORKERS = 8

# Set once any Workday JSON endpoint answers 200 in this process. Guards
# against reading a wholesale block as "every requisition is closed".
_WORKDAY_REACHABLE: set[bool] = set()

_EXPIRED_MARKERS = (
    "no longer accepting applications",
    "no longer accepting application",
    "this job is no longer available",
    "this position is no longer available",
    "this posting is no longer available",
    "the job you are looking for is no longer",
    "job posting has expired",
    "this job has expired",
    "this posting has expired",
    "posting is closed",
    "this requisition is closed",
    "this position has been filled",
    "position has since been filled",
    "we are no longer accepting",
    "job not found",
    "position not found",
    "requisition not found",
    "sorry, this job is not available",
    "sorry, this position is no longer",
    "the job you have selected is no longer",
    "job id is no longer active",
    "this opportunity is no longer available",
)

_TAG_RE = re.compile(r"<(?:script|style)\b.*?</(?:script|style)>", re.I | re.S)
_MARKUP_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"\s+")


def _visible_text(body: bytes) -> str:
    try:
        html = body.decode("utf-8", errors="replace")
    except Exception:  # pragma: no cover
        return ""
    html = _TAG_RE.sub(" ", html)
    html = _MARKUP_RE.sub(" ", html)
    text = _WS_RE.sub(" ", html).lower()
    return text.replace("’", "'").replace("‘", "'")


@dataclass(frozen=True, slots=True)
class Liveness:
    url: str
    state: str
    reason: str
    http_status: int | None = None
    final_url: str | None = None
    checked_at: str = ""

    @property
    def is_gone(self) -> bool:
        return self.state == GONE

    def as_dict(self) -> dict[str, object]:
        return {
            "state": self.state,
            "reason": self.reason,
            "http_status": self.http_status,
            "checked_at": self.checked_at,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


# --- Workday ---------------------------------------------------------------
#
# A Workday careers site is a React shell: EVERY /job/... path returns HTTP 200
# with the same HTML, whether or not the requisition still exists. So the
# ordinary check can never retire a closed Workday posting, and Workday is the
# largest source on this board -- KBR, GDIT and Geneva between them. A closed
# requisition sat published for weeks purely because its shell still answered.
#
# The JSON endpoint the shell itself calls does distinguish them. Measured
# against five real KBR requisitions from one client, same headers, same run:
#
#     R2128060  R2128061  R2129095   still open    -> CXS 200, HTML 200
#     R2122577  R2120241  reposted under a new id  -> CXS 403, HTML 200
#
# So a 403 there is Workday saying the requisition is unpublished. It is not
# the generic 403 that check_url deliberately treats as unknown.

_WORKDAY_HOST_RE = re.compile(r"^[a-z0-9-]+\.wd\d+\.myworkdayjobs\.com$", re.I)
_WORKDAY_PATH_RE = re.compile(r"^/(?:[a-z]{2}-[A-Z]{2}/)?([^/]+)/job/(.+)$")


def workday_cxs_url(url: str) -> str | None:
    """The JSON endpoint behind a Workday posting URL, or None."""
    try:
        parts = urllib.parse.urlsplit(url)
    except ValueError:
        return None
    host = (parts.hostname or "").lower()
    if not _WORKDAY_HOST_RE.match(host):
        return None
    match = _WORKDAY_PATH_RE.match(parts.path)
    if not match:
        return None
    site, rest = match.group(1), match.group(2)
    tenant = host.split(".", 1)[0]
    return f"{parts.scheme}://{host}/wday/cxs/{tenant}/{site}/job/{rest}"


def check_url(url: str, *, timeout: int = _DEFAULT_TIMEOUT) -> Liveness:
    """Never raises; anything it cannot interpret becomes ``unknown``."""
    if not url or not url.lower().startswith(("http://", "https://")):
        return Liveness(url, UNKNOWN, "no fetchable url", checked_at=_now())

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", None) or response.getcode()
            final_url = response.geturl()
            body = response.read(_MAX_BODY_BYTES)
    except urllib.error.HTTPError as exc:
        if exc.code in (404, 410):
            return Liveness(url, GONE, f"HTTP {exc.code}", exc.code, checked_at=_now())
        return Liveness(
            url, UNKNOWN, f"HTTP {exc.code} (not a removal signal)", exc.code,
            checked_at=_now(),
        )
    except (urllib.error.URLError, TimeoutError, OSError, ValueError) as exc:
        return Liveness(url, UNKNOWN, f"unreachable: {exc}", checked_at=_now())

    # Workday's shell answers 200 for a requisition that no longer exists, so
    # the body below can never say otherwise. Ask the endpoint that knows.
    cxs = workday_cxs_url(url)
    if cxs is not None:
        verdict = _workday_requisition_state(cxs, timeout=timeout)
        if verdict is not None:
            return Liveness(url, verdict, f"workday cxs: {verdict}", status, final_url, _now())

    text = _visible_text(body)
    for marker in _EXPIRED_MARKERS:
        if marker in text:
            return Liveness(
                url, GONE, f"page says {marker!r}", status, final_url, _now()
            )

    reason = "reachable"
    if final_url and _redirected_off_posting(url, final_url):
        reason = f"redirected to {final_url}"

    return Liveness(url, LIVE, reason, status, final_url, _now())


_POSTING_PATH_RE = re.compile(
    r"/(?:job|jobs|opening|position|posting|vacanc|requisition|career)s?[-/]"
    r"(?P<tail>[^/?#]+)",
    re.I,
)

_LISTING_TAIL_RE = re.compile(
    r"^(?:search|results?|list|index|all|browse|home|apply|overview)$", re.I
)


def _looks_like_a_posting(path: str) -> bool:
    match = _POSTING_PATH_RE.search(path)
    if not match:
        return False
    return not _LISTING_TAIL_RE.match(match.group("tail"))


def _redirected_off_posting(original: str, final: str) -> bool:
    if original.rstrip("/") == final.rstrip("/"):
        return False
    if not _looks_like_a_posting(urllib.parse.urlparse(original).path):
        return False
    return not _looks_like_a_posting(urllib.parse.urlparse(final).path)


def check_all(
    urls: Iterable[str],
    *,
    workers: int = _DEFAULT_WORKERS,
    timeout: int = _DEFAULT_TIMEOUT,
) -> dict[str, Liveness]:
    """Deduplicates and checks concurrently. Workers stay modest to avoid abuse."""
    unique = sorted({u for u in urls if u})
    if not unique:
        return {}

    log.info("liveness: checking %d posting url(s)", len(unique))
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        verdicts = pool.map(lambda u: check_url(u, timeout=timeout), unique)
    results = {v.url: v for v in verdicts}

    gone = sum(1 for v in results.values() if v.is_gone)
    unknown = sum(1 for v in results.values() if v.state == UNKNOWN)
    log.info(
        "liveness: %d live, %d gone, %d unverifiable (kept)",
        len(results) - gone - unknown, gone, unknown,
    )
    return results


def _workday_requisition_state(cxs_url: str, *, timeout: int) -> str | None:
    """``gone`` / ``live`` from Workday's own JSON endpoint, or None if unclear.

    Returns None rather than guessing whenever the answer could be about us
    instead of the requisition -- a timeout, a 5xx, anything unparseable.
    """
    request = urllib.request.Request(
        cxs_url,
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", None) or response.getcode()
            if status == 200:
                _WORKDAY_REACHABLE.add(True)
                return LIVE
            return None
    except urllib.error.HTTPError as exc:
        if exc.code in (403, 404, 410):
            # Only trust this as a removal once something in this run has come
            # back 200 from a Workday endpoint. Without that check, Workday
            # rate-limiting or blocking us wholesale would read as "every
            # requisition closed" and empty the board in one sweep.
            if _WORKDAY_REACHABLE:
                return GONE
            log.warning(
                "workday cxs %s returned %s before any 200 this run; "
                "treating as unknown rather than risking a mass retire",
                cxs_url, exc.code,
            )
        return None
    except (urllib.error.URLError, TimeoutError, OSError, ValueError):
        return None
