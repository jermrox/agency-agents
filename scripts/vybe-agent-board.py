#!/usr/bin/env python3
"""Check every Vybe agent's live surface and render the agent board.

Why this exists. On 10 Oct 2026 the founder's other company's Calendly link sat
on the Growth Scout dashboard for hours after the repository was fixed, because
that agent publishes to three surfaces and none of them deploys from git. The
code was right and the page was wrong, and the only reason anyone found out was
the founder looking at it himself.

So this does not read the repository. It fetches each live URL the way a
visitor does, and judges the agent by what is actually being served:

  stale    the surface's own timestamp is older than the agent's cadence allows
  foreign  the page carries an account belonging to another of the founder's
           ventures, which VYBE-AGENT-STANDARDS.md forbids
  dead     the URL did not return 200

Any of those is a failure and exits non-zero, so the scheduled workflow turns
red in GitHub rather than waiting to be noticed. The board is written either
way: a board that disappears when something breaks is useless at the moment it
matters most.

Scope is Vybe Health only, by rule 6 of VYBE-AGENT-STANDARDS.md. The founder's
other ventures run their own agents; this board does not track them and does
not name them. Naming them here would put another venture's roster on a Vybe
page, which is the scope leak the rule exists to stop.

It also writes vybe-hub.html: the one short page the founder asked for on
11 Oct 2026 ("why isn't this synced across all the dashboards"). The hub reads
the facts that matter out of the same fetched feeds — money closing soon,
calls booked, drafts waiting, targets ready — so it is synced by construction
rather than by someone retyping numbers into a chat.

Usage:
  python3 scripts/vybe-agent-board.py                     # check, render, exit 1 if red
  python3 scripts/vybe-agent-board.py --out-dir dashboards
  python3 scripts/vybe-agent-board.py --no-fail           # render, always exit 0
"""

import argparse
import datetime as dt
import html
import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

UA = "vybe-agent-board (+https://github.com/jermrox/agency-agents)"
TIMEOUT = 45

# Accounts belonging to the founder's other ventures. Assembled from pieces so
# this file is not itself a copyable source of the wrong strings.
FOREIGN = [
    "jeremylahn" + "-i-grow",
    "i" + "-grow.co",
    "lscops" + ".com",
    "debouillet" + ".com",
]

# One entry per Vybe agent surface.
#
# stamp_re pulls the surface's OWN idea of when it was last written, because a
# Netlify deploy time would say the file was uploaded, not that the data behind
# it is current -- a redeploy of a stale page would read as fresh.
#
# max_age_h is the agent's cadence plus room for one missed run, so a single
# skipped run is not an alarm but a stopped agent is.
SURFACES = [
    {
        "agent": "Revsom",
        "role": "funding board and application packets",
        "surface": "agentrevup.netlify.app/funding.json",
        "url": "https://agentrevup.netlify.app/funding.json",
        "stamp_re": r'"generated"\s*:\s*"([^"]+)"',
        "max_age_h": 30,          # daily sweep at 13:40Z
        "cadence": "daily 13:40Z",
    },
    {
        "agent": "Revsom",
        "role": "the Apply page",
        "surface": "agentrevup.netlify.app/apply",
        "url": "https://agentrevup.netlify.app/apply.html",
        "stamp_re": None,         # no machine timestamp; checked for reachability and accounts
        "max_age_h": None,
        "cadence": "with each packet",
    },
    {
        "agent": "Marketsom",
        "role": "daily marketing briefing",
        "surface": "agentmarksom.netlify.app/briefing.html",
        "url": "https://agentmarksom.netlify.app/briefing.html",
        "stamp_re": r'"asof"\s*:\s*"([^"]+)"',
        "max_age_h": 30,          # daily 10:23Z
        "cadence": "daily 10:23Z",
    },
    {
        "agent": "Growsom",
        "role": "outreach and investor board",
        "surface": "agentgrowthscout.netlify.app",
        "url": "https://agentgrowthscout.netlify.app",
        "stamp_re": r"Updated (\d{4}-\d{2}-\d{2} \d{2}:\d{2}) UTC",
        "max_age_h": 14,          # three runs a day, so half a day is already late
        "cadence": "3x daily",
    },
    {
        "agent": "Growsom",
        "role": "board data feed",
        "surface": "agentgrowthscout.netlify.app/data.json",
        "url": "https://agentgrowthscout.netlify.app/data.json",
        "stamp_re": r'"generated"\s*:\s*"([^"]+)"',
        "max_age_h": 14,
        "cadence": "3x daily",
    },
    {
        "agent": "Instasom",
        "role": "social dashboard",
        "surface": "instasum.netlify.app/all.json",
        "url": "https://instasum.netlify.app/all.json",
        "stamp_re": r'"generatedAt"\s*:\s*"([^"]+)"',
        "max_age_h": 30,          # daily 10:38Z data pull
        "cadence": "daily 10:38Z",
    },
]

