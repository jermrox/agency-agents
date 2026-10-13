# Brief: How Accurate Are Sleep Trackers? What the Lab Studies Show

Category: Content & SEO (2), with AI search (3) | Audience: end users who own or are choosing a wrist or ring tracker and doubt the stage chart (closest segment: baseline nerds and subscription-quitters, `plan-2026-q4.md`) | Channel: organic search, vybe.health | Number to move: impressions and clicks for the "sleep tracker accuracy" question family in Search Console, and Organic Search `waitlist_signup` in GA4 (baseline: none recorded)

**BLUF.** Of the six candidate topics, "how accurate are sleep trackers" is the one to write next: it is the only candidate with a rich, multi-brand question family, no Vybe page, a slot in the plan, and a results page where nobody puts the primary studies first. Its monthly volume and keyword difficulty could not be pulled today because DataForSEO is unfunded (balance −$0.05 at 13 Oct 2026), so every demand figure below is either a dated 3 Oct 2026 pull, a labelled public source, or marked "not available". **Not ready to publish until DataForSEO is funded and the volume, difficulty and Google results page for the target query are pulled.** Decision needed from the founder: fund DataForSEO (and Firecrawl, at −1,000 credits) so the next brief can carry real figures.

Decision: write a new explainer at `/learn/how-accurate-are-sleep-trackers/`. Do not fold it into the HRV explainer or the screenless explainer, neither of which mentions sleep stages (both read 13 Oct 2026, below). Do not refresh `briefs/what-is-a-good-hrv.md`: nothing in today's Search Console pull changes it (still no "good hrv" impressions).

## Why this topic, and not the other five

Sizing table. Every figure names its source and date. "Not available" means no funded tool returned a figure and no public source published one; nothing here is estimated.

| Candidate | Monthly volume (US) | KD | Vybe page today (Search Console, 12 Jul to 10 Oct 2026) | Already briefed? | Verdict |
|---|---|---|---|---|---|
| what is a good hrv | 14,800 bucket (DataForSEO, 3 Oct 2026; not re-pulled: DataForSEO unfunded, 13 Oct 2026) | 17 (same pull) | None for any "good hrv" query; the HRV explainer's 64 impressions are all definition queries at position 84 | Yes, `what-is-a-good-hrv.md` | Keep the brief as is. No new data says refresh. |
| screenless fitness tracker | 40,500 average; 60,500 Aug 2026; 110,000 May to Jul peak (DataForSEO, 3 Oct 2026; not re-pulled) | 41 (same pull) | None for any screenless query; `/learn/screenless-health-wearable/` has 6 impressions at position 15, queries hidden | Yes, `screenless-fitness-tracker.md` | Keep the brief as is. Autocomplete on 13 Oct 2026 still returns 10 variants, so demand has not vanished. |
| wearable without subscription | "best fitness tracker without subscription" 1,000 average (1,600 May to Aug 2026), "fitness tracker without subscription" 260, "smart ring without subscription" 1,900, "health band no subscription" 10 (DataForSEO, 3 Oct 2026; not re-pulled). "wearable without subscription" itself: not available | 29, 15, not pulled, not pulled | `/learn/wearable-subscriptions/` ("Can you get a health tracker without a required subscription?", published 19 Sep 2026) exists and has **no impressions** in the 90-day window | The "without subscription" terms are supporting queries in `screenless-fitness-tracker.md` | A new page would split the query three ways. The existing page needs a rewrite in place later, not a second page now. |
| how accurate are sleep stages on a wearable | **Not available** from a funded tool. Public evidence of demand: Google autocomplete on 13 Oct 2026 returns ten suggestions for each of four seeds ("how accurate are sleep trackers", "are sleep trackers accurate", "sleep tracker accuracy", "sleep stages accuracy"), three of them with a "reddit" suffix, plus brand families for Apple Watch, Fitbit, Garmin, Oura and WHOOP (ten each). Context, public third-party estimates, not DataForSEO: "sleep tracker" about 40,500 (seodata.dev, undated) or 60,500 (rankhero.com, updated 12 Feb 2026); "best sleep tracker" about 6,600 (seodata.dev) | Not available | **No page** on the site mentions sleep tracker accuracy or sleep stages (`/learn/` hub, HRV explainer, screenless explainer, subscription guide, read 13 Oct 2026). No Search Console query contains "sleep", "accura" or "stage" | No. `seo-plan.md` Phase 2 lists "sleep tracker accuracy" as a starting query | **Write it.** Reasons below. |
| own your health data wearable | Not available. Autocomplete on 13 Oct 2026 returns only two suggestions for "own your health data" ("own your health data", "what is personal health data") | Not available | `/learn/health-data-privacy-ownership/` ("How private is your wearable health data?", published 19 Sep 2026) exists and has no impressions in the window | No | Thin demand and a page already there. Not a page; fix the existing one later. |
| HRV dropped after late night | "why is my hrv low" 590, "is low hrv bad" 320 (DataForSEO, 3 Oct 2026; not re-pulled). The literal phrase: not available. Autocomplete on 13 Oct 2026: "why did my hrv drop so much / last night / suddenly / overnight", "hrv dropped by 20 / to 15 / overnight" | 17 for "why is my hrv low" (same pull) | None | "why is my hrv low" is H2 5 of `what-is-a-good-hrv.md`; late dinners and overnight HRV are the Nourish brief `eating-before-bed-sleep.md` | A third page would cannibalise two briefs. Add the "dropped last night / by 20 points" wording to the good-HRV page's H2 5 instead. |

