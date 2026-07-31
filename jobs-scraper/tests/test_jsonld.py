"""schema.org JSON-LD extractor tests.

Every test drives the adapter through a fake ``fetch`` so the suite runs with
no outbound network, using payload shapes captured from real career pages
(iCIMS, Taleo, SuccessFactors, and hand-rolled site templates all emit
variations of these).
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402

from tactical_jobs.sources.jsonld import (  # noqa: E402
    JSONLD_SOURCES,
    JSONLDSource,
    is_job_posting,
)

PAGE_URL = "https://careers.example.com/job/12345"


def _page(*blocks: str, extra: str = "") -> bytes:
    """Wrap JSON-LD blocks in a plausible career page."""
    scripts = "".join(
        f'<script type="application/ld+json">{block}</script>' for block in blocks
    )
    return (
        "<html><head><title>Careers</title>"
        '<script type="text/javascript">var tracker = {"jobId": "12345"};</script>'
        f"{scripts}</head><body><h1>Apply</h1>{extra}</body></html>"
    ).encode()


def _install(monkeypatch, pages: dict[str, bytes], *, log: list[str] | None = None):
    """Replace the module's ``fetch`` with a lookup over captured pages."""

    def fake_fetch(url, **kwargs):
        if log is not None:
            log.append(url)
        try:
            return pages[url]
        except KeyError:
            raise RuntimeError(f"unmocked url {url}")

    monkeypatch.setattr("tactical_jobs.sources.jsonld.fetch", fake_fetch)


def _run(monkeypatch, pages, options, *, log=None):
    _install(monkeypatch, pages, log=log)
    return list(JSONLDSource("example", options).fetch())


BARE_JOB = """
{
  "@context": "https://schema.org/",
  "@type": "JobPosting",
  "title": "Tactical Strength and Conditioning Coach",
  "identifier": {"@type": "PropertyValue", "name": "Req", "value": "REQ-9981"},
  "url": "https://careers.example.com/job/12345",
  "datePosted": "2026-07-14",
  "validThrough": "2026-09-30T00:00:00",
  "employmentType": "FULL_TIME",
  "description": "<p>Embed with a USASOC THOR3 team.</p><ul><li>CSCS required</li></ul>",
  "qualifications": "<p>TSAC-F preferred. Active Secret clearance.</p>",
  "occupationalCategory": "Human Performance",
  "hiringOrganization": {"@type": "Organization", "name": "Leidos"},
  "jobLocation": {
    "@type": "Place",
    "address": {
      "@type": "PostalAddress",
      "addressLocality": "Fort Bragg",
      "addressRegion": "NC",
      "addressCountry": "US"
    }
  },
  "baseSalary": {
    "@type": "MonetaryAmount",
    "currency": "USD",
    "value": {"@type": "QuantitativeValue", "minValue": 85000, "maxValue": 110000, "unitText": "YEAR"}
  }
}
"""


def test_bare_job_posting_object_maps_every_core_field(monkeypatch):
    postings = _run(monkeypatch, {PAGE_URL: _page(BARE_JOB)}, {"urls": [PAGE_URL]})
    assert len(postings) == 1
    posting = postings[0]
    assert posting.source == "jsonld:example"
    assert posting.source_id == "REQ-9981"
    assert posting.title == "Tactical Strength and Conditioning Coach"
    assert posting.employer == "Leidos"
    assert posting.url == PAGE_URL
    assert posting.location == "Fort Bragg, NC, US"
    assert posting.department == "Human Performance"
    assert posting.posted_at is not None and posting.posted_at.year == 2026


def test_description_captures_html_and_every_narrative_field(monkeypatch):
    """qualifications is where the certs live; dropping it blinds enrichment."""
    posting = _run(monkeypatch, {PAGE_URL: _page(BARE_JOB)}, {"urls": [PAGE_URL]})[0]
    assert "THOR3" in posting.description
    assert "CSCS required" in posting.description
    assert "TSAC-F" in posting.description
    assert "Secret clearance" in posting.description
    # Block tags become separators rather than gluing words together.
    assert "teamCSCS" not in posting.description
    assert "<p>" not in posting.description
    # employmentType is folded in as a labelled fact.
    assert "Employment type: FULL_TIME." in posting.description


def test_valid_through_is_kept_in_raw(monkeypatch):
    posting = _run(monkeypatch, {PAGE_URL: _page(BARE_JOB)}, {"urls": [PAGE_URL]})[0]
    assert posting.raw["validThrough"] == "2026-09-30T00:00:00"
    assert posting.raw["sourcePageUrl"] == PAGE_URL