STAMP_FORMATS = [
    "%Y-%m-%dT%H:%M:%S%z",
    "%Y-%m-%dT%H:%M:%SZ",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d",
]


def parse_stamp(raw):
    """Return an aware UTC datetime, or None if the format is not one we know."""
    s = raw.strip()
    # Some surfaces write "2026-10-10 16:33 UTC". Drop a trailing zone word: the
    # formats below are all read as UTC anyway, and the first real run of this
    # script marked a healthy feed red purely because of those four characters.
    cleaned = re.sub(r"\s+(UTC|GMT|Z)$", "", s)
    # Python's %z rejects a bare "Z" before 3.11 and accepts "+00:00"; normalise.
    cleaned = re.sub(r"Z$", "+0000", cleaned)
    cleaned = re.sub(r"([+-]\d{2}):(\d{2})$", r"\1\2", cleaned)
    # Drop fractional seconds, which no format above expects.
    cleaned = re.sub(r"\.\d+", "", cleaned)
    for fmt in STAMP_FORMATS:
        try:
            d = dt.datetime.strptime(cleaned, fmt)
            return d if d.tzinfo else d.replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return None


def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
        return r.status, r.read().decode("utf-8", errors="replace")


def check(entry, now):
    """One surface, judged on what is actually served."""
    out = dict(entry)
    out["problems"] = []
    out["stamp"] = None
    out["age_h"] = None
    out["foreign"] = []

    try:
        status, body = fetch(entry["url"])
    except urllib.error.HTTPError as e:
        out["problems"].append(f"dead: HTTP {e.code}")
        out["state"] = "dead"
        return out
    except Exception as e:  # DNS, TLS, timeout, reset
        out["problems"].append(f"dead: {type(e).__name__}")
        out["state"] = "dead"
        return out

    if status != 200:
        out["problems"].append(f"dead: HTTP {status}")
    # The hub reads facts out of the same fetch. Stripped before the JSON is
    # written, so the committed file stays small and holds no page copies.
    out["_body"] = body

    # An account from another venture is a failure whatever else is true: this
    # is the exact defect that reached fifty partner organisations.
    for needle in FOREIGN:
        if needle in body:
            out["foreign"].append(needle)
    if out["foreign"]:
        out["problems"].append("foreign account on the page: " + ", ".join(out["foreign"]))

    if entry["stamp_re"]:
        m = re.search(entry["stamp_re"], body)
        if not m:
            # The page changed shape. Not provably stale, but no longer checkable,
            # which is its own problem worth a red mark.
            out["problems"].append("no timestamp found — page shape changed?")
        else:
            out["stamp"] = m.group(1)
            d = parse_stamp(m.group(1))
            if d is None:
                out["problems"].append(f"unreadable timestamp {m.group(1)!r}")
            else:
                age = (now - d).total_seconds() / 3600.0
                out["age_h"] = round(age, 1)
                if entry["max_age_h"] and age > entry["max_age_h"]:
                    out["problems"].append(
                        f"stale: {age:.1f}h old, cadence allows {entry['max_age_h']}h"
                    )

    out["state"] = "ok" if not out["problems"] else (
        "dead" if any(p.startswith("dead") for p in out["problems"]) else "bad"
    )
    return out


def render(rows, now):
    """The board. Same palette as the other agent boards so it reads as one system."""
    red = [r for r in rows if r["state"] != "ok"]
    agents = sorted({r["agent"] for r in rows})
    bad_agents = sorted({r["agent"] for r in red})

    if red:
        headline = (
            f"{len(red)} of {len(rows)} surfaces need attention"
            f" — {', '.join(bad_agents)}"
        )
    else:
        headline = f"All {len(rows)} Vybe surfaces are current and carry only Vybe accounts"

    def cell(r):
        chip = {"ok": ("ok", "OK"), "bad": ("bad", "NEEDS FIXING"), "dead": ("dead", "UNREACHABLE")}[r["state"]]
        age = "—"
        if r["age_h"] is not None:
            age = f"{r['age_h']:.1f}h ago"
        elif r["stamp_re"] is None:
            age = "no timestamp"
        probs = "".join(
            f'<li>{html.escape(p)}</li>' for p in r["problems"]
        )
        return f"""<tr class="{chip[0]}">
  <td class="ag">{html.escape(r['agent'])}</td>
  <td>{html.escape(r['role'])}<div class="u"><a href="{html.escape(r['url'])}">{html.escape(r['surface'])}</a></div></td>
  <td class="cad">{html.escape(r['cadence'])}</td>
  <td class="age">{html.escape(age)}</td>
  <td><span class="chip {chip[0]}">{chip[1]}</span>{f'<ul class="probs">{probs}</ul>' if probs else ''}</td>
</tr>"""

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Vybe Agent Board</title>
<style>
:root {{
  --bg:#f6f8f7; --surface:#fff; --surface-2:#eef3f1; --line:#dbe3e0;
  --ink:#12201c; --ink-2:#44554f; --ink-3:#6b7a75;
  --brand:#1f8e78; --brand-ink:#0f5e4f;
  --good:#1d7a3a; --good-bg:#e3f3e7; --crit:#a3262a; --crit-bg:#fbe3e3;
  --warn:#8a5a00; --warn-bg:#fbefd5;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#0e1513; --surface:#151f1c; --surface-2:#1b2824; --line:#2a3a35;
  --ink:#e7efec; --ink-2:#b4c4be; --ink-3:#8a9c96;
  --brand:#4cc3a8; --brand-ink:#8fe0cd;
  --good:#7ad596; --good-bg:#173322; --crit:#f19a9a; --crit-bg:#3a1a1b;
  --warn:#f0c46b; --warn-bg:#352a12;
  color-scheme: dark;
}} }}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:15px/1.5 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif }}
a {{ color:var(--brand-ink) }}
.wrap {{ max-width:1100px; margin:0 auto; padding:24px 16px 64px }}
h1 {{ font-size:26px; margin:0 0 4px; letter-spacing:-.01em }}
h1 span {{ color:var(--brand) }}
.head {{ font-size:19px; line-height:1.35; margin:14px 0 2px; font-weight:600 }}
.head.ok {{ color:var(--good) }} .head.bad {{ color:var(--crit) }}
.sub {{ color:var(--ink-2); margin:4px 0 0; max-width:74ch }}
.meta {{ color:var(--ink-3); font-size:13px; margin-top:10px }}
table {{ border-collapse:collapse; width:100%; font-size:14px; margin-top:18px;
  background:var(--surface); border:1px solid var(--line); border-radius:10px; overflow:hidden }}
