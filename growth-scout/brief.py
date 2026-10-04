#!/usr/bin/env python3
"""Weekly morning brief for Vybe Growth Scout.

Reads data/targets.json (built by build.py) and prints the brief as HTML
(default) or plain text (--text). Counts and rows come only from the board;
nothing is added or guessed here. Use --since YYYY-MM-DD to mark what changed
since the previous brief (compares against data/last_brief.json when present).
"""
from __future__ import annotations
import argparse, datetime as dt, html, json, pathlib

ROOT = pathlib.Path(__file__).parent
STATE = ROOT / "data" / "last_brief.json"
DASH = "https://claude.ai/artifact/6Lp18yuh93GaXbuqjcjZbu"


def load():
    return json.loads((ROOT / "data" / "targets.json").read_text())


def days_to(deadline, today):
    return (dt.date.fromisoformat(deadline) - today).days


def build(save: bool):
    d = load()
    today = dt.date.fromisoformat(d["today"])
    rows = d["targets"]
    prev = set()
    if STATE.exists():
        prev = set(json.loads(STATE.read_text()).get("ids", []))
    new = [r for r in rows if r["id"] not in prev] if prev else []
    deadlines = sorted(
        (r for r in rows if r.get("deadline") and 0 <= days_to(r["deadline"], today) <= 30),
        key=lambda r: r["deadline"],
    )
    top = [r for r in rows if r.get("sendable")][:10]
    held = [r for r in rows if r.get("identity_needs_ok")]
    if save:
        STATE.write_text(json.dumps({"date": d["today"], "ids": [r["id"] for r in rows]}))
    return d, today, deadlines, top, new, held


def fmt(r):
    return {
        "name": r["name"],
        "type": r["type"],
        "ask": r.get("ask") or "",
        "url": r.get("contact_url") or (r.get("evidence") or [""])[0],
        "deadline": r.get("deadline"),
    }


def render(text: bool, save: bool) -> str:
    d, today, deadlines, top, new, held = build(save)
    s = d["summary"]
    L = []
    L.append(f"Vybe Growth Scout: weekly brief, {today:%a %d %b %Y}")
    L.append("")
    L.append(
        f"Board: {s['total']} verified targets ({s['investor']} investor, {s['growth']} growth, "
        f"{s['social']} social, {s['sponsorship']} sponsorship, {s['app_partners']} app partners). "
        f"{s['high']} High priority. {s['ready_to_send']} drafts ready."
    )
    if new:
        L.append(f"New since last brief: {len(new)}.")
    L.append("")
    L.append(f"DEADLINES IN THE NEXT 30 DAYS ({len(deadlines)})")
    for r in deadlines:
        f = fmt(r)
        L.append(f"- {f['deadline']} ({days_to(f['deadline'], today)}d): {f['name']} [{f['type']}] {f['url']}")
    if not deadlines:
        L.append("- none")
    L.append("")
    L.append("TOP 10 TO CONTACT THIS WEEK")
    for i, r in enumerate(top, 1):
        f = fmt(r)
        L.append(f"{i}. {f['name']} [{f['type']}]: {f['ask']} {f['url']}")
    if new:
        L.append("")
        L.append("NEW ON THE BOARD")
        for r in new[:15]:
            L.append(f"- {r['name']} [{r['type']}]")
    L.append("")
    L.append("WAITING ON THE FOUNDER")
    L.append(
        f"- {len(held)} drafts are held until founder identity wording is approved "
        "(founder_identity_approved in params.toml)."
    )
    L.append("- Application drafts in growth-scout/applications still have [FOUNDER] fields to fill.")
    L.append("")
    L.append(f"Dashboard: {DASH}")
    L.append("Drafts only: nothing on the board has been contacted. Targets are people we found, not people we have spoken to.")
    plain = "\n".join(L)
    if text:
        return plain
    out = ["<div style='font-family:system-ui,sans-serif;max-width:640px;line-height:1.45'>"]
    for line in L:
        if not line:
            continue
        e = html.escape(line)
        if line.isupper() or line.startswith(("DEADLINES", "TOP 10", "NEW ON", "WAITING")):
            out.append(f"<h3 style='margin:18px 0 6px'>{e.title()}</h3>")
        elif line.startswith("Vybe Growth"):
            out.append(f"<h2>{e}</h2>")
        elif line.startswith(("- ", "1", "2", "3", "4", "5", "6", "7", "8", "9")):
            out.append(f"<div style='margin:3px 0'>{e}</div>")
        else:
            out.append(f"<p>{e}</p>")
    out.append("</div>")
    return "\n".join(out)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--text", action="store_true")
    ap.add_argument("--save", action="store_true", help="record this brief's ids for next week's diff")
    a = ap.parse_args()
    print(render(a.text, a.save))
