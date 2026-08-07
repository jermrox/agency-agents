"""Insights tests: annualization, fingerprint dedupe, percentiles, and shares.

The bar for this module is not "produces numbers" -- it is "produces numbers
that mean something". So most of these tests are about the ways a naive
implementation would silently lie: mixing hourly with annual pay, counting a
job once per archived revision, or reading a state out of the word "in".
"""

from __future__ import annotations

import copy
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.insights import (  # noqa: E402
    DISCIPLINE_TAGS,
    DOMAIN_TAGS,
    annualized_salary,
    build_insights,
    render_summary,
    state_code,
)
from tactical_jobs.models import JobPosting  # noqa: E402

DEFAULT_ENRICHMENT: dict[str, Any] = {
    "certifications": ["CSCS", "TSAC-F"],
    "clearance": "Secret",
    "salary_min": 85000,
    "salary_max": 95000,
    "salary_period": "year",
    "education": "Bachelors",
    "years_experience_min": 3,
    "employment_type": "full-time",
    "installation": "Fort Liberty",
    "service_branch": "Army",
    "program": "THOR3",
}


def record(
    *,
    title: str = "Tactical Strength and Conditioning Coach",
    employer: str = "O2X Human Performance",
    location: str = "Fort Liberty, NC",
    posted_at: str | None = "2026-03-01T00:00:00+00:00",
    archived_at: str = "2026-03-02T00:00:00+00:00",
    remote: bool = False,
    tags: tuple[str, ...] = ("sof", "strength-conditioning"),
    enrichment: dict[str, Any] | None = None,
    fingerprint: str | None = None,
    source: str = "greenhouse:o2x",
    source_id: str = "1",
) -> dict[str, Any]:
    """An archive row in the shape ``JobPosting.to_archive_dict`` produces.

    ``fingerprint`` defaults to employer+title+location so that varying any of
    those in a test produces a genuinely distinct job, exactly as the real
    fingerprint would.
    """
    return {
        "id": f"{source}:{source_id}",
        "fingerprint": fingerprint or f"{employer}|{title}|{location}".casefold(),
        "source": source,
        "url": f"https://example.invalid/{source_id}",
        "title": title,
        "employer": employer,
        "location": location,
        "remote": remote,
        "department": None,
        "compensation": None,
        "posted_at": posted_at,
        "description": "CSCS and TSAC-F required. Embedded with a THOR3 team.",
        "score": 21.5,
        "tags": list(tags),
        "enrichment": DEFAULT_ENRICHMENT if enrichment is None else enrichment,
        "matched": {"domain": ["thor3"], "discipline": ["cscs"], "excluded_by": []},
        "source_id": source_id,
        "description_chars": 52,
        "archived_at": archived_at,
    }


def salaried(value: float, period: str = "year", **overrides: Any) -> dict[str, Any]:
    """A record whose only interesting property is what it pays."""
    enrichment = {"salary_min": value, "salary_max": value, "salary_period": period}
    return record(enrichment=enrichment, **overrides)


def names(entries: list[dict[str, Any]], key: str = "name") -> list[str]:
    return [entry[key] for entry in entries]


# --------------------------------------------------------------------------
# Empty corpus: the first run of a fresh checkout, not an error.
# --------------------------------------------------------------------------


def test_empty_corpus_returns_every_required_key():
    insights = build_insights([])
    assert set(insights) >= {
        "generated_at",
        "totals",
        "by_employer",
        "by_discipline",
        "by_domain",
        "by_branch",
        "by_installation",
        "by_state",
        "certifications",
        "clearances",
        "salary",
        "remote",
        "timeline",
        "trends",
        "top_titles",
    }


def test_empty_corpus_totals_are_zeroed():
    totals = build_insights([])["totals"]
    assert totals["postings"] == 0
    assert totals["employers"] == 0
    assert totals["unique_jobs"] == 0
    assert totals["with_salary"] == 0
    assert totals["date_span"] == {"earliest": None, "latest": None}


def test_empty_corpus_salary_block_is_none_not_zero():
    """Zero would claim the field pays nothing; None says we do not know."""
    salary = build_insights([])["salary"]
    assert salary["count"] == 0
    assert salary["median"] is None and salary["p25"] is None and salary["p75"] is None
    assert salary["min"] is None and salary["max"] is None
    assert salary["by_discipline"] == {}


def test_empty_corpus_lists_are_empty_and_remote_is_zero():
    insights = build_insights([])
    assert insights["by_employer"] == []
    assert insights["timeline"] == []
    assert insights["trends"]["fastest_growing_employers"] == []
    assert insights["remote"] == {"count": 0, "share": 0.0}


def test_render_summary_of_an_empty_corpus_says_so():
    text = render_summary(build_insights([]))
    assert "empty" in text.lower()
    assert text.endswith("\n")


def test_non_mapping_records_are_ignored_rather_than_fatal():
    insights = build_insights(["not a record", None, 42, record()])  # type: ignore[list-item]
    assert insights["totals"]["postings"] == 1
    assert insights["totals"]["unique_jobs"] == 1


def test_generated_at_is_a_parseable_utc_timestamp():
    stamp = datetime.fromisoformat(build_insights([])["generated_at"])
    assert stamp.tzinfo is not None
    assert stamp <= datetime.now(timezone.utc)


# --------------------------------------------------------------------------
# A single record: every section has to survive n=1.
# --------------------------------------------------------------------------


def test_single_record_totals():
    totals = build_insights([record()])["totals"]
    assert totals["postings"] == 1
    assert totals["unique_jobs"] == 1
    assert totals["employers"] == 1
    assert totals["with_salary"] == 1


def test_single_record_populates_every_facet():
    insights = build_insights([record()])
    assert insights["by_employer"][0]["name"] == "O2X Human Performance"
    assert insights["by_state"] == [{"code": "NC", "count": 1}]
    assert insights["by_installation"] == [{"name": "Fort Liberty", "count": 1}]
    assert insights["by_branch"] == [{"name": "Army", "count": 1}]
    assert insights["clearances"] == [{"name": "Secret", "count": 1}]
    assert names(insights["certifications"]) == ["CSCS", "TSAC-F"]
    assert insights["top_titles"][0]["count"] == 1


