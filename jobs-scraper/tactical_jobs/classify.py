"""Relevance scoring for tactical human performance roles.

The whole problem with a keyword scraper in this space is that "performance"
and "tactical" are two of the most overloaded words in job listings. A single
bag of keywords produces a board full of Performance Marketing Managers and
Tactical Category Buyers.

So this scores on two independent axes and requires signal on **both**:

* **domain** -- is the population tactical? (military, SOF, LE, fire, EMS)
* **discipline** -- is the work human performance? (S&C, ATC, PT, RD, cognitive)

"Strength Coach, University of Michigan" hits discipline but not domain.
"Performance Engineer, Lockheed Martin" hits domain but not discipline.
Neither is a match. "THOR3 Strength and Conditioning Coach" hits both.

Title matches count for more than description matches, because a description
that merely *mentions* working with first responders is much weaker evidence
than a title that names the job.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .models import JobPosting

# --------------------------------------------------------------------------
# Axis 1: tactical domain. Who is the athlete?
# --------------------------------------------------------------------------
# Weights are rough confidence: a term that is *only* used in this space
# (THOR3, POTFF) scores far above a term that merely co-occurs (government).
DOMAIN_TERMS: dict[str, float] = {
    # Named DoD human performance programs -- essentially zero false positives.
    "thor3": 5.0,
    "potff": 5.0,
    "preservation of the force": 5.0,
    "holistic health and fitness": 5.0,
    "h2f": 4.0,
    "human performance program": 3.5,
    "sports medicine and reconditioning": 4.0,
    "operator performance": 4.0,
    "tactical athlete": 4.5,
    "warfighter": 3.5,
    # Special operations components.
    "special operations": 3.5,
    "special warfare": 3.5,
    "socom": 3.5,
    "ussocom": 3.5,
    "usasoc": 3.5,
    "marsoc": 3.5,
    "afsoc": 3.5,
    "naval special warfare": 3.5,
    "green beret": 3.0,
    "army ranger": 3.0,
    "navy seal": 3.0,
    # Broader military.
    "military": 2.0,
    "department of defense": 2.0,
    "dod": 1.5,
    "soldier": 2.0,
    "airman": 2.0,
    "sailor": 1.5,
    "marine corps": 2.0,
    "active duty": 2.0,
    "service member": 2.0,
    "servicemember": 2.0,
    "veteran": 1.0,
    "combat": 1.5,
    "garrison": 1.5,
    "brigade": 1.5,
    "battalion": 1.5,
    # First responders.
    "first responder": 3.0,
    "law enforcement": 3.0,
    "firefighter": 3.0,
    "fire department": 2.5,
    "police department": 2.5,
    "public safety": 2.0,
    "swat": 3.0,
    "paramedic": 1.5,
    "corrections officer": 2.0,
    "federal agent": 2.0,
    # Generic but useful when stacked with the above.
    "tactical": 1.5,
    "uniformed": 1.5,
}

# --------------------------------------------------------------------------
# Axis 2: human performance discipline. What is the work?
# --------------------------------------------------------------------------
DISCIPLINE_TERMS: dict[str, float] = {
    # Strength and conditioning.
    "strength and conditioning": 4.0,
    "tactical strength and conditioning": 5.0,
    "tsac": 4.5,
    "tsac-f": 5.0,
    "strength coach": 4.0,
    "cscs": 3.5,
    "human performance": 4.0,
    "performance coach": 3.5,
    "performance specialist": 3.5,
    "exercise physiologist": 4.0,
    "exercise science": 3.0,
    "physical readiness": 3.0,
    "fitness coordinator": 2.5,
    "conditioning coach": 3.5,
    # Sports medicine / rehab.
    "athletic trainer": 4.0,
    "athletic training": 3.5,
    "physical therapist": 3.5,
    "physical therapy": 3.0,
    "sports medicine": 3.5,
    "reconditioning": 3.5,
    "musculoskeletal": 2.5,
    "injury prevention": 3.0,
    "return to duty": 3.0,
    "return to play": 2.5,
    # Nutrition.
    "registered dietitian": 4.0,
    "performance dietitian": 4.5,
    "sports nutrition": 3.5,
    "nutritionist": 2.5,
    # Cognitive / mental performance.
    "cognitive performance": 4.5,
    "mental performance": 4.5,
    "sport psychologist": 4.0,
    "sport psychology": 4.0,
    "performance psychology": 4.0,
    "mental skills": 3.0,
    "resilience training": 2.5,
    # Sleep / recovery / physiology.
    "sleep scientist": 3.0,
    "recovery specialist": 3.0,
    "biomechanist": 4.0,
    "biomechanics": 3.0,
    "physiologist": 3.0,
    "wearable": 1.5,
    "force plate": 3.0,
    "vo2": 2.5,
    # Program leadership.
    "director of human performance": 5.0,
    "human performance director": 5.0,
    "performance director": 3.0,
    "strength and conditioning director": 4.5,
}

# --------------------------------------------------------------------------
# Hard exclusions. Any hit here vetoes the posting outright.
# --------------------------------------------------------------------------
# These are phrases where "performance" or "tactical" carries a completely
# unrelated meaning. A veto is safer than a negative weight: we would rather
# silently drop a real job than publish a software listing to a coaching board.
EXCLUSION_TERMS: tuple[str, ...] = (
    "performance marketing",
    "marketing performance",
    "sales performance",
    "performance management system",
    "high performance computing",
    "performance engineer",
    "performance engineering",
    "performance testing",
    "performance test engineer",
    "database performance",
    "application performance",
    "web performance",
    "site performance",
    "query performance",
    "ad performance",
    "campaign performance",
    "portfolio performance",
    "fund performance",
    "tactical marketing",
    "tactical buyer",
    "tactical sourcing",
    "tactical procurement",
    "tactical gear",  # retail/e-commerce, not coaching
    "performance review process",
    "sales engineer",
)

# Terms whose presence in the *title* is worth extra, since a title is a much
# stronger claim about the job than a passing mention in the body.
TITLE_MULTIPLIER = 2.5
DESCRIPTION_CAP = 3
"""Count a description term at most this many times.

