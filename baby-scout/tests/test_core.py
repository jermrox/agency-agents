import datetime as dt
import json
from pathlib import Path

import pytest

from baby_scout import deals, plan, recalls, safety
from baby_scout.collect import extract_products, observation_from_page
from baby_scout.models import Observation, WatchItem
from baby_scout.store import PriceStore

FIX = Path(__file__).parent / "fixtures"
TODAY = dt.date(2026, 9, 28)


def _recalls():
    return [recalls.parse_recall(r) for r in json.loads((FIX / "cpsc_sample.json").read_text())]


# -- deals -----------------------------------------------------------------

def _hist(prices, start=TODAY - dt.timedelta(days=80), step=10):
    return [(start + dt.timedelta(days=i * step), p) for i, p in enumerate(prices)]


def test_tracking_until_enough_history():
    s = deals.score(100, _hist([110, 105]), today=TODAY)
    assert s.verdict == "tracking"


def test_buy_now_at_annual_low():
    s = deals.score(199, _hist([249, 259, 249, 239, 249, 205]), today=TODAY)
    assert s.verdict == "buy_now"


def test_wait_when_sale_is_above_median():
    s = deals.score(255, _hist([249, 249, 245, 249, 199]), today=TODAY)
    assert s.verdict == "wait"
    assert s.pct_below_median < 0


def test_good_band():
    s = deals.score(210, _hist([250, 250, 250, 250, 180]), today=TODAY)
    assert s.verdict == "good"


def test_fake_discount_flagged():
    s = deals.score(249, _hist([259, 259, 255, 259, 239]), list_price=399, today=TODAY)
    assert s.fake_discount
    assert "list" in s.note


def test_stack_compounds_and_gift_card_only_if_used():
    r = deals.stack(100, pct_off=[15, 10])
    assert r["at_register"] == 76.5
    used = deals.stack(100, gift_card=20)
    unused = deals.stack(100, gift_card=20, gift_card_will_be_used=False)
    assert used["net"] == 80 and unused["net"] == 100


def test_unit_price():
    assert deals.unit_price(39.99, 198) == pytest.approx(0.202, abs=1e-3)
    with pytest.raises(ValueError):
        deals.unit_price(10, 0)


# -- recalls ---------------------------------------------------------------

def test_model_match_by_model_number():
    m = recalls.match_recalls(_recalls(), "Nestwell", "Cozy Dream Bassinet", "NW-CD100")
    assert [r.number for r in m.model_hits] == ["25-901"]
    assert len(m.brand_hits) == 2


def test_other_model_of_same_brand_not_matched():
    m = recalls.match_recalls(_recalls(), "Nestwell", "Travel Crib Lite", "NW-TC9")
    assert m.model_hits == []
    assert len(m.brand_recent(5, TODAY)) == 1   # only the 2025 one is within 5 years


def test_other_brand_ignored():
    m = recalls.match_recalls(_recalls(), "Bramble & Co.", "Roam Convertible Car Seat", "BC-RC-22")
    assert m.model_hits == [] and len(m.brand_hits) == 1


# -- safety ----------------------------------------------------------------

def _item(**kw):
    base = dict(key="k", brand="Nestwell", model="Cozy Dream Bassinet", category="bassinet", model_number="NW-CD100")
    base.update(kw)
    return WatchItem(**base)


def test_open_recall_fails_gate_and_gets_no_score():
    item = _item()
    rep = safety.evaluate(item, recalls.match_recalls(_recalls(), "Nestwell", item.model, item.model_number), today=TODAY)
    assert not rep.passed and rep.score is None
    assert "25-901" in rep.failures[0].evidence


def test_remedied_recall_passes():
    item = _item(remedy_applied=["25-901"])
    rep = safety.evaluate(item, recalls.match_recalls(_recalls(), "Nestwell", item.model, item.model_number), today=TODAY)
    assert rep.passed and rep.score is not None


@pytest.mark.parametrize("text", ["Dreamy Inclined Sleeper", "Plush Crib Bumper set", "drop-side crib",
                                  "weighted sleep sack", "Infant sleep positioner"])
def test_banned_types(text):
    assert safety.banned_reason(text)


def test_banned_type_fails_gate():
    rep = safety.evaluate(_item(model="Rock n Rest Inclined Sleeper", model_number=""), None, today=TODAY)
    assert not rep.passed


