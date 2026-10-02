#!/usr/bin/env python3
"""Build the Vybe Growth Scout board.

Reads every lane file in data/raw/*.json, applies the gates and priority rules
in params.toml, de-duplicates, and writes:

  data/targets.json   the ranked, validated target list (the record)
  site/data.json      the same data for the dashboard
  site/index.html     the self-contained dashboard (no external requests)

Python 3.11+ standard library only.

  python3 growth-scout/build.py            # build
  python3 growth-scout/build.py --check    # validate only, exit 1 on problems
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RAW = ROOT / "data" / "raw"
SITE = ROOT / "site"
LINK_CHECK = ROOT / "data" / "link_check.json"

TYPES = {
    "vc", "angel", "angel-group", "syndicate", "accelerator", "corporate-vc",
    "builder", "research-lab", "amplifier", "community", "event", "listing", "signal",
    "competitor-deal", "athlete", "team", "program",
}
HUNTS = {"investor", "growth", "social", "sponsorship"}


def load_params() -> dict:
    with open(ROOT / "params.toml", "rb") as fh:
        return tomllib.load(fh)


def parse_date(value) -> dt.date | None:
    if not value or not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def norm(text: str | None) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def validate(row: dict, params: dict, today: dt.date) -> list[str]:
    """Return the reasons a row fails the gates (empty list = keep)."""
    gates = params["gates"]
    problems = []
    if not row.get("name"):
        problems.append("no name")
    if row.get("type") not in TYPES:
        problems.append(f"unknown type {row.get('type')!r}")
    if row.get("hunt") not in HUNTS:
        problems.append(f"unknown hunt {row.get('hunt')!r}")
    evidence = [u for u in row.get("evidence") or [] if isinstance(u, str) and u.startswith("http")]
    if len(evidence) < gates["min_evidence_urls"]:
        problems.append("no evidence URL")
    fit = row.get("fit")
    if not isinstance(fit, (int, float)) or fit < gates["min_fit"]:
        problems.append(f"fit {fit} below {gates['min_fit']}")
    contact = row.get("contact_url") or ""
    if contact and not contact.startswith("http"):
        problems.append("contact_url is not a URL (never a guessed email)")
    name_blob = norm(f"{row.get('name')} {row.get('org')}")
    for bad in gates["exclude_names"]:
        if norm(bad) and norm(bad) in name_blob:
            problems.append(f"excluded name {bad}")
    # Only the target's own name decides the lane: a VC whose deal note
    # mentions SBIR is still a VC, but "Acme SBIR Program" is a grant.
    name_text = f"{row.get('name')}".lower()
    for kw in gates["exclude_keywords"]:
        if kw.lower() in name_text and row.get("type") not in {"signal"}:
            problems.append(f"out of lane ({kw}: funding sweep owns it)")
    deadline = parse_date(row.get("deadline"))
    if deadline and deadline < today:
        problems.append(f"deadline {deadline} passed")
    if row.get("type") in {"vc", "corporate-vc", "angel", "syndicate"}:
        last = parse_date(row.get("last_signal_date"))
        if last and (today - last).days > gates["max_signal_age_days"]:
            problems.append(f"last signal {last} too old")
    return problems


IDENTITY_RE = re.compile(
    r"\bveteran[- ](?:owned|founder|led)|\bveteran-,|\b(?:woman|women)[- ](?:owned|led|founder)|\bwoman-,|\bminority[- ]owned",
    re.I,
)


def uses_founder_identity(row: dict) -> bool:
    """True when the drafted opener tells the founder-identity story."""
    return bool(IDENTITY_RE.search(row.get("opener") or ""))


def score(row: dict, params: dict, today: dt.date) -> tuple[int, str]:
    p = params["priority"]
    s = int(row["fit"]) * 10
    deadline = parse_date(row.get("deadline"))
    if deadline and 0 <= (deadline - today).days <= p["deadline_window_days"]:
        s += p["deadline_bonus"]
    last = parse_date(row.get("last_signal_date"))
    if last and 0 <= (today - last).days <= p["recent_signal_days"]:
        s += p["recent_signal_bonus"]
    if row.get("confidence") == "verified":
        s += p["verified_bonus"]
    if row.get("contact_url"):
        s += p["open_channel_bonus"]
    ice = row.get("ice") or {}
    if row.get("hunt") == "growth" and all(isinstance(ice.get(k), (int, float)) for k in "ice"):
        # Easy, high-confidence wins move up; hard ones move down.
        s += round((ice["i"] + ice["c"] + ice["e"]) / 3) - 7
    s = max(0, min(100, s))
    label = "High" if s >= p["high"] else "Medium" if s >= p["medium"] else "Low"
    return s, label


def load_link_check() -> dict:
    """{url: {"status": "ok" | "dead" | "unverified", "note": str}} from the last link check."""
    if not LINK_CHECK.exists():
        return {}
    data = json.loads(LINK_CHECK.read_text())
    return data.get("urls", {})


def apply_link_check(row: dict, checks: dict) -> str | None:
    """Drop dead links from a row. Returns a rejection reason when nothing citable is left."""
    status = lambda u: (checks.get(u) or {}).get("status")  # noqa: E731
    dead = [u for u in row["evidence"] if status(u) == "dead"]
    row["evidence"] = [u for u in row["evidence"] if status(u) != "dead"]
    if not row["evidence"]:
        return f"every evidence link is dead ({len(dead)} checked)"
    contact = row.get("contact_url")
    if contact and status(contact) == "dead":
        row["contact_url"] = None
        row["contact_note"] = f"contact link dead: {(checks[contact].get('note') or '').strip()}"
    checked = [u for u in row["evidence"] + ([row["contact_url"]] if row.get("contact_url") else []) if u in checks]
    if row.get("contact_note"):
        row["link_status"] = "contact dead"
    elif checked and all(status(u) == "ok" for u in checked):
        row["link_status"] = "verified"
    elif checked:
        row["link_status"] = "partly verified"
    else:
        row["link_status"] = "not checked"
    return None


def dedupe_key(row: dict) -> str:
    if row.get("type") in {"signal", "competitor-deal"}:
        return row["type"] + ":" + norm(row.get("name"))
    return norm(row.get("name")) + "|" + norm(row.get("org"))


def build(params: dict, today: dt.date) -> tuple[list[dict], list[dict], dict]:
    kept: dict[str, dict] = {}
    rejected: list[dict] = []
    lanes = {}
    checks = load_link_check()
    for path in sorted(RAW.glob("*.json")):
        lane = path.stem
        try:
            rows = json.loads(path.read_text())
        except json.JSONDecodeError as exc:
            rejected.append({"lane": lane, "name": path.name, "reasons": [f"invalid JSON: {exc}"]})
            continue
        if not isinstance(rows, list):
            rows = rows.get("targets", []) if isinstance(rows, dict) else []
        lanes[lane] = {"raw": len(rows), "kept": 0}
        for row in rows:
            if not isinstance(row, dict):
                continue
            reasons = validate(row, params, today)
            if reasons:
                rejected.append({"lane": lane, "name": row.get("name"), "reasons": reasons})
                continue
            row = dict(row)
            row["lane"] = lane
            row["evidence"] = [u for u in row["evidence"] if isinstance(u, str) and u.startswith("http")]
            dead = apply_link_check(row, checks)
            if dead:
                rejected.append({"lane": lane, "name": row.get("name"), "reasons": [dead]})
                continue
            row["score"], row["priority"] = score(row, params, today)
            row["identity_needs_ok"] = (
                uses_founder_identity(row) and not params["outreach"].get("founder_identity_approved", False)
            )
            key = dedupe_key(row)
            prior = kept.get(key)
            if prior:
                # Keep the stronger row; merge the evidence so nothing is lost.
                merged_ev = list(dict.fromkeys(prior["evidence"] + row["evidence"]))
                winner = row if row["score"] > prior["score"] else prior
                winner["evidence"] = merged_ev
                kept[key] = winner
                continue
            kept[key] = row
            lanes[lane]["kept"] += 1
    targets = sorted(kept.values(), key=lambda r: (-r["score"], r.get("deadline") or "9999", r["name"]))
    for i, row in enumerate(targets, 1):
        row["rank"] = i
        row["id"] = re.sub(r"\s+", "-", norm(f"{row['name']} {row.get('org') or ''}"))[:80]
    return targets, rejected, lanes


def summary(targets: list[dict], today: dt.date) -> dict:
    def count(pred):
        return sum(1 for t in targets if pred(t))

    soon = [t for t in targets if (d := parse_date(t.get("deadline"))) and 0 <= (d - today).days <= 30]
    return {
        "total": len(targets),
        "investor": count(lambda t: t["hunt"] == "investor" and t["type"] != "signal"),
        "growth": count(lambda t: t["hunt"] == "growth" and t["type"] != "signal"),
        "social": count(lambda t: t["hunt"] == "social"),
        "sponsorship": count(lambda t: t["hunt"] == "sponsorship" and t["type"] != "competitor-deal"),
        "competitor_deals": count(lambda t: t["type"] == "competitor-deal"),
        "signals": count(lambda t: t["type"] == "signal"),
        "high": count(lambda t: t["priority"] == "High" and t["type"] != "signal"),
        "deadlines_30d": len(soon),
        "ready_to_send": count(lambda t: t["type"] not in {"signal", "competitor-deal"} and t.get("contact_url")
                               and t.get("opener") and not t.get("identity_needs_ok")),
        "identity_needs_ok": count(lambda t: t.get("identity_needs_ok")),
    }


def render(data: dict) -> str:
    template = (ROOT / "template.html").read_text()
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    return (
        template.replace("/*__DATA__*/null", payload)
        .replace("__GENERATED__", html.escape(data["generated"]))
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate only")
    ap.add_argument("--today", help="override today's date (YYYY-MM-DD)")
    args = ap.parse_args()

    params = load_params()
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()
    targets, rejected, lanes = build(params, today)

    print(f"{len(targets)} targets kept, {len(rejected)} rejected")
    for lane, c in lanes.items():
        print(f"  {lane:14} raw {c['raw']:3}  kept {c['kept']:3}")
    for r in rejected[:40]:
        print(f"  rejected [{r['lane']}] {r['name']}: {'; '.join(r['reasons'])}")
    if args.check:
        bad = [r for r in rejected if any("invalid JSON" in x or "never a guessed" in x for x in r["reasons"])]
        return 1 if bad else 0

    data = {
        "generated": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "today": today.isoformat(),
        "scope": params["scope"],
        "sprint": params["sprint"],
        "lanes": [{"id": l["id"], "title": l["title"], "hunt": l["hunt"], **lanes.get(l["id"], {"raw": 0, "kept": 0})}
                  for l in params["lanes"]],
        "summary": summary(targets, today),
        "targets": targets,
        "rejected_count": len(rejected),
    }
    (ROOT / "data" / "targets.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    SITE.mkdir(exist_ok=True)
    (SITE / "data.json").write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    (SITE / "index.html").write_text(render(data))
    print(f"wrote {SITE / 'index.html'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
