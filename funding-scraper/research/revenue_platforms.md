# Revenue platforms for Vybe Health: pre-orders, sales and paid pilots up to the May 2027 launch

Prepared 11 Oct 2026 from `VYBE_PROFILE.md`. Vybe is pre-revenue and under a year old. It sells a
screenless ECG/HRV band with no subscription, plus DevKit v0.1 (SDK/API), which is placed with 5–10
design partners. It is not a medical device and makes no diagnostic claims. Consumer launch is
May 2027, followed by Best Buy.

**How this was checked.** Fees, rules and campaign totals come from each platform's own page or
the campaign page, read on 11 Oct 2026. Kickstarter totals come from each project's own
`/stats.json`. Anything not on an official page is marked *press-reported* or *not stated*.

**About the revenue figures.** The "realistic revenue" numbers are **our estimates**, not facts.
They are scaled from the verified comparables below and assume Vybe starts with a small audience.
The Vybe band price is **not stated** in the profile. The estimates assume a $199–$299 band and
dev kits at $249–$399, which is the range of the comparables (HealthyPi Move $299; Movesense dev
kits €249–€399).

---

## Ranked top 10 (by realistic revenue before and at launch)

| # | Platform | Revenue type | Realistic revenue for Vybe, Oct 2026 – Jul 2027 (estimate) | Fees (verified) | Timing (when to start) | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Kickstarter** (+ Late Pledges) | Consumer band pre-orders | **$50K–$300K** base case. $500K+ only with a large pre-launch list and paid ads; Circular Ring 2 used many paid promotion partners. | 5% platform fee + 3% + $0.30 per pledge (pledges under $10: 5% + $0.08). No fee if the campaign is unfunded. Late Pledges carry the same 5% fee. | Pre-launch page now. Launch roughly Feb–Mar 2027, once the DVT/production prototype is filmed. Turn Late Pledges on before the deadline. | **Primary consumer pre-order channel.** |
| 2 | **Direct B2B: DevKit sales + paid pilots** (invoice/PO, Vybe store) | Hardware + SDK access, research and enterprise pilot fees | **$15K–$100K** (for example 20–60 kits at $249–$399, plus 2–5 paid pilots). Pilot prices: not stated by any public source. | Card processing only (Stripe/Shopify 2.9% + 30¢), or none on bank transfer and PO | **Now.** Turn the 5–10 design partners into paid kits and pilots. | **Start immediately.** Fastest real revenue and validates the platform story. |
| 3 | **Own Shopify store pre-orders/deposits** (then DTC sales at launch) | Deposits or full pre-orders, then launch sales | **$20K–$100K** before launch (waitlist plus post-Kickstarter pre-orders). More at launch. | Shopify Basic $29/mo (billed yearly), cards from 2.9% + 30¢. Pre-order app needed: e.g. PreProduct is free + 5.0% of paid pre-order revenue, or $59.99/mo, or $259.99/mo at 0%. | Waitlist now. Paid pre-orders after the Kickstarter ends (do not run them during the campaign). | **Core owned channel.** Also the gateway to Shopify Capital. |
| 4 | **Pledge manager / post-campaign store** (Kickstarter Late Pledges, BackerKit Pledge Manager, Crowd Supply-style pre-orders) | Add-ons, late pledges, extra bands and straps | **+$10K–$100K** on top of #1. HealthyPi Move grew from $24,274 at campaign end to $55,954 with post-campaign orders. | BackerKit PM for an off-platform campaign: campaign fee 2% or less + 3.5% transaction fee + Stripe fees | Set up in the last weeks of the campaign; run until shipping. | **Do it.** Cheap incremental revenue. |
| 5 | **Amazon** (standard Professional seller) | Retail sales at launch | **$5K–$50K** in the first 2–3 months after May 2027 (needs reviews and ads) | $39.99/mo Professional. Referral fee 8% for Consumer Electronics (Electronics Accessories: 15% up to $100, 8% above). New-to-Amazon brands: "over $50,000 in automatic referral-fee waivers" in year 1. | Brand Registry once the trademark is filed. List at launch (May 2027). | **Yes at launch.** Amazon Launchpad and Accelerator are no longer listed on Amazon's seller site. |
| 6 | **Best Buy Marketplace** (third-party, BestBuy.com) | Online retail at launch | **$5K–$30K** in the first months | Not stated publicly. The page says only "transparent, competitive fees". | Apply about Feb–Mar 2027. Approval is vetted. | **Yes.** The realistic first step into Best Buy before a store/vendor deal. |
| 7 | **Indiegogo** (now Gamefound-powered) | Consumer pre-orders | Same range as Kickstarter **if used instead of it**. Do not run both at once. | 5% platform fee + 3% + $0.20 per transaction. Fixed funding only since 16 Oct 2025. | Alternative to #1, same window | **Backup.** Its content policy lists "health and wellness" among prohibited categories, so get written pre-clearance first. |
| 8 | **Crowd Supply** | DevKit crowdfunding to engineers | **$20K–$60K** (HealthyPi Move $24K at campaign end, $56K total; HealthyPi 5 $56K) **only if** Vybe releases an open-source DevKit variant | 5% of campaign pledges + 2.9% + $0.30. Optional 10% on post-campaign pre-orders; optional fulfilment fee. | Only after deciding to open firmware and schematics. Campaign 3–4 months from submission. | **Conditional.** Requires open firmware and schematics, which conflicts with Vybe's proprietary engine. |
| 9 | **Best Buy vendor (stores), Costco, QVC/HSN** | Wholesale / retail POs | **About $0 before launch.** First POs realistically late 2027 or later, after sell-through data. | Margins not stated publicly. QVC requires GS1/UPC and has chargebacks for non-compliance. | Register diverse-supplier status now (Costco Supplier Inclusion form; Best Buy asks certified diverse suppliers to name their certifier). Pitch after launch. | **Prepare now, sell later.** |
| 10 | **Gumroad** | Digital DevKit extras (docs, courses, paid workshops) or small hardware batches | **<$5K** | 10% + $0.50 per direct sale; 30% via Gumroad Discover | Any time | **Minor.** Not a hardware channel. |