def test_single_record_salary_collapses_to_one_point():
    """One data point is a whole distribution, not an error."""
    salary = build_insights([salaried(90_000)])["salary"]
    assert salary["count"] == 1
    assert salary["min"] == salary["max"] == 90_000.0
    assert salary["p25"] == salary["median"] == salary["p75"] == 90_000.0


def test_real_archive_dict_is_consumed_unmodified():
    """Guards the contract with models.py rather than with the test's own helper."""
    posting = JobPosting(
        source="usajobs:fed",
        source_id="8827311",
        url="https://example.invalid/8827311",
        title="Exercise Physiologist",
        employer="US Army H2F",
        location="Fort Campbell, KY",
        description="H2F performance readiness.",
        posted_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
    )
    posting.tags = ["military", "strength-conditioning"]
    posting.enrichment = {"certifications": ["CSCS"], "salary_min": 82000, "salary_period": "year"}

    insights = build_insights([posting.to_archive_dict()])
    assert insights["totals"]["unique_jobs"] == 1
    assert insights["by_state"] == [{"code": "KY", "count": 1}]
    assert insights["salary"]["median"] == 82_000.0


# --------------------------------------------------------------------------
# Missing, null, and hostile enrichment.
# --------------------------------------------------------------------------


def test_missing_enrichment_key_does_not_crash():
    row = record()
    del row["enrichment"]
    insights = build_insights([row])
    assert insights["totals"]["unique_jobs"] == 1
    assert insights["totals"]["with_salary"] == 0
    assert insights["certifications"] == []


def test_none_enrichment_does_not_crash():
    insights = build_insights([{**record(), "enrichment": None}])
    assert insights["totals"]["with_salary"] == 0
    assert insights["clearances"] == []


def test_enrichment_of_the_wrong_type_is_ignored():
    insights = build_insights([{**record(), "enrichment": "TS/SCI, CSCS"}])
    assert insights["totals"]["unique_jobs"] == 1
    assert insights["certifications"] == []


def test_junk_values_inside_enrichment_are_skipped_individually():
    """One unusable field must not cost us the usable ones on the same record."""
    row = record(
        enrichment={
            "certifications": [None, "", "CSCS", 7],
            "clearance": 12345,
            "salary_min": "not a number",
            "salary_max": None,
            "installation": "Fort Carson",
        }
    )
    insights = build_insights([row])
    assert names(insights["certifications"]) == ["CSCS"]
    assert insights["clearances"] == []
    assert insights["by_installation"] == [{"name": "Fort Carson", "count": 1}]
    assert insights["totals"]["with_salary"] == 0


def test_a_bare_string_certification_field_is_read_as_one_certification():
    insights = build_insights([record(enrichment={"certifications": "TSAC-F"})])
    assert insights["certifications"] == [{"name": "TSAC-F", "count": 1, "share": 1.0}]


def test_missing_tags_leave_the_facets_empty_without_crashing():
    row = record()
    row["tags"] = None
    insights = build_insights([row])
    assert insights["by_discipline"] == []
    assert insights["by_domain"] == []


def test_missing_location_yields_no_state():
    insights = build_insights([record(location="")])
    assert insights["by_state"] == []


def test_records_are_not_mutated_by_analysis():
    rows = [record(source_id="1"), record(source_id="2", title="Athletic Trainer")]
    before = copy.deepcopy(rows)
    build_insights(rows)
    assert rows == before


def test_insights_are_json_serializable():
    """It gets written to a status file and served to the site verbatim."""
    payload = json.dumps(build_insights([record(), record(title="Athletic Trainer")]))
    assert json.loads(payload)["totals"]["unique_jobs"] == 2


# --------------------------------------------------------------------------
# Annualization: the assumption everything about pay rests on.
# --------------------------------------------------------------------------


def test_hourly_and_annual_pay_of_equal_value_land_in_the_same_band():
    """$50/hr and $104,000/yr are the same job. The report has to agree."""
    insights = build_insights(
        [salaried(50, "hour"), salaried(104_000, "year", title="Coach B", source_id="2")]
    )
    salary = insights["salary"]
    assert salary["count"] == 2
    assert salary["min"] == salary["max"] == 104_000.0
    assert salary["median"] == 104_000.0


def test_hourly_pay_is_multiplied_by_2080():
    assert build_insights([salaried(45, "hour")])["salary"]["median"] == 93_600.0


def test_unannualized_hourly_pay_would_have_wrecked_the_median():
    """The regression this whole rule exists to prevent."""
    insights = build_insights(
        [salaried(45, "hour"), salaried(95_000, "year", title="Coach B", source_id="2")]
    )
    assert insights["salary"]["count"] == 2
    assert insights["salary"]["median"] > 90_000
    # The bug this guards: an unannualized 45 would be the minimum of the set.
    assert insights["salary"]["min"] > 90_000


def test_period_labels_are_read_loosely():
    for period in ("hour", "Hourly", "per hour", "USD/hour", "HR"):
        assert annualized_salary({"salary_min": 50, "salary_period": period}) == 104_000.0
    for period in ("year", "Annual", "per year", "annually", "salary"):
        assert annualized_salary({"salary_min": 104_000, "salary_period": period}) == 104_000.0


def test_monthly_and_weekly_periods_annualize():
    assert annualized_salary({"salary_min": 8_000, "salary_period": "month"}) == 96_000.0
    assert annualized_salary({"salary_min": 2_000, "salary_period": "weekly"}) == 104_000.0


def test_an_unlabeled_small_figure_is_read_as_hourly():
    """Federal postings routinely omit the period; magnitude is the tiebreaker."""
    assert annualized_salary({"salary_min": 42, "salary_max": 48}) == 45 * 2080


