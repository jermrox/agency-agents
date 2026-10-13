#!/usr/bin/env python3
"""Lint the hub-owned Vybe routines in vybe-ops/routines/ (rule 15).

A routine is the standing order an agent runs on. It fails this check when it
contradicts VYBE-AGENT-STANDARDS.md in a way the hub has already seen break
an agent: an order the founder reversed left active, the founder's voice
where John's belongs, a session connector named as something to use, no
"never end a run waiting" line, no rule-14 line on a routine that drafts
email, a foreign account string, or a model name.
"""
from __future__ import annotations
import re, sys, pathlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROUTINES = sorted((ROOT / "vybe-ops" / "routines").glob("*.md"))
REQUIRED_FRONT = ("agent", "session", "triggers", "cron", "owner", "last_reconciled")
# Assembled from pieces so this file is not itself a source of the strings.
FOREIGN = ["jeremylahn" + "-i-grow", "i" + "-grow.co", "i" + "-grow", "lscops" + ".com", "debouillet" + ".com"]
MODEL_NAMES = re.compile(r"claude-(opus|sonnet|haiku|fable)|\bopus\b|\bsonnet\b", re.I)
CONNECTORS = re.compile(r"mcp__(Gmail|Calendly|Google_Drive|Google_Calendar|Slack|Airtable)__", re.I)
DRAFTS = re.compile(r"\b(draft|outreach|opener|pitch)\b", re.I)

def front_matter(text: str) -> dict:
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return {}
    out = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            out[k.strip()] = v.split("#")[0].strip()
    return out

def main() -> int:
    fails: list[str] = []
    if not ROUTINES:
        print("FAIL: no routines found under vybe-ops/routines/")
        return 1
    for path in ROUTINES:
        if path.name == "README.md":
            continue
        text = path.read_text(encoding="utf-8")
        rel = path.relative_to(ROOT)
        fm = front_matter(text)
        for k in REQUIRED_FRONT:
            if k not in fm or not fm[k]:
                fails.append(f"{rel}: front matter is missing '{k}'")
        if fm.get("owner", "").lower() != "hub":
            fails.append(f"{rel}: owner must be 'hub' (rule 15)")
        low = text.lower()
        if "rule 13" not in low or "never end" not in low:
            fails.append(f"{rel}: no rule-13 'never end a run waiting' line")
        if "founder's voice" in low or "founder’s voice" in low:
            fails.append(f"{rel}: drafts in the founder's voice; rule 11 says John's")
        if re.search(r"research, not drafts(?![^\n]*supersed)", low):
            fails.append(f"{rel}: 'research, not drafts' is active; the founder reversed it on 12 Oct")
        if "do not draft" in low and "supersed" not in low:
            fails.append(f"{rel}: 'do not draft' is active; rule 11 requires drafting as John")
        for needle in FOREIGN:
            if needle in low:
                fails.append(f"{rel}: contains a foreign account string (rule 4)")
                break
        if MODEL_NAMES.search(text):
            fails.append(f"{rel}: names a model")
        for m in CONNECTORS.finditer(text):
            window = text[max(0, m.start() - 80): m.start()].lower()
            if not re.search(r"never|not|no |forbid|banned", window):
                fails.append(f"{rel}: names a session connector without forbidding it")
                break
        drafts_email = DRAFTS.search(text) and "john" in low and fm.get("agent", "").lower() in ("marketsom", "growsom", "instasom")
        if drafts_email:
            if "director of growth" not in low:
                fails.append(f"{rel}: drafts email but never names John, Director of Growth (rule 11)")
            if "rule 14" not in low or "persuasion" not in low:
                fails.append(f"{rel}: drafts email but carries no rule-14 persuasion line")
        if "vybe-agent-standards.md" not in low:
            fails.append(f"{rel}: does not point at VYBE-AGENT-STANDARDS.md")
    if fails:
        print(f"FAIL: {len(fails)} routine finding(s)")
        for f in fails:
            print("  " + f)
        return 1
    print(f"OK: {sum(1 for p in ROUTINES if p.name != 'README.md')} routines pass the rule-15 lint")
    return 0

if __name__ == "__main__":
    sys.exit(main())
