# Candidate queue — NOT on the board

Every row here is a lead, not an opportunity. Nothing moves from this file to
`sources.toml` until `probe-candidates.yml` has read the programme's own page
from a runner and confirmed three things: it is still running, its deadline,
and its eligibility gate. That rule is why the live board carries no expired
entries, and it is not relaxed for a large number.

Direct fetches from the sandbox still fail (the egress proxy returns
`EGRESS_BLOCKED` for almost every host), but a **server-side fetch tool reads
these pages fine** — that is how the 24 Sep rows below were confirmed against
each programme's own site rather than against a listicle. Use it. Anything in
this file that has not been through it is still **unverified**: treat every
figure as a claim to check.

The 24 Sep pass is the argument for the rule: of nine leads read first-hand,
four were dead — one organisation's site was a parking page and another's
domain had been taken over by a gambling site, while both still appear on
current "best grants for veterans/women/minority founders" listicles.

Eligibility confirmed by Jeremy 2026-09-20: Vybe Health qualifies as
**veteran-owned, woman-owned and minority-owned (51%+)**. That opens a
category the board had barely searched — it held 11 restricted rows out of 107.

## Promoted to the board — 24 Sep 2026

Read first-hand from each programme's own site, then added to `sources.toml`:

| Now on the board | Award | Window |
|---|---|---|
| **Buckeye State Credit Union** Small Business Recovery Grant | **$200K / $150K / $125K** | closes 30 Sep 2026 |
| **Tory Burch Foundation Fellows** — 2027 Program | fellowship place, free to apply | 22 Sep – 17 Nov 2026 |
| **Boundless Futures** EmpowHer Grant | up to **$50,000** | opens 1 Nov 2026 |
| **The Rosie Network** Service2CEO | free training, no cash | rolling cohorts |

The **Stephen L. Tadlock Veteran Business Grant** was already on the board as a
stub pointing at grantwatch.com with "varies" for an amount. It now carries the
programme's own URL, dates (15 Sep – 15 Oct 2026) and terms.

## Promoted to the board — 25 Sep 2026

| Now on the board | Award | Window |
|---|---|---|
| **Veteran Shark Tank 2026** | **$50,000** to the winner | closes 13 Oct 2026 |
| **AARP AgeTech Collaborative** Startup Accelerator | free, no equity, no cash | rolling cohorts |
| **IFW by Honeycomb** Universal Funding & Grant Application | varies by sponsor | standing |

Veteran Shark Tank is the find: its age test is a **ceiling** (under three years on
7 Dec 2026), the opposite of every other veteran programme's minimum trading
history, so a company too young for Buckeye or Tadlock clears it. Drafted as the
`sharktank` packet the same day.

## Priority 2 — women-founder

| Candidate | Claimed award | Gate | What to confirm |
|---|---|---|---|
| Fearless Fund | $20,000 | Black women founders | "Next cycle forthcoming" — is there a live cycle? Note the 2024 litigation settlement changed how this fund can gate on race |
| iFundWomen grant marketplace | varies by sponsor | women-owned | Which sponsor grants are live now |

## Priority 3 — veteran

| Candidate | Claimed award | Gate | What to confirm |
|---|---|---|---|
| Hiring Our Heroes Small Business Grant | 4 × $10,000 + 1 × $25,000 | veteran / military spouse, 3–20 employees, ≤$5M revenue | Real programme, but the 2026 cycle closed 15 Dec 2025 and no 2027 window is posted. Worth watching — check again around Oct/Nov |
| IVMF Military Founders Lab / CEOcircle (absorbed Bunker Labs) | programme, funding unclear | veteran / military spouse | Whether it carries cash or is training-only. Training-only still gets a row, labelled as such |

## Priority 4 — minority / general

| Candidate | Claimed award | Gate | What to confirm |
|---|---|---|---|
| Transform microgrant | microgrant + year-long programme | marginalised founders | Amount and cycle |
| MBDA Business Center network | advisory, some capital access | minority-owned | Whether any centre runs a direct grant |

## Explicitly rejected, do not re-add

Dead on inspection, 24 Sep 2026 — each of these still headlines the listicles:

- **Google for Startups Black Founders Fund** and **Latino Founders Fund** —
  Google's own Founders Funds page is written entirely in the past tense
  ("provided more than $58 million", "supported 600+ founders"). No open US
  round. These were Priority 1 on this list; they are not opportunities.
- **SoGal Black Founder Startup Grant** — `sogalfoundation.org` serves a
  Squarespace "We're under construction" parking page. The organisation's web
  presence is down; a rolling grant you cannot apply for is not rolling.
- **StreetShares Foundation Veteran Award** — `streetsharesfoundation.org` now
  resolves to a gambling site. The domain has been taken over. Never link it.
- **Black Ambition Prize** — its own application page says it is "not accepting
  new applications for the Prize Competition in 2026" and is instead backing
  founders already in its portfolio.
- **Nasdaq Milestone Makers** — free and real, but themed CleanTech, and as of
  25 Sep its own page still advertises a cohort whose applications closed
  **27 October 2025**. Recheck when the theme rotates AND the page is current.

Dead on inspection, 25 Sep 2026:

- **FedEx Entrepreneur Fund** (FedEx + Hello Alice + GEN) — **closed.** Hello
  Alice's own page says so in the first line, and FedEx Cares has already
  announced the 2026 graduates. An aggregator was showing "deadline November 21,
  **2026** — 85 days remaining"; the real deadline was 21 November **2025**. This
  is the second aggregator date-shift caught in two days. Note it is also a
  different programme from the retired FedEx Small Business Grant Contest, so
  "FedEx" appearing on a board row is not automatically the dead one — check
  which.
- **SoGal Black Founder Startup Grant** — the 24 Sep note said
  `sogalfoundation.org` serves a parking page, which is still true. Re-checked
  from the other direction: `iamsogal.com` does resolve and the Foundation
  exists, but the site shows no grant programme and its contact block still
  reads `your@emailaddress.com`. So the grant is not applicable-for rather than
  provably discontinued. Leave it off the board; revisit only if a working
  application page appears.
- **Makers Mindset × The Equity Studio** — open (9 Sep – 9 Oct 2026), $10,000 ×
  5, women-owned, no fee. Rejected on fit, not integrity: eligible categories
  are beauty and wellness CPG — supplements, ingestibles, skincare. Vybe is a
  wearable and an app, not a consumer packaged good.

Standing rejections:

- **Secretsos Small Business Grant** — charges an application fee. Already on
  the board; flag it so the fee is visible before anyone applies.
- **Outta Excuses** — application fee.
- **HerRise Microgrant**, **Hey Helen Grant**, **Freed Fellowship**, **Women
  Founders Grant** — all charge $15–$25 per application. NerdWallet's Sep 2026
  roundup also lists a **$15 fee on the Amber Grant**, which is already on the
  board with no fee noted — worth confirming on WomensNet's own page next sweep.
- **NASE Growth Grants** — no application fee, but requires paid NASE
  membership, which is the same barrier wearing a different hat.
- Any programme requiring a clinical trial (see the blocklist in
  `sources.toml`): Vybe has no trial arm, no IRB, no clinical infrastructure.
