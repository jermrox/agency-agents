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
    MAX_WINDOW_DAYS,
    REQUEST_FIELDS,
    USASPENDING_ENDPOINT,
    ContractAward,
    build_request,
    fetch_awards,
    flatten,
    keyword_list,
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


def test_picker_returns_a_default_instead_of_raising_on_a_non_dict():
    """The resolver is handed whatever the API sent. None of it may raise."""
    for record in (None, "a bare string", 42, [1, 2, 3], True):
        assert pick_field(record, "Award ID", default="none") == "none"
    assert flatten(None) == ""
    assert flatten(object()) == ""
    assert flatten({"nested": {"deeper": {}}}) == ""


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


def test_an_empty_spelling_does_not_shadow_a_populated_one():
    """Both keys normalize to 'awardid'; the one with a value has to win.

    This is what a payload mid-rename looks like. First-occurrence-wins let the
    blank key claim the normalized slot and made the real value unreachable.
    """
    record = {"Award ID": "", "award_id": "W911SF24F0123"}
    assert pick_field(record, "Award ID") == "W911SF24F0123"


def test_an_empty_recipient_spelling_does_not_drop_the_whole_award():
    """Same collision on the recipient field cost the entire record."""
    record = {
        "Recipient Name": "",
        "recipient_name": "Tactical Performance Group LLC",
        "Description": "H2F PERFORMANCE TEAM STAFFING",
    }
    award = to_award(record)
    assert award is not None
    assert award.recipient == "Tactical Performance Group LLC"


def test_a_nested_recipient_object_still_yields_a_name():
    """A recipient block spells its display field 'recipient_name', not 'name'.

    Flattening it to "" dropped the award, silently, as if it did not exist.
    """
    record = {
        "recipient": {"recipient_name": "Tactical Performance Group LLC", "recipient_hash": "x"},
        "Description": "H2F PERFORMANCE TEAM STAFFING",
    }
    assert to_award(record).recipient == "Tactical Performance Group LLC"


def test_a_zero_value_is_kept_not_treated_as_missing():
    """A zero-dollar modification is a published figure, not an absent one."""
    award = to_award(dict(HUMAN_LABEL_RECORD, **{"Award Amount": 0}))
    assert award.amount == 0.0


def test_total_outlays_is_not_read_as_the_award_amount():
    """Outlays are money already paid, not the value of the award.

    Substituting one for the other silently reorders a briefing that ranks
    employers by dollars. 'not published' is the honest answer.
    """
    record = {
        "Recipient Name": "Tactical Performance Group LLC",
        "Description": "H2F PERFORMANCE TEAM STAFFING",
        "Total Outlays": 12345.0,
    }
    assert to_award(record).amount is None


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


def test_amount_reads_scientific_notation_as_written():
    """Deleting every non-digit turned "1.5e6" into 1.56 -- six orders of
    magnitude off, no error, in the one number the briefing ranks on."""
    assert parse_amount("1.5e6") == 1_500_000.0
    assert parse_amount("$1.845e7") == 18_450_000.0


def test_amount_refuses_a_string_with_two_numbers_in_it():
    """A range or a malformed figure is not a dollar value; do not guess one."""
    assert parse_amount("12.5.3") is None
    assert parse_amount("$100,000 - $250,000") is None
    assert parse_amount("W911SF24F0123") is None


def test_amount_refuses_a_parenthesised_figure():
    """Accounting notation for a negative. Reporting a deobligation as a
    quarter-million-dollar win is the expensive direction to be wrong in."""
    assert parse_amount("(250,000)") is None


def test_amount_tolerates_a_trailing_currency_word():
    assert parse_amount("18450000.00 USD") == 18450000.0


def test_amount_rejects_non_finite_numbers():
    assert parse_amount(float("inf")) is None
    assert parse_amount(float("nan")) is None


# --------------------------------------------------------------------------
# Scoring
# --------------------------------------------------------------------------


def named_program() -> ContractAward:
    return ContractAward(
        recipient="A", description="H2F HOLISTIC HEALTH AND FITNESS PROGRAM SUPPORT"
    )


def generic_discipline() -> ContractAward:
    return ContractAward(recipient="B", description="ATHLETIC TRAINING SERVICES")