**Not ranked (no realistic pre-launch revenue):**
- **Target Takeoff**: invite-only, for brands Target has already selected.
- **b8ta**: US stores shut 18 Feb 2022.
- **GoFundMe**: bans rewards in exchange for donations, so it cannot take pre-orders.
- **Amazon Launchpad and Amazon Accelerator**: no longer on Amazon's seller program pages.
- **Revenue-based financing**: financing rather than revenue. See section 4.

---

## 1. Hardware crowdfunding and pre-order

### Health-claim rules that apply to every channel
- **FDA.** FDA reissued *General Wellness: Policy for Low Risk Devices* on 6 Jan 2026. It added
  "clarity … on products that perform non-invasive sensing of physiologic parameters"
  ([FDA town hall page](https://www.fda.gov/medical-devices/medical-devices-news-and-events/town-hall-general-wellness-policy-low-risk-devices-final-guidance-02112026)).
- **WHOOP precedent.** In a 17 Jun 2026 letter, FDA said it does not intend to enforce device
  requirements on WHOOP's modified "Blood Pressure Insights" product, citing the updated guidance
  ([FDA letter](https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/whoop-inc-709755-06172026)).
  This confirms Vybe's wellness-only framing is the right posture for campaign copy.
- **What to keep out of campaign copy:** AFib or arrhythmia detection, "detects disease",
  blood-pressure or glucose claims, and "prevents injury" claims.

### Kickstarter — rank 1
**Fees.** "Kickstarter's 5% fee, and payment processing fees (between 3% and 5%)." In the US that
is 3% + $0.30 per pledge, or 5% + $0.08 for pledges under $10. "If funding isn't successful, there
are no fees" ([kickstarter.com/help/fees](https://www.kickstarter.com/help/fees)).

**Late Pledges.** These must be enabled before the deadline. They carry "weekly payouts and the
same 5% fee" ([features.kickstarter.com/late-pledges](https://features.kickstarter.com/late-pledges)).

**Health and wearable rules** ([kickstarter.com/rules](https://www.kickstarter.com/rules)). The
rules prohibit:
- "Items claiming to diagnose, cure, treat, or prevent a **serious** illness or condition"
- "Items claiming to prevent a serious injury or death"

The second ban matters for any tactical or safety marketing.

**Hardware prototype rule (same page).** "Prototype demonstration should reflect a product's
current state and should not include any CGI or special effects to demonstrate functionality that
does not yet exist." If software and hardware must work together, "creators are required to show
that functionality … or disclose that it has not yet been developed." Creators also "must not use
Kickstarter as a method to funnel engagement to external websites."

**Fulfilment expectations.** Creators are "expected to put a genuine effort into fully completing
their projects" and to update backers regularly. There is no fixed delivery deadline in the rules.

**Comparable campaigns** (totals from each project's Kickstarter `stats.json`; all successful):

| Campaign | Backers | Pledged | Source |
|---|---|---|---|
| Circular Ring 2 (health-tracking ring) | 13,695 | $4,078,500 | [Kickstarter](https://www.kickstarter.com/projects/circular-ring/circular-ring-2-worlds-most-advanced-health-tracking-ring). The creator page lists many paid newsletter and marketing partners. |
| VELIA / Iris smart ring | 3,465 | 622,672 (project currency, CHF per search listing) | [Kickstarter](https://www.kickstarter.com/projects/iris-smart-ring/iris-smart-ring-elevate-style-embrace-self-awareness) |
| Ultrahuman Ring AIR (HRV/sleep) | 1,022 | 311,564.5 (GBP per search listing) | [Kickstarter](https://www.kickstarter.com/projects/ultrahuman/ultrahuman-ring-air). The page says the first 2022 Ultrahuman Kickstarter raised "over 500k USD". |
| Bangle.js 2 (open smartwatch, HR) | 2,094 | 176,522 (GBP per search listing) | [Kickstarter](https://www.kickstarter.com/projects/gfw/banglejs-2-the-open-smart-watch) |
| OpenBCI "Biosensing for Everybody" (dev hardware) | 644 | $168,829 | [Kickstarter](https://www.kickstarter.com/projects/openbci/openbci-biosensing-for-everybody) |
| EmotiBit (research biometric wearable) | 332 | $118,692 | [Kickstarter](https://www.kickstarter.com/projects/emotibit/emotibit-0) |
| Y-RING | 398 | $83,649 | [Kickstarter](https://www.kickstarter.com/projects/1936791793/y-ring) |
| airing smart ring (hormone/heart) | 313 | $45,037 | [Kickstarter](https://www.kickstarter.com/projects/2016344821/a-smart-ring-that-understands-hormones-emotions-and-health) |

**Reading the comparables.** Unknown or first-time health-ring brands land at $45K–$84K. Funded,
marketed brands reach $300K–$600K. The $4M outlier had heavy paid promotion. Vybe's base case of
$50K–$300K assumes a modest list built between now and launch.

### Indiegogo (incl. InDemand, now "Late Pledge") — rank 7
**Platform change.** Gamefound acquired Indiegogo on 22 Jul 2025, and the platform migrated on
16 Oct 2025
([support.indiegogo.com](https://support.indiegogo.com/hc/en-us/articles/39600950083988-Indiegogo-s-Acquisition-by-Gamefound)).

**Fees and mechanics** ([help.indiegogo.com/article/645](https://help.indiegogo.com/article/645-what-changed-with-the-platform-upgrade)):
- Flat 5% platform fee + 3% + $0.20 per transaction.
- Flexible Funding has been discontinued for new campaigns.
- InDemand is now "Late Pledge", followed by a Pledge Manager stage.
- New campaigns use Adyen, and creators must pass a two-step compliance and KYC review.
- Campaign end dates cannot be changed once live.

**Health rules** ([Content Policy](https://www.indiegogo.com/en/terms/contentpolicy)). The policy
lists "health and wellness, medication, and dietary supplements, including but not limited to" the
following:
- drugs and supplements
- "any item claiming to cure, treat, or prevent an illness or serious medical condition"
- FDA class III medical devices
- "products making false or misleading health claims"

Read literally, the heading puts "health and wellness" itself in the prohibited list. Health-ring
campaigns do run on Indiegogo, but Vybe should get written pre-clearance from Indiegogo before
building there.

**Comparable.** Ring One (Muse Wearables):
[campaign page](https://www.indiegogo.com/en/projects/ringone/ring-one-the-most-advanced-smart-ring-for-you).
The total is not shown on the campaign page. It is *press-reported* as "over 7,800 backers and
raising more than $1.7 million"
([Notebookcheck](https://www.notebookcheck.net/Ring-One-smart-ring-team-share-crowdfunding-campaign-update.832655.0.html)).
Notebookcheck also reports shipping well behind the original estimate, which is a fulfilment
warning.

### Crowd Supply — rank 8 (conditional)
**Fees** ([working-with-crowd-supply](https://www.crowdsupply.com/working-with-crowd-supply)):
- 2.9% + $0.30 per transaction
- 5% of the total pledged during the campaign
- optional 10% on pledges after the campaign
- optional fulfilment fee

It is all-or-nothing. Crowd Supply can also buy inventory or drop-ship afterwards, and those terms
are negotiated.

**Blocking rules:**
- "We require a significant portion of your hardware to be open source, at least the firmware and
  the schematics"
  ([why-projects-get-rejected](https://www.crowdsupply.com/guide/why-projects-get-rejected)).
- A working, preferably EVT, prototype is required.
- "Anything that has been or is currently selling anywhere else" is not suitable.
- Do not run a campaign on another platform at the same time
  ([when-to-submit](https://www.crowdsupply.com/guide/when-to-submit)).

Vybe's proprietary firmware and signal-processing engine conflicts with the open-source
requirement. Crowd Supply fits only an open reference DevKit board.

**Comparables:**
- **HealthyPi Move** (open-source ECG wearable): $24,274 against a $10,000 goal at campaign end
  ([crowdfunding page](https://www.crowdsupply.com/protocentral/healthypi-move/crowdfunding)), now
  $55,954 including later orders, at $299 per unit
  ([product page](https://www.crowdsupply.com/protocentral/healthypi-move)). It was fulfilled
  through Crowd Supply and Mouser from the US.
- **HealthyPi 5:** $56,190 raised ([page](https://www.crowdsupply.com/protocentral/healthypi-5)).

### BackerKit (crowdfunding and pledge manager) — rank 4 as pledge manager
Source: [backerkit.com/pricing](https://www.backerkit.com/pricing).

**Crowdfunding on BackerKit:**
- 5% platform fee + 2.9% + $0.30 per pledge (US), charged only if the goal is reached.
- Pledge Manager: 0% campaign fee + 5% transaction fee.

**Pledge Manager for a campaign run elsewhere** (e.g. Kickstarter):
- Campaign fee "2% or less". The bands start at 2.00% up to $50K and fall to 1.10%, capped at $5
  per backer when the average pledge is over $250.
- 3.5% transaction fee on add-ons and pre-orders
  ([pricing/pledge_manager](https://www.backerkit.com/pricing/pledge_manager)).

BackerKit also runs a "Pre-order marketplace". We found no wearable comparable on BackerKit.

### Shopify pre-orders — rank 3
**How pre-orders work.** Shopify needs a pre-order app. You "can collect full, partial, or no
payment at the time the customer places their order"
([help.shopify.com](https://help.shopify.com/en/manual/products/purchase-options/pre-orders)).

**Plans** ([shopify.com/pricing](https://www.shopify.com/pricing)):
- $29/mo, cards from 2.9% + 30¢
- $79/mo, cards from 2.7% + 30¢
- $299/mo, cards from 2.5% + 30¢

**Example app.** PreProduct: free + 5.0% of paid pre-order revenue, $59.99/mo (0% on the first $5K
a month, then 0.5%), or $259.99/mo at 0% ([apps.shopify.com/preproduct](https://apps.shopify.com/preproduct)).

**Claim rules.** These are Shopify's general Acceptable Use Policy plus FTC and FDA law. No
wearable-specific rule was found.

### Gumroad — rank 10
10% + $0.50 per direct sale; 30% via Discover ([gumroad.com/pricing](https://gumroad.com/pricing)).
It fits digital DevKit add-ons (paid onboarding, a course, sample datasets) more than hardware.

### GoFundMe-type sites — not usable
The terms prohibit "promotions involving rewards … in exchange for donations"
([gofundme.com/terms](https://www.gofundme.com/terms), §8.12). Pre-orders are not allowed.

---

## 2. Retail and marketplace launch routes

### Amazon — rank 5
**Fees** ([sell.amazon.com/pricing](https://sell.amazon.com/pricing)):
- Professional plan $39.99/mo; Individual $0.99 per item.
- Referral fees: Consumer Electronics 8% (min $0.30). Electronics Accessories 15% up to $100,
  then 8%. Amazon's fee category guidelines decide which applies to a wearable band.
- New-to-Amazon brands: "over $50,000 in automatic referral-fee waivers for your first year".

**Launchpad and Accelerator.** `sell.amazon.com/programs/launchpad` now opens the generic programs
page, and `/programs/amazon-accelerator` returns "Page not found". Neither program appears on
Amazon's current program list, so plan for standard selling plus Brand Registry. Third-party blogs
still describe Launchpad (a 5% fee), but that is unverified on Amazon's site.

**When.** At launch in May 2027, once inventory exists (Amazon has no pre-order route for a new
brand).

### Best Buy — ranks 6 and 9
**Marketplace** ([bestbuy.com/marketplace](https://www.bestbuy.com/marketplace)):
- "Get approved and join … Approval is subject to terms and conditions."
- Fees: "transparent, competitive", but not stated publicly.
- Sellers are "carefully selected".
- It runs on Mirakl
  ([Mirakl](https://www.mirakl.com/blogs/marketplace/best-buy-partners-with-mirakl-doubles-product-assortment-with-marketplace/)).

**Vendor (owned inventory or Supplier Direct Fulfillment)**
([partners.bestbuy.com SDF onboarding](https://partners.bestbuy.com/-/supplier-direct-fulfillment-sdf-onboarding)):
- Requires EDI through Rithum, EFT, PDM for SKU setup, and a Best Buy FedEx account.
- Setup takes about 2 weeks longer than for Core vendors.
- "If you are a certified Diverse Supplier, please provide the name of the organization." Vybe
  should get NMSDC, WBENC or NaVOBA/VOSB certification to use this.
- IoT products are asked extra questions at SKU setup.
- Margins and terms are not stated publicly.

**Health programmes.** No Best Buy "Assisted Living" partner programme for third-party wearables
was found on Best Buy's pages. Best Buy Health has been shrinking: Best Buy sold Current Health
back to its co-founder in June 2025, and Lively remains (*press-reported*,
[Healthcare Dive](https://www.healthcaredive.com/news/best-buy-sells-current-health-home-care-christopher-mcghee/751645/)).
Do not plan on a health-partner route.

**When.** Apply to the Marketplace about Q1 2027. Pitch a vendor or store deal after 3–6 months of
sell-through.

### Target Takeoff — not ranked
"Our program supports brands already selected by Target for placement in-store or online … No
need to fill out a program-specific application"
([accelerators.target.com](https://accelerators.target.com/programs/target-takeoff/)). It is
invite-only after Target picks you, so Vybe has no pre-launch route here.

### b8ta and its successors — not ranked
b8ta "officially shut down its U.S. brick-and-mortar operations on Feb. 18, 2022" (*press-reported*,
[Retail TouchPoints](https://www.retailtouchpoints.com/news/b8ta-ends-u-s-operations-but-the-experiential-trailblazer-leaves-multiple-lessons-for-other-retailers/101879/)).
We could not verify a current US retail-as-a-service operator with public pricing.

### Costco (incl. Roadshow) — rank 9
**Supplier Inclusion.** Costco's Supplier Inclusion programme has an intake form; "completing the
application does not guarantee a business partnership"
([costco.com/f/-/supplier-diversity](https://www.costco.com/f/-/supplier-diversity)). This fits
Vybe's veteran-, woman- and minority-owned status.

**Roadshow.** We found no official Costco page describing Roadshow requirements or fees. Not stated.

**When.** After launch, with sell-through data.

### QVC/HSN — rank 9
**Onboarding** ([QVC Vendor Onboarding Guide PDF](https://www.qvc.com/footers/pdf/QVC_Vendor_Onboarding_Guide.pdf)):
- Categories include Electronics and Health & Fitness.
- QVC prefers products "making their debut on QVC or are entirely exclusive to us".
- Every item goes through a **Legal Claims Review** and QA with lead times.
- Required: buyer, QA and show samples; GS1 GTINs; vendor chargebacks for non-compliance.
- Payment terms offered include Net 90, Net 50 with 2% discount, or Net 30 with 3% discount.
- Margins: not stated.

**When.** Post-launch, needing inventory depth and a demonstrable on-air story.

---

## 3. B2B revenue (DevKit and pilots) — rank 2
**Channels:**
- direct invoice or university PO from a Vybe store page
- Crowd Supply (with Mouser fulfilment), only if an open variant exists
- enterprise and research pilot contracts

**Comparable public dev-kit prices** (verified on vendor pages):
- **Movesense** ([dev kits](https://www.movesense.com/product-category/dev-kits/)), all VAT 0%:
  - MD Developer Kit 399,00 € (was 479,00 €)
  - Flash Developer Kit 379,00 €
  - HR+ Developer Kit 249,00 €
- **HealthyPi Move:** $299 ([Crowd Supply](https://www.crowdsupply.com/protocentral/healthypi-move)).

**Paid-pilot price points** for university or enterprise wellness pilots are **not stated** on any
public page we found. Set them by contract.

**Practical model.**
- Price DevKit v0.1 inside the $249–$399 band, plus a paid SDK/API licence and support tier.
- Convert the 5–10 design partners into paid orders. Even 3–5 small paid pilots plus kits beat
  every retail channel before May 2027.

---

## 4. Revenue-based financing: when Vybe would qualify

| Provider | Minimum (from the provider's own page) | Earliest Vybe qualifies (estimate) |
|---|---|---|
| **Stripe Capital** | US business; ≥3 months processing history; $5,000/yr minimum volume and $1,000 average over the last 3 months ([docs.stripe.com](https://docs.stripe.com/capital/how-stripe-capital-works)). Flat fee, e.g. "$15,000 loan, $1,500 loan fee" ([stripe.com/capital](https://stripe.com/capital)). | About 3 months after Stripe sales start. If DevKit sales start Q4 2026, roughly **Q1–Q2 2027** (small offers). |
| **Shopify Capital** | US merchants; "Sell on Shopify for at least 90 days"; offers by invitation; funding up to $2M; repaid from a fixed % of daily sales; max term 18 months ([shopify.com/capital](https://www.shopify.com/capital)) | About 90 days after the Shopify store takes orders: **~Q2 2027** |
| **Pipe** | "Businesses incorporated in the US … typically with at least $10,000+ annualized predictable revenue" ([pipe.com/resources](https://pipe.com/resources)). Terms say it is for businesses with recurring revenue. | When SDK/API licences create recurring revenue: **late 2027** |
| **Arc** | ≥6 months runway, "at least $10k in MRR for the past 6 months", US entity ([arc.tech](https://www.arc.tech/encyclopedia/revenue-based-financing)) | 6 months at $10K MRR: **2028** at the earliest |
| **Lighter Capital** | "Minimum of $200K in annual recurring revenue or $15K MRR from a diverse customer base", from software, SaaS or tech services ([lightercapital.com/how-it-works](https://www.lightercapital.com/how-it-works)) | Only with SDK/licensing ARR: **2028+** |
| **Clearco** | "Over $100,000 in monthly revenue through your connected ecommerce platforms … for the past 6 months" ([help.clear.co](https://help.clear.co/articles/en_US/Knowledge/How-to-apply-to-Clearco)) | After 6 months at $100K/mo of DTC revenue: **not before 2028** |

---

## Recommended sequence (Oct 2026 → May 2027)

1. **Now – Dec 2026: B2B first.**
   - Convert DevKit design partners into paid kits and pilots (invoice/PO and Stripe).
   - Open a Shopify store with a free email waitlist; take no pre-order money yet.
   - Launch the Kickstarter "coming soon" page.
   - Register a trademark and Amazon Brand Registry.
   - Start the diverse-supplier certifications (NMSDC, WBENC, NaVOBA).
   - Lock wellness-only copy against FDA's Jan 2026 General Wellness guidance and Kickstarter's
     health rules.
2. **Jan 2027: final campaign assets.**
   - Film the real DVT prototype with no CGI and show the app–band dependency.
   - Line up the pledge manager (Kickstarter native or BackerKit).
   - Apply to the Best Buy Marketplace.
   - Stripe Capital may start offering small advances once DevKit sales have 3 months of history.
3. **Feb–Mar 2027: run the Kickstarter campaign.**
   - 30–35 days, all-or-nothing, with Late Pledges enabled before the deadline.
   - Do not run Indiegogo or Crowd Supply at the same time.
   - Use Indiegogo only as the fallback platform, after written pre-clearance.
4. **Mar–May 2027: post-campaign sales.**
   - Late Pledges and pledge-manager add-ons, then Shopify paid pre-orders (deposit or full) for
     non-backers.
   - Keep publishing DevKit and SDK updates to developers.
5. **May 2027: launch.**
   - Fulfil backers first, then go live on Shopify DTC, Amazon (standard listing) and the Best Buy
     Marketplace.
   - Shopify Capital invitations become possible about 90 days after the store's first orders.
6. **H2 2027: wholesale.**
   - With sell-through data, pitch a Best Buy vendor or store deal (as a certified diverse
     supplier), Costco Supplier Inclusion and QVC.
   - RBF beyond Stripe and Shopify (Pipe, Arc, Lighter) only once SDK/API licensing produces
     recurring revenue.

**Open items to verify before committing:**
- Best Buy Marketplace commission (not public).
- Indiegogo's reading of "health and wellness" (ask support).
- Kickstarter category placement for an ECG band (pre-submission check with Kickstarter).
- Costco Roadshow terms (no official page).
