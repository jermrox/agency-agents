"""Classifier tests.

The two-axis rule is the whole product, so these lean heavily on the
false-positive cases -- a board full of Performance Marketing Managers is the
failure mode that would actually embarrass us.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.classify import Thresholds, Verdict, classify  # noqa: E402
from tactical_jobs.models import JobPosting  # noqa: E402


def make(title: str, description: str = "", employer: str = "Acme", **kwargs) -> JobPosting:
    return JobPosting(
        source="test",
        source_id="1",
        url="https://example.invalid/job",
        title=title,
        employer=employer,
        description=description,
        **kwargs,
    )


# --------------------------------------------------------------------------
# True positives
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "title,description",
    [
        (
            "Tactical Strength and Conditioning Coach",
            "Support THOR3 program for special operations soldiers. CSCS required.",
        ),
        (
            "Human Performance Coach - H2F",
            "Holistic Health and Fitness brigade athletic trainer supporting soldiers.",
        ),
        (
            "Cognitive Performance Specialist",
            "Embedded with Naval Special Warfare to deliver mental performance training.",
        ),
        (
            "Performance Dietitian",
            "Registered dietitian supporting warfighter nutrition at a SOCOM unit.",
        ),
        (
            "Athletic Trainer - Fire Department",
            "Provide injury prevention and sports medicine services to firefighters.",
        ),
    ],
)
def test_matches_real_tactical_roles(title, description):
    posting = make(title, description)
    assert classify(posting) in {Verdict.PUBLISH, Verdict.REVIEW}
    assert posting.domain_hits and posting.discipline_hits


def test_strong_match_reaches_publish_threshold():
    posting = make(
        "Tactical Strength and Conditioning Coach (TSAC-F)",
        "THOR3 human performance program supporting special operations soldiers. "
        "Work alongside athletic trainers and performance dietitians. CSCS required.",
        employer="USASOC",
    )
    assert classify(posting) == Verdict.PUBLISH


# --------------------------------------------------------------------------
# False positives -- the reason the two-axis rule exists
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "title,description",
    [
        # Discipline, but no tactical domain.
        (
            "Strength and Conditioning Coach",
            "Work with our NCAA Division I football program. CSCS required.",
        ),
        (
            "Athletic Trainer",
            "Provide sports medicine coverage for a high school athletics department.",
        ),
        # Domain, but no human performance discipline.
        (
            "Software Engineer",
            "Build mission systems for the Department of Defense and special operations.",
        ),
        (
            "Logistics Coordinator",
            "Support Army brigade supply operations for soldiers in garrison.",
        ),
        # Neither.
        ("Account Executive", "Sell SaaS to mid-market companies."),
    ],
)
def test_rejects_single_axis_matches(title, description):
    assert classify(make(title, description)) == Verdict.REJECT


@pytest.mark.parametrize(
    "title,description",
    [
        ("Performance Marketing Manager", "Own paid acquisition and campaign performance."),
        ("Performance Engineer", "Optimize application performance for military customers."),
        ("Tactical Buyer", "Tactical procurement and sourcing for defense supply chains."),
        (
            "Director of Performance",
            "Own sales performance for our law enforcement tactical gear line.",
        ),
    ],
)
def test_exclusions_veto_outright(title, description):
    posting = make(title, description)
    assert classify(posting) == Verdict.REJECT
    assert posting.exclusion_hits
    assert posting.score == 0.0


def test_exclusion_beats_otherwise_strong_signal():
    """An exclusion must win even when both axes score well."""
    posting = make(
        "Performance Engineer",
        "Support THOR3 special operations human performance strength and conditioning "
        "platform for soldiers. Tactical athlete data.",
    )
    assert classify(posting) == Verdict.REJECT


# --------------------------------------------------------------------------
# Scoring mechanics
# --------------------------------------------------------------------------

def test_title_outweighs_description():
    in_title = make(
        "Tactical Strength and Conditioning Coach", "Supporting military service members."
    )
    in_body = make(
        "Coach", "Tactical strength and conditioning for military service members."
    )
    classify(in_title)
    classify(in_body)
    assert in_title.score > in_body.score


def test_description_repetition_is_capped():
    """A verbose posting must not outrank a precise one by repetition alone."""
    once = make("Coach", "military " + "soldier " + "strength and conditioning")
    spammy = make("Coach", ("military soldier strength and conditioning " * 40))
    classify(once)
    classify(spammy)
    # Capped at DESCRIPTION_CAP hits per term, so the ratio stays small.
    assert spammy.score <= once.score * 3


def test_thresholds_are_configurable():
    posting = make(
        "Human Performance Coach",
        "Supporting soldiers with strength and conditioning.",
    )
    strict = classify(posting, Thresholds(publish=999.0, review=998.0))
    assert strict == Verdict.REJECT


def test_axis_floors_block_borderline_domain():
    """A high discipline score cannot carry a posting with no domain signal."""
    posting = make(
        "Director of Human Performance",
        "Lead strength and conditioning, sports medicine, and performance nutrition "
        "for our professional basketball organization.",
    )
    assert classify(posting) == Verdict.REJECT


# --------------------------------------------------------------------------
# Tagging
# --------------------------------------------------------------------------

def test_tags_cover_discipline_and_domain():
    posting = make(
        "Tactical Strength and Conditioning Coach",
        "THOR3 special operations program supporting soldiers.",
    )
    classify(posting)
    assert "strength-conditioning" in posting.tags
    assert "sof" in posting.tags


def test_remote_flag_becomes_a_tag():
    posting = make(
        "Human Performance Coach",
        "Remote role supporting law enforcement strength and conditioning programs.",
        remote=True,
    )
    classify(posting)
    assert "remote" in posting.tags
    assert "first-responder" in posting.tags


def test_punctuation_does_not_break_matching():
    """'Coach/Specialist' and 'S&C' must still match."""
    posting = make(
        "Strength & Conditioning Coach/Specialist",
        "Supporting military special operations soldiers.",
    )
    assert classify(posting) in {Verdict.PUBLISH, Verdict.REVIEW}


# --- service context: the classifier reads the location ---------------------
#
# Every string below is from a real posting pulled on 2026-08-28.


def _posting(title, employer="", location="", description=""):
    return JobPosting(
        source="test", source_id="1", url="https://example.invalid/j",
        title=title, employer=employer, location=location, description=description,
    )


def test_the_installation_is_domain_evidence():
    # A Defense Health Agency physical therapist at Camp Lejeune. Before the
    # location was read, its strongest tactical signal sat in a field the
    # classifier never opened.
    posting = _posting(
        "Physical Therapist",
        "Military Treatment Facilities under DHA",
        "Camp Lejeune, North Carolina",
        "Provides outpatient physical therapy and return-to-duty rehabilitation.",
    )
    assert classify(posting) == Verdict.PUBLISH
    assert "service context" in posting.domain_hits


def test_a_credential_pathway_is_not_a_tactical_posting():
    # Federal health-care announcements list military training among the
    # qualifying routes into the profession. That sentence is about the
    # applicant's schooling, not about the work, and it was putting outpatient
    # VA clinic jobs on the board.
    posting = _posting(
        "Physical Therapy Assistant",
        "Veterans Health Administration",
        "Montgomery, Alabama",
        "Graduate of military physical therapy assistant programs that meet the "
        "educational requirement and have successfully passed the NPTE for PTAs.",
    )
    assert classify(posting) == Verdict.REJECT
    assert "service context" not in (posting.domain_hits or [])


def test_service_context_alone_does_not_carry_a_posting():
    # Branch context is evidence, not a free pass. A job on a base still has
    # to be a human performance job.
    posting = _posting("Contract Specialist", "", "Fort Bragg, North Carolina")
    assert classify(posting) == Verdict.REJECT


def test_a_civilian_clinic_in_a_fort_named_city_stays_off_the_board():
    posting = _posting(
        "Physical Therapist",
        "Veterans Health Administration",
        "Fort Lauderdale, Florida",
        "Outpatient physical therapy in a community clinic setting.",
    )
    assert classify(posting) == Verdict.REJECT


# --- applicant requirements are not discipline evidence -----------------------
#
# Every string below is from a live posting. The CBP sentence is the one that
# put five border-officer announcements on the board: "physical readiness"
# scored exactly the discipline floor, so one occurrence cleared the axis alone.

_CBP_BOILERPLATE = (
    "Physical Fitness Test: You will be required to successfully pass the "
    "Pre-employment Fitness Test. Please view both Hiring Process Deep Dive "
    "Video: The Fitness Test and Pre-Employment Fitness Test Physical Readiness "
    "Program, a 6-week program designed to assist you in achieving a level of "
    "physical fitness that will help you successfully pass the CBP fitness test. "
    "As a CBP Officer you will enforce customs, immigration and agriculture laws "
    "at ports of entry. Law enforcement experience preferred. Tactical."
)


def test_cbp_officer_is_rejected_on_the_discipline_axis():
    p = _posting("CBP Officer", employer="Customs and Border Protection",
                 location="Ketchikan, Alaska", description=_CBP_BOILERPLATE)
    assert classify(p, Thresholds()) == Verdict.REJECT
    # The domain axis is genuinely satisfied -- this is a tactical employer.
    # What fails is discipline: the only hit is the applicant fitness-test
    # sentence, and it no longer clears the floor by itself.
    assert p.discipline_hits == ["physical readiness"]


def test_physical_readiness_alone_is_below_the_discipline_floor():
    p = _posting("Program Analyst", employer="United States Army",
                 location="Fort Bragg, North Carolina",
                 description="Military installation. Physical readiness standards apply.")
    classify(p, Thresholds())
    assert p.discipline_hits == ["physical readiness"]
    assert classify(p, Thresholds()) == Verdict.REJECT


def test_installation_fitness_roles_earn_publish_on_their_own():
    # Demoting "physical readiness" alone dropped these three real Navy MWR
    # postings. They now qualify on the work they actually describe.
    for title in ("Fitness Specialist", "Sports Specialist (Fitness Instructor)",
                  "MWR Supervisory Recreation Specialist (Fitness Program Manager)"):
        p = _posting(title, employer="Commander, Navy Installations Command",
                     location="Naval Station Norfolk, Virginia",
                     description="Plan and lead fitness programs for active duty "
                                 "sailors at the installation fitness center.")
        assert classify(p, Thresholds()) == Verdict.PUBLISH, title
        assert "physical readiness" not in p.discipline_hits


class TestVetoYieldsToAnUnmistakableTitle:
    """The phrase veto exists for "performance" meaning software or sales. A
    strength coach whose duties include "performance testing" of athletes is
    not a software listing, and LMR's special-tactics postings were being
    dropped for exactly that phrase."""

    def _posting(self, title, description):
        from tactical_jobs.models import JobPosting

        return JobPosting(source="t", source_id="1", url="https://x/1", title=title,
                          employer="LMR Technical Group", location="Portland, Oregon", description=description)

    def test_human_performance_title_survives_a_performance_testing_mention(self):
        from tactical_jobs.classify import Verdict, classify

        body = ("Support the 125th Special Tactics Squadron human performance program for special operations "
                "warfighters. Experience with performance testing, load management, return to duty and strength "
                "and conditioning programming for military tactical athletes.")
        assert classify(self._posting("Certified Strength and Conditioning Specialist (CSCS)", body)) == Verdict.PUBLISH
        assert classify(self._posting("Physical Therapist", body)) == Verdict.PUBLISH

    def test_software_titles_are_still_vetoed(self):
        from tactical_jobs.classify import Verdict, classify

        body = ("Performance testing of web applications for a military customer; strength and conditioning "
                "of the load test suite; human performance dashboards for special operations.")
        assert classify(self._posting("Performance Test Engineer", body)) == Verdict.REJECT
        assert classify(self._posting("Senior Performance Engineer", body)) == Verdict.REJECT
