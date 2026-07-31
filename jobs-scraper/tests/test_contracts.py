"""Contract-award lead tests.

Two things have to hold for this module to be worth running. The mapping has to
survive the API renaming its own fields -- that is what the tolerant picker is
for, so it is tested against three genuinely different shapes of the same
payload. And the briefing has to stay short: a defense prime wins hundreds of
unrelated contracts, so an award with no human performance signal must be
rejected outright rather than ranked low.

No test here touches the network. ``post_json`` is monkeypatched as imported
into ``tactical_jobs.contracts`` and fed captured-shape payloads.
"""

from __future__ import annotations

import json
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_jobs.contracts import (  # noqa: E402
    AWARD_TYPE_CODES,
    CONTEXT_CAP,
    DEFAULT_KEYWORDS,
    REQUEST_FIELDS,
    USASPENDING_ENDPOINT,
    ContractAward,
    fetch_awards,
    flatten,
    normalize_key,
    parse_amount,
    pick_field,
    rank_recipients,
    render_leads,
    score_award,
    to_award,
)
from tactical_jobs.http import FetchError  # noqa: E402

# --------------------------------------------------------------------------
# The same award, in the three shapes this payload has been observed in.
# --------------------------------------------------------------------------

HUMAN_LABEL_RECORD = {
    "Award ID": "W911SF24F0123",
    "Recipient Name": "Tactical Performance Group LLC",
    "Award Amount": 18450000.0,
    "Description": "H2F HOLISTIC HEALTH AND FITNESS PERFORMANCE TEAM STAFFING - "
    "STRENGTH AND CONDITIONING COACHES, ATHLETIC TRAINERS, DIETITIANS",
    "Awarding Agency": "Department of Defense",
    "Awarding Sub Agency": "Department of the Army",
    "Start Date": "2026-03-01",
    "End Date": "2027-02-28",
    "Place of Performance State Code": "NC",
}

CAMEL_CASE_RECORD = {
    "awardId": "W911SF24F0123",
    "recipientName": "Tactical Performance Group LLC",
    "awardAmount": "$18,450,000.00",
    "description": HUMAN_LABEL_RECORD["Description"],
    "awardingAgency": "Department of Defense",
    "awardingSubAgency": "Department of the Army",
    "startDate": "2026-03-01",
    "endDate": "2027-02-28",
    "placeOfPerformanceStateCode": "NC",
}

# The underlying award record's own column names -- not a casing variant of the
# request labels but a different vocabulary for the same values.
COLUMN_NAME_RECORD = {
    "piid": "W911SF24F0123",
    "recipient_name": "Tactical Performance Group LLC",
    "total_obligation": 18450000,
    "prime_award_base_transaction_description": HUMAN_LABEL_RECORD["Description"],
    "awarding_toptier_agency_name": "Department of Defense",
    "awarding_subtier_agency_name": "Department of the Army",
    "period_of_performance_start_date": "2026-03-01T00:00:00Z",
    "period_of_performance_current_end_date": "2027-02-28",
    "pop_state_code": "NC",
}

NOISE_RECORD = {
    "Award ID": "N0018924D0007",
    "Recipient Name": "Generic Defense Integrators Inc",
    "Award Amount": 91000000.0,
    "Description": "BASE OPERATIONS SUPPORT SERVICES INCLUDING CUSTODIAL, "
    "GROUNDS MAINTENANCE AND IT REFRESH FOR ARMY INSTALLATION",
    "Awarding Agency": "Department of Defense",
    "Awarding Sub Agency": "Department of the Navy",
    "Start Date": "2026-01-15",
    "End Date": "2031-01-14",
    "Place of Performance State Code": "VA",
}


def page(records, *, has_next: bool = False) -> bytes:
    """A captured-shape response body, encoded the way the helper returns it."""
    return json.dumps(
        {"results": records, "page_metadata": {"page": 1, "hasNext": has_next}}
    ).encode()


class FakePost:
    """Stands in for ``http.post_json``: records bodies, replays pages."""

    def __init__(self, *pages, error_on_page: int | None = None):
        self.pages = list(pages)
        self.error_on_page = error_on_page
        self.calls: list[dict] = []

    def __call__(self, url, payload, **kwargs):
        self.calls.append(payload)
        if self.error_on_page is not None and len(self.calls) == self.error_on_page:
            raise FetchError("boom")
        index = len(self.calls) - 1
        if index >= len(self.pages):
            return page([])
        return self.pages[index]


