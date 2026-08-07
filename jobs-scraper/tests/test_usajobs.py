"""Tests for the USAJOBS adapter.

The payload shape here mirrors the real data.usajobs.gov Search API response
(SearchResult.SearchResultItems[].MatchedObjectDescriptor). No test reaches
the network; fetch_json is replaced as imported into the adapter module.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.sources.usajobs import DEFAULT_KEYWORDS, USAJobsSource  # noqa: E402


@pytest.fixture(autouse=True)
def block_the_network(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError(
            "test reached the network; monkeypatch fetch_json as imported "
            "into tactical_jobs.sources.usajobs"
        )

    monkeypatch.setattr("tactical_jobs.sources.usajobs.fetch_json", blocked)


def _descriptor(**overrides):
    base = {
        "PositionID": "ARMY-H2F-25-001",
        "PositionTitle": "Strength and Conditioning Coach",
        "PositionURI": "https://www.usajobs.gov/job/123456700",
        "OrganizationName": "Department of the Army",
        "DepartmentName": "Department of Defense",
        "PositionLocationDisplay": "Fort Bragg, North Carolina",
        "QualificationSummary": "Supports the H2F program for an Infantry Brigade.",
        "PublicationStartDate": "2026-07-15T00:00:00Z",
        "PositionRemuneration": [
            {"MinimumRange": "63312", "MaximumRange": "85658", "RateIntervalCode": "Per Year"}
        ],
        "JobCategory": [{"Name": "Recreation Specialist"}],
        "PositionSchedule": [{"Name": "Full-time"}],
        "PositionOfferingType": [{"Name": "Permanent"}],
        "UserArea": {
            "Details": {
                "MajorDuties": ["Design and deliver strength and conditioning programming."],
                "Education": "Bachelor's degree in exercise science or related field required.",
                "Requirements": "CSCS certification required.",
                "Evaluations": "",
                "Benefits": "",
                "OtherInformation": "",
                "AgencyMarketingStatement": "",
                "SecurityClearanceRequired": "Not Applicable",
                "TeleworkEligible": False,
                "TravelCode": "Not required",
                "PromotionPotential": "",
                "WhoMayApply": "United States Citizens",
                "DrugTestRequired": "No",
            }
        },
    }
    base.update(overrides)
    return base


def _item(**overrides):
    descriptor_overrides = overrides.pop("descriptor", {})
    return {
        "MatchedObjectId": overrides.pop("id", "123456700"),
        "MatchedObjectDescriptor": _descriptor(**descriptor_overrides),
        **overrides,
    }


def _page(items, total=None):
    return {"SearchResult": {"SearchResultItems": items, "SearchResultCount": len(items), **({"SearchResultCountAll": total} if total else {})}}


def _source(**options):
    opts = {"api_key": "test-key", "user_agent": "jeremy@socialsips.io", "max_pages": 1, **options}
    return USAJobsSource("federal", opts)


def test_requires_api_key_and_user_agent():
    with pytest.raises(KeyError):
        USAJobsSource("federal", {"user_agent": "x@example.com"}).fetch().__next__()
    with pytest.raises(KeyError):
        USAJobsSource("federal", {"api_key": "x"}).fetch().__next__()


def test_sends_the_documented_headers_and_params(monkeypatch):
    calls = []

    def fake_fetch_json(url, *, headers, params):
        calls.append((url, headers, params))
        return _page([])

    monkeypatch.setattr("tactical_jobs.sources.usajobs.fetch_json", fake_fetch_json)
    list(_source(keywords=["strength and conditioning"], max_pages=1).fetch())

    assert len(calls) == 1
    url, headers, params = calls[0]
    assert url == "https://data.usajobs.gov/api/search"
    assert headers["Authorization-Key"] == "test-key"
    assert headers["User-Agent"] == "jeremy@socialsips.io"
    assert headers["Host"] == "data.usajobs.gov"
    assert params["Keyword"] == "strength and conditioning"
    assert params["WhoMayApply"] == "All"


def test_default_keywords_cover_the_niche():
    assert "human performance" in DEFAULT_KEYWORDS
    assert "strength and conditioning" in DEFAULT_KEYWORDS
    assert "holistic health and fitness" in DEFAULT_KEYWORDS


def test_maps_the_core_fields(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page([_item()]),
    )
    postings = list(_source(keywords=["x"]).fetch())
    assert len(postings) == 1
    p = postings[0]
    assert p.title == "Strength and Conditioning Coach"
    assert p.url == "https://www.usajobs.gov/job/123456700"
    assert p.employer == "Department of the Army"
    assert p.department == "Department of Defense"
    assert p.location == "Fort Bragg, North Carolina"
    assert p.source_id == "123456700"
    assert p.source == "usajobs:federal"
    assert p.compensation == "$63312 - $85658 Per Year"
    assert not p.remote


def test_falls_back_to_department_when_organization_is_blank(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page([_item(descriptor={"OrganizationName": ""})]),
    )
    posting = next(iter(_source(keywords=["x"]).fetch()))
    assert posting.employer == "Department of Defense"


def test_falls_back_to_federal_government_when_both_are_blank(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page(
            [_item(descriptor={"OrganizationName": "", "DepartmentName": ""})]
        ),
    )
    posting = next(iter(_source(keywords=["x"]).fetch()))
    assert posting.employer == "U.S. Federal Government"


def test_description_pulls_in_every_narrative_block(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page([_item()]),
    )
    posting = next(iter(_source(keywords=["x"]).fetch()))
    assert "H2F program" in posting.description
    assert "strength and conditioning programming" in posting.description
    assert "exercise science" in posting.description
    assert "CSCS certification" in posting.description


def test_structured_facts_are_folded_into_the_description(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page(
            [
                _item(
                    descriptor={
                        "UserArea": {
                            "Details": {
                                "MajorDuties": [],
                                "Education": "",
                                "Requirements": "",
                                "Evaluations": "",
                                "Benefits": "",
                                "OtherInformation": "",
                                "AgencyMarketingStatement": "",
                                "SecurityClearanceRequired": "Secret",
                                "TeleworkEligible": False,
                                "TravelCode": "25% or less",
                                "PromotionPotential": "",
                                "WhoMayApply": "United States Citizens",
                                "DrugTestRequired": "Yes",
                            }
                        }
                    }
                )
            ]
        ),
    )
    posting = next(iter(_source(keywords=["x"]).fetch()))
    assert "Security clearance: Secret." in posting.description
    assert "Travel: 25% or less." in posting.description
    assert "Drug test required: Yes." in posting.description


def test_job_category_and_schedule_are_folded_in(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page([_item()]),
    )
    posting = next(iter(_source(keywords=["x"]).fetch()))
    assert "Job category: Recreation Specialist." in posting.description
    assert "Position schedule: Full-time." in posting.description
    assert "Offering type: Permanent." in posting.description


def test_telework_eligible_true_marks_the_posting_remote(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page(
            [_item(descriptor={"UserArea": {"Details": {"TeleworkEligible": True}}})]
        ),
    )
    posting = next(iter(_source(keywords=["x"]).fetch()))
    assert posting.remote is True


def test_missing_remuneration_leaves_compensation_none(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page([_item(descriptor={"PositionRemuneration": []})]),
    )
    posting = next(iter(_source(keywords=["x"]).fetch()))
    assert posting.compensation is None


def test_item_without_a_descriptor_is_skipped(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page([{"MatchedObjectId": "1"}, _item(id="2")]),
    )
    postings = list(_source(keywords=["x"]).fetch())
    assert [p.source_id for p in postings] == ["2"]


def test_dedupes_the_same_posting_across_keywords(monkeypatch):
    calls = {"n": 0}

    def fake_fetch_json(*a, **k):
        calls["n"] += 1
        return _page([_item()])

    monkeypatch.setattr("tactical_jobs.sources.usajobs.fetch_json", fake_fetch_json)
    postings = list(_source(keywords=["strength", "conditioning"], max_pages=1).fetch())
    assert calls["n"] == 2
    assert len(postings) == 1


def test_pagination_stops_on_a_short_page(monkeypatch):
    pages = [_page([_item(id=str(i)) for i in range(250)]), _page([_item(id="250")])]
    calls = {"n": 0}

    def fake_fetch_json(*a, **k):
        page = pages[calls["n"]]
        calls["n"] += 1
        return page

    monkeypatch.setattr("tactical_jobs.sources.usajobs.fetch_json", fake_fetch_json)
    postings = list(_source(keywords=["x"], max_pages=5, results_per_page=250).fetch())
    assert calls["n"] == 2
    assert len(postings) == 251


def test_pagination_respects_max_pages(monkeypatch):
    def fake_fetch_json(url, *, headers, params):
        page = params["Page"]
        offset = (page - 1) * 250
        return _page([_item(id=str(offset + i)) for i in range(250)])

    monkeypatch.setattr("tactical_jobs.sources.usajobs.fetch_json", fake_fetch_json)
    postings = list(_source(keywords=["x"], max_pages=2, results_per_page=250).fetch())
    assert len(postings) == 500


def test_empty_result_set_yields_nothing(monkeypatch):
    monkeypatch.setattr(
        "tactical_jobs.sources.usajobs.fetch_json",
        lambda *a, **k: _page([]),
    )
    assert list(_source(keywords=["obscure query"]).fetch()) == []