def test_salary_range_maps_to_compensation(monkeypatch):
    posting = _run(monkeypatch, {PAGE_URL: _page(BARE_JOB)}, {"urls": [PAGE_URL]})[0]
    assert posting.compensation == "$85000 - $110000 per YEAR"


def test_hourly_single_value_salary(monkeypatch):
    block = """
    {"@type": "JobPosting", "title": "Athletic Trainer",
     "baseSalary": {"@type": "MonetaryAmount", "currency": "USD",
                    "value": {"@type": "QuantitativeValue", "value": 48.5, "unitText": "HOUR"}}}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.compensation == "$48.5 per HOUR"


def test_non_usd_salary_keeps_the_currency_code(monkeypatch):
    block = """
    {"@type": "JobPosting", "title": "Performance Dietitian",
     "baseSalary": {"@type": "MonetaryAmount", "currency": "EUR",
                    "value": {"minValue": 60000.0, "maxValue": 72000.0, "unitText": "YEAR"}}}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    # Floats must not render as "60000.0".
    assert posting.compensation == "60000 - 72000 EUR per YEAR"


def test_missing_salary_leaves_compensation_none(monkeypatch):
    block = '{"@type": "JobPosting", "title": "Human Performance Coach"}'
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.compensation is None


def test_list_of_objects_picks_out_only_job_postings(monkeypatch):
    block = """
    [
      {"@type": "WebSite", "name": "Example Careers"},
      {"@type": "BreadcrumbList", "itemListElement": []},
      {"@type": "JobPosting", "title": "Cognitive Performance Specialist",
       "url": "https://careers.example.com/job/777",
       "hiringOrganization": {"name": "Booz Allen Hamilton"}}
    ]
    """
    postings = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})
    assert len(postings) == 1
    assert postings[0].title == "Cognitive Performance Specialist"
    assert postings[0].employer == "Booz Allen Hamilton"


def test_graph_container_is_unwrapped(monkeypatch):
    block = """
    {"@context": "https://schema.org", "@graph": [
      {"@type": "Organization", "name": "Amentum"},
      {"@type": "JobPosting", "title": "Physical Therapist (POTFF)",
       "identifier": "POTFF-42",
       "hiringOrganization": {"name": "Amentum"}}
    ]}
    """
    postings = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})
    assert [p.title for p in postings] == ["Physical Therapist (POTFF)"]
    assert postings[0].source_id == "POTFF-42"


def test_type_given_as_a_list_is_recognized(monkeypatch):
    block = """
    {"@type": ["JobPosting", "Thing"], "title": "Strength Coach (H2F)",
     "identifier": {"value": "H2F-1"}}
    """
    postings = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})
    assert len(postings) == 1
    assert postings[0].title == "Strength Coach (H2F)"


def test_fully_qualified_type_url_is_recognized():
    assert is_job_posting({"@type": "https://schema.org/JobPosting"})
    assert is_job_posting({"@type": "schema:JobPosting"})
    assert is_job_posting({"@type": ["JobPosting"]})
    assert not is_job_posting({"@type": "Organization"})
    assert not is_job_posting({"@type": None})
    assert not is_job_posting("JobPosting")


def test_job_location_as_a_list_keeps_every_site(monkeypatch):
    block = """
    {"@type": "JobPosting", "title": "Tactical Athletic Trainer",
     "jobLocation": [
       {"@type": "Place", "address": {"addressLocality": "Coronado", "addressRegion": "CA", "addressCountry": "US"}},
       {"@type": "Place", "address": {"addressLocality": "Virginia Beach", "addressRegion": "VA"}}
     ]}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.location == "Coronado, CA, US; Virginia Beach, VA"


def test_address_country_as_an_object_is_flattened(monkeypatch):
    block = """
    {"@type": "JobPosting", "title": "Performance Dietitian",
     "jobLocation": {"address": {"addressLocality": "Fort Campbell", "addressRegion": "KY",
                                 "addressCountry": {"@type": "Country", "name": "US"}}}}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.location == "Fort Campbell, KY, US"


def test_string_job_location_falls_back_to_the_place_name(monkeypatch):
    block = """
    {"@type": "JobPosting", "title": "Fire/EMS Performance Coach",
     "jobLocation": {"@type": "Place", "name": "Camp Lejeune, NC"}}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.location == "Camp Lejeune, NC"


def test_telecommute_marks_the_posting_remote(monkeypatch):
    block = """
    {"@type": "JobPosting", "title": "Remote Performance Analyst",
     "jobLocationType": "TELECOMMUTE"}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.remote is True
    assert posting.location == "Remote"


