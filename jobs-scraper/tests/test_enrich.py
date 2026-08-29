"""Enrichment tests.

Extraction is judged on two things: does it find the fact when it is there,
and -- much more importantly -- does it stay silent when it is not. A missing
salary shrinks the sample; a wrong one corrupts every average built on top of
it. So the negative cases here outnumber the positive ones on purpose, and
they are drawn from the phrasing that actually appears in tactical human
performance postings: headcounts, equipment budgets, 401(k) matches, contract
periods of performance, and "SMART goals".
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.enrich import Enrichment, enrich, enrich_text  # noqa: E402
from tactical_jobs.models import JobPosting  # noqa: E402


def make(title: str, description: str = "", **kwargs) -> JobPosting:
    return JobPosting(
        source="test",
        source_id="1",
        url="https://example.invalid/job",
        title=title,
        employer="Acme",
        description=description,
        **kwargs,
    )


# --------------------------------------------------------------------------
# Salary -- the formats the market actually uses
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("$75,000 - $95,000 per year", (75000.0, 95000.0, "year")),
        ("$75K-$95K", (75000.0, 95000.0, "year")),
        ("$75k - $95k annually", (75000.0, 95000.0, "year")),
        ("75000.00 - 95000.00 Annually", (75000.0, 95000.0, "year")),
        ("$45.00/hour", (45.0, 45.0, "hour")),
        ("$45 - $60 per hour", (45.0, 60.0, "hour")),
        ("Salary: 80,000", (80000.0, 80000.0, "year")),
        ("$85,000.00 to $110,000.00 per year", (85000.0, 110000.0, "year")),
        ("Pay range: $32.50 - $48.75 hourly", (32.5, 48.75, "hour")),
        ("$120,000 – $140,000 /yr", (120000.0, 140000.0, "year")),
        # USAJOBS and the major ATS vendors each render this differently.
        ("$75,000.00 - $95,000.00 / Per Year", (75000.0, 95000.0, "year")),
        ("USD 90,000 - USD 115,000 annually", (90000.0, 115000.0, "year")),
        ("$28.85 - $43.27 / hourly", (28.85, 43.27, "hour")),
    ],
)
def test_compensation_field_formats(text, expected):
    result = enrich_text("Coach", "", compensation=text)
    assert (result.salary_min, result.salary_max, result.salary_period) == expected


def test_k_suffix_applies_to_both_ends_of_a_range():
    """"$75-$95K" abbreviates both sides but only marks one."""
    result = enrich_text("Coach", "", compensation="$75-$95K")
    assert (result.salary_min, result.salary_max) == (75000.0, 95000.0)


def test_reversed_range_is_normalized():
    result = enrich_text("Coach", "", compensation="$95,000 - $75,000")
    assert (result.salary_min, result.salary_max) == (75000.0, 95000.0)


def test_salary_is_read_from_description_when_compensation_is_absent():
    result = enrich_text(
        "Strength Coach",
        "The salary range for this position is $88,000 to $104,000 per year.",
    )
    assert (result.salary_min, result.salary_max, result.salary_period) == (
        88000.0,
        104000.0,
        "year",
    )


def test_compensation_field_beats_description_text():
    """The structured field is source data; the description is prose about it."""
    result = enrich_text(
        "Strength Coach",
        "Comparable roles in the region pay around $60,000 per year.",
        compensation="$88,000 - $104,000 per year",
    )
    assert (result.salary_min, result.salary_max) == (88000.0, 104000.0)


def test_unlabeled_compensation_field_still_parses():
    """No cue word is demanded of a field that exists only to hold pay."""
    result = enrich_text("Coach", "", compensation="$75,000 - $95,000")
    assert (result.salary_min, result.salary_max, result.salary_period) == (
        75000.0,
        95000.0,
        "year",
    )


def test_range_is_preferred_over_a_lone_figure():
    result = enrich_text(
        "Coach",
        "A $5,000 relocation bonus is offered. The salary range is $90,000 - $115,000 per year.",
    )
    assert (result.salary_min, result.salary_max) == (90000.0, 115000.0)


def test_starting_at_sets_only_the_floor():
    result = enrich_text("Coach", "Compensation starting at $75,000 annually.")
    assert (result.salary_min, result.salary_max, result.salary_period) == (
        75000.0,
        None,
        "year",
    )


def test_up_to_sets_only_the_ceiling():
    result = enrich_text("Coach", "Salary up to $95,000 per year depending on experience.")
    assert (result.salary_min, result.salary_max) == (None, 95000.0)


def test_nearest_period_word_wins_over_a_later_one():
    """"$45.00/hour ($93,600 annually)" states two periods for two figures."""
    result = enrich_text("Coach", "", compensation="$45.00/hour ($93,600 annually)")
    assert result.salary_period == "hour"
    assert result.salary_min == 45.0


def test_period_is_inferred_from_magnitude_when_unlabeled():
    yearly = enrich_text("Coach", "", compensation="$92,000")
    hourly = enrich_text("Coach", "", compensation="$46.50")
    assert yearly.salary_period == "year"
    assert hourly.salary_period == "hour"


# --------------------------------------------------------------------------
# Salary -- sanity bounds
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        # A four-digit "salary" that is really a calendar year.
        "Salary determined by the 2026 pay tables.",
        "Applications for the 2025 hiring cycle are open; salary is competitive.",
        # Impossible hourly rate.
        "Hourly rate of $1,200 per hour",
        # Impossible annual salary.
        "Annual salary of $4,500 per year",
        # Ambiguous magnitude between a wage and a salary.
        "Weekly pay of $800",
    ],
)
def test_sanity_bounds_reject_impossible_pay(text):
    result = enrich_text("Coach", text)
    assert result.salary_min is None
    assert result.salary_max is None
    assert result.salary_period is None


def test_bounds_reject_a_range_when_either_end_is_impossible():
    result = enrich_text("Coach", "", compensation="$45 - $2,000,000 per hour")
    assert result.salary_min is None


def test_hourly_ceiling_and_floor_are_inclusive_of_real_rates():
    low = enrich_text("Coach", "", compensation="$18.00 per hour")
    high = enrich_text("Coach", "", compensation="$180.00 per hour")
    assert low.salary_min == 18.0
    assert high.salary_min == 180.0


# --------------------------------------------------------------------------
# Salary -- no false extraction from prose that merely contains a number
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        "Provide human performance support to 300 Soldiers in a light infantry battalion.",
        "Manage a $500,000 equipment budget for the performance center.",
        # Vetoed by the noun *after* the figure, with nothing suspicious before it.
        "The performance center was built with a $250,000 renovation grant.",
        "Programming is funded by a $180,000 award from the state wellness office.",
        "The facility includes 12 racks, 4 platforms, and 2 force plates.",
        "Benefits include a 401(k) match, medical, and dental. Salary is competitive.",
        "Benefits include 401k matching; compensation commensurate with experience.",
        "Full-time position, 40 hours per week. Pay is highly competitive.",
        "Employer contributes 6 percent toward retirement; pay is negotiable.",
        "Deliver 25 sessions per week to tactical athletes. Compensation is competitive.",
        "Program supports 1,200 personnel across three brigades.",
        "Travel up to 20 percent. Salary commensurate with experience.",
    ],
)
def test_prose_numbers_are_not_salaries(text):
    result = enrich_text("Human Performance Coach", text)
    assert result.salary_min is None
    assert result.salary_max is None


def test_no_salary_at_all_degrades_to_none():
    result = enrich_text("Strength and Conditioning Coach", "Support tactical athletes.")
    assert (result.salary_min, result.salary_max, result.salary_period) == (None, None, None)


def test_non_numeric_compensation_falls_through_to_the_description():
    result = enrich_text(
        "Coach",
        "The advertised salary range is $70,000 - $80,000 per year.",
        compensation="Competitive, DOE",
    )
    assert (result.salary_min, result.salary_max) == (70000.0, 80000.0)


# --------------------------------------------------------------------------
# Certifications
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("CSCS required.", "CSCS"),
        ("Certified Strength and Conditioning Specialist required.", "CSCS"),
        ("Certified Strength & Conditioning Specialist required.", "CSCS"),
        ("TSAC-F preferred.", "TSAC-F"),
        ("TSAC Facilitator preferred.", "TSAC-F"),
        ("Tactical Strength and Conditioning Facilitator preferred.", "TSAC-F"),
        ("Must hold ATC credential.", "ATC"),
        ("BOC certified applicants only.", "ATC"),
        ("BOC-certified athletic trainer.", "ATC"),
        ("Athletic Trainer Certified with state licensure.", "ATC"),
        ("Certified Athletic Trainer with state licensure.", "ATC"),
        ("Licensed Athletic Trainer in the state of North Carolina.", "LAT"),
        ("LAT/ATC required.", "LAT"),
        ("Registered Dietitian required.", "RD"),
        ("Registered Dietitian Nutritionist required.", "RD"),
        ("RDN required.", "RD"),
        ("RD required.", "RD"),
        ("CISSN strongly preferred.", "CISSN"),
        ("Certified Sports Nutritionist preferred.", "CISSN"),
        ("DPT from an accredited program.", "DPT"),
        ("Doctor of Physical Therapy from an accredited program.", "DPT"),
        ("NSCA-CPT accepted in lieu of CSCS.", "NSCA-CPT"),
        ("NSCA Certified Personal Trainer accepted.", "NSCA-CPT"),
        ("CSPS is a plus.", "CSPS"),
        ("PhD in exercise physiology preferred.", "PhD"),
        ("Ph.D. in exercise physiology preferred.", "PhD"),
    ],
)
def test_certification_aliases_normalize(text, expected):
    assert expected in enrich_text("Coach", text).certifications


def test_certifications_are_deduped_and_sorted():
    result = enrich_text(
        "Athletic Trainer",
        "BOC certified ATC required. Certified Athletic Trainer preferred. CSCS a plus. CSCS.",
    )
    assert result.certifications == ["ATC", "CSCS"]


def test_certification_in_the_title_counts():
    result = enrich_text("Strength and Conditioning Coach (CSCS, TSAC-F)", "Support Soldiers.")
    assert set(result.certifications) == {"CSCS", "TSAC-F"}


@pytest.mark.parametrize(
    "text",
    [
        # Word-boundary: the acronym must not match inside another word.
        "Programming includes lat pulldowns and lat raises for the lats.",
        "Facility is located at 123 Ranger Rd. near the 3rd Battalion area.",
        "Report to the CPT serving as company commander.",
        "Coordinate with air traffic control ATC personnel on the flightfield.",
        "Athletes rotate through the CSCSX simulator bay.",
    ],
)
def test_no_certification_from_lookalike_text(text):
    assert enrich_text("Human Performance Coach", text).certifications == []


def test_bare_tsac_is_not_the_credential():
    """TSAC is the NSCA's program name; TSAC-F is the credential."""
    result = enrich_text("Coach", "Familiarity with the NSCA TSAC community is a plus.")
    assert result.certifications == []


