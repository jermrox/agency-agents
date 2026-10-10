# Brief: What Is a Good HRV? Why Your Own Baseline Beats a Chart

Category: Content & SEO (2), with AI search (3) | Audience: end users who are asking the question (closest segment: baseline nerds) | Channel: search page | Number to move: impressions and clicks for the "good hrv" cluster in Search Console, and Organic Search `waitlist_signup` in GA4
Decision: write a new explainer at `/learn/what-is-a-good-hrv/`. Don't fold it into the existing HRV page. Reason under "Vybe today".

Question: "what is a good hrv"      Pillar: Vitals (the pillar that leads search)
Target query: what is a good hrv — 14,800/mo bucket, KD 17, CPC $0.49 (DataForSEO, US, pulled 3 Oct 2026). Google Ads merges "good hrv" into the same 14,800, so the two are one number and must not be added. Over the 12 months from Sep 2025 to Aug 2026 the volume moved up one bucket, from 12,100 to 14,800, with an 18,100 spike in Jan 2026 (New Year). The pull has no same-month comparison a year apart, so I am not quoting a growth percentage.
Supporting queries (DataForSEO, 3 Oct 2026, monthly buckets):
- what is a good hrv score — 3,600, KD 18
- what is a normal hrv — 3,600, KD 31
- hrv by age — 8,100. "What is a good hrv by age" is 480 at KD 13. Answer it with the baseline explanation, not an age table.
- high hrv meaning — 1,300
- what is a good hrv while sleeping — 880, KD 18
- why is my hrv low — 590, KD 17. "Is low hrv bad" is 320.

Left to their own pages, so this page doesn't cannibalise them: "how to improve hrv" (8,100, KD 18), "what does hrv mean" (5,400, owned by the existing explainer) and "hrv tracker" (2,400, commercial).

People Also Ask to answer (SERP pull, US desktop, 3 Oct 2026):
- What is a good HRV for my age?
- Is 37 a low HRV?
- Is a 43ms HRV bad?
- Is 22ms HRV ok?
- What is an unsafe HRV?
- What do cardiologists say about HRV?

Vybe today (Search Console, `sc-domain:vybe.health`, 3 Jul to 1 Oct 2026):
- No impressions for "what is a good hrv" or any "good hrv" variant, in the last 90 days or in the full 16-month history.
- `/learn/heart-rate-variability-explained/` has 63 impressions, 0 clicks and an average position of 85.5. All of them come from definition queries ("heart rate variability", "what is heart rate variability", "heart rate variability meaning").
- No page is in a position to rank for the question, so this is a new page. The existing explainer keeps the definition intent and links here with the anchor text "what is a good HRV".
- Cannibalisation check: no page has a click, so no page owns the query.

Who ranks (organic top 3, 3 Oct 2026):
1. apexlifefitness.com, published a day before the pull. It already leads with "a number you cannot look up… above your own last thirty days". It is the real competitor for the baseline framing, but it gives no confidence and no competing explanations.
2. trainerroad.com, a forum thread from 2018.
3. cloudpbx.cazenovia.edu, a thin page on a university subdomain.

What the top three miss: a clear first-line answer from a source people trust, any sense of how sure an HRV reading is, and why a single low night has more than one explanation.

Other SERP features:
- **AI Overview.** It is present and opens with "not a single universal number, but rather a personal baseline". Then it quotes age-band ranges in ms and says lower numbers "signal stress, fatigue, or illness". It cites WHOOP, Oura, BodySpec, Polar, Different Health and Northwell.
- **Forums.** Forum results take organic positions 2 and 4 (TrainerRoad and a Facebook Garmin thread). A Perspectives block shows a Garmin forum post ("Genuinely curious what is normal") and an r/cfs thread. People are still asking each other, so the existing answers don't satisfy them. That is the opening.
- **Video.** There is a video pack.

Page type: explainer. The answer comes in the first 53 words with no product. The numeric PAA questions get their own section.

Title (55 characters): What Is a Good HRV? Why Your Own Baseline Beats a Chart
Meta (155 characters): There's no single good HRV number. Learn why HRV varies so much between people, why an age chart can mislead, and how to read yours against your own range.
H1: What is a good HRV?
URL: `/learn/what-is-a-good-hrv/`

