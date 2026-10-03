# Vybe Health — Brand Brief v1 (30 Sep 2026)

Messaging House and Claim Register, built from the live site (read through
Firecrawl on 30 Sep 2026: home, `/band`, `/ecosystem`) and the Instagram
account. Claims are listed at the support level the evidence allows. The
founder approves anything marked "founder to confirm" before it is reused.

## Messaging House

**Roof.** We build the wearable. They build what's possible with it.

**Public one-liner (site title).** Private, Screenless Health Intelligence.

**Site headline.** "No Subscription." then "Five connected signals,
interpreted around your own changing baseline. Buy the device. Own the
experience."

| Pillar | For end users | For builders | Proof on the site today |
|---|---|---|---|
| Your own baseline | "Read against your own changing baseline", not a population norm | Behavioural baselines are a licensable model | Home, `/ecosystem`, Vitals and Move factor copy |
| Five factors, one signal | Nourish, Vitals, Connect, Move, Restore "fold into one living picture of you" | Five Factor interpretation and Lifestyle Architecture can be licensed without Vybe hardware | `/ecosystem` "Five signals. One quiet system." |
| Own your data | "Your signals stay yours. Nothing sold and nothing shared." No required consumer subscription | Consented access only; "never selling user data" | Home privacy block, `/learn/health-data-privacy-ownership` |
| Screenless, calm | "Built to be forgotten." "The Band senses. Vybe understands." | A quiet sensing layer other apps can sit on | `/band` |

**Platform story (from `/ecosystem`).** Eight ways in: Hardware; Enterprise
and Teams; Developer API (usage-based); Vybe Intelligence (license the
interpretation layer, no hardware required); Research Infrastructure;
Algorithm Licensing; OEM / Embedded Vybe; Strategic Partnerships.

**Five factors, as the site words them.**
- Restore: sleep stages and timing, read across weeks
- Move: training load, weighed against your own norm
- Nourish: food, timing and hydration, in plain language
- Connect: time with people, alone and outside
- Vitals: heart rhythm and HRV against your baseline (site wording as read; counsel to review, see rows 5 and 5a)

**The offer right now.** Pre-launch. The call to action is "just vybe", which
leads to the waitlist. "The first 1,000 on the waitlist are guaranteed a
position to buy a band." The waitlist form also captures partnership,
creator, affiliate and sponsorship interest, what the visitor wears now
(Apple Watch, WHOOP, Oura, Garmin, Fitbit, none, other) and what they most
want to understand (sleep, recovery, stress, training, food and energy, the
whole picture).

**Words we use.** Vybe Health, Vybe, the band, baseline, five factors, own
your data, screenless, no required subscription, private intelligence,
build on it.

**Words we avoid.** Vybe Band as a brand name, medical, clinical-grade,
diagnose, treat, cure, "accurate" without a basis, "best", any price
comparison, any competitor mockery.

## Claim Register v1

Ladder: **observed** (a product fact or spec) → **associated** → **personally
supported** → **hypothesis**. Health and science claims need a source.

