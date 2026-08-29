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


# --------------------------------------------------------------------------
# regression: description fields that are not plain HTML strings
#
# Tenants emit ``jobDescription`` as a bare HTML string, as
# ``{"descriptor": "<p>..."}``, or as a list of HTML chunks. Handing a
# non-string to html_to_text raises, and a raising record used to be dropped
# outright -- losing the exact text this project exists to mine.
# --------------------------------------------------------------------------


def test_job_description_wrapped_in_a_descriptor_is_still_mined(monkeypatch):
    posting = _mapped(monkeypatch, {"jobDescription": {"descriptor": DESCRIPTION_HTML}})

    assert "H2F Performance Readiness Team" in posting.description
    assert "CSCS or TSAC-F required" in posting.description


def test_job_description_split_into_a_list_of_chunks_is_joined(monkeypatch):
    posting = _mapped(
        monkeypatch,
        {
            "jobDescription": [
                "<p>Embedded with 3rd Special Forces Group (THOR3).</p>",
                "<ul><li>TSAC-F preferred</li><li>TS/SCI clearance</li></ul>",
            ]
        },
    )

    assert "THOR3" in posting.description
    assert "TSAC-F preferred" in posting.description
    assert "TS/SCI clearance" in posting.description


def test_an_unusable_job_description_falls_back_instead_of_dropping_the_job(monkeypatch):
    posting = _mapped(monkeypatch, {"jobDescription": 12345})

    assert posting.source_id == "R-00123456", "the posting must survive"
    assert "Human Performance Coach" in posting.description


def test_description_is_plain_text_never_raw_markup(monkeypatch):
    posting = _mapped(
        monkeypatch,
        {"jobDescription": "<div>CSCS required</div><script>track();</script><style>a{}</style>"},
    )

    assert "CSCS required" in posting.description
    for markup in ("<div", "<script", "<style", "</div>"):
        assert markup not in posting.description
    assert "track()" not in posting.description


def test_unicode_survives_the_round_trip(monkeypatch):
    posting = _mapped(
        monkeypatch,
        {"jobDescription": "<p>Café — Fußball readiness – CSCS</p>"},
        {"title": "Coach — Fort Cavazos"},
    )

    assert "Café" in posting.description
    assert "Fußball" in posting.description
    assert posting.title == "Coach — Fort Cavazos"


# --------------------------------------------------------------------------
# regression: one flaky page must not cost the other search terms
# --------------------------------------------------------------------------


def test_a_failure_on_the_very_first_term_keeps_the_later_terms(monkeypatch):
    """A transient 503 on request #1 used to throw away every other search."""
    api = FakeAPI(
        {
            ("human performance", 0): FetchError("HTTP 503"),
            ("athletic trainer", 0): _page([_listing("/job/Good_R1")]),
        }
    )
    postings = _run(
        monkeypatch,
        api,
        {"search_terms": ["human performance", "athletic trainer"], "detail_limit": 0},
    )

    assert [posting.source_id for posting in postings] == ["/job/Good_R1"]


def test_every_term_failing_is_still_reported_as_an_error(monkeypatch):
    api = FakeAPI(
        {
            ("human performance", 0): FetchError("HTTP 503"),
            ("athletic trainer", 0): FetchError("HTTP 503"),
        }
    )
    with pytest.raises(FetchError):
        _run(
            monkeypatch,
            api,
            {"search_terms": ["human performance", "athletic trainer"]},
        )


def test_a_failure_with_no_results_anywhere_is_not_reported_as_success(monkeypatch):
    """Empty-but-healthy terms must not mask a broken tenant/site config."""
    api = FakeAPI(
        {
            ("human performance", 0): _page([]),
            ("athletic trainer", 0): FetchError("HTTP 404"),
        }
    )
    with pytest.raises(FetchError):
        _run(
            monkeypatch,
            api,
            {"search_terms": ["human performance", "athletic trainer"]},
        )