def install(monkeypatch, fake) -> FakePost:
    monkeypatch.setattr("tactical_jobs.contracts.post_json", fake)
    return fake


# --------------------------------------------------------------------------
# Tolerant field picker
# --------------------------------------------------------------------------


def test_normalize_key_folds_case_and_punctuation():
    assert normalize_key("Award ID") == normalize_key("award_id") == normalize_key("awardId")


def test_maps_human_label_shape():
    award = to_award(HUMAN_LABEL_RECORD)
    assert award is not None
    assert award.award_id == "W911SF24F0123"
    assert award.recipient == "Tactical Performance Group LLC"
    assert award.amount == 18450000.0
    assert award.agency == "Department of Defense"
    assert award.sub_agency == "Department of the Army"
    assert award.start_date == "2026-03-01"
    assert award.end_date == "2027-02-28"
    assert award.state == "NC"


def test_maps_camel_case_shape_identically():
    assert to_award(CAMEL_CASE_RECORD).to_dict() == to_award(HUMAN_LABEL_RECORD).to_dict()


def test_maps_underlying_column_shape_identically():
    """Different names, not just different casing -- piid, total_obligation."""
    assert to_award(COLUMN_NAME_RECORD).to_dict() == to_award(HUMAN_LABEL_RECORD).to_dict()


def test_picker_returns_default_when_field_absent():
    assert pick_field({"Recipient Name": "x"}, "Award ID", default="none") == "none"


def test_picker_skips_present_but_empty_key():
    """A key that exists with an empty value must not shadow the next candidate."""
    record = {"Award ID": "", "piid": "W911-REAL"}
    assert pick_field(record, "Award ID", "piid") == "W911-REAL"


def test_flatten_reads_a_nested_agency_object():
    record = dict(HUMAN_LABEL_RECORD, **{"Awarding Agency": {"name": "Department of the Army"}})
    assert to_award(record).agency == "Department of the Army"
    assert flatten([{"name": "a"}, {"name": "b"}]) == "a, b"


def test_start_date_is_normalized_to_iso_day():
    """The column shape carries a full timestamp; the briefing prints a day."""
    assert to_award(COLUMN_NAME_RECORD).start_date == "2026-03-01"


# --------------------------------------------------------------------------
# Amount parsing
# --------------------------------------------------------------------------


def test_amount_from_number():
    assert parse_amount(18450000.0) == 18450000.0
    assert parse_amount(1234) == 1234.0


def test_amount_from_formatted_string():
    assert parse_amount("$18,450,000.00") == 18450000.0


def test_amount_from_none_is_none():
    assert parse_amount(None) is None
    assert to_award(dict(HUMAN_LABEL_RECORD, **{"Award Amount": None})).amount is None


def test_amount_from_unparseable_string_is_none():
    assert parse_amount("not published") is None
    assert parse_amount("") is None


def test_amount_rejects_bool():
    """bool is an int subclass; a flag is not a dollar figure."""
    assert parse_amount(True) is None


def test_amount_keeps_negative_deobligation():
    assert parse_amount("-$250,000") == -250000.0


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


def named_program() -> ContractAward:
    return ContractAward(
        recipient="A", description="H2F HOLISTIC HEALTH AND FITNESS PROGRAM SUPPORT"
    )


def generic_discipline() -> ContractAward:
    return ContractAward(recipient="B", description="ATHLETIC TRAINING SERVICES")


def test_named_program_far_outscores_a_generic_discipline():
    assert score_award(named_program()) > score_award(generic_discipline()) * 1.5


def test_thor3_and_potff_are_top_signals():
    thor3 = score_award(ContractAward(description="THOR3 HUMAN PERFORMANCE SUPPORT USASOC"))
    potff = score_award(
        ContractAward(description="POTFF PRESERVATION OF THE FORCE AND FAMILY SUPPORT")
    )
    assert thor3 > 5.0
    assert potff > 5.0


def test_award_with_no_human_performance_signal_is_rejected():
    assert score_award(to_award(NOISE_RECORD)) == 0.0


def test_population_words_alone_never_qualify_an_award():
    """This is the whole reason a prime's other 300 contracts stay out."""
    award = ContractAward(
        description="SOLDIER SUPPORT SERVICES FOR ARMY BRIGADE READINESS AND "
        "SPECIAL OPERATIONS INSTALLATION LOGISTICS"
    )
    assert score_award(award) == 0.0


