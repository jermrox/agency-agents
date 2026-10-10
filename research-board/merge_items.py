#!/usr/bin/env python3
"""Fold a sweep's new items into findings.json, one item per document.

    python merge_items.py new1.json [new2.json ...]

Each input is ``{"items": [...], "coverage_additions": [{"primary_url", "coverage_url"}]}``.
An incoming item that resolves to a document already on file (same normalised
URL, or a shared identifier) does not become a second item: its coverage is
folded into the existing one, and the higher-scoring write-up is kept. Nothing
already on file is dropped. The merged file is validated before it is written.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from tactical_research.models import BoardItem, dump, load  # noqa: E402

FINDINGS = HERE / "findings.json"


def norm_url(url: str) -> str:
    url = (url or "").strip().lower().replace("http://", "https://")
    url = re.sub(r"[?#].*$", "", url).rstrip("/")
    return url.replace("://www.", "://")


def keys(item: BoardItem) -> list[tuple[str, str]]:
    found = [("url", norm_url(item.primary_url))]
    for part in re.split(r"[;,]\s*", item.identifier or ""):
        part = re.sub(r"[^a-z0-9./]", "", part.lower())
        if part:
            found.append(("id", part))
    return found


def merge(existing: list[BoardItem], incoming: list[BoardItem], coverage: list[dict] = ()) -> tuple[list[BoardItem], int]:
    """(merged items, number of genuinely new items)."""
    items = list(existing)
    index: dict[tuple[str, str], int] = {}
    for pos, item in enumerate(items):
        for key in keys(item):
            index.setdefault(key, pos)

    added = 0
    for item in incoming:
        hit = next((index[k] for k in keys(item) if k in index), None)
        if hit is None:
            hit = len(items)
            items.append(item)
            added += 1
        else:
            kept = items[hit]
            union = kept.coverage_urls + [u for u in item.coverage_urls if u not in kept.coverage_urls]
            if item.score > kept.score:
                item.coverage_urls = union
                item.first_seen = kept.first_seen or item.first_seen
                items[hit] = item
            else:
                kept.coverage_urls = union
        for key in keys(items[hit]):
            index.setdefault(key, hit)

    by_url = {norm_url(i.primary_url): i for i in items}
    for row in coverage:
        target = by_url.get(norm_url(row.get("primary_url", "")))
        url = row.get("coverage_url", "")
        if target and url and url not in target.coverage_urls:
            target.coverage_urls.append(url)

    items.sort(key=lambda i: i.date_published, reverse=True)
    return items, added


def main(argv: list[str]) -> int:
    existing = load(FINDINGS) if FINDINGS.exists() else []
    incoming: list[BoardItem] = []
    coverage: list[dict] = []
    for path in argv:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        incoming += [BoardItem(**row) for row in data.get("items", [])]
        coverage += data.get("coverage_additions", [])

    merged, added = merge(existing, incoming, coverage)
    problems = [(i.headline, p) for i in merged for p in i.validate()]
    if problems:
        for headline, problem in problems:
            print(f"  invalid: {headline} — {problem}", file=sys.stderr)
        return 1
    dump(merged, FINDINGS)
    print(f"{added} new item(s); {len(incoming) - added} folded into existing documents; {len(merged)} on file")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