def test_no_certifications_returns_empty_list_not_none():
    assert enrich_text("Coach", "Support the unit.").certifications == []


# --------------------------------------------------------------------------
# Clearance
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("Active TS/SCI clearance required.", "TS/SCI"),
        ("Top Secret/SCI clearance required.", "TS/SCI"),
        ("Must hold sensitive compartmented information access.", "TS/SCI"),
        ("An active Top Secret clearance is required.", "Top Secret"),
        ("Secret clearance required.", "Secret"),
        ("Must be able to obtain a Secret.", "Secret"),
        ("Candidate must be able to obtain and maintain a Secret clearance.", "Secret"),
        ("Position requires a Public Trust background investigation.", "Public Trust"),
        ("Public Trust clearance required.", "Public Trust"),
    ],
)
def test_clearance_levels(text, expected):
    assert enrich_text("Coach", text).clearance == expected


def test_highest_clearance_mentioned_wins():
    result = enrich_text(
        "Human Performance Coach",
        "A Secret clearance is required at hire; TS/SCI eligibility is preferred. "
        "Public Trust positions may also be considered.",
    )
    assert result.clearance == "TS/SCI"


def test_top_secret_outranks_secret():
    result = enrich_text("Coach", "Secret clearance required, Top Secret preferred.")
    assert result.clearance == "Top Secret"


