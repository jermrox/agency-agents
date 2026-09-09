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


def test_the_installation_alone_clears_the_domain_floor():
    # KBR "Physical Therapist (Eielson AFB, AK)" and a DHA physical therapy
    # assistant at Fort Sill: the base is the only domain evidence, and other
    # DHA physical therapists were already on the board.
    posting = _posting(
        "Physical Therapist (Eielson AFB, AK)",
        "KBR",
        "Fairbanks, Alaska",
        "Provides outpatient physical therapy and return-to-duty rehabilitation.",
    )
    assert classify(posting) == Verdict.PUBLISH
    assert posting.domain_hits == ["service context"]


def test_a_veterans_clinic_on_a_former_base_gets_no_service_context():
    # VA Northern California sits on the old Mather AFB. The base name in the
    # location is history, not evidence about the work.
    posting = _posting(
        "Dietitian (Facility Program Coordinator)",
        "Veterans Health Administration",
        "Mather AFB, California",
        "Registered dietitian coordinating outpatient nutrition programs at the "
        "medical center.",
    )
    assert classify(posting) == Verdict.REJECT
    assert "service context" not in posting.domain_hits


def test_civilian_health_care_employers_are_rejected_outright():
    # USAJOBS 2026-09-05: a VA staff physical therapist in Abilene ("military"
    # three times in the credential boilerplate) and an Indian Health Service
    # physician assistant ("active duty", "uniformed" for the Commissioned
    # Corps) both reached PUBLISH on vocabulary about the applicant.
    va = _posting(
        "Staff Physical Therapist - EDRP Approved",
        "Veterans Health Administration",
        "Abilene, Texas",
        "Graduate of a military physical therapy program or an accredited program. "
        "Military physical therapists and physical therapy assistants with military "
        "training qualify. Outpatient musculoskeletal care for veterans.",
    )
    assert classify(va) == Verdict.REJECT
    assert va.exclusion_hits == ["civilian health care employer"]
    ihs = _posting(
        "Physician Assistant",
        "Indian Health Service",
        "Multiple Locations",
        "Commissioned Corps officers serve on active duty as members of a uniformed "
        "service. Physician assistant providing health promotion and primary care.",
    )
    assert classify(ihs) == Verdict.REJECT
    bop = _posting(
        "Clinical Psychologist (Chief Psychologist)",
        "Bureau of Prisons/Federal Prison System",
        "Three Rivers, Texas",
        "Doctoral degree in clinical psychology required. The Bureau of Prisons is a "
        "public safety agency; military spouse preference applies.",
    )
    assert classify(bop) == Verdict.REJECT


def test_a_single_body_mention_is_not_a_discipline():
    # Army National Guard "Safety and Occupational Health Manager (Title 32)"
    # at Fort Pickett: strong domain, and "health promotion" once in the body.
    safety = _posting(
        "Safety and Occupational Health Manager (Title 32) (Indefinite)",
        "Army National Guard Units",
        "Fort Pickett, Virginia",
        "Manages the installation safety program for Soldiers and DoD civilians. "
        "Coordinates with health promotion staff on the safety council.",
    )
    assert classify(safety) == Verdict.REJECT
    # AFSOC "Publicity Assistant (Graphic Designer)": the MWR fitness center
    # is mentioned once among the facilities the designer makes flyers for.
    designer = _posting(
        "PUBLICITY ASSISTANT (GRAPHIC DESIGNER)",
        "Air Force Special Operations Command",
        "Hurlburt Field, Florida",
        "Designs flyers and social media for special operations MWR programs "
        "including the fitness center, bowling center and outdoor recreation. "
        "Military spouse and veteran preference apply.",
    )
    assert classify(designer) == Verdict.REJECT


def test_two_body_terms_or_a_title_term_carry_a_posting():
    # Marine Corps "HITT Instructor" names no listed discipline in its title
    # but two in its text; KBR's SOF social workers name theirs in the title.
    hitt = _posting(
        "HITT INSTRUCTOR-LEVEL I, NF-0189-02",
        "U.S. Marine Corps",
        "Camp Lejeune, North Carolina",
        "Delivers High Intensity Tactical Training to Marines: strength and "
        "conditioning sessions and sports medicine referrals for the battalion.",
    )
    assert classify(hitt) == Verdict.PUBLISH
    lcsw = _posting(
        "Special Operations Licensed Clinical Social Worker (AFSOC GSU/Southern Pines)",
        "KBR",
        "Fort Bragg, North Carolina",
        "Embedded with the special operations unit's human performance team.",
    )
    assert classify(lcsw) == Verdict.PUBLISH
    assert "licensed clinical social worker" in lcsw.discipline_hits


