"""Render the daily dashboard: one self-contained HTML page plus data.json.

Everything the page shows is embedded as JSON, so the file works from disk,
from Netlify, or as an email attachment -- no server, no external requests.
The archive of daily reports is embedded too, and the report picker at the
top re-scopes every section below it to that day.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from .models import utcnow
from . import guide
from .report import ReportArchive


def load_picks(path: str | Path | None) -> dict[str, Any] | None:
    """The curated, sourced car seat and stroller safety picks, if the file exists."""
    if not path or not Path(path).exists():
        return None
    return json.loads(Path(path).read_text(encoding="utf-8"))


def payload(results: list[dict[str, Any]], plan: dict[str, Any] | None, archive: ReportArchive,
            picks: dict[str, Any] | None = None) -> dict[str, Any]:
    dates = archive.dates()
    return {
        "generated_at": utcnow(),
        "latest": dates[-1] if dates else None,
        "reports": {d: archive.load(d) for d in dates[-120:]},
        "details": {r["key"]: r for r in results},
        "plan": plan,
        "picks": picks,
    }


def write(results: list[dict[str, Any]], plan: dict[str, Any] | None, archive: ReportArchive,
          site_dir: str | Path, picks_path: str | Path | None = None,
          top10_dir: str | Path | None = None) -> Path:
    site = Path(site_dir)
    site.mkdir(parents=True, exist_ok=True)
    data = payload(results, plan, archive, load_picks(picks_path))
    (site / "data.json").write_text(json.dumps(data, indent=1) + "\n", encoding="utf-8")
    reports_out = site / "reports"
    reports_out.mkdir(exist_ok=True)
    for date in archive.dates():
        shutil.copyfile(archive.dir / f"{date}.json", reports_out / f"{date}.json")
    embedded = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
    index = site / "index.html"
    index.write_text(TEMPLATE.replace("__DATA__", embedded), encoding="utf-8")
    guide.write(site, data["picks"], guide.load_top10(top10_dir), data["generated_at"])
    return index


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Baby Gear Dashboard</title>
<meta name="description" content="Daily prices, deals, recalls, spending and buy plan for baby gear.">
<style>
:root{
  color-scheme:light;
  --page:#f9f9f7;--surface:#fcfcfb;--raised:#ffffff;
  --ink:#0b0b0b;--ink-2:#52514e;--muted:#6f6d68;
  --grid:#e1e0d9;--axis:#c3c2b7;--border:rgba(11,11,11,.10);
  --series-1:#2a78d6;--track:#cde2fb;
  --good:#0ca30c;--good-text:#006300;--warning:#fab219;--serious:#ec835a;--critical:#d03b3b;
  --accent:#c2185b;
}
@media (prefers-color-scheme:dark){
  :root:where(:not([data-theme="light"])){
    color-scheme:dark;
    --page:#0d0d0d;--surface:#1a1a19;--raised:#1f1f1e;
    --ink:#ffffff;--ink-2:#c3c2b7;--muted:#9a988f;
    --grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
    --series-1:#3987e5;--track:#184f95;
    --good-text:#0ca30c;--accent:#f472b6;
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --page:#0d0d0d;--surface:#1a1a19;--raised:#1f1f1e;
  --ink:#ffffff;--ink-2:#c3c2b7;--muted:#9a988f;
  --grid:#2c2c2a;--axis:#383835;--border:rgba(255,255,255,.10);
  --series-1:#3987e5;--track:#184f95;
  --good-text:#0ca30c;--accent:#f472b6;
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--page);color:var(--ink)}
body{font:15px/1.5 system-ui,-apple-system,"Segoe UI",sans-serif;padding:20px 16px 48px}
main{max-width:1120px;margin:0 auto}
h1{font-size:26px;margin:0}h2{font-size:18px;margin:0 0 10px}h3{font-size:15px;margin:0}
p{margin:0}
.muted{color:var(--muted);font-size:13px}.ink2{color:var(--ink-2)}
.top{display:flex;flex-wrap:wrap;gap:12px 24px;align-items:end;justify-content:space-between;margin-bottom:16px}
.controls{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
select,button{font:inherit;color:var(--ink);background:var(--raised);border:1px solid var(--border);border-radius:8px;padding:6px 10px}
button{cursor:pointer}
section{margin-top:28px}
.kpis{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(170px,1fr))}
.tile{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px}
.tile .label{font-size:13px;color:var(--ink-2)}
.tile .value{font-size:28px;font-weight:650;line-height:1.2;margin-top:4px}
.tile .sub{font-size:12px;color:var(--muted);margin-top:2px}
.hero .value{font-size:48px}
.meter{height:8px;border-radius:4px;background:var(--track);overflow:hidden;margin-top:8px}
.meter>span{display:block;height:100%;background:var(--series-1);border-radius:4px}
.meter.over>span{background:var(--critical)}
.events{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.event{display:flex;gap:10px;align-items:flex-start;background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 12px}
.badge{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:600;white-space:nowrap;border-radius:99px;padding:2px 8px;border:1px solid var(--border);color:var(--ink)}
.dot{width:8px;height:8px;border-radius:50%;flex:none}
.s-critical .dot{background:var(--critical)}.s-good .dot{background:var(--good)}.s-warning .dot{background:var(--warning)}.s-info .dot{background:var(--axis)}.s-serious .dot{background:var(--serious)}
.grid{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(310px,1fr))}
.card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:14px;display:flex;flex-direction:column;gap:8px;min-width:0}
.card header{display:flex;flex-wrap:wrap;gap:6px 8px;justify-content:space-between;align-items:flex-start}
.card h3{flex:1 1 160px}
.price{font-size:22px;font-weight:650}
.facts{display:flex;flex-wrap:wrap;gap:4px 14px;font-size:13px;color:var(--ink-2)}
.spark{position:relative}
.spark svg{display:block;width:100%;height:64px;overflow:visible;outline:none}
.spark svg:focus-visible{outline:2px solid var(--series-1);outline-offset:4px;border-radius:4px}
.tip{position:absolute;pointer-events:none;background:var(--raised);border:1px solid var(--border);border-radius:8px;padding:4px 8px;font-size:12px;white-space:nowrap;box-shadow:0 2px 8px rgba(0,0,0,.12);transform:translate(-50%,-100%);top:-4px;display:none}
.tip strong{font-size:13px}
.tip .key{display:inline-block;width:10px;height:2px;background:var(--series-1);vertical-align:middle;margin-right:5px}
details summary{cursor:pointer;font-size:13px;color:var(--ink-2)}
.gates{list-style:none;padding:0;margin:6px 0 0;font-size:13px;display:grid;gap:4px}
.gates b{font-size:11px;letter-spacing:.02em;margin-right:4px}
.g-pass b{color:var(--good-text)}.g-fail b{color:var(--critical)}.g-check b{color:var(--ink-2)}.g-na b{color:var(--muted)}
.scroll{overflow-x:auto;background:var(--surface);border:1px solid var(--border);border-radius:12px}
table{border-collapse:collapse;width:100%;min-width:640px;font-size:14px}
th,td{text-align:left;padding:8px 12px;border-bottom:1px solid var(--grid);vertical-align:top}
th{font-size:12px;color:var(--ink-2);font-weight:600}
tr:last-child td{border-bottom:0}
td.num,th.num{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}
.nw{white-space:nowrap}
tbody tr.pick{cursor:pointer}tbody tr.pick:hover{background:var(--page)}
tr.sel td{background:var(--page);font-weight:600}
.empty{background:var(--surface);border:1px dashed var(--axis);border-radius:12px;padding:16px;color:var(--ink-2)}
.foot{margin-top:36px;font-size:12px;color:var(--muted)}
.chips{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px}
.chips button{font-size:13px;padding:4px 10px;border-radius:99px}
.chips button[aria-pressed="true"]{background:var(--ink);color:var(--page);border-color:var(--ink)}
.recalls{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.recall{background:var(--surface);border:1px solid var(--border);border-radius:10px;padding:10px 12px;display:grid;gap:4px}
.recall .meta{display:flex;flex-wrap:wrap;gap:4px 12px;font-size:12px;color:var(--muted)}
.recall a{font-weight:600}
.picks{display:grid;gap:12px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr))}
.pick-card .rank{font-size:12px;font-weight:700;color:var(--accent)}
.flags{display:flex;flex-wrap:wrap;gap:4px}
.flag{font-size:12px;border-radius:6px;padding:1px 6px;background:var(--page);border:1px solid var(--border);color:var(--ink-2)}
.flag.hot{border-color:var(--critical);color:var(--critical)}
.srcs{font-size:12px;display:flex;flex-wrap:wrap;gap:4px 10px}
.dates{list-style:none;margin:0 0 12px;padding:0;display:grid;gap:4px;font-size:13px}
.search{width:100%;max-width:420px;margin:0 0 10px;font:inherit;color:var(--ink);background:var(--raised);border:1px solid var(--border);border-radius:8px;padding:6px 10px}
.dates .past{color:var(--muted);text-decoration:line-through}
a{color:var(--series-1)}
.guide-link{display:inline-block;background:var(--accent);color:#fff;text-decoration:none;font-weight:650;border-radius:10px;padding:8px 14px}
</style>
</head>
<body>
<main>
  <div class="top">
    <div>
      <h1>🍼 Baby Gear Dashboard</h1>
      <p class="muted" id="updated"></p>
    </div>
    <div class="controls">
      <label for="day" class="muted">Report</label>
      <select id="day"></select>
      <a class="guide-link" href="guide.html" style="padding:6px 12px">🛡️ Safety Guide</a>
      <button id="theme" type="button" aria-label="Toggle light or dark theme">◐</button>
    </div>
  </div>

  <div class="kpis" id="kpis"></div>

  <section aria-labelledby="h-changes"><h2 id="h-changes">What changed</h2><ul class="events" id="events"></ul></section>
  <section aria-labelledby="h-recalls"><h2 id="h-recalls">Baby &amp; kid recalls</h2><p class="muted" id="recalls-note" style="margin-bottom:8px"></p><div class="chips" id="recall-filters" role="group" aria-label="Filter recalls by type"></div><div id="recalls"></div></section>
  <section aria-labelledby="h-picks"><h2 id="h-picks">Car seat &amp; stroller safety picks</h2><p style="margin:0 0 10px"><a class="guide-link" href="guide.html">Open the full Safety Guide: top 10 per category with photos, prices, filters and side-by-side compare →</a></p><p class="muted" id="picks-note" style="margin-bottom:8px"></p><ul class="dates" id="picks-dates"></ul><div class="chips" id="picks-tabs" role="group" aria-label="Choose a category"></div><div id="picks"></div></section>
  <section aria-labelledby="h-watch"><h2 id="h-watch">Watchlist</h2><div class="grid" id="items"></div></section>
  <section aria-labelledby="h-plan"><h2 id="h-plan">Buy plan</h2><div id="plan"></div></section>
  <section aria-labelledby="h-spend"><h2 id="h-spend">Spending</h2><div id="spend"></div></section>
  <section aria-labelledby="h-arch"><h2 id="h-arch">Report archive</h2><p class="muted" style="margin-bottom:8px">Select a day to see that report.</p><div id="archive"></div></section>

  <p class="foot">Prices are judged against their own history, not list price. Items that fail a safety gate never show as deals. Sale windows are past-year patterns, so confirm the dates. Not medical advice.</p>
</main>
<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
"use strict";
var D = JSON.parse(document.getElementById("data").textContent);
var dates = Object.keys(D.reports).sort();
var $ = function(id){ return document.getElementById(id); };

function el(tag, attrs, kids){
  var n = document.createElement(tag);
  if (attrs) for (var k in attrs){
    if (k === "text") n.textContent = attrs[k];
    else if (k === "cls") n.className = attrs[k];
    else n.setAttribute(k, attrs[k]);
  }
  (kids || []).forEach(function(c){ if (c != null) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
  return n;
}
function money(v, perUnit){
  if (v == null) return "—";
  if (perUnit && v < 1) return "$" + v.toFixed(3);
  return "$" + v.toLocaleString(undefined, {minimumFractionDigits:2, maximumFractionDigits:2});
}
function whole(v){ return v == null ? "—" : "$" + Math.round(v).toLocaleString(); }
function fmtDate(iso){ var d = new Date(iso + "T12:00:00Z"); return d.toLocaleDateString(undefined, {month:"short", day:"numeric", year:"numeric", timeZone:"UTC"}); }

var VERDICT = {
  buy_now:["good","Buy now"], good:["good","Good price"], fair:["warning","Fair — probably wait"],
  wait:["warning","Wait — likely to drop"], tracking:["info","Tracking — not enough history"], skip:["critical","Skip — fails safety"],
  bought:["good","Bought"]
};
var SEV_LABEL = {critical:"Alert", good:"Good news", warning:"Heads up", info:"Info"};

function badge(sev, label){
  return el("span", {cls:"badge s-" + sev}, [el("span", {cls:"dot", "aria-hidden":"true"}), label]);
}

/* ---------- theme toggle ---------- */
(function(){
  var root = document.documentElement, saved = null;
  try { saved = localStorage.getItem("bgd-theme"); } catch(e) {}
  if (saved) root.setAttribute("data-theme", saved);
  $("theme").addEventListener("click", function(){
    var dark = root.getAttribute("data-theme") ? root.getAttribute("data-theme") === "dark"
      : window.matchMedia("(prefers-color-scheme: dark)").matches;
    var next = dark ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try { localStorage.setItem("bgd-theme", next); } catch(e) {}
  });
})();

/* ---------- sparkline with crosshair tooltip ---------- */
function sparkline(points, perUnit, name){
  var wrap = el("div", {cls:"spark"});
  if (!points || points.length < 2){
    wrap.appendChild(el("p", {cls:"muted", text: points && points.length ? "One price so far — the trend line starts with the second." : "No price history yet."}));
    return wrap;
  }
  var W = 300, H = 64, P = 4, NS = "http://www.w3.org/2000/svg";
  var t0 = Date.parse(points[0][0]), t1 = Date.parse(points[points.length-1][0]);
  var vals = points.map(function(p){ return p[1]; });
  var lo = Math.min.apply(null, vals), hi = Math.max.apply(null, vals);
  if (hi === lo){ hi += 1; lo -= 1; }
  var X = function(t){ return P + (t1 === t0 ? 0.5 : (t - t0) / (t1 - t0)) * (W - 2*P); };
  var Y = function(v){ return P + (1 - (v - lo) / (hi - lo)) * (H - 2*P); };
  var xy = points.map(function(p){ return [X(Date.parse(p[0])), Y(p[1])]; });
  var svg = document.createElementNS(NS, "svg");
  svg.setAttribute("viewBox", "0 0 " + W + " " + H);
  svg.setAttribute("preserveAspectRatio", "none");
  svg.setAttribute("tabindex", "0");
  svg.setAttribute("role", "img");
  svg.setAttribute("aria-label", name + " price history: " + points.length + " days, low " + money(lo, perUnit) + ", high " + money(hi, perUnit) + ". Use arrow keys to read values.");
  function mk(tag, attrs){ var n = document.createElementNS(NS, tag); for (var k in attrs) n.setAttribute(k, attrs[k]); return n; }
  svg.appendChild(mk("line", {x1:P, x2:W-P, y1:H-P, y2:H-P, stroke:"var(--axis)", "stroke-width":1, "vector-effect":"non-scaling-stroke"}));
  svg.appendChild(mk("path", {d:"M" + xy.map(function(p){ return p[0].toFixed(1) + "," + p[1].toFixed(1); }).join("L"),
    fill:"none", stroke:"var(--series-1)", "stroke-width":2, "stroke-linejoin":"round", "stroke-linecap":"round", "vector-effect":"non-scaling-stroke"}));
  var last = xy[xy.length-1];
  svg.appendChild(mk("circle", {cx:last[0], cy:last[1], r:3, fill:"var(--series-1)", stroke:"var(--surface)", "stroke-width":2, "vector-effect":"non-scaling-stroke"}));
  var cross = mk("line", {y1:0, y2:H, stroke:"var(--ink-2)", "stroke-width":1, "vector-effect":"non-scaling-stroke", visibility:"hidden"});
  svg.appendChild(cross);
  var tip = el("div", {cls:"tip", role:"status"});
  wrap.appendChild(svg); wrap.appendChild(tip);
  var idx = points.length - 1;
  function show(i){
    idx = Math.max(0, Math.min(points.length - 1, i));
    var p = xy[idx];
    cross.setAttribute("x1", p[0]); cross.setAttribute("x2", p[0]); cross.setAttribute("visibility", "visible");
    tip.textContent = "";
    tip.appendChild(el("strong", {text: money(points[idx][1], perUnit)}));
    tip.appendChild(el("div", {}, [el("span", {cls:"key"}), fmtDate(points[idx][0])]));
    var box = svg.getBoundingClientRect();
    tip.style.left = (p[0] / W * box.width) + "px";
    tip.style.display = "block";
  }
  function hide(){ cross.setAttribute("visibility", "hidden"); tip.style.display = "none"; }
  svg.addEventListener("pointermove", function(ev){
    var box = svg.getBoundingClientRect(), x = (ev.clientX - box.left) / box.width * W, best = 0, bd = 1e9;
    xy.forEach(function(p, i){ var d = Math.abs(p[0] - x); if (d < bd){ bd = d; best = i; } });
    show(best);
  });
  svg.addEventListener("pointerleave", hide);
  svg.addEventListener("focus", function(){ show(idx); });
  svg.addEventListener("blur", hide);
  svg.addEventListener("keydown", function(ev){
    if (ev.key === "ArrowLeft"){ show(idx - 1); ev.preventDefault(); }
    if (ev.key === "ArrowRight"){ show(idx + 1); ev.preventDefault(); }
  });
  return wrap;
}

/* ---------- sections ---------- */
function tile(label, value, sub, extra, hero){
  var t = el("div", {cls:"tile" + (hero ? " hero" : "")}, [el("div", {cls:"label", text:label}), el("div", {cls:"value", text:value})]);
  if (sub) t.appendChild(el("div", {cls:"sub", text:sub}));
  if (extra) t.appendChild(extra);
  return t;
}

function renderKpis(r){
  var box = $("kpis"); box.textContent = "";
  var s = r.spending, t = r.totals;
  if (r.days_to_due != null){
    var dd = r.days_to_due;
    box.appendChild(tile(dd >= 0 ? "Days until due date" : "Days since due date", String(Math.abs(dd)), "Due " + fmtDate(r.due_date), null, true));
  }
  var meter = null;
  if (s.budget){
    var pct = Math.min(100, s.spent / s.budget * 100);
    meter = el("div", {cls:"meter" + (s.projected_high > s.budget ? " over" : ""), role:"meter", "aria-valuemin":"0", "aria-valuemax":String(s.budget), "aria-valuenow":String(s.spent), "aria-label":"Spent of budget"}, [el("span")]);
    meter.firstChild.style.width = pct.toFixed(1) + "%";
  }
  box.appendChild(tile("Spent so far", whole(s.spent),
    s.budget ? "of " + whole(s.budget) + " budget · " + whole(s.remaining_budget) + " left" : "No budget set", meter));
  box.appendChild(tile("Saved vs typical price", whole(s.saved_vs_typical), "compared with each item's 90-day median"));
  box.appendChild(tile("Buy-now deals", String(t.buy_now), t.at_target + " at or below your target"));
  var alerts = tile("Safety alerts", String(t.safety_fail), t.safety_fail ? "Items that fail a safety gate" : "No items failing a safety gate");
  if (t.safety_fail) alerts.querySelector(".label").prepend(badge("critical", "Alert"), " ");
  box.appendChild(alerts);
  if (r.recall_watch && r.recall_watch.available){
    var fresh = r.events.filter(function(e){ return e.type === "recall_watch" && e.key !== "more"; }).length
      + r.events.filter(function(e){ return e.key === "more"; }).reduce(function(n, e){ return n + (parseInt(e.detail, 10) || 0); }, 0);
    box.appendChild(tile("Baby & kid recalls", String(r.recall_watch.items.length),
      "last " + r.recall_watch.days + " days" + (fresh ? " · " + fresh + " new since the last report" : "")));
  }
  box.appendChild(tile("Still to buy (estimate)", whole(s.still_to_buy_low) + "–" + whole(s.still_to_buy_high),
    s.budget ? "projected total up to " + whole(s.projected_high) : ""));
}

var recallGroup = "All";
function renderRecalls(r){
  var box = $("recalls"), chips = $("recall-filters"), note = $("recalls-note");
  box.textContent = ""; chips.textContent = "";
  var rw = r.recall_watch;
  if (!rw){ note.textContent = "This report is from before the recall watch was added."; return; }
  if (!rw.available){ note.textContent = "The CPSC recall database couldn't be reached for this report."; return; }
  var items = rw.items || [];
  note.textContent = items.length + " U.S. CPSC recalls of baby, toddler and kid products, and childproofing hazards, in the " + rw.days + " days before this report. Check anything you own, were given or bought second-hand.";
  if (!items.length) return;
  var counts = {};
  items.forEach(function(x){ counts[x.group] = (counts[x.group] || 0) + 1; });
  var groups = ["All"].concat(Object.keys(counts).sort(function(a, b){ return counts[b] - counts[a]; }));
  if (groups.indexOf(recallGroup) < 0) recallGroup = "All";
  groups.forEach(function(g){
    var b = el("button", {type:"button", "aria-pressed": String(g === recallGroup), text: g + " (" + (g === "All" ? items.length : counts[g]) + ")"});
    b.addEventListener("click", function(){ recallGroup = g; renderRecalls(r); });
    chips.appendChild(b);
  });
  var ul = el("ul", {cls:"recalls"});
  items.filter(function(x){ return recallGroup === "All" || x.group === recallGroup; }).forEach(function(x){
    var title = x.url && /^https:\/\/(www\.)?(cpsc|saferproducts)\.gov\//.test(x.url)
      ? el("a", {href:x.url, target:"_blank", rel:"noopener noreferrer", text:x.title})
      : el("strong", {text:x.title});
    var meta = el("div", {cls:"meta"}, [el("span", {text:fmtDate(x.date)}), el("span", {text:x.group})]);
    if (x.units) meta.appendChild(el("span", {text:"Units: " + x.units}));
    if (x.sold_at) meta.appendChild(el("span", {text:"Sold at: " + x.sold_at}));
    var li = el("li", {cls:"recall"}, [title, meta]);
    if (x.hazard) li.appendChild(el("div", {cls:"ink2", text:"Hazard: " + x.hazard}));
    if (x.remedy) li.appendChild(el("div", {cls:"ink2", text:"Remedy: " + x.remedy}));
    ul.appendChild(li);
  });
  box.appendChild(ul);
}

var pickCat = 0, recallType = "All", recallQuery = "";
function renderPicks(r){
  var P = D.picks, box = $("picks"), tabs = $("picks-tabs"), note = $("picks-note"), dl = $("picks-dates");
  box.textContent = ""; tabs.textContent = ""; dl.textContent = "";
  if (!P){ note.textContent = "No safety picks file yet (data/gear_picks.json)."; return; }
  note.textContent = P.summary + " Last reviewed " + fmtDate(P.reviewed) + ". " + (P.verified ? P.verified + " " : "") + P.caveats.join(" ");
  (P.dates || []).forEach(function(x){
    dl.appendChild(el("li", {cls: x.date < r.date ? "past" : ""}, [el("strong", {text: fmtDate(x.date) + ": "}),
      el("a", {href:x.url, target:"_blank", rel:"noopener noreferrer", text:x.label})]));
  });
  var link = function(t, u){ return el("a", {href:u, target:"_blank", rel:"noopener noreferrer", text:t}); };
  var db = (P.recall_db && P.recall_db.items) || [];
  var watchText = ((r.recall_watch && r.recall_watch.items) || []).map(function(x){ return ((x.title || "") + " " + (x.products || []).join(" ")).toLowerCase(); });
  var views = P.categories.map(function(c){ return {name:c.name, kind:"picks", cat:c}; });
  if (P.brands) views.push({name:"Brands A–Z", kind:"brands"});
  if (P.tech) views.push({name:"Safety tech: what's proven", kind:"tech"});
  if (db.length) views.push({name:"All recalls 2016–2026 (" + db.length + ")", kind:"recalls"});
  views.push({name:"Avoid / recalled", kind:"avoid"});
  if (P.trust) views.push({name:"How much to trust the sources", kind:"trust"});
  if (pickCat >= views.length) pickCat = 0;
  views.forEach(function(v, i){
    var b = el("button", {type:"button", "aria-pressed": String(i === pickCat), text:v.name});
    b.addEventListener("click", function(){ pickCat = i; renderPicks(r); });
    tabs.appendChild(b);
  });
  var v = views[pickCat];
  var list = function(items, tagOf){
    var ul = el("ul", {cls:"recalls"});
    items.forEach(function(x){
      var head = el("div", {}, [link(x.name, x.url)]);
      var tag = tagOf && tagOf(x);
      if (tag){ head.appendChild(document.createTextNode(" ")); head.appendChild(el("span", {cls:"flag" + (/caution|none|weak/i.test(tag) ? " hot" : ""), text:tag})); }
      ul.appendChild(el("li", {cls:"recall"}, [head, el("div", {cls:"ink2", text:x.detail})]));
    });
    box.appendChild(ul);
  };
  if (v.kind === "trust") return list(P.trust, function(x){ return x.weight; });
  if (v.kind === "avoid") return list(P.avoid);
  if (v.kind === "brands") return list(P.brands, function(x){ return x.verdict; });
  if (v.kind === "tech") return list(P.tech, function(x){ return "Evidence: " + x.grade; });
  if (v.kind === "recalls"){
    box.appendChild(el("p", {cls:"muted", style:"margin-bottom:8px", text:P.recall_db.note}));
    var types = ["All"], counts = {};
    db.forEach(function(x){ counts[x.type] = (counts[x.type] || 0) + 1; if (types.indexOf(x.type) < 0) types.push(x.type); });
    var bar = el("div", {cls:"chips"});
    types.forEach(function(t){
      var b = el("button", {type:"button", "aria-pressed": String(t === recallType), text: t + " (" + (t === "All" ? db.length : counts[t]) + ")"});
      b.addEventListener("click", function(){ recallType = t; renderPicks(r); });
      bar.appendChild(b);
    });
    box.appendChild(bar);
    var q = el("input", {type:"search", placeholder:"Search brand or model (e.g. Graco, Doona, YOYO)", "aria-label":"Search recalls", value:recallQuery, cls:"search"});
    box.appendChild(q);
    var holder = el("div");
    box.appendChild(holder);
    var draw = function(){
      holder.textContent = "";
      var needle = recallQuery.toLowerCase();
      var rows = db.filter(function(x){ return (recallType === "All" || x.type === recallType) &&
        (!needle || (x.brand + " " + x.products + " " + x.id).toLowerCase().indexOf(needle) >= 0); });
      var tb = el("tbody");
      rows.forEach(function(x){
        tb.appendChild(el("tr", {}, [el("td", {cls:"nw", text:fmtDate(x.date)}), el("td", {text:x.brand}),
          el("td", {}, [el("div", {text:x.products}), el("div", {cls:"muted", text:x.hazard})]),
          el("td", {}, [el("span", {cls:"flag" + (x.severity === "HIGH" ? " hot" : ""), text:x.severity})]),
          el("td", {cls:"nw"}, [link(x.source + " " + x.id, x.url)])]));
      });
      var head = el("thead", {}, [el("tr", {}, [el("th",{text:"Date"}), el("th",{text:"Brand"}), el("th",{text:"Product and hazard"}), el("th",{text:"Severity"}), el("th",{text:"Record"})])]);
      holder.appendChild(el("p", {cls:"muted", text: rows.length + " recalls shown"}));
      holder.appendChild(el("div", {cls:"scroll"}, [el("table", {}, [head, tb])]));
    };
    q.addEventListener("input", function(){ recallQuery = q.value; draw(); });
    draw();
    return;
  }
  var grid = el("div", {cls:"picks"});
  v.cat.picks.forEach(function(p){
    var re = null; try { re = new RegExp(p.match, "i"); } catch(e) {}
    var inWatch = re && watchText.some(function(t){ return re.test(t); });
    var inDb = re && p.recall === "None found" && db.some(function(x){ return re.test(x.products + " " + x.brand); });
    var flags = el("div", {cls:"flags"});
    if (inWatch) flags.appendChild(el("span", {cls:"flag hot", text:"In this report's CPSC recall watch: check it"}));
    if (inDb) flags.appendChild(el("span", {cls:"flag hot", text:"Name matches a recall in the 2016–26 list: check it"}));
    flags.appendChild(el("span", {cls:"flag" + (p.recall === "None found" ? "" : " hot"), text:"Recalls: " + p.recall}));
    p.flags.forEach(function(f){ flags.appendChild(el("span", {cls:"flag", text:f})); });
    grid.appendChild(el("div", {cls:"card pick-card"}, [
      el("header", {}, [el("h3", {}, [el("span", {cls:"rank", text:"#" + p.rank + " "}), document.createTextNode(p.name)]), el("span", {cls:"price", text:p.price})]),
      el("p", {cls:"ink2", text:p.why}), flags,
      el("div", {cls:"srcs"}, [el("span", {cls:"muted", text:"Sources:"})].concat(p.sources.map(function(s){ return link(s[0], s[1]); })))]));
  });
  box.appendChild(grid);
}

function renderEvents(r){
  var ul = $("events"); ul.textContent = "";
  if (!r.events.length){
    ul.appendChild(el("li", {cls:"empty", text: dates.indexOf(r.date) === 0 ? "This is the first report, so changes start showing tomorrow." : "Nothing changed since the previous report."}));
    return;
  }
  r.events.forEach(function(e){
    ul.appendChild(el("li", {cls:"event"}, [badge(e.severity, SEV_LABEL[e.severity]),
      el("div", {}, [el("strong", {text:e.name}), el("div", {cls:"ink2", text:e.detail})])]));
  });
}

function renderItems(r, isLatest){
  var box = $("items"); box.textContent = "";
  if (!r.items.length){ box.appendChild(el("p", {cls:"empty", text:"No items on the watchlist yet."})); return; }
  r.items.forEach(function(it){
    var det = D.details[it.key] || {};
    var v = VERDICT[it.verdict] || VERDICT.tracking;
    var card = el("article", {cls:"card"});
    card.appendChild(el("header", {}, [el("h3", {text:it.name}), badge(v[0], v[1])]));
    card.appendChild(el("p", {cls:"muted", text: it.category + (det.condition ? " · " + det.condition : "") + (det.target_price ? " · target " + money(det.target_price, it.per_unit) : "")}));
    if (it.price != null){
      card.appendChild(el("div", {}, [el("span", {cls:"price", text: money(it.price, it.per_unit) + (it.per_unit ? " / unit" : "")}),
        el("span", {cls:"ink2", text:" at " + (it.retailer || "?")})]));
      var facts = el("div", {cls:"facts"});
      if (it.stock) facts.appendChild(el("span", {text: it.stock.replace(/_/g, " ")}));
      if (it.median_90d != null){
        var pct = (it.median_90d - it.price) / it.median_90d * 100;
        facts.appendChild(el("span", {text: "90-day median " + money(it.median_90d, it.per_unit) + " (now " + Math.abs(pct).toFixed(1) + "% " + (pct >= 0 ? "below" : "above") + ")"}));
      }
      if (it.low_365d != null) facts.appendChild(el("span", {text: "12-month low " + money(it.low_365d, it.per_unit)}));
      card.appendChild(facts);
    } else {
      card.appendChild(el("p", {cls:"ink2", text:"No price logged yet."}));
    }
    var hist = (det.history || []).filter(function(p){ return p[0] <= r.date; });
    card.appendChild(sparkline(hist, it.per_unit, it.name));
    var sum = it.safety_passed ? "Safety: passes all gates · confidence " + (it.safety_score == null ? "—" : it.safety_score + "/100")
                               : "Safety: fails a gate" + (it.recalls.length ? " · recall " + it.recalls.join(", ") : "");
    var d = el("details", {}, [el("summary", {}, [it.safety_passed ? "✅ " : "❌ ", sum])]);
    if (!it.safety_passed) d.open = true;
    if (isLatest && det.safety){
      var gl = el("ul", {cls:"gates"});
      det.safety.gates.forEach(function(g){
        gl.appendChild(el("li", {cls:"g-" + g.status.replace("/", "")}, [el("b", {text:g.status.toUpperCase()}), g.name + ": " + g.evidence]));
      });
      d.appendChild(gl);
      if (det.safety.unverified && det.safety.unverified.length)
        d.appendChild(el("p", {cls:"muted", text:"Not verified yet: " + det.safety.unverified.join(", ")}));
    } else if (!isLatest){
      d.appendChild(el("p", {cls:"muted", text:"Gate details are shown for the latest report."}));
    }
    card.appendChild(d);
    box.appendChild(card);
  });
}

function renderPlan(r){
  var box = $("plan"); box.textContent = "";
  var plan = D.plan;
  if (!plan){ box.appendChild(el("p", {cls:"empty", text:"Add a due date to the watchlist to get a buy plan."})); return; }
  var bought = {};
  (r.spending.purchases || []).forEach(function(p){ if (p.category) bought[p.category] = p; });
  var tb = el("tbody");
  plan.rows.forEach(function(row){
    var status;
    if (bought[row.category]) status = badge("good", "Bought " + money(bought[row.category].price));
    else if (row.window_start && row.window_start <= r.date && row.window_end >= r.date) status = badge("warning", "Sale window open");
    else if (row.need_by < r.date) status = badge("critical", "Overdue");
    else status = el("span", {cls:"muted", text:"Planned"});
    tb.appendChild(el("tr", {}, [
      el("td", {}, [el("div", {text:row.item}), row.note ? el("div", {cls:"muted", text:row.note}) : null]),
      el("td", {cls:"nw", text:fmtDate(row.need_by)}),
      el("td", {text:row.buy_window}),
      el("td", {cls:"num", text:whole(row.estimate_low) + "–" + whole(row.estimate_high)}),
      el("td", {text: row.buy_new ? "New only" : "New or used"}),
      el("td", {}, [status])]));
  });
  var head = el("thead", {}, [el("tr", {}, ["Item","Need by","When to buy","Estimate","Condition","Status"].map(function(h, i){ return el("th", {cls: i === 3 ? "num" : "", text:h}); }))]);
  box.appendChild(el("div", {cls:"scroll"}, [el("table", {}, [head, tb])]));
  box.appendChild(el("p", {cls:"muted", style:"margin-top:8px", text:"Registry completion discount " + plan.registry_completion_window + ". " + plan.caveat}));
}

function renderSpend(r){
  var box = $("spend"); box.textContent = "";
  var ps = r.spending.purchases || [];
  if (!ps.length){ box.appendChild(el("p", {cls:"empty", text:"No purchases logged yet. Log one with: python3 -m baby_scout bought --key <item> --price <paid> --retailer <store>"})); return; }
  var tb = el("tbody");
  ps.slice().sort(function(a, b){ return a.date < b.date ? 1 : -1; }).forEach(function(p){
    var saved = p.median_90d ? p.median_90d - p.price : null;
    tb.appendChild(el("tr", {}, [el("td", {cls:"nw", text:fmtDate(p.date)}), el("td", {text:p.name || p.key}), el("td", {text:p.retailer || ""}),
      el("td", {cls:"num", text:money(p.price)}), el("td", {cls:"num", text: saved == null ? "—" : (saved >= 0 ? money(saved) : "−" + money(-saved))})]));
  });
  var head = el("thead", {}, [el("tr", {}, [el("th",{text:"Date"}), el("th",{text:"Item"}), el("th",{text:"Store"}), el("th",{cls:"num",text:"Paid"}), el("th",{cls:"num",text:"Saved vs typical"})])]);
  box.appendChild(el("div", {cls:"scroll"}, [el("table", {}, [head, tb])]));
}

function renderArchive(current){
  var box = $("archive"); box.textContent = "";
  var tb = el("tbody");
  dates.slice().reverse().forEach(function(d){
    var r = D.reports[d];
    var alerts = r.events.filter(function(e){ return e.severity === "critical"; }).length;
    var good = r.events.filter(function(e){ return e.severity === "good"; }).length;
    var tr = el("tr", {cls:"pick" + (d === current ? " sel" : ""), tabindex:"0", "aria-label":"Show report for " + fmtDate(d)}, [
      el("td", {cls:"nw", text:fmtDate(d)}), el("td", {cls:"num", text:String(r.totals.buy_now)}),
      el("td", {cls:"num", text:String(alerts)}), el("td", {cls:"num", text:String(good)}),
      el("td", {cls:"num", text:whole(r.spending.spent)}),
      el("td", {text: r.events.length ? r.events[0].name + ": " + r.events[0].type.replace(/_/g, " ") : "No changes"})]);
    var go = function(){ select(d); window.scrollTo({top:0, behavior:"smooth"}); };
    tr.addEventListener("click", go);
    tr.addEventListener("keydown", function(ev){ if (ev.key === "Enter" || ev.key === " "){ ev.preventDefault(); go(); } });
    tb.appendChild(tr);
  });
  var head = el("thead", {}, [el("tr", {}, [el("th",{text:"Date"}), el("th",{cls:"num",text:"Buy now"}), el("th",{cls:"num",text:"New alerts"}),
    el("th",{cls:"num",text:"Good news"}), el("th",{cls:"num",text:"Spent"}), el("th",{text:"Top change"})])]);
  box.appendChild(el("div", {cls:"scroll"}, [el("table", {}, [head, tb])]));
}

function select(d){
  var r = D.reports[d];
  $("day").value = d;
  var latest = d === D.latest;
  $("updated").textContent = (latest ? "Latest report · " : "Past report · ") + fmtDate(d) + " · generated " + r.generated_at.replace("T", " ").replace("Z", " UTC");
  renderKpis(r); renderEvents(r); renderRecalls(r); renderPicks(r); renderItems(r, latest); renderPlan(r); renderSpend(r); renderArchive(d);
  try { history.replaceState(null, "", latest ? location.pathname : "#" + d); } catch(e) {}
}

if (!dates.length){
  $("kpis").appendChild(el("p", {cls:"empty", text:"No reports yet. Run: python3 -m baby_scout run"}));
  return;
}
var sel = $("day");
dates.slice().reverse().forEach(function(d){ sel.appendChild(el("option", {value:d, text:fmtDate(d) + (d === D.latest ? " (latest)" : "")})); });
sel.addEventListener("change", function(){ select(sel.value); });
var fromHash = location.hash.slice(1);
select(D.reports[fromHash] ? fromHash : D.latest);
})();
</script>
</body>
</html>
"""
