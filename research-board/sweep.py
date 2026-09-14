#!/usr/bin/env python3
"""The weekly sweep. Crawl the registry, resolve to primary documents, fetch.

This is the network half, and it runs in CI because that is the only place
outbound fetch works. Everything it decides is in ``tactical_research`` and
tested without a network; this file is the part that talks to hosts.

What it produces is deliberately *not* a finished board. It emits
``candidates.json``: one entry per clustered primary document, carrying the
fetched text a blurb has to be written from. The brief is explicit that a blurb
comes from the document rather than from coverage of it — "the agent cannot get
context right from search snippets any better than those outlets did" — so the
sweep's job is to put the document in front of whoever writes, and no more. It
never invents a blurb, and an unreadable page never becomes a candidate.

    python sweep.py                 # crawl, cluster, fetch, write candidates.json
    python sweep.py --render        # findings.json -> board.html + archive.html
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from tactical_research import models  # noqa: E402
from tactical_research.cluster import Sighting, cluster  # noqa: E402
from tactical_research.extract import document, links  # noqa: E402
from tactical_research.identifiers import is_fetchable  # noqa: E402
from tactical_research.render import render_archive, render_board  # noqa: E402

PKG = HERE / "tactical_research"
SOURCES = PKG / "sources.json"
CANDIDATES = HERE / "candidates.json"
FINDINGS = HERE / "findings.json"
OUT = HERE / "site"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
TIMEOUT = 25
MAX_BYTES = 2_000_000

# Per listing page. A source that offers two hundred links is offering its
# whole archive, and following all of it every week buys nothing: the window
# rule throws away anything older than a month anyway.
LINKS_PER_SOURCE = 40

# Only these prove a page is gone. Everything else — 403, 429, a timeout — is
# the host declining to answer a robot, which says nothing about the entry.
GONE = (404, 410)

# How far back a sighting can be dated and still be worth fetching. Wider than
# the 30-day board on purpose — an item published just outside the window may
# still be the primary document a fresh piece of coverage points at.
LOOKBACK_DAYS = 45


def fetch(url: str) -> tuple[str | None, int | None]:
    """(page, status). None means we have no opinion about this URL."""
    request = urllib.request.Request(url, headers=HEADERS)
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            return response.read(MAX_BYTES).decode("utf-8", errors="replace"), 200
    except urllib.error.HTTPError as problem:
        return None, problem.code
    except (urllib.error.URLError, OSError, ValueError):
        return None, None


def gather(sources: list[dict]) -> tuple[list[Sighting], dict]:
    """Crawl every source listing and turn its links into sightings."""
    sightings: list[Sighting] = []
    tally = {"sources": 0, "refused": 0, "gone": 0, "links": 0, "empty": 0}
    quiet: list[str] = []          # crawled fine, offered nothing

    for source in sources:
        url = source.get("url", "")
        if not url:
            continue
        html, status = fetch(url)
        if html is None:
            # Gone and refused are different problems with different fixes, and
            # collapsing them is how a dead registry entry hides behind a bot
            # filter. A 404 needs the entry repointed; a 403 is the host
            # declining the robot and the entry may be perfectly correct.
            if status in GONE:
                tally["gone"] += 1
                quiet.append(f"{source['name']} (HTTP {status} — the page is gone)")
                print(f"  GONE: {source['name']} — HTTP {status}", file=sys.stderr)
            else:
                tally["refused"] += 1
                where = f"HTTP {status}" if status else "no response"
                quiet.append(f"{source['name']} (refused: {where})")
                print(f"  refused: {source['name']} — {where}", file=sys.stderr)
            continue
        tally["sources"] += 1

        found = links(html, url)[:LINKS_PER_SOURCE]
        tally["links"] += len(found)
        print(f"  {source['name']}: {len(found)} links")
        if not found:
            # A 200 that yielded no links is a source contributing nothing —
            # usually a JavaScript app that renders its listing client-side.
            # Left unsaid it is indistinguishable from a quiet week, which is
            # how a registry rots while every run stays green.
            tally["empty"] += 1
            quiet.append(f"{source['name']} (0 links)")
        for link in found:
            sightings.append(
                Sighting(
                    title=link.title,
                    url=link.url,
                    # Trade press is coverage by policy, not by guesswork: the
                    # registry marks it, and an event exception only applies to
                    # sources that are not coverage-only.
                    is_event="Event pages" in source.get("name", ""),
                )
            )
    tally["quiet_sources"] = quiet
    return sightings, tally


def read_documents(items, today) -> tuple[list[dict], dict]:
    """Fetch each clustered item's primary document and keep what we can read."""
    candidates: list[dict] = []
    tally = {"fetched": 0, "unreadable": 0, "refused": 0, "stale": 0}
    horizon = today - timedelta(days=LOOKBACK_DAYS)

    for item in items:
        if not is_fetchable(item.primary_url) and not item.from_coverage:
            continue
        html, status = fetch(item.primary_url)
        if html is None:
            tally["refused"] += 1
            continue

        doc = document(html)
        if not doc.is_readable:
            # A 200 that yielded nothing readable — a JavaScript shell, a login
            # wall, a PDF we cannot decode. Writing a blurb from this would mean
            # writing it from the headline, which is the failure the brief names.
            tally["unreadable"] += 1
            continue

        published = doc.published or item.published
        if published:
            try:
                when = datetime.strptime(published[:10], "%Y-%m-%d").date()
            except ValueError:
                when = None
            if when and when < horizon:
                tally["stale"] += 1
                continue

        tally["fetched"] += 1
        candidates.append(
            {
                "primary_url": item.primary_url,
                "identifier": item.identifier.value if item.identifier else "",
                "source_title": item.title,
                "document_title": doc.title,
                "date_published": published,
                "coverage_urls": item.coverage_urls,
                "from_coverage": item.from_coverage,
                "excerpt": doc.excerpt,
            }
        )
    return candidates, tally


