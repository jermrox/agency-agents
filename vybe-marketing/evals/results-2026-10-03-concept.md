# Concept test results, 3 Oct 2026

Graders were fresh sessions that had not seen the work being graded. The
writers were fresh sessions holding only the agent file and
`vybe-marketing/`, with `evals/` closed to them.

## C1: LinkedIn company page (blind A/B grade)

| Dimension | New draft | First draft (2 Oct) |
|---|---|---|
| 1 Distinctiveness | 3 | 1 |
| 2 Channel and half | 3 | 1 |
| 3 Show, don't tell | 2 | 1 |
| 4 Order | 3 | 1 |
| 5 Claim status (gate) | 2 | **0** |
| 6 Voice | 3 | 2 |
| **Total** | **16/18, pass** | **6/18, fail** |

The first draft failed the claims gate on a present-tense "Developer API"
line, which the public FAQ dates to June 2028. The guardrail missed it.

**Fixes applied:**
- one labelled sample answer is now shown;
- "aggregate only, with consent" now sits next to the team and research invitation;
- "Our band" replaces "The Vybe band";
- the guardrail gains a roadmap rule that blocks "available now"-style SDK, API, DevKit and ring claims.

## Round 1: cold take

**Part A, knowledge: 12/12, pass.**

**Part B, copy:**

| Case | Score | Result | Main miss |
|---|---|---|---|
| C2 Homepage hero | 13/18 | Fail | The platform half was missing, and "Every answer is…" read as shipped. |
| C3 Instagram Reel caption | 12/18 | Fail (gate) | "an answer Vybe gets wrong" was in the present tense. The example gave one cause for an HRV change. |
| C4 Cold email to a lab | 13/18 | Fail | The row's second line was left out, and the first line was a 48-word run-on. |

**Diagnosis.** The agent knew the concept but applied it unevenly. The root
causes were in `concept.md` itself:
1. "Designed to" read as a once-per-piece label.
2. The example answer in `concept.md` gave a single cause, against the evidence library.
3. The concept check never said each piece must carry both columns of its channel row.

**Fixes applied (same day):**
- `concept.md`:
  - the example sentences are now marked as internal illustrations;
  - the example now names competing explanations;
  - check Q1 requires both columns of the row;
  - check Q6 applies "designed to" to every sentence, including calls to action, bans the present tense before launch, and requires more than one explanation.
- The agent file: the weekly Two-Product Test no longer excuses a single piece.
- The rubric: D2 and D5 are reworded to match.
- The key: Q9 now matches.
- The guardrail: allow markers are added for review notes.

## Round 2: rerun cold after the fixes

| Case | Round 1 | Round 2 | Result |
|---|---|---|---|
| C2 Homepage hero | 13 | **18** | Pass. H1: "A health band designed to tell you how sure it is." |
| C3 Instagram Reel caption | 12 (gate) | **16** | Pass. Shows one sample answer with three explanations. |
| C4 Cold email to a lab | 13 | 13 (gate) | Fail. It offered a lab "licensed, consented access to the signals" and implied a testable band, neither confirmed. |

**Fixes applied:**
- Check Q7 now covers offers. Builder, lab and team copy invites a design-partner conversation and never promises access, a device, terms or a date.
- Example explanations stay everyday ones; an illness is never offered ("an oncoming cold" removed).
- New Claim Register row 19 covers "patterns, not causes".
- The guardrail ignores review notes that quote a banned phrase.

## Round 3: C4 rerun cold

| Dimension | Score |
|---|---|
| D1 Distinctiveness | 2 |
| D2 Channel and half | 2 |
| D3 Show | 2 |
| D4 Order | 2 |
| D5 Claim status (gate) | 2 |
| D6 Voice | 3 |
| **Total** | **13/18, fail by one point** |

The claims gate now passes: it uses "designed to" and "design partner", and
promises no access, device, terms or date. The guardrail passes. It still
fails because it opens on the lab's own work, which fits any competitor, and
runs as one 63-word sentence.

**Fix:** a short-format rule in check Q8. Put the unclaimed idea in the first
ten words and stay under 25 words.

C4 is the case to rerun first next time.

## Where the agent stands

| Measure | Result |
|---|---|
| Knowledge (Part A) | 12/12 |
| LinkedIn page (C1) | 16/18, pass |
| Homepage hero (C2) | 18/18, pass |
| Instagram caption (C3) | 16/18, pass |
| Lab email first line (C4) | 13/18, fail by one point |

**Founder approvals that gate publication:**
- Claim Register rows 14 to 17 and 19, for public copy in "designed to" form;
- what a research lab would actually get as a design partner.

## Cycle 2 of the refinement block

Cold writer under the cycle-1 rules; separate grader.

| Case | Before | Now | Result |
|---|---|---|---|
| C4 Lab email first line, with companion line | 13 | **15** | Pass. "Vybe is designed to state how sure each answer is, so your lab could start at the interpretation. Pre-launch; seeking design partners." |
| C8 Pricing line, with companion line | 11 | **16** | Pass. Calibration first, the add-on contrast second, "no required subscription" underneath. |
| S3 Screenless category brief (search rubric) | — | **16** | Pass. The competitor table broke the table rules; it was fixed and saved to `briefs/`. |

