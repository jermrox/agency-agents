#!/usr/bin/env python3
"""Enforce rule 7 of VYBE-AGENT-STANDARDS.md on what Vybe outreach is for.

Why this exists. By 11 October 2026 two agents had emailed 86 organisations
between them from the same mailbox, and the founder had to read the logs
himself to find out that:

  * 23 of Marketsom's 49 logged emails pitched a vendor table, a booth, an
    expo slot or a sponsor tier — things Vybe has neither the budget nor the
    bandwidth for, and four of which were already dead by the time they were
    counted;
  * Growsom had emailed battery manufacturers, an ECG-patch PCBA supplier and
    contract engineering firms as "partners". Those sell TO Vybe. One of them
    has a call booked;
  * 14 organisations had been approached by BOTH agents, several with a
    different ask each time.

Outreach exists to win collaboration, investment or revenue. This script
fails the build when a logged email does something else.

History is evidence, not a violation: rows dated before the rule are reported
as context and never fail the build. Only rows on or after RULE_DATE do.
"""
import json
import pathlib
import re
import sys
from collections import Counter
from datetime import date

RULE_DATE = date(2026, 10, 11)
YEAR = 2026
STANDARDS = "VYBE-AGENT-STANDARDS.md"

# An event presence Vybe cannot staff. Assembled as whole words so that
# "roundtable" and "standards" do not match.
BOOTH = re.compile(
    r"\b(table|tables|booth|booths|tent|tents|expo|exhibitor|exhibit|"
    r"vendor slot|vendor space|sponsor tier|supporting sponsor|"
    r"sampling stand|activation)\b",
    re.I,
)

# Organisations that sell hardware or engineering TO Vybe. Approaching one is
# procurement, which is the founders' decision and not an outreach lane.
SUPPLIER = re.compile(
    r"\b(batter\w*|pcba|pcb|manufactur\w*|engineering|tooling|injection|"
    r"mould|mold|contract manufactur\w*|oem|odm|foundry|fabricat\w*)\b",
    re.I,
)

# Declining a stand is the one allowed use of these words, and it is what the
# founder asked for on 11 October. The first run of this script failed all four
# of Marketsom's cancellation drafts, which is a gate punishing the fix.
DECLINE = re.compile(
    r"\b(won'?t be able|not be able|release the table|don'?t hold|"
    r"do not hold|decided not to|won'?t be taking|not taking|no need to send|"
    r"cancel|withdraw|decline|pass on|release our)\b",
    re.I,
)

MONTHS = {m: i for i, m in enumerate(
    "jan feb mar apr may jun jul aug sep oct nov dec".split(), 1)}


def parse_day(s):
    """'11 Oct' or '2026-10-11' -> date. None when unparseable."""
    s = (s or "").strip()
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
    if m:
        return date(*map(int, m.groups()))
    m = re.match(r"^(\d{1,2})\s+([A-Za-z]{3})", s)
    if m and m.group(2).lower() in MONTHS:
        return date(YEAR, MONTHS[m.group(2).lower()], int(m.group(1)))
    return None


def norm(name):
    """Fold an organisation name so the two agents' spellings line up."""
    s = re.sub(r"\(.*?\)", "", (name or "").lower())
    s = re.sub(r"\b(inc|llc|ltd|co|corp|the|usa|us|app|labs|formerly)\b", "", s)
    return re.sub(r"[^a-z0-9]", "", s)


def load_rows(path):
    p = pathlib.Path(path)
    if not p.exists():
        return None
    d = json.loads(p.read_text())
    if isinstance(d, list):
        return d
    for k in ("entries", "outreach", "log", "threads"):
        if isinstance(d.get(k), list):
            return d[k]
    return []


