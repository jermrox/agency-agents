---
name: vybe-audience-targeting
description: >
  Find, size and reach Vybe Health's audiences the way the Marketing Director
  agent should: pick a wedge with evidence, map the organisations, programmes,
  roles, public creators, communities and events inside it, choose the channel
  and buying path, and target within each ad platform's health rules and US
  consumer-health-data law. Use this skill whenever the user asks who to
  target, which audience or segment to win first, for a target list, creator
  shortlist, ABM list, campaign targeting, a Meta/Google/LinkedIn/Reddit
  audience, event or conference plans, or "how do we reach X" for Vybe, even
  if they don't name the skill. Ends by scoring the output with the eval
  rubric and guardrail in vybe-marketing/evals/.
---

# Vybe audience targeting

The job is to name **who exactly** buys first and **how to reach them in ways
that work and are allowed**. The baseline eval (2 Oct 2026) scored the agent
17/30 and 19/30 because it was honest but vague on both. This skill closes
that gap. Read `marketing/marketing-vybe-health-marketing-director.md` and
`vybe-marketing/brand-brief.md` first; this skill does not repeat them.

## The failure this exists to prevent

Two expensive mistakes, both already seen in Vybe's own data:

1. **Buying traffic from nobody.** In September 2026 about 90% of 10,242 paid
   sessions came from India, Bangladesh and Pakistan for a US founding batch,
   and produced 4 signups. Every plan names its market and audience before it
   names a channel.
2. **Targeting the way platforms forbid.** Health-interest targeting, health
   conversion events on a classified site, or pixels firing on health answers
   without consent get an account restricted and can breach state law. Every
   targeting choice names the rule it respects.

## Procedure

**Answer the question asked.** Copy the prompt word for word as the first
line of the output. If it names a segment or an event (HYROX, a team, a
lab), load that segment from `vybe-marketing/marksom.json` and answer for it.
A wider or different scope needs a "Scope change:" line with the reason.
Recommending a skip is allowed when the wedge scores argue for it (for
example, Moat 0 because a competitor holds an exclusive).

Do these in order. Skip none.

### 1. Name one segment
Write: who they are, the shared problem, the trigger that makes them switch
now, and an estimated size **with a source and date**. "Health-conscious
people" fails. If size is unknown, say unknown and how to find out.
Size only the accounts that meet the entry criterion you named (for example,
fire departments that run a wellness-fitness programme, not all career
departments). If that count is unknown, say so and how to find it; never use
the parent total as the high end.