Cycle-1 copy, same grader standard: C5 16, C6 17 and C7 16 (pass).

**New rules:**
- Each concept-check answer quotes the copy words that satisfy it; the writer's notes had over-claimed in all three cases.
- Claims use the Register's own wording ("nothing shared without consent").
- Search pages open the Vybe section on an unclaimed idea.
- Device tables carry no per-brand price column, and Vybe's row says "pre-launch" with nothing unconfirmed.

## Search briefs

| Case | Score | Result |
|---|---|---|
| S1 What is a good HRV | **17/18** | Pass |
| S3 Screenless fitness tracker | **16/18** | Pass |
| S2 WHOOP vs Oura (fair comparison) | **16/18** | Pass |

**S2.** Every WHOOP and Oura fact is sourced from the brand's own pages; the grader confirmed three and found one sourced to an older model.

Weak spots:
- an unsourced line about both competitors in Vybe's section;
- a membership point listed as a downside;
- uneven rows.

New rule: on a vs page, Vybe's section never describes the compared products.
| S4 Eating before bed (Nourish) | **16/18** | Pass. The grader checked five studies on PubMed: all match design, size and direction. It lost points for one unsourced line in the answer-first paragraph, one overstated study framing and one unsupported "size may matter as much" line. |
| S5 Oura ring alternative | **17/18** | Pass. The grader verified the ITC 337-TA-1398 notices, the competitor quotes and the live Vybe page. It found the brief had missed two open cases (337-TA-1468 with Oura as complainant, 337-TA-1478 with Oura as respondent). I verified both from the Federal Register and fixed the brief before saving it to `briefs/`. New rules: search the dockets both ways for legal questions; Vybe's table row uses approved rows only; answer-first sources show in the copy; disclose an author's own app. |
| S6 Overtraining symptoms (Move) | **15/18** | Pass. DataForSEO was unfunded, so volume and KD came from the dated table and no Google results page was pulled. The grader checked nine studies on PubMed; all match on design and size. It lost points for unsourced symptom lists and urgent-care signs, for describing Le Meur 2013's functionally overreached triathletes as if they were overtrained, and for missing founder sign-off as a check before publishing. New rules: every health statement is sourced, participants are described exactly, symptoms pages need a crisis route, and the brief template has a "Before publishing" section. Saved to `briefs/` as not ready to publish. |

## Regression run, C1 to C8 (final rules)

A fresh writer redid every case; a separate grader scored only what the copy
contains.

| Case | D1 | D2 | D3 | D4 | D5 | D6 | Total | Result |
|---|---|---|---|---|---|---|---|---|
| C1 LinkedIn tagline and About | 3 | 2 | 3 | 3 | 2 | 3 | 16 | Pass |
| C2 Homepage hero | 3 | 3 | 3 | 3 | 3 | 2 | 17 | Pass |
| C3 Instagram answer Reel | 3 | 3 | 3 | 3 | 3 | 3 | 18 | Pass |
| C4 Lab email first line | 3 | 2 | 3 | 2 | 2 | 3 | 15 | Pass |
| C5 Nourish Reel | 3 | 3 | 3 | 3 | 2 | 3 | 17 | Pass |
| C6 Connect daylight | 2 | 2 | 3 | 3 | 3 | 3 | 16 | Pass |
| C7 Move, H2F one-pager | 3 | 1 | 3 | 3 | **1** | 3 | 14 | **Fail (D5 gate)** |
| C8 Pricing line | 3 | 3 | 3 | 3 | 2 | 2 | 16 | Pass |

**C7 failure.** "Shared only under each soldier's revocable consent" drops
row 4's exceptions; "talking with performance teams as design partners"
states unconfirmed conversations as fact. The guardrail passed it because a
paragraph-level allow marker covered the whole piece.

**Pattern.** D2 lost points in C1, C4, C6 and C7: the row's second column was
tacked on at the end or relabelled ("the band is the proof").

**Fixes:** placement rules in Q1, a Q7 line on unconfirmed relationships, the
tactical row rewritten, row 21 aligned, and a sentence-level guardrail with a
blocking `privacy-claim` rule. C7 is retested below.


## Retest of C1, C4, C6 and C7 (placement rules)

| Case | D1 | D2 | D3 | D4 | D5 | D6 | Total | Result | Before |
|---|---|---|---|---|---|---|---|---|---|
| C1 LinkedIn tagline and About | 3 | 3 | 3 | 3 | 3 | 3 | **18** | Pass | 16 |
| C4 Lab email first line | 2 | 3 | 3 | 2 | 2 | 3 | **15** | Pass | 15 |
| C6 Connect daylight | 2 | 3 | 3 | 3 | 3 | 2 | **16** | Pass | 16 |
| C7 H2F one-pager | 2 | 3 | 3 | 3 | **1** | 2 | **14** | **Fail (D5)** | 14 |

