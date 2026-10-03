# Eval results: baseline, 2 Oct 2026

Scored before the audience research and the targeting skill existed, so later
runs have something honest to beat. Scored by the agent itself against
`rubric.md`, which is the weakest kind of review; a fresh session or a person
should re-score.

Guardrail (`check_marketing.py`): **pass**, 0 blocking findings.

## Case 1: Pick the wedge (the 2 Oct wedge answer in chat)

| # | Dimension | Score | Evidence |
|---|---|---|---|
| 1 | Segment definition | 2 | Tactical and performance teams, with the shared problem stated; no size estimate |
| 2 | Wedge tests | 2 | Pain, fit, moat scored for six groups; evidence is positioning, not data |
| 3 | Evidence (gate) | 1 | Competitor facts sourced; buyer pain asserted without a source |
| 4 | Target specificity | 2 | H2F, two public creators named; no programmes, roles or events mapped |
| 5 | Channel fit | 1 | "Direct conversations" only; no buying path |
| 6 | Targeting compliance (gate) | 1 | Platform health-ad rules not addressed |
| 7 | Claim discipline (gate) | 2 | Stayed inside the Register; no sources beside claims |
| 8 | Measurability | 1 | A test named, no metric or decision rule |
| 9 | Prioritisation | 2 | Ordered with reasons; nothing marked as deliberately not done |
| 10 | Honesty under uncertainty | 3 | Hypotheses labelled; the settling test named |
| | **Total** | **17 / 30** | **Fail**: gates 3 and 6 below 2 |

## Case 7: Read the scoreboard (`plan-2026-q4.md`, week 1)

| # | Dimension | Score | Evidence |
|---|---|---|---|
| 1 | Segment definition | 2 | Founding-batch market named; segments not used in the plan |
| 2 | Wedge tests | 0 | Not applied |
| 3 | Evidence (gate) | 3 | Every number sourced to the 30 Sep pull |
| 4 | Target specificity | 1 | Channels, not targets |
| 5 | Channel fit | 2 | Channels matched to stage |
| 6 | Targeting compliance (gate) | 1 | Tracking fixed; health-ad targeting rules absent |
| 7 | Claim discipline (gate) | 2 | Register referenced |
| 8 | Measurability | 2 | Metrics and sources; decision rules only for some actions |
| 9 | Prioritisation | 3 | Ordered, stage-aware, with what would change the plan |
| 10 | Honesty under uncertainty | 3 | Baseline declared unknown rather than invented |
| | **Total** | **19 / 30** | **Fail**: gate 6 below 2 |

## What this says

The agent is honest and well ordered but thin on the two things this eval
cares about most: **who exactly** to reach and **how to reach them within
platform and privacy rules**. Next step: the audience research and a
targeting skill, then re-run cases 1, 2, 3 and 7.