Why the sleep-accuracy question wins on fit, even without a volume figure:

1. **It is the one question in the set that is literally about how sure a reading is.** Vybe's unclaimed idea is an answer that states its confidence and what it could not see. A page that explains why a stage chart is an estimate, with the studies and their sizes, earns the right to say that.
2. **The results page has no primary-source-first answer.** Two labelled proxies for the Google results page (below) put mattress retailers, sleep-app blogs and a 2021 news piece on top. The "reddit" suffix on three autocomplete seeds says people are asking each other because the pages don't satisfy.
3. **Nothing to cannibalise.** No Vybe page or brief touches it. The other two unbriefed candidates each already have a page with zero impressions.
4. **It is in the plan.** `seo-plan.md` Phase 2 Sleep pillar lists "sleep tracker accuracy".

Demand-to-difficulty, stated honestly: demand is evidenced but unquantified, and difficulty is unmeasured. The proxies show low-authority 2026 app blogs (welltory.com, kygo.app, zomni.app) in the top ten, which is consistent with a beatable page, but that is an observation, not a KD. The 8-week review re-pulls both before any budget follows.

## Data pulled for this brief (13 Oct 2026)

- **DataForSEO (Composio, account `dataforseo_scamp-arum`, login jeremy@vybe.health):** three calls, all returned `40200 Payment Required` at cost $0: Google Ads keywords-for-keywords live (20 seeds), Labs bulk keyword difficulty live (14 terms), SERP Google organic task post (3 keywords, desktop, depth 20, AI Overview and People Also Ask requested). Account balance −$0.05. **Flag to the founder: DataForSEO is unfunded.** Composio's catalogue has no Google Ads Keyword Planner tool on the Vybe Google Ads account, so there was no second funded source for volume.
- **Google Search Console (Composio, account `google_search_console_foliot-byee`, property `sc-domain:vybe.health`, permission siteOwner):** two pulls, `data_state: final`, search type web, no filters, 2026-07-12 to 2026-10-10 (ends three days before today). Dimensions query+page (40 rows, row limit 1,000) and page alone (21 rows). Site total in the window: 323 impressions, 11 clicks.
- **Firecrawl (Composio):** every scrape and search returned `402 Insufficient credits`; `FIRECRAWL_CREDIT_USAGE_GET` shows remainingCredits −1000 of 1,000. **Flag to the founder: Firecrawl is over its plan.** vybe.health and competitor pages were read with the session's page fetch (public pages, allowed by Standards rule 1); the site rendered enough text to quote.
- **Google autocomplete (public, suggestqueries.google.com, hl=en, gl=us, 13 Oct 2026):** 21 seeds, ten suggestions each. It shows which questions people type, not how many.
- **Results-page proxies (13 Oct 2026):** the session's WebSearch tool (engine unlabelled) and DuckDuckGo's HTML results (Bing-backed). Neither is Google, neither shows an AI Overview or People Also Ask. Both are labelled as proxies wherever they appear below.
- **Studies:** abstracts and disclosure statements read through Europe PMC's public REST API (13 Oct 2026); PubMed itself refused the fetch (cookie wall).
- **Public volume sites:** rankhero.com and seodata.dev have no page for "how accurate are sleep trackers", "are sleep trackers accurate" or "sleep tracker accuracy" (all 404, 13 Oct 2026). Their head-term figures are quoted above as context only.

