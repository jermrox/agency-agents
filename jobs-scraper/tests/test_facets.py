"""Facet tests.

The cases below are drawn from the real board rather than invented: every
title, location, and phrase in here appeared in a live posting. The negative
cases matter more than the positive ones -- a facet that over-matches hides
jobs from the person who wanted them.
"""

from __future__ import annotations

from tactical_jobs.facets import (
    branch_labels,
    branches_of,
    contingency_of,
    discipline_of,
    facets_for,
    is_lead,
    location_classes,
    salary_floor_annual,
)
from tactical_jobs.models import JobPosting


# --------------------------------------------------------------------------
# Discipline
# --------------------------------------------------------------------------


def test_discipline_reads_real_board_titles():
    cases = {
        "Certified Strength and Conditioning Coach (CSCS) - HPO": "strength-conditioning",
        "H2FIT: Strength and Conditioning Coaches (multiple locations)": "strength-conditioning",
        "Certified Athletic Trainer (ATC) - HPO": "athletic-training",
        "Athletic Trainer - Army H2F Program": "athletic-training",
        "Special Operations Physical Therapist (5th SFG(A))": "physical-therapy",
        "Special Operations Performance Dietitian (352 SOW)": "nutrition",
        "Cognitive Performance Specialist (RQ204500)": "cognitive-performance",
        "Special Operations Human Performance Advisor (SOCEUR)": "human-performance",
        "On-Site Human Performance Specialist": "human-performance",
    }
    for title, expected in cases.items():
        assert discipline_of(title) == expected, title


def test_specific_discipline_beats_the_generalist_bucket():
    # Nearly every title on this board contains "human performance". The
    # generalist bucket must never swallow a job that names a real discipline.
    assert (
        discipline_of("Human Performance Athletic Trainer, H2F")
        == "athletic-training"
    )
    assert (
        discipline_of("Human Performance Dietitian, POTFF") == "nutrition"
    )


def test_description_is_only_a_fallback_and_only_reads_the_head():
    # A strength job whose description mentions the rest of the embedded team
    # must not come back as nutrition or athletic training.
    description = (
        "Deliver strength programming to assigned units. "
        + "Filler. " * 80
        + "You will work alongside our registered dietitian and athletic trainer."
    )
    assert discipline_of("Tactical Performance Coach", description) == "human-performance"


def test_description_fallback_fires_when_the_title_is_silent():
    assert discipline_of("Contractor Support Role", "Registered Dietitian needed") == "nutrition"


def test_unmatched_title_is_other_not_a_guess():
    assert discipline_of("Program Analyst") == "other"


def test_credential_abbreviations_do_not_match_inside_words():
    # "ATC" inside MATCH/PATCH, "RD" inside WARD/THIRD, "PT" inside CAPTAIN.
    assert discipline_of("Match Coordinator") == "other"
    assert discipline_of("Third Shift Supervisor") == "other"


def test_lead_is_a_separate_axis_from_discipline():
    title = "H2F: Installation Lead Strength & Conditioning Coach"
    assert discipline_of(title) == "strength-conditioning"
    assert is_lead(title) is True
    assert is_lead("Certified Strength and Conditioning Coach (CSCS)") is False


# --------------------------------------------------------------------------
# Location
# --------------------------------------------------------------------------


def test_conus_and_oconus_from_real_locations():
    assert location_classes("Fort Bragg, NC") == frozenset({"conus"})
    assert location_classes("Kadena AB, Okinawa, Japan") == frozenset({"oconus"})
    assert location_classes("Baumholder, Germany") == frozenset({"oconus"})
    assert location_classes("RAF Lakenheath, UK") == frozenset({"oconus"})


def test_multi_location_postings_report_every_class():
    got = location_classes("Fort Bragg, NC / Hurlburt Field, FL / Coronado, CA")
    assert got == frozenset({"conus"})
    both = location_classes("Fort Campbell, KY and Stuttgart, Germany")
    assert both == frozenset({"conus", "oconus"})


