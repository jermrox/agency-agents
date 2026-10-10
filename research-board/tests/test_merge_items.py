"""Merging a sweep into findings.json: the document is the item, never twice."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from merge_items import merge  # noqa: E402
from tactical_research.models import BoardItem  # noqa: E402


def item(url="https://www.esd.whs.mil/x.pdf", **kw):
    base = dict(headline="H", blurb="B.", primary_url=url, date_published="2026-10-01",
                type="Policy", sector="MIL", tags=["Standards and tests"])
    base.update(kw)
    return BoardItem(**base)


def test_a_new_document_is_added():
    merged, added = merge([item()], [item(url="https://gao.gov/y")])
    assert added == 1 and len(merged) == 2


def test_the_same_url_in_another_spelling_is_not_a_second_item():
    merged, added = merge([item()], [item(url="http://esd.whs.mil/x.pdf/?utm_source=z")])
    assert added == 0 and len(merged) == 1


def test_a_shared_identifier_folds_coverage_into_the_existing_item():
    old = item(identifier="DOI 10.1/abc; PMID 1", coverage_urls=["https://a.com"])
    new = item(url="https://doi.org/10.1/abc", identifier="DOI 10.1/abc", coverage_urls=["https://b.com"])
    merged, added = merge([old], [new])
    assert added == 0 and merged[0].coverage_urls == ["https://a.com", "https://b.com"]


def test_a_better_write_up_replaces_the_old_one_but_keeps_its_first_seen():
    old = item(score=4, first_seen="2026-10-03")
    new = item(score=8, headline="Better", first_seen="2026-10-04")
    merged, _ = merge([old], [new])
    assert merged[0].headline == "Better" and merged[0].first_seen == "2026-10-03"


def test_coverage_additions_attach_to_their_document():
    merged, _ = merge([item()], [], [{"primary_url": "https://esd.whs.mil/x.pdf", "coverage_url": "https://c.com"}])
    assert merged[0].coverage_urls == ["https://c.com"]


def test_nothing_on_file_is_dropped():
    on_file = [item(url=f"https://a.mil/{n}") for n in range(5)]
    merged, _ = merge(on_file, [])
    assert len(merged) == 5