Question: "how accurate are sleep trackers?" (and: are the deep and REM numbers real, which brand is most accurate, should I trust it)      Pillar: Restore. The concept says Restore is proof, not hook, and Vitals leads search; this page is still Restore because the question is about sleep staging, and it keeps Vitals in view: the trackers in every study estimate stages from movement and heart rate, so the HRV explainer links in both directions.
Target query: how accurate are sleep trackers — volume **not available** (DataForSEO unfunded, 13 Oct 2026), KD **not available**, CPC **not available**. Google autocomplete (13 Oct 2026) lists it first for its own seed and also surfaces it under "how do sleep trackers know", so it is the family's head question.
Supporting queries (Google autocomplete, 13 Oct 2026; no volumes; never add families together):
- are sleep trackers accurate; are sleep trackers reliable; is sleep tracking accurate; how reliable are sleep trackers
- sleep tracker accuracy; sleep tracker accuracy comparison; sleep tracking accuracy
- garmin / fitbit / whoop / apple / oura / ringconn sleep stage(s) accuracy; "what percentage of sleep stages is normal"
- how accurate are sleep trackers on smart watches / on watches / garmin; how accurate are sleep tracking rings / apps / devices
- how accurate is apple watch sleep stages; how accurate is fitbit sleep stages; how accurate is garmin sleep stages; how accurate is whoop sleep stages; how accurate is oura ring sleep
- how do sleep trackers know when you fall asleep; how does a sleep tracker know you're in rem; do sleep trackers work
Left to other pages or left alone: "can a sleep tracker detect sleep apnea" and "how accurate is apple watch sleep apnea" (medical intent; this page never serves it and says so in one line); "how accurate is oura ring steps / calorie burn / ovulation" (not sleep); "sleep tracker" and "best sleep tracker" (head terms; `seo-plan.md` says do not chase yet).

People Also Ask to answer: **not pulled** (the SERP task returned Payment Required). Stand-in, labelled: the question-shaped autocomplete suggestions above. The six the outline answers: Are sleep trackers accurate? How accurate are sleep stages (deep, REM)? Which sleep tracker is most accurate? How do sleep trackers know when you fall asleep? Do sleep trackers work? What percentage of sleep stages is normal? When the Google pull is done, replace this list with the real People Also Ask and keep any question here that it confirms.

Vybe today (Search Console, `sc-domain:vybe.health`, 12 Jul to 10 Oct 2026, final data):
- No query in the 40 query rows contains "sleep", "accura", "stage", "subscription", "data" or "own". So no page earns impressions for this question or for the other two unbriefed candidates.
- The pages that could be confused with it: `/learn/heart-rate-variability-explained/` 64 impressions, 0 clicks, average position 84.4, all HRV definition queries; `/learn/whoop-recovery-score-meaning/` 30 impressions, 0 clicks, position 17.8, WHOOP recovery queries; `/learn/screenless-health-wearable/` 6 impressions, position 15.3, queries hidden.
- `/learn/wearable-subscriptions/` and `/learn/health-data-privacy-ownership/` do not appear in the page rows at all: zero impressions in 90 days. Flag for the plan.
- So this is a new page. Cannibalisation check: no page has a click on any sleep query, so no page owns it.

Who ranks (two labelled proxies, 13 Oct 2026; **not the Google results page**):
- *WebSearch proxy, top ten:* amerisleep.com (mattress retailer blog), cqu.edu.au news (a sleep scientist's explainer), mattressclarity.com, sleepreviewmag.com (trade press), risescience.com (a sleep app's blog), slumberstudios.com, sleepreviewmag.com again, simbasleep.com (mattress), theconversation.com (2021), caringsupport.com.
- *DuckDuckGo proxy, top ten:* sleepfoundation.org news, thebettersleepclinic.com, mattressnut.com, welltory.com (app blog, "Best Sleep Trackers 2026: Accuracy Compared"), wearablewellnessguide.com, thesleepconsultant.com, thehippiescientist.net, nytimes.com/wirecutter (best sleep trackers), kygo.app, zomni.app ("11 Devices vs the Sleep Lab").
- What they miss: no device maker's own page is in either top ten; the pages that quote accuracy percentages mostly quote them without the study, its size or who paid for it; none says what to do with an estimate once you know it is one; several are "best tracker" lists wearing the accuracy question as a title. A primary-source-first explainer that names each study's design, size and funder, and then says what an estimate is good for, is the gap.
- AI-search visibility: **not pulled**. The WebSearch proxy generated a synthesised answer citing amerisleep, CQU, RISE and The Conversation, and itself warned that several figures lacked a primary citation. Pages that carry the study, the size and the number in one sentence are the ones such answers quote; the answer-first paragraph below is written to be that sentence.
- Forum signal: three autocomplete seeds carry a "reddit" suffix ("how accurate are sleep trackers reddit", "are sleep trackers accurate reddit", "sleep cycle accuracy reddit"). Reddit's position in the Google results is unknown until the pull.

