"""Small, dependency-free HTTP helper with a robots.txt gate.

Retail sites are not ours to hammer. Every page fetch goes through
:func:`allowed_by_robots` first, requests are spaced by ``min_interval``
per host, and the user agent says who we are. Logins, CAPTCHAs and paywalls
are never worked around: a 401/403 is reported, not retried.
"""

from __future__ import annotations

import gzip
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
from typing import Any

log = logging.getLogger(__name__)

USER_AGENT = "BabyGearScout/0.1 (personal price and recall tracker; stdlib urllib)"
DEFAULT_TIMEOUT = 30
RETRY_STATUSES = {429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    """A request that could not be completed."""


_robots_cache: dict[str, urllib.robotparser.RobotFileParser | None] = {}
_last_hit: dict[str, float] = {}


def allowed_by_robots(url: str) -> bool:
    """True when the site's robots.txt permits our user agent to fetch ``url``.

    An unreachable robots.txt is treated as "allowed" (the RFC 9309 default
    for a 4xx), but a 5xx or network failure is treated as "not allowed" --
    when in doubt, don't.
    """
    parts = urllib.parse.urlparse(url)
    origin = f"{parts.scheme}://{parts.netloc}"
    if origin not in _robots_cache:
        parser = urllib.robotparser.RobotFileParser()
        try:
            request = urllib.request.Request(f"{origin}/robots.txt", headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(request, timeout=15) as response:
                parser.parse(response.read().decode("utf-8", "replace").splitlines())
            _robots_cache[origin] = parser
        except urllib.error.HTTPError as exc:
            _robots_cache[origin] = None if 400 <= exc.code < 500 else parser
            if exc.code >= 500:
                parser.disallow_all = True
        except (urllib.error.URLError, TimeoutError, OSError):
            parser.disallow_all = True
            _robots_cache[origin] = parser
    cached = _robots_cache[origin]
    return True if cached is None else cached.can_fetch(USER_AGENT, url)


def _pace(url: str, min_interval: float) -> None:
    host = urllib.parse.urlparse(url).netloc
    wait = _last_hit.get(host, 0) + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    _last_hit[host] = time.monotonic()


def fetch(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 3,
    min_interval: float = 2.0,
) -> bytes:
    """GET ``url`` politely and return the raw body."""
    if params:
        separator = "&" if urllib.parse.urlparse(url).query else "?"
        url = f"{url}{separator}{urllib.parse.urlencode(params)}"
    headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    last_error: Exception | None = None
    for attempt in range(retries):
        if attempt:
            time.sleep(2.0**attempt)
        _pace(url, min_interval)
        try:
            request = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return body
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in RETRY_STATUSES:
                raise FetchError(f"HTTP {exc.code} for {url}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
    raise FetchError(f"{url} failed after {retries} attempts: {last_error}")


def fetch_json(url: str, **kwargs: Any) -> Any:
    body = fetch(url, **kwargs)
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise FetchError(f"{url} returned non-JSON body: {exc}") from exc