def test_an_unlabeled_large_figure_is_read_as_annual():
    assert annualized_salary({"salary_min": 90_000, "salary_max": 100_000}) == 95_000.0


def test_a_band_is_reported_at_its_midpoint():
    assert annualized_salary({"salary_min": 80_000, "salary_max": 100_000}) == 90_000.0


def test_a_one_sided_band_uses_the_figure_it_has():
    assert annualized_salary({"salary_min": 78_000, "salary_period": "year"}) == 78_000.0
    assert annualized_salary({"salary_max": 78_000, "salary_period": "year"}) == 78_000.0


def test_salary_strings_with_currency_formatting_are_read():
    assert annualized_salary({"salary_min": "$95,000", "salary_period": "per year"}) == 95_000.0


def test_absent_or_zero_salary_is_not_a_salary():
    assert annualized_salary({}) is None
    assert annualized_salary(None) is None
    assert annualized_salary({"salary_min": 0, "salary_max": 0}) is None


def test_parse_artifacts_outside_the_plausible_band_are_dropped():
    """A "$1.00" placeholder would drag a median further than any real outlier."""
    assert annualized_salary({"salary_min": 1, "salary_period": "year"}) is None
    assert annualized_salary({"salary_min": 99_000_000, "salary_period": "year"}) is None
    corpus = [salaried(1, "year"), salaried(90_000, "year", title="Coach B", source_id="2")]
    assert build_insights(corpus)["salary"] == {
        "count": 1,
        "min": 90_000.0,
        "max": 90_000.0,
        "median": 90_000.0,
        "p25": 90_000.0,
        "p75": 90_000.0,
        "by_discipline": {"strength-conditioning": {
            "count": 1,
            "min": 90_000.0,
            "max": 90_000.0,
            "median": 90_000.0,
            "p25": 90_000.0,
            "p75": 90_000.0,
        }},
    }


def test_a_boolean_is_never_a_salary():
    assert annualized_salary({"salary_min": True, "salary_max": True}) is None


# --------------------------------------------------------------------------
# Fingerprint dedupe: one job stays one job however often it is archived.
# --------------------------------------------------------------------------


def test_postings_and_unique_jobs_diverge_on_re_posts():
    rows = [record(source_id=str(n)) for n in range(5)]
    rows.append(record(title="Athletic Trainer", source_id="6"))
    totals = build_insights(rows)["totals"]
    assert totals["postings"] == 6
    assert totals["unique_jobs"] == 2


def test_a_job_archived_five_times_counts_once_toward_salary():
    rows = [salaried(100_000, source_id=str(n)) for n in range(5)]
    rows.append(salaried(50_000, title="Athletic Trainer", source_id="9"))
    salary = build_insights(rows)["salary"]
    assert salary["count"] == 2
    assert salary["median"] == 75_000.0


def test_a_job_archived_five_times_counts_once_toward_its_employer():
    rows = [record(source_id=str(n)) for n in range(5)]
    assert build_insights(rows)["by_employer"][0]["count"] == 1


def test_syndication_across_two_boards_counts_once():
    """Same job, two sources, two identities, one fingerprint."""
    rows = [
        record(source="greenhouse:o2x", source_id="1"),
        record(source="usajobs:fed", source_id="8827311"),
    ]
    totals = build_insights(rows)["totals"]
    assert totals["postings"] == 2
    assert totals["unique_jobs"] == 1


def test_the_newest_archived_revision_wins():
    """An employer who adds a salary band later is telling us something new."""
    old = salaried(80_000, archived_at="2026-01-01T00:00:00+00:00")
    new = salaried(120_000, archived_at="2026-06-01T00:00:00+00:00")
    assert build_insights([new, old])["salary"]["median"] == 120_000.0
    assert build_insights([old, new])["salary"]["median"] == 120_000.0


def test_records_without_a_fingerprint_do_not_collapse_together():
    rows = []
    for index in range(3):
        row = record(source_id=str(index), title=f"Coach {index}")
        del row["fingerprint"]
        rows.append(row)
    assert build_insights(rows)["totals"]["unique_jobs"] == 3


def test_employers_are_grouped_case_insensitively():
    rows = [
        record(employer="US Army H2F", title="Coach", source_id="1"),
        record(employer="US ARMY H2F", title="Athletic Trainer", source_id="2"),
    ]
    insights = build_insights(rows)
    assert insights["totals"]["employers"] == 1
    assert insights["by_employer"] == [
        {
            "name": "US Army H2F",
            "count": 2,
            "disciplines": ["strength-conditioning"],
            "median_salary": 90_000.0,
        }
    ]


# --------------------------------------------------------------------------
# Percentile math.
# --------------------------------------------------------------------------


def test_percentiles_on_an_odd_sized_set_hit_real_data_points():
    rows = [
        salaried(value, source_id=str(index), title=f"Coach {index}")
        for index, value in enumerate((60_000, 70_000, 80_000, 90_000, 100_000))
    ]
    salary = build_insights(rows)["salary"]
    assert salary["p25"] == 70_000.0
    assert salary["median"] == 80_000.0
    assert salary["p75"] == 90_000.0


def test_percentiles_on_an_even_sized_set_interpolate():
    rows = [
        salaried(value, source_id=str(index), title=f"Coach {index}")
        for index, value in enumerate((60_000, 70_000, 80_000, 90_000))
    ]
    salary = build_insights(rows)["salary"]
    assert salary["p25"] == 67_500.0
    assert salary["median"] == 75_000.0
    assert salary["p75"] == 82_500.0


def test_median_agrees_with_the_standard_library():
    values = [61_000, 74_500, 88_000, 92_250, 130_000, 45_000, 99_999]
    rows = [
        salaried(value, source_id=str(index), title=f"Coach {index}")
        for index, value in enumerate(values)
    ]
    assert build_insights(rows)["salary"]["median"] == round(statistics.median(values), 2)


