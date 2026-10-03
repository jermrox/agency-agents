# Targeting eval results, 3 Oct 2026

Writer: a fresh session holding only the agent file, the targeting skill and
`vybe-marketing/`, with `evals/` closed to it. Grader: a separate fresh
session, which also spot-checked four sources.

| Case | 2 Oct (self-scored) | 3 Oct (independent) | Result |
|---|---|---|---|
| 3 Meta campaign for subscription quitters | 21, fail | **27/30** | Pass once the guardrail false positive is fixed |
| 5 Twenty organisations for the SDK | not run | **25/30** | Pass |

**Case 3.** The campaign is fully built and gated (no launch before Jan 2027).
- No competitor-customer or health targeting; broad and Advantage+ audiences, with manual placements.
- The waitlist's "what do you wear now" field measures reach and stays out of the pixel and Conversions API.
- Covers the Washington My Health My Data Act and the FTC Health Breach Notification Rule.
- n=30, with ship, kill and extend rules.

It lost points on evidence (one wrong citation to `concept.md`, a few unsourced figures) and on claim discipline (it called Claim Register row 21 "new").

**Case 5.** Twenty named organisations, each with a trigger, a buying path and a fit score; four rejected with reasons. It lost points on the segment (no size estimate), wedge (it omitted Polar SDK and Movesense from the moat), evidence, claims (an unregistered data-handling line scheduled to send) and prioritisation (bunched fit scores, cost not weighed).

**Sources spot-checked:**
- WHOOP has more than 3M members, 58% outside the US: holds.
- Oura's S-1 reports 5.0M paid members: holds.
- Fitbit Web API off on 30 Oct 2026, with support ending 30 Sep: holds per Fitabase and the trade press.
- AFSOC's WHOOP contract figures rest on a single page: not confirmed.

**Changes made:**
- `vybe-audience-targeting` now requires a Claim Register row number beside every claim, and a "New" label only after searching the Register. An unregistered claim blocks scheduling.
- It bans absolute outcome promises.
- It adds a sourcing step: a link and checked date, or "(unsourced)", with repository citations quoting their line.
- It runs the guardrail before handing back.
- The guardrail allows rule notes such as "nothing relies on…".

## Cycle 3: cases 4 and 8

| Case | Score | Result |
|---|---|---|
| 4 Creator shortlist for baseline nerds | **27/30** | Pass. Ten public creators in three tiers, ties to WHOOP and Oura stated, nobody paid or promised a device before launch, and FTC endorsement rules cited. |
| 8 HYROX race weekend | 10/30 | Fail: it answered the wrong prompt. The orchestrator's task text substituted a general events plan, so the miss is in the test setup. Against that prompt it scored 26. A rerun with the real prompt is under way. |

The grader also found:
- **H2F figures:** "66 brigade teams now, 129 by FY2029" is correct but was cited to an older AUSA page that says "111 by FY2027". The writer proposed changing the number; the right fix was the citation (Army.mil 8 Dec 2025; Modern War Institute 3 Mar 2026). The citation is now fixed.
- **Creator tie:** Dan Plews co-authored a WHOOP-led paper, which was not recorded.
- **Outlet tie:** coverage by an owned or linked outlet was proposed without disclosing the connection.

**Changes made to `vybe-audience-targeting`:**
- Answer the prompt word for word, with an explicit "Scope change:" line if needed.
- Search for a figure's real source before correcting it.
- Check creators for competitor ties.
- Never quote a creator's critique without written permission.
- Disclose any owned or linked outlet.

## Cycle 5: case 8 rerun with the real prompt

**Case 8 HYROX race weekend: 28/30, pass, "Strong"** (all three gates at 3).

The plan:
- No sponsorship and no activity inside the venue. HYROX US terms clauses 9.8 and 10.3 rule it out, and Amazfit's exclusive covers smart straps.
- Tampa is a content-only test.
- One off-site meetup with no HYROX marks at Dallas, behind three dated gates. The default is no trip.

It uses no geofencing, a consented QR form, and a Register row beside every claim. The grader confirmed the Amazfit deal, both race dates and the terms quotes.

**Changes made to `vybe-audience-targeting`:**
- A worldwide total is not a segment size; give a counted low-to-high estimate.
- In-person activations need three local reach points outside the exclusive partner's network and a schedule-clash check.
- "Not affiliated" goes on every piece.
- Association by time and place goes to counsel as ambush risk.

**Independent targeting scores today:**

| Case | Score |
|---|---|
| 3 | 27 |
| 4 | 27 |
| 5 | 25 |
| 8 | 28 |

All pass.

## Cycle 7: case 6

**Case 6 privacy-first ads: 24/30, pass, just.**

