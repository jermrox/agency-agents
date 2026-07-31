"""Tests for the configurable agency-board and sitemap-discovery adapters.

There is no outbound network in the sandbox or in CI, so every transport
symbol is replaced *as imported into the adapter module* and the assertions
are about the mapping: which path produced which JobPosting field, which
request was made, and what happens when a board answers with junk.

The payload shapes are the ones federal and NAF-style boards actually use --
records under a wrapper key, a link that is a site-root path, a teaser
description with the real text behind a second request, and page-numbered
pagination.
"""

from __future__ import annotations

import gzip
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.http import FetchError  # noqa: E402
from tactical_jobs.models import JobPosting  # noqa: E402
from tactical_jobs.sources.agencies import (  # noqa: E402
    AGENCY_SOURCES,
    AgencyBoardSource,
    SitemapJobsSource,
    deslugify,
    resolve_path,
)
from tactical_jobs.sources.base import Source  # noqa: E402

LIST_URL = "https://careers.example.gov/api/vacancies"
SITEMAP_URL = "https://careers.example.gov/sitemap.xml"


@pytest.fixture(autouse=True)
def block_the_network(monkeypatch):
    """No test may reach the network, including by accident.

    Replacing all three transport symbols by default means an unpatched call
    names itself instead of failing as a timeout somewhere unrelated.
    """

    def blocked(*args, **kwargs):
        raise AssertionError(
            "test reached the network; monkeypatch fetch/fetch_json/post_json "
            "as imported into tactical_jobs.sources.agencies"
        )

    monkeypatch.setattr("tactical_jobs.sources.agencies.fetch", blocked)
    monkeypatch.setattr("tactical_jobs.sources.agencies.fetch_json", blocked)
    monkeypatch.setattr("tactical_jobs.sources.agencies.post_json", blocked)


# ---------------------------------------------------------------------------
# fakes
# ---------------------------------------------------------------------------


def install_json(monkeypatch, responder, *, calls=None):
    """Replace ``fetch_json`` with ``responder(url, params, headers)``."""

    def fake_fetch_json(url, **kwargs):
        if calls is not None:
            calls.append({"url": url, **kwargs})
        return responder(url, kwargs.get("params"), kwargs.get("headers"))

    monkeypatch.setattr("tactical_jobs.sources.agencies.fetch_json", fake_fetch_json)


def install_post(monkeypatch, responder, *, calls=None):
    """Replace ``post_json`` with ``responder(url, payload)``, returning bytes."""

    def fake_post_json(url, payload, **kwargs):
        if calls is not None:
            calls.append({"url": url, "payload": payload, **kwargs})
        return responder(url, payload)

    monkeypatch.setattr("tactical_jobs.sources.agencies.post_json", fake_post_json)


def install_fetch(monkeypatch, documents, *, calls=None):
    """Replace ``fetch`` with a lookup over captured sitemap documents."""

    def fake_fetch(url, **kwargs):
        if calls is not None:
            calls.append(url)
        try:
            body = documents[url]
        except KeyError:
            raise FetchError(f"HTTP 404 for {url}") from None
        if isinstance(body, Exception):
            raise body
        return body if isinstance(body, (bytes, bytearray)) else str(body).encode()

    monkeypatch.setattr("tactical_jobs.sources.agencies.fetch", fake_fetch)


def static(payload):
    """A responder that answers every request with the same payload."""

    def responder(url, params=None, headers=None):
        return payload

    return responder


# ---------------------------------------------------------------------------
# captured payload shapes
# ---------------------------------------------------------------------------

LONG_TEXT = (
    "The installation Fitness, Sports and Aquatics program is hiring a "
    "strength and conditioning coach to deliver Holistic Health and Fitness "
    "programming to assigned units. CSCS or TSAC-F required. Candidates must "
    "be able to obtain a Secret clearance and pass a physical ability test. "
    "Duties include athlete monitoring, return-to-duty progressions, and "
    "coordination with the embedded athletic trainer and performance "
    "dietitian at the military treatment facility."
)