def test_percentiles_are_ordered_and_bracket_the_median():
    values = (52_000, 61_000, 74_500, 88_000, 92_250, 130_000)
    rows = [
        salaried(value, source_id=str(index), title=f"Coach {index}")
        for index, value in enumerate(values)
    ]
    salary = build_insights(rows)["salary"]
    assert salary["min"] <= salary["p25"] <= salary["median"] <= salary["p75"] <= salary["max"]


def test_salary_is_broken_out_by_discipline():
    rows = [
        salaried(100_000, title="Coach", tags=("strength-conditioning",), source_id="1"),
        salaried(60_000, title="Trainer", tags=("sports-medicine",), source_id="2"),
        salaried(80_000, title="Lead Coach", tags=("strength-conditioning",), source_id="3"),
    ]
    by_discipline = build_insights(rows)["salary"]["by_discipline"]
    assert by_discipline["strength-conditioning"]["median"] == 90_000.0
    assert by_discipline["sports-medicine"]["count"] == 1
    assert "nutrition" not in by_discipline


def test_employer_median_salary_is_none_when_nothing_is_published():
    rows = [record(enrichment={"installation": "JBLM"})]
    assert build_insights(rows)["by_employer"][0]["median_salary"] is None


# --------------------------------------------------------------------------
# State parsing.
# --------------------------------------------------------------------------


def test_state_from_a_trailing_two_letter_code():
    assert state_code("Fort Bragg, NC") == "NC"
    assert state_code("Joint Base Lewis-McChord, WA") == "WA"


def test_state_survives_a_trailing_zip_and_country():
    assert state_code("Coronado, CA 92118") == "CA"
    assert state_code("Fort Campbell, KY 42223, USA") == "KY"


def test_state_from_a_spelled_out_name():
    assert state_code("Fayetteville, North Carolina") == "NC"
    assert state_code("Camp Lejeune, North Carolina, United States") == "NC"


def test_longer_state_names_win_over_the_names_inside_them():
    assert state_code("Morgantown, West Virginia") == "WV"


def test_the_district_is_not_washington_state():
    assert state_code("Washington, D.C.") == "DC"
    assert state_code("Washington, DC") == "DC"
    assert state_code("Tacoma, Washington") == "WA"


def test_remote_and_unparseable_locations_have_no_state():
    assert state_code("Remote") is None
    assert state_code("Multiple Locations") is None
    assert state_code("") is None
    assert state_code(None) is None


def test_prose_two_letter_words_are_not_read_as_states():
    """"Remote in US" is not Indiana; half the state codes are English words."""
    assert state_code("Remote in US") is None
    assert state_code("Hiring now or later") is None


def test_a_lowercase_trailing_code_is_still_a_state():
    assert state_code("fort campbell, ky") == "KY"


def test_a_leading_abbreviation_does_not_beat_the_real_state():
    assert state_code("JB Lewis-McChord, WA") == "WA"


def test_by_state_aggregates_and_ranks():
    rows = [
        record(location="Fort Liberty, NC", title="Coach A", source_id="1"),
        record(location="Fort Bragg, NC 28310", title="Coach B", source_id="2"),
        record(location="Coronado, CA", title="Coach C", source_id="3"),
        record(location="Remote", title="Coach D", source_id="4"),
    ]
    assert build_insights(rows)["by_state"] == [
        {"code": "NC", "count": 2},
        {"code": "CA", "count": 1},
    ]


# --------------------------------------------------------------------------
# Timeline.
# --------------------------------------------------------------------------


def test_timeline_buckets_by_month():
    rows = [
        record(posted_at="2026-01-05T00:00:00+00:00", title="A", source_id="1"),
        record(posted_at="2026-01-20T00:00:00+00:00", title="B", source_id="2"),
        record(posted_at="2026-03-10T00:00:00+00:00", title="C", source_id="3"),
    ]
    assert build_insights(rows)["timeline"] == [
        {"month": "2026-01", "count": 2},
        {"month": "2026-02", "count": 0},
        {"month": "2026-03", "count": 1},
    ]


def test_timeline_is_chronological_regardless_of_input_order():
    rows = [
        record(posted_at="2026-05-01T00:00:00+00:00", title="C", source_id="3"),
        record(posted_at="2025-11-01T00:00:00+00:00", title="A", source_id="1"),
        record(posted_at="2026-02-01T00:00:00+00:00", title="B", source_id="2"),
    ]
    months = [entry["month"] for entry in build_insights(rows)["timeline"]]
    assert months == sorted(months)
    assert months[0] == "2025-11" and months[-1] == "2026-05"


def test_timeline_crosses_the_year_boundary_without_a_gap():
    rows = [
        record(posted_at="2025-12-15T00:00:00+00:00", title="A", source_id="1"),
        record(posted_at="2026-01-15T00:00:00+00:00", title="B", source_id="2"),
    ]
    assert [entry["month"] for entry in build_insights(rows)["timeline"]] == [
        "2025-12",
        "2026-01",
    ]


def test_undated_postings_are_left_out_of_the_timeline():
    rows = [
        record(posted_at="2026-01-05T00:00:00+00:00", title="A", source_id="1"),
        record(posted_at=None, title="B", source_id="2"),
    ]
    insights = build_insights(rows)
    assert insights["timeline"] == [{"month": "2026-01", "count": 1}]
    assert insights["totals"]["unique_jobs"] == 2


def test_date_only_timestamps_are_accepted():
    insights = build_insights([record(posted_at="2026-04-09")])
    assert insights["timeline"] == [{"month": "2026-04", "count": 1}]


def test_one_misdated_posting_cannot_flood_the_timeline():
    """A 1970 date from a bad feed must not push the readable months off a chart."""
    rows = [
        record(posted_at="1970-01-01T00:00:00+00:00", title="A", source_id="1"),
        record(posted_at="2026-06-01T00:00:00+00:00", title="B", source_id="2"),
    ]
    timeline = build_insights(rows)["timeline"]
    assert len(timeline) == 120
    assert timeline[-1] == {"month": "2026-06", "count": 1}
    assert timeline[0]["month"] == "2016-07"


