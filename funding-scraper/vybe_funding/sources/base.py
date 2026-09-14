"""Source protocol and shared helpers.

A source takes a config block and yields Opportunity records. It never writes
files, never decides what is publishable, and never edits config -- the same
separation the jobs scraper holds, so a broken source degrades to "zero rows
from that source" instead of corrupting the run.
"""

from __future__ import annotations

import html
import re
from typing import Any, Iterable

from ..models import Opportunity

_TAGS = re.compile(r"<[^>]+>")
_WHITESPACE = re.compile(r"\s+")


def strip_html(value: Any) -> str:
    """Flatten an HTML blob to readable single-line text."""
    if not value:
        return ""
    text = _TAGS.sub(" ", str(value))
    return _WHITESPACE.sub(" ", html.unescape(text)).strip()


def first_key(record: dict[str, Any], keys: Iterable[str]) -> str:
    """Return the first non-empty value among ``keys``.

    The tolerant-field-picker pattern from the jobs scraper's contracts.py: an
    upstream rename costs one extra lookup instead of an empty board.
    """
    for key in keys:
        value = record.get(key)
        if value not in (None, "", []):
            return str(value).strip()
    return ""


class SourceError(RuntimeError):
    """A source that could not produce results."""


class Source:
    """Base class for every adapter."""

    kind = "base"

    def __init__(self, name: str, options: dict[str, Any]) -> None:
        self.name = name
        self.options = options

    def require(self, key: str) -> Any:
        """Read a required option, failing loudly when it is missing."""
        if key not in self.options:
            raise SourceError(f"source {self.name!r} ({self.kind}) requires option {key!r}")
        return self.options[key]

    def relevant(self, opportunity: Opportunity) -> bool:
        """Does this record match the source's ``require_any`` terms?

        Grants.gov treats a multi-word ``keyword`` as a loose OR, so
        "human performance physiological monitoring" returns crocodile
        population monitoring and wildland fire staffing alongside the real
        hits. Those outrank genuine matches in the closing-soon list purely by
        having a nearer deadline, which is how a funding board stops being read.

        A source with no ``require_any`` keeps everything, so this is opt-in and
        cannot silently empty a board.
        """
        terms = self.options.get("require_any") or []
        if not terms:
            return True
        haystack = f"{opportunity.name} {opportunity.summary}".lower()
        return any(str(term).lower() in haystack for term in terms)

    def fetch(self) -> Iterable[Opportunity]:  # pragma: no cover - interface
        raise NotImplementedError
