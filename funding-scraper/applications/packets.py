"""Application packets — the single source for the Apply page.

Answers use {{KEY}} placeholders for facts only Jeremy has. The page fills them
from the fact sheet as he types; an unfilled one shows as a highlighted gap.
Never replace a placeholder with an invented fact.

Run `python3 build.py` to regenerate index.html after editing.
"""

FACTS = [
    ("LEGAL_NAME", "Legal business name", "Vybe Health, Inc."),
    ("STATE", "State of formation", "Delaware"),
    ("FORMED", "Date formed", "March 2024"),
    ("EIN", "EIN", "12-3456789"),
    ("CITY", "Business city and state", "Akron, OH"),
    ("WEBSITE", "Website", "vybe.health"),
    ("EMAIL", "Company email", "you@vybe.health"),
    ("CEO", "CEO name and title", "Jane Doe, Founder and CEO"),
    ("OWNERSHIP", "Who owns what", "Jane Doe 60%, John Roe 40%"),
    ("WOMAN_OWNER", "Woman owner (the Amber / Tory Burch applicant)", "Jane Doe"),
    ("VETERAN_OWNER", "Veteran owner, branch, years", "John Roe, US Army, 2008-2016"),
    ("MINORITY_BASIS", "Minority ownership, as the federal definition names it", "Black American"),
    ("REVENUE", "Revenue, last 12 months", "$0 (pre-revenue)"),
    ("EMPLOYEES", "Employees (including founders)", "3"),
    ("STAGE", "Where the product is today", "working Band prototype; app in private beta"),
    ("TRACTION", "Users, waitlist or pilots", "a 400-person waitlist"),
]

# Gates the viewer answers once; each packet lists which it depends on.
GATES = [
    ("years2", "In business 2+ years"),
    ("years1", "In business 1+ year"),
    ("staff2", "2 or more employees"),
    ("rev75", "Revenue of $75,000+ a year"),
    ("incorp", "Incorporated (LLC or corporation)"),
    ("equity", "Raised equity from an institutional investor"),
    # An age CEILING, not a floor. Most veteran grants want a minimum trading
    # history; Veteran Shark Tank wants the opposite, which is why a company too
    # young for Tadlock or Buckeye clears it.
    ("under3", "In business less than 3 years"),
    # Not money and not paperwork: PenFed's Accelerator is four days in a room
    # plus six weeks of mentoring, and the Incubator three days. A founder who
    # cannot travel is not eligible however good the business is, so it belongs
    # here rather than buried in a note.
    ("inperson", "Able to attend several days in person, travel covered"),
    # Army xTech's ownership test is not the usual paperwork question. It is a
    # citizenship AND control test: a cap table that passes can still fail on
    # who actually controls the company, so it gets its own line.
    ("uscitizen", "Majority owned AND controlled by US citizens or permanent residents"),
    # Federal prize competitions bar a submission that duplicates work already
    # funded or pending elsewhere in government. Only the founders know this.
    ("nodupfed", "No substantially similar proposal funded or pending at another federal agency"),
    # Ohio TechCred's two real gates, and the reason its board row was corrected.
    # "Ohio-based" is not the test: the premises must not be residential, so a
    # company working out of a founder's house fails on the address alone.
    ("ohiosite", "A physical, non-residential business location in Ohio"),
    # And the payroll test. Contractors and 1099 workers count for nothing here,
    # so a founding team drawing no wage has nobody eligible to train.
    ("w2ohio", "Ohio-resident W-2 employees reported to Ohio unemployment insurance"),
]

# Confirmed by Jeremy 2026-09-24. The page opens with these answers, and the
# daily routine must not draft a packet whose gates these fail:
# under 1 year in business, revenue under $75,000, 2-100 employees, incorporated.
# Institutional equity was not asked; leave it unanswered until it is.
GATE_DEFAULTS = {
    "years2": "no",
    "years1": "no",
    "staff2": "yes",
    "rev75": "no",
    "incorp": "yes",
    # Follows directly from "under 1 year in business" — not a separate claim.
    "under3": "yes",
}

# Reusable blocks. Written in Vybe's voice: calm, plain, short lines.
ONE_LINER = (
    "{{LEGAL_NAME}} builds Vybe, a personal health intelligence platform: a "
    "screenless band, a person's connected health data, and AI that answers plain "
    "questions about their own body."
)

SHORT = (
    "Vybe turns the signals a body already produces into answers a person can act "
    "on. The screenless Vybe Band tracks ECG, heart-rate variability, sleep and "
    "activity. Vybe Intelligence reads those signals alongside the context around "
    "them, like stress, work, travel and weather, and answers questions such as "
    "\"Why am I tired today?\" There is no required subscription."
)

LONG = (
    "Most wearables stop at the score. They report that heart-rate variability "
    "dropped and leave the person to work out why. Vybe is built for the step "
    "after the number.\n\n"
    "The Vybe Band is a screenless wearable that tracks ECG, heart-rate "
    "variability, sleep and activity. Vybe Intelligence reads those signals across "
    "five parts of a person's life: Restore, Move, Nourish, Connect and Vitals. "
    "Connect is the one other products miss. A reading can change for reasons a "
    "sensor cannot see, like a hard week at work, a long flight or a heat wave, so "
    "Vybe takes that context into account.\n\n"
    "People ask plain questions, such as \"Why am I tired today?\" or \"Should I "
    "train tonight?\", and get an answer grounded in their own data, with the "
    "evidence shown and one next step.\n\n"
    "Vybe has no required subscription. The interpretation is part of the product, "
    "not a monthly fee. Vybe is not a medical device and makes no diagnostic claims."
)

WHY_NOW = (
    "Wearables are a roughly $103 billion market in 2026, and AI on wearables is "
    "growing about 27.8% a year through 2033. The category has split. Oura kept "
    "its subscription and deepened its intelligence, reaching an $11 billion "
    "valuation. Whoop went subscription-only, reversed a 2025 upgrade decision "
    "under pressure and now faces a 2026 class action. Ultrahuman, RingConn and "
    "Amazfit dropped the subscription and the intelligence with it. No one offers "
    "deep interpretation without a required subscription. That is Vybe's position."
)