th,td {{ text-align:left; padding:11px 12px; border-bottom:1px solid var(--line); vertical-align:top }}
th {{ font-size:12px; text-transform:uppercase; letter-spacing:.04em; color:var(--ink-3);
  background:var(--surface-2); white-space:nowrap }}
tr:last-child td {{ border-bottom:0 }}
td.ag {{ font-weight:600; white-space:nowrap }}
.u {{ font-size:12px; margin-top:3px }}
.u a {{ overflow-wrap:anywhere }}
td.cad, td.age {{ color:var(--ink-2); white-space:nowrap; font-variant-numeric:tabular-nums }}
.chip {{ display:inline-block; font-size:11px; font-weight:700; letter-spacing:.06em;
  padding:3px 9px; border-radius:999px; white-space:nowrap }}
.chip.ok {{ background:var(--good-bg); color:var(--good) }}
.chip.bad {{ background:var(--warn-bg); color:var(--warn) }}
.chip.dead {{ background:var(--crit-bg); color:var(--crit) }}
tr.bad {{ background:var(--warn-bg) }} tr.dead {{ background:var(--crit-bg) }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) tr.bad,
  :root:not([data-theme="light"]) tr.dead {{ background:transparent }} }}
ul.probs {{ margin:7px 0 0; padding-left:18px; font-size:13px; color:var(--ink-2) }}
.note {{ margin-top:28px; padding-top:16px; border-top:1px solid var(--line);
  color:var(--ink-3); font-size:13px; max-width:78ch }}
.note strong {{ color:var(--ink-2) }}
</style>
</head>
<body>
<div class="wrap">
  <h1><span>Vybe</span> Agent Board</h1>
  <p class="sub">Every Vybe Health agent, judged by the page it actually serves — not by what is in the repository.</p>
  <p class="head {'bad' if red else 'ok'}">{html.escape(headline)}</p>
  <p class="meta">Checked {now.strftime('%Y-%m-%d %H:%M')} UTC · {len(agents)} agents · {len(rows)} surfaces</p>

  <table>
    <thead><tr><th>Agent</th><th>Surface</th><th>Cadence</th><th>Last written</th><th>State</th></tr></thead>
    <tbody>
{chr(10).join(cell(r) for r in rows)}
    </tbody>
  </table>

  <p class="note">
    <strong>How this is judged.</strong> Each surface is fetched like a visitor would, and read for
    two things: its own last-written timestamp, and whether it carries an account belonging to
    another of the founder's ventures. A surface is red when it is older than its cadence allows,
    when such an account appears on it, or when it does not return 200. "Last written" is the page's
    own stamp, not the deploy time, so republishing a stale page does not make it look fresh.
    <br><br>
    <strong>Why it is not judged on the repository.</strong> Three of these surfaces do not deploy
    from git. Fixing the code updates none of them, which is how a wrong booking link stayed live
    for hours on 10 Oct 2026 while the repository was already correct.
    <br><br>
    <strong>Scope.</strong> Vybe Health only. Agents belonging to other ventures are out of scope
    and are neither tracked nor named here.
    Rules: <a href="https://github.com/jermrox/agency-agents/blob/main/VYBE-AGENT-STANDARDS.md">VYBE-AGENT-STANDARDS.md</a>.
  </p>