## Answer first (40 to 60 words)

There is no single good HRV number. HRV varies widely between healthy people, falls with age, and is calculated differently by different devices, so a chart cannot tell you whether yours is good. The useful question is whether your number sits inside your own usual range, measured the same way, over several weeks.

(53 words. No product, no range, no threshold. This paragraph is the AI Overview candidate.)

## Outline

**H2 1. What is a good HRV?**
- The answer-first paragraph above.
- One plain line on what HRV is: the small variation in time between heartbeats, in milliseconds. Link to the existing explainer for the full definition.

**H2 2. Why is there no single "good" HRV number?**
- The spread between healthy people is very large. A systematic review of 44 studies and 21,438 healthy adults found large differences between individuals, and values that depended on how the data was recorded and cleaned (Nunan 2010).
- Published norms depend on recording length, age and sex. 24-hour, 5-minute and shorter readings are not interchangeable (Shaffer and Ginsberg 2017).
- Devices use different metrics. Apple Health stores HRV as SDNN (HealthKit `heartRateVariabilitySDNN`), while many rings and bands report RMSSD overnight. A number from one device can't be read against a chart built from another.
- Devices also differ in how closely they match a lab reference at night (Dial 2025, five wearables). Compare yourself with yourself, on the same device.

**H2 3. What is a good HRV for my age?** (PAA; "hrv by age" 8,100)
- On average, HRV tends to be lower in older age groups, and some measures differ between women and men (Voss 2015, 1,906 healthy adults).
- An age chart tells you where a group sits, not whether your number is good for you. The ranges in search results come from different devices, metrics and recording windows.
- **No numeric age table on this page.** That is a deliberate break from the AI Overview and a skill rule. Instead, show one simple illustration: two people of the same age, each steady in a different range, and both normal for themselves. Label it "illustration, not data".

**H2 4. Is 37 a low HRV? Is 22 or 43 ms bad?** (three PAA questions in one section)
- A single number means little without your own baseline. The same 37 ms can sit in the middle of one person's usual range and at the bottom of another's.
- What to compare instead:
  - today against your own last few weeks;
  - on the same device and the same metric;
  - at the same time of day, ideally overnight or first thing in the morning (Plews 2013 recommends a consistent daily measurement time).
- Weekly averaging is more useful than any single day (Plews 2013, on using averaged HRV to read training status in athletes).
- **Never give a cut-off or say a number is "low" or "bad" in absolute terms.**

**H2 5. Why is my HRV low today?** (590)
- HRV is sensitive, not specific. In about 9 million measurements from 28,175 people, HRV and resting heart rate shifted with training, alcohol, menstrual-cycle phase and being unwell (Altini and Plews 2021).
- So a dip usually has more than one possible explanation. Show them side by side (a short night, a hard session, a late drink, travel) instead of naming one cause.
- Use "associated with" wording throughout. Never say that X caused your drop.

**H2 6. What is a good HRV while sleeping?** (880)
- Many wearables report a nighttime figure, so readings are taken under similar conditions each night (Dial 2025 compared nocturnal readings). The comparison is still with your own nights, not with other people's.
- Link to the device-agreement point in H2 2 (Dial 2025).

**H2 7. What do cardiologists say about HRV, and is there an "unsafe" HRV?** (two PAA questions)
- That is a population finding. It is not a way to read one person's number.
- A wearable's HRV is not a diagnostic test, and there is no safe or unsafe cut-off to read from it.
- If you have symptoms that worry you, such as chest pain, fainting or shortness of breath, talk to a clinician rather than a wearable app.

**H2 8. How to read your own HRV**
- Measure the same way every time.
- Give it a few weeks to learn your range.
- Look at the weekly trend before the daily number.
- When it moves, list what else changed, and treat each one as a possible explanation, not the cause.
- This section hands off to the one Vybe section.

## The Vybe angle (one section)

**H2: What an answer about your HRV should tell you**

