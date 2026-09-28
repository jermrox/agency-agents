"""Time-phased buy plan against the due date.

Each category has a "need by" offset from the due date and a set of sale
windows in which it has historically been discounted. The planner picks the
latest window that still closes before the need-by date, so the household
buys at the best likely time without cutting it close; if no window fits it
says "buy by <date>" instead of inventing one.

Sale windows are *historical patterns*, not announcements. Retailers move
them every year -- confirm the dates before planning around them.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Any

# (name, start month, start day, end month, end day)
WINDOWS: dict[str, tuple[int, int, int, int, str]] = {
    "january_clearance": (1, 2, 1, 31, "January clearance / model-year changeover"),
    "spring_trade_in": (4, 10, 4, 30, "Spring car seat trade-in events (big-box retailers)"),
    "summer_sales": (7, 8, 7, 20, "Mid-July online sale events"),
    "fall_trade_in": (9, 8, 9, 30, "September Baby Safety Month car seat trade-ins"),
    "october_sales": (10, 6, 10, 15, "October online sale events"),
    "black_friday": (11, 20, 12, 2, "Black Friday / Cyber Monday"),
}


@dataclass
class Need:
    category: str
    label: str
    weeks_from_due: int          # negative = before the due date
    low: int
    high: int
    windows: tuple[str, ...]
    buy_new: bool = True
    note: str = ""


NEEDS: list[Need] = [
    Need("car_seat.infant", "Infant car seat (or convertible)", -5, 180, 350,
         ("spring_trade_in", "fall_trade_in", "black_friday"), True,
         "Needed to leave the hospital. Install and get it checked by a CPST before 36 weeks."),
    Need("stroller", "Stroller / travel system", -4, 150, 600,
         ("black_friday", "summer_sales", "october_sales", "spring_trade_in", "fall_trade_in", "january_clearance"), False),
    Need("bassinet", "Bassinet or play yard", -4, 80, 250,
         ("black_friday", "summer_sales", "october_sales"), True,
         "Flat, firm surface, fitted sheet only."),
    Need("breast_pump", "Breast pump", -6, 0, 300, (), True,
         "Most US health plans cover a pump under the ACA -- call the insurer before buying."),
    Need("monitor", "Baby monitor", -2, 50, 250, ("black_friday", "summer_sales", "october_sales"), False),
    Need("carrier.soft", "Soft carrier / wrap", -2, 40, 200, ("black_friday", "summer_sales"), False),
    Need("diapers", "Diapers (newborn + size 1 starter stock)", -3, 60, 120, (), True,
         "Don't stockpile newborn size; babies outgrow it in weeks. Compare per diaper."),
    Need("crib.full_size", "Crib + new firm mattress", 16, 250, 550,
         ("black_friday", "january_clearance", "summer_sales", "october_sales"), True,
         "Mattress new; crib may be used only if it meets the post-2011 standard."),
    Need("high_chair", "High chair", 22, 60, 250, ("black_friday", "summer_sales", "january_clearance"), False),
    Need("car_seat.convertible", "Convertible car seat (if you started with an infant seat)", 40, 180, 400,
         ("spring_trade_in", "fall_trade_in", "black_friday"), True),
    Need("gate", "Baby gates", 30, 40, 150, ("black_friday", "summer_sales"), False),
]


def _occurrences(name: str, start: dt.date, end: dt.date) -> list[tuple[dt.date, dt.date]]:
    sm, sd, em, ed, _ = WINDOWS[name]
    out = []
    for year in range(start.year - 1, end.year + 1):
        begin = dt.date(year, sm, sd)
        finish = dt.date(year + (1 if em < sm else 0), em, ed)
        if finish >= start and begin <= end:
            out.append((max(begin, start), finish))
    return out


def best_window(need_by: dt.date, today: dt.date, names: tuple[str, ...]) -> tuple[str, dt.date, dt.date] | None:
    """Latest sale window that closes on or before ``need_by``."""
    candidates = []
    for name in names:
        for begin, finish in _occurrences(name, today, need_by):
            if finish <= need_by:
                candidates.append((finish, begin, name))
    if not candidates:
        return None
    finish, begin, name = max(candidates)
    return name, begin, finish


def build_plan(due: dt.date, budget: float | None = None, today: dt.date | None = None,
               owned: set[str] | None = None) -> dict[str, Any]:
    today = today or dt.date.today()
    owned = owned or set()
    rows = []
    low_total = high_total = 0
    for need in NEEDS:
        if need.category in owned:
            continue
        need_by = due + dt.timedelta(weeks=need.weeks_from_due)
        window = best_window(need_by, today, need.windows)
        if window:
            name, begin, finish = window
            when = f"{WINDOWS[name][4]}: {begin:%b %d} - {finish:%b %d, %Y}"
        elif need_by < today:
            when = "Overdue -- buy now at the best in-stock price"
        else:
            when = f"Buy by {need_by:%b %d, %Y} (no reliable sale window before then)"
        rows.append({
            "category": need.category, "item": need.label, "need_by": need_by.isoformat(),
            "buy_window": when, "estimate_low": need.low, "estimate_high": need.high,
            "buy_new": need.buy_new, "note": need.note,
        })
        low_total += need.low
        high_total += need.high
    rows.sort(key=lambda r: r["need_by"])
    registry_open = due - dt.timedelta(weeks=8)
    return {
        "due_date": due.isoformat(),
        "generated": today.isoformat(),
        "rows": rows,
        "estimate_low": low_total,
        "estimate_high": high_total,
        "budget": budget,
        "over_budget_risk": bool(budget and high_total > budget),
        "registry_completion_window": f"typically opens ~{registry_open:%b %d, %Y} (verify with your registry)",
        "caveat": "Estimates are planning placeholders; replace with tracked prices. Sale windows are historical patterns -- confirm dates each year.",
    }
