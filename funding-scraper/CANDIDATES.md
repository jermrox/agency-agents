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

**MedTech Innovator Vantage — read the same day, and removed.** It was flagged
here as the next row to inspect; its own page settles it. The programme funds
"the development, evaluation, and validation of **diagnostic and medical device
technologies**", and states outright that "BARDA primarily develops medical
countermeasures to counter acute threats and **does not support research and
development or acceleration in the areas of oncology or chronic disease**".
Its named interests are acute radiation syndrome, Botulinum toxin serotypes,
femtomolar point-of-care assays and pathogen-ID sequencing. Vybe is a consumer
wellness product about everyday recovery, with no device classification and no
diagnostic claim — by product rule, not by omission.

The row's own note was the real problem. It read: "frame Vybe's continuous
physiological monitoring as early-signal detection." That is a board row
coaching a founder to dress a wellness product as a diagnostic to fit a
countermeasure programme — the opposite of what this file exists for, and the
same misframe `DECKS.md` had already rejected for a deck. Dates were not the
issue: 1 Sep – 15 Oct 2026 is correct, awards Mar–Apr 2027. Fit was.

**The MedTech Conference Start-Up Pitch — corrected, not removed.** Reading it
in the same pass found the opposite kind of error. The board had it as "medical
device and medtech startups", rolling, "cash award + conference pass". Its own
page says the competition is scoped to a **military-focused application of
medtech, diagnostics, digital health or imaging** — digital health named
explicitly, and military focus is the category Vybe is strongest in — for
companies that have **raised under $10M**, with **$7,500** to the winner. And it
is not rolling: the 2026 applications **closed 6 August** for the 18 October
event in Boston, so a row carried as "apply any time" was quietly unwinnable for
seven weeks. The 2027 window is unposted; on this year's pattern it is a
June–July job. Selected companies still pay $750 to attend.

## Promoted to the board — 29 Sep 2026

| Now on the board | Award | Window |
|---|---|---|
| **Army xTech\|Search 10** | up to **$1,000,000** in non-dilutive prizes, plus a Phase I SBIR/STTR worth up to **$300,000** | white paper due **19 Oct 2026**, 5pm ET |
| **Freed Fellowship Grant** | $500 a month, plus a $2,500 end-of-year grant | rolling, one Fellow selected monthly |
| **Kinetic — Health Care Innovation in Motion** (Bounce Innovation Hub × NEOMED, Akron) | no cash — services, EIRs, free coworking | rolling; no intake window published |

xTech|Search 10 is the find, and it is the largest non-dilutive item this board
has ever carried. It is **open-topic**, so there is no stated problem to contort
the product into, and one of its four published priority portfolios is
*"Immersive and Wearables: smart electronic devices that can be worn by or
attached to the user to gather data or provide insight"* — Vybe's category,
written by the Army. Money lands early: $5,000 at semifinal, which up to 50
companies reach.

**The gate to read before writing a word.** The competition excludes
technologies falling *exclusively* within the U.S. Army Medical Research and
Development Command portfolio — military operational medicine, clinical and
rehabilitative medicine, infectious disease, CBRN. A defence application invites
a founder to sound more serious by sounding more clinical, and here that is the
sentence that makes the submission ineligible. Vybe's honest position — a
commercial consumer wearable with a dual-use readiness application, no device
classification, no diagnostic claim — is both true and the only one that clears
the exclusion. This is the same failure mode `DECKS.md` rejected for the MedTech
Innovator row, arriving from the opposite direction.

Drafted the same day as the `xtech` packet. The RFI PDF was not readable from
here, so the packet is built against the four things the competition's own page
says it weighs, and says so in its note rather than guessing at section headings.

**Kinetic is on the board for location, not money.** Bounce is in Akron, which is
where the company is, and the offer is free coworking, entrepreneurs-in-residence
and discounted professional services. Its published outcomes are about regulatory
pathways and FDA submissions; Vybe has neither and should not acquire one to
qualify, so the row says the fit is the commercialization half. Two unknowns the
page does not answer: there is no application form, and startups inside their
"Launch Pad period" are excluded from the free services.

## Rejected on inspection — 29 Sep 2026

- **Cartier Women's Initiative** — real, large ($100K/$60K/$30K to nine regional
  and three thematic fellows), free, and the Science & Technology Pioneer Award
  would fit. Its own awards page says *"Applications are now closed for the 2027
  edition"* and publishes no date for the next one. Not a board row until a
  window is posted; on the published pattern that is a spring job. Worth a diary
  note, not an entry.
- **Founders First Capital Partners** — rejected on fit, not integrity. Its own
  page sets the floor at **$500K to $10M+ annual revenue** and serves
  service-based B2B or B2G companies. Vybe is pre-revenue consumer hardware. The
  capital is also revenue-based loans and term loans, not grant money.

## Promoted to the board — 30 Sep 2026

The board held exactly one Ohio row before today, which was a gap: the company
operates from Akron and two of the three rows below are state or regional money.