A number alone can't tell you how sure it is or what it missed. Vybe is designed to answer in a plain sentence. Each answer is designed to state its confidence in words, with a reason you can count (Register row 14). It is designed to say what Vybe could not see (row 15). And it is designed to name the explanations that fit instead of one culprit (row 19). It is designed to read all of this against your own baseline, not a population average (row 9), across five connected signals (row 3).

Show one answer, labelled **"prototype, sample data"**:

> "Your HRV has been below your usual range for three nights. Moderate confidence: three nights since the change, and one night with a gap in the reading. Two later bedtimes fit best; Sunday's long run and Monday's flight fit too. What Vybe could not see: anything you drank, how you feel today. One next step: keep tonight's bedtime close to your usual one and check again tomorrow."

Rules for this section:
- Every sentence that asserts rows 14, 15 or 19 keeps "designed to". Vybe is pre-launch, so nothing in this section says Vybe *does* something in the present tense.
- One proof point, as hygiene, after the unclaimed idea and never before it: no required subscription (row 2).
- Do not quote the prototype's "4 of 7" self-grading tally anywhere.
- No accuracy claim for the band. No "ECG". No "heart rhythm". The words are "HRV and heart rate" only.

## Proof and sources

Health statements were checked on PubMed and Apple's developer documentation on 3 Oct 2026. Use each source at the strength stated here and no further.