def test_date_span_reports_the_extremes():
    rows = [
        record(posted_at="2026-01-05T00:00:00+00:00", title="A", source_id="1"),
        record(posted_at="2026-07-30T00:00:00+00:00", title="B", source_id="2"),
        record(posted_at="2026-03-03T00:00:00+00:00", title="C", source_id="3"),
    ]
    span = build_insights(rows)["totals"]["date_span"]
    assert span["earliest"].startswith("2026-01-05")
    assert span["latest"].startswith("2026-07-30")


# --------------------------------------------------------------------------
# Shares.
# --------------------------------------------------------------------------


def test_discipline_share_is_out_of_jobs_that_carry_a_discipline():
    rows = [
        record(title="A", source_id="1", tags=("strength-conditioning", "sports-medicine")),
        record(title="B", source_id="2", tags=("strength-conditioning",)),
        record(title="C", source_id="3", tags=("military",)),
    ]
    by_discipline = {e["name"]: e for e in build_insights(rows)["by_discipline"]}
    assert by_discipline["strength-conditioning"] == {
        "name": "strength-conditioning",
        "count": 2,
        "share": 1.0,
        "median_salary": 90_000.0,
    }
    assert by_discipline["sports-medicine"]["share"] == 0.5


def test_every_share_is_a_fraction_between_zero_and_one():
    rows = [
        record(title=f"Coach {index}", source_id=str(index), tags=tags)
        for index, tags in enumerate(
            [
                ("strength-conditioning", "sof"),
                ("sports-medicine", "military"),
                ("nutrition", "military", "first-responder"),
                ("cognitive", "sof"),
            ]
        )
    ]
    insights = build_insights(rows)
    for section in ("by_discipline", "by_domain", "certifications"):
        for entry in insights[section]:
            assert 0.0 < entry["share"] <= 1.0


def test_single_valued_facet_shares_sum_to_one():
    """Each of these jobs has exactly one discipline, so the shares partition."""
    rows = [
        record(title="A", source_id="1", tags=("strength-conditioning",)),
        record(title="B", source_id="2", tags=("sports-medicine",)),
        record(title="C", source_id="3", tags=("nutrition",)),
        record(title="D", source_id="4", tags=("nutrition",)),
    ]
    shares = [entry["share"] for entry in build_insights(rows)["by_discipline"]]
    assert round(sum(shares), 6) == 1.0


def test_domain_entries_report_a_population_not_a_wage():
    rows = [record(title="A", source_id="1", tags=("sof",))]
    assert build_insights(rows)["by_domain"] == [{"name": "sof", "count": 1, "share": 1.0}]


def test_certification_share_is_out_of_jobs_that_list_any_certification():
    rows = [
        record(title="A", source_id="1", enrichment={"certifications": ["CSCS", "TSAC-F"]}),
        record(title="B", source_id="2", enrichment={"certifications": ["CSCS"]}),
        record(title="C", source_id="3", enrichment={"installation": "JBLM"}),
    ]
    certifications = {entry["name"]: entry for entry in build_insights(rows)["certifications"]}
    assert certifications["CSCS"] == {"name": "CSCS", "count": 2, "share": 1.0}
    assert certifications["TSAC-F"]["share"] == 0.5


def test_a_certification_repeated_within_one_posting_counts_once():
    rows = [record(enrichment={"certifications": ["CSCS", "cscs", "CSCS"]})]
    assert build_insights(rows)["certifications"] == [
        {"name": "CSCS", "count": 1, "share": 1.0}
    ]


def test_remote_share_is_out_of_all_unique_jobs():
    rows = [
        record(title="A", source_id="1", remote=True),
        record(title="B", source_id="2", remote=False),
        record(title="C", source_id="3", remote=False),
        record(title="D", source_id="4", remote=True),
    ]
    assert build_insights(rows)["remote"] == {"count": 2, "share": 0.5}


# --------------------------------------------------------------------------
# Ranking, trimming, and trends.
# --------------------------------------------------------------------------


def test_employers_are_ranked_by_count_then_name():
    rows = [
        record(employer="Alpha", title=f"Coach {n}", source_id=f"a{n}") for n in range(2)
    ]
    rows += [record(employer="Zulu", title=f"Coach {n}", source_id=f"z{n}") for n in range(3)]
    rows += [record(employer="Bravo", title="Coach 0", source_id="b0")]
    assert names(build_insights(rows)["by_employer"]) == ["Zulu", "Alpha", "Bravo"]


def test_employer_entries_carry_their_disciplines():
    rows = [
        record(employer="Alpha", title="A", source_id="1", tags=("strength-conditioning",)),
        record(employer="Alpha", title="B", source_id="2", tags=("nutrition",)),
    ]
    entry = build_insights(rows)["by_employer"][0]
    assert sorted(entry["disciplines"]) == ["nutrition", "strength-conditioning"]


def test_titles_are_grouped_case_insensitively():
    rows = [
        record(title="Athletic Trainer", employer="Alpha", source_id="1"),
        record(title="ATHLETIC TRAINER", employer="Bravo", source_id="2"),
    ]
    assert build_insights(rows)["top_titles"] == [{"title": "Athletic Trainer", "count": 2}]


def test_top_n_trims_the_long_tail_lists():
    rows = [record(employer=f"Employer {n}", title=f"Coach {n}", source_id=str(n)) for n in range(9)]
    insights = build_insights(rows, top_n=3)
    assert len(insights["by_employer"]) == 3
    assert len(insights["top_titles"]) == 3


def test_a_non_positive_top_n_means_no_limit():
    rows = [record(employer=f"Employer {n}", title=f"Coach {n}", source_id=str(n)) for n in range(9)]
    assert len(build_insights(rows, top_n=0)["by_employer"]) == 9


def test_the_timeline_is_never_trimmed_by_top_n():
    rows = [
        record(posted_at=f"2026-{month:02d}-01T00:00:00+00:00", title=f"C{month}", source_id=str(month))
        for month in range(1, 8)
    ]
    assert len(build_insights(rows, top_n=2)["timeline"]) == 7


