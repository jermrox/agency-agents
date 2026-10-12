"""Decision fields for every opportunity row (VYBE-AGENT-STANDARDS rule 9.7).

The operations console scores every lead 1-10 and prints why. It needs the
funding agent's own read beside its arithmetic, as separate machine-readable
fields: ``fit``, ``fit_why``, ``cost``, ``effort_hours``, ``travel`` and
``next_date``.

TWO SOURCES, ALWAYS LABELLED
A curated row can carry a hand-reviewed ``fit`` / ``fit_why`` (and ``cost``,
``effort_hours``, ``travel``) in sources.toml; those win and the row is marked
``fit_source = "reviewed"``. Every other row gets a transparent rule-based
estimate marked ``fit_source = "heuristic"``. The console and the founder can
then tell a judgement from arithmetic -- a computed number dressed up as a
human read is exactly the kind of quiet error that makes a board untrusted.

The heuristic is deliberately simple and readable; change the weights here,
not in the data.
"""

from __future__ import annotations

import re
from typing import Any

# Words that put Vybe in a programme's target -- wearable, health, founder identity.
_FIT_TERMS = re.compile(
    r"wearable|sensor|biosensor|\bhrv\b|\becg\b|sleep|recovery|digital health|health ?tech|"
    r"human performance|longevity|aging|ageing|veteran|women|woman|minority|black|latin|hardware|iot",
    re.I,
)
# A note that leads with a gate in capitals ("OHIO ONLY", "MUST BE A STUDENT") is
# warning the reader; the curation convention puts disqualifying gates there.
_CAPS_LEAD = re.compile(r"^\s*([A-Z0-9][A-Z0-9 ,;:'/&()$.-]{12,}?)(?:[.:]|\s[a-z])")
_TRAVEL = re.compile(
    r"\bin[- ]person\b|\btravel\b|\bon[- ]site\b|\brelocat|\bbooth\b|\bfly\b|"
    r"attend (?:the )?(?:final|summit|demo day)|las vegas|tokyo|düsseldorf|dusseldorf",
    re.I,
)
_FEE = re.compile(
    r"\$\s?([\d,]+(?:\.\d+)?)\s*(?:non-?refundable\s+)?(?:application|entry|registration|pitch|submission|booth|program(?:me)?)\s+fee"
    r"|(?:application|entry|registration|pitch|submission)\s+fee\s+(?:of\s+)?\$\s?([\d,]+(?:\.\d+)?)",
    re.I,
)
_NO_FEE = re.compile(r"\bno (?:application |entry )?fees?\b|\bfree to (?:apply|enter)\b|\bno cost\b", re.I)
_BIG_MONEY = re.compile(r"\$\s?(\d[\d,]*)(?:\s*(k|m|million))?", re.I)
# A residency gate for a state other than Ohio (Vybe is in Akron) -- the commonest
# reason a well-matched row is still unfileable. Ohio rows are not penalised.
_OTHER_STATE_NAME = re.compile(
    r"\b(?:upstate ny|new york|ny state|ny-registered|michigan|connecticut|massachusetts|california|texas|"
    r"washington[- ](?:state|only)|pennsylvania|new jersey|illinois|colorado|georgia|florida|virginia|maryland|"
    r"minnesota|wisconsin|indiana|kentucky|tennessee|north carolina|arizona|oregon|utah|rochester|ithaca|buffalo)\b",
    re.I,
)
_OTHER_STATE_CODE = re.compile(
    r"\b(?:NY|CA|MA|TX|MI|CT|PA|NJ|IL|WA)\b(?:[- ](?:based|state|only|registered)|\s+(?:manufacturer|for-profit|nonprofit|operations|employer))",
)
# ...unless the row itself says the state is only a venue, not a gate.
_NO_GEO_GATE = re.compile(
    r"no geographic|(?:do|does) not restrict|from anywhere|anywhere in the u|nationwide|open to founders anywhere|worldwide",
    re.I,
)
# Money that only reaches a company through a university or nonprofit applicant.
_ACADEMIC = re.compile(
    r"faculty (?:pi|member)|(?:university|nonprofit)(?: or (?:university|nonprofit))? applies|"
    r"routed through a university|^academic researchers|cornell|\bpi must apply",
    re.I,
)
_HEAVY = re.compile(r"proposal|white paper|narrative|research plan|budget justification|letters? of support", re.I)


def _largest_amount(text: str) -> float:
    best = 0.0
    for num, unit in _BIG_MONEY.findall(text or ""):
        try:
            value = float(num.replace(",", ""))
        except ValueError:
            continue
        unit = (unit or "").lower()
        if unit == "k":
            value *= 1_000
        elif unit in ("m", "million"):
            value *= 1_000_000
        best = max(best, value)
    return best


