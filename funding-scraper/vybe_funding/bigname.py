"""Big-name score for every opportunity row (VYBE-AGENT-STANDARDS rule 12).

"The name on the door is worth more than the headcount." Every row carries
``big_name`` (1-10) and ``big_name_why`` (one sentence: what makes the name
known and what door a win opens), so the console can rank by eligibility
first, then name, then money.

| big_name | what it is |
|---|---|
| 9-10 | a household or national name (NIH, Google, NBA, Garmin, Costco) |
| 7-8  | a flagship university, state or national body, federal agency, major fund or accelerator |
| 5-6  | a regional body, a known sector organisation, a seed fund or a developer-tools brand |
| 1-4  | a local event, a small nonprofit, an unknown funder, a vendor's own contest or perk |

TWO SOURCES, ALWAYS LABELLED (same contract as rule 9.7's fit): a curated row
may carry a hand-set ``big_name`` / ``big_name_why`` in sources.toml, which
wins and is marked ``big_name_source = "reviewed"``; every other row is scored
from the funder's name against the table below and marked "rule". Change the
table here, never the data.
"""

from __future__ import annotations

import re
from typing import Any

# (pattern, score, what makes the name known). Checked against the agency, then
# the programme name. The name mentioned FIRST wins, so "AMD with lablab.ai
# (partners: Google)" is scored as AMD, not Google; on a tie, the higher score.
_NAMES: list[tuple[str, int, str]] = [
    # 10 -- names every investor, journalist and buyer already knows
    (r"\bgoogle\b", 10, "Google"),
    (r"\bmicrosoft\b", 10, "Microsoft"),
    (r"\bamazon\b|\baws\b|amazon web services", 10, "Amazon / AWS"),
    (r"\bnvidia\b", 10, "NVIDIA"),
    (r"\bnba\b|national basketball association", 10, "the NBA"),
    (r"\bnfl\b|national football league", 10, "the NFL"),
    (r"olympic|team usa", 10, "Team USA (USOPC)"),
    # 9 -- national names: federal research flagships, consumer brands, wearables
    (r"national institutes? of health|\bnih\b|national institute on", 9, "the National Institutes of Health"),
    (r"national science foundation|\bnsf\b", 9, "the National Science Foundation"),
    (r"\bdarpa\b", 9, "DARPA"),
    (r"arpa-h", 9, "ARPA-H"),
    (r"\bnasa\b|space health", 9, "NASA-funded space health"),
    (r"mayo clinic", 9, "Mayo Clinic"),
    (r"\baarp\b", 9, "AARP"),
    (r"\bgarmin\b", 9, "Garmin"),
    (r"\bwhoop\b", 9, "WHOOP"),
    (r"\bcostco\b", 9, "Costco"),
    (r"target corporation", 9, "Target"),
    (r"\bverizon\b", 9, "Verizon"),
    (r"\bintuit\b", 9, "Intuit"),
    (r"\bpaypal\b", 9, "PayPal"),
    (r"marshalls|\btjx\b", 9, "Marshalls / TJX"),
    (r"\bmit\b|massachusetts institute of technology", 9, "MIT"),
    (r"consumer technology association|\bces\b", 9, "CES (Consumer Technology Association)"),
    (r"\banthropic\b", 9, "Anthropic"),
    # 8 -- federal agencies, flagship universities, major accelerators, big foundations and brands
    (r"department of (?:war|defense)|\bdod\b|\bdow\b|air force|\barmy\b|\bnavy\b|special operations|afwerx|xtech|acc-apg|detrick", 8, "the Department of Defense"),
    (r"defense health agency|congressionally directed|\bcdmrp\b", 8, "the Defense Health Agency"),
    (r"food and drug administration|\bfda\b", 8, "the FDA"),
    (r"centers for medicare|\bcms\b", 8, "CMS"),
    (r"veterans affairs|\bvha\b", 8, "the Department of Veterans Affairs"),
    (r"healthcare research and quality|\bahrq\b|health resources and services|\bhrsa\b|substance abuse and mental health|samhsa", 8, "a federal HHS agency"),
    (r"\bnist\b|\bsba\b|minority business development agency|department of commerce|national park service", 8, "a federal agency"),
    (r"techstars|y combinator|masschallenge|creative destruction lab|plug and play|\b500 global\b|antler|south park commons|extreme tech challenge", 8, "a major accelerator"),
    (r"yale|cornell|berkeley|clemson|syracuse|rice (?:university|business)|rutgers|case western|george mason|fordham|\bepfl\b|ohio state", 8, "a flagship university"),
    (r"robert wood johnson|sloan foundation|keck foundation|schmidt sciences|tory burch", 8, "a nationally known foundation"),
    (r"\bamd\b|\barm\b|siemens|dassault|solidworks|\bptc\b|onshape|stmicro|analog devices|renesas|murata|withings|kickstarter|cloudflare|mongodb|digitalocean|elevenlabs", 8, "a major technology brand"),
    (r"\bhlth\b|\bvive\b|\bmedica\b|\bitu\b|ai for good|world health expo|dmea", 8, "a major health-tech or industry stage"),
    (r"economic development|empire state development|department of development|third frontier|\bdceo\b|\bedc\b|\bedd\b|\bwedc\b|innovate alabama|labor (?:&|and) industries", 8, "a state economic-development agency"),
    (r"ohiohealth|university hospitals", 8, "a major Ohio health system"),
    # 6 -- regional bodies, known sector organisations, developer-tools brands
    (r"jumpstart|\bglide\b|bounce innovation|lightship|nextcorps|fuzehub|luminate|ohio aerospace institute|university of akron|northeast ohio medical", 6, "a regional innovation body"),
    (r"hello alice|ifundwomen|penfed|\bdav\b|disabled american veterans|d'aniello|ivmf|medtech conference|global entrepreneurship network|insurtech|spie|national braille press|mercatus|american academy of", 6, "a recognised national sector organisation"),
    (r"posthog|mixpanel|amplitude|sentry|retool|algolia|notion|zendesk|intercom|carta|together ai|aptible|digikey|w[uü]rth|pcbway|\bjlc|seeed|nextpcb|vultr|lablab|devpost|kaggle|tuya", 4, "a vendor running its own contest or perk (a parts shop, tools or hosting brand)"),
    (r"emerge americas|hello tomorrow|sushi tech|swisstech|startup prize|global health accelerator|innovation world cup|halcyon|activate|brinc", 6, "a recognised startup programme"),
    (r"university|college|institute", 6, "a university or institute"),
    # 4 -- small or local
    (r"veteran shark tank|founders live|sky's the limit|warrior rising|women veterans giving|rosie network|pave her way|freed fellowship|secretsos|shophand|darcy|nika lawrie|sengo|hidden starters|breva|caelestinus|terra|corti|charmhealth|inventacare|qloo|credit union|tully rinckey|vetcon|wbdc|patent pro bono|cleveland ip", 4, "a small or local funder"),
]
_COMPILED = [(re.compile(p, re.I), s, w) for p, s, w in _NAMES]

