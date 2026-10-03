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