D2 went to 3 in all four: the placement rules worked. But the "row phrases
word for word" rule made writers print the table's directions:
- C6 opened on "One calibrated answer, shown, not described.";
- C4 told a validation lab the band is "the reference device", which reads as a criterion measure;
- C7's "designed to" sat in a later clause, leaving "Vybe shows readiness…" unhedged, so it failed again.

**Fixes:**
- Quoted cells are used exactly; every other cell is a direction to carry out, never print.
- "Designed to" governs the main verb.
- The builder row no longer says "reference device".
- The tactical lead is quoted copy backed by a new Register row 22 (founder to confirm).
- Q1's row 21 example carries row 21's hold.

## Round 3: C4, C6 and C7 (directions vs quoted wording)

| Case | D1 | D2 | D3 | D4 | D5 | D6 | Total | Result |
|---|---|---|---|---|---|---|---|---|
| C4 Lab email first line | 2 | 3 | 3 | 3 | 3 | 2 | **16** | Pass |
| C6 Connect daylight | 2 | 3 | 3 | 3 | 3 | 3 | **17** | Pass |
| C7 H2F one-pager | 3 | 2 | 3 | 3 | 3 | 3 | **17** | Pass (draft: row 22 holds scheduling) |

All eight copy cases now pass. Two problems remained:
- C4's first line was 25 words against "under 25", and the writer miscounted.
- C7 lightly reworded a direction cell ("no screen, so the data keeps arriving") without giving the reason, and credited the team view to the band.

**Fixes:**
- `check_marketing.py` now counts the words in any line labelled tagline, first line, subject line or hook, and blocks at 25 or more.
- The tactical and builder direction cells now state the reason, and row 22's subject is the team view.
- Q1 adds that a copy sentence never reuses a direction cell's wording beyond its quoted phrases.

## Final regression, C1 to C8 (all rules in force)

A fresh writer redid all eight cases, and a separate grader scored only the copy.

| Case | D1 | D2 | D3 | D4 | D5 | D6 | Total | Result |
|---|---|---|---|---|---|---|---|---|
| C1 LinkedIn | 3 | 3 | 3 | 3 | 3 | 3 | **18** | Pass |
| C2 Hero | 3 | 3 | 3 | 3 | 2 | 3 | **17** | Pass |
| C3 Reel caption | 3 | 3 | 3 | 3 | 2 | 3 | **17** | Pass |
| C4 Lab email | 3 | 3 | 3 | 2 | 3 | 3 | **17** | Pass |
| C5 Nourish | 3 | 3 | 3 | 3 | 2 | 3 | **17** | Pass |
| C6 Connect | 3 | 3 | 3 | 3 | 2 | 3 | **17** | Pass |
| C7 H2F | 3 | 2 | 3 | 3 | 2 | 3 | **16** | Pass (held for row 22) |
| C8 Pricing | 3 | 3 | 3 | 3 | 3 | 3 | **18** | Pass (held for row 21) |

D1 is now 3 in every piece. All short formats are under 25 words, and every prompt was quoted exactly. Weakest pattern: one stamped closing line, "The band is designed to produce that answer, with no required subscription", appeared in C2, C3, C5 and C6. It reads as boilerplate, and tying the answer to "no subscription" is row 21's claim, made without a hold. C6's blind spot ("mornings you were outside and didn't log") implied the band can't sense outdoors.

**Fixes:**
- Q1 and Register row 21: a sentence that ties an answer to "no required subscription" is row 21 and carries its hold. Without a hold, it gets its own sentence about the band.
- Q6: blind spots never name a sensing gap on an unconfirmed spec.
- `check_marketing.py` has a blocking `row21` rule, scoped to each markdown section's hold. It catches exactly those four pieces in this run and passes the held C8.

## Retest of C2, C3, C5 and C6 (row 21 rule)

| Case | D1 | D2 | D3 | D4 | D5 | D6 | Total | Before |
|---|---|---|---|---|---|---|---|---|
| C2 Hero | 3 | 3 | 3 | 3 | 3 | 3 | **18** | 17 |
| C3 Reel caption | 3 | 3 | 3 | 3 | 3 | 3 | **18** | 17 |
| C5 Nourish | 3 | 2 | 3 | 3 | 2 | 3 | **16** | 17 |
| C6 Connect | 3 | 2 | 3 | 3 | 2 | 3 | **16** | 17 |

The row 21 tie is gone in all four, and C5's present-tense line and C6's sensing blind spot are fixed. New misses:
- C5's call to action asked "what your own late dinners do", which assumes a cause.
- C6 answered "Why mornings?" with UK Biobank's day-vs-night finding, and wrote "buy the band once".
- Both carried only half of the Instagram "then" cell, or carried it after an evidence paragraph.
- C2's sub-line was 55 words.

**Fixes:**
- Q1 carries the whole "then" cell, directly after the pointer.
- Q6 treats call-to-action questions, pricing words and citations as claims.
- Q8 and `check_marketing.py` count a sub-line or subhead as a short format; the checker now blocks C2's 55-word sub-line.
