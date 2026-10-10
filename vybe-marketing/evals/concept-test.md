# Concept test

Checks whether the Marketing Director understands what Vybe Health is and
tells it that way. `rubric.md` scores targeting work; this file scores the
idea. Run it after any change to `concept.md` or the agent file, in a fresh
session that has only the agent file and `vybe-marketing/` as context. Log
the result in a dated `results-YYYY-MM-DD-concept.md`.

## Part A: knowledge (12 questions, 1 point each, pass at 10)

Answer each question in one or two sentences, without opening `concept.md`.
The grader marks against the key below. Half credit is allowed.

| # | Question | Key (what a full-credit answer contains) |
|---|---|---|
| 1 | What is the concept in one line? | You don't need more data; you need what it tells you, how sure it is, and whether its advice worked. |
| 2 | What do competitors get wrong, according to the product? | They open on a score and leave the interpreting to you. |
| 3 | Name the three parts of a Vybe answer beyond the sentence itself. | Confidence in words with its reason, what it could not see, and a later check on whether the suggestion worked. |
| 4 | Which four Vybe claims are crowded, and who holds them? | Any four of: no subscription (Polar, Amazfit, Circular); screenless (Amazfit, Polar); own baseline (Circular, WHOOP, Terra); plain-sentence answers (Circular Kira, Ultrahuman Jade); data never sold (Oura). |
| 5 | Which positions does no competitor own? | Calibrated answers (confidence and blind spots), self-grading and a score-skeptic stance. "Built to be built on" is narrowed since 5 Oct 2026 (Ultrahuman UltraSignal): a band whose owner grants builders access by consent. |
| 6 | What is the swap test? | Put a competitor's name in the line; if it is still true, it is hygiene, not the concept. |
| 7 | On LinkedIn, which half leads, and why? | The company and platform half, because LinkedIn readers are builders, partners, buyers, investors and hires. The band is the proof. |
| 8 | How do you describe the platform today, and what must you never say? | "Designed to be built on", "talk to us", design partners. Never "available now": the public FAQ dates API v1 to 2028 and /research says no SDK is available today. Hold "built open" until the founder confirms. |
| 9 | How do you write a design commitment that has not shipped? | "Built to" or "designed to" in every sentence that asserts it, calls to action included, until the founder confirms it has shipped (Claim Register rows 14 to 17). |
| 10 | What are the five factors, as the site names them? | Restore, Move, Nourish, Connect, Vitals. |
| 11 | What does Vybe do when asked "Do I have sleep apnea?" | It says that is outside what Vybe does, still shows the person's own signal, and suggests exporting it for a clinician. The boundary is on the claim, not on the data. |
| 12 | Name two tensions only the founder can settle, and the safe side for each. | Any two rows from the tensions table in `concept.md`, each with its safe side. |

## Part B: copy fidelity (6 dimensions, 0 to 3 each, pass at 14 of 18)

Score any public-facing copy: a bio, a post, a page, an ad or a pitch.

| # | Dimension | 0 | 1 | 2 | 3 |
|---|---|---|---|---|---|
| 1 | **Distinctiveness** (swap test) | A competitor's name fits every line | The hook fits a competitor; something distinctive comes later | The hook is distinctive but generic in wording | The hook fits no competitor and is said in Vybe's own words |
| 2 | **Channel and half** | Wrong lead for the channel | Right lead, the row's "then" line missing | Right lead, the "then" line mentioned | Right lead, with the "then" line placed as proof (channel table in `concept.md`) |
| 3 | **Show, don't tell** | "Insights", "intelligence" with nothing behind them | Describes features | Names what an answer contains | Shows or plainly describes one answer: the sentence, its confidence, a blind spot |
| 4 | **Order** | Hygiene only | Hygiene first, unclaimed later | Unclaimed first, hygiene thin or missing | Unclaimed first, hygiene as proof underneath |
| 5 | **Claim status** *(gate)* | A medical, roadmap or unconfirmed claim | An unapproved claim, a design commitment in the present tense, or a single-cause explanation | Approved claims only | Approved claims at the right status, "designed to" on every sentence that needs it, and every example answer gives more than one explanation |
| 6 | **Voice** | Hype or a stack of adjectives | Corporate filler | Plain | Plain, declarative and calm; admits limits ("pre-launch", "not yet") |

**Pass:** 14 or more, with dimension 5 at 2 or higher. The guardrail
(`check_marketing.py`) must also pass.

## Fixed copy cases

| Case | Prompt |
|---|---|
| C1 | Write the LinkedIn company page tagline (120 characters max) and About section. |
| C2 | Write the homepage hero: eyebrow, H1 and one sub-line. |
| C3 | Write an Instagram caption for a Reel that shows one Vybe answer. |
| C4 | Write the first line of a cold email to a university wearable-validation lab. |
| C5 | Nourish: write an Instagram caption for a Reel on late dinners and overnight HRV. |
| C6 | Connect: write a short post on morning daylight. Assume the band's light sensor is unconfirmed. |
| C7 | Move: write the opening paragraph of a one-pager for an Army H2F performance team. |
| C8 | Pricing: write one line contrasting Vybe with coaches sold as a paid add-on, with no price comparison. |
