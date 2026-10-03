"""Command line entry point: ``python3 -m baby_scout <command>``."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import logging
import statistics
import sys
from pathlib import Path

from . import board, config, dashboard, deals, plan, recalls, report, safety, watch
from .collect import CollectError, collect, extract_products
from .http import FetchError
from .models import Observation, utcnow
from .store import PriceStore, PurchaseStore

log = logging.getLogger("baby_scout")


def _load_recalls(args: argparse.Namespace, brand: str) -> list[recalls.Recall] | None:
    """Recalls for ``brand`` from a saved API response, or live, or None offline."""
    if getattr(args, "recalls_file", None):
        raw = json.loads(Path(args.recalls_file).read_text(encoding="utf-8"))
        return [recalls.parse_recall(r) for r in raw]
    if getattr(args, "offline", False):
        return None
    try:
        return recalls.fetch_recalls(brand)
    except FetchError as exc:
        log.warning("CPSC lookup for %s failed: %s", brand, exc)
        return None


def _paths(args: argparse.Namespace) -> dict[str, Path]:
    data = Path(args.data)
    return {
        "watchlist": Path(args.watchlist) if getattr(args, "watchlist", None) else data / "watchlist.toml",
        "prices": data / "prices.jsonl",
        "purchases": data / "purchases.jsonl",
        "reports": data / "reports",
    }


def _today(args: argparse.Namespace) -> dt.date:
    return dt.date.fromisoformat(args.today) if getattr(args, "today", None) else dt.date.today()


def _load_watch(args: argparse.Namespace, today: dt.date) -> list[dict] | None:
    """Recent child-related recalls from a saved API response, or live, or None offline."""
    since = today - dt.timedelta(days=args.watch_days)
    if getattr(args, "watch_file", None):
        return watch.select(json.loads(Path(args.watch_file).read_text(encoding="utf-8")), since)
    if args.offline:
        return None
    try:
        return watch.fetch(today, args.watch_days)
    except FetchError as exc:
        log.warning("CPSC recall watch failed: %s", exc)
        return None


def cmd_run(args: argparse.Namespace) -> int:
    paths = _paths(args)
    wl = config.load(paths["watchlist"])
    store = PriceStore(paths["prices"])
    today = _today(args)

    if not args.offline:
        for item in wl.items:
            for offer in item.offers:
                if not offer.url:
                    continue
                try:
                    obs = collect(item.key, offer.retailer, offer.url,
                                  unit_count=item.unit_count, unit_label=item.unit_label)
                    store.append(obs)
                    print(f"  {item.key} @ {offer.retailer}: ${obs.price:.2f} ({obs.stock_status})")
                except CollectError as exc:
                    print(f"  {item.key} @ {offer.retailer}: skipped -- {exc}")

    cache: dict[str, list[recalls.Recall] | None] = {}
    results = []
    for item in wl.items:
        if item.brand not in cache:
            cache[item.brand] = _load_recalls(args, item.brand)
        brand_recalls = cache[item.brand]
        match = (recalls.match_recalls(brand_recalls, item.brand, item.model, item.model_number)
                 if brand_recalls is not None else None)
        latest = store.latest(item.key, until=today)
        sold_by = next((o.sold_by_retailer for o in latest if o.sold_by_retailer is not None), None)
        safety_report = safety.evaluate(item, match, sold_by_retailer=sold_by, today=today, checked_at=utcnow())
        results.append(board.item_result(item, store, safety_report, match, today=today))

    buy_plan = None
    if wl.household.due_date:
        buy_plan = plan.build_plan(dt.date.fromisoformat(wl.household.due_date), wl.household.budget,
                                   today=today, owned=set(wl.household.owned))

    archive = report.ReportArchive(paths["reports"])
    purchases = [p for p in PurchaseStore(paths["purchases"]).all() if p["date"] <= today.isoformat()]
    daily = report.build(results, buy_plan, purchases, wl.household.budget,
                         wl.household.due_date, archive.previous(today.isoformat()), today,
                         watch=_load_watch(args, today), watch_days=args.watch_days)
    report_path = archive.save(daily)
    index = dashboard.write(results, buy_plan, archive, args.site, picks_path=Path(args.data) / "gear_picks.json")

    for r in daily["items"]:
        print(f"{deals.VERDICT_LABELS[r['verdict']]:34} {r['name']}")
    if daily["events"]:
        print("\nChanges since the last report:")
        for e in daily["events"]:
            print(f"  [{e['severity']}] {e['name']}: {e['detail']}")
    rw = daily["recall_watch"]
    print(f"\nRecall watch: {len(rw['items'])} baby/kid recalls in the last {rw['days']} days"
          if rw["available"] else "\nRecall watch: not run (offline or CPSC unreachable)")
    print(f"Saved {report_path} and {index}")
    return 0


def cmd_bought(args: argparse.Namespace) -> int:
    paths = _paths(args)
    name, category = args.key, args.category
    if paths["watchlist"].exists():
        for item in config.load(paths["watchlist"]).items:
            if item.key == args.key:
                name, category = item.name, category or item.category
    when = dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    history = [(d, p) for d, p in PriceStore(paths["prices"]).history(args.key) if 0 <= (when - d).days <= 90]
    median = round(statistics.median(p for _, p in history), 2) if len(history) >= deals.MIN_POINTS else None
    PurchaseStore(paths["purchases"]).append({
        "key": args.key, "name": name, "category": category, "price": args.price,
        "retailer": args.retailer, "date": when.isoformat(), "median_90d": median,
    })
    saved = f"; ${median - args.price:,.2f} under its 90-day median" if median and median > args.price else ""
    print(f"Logged purchase: {name} for ${args.price:,.2f} at {args.retailer} on {when}{saved}")
    return 0


def cmd_add_price(args: argparse.Namespace) -> int:
    observed = utcnow() if not args.date else f"{args.date}T12:00:00Z"
    obs = Observation(
        key=args.key, retailer=args.retailer, price=args.price, observed_at=observed, source="manual",
        list_price=args.list_price, stock_status=args.stock, seller=args.seller,
        sold_by_retailer=args.sold_by_retailer, url=args.url,
        unit_count=args.unit_count, unit_label=args.unit_label,
    )
    PriceStore(_paths(args)["prices"]).append(obs)
    unit = f" (${obs.unit_price}/{args.unit_label or 'unit'})" if obs.unit_price else ""
    print(f"Logged {args.key} @ {args.retailer}: ${args.price:.2f}{unit} on {observed[:10]}")
    return 0


def cmd_recalls(args: argparse.Namespace) -> int:
    found = _load_recalls(args, args.brand)
    if found is None:
        print("Recall lookup unavailable (offline or API unreachable).")
        return 2
    match = recalls.match_recalls(found, args.brand, args.model, args.model_number)
    print(f"{len(match.brand_hits)} {args.brand} recall(s) on file; "
          f"{len(match.brand_recent())} in the last 5 years; {len(match.model_hits)} match this model.")
    for r in match.model_hits:
        print(f"  ⚠ {r.number} {r.date} {r.title}\n    {r.url}")
    return 1 if match.model_hits else 0


def cmd_plan(args: argparse.Namespace) -> int:
    result = plan.build_plan(dt.date.fromisoformat(args.due), args.budget)
    if args.json:
        print(json.dumps(result, indent=2))
        return 0
    print(f"Buy plan for due date {result['due_date']}\n")
    for r in result["rows"]:
        print(f"- {r['item']} (need by {r['need_by']}, ${r['estimate_low']}-${r['estimate_high']}, "
              f"{'buy new' if r['buy_new'] else 'new or used'})\n    {r['buy_window']}")
        if r["note"]:
            print(f"    note: {r['note']}")
    budget = f" vs budget ${args.budget:,.0f}" if args.budget else ""
    print(f"\nEstimate ${result['estimate_low']:,}-${result['estimate_high']:,}{budget}")
    print(f"Registry completion discount {result['registry_completion_window']}")
    print(result["caveat"])
    return 0


def cmd_stack(args: argparse.Namespace) -> int:
    result = deals.stack(args.price, pct_off=args.pct or [], gift_card=args.gift_card,
                         cashback_pct=args.cashback, rebate=args.rebate,
                         gift_card_will_be_used=not args.gift_card_unused)
    print(json.dumps(result, indent=2))
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    print(json.dumps(extract_products(Path(args.file).read_text(encoding="utf-8")), indent=2))
    return 0


def cmd_safety(args: argparse.Namespace) -> int:
    reason = safety.banned_reason(args.text)
    print(reason or "No banned-category match. (Still run a recall check.)")
    return 1 if reason else 0


def _bool(text: str) -> bool:
    return text.lower() in {"1", "true", "yes", "y"}


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="baby_scout", description="Baby gear price, deal and safety tracker")
    p.add_argument("-v", "--verbose", action="store_true")
    sub = p.add_subparsers(dest="command", required=True)

    r = sub.add_parser("run", help="collect prices, check recalls, save today's report, rebuild the dashboard")
    r.add_argument("--data", default="data", help="folder holding watchlist.toml, prices, purchases and reports")
    r.add_argument("--watchlist", help="watchlist file (default: <data>/watchlist.toml)")
    r.add_argument("--site", default="site", help="where the dashboard is written")
    r.add_argument("--offline", action="store_true", help="no network: use logged prices only")
    r.add_argument("--recalls-file", help="saved CPSC API JSON to use instead of a live lookup")
    r.add_argument("--watch-file", help="saved CPSC API JSON for the recall watch instead of a live lookup")
    r.add_argument("--watch-days", type=int, default=60, help="how far back the recall watch looks (default 60)")
    r.add_argument("--today", help=argparse.SUPPRESS)
    r.set_defaults(func=cmd_run)

    a = sub.add_parser("add-price", help="log a price you saw (in store, app, flyer)")
    a.add_argument("--key", required=True)
    a.add_argument("--retailer", required=True)
    a.add_argument("--price", type=float, required=True)
    a.add_argument("--list-price", type=float)
    a.add_argument("--stock", default="in_stock",
                   choices=["in_stock", "low_stock", "out_of_stock", "preorder", "online_only", "store_only", "unknown"])
    a.add_argument("--seller")
    a.add_argument("--sold-by-retailer", type=_bool)
    a.add_argument("--url")
    a.add_argument("--unit-count", type=float, help="e.g. 164 for a 164-count diaper box")
    a.add_argument("--unit-label", help="diaper, wipe, oz ...")
    a.add_argument("--date", help="YYYY-MM-DD if logging an older price")
    a.add_argument("--data", default="data")
    a.set_defaults(func=cmd_add_price)

    bt = sub.add_parser("bought", help="log something you bought (feeds spending and savings)")
    bt.add_argument("--key", required=True, help="watchlist key, or any short name")
    bt.add_argument("--price", type=float, required=True, help="what you actually paid")
    bt.add_argument("--retailer", required=True)
    bt.add_argument("--category", help="plan category, e.g. stroller (taken from the watchlist when the key matches)")
    bt.add_argument("--date", help="YYYY-MM-DD (default today)")
    bt.add_argument("--data", default="data")
    bt.add_argument("--watchlist", help=argparse.SUPPRESS)
    bt.set_defaults(func=cmd_bought)

    c = sub.add_parser("recalls", help="CPSC recall check for one product")
    c.add_argument("--brand", required=True)
    c.add_argument("--model", required=True)
    c.add_argument("--model-number", default="")
    c.add_argument("--recalls-file")
    c.set_defaults(func=cmd_recalls, offline=False)

    pl = sub.add_parser("plan", help="time-phased buy plan from a due date")
    pl.add_argument("--due", required=True, help="YYYY-MM-DD")
    pl.add_argument("--budget", type=float)
    pl.add_argument("--json", action="store_true")
    pl.set_defaults(func=cmd_plan)

    s = sub.add_parser("stack", help="true price after stacking promos")
    s.add_argument("--price", type=float, required=True)
    s.add_argument("--pct", type=float, action="append", help="percent off; repeatable")
    s.add_argument("--gift-card", type=float, default=0.0)
    s.add_argument("--gift-card-unused", action="store_true")
    s.add_argument("--cashback", type=float, default=0.0, help="cash-back percent")
    s.add_argument("--rebate", type=float, default=0.0)
    s.set_defaults(func=cmd_stack)

    x = sub.add_parser("extract", help="show the schema.org product data in a saved HTML page")
    x.add_argument("--file", required=True)
    x.set_defaults(func=cmd_extract)

    b = sub.add_parser("banned", help="check a product name/description against banned types")
    b.add_argument("text")
    b.set_defaults(func=cmd_safety)
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.WARNING, format="%(levelname)s %(message)s")
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