def test_an_explicit_discipline_alone_is_still_a_lead():
    assert score_award(generic_discipline()) > 0.0


def test_context_bonus_is_capped():
    """A wall of population words cannot outrank a named program."""
    stacked = ContractAward(
        description="ATHLETIC TRAINING SERVICES FOR ARMY NAVY AIR FORCE MARINE CORPS "
        "SOLDIER AIRMAN WARFIGHTER BRIGADE BATTALION READINESS INSTALLATION "
        "SPECIAL OPERATIONS SOCOM USASOC MARSOC AFSOC LAW ENFORCEMENT FIREFIGHTER"
    )
    assert score_award(stacked) <= score_award(generic_discipline()) + CONTEXT_CAP
    assert score_award(stacked) < score_award(named_program())


def test_overlapping_terms_in_one_axis_count_once():
    """'athletic training services' must not also bank 'athletic training'."""
    assert score_award(ContractAward(description="ATHLETIC TRAINING SERVICES")) == score_award(
        ContractAward(description="AWARD FOR ATHLETIC TRAINING SERVICES ON SITE")
    )
    assert score_award(ContractAward(description="ATHLETIC TRAINING SERVICES")) == 4.0


def test_empty_description_scores_zero():
    assert score_award(ContractAward(recipient="A", description="")) == 0.0


def test_scoring_ignores_the_recipient_name():
    """An employer named 'Human Performance...' must not launder its other work."""
    award = ContractAward(
        recipient="Human Performance Solutions LLC",
        description="GROUNDS MAINTENANCE AND SNOW REMOVAL",
    )
    assert score_award(award) == 0.0


# --------------------------------------------------------------------------
# Record mapping edges
# --------------------------------------------------------------------------


def test_to_award_rejects_a_non_dict_record():
    assert to_award("W911SF24F0123") is None
    assert to_award(None) is None


def test_to_award_requires_a_recipient():
    """An award naming nobody answers none of the questions this module asks."""
    assert to_award({"Award ID": "X", "Description": "H2F SUPPORT"}) is None


def test_to_dict_carries_every_public_field():
    assert set(to_award(HUMAN_LABEL_RECORD).to_dict()) == {
        "award_id",
        "recipient",
        "amount",
        "description",
        "agency",
        "sub_agency",
        "start_date",
        "end_date",
        "state",
        "relevance",
    }


# --------------------------------------------------------------------------
# fetch_awards
# --------------------------------------------------------------------------


def test_fetch_maps_one_page(monkeypatch):
    install(monkeypatch, FakePost(page([HUMAN_LABEL_RECORD])))
    awards = fetch_awards()
    assert len(awards) == 1
    assert awards[0].recipient == "Tactical Performance Group LLC"
    assert awards[0].relevance > 0


def test_fetch_drops_no_signal_records(monkeypatch):
    install(monkeypatch, FakePost(page([HUMAN_LABEL_RECORD, NOISE_RECORD])))
    awards = fetch_awards()
    assert [award.award_id for award in awards] == ["W911SF24F0123"]


def test_fetch_follows_has_next(monkeypatch):
    second = dict(HUMAN_LABEL_RECORD, **{"Award ID": "W911SF25F0456"})
    fake = install(
        monkeypatch,
        FakePost(page([HUMAN_LABEL_RECORD], has_next=True), page([second], has_next=False)),
    )
    awards = fetch_awards()
    assert len(fake.calls) == 2
    assert [call["page"] for call in fake.calls] == [1, 2]
    assert len(awards) == 2


def test_fetch_stops_at_max_pages(monkeypatch):
    """A hasNext that is always true must not walk the whole corpus."""
    pages = [
        page([dict(HUMAN_LABEL_RECORD, **{"Award ID": f"W911-{i}"})], has_next=True)
        for i in range(10)
    ]
    fake = install(monkeypatch, FakePost(*pages))
    awards = fetch_awards(max_pages=3)
    assert len(fake.calls) == 3
    assert len(awards) == 3


def test_fetch_stops_when_has_next_is_false(monkeypatch):
    fake = install(monkeypatch, FakePost(page([HUMAN_LABEL_RECORD], has_next=False)))
    fetch_awards(max_pages=5)
    assert len(fake.calls) == 1


