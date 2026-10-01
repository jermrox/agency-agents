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

## Promoted to the board — 1 Oct 2026 (wearable sweep)

A sweep aimed only at health-wearable money that a pre-revenue company can file
without a trial, a fee or a licence. Most leads were already closed; three were not.

| Now on the board | Award | Window |
|---|---|---|
| **NIH NOURISH Autoimmunity Digital Health Challenge** — Phase 1 | up to 10 × **$20,000**; $650K across three phases | opened 1 Oct; package due **11 Dec 2026** (page header says 8 Jan 2027) |
| **AgeTech After Dark @ CES 2027** (AARP) | **$10,000** grand prize + CES tickets for finalists | closes **12 Oct 2026** |
| **CES 2027 Eureka Park** | booth, no cash — **paid**, price unpublished | rolling until sold out |

NOURISH is the best wearable fit found in weeks: NIH's own scope list names
smartwatches, fitness trackers and biosensors for heart rate, sleep and activity
alongside AI diet insights. It is a prize, not a grant, so none of the federal
registrations gate it.

## Corrected on the board — 1 Oct 2026

**Xcelerate (WHX Tech)** was carried with no deadline and no mention of its real
gate. The deadline is **4 Nov 2026**, and only startups holding a confirmed
**WHX Tech Startup Pod** — a paid exhibitor package, price not published — are
shortlisted. The pitches are in Dubai, 26–28 Jan 2027, at the startup's own travel
cost. The row now says all of that.

## Rejected on inspection — 1 Oct 2026 (wearable sweep)

- **DARPA "Engineering Sleep for Cognitive Performance"** (DPA26BZ03-DV012) — a
  wearable closed-loop sleep topic, as close to Vybe as a DoD topic gets. Ran
  24 Jun – 22 Jul 2026 and was **missed** because the `dod_sbir` source has 403'd
  for weeks. The structural fix is to read each monthly DSIP release by hand until
  that source works. **DoD FY26 Release 6** (opened 23 Sep, closes 21 Oct) was read
  in full and has no wearable or human-performance topic.
- **eWEAR Health Prize @ Stanford** ($25K) — closed 25 Sep, and the founder must be
  **18–35** on 6 Nov 2026. Watch for the 2027 cycle only if a founder fits the age gate.
- **2026 Health Security Innovation Prize Challenge** (TechConnect, $200K, lists
  wearable biosensors) — **closed 23 Mar 2026**; pitches were 12 May. CBRN-defence
  framed. Re-check around February 2027.
- **AgeTech Open Mic (Oct and Nov)** and the **Making Aging Easier pitch @ HLTH** — closed
  30 Sep and 26 Jun. The CES pitch above is the live one.
- **AHA Health Tech Competition** — closed 18 Sep, and it wants clinical or pilot
  data plus paying customers.
- **NurseHack4Health** — closed 21 Sep, nurse-led teams only.
- **KU / Garmin Wearable Insights** — closed, academic.
- **Samsung Mobile Advance 2026** — closed.
- **TOPx HHS Tech Sprint** — Phase 2 is only for teams selected in Phase 1.
- **HHS All-American Fitness Challenge** — youth K–12 framing, current phase unclear.
- **J&J QuickFire Challenges** — none open for wearables today.
- **Women's Health Europe Forum pitch** — EU/UK-incorporated companies only.
- **VR Health Champions** (€60K) — European XR SMEs only.
- **Columbia Fast-Pitch**, **AMSA Digital Health Festival**, **UW–Madison Bradley
  Challenge** — student-only, or prizes too small to be worth a submission.
- **NNEMTC pitch** (Portland, ME, 12–13 Nov) — open to any early-stage digital
  health company, but the prize is in-kind only and no deadline is posted. Held
  back, not rejected; worth an hour if a regulatory-readiness review is wanted.

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

## Promoted to the board — 1 Oct 2026 (four-lane parallel sweep)

The founder's complaint was right: the automated sweep only reads federal APIs, so
everything it finds needs SAM.gov and most of it is off-topic. Four parallel searches
went after startup-relevant money instead, in four lanes:

- health-tech pitch prizes
- government prizes
- women-, minority- and veteran-founder programmes
- Ohio and corporate programmes

Every row below was read on its own page, and each carries a `sam` tag.