def test_secret_outranks_public_trust():
    result = enrich_text(
        "Coach", "Public Trust position; a Secret clearance may be required later."
    )
    assert result.clearance == "Secret"


@pytest.mark.parametrize(
    "text",
    [
        "Our secret sauce is the coaching staff.",
        # Clearance vocabulary is present, but the phrase is about IP.
        "Staff must hold trade secret and proprietary information in confidence.",
        "We maintain the public trust of the communities we serve.",
        "Officers work hard to earn the public trust every single day.",
        "Support the unit's physical readiness program.",
    ],
)
def test_no_clearance_from_ordinary_prose(text):
    assert enrich_text("Coach", text).clearance is None


# --------------------------------------------------------------------------
# Education
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("High school diploma or equivalent required.", "High School"),
        ("GED required.", "High School"),
        ("Associate's degree in a health science field.", "Associate"),
        ("Associate degree required.", "Associate"),
        ("Bachelor's degree in exercise science required.", "Bachelor"),
        ("Bachelor degree required.", "Bachelor"),
        ("Baccalaureate degree in kinesiology.", "Bachelor"),
        ("BS in exercise science required.", "Bachelor"),
        ("Master's degree in exercise physiology required.", "Master"),
        ("Masters degree required.", "Master"),
        ("Master of Science in Kinesiology required.", "Master"),
        ("Graduate degree in a related field.", "Master"),
        ("Doctorate in exercise physiology required.", "Doctorate"),
        ("Doctor of Physical Therapy required.", "Doctorate"),
        ("PhD in biomechanics required.", "Doctorate"),
    ],
)
def test_education_levels(text, expected):
    assert enrich_text("Coach", text).education == expected


def test_education_reports_the_floor_not_the_aspiration():
    """"Bachelor's required, Master's preferred" gates on the Bachelor's."""
    result = enrich_text(
        "Strength Coach",
        "Bachelor's degree in exercise science required. Master's degree preferred.",
    )
    assert result.education == "Bachelor"


@pytest.mark.parametrize(
    "text",
    [
        "Five years of experience coaching high school athletes.",
        "Serve as the Associate Director of Human Performance.",
        "Certification as a Master Resilience Trainer is a plus.",
        "Coordinate with the unit's master fitness trainers.",
    ],
)
def test_no_education_from_lookalike_text(text):
    assert enrich_text("Human Performance Coach", text).education is None


# --------------------------------------------------------------------------
# Years of experience
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("5+ years of experience with tactical populations.", 5),
        ("Minimum of three (3) years of experience required.", 3),
        ("At least 2 years experience in a collegiate or tactical setting.", 2),
        ("Requires 7 years of progressively responsible experience.", 7),
        ("3-5 years of experience required.", 3),
        ("Two (2) to four (4) years of relevant experience.", 2),
        ("Experience: 10 years supporting military populations.", 10),
        ("One year of experience is required.", 1),
        ("5 yrs experience preferred.", 5),
    ],
)
def test_years_of_experience_formats(text, expected):
    assert enrich_text("Coach", text).years_experience_min == expected


def test_years_takes_the_minimum_stated_anywhere():
    result = enrich_text(
        "Human Performance Coach",
        "Ten years of experience leading a program is preferred. "
        "A minimum of three (3) years of experience with tactical athletes is required.",
    )
    assert result.years_experience_min == 3


@pytest.mark.parametrize(
    "text",
    [
        "This contract has a 5 year period of performance with four option years.",
        "Selected candidates must relocate within 2 years of hire.",
        "The program launched 3 years ago at a sister installation.",
        "Provide coverage 5 days per week.",
    ],
)
def test_years_requires_experience_context(text):
    assert enrich_text("Coach", text).years_experience_min is None


def test_absurd_year_counts_are_ignored():
    result = enrich_text("Coach", "Program has 75 years of experience across the staff.")
    assert result.years_experience_min is None


# --------------------------------------------------------------------------
# Employment type
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "title,description,expected",
    [
        ("Athletic Trainer", "This is a full-time position with benefits.", "Full-time"),
        ("Athletic Trainer", "Full time, 40 hours per week.", "Full-time"),
        ("Athletic Trainer (Part-Time)", "Twenty hours per week.", "Part-time"),
        ("Athletic Trainer", "Part time role, evenings only.", "Part-time"),
        ("Athletic Trainer - Per Diem", "Coverage as needed.", "Per-diem"),
        ("Athletic Trainer", "PRN coverage for the fire department.", "Per-diem"),
        ("Strength Coach", "This is a 1099 contract position.", "Contract"),
        ("Strength Coach", "Independent contractor engagement.", "Contract"),
        ("Strength Coach", "Contract-to-hire opportunity.", "Contract"),
    ],
)
def test_employment_types(title, description, expected):
    assert enrich_text(title, description).employment_type == expected


