#!/usr/bin/env python3
"""Inject funding.json into the dashboard's built-in list.

WHY THIS EXISTS
The dashboard carries a built-in opportunity list so the page still renders
when funding.json is unreachable -- offline, or published somewhere the
relative fetch does not resolve (a Claude artifact, an embed). That fallback is
only useful if it stays current, and a hand-maintained copy of a 50-row list
drifts within a week.

So the built-in list is generated, never edited: sources.toml is the single
source of truth, the sweep renders it to funding.json, and this script writes
that into the page between two markers. The runtime fetch still runs on top,
so a deployed page picks up a fresher sweep than the one baked in at build.

    python3 scripts/sync-funding-dashboard.py

Idempotent. Fails loudly if the markers are missing rather than writing a page
with a silently empty table.
"""

from __future__ import annotations

import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FEED = ROOT / "funding-scraper" / "output" / "funding.json"
PAGE = ROOT / "dashboards" / "vybe-funding-tracker.html"
PACKETS = ROOT / "funding-scraper" / "applications" / "packets.py"

BEGIN = "  // >>> GENERATED: built-in opportunity list (scripts/sync-funding-dashboard.py)"
END = "  // <<< END GENERATED"

# The dashboard's row shape differs from the feed's: it renders `type` for its
# filter chips, where the feed carries the richer `kind`.
KIND_TO_TYPE = {
    "credit": "grant",
    "partnership": "grant",
    "accelerator": "accelerator",
    "visibility": "visibility",
    "grant": "grant",
}


def js_string(value: str) -> str:
    """Emit a single-quoted JS string literal, escaped."""
    return "'" + str(value or "").replace("\\", "\\\\").replace("'", "\\'").replace("\n", " ") + "'"


def _packets(rows: list[dict]) -> list[dict]:
    """The drafted application packets that match a row on the board.

    The board's first line names the next one to file (lesson 15 Oct, rule 8).
    A packet counts only while its programme is still a board row: one that was
    removed (expired, fee-charging, rejected) must never be the line a founder
    acts on.
    """
    if not PACKETS.exists():
        return []
    spec = importlib.util.spec_from_file_location("vybe_packets", PACKETS)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    by_url = {r.get("url"): r for r in rows}
    out = []
    for pk in getattr(mod, "PACKETS", []):
        row = by_url.get(pk.get("url"))
        if row is None:
            key = str(pk.get("name", "")).lower()[:18]
            row = next((r for r in rows if r.get("name", "").lower().startswith(key)), None)
        if row is None:
            continue
        out.append({
            "id": pk["id"],
            "name": pk["name"],
            "deadline": str(pk.get("deadline") or "rolling"),
            "fee": pk.get("fee") or "",
            "sam": row.get("sam") or "",
            "big_name": row.get("big_name") or 0,
        })
    return out


def main() -> int:
    if not FEED.exists():
        print(f"error: {FEED} missing — run the sweep first", file=sys.stderr)
        return 2
    if not PAGE.exists():
        print(f"error: {PAGE} missing", file=sys.stderr)
        return 2

    feed = json.loads(FEED.read_text(encoding="utf-8"))
    rows = feed.get("opportunities", [])
    if not rows:
        print("error: feed contains no opportunities; refusing to blank the page", file=sys.stderr)
        return 2

    lines = [BEGIN, "  var GRANTS = ["]
    for row in rows:
        parts = [
            f"id:{js_string(row['id'])}",
            f"name:{js_string(row['name'])}",
            f"type:{js_string(KIND_TO_TYPE.get(row.get('kind', 'grant'), 'grant'))}",
            f"amount:{js_string(row.get('amount') or 'see program')}",
            f"url:{js_string(row['url'])}",
            f"deadline:{js_string(row['close_date']) if row.get('close_date') else 'null'}",
            f"note:{js_string(row.get('summary') or row.get('eligibility') or '')}",
        ]
        # Emitted whenever the feed has one, past or future: the page decides
        # what it means by comparing it to the clock. Filtering to future dates
        # here would bake the sweep date into the page, so a row generated in
        # September would still read "not open yet" when served in November.
        if row.get("open_date"):
            parts.append(f"opens:{js_string(row['open_date'])}")
        if row.get("sam"):
            parts.append(f"sam:{js_string(row['sam'])}")
        docs = row.get("documents") or []
        if docs:
            parts.append("documents:[" + ",".join(js_string(d) for d in docs) + "]")
        lines.append("    {" + ", ".join(parts) + "},")
    lines.append("  ];")
    lines.append("  var PACKETS = [")
    for pk in _packets(rows):
        lines.append(
            "    {" + ", ".join([
                f"id:{js_string(pk['id'])}",
                f"name:{js_string(pk['name'])}",
                f"deadline:{js_string(pk['deadline'])}",
                f"fee:{js_string(pk['fee'])}",
                f"sam:{js_string(pk['sam'])}",
                f"big_name:{int(pk['big_name'])}",
            ]) + "},"
        )
    lines.append("  ];")
    lines.append(END)

    page = PAGE.read_text(encoding="utf-8")
    block = "\n".join(lines)

    if BEGIN in page and END in page:
        page = re.sub(
            re.escape(BEGIN) + r".*?" + re.escape(END),
            lambda _: block,
            page,
            flags=re.DOTALL,
        )
    else:
        # First run: replace the hand-written array wholesale.
        match = re.search(r"  var GRANTS = \[.*?\n  \];", page, flags=re.DOTALL)
        if not match:
            print("error: could not find the GRANTS array or its markers", file=sys.stderr)
            return 2
        page = page[: match.start()] + block + page[match.end() :]

    PAGE.write_text(page, encoding="utf-8")
    print(f"synced {len(rows)} opportunities into {PAGE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