BOARD_PAYLOAD = {
    "meta": {"totalPages": 1},
    "data": {
        "results": [
            {
                "vacancyId": "NAF-2026-118",
                "position": {"title": "Tactical Strength and Conditioning Coach"},
                "links": {"detail": "/vacancy/NAF-2026-118"},
                "location": {"display": "Fort Bragg, NC"},
                "organization": {"name": "Army MWR"},
                "openDate": "2026-07-14T00:00:00Z",
                "payPlan": {"display": "NF-04 $62,000 - $78,000 per year"},
                "series": "0030 Sports Specialist",
                "schedule": "Full Time",
                "summary": "<p>Deliver H2F programming.</p>",
                "qualifications": "<ul><li>CSCS required</li><li>Secret clearance</li></ul>",
            }
        ]
    },
}


# ---------------------------------------------------------------------------
# dot-path resolver
# ---------------------------------------------------------------------------


def test_resolve_path_empty_path_returns_payload():
    payload = {"jobs": [1, 2]}
    assert resolve_path(payload, "") is payload
    assert resolve_path(payload, None) is payload
    assert resolve_path(payload, "   ") is payload


def test_resolve_path_walks_nested_keys():
    payload = {"data": {"results": {"title": "Athletic Trainer"}}}
    assert resolve_path(payload, "data.results.title") == "Athletic Trainer"


def test_resolve_path_missing_intermediate_key_returns_none():
    payload = {"data": {"results": []}}
    assert resolve_path(payload, "data.missing.title") is None
    assert resolve_path(payload, "nothing.at.all.here") is None


def test_resolve_path_missing_final_key_returns_none():
    assert resolve_path({"a": {"b": 1}}, "a.c") is None


def test_resolve_path_indexes_lists():
    payload = {"jobs": [{"title": "first"}, {"title": "second"}]}
    assert resolve_path(payload, "jobs.0.title") == "first"
    assert resolve_path(payload, "jobs.1.title") == "second"
    assert resolve_path(payload, "jobs.-1.title") == "second"


def test_resolve_path_out_of_range_index_returns_none():
    assert resolve_path({"jobs": [{"title": "only"}]}, "jobs.7.title") is None


def test_resolve_path_non_numeric_segment_on_a_list_returns_none():
    assert resolve_path({"jobs": [{"title": "x"}]}, "jobs.title") is None


def test_resolve_path_into_a_scalar_returns_none():
    assert resolve_path({"title": "Coach"}, "title.name") is None


def test_resolve_path_maps_over_a_list():
    payload = {"sections": [{"body": "one"}, {"body": "two"}, {"other": "skip"}]}
    assert resolve_path(payload, "sections.[].body") == ["one", "two"]


def test_resolve_path_bracket_syntax_matches_dotted_syntax():
    payload = {"sections": [{"body": "one"}, {"body": "two"}]}
    assert resolve_path(payload, "sections[].body") == resolve_path(
        payload, "sections.[].body"
    )


def test_resolve_path_trailing_map_returns_the_list_itself():
    payload = {"tags": ["h2f", "thor3"]}
    assert resolve_path(payload, "tags.[]") == ["h2f", "thor3"]


def test_resolve_path_map_over_a_non_list_returns_none():
    assert resolve_path({"sections": {"body": "one"}}, "sections.[].body") is None


def test_resolve_path_nested_maps_flatten_one_level():
    payload = {"groups": [{"items": [{"t": "a"}, {"t": "b"}]}, {"items": [{"t": "c"}]}]}
    assert resolve_path(payload, "groups[].items[].t") == ["a", "b", "c"]


# ---------------------------------------------------------------------------
# AgencyBoardSource -- configuration guards
# ---------------------------------------------------------------------------


def test_missing_url_option_is_reported():
    source = AgencyBoardSource("naf", {"field_map": {"title": "t", "url": "u"}})
    with pytest.raises(KeyError, match="requires option 'url'"):
        list(source.fetch())


def test_missing_field_map_is_reported():
    source = AgencyBoardSource("naf", {"url": LIST_URL})
    with pytest.raises(KeyError, match="requires option 'field_map'"):
        list(source.fetch())


def test_field_map_without_title_is_rejected():
    source = AgencyBoardSource("naf", {"url": LIST_URL, "field_map": {"url": "links.detail"}})
    with pytest.raises(KeyError, match="field_map key 'title'"):
        list(source.fetch())


def test_field_map_without_url_is_rejected():
    source = AgencyBoardSource("naf", {"url": LIST_URL, "field_map": {"title": "position.title"}})
    with pytest.raises(KeyError, match="field_map key 'url'"):
        list(source.fetch())


def test_field_map_that_is_not_a_table_is_rejected():
    source = AgencyBoardSource("naf", {"url": LIST_URL, "field_map": ["title", "url"]})
    with pytest.raises(TypeError, match="field_map to be a table"):
        list(source.fetch())