Added (13):
- 2027 NIA Start-Up Challenge
- Break the Barrier
- CharmHealth Innovation Challenge
- PM&R Pitch Tank
- Global Deep Tech Battle @ CES
- ARPA-H Proactive Health ISO
- USSOCOM human-performance BAA
- AFRL 711th HPW CHEERS
- eMerge NatSec Veteran Pitch
- Clemson Blake Family Military & Veterans Pitch
- VETCON Business Plan Competition
- Halcyon
- UARF I-Corps (Akron)

**Watch list — real, but no open window or no cash today:**
- MedTech Innovator 2027 (last cycle opened 6 Oct; re-check mid-October)
- ASICS Kenzen ($40K, wearables and sleep; 2027 cycle)
- Rev1 Customer to Capital (Spring 2027, opens "in the winter")
- USSOCOM Engage SOF (the capability list sits on an "Archive" page; confirm first)
- ST for Startups and Infineon Co-Innovation (in-kind; only if the Band uses their parts)
- NXP Startup Program (needs prior incubator funding)
- JumpStart's cohort closing 17 Nov (confirm which accelerator it is)
- Delaware rural health-tech (Q1 2027)
- ONR long-range research announcement successor

## Rejected on inspection — 1 Oct 2026 (four-lane parallel sweep)

