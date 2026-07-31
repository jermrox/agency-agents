"""Tests for the public-sector, association-feed, and generic-JSON adapters.

Everything runs against captured payload shapes. There is no outbound network
in CI or the sandbox, so ``fetch``/``fetch_json`` are replaced as imported
into the adapter module and the assertions are about field mapping, envelope
tolerance, title parsing, and graceful degradation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.http import FetchError  # noqa: E402
from tactical_jobs.sources.govjobs import (  # noqa: E402
    GOV_SOURCES,
    GenericJSONSource,
    GovernmentJobsSource,
    JobsRSSSource,
    as_int,
    envelope_records,
    flatten,
    looks_like_location,
    normalize_key,
    pick_field,
    resolve_path,
    split_listing_title,
)


@pytest.fixture(autouse=True)
def block_the_network(monkeypatch):
    """No test may reach the network, including by accident.

    There is no outbound network in CI, so a test that quietly started making
    a real request would fail as a timeout somewhere unrelated. Replacing both
    transport symbols by default means an unpatched call names itself.
    """

    def blocked(*args, **kwargs):
        raise AssertionError(
            "test reached the network; monkeypatch fetch/fetch_json as imported "
            "into tactical_jobs.sources.govjobs"
        )

    monkeypatch.setattr("tactical_jobs.sources.govjobs.fetch", blocked)
    monkeypatch.setattr("tactical_jobs.sources.govjobs.fetch_json", blocked)

LIST_URL = "https://www.governmentjobs.com/careers/austintx"

LONG_BODY = (
    "The Austin Fire Department Wellness Division is hiring a peer fitness "
    "trainer to deliver strength and conditioning programming to sworn "
    "personnel. CSCS or TSAC-F required. NFPA 1583 experience preferred. "
    "Candidates must pass a physical ability test and hold a current CPR "
    "certification. This position reports to the Health and Safety Officer "
    "and supports approximately 1,100 firefighters across 50 stations."
)


class FakeGov:
    """Stands in for the NEOGOV list and detail endpoints."""

    def __init__(self, pages, details=None, list_url=LIST_URL):
        self.pages = pages
        self.details = details or {}
        self.list_url = list_url
        self.list_calls: list[tuple[str, dict]] = []
        self.detail_calls: list[tuple[str, dict]] = []

    def fetch_json(self, url, params=None, headers=None, **kwargs):
        if url == self.list_url:
            self.list_calls.append((url, params or {}))
            page = (params or {}).get("page", 1)
            payload = self.pages(page) if callable(self.pages) else self.pages.get(page)
            if payload is None:
                return {"items": []}
            if isinstance(payload, Exception):
                raise payload
            return payload

        self.detail_calls.append((url, params or {}))
        detail = self.details(url) if callable(self.details) else self.details.get(url)
        if detail is None:
            raise FetchError(f"HTTP 404 for {url}")
        if isinstance(detail, Exception):
            raise detail
        return detail

    def install(self, monkeypatch):
        monkeypatch.setattr("tactical_jobs.sources.govjobs.fetch_json", self.fetch_json)
        return self


def run_gov(monkeypatch, api, options=None, name="austintx"):
    api.install(monkeypatch)
    merged = {"agency": "austintx", **(options or {})}
    return list(GovernmentJobsSource(name, merged).fetch())


# ==========================================================================
# tolerant field access
# ==========================================================================


def test_normalize_key_folds_case_and_punctuation():
    assert normalize_key("jobTitle") == "jobtitle"
    assert normalize_key("job_title") == "jobtitle"
    assert normalize_key("Job Title") == "jobtitle"
    assert normalize_key("JOB-TITLE") == "jobtitle"


def test_pick_field_returns_the_first_present_candidate():
    record = {"jobTitle": "Peer Fitness Trainer", "title": "ignored"}
    # Candidate order decides, not key order in the record.
    assert pick_field(record, "title", "jobTitle") == "ignored"
    assert pick_field(record, "jobTitle", "title") == "Peer Fitness Trainer"


def test_pick_field_skips_present_but_empty_values():
    record = {"title": "", "jobTitle": None, "positionTitle": "Wellness Coordinator"}
    assert pick_field(record, "title", "jobTitle", "positionTitle") == "Wellness Coordinator"


def test_pick_field_matches_across_naming_conventions():
    assert pick_field({"date_posted": "2026-07-01"}, "datePosted") == "2026-07-01"
    assert pick_field({"PostedDate": "2026-07-01"}, "postedDate") == "2026-07-01"


def test_pick_field_flattens_objects_and_lists():
    assert pick_field({"department": {"name": "Fire"}}, "department") == "Fire"
    assert pick_field({"location": ["Austin, TX", "Round Rock, TX"]}, "location") == (
        "Austin, TX, Round Rock, TX"
    )


def test_pick_field_default_when_nothing_matches():
    assert pick_field({"other": "x"}, "title", default="") == ""
    assert pick_field("not-a-dict", "title") == ""


def test_envelope_records_accepts_a_bare_root_array():
    assert envelope_records([{"id": 1}]) == [{"id": 1}]


def test_envelope_records_finds_a_nested_array():
    payload = {"meta": {"count": 1}, "data": {"results": [{"id": 1}]}}
    assert envelope_records(payload) == [{"id": 1}]


def test_envelope_records_ignores_unrelated_arrays():
    assert envelope_records({"facets": [{"id": 1}], "meta": {}}) == []


# ==========================================================================
# governmentjobs: envelope variants
# ==========================================================================


def test_camel_case_envelope_variant(monkeypatch):
    api = FakeGov(
        {
            1: {
                "items": [
                    {
                        "id": 4412,
                        "title": "Peer Fitness Trainer",
                        "location": "Austin, TX",
                        "salaryDisplay": "$62,000.00 - $78,000.00 Annually",
                        "department": "Austin Fire Department",
                        "jobType": "Full Time",
                        "datePosted": "2026-07-15T00:00:00",
                        "detailUrl": "/careers/austintx/jobs/4412",
                    }
                ]
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]

    assert posting.source_id == "4412"
    assert posting.title == "Peer Fitness Trainer"
    assert posting.location == "Austin, TX"
    assert posting.compensation == "$62,000.00 - $78,000.00 Annually"
    assert posting.department == "Austin Fire Department"
    assert posting.posted_at is not None and posting.posted_at.year == 2026


def test_pascal_case_envelope_variant(monkeypatch):
    api = FakeGov(
        {
            1: {
                "Jobs": [
                    {
                        "Id": "5501",
                        "JobTitle": "Wellness Coordinator",
                        "JobLocation": "Mesa, AZ",
                        "Salary": "$70,000.00 Annually",
                        "DepartmentName": "Fire and Medical",
                        "EmploymentType": "Full-Time Regular",
                        "PostedDate": "2026-06-02",
                    }
                ]
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]

    assert posting.source_id == "5501"
    assert posting.title == "Wellness Coordinator"
    assert posting.location == "Mesa, AZ"
    assert posting.compensation == "$70,000.00 Annually"
    assert posting.department == "Fire and Medical"
    assert "Job type: Full-Time Regular." in posting.description


def test_snake_case_nested_envelope_variant(monkeypatch):
    api = FakeGov(
        {
            1: {
                "data": {
                    "results": [
                        {
                            "job_id": 77,
                            "position_title": "Tactical Athletic Trainer",
                            "location_name": "Travis County, TX",
                            "salary_range": "$34.00 - $41.00 Hourly",
                            "department_name": "Emergency Services",
                            "job_type": "Full Time",
                            "date_posted": "2026-05-20",
                        }
                    ]
                }
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]

    assert posting.source_id == "77"
    assert posting.title == "Tactical Athletic Trainer"
    assert posting.location == "Travis County, TX"
    assert posting.compensation == "$34.00 - $41.00 Hourly"
    assert posting.department == "Emergency Services"


def test_city_and_state_fields_are_joined_when_no_location_field(monkeypatch):
    api = FakeGov(
        {1: {"items": [{"id": 9, "title": "Fitness Specialist", "city": "Tacoma", "state": "WA"}]}}
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]
    assert posting.location == "Tacoma, WA"


def test_min_and_max_salary_fields_are_rendered(monkeypatch):
    api = FakeGov(
        {
            1: {
                "items": [
                    {
                        "id": 9,
                        "title": "Fitness Specialist",
                        "salaryMin": "$28.00",
                        "salaryMax": "$36.00",
                        "payFrequency": "Hourly",
                    }
                ]
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]
    assert posting.compensation == "$28.00 - $36.00 Hourly"


# ==========================================================================
# governmentjobs: request construction
# ==========================================================================


def test_list_url_is_built_from_the_agency_slug(monkeypatch):
    api = FakeGov({1: {"items": []}})
    run_gov(monkeypatch, api)
    url, params = api.list_calls[0]
    assert url == LIST_URL
    assert params == {"format": "json", "page": 1}


def test_url_option_overrides_the_agency_url(monkeypatch):
    override = "https://agency.jobs.example.gov/api/openings?format=json"
    api = FakeGov({1: {"items": []}}, list_url=override)
    run_gov(monkeypatch, api, {"url": override})
    url, params = api.list_calls[0]
    assert url == override
    # format is already in the override, so it is not appended a second time.
    assert params == {"page": 1}


def test_agency_is_required():
    with pytest.raises(KeyError):
        list(GovernmentJobsSource("x", {}).fetch())


def test_public_url_uses_the_governmentjobs_permalink(monkeypatch):
    api = FakeGov(
        {
            1: {
                "items": [
                    {"id": 4412, "title": "Peer Fitness Trainer", "detailUrl": "/careers/austintx/jobs/4412"}
                ]
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]
    assert posting.url == "https://www.governmentjobs.com/jobs/4412"


def test_url_falls_back_to_the_tenant_link_without_an_id(monkeypatch):
    api = FakeGov(
        {1: {"items": [{"title": "Peer Fitness Trainer", "link": "/careers/austintx/jobs/1"}]}}
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]
    assert posting.url == "https://www.governmentjobs.com/careers/austintx/jobs/1"
    assert posting.source_id == posting.url


def test_employer_defaults_to_the_agency_then_the_option(monkeypatch):
    api = FakeGov({1: {"items": [{"id": 1, "title": "Coach"}]}})
    assert run_gov(monkeypatch, api, {"detail_limit": 0})[0].employer == "austintx"

    api = FakeGov({1: {"items": [{"id": 1, "title": "Coach"}]}})
    posting = run_gov(
        monkeypatch, api, {"detail_limit": 0, "employer": "City of Austin"}
    )[0]
    assert posting.employer == "City of Austin"
    assert posting.source == "governmentjobs:austintx"


# ==========================================================================
# governmentjobs: detail fetching
# ==========================================================================


def test_detail_fetch_supplies_the_full_description(monkeypatch):
    api = FakeGov(
        {1: {"items": [{"id": 4412, "title": "Peer Fitness Trainer", "description": "Teaser."}]}},
        details={
            "https://www.governmentjobs.com/jobs/4412": {
                "job": {
                    "definition": f"<p>{LONG_BODY}</p>",
                    "minimumQualifications": "<ul><li>CSCS required</li><li>EMT-B preferred</li></ul>",
                }
            }
        },
    )
    posting = run_gov(monkeypatch, api)[0]

    assert "Austin Fire Department Wellness Division" in posting.description
    assert "CSCS required" in posting.description
    assert "EMT-B preferred" in posting.description
    # Block tags became separators rather than gluing words together.
    assert "requiredEMT" not in posting.description
    assert api.detail_calls[0][1] == {"format": "json"}


def test_a_long_list_description_avoids_the_detail_request(monkeypatch):
    api = FakeGov({1: {"items": [{"id": 1, "title": "Coach", "description": LONG_BODY}]}})
    posting = run_gov(monkeypatch, api)[0]

    assert api.detail_calls == []
    assert LONG_BODY[:40] in posting.description


def test_detail_request_prefers_the_tenant_detail_link(monkeypatch):
    api = FakeGov(
        {1: {"items": [{"id": 4412, "title": "Coach", "detailUrl": "/careers/austintx/jobs/4412"}]}},
        details={
            "https://www.governmentjobs.com/careers/austintx/jobs/4412": {"description": LONG_BODY}
        },
    )
    posting = run_gov(monkeypatch, api)[0]

    assert api.detail_calls[0][0] == (
        "https://www.governmentjobs.com/careers/austintx/jobs/4412"
    )
    assert LONG_BODY[:40] in posting.description


def test_detail_failure_keeps_the_posting(monkeypatch):
    api = FakeGov(
        {1: {"items": [{"id": 1, "title": "Peer Fitness Trainer", "description": "Teaser."}]}},
        details={},  # every detail lookup 404s
    )
    postings = run_gov(monkeypatch, api)

    assert len(postings) == 1, "a dead detail page must not drop the posting"
    assert "Teaser." in postings[0].description


def test_detail_limit_bounds_the_detail_fanout(monkeypatch):
    listings = [{"id": i, "title": f"Coach {i}"} for i in range(6)]
    api = FakeGov(
        {1: {"items": listings}},
        details=lambda url: {"description": LONG_BODY},
    )
    postings = run_gov(monkeypatch, api, {"detail_limit": 2})

    assert len(api.detail_calls) == 2
    assert len(postings) == 6, "postings past the detail budget are still yielded"
    assert LONG_BODY[:40] in postings[0].description
    assert LONG_BODY[:40] not in postings[5].description


def test_detail_fields_fill_gaps_left_by_the_list(monkeypatch):
    api = FakeGov(
        {1: {"items": [{"id": 4412, "title": "Coach"}]}},
        details={
            "https://www.governmentjobs.com/jobs/4412": {
                "description": LONG_BODY,
                "salaryDisplay": "$65,000.00 Annually",
                "department": "Fire Wellness",
                "jobType": "Full Time",
                "datePosted": "2026-07-15",
                "location": "Austin, TX",
            }
        },
    )
    posting = run_gov(monkeypatch, api)[0]

    assert posting.compensation == "$65,000.00 Annually"
    assert posting.department == "Fire Wellness"
    assert posting.location == "Austin, TX"
    assert posting.posted_at is not None and posting.posted_at.month == 7
    assert posting.raw["detail"]["jobType"] == "Full Time"


# ==========================================================================
# governmentjobs: pagination and resilience
# ==========================================================================


def test_pagination_walks_pages_until_total_pages(monkeypatch):
    api = FakeGov(
        {
            1: {"items": [{"id": 1, "title": "A"}, {"id": 2, "title": "B"}], "totalPages": 2},
            2: {"items": [{"id": 3, "title": "C"}], "totalPages": 2},
        }
    )
    postings = run_gov(monkeypatch, api, {"detail_limit": 0})

    assert [params["page"] for _, params in api.list_calls] == [1, 2]
    assert [posting.source_id for posting in postings] == ["1", "2", "3"]


def test_pagination_stops_at_max_pages(monkeypatch):
    def endless(page):
        return {"items": [{"id": f"{page}-{i}", "title": "Coach"} for i in range(2)]}

    api = FakeGov(endless)
    postings = run_gov(monkeypatch, api, {"max_pages": 3, "detail_limit": 0})

    assert len(api.list_calls) == 3
    assert len(postings) == 6


def test_pagination_stops_when_a_tenant_ignores_the_page_parameter(monkeypatch):
    api = FakeGov(lambda page: {"items": [{"id": 1, "title": "Coach"}]})
    postings = run_gov(monkeypatch, api, {"max_pages": 5, "detail_limit": 0})

    assert len(postings) == 1
    assert len(api.list_calls) == 2, "one repeat page proves the parameter is ignored"


def test_first_page_failure_is_raised_rather_than_silently_empty(monkeypatch):
    api = FakeGov({1: FetchError("HTTP 503")})
    with pytest.raises(FetchError):
        run_gov(monkeypatch, api)


def test_a_later_page_failure_keeps_what_was_already_collected(monkeypatch):
    api = FakeGov(
        {
            1: {"items": [{"id": 1, "title": "Coach"}], "totalPages": 9},
            2: FetchError("HTTP 503"),
        }
    )
    postings = run_gov(monkeypatch, api, {"detail_limit": 0})
    assert [posting.source_id for posting in postings] == ["1"]


def test_malformed_records_are_skipped_not_fatal(monkeypatch):
    api = FakeGov(
        {
            1: {
                "items": [
                    "not-a-dict",
                    {"id": 2},  # no title
                    {"title": "No id and no link"},  # no url
                    {"id": 4, "title": "Peer Fitness Trainer"},
                ]
            }
        }
    )
    postings = run_gov(monkeypatch, api, {"detail_limit": 0})

    assert [posting.source_id for posting in postings] == ["4"]


def test_remote_flag_from_the_location(monkeypatch):
    api = FakeGov(
        {
            1: {
                "items": [
                    {"id": 1, "title": "Wellness Coach", "location": "Remote - Statewide"},
                    {"id": 2, "title": "Wellness Coach", "location": "Austin, TX"},
                ]
            }
        }
    )
    postings = run_gov(monkeypatch, api, {"detail_limit": 0})

    assert postings[0].remote is True
    assert postings[1].remote is False


# ==========================================================================
# jobsrss: title parsing helpers
# ==========================================================================


def test_looks_like_location_accepts_real_states_only():
    assert looks_like_location("Austin, TX") is True
    assert looks_like_location("Colorado Springs, Colorado") is True
    assert looks_like_location("Remote") is True
    assert looks_like_location("Coach, Football") is False
    assert looks_like_location("Strength and Conditioning") is False


def test_split_dash_pattern_title_employer_location():
    title, employer, location = split_listing_title(
        "Tactical Strength and Conditioning Coach - Austin Fire Department - Austin, TX"
    )
    assert title == "Tactical Strength and Conditioning Coach"
    assert employer == "Austin Fire Department"
    assert location == "Austin, TX"


def test_split_at_pattern_with_a_parenthetical_location():
    title, employer, location = split_listing_title(
        "Athletic Trainer at Boston Police Department (Boston, MA)"
    )
    assert title == "Athletic Trainer"
    assert employer == "Boston Police Department"
    assert location == "Boston, MA"


def test_split_two_part_title_that_is_only_a_location():
    title, employer, location = split_listing_title("Tactical Strength Coach - Denver, CO")
    assert (title, employer, location) == ("Tactical Strength Coach", "", "Denver, CO")


def test_split_leaves_a_plain_title_alone():
    assert split_listing_title("Human Performance Dietitian") == (
        "Human Performance Dietitian",
        "",
        "",
    )


def test_split_does_not_treat_a_non_location_parenthetical_as_a_location():
    title, employer, location = split_listing_title(
        "Strength Coach - O2X Human Performance (Part Time)"
    )
    assert title == "Strength Coach"
    assert employer == "O2X Human Performance (Part Time)"
    assert location == ""


# ==========================================================================
# jobsrss: feed adapters
# ==========================================================================


def rss_feed(items: str) -> bytes:
    return f"<rss version='2.0'><channel>{items}</channel></rss>".encode()


ITEM = """
<item>
  <title>Tactical Strength and Conditioning Coach - Austin Fire Department - Austin, TX</title>
  <link>https://careers.nsca.com/jobs/8891</link>
  <guid>nsca-8891</guid>
  <pubDate>Wed, 15 Jul 2026 09:00:00 +0000</pubDate>
  <description>&lt;p&gt;CSCS and TSAC-F required. NFPA 1583 program experience preferred.&lt;/p&gt;</description>
