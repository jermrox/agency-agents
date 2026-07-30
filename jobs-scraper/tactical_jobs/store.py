"""Persistent memory of what has already been seen and published.

Without this, every scheduled run republishes the same jobs. The store is a
single JSON file so it can be committed back to the repo by the scheduled
workflow -- no database to operate, and the history is reviewable in a diff.

Two levels of identity are tracked:

* ``identity``  -- same posting, same source. Exact.
* ``fingerprint`` -- same employer + title + location across *different*
  sources. Catches an employer that syndicates one job to both its own ATS
  and USAJOBS.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterable

from .models import JobPosting

SCHEMA_VERSION = 1


@dataclass(slots=True)
class SeenRecord:
    identity: str
    fingerprint: str
    first_seen: str
    last_seen: str
    status: str
    title: str
    employer: str
    url: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "identity": self.identity,
            "fingerprint": self.fingerprint,
            "first_seen": self.first_seen,
            "last_seen": self.last_seen,
            "status": self.status,
            "title": self.title,
            "employer": self.employer,
            "url": self.url,
        }


@dataclass(slots=True)
class Store:
    path: Path
    records: dict[str, SeenRecord] = field(default_factory=dict)
    _fingerprints: dict[str, str] = field(default_factory=dict, repr=False)

    @classmethod
    def load(cls, path: str | Path) -> "Store":
        path = Path(path)
        store = cls(path=path)
        if not path.exists():
            return store
        try:
            data = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            # A corrupt state file must not wedge the pipeline. Starting
            # empty re-publishes at worst; crashing publishes nothing ever.
            return store
        for entry in data.get("records", []):
            record = SeenRecord(**entry)
            store.records[record.identity] = record
            store._fingerprints.setdefault(record.fingerprint, record.identity)
        return store

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": SCHEMA_VERSION,
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "records": [r.to_dict() for r in sorted(self.records.values(), key=lambda r: r.first_seen)],
        }
        # Write-then-rename so an interrupted run cannot truncate the state.
        temporary = self.path.with_suffix(".json.tmp")
        temporary.write_text(json.dumps(payload, indent=2, sort_keys=False) + "\n")
        temporary.replace(self.path)

    def is_new(self, posting: JobPosting) -> bool:
        if posting.identity in self.records:
            return False
        return posting.fingerprint not in self._fingerprints

    def mark(self, posting: JobPosting, status: str) -> None:
        """Record ``posting`` with ``status``, preserving its first-seen date."""
        now = datetime.now(timezone.utc).isoformat()
        existing = self.records.get(posting.identity)
        record = SeenRecord(
            identity=posting.identity,
            fingerprint=posting.fingerprint,
            first_seen=existing.first_seen if existing else now,
            last_seen=now,
            status=status,
            title=posting.title,
            employer=posting.employer,
            url=posting.url,
        )
        self.records[record.identity] = record
        self._fingerprints.setdefault(record.fingerprint, record.identity)

    def filter_new(self, postings: Iterable[JobPosting]) -> list[JobPosting]:
        """Return only postings not seen before, deduping within the batch too.

        A single run can surface the same job twice (two sources, one
        employer), so in-batch fingerprints are tracked alongside stored ones.
        """
        fresh: list[JobPosting] = []
        batch_identities: set[str] = set()
        batch_fingerprints: set[str] = set()
        for posting in postings:
            if posting.identity in batch_identities or posting.fingerprint in batch_fingerprints:
                continue
            if not self.is_new(posting):
                continue
            batch_identities.add(posting.identity)
            batch_fingerprints.add(posting.fingerprint)
            fresh.append(posting)
        return fresh

    def prune(self, max_age_days: int) -> int:
        """Drop records older than ``max_age_days``. Returns the count removed.

        Keeps the state file from growing without bound. The window must stay
        comfortably longer than a typical posting's life, or a job that ages
        out would be re-published as "new" while still listed.
        """
        if max_age_days <= 0:
            return 0
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_age_days)
        stale = []
        for identity, record in self.records.items():
            try:
                last_seen = datetime.fromisoformat(record.last_seen)
            except ValueError:
                continue
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=timezone.utc)
            if last_seen < cutoff:
                stale.append(identity)
        for identity in stale:
            record = self.records.pop(identity)
            if self._fingerprints.get(record.fingerprint) == identity:
                del self._fingerprints[record.fingerprint]
        return len(stale)