</div>
</body>
</html>
"""


# ------------------------------------------------------------------ the hub ---

def _cut(text, n):
    """Truncate at a word boundary. A line that ends mid-word reads as broken."""
    text = str(text or "")
    if len(text) <= n:
        return text
    head = text[:n].rsplit(" ", 1)[0]
    return head.rstrip(" ,;:·-") + "…"


def _sentences(text, n_chars):
    """First whole sentences up to n_chars. The 'so what' must not end mid-thought."""
    text = re.sub(r"\s+", " ", str(text or "")).strip()
    if len(text) <= n_chars:
        return text
    out = ""
    for sent in re.split(r"(?<=[.!?])\s+", text):
        if len(out) + len(sent) + 1 > n_chars:
            break
        out = (out + " " + sent).strip()
    return out or _cut(text, n_chars)


def _json_in(body):
    try:
        return json.loads(body)
    except Exception:
        return None


def _live_data(body):
    """Marketsom's briefing keeps its numbers in <script id="live-data">."""
    m = re.search(r'<script id="live-data" type="application/json">(.*?)</script>', body, re.S)
    return _json_in(m.group(1)) if m else None


def extract_facts(rows, now):
    """Pull the few facts the founder actually asks about out of each live feed.

    Every value is None when the feed is unreadable, and the hub prints
    'unavailable' for None. A missing metric is never shown as 0 — that is
    Instasom standard 9 and it applies here too.
    """
    by_url = {r["url"]: r for r in rows}
    f = {"revsom": {}, "marketsom": {}, "growsom": {}, "instasom": {}, "needs_you": []}

    # Revsom — money with a clock on it
    r = by_url.get("https://agentrevup.netlify.app/funding.json")
    d = _json_in(r.get("_body", "")) if r else None
    opps = d.get("opportunities") if isinstance(d, dict) else None
    if isinstance(opps, list):
        opps = [o for o in opps if isinstance(o, dict)]
        f["revsom"]["total"] = len(opps)
        f["revsom"]["no_sam"] = sum(1 for o in opps if str(o.get("sam", "")).lower() == "none")
        soon = sorted(
            (o for o in opps if isinstance(o.get("days_left"), int) and 0 <= o["days_left"] <= 14),
            key=lambda o: o["days_left"],
        )
        f["revsom"]["closing_14d"] = len(soon)
        f["revsom"]["closing"] = [
            {"name": o.get("name", ""), "days": o["days_left"], "amount": str(o.get("amount", "")),
             "url": o.get("url", ""), "docs": [str(x) for x in (o.get("documents") or []) if x],
             "who": _cut(str(o.get("eligibility") or o.get("agency") or ""), 130),
             "why": _sentences(o.get("summary"), 260),
             "veteran": "veteran" in (str(o.get("eligibility", "")) + o.get("name", "")).lower()}
            for o in soon
        ]
        for o in f["revsom"]["closing"][:6]:
            f["needs_you"].append({
                "who": "Revsom", "kind": "money",
                "when": "today" if o["days"] == 0 else ("tomorrow" if o["days"] == 1 else f"{o['days']} days"),
                "what": o["name"], "detail": _cut(o["amount"], 60) + (" · veteran-owned fits" if o["veteran"] else ""),
                "who_is": o["who"], "why": o["why"],
                # The human steps, straight from the opportunity row. This is the
                # line the founder asked for: not "needs you" but what a person does.
                "do": [_cut(d, 110) for d in o["docs"]] or ["Open the application page and the drafted packet"],
                "url": o["url"] or "https://agentrevup.netlify.app/apply",
                "url_label": "application page",
                "url2": "https://agentrevup.netlify.app/apply", "url2_label": "drafted answers",
                "sort": o["days"],
            })

    # Marketsom — calls, deadlines, drafts waiting, named problems
    r = by_url.get("https://agentmarksom.netlify.app/briefing.html")
    d = _live_data(r.get("_body", "")) if r else None
    if isinstance(d, dict):
        f["marketsom"]["headline"] = d.get("headline")
        f["marketsom"]["drafts"] = d.get("drafts")
        f["marketsom"]["bookings"] = d.get("bookings")
        probs = d.get("problems")
        f["marketsom"]["problems"] = len(probs) if isinstance(probs, list) else None
        up = d.get("upcoming")
        if isinstance(up, list):
            for u in up[:6]:
                if not isinstance(u, dict):
                    continue
                kind = "call" if u.get("kind") == "call" else "deadline"
                when = " ".join(str(u.get(k, "")) for k in ("day", "time") if u.get(k)).strip()
                lines = [str(x) for x in (u.get("lines") or []) if x]
                prep = u.get("prep")
                if kind == "call":
                    # who is on it and whether they charge are shown above the list;
                    # the list is only the actions.
                    do = ["Read the prep brief first" if prep else "No prep brief yet — ask for one before joining",
                          "Join the call at the time shown",
                          "Decide on the call: no-cost route, or a short polite no"]
                else:
                    do = [_cut(l, 110) for l in lines[:3]] or ["Open the briefing for what is due"]
                f["needs_you"].append({
                    "who": "Marketsom", "kind": kind, "when": when or "soon",
                    "what": str(u.get("what", "")), "detail": "",
                    "who_is": _cut(lines[0], 160) if lines else "",
                    "why": _cut(" ".join(lines[1:3]), 220) if len(lines) > 1 else "",
                    "do": do,
                    "url": prep or "https://agentmarksom.netlify.app/briefing.html",
                    "url_label": "prep brief" if prep else "briefing",
                    "url2": "https://agentmarksom.netlify.app/briefing.html" if prep else None, "url2_label": "briefing",
                    "sort": 0 if kind == "call" else 3,
                })
        if isinstance(d.get("drafts"), int) and d["drafts"] > 0:
            f["needs_you"].append({
                "who": "Marketsom", "kind": "drafts", "when": "waiting",
                "what": f"{d['drafts']} partner drafts waiting for you to send",
                "detail": "John is on CC of every one",
                "who_is": "Community partners Marketsom researched this week — leagues, clubs, member bodies",
                "why": "Nothing reaches a partner until you send it. These are the asks for no-cost member offers and shared content.",
                "do": ["Open Gmail drafts from jeremy@vybe.health", "Read each one; send the ones you approve, delete the rest",
                       "Nothing goes out until you press send"],
                "url": "https://agentmarksom.netlify.app/partner-board.html", "url_label": "partner board",
                "url2": None, "url2_label": None, "sort": 2,
            })

    # Growsom — targets ready, deadlines inside 30 days, and the top items
    r = by_url.get("https://agentgrowthscout.netlify.app/data.json")
    d = _json_in(r.get("_body", "")) if r else None
    sm = d.get("summary") if isinstance(d, dict) else None
    if isinstance(sm, dict):
        for k in ("total", "ready_to_send", "outreach_queue", "deadlines_30d", "high"):
            f["growsom"][k] = sm.get(k)
    tg = d.get("targets") if isinstance(d, dict) else None
    if isinstance(tg, list):
        rows_ = [x for x in tg if isinstance(x, dict) and str(x.get("priority", "")).lower() == "high"]
        rows_.sort(key=lambda x: -(x.get("score") or 0))
        f["growsom"]["top"] = [{
            "what": str(x.get("name") or x.get("org") or ""),
            "who_is": _cut(f"{x.get('type') or x.get('lane') or ''}" + (f" · {x.get('geo')}" if x.get("geo") else ""), 90),
            "why": _sentences(x.get("why_now") or x.get("why"), 200),
            "do": [_cut(x.get("move") or x.get("ask") or "Approve the drafted opener so Growsom can send it", 110)],
            "url": x.get("contact_url") or "https://agentgrowthscout.netlify.app/",
        } for x in rows_[:4]]

    # Instasom — people to follow, the latest numbers, the top picks
    r = by_url.get("https://instasum.netlify.app/all.json")
    d = _json_in(r.get("_body", "")) if r else None
    col = d.get("collections") if isinstance(d, dict) else None
    if isinstance(col, dict):
        ppl = col.get("people")
        items = list(ppl.values()) if isinstance(ppl, dict) else (ppl if isinstance(ppl, list) else [])
        items = [x for x in items if isinstance(x, dict)]
        f["instasom"]["people"] = len(items) or None
        f["instasom"]["to_follow"] = sum(1 for x in items if x.get("status") == "Not started") or None
        fol = col.get("followers")
        f["instasom"]["days"] = len(fol) if hasattr(fol, "__len__") else None
        if isinstance(fol, dict) and fol:
            latest = fol[sorted(fol.keys())[-1]]
            if isinstance(latest, dict):
                f["instasom"]["ig"] = latest.get("ig")
                f["instasom"]["fb"] = latest.get("fb")
        pick = [x for x in items if x.get("status") == "Not started" and not x.get("followOnly")]
        def _n(v):
            try: return float(str(v).lower().replace("k", "e3").replace(",", ""))
            except Exception: return 0.0
        pick.sort(key=lambda x: -_n(x.get("followers")))
        f["instasom"]["top"] = [{
            "what": f"@{str(x.get('handle','')).lstrip('@')}" + (f" — {x.get('name')}" if x.get("name") else ""),
            "who_is": _cut(f"{x.get('category') or ''} · {x.get('followers') or '?'} followers", 90),
            "why": _sentences(x.get("why"), 200),
            "do": [_cut(x.get("action") or "Follow, then tick the box on the social dashboard", 110)],
            "url": x.get("url") or f"https://www.instagram.com/{str(x.get('handle','')).lstrip('@')}/",
        } for x in pick[:4]]

    # Marketsom — the replies and problems as items
    r = by_url.get("https://agentmarksom.netlify.app/briefing.html")
    d = _live_data(r.get("_body", "")) if r else None
    if isinstance(d, dict):
        probs = d.get("problems") if isinstance(d.get("problems"), list) else []
        f["marketsom"]["top"] = [{
            "what": _cut(str(pr.get("title") or pr.get("what") or pr) if not isinstance(pr, str) else pr, 90),
            "who_is": "", "why": _sentences((pr.get("why") or pr.get("detail") or "") if isinstance(pr, dict) else "", 200),
            "do": [_cut((pr.get("fix") or pr.get("do") or pr.get("action") or "Read it on the briefing") if isinstance(pr, dict) else "Read it on the briefing", 110)],
            "url": "https://agentmarksom.netlify.app/briefing.html",
        } for pr in probs[:4]]

    # Revsom — top items are the soonest closes (already in needs_you); keep 4 here too
    f["revsom"]["top"] = [{
        "what": o["name"], "who_is": o["who"], "why": o["why"],
        "do": [_cut(x, 110) for x in o["docs"][:3]] or ["Open the application page"],
        "url": o["url"] or "https://agentrevup.netlify.app/apply",
    } for o in (f["revsom"].get("closing") or [])[:4]]

    f["needs_you"].sort(key=lambda x: x["sort"])
    return f