_DOOR = {
    10: "a win is a headline on its own and opens investor, retail and press doors",
    9: "a win is national-level credibility that investors and partners recognise",
    8: "a win is a credential investors, partners and later federal or state reviewers recognise",
    7: "a win is a credential investors and partners recognise",
    6: "a win is a regional or sector credential and a warm introduction, not a headline",
    4: "a win is a contact and some cash, not a name that opens doors",
    3: "an unknown name: worth the money only, not the credential",
}


def _rule_score(row: dict[str, Any]) -> tuple[int, str]:
    best: tuple[int, str] | None = None
    for field in ("agency", "name"):
        text = str(row.get(field) or "")
        hits = []
        for rx, score, who in _COMPILED:
            m = rx.search(text)
            if m:
                hits.append((m.start(), -score, who))
        if hits:
            _, neg, who = min(hits)
            best = (-neg, who)
            break  # the funder's own name decides; the programme title is the fallback
    if best is None:
        return 3, f"Scored from the funder's name, not hand-reviewed: no known name matched, so {_DOOR[3]}."
    score, who = best
    return score, f"Scored from the funder's name, not hand-reviewed: {who}; {_DOOR.get(score, _DOOR[6])}."


def big_name_fields(row: dict[str, Any], reviewed: dict[str, Any]) -> dict[str, Any]:
    """Return the rule-12 fields for one serialized row. Hand-set values win."""
    if reviewed.get("big_name") is not None:
        return {
            "big_name": int(reviewed["big_name"]),
            "big_name_why": str(reviewed.get("big_name_why") or ""),
            "big_name_source": "reviewed",
        }
    score, why = _rule_score(row)
    return {"big_name": score, "big_name_why": why, "big_name_source": "rule"}
