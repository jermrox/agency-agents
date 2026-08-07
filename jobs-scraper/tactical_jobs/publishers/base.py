"""Publisher protocol.

A publisher is the only part of the system that causes an outward-facing
effect, so the interface is deliberately narrow: given the postings that
survived scoring and dedupe, do one thing with them.

``publish`` receives *approved* postings only. Anything routed to review is
handed to a review-queue publisher instead, never to a live sink.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Sequence

from ..models import JobPosting


class Publisher(ABC):
    kind: str = ""

    def __init__(self, options: dict[str, Any]) -> None:
        self.options = options

    def require(self, key: str) -> Any:
        if key not in self.options:
            raise KeyError(f"publisher '{self.kind}' requires option '{key}'")
        return self.options[key]

    @abstractmethod
    def publish(self, postings: Sequence[JobPosting]) -> str:
        """Emit ``postings``. Returns a one-line human summary for the run log."""

    def close(self) -> None:
        """Optional hook for publishers that batch or hold resources."""
