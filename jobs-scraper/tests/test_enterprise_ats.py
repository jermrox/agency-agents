"""Enterprise ATS adapter tests (iCIMS, SuccessFactors, CSOD, Oracle Cloud,
Jobvite, Radancy).

Everything runs against captured payload shapes taken from the career-ops
recipes these adapters were ported from. There is no outbound network in CI
or the sandbox, so ``fetch``/``fetch_json``/``post_json`` are replaced as
imported into the adapter module, and the assertions are about field mapping,
pagination bounds, malformed-record handling, and the honesty rule: a field
the response does not state stays ``None``/``""``.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.http import FetchError  # noqa: E402
from tactical_jobs.sources.base import Source  # noqa: E402
from tactical_jobs.sources.enterprise_ats import (  # noqa: E402
    ENTERPRISE_SOURCES,
    CornerstoneSource,
    ICIMSSource,
    JobviteSource,
    OracleCloudSource,
    RadancySource,
    SuccessFactorsSource,
)


class FakeHTTP:
    """Stands in for the three http helpers and records what was asked.

    Route values may be str/bytes (text), dicts (json), or Exceptions;
    callables receive the URL (and the payload, for posts). A missing route
    raises ``FetchError`` -- the same shape a live 404 produces.
    """

    def __init__(self, text=None, json_routes=None, post_routes=None):
        self.text = text or {}
        self.json_routes = json_routes or {}
        self.post_routes = post_routes or {}
        self.text_calls: list[tuple[str, dict]] = []
        self.json_calls: list[tuple[str, dict]] = []
        self.post_calls: list[tuple[str, dict, dict]] = []

    def _resolve(self, routes, url):
        value = routes(url) if callable(routes) else routes.get(url)
        if value is None:
            raise FetchError(f"HTTP 404 for {url}")
        if isinstance(value, Exception):
            raise value
        return value

    def fetch(self, url, **kwargs):
        self.text_calls.append((url, kwargs))
        value = self._resolve(self.text, url)
        return value.encode() if isinstance(value, str) else value

    def fetch_json(self, url, **kwargs):
        self.json_calls.append((url, kwargs))
        return self._resolve(self.json_routes, url)

    def post_json(self, url, payload, **kwargs):
        self.post_calls.append((url, payload, kwargs))
        routes = self.post_routes
        value = routes(url, payload) if callable(routes) else routes.get(url)
        if value is None:
            raise FetchError(f"HTTP 404 for POST {url}")
        if isinstance(value, Exception):
            raise value
        return json.dumps(value).encode()

    def install(self, monkeypatch):
        monkeypatch.setattr("tactical_jobs.sources.enterprise_ats.fetch", self.fetch)
        monkeypatch.setattr("tactical_jobs.sources.enterprise_ats.fetch_json", self.fetch_json)
        monkeypatch.setattr("tactical_jobs.sources.enterprise_ats.post_json", self.post_json)
        return self


# ---------------------------------------------------------------------------
# iCIMS
# ---------------------------------------------------------------------------

ICIMS_ORIGIN = "https://careers-acme.icims.com"


def _icims_card(job_id, title, location=None, href=None):
    href = href or f"{ICIMS_ORIGIN}/jobs/{job_id}/{title.lower().replace(' ', '-')}/job?in_iframe=1&amp;hub=8"
    location_html = (
        '<div><span class="glyph field-label">Location</span>'
        f'<span class="field-value">{location}</span></div>'
        if location
        else ""
    )
    return (
        '<li class="iCIMS_JobCardItem card">'
        f'<a class="iCIMS_Anchor" href="{href}"><h3 class="themed"> {title} </h3></a>'
        f"{location_html}</li>"
    )


def _icims_page(cards):
    return f"<ul>{''.join(cards)}</ul>" if cards else '<div class="iCIMS_NoResults">Sorry.</div>'


def _icims_search_url(page):
    return f"{ICIMS_ORIGIN}/jobs/search?ss=1&pr={page}&in_iframe=1"


def _run_icims(monkeypatch, api, options=None):
    api.install(monkeypatch)
    merged = {"careers_url": f"{ICIMS_ORIGIN}/jobs/search?ss=1", "employer": "ACME Defense", **(options or {})}
    return list(ICIMSSource("acme", merged).fetch())


def test_icims_maps_list_fields_and_leaves_absent_ones_empty(monkeypatch):
    api = FakeHTTP(
        text={
            _icims_search_url(0): _icims_page(
                [_icims_card(5011, "Human Performance Coach", "Fort Bragg, NC")]
            ),
            _icims_search_url(1): _icims_page([]),
        }
    )
    posting = _run_icims(monkeypatch, api)[0]

    assert posting.source == "icims:acme"
    assert posting.source_id == "5011"
    assert posting.title == "Human Performance Coach"
    assert posting.employer == "ACME Defense"
    assert posting.location == "Fort Bragg, NC"
    # The list page carries no query-free URL... the query IS stripped:
    assert posting.url == f"{ICIMS_ORIGIN}/jobs/5011/human-performance-coach/job"
    # The list page states no date and no description -- neither is invented.
    assert posting.posted_at is None
    assert posting.description == ""


def test_icims_resolves_relative_hrefs_and_drops_off_origin_cards(monkeypatch):
    api = FakeHTTP(
        text={
            _icims_search_url(0): _icims_page(
                [
                    _icims_card(7001, "Athletic Trainer", href="/jobs/7001/athletic-trainer/job"),
                    _icims_card(
                        9999,
                        "Phisher",
                        href="https://evil.example.com/jobs/9999/phisher/job",
                    ),
                ]
            ),
            _icims_search_url(1): _icims_page([]),
        }
    )
    postings = _run_icims(monkeypatch, api)

    assert [p.source_id for p in postings] == ["7001"]
    assert postings[0].url == f"{ICIMS_ORIGIN}/jobs/7001/athletic-trainer/job"


def test_icims_card_without_a_title_is_skipped(monkeypatch):
    broken = '<li class="iCIMS_JobCardItem"><a href="/jobs/1234/coach/job">no h3 here</a></li>'
    api = FakeHTTP(
        text={
            _icims_search_url(0): f"<ul>{broken}{_icims_card(5011, 'Coach', 'Tampa, FL')}</ul>",
            _icims_search_url(1): _icims_page([]),
        }
    )
    postings = _run_icims(monkeypatch, api)
    assert [p.source_id for p in postings] == ["5011"]


def test_icims_pagination_stops_when_a_page_repeats(monkeypatch):
    """Some tenants serve the last real page again for an out-of-range pr."""
    page = _icims_page([_icims_card(5011, "Coach", "Tampa, FL")])
    api = FakeHTTP(text={_icims_search_url(0): page, _icims_search_url(1): page})
    postings = _run_icims(monkeypatch, api)

    assert len(api.text_calls) == 2
    assert [p.source_id for p in postings] == ["5011"]


def test_icims_max_pages_bounds_the_walk(monkeypatch):
    def endless(url):
        page = int(re.search(r"pr=(\d+)", url).group(1))
        return _icims_page([_icims_card(1000 + page, f"Coach {page}", "Tampa, FL")])

    api = FakeHTTP(text=endless)
    postings = _run_icims(monkeypatch, api, {"max_pages": 3})

    assert len(api.text_calls) == 3
    assert len(postings) == 3


def test_icims_rejects_a_non_icims_host(monkeypatch):
    FakeHTTP().install(monkeypatch)
    source = ICIMSSource("x", {"careers_url": "https://careers.example.com/jobs/search"})
    with pytest.raises(ValueError):
        list(source.fetch())


def test_icims_makes_no_detail_requests_by_default(monkeypatch):
    api = FakeHTTP(
        text={
            _icims_search_url(0): _icims_page([_icims_card(5011, "Coach", "Tampa, FL")]),
            _icims_search_url(1): _icims_page([]),
        }
    )
    _run_icims(monkeypatch, api)
    assert not any(url.endswith("/job?in_iframe=1") for url, _ in api.text_calls)


def test_icims_date_enrichment_reads_the_detail_jsonld(monkeypatch):
    detail_url = f"{ICIMS_ORIGIN}/jobs/5011/coach/job?in_iframe=1"
    detail_html = (
        '<html><script nonce="c5p" type="application/ld+json">'
        '{"@context":"http://schema.org","@type":"JobPosting",'
        '"title":"Coach","datePosted":"2026-07-01"}'
        "</script></html>"
    )
    api = FakeHTTP(
        text={
            _icims_search_url(0): _icims_page(
                [_icims_card(5011, "Coach", "Tampa, FL"), _icims_card(5012, "Trainer", "Tampa, FL")]
            ),
            _icims_search_url(1): _icims_page([]),
            detail_url: detail_html,
            # 5012's detail page carries no JSON-LD -- its date must stay None.
        }
    )
    postings = _run_icims(monkeypatch, api, {"detail_limit": 1})

    assert postings[0].posted_at is not None
    assert (postings[0].posted_at.year, postings[0].posted_at.month, postings[0].posted_at.day) == (2026, 7, 1)
    assert postings[1].posted_at is None, "past the detail budget, no date is invented"


def test_icims_detail_failure_leaves_the_posting_undated(monkeypatch):
    api = FakeHTTP(
        text={
            _icims_search_url(0): _icims_page([_icims_card(5011, "Coach", "Tampa, FL")]),
            _icims_search_url(1): _icims_page([]),
            # detail URL missing -> FetchError inside enrichment
        }
    )
    postings = _run_icims(monkeypatch, api, {"detail_limit": 5})
    assert len(postings) == 1
    assert postings[0].posted_at is None


# ---------------------------------------------------------------------------
# SuccessFactors
# ---------------------------------------------------------------------------

SF_URL = "https://jobs.example.com"


def _sf_tile(job_id, title, data_url, city=None):
    city_html = (
        f'<div class="jobdetail-value" id="job-{job_id}-desktop-section-city-value">{city}</div>'
        if city
        else ""
    )
    return (
        f'<li class="job-tile job-id-{job_id} tile" data-url="{data_url}">'
        f'<div><a class="jobTitle-link" href="{data_url}">{title}</a>{city_html}</div></li>'
    )


def _csb_record(job_id, title, url_title, locations, start):
    return {
        "response": {
            "id": job_id,
            "unifiedStandardTitle": title,
            "unifiedUrlTitle": url_title,
            "jobLocationShort": locations,
            "unifiedStandardStart": start,
        }
    }


def _run_sf(monkeypatch, api, options=None):
    api.install(monkeypatch)
    merged = {"careers_url": SF_URL, "employer": "Example Industrial", **(options or {})}
    return list(SuccessFactorsSource("example", merged).fetch())


def test_sf_rmk_maps_tiles_and_never_invents_a_date(monkeypatch):
    api = FakeHTTP(
        text={
            f"{SF_URL}/tile-search-results/?startrow=0": f"<ul>{_sf_tile(4711, 'Human Performance Engineer', '/job/Oberkochen-Human-Performance-Engineer-XY1/4711/', city='Oberkochen')}</ul>",
            f"{SF_URL}/tile-search-results/?startrow=1": "<ul></ul>",
        }
    )
    posting = _run_sf(monkeypatch, api)[0]

    assert posting.source == "successfactors:example"
    assert posting.source_id == "4711"
    assert posting.title == "Human Performance Engineer"
    assert posting.employer == "Example Industrial"
    assert posting.location == "Oberkochen"
    assert posting.url == f"{SF_URL}/job/Oberkochen-Human-Performance-Engineer-XY1/4711/"
    assert posting.posted_at is None, "RMK states no posting date"
    assert posting.description == ""


def test_sf_rmk_recovers_the_city_from_the_slug(monkeypatch):
    """Tenants that render no city field still state the city in the path."""
    api = FakeHTTP(
        text={
            f"{SF_URL}/tile-search-results/?startrow=0": f"<ul>{_sf_tile(88, 'Senior Systems Engineer', '/job/Bad-Homburg-Senior-Systems-Engineer-Z9/88/')}</ul>",
            f"{SF_URL}/tile-search-results/?startrow=1": "<ul></ul>",
        }
    )
    posting = _run_sf(monkeypatch, api)[0]
    assert posting.location == "Bad Homburg"


def test_sf_rmk_advances_startrow_by_returned_count(monkeypatch):
    api = FakeHTTP(
        text={
            f"{SF_URL}/tile-search-results/?startrow=0": "<ul>"
            + _sf_tile(1, "Coach A", "/job/X-Coach-A-1/1/", city="X")
            + _sf_tile(2, "Coach B", "/job/X-Coach-B-2/2/", city="X")
            + "</ul>",
            f"{SF_URL}/tile-search-results/?startrow=2": f"<ul>{_sf_tile(3, 'Coach C', '/job/X-Coach-C-3/3/', city='X')}</ul>",
            f"{SF_URL}/tile-search-results/?startrow=3": "<ul></ul>",
        }
    )
    postings = _run_sf(monkeypatch, api)
    assert [p.source_id for p in postings] == ["1", "2", "3"]
    assert [url for url, _ in api.text_calls] == [
        f"{SF_URL}/tile-search-results/?startrow=0",
        f"{SF_URL}/tile-search-results/?startrow=2",
        f"{SF_URL}/tile-search-results/?startrow=3",
    ]


def test_sf_rmk_stops_when_the_server_ignores_the_offset(monkeypatch):
    page = f"<ul>{_sf_tile(1, 'Coach', '/job/X-Coach-1/1/', city='X')}</ul>"
    api = FakeHTTP(
        text={
            f"{SF_URL}/tile-search-results/?startrow=0": page,
            f"{SF_URL}/tile-search-results/?startrow=1": page,  # same id again
        }
    )
    postings = _run_sf(monkeypatch, api)
    assert len(postings) == 1
    assert len(api.text_calls) == 2


def test_sf_falls_back_to_csb_when_the_tile_endpoint_is_an_empty_shell(monkeypatch):
    def posts(url, payload):
        assert url == f"{SF_URL}/services/recruiting/v1/jobs"
        if payload["locale"] == "en_US" and payload["pageNumber"] == 0:
            return {
                "totalJobs": 1,
                "jobSearchResult": [
                    _csb_record(555, "Program &amp; Release Manager", "Program-&amp;-Release-Manager", ["Karlovy Vary, CZE, 36004<br/>"], "6/18/26")
                ],
            }
        return {"totalJobs": 1, "jobSearchResult": []}

    api = FakeHTTP(
        text={
            f"{SF_URL}/tile-search-results/?startrow=0": "<!DOCTYPE html>",
            f"{SF_URL}/search/": '<a href="/search/?q=&amp;startrow=0&amp;locale=en_US">English</a>',
        },
        post_routes=posts,
    )
    postings = _run_sf(monkeypatch, api)

    assert len(postings) == 1
    posting = postings[0]
    assert posting.source_id == "555"
    assert posting.title == "Program & Release Manager"
    assert posting.location == "Karlovy Vary, CZE, 36004"
    # Slug entities decoded, URL-structural chars dropped and runs of hyphens
    # collapsed (career-ops parseCsbJobs), id-locale tail kept.
    assert posting.url == f"{SF_URL}/job/Program-Release-Manager/555-en_US"
    assert posting.posted_at is not None
    assert (posting.posted_at.year, posting.posted_at.month, posting.posted_at.day) == (2026, 6, 18)


def test_sf_variant_csb_skips_the_tile_endpoint(monkeypatch):
    def posts(url, payload):
        if payload["locale"] == "de_DE" and payload["pageNumber"] == 0:
            return {"totalJobs": 1, "jobSearchResult": [_csb_record(1, "Koch", "Koch", ["Berlin, DEU"], "20.11.23")]}
        return {"totalJobs": 1, "jobSearchResult": []}

    api = FakeHTTP(
        text={f"{SF_URL}/search/": '<a href="/search/?q=&amp;locale=de_DE">DE</a>'},
        post_routes=posts,
    )
    postings = _run_sf(monkeypatch, api, {"variant": "csb"})

    assert len(postings) == 1
    assert not any("tile-search-results" in url for url, _ in api.text_calls)
    # European D.M.YY date parsed with day first.
    stamp = postings[0].posted_at
    assert (stamp.year, stamp.month, stamp.day) == (2023, 11, 20)


def test_sf_csb_unparseable_date_stays_none(monkeypatch):
    def posts(url, payload):
        if payload["locale"] == "en_US" and payload["pageNumber"] == 0:
            return {"totalJobs": 1, "jobSearchResult": [_csb_record(9, "Analyst", "Analyst", ["Wien, AUT"], "posted recently")]}
        return {"totalJobs": 1, "jobSearchResult": []}

    api = FakeHTTP(
        text={f"{SF_URL}/search/": '<a href="?locale=en_US">EN</a>'},
        post_routes=posts,
    )
    postings = _run_sf(monkeypatch, api, {"variant": "csb"})
    assert postings[0].posted_at is None


def test_sf_csb_dedupes_across_locales_first_locale_wins(monkeypatch):
    def posts(url, payload):
        if payload["pageNumber"] == 0:
            return {"totalJobs": 1, "jobSearchResult": [_csb_record(77, "Fitter", "Fitter", ["Ulm, DEU"], "1.2.24")]}
        return {"totalJobs": 1, "jobSearchResult": []}

    api = FakeHTTP(
        text={f"{SF_URL}/search/": '<a href="?locale=en_US">EN</a><a href="?locale=de_DE">DE</a>'},
        post_routes=posts,
    )
    postings = _run_sf(monkeypatch, api, {"variant": "csb"})

    assert len(postings) == 1, "the same job id under two locales is one posting"
    # de_DE outranks en_US in the recipe's priority order.
    assert postings[0].url.endswith("/77-de_DE")


def test_sf_csb_skips_records_missing_id_or_title(monkeypatch):
    def posts(url, payload):
        if payload["locale"] == "en_US" and payload["pageNumber"] == 0:
            return {
                "totalJobs": 3,
                "jobSearchResult": [
                    {"response": {"unifiedStandardTitle": "No id"}},
                    {"response": {"id": 2, "unifiedStandardTitle": ""}},
                    {"no_response": True},
                    _csb_record(3, "Good", "Good", ["Graz, AUT"], "6/1/26"),
                ],
            }
        return {"totalJobs": 3, "jobSearchResult": []}

    api = FakeHTTP(
        text={f"{SF_URL}/search/": '<a href="?locale=en_US">EN</a>'},
        post_routes=posts,
    )
    postings = _run_sf(monkeypatch, api, {"variant": "csb"})
    assert [p.source_id for p in postings] == ["3"]


def test_sf_csb_paginates_to_the_reported_total(monkeypatch):
    def posts(url, payload):
        page = payload["pageNumber"]
        if payload["locale"] != "en_US" or page > 2:
            return {"totalJobs": 25, "jobSearchResult": []}
        count = 10 if page < 2 else 5
        return {
            "totalJobs": 25,
            "jobSearchResult": [
                _csb_record(page * 10 + i, f"Job {page * 10 + i}", "slug", ["X"], "6/1/26")
                for i in range(count)
            ],
        }

    api = FakeHTTP(
        text={f"{SF_URL}/search/": '<a href="?locale=en_US">EN</a>'},
        post_routes=posts,
    )
    postings = _run_sf(monkeypatch, api, {"variant": "csb"})

    assert len(postings) == 25
    assert [p["pageNumber"] for _, p, _ in api.post_calls] == [0, 1, 2]


# ---------------------------------------------------------------------------
# Cornerstone OnDemand
# ---------------------------------------------------------------------------

CSOD_URL = "https://career-ohb.csod.com/ux/ats/careersite/4/home?c=career-ohb"
CSOD_HOME = "https://career-ohb.csod.com/ux/ats/careersite/4/home?c=career-ohb"
CSOD_API = "https://career-ohb.csod.com/services/x/career-site/v1/search"
CSOD_TOKEN = "eyJhbGciOiJIUzI1NiJ9.e30.abc-_123"
CSOD_HOME_HTML = f'<html><script>var cs = {{"token":"{CSOD_TOKEN}","culture":1}};</script></html>'


def _csod_req(req_id, title, date="7/3/2026", locations=None):
    return {
        "requisitionId": req_id,
        "displayJobTitle": title,
        "postingEffectiveDate": date,
        "locations": locations if locations is not None else [{"city": "Bremen", "state": "", "country": "DE"}],
    }


def _csod_page(reqs, total=None):
    return {"data": {"totalCount": total if total is not None else len(reqs), "requisitions": reqs}}


def _run_csod(monkeypatch, api, options=None):
    api.install(monkeypatch)
    merged = {"careers_url": CSOD_URL, "employer": "OHB", **(options or {})}
    return list(CornerstoneSource("ohb", merged).fetch())


def test_csod_extracts_the_anonymous_token_and_sends_it_as_bearer(monkeypatch):
    api = FakeHTTP(
        text={CSOD_HOME: CSOD_HOME_HTML},
        post_routes=lambda url, payload: _csod_page([_csod_req("R1", "Systems Engineer")]),
    )
    _run_csod(monkeypatch, api)

    url, payload, kwargs = api.post_calls[0]
    assert url == CSOD_API
    assert kwargs["headers"]["Authorization"] == f"Bearer {CSOD_TOKEN}"
    assert payload["careerSiteId"] == 4
    assert payload["careerSitePageId"] == 4
    assert payload["pageNumber"] == 1
    assert payload["pageSize"] == 25
    assert payload["cultureName"] == "en-US"
    assert payload["searchText"] == ""


def test_csod_maps_requisition_fields(monkeypatch):
    req = _csod_req(
        "ab12-34",
        "Human <b>Performance</b> Coordinator",
        date="7/3/2026",
        locations=[
            {"city": "Bremen", "state": "", "country": "DE"},
            {"city": "", "state": "", "country": "US"},
        ],
    )
    api = FakeHTTP(text={CSOD_HOME: CSOD_HOME_HTML}, post_routes=lambda u, p: _csod_page([req]))
    posting = _run_csod(monkeypatch, api)[0]

    assert posting.source == "csod:ohb"
    assert posting.source_id == "ab12-34"
    assert posting.title == "Human Performance Coordinator"
    assert posting.employer == "OHB"
    assert posting.location == "Bremen, DE / US"
    assert posting.url == (
        "https://career-ohb.csod.com/ux/ats/careersite/4/home/requisition/ab12-34?c=career-ohb"
    )
    assert (posting.posted_at.year, posting.posted_at.month, posting.posted_at.day) == (2026, 7, 3)
    assert posting.description == "", "the search response states no description"


def test_csod_impossible_dates_stay_none(monkeypatch):
    api = FakeHTTP(
        text={CSOD_HOME: CSOD_HOME_HTML},
        post_routes=lambda u, p: _csod_page(
            [_csod_req("R1", "Coach", date="4/31/2026"), _csod_req("R2", "Coach 2", date="Posted today")]
        ),
    )
    postings = _run_csod(monkeypatch, api)
    assert [p.posted_at for p in postings] == [None, None]


def test_csod_paginates_until_the_reported_total(monkeypatch):
    def posts(url, payload):
        page = payload["pageNumber"]
        if page == 1:
            return _csod_page([_csod_req(f"R{i}", f"Job {i}") for i in range(25)], total=30)
        return _csod_page([_csod_req(f"R{25 + i}", f"Job {25 + i}") for i in range(5)], total=30)

    api = FakeHTTP(text={CSOD_HOME: CSOD_HOME_HTML}, post_routes=posts)
    postings = _run_csod(monkeypatch, api)

    assert len(postings) == 30
    assert [payload["pageNumber"] for _, payload, _ in api.post_calls] == [1, 2]


def test_csod_missing_token_is_an_error_not_an_empty_board(monkeypatch):
    api = FakeHTTP(text={CSOD_HOME: "<html>no embedded config here</html>"})
    api.install(monkeypatch)
    with pytest.raises(FetchError):
        list(CornerstoneSource("ohb", {"careers_url": CSOD_URL}).fetch())


def test_csod_malformed_requisitions_are_skipped(monkeypatch):
    api = FakeHTTP(
        text={CSOD_HOME: CSOD_HOME_HTML},
        post_routes=lambda u, p: _csod_page(
            [
                "not-a-dict",
                {"displayJobTitle": "No id"},
                {"requisitionId": "R9", "displayJobTitle": ""},
                _csod_req("R1", "Good"),
            ]
        ),
    )
    postings = _run_csod(monkeypatch, api)
    assert [p.source_id for p in postings] == ["R1"]


def test_csod_rejects_a_non_csod_url(monkeypatch):
    FakeHTTP().install(monkeypatch)
    with pytest.raises(ValueError):
        list(CornerstoneSource("x", {"careers_url": "https://evil.com/ux/ats/careersite/4/home"}).fetch())


# ---------------------------------------------------------------------------
# Oracle Cloud Recruiting
# ---------------------------------------------------------------------------

ORACLE_URL = "https://acme.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/jobs"


def _oracle_req(req_id="300000123", title="Human Performance Specialist", **extra):
    req = {
        "Id": req_id,
        "Title": title,
        "PostedDate": "2026-07-15",
        "PrimaryLocation": "Tampa, FL, United States",
        "WorkplaceTypeCode": "ORA_ONSITE",
        "ShortDescriptionStr": "<p>Support the SOCOM POTFF human performance program.</p>",
    }
    req.update(extra)
    return req


def _oracle_page(reqs, total=None, has_more=False):
    return {
        "hasMore": has_more,
        "items": [{"TotalJobsCount": total if total is not None else len(reqs), "requisitionList": reqs}],
    }


def _run_oracle(monkeypatch, api, options=None):
    api.install(monkeypatch)
    merged = {"careers_url": ORACLE_URL, "employer": "ACME", **(options or {})}
    return list(OracleCloudSource("acme", merged).fetch())


def test_oracle_builds_the_finder_url(monkeypatch):
    api = FakeHTTP(json_routes=lambda url: _oracle_page([_oracle_req()]))
    _run_oracle(monkeypatch, api)

    url = api.json_calls[0][0]
    assert url.startswith(
        "https://acme.fa.us2.oraclecloud.com/hcmRestApi/resources/latest/recruitingCEJobRequisitions?onlyData=true"
    )
    # The expand is REQUIRED -- without it the API returns no requisitionList.
    assert "expand=requisitionList.workLocation%2CrequisitionList.secondaryLocations" in url
    assert "finder=findReqs;siteNumber=CX_1001," in url
    assert "facetsList=LOCATIONS%3BWORK_LOCATIONS%3B" in url
    assert "sortBy=POSTING_DATES_DESC" in url
    # limit/offset set both in the finder and top-level.
    assert ",limit=200," in url and "&limit=200" in url
    assert ",offset=0" in url and "&offset=0" in url


def test_oracle_maps_requisition_fields(monkeypatch):
    api = FakeHTTP(json_routes=lambda url: _oracle_page([_oracle_req()]))
    posting = _run_oracle(monkeypatch, api)[0]

    assert posting.source == "oraclecloud:acme"
    assert posting.source_id == "300000123"
    assert posting.title == "Human Performance Specialist"
    assert posting.employer == "ACME"
    assert posting.location == "Tampa, FL, United States"
    assert posting.url == (
        "https://acme.fa.us2.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1001/job/300000123"
    )
    assert "SOCOM POTFF" in posting.description
    assert "<p>" not in posting.description
    assert (posting.posted_at.year, posting.posted_at.month, posting.posted_at.day) == (2026, 7, 15)
    assert posting.remote is False


def test_oracle_remote_workplace_type_sets_the_flag(monkeypatch):
    api = FakeHTTP(json_routes=lambda url: _oracle_page([_oracle_req(WorkplaceTypeCode="ORA_REMOTE")]))
    assert _run_oracle(monkeypatch, api)[0].remote is True


def test_oracle_prefers_the_stated_external_url(monkeypatch):
    api = FakeHTTP(
        json_routes=lambda url: _oracle_page(
            [_oracle_req(ExternalURL=" https://careers.acme.com/job/300000123 ")]
        )
    )
    assert _run_oracle(monkeypatch, api)[0].url == "https://careers.acme.com/job/300000123"


def test_oracle_ignores_has_more_and_stops_on_the_total(monkeypatch):
    """Some tenants return hasMore:false on every page with thousands left."""

    def routes(url):
        offset = int(re.search(r"offset=(\d+)", url).group(1))
        if offset == 0:
            return _oracle_page([_oracle_req(str(i)) for i in range(200)], total=250, has_more=False)
        return _oracle_page([_oracle_req(str(200 + i)) for i in range(50)], total=250, has_more=False)

    api = FakeHTTP(json_routes=routes)
    postings = _run_oracle(monkeypatch, api)

    assert len(api.json_calls) == 2, "hasMore:false on page one must not stop the walk"
    assert len(postings) == 250


def test_oracle_stops_on_a_short_page(monkeypatch):
    api = FakeHTTP(json_routes=lambda url: _oracle_page([_oracle_req(str(i)) for i in range(3)], total=999))
    postings = _run_oracle(monkeypatch, api)
    assert len(api.json_calls) == 1
    assert len(postings) == 3


def test_oracle_falls_back_to_the_expanded_work_location(monkeypatch):
    api = FakeHTTP(
        json_routes=lambda url: _oracle_page(
            [
                _oracle_req(
                    "1",
                    PrimaryLocation=None,
                    workLocation=[{"TownOrCity": "Bremen", "Region": "HB", "Country": "Germany"}],
                ),
                _oracle_req("2", PrimaryLocation=None),
            ]
        )
    )
    postings = _run_oracle(monkeypatch, api)
    assert postings[0].location == "Bremen, HB, Germany"
    assert postings[1].location == "", "an unstated location stays empty"


def test_oracle_rows_without_an_id_or_url_are_dropped(monkeypatch):
    api = FakeHTTP(
        json_routes=lambda url: _oracle_page(
            [
                "not-a-dict",
                {"Title": "No id, no url"},
                {"RequisitionNumber": "REQ-7", "Title": "Id via requisition number"},
                _oracle_req("42"),
            ]
        )
    )
    postings = _run_oracle(monkeypatch, api)
    assert [p.source_id for p in postings] == ["REQ-7", "42"]


def test_oracle_rejects_an_untrusted_host(monkeypatch):
    FakeHTTP().install(monkeypatch)
    for bad in (
        "https://acme.fa.us2.oraclecloud.com.evil.com/x",
        "https://acme.oraclecloud.com/hcmUI/CandidateExperience/en/sites/CX_1/jobs",
    ):
        with pytest.raises(ValueError):
            list(OracleCloudSource("x", {"careers_url": bad}).fetch())


# ---------------------------------------------------------------------------
# Jobvite
# ---------------------------------------------------------------------------

JOBVITE_API = "https://jobs.jobvite.com/api/company/acmedefense/jobs"


def _jobvite_job(**extra):
    job = {
        "id": "okiXcfwl",
        "title": "Tactical Strength Coach",
        "category": "Human Performance",
        "location": "Fayetteville, NC",
        "country": "United States",
        "jobType": "Full-Time",
        "date": "2026-06-30T00:00:00.000+0000",
        "applyURL": "https://careers.acmedefense.com/jobs/12345",
    }
    job.update(extra)
    return job


def _run_jobvite(monkeypatch, api, options=None):
    api.install(monkeypatch)
    merged = {
        "careers_url": "https://jobs.jobvite.com/acmedefense",
        "employer": "ACME Defense",
        **(options or {}),
    }
    return list(JobviteSource("acme", merged).fetch())


def test_jobvite_requests_the_company_api_derived_from_the_careers_url(monkeypatch):
    api = FakeHTTP(json_routes={JOBVITE_API: {"jobs": [_jobvite_job()]}})
    _run_jobvite(monkeypatch, api)
    assert api.json_calls[0][0] == JOBVITE_API


def test_jobvite_maps_fields(monkeypatch):
    api = FakeHTTP(json_routes={JOBVITE_API: {"jobs": [_jobvite_job()]}})
    posting = _run_jobvite(monkeypatch, api)[0]

    assert posting.source == "jobvite:acme"
    assert posting.source_id == "okiXcfwl"
    assert posting.title == "Tactical Strength Coach"
    assert posting.employer == "ACME Defense"
    assert posting.location == "Fayetteville, NC"
    assert posting.url == "https://careers.acmedefense.com/jobs/12345"
    assert posting.department == "Human Performance"
    assert (posting.posted_at.year, posting.posted_at.month, posting.posted_at.day) == (2026, 6, 30)
    assert posting.description == "", "the list response states no description"


def test_jobvite_location_falls_back_to_the_stated_country(monkeypatch):
    api = FakeHTTP(json_routes={JOBVITE_API: {"jobs": [_jobvite_job(location="")]}})
    assert _run_jobvite(monkeypatch, api)[0].location == "United States"


def test_jobvite_missing_date_stays_none(monkeypatch):
    api = FakeHTTP(json_routes={JOBVITE_API: {"jobs": [_jobvite_job(date=None)]}})
    assert _run_jobvite(monkeypatch, api)[0].posted_at is None


def test_jobvite_drops_untitled_and_unlinkable_records(monkeypatch):
    api = FakeHTTP(
        json_routes={
            JOBVITE_API: {
                "jobs": [
                    _jobvite_job(id="1", title=""),
                    _jobvite_job(id="2", applyURL="http://insecure.example.com/x"),
                    _jobvite_job(id="3", applyURL=None),
                    "not-a-dict",
                    _jobvite_job(id="4"),
                ]
            }
        }
    )
    postings = _run_jobvite(monkeypatch, api)
    assert [p.source_id for p in postings] == ["4"]


def test_jobvite_accepts_an_api_style_careers_url(monkeypatch):
    api = FakeHTTP(json_routes={JOBVITE_API: {"jobs": [_jobvite_job()]}})
    postings = _run_jobvite(monkeypatch, api, {"careers_url": JOBVITE_API})
    assert len(postings) == 1


def test_jobvite_rejects_a_foreign_host(monkeypatch):
    FakeHTTP().install(monkeypatch)
    with pytest.raises(ValueError):
        list(JobviteSource("x", {"careers_url": "https://jobs.lever.co/acme"}).fetch())


# ---------------------------------------------------------------------------
# Radancy
# ---------------------------------------------------------------------------

RADANCY_LIST = "https://careers.munichre.com/en/search-jobs"


def _radancy_modern_item(job_id, title, href, location):
    return (
        '<li class="search-results-list__item job-list-12-list__item">'
        f'<a class="search-results-list__job-link job-list-12-list__job-link" href="{href}" data-job-id="{job_id}">{title}</a>'
        '<ul><li class="search-results-list__job-info--location job-info"><i class="icon"></i>'
        f"<span>{location}</span></li></ul></li>"
    )


def _radancy_section(items, total_results, total_pages):
    return (
        f'<section id="search-results" data-total-results="{total_results}" data-total-pages="{total_pages}">'
        f"<ul>{''.join(items)}</ul></section>"
    )


def _fragment_page(url):
    match = re.search(r"CurrentPage=(\d+)", url)
    return int(match.group(1)) if match else None


def _run_radancy(monkeypatch, api, options=None):
    api.install(monkeypatch)
    merged = {"careers_url": RADANCY_LIST, "employer": "Munich Re", **(options or {})}
    return list(RadancySource("munichre", merged).fetch())


def test_radancy_prefers_the_fragment_endpoint_and_omits_the_filters_module(monkeypatch):
    def routes(url):
        assert url.startswith(f"{RADANCY_LIST}/results?")
        return {
            "filters": "",
            "hasJobs": True,
            "results": _radancy_section(
                [_radancy_modern_item(4711, "Senior Underwriter", "/en/job/muenchen/senior-underwriter/1234/4711", "München, Germany")],
                1,
                1,
            ),
        }

    api = FakeHTTP(json_routes=routes)
    postings = _run_radancy(monkeypatch, api)

    url = api.json_calls[0][0]
    # SearchResultsModuleName MUST be sent; SearchFiltersModuleName MUST NOT
    # (it re-attaches a multi-megabyte facet blob to every page).
    assert "SearchResultsModuleName=Search+Results" in url
    assert "SearchFiltersModuleName" not in url

    posting = postings[0]
    assert posting.source == "radancy:munichre"
    assert posting.source_id == "4711"
    assert posting.title == "Senior Underwriter"
    assert posting.location == "München, Germany"
    assert posting.url == "https://careers.munichre.com/en/job/muenchen/senior-underwriter/1234/4711"
    assert posting.posted_at is None, "the list markup states no date"
    assert posting.description == ""


def test_radancy_fragment_pagination_is_bounded_by_the_server_page_count(monkeypatch):
    def routes(url):
        page = _fragment_page(url)
        items = [
            _radancy_modern_item(page * 10 + i, f"Job {page * 10 + i}", f"/en/job/x/y/{page * 10 + i}", "Munich")
            for i in range(2)
        ]
        return {"results": _radancy_section(items, 4, 2)}

    api = FakeHTTP(json_routes=routes)
    postings = _run_radancy(monkeypatch, api)

    assert [_fragment_page(url) for url, _ in api.json_calls] == [1, 2]
    assert len(postings) == 4


def test_radancy_stated_zero_total_pages_stops_after_the_first_fragment(monkeypatch):
    """radancy.mjs uses `totalPages ?? maxPages`: a server-STATED total of 0
    means no more pages -- it must not be treated like a missing total and
    restart a walk to the local cap."""

    def routes(url):
        assert _fragment_page(url) == 1, "no page past 1 may be requested"
        items = [_radancy_modern_item(1, "Coach", "/en/job/a/1", "Munich")]
        return {"results": _radancy_section(items, 1, 0)}

    api = FakeHTTP(json_routes=routes)
    postings = _run_radancy(monkeypatch, api)

    assert [_fragment_page(url) for url, _ in api.json_calls] == [1]
    assert [p.source_id for p in postings] == ["1"]


def test_radancy_missing_total_pages_still_walks_to_the_next_page(monkeypatch):
    """A fragment WITHOUT data-total-pages falls back to the local cap, so
    pagination continues until an empty page (the mjs `??` fallback arm)."""

    def routes(url):
        page = _fragment_page(url)
        if page == 1:
            return {"results": "<ul>" + _radancy_modern_item(1, "Coach A", "/en/job/a/1", "Munich") + "</ul>"}
        if page == 2:
            return {"results": "<ul>" + _radancy_modern_item(2, "Coach B", "/en/job/b/2", "Hamburg") + "</ul>"}
        return {"results": ""}

    api = FakeHTTP(json_routes=routes)
    postings = _run_radancy(monkeypatch, api)

    assert [p.source_id for p in postings] == ["1", "2"]
    assert [_fragment_page(url) for url, _ in api.json_calls] == [1, 2, 3]


def test_radancy_falls_back_to_the_html_walk_when_the_fragment_fails(monkeypatch):
    api = FakeHTTP(
        json_routes=lambda url: FetchError("HTTP 500"),
        text={
            f"{RADANCY_LIST}?p=1": "<ul>"
            + _radancy_modern_item(1, "Coach A", "/en/job/a/1", "Munich")
            + _radancy_modern_item(2, "Coach B", "/en/job/b/2", "Hamburg")
            + "</ul>",
            f"{RADANCY_LIST}?p=2": "<div>past the last page</div>",
        },
    )
    postings = _run_radancy(monkeypatch, api)
    assert [p.source_id for p in postings] == ["1", "2"]


def test_radancy_parses_the_legacy_markup_without_phantom_rows(monkeypatch):
    legacy = (
        '<li><a href="/job/tampa-fl/performance-coach/1234/98765" data-job-id="98765">'
        "<h2>Performance Coach</h2>"
        '<span class="job-id job-info">R-12345</span>'
        '<span class="job-location">Tampa, FL</span>'
        '</a><button class="js-save-job-btn" data-job-id="98765">Save</button></li>'
    )
    api = FakeHTTP(json_routes=lambda url: {"results": f'<section id="search-results" data-total-results="1" data-total-pages="1"><ul>{legacy}</ul></section>'})
    postings = _run_radancy(monkeypatch, api)

    assert len(postings) == 1, "the save-job button repeats data-job-id but is not a row"
    posting = postings[0]
    assert posting.source_id == "98765"
    assert posting.title == "Performance Coach", "req-number and location spans stay out of the title"
    assert posting.location == "Tampa, FL"
    assert posting.url == "https://careers.munichre.com/job/tampa-fl/performance-coach/1234/98765"


def test_radancy_html_walk_stops_when_the_server_clamps_the_page(monkeypatch):
    page = "<ul>" + _radancy_modern_item(1, "Coach", "/en/job/a/1", "Munich") + "</ul>"
    api = FakeHTTP(
        json_routes=lambda url: FetchError("HTTP 404"),
        text={f"{RADANCY_LIST}?p=1": page, f"{RADANCY_LIST}?p=2": page},
    )
    postings = _run_radancy(monkeypatch, api)
    assert len(postings) == 1
    assert len(api.text_calls) == 2


def test_radancy_max_jobs_caps_the_yield(monkeypatch):
    items = [_radancy_modern_item(i, f"Job {i}", f"/en/job/x/{i}", "Munich") for i in range(5)]
    api = FakeHTTP(json_routes=lambda url: {"results": _radancy_section(items, 5, 1)})
    postings = _run_radancy(monkeypatch, api, {"max_jobs": 2})
    assert len(postings) == 2


def test_radancy_derives_the_search_url_from_a_branded_careers_url(monkeypatch):
    def routes(url):
        assert url.startswith("https://karriere.example.com/de/search-jobs/results?")
        return {"results": _radancy_section([_radancy_modern_item(9, "Koch", "/de/job/k/9", "Berlin")], 1, 1)}

    api = FakeHTTP(json_routes=routes)
    postings = _run_radancy(monkeypatch, api, {"careers_url": "https://karriere.example.com/de/irgendwas"})
    assert len(postings) == 1
    assert postings[0].url == "https://karriere.example.com/de/job/k/9"


# ---------------------------------------------------------------------------
# exports: every candidate vendor was ported, none skipped
# ---------------------------------------------------------------------------


def test_export_tuple_covers_every_ported_vendor_once():
    assert ENTERPRISE_SOURCES == (
        ICIMSSource,
        SuccessFactorsSource,
        CornerstoneSource,
        OracleCloudSource,
        JobviteSource,
        RadancySource,
    )
    kinds = [cls.kind for cls in ENTERPRISE_SOURCES]
    assert len(kinds) == len(set(kinds)), "kinds must be unique for the registry"
    assert all(issubclass(cls, Source) for cls in ENTERPRISE_SOURCES)


def test_no_candidate_vendor_was_skipped():
    """All six career-ops recipes are public and keyless (CSOD's bearer token
    is an anonymous JWT embedded in the public page, not a credential), so
    all six are ported. If one is ever removed, that must be a recorded
    decision -- update this test with the reason."""
    assert {cls.kind for cls in ENTERPRISE_SOURCES} == {
        "icims",
        "successfactors",
        "csod",
        "oraclecloud",
        "jobvite",
        "radancy",
    }
