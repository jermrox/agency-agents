"""Deal scoring: a price is judged against its own history, never list price.

Verdicts:
  buy_now  -- within 3% of the 365-day low
  good     -- at least 15% under the 90-day median
  fair     -- 5-15% under the 90-day median
  wait     -- less than 5% under the 90-day median (or above it)
  tracking -- fewer than MIN_POINTS observations in 90 days; no verdict yet
"""

from __future__ import annotations

import datetime as dt
import statistics
from dataclasses import dataclass
from typing import Any, Iterable

MIN_POINTS = 5
NEAR_LOW = 0.03

VERDICT_LABELS = {
    "buy_now": "🟢 Buy now",
    "good": "🟡 Good, not great",
    "fair": "🟠 Fair -- probably wait",
    "wait": "🟠 Wait -- likely to drop",
    "tracking": "⚪ Tracking -- not enough history",
    "skip": "🔴 Skip -- fails safety",
    "bought": "✅ Bought",
}


@dataclass
class DealScore:
    verdict: str
    current: float
    median_90d: float | None = None
    low_365d: float | None = None
    pct_below_median: float | None = None
    points_90d: int = 0
    fake_discount: bool = False
    note: str = ""

    @property
    def label(self) -> str:
        return VERDICT_LABELS[self.verdict]

    def to_dict(self) -> dict[str, Any]:
        data = self.__dict__.copy()
        data["label"] = self.label
        return data


def score(
    current: float,
    history: Iterable[tuple[dt.date, float]],
    *,
    list_price: float | None = None,
    today: dt.date | None = None,
) -> DealScore:
    today = today or dt.date.today()
    points = [(d, p) for d, p in history if p > 0]
    last90 = [p for d, p in points if 0 <= (today - d).days <= 90]
    last365 = [p for d, p in points if 0 <= (today - d).days <= 365]

    if len(last90) < MIN_POINTS:
        return DealScore("tracking", current, points_90d=len(last90),
                         note=f"{len(last90)} price point(s) in 90 days; need {MIN_POINTS} before judging.")

    median = statistics.median(last90)
    low = min(last365 + [current])
    pct = (median - current) / median * 100
    near_low = current <= low * (1 + NEAR_LOW)

    if near_low:
        verdict = "buy_now"
    elif pct >= 15:
        verdict = "good"
    elif pct >= 5:
        verdict = "fair"
    else:
        verdict = "wait"

    fake = False
    note = ""
    if list_price and list_price > current:
        claimed = (list_price - current) / list_price * 100
        if claimed - pct >= 15:
            fake = True
            note = (f"Advertised {claimed:.0f}% off list, but only {pct:.0f}% below what it has "
                    f"actually sold for over 90 days.")
    places = 4 if median < 1 else 2   # per-unit prices (diapers, wipes) need sub-cent precision
    return DealScore(verdict, current, round(median, places), round(low, places), round(pct, 1),
                     len(last90), fake, note)


def unit_price(price: float, count: float) -> float:
    if count <= 0:
        raise ValueError("unit count must be positive")
    return round(price / count, 4)


def stack(
    price: float,
    *,
    pct_off: Iterable[float] = (),
    gift_card: float = 0.0,
    cashback_pct: float = 0.0,
    rebate: float = 0.0,
    gift_card_will_be_used: bool = True,
) -> dict[str, float]:
    """True out-of-pocket after stacking promos.

    Percentage discounts compound (a 15% registry discount on top of a 10%
    coupon is 23.5%, not 25%). A gift card is only money if it gets spent, so
    it counts only when ``gift_card_will_be_used``.
    """
    paid = price
    for pct in pct_off:
        paid *= 1 - pct / 100
    at_register = round(paid, 2)
    back = paid * cashback_pct / 100 + rebate + (gift_card if gift_card_will_be_used else 0.0)
    net = round(max(0.0, paid - back), 2)
    return {
        "sticker": round(price, 2),
        "at_register": at_register,
        "net": net,
        "effective_pct_off": round((price - net) / price * 100, 1) if price else 0.0,
    }
