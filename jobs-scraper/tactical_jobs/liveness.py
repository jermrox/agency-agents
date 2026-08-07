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
