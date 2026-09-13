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

    def fetch(self) -> Iterable[Opportunity]:  # pragma: no cover - interface
        raise NotImplementedError
