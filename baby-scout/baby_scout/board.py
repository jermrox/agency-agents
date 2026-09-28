"""Assemble per-item results into board.json and a self-contained board.html."""

from __future__ import annotations

import datetime as dt
import html
import json
from pathlib import Path
from typing import Any

from . import deals
from .models import WatchItem, utcnow
from .recalls import RecallMatch
from .safety import SafetyReport
from .store import PriceStore


def item_result(item: WatchItem, store: PriceStore, safety: SafetyReport,
                recalls: RecallMatch | None, today: dt.date | None = None) -> dict[str, Any]:
    latest = store.latest(item.key)
    in_stock = [o for o in latest if o.stock_status != "out_of_stock"]
    best = min(in_stock or latest, key=lambda o: o.unit_price or o.price, default=None)
    per_unit = bool(item.unit_count or (best and best.unit_count))
    deal = None
    if best is not None:
        current = best.unit_price if per_unit and best.unit_price else best.price
        deal = deals.score(current, store.history(item.key, per_unit=per_unit),
                           list_price=None if per_unit else best.list_price, today=today)
        if not safety.passed:
            deal.verdict = "skip"
    return {
        "key": item.key,
        "name": item.name,
        "brand": item.brand,
        "model": item.model,
        "category": item.category,
        "condition": item.condition,
        "target_price": item.target_price,
        "per_unit": per_unit,
        "best": best.to_dict() if best else None,
        "offers": [o.to_dict() for o in latest],
        "deal": deal.to_dict() if deal else None,
        "at_or_below_target": bool(deal and item.target_price and deal.current <= item.target_price),
        "safety": safety.to_dict(),
        "recalls": {
            "model": [r.to_dict() for r in recalls.model_hits],
            "brand_count": len(recalls.brand_hits),
        } if recalls else None,
    }


def write(results: list[dict[str, Any]], out_dir: str | Path, plan: dict[str, Any] | None = None) -> tuple[Path, Path]:
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    payload = {"generated_at": utcnow(), "items": results, "plan": plan}
    json_path = out / "board.json"
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    html_path = out / "board.html"
    html_path.write_text(render_html(payload), encoding="utf-8")
    return json_path, html_path


def _money(v: float | None, per_unit: bool = False) -> str:
    if v is None:
        return "—"
    return f"${v:,.3f}" if per_unit and v < 1 else f"${v:,.2f}"


def _card(r: dict[str, Any]) -> str:
    e = html.escape
    s = r["safety"]
    d = r["deal"]
    best = r["best"]
    verdict = d["verdict"] if d else ("skip" if not s["passed"] else "tracking")
    label = deals.VERDICT_LABELS[verdict]
    unit = " / unit" if r["per_unit"] else ""
    price_line = "No price logged yet."
    if best:
        price_line = (f"<strong>{_money(d['current'] if d else best['price'], r['per_unit'])}{unit}</strong> at "
                      f"{e(best['retailer'])} · {e(best['stock_status'].replace('_', ' '))} · "
                      f"seen {e(best['observed_at'][:16].replace('T', ' '))} UTC ({e(best['source'])})")
    stats = ""
    if d and d.get("median_90d") is not None:
        pct = d["pct_below_median"]
        direction = f"{pct:.1f}% below" if pct >= 0 else f"{-pct:.1f}% above"
        stats = (f"<li>90-day median {_money(d['median_90d'], r['per_unit'])} → now {direction}</li>"
                 f"<li>365-day low {_money(d['low_365d'], r['per_unit'])}</li>")
    elif d:
        stats = f"<li>{e(d['note'])}</li>"
    if d and r["target_price"] and not r["at_or_below_target"]:
        stats += f"<li>Above your target of {_money(r['target_price'], r['per_unit'])}</li>"
    if d and d.get("fake_discount"):
        stats += f"<li class='warn'>{e(d['note'])}</li>"
    gates = "".join(
        f"<li class='g-{e(g['status'].replace('/', ''))}'><span>{e(g['status'].upper())}</span> "
        f"{e(g['name'])}: {e(g['evidence'])}</li>" for g in s["gates"])
    score = f"{s['score']}/100" if s["score"] is not None else "not scored (failed a gate)"
    unverified = (f"<p class='muted'>Unverified: {e(', '.join(s['unverified']))}</p>" if s["unverified"] else "")
    return f"""
<article class="card v-{verdict}">
  <header><h2>{e(r['name'])}</h2><span class="pill">{e(label)}</span></header>
  <p class="muted">{e(r['category'])} · {e(r['condition'])}{' · target ' + _money(r['target_price']) if r['target_price'] else ''}</p>
  <p>{price_line}</p>
  <ul class="stats">{stats}</ul>
  <details {'open' if not s['passed'] else ''}><summary>Safety: {'✅ passes gates' if s['passed'] else '❌ fails a gate'} · confidence {score}</summary>
    <ul class="gates">{gates}</ul>{unverified}
  </details>
</article>"""