def test_dod_definition_puts_alaska_and_hawaii_oconus():
    # CONUS is the 48 contiguous states. This surprises people, so it is pinned.
    assert "oconus" in location_classes("Joint Base Elmendorf-Richardson, AK")
    assert "oconus" in location_classes("Schofield Barracks, HI")
    assert "conus" not in location_classes("Schofield Barracks, HI")


def test_iso_country_codes_in_a_delimited_list_are_oconus():
    # Verbatim location string from the live NSCA board's Serco H2FIT posting.
    got = location_classes("JP; IT; DE; KY, US; AZ, US; HI, US; TX, US")
    assert got == frozenset({"conus", "oconus"})


def test_de_is_delaware_when_the_list_says_so_and_germany_when_it_does_not():
    # The one genuinely ambiguous code. The list format disambiguates it.
    assert location_classes("DE, US") == frozenset({"conus"})
    assert "oconus" in location_classes("JP; DE; KY, US")


def test_a_bare_us_state_list_is_not_dragged_oconus():
    assert location_classes("Fort Bliss, TX; Fort Riley, KS") == frozenset({"conus"})


def test_travel_and_tbd_placement_are_not_remote():
    # Both are real O2X location strings. Calling them remote would put a
    # traveling instructor in front of someone who needs work-from-home.
    assert location_classes("Various (travel)") == frozenset()
    assert location_classes("Placement determined after hire (relocation)") == frozenset()


def test_remote_is_detected_from_flag_or_text():
    assert "remote" in location_classes("", remote_flag=True)
    assert "remote" in location_classes("Remote (US)")
    assert "remote" not in location_classes("On-site; remote work is not available")


def test_unclassifiable_location_returns_empty_so_the_board_shows_it():
    assert location_classes("TBD") == frozenset()


# --------------------------------------------------------------------------
# Contingency -- the filter that protects candidates from resume collectors
# --------------------------------------------------------------------------


def test_award_contingency_is_flagged():
    assert (
        contingency_of("This position is contingent upon contract award.")
        == "contingent"
    )
    assert contingency_of("Role is contingent on funding.") == "contingent"


def test_contingent_attached_to_the_listing_needs_no_award_vocabulary():
    # Verbatim from the three live GDIT postings. "Contingent posting" is a
    # term of art in government contracting and is conclusive on its own --
    # requiring an award keyword nearby let all three through as "unknown".
    assert (
        contingency_of("Re-verified active. Contingent posting, expected 2026 start.")
        == "contingent"
    )
    for phrase in (
        "This is a contingent position.",
        "Contingency hire pending program start.",
        "Contingent requisition.",
    ):
        assert contingency_of(phrase) == "contingent", phrase


def test_onboarding_boilerplate_is_not_a_contingent_posting():
    # This sentence, or one like it, appears in a large share of all postings.
    # Matching it would flag essentially the entire board.
    boilerplate = (
        "Employment is contingent upon successful completion of a background "
        "check and drug screen."
    )
    assert contingency_of(boilerplate) == "unknown"
    assert contingency_of("Offer contingent upon E-Verify and I-9 review.") == "unknown"


def test_pipeline_language_counts_even_without_the_word_contingent():
    for phrase in (
        "We are building a talent pipeline for anticipated openings.",
        "Pending contract award, we expect several openings.",
        "If awarded, this role will begin in Q1.",
        "Submit your resume for future consideration.",
    ):
        assert contingency_of(phrase) == "contingent", phrase


def test_funded_is_only_claimed_when_the_posting_says_so():
    assert contingency_of("This is a fully funded position on an active contract.") == "funded"
    assert contingency_of("Great team, great mission.") == "unknown"


def test_contingent_wins_over_funded_when_both_appear():
    blob = "Active contract. Additional seats contingent upon award of the option year."
    assert contingency_of(blob) == "contingent"


# --------------------------------------------------------------------------
# Salary
# --------------------------------------------------------------------------