Three ads lead with calibrated answers, with privacy as the proof. Every claim has a Register row, there is no HIPAA wording, the pixel waits for consent, and the Washington health-data law is covered.

It lost points on:
- **Evidence:** it said "no privacy policy we can check yet", but vybe.health/privacy is live (Oct 2026). Its site reader cut the page short.
- **Claims:** "nothing shared without consent" doesn't match that policy, which allows sharing with service providers and where the law requires.
- **Measurability:** a blank keep threshold.

**Site facts found by the grader (Firecrawl, 3 Oct 2026):**
- The homepage still says "The first 1,000 on the waitlist are guaranteed a position to buy a band."
- /waitlist says sign-up "is not a device order" and is "evaluated on eligibility".

**Changes made:**
- Claim Register row 4 now matches the live policy.
- Row 11 is marked as a page conflict.
- Two founder rows are added to the tensions table.
- Both skills now read vybe.health with Firecrawl and cite it for any "not found".
- Privacy claims quote the policy clause.
- "Share" is reserved for data leaving Vybe.
- Thresholds need a number or a named placeholder.

**Targeting cases graded independently today:** 3 (27), 4 (27), 5 (25), 6 (24) and 8 (28). All pass.

## Cases 1 and 2, independent rerun (corrected prompts)

A fresh writer answered the exact prompts from `cases.md`; a separate grader
scored them against `rubric.md` and spot-checked the sources.

| Case | Score | Gates (3, 6, 7) | Result |
|---|---|---|---|
| 1 Pick the wedge | **28/30** | 3, 3, 3 | Pass (Strong) |
| 2 Tactical buyer map | **25/30** | 2, 3, 2 | Pass |

The grader confirmed the Army Times (28 Sep 2026) pilot timing, the FAR
thresholds and set-aside rule, the POTFF III award estimate, the AFG FY2025
close date and the Washington MHMDA employment exclusion. Weak spots:
- case 1's first checkpoint fell 58 days out, not within 30;
- neither case weighed cost;
- case 2 sized all career fire departments, not those with a wellness programme;
- one quote was a paraphrase in quote marks, and two event dates cited the wrong year's or an aggregator's page;
- case 2 took /enterprise's wording without noticing that /faq disagrees.

**New rules in the skill:** size only accounts that meet the entry criterion;
rank targets with a cost column; when site pages disagree, cite both and flag
it; quotes word for word and dated sources from the right year; the first test
checkpoint within 30 days.

## Case 7, independent rerun

**25/30, pass** (24 before; gates 3, 6 and 7 all at 3). A second check
re-pulled 12 of the numbers from GA4 and Search Console, read-only, and all of
them matched. Weak spots:
- the targets were search queries and pages, not communities or creators;
- there was no proven / suggested split, and the answer gave seven changes instead of one;
- the "last week" Search Console figure was copied from the old scoreboard;
- a stale read produced a false "Register ends at row 21" note.

**New rules:**
- The agent file's scoreboard template now has Proven, Suggested and Unknown blocks, one biggest problem and one change.
- "Last week" is re-pulled with the same window length.
- Any "the file says" note re-reads the file first.
- The targeting skill carries a segment's `marksom.json` evidence and named targets into the answer.

## Case 5, independent rerun

**28/30, pass at the Strong level** (25 before; gates 3, 6 and 7 all at 3).
The grader checked the triggers:
- The Fitbit Web API end date: trade reports say 30 Oct, while Google's page still says September 2026.
- The Google Fit end-2026 date was confirmed word for word.
- The yearly security assessment was confirmed.
- RunGap and Intervals.icu declining it, and Labfront listing the Garmin CIRQA band, were both confirmed.
- The POTFF III and H2FMS details were confirmed.

No private contact details appear. The fit scores range from 5 to 9. Weak spots:
- Moat was scored 3 without testing open developer devices (Polar BLE SDK, Movesense). This is the second run with the same miss.
- Teams already moving to Google's new API were still scored 9.
- One programme stage was a year old with no status check.

**New rules in the skill:**
- Builder Moat is tested against open SDKs.
- Fit scores quote their band and apply one test to every row.
- Quotes cite their exact page, and old programme stages carry a status-checked date.

## Case 6, independent rerun

**26/30, pass** (24 before; gates at 2, 3 and 2). The three ads score 17, 16
and 17 as copy (Part B). The grader verified on the live site:
- /privacy §3 ("We do not use your data for advertising targeting"), §4 and §6 ("export … by contacting us");
- the homepage "nothing shared" line;
- the /faq answers.

It also confirmed HINTS 2024's 41.1% and Cisco's 38% "Privacy Actives".