def render_html(payload: dict[str, Any]) -> str:
    e = html.escape
    cards = "".join(_card(r) for r in payload["items"]) or "<p>No items on the watchlist yet.</p>"
    plan_html = ""
    plan = payload.get("plan")
    if plan:
        rows = "".join(
            f"<tr><td>{e(r['item'])}</td><td class='nw'>{e(r['need_by'])}</td><td>{e(r['buy_window'])}</td>"
            f"<td>${r['estimate_low']:,}–${r['estimate_high']:,}</td><td>{'New' if r['buy_new'] else 'New or used'}</td></tr>"
            for r in plan["rows"])
        budget = f" vs budget ${plan['budget']:,.0f}" if plan.get("budget") else ""
        plan_html = f"""
<section><h2>Buy plan — due {e(plan['due_date'])}</h2>
<p>Estimated ${plan['estimate_low']:,}–${plan['estimate_high']:,}{budget}. Registry completion discount {e(plan['registry_completion_window'])}.</p>
<div class="scroll"><table><thead><tr><th>Item</th><th>Need by</th><th>When to buy</th><th>Estimate</th><th>Buy</th></tr></thead>
<tbody>{rows}</tbody></table></div>
<p class="muted">{e(plan['caveat'])}</p></section>"""
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Baby Gear Board</title>
<style>
:root{{--bg:#fbf8f6;--fg:#1f1a1c;--muted:#6b6166;--card:#fff;--line:#eadfe3;--good:#15803d;--mid:#a16207;--bad:#b91c1c;--accent:#db2777}}
@media (prefers-color-scheme:dark){{:root:not([data-theme="light"]){{--bg:#161214;--fg:#f3eef0;--muted:#a79ca1;--card:#211b1e;--line:#3a3035;--good:#4ade80;--mid:#facc15;--bad:#f87171;--accent:#f472b6}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--fg);font:15px/1.5 system-ui,-apple-system,Segoe UI,sans-serif;padding:24px 16px}}
main{{max-width:1040px;margin:0 auto}}h1{{margin:0 0 4px}}h2{{font-size:17px;margin:0}}
.muted{{color:var(--muted);font-size:13px}}.grid{{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));margin:20px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-left:4px solid var(--line);border-radius:10px;padding:14px}}
.v-buy_now{{border-left-color:var(--good)}}.v-good,.v-fair,.v-wait{{border-left-color:var(--mid)}}.v-skip{{border-left-color:var(--bad)}}
.card header{{display:flex;flex-wrap:wrap;justify-content:space-between;gap:6px 8px;align-items:start}}.card h2{{flex:1 1 160px}}.pill{{font-size:12px;white-space:nowrap;border:1px solid var(--line);border-radius:99px;padding:2px 8px}}
ul{{padding-left:18px;margin:6px 0}}.gates{{list-style:none;padding:0;font-size:13px}}.gates li{{margin:4px 0}}
.gates span{{font-weight:600;font-size:11px;margin-right:4px}}.g-pass span{{color:var(--good)}}.g-fail span{{color:var(--bad)}}.g-check span{{color:var(--mid)}}.g-na span{{color:var(--muted)}}
.warn{{color:var(--bad)}}summary{{cursor:pointer;font-size:14px}}
.scroll{{overflow-x:auto}}.nw{{white-space:nowrap}}table{{border-collapse:collapse;width:100%;font-size:14px}}th,td{{text-align:left;padding:6px 8px;border-bottom:1px solid var(--line);vertical-align:top}}
</style></head><body><main>
<h1>🍼 Baby Gear Board</h1>
<p class="muted">Generated {e(payload['generated_at'])}. Prices are judged against their own history, not list price. Safety gates run before any deal is shown. Not medical advice.</p>
<div class="grid">{cards}</div>{plan_html}
</main></body></html>
"""