def render() -> int:
    """findings.json -> the two pages. Deterministic, no network."""
    if not FINDINGS.exists():
        print(f"No {FINDINGS.name}: nothing to render yet.", file=sys.stderr)
        return 1
    items = models.load(FINDINGS)
    problems = [(i.headline, p) for i in items for p in i.validate()]
    if problems:
        for headline, problem in problems:
            print(f"  invalid: {headline or '(untitled)'} — {problem}", file=sys.stderr)
        print(f"{len(problems)} schema problem(s); refusing to render.", file=sys.stderr)
        return 1

    OUT.mkdir(exist_ok=True)
    (OUT / "board.html").write_text(render_board(items), encoding="utf-8")
    (OUT / "archive.html").write_text(render_archive(items), encoding="utf-8")
    board, archive = models.split_window(items)
    print(f"Rendered {len(board)} board items and {len(archive)} archive items into {OUT}/")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--render", action="store_true", help="render findings.json and stop")
    args = parser.parse_args(argv)
    if args.render:
        return render()

    today = datetime.now(timezone.utc).date()
    sources = json.loads(SOURCES.read_text(encoding="utf-8"))["sources"]
    print(f"Crawling {len(sources)} sources")
    sightings, crawl = gather(sources)

    items = cluster(sightings)
    print(f"\n{len(sightings)} sightings clustered into {len(items)} items")

    candidates, read = read_documents(items, today)

    quiet = crawl.pop("quiet_sources", [])
    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "window_days": models.WINDOW_DAYS,
        "counts": {**crawl, **read, "candidates": len(candidates)},
        "quiet_sources": quiet,
        "candidates": candidates,
    }
    CANDIDATES.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(
        f"\n{len(candidates)} candidates written to {CANDIDATES.name}\n"
        f"  {crawl['sources']} sources crawled, {crawl['refused']} refused, "
        f"{crawl['gone']} gone, {crawl['empty']} returned nothing\n"
        f"  {read['refused']} documents refused, {read['unreadable']} unreadable, "
        f"{read['stale']} outside the {LOOKBACK_DAYS}-day lookback"
    )
    if quiet:
        print("\nContributing nothing this run — check whether the source moved:")
        for name in quiet:
            print(f"  - {name}")
    print(
        "\nBlurbs are not written here. Each candidate carries the document text "
        "they have to be written from."
    )
    # A quiet week is a real answer, not a failure.
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