def test_max_pages_is_applied_per_search_term(monkeypatch):
    def endless(payload):
        term, start = payload["searchText"], payload["offset"]
        return _page(
            [_listing(f"/job/{term}{start + i}_R{start + i}") for i in range(payload["limit"])],
            total=1000,
        )

    api = FakeAPI(endless)
    postings = _run(
        monkeypatch,
        api,
        {"search_terms": ["alpha", "bravo"], "limit": 2, "max_pages": 2, "detail_limit": 0},
    )

    assert [(payload["searchText"], payload["offset"]) for _, payload in api.search_calls] == [
        ("alpha", 0),
        ("alpha", 2),
        ("bravo", 0),
        ("bravo", 2),
    ]
    assert len(postings) == 8


def test_a_non_list_job_postings_value_terminates_cleanly(monkeypatch):
    api = FakeAPI({("human performance", 0): {"total": 5, "jobPostings": "nope"}})
    postings = _run(monkeypatch, api)

    assert postings == []
    assert len(api.search_calls) == 1, "a junk page must not be paginated forever"


# --------------------------------------------------------------------------
# regression: option coercion. Config is hand-edited TOML; one bad value must
# degrade to the documented default, not abort the source.
# --------------------------------------------------------------------------


def test_junk_limit_falls_back_to_the_default_page_size(monkeypatch):
    api = FakeAPI({("human performance", 0): _page([_listing("/job/A_R1")])})
    postings = _run(monkeypatch, api, {"limit": None, "detail_limit": 0})

    assert api.search_calls[0][1]["limit"] == 20
    assert len(postings) == 1


def test_junk_max_pages_falls_back_to_the_default(monkeypatch):
    def endless(payload):
        start = payload["offset"]
        return _page(
            [_listing(f"/job/J{start + i}_R{start + i}") for i in range(payload["limit"])],
            total=1000,
        )

    api = FakeAPI(endless)
    _run(monkeypatch, api, {"limit": 2, "max_pages": "many", "detail_limit": 0})

    assert len(api.search_calls) == 5


def test_junk_detail_limit_falls_back_to_the_default(monkeypatch):
    listings = [_listing(f"/job/J{i}_R{i}") for i in range(60)]
    api = FakeAPI(
        {("human performance", 0): _page(listings)}, details=lambda url: _detail()
    )
    postings = _run(monkeypatch, api, {"limit": 60, "detail_limit": None})

    assert len(api.detail_calls) == 50
    assert len(postings) == 60


def test_default_detail_limit_is_fifty(monkeypatch):
    listings = [_listing(f"/job/J{i}_R{i}") for i in range(60)]
    api = FakeAPI(
        {("human performance", 0): _page(listings)}, details=lambda url: _detail()
    )
    _run(monkeypatch, api, {"limit": 60})

    assert len(api.detail_calls) == 50