def test_title_beats_description_for_employment_type():
    result = enrich_text(
        "Athletic Trainer (Part-Time)",
        "You will work alongside our full-time staff of six.",
    )
    assert result.employment_type == "Part-time"


def test_government_contract_language_is_not_an_employment_type():
    """Nearly every billet in this market is funded by a contract."""
    result = enrich_text(
        "Strength and Conditioning Coach",
        "Work is performed under a government contract vehicle. The contract is "
        "expected to be awarded in the fall.",
    )
    assert result.employment_type is None


def test_full_time_beats_later_contract_language():
    result = enrich_text(
        "Strength Coach",
        "This is a full-time contract position supporting the H2F program.",
    )
    assert result.employment_type == "Full-time"


def test_travel_per_diem_is_not_a_schedule():
    result = enrich_text(
        "Strength Coach",
        "Per diem and lodging are reimbursed for travel to satellite sites.",
    )
    assert result.employment_type is None


def test_no_employment_type_returns_none():
    assert enrich_text("Coach", "Support the unit.").employment_type is None


# --------------------------------------------------------------------------
# Installations
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("Position located at Fort Bragg, NC.", "Fort Bragg"),
        ("Position located at Fort Liberty, NC.", "Fort Bragg"),
        ("Position located at Ft. Bragg, NC.", "Fort Bragg"),
        ("Supporting units at Fort Campbell, KY.", "Fort Campbell"),
        ("Supporting units at Fort Carson, CO.", "Fort Carson"),
        ("Reports to the JBLM performance center.", "JBLM"),
        ("Joint Base Lewis-McChord, WA.", "JBLM"),
        ("Embedded at Camp Lejeune, NC.", "Camp Lejeune"),
        ("Embedded at Camp Pendleton, CA.", "Camp Pendleton"),
        ("Located in Coronado, CA.", "Coronado"),
        ("Located at Hurlburt Field, FL.", "Hurlburt Field"),
        ("Located at Fort Moore, GA.", "Fort Benning"),
        ("Located at Fort Cavazos, TX.", "Fort Hood"),
        ("Located at Peterson SFB, CO.", "Peterson SFB"),
    ],
)
def test_installation_recognition_and_canonicalization(text, expected):
    assert enrich_text("Coach", text).installation == expected


def test_renamed_posts_collapse_to_one_installation():
    """Bragg and Liberty are one place; two labels would split the market data."""
    old = enrich_text("Coach", "", location="Fort Bragg, NC")
    new = enrich_text("Coach", "", location="Fort Liberty, NC")
    assert old.installation == new.installation == "Fort Bragg"


def test_location_field_is_used_for_installation():
    result = enrich_text("Strength Coach", "Support the brigade.", location="Fort Campbell, KY")
    assert result.installation == "Fort Campbell"


def test_location_beats_a_passing_mention_in_the_description():
    result = enrich_text(
        "Strength Coach",
        "Coordinates with counterparts at Fort Carson and Fort Drum.",
        location="Fort Campbell, KY",
    )
    assert result.installation == "Fort Campbell"


def test_unknown_installation_is_none():
    result = enrich_text("Strength Coach", "Remote role.", location="Austin, TX")
    assert result.installation is None


# --------------------------------------------------------------------------
# Service branch
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("Supporting Soldiers in an Army infantry brigade combat team.", "Army"),
        ("Supporting Naval Special Warfare operators and their families.", "Navy"),
        ("Supporting AFSOC Air Commandos and Air Force special tactics teams.", "Air Force"),
        ("Supporting Marines at a Marine Corps installation.", "Marine Corps"),
        ("Supporting Coast Guard members and their units.", "Coast Guard"),
        ("Supporting Space Force Guardians at a USSF unit.", "Space Force"),
        ("Supporting USSOCOM components under a joint task force.", "Joint"),
    ],
)
def test_service_branch_detection(text, expected):
    assert enrich_text("Human Performance Coach", text).service_branch == expected


def test_equal_evidence_across_services_reads_as_joint():
    result = enrich_text(
        "Human Performance Coach",
        "Supports the Army and Marine Corps components of the task force.",
    )
    assert result.service_branch == "Joint"


def test_installation_alone_implies_a_branch():
    result = enrich_text("Athletic Trainer", "Provide coverage.", location="Camp Lejeune, NC")
    assert result.service_branch == "Marine Corps"


def test_explicit_branch_language_outweighs_the_installation_hint():
    result = enrich_text(
        "Athletic Trainer",
        "Supporting Soldiers of the Army H2F program.",
        location="JBLM, WA",
    )
    assert result.service_branch == "Army"


def test_no_branch_signal_is_none():
    result = enrich_text(
        "Strength Coach", "Support firefighters at a municipal fire department."
    )
    assert result.service_branch is None


# --------------------------------------------------------------------------
# Programs
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text,expected",
    [
        ("Supports the H2F program at the brigade level.", "H2F"),
        ("Supports the Holistic Health and Fitness program.", "H2F"),
        ("THOR3 strength and conditioning support.", "THOR3"),
        ("Thor 3 human performance element.", "THOR3"),
        ("Tactical Human Optimization, Rapid Rehabilitation and Reconditioning.", "THOR3"),
        ("POTFF human performance element.", "POTFF"),
        ("Preservation of the Force and Family program.", "POTFF"),
        ("Assigned to the Camp Lejeune SMART Center.", "SMART"),
        ("Sports Medicine and Reconditioning Team clinic.", "SMART"),
    ],
)
def test_program_detection(text, expected):
    assert enrich_text("Human Performance Coach", text).program == expected


