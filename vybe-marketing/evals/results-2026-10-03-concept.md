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

## Round 2

Pending. The same three cases are being rerun cold after the fixes.
