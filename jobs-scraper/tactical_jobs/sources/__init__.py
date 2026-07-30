"""Source registry: maps a config ``kind`` to an adapter class."""

from __future__ import annotations

from typing import Any

from .ats import ATS_SOURCES
from .base import Source, html_to_text, looks_remote, parse_timestamp
from .feeds import RSSSource
from .usajobs import USAJobsSource

_REGISTRY: dict[str, type[Source]] = {
    cls.kind: cls for cls in (*ATS_SOURCES, USAJobsSource, RSSSource)
}


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