def test_smart_goals_is_not_the_smart_program():
    """The most common false positive in the entire coaching vocabulary."""
    result = enrich_text(
        "Strength Coach",
        "Work with athletes to set SMART goals and track smart progressions.",
    )
    assert result.program is None


def test_most_specific_program_wins():
    result = enrich_text(
        "Human Performance Coach",
        "This THOR3 billet falls under the broader POTFF program of record.",
    )
    assert result.program == "THOR3"


def test_program_in_the_title_beats_the_description():
    result = enrich_text(
        "H2F Strength and Conditioning Coach",
        "The program is modeled on the THOR3 construct used across USASOC.",
    )
    assert result.program == "H2F"


def test_no_program_is_none():
    assert enrich_text("Strength Coach", "Support firefighters.").program is None


# --------------------------------------------------------------------------
# Shape, defaults, and graceful degradation
# --------------------------------------------------------------------------

def test_empty_enrichment_has_stable_keys():
    keys = set(Enrichment().to_dict())
    assert keys == {
        "certifications",
        "clearance",
        "salary_min",
        "salary_max",
        "salary_period",
        "education",
        "years_experience_min",
        "employment_type",
        "installation",
        "service_branch",
        "program",
    }


def test_to_dict_keys_are_present_even_when_everything_is_unknown():
    payload = enrich_text("", "").to_dict()
    assert payload["certifications"] == []
    assert all(payload[key] is None for key in payload if key != "certifications")


def test_to_dict_certifications_is_a_copy():
    """Callers mutating the dict must not corrupt the dataclass."""
    result = enrich_text("Coach", "CSCS required.")
    payload = result.to_dict()
    payload["certifications"].append("BOGUS")
    assert result.certifications == ["CSCS"]


@pytest.mark.parametrize(
    "title,description,location,compensation",
    [
        ("", "", "", ""),
        ("Coach", "", "", ""),
        ("", "$$$ ---- ,,,", "", "$"),
        ("Coach", "\n\n\t  \n", "  ", "   "),
        ("Coach", "Salary: $", "", "-"),
        ("Coach", "x" * 20000, "", ""),
    ],
)
def test_degenerate_input_never_raises(title, description, location, compensation):
    result = enrich_text(title, description, location, compensation)
    assert isinstance(result, Enrichment)
    assert isinstance(result.to_dict(), dict)


def test_enrich_stamps_the_posting():
    posting = make(
        "Tactical Strength and Conditioning Coach",
        "CSCS required. Secret clearance required. Salary: $90,000 per year.",
        location="Fort Bragg, NC",
    )
    result = enrich(posting)
    assert posting.enrichment == result.to_dict()
    assert posting.enrichment["installation"] == "Fort Bragg"


def test_enrich_reads_the_postings_compensation_field():
    posting = make("Strength Coach", "Support Soldiers.", compensation="$45.00 - $60.00 hourly")
    result = enrich(posting)
    assert (result.salary_min, result.salary_max, result.salary_period) == (45.0, 60.0, "hour")


def test_enrich_survives_a_posting_with_no_description():
    posting = make("Strength Coach")
    result = enrich(posting)
    assert result.to_dict()["certifications"] == []


def test_enrichment_flows_into_the_public_dict():
    posting = make("Strength Coach", "CSCS required.")
    enrich(posting)
    assert posting.to_public_dict()["enrichment"]["certifications"] == ["CSCS"]


# --------------------------------------------------------------------------
# Realistic full-length postings
# --------------------------------------------------------------------------

SOF_POSTING = """
Position: Tactical Strength and Conditioning Coach (THOR3)
Location: Fort Liberty, North Carolina

Summary
The Tactical Human Optimization, Rapid Rehabilitation and Reconditioning (THOR3)
program provides embedded human performance support to United States Army Special
Operations Command (USASOC) operators. The Strength and Conditioning Coach designs
and delivers periodized training for Green Berets assigned to a Special Forces Group,
and works alongside athletic trainers, physical therapists, and performance
dietitians as part of a multidisciplinary team.

Responsibilities
- Design annual training plans for approximately 400 assigned operators.
- Conduct force plate and VO2 assessments and interpret results for commanders.
- Coordinate return-to-duty progressions with the sports medicine staff.
- Manage a $250,000 equipment budget for the unit performance facility.

Qualifications
- Master's degree in exercise science, kinesiology, or a closely related field.
- NSCA Certified Strength and Conditioning Specialist (CSCS) required at hire.
- TSAC-F preferred.
- Minimum of three (3) years of experience training tactical or collegiate athletes.
- Must be able to obtain and maintain a Secret clearance.

Compensation and Benefits
This is a full-time position under a government contract. The salary range is
$85,000 - $110,000 per year, depending on experience. Benefits include medical,
dental, 401(k) with company match, and 15 days of paid leave.
"""

CONVENTIONAL_POSTING = """
Athletic Trainer - Holistic Health and Fitness (H2F)
Fort Campbell, KY

The H2F Athletic Trainer provides musculoskeletal injury prevention and
rehabilitation services to Soldiers assigned to a brigade combat team. The
Athletic Trainer works within the H2F Performance Readiness Center under the
direction of the Program Director.

Minimum Qualifications
- Bachelor's degree from a CAATE accredited athletic training program. Master's
  degree preferred.
- BOC certified (ATC) and eligible for licensure in Kentucky.
- At least 2 years experience providing athletic training services.
- Must be able to obtain a Public Trust position determination.

Schedule and Pay
Part-time, 20 hours per week. $45.00/hour. Per diem and lodging are provided for
occasional travel to satellite training sites.
"""