def test_fetch_on_empty_results_returns_empty(monkeypatch):
    install(monkeypatch, FakePost(page([])))
    assert fetch_awards() == []


def test_fetch_skips_malformed_records_and_keeps_the_rest(monkeypatch):
    install(
        monkeypatch,
        FakePost(page(["a bare string", None, 42, {"Description": "H2F"}, HUMAN_LABEL_RECORD])),
    )
    awards = fetch_awards()
    assert [award.award_id for award in awards] == ["W911SF24F0123"]


def test_fetch_dedupes_a_repeated_award_id(monkeypatch):
    install(
        monkeypatch,
        FakePost(
            page([HUMAN_LABEL_RECORD], has_next=True),
            page([CAMEL_CASE_RECORD], has_next=False),
        ),
    )
    assert len(fetch_awards()) == 1


def test_fetch_sends_the_documented_request_body(monkeypatch):
    fake = install(monkeypatch, FakePost(page([])))
    fetch_awards()
    body = fake.calls[0]
    assert body["filters"]["keywords"] == list(DEFAULT_KEYWORDS)
    assert body["filters"]["award_type_codes"] == list(AWARD_TYPE_CODES)
    assert body["fields"] == list(REQUEST_FIELDS)
    assert body["sort"] == "Award Amount"
    assert body["order"] == "desc"


def test_fetch_uses_custom_keywords(monkeypatch):
    fake = install(monkeypatch, FakePost(page([])))
    fetch_awards(keywords=["THOR3"])
    assert fake.calls[0]["filters"]["keywords"] == ["THOR3"]


def test_fetch_clamps_limit_to_the_api_maximum(monkeypatch):
    fake = install(monkeypatch, FakePost(page([])))
    fetch_awards(limit=5000)
    assert fake.calls[0]["limit"] == 100


def test_fetch_time_period_follows_since_days(monkeypatch):
    fake = install(monkeypatch, FakePost(page([])))
    fetch_awards(since_days=30)
    window = fake.calls[0]["filters"]["time_period"][0]
    assert window["end_date"] == date.today().isoformat()
    assert window["start_date"] == (date.today() - timedelta(days=30)).isoformat()


def test_fetch_posts_to_the_keyless_endpoint(monkeypatch):
    seen: list[str] = []

    def fake(url, payload, **kwargs):
        seen.append(url)
        assert "api_key" not in json.dumps(payload).lower()
        return page([])

    monkeypatch.setattr("tactical_jobs.contracts.post_json", fake)
    fetch_awards()
    assert seen == [USASPENDING_ENDPOINT]


def test_fetch_propagates_a_first_page_failure(monkeypatch):
    """A dead first page is a broken query, not a quiet quarter."""
    install(monkeypatch, FakePost(page([]), error_on_page=1))
    with pytest.raises(FetchError):
        fetch_awards()


def test_fetch_keeps_earlier_awards_when_a_later_page_fails(monkeypatch):
    install(
        monkeypatch,
        FakePost(page([HUMAN_LABEL_RECORD], has_next=True), error_on_page=2),
    )
    assert len(fetch_awards()) == 1


def test_fetch_accepts_an_already_decoded_payload(monkeypatch):
    install(monkeypatch, FakePost({"results": [HUMAN_LABEL_RECORD]}))
    assert len(fetch_awards()) == 1


def test_fetch_raises_on_a_non_json_body(monkeypatch):
    install(monkeypatch, FakePost(b"<html>gateway timeout</html>"))
    with pytest.raises(FetchError):
        fetch_awards()


def test_fetch_sorts_strongest_signal_first(monkeypatch):
    weak = dict(
        HUMAN_LABEL_RECORD,
        **{
            "Award ID": "W911-WEAK",
            "Description": "ATHLETIC TRAINING SERVICES",
            "Award Amount": 99000000.0,
        },
    )
    install(monkeypatch, FakePost(page([weak, HUMAN_LABEL_RECORD])))
    awards = fetch_awards()
    assert [award.award_id for award in awards] == ["W911SF24F0123", "W911-WEAK"]


# --------------------------------------------------------------------------
# rank_recipients
# --------------------------------------------------------------------------


