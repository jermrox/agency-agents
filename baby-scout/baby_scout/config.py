"""Load the household watchlist (TOML)."""

from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .models import Offer, WatchItem


@dataclass
class Household:
    due_date: str | None = None
    budget: float | None = None
    region: str = "US"
    owned: list[str] = field(default_factory=list)


@dataclass
class Watchlist:
    household: Household
    items: list[WatchItem]


_ITEM_FIELDS = set(WatchItem.__dataclass_fields__) - {"offers"}


def load(path: str | Path) -> Watchlist:
    with open(path, "rb") as fh:
        raw: dict[str, Any] = tomllib.load(fh)
    hh = raw.get("household", {})
    household = Household(
        due_date=str(hh["due_date"]) if hh.get("due_date") else None,
        budget=hh.get("budget"),
        region=hh.get("region", "US"),
        owned=list(hh.get("owned", [])),
    )
    items = []
    seen = set()
    for entry in raw.get("item", []):
        unknown = set(entry) - _ITEM_FIELDS - {"offer"}
        if unknown:
            raise ValueError(f"item {entry.get('key')!r}: unknown field(s) {sorted(unknown)}")
        for required in ("key", "brand", "model", "category"):
            if not entry.get(required):
                raise ValueError(f"item missing required field {required!r}: {entry}")
        if entry["key"] in seen:
            raise ValueError(f"duplicate item key {entry['key']!r}")
        seen.add(entry["key"])
        fields = {k: v for k, v in entry.items() if k in _ITEM_FIELDS}
        for date_field in ("expiration_date", "need_by"):
            if fields.get(date_field) is not None:
                fields[date_field] = str(fields[date_field])
        offers = [Offer(retailer=o["retailer"], url=o.get("url")) for o in entry.get("offer", [])]
        items.append(WatchItem(**fields, offers=offers))
    return Watchlist(household, items)
