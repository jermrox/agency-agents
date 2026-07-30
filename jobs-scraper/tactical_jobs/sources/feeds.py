"""Generic RSS/Atom adapter.

Escape hatch for employers that publish a jobs feed but run an ATS this
project has no dedicated adapter for. Feeds carry less structure than an ATS
API -- usually just title, link, and a description blob -- so postings from
here tend to score lower and land in the review queue. That is the correct
outcome rather than a bug.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from typing import Iterable

from ..http import fetch
from ..models import JobPosting
from .base import Source, html_to_text, looks_remote, parse_timestamp

_NAMESPACES = {
    "atom": "http://www.w3.org/2005/Atom",
    "content": "http://purl.org/rss/1.0/modules/content/",
    "dc": "http://purl.org/dc/elements/1.1/",
}


def _text(element: ET.Element | None) -> str:
    if element is None:
        return ""
    return "".join(element.itertext()).strip()


class RSSSource(Source):
    kind = "rss"

    def fetch(self) -> Iterable[JobPosting]:
        url = self.require("url")
        employer = self.options.get("employer", self.name)
        body = fetch(url)
        try:
            root = ET.fromstring(body)
        except ET.ParseError as exc:
            raise RuntimeError(f"{url} is not valid XML: {exc}") from exc

        items = root.findall(".//item")
        if items:
            yield from self._parse_rss(items, employer)
        else:
            yield from self._parse_atom(root.findall("atom:entry", _NAMESPACES), employer)

    def _parse_rss(self, items: list[ET.Element], employer: str) -> Iterable[JobPosting]:
        for item in items:
            link = _text(item.find("link"))
            title = _text(item.find("title"))
            description = html_to_text(
                _text(item.find("content:encoded", _NAMESPACES))
                or _text(item.find("description"))
            )
            guid = _text(item.find("guid")) or link
            if not (title and link):
                continue
            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=guid,
                url=link,
                title=title,
                employer=employer,
                location=self.options.get("location", ""),
                description=description,
                posted_at=parse_timestamp(
                    _text(item.find("pubDate")) or _text(item.find("dc:date", _NAMESPACES))
                ),
                remote=looks_remote(title, description),
                raw={"title": title, "link": link},
            )

    def _parse_atom(self, entries: list[ET.Element], employer: str) -> Iterable[JobPosting]:
        for entry in entries:
            link_el = entry.find("atom:link", _NAMESPACES)
            link = link_el.get("href", "") if link_el is not None else ""
            title = _text(entry.find("atom:title", _NAMESPACES))
            description = html_to_text(
                _text(entry.find("atom:content", _NAMESPACES))
                or _text(entry.find("atom:summary", _NAMESPACES))
            )
            if not (title and link):
                continue
            yield JobPosting(
                source=f"{self.kind}:{self.name}",
                source_id=_text(entry.find("atom:id", _NAMESPACES)) or link,
                url=link,
                title=title,
                employer=employer,
                location=self.options.get("location", ""),
                description=description,
                posted_at=parse_timestamp(
                    _text(entry.find("atom:updated", _NAMESPACES))
                    or _text(entry.find("atom:published", _NAMESPACES))
                ),
                remote=looks_remote(title, description),
                raw={"title": title, "link": link},
            )
