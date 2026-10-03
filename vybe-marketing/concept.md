# The Vybe Health concept

Read this before writing anything for Vybe. It says what the company is, the
one idea the product is built on, which parts of the story are crowded and
which are Vybe's alone, and the check every piece of copy passes before it
ships. The brand brief (`brand-brief.md`) holds the approved claims; this
file holds the idea those claims serve.

Built on 3 Oct 2026 from four reads:
- the product prototype and its design rules (`vybe-app/README.md` and its sample screens);
- the founder's own words from the 2 Sep kickoff meeting and the 1 Oct founder uploads (`funding-scraper/VYBE_PROFILE.md`);
- all 24 public vybe.health pages and all 5 Instagram posts (read through Firecrawl and the Instagram API on 3 Oct);
- the self-descriptions of 16 category players.

Private detail (costs, suppliers, unreleased features, partner names) stays
in the founder's files and never comes into this repository.

## The concept in one line

**You don't need more data. You need what the data tells you, how sure it is,
and whether its advice worked.**

The first sentence is the team's own framing from the 2 Sep kickoff ("users
don't need more data, they need what the data tells them"). The rest is what
the prototype does about it.

## The concept in one paragraph

Every wearable hands you a score and leaves you to work out what it means.
Vybe began with its founders' frustration with opaque scores that leave you
guessing. Vybe answers instead. The answer is
a plain sentence, read against your own changing baseline across five
connected signals (Restore, Move, Nourish, Connect, Vitals). It says how
confident it is and why, names what it could not see, and later checks
whether its own suggestion worked, including the times it got it wrong. You
buy the band once; the answers come with it; your data stays yours. And the
company is built so others can build on it: **"We build the wearable. They
build what's possible with it."**

## The product promises that are also marketing promises

These come from the prototype app. They are design commitments, not shipped
features. In public copy say "built to" or "designed to" until the founder
confirms each one has shipped. Claim Register rows 14 to 17 and 19 in
`brand-brief.md` track them; row 18 covers the platform direction.

**The example sentences are internal illustrations, not approved copy.**
Public copy may quote one only when it is labelled "prototype, sample data".
Every example names more than one explanation, because a change in HRV or
recovery has no single cause (evidence library, `brand-brief.md`). Explanations
are everyday ones (sleep, training, timing, travel); an illness or condition is
never offered as an explanation.

| # | Promise | What it looks like in the product |
|---|---|---|
| 1 | **The answer comes first, as a sentence** | "You are less recovered than usual. The 1am bedtime after Saturday fits best; Friday's hard session and two short nights fit too." The readings sit underneath as evidence. |
| 2 | **Confidence is stated in words, with its reason** | "Moderate confidence — three nights of data since the change, and one known context event." Never a percentage. |
| 3 | **It shows what it could not see** | "What Vybe could not see: whether the late nights were work or choice, anything you drank, how you actually feel today." |
| 4 | **It grades its own advice** | The criterion is written down before the attempt. The record is a fraction ("4 of 7"), and there is a section called "What Vybe got wrong". |
| 5 | **Your own baseline, not a population norm** | "Higher than your own normal" instead of "above average for your age". |
| 6 | **Five signals, one system** | A Nourish screen can make a Restore argument: the factors talk to each other. |
| 7 | **Patterns are not causes** | "This is a pattern, not a cause." The weeks a pattern broke are shown at the same size as the weeks it held. |
| 8 | **The boundary is on the claim, not your data** | Asked "Do I have sleep apnea?", it says that is outside what Vybe does, still shows the breathing signal, and suggests exporting it for a clinician. |
| 9 | **Nothing on by default; export and delete up front** | Every permission switch starts off. Export is one file you can open, and delete asks twice. |
| 10 | **Honest on day one** | First run ends on "Today — nothing yet", then says what arrives after 3 nights, 2 weeks and 6 weeks. |

## Crowded and unclaimed

Checked on 3 Oct 2026 against 16 category players (WHOOP, Oura, Ultrahuman,
Polar, Garmin Health, Amazfit, Circular, Movano/Evie, Terra, Junction,
Thryve, ROOK, Spike, Movesense, OpenBCI, Polar SDK). Refresh monthly.

**Hygiene: true, worth saying, never the hook.** Someone else already leads
with each of these.

