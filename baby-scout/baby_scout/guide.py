"""Render the interactive Safety Guide page (site/guide.html).

The guide is the browsable side of the curated research: a top 10 per
category with photos, prices, test scores, recalls and sources, plus the brand
verdicts, safety-tech grades and the 2016-2026 recall list from
data/gear_picks.json. Like the dashboard it is one self-contained file with the
data embedded; product photos are the only external requests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

CATEGORIES = [
    ("infant_car_seats", "Infant car seats", "🍼"),
    ("convertible_car_seats", "Convertible & all-in-one seats", "🚗"),
    ("travel_systems", "Travel systems & combos", "🧩"),
    ("compact_strollers", "Compact & travel strollers", "✈️"),
    ("fullsize_strollers", "Full-size & modular strollers", "🛒"),
    ("joggers_wagons", "Joggers & wagons", "🏃"),
]


def load_top10(top10_dir: str | Path | None) -> list[dict[str, Any]]:
    """Each category's ranked list from data/top10/<slug>.json, in display order."""
    out = []
    if not top10_dir or not Path(top10_dir).is_dir():
        return out
    for slug, name, icon in CATEGORIES:
        path = Path(top10_dir) / f"{slug}.json"
        if path.exists():
            items = json.loads(path.read_text(encoding="utf-8"))
            out.append({"slug": slug, "name": name, "icon": icon,
                        "items": sorted(items, key=lambda x: x.get("rank") or 99)})
    return out


def write(site_dir: str | Path, picks: dict[str, Any] | None, top10: list[dict[str, Any]],
          generated_at: str) -> Path | None:
    if not picks and not top10:
        return None
    data = {"generated_at": generated_at, "picks": picks or {}, "categories": top10}
    embedded = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
    page = Path(site_dir) / "guide.html"
    page.write_text(TEMPLATE.replace("__DATA__", embedded), encoding="utf-8")
    return page


TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Baby Gear Safety Guide</title>
<meta name="description" content="Top 10 car seats, strollers and travel systems ranked on independent safety evidence, with photos, prices, recalls and sources.">
<style>
:root{
  color-scheme:light;
  --page:#f7f6f2;--surface:#fdfcfa;--raised:#ffffff;--sunk:#efede6;
  --ink:#141412;--ink-2:#4f4d48;--muted:#77746c;
  --border:rgba(20,20,18,.11);--grid:#e2e0d8;
  --accent:#c2185b;--accent-ink:#ffffff;--accent-soft:#fde7ef;
  --blue:#2a78d6;--blue-soft:#e3effd;
  --good:#0b8a3e;--good-soft:#e2f5e9;--warn:#a86700;--warn-soft:#fff2d6;--bad:#c62f2f;--bad-soft:#fde6e4;
  --shadow:0 1px 2px rgba(0,0,0,.05),0 6px 18px rgba(0,0,0,.06);
}
@media (prefers-color-scheme:dark){
  :root:where(:not([data-theme="light"])){
    color-scheme:dark;
    --page:#0f0f0e;--surface:#1a1a18;--raised:#22221f;--sunk:#141412;
    --ink:#f5f4ef;--ink-2:#c9c7be;--muted:#9a978e;
    --border:rgba(255,255,255,.11);--grid:#2d2d2a;
    --accent:#f472b6;--accent-ink:#1a0610;--accent-soft:#3a1626;
    --blue:#5aa2f0;--blue-soft:#15304f;
    --good:#3fcf74;--good-soft:#11331e;--warn:#f0b445;--warn-soft:#3a2c0d;--bad:#ff7a6e;--bad-soft:#3d1714;
    --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 22px rgba(0,0,0,.35);
  }
}
:root[data-theme="dark"]{
  color-scheme:dark;
  --page:#0f0f0e;--surface:#1a1a18;--raised:#22221f;--sunk:#141412;
  --ink:#f5f4ef;--ink-2:#c9c7be;--muted:#9a978e;
  --border:rgba(255,255,255,.11);--grid:#2d2d2a;
  --accent:#f472b6;--accent-ink:#1a0610;--accent-soft:#3a1626;
  --blue:#5aa2f0;--blue-soft:#15304f;
  --good:#3fcf74;--good-soft:#11331e;--warn:#f0b445;--warn-soft:#3a2c0d;--bad:#ff7a6e;--bad-soft:#3d1714;
  --shadow:0 1px 2px rgba(0,0,0,.4),0 8px 22px rgba(0,0,0,.35);
}
*{box-sizing:border-box}
html,body{margin:0;background:var(--page);color:var(--ink)}
body{font:15px/1.5 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;padding:0 16px 120px}
a{color:var(--blue)}
button,input,select{font:inherit;color:var(--ink)}
main{max-width:1240px;margin:0 auto}
.hero{padding:28px 0 18px;display:flex;flex-wrap:wrap;gap:12px 24px;align-items:flex-end;justify-content:space-between}
.hero h1{font-size:30px;line-height:1.15;margin:0;letter-spacing:-.01em}
.hero p{margin:6px 0 0;color:var(--ink-2);max-width:720px}
.top-actions{display:flex;gap:8px;flex-wrap:wrap}
.btn{background:var(--raised);border:1px solid var(--border);border-radius:10px;padding:7px 12px;cursor:pointer;text-decoration:none;color:var(--ink);display:inline-flex;align-items:center;gap:6px}
.btn:hover{border-color:var(--ink-2)}
.btn.primary{background:var(--accent);color:var(--accent-ink);border-color:var(--accent)}
.btn[aria-pressed="true"]{background:var(--ink);color:var(--page);border-color:var(--ink)}
.notice{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:12px 14px;color:var(--ink-2);font-size:13.5px;margin-bottom:14px}
.notice b{color:var(--ink)}
.cats{display:flex;gap:8px;overflow-x:auto;padding:4px 0 10px;scrollbar-width:thin}
.cat{flex:none;display:flex;flex-direction:column;align-items:flex-start;gap:2px;min-width:150px;padding:10px 12px;border-radius:14px;border:1px solid var(--border);background:var(--surface);cursor:pointer;text-align:left}
.cat .ic{font-size:20px}.cat .nm{font-weight:650;font-size:14px}.cat .ct{font-size:12px;color:var(--muted)}
.cat[aria-pressed="true"]{background:var(--ink);color:var(--page);border-color:var(--ink)}
.cat[aria-pressed="true"] .ct{color:var(--page);opacity:.75}
.layout{display:grid;grid-template-columns:260px 1fr;gap:18px;align-items:start}
@media (max-width:900px){.layout{grid-template-columns:1fr}}
.filters{position:sticky;top:12px;background:var(--surface);border:1px solid var(--border);border-radius:14px;padding:14px;display:grid;gap:14px}
@media (max-width:900px){.filters{position:static}.filters.collapsed .fbody{display:none}}
.filters h2{font-size:14px;margin:0;display:flex;justify-content:space-between;align-items:center}
.fbody{display:grid;gap:14px}
.fgroup label.title{display:block;font-size:12px;font-weight:650;color:var(--ink-2);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px}
.search{width:100%;padding:8px 10px;border-radius:10px;border:1px solid var(--border);background:var(--raised)}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:12.5px;padding:4px 10px;border-radius:99px;border:1px solid var(--border);background:var(--raised);cursor:pointer}
.chip[aria-pressed="true"]{background:var(--ink);color:var(--page);border-color:var(--ink)}
input[type=range]{width:100%;accent-color:var(--accent)}
.rangeval{font-size:13px;color:var(--ink-2)}
select{width:100%;padding:7px 10px;border-radius:10px;border:1px solid var(--border);background:var(--raised)}
.resultbar{display:flex;flex-wrap:wrap;gap:8px 16px;align-items:center;justify-content:space-between;margin-bottom:10px}
.resultbar .count{color:var(--ink-2);font-size:14px}
.grid{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(280px,1fr))}
.card{position:relative;background:var(--surface);border:1px solid var(--border);border-radius:16px;overflow:hidden;display:flex;flex-direction:column;box-shadow:var(--shadow);min-width:0}
.card.saved{outline:2px solid var(--accent);outline-offset:-2px}
.photo{position:relative;aspect-ratio:4/3;background:#fff;display:flex;align-items:center;justify-content:center;border-bottom:1px solid var(--border)}
.photo img{max-width:88%;max-height:88%;object-fit:contain}
.photo .ph{font-size:46px;font-weight:700;color:#c9c6bc}
.rank{position:absolute;top:10px;left:10px;background:var(--ink);color:var(--page);font-weight:750;font-size:14px;border-radius:10px;padding:3px 9px}
.rank.r1{background:linear-gradient(135deg,#d4a017,#f5d36b);color:#2a1d00}
.heart{position:absolute;top:8px;right:8px;width:36px;height:36px;border-radius:50%;border:1px solid var(--border);background:rgba(255,255,255,.92);cursor:pointer;font-size:17px;line-height:1;color:#222}
.heart[aria-pressed="true"]{background:var(--accent);color:#fff;border-color:var(--accent)}
.body{padding:12px 14px 14px;display:flex;flex-direction:column;gap:9px;flex:1}
.brand{font-size:12px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted);font-weight:650}
.name{font-size:16.5px;font-weight:700;line-height:1.25;margin:0}
.pricerow{display:flex;align-items:baseline;justify-content:space-between;gap:8px;flex-wrap:wrap}
.price{font-size:22px;font-weight:750}
.price small{font-size:12px;color:var(--muted);font-weight:500;margin-left:4px}
.pill{display:inline-flex;align-items:center;gap:5px;font-size:12px;font-weight:650;border-radius:99px;padding:2px 9px;white-space:nowrap}
.ev-Strong{background:var(--good-soft);color:var(--good)}
.ev-Moderate{background:var(--blue-soft);color:var(--blue)}
.ev-Limited{background:var(--warn-soft);color:var(--warn)}
.ev-Maker{background:var(--sunk);color:var(--ink-2)}
.scores{display:grid;gap:5px}
.bar{display:grid;grid-template-columns:92px 1fr 40px;gap:8px;align-items:center;font-size:12.5px;color:var(--ink-2)}
.track{height:8px;background:var(--sunk);border-radius:4px;overflow:hidden}
.track>span{display:block;height:100%;border-radius:4px;background:var(--blue)}
.bar b{color:var(--ink);text-align:right;font-variant-numeric:tabular-nums}
.labels{display:flex;flex-wrap:wrap;gap:5px}
.lab{font-size:12px;border-radius:7px;padding:2px 7px;background:var(--sunk);color:var(--ink-2)}
.lab.cr-Best{background:var(--good-soft);color:var(--good)}.lab.cr-Better{background:var(--blue-soft);color:var(--blue)}.lab.cr-Basic{background:var(--bad-soft);color:var(--bad)}
.specs{display:flex;flex-wrap:wrap;gap:3px 12px;font-size:12.5px;color:var(--ink-2)}
.feats{display:flex;flex-wrap:wrap;gap:5px}
.feat{font-size:11.5px;border:1px solid var(--border);border-radius:7px;padding:1px 7px;color:var(--ink-2)}
.recall{font-size:12.5px;border-radius:9px;padding:6px 9px}
.recall.ok{background:var(--good-soft);color:var(--good)}
.recall.bad{background:var(--bad-soft);color:var(--bad)}
.why{font-size:13.5px;color:var(--ink-2);margin:0}
details{font-size:13px}
details summary{cursor:pointer;color:var(--ink-2);font-weight:600}
details ul{margin:6px 0 0;padding-left:18px;color:var(--ink-2)}
.srcs{font-size:12px;display:flex;flex-wrap:wrap;gap:3px 10px}
.actions{display:flex;gap:8px;margin-top:auto;padding-top:4px}
.actions .btn{flex:1;justify-content:center;font-size:13.5px;padding:7px 8px}
.empty{background:var(--surface);border:1px dashed var(--muted);border-radius:14px;padding:24px;color:var(--ink-2);text-align:center}
.tray{position:fixed;left:50%;bottom:14px;transform:translateX(-50%);width:min(980px,calc(100% - 24px));background:var(--raised);border:1px solid var(--border);border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.25);padding:10px 12px;display:none;align-items:center;gap:10px;z-index:20}
.tray.show{display:flex}
.tray .slots{display:flex;gap:8px;flex:1;overflow-x:auto}
.slot{flex:none;display:flex;align-items:center;gap:6px;background:var(--sunk);border-radius:10px;padding:4px 8px;font-size:13px;max-width:220px}
.slot img{width:30px;height:30px;object-fit:contain;background:#fff;border-radius:6px}
.slot span{white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.slot button{border:0;background:none;cursor:pointer;color:var(--muted);font-size:15px}
dialog{border:1px solid var(--border);border-radius:16px;background:var(--surface);color:var(--ink);padding:0;width:min(1100px,calc(100% - 24px));max-height:88vh}
dialog::backdrop{background:rgba(0,0,0,.45)}
.dhead{display:flex;justify-content:space-between;align-items:center;padding:12px 16px;border-bottom:1px solid var(--border);position:sticky;top:0;background:var(--surface)}
.dhead h2{margin:0;font-size:18px}
.cmp{overflow:auto;padding:0 0 12px}
.cmp table{border-collapse:collapse;width:100%;min-width:640px;font-size:13.5px}
.cmp th,.cmp td{border-bottom:1px solid var(--grid);padding:9px 12px;text-align:left;vertical-align:top}
.cmp th{color:var(--ink-2);font-weight:600;width:150px;background:var(--surface);position:sticky;left:0}
.cmp-photo{width:140px;height:105px;display:flex;align-items:center;justify-content:center;background:#fff;border-radius:10px;border:1px solid var(--border)}
.cmp-photo img{max-width:92%;max-height:92%;object-fit:contain}
.cmp-photo .ph{font-size:30px;font-weight:700;color:#c9c6bc}
.cmp .best{background:var(--good-soft)}
section.more{margin-top:34px}
section.more h2{font-size:20px;margin:0 0 4px}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0}
.list{list-style:none;margin:0;padding:0;display:grid;gap:8px}
.list li{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:10px 12px}
.list .t{font-weight:650}
.list .d{color:var(--ink-2);font-size:13.5px;margin-top:2px}
.tag{font-size:11.5px;font-weight:650;border-radius:7px;padding:1px 7px;margin-left:6px;background:var(--sunk);color:var(--ink-2)}
.tag.hot{background:var(--bad-soft);color:var(--bad)}.tag.good{background:var(--good-soft);color:var(--good)}
.rtable{overflow-x:auto;background:var(--surface);border:1px solid var(--border);border-radius:12px}
.rtable table{border-collapse:collapse;width:100%;min-width:680px;font-size:13.5px}
.rtable th,.rtable td{padding:8px 12px;border-bottom:1px solid var(--grid);text-align:left;vertical-align:top}
.rtable th{font-size:12px;color:var(--ink-2)}
.nw{white-space:nowrap}
.foot{margin-top:40px;font-size:12.5px;color:var(--muted)}
:focus-visible{outline:2px solid var(--blue);outline-offset:2px}
</style>
</head>
<body>
<main>
  <div class="hero">
    <div>
      <h1>🛡️ Baby Gear Safety Guide</h1>
      <p>Top 10 car seats, strollers and combos in each category, ranked on independent crash tests, recall records and proven safety features. Every number links to its source.</p>
    </div>
    <div class="top-actions">
      <a class="btn" href="index.html">← Daily dashboard</a>
      <button class="btn" id="show-saved" type="button" aria-pressed="false">♥ Saved <span id="saved-count">0</span></button>
      <button class="btn" id="theme" type="button" aria-label="Toggle light or dark theme">◐</button>
    </div>
  </div>
  <div class="notice" id="notice"></div>
  <div class="cats" id="cats" role="group" aria-label="Choose a category"></div>
  <div class="layout">
    <aside class="filters collapsed" id="filters" aria-label="Filters">
      <h2>Filters <button class="btn" id="toggle-filters" type="button" style="padding:3px 9px;font-size:12.5px">Show</button></h2>
      <div class="fbody">
        <div class="fgroup"><label class="title" for="q">Search</label><input class="search" id="q" type="search" placeholder="Brand, model, feature…"></div>
        <div class="fgroup"><label class="title" for="price">Max price</label><input id="price" type="range" min="0" max="2000" step="25"><div class="rangeval" id="price-val"></div></div>
        <div class="fgroup"><span class="title" style="display:block;font-size:12px;font-weight:650;color:var(--ink-2);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px">Must have</span><div class="chips" id="f-feats"></div></div>
        <div class="fgroup"><span class="title" style="display:block;font-size:12px;font-weight:650;color:var(--ink-2);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px">Evidence</span><div class="chips" id="f-ev"></div></div>
        <div class="fgroup"><span class="title" style="display:block;font-size:12px;font-weight:650;color:var(--ink-2);text-transform:uppercase;letter-spacing:.04em;margin-bottom:6px">Brand</span><div class="chips" id="f-brands"></div></div>
        <div class="fgroup"><label class="chip" style="display:inline-flex;gap:6px;align-items:center"><input type="checkbox" id="f-norecall"> No recalls 2016–26</label></div>
        <button class="btn" id="reset" type="button">Reset filters</button>
      </div>
    </aside>
    <div>
      <div class="resultbar">
        <div class="count" id="count"></div>
        <label style="display:flex;gap:8px;align-items:center;font-size:14px">Sort
          <select id="sort" style="width:auto">
            <option value="rank">Safety rank</option>
            <option value="price-asc">Price: low to high</option>
            <option value="price-desc">Price: high to low</option>
            <option value="crash">Crash score</option>
            <option value="weight">Lightest</option>
          </select>
        </label>
      </div>
      <div class="grid" id="grid"></div>
    </div>
  </div>

  <section class="more" aria-labelledby="h-more">
    <h2 id="h-more">Brands, tech, recalls &amp; sources</h2>
    <div class="tabs" id="more-tabs" role="group" aria-label="More research"></div>
    <div id="more"></div>
  </section>
  <p class="foot" id="foot"></p>
</main>

<div class="tray" id="tray" aria-live="polite">
  <strong style="font-size:13px;white-space:nowrap">Compare</strong>
  <div class="slots" id="slots"></div>
  <button class="btn primary" id="open-compare" type="button">Compare</button>
  <button class="btn" id="clear-compare" type="button" aria-label="Clear comparison">✕</button>
</div>
<dialog id="dlg" aria-labelledby="dlg-title">
  <div class="dhead"><h2 id="dlg-title">Side-by-side</h2><button class="btn" id="close-dlg" type="button">Close</button></div>
  <div class="cmp" id="cmp"></div>
</dialog>

<script type="application/json" id="data">__DATA__</script>
<script>
(function(){
"use strict";
var D = JSON.parse(document.getElementById("data").textContent);
var P = D.picks || {}, CATS = D.categories || [];
var $ = function(id){ return document.getElementById(id); };
function el(tag, attrs, kids){
  var n = document.createElement(tag);
  if (attrs) for (var k in attrs){
    var v = attrs[k]; if (v == null) continue;
    if (k === "text") n.textContent = v; else if (k === "cls") n.className = v; else n.setAttribute(k, v);
  }
  (kids || []).forEach(function(c){ if (c != null) n.appendChild(typeof c === "string" ? document.createTextNode(c) : c); });
  return n;
}
function store(key, val){ try { if (val === undefined) return JSON.parse(localStorage.getItem(key) || "null"); localStorage.setItem(key, JSON.stringify(val)); } catch(e) { return null; } }
var safeUrl = function(u){ return typeof u === "string" && /^https:\/\//.test(u) ? u : null; };
var money = function(v){ return v == null ? "Price n/a" : "$" + Number(v).toLocaleString("en-US", {maximumFractionDigits: v % 1 ? 2 : 0}); };
var fmtDate = function(s){ var p = (s || "").slice(0,10).split("-"); if (p.length < 3) return s || ""; return new Date(Date.UTC(+p[0], +p[1]-1, +p[2])).toLocaleDateString("en-US", {month:"short", day:"numeric", year:"numeric", timeZone:"UTC"}); };
var link = function(t, u){ var s = safeUrl(u); return s ? el("a", {href:s, target:"_blank", rel:"noopener noreferrer", text:t}) : el("span", {text:t}); };

// theme
(function(){
  var saved = store("guide-theme"); if (saved) document.documentElement.setAttribute("data-theme", saved);
  $("theme").addEventListener("click", function(){
    var cur = document.documentElement.getAttribute("data-theme") || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
    var next = cur === "dark" ? "light" : "dark"; document.documentElement.setAttribute("data-theme", next); store("guide-theme", next);
  });
})();

// every item gets a stable id
CATS.forEach(function(c){ c.items.forEach(function(it){ it._id = c.slug + ":" + it.rank; it._cat = c.name; }); });
var byId = {}; CATS.forEach(function(c){ c.items.forEach(function(it){ byId[it._id] = it; }); });

var state = {cat: 0, q: "", maxPrice: null, feats: [], ev: [], brands: [], noRecall: false, sort: "rank", savedOnly: false};
var saved = (store("guide-saved") || []).filter(function(id){ return byId[id]; });
var compare = (store("guide-compare") || []).filter(function(id){ return byId[id]; });
var hashCat = CATS.findIndex(function(c){ return c.slug === location.hash.slice(1); });
if (hashCat >= 0) state.cat = hashCat; else if (store("guide-cat") != null && CATS[store("guide-cat")]) state.cat = store("guide-cat");

var reviewed = P.reviewed ? fmtDate(P.reviewed) : "";
$("notice").appendChild(el("span", {}, [el("b", {text:"How to read this: "}),
  "no U.S. government crash rating exists for car seats, and every seat sold legally passes the federal crash test, so ranks separate good from better, not safe from unsafe. Scores come from Consumer Reports and BabyGearLab (see “How much to trust the sources” below). “No recall found” was checked against NHTSA and CPSC data" + (reviewed ? " on " + reviewed : "") + "; always check your exact model number at NHTSA.gov/recalls. Prices are list prices and change often."]));

function current(){ return CATS[state.cat] || {items: []}; }
function isRecalled(it){ return (it.recall_ids && it.recall_ids.length) || (it.recall_status && !/^none/i.test(it.recall_status)); }
function evKey(it){ return (it.evidence_level || "Limited").split(" ")[0]; }

function renderCats(){
  var box = $("cats"); box.textContent = "";
  CATS.forEach(function(c, i){
    var b = el("button", {cls:"cat", type:"button", "aria-pressed": String(i === state.cat)}, [
      el("span", {cls:"ic", text:c.icon}), el("span", {cls:"nm", text:c.name}), el("span", {cls:"ct", text:"Top " + c.items.length})]);
    b.addEventListener("click", function(){ state.cat = i; state.brands = []; state.feats = []; state.savedOnly = false; $("show-saved").setAttribute("aria-pressed", "false");
      store("guide-cat", i); try { history.replaceState(null, "", "#" + c.slug); } catch(e) {} renderAll(); });
    box.appendChild(b);
  });
}

function chipGroup(id, values, selected, onChange){
  var box = $(id); box.textContent = "";
  values.forEach(function(v){
    var b = el("button", {cls:"chip", type:"button", "aria-pressed": String(selected.indexOf(v) >= 0), text:v});
    b.addEventListener("click", function(){ var i = selected.indexOf(v); if (i >= 0) selected.splice(i, 1); else selected.push(v); onChange(); });
    box.appendChild(b);
  });
}

function renderFilters(){
  var items = current().items;
  var brands = Array.from(new Set(items.map(function(x){ return x.brand; }).filter(Boolean))).sort();
  var feats = {}; items.forEach(function(x){ (x.features || []).forEach(function(f){ feats[f] = (feats[f] || 0) + 1; }); });
  chipGroup("f-brands", brands, state.brands, renderGrid);
  chipGroup("f-feats", Object.keys(feats).sort(function(a, b){ return feats[b] - feats[a]; }), state.feats, renderGrid);
  chipGroup("f-ev", ["Strong", "Moderate", "Limited", "Maker"], state.ev, renderGrid);
  var prices = items.map(function(x){ return x.price_usd; }).filter(function(v){ return v != null; });
  var top = prices.length ? Math.ceil(Math.max.apply(null, prices) / 50) * 50 : 2000;
  var r = $("price"); r.max = String(top);
  if (state.maxPrice == null || state.maxPrice > top) state.maxPrice = top;
  r.value = String(state.maxPrice);
  $("price-val").textContent = "Up to " + money(state.maxPrice);
}

function filtered(){
  var pool = state.savedOnly ? saved.map(function(id){ return byId[id]; }) : current().items.slice();
  var q = state.q.toLowerCase();
  var out = pool.filter(function(x){
    if (!state.savedOnly){
      if (state.maxPrice != null && x.price_usd != null && x.price_usd > state.maxPrice) return false;
      if (state.brands.length && state.brands.indexOf(x.brand) < 0) return false;
      if (state.feats.some(function(f){ return (x.features || []).indexOf(f) < 0; })) return false;
      if (state.ev.length && state.ev.indexOf(evKey(x)) < 0) return false;
      if (state.noRecall && isRecalled(x)) return false;
    }
    if (q && (x.name + " " + x.brand + " " + (x.features || []).join(" ") + " " + (x.why || "")).toLowerCase().indexOf(q) < 0) return false;
    return true;
  });
  var num = function(v, dflt){ return v == null ? dflt : v; };
  var s = state.sort;
  out.sort(function(a, b){
    if (s === "price-asc") return num(a.price_usd, 1e9) - num(b.price_usd, 1e9);
    if (s === "price-desc") return num(b.price_usd, -1) - num(a.price_usd, -1);
    if (s === "crash") return num(b.scores && b.scores.bgl_crash, -1) - num(a.scores && a.scores.bgl_crash, -1);
    if (s === "weight") return num(a.specs && a.specs.weight_lb, 1e9) - num(b.specs && b.specs.weight_lb, 1e9);
    return (a._cat === b._cat ? 0 : (a._cat < b._cat ? -1 : 1)) || a.rank - b.rank;
  });
  return out;
}

function photo(it, cls){
  var box = el("div", {cls: cls || "photo"});
  var initials = (it.brand || it.name || "?").split(/\s+/).map(function(w){ return w[0]; }).join("").slice(0, 2).toUpperCase();
  var src = safeUrl(it.image_url);
  if (src){
    var img = el("img", {src:src, alt:it.name, loading:"lazy", referrerpolicy:"no-referrer", decoding:"async"});
    img.addEventListener("error", function(){ img.replaceWith(el("span", {cls:"ph", text:initials})); });
    box.appendChild(img);
  } else box.appendChild(el("span", {cls:"ph", text:initials}));
  return box;
}

function bar(label, value, max, suffix){
  if (value == null) return null;
  var pct = Math.max(0, Math.min(100, value / max * 100));
  return el("div", {cls:"bar"}, [el("span", {text:label}), el("div", {cls:"track", role:"img", "aria-label": label + " " + value + " of " + max}, [el("span", {style:"width:" + pct + "%"})]), el("b", {text:String(value) + (suffix || "")})]);
}

function card(it){
  var sc = it.scores || {}, sp = it.specs || {};
  var isSaved = saved.indexOf(it._id) >= 0, inCmp = compare.indexOf(it._id) >= 0;
  var ph = photo(it);
  ph.appendChild(el("span", {cls:"rank" + (it.rank === 1 ? " r1" : ""), text:"#" + it.rank}));
  var heart = el("button", {cls:"heart", type:"button", "aria-pressed": String(isSaved), "aria-label": (isSaved ? "Remove " : "Save ") + it.name, text: isSaved ? "♥" : "♡"});
  heart.addEventListener("click", function(){ toggle(saved, it._id); store("guide-saved", saved); renderAll(); });
  ph.appendChild(heart);

  var labels = el("div", {cls:"labels"});
  if (sc.cr_crash) labels.appendChild(el("span", {cls:"lab cr-" + sc.cr_crash, text:"CR crash: " + sc.cr_crash}));
  if (sc.wirecutter) labels.appendChild(el("span", {cls:"lab", text:"Wirecutter: " + sc.wirecutter}));
  if (sc.adac) labels.appendChild(el("span", {cls:"lab", text:"ADAC (EU): " + sc.adac}));
  var specs = el("div", {cls:"specs"});
  [["⚖️", sp.weight_lb != null ? sp.weight_lb + " lb" : null], ["🪑", sp.carrier_weight_lb != null ? "carrier " + sp.carrier_weight_lb + " lb" : null], ["👶", sp.child_range], ["↩️", sp.rear_facing_max_lb != null ? "RF to " + sp.rear_facing_max_lb + " lb" : null],
   ["↔️", sp.width_in != null ? sp.width_in + " in wide" : null], ["📦", sp.fold], ["⏳", sp.expiration_years != null ? sp.expiration_years + "-yr life" : null]]
   .forEach(function(s){ if (s[1]) specs.appendChild(el("span", {text:s[0] + " " + s[1]})); });
  var recalled = isRecalled(it);
  var recallTxt = (recalled ? "⚠️ " : "✓ ") + (it.recall_status || "No recall found") + (it.investigation ? " · Investigation: " + it.investigation : "");
  var cmpBtn = el("button", {cls:"btn", type:"button", "aria-pressed": String(inCmp), text: inCmp ? "✓ Comparing" : "+ Compare"});
  cmpBtn.addEventListener("click", function(){
    if (!inCmp && compare.length >= 4){ alert("You can compare up to 4 at a time."); return; }
    toggle(compare, it._id); store("guide-compare", compare); renderAll();
  });
  var more = el("details", {}, [el("summary", {text:"Cautions & sources"}),
    (it.cautions && it.cautions.length) ? el("ul", {}, it.cautions.map(function(c){ return el("li", {text:c}); })) : null,
    el("div", {cls:"srcs", style:"margin-top:6px"}, [el("span", {cls:"muted", text:"Sources:"})].concat((it.sources || []).map(function(s){ return link(s[0], s[1]); }))
      .concat(it.price_source_url ? [link("Price", it.price_source_url)] : []))]);
  return el("article", {cls:"card" + (isSaved ? " saved" : "")}, [ph, el("div", {cls:"body"}, [
    el("div", {cls:"brand", text: (it.brand || "") + (state.savedOnly ? " · " + it._cat : "")}),
    el("h3", {cls:"name", text:it.name}),
    el("div", {cls:"pricerow"}, [el("span", {cls:"price"}, [money(it.price_usd), it.price_note ? el("small", {text:it.price_note}) : null]),
      el("span", {cls:"pill ev-" + evKey(it), text:"Evidence: " + (it.evidence_level || "Limited")})]),
    el("div", {cls:"scores"}, [bar("Crash (BGL)", sc.bgl_crash, 10), bar("Overall (BGL)", sc.bgl_overall, 100), bar("Brakes (BGL)", sc.bgl_brakes, 10)]),
    labels.childNodes.length ? labels : null,
    specs.childNodes.length ? specs : null,
    (it.features && it.features.length) ? el("div", {cls:"feats"}, it.features.map(function(f){ return el("span", {cls:"feat", text:f}); })) : null,
    el("div", {cls:"recall " + (recalled || it.investigation ? "bad" : "ok"), text:recallTxt}),
    el("p", {cls:"why", text:it.why || ""}),
    more,
    el("div", {cls:"actions"}, [cmpBtn, safeUrl(it.product_url) ? el("a", {cls:"btn", href:safeUrl(it.product_url), target:"_blank", rel:"noopener noreferrer", text:"View product ↗"}) : null])
  ])]);
}
function toggle(arr, id){ var i = arr.indexOf(id); if (i >= 0) arr.splice(i, 1); else arr.push(id); }

function renderGrid(){
  renderFilters();
  var items = filtered(), grid = $("grid"); grid.textContent = "";
  var c = current();
  $("count").textContent = state.savedOnly ? items.length + " saved item" + (items.length === 1 ? "" : "s") + " across all categories" :
    "Showing " + items.length + " of " + c.items.length + " in " + c.name;
  if (!items.length){
    grid.appendChild(el("div", {cls:"empty", text: state.savedOnly ? "Nothing saved yet. Tap ♡ on any product to build your shortlist." : "No products match these filters. Try raising the price or removing a filter."}));
  } else items.forEach(function(it){ grid.appendChild(card(it)); });
  $("saved-count").textContent = String(saved.length);
  renderTray();
}

function renderTray(){
  var tray = $("tray"), slots = $("slots"); slots.textContent = "";
  tray.classList.toggle("show", compare.length > 0);
  compare.forEach(function(id){
    var it = byId[id]; var x = el("button", {type:"button", "aria-label":"Remove " + it.name, text:"✕"});
    x.addEventListener("click", function(){ toggle(compare, id); store("guide-compare", compare); renderAll(); });
    var thumb = safeUrl(it.image_url) ? el("img", {src:safeUrl(it.image_url), alt:"", referrerpolicy:"no-referrer"}) : null;
    slots.appendChild(el("div", {cls:"slot"}, [thumb, el("span", {text:it.name}), x]));
  });
  $("open-compare").disabled = compare.length < 2;
  $("open-compare").textContent = compare.length < 2 ? "Pick 2+" : "Compare " + compare.length;
}

function openCompare(){
  var items = compare.map(function(id){ return byId[id]; });
  var box = $("cmp"); box.textContent = "";
  var best = function(vals, higher){ var nums = vals.filter(function(v){ return v != null; }); if (nums.length < 2 || Math.max.apply(null, nums) === Math.min.apply(null, nums)) return null; return higher ? Math.max.apply(null, nums) : Math.min.apply(null, nums); };
  var rows = [
    ["", function(it){ return photo(it, "cmp-photo"); }],
    ["Product", function(it){ return el("div", {}, [el("div", {cls:"brand", text:it.brand}), el("strong", {text:it.name}), el("div", {cls:"muted", text:it._cat + " · #" + it.rank})]); }],
    ["Price", function(it){ return money(it.price_usd); }, function(it){ return it.price_usd; }, false],
    ["Evidence", function(it){ return it.evidence_level || ""; }],
    ["BGL crash /10", function(it){ return it.scores && it.scores.bgl_crash != null ? String(it.scores.bgl_crash) : "—"; }, function(it){ return it.scores && it.scores.bgl_crash; }, true],
    ["BGL overall", function(it){ return it.scores && it.scores.bgl_overall != null ? String(it.scores.bgl_overall) : "—"; }, function(it){ return it.scores && it.scores.bgl_overall; }, true],
    ["BGL brakes /10", function(it){ return it.scores && it.scores.bgl_brakes != null ? String(it.scores.bgl_brakes) : "—"; }, function(it){ return it.scores && it.scores.bgl_brakes; }, true],
    ["CR crash", function(it){ return (it.scores && it.scores.cr_crash) || "—"; }],
    ["Wirecutter", function(it){ return (it.scores && it.scores.wirecutter) || "—"; }],
    ["Weight", function(it){ return it.specs && it.specs.weight_lb != null ? it.specs.weight_lb + " lb" : "—"; }, function(it){ return it.specs && it.specs.weight_lb; }, false],
    ["Child range", function(it){ return (it.specs && it.specs.child_range) || "—"; }],
    ["Fold / width", function(it){ return (it.specs && (it.specs.fold || (it.specs.width_in ? it.specs.width_in + " in" : null))) || "—"; }],
    ["Features", function(it){ return (it.features || []).join(", ") || "—"; }],
    ["Recalls", function(it){ return (it.recall_status || "None found") + (it.investigation ? " · " + it.investigation : ""); }],
    ["Why ranked", function(it){ return it.why || ""; }],
    ["Cautions", function(it){ return (it.cautions || []).join(" · ") || "—"; }]
  ];
  var tb = el("tbody");
  rows.forEach(function(r){
    var b = r[2] ? best(items.map(r[2]), r[3]) : null;
    var tr = el("tr", {}, [el("th", {text:r[0]})]);
    items.forEach(function(it){ var v = r[1](it); var td = el("td", {cls: b != null && r[2](it) === b ? "best" : null}); td.appendChild(typeof v === "string" ? document.createTextNode(v) : v); tr.appendChild(td); });
    tb.appendChild(tr);
  });
  box.appendChild(el("table", {}, [tb]));
  box.appendChild(el("p", {cls:"muted", style:"padding:0 16px", text:"Green = best value in that row. Compare crash scores only within the same tester; BGL and CR use different tests."}));
  var d = $("dlg"); if (d.showModal) d.showModal(); else d.setAttribute("open", "");
}

// research tabs
var moreTab = 0, recallType = "All", recallQ = "";
function renderMore(){
  var tabs = $("more-tabs"), box = $("more"); tabs.textContent = ""; box.textContent = "";
  var db = (P.recall_db && P.recall_db.items) || [];
  var views = [];
  if (P.brands) views.push(["Brands A–Z (" + P.brands.length + ")", "brands"]);
  if (P.tech) views.push(["Safety tech: what's proven", "tech"]);
  if (db.length) views.push(["All recalls 2016–2026 (" + db.length + ")", "recalls"]);
  if (P.avoid) views.push(["Avoid / recalled", "avoid"]);
  if (P.trust) views.push(["How much to trust the sources", "trust"]);
  if (P.dates) views.push(["Key dates & sales", "dates"]);
  if (!views.length){ box.appendChild(el("p", {cls:"muted", text:"No research data."})); return; }
  if (moreTab >= views.length) moreTab = 0;
  views.forEach(function(v, i){ var b = el("button", {cls:"chip", type:"button", "aria-pressed": String(i === moreTab), text:v[0]}); b.addEventListener("click", function(){ moreTab = i; renderMore(); }); tabs.appendChild(b); });
  var kind = views[moreTab][1];
  var list = function(items, tagOf){
    var ul = el("ul", {cls:"list"});
    items.forEach(function(x){
      var t = tagOf ? tagOf(x) : null;
      ul.appendChild(el("li", {}, [el("div", {cls:"t"}, [link(x.name || x.label, x.url), t ? el("span", {cls:"tag" + (/caution|none|weak/i.test(t) ? " hot" : (/recommended|strong/i.test(t) ? " good" : "")), text:t}) : null]),
        x.detail ? el("div", {cls:"d", text:x.detail}) : null]));
    });
    box.appendChild(ul);
  };
  if (kind === "brands") return list(P.brands, function(x){ return x.verdict; });
  if (kind === "tech") return list(P.tech, function(x){ return "Evidence: " + x.grade; });
  if (kind === "avoid") return list(P.avoid);
  if (kind === "trust") return list(P.trust, function(x){ return x.weight; });
  if (kind === "dates") return list(P.dates.map(function(x){ return {name: fmtDate(x.date) + ": " + x.label, url: x.url}; }));
  box.appendChild(el("p", {cls:"muted", text:P.recall_db.note}));
  var types = ["All"], counts = {};
  db.forEach(function(x){ counts[x.type] = (counts[x.type] || 0) + 1; if (types.indexOf(x.type) < 0) types.push(x.type); });
  var chips = el("div", {cls:"chips", style:"margin:8px 0"});
  types.forEach(function(t){ var b = el("button", {cls:"chip", type:"button", "aria-pressed": String(t === recallType), text:t + " (" + (t === "All" ? db.length : counts[t]) + ")"}); b.addEventListener("click", function(){ recallType = t; renderMore(); }); chips.appendChild(b); });
  box.appendChild(chips);
  var q = el("input", {cls:"search", type:"search", placeholder:"Search recalls by brand or model (e.g. Graco, Doona, YOYO)", value:recallQ, "aria-label":"Search recalls", style:"max-width:440px;margin-bottom:8px"});
  box.appendChild(q);
  var holder = el("div"); box.appendChild(holder);
  var draw = function(){
    holder.textContent = "";
    var n = recallQ.toLowerCase();
    var rows = db.filter(function(x){ return (recallType === "All" || x.type === recallType) && (!n || (x.brand + " " + x.products + " " + x.id).toLowerCase().indexOf(n) >= 0); });
    var tb = el("tbody");
    rows.forEach(function(x){ tb.appendChild(el("tr", {}, [el("td", {cls:"nw", text:fmtDate(x.date)}), el("td", {text:x.brand}),
      el("td", {}, [el("div", {text:x.products}), el("div", {cls:"muted", style:"font-size:12.5px", text:x.hazard})]),
      el("td", {}, [el("span", {cls:"tag" + (x.severity === "HIGH" ? " hot" : ""), text:x.severity})]), el("td", {cls:"nw"}, [link(x.source + " " + x.id, x.url)])])); });
    holder.appendChild(el("p", {cls:"muted", text:rows.length + " recalls shown"}));
    holder.appendChild(el("div", {cls:"rtable"}, [el("table", {}, [el("thead", {}, [el("tr", {}, ["Date","Brand","Product and hazard","Severity","Record"].map(function(h){ return el("th", {text:h}); }))]), tb])]));
  };
  q.addEventListener("input", function(){ recallQ = q.value; draw(); });
  draw();
}

function renderAll(){ renderCats(); renderGrid(); }

$("q").addEventListener("input", function(){ state.q = this.value; renderGrid(); });
$("price").addEventListener("input", function(){ state.maxPrice = +this.value; $("price-val").textContent = "Up to " + money(state.maxPrice); renderGrid(); });
$("sort").addEventListener("change", function(){ state.sort = this.value; renderGrid(); });
$("f-norecall").addEventListener("change", function(){ state.noRecall = this.checked; renderGrid(); });
$("reset").addEventListener("click", function(){ state.q = ""; $("q").value = ""; state.maxPrice = null; state.feats = []; state.ev = []; state.brands = []; state.noRecall = false; $("f-norecall").checked = false; renderGrid(); });
$("toggle-filters").addEventListener("click", function(){ var f = $("filters"); f.classList.toggle("collapsed"); this.textContent = f.classList.contains("collapsed") ? "Show" : "Hide"; });
if (matchMedia("(min-width: 901px)").matches){ $("filters").classList.remove("collapsed"); $("toggle-filters").style.display = "none"; }
$("show-saved").addEventListener("click", function(){ state.savedOnly = !state.savedOnly; this.setAttribute("aria-pressed", String(state.savedOnly)); renderGrid(); });
$("open-compare").addEventListener("click", openCompare);
$("clear-compare").addEventListener("click", function(){ compare = []; store("guide-compare", compare); renderAll(); });
$("close-dlg").addEventListener("click", function(){ var d = $("dlg"); if (d.close) d.close(); else d.removeAttribute("open"); });
$("foot").textContent = "Guide generated " + (D.generated_at || "").replace("T", " ").replace("Z", " UTC") + ". Product photos and names belong to their manufacturers and link to the source page. This guide is research, not a substitute for your seat's manual or a certified child passenger safety technician.";

if (!CATS.length){ $("grid").appendChild(el("div", {cls:"empty", text:"Top 10 lists are not available yet."})); renderMore(); return; }
renderAll(); renderMore();
})();
</script>
</body>
</html>
"""
