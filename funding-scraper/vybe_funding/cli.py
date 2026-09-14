"""Run the sweep, write funding.json, report what changed.

    python3 -m vybe_funding run --config sources.toml
    python3 -m vybe_funding run --config sources.toml --dry-run

A source that fails is logged and skipped -- one dead endpoint must never take
down the whole sweep, because a board that fails to publish is worse than a
board missing one agency.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
import tomllib
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from .models import Opportunity
from .sources import build
from .sources.curated import stale_entries

log = logging.getLogger("vybe_funding")

DEFAULT_STALE_DAYS = 45

# Stop calling a detail endpoint that is not answering. grants.gov's
# fetchOpportunity timed out on essentially every row, and at one call per row
# that is twenty minutes of sweep spent learning what the first three calls
# already said. A dead endpoint costs three timeouts now, not a hundred.
ENRICH_FAILURE_BUDGET = 3


def load_config(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def collect(config: dict[str, Any]) -> tuple[list[Opportunity], list[str]]:
    """Run every configured source. Returns (opportunities, error messages)."""
    found: list[Opportunity] = []
    errors: list[str] = []

    for name, options in config.get("sources", {}).items():
        if not isinstance(options, dict) or not options.get("enabled", True):
            continue
        try:
            source = build(name, options)
            fetched = list(source.fetch())
            rows = [row for row in fetched if source.relevant(row)]
            dropped = len(fetched) - len(rows)
            # Report the drop rather than just the survivors: a filter that
            # quietly eats a whole source looks identical to a dead API.
            if dropped:
                log.info(
                    "%-14s %3d opportunities (%d off-topic dropped)",
                    name, len(rows), dropped,
                )
            else:
                log.info("%-14s %3d opportunities", name, len(rows))
            # Detail lookups run only on rows that survived the filter, so the
            # request count tracks the board, not the search. One row's detail
            # failing must never cost the run the row itself.
            enriched = 0
            consecutive_failures = 0
            gave_up = False
            for row in rows:
                if consecutive_failures >= ENRICH_FAILURE_BUDGET:
                    gave_up = True
                    break
                try:
                    before = (row.summary, row.eligibility, row.amount)
                    source.enrich(row)
                    if (row.summary, row.eligibility, row.amount) != before:
                        enriched += 1
                    consecutive_failures = 0
                except Exception as exc:  # noqa: BLE001 - detail is optional
                    consecutive_failures += 1
                    log.debug("%s: detail lookup failed for %r: %s", name, row.name, exc)
            if gave_up:
                log.warning(
                    "%-14s detail lookups abandoned after %d consecutive failures",
                    name, ENRICH_FAILURE_BUDGET,
                )
            elif enriched:
                log.info("%-14s %3d detail lookups filled", name, enriched)

            found.extend(rows)
        except Exception as exc:  # noqa: BLE001 - one bad source must not end the run
            message = f"{name}: {exc}"
            log.error("%-14s FAILED  %s", name, exc)
            errors.append(message)

    return found, errors


def deduplicate(opportunities: list[Opportunity]) -> list[Opportunity]:
    """Collapse the same opportunity arriving from two sources.

    Curated entries win over API rows on a collision: a human-checked amount
    and eligibility note is more useful on the board than a raw API title.
    """
    by_fingerprint: dict[str, Opportunity] = {}
    for opp in opportunities:
        key = opp.id
        existing = by_fingerprint.get(key)
        if existing is None or (opp.source == "curated" and existing.source != "curated"):
            by_fingerprint[key] = opp
    return list(by_fingerprint.values())


def publish(opportunities: list[Opportunity], output_dir: Path, today: date, errors: list[str]) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "funding.json"

    rows = [opp.to_dict(today) for opp in opportunities]
    # Soonest real deadline first; rolling after; closed last. Same ordering the
    # dashboard applies, so the file reads correctly even opened raw.
    rank = {"soon": 0, "open": 1, "rolling": 2, "closed": 3}
    rows.sort(key=lambda r: (rank.get(r["status"], 9), r["days_left"] if r["days_left"] is not None else 9999, r["name"]))

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": today.isoformat(),
        "count": len(rows),
        "source_errors": errors,
        "opportunities": rows,
    }
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def summarize(opportunities: list[Opportunity], today: date, stale_days: int) -> None:
    buckets: dict[str, int] = {}
    for opp in opportunities:
        buckets[opp.status(today)] = buckets.get(opp.status(today), 0) + 1

    log.info("-" * 58)
    for status in ("soon", "open", "rolling", "closed"):
        if buckets.get(status):
            log.info("%-8s %3d", status, buckets[status])

    urgent = sorted(
        (o for o in opportunities if o.status(today) == "soon"),
        key=lambda o: o.days_left(today) or 0,
    )
    if urgent:
        log.info("-" * 58)
        log.info("Closing within 30 days:")
        for opp in urgent:
            log.info("  %3dd  %s", opp.days_left(today), opp.name[:70])

    stale = stale_entries(opportunities, today, stale_days)
    if stale:
        log.warning("-" * 58)
        log.warning("Curated entries needing re-verification (>%dd old):", stale_days)
        for name, age in stale:
            log.warning("  %3dd  %s", age, name[:70])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="vybe_funding")
    sub = parser.add_subparsers(dest="command", required=True)

    run = sub.add_parser("run", help="collect and publish")
    run.add_argument("--config", type=Path, default=Path("sources.toml"))
    run.add_argument("--dry-run", action="store_true", help="collect and report without writing")
    run.add_argument("--verbose", "-v", action="store_true")

    args = parser.parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if getattr(args, "verbose", False) else logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    if not args.config.exists():
        log.error("config not found: %s", args.config)
        return 2

    config = load_config(args.config)
    runtime = config.get("runtime", {})
    today = date.today()

    opportunities, errors = collect(config)
    opportunities = deduplicate(opportunities)
    summarize(opportunities, today, int(runtime.get("stale_days", DEFAULT_STALE_DAYS)))

    if args.dry_run:
        log.info("-" * 58)
        log.info("dry run -- nothing written (%d opportunities)", len(opportunities))
        return 1 if errors else 0

    target = publish(opportunities, Path(runtime.get("output_dir", "output")), today, errors)
    log.info("-" * 58)
    log.info("wrote %s (%d opportunities)", target, len(opportunities))

    # A failed source is a non-zero exit so CI surfaces it, but the file is
    # still written: a partially-fresh board beats no board.
    return 1 if errors else 0