| Vybe phrase | Already led with by |
|---|---|
| No subscription / no monthly fees | Polar Loop ("No screens. No interruptions. No monthly fees."), Amazfit Helio, Circular |
| Screenless / "No screen, no noise" | Amazfit ("No screen. No noise. Just your body's data."), Polar, WHOOP |
| Against your own baseline | Circular, WHOOP, Terra |
| Answers in plain sentences | Circular's Kira ("in sentences instead of charts"), Ultrahuman's Jade ("No more dashboards to decode") |
| Data never sold | Oura and others |
| "Developer platform" / "health data API" | WHOOP Developer Platform; Terra, ROOK, Spike, Thryve, Junction |
| "A platform for apps and plugins built on top" | Ultrahuman PowerPlugs. Say "invites builders in". |
| "See how the score is calculated" / "which factors drive it" | Apple Readiness and Sleep Score (Sep 2026) |
| "Which habits are working" / "recalibrates as you implement" | WHOOP Behavior Trends, Ultrahuman Dynamic Recovery, Samsung habit rate. These grade **the user**, not the advice. |
| "We would rather you checked than trusted a banner" | Circular |

**Vybe's alone: lead with these.**

1. **Calibrated answers.** It tells you how sure it is and what it couldn't
   see. No consumer brand claims this (8 AI coaches checked on 3 Oct 2026).
   It builds trust only in one shape: a reason you can count ("three nights of
   data"), the likely explanations in order, and one next step. A bare "not
   sure" lowers trust. Every AI coach in the category sells
   fluency, and the only admission of limits is a disclaimer ("Advisor can
   make mistakes"). Vybe's /learn articles already write this way ("Read the
   evidence and the limits together"), so the claim is credible.
2. **It keeps score on itself.** No one publicly tracks whether their own
   suggestions worked. Three brands grade the user's habits, so always say
   "Vybe grades its own advice", never "see what's working". A public,
   time-stamped log of graded suggestions would be proof no wearable publishes.
3. **Score-skeptic as a stance.** Apple now shows how its scores are
   calculated, so the stance is no longer "scores are opaque". It is "a score
   can't tell you how sure it is or what it missed". Vybe takes this position in its own name
   ("a proprietary readiness score and no way to inspect, reproduce or justify
   how it was derived", from /research). Today it is buried on /research and in
   a WHOOP explainer.
4. **A wearable built to be built on.** The market splits three ways:
   - closed consumer brands, whose data access depends on a membership;
   - aggregators that own no sensor;
   - medical or research kits.

   No one offers a consumer band whose owner invites builders in. The public
   FAQ dates API v1 to June 2028 and the SDK to December 2028, so say "built
   open from day one" and "talk to us". Never say "available now".

**Not Vybe's alone, but useful with the calibration clause: "the answers
come with the band".** Google, Garmin and Polar now charge for the AI coach
on top of the device, so the paywall has moved from the data to the
explanation. But Circular also includes its coach, so the line fails the swap
test on its own. Use it only joined to calibration ("Answers that say how
sure they are come with the band"), only in the same piece as "no required
subscription", and only once the founder confirms it (Claim Register row 21).

**The swap test.** Put a competitor's name in place of "Vybe" in the line. If
it is still true, the line is hygiene, not the concept. "No screen, no
subscription" passes for Polar. "It tells you how sure it is, and checks
whether its advice worked" passes for no one.

## The five pillars, by job

Evidence: `reports/Vybe five pillars marketing.md` (3 Oct 2026, not in the
repository). US monthly searches are from DataForSEO.

| Pillar | Demand | Competition | Its job in the marketing |
|---|---|---|---|
| **Vitals** (HRV, heart rate) | ~400k a month; "what is a good hrv" 14.8k at KD 17 | Turning medical (Apple, Oura and WHOOP blood pressure, ECG) | **Search lead.** Answer the HRV questions people ask. Say "HRV and heart rate", never "heart rhythm" or "ECG". |
| **Restore** (sleep) | ~239k a month; "sleep tracker" down 42% | Most crowded: 8 of 11 brands lead with it | Proof, not hook. Show a sleep answer that names its confidence. |
| **Nourish** (food timing) | ~30k a month and rising; "meal timing" KD 7 | Nobody leads with it | **Social lead.** "Late dinner, lower HRV?" shows five signals as one system. |
| **Connect** | Daylight cluster ~22k and rising ("sunlight exposure" +97%) | Nobody measures it | Launch as **daylight and daily rhythm**, only if the band has a light sensor. People time and alone time are logged by the user, and are never scored against each other. **Until the sensor is confirmed**, Connect content teaches daylight itself (evidence library) and uses what the person logs; it never states what the band does or does not sense. |
| **Move** (training load) | ~2k consumer searches | Garmin, Polar, Amazfit | Team and tactical channels. For consumers use "overtraining" and "rest day". A Move piece shows a Move answer (load against the person's own normal), not a sleep answer. |

Never say Vybe detects loneliness or stress from HRV: wrist HRV explains
about 1–2% of perceived stress. Never say which pillar ships first; sequencing
is roadmap.

**Example answer shapes** (internal illustrations; quote only as "prototype,
sample data"):

| Pillar | Shape |
|---|---|
| Vitals | "Your HRV is below your own range for the second morning. Short sleep fits best; Tuesday's hard session fits too. Moderate confidence: 19 days of data. Next: an easy day." |
| Move | "Your training load is above your own normal for the third week. The added interval session fits best; shorter sleep fits too. Moderate confidence: 21 days of data. Next: keep Thursday easy." |
| Nourish | "On nights you ate after 21:00, your HRV ran lower. Late dinners fit; so do the later bedtimes on those nights. Low confidence: six such nights. Next: try an earlier dinner twice this week." |

## Two halves, one company

Vybe is a band and a platform. Each piece of copy leads with one half and
leaves room for the other. Over a week, both halves get marketed (the
Two-Product Test in the agent file).

| Where | Who reads it | Lead with | Then |
|---|---|---|---|
| LinkedIn company page, founder LinkedIn | Builders, partners, researchers, tactical and performance buyers, investors, hires | The company: score-skeptic stance, calibrated answers, built to be built on | The band as the proof |
| Instagram, Facebook | End users | One calibrated answer, shown, not described | No required subscription, data stays yours |
| /developers, builder email | Developers, labs, startups | "Start at the interpretation, not at signal cleaning"; licensed, consented access | The band as the reference device |
| Tactical and team buyers | H2F, POTFF, performance staff | Readiness in aggregate, with consent; screenless, no GPS | Calibrated answers keep athletes and operators from over-trusting a number |
| Waitlist, homepage | Mixed | Calibrated answers | Hygiene as proof points underneath |
| Search pages | People asking a question | The direct answer to their question (HRV, alternatives, screenless) | Calibrated answers, then the waitlist. In search, "screenless fitness tracker" (~40k a month) and "whoop alternative" are worth ranking for even though they fail the swap test as hooks. |

## The concept check

Run all eight questions before any copy ships. The agent writes the answers
in one line each under the draft, and **each answer quotes the words in the
copy that satisfy it**. If no words in the copy satisfy an item, the item
fails; the notes cannot supply what the copy lacks (a sample answer "above
it", an email body that is not written).

1. **Audience and channel.** Which one audience, on which channel, and which half leads (see the table above)? Every piece carries **both columns of its row**: the lead, and the "then" line underneath. The weekly Two-Product Test does not excuse dropping the second column from a single piece. A one-line format (a tagline, a pricing line, an email's first line) names the companion line that carries the second column, and the two are graded together. Builder short lines lead with what the builder gets (start at the interpretation, consented access), not with the band, and say "pre-launch" or "design partner".
2. **The swap test.** Is the hook something only Vybe can say? If a competitor's name fits, rewrite it.
3. **Show it.** Does the piece show one real-shaped answer (a sentence, its confidence, one blind spot) instead of describing "insights"?
4. **Order.** Are the unclaimed ideas first and hygiene second?
5. **Two products.** Over the week, does this piece and its neighbours market both the band and the platform?
6. **Claims.** Is every claim in the Claim Register at the right status, in the Register's own wording ("nothing shared without consent", not "nothing shared")? "Designed to" applies to **every sentence** that asserts rows 14 to 17 or 19, calls to action included. Before launch, never write in the present tense that Vybe *does* something ("every answer is", "the answer Vybe gets wrong"). Does every example answer give more than one explanation?
7. **Roadmap and offers.** Does anything rely on an unreleased feature, an unconfirmed spec (battery life, "validated", ECG, the ring) or an internal fact? Builder, lab and team copy invites a conversation as a design partner (row 18). It never promises signal access, a device to test, terms or a date the founder has not confirmed.
8. **Voice.** Plain and declarative, one action instead of a list, no hype, and willing to say "not yet" or "we don't know". **Short formats** (a tagline, a subject line, an email's first line, a hook) put the unclaimed idea in the first ten words and stay under 25 words. They never open on context the reader already knows.

## Tensions only the founder can settle

Until each one is settled, copy takes the safe side shown.

| Tension | Safe side until decided |
|---|---|
| "No Subscription" (homepage) vs "no required consumer subscription" (site body) vs any paid feature the founder may add later | Say "no required subscription". Never say "free forever" or "$0, ever"; the /about page's "$0 Monthly subscription, ever" needs review. |
| Five-factor names: the site says Restore, Move, Nourish, Connect, Vitals. The 2 Sep kickoff used Move, Nourish, Recover, Mind, Health. | Use the site's names; they are the latest published version. |
| The /about page says "4 Signals read as one"; everywhere else says five | Say five. The /about stat needs fixing. |
| Battery: "30 days" (Instagram, 25 Sep) vs "lasts for days" (site) | "Lasts for days" until the founder confirms a number. |
| ECG and heart-rhythm wording vs no FDA clearance | "HRV" and "heart rate" only, until counsel clears it (Claim Register 5, 5a). |
| Band only (brand) vs a Vybe Ring on /hardware and the compare pages | "The band". Mention the ring only when the founder approves it. |
| Platform today vs API v1 in June 2028 (public FAQ) | "Built open", "talk to us", "design partners". Never "available now". |
| "Never sold" vs enterprise, research and data-services revenue | Enterprise and research copy says aggregate only, with revocable consent. The founder sets the exact wording. |
| "Vybe Intelligence, no hardware required" vs "We build the wearable" | Lead with the wearable; licensing is a builder-channel detail. |
| Audience order: the founder pitched everyday people first; the plan's wedge is tactical and performance teams; the research put builders first | Company channels lead with the company story. Consumer channels lead with calibrated answers. The wedge stays as in `plan-2026-q4.md` until the founder decides. |
| Founder-identity story (veteran-, woman- and minority-owned) | Only in a piece the founder has approved. |

## Learning log

Newest first. Every miss, correction from the founder, or result that
changes how the concept is told gets one entry: date, what happened, what
changes.

- **2026-10-03. Refinement block, cycles 1 and 2.** Fresh writers and graders.
  - Lab email: 13 → 15. Pricing line: 11 → 16. HRV brief: 17. Screenless brief: 16. Nourish, Connect and Move pieces: 16 to 17.
  - Misses that became rules:
    - "the answers come with the band" alone fails the swap test (Claim Register row 21);
    - a Move piece used a sleep answer;
    - daylight copy stated what the band can't sense;
    - concept-check notes claimed what the copy didn't contain.

  Lesson: grade the copy, never the notes about the copy.
- **2026-10-03. Five-pillar research.** Six research tracks (search demand,
  competitor messaging and ads, Connect science, launch playbooks, channel
  costs, proof by audience). **Changes:**
  - pillars now have jobs: Vitals leads search, Nourish leads social, Connect is daylight, Move goes to teams;
  - calibration must carry a countable reason, ranked explanations and a next step;
  - new crowded phrases: Apple's score transparency, user-habit grading, Circular's "checked than trusted", Ultrahuman's "platform";
  - "The answers come with the band" replaces "no subscription" as the pricing line.

  Lesson: the open ground moves monthly, so the swap test needs this table kept current.
- **2026-10-03. Concept test, round 3 (lab email only).** The claims gate
  now passes, with no unconfirmed offer, but the email still scored 13/18. It
  opened on the lab's own work, which fits any competitor, and ran as one
  63-word sentence. **Change:** a short-format rule in check Q8. Lesson: in
  short copy, the distinctive idea has to arrive first or it does not arrive.
- **2026-10-03. Concept test, round 2.** The homepage hero (18/18) and the
  Instagram caption (16/18) passed. The lab email failed again: it offered
  signal access and a device that nobody has confirmed. **Changes:**
  - check Q7 covers offers;
  - example explanations stay everyday ones;
  - Claim Register row 19 was added.

  Lesson: in builder copy, the risk moves from health claims to commercial
  promises.
- **2026-10-03. Concept test, round 1.** The agent knew the concept (12/12)
  but failed all three cold copy cases (12 to 13 of 18). It hedged a design
  commitment once, then wrote it in the present tense in the call to action.
  It copied this file's single-cause example answer. It dropped the second
  line of its channel row. **Changes:**
  - the examples are marked as illustrations and now name competing explanations;
  - check Q1 requires both columns of the row;
  - check Q6 applies "designed to" to every sentence.

  Lesson: an example in this file becomes copy, so every example must pass
  the same rules as copy.
- **2026-10-03. LinkedIn company page miss.** The first tagline I drafted
  ("Private, screenless health intelligence. Five signals read against your
  own baseline. Your data stays yours.") failed three checks:
  - The swap test: Polar, Amazfit and Circular all fit it.
  - The channel table: LinkedIn is a company channel, and the draft sold only the band.
  - The order rule: hygiene first, none of the unclaimed ideas.

  The founder said to keep learning the concept. **Changes:**
  - This file now exists, and the agent reads it first.
  - The eight-question concept check is mandatory before copy ships.
  - `evals/concept-test.md` scores concept fidelity.
  - The LinkedIn copy is redone in `linkedin-company-page.md`.