def sample_awards() -> list[ContractAward]:
    return [
        ContractAward(
            award_id="A1",
            recipient="Tactical Performance Group LLC",
            amount=10_000_000.0,
            description="H2F PERFORMANCE TEAM",
            agency="Department of Defense",
            sub_agency="Department of the Army",
            start_date="2026-03-01",
            state="NC",
            relevance=9.0,
        ),
        ContractAward(
            award_id="A2",
            recipient="TACTICAL PERFORMANCE GROUP LLC",
            amount=5_000_000.0,
            description="THOR3 STRENGTH AND CONDITIONING",
            agency="Department of Defense",
            sub_agency="US Special Operations Command",
            start_date="2026-06-15",
            state="FL",
            relevance=12.0,
        ),
        ContractAward(
            award_id="B1",
            recipient="Small Coaching Co",
            amount=250_000.0,
            description="ATHLETIC TRAINING SERVICES",
            agency="Department of Defense",
            sub_agency="Department of the Navy",
            start_date="2026-02-01",
            state="VA",
            relevance=4.0,
        ),
    ]


def test_rank_aggregates_by_recipient():
    ranked = rank_recipients(sample_awards())
    top = ranked[0]
    assert top["recipient"] == "Tactical Performance Group LLC"
    assert top["awards"] == 2
    assert top["total_amount"] == 15_000_000.0
    assert top["agencies"] == [
        "Department of Defense / Department of the Army",
        "Department of Defense / US Special Operations Command",
    ]
    assert top["latest_award_date"] == "2026-06-15"
    assert top["states"] == ["FL", "NC"]
    assert top["award_ids"] == ["A1", "A2"]


def test_rank_merges_case_variants_of_one_recipient():
    ranked = rank_recipients(sample_awards())
    assert len(ranked) == 2
    assert ranked[0]["recipient"] == "Tactical Performance Group LLC"


def test_rank_orders_by_total_award_value():
    assert [entry["recipient"] for entry in rank_recipients(sample_awards())] == [
        "Tactical Performance Group LLC",
        "Small Coaching Co",
    ]


def test_rank_keeps_the_strongest_signal_per_recipient():
    top = rank_recipients(sample_awards())[0]
    assert top["top_relevance"] == 12.0
    assert "THOR3" in top["top_description"]


def test_rank_counts_awards_with_no_published_amount():
    awards = sample_awards()
    awards.append(
        ContractAward(recipient="Small Coaching Co", amount=None, description="H2F SUPPORT")
    )
    entry = next(e for e in rank_recipients(awards) if e["recipient"] == "Small Coaching Co")
    assert entry["awards"] == 2
    assert entry["awards_missing_amount"] == 1
    assert entry["total_amount"] == 250_000.0


def test_rank_respects_top_n():
    assert len(rank_recipients(sample_awards(), top_n=1)) == 1


def test_rank_of_nothing_is_nothing():
    assert rank_recipients([]) == []


def test_rank_skips_awards_with_no_recipient():
    assert rank_recipients([ContractAward(description="H2F SUPPORT")]) == []


# --------------------------------------------------------------------------
# render_leads
# --------------------------------------------------------------------------


def test_render_makes_the_next_step_obvious():
    text = render_leads(sample_awards())
    assert "Tactical Performance Group LLC" in text
    assert "$15,000,000" in text
    assert "Next step: find this employer's ATS board" in text
    assert "sources.toml" in text


def test_render_shows_agencies_and_counts():
    text = render_leads(sample_awards())
    assert "US Special Operations Command" in text
    assert "2 award(s)" in text


def test_render_on_empty_input_is_a_readable_briefing():
    text = render_leads([])
    assert "No relevant awards found" in text
    assert "since_days" in text
    assert text.endswith("\n")


def test_render_respects_top_n():
    text = render_leads(sample_awards(), top_n=1)
    assert "Tactical Performance Group LLC" in text
    assert "Small Coaching Co" not in text


def test_render_escapes_table_pipes():
    award = ContractAward(
        award_id="A1",
        recipient="Pipe | Co",
        amount=1000.0,
        description="H2F SUPPORT",
        relevance=6.0,
    )
    assert "Pipe \\| Co" in render_leads([award])


def test_render_labels_an_unpublished_amount():
    award = ContractAward(
        award_id="A1", recipient="Quiet Co", amount=None, description="H2F SUPPORT", relevance=6.0
    )
    text = render_leads([award])
    assert "not published" in text