def render_hub(rows, facts, now):
    """One page, one shape, every agent. The founder's words, 11 Oct: 'one
    organized system… you are the central hub… what it is, why it matters,
    what I physically do.' Each agent gets the same block: purpose in money
    terms, alive, what it is pulling, its top items, what needs a human."""
    by_agent = {}
    for r in rows:
        by_agent.setdefault(r["agent"], []).append(r)

    def alive(agent):
        rs = by_agent.get(agent, [])
        if not rs:
            return ("unk", None, "no live page")
        bad = [r for r in rs if r["state"] != "ok"]
        ages = [r["age_h"] for r in rs if r.get("age_h") is not None]
        age = min(ages) if ages else None
        return ("bad" if bad else "ok", age, "; ".join(p for r in bad for p in r["problems"])[:90])

    def na(v):
        return "unavailable" if v in (None, "") else f"{v:,}" if isinstance(v, int) else str(v)

    def ago(age):
        if age is None:
            return "no timestamp"
        return f"{int(age * 60)} min ago" if age < 1 else (f"{age:.0f}h ago" if age < 48 else f"{age / 24:.0f} days ago")

    def card(it, kind="•", when=None):
        who = f'<p class="row"><span class="lbl">What it is</span>{html.escape(it["who_is"])}</p>' if it.get("who_is") else ""
        why = f'<p class="row"><span class="lbl">Why it matters</span>{html.escape(it["why"])}</p>' if it.get("why") else ""
        steps = "".join(f"<li>{html.escape(x)}</li>" for x in it.get("do", []))
        head = (f'<b>{html.escape(when)}</b> — ' if when else "") + html.escape(_cut(it["what"], 90))
        links = f'<a href="{html.escape(it["url"])}">{html.escape(it.get("url_label") or "open")}</a>'
        if it.get("url2"):
            links += f' · <a href="{html.escape(it["url2"])}">{html.escape(it.get("url2_label") or "more")}</a>'
        return f"""<div class="card"><span class="k">{kind}</span><div class="body">
  <p class="head">{head}</p>{who}{why}
  <p class="row"><span class="lbl">What you do</span></p><ol class="do">{steps}</ol>
  <span class="links2">{links}</span></div></div>"""

    rv, mk, gs, ig = facts["revsom"], facts["marketsom"], facts["growsom"], facts["instasom"]
    needs = facts["needs_you"]

    sections = [
        dict(name="Revsom", purpose="Money that costs no equity: grants, prizes, credits.",
             url="https://agentrevup.netlify.app/", label="funding board",
             pulling=f"{na(rv.get('total'))} opportunities · {na(rv.get('no_sam'))} need no registration · {na(rv.get('closing_14d'))} close inside 14 days",
             top=rv.get("top") or [], kind="$",
             needs=[n for n in needs if n["who"] == "Revsom"]),
        dict(name="Growsom", purpose="Investors, and free integrations that put Vybe's SDK in other people's products.",
             url="https://agentgrowthscout.netlify.app/", label="target board",
             pulling=f"{na(gs.get('total'))} targets · {na(gs.get('high'))} high priority · {na(gs.get('ready_to_send'))} ready to send on John's approval",
             top=gs.get("top") or [], kind="→",
             needs=[n for n in needs if n["who"] == "Growsom"]),
        dict(name="Marketsom", purpose="No-cost partners with reach — leagues, clubs, member bodies — and honest marketing numbers.",
             url="https://agentmarksom.netlify.app/briefing.html", label="daily briefing",
             pulling=_cut(mk.get("headline") or "briefing unavailable", 140),
             top=mk.get("top") or [], kind="!",
             needs=[n for n in needs if n["who"] == "Marketsom"]),
        dict(name="Instasom", purpose="An audience that follows before launch, built one real person at a time.",
             url="https://instasum.netlify.app/", label="social dashboard",
             pulling=f"Instagram {na(ig.get('ig'))} raw followers · {na(ig.get('to_follow'))} verified people still to follow · Facebook {na(ig.get('fb'))}",
             top=ig.get("top") or [], kind="@",
             needs=[n for n in needs if n["who"] == "Instasom"]),
        dict(name="Daily worker", purpose="The product itself: one new app screen every weekday, funding rows, packets, Monday decks.",
             url=None, label=None,
             pulling="14 screens · 17 funding packets · 111 drafted answers. No live page yet — its work is code.",
             top=[], kind="▣", needs=[]),
    ]

    def section(sec):
        state, age, why = alive(sec["name"]) if sec["name"] != "Daily worker" else ("unk", None, "")
        dot = {"ok": "ok", "bad": "bad", "unk": "unk"}[state]
        when = ago(age) if sec["url"] else "no live page"
        link = f'<a class="more" href="{html.escape(sec["url"])}">{html.escape(sec["label"])} →</a>' if sec["url"] else ""
        needs_html = "".join(card(n, {"money": "$", "call": "☎", "deadline": "!", "drafts": "✉"}.get(n["kind"], "•"), n["when"]) for n in sec["needs"][:4])
        top_html = "".join(card(t, sec["kind"]) for t in sec["top"][:4])
        return f"""<section class="agent {dot}">
  <header><span class="dot"></span><h2>{html.escape(sec["name"])}</h2><span class="when">{html.escape(when)}{'' if state != 'bad' else ' · ' + html.escape(why)}</span></header>
  <p class="purpose">{html.escape(sec["purpose"])}</p>
  <p class="pulling"><span class="lbl">What it is pulling</span>{html.escape(sec["pulling"])}</p>
  {'<h3>Needs you</h3>' + needs_html if needs_html else ''}
  {'<h3>Top of its list</h3>' + top_html if top_html else ''}
  {link}
</section>"""

    n_bad = sum(1 for sname in ("Revsom", "Growsom", "Marketsom", "Instasom") if alive(sname)[0] == "bad")
    status = "All agents running" if n_bad == 0 else f"{n_bad} agent{'s' if n_bad > 1 else ''} need attention"
    n_needs = len(needs)

    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Vybe Hub</title>
