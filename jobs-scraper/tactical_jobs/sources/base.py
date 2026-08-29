"""Source adapter protocol plus shared parsing helpers."""

from __future__ import annotations

import html
import re
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from html.parser import HTMLParser
from typing import Any, Iterable

from ..models import JobPosting


class _TextExtractor(HTMLParser):
    """Flatten HTML to readable plain text.

    ATS descriptions are HTML blobs. The classifier only needs words, and the
    publishers only need a short excerpt, so a full HTML parser dependency
    would be overkill -- but naive tag-stripping glues words together across
    block boundaries ("...experience</li><li>CSCS..." -> "experienceCSCS"),
    which silently breaks phrase matching. Emitting a separator on block tags
    fixes that.
    """

    _BLOCK_TAGS = {
        "p", "div", "br", "li", "ul", "ol", "tr", "td", "th", "table",
        "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "header",
        "footer", "blockquote", "pre",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self._parts: list[str] = []
        self._suppress = 0

    def handle_starttag(self, tag: str, attrs: Any) -> None:
        if tag in {"script", "style"}:
            self._suppress += 1
        elif tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"script", "style"} and self._suppress:
            self._suppress -= 1
        elif tag in self._BLOCK_TAGS:
            self._parts.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._suppress:
            self._parts.append(data)

    def text(self) -> str:
        joined = "".join(self._parts)
        joined = re.sub(r"[ \t\r\f\v]+", " ", joined)
        joined = re.sub(r"\n\s*\n\s*", "\n\n", joined)
        return joined.strip()


def html_to_text(raw: str | None) -> str:
    """Convert an HTML (or already-plain) description to plain text."""
    if not raw:
        return ""
    unescaped = html.unescape(raw)
    if "<" not in unescaped:
        return re.sub(r"\s+", " ", unescaped).strip()
    parser = _TextExtractor()
    try:
        parser.feed(unescaped)
        parser.close()
    except Exception:  # pragma: no cover - malformed markup
        return re.sub(r"<[^>]+>", " ", unescaped)
    return parser.text()


def parse_timestamp(value: Any) -> datetime | None:
    """Best-effort timestamp parsing across the formats ATS vendors emit."""
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        # Vendors are inconsistent about seconds vs milliseconds; anything
        # past ~2286 in seconds is certainly milliseconds.
        seconds = value / 1000 if value > 10_000_000_000 else value
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if isinstance(value, str):
        text = value.strip()
        if text.endswith("Z"):
            text = f"{text[:-1]}+00:00"
        for candidate in (text, text.split("T")[0]):
            try:
                parsed = datetime.fromisoformat(candidate)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
        for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S %Z", "%Y/%m/%d"):
            try:
                parsed = datetime.strptime(text, fmt)
                return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


# "telework" is deliberately absent. In federal usage it means the postholder
# may be approved for OCCASIONAL work from home from a job that is otherwise
# on the installation -- measured across 25 live USAJOBS announcements it was
# true on 10 while the actual remote flag was true on none. Treating it as a
# synonym for remote put on-base jobs in front of people filtering for work
# from home. "telecommut" stays a hint elsewhere: that one really does mean
# the duty station is your home.
REMOTE_HINTS = ("remote", "work from home", "virtual", "anywhere")


def looks_remote(*fields: str | None) -> bool:
    blob = " ".join(f.lower() for f in fields if f)
    return any(hint in blob for hint in REMOTE_HINTS)


class Source(ABC):
    """Base class for every source adapter.

    Subclasses do exactly one thing: turn a remote endpoint into normalized
    :class:`JobPosting` objects. Filtering, scoring, dedupe, and publishing
    all happen downstream, so adapters stay small and testable.
    """

    kind: str = ""

    def __init__(self, name: str, options: dict[str, Any]) -> None:
        self.name = name
        self.options = options

    def require(self, key: str) -> Any:
        """Fetch a required option, failing with a useful message."""
        if key not in self.options:
            raise KeyError(f"source '{self.name}' ({self.kind}) requires option '{key}'")
        return self.options[key]

    @abstractmethod
    def fetch(self) -> Iterable[JobPosting]:
        """Yield every posting currently listed by this source."""