| # | Claim (as published) | Where | Ladder / type | Support | Status |
|---|---|---|---|---|---|
| 1 | Screenless band | Site, IG | Product fact | Design intent on `/band` | Approved |
| 2 | No required consumer subscription | Site | Product / pricing fact | Site copy, repeated | Approved. Note the site says "required consumer subscription"; IG says "No Subscription". Keep the site's wording where space allows. |
| 3 | Five connected signals read against your own baseline | Site | Product fact | Site copy | Approved |
| 4 | Health data never sold, nothing shared without consent | Site | Privacy promise | Site copy; must match the data screen and privacy policy | Approved. Counsel to confirm the privacy policy matches before paid use. |
| 5 | ECG, HRV and heart rhythm in one continuous record | `/ecosystem` Vitals | Product spec | Site copy | **Counsel to review.** WHOOP holds an FDA 510(k) clearance for its ECG feature (K243236, Class II, cleared 4 Apr 2025, per the openFDA database). Vybe has no clearance, so "ECG" on a Vybe page must never read as a clinical or diagnostic ECG. Founder to confirm "continuous" is the shipped behaviour. |
| 5a | "Heart rhythm and HRV against your baseline" | Home, Vitals factor | Product capability | Site copy | **Counsel to review before any ad use.** Per the 2 Oct 2026 targeting research, heart-rhythm and AFib-adjacent wording is the highest regulatory risk across FDA wellness guidance, Google's Health category and Meta's health classification. FDA sent WHOOP a warning letter in July 2025 over a blood-pressure feature. Use "HRV" and "heart rate" in ads until cleared. |
| 6 | Sleep stages, efficiency and recovery, read across every night | `/ecosystem` Restore | Product spec, estimate | Wrist-based sleep staging is an estimate | Approved only with "estimated" where stages are named in long copy or ads |
| 7 | 30 days of battery | IG post, 25 Sep | Product spec | Not on the site | Founder to confirm before reuse |
| 8 | "Validated proprietary models for sleep, recovery, HRV, readiness, and behavioral baselines" | `/ecosystem` Algorithm Licensing | Validation claim | No study or method cited on the site | Founder to confirm what "validated" rests on. Until then, do not repeat in ads or press. |
| 9 | Personal baseline instead of a population average | Site | Product fact | Site copy | Approved |
| 10 | "See what is affecting you": signals read next to life context (travel, deadlines, late dinner) | Home | Product capability, associative | Calendar and timing integration described in `vybe-app/README.md` | Approved as capability language; never as a causal claim about a specific reader |
| 11 | First 1,000 on the waitlist are guaranteed a position to buy | Home | Offer term | Site copy | Approved. Any ad using it must match the site exactly. **Re-verify before use (3 Oct 2026):** a read of the site did not return this line, and the waitlist page says applications are "evaluated on eligibility". |
| 12 | "Own your personalized SDK and Application" | IG bio | Platform claim | Unclear what a consumer "owns" | Founder to rewrite; suggested: "Build on it: SDK and API for teams" |
| 13 | Not a medical device; no diagnosis | Implicit | Regulatory posture | Funding notes, product rule | Standing rule. Add a plain line to `/faq` if not already there. |
| 14 | Answers in a plain sentence, with its confidence stated in words and the reason for it | Not public yet | Design commitment | `vybe-app/README.md` (Restore, Ask screens) | **Founder to approve for public copy.** Until it ships, write "built to" or "designed to". This is the lead claim; see `concept.md`. |
| 15 | Every answer shows what Vybe could not see | Not public yet | Design commitment | `vybe-app/README.md` (Ask screen) | Founder to approve. Same "designed to" rule as row 14. |
| 16 | Vybe checks whether its own suggestions worked, and shows the ones it got wrong | Not public yet | Design commitment | `vybe-app/README.md` (Outcome screen) | Founder to approve. Same "designed to" rule. Never quote the prototype's sample tally ("4 of 7") as a result. |
| 17 | Nothing is on by default; export takes one tap, and delete asks twice before it acts | Not public yet | Design commitment, privacy | `vybe-app/README.md` (Onboarding, Data screens) | Founder to approve, and counsel to check against the privacy policy before paid use. |
| 18 | Built open: others can build on the band | IG, 29 Sep; site `/developers` | Platform direction | The public FAQ dates API v1 to Jun 2028 and the SDK to Dec 2028 | Approved as a direction ("built open", "talk to us", "design partners"). Never "available now". |
| 19 | Shows patterns, not causes: names the explanations that fit instead of one culprit | Not public yet | Design commitment | `vybe-app/README.md` (Pattern history screen); evidence library on HRV | Founder to approve. Same "designed to" rule as row 14. Explanations stay everyday ones (sleep, training, timing), never an illness. |
| 20 | No GPS; Bluetooth-only pairing | `/hardware` lists Bluetooth-first and no GPS sensor | Product spec | Site hardware table; matters to tactical buyers (DoD geolocation rules) | **Founder to confirm** there is no GPS in the band at launch before any tactical copy uses it. |
| 21 | "The answers come with the band" | Not public yet | Pricing scope, derived from row 2 | Competitors charging for AI coaches (research, 3 Oct 2026) | **Founder to confirm** it holds against any future paid feature. Until then, never use it alone: join it to calibration and carry "no required subscription" in the same piece. |

