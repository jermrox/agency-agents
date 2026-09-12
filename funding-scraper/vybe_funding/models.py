"""Core data types for the funding sweep.

One opportunity moves through the pipeline as a single ``Opportunity``:
sources build it, ``status`` derives its open/closed state from the dates,
and the publisher renders it to JSON for the dashboard.

WHY STATUS IS DERIVED, NEVER STORED
The failure mode this whole project exists to prevent is a board full of
expired deadlines presented as live opportunities. A stored status goes stale
the moment the clock passes it; a derived one cannot. ``status`` is therefore
computed from ``close_date`` against the run date every time, and the JSON the
dashboard reads carries the date so the page can re-derive it client-side too.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Any

_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def slugify(text: str) -> str:
    return _SLUG_STRIP.sub("-", text.lower()).strip("-")


def parse_date(value: Any) -> date | None:
    """Best-effort date parsing across the formats these APIs actually emit.

    Grants.gov returns ``MM/DD/YYYY``. SBIR.gov returns ISO ``YYYY-MM-DD`` and
    sometimes a full timestamp. Curated TOML entries are ISO. Anything that
    does not parse returns None rather than raising: a missing close date makes
    an opportunity "rolling", which is a legitimate state, not an error.
    """
    if value in (None, "", "N/A"):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(text[: len(fmt) + 2].rstrip("Z"), fmt).date()
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        return None


@dataclass(slots=True)
class Opportunity:
    """One funding opportunity, normalized across every source."""

    source: str
    name: str
    url: str
    agency: str = ""
    amount: str = ""
    summary: str = ""
    open_date: date | None = None
    close_date: date | None = None
    pillar: int = 2
    kind: str = "grant"  # grant | credit | accelerator | partnership | visibility
    eligibility: str = ""
    documents: list[str] = field(default_factory=list)
    """What you must have in hand to apply.

    Kept separate from ``eligibility`` because they fail differently: an
    eligibility miss means don't bother, while a missing document means start
    now. Federal registrations (SAM.gov UEI, eRA Commons, SBC control number)
    take weeks to clear and gate every federal row on the board, so they belong
    here where the lead time is visible rather than buried in a solicitation.
    """
    raw: dict[str, Any] = field(default_factory=dict, repr=False)

    @property
    def id(self) -> str:
        """Stable identifier so the dashboard can keep per-row progress.

        Keyed on source + name rather than a vendor id, because the same
        program reappears under a new solicitation number every cycle and the
        user's "Applied" marker should survive that.
        """
        return f"{self.source}-{slugify(self.name)}"[:80]

    @property
    def fingerprint(self) -> str:
        return hashlib.sha256(f"{self.source}|{self.name}|{self.url}".encode()).hexdigest()[:16]

    def status(self, today: date) -> str:
        """open | soon | closed | rolling, derived fresh every run."""
        if self.close_date is None:
            return "rolling"
        days = (self.close_date - today).days
        if days < 0:
            return "closed"
        if days <= 30:
            return "soon"
        return "open"

    def days_left(self, today: date) -> int | None:
        if self.close_date is None:
            return None
        return (self.close_date - today).days

    def to_dict(self, today: date) -> dict[str, Any]:
        return {
            "id": self.id,
            "source": self.source,
            "name": self.name,
            "url": self.url,
            "agency": self.agency,
            "amount": self.amount,
            "summary": self.summary,
            "open_date": self.open_date.isoformat() if self.open_date else None,
            "close_date": self.close_date.isoformat() if self.close_date else None,
            "status": self.status(today),
            "days_left": self.days_left(today),
            "pillar": self.pillar,
            "kind": self.kind,
            "eligibility": self.eligibility,
            "documents": self.documents,
        }
