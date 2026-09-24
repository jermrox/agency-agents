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

from .models import Opportunity, parse_date
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


def collect(
    config: dict[str, Any], only: set[str] | None = None
) -> tuple[list[Opportunity], list[str], set[str]]:
    """Run every configured source. Returns (opportunities, error messages).

    ``only`` restricts the run to the named sources. That exists for one
    reason: proving a newly written adapter. Without it the only way to see
    what a new source actually returns is to publish it, which is backwards --
    a wrong row on the board is the expensive mistake, not a slow run.
    """
    found: list[Opportunity] = []
    errors: list[str] = []
    failed: set[str] = set()

    for name, options in config.get("sources", {}).items():
        if not isinstance(options, dict):
            continue
        if only:
            if name not in only:
                continue
            # Naming a source explicitly overrides `enabled = false`. A source
            # is disabled precisely because it is not trustworthy yet, and
            # running it read-only is how it stops being untrustworthy --
            # honouring the flag here would lock out the only way to fix it.
        elif not options.get("enabled", True):
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
            failed.add(name)

    return found, errors, failed


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


def publish(
    opportunities: list[Opportunity],
    output_dir: Path,
    today: date,
    errors: list[str],
    failed_sources: set[str] | None = None,
) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "funding.json"

    rows = [opp.to_dict(today) for opp in opportunities]

    # A source that FAILED contributes nothing, and publishing that as-is
    # deletes every row it used to carry. That is how a real opportunity with
    # a live deadline silently leaves the board: DSIP started returning 403
    # after several long walks, and the Navy wearable topic closing in six
    # days simply vanished from the published feed. An upstream outage is not
    # evidence that an opportunity ended.
    #
    # Rows are keyed on the source LABEL they carry (`source`), not the config
    # block name, because that is what the published file records. A label
    # that produced rows this run is live, so anything of its that is missing
    # now is genuinely gone -- filtered out or closed -- and is NOT carried.
    # Only a label that vanished entirely, in a run that also had a failure,
    # gets its rows carried. That can under-protect but never over-carries.
    #
    # Carried rows keep their own close date and have their status recomputed,
    # so a genuinely expired one still goes closed on schedule.
    if failed_sources and target.exists():
        try:
            previous = json.loads(target.read_text(encoding="utf-8"))
            live_labels = {r.get("source") for r in rows}
            known_ids = {r.get("id") for r in rows}
            carried: list[str] = []
            for row in previous.get("opportunities", []):
                if row.get("source") in live_labels or row.get("id") in known_ids:
                    continue
                close = parse_date(row.get("close_date"))
                if close is not None and close < today:
                    continue  # genuinely expired -- let it go
                row = dict(row)
                row["stale"] = True
                # Say so on the row itself, not only in the JSON: a reader of
                # the board has no other way to know this one was not rechecked.
                marker = "Not refreshed this run — its source was unreachable."
                existing_note = (row.get("summary") or "").strip()
                if marker not in existing_note:
                    row["summary"] = f"{marker} {existing_note}".strip()
                if close is not None:
                    row["days_left"] = (close - today).days
                    row["status"] = "soon" if row["days_left"] <= 30 else "open"
                rows.append(row)
                carried.append(row.get("source", "?"))
            if carried:
                log.warning(
                    "carried %d row(s) forward from %s -- the source failed this "
                    "run and its rows were not refreshed",
                    len(carried), ", ".join(sorted(set(carried))),
                )
        except (OSError, ValueError) as exc:
            log.warning("could not carry rows forward from %s: %s", target, exc)
    # Soonest real deadline first; rolling after; closed last. Same ordering the
    # dashboard applies, so the file reads correctly even opened raw.
    rank = {"soon": 0, "open": 1, "rolling": 2, "closed": 3}
    rows.sort(key=lambda r: (rank.get(r["status"], 9), r["days_left"] if r["days_left"] is not None else 9999, r["name"]))

    payload = {
        "generated": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "as_of": today.isoformat(),
        "count": len(rows),
        "source_errors": errors,
        "stale_sources": sorted(failed_sources or ()),
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
    run.add_argument(
        "--only",
        action="append",
        metavar="SOURCE",
        help="run only this source, repeatable. Implies --dry-run: a partial "
             "collection must never overwrite a whole board.",
    )

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

    only = set(args.only or ())
    if only:
        known = set(config.get("sources", {}))
        unknown = sorted(only - known)
        if unknown:
            log.error("unknown source(s): %s", ", ".join(unknown))
            log.error("known: %s", ", ".join(sorted(known)))
            return 2
        # Publishing a subset would silently delete every row the skipped
        # sources contribute, so --only is read-only by construction.
        args.dry_run = True

    opportunities, errors, failed = collect(config, only)
    opportunities = deduplicate(opportunities)
    summarize(opportunities, today, int(runtime.get("stale_days", DEFAULT_STALE_DAYS)))

    if args.dry_run:
        if args.verbose:
            # The point of a dry run on a new adapter is to read what it
            # produced, field by field, before any of it reaches the board.
            log.info("-" * 58)
            for row in opportunities:
                log.info("  %s", row.name)
                log.info("      source=%s  agency=%s", row.source, row.agency)
                log.info("      url=%s", row.url)
                log.info("      open=%s  close=%s  amount=%s",
                         row.open_date, row.close_date, row.amount)
                log.info("      summary=%s", row.summary[:200])
                if row.raw:
                    # An undocumented upstream is diagnosed from its own field
                    # names. Printing the keys is how a wrong guess in a key
                    # tuple becomes visible instead of silently yielding None.
                    log.info("      raw keys=%s", ", ".join(sorted(row.raw)))
        log.info("-" * 58)
        log.info("dry run -- nothing written (%d opportunities)", len(opportunities))
        return 1 if errors else 0

    target = publish(
        opportunities, Path(runtime.get("output_dir", "output")), today, errors, failed
    )
    log.info("-" * 58)
    log.info("wrote %s (%d opportunities)", target, len(opportunities))

    # A failed source is a non-zero exit so CI surfaces it, but the file is
    # still written: a partially-fresh board beats no board.
    return 1 if errors else 0