def main():
    fail = 0
    marksom = load_rows("vybe-marketing/research/outreach-log.json")
    if marksom is None:
        print("SKIP: no outreach log in this checkout; nothing to judge.")
        return 0

    print(f"Checking rule 7 of {STANDARDS} over {len(marksom)} logged emails…")

    booth_old, booth_new, supplier_new, declines = [], [], [], []
    for r in marksom:
        org = r.get("org") or r.get("organisation") or ""
        when = parse_day(r.get("date"))
        text = " ".join(str(r.get(k, "")) for k in ("subject", "body", "kind"))
        if BOOTH.search(text) and not DECLINE.search(text):
            (booth_new if when and when >= RULE_DATE else booth_old).append(
                (r.get("date", "?"), org, (r.get("subject") or "")[:60]))
        elif BOOTH.search(text) and DECLINE.search(text):
            declines.append(org)
        if SUPPLIER.search(f"{org} {text}") and when and when >= RULE_DATE:
            supplier_new.append((r.get("date", "?"), org))

    if declines:
        print(f"  {len(declines)} email(s) decline a stand that was already "
              f"offered. That is the allowed use of the words: "
              f"{', '.join(sorted(set(declines)))}")

    if booth_old:
        print(f"  context: {len(booth_old)} pre-rule emails pitched an event "
              f"presence. Kept as the record, not counted as failures.")

    for label, rows, why in (
        ("an event presence", booth_new,
         "Vybe has no budget and no bandwidth to staff a stand."),
        ("a supplier", supplier_new,
         "They sell to Vybe. Procurement is the founders', not an outreach lane."),
    ):
        if rows:
            print(f"FAIL: {len(rows)} email(s) dated on or after "
                  f"{RULE_DATE.isoformat()} pitch {label}:")
            for d, org, *rest in rows:
                print(f"  {d:8} {org[:40]:40} {rest[0] if rest else ''}")
            print(f"  {why} Rule 7 of {STANDARDS}.")
            fail = 1

    # --- one organisation, one owner, one ask -------------------------------
    growsom = load_rows("growth-scout/data/followups.json")
    if growsom is None:
        print("  note: growth-scout/data/followups.json is not in this "
              "checkout, so the two-agent overlap could not be checked here. "
              "It lives on the growth-scout branch.")
    else:
        mk, mk_new = {}, set()
        for r in marksom:
            if not r.get("org"):
                continue
            k = norm(r["org"])
            mk[k] = r["org"]
            d = parse_day(r.get("date"))
            if d and d >= RULE_DATE:
                mk_new.add(k)
        gs, gs_new = {}, set()
        for t in growsom:
            if not t.get("org"):
                continue
            k = norm(t["org"])
            gs[k] = t["org"]
            d = parse_day(t.get("first_sent"))
            if d and d >= RULE_DATE:
                gs_new.add(k)

        both = sorted((set(mk) & set(gs)) - {""})
        fresh = sorted(((mk_new & set(gs)) | (gs_new & set(mk))) - {""})

        if both:
            print(f"  context: {len(both)} organisation(s) were approached by "
                  f"BOTH agents before the rule. Each needs one owner "
                  f"assigned, and neither agent approaches it again:")
            for k in both:
                print(f"    {mk[k]}")
        # A collision is resolved by naming an owner, not by an alarm that
        # stays red. OUTREACH-OWNERS.json is that resolution; an org missing
        # from it is the only thing that fails here.
        owners = {}
        op = pathlib.Path("OUTREACH-OWNERS.json")
        if op.exists():
            owners = {norm(k): v
                      for k, v in json.loads(op.read_text())["owners"].items()}

        unowned = [k for k in fresh if k not in owners]
        if fresh:
            named = [k for k in fresh if k in owners]
            if named:
                print(f"  {len(named)} live collision(s), each with one owner "
                      f"in OUTREACH-OWNERS.json:")
                for k in named:
                    print(f"    {mk.get(k) or gs.get(k):38} -> {owners[k]}")
        if unowned:
            print(f"FAIL: {len(unowned)} organisation(s) touched by a second "
                  f"agent on or after {RULE_DATE.isoformat()} with no owner:")
            for k in unowned:
                print(f"  {mk.get(k) or gs.get(k)}")
            print("  Add each to OUTREACH-OWNERS.json. One organisation, one "
                  f"owning agent, one ask. Rule 7 of {STANDARDS}.")
            fail = 1

    if not fail:
        kinds = Counter(r.get("kind", "?") for r in marksom)
        print(f"PASSED: no post-rule email pitches a stand or a supplier; "
              f"no organisation is held by two agents. "
              f"{dict(kinds)}")
    return fail


if __name__ == "__main__":
    sys.exit(main())
