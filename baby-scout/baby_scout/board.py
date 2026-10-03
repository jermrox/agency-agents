"""Assemble one watchlist item's price, deal and safety results."""

from __future__ import annotations

import datetime as dt
from typing import Any

from . import deals
from .models import WatchItem
from .recalls import RecallMatch
from .safety import SafetyReport
from .store import PriceStore


def item_result(item: WatchItem, store: PriceStore, safety: SafetyReport,
                recalls: RecallMatch | None, today: dt.date | None = None) -> dict[str, Any]:
    latest = store.latest(item.key, until=today)
    in_stock = [o for o in latest if o.stock_status != "out_of_stock"]
    best = min(in_stock or latest, key=lambda o: o.unit_price or o.price, default=None)
    per_unit = bool(item.unit_count or (best and best.unit_count))
    deal = None
    if best is not None:
        current = best.unit_price if per_unit and best.unit_price else best.price
        deal = deals.score(current, store.history(item.key, per_unit=per_unit, until=today),
                           list_price=None if per_unit else best.list_price, today=today)
        if not safety.passed:
            deal.verdict = "skip"
    return {
        "key": item.key,
        "name": item.name,
        "brand": item.brand,
        "model": item.model,
        "category": item.category,
        "condition": item.condition,
        "target_price": item.target_price,
        "per_unit": per_unit,
        "best": best.to_dict() if best else None,
        "history": [[d.isoformat(), v] for d, v in store.history(item.key, per_unit=per_unit, until=today)
                    if not today or (today - d).days <= 365],
        "offers": [o.to_dict() for o in latest],
        "deal": deal.to_dict() if deal else None,
        "at_or_below_target": bool(deal and item.target_price and deal.current <= item.target_price),
        "safety": safety.to_dict(),
        "recalls": {
            "model": [r.to_dict() for r in recalls.model_hits],
            "brand_count": len(recalls.brand_hits),
        } if recalls else None,
    }