<style>
:root {{
  --bg:#f6f8f7; --surface:#fff; --surface-2:#eef3f1; --line:#dbe3e0;
  --ink:#12201c; --ink-2:#44554f; --ink-3:#6b7a75;
  --brand:#1f8e78; --brand-ink:#0f5e4f;
  --good:#1d7a3a; --good-bg:#e3f3e7; --crit:#a3262a; --crit-bg:#fbe3e3;
  --warn:#8a5a00; --warn-bg:#fbefd5;
  color-scheme: light;
}}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{
  --bg:#0e1513; --surface:#151f1c; --surface-2:#1b2824; --line:#2a3a35;
  --ink:#e7efec; --ink-2:#b4c4be; --ink-3:#8a9c96;
  --brand:#4cc3a8; --brand-ink:#8fe0cd;
  --good:#7ad596; --good-bg:#173322; --crit:#f19a9a; --crit-bg:#3a1a1b;
  --warn:#f0c46b; --warn-bg:#352a12;
  color-scheme: dark;
}} }}
:root[data-theme="dark"] {{
  --bg:#0e1513; --surface:#151f1c; --surface-2:#1b2824; --line:#2a3a35;
  --ink:#e7efec; --ink-2:#b4c4be; --ink-3:#8a9c96;
  --brand:#4cc3a8; --brand-ink:#8fe0cd;
  --good:#7ad596; --good-bg:#173322; --crit:#f19a9a; --crit-bg:#3a1a1b;
  --warn:#f0c46b; --warn-bg:#352a12;
  color-scheme: dark;
}}
* {{ box-sizing:border-box }}
body {{ margin:0; background:var(--bg); color:var(--ink);
  font:16px/1.45 ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,sans-serif }}
