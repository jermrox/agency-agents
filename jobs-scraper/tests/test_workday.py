"""Workday adapter tests.

Everything here runs against captured payload shapes. There is no outbound
network in CI or the sandbox, so ``post_json``/``fetch_json`` are replaced as
imported into the adapter module and the assertions are about field mapping,
pagination, dedupe, and graceful degradation.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.http import FetchError  # noqa: E402
from tactical_jobs.sources.workday import (  # noqa: E402
    WORKDAY_SOURCES,
    DEFAULT_SEARCH_TERMS,
    WorkdaySource,
)

OPTIONS = {
    "tenant": "leidos",
    "site": "External",
    "data_center": "wd5",
    "employer": "Leidos",
    "search_terms": ["human performance"],
}

DESCRIPTION_HTML = (
    "<p>Serve on an H2F Performance Readiness Team at Fort Bragg.</p>"
    "<ul><li>CSCS or TSAC-F required</li>"
    "<li>Active Secret clearance required</li></ul>"
)


def _listing(path: str, title: str = "Human Performance Coach", **extra):
    record = {
        "title": title,
        "externalPath": path,
        "locationsText": "Fort Bragg, NC",
        "postedOn": "Posted 5 Days Ago",
        "bulletFields": ["R-00123456", "Full time"],
    }
    record.update(extra)
    return record


def _page(postings, total=None):
    return {
        "total": len(postings) if total is None else total,
        "jobPostings": list(postings),
    }


def _detail(**extra):
    info = {
        "title": "Human Performance Coach",
        "jobDescription": DESCRIPTION_HTML,
        "location": "Fort Bragg, NC",
        "startDate": "2026-07-01",
        "timeType": "Full time",
        "jobReqId": "R-00123456",
        "remoteType": "On-site",
    }
    info.update(extra)
    return {"jobPostingInfo": info}


class FakeAPI:
    """Stands in for the two Workday endpoints and records what was asked."""

    def __init__(self, pages=None, details=None, *, encode=True):
        # pages: dict keyed by (searchText, offset) -> payload, or a callable.
        self.pages = pages if pages is not None else {}
        self.details = details or {}
        self.encode = encode
        self.search_calls: list[tuple[str, dict]] = []
        self.detail_calls: list[str] = []

    def post_json(self, url, payload, **kwargs):
        self.search_calls.append((url, payload))
        if callable(self.pages):
            page = self.pages(payload)
        else:
            page = self.pages.get((payload["searchText"], payload["offset"]), _page([]))
        if isinstance(page, Exception):
            raise page
        return json.dumps(page).encode() if self.encode else page

    def fetch_json(self, url, **kwargs):
        self.detail_calls.append(url)
        detail = self.details(url) if callable(self.details) else self.details.get(url)
        if detail is None:
            raise FetchError(f"HTTP 404 for {url}")
        if isinstance(detail, Exception):
            raise detail
        return detail

    def install(self, monkeypatch):
        monkeypatch.setattr("tactical_jobs.sources.workday.post_json", self.post_json)
        monkeypatch.setattr("tactical_jobs.sources.workday.fetch_json", self.fetch_json)
        return self


def _run(monkeypatch, api, options=None, name="leidos"):
    api.install(monkeypatch)
    merged = {**OPTIONS, **(options or {})}
    return list(WorkdaySource(name, merged).fetch())


# --------------------------------------------------------------------------
# search request shape and URL construction
# --------------------------------------------------------------------------


def test_posts_the_workday_search_payload_to_the_cxs_endpoint(monkeypatch):
    api = FakeAPI({("human performance", 0): _page([_listing("/job/Fort-Bragg/Coach_R1")])},
                  {"https://leidos.wd5.myworkdayjobs.com/wday/cxs/leidos/External/job/Fort-Bragg/Coach_R1": _detail()})
    _run(monkeypatch, api)

    url, payload = api.search_calls[0]
    assert url == "https://leidos.wd5.myworkdayjobs.com/wday/cxs/leidos/External/jobs"
    assert payload == {
        "appliedFacets": {},
        "limit": 20,
        "offset": 0,
        "searchText": "human performance",
    }


def test_builds_the_human_facing_url_not_the_api_path(monkeypatch):
    path = "/job/Fort-Bragg-NC/Human-Performance-Coach_R-00123456"
    api = FakeAPI(
        {("human performance", 0): _page([_listing(path)])},
        {f"https://leidos.wd5.myworkdayjobs.com/wday/cxs/leidos/External{path}": _detail()},
    )
    posting = _run(monkeypatch, api)[0]

    assert posting.url == f"https://leidos.wd5.myworkdayjobs.com/External{path}"
    assert "/wday/cxs/" not in posting.url
    # The detail request, by contrast, must use the API path.
    assert "/wday/cxs/leidos/External" in api.detail_calls[0]


def test_data_center_option_selects_the_host(monkeypatch):
    api = FakeAPI({("human performance", 0): _page([_listing("/job/A_R1")])})
    posting = _run(monkeypatch, api, {"data_center": "wd1"})[0]
    assert posting.url.startswith("https://leidos.wd1.myworkdayjobs.com/External/")


def test_external_path_without_a_leading_slash_is_normalized(monkeypatch):
    api = FakeAPI({("human performance", 0): _page([_listing("job/A_R1")])})
    posting = _run(monkeypatch, api)[0]
    assert posting.url == "https://leidos.wd5.myworkdayjobs.com/External/job/A_R1"


# --------------------------------------------------------------------------
# pagination
# --------------------------------------------------------------------------


def test_paginates_with_offset_until_total_is_reached(monkeypatch):
    api = FakeAPI(
        {
            ("human performance", 0): _page(
                [_listing("/job/A_R1"), _listing("/job/B_R2")], total=5
            ),
            ("human performance", 2): _page(
                [_listing("/job/C_R3"), _listing("/job/D_R4")], total=5
            ),
            ("human performance", 4): _page([_listing("/job/E_R5")], total=5),
        }
    )
    postings = _run(monkeypatch, api, {"limit": 2, "detail_limit": 0})

    assert [payload["offset"] for _, payload in api.search_calls] == [0, 2, 4]
    assert len(postings) == 5


def test_pagination_stops_at_max_pages(monkeypatch):
    def endless(payload):
        start = payload["offset"]
        return _page(
            [_listing(f"/job/J{start + i}_R{start + i}") for i in range(payload["limit"])],
            total=1000,
        )

    api = FakeAPI(endless)
    postings = _run(monkeypatch, api, {"limit": 2, "max_pages": 3, "detail_limit": 0})

    assert len(api.search_calls) == 3
    assert len(postings) == 6


def test_pagination_stops_on_a_short_page(monkeypatch):
    api = FakeAPI(
        {
            # total lies (says more exist) but the page came back short.
            ("human performance", 0): _page([_listing("/job/A_R1")], total=99),
        }
    )
    postings = _run(monkeypatch, api, {"limit": 20, "detail_limit": 0})

    assert len(api.search_calls) == 1
    assert len(postings) == 1


def test_pagination_without_a_total_still_terminates(monkeypatch):
    """Some tenants omit ``total``; max_pages has to be the backstop."""

    def endless(payload):
        start = payload["offset"]
        return {
            "jobPostings": [
                _listing(f"/job/J{start + i}_R{start + i}") for i in range(payload["limit"])
            ]
        }

    api = FakeAPI(endless)
    postings = _run(monkeypatch, api, {"limit": 2, "max_pages": 4, "detail_limit": 0})

    assert len(api.search_calls) == 4
    assert len(postings) == 8


def test_empty_response_yields_nothing(monkeypatch):
    api = FakeAPI({("human performance", 0): _page([])})
    assert _run(monkeypatch, api) == []
    assert api.detail_calls == []


# --------------------------------------------------------------------------
# dedupe across search terms
# --------------------------------------------------------------------------


def test_dedupes_by_external_path_across_search_terms(monkeypatch):
    shared = _listing("/job/Fort-Bragg/Coach_R1")
    api = FakeAPI(
        {
            ("human performance", 0): _page([shared, _listing("/job/Only-HP_R2")]),
            ("strength and conditioning", 0): _page(
                [shared, _listing("/job/Only-SC_R3")]
            ),
        }
    )
    postings = _run(
        monkeypatch,
        api,
        {
            "search_terms": ["human performance", "strength and conditioning"],
            "detail_limit": 0,
        },
    )

    paths = [posting.source_id for posting in postings]
    assert paths == ["/job/Fort-Bragg/Coach_R1", "/job/Only-HP_R2", "/job/Only-SC_R3"]
    # The duplicate must not cost a second detail request either.
    assert len(paths) == len(set(paths))


def test_dedupe_happens_before_detail_fetches(monkeypatch):
    shared = _listing("/job/Shared_R1")
    api = FakeAPI(
        {
            ("human performance", 0): _page([shared]),
            ("athletic trainer", 0): _page([shared]),
        },
        details=lambda url: _detail(),
    )
    postings = _run(
        monkeypatch, api, {"search_terms": ["human performance", "athletic trainer"]}
    )

    assert len(postings) == 1
    assert len(api.detail_calls) == 1


# --------------------------------------------------------------------------
# detail enrichment
# --------------------------------------------------------------------------


def test_detail_fetch_supplies_the_full_description(monkeypatch):
    path = "/job/Fort-Bragg/Coach_R1"
    api = FakeAPI(
        {("human performance", 0): _page([_listing(path)])},
        {f"https://leidos.wd5.myworkdayjobs.com/wday/cxs/leidos/External{path}": _detail()},
    )
    posting = _run(monkeypatch, api)[0]

    assert "H2F Performance Readiness Team" in posting.description
    assert "CSCS or TSAC-F required" in posting.description
    assert "Secret clearance" in posting.description
    # Block tags became separators rather than gluing words together.
    assert "requiredActive" not in posting.description
    # Structured facts are folded in for the enrichment layer.
    assert "Time type: Full time." in posting.description


def test_detail_failure_falls_back_to_list_fields(monkeypatch):
    api = FakeAPI(
        {("human performance", 0): _page([_listing("/job/A_R1")])},
        details={},  # every detail lookup 404s
    )
    postings = _run(monkeypatch, api)

    assert len(postings) == 1, "a dead detail page must not drop the posting"
    posting = postings[0]
    assert posting.title == "Human Performance Coach"
    assert posting.location == "Fort Bragg, NC"
    assert "Human Performance Coach" in posting.description
    assert "R-00123456" in posting.description  # bulletFields kept as signal
    assert posting.source_id == "/job/A_R1"


def test_detail_limit_bounds_the_detail_fanout(monkeypatch):
    listings = [_listing(f"/job/J{i}_R{i}") for i in range(10)]
    api = FakeAPI(
        {("human performance", 0): _page(listings)},
        details=lambda url: _detail(),
    )
    postings = _run(monkeypatch, api, {"limit": 10, "detail_limit": 3})

    assert len(api.detail_calls) == 3
    assert len(postings) == 10, "postings past the detail budget are still yielded"
    assert "H2F Performance Readiness Team" in postings[0].description
    assert "H2F Performance Readiness Team" not in postings[9].description


# --------------------------------------------------------------------------
# field mapping
# --------------------------------------------------------------------------


def _mapped(monkeypatch, detail_extra=None, listing_extra=None):
    path = "/job/A_R1"
    api = FakeAPI(
        {("human performance", 0): _page([_listing(path, **(listing_extra or {}))])},
        {
            f"https://leidos.wd5.myworkdayjobs.com/wday/cxs/leidos/External{path}": _detail(
                **(detail_extra or {})
            )
        },
    )
    return _run(monkeypatch, api)[0]


def test_source_label_and_employer(monkeypatch):
    posting = _mapped(monkeypatch)
    assert posting.source == "workday:leidos"
    assert posting.employer == "Leidos"


def test_employer_defaults_to_the_tenant(monkeypatch):
    api = FakeAPI({("human performance", 0): _page([_listing("/job/A_R1")])})
    api.install(monkeypatch)
    posting = list(
        WorkdaySource(
            "prime",
            {"tenant": "amentum", "site": "External", "search_terms": ["human performance"]},
        ).fetch()
    )[0]
    assert posting.employer == "amentum"


def test_source_id_prefers_job_req_id(monkeypatch):
    posting = _mapped(monkeypatch)
    assert posting.source_id == "R-00123456"


def test_source_id_falls_back_to_external_path(monkeypatch):
    posting = _mapped(monkeypatch, {"jobReqId": ""})
    assert posting.source_id == "/job/A_R1"


def test_posted_at_prefers_start_date_over_the_human_postedon_string(monkeypatch):
    posting = _mapped(monkeypatch)
    assert posting.posted_at is not None
    assert (posting.posted_at.year, posting.posted_at.month, posting.posted_at.day) == (
        2026,
        7,
        1,
    )


def test_unparseable_posted_on_leaves_posted_at_empty(monkeypatch):
    posting = _mapped(monkeypatch, {"startDate": None})
    assert posting.posted_at is None


def test_remote_type_sets_the_remote_flag(monkeypatch):
    assert _mapped(monkeypatch, {"remoteType": "Remote"}).remote is True
    assert _mapped(monkeypatch, {"remoteType": "On-site"}).remote is False


def test_remote_flag_reads_a_remote_location_too(monkeypatch):
    posting = _mapped(monkeypatch, {"location": "Remote - United States"})
    assert posting.remote is True


def test_detail_location_wins_over_the_list_display_text(monkeypatch):
    posting = _mapped(
        monkeypatch,
        {"location": "Fort Liberty, NC", "additionalLocations": ["Camp Lejeune, NC"]},
        {"locationsText": "2 Locations"},
    )
    assert posting.location == "Fort Liberty, NC; Camp Lejeune, NC"


def test_compensation_from_a_structured_pay_range(monkeypatch):
    posting = _mapped(
        monkeypatch,
        {"payRange": {"minimum": "$78,000", "maximum": "$104,000", "frequency": "Annually"}},
    )
    assert posting.compensation == "$78,000 - $104,000 Annually"


def test_department_from_job_family_group_descriptor(monkeypatch):
    posting = _mapped(monkeypatch, {"jobFamilyGroup": {"descriptor": "Health Services"}})
    assert posting.department == "Health Services"


def test_department_is_none_when_absent(monkeypatch):
    assert _mapped(monkeypatch).department is None


def test_raw_keeps_both_payloads_for_debugging(monkeypatch):
    posting = _mapped(monkeypatch)
    assert posting.raw["jobPosting"]["externalPath"] == "/job/A_R1"
    assert posting.raw["jobPostingInfo"]["jobReqId"] == "R-00123456"


# --------------------------------------------------------------------------
# malformed input and failure handling
# --------------------------------------------------------------------------


def test_malformed_records_are_skipped_not_fatal(monkeypatch):
    api = FakeAPI(
        {
            ("human performance", 0): _page(
                [
                    "not-a-dict",
                    {"title": "No path here"},
                    {"externalPath": "", "title": "Empty path"},
                    _listing("/job/Good_R1"),
                ]
            )
        }
    )
    postings = _run(monkeypatch, api, {"detail_limit": 0})

    assert len(postings) == 1
    assert postings[0].source_id == "/job/Good_R1"


def test_a_first_page_failure_is_reported_rather_than_silently_empty(monkeypatch):
    api = FakeAPI({("human performance", 0): FetchError("HTTP 503")})
    with pytest.raises(FetchError):
        _run(monkeypatch, api)


def test_a_later_page_failure_keeps_what_was_already_collected(monkeypatch):
    api = FakeAPI(
        {
            ("human performance", 0): _page([_listing("/job/A_R1")], total=99),
            ("human performance", 1): FetchError("HTTP 503"),
        }
    )
    postings = _run(monkeypatch, api, {"limit": 1, "detail_limit": 0})

    assert [posting.source_id for posting in postings] == ["/job/A_R1"]


def test_one_failing_search_term_does_not_lose_the_others(monkeypatch):
    api = FakeAPI(
        {
            ("human performance", 0): _page([_listing("/job/A_R1")]),
            ("athletic trainer", 0): FetchError("HTTP 500"),
            ("physical therapist", 0): _page([_listing("/job/B_R2")]),
        }
    )
    postings = _run(
        monkeypatch,
        api,
        {
            "search_terms": ["human performance", "athletic trainer", "physical therapist"],
            "detail_limit": 0,
        },
    )
    assert [posting.source_id for posting in postings] == ["/job/A_R1", "/job/B_R2"]


def test_non_json_search_body_raises_a_fetch_error(monkeypatch):
    def broken_post(url, payload, **kwargs):
        return b"<html>Access Denied</html>"

    monkeypatch.setattr("tactical_jobs.sources.workday.post_json", broken_post)
    with pytest.raises(FetchError):
        list(WorkdaySource("leidos", OPTIONS).fetch())


def test_an_already_parsed_search_body_is_accepted(monkeypatch):
    api = FakeAPI(
        {("human performance", 0): _page([_listing("/job/A_R1")])}, encode=False
    )
    postings = _run(monkeypatch, api, {"detail_limit": 0})
    assert len(postings) == 1


def test_a_detail_payload_without_job_posting_info_degrades(monkeypatch):
    path = "/job/A_R1"
    api = FakeAPI(
        {("human performance", 0): _page([_listing(path)])},
        {f"https://leidos.wd5.myworkdayjobs.com/wday/cxs/leidos/External{path}": {}},
    )
    posting = _run(monkeypatch, api)[0]
    assert posting.source_id == path
    assert "Human Performance Coach" in posting.description


# --------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------


def test_tenant_is_required():
    with pytest.raises(KeyError):
        list(WorkdaySource("x", {"site": "External"}).fetch())


def test_site_is_required():
    with pytest.raises(KeyError):
        list(WorkdaySource("x", {"tenant": "leidos"}).fetch())


def test_default_search_terms_cover_the_tactical_disciplines(monkeypatch):
    api = FakeAPI({})
    api.install(monkeypatch)
    list(WorkdaySource("leidos", {"tenant": "leidos", "site": "External"}).fetch())

    searched = {payload["searchText"] for _, payload in api.search_calls}
    assert searched == set(DEFAULT_SEARCH_TERMS)
    assert "strength and conditioning" in searched
    assert "holistic health and fitness" in searched


def test_an_explicitly_empty_search_terms_list_pulls_the_whole_board(monkeypatch):
    api = FakeAPI({("", 0): _page([_listing("/job/A_R1")])})
    postings = _run(monkeypatch, api, {"search_terms": [], "detail_limit": 0})

    assert [payload["searchText"] for _, payload in api.search_calls] == [""]
    assert len(postings) == 1


def test_a_string_search_term_is_accepted(monkeypatch):
    api = FakeAPI({("cognitive performance", 0): _page([_listing("/job/A_R1")])})
    postings = _run(
        monkeypatch, api, {"search_terms": "cognitive performance", "detail_limit": 0}
    )
    assert len(postings) == 1


def test_delay_seconds_throttles_requests(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr("tactical_jobs.sources.workday.time.sleep", lambda s: slept.append(s))
    api = FakeAPI(
        {("human performance", 0): _page([_listing("/job/A_R1")])},
        details=lambda url: _detail(),
    )
    _run(monkeypatch, api, {"delay_seconds": 0.25})

    assert slept and all(pause == 0.25 for pause in slept)


def test_kind_and_export_tuple():
    assert WorkdaySource.kind == "workday"
    assert WORKDAY_SOURCES == (WorkdaySource,)
