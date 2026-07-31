"""Command-line entry point.

    python -m tactical_jobs run --config sources.toml
    python -m tactical_jobs run --config sources.toml --dry-run
    python -m tactical_jobs classify --title "..." --description "..."
    python -m tactical_jobs sources
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from .archive import Archive
from .classify import Thresholds, classify
from .config import Config, ConfigError
from .discover import discover, render_watchlist
from .insights import build_insights, render_summary
from .models import JobPosting
from .pipeline import run
from .publishers import available_kinds as publisher_kinds
from .report import render_html, render_markdown
from .sources import available_kinds as source_kinds
from .sources import keyless_kinds


def _configure_logging(verbose: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if verbose else logging.INFO,
        format="%(levelname)-7s %(name)s: %(message)s",
        stream=sys.stderr,
    )


def _cmd_run(args: argparse.Namespace) -> int:
    config = Config.load(args.config)
    if args.dry_run:
        print("DRY RUN — no publishing, no state changes\n", file=sys.stderr)
    report = run(config, dry_run=args.dry_run)
    print(report.summary())

    if args.dry_run and (report.approved or report.review):
        print("\n--- would queue ---")
        for posting in sorted(
            [*report.approved, *report.review], key=lambda p: p.score, reverse=True
        ):
            location = posting.location or "n/a"
            print(f"  [{posting.score:5.1f}] {posting.title} — {posting.employer} ({location})")
            print(f"          {posting.url}")

    # A run where every source failed is a failed run, even though the
    # pipeline survived it -- surface that to the scheduler via exit code.
    if report.errors and report.fetched == 0:
        return 1
    return 0


def _cmd_classify(args: argparse.Namespace) -> int:
    """Score one hypothetical posting. Useful for tuning thresholds."""
    posting = JobPosting(
        source="cli",
        source_id="cli",
        url="https://example.invalid/job",
        title=args.title,
        employer=args.employer or "",
        location=args.location or "",
        description=args.description or "",
    )
    verdict = classify(posting, Thresholds())
    result = posting.to_public_dict()
    result["verdict"] = verdict
    result.pop("description", None)
    print(json.dumps(result, indent=2))
    return 0


def _cmd_sources(_: argparse.Namespace) -> int:
    keyless = set(keyless_kinds())
    print("source kinds (* = needs an API key):")
    for kind in source_kinds():
        print(f"  {kind}{'' if kind in keyless else ' *'}")
    print(f"\n{len(keyless)}/{len(source_kinds())} usable with no credentials.")
    print("publisher kinds: " + ", ".join(publisher_kinds()))
    return 0


def _cmd_insights(args: argparse.Namespace) -> int:
    """Rebuild the digest and dashboard from the archive without re-fetching."""
    archive = Archive.load(args.archive)
    records = archive.records()
    if not records:
        print(f"no records in {args.archive}", file=sys.stderr)
        return 1

    insights = build_insights(records)
    if args.json:
        print(json.dumps(insights, indent=2))
        return 0

    print(render_summary(insights))
    if args.out:
        out = Path(args.out)
        out.mkdir(parents=True, exist_ok=True)
        (out / "insights.json").write_text(json.dumps(insights, indent=2) + "\n")
        (out / "digest.md").write_text(render_markdown(insights))
        (out / "dashboard.html").write_text(render_html(insights))
        print(f"\nwrote digest.md, dashboard.html, insights.json -> {out}", file=sys.stderr)
    return 0


def _cmd_discover(args: argparse.Namespace) -> int:
    """Mine text for candidate employers and unknown vocabulary.

    Point it at podcast show notes, newsletters, or any corpus describing this
    industry -- the output is a watchlist worksheet, never a live config.
    """
    texts: list[str] = []
    for path in args.paths:
        target = Path(path)
        if target.is_dir():
            texts.extend(
                child.read_text(errors="replace")
                for child in sorted(target.rglob("*"))
                if child.is_file()
            )
        elif target.exists():
            texts.append(target.read_text(errors="replace"))
        else:
            print(f"skipping missing path: {path}", file=sys.stderr)

    if not texts and not sys.stdin.isatty():
        texts.append(sys.stdin.read())
    if not texts:
        print("nothing to analyze: pass file paths or pipe text on stdin", file=sys.stderr)
        return 2

    result = discover(texts, min_mentions=args.min_mentions)
    print(render_watchlist(result, limit=args.limit))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tactical_jobs",
        description="Aggregate tactical human performance jobs and publish them.",
    )
    parser.add_argument("-v", "--verbose", action="store_true", help="debug logging")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="fetch, classify, and publish")
    run_parser.add_argument("--config", default="sources.toml", help="path to config TOML")
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="score and report without publishing or writing state",
    )
    run_parser.set_defaults(func=_cmd_run)

    classify_parser = subparsers.add_parser(
        "classify", help="score a single posting (for tuning)"
    )
    classify_parser.add_argument("--title", required=True)
    classify_parser.add_argument("--employer")
    classify_parser.add_argument("--location")
    classify_parser.add_argument("--description")
    classify_parser.set_defaults(func=_cmd_classify)

    sources_parser = subparsers.add_parser("sources", help="list available adapters")
    sources_parser.set_defaults(func=_cmd_sources)

    insights_parser = subparsers.add_parser(
        "insights", help="rebuild the digest and dashboard from the archive"
    )
    insights_parser.add_argument("--archive", default="state/corpus.jsonl")
    insights_parser.add_argument(
        "--out", help="directory to write digest.md, dashboard.html, insights.json"
    )
    insights_parser.add_argument(
        "--json", action="store_true", help="print the raw insights JSON instead"
    )
    insights_parser.set_defaults(func=_cmd_insights)

    discover_parser = subparsers.add_parser(
        "discover", help="mine text for candidate employers and vocabulary"
    )
    discover_parser.add_argument(
        "paths", nargs="*", help="files or directories; reads stdin when omitted"
    )
    discover_parser.add_argument("--min-mentions", type=int, default=2)
    discover_parser.add_argument("--limit", type=int, default=40)
    discover_parser.set_defaults(func=_cmd_discover)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    _configure_logging(args.verbose)
    try:
        return args.func(args)
    except ConfigError as exc:
        print(f"config error: {exc}", file=sys.stderr)
        return 2
    except KeyboardInterrupt:  # pragma: no cover
        return 130


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
