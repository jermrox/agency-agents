"""CPSC recall lookup (SaferProducts.gov REST API, keyless, JSON).

The API does substring matching on whatever fields it is given, so a query for
Manufacturer=Graco returns every Graco recall back to the 1990s -- high recall,
low precision. :func:`match_recalls` narrows that locally: a hit must name the
brand *and* overlap the model name or model number. Brand-only hits are kept
separately because they still feed the brand-history part of the safety score.

Car seats are regulated by NHTSA, not CPSC. For those, the report carries a
link to NHTSA's recall lookup instead of pretending CPSC coverage is complete.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any

from .http import fetch_json

CPSC_URL = "https://www.saferproducts.gov/RestWebServices/Recall"
NHTSA_CAR_SEAT_RECALLS = "https://www.nhtsa.gov/recalls"


@dataclass
class Recall:
    number: str
    title: str
    date: str
    url: str
    products: list[str] = field(default_factory=list)
    models: list[str] = field(default_factory=list)
    manufacturers: list[str] = field(default_factory=list)
    hazards: list[str] = field(default_factory=list)
    remedies: list[str] = field(default_factory=list)

    @property
    def year(self) -> int | None:
        try:
            return int(self.date[:4])
        except (TypeError, ValueError):
            return None

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


def _names(items: Any, key: str = "Name") -> list[str]:
    out = []
    for item in items or []:
        if isinstance(item, dict) and item.get(key):
            out.append(str(item[key]).strip())
    return out


def parse_recall(raw: dict[str, Any]) -> Recall:
    products = raw.get("Products") or []
    return Recall(
        number=str(raw.get("RecallNumber") or raw.get("RecallID") or ""),
        title=str(raw.get("Title") or "").strip(),
        date=str(raw.get("RecallDate") or "")[:10],
        url=str(raw.get("URL") or ""),
        products=_names(products),
        models=[m for m in _names(products, "Model") if m],
        manufacturers=_names(raw.get("Manufacturers")) + _names(raw.get("Importers")),
        hazards=_names(raw.get("Hazards")),
        remedies=_names(raw.get("Remedies")),
    )


def fetch_recalls(brand: str, *, since: str | None = None) -> list[Recall]:
    """All CPSC recalls naming ``brand`` as manufacturer (live network call)."""
    params = {"format": "json", "Manufacturer": brand}
    if since:
        params["RecallDateStart"] = since
    payload = fetch_json(CPSC_URL, params=params, min_interval=1.0)
    return [parse_recall(r) for r in payload or [] if isinstance(r, dict)]


_TOKEN = re.compile(r"[a-z0-9]+")


def _tokens(text: str) -> set[str]:
    return {t for t in _TOKEN.findall(text.lower()) if len(t) > 1}


def _norm_model(text: str) -> str:
    return re.sub(r"[^a-z0-9]", "", text.lower())


def _mentions_brand(recall: Recall, brand: str) -> bool:
    needle = brand.lower()
    haystack = " ".join([recall.title, *recall.products, *recall.manufacturers]).lower()
    return needle in haystack


def _mentions_model(recall: Recall, model: str, model_number: str) -> bool:
    if model_number:
        wanted = _norm_model(model_number)
        if wanted and any(wanted in _norm_model(m) or _norm_model(m) == wanted for m in recall.models):
            return True
        if wanted and wanted in _norm_model(recall.title + " ".join(recall.products)):
            return True
    # Every distinctive token of the model name must appear (so "4Ever DLX"
    # does not match a recall of the "Extend2Fit").
    wanted_tokens = _tokens(model)
    if not wanted_tokens:
        return False
    have = _tokens(" ".join([recall.title, *recall.products, *recall.models]))
    return wanted_tokens <= have


@dataclass
class RecallMatch:
    model_hits: list[Recall]
    brand_hits: list[Recall]

    def brand_recent(self, years: int = 5, today: dt.date | None = None) -> list[Recall]:
        cutoff = (today or dt.date.today()).year - years
        return [r for r in self.brand_hits if (r.year or 0) >= cutoff]


def match_recalls(recalls: list[Recall], brand: str, model: str, model_number: str = "") -> RecallMatch:
    brand_hits = [r for r in recalls if _mentions_brand(r, brand)]
    model_hits = [r for r in brand_hits if _mentions_model(r, model, model_number)]
    return RecallMatch(model_hits=model_hits, brand_hits=brand_hits)