Page type: explainer. The answer comes in the first 60 words with no product. Each supporting question gets one H2. The medical variant gets one short line and no number.

Title (58 characters): How Accurate Are Sleep Trackers? What the Lab Studies Show
Meta (145 characters): Sleep trackers tell sleep from wake well but estimate stages less reliably. What 24 studies and two lab trials found, and which numbers to trust.
H1: How accurate are sleep trackers?
URL: `/learn/how-accurate-are-sleep-trackers/`

## Answer first (40 to 60 words)

Wrist and ring trackers tell sleep from wake well but name stages less reliably (Chinoy 2021). Across 24 studies of 798 people they differed from polysomnography on total sleep time and time awake (Lee 2025). In a 62-person lab study, stage agreement was fair to moderate (Schyvens 2025). Stages are estimates; trends across nights are the useful part (Lee 2025).

(60 words. No product. Every sentence carries a source. This paragraph is the AI Overview candidate.)

## Outline

**H2 1. How accurate are sleep trackers?**
- The answer-first paragraph above.
- One plain definition: a sleep lab scores stages from recordings of brain activity, eye movements and muscle tone, under the American Academy of Sleep Medicine's scoring rules (AASM Manual, version 3, February 2023). A wrist or ring tracker has none of those signals. It estimates sleep from movement and heart rate (Miller 2020, describing the WHOOP strap; Altini and Kinnunen 2021, describing the Oura ring).

**H2 2. Are sleep trackers accurate at telling sleep from wake?** (autocomplete: "are sleep trackers accurate", "do sleep trackers work")
- Mostly yes for sleep, less so for wake. In a lab study of 34 healthy young adults over three nights, seven consumer devices identified at least 93% of sleep epochs but only 18% to 54% of wake epochs, and did worse on a deliberately disrupted night (Chinoy 2021; funded by the US Office of Naval Research, no device-maker funding).
- The same pattern in a one-night lab study of 62 adults and six wrist devices: more than 90% of sleep epochs identified, specificity for wake 29% to 52% (Schyvens 2025; funded by Flanders Innovation & Entrepreneurship).
- What that means for the reader, in plain words: a tracker tends to count time lying still as sleep, so a restless night can look better than it felt.