- **SXSW Pitch 2027** — Application fee ($225 regular entry Sep 14 to Nov 13, 2026, non-refundable). Its product must also have launched before Jan 1, 2024, which Vybe fails.
- **AIMed26 Shark Tank** — Application fee ($100–$300) plus a $900 entry fee if selected. Applications also closed Sep 18, 2026.
- **Women's HealthX Startup Pitch Fest 2026 (Boston)** — Pay-to-pitch: the startup booth plus Pitchfest package costs $1,199, and the prize is only $1,000.
- **2027 Global Innovation in Women's Health Pitch Showcase (Aquillius, via F6S)** — The application form says an application fee is due on review before an applicant can advance.
- **Medical Innovation Expo Pitch Competition 2027** — Only for students enrolled at US institutions. It also charges a non-refundable application fee and targets FDA 510(k)-pathway devices.
- **MedCity INVEST Digital Health 2026: Innovation Showcase (Dallas, Oct 29)** — Visibility only, with no cash prize (the prize is an editorial feature). Accepted startups pay $495 admission, and no deadline is stated on the official page. The consumer and wearables theme fits, so it is still worth it if the team is going to Dallas anyway.
- **MedTech Innovator 2027 Accelerator** — Not open. The apply page says 2026 applications are closed and offers a notify-me list for 2027. No 2027 dates are published; the 'Deadline: December 1, 2026' text on that page appears to be a stale 2025 date. Re-check mid-October, because last cycle opened Oct 6. It is free, equity-free and has up to $350K in awards.
- **MassChallenge Healthcare Challenge / Traction 2027** — Not open. The site says 'Applications for the 2027 program later this year' and gives no dates.
- **ViVE 2027 Startup Pitch Competition (Nashville, Mar 14–17, 2027)** — The page still shows 2026 information and no 2027 application or deadline is posted. Watch it: the requirements are under 5 years old and under $8M raised.
- **HIMSS27 Emerge Pitch Competition** — No 2027 application window or deadline is posted. Categories target hospital-system and payer operations, which is a poor fit for a consumer wearable.
- **NFLPA Pitch Day 2027** — Not announced ('Stay Tuned for Pitch Day 2027 Announcements'). The prize is event access and mentoring, not cash. Watch it: past winners include Whoop and the Somnee sleep wearable.
- **SPORT[GEN] Summit — The Draft 2027** — Not open until Feb 18, 2027 (closes Apr 24, 2027). The event location is not stated on the page and there is no cash prize.
- **ASICS Kenzen 2026** — Closed Jul 30, 2026. It is a strong fit for the future ($40K/$25K/$10K cash, US-incorporated, wearables, sleep and recovery categories), so watch for the 2027 edition.
- **SFIA Start-Up Challenge** — No current application window or deadline is published on the page.
- **MIT Sloan Healthcare Innovations Prize (SHIP)** — No 2027 dates or application window are published on the page.
- **Johns Hopkins Healthcare Design Competition** — Student-only. The page says projects run by startup companies are ineligible.
- **Hollomon Health Innovation Challenge (UW Foster)** — Student-only (Cascadia Corridor students), and non-students cannot receive prize money.
- **Wells Student HealthTech Challenge (Pitt)** — Only for University of Pittsburgh students, and it closed Aug 30, 2026.
- **Global Health Innovation Grand Challenge 2027 (Carle Illinois / GCIEM)** — Framed as university student-team competitions, with no prize amount stated.
- **Women's Fast Pitch 2026 (Women's Venture Summit)** — Closed Sep 16, 2026.
- **Wharton Healthcare Alumni Pitch Competition 2026** — Closed Sep 25, 2026, and applicants are sourced through Wharton/Penn alumni networks.
- **Rural Health Innovation Challenge (AgeTech Connect @ GSA)** — Requires a commercially available product and verifiable customers. Vybe is pre-revenue.
- **FDA READI-Home Innovation Challenge** — Closed Sep 30, 2026. It requires a regulated medical device via a Q-submission and gives no money.
- **ARPA-H REST (Restorative & health-Enhancing Sleep Time)** — Requires clinical-fidelity diagnosis of insomnia or poor sleep and clinical-trial-grade teaming. Solution summaries were due Aug 12, 2026, and full proposals are by invitation only.
- **2Flo Ventures Health Equity Pitch Competition 2026** — No event date or application deadline is stated, and the Luma event is not taking registrations.
- **NBA Foundation All-Star Pitch Competition 2027** — Not open ('Applications for 2027 will open in the Fall'), and past editions targeted entrepreneurs local to the host market.
- **Comcast NBCUniversal SportsTech Accelerator** — Takes equity, and no 2027 window was confirmed on the official site.
- **MedStartr 2026 Grand Challenge** — The prize investment is subject to an equity agreement.
- **47Pitches HealthTech 2027** — Charges equity: a 0.5% platform fee plus 1.0% for top-3 finishers.
- **Pitch Black (We Pitch Black) 2027** — Only for businesses formed in Nebraska or Iowa.
- **Flywheel Investment Conference 2027** — Requires a presence in Washington State, and the winner's award is a convertible-note investment.
- **Health 2.0 Conference USA 2027** — No startup competition with a published application. Startup stage time is sold through sponsorship and exhibitor packages.
- **DMEA nova Award 2027** — Non-US event (Munich, Apr 2027) with a €3,000 cash prize.
- **Xcelerate @ WHX Dubai 2027** — Non-US (Dubai). It also requires a paid WHX startup pod to be eligible.
- **ICT&health World Conference 2027: The Most Innovative Session** — Non-US event (Maastricht, NL) with no cash prize stated.
- **Longevity 5.0 Pitch Competition & Call4Ideas (Rome)** — Non-US event (Rome, Jan 2027) with no cash prize stated.
- **Johns Hopkins Ward Infinity Impact Accelerator** — Closed (Jul 31, 2026), and it is for ventures in the Washington, D.C. metro region.
- **TMC Innovation Healthtech Accelerator** — No application window is published, equity and fee terms are unpublished, and it targets clinical and enterprise deployment.
- **ARPA-H REST (Restorative & health-Enhancing Sleep Time), ARPA-H-SOL-26-159** — Closed to new entrants. Solution summaries were due 2026-08-12 and are required to propose; full proposals (SAM.gov offers due 2026-10-13) are by invitation only. The program also targets diagnosing insomnia 'with clinical fidelity' and lists clinical trials and regulatory science, which conflicts with Vybe's no-diagnostic, no-trial position.
- **ARPA-H Delphi (wearable/ingestible biosensor chiplets), ARPA-H-SOL-26-153** — Closed: solution summaries were due 2026-04-08 and proposals 2026-05-13. It also includes a clinical-trial/human-factors technical area and requires SAM registration to propose.
- **ARPA-H SURPASS (ARPA-H-SOL-26-164)** — Open (solution summary due 2026-11-30), but it is about clinical-trial design, statistics and trial operations. That requires clinical-trial capability Vybe does not have.
- **ARPA-H 2026 SBIR/STTR topics** — Closed: Stage 1 solution summaries were due 2026-07-17. The topics (fertility test, bioadhesives, endometriosis, autoimmune diagnostics and others) are also diagnostic or single-disease.
- **ARPA-H ASCENT-IBO (via PHO ISO, summaries by 2026-10-15)** — Single-disease (opioid use disorder) Phase 1/2 ibogaine clinical trials. Clinical-trial requirement.
- **Army xTech|Disrupt Endurance (AUSA walk-up, 12–14 Oct 2026)** — Open, but off-topic: it seeks Soldier power generation and storage technology, not physiological monitoring. It also requires an in-person walk-up at AUSA in Washington, DC on Oct 12–13. No other xTech competition (other than xTech|Search 10, already listed) is accepting submissions; Kinetic Reach, Adaptive Strike and Apex Intercept are past their submission windows.
- **Navy STTR DON26TZ01-NV016 'Nudging Behaviors for Better Sleep' (COTS wearables)** — Closed 2026-06-03. It was a near-perfect topic fit, so watch for a follow-on. It was also STTR, which requires a research-institution partner.
- **Navy SBIR DON26BZ05-NV068 'Intelligent Tools for Naval Aircrew Performance and Readiness'** — Closed 2026-09-23 (DoW Release 5). Release 6 is already on the board.
- **USSOCOM / USASOC Sources Sought 'Wearable Safety & Physiological Monitoring Technology' (SWCS_Wearables)** — Closed: the response deadline was 2026-09-17. It was an RFI only (no award), and it required GPS, two-way comms, core temperature and SAM registration.
- **SOFWERX open assessment events (Contactless Iris Collection, Battery Bottle, Distributed Micro Sensors, 4 POG AI-PSYOP)** — None is about human performance or wearable physiology. Micro Sensors submissions closed 2026-08-28. Iris (opens 2026-10-27) and 4 POG (opens 2026-10-19) are biometric-ID and PSYOP topics. There is no current SOFWERX human-performance call; the 2024 NSWCEN Performance Monitoring Wearables demo day is long closed.
- **DIU AI Assisted Triage & Treatment Challenge ($999K)** — Closed 2026-03-02. It also required FDA 510(k) clearance before procurement and hemodynamic (medical) monitoring. No current DIU AOI covers wellness wearables.
- **DHA Enterprise-Wide Commercial Solutions Opening (HT003826SC005)** — This is a framework open to 2027-08-06 that only accepts responses to specific Areas of Interest. No AoI matching wearables or wellness could be verified on an official page today. Re-check later.
- **MTEC FY2026 Multi-Topic RPP (Focus Area 2: Service member physical fitness)** — Only current MTEC members may submit, and MTEC membership carries an annual fee. That counts as an application-fee barrier. Timing is also unverified.
- **ONR Long Range BAA N00014-25-S-B001** — Lapsing: 'The Government reserves the right not to review proposals submitted under this BAA after 30 September 2026 or after a successor ... is issued.' No FY27 successor could be verified today. Re-check for a successor.
- **NASA Artemis II Human Research Data Methodology Challenge** — Closed 2026-06-05; winners have been announced. No open NASA human-health challenge was found.
- **ACL Caregiver AI Prize Challenge** — Phase 1 closed 2026-07-31. Only Phase 1 winners may enter Phase 2.
- **ACL Health at Home Challenge** — Phase 2 is limited to Phase 1 winners, and the challenge is aimed at community care hubs and health-care organization partnerships, not device startups.
- **NIDA 'One-Step, Rapid, Low-Cost Definitive Drug Testing at the Point of Need' Challenge** — Open until 2026-12-15, but off-fit: it wants instruments to quantify illicit drugs, a diagnostic and lab domain.
- **2026 '$100,000 Start an SUD Startup' Challenge (NIDA)** — Open until 2026-11-02, but single-area (substance use disorder) and research-to-biotech oriented.
- **NIH Supplements, Facts First Challenge (Phase 2)** — Phase 2 runs until 2027-05-21 but only Phase 1 winners may enter. Phase 1 closed 2026-05-07.
- **NIH NEI Vision Precision Challenge / AYA Cancer Data / Kidney AI / OligoTox / SPARK and other open NIH challenges** — Single-disease or research-data challenges (vision acuity, cancer data, kidney imaging, oligonucleotide toxicity, literature AI) with no fit to a consumer wellness wearable.
- **VA Veterans Health Hackathon** — The official page shows no current dates or cash prize. The 2025–26 cohort has already moved to the Make-a-thon and Accelerator. No live window could be verified.
- **VA VHAIE Suicide Prevention BAA (36C10X24R0053)** — The concept-paper window ended 2026-09-30 (response date shown as 2026-09-15). It is also single-area.
- **JobsOhio Small Business Grant (formerly Inclusion Grant)** — Vybe fails the gates: 'annual revenues between $100,000 and $25 million' and 'at least one year of operating history'. It is also B2B-revenue and reimbursement-based for fixed assets. Revisit after a year of revenue.
- **Ohio Rural Health Transformation Program — Rural Health Innovation Hubs RFP (DOH59718)** — Closed 2026-09-01. It is also limited to Ohio providers and organizations with at least 5 years of delivering health services in rural counties. Ohio has no startup-facing Rural Tech Catalyst Fund.
- **Delaware Rural Health Tech Accelerator (Delaware Prosperity Partnership, RHTP-funded)** — Not open yet and no date has been published: DPP is still procuring an operator (proposals due Oct 5) and says startup applications 'will open later'. Winners must also establish a Delaware presence. Re-check in Q1 2027.
- **Louisiana Rural Tech Catalyst Fund (RTCF)** — Closed: 'This application is now closed' and Cohort 1 is under review. A year-2 window was reported but is not posted. Out-of-state winners must operate in Louisiana.
- **South Carolina SCRA Tech Catalyst Fund (RHTP)** — Closed 2026-06-25. It also requires SC Secretary of State registration, prefers SC-based companies and requires TRL 5+.
- **MassCEC InnovateMass (Fall 2026)** — Open until 2026-10-20 but clean-energy/climatetech only, and it requires relocating to Massachusetts.
- **Arch Grants 2026 Startup Competition** — Closed 2026-03-31. It also requires relocating to St. Louis for a year.
- **Ohio Third Frontier TVSF Round 46** — Round 46 closed 2026-08-06. It also requires licensing a technology from an Ohio research institution. TVSF Phase 2 is already on the board.
- **Urban One × National Urban League Community Business Pitch Competition (ONE Voyage)** — Deadline 18 Oct 2026, but the pitch happens live on the ONE Voyage cruise ('Attend the ONE Voyage Cruise and You Could Win'), so entry in effect requires buying a cruise ticket (an application cost). The prize is up to $100K of promotional support, not cash.
- **digitalundivided BREAKTHROUGH** — Requires $50K+ annual revenue, 1+ year registered and location within 100 miles of a program MSA. Vybe is pre-revenue and under 1 year old. The 2026 recruitment window (Mar–Apr) is closed, and the other digitalundivided programs show only a waitlist.
- **Heal.LA Bioscience & Healthcare Accelerator (Larta)** — No live window: the page offers only 'register your interest for our next cohort'. The program is also built around piloting in Los Angeles County communities.
- **Veteran Loan Fund — Veteran & Military Spouse Accelerator** — No live window. The page says 'Our first cohort is underway and a second is on the way. Tell us you're interested.' The main offer is loan capital; the $3K–$5K grant comes only on completion.
- **V-WISE 2027 (IVMF, women veterans)** — Not open. 2026 is sold out and 2027 has only an interest form (program Mar–Apr 2027, Atlanta). Training only, no cash. Recheck in Q1 2027.
- **Springboard Enterprises Women's Health / Longevity Accelerators** — Application fee ($100–$200) and a program fee if selected. Targets late-seed to Series B companies. The 2027 Women's Health cohort is waitlist-only.
- **The Vetted Accelerator (combat veterans, US/Israel)** — Equity investment model (Vetted Fund), not non-dilutive. Applications closed ('Notify me when applications open'). Requires combat-veteran status and two 10-day in-person bootcamps (Tel Aviv and Miami).
- **Blackbird Founders Fellowship (Blackbird Alliance × Grid110)** — Lead only (newsletter). It requires a revenue-generating venture and in-person attendance in Los Angeles for all six sessions. Deadline 7 Oct 2026. Vybe is pre-revenue and based in Ohio.
- **Amazon Black Business Accelerator** — The URL now redirects to a generic 'Amazon selling programs' page. No BBA program or application exists, and it was a seller-on-Amazon program in any case.
- **Brown Venture Group** — A venture capital firm (equity), and its site says it is 'not currently accepting unsolicited pitches'.
- **VetsinTech Startup Pitch Contest 2026** — Closed: applications were due 22 Jul 2026 and the final ran on 20 Aug 2026.
- **Women in AI Pitch Competition — NYC Fall '26 (Oasis Collective)** — Closed 7 Sep 2026. No later city stop with an open window was found.
- **Women Founders Network Fast Pitch 2026** — Closed 31 May 2026 and charged a $50 application fee.
- **Visionaries Pitch Competition 2026** — Closed 18 Jun 2026 and charged a $20 admin fee.
- **Google for Startups Women Founders Fund** — The page states 'There are no Women Founders Funds available at the moment.'
- **Innovate Forward: Women's Health Innovation Challenge (Nestlé Health Science × Tufts)** — Not open today (the next cycle opens 18 Oct 2026). It is narrowly themed on perimenopause/menopause, urogenital and metabolic health and is 'science-driven', which is a poor fit for a general wellness wearable. Recheck on 18 Oct if Vybe builds a menopause and sleep angle.
- **FemTech Breakfast Club 2027** — Canadian-incorporated companies only, and it closed 25 Sep 2026.
- **Go Vertical ICM Innovation Grant 2026** — $99.99 application fee; closed 19 Jun 2026; the prize is services, not cash.
- **Aspire Accelerator (Women's Center for Economic Opportunity, Ohio)** — $99 non-refundable application fee. Requires 3+ years in business and $50K+ revenue.
- **MassChallenge × BCBSMA Health Equity Business Accelerator (HEBA)** — The page covers the 2026 cycle, which ran its information sessions in Nov 2025. No 2027 application window or dates are posted.
- **Halcyon Africa Innovation in Agriculture and Food Security Accelerator (2027)** — Halcyon's only open call (closes 23/30 Oct 2026) is for Sub-Saharan African agriculture ventures, so it is non-US and off-sector. The year-round eligibility form is listed separately as an entry.
- **LatinTech Pitch 2026** — Texas-headquartered companies only, and requires outside seed funding; closed 29 Aug 2026.
- **Melamoon / DMZ Black Innovation Summit / FACE Propelling Black Entrepreneurship** — Canada-only programs (all require Canadian-based businesses).
- **BizVets LA Pitch Competition** — No 2026 application page found. The 2025 edition was an LA-area, defense-tech event.
- **Women's HealthX Startup Pitch Fest 2026 (Alpha Events, Boston)** — Fee to pitch: 'Startup Booth + Pitchfest Competition $1,199' (prize only $1,000). Closes 2 Nov 2026.
- **Dublin Pitch 2026 (COhatch + City of Dublin, OH)** — Video submissions were due 1 Oct 2026 (today); the window closes before the 2 Oct cutoff.
- **Tech419 Pitch Competition (University of Toledo)** — Closed 5 Jul 2026 ('Applications are closed for the 2026 Tech419 Pitch Competition'); also limited to Northwest Ohio.
- **PioBiz Round 3 Business Plan Competition (Marietta College)** — Open to the community only for people who 'live and/or work within 100 miles of Marietta, Ohio'. Akron is about 115 straight-line miles away, so Vybe likely fails the gate. Deadline 25 Oct 2026; $10K top prize paid over up to three years. Ask entr@marietta.edu if a founder lives closer.
- **Kent State Idea Pitch – Fall 2026** — Student-only (current Kent State students); deadline was 24 Sep.
- **Cintrifuse Emerging Founder Residency** — The $300K is an investment through Cintrifuse Capital (dilutive). It also requires relocating to Cincinnati and co-working at Union Hall 4 days a week, is aimed at recent graduates and early-career founders, and the 2026 cohort started in Sep.
- **Rev1 Concept to Customer Bootcamp (Fall 2026)** — Fall applications were due 4 Sep 2026; aimed at B2B concepts. Watch for the Spring 2027 session.
- **UH Haslam Sports Innovation Center Challenge (UH Ventures + Plug and Play)** — Closed 30 Apr 2026 (finals were 18 Jun 2026). Strong fit next year; watch for a 2027 call.
- **CDL-Cleveland Healthcare Delivery stream (Creative Destruction Lab + UH + CWRU)** — Applications closed 24 Jul 2026.
- **PNC Startup Showcase 2026 (Bounce Innovation Hub)** — Event was 24 Sep 2026; the six presenters were Bounce-featured companies with no open application. The $5,000 audience prize is past.
- **Synthe6 Materials Accelerator / PIC Translational R&D Funding (Bounce + Polymer Industry Cluster)** — 2026 intake closed 30 Jun 2026, and it is focused on polymer and advanced-materials startups. Relevant only if Vybe develops a novel band material.
- **Ohio Third Frontier TVSF Phase 1 (Round 46)** — Lead applicant must be an Ohio university, nonprofit research institution or federal lab with a tech-transfer office (not a startup); Round 46 proposals were due 6 Aug 2026.
- **Youngstown Innovation Hub NSF SBIR/STTR Cohort Program** — Applications were due 21 Jul 2026. Watch for a second pilot cohort; it fits Vybe's NSF Project Pitch work.
- **Ohio VC Fest 2026 – founder pitches** — Founder registration ended 7 Sep 2026.
- **CincyTech 'Pitch Us' / Ohio TechAngels** — Equity investors (dilutive), not grants or prizes.
- **Ohio Early Stage Focus Fund (SSBCI)** — Applicants are investment-fund managers, not startups; the money reaches companies as equity investment.
- **Minority Contractor Capital Access Program (MCCAP), Akron** — Contracting businesses only; support is short-term loans.
- **Qualcomm AI Program for Innovators 2026 – APAC** — Non-US only (Japan, Singapore, South Korea) and closed 30 Apr 2026. Qualcomm Innovate in Taiwan is also Taiwan-only and closed.
- **Arm Flexible Access for Startups** — Wrong fit: free Arm IP for startups designing their own system-on-chip silicon. Vybe builds a device from off-the-shelf parts and does not tape out chips.
- **Texas Instruments TechMatch startup program** — 'TechMatch™ is only open to Participants from EMEA.'
- **Texas Instruments Strategic Partnerships** — For companies building ICs, semiconductor materials or packaging, and requires being 'responsibly funded (i.e. reputable venture capitalist, incubation program or equity accelerator)'.
- **Nexperia Startup Challenge 2026/2027** — European-based hardware startups only; micro-mobility power electronics.
- **Infineon Startup Challenge 2026 (humanoid robotics)** — Closed 27 May 2026; off-topic. The rolling Co-Innovation program is listed as an entry instead.
- **Bayer G4A Startup Acceleration Program** — Run only in Türkiye (500,000 TL grants); closed 1 Feb 2026.
- **MassChallenge 2026 Healthcare Challenge Program** — Applications closed, and it requires a validated product with prior corporate proofs of concept (pilots).
- **ASICS Kenzen 2026 pitch competition** — Closed 30 Jul 2026 (finals 22 Oct). Wearables and sleep/recovery categories, $40K top prize, US-incorporated: a strong fit for the 2027 edition.
- **Garmin Health Awards 2026** — Closed 8 May 2026, and the solution must use Garmin wearables and Garmin Health APIs or SDKs. Lead came from an aggregator only.
- **Oura Partner Program** — 'This program is currently by invitation only' (it is an affiliate marketing program, not funding).
- **Samsung Health partnerships / Health Sensor SDK partner program** — Not a funded program: a contact form, plus SDK partner registration for Wear OS apps on Galaxy Watch. No money and no defined intake.
- **Garmin Connect Developer Program** — Gives API access for pulling Garmin data into an app; no funding, and it serves a competing wearable's ecosystem.
- **Google for Startups Accelerator: Women Founders (North America)** — No open application window shown on the official page today; it targets Seed to Series A startups with traction.
- **Apple Entrepreneur Camp** — Could not confirm an open 2026–27 window on Apple's page; past cycles closed in early September. It also requires an app already on the App Store or in TestFlight. Recheck: it fits women and minority founders.
- **AgeInnovate 2026 Startup Competition (Nashville)** — Closed 15 Jul 2026.
- **AgeTec 2026 Pitch Competition (LifeSpan Network, UMD)** — Startup deadline was 31 Aug 2026; it also wants early traction (pilots, partnerships or revenue).
- **AgeTech Connect Rural Health Innovation Challenge (GSA 2026)** — Requires a commercially available product with verifiable customers; Vybe is pre-revenue.
- **DHN HealthTech Innovation Challenge 2026** — India-focused; closed 23 Sep 2026.
- **Wayra / Pfizer Innomakers4Health 2026** — In-person hackathon in Madrid for individuals (€3,000 prize); non-US and not a company program.

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
