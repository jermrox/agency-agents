"""Normalize any board feed into the one shape the site renders.

Handles both the legacy hand-curated sweep shape (rows of rank/validity/
title/employer/...) and the native pipeline shape (JobPosting.to_public_dict),
deriving facets and a confidence badge for either via the same enrich/facets
code the pipeline uses.

    python -m tactical_jobs feed --in jobs.json --out jobs.json
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .enrich import enrich
from .facets import facets_for
from .models import JobPosting

FEED_VERSION = 2

CONFIDENCE_DEFINITIONS: dict[str, str] = {
    "verified": (
        "We fetched this posting's own URL and the employer's system returned "
        "it as open, on the date shown."
    ),
    "listed": (
        "Taken from the employer's own careers system, but the link could not "
        "be re-checked automatically (some career sites block automated "
        "requests). Confirm before you invest time in an application."
    ),
    "aggregator": (
        "Found on a third-party job board and not confirmed against the "
        "employer. Treat as a lead: check the employer's own careers page "
        "before applying."
    ),
}

CONTINGENCY_DEFINITIONS: dict[str, str] = {
    "contingent": (
        "The posting says the role depends on the employer winning or funding "
        "a contract. These are real openings on paper, but the start date can "
        "slip by many months or never arrive."
    ),
    "funded": "The posting states the position is funded on an active contract.",
    "unknown": "The posting does not say either way.",
}

_LEGACY_VALIDITY = {
    "verified": "verified",
    "high": "listed",
    "high confidence": "listed",
    "aggregator": "aggregator",
}

_FIRST_PARTY_PREFIXES = (
    "workday", "greenhouse", "lever", "ashby", "workable", "smartrecruiters",
    "recruitee", "bamboohr", "breezy", "personio", "rippling", "icims",
    "taleo", "successfactors", "phenom", "jsonld", "governmentjobs", "usajobs",
)


def _stable_id(url: str, title: str) -> str:
    return hashlib.sha256(f"{url}\x00{title}".encode()).hexdigest()[:20]


def _is_legacy(row: dict[str, Any]) -> bool:
    return "validity" in row and "id" not in row


def confidence_of(row: dict[str, Any]) -> str:
    liveness = row.get("liveness") or {}
    if liveness.get("state") == "live":
        return "verified"

    if _is_legacy(row):
        return _LEGACY_VALIDITY.get(str(row.get("validity", "")).lower(), "aggregator")

    source = str(row.get("source", "")).lower()
    if source.startswith(_FIRST_PARTY_PREFIXES):
        return "listed"
    return "aggregator"


def _posting_from_legacy(row: dict[str, Any]) -> JobPosting:
    notes = str(row.get("notes") or "")
    salary = str(row.get("salary") or "")
    program = str(row.get("program") or "")
    description = "\n".join(part for part in (notes, salary, program) if part)
    url = str(row.get("url") or "")
    title = str(row.get("title") or "")
    return JobPosting(
        source="legacy",
        source_id=_stable_id(url, title),
        url=url,
        title=title,
        employer=str(row.get("employer") or ""),
        location=str(row.get("location") or ""),
        description=description,
        compensation=salary or None,
    )


def _posting_from_native(row: dict[str, Any]) -> JobPosting:
    return JobPosting(
        source=str(row.get("source") or ""),
        source_id=str(row.get("id") or ""),
        url=str(row.get("url") or ""),
        title=str(row.get("title") or ""),
        employer=str(row.get("employer") or ""),
        location=str(row.get("location") or ""),
        description=str(row.get("description") or ""),
        remote=bool(row.get("remote")),
        compensation=row.get("compensation"),
        enrichment=row.get("enrichment") or {},
    )


def normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    legacy = _is_legacy(row)
    posting = _posting_from_legacy(row) if legacy else _posting_from_native(row)

    if not posting.enrichment:
        try:
            enrich(posting)
        except Exception:  # pragma: no cover
            posting.enrichment = {}
    posting.facets = facets_for(posting)

    entry = posting.to_public_dict()
    entry["id"] = str(row.get("id") or posting.source_id)
    entry["confidence"] = confidence_of(row)
    entry["program"] = row.get("program") or posting.enrichment.get("program")
    entry["compensation"] = row.get("salary") or row.get("compensation")
    entry["notes"] = row.get("notes") or ""
    if isinstance(row.get("rank"), (int, float)) and not isinstance(row.get("rank"), bool):
        entry["rank"] = row["rank"]
    if row.get("liveness"):
        entry["liveness"] = row["liveness"]
    if row.get("listed_at"):
        entry["listed_at"] = row["listed_at"]
    return entry


def normalize_feed(payload: dict[str, Any]) -> dict[str, Any]:
    rows = payload.get("jobs") or []
    jobs = [normalize_row(row) for row in rows if isinstance(row, dict)]

    generated = (
        payload.get("generated_at")
        or payload.get("generated")
        or datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    out: dict[str, Any] = {
        "version": FEED_VERSION,
        "generated_at": generated,
        "count": len(jobs),
        "jobs": jobs,
        "definitions": {
            "confidence": CONFIDENCE_DEFINITIONS,
            "contingency": CONTINGENCY_DEFINITIONS,
        },
    }
    for key in ("live_feeds", "notes_on_closed"):
        if payload.get(key):
            out[key] = payload[key]
    return out


def normalize_file(source: Path, destination: Path) -> dict[str, Any]:
    payload = json.loads(Path(source).read_text())
    normalized = normalize_feed(payload)
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(normalized, indent=2) + "\n")
    return normalized