FIRST_RESPONDER_POSTING = """
Performance Dietitian - Metro Fire Department

We are hiring a Registered Dietitian (RD/RDN) to build a nutrition program for
850 firefighters and paramedics across 22 stations. Our department has worked hard
to earn the public trust of the community, and this role is part of that
commitment.

Requirements
- Registered Dietitian credential in good standing; CISSN preferred.
- Bachelor's degree required in nutrition or dietetics.
- 5+ years of experience in sports or tactical nutrition.
- Valid driver's license.

This is a 1099 contract position. Compensation: $60 - $85 per hour. The department
manages a $1,500,000 wellness grant that funds this role through 2029.
"""


def test_sof_posting_end_to_end():
    result = enrich_text(
        "Tactical Strength and Conditioning Coach (THOR3)",
        SOF_POSTING,
        location="Fort Liberty, NC",
    )
    assert set(result.certifications) == {"CSCS", "TSAC-F"}
    assert result.clearance == "Secret"
    assert (result.salary_min, result.salary_max, result.salary_period) == (
        85000.0,
        110000.0,
        "year",
    )
    assert result.education == "Master"
    assert result.years_experience_min == 3
    assert result.employment_type == "Full-time"
    assert result.installation == "Fort Bragg"
    assert result.service_branch == "Army"
    assert result.program == "THOR3"


def test_conventional_posting_end_to_end():
    result = enrich_text(
        "Athletic Trainer - Holistic Health and Fitness (H2F)",
        CONVENTIONAL_POSTING,
        location="Fort Campbell, KY",
    )
    assert "ATC" in result.certifications
    assert result.clearance == "Public Trust"
    assert (result.salary_min, result.salary_max, result.salary_period) == (45.0, 45.0, "hour")
    assert result.education == "Bachelor"
    assert result.years_experience_min == 2
    assert result.employment_type == "Part-time"
    assert result.installation == "Fort Campbell"
    assert result.service_branch == "Army"
    assert result.program == "H2F"


def test_first_responder_posting_end_to_end():
    result = enrich_text(
        "Performance Dietitian - Metro Fire Department",
        FIRST_RESPONDER_POSTING,
        location="Denver, CO",
    )
    assert set(result.certifications) == {"RD", "CISSN"}
    # "earn the public trust of the community" is not a clearance.
    assert result.clearance is None
    assert (result.salary_min, result.salary_max, result.salary_period) == (60.0, 85.0, "hour")
    assert result.education == "Bachelor"
    assert result.years_experience_min == 5
    assert result.employment_type == "Contract"
    assert result.installation is None
    assert result.service_branch is None
    assert result.program is None


def test_realistic_posting_ignores_the_equipment_budget():
    """The SOF posting names a $250,000 budget before it names the salary."""
    result = enrich_text("Coach", SOF_POSTING)
    assert result.salary_min == 85000.0


def test_realistic_posting_ignores_the_headcount():
    result = enrich_text("Coach", FIRST_RESPONDER_POSTING)
    assert result.salary_max == 85.0


def test_federal_grade_prefix_does_not_become_the_salary():
    """"GS-12" is a pay grade sitting right next to the pay range."""
    result = enrich_text("Exercise Physiologist", "GS-12 ($88,520 - $115,079 per year).")
    assert (result.salary_min, result.salary_max) == (88520.0, 115079.0)


def test_zero_pay_is_rejected():
    assert enrich_text("Coach", "", compensation="$0.00 - $0.00").salary_min is None


# --------------------------------------------------------------------------
# Typography from HTML extraction
# --------------------------------------------------------------------------
# Descriptions reach us as text pulled out of HTML, so they are full of the
# characters a CMS substitutes automatically. Every one of these previously
# produced a *wrong* answer rather than a missing one.

@pytest.mark.parametrize(
    "text,expected",
    [
        ("Master’s degree in exercise physiology required.", "Master"),
        ("Associate’s degree in a health science field.", "Associate"),
        ("Bachelor’s degree in exercise science required.", "Bachelor"),
    ],
)
def test_curly_apostrophe_does_not_hide_the_degree(text, expected):
    """U+2019 is what a CMS writes; the ASCII apostrophe is the exception."""
    assert enrich_text("Coach", text).education == expected


def test_curly_apostrophe_still_reports_the_floor():
    result = enrich_text(
        "Strength Coach",
        "Bachelor’s degree required. Master’s degree preferred.",
    )
    assert result.education == "Bachelor"


def test_curly_apostrophe_in_years_of_experience():
    assert enrich_text("Coach", "Requires 5 years’ experience.").years_experience_min == 5


@pytest.mark.parametrize("dash", ["-", "‐", "‒", "–", "—", "−"])
def test_every_dash_variant_is_a_range_separator(dash):
    result = enrich_text("Coach", "", compensation=f"$75,000 {dash} $95,000 per year")
    assert (result.salary_min, result.salary_max) == (75000.0, 95000.0)


@pytest.mark.parametrize("dash", ["-", "–", "—"])
def test_every_dash_variant_works_in_a_years_range(dash):
    text = f"Requires {dash.join('35')} years of experience."
    assert enrich_text("Coach", text).years_experience_min == 3


def test_non_breaking_space_does_not_break_a_range():
    result = enrich_text("Coach", "", compensation="$75,000 - $95,000 per year")
    assert (result.salary_min, result.salary_max) == (75000.0, 95000.0)


