#!/usr/bin/env python3
"""Run the standards-panel watch. Fetches, compares, reports.

Split from ``tactical_research/watch.py`` on purpose: everything that decides
what counts as a change is pure and tested, and this file is only the part that
touches the network. It runs in CI because that is where outbound fetch works.

It writes the snapshot and never writes ``standards.json`` — section 6 puts a
person in charge of the table and the bot in charge of the alarm.
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from tactical_research.watch import missing_flags, report, sweep  # noqa: E402

HERE = Path(__file__).resolve().parent
STANDARDS = HERE / "tactical_research" / "standards.json"
SNAPSHOT = HERE / "standards-snapshot.json"

# Several .mil and .gov hosts sit behind filters that refuse a bare urllib
# request outright. A full browser header set clears some of them; the ones it
# does not are reported as refusals rather than treated as changes.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "no-cache",
}
TIMEOUT = 25

# Only these prove a page is gone. Everything else — 403, 429, a timeout — is
# the host declining to answer a robot, which says nothing about the standard.
GONE = (404, 410)


def fetch(url: str) -> tuple[str | None, int | None]:
    """(page, status). A page of None means we have no opinion this week.

    The status comes back so the caller can tell "this page is gone", which an
    editor needs to know, from "this host refused the robot", which they do not.
    """
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read(2_000_000).decode("utf-8", errors="replace"), 200
    except urllib.error.HTTPError as problem:
        print(f"  could not fetch {url}: HTTP {problem.code}", file=sys.stderr)
        return None, problem.code
    except (urllib.error.URLError, OSError, ValueError) as problem:
        print(f"  could not fetch {url}: {problem}", file=sys.stderr)
        return None, None


def main() -> int:
    rows = json.loads(STANDARDS.read_text(encoding="utf-8"))["rows"]
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}

    pages: dict[str, str] = {}
    gone: dict[str, int] = {}
    for row in rows:
        url = row.get("url", "")
        if not url:
            continue
        print(f"watching {row['name']}")
        html, status = fetch(url)
        if html is not None:
            pages[url] = html
        elif status in GONE:
            gone[url] = status

    refused = sum(1 for r in rows if r.get("url") and r["url"] not in pages and r["url"] not in gone)
    flags, updated = sweep(rows, pages, snapshot)
    flags = missing_flags(rows, gone) + flags

    text = report(flags)
    if refused:
        text += f"\n\n{refused} page(s) refused the request this run; their baselines are unchanged."
    print("\n" + text)

    SNAPSHOT.write_text(json.dumps(updated, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write("## Standards panel watch\n\n" + text + "\n")

    # A change is news for an editor, not a broken build. Exiting non-zero here
    # would mean a red check every time a standard is actually updated.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
