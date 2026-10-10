#!/usr/bin/env python3
"""Build vybe-marketing/hub/reports.html: every Marksom report on one page.

Each report is a section you switch on from the list. Markdown files are
rendered at build time, and the partner outreach log comes from
vybe-marketing/research/outreach-log.json (no email addresses).

Usage: python3 vybe-marketing/hub/build_reports.py   (needs: pip install markdown)
"""
import html, json, re
from pathlib import Path

import markdown

ROOT = Path(__file__).resolve().parents[1]
HUB = ROOT / "hub"

GROUPS = [
    ("Outreach", [
        ("outreach", "Every partner email", None),
        ("forms", "Forms and DMs to send (5 Oct)", "research/forms-and-dms-2026-10-05.md"),
    ]),
    ("Partner research", [
        ("candidates", "Partner candidates (4 Oct)", "research/partner-candidates-2026-10-04.md"),
        ("life", "Life stages and situations (4 Oct)", "research/life-stages-2026-10-04.md"),
        ("portfolio", "Community portfolio", "community-portfolio.md"),
    ]),
    ("Strategy", [
        ("plan", "Marketing plan, Oct to Dec", "plan-2026-q4.md"),
        ("concept", "The Vybe Health concept", "concept.md"),
        ("brand", "Brand brief", "brand-brief.md"),
        ("seo", "Search plan", "seo-plan.md"),
        ("linkedin", "LinkedIn company page", "linkedin-company-page.md"),
    ]),
    ("Search page briefs", [
        ("b-hrv", "What is a good HRV?", "briefs/what-is-a-good-hrv.md"),
        ("b-screenless", "Screenless fitness trackers", "briefs/screenless-fitness-tracker.md"),
        ("b-oura", "Oura ring alternatives", "briefs/oura-ring-alternative.md"),
        ("b-whoop", "WHOOP vs Oura", "briefs/whoop-vs-oura.md"),
        ("b-over", "Overtraining symptoms", "briefs/overtraining-symptoms.md"),
        ("b-bed", "Eating before bed", "briefs/eating-before-bed-sleep.md"),
    ]),
    ("Scoreboards and checks", [
        ("sb-1005", "Scoreboard, week of 28 Sep", "scoreboard-2026-10-05.md"),
        ("sb-0930", "Scoreboard, baseline 30 Sep", "scoreboard-2026-09-30.md"),
        ("cc-1005", "Concept check (5 Oct)", "research/concept-check-2026-10-05.md"),
    ]),
]

EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def md(path):
    text = (ROOT / path).read_text()
    text = EMAIL.sub(lambda m: m.group(0) if m.group(0).endswith("vybe.health") else "[address removed]", text)
    out = markdown.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])
    # Keep each table row, list item and paragraph on one line, as in the source,
    # so the marketing guardrail reads a row's "avoid"/"never" with its claim.
    return re.sub(r"<(tr|li|p)>(.*?)</\1>", lambda m: m.group(0).replace("\n", " "), out, flags=re.S)


def outreach():
    rows = json.loads((ROOT / "research/outreach-log.json").read_text())
    sent = [r for r in rows if not r["kind"].startswith("Draft")]
    orgs = sorted({r["org"] for r in sent})
    out = [f'<h1>{len(sent)} partner emails sent to {len(orgs)} organisations</h1>',
           '<p class="lede">Every partner email from jeremy@vybe.health that Marksom wrote, newest first. '
           'Open one to read it. Addresses are left out on purpose. Drafts still waiting in Gmail are marked.</p>',
           '<div class="chips" role="group" aria-label="Filter">'
           '<button type="button" data-k="all" aria-pressed="true">All</button>'
           '<button type="button" data-k="First email" aria-pressed="false">First emails</button>'
           '<button type="button" data-k="Reply" aria-pressed="false">Replies and follow-ups</button>'
           '<button type="button" data-k="Draft" aria-pressed="false">Drafts</button></div>']
    order = ["10 Oct", "9 Oct", "8 Oct", "6 Oct"]
    for d in order:
        day = [r for r in rows if r["date"] == d]
        if not day:
            continue
        out.append(f'<h2 class="day">{d}</h2>')
        for r in day:
            k = "Draft" if r["kind"].startswith("Draft") else ("First email" if r["kind"] == "First email" else "Reply")
            body = "".join(
                "<ul>" + "".join(f"<li>{html.escape(li[2:])}</li>" for li in p.split("\n") if li.startswith("- ")) + "</ul>"
                if p.lstrip().startswith("- ") else f"<p>{html.escape(p)}</p>"
                for p in r["body"].split("\n\n"))
            subj = html.escape(r["subject"] or "Reply in their thread")
            out.append(f'<details class="mail" data-k="{k}"><summary><b>{html.escape(r["org"])}</b>'
                       f'<span class="tag {k.split()[0].lower()}">{html.escape(r["kind"])}</span>'
                       f'<span class="subj">{subj}</span></summary><div class="mbody">{body}</div></details>')
    return "\n".join(out)


