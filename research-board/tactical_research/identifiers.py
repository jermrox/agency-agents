"""Recognise the identifiers that make two items the same document.

The board's credibility rests on this module. When a DoWI is updated, dozens of
outlets write it up and most get the context wrong; the board has to show that
as one item, written from the issuance, with the articles collapsed underneath.
That only works if an identifier can be pulled out of messy text and resolved to
the one official host that serves it.

Each identifier normalises to a canonical string. Two items sharing a canonical
identifier are the same document no matter how their URLs or titles differ.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Every host the sweep is allowed to fetch a primary document from. Anything
# else is coverage, and coverage never becomes an item on its own.
FETCH_ALLOWLIST = (
    "esd.whs.mil",
    "armypubs.army.mil",
    "marines.mil",
    "mynavyhr.navy.mil",
    "af.mil",
    "spaceforce.mil",
    "health.mil",
    "media.defense.gov",
    "pubmed.ncbi.nlm.nih.gov",
    "pmc.ncbi.nlm.nih.gov",
    "doi.org",
    "nfpa.org",
    "osha.gov",
    "regulations.gov",
    "federalregister.gov",
    "gao.gov",
    "cdc.gov",
    "usfa.fema.gov",
    "fbi.gov",
    "bja.ojp.gov",
    "nij.ojp.gov",
)


@dataclass(frozen=True)
class Identifier:
    """A document identity: what kind, its canonical form, and where it lives."""

    kind: str
    value: str
    url: str

    @property
    def key(self) -> str:
        """The clustering key. Same key means same document."""
        return f"{self.kind}:{self.value}"


def _issuance(match: re.Match) -> str:
    return match.group(1).upper().replace(" ", "")


# Ordered: the more specific patterns first, so "DoDI 1308.03" is not also read
# as a bare number by a looser rule further down.
_PATTERNS: tuple[tuple[str, re.Pattern, object], ...] = (
    # DoD / Department of War issuances. The department was renamed, and both
    # spellings appear in the wild for the same document, so they normalise to
    # one key — otherwise a renamed reissue would split into two items.
    (
        "dodi",
        re.compile(r"\bDo[DW]I\s*([0-9]{4}\.[0-9]{2}[A-Z]?)\b", re.I),
        lambda m: f"https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodi/{m.group(1)}.pdf",
    ),
    (
        "dodd",
        re.compile(r"\bDo[DW]D\s*([0-9]{4}\.[0-9]{2}[A-Z]?)\b", re.I),
        lambda m: f"https://www.esd.whs.mil/Portals/54/Documents/DD/issuances/dodd/{m.group(1)}.pdf",
    ),
    # Army Directives and regulations.
    (
        "army-directive",
        re.compile(r"\bArmy\s+Directive\s+((?:19|20)[0-9]{2}-[0-9]{2})\b", re.I),
        lambda m: "https://armypubs.army.mil/ProductMaps/PubForm/Details.aspx?PUB_ID=" + m.group(1),
    ),
    (
        "army-reg",
        re.compile(r"\bAR\s+([0-9]{2,3}-[0-9]{1,3})\b"),
        lambda m: "https://armypubs.army.mil/ProductMaps/PubForm/Details.aspx?PUB_ID=" + m.group(1),
    ),
    # Service administrative messages.
    (
        "maradmin",
        re.compile(r"\bMARADMIN\s*([0-9]{1,3}/[0-9]{2})\b", re.I),
        lambda m: "https://www.marines.mil/News/Messages/",
    ),
    (
        "navadmin",
        re.compile(r"\bNAVADMIN\s*([0-9]{1,3}/[0-9]{2})\b", re.I),
        lambda m: "https://www.mynavyhr.navy.mil/References/Messages/NAVADMIN-2025/",
    ),
    # Literature.
    (
        "doi",
        re.compile(r"\b(10\.[0-9]{4,9}/[-._;()/:A-Z0-9]+)", re.I),
        lambda m: "https://doi.org/" + m.group(1),
    ),
    (
        "pmid",
        re.compile(r"\bPMID:?\s*([0-9]{6,9})\b", re.I),
        lambda m: f"https://pubmed.ncbi.nlm.nih.gov/{m.group(1)}/",
    ),
    (
        "pmcid",
        re.compile(r"\b(PMC[0-9]{6,9})\b"),
        lambda m: f"https://pmc.ncbi.nlm.nih.gov/articles/{m.group(1)}/",
    ),
    # Fire and cross-sector standards.
    (
        "nfpa",
        re.compile(r"\bNFPA\s+([0-9]{3,4}[A-Z]?)\b", re.I),
        lambda m: f"https://www.nfpa.org/codes-and-standards/nfpa-{m.group(1)}-standard-development",
    ),
    # Rulemaking and oversight.
    (
        "docket",
        re.compile(r"\b(OSHA|DOT|FEMA|DOJ)[-\s]([0-9]{4})[-\s]([0-9]{4,5})\b", re.I),
        lambda m: f"https://www.regulations.gov/docket/{m.group(1).upper()}-{m.group(2)}-{m.group(3)}",
    ),
    (
        "gao",
        re.compile(r"\bGAO[-\s]?([0-9]{2}-[0-9]{5,6})\b", re.I),
        lambda m: f"https://www.gao.gov/products/gao-{m.group(1)}",
    ),
)


def find_identifiers(text: str) -> list[Identifier]:
    """Every identifier in `text`, most specific kinds first, de-duplicated.

    Order within a kind follows the text. Order between kinds follows _PATTERNS,
    which is deliberate: an item that cites both an issuance and a DOI is the
    issuance, and the DOI belongs to something it references.
    """
    if not text:
        return []
    found: list[Identifier] = []
    seen: set[str] = set()
    for kind, pattern, to_url in _PATTERNS:
        for match in pattern.finditer(text):
            if kind == "docket":
                value = f"{match.group(1).upper()}-{match.group(2)}-{match.group(3)}"
            elif kind in ("doi", "pmcid"):
                value = match.group(1)
            else:
                value = _issuance(match)
            ident = Identifier(kind=kind, value=value, url=to_url(match))
            if ident.key in seen:
                continue
            seen.add(ident.key)
            found.append(ident)
    return found


def primary_identifier(text: str) -> Identifier | None:
    """The one identifier that decides this item's identity, or None."""
    idents = find_identifiers(text)
    return idents[0] if idents else None


def host_of(url: str) -> str:
    """Bare host for `url`, lowercased, without a leading www."""
    match = re.match(r"https?://([^/?#]+)", url or "", re.I)
    if not match:
        return ""
    host = match.group(1).lower()
    if host.startswith("www."):
        host = host[4:]
    return host


def is_fetchable(url: str) -> bool:
    """True when `url` is on an allowlisted primary-source host.

    Subdomains of an allowlisted host count; lookalikes appended to it do not,
    so `af.mil` admits `static.af.mil` but never `af.mil.example.com`.
    """
    host = host_of(url)
    if not host:
        return False
    return any(host == allowed or host.endswith("." + allowed) for allowed in FETCH_ALLOWLIST)
