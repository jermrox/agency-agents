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

from .facets import branches_of
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
    # Named SOF/conventional units and career fields.
    "tacp": 3.5,
    "pararescue": 3.5,
    "combat controller": 3.5,
    "special tactics": 3.5,
    "explosive ordnance disposal": 3.0,
    "eod": 2.0,
    "national guard": 2.5,
    "army reserve": 2.0,
    "coast guard": 2.0,
    "space force": 2.0,
    "infantry": 2.0,
    "aircrew": 2.0,
    "submarine": 1.5,
    # Accession and training pipelines -- a large and often-overlooked slice of
    # tactical human performance hiring sits at schoolhouses and academies.
    "basic training": 2.5,
    "recruit training": 3.0,
    "initial entry training": 3.0,
    "boot camp": 2.0,
    "military academy": 2.5,
    "west point": 3.0,
    "naval academy": 3.0,
    "air force academy": 3.0,
    "rotc": 2.5,
    "cadet": 2.0,
    "drill sergeant": 2.5,
    "selection course": 2.5,
    "training command": 2.0,
    # First responders.
    "first responder": 3.0,
    "law enforcement": 3.0,
    "firefighter": 3.0,
    "fire department": 2.5,
    "fire rescue": 2.5,
    "police department": 2.5,
    "sheriff": 2.5,
    "state trooper": 2.5,
    "public safety": 2.0,
    "swat": 3.0,
    "paramedic": 1.5,
    "emergency medical services": 1.5,
    "corrections officer": 2.0,
    "federal agent": 2.0,
    "border patrol": 3.0,
    "customs and border protection": 3.0,
    "secret service": 3.0,
    "federal bureau of investigation": 2.5,
    "us marshals": 3.0,
    "peer fitness trainer": 3.5,
    # NOTE: "wellness program" deliberately does NOT appear here. It carries no
    # tactical-population signal -- corporate wellness uses the identical phrase --
    # so listing it let "Wellness Coordinator, Acme Corp" clear the domain floor.
    # A genuine fire/LE wellness role still scores via "fire department" etc.
    # Service fitness tests and body-composition programs. These are named
    # instruments that only exist inside the tactical world, so a listing that
    # mentions one is almost certainly in-domain. Vocabulary sourced from the
    # MOPs & MOEs podcast catalog, which tracks this space week to week.
    "acft": 4.0,
    "army combat fitness test": 4.5,
    "army fitness test": 4.0,
    "combat fitness test": 3.5,
    "combat field test": 3.5,
    "physical readiness test": 3.0,
    "physical fitness test": 2.0,
    "body composition program": 3.0,
    "army body composition": 3.5,
    "occupational physical assessment": 3.5,
    "opat": 3.0,
    "prt": 1.5,
    # POTFF/H2F program pillars -- these phrasings show up in billet
    # descriptions for the non-physical domains of the same teams.
    "spiritual fitness": 2.5,
    "moral injury": 2.0,
    "human performance optimization": 3.5,
    # Generic but useful when stacked with the above.
    "tactical": 1.5,
    "uniformed": 1.5,
    "operational readiness": 2.0,
    "force readiness": 2.5,
    "occupational athlete": 3.0,
    "industrial athlete": 2.5,
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
    "readiness monitoring": 2.5,
    "load monitoring": 2.5,
    "athlete monitoring": 3.0,
    "periodization": 2.5,
    "return to performance": 3.0,
    # Sport science and the data side of human performance -- a fast-growing
    # slice of this market that a purely coaching-shaped keyword list misses.
    "sport scientist": 4.0,
    "sports scientist": 4.0,
    "sport science": 3.5,
    "performance analyst": 3.0,
    "human performance analyst": 4.5,
    "performance technology": 3.0,
    # NOTE: bare "human factors" is deliberately absent. In defense listings it
    # almost always means systems/ergonomics ENGINEERING, not human performance,
    # so it handed "Human Factors Engineer, Lockheed" a discipline score it had
    # no business having -- the exact false positive the two-axis rule exists to
    # prevent. Genuine sport-science roles score via the terms around it.
    "kinesiologist": 3.5,
    "kinesiology": 2.5,
    # Allied clinical roles that staff the same embedded teams.
    "occupational therapist": 3.0,
    "physician assistant": 2.0,
    "chiropractor": 2.5,
    "massage therapist": 2.0,
    "manual therapy": 2.5,
    "physical therapy technician": 3.0,
    "rehabilitation specialist": 3.0,
    "strength technician": 3.0,
    "athletic training student": 2.0,
    # Program leadership and delivery.
    "director of human performance": 5.0,
    "human performance director": 5.0,
    "performance director": 3.0,
    "strength and conditioning director": 4.5,
    "human performance manager": 4.0,
    "human performance coordinator": 4.0,
    "wellness coordinator": 2.5,
    "fitness program manager": 3.0,
    "performance program manager": 3.5,
    "health promotion": 2.5,
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


