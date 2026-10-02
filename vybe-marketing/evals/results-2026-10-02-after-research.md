# Eval results: after the audience research and targeting skill, 2 Oct 2026

Same rubric, same scorer as the baseline (the agent itself, the weakest kind of
review). Outputs scored: the Marksom hub data (`marksom.json`) for cases 1 to
3, and the updated `plan-2026-q4.md` for case 7.

Guardrail (`check_marketing.py`): **pass**, 0 blocking findings.

Scores in dimension order 1 to 10: segment, wedge, evidence (gate), targets,
channel, compliance (gate), claims (gate), measurability, priority, honesty.

| Case | Scores | Total | Result | Lowest dimensions |
|---|---|---|---|---|
| 1. Pick the wedge | 3 3 2 3 3 3 2 2 3 3 | **27** | Pass | Evidence: some figures rest on secondary or unverified sources. Claims: messages carry no source beside each claim. Measurability: tests have no minimum sample. |
| 2. Tactical buyer map | 3 2 2 3 3 3 2 2 2 3 | **25** | Pass | Prioritisation inside the tactical list is not ranked; procurement timelines partly secondary. |
| 3. Meta campaign for quitters | 2 2 2 2 2 3 2 2 2 2 | **21** | Fail | Not yet a campaign: no creative set, budget, conversion event plan or decision rule. Compliance is strong; everything else is a sketch. |
| 7. Read the scoreboard | 2 2 3 2 2 3 2 2 3 3 | **24** | Pass | Measurability and target specificity still thin in the plan itself. |
| **Mean** | | **24.3** | 3 of 4 pass | Baseline mean was 18.0 (cases 1 and 7 only). |

## Change from the baseline

| Case | Baseline | After | Why it moved |
|---|---|---|---|
| 1 | 17 | 27 | Sized segment, 35 named targets with sources, buying paths, platform rules |
| 7 | 19 | 24 | Audience order and paid-restart targeting rules added to the plan |

## What to fix next

1. **Case 3:** write the actual subscription-quitter campaign brief (three
   creatives from the Register, allowed conversion event, budget cap, decision
   rule) and re-score.
2. **Every case:** put the source beside each claim in messages, and give each
   test a minimum sample.
3. **Independent review:** have the founder or a fresh session score cases 1
   and 2 without seeing these scores.
