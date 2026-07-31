"""Phenom People adapter tests.

Everything here runs against captured payload shapes ported from
santifer/career-ops providers/phenom.mjs (MIT). There is no outbound network
in CI or the sandbox, so ``post_json`` is replaced as imported into the
adapter module and the assertions are about the refineSearch request body,
pagination, keyword dedupe, slug/URL construction, and the honesty rules
(no invented dates, no applyUrl-as-listing, no fabricated description).
"""

from __future__ import annotations

import json
import sys
from datetime import timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.http import FetchError  # noqa: E402
from tactical_jobs.sources.phenom import (  # noqa: E402
    PHENOM_SOURCES,
    PhenomSource,
    slugify,
)

OPTIONS = {
    "url": "https://careers.serco-na.com",
    "employer": "Serco",
    # The real default is a polite 0.5s; tests must not actually sleep.
    "delay_seconds": 0,
}

WIDGETS_URL = "https://careers.serco-na.com/widgets"


def _job(job_id, title="Human Performance Coach", **extra):
    record = {
        "jobId": job_id,
        "title": title,
        "city": "Fort Liberty",
        "state": "North Carolina",
        "country": "United States",
        "location": "Fort Liberty, North Carolina, United States",
        "postedDate": "2026-05-07T18:25:30.000+0000",
        "applyUrl": f"https://ats.example.com/apply/{job_id}",
        "category": "Human Performance",
    }
    record.update(extra)
    return record


def _page(jobs, total=None, status=200):
    refine = {
        "totalHits": len(jobs) if total is None else total,
        "data": {"jobs": list(jobs)},
    }
    if status is not None:
        refine["status"] = status
    return {"refineSearch": refine}


class FakeAPI:
    """Stands in for the /widgets endpoint and records what was asked."""

    def __init__(self, pages=None, *, encode=True):
        # pages: dict keyed by (keywords, from) -> payload, or a callable.
        self.pages = pages if pages is not None else {}
        self.encode = encode
        self.calls: list[tuple[str, dict]] = []

    def post_json(self, url, payload, **kwargs):
        self.calls.append((url, payload))
        if callable(self.pages):
            page = self.pages(payload)
        else:
            page = self.pages.get((payload["keywords"], payload["from"]), _page([]))
        if isinstance(page, Exception):
            raise page
        return json.dumps(page).encode() if self.encode else page

    def install(self, monkeypatch):
        monkeypatch.setattr("tactical_jobs.sources.phenom.post_json", self.post_json)
        return self


def _run(monkeypatch, api, options=None, name="serco"):
    api.install(monkeypatch)
    merged = {**OPTIONS, **(options or {})}
    return list(PhenomSource(name, merged).fetch())


# --------------------------------------------------------------------------
# request shape: the refineSearch body is what makes the endpoint answer
# --------------------------------------------------------------------------


