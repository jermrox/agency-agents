# Brief an "oura ring alternative" page.

## Brief: Oura Ring Alternatives: How to Choose a Ring or a Band

Category: Content & SEO (2), with AI search (3) | Audience: end users who own or are pricing an Oura Ring and are looking at other options (the subscription-quitter search door in `plan-2026-q4.md`) | Channel: organic search, vybe.health | Number to move: qualified waitlist signups that GA4 attributes to Organic Search (baseline: none recorded)

**Decision: improve the existing page, do not write a new one.** Rewrite `/compare/oura-ring-alternative/` in place, at the same URL. Reasons, following step 3 of the skill:
- Search Console has no query rows for any Oura question (3 Jul to 30 Sep 2026, by query and page). The page's only impression in the window (position 7) has its query hidden. So nothing shows that the page earns impressions for a *different* question. That is the case in which the skill says to write a new page.
- No other vybe.health page has an impression for any Oura question. The existing URL, its title tag ("Oura Ring Alternative: Compare Memberships | Vybe") and its H1 ("Considering an Oura Ring alternative? Compare access.") all target this query already. A second page would split the query across two URLs, and the cannibalization rule gives the query to the page that already owns it.
- `seo-plan.md` Phase 1 already says "Oura alternative (expand the existing page)".
- Limit: with one hidden-query impression, the step-3 query test cannot really be passed or failed. The 8-week review re-pulls the query rows. If the page's impressions turn out to come from another question (for example the Oura membership itself), that question gets its own page, linked both ways with this one.

What the rewrite changes on the live page (Firecrawl, `onlyMainContent: false`, `waitFor` 3000 ms, read 3 Oct 2026 [V1]):
1. It never answers the searcher's question. The page is a two-column "Vybe Band / Vybe Ring" vs "Oura Ring" table. Searchers want to know what the alternatives are, and the AI Overview names other rings. Comparing a shipping product with a pre-launch one cannot be fair (the WHOOP vs Oura brief retired the "vs Vybe" headlines until launch for the same reason).
2. It names a Vybe ring ("Vybe plans a ring and a band"). The founder has not approved the ring (`concept.md` tensions: "The band"). It also uses "Vybe Band" as a name, which is on the brand brief's avoid list.
3. Its "Core sensing" row uses cardiac wording that Claim Register rows 5 and 5a bar from copy. The rewrite says "HRV and heart rate" only.
4. Its "Worn" row gives a battery target. Row 7 is unconfirmed, and battery is never compared with a named competitor.
5. It frames the membership as a downside. One H2 is "The part people discover after they buy", and the copy tells readers to "calculate the total cost over the period you expect to use it". That is the price framing the comparison rules forbid. In the rewrite, the membership is described once, factually, in Oura's own words.
6. It tells readers to "Check current terms for features without membership", but Oura's own page answers that question ([O1], quoted below). Fairness means quoting the answer.
7. Its Vybe section opens on hygiene ("Vybe plans a screenless ring and band with wellness interpretation included and no required consumer subscription"), fails the order rule, and shows no answer.
8. Its call to action is a hygiene hook ("Want an Oura alternative without a membership?"). It also says in the present tense that Vybe "does not charge people a monthly fee", which goes beyond Register row 2's wording ("no required consumer subscription").
9. It cites one source.

Keep from the live page: the honest pre-launch lines ("Vybe is pre-launch and has no independent device reviews or verified performance comparison yet"), the "Credit where it is due" idea, the line "Vybe provides wellness insights, not medical advice, diagnosis or treatment", and the internal links. Change one of those links: point "See the hardware" at `/band`, not `/hardware`, because `/hardware` presents the unapproved ring.

Data pulled for this brief (3 Oct 2026): DataForSEO, US, English, location 2840. Four calls:
1. Google Ads keywords-for-keywords live, 6 seeds, 21 rows with 12-month series.
2. Labs bulk keyword difficulty live, 13 terms. It failed with "40200 Payment Required" (cost $0) and was not retried, because DataForSEO Labs is not funded on this account.
3. SERP Google organic task post, desktop, depth 20.
4. SERP task get (advanced). It returned on the first try.