Weak spots:
- The low-end proxy (23.8%) dropped its population. The survey measured willingness to share data *with clinicians*.
- Ad 2's "the record of what worked is your health data" presumed row 16 works.
- Every primary text opened on a line a competitor could print, with the distinctive idea below Meta's "See more" cut.
- With no honest data screen to show, every ad used the same row 4 sentence.

**New rules:**
- Noun phrases that presume a design commitment need "designed to".
- Survey proxies quote their question and population.
- On Meta, the unclaimed idea goes above the cut.
- The policy's §3 line becomes Claim Register row 23.
- The export conflict between §6, /faq and row 17 is logged for the founder.

## Case 3, independent rerun

**28/30, pass** (27 before; gates at 2, 3 and 3). The three ads score 18, 16
and 17 as copy. The grader checked these claims:
- Oura's S-1 (filed 3 Sep 2026): "approximately 5.0 million Paid Members" and the ~85% 12-month retention match word for word.
- WHOOP's "over 2.5 million members".
- Rock Health's switching figure.
- Meta's 2025 health-advertiser event and audience restrictions.

It confirmed the conflict between /privacy §3 ("We do not use your data for advertising targeting") and the plan's weeks 7 to 10 retargeting. The plan now holds retargeting, waitlist lookalikes and conversion events for counsel.

Weak spots:
- Oura's retention was used as the inverse of lapse without its definition (it counts winbacks and grace periods).
- There was no measurement option that sends Meta nothing.
- Global Privacy Control was missing.
- Two Oura quotes had no URL.

**New rules:**
- Company metrics used as proxies quote their definition and the direction of bias.
- The targeting template requires a zero-data option and GPC.
- Rubric dimension 6, level 3, names both.

## Case 4, independent rerun

**29/30, pass at the Strong level** (27 before; all gates at 3). The grader checked:
- the Social Blade counts for The Quantified Scientist (417K), DC Rainmaker (652K) and Andy Galpin (200K);
- Altini's Oura advisor role;
- the WHOOP-led paper (27 Nov 2025) co-authored by Altini and Galpin;
- the QS NYC Show&Tell on 13 Oct at Civic Hall.

No private contact details appear.

Weak spots:
- The two paid candidates had no verified Instagram handle, and DesFit's was missed.
- DesFit's tie row dropped Polar and Coros from the tracker's list.
- What each creator has said about subscriptions was missing.
- Four of the ten were event hosts or citation-only.

**New rules in the skill:**
- Copy every brand a tie source names.
- Ad candidates need a live-channel handle with a dated count.
- Quote each creator's public view on subscriptions and baselines.
- Say how many names can actually be worked with.

## Case 2, second independent rerun (all new rules)

**28/30, pass** (25 before; gates at 2, 3 and 3). Fire sizing now counts only
departments running a wellness-fitness programme (≈940 to 1,610, from NFPA,
with the arithmetic checked). Costs, a zero-data LinkedIn option and Global
Privacy Control are in, and every quote checked was word for word.

The grader verified:
- the 2016 DoD CIO memo's four device conditions, word for word, but its FAQ says it is "NOT intended to prohibit any devices", so calling it a blocker overreached;
- the /faq FCC filing (Dec 2026) and pilot (Jan 2027) dates;
- the POTFF III contact restriction (a draft RFP, not source selection);
- the AUSA, FFCA and FDSOA dates.

Weak spots:
- The procurement stage was misnamed, and the article that named GDIT on H2FMS was missed.
- The FFCA cash cost was left unknown although the page lists it.
- NSCA TAT was dropped without a reason.
- Pages contradicting themselves (/faq "funded through … pilots", /enterprise "deployments exist") were missed again.

**New rules:**
- Check each page against itself.
- Quote procurement stages and a policy's scope clause.
- Name contractors the cited articles name.
- Fill cash from the page.
- Carry every target over or give a reason.
- Give a publication or community per programme.

## Case 7, second independent rerun (new scoreboard template)

**26/30, pass** (25 before; all gates at 3). All four earlier weak spots are fixed:
- Proven, Suggested and Unknown are split.
- There is one biggest problem and one change.
- Last week's figures were re-pulled, not copied.
- Targets are communities, not queries.

The grader re-pulled ten GA4 figures and all matched. The change: pause "Vybe Health - 9/15" (397 of 598 sessions, 82% from India, Pakistan and Bangladesh, 0 signups).

Weak spots:
- The change covered one campaign, not every out-of-market paid source.
- Its threshold ignored the decline already under way.
- A restart condition imported conversions despite the counsel hold.
- Segment detail was thin.

**New rules:**
- The agent file scopes the change to the whole cause, sets thresholds against the trend, and carries segment detail.
- Plan action 3 imports no conversions until counsel rules.
