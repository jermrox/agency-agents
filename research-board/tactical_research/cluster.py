"""Collapse many sightings of one document into one item.

The rule from the brief, in one line: the document is the item, never the
coverage. A DoWI update produces articles across dozens of outlets; the board
shows one item, written from the issuance, with the articles underneath.

Clustering is by identifier first and canonical URL second. Coverage attaches to
the item it is about, and only becomes an item itself when nothing primary
exists — events and program announcements, per the brief's exception.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .identifiers import Identifier, is_fetchable, primary_identifier


@dataclass
class Sighting:
    """One thing the sweep saw: a document, or an article about one."""

    title: str
    url: str
    text: str = ""
    published: str = ""
    is_event: bool = False

    def identify(self) -> Identifier | None:
        """The identifier for this sighting, from its title, text, and URL."""
        return primary_identifier(" ".join((self.title, self.text, self.url)))


@dataclass
class Item:
    """One document, plus every article written about it."""

    key: str
    primary_url: str
    identifier: Identifier | None
    title: str
    published: str = ""
    coverage_urls: list[str] = field(default_factory=list)
    from_coverage: bool = False

    @property
    def coverage_count(self) -> int:
        return len(self.coverage_urls)


def _canonical_url(url: str) -> str:
    """Strip the noise that makes one URL look like several."""
    url = (url or "").split("#", 1)[0]
    if "?" in url:
        base, query = url.split("?", 1)
        keep = [
            part
            for part in query.split("&")
            # utm_* and friends identify the referrer, not the document.
            if part and not part.lower().startswith(("utm_", "fbclid", "gclid", "mc_cid", "mc_eid"))
        ]
        url = base + ("?" + "&".join(keep) if keep else "")
    return url.rstrip("/").lower()


def cluster(sightings: list[Sighting]) -> list[Item]:
    """Group `sightings` into items, one per document.

    A sighting on an allowlisted host is a primary document, keyed by its
    identifier when it has one and by its canonical URL when it does not.
    Everything else is coverage: it attaches to the item sharing its identifier,
    and is dropped otherwise — unless it is an event, which the brief allows to
    stand alone because events often have no underlying document.
    """
    items: dict[str, Item] = {}
    orphans: list[Sighting] = []

    # Primary documents first, so coverage always has something to attach to.
    # The HOST decides primacy, never the presence of an identifier: a trade
    # article quoting "DoWI 1308.03" is coverage of that issuance, not the
    # issuance. Reading it the other way lets the loudest outlet become the
    # item, which is the exact failure the brief is guarding against.
    for sighting in sightings:
        if not is_fetchable(sighting.url):
            orphans.append(sighting)
            continue
        ident = sighting.identify()
        key = ident.key if ident else "url:" + _canonical_url(sighting.url)
        existing = items.get(key)
        if existing is None:
            items[key] = Item(
                key=key,
                # Prefer the identifier's official host over whatever URL the
                # sighting came in on: the resolver knows where it really lives.
                primary_url=ident.url if ident else sighting.url,
                identifier=ident,
                title=sighting.title,
                published=sighting.published,
            )
        else:
            # Same document seen twice. Keep the earliest publication date and
            # the first title; a second sighting adds nothing but noise.
            if sighting.published and (not existing.published or sighting.published < existing.published):
                existing.published = sighting.published
            if not is_fetchable(existing.primary_url) and is_fetchable(sighting.url):
                existing.primary_url = sighting.url

    # Then coverage, onto the item it is about.
    for sighting in orphans:
        ident = primary_identifier(" ".join((sighting.title, sighting.text, sighting.url)))
        key = ident.key if ident else None
        if key and key in items:
            url = sighting.url
            if url not in items[key].coverage_urls:
                items[key].coverage_urls.append(url)
            continue
        if sighting.is_event:
            ckey = "url:" + _canonical_url(sighting.url)
            items.setdefault(
                ckey,
                Item(
                    key=ckey,
                    primary_url=sighting.url,
                    identifier=None,
                    title=sighting.title,
                    published=sighting.published,
                    from_coverage=True,
                ),
            )
        # Everything else is dropped: an article about a document we do not
        # have is not an item, it is a lead.

    return list(items.values())
