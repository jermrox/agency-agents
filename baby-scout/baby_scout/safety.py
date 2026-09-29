"""Hard safety gates and the 0-100 confidence score.

Gates are pass/fail and run first. A product that fails any gate gets no
score and is never shown as a deal, however cheap it is. Only products that
pass every gate get a confidence score, and every factor we could not verify
is scored at half credit and listed, so a thin score is visibly thin.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass, field
from typing import Any

from .models import WatchItem
from .recalls import NHTSA_CAR_SEAT_RECALLS, RecallMatch

BANNED_PATTERNS: dict[str, str] = {
    r"\binclined?\s+(infant\s+)?sleep(er)?s?\b": "Inclined infant sleepers are banned for sale in the US (Safe Sleep for Babies Act, 2022).",
    r"\bcrib\s+bumpers?\b|\bbumper\s+pads?\b": "Padded crib bumpers are banned for sale in the US (Safe Sleep for Babies Act, 2022).",
    r"\bdrop[\s-]?side\b": "Drop-side cribs do not meet the federal crib standard (16 CFR 1219/1220).",
    r"\bsleep\s+positioners?\b": "Infant sleep positioners: FDA and AAP warn against them (suffocation risk).",
    r"\bweighted\s+(sleep\s+sack|swaddle|blanket)s?\b": "Weighted infant sleep products: the AAP recommends against them; CPSC has warned about them.",
    r"\b(sleep|infant|baby)\s+wedges?\b": "Infant sleep wedges: the AAP recommends a flat, firm sleep surface only.",
}

MANDATORY_STANDARD: dict[str, str] = {
    "car_seat": "FMVSS 213",
    "crib.full_size": "16 CFR 1220",
    "crib.mini": "16 CFR 1220",
    "crib": "16 CFR 1219/1220",
    "bassinet": "16 CFR 1218",
    "play_yard": "16 CFR 1221",
    "high_chair": "16 CFR 1231",
    "carrier.soft": "16 CFR 1226",
    "carrier.frame": "16 CFR 1230",
    "sling": "16 CFR 1228",
    "gate": "16 CFR 1239",
    "stroller": "16 CFR 1227",
    "bouncer": "16 CFR 1229",
    "swing": "16 CFR 1223",
    "infant_sleep": "16 CFR 1236",
}

SINGLE_USER_WHEN_USED = ("breast_pump", "crib_mattress")


def mandatory_standard(category: str) -> str | None:
    parts = category.split(".")
    for i in range(len(parts), 0, -1):
        hit = MANDATORY_STANDARD.get(".".join(parts[:i]))
        if hit:
            return hit
    return None


@dataclass
class Gate:
    name: str
    status: str  # pass | fail | n/a | check
    evidence: str

    def to_dict(self) -> dict[str, Any]:
        return self.__dict__.copy()


@dataclass
class SafetyReport:
    gates: list[Gate]
    score: int | None
    factors: list[dict[str, Any]] = field(default_factory=list)
    unverified: list[str] = field(default_factory=list)
    checked_at: str = ""
    links: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(g.status != "fail" for g in self.gates)

    @property
    def failures(self) -> list[Gate]:
        return [g for g in self.gates if g.status == "fail"]

    def to_dict(self) -> dict[str, Any]:
        return {
            "passed": self.passed,
            "score": self.score,
            "gates": [g.to_dict() for g in self.gates],
            "factors": self.factors,
            "unverified": self.unverified,
            "checked_at": self.checked_at,
            "links": self.links,
        }


def banned_reason(text: str) -> str | None:
    lowered = text.lower()
    for pattern, reason in BANNED_PATTERNS.items():
        if re.search(pattern, lowered):
            return reason
    return None


def evaluate(
    item: WatchItem,
    recalls: RecallMatch | None,
    *,
    sold_by_retailer: bool | None = None,
    today: dt.date | None = None,
    checked_at: str = "",
) -> SafetyReport:
    today = today or dt.date.today()
    gates: list[Gate] = []
    links: list[str] = []
    is_car_seat = item.category.startswith("car_seat")

    # 1. Recalls.
    if recalls is None:
        gates.append(Gate("No open CPSC recall", "check",
                          "Recall lookup did not run (offline or API unreachable). Re-check before buying."))
    else:
        open_hits = [r for r in recalls.model_hits if r.number not in item.remedy_applied]
        if open_hits:
            first = open_hits[0]
            gates.append(Gate("No open CPSC recall", "fail",
                              f"{len(open_hits)} matching recall(s), e.g. {first.number} {first.date}: {first.title} {first.url}".strip()))
        else:
            fixed = len(recalls.model_hits) - len(open_hits)
            note = f"; {fixed} matched recall(s) marked remedied" if fixed else ""
            gates.append(Gate("No open CPSC recall", "pass",
                              f"0 open matches among {len(recalls.brand_hits)} {item.brand} recalls{note}"))
    if is_car_seat:
        gates.append(Gate("No open NHTSA car seat recall", "check",
                          f"Car seats are NHTSA-regulated: look up the model and manufacture date at {NHTSA_CAR_SEAT_RECALLS}"))
        links.append(NHTSA_CAR_SEAT_RECALLS)

    # 2. Banned categories.
    reason = banned_reason(f"{item.category} {item.model}")
    gates.append(Gate("Not a banned product type", "fail" if reason else "pass",
                      reason or f"Category {item.category}"))

    # 3. Mandatory standard.
    standard = mandatory_standard(item.category)
    gates.append(Gate("Mandatory federal standard", "check" if standard else "n/a",
                      f"Confirm the {standard} compliance label on the product/manual" if standard
                      else "No category-specific mandatory standard"))

    # 4. Used-gear rules.
    if item.condition == "used":
        if any(item.category.startswith(c) for c in SINGLE_USER_WHEN_USED):
            gates.append(Gate("Safe to buy used", "fail",
                              "Buy new: single-user breast pumps and crib mattresses can't be verified second-hand."))
        elif is_car_seat:
            problems = []
            if not item.expiration_date:
                problems.append("expiration date unknown")
            elif dt.date.fromisoformat(item.expiration_date) <= today:
                problems.append(f"expired {item.expiration_date}")
            if item.crash_history_known is not True:
                problems.append("crash history not known")
            if item.labels_intact is not True:
                problems.append("labels not confirmed intact")
            gates.append(Gate("Used car seat is verifiable", "fail" if problems else "pass",
                              "; ".join(problems) if problems else
                              f"Expires {item.expiration_date}, no crashes, labels intact"))
        else:
            gates.append(Gate("Used item check", "check",
                              "Confirm all parts, hardware and harness are present and the model is not recalled."))

    report = SafetyReport(gates=gates, score=None, checked_at=checked_at, links=links)
    if not report.passed:
        return report

    # Confidence score, 5 factors x 20 points.
    unverified: list[str] = []

    def factor(name: str, points: float | None, note: str) -> dict[str, Any]:
        if points is None:
            unverified.append(name)
            points = 10
        return {"factor": name, "points": round(points), "max": 20, "note": note}

    factors = [
        factor("Voluntary certification (JPMA)",
               None if item.jpma_certified is None else (20 if item.jpma_certified else 8),
               {True: "JPMA certified", False: "Not JPMA certified", None: "Unknown"}[item.jpma_certified]),
        factor("Sold by retailer or brand",
               None if sold_by_retailer is None else (20 if sold_by_retailer else 6),
               {True: "Sold by retailer/brand", False: "Third-party marketplace seller -- counterfeit risk", None: "Seller unknown"}[sold_by_retailer]),
    ]
    if recalls is None:
        factors.append(factor("Brand recall history (5 yrs)", None, "Recall lookup did not run"))
    else:
        n = len(recalls.brand_recent(5, today))
        factors.append(factor("Brand recall history (5 yrs)", max(0, 20 - 4 * n),
                              f"{n} {item.brand} recall(s) since {today.year - 5}"))
    if is_car_seat:
        stars = item.ease_of_use_stars
        factors.append(factor("NHTSA ease-of-use rating", None if stars is None else stars / 5 * 20,
                              f"{stars}/5 stars" if stars is not None else "Not recorded"))
    else:
        factors.append(factor("Ease of correct use", None, "Not rated for this category"))
    factors.append(factor("Condition", 20 if item.condition == "new" else 12,
                          "New" if item.condition == "new" else "Used, passed checks"))

    report.score = int(sum(f["points"] for f in factors))
    report.factors = factors
    report.unverified = unverified
    return report
