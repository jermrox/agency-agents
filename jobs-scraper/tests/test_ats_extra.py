"""Mapping tests for the second-tier ATS adapters.

Every test here runs against a captured payload shape rather than the live
vendor API, so the suite stays meaningful in CI and in a sandbox with no
outbound network. The transport helper is replaced *as imported into the
adapter module*, which is the only seam these adapters have.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from tactical_jobs.http import FetchError  # noqa: E402
from tactical_jobs.sources.ats_extra import (  # noqa: E402
    ATS_EXTRA_SOURCES,
    BambooHRSource,
    BreezySource,
    JazzHRSource,
    PersonioSource,
    RipplingSource,
    TeamtailorSource,
)

MODULE = "tactical_jobs.sources.ats_extra"


class Recorder:
    """A stand-in for ``fetch_json``/``fetch`` that logs every call.

    Routing is by substring so a test can describe a list endpoint and a
    detail endpoint in one dict and still assert on call counts.
    """

    def __init__(self, routes: dict[str, object], default: object = None) -> None:
        self.routes = routes
        self.default = default
        self.calls: list[tuple[str, dict]] = []

    def __call__(self, url: str, **kwargs: object) -> object:
        self.calls.append((url, kwargs))
        for fragment, payload in self.routes.items():
            if fragment in url:
                if isinstance(payload, Exception):
                    raise payload
                return payload
        if isinstance(self.default, Exception):
            raise self.default
        return self.default

    @property
    def urls(self) -> list[str]:
        return [url for url, _ in self.calls]


# ---------------------------------------------------------------------------
# BambooHR
# ---------------------------------------------------------------------------

BAMBOO_LIST = {
    "result": [
        {
            "id": 4821,
            "jobOpeningName": "Tactical Strength and Conditioning Coach",
            "location": {"city": "Fayetteville", "state": "North Carolina"},
            "employmentStatusLabel": "Full-Time",
            "departmentLabel": "Human Performance",
        }
    ]
}

BAMBOO_DETAIL = {
    "result": {
        "jobOpening": {
            "description": (
                "<p>Embed with a USASOC THOR3 team at Fort Bragg.</p>"
                "<ul><li>CSCS required</li><li>Secret clearance required</li></ul>"
            ),
            "compensation": "$85,000 - $95,000 per year",
            "datePosted": "2026-07-05",
        }
    }
}


def _bamboo(monkeypatch, routes, **options):
    recorder = Recorder(routes)
    monkeypatch.setattr(f"{MODULE}.fetch_json", recorder)
    source = BambooHRSource("thor3", {"subdomain": "acme", **options})
    return list(source.fetch()), recorder


def test_bamboohr_maps_core_fields(monkeypatch):
    postings, _ = _bamboo(
        monkeypatch,
        {"/list": BAMBOO_LIST, "/detail": BAMBOO_DETAIL},
        employer="Acme Performance",
    )
    assert len(postings) == 1
    posting = postings[0]
    assert posting.source == "bamboohr:thor3"
    assert posting.source_id == "4821"
    assert posting.url == "https://acme.bamboohr.com/careers/4821"
    assert posting.title == "Tactical Strength and Conditioning Coach"
    assert posting.employer == "Acme Performance"
    assert posting.location == "Fayetteville, North Carolina"
    assert posting.department == "Human Performance"


def test_bamboohr_fetches_the_detail_endpoint_for_the_description(monkeypatch):
    """The list endpoint has no description; without the detail call this
    adapter would ship a title and nothing the enrichment layer can mine."""
    postings, recorder = _bamboo(
        monkeypatch, {"/list": BAMBOO_LIST, "/detail": BAMBOO_DETAIL}
    )
    description = postings[0].description
    assert "https://acme.bamboohr.com/careers/4821/detail" in recorder.urls
    assert "THOR3" in description
    assert "CSCS" in description
    assert "Secret clearance" in description
    # Block tags become separators rather than gluing words together.
    assert "BraggCSCS" not in description
    # ...and the markup itself is gone, not merely reformatted.
    assert "<p>" not in description and "<li>" not in description


def test_bamboohr_reads_compensation_and_posted_at_from_the_detail(monkeypatch):
    postings, _ = _bamboo(
        monkeypatch, {"/list": BAMBOO_LIST, "/detail": BAMBOO_DETAIL}
    )
    posting = postings[0]
    assert posting.compensation == "$85,000 - $95,000 per year"
    assert posting.posted_at is not None
    assert posting.posted_at.year == 2026


def test_bamboohr_folds_structured_fields_into_the_text(monkeypatch):
    postings, _ = _bamboo(
        monkeypatch, {"/list": BAMBOO_LIST, "/detail": BAMBOO_DETAIL}
    )
    description = postings[0].description
    assert "Department: Human Performance." in description
    assert "Employment type: Full-Time." in description


def test_bamboohr_detail_limit_bounds_the_fan_out(monkeypatch):
    listing = {
        "result": [
            {"id": i, "jobOpeningName": f"Coach {i}", "location": {"city": "Tampa"}}
            for i in range(1, 4)
        ]
    }
    postings, recorder = _bamboo(
        monkeypatch, {"/list": listing, "/detail": BAMBOO_DETAIL}, detail_limit=1
    )
    # Every posting still comes back; only the detail fan-out is capped.
    assert len(postings) == 3
    assert sum(1 for url in recorder.urls if url.endswith("/detail")) == 1
    assert "THOR3" in postings[0].description
    assert postings[1].title == "Coach 2"


def test_bamboohr_keeps_the_posting_when_the_detail_call_fails(monkeypatch):
    postings, _ = _bamboo(
        monkeypatch,
        {"/list": BAMBOO_LIST, "/detail": FetchError("HTTP 503")},
    )
    posting = postings[0]
    assert posting.title == "Tactical Strength and Conditioning Coach"
    # Degraded to list-level fields rather than dropped.
    assert "Tactical Strength and Conditioning Coach" in posting.description
    assert "Location: Fayetteville, North Carolina." in posting.description
    assert posting.compensation is None


def test_bamboohr_skips_malformed_records_without_losing_good_ones(monkeypatch):
    listing = {
        "result": [
            "not-an-object",
            {"jobOpeningName": "No id here"},
            BAMBOO_LIST["result"][0],
        ]
    }
    postings, _ = _bamboo(monkeypatch, {"/list": listing, "/detail": BAMBOO_DETAIL})
    assert [p.source_id for p in postings] == ["4821"]


def test_bamboohr_detects_a_remote_location(monkeypatch):
    listing = {
        "result": [
            {
                "id": 9,
                "jobOpeningName": "Cognitive Performance Specialist",
                "location": {"city": "Remote", "state": "US"},
            }
        ]
    }
    postings, _ = _bamboo(monkeypatch, {"/list": listing, "/detail": BAMBOO_DETAIL})
    assert postings[0].remote is True


def test_bamboohr_requires_a_subdomain():
    with pytest.raises(KeyError):
        list(BambooHRSource("thor3", {}).fetch())


def test_bamboohr_tolerates_a_non_numeric_detail_limit(monkeypatch):
    """A hand-edited TOML can leave ``detail_limit`` blank or quoted. A bad
    value for a safety rail must not take the whole board offline."""
    for bad in (None, "", "lots"):
        postings, recorder = _bamboo(
            monkeypatch,
            {"/list": BAMBOO_LIST, "/detail": BAMBOO_DETAIL},
            detail_limit=bad,
        )
        assert len(postings) == 1
        # Fell back to the default budget, so the detail call still happened.
        assert any(url.endswith("/detail") for url in recorder.urls)
        assert "CSCS" in postings[0].description


def test_bamboohr_accepts_a_detail_limit_given_as_a_string(monkeypatch):
    postings, recorder = _bamboo(
        monkeypatch, {"/list": BAMBOO_LIST, "/detail": BAMBOO_DETAIL}, detail_limit="1"
    )
    assert len(postings) == 1
    assert sum(1 for url in recorder.urls if url.endswith("/detail")) == 1


# ---------------------------------------------------------------------------
# Breezy
# ---------------------------------------------------------------------------

BREEZY_JOBS = [
    {
        "id": "5f2c9a",
        "name": "Athletic Trainer (POTFF)",
        "description": "<p>Support SOCOM operators.</p><ul><li>ATC required</li></ul>",
        "location": {
            "name": "Fort Campbell, KY",
            "city": "Fort Campbell",
            "country": {"id": "US", "name": "United States"},
        },
        "type": {"name": "Full-Time"},
        "department": "Sports Medicine",
        "published_date": "2026-06-18T14:22:31.000Z",
        "url": "https://acme.breezy.hr/p/5f2c9a-athletic-trainer",
    }
]


def _breezy(monkeypatch, payload, **options):
    recorder = Recorder({}, default=payload)
    monkeypatch.setattr(f"{MODULE}.fetch_json", recorder)
    source = BreezySource("acme", {"company": "acme", **options})
    return list(source.fetch()), recorder


def test_breezy_maps_core_fields(monkeypatch):
    postings, recorder = _breezy(monkeypatch, BREEZY_JOBS, employer="Acme")
    assert recorder.urls == ["https://acme.breezy.hr/json"]
    posting = postings[0]
    assert posting.source == "breezy:acme"
    assert posting.source_id == "5f2c9a"
    assert posting.title == "Athletic Trainer (POTFF)"
    assert posting.employer == "Acme"
    assert posting.location == "Fort Campbell, KY"
    assert posting.department == "Sports Medicine"
    assert posting.url.endswith("/p/5f2c9a-athletic-trainer")
    assert "ATC required" in posting.description
    assert "operators.ATC" not in posting.description
    assert "<p>" not in posting.description and "<li>" not in posting.description


def test_breezy_parses_the_published_date(monkeypatch):
    posting = _breezy(monkeypatch, BREEZY_JOBS)[0][0]
    assert posting.posted_at is not None
    assert (posting.posted_at.year, posting.posted_at.month) == (2026, 6)


def test_breezy_assembles_a_location_when_the_display_name_is_missing(monkeypatch):
    payload = [
        {
            "id": "1",
            "name": "Performance Dietitian",
            "location": {"city": "Coronado", "state": "CA", "country": {"name": "United States"}},
        }
    ]
    posting = _breezy(monkeypatch, payload)[0][0]
    assert posting.location == "Coronado, CA, United States"


def test_breezy_honors_the_remote_flag(monkeypatch):
    """The flag has to carry the decision on its own.

    The location text is deliberately one that ``looks_remote`` would reject,
    so this fails if the adapter stops reading ``is_remote``.
    """
    flagged = [
        {
            "id": "2",
            "name": "Cognitive Performance Specialist",
            "location": {"name": "Coronado, CA", "is_remote": True},
        }
    ]
    unflagged = [
        {
            "id": "3",
            "name": "Cognitive Performance Specialist",
            "location": {"name": "Coronado, CA"},
        }
    ]
    assert _breezy(monkeypatch, flagged)[0][0].remote is True
    assert _breezy(monkeypatch, unflagged)[0][0].remote is False


def test_breezy_builds_a_url_when_the_record_omits_one(monkeypatch):
    payload = [{"id": "abc", "name": "Strength Coach"}]
    assert _breezy(monkeypatch, payload)[0][0].url == "https://acme.breezy.hr/p/abc"


def test_breezy_handles_unicode_and_entities(monkeypatch):
    payload = [
        {
            "id": "unicode-1",
            "name": "Physiologiste de la performance",
            "description": "<p>Café &amp; naïve — CSCS requis</p>",
            "location": {"name": "Québec"},
        }
    ]
    posting = _breezy(monkeypatch, payload)[0][0]
    assert posting.title == "Physiologiste de la performance"
    assert posting.location == "Québec"
    assert "Café & naïve" in posting.description


def test_breezy_tolerates_a_record_of_all_nulls(monkeypatch):
    payload = [
        {
            "id": "n1",
            "name": None,
            "description": None,
            "location": None,
            "type": None,
            "department": None,
            "published_date": None,
            "url": None,
        }
    ]
    posting = _breezy(monkeypatch, payload)[0][0]
    assert posting.title == ""
    assert posting.location == ""
    assert posting.department is None
    assert posting.posted_at is None
    assert posting.url == "https://acme.breezy.hr/p/n1"


def test_breezy_skips_malformed_records(monkeypatch):
    payload = [{"name": "No id"}, None, BREEZY_JOBS[0]]
    postings, _ = _breezy(monkeypatch, payload)
    assert [p.source_id for p in postings] == ["5f2c9a"]


# ---------------------------------------------------------------------------
# JazzHR
# ---------------------------------------------------------------------------

JAZZHR_JOBS = [
    {
        "id": "j3k9x2",
        "title": "Human Performance Program Manager",
        "description": "<p>Lead an Army H2F team.</p><p>TSAC-F preferred.</p>",
        "city": "Fort Carson",
        "state": "CO",
        "department": "Holistic Health and Fitness",
        "original_open_date": "2026-05-02",
        "status": "Open",
    }
]


def _jazzhr(monkeypatch, payload, **options):
    recorder = Recorder({}, default=payload)
    monkeypatch.setattr(f"{MODULE}.fetch_json", recorder)
    source = JazzHRSource("acme", {"api_key": "secret-key", "board": "acmehp", **options})
    return list(source.fetch()), recorder


def test_jazzhr_maps_core_fields(monkeypatch):
    postings, _ = _jazzhr(monkeypatch, JAZZHR_JOBS, employer="Acme")
    posting = postings[0]
    assert posting.source == "jazzhr:acme"
    assert posting.source_id == "j3k9x2"
    assert posting.title == "Human Performance Program Manager"
    assert posting.location == "Fort Carson, CO"
    assert posting.department == "Holistic Health and Fitness"
    assert posting.posted_at is not None
    assert "H2F" in posting.description and "TSAC-F" in posting.description


def test_jazzhr_builds_the_public_apply_url(monkeypatch):
    posting = _jazzhr(monkeypatch, JAZZHR_JOBS)[0][0]
    assert posting.url == "https://acmehp.applytojob.com/apply/j3k9x2"


def test_jazzhr_sends_the_api_key_as_a_query_parameter(monkeypatch):
    _, recorder = _jazzhr(monkeypatch, JAZZHR_JOBS)
    url, kwargs = recorder.calls[0]
    assert url == "https://api.resumatorapi.com/v1/jobs"
    assert kwargs["params"] == {"apikey": "secret-key"}


def test_jazzhr_slugifies_a_board_derived_from_a_display_name(monkeypatch):
    """The board slug is interpolated into a hostname.

    Without slugifying, an employer name falls straight through and the
    pipeline publishes ``https://Acme Performance Group.applytojob.com/...``,
    which passes the "has a url" check and is unopenable.
    """
    recorder = Recorder({}, default=JAZZHR_JOBS)
    monkeypatch.setattr(f"{MODULE}.fetch_json", recorder)
    source = JazzHRSource(
        "acme", {"api_key": "k", "employer": "Acme Performance Group"}
    )
    posting = list(source.fetch())[0]
    assert posting.url == "https://acme-performance-group.applytojob.com/apply/j3k9x2"
    # The employer label itself is untouched -- only the host is normalized.
    assert posting.employer == "Acme Performance Group"


def test_jazzhr_url_host_is_always_legal(monkeypatch):
    recorder = Recorder({}, default=JAZZHR_JOBS)
    monkeypatch.setattr(f"{MODULE}.fetch_json", recorder)
    for name, options in (
        ("Acme HP", {"api_key": "k"}),
        ("acme", {"api_key": "k", "board": "Acme_HP"}),
        ("acme", {"api_key": "k", "board": "https://acmehp.applytojob.com/"}),
    ):
        url = list(JazzHRSource(name, options).fetch())[0].url
        host = url.split("//", 1)[1].split("/", 1)[0]
        assert " " not in host and host == host.lower(), url
        assert host.endswith(".applytojob.com")
        assert not host.startswith(".")


def test_jazzhr_board_option_beats_the_employer_name(monkeypatch):
    recorder = Recorder({}, default=JAZZHR_JOBS)
    monkeypatch.setattr(f"{MODULE}.fetch_json", recorder)
    source = JazzHRSource("acme", {"api_key": "k", "board": "acmehp", "employer": "Acme Inc"})
    assert list(source.fetch())[0].url.startswith("https://acmehp.applytojob.com/")


def test_jazzhr_drops_jobs_that_are_not_open(monkeypatch):
    payload = [
        {"id": "a", "title": "Closed role", "status": "Closed"},
        {"id": "b", "title": "Filled role", "status": "Filled"},
        {"id": "c", "title": "Draft role", "status": "Draft"},
        {"id": "d", "title": "Open role", "status": "Open"},
        {"id": "e", "title": "Active role", "status": "active"},
    ]
    postings, _ = _jazzhr(monkeypatch, payload)
    assert [p.source_id for p in postings] == ["d", "e"]


def test_jazzhr_keeps_a_record_with_no_status_field(monkeypatch):
    """A missing field is not evidence that a requisition closed."""
    postings, _ = _jazzhr(monkeypatch, [{"id": "z", "title": "Strength Coach"}])
    assert [p.source_id for p in postings] == ["z"]


def test_jazzhr_handles_a_single_record_response(monkeypatch):
    """The API returns a lone object, not an array, for a one-job board."""
    postings, _ = _jazzhr(monkeypatch, JAZZHR_JOBS[0])
    assert [p.source_id for p in postings] == ["j3k9x2"]


def test_jazzhr_skips_malformed_records(monkeypatch):
    payload = [{"title": "No id", "status": "Open"}, 42, JAZZHR_JOBS[0]]
    postings, _ = _jazzhr(monkeypatch, payload)
    assert [p.source_id for p in postings] == ["j3k9x2"]


# ---------------------------------------------------------------------------
# Teamtailor
# ---------------------------------------------------------------------------


def _teamtailor_job(job_id: str, title: str, **attributes: object) -> dict:
    base = {
        "title": title,
        "body": "<p>Embed with a Naval Special Warfare team.</p><p>CSCS required.</p>",
        "created-at": "2026-04-11T09:00:00+00:00",
        "careersite-job-url": f"https://acme.teamtailor.com/jobs/{job_id}",
        "remote-status": "none",
    }
    base.update(attributes)
    return {"id": job_id, "type": "jobs", "attributes": base}


TEAMTAILOR_PAGE = {
    "data": [
        {
            **_teamtailor_job("11", "Strength and Conditioning Coach", pitch="THOR3 support"),
            "relationships": {
                "locations": {"data": [{"type": "locations", "id": "7"}]},
                "department": {"data": {"type": "departments", "id": "3"}},
            },
        }
    ],
    "included": [
        {"type": "locations", "id": "7", "attributes": {"name": "Coronado, CA"}},
        {"type": "departments", "id": "3", "attributes": {"name": "Human Performance"}},
    ],
    "links": {},
}


def _teamtailor(monkeypatch, pages, **options):
    """Serve ``pages`` in order, one per request."""
    queue = list(pages)

    class PageRecorder(Recorder):
        def __call__(self, url: str, **kwargs: object) -> object:
            self.calls.append((url, kwargs))
            return queue.pop(0) if queue else {"data": []}

    recorder = PageRecorder({})
    monkeypatch.setattr(f"{MODULE}.fetch_json", recorder)
    source = TeamtailorSource("acme", {"api_key": "tt-key", **options})
    return list(source.fetch()), recorder


def test_teamtailor_maps_core_fields(monkeypatch):
    postings, _ = _teamtailor(monkeypatch, [TEAMTAILOR_PAGE], employer="Acme")
    posting = postings[0]
    assert posting.source == "teamtailor:acme"
    assert posting.source_id == "11"
    assert posting.title == "Strength and Conditioning Coach"
    assert posting.employer == "Acme"
    assert posting.url == "https://acme.teamtailor.com/jobs/11"
    assert posting.posted_at is not None and posting.posted_at.year == 2026
    assert "Naval Special Warfare" in posting.description
    assert "THOR3 support" in posting.description  # the pitch must not be dropped
    assert "<p>" not in posting.description


def test_teamtailor_sends_the_documented_auth_headers(monkeypatch):
    _, recorder = _teamtailor(monkeypatch, [TEAMTAILOR_PAGE])
    _, kwargs = recorder.calls[0]
    headers = kwargs["headers"]
    assert headers["Authorization"] == "Token token=tt-key"
    assert headers["X-Api-Version"] == "20210218"


def test_teamtailor_resolves_side_loaded_locations_and_departments(monkeypatch):
    """Location and department are JSON:API relationships, not attributes."""
    posting = _teamtailor(monkeypatch, [TEAMTAILOR_PAGE])[0][0]
    assert posting.location == "Coronado, CA"
    assert posting.department == "Human Performance"


def test_teamtailor_follows_the_next_link(monkeypatch):
    page_one = {
        "data": [_teamtailor_job("1", "Coach One")],
        "links": {"next": "https://api.teamtailor.com/v1/jobs?page[number]=2"},
    }
    page_two = {
        "data": [_teamtailor_job("2", "Coach Two"), _teamtailor_job("3", "Coach Three")],
        "links": {},
    }
    postings, recorder = _teamtailor(monkeypatch, [page_one, page_two])
    assert [p.source_id for p in postings] == ["1", "2", "3"]
    assert recorder.urls[1] == "https://api.teamtailor.com/v1/jobs?page[number]=2"
    # The cursor already carries the query string, so params are not re-sent.
    assert recorder.calls[1][1]["params"] is None


def test_teamtailor_stops_at_max_pages(monkeypatch):
    pages = [
        {
            "data": [_teamtailor_job(str(n), f"Coach {n}")],
            "links": {"next": f"https://api.teamtailor.com/v1/jobs?page[number]={n + 1}"},
        }
        for n in range(1, 5)
    ]
    postings, recorder = _teamtailor(monkeypatch, pages, max_pages=2)
    assert len(recorder.calls) == 2
    assert [p.source_id for p in postings] == ["1", "2"]


def test_teamtailor_stops_when_next_points_at_the_current_page(monkeypatch):
    self_referential = {
        "data": [_teamtailor_job("1", "Coach One")],
        "links": {"next": "https://api.teamtailor.com/v1/jobs"},
    }
    _, recorder = _teamtailor(
        monkeypatch, [self_referential, self_referential], max_pages=5
    )
    assert len(recorder.calls) == 1


def test_teamtailor_resolves_a_relative_next_link(monkeypatch):
    """``next`` is sometimes served as a path.

    Handing a bare path to urllib raises "unknown url type", which would look
    like a flaky cursor and silently truncate the board at page one.
    """
    page_one = {
        "data": [_teamtailor_job("1", "Coach One")],
        "links": {"next": "/v1/jobs?page%5Bnumber%5D=2"},
    }
    page_two = {"data": [_teamtailor_job("2", "Coach Two")], "links": {}}
    postings, recorder = _teamtailor(monkeypatch, [page_one, page_two])
    assert [p.source_id for p in postings] == ["1", "2"]
    assert recorder.urls[1] == "https://api.teamtailor.com/v1/jobs?page%5Bnumber%5D=2"


def test_teamtailor_reads_a_lone_data_object(monkeypatch):
    """JSON:API allows a single resource object rather than a one-item array."""
    page = {"data": _teamtailor_job("42", "Sole Coach"), "links": {}}
    postings, _ = _teamtailor(monkeypatch, [page])
    assert [p.source_id for p in postings] == ["42"]
    assert postings[0].title == "Sole Coach"


def test_teamtailor_falls_back_to_the_record_level_careersite_link(monkeypatch):
    """Some API versions put the public link in the resource's ``links``.

    A posting with an empty url is discarded by the pipeline, so missing this
    fallback loses the job entirely.
    """
    record = {
        "id": "77",
        "type": "jobs",
        "attributes": {"title": "Coach", "body": "<p>H2F.</p>"},
        "links": {
            "self": "https://api.teamtailor.com/v1/jobs/77",
            "careersite-job-url": "https://acme.teamtailor.com/jobs/77-coach",
        },
    }
    postings, _ = _teamtailor(monkeypatch, [{"data": [record], "links": {}}])
    assert postings[0].url == "https://acme.teamtailor.com/jobs/77-coach"


def test_teamtailor_never_uses_the_api_self_link_as_the_public_url(monkeypatch):
    record = {
        "id": "78",
        "type": "jobs",
        "attributes": {"title": "Coach"},
        "links": {"self": "https://api.teamtailor.com/v1/jobs/78"},
    }
    postings, _ = _teamtailor(monkeypatch, [{"data": [record], "links": {}}])
    assert "api.teamtailor.com" not in postings[0].url


def test_teamtailor_tolerates_a_non_numeric_max_pages(monkeypatch):
    pages = [
        {
            "data": [_teamtailor_job(str(n), f"Coach {n}")],
            "links": {"next": f"https://api.teamtailor.com/v1/jobs?page[number]={n + 1}"},
        }
        for n in range(1, 4)
    ]
    postings, recorder = _teamtailor(monkeypatch, list(pages), max_pages=None)
    assert [p.source_id for p in postings] == ["1", "2", "3"]
    postings, _ = _teamtailor(monkeypatch, list(pages), max_pages="2")
    assert [p.source_id for p in postings] == ["1", "2"]


def test_teamtailor_reads_remote_status(monkeypatch):
    pages = [
        {
            "data": [
                _teamtailor_job("1", "Remote Coach", **{"remote-status": "fully"}),
                _teamtailor_job("2", "Hybrid Coach", **{"remote-status": "hybrid"}),
            ],
            "links": {},
        }
    ]
    postings, _ = _teamtailor(monkeypatch, pages)
    assert postings[0].remote is True
    # "hybrid" is on-site work with flexibility, not a remote job.
    assert postings[1].remote is False


def test_teamtailor_skips_unpublished_and_malformed_records(monkeypatch):
    pages = [
        {
            "data": [
                _teamtailor_job("1", "Draft Coach", status="draft"),
                _teamtailor_job("2", "Archived Coach", status="archived"),
                {"type": "jobs", "attributes": {"title": "No id"}},
                "not-an-object",
                _teamtailor_job("5", "Live Coach", status="published"),
            ],
            "links": {},
        }
    ]
    postings, _ = _teamtailor(monkeypatch, pages)
    assert [p.source_id for p in postings] == ["5"]


def test_teamtailor_retries_without_the_side_loading_query(monkeypatch):
    """A tenant that rejects ``include`` must still yield postings."""
    sent: list[object] = []

    def picky(url: str, **kwargs: object):
        sent.append(kwargs.get("params"))
        if kwargs.get("params"):
            raise FetchError("HTTP 400 unsupported include")
        return {"data": [_teamtailor_job("1", "Coach One")], "links": {}}

    monkeypatch.setattr(f"{MODULE}.fetch_json", picky)
    postings = list(TeamtailorSource("acme", {"api_key": "tt-key"}).fetch())
    assert [p.source_id for p in postings] == ["1"]
    assert len(sent) == 2 and sent[1] is None


def test_teamtailor_raises_when_the_first_page_fails(monkeypatch):
    """A dead first page is a broken key, not a flaky cursor."""

    def boom(*args, **kwargs):
        raise FetchError("HTTP 401")

    monkeypatch.setattr(f"{MODULE}.fetch_json", boom)
    with pytest.raises(FetchError):
        list(TeamtailorSource("acme", {"api_key": "bad"}).fetch())


def test_teamtailor_keeps_the_first_page_when_a_later_page_fails(monkeypatch):
    page_one = {
        "data": [_teamtailor_job("1", "Coach One")],
        "links": {"next": "https://api.teamtailor.com/v1/jobs?page[number]=2"},
    }
    calls: list[str] = []

    def flaky(url: str, **kwargs: object):
        calls.append(url)
        if len(calls) == 1:
            return page_one
        raise FetchError("HTTP 503")

    monkeypatch.setattr(f"{MODULE}.fetch_json", flaky)
    postings = list(TeamtailorSource("acme", {"api_key": "tt-key"}).fetch())
    assert [p.source_id for p in postings] == ["1"]


# ---------------------------------------------------------------------------
# Personio
# ---------------------------------------------------------------------------

PERSONIO_XML = """<?xml version="1.0" encoding="utf-8"?>
<workzag-jobs>
  <position>
    <id>2054871</id>
    <name>Performance Dietitian (H2F)</name>
    <office>Fort Liberty, NC</office>
    <department>Human Performance</department>
    <employmentType>FULL_TIME</employmentType>
    <schedule>full-time</schedule>
    <seniority>experienced</seniority>
    <createdAt>2026-03-09T08:15:00+00:00</createdAt>
    <jobDescriptions>
      <jobDescription>
        <name>Your mission</name>
        <value>&lt;p&gt;Feed an Army H2F brigade.&lt;/p&gt;</value>
      </jobDescription>
      <jobDescription>
        <name>Your profile</name>
        <value>&lt;ul&gt;&lt;li&gt;RD credential required&lt;/li&gt;&lt;li&gt;CSSD preferred&lt;/li&gt;&lt;/ul&gt;</value>
      </jobDescription>
      <jobDescription>
        <name>Why us?</name>
        <value>Secret clearance sponsored.</value>
      </jobDescription>
    </jobDescriptions>
  </position>
