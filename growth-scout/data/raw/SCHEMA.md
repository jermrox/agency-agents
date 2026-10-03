Each research lane writes a JSON array to growth-scout/data/raw/<lane>.json. One object per target:

{
  "name": "Person or organization name exactly as on the source",
  "org": "Firm/company (or same as name)",
  "role": "Partner / Founder / Angel / Editor / null",
  "type": "vc | angel | angel-group | syndicate | accelerator | corporate-vc | builder | research-lab | amplifier | community | event | listing | signal",
  "hunt": "investor | growth | social",
  "why": "One or two sentences: the public evidence that makes them fit Vybe Health (cite the deal, post, thesis, thread)",
  "why_now": "The dated, recent trigger (deal date, post date, event date, deadline) or null",
  "evidence": ["https://... the URLs you actually opened that prove the claim (min 1)"],
  "channel": "How to reach them publicly: 'LinkedIn', 'X', 'Instagram DM', 'contact form', 'pitch form', 'apply', 'email listed on site', 'warm intro needed'",
  "contact_url": "Public URL for that channel (their profile / pitch form / contact page) or null. NEVER a guessed email.",
  "warm_path": "Shared network angle if visible (veteran network, Ohio, accelerator, university) or null",
  "fit": 1-10 integer per the rubric,
  "ice": {"i":1-10,"c":1-10,"e":1-10} or null (required for hunt=growth),
  "ask": "One small specific ask (15-min call, listing, feedback, intro, application)",
  "opener": "Draft first message under 80 words, founder voice, no hype, no health claims, investors: ask for a conversation, never mention terms/valuation",
  "check_size": "As stated by a source, else null",
  "stage": "pre-seed/seed/A etc as stated, else null",
  "geo": "City/region or null",
  "deadline": "YYYY-MM-DD if an application/event deadline exists, else null",
  "last_signal_date": "YYYY-MM-DD of the most recent dated evidence, else null",
  "confidence": "verified (2+ sources or primary source) | single-source",
  "tags": ["wearables","health-hardware","digital-health","ohio","veteran","women-founders","tactical","dev-platform","sleep","hrv", ...]
}

Fit rubric:
- Investor 9-10: invested in wearables/health hardware in last 24 months AND writes pre-seed/seed. 7-8: digital health / hardware / dev-platform thesis, or founder-identity network Vybe qualifies for (veteran, woman, minority-owned, Ohio). <7: drop.
- Builder 9-10: building a wearable-health product blocked on hardware or data access (e.g. hurt by Fitbit Web API / Google Fit sunsets). 7-8: lab/tactical/performance/health org with defined wearable use case.
- Amplifier 9-10: audience is exactly wearables/HRV/sleep/quantified-self/HYROX/tactical and reviews gear honestly.
Only include fit >= 7.

Hard rules: never invent a person, URL, email, number or date. Every row needs evidence URLs you fetched. Public professional info only. Skip unrelated "Vybe" companies. Vybe Health = vybe.health, Akron OH, pre-launch developer platform for wearable health (screenless ECG/HRV band, licensed SDK/API, DevKit v0.1 for 5-10 design partners, consumer launch May 2027), veteran/woman/minority-owned, no subscription, general wellness (no medical claims).

SPONSORSHIP LANES (added): hunt = "sponsorship". Extra types:
- "competitor-deal": what a competing wearable brand sponsors (WHOOP, Oura, Garmin, Polar, Ultrahuman, Coros, Apple, Samsung, Amazfit, Hume...). name = "<Brand> x <Partner>", org = brand, why = the deal and what it tells Vybe, fit = how much Vybe can learn/copy at small scale.
- "athlete": an individual athlete/coach who could wear/represent Vybe. Prefer micro/mid athletes (HYROX, CrossFit, ultra/trail, tactical/military athletes, Paralympians, women's sports, college NIL, Ohio-based) who are NOT locked into a competing wearable deal (if they are, say so and lower fit). Follower counts only if shown on a source, with date.
- "team": a club/college/minor-league/semi-pro/esports team open to small sponsors (Ohio first: Akron, Cleveland, Columbus, Kent State, Akron Zips, minor league, HYROX gyms, run clubs).
- "event": races/competitions with entry-level sponsor or vendor packages (HYROX events, marathons/half marathons in Ohio, Spartan, tactical/fire-fighter competitions, collegiate, veterans games) — include deadline/date and package price only if published.
- "program": sponsorship marketplaces/NIL platforms/ambassador networks (e.g. Opendorse, SponsorUnited insights, athlete ambassador platforms) and in-kind/product-seeding routes.
ask = the small entry move (seed 5 bands, $X vendor booth if published, recovery-data content collab, ambassador). opener as usual (no health claims, no outcome promises).

PARTNERSHIP LANES (added 2026-10-03): hunt = "partnership". Rule: prove the opportunity, never assume it.

type "app-partner" (a health/fitness app Vybe could integrate with or co-market with). Extra fields, all required:
- "existing_wearables": ["Garmin", "Apple Health", ...] exactly as the app's own integrations page / docs / changelog lists them; [] only if you confirmed it has none; null if you could not find out.
- "exclusive": true if a source shows an exclusive or owned hardware relationship (e.g. the app is a wearable brand's own app, or a stated exclusive deal); false if it integrates with several brands or via an aggregator (Terra, Junction, Rook, Thryve, HealthKit/Health Connect); null if unknown.
- "partner_status": "open" (multi-device or asks for integrations / has a partner page), "competitor" (makes its own wearable — fit <= 6 unless co-op angle is real), "exclusive" (fit <= 6), "no-wearable-yet" (no device integration at all; opportunity = be its first), or "unknown".
- "opportunity": the concrete collaboration (e.g. "add Vybe as a data source via their Terra integration", "co-market recovery feature to their runners", "be the first wearable in their app"), grounded in what you found.
- "unknowns": what you could not verify (e.g. "no public partner contact", "pricing of API unknown").
Do NOT write that an app "has no partnership" unless you checked its integrations/partners page or docs; say "unknown" instead.

type "sport" (a sport or competition level where wearables are rare, banned in competition, or unserved). Extra fields:
- "wearable_adoption": what a source says about current wearable use (survey, governing-body rule, article), with the claim's date.
- "competition_rule": the governing body's rule on wearables during competition if one exists, else null. Vybe's band is worn overnight, so an in-competition ban does not block an overnight recovery use; say so only when the rule is about competition.
- "opportunity": the concrete first move (club pilot, federation partnership, coach community), plus named clubs/federations/athletes when found.
- "unknowns".
Athletes found in these sports use type "athlete" (hunt "sponsorship") and must say whether a source shows them using any wearable (and which) or "no wearable found in public posts".
