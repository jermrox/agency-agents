"""Re-check whether a published posting still exists.

The board's credibility rests almost entirely on this file. A job aggregator
that shows dead listings is worse than no aggregator: the candidate spends
their evening writing a cover letter for a requisition that closed three weeks
ago, and they only find out after they hit submit.

Sources tell us what is on a board *today*. They cannot tell us that yesterday's
posting came down, because a posting that came down simply stops appearing --
and "stopped appearing" is indistinguishable from "the source errored", "the
search terms drifted", or "the ATS paginated differently". So the only reliable
way to retire a listing is to go back and ask its own URL.

THE BIAS IS DELIBERATE AND ONE-WAY
    We drop a job only on unambiguous evidence that it is gone: the server
    said 404/410, or the page itself says the posting is closed. Everything
    else -- a 403 from a bot-blocking CDN, a timeout, a 500, a redirect
    somewhere unexpected -- returns ``unknown`` and the job STAYS on the board.
    Wrongly dropping a live job is invisible to us and costly to the candidate;
    wrongly keeping a dead one is visible and self-correcting on the next pass.
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

# Phrases an ATS puts on the page when a requisition is closed but the URL
# still resolves 200. Every one of these is a whole sentence an ATS renders in
# place of the job -- none is a phrase that could appear in the body of a live
# posting, which is what keeps this from retiring healthy listings.
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
    """Strip markup so a marker inside a <script> blob cannot trigger a match."""
    try:
        html = body.decode("utf-8", errors="replace")
    except Exception:  # pragma: no cover - decode with errors= cannot raise
        return ""
    html = _TAG_RE.sub(" ", html)
    html = _MARKUP_RE.sub(" ", html)
    # Collapse whitespace and normalize the typographic apostrophes ATS
    # templates emit, so "job isn't available" matches the plain-ASCII marker.
    text = _WS_RE.sub(" ", html).lower()
    return text.replace("’", "'").replace("‘", "'")


@dataclass(frozen=True, slots=True)
class Liveness:
    """The verdict for one URL."""

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
    """Ask one posting URL whether it still exists.

    Never raises. Any failure this function cannot interpret becomes
    ``unknown``, which keeps the job published.
    """
    if not url or not url.lower().startswith(("http://", "https://")):
        return Liveness(url, UNKNOWN, "no fetchable url", checked_at=_now())

    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            # Ask for HTML explicitly. Some ATS hosts serve a JSON error body
            # with a 200 to clients that do not, which reads as a live page.
            "Accept": "text/html,application/xhtml+xml,application/json;q=0.8,*/*;q=0.5",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", None) or response.getcode()
            final_url = response.geturl()
            body = response.read(_MAX_BODY_BYTES)
    except urllib.error.HTTPError as exc:
        # The only codes that mean "this posting is gone". 403 in particular
        # does NOT: KBR's public job HTML 403s every non-browser fetcher while
        # the requisition is perfectly live, which is why the Workday adapter
        # reads the CXS JSON endpoint instead.
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

    # A redirect off the posting and onto a bare careers or search root is the
    # classic soft-expiry: the ATS 302s a dead requisition to its job search.
    # It is a strong hint but NOT proof -- vanity URLs and locale redirects
    # look identical -- so this reports live and lets the board show a hint.
    reason = "reachable"
    if final_url and _redirected_off_posting(url, final_url):
        reason = f"redirected to {final_url}"

    return Liveness(url, LIVE, reason, status, final_url, _now())


_POSTING_PATH_RE = re.compile(
    r"/(?:job|jobs|opening|position|posting|vacanc|requisition|career)s?[-/]"
    r"(?P<tail>[^/?#]+)",
    re.I,
)

# Path tails that mean "the list of jobs", not "one job". Landing on one of
# these is the soft-expiry signal; landing on a requisition id or slug is not.
_LISTING_TAIL_RE = re.compile(
    r"^(?:search|results?|list|index|all|browse|home|apply|overview)$", re.I
)


def _looks_like_a_posting(path: str) -> bool:
    match = _POSTING_PATH_RE.search(path)
    if not match:
        return False
    return not _LISTING_TAIL_RE.match(match.group("tail"))


def _redirected_off_posting(original: str, final: str) -> bool:
    """True when a URL that looked like a posting landed somewhere that does not."""
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
    """Check many URLs concurrently. Deduplicates before dispatching.

    ``workers`` stays modest on purpose: this hits a handful of employer ATS
    hosts, and a job board hammering a recruiter's careers page is how a bot
    earns a permanent block.
    """
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