</workzag-jobs>
"""


def _personio(monkeypatch, xml: str, **options):
    recorder = Recorder({}, default=xml.encode())
    monkeypatch.setattr(f"{MODULE}.fetch", recorder)
    source = PersonioSource("acme", {"company": "acme", **options})
    return list(source.fetch()), recorder


def test_personio_maps_core_fields(monkeypatch):
    postings, recorder = _personio(monkeypatch, PERSONIO_XML, employer="Acme")
    assert recorder.urls == ["https://acme.jobs.personio.de/xml"]
    posting = postings[0]
    assert posting.source == "personio:acme"
    assert posting.source_id == "2054871"
    assert posting.title == "Performance Dietitian (H2F)"
    assert posting.employer == "Acme"
    assert posting.location == "Fort Liberty, NC"
    assert posting.department == "Human Performance"
    assert posting.url == "https://acme.jobs.personio.de/job/2054871"
    assert posting.posted_at is not None and posting.posted_at.year == 2026


def test_personio_concatenates_every_job_description_section(monkeypatch):
    """Certifications live in "Your profile"; reading only the first section
    would blind the enrichment layer to most of what it exists to extract."""
    description = _personio(monkeypatch, PERSONIO_XML)[0][0].description
    for needle in ("Feed an Army H2F brigade", "RD credential", "CSSD", "Secret clearance"):
        assert needle in description, f"missing {needle!r}"
    assert "Your mission" in description and "Your profile" in description
    assert description.index("Feed an Army") < description.index("RD credential")


def test_personio_flattens_html_inside_a_section(monkeypatch):
    description = _personio(monkeypatch, PERSONIO_XML)[0][0].description
    assert "<p>" not in description and "<li>" not in description
    assert "requiredCSSD" not in description


def test_personio_folds_structured_fields_into_the_text(monkeypatch):
    description = _personio(monkeypatch, PERSONIO_XML)[0][0].description
    assert "Employment type: Full Time." in description
    assert "Department: Human Performance." in description


def test_personio_flags_a_remote_office(monkeypatch):
    xml = PERSONIO_XML.replace("<office>Fort Liberty, NC</office>", "<office>Remote</office>")
    assert _personio(monkeypatch, xml)[0][0].remote is True
    assert _personio(monkeypatch, PERSONIO_XML)[0][0].remote is False


def test_personio_skips_a_position_missing_its_identity(monkeypatch):
    xml = """<workzag-jobs>
      <position><name>No id</name></position>
      <position><id>7</id></position>
      <position><id>9</id><name>Strength Coach</name><office>Tampa, FL</office></position>
    </workzag-jobs>"""
    postings, _ = _personio(monkeypatch, xml)
    assert [p.source_id for p in postings] == ["9"]


def test_personio_keeps_the_raw_sections(monkeypatch):
    raw = _personio(monkeypatch, PERSONIO_XML)[0][0].raw
    assert raw["office"] == "Fort Liberty, NC"
    assert [section["name"] for section in raw["jobDescriptions"]] == [
        "Your mission",
        "Your profile",
        "Why us?",
    ]


def test_personio_tolerates_an_empty_section_and_unicode(monkeypatch):
    xml = (
        "<workzag-jobs><position><id>3</id><name>Physiologiste</name>"
        "<office>Québec</office><jobDescriptions>"
        "<jobDescription><name>Empty</name></jobDescription>"
        "<jobDescription><name>Profil</name><value>&lt;p&gt;CSCS requis&lt;/p&gt;</value>"
        "</jobDescription></jobDescriptions></position></workzag-jobs>"
    )
    posting = _personio(monkeypatch, xml)[0][0]
    assert posting.location == "Québec"
    assert "CSCS requis" in posting.description
    # The empty section contributes no stray heading.
    assert "Empty" not in posting.description


def test_personio_raises_a_clear_error_on_invalid_xml(monkeypatch):
    with pytest.raises(RuntimeError, match="not valid XML"):
        _personio(monkeypatch, "<workzag-jobs><position>")


# ---------------------------------------------------------------------------
# Rippling
# ---------------------------------------------------------------------------

RIPPLING_JOBS = [
    {
        "uuid": "6f0d2c1e-9a55-4b31-9f0a-1d2e3f4a5b6c",
        "name": "Tactical Athletic Trainer",
        "descriptionHtml": "<p>Support a county fire department.</p><p>ATC and CSCS preferred.</p>",
        "workLocation": {"label": "Mesa, AZ"},
        "department": {"label": "Occupational Health"},
        "employmentType": "FULL_TIME",
        "url": "https://ats.rippling.com/acme-fire/jobs/6f0d2c1e",
        "publishedAt": "2026-02-14T00:00:00Z",
    }
]


def _rippling(monkeypatch, payload, **options):
    recorder = Recorder({}, default=payload)
    monkeypatch.setattr(f"{MODULE}.fetch_json", recorder)
    source = RipplingSource("acme", {"board_token": "acme-fire", **options})
    return list(source.fetch()), recorder


def test_rippling_maps_core_fields(monkeypatch):
    postings, recorder = _rippling(monkeypatch, RIPPLING_JOBS, employer="Acme Fire")
    assert recorder.urls == [
        "https://api.rippling.com/platform/api/ats/v1/board/acme-fire/jobs"
    ]
    posting = postings[0]
    assert posting.source == "rippling:acme"
    assert posting.source_id == "6f0d2c1e-9a55-4b31-9f0a-1d2e3f4a5b6c"
    assert posting.title == "Tactical Athletic Trainer"
    assert posting.employer == "Acme Fire"
    assert posting.location == "Mesa, AZ"
    assert posting.department == "Occupational Health"
    assert posting.url == "https://ats.rippling.com/acme-fire/jobs/6f0d2c1e"
    assert posting.posted_at is not None and posting.posted_at.year == 2026
    assert "ATC and CSCS preferred" in posting.description
    assert "department.ATC" not in posting.description
    assert "<p>" not in posting.description


def test_rippling_folds_the_employment_type_into_the_text(monkeypatch):
    description = _rippling(monkeypatch, RIPPLING_JOBS)[0][0].description
    assert "Employment type: Full Time." in description


def test_rippling_builds_a_url_when_the_record_omits_one(monkeypatch):
    payload = [{"uuid": "abc123", "name": "Strength Coach"}]
    posting = _rippling(monkeypatch, payload)[0][0]
    assert posting.url == "https://ats.rippling.com/acme-fire/jobs/abc123"


def test_rippling_detects_a_remote_work_location_type(monkeypatch):
    """The structured field decides on its own.

    The location text is one ``looks_remote`` would reject, so this fails if
    ``workLocationType`` stops being read.
    """
    remote = [
        {
            "uuid": "r1",
            "name": "Cognitive Performance Specialist",
            "workLocation": {"label": "Mesa, AZ"},
            "workLocationType": "REMOTE",
        }
    ]
    onsite = [
        {
            "uuid": "r2",
            "name": "Cognitive Performance Specialist",
            "workLocation": {"label": "Mesa, AZ"},
            "workLocationType": "ON_SITE",
        }
    ]
    assert _rippling(monkeypatch, remote)[0][0].remote is True
    assert _rippling(monkeypatch, onsite)[0][0].remote is False


def test_rippling_handles_a_unicode_id_and_title(monkeypatch):
    payload = [
        {
            "uuid": "übung-1",
            "name": "Спеціаліст з фізичної підготовки",
            "descriptionHtml": "<p>Café &amp; naïve</p>",
        }
    ]
    posting = _rippling(monkeypatch, payload)[0][0]
    assert posting.source_id == "übung-1"
    assert posting.title == "Спеціаліст з фізичної підготовки"
    assert "Café & naïve" in posting.description
    # The id is percent-encoded in the URL rather than emitted raw.
    assert posting.url == "https://ats.rippling.com/acme-fire/jobs/%C3%BCbung-1"


def test_rippling_reads_an_envelope_payload(monkeypatch):
    postings, _ = _rippling(monkeypatch, {"jobs": RIPPLING_JOBS})
    assert len(postings) == 1


def test_rippling_skips_malformed_records(monkeypatch):
    payload = [{"name": "No uuid"}, ["nope"], RIPPLING_JOBS[0]]
    postings, _ = _rippling(monkeypatch, payload)
    assert [p.source_id for p in postings] == ["6f0d2c1e-9a55-4b31-9f0a-1d2e3f4a5b6c"]


# ---------------------------------------------------------------------------
# Module contract
# ---------------------------------------------------------------------------


def test_every_adapter_is_exported():
    assert set(ATS_EXTRA_SOURCES) == {
        BambooHRSource,
        BreezySource,
        JazzHRSource,
        TeamtailorSource,
        PersonioSource,
        RipplingSource,
    }


def test_kinds_are_unique_and_non_empty():
    kinds = [cls.kind for cls in ATS_EXTRA_SOURCES]
    assert all(kinds)
    assert len(set(kinds)) == len(kinds)


def test_kinds_do_not_collide_with_the_first_tier_adapters():
    """A duplicate ``kind`` would silently shadow an adapter in the registry."""
    from tactical_jobs.sources.ats import ATS_SOURCES

    existing = {cls.kind for cls in ATS_SOURCES} | {"usajobs", "rss"}
    assert not {cls.kind for cls in ATS_EXTRA_SOURCES} & existing


CONFIGURED = (
    (BambooHRSource, {"subdomain": "acme"}),
    (BreezySource, {"company": "acme"}),
    (JazzHRSource, {"api_key": "k", "board": "acme"}),
    (TeamtailorSource, {"api_key": "k"}),
    (RipplingSource, {"board_token": "acme"}),
)


@pytest.mark.parametrize("payload", [None, {}, [], "", 0, {"result": "oops"}, {"data": None}])
def test_no_json_adapter_crashes_on_an_empty_or_odd_response(monkeypatch, payload):
    """A dead or empty board yields nothing; it does not raise."""
    monkeypatch.setattr(f"{MODULE}.fetch_json", lambda url, **kwargs: payload)
    for cls, options in CONFIGURED:
        assert list(cls("probe", options).fetch()) == [], cls.__name__


@pytest.mark.parametrize(
    "record",
    [
        None,
        42,
        "text",
        ["nope"],
        {},
        {"id": None},
        {"id": "1", "location": "string-not-object", "department": {"unexpected": 1}},
    ],
)
def test_no_json_adapter_crashes_on_an_odd_record(monkeypatch, record):
    """One junk record may be skipped, but it must never raise."""
    monkeypatch.setattr(f"{MODULE}.fetch_json", lambda url, **kwargs: [record])
    for cls, options in CONFIGURED:
        postings = list(cls("probe", options).fetch())
        assert len(postings) <= 1, cls.__name__


def test_every_adapter_reports_its_missing_required_option():
    for cls, option in (
        (BambooHRSource, "subdomain"),
        (BreezySource, "company"),
        (JazzHRSource, "api_key"),
        (TeamtailorSource, "api_key"),
        (PersonioSource, "company"),
        (RipplingSource, "board_token"),
    ):
        with pytest.raises(KeyError, match=option):
            list(cls("unconfigured", {}).fetch())
