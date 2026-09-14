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


def _word_match(term: str, haystack: str) -> bool:
    """Is ``term`` present in ``haystack`` as a whole word (or word prefix)?

    Trailing-stem terms like "agricultur" still match "agriculture" and
    "agricultural" -- the boundary is required at the start, not the end.
    """
    return re.search(rf"\b{re.escape(term)}", haystack) is not None


def strip_html(value: Any) -> str:
    """Flatten an HTML blob to readable single-line text."""
    if not value:
        return ""
    text = _TAGS.sub(" ", str(value))
    return _WHITESPACE.sub(" ", html.unescape(text)).strip()


def first_key(record: dict[str, Any], keys: Iterable[str]) -> str:
    """Return the first non-empty scalar value among ``keys``.

    The tolerant-field-picker pattern from the jobs scraper's contracts.py: an
    upstream rename costs one extra lookup instead of an empty board.

    Containers are skipped rather than stringified. grants.gov nests a whole
    object under "synopsis", and str()-ing it put a raw Python dict repr --
    "{'opportunityId': 362179, 'version': 1, ...}" -- into the summary of the
    row closing soonest on the board. A missing field is recoverable; a field
    full of machine noise is worse than empty.
    """
    for key in keys:
        value = record.get(key)
        if isinstance(value, (dict, list, tuple, set)):
            continue
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
        haystack = f"{opportunity.name} {opportunity.summary}".lower()

        # A blocklist runs first, because require_any is a broad OR: one generic
        # word is enough to admit a row. "readiness" let a forestry program onto
        # the board and "diagnos" let in a Ghana laboratory-strengthening
        # programme, both with empty summaries so the single title hit was the
        # whole case for them. Naming the domains Vybe does not work in is more
        # precise than trying to make every keyword unambiguous.
        #
        # Blocklist terms match on word boundaries, unlike require_any. A false
        # positive here silently deletes a real opportunity, so the cost is not
        # symmetric: bare substring matching had "crop" reject two
        # microphysiological-systems awards, and would have had "election"
        # reject anything mentioning patient selection.
        blocked = self.options.get("exclude_any") or []
        if any(_word_match(str(term).lower(), haystack) for term in blocked):
            return False

        terms = self.options.get("require_any") or []
        if not terms:
            return True
        return any(str(term).lower() in haystack for term in terms)

    def enrich(self, opportunity: Opportunity) -> None:
        """Fill in detail a search result does not carry. Default: nothing.

        Called only for rows that survived ``relevant``, so the request count
        tracks what reaches the board rather than what the search returned.
        """
        return None

    def fetch(self) -> Iterable[Opportunity]:  # pragma: no cover - interface
        raise NotImplementedError
