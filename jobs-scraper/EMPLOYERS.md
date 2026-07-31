# The tactical human performance employer landscape

Who actually hires in this space, and how we found them.

**Why this file exists.** The scraper has 19 working source adapters and that was
never the bottleneck — knowing *who to point them at* was. This is the researched
answer, with citations, so the list can be argued with rather than trusted.

**What is and is not verified here.** The contract awards below are verified from
company press releases and federal contracting records, with links. The **ATS board
tokens are not verified** — that requires network access this build environment does
not have. Treat every token as a hypothesis and confirm it before enabling
(see [Adding an employer](README.md#adding-an-employer)).

---

## The insight: contract awards are a leading indicator

When a contractor wins an H2F or POTFF contract they must staff it, and they start
hiring within weeks. **The award is public before any job posting exists.**

The clearest example: in January 2025 Serco announced a US Army H2F award worth up
to **$247M**, under which "Team Serco" planned to hire and deploy **over 350
certified Strength and Conditioning Coaches** in the base year alone, supporting 45
Army brigades across 15 CONUS locations.[^serco]

That single award represents more tactical strength-and-conditioning hiring than
most job boards in this niche will show in a year — and it was knowable months
before those postings appeared.

This is what `tactical_jobs/contracts.py` automates, against the
[USASpending.gov API](https://api.usaspending.gov/), which is **completely open —
no API key, no account**.

---

## Prime contractors — verified awards

These won the contracts. They do the hiring.

| Employer | Program | Award | Evidence |
|---|---|---:|---|
| **Serco** | Army H2F | $247M ceiling | [Serco press release][^serco] |
| **KBR** (KBRwyle) | USSOCOM POTFF | $500M | [KBR][^kbr] |
| **GAP Solutions** | Army H2F | $100M+ | [GAP Solutions][^gap] |
| **HigherEchelon** | Army H2F (Team Serco) | subcontract | [^serco] |
| **Hyperion Biotechnology** | Army H2F (Team Serco) | subcontract | [^serco] |
| **Resolution Think** | Army H2F (Team Serco) | subcontract | [^serco] |
| **The Geneva Foundation** | Army H2F (Team Serco) | subcontract | [^serco] |

**Note how wrong a guess would have been.** Before this research the registry was
seeded with the usual defense primes — Leidos, Booz Allen, CACI. Those are
reasonable guesses and **none of them are the actual H2F winners**. This is exactly
why the tokens in the config are labelled unverified rather than presented as fact.

KBR runs a **dedicated POTFF careers page** at
`careers.kbr.com/us/en/potff2` — a rare case of an employer segmenting this exact
work, and a high-value target for the `jsonld` or `agencyboard` adapter.

## Specialist firms

Human performance is their whole business, so nearly every posting is relevant.

| Employer | Notes |
|---|---|
| **O2X Human Performance** | Tactical HP for military and first responders |
| **EXOS** | Performance training; military and government contracts |
| **PSI** | Places athletic trainers with US military units (`athletictrainerjob.com`) |
| **Sword Performance** | Tactical performance |
| **Magellan Federal** | Long-running military HP and resilience staffing |

## Federal, direct

Beyond USAJOBS. Service civilian and NAF hiring carries fitness and sports-program
staffing that never reaches USAJOBS.

| Employer | Notes |
|---|---|
| Department of the Army (H2F) | Government-civilian H2F billets |
| Defense Health Agency | Sports medicine, physical therapy |
| Naval Special Warfare | Sports medicine physicians, PTs, strength coaches, dietitians, cognitive specialists under one roof |
| USMC Human Performance Branch, Quantico | `fitness.marines.mil` |
| Navy Military Athletic Training Readiness | Navy Medicine athletic trainer program |
| Department of Veterans Affairs | Rehabilitation, whole health |

## Association career centers

The highest signal-per-posting anywhere in this niche — almost every listing is a
strength coach or athletic trainer role, where a general job site is overwhelmingly
noise.

NSCA · NATA · ACSM · CSCCa · AASP · SCAN (sports nutrition) · APTA

---

## Contract intelligence sources

All keyless except where noted.

| Source | Use | Key needed? |
|---|---|---|
| [USASpending.gov API](https://api.usaspending.gov/) | Awards — who won, how much, when | **No** |
| [SAM.gov](https://sam.gov/) | Open solicitations — who is *about* to win | Key for API; web UI free |
| [GovTribe](https://govtribe.com/) | Award and opportunity tracking | Commercial |
| [HigherGov](https://www.highergov.com/) | Award and opportunity tracking | Commercial |

`contracts.py` targets USASpending precisely because it is the one with a fully open
API — consistent with the no-credentials constraint.

---

## How to verify a token before enabling it

```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/<token>/jobs" | head -c 300
curl -s "https://api.lever.co/v0/postings/<token>?mode=json"      | head -c 300
```

For Workday, read tenant/site straight out of the careers URL:
`https://{tenant}.{dc}.myworkdayjobs.com/{site}`

Then add the block and run `--dry-run`. A wrong token surfaces as an `ERROR` line in
the run summary, never a silent zero.

[^serco]: [Serco Awarded $247M U.S. Army Holistic Health and Fitness (H2F) Contract](https://www.serco.com/na/media-and-news/2025/serco-awarded-247m-us-army-holistic-health-and-fitness-h2f-contract), January 2025. Team Serco comprises Serco, HigherEchelon, Hyperion Biotechnology, Resolution Think, and The Geneva Foundation.
[^kbr]: [KBRwyle Provides Holistic Care to U.S. Special Ops Forces and Their Families under New Contract](https://www.kbr.com/en/insights-news/stories/kbrwyle-provides-holistic-care-us-special-ops-forces-and-their-families-under). Staffing includes clinical psychologists, social workers, physical therapists, athletic trainers, nurses, dietitians, strength and conditioning coaches, and data scientists.
[^gap]: [GAP Solutions Receives $100M+ Contract Award for US Army Holistic Health & Fitness](https://www.gapsi.com/gap-solutions-receives-100m-contract-award-for-us-army-holistic-health-fitness/).
