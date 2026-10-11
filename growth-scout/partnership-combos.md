# Partnership combos for Vybe Health

Drafted 3 Oct 2026. A "combo" is two or three partners from the board whose
facts fit together into one joint offer. Every combo below is an **idea**, built
from facts already sourced in `data/targets.json` (search the names in bold to
see each row's evidence). Nothing here has been agreed with anyone, and no
integration with Vybe exists yet, so none of this may be described to a
partner as existing.

Vybe's side of every combo: a screenless band worn overnight (ECG and HRV), the
licensed SDK and API, and DevKit v0.1 for 5 to 10 design partners. Wellness
framing only.

## 1. Training that reads last night: Fitbod, Tredict, AI Endurance
- **Fitbod** builds workouts around a per-muscle recovery score that its own
  help center calls "an estimate, not a measurement".
- **Tredict** already syncs nightly HRV and sleep from Oura, Garmin, Coros,
  Suunto and Polar, and has a public API for receiving health data.
- **AI Endurance** takes overnight data directly from six brands only; anything
  else goes through Intervals.icu or manual entry.
- **The offer (idea):** Vybe as the overnight source behind strength (Fitbod) and
  endurance (Tredict, AI Endurance) training, so a poor night changes the plan.
- **First move:** Tredict's API application page, then the named contacts on each
  row (Felix Gertz at Tredict, Markus Rummel at AI Endurance, Jesse Padilla at
  Fitbod).
- **Not yet known:** whether Fitbod reads sleep or HRV from Apple Health today;
  whether these three share users.

## 2. Sleep next to food: MyFitnessPal, Alma
- **MyFitnessPal's** published device-partner list (updated May 2026) has Fitbit,
  Garmin, Withings, Polar, Samsung Health, Health Connect and Apple Watch, with
  **no overnight HRV or sleep band**. Its developer API is open to approved
  devices.
- **Alma** reads Garmin, Oura and WHOOP through Apple Health and says it brings
  food, movement and sleep together.
- **The offer (idea):** the Nourish and Restore factors together: last night's
  rest beside today's food log.
- **First move:** the MyFitnessPal API application (Kate Maxwell, VP Partnerships,
  is the named contact); a LinkedIn note to Rami Alhamad at Alma.
- **Not yet known:** MyFitnessPal's published API data types do not mention sleep
  or HRV.

## 3. Akron community: Akron Marathon, Endorphins Running, local gyms
- **Akron Marathon Race Series 2027:** the 2026 brochure listed a $700 expo
  booth, or a $500 official sponsor tier plus a $75 mile marker (2027 terms not
  published; the 2026 commitment deadline was May 31).
- **Endorphins Running** syncs WHOOP, Oura, Garmin, Apple Health, COROS, Polar and
  Suunto and claims 100,000+ runners and 1,500+ group runs a year in 12+ cities.
- **REACH Fitness** and **T3 Performance** are Ohio HYROX training clubs.
- **The offer (idea):** a "founding club": bands for one club's leaders, a
  recovery booth at the race, and a feedback night at the gyms.
- **Not yet known:** whether Endorphins Running has any Akron presence; 2027 booth
  pricing.

## 4. First responders: Neurovus, Firefighter Challenge, Akron Fire
- **Neurovus** is a first-responder recovery platform that reads HRV drift from
  wearables people already own; fire-department pilot applications were open and
  the pilot cohort starts in Q1 2027.
- **Hunter Brancifort** (Akron Fire, 2026 regional champion) and the
  **Firefighter Challenge League** (which asks for donated prizes and swag).
- **A survey** of 24 fire stations found 53% of firefighters do not wear
  wearables, citing cost and devices breaking under bunker gear. A band worn
  overnight at home avoids the gear problem.
- **The offer (idea):** Vybe as the overnight sensor in a Neurovus fire-department
  pilot, with Akron Fire competitors as the first cohort.
- **Needs:** department approval; confirmation that Neurovus takes new devices.

## 5. Tactical research bench: Ohio State, AFRL, INVI
- **Human Performance Collaborative (Ohio State)** published an ECG-referenced
  validation of nightly heart rate and HRV across Garmin, Oura, Polar and WHOOP.
- **STRONG Lab, 711th Human Performance Wing (Wright-Patterson)** exists to
  validate and transition wearables with commercial partners.
- **INVI MindHealth** is a device-agnostic resilience platform for veterans.
- **The offer (idea):** run DevKits through Ohio State's validation protocol; a
  result there is the credential for the AFRL conversation.
- **Not yet known:** willingness to include a new device; the AFRL route is through
  Ohio State's co-authors.

## 6. Developer plumbing: Open Wearables, freddy, the builders stuck on WHOOP
- **Open Wearables** (open-source wearable data API) lists direct Bluetooth
  connections on its roadmap, so Vybe could offer to write its own adapter.
- **freddy** connects 29 sources and invites requests for new ones.
- **PlayersLab, RestOrTrain and Kygo Health** have each posted publicly that a
  finished WHOOP integration is stuck behind WHOOP's 10-member developer cap.
- **The offer (idea):** be listed once as a source and reach many apps; give the
  stuck builders a DevKit with no cap.
- **Timing:** Fitbit's Web API turns off on 30 Oct 2026.

## What to do first (a week)
1. Tredict API application and a note to Fitbod's partnerships lead (combo 1).
2. MyFitnessPal API application (combo 2).
3. Offers to the three WHOOP-capped builders (combo 6).
4. Neurovus and Akron Fire (combo 4).
5. Akron Marathon expo terms for 2027 (combo 3).
