"""Search-result harvest tests.

The filter here decides what counts as a job, and someone will quote the
resulting number. So these tests concentrate on the two ways the count goes
wrong: letting articles through (inflating it) and discarding real postings
(hiding them). The second failure already happened once -- a host allowlist
threw away 57 of 75 results, nearly all real openings -- so it gets the most
coverage.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.sources.searchresults import (  # noqa: E402
    SearchResultsSource,
    looks_like_posting,
    parse_results,
    rejection_reason,
)


def block(title: str, url: str, published: str = "", highlights: str = "") -> str:
    out = f"Title: {title}\nURL: {url}\n"
    if published:
        out += f"Published: {published}\n"
    out += f"Highlights: {highlights}\n\n---\n\n"
    return out


def one(title: str, url: str, **kw):
    return parse_results(block(title, url, **kw))[0]


# --------------------------------------------------------------------------
# Parsing
# --------------------------------------------------------------------------

def test_parses_multiple_records():
    text = block("A", "https://x.test/jobs/a") + block("B", "https://x.test/jobs/b")
    assert [r.title for r in parse_results(text)] == ["A", "B"]


def test_multiline_highlights_stay_with_their_result():
    text = (
        "Title: Coach\nURL: https://x.test/jobs/coach\nHighlights: first line\n"
        "second line\nthird line\n\n"
        "Title: Other\nURL: https://x.test/jobs/other\nHighlights: elsewhere\n"
    )
    results = parse_results(text)
    assert "second line" in results[0].text and "third line" in results[0].text
    assert "elsewhere" not in results[0].text


def test_result_without_a_url_is_dropped():
    assert parse_results("Title: Orphan\nHighlights: nothing\n") == []


def test_published_timestamp_is_parsed(tmp_path):
    src = tmp_path / "r.txt"
    src.write_text(block("Coach", "https://x.test/jobs/coach",
                         published="2026-06-11T12:02:04.000Z"))
    posting = list(SearchResultsSource("s", {"directory": str(tmp_path)}).fetch())[0]
    assert posting.posted_at is not None
    assert posting.posted_at.date().isoformat() == "2026-06-11"


def test_absent_timestamp_yields_no_date(tmp_path):
    (tmp_path / "r.txt").write_text(block("Coach", "https://x.test/jobs/coach"))
    posting = list(SearchResultsSource("s", {"directory": str(tmp_path)}).fetch())[0]
    assert posting.posted_at is None


# --------------------------------------------------------------------------
# Keeping real postings -- the regression that mattered
# --------------------------------------------------------------------------

def test_no_host_allowlist_long_tail_boards_are_kept():
    """Regression: a fixed host list discarded 57 of 75 results.

    Every URL below carried a real Serco/GDIT/Geneva Foundation opening and was
    being thrown away purely because its host was not on a hand-written list.
    """
    real = [
        "https://www.nexxt.com/jobs/h2fit-strength-conditioning-coach-fort-bragg-nc-3315038293-j",
        "https://us.trabajo.org/job-5003-f2146cca458089ccac1abdd47fa1cd6c",
        "https://unjoblink.org/job/details/400345/",
        "https://www.jobs-cast.com/job/D9mjpHkFF/h2f-installation-lead-coach-fort-polk",
        "https://clearedcareers.com/job/843303/special-operations-performance-dietitian",
        "https://serco-na.dejobs.org/quantico-va/h2fit-strength-conditioning-coach/9AD0EFD",
        "https://nsca.careerwebsite.com/job/h2fit-strength-and-conditioning-coaches/80404193/",
        "https://recruiting.paylocity.com/recruiting/jobs/Details/4154042/Tanaq/Athletic-Trainer",
        "https://lensa.com/job-v1/serco/fort-lee-va/coach/212ac5fb4702078ac6e3e84e63e0f89d",
        "https://www.gdit.com/careers/job/fa8a6d1d5/cognitive-performance-specialist/",
        "https://career360.snhu.edu/jobs/resolution-think-llc-strength-and-conditioning-coach/",
        "https://clarksqn.com/workspread/job/strength-and-conditioning-coach-scc-army-h2f",
    ]
    for url in real:
        assert looks_like_posting(one("Strength and Conditioning Coach", url)), url


# --------------------------------------------------------------------------
# Rejecting things that are not postings
# --------------------------------------------------------------------------

def test_rejects_editorial_titles():
    for title in (
        "Tactical strength and conditioning: A career overview",
        "How to Get a Job in Tactical Human Performance",
        "Serco Awarded $247M US Army H2F Contract",
        "Top 10 Tips for Tactical Coaches",
        "CSCS Certification Guide",
    ):
        assert rejection_reason(one(title, "https://x.test/jobs/thing")) is not None, title


def test_rejects_listing_index_pages():
    for url in (
        "https://jobboard.simplifaster.com/jobs/",
        "https://example.test/careers",
        "https://example.test/job-category/",
        "https://example.test/search-results",
    ):
        assert rejection_reason(one("Coach", url)) == "listing index, not one posting", url


def test_rejects_pages_with_no_posting_path():
    assert rejection_reason(one("Coach", "https://example.test/about-us")) == \
        "no individual-posting path"


def test_rejects_tos_excluded_sites():
    """These are never scraped by this project, so they never enter the count."""
    for url in (
        "https://www.indeed.com/viewjob?jk=abc123",
        "https://www.ziprecruiter.com/jobs/coach-abc",
        "https://www.glassdoor.com/job-listing/coach",
        "https://www.linkedin.com/jobs/view/12345",
    ):
        reason = rejection_reason(one("Coach", url))
        assert reason is not None, url


def test_rejects_result_missing_a_title():
    assert rejection_reason(one("", "https://x.test/jobs/a")) == "missing url or title"


# --------------------------------------------------------------------------
# Source behaviour
# --------------------------------------------------------------------------

def test_urls_are_deduplicated_across_files(tmp_path):
    same = block("Coach", "https://x.test/jobs/coach")
    (tmp_path / "a.txt").write_text(same)
    (tmp_path / "b.txt").write_text(same)
    assert len(list(SearchResultsSource("s", {"directory": str(tmp_path)}).fetch())) == 1


def test_fragment_only_difference_is_deduplicated(tmp_path):
    (tmp_path / "a.txt").write_text(
        block("Coach", "https://x.test/jobs/coach")
        + block("Coach", "https://x.test/jobs/coach#apply")
    )
    assert len(list(SearchResultsSource("s", {"directory": str(tmp_path)}).fetch())) == 1


def test_employer_is_not_inferred_from_the_title(tmp_path):
    """Search titles append site names; splitting one out would be a guess."""
    (tmp_path / "a.txt").write_text(
        block("H2Fit: Coach - Fort Bragg | Serco Jobs | Apply at CareerBuilder",
              "https://x.test/jobs/coach")
    )
    posting = list(SearchResultsSource("s", {"directory": str(tmp_path)}).fetch())[0]
    assert posting.employer == ""


def test_highlights_become_the_description(tmp_path):
    (tmp_path / "a.txt").write_text(
        block("Coach", "https://x.test/jobs/coach",
              highlights="CSCS required. Supports H2F Soldiers at brigade level.")
    )
    posting = list(SearchResultsSource("s", {"directory": str(tmp_path)}).fetch())[0]
    assert "CSCS" in posting.description and "brigade" in posting.description


def test_missing_directory_is_survivable():
    assert list(SearchResultsSource("s", {"directory": "/nonexistent/zz"}).fetch()) == []


def test_provenance_is_recorded(tmp_path):
    (tmp_path / "run1.txt").write_text(block("Coach", "https://x.test/jobs/coach"))
    posting = list(SearchResultsSource("s", {"directory": str(tmp_path)}).fetch())[0]
    assert posting.raw["result_file"] == "run1.txt"


def test_author_metadata_is_never_used_as_the_employer(tmp_path):
    """Regression: the author field is about the SITE, not the hiring company.

    Using it produced an employer breakdown of "N/A", "Site built by:
    Career.com", "The Escape" and "xpatjobs" -- site metadata presented as
    employers.
    """
    (tmp_path / "a.txt").write_text(
        "Title: Coach\nURL: https://x.test/jobs/coach\n"
        "Author: Site built by: Career.com\nHighlights: Serco H2F role\n"
    )
    posting = list(SearchResultsSource("s", {"directory": str(tmp_path)}).fetch())[0]
    assert posting.employer == ""