# ---------------------------------------------------------------------------
# AgencyBoardSource -- GET mapping
# ---------------------------------------------------------------------------


def _board(**overrides):
    options = {
        "url": LIST_URL,
        "records_path": "data.results",
        "base_url": "https://careers.example.gov",
        "employer": "Army MWR",
        "field_map": {
            "title": "position.title",
            "url": "links.detail",
            "source_id": "vacancyId",
            "location": "location.display",
            "employer": "organization.name",
            "posted_at": "openDate",
            "compensation": "payPlan.display",
            "department": "series",
            "job_type": "schedule",
            "description": ["summary", "qualifications"],
        },
    }
    options.update(overrides)
    return options


def test_get_mode_maps_every_configured_field(monkeypatch):
    calls: list[dict] = []
    install_json(monkeypatch, static(BOARD_PAYLOAD), calls=calls)

    postings = list(AgencyBoardSource("naf", _board()).fetch())

    assert len(postings) == 1
    job = postings[0]
    assert isinstance(job, JobPosting)
    assert job.source == "agencyboard:naf"
    assert job.source_id == "NAF-2026-118"
    assert job.title == "Tactical Strength and Conditioning Coach"
    assert job.employer == "Army MWR"
    assert job.location == "Fort Bragg, NC"
    assert job.department == "0030 Sports Specialist"
    assert job.compensation == "NF-04 $62,000 - $78,000 per year"
    assert job.posted_at is not None and job.posted_at.year == 2026
    assert job.remote is False
    assert calls[0]["url"] == LIST_URL
    assert job.raw["listing"]["vacancyId"] == "NAF-2026-118"


def test_description_concatenates_every_configured_path(monkeypatch):
    install_json(monkeypatch, static(BOARD_PAYLOAD))

    job = list(AgencyBoardSource("naf", _board()).fetch())[0]

    # Both mapped paths survive, and the HTML is flattened to text.
    assert "Deliver H2F programming." in job.description
    assert "CSCS required" in job.description
    assert "<li>" not in job.description


def test_structured_facts_are_folded_into_the_description(monkeypatch):
    install_json(monkeypatch, static(BOARD_PAYLOAD))

    job = list(AgencyBoardSource("naf", _board()).fetch())[0]

    assert "Job type: Full Time." in job.description
    assert "Salary: NF-04 $62,000 - $78,000 per year." in job.description
    assert "Department: 0030 Sports Specialist." in job.description


def test_field_map_list_takes_the_first_non_empty_path(monkeypatch):
    payload = {"results": [{"title": "Athletic Trainer", "href": "/job/1", "city": "", "site": "Fort Carson, CO"}]}
    install_json(monkeypatch, static(payload))

    options = _board(
        records_path="results",
        field_map={
            "title": "title",
            "url": "href",
            "location": ["city", "site"],
        },
    )
    job = list(AgencyBoardSource("naf", options).fetch())[0]

    assert job.location == "Fort Carson, CO"


def test_mapped_list_values_are_flattened(monkeypatch):
    payload = {
        "results": [
            {
                "title": "Performance Dietitian",
                "href": "/job/2",
                "sites": [{"name": "Fort Bragg, NC"}, {"name": "Camp Lejeune, NC"}],
                "sections": [{"body": "Feed the force."}, {"body": "RD required."}],
            }
        ]
    }
    install_json(monkeypatch, static(payload))

    options = _board(
        records_path="results",
        field_map={
            "title": "title",
            "url": "href",
            "location": "sites[].name",
            "description": "sections[].body",
        },
    )
    job = list(AgencyBoardSource("naf", options).fetch())[0]

    assert job.location == "Fort Bragg, NC, Camp Lejeune, NC"
    assert "Feed the force." in job.description
    assert "RD required." in job.description


def test_relative_url_joins_against_base_url(monkeypatch):
    install_json(monkeypatch, static(BOARD_PAYLOAD))

    job = list(AgencyBoardSource("naf", _board()).fetch())[0]

    assert job.url == "https://careers.example.gov/vacancy/NAF-2026-118"


def test_relative_url_falls_back_to_the_request_url(monkeypatch):
    install_json(monkeypatch, static(BOARD_PAYLOAD))

    options = _board()
    options.pop("base_url")
    job = list(AgencyBoardSource("naf", options).fetch())[0]

    # No base_url configured, so the endpoint itself is the base.
    assert job.url == "https://careers.example.gov/vacancy/NAF-2026-118"