def test_applicant_location_requirements_imply_remote(monkeypatch):
    block = """
    {"@type": "JobPosting", "title": "Cognitive Performance Specialist",
     "applicantLocationRequirements": {"@type": "Country", "name": "USA"}}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.remote is True
    assert posting.location == "Remote - USA"


def test_onsite_posting_is_not_remote(monkeypatch):
    posting = _run(monkeypatch, {PAGE_URL: _page(BARE_JOB)}, {"urls": [PAGE_URL]})[0]
    assert posting.remote is False


def test_remote_wording_in_the_location_is_detected(monkeypatch):
    block = """
    {"@type": "JobPosting", "title": "Performance Coach",
     "jobLocation": {"address": {"addressLocality": "Remote", "addressCountry": "US"}}}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.remote is True


def test_page_without_json_ld_yields_nothing(monkeypatch):
    page = b"<html><body><h1>No structured data here</h1></body></html>"
    assert _run(monkeypatch, {PAGE_URL: page}, {"urls": [PAGE_URL]}) == []


def test_json_ld_without_a_job_posting_yields_nothing(monkeypatch):
    block = '{"@type": "Organization", "name": "KBR", "url": "https://kbr.com"}'
    assert _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]}) == []


def test_malformed_json_block_is_skipped_not_fatal(monkeypatch):
    broken = '{"@type": "JobPosting", "title": "Broken",,,}'
    postings = _run(
        monkeypatch, {PAGE_URL: _page(broken, BARE_JOB)}, {"urls": [PAGE_URL]}
    )
    # The valid sibling block on the same page still comes through.
    assert [p.source_id for p in postings] == ["REQ-9981"]


def test_cdata_wrapped_block_is_parsed(monkeypatch):
    block = '//<![CDATA[\n{"@type": "JobPosting", "title": "Wrapped Coach"}\n//]]>'
    postings = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})
    assert [p.title for p in postings] == ["Wrapped Coach"]


def test_job_posting_without_a_title_is_skipped(monkeypatch):
    block = '{"@type": "JobPosting", "description": "No title anywhere."}'
    assert _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]}) == []


def test_a_failing_page_is_skipped_and_the_run_continues(monkeypatch):
    good = "https://careers.example.com/job/ok"
    dead = "https://careers.example.com/job/dead"
    pages = {good: _page(BARE_JOB)}
    postings = _run(monkeypatch, pages, {"urls": [dead, good]})
    assert [p.source_id for p in postings] == ["REQ-9981"]


def test_source_id_falls_back_to_the_job_url_then_the_page_url(monkeypatch):
    with_url = '{"@type": "JobPosting", "title": "A", "url": "https://x.test/job/1"}'
    bare = '{"@type": "JobPosting", "title": "B"}'
    other = "https://careers.example.com/job/999"
    pages = {PAGE_URL: _page(with_url), other: _page(bare)}
    postings = _run(monkeypatch, pages, {"urls": [PAGE_URL, other]})
    assert postings[0].source_id == "https://x.test/job/1"
    assert postings[1].source_id == other
    assert postings[1].url == other


def test_at_id_is_used_as_the_url_when_url_is_absent(monkeypatch):
    block = '{"@type": "JobPosting", "title": "C", "@id": "https://x.test/job/7"}'
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert posting.url == "https://x.test/job/7"


def test_employer_option_backfills_a_missing_hiring_organization(monkeypatch):
    block = '{"@type": "JobPosting", "title": "Embedded Physical Therapist"}'
    posting = _run(
        monkeypatch,
        {PAGE_URL: _page(block)},
        {"urls": [PAGE_URL], "employer": "Naval Special Warfare Command"},
    )[0]
    assert posting.employer == "Naval Special Warfare Command"


def test_duplicate_postings_across_pages_are_emitted_once(monkeypatch):
    other = "https://careers.example.com/job/12345?src=feed"
    pages = {PAGE_URL: _page(BARE_JOB), other: _page(BARE_JOB)}
    postings = _run(monkeypatch, pages, {"urls": [PAGE_URL, other]})
    assert len(postings) == 1


SITEMAP = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <url><loc>https://careers.example.com/job/12345</loc></url>
  <url><loc>https://careers.example.com/about</loc></url>
</urlset>
""".encode()

SITEMAP_INDEX = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
  <sitemap><loc>https://careers.example.com/sitemap-jobs.xml</loc></sitemap>
</sitemapindex>
""".encode()


def test_sitemap_urls_are_fetched_and_parsed(monkeypatch):
    pages = {
        "https://careers.example.com/sitemap.xml": SITEMAP,
        PAGE_URL: _page(BARE_JOB),
        "https://careers.example.com/about": b"<html><body>About us</body></html>",
    }
    postings = _run(
        monkeypatch, pages, {"sitemap": "https://careers.example.com/sitemap.xml"}
    )
    assert [p.source_id for p in postings] == ["REQ-9981"]


