"""The daily report: today's results, the money, and what changed since last time.

One JSON file per day under ``reports/``. Each file is self-contained, so the
dashboard can show any past day, and the diff against the previous report is
what turns a board into a daily briefing: new recalls, new lows, stock changes,
items that reached their target.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any

from .models import utcnow

SEVERITY = {  # drives ordering and the status icon on the dashboard
    "new_recall": "critical",
    "safety_fail": "critical",
    "buy_now": "good",
    "hit_target": "good",
    "new_low": "good",
    "price_drop": "good",
    "back_in_stock": "good",
    "price_rise": "warning",
    "out_of_stock": "warning",
    "window_open": "warning",
    "tracking": "info",
    "purchased": "good",
}
ORDER = {"critical": 0, "good": 1, "warning": 2, "info": 3}


def _compact(r: dict[str, Any], bought: set[str]) -> dict[str, Any]:
    best = r.get("best") or {}
    deal = r.get("deal") or {}
    verdict = deal.get("verdict") or ("skip" if not r["safety"]["passed"] else "tracking")
    if r["key"] in bought and r["safety"]["passed"]:
        verdict = "bought"
    return {
        "key": r["key"],
        "name": r["name"],
        "category": r["category"],
        "verdict": verdict,
        "price": deal.get("current", best.get("price")),
        "per_unit": r["per_unit"],
        "retailer": best.get("retailer"),
        "stock": best.get("stock_status"),
        "median_90d": deal.get("median_90d"),
        "low_365d": deal.get("low_365d"),
        "at_or_below_target": r.get("at_or_below_target", False),
        "safety_passed": r["safety"]["passed"],
        "safety_score": r["safety"]["score"],
        "recalls": [x["number"] for x in (r.get("recalls") or {}).get("model", [])],
    }


def _event(kind: str, item: dict[str, Any], detail: str) -> dict[str, Any]:
    return {"type": kind, "severity": SEVERITY[kind], "key": item["key"], "name": item["name"], "detail": detail}


def _money(v: float | None, per_unit: bool) -> str:
    if v is None:
        return "?"
    return f"${v:,.4f}" if per_unit and v < 1 else f"${v:,.2f}"


def diff(prev: dict[str, Any] | None, items: list[dict[str, Any]], plan: dict[str, Any] | None,
         today: dt.date) -> list[dict[str, Any]]:
    before = {i["key"]: i for i in (prev or {}).get("items", [])}
    events = []
    for it in items:
        old = before.get(it["key"])
        new_recalls = sorted(set(it["recalls"]) - set(old["recalls"] if old else []))
        if new_recalls:
            events.append(_event("new_recall", it, f"Matches CPSC recall {', '.join(new_recalls)}. Don't buy; if you own it, follow the recall remedy."))
        elif not it["safety_passed"] and (old is None or old["safety_passed"]):
            events.append(_event("safety_fail", it, "Fails a safety gate -- see the item for why."))
        if it["verdict"] == "bought":
            continue
        if it["verdict"] == "buy_now" and (old is None or old["verdict"] != "buy_now"):
            events.append(_event("buy_now", it, f"{_money(it['price'], it['per_unit'])} at {it['retailer']} is within 3% of its 12-month low."))
        if it["at_or_below_target"] and not (old and old["at_or_below_target"]):
            events.append(_event("hit_target", it, f"At or below your target: {_money(it['price'], it['per_unit'])} at {it['retailer']}."))
        if (old and it["price"] is not None and old.get("price") is not None and it["safety_passed"]
                and "out_of_stock" not in (it["stock"], old.get("stock"))):
            change = (it["price"] - old["price"]) / old["price"] * 100 if old["price"] else 0
            if it["low_365d"] is not None and it["price"] <= it["low_365d"] and it["price"] < old["price"] and it["verdict"] != "buy_now":
                events.append(_event("new_low", it, f"New 12-month low: {_money(it['price'], it['per_unit'])}."))
            elif change <= -3:
                events.append(_event("price_drop", it, f"Down {-change:.0f}% to {_money(it['price'], it['per_unit'])} ({_money(old['price'], it['per_unit'])} last report)."))
            elif change >= 3:
                events.append(_event("price_rise", it, f"Up {change:.0f}% to {_money(it['price'], it['per_unit'])}."))
        if old and old.get("stock") == "out_of_stock" and it["stock"] not in (None, "out_of_stock"):
            events.append(_event("back_in_stock", it, f"Back in stock at {it['retailer']}."))
        elif old and old.get("stock") not in (None, "out_of_stock") and it["stock"] == "out_of_stock":
            events.append(_event("out_of_stock", it, "Now out of stock everywhere we track."))
    for row in (plan or {}).get("rows", []):
        opens = row.get("window_start")
        if opens and opens == today.isoformat():
            events.append({"type": "window_open", "severity": "warning", "key": row["category"], "name": row["item"],
                           "detail": f"Sale window opens today: {row['buy_window']}"})
    events.sort(key=lambda e: ORDER[e["severity"]])
    return events


def purchase_events(purchases: list[dict[str, Any]], today: dt.date) -> list[dict[str, Any]]:
    out = []
    for p in purchases:
        if p.get("date") == today.isoformat():
            saved = (p.get("median_90d") or 0) - p["price"]
            note = f", ${saved:,.2f} under its typical price" if saved > 0 else ""
            out.append({"type": "purchased", "severity": "good", "key": p["key"], "name": p.get("name") or p["key"],
                        "detail": f"Bought for ${p['price']:,.2f} at {p.get('retailer', '?')}{note}."})
    return out


def spending(purchases: list[dict[str, Any]], budget: float | None, plan: dict[str, Any] | None) -> dict[str, Any]:
    spent = round(sum(p["price"] for p in purchases), 2)
    saved = round(sum(max(0.0, (p.get("median_90d") or p["price"]) - p["price"]) for p in purchases), 2)
    bought = {p.get("category") for p in purchases if p.get("category")}
    remaining_low = remaining_high = 0
    for row in (plan or {}).get("rows", []):
        if row["category"] not in bought:
            remaining_low += row["estimate_low"]
            remaining_high += row["estimate_high"]
    return {
        "spent": spent,
        "saved_vs_typical": saved,
        "budget": budget,
        "remaining_budget": round(budget - spent, 2) if budget is not None else None,
        "still_to_buy_low": remaining_low,
        "still_to_buy_high": remaining_high,
        "projected_high": round(spent + remaining_high, 2),
        "purchases": purchases,
    }


def build(results: list[dict[str, Any]], plan: dict[str, Any] | None, purchases: list[dict[str, Any]],
          budget: float | None, due_date: str | None, prev: dict[str, Any] | None,
          today: dt.date) -> dict[str, Any]:
    bought = {p["key"] for p in purchases}
    items = [_compact(r, bought) for r in results]
    return {
        "date": today.isoformat(),
        "generated_at": utcnow(),
        "due_date": due_date,
        "days_to_due": (dt.date.fromisoformat(due_date) - today).days if due_date else None,
        "totals": {
            "watched": len(items),
            "buy_now": sum(i["verdict"] == "buy_now" for i in items),
            "bought": sum(i["verdict"] == "bought" for i in items),
            "safety_fail": sum(not i["safety_passed"] for i in items),
            "tracking": sum(i["verdict"] == "tracking" for i in items),
            "at_target": sum(bool(i["at_or_below_target"]) and i["verdict"] != "bought" for i in items),
        },
        "spending": spending(purchases, budget, plan),
        "events": diff(prev, items, plan, today) + purchase_events(purchases, today),
        "items": items,
    }


class ReportArchive:
    def __init__(self, directory: str | Path) -> None:
        self.dir = Path(directory)

    def dates(self) -> list[str]:
        if not self.dir.exists():
            return []
        return sorted(p.stem for p in self.dir.glob("????-??-??.json"))

    def load(self, date: str) -> dict[str, Any]:
        return json.loads((self.dir / f"{date}.json").read_text(encoding="utf-8"))

    def previous(self, before: str) -> dict[str, Any] | None:
        earlier = [d for d in self.dates() if d < before]
        return self.load(earlier[-1]) if earlier else None

    def save(self, report: dict[str, Any]) -> Path:
        self.dir.mkdir(parents=True, exist_ok=True)
        path = self.dir / f"{report['date']}.json"
        path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        return path

    def summaries(self, limit: int = 120) -> list[dict[str, Any]]:
        """Newest-first digest of past reports for the dashboard's archive."""
        out = []
        for date in reversed(self.dates()[-limit:]):
            r = self.load(date)
            out.append({"date": date, "totals": r["totals"], "spent": r["spending"]["spent"],
                        "saved": r["spending"]["saved_vs_typical"], "events": r["events"]})
        return out