def test_absolute_and_protocol_relative_urls_are_preserved(monkeypatch):
    payload = {
        "results": [
            {"title": "A", "href": "https://other.example.gov/job/1"},
            {"title": "B", "href": "//other.example.gov/job/2"},
        ]
    }
    install_json(monkeypatch, static(payload))

    options = _board(records_path="results", field_map={"title": "title", "url": "href"})
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert [job.url for job in postings] == [
        "https://other.example.gov/job/1",
        "https://other.example.gov/job/2",
    ]


def test_records_without_a_title_or_url_are_skipped(monkeypatch):
    payload = {
        "results": [
            {"title": "", "href": "/job/1"},
            {"title": "Athletic Trainer", "href": ""},
            {"title": "Exercise Physiologist", "href": "/job/3"},
            "a bare string the board should not have sent",
        ]
    }
    install_json(monkeypatch, static(payload))

    options = _board(records_path="results", field_map={"title": "title", "url": "href"})
    postings = list(AgencyBoardSource("naf", options).fetch())

    # One bad record never costs the rest of the board.
    assert [job.title for job in postings] == ["Exercise Physiologist"]


def test_root_array_response_needs_no_records_path(monkeypatch):
    install_json(monkeypatch, static([{"title": "Coach", "href": "/job/9"}]))

    options = _board(records_path="", field_map={"title": "title", "url": "href"})
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert [job.title for job in postings] == ["Coach"]


def test_single_object_response_is_read_as_one_record(monkeypatch):
    install_json(monkeypatch, static({"job": {"title": "Coach", "href": "/job/9"}}))

    options = _board(records_path="job", field_map={"title": "title", "url": "href"})
    assert len(list(AgencyBoardSource("naf", options).fetch())) == 1


def test_records_path_that_does_not_resolve_yields_nothing(monkeypatch):
    install_json(monkeypatch, static({"data": {"results": "not a list"}}))

    options = _board(field_map={"title": "title", "url": "href"})
    assert list(AgencyBoardSource("naf", options).fetch()) == []


def test_remote_flag_comes_from_the_field_map_when_mapped(monkeypatch):
    payload = {"results": [{"title": "Coach", "href": "/job/1", "telework": "Yes"}]}
    install_json(monkeypatch, static(payload))

    options = _board(
        records_path="results",
        field_map={"title": "title", "url": "href", "remote": "telework"},
    )
    assert list(AgencyBoardSource("naf", options).fetch())[0].remote is True


def test_remote_falls_back_to_the_location_heuristic(monkeypatch):
    payload = {"results": [{"title": "Coach", "href": "/job/1", "where": "Remote (CONUS)"}]}
    install_json(monkeypatch, static(payload))

    options = _board(
        records_path="results",
        field_map={"title": "title", "url": "href", "location": "where"},
    )
    assert list(AgencyBoardSource("naf", options).fetch())[0].remote is True


# ---------------------------------------------------------------------------
# AgencyBoardSource -- POST mode
# ---------------------------------------------------------------------------