SERVICE_CONTEXT_WEIGHT = 3.0
"""Domain credit for a posting whose service branch can be identified.

Set so that branch context alone does not clear ``min_domain`` -- it still
needs some vocabulary of its own -- while a posting carrying both clears it
comfortably. Tuned against the live board: at this weight the branch-aware
rule keeps every tactical posting the old thresholds kept and adds seven the
location field had been hiding, while dropping twenty VA clinic roles.
"""


@dataclass(frozen=True, slots=True)
class Thresholds:
    """Score cutoffs that decide what happens to a posting."""

    publish: float = 14.0
    """At or above this, the posting is good enough to go straight out."""

    review: float = 8.0
    """At or above this (but below publish), route to the review queue."""

    min_domain: float = 3.5
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

    # Where the job physically is, is domain evidence -- and until now nothing
    # read it. The scoring haystack is title + department + description +
    # employer; `location` was never in it. So a physical therapist post at
    # Fort Gordon or Camp Lejeune had its single strongest tactical signal
    # sitting in a field the classifier never opened.
    #
    # That gap mattered in both directions once USAJOBS went live. Federal
    # health-care announcements list "graduate of military physical therapy
    # assistant programs" among the qualifying credentials, so an outpatient
    # VA clinic job in Montgomery, Alabama picked up a domain hit from a
    # sentence about schooling. Meanwhile a real Defense Health Agency posting
    # at Camp Lejeune scored no higher, because the base name was invisible.
    #
    # Service-branch context is the discriminator. It is read from the
    # employer, the program name and the installation, it already excludes the
    # cities named Fort-something, and it is exactly what "military" in a
    # credential list is not: evidence about the work, not about the applicant.
    if branches_of(posting.title, posting.employer, posting.location):
        domain_score += SERVICE_CONTEXT_WEIGHT
        domain_hits = [*domain_hits, "service context"]

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
            "strength technician",
        ),
        "sports-medicine": (
            "athletic trainer",
            "athletic training",
            "athletic training student",
            "physical therapist",
            "physical therapy",
            "physical therapy technician",
            "sports medicine",
            "reconditioning",
            "rehabilitation specialist",
            "occupational therapist",
            "chiropractor",
            "manual therapy",
            "massage therapist",
            "physician assistant",
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
        "sport-science": (
            "sport scientist",
            "sports scientist",
            "sport science",
            "performance analyst",
            "human performance analyst",
            "performance technology",
            "readiness monitoring",
            "load monitoring",
            "force plate",
        ),
        "research": (
            "biomechanist",
            "biomechanics",
            "physiologist",
            "sleep scientist",
            "kinesiologist",
            "kinesiology",
        ),
        "leadership": (
            "director of human performance",
            "human performance director",
            "performance director",
            "strength and conditioning director",
            "human performance manager",
            "human performance coordinator",
            "fitness program manager",
            "performance program manager",
            "wellness coordinator",
            "health promotion",
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
            "national guard",
            "army reserve",
            "coast guard",
            "space force",
            "infantry",
            "aircrew",
            "submarine",
            "explosive ordnance disposal",
            "eod",
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
            "tacp",
            "pararescue",
            "combat controller",
            "special tactics",
        ),
        "first-responder": (
            "first responder",
            "law enforcement",
            "firefighter",
            "fire department",
            "fire rescue",
            "police department",
            "sheriff",
            "state trooper",
            "public safety",
            "swat",
            "paramedic",
            "emergency medical services",
            "corrections officer",
            "federal agent",
            "border patrol",
            "customs and border protection",
            "secret service",
            "federal bureau of investigation",
            "us marshals",
            "peer fitness trainer",
        ),
        # Accession pipelines are a distinct hiring population from operational
        # units -- schoolhouses staff differently and hire on their own cycle.
        "training-pipeline": (
            "basic training",
            "recruit training",
            "initial entry training",
            "boot camp",
            "military academy",
            "west point",
            "naval academy",
            "air force academy",
            "rotc",
            "cadet",
            "drill sergeant",
            "selection course",
            "training command",
        ),
    }
    for tag, members in domain_map.items():
        if any(hit in members for hit in domain_hits):
            tags.add(tag)

    if posting.remote:
        tags.add("remote")
    return sorted(tags)
