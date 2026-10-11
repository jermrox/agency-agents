# Developer-Platform (SDK/API) Marketing for Health and Wearable Data — Fact Base for Vybe Health SDK

Research note: several primary vendor pages (tryterra.co, sahha.ai, openwearables.io, themomentum.ai, developer.garmin.com, pmc.ncbi.nlm.nih.gov) were blocked by the network proxy, so some figures come from search-result snippets of those pages rather than full-page reads. Where a figure is from a competitor's comparison page (e.g., Sahha's "Terra alternatives"), treat it as a competitor claim and re-verify on the vendor's own pricing page before publishing.

## 1. How platforms position and price (Terra, Oura, WHOOP, Polar, Garmin, Google, Apple, Samsung, Sahha, Thryve, Rook, Junction)

### Takeaway
The market splits into (a) device makers whose APIs are free but gated behind hardware/membership or partner approval (WHOOP, Oura, Garmin, Polar, Samsung), (b) OS-level on-device stores (Apple HealthKit, Google Health Connect), and (c) paid aggregators that sell "one API for hundreds of devices" at roughly $300-$500/month entry points with free sandboxes (Terra, Sahha, Junction, Rook, Thryve). A free, self-serve developer entry point with published pricing is now the norm among aggregators; device makers compete on data depth and approval-based partnerships.