</item>
"""


def run_rss(monkeypatch, body: bytes, options=None, name="nsca"):
    monkeypatch.setattr("tactical_jobs.sources.govjobs.fetch", lambda url, **kw: body)
    merged = {"url": "https://careers.nsca.com/rss", **(options or {})}
    return list(JobsRSSSource(name, merged).fetch())


def test_rss_item_maps_title_employer_and_location(monkeypatch):
    posting = run_rss(monkeypatch, rss_feed(ITEM))[0]

    assert posting.source == "jobsrss:nsca"
    assert posting.source_id == "nsca-8891"
    assert posting.url == "https://careers.nsca.com/jobs/8891"
    assert posting.title == "Tactical Strength and Conditioning Coach"
    assert posting.employer == "Austin Fire Department"
    assert posting.location == "Austin, TX"
    assert "CSCS and TSAC-F required" in posting.description
    assert posting.posted_at is not None and posting.posted_at.day == 15


def test_rss_keeps_the_original_title_in_the_description(monkeypatch):
    posting = run_rss(monkeypatch, rss_feed(ITEM))[0]
    assert "Listed as: Tactical Strength and Conditioning Coach - Austin Fire" in (
        posting.description
    )


def test_rss_leaves_an_unparsed_title_untouched(monkeypatch):
    item = """
    <item><title>Human Performance Dietitian</title>
    <link>https://careers.nsca.com/jobs/1</link>
    <description>RD credential required.</description></item>
    """
    posting = run_rss(monkeypatch, rss_feed(item), {"employer": "NSCA Career Center"})[0]

    assert posting.title == "Human Performance Dietitian"
    assert posting.employer == "NSCA Career Center"
    assert "Listed as:" not in posting.description


def test_employer_from_description_mode(monkeypatch):
    item = """
    <item><title>Cognitive Performance Specialist</title>
    <link>https://careers.aasp.org/jobs/12</link>
    <description>&lt;p&gt;Employer: O2X Human Performance&lt;/p&gt;
    &lt;p&gt;Location: Quantico, VA&lt;/p&gt;
    &lt;p&gt;Embedded with Naval Special Warfare.&lt;/p&gt;</description></item>
    """
    posting = run_rss(monkeypatch, rss_feed(item), {"employer_from": "description"})[0]

    assert posting.employer == "O2X Human Performance"
    assert posting.location == "Quantico, VA"


def test_employer_from_description_falls_back_to_the_first_line_pattern(monkeypatch):
    item = """
    <item><title>Performance Dietitian</title>
    <link>https://careers.acsm.org/jobs/3</link>
    <description>Performance Dietitian at EXOS - Fort Campbell, KY</description></item>
    """
    posting = run_rss(monkeypatch, rss_feed(item), {"employer_from": "description"})[0]
    assert posting.employer == "EXOS"


def test_employer_from_fixed_mode(monkeypatch):
    posting = run_rss(
        monkeypatch,
        rss_feed(ITEM),
        {"employer_from": "fixed", "fixed_employer": "NSCA Career Center"},
    )[0]

    assert posting.employer == "NSCA Career Center"
    # Fixed employer does not disable title cleanup or location parsing.
    assert posting.title == "Tactical Strength and Conditioning Coach"
    assert posting.location == "Austin, TX"


def test_employer_from_title_is_the_default(monkeypatch):
    assert run_rss(monkeypatch, rss_feed(ITEM))[0].employer == "Austin Fire Department"


def test_employer_falls_back_through_option_then_source_name(monkeypatch):
    item = """
    <item><title>Athletic Trainer</title>
    <link>https://careers.nata.org/jobs/5</link></item>
    """
    assert run_rss(monkeypatch, rss_feed(item))[0].employer == "nsca"
    assert (
        run_rss(monkeypatch, rss_feed(item), {"fixed_employer": "NATA"})[0].employer
        == "NATA"
    )


def test_location_option_is_the_last_resort(monkeypatch):
    item = """
    <item><title>Athletic Trainer</title>
    <link>https://careers.nata.org/jobs/5</link></item>
    """
    posting = run_rss(monkeypatch, rss_feed(item), {"location": "Fort Bragg, NC"})[0]
    assert posting.location == "Fort Bragg, NC"


def test_content_encoded_wins_when_it_is_the_fuller_body(monkeypatch):
    item = """
    <item><title>Strength Coach</title>
    <link>https://careers.cscca.org/jobs/7</link>
    <description>Truncated teaser...</description>
    <content:encoded xmlns:content="http://purl.org/rss/1.0/modules/content/">
      &lt;p&gt;Full posting. CSCS required. Secret clearance required.&lt;/p&gt;
    </content:encoded></item>
    """
    posting = run_rss(monkeypatch, rss_feed(item))[0]
    assert "Secret clearance required" in posting.description
    assert "Truncated teaser" not in posting.description


def test_items_without_a_title_or_link_are_skipped(monkeypatch):
    items = """
    <item><link>https://careers.nsca.com/jobs/1</link></item>
    <item><title>No link here</title></item>
    """ + ITEM
    postings = run_rss(monkeypatch, rss_feed(items))
    assert [posting.source_id for posting in postings] == ["nsca-8891"]


def test_a_permalink_guid_can_stand_in_for_a_missing_link(monkeypatch):
    item = """
    <item><title>Athletic Trainer</title>
    <guid isPermaLink="true">https://careers.nata.org/jobs/5</guid></item>
    """
    posting = run_rss(monkeypatch, rss_feed(item))[0]
    assert posting.url == "https://careers.nata.org/jobs/5"


def test_atom_feed_is_parsed(monkeypatch):
    feed = """<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom">
      <entry>
        <title>Human Performance Dietitian at Naval Special Warfare (Coronado, CA)</title>
        <link rel="alternate" href="https://careers.example.org/jobs/9"/>
        <id>tag:example,2026:9</id>
        <updated>2026-07-10T12:00:00Z</updated>
        <content type="html">&lt;p&gt;RD credential and Secret clearance required.&lt;/p&gt;</content>
      </entry>
    </feed>""".encode()
    posting = run_rss(monkeypatch, feed)[0]

    assert posting.title == "Human Performance Dietitian"
    assert posting.employer == "Naval Special Warfare"
    assert posting.location == "Coronado, CA"
    assert posting.url == "https://careers.example.org/jobs/9"
    assert posting.source_id == "tag:example,2026:9"
    assert "RD credential" in posting.description
    assert posting.posted_at is not None and posting.posted_at.month == 7


def test_remote_titles_set_the_remote_flag(monkeypatch):
    item = """
    <item><title>Cognitive Performance Specialist - O2X - Remote</title>
    <link>https://careers.aasp.org/jobs/22</link></item>
    """
    posting = run_rss(monkeypatch, rss_feed(item))[0]
    assert posting.remote is True
    assert posting.location == "Remote"


def test_rss_url_is_required():
    with pytest.raises(KeyError):
        list(JobsRSSSource("x", {}).fetch())


def test_invalid_xml_is_reported(monkeypatch):
    with pytest.raises(RuntimeError):
        run_rss(monkeypatch, b"<rss><channel>")


# ==========================================================================
# genericjson: dot-path resolver
# ==========================================================================


def test_resolve_path_walks_nested_keys():
    payload = {"data": {"jobs": [{"name": "Coach"}]}}
    assert resolve_path(payload, "data.jobs.0.name") == "Coach"


def test_resolve_path_returns_none_for_a_missing_key():
    assert resolve_path({"data": {}}, "data.jobs.0.name") is None
    assert resolve_path({}, "content.html") is None


def test_resolve_path_returns_none_instead_of_indexing_a_scalar():
    assert resolve_path({"title": "Coach"}, "title.name") is None


def test_resolve_path_handles_list_indices_and_overflow():
    payload = {"jobs": ["a", "b"]}
    assert resolve_path(payload, "jobs.1") == "b"
    assert resolve_path(payload, "jobs.9") is None
    assert resolve_path(payload, "jobs.name") is None


def test_resolve_path_empty_path_returns_the_payload():
    payload = [{"name": "Coach"}]
    assert resolve_path(payload, "") is payload
    assert resolve_path(payload, None) is payload


# ==========================================================================
# genericjson: adapter
# ==========================================================================


API_URL = "https://careers.example.org/api/jobs"

FIELD_MAP = {
    "title": "name",
    "url": "links.self",
    "description": "content.html",
    "source_id": "reference",
    "employer": "org.name",
    "location": "place.display",
    "posted_at": "published",
    "department": "org.unit",
    "compensation": "pay.display",
}

RECORD = {
    "name": "Human Performance Coach",
    "reference": "HPC-9",
    "links": {"self": "/jobs/9"},
    "content": {"html": "<p>Embedded with 3rd Special Forces Group. CSCS required.</p>"},
    "org": {"name": "Amentum", "unit": "Health Services"},
    "place": {"display": "Fort Bragg, NC"},
    "pay": {"display": "$85,000 - $95,000 Annually"},
    "published": "2026-07-05T00:00:00Z",
}


class FakeAPI:
    def __init__(self, payloads):
        self.payloads = payloads
        self.calls: list[str] = []

    def fetch_json(self, url, params=None, headers=None, **kwargs):
        self.calls.append(url)
        payload = self.payloads(url) if callable(self.payloads) else self.payloads.get(url)
        if payload is None:
            raise FetchError(f"HTTP 404 for {url}")
        if isinstance(payload, Exception):
            raise payload
        return payload

    def install(self, monkeypatch):
        monkeypatch.setattr("tactical_jobs.sources.govjobs.fetch_json", self.fetch_json)
        return self


def run_generic(monkeypatch, payloads, options, name="example"):
    FakeAPI(payloads).install(monkeypatch)
    merged = {"url": API_URL, **options}
    return list(GenericJSONSource(name, merged).fetch())


def test_generic_maps_every_configured_field(monkeypatch):
    postings = run_generic(
        monkeypatch,
        {API_URL: {"data": {"jobs": [RECORD]}}},
        {"records_path": "data.jobs", "field_map": FIELD_MAP},
    )
    posting = postings[0]

    assert posting.source == "genericjson:example"
    assert posting.source_id == "HPC-9"
    assert posting.title == "Human Performance Coach"
    assert posting.employer == "Amentum"
    assert posting.location == "Fort Bragg, NC"
    assert posting.department == "Health Services"
    assert posting.compensation == "$85,000 - $95,000 Annually"
    assert "3rd Special Forces Group" in posting.description
    assert posting.posted_at is not None and posting.posted_at.day == 5


def test_generic_empty_records_path_means_the_root_is_the_array(monkeypatch):
    postings = run_generic(
        monkeypatch,
        {API_URL: [RECORD]},
        {"field_map": FIELD_MAP},
    )
    assert len(postings) == 1


def test_generic_relative_urls_resolve_against_the_endpoint(monkeypatch):
    posting = run_generic(
        monkeypatch, {API_URL: [RECORD]}, {"field_map": FIELD_MAP}
    )[0]
    assert posting.url == "https://careers.example.org/jobs/9"


def test_generic_absolute_urls_are_left_alone(monkeypatch):
    record = {**RECORD, "links": {"self": "https://other.example.com/jobs/9"}}
    posting = run_generic(
        monkeypatch, {API_URL: [record]}, {"field_map": FIELD_MAP}
    )[0]
    assert posting.url == "https://other.example.com/jobs/9"


def test_generic_field_map_requires_title_and_url():
    with pytest.raises(KeyError):
        list(GenericJSONSource("x", {"url": API_URL, "field_map": {"title": "name"}}).fetch())
    with pytest.raises(KeyError):
        list(GenericJSONSource("x", {"url": API_URL, "field_map": {"url": "link"}}).fetch())


def test_generic_field_map_is_required():
    with pytest.raises(KeyError):
        list(GenericJSONSource("x", {"url": API_URL}).fetch())


def test_generic_records_without_a_title_or_url_are_skipped(monkeypatch):
    payload = [
        {"name": "", "links": {"self": "/jobs/1"}},
        {"name": "No link", "links": {}},
        "not-a-record",
        RECORD,
    ]
    postings = run_generic(monkeypatch, {API_URL: payload}, {"field_map": FIELD_MAP})
    assert [posting.source_id for posting in postings] == ["HPC-9"]


def test_generic_accepts_several_candidate_paths_per_field(monkeypatch):
    record = {"jobTitle": "Athletic Trainer", "link": "/jobs/4"}
    postings = run_generic(
        monkeypatch,
        {API_URL: [record]},
        {"field_map": {"title": ["name", "jobTitle"], "url": ["links.self", "link"]}},
    )
    assert postings[0].title == "Athletic Trainer"
    assert postings[0].url == "https://careers.example.org/jobs/4"


def test_generic_concatenates_every_description_path(monkeypatch):
    record = {
        "name": "Coach",
        "link": "/jobs/4",
        "summary": "Support the H2F program.",
        "qualifications": "<ul><li>CSCS required</li></ul>",
    }
    posting = run_generic(
        monkeypatch,
        {API_URL: [record]},
        {
            "field_map": {
                "title": "name",
                "url": "link",
                "description": ["summary", "qualifications"],
            }
        },
    )[0]

    assert "Support the H2F program." in posting.description
    assert "CSCS required" in posting.description


def test_generic_remote_field_is_coerced(monkeypatch):
    field_map = {"title": "name", "url": "link", "remote": "isRemote"}
    payload = [
        {"name": "Coach", "link": "/jobs/1", "isRemote": True},
        {"name": "Coach", "link": "/jobs/2", "isRemote": "false"},
    ]
    postings = run_generic(monkeypatch, {API_URL: payload}, {"field_map": field_map})

    assert postings[0].remote is True
    assert postings[1].remote is False


def test_generic_remote_is_inferred_when_unmapped(monkeypatch):
    record = {"name": "Coach", "link": "/jobs/1", "place": "Remote - CONUS"}
    posting = run_generic(
        monkeypatch,
        {API_URL: [record]},
        {"field_map": {"title": "name", "url": "link", "location": "place"}},
    )[0]
    assert posting.remote is True


def test_generic_detail_fetch_fills_a_missing_description(monkeypatch):
    record = {"name": "Coach", "links": {"self": "/jobs/9", "detail": "/api/jobs/9"}}
    postings = run_generic(
        monkeypatch,
        {
            API_URL: {"jobs": [record]},
            "https://careers.example.org/api/jobs/9": {
                "body": {"html": "<p>CSCS required. Secret clearance required.</p>"},
                "unit": "Health Services",
            },
        },
        {
            "records_path": "jobs",
            "field_map": {
                "title": "name",
                "url": "links.self",
                "detail_url": "links.detail",
            },
            "detail_field_map": {"description": "body.html", "department": "unit"},
        },
    )
    posting = postings[0]

    assert "Secret clearance required" in posting.description
    assert posting.department == "Health Services"


def test_generic_detail_limit_bounds_the_fanout(monkeypatch):
    records = [
        {"name": f"Coach {i}", "links": {"self": f"/jobs/{i}", "detail": f"/api/jobs/{i}"}}
        for i in range(4)
    ]
    api = FakeAPI(
        lambda url: {"jobs": records}
        if url == API_URL
        else {"body": {"html": "<p>CSCS required.</p>"}}
    )
    api.install(monkeypatch)
    postings = list(
        GenericJSONSource(
            "example",
            {
                "url": API_URL,
                "records_path": "jobs",
                "detail_limit": 1,
                "field_map": {
                    "title": "name",
                    "url": "links.self",
                    "detail_url": "links.detail",
                },
                "detail_field_map": {"description": "body.html"},
            },
        ).fetch()
    )

    assert len([call for call in api.calls if call != API_URL]) == 1
    assert len(postings) == 4


def test_generic_detail_failure_keeps_the_posting(monkeypatch):
    record = {"name": "Coach", "links": {"self": "/jobs/9", "detail": "/api/jobs/9"}}
    postings = run_generic(
        monkeypatch,
        {API_URL: {"jobs": [record]}},  # the detail URL 404s
        {
            "records_path": "jobs",
            "field_map": {"title": "name", "url": "links.self", "detail_url": "links.detail"},
        },
    )
    assert len(postings) == 1
    assert postings[0].description == ""


def test_generic_bad_records_path_yields_nothing(monkeypatch):
    postings = run_generic(
        monkeypatch,
        {API_URL: {"data": {}}},
        {"records_path": "data.jobs", "field_map": FIELD_MAP},
    )
    assert postings == []


def test_generic_single_object_payload_is_treated_as_one_record(monkeypatch):
    postings = run_generic(
        monkeypatch, {API_URL: {"job": RECORD}}, {"records_path": "job", "field_map": FIELD_MAP}
    )
    assert len(postings) == 1


def test_generic_duplicate_records_are_collapsed(monkeypatch):
    postings = run_generic(
        monkeypatch, {API_URL: [RECORD, dict(RECORD)]}, {"field_map": FIELD_MAP}
    )
    assert len(postings) == 1


# ==========================================================================
# registration surface
# ==========================================================================


def test_kinds_are_unique_and_exported():
    assert GovernmentJobsSource.kind == "governmentjobs"
    assert JobsRSSSource.kind == "jobsrss"
    assert GenericJSONSource.kind == "genericjson"
    assert GOV_SOURCES == (GovernmentJobsSource, JobsRSSSource, GenericJSONSource)
    assert len({cls.kind for cls in GOV_SOURCES}) == 3


def test_module_imports_only_the_standard_library_and_the_project():
    """No third-party dependency may creep in: this project ships stdlib only."""
    import ast

    module = Path(__file__).resolve().parents[1] / "tactical_jobs" / "sources" / "govjobs.py"
    tree = ast.parse(module.read_text(encoding="utf-8"))
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            roots.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and not node.level:
            roots.add((node.module or "").split(".")[0])

    assert roots <= {"logging", "re", "xml", "typing", "urllib", "__future__"}, roots


# ==========================================================================
# regressions found in adversarial review
# ==========================================================================


def test_flatten_reads_link_objects():
    """A link emitted as ``{"href": ...}`` must still produce a url."""
    assert flatten({"href": "/careers/austintx/jobs/1"}) == "/careers/austintx/jobs/1"
    assert flatten({"url": "https://x/1"}) == "https://x/1"
    # An explicit display key still wins over the link.
    assert flatten({"name": "Fire", "href": "/x"}) == "Fire"


def test_flatten_composes_an_address_object():
    assert flatten({"city": "Austin", "state": "TX"}) == "Austin, TX"
    assert flatten({"City": "Mesa", "StateProvince": "AZ"}) == "Mesa, AZ"
    assert flatten({"city": "Austin"}) == "Austin"
    assert flatten({"unrelated": 1}) == ""


def test_a_record_whose_only_link_is_an_object_is_not_dropped(monkeypatch):
    """Regression: an object-shaped link flattened to "" and lost the record."""
    api = FakeGov(
        {
            1: {
                "items": [
                    {"title": "Peer Fitness Trainer", "link": {"href": "/careers/austintx/jobs/1"}}
                ]
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]
    assert posting.url == "https://www.governmentjobs.com/careers/austintx/jobs/1"


def test_a_nested_location_object_is_composed(monkeypatch):
    """Regression: ``{"location": {"city": ..., "state": ...}}`` mapped to ""."""
    api = FakeGov(
        {
            1: {
                "items": [
                    {
                        "id": 1,
                        "title": "Wellness Coordinator",
                        "location": {"city": "Austin", "state": "TX"},
                    }
                ]
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]
    assert posting.location == "Austin, TX"


def test_total_pages_as_a_string_still_stops_pagination(monkeypatch):
    """Regression: a stringified page count was ignored and pages kept loading."""
    api = FakeGov(
        {
            1: {"items": [{"id": 1, "title": "Coach"}], "totalPages": "1"},
            2: {"items": [{"id": 2, "title": "Coach"}]},
        }
    )
    postings = run_gov(monkeypatch, api, {"detail_limit": 0})

    assert len(api.list_calls) == 1
    assert [posting.source_id for posting in postings] == ["1"]


def test_a_detail_payload_wrapped_in_an_array_is_still_read(monkeypatch):
    """Regression: a one-element array detail body was discarded after fetching."""
    api = FakeGov(
        {1: {"items": [{"id": 4412, "title": "Coach", "description": "Teaser."}]}},
        details={
            "https://www.governmentjobs.com/jobs/4412": [
                {"definition": f"<p>{LONG_BODY}</p>"}
            ]
        },
    )
    posting = run_gov(monkeypatch, api)[0]
    assert "Austin Fire Department Wellness Division" in posting.description


def test_relative_tenant_links_resolve_against_a_url_override(monkeypatch):
    """Regression: an override host's relative links pointed at governmentjobs.com."""
    override = "https://agency.jobs.example.gov/api/openings?format=json"
    api = FakeGov(
        {1: {"items": [{"title": "Coach", "detailUrl": "/jobs/1"}]}},
        details={"https://agency.jobs.example.gov/jobs/1": {"description": LONG_BODY}},
        list_url=override,
    )
    posting = run_gov(monkeypatch, api, {"url": override})[0]

    assert posting.url == "https://agency.jobs.example.gov/jobs/1"
    assert api.detail_calls[0][0] == "https://agency.jobs.example.gov/jobs/1"
    assert LONG_BODY[:40] in posting.description


