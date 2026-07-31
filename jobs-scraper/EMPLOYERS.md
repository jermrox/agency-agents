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

| Employer | Program | Award | Announced | Status | Evidence |
|---|---|---:|---|---|---|
| **Serco** | Army H2F | $247M ceiling | **Jan 2025** | Current | [Serco][^serco] |
| **KBR** (KBRwyle) | USSOCOM POTFF | $500M | **Dec 2018** | ⚠ Dated | [KBR][^kbr] |
| **GAP Solutions** | Army H2F | $100M+ | **Aug 2021** | ⚠ Expired | [GAP Solutions][^gap] |
| **HigherEchelon** | Army H2F (Team Serco) | subcontract | Jan 2025 | Current | [^serco] |
| **Hyperion Biotechnology** | Army H2F (Team Serco) | subcontract | Jan 2025 | Current | [^serco] |
| **Resolution Think** | Army H2F (Team Serco) | subcontract | Jan 2025 | Current | [^serco] |
| **The Geneva Foundation** | Army H2F (Team Serco) | subcontract | Jan 2025 | Current | [^serco] |

> **Read the dates.** An earlier version of this file listed these awards without
> them, which implied all three were live contracts. Opening the primary sources
> corrected that:
>
> * **KBR's POTFF award is from December 2018** — a five-year base plus a
>   three-year option, so roughly 2018–2026. POTFF has since gone to recompete
>   (POTFF III), which makes KBR an incumbent and likely bidder rather than a
>   confirmed current holder.
> * **GAP Solutions' H2F award is from August 2021** — one base year plus two
>   option years from September 2021, so it ran to about late 2024.
>
> Only the Serco award is recent. All three still identify *who competes for
> this work*, which is what the watchlist needs — but "who won in 2018" and
> "who is hiring now" are different claims, and this table previously blurred
> them. This is exactly the gap `contracts.py` closes by querying live award
> data instead of relying on press releases.

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

USASpending publishes under the **DATA Act**, the law requiring federal spending
information to be publicly accessible — which is why award reads need no account
and the weekly watch costs nothing to run.

---

## Why board tokens are not secrets

The claim that an ATS "board token" is a public slug rather than a credential is
load-bearing for the whole keyless design, so here is the vendor stating it.

Greenhouse's Job Board API documentation describes the endpoint's purpose as
giving third parties "a simple JSON representation of your company's offices,
departments, and published jobs" so they can "build careers pages", and says
plainly:

> Only the application submission endpoint … requires Basic Auth.

Reading jobs is unauthenticated **by design**; only *writing* an application
needs a key. — [Greenhouse Job Board API](https://developers.greenhouse.io/job-board.html),
[Lever Postings API](https://github.com/lever/postings-api)

By contrast, [USAJOBS](https://developer.usajobs.gov/tutorials/search-jobs)
requires `Host`, `User-Agent`, and `Authorization-Key` headers plus a key
obtained by application — which is why it is one of only three credentialed
adapters out of 23.

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