def test_bare_clinical_professions_need_the_performance_context():
    # KBR "Special Operations Clinical Psychologist (75th Ranger Regiment)":
    # the POTFF description names human performance, so the title carries.
    sof = _posting(
        "Special Operations Clinical Psychologist (75th Ranger Regiment, Fort Benning, GA)",
        "KBR",
        "Fort Benning, Georgia",
        "Embedded with the Regiment's human performance and POTFF team.",
    )
    assert classify(sof) == Verdict.PUBLISH
    # A military treatment facility social worker: the same profession, no
    # performance context anywhere in the posting.
    clinic = _posting(
        "Social Worker (Clinical)",
        "Military Treatment Facilities under DHA",
        "Joint Base Lewis-McChord, Washington",
        "Provides clinical social work services to beneficiaries at the medical center.",
    )
    assert classify(clinic) == Verdict.REJECT
    # Air National Guard "SOCIAL WORKER" at Fairchild AFB: the title term
    # repeated three times in the body is still one weak signal.
    guard = _posting(
        "SOCIAL WORKER",
        "Air National Guard Units",
        "Fairchild AFB, Washington",
        "The social worker serves as the wing's social worker. The social worker "
        "provides counseling to Airmen in support of combat operational readiness. "
        "A licensed social worker is required.",
    )
    assert classify(guard) == Verdict.REJECT
    assert guard.discipline_hits == ["social worker"]
    # Case management is care coordination, never human performance, whatever
    # team it sits on (KBR's SOF nurse case managers, an ICE behavioral
    # health case manager).
    case = _posting(
        "Special Operations Case Manager / Nurse Case Manager (Hampton Roads, VA)",
        "KBR",
        "Hampton, Virginia",
        "Coordinates care for the special operations human performance program; "
        "liaises with the unit psychologist and social worker.",
    )
    assert classify(case) == Verdict.REJECT
    assert "case manager" in case.exclusion_hits


def test_a_uniformed_occupation_in_the_title_is_not_a_performance_job():
    # USAJOBS 883089300, on the live board 2026-08-29 to 2026-09-05: a military
    # training instructor billet in the pararescue pipeline, carried by the
    # fitness test its students take and one "strength and conditioning".
    pj = _posting(
        "TRAINING INSTRUCTOR (PARARESCUE)",
        "Air Education and Training Command",
        "Lackland AFB, Texas",
        "Instructs pararescue apprentice course students in special tactics skills. "
        "Students must pass the physical ability and stamina test. Plans strength "
        "and conditioning sessions and sports medicine referrals for the class.",
    )
    assert classify(pj) == Verdict.REJECT
    assert "training instructor" in pj.exclusion_hits
    # The coach who trains them is the job the board exists for.
    coach = _posting(
        "Strength and Conditioning Coach (Pararescue)",
        "KBR",
        "Hurlburt Field, Florida",
        "Special operations human performance program for the pararescue squadron.",
    )
    assert classify(coach) == Verdict.PUBLISH
    # A recruiting-pipeline operator posting: fitness tests all over it, no job.
    swo = _posting(
        "Special Warfare Operator",
        "United States Navy",
        "Coronado, California",
        "Candidates must pass the physical screening test and the physical "
        "readiness test; physical readiness standards apply throughout training.",
    )
    assert classify(swo) == Verdict.REJECT
    drill = _posting(
        "Drill Sergeant",
        "United States Army",
        "Fort Jackson, South Carolina",
        "Leads basic training; administers the Army Combat Fitness Test.",
    )
    assert classify(drill) == Verdict.REJECT


def test_hitt_instructors_carry_on_the_programme_name():
    for title in ("HITT INSTRUCTOR-LEVEL I, NF-0189-02", "High Intensity Tactical Training (HITT) Instructor"):
        posting = _posting(
            title,
            "U.S. Marine Corps",
            "Camp Lejeune, North Carolina",
            "Delivers the Marine Corps fitness programme to Marines of the battalion.",
        )
        assert classify(posting) == Verdict.PUBLISH, title