PACKETS = [
    {
        "id": "buckeye",
        "name": "Buckeye State CU Small Business Recovery Grant",
        "funder": "Buckeye State Credit Union (CDFI Equitable Recovery Program)",
        "amount": "$200,000 / $150,000 / $125,000 — three grants",
        "deadline": "2026-09-30",
        "fee": None,
        "url": "https://www.buckeyecu.org/small-business-recovery-grant/",
        "submit": "Download the application from the program page, complete it, and email the full package to grantsupport@buckeyecu.org by 30 September. Membership is not required and businesses outside Akron may apply; Summit County gets priority.",
        "gates": ["years2"],
        "confirmed": ["Minority-owned or minority-controlled (confirmed 20 Sep)"],
        "why": "The largest award on the board that Vybe's ownership qualifies for. Reviewers score eligibility, completeness, alignment with the program and community impact. Funds may pay payroll, rent, utilities, inventory, supplies and working capital.",
        "docs": [
            "Completed application form (from the program page)",
            "Proof of two or more years in operation: formation documents plus two years of tax returns or financial statements",
            "Proof of minority ownership or control: operating agreement or cap table, and any MBE certification you hold",
            "Certificate of good standing from your state",
            "The community-benefit plan and use-of-funds budget below",
        ],
        "note": "The exact form was not readable from here. These are the sections the program says it scores; paste each into the matching part of the downloaded form. Label every attachment by name so the reviewer never has to hunt for proof.",
        "fields": [
            {"q": "Business overview", "a": LONG},
            {"q": "Operating history (two years or more)", "a":
                "{{LEGAL_NAME}} was formed in {{STATE}} in {{FORMED}} and has operated "
                "continuously since. Over that time we have [name two or three milestones: "
                "the first working Band, first customers or testers, first hire]. Today the "
                "product is at this stage: {{STAGE}}. We have {{EMPLOYEES}} people on the "
                "team and our revenue over the last 12 months was {{REVENUE}}."},
            {"q": "Minority ownership and control", "a":
                "{{LEGAL_NAME}} is at least 51% owned and controlled by minority owners "
                "({{MINORITY_BASIS}}). Ownership: {{OWNERSHIP}}. {{CEO}} directs day-to-day "
                "operations. The operating agreement and cap table are attached as proof."},
            {"q": "Community served and how the grant benefits it", "a":
                "Personal health insight has become a subscription product. The best-known "
                "wearables put the interpretation behind a recurring monthly fee. That fee "
                "prices out the households with the most avoidable health risk and the least "
                "time to manage it.\n\n"
                "Vybe removes the fee. A person buys the Band once and the answers come with "
                "it.\n\n"
                "With this grant we will place Vybe Bands with [number] residents of low- to "
                "moderate-income neighborhoods through [partner organization, such as a "
                "community health center or veteran service organization], and hire [number] "
                "people from those neighborhoods to onboard users in person. Onboarding in "
                "person matters: the product only helps someone who can get a useful answer "
                "on the first day.\n\n"
                "We will report at 90 and 180 days: residents actively using the Band, jobs "
                "created, and the share of users who say an answer changed what they did."},
            {"q": "Use of funds (suggested split for $200,000 — replace with your real costs)", "a":
                "Payroll: two hires, a community onboarding lead and an engineer — $90,000\n"
                "Inventory: Vybe Bands for the community pilot — $60,000\n"
                "Working capital: manufacturing deposits and operating reserve — $30,000\n"
                "Rent, utilities and software — $20,000\n"
                "Total: $200,000\n\n"
                "Every line is an allowed use under the program: payroll, inventory, working "
                "capital and day-to-day operating expenses."},
            {"q": "Jobs and outcomes", "a":
                "The grant creates [number] jobs within six months, at least [number] filled "
                "by residents of the communities the pilot serves. It puts [number] Bands on "
                "people who would not otherwise have access to this kind of insight, and it "
                "carries Vybe from {{STAGE}} to a product in daily use outside our team."},
        ],
    },
    {
        "id": "amber",
        "name": "Amber Grant for Women",
        "funder": "WomensNet",
        "amount": "$10,000 monthly (three awards a month), plus $50,000 year-end",
        "deadline": "2026-09-30",
        "fee": "$15 non-refundable application fee",
        "url": "https://ambergrantsforwomen.com/get-an-amber-grant/",
        "submit": "Short online form, applied by the woman owner. Applying by 30 September enters the September round; winners are announced by the 21st of the following month. One application also enters you for the Startup Grant (if sales are under $10,000) and any Business Category Grant for 12 months.",
        "gates": [],
        "confirmed": ["51%+ woman-owned (confirmed 20 Sep)"],
        "why": "Running since 1998 with no revenue floor, so it works before Vybe has sales. A pre-revenue Vybe is also automatically considered for the $10,000 Startup Grant. The $15 fee is the only cost.",
        "docs": [],
        "note": "Judges read these as a person talking about her business. The bracketed sentence about why you started Vybe matters more than any polish here; write it yourself.",
        "fields": [
            {"q": "Tell us about yourself and your business", "a":
                "I'm {{WOMAN_OWNER}}, and I lead {{LEGAL_NAME}}. [One or two sentences in your "
                "own words: why you started Vybe.]\n\n"
                "Most wearables stop at the score. They tell you your heart-rate variability "
                "dropped and leave you to work out why. Vybe is built for the step after the "
                "number. Our screenless Vybe Band tracks ECG, heart-rate variability, sleep "
                "and activity, and Vybe Intelligence reads those signals alongside the rest "
                "of your life, like stress, work, travel and weather. You ask a plain "
                "question, such as \"Why am I tired today?\", and get an answer from your own "
                "data with one next step.\n\n"
                "There is no required subscription. The answers come with the Band. Today we "
                "are at this stage: {{STAGE}}."},
            {"q": "What would you do with the grant?", "a":
                "Put Vybe on the wrists of its first [number] people outside our team. The "
                "$10,000 covers at-cost Bands for that group and six weeks of hands-on "
                "onboarding. That test answers the question our business depends on: can a "
                "person, not an engineer, get a useful answer about their own health on the "
                "first day? What they tell us shapes the product we take to market."},
        ],
    },
    {
        "id": "sharktank",
        "name": "Veteran Shark Tank 2026 (13th annual)",
        "funder": "Veteran Shark Tank — Philadelphia",
        "amount": "$50,000 to the winner; five veterans pitch live on 7 December 2026",
        "deadline": "2026-10-13",
        "fee": None,
        "url": "https://veteransharktank.com/apply/",
        "submit": "Submit the application form at veteransharktank.com/apply with a pitch video of 2 minutes or less and a deck of no more than 10 slides. The committee judges the video and the deck together, as one package, the way the live competition does. If something fails the criteria you get five days from notice to fix and resubmit. Questions go to info@veteransharktank.com.",
        "gates": ["under3"],
        "confirmed": ["Veteran-owned 51%+ (confirmed 20 Sep)"],
        "why": "The one live item on the board whose age test runs in Vybe's favour: the business must be UNDER three years old, where Buckeye wants two years and Tadlock one. Biggest single cheque Vybe currently qualifies for, and the 2016 winner was NeuroFlow, a behavioural-health platform, so the judges have backed health tech before.",
        "docs": [
            "Proof of veteran status (DD-214 or equivalent)",
            "Pitch video, 2 minutes maximum — narrated, not a promo",
            "Deck, 10 slides maximum, covering the six sections below in this order",
            "Evidence the business is under three years old as of 7 Dec 2026",
        ],
        "note": "This is a pitch, not a grant form: the committee is buying a person as much as a company. The video should be you talking, not a product reel — they say so explicitly. Financials below are left as bracketed prompts on purpose; a projection is a claim about your own business and nobody else should write it for you.",
        "fields": [
            {"q": "Video spine — what the business is, and why it belongs in Veteran Shark Tank 2026 (2 minutes, narrated)", "a":
                "I'm {{VETERAN_OWNER}}, and I'm building Vybe at {{LEGAL_NAME}}.\n\n"
                "Every wearable hands you a number. None of them tell you why it moved. "
                "Vybe is built for the step after the number: the screenless Band reads your "
                "heart, sleep and movement, and Vybe Intelligence reads those signals next to "
                "the life around them — a hard week, a long flight, a heat wave. You ask "
                "\"Why am I tired today?\" and you get an answer out of your own data, the "
                "evidence behind it, and one thing to do.\n\n"
                "There is no required subscription. The interpretation comes with the Band.\n\n"
                "We are at this stage: {{STAGE}}. {{TRACTION}}.\n\n"
                "[Close in your own words: why a veteran is the right person to build a "
                "product about recovery and readiness, and what $50,000 changes in the next "
                "six months. This is the part the judges remember — keep it yours.]"},
            {"q": "Slide — Market: size, growth, competition and regulatory dynamics", "a":
                WHY_NOW + "\n\n"
                "Regulatory position: Vybe is a consumer wellness product. It is not a "
                "medical device, makes no diagnostic claim and needs no clearance to ship, "
                "which is why it can reach people now rather than after a trial."},
            {"q": "Slide — Product and value proposition", "a": SHORT},
            {"q": "Slide — Go-to-market: customer acquisition strategy and cost", "a":
                "The Band is bought once, so the first sale is the whole relationship — no "
                "subscription to win and no churn to fight.\n\n"
                "Three routes, in the order we intend to open them:\n"
                "1. Direct, to people already unhappy about paying monthly for their own "
                "numbers. That grievance is specific and easy to find.\n"
                "2. The veteran and military-family community, where recovery and readiness "
                "are already the language people use.\n"
                "3. Licensing the interpretation layer to partners who have hardware and no "
                "answer to give with it.\n\n"
                "[Your numbers: what a customer costs you to acquire today, through which "
                "channel, and what you have actually spent to learn that. If you do not know "
                "yet, say so and say what you will test first — a made-up CAC is the "
                "fastest way to lose a judge who has run a business.]"},
            {"q": "Slide — Customers: profile and attractiveness", "a":
                "The person who buys Vybe already owns a wearable and has stopped opening it. "
                "They have the data and none of the meaning, and they resent paying a monthly "
                "fee to be told a number they can already see.\n\n"
                "[Describe who you have actually talked to: how many, how you reached them, "
                "and the one sentence you heard most often. Real quotes beat a persona.]\n\n"
                "Beyond consumers, Vybe is a platform: developers, researchers and employers "
                "need interpretation they can build on, and none of them want to build a "
                "sensor stack to get it."},
            {"q": "Slide — Financials: current and projected model", "a":
                "[This slide is yours to write, and only you can. The committee asks for "
                "sales, cost of goods sold, operating expenses and expected profit, current "
                "and projected. Give them:\n"
                "- unit economics: what a Band costs to make and what it sells for\n"
                "- revenue to date, even if it is zero — say zero rather than dress it up\n"
                "- monthly operating cost and how long your runway is\n"
                "- a projection with the two or three assumptions it rests on named\n"
                "Judges forgive a small number. They do not forgive a number you cannot "
                "explain.]"},
            {"q": "Slide — Key risks and mitigants", "a":
                "Hardware execution. A screenless band has to be manufactured and it has to "
                "be reliable. [Name where you are with your manufacturer and what is de-risked "
                "so far.]\n\n"
                "A big wearable adds real interpretation. Possible, and the reason to be "
                "early. Our answer is the context layer — Connect, the part that reads work, "
                "travel and stress — which is harder to copy than a score, plus a "
                "buy-once model an incumbent with subscription revenue cannot match without "
                "hurting itself.\n\n"
                "Trust. We ask people for health data and the whole product depends on their "
                "believing we will not sell it. Mitigation is structural rather than stated: "
                "the data lives on the person's phone, the app shows them where every piece "
                "of it sits, and export and delete are one tap from the home screen.\n\n"
                "Staying a wellness product. Any drift toward a diagnostic claim pulls Vybe "
                "into a regulatory path it is not funded for, so the claim boundary is a "
                "product rule, not a marketing preference."},
        ],
    },
    {
        "id": "tadlock",
        "name": "Stephen L. Tadlock Veteran Business Grant",
        "funder": "Founders First CDC",
        "amount": "$1,000 micro-grant plus a free program place (Passport or Zebra)",
        "deadline": "2026-10-15",
        "fee": None,
        "url": "https://foundersfirstcdc.org/stephen-tadlock",
        "submit": "Online application, open since 15 September, closes 15 October. Semifinalists announced 22 October, finalists 10 November. The veteran applies as CEO, President or owner.",
        "gates": ["years1", "staff2"],
        "confirmed": ["Veteran-owned (confirmed 20 Sep)", "Revenue under $5M"],
        "why": "Small cash, but the Passport program (weekly sessions on marketing, sales, operations and finance, worth $1,499) fits where Vybe is. Two hard gates: at least one year in business and 2 to 100 employees.",
        "docs": ["DD-214 or other proof of service may be requested"],
        "note": "",
        "fields": [
            {"q": "Describe your business", "a": SHORT},
            {"q": "Your military service", "a":
                "{{VETERAN_OWNER}}. [Two sentences in your own words: what you did in service "
                "and one thing it taught you that you use running Vybe.]"},
            {"q": "How would you use the $1,000?", "a":
                "[Choose one and keep it specific:] a radio pre-scan ahead of the Band's FCC "
                "certification / filing the VYBE trademark / at-cost Bands for our first ten "
                "outside testers. A small grant does the most good on one named cost."},
            {"q": "Which program, and why?", "a":
                "Passport Community. Vybe's next step is getting from {{STAGE}} to paying "
                "customers, and Passport's weekly sessions cover the four things that step "
                "depends on: marketing, sales, operations and finance."},
        ],
    },
    {
        "id": "toryburch",
        "name": "Tory Burch Foundation Fellows — 2027",
        "funder": "Tory Burch Foundation",
        "amount": "Fellowship place (about 120 chosen): coaching, advisors, peer network",
        "deadline": "2026-11-17",
        "fee": None,
        "url": "https://fellows.toryburchfoundation.org/prog/2027_fellows_program/",
        "submit": "Online only, one applicant per business: the woman who owns the largest or equal-largest stake and manages the business day to day. Include a photo (JPG, GIF or PNG, under 2 MB) and a video of up to 2 minutes.",
        "gates": ["rev75"],
        "confirmed": ["51%+ woman-owned (confirmed 20 Sep)"],
        "why": "The Foundation's terms require a revenue-generating business with at least $75,000 a year. If Vybe is below that, skip this cycle; the gate is firm. A business plan is optional.",
        "docs": ["Photo of the applicant, under 2 MB", "Video, 2 minutes or less (script below)"],
        "note": "The revenue floor is stated in the Foundation's terms for the 2026 cycle; the 2027 page shows no change. Confirm in the 2027 rules when you open the form.",
        "fields": [
            {"q": "Describe your business", "a": LONG},
            {"q": "Your biggest challenge right now", "a":
                "Moving from {{STAGE}} to a first production run while keeping the product "
                "free of a required subscription. Hardware companies usually fund that step "
                "with recurring fees. We have chosen not to charge them, so the product has "
                "to earn its way through the Band itself, partnerships and licensing."},
            {"q": "What you want from the Fellowship", "a":
                "Advisors who have taken a consumer hardware product through manufacturing "
                "and into retail, and peers a year or two ahead who have made the pricing "
                "decisions we are making now."},
            {"q": "Video script (about 2 minutes)", "a":
                "I'm {{WOMAN_OWNER}}, and I lead {{LEGAL_NAME}}.\n\n"
                "[Hold up the Band.] This is the Vybe Band. It has no screen, on purpose. It "
                "tracks your heart, your sleep and how you move.\n\n"
                "Every wearable gives you a number. Your sleep score is 71. Your heart-rate "
                "variability is down. Then it stops, and you're left asking why.\n\n"
                "Vybe answers the why. You ask a plain question, like \"Why am I tired "
                "today?\", and Vybe looks at your body and the life around it: the hard week "
                "at work, the late flight, the heat. You get an answer from your own data and "
                "one thing to do next.\n\n"
                "And there's no required subscription. The answers come with the Band. Health "
                "insight shouldn't be a monthly bill.\n\n"
                "[One sentence in your own words: why this matters to you.]\n\n"
                "We're at this stage: {{STAGE}}. The Fellowship would put me in a room with "
                "women who have taken hardware to market. That's the step in front of us."},
        ],
    },
    {
        "id": "penfed",
        "name": "Veteran Entrepreneur Program — Accelerator",
        "funder": "The PenFed Foundation for Military Heroes",
        "amount": "No cash award: a free place, travel and meals covered, zero equity taken — plus eligibility for the year-end Pitch Competition, which awards non-dilutive funding",
        "deadline": "rolling",
        "fee": None,
        "url": "https://penfedfoundation.org/our-programs/accelerator/",
        "submit": "One multi-step form, linked from the VEP page. The selection committee reviews applications monthly, then invites shortlisted founders to an interview. An application that is not selected is held on file for a full calendar year and reconsidered for later cohorts, so submitting between cohorts costs nothing. Five Accelerator cohorts run each year; the Incubator dates on the form are Tysons 17-19 June, New York 12-14 August and Boston 14-16 October 2026.",
        "gates": ["incorp", "inperson"],
        "confirmed": ["Veteran-owned 51%+ (confirmed 20 Sep)"],
        "why": "The strongest non-cash item on the board, and the gate is one Vybe already clears: majority veteran-owned. No fee, no equity, flights and hotels paid, and the Accelerator feeds a year-end pitch competition whose prize is non-dilutive. It is also the rare rolling application that does not expire — held on file for a year — so there is no deadline to miss. The Foundation says it is industry agnostic but gives priority to national security and defense businesses, which is worth knowing before writing the answers.",
        "docs": [
            "Member-4 DD-214 for the veteran owner (the form asks you to confirm you can produce it)",
            "EIN and state formation documents",
            "Company website",
            "Availability for four days in person plus six weeks of mentoring",
        ],
        "note": "The form routes you to the Accelerator or the Incubator based on one answer — the product's stage. Accelerator is for a validated or launched product with early traction; Incubator is for an idea with no product or revenue. The answers below are written for the Accelerator; if the honest stage answer is pre-MVP, the same material still applies but the cohort is the Incubator and the commitment is three days rather than four. Nothing here fills in the stage for you.",
        "fields": [
            {"q": "Military service and veteran status", "a":
                "Veteran owner: {{VETERAN_OWNER}}.\n\n"
                "The form asks for service status from a list (active duty, retired, "
                "reserves or guard, spouse, separated, medically retired) and then asks you "
                "to confirm you can produce a Member-4 DD-214. It also states plainly that "
                "the nature of the separation is considered in review. Answer it as it is."},
            {"q": "Brief founder bio: military and professional background, and other experience relevant to your company", "a":
                "[This one is yours and nobody should draft it for you. What the reviewers "
                "are looking for, from their own selection criteria, is leadership and "
                "coachability — so the useful shape is: what you were responsible for in "
                "service, what you did after it, and the specific thing in that history that "
                "makes you the person to build a product about recovery and readiness. Two "
                "short paragraphs beats a resume.]"},
            {"q": "What stage of development is your product or service in?", "a":
                "{{STAGE}}\n\n"
                "Pick the option on the form that matches that sentence — the list runs "
                "concept, research and validation, prototype/MVP, pilot/beta, pre-launch, "
                "launched, revenue-generating, growth and scaling. This single answer decides "
                "which programme you are offered, so it is worth answering precisely rather "
                "than optimistically."},
            {"q": "Main industry and sub-type", "a":
                "Healthcare & Life Sciences. Sub-type: consumer digital health and wearables.\n\n"
                "Say in the description that Vybe is a consumer wellness product, not a "
                "medical device, and makes no diagnostic claim. Reviewers in this category "
                "will assume a regulatory pathway unless told otherwise, and Vybe's ability "
                "to ship without one is an advantage rather than a gap."},
            {"q": "Provide a brief description of your company and the product/service you provide", "a": SHORT},
            {"q": "What problem does your company solve?", "a":
                "People own the data and not the meaning.\n\n"
                "A wearable reports that heart-rate variability fell 18% and stops there. The "
                "person is left to guess whether it was the late dinner, the bad night, the "
                "flight or the week they have had — and most of them stop opening the app. "
                "The measurement problem is solved; the interpretation problem is not.\n\n"
                "Vybe answers the question the number raises. It reads the signals alongside "
                "the context around them and replies in a sentence, with the evidence it used "
                "and one thing to do next."},
            {"q": "How is your product/service different than what is already on the market?", "a":
                WHY_NOW + "\n\n"
                "Two differences, and the second is the durable one:\n\n"
                "The interpretation is not a subscription. The Band is bought once and the "
                "answers come with it.\n\n"
                "The context layer. Vybe reads five parts of a life — Restore, Move, Nourish, "
                "Connect and Vitals — and Connect is the one competitors leave out: work, "
                "travel, stress and weather, the reasons a reading moves that no sensor can "
                "see. A score is easy to copy. A model of somebody's week is not."},
            {"q": "Who is your target market?", "a":
                "The person who already owns a wearable and has stopped looking at it. They "
                "have years of their own data, no answers from it, and a monthly fee for the "
                "privilege.\n\n"
                "Two segments beyond that, both reachable without consumer-scale marketing: "
                "the veteran and military-family community, where recovery and readiness are "
                "already the everyday language; and platform customers — developers, "
                "researchers and employers who need interpretation they can build on and do "
                "not want to build a sensor stack to get it.\n\n"
                "[If you have specific numbers on who you have reached so far, put them here "
                "instead of a description.]"},
            {"q": "Have you conducted any market validation? If yes, describe the type of validation and the key findings", "a":
                "What is established: {{TRACTION}}.\n\n"
                "[The rest is yours, and this is the answer the committee weighs most heavily "
                "for the Accelerator, because 'validated' is in their entry criteria. Say how "
                "many people you have actually spoken to, how you reached them, and the "
                "sentence you heard most often. If the validation so far is a waitlist and a "
                "set of conversations, say exactly that — an honest small number reads as "
                "evidence, and an invented survey reads as a company that does not know its "
                "own customers.]"},
            {"q": "How do you plan to generate revenue?", "a":
                "Hardware sold once, at a margin, with the intelligence included. No required "
                "subscription — which is the position, not a discount.\n\n"
                "Then licensing: the interpretation layer sold to partners who have sensors "
                "and nothing to say with the readings. That is the same product doing "
                "second-hand work, so it costs little to serve.\n\n"
                "[Your numbers: what a Band costs to build and what it sells for. Do not "
                "publish a price here that you have not decided.]"},
            {"q": "Do you currently have revenue? If so, enter the annual amount", "a":
                "{{REVENUE}}\n\n"
                "The form says to enter 0 if there is none. Enter 0. A pre-revenue answer is "
                "not a disqualifier for either track — it is one of the inputs that decides "
                "which one you are offered."},
            {"q": "Formation: EIN and state filing", "a":
                "EIN {{EIN}}, formed in {{STATE}} in {{FORMED}}, operating from {{CITY}}. "
                "Website {{WEBSITE}}.\n\n"
                "The Accelerator section asks you to tick that the business has an EIN and "
                "has filed formation documents with the state. Both are true for Vybe."},
        ],
    },
    {
        "id": "xtech",
        "name": "Army xTech|Search 10",
        "funder": "U.S. Army FUZE xTech Program, ASA(ALT)",
        "amount": "Up to $1,000,000 in non-dilutive prizes across the competition — $5,000 to each of up to 50 semifinalists, a further $20,000 to each of up to 20 finalists, then $200,000 / $100,000 / $50,000 — plus a Phase I Army SBIR or STTR proposal worth up to $300,000 for finalists",
        "deadline": "2026-10-19",
        "fee": None,
        "url": "https://xtech.army.mil/competition/xtechsearch10/",
        "submit": "Submit a concept white paper through the xTech portal linked from xtech.army.mil/competitions by 5pm ET on 19 October 2026. One submission per company. Semifinalists pitch virtually 18-29 January 2027, finalists demonstrate at eMerge Americas in Miami 2-4 March 2027, and the SBIR/STTR window runs to 30 April 2027.",
        "gates": ["incorp", "uscitizen", "nodupfed"],
        "confirmed": [
            "Veteran-owned 51%+ (confirmed 20 Sep)",
            "Fewer than 500 employees — a 3-person company cannot fail this ceiling",
        ],
        "why": "The largest non-dilutive opportunity on the board and the only one that names Vybe's category in the Army's own words: one of the four published priority portfolios is 'Immersive and Wearables — smart electronic devices that can be worn by or attached to the user to gather data or provide insight'. It is open-topic, so there is no stated problem to contort the product into; it is free; it takes no equity; and $5,000 lands at the semifinal stage, which is a real outcome for a white paper rather than a lottery ticket.",
        "docs": [
            "Concept white paper submitted through the xTech portal",
            "Eligibility attestation: for-profit, more than 50% owned and controlled by US citizens or permanent residents, 500 or fewer employees including affiliates",
            "Disclosure of any substantially similar proposal funded, being funded, or pending award at another federal agency",
            "SAM.gov UEI and a CAGE code — needed for the Phase I SBIR/STTR stage, not for the white paper",
        ],
        "note": (
            "THE RFI PDF WAS NOT READABLE FROM HERE, so the exact white paper format — section "
            "headings, page limit, file type — is not confirmed. Section IV of the RFI has it, and "
            "it is the first thing to open. The sections below are drafted against what the "
            "competition's own page publishes that it weighs: the solution's advantage, its "
            "technical viability, its commercial potential, and a clear line to an Army need.\n\n"
            "THE EXCLUSION THAT DECIDES THIS APPLICATION. The page states that technologies "
            "falling EXCLUSIVELY within the U.S. Army Medical Research and Development Command "
            "portfolio — military operational medicine, clinical and rehabilitative medicine, "
            "infectious disease, CBRN — are excluded from xTech|Search. Vybe is a commercial "
            "consumer wearable with a dual-use readiness application. That is true, and it is also "
            "the only framing under which this is eligible. The temptation with a defence "
            "application is to sound more serious by sounding more clinical. Here that is the "
            "sentence that makes the submission ineligible, so every answer below stays on the "
            "wellness side of the line on purpose.\n\n"
            "Financials, manufacturing status and anything about customer conversations are left "
            "as bracketed prompts. Judges comparing unlike technologies lean on evidence of real "
            "commercial traction, and a number nobody can stand behind is worse than a small one."
        ),
        "fields": [
            {"q": "Technology description — what it is, in plain terms", "a": LONG},
            {"q": "One-line summary", "a": ONE_LINER},
            {"q": "The Army need it addresses", "a":
                "A soldier's readiness is already being measured. Wrist and ring wearables are "
                "common in the force, and the sensors report heart rate, heart-rate variability, "
                "sleep and movement. What none of them do is say what the numbers mean for this "
                "person, this week, given what has actually happened to them.\n\n"
                "That gap is an interpretation problem, not a sensor problem, and it is the one "
                "Vybe is built to close. The published priority areas include multi-domain force "
                "readiness across dispersed formations and soldier support across distributed "
                "environments. Readiness data that nobody can read is the same as no readiness "
                "data, and the cost of the gap is carried by leaders making training and rest "
                "decisions on a number with no explanation attached.\n\n"
                "Vybe's answer is the Connect layer: the part that reads context a sensor cannot "
                "see — schedule, travel, heat, workload — and uses it to explain why a signal "
                "moved. Vybe is a wellness product and stays one. It supports a decision about "
                "training and rest. It does not diagnose, screen, or triage, and nothing in this "
                "submission asks the Army to treat it as though it does.\n\n"
                "[If there is a specific unit, programme or military user you have actually "
                "spoken to, name them here and say what they told you. If there is not, say so "
                "plainly — the competition explicitly welcomes companies that do not yet know "
                "the Army problem their technology solves.]"},
            {"q": "Technical advantage over what already exists commercially", "a":
                "Three things, and the third is the one that is hard to copy.\n\n"
                "1. Interpretation, not scoring. Every competitor returns a number and leaves the "
                "reasoning to the user. Vybe returns a sentence, the evidence behind it, and one "
                "action — and it states what it could not see, which is the part that keeps it "
                "honest.\n\n"
                "2. Context as an input, not a footnote. Work, travel, heat and schedule change "
                "physiological readings. Vybe models them as signals. A score computed from the "
                "sensor alone cannot be corrected after the fact by a user note.\n\n"
                "3. No required subscription. The interpretation ships with the Band. This is a "
                "commercial advantage, but it is also a structural one against incumbents: a "
                "company living on monthly revenue cannot match buy-once without cutting its own "
                "income.\n\n"
                + WHY_NOW},
            {"q": "Technical viability and maturity", "a":
                "Where the product is today: {{STAGE}}.\n\n"
                "The physiological sensing is established engineering — ECG, photoplethysmography, "
                "accelerometry — and the risk does not sit there. It sits in the interpretation "
                "layer, which is why that is where the work and the evidence are.\n\n"
                "[This section needs your real numbers, and only you have them:\n"
                "- Technology readiness level, and what you are basing that on\n"
                "- What the Band measures today versus what it is specified to measure\n"
                "- How the interpretation layer is built and what it has been validated against\n"
                "- Manufacturing status: who is building the Band, what stage that is at, and "
                "what is already de-risked\n"
                "- Any bench, field or user data you can actually show\n"
                "A reviewer who works with hardware will know immediately if a maturity claim is "
                "generous. An honest early-stage answer with a clear roadmap beats an inflated "
                "one.]"},
            {"q": "Commercial potential and traction", "a":
                "Vybe is a commercial product first, which is the shape this competition asks "
                "for: technologies with commercial traction that may also serve the Army.\n\n"
                "The buyer is someone who already owns a wearable and has stopped opening it. "
                "They have the data and none of the meaning, and they resent paying monthly to be "
                "shown a number they can already see. The Band is bought once, so the first sale "
                "is the whole relationship.\n\n"
                "Beyond direct sales, the interpretation layer licenses: other manufacturers have "
                "sensors and nothing to say with them.\n\n"
                "Current position: revenue {{REVENUE}}; {{TRACTION}}; team of {{EMPLOYEES}}.\n\n"
                "[Add what you can evidence: pre-orders, pilots, letters of intent, partner "
                "conversations, or money raised. If the honest answer is a waitlist and nothing "
                "else, say that. Overstating traction to a panel that reads hundreds of these is "
                "the cheapest way to lose.]"},
            {"q": "Transition path — what a follow-on Phase I would demonstrate", "a":
                "The competition's Phase I asks for a feasibility study and a concept "
                "demonstration, so the proposal writes itself from what is genuinely unproven: "
                "whether the interpretation layer holds up on people under sustained physical "
                "load rather than on consumers going about a normal week.\n\n"
                "A six-month Phase I would put that to the test: run the Band and the "
                "interpretation layer against a defined training population, compare what Vybe "
                "says about recovery with what the people and their leaders already observe, and "
                "report where it agrees, where it does not, and what the system refuses to answer.\n\n"
                "The commercial path is unchanged either way, which is the point of dual use: the "
                "product ships to consumers regardless, and the Army work makes the interpretation "
                "better rather than forking it.\n\n"
                "[Budget: a Phase I is capped at $300,000 over six months. A suggested split to "
                "replace with your own — roughly 60% engineering time, 20% hardware and field "
                "instrumentation, 10% data and analysis, 10% programme management. These are a "
                "starting shape, not costed figures.]"},
            {"q": "Eligibility statement", "a":
                "{{LEGAL_NAME}} is a for-profit small business, formed in {{STATE}} in {{FORMED}}, "
                "operating from {{CITY}}, EIN {{EIN}}. Ownership: {{OWNERSHIP}}. Employees "
                "including founders: {{EMPLOYEES}}, well inside the 500 ceiling.\n\n"
                "[Confirm before you submit, because these are the three things that end an "
                "application:\n"
                "- More than 50% of the equity is owned AND controlled by US citizens or "
                "permanent residents. Both words matter; a control arrangement can fail this "
                "even when the cap table passes.\n"
                "- This submission is not substantially the same as any proposal funded, being "
                "funded, or pending award at another federal agency. If anything is close, the "
                "competition says to disclose it early rather than hope.\n"
                "- One submission per company. Pick the strongest framing and send that one.]"},
            {"q": "Why this is not a medical technology", "a":
                "Worth stating plainly in the submission rather than leaving a reviewer to "
                "wonder, because the exclusion is specific.\n\n"
                "Vybe is a consumer wellness product. It is not a medical device, it holds no "
                "device classification, it makes no diagnostic or therapeutic claim, and it needs "
                "no clearance to ship — which is why it is on shelves rather than in a trial. It "
                "does not screen for conditions, and when a user asks it a clinical question it "
                "declines and says to see a clinician.\n\n"
                "What it does is read a person's own signals and explain them. That is a "
                "human-performance and readiness capability of the ordinary commercial kind, and "
                "it does not fall within the Army Medical Research and Development Command "
                "portfolio the competition excludes."},
        ],
    },
    {
        "id": "techcred",
        "name": "Ohio TechCred — October 2026 round",
        "funder": "Ohio Department of Development",
        "amount": "Reimbursement of up to $1,000 per person per credential, capped at $30,000 per application period",
        "deadline": "2026-10-30",
        "fee": None,
        "url": "https://development.ohio.gov/business/workforce-development/tech-cred/apply",
        "submit": "Apply online at development.ohio.gov/TechCred. The window opens 9:00am on 1 October 2026 and closes 3:00pm on 30 October 2026. One application per federal tax ID per period. It is competitive and merit-based rather than first come, first served, and review can take up to 90 days. Training must start on or after the first day of the application period and finish within 12 months.",
        "gates": ["ohiosite", "w2ohio"],
        "confirmed": [
            "Operating from Ohio — the company works out of Akron",
        ],
        "why": "The nearest live deadline on the board and the only one that pays for something Vybe has to buy anyway. It is a cost offset, not a cheque: up to $30,000 back on technology credentials for people already on the payroll or about to be. Worth doing because the window is short, the form is mostly facts rather than persuasion, and a company that misses it waits a full round.",
        "docs": [
            "Federal tax ID",
            "Ohio Payee ID Number from ohiopays.ohio.gov",
            "Ohio Secretary of State charter or entity number from businesssearch.ohiosos.gov",
            "Physical, non-residential Ohio business address",
            "Number of Ohio W-2 employees",
            "For each credential: the training provider from Ohio's eligible list, training cost, certification test cost, and the reimbursement requested",
            "Headcounts of incumbent and prospective employees per credential, with average wages before and after",
        ],
        "note": (
            "READ THE TWO GATES FIRST, BECAUSE THEY DECIDE WHETHER ANY OF THIS IS WORTH "
            "TYPING. TechCred needs a physical, NON-RESIDENTIAL business location in Ohio, "
            "and it needs Ohio-resident W-2 employees who are reported to the Ohio "
            "Unemployment Insurance Office with Ohio income tax withheld. Contractors and "
            "1099 workers do not count for anything here. A three-person company working "
            "from home, or one whose founders take no W-2 wage, fails before the credentials "
            "are chosen — and the reimbursement stage asks for each earner's wage, hire date "
            "and W4/IT4 verification, so this is not a gate that can be finessed later.\n\n"
            "Two more things worth knowing before the window opens. The programme was "
            "reframed in July 2026 with a tighter technology-focused credential definition "
            "and a NEW list of eligible training providers, so any provider chosen from "
            "older advice has to be re-checked against the current list — and the provider "
            "must be independent of Vybe, with no shared ownership or management. And the "
            "money is a reimbursement: Vybe pays the provider, then claims, with an itemised "
            "invoice and proof of payment showing Vybe as the payer. Payment typically "
            "arrives within 60 days of an approved request.\n\n"
            "The application itself does NOT ask you to name individuals — only how many "
            "incumbent and prospective employees will earn each credential, with average "
            "wages before and after. The credential choices and the cost figures below are "
            "left as bracketed prompts because they depend on which providers are on the "
            "current eligible list and what they actually charge, neither of which can be "
            "invented. Check the Eligible Credential List on the apply page first, then fill "
            "these in from real quotes."
        ),
        "fields": [
            {"q": "Employer information", "a":
                "Employer name: {{LEGAL_NAME}}\n"
                "Federal Tax ID: {{EIN}}\n"
                "Physical, non-residential business address: [the Ohio premises — NOT a home "
                "address, and not a registered-agent address. If Vybe has no non-residential "
                "Ohio location, this is where the application stops.]\n"
                "Website: {{WEBSITE}}\n"
                "Point of contact: {{CEO}}, {{EMAIL}}\n"
                "Number of Ohio W-2 employees: [how many people are on an Ohio W-2, reported "
                "to Ohio unemployment insurance. Founders drawing no wage do not count.]\n\n"
                "[Two numbers you have to fetch rather than remember:\n"
                "- Payee ID Number — register or look it up at ohiopays.ohio.gov\n"
                "- Ohio Secretary of State charter or entity number — businesssearch.ohiosos.gov. "
                "Vybe is formed in {{STATE}}, so if it has not filed as a foreign entity in "
                "Ohio there will be no number to enter, and that filing has to happen first.]"},
            {"q": "Employer's industry", "a":
                "Healthcare and life sciences — consumer digital health and wearables.\n\n"
                "Worth adding in any free text that Vybe is a consumer wellness product, not a "
                "medical device, and makes no diagnostic claim. A reviewer in this category "
                "will otherwise assume a regulatory pathway, and Vybe's ability to ship "
                "without one is an advantage rather than a gap."},
            {"q": "What the company does (for any description field)", "a": SHORT},
            {"q": "Credential 1 — what to train and why it is technology-focused", "a":
                "[Choose from the Eligible Credential List on the apply page. What TechCred is "
                "buying here is a short, technology-focused credential, so the ones that fit "
                "the work Vybe actually does are in embedded firmware, wireless and Bluetooth "
                "Low Energy, data engineering, applied machine learning, and mobile "
                "development. Name the one the person will genuinely use, not the one that "
                "sounds most impressive.]\n\n"
                "Training provider: [must be on Ohio's current eligible list, and must be "
                "independent of Vybe — no shared owners, no shared management.]\n"
                "Training cost: [from a real quote]\n"
                "Certification test cost: [from a real quote]\n"
                "Total actual cost: [the two added together]\n"
                "Reimbursement requested: [up to $1,000]\n\n"
                "If the credential Vybe needs is not on the list, select “Credential Not "
                "Listed” and supply the provider's own outline, the learning objectives, "
                "evidence the skills are technology-focused, and evidence the credential has "
                "value beyond Vybe. That is a real piece of work, not a checkbox."},
            {"q": "Credential 2 and beyond", "a":
                "[Repeat the block above for each credential. The cap is $1,000 per person per "
                "credential and $30,000 per application, and multiple credentials for the same "
                "person are allowed — so the arithmetic that reaches $30,000 is people "
                "multiplied by credentials, not one large course.\n\n"
                "A suggested shape to replace with your own, once the eligible list is open: "
                "one firmware or BLE credential for whoever owns the Band, one data or applied "
                "ML credential for whoever owns Vybe Intelligence, and one mobile credential "
                "for whoever owns the app. Three credentials across three people is $3,000 at "
                "the cap — a long way under $30,000, which is the honest size of this "
                "opportunity for a company of Vybe's headcount.]"},
            {"q": "Trainee information per credential", "a":
                "[The form asks for counts, not names:\n"
                "- Number of INCUMBENT W-2 employees who will earn each credential, with their "
                "average current hourly wage and average expected wage after\n"
                "- Number of PROSPECTIVE W-2 employees who will earn each credential, with the "
                "average wage they would have earned without it and the average expected wage "
                "after\n\n"
                "Prospective hires are allowed, which is the flexible part of this programme — "
                "you can request funding for roles you plan to fill. But at reimbursement you "
                "have to name the person, prove they were hired, and supply their wage before "
                "and after, so do not claim for a role you are not confident of filling within "
                "12 months.]"},
            {"q": "How the training fits the business", "a":
                "The Band and the interpretation layer are built in-house, so the skills that "
                "limit Vybe are specific and identifiable: reliable firmware on a screenless "
                "device, Bluetooth that does not drop, and models that hold up on a real "
                "person's time series rather than a clean dataset.\n\n"
                "Credentials in those areas move work that would otherwise be contracted out "
                "onto the payroll, which is the outcome TechCred exists for. It also does "
                "something the grant cannot: contractors take the knowledge with them, and an "
                "employee who earns the credential keeps it inside the company.\n\n"
                "[If the form gives room, name the specific thing each credential unblocks. A "
                "reviewer comparing applications is reading for whether the training is real "
                "work or a shopping list.]"},
            {"q": "Before you submit — the timing rule that catches people", "a":
                "Training must start ON OR AFTER the first day of the application period and "
                "finish within 12 months of the award. Anything Vybe pays for before the grant "
                "agreement is executed is at Vybe's own risk and may not be reimbursed.\n\n"
                "So: do not enrol anybody before submitting, and do not pay an invoice hoping "
                "it will be covered retroactively. Submit in the window, wait for the executed "
                "agreement, then book the training.\n\n"
                "Also: if something is missing from the application and it was submitted at "
                "least 24 hours before the round closes, the programme will tell you what it "
                "needs. Submitting on 29 October rather than 30 October buys that safety net."},
        ],
    },
    {
        "id": "freed",
        "name": "Freed Fellowship Grant — monthly",
        "funder": "Freed Fellowship LLC",
        "amount": "$500 a month to one selected US business owner, no strings and no equity; monthly Fellows are then eligible for an additional $2,500 end-of-year grant",
        "deadline": "rolling",
        "fee": None,
        "url": "https://www.freedfellowship.com/grant",
        "submit": "Short online submission at freedfellowship.com/grant. One Fellow is selected every month, so a submission that does not win is a submission already made for the next round. Every submission — not just the winner — gets a written Freed score against the five-part framework plus two months inside the Freed Studio community.",
        "gates": [],
        "confirmed": [
            "US-based business owner with an existing business — no ownership, revenue, sector or age gate is published",
        ],
        "why": "The smallest money on the board and one of the most useful things on it, for one reason: every submission comes back with a written outside read on the business, scored against five named criteria. Vybe has $50,000 to $1,000,000 of applications in flight over the next month. Paying nothing to find out how a stranger scores the pitch, before those go in, is worth more than the $500.",
        "docs": [],
        "note": (
            "BE HONEST ABOUT THE SIZE OF THIS. It is $500 a month, with a $2,500 "
            "end-of-year grant open only to monthly Fellows. Nobody should spend a day on "
            "it. It earns a packet because the submission is short, it recurs every month "
            "so there is no deadline to miss, and the thing it returns — a score and "
            "written recommendations against Freed's five Cs — is the one piece of outside "
            "feedback on this board that arrives whether or not you win.\n\n"
            "Treat the answers below as the first draft of a reusable pitch rather than a "
            "grant application. The five headings are Freed's own, in their order: Context, "
            "Content, Community, Chemistry, Commerce. Where an answer needs a number only "
            "the founders have, it is a bracketed prompt — a made-up figure here would also "
            "corrupt the feedback, which is the entire point of applying.\n\n"
            "No application fee is named anywhere on the application page. Worth a second "
            "look at the form itself before submitting, since a fee appearing later would "
            "change the arithmetic on a $500 award."
        ),
        "fields": [
            {"q": "One-line summary", "a": ONE_LINER},
            {"q": "Context — why is the market in your favour?", "a":
                WHY_NOW + "\n\n"
                "The short version: the category split, and nobody took the position Vybe "
                "is taking. Deep interpretation without a required subscription is an empty "
                "space on the shelf, and it is empty because it costs the incumbents their "
                "recurring revenue to enter it."},
            {"q": "Content — what is your compelling core narrative?", "a":
                "People own the data and not the meaning.\n\n"
                "A wearable reports that heart-rate variability fell 18% and stops there. "
                "The person is left to guess whether it was the late dinner, the bad night, "
                "the flight or the week they have had — and most of them stop opening the "
                "app. The measurement problem is solved. The interpretation problem is not, "
                "and that is the whole company.\n\n"
                + SHORT},
            {"q": "Community — have you found or created a community?", "a":
                "Two, and neither needs consumer-scale marketing to reach.\n\n"
                "People who already own a wearable and have stopped opening it. The "
                "grievance is specific — paying monthly to be shown a number they can "
                "already see — which makes them findable in a way a general wellness "
                "audience is not.\n\n"
                "The veteran and military-family community, where recovery and readiness "
                "are already the everyday language rather than a wellness concept that has "
                "to be introduced. Vybe is veteran-, woman- and minority-owned, so this is "
                "a community the founders are in rather than one they are marketing at.\n\n"
                "Current position: {{TRACTION}}.\n\n"
                "[Add what you can evidence about the people you have actually reached: how "
                "many, through what, and the sentence you heard most often. Freed scores "
                "this heading on evidence of a real audience, and a waitlist described "
                "honestly reads better than a described persona.]"},
            {"q": "Chemistry — have you found your special sauce?", "a":
                "The context layer, and it is the part that is hard to copy.\n\n"
                "Vybe reads five parts of a life — Restore, Move, Nourish, Connect and "
                "Vitals — and Connect is the one competitors leave out: work, travel, "
                "stress and weather, the reasons a reading moves that no sensor can see. A "
                "score is easy to copy. A model of somebody's week is not.\n\n"
                "The second piece is restraint, and it is a product decision rather than a "
                "marketing one. Vybe states what it could not see alongside every answer, "
                "and when it is asked a clinical question it declines and says to see a "
                "clinician. It is a consumer wellness product, not a medical device, and "
                "holding that line is what lets it ship at all."},
            {"q": "Commerce — how do you make money?", "a":
                "The Band is bought once, at a margin, with the intelligence included. No "
                "required subscription — which is the position, not a discount.\n\n"
                "Then licensing: the interpretation layer sold to manufacturers who have "
                "sensors and nothing to say with the readings. Same product, second "
                "customer, little extra cost to serve.\n\n"
                "Revenue over the last 12 months: {{REVENUE}}. Team of {{EMPLOYEES}}. "
                "Product stage: {{STAGE}}.\n\n"
                "[Your unit economics: what a Band costs to build and what it sells for. "
                "This is the heading Freed scores hardest and the one where a number you "
                "cannot defend does the most damage — to the score and to the usefulness of "
                "the feedback.]"},
            {"q": "What would you do with the grant?", "a":
                "[Keep it to one named cost. $500 does the most good on something specific "
                "and finishable — a radio pre-scan ahead of the Band's FCC work, at-cost "
                "Bands for the next few outside testers, or the VYBE trademark filing. A "
                "$500 answer that reads like a $50,000 plan is the fastest way to look like "
                "you have not thought about it.]"},
        ],
    },
    {
        "id": "credits",
        "name": "Cloud and AI credits — five programs, one description",
        "funder": "NVIDIA, Microsoft, AWS, Google, Anthropic",
        "amount": "NVIDIA Inception (free, routes to partner credit offers) · Microsoft up to $150K · AWS Activate Founders $1K · Google Cloud Start $2K · Anthropic credits need institutional funding",
        "deadline": "rolling",
        "fee": None,
        "url": "https://www.nvidia.com/en-us/startups/",
        "submit": "All rolling, all short online forms, ten minutes each. Apply in this order: NVIDIA Inception (nvidia.com/startups), Microsoft for Startups (microsoft.com/startups), AWS Activate Founders (aws.amazon.com/startups), Google for Startups Cloud Program Start tier (cloud.google.com/startup). Use the company email, not a personal one.",
        "gates": ["incorp"],
        "confirmed": [],
        "why": "Credits cut what Vybe spends to run its AI, and they compound: Inception membership opens partner offers. Correction to the board: Anthropic's program is open to anyone to join, but its credits require equity from an institutional investor and a company under four years old. Join it now for the community; apply for credits after a priced round.",
        "docs": ["Company email address", "Website", "Claude Console account (for Anthropic)"],
        "note": "Inception membership may give a legitimate way to reference NVIDIA. Read Inception's brand guidelines before putting any NVIDIA mark on packaging; membership is not the same as a partnership.",
        "fields": [
            {"q": "One-line description", "a": ONE_LINER},
            {"q": "What you are building (short)", "a": SHORT},
            {"q": "How you use AI / how you'd use the credits", "a":
                "Vybe Intelligence runs models over each user's own time-series signals, "
                "ECG, heart-rate variability, sleep and activity, and a language model turns "
                "the result into a plain answer with the evidence shown. Credits would pay "
                "for training and evaluating those models and for inference as we move from "
                "{{STAGE}} to daily use by {{TRACTION}}."},
            {"q": "Industry and stage", "a":
                "Industry: Healthcare and life sciences (consumer health, wearables). "
                "Stage: {{STAGE}}. Team: {{EMPLOYEES}} people. Funding: [bootstrapped / "
                "amount raised]."},
        ],
    },
    {
        "id": "veterans",
        "name": "Veteran pitch circuit — Second Service Foundation and Warrior Rising",
        "funder": "Second Service Foundation · Warrior Rising",
        "amount": "Second Service: $1,000–$15,000 per regional event · Warrior Rising: up to $20,000 through business showers",
        "deadline": "rolling",
        "fee": None,
        "url": "https://secondservicefoundation.org/",
        "submit": "Second Service runs regional Military Entrepreneur Challenge pitch events; register for the next one near you. Warrior Rising is training-first: complete its program to become eligible for business-shower awards (warriorrising.org). Both require 51%+ veteran (or eligible military-family) ownership.",
        "gates": [],
        "confirmed": ["Veteran-owned 51%+ (confirmed 20 Sep)"],
        "why": "Repeatable. Each Second Service event is a new chance at cash with the same pitch, and a win is a line in every later application.",
        "docs": [],
        "note": "",
        "fields": [
            {"q": "60-second pitch", "a":
                "I'm {{VETERAN_OWNER}}, and I'm building Vybe.\n\n"
                "Every wearable gives you a number. None of them tell you why it moved. Vybe "
                "does. The screenless Vybe Band reads your heart, sleep and movement, and "
                "Vybe Intelligence connects them to the life around them: stress, work, "
                "travel. Ask \"Why am I tired today?\" and you get an answer from your own "
                "data and one next step.\n\n"
                "No required subscription. The answers come with the Band.\n\n"
                "We're at this stage: {{STAGE}}. [Your ask: what this award buys.]"},
            {"q": "Why a veteran is building this", "a":
                "[In your own words: what service taught you about sleep, recovery or "
                "readiness, and why a product that explains your body matters to you.]"},
        ],
    },
]

COMPANY = (
    "Legal name: {{LEGAL_NAME}}\n"
    "Formed: {{STATE}}, {{FORMED}}\n"
    "EIN: {{EIN}}\n"
    "Location: {{CITY}}\n"
    "Website: {{WEBSITE}}\n"
    "Email: {{EMAIL}}\n"
    "Lead: {{CEO}}\n"
    "Ownership: {{OWNERSHIP}}\n"
    "Employees: {{EMPLOYEES}}\n"
    "Revenue, last 12 months: {{REVENUE}}"
)

SHARED = [
    ("Company details, for the top of any form", COMPANY),
    ("One line", ONE_LINER),
    ("Short description (about 60 words)", SHORT),
    ("Long description (about 190 words)", LONG),
    ("Why now", WHY_NOW),
]