def _cost(text: str) -> int:
    match = _FEE.search(text)
    if match:
        raw = (match.group(1) or match.group(2) or "0").replace(",", "")
        try:
            return int(float(raw))
        except ValueError:
            return 0
    return 0


def _effort(kind: str, documents: list[str], sam: str, text: str) -> float:
    base = {"credit": 0.5, "partnership": 1.0, "visibility": 3.0, "accelerator": 4.0}.get(kind, 4.0)
    hours = base + max(0, len(documents) - 2) * 1.0
    joined = " ".join(documents) + " " + text
    if re.search(r"video", joined, re.I):
        hours += 1.5
    if re.search(r"\bdeck\b", joined, re.I):
        hours += 2
    if _HEAVY.search(joined):
        hours += 8
    if sam == "required":
        hours = max(hours, 40.0)  # a federal proposal, plus registrations
    return round(hours * 2) / 2


def _heuristic_fit(row: dict[str, Any], cost: int, travel: bool) -> tuple[int, str]:
    sam = row.get("sam") or ""
    note = row.get("summary") or ""
    elig = row.get("eligibility") or ""
    text = " ".join([row.get("name") or "", note, elig])

    score = 4.0
    reasons = []
    score += {"none": 2, "later": 0.5, "required": -2, "check": -1}.get(sam, 0)
    terms = {m.lower() for m in _FIT_TERMS.findall(text)}
    if terms:
        score += min(2, len(terms) * 0.75)
    if _largest_amount(row.get("amount") or "") >= 50_000:
        score += 1
    if cost > 0:
        score -= 2
        reasons.append(f"${cost} to enter")
    if travel:
        score -= 0.5
    gate = _CAPS_LEAD.match(note)
    if gate:
        score -= 1.5
        reasons.append(gate.group(1).strip().rstrip(",;:").capitalize())
    gate_text = " ".join([elig, note, " ".join(row.get("documents") or [])])
    state = _OTHER_STATE_NAME.search(gate_text) or _OTHER_STATE_CODE.search(gate_text)
    if state and not gate and not _NO_GEO_GATE.search(gate_text):
        score -= 3
        reasons.append(f"Residency gate ({state.group(0).strip()}); Vybe is in Ohio")
    if _ACADEMIC.search(gate_text):
        score -= 2.5
        reasons.append("A university or nonprofit must be the applicant")
    if row.get("kind") == "credit":
        score -= 0.5
    fit = int(max(1, min(10, round(score))))

    door = re.split(r"(?<=[.;])\s", elig.strip(), maxsplit=1)[0][:140] if elig else "eligibility not stated"
    risk = "; ".join(reasons) if reasons else (
        "SAM.gov registration first" if sam == "required" else "no disqualifier flagged on the row"
    )
    why = f"Rule-based estimate, not hand-reviewed. Door: {door.rstrip('.;')}. Watch: {risk}."
    return fit, why


def decision_fields(row: dict[str, Any], reviewed: dict[str, Any]) -> dict[str, Any]:
    """Return the rule-9.7 fields for one serialized row.

    ``reviewed`` carries any hand-set values from sources.toml (fit, fit_why,
    cost, effort_hours, travel). Hand-set values always win.
    """
    text = " ".join(str(row.get(k) or "") for k in ("name", "amount", "summary", "eligibility"))
    text += " " + " ".join(row.get("documents") or [])

    cost = reviewed.get("cost")
    if cost is None:
        cost = 0 if _NO_FEE.search(text) and not _FEE.search(text) else _cost(text)
    travel = reviewed.get("travel")
    if travel is None:
        travel = bool(_TRAVEL.search(text)) and not re.search(r"\bvirtual(?:ly)? only\b|\bonline only\b", text, re.I)
    effort = reviewed.get("effort_hours")
    if effort is None:
        effort = _effort(row.get("kind") or "", row.get("documents") or [], row.get("sam") or "", text)

    if reviewed.get("fit") is not None:
        fit = int(reviewed["fit"])
        why = str(reviewed.get("fit_why") or "")
        source = "reviewed"
    else:
        fit, why = _heuristic_fit(row, int(cost), bool(travel))
        source = "heuristic"

    return {
        "fit": fit,
        "fit_why": why,
        "fit_source": source,
        "cost": int(cost),
        "effort_hours": float(effort),
        "travel": bool(travel),
        "next_date": row.get("close_date"),
    }