**H2 3. How accurate are the deep, light and REM stages?** (autocomplete: "sleep stages accuracy", the brand "sleep stages accuracy" family)
- Stages are the weak point. Across the six devices in Schyvens 2025, agreement with the lab on stages was "fair to moderate" (Cohen's kappa 0.21 to 0.53). Chinoy 2021 called stage results "inconsistent". Say what kappa is in one clause: how much better than chance the device's stage matched the lab's.
- Where trials disagree, show both. A WHOOP-funded study of 32 adults with one lab night reported good to excellent agreement for dream sleep and slow-wave sleep (Berryhill 2020; "funded by a grant to the University of Arizona from WHOOP Inc."). The two independent lab studies above found weaker stage agreement across devices. The honest line: results depend on the device, the night, and who ran the study.
- Deep and REM minutes are estimates. Read them as "more or less than my own usual", never as a lab result.

**H2 4. Which sleep tracker is most accurate?** (autocomplete: "sleep tracker accuracy comparison", the five brand families)
- No winner is named, and no accuracy percentage is attached to any brand. Instead: what the comparison studies measured and found at the level of the whole set (Lee 2025: devices from Fitbit, WHOOP, Garmin, Apple and others, pooled; Schyvens 2025: kappa range across six devices, with the authors' note that devices at the higher end "could be effectively used to track prolonged and significant changes in sleep architecture").
- Company-run studies, quoted as such: Oura's blog says its staging "achieves 79% agreement with gold-standard polysomnography (PSG)" (ouraring.com, "new sleep staging algorithm", published 16 Nov 2022, read 13 Oct 2026). The study it rests on is Altini and Kinnunen 2021: 440 nights from 106 people; its disclosure reads "H.K. is employed by Oura Health, M.A. is an advisor at Oura Health." WHOOP's own page on how well it measures sleep could not be read today (403), so the page quotes the WHOOP-funded Berryhill 2020 study instead and says who funded it.
- The rule for the reader: an accuracy figure is only comparable to another figure from the same lab, the same night and the same scoring method. Brand-to-brand percentages from different studies are not a league table.
- No device table on this page (the skill's table rules do not fit an explainer with no shipping Vybe row).

**H2 5. How do sleep trackers know when you fall asleep?** (autocomplete family "how do sleep trackers know")
- Movement slows and heart rate settles; the algorithm reads both (Miller 2020; Altini and Kinnunen 2021). Adding heart-rate-derived and time-of-day features raised four-stage accuracy from 57% to 79% in Oura's own dataset (Altini and Kinnunen 2021), which is the clearest public statement that movement alone is not enough for stages.
- Why bedtime matters: in Miller 2020, "bed times were entered by researchers", and the authors say the device is a reasonable estimate "if accurate bedtimes are manually entered". Lying in bed awake is the hardest case for every device (Chinoy 2021, specificity).

**H2 6. What percentage of sleep stages is normal?** (autocomplete)
- Explain why a population percentage cannot grade one person's night from a tracker: the tracker's stage split is itself an estimate (H2 3), and lab norms were scored from brain signals the tracker does not have (H2 1). The useful comparison is your own usual split on your own device, across weeks.
- No numeric stage table on this page. That is a deliberate break from the pages that print "20% deep sleep" as a target.

**H2 7. Can a sleep tracker tell you about sleep apnea?** (one short answer; autocomplete asks "can a sleep tracker detect sleep apnea", and this page never says that a tracker can)
- One paragraph, no number: a wellness tracker is not a medical device and gives no diagnosis. Snoring, gasping, or daytime sleepiness that worries you are for a clinician, who can order the lab test the studies above compare against. Nothing in this section names a feature of any product.

**H2 8. How to use a sleep estimate well**
- Compare you with you: same device, same wrist or finger, same wake-up routine.
- Trust total sleep and bedtime consistency before stage minutes (Lee 2025: "useful for tracking general sleep patterns"; Schyvens 2025: "prolonged and significant changes").
- Give it weeks, not nights.
- When a number moves, list what else changed, and treat each one as a possible explanation, not the cause.
- This section hands off to the one Vybe section.

## The Vybe angle (one section)

**H2: What a sleep answer should tell you**

A stage chart cannot tell you how sure it is or what it missed. Vybe is designed to answer in a plain sentence that states its confidence in words, with a reason you can count (Register row 14). It is designed to say what it could not see (row 15), and to name the explanations that fit instead of one culprit (row 19). Its sleep stages are estimated (row 6), read against your own usual nights rather than a population split (row 9), with five connected signals in view (row 3). Later, it is designed to check whether its own suggestion worked (row 16).

Show one answer, labelled **"prototype, sample data"**:

> "Your estimated deep sleep has run below your own usual for four nights. Low confidence: four nights, and a wrist sensor's sleep stages are estimates, not a lab reading. Later bedtimes fit best; Tuesday's late dinner fits too. What Vybe could not see: how rested you feel, anything you drank. One next step: keep tonight's bedtime close to your usual and check again in a week."

Then the proof underneath, in its own sentences: Vybe is a screenless band (row 1), so there is nothing to check at 3am. There is no required consumer subscription (row 2). Health data is never sold; it is shared only with your consent, with service providers that run the service, or where the law requires (row 4).

Rules for this section:
- Every sentence that asserts rows 14, 15, 16 or 19 keeps "designed to" as its main verb. Vybe is pre-launch; nothing here says Vybe *does* something in the present tense.
- "Estimated" sits next to "sleep stages" every time (row 6). The answer's own confidence line repeats it, so the page practises what it explains.
- The sample answer gives two explanations (bedtimes, a late dinner), both everyday, neither an illness.
- No accuracy claim for the band, no percentage, no "validated" (the homepage says "validation has not been established", read 13 Oct 2026), no sensing spec (the homepage says "sensing specifications remain unconfirmed"), no battery figure, no ring. Words are "HRV and heart rate" only.
- The "no required consumer subscription" sentence stands apart from the sentence that says the band is designed to produce the answer, with the screenless sentence between them, so the two never read as row 21.
- Do not quote the prototype's "4 of 7" tally.

## Proof and sources

Abstracts and disclosures were read through Europe PMC on 13 Oct 2026. Use each source at the strength stated and no further. Study design and size go into the page copy, not only here.

| Statement on the page | Source | Design, size, funding | Does not support |
|---|---|---|---|
| Consumer wrist trackers differ from polysomnography on total sleep time, sleep efficiency, sleep latency and wake after sleep onset; still "useful for tracking general sleep patterns" | Lee YJ et al., *J Clin Sleep Med* 2025;21(3):573-582. [doi:10.5664/jcsm.11460](https://doi.org/10.5664/jcsm.11460) (brand-brief evidence library) | Meta-analysis, 24 studies, 798 participants, devices including Fitbit, WHOOP, Garmin, Apple Watch, Xiaomi | Any figure for the Vybe band; any per-brand ranking (the subgroup results are by device family, not a league table) |
| Seven devices identified ≥93% of sleep epochs; wake specificity 0.18 to 0.54; stage results "inconsistent"; worse on disrupted nights | Chinoy ED et al., *Sleep* 2021;44(5):zsaa291. [doi:10.1093/sleep/zsaa291](https://doi.org/10.1093/sleep/zsaa291) | Lab trial, 34 healthy young adults, 3 nights, 4 wearables and 3 bedside devices. "Funded by the Office of Naval Research"; "no funding or other financial support … from any device companies" | Claims about older adults, shift workers or people with sleep disorders; the 2017-era devices tested are not today's models |
| Six wrist devices: >90% of sleep epochs, specificity 29% to 52%, stage kappa 0.21 to 0.53, "fair to moderate agreement" | Schyvens AM et al., *Sleep Advances* 2025;6(2):zpaf021. [doi:10.1093/sleepadvances/zpaf021](https://doi.org/10.1093/sleepadvances/zpaf021) | Lab trial, 62 adults (52 men), one night, Fitbit Charge 5, Fitbit Sense, Withings ScanWatch, Garmin Vivosmart 4, WHOOP 4.0, Apple Watch Series 8. Funded by Flanders Innovation & Entrepreneurship; "no financial arrangements or affiliations" | Any per-brand verdict on the page; a one-night study of mostly men does not generalise to a reader's nights |
| Oura's staging reached 96% sleep/wake and 79% four-stage accuracy with heart-rate-derived and time-of-day features, 57% with movement alone | Altini M, Kinnunen H, *Sensors* 2021;21(13):4302. [doi:10.3390/s21134302](https://doi.org/10.3390/s21134302) | Company dataset, 440 nights, 106 people, 5-fold cross-validation. Disclosure: "H.K. is employed by Oura Health, M.A. is an advisor at Oura Health." | Independent validation of the shipping ring; comparison with any other brand |
| Oura's public claim, quoted as the company's own words | ouraring.com/blog/new-sleep-staging-algorithm/, published 16 Nov 2022, read 13 Oct 2026: "achieves 79% agreement with gold-standard polysomnography (PSG)" | Company blog | Anything beyond the quoted sentence |
| A WHOOP-funded lab study found good to excellent agreement for slow-wave and dream sleep | Berryhill S et al., *J Clin Sleep Med* 2020;16(5):775-783. [doi:10.5664/jcsm.8356](https://doi.org/10.5664/jcsm.8356) | Randomised crossover trial plus one PSG night, 32 participants (21 women, mean age about 24). "This study was funded by a grant to the University of Arizona from WHOOP Inc." | That the result holds for other devices, other ages or more than one night; the trial's sleep-quality finding is a separate question and is not used on this page |
| Wrist trackers estimate sleep from movement and heart rate; agreement with the lab was 89% for sleep/wake and 64% for four stages; bedtimes were entered by researchers | Miller DJ et al., *J Sports Sci* 2020;38(22):2631-2636. [doi:10.1080/02640414.2020.1797448](https://doi.org/10.1080/02640414.2020.1797448) | Lab protocol, 12 healthy adults, 86 sleeps. **Funding statement not retrieved today** (publisher and repository both refused the fetch); retrieve and disclose before publishing | Any accuracy claim about today's WHOOP hardware or app |
| A sleep lab scores stages under published rules | AASM Manual for the Scoring of Sleep and Associated Events, version 3, February 2023 (aasm.org/clinical-resources/scoring-manual/, read 13 Oct 2026): "rules for scoring sleep stages, arousals, respiratory events during sleep, movements during sleep and cardiac events" | Standards document | Any statement about a consumer device |

Not used on this page, on purpose: the Dial 2025 heart-rate and HRV validation (it is about overnight HRV, not sleep stages, and belongs to the HRV pages); any vendor-blog percentage without a primary citation; the Haghayegh 2019 Fitbit meta-analysis until its funding statement is read.

## Call to action

One call to action: **Join the waitlist**, worded as the site's button ("Join the waitlist", read 13 Oct 2026). The "first 1,000" line is left out: Register row 11 is on hold until the homepage and /terms agree.

## Schema and AI search

- `Article` schema with the H2s as question headings. `FAQPage` markup is optional: since 2023 Google shows FAQ rich results only for well-known government and health sites, so it earns no rich result here, though it does no harm.
- The 60-word answer-first paragraph is the AI Overview and assistant candidate: four sentences, each with a study and its finding, two with the study's size.
- Keep the page under 20K tokens. Allow GPTBot, ClaudeBot, PerplexityBot and Google-Extended in `robots.txt`. Add the page to `llms.txt` under /learn.
- Internal links:
  - from `/learn/heart-rate-variability-explained/` ("What raises and lowers HRV" section) with the anchor "how accurate are sleep trackers";
  - from `/learn/screenless-health-wearable/` ("A practical comparison checklist") with the same anchor;
  - from this page to `/learn/heart-rate-variability-explained/` (the heart-rate half of staging) and to `/learn/whoop-recovery-score-meaning/` (a score built partly on sleep estimates);
  - to `/compare/whoop-vs-oura/` once that page exists, from H2 4.

## Measure

- **Current position.** None: no impression for any sleep query, 12 Jul to 10 Oct 2026.
- **Targets.** At the 8-week review: impressions on the "sleep tracker accuracy" family (queries containing "sleep" and "accura" or "stage"), and an average position of 30 or better for "how accurate are sleep trackers". Later: top 10 (the seo-plan definition of a working page) with Organic Search `waitlist_signup` attributed to the page in GA4.
- **Review date.** 8 weeks after publishing. Record the publish date on the scoreboard.
- **Decision rules.**
  - If impressions rise but the click rate stays under 1%, rewrite the title and meta.
  - If there are no impressions at 8 weeks, run URL inspection, then check internal links and indexing before touching the copy.
  - If the brand-variant queries ("how accurate is fitbit sleep stages", and so on) bring most impressions, add one H3 per brand under H2 4 that quotes that brand's own page and the independent study that included it, still with no winner.
  - If the page earns clicks but no waitlist signups after 8 weeks, test the position of the Vybe section before changing the CTA.

## Plan check (`seo-plan.md`, step 4b)

The plan's Phase 2 Sleep pillar is a commercial guide, "Best Sleep Trackers Without a Subscription: What You Actually Own", with "sleep tracker accuracy" as one starting query. Today's evidence says the accuracy question is its own explainer: it has its own ten-deep question family across five brands, and a "best … without a subscription" title cannot answer "how accurate" in its first sixty words. Two more things the plan does not know: `/learn/wearable-subscriptions/` and `/learn/health-data-privacy-ownership/` exist and earned zero impressions in 90 days.

Proposed dated note for `seo-plan.md` (this run delivers one file, so the note stays here for the agent to apply): "13 Oct 2026: the Phase 2 Sleep pillar splits in two. `/learn/how-accurate-are-sleep-trackers/` is an explainer for the accuracy question family (volume and KD not pulled: DataForSEO unfunded, 13 Oct 2026; brief in `briefs/how-accurate-are-sleep-trackers.md`). The commercial sleep guide keeps 'sleep tracker no subscription' and links to the explainer. Before any new 'without subscription' or 'own your data' page, rewrite the two existing pages that earn nothing: `/learn/wearable-subscriptions/` and `/learn/health-data-privacy-ownership/` (0 impressions, 12 Jul to 10 Oct 2026)."

## Before publishing

- **Fund DataForSEO**, then pull: Google Ads search volume and the 12-month series for "how accurate are sleep trackers" and the supporting family; Labs bulk KD for the same; the Google organic SERP (desktop, depth 20, AI Overview and People Also Ask) for the target query. Replace every "not available" above, replace the autocomplete stand-in with the real People Also Ask, and record Reddit's position.
- **Fund Firecrawl**, then re-read vybe.health (`onlyMainContent: false`, `waitFor` 3000) so the "no page mentions sleep stages" statement cites the scrape the skill asks for; today's statement cites the session's page fetch.
- Retrieve the Miller 2020 funding statement and disclose it in H2 1 and H2 5 if WHOOP funded or supplied the study. Try to read WHOOP's own sleep-measurement page (403 today) so the company is quoted from its own words as Oura is.
- Founder signs off Claim Register rows 14, 15, 16 and 19 for public copy, and confirms row 6's "estimated" wording is how the app will label stages.
- Re-read /faq and /hardware for the sensing line before scheduling; the homepage line "sensing specifications remain unconfirmed" (13 Oct 2026) means the sample answer stays labelled "prototype, sample data" and keeps "designed to".
- Standards rule 4: the text was searched for the two forbidden strings (the other venture's name and the founder's personal handle); neither appears anywhere in this file.

## Concept check

1. **Audience and channel.** End users asking a question, on a search page. The lead is the direct answer in the first sentence: "Wrist and ring trackers tell sleep from wake well but name stages less reliably." The "then" column comes after the shown answer and points back to it: "Vybe is designed to answer in a plain sentence that states its confidence in words, with a reason you can count", then the proof sentences, each on its own, with the screenless sentence between the pointer and "There is no required consumer subscription".
2. **Swap test.** The hook is the searcher's question, which any sleep blog can carry; that is allowed on a search page. The Vybe section's opening, "A stage chart cannot tell you how sure it is or what it missed", fits no competitor: Oura, WHOOP, Fitbit and Garmin each publish an accuracy figure and none publishes its confidence per answer.
3. **Show it.** One answer is shown, labelled "prototype, sample data": a sentence ("Your estimated deep sleep has run below your own usual for four nights"), its confidence with a countable reason ("Low confidence: four nights, and a wrist sensor's sleep stages are estimates"), a blind spot ("What Vybe could not see: how rested you feel, anything you drank"), two explanations and one next step.
4. **Order.** The page answers first by the explainer rule. Inside the Vybe section the calibrated answer comes first; "screenless band", "no required consumer subscription" and the row 4 data line come after the shown answer as proof.
5. **Two products.** This piece sells the band's thinking to end users. The platform half has to come from the same week's builder piece (LinkedIn or /developers); the page keeps one CTA and adds no builder link.
6. **Claims.** Rows 14, 15, 16 and 19 each sit in a "designed to" sentence ("designed to answer in a plain sentence", "designed to say what it could not see", "designed to check whether its own suggestion worked", "designed to … name the explanations that fit"). Row 6 carries "estimated" in the section and inside the answer ("sleep stages are estimates"). Rows 1, 2, 3 and 9 are approved facts. Row 4 is in the Register's own wording. The sample answer gives two everyday explanations. Every health statement names its study, size and funder in the copy. No percentage is attached to Vybe.
7. **Roadmap and offers.** Nothing relies on an unreleased feature or an unconfirmed spec: no battery figure, no "validated", no heart-rhythm term, no ring, no sensing spec, no accuracy figure for the band. The row 11 offer is left out while it is on hold. No builder offer.
8. **Voice.** Plain and declarative, one action ("Join the waitlist"), no winner ("No winner is named"), and willing to say what is unknown: "not available", "not pulled", "Funding statement not retrieved today".

## Guardrail and rubric score

- `python3 vybe-marketing/evals/check_marketing.py vybe-marketing/briefs/how-accurate-are-sleep-trackers.md`, run 13 Oct 2026: **0 blocking findings, exit 0.** Four lines were matched and allowed (two sentences that quote the "sleep apnea" autocomplete phrase while saying the page never serves it, the "not a medical device … no diagnosis" line, and the row 4 privacy sentence, which names service providers and the law). One earlier draft of the H2 7 heading failed because it quoted the autocomplete phrase without a marker; the heading now says the page never makes that claim.
- Search-brief rubric (`evals/search-brief-rubric.md`), self-scored: D1 Demand evidence **1** (dated sources and Search Console status, but no volume or KD for the target query; this is the reason the brief is not ready to publish); D2 Answer first **3** (gate); D3 Searcher fit **2** (right type, every autocomplete question covered and the gap named, but the real People Also Ask was not pulled); D4 Vybe angle **3**; D5 Claim and health safety **3** (gate); D6 Measurability **3**. Total **15 of 18**, pass on the gates, with D1 to be re-scored once DataForSEO is funded.

## Notes on the skill (3 lines)

1. The "Current priorities" table has a corrupted row: "meal timing … CPC is high (HRV dropped after late night..82)". The CPC figure is lost and a candidate query has been pasted into the wrong cell. Restore the figure from the 3 Oct pull or mark it "not available".
2. The unfunded fallback names "Firecrawl or Exa" as the results-page stand-in. Standards rule 1 bars `mcp__Exa__*`, and Firecrawl is also unfunded today. The skill should name the allowed public fallbacks (the session's web search and page fetch, Google autocomplete) and say how to label them, which this brief does.
3. The step-3 "improve the page" rule needs a case for pages that exist and earn nothing: two of today's candidates had a live page with zero impressions in 90 days. The rule should say to audit that page's title, indexing and links before writing a brief on the same question.

## Which numbers are real and which are not

- **Real, pulled today (13 Oct 2026):** every Search Console figure (window, rows, impressions, positions); the DataForSEO and Firecrawl failure codes and balances; the Google autocomplete families; the two results-page proxies; every study's design, size, result and disclosure; the Oura blog quote and date; the vybe.health quotes.
- **Real, but dated 3 Oct 2026 and not re-pulled:** every volume and KD in the sizing table for "what is a good hrv", "screenless fitness tracker", the "without subscription" terms and "why is my hrv low".
- **Public third-party estimates, context only:** "sleep tracker" 40,500 or 60,500 and "best sleep tracker" 6,600 (seodata.dev, rankhero.com).
- **Not available, and not estimated:** volume, KD, CPC, People Also Ask and AI Overview for the target query and its family.
