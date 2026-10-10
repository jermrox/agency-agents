"""Daily report diffs, spending roll-up and the end-to-end run -> dashboard path."""

import datetime as dt
import json
import shutil
from pathlib import Path

from baby_scout import report
from baby_scout.cli import main
from baby_scout.models import Observation
from baby_scout.store import PriceStore

FIX = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]


def _item(**kw):
    base = dict(key="k", name="Thing", category="stroller", verdict="fair", price=100.0, per_unit=False,
                retailer="A", stock="in_stock", median_90d=110.0, low_365d=95.0, at_or_below_target=False,
                safety_passed=True, safety_score=80, recalls=[])
    base.update(kw)
    return base


def _events(prev_items, items):
    return report.diff({"items": prev_items}, items, None, dt.date(2026, 9, 28))


def test_new_recall_is_critical_and_first():
    ev = _events([_item()], [_item(recalls=["25-901"], safety_passed=False, verdict="skip", price=80)])
    assert ev[0]["type"] == "new_recall" and ev[0]["severity"] == "critical"


def test_price_drop_and_rise():
    assert [e["type"] for e in _events([_item()], [_item(price=96)])] == ["price_drop"]
    assert [e["type"] for e in _events([_item()], [_item(price=110)])] == ["price_rise"]
    assert _events([_item()], [_item(price=101)]) == []


def test_new_low_beats_plain_drop():
    ev = _events([_item()], [_item(price=90, low_365d=90)])
    assert [e["type"] for e in ev] == ["new_low"]


def test_no_price_events_when_out_of_stock():
    ev = _events([_item()], [_item(price=130, stock="out_of_stock")])
    assert [e["type"] for e in ev] == ["out_of_stock"]


def test_buy_now_and_target_fire_once():
    now = _item(verdict="buy_now", at_or_below_target=True)
    assert {e["type"] for e in _events([_item()], [now])} == {"buy_now", "hit_target"}
    assert _events([now], [now]) == []


def test_bought_items_are_quiet():
    assert _events([_item()], [_item(verdict="bought", price=50)]) == []


def test_spending_rollup():
    plan = {"rows": [{"category": "stroller", "estimate_low": 100, "estimate_high": 300},
                     {"category": "monitor", "estimate_low": 50, "estimate_high": 150}]}
    s = report.spending([{"key": "s", "category": "stroller", "price": 200, "median_90d": 250}], 1000, plan)
    assert s["spent"] == 200 and s["saved_vs_typical"] == 50
    assert s["still_to_buy_high"] == 150 and s["projected_high"] == 350 and s["remaining_budget"] == 800


def test_run_builds_archive_and_dashboard(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    shutil.copy(ROOT / "watchlist.example.toml", data / "watchlist.toml")
    store = PriceStore(data / "prices.jsonl")
    for i, price in enumerate([150, 149, 151, 150, 148, 150]):
        store.append(Observation("nestwell-cozy-dream", "Example Mart", price,
                                 observed_at=f"2026-09-{10 + i:02d}T12:00:00Z"))
    common = ["run", "--data", str(data), "--site", str(tmp_path / "site"), "--offline",
              "--recalls-file", str(FIX / "cpsc_sample.json")]
    assert main(common + ["--today", "2026-09-20"]) == 0
    assert main(["bought", "--data", str(data), "--key", "bramble-roam-convertible", "--price", "240",
                 "--retailer", "Big Box", "--date", "2026-09-21"]) == 0
    assert main(common + ["--today", "2026-09-21"]) == 0

    day1 = json.loads((data / "reports" / "2026-09-20.json").read_text())
    day2 = json.loads((data / "reports" / "2026-09-21.json").read_text())
    assert any(e["type"] == "new_recall" for e in day1["events"])
    assert day1["spending"]["spent"] == 0 and day2["spending"]["spent"] == 240
    assert any(e["type"] == "purchased" for e in day2["events"])
    assert not any(e["type"] == "new_recall" for e in day2["events"])   # not re-announced

    html = (tmp_path / "site" / "index.html").read_text()
    assert "Baby Gear Dashboard" in html and "</script>" in html
    embedded = html.split('id="data">', 1)[1].split("</script>", 1)[0]
    payload = json.loads(embedded)
    assert sorted(payload["reports"]) == ["2026-09-20", "2026-09-21"]
    assert payload["latest"] == "2026-09-21"
    assert (tmp_path / "site" / "reports" / "2026-09-20.json").exists()


def test_backfilled_report_ignores_later_prices(tmp_path):
    store = PriceStore(tmp_path / "p.jsonl")
    store.append(Observation("k", "A", 100, observed_at="2026-09-01T10:00:00Z"))
    store.append(Observation("k", "A", 50, observed_at="2026-09-10T10:00:00Z"))
    assert store.latest("k", until=dt.date(2026, 9, 5))[0].price == 100
    assert store.history("k", until=dt.date(2026, 9, 5)) == [(dt.date(2026, 9, 1), 100)]


def test_dashboard_embeds_sourced_safety_picks(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    shutil.copy(ROOT / "watchlist.example.toml", data / "watchlist.toml")
    shutil.copy(ROOT / "data" / "gear_picks.json", data / "gear_picks.json")
    assert main(["run", "--data", str(data), "--site", str(tmp_path / "site"), "--offline",
                 "--recalls-file", str(FIX / "cpsc_sample.json"), "--today", "2026-10-03"]) == 0
    html = (tmp_path / "site" / "index.html").read_text()
    picks = json.loads(html.split('id="data">', 1)[1].split("</script>", 1)[0])["picks"]
    names = [c["name"] for c in picks["categories"]]
    assert names == ["Infant car seats", "Convertible car seats", "Compact strollers", "Car seat + stroller combos"]
    assert picks["trust"] and all(t["url"].startswith("https://") for t in picks["trust"])
    for cat in picks["categories"]:
        assert 3 <= len(cat["picks"]) <= 5
        for p in cat["picks"]:
            assert p["sources"] and all(url.startswith("https://") for _, url in p["sources"])
    assert all(a["url"].startswith("https://") for a in picks["avoid"] + picks["brands"] + picks["tech"])
    assert len(picks["recall_db"]["items"]) > 50
    guide_html = (tmp_path / "site" / "guide.html").read_text()
    assert "Baby Gear Safety Guide" in guide_html and 'href="guide.html"' in html
    assert all(x["url"].startswith("https://") for x in picks["recall_db"]["items"])


def test_dashboard_without_picks_file(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    shutil.copy(ROOT / "watchlist.example.toml", data / "watchlist.toml")
    assert main(["run", "--data", str(data), "--site", str(tmp_path / "site"), "--offline",
                 "--recalls-file", str(FIX / "cpsc_sample.json"), "--today", "2026-10-03"]) == 0
    html = (tmp_path / "site" / "index.html").read_text()
    assert json.loads(html.split('id="data">', 1)[1].split("</script>", 1)[0])["picks"] is None


def test_top10_lists_are_complete_and_sourced():
    for path in sorted((ROOT / "data" / "top10").glob("*.json")):
        items = json.loads(path.read_text())
        assert [x["rank"] for x in sorted(items, key=lambda x: x["rank"])] == list(range(1, 11)), path.name
        for x in items:
            assert x["name"] and x["brand"] and x["sources"], (path.name, x.get("name"))
            for url in [x.get("image_url"), x.get("product_url"), x.get("price_source_url")] + [s[1] for s in x["sources"]]:
                assert url is None or url.startswith("https://"), (path.name, x["name"], url)