def test_salary_floor_annualizes_hourly_and_passes_through_annual():
    # Flat keys, matching exactly what enrich.Enrichment.to_dict() writes.
    assert salary_floor_annual({"salary_min": 63312, "salary_period": "year"}) == 63312
    assert (
        salary_floor_annual({"salary_min": 25.0, "salary_period": "hour"})
        == 25.0 * 2080
    )


def test_salary_floor_falls_back_to_max_when_only_a_ceiling_was_found():
    assert (
        salary_floor_annual(
            {"salary_min": None, "salary_max": 85000, "salary_period": "year"}
        )
        == 85000
    )


def test_salary_floor_is_none_when_nothing_was_extracted():
    assert salary_floor_annual({}) is None
    assert salary_floor_annual({"salary_min": None, "salary_max": None}) is None
    # An unrecognized period is not guessed at -- publishing a wrong number is
    # worse than publishing none.
    assert salary_floor_annual({"salary_min": 40, "salary_period": "week"}) is None


# --------------------------------------------------------------------------
# Assembly
# --------------------------------------------------------------------------


def test_facets_for_produces_the_published_shape():
    posting = JobPosting(
        source="workday:kbr",
        source_id="R2127121",
        url="https://example.invalid/job/R2127121",
        title="Special Operations Strength and Conditioning Specialist",
        employer="KBR",
        location="Hurlburt Field, FL",
        description="Support AFSOC POTFF. Position is fully funded.",
        enrichment={
            "salary_min": 85000,
            "salary_max": 105000,
            "salary_period": "year",
        },
    )
    facets = facets_for(posting)
    assert facets["discipline"] == "strength-conditioning"
    assert facets["discipline_label"] == "Strength & Conditioning"
    assert facets["lead"] is False
    assert facets["location_classes"] == ["conus"]
    assert facets["contingency"] == "funded"
    assert facets["salary_floor_annual"] == 85000


# --------------------------------------------------------------------------
# Cases found by reading live postings rather than by imagining phrasings
# --------------------------------------------------------------------------


def test_contingent_upon_a_vacancy_is_a_real_contingency():
    # Verbatim from KBR's live R2PC requisition. No contract is mentioned, but
    # for the candidate "the seat may not exist" is the same problem.
    assert (
        contingency_of("This position is contingent upon a vacancy at this location.")
        == "contingent"
    )


def test_behavioral_health_roles_get_their_own_bucket():
    for title in (
        "Special Operations Licensed Clinical Social Worker (Southern Pines, NC)",
        "Behavioral Health Provider, POTFF",
    ):
        assert discipline_of(title) == "behavioral-health", title


def test_sport_psychology_stays_with_cognitive_performance():
    # Ordering check: the behavioral-health patterns must not capture the
    # performance-psychology roles a mental performance coach is filtering for.
    assert discipline_of("Sport Psychologist, SOCOM POTFF") == "cognitive-performance"


def test_r2pc_routes_to_cognitive_performance_but_a_bare_title_does_not():
    assert discipline_of("Performance Expert (R2PC) - Fort Stewart, Georgia") == "cognitive-performance"
    assert discipline_of("Performance Expert - Fort Stewart, Georgia") == "human-performance"


# --- service branch ---------------------------------------------------------
#
# Every case below is a real posting pulled from a live board on 2026-08-28,
# not an invented string.


def test_employer_that_names_a_service_wins_over_the_installation():
    # USAJOBS posts this as Space Force at Schriever AFB -- a base the Space
    # Force inherited under its old Air Force name. Reading both fields would
    # file a Space Force job under Air Force.
    assert branches_of(
        "RECREATION ASSISTANT (FITNESS CENTER)",
        "United States Space Force",
        "Schriever AFB, Colorado",
    ) == frozenset({"space-force"})


def test_usajobs_organization_names_resolve_to_their_service():
    cases = {
        "U.S. Marine Corps": "marine-corps",
        "Commander, Navy Installations Command": "navy",
        "Department of the Army": "army",
        "United States Space Force": "space-force",
    }
    for employer, expected in cases.items():
        assert branches_of("Fitness Specialist", employer) == frozenset({expected}), employer


