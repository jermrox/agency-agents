# Accelerator application drafts: a16z speedrun, Y Combinator, Techstars

Drafted 3 Oct 2026 for the founder. Everything below is built from facts the
project can source. Anything only the founder knows is marked **[FOUNDER: ...]**.
Nothing here has been sent or submitted.

## The plan, in date order

| When | Do this | Why |
|---|---|---|
| Now to Oct 11 | Fill every **[FOUNDER]** field below. Record a 1-minute founder video (speedrun and YC both want a face and a voice). | The drafts are 80% done; the rest is facts only you hold. |
| **Oct 13** | Veteran Shark Tank 2026 closes ($50K non-dilutive, on the funding board). Not in this file. | Closes before everything else here. |
| **Oct 12 to Nov 1** | Submit **a16z speedrun SR008** inside the priority window (reviewed fastest; applications are also accepted year-round). | Cohort starts early 2027. |
| **Nov 2, 8pm PT** | Submit **YC W27** (on-time applicants hear by Dec 11). | The batch is in person in San Francisco, Jan to Mar. |
| about Nov 11 | **SXSW Pitch 2027**, Life Sciences / Healthcare category ($225 entry per our research; one SXSW page says Nov 11, another Nov 13, so submit by the 11th). | Cheap investor exposure. |
| **Nov 18** | **Techstars Anywhere** (final deadline). Techstars AI Health (Baltimore) closes the same day. | Remote-first, three in-person offsites. |

If you only do one: speedrun. It is the only program where our research found a
direct wearable precedent: speedrun backed Clair Health's wrist wearable in
June 2026.

## Fit, honestly

| Program | What it offers | Where Vybe fits | Where it does not |
|---|---|---|---|
| **a16z speedrun SR008** | Up to $1M; $10M+ in partner credits; 1,000+ founder community. Contact: sr-team@a16z.com (published on its apply page). | Hardware plus platform story; precedent in Clair Health. Named contact from our research: Emily Bennett, Investment Partner. | Highly selective; they will want proof of speed and traction. |
| **Y Combinator W27** | Standard deal, about $500K (confirm current terms on ycombinator.com). Decision by Dec 11 if on time. | Dev-platform framing is YC-native. | The batch is in person in San Francisco for about three months. Needs a decision about relocating. |
| **Techstars Anywhere** | Remote-first; applications Aug 24 to Nov 18; starts Mar 8 2027; Demo Day Jun 3 2027; about $220K (confirm). | No relocation needed. | Its stated emphasis is robotics, energy, applied and physical AI and materials science. Wearables are a stretch; **Techstars AI Health (Baltimore)** may fit better, and the row on the board names a contact for a fit check. |

## Answers that work for all three

### One line
Vybe Health is the developer platform for wearable health: we build the
screenless band and the data platform, and other teams build what is possible
with it.

### What we do (about 50 words)
Vybe builds the hardware (a screenless band, later a ring), the engine
(firmware, signal processing, sensor fusion), a secure data platform and a
licensed SDK and API. Developers, researchers and tactical-performance teams
build applications on our data instead of becoming a hardware company. We keep
the IP; they get a socket, not the recipe.

### The problem
A good wearable-health idea usually forces a team to become a hardware company,
and the incumbents are closing their data:

- **Oura:** Gen3 ring users without an active membership can no longer reach
  their data through the Oura API, and neither can partner apps (Oura partner
  support, updated 26 Aug 2026).
- **WHOOP:** developer apps are capped at 10 members until WHOOP approves them.
  PlayersLab, RestOrTrain and Kygo Health have each posted publicly that their
  WHOOP integration is finished but stuck behind the cap, with approval requests
  open for weeks to months (WHOOP community forum, Jul to Aug 2026).
- **Fitbit:** the Web API turns off on 30 Oct 2026 and OAuth grants do not
  carry over, so every app must re-authorise on a new API (Sahha and Open
  Wearables migration guides).