def test_named_program_outscores_a_generic_discipline_by_a_clear_margin():
    """Rewritten: the old form asserted ``named > generic * 1.5`` and only held
    because "H2F HOLISTIC HEALTH AND FITNESS" banked the acronym and its own
    expansion as two separate 6-point signals. Once aliases collapse, a named
    program is worth 6.0 against a discipline's 4.0 -- still a clear ordering,
    but exactly 1.5x, so the multiplicative form was measuring the bug.
    """
    assert score_award(named_program()) > score_award(generic_discipline())
    assert score_award(named_program()) - score_award(generic_discipline()) >= 2.0


def test_an_acronym_and_its_expansion_score_once():
    """"H2F HOLISTIC HEALTH AND FITNESS" is a program named twice, not two."""
    spelled_out = score_award(ContractAward(description="HOLISTIC HEALTH AND FITNESS SUPPORT"))
    both = score_award(ContractAward(description="H2F HOLISTIC HEALTH AND FITNESS SUPPORT"))
    assert both == spelled_out
    # ... and so a wordier H2F award cannot leapfrog an equally strong THOR3 one.
    assert both == score_award(ContractAward(description="THOR3 SUPPORT"))


def test_potff_and_its_expansion_score_once():
    assert score_award(
        ContractAward(description="POTFF PRESERVATION OF THE FORCE AND FAMILY")
    ) == score_award(ContractAward(description="PRESERVATION OF THE FORCE AND FAMILY"))


def test_context_cannot_lift_a_bare_discipline_over_a_named_program():
    """The invariant CONTEXT_CAP exists for, asserted at the boundary.

    At the original cap of 3.0 this failed: 4.0 + 3.0 beat a clean 6.0 program.
    """
    stacked = ContractAward(
        description="ATHLETIC TRAINING SERVICES FOR ARMY SOLDIER BRIGADE READINESS "
        "SPECIAL OPERATIONS SOCOM WARFIGHTER INSTALLATION"
    )
    assert score_award(stacked) < score_award(
        ContractAward(description="HOLISTIC HEALTH AND FITNESS SUPPORT")
    )


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


def test_fetch_treats_a_bare_string_as_one_keyword(monkeypatch):
    """``list("THOR3")`` is ['T','H','O','R','3'] -- a query that returns tens
    of thousands of unrelated awards while looking like it worked."""
    fake = install(monkeypatch, FakePost(page([])))
    fetch_awards(keywords="THOR3")
    assert fake.calls[0]["filters"]["keywords"] == ["THOR3"]


def test_fetch_falls_back_to_defaults_on_empty_keywords(monkeypatch):
    """An empty keywords filter matches the entire federal contract corpus."""
    fake = install(monkeypatch, FakePost(page([])))
    fetch_awards(keywords=[])
    assert fake.calls[0]["filters"]["keywords"] == list(DEFAULT_KEYWORDS)
    fake2 = install(monkeypatch, FakePost(page([])))
    fetch_awards(keywords=["   ", ""])
    assert fake2.calls[0]["filters"]["keywords"] == list(DEFAULT_KEYWORDS)


def test_build_request_never_sends_an_empty_keyword_filter():
    assert build_request([], since_days=30, limit=10, page=1)["filters"]["keywords"] == list(
        DEFAULT_KEYWORDS
    )
    assert build_request("H2F", since_days=30, limit=10, page=1)["filters"]["keywords"] == ["H2F"]


def test_an_absurd_since_days_is_clamped_not_fatal(monkeypatch):
    """``date.today() - timedelta(days=10**8)`` raises OverflowError.

    A window from a config file or a CLI flag should widen the search, not end
    the run with a traceback.
    """
    fake = install(monkeypatch, FakePost(page([])))
    fetch_awards(since_days=10**8)
    window = fake.calls[0]["filters"]["time_period"][0]
    assert window["start_date"] == (date.today() - timedelta(days=MAX_WINDOW_DAYS)).isoformat()


def test_a_non_numeric_paging_argument_does_not_crash(monkeypatch):
    fake = install(monkeypatch, FakePost(page([]), page([])))
    fetch_awards(limit=None, max_pages=None, since_days=None)
    assert fake.calls[0]["limit"] == 100
    assert len(fake.calls) == 1


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


def test_fetch_sends_no_credential_of_any_kind(monkeypatch):
    """The operator has no key and cannot get one. Nothing may ask for one."""
    seen: list[tuple] = []

    def fake(url, payload, **kwargs):
        seen.append((url, payload, kwargs))
        return page([])

    monkeypatch.setattr("tactical_jobs.contracts.post_json", fake)
    fetch_awards()
    url, payload, kwargs = seen[0]
    blob = json.dumps([url, payload, kwargs], default=str).lower()
    for secret in ("api_key", "apikey", "authorization", "bearer", "token", "x-api", "oauth"):
        assert secret not in blob


