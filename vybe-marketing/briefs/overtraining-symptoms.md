# Move: brief an explainer for "overtraining symptoms".

# Brief: Overtraining Symptoms: The Signs and When to See a Clinician

Category: Content & SEO (2), with AI search (3) | Audience: end users asking the question (closest segments: the HYROX training community and baseline nerds) | Channel: search page | Number to move: Search Console impressions and clicks for the "overtraining symptoms" cluster, and Organic Search `waitlist_signup` in GA4
Decision: write a new Move explainer at `/learn/overtraining-symptoms/`. No Vybe page gets impressions for the question (see "Vybe today"), so there is nothing to improve and nothing to cannibalise.

Question: "overtraining symptoms" / "how do I know if I'm overtraining?"      Pillar: Move (training load). concept.md: "For consumers use 'overtraining' and 'rest day'. A Move piece shows a Move answer (load against the person's own normal), not a sleep answer."

Page type: explainer for a symptoms query. The safety rows of the page-type table govern the whole page:
- no diagnosis: the page never tells a reader they are or are not overtrained;
- no thresholds: no heart-rate, HRV or load-ratio cut-off anywhere, including the ones competitors print;
- it says plainly when to see a clinician, in the answer-first paragraph and in its own section.

Target query: overtraining symptoms — 3,600/mo, KD 8 (DataForSEO, US, as recorded in the skill's priorities table, pulled 3 Oct 2026). CPC not pulled. **KD not re-pulled (Labs unfunded).**
- Every DataForSEO call this run returned "40200 Payment Required" on 3 Oct 2026. That covers SERP task post (twice), Keywords Data keywords-for-keywords live and Labs bulk keyword difficulty. The account shows a $0.996 balance, so the block is more than the Labs funding the skill describes. **Flag to the founder: DataForSEO is unusable until the account is funded.**
- No 12-month series and no Trends pull, so no trend figure and no latest-month or peak figure is quoted. The volume is the bucket from the priorities table, not a fresh pull.
- Volume conflict to settle: concept.md gives Move "~2k consumer searches". The priorities table gives this single query 3,600. Refresh both from one pull before the Move row is reused.

Supporting queries (none sized this run; DataForSEO unfunded on 3 Oct 2026; do not publish volumes for them until pulled):
- signs of overtraining: the wellness-intent variant. Polar, HSS and NASM pages use this phrasing.
- am i overtraining / how do you know you're overtraining: Reddit thread titles (Firecrawl search, 3 Oct 2026).
- overreaching vs overtraining: answered in H2 2.
- rest day: the consumer Move term in concept.md. Linked, not targeted here.
- Left to medical sites on purpose: "overtraining syndrome" and "overtraining syndrome treatment". Their leading result is a disease page ("Diseases & Conditions", Cleveland Clinic) and the intent is clinical. A wellness page must not serve diagnosis or treatment intent (skill step 4d).

People Also Ask to answer: **not pulled.** The SERP task was refused (40200). The H2 questions below come from Firecrawl search titles and headings on 3 Oct 2026, not from Google's PAA box:
- "How can I tell if I'm overtraining?" (Polar H2)
- "Should I Worry About Overtraining if I'm Not an Elite Athlete?" (Polar title)
- "How do you know you're overtraining?" (r/naturalbodybuilding title)
- "How did you know it was overtraining and not something else?" (r/AdvancedRunning title)
- "What is overtraining syndrome?" and "When should I see my healthcare provider?" (Cleveland Clinic headings)

**Before publishing:** pull the Google SERP for "overtraining symptoms" (Google organic, US, en, `location_code` 2840, with AI Overview and People Also Ask). Add any PAA question it shows as an H2, drop or reword any H2 it does not support, and read the AI Overview. The page does not ship until that pull is in this brief.

Vybe today (Search Console, `sc-domain:vybe.health`, `data_state: final`, 3 Jul to 30 Sep 2026, the range ending 3 days before this 3 Oct pull):
- **Pull 1**, dimensions query and page, no filter: 10 rows. Every row is an HRV definition query on `/learn/heart-rate-variability-explained/` (average position 83 to 97), plus "vybe health" on the homepage at position 4. Nothing about overtraining, training load, rest or recovery.
- **Pull 2**, dimension query, filter `includingRegex` "overtrain|over train|rest day|training load|recovery|fatigue": no rows.
- **Pull 3**, dimension page alone: 28 impressions and 0 clicks across 10 pages. 15 of them are on `/learn/heart-rate-variability-explained/`, at an average position of about 83. No Move page exists.
- **Firecrawl read of `/learn/`** (3 Oct 2026, `onlyMainContent: false`, `waitFor` 3000): the hub lists HRV, recovery-score, screenless, subscription, privacy and device-claim guides, and no overtraining or training-load guide. The HRV explainer has a section "Using HRV to make a training decision" and the line "Sustained training load and stress may change your baseline over time".
- Conclusion: this is a new page. It links to the HRV explainer, with the anchor "HRV and training decisions". The HRV explainer links back here, with the anchor "overtraining symptoms".

Who ranks: **no Google ranking this run** (SERP unfunded). A Firecrawl web search for "overtraining symptoms" (US, en, 3 Oct 2026) returned this order. It is a proxy, not Google's positions:
1. Cleveland Clinic, "Overtraining Syndrome: Symptoms, Causes & Treatment Options" (my.clevelandclinic.org/health/diseases/overtraining-syndrome, "Last updated on 02/28/2024", read through Firecrawl 3 Oct 2026). It calls OTS "a medical condition". It says "Visit a provider as soon as you notice symptoms or warning signs". It prints heart-rate cut-offs for bradycardia and tachycardia. It states "Studies estimate that around two-thirds of elite runners will experience it at some point" with no source shown.
2. PMC, "Overtraining Syndrome: A Practical Guide" (a clinical review).
3. Hoag Orthopedic Institute blog (Jan 2026).
4. NASM, a trainer's guide.
5. HSS, "Overtraining: What It Is, Symptoms, and Recovery" (hss.edu, read through Firecrawl 3 Oct 2026). It separates the two states: "Overreaching usually happens after several consecutive days of hard training and results in feeling run down. Luckily, the effects of overreaching can be easily reversed with rest."

Also in the proxy results:
- **Polar** at position 8, "Should I Worry About Overtraining if I'm Not an Elite Athlete?" (polar.com/en/guide/overtraining, read through Firecrawl 3 Oct 2026). It gives a fixed cut-off: a morning resting heart rate "significantly elevated from its usual average (seven or more beats per minute)" means "you're not fully recovered". It promotes its orthostatic test as a tool for spotting overtraining (this brief does not repeat the page's stronger wording), and it sells Training Load Pro, which compares "strain and tolerance".
- **Reddit.** An r/xxfitness thread at position 7. A second search ("overtraining symptoms reddit") returned five threads (r/naturalbodybuilding, r/Fitness, r/ultrarunning, r/Velo, r/AdvancedRunning). The r/AdvancedRunning title is the question this page answers: "How did you know it was overtraining and not something else?"

What the results miss: they are symptom checklists. The clinical pages treat a reader as a patient, and the brand page gives a fixed number. None says how weak any single signal is on its own, that heart-rate and HRV changes can run in either direction, or that self-reported measures tracked training load better than objective ones in a 56-study review.

Swap-test note for the Vybe section: "training load against your own normal" is hygiene. Polar's Training Load Pro already compares today's load with recent training, so the Vybe section cannot lead with it.

Title (60 characters): Overtraining Symptoms: The Signs and When to See a Clinician
Meta (157 characters): Overtraining symptoms include lasting fatigue, a drop in performance and mood changes. Why no single number confirms it, and when to see a clinician instead.
H1: Overtraining symptoms
URL: `/learn/overtraining-symptoms/`

## Answer first (40 to 60 words)

Common overtraining symptoms are lasting fatigue, a drop in performance and mood changes (ECSS and ACSM consensus, Meeusen 2013), plus poor sleep and more frequent colds (Cleveland Clinic, 2024). No single test or number confirms overtraining; clinicians first rule out other causes (Carrard 2021, a review of 39 studies). Cleveland Clinic advises seeing a provider when symptoms appear.

(58 words by `wc -w`. No product, no number, no cut-off. Every sentence carries an inline source, linked in the copy. The page names no product here. This paragraph is the AI Overview candidate.)

## Outline

**H2 1. What are the symptoms of overtraining?**
- The answer-first paragraph above.
- Then three plain groups, taken from the cited pages and the consensus statement, with no numbers attached:
  - **in training:** performance slipping, heavy legs at easy effort, soreness that lingers;
  - **day to day:** tiredness that rest does not fix, poor sleep, low motivation, irritability;
  - **health:** more frequent colds, appetite changes, injuries that keep coming back, changes to periods.
- Say in the copy that many of these also have other causes, which is why the list cannot tell anyone what is going on (H2 3).
- **Do not reproduce** Cleveland Clinic's beats-per-minute cut-offs or Polar's "seven or more beats per minute" rule. That is the skill's no-threshold rule for a symptoms page.

**H2 2. Overreaching or overtraining: what's the difference?**
- An expert consensus statement from the European College of Sport Science and the American College of Sports Medicine sets out the stages (Meeusen 2013, consensus statement, not a trial):
  - a short dip after hard training that recovers and leaves you fitter ("functional overreaching");
  - a longer dip that needs weeks to recover ("nonfunctional overreaching");
  - overtraining syndrome, a prolonged problem.
- The same statement says that telling the last two apart "is very difficult". It says the distinction depends on how things turn out and on ruling out other causes. It also says there is "no scientific evidence" yet to confirm or refute that overtraining symptoms are more severe. Quote these two phrases word for word.
- HSS's point, attributed: overreaching after several hard days can be reversed with rest.

**H2 3. How do you know it's overtraining and not something else?** (the r/AdvancedRunning question)
- The consensus statement explains overtraining by first excluding other things. Its examples include infection, not eating enough for the training, and low iron (Meeusen 2013). Write "a clinician checks", never "check yourself for".
- Not eating enough for the amount of training is its own recognised problem in sport, with overlapping signs. The IOC consensus statement on Relative Energy Deficiency in Sport (Mountjoy 2023, an expert consensus) introduces a clinical assessment tool for it. Say only that this overlap is one more reason the question belongs with a clinician.
- Everyday explanations that change the same signals: a hard block of training, short nights, work stress, a cold coming on, alcohol, travel. List them side by side. Never rank one as the cause.

**H2 4. Can heart rate or HRV tell you you're overtrained?**
- Not on its own, and the direction can surprise people.
  - Popular guides describe a higher morning heart rate or a lower HRV.
  - In a randomised trial of 21 male triathletes, 13 trained harder for three weeks and 8 trained normally (Le Meur 2013). The harder-training group's weekly-averaged HRV rose, not fell, and resting heart rate went down. Both reversed during a lighter week.
  - The same trial found single once-a-week readings showed no clear change, because day-to-day variation was so wide.
- In about 9 million morning measurements from 28,175 app users, HRV and resting heart rate shifted with training, alcohol, menstrual-cycle phase and sickness (Altini and Plews 2021, observational). HRV was sensitive but not specific. Disclose in the copy that the measurements came from a smartphone app that first author Marco Altini created (HRV4Training). Confirm the paper's conflict-of-interest statement before publishing.
- The line to write: a change in your numbers is a reason to look at what else changed, not a verdict. No cut-off in ms or beats per minute.

**H2 5. Should you worry about overtraining if you're not an elite athlete?** (Polar's title question)
- In a survey of 376 young athletes across 19 sports, 29% reported having been overreached or overtrained at least once (Matos 2011, cross-sectional survey). Training load alone was not a significant predictor in that survey; competitive level and sex explained a small share. Use association words only.
- A scoping review of 47 studies in strength sports and resistance training found evidence of nonfunctional overreaching. It found "minimal evidence" that true overtraining syndrome had occurred in those groups (Bell 2020, scoping review).
- Do not repeat Cleveland Clinic's unsourced "two-thirds of elite runners" figure.

**H2 6. Does a training-load number tell you when to rest?**
- Researchers disagree. Show both sides:
  - A 2016 review proposed comparing recent load with longer-term load, as a ratio, to manage injury risk (Gabbett 2016, narrative review).
  - A 2020 methods analysis argued that no study had properly estimated a causal effect. It concluded "There is no evidence supporting the use of ACWR in training-load-management systems or for training recommendations aimed at reducing injury risk" (Impellizzeri 2020, methodological critique, no new participants).
- A systematic review of 56 studies found that self-reported measures such as mood and perceived stress tracked training load "with superior sensitivity and consistency" compared with objective measures. The two kinds of measure generally did not correlate (Saw 2016, systematic review).
- The line to write: how you feel is data too. No ratio, zone or cut-off on this page.

**H2 7. Rest days and recovery: what helps?**
- Keep this general and non-prescriptive:
  - the consensus statement frames prevention as balancing overload with enough recovery (Meeusen 2013);
  - HSS says overreaching can be reversed with rest;
  - Cleveland Clinic says recovery from the syndrome "can take anywhere from a few weeks to months".
- No fixed number of rest days, no taper rule, no supplement or diet advice. Sleep and eating enough for the training are named as part of recovery, not as treatment.

**H2 8. When should you see a clinician?**
- **Stop and get urgent care** for chest pain, fainting, or breathlessness that is out of proportion to the effort, during or after exercise.
- **Book a clinician or a sports medicine doctor** if any of these apply:
  - tiredness or a drop in performance does not ease with rest;
  - you keep getting ill or injured;
  - your periods change or stop;
  - you lose weight without trying;
  - low mood stays, or you feel unlike yourself.
- Say plainly: no wearable, app or symptom list can rule overtraining in or out. That is a clinician's job, because other causes have to be checked first (Meeusen 2013; Carrard 2021).
- No time-based cut-off ("after two weeks"); "does not ease with rest" is the wording.

**H2 9. How to read your own training data**
- Compare with your own normal, on the same device, at the same time of day.
- Look at weekly averages before single days (Le Meur 2013 found single weekly readings missed the change).
- Put how you feel next to the numbers (Saw 2016).
- When the numbers move, list what else changed as possible explanations, not one cause.
- This section hands off to the one Vybe section.

## The Vybe angle (one section)

**H2: What an answer about your training load should tell you**

A training-load score can't tell you how sure it is, or what else changed that week. Vybe is designed to answer in a plain sentence that states its confidence in words, with a reason you can count (Register row 14). It is designed to say what it could not see (row 15), and to name the explanations that fit instead of one culprit (row 19). After you try a change, Vybe is designed to check whether its suggestion worked, and to show the times it didn't (row 16).

Show one Move answer, labelled **"prototype, sample data"**:

> "Your training load has been above your own normal for three weeks, and your morning heart rate has sat above your usual range for four days. The added interval session fits most closely; three short nights and a heavy work week fit too. Moderate confidence: 24 days of data, and two mornings with no reading. What Vybe could not see: how your legs feel, and how you slept before you started wearing the band. One next step: make Thursday an easy day and check again on Saturday."

The band is designed to produce that answer: the site describes Move as "Training load, weighed against your own norm" (vybe.health homepage, Firecrawl, 3 Oct 2026). The band reads that load against your own baseline, not a population average (row 9), across five connected signals (row 3). Vybe is a wellness product, not a medical device. It is designed to show a pattern, and whether anyone is overtrained is a question for a clinician (row 13). There is no required consumer subscription (row 2).

Rules for this section:
- Every sentence that asserts rows 14, 15, 16 or 19 keeps "designed to". Vybe is pre-launch, so nothing here says Vybe *does* something in the present tense.
- The sample answer is a Move answer (load against the person's own normal), not a sleep answer. Its explanations are everyday ones (training, sleep, work). It names no illness, and it never says "overtraining".
- Do not lead with "training load against your own normal". Polar's Training Load Pro already offers it (swap test).
- Hygiene comes after the unclaimed idea and the shown answer, never before: own baseline (row 9), then no required subscription (row 2) in the site's wording.
- No "4 of 7" tally. No accuracy claim for the band. The words are "HRV and heart rate" only. No battery figure. No GPS statement (row 20 unconfirmed).

## Proof and sources

Health statements were checked on PubMed (design, size and abstract read for each) and on the named pages through Firecrawl, 3 Oct 2026. Use each at the strength stated and no further.

| Statement on the page | Source and design | Strength | Does not support |
|---|---|---|---|
| Fatigue, performance decline and mood disturbance are typical symptoms; NFOR and OTS are "very difficult" to tell apart; recognising OTS rests on ruling out other causes; no single marker is generally accepted | Meeusen et al., *Med Sci Sports Exerc* 2013, joint ECSS and ACSM consensus statement. [doi:10.1249/MSS.0b013e318279a10a](https://doi.org/10.1249/MSS.0b013e318279a10a) | Expert consensus | Any self-check, cut-off or marker |
| No gold-standard test; OTS is recognised only by ruling out other causes; candidate markers and scores need validation in larger samples and in women | Carrard et al., *Sports Health* 2022 (online 2021), scoping review of 39 studies. [doi:10.1177/19417381211044739](https://doi.org/10.1177/19417381211044739) | Scoping review | That any listed marker works for one person |
| Three weeks of harder training raised weekly-averaged HRV and lowered resting HR; single weekly readings missed it; reversed with taper | Le Meur et al., *Med Sci Sports Exerc* 2013, randomised trial, 21 male triathletes (13 intensified, 8 normal). [doi:10.1249/MSS.0b013e3182980125](https://doi.org/10.1249/MSS.0b013e3182980125) | Small randomised trial, men only | Women, non-athletes, or any direction rule |
| HRV and resting HR shift with training, alcohol, cycle phase and sickness; sensitive, not specific | Altini and Plews, *Sensors* 2021, about 9 million measurements from 28,175 people, collected with a smartphone app; first author created the app (HRV4Training; confirm the paper's disclosure). [doi:10.3390/s21237932](https://doi.org/10.3390/s21237932) | Large observational | Any single cause for one reader's change |
| Self-reported measures tracked training load more sensitively and consistently than objective ones; the two generally did not correlate | Saw, Main and Gastin, *Br J Sports Med* 2016 (online 2015), systematic review of 56 studies. [doi:10.1136/bjsports-2015-094758](https://doi.org/10.1136/bjsports-2015-094758) | Systematic review | That wearables are useless, or that feelings settle the question |
| 29% of young athletes reported NFOR/OT at least once; load not a significant predictor in that survey | Matos, Winsley and Williams, *Med Sci Sports Exerc* 2011, cross-sectional survey of 376 athletes aged about 15, 19 sports. [doi:10.1249/MSS.0b013e318207f87b](https://doi.org/10.1249/MSS.0b013e318207f87b) | Association (self-report survey) | Adult or recreational prevalence |
| NFOR occurs in resistance training; minimal evidence of true OTS there | Bell et al., *J Sports Sci* 2020, scoping review of 47 studies. [doi:10.1080/02640414.2020.1763077](https://doi.org/10.1080/02640414.2020.1763077) | Scoping review | That lifters can't be overtrained |
| A ratio of recent to longer-term load proposed for managing injury risk | Gabbett, *Br J Sports Med* 2016, narrative review. [doi:10.1136/bjsports-2015-095788](https://doi.org/10.1136/bjsports-2015-095788) | Narrative review | Any ratio threshold on this page |
| No evidence supports that ratio for training recommendations; no causal effect estimated | Impellizzeri et al., *Int J Sports Physiol Perform* 2020, methodological critique. [doi:10.1123/ijspp.2019-0864](https://doi.org/10.1123/ijspp.2019-0864) | Methods analysis, no participants | That load monitoring has no value |
| Low energy availability is its own syndrome with overlapping signs, assessed clinically | Mountjoy et al., *Br J Sports Med* 2023, IOC consensus statement on REDs. [doi:10.1136/bjsports-2023-106994](https://doi.org/10.1136/bjsports-2023-106994) | Expert consensus | Any eating or weight advice |
| Symptom list (poor sleep, frequent colds); "Visit a provider as soon as you notice symptoms"; recovery takes "a few weeks to months" | Cleveland Clinic, Overtraining Syndrome (last updated 28 Feb 2024; Firecrawl, 3 Oct 2026) | Patient education page | Its bpm cut-offs and its unsourced prevalence figure, which this page does not repeat |
| Overreaching can be reversed with rest | HSS, Overtraining (Firecrawl, 3 Oct 2026) | Patient education page | Any rest-day rule |

Left out on purpose: Bosquet et al. 2008 (*Br J Sports Med*, meta-analysis of heart rate and over-reaching). Its abstract does not give the number of studies, and the full text was not available through PubMed Central on 3 Oct 2026. Without the size it can't meet the design-and-size rule. Add it only once the count is confirmed from the paper.

## Call to action

One call to action: **Join the waitlist.** No supporting offer line. Claim Register row 11 ("first 1,000 … guaranteed a position to buy") is on hold until the homepage and /waitlist agree (3 Oct 2026 conflict). The homepage still carried it on 3 Oct 2026 (Firecrawl).

## Schema and AI search

- `Article` schema, with every H2 written as a question.
- FAQPage markup for H2s 2 to 6 and 8 is optional. Since 2023 Google shows FAQ rich results only for well-known government and health sites, so it earns no rich result here, though it does no harm.
- The 58-word answer-first paragraph is the AI Overview candidate. The Overview itself was not read this run (SERP unfunded); read it in the pre-publish SERP pull and note where it differs.
- In the body, name each study with its design and size in one sentence ("a randomised trial of 21 male triathletes"), so a quoted sentence keeps its strength.
- Keep the page under 20K tokens. Add it to `llms.txt` under /learn. Allow GPTBot, ClaudeBot, PerplexityBot and Google-Extended.
- Internal links:
  - to and from `/learn/heart-rate-variability-explained/` (anchors "HRV and training decisions" and "overtraining symptoms");
  - to `/learn/whoop-recovery-score-meaning/`, with the anchor "what a recovery score can't tell you".

## Measure

- **Current position.** None. No impressions for any overtraining, training-load, rest-day, recovery or fatigue query, 3 Jul to 30 Sep 2026 (`data_state: final`; pulls listed under "Vybe today").
- **Targets.**
  - At the 8-week review: impressions on the overtraining cluster, and an average position of 30 or better for "overtraining symptoms" (KD 8, from the priorities table).
  - Later goal: top 10 (the seo-plan definition of a working page), with Organic Search `waitlist_signup` attributed to the page in GA4.
- **Review date.** 8 weeks after publishing. Record the publish date on the scoreboard.
- **Decision rules.**
  - If impressions rise but the click rate stays under 1%, rewrite the title and meta (test "Signs of Overtraining: What They Mean and When to Get Help").
  - If impressions come mainly from "overtraining syndrome" treatment queries, narrow the wording toward training and rest rather than chase clinical intent.
  - If there are no impressions at 8 weeks, run URL inspection and check indexing and internal links before touching the copy.
  - If the page earns clicks but no waitlist signups, test the Vybe section's position before changing the CTA.

## Note for the search plan (4b, dated 3 Oct 2026; this run is read-only, so the note stays here for the agent to apply)

`seo-plan.md` has no Move page in any phase. Its Phase 2 "Recovery" pillar ("recovery tracker no subscription, recovery score meaning, best recovery wearable") is the nearest home. The skill's priorities table lists "overtraining symptoms" at 3,600 a month, KD 8 ("Move for consumers"), which on those figures is easier than any Phase 2 HRV query. Suggest adding `/learn/overtraining-symptoms/` to Phase 2 under Recovery, as the Move entry, and refreshing its volume, KD and SERP once DataForSEO is funded. Also reconcile concept.md's "~2k consumer searches" for Move with the 3,600 for this one query.

## Flags for the founder

1. **DataForSEO:** every endpoint (SERP, Keywords Data, Labs) returned "40200 Payment Required" on 3 Oct 2026, with $0.996 showing as the balance. Search briefs can't be sized until it is funded.
2. **Homepage line (Firecrawl, 3 Oct 2026):** "so you can see what is actually driving the change". It reads as a cause claim. Same tension as the /enterprise "actually caused it" line in concept.md; counsel and the founder to review.
3. **Homepage Vitals line** still reads "Heart rhythm and HRV against your baseline" (Register row 5a, counsel to review). This page uses "HRV and heart rate" only.

## Concept check

Every quotation below is copied from the page copy: the answer-first paragraph, the Vybe section prose, the sample answer and the call to action.

1. **Audience and channel.**
   - End users on a search page, so the lead is the direct answer, in the first sentence: "Common overtraining symptoms are lasting fatigue, a drop in performance and mood changes".
   - The "then" column (calibrated answers, then the waitlist) comes after the shown answer and points back to it: "The band is designed to produce that answer". It is followed by "Join the waitlist."
2. **Swap test.** The hook is the searcher's question, which is right for search. The Vybe section opens on a line no competitor fits: "A training-load score can't tell you how sure it is, or what else changed that week." Load against your own normal, which Polar already offers, comes later as proof.
3. **Show it.** One Move answer is shown, labelled "prototype, sample data". It contains:
   - the sentence: "Your training load has been above your own normal for three weeks";
   - its confidence with a countable reason: "Moderate confidence: 24 days of data, and two mornings with no reading";
   - a blind spot: "What Vybe could not see: how your legs feel";
   - one next step: "make Thursday an easy day and check again on Saturday".
4. **Order.** The unclaimed idea comes first ("Vybe is designed to answer in a plain sentence that states its confidence in words, with a reason you can count"). Hygiene comes after the shown answer: "against your own baseline, not a population average (row 9)", then "There is no required consumer subscription (row 2)."
5. **Two products.** This page sells the band's thinking to end users with one CTA, "Join the waitlist." The platform half has to come from the same week's builder piece (LinkedIn or /developers). The team version of Move (H2F and performance staff) uses Register row 22 and stays unscheduled until the founder confirms it.
6. **Claims.**
   - "Designed to" governs every row 14 to 16 and 19 sentence:
     - "Vybe is designed to answer in a plain sentence";
     - "It is designed to say what it could not see (row 15)";
     - "Vybe is designed to check whether its suggestion worked, and to show the times it didn't (row 16)".
   - Row 13: "Vybe is a wellness product, not a medical device." Row 2 in the site's wording: "no required consumer subscription".
   - The Move line is quoted from the site, exactly: "Training load, weighed against your own norm".
   - The example gives more than one everyday explanation: "The added interval session fits most closely; three short nights and a heavy work week fit too."
   - No diagnosis, and no threshold anywhere: "No single test or number confirms overtraining".
7. **Roadmap and offers.** Nothing relies on an unreleased feature or an unconfirmed spec. There is no battery figure, no "validated", no ECG, no ring, no GPS statement and no accuracy figure. The row 11 offer is left out while it is on hold. No builder offer.
8. **Voice.** Plain, and willing to say what isn't known: "No single test or number confirms overtraining". It has one action ("Join the waitlist."), no hype, and points to a clinician instead of a verdict: "Cleveland Clinic advises seeing a provider when symptoms appear."

## Notes on the skill (3 lines)

1. Wrong or brittle: the skill says only Labs returned 40200 on 3 Oct 2026. In this run SERP and Keywords Data refused too, so the fallback (quote the priorities table) covers KD but leaves no route for PAA, who ranks, CPC or supporting volumes. The skill should say what to do when the whole account is blocked (Firecrawl search as a labelled proxy, plus a pre-publish SERP gate, as here).
2. Missing: a symptoms row in the page-type table. The safety rows cover HRV numbers, but symptoms pages need explicit rules: no time-based "see a doctor after N weeks" cut-off, no repeating competitor bpm thresholds, and urgent signs kept separate from routine ones.
3. Unclear: concept.md gives Move "~2k consumer searches" while the priorities table gives one Move query 3,600. The skill should name the source pull for each.

## Grader fixes before publishing (independent grade, 3 Oct 2026: 15/18, pass)

Status: **not ready to publish.** DataForSEO was unfunded, so the Google
results page and People Also Ask list were not pulled.
- Add a source beside the symptom groups (periods, appetite, recurring injuries, heavy legs), the everyday explanations in H2 3, and the urgent-care signs in H2 8.
- Describe Le Meur 2013 as run: 21 trained male triathletes, functionally overreached, who improved after the lighter week. Only the HRV responses are reported as reversing.
- Use one "when to see someone" rule across the answer-first paragraph and H2 8. Add a crisis route (988) beside "low mood stays".
- Rewrite "The band reads that load against your own baseline…" with "designed to".
- Founder sign-off is required for rows 14, 15, 16 and 19 before publishing.