def test_posts_the_refine_search_body_to_the_widgets_endpoint(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    _run(monkeypatch, api)

    url, payload = api.calls[0]
    assert url == WIDGETS_URL
    # The keys the recipe documents as load-bearing must all be present.
    assert payload["lang"] == "en_global"
    assert payload["country"] == "global"
    assert payload["ddoKey"] == "refineSearch"
    assert payload["pageName"] == "search-results"
    assert payload["siteType"] == "external"
    assert payload["jobs"] is True
    assert payload["counts"] is True
    assert payload["from"] == 0
    assert payload["size"] == 100
    assert payload["keywords"] == ""
    assert payload["selected_fields"] == {}
    assert payload["all_fields"] == ["category", "country", "city"]


def test_lang_country_and_selected_fields_options_reach_the_body(monkeypatch):
    api = FakeAPI(lambda payload: _page([_job("1")]))
    _run(
        monkeypatch,
        api,
        {
            "lang": "en_us",
            "country": "us",
            "selected_fields": {"country": ["United States of America"]},
        },
    )

    payload = api.calls[0][1]
    assert payload["lang"] == "en_us"
    assert payload["country"] == "us"
    assert payload["selected_fields"] == {"country": ["United States of America"]}
    # The recipe sends global=true only for the global scope.
    assert payload["global"] is False


def test_origin_is_reduced_from_a_full_careers_url(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    postings = _run(
        monkeypatch,
        api,
        {"url": "https://careers.serco-na.com/global/en/search-results?from=0"},
    )

    assert api.calls[0][0] == WIDGETS_URL
    assert postings[0].url.startswith("https://careers.serco-na.com/global/en/job/")


def test_unresolvable_url_raises(monkeypatch):
    api = FakeAPI()
    api.install(monkeypatch)
    with pytest.raises(ValueError):
        list(PhenomSource("x", {**OPTIONS, "url": "not a url"}).fetch())


def test_url_is_required(monkeypatch):
    api = FakeAPI()
    api.install(monkeypatch)
    with pytest.raises(KeyError):
        list(PhenomSource("x", {"employer": "Serco"}).fetch())


# --------------------------------------------------------------------------
# pagination via totalHits
# --------------------------------------------------------------------------


def test_paginates_with_from_offsets_until_total_hits(monkeypatch):
    api = FakeAPI(
        {
            ("", 0): _page([_job("1"), _job("2")], total=5),
            ("", 2): _page([_job("3"), _job("4")], total=5),
            ("", 4): _page([_job("5")], total=5),
        }
    )
    postings = _run(monkeypatch, api, {"size": 2})

    assert [payload["from"] for _, payload in api.calls] == [0, 2, 4]
    assert [posting.source_id for posting in postings] == ["1", "2", "3", "4", "5"]


def test_pagination_stops_at_max_pages(monkeypatch):
    def endless(payload):
        start = payload["from"]
        return _page(
            [_job(str(start + i)) for i in range(payload["size"])], total=100_000
        )

    api = FakeAPI(endless)
    postings = _run(monkeypatch, api, {"size": 2, "max_pages": 3})

    assert len(api.calls) == 3
    assert len(postings) == 6


def test_pagination_stops_when_the_server_ignores_from(monkeypatch):
    # totalHits says thousands more exist, but every page is the same page.
    api = FakeAPI(lambda payload: _page([_job("1"), _job("2")], total=5000))
    postings = _run(monkeypatch, api, {"size": 2, "max_pages": 10})

    assert len(api.calls) == 2, "one repeat page proves `from` is ignored; stop"
    assert [posting.source_id for posting in postings] == ["1", "2"]


def test_empty_response_yields_nothing(monkeypatch):
    api = FakeAPI({("", 0): _page([])})
    assert _run(monkeypatch, api) == []
    assert len(api.calls) == 1


# --------------------------------------------------------------------------
# keyword searches, deduped by jobId
# --------------------------------------------------------------------------


def test_keywords_are_each_searched_and_deduped_by_job_id(monkeypatch):
    shared = _job("1")
    api = FakeAPI(
        {
            ("human performance", 0): _page([shared, _job("2")]),
            ("strength and conditioning", 0): _page([shared, _job("3")]),
        }
    )
    postings = _run(
        monkeypatch,
        api,
        {"keywords": ["human performance", "strength and conditioning"]},
    )

    assert [payload["keywords"] for _, payload in api.calls] == [
        "human performance",
        "strength and conditioning",
    ]
    assert [posting.source_id for posting in postings] == ["1", "2", "3"]


def test_an_overlapping_first_page_does_not_end_a_later_keyword_early(monkeypatch):
    """Keyword two may open with jobs keyword one already found and still
    have fresh ones on its next page; global dedupe must not read that
    overlap as a pagination loop."""
    api = FakeAPI(
        {
            ("hp", 0): _page([_job("1"), _job("2")], total=2),
            ("sc", 0): _page([_job("1"), _job("2")], total=4),
            ("sc", 2): _page([_job("3"), _job("4")], total=4),
        }
    )
    postings = _run(monkeypatch, api, {"keywords": ["hp", "sc"], "size": 2})

    assert [posting.source_id for posting in postings] == ["1", "2", "3", "4"]


def test_a_string_keyword_is_accepted(monkeypatch):
    api = FakeAPI({("athletic trainer", 0): _page([_job("1")])})
    postings = _run(monkeypatch, api, {"keywords": "athletic trainer"})
    assert len(postings) == 1


def test_none_entries_in_keywords_are_dropped_not_searched_for(monkeypatch):
    api = FakeAPI({("wanted", 0): _page([_job("1")])})
    _run(monkeypatch, api, {"keywords": [None, "wanted"]})
    assert [payload["keywords"] for _, payload in api.calls] == ["wanted"]


def test_repeated_keywords_are_only_requested_once(monkeypatch):
    api = FakeAPI({("hp", 0): _page([_job("1")])})
    _run(monkeypatch, api, {"keywords": ["hp", "hp"]})
    assert len(api.calls) == 1


def test_no_keywords_means_one_unfiltered_search(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    _run(monkeypatch, api, {"keywords": []})
    assert [payload["keywords"] for _, payload in api.calls] == [""]


# --------------------------------------------------------------------------
# slugify parity with the upstream recipe
# --------------------------------------------------------------------------


def test_slugify_collapses_non_alphanumeric_runs_to_single_hyphens():
    assert slugify("Human Performance Specialist") == "Human-Performance-Specialist"
    assert slugify("H2F — Athletic Trainer II") == "H2F-Athletic-Trainer-II"
    assert slugify("Coach (Strength & Conditioning)") == "Coach-Strength-Conditioning"


def test_slugify_strips_accents_via_nfkd_not_hyphens():
    assert slugify("Küchenchef (m/w/d) – Café") == "Kuchenchef-m-w-d-Cafe"
    assert slugify("Éducateur spécialisé") == "Educateur-specialise"


def test_slugify_preserves_case_like_phenom_does():
    assert slugify("Human Performance Coach") == "Human-Performance-Coach"


def test_slugify_trims_edge_hyphens():
    assert slugify("  Coach  ") == "Coach"
    assert slugify("- Coach -") == "Coach"


def test_slugify_falls_back_to_job_when_nothing_survives():
    assert slugify("!!!") == "job"
    assert slugify("") == "job"


# --------------------------------------------------------------------------
# job URL construction; applyUrl is NEVER the listing URL
# --------------------------------------------------------------------------


def test_job_url_is_the_public_listing_on_the_branded_host(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("98098")])})
    posting = _run(monkeypatch, api)[0]

    assert posting.url == (
        "https://careers.serco-na.com/global/en/job/98098/Human-Performance-Coach"
    )