| Now on the board | Award | Window |
|---|---|---|
| **Ohio Third Frontier TVSF Phase 2 — Start-Up Fund** | up to **$200,000**, a grant, no cost share required | quarterly; Round 46 closed 6 Aug, next RFP ~late Oct |
| **Innovation Fund (Northeast Ohio)** — GLIDE / LCCC Foundation | "A" up to **$50,000**, "B" up to **$150,000**, matched dollar-for-dollar | quarterly cycles |
| **DAV Patriot Boot Camp** | free three-day programme; cohort pitch contest was **$10,000** non-dilutive in spring 2026 | cohorts several times a year; next window unposted |

**TVSF is the big one and Vybe cannot apply for it today.** Phase 2 exists to move
technology *out of* Ohio research institutions and into startups, so the project's
technology must be one the company has licensed — or intends to license — from an
Ohio university, an Ohio not-for-profit research institution or a federal lab, and
it must already carry IP protection. A company that built its own stack has nothing
to propose. It earns a row anyway because this is a gate Vybe could clear on
purpose rather than by luck: the Round 44 award list includes the University of
Akron Research Foundation, and the Kinetic programme added to the board yesterday
is a partnership with NEOMED. A licence taken to qualify for a grant would be a bad
idea. A licence Vybe actually wants would open a $200,000 round every quarter.

**Innovation Fund has one unanswered question and it is the important one.** The
fund calls these "awards" and also calls itself a pre-seed investor with
"portfolio companies" expected to give back "educationally and financially".
Nothing on its public pages says whether the money is a grant, a note or equity.
This board is for non-dilutive funding, so that is the first question to GLIDE, not
the last. Its published figures also conflict — GLIDE's own support pages still
show $25,000 and $100,000 against the fund's $50,000 and $150,000 — and the
dollar-for-dollar match means a $50,000 award needs $50,000 of Vybe's own money
already committed.

**Patriot Boot Camp has the lowest bar of any veteran programme here.** Revenue and
raised capital are explicitly *preferences*, not requirements, and an EIN and
website are preferred rather than required — unusual enough to be worth saying.
Free, spouses included, and the pitch contest at the end is the cash. No window is
posted: the June 2026 Salt Lake City cohort has been and gone, so today's action is
the mailing list, not a deadline.

## Corrected on the board — 30 Sep 2026

**Ohio TechCred** was carried with the eligibility line "OHIO-BASED EMPLOYERS
ONLY", which understates the gate badly enough to waste a week. The real test is
four things: Secretary of State registration, a **physical, non-residential**
business location in Ohio, Ohio-resident **W-2** employees reported to Ohio
unemployment insurance, and Ohio income tax withheld for them. Contractors and 1099
workers count for nothing, and an employer exempt from those reporting requirements
is not eligible at all. A three-person startup working from a founder's house, or
one whose founders draw no W-2 wage, fails on the address and the payroll before
any credential is chosen — and the reimbursement stage asks for each earner's wage,
hire date and W4/IT4 verification, so it is not a gate that can be finessed later.

The programme was also reframed in **July 2026** with a tighter technology-focused
credential definition, updated employer eligibility and a **new** eligible-provider
list, so any provider picked from older advice needs re-checking. Window: 9:00am
1 Oct to 3:00pm 30 Oct 2026. Drafted the same day as the `techcred` packet.

## Rejected on inspection — 30 Sep 2026

- **Fast Break for Small Business** (LegalZoom + Accion Opportunity Fund + NBA /
  WNBA) — **dead.** Accion's own programme page says it "began in 2021 and closed
  for the final time in 2024". It was a $6M multi-year commitment with $10,000
  grants and it is finished; "details about future programming will be available
  soon" has been the line since. This is the third aggregator-fed lead in a week
  whose real status is closed. Do not re-add without a live application page.
- **SOFWERX Tech Tuesday** — real, free, and the cheapest door into USSOCOM human
  performance, which is the category Vybe is strongest in. Kept off the board for
  one reason: its own page says **"New Tech Tuesday submissions are currently
  paused"** while it works through the queue. A forum you cannot submit to is not
  an opportunity. Watch it — the forum itself is still running weekly, so the pause
  should lift. Note also that SOFWERX's homepage advertises a 30-minute slot while
  the Tech Tuesday page says 20 minutes (10 present, 5 Q&A); the programme page is
  the one to believe. Submissions go through Submittable when they reopen.

## Status derivation — verified live, 1 Oct 2026

The `forecast` state built on 28 Sep had its first unattended test today, and it
passed on both sides of the pipeline. Verified by running `models.py` and the
dashboard's own `classify()` over the same three rows across the date boundary:

| Row | 30 Sep | 1 Oct |
|---|---|---|
| **Ohio TechCred** (opens 1 Oct, closes 30 Oct) | `forecast`, 1 day until open | `soon`, 29 days left, `days_until_open` null |
| **Buckeye State CU** (closed 30 Sep) | `soon`, 0 days left | `closed` |
| **Amber Grant** (closed 30 Sep) | `soon`, 0 days left | `closed` |