### Cited Findings
**Aggregators**
- Terra: subscriptions start at $399/month billed annually or $499/month billed monthly, including 100,000 credits/month; overages $0.005/credit up to 1M, $0.003 beyond; Streaming API and Planned Workouts are separately priced add-ons — [Terra pricing](https://tryterra.co/pricing); [Terra docs pricing](https://docs.tryterra.co/unified-api/pricing) (figures via search snippet; page blocked for full fetch)
- Terra markets coverage of "500+ wearables" and was positioned at seed stage as "the Plaid for fitness data" — [Terra homepage](https://tryterra.co/); [TechCrunch](https://techcrunch.com/?p=2163685)
- Competitor-claimed Terra effective cost: ~200 credits per active user per month, i.e. ~$4,800/yr at 500 users, ~$10,800/yr at 1,000 users — [Sahha: Terra alternatives](https://sahha.ai/compare/terra-alternatives/) (competitor claim)
- Sahha: "Start free with 25 development users and every product unlocked in sandbox"; production from $299/month billed annually with 1,000 users included, per-user pricing beyond; markets "Garmin, WHOOP, Oura & 800+ devices" — [Sahha comparison](https://sahha.ai/compare/terra-alternatives/); [Sahha homepage](https://sahha.ai/)
- Junction (formerly Vital / tryVital): Launch plan flat $300/month for up to 500 users, Link widget, 300+ device integrations; Enterprise needed for lab testing, unlimited users, uptime SLAs or a signed BAA; lab testing across all 50 US states with at-home kits/phlebotomy — [Junction pricing](https://www.tryvital.com/pricing); [Junction](https://www.junction.com/)
- Junction raised an $18M Series A (TechCrunch, 11 Mar 2025), positioning as an API linking wearables with labs — [TechCrunch](https://techcrunch.com/2025/03/11/junction-an-api-to-link-health-wearables-with-labs-raises-18m)
- A competitor comparison lists Junction at "$0.50/user/mo with a $300 minimum", Thryve as offering self-hosting with no licence fee, and Rook as requiring a wearable before returning data and billing its scoring layer on top — [Sahha comparison](https://sahha.ai/compare/terra-alternatives/) (competitor claim; conflicts in framing with Junction's own flat-$300 "Launch" description above)
- Industry framing: "Most vendors charge between $0.50 and $2 per connected user per month" — [Sahha comparison](https://sahha.ai/compare/terra-alternatives/) (competitor claim)
- Open-source/self-hosted entrants (Open Wearables) now market directly against Terra, Rook, Sahha, Spike and Junction — [Open Wearables compare](https://openwearables.io/compare)

**Device makers**
- WHOOP: "Access to the WHOOP Developer Platform and API is currently free, however, you must have a WHOOP device, which requires a membership"; v2 API released with developers urged to migrate from v1; a separate "Trusted Partner API" serves lab/diagnostics partners (requisitions, appointments, diagnostic results) — [WHOOP support](https://support.whoop.com/s/article/The-WHOOP-Developer-Platform?language=en_US); [WHOOP API changelog](https://developer.whoop.com/docs/api-changelog/); [WHOOP for Developers](https://developer.whoop.com/)
- WHOOP publishes an engineering blog post on how it designed its API (dev-rel content as marketing) — [WHOOP Engineering](https://engineering.prod.whoop.com/dev-platform/)
- Oura: Gen3 and later users without an active Oura Membership cannot access their data via the API, and partner apps cannot access those users' data; all users can download data files from the Membership Hub — [Oura Member Care](https://support.ouraring.com/hc/en-us/articles/4415266939155-The-Oura-API); [Oura for Organizations help](https://partnersupport.ouraring.com/hc/en-us/articles/20949682312211-Intro-to-the-Oura-API)
- Oura for Organizations sells to researchers with ring + customizable dashboards + data integration, "50+ biometrics"; claims 1,000+ peer-reviewed studies — [Oura for Organizations: researchers](https://organizations.ouraring.com/solutions/researchers); [Oura for Organizations](https://organizations.ouraring.com/)
- Garmin Connect Developer Program: no licensing or maintenance fees for the program itself, but some metrics may require a license fee or minimum device order for commercial use; partner-approval only, not self-serve — [Garmin program FAQ](https://developer.garmin.com/gc-developer-program/program-faq/); [Garmin Health API](https://developer.garmin.com/gc-developer-program/health-api/). A "$5,000 one-time administrative fee" for production Health API access is reported by third parties only — [AIFitnessAPI](https://aifitnessapi.com/pricing/garmin-api-pricing) (unverified; Garmin publishes no price list)
- Garmin also offers separate Health SDKs (device-level) alongside cloud APIs — [Garmin Health SDK](https://developer.garmin.com/health-sdk/)
- Polar Open AccessLink: "free to use, and now open to all developers"; any registered Polar Flow user can create an API client via an admin wizard — [Polar blog](https://www.polar.com/blog/introducing-polar-open-accesslink-api/); [Polar developers](https://www.polar.com/us-en/developers)
- Community-built clients (e.g., async Python client with full AccessLink V3 coverage) exist on GitHub/PyPI — [GitHub polar-flow](https://github.com/StuMason/polar-flow); [PyPI polar-accesslink](https://pypi.org/project/polar-accesslink/)
- Samsung: Samsung Health SDK for Android deprecated as of 31 July 2025; the new Samsung Health Data SDK can be used in developer mode without a partner request for read-only testing, but writing data or distributing an app requires a partnership — [Samsung Dev Insight Oct 2025](https://developer.samsung.com/sdp/news/en/2025/10/30/dev-insight-oct-2025-move-to-samsung-health-data-sdk-as-samsung-health-sdk-for-android-deprecates-and-other-latest-news); [Samsung Health SDK overview](https://developer.samsung.com/health/android/overview.html)

**OS platforms**
- Google Health Connect is an on-device Android SDK (same integration model as HealthKit, both require a mobile app); in March 2025 it added FHIR medical records (developer preview, starting with immunizations) — [Android Developers: Health Connect](https://developer.android.com/health-and-fitness/health-connect); [Sahha: HealthKit vs Health Connect](https://sahha.ai/blog/healthkit-vs-health-connect/); [Health Connect comparison guide](https://developer.android.com/health-and-fitness/health-connect/comparison-guide)
- Google Fit APIs (including REST) are scheduled for end of service by end of 2026; Google recommends Health Connect or the Google Health API — [Android Developers: Fit migration](https://developer.android.com/health-and-fitness/health-connect/migration/fit)
- Apple HealthKit is iOS-only with its own schema/permission model; supporting HealthKit and Health Connect is "two integrations, not one" — [Sahha: HealthKit vs Health Connect](https://sahha.ai/blog/healthkit-vs-health-connect/)

### Inferences
- Vybe's clearest differentiation vs. WHOOP/Oura is removing the membership gate for developer/research access (or pricing it transparently), since both incumbents tie API access to paid consumer memberships.
- Vybe should ship Health Connect and HealthKit write-through on day one; aggregators (Terra, Sahha, Junction) then pick up Vybe data with no bespoke work, and a listing on them is itself a distribution channel.
- A published price page plus a free sandbox (Sahha's "25 dev users" pattern) is table stakes for the indie/startup developer segment; enterprise/research should be "contact us" with published starting points.

### Gaps
- Could not fetch Rook's or Thryve's own pricing pages; figures above are competitor claims.
- Apple HealthKit has no fee, but no primary Apple source was fetched in this session.
- WHOOP's research-license terms (if any) were not found.

## 2. Channels and content that win developers

### Takeaway
Documentation is still the single most-used developer learning resource, and developer marketing evidence favors docs, a self-serve portal, YouTube and LinkedIn over generic social; Hacker News/Product Hunt can drive high-value spikes if the post is technical and non-promotional. LLM/AI-assistant discoverability of docs is an emerging channel.

### Cited Findings
- Stack Overflow 2025: technical documentation is the most popular learning resource (68%), then online resources (59%) and Stack Overflow (51%), all down year-over-year; 44% use AI tools to learn to code (up from 37%) — [Stack Overflow 2025 survey / Tech Elevator summary](https://www.techelevator.com/learning-to-code-in-2025-insights-from-the-stack-overflow-developer-survey/); [Survey: Developers](https://survey.stackoverflow.co/2025/developers)
- Stack Overflow 2025: 69% of developers learned a new technique or language in the past year; 36% focused on AI-enabled programming — [Stack Overflow for Leaders](https://stackoverflow.co/internal/resources/2025-stack-overflow-developer-survey-for-leaders/continuous-learning/)
- Stack Overflow 2025 headline: trust in AI accuracy at an all-time low — [Stack Overflow press release](https://stackoverflow.co/company/press/archive/stack-overflow-2025-developer-survey/)
- State of DevRel 2024 (as summarized by AngelHack): LinkedIn most effective channel for reaching developers (39.8%), then branded developer portal (28.5%), company website (26%), YouTube (26%); LLMs (ChatGPT, Claude, Perplexity) increasingly the first research channel, making GEO part of the mix — [AngelHack: Developer Relations in 2026](https://angelhack.com/blog/developer-relations/) (secondary summary of the DevRel.Agency report: [State of DevRel](https://www.devrel.agency/blog/categories/stateofdevrel))
- Recommended DevRel operational metrics: docs page engagement, getting-started completion, activation (API key created, first API call, tutorial completion), Discord/Slack/OSS activity — [AngelHack](https://angelhack.com/blog/developer-relations/)
- Launch sequencing advice: Product Hunt first, then a separate Show HN a few days later with a more technical story; HN is "not a traditional marketing channel" and punishes promotional posts — [Smol Launch](https://smollaunch.com/compare/product-hunt-vs-hacker-news); [Markepear: launch a dev tool on HN](https://www.markepear.dev/blog/dev-tool-hacker-news-launch)
- Competitors use comparison/"alternatives" pages and migration guides as SEO content (e.g., Sahha, Terra, Thryve and Open Wearables all published Fitbit-sunset migration guides) — [Sahha Fitbit migration](https://sahha.ai/blog/fitbit-api-sunset-migration/); [Terra Google Health API guide](https://tryterra.co/blog/everything-you-need-to-know-about-google-health-new-api); [Thryve Fitbit deprecation](https://www.thryve.health/blog/fitbit-api-deprecation); [Open Wearables migration guide](https://openwearables.io/blog/fitbit-web-api-shutdown-2026-migration-guide)
- Third parties build GitHub SDKs for popular health APIs unprompted (Polar), and "API Evangelist" maintains public profiles of WHOOP and Vital/Junction APIs on GitHub — [GitHub polar-flow](https://github.com/StuMason/polar-flow); [api-evangelist/whoop-co](https://github.com/api-evangelist/whoop-co); [api-evangelist/vital-io](https://github.com/api-evangelist/vital-io)

### Inferences
- Pre-launch, docs-first is the highest-leverage move: publish API reference, data dictionary for the five factors, and a sample dataset before hardware ships, so developers (and LLM assistants) can find and evaluate it.
- "Event-driven content" (e.g., a Fitbit/Google Fit migration guide) is a proven acquisition tactic in this category; Vybe can do the same around each platform change.
- Measure activation (first API call on sample data) rather than follower counts.

### Gaps
- Could not access the full 2025 State of DevRel or Evans Data 2025 report; the channel percentages above are from the 2024 edition via a secondary source.
- No sourced evidence found on hackathon or Discord ROI specifically for health-data APIs.
- No case study found of a wearable API's HN/Product Hunt launch results.

## 3. How researchers pick wearables and what they complain about

### Takeaway
Researchers prioritize reliable automated data collection across participants, access to validated (ideally raw) data, and cost; they complain about single-vendor lock-in, proprietary computed metrics that differ across manufacturers, and cost of middleware such as Fitabase.

### Cited Findings
- Fitabase is the most popular research data-collection system, used at 450+ institutions and 1,100+ studies; but it only accesses Fitbit-related products, its dashboard cannot be adapted to study-specific needs, and its cost (~$5,000/year) posed scalability challenges — [JMIR mHealth and uHealth, ADAM architecture](https://mhealth.jmir.org/2024/1/e50043) (2024 paper)
- "The lack of a data collection and management system that is useful across wearable technologies is a major barrier" for multi-device studies — [JMIR mHealth and uHealth](https://mhealth.jmir.org/2024/1/e50043)
- June 2025 adolescent-athlete study connected Fitbit to Fitabase via HIPAA-compliant protocol for de-identified access — [JMIR Formative Research 2025](https://formative.jmir.org/2025/1/e54630)
- Consumer wearables mix direct measurements (heart rate) with proprietary-algorithm outputs (sleep stages); computed variables differ by manufacturer and cross-device validation is an ongoing concern; data access policies vary by manufacturer — [Clinical and Translational Science 2026 tutorial, "Device and Data Access Considerations..."](https://ascpt.onlinelibrary.wiley.com/doi/10.1111/cts.70693); [PubMed](https://pubmed.ncbi.nlm.nih.gov/42552672/)
- Privacy policies of leading manufacturers are tracked in a living systematic analysis (npj Digital Medicine 2025) — [PMC12167361](https://pmc.ncbi.nlm.nih.gov/articles/PMC12167361/)
- Missing-data mechanisms in wearable sleep data are an active research topic (JMIR mHealth) — [JMIR mHealth](https://doi.org/10.2196/81123)
- Fitbit Web API sunset (Sept 2026) with closed new registrations and no token carry-over forces every participant to re-consent — directly disrupting Fitbit/Fitabase-based studies — [Sahha migration guide](https://sahha.ai/blog/fitbit-api-sunset-migration/); [Fitbit Community](https://community.fitbit.com/t5/Web-API-Development/Introducing-the-next-phase-of-the-Fitbit-Web-API/td-p/5821061)
- Oura markets to researchers with "a 2025 independent peer-reviewed study" finding the ring showed the strongest agreement among consumer wearables for HRV and RHR — [Oura for Organizations: researchers](https://organizations.ouraring.com/solutions/researchers) (vendor claim)

### Inferences
- The Fitbit sunset creates a 2026-2027 window where researchers are actively re-evaluating devices; Vybe's pre-launch research program should target labs affected by it.
- A research tier that offers raw/high-frequency data, a published algorithm/validation white paper, study-management dashboard, and HIPAA/BAA-ready terms directly addresses the stated complaints.
- Validation studies (even pilot) are the core "marketing content" for this audience; peer-reviewed agreement claims are what Oura leads with.

### Gaps
- Could not fetch the full CTS 2026 tutorial (PMC blocked) for device-by-device specifics.
- No 2025-2026 primary data found on Fitabase current pricing or on researcher survey rankings of devices.

## 4. Enterprise use cases and how vendors sell into them

### Takeaway
Enterprise demand concentrates in military/defense, corporate wellness, sports, and research/health systems; vendors sell via separate "for Organizations/Business" platforms with dashboards, bulk hardware and tiered contract pricing, and defense sales involve federal-compliant hosting and contract protests.

### Cited Findings
- Oura's ~$96M Pentagon contract (Oct 2024) for rings and services — [DefenseScoop](https://defensescoop.com/2024/10/02/pentagon-contracts-for-96m-in-oura-smart-rings-services/)
- WHOOP protested the award, alleging vendor preference, with a second GAO protest in January 2025 — [Breaking Defense](https://breakingdefense.com/2025/02/pentagons-96m-wearable-contract-sparks-protest-accusations-of-vendor-preference/). (A search summary claimed the Oura contract was "ultimately canceled"; I could not verify this in a primary source — treat as unconfirmed.)
- WHOOP won a contract via MIT Lincoln Laboratory (Navy-sponsored) to integrate its platform into the Navy's CREW (Command Readiness, Endurance, and Watchstanding) program — [MobiHealthNews](https://www.mobihealthnews.com/news/whoop-wins-contract-support-us-navy-wearables)
- The DoD is Oura's largest enterprise customer; Oura's Enterprise Platform is separate from consumer and uses Palantir's FedStart hosting to meet government security requirements; DoD sees only data service members consent to share — [TechCrunch](https://techcrunch.com/2025/09/09/smart-ring-maker-ouras-ceo-addresses-recent-backlash-says-future-is-a-cloud-of-wearables/); [Fortune](https://fortune.com/2025/09/09/oura-ceo-tom-hale-data-privacy-oura-ring-defense-department-palantir); [Snopes](https://www.snopes.com/fact-check/oura-ring-palantir-data-privacy/)
- Army H2F expanding to 111 active-duty brigades by May 2027 with 1,000 performance coaches; H2F Management System delivers "data-driven insights... typically only found within Special Operations or professional athletics" — [Serco](https://www.serco.com/na/media-and-news/2025/how-the-armys-h2f-program-is-building-a-fitter-more-holistic-force)
- Army leaders are wary of "data fatigue" as the fitness management system rolls out (Sept 2026) — [Army Times](https://www.armytimes.com/news/your-military/2026/09/28/army-leaders-wary-of-data-fatigue-as-fitness-management-system-rolls-out/)
- Oura for Business sells bulk hardware and analytics subscriptions to employers, health systems and sports organizations with tiered enterprise pricing — [Sacra](https://sacra.com/c/oura/); [Oura blog: Oura for Business](https://ouraring.com/blog/oura-for-business/)
- Junction gates BAA, SLAs and lab testing behind Enterprise — a typical way to separate self-serve dev from regulated enterprise buyers — [Junction pricing](https://www.tryvital.com/pricing)
- Aggregators like Validic list WHOOP and Oura in their enterprise marketplace (health systems channel) — [Validic: WHOOP](https://help.validic.com/space/VCS/4888723465/Whoop+API+Integration+for+Developers); [Validic: Oura](https://help.validic.com/space/VCS/3755966510)

### Inferences
- H2F's May 2027 expansion timeline coincides with Vybe's May 2027 launch; a pilot-ready enterprise package (dashboard, consented data sharing, federal-grade hosting roadmap) is a relevant pre-launch sales asset. "Data fatigue" suggests a screenless, low-burden device plus coach-facing summaries is a fitting pitch.
- Insurer and clinical-trial channels likely go through integrators (Validic, Junction, Terra), so partnership listings matter as much as direct sales.

### Gaps
- No 2025-2026 sourced data found on insurer wearable programs or clinical-trial device selection; not researched in depth within tool budget.
- Oura contract status after the WHOOP protests is unconfirmed.

## 5. Does Instagram/Facebook matter for developer marketing; what "build in public" works

### Takeaway
Available evidence ranks LinkedIn, a developer portal, the company site and YouTube as the top developer channels; Instagram/Facebook do not appear in those rankings. Consumer social can still matter indirectly as trust/reputation (the Oura backlash spread on social media), but SDK acquisition should run through dev channels.

### Cited Findings
- Top developer-reaching channels: LinkedIn 39.8%, developer portal 28.5%, company website 26%, YouTube 26% (State of DevRel 2024) — [AngelHack](https://angelhack.com/blog/developer-relations/)
- 70% of new learners use YouTube for tutorials; Stack Overflow, GitHub and YouTube remain top community learning tools — [Tech Elevator summary of SO 2025](https://www.techelevator.com/learning-to-code-in-2025-insights-from-the-stack-overflow-developer-survey/)
- Oura's DoD/Palantir controversy was amplified by social media creators saying they were ditching rings, despite company clarifications — [Slate](https://slate.com/technology/2025/10/oura-ring-pentagon-department-of-defense-health-wearable.html); [Pedestrian](https://www.pedestrian.tv/tech-gaming/oura-ring-backlash-military-privacy-data/); [Tom's Guide](https://www.tomsguide.com/wellness/smart-rings/oura-is-expanding-its-partnership-with-the-u-s-military-and-users-are-stressed-heres-what-that-means-for-your-data)
- Engineering-authored content (e.g., WHOOP Engineering "Designing the WHOOP API") is a form of build-in-public/dev storytelling used by an incumbent — [WHOOP Engineering](https://engineering.prod.whoop.com/dev-platform/)
- On HN, technical stories outperform promotional ones — [Markepear](https://www.markepear.dev/blog/dev-tool-hacker-news-launch)

### Inferences
- Use Instagram/Facebook for the SDK only for (a) showcase posts of what developers built (social proof for consumers) and (b) privacy/trust messaging; route developer calls to action to the portal, GitHub and LinkedIn/YouTube.
- Build-in-public content likely to work: API design decisions, validation data, changelogs, sample-data notebooks, and technical postmortems.

### Gaps
- No sourced study specifically measuring Instagram/Facebook effectiveness for developer acquisition was found; the conclusion rests on their absence from channel rankings.

## 6. Recent platform events: shutdowns, pricing changes, privacy/regulatory

### Takeaway
2025-2026 saw major API churn (Fitbit Web API and Google Fit shutdowns, Samsung SDK deprecation, WHOOP v2, Oura membership gating), a tougher consumer-health privacy regime (amended FTC HBNR), and FDA scrutiny of wellness claims (WHOOP). Stability, clear deprecation policy and careful claims language are marketable differentiators.

### Cited Findings
- Fitbit Web API: deprecated September 2026 as a hard cutoff; new developer registrations closed; successor Google Health API is a cloud REST API with no SDK aggregating Fitbit, Pixel and other sources; existing OAuth tokens do not carry over, so every user must re-consent — [Sahha migration guide](https://sahha.ai/blog/fitbit-api-sunset-migration/); [Fitbit Community announcement](https://community.fitbit.com/t5/Web-API-Development/Introducing-the-next-phase-of-the-Fitbit-Web-API/td-p/5821061); [Terra guide](https://tryterra.co/blog/everything-you-need-to-know-about-google-health-new-api)
- Google Fit APIs end of service by end of 2026 — [Android Developers](https://developer.android.com/health-and-fitness/health-connect/migration/fit)
- Samsung Health SDK for Android deprecated 31 July 2025 — [Samsung Developer](https://developer.samsung.com/sdp/news/en/2025/10/30/dev-insight-oct-2025-move-to-samsung-health-data-sdk-as-samsung-health-sdk-for-android-deprecates-and-other-latest-news)
- WHOOP v2 API launched; v1 migration encouraged — [WHOOP changelog](https://developer.whoop.com/docs/api-changelog/)
- Oura requires active membership for API access on Gen3+ rings — [Oura Member Care](https://support.ouraring.com/hc/en-us/articles/4415266939155-The-Oura-API)
- FTC amended Health Breach Notification Rule effective 29 July 2024: covers health apps and fitness trackers not covered by HIPAA; unauthorized disclosure (not just hacking) is a "breach"; notify individuals and FTC within 60 days (FTC notice simultaneous for 500+ affected) — [Federal Register](https://www.federalregister.gov/documents/2024/05/30/2024-10855/health-breach-notification-rule); [FTC blog](https://www.ftc.gov/business-guidance/blog/2024/04/updated-ftc-health-breach-notification-rule-puts-new-provisions-place-protect-users-health-apps); [FTC compliance guide](https://www.ftc.gov/business-guidance/resources/complying-ftcs-health-breach-notification-rule-0)
- FDA warning letter to WHOOP (14 July 2025) over Blood Pressure Insights; WHOOP called it FDA "overstepping"; FDA later closed the letter after product/labeling changes, consistent with updated General Wellness guidance — [FDA warning letter](https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/whoop-inc-709755-07142025); [CNBC](https://www.cnbc.com/2025/07/15/whoop-fda-blood-pressure-feature-wearables.html); [MedTech Dive](https://www.medtechdive.com/news/fda-drops-whoop-warning-letter-over-blood-pressure-feature/823652/)
- Oura/DoD/Palantir privacy backlash (Aug-Sept 2025) — [TechCrunch](https://techcrunch.com/2025/09/09/smart-ring-maker-ouras-ceo-addresses-recent-backlash-says-future-is-a-cloud-of-wearables/)

### Inferences
- Vybe's SDK marketing should lead with a public deprecation/versioning policy and "your data, your consent" architecture, directly contrasting with the 2025-2026 churn.
- Anything Vybe's "Vitals" factor exposes via SDK must use wellness (not diagnostic) language to avoid the WHOOP-style FDA issue; developers building on Vybe inherit this risk, so developer terms and docs should include claims guidance.
- Any Vybe app/SDK that shares data with third parties falls under FTC HBNR if not HIPAA-covered; a BAA-ready enterprise tier plus HBNR-compliant consent flows is a sales asset.

### Gaps
- Exact date of FDA's closure of the WHOOP letter not captured in fetched snippets (reported as roughly a year after July 2025).
- The FTC "withdraws obsolete policy statement" (Sept 2026) result appeared in search, but its relevance to HBNR was not verified.
