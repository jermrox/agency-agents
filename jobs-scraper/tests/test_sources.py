"""Source adapter mapping tests.

These run against captured payload shapes rather than the live APIs, so they
stay meaningful in CI and in a sandbox with no outbound network.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.sources.ats import (  # noqa: E402
    AshbySource,
    GreenhouseSource,
    LeverSource,
)
from tactical_jobs.sources.usajobs import USAJobsSource  # noqa: E402

USAJOBS_ITEM = {
    "MatchedObjectId": "830123400",
    "MatchedObjectDescriptor": {
        "PositionTitle": "Exercise Physiologist (Holistic Health and Fitness)",
        "PositionURI": "https://www.usajobs.gov/job/830123400",
        "PositionLocationDisplay": "Fort Campbell, Kentucky",
        "OrganizationName": "U.S. Army Forces Command",
        "DepartmentName": "Department of the Army",
        "PublicationStartDate": "2026-07-15",
        "QualificationSummary": "Must hold CSCS certification from NSCA.",
        "PositionRemuneration": [
            {"MinimumRange": "72553", "MaximumRange": "94317", "RateIntervalCode": "Per Year"}
        ],
        "JobCategory": [{"Name": "Sports Specialist", "Code": "0030"}],
        "PositionSchedule": [{"Name": "Full-time"}],
        "PositionOfferingType": [{"Name": "Permanent"}],
        "UserArea": {
            "Details": {
                "JobSummary": "Serve on an H2F Performance Readiness Team supporting Soldiers.",
                "MajorDuties": [
                    "Design strength and conditioning programs.",
                    "Conduct movement screens.",
                ],
                "Education": "Master's degree in Exercise Science required.",
                "Requirements": "Must obtain and maintain a Secret security clearance.",
                "Evaluations": "Candidates rated on TSAC-F experience.",
                "SecurityClearanceRequired": "Secret",
                "TeleworkEligible": "No",
                "WhoMayApply": "United States Citizens",
                "PromotionPotential": "12",
            }
        },
    },
}


def _usajobs_posting():
    return USAJobsSource("federal", {"api_key": "x", "user_agent": "x"})._to_posting(
        USAJOBS_ITEM
    )


def test_usajobs_maps_core_fields():
    posting = _usajobs_posting()
    assert posting.title.startswith("Exercise Physiologist")
    assert posting.employer == "U.S. Army Forces Command"
    assert posting.department == "Department of the Army"
    assert posting.location == "Fort Campbell, Kentucky"
    assert posting.url.endswith("830123400")
    assert posting.posted_at is not None


def test_usajobs_formats_compensation():
    assert _usajobs_posting().compensation == "$72553 - $94317 Per Year"


def test_usajobs_prefers_hiring_org_over_parent_department():
    """The hiring org is the useful employer label for a job board."""
    posting = _usajobs_posting()
    assert posting.employer != posting.department


def test_usajobs_captures_every_narrative_block():
    """Education/Requirements/Evaluations carry the cert and clearance language.

    Dropping them would blind the enrichment layer to most of what it exists
    to extract, so this asserts each block reaches the description.
    """
    description = _usajobs_posting().description
    for needle in (
        "CSCS",  # QualificationSummary
        "H2F Performance Readiness Team",  # JobSummary
        "movement screens",  # MajorDuties
        "Master's degree",  # Education
        "Secret security clearance",  # Requirements
        "TSAC-F",  # Evaluations
    ):
        assert needle in description, f"missing {needle!r}"


def test_usajobs_folds_structured_facts_into_the_text():
    description = _usajobs_posting().description
    assert "Security clearance: Secret." in description
    assert "Job category: Sports Specialist." in description
    assert "Position schedule: Full-time." in description


def test_usajobs_survives_a_sparse_record():
    """Most fields absent must yield a posting, not an exception."""
    posting = USAJobsSource("federal", {"api_key": "x", "user_agent": "x"})._to_posting(
        {"MatchedObjectId": "1", "MatchedObjectDescriptor": {"PositionTitle": "Coach"}}
    )
    assert posting is not None
    assert posting.title == "Coach"
    assert posting.compensation is None


def test_usajobs_returns_none_without_a_descriptor():
    source = USAJobsSource("federal", {"api_key": "x", "user_agent": "x"})
    assert source._to_posting({"MatchedObjectId": "1"}) is None


def test_greenhouse_maps_a_board_payload(monkeypatch):
    payload = {
        "jobs": [
            {
                "id": 4567,
                "title": "Tactical Strength and Conditioning Coach",
                "absolute_url": "https://boards.greenhouse.io/acme/jobs/4567",
                "location": {"name": "Fort Bragg, NC"},
                "content": "&lt;p&gt;Support THOR3 Soldiers.&lt;/p&gt;&lt;ul&gt;&lt;li&gt;CSCS required&lt;/li&gt;&lt;/ul&gt;",
                "updated_at": "2026-07-01T12:00:00Z",
                "departments": [{"name": "Human Performance"}],
            }
        ]
    }
    monkeypatch.setattr(
        "tactical_jobs.sources.ats.fetch_json", lambda *a, **k: payload
    )
    postings = list(
        GreenhouseSource("acme", {"board_token": "acme", "employer": "Acme"}).fetch()
    )
    assert len(postings) == 1
    posting = postings[0]
    assert posting.source_id == "4567"
    assert posting.employer == "Acme"
    assert posting.department == "Human Performance"
    # HTML entities unescaped and block tags turned into separators.
    assert "THOR3" in posting.description and "CSCS" in posting.description
    assert "Soldiers.CSCS" not in posting.description


def test_lever_merges_list_sections_into_the_description(monkeypatch):
    payload = [
        {
            "id": "abc-123",
            "text": "Human Performance Coach",
            "hostedUrl": "https://jobs.lever.co/acme/abc-123",
            "categories": {"location": "Coronado, CA", "team": "Performance"},
            "descriptionPlain": "Support Naval Special Warfare operators.",
            "lists": [{"content": "&lt;li&gt;TSAC-F preferred&lt;/li&gt;"}],
            "createdAt": 1772000000000,
        }
    ]
    monkeypatch.setattr(
        "tactical_jobs.sources.ats.fetch_json", lambda *a, **k: payload
    )
    posting = list(
        LeverSource("acme", {"board_token": "acme", "employer": "Acme"}).fetch()
    )[0]
    assert "Naval Special Warfare" in posting.description
    assert "TSAC-F" in posting.description  # the lists block must not be dropped
    assert posting.department == "Performance"
    assert posting.posted_at is not None and posting.posted_at.year > 2020


def test_ashby_reads_remote_flag_and_compensation(monkeypatch):
    payload = {
        "jobs": [
            {
                "id": "xyz",
                "title": "Performance Dietitian",
                "jobUrl": "https://jobs.ashbyhq.com/acme/xyz",
                "location": "Remote - US",
                "descriptionPlain": "RD required.",
                "publishedAt": "2026-06-01T00:00:00Z",
                "isRemote": True,
                "department": "Nutrition",
                "compensationTierSummary": "$80K - $95K",
            }
        ]
    }
    monkeypatch.setattr(
        "tactical_jobs.sources.ats.fetch_json", lambda *a, **k: payload
    )
    posting = list(
        AshbySource("acme", {"board_token": "acme", "employer": "Acme"}).fetch()
    )[0]
    assert posting.remote is True
    assert posting.compensation == "$80K - $95K"
    assert posting.department == "Nutrition"
