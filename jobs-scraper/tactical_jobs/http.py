"""Small, dependency-free HTTP helper.

The whole project sticks to the standard library so it can run in a bare
GitHub Actions container with no install step. That means ``urllib`` plus a
little care around retries, timeouts, and identifying ourselves honestly.
"""

from __future__ import annotations

import gzip
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

log = logging.getLogger(__name__)

USER_AGENT = (
    "MOPsAndMOEs-JobsBot/1.0 "
    "(+https://www.mopsnmoes.com; tactical human performance job aggregator)"
)
"""Identify the bot and give operators a way to reach us.

Every source this project ships is a documented public JSON endpoint, but a
contactable user agent is still the right thing to send.
"""

DEFAULT_TIMEOUT = 30
RETRY_STATUSES = {429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    """A request that could not be completed after retries."""


def fetch(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, Any] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 3,
    backoff: float = 2.0,
) -> bytes:
    """GET ``url`` and return the raw body, retrying transient failures."""
    if params:
        separator = "&" if urllib.parse.urlparse(url).query else "?"
        url = f"{url}{separator}{urllib.parse.urlencode(params)}"

    request_headers = {
        "User-Agent": USER_AGENT,
        "Accept-Encoding": "gzip",
        **(headers or {}),
    }

    last_error: Exception | None = None
    for attempt in range(retries):
        if attempt:
            delay = backoff**attempt
            log.debug("retrying %s in %.1fs (attempt %d)", url, delay, attempt + 1)
            time.sleep(delay)
        try:
            request = urllib.request.Request(url, headers=request_headers)
            with urllib.request.urlopen(request, timeout=timeout) as response:
                body = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    body = gzip.decompress(body)
                return body
        except urllib.error.HTTPError as exc:
            last_error = exc
            # 4xx other than rate limiting will not fix themselves; stop early.
            if exc.code not in RETRY_STATUSES:
                raise FetchError(f"HTTP {exc.code} for {url}") from exc
            log.debug("retryable HTTP %d for %s", exc.code, url)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            log.debug("network error for %s: %s", url, exc)

    raise FetchError(f"{url} failed after {retries} attempts: {last_error}")


def fetch_json(url: str, **kwargs: Any) -> Any:
    """GET ``url`` and parse the response as JSON."""
    body = fetch(url, **kwargs)
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise FetchError(f"{url} returned non-JSON body: {exc}") from exc


def post_json(
    url: str,
    payload: Any,
    *,
    headers: dict[str, str] | None = None,
    timeout: int = DEFAULT_TIMEOUT,
) -> bytes:
    """POST ``payload`` as JSON. Used by the webhook/Discord publishers."""
    data = json.dumps(payload).encode()
    request_headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": "application/json",
        **(headers or {}),
    }
    request = urllib.request.Request(url, data=data, headers=request_headers, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise FetchError(f"POST {url} failed with HTTP {exc.code}: {exc.read()[:300]!r}") from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise FetchError(f"POST {url} failed: {exc}") from exc
