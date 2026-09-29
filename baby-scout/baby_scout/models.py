"""Data shapes shared across the package."""

from __future__ import annotations

import datetime as dt
from dataclasses import asdict, dataclass, field
from typing import Any


def utcnow() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Observation:
    """One price sighting for one product at one retailer.

    ``source`` records how we know: ``jsonld`` (read from the retailer page's
    schema.org markup), ``manual`` (typed in by the parent), or ``feed``.
    A price without a source and a timestamp is never shown to anyone.
    """

    key: str
    retailer: str
    price: float
    observed_at: str = field(default_factory=utcnow)
    source: str = "manual"
    currency: str = "USD"
    list_price: float | None = None
    stock_status: str = "unknown"
    seller: str | None = None
    sold_by_retailer: bool | None = None
    url: str | None = None
    rating: float | None = None
    review_count: int | None = None
    unit_count: float | None = None
    unit_label: str | None = None

    @property
    def unit_price(self) -> float | None:
        if self.unit_count and self.unit_count > 0:
            return round(self.price / self.unit_count, 4)
        return None

    @property
    def date(self) -> dt.date:
        return dt.date.fromisoformat(self.observed_at[:10])

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["unit_price"] = self.unit_price
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Observation":
        known = {f for f in cls.__dataclass_fields__}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Offer:
    retailer: str
    url: str | None = None


@dataclass
class WatchItem:
    """One product the household is considering, from the watchlist file."""

    key: str
    brand: str
    model: str
    category: str
    model_number: str = ""
    upc: str = ""
    target_price: float | None = None
    need_by: str | None = None
    condition: str = "new"                 # new | used
    jpma_certified: bool | None = None
    ease_of_use_stars: float | None = None  # NHTSA 1-5, car seats only
    remedy_applied: list[str] = field(default_factory=list)  # recall numbers already fixed
    # Used car seats only.
    expiration_date: str | None = None
    crash_history_known: bool | None = None
    labels_intact: bool | None = None
    unit_count: float | None = None
    unit_label: str | None = None
    offers: list[Offer] = field(default_factory=list)

    @property
    def name(self) -> str:
        return f"{self.brand} {self.model}".strip()
