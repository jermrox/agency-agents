"""The standards panel watcher: the bot is the alarm, never the editor.

Section 6 is explicit — a person edits the table, and the bot's only job is to
watch each row's official page weekly and raise a flag when the page's date,
title, or effective date changes. Nothing here writes to ``standards.json``.
The snapshot it compares against is a separate file for exactly that reason.

The judgement call in here is what counts as a change worth waking someone for.
A raw content hash would flag almost every row almost every week: federal pages
carry rotating banners, visitor counters, and session tokens. A watcher that
cries wolf weekly is one the editor learns to ignore, which is worse than no
watcher at all. So a hash difference alone is recorded and not flagged; the
title and the dates on the page are what raise the flag.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

# Dates as official pages actually write them. Deliberately narrow: a looser
# pattern picks up version numbers and phone numbers and turns every week into
# a flag.
_DATE_PATTERNS = (
    re.compile(r"\b(\d{4}-\d{2}-\d{2})\b"),                               # 2026-01-01
    re.compile(r"\b(\d{1,2}\s+[A-Z][a-z]{2,8}\s+\d{4})\b"),               # 1 January 2026
    re.compile(r"\b([A-Z][a-z]{2,8}\s+\d{1,2},\s+\d{4})\b"),              # January 1, 2026
    re.compile(r"\b(\d{1,2}/\d{1,2}/\d{4})\b"),                           # 01/01/2026
)

_TITLE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_TAGS = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I | re.S)
_MARKUP = re.compile(r"<[^>]+>")


@dataclass
class Flag:
    """One reason an editor should look at a row."""

    row: str
    field: str
    before: str
    after: str

    def line(self) -> str:
        return f"{self.row}: {self.field} changed from {self.before or '(none)'} to {self.after or '(none)'}"


@dataclass
class Fingerprint:
    """What we remember about a watched page between sweeps."""

    title: str = ""
    dates: list[str] = field(default_factory=list)
    content_hash: str = ""

    def to_dict(self) -> dict:
        return {"title": self.title, "dates": self.dates, "content_hash": self.content_hash}

    @classmethod
    def from_dict(cls, data: dict) -> "Fingerprint":
        return cls(
            title=data.get("title", ""),
            dates=list(data.get("dates", [])),
            content_hash=data.get("content_hash", ""),
        )


def fingerprint(html: str) -> Fingerprint:
    """Reduce a page to the three things worth comparing week to week."""
    title = ""
    found = _TITLE.search(html or "")
    if found:
        title = _collapse(_MARKUP.sub(" ", found.group(1)))

    text = _MARKUP.sub(" ", _TAGS.sub(" ", html or ""))
    dates = sorted({_collapse(m) for pattern in _DATE_PATTERNS for m in pattern.findall(text)})

    return Fingerprint(
        title=title,
        dates=dates,
        content_hash=hashlib.sha256(_collapse(text).encode("utf-8")).hexdigest()[:16],
    )


def compare(row_name: str, before: Fingerprint | None, after: Fingerprint) -> list[Flag]:
    """Flags for one row. Empty means nothing an editor needs to see.

    A row with no previous fingerprint is not a change — it is a new row, and
    reporting it as changed would mean every added row arrives pre-flagged.
    """
    if before is None:
        return []

    flags: list[Flag] = []
    if before.title != after.title:
        flags.append(Flag(row_name, "title", before.title, after.title))

    gained = [d for d in after.dates if d not in before.dates]
    lost = [d for d in before.dates if d not in after.dates]
    if gained or lost:
        flags.append(Flag(row_name, "dates", ", ".join(before.dates), ", ".join(after.dates)))

    # A hash-only difference is not flagged on purpose: see the module docstring.
    return flags


def missing_flags(rows: list[dict], gone: dict[str, int]) -> list[Flag]:
    """Flags for rows whose page is gone.

    A row pointing at a 404 can never be watched again, so it is worth an
    editor's attention in its own right — silently watching nothing is the
    failure mode a green check hides. Only 404 and 410 count: a 403 is a bot
    filter refusing the robot, which says nothing about the standard.
    """
    return [
        Flag(row.get("name", row.get("url", "")), "page", "reachable", f"HTTP {gone[row['url']]} — the page is gone")
        for row in rows
        if row.get("url") in gone
    ]


def sweep(rows: list[dict], pages: dict[str, str], snapshot: dict) -> tuple[list[Flag], dict]:
    """Compare every row against the snapshot. Returns (flags, next snapshot).

    ``pages`` maps URL to fetched HTML. A row whose page could not be fetched
    keeps its old fingerprint rather than being recorded as blank — otherwise a
    single outage rewrites the baseline and the real change that follows it
    goes unnoticed.
    """
    flags: list[Flag] = []
    updated = dict(snapshot)

    for row in rows:
        url = row.get("url", "")
        name = row.get("name", url)
        if not url:
            continue                      # a row with no page cannot be watched
        html = pages.get(url)
        if html is None:
            continue                      # fetch failed: keep the old baseline

        after = fingerprint(html)
        raw_before = snapshot.get(url)
        before = Fingerprint.from_dict(raw_before) if raw_before else None

        flags.extend(compare(name, before, after))
        updated[url] = after.to_dict()

    return flags, updated


def report(flags: list[Flag]) -> str:
    """What the editor reads. Plain, and silent when there is nothing to say."""
    if not flags:
        return "No watched standards page changed its title or dates this week."
    lines = [f"{len(flags)} standards page(s) changed — check the panel:", ""]
    lines.extend(f"- {flag.line()}" for flag in flags)
    lines.append("")
    lines.append("The bot does not edit the table. These are for a person to verify.")
    return "\n".join(lines)


def _collapse(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()
