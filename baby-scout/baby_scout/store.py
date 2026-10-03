"""Append-only price history, one JSON object per line.

JSONL keeps the history diffable in git and trivially mergeable, and it is
the only state this tool keeps.
"""

from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Iterator

from .models import Observation


class PriceStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, obs: Observation) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(obs.to_dict(), sort_keys=True) + "\n")

    def all(self) -> Iterator[Observation]:
        if not self.path.exists():
            return
        with self.path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    yield Observation.from_dict(json.loads(line))

    def for_key(self, key: str, until: dt.date | None = None) -> list[Observation]:
        """Observations for ``key``, oldest first, optionally only those seen on or before ``until``."""
        return sorted((o for o in self.all() if o.key == key and (until is None or o.date <= until)),
                      key=lambda o: o.observed_at)

    def history(self, key: str, *, per_unit: bool = False, until: dt.date | None = None) -> list[tuple[dt.date, float]]:
        """Daily lowest price across retailers (or lowest unit price)."""
        best: dict[dt.date, float] = {}
        for obs in self.for_key(key, until):
            value = obs.unit_price if per_unit else obs.price
            if value is None or obs.stock_status == "out_of_stock":
                continue
            best[obs.date] = min(value, best.get(obs.date, value))
        return sorted(best.items())

    def latest(self, key: str, until: dt.date | None = None) -> list[Observation]:
        """Most recent observation per retailer."""
        latest: dict[str, Observation] = {}
        for obs in self.for_key(key, until):
            latest[obs.retailer] = obs
        return sorted(latest.values(), key=lambda o: o.price)


class PurchaseStore:
    """What the household actually bought -- the "spent" side of the budget."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def append(self, purchase: dict) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(purchase, sort_keys=True) + "\n")

    def all(self) -> list[dict]:
        if not self.path.exists():
            return []
        with self.path.open(encoding="utf-8") as fh:
            return [json.loads(line) for line in fh if line.strip()]