def test_the_marine_corps_warr_programme_is_read_as_human_performance():
    # USAJOBS 879684900, read on 2026-09-05: the Twentynine Palms WARR/Semper
    # Fit role. It was vetoed on "performance testing" (testing Marines) with
    # no discipline term in its title.
    posting = _posting(
        "Supervisory Performance Education Specialist NF4",
        "U.S. Marine Corps",
        "Twentynine Palms, California",
        "Serves as the Supervisory Performance Education Specialist for the Warrior "
        "Athlete Readiness and Resilience (WARR)/Semper Fit to improve readiness, "
        "lethality, and resilience of the total force in all domains of Marine Corps "
        "Total Fitness. Prepares content on sleep science, recovery and adaptation. "
        "Conducts performance testing of Marines.",
    )
    assert classify(posting) == Verdict.PUBLISH
    assert "performance education" in posting.discipline_hits
    assert "semper fit" in posting.domain_hits


def test_ready_and_resilient_is_a_discipline():
    posting = _posting(
        "Readiness and Resilience Division Chief",
        "Joint Activities",
        "Fort Meade, Maryland",
        "Leads the Ready and Resilient program for Soldiers, Department of Defense "
        "civilians and families across the installation.",
    )
    assert classify(posting) == Verdict.PUBLISH
    assert "readiness and resilience" in posting.discipline_hits
    assert "cognitive" in posting.tags


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


def test_repeating_the_applicant_fitness_requirement_does_not_make_it_a_job():
    # Acuity International "Protective Security Specialists - WPS III
    # (Somalia)", 2026-09-05: "physical readiness" three times in the
    # candidate requirements, and three times the demoted weight cleared the
    # discipline floor alone.
    p = _posting(
        "Protective Security Specialists - WPS III (Somalia)",
        employer="Acuity International",
        location="Reston, VA",
        description=(
            "Provides protective security for Chief of Mission personnel. Must pass "
            "the physical readiness test at hire. Physical readiness standards are "
            "maintained throughout deployment; a physical readiness assessment is "
            "repeated annually. Prior military or law enforcement experience; veteran "
            "preferred."
        ),
    )
    assert classify(p, Thresholds()) == Verdict.REJECT
    assert p.discipline_hits == ["physical readiness"]


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


def test_youth_programmes_and_facility_staff_are_not_performance_jobs():
    """Read from the live board 2026-09-05: Army Child and Youth Services
    fitness and sports specialists teach children; Navy and Space Force
    "Recreation Assistant (Fitness Center)" posts open the building and clean
    the equipment. Neither is the job the board exists for, whatever
    discipline word the title also carries."""
    cys = _posting(
        "Fitness Specialist (CYS) NF-03",
        "United States Army Installation Management Command",
        "Fort Benning, Georgia",
        "Shares expertise in age-appropriate exercises and skills development for "
        "children and youth; supports installation volunteer sports coaches.",
    )
    assert classify(cys) == Verdict.REJECT
    assert "cys" in cys.exclusion_hits
    attendant = _posting(
        "Recreation Assistant - Pearl Harbor Fitness Center",
        "Commander, Navy Installations Command",
        "Honolulu, Hawaii",
        "Opens and readies the fitness center, cleans equipment and prepares league "
        "schedules for service members under Navy Fitness, Sports and Aquatics standards.",
    )
    assert classify(attendant) == Verdict.REJECT
    intramural = _posting(
        "Sports Specialist NF-03",
        "United States Army Installation Management Command",
        "Schofield Barracks, Hawaii",
        "Plans and administers a sports program of individual and team sports for "
        "soldiers and families.",
    )
    assert classify(intramural) == Verdict.REJECT
    # Installation fitness delivered to service members stays.
    trainer = _posting(
        "Recreation Specialist - Fitness Specialist",
        "Commander, Navy Installations Command",
        "Virginia Beach, Virginia",
        "Designs, leads and evaluates individual and group exercise programs for "
        "active duty service members.",
    )
    assert classify(trainer) == Verdict.PUBLISH
    navy = _posting(
        "Sports Specialist (Fitness Trainer)",
        "Commander, Navy Installations Command",
        "Groton, Connecticut",
        "Instructs active duty sailors in strength and conditioning and leads fitness classes.",
    )
    assert classify(navy) == Verdict.PUBLISH


def test_research_administration_and_umbrella_notices_are_not_jobs():
    coordinator = _posting(
        "Clinical Research Coordinator",
        "The Geneva Foundation",
        "West Point, NY",
        "Principal administration liaison for a musculoskeletal injury study at Keller "
        "Army Community Hospital; maintains record keeping systems; coordinates "
        "physical therapy and sports medicine investigators.",
    )
    assert classify(coordinator) == Verdict.REJECT
    umbrella = _posting(
        "Medical",
        "Department of the Air Force Headquarters",
        "Location Negotiable After Selection",
        "Direct hire authority occupations: physical therapist, occupational "
        "therapist, nutritionist, physician assistant.",
    )
    assert classify(umbrella) == Verdict.REJECT
    assert umbrella.exclusion_hits == ["umbrella notice"]


