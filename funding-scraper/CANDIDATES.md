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

## Promoted to the board — 28 Sep 2026

| Now on the board | Award | Window |
|---|---|---|
| **PenFed Foundation** Veteran Entrepreneur Program (Accelerator / Incubator) | free place, travel covered, **zero equity**; Accelerator feeds a year-end pitch competition for non-dilutive funding | rolling, reviewed monthly |
| **IVMF Military Founders Lab** (Syracuse) | free 10-week virtual programme, no cash | 3 cohorts a year; next intake winter 2027, dates unposted |
| **Veterans Business Battle** (Rice University) | **$30,000** non-dilutive split between the top three, plus investors with earmarked capital | 2027 window unposted; the 2026 early window ran 2 Sep – 10 Nov |

PenFed is the find. It is the only item on the board whose only hard gate is one
Vybe has already confirmed — majority veteran-owned — and it costs nothing:
no fee, no equity, flights and hotels paid. An unsuccessful application is held
on file for a calendar year, so there is no window to miss. Drafted the same day
as the `penfed` packet, against the real form, which turns out to be readable
end to end without an account.

The Military Founders Lab matters for the same reason Veteran Shark Tank did: its
revenue test is a **ceiling** (under $250K in the last 12 months, or pre-revenue
with confirmed capital), where most veteran programmes set a floor. Its cohort
tracks include Women Founders and Black Founders — three of Vybe's confirmed
categories in one programme.

## Removed from the board — 28 Sep 2026

Both were rows this file helped put there, and both came off after reading the
programme's own page rather than its summary:

- **Paratus Digital Health Accelerator (BARDA network)** — the board carried
  `close_date = 2027-01-15` with the note "closes 15 Jan, annually". MATTER's own
  page says the preliminary application was due **15 January 2026**, that awards
  were announced in June 2026 and that funding began that summer. No 2027 window
  is published anywhere on it. The date on the board was extrapolated from the
  word "annually" — which is the same failure as a stale deadline, wearing the
  clothes of a live one. Reading further kills it on fit as well: the funding
  buys a **proof-of-concept study at a partner study site**, for detecting
  infectious disease and CBRN exposure, "enabling earlier diagnosis and
  intervention". That is a diagnostic posture and a trial arm, neither of which
  Vybe has. PR #20 called this "the closest programme fit on the board"; that
  claim does not survive the page.
- **Boundless Futures Foundation — EmpowHer Grant** — up to $50,000, real, and
  opening 1 November, but the foundation's own submission manager restricts
  eligible businesses to those addressing **poverty, hunger or humanitarian aid,
  or sustainability and the environment**. Consumer health is not on the list,
  so the age ceiling that made this row attractive is irrelevant. It also
  requires existing revenue, a self-reported credit score and a third-party
  background check — none of which the row stated. Watch it only if the eligible
  categories change.

**Next row to inspect:** **MedTech Innovator Vantage (BARDA Accelerator
Network)** is still on the board, closing 15 Oct. It is the same network and the
same posture problem that just removed Paratus, and `DECKS.md` already records it
as a structural disqualifier for a deck. Read its own page before that deadline
and either state the medical-device gate on the row or take it off.

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

Dead or rejected on inspection, 28 Sep 2026:

- **Google for Startups Accelerator: North America** — genuinely equity-free and
  genuinely real, but the 2026 North America cohort was **AI for Energy** (grid
  modernisation, demand flexibility, energy affordability) and applications
  closed 30 June 2026. Google's own page also sets a **5+ employees** floor and
  asks for a CTO committed to every session. The Canada page says 2027 dates
  will be announced later this year. Recheck when a 2027 AI-First cohort with a
  theme Vybe fits is posted — and check the headcount gate first.
- **Visa She's Next** — the 2026 programme was **Ireland only** (€90,000 across
  five winners, closed 6 April, 51% women-owned and €10K minimum revenue). Visa
  has run US cycles through iFundWomen in past years; no US 2026 window is
  posted. Worth a look each spring, not now.
- **Comcast RISE** — settled. `comcastrise.com` now serves Comcast's Project UP
  page, which describes RISE entirely in the past tense ("has supported 14,500
  small business owners") with no application anywhere on it. The board's
  standing judgement was right; this is the confirmation, dated.
- **Hiring Our Heroes Small Business Grant** — their own site no longer lists an
  entrepreneurship programme at all: the homepage offers hiring events,
  fellowships, a Skilled Trades Academy and career connectors. The grant is not
  merely between cycles, it is absent from the programme list. Drop it from
  Priority 3 unless it reappears.
- **Founders First CDC — Pride Business Grant** — real, national, $1,000 plus a
  free programme place, and deliberately not added. Its gate is the founders'
  LGBTQIA+ status, which nobody has stated and which is not something a board
  row should invite a claim about. If the founders say it applies, it is a
  one-line add.
- **Founders First CDC — Kitty Fund Mom Business Grant** — same shape, $1,000
  plus a programme place, gated on mother-owned. Left in the queue rather than on
  the board because that gate is unconfirmed for Vybe. Sister programme to the
  Tadlock grant already on the board, so the application is a known quantity.

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