Long federal postings repeat "Soldier" 40 times; without a cap a single
verbose listing would outrank every genuinely relevant one.
"""


@dataclass(frozen=True, slots=True)
class Thresholds:
    """Score cutoffs that decide what happens to a posting."""

    publish: float = 14.0
    """At or above this, the posting is good enough to go straight out."""

    review: float = 8.0
    """At or above this (but below publish), route to the review queue."""

    min_domain: float = 1.5
    """Minimum domain-axis score. Blocks collegiate/pro sports jobs."""

    min_discipline: float = 3.0
    """Minimum discipline-axis score. Blocks defense-industry engineering."""


class Verdict:
    PUBLISH = "publish"
    REVIEW = "review"
    REJECT = "reject"


def _haystack(posting: JobPosting) -> tuple[str, str]:
    """Return (title, description) lowercased with separators normalized."""
    title = f" {posting.title.lower()} {posting.department or ''} ".replace("&", " and ")
    body = f" {posting.description.lower()} {posting.employer.lower()} ".replace("&", " and ")
    # Treat punctuation as whitespace so "coach/specialist" matches both.
    title = re.sub(r"[^a-z0-9]+", " ", title)
    body = re.sub(r"[^a-z0-9]+", " ", body)
    return title, body


def _score_axis(
    terms: dict[str, float], title: str, body: str
) -> tuple[float, list[str]]:
    """Score one axis, returning the total and the terms that fired."""
    total = 0.0
    hits: list[str] = []
    for term, weight in terms.items():
        needle = re.sub(r"[^a-z0-9]+", " ", term)
        padded = f" {needle} "
        in_title = padded in title
        body_count = min(body.count(padded), DESCRIPTION_CAP)
        if not in_title and body_count == 0:
            continue
        hits.append(term)
        if in_title:
            total += weight * TITLE_MULTIPLIER
        total += weight * body_count
    return total, hits


def classify(posting: JobPosting, thresholds: Thresholds | None = None) -> str:
    """Score ``posting`` in place and return a :class:`Verdict`."""
    thresholds = thresholds or Thresholds()
    title, body = _haystack(posting)

    # Exclusions win outright, before any scoring work.
    excluded = [
        term
        for term in EXCLUSION_TERMS
        if f" {re.sub(r'[^a-z0-9]+', ' ', term)} " in title
        or f" {re.sub(r'[^a-z0-9]+', ' ', term)} " in body
    ]
    if excluded:
        posting.exclusion_hits = excluded
        posting.score = 0.0
        return Verdict.REJECT

    domain_score, domain_hits = _score_axis(DOMAIN_TERMS, title, body)
    discipline_score, discipline_hits = _score_axis(DISCIPLINE_TERMS, title, body)

    posting.domain_hits = domain_hits
    posting.discipline_hits = discipline_hits
    posting.score = domain_score + discipline_score
    posting.tags = _derive_tags(domain_hits, discipline_hits, posting)

    # Both axes must clear their floor -- this is what keeps the board tactical
    # *and* keeps it about human performance.
    if domain_score < thresholds.min_domain or discipline_score < thresholds.min_discipline:
        return Verdict.REJECT
    if posting.score >= thresholds.publish:
        return Verdict.PUBLISH
    if posting.score >= thresholds.review:
        return Verdict.REVIEW
    return Verdict.REJECT


def _derive_tags(
    domain_hits: list[str], discipline_hits: list[str], posting: JobPosting
) -> list[str]:
    """Human-facing facets for filtering the published board."""
    tags: set[str] = set()

    discipline_map = {
        "strength-conditioning": (
            "strength and conditioning",
            "tactical strength and conditioning",
            "tsac",
            "tsac-f",
            "strength coach",
            "cscs",
            "conditioning coach",
            "exercise physiologist",
        ),
        "sports-medicine": (
            "athletic trainer",
            "athletic training",
            "physical therapist",
            "physical therapy",
            "sports medicine",
            "reconditioning",
        ),
        "nutrition": (
            "registered dietitian",
            "performance dietitian",
            "sports nutrition",
            "nutritionist",
        ),
        "cognitive": (
            "cognitive performance",
            "mental performance",
            "sport psychologist",
            "sport psychology",
            "performance psychology",
            "mental skills",
        ),
        "research": ("biomechanist", "biomechanics", "physiologist", "sleep scientist"),
        "leadership": (
            "director of human performance",
            "human performance director",
            "performance director",
            "strength and conditioning director",
        ),
    }
    for tag, members in discipline_map.items():
        if any(hit in members for hit in discipline_hits):
            tags.add(tag)

    domain_map = {
        "military": (
            "military",
            "department of defense",
            "dod",
            "soldier",
            "airman",
            "sailor",
            "marine corps",
            "active duty",
            "service member",
            "servicemember",
            "h2f",
            "holistic health and fitness",
            "brigade",
            "battalion",
            "garrison",
        ),
        "sof": (
            "thor3",
            "potff",
            "preservation of the force",
            "special operations",
            "special warfare",
            "socom",
            "ussocom",
            "usasoc",
            "marsoc",
            "afsoc",
            "naval special warfare",
            "green beret",
            "army ranger",
            "navy seal",
        ),
        "first-responder": (
            "first responder",
            "law enforcement",
            "firefighter",
            "fire department",
            "police department",
            "public safety",
            "swat",
            "paramedic",
            "corrections officer",
            "federal agent",
        ),
    }
    for tag, members in domain_map.items():
        if any(hit in members for hit in domain_hits):
            tags.add(tag)

    if posting.remote:
        tags.add("remote")
    return sorted(tags)