def test_curly_quotes_do_not_hide_the_program():
    assert enrich_text("Coach", "Assigned to the “SMART Center”.").program == "SMART"


# --------------------------------------------------------------------------
# Salary -- range formats that must not collapse to their floor
# --------------------------------------------------------------------------
# Reporting min == max when a real band was stated is worse than reporting
# nothing: it publishes a ceiling that is tens of thousands too low, and it
# looks entirely plausible in an aggregate.

@pytest.mark.parametrize(
    "text,expected",
    [
        # Prose states a band with "and", not a dash.
        ("between $80,000 and $95,000 per year", (80000.0, 95000.0)),
        # The currency marker sits on the near side of the separator.
        ("90,000.00 USD - 115,000.00 USD", (90000.0, 115000.0)),
        # Each endpoint carries its own period label.
        ("$75,000/yr - $95,000/yr", (75000.0, 95000.0)),
        ("$75,000 annually - $95,000 annually", (75000.0, 95000.0)),
        ("$32.50/hr - $48.75/hr", (32.5, 48.75)),
    ],
)
def test_range_formats_do_not_collapse_to_one_endpoint(text, expected):
    result = enrich_text("Coach", "", compensation=text)
    assert (result.salary_min, result.salary_max) == expected


def test_between_and_range_in_description_prose():
    result = enrich_text(
        "Strength Coach",
        "The advertised salary range is between $80,000 and $95,000 per year.",
    )
    assert (result.salary_min, result.salary_max) == (80000.0, 95000.0)


def test_and_is_only_a_separator_when_it_is_the_whole_gap():
    """"$85,000 and relocation of $10,000" is two facts, not a band."""
    result = enrich_text(
        "Strength Coach",
        "Salary is $85,000 per year and relocation of $10,000 is available.",
    )
    assert (result.salary_min, result.salary_max) == (85000.0, 85000.0)


# --------------------------------------------------------------------------
# Salary -- one-time payments are not the pay rate
# --------------------------------------------------------------------------
# A sign-on bonus stated as a band is range-shaped, so it outranks the real
# salary and wins outright unless it is vetoed.

def test_a_bonus_range_does_not_become_the_salary():
    result = enrich_text(
        "Strength Coach",
        "Sign-on bonus of $10,000 - $15,000. Salary is $85,000 per year.",
    )
    assert (result.salary_min, result.salary_max) == (85000.0, 85000.0)


def test_a_relocation_range_does_not_become_the_salary():
    result = enrich_text(
        "Strength Coach",
        "Relocation assistance of $12,000 - $20,000. Salary: $85,000 - $110,000 per year.",
    )
    assert (result.salary_min, result.salary_max) == (85000.0, 110000.0)


@pytest.mark.parametrize(
    "text",
    [
        "A signing bonus of $15,000 is offered. Compensation is competitive.",
        "Relocation reimbursement of $20,000 is available. Pay is negotiable.",
        "Retention bonus of $12,000 after two years. Salary is competitive.",
        "$18,000 severance is provided on contract completion. Pay varies.",
    ],
)
def test_one_time_payments_are_never_the_salary(text):
    result = enrich_text("Strength Coach", text)
    assert result.salary_min is None
    assert result.salary_max is None


def test_a_bonus_mentioned_after_the_salary_does_not_veto_it():
    """"bonus" trails a real salary constantly; only the labels veto."""
    result = enrich_text("Coach", "Salary is $85,000 per year plus an annual bonus.")
    assert (result.salary_min, result.salary_max) == (85000.0, 85000.0)


def test_hiring_range_is_the_salary_not_a_hiring_bonus():
    """"Hiring range" is standard ATS phrasing for the actual band."""
    result = enrich_text("Coach", "The hiring range is $85,000 - $95,000 per year.")
    assert (result.salary_min, result.salary_max) == (85000.0, 95000.0)


def test_a_hiring_bonus_touching_the_figure_is_still_vetoed():
    result = enrich_text("Coach", "A $15,000 hiring bonus is offered. Pay is competitive.")
    assert result.salary_min is None


# --------------------------------------------------------------------------
# Certifications -- "RD" is a road as often as it is a dietitian
# --------------------------------------------------------------------------

@pytest.mark.parametrize(
    "text",
    [
        # Federal postings print facility addresses in full capitals, which
        # defeats the uppercase-only rule on its own.
        "Report to BLDG 4-2817 REILLY RD, FORT BRAGG, NC 28310.",
        "Facility is at 2175 REILLY RD near the airfield.",
        "Parking is available off SOUTHGATE RD.",
    ],
)
def test_an_address_does_not_produce_an_rd_credential(text):
    assert enrich_text("Human Performance Coach", text).certifications == []


@pytest.mark.parametrize(
    "text",
    [
        "RD required.",
        "RD credential in dietetics required.",
        "Registered Dietitian (RD/RDN) wanted.",
        "Must hold an active RD certification.",
        "RD or RDN preferred.",
    ],
)
def test_rd_still_counts_when_credential_vocabulary_is_present(text):
    assert "RD" in enrich_text("Performance Dietitian", text).certifications


def test_rdn_needs_no_supporting_context():
    """"RDN" has no ordinary-English meaning, so it stands on its own."""
    assert enrich_text("Coach", "RDN.").certifications == ["RD"]


# --------------------------------------------------------------------------
# Pathological input must not hang the run
# --------------------------------------------------------------------------
# A description pulled out of pretty-printed HTML routinely carries runs of
# hundreds of whitespace characters. Several patterns here stack optional
# groups separated by ``\s*``, which lets the engine redistribute one run
# across every gap -- polynomial backtracking. A 400-space run took fifteen
# seconds to reject and an 800-space run never finished, which is a hung
# nightly run, not a slow one.