def test_post_mode_sends_the_configured_json_body(monkeypatch):
    calls: list[dict] = []
    install_post(monkeypatch, lambda url, payload: b'{"results": [{"t": "Coach", "u": "/job/1"}]}', calls=calls)

    options = _board(
        method="POST",
        json_body={"appliedFacets": {}, "limit": 20},
        records_path="results",
        field_map={"title": "t", "url": "u"},
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert [job.title for job in postings] == ["Coach"]
    assert calls[0]["url"] == LIST_URL
    assert calls[0]["payload"] == {"appliedFacets": {}, "limit": 20}
    assert calls[0]["headers"]["Accept"] == "application/json"


def test_post_mode_accepts_an_already_parsed_body(monkeypatch):
    install_post(monkeypatch, lambda url, payload: {"results": [{"t": "Coach", "u": "/job/1"}]})

    options = _board(method="post", records_path="results", field_map={"title": "t", "url": "u"})
    assert len(list(AgencyBoardSource("naf", options).fetch())) == 1


def test_post_mode_non_json_body_raises(monkeypatch):
    install_post(monkeypatch, lambda url, payload: b"<html>login wall</html>")

    options = _board(method="POST", records_path="results", field_map={"title": "t", "url": "u"})
    with pytest.raises(FetchError):
        list(AgencyBoardSource("naf", options).fetch())


def test_post_mode_paginates_through_the_body(monkeypatch):
    calls: list[dict] = []

    def responder(url, payload):
        page = payload["offset"]
        if page >= 40:
            return {"results": []}
        return {"results": [{"t": f"Coach {page}", "u": f"/job/{page}"}]}

    install_post(monkeypatch, responder, calls=calls)

    options = _board(
        method="POST",
        json_body={"limit": 20},
        records_path="results",
        field_map={"title": "t", "url": "u"},
        page_param="offset",
        page_start=0,
        page_step=20,
        max_pages=5,
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert [job.title for job in postings] == ["Coach 0", "Coach 20"]
    assert [call["payload"]["offset"] for call in calls] == [0, 20, 40]
    # The configured body is never mutated across pages.
    assert options["json_body"] == {"limit": 20}


# ---------------------------------------------------------------------------
# AgencyBoardSource -- pagination
# ---------------------------------------------------------------------------


def _paged_responder(pages):
    def responder(url, params=None, headers=None):
        page = (params or {}).get("page", 1)
        return {"results": pages.get(page, [])}

    return responder


def test_pagination_walks_pages_until_one_is_empty(monkeypatch):
    calls: list[dict] = []
    pages = {
        1: [{"t": "Coach A", "u": "/job/a"}],
        2: [{"t": "Coach B", "u": "/job/b"}],
    }
    install_json(monkeypatch, _paged_responder(pages), calls=calls)

    options = _board(
        records_path="results",
        field_map={"title": "t", "url": "u"},
        page_param="page",
        max_pages=5,
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert [job.title for job in postings] == ["Coach A", "Coach B"]
    assert [call["params"]["page"] for call in calls] == [1, 2, 3]


def test_pagination_is_bounded_by_max_pages(monkeypatch):
    calls: list[dict] = []

    def responder(url, params=None, headers=None):
        page = (params or {}).get("page", 1)
        return {"results": [{"t": f"Coach {page}", "u": f"/job/{page}"}]}

    install_json(monkeypatch, responder, calls=calls)

    options = _board(
        records_path="results",
        field_map={"title": "t", "url": "u"},
        page_param="page",
        max_pages=2,
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert len(postings) == 2
    assert len(calls) == 2


def test_page_start_is_honoured(monkeypatch):
    calls: list[dict] = []
    install_json(monkeypatch, _paged_responder({0: [{"t": "Coach", "u": "/job/1"}]}), calls=calls)

    options = _board(
        records_path="results",
        field_map={"title": "t", "url": "u"},
        page_param="page",
        page_start=0,
        max_pages=3,
    )
    list(AgencyBoardSource("naf", options).fetch())

    assert calls[0]["params"]["page"] == 0


def test_pagination_stops_when_a_page_repeats_itself(monkeypatch):
    calls: list[dict] = []
    install_json(
        monkeypatch,
        static({"results": [{"t": "Coach", "u": "/job/1"}]}),
        calls=calls,
    )

    options = _board(
        records_path="results",
        field_map={"title": "t", "url": "u"},
        page_param="page",
        max_pages=9,
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    # A board that ignores ``page`` must not be fetched nine times.
    assert len(postings) == 1
    assert len(calls) == 2


def test_total_pages_path_stops_the_walk_early(monkeypatch):
    calls: list[dict] = []

    def responder(url, params=None, headers=None):
        page = (params or {}).get("page", 1)
        return {"meta": {"totalPages": 2}, "results": [{"t": f"C{page}", "u": f"/job/{page}"}]}

    install_json(monkeypatch, responder, calls=calls)

    options = _board(
        records_path="results",
        field_map={"title": "t", "url": "u"},
        page_param="page",
        max_pages=9,
        total_pages_path="meta.totalPages",
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert len(postings) == 2
    assert len(calls) == 2


def test_no_page_param_means_exactly_one_request(monkeypatch):
    calls: list[dict] = []
    install_json(monkeypatch, static({"results": [{"t": "Coach", "u": "/job/1"}]}), calls=calls)

    options = _board(records_path="results", field_map={"title": "t", "url": "u"}, max_pages=7)
    list(AgencyBoardSource("naf", options).fetch())

    assert len(calls) == 1


def test_first_page_failure_is_raised(monkeypatch):
    def responder(url, params=None, headers=None):
        raise FetchError("HTTP 503")

    install_json(monkeypatch, responder)

    options = _board(records_path="results", field_map={"title": "t", "url": "u"})
    with pytest.raises(FetchError):
        list(AgencyBoardSource("naf", options).fetch())


def test_later_page_failure_keeps_the_earlier_pages(monkeypatch):
    def responder(url, params=None, headers=None):
        page = (params or {}).get("page", 1)
        if page > 1:
            raise FetchError("HTTP 500")
        return {"results": [{"t": "Coach A", "u": "/job/a"}]}

    install_json(monkeypatch, responder)

    options = _board(
        records_path="results",
        field_map={"title": "t", "url": "u"},
        page_param="page",
        max_pages=4,
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert [job.title for job in postings] == ["Coach A"]


# ---------------------------------------------------------------------------
# AgencyBoardSource -- detail fetch
# ---------------------------------------------------------------------------

TEASER_PAYLOAD = {
    "results": [
        {"id": "118", "t": "Strength and Conditioning Coach", "u": "/job/118", "teaser": "Apply now."},
        {"id": "119", "t": "Athletic Trainer", "u": "/job/119", "teaser": "Apply now."},
    ]
}


def _detail_options(**overrides):
    options = _board(
        records_path="results",
        field_map={
            "title": "t",
            "url": "u",
            "source_id": "id",
            "description": "teaser",
        },
        detail_url_template="https://careers.example.gov/api/vacancy/{id}",
        detail_id_field="id",
    )
    options.update(overrides)
    return options


def test_detail_fetch_supplies_the_full_description(monkeypatch):
    calls: list[dict] = []

    def responder(url, params=None, headers=None):
        if url == LIST_URL:
            return TEASER_PAYLOAD
        return {"vacancy": {"body": LONG_TEXT, "office": "Fitness and Sports"}}

    install_json(monkeypatch, responder, calls=calls)

    options = _detail_options(
        detail_records_path="vacancy",
        detail_field_map={"title": "t", "url": "u", "description": "body", "department": "office"},
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert len(postings) == 2
    assert "TSAC-F required" in postings[0].description
    assert postings[0].department == "Fitness and Sports"
    assert [call["url"] for call in calls[1:]] == [
        "https://careers.example.gov/api/vacancy/118",
        "https://careers.example.gov/api/vacancy/119",
    ]


def test_detail_fetch_is_bounded_by_detail_limit(monkeypatch):
    calls: list[dict] = []

    def responder(url, params=None, headers=None):
        if url == LIST_URL:
            return TEASER_PAYLOAD
        return {"body": LONG_TEXT}

    install_json(monkeypatch, responder, calls=calls)

    options = _detail_options(
        detail_limit=1,
        detail_field_map={"title": "t", "url": "u", "description": "body"},
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert len(postings) == 2
    # One detail request spent, and the second posting keeps its teaser.
    assert len([call for call in calls if call["url"] != LIST_URL]) == 1
    assert "TSAC-F" in postings[0].description
    assert "TSAC-F" not in postings[1].description


def test_detail_fetch_failure_degrades_to_the_list_record(monkeypatch):
    def responder(url, params=None, headers=None):
        if url == LIST_URL:
            return TEASER_PAYLOAD
        raise FetchError("HTTP 404")

    install_json(monkeypatch, responder)

    postings = list(AgencyBoardSource("naf", _detail_options()).fetch())

    assert [job.title for job in postings] == [
        "Strength and Conditioning Coach",
        "Athletic Trainer",
    ]
    assert postings[0].description.startswith("Apply now.")


def test_detail_fetch_is_skipped_when_the_list_text_is_long_enough(monkeypatch):
    calls: list[dict] = []
    payload = {"results": [{"id": "118", "t": "Coach", "u": "/job/118", "teaser": LONG_TEXT}]}
    install_json(monkeypatch, static(payload), calls=calls)

    list(AgencyBoardSource("naf", _detail_options()).fetch())

    assert len(calls) == 1


def test_detail_fetch_is_skipped_when_the_id_is_missing(monkeypatch):
    calls: list[dict] = []
    payload = {"results": [{"t": "Coach", "u": "/job/118", "teaser": "Apply now."}]}
    install_json(monkeypatch, static(payload), calls=calls)

    list(AgencyBoardSource("naf", _detail_options()).fetch())

    assert len(calls) == 1


def test_detail_template_can_use_a_record_key_directly(monkeypatch):
    calls: list[dict] = []

    def responder(url, params=None, headers=None):
        if url == LIST_URL:
            return {"results": [{"slug": "coach-118", "t": "Coach", "u": "/job/118"}]}
        return {"body": LONG_TEXT}

    install_json(monkeypatch, responder, calls=calls)

    options = _board(
        records_path="results",
        field_map={"title": "t", "url": "u"},
        detail_url_template="https://careers.example.gov/api/{slug}.json",
        detail_field_map={"title": "t", "url": "u", "description": "body"},
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert calls[1]["url"] == "https://careers.example.gov/api/coach-118.json"
    assert "TSAC-F required" in postings[0].description


def test_detail_response_may_be_a_one_element_array(monkeypatch):
    def responder(url, params=None, headers=None):
        if url == LIST_URL:
            return TEASER_PAYLOAD
        return [{"body": LONG_TEXT}]

    install_json(monkeypatch, responder)

    options = _detail_options(
        detail_field_map={"title": "t", "url": "u", "description": "body"}
    )
    postings = list(AgencyBoardSource("naf", options).fetch())

    assert "athlete monitoring" in postings[0].description


# ---------------------------------------------------------------------------
# SitemapJobsSource
# ---------------------------------------------------------------------------

URLSET = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url>
    <loc>https://careers.example.gov/jobs/tactical-strength-and-conditioning-coach</loc>
    <lastmod>2026-07-01</lastmod>
  </url>
  <url>
    <loc>https://careers.example.gov/jobs/human_performance_specialist.html</loc>
  </url>
  <url>
    <loc>https://careers.example.gov/about/our-mission</loc>
  </url>
  <url>
    <loc>/jobs/naf-fitness-specialist</loc>
  </url>
</urlset>
"""

INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://careers.example.gov/sitemap-jobs-1.xml</loc></sitemap>
  <sitemap><loc>https://careers.example.gov/sitemap-jobs-2.xml</loc></sitemap>
</sitemapindex>
"""


def _shard(*locs):
    entries = "".join(f"<url><loc>{loc}</loc></url>" for loc in locs)
    return (
        '<?xml version="1.0" encoding="UTF-8"?>'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}</urlset>"
    )


def test_sitemap_yields_one_record_per_url(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: URLSET})

    postings = list(SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch())

    assert len(postings) == 4
    assert postings[0].source == "sitemapjobs:example"
    assert postings[0].source_id == postings[0].url
    assert postings[0].employer == "example"
    # A discovery record carries no description on purpose.
    assert all(job.description == "" for job in postings)
    assert postings[0].raw["discovery"] is True


def test_sitemap_titles_are_deslugified(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: URLSET})

    titles = [job.title for job in SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch()]

    assert titles[0] == "Tactical Strength And Conditioning Coach"
    assert titles[1] == "Human Performance Specialist"
    assert titles[3] == "Naf Fitness Specialist"


def test_sitemap_resolves_relative_locations(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: URLSET})

    urls = [job.url for job in SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch()]

    assert "https://careers.example.gov/jobs/naf-fitness-specialist" in urls


def test_sitemap_lastmod_is_kept_out_of_posted_at(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: URLSET})

    job = list(SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch())[0]

    assert job.posted_at is None
    assert job.raw["lastmod"] == "2026-07-01"


def test_url_include_filters_the_sitemap(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: URLSET})

    options = {"sitemap": SITEMAP_URL, "url_include": ["/jobs/"]}
    urls = [job.url for job in SitemapJobsSource("example", options).fetch()]

    assert len(urls) == 3
    assert all("/jobs/" in url for url in urls)


def test_url_exclude_filters_the_sitemap(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: URLSET})

    options = {"sitemap": SITEMAP_URL, "url_exclude": ["/about/"]}
    urls = [job.url for job in SitemapJobsSource("example", options).fetch()]

    assert all("/about/" not in url for url in urls)
    assert len(urls) == 3


def test_max_urls_caps_the_run(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: URLSET})

    options = {"sitemap": SITEMAP_URL, "max_urls": 2}
    assert len(list(SitemapJobsSource("example", options).fetch())) == 2


def test_sitemap_index_is_followed_one_level(monkeypatch):
    documents = {
        SITEMAP_URL: INDEX,
        "https://careers.example.gov/sitemap-jobs-1.xml": _shard(
            "https://careers.example.gov/jobs/athletic-trainer-h2f"
        ),
        "https://careers.example.gov/sitemap-jobs-2.xml": _shard(
            "https://careers.example.gov/jobs/cognitive-performance-specialist"
        ),
    }
    calls: list[str] = []
    install_fetch(monkeypatch, documents, calls=calls)

    postings = list(SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch())

    assert [job.title for job in postings] == [
        "Athletic Trainer H2f",
        "Cognitive Performance Specialist",
    ]
    assert len(calls) == 3


def test_sitemap_index_is_bounded_by_max_sitemaps(monkeypatch):
    documents = {
        SITEMAP_URL: INDEX,
        "https://careers.example.gov/sitemap-jobs-1.xml": _shard(
            "https://careers.example.gov/jobs/athletic-trainer"
        ),
        "https://careers.example.gov/sitemap-jobs-2.xml": _shard(
            "https://careers.example.gov/jobs/dietitian"
        ),
    }
    calls: list[str] = []
    install_fetch(monkeypatch, documents, calls=calls)

    options = {"sitemap": SITEMAP_URL, "max_sitemaps": 1}
    postings = list(SitemapJobsSource("example", options).fetch())

    assert [job.title for job in postings] == ["Athletic Trainer"]
    assert len(calls) == 2


def test_child_sitemap_failure_keeps_the_other_shards(monkeypatch):
    documents = {
        SITEMAP_URL: INDEX,
        "https://careers.example.gov/sitemap-jobs-2.xml": _shard(
            "https://careers.example.gov/jobs/exercise-physiologist"
        ),
    }
    install_fetch(monkeypatch, documents)

    postings = list(SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch())

    assert [job.title for job in postings] == ["Exercise Physiologist"]


def test_duplicate_urls_are_emitted_once(monkeypatch):
    duplicated = _shard(
        "https://careers.example.gov/jobs/coach",
        "https://careers.example.gov/jobs/coach",
    )
    install_fetch(monkeypatch, {SITEMAP_URL: duplicated})

    assert len(list(SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch())) == 1


def test_gzipped_sitemap_body_is_decompressed(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: gzip.compress(URLSET.encode())})

    postings = list(SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch())

    assert len(postings) == 4


def test_missing_sitemap_option_is_reported():
    with pytest.raises(KeyError, match="requires option 'sitemap'"):
        list(SitemapJobsSource("example", {}).fetch())


def test_unreadable_root_sitemap_raises(monkeypatch):
    install_fetch(monkeypatch, {})

    with pytest.raises(RuntimeError, match="could not be read"):
        list(SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch())


def test_root_sitemap_that_is_not_xml_raises(monkeypatch):
    install_fetch(monkeypatch, {SITEMAP_URL: "<html><body>login wall</body>"})

    with pytest.raises(RuntimeError, match="not valid XML"):
        list(SitemapJobsSource("example", {"sitemap": SITEMAP_URL}).fetch())


# ---------------------------------------------------------------------------
# de-slugification
# ---------------------------------------------------------------------------


def test_deslugify_drops_a_purely_numeric_final_segment():
    assert deslugify("https://x.gov/jobs/athletic-trainer/948213") == "Athletic Trainer"


def test_deslugify_preserves_acronyms():
    assert deslugify("https://x.gov/jobs/coach-USASOC-THOR3") == "Coach USASOC THOR3"


def test_deslugify_handles_encoding_extensions_and_query_strings():
    assert deslugify("https://x.gov/jobs/strength%20coach.aspx?src=rss") == "Strength Coach"
    assert deslugify("https://x.gov/jobs/performance_dietitian/") == "Performance Dietitian"


def test_deslugify_of_a_bare_host_is_empty():
    assert deslugify("https://x.gov/") == ""


def test_numeric_only_path_falls_back_to_the_number():
    assert deslugify("https://x.gov/948213") == "948213"


# ---------------------------------------------------------------------------
# registry shape
# ---------------------------------------------------------------------------


def test_agency_sources_are_exported_and_well_formed():
    assert AGENCY_SOURCES == (AgencyBoardSource, SitemapJobsSource)
    kinds = [cls.kind for cls in AGENCY_SOURCES]
    assert kinds == ["agencyboard", "sitemapjobs"]
    assert len(set(kinds)) == len(kinds)
    assert all(issubclass(cls, Source) for cls in AGENCY_SOURCES)