Both implementations agree on all three rows and all three transitions. The
dashboard re-derives from the live clock rather than reading the stored `status`,
so the page was correct this morning even though `output/funding.json` still
carried `as_of: 2026-09-30`. That is the behaviour the 28 Sep work was for.

**One caveat worth knowing.** The stored `status` field in `funding.json` *is* a
day stale until the sweep runs. The dashboard does not use it, but anything else
reading that field directly will be behind by up to a day. Re-derive, do not read.

**And one real bug the check found.** The **Amber Grant** closes on the last day
of EVERY month. Its row carried `close_date = 2026-09-30`, so the derivation
published it as `closed` on 1 October — correct arithmetic, wrong answer, because
the programme had simply rolled to its next monthly round. A falsely dead row on a
live programme is the same failure as a stale deadline, pointing the other way.
Rolled to `2026-10-31`; the next roll is due 1 November. Until the model carries a
recurrence rule, any monthly row needs advancing on the first of the month — Amber
is the only one on the board today.

The **Buckeye** row is genuinely closed and stays on the board for the record, but
its note still read "CLOSES 30 SEP — six days out". Prose that counts down does not
survive the date it was written on; rewritten in the past tense.

## Promoted to the board — 1 Oct 2026

| Now on the board | Award | Window |
|---|---|---|
| **DoW SBIR / STTR Specific Topics — Release 6** (26.BX / 26.BZ / 26.TX / 26.TZ) | Phase I feasibility, then Phase II prototype; non-dilutive contract money | **closes 21 Oct 2026** |
| **Ohio Centers of Excellence** (JumpStart, Ohio Third Frontier) | no cash — rolling intake to advisors and the state's non-dilutive programmes | rolling |
| **Ohio MBDA Business Center** (US Commerce, Cleveland) | no cash — free consulting, grant identification and packaging | rolling |
| **Ohio Minority Business Assistance Centers** (Ohio Dept of Development) | no cash — free counselling, certification, procurement help | rolling |

**The Centers of Excellence row is the answer to yesterday's TVSF problem.** TVSF
Phase 2's $200,000 is blocked because the technology must be licensed from an Ohio
research institution, and this network is how that introduction happens rather than
something to arrange cold. Its named Regional Startup Ambassadors include **Bounce
Innovation Hub** (Akron — on this board via Kinetic) and **GLIDE at Lorain County
Community College** (which administers the Innovation Fund — also on this board).
Three rows added over three days turn out to be one system with one front door.

**The DAF window is reading work, not writing work.** Eligibility is the same test
Vybe passed for xTech|Search 10 — for-profit, under 500 employees, majority US
citizen owned *and controlled*, dual-use — and 26.BX is literally the solicitation
family xTech's follow-on topic sits in. But these are **Specific** topics, so the
only question that matters is whether any Release 6 topic fits a consumer wearable
without requiring a clinical or diagnostic posture. Read the DSIP topic list before
drafting a word. **No Open Topic cycle is currently published**, and Open Topic is
the one that takes any dual-use technology — that is the thing to wait for if
nothing in Release 6 fits.

**The two minority-business centres differ in a way that matters.** The federal
MBDA definition (15 C.F.R. 1400.1) has no state-residency test and no minimum time
in business, so Vybe qualifies today. Ohio's own MBE definition requires the owner
to be an **Ohio resident** who has held the 51% **for more than a year** — so formal
Ohio MBE certification, and the 15% state-contract set-aside behind it, is likely a
2027 conversation. The free counselling at both is open now either way.

## Corrected on the board — 1 Oct 2026

**Veterans Business Battle** — corrected against this board's own row, on the date
the 28 Sep note said to re-check it. Rice's page today still advertises the **12th
annual** competition, 8–9 April 2026, and says "Applications to compete are closed
as of January 31, 2026". It still lists the 2025 winners. So the "13th annual" this
board claimed was an extrapolation rather than something Rice published, and the
"$30,000 split between the top three" figure is not on the page either. Both have
been removed from the row. What the page does support: the largest veteran-only
business competition in the country, $10M+ of investment extended since 2015, free
to apply, two-day in-person final in Houston, and 2025 winners spanning health
tech, agriculture and consumer hardware. Check again in November for an autumn
window.

## Rejected on inspection — 1 Oct 2026

- **JumpStart Trailblazer HealthTech Accelerator** — genuinely good and genuinely
  closed. **$50,000 of fully covered services** through their Preferred Partner
  Program, three months plus two months of EIR advising, no fee and no equity. Its
  own page says "Applications are currently closed. Please check back soon!" Also
  worth knowing before it reopens: candidates are scored on "the likelihood of a
  venture capital raise within 12 months", and the programme describes itself as
  preparing companies for "their next dilutive fundraise" — a philosophical mismatch
  with a buy-once product, though not a disqualifier. Watch for the next cohort.
- **Hello Alice funding portal** — could not be read today (the fetch failed, not a
  404). The platform row already on this board stands; re-check whether a live
  partner grant exists before treating it as actionable.

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