**Claims never to make.** Any diagnosis or treatment; "clinical-grade" or
"medical-grade"; any accuracy percentage without a cited method; any
cause-and-effect statement about a reader's own body; any comparison on price
or battery against a named competitor; any partnership (HYROX, HYDROX, a
creator) before it is signed.

## Safe and unsafe claim shapes

From the founder's Activity Mode research (Sep 2026), which reads FDA's
January 2026 General Wellness guidance. Counsel to confirm before paid use.

**Inside wellness:** "Track heart rate, breathing rate, workout intensity and
recovery during exercise." "Understand how your heart and breathing respond
to training." "See how your sleep compares with your own baseline."

**Outside wellness, never write:** detect, diagnose, identify, warn of or
monitor for any condition (for example respiratory distress, arrhythmia,
asthma, sleep apnea, cardiopulmonary disease). The same test applies to app
strings, push notifications and AI answers, not only to the website.

**Unreleased features.** The founder's research describes features and device
integrations that are not shipped. None of them appears in public copy, ads,
press or social until it ships and the founder approves the claim. This
includes any statement that another company's device works with Vybe.

**Data claims.** Consumer health data collected directly by Vybe is usually
outside HIPAA, but the FTC Act and the FTC Health Breach Notification Rule
still apply. Do not write "HIPAA-compliant" in consumer copy.

## Evidence library

Checked on PubMed on 1 Oct 2026. Use these for content and claims at the
support level stated; do not stretch them.

| Study | What it supports | What it does not support |
|---|---|---|
| Gardiner et al., *Sleep Med Rev* 2024, systematic review and meta-analysis of 27 studies. [doi:10.1016/j.smrv.2024.102030](https://doi.org/10.1016/j.smrv.2024.102030) | At the population level, alcohol delays REM onset and reduces REM duration, from about two standard drinks, worsening with dose. | That alcohol caused any one reader's bad night or HRV drop. |
| Altini & Plews, *Sensors* 2021, about 9 million measurements from 28,175 people. [doi:10.3390/s21237932](https://doi.org/10.3390/s21237932) | HRV and resting HR shift with training, alcohol, menstrual-cycle phase and sickness; HRV is sensitive but not specific. The basis for "show competing explanations". | Any single cause for a change in HRV. |
| Lee et al., *J Clin Sleep Med* 2025, meta-analysis of 24 studies of consumer wrist trackers against polysomnography. [doi:10.5664/jcsm.11460](https://doi.org/10.5664/jcsm.11460) | Wrist sleep trackers differ significantly from lab polysomnography on total sleep time, efficiency, latency and wake after sleep onset; useful for general patterns. | Any accuracy figure for the Vybe band, which was not in the study. |
| US Surgeon General advisory, *Our Epidemic of Loneliness and Isolation*, 3 May 2023 (checked 3 Oct 2026) | About half of US adults report loneliness. Poor social relationships go with 29% higher heart-disease risk and 32% higher stroke risk; isolation with about 50% higher dementia risk in older adults; early-death risk comparable to smoking "up to 15 cigarettes a day". | Anything about a Vybe user, or that Vybe reduces these risks. Keep "up to", and keep the comparison about early death. Never use it as a product claim. |
| WHO Commission on Social Connection report, 30 Jun 2025 | "Nearly one in six" people worldwide are lonely; about 871,000 deaths a year are attributed to loneliness (2014–2019, modelled). | A measured death count, or any claim that Vybe detects loneliness. |
| UK Biobank light-sensor cohorts (Burns 2023; Windred 2024, 2025), about 86,000–89,000 adults | Brighter days and darker nights go with better mental health and lower mortality (association). | Causation, or any Vybe light measurement until the band's light sensor is confirmed. |
| Martinez et al. 2022, 657 people | Wrist HRV explains only about 1–2% of day-to-day variation in perceived stress. | Any claim that Vybe detects stress or loneliness from HRV. |

Marco Altini, first author of the HRV study, is on the Reels program's
"baseline" follow list (@altini_marco); citing the work in a Reel and
crediting him is natural and honest.