def test_sitemap_index_is_followed_one_level(monkeypatch):
    pages = {
        "https://careers.example.com/sitemap.xml": SITEMAP_INDEX,
        "https://careers.example.com/sitemap-jobs.xml": SITEMAP,
        PAGE_URL: _page(BARE_JOB),
        "https://careers.example.com/about": b"<html><body>About us</body></html>",
    }
    requested: list[str] = []
    postings = _run(
        monkeypatch,
        pages,
        {"sitemap": "https://careers.example.com/sitemap.xml"},
        log=requested,
    )
    assert "https://careers.example.com/sitemap-jobs.xml" in requested
    assert [p.title for p in postings] == ["Tactical Strength and Conditioning Coach"]


def test_url_include_filters_the_pages_fetched(monkeypatch):
    pages = {
        "https://careers.example.com/sitemap.xml": SITEMAP,
        PAGE_URL: _page(BARE_JOB),
    }
    requested: list[str] = []
    postings = _run(
        monkeypatch,
        pages,
        {"sitemap": "https://careers.example.com/sitemap.xml", "url_include": ["/job/"]},
        log=requested,
    )
    assert "https://careers.example.com/about" not in requested
    assert len(postings) == 1


def test_max_urls_caps_the_fan_out(monkeypatch):
    urls = [f"https://careers.example.com/job/{n}" for n in range(10)]
    pages = {url: _page(f'{{"@type": "JobPosting", "title": "Coach {url[-1]}"}}') for url in urls}
    requested: list[str] = []
    postings = _run(monkeypatch, pages, {"urls": urls, "max_urls": 3}, log=requested)
    assert len(requested) == 3
    assert len(postings) == 3


def test_unreachable_sitemap_degrades_to_no_postings(monkeypatch):
    postings = _run(monkeypatch, {}, {"sitemap": "https://careers.example.com/gone.xml"})
    assert postings == []


def test_malformed_sitemap_xml_degrades_to_no_postings(monkeypatch):
    pages = {"https://careers.example.com/sitemap.xml": b"<urlset><url><loc>oops"}
    postings = _run(
        monkeypatch, pages, {"sitemap": "https://careers.example.com/sitemap.xml"}
    )
    assert postings == []


def test_delay_seconds_pauses_between_pages(monkeypatch):
    class _Clock:
        def __init__(self) -> None:
            self.slept: list[float] = []

        def sleep(self, seconds: float) -> None:
            self.slept.append(seconds)

    clock = _Clock()
    monkeypatch.setattr("tactical_jobs.sources.jsonld.time", clock)
    urls = [f"https://careers.example.com/job/{n}" for n in range(3)]
    pages = {url: _page(f'{{"@type": "JobPosting", "title": "Coach", "url": "{url}"}}') for url in urls}
    postings = _run(monkeypatch, pages, {"urls": urls, "delay_seconds": 0.25})
    assert len(postings) == 3
    # One pause between pages, none before the first.
    assert clock.slept == [0.25, 0.25]


def test_missing_urls_and_sitemap_raises_a_useful_key_error():
    with pytest.raises(KeyError) as excinfo:
        list(JSONLDSource("example", {}).fetch())
    assert "urls" in str(excinfo.value)


def test_a_single_url_string_is_accepted(monkeypatch):
    postings = _run(monkeypatch, {PAGE_URL: _page(BARE_JOB)}, {"urls": PAGE_URL})
    assert len(postings) == 1


def test_script_type_with_a_charset_suffix_is_still_read(monkeypatch):
    markup = (
        '<html><head><script type="application/ld+json; charset=UTF-8">'
        '{"@type": "JobPosting", "title": "Program Manager, Human Performance"}'
        "</script></head><body></body></html>"
    ).encode()
    postings = _run(monkeypatch, {PAGE_URL: markup}, {"urls": [PAGE_URL]})
    assert [p.title for p in postings] == ["Program Manager, Human Performance"]


def test_structured_requirement_objects_reach_the_description(monkeypatch):
    """Clearance and credential objects carry the signal enrichment mines."""
    block = """
    {"@type": "JobPosting", "title": "Human Performance Program Manager",
     "description": "Support SOCOM POTFF.",
     "educationRequirements": {"@type": "EducationalOccupationalCredential",
                               "credentialCategory": "master degree"},
     "securityClearanceRequirement": "Top Secret/SCI"}
    """
    posting = _run(monkeypatch, {PAGE_URL: _page(block)}, {"urls": [PAGE_URL]})[0]
    assert "POTFF" in posting.description
    assert "master degree" in posting.description
    assert "Security clearance: Top Secret/SCI." in posting.description


def test_module_exports_the_source_tuple():
    assert JSONLD_SOURCES == (JSONLDSource,)
    assert JSONLDSource.kind == "jsonld"
