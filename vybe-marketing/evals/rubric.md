# Marketing Director eval: finding and targeting audiences

How to score the Vybe Health Marketing Director on its core job: finding the
groups and people most likely to buy, and reaching them in ways that work and
are allowed. Use it on any audience plan, campaign brief, target list or wedge
recommendation the agent produces.

Two layers:

1. **Guardrail, automatic.** `python3 vybe-marketing/evals/check_marketing.py`
   must pass. A blocking finding (a medical claim, private contact details,
   sensitive-category targeting, an implied partnership, "HIPAA-compliant")
   fails the output outright, whatever it scores below.
2. **Rubric, judged.** Ten dimensions, each scored 0 to 3. A reviewer (the
   founder, a person on the team, or a separate Claude session that has not
   seen the output being made) scores it and writes one line of evidence per
   score.

## Dimensions

| # | Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| 1 | **Segment definition** | "Health-conscious people" | A category ("athletes") | A specific group with a shared problem | A specific group, its shared problem, its trigger to switch, and an estimated size with a source |
| 2 | **Wedge tests** | Not applied | Pain, fit and moat named without evidence | All three scored, some evidence | All three scored with evidence, and the weakest test called out honestly |
| 3 | **Evidence** *(gate)* | Numbers with no source | Some sources | Most numbers sourced and dated | Every number sourced and dated; unknowns stated as unknown |
| 4 | **Target specificity** | No named targets | Platforms only ("Instagram") | Named communities, programs or publications | Named organizations, programs, roles, public creators, events and communities, each with why it matters; no private individuals' details |
| 5 | **Channel fit** | Same channel for every segment | Channels listed without reasons | Channel matched to where each segment gathers | Channel matched, with the buying path (consumer, unit purchase, SBIR, partner) and respects the live-channel rule |
| 6 | **Targeting compliance** *(gate)* | Uses prohibited targeting | Ignores platform rules | Follows platform rules | Follows platform rules and privacy law (consent, pixels, Global Privacy Control, consumer-health-data laws) and names the compliant alternative it uses, including one that sends ad platforms no Vybe data while the privacy policy's ad-targeting line is unresolved |
| 7 | **Claim discipline** *(gate)* | Medical or causal claims | Unapproved claims | Claims from the Claim Register | Claims from the Register at the right ladder level, with the source beside each |
| 8 | **Measurability** | No metric | A metric, no source | Metric and source | Metric, source, minimum sample, decision rule and review date |
| 9 | **Prioritisation** | Everything at once | A list with no order | Ordered, with a reason | Ordered by stage, cost and evidence, with what is deliberately not being done |
| 10 | **Honesty under uncertainty** | Hypotheses stated as facts | Mixed | Hypotheses labelled | Hypotheses labelled, the test that would settle each named, and what would change the plan |

## Passing

- **Pass:** 24 or more out of 30, no gate dimension (3, 6, 7) below 2, and
  the guardrail passes.
- **Strong:** 27 or more, every gate at 3.
- Anything else goes back to the agent with the lowest two dimensions named.

## Test cases

`cases.md` holds fixed prompts. Run each one in a fresh session with only the
agent file and `vybe-marketing/` as context, score the output, and log the
result in a dated `results-YYYY-MM-DD.md`. Re-run the full set after any
change to the agent file or the targeting skill, so a change that makes one
answer better and another worse is visible.
