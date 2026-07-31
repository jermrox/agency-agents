"""Employer and vocabulary discovery from tactical human performance media.

THE PROBLEM THIS SOLVES
A job scraper is only as good as its list of employers to watch. Hand-curating
that list is the real bottleneck -- you cannot scrape a board you have never
heard of, and this industry's employers are not household names.

But the MOPs & MOEs podcast has been interviewing this exact ecosystem weekly
for years: the units, the contractors, the sponsors, the schools, the vendors.
Its episode catalog is a running census of who matters in tactical human
performance. Mining it produces a candidate employer watchlist far faster than
anyone could assemble by hand, and it keeps producing new ones as the show
publishes.

The same pass harvests *vocabulary*. Episode topics track how this field
actually talks right now -- ACFT, AFT, ABCP, offset PT, athlete monitoring --
and terms the classifier does not yet know are exactly the terms that would
cause it to miss jobs.

WHAT THIS IS NOT
This does not treat the podcast as a job source; episodes are not jobs. It is
an intelligence feed that produces two artifacts for a human to act on:

  1. candidate employers -> paste into sources.toml after finding their ATS
  2. candidate vocabulary -> consider adding to classify.py

Both outputs are explicitly *candidates*. Nothing here auto-edits the
classifier or the source list, because a false employer wastes a fetch and a
false keyword quietly corrupts scoring for everything.
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Iterable

from .classify import DISCIPLINE_TERMS, DOMAIN_TERMS

# Organizations that appear constantly in this space but are not employers to
# scrape -- either they are the show itself, a platform, or a generic body.
_STOPLIST = {
    "mops", "moes", "mops moes", "the army", "the navy", "the air force",
    "united states", "u s", "us", "the us", "the united states", "america",
    "instagram", "youtube", "spotify", "apple podcasts", "facebook", "twitter",
    "linkedin", "patreon", "discord", "the podcast", "this episode",
    "what we get into", "mentioned in this episode", "learn more", "free trial",
    "views expressed", "the same", "the best", "the original", "part 2",
}

# Suffixes that mark a capitalized run as an organization rather than a person
# or a title. Requiring one of these massively cuts false positives compared to
# treating every capitalized bigram as a company.
_ORG_SUFFIXES = (
    "university", "college", "institute", "school", "academy", "command",
    "group", "systems", "solutions", "technologies", "technology", "labs",
    "laboratory", "health", "performance", "fitness", "sports", "medicine",
    "consulting", "partners", "associates", "services", "corporation",
    "company", "international", "global", "federal", "defense", "tactical",
    "athletics", "training", "research", "center", "centre", "foundation",
    "association", "society", "council", "network", "alliance", "team",
)

_ORG_LEGAL = (" inc", " llc", " ltd", " corp", " co", " plc", " gmbh", " l3")

# A run of capitalized words, optionally joined by lowercase connectors.
# NOTE: '.' is deliberately excluded from the token character class. Allowing it
# let a run swallow the sentence boundary and keep going -- producing junk like
# "Institute for Human and Machine Cognition. We" instead of the organization.
_CAP_RUN = re.compile(
    r"\b([A-Z][A-Za-z0-9&'’-]*(?:\s+(?:of|and|for|the|de|van)\s+[A-Z][A-Za-z0-9&'’-]*"
    r"|\s+[A-Z][A-Za-z0-9&'’-]*){0,5})\b"
)

# Single all-caps tokens are usually instruments, tests, or programs (ACFT,
# DEXA, OPAT), not employers. Only these are organizations worth watching, so a
# lone acronym outside this set is routed to vocabulary instead.
_ORG_ACRONYMS = {
    "USASOC", "SOCOM", "USSOCOM", "MARSOC", "AFSOC", "NSW", "WARCOM",
    "NSCA", "NATA", "ACSM", "CSCCA", "AASP", "SCAN",
    "USUHS", "CHAMP", "NHRC", "USARIEM", "WRAIR", "NAMRU",
    "DHA", "DOD", "VA", "TRADOC", "FORSCOM", "AETC", "USAREC",
    "O2X", "EXOS", "NFL", "NBA", "NCAA",
}

# Relevance gate for mining, deliberately SEPARATE from the classifier's
# DOMAIN_TERMS. Scoring terms are tuned for precision -- they decide whether a
# job reaches the site, so they are multi-word and strict. This gate only
# decides whether a document is worth reading for candidates, where a miss
# costs real leads and a false positive costs one reviewable table row. Bare
# service words are exactly right here and exactly wrong there.
_TACTICAL_GATE = (
    "army", "navy", "air force", "marine", "coast guard", "space force",
    "soldier", "sailor", "airman", "military", "tactical", "warfighter",
    "special operations", "defense", "veteran", "combat", "troop", "unit",
    "first responder", "firefighter", "police", "law enforcement", "swat",
    "human performance", "strength and conditioning", "athletic trainer",
    "fitness test", "readiness",
)

# Phrases starting with these are sentence fragments, not terms of art.
_PHRASE_STOP_LEAD = {
    "the", "and", "a", "an", "of", "for", "to", "is", "was", "are", "were",
    "our", "this", "that", "these", "those", "only", "same", "best", "new",
    "his", "her", "their", "its", "it", "we", "you", "they", "with", "from",
    "on", "in", "at", "by", "as", "or", "but", "not", "no", "any", "all",
}

# Bare domains mentioned in show notes -- sponsors and referenced companies
# publish these, and a domain is a much stronger employer signal than a name.
_DOMAIN = re.compile(r"\b((?:[a-z0-9][a-z0-9-]*\.)+(?:com|org|net|io|us|mil|edu|co))\b")

_KNOWN_ATS_HOSTS = {
    "greenhouse.io": "greenhouse",
    "lever.co": "lever",
    "ashbyhq.com": "ashby",
    "workable.com": "workable",
    "smartrecruiters.com": "smartrecruiters",
    "recruitee.com": "recruitee",
    "bamboohr.com": "bamboohr",
    "breezy.hr": "breezy",
    "applytojob.com": "jazzhr",
    "myworkdayjobs.com": "workday",
    "icims.com": "icims",
    "governmentjobs.com": "governmentjobs",
}


@dataclass(slots=True)
class Candidate:
    """One discovered thing, with the evidence that produced it."""

    value: str
    kind: str
    """``employer`` | ``domain`` | ``vocabulary`` | ``ats``"""

    mentions: int = 1
    contexts: list[str] = field(default_factory=list)
    ats_hint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "value": self.value,
            "kind": self.kind,
            "mentions": self.mentions,
            "ats_hint": self.ats_hint,
            "contexts": self.contexts[:3],
        }


def _normalize(name: str) -> str:
    return re.sub(r"\s+", " ", name).strip(" .,-–—'’").strip()


def _looks_like_org(name: str) -> bool:
    """Heuristic: is this capitalized run an organization worth watching?

    Deliberately strict. A missed employer costs one line in a watchlist a
    human is reviewing anyway; a flood of false ones makes the whole artifact
    useless and it gets ignored.
    """
    lowered = name.lower()
    if lowered in _STOPLIST or len(name) < 4:
        return False
    words = name.split()
    if len(words) > 7:
        return False

    # A lone acronym is only an organization if we know it to be one. Without
    # this, every instrument and test in the corpus (ACFT, DEXA, OPAT, BodPod)
    # lands in the employer watchlist and buries the real leads.
    if len(words) == 1:
        return name.upper() in _ORG_ACRONYMS

    if any(lowered.endswith(suffix) for suffix in _ORG_LEGAL):
        return True
    if any(word.lower() in _ORG_SUFFIXES for word in words):
        return True
    # A multi-word run containing a known org acronym, e.g. "USASOC Human
    # Performance" or "MARSOC Preservation of the Force".
    return any(w.upper() in _ORG_ACRONYMS for w in words)


def _context(text: str, index: int, width: int = 90) -> str:
    start = max(0, index - width // 2)
    return " ".join(text[start : index + width].split())


def is_relevant(text: str) -> bool:
    """Is this document about the tactical realm at all?

    Gate for every extractor. Without it, an off-topic document still
    contributes domains and organizations -- a podcast ad read for an espresso
    machine would put its vendor in the employer watchlist.
    """
    lowered = text.lower()
    return any(term in lowered for term in _TACTICAL_GATE)


def extract_employers(text: str) -> list[Candidate]:
    """Pull candidate organizations out of a block of prose."""
    if not is_relevant(text):
        return []

    found: dict[str, Candidate] = {}

    for match in _CAP_RUN.finditer(text):
        name = _normalize(match.group(1))
        if not _looks_like_org(name):
            continue
        key = name.lower()
        if key in found:
            found[key].mentions += 1
        else:
            found[key] = Candidate(
                value=name, kind="employer", contexts=[_context(text, match.start())]
            )

    for match in _DOMAIN.finditer(text):
        domain = match.group(1).lower()
        if domain.endswith((".mil", ".edu")):
            # Government and academic domains are references, not employers
            # with a scrapable careers board.
            continue
        key = f"domain:{domain}"
        if key in found:
            found[key].mentions += 1
            continue
        ats = next(
            (kind for host, kind in _KNOWN_ATS_HOSTS.items() if domain.endswith(host)),
            None,
        )
        found[key] = Candidate(
            value=domain,
            kind="ats" if ats else "domain",
            ats_hint=ats,
            contexts=[_context(text, match.start())],
        )

    return sorted(found.values(), key=lambda c: (-c.mentions, c.value.lower()))


def extract_vocabulary(text: str, *, min_mentions: int = 2) -> list[Candidate]:
    """Find domain-shaped terms the classifier does not already know.

    Looks for acronyms and multi-word phrases that co-occur with terms the
    classifier *does* know -- co-occurrence is what separates a real term of
    art from an incidental capitalized word.
    """
    known = {t.lower() for t in (*DOMAIN_TERMS, *DISCIPLINE_TERMS)}
    lowered = text.lower()

    # Only mine text that is actually about this domain, or every proper noun
    # in an off-topic paragraph becomes a candidate.
    if not is_relevant(text):
        return []

    counts: Counter[str] = Counter()
    contexts: dict[str, str] = {}

    for match in re.finditer(r"\b([A-Z]{2,6}[0-9]?)\b", text):
        token = match.group(1)
        if token.lower() in known or token.lower() in _STOPLIST:
            continue
        counts[token] += 1
        contexts.setdefault(token, _context(text, match.start()))

    for match in re.finditer(
        r"\b((?:[a-z]+\s){1,3}(?:test|assessment|screen|standard|program|protocol|index|score))\b",
        lowered,
    ):
        phrase = _normalize(match.group(1))

        # Trim leading function words rather than discarding the match. The
        # quantifier is greedy, so a real term is routinely captured with a
        # determiner glued on ("the combat readiness assessment"); rejecting on
        # a stopword lead would throw away the term along with the grammar.
        words = phrase.split()
        while words and words[0] in _PHRASE_STOP_LEAD:
            words.pop(0)
        phrase = " ".join(words)

        # What survives must still be a compound term, not a lone noun.
        if len(words) < 2 or phrase in known or len(phrase) < 8:
            continue
        counts[phrase] += 1
        contexts.setdefault(phrase, _context(text, match.start()))

    return sorted(
        (
            Candidate(
                value=term,
                kind="vocabulary",
                mentions=count,
                contexts=[contexts.get(term, "")],
            )
            for term, count in counts.items()
            if count >= min_mentions
        ),
        key=lambda c: (-c.mentions, c.value.lower()),
    )


def discover(texts: Iterable[str], *, min_mentions: int = 2) -> dict[str, Any]:
    """Run discovery over many documents (e.g. every podcast episode note)."""
    employers: dict[str, Candidate] = {}
    vocabulary: dict[str, Candidate] = {}
    document_count = 0

    for text in texts:
        if not text or not text.strip():
            continue
        document_count += 1
        for candidate in extract_employers(text):
            existing = employers.get(candidate.value.lower())
            if existing:
                existing.mentions += candidate.mentions
                existing.contexts.extend(candidate.contexts)
            else:
                employers[candidate.value.lower()] = candidate
        for candidate in extract_vocabulary(text, min_mentions=1):
            existing = vocabulary.get(candidate.value.lower())
            if existing:
                existing.mentions += candidate.mentions
                existing.contexts.extend(candidate.contexts)
            else:
                vocabulary[candidate.value.lower()] = candidate

    ranked_employers = sorted(
        (c for c in employers.values() if c.mentions >= min_mentions),
        key=lambda c: (-c.mentions, c.value.lower()),
    )
    ranked_vocabulary = sorted(
        (c for c in vocabulary.values() if c.mentions >= min_mentions),
        key=lambda c: (-c.mentions, c.value.lower()),
    )

    return {
        "documents": document_count,
        "employers": [c.to_dict() for c in ranked_employers if c.kind == "employer"],
        "domains": [c.to_dict() for c in ranked_employers if c.kind == "domain"],
        "ats_boards": [c.to_dict() for c in ranked_employers if c.kind == "ats"],
        "vocabulary": [c.to_dict() for c in ranked_vocabulary],
    }


def render_watchlist(discovery: dict[str, Any], *, limit: int = 40) -> str:
    """Render discovery output as a Markdown worksheet for a human.

    Emits commented-out TOML stubs rather than live config: finding an
    employer's ATS still takes a human 30 seconds, and a wrong board token
    silently returns nothing.
    """
    lines = [
        "# Discovered employer watchlist",
        "",
        f"Mined from {discovery.get('documents', 0)} document(s). "
        "Everything here is a **candidate** — confirm the ATS before enabling.",
        "",
    ]

    boards = discovery.get("ats_boards", [])
    if boards:
        lines += ["## Known ATS boards (highest confidence)", ""]
        for entry in boards[:limit]:
            lines.append(
                f"- `{entry['value']}` — looks like **{entry['ats_hint']}** "
                f"({entry['mentions']} mention(s))"
            )
        lines.append("")

    employers = discovery.get("employers", [])
    if employers:
        lines += [
            "## Candidate employers",
            "",
            "| Organization | Mentions | Context |",
            "|---|---:|---|",
        ]
        for entry in employers[:limit]:
            context = (entry["contexts"][0] if entry["contexts"] else "").replace("|", "\\|")
            lines.append(f"| {entry['value']} | {entry['mentions']} | {context[:80]} |")
        lines.append("")

    domains = discovery.get("domains", [])
    if domains:
        lines += ["## Referenced domains — check these for a careers page", ""]
        for entry in domains[:limit]:
            lines.append(f"- https://{entry['value']} ({entry['mentions']} mention(s))")
        lines.append("")

    vocabulary = discovery.get("vocabulary", [])
    if vocabulary:
        lines += [
            "## Vocabulary the classifier does not know",
            "",
            "Terms of art appearing alongside known domain language. Adding a real "
            "one widens coverage; adding a wrong one quietly corrupts scoring, so "
            "review each.",
            "",
            "| Term | Mentions | Context |",
            "|---|---:|---|",
        ]
        for entry in vocabulary[:limit]:
            context = (entry["contexts"][0] if entry["contexts"] else "").replace("|", "\\|")
            lines.append(f"| `{entry['value']}` | {entry['mentions']} | {context[:70]} |")
        lines.append("")

    if not (boards or employers or domains or vocabulary):
        lines.append("_Nothing discovered._")

    return "\n".join(lines) + "\n"
