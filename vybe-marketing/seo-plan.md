# Vybe Health — Search Plan v1 (1 Oct 2026)

Built from the founder's competitor keyword research (WHOOP, Oura vs.
vybe.health, Sep 2026) and the Search Console baseline in
`scoreboard-2026-09-30.md`. It replaces the "content clusters" bullet in the
Q4 plan.

## What is known and what is not

- **Known.** WHOOP sells membership tiers ("Choose a membership") and Oura
  directs buyers to "Explore Membership". Vybe's site already has a
  WHOOP-alternative statement on the home page, `/compare/oura-ring-alternative/`,
  an HRV explainer and a screenless-wearable explainer.
- **Known.** Search Console shows 15 impressions and 0 clicks in four weeks.
  The Oura comparison page sits at position 7 and the screenless page at
  position 8, each on a single impression.
- **Not known.** Search volume, keyword difficulty and competitor positions.
  The research declined to invent them and so does this plan. Before
  production order is locked, pull an Ahrefs or Semrush export for whoop.com,
  ouraring.com and vybe.health (United States database, positions 4 to 10,
  1,000+ monthly searches, themes recovery, HRV, strain, sleep) and score each
  candidate on volume, difficulty, rank gap, intent, relevance, existing URL,
  SERP-feature risk and conversion value.

## The rule that reconciles search with positioning

Searchers type "no subscription", so titles and H1s use that phrase where it
matches the query. The page itself never stops there. Within the first screen
it says what is specific to Vybe: your own baseline, the five factors read as
one signal, and data you own. "No subscription" is the door; the argument is
behind it. This keeps the agent's rule that crowded claims are proof points,
not the whole hook.

## Update, 3 Oct 2026: demand data moves "screenless" into Phase 1

DataForSEO (US, 3 Oct 2026) puts "screenless fitness tracker" at about
40,500 searches a month on a 12-month average (60,500 in August, 110,000 at
the May to July peak), KD 41, CPC $1.72. The original Phase 1 category
cluster ("health band no subscription" and its variants) gets about 10 to
200 a month. So the Phase 1 category page now targets the screenless
cluster, starting with the easy long-tails: "fitness tracker no screen"
(KD 7), "best screenless fitness tracker" (KD 9) and "screenless fitness
band" (KD 12). "No subscription" stays in the page as proof. Its brief goes in
`briefs/` once graded; the Phase 2 screenless pillar becomes a supporting
guide that links to it. HRV explainers (Vitals) also move up; see
`briefs/what-is-a-good-hrv.md`.

## Phase 1: three commercial pages (weeks 3 to 6)

| Page | Primary query cluster | Title (≤60 chars) |
|---|---|---|
| WHOOP alternative | whoop alternative no subscription, whoop without membership, whoop monthly fee alternative, screenless whoop alternative | WHOOP Alternative Without a Subscription: Meet Vybe |
| Oura alternative (expand the existing page) | oura alternative no subscription, oura ring alternative no membership, health band vs smart ring | Oura Ring Alternative With No Monthly Membership |
| Category (updated 3 Oct) | screenless fitness tracker, fitness tracker no screen, best screenless fitness tracker, screenless fitness band; then fitness tracker no subscription | Screenless Fitness Trackers: What to Look For, and Vybe |

Each page carries: a plain feature comparison that only lists what Vybe can
substantiate, a "what you own" section, FAQ schema, transparent limitations,
and the waitlist call to action. No feature-parity claim with WHOOP's or
Oura's coaching, medical or proprietary features. No price or battery
comparison against a named competitor (agent rule).

## Phase 2: four pillar pages, each linking to the commercial pages

| Pillar | Starting queries | Title |
|---|---|---|
| HRV | what is a good HRV, how to improve HRV, HRV tracker no subscription, HRV during sleep | What Is HRV, and How Can You Track It Without a Subscription? |
| Sleep | sleep tracker no subscription, how much deep sleep do you need, sleep tracker accuracy | Best Sleep Trackers Without a Subscription: What You Actually Own |
| Recovery | recovery tracker no subscription, recovery score meaning, best recovery wearable | Recovery Tracking Without a Screen or Monthly Membership |
| Screenless | screenless health wearable, screenless fitness tracker, screenless sleep tracker | Screenless Health Wearables: Benefits, Tradeoffs, and Alternatives |

The HRV page already exists (`/learn/heart-rate-variability-explained/`) and
is the only page Google shows for any query today. Rewrite it first.

The sleep guide is a commercial guide that compares recurring-fee models with
buy-once hardware and explains in plain language what stays available without
payment. It must state that wrist sleep staging is an estimate (evidence
library in `brand-brief.md`).

Strain content explains the concept in neutral language. Never imply Vybe has
a WHOOP-equivalent strain metric.

## Do not chase yet

Head terms: "HRV", "sleep tracker", "smart ring", "recovery", "fitness
tracker", "WHOOP strain", "recovery score". Brand authority decides those.
Win the long-tail and comparison queries first, earn links, then widen.

## Headline bank (search-aligned)

- WHOOP Alternative Without a Subscription: Vybe's Screenless Health Band (main conversion page, primary candidate)
- WHOOP vs. Vybe: Recovery Tracking Without Membership Fees
- Oura Ring vs. Vybe: A No-Subscription Health Wearable
- Track Sleep, HRV, and Recovery Without a Monthly Fee
- A Fitness Tracker You Own, No Subscription Required
- Best HRV Trackers Without a Monthly Fee
- Best Sleep Trackers Without a Subscription in 2026

"Best X" titles need a fair list that includes other no-subscription devices
(Polar, Garmin, Amazfit and others). A list that only praises Vybe reads as an
ad and fails the honesty rule.

## Measurement

Search Console weekly, by page and query, in the scoreboard. A page counts as
working when it holds a top-10 position on its primary cluster and sends
waitlist signups that GA4 attributes to Organic Search.
