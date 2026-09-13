"""Reading a fetched page: what links it offers, and what a document says.

Pure parsing, no network. The sweep's network half lives in ``sweep.py``; this
is everything that can be tested without pretending to be the internet.

Two jobs, deliberately separate. ``links`` reads a source's listing page and
says what it is pointing at — that is discovery, and it is allowed to be
generous. ``document`` reads a primary document and pulls out the title, the
date, and the text a blurb gets written from — that is evidence, and it is not
allowed to guess.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from html import unescape
from urllib.parse import urljoin

_ANCHOR = re.compile(r'<a\b[^>]*href=(["\'])(.*?)\1[^>]*>(.*?)</a>', re.I | re.S)
_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_H1 = re.compile(r"<h1[^>]*>(.*?)</h1>", re.I | re.S)
_META_DATE = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:article:published_time|citation_publication_date|'
    r'dc\.date|dcterms\.date|date|pubdate)["\'][^>]*content=["\']([^"\']+)["\']',
    re.I,
)
_TIME_TAG = re.compile(r'<time[^>]+datetime=["\']([^"\']+)["\']', re.I)
_STRIP = re.compile(r"<(script|style|nav|footer|header|noscript)[^>]*>.*?</\1>", re.I | re.S)
_MARKUP = re.compile(r"<[^>]+>")

_DATE_FORMATS = (
    "%Y-%m-%d",
    "%d %B %Y",
    "%d %b %Y",
    "%B %d, %Y",
    "%b %d, %Y",
    "%m/%d/%Y",
)

# Navigation, not content. A listing page is mostly chrome, and treating chrome
# as a finding is how a sweep fills a board with "Skip to main content".
_CHROME = (
    "skip to", "home", "contact", "about", "privacy", "accessibility", "sitemap",
    "search", "login", "log in", "sign in", "subscribe", "menu", "back to top",
    "share", "print", "download", "español", "foia", "no fear act",
)

# How much of a document a blurb gets written from. Enough for the lede and the
# first substantive paragraphs; not so much that a run carries whole PDFs.
EXCERPT_CHARS = 2400


@dataclass
class Link:
    """One outbound link from a source's listing page."""

    url: str
    title: str


@dataclass
class Document:
    """What a fetched primary document says about itself."""

    title: str = ""
    published: str = ""            # ISO date, or empty when the page does not say
    excerpt: str = ""              # the text a blurb is written from

    @property
    def is_readable(self) -> bool:
        """Whether there is enough here to write from.

        A page that returned 200 but yielded nothing — a JavaScript shell, a
        login wall, a PDF we cannot decode — must not become an item with an
        invented blurb. This is the check that keeps that from happening.
        """
        return bool(self.title.strip()) and len(self.excerpt.strip()) >= 200


def links(html: str, base_url: str) -> list[Link]:
    """Every content link on a listing page, resolved against `base_url`."""
    found: list[Link] = []
    seen: set[str] = set()
    for _, href, label in _ANCHOR.findall(html or ""):
        text = _text(label)
        if not text or len(text) < 15:
            continue                          # a link too short to be a headline
        if any(text.lower().startswith(word) or text.lower() == word for word in _CHROME):
            continue
        href = unescape(href.strip())
        if not href or href.startswith(("#", "mailto:", "javascript:", "tel:")):
            continue
        url = urljoin(base_url, href)
        if not url.startswith("https://"):
            continue                          # the sweep does not follow plain http
        if url in seen:
            continue
        seen.add(url)
        found.append(Link(url=url, title=text))
    return found


def document(html: str) -> Document:
    """Title, date and readable text from a fetched primary document."""
    body = _STRIP.sub(" ", html or "")

    title = ""
    heading = _H1.search(body)
    if heading:
        title = _text(heading.group(1))
    if not title:
        tag = _TITLE.search(html or "")
        if tag:
            title = _text(tag.group(1))

    published = ""
    for pattern in (_META_DATE, _TIME_TAG):
        found = pattern.search(html or "")
        if found:
            published = _iso(found.group(1))
            if published:
                break

    text = _text(_MARKUP.sub(" ", body))
    return Document(title=title, published=published, excerpt=text[:EXCERPT_CHARS])


def _text(value: str) -> str:
    return re.sub(r"\s+", " ", unescape(_MARKUP.sub(" ", value or ""))).strip()


def _iso(value: str) -> str:
    """An ISO date, or empty. Never a guess.

    An item with the wrong date lands in the wrong month and either misses the
    board or overstays on it, so a date we cannot read is left blank and the
    window rule sends the item to the archive.
    """
    raw = (value or "").strip()
    if not raw:
        return ""
    candidate = raw.split("T", 1)[0].strip()
    for fmt in _DATE_FORMATS:
        try:
            parsed = datetime.strptime(candidate, fmt).date()
        except ValueError:
            continue
        if date(1990, 1, 1) <= parsed <= date(2100, 1, 1):
            return parsed.isoformat()
    return ""