def test_as_int_falls_back_instead_of_raising():
    assert as_int(None, 5) == 5
    assert as_int("", 5) == 5
    assert as_int("3", 5) == 3
    assert as_int(7, 5) == 7
    assert as_int("many", 5) == 5
    assert as_int(True, 5) == 5


def test_blank_numeric_options_do_not_abort_the_source(monkeypatch):
    """Regression: ``int(None)`` on a blank option killed the whole source."""
    api = FakeGov({1: {"items": [{"id": 1, "title": "Coach", "description": LONG_BODY}]}})
    postings = run_gov(
        monkeypatch,
        api,
        {"detail_limit": None, "max_pages": "", "detail_min_chars": "nope"},
    )
    assert [posting.source_id for posting in postings] == ["1"]


def test_generic_blank_detail_limit_does_not_abort(monkeypatch):
    postings = run_generic(
        monkeypatch,
        {API_URL: [RECORD]},
        {"field_map": FIELD_MAP, "detail_limit": None},
    )
    assert len(postings) == 1


def test_looks_like_location_rejects_a_phrase_that_merely_contains_a_hint():
    """Regression: substring matching read "Virtual Reality Program" as remote."""
    assert looks_like_location("Virtual Reality Program") is False
    assert looks_like_location("Remote Sensing Analyst") is False
    assert looks_like_location("Anywhere Fitness Company") is False
    # Genuine remote labels, with and without a qualifier, still pass.
    assert looks_like_location("Remote") is True
    assert looks_like_location("Remote - Statewide") is True
    assert looks_like_location("Remote, US") is True
    assert looks_like_location("Telework (CONUS)") is True
    assert looks_like_location("Remote, Texas") is True