def test_used_car_seat_rules():
    ok = _item(category="car_seat.infant", model="Snug", model_number="", condition="used",
               expiration_date="2031-01-01", crash_history_known=True, labels_intact=True)
    assert safety.evaluate(ok, None, today=TODAY).passed
    expired = _item(category="car_seat.infant", model="Snug", model_number="", condition="used",
                    expiration_date="2025-01-01", crash_history_known=True, labels_intact=True)
    rep = safety.evaluate(expired, None, today=TODAY)
    assert not rep.passed and "expired" in rep.failures[0].evidence
    unknown = _item(category="car_seat.infant", model="Snug", model_number="", condition="used")
    assert not safety.evaluate(unknown, None, today=TODAY).passed


def test_used_breast_pump_fails():
    rep = safety.evaluate(_item(category="breast_pump", model="Pump", model_number="", condition="used"), None, today=TODAY)
    assert not rep.passed


def test_unverified_factors_are_listed():
    rep = safety.evaluate(_item(model="Other", model_number="X"), None, today=TODAY)
    assert rep.passed
    assert "Voluntary certification (JPMA)" in rep.unverified
    assert any(g.status == "check" for g in rep.gates)   # recall lookup did not run


def test_car_seat_points_to_nhtsa():
    rep = safety.evaluate(_item(category="car_seat.convertible", model="Roam", model_number=""), None, today=TODAY)
    assert any("nhtsa" in link for link in rep.links)


def test_mandatory_standard_lookup():
    assert safety.mandatory_standard("car_seat.infant") == "FMVSS 213"
    assert safety.mandatory_standard("crib.full_size") == "16 CFR 1220"
    assert safety.mandatory_standard("diapers") is None


# -- collect ---------------------------------------------------------------

def test_extract_jsonld_product():
    [p] = extract_products((FIX / "product_page.html").read_text())
    assert p["price"] == 129.99 and p["list_price"] == 189.99
    assert p["stock_status"] == "in_stock" and p["seller"] == "Example Mart"
    assert p["rating"] == 4.6 and p["review_count"] == 812


def test_observation_from_page_marks_seller():
    obs = observation_from_page("k", "Example Mart", "https://example.com", (FIX / "product_page.html").read_text())
    assert obs.sold_by_retailer is True and obs.source == "jsonld"


def test_page_without_markup_raises():
    from baby_scout.collect import CollectError
    with pytest.raises(CollectError):
        observation_from_page("k", "X", "https://example.com", "<html><body>no data</body></html>")


# -- store -----------------------------------------------------------------

def test_store_history_takes_daily_low_and_skips_out_of_stock(tmp_path):
    s = PriceStore(tmp_path / "p.jsonl")
    s.append(Observation("k", "A", 100, observed_at="2026-09-01T10:00:00Z"))
    s.append(Observation("k", "B", 90, observed_at="2026-09-01T11:00:00Z"))
    s.append(Observation("k", "C", 50, observed_at="2026-09-02T11:00:00Z", stock_status="out_of_stock"))
    assert s.history("k") == [(dt.date(2026, 9, 1), 90)]
    assert [o.retailer for o in s.latest("k")] == ["C", "B", "A"]


def test_unit_price_history(tmp_path):
    s = PriceStore(tmp_path / "p.jsonl")
    s.append(Observation("d", "A", 39.6, observed_at="2026-09-01T10:00:00Z", unit_count=198))
    assert s.history("d", per_unit=True) == [(dt.date(2026, 9, 1), 0.2)]


# -- plan ------------------------------------------------------------------

def test_window_must_close_before_need_by():
    w = plan.best_window(dt.date(2026, 12, 20), TODAY, ("black_friday", "fall_trade_in"))
    assert w[0] == "black_friday" and w[2] <= dt.date(2026, 12, 20)
    none = plan.best_window(dt.date(2026, 10, 1), TODAY, ("black_friday",))
    assert none is None


def test_plan_orders_by_need_and_skips_owned():
    result = plan.build_plan(dt.date(2027, 2, 10), 4500, today=TODAY, owned={"high_chair"})
    cats = [r["category"] for r in result["rows"]]
    assert "high_chair" not in cats
    assert [r["need_by"] for r in result["rows"]] == sorted(r["need_by"] for r in result["rows"])
    seat = next(r for r in result["rows"] if r["category"] == "car_seat.infant")
    assert "Black Friday" in seat["buy_window"]


def test_overdue_item():
    result = plan.build_plan(dt.date(2026, 10, 1), today=TODAY)
    pump = next(r for r in result["rows"] if r["category"] == "breast_pump")
    assert pump["buy_window"].startswith("Overdue")


def test_unit_prices_keep_sub_cent_precision():
    s = deals.score(0.2171, _hist([0.2231, 0.2212, 0.2248, 0.2205, 0.2226]), today=TODAY)
    assert s.median_90d == 0.2226 and s.low_365d == 0.2171