_REDOS_BUDGET_SECONDS = 5.0


@pytest.mark.parametrize(
    "description",
    [
        "5" + " " * 20000 + "q",
        "Requires 5" + " " * 20000 + "of experience",
        "401" + " " * 20000 + "z",
        "three" + " " * 20000 + "x",
        "5 (5) to 7" + " " * 20000 + "y",
        " " * 20000,
        ("5   ( ) + - to  " * 2000),
    ],
)
def test_whitespace_runs_do_not_blow_up_the_matcher(description):
    start = time.monotonic()
    enrich_text("Human Performance Coach", description)
    assert time.monotonic() - start < _REDOS_BUDGET_SECONDS


def test_a_huge_whitespace_gap_between_two_figures_does_not_hang():
    """The gap between two numbers is matched whole, so it is unbounded."""
    start = time.monotonic()
    result = enrich_text("Coach", "", compensation="$75,000" + " " * 40000 + "$95,000")
    assert time.monotonic() - start < _REDOS_BUDGET_SECONDS
    # Not a range: the separator never matched, so only the first figure reads.
    assert result.salary_max == 75000.0


def test_a_long_realistic_description_stays_fast():
    body = "Requires 5 years of experience. Salary $85,000 per year. " * 5000
    start = time.monotonic()
    enrich_text("Strength and Conditioning Coach", body)
    assert time.monotonic() - start < _REDOS_BUDGET_SECONDS


# --------------------------------------------------------------------------
# None-valued fields, which is what a thin source adapter actually hands over
# --------------------------------------------------------------------------

def test_none_arguments_are_treated_as_absent():
    result = enrich_text(None, None, None, None)  # type: ignore[arg-type]
    assert result.to_dict() == Enrichment().to_dict()


def test_enrich_survives_none_valued_posting_fields():
    posting = make("Strength Coach", "CSCS required.")
    posting.compensation = None
    posting.department = None
    result = enrich(posting)
    assert result.certifications == ["CSCS"]


def test_a_compound_hour_unit_is_not_a_pay_rate():
    """Serco's H2F postings advertise the SCHEDULE, not a wage.

    "Enjoy a predictable daily work schedule and 80-hour pay periods
    (generally 40-hour work weeks)."

    The unit-noun veto only skipped whitespace before the noun, so "80 hours"
    was rejected while the compound adjective "80-hour" sailed past. "pay" two
    words later satisfied the salary cue, and 22 of the 91 jobs on the board
    published a floor of $80/hr -> $166,400 a year, roughly a hundred thousand
    above what an H2F strength and conditioning coach actually earns.
    """
    result = enrich_text(
        "H2Fit: Strength & Conditioning Coach - Fort Bragg, NC",
        "Enjoy a predictable daily work schedule and 80-hour pay periods "
        "(generally 40-hour work weeks). No away games and no weekend work.",
    )
    assert (result.salary_min, result.salary_max, result.salary_period) == (None, None, None)


@pytest.mark.parametrize(
    "sentence",
    [
        "Supports a 12-hour shift rotation with paid overtime.",
        "Requires 40-hour work weeks and occasional travel.",
        "A 90-day probationary period applies before benefits begin.",
        "Salaried role managing a 250-soldier population.",
    ],
)
def test_other_compound_units_are_not_pay_either(sentence):
    result = enrich_text("Coach", sentence)
    assert (result.salary_min, result.salary_max, result.salary_period) == (None, None, None)


@pytest.mark.parametrize(
    "sentence,expected",
    [
        ("The salary range is $75,000 - $95,000 per year.", (75000.0, 95000.0, "year")),
        ("Compensation: $38.50 per hour.", (38.5, 38.5, "hour")),
        ("Pay range $60k-$80k annually.", (60000.0, 80000.0, "year")),
        ("This position pays $45/hr.", (45.0, 45.0, "hour")),
    ],
)
def test_real_pay_statements_still_parse(sentence, expected):
    """The other half of the guard: tightening must not silently empty salary."""
    result = enrich_text("Coach", sentence)
    assert (result.salary_min, result.salary_max, result.salary_period) == expected


def test_benefits_prose_is_not_a_salary_cue():
    """The bare words "paid", "pay", "rate" and "range" are everywhere.

    Both of these sat in one real Serco H2F posting, and between them
    published a strength and conditioning coach at $80/hr ($166,400) and then
    at $10/hr. The cue list is the only gate on a number carrying neither a
    currency symbol nor a "k" suffix, so it must not contain a word a benefits
    section says in passing.
    """
    for sentence in (
        "Support your work/life balance with 10 paid Federal Holidays and paid time off.",
        "Enjoy a predictable daily work schedule and 80-hour pay periods.",
        "Ability to travel up to 10%, as required, to support dispersed units.",
        "This role has a wide range of 15 responsibilities.",
    ):
        result = enrich_text("H2Fit: Strength & Conditioning Coach", sentence)
        assert result.salary_min is None, sentence


@pytest.mark.parametrize(
    "sentence,expected",
    [
        ("Salary: 78,000 annually.", (78000.0, 78000.0, "year")),
        ("The hourly rate is 32.50.", (32.5, 32.5, "hour")),
        ("Compensation of 85,000 per year.", (85000.0, 85000.0, "year")),
    ],
)
def test_a_bare_number_with_a_real_cue_still_parses(sentence, expected):
    """Tightening the cue list must not cost the unsymbolled real cases."""
    result = enrich_text("Coach", sentence)
    assert (result.salary_min, result.salary_max, result.salary_period) == expected