def test_trends_compare_the_last_window_against_the_one_before_it():
    rows = [
        record(employer="Surge", title="A", source_id="1", posted_at="2026-05-01T00:00:00+00:00"),
        record(employer="Surge", title="B", source_id="2", posted_at="2026-06-01T00:00:00+00:00"),
        record(employer="Surge", title="C", source_id="3", posted_at="2026-06-30T00:00:00+00:00"),
        record(employer="Surge", title="D", source_id="4", posted_at="2026-02-01T00:00:00+00:00"),
        record(employer="Fading", title="E", source_id="5", posted_at="2026-02-15T00:00:00+00:00"),
    ]
    trends = build_insights(rows)["trends"]
    growing = trends["fastest_growing_employers"]
    assert growing[0] == {"name": "Surge", "recent": 3, "previous": 1, "change": 2}
    assert "Fading" not in names(growing)
    assert trends["window_days"] == 90


def test_emerging_certifications_are_the_ones_appearing_more_lately():
    recent = {"certifications": ["CISSN"]}
    old = {"certifications": ["CSCS"]}
    rows = [
        record(title="A", source_id="1", posted_at="2026-06-01T00:00:00+00:00", enrichment=recent),
        record(title="B", source_id="2", posted_at="2026-06-20T00:00:00+00:00", enrichment=recent),
        record(title="C", source_id="3", posted_at="2026-02-01T00:00:00+00:00", enrichment=old),
        record(title="D", source_id="4", posted_at="2026-02-10T00:00:00+00:00", enrichment=old),
    ]
    emerging = build_insights(rows)["trends"]["emerging_certifications"]
    assert emerging[0]["name"] == "CISSN"
    assert emerging[0]["change"] == 2
    assert "CSCS" not in names(emerging)


def test_trends_are_suppressed_on_a_corpus_too_small_to_have_one():
    """Two data points is a coin flip, not a trend."""
    rows = [
        record(title="A", source_id="1", posted_at="2026-06-01T00:00:00+00:00"),
        record(title="B", source_id="2", posted_at="2026-06-02T00:00:00+00:00"),
    ]
    trends = build_insights(rows)["trends"]
    assert trends["fastest_growing_employers"] == []
    assert trends["emerging_certifications"] == []
    assert trends["pivot"] is None


def test_trends_anchor_to_the_corpus_not_to_wall_clock_now():
    """A corpus from 2019 still has a most-recent quarter."""
    rows = [
        record(employer="Surge", title=f"C{n}", source_id=str(n), posted_at=f"2019-06-0{n}T00:00:00+00:00")
        for n in range(1, 5)
    ]
    trends = build_insights(rows)["trends"]
    assert trends["pivot"].startswith("2019-03")
    assert names(trends["fastest_growing_employers"]) == ["Surge"]


# --------------------------------------------------------------------------
# The terminal digest.
# --------------------------------------------------------------------------


def test_render_summary_reports_the_headline_numbers():
    rows = [record(source_id=str(n)) for n in range(4)]
    rows.append(record(title="Athletic Trainer", source_id="9"))
    text = render_summary(build_insights(rows))
    assert "5 postings" in text
    assert "2 unique jobs" in text
    assert "O2X Human Performance" in text
    assert "$90,000" in text


def test_render_summary_flags_the_re_post_gap():
    rows = [record(source_id=str(n)) for n in range(4)]
    assert "re-posts" in render_summary(build_insights(rows))


def test_render_summary_is_plain_ascii_with_no_emoji():
    rows = [record(source_id=str(n), title=f"Coach {n}") for n in range(6)]
    text = render_summary(build_insights(rows))
    assert text.isascii()
    assert all(ord(char) < 128 for char in text)


def test_render_summary_omits_sections_with_no_data():
    rows = [record(enrichment={})]
    text = render_summary(build_insights(rows))
    assert "CLEARANCES" not in text
    assert "CERTIFICATIONS" not in text
    assert "CORPUS" in text


def test_render_summary_draws_a_timeline():
    rows = [
        record(posted_at="2026-01-05T00:00:00+00:00", title="A", source_id="1"),
        record(posted_at="2026-02-05T00:00:00+00:00", title="B", source_id="2"),
    ]
    text = render_summary(build_insights(rows))
    assert "2026-01" in text and "2026-02" in text
    assert "#" in text


def test_render_summary_tolerates_a_partial_report():
    """It runs against whatever a caller hands it, including a stub."""
    text = render_summary({"totals": {"postings": 3, "unique_jobs": 3}})
    assert "3 postings" in text
    assert text.endswith("\n")


def test_render_summary_keeps_non_ascii_employer_names_intact():
    text = render_summary(build_insights([record(employer="Fuerza Aérea Performance")]))
    assert "Fuerza Aérea Performance" in text


# --------------------------------------------------------------------------
# The seam with enrich.py: this module reads what that one writes, and the
# period vocabulary in particular is a contract between them. Skipped rather
# than failed when enrich is absent, so this file stands on its own.
# --------------------------------------------------------------------------


def test_a_real_enriched_hourly_posting_annualizes_end_to_end():
    enrich_module = pytest.importorskip("tactical_jobs.enrich")

    posting = JobPosting(
        source="usajobs:fed",
        source_id="8827311",
        url="https://example.invalid/8827311",
        title="Tactical Strength and Conditioning Coach",
        employer="US Army H2F",
        location="Fort Campbell, KY 42223",
        description=(
            "CSCS and TSAC-F required. Secret clearance required. "
            "Salary $45.00 to $52.00 per hour. THOR3 team at Fort Campbell."
        ),
        compensation="$45.00 - $52.00 per hour",
    )
    posting.enrichment = enrich_module.enrich(posting).to_dict()

    insights = build_insights([posting.to_archive_dict()])
    # Midpoint of $45-$52 is $48.50; annualized that is $100,880 -- and the
    # unannualized answer would have been $48.50, which is the whole point.
    assert insights["salary"]["median"] == 100_880.0
    assert insights["totals"]["with_salary"] == 1
    assert names(insights["certifications"]) == ["CSCS", "TSAC-F"]
    assert insights["clearances"] == [{"name": "Secret", "count": 1}]
    assert insights["by_state"] == [{"code": "KY", "count": 1}]


