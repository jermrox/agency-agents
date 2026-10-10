"""Recall watch: classification against real CPSC wording, windowing, and daily diffs."""

import datetime as dt
import json
import shutil
from pathlib import Path

from baby_scout import report, watch
from baby_scout.cli import main

FIX = Path(__file__).parent / "fixtures"
ROOT = Path(__file__).resolve().parents[1]
RAW = json.loads((FIX / "cpsc_watch_sample.json").read_text())
BY_NUMBER = {r["RecallNumber"]: r for r in RAW}


def group(number):
    return watch.classify(BY_NUMBER[number])


def test_groups_from_real_cpsc_titles():
    assert group("26-801") == "Feeding & teething"
    assert group("26-802") == "Sleep"                       # crib mattress, not furniture
    assert group("26-803") == "Nursery furniture (tip-over)"
    assert group("26-808") == "Toys"
    assert group("26-809") == "Clothing"                    # children's loungewear


def test_curly_apostrophe_childrens_is_recognised():
    # CPSC titles use U+2019; a straight-quote-only pattern missed this recall.
    assert group("26-804") == "Other kids' products"


def test_child_poisoning_hazards_are_childproofing_not_kid_products():
    assert group("26-805") == "Childproofing (poisoning risk)"


def test_adult_products_stay_out():
    assert group("26-806") is None                          # adult mattress
    assert group("26-807") is None                          # "keep out of reach of children" is not a kid product
    assert group("26-810") is None                          # adult hoodie: clothing needs a child word


def test_select_windows_dedupes_and_sorts():
    items = watch.select(RAW, since=dt.date(2026, 8, 1))
    numbers = [i["number"] for i in items]
    assert "26-500" not in numbers                          # before the window
    assert numbers.count("26-808") == 1                     # duplicate row collapsed
    assert numbers[0] == "26-808"                           # newest first
    teether = next(i for i in items if i["number"] == "26-801")
    assert teether["units"] == "About 4,500" and teether["remedy"] == "Refund" and teether["sold_at"] == "Target"


def _report(numbers, available=True):
    return {"recall_watch": {"available": available, "items": [{"number": n} for n in numbers]}}


def _items(*numbers):
    return [{"number": n, "title": f"Recall {n}", "group": "Toys", "hazard": "Choking", "url": ""} for n in numbers]


def test_first_watch_report_is_a_quiet_baseline():
    assert report.watch_events(None, _items("a", "b")) == []
    assert report.watch_events({"items": []}, _items("a", "b")) == []          # report from before the watch
    assert report.watch_events(_report([], available=False), _items("a")) == []


def test_only_new_recalls_are_announced_and_capped():
    assert [e["key"] for e in report.watch_events(_report(["a"]), _items("a", "b"))] == ["b"]
    many = _items(*[str(i) for i in range(10)])
    events = report.watch_events(_report([]), many)
    assert len(events) == report.WATCH_EVENT_LIMIT + 1
    assert events[-1]["key"] == "more" and events[-1]["detail"].startswith("4 more")
    assert report.watch_events(_report(["a"]), None) == []                     # lookup failed today


def test_run_records_watch_and_dashboard_shows_it(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    shutil.copy(ROOT / "watchlist.example.toml", data / "watchlist.toml")
    args = ["run", "--data", str(data), "--site", str(tmp_path / "site"), "--offline",
            "--recalls-file", str(FIX / "cpsc_sample.json"), "--watch-file", str(FIX / "cpsc_watch_sample.json")]
    assert main(args + ["--today", "2026-09-28"]) == 0
    day = json.loads((data / "reports" / "2026-09-28.json").read_text())
    rw = day["recall_watch"]
    assert rw["available"] and rw["days"] == 60
    assert sorted(i["number"] for i in rw["items"]) == ["26-801", "26-802", "26-803", "26-804", "26-805", "26-808", "26-809"]
    assert not any(e["type"] == "recall_watch" for e in day["events"])        # baseline day
    html = (tmp_path / "site" / "index.html").read_text()
    assert "Baby &amp; kid recalls" in html and "renderRecalls" in html


def test_offline_run_marks_watch_unavailable(tmp_path):
    data = tmp_path / "data"
    data.mkdir()
    shutil.copy(ROOT / "watchlist.example.toml", data / "watchlist.toml")
    assert main(["run", "--data", str(data), "--site", str(tmp_path / "site"), "--offline", "--today", "2026-09-28"]) == 0
    day = json.loads((data / "reports" / "2026-09-28.json").read_text())
    assert day["recall_watch"] == {"available": False, "days": 60, "items": []}