def test_split_keeps_the_employer_when_the_tail_is_not_a_location():
    title, employer, location = split_listing_title("Coach - Virtual Reality Program")
    assert (title, employer, location) == ("Coach", "Virtual Reality Program", "")


def test_rss_relative_item_link_resolves_against_the_feed_url(monkeypatch):
    """Regression: a root-relative <link> dropped the item entirely."""
    item = """
    <item><title>Athletic Trainer</title>
    <link>/jobs/8891</link></item>
    """
    monkeypatch.setattr(
        "tactical_jobs.sources.govjobs.fetch", lambda url, **kw: rss_feed(item)
    )
    postings = list(
        JobsRSSSource("nsca", {"url": "https://careers.nsca.com/feeds/jobs.rss"}).fetch()
    )
    assert postings[0].url == "https://careers.nsca.com/jobs/8891"


def test_rss_protocol_relative_item_link_resolves(monkeypatch):
    item = """
    <item><title>Athletic Trainer</title>
    <link>//cdn.nsca.com/jobs/8891</link></item>
    """
    posting = run_rss(monkeypatch, rss_feed(item))[0]
    assert posting.url == "https://cdn.nsca.com/jobs/8891"


def test_rss_non_url_guid_is_not_mistaken_for_a_link(monkeypatch):
    """An opaque guid is an identifier, not a URL, so the item has no link."""
    item = """
    <item><title>Athletic Trainer</title>
    <guid isPermaLink="false">nsca-8891</guid></item>
    """
    assert run_rss(monkeypatch, rss_feed(item)) == []