# --------------------------------------------------------------------------
# Regressions found during adversarial review
# --------------------------------------------------------------------------

def _record(**overrides):
    """Minimal archive-shaped record; override just what a test cares about."""
    base = {
        "id": "a1",
        "fingerprint": "f1",
        "source": "test",
        "url": "https://example.invalid/1",
        "title": "Strength and Conditioning Coach",
        "employer": "USASOC",
        "location": "Fort Bragg, NC",
        "remote": False,
        "posted_at": "2026-05-01T00:00:00+00:00",
        "archived_at": "2026-05-01T00:00:00+00:00",
        "description": "THOR3 program.",
        "score": 20.0,
        "tags": ["sof"],
        "enrichment": {},
        "matched": {"domain": [], "discipline": [], "excluded_by": []},
    }
    base.update(overrides)
    return base


def test_preposition_in_an_allcaps_location_is_not_a_state():
    """Regression: 'REMOTE - US OR CANADA' parsed OR as Oregon.

    An all-caps location field makes every English preposition look like a
    state code, so position -- not just casing -- has to carry the weight.
    """
    insights = build_insights([_record(location="REMOTE - US OR CANADA")])
    codes = {entry["code"] for entry in insights["by_state"]}
    assert "OR" not in codes


def test_genuine_trailing_state_code_still_parses():
    """The fix above must not break the common case it sits next to."""
    insights = build_insights(
        [
            _record(location="Fort Bragg, NC"),
            _record(id="a2", fingerprint="f2", location="Coronado, CA 92118"),
            _record(id="a3", fingerprint="f3", location="Fort Carson CO USA"),
        ]
    )
    codes = {entry["code"] for entry in insights["by_state"]}
    assert {"NC", "CA", "CO"} <= codes


def test_string_false_is_not_treated_as_remote():
    """Regression: bare bool("false") is True, which would report the whole
    corpus as remote the moment any source wrote its booleans as text."""
    insights = build_insights(
        [
            _record(remote="false"),
            _record(id="a2", fingerprint="f2", remote="no"),
            _record(id="a3", fingerprint="f3", remote=""),
        ]
    )
    assert insights["remote"]["count"] == 0


def test_string_true_is_treated_as_remote():
    insights = build_insights([_record(remote="true")])
    assert insights["remote"]["count"] == 1


def test_non_list_corpus_is_an_empty_corpus_not_a_crash():
    """A caller holding None from a status file that failed to parse should
    get an empty report, not a TypeError out of a loop header."""
    for value in (None, {}, "not a corpus", 42):
        insights = build_insights(value)
        assert insights["totals"]["postings"] == 0


def test_discipline_and_domain_vocabularies_match_the_classifier():
    """Regression: the tag lists here had drifted from ``classify.py``.

    ``sport-science`` and ``training-pipeline`` were missing, and a missing slug
    does not merely omit a row -- it drops those jobs out of the *denominator*
    every share in that facet is taken over, silently inflating every other
    number. Driving ``_derive_tags`` with the classifier's full term vocabulary
    yields every tag it can ever emit, which is the only honest way to assert
    the two modules still agree.
    """
    from tactical_jobs import classify

    posting = JobPosting(
        source="s",
        source_id="1",
        url="https://example.invalid/1",
        title="t",
        employer="e",
        location="l",
        description="d",
    )
    emitted = set(
        classify._derive_tags(
            list(classify.DOMAIN_TERMS), list(classify.DISCIPLINE_TERMS), posting
        )
    )
    # "remote" is a work arrangement, not a facet; it has its own section.
    assert emitted - {"remote"} == set(DISCIPLINE_TAGS) | set(DOMAIN_TAGS)


def test_sport_science_jobs_are_counted_and_dilute_the_discipline_shares():
    rows = [
        record(title="A", source_id="1", tags=("sport-science",)),
        record(title="B", source_id="2", tags=("strength-conditioning",)),
    ]
    by_discipline = {e["name"]: e for e in build_insights(rows)["by_discipline"]}
    assert by_discipline["sport-science"]["count"] == 1
    # The bug: with sport-science absent from the vocabulary, strength
    # conditioning was 1-of-1 and reported a 100% share of the field.
    assert by_discipline["strength-conditioning"]["share"] == 0.5


def test_training_pipeline_jobs_are_counted_as_a_population():
    rows = [record(title="A", source_id="1", tags=("training-pipeline",))]
    assert build_insights(rows)["by_domain"] == [
        {"name": "training-pipeline", "count": 1, "share": 1.0}
    ]


def test_sport_science_gets_its_own_salary_breakout():
    rows = [salaried(88_000, tags=("sport-science",))]
    assert build_insights(rows)["salary"]["by_discipline"]["sport-science"]["count"] == 1


# --------------------------------------------------------------------------
# Period labels that contain other period labels.
# --------------------------------------------------------------------------


def test_biweekly_is_twenty_six_periods_not_fifty_two():
    """Regression: "bi-weekly" contains "weekly", and a left-to-right scan for
    the first recognizable word doubled every biweekly figure."""
    assert annualized_salary({"salary_min": 4_000, "salary_period": "bi-weekly"}) == 104_000.0
    assert annualized_salary({"salary_min": 4_000, "salary_period": "Bi-Weekly"}) == 104_000.0
    # The term it contains still has to read correctly on its own.
    assert annualized_salary({"salary_min": 2_000, "salary_period": "weekly"}) == 104_000.0


