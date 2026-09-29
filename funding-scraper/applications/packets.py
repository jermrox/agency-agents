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