Search Console: `sc-domain:vybe.health`, 2026-07-03 to 2026-09-30 (ends 3 days before today), `data_state: final`, search type web, no filters. Pulled once with dimensions query and page and once with page alone, row limit 1,000 each. Firecrawl was used for vybe.health and the competitor pages. Exa's fetch was used for Samsung and Amazfit, after Firecrawl returned a Samsung 404 at the old URL, and for Tom's Guide, which Firecrawl does not support. Exa search found the ITC primary notices. Volumes are Google Ads buckets: 12-month averages unless a month is named. Google Trends was not pulled.

Question: "oura ring alternative" (what else is like an Oura Ring, which one should I get, do I have to pay a membership)      Pillar: Restore (sleep) and Vitals (HRV and heart rate) are what every ring in the comparison measures. Vitals leads the Vybe section, because Vitals leads search
Target query: oura ring alternative — 6,600/mo (12-month average bucket; latest month, Aug 2026, 6,600; 8,100 at the Nov 2025 to Jan 2026 peak and again in Jul 2026), KD 2, CPC $1.99, Google Ads competition HIGH (100) (DataForSEO, 3 Oct 2026). The KD comes from the skill's Current priorities table (DataForSEO, pulled 3 Oct 2026), because this session's own KD pull failed (see above). Volume, CPC and competition come from this session's pull.
Demand trend (Google Ads 12-month series, DataForSEO, pulled 3 Oct 2026): the first three months (Sep to Nov 2025) ran 5,400, 5,400 and 8,100. The last three (Jun to Aug 2026) ran 6,600, 8,100 and 6,600. Demand is steady to slightly up, with no launch spike. This is search demand, not sales. No growth percentage is quoted.
Merged variants: "oura ring competitors" and "oura ring competitor" return the same 2,900 and the same series, and so do "oura competitors" and "oura competitor" (390). Google Ads merges each pair, so each pair is one figure, never two.
Supporting queries (12-month average buckets, DataForSEO 3 Oct 2026; never add these together; KD not available this session):
- oura ring competitors — 2,900 (Aug 2026: 2,400; 4,400 at the Nov to Dec 2025 peak)
- smart ring without subscription — 1,900 (1,600 in Sep 2025, 2,400 in Aug 2026). Not Oura-branded, but it is the same need
- alternative to oura ring — 1,300 (Aug 2026: 1,000)
- best oura ring alternative — 720 (390 in Sep 2025, 720 in Aug 2026). It is answered only with a fair list and no winner
- oura alternative — 390; oura ring alternative reddit — 390; similar to oura ring — 320
- oura ring alternative no subscription — 260 (the plan's lead cluster; see "Plan check"); best alternative to oura ring — 260
- Not targeted: "oura ring cheaper alternative" (170 average, rising from 50 to 260 a month). It is a price question, and this page makes no price comparison

People Also Ask to answer (SERP, desktop, 3 Oct 2026): Why are people ditching their Oura rings? Why is Oura Ring being sued? Which smart ring is the best in 2026? Not answered: "What ring does Jennifer Aniston wear?". It is a celebrity question with nothing to source, and answering it would imply an endorsement.

Vybe today: Search Console (2026-07-03 to 2026-09-30, final): `/compare/oura-ring-alternative/` has 1 impression at position 7 and 0 clicks, with its query hidden. No query row names Oura. The page-only pull totals 28 impressions and 0 clicks for the whole site: 15 on the HRV explainer at about position 83, 4 on the homepage, and one or two each on eight other pages. The query and page pull shows only 10 rows, all HRV definition queries plus "vybe health". vybe.health is not in the top 20 results for the target query (SERP, 3 Oct 2026).

Who ranks (desktop SERP, 3 Oct 2026, 107,000 results):
- An AI Overview sits on top. It says the alternatives "are the RingConn Gen 2 Air and the Samsung Galaxy Ring, both offering robust health and sleep tracking without Oura's mandatory monthly subscription fee". It then gives a cost line and a battery line for each of four rings. It cites a Reddit thread (r/UninfluencedReviews), Wareable, Forbes, Tom's Guide, PCMag, circulsense.com and five YouTube videos.
- Top five organic: omnihealthring.com (a ring seller's blog), a Reddit thread in r/SmartRings ("Recommendations to replace Oura gen 2", position 2), Quora, vertu.com and an Instagram reel. A "perspectives" block (Forbes, PCMag UK, Wired, two Reddit threads, Facebook posts) sits between them.
- Tom's Guide's list (James Frew, "Last updated 22 September 2026"), cited in the AI Overview, is the only reviewed source that opens on Oura's patent case [T1].

What they miss:
- The AI Overview and most results lead on price and battery. Vybe must not compete on either.
- Seller blogs and social posts fill the organic results.
- Except for Tom's Guide, nothing explains the patent case that decides which rings US buyers can get.
- None says what each app does with the readings, how sure it is, or what the membership changes, in the maker's own words.
- A Reddit thread at position 2 means the existing answers are not doing the job. That is the opening.

Intent check (4d): commercial comparison with wellness intent. No disease, weight-loss or medication intent on the page, so the head term stands.

Page type: fair comparison, with a device table. Each product gets its strength in its maker's words. No price or battery comparison, no "best" badge, no winner, and no per-brand price or membership column.

Title (54 characters): Oura Ring Alternatives: How to Choose a Ring or a Band
Meta (≤160 characters): Other smart rings and screen-free bands that track sleep, heart rate and HRV, what each app leads with, what Oura's membership covers, and where Vybe fits.
H1: Oura Ring alternatives: other rings and bands, and how to choose
URL: `/compare/oura-ring-alternative/` (unchanged; 301 nothing)

## Answer first (40 to 60 words)

An Oura Ring alternative is another wearable that tracks sleep and heart
rate: a smart ring such as RingConn Gen 2 Air or Samsung Galaxy Ring, or a
screen-free band such as Polar Loop. They differ in what the app explains,
what needs a membership, and how data is handled. A 2025 patent ruling
limits which rings reach the US.

(60 words by `wc -w`. No Vybe mention and no winner. The first sentence is a definition, sourced to each maker's page [R1, G1, P1]. The second is sourced to [O1, R1, P1]. The third is sourced to [I1, I2]. This paragraph is the AI Overview candidate.)

## Outline

1. **What are the alternatives to an Oura Ring?** Three kinds, each given
   its real strength:
   - other smart rings (same form, a different app);
   - screen-free bands (wrist or arm, no display);
   - watches (a screen and smartwatch features).

   Then the device table below. Grant Oura first, in its own words: "The
   world's smallest smart ring puts 50+ health metrics at your fingertips";
   titanium, waterproof to 100 m; and it "Integrates with 100+ apps" [O2].
   Its Readiness Score "uses your temperature trends, heart rate, sleep, and
   more to highlight how energized you are for the day" [O2].
2. **Does an Oura Ring work without a membership?** (answers "oura ring
   alternative no subscription" and "smart ring without subscription").
   Quote Oura word for word: "If you choose not to begin or continue your
   Oura Membership, your Oura Ring and Oura App will still function, but the
   insights, personal health data, and benefits you receive will be much
   more limited" [O1]. Then grant what Oura grants: "Even without a
   membership, you can export all of your Oura data in CSV format through
   the Membership Hub", and members "gain access to Oura Advisor (Oura's
   AI-powered health companion)" [O1]. Then say that some other makers
   include their app features with the device, and quote them: RingConn's
   comparison table lists "Subscription Fee: Free" [R1]; Polar says "Full
   access to every feature from day one" [P1]; Amazfit says "No required
   subscription" [A1]. No figures anywhere, no cheaper-or-dearer wording,
   and no Vybe line in this section.
3. **Which smart ring is the best in 2026?** Neither this page nor anyone
   can name one for every reader. Say what decides it:
   - *Your phone.* Samsung says "To start using Galaxy Ring, a Samsung
     account must be registered on your Samsung Galaxy smartphone" [G1].
     The Oura app is "Available on iOS and Android" [O2].
   - *Ring or band.*
   - *What the app explains.*
   - *What the membership covers.*

   No winner and no ranking.
4. **What happened with Oura's patent case?** (answers "oura ring
   competitors" readers who find a ring unavailable). One neutral, dated
   paragraph, from the US International Trade Commission's own notices:
   - On 21 Aug 2025, in investigation 337-TA-1398, the Commission found that
     Ultrahuman and RingConn smart rings infringed one Oura patent. It issued
     a limited exclusion order and cease and desist orders against both
     [I1].
   - Circular had settled with Oura in July 2024 [I3].
   - On 8 Dec 2025, after "a Patent License & Settlement Agreement", the
     Commission removed RingConn from the exclusion order and rescinded its
     cease and desist orders [I2].
   - Ultrahuman appealed to the Federal Circuit (No. 2026-1083). The
     Commission denied its motion to stay the orders on 15 Dec 2025 [I3].

   Before publishing, the writer rechecks the Commission's docket and the
   Federal Circuit appeal, then states the current status or "unresolved
   as of [date]". Two more investigations are open, and the page shows
   both directions (corrected 3 Oct 2026 after grading):
   - 337-TA-1468, instituted 17 Dec 2025: Oura is the complainant. The
     respondents include Samsung, Reebok, Zepp Health (Amazfit's maker)
     and Nexxbase (Noise and LunaZone, the Luna ring) [I4]. Oura's own blog
     says Nexxbase submitted a consent order to stay out of the US market;
     cite that as Oura's statement [I6].
   - 337-TA-1478, instituted 13 Jan 2026: Samsung is the complainant and
     Oura the respondent [I5].
   The Commission has made no decision on the merits of either case; the
   writer rechecks both dockets before publishing. Tom's Guide's account [T1] is
   background for the writer, not a source for the page. No adjectives, no
   opinion.
5. **Why are people ditching their Oura rings?** Say plainly that we have
   no data on why people stop wearing any ring. Then give what to check
   before switching: whether the replacement works with your phone, what
   it includes without a membership (H2 2), and whether it can take your
   history. Oura's own export line in H2 2 answers that last point for
   Oura. No forum quotes and no speculation.
6. **Why is Oura Ring being sued?** One neutral, dated line from the
   Commission's notice: Samsung filed a complaint on 15 Dec 2025, and the
   Commission instituted investigation 337-TA-1478 against Oura on 13 Jan
   2026, with no decision on the merits yet [I5]. Never answer from news or
   forum posts.
7. **Ring or band: what changes?**
   - A ring is small and easy to sleep in.
   - A band can go on the wrist or the upper arm. Amazfit says the Helio
     Strap is for "Wrist or upper-arm wear for training" [A1].
   - Neither has a screen, so everything goes through the phone.

   Sleep stages from any consumer wearable are estimates. A 2025
   meta-analysis of 24 studies found that wrist trackers differ
   significantly from lab polysomnography on total sleep time, efficiency,
   latency and wake after sleep onset (Lee et al. 2025). Rings were not in
   that analysis, so the page draws nothing from it about rings. For its
   ring, Oura cites its own multi-night study against polysomnography,
   by Altini (Vrije Universiteit Amsterdam) and Kinnunen (Oura Health),
   *Sensors* 2021 [O2]. The
   page quotes no accuracy percentage for any device and names no accuracy
   winner.
8. **How do these devices compare you, and what does a change mean?**
   - Oura says its readings are personal: "personal health data, day and
     night" [O2]. RingConn says it "helps you notice shifts that matter"
     across "heart rate, heart rate variability, and blood oxygen" [R1].
   - The point for any device: HRV and resting heart rate move with
     training, alcohol, menstrual-cycle phase and sickness. That comes from
     an observational analysis of about 9 million measurements from 28,175
     people, so these are associations, not causes (Altini and Plews 2021).
   - A drop in a score has more than one explanation that fits. No single
     reading says which one it was.
   - Disclosure in the copy: Marco Altini, first author of that analysis,
     also co-wrote the Oura study that Oura cites in H2 7, and its data
     came from his own app, HRV4Training.
9. **Where Vybe fits (pre-launch)** (the one Vybe section, below).
10. **FAQ** (repeats the three PAA questions as short Q and A pairs).

**Device table for H2 1.** Every cell was checked on 3 Oct 2026 against the maker's own page. Source codes refer to "Proof and sources".

| Device | Form | What it leads with, in its maker's words | Source, checked 3 Oct 2026 |
|---|---|---|---|
| Oura Ring 5 | Titanium smart ring | "The world's smallest smart ring puts 50+ health metrics at your fingertips." | [O2] |
| RingConn Gen 2 Air | Smart ring | "Smarter Health Guidance": "AI-powered insights for proactive wellness" | [R1] |
| Samsung Galaxy Ring | Titanium smart ring | "AI-powered health tracker on your finger" | [G1] |
| Polar Loop | Screen-free band | "No screens. No interruptions. No monthly fees." | [P1] |
| Amazfit Helio Strap | Screenless strap, wrist or upper arm | "No screen. No noise. Just your body's data." | [A1] |
| Vybe band (pre-launch) | Pre-launch. Screenless band | Pre-launch. Designed to answer in a plain sentence that says how sure it is, and why | Pre-launch. Claim Register rows 1 and 14, `brand-brief.md` v1 |

Table rules:
- No price, membership, battery, accuracy, data-export or light-sensing column. No "best" badge, ticks, crosses or winner row.
- Vybe's row says "pre-launch" in every cell and shows nothing unconfirmed.
- Ultrahuman, Circular, Luna and the Amazfit Helio Ring get no row. Ultrahuman is under the 2025 exclusion order, whose current status needs a recheck. None of the four has an own-page line on file from this session. They appear only as names in H2 4, and only where a primary source names them.
- Every cell is rechecked on publish day, and the caption date is updated.

Internal links: to `/compare/whoop-vs-oura/` and `/screenless-fitness-tracker/` (once published), `/compare/whoop-alternative`, `/learn/heart-rate-variability-explained/`, `/learn/hrv-tracker`, `/learn/health-data-privacy-ownership`, `/band` and the waitlist. Link back to this page from the WHOOP vs Oura page and the screenless category page.

## The Vybe angle (one section)

Heading: "Where Vybe fits (pre-launch)".

Before publishing: the founder signs off Claim Register rows 14, 15, 16 and
19 for public copy. Until then this section stays in draft.

Copy:

"A score is one number. Vybe's answers are designed to say how sure they
are, and why."

Each answer is designed to come as a plain sentence, with its confidence in
words and a reason you can count (row 14). Each answer is designed to name
what Vybe could not see (row 15), and to give the everyday explanations that
fit instead of one culprit (row 19). Vybe is also designed to check later
whether its own suggestion worked, and to show the ones it got wrong
(row 16).

Show one answer, labelled **"Prototype, sample data"**:

> Your HRV has been below your own range for two mornings. The two short nights fit most closely; Monday's long run fits too. Moderate confidence: 23 days of data, and one travel day logged. What Vybe could not see: anything you drank, how you feel today. Next: an easy day.

Then, pointing back to it: the band is designed to produce that answer. It
is a screenless band, and it is pre-launch (row 1). It reads five connected
signals against your own baseline, not a population average (rows 3 and 9).
There is no required consumer subscription (row 2). Health data is never
sold; it is shared only with your consent, with service providers that run
the service, or where the law requires (row 4). And it is built open, so
others can build on the band: if you build health products, talk to us
(row 18).

Rules for this section:
- It names no other product and compares Vybe with none on any feature, price, battery or accuracy.
- No tally from the prototype (row 16).
- No battery line (row 7 unconfirmed).
- No export or one-tap claim (row 17 unconfirmed; tension in `concept.md`).
- No light-sensing line.
- No "validated" (row 8).
- No ring.
- No clinical wording (rows 5 and 5a): Vybe copy says "HRV and heart rate" only.
- No "the answers come with the band" (row 21 is on hold).

## Proof and sources

Product facts, each read on 3 Oct 2026:
- [V1] Vybe, "Oura Ring Alternative: Compare Memberships | Vybe", https://vybe.health/compare/oura-ring-alternative/ (Firecrawl, `onlyMainContent: false`, `waitFor` 3000 ms). "Published September 17, 2026 · Updated September 24, 2026". It is the source for every quote in "What the rewrite changes".
- [O1] Oura Membership, https://ouraring.com/membership (Firecrawl). Quotes used: "your Oura Ring and Oura App will still function, but the insights, personal health data, and benefits you receive will be much more limited"; "Even without a membership, you can export all of your Oura data in CSV format through the Membership Hub"; "Oura Advisor (Oura's AI-powered health companion)"; "we don't sell your data, and we'll never share it without consent".
- [O2] Oura Ring 5 store page, https://ouraring.com/store/rings/oura-ring-5 (Firecrawl). Quotes used: "The world's smallest smart ring puts 50+ health metrics at your fingertips"; titanium; waterproof to 100m; "Integrates with 100+ apps"; "Available on iOS and Android"; the Readiness Score line; "personal health data, day and night". Its sleep-staging footnote cites Altini M, Kinnunen H, *Sensors* 2021;21(13):4302, [doi:10.3390/s21134302](https://doi.org/10.3390/s21134302). The page's accuracy percentages are not repeated.
- [R1] RingConn Gen 2 Air, https://ringconn.com/products/ringconn-gen-2-air (Firecrawl). Quotes used: "Smarter Health Guidance"; "AI-powered insights for proactive wellness"; its comparison table row "Subscription Fee: Free"; and the Vitals line "heart rate, heart rate variability, and blood oxygen ... helps you notice shifts that matter".
- [G1] Samsung Galaxy Ring, https://www.samsung.com/us/rings/galaxy-ring/ (Exa fetch; Firecrawl had returned a 404 at the old /us/watches/ URL). Quotes used: "AI-powered health tracker on your finger"; "To start using Galaxy Ring, a Samsung account must be registered on your Samsung Galaxy smartphone".
- [P1] Polar Loop, https://www.polar.com/us-en/loop (Firecrawl). Quotes used: "No screens. No interruptions. No monthly fees."; "Full access to every feature from day one".
- [A1] Amazfit Helio Strap, https://us.amazfit.com/products/helio-strap (Exa fetch). Quotes used: "No screen. No noise. Just your body's data."; "No required subscription"; "Wrist or upper-arm wear for training".
- [I1] US ITC, Inv. 337-TA-1398, final determination, 90 FR 41594-95 (26 Aug 2025), https://www.federalregister.gov/documents/2025/08/26/2025-16316/certain-smart-wearable-devices-systems-and-components-thereof-notice-of-the-commissions-final (vote 21 Aug 2025).
- [I2] US ITC, modification and rescission as to RingConn, 90 FR (12 Dec 2025), https://www.govinfo.gov/content/pkg/FR-2025-12-12/html/2025-22586.htm (vote 8 Dec 2025).
- [I3] US ITC, notice denying Ultrahuman's motion to stay, 15 Dec 2025, https://www.usitc.gov/sites/default/files/secretary/fed_reg_notices/337/337_1398_notice12152025sgl.pdf. It also records the Circular settlement (Order No. 12, 9 Jul 2024) and Federal Circuit appeal No. 2026-1083.
- [I4] US ITC, Inv. 337-TA-1468, institution notice, 90 FR (22 Dec 2025), https://www.govinfo.gov/content/pkg/FR-2025-12-22/html/2025-23584.htm, and news release 18 Dec 2025, https://www.usitc.gov/press_room/news_release/2025/er1218_67858.htm (checked 3 Oct 2026)
- [I5] US ITC, Inv. 337-TA-1478, institution notice, 91 FR 2153 (16 Jan 2026), https://www.federalregister.gov/documents/2026/01/16/2026-00852/certain-wearable-devices-institution-of-investigation (checked 3 Oct 2026)
- [I6] Oura, "Oura Files ITC Action Against Samsung, Reebok…", updated 8 Jan 2026, https://ouraring.com/blog/itc-action-patent-infringement/ (party statement; checked 3 Oct 2026)
- [T1] Tom's Guide, "Best Oura Ring alternatives we've tested for all-day tracking", James Frew, last updated 22 Sep 2026, https://www.tomsguide.com/wellness/fitness-trackers/best-oura-ring-alternatives (Exa fetch; Firecrawl does not support the site). Used only in "Who ranks". No fact on the page rests on it.

Health statements:
- Wrist sleep staging is an estimate: Lee et al., *J Clin Sleep Med* 2025, a meta-analysis of 24 studies of consumer wrist trackers against polysomnography, [doi:10.5664/jcsm.11460](https://doi.org/10.5664/jcsm.11460). It covers wrist trackers, not rings. The page says "wrist trackers" wherever it cites it and quotes none of its numbers.
- HRV is sensitive but not specific: Altini and Plews, *Sensors* 2021, an observational analysis of about 9 million measurements from 28,175 people, [doi:10.3390/s21237932](https://doi.org/10.3390/s21237932). Association wording only. The competitor tie (the first author also co-wrote the Oura study in [O2]) is disclosed in the copy, in H2 8.

Search data: the DataForSEO pulls and Search Console range listed at the top (3 Oct 2026).

## Call to action

One: join the waitlist, with /waitlist's own line underneath: "signing up is
not a device order". Do not use the "first 1,000" offer. Register row 11
holds it until the homepage and /waitlist agree.

## Schema and AI search

- Article schema, with each PAA question as an H2, plus BreadcrumbList.
- FAQPage markup on the FAQ block is optional: since 2023 Google shows FAQ rich results only for well-known government and health sites, so it earns no rich result here, though it does no harm.
- No Product, Offer or Review schema for any device: this page reviews nothing and sells nothing.
- The answer-first paragraph is the AI Overview candidate. Keep it in plain HTML near the top.
- Make the device table a real HTML table, so AI answers can quote a row.
- Keep the patent paragraph dated in visible text, because AI answers lift dates.
- Stay under the 8K-token landing budget. Allow GPTBot, ClaudeBot, PerplexityBot and Google-Extended in `robots.txt`, and add the page to `llms.txt` once that ships.

## Plan check

`seo-plan.md` (v1, 1 Oct 2026, updated 3 Oct) lists this page in Phase 1 as
"Oura alternative (expand the existing page)". Its query cluster is "oura
alternative no subscription, oura ring alternative no membership, health
band vs smart ring", and its title is "Oura Ring Alternative With No Monthly
Membership". The data disagrees on three points:
- **The cluster is pointed at the small terms.** "oura ring alternative no subscription" gets 260 a month, while the head term "oura ring alternative" gets 6,600 at KD 2. "oura ring competitors" (2,900) and "alternative to oura ring" (1,300) are also larger than the plan's lead term.
- **The title leads with hygiene and sets up a membership comparison.** The comparison rules limit that comparison to Oura's own wording, with no figures, and the searcher typed the head term, not "no membership".
- **The plan predates the patent ruling's effect on the results page.** The ruling decides which rings a fair alternatives page can list, and only Tom's Guide on page one explains it.

Proposed dated note for `seo-plan.md`: "3 Oct 2026: the Oura page (`/compare/oura-ring-alternative/`) is rewritten in place to target 'oura ring alternative' (6,600/mo, KD 2, DataForSEO) as a fair alternatives page with a sourced device table, not a Vybe-vs-Oura table. 'No subscription' moves from the title to proof. The title becomes 'Oura Ring Alternatives: How to Choose a Ring or a Band'. The ITC exclusion order (337-TA-1398) is rechecked monthly." This run is read-only, so the note stays here for the agent to apply.

Also for the founder:
- `/hardware` presents an unapproved Vybe ring.
- The site-wide footer line "No subscription required to understand your own body" goes beyond Register row 2's wording.

## Measure

- **Current position:** no query-level impressions for "oura ring alternative" or any supporting query. Page level: 1 impression at position 7, 0 clicks, query hidden (Search Console, 2026-07-03 to 2026-09-30, final, dimensions query+page and page). Not in the top 20 for the head term (SERP, 3 Oct 2026).
- **Target at 8 weeks:** top 20 for "oura ring alternative". Top 10 for at least two of "alternative to oura ring", "similar to oura ring" and "oura ring alternative no subscription" (KD for these to be pulled once Labs is funded). The first Organic Search waitlist signups attributed in GA4.
- **Review date:** 8 weeks after the rewrite is published.
- **Decision rules:**
  - Re-pull Search Console by query and page, with the same settings. If this page's impressions come mainly from a different question, write that question its own page and link the two (step 3).
  - If impressions rise but the click rate stays under 1%, rewrite the title and meta.
  - If the head term is still past position 50 at 8 weeks, re-point the H1 at "alternative to oura ring" and "smart ring without subscription".
  - If this page and `/compare/whoop-vs-oura/` both show for the same query, the page with the clicks keeps it and the other drops the overlapping section.
  - If the ITC status changes, or a listed device changes its own page, update the table and H2 4 within a week.
- **Paid tie-in:** none for now. CPC $1.99 is inside the plan's "under $2.50" rule, but bidding on a competitor's name risks implying affiliation, and Google Ads competition is HIGH (100). Organic only, unless the founder approves a separate competitor campaign with its own copy review.

## Claims used, with ladder level

- Rows 1, 2, 3, 9: product facts, approved, in Register wording.
- Row 4: privacy promise, in the Register's own wording.
- Rows 14, 15, 16, 19: design commitments, "designed to", founder sign-off gated.
- Row 18: platform direction ("built open", "talk to us").
- Health statements: associated (Altini and Plews), and observed at the population level for wrist trackers only (Lee et al.).
- Competitor statements: quoted from their own pages, dated.

## Concept check

1. **Audience and channel.** End users, search page. Lead column (the direct answer): "An Oura Ring alternative is another wearable that tracks sleep and heart rate". Second column (calibrated answers, then the waitlist): "A score is one number. Vybe's answers are designed to say how sure they are, and why.", then "One: join the waitlist". The proof points back to the shown answer: "the band is designed to produce that answer".
2. **Swap test.** The hook "oura ring alternative" fails on purpose, because the searcher typed it (search row of the channel table). The Vybe section's opening fits no competitor: "Vybe's answers are designed to say how sure they are, and why", and "Vybe is also designed to check later whether its own suggestion worked, and to show the ones it got wrong".
3. **Show it.** One real-shaped answer, labelled "Prototype, sample data". Sentence: "Your HRV has been below your own range for two mornings". Confidence with a countable reason: "Moderate confidence: 23 days of data, and one travel day logged". Blind spot: "What Vybe could not see: anything you drank, how you feel today". One step: "Next: an easy day."
4. **Order.** The Vybe section opens on "designed to say how sure they are, and why" and "designed to come as a plain sentence, with its confidence in words and a reason you can count". Hygiene follows: "It is a screenless band", "against your own baseline", "There is no required consumer subscription".
5. **Two products.** The page sells the band ("join the waitlist") and names the platform once: "it is built open, so others can build on the band: if you build health products, talk to us".
6. **Claims.** Rows 14, 15, 16 and 19 each sit in a sentence whose main verb "designed to" governs: "Each answer is designed to come as a plain sentence" (row 14), "Each answer is designed to name what Vybe could not see" (row 15), "and to give the everyday explanations that fit" (row 19), "Vybe is also designed to check later whether its own suggestion worked" (row 16). Sign-off is gated: "the founder signs off Claim Register rows 14, 15, 16 and 19". Privacy uses row 4's wording: "Health data is never sold; it is shared only with your consent, with service providers that run the service, or where the law requires". The sample gives two explanations: "The two short nights fit most closely; Monday's long run fits too."
7. **Roadmap and offers.** Nothing relies on an unconfirmed spec: "No battery line (row 7 unconfirmed)", "No export or one-tap claim", "No light-sensing line", "No ring". No offer is used: "Do not use the 'first 1,000' offer". The heading says "Where Vybe fits (pre-launch)", and the table row says "Pre-launch" in every cell. The builder line invites a conversation and promises nothing: "talk to us".
8. **Voice.** Plain and declarative, with one action ("One: join the waitlist") and no winner ("No winner and no ranking"). It says "we don't know" where it should: "Say plainly that we have no data on why people stop wearing any ring", "This session found no primary court filing against Oura", and "unresolved as of [date]".