def test_unicode_survives_every_adapter(monkeypatch):
    api = FakeGov(
        {1: {"items": [{"id": 1, "title": "Entraîneur – Pôle", "location": "Québec, QC"}]}}
    )
    assert run_gov(monkeypatch, api, {"detail_limit": 0})[0].title == "Entraîneur – Pôle"

    item = (
        "<item><title>Kraftrainer - Feuerwehr München - Austin, TX</title>"
        "<link>https://x/1</link>"
        "<description>Fußball und Ernährung.</description></item>"
    )
    posting = run_rss(monkeypatch, rss_feed(item))[0]
    assert posting.employer == "Feuerwehr München"
    assert "Fußball" in posting.description

    posting = run_generic(
        monkeypatch,
        {API_URL: [{"name": "Entraîneur", "link": "/1", "d": "<p>Fußball</p>"}]},
        {"field_map": {"title": "name", "url": "link", "description": "d"}},
    )[0]
    assert posting.title == "Entraîneur"
    assert posting.description == "Fußball"


def test_empty_and_none_payloads_never_crash(monkeypatch):
    assert run_gov(monkeypatch, FakeGov({1: {}}), {"detail_limit": 0}) == []
    assert run_gov(monkeypatch, FakeGov({1: "unexpected string"}), {"detail_limit": 0}) == []
    assert run_gov(monkeypatch, FakeGov({1: {"items": [None, 7]}}), {"detail_limit": 0}) == []
    assert run_generic(monkeypatch, {API_URL: []}, {"field_map": FIELD_MAP}) == []
    assert run_generic(monkeypatch, {API_URL: [None, 7]}, {"field_map": FIELD_MAP}) == []