| Statement on the page | Source | Does not support |
|---|---|---|
| Large differences between healthy individuals; values depend on method and editing | Nunan, Sandercock and Brodie, *Pacing Clin Electrophysiol* 2010, systematic review of 44 studies, 21,438 adults. [doi:10.1111/j.1540-8159.2010.02841.x](https://doi.org/10.1111/j.1540-8159.2010.02841.x) | Any "good" range for one person, or any risk reading of one person's number |
| Norms depend on recording length, age and sex, and are not interchangeable | Shaffer and Ginsberg, *Front Public Health* 2017. [doi:10.3389/fpubh.2017.00258](https://doi.org/10.3389/fpubh.2017.00258) | A table of norms to publish |
| HRV indices change with age, and some differ by sex | Voss et al., *PLoS One* 2015, 1,906 healthy adults (KORA S4). [doi:10.1371/journal.pone.0118308](https://doi.org/10.1371/journal.pone.0118308) | Wearable ms ranges by age |
| HRV and resting HR shift with training, alcohol, cycle phase and sickness; sensitive, not specific | Altini and Plews, *Sensors* 2021, about 9 million measurements from 28,175 people (already in the brand-brief evidence library). [doi:10.3390/s21237932](https://doi.org/10.3390/s21237932) | Any single cause for a reader's dip |
| Averaged, longitudinal HRV is more useful than single readings; each athlete has an individual pattern | Plews et al., *Sports Med* 2013. [doi:10.1007/s40279-013-0071-8](https://doi.org/10.1007/s40279-013-0071-8) | Claims about non-athletes beyond the general principle |
| Wearables differ in how well nocturnal HRV agrees with a lab reference recording | Dial et al., *Physiol Rep* 2025, five devices, 13 adults, 536 nights. [doi:10.14814/phy2.70527](https://doi.org/10.14814/phy2.70527) | Any accuracy figure for the Vybe band, which was not tested. Do not quote competitors' error rates on this page. |
| Apple Health stores HRV as SDNN | Apple developer documentation, `HKQuantityTypeIdentifier.heartRateVariabilitySDNN` ([developer.apple.com](https://developer.apple.com/documentation/healthkit/hkquantitytypeidentifier/heartratevariabilitysdnn)) | Any statement about the accuracy of Apple's HRV |

## Call to action

One call to action: **Join the waitlist.** The supporting line is exactly as the site words it: "The first 1,000 on the waitlist are guaranteed a position to buy a band." (Register row 11.)

## Schema and AI search

- Use `Article` schema, plus `FAQPage` for the six PAA H2s. Each FAQ answer is the first two sentences of its section.
- Google limits FAQ rich results to a small set of authoritative sites, so FAQPage is there to make the page easy for machines to read, not to win a rich result.
- The 53-word answer-first paragraph is the AI Overview and assistant candidate. It already matches the AI Overview's opening idea (a personal baseline, not one number) and adds why: spread, age and device.
- Keep the page under 20K tokens.
- Allow GPTBot, ClaudeBot, PerplexityBot and Google-Extended in `robots.txt`.
- Add the page to `llms.txt` under /learn.
- Internal links:
  - from `/learn/heart-rate-variability-explained/` with the anchor "what is a good HRV";
  - from this page to `/learn/whoop-recovery-score-meaning/`;
  - to a later "how to improve HRV" page once it exists.

## Measure

- **Current position.** None for "what is a good hrv": no impressions, 3 Jul to 1 Oct 2026. The related explainer averages position 85.5 on definition queries.
- **Targets.**
  - At the 8-week review: impressions on the "good hrv" cluster, and an average position of 30 or better for the target query.
  - Later goal: top 10 (the seo-plan definition of a working page), with Organic Search `waitlist_signup` attributed to the page in GA4.
- **Review date.** 8 weeks after publishing. Record the publish date on the scoreboard.
- **Decision rules.**
  - If impressions rise but the click rate stays under 1%, rewrite the title and meta.
  - If there are no impressions at 8 weeks, run URL inspection, then check internal links and indexing before touching the copy.
  - If the old explainer starts taking "good hrv" impressions away from this page, keep the page with more clicks and redirect or narrow the other.
  - If the page earns clicks but no waitlist signups after 8 weeks, test the Vybe section's position before changing the CTA.

## Concept check

1. **Audience and channel.**
   - Who and where: end users asking a question, on a search page.
   - The lead: the direct answer to "what is a good hrv".
   - The "then" line, carried: calibrated answers in the one Vybe section, then the waitlist.
2. **Swap test.** The hook is the searcher's own question, and the baseline answer is hygiene that apexlifefitness and the AI Overview also give. The Vybe section passes the test: no competitor claims an answer designed to state its confidence with a countable reason and to name what it could not see.
3. **Show it.** One answer is shown, labelled "prototype, sample data". It has a sentence, its confidence with a countable reason, one blind spot, three ranked explanations and one next step.
4. **Order.** The page answers first by the skill's explainer rule. Inside the Vybe section, the calibrated answer comes first and the baseline and no-required-subscription come second, as proof.
5. **Two products.** This piece sells the band's thinking to end users. The platform half has to come from the same week's builder piece (LinkedIn or /developers). The page keeps one CTA, so it does not add a builder link.
6. **Claims.**
   - Product claims: rows 14, 15 and 19 say "designed to" in every sentence. Rows 9 and 3 are approved product facts. Row 11 matches the site exactly. Row 2 uses the "no required subscription" wording.
   - Health statements: each one cites a source at the "observed" or "associated" population level.
   - The example answer gives three explanations, all everyday ones, and none is an illness.
7. **Roadmap and offers.** Nothing relies on an unreleased feature or an unconfirmed spec. The page has no battery figure, no "validated", no ECG, no ring and no accuracy figure. It makes no builder offer.
8. **Voice.** The copy is plain and declarative. It has one action. It says "a chart cannot tell you" and "there is no cut-off" instead of hedging. It has no hype, no "let's dive in" and no rhetorical triplets in the copy.

## Notes on the skill (3 lines)

1. The "Current priorities" row says Vybe's HRV page "holds 62 of its 68 impressions" for "what is a good hrv". Live Search Console shows 63 page impressions, all on definition queries, and zero for any "good hrv" query. So the "improve that page" rule in step 3 would have sent this brief to the wrong page. The row should name the queries.
2. "Rising about 30%" can't be checked with the endpoints the skill lists. The Google Ads 12-month series has no same-month-a-year-apart point, and Trends is listed but costs extra calls. The skill should say which pull backs each trend figure.
3. Missing: how to answer the large "hrv by age" demand (8,100) and the AI Overview's age tables without quoting a population range. Also missing: whether FAQPage is still worth adding now that Google limits FAQ rich results, and whether the new page or the existing explainer gets the brief when the question has no impressions anywhere.
