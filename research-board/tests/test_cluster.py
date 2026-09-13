"""Clustering: the document is the item, never the coverage.

The brief calls this the hardest part of the build and the one that decides
whether the board is trusted, so the cases here are the failure modes rather
than the happy path: coverage outnumbering the document, the same document
arriving by different URLs, and an article about a document nobody fetched.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tactical_research.cluster import Sighting, cluster  # noqa: E402


def _by_key(items):
    return {item.key: item for item in items}


class TestTheBriefsExample:
    """'The recent DoWI 1308.03 update produced articles across dozens of outlets.'"""

    def setup_method(self):
        self.sightings = [
            Sighting(
                title="DoWI 1308.03, DoD Physical Fitness and Body Composition Program",
                url="https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/130803p.pdf",
                published="2026-09-01",
            ),
            Sighting(
                title="Pentagon overhauls fitness rules",
                url="https://taskandpurpose.com/news/pentagon-fitness",
                text="The update to DoWI 1308.03 takes effect next year.",
                published="2026-09-02",
            ),
            Sighting(
                title="What the new DoD fitness instruction means",
                url="https://www.militarytimes.com/story",
                text="DoDI 1308.03 was reissued.",
                published="2026-09-02",
            ),
            Sighting(
                title="New fitness standards explained",
                url="https://www.firerescue1.com/fitness/story",
                text="the DoWI 1308.03 change",
                published="2026-09-03",
            ),
        ]

    def test_one_item_not_four(self):
        assert len(cluster(self.sightings)) == 1

    def test_the_item_is_the_issuance(self):
        item = cluster(self.sightings)[0]
        assert item.identifier.key == "dodi:1308.03"
        assert "esd.whs.mil" in item.primary_url

    def test_articles_become_coverage(self):
        item = cluster(self.sightings)[0]
        assert item.coverage_count == 3
        assert any("taskandpurpose" in u for u in item.coverage_urls)

    def test_headline_comes_from_the_document_not_the_loudest_outlet(self):
        assert cluster(self.sightings)[0].title.startswith("DoWI 1308.03")

    def test_order_does_not_matter(self):
        """Coverage arriving before the document must still attach to it."""
        reversed_items = cluster(list(reversed(self.sightings)))
        assert len(reversed_items) == 1
        assert reversed_items[0].coverage_count == 3


class TestNeverAnItemFromAnArticle:
    def test_coverage_of_an_unseen_document_is_dropped(self):
        """An article about a document we do not have is a lead, not an item."""
        items = cluster([
            Sighting(
                title="Army changes its fitness test",
                url="https://www.militarytimes.com/x",
                text="Army Directive 2026-07 does it",
            )
        ])
        assert items == []

    def test_coverage_with_no_identifier_at_all_is_dropped(self):
        items = cluster([Sighting(title="Fitness is important", url="https://blog.example.com/x")])
        assert items == []


class TestExceptions:
    def test_an_event_may_stand_on_coverage(self):
        """The brief's exception: events often have no underlying document."""
        items = cluster([
            Sighting(
                title="NSCA TSAC Conference 2027",
                url="https://www.nsca.com/tsac-conference",
                is_event=True,
            )
        ])
        assert len(items) == 1
        assert items[0].from_coverage is True

    def test_allowlisted_url_is_primary_without_an_identifier(self):
        """A program page on an official host is a document in its own right."""
        items = cluster([
            Sighting(title="CDMRP PRORP funding", url="https://cdmrp.health.mil/funding/prorp")
        ])
        assert len(items) == 1
        assert items[0].identifier is None


class TestSameDocumentDifferentUrls:
    def test_tracking_parameters_do_not_split_an_item(self):
        items = cluster([
            Sighting(title="PRORP", url="https://cdmrp.health.mil/funding/prorp?utm_source=x"),
            Sighting(title="PRORP", url="https://cdmrp.health.mil/funding/prorp"),
        ])
        assert len(items) == 1

    def test_fragment_and_trailing_slash_do_not_split_an_item(self):
        items = cluster([
            Sighting(title="PRORP", url="https://cdmrp.health.mil/funding/prorp/"),
            Sighting(title="PRORP", url="https://cdmrp.health.mil/funding/prorp#top"),
        ])
        assert len(items) == 1

    def test_same_issuance_from_two_hosts_is_one_item(self):
        items = cluster([
            Sighting(title="Army Directive 2026-07", url="https://armypubs.army.mil/a.pdf"),
            Sighting(title="Army Directive 2026-07 posted", url="https://api.army.mil/b.pdf"),
        ])
        assert len(items) == 1

    def test_earliest_publication_date_wins(self):
        items = cluster([
            Sighting(title="AD 2026-07", url="https://armypubs.army.mil/a.pdf", published="2026-09-05"),
            Sighting(title="AD 2026-07", url="https://armypubs.army.mil/a.pdf", published="2026-09-01"),
        ])
        assert items[0].published == "2026-09-01"


class TestDistinctDocumentsStaySeparate:
    def test_two_different_issuances(self):
        items = cluster([
            Sighting(title="DoWI 1308.03", url="https://www.esd.whs.mil/a.pdf"),
            Sighting(title="DoWI 1010.09", url="https://www.esd.whs.mil/b.pdf"),
        ])
        assert len(items) == 2

    def test_empty_input(self):
        assert cluster([]) == []
