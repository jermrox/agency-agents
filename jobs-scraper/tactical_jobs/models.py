"""Core data types shared by every stage of the pipeline.

A posting moves through the pipeline as a single ``JobPosting`` instance:
sources build it, the classifier annotates it, the store decides whether it
is new, and publishers render it. Nothing downstream of a source is allowed
to reach back into ``raw`` -- that field exists for debugging and for writing
richer source adapters later, and is deliberately never published.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# Collapses the punctuation/spacing noise that makes the same job look
# different across two ATS vendors ("Sr." vs "Senior", "  -  " vs " - ").
_FINGERPRINT_STRIP = re.compile(r"[^a-z0-9]+")
_ABBREVIATIONS = {
    "sr": "senior",
    "jr": "junior",
    "asst": "assistant",
    "assoc": "associate",
    "coord": "coordinator",
    "spec": "specialist",
    "mgr": "manager",
    "dir": "director",
    "s&c": "strength and conditioning",
}


def _canonical(text: str) -> str:
    """Lowercase, expand common abbreviations, strip everything else."""
    lowered = text.lower().replace("&", " and ")
    words = [_ABBREVIATIONS.get(w, w) for w in _FINGERPRINT_STRIP.split(lowered) if w]
    return " ".join(words)


@dataclass(slots=True)
class JobPosting:
    """One job, normalized across every source we support."""

    source: str
    """Adapter instance that produced this, e.g. ``greenhouse:o2x``."""

    source_id: str
    """Stable id within that source. Used for exact-match dedupe."""

    url: str
    title: str
    employer: str
    location: str = ""
    description: str = ""
    posted_at: datetime | None = None
    remote: bool = False
    department: str | None = None
    compensation: str | None = None
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    # Populated by classify.py.
    score: float = 0.0
    domain_hits: list[str] = field(default_factory=list)
    discipline_hits: list[str] = field(default_factory=list)
    exclusion_hits: list[str] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)

    # Populated by enrich.py: structured facts pulled out of the description
    # (certifications, clearance, salary, installation, branch, program...).
    # Kept as a plain dict so the analytics layer can consume archived JSON
    # and live postings through exactly the same shape.
    enrichment: dict[str, Any] = field(default_factory=dict)

    @property
    def identity(self) -> str:
        """Exact identity: the same posting re-fetched from the same source.

        Cheap and precise -- this is what catches the 99% case of a nightly
        run seeing yesterday's jobs again.
        """
        return hashlib.sha256(f"{self.source}\x00{self.source_id}".encode()).hexdigest()[:20]

    @property
    def fingerprint(self) -> str:
        """Fuzzy identity: the same job posted to two different boards.

        An employer that syndicates to both its Greenhouse board and USAJOBS
        produces two rows with different ``identity`` values but the same
        ``fingerprint``, so the store can suppress the duplicate.
        """
        basis = f"{_canonical(self.employer)}\x00{_canonical(self.title)}\x00{_canonical(self.location)}"
        return hashlib.sha256(basis.encode()).hexdigest()[:20]

    @property
    def posted_at_iso(self) -> str | None:
        if self.posted_at is None:
            return None
        stamp = self.posted_at
        if stamp.tzinfo is None:
            stamp = stamp.replace(tzinfo=timezone.utc)
        return stamp.astimezone(timezone.utc).isoformat()

    def to_archive_dict(self) -> dict[str, Any]:
        """Full-fidelity record for the archive.

        Unlike :meth:`to_public_dict` this keeps the **complete** description
        rather than an excerpt, because the analytics layer mines the full
        text for certifications, clearances, and salary language.
        """
        record = self.to_public_dict()
        record["description"] = self.description
        record["description_chars"] = len(self.description)
        record["source_id"] = self.source_id
        return record

    def to_public_dict(self) -> dict[str, Any]:
        """The shape that leaves the system. Excludes ``raw`` on purpose."""
        return {
            "id": self.identity,
            "fingerprint": self.fingerprint,
            "source": self.source,
            "url": self.url,
            "title": self.title,
            "employer": self.employer,
            "location": self.location,
            "remote": self.remote,
            "department": self.department,
            "compensation": self.compensation,
            "posted_at": self.posted_at_iso,
            "description": self.description,
            "score": round(self.score, 2),
            "tags": sorted(self.tags),
            "enrichment": self.enrichment,
            "matched": {
                "domain": sorted(set(self.domain_hits)),
                "discipline": sorted(set(self.discipline_hits)),
                "excluded_by": sorted(set(self.exclusion_hits)),
            },
        }


@dataclass(slots=True)
class SourceError:
    """A source that failed. Collected rather than raised.

    One dead career page must never take down a nightly run, so the pipeline
    accumulates these and reports them in the run summary instead.
    """

    source: str
    message: str

    def __str__(self) -> str:  # pragma: no cover - trivial
        return f"{self.source}: {self.message}"