def test_fetch_stops_when_page_metadata_is_missing_entirely(monkeypatch):
    """No metadata is not a licence to keep walking."""
    fake = install(monkeypatch, FakePost(json.dumps({"results": [HUMAN_LABEL_RECORD]}).encode()))
    fetch_awards(max_pages=5)
    assert len(fake.calls) == 1


def test_fetch_stops_on_a_string_has_next(monkeypatch):
    """Some payloads write their booleans as text; "false" is not true."""
    body = json.dumps(
        {"results": [HUMAN_LABEL_RECORD], "page_metadata": {"hasNext": "false"}}
    ).encode()
    fake = install(monkeypatch, FakePost(body))
    fetch_awards(max_pages=5)
    assert len(fake.calls) == 1


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


def test_rank_tolerates_an_amount_that_is_not_a_number():
    """These functions are public; an award replayed from an archive can carry
    "$5" in that slot, and ``float("$5")`` ended the whole briefing."""
    ranked = rank_recipients(
        [
            ContractAward(recipient="Odd Co", amount="$5", description="H2F SUPPORT"),
            ContractAward(recipient="Odd Co", amount="not published", description="H2F SUPPORT"),
        ]
    )
    assert ranked[0]["total_amount"] == 5.0
    assert ranked[0]["awards_missing_amount"] == 1


def test_rank_tolerates_a_relevance_that_is_not_a_number():
    ranked = rank_recipients(
        [ContractAward(recipient="Odd Co", description="H2F SUPPORT", relevance="high")]
    )
    assert ranked[0]["top_relevance"] == 0.0


def test_rank_keeps_a_free_text_date_when_it_is_the_only_one():
    """Printing 'not published' next to a date we were handed is a lie."""
    entry = rank_recipients(
        [ContractAward(recipient="Odd Co", description="H2F SUPPORT", start_date="March 2026")]
    )[0]
    assert entry["latest_award_date"] == "March 2026"


def test_rank_prefers_a_comparable_date_over_free_text():
    entry = rank_recipients(
        [
            ContractAward(recipient="Odd Co", description="H2F", start_date="March 2026"),
            ContractAward(recipient="Odd Co", description="H2F", start_date="2026-01-04"),
        ]
    )[0]
    assert entry["latest_award_date"] == "2026-01-04"


def test_keyword_list_coerces_what_callers_actually_pass():
    assert keyword_list("H2F") == ["H2F"]
    assert keyword_list(["H2F", " ", ""]) == ["H2F"]
    assert keyword_list(None) == list(DEFAULT_KEYWORDS)
    assert keyword_list([]) == list(DEFAULT_KEYWORDS)


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


def test_render_summary_counts_only_the_recipients_it_shows():
    """The summary line used to contradict itself under ``top_n``: it counted
    every award but totalled only the shown ones."""
    text = render_leads(sample_awards(), top_n=1)
    assert "**2 relevant award(s)** across **1 recipient(s)**" in text
    assert "$15,000,000" in text
    assert "$15,250,000" not in text


def test_render_lists_every_award_behind_a_shown_recipient():
    """``top_n`` counts recipients; slicing the award table with it hid rows
    the block above had already promised ("across 2 award(s)")."""
    text = render_leads(sample_awards(), top_n=1)
    assert "| A1 |" in text
    assert "| A2 |" in text
    assert "| B1 |" not in text


def test_render_survives_an_award_with_junk_in_every_slot():
    award = ContractAward(
        award_id="A1",
        recipient="Odd Co",
        amount="not published",
        description="H2F SUPPORT",
        relevance="high",
    )
    text = render_leads([award])
    assert "Odd Co" in text
    assert text.endswith("\n")


def test_render_survives_unicode_and_very_long_text():
    award = ContractAward(
        award_id="W911" + "0" * 400,
        recipient="Ünïcødé Performance Ω " + "x" * 300,
        amount=1000.0,
        description="H2F HOLISTIC HEALTH AND FITNESS " + "ü" * 4000,
        relevance=6.0,
    )
    text = render_leads([award])
    assert "Ünïcødé Performance Ω" in text
    # Table cells are truncated, so one absurd record cannot blow up a row.
    assert max(len(line) for line in text.splitlines()) < 600


def test_render_labels_an_unpublished_amount():
    award = ContractAward(
        award_id="A1", recipient="Quiet Co", amount=None, description="H2F SUPPORT", relevance=6.0
    )
    text = render_leads([award])
    assert "not published" in text
