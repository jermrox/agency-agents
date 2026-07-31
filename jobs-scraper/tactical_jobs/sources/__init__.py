"""Source registry: maps a config ``kind`` to an adapter class."""

from __future__ import annotations

from typing import Any

from .agencies import AGENCY_SOURCES
from .ats import ATS_SOURCES
from .ats_extra import ATS_EXTRA_SOURCES
from .base import Source, html_to_text, looks_remote, parse_timestamp
from .boards import BOARD_SOURCES
from .capture import CAPTURE_SOURCES
from .feeds import RSSSource
from .govjobs import GOV_SOURCES
from .jsonld import JSONLD_SOURCES
from .usajobs import USAJobsSource
from .workday import WORKDAY_SOURCES

_REGISTRY: dict[str, type[Source]] = {
    cls.kind: cls
    for cls in (
        *AGENCY_SOURCES,
        *ATS_SOURCES,
        *ATS_EXTRA_SOURCES,
        *BOARD_SOURCES,
        *CAPTURE_SOURCES,
        *GOV_SOURCES,
        *JSONLD_SOURCES,
        *WORKDAY_SOURCES,
        USAJobsSource,
        RSSSource,
    )
}

# Adapters that need a credential. Everything else runs on public board tokens
# or plain URLs, which matters a great deal: a deployment with no API keys at
# all still reaches the large majority of this market.
CREDENTIALED_KINDS: frozenset[str] = frozenset({"usajobs", "jazzhr", "teamtailor"})


def keyless_kinds() -> list[str]:
    """Adapters usable with no API key of any sort."""
    return sorted(set(_REGISTRY) - CREDENTIALED_KINDS)


def available_kinds() -> list[str]:
    return sorted(_REGISTRY)


def build_source(kind: str, name: str, options: dict[str, Any]) -> Source:
    """Instantiate the adapter registered for ``kind``."""
    try:
        cls = _REGISTRY[kind]
    except KeyError:
        raise KeyError(
            f"unknown source kind '{kind}'. Available: {', '.join(available_kinds())}"
        ) from None
    return cls(name=name, options=options)


__all__ = [
    "Source",
    "available_kinds",
    "build_source",
    "html_to_text",
    "looks_remote",
    "parse_timestamp",
]
