"""Small, dependency-free HTTP helper.

Standard library only, so this runs in a bare GitHub Actions container with no
install step -- the same contract the jobs scraper holds itself to.
"""

from __future__ import annotations

import gzip
import json
import logging
import time
import urllib.error
import urllib.request
from typing import Any

log = logging.getLogger(__name__)

USER_AGENT = (
    "VybeFundingBot/1.0 "
    "(+https://github.com/jermrox/agency-agents; non-dilutive funding sweep)"
)

DEFAULT_TIMEOUT = 30
RETRY_STATUSES = {429, 500, 502, 503, 504}


class FetchError(RuntimeError):
    """A request that could not be completed after retries."""


def fetch(
    url: str,
    *,
    method: str = "GET",
    headers: dict[str, str] | None = None,
    body: bytes | None = None,
    timeout: int = DEFAULT_TIMEOUT,
    retries: int = 3,
) -> str:
    """Fetch a URL, retrying transient failures with linear backoff."""
    request_headers = {"User-Agent": USER_AGENT, "Accept-Encoding": "gzip"}
    if headers:
        request_headers.update(headers)

    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url, data=body, headers=request_headers, method=method
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                payload = response.read()
                if response.headers.get("Content-Encoding") == "gzip":
                    payload = gzip.decompress(payload)
                return payload.decode("utf-8", errors="replace")
        except urllib.error.HTTPError as exc:
            last_error = exc
            if exc.code not in RETRY_STATUSES or attempt == retries:
                raise FetchError(f"{url} returned HTTP {exc.code}") from exc
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            last_error = exc
            if attempt == retries:
                raise FetchError(f"{url} failed: {exc}") from exc
        sleep_for = attempt * 2
        log.warning("%s attempt %d/%d failed, retrying in %ds", url, attempt, retries, sleep_for)
        time.sleep(sleep_for)

    raise FetchError(f"{url} failed after {retries} attempts: {last_error}")


def fetch_json(url: str, **kwargs: Any) -> Any:
    """Fetch and parse JSON, failing loudly on a non-JSON body.

    A source that starts returning an HTML error page is a real failure worth
    surfacing -- silently treating it as "zero opportunities" is exactly the
    bug that makes an aggregator quietly go stale.
    """
    raw = fetch(url, **kwargs)
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise FetchError(f"{url} did not return JSON: {raw[:200]!r}") from exc


def post_json(url: str, payload: dict[str, Any], **kwargs: Any) -> Any:
    """POST a JSON body and parse the JSON response."""
    body = json.dumps(payload).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    headers.update(kwargs.pop("headers", {}) or {})
    return fetch_json(url, method="POST", body=body, headers=headers, **kwargs)