def test_apply_url_is_never_used_as_the_job_url(monkeypatch):
    job = _job("98098", applyUrl="https://ats.example.com/apply/98098")
    api = FakeAPI({("", 0): _page([job])})
    posting = _run(monkeypatch, api)[0]

    assert posting.url != job["applyUrl"]
    assert "ats.example.com" not in posting.url
    # The downstream-ATS link stays available for debugging, in raw only.
    assert posting.raw["job"]["applyUrl"] == "https://ats.example.com/apply/98098"


def test_url_prefix_option_is_used_and_trimmed(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("7")])})
    posting = _run(monkeypatch, api, {"url_prefix": "/na/en/"})[0]
    assert posting.url == (
        "https://careers.serco-na.com/na/en/job/7/Human-Performance-Coach"
    )


def test_job_id_is_percent_encoded_in_the_url(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("R 100/2")])})
    posting = _run(monkeypatch, api)[0]
    assert "/job/R%20100%2F2/" in posting.url


def test_slug_comes_from_the_markup_stripped_title(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("5", title="<b>Coach</b>")])})
    posting = _run(monkeypatch, api)[0]
    assert posting.title == "Coach"
    assert posting.url.endswith("/job/5/Coach")


# --------------------------------------------------------------------------
# honesty: dates only from response fields
# --------------------------------------------------------------------------