- **Google Fit:** the APIs, including REST, are deprecated in 2026 with no REST
  replacement (Google's own migration FAQ).

Sources for each are in `growth-scout/data/targets.json` (search the names
above) so you can click through before you quote them.

### Why now
- The incumbents are tying data access to subscriptions or caps just as
  developers need it, and a major API is shutting off in four weeks.
- The category is large and being funded: Oura reported about $1.2B revenue in
  the nine months to June 2026 with about 5M paid members (public S-1, TechCrunch
  3 Sep 2026); WHOOP raised $575M at a $10.1B valuation (Mar 2026).
- The platform thesis is being validated by others: Ultrahuman raised $70M led
  by Qualcomm Ventures (Sep 2026) and says it will open its ring to third-party
  developers. Say this plainly: it also makes Ultrahuman a competitor for the
  same developers.
- FDA's revised General Wellness guidance (6 Jan 2026) puts non-invasive
  wearables that estimate HRV and similar signals for wellness use under
  enforcement discretion. Vybe stays inside it: no diagnosis, no treatment, no
  disease claims.

### What we have built
**[FOUNDER: be exact. Say what exists today: prototype band? firmware? the
app prototype in `vybe-app/`? Mark anything not shipped as "planned".]**
Facts the project can state today:
- Public site live at vybe.health with a founding-batch waitlist.
- Lifestyle Architecture prototype app (organised around the five factors:
  Vitals, Restore, Nourish, Move, Connect). Numbers in the prototype are
  sample data; do not present them as measurements.
- First milestone: Vybe DevKit v0.1 (device, SDK, docs, API) with 5 to 10
  external design partners. **Not yet delivered.**

### Traction
**[FOUNDER: only real numbers.]**
- Waitlist signups: [N] as of [date]
- Design-partner conversations held (not just targeted): [N]
- Letters of intent or pilots: [N]
- Revenue to date: [$] (company profile says under $75K; give the true figure)

> Do not count the board's targets as traction. They are people we have found,
> not people we have spoken to. Once you have actually spoken to one, it can
> count, with a date.

### Business model
Hardware sales; SDK and API licensing; enterprise and research deployments;
platform fees; marketplace share; data and analytics services; reference-design
licensing. No mandatory consumer subscription. Consumer launch planned for May
2027, then major retail (planned, not confirmed).

### Competition (be straight about it)
| | What they do | How Vybe differs |
|---|---|---|
| WHOOP, Oura | Subscription incumbents with closed or capped APIs | Open, licensed platform; no required consumer subscription |
| Fitbit Air ($99), Garmin Cirqa, Polar Loop, Amazfit, Hume | Screenless or low-price bands | "Screenless" and "no subscription" are no longer unique. Lead with personal baselines, the five factors read as one signal, owning your data, and the platform others build on |
| Ultrahuman | Opening its ring to third-party developers | Closest to our platform thesis; we are earlier and smaller |
| Aggregators (Terra, Junction, Thryve, Sahha) | One API over many wearables | They depend on other companies' hardware and permissions; we make the hardware. They are also potential channel partners |

### Why us
**[FOUNDER: your story, in your voice.]** Optional, **only with your approval**:
Vybe is veteran-owned, woman-owned and minority-owned and based in Akron, Ohio.
This is real and matters to these investors, but it is your story to tell, so it
is not in any draft until you say so.

### Milestones and use of funds
**[FOUNDER: the amount you are raising and the split.]** A frame that matches
the profile: place DevKit v0.1 with 5 to 10 design partners; reach "10
organisations say they could not build their product without Vybe"; ship the
founding batch; consumer launch May 2027.

### Risks to name before they ask
- Hardware execution (manufacturing, battery, validation).
- Regulatory posture: wellness only, not a medical device. Heart-rhythm and ECG
  wording should be reviewed by counsel before it goes anywhere public, because
  WHOOP holds an FDA clearance for its ECG feature and the lines matter.
- Crowded claims, and incumbents with large budgets.

## Program-specific notes

**a16z speedrun.** Apply Oct 12 to Nov 1. Their pitch is speed, so lead with
what you shipped fastest and the dated Fitbit shutdown. Once the application is
in, a short note to Emily Bennett (her row on the board has a drafted opener)
mentioning the application and the Clair Health precedent is reasonable.

**Y Combinator W27.** Apply by Nov 2, 8pm PT. YC wants the plainest possible
description, what people want, and what you built. Decide on San Francisco
before you apply. If you cannot relocate for the batch, YC's Early Decision for
later batches is the alternative; read it on their site.

**Techstars Anywhere.** Apply by Nov 18. Frame the band as applied and physical
AI (sensing plus interpretation) to match their stated emphasis. Ask for the
fit call with the managing director first; if it does not fit, apply to
Techstars AI Health (Baltimore) instead.

## Before you submit anything

1. Fill every **[FOUNDER]** field and delete these notes.
2. Re-read each program's live form; questions change between cycles.
3. Check every number against its source link (they are in the targets data).
4. Counsel read of the ECG / heart-rhythm wording and the privacy promises.