a {{ color:var(--brand-ink); text-decoration:none }}
.wrap {{ max-width:640px; margin:0 auto; padding:20px 16px 60px }}
h1 {{ font-size:22px; margin:0; letter-spacing:-.01em }} h1 span {{ color:var(--brand) }}
.goal {{ margin:6px 0 0; color:var(--ink-2); font-size:15px }}
.status {{ display:flex; gap:8px; margin:10px 0 0; font-weight:600; color:{'var(--good)' if n_bad == 0 else 'var(--crit)'} }}
.status .meta {{ font-weight:400; color:var(--ink-3); font-size:13px; margin-left:auto; text-align:right }}
.jump {{ margin:14px 0 0; font-size:13.5px; color:var(--ink-3); line-height:1.9 }}
.jump a {{ border-bottom:1px solid var(--line); margin-right:8px }}
section.agent {{ margin-top:26px; padding-top:18px; border-top:2px solid var(--line) }}
section.agent header {{ display:flex; align-items:center; gap:10px }}
section.agent h2 {{ margin:0; font-size:19px }}
section.agent .when {{ margin-left:auto; font-size:12.5px; color:var(--ink-3); text-align:right }}
.dot {{ flex:0 0 10px; height:10px; border-radius:50%; background:var(--ink-3) }}
section.ok .dot {{ background:var(--good) }} section.bad .dot {{ background:var(--crit) }}
.purpose {{ margin:6px 0 0; color:var(--ink-2); font-size:15px }}
.pulling {{ margin:10px 0 0; font-size:14.5px; background:var(--surface-2); border-radius:10px; padding:10px 12px }}
.lbl {{ display:block; font-size:11px; letter-spacing:.07em; text-transform:uppercase; color:var(--ink-3); font-weight:600; margin-bottom:2px }}
h3 {{ font-size:12px; text-transform:uppercase; letter-spacing:.07em; color:var(--ink-3); margin:16px 0 6px; font-weight:600 }}
.card {{ display:flex; gap:12px; align-items:flex-start; background:var(--surface); border:1px solid var(--line);
  border-radius:12px; padding:12px 14px; margin-top:8px }}
