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

from .classify import Thresholds, classify
from .config import Config, ConfigError
from .models import JobPosting
from .pipeline import run
from .publishers import available_kinds as publisher_kinds
from .sources import available_kinds as source_kinds


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
    print("source kinds:    " + ", ".join(source_kinds()))
    print("publisher kinds: " + ", ".join(publisher_kinds()))
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
