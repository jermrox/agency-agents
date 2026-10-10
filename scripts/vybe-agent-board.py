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

Scope is Vybe Health only. The founder's other ventures run their own agents
(Leadsom for i-Grow, Researchsom and Crawlsom for MOPs and MOEs, Babysom) and
they are deliberately not tracked here.

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
    <strong>Scope.</strong> Vybe Health only. Leadsom (i-Grow), Researchsom and Crawlsom (MOPs and
    MOEs) and Babysom belong to other ventures and are not tracked here.
    Rules: <a href="https://github.com/jermrox/agency-agents/blob/main/VYBE-AGENT-STANDARDS.md">VYBE-AGENT-STANDARDS.md</a>.
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
    (out / "vybe-agent-board.html").write_text(render(rows, now))
    (out / "vybe-agents.json").write_text(json.dumps(
        {"checked": now.isoformat(), "surfaces": rows}, indent=2) + "\n")

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