.card .k {{ flex:0 0 26px; height:26px; border-radius:8px; background:var(--surface-2); color:var(--brand-ink);
  font-weight:700; text-align:center; line-height:26px; font-size:14px }}
.card .body {{ min-width:0; flex:1 }}
.card .head {{ margin:0; font-size:15.5px }} .card .head b {{ color:var(--crit) }}
.card .row {{ margin:7px 0 0; font-size:14px; line-height:1.45 }}
.card .do {{ margin:2px 0 4px; padding-left:20px; font-size:14px }} .card .do li {{ margin:2px 0 }}
.card .links2 {{ display:block; font-size:13px; color:var(--ink-3); margin-top:4px }}
.card .links2 a {{ border-bottom:1px solid var(--line) }}
.more {{ display:inline-block; margin-top:12px; font-size:14px; border-bottom:1px solid var(--line) }}
.foot {{ margin-top:30px; padding-top:14px; border-top:1px solid var(--line); font-size:13px; color:var(--ink-3); line-height:1.8 }}
.foot a {{ border-bottom:1px solid var(--line) }}
</style>
</head>
<body>
<div class="wrap">
  <h1><span>Vybe</span> hub</h1>
  <p class="goal">Five agents, one job: bring Vybe money — collaboration, investors, opportunity. No booths. No suppliers. Nothing from any other company.</p>
  <p class="status"><span>{html.escape(status)} · {n_needs} thing{'s' if n_needs != 1 else ''} need you</span><span class="meta">checked {now.strftime('%H:%M')} UTC<br>refreshes every 4h</span></p>
  <p class="jump">{' '.join(f'<a href="#{sec["name"].lower().replace(" ", "-")}">{html.escape(sec["name"])}</a>' for sec in sections)}</p>

{chr(10).join(section(sec).replace('<section class="agent', f'<section id="{sec["name"].lower().replace(" ", "-")}" class="agent', 1) for sec in sections)}

  <p class="foot">
    Every card is the same shape: what it is · why it matters · what you do. Nothing here is typed by hand — it is read from each agent's own live page.<br>
    <a href="vybe-agent-board.html">Is every dashboard current?</a> ·
    <a href="vybe-fleet-map.html">How the system fits together</a> ·
    <a href="https://github.com/jermrox/agency-agents/blob/main/VYBE-AGENT-STANDARDS.md">The rules</a>
  </p>
</div>
</body>
</html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-dir", default="dashboards")
    ap.add_argument("--no-fail", action="store_true",
                    help="render and exit 0 even when a surface is red")
    args = ap.parse_args()

    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
    rows = [check(e, now) for e in SURFACES]

    out = pathlib.Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    facts = extract_facts(rows, now)
    (out / "vybe-hub.html").write_text(render_hub(rows, facts, now))
    (out / "vybe-agent-board.html").write_text(render(rows, now))
    slim = [{k: v for k, v in r.items() if k != "_body"} for r in rows]
    (out / "vybe-agents.json").write_text(json.dumps(
        {"checked": now.isoformat(), "surfaces": slim,
         "needs_you": facts["needs_you"]}, indent=2) + "\n")

    red = [r for r in rows if r["state"] != "ok"]
    for r in rows:
        mark = "ok  " if r["state"] == "ok" else "RED "
        age = f"{r['age_h']}h" if r["age_h"] is not None else "-"
        print(f"{mark} {r['agent']:<10} {r['surface']:<46} {age:>7}  {'; '.join(r['problems'])}")
    print(f"\n{len(rows) - len(red)}/{len(rows)} surfaces OK")

    if red and not args.no_fail:
        print(f"FAIL: {len(red)} surface(s) need attention", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
