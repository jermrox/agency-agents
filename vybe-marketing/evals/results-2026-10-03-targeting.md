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
