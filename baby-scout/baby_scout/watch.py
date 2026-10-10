"""Recall watch: every recent CPSC recall that touches babies, toddlers or kids.

The household watchlist only catches recalls of products the parent already
named. This catches the rest -- the teether a grandparent bought, the dresser
in the nursery, the toy from a party bag -- by scanning every recall CPSC
published in the last ``days`` days and keeping the child-related ones.

CPSC leaves the product "Type" blank on roughly 40% of recalls, so matching
runs on the title, description, product names and types together. Each hit is
filed under one group so the dashboard can be filtered by what the parent is
shopping for. Groups are checked in order and the first match wins: a
"crib mattress" is Sleep, not Furniture.
"""

from __future__ import annotations

import datetime as dt
import re
from typing import Any

from .http import fetch_json
from .recalls import CPSC_URL

GROUPS: list[tuple[str, str]] = [
    ("Sleep", r"\b(cribs?|bassinets?|cradles?|play ?yards?|playpens?|crib mattress\w*|sleep(ers?| sacks?| positioners?)|swaddl\w*|baby (beds?|nests?|loungers?))\b"),
    ("Car seats & travel", r"\b(car seats?|booster seats?|strollers?|baby carriers?|infant carriers?|slings?|wraps? carrier|travel systems?)\b"),
    ("Feeding & teething", r"\b(teeth(er|ers|ing)|pacifiers?|sippy|baby bottles?|bottle nipples?|high ?chairs?|booster chairs?|formula|baby food|bibs?)\b"),
    ("Baby gear", r"\b(walkers?|jumpers?|bouncers?|baby swings?|swings?|baby gates?|safety gates?|changing (tables?|pads?)|bath (seats?|tubs?)|baby monitors?|nursing pillows?)\b"),
    ("Nursery furniture (tip-over)", r"\b(dressers?|chests? of drawers|chests?|wardrobes?|bookcases?|tv stands?)\b"),
    ("Clothing", r"\b(pajamas?|sleepwear|loungewear|onesies?|garments?|hoodies?|drawstrings?)\b"),
    ("Toys", r"\b(toys?|rattles?|busy boards?|play ?sets?|blocks|puzzles?|dolls?|plush|squishy|fidget\w*|magnetic (balls?|sets?|tiles?)|building sets?)\b"),
]

CHILD = re.compile(r"\b(infants?|bab(y|ies)|toddlers?|newborns?|nursery|children[\u2019']?s|childrens|child|kids[\u2019']?|youth)\b", re.I)
NOT_A_CHILD_PRODUCT = re.compile(r"\bchild[- ]?(resistant|proof|safety (caps?|closures?|packaging))\b|\bkeep out of (the )?reach of children\b", re.I)
"""Packaging language ("child-resistant cap") says nothing about who the product is for."""
CHILDPROOFING = re.compile(r"\bchild(ren)?[\u2019']?s? poisoning\b|\bchild[- ]?resistant\b|\bpoisoning (hazard|risk) to (young )?children\b", re.I)
"""Household products recalled because a child could get into them (fuel cans,
medicines, cleaners without child-resistant packaging). Not baby gear, but
exactly what a parent childproofing a home needs to hear about."""
ALWAYS_CHILD = {"Sleep", "Car seats & travel", "Feeding & teething", "Baby gear", "Toys", "Nursery furniture (tip-over)"}
"""Groups that are child-related on their own. Clothing needs a child word too,
so an adult hoodie recall stays out."""

_COMPILED = [(name, re.compile(pattern, re.I)) for name, pattern in GROUPS]


def _text(raw: dict[str, Any], keep_packaging: bool = False) -> str:
    products = raw.get("Products") or []
    parts = [raw.get("Title") or "", raw.get("Description") or ""]
    parts += [f"{p.get('Name') or ''} {p.get('Type') or ''}" for p in products if isinstance(p, dict)]
    joined = " ".join(parts)
    return joined if keep_packaging else NOT_A_CHILD_PRODUCT.sub(" ", joined)


def classify(raw: dict[str, Any]) -> str | None:
    """The group a raw CPSC recall belongs to, or None if it isn't child-related."""
    original = _text(raw, keep_packaging=True)
    text = _text(raw)
    for name, pattern in _COMPILED:
        if pattern.search(text):
            if name in ALWAYS_CHILD or CHILD.search(text):
                return name
    if CHILDPROOFING.search(original):
        return "Childproofing (poisoning risk)"
    if CHILD.search(text):
        return "Other kids' products"
    return None


def _names(items: Any, key: str = "Name") -> list[str]:
    return [str(i[key]).strip() for i in items or [] if isinstance(i, dict) and i.get(key)]


def summarize(raw: dict[str, Any], group: str) -> dict[str, Any]:
    images = _names(raw.get("Images"), "URL")
    units = _names(raw.get("Products"), "NumberOfUnits")
    return {
        "number": str(raw.get("RecallNumber") or raw.get("RecallID") or ""),
        "date": str(raw.get("RecallDate") or "")[:10],
        "title": str(raw.get("Title") or "").strip(),
        "group": group,
        "products": _names(raw.get("Products"))[:3],
        "hazard": (_names(raw.get("Hazards")) or [""])[0],
        "remedy": ", ".join(_names(raw.get("RemedyOptions")) or _names(raw.get("Remedies")))[:200],
        "units": units[0] if units else "",
        "sold_at": ", ".join(_names(raw.get("Retailers")))[:200],
        "url": str(raw.get("URL") or ""),
        "image": images[0] if images else "",
    }


def select(raw_recalls: list[dict[str, Any]], since: dt.date) -> list[dict[str, Any]]:
    """Child-related recalls dated on or after ``since``, newest first, de-duplicated."""
    out: dict[str, dict[str, Any]] = {}
    for raw in raw_recalls:
        if not isinstance(raw, dict):
            continue
        date = str(raw.get("RecallDate") or "")[:10]
        if not date or date < since.isoformat():
            continue
        group = classify(raw)
        if group:
            item = summarize(raw, group)
            out.setdefault(item["number"] or item["title"], item)
    return sorted(out.values(), key=lambda r: (r["date"], r["number"]), reverse=True)


def fetch(today: dt.date, days: int = 60) -> list[dict[str, Any]]:
    """Live: all CPSC recalls in the window, filtered to child-related ones."""
    since = today - dt.timedelta(days=days)
    payload = fetch_json(CPSC_URL, params={"format": "json", "RecallDateStart": since.isoformat()}, min_interval=1.0)
    return select(payload or [], since)