def test_junk_delay_seconds_does_not_sleep(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr("tactical_jobs.sources.workday.time.sleep", lambda s: slept.append(s))
    api = FakeAPI(
        {("human performance", 0): _page([_listing("/job/A_R1")])},
        details=lambda url: _detail(),
    )
    postings = _run(monkeypatch, api, {"delay_seconds": "fast"})

    assert slept == []
    assert len(postings) == 1


def test_delay_is_skipped_before_the_first_request_and_applied_between_pages(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr("tactical_jobs.sources.workday.time.sleep", lambda s: slept.append(s))
    api = FakeAPI(
        {
            ("human performance", 0): _page([_listing("/job/A_R1")], total=3),
            ("human performance", 1): _page([_listing("/job/B_R2")], total=3),
            ("human performance", 2): _page([_listing("/job/C_R3")], total=3),
        }
    )
    _run(monkeypatch, api, {"limit": 1, "detail_limit": 0, "delay_seconds": 0.5})

    assert len(api.search_calls) == 3
    assert slept == [0.5, 0.5], "no pause before request one, one pause between each pair"


def test_default_data_center_is_wd1(monkeypatch):
    api = FakeAPI({("human performance", 0): _page([_listing("/job/A_R1")])})
    api.install(monkeypatch)
    posting = list(
        WorkdaySource(
            "kbr",
            {"tenant": "kbr", "site": "External", "search_terms": ["human performance"],
             "detail_limit": 0},
        ).fetch()
    )[0]

    assert posting.url == "https://kbr.wd1.myworkdayjobs.com/External/job/A_R1"


def test_none_entries_in_search_terms_are_dropped_not_searched_for(monkeypatch):
    api = FakeAPI({("wanted", 0): _page([_listing("/job/A_R1")])})
    postings = _run(
        monkeypatch, api, {"search_terms": [None, "wanted"], "detail_limit": 0}
    )

    assert [payload["searchText"] for _, payload in api.search_calls] == ["wanted"]
    assert len(postings) == 1


def test_repeated_search_terms_are_only_requested_once(monkeypatch):
    api = FakeAPI({("human performance", 0): _page([_listing("/job/A_R1")])})
    _run(
        monkeypatch,
        api,
        {"search_terms": ["human performance", "human performance"], "detail_limit": 0},
    )

    assert len(api.search_calls) == 1


def test_a_non_list_search_terms_value_falls_back_to_the_defaults(monkeypatch):
    api = FakeAPI({})
    api.install(monkeypatch)
    list(
        WorkdaySource(
            "leidos", {"tenant": "leidos", "site": "External", "search_terms": 7}
        ).fetch()
    )

    assert {payload["searchText"] for _, payload in api.search_calls} == set(
        DEFAULT_SEARCH_TERMS
    )


# --------------------------------------------------------------------------
# remaining mapping details
# --------------------------------------------------------------------------


def test_pay_range_with_numeric_values_is_rendered(monkeypatch):
    posting = _mapped(
        monkeypatch,
        {"payRange": {"minimum": {"value": 78000}, "maximum": {"value": 104000}}},
    )
    assert posting.compensation == "78000 - 104000"


def test_job_req_id_is_folded_into_the_description_text(monkeypatch):
    posting = _mapped(monkeypatch)
    assert "Job requisition id: R-00123456." in posting.description


def test_remote_is_false_when_nothing_indicates_remote(monkeypatch):
    posting = _mapped(monkeypatch)
    assert posting.remote is False


def test_a_bare_remote_additional_location_never_makes_an_onsite_job_remote():
    """KBR requisition R2128061, fetched live from its Workday CXS endpoint.

    Its own title is "Special Operations Physical Therapist-TEMP POSITION,
    (Onsite - Fort Bragg, NC)". Workday's remoteType is null. Yet
    additionalLocations carries ["Remote - U.S."], which the adapter used to
    concatenate onto the real location -- producing both a false Remote
    classification and a published location that was wrong about where the job
    is. All three of KBR's SOF postings on the board carried this boilerplate.
    """
    from tactical_jobs.sources.workday import _location

    info = {
        "location": "Fayetteville, North Carolina",
        "additionalLocations": ["Remote - U.S."],
        "remoteType": None,
    }
    assert _location({"locationsText": "2 Locations"}, info) == "Fayetteville, North Carolina"


def test_a_declared_remote_type_keeps_the_remote_location():
    from tactical_jobs.sources.workday import _location

    info = {
        "location": "Remote - U.S.",
        "additionalLocations": [],
        "remoteType": "Fully Remote",
    }
    assert _location({}, info) == "Remote - U.S."


def test_a_bare_remote_entry_survives_when_it_is_the_only_location():
    # Dropping it would leave the posting unplaceable, which is worse.
    from tactical_jobs.sources.workday import _location

    info = {"location": "Remote - U.S.", "additionalLocations": [], "remoteType": None}
    assert _location({}, info) == "Remote - U.S."


def test_bare_remote_detection_does_not_swallow_a_real_place():
    from tactical_jobs.sources.workday import _is_bare_remote_location

    for text in ("Remote - U.S.", "Remote", "Fully Remote", "Virtual", "Remote - USA"):
        assert _is_bare_remote_location(text), text
    for text in ("Remote, Texas", "Fort Bragg, NC", "Fayetteville, North Carolina"):
        assert not _is_bare_remote_location(text), text
