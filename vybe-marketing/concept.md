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
| 1 | **The answer comes first, as a sentence** | "You are less recovered than usual. The 1am bedtime after Saturday fits most closely; Friday's hard session and two short nights fit too." The readings sit underneath as evidence. |
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
Thryve, ROOK, Spike, Movesense, OpenBCI, Polar SDK). Refreshed on 5 Oct
2026 from each brand's own site, adding Garmin CIRQA. Refresh monthly.

**Hygiene: true, worth saying, never the hook.** Someone else already leads
with each of these.

| Vybe phrase | Already led with by |
|---|---|
| No subscription / no monthly fees | Polar Loop ("No screens. No interruptions. No monthly fees."), Amazfit Helio ("No required subscription.", Vybe's own wording, 5 Oct 2026), Circular, Garmin CIRQA ("no subscription required", garmin.com newsroom, 21 Jul 2026) |
| Screenless / "No screen, no noise" | Amazfit ("No screen. No noise. Just your body's data."), Polar, WHOOP, Garmin CIRQA ("its first screen-free smart band", 21 Jul 2026) |
| Against your own baseline | Circular, WHOOP, Terra |
| Answers in plain sentences | Circular's Kira ("in sentences instead of charts"), Ultrahuman's Jade ("No more dashboards to decode") |
| Data never sold | Oura and others |
| "Developer platform" / "health data API" | WHOOP Developer Platform; Terra, ROOK, Spike, Thryve, Junction; Ultrahuman UltraSignal ("World's first wearable-based developer platform", ultrahuman.com/us/ultrasignal, read 5 Oct 2026) |
| "A platform for apps and plugins built on top" | Ultrahuman PowerPlugs. Say "invites builders in". |
| "See how the score is calculated" / "which factors drive it" | Apple Readiness and Sleep Score (Sep 2026); WHOOP ("recommendations tie back to metrics you can see in the app", 5 Oct 2026) |
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
   can't tell you how sure it is or what it missed". Vybe took this position
   in its own name on /research, but on 5 Oct 2026 that line was gone; the page
   now reads "rather than rely only on a proprietary score". Until the founder
   puts the stance back on the site, quote no site wording for it.
4. **A wearable built to be built on.** The market splits three ways:
   - closed consumer brands, whose data access depends on a membership;
   - aggregators that own no sensor;
   - medical or research kits.

   Ultrahuman now invites developers onto its ring's raw sensor streams and
   loans dev kits (UltraSignal: "World's first wearable-based developer
   platform", read 5 Oct 2026), so this is no longer Vybe's alone. What is
   left is narrower: a band, access the owner grants by consent, and starting
   at the interpretation rather than at signal cleaning. Never say "first" or
   "only". The public FAQ dates API v1 to June 2028 and the SDK to December
   2028, and /research says "no SDK is available today", so say "designed to
   be built on" and "talk to us". Never say "available now"; hold "built
   open" until the founder confirms what is open today.

**Not Vybe's alone, but useful with the calibration clause: "the answers
come with the band".** Google and Garmin now charge for the AI coach on top
of the device, so the paywall has moved from the data to the explanation.
Polar is not one of them: its Loop page says "No locked insights" (5 Oct
2026). Circular, Polar and Amazfit include their guidance, so the line fails
the swap test on its own. Use it only joined to calibration ("Answers that say how
sure they are come with the band"), and only in the same piece as "no required
subscription". A draft may carry it; nothing that carries it is scheduled until
the founder confirms row 21 (Claim Register row 21 says the same).

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
| Vitals | "Your HRV is below your own range for the second morning. Short sleep fits most closely; Tuesday's hard session fits too. Moderate confidence: 19 days of data. Next: an easy day." |
| Move | "Your training load is above your own normal for the third week. The added interval session fits most closely; shorter sleep fits too. Moderate confidence: 21 days of data. Next: keep Thursday easy." |
| Nourish | "On nights you ate after 21:00, your HRV ran lower. Late dinners fit; so do the later bedtimes on those nights. Low confidence: six such nights. Next: try an earlier dinner twice this week." |

## Two halves, one company

Vybe is a band and a platform. Each piece of copy leads with one half and
leaves room for the other. Over a week, both halves get marketed (the
Two-Product Test in the agent file).

| Where | Who reads it | Lead with | Then |
|---|---|---|---|
| LinkedIn company page, founder LinkedIn | Builders, partners, researchers, tactical and performance buyers, investors, hires | The company: score-skeptic stance, calibrated answers, built to be built on | The band as the proof |
| Instagram, Facebook | End users | One calibrated answer, shown, not described | No required subscription, data stays yours |
| /developers, builder email | Developers, labs, startups | "Start at the interpretation, not at signal cleaning"; licensed, consented access | Tie the answer back to the band that produces it, in the builder's terms (what they can build on). Never "reference device" or "reference standard" in lab or research copy: in validation science it means the criterion measure |
| Tactical and team buyers | H2F, POTFF, performance staff | "Designed to show readiness in aggregate, with consent, in answers that say how sure they are" (Claim Register row 22) | Give the reason no screen matters to a team: there is nothing to check or switch off, so it stays on through a training cycle and the group's record has fewer gaps. Row 22's subject is the team view, not the band. Per-person detail only in the /enterprise wording, "with per-person detail where the individual has consented to share it", and flag that /faq disagrees. No GPS waits for row 20 |
| Waitlist, homepage | Mixed | Calibrated answers | Hygiene as proof points underneath |

Cells in quotation marks are wording to use exactly. Every other cell is a
direction: carry it out, never print it.
| Search pages | People asking a question | The direct answer to their question (HRV, alternatives, screenless) | Calibrated answers, then the waitlist. In search, "screenless fitness tracker" (~40k a month) and "whoop alternative" are worth ranking for even though they fail the swap test as hooks. |

## The concept check

Run all eight questions before any copy ships. The agent writes the answers
in one line each under the draft, and **each answer quotes the words in the
copy that satisfy it**. If no words in the copy satisfy an item, the item
fails; the notes cannot supply what the copy lacks (a sample answer "above
it", an email body that is not written).

1. **Audience and channel.** Which one audience, on which channel, and which half leads (see the table above)? Every piece carries **both columns of its row**: the lead, and the "then" line underneath. The weekly Two-Product Test does not excuse dropping the second column from a single piece. A one-line format (a tagline, a pricing line, an email's first line) names the companion line that carries the second column, and the two are graded together. Builder short lines lead with what the builder gets (start at the interpretation, consented access), not with the band, and say "pre-launch" or "design partner". Placement is part of the test:
   - **The lead is in the first sentence** (the first ten words in a short format): the row's idea, with any quoted wording exact.
   - **The "then" column comes after the shown answer and points back to it**, in your own words: say that the band is designed to produce that answer, and word it differently in each piece. Any sentence that ties the answer to "no (required) subscription" ("that answer, with no required subscription", "no subscription stands between you and it") is row 21 and carries its hold. Without a hold, "no required subscription" gets its own sentence about the band, apart from the answer, and not straight after the sentence that says the band produces the answer (the two together say row 21). Put another sentence between them, or carry row 21's hold. Vary the "then" line across a feed: one stamped closing sentence reads as boilerplate. In the weekly Two-Product Test, read the week's pieces side by side: no two share a hook template, a pointer-and-subscription pair or a closing line. Carry every part of the "then" cell (on Instagram and Facebook: "no required subscription" and a data line in row 4 or row 23 wording), directly after the sentence that points back to the answer, with no teaching or evidence paragraph in between. A hygiene list tacked on at the end does not count, and neither does calling hygiene "the proof".
   - **Quoted wording goes in exactly; directions get carried out, never printed.** Wording in quotation marks in the table, or marked as /enterprise or Claim Register wording, goes into the copy exactly. Rewording it ("with consent" turned into an "only" sharing promise) makes a new claim, and a new claim needs the Register first. Every other cell is a direction: "One calibrated answer, shown, not described" means show one answer; it is never the post's opening line. Test: if a sentence only makes sense to someone who has read this table, rewrite it. A copy sentence never reuses a direction cell's wording beyond its quoted phrases.
2. **The swap test.** Is the hook something only Vybe can say? If a competitor's name fits, rewrite it.
3. **Show it.** Does the piece show one real-shaped answer (a sentence, its confidence, one blind spot) instead of describing "insights"?
4. **Order.** Are the unclaimed ideas first and hygiene second?
5. **Two products.** Over the week, does this piece and its neighbours market both the band and the platform?
6. **Claims.** Is every claim in the Claim Register at the right status, in the Register's own wording (row 4: "never sold; shared only with your consent, with service providers that run the service, or where the law requires", never "nothing shared")? "Designed to" applies to **every sentence** that asserts rows 14 to 17, 19 or 22, calls to action included. Before launch, never write in the present tense that Vybe *does* something ("every answer is", "the answer Vybe gets wrong"). "Designed to" must govern the sentence's main verb: a hedge in a later clause does not cover "Vybe shows…" at the start. The same goes for noun phrases that assume a design commitment already works ("the record of what worked", "the times it got it wrong"): rewrite them as "designed to" sentences. Does every example answer give more than one explanation? Questions, pricing words and citations are claims too: a call-to-action question never assumes a cause in the reader's body ("what your late dinners do"); no pricing-scope words beyond row 2 ("buy once", "forever"); a cited study supports only what it measured (UK Biobank compared daytime and night light, not morning light). Blind spots are claims too: a "what Vybe could not see" line never names a gap in what the band senses while that spec is unconfirmed (being outside, daylight, location); write it as a gap in the person's log or context ("mornings you didn't log").
7. **Roadmap and offers.** Does anything rely on an unreleased feature, an unconfirmed spec (battery life, "validated", ECG, the ring) or an internal fact? Builder, lab and team copy invites a conversation as a design partner (row 18). It never promises signal access, a device to test, terms or a date the founder has not confirmed, and never states conversations, pilots or partners as happening ("we're talking with performance teams") unless the founder has confirmed them; invite instead ("we're looking for design partners").
8. **Voice.** Plain and declarative, one action instead of a list, no hype, and willing to say "not yet" or "we don't know". **Short formats** (a tagline, a subject line, an email's first line, a hook, a homepage sub-line or subhead) put the unclaimed idea in the first ten words and stay under 25 words. They never open on context the reader already knows.

## Tensions only the founder can settle

Until each one is settled, copy takes the safe side shown.

| Tension | Safe side until decided |
|---|---|
| "No Subscription" (homepage) and "No subscription required" (site footer) vs "no required consumer subscription" (site body) vs any paid feature the founder may add later | Say "no required subscription". Never say "free forever" or "$0, ever"; the /about page's "$0 Monthly subscription, ever" needs review. |
| Five-factor names: the site says Restore, Move, Nourish, Connect, Vitals. The 2 Sep kickoff used Move, Nourish, Recover, Mind, Health. | Use the site's names; they are the latest published version. |
| The /about page says "4 Signals read as one"; everywhere else says five | Say five. The /about stat needs fixing. |
| Battery: "30 days" (Instagram, 25 Sep) vs "lasts for days" (site) | "Lasts for days" until the founder confirms a number. |
| ECG and heart-rhythm wording vs no FDA clearance | "HRV" and "heart rate" only, until counsel clears it (Claim Register 5, 5a). |
| Band only (brand) vs a Vybe Ring on /hardware and the compare pages | "The band". Mention the ring only when the founder approves it. |
| Platform today vs API v1 in June 2028 (public FAQ) | "Built open", "talk to us", "design partners". Never "available now". |
| "Never sold" vs enterprise, research and data-services revenue | Enterprise and research copy uses the /enterprise wording: group-level views, "with per-person detail where the individual has consented to share it" (scraped 3 Oct 2026). The site disagrees with itself: /faq says enterprises license insight "without individual visibility". Never "aggregate only" or "never the individual" until the founder reconciles the two pages. |
| "Vybe Intelligence, no hardware required" vs "We build the wearable" | Lead with the wearable; licensing is a builder-channel detail. |
| Audience order: the founder pitched everyday people first; the plan's wedge is tactical and performance teams; the research put builders first | Company channels lead with the company story. Consumer channels lead with calibrated answers. The wedge stays as in `plan-2026-q4.md` until the founder decides. |
| Founder-identity story (veteran-, woman- and minority-owned) | Only in a piece the founder has approved. |
| Homepage "Nothing sold and nothing shared" vs the live privacy policy, which allows sharing with service providers and where the law requires | Use Claim Register row 4's wording. The founder fixes the homepage line. |
| Export: /privacy §6 says "export your data at any time by contacting us"; /faq says "Yes. Your history is yours to take with you or erase"; Register row 17 is the design commitment "export takes one tap" (all read 3 Oct 2026) | No export or delete claim in copy until the founder settles it. /faq's "shared only with your explicit, revocable consent" also leaves out the policy's exceptions for service providers and where the law requires, so use row 4's wording. |
| Homepage "first 1,000 guaranteed a position to buy" vs /waitlist "evaluated on eligibility" | Don't use the offer until the two pages agree. |
| Pages that contradict their own "pre-launch" line (read 3 Oct 2026): /faq "funded through the founding batch, early enterprise and research pilots" (pilots are dated Jan 2027 on the same page); /enterprise "Vybe enterprise deployments exist" | Copy says pilots and deployments are "planned" or "being designed with partners". The founder fixes both lines. |
| /waitlist loads a Google Ads tag, GA4 and a Replit analytics script with no visible consent step or GPC check, and no footer links a consumer health privacy policy (Firecrawl rawHtml, 3 Oct 2026) | No paid traffic to /waitlist until a consent gate holds every tag and the health privacy link is live (plan week 1, action 7). |
| /privacy §3 "We do not use your data for advertising targeting" vs the plan's weeks 7 to 10 paid retargeting, waitlist lookalikes and conversion events sent to ad platforms (read 3 Oct 2026) | Hold all three until counsel rules. Broad audiences with self-selecting creative stay allowed. |
| /research says "SDK libraries exist for teams instrumenting custom protocols" and offers "raw signal access" (scraped 3 Oct 2026), while the public FAQ dates the SDK to December 2028. /faq itself also says, in the present tense, "Developers build on clean physiology through our API" and "Researchers access sensor level data under consent" | Say "built open", "talk to us" and "design partners". Never say the SDK or raw signal access exists. The founder fixes /research, and raw signal access needs a Register row before any copy uses it. |
| /research "Vybe's validated sleep, recovery and HRV interpretation" vs /developers "No clinical validation is claimed" (both scraped 3 Oct 2026) | Never say "validated". The founder fixes the /research line. |
| /enterprise says a dip in readiness "can be traced to the things that actually caused it" (scraped 3 Oct 2026) | Copy names likely explanations, never causes ("fits most closely"). Counsel and the founder review the /enterprise line. |
| /hardware lists no GPS line and says "Bluetooth-first", not "Bluetooth-only" (scraped 3 Oct 2026) | Say neither "no GPS" nor "Bluetooth-only" until the founder confirms the spec (Claim Register row 20). |

## Learning log

Newest first. Every miss, correction from the founder, or result that
changes how the concept is told gets one entry: date, what happened, what
changes.

- **2026-10-05. Monthly concept check, evals and first weekly scoreboard.**
  - The founder rewrote most of vybe.health in "pre-launch / planned / not
    available today" wording. This fixed most site conflicts and opened new
    ones (Firecrawl, 22 pages, read 5 Oct):
    - /faq says "HRV and heart-rate sensing specifications remain
      unconfirmed", and /hardware says "vital-sign sensing unconfirmed".
    - The homepage, /faq and /hardware promise "The first 1,000 on the
      waitlist are guaranteed a position to buy a band", but /terms §3 says
      waitlist signups "do not guarantee availability".
    - The /enterprise wording that Register row 22 quoted is gone; it now
      says "individual detail only by consent".
  - Competitors moved too. Ultrahuman's UltraSignal now claims part of
    "built to be built on", Garmin CIRQA joins "screenless" and "no
    subscription", and Amazfit uses "No required subscription" word for
    word. Polar does not charge for its coach.
  - Evals, fresh writer and separate grader: C4 16, C3 17, S3 18 (all pass);
    targeting case 7 24 of 30, a pass by one point (`evals/results-2026-10-05.md`).
    The writer of case 7 caught that the first draft of this week's
    scoreboard broke plan action 3 (no conversion imports until counsel) and
    the concept's consent-gate hold on paid traffic. The scoreboard's change
    is now "pause all paid".
  - **Changes:**
    - Treat HRV and heart-rate sensing as unconfirmed specs. Any example
      answer that reads HRV is labelled "prototype, sample data" and phrased
      with "designed to".
    - Before scheduling copy that quotes site wording, re-read that page.
      Read /terms in every offer check. Founding-batch offer copy stays on
      hold (row 11).
    - Run a targeted competitor search before calling anything unclaimed.
    - Before writing a scoreboard's "change", check it against this file's
      rules table and the plan's open week-1 actions.
      Never take paid-labelled sessions as outside traffic without a
      new-user and `gclid` check, and draw no conclusion from fewer than 5
      signups.
    - Q1's pointer is now a direction, not a quoted sentence, after
      writers copied it word for word.
    - The search skill's unfunded fallback now quotes the last dated
      results pull, and refreshed briefs carry earlier queries forward.
  - **Still open:** `check_marketing.py` does not count words on an
    unlabelled first line.
- **2026-10-03. Final regression, all rules in force.** All eight copy cases
  pass (C1 18, C2 17, C3 17, C4 17, C5 17, C6 17, C7 16, C8 18). Four pieces
  ended on the same stamped line tying the answer to "no required
  subscription", which is row 21 made without a hold. Q1 and the Register now
  say so, Q6 adds that blind spots are claims, and the guardrail blocks the
  pattern section by section.
- **2026-10-03. Retests after the regression.** C1 rose to 18. The
  placement rules lifted D2 to 3 in every retested piece, but the "word for
  word" rule made writers print the table's directions as copy. The fix: quoted
  cells stay exact, and every other cell is a direction to carry out. C7 then
  failed on "Vybe shows…", so "designed to" now governs the main verb, and
  Register row 22 holds the team view. Round 3: C4 16, C6 17, C7 17, so all
  eight cases pass. The guardrail now counts short formats.
- **2026-10-03. Regression run, C1 to C8 under the final rules.** A fresh
  writer redid all eight cases and a separate grader scored the copy only.
  Seven passed (C1 16, C2 17, C3 18, C4 15, C5 17, C6 16, C8 16). C7, the
  H2F one-pager, failed the claims gate at 14: it wrote "shared only under
  each soldier's revocable consent", which drops row 4's exceptions, and it
  stated design-partner conversations as fact. The guardrail missed it
  because one "not a medical device" cleared the whole paragraph. The weak
  pattern across four pieces: the channel row's second column was tacked on,
  not built in. **Changes:**
  - Q1 now sets placement: the lead in the first sentence, the "then" column
    after the shown answer and pointing back to it, and row phrases word for word.
  - Q7 bars stating conversations, pilots or partners as happening.
  - The tactical row's lead carries consent and calibration in one sentence,
    and uses the /enterprise wording on per-person detail.
  - Row 21 reads the same here and in the Register: drafts may carry it
    joined to calibration; nothing carrying it is scheduled until confirmed.
  - `check_marketing.py` checks sentence by sentence and has a blocking
    `privacy-claim` rule. On the saved drafts it now catches C7's line and
    the old "nothing shared" wording it used to pass.
  - Three site conflicts were added to the tensions table (/research
    "validated", the /enterprise cause line, no GPS line on /hardware).
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
  - "The answers come with the band" (row 21) replaces "no subscription" as the pricing line.

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