def test_semimonthly_is_twenty_four_periods_not_twelve():
    assert annualized_salary({"salary_min": 4_000, "salary_period": "semi-monthly"}) == 96_000.0
    assert annualized_salary({"salary_min": 8_000, "salary_period": "monthly"}) == 96_000.0


def test_a_period_naming_both_salary_and_hour_is_hourly():
    """Regression: "salary per hour" hit the generic "salary" first and read a
    $50 wage as a $50 annual salary, which then vanished as an artifact."""
    assert annualized_salary({"salary_min": 50, "salary_period": "salary per hour"}) == 104_000.0
    assert annualized_salary({"salary_min": 104_000, "salary_period": "salary"}) == 104_000.0


def test_plural_and_latinate_period_spellings_are_understood():
    assert annualized_salary({"salary_min": 50, "salary_period": "hours"}) == 104_000.0
    assert annualized_salary({"salary_min": 50, "salary_period": "USD / hr"}) == 104_000.0
    assert annualized_salary({"salary_min": 104_000, "salary_period": "per annum"}) == 104_000.0


# --------------------------------------------------------------------------
# Dates that cannot be moved into UTC.
# --------------------------------------------------------------------------


def test_an_extreme_dated_offset_does_not_take_down_the_run():
    """Regression: shifting a year-1 or year-9999 stamp to UTC raises
    OverflowError -- not ValueError -- and it escaped the parser entirely."""
    rows = [
        record(title="A", source_id="1", posted_at="0001-01-01T00:00:00+05:00"),
        record(title="B", source_id="2", posted_at="9999-12-31T23:59:59-05:00"),
        record(title="C", source_id="3", posted_at="2026-05-01T00:00:00+00:00"),
    ]
    insights = build_insights(rows)
    assert insights["totals"]["unique_jobs"] == 3
    # The two unusable dates drop out; the readable one still anchors the span.
    assert insights["timeline"] == [{"month": "2026-05", "count": 1}]
    assert insights["totals"]["date_span"]["earliest"].startswith("2026-05")


def test_an_extreme_archived_at_does_not_take_down_the_run():
    row = record(archived_at="0001-01-01T00:00:00+05:00")
    assert build_insights([row])["totals"]["unique_jobs"] == 1


# --------------------------------------------------------------------------
# State parsing: which segment the name is read out of.
# --------------------------------------------------------------------------


def test_the_trailing_segment_wins_over_a_longer_name_earlier_in_the_string():
    """Regression: longest-name-first across the whole string read "New York
    Life, Dallas, Texas" as New York, because "new york" is the longer token."""
    assert state_code("New York Life, Dallas, Texas") == "TX"
    assert state_code("Indiana Avenue, Chicago, Illinois") == "IL"
    assert state_code("Nevada, Iowa") == "IA"


def test_longest_name_still_wins_inside_one_segment():
    assert state_code("Morgantown, West Virginia") == "WV"
    assert state_code("Camp Lejeune, North Carolina, United States") == "NC"


def test_a_code_followed_only_by_a_country_or_zip_is_a_state():
    assert state_code("Fort Bragg NC USA") == "NC"
    assert state_code("Fort Carson CO 80913") == "CO"


def test_a_two_letter_code_leading_a_company_name_is_not_a_state():
    """"CA Fitness Center" is a business, not California."""
    assert state_code("CA Fitness Center") is None


# --------------------------------------------------------------------------
# Credential labels and the trend join.
# --------------------------------------------------------------------------


def test_canonical_credential_spelling_survives_the_report():
    """Regression: certifications were upper-cased, printing "PHD" for PhD."""
    rows = [record(enrichment={"certifications": ["PhD", "NSCA-CPT", "phd"]})]
    assert names(build_insights(rows)["certifications"]) == ["NSCA-CPT", "PhD"]


def test_a_case_variant_employer_is_not_reported_as_growing():
    """Regression: the two trend windows were joined on the spelling ``_tally``
    displayed, so a board that changed its capitalization between quarters was
    reported as the fastest-growing employer on completely flat headcount."""
    rows = [
        record(employer="US Army H2F", title="A", source_id="1", posted_at="2026-06-01T00:00:00+00:00"),
        record(employer="US Army H2F", title="B", source_id="2", posted_at="2026-06-02T00:00:00+00:00"),
        record(employer="US ARMY H2F", title="C", source_id="3", posted_at="2026-02-01T00:00:00+00:00"),
        record(employer="US ARMY H2F", title="D", source_id="4", posted_at="2026-02-02T00:00:00+00:00"),
    ]
    assert build_insights(rows)["trends"]["fastest_growing_employers"] == []


def test_a_case_variant_credential_is_not_reported_as_emerging():
    rows = [
        record(title="A", source_id="1", posted_at="2026-06-01T00:00:00+00:00",
               enrichment={"certifications": ["CSCS"]}),
        record(title="B", source_id="2", posted_at="2026-06-02T00:00:00+00:00",
               enrichment={"certifications": ["CSCS"]}),
        record(title="C", source_id="3", posted_at="2026-02-01T00:00:00+00:00",
               enrichment={"certifications": ["cscs"]}),
        record(title="D", source_id="4", posted_at="2026-02-02T00:00:00+00:00",
               enrichment={"certifications": ["cscs"]}),
    ]
    assert build_insights(rows)["trends"]["emerging_certifications"] == []


def test_genuine_employer_growth_still_registers_after_the_case_fix():
    """The join fix must not suppress the signal it was protecting."""
    rows = [
        record(employer="Surge", title="A", source_id="1", posted_at="2026-06-01T00:00:00+00:00"),
        record(employer="Surge", title="B", source_id="2", posted_at="2026-06-02T00:00:00+00:00"),
        record(employer="SURGE", title="C", source_id="3", posted_at="2026-06-03T00:00:00+00:00"),
        record(employer="Surge", title="D", source_id="4", posted_at="2026-02-01T00:00:00+00:00"),
    ]
    growing = build_insights(rows)["trends"]["fastest_growing_employers"]
    assert growing[0]["recent"] == 3
    assert growing[0]["previous"] == 1