def test_posted_date_iso_instant_is_parsed(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    posting = _run(monkeypatch, api)[0]

    assert posting.posted_at is not None
    assert (posting.posted_at.year, posting.posted_at.month, posting.posted_at.day) == (
        2026,
        5,
        7,
    )
    assert posting.posted_at.utcoffset() == timedelta(0)


def test_missing_posted_date_is_none_never_invented(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1", postedDate=None)])})
    posting = _run(monkeypatch, api)[0]
    assert posting.posted_at is None


def test_date_created_is_the_documented_fallback(monkeypatch):
    job = _job("1", postedDate=None, dateCreated="2026-04-01T00:00:00.000+0000")
    api = FakeAPI({("", 0): _page([job])})
    posting = _run(monkeypatch, api)[0]
    assert (posting.posted_at.year, posting.posted_at.month) == (2026, 4)


def test_unparseable_posted_date_is_none(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1", postedDate="Posted Yesterday")])})
    posting = _run(monkeypatch, api)[0]
    assert posting.posted_at is None


# --------------------------------------------------------------------------
# honesty: the description is the search summary and says so
# --------------------------------------------------------------------------


def test_description_is_built_only_from_stated_fields(monkeypatch):
    job = {
        "jobId": "9",
        "title": "Strength Coach",
        "location": "Herndon, Virginia, United States",
    }
    api = FakeAPI({("", 0): _page([job])})
    posting = _run(monkeypatch, api)[0]

    assert posting.description == "Strength Coach Herndon, Virginia, United States"


def test_category_is_included_when_the_response_states_it(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    posting = _run(monkeypatch, api)[0]

    assert "Job category: Human Performance." in posting.description
    assert posting.department == "Human Performance"


def test_department_is_none_when_category_absent(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1", category=None)])})
    posting = _run(monkeypatch, api)[0]
    assert posting.department is None


def test_raw_records_that_the_description_is_a_search_summary(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    posting = _run(monkeypatch, api)[0]

    assert posting.raw["job"]["jobId"] == "1"
    assert "search-result summary" in posting.raw["description_note"]
    assert "posting body" in posting.raw["description_note"]


# --------------------------------------------------------------------------
# field mapping
# --------------------------------------------------------------------------


def test_source_label_and_employer(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    posting = _run(monkeypatch, api)[0]
    assert posting.source == "phenom:serco"
    assert posting.employer == "Serco"


def test_employer_defaults_to_the_source_name(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    api.install(monkeypatch)
    posting = list(
        PhenomSource(
            "serco",
            {"url": "https://careers.serco-na.com", "delay_seconds": 0},
        ).fetch()
    )[0]
    assert posting.employer == "serco"


def test_location_prefers_the_explicit_location_field(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1", location="Joint Base Lewis-McChord, WA")])})
    posting = _run(monkeypatch, api)[0]
    assert posting.location == "Joint Base Lewis-McChord, WA"


def test_location_assembled_from_city_state_country_dedupes(monkeypatch):
    job = _job(
        "1",
        location=None,
        city="Singapore",
        state="Singapore",
        country="Singapore",
    )
    api = FakeAPI({("", 0): _page([job])})
    posting = _run(monkeypatch, api)[0]
    assert posting.location == "Singapore"


def test_remote_location_sets_the_remote_flag(monkeypatch):
    api = FakeAPI(
        {("", 0): _page([_job("1", location="Remote - United States")])}
    )
    posting = _run(monkeypatch, api)[0]
    assert posting.remote is True


def test_unicode_title_survives_and_slug_is_ascii(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1", title="Coach — Größtes Café Team")])})
    posting = _run(monkeypatch, api)[0]

    assert posting.title == "Coach — Größtes Café Team"
    # ö decomposes to o + combining mark (stripped); ß has no NFKD
    # decomposition, so like the upstream it collapses to a hyphen.
    assert posting.url.endswith("/job/1/Coach-Gro-tes-Cafe-Team")


# --------------------------------------------------------------------------
# malformed input and failure handling
# --------------------------------------------------------------------------


def test_malformed_records_are_skipped_not_fatal(monkeypatch):
    api = FakeAPI(
        {
            ("", 0): _page(
                [
                    "not-a-dict",
                    {"title": "No jobId here"},
                    {"jobId": "77"},  # no title: no meaningful listing
                    {"jobId": "  ", "title": "Blank id"},
                    _job("1"),
                ]
            )
        }
    )
    postings = _run(monkeypatch, api)

    assert [posting.source_id for posting in postings] == ["1"]


def test_refine_search_error_status_is_reported_not_silently_empty(monkeypatch):
    api = FakeAPI({("", 0): _page([], status=500)})
    with pytest.raises(FetchError):
        _run(monkeypatch, api)


def test_an_error_status_on_a_later_page_keeps_what_was_collected(monkeypatch):
    api = FakeAPI(
        {
            ("", 0): _page([_job("1")], total=99),
            ("", 1): _page([], status=403),
        }
    )
    postings = _run(monkeypatch, api, {"size": 1})
    assert [posting.source_id for posting in postings] == ["1"]


def test_one_failing_keyword_does_not_lose_the_others(monkeypatch):
    api = FakeAPI(
        {
            ("hp", 0): _page([_job("1")]),
            ("at", 0): FetchError("HTTP 503"),
            ("pt", 0): _page([_job("2")]),
        }
    )
    postings = _run(monkeypatch, api, {"keywords": ["hp", "at", "pt"]})
    assert [posting.source_id for posting in postings] == ["1", "2"]


def test_a_missing_refine_search_block_is_an_error(monkeypatch):
    api = FakeAPI({("", 0): {"unexpected": True}})
    with pytest.raises(FetchError):
        _run(monkeypatch, api)


def test_non_json_body_raises_a_fetch_error(monkeypatch):
    def broken_post(url, payload, **kwargs):
        return b"<html>Access Denied</html>"

    monkeypatch.setattr("tactical_jobs.sources.phenom.post_json", broken_post)
    with pytest.raises(FetchError):
        list(PhenomSource("serco", OPTIONS).fetch())


def test_a_status_free_refine_search_block_is_accepted(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")], status=None)})
    postings = _run(monkeypatch, api)
    assert len(postings) == 1


def test_an_already_parsed_body_is_accepted(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])}, encode=False)
    postings = _run(monkeypatch, api)
    assert len(postings) == 1


# --------------------------------------------------------------------------
# option handling: clamps, junk tolerance, pacing
# --------------------------------------------------------------------------


def test_size_is_clamped_to_the_widget_maximum_of_100(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    _run(monkeypatch, api, {"size": 500})
    assert api.calls[0][1]["size"] == 100


def test_size_is_clamped_up_to_at_least_one(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    _run(monkeypatch, api, {"size": 0})
    assert api.calls[0][1]["size"] == 1


def test_junk_size_falls_back_to_the_default(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    _run(monkeypatch, api, {"size": "big"})
    assert api.calls[0][1]["size"] == 100


def test_junk_max_pages_falls_back_to_the_default_of_five(monkeypatch):
    api = FakeAPI(lambda payload: _page([_job(str(payload["from"]))], total=10_000))
    _run(monkeypatch, api, {"size": 1, "max_pages": "many"})
    assert len(api.calls) == 5


def test_junk_selected_fields_degrades_to_no_facet_filter(monkeypatch):
    api = FakeAPI({("", 0): _page([_job("1")])})
    _run(monkeypatch, api, {"selected_fields": "usa"})
    assert api.calls[0][1]["selected_fields"] == {}


def test_delay_seconds_paces_between_requests_but_not_before_the_first(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr("tactical_jobs.sources.phenom.time.sleep", lambda s: slept.append(s))
    api = FakeAPI(
        {
            ("", 0): _page([_job("1")], total=3),
            ("", 1): _page([_job("2")], total=3),
            ("", 2): _page([_job("3")], total=3),
        }
    )
    _run(monkeypatch, api, {"size": 1, "delay_seconds": 0.25})

    assert len(api.calls) == 3
    assert slept == [0.25, 0.25]


def test_default_delay_is_half_a_second(monkeypatch):
    slept: list[float] = []
    monkeypatch.setattr("tactical_jobs.sources.phenom.time.sleep", lambda s: slept.append(s))
    api = FakeAPI(
        {
            ("", 0): _page([_job("1")], total=2),
            ("", 1): _page([_job("2")], total=2),
        }
    )
    api.install(monkeypatch)
    options = {"url": "https://careers.serco-na.com", "size": 1}
    list(PhenomSource("serco", options).fetch())

    assert slept == [0.5]


def test_kind_and_export_tuple():
    assert PhenomSource.kind == "phenom"
    assert PHENOM_SOURCES == (PhenomSource,)