def build():
    nav, panels = [], []
    for g, items in GROUPS:
        nav.append(f'<p class="label">{html.escape(g)}</p>')
        for rid, title, path in items:
            nav.append(f'<button type="button" class="ri" data-r="{rid}" aria-pressed="false">{html.escape(title)}</button>')
            body = outreach() if path is None else md(path)
            panels.append(f'<article class="doc" id="r-{rid}" hidden>{body}</article>')
    nav.append('<p class="label">Other pages</p><a class="ri" href="partner-board.html">Partner board: 41 sports scored</a>')
    tokens = re.search(r"(:root\{.*?\.logo\.small\{[^}]*\})", (HUB / "briefing.html").read_text(), re.S).group(1)
    page = TEMPLATE.replace("/*TOKENS*/", tokens).replace("<!--NAV-->", "\n".join(nav)).replace("<!--PANELS-->", "\n".join(panels))
    (HUB / "reports.html").write_text(page)
    print(f"wrote {HUB / 'reports.html'} ({len(page)} bytes)")


TEMPLATE = """<!doctype html>
<html lang="en">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Marksom Reports</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Instrument+Serif&family=Work+Sans:wght@400;500;600&family=Jost:wght@500;700&family=IBM+Plex+Mono:wght@400;500&display=swap">
<style>
/*TOKENS*/
.reports{display:flex;gap:8px;flex-wrap:wrap;padding:10px 0 2px}.reports a{border:1px solid var(--line);border-radius:999px;padding:5px 12px;font-size:13px;color:var(--ink);text-decoration:none}.reports a[aria-current="page"]{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.toggle{margin-left:auto;border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:5px 12px;font-size:13px}
.layout{display:grid;grid-template-columns:280px minmax(0,1fr);gap:28px;padding-block:28px 64px}
.side{position:sticky;top:120px;align-self:start;max-height:calc(100vh - 140px);overflow:auto;display:flex;flex-direction:column;gap:4px}
.side .label{margin:14px 0 4px}
.ri{display:block;text-align:left;border:1px solid transparent;background:transparent;border-radius:10px;padding:7px 10px;font-size:15px;color:var(--ink);text-decoration:none;line-height:1.35}
.ri:hover{background:var(--tint)}
.ri[aria-pressed="true"]{background:var(--forest);color:var(--on-forest)}
.doc{background:var(--surface);border:1px solid var(--line);border-radius:4px;padding:28px clamp(18px,4vw,44px);min-width:0;overflow-wrap:anywhere}
.doc h1{font-size:clamp(32px,4.5vw,48px);margin-bottom:14px}
.doc h2{font-size:clamp(24px,3vw,32px);margin:30px 0 10px}
.doc h3{font-size:22px;margin:22px 0 8px}
.doc p,.doc ul,.doc ol{margin:0 0 12px}
.doc table{border-collapse:collapse;width:100%;font-size:14px;margin:0 0 16px;display:block;overflow-x:auto}
.doc th,.doc td{border:1px solid var(--line);padding:6px 8px;text-align:left;vertical-align:top}
.doc th{background:var(--tint)}
.doc code,.doc pre{font-family:var(--mono);font-size:13px}
.doc pre{background:var(--tint);padding:12px;overflow-x:auto;white-space:pre-wrap}
.doc blockquote{border-left:3px solid var(--mint);margin:0 0 12px;padding-left:14px;color:var(--muted)}
.lede{color:var(--muted)}
.chips{display:flex;gap:8px;flex-wrap:wrap;margin:16px 0}
.chips button{border:1px solid var(--line);background:var(--surface);border-radius:999px;padding:5px 12px;font-size:13px}
.chips button[aria-pressed="true"]{background:var(--ink);color:var(--surface);border-color:var(--ink)}
.day{font-size:24px!important;margin:24px 0 8px!important}
.mail{border:1px solid var(--line);border-radius:8px;margin:0 0 8px;background:var(--ground)}
.mail summary{cursor:pointer;padding:10px 14px;display:flex;flex-wrap:wrap;gap:6px 10px;align-items:baseline}
.mail .subj{flex-basis:100%;color:var(--muted);font-size:14px}
.mail .mbody{padding:4px 16px 12px;font-size:15px;border-top:1px solid var(--line)}
.mail .mbody p{margin:10px 0}
.tag{font-size:11px;letter-spacing:.08em;text-transform:uppercase;border-radius:999px;padding:2px 8px;background:var(--intel-bg);color:var(--intel)}
.tag.draft{background:var(--warn-bg);color:var(--warn)}
.tag.reply,.tag.follow-up{background:var(--tint);color:var(--ink)}
@media (max-width:820px){.layout{grid-template-columns:1fr}.side{position:static;max-height:none;flex-direction:row;flex-wrap:wrap}.side .label{flex-basis:100%;margin:8px 0 0}.ri{border-color:var(--line);font-size:14px;padding:5px 10px;border-radius:999px}}
</style>
<body>
<header class="top">
  <div class="wrap">
    <nav class="reports" aria-label="Reports"><a href="briefing.html">Daily briefing</a><a href="reports.html" aria-current="page">All reports</a><a href="./">Agent hub</a><a href="scoreboard.html">Weekly scoreboard</a><button class="toggle" id="theme" type="button" aria-label="Switch colour theme">Theme</button></nav>
    <div class="bar"><div class="brand"><div><b>All reports</b><div class="sub">Marksom · every report, email and research file in one place</div></div></div></div>
  </div>
</header>
<main class="wrap layout">
  <aside class="side" aria-label="Choose a report">
<!--NAV-->
  </aside>
  <div>
<!--PANELS-->
  </div>
</main>
<script>
(function () {
  var root = document.documentElement;
  try { var saved = localStorage.getItem("vybe-mkt-theme"); if (saved) root.setAttribute("data-theme", saved); } catch (e) {}
  document.getElementById("theme").addEventListener("click", function () {
    var dark = root.getAttribute("data-theme") ? root.getAttribute("data-theme") === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("vybe-mkt-theme", next); } catch (e) {}
  });
  var btns = document.querySelectorAll("button.ri");
  function show(id, push) {
    if (!document.getElementById("r-" + id)) id = "outreach";
    document.querySelectorAll(".doc").forEach(function (d) { d.hidden = d.id !== "r-" + id; });
    btns.forEach(function (b) { b.setAttribute("aria-pressed", b.dataset.r === id ? "true" : "false"); });
    if (push) { history.replaceState(null, "", "#" + id); window.scrollTo(0, 0); }
  }
  btns.forEach(function (b) { b.addEventListener("click", function () { show(b.dataset.r, true); }); });
  window.addEventListener("hashchange", function () { show(location.hash.slice(1), false); });
  show(location.hash.slice(1), false);
  var chips = document.querySelectorAll(".chips button");
  chips.forEach(function (c) { c.addEventListener("click", function () {
    chips.forEach(function (x) { x.setAttribute("aria-pressed", x === c ? "true" : "false"); });
    document.querySelectorAll(".mail").forEach(function (m) { m.hidden = !(c.dataset.k === "all" || m.dataset.k === c.dataset.k); });
    document.querySelectorAll("h2.day").forEach(function (h) { var n = h.nextElementSibling, any = false;
      while (n && n.classList.contains("mail")) { if (!n.hidden) any = true; n = n.nextElementSibling; } h.hidden = !any; });
  }); });
})();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    build()
