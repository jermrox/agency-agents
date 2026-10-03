import datetime as dt
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build", ROOT / "build.py")
build = importlib.util.module_from_spec(spec)
spec.loader.exec_module(build)

TODAY = dt.date(2026, 10, 2)
PARAMS = build.load_params()


def row(**kw):
    base = {
        "name": "Example Ventures", "org": "Example Ventures", "type": "vc", "hunt": "investor",
        "why": "Led a seed round in a wearable company.", "evidence": ["https://example.com/a"],
        "fit": 8, "confidence": "verified", "contact_url": "https://example.com/pitch",
        "last_signal_date": "2026-08-01", "opener": "Hi", "ask": "15-minute call",
    }
    base.update(kw)
    return base


def test_valid_row_passes():
    assert build.validate(row(), PARAMS, TODAY) == []


def test_rejects_missing_evidence_low_fit_and_guessed_email():
    assert "no evidence URL" in build.validate(row(evidence=[]), PARAMS, TODAY)
    assert any("below" in r for r in build.validate(row(fit=5), PARAMS, TODAY))
    assert any("guessed" in r for r in build.validate(row(contact_url="jane@example.com"), PARAMS, TODAY))


def test_rejects_past_deadline_stale_investor_and_unrelated_vybe():
    assert any("passed" in r for r in build.validate(row(deadline="2026-09-01"), PARAMS, TODAY))
    assert any("too old" in r for r in build.validate(row(last_signal_date="2023-01-01"), PARAMS, TODAY))
    assert any("excluded" in r for r in build.validate(row(name="VybeBand"), PARAMS, TODAY))


def test_grants_belong_to_funding_sweep():
    assert any("funding sweep" in r for r in build.validate(row(name="Acme SBIR Phase I"), PARAMS, TODAY))
    assert build.validate(row(why="Backed a wearable with DoD SBIR support"), PARAMS, TODAY) == []


def test_score_bonuses_and_cap():
    s, label = build.score(row(fit=9, deadline="2026-10-20"), PARAMS, TODAY)
    assert s == 100 and label == "High"
    s, label = build.score(row(fit=7, confidence="single-source", contact_url=None, last_signal_date=None), PARAMS, TODAY)
    assert s == 70 and label == "Low"


def test_build_dedupes_and_ranks(tmp_path, monkeypatch):
    raw = tmp_path / "raw"
    raw.mkdir()
    (raw / "a.json").write_text(json.dumps([row(fit=7), row(name="Other Fund", org="Other Fund", fit=9)]))
    (raw / "b.json").write_text(json.dumps([row(fit=8, evidence=["https://example.com/b"])]))
    monkeypatch.setattr(build, "RAW", raw)
    targets, rejected, lanes = build.build(PARAMS, TODAY)
    assert [t["name"] for t in targets] == ["Other Fund", "Example Ventures"]
    ex = targets[1]
    assert ex["fit"] == 8 and set(ex["evidence"]) == {"https://example.com/a", "https://example.com/b"}
    assert [t["rank"] for t in targets] == [1, 2]
    assert rejected == []


def test_render_escapes_script_close(tmp_path):
    data = {"generated": "2026-10-02 18:30 UTC", "targets": [{"name": "</script><b>x"}]}
    out = build.render(data)
    assert "</script><b>x" not in out


def test_sponsorship_rows_are_valid_and_competitor_deals_dedupe_by_headline():
    a = row(name="WHOOP x HYROX", org="WHOOP", type="competitor-deal", hunt="sponsorship", contact_url=None)
    assert build.validate(a, PARAMS, TODAY) == []
    assert build.dedupe_key(a) == build.dedupe_key(dict(a, org="Whoop Inc"))
    assert build.validate(row(type="athlete", hunt="sponsorship"), PARAMS, TODAY) == []


def test_founder_identity_openers_are_flagged():
    assert build.uses_founder_identity(row(opener="Hi - Vybe is a woman-, veteran- and minority-owned startup"))
    assert build.uses_founder_identity(row(opener="I'm a veteran founder in Akron"))
    assert not build.uses_founder_identity(row(opener="Our cohort gets monthly calls with veteran mentors"))
    assert not build.uses_founder_identity(row(opener="We're building Vybe Health in Akron, Ohio"))


def test_link_check_drops_dead_links(tmp_path, monkeypatch):
    checks = {
        "https://example.com/a": {"status": "dead", "note": "404"},
        "https://example.com/b": {"status": "ok", "note": "live"},
        "https://example.com/pitch": {"status": "dead", "note": "form removed"},
    }
    r = row(evidence=["https://example.com/a", "https://example.com/b"])
    assert build.apply_link_check(r, checks) is None
    assert r["evidence"] == ["https://example.com/b"]
    assert r["contact_url"] is None and r["link_status"] == "contact dead"

    gone = row(evidence=["https://example.com/a"])
    assert "dead" in build.apply_link_check(gone, checks)

    fresh = row(evidence=["https://example.com/b"], contact_url=None)
    build.apply_link_check(fresh, checks)
    assert fresh["link_status"] == "verified"
    unchecked = row(evidence=["https://example.com/zzz"], contact_url=None)
    build.apply_link_check(unchecked, checks)
    assert unchecked["link_status"] == "not checked"


def test_warm_intro_rows_are_not_sendable():
    assert build.is_sendable(row())
    assert not build.is_sendable(row(channel="warm intro needed"))
    assert not build.is_sendable(row(contact_url=None))
    assert not build.is_sendable(row(type="signal"))


def test_app_partner_rows_must_show_existing_integrations():
    ok = row(type="app-partner", hunt="partnership", existing_wearables=["Garmin"], exclusive=False,
             partner_status="open", opportunity="Add Vybe via their Terra integration")
    assert build.validate(ok, PARAMS, TODAY) == []
    no_list = dict(ok); del no_list["existing_wearables"]
    assert any("existing_wearables" in r for r in build.validate(no_list, PARAMS, TODAY))
    assert any("scored above 6" in r for r in build.validate(dict(ok, partner_status="exclusive"), PARAMS, TODAY))
    assert any("opportunity" in r for r in build.validate(dict(ok, opportunity=""), PARAMS, TODAY))


def test_sport_rows_need_adoption_evidence():
    s = row(type="sport", hunt="partnership", wearable_adoption="Survey: 12% of clubs", opportunity="Club pilot")
    assert build.validate(s, PARAMS, TODAY) == []
    assert build.validate(dict(s, wearable_adoption=None), PARAMS, TODAY)