def test_h2f_is_an_army_program_even_without_the_word_army():
    # Serco's H2F postings never say "Army" in the title or location.
    assert branches_of(
        "H2Fit: Strength & Conditioning Coach - Fort Bragg, NC",
        "Serco USA",
        "Fort Bragg, North Carolina, USA",
    ) == frozenset({"army"})


def test_hitt_is_the_marine_corps_tell():
    assert "marine-corps" in branches_of("HITT INSTRUCTOR-LEVEL I, NF-0189-02", "", "")


def test_a_multi_service_requisition_reports_every_branch_it_serves():
    # One real GDIT req spanning an Army post, an Air Force field, and a joint
    # base. Collapsing this to a single branch would be wrong either way.
    found = branches_of(
        "Strength and Conditioning Specialists",
        "General Dynamics Information Technology",
        "USA NC Fort Bragg; USA CA San Diego; USA KY Fort Campbell; "
        "USA FL Hurlburt Field; USA WA Joint Base Lewis-McChord",
    )
    assert found == frozenset({"army", "air-force", "joint"})


def test_sof_requisition_across_three_services():
    assert branches_of(
        "Psychometrist",
        "General Dynamics Information Technology",
        "USA NC Fort Bragg; USA CA Coronado; USA NC Camp Lejeune",
    ) == frozenset({"army", "navy", "marine-corps"})


def test_fort_means_army_and_afb_means_air_force():
    assert branches_of("Athletic Trainer", "", "Fort Campbell, KY") == frozenset({"army"})
    assert branches_of("Athletic Trainer", "", "MacDill AFB, FL") == frozenset({"air-force"})


def test_potff_is_joint_not_a_single_service():
    assert "joint" in branches_of("Physical Therapist, POTFF", "", "")


def test_a_collegiate_role_has_no_branch_at_all():
    # The point of an empty set: the board treats unknown as "always show",
    # so guessing a branch here would hide the job from every filter.
    assert branches_of("Head Strength Coach", "State University", "Columbus, Ohio") == frozenset()


def test_description_is_only_consulted_when_the_strong_fields_are_silent():
    # A Serco H2F posting mentions the Air Force once, deep in boilerplate.
    # That must not add air-force to an Army job.
    army = branches_of(
        "H2Fit: Strength & Conditioning Coach - Fort Sill, OK",
        "Serco USA",
        "Fort Sill, Oklahoma, USA",
        "Serco supports the Army, Navy, Air Force and Marine Corps worldwide.",
    )
    assert army == frozenset({"army"})
    # With nothing in title/employer/location, the description is all there is.
    assert branches_of("Athletic Trainer", "", "", "Embedded with AFSOC aircrew.") == frozenset(
        {"air-force"}
    )


def test_branch_labels_come_back_in_canonical_order():
    assert branch_labels({"joint", "army", "navy"}) == ["Army", "Navy", "Joint / DoD-wide"]


def test_a_civilian_fort_city_is_not_an_army_post():
    # Fort Worth, Fort Lauderdale and Fort Collins are cities, not installations.
    # A VA hospital in Fort Lauderdale was being labelled Army because of this.
    for city in (
        "Fort Worth, Texas",
        "Fort Lauderdale, Florida",
        "Fort Collins, Colorado",
        "Fort Myers, Florida",
        "Fort Wayne, Indiana",
        "Fort Smith, Arkansas",
    ):
        assert branches_of("Physical Therapist", "", city) == frozenset(), city


def test_real_army_posts_still_resolve():
    for post in (
        "Fort Bragg, North Carolina",
        "Fort Campbell, Kentucky",
        "Fort Leonard Wood, Missouri",
        "Ft. Drum, NY",
        "Fort Wainwright",
        "Fort Belvoir, VA",
    ):
        assert branches_of("Athletic Trainer", "", post) == frozenset({"army"}), post
