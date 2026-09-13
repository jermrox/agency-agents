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

from tactical_research.watch import report, sweep  # noqa: E402

HERE = Path(__file__).resolve().parent
STANDARDS = HERE / "tactical_research" / "standards.json"
SNAPSHOT = HERE / "standards-snapshot.json"

# Several .mil and .gov hosts refuse a bare urllib user agent outright.
UA = "Mozilla/5.0 (compatible; tactical-hp-board standards watch; +https://github.com/jermrox/agency-agents)"
TIMEOUT = 25


def fetch(url: str) -> str | None:
    """The page, or None if the host did not give us one.

    None means "no opinion this week", not "the page is empty" — a 403 from a
    bot filter is the host refusing the robot, not the standard disappearing.
    """
    request = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            raw = response.read(2_000_000)
        return raw.decode("utf-8", errors="replace")
    except (urllib.error.URLError, urllib.error.HTTPError, OSError, ValueError) as problem:
        print(f"  could not fetch {url}: {problem}", file=sys.stderr)
        return None


def main() -> int:
    rows = json.loads(STANDARDS.read_text(encoding="utf-8"))["rows"]
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}

    pages: dict[str, str] = {}
    for row in rows:
        url = row.get("url", "")
        if not url:
            continue
        print(f"watching {row['name']}")
        html = fetch(url)
        if html is not None:
            pages[url] = html

    unreachable = sum(1 for r in rows if r.get("url") and r["url"] not in pages)
    flags, updated = sweep(rows, pages, snapshot)

    text = report(flags)
    if unreachable:
        text += f"\n\n{unreachable} page(s) could not be fetched this run; their baselines are unchanged."
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