def test_a_salary_object_is_rendered(monkeypatch):
    """Regression: an object-shaped salary flattened to "" and pay was lost."""
    api = FakeGov(
        {
            1: {
                "items": [
                    {
                        "id": 1,
                        "title": "Coach",
                        "salary": {"min": 62000, "max": 78000, "frequency": "Annually"},
                    }
                ]
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]
    assert posting.compensation == "62000 - 78000 Annually"
    assert "Salary: 62000 - 78000 Annually." in posting.description


def test_a_one_sided_salary_object_is_rendered(monkeypatch):
    api = FakeGov({1: {"items": [{"id": 1, "title": "Coach", "payRange": {"from": "$34.00"}}]}})
    assert run_gov(monkeypatch, api, {"detail_limit": 0})[0].compensation == "$34.00"


def test_none_valued_fields_do_not_crash_the_mapping(monkeypatch):
    api = FakeGov(
        {
            1: {
                "items": [
                    {
                        "id": 1,
                        "title": "Coach",
                        "location": None,
                        "salary": None,
                        "department": None,
                        "datePosted": None,
                        "detailUrl": None,
                    }
                ]
            }
        }
    )
    posting = run_gov(monkeypatch, api, {"detail_limit": 0})[0]
    assert (posting.location, posting.compensation, posting.department) == ("", None, None)
    assert posting.posted_at is None