def test_a_clinician_needs_a_named_programme_or_unit():
    clinic = _posting(
        "Supervisory Clinical Psychologist",
        "Military Treatment Facilities under DHA",
        "Fort Polk, Louisiana",
        "Conducts psychological evaluations and establishes psychiatric diagnoses for "
        "beneficiaries of the military treatment facility.",
    )
    assert classify(clinic) == Verdict.REJECT
    guard = _posting(
        "SOCIAL WORKER",
        "Army National Guard Units",
        "Carson City, Nevada",
        "Provides behavioral health services to Soldiers of the National Guard; "
        "return to duty determinations and health promotion.",
    )
    assert classify(guard) == Verdict.REJECT
    sof = _posting(
        "Special Operations Clinical Psychologist (Dam Neck, VA)",
        "KBR",
        "Virginia Beach, Virginia",
        "Embedded behavioral health on the POTFF team.",
    )
    assert classify(sof) == Verdict.PUBLISH


# --------------------------------------------------------------------------
# A VA facility named in the text; a clinician within an operational unit
# --------------------------------------------------------------------------


def test_a_staffing_firm_placement_at_a_va_hospital_is_rejected():
    # Loyal Source, 2026-09-09: "Pain Physical Therapist ... NY Harbor VA
    # Health Care System" reached PUBLISH on "military" and "veteran" repeated
    # in the text. The employer is the staffing firm; the work is the VA's.
    posting = make(
        "Pain Physical Therapist",
        "Loyal Source Government Services is looking for a full-time Pain Physical "
        "Therapist to provide services to the NY Harbor VA Health Care System. "
        "Physical Therapists must focus on patient care with our Veteran population "
        "while working with our VA community. Military and veteran applicants are "
        "encouraged; military spouses and veterans receive preference.",
        employer="Loyal Source Government Services",
        location="New York",
    )
    assert classify(posting) == Verdict.REJECT
    assert posting.exclusion_hits == ["civilian health care site"]


def test_a_va_mention_in_prior_experience_does_not_veto_a_potff_posting():
    # KBR's POTFF social workers list "Department of Veterans Affairs (VA) MTF"
    # among acceptable prior experience; the named programme keeps them.
    posting = make(
        "Special Operations Licensed Clinical Social Worker (Southern Pines, NC)",
        "Provide behavioral health services under the Preservation of the Force and "
        "Family (POTFF) program to special operations forces personnel. Licensed "
        "clinical social worker. Experience working in a Government setting such as "
        "a DOD or Department of Veterans Affairs (VA) MTF is desired.",
        employer="KBR",
        location="Southern Pines, North Carolina",
    )
    assert classify(posting) == Verdict.PUBLISH


def test_a_social_worker_within_an_operational_unit_is_embedded_behavioral_health():
    # Loyal Source, 2026-08-31: the contractor "shall function within an
    # operational unit, as a Behavioral Health Care Provider", attends the
    # commander's staff meetings and reports to the unit commander.
    posting = make(
        "Licensed Clinical Social Worker",
        "The contractor shall function within an operational unit, as a Behavioral "
        "Health Care Provider. The contractor shall attend commander's staff "
        "meetings and other meetings as directed by the unit Commander. Licensed "
        "clinical social worker applying evidence-based therapies in the evaluation "
        "and treatment of military service members. Veterans encouraged to apply.",
        employer="Loyal Source Government Services",
        location="Jacksonville, North Carolina",
    )
    assert classify(posting) == Verdict.PUBLISH
    assert "operational unit" in posting.domain_hits


def test_a_treatment_facility_psychologist_still_needs_a_programme():
    # The same employer's clinic psychologist: MTF privileges, psychiatric
    # diagnoses, medical and surgical patients, no unit or programme named.
    posting = make(
        "Clinical Psychologist",
        "The Psychologist shall practice within the guidelines of their state "
        "licensing board and MTF privileges, conduct psychological evaluations and "
        "establish psychiatric diagnoses, helping medical and surgical patients deal "
        "with illnesses. Military treatment facility. Veterans encouraged to apply.",
        employer="Loyal Source Government Services",
        location="Monterey, California",
    )
    assert classify(posting) == Verdict.REJECT
