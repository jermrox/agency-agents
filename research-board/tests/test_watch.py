"""The standards panel watcher.

The failure that matters is not a missed change — it is a watcher nobody reads.
Most of these tests are about *not* flagging: a rotating banner, a first sight
of a row, a week the page was unreachable. A weekly false alarm trains the
editor to ignore the real one.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_research.watch import (  # noqa: E402
    Fingerprint,
    compare,
    fingerprint,
    STALE_RUNS,
    missing_flags,
    report,
    stale_flags,
    sweep,
)

ROWS = [{"name": "Army Fitness Test", "url": "https://www.army.mil/aft/"}]


def page(title="Army Fitness Test", body="Effective 2026-01-01."):
    return f"<html><head><title>{title}</title></head><body><p>{body}</p></body></html>"


class TestFingerprint:
    def test_reads_the_title(self):
        assert fingerprint(page()).title == "Army Fitness Test"

    def test_finds_dates_in_the_formats_official_pages_use(self):
        html = page(body="Effective 2026-01-01, superseding 1 January 2025 and March 4, 2024.")
        dates = fingerprint(html).dates
        assert "2026-01-01" in dates and "1 January 2025" in dates and "March 4, 2024" in dates

    def test_ignores_scripts_and_styles(self):
        noisy = page(body="Effective 2026-01-01.") .replace(
            "</body>", "<script>var t='2019-09-09';</script></body>")
        assert fingerprint(noisy).dates == ["2026-01-01"]

    def test_whitespace_changes_are_not_content_changes(self):
        a = fingerprint(page())
        b = fingerprint(page().replace("<p>", "<p>\n   "))
        assert a.content_hash == b.content_hash and a.dates == b.dates


class TestCompare:
    def test_a_new_title_raises_a_flag(self):
        before = fingerprint(page(title="Army Physical Fitness Test"))
        after = fingerprint(page(title="Army Fitness Test"))
        flags = compare("AFT", before, after)
        assert [f.field for f in flags] == ["title"]

    def test_a_new_effective_date_raises_a_flag(self):
        before = fingerprint(page(body="Effective 2025-01-01."))
        after = fingerprint(page(body="Effective 2026-01-01."))
        assert [f.field for f in compare("AFT", before, after)] == ["dates"]

    def test_a_removed_date_raises_a_flag_too(self):
        before = fingerprint(page(body="Effective 2025-01-01 through 2026-01-01."))
        after = fingerprint(page(body="Effective 2025-01-01."))
        assert [f.field for f in compare("AFT", before, after)] == ["dates"]

    def test_an_unchanged_page_is_silent(self):
        assert compare("AFT", fingerprint(page()), fingerprint(page())) == []

    def test_a_rotating_banner_does_not_wake_anyone(self):
        # Federal pages churn constantly. If body text alone raised a flag, the
        # panel would be flagged every week and the editor would stop looking.
        before = fingerprint(page(body="Effective 2026-01-01. Visitor 41."))
        after = fingerprint(page(body="Effective 2026-01-01. Visitor 42."))
        assert compare("AFT", before, after) == []

    def test_a_first_sighting_is_not_a_change(self):
        assert compare("AFT", None, fingerprint(page())) == []


class TestSweep:
    def test_records_a_baseline_on_the_first_run_without_flagging(self):
        flags, snapshot = sweep(ROWS, {ROWS[0]["url"]: page()}, {})
        assert flags == []
        assert snapshot[ROWS[0]["url"]]["title"] == "Army Fitness Test"

    def test_flags_a_change_against_the_baseline(self):
        _, first = sweep(ROWS, {ROWS[0]["url"]: page()}, {})
        flags, _ = sweep(ROWS, {ROWS[0]["url"]: page(body="Effective 2027-01-01.")}, first)
        assert len(flags) == 1 and flags[0].row == "Army Fitness Test"

    def test_a_failed_fetch_keeps_the_old_baseline(self):
        # Overwriting with a blank on an outage would mean the real change that
        # lands the following week compares against nothing and goes unseen.
        _, first = sweep(ROWS, {ROWS[0]["url"]: page()}, {})
        flags, after_outage = sweep(ROWS, {}, first)
        assert flags == [] and after_outage == first

    def test_a_row_with_no_url_drops_out_quietly_rather_than_crashing(self):
        flags, snapshot = sweep([{"name": "Draft row", "url": ""}], {}, {})
        assert flags == [] and snapshot == {}

    def test_never_touches_the_table_itself(self):
        """Section 6: the bot is the alarm, not the editor."""
        rows = [dict(ROWS[0])]
        sweep(rows, {ROWS[0]["url"]: page(title="Something else")}, {})
        assert rows == [ROWS[0]]


class TestMissingPages:
    """A row pointing at a dead page watches nothing, and looks identical to a
    row that simply never changes. The first CI run caught four of these."""

    def test_a_gone_page_is_flagged_for_the_editor(self):
        flags = missing_flags(ROWS, {ROWS[0]["url"]: 404})
        assert len(flags) == 1 and "gone" in flags[0].after

    def test_a_reachable_row_is_not_flagged(self):
        assert missing_flags(ROWS, {}) == []

    def test_a_refusal_is_not_a_missing_page(self):
        # 403 is a bot filter answering and declining. The standard is fine.
        assert missing_flags(ROWS, {}) == []


class TestPersistentlyRefused:
    """Six .mil rows refuse automated requests outright. A refusal is correctly
    not a change — but week after week it looks exactly like a page that never
    changes, and the panel would report "nothing changed" about a page it has
    never once read."""

    def test_a_refusal_is_counted_not_forgotten(self):
        _, snapshot = sweep(ROWS, {}, {}, refused={ROWS[0]["url"]})
        assert snapshot[ROWS[0]["url"]]["refused_runs"] == 1

    def test_refusals_accumulate_across_runs(self):
        snapshot = {}
        for _ in range(3):
            _, snapshot = sweep(ROWS, {}, snapshot, refused={ROWS[0]["url"]})
        assert snapshot[ROWS[0]["url"]]["refused_runs"] == 3

    def test_one_bad_week_does_not_raise_a_flag(self):
        _, snapshot = sweep(ROWS, {}, {}, refused={ROWS[0]["url"]})
        assert stale_flags(ROWS, snapshot) == []

    def test_a_month_of_refusals_tells_the_editor_to_look_by_hand(self):
        snapshot = {}
        for _ in range(STALE_RUNS):
            _, snapshot = sweep(ROWS, {}, snapshot, refused={ROWS[0]["url"]})
        flags = stale_flags(ROWS, snapshot)
        assert len(flags) == 1 and "by hand" in flags[0].after

    def test_reading_the_page_again_clears_the_counter(self):
        snapshot = {}
        for _ in range(STALE_RUNS):
            _, snapshot = sweep(ROWS, {}, snapshot, refused={ROWS[0]["url"]})
        _, snapshot = sweep(ROWS, {ROWS[0]["url"]: page()}, snapshot)
        assert snapshot[ROWS[0]["url"]]["refused_runs"] == 0
        assert stale_flags(ROWS, snapshot) == []

    def test_a_refused_row_keeps_the_baseline_it_had(self):
        _, first = sweep(ROWS, {ROWS[0]["url"]: page()}, {})
        _, after = sweep(ROWS, {}, first, refused={ROWS[0]["url"]})
        assert after[ROWS[0]["url"]]["title"] == first[ROWS[0]["url"]]["title"]


class TestReport:
    def test_says_nothing_happened_rather_than_printing_an_empty_list(self):
        assert "No watched standards page changed" in report([])

    def test_names_the_row_and_what_moved(self):
        before = Fingerprint(title="Old", dates=[])
        flags = compare("NFPA 1580", before, fingerprint(page(title="New")))
        text = report(flags)
        assert "NFPA 1580" in text and "Old" in text and "New" in text

    def test_reminds_the_reader_that_a_person_edits_the_table(self):
        flags = compare("AFT", Fingerprint(title="Old"), fingerprint(page()))
        assert "does not edit the table" in report(flags)