### 2. Run the wedge tests
Score 0 to 3 with evidence: **Pain** (do they feel it today), **Fit** (is
Vybe clearly better for them), **Moat** (would WHOOP, Oura or Garmin have to
break their own model to follow). Name the weakest test out loud.
"No subscription" alone fails Moat: Garmin Cirqa, Fitbit Air, Amazfit Helio,
Polar Loop and Hume all offer it. For builders, test Moat against the open
developer devices too (the Polar BLE SDK, Movesense, and any device already in
the target's own device list) before scoring it 3.

**Fit scores are consistent.** Each 1-to-10 score quotes the agent file's band
it meets, and one test applies to every row: a team that has moved, or is
moving, to a replacement API is not "blocked", so it scores 8 at most. The
rank order follows fit, or says why it does not.

**A worldwide total is not a segment size.** Give a low-to-high estimate
for the segment itself from a countable public source (for example last
year's finisher count for one race, times the share of US residents), label
it "estimate" and show the method.

### 3. Map the targets
When the answer narrows to a segment already in `vybe-marketing/marksom.json`,
carry that segment's evidence into the answer: its `score_why` lines for Pain,
Fit and Moat, and its named targets (communities, creators, publications,
programmes). Search queries and pages are channels, not targets.
List organisations, programmes, roles, public creators, communities, events
and publications, each with **why it matters** and a **source**. Never list
private individuals' names with contact details; name roles ("H2F Integrator",
"health and safety chief") and public figures speaking publicly. Check
community names are what you think (r/HRV is the Honda HR-V car subreddit).

**In-person activations** (a race weekend, a meetup, an event):
- Name at least three local public reach points that sit outside any competitor's exclusive network (run clubs, independent gyms, local public creators), each with an invite method and expected reach. If there are none, estimate turnout from owned channels alone.
- Check the time against the official event schedule so the activation doesn't clash.
- Put "not affiliated with any event or organiser" on every printed and posted piece.
- Treat association by time and place in race week as an ambush-marketing risk for counsel.

### 4. Choose the channel and buying path
Match each target to where it gathers and how it buys: consumer checkout,
unit purchase card (up to $15,000), simplified acquisition (up to $350,000,
small-business set-aside), SBIR/STTR, DIU or AFWERX, a prime contractor, a
research grant, or a developer self-serve plan. Consumer social stays on
Instagram and Facebook unless the founder opens another channel.
Rank the targets in a table with columns for stage, **cost to Vybe** (founder
hours, travel, cash) and evidence, so the order is argued, not asserted.
Fill cash from the cited event page before writing "unknown", and label hour
figures as estimates. Carry every `marksom.json` target for the segment into
the answer or say why it was dropped, and give at least one publication or
community per programme, or say there is none.

### 5. Check the targeting rules

| Platform | Never | Use instead |
|---|---|---|
| Meta (placement) | A primary text whose first line could be any competitor's, with the distinctive idea below the "See more" cut (about 125 characters) or only in the headline, which feed placements often hide | The unclaimed idea (confidence or a blind spot) above the cut or on the creative itself. When the data screen can't be shown honestly, use a privacy proof the live policy supports (Register row 23), not the same row 4 sentence in every ad |
| Meta | Health-condition interests (removed Jan 2022); renaming events to dodge health classification; health answers in pixel parameters | Broad or Advantage+ audiences with creative that self-selects; partnership (creator) ads; neutral URLs and event names; consented first-party lists; Vybe's own signup count as the source of truth |
| Google Ads / YouTube | Claims or landing copy that put Vybe in the "Health" sensitive category (conditions, medical devices), which strips remarketing, Customer Match and lookalikes | Wellness wording from the Claim Register; search on comparison and no-subscription queries; Consent Mode with `ad_user_data` and `ad_personalization` |
| LinkedIn | Nothing health-specific found; still no personal data scraping | Job title, function, seniority, company lists and Groups for B2B and ABM; expect $6 to $15 CPCs |
| Reddit | Targeting on health, biometric or genetic data; Medical & Mental Health communities | Fitness, Wellness and Nutrition interests; named community and keyword targeting; organic 90/10 participation with affiliation disclosed |
| X | Sensitive-category (health) targeting | Keyword and conversation targeting; mostly listening |
| Podcasts | Implying a host's medical endorsement | Host-read reads with the host's own experience |

**Privacy law musts (US):** opt-in consent before collecting consumer health
data, a separate Consumer Health Privacy Policy link on the homepage
(Washington My Health My Data Act; Nevada and Connecticut similar), honour
Global Privacy Control, no geofencing within 2,000 feet of health-care sites,
and treat unauthorised sharing with ad platforms as a breach under the FTC
Health Breach Notification Rule. Not legal advice; counsel confirms.

### 6. Write the message from the Claim Register
One audience, one message, claims at their ladder level with the source
beside each. "Heart rhythm", "ECG" and anything near AFib carry the highest
regulatory risk; do not use them in ads until counsel clears the wording.

- **Look up every claim's row.** Before writing a claim, find its row number
  in the current Claim Register in `vybe-marketing/brand-brief.md` and put the
  number beside it. Label a claim "New" only after searching the Register for
  its phrase. A claim with no row blocks the piece from being scheduled; it
  does not go out with a flag.
- **No absolute promises.** Avoid "never", "always" and "every" about
  outcomes ("a coach is never left trusting one number"). Absolutes are
  allowed only for Vybe's own conduct rules ("never sold") that the Register
  already approves.
- Run the concept check in `vybe-marketing/concept.md` under every piece of copy.
- **Privacy claims match the live policy.** Before any privacy claim goes in
  copy, read vybe.health/privacy, /learn/health-data-privacy-ownership and the
  homepage privacy block, and quote the matching policy clause beside the
  claim. Use only wording the policy supports; if it allows exceptions (the
  law, service providers), say so or drop the claim. "Share" means data
  leaving Vybe; a permission the person left off is "what you left switched
  off", not "what you chose not to share".
- Re-read the Claim Register at the moment of writing; it changes.

### 6b. Source every number

**Read vybe.health with Firecrawl** (Composio; `onlyMainContent: false`,
`waitFor` about 3000 ms), not a quick fetch: the site renders in the browser
and short fetches cut it off. Every site fact, and every "not on the site" or
"doesn't exist", cites the scrape's URL and time.

**Measures need numbers.** A keep or kill threshold is a number, or a named
placeholder the founder fills in (for example `MAX_CPR` from the budget
rule). Justify the minimum sample from the expected conversion rate, not a
round number.


**When pages disagree.** Before writing or rejecting a claim, list how every
page you scraped words it. Also check each page against itself: a
present-tense line ("deployments exist", "funded through pilots", "developers
build through our API") that contradicts the same page's roadmap or
"pre-launch" line is a conflict to flag. If two pages disagree (for example /faq "without
individual visibility" vs /enterprise "per-person detail where the individual
has consented"), cite both and flag the conflict to the founder; never pick one.

**Survey proxies keep their population.** When a survey figure or a
company-defined metric (retention, paid members) stands in for a segment,
quote its question, population or definition word for word, and say which way
it biases the estimate (Oura's 12-month retention counts winbacks and grace
periods, so 100 minus it understates lapse) ("willingness to
share data *with clinicians*") and give one line on why it stands in for the
segment's entry criterion. If it doesn't, find another proxy.

**Quotes and dated sources.** Text in quote marks is word for word from the
source, cited to the exact page it is on; otherwise paraphrase without quote
marks. A procurement or programme stage older than about six months carries a
"status checked [date]" line. Quote the stage in the notice's own words (draft
RFP, presolicitation, solicitation, award), name any contractor the cited
articles already name, and quote the scope clause of any policy you call a
blocker (the 2016 DoD CIO wearables memo says it is "NOT intended to prohibit
any devices"; devices outside it go through normal approval). A dated event or figure
cites the primary page for that year (the organiser, the agency), not last
year's page or an aggregator.

**Before correcting a figure already in the repository**, search for its
real source. Prefer the newest official source. Fix only the citation unless
a newer primary source contradicts the number.

**Creators and outlets.**
- Check every creator for ties to the competitive set (co-authored papers,
  advisory roles, sponsored episodes with WHOOP, Oura, Garmin and the others),
  and record the original publication date, not a republish date.
- No partnership-ad candidate goes forward with an unreviewed competitor tie.
- Copy every competitor-set brand a tie source names (if a sponsor tracker
  lists Garmin, Amazfit, Coros and Polar, all four go in the row).
- A partnership-ad candidate needs a handle on the live channel (Instagram or
  Facebook) with a follower count, source and date; otherwise mark it "not an
  ad candidate".
- For each creator, quote what they have said publicly about subscriptions
  and about baselines, or write "nothing found".
- State how many of the N names can actually be worked with (not event hosts
  or citation-only names); if fewer than asked, fill the gap or say why not.
- A creator's critique is never quoted, or shown as "reviewed by", without
  their written permission.
- Coverage by an outlet the founders own or are linked to (for example
  mopsnmoes.com) always discloses the connection.

Every number and every competitor fact carries a link and the date it was
checked, or the word "(unsourced)". A citation to a repository file quotes
the line it relies on; if the line is not there, the citation is wrong.

### 7. Design the test
Metric, source, minimum sample, decision rule, review date, and what result
would make you drop the segment. **The first decision checkpoint lands within
30 days** (or the window the case names), using the cheapest signal that could
prove the pick wrong, such as meetings booked at the next event. Later
checkpoints may follow.

### 8. Score it
Run `python3 vybe-marketing/evals/check_marketing.py <your draft>` before handing anything back. Running the checker is always allowed, even when you have been asked not to read `evals/`. It must pass. Then score
against `vybe-marketing/evals/rubric.md` and log the run in
`vybe-marketing/evals/results-YYYY-MM-DD.md`. Below 24/30, or a gate
dimension below 2, means rework before it ships.

## Output template

```markdown
# Audience: [segment]
**Who / problem / trigger / size (source, date):** ...
**Wedge:** Pain [0-3] · Fit [0-3] · Moat [0-3] · weakest: ...

| Target | Type | Why it matters | Channel | Buying path | Source |
|---|---|---|---|---|---|

**Targeting rules respected:** ... (consent before any pixel, Global Privacy Control honoured, the consumer health privacy link, no health or competitor interests; and, while /privacy §3 is unresolved, one measurement option that sends Vybe no data to ad platforms, such as link-click optimisation with UTMs read in Vybe's own store)
**Message (Register claims + sources):** ...
**Test:** metric · source · sample · decision rule · review date
**Eval:** guardrail pass/fail · rubric score · lowest dimensions
```

## Where the current answers live

`vybe-marketing/marksom.json` holds the current segments, targets, channels,
platform rules and eval runs, and powers the Marksom hub
(`vybe-marketing/hub/`). Update it when an answer changes, keep the embedded
copy in the hub page identical (same snippet as the scoreboard, pointed at
`marksom.json`), and re-run the eval.
