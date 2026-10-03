---
name: vybe-search-content
description: Size a search opportunity for Vybe Health with real data and turn it into a page brief that answers the searcher first and tells Vybe's concept second. Use whenever the user asks for SEO, a search page, an explainer, a blog post, a "vs" or "alternative" page, keywords, People Also Ask, AI-search (AEO) visibility, or "what should we write about" for Vybe, even if they don't name the skill. Uses DataForSEO and Google Search Console through Composio, and ends with the concept check and the marketing guardrail.
---

# Vybe search content

The job: find questions real people search for, prove the demand with
numbers, and write a page brief that answers the question in its first
lines and then shows what only Vybe can add. Search is the one channel
where crowded phrases ("screenless fitness tracker", "whoop alternative")
are worth using, because the searcher typed them. The hook can be hygiene;
the answer must still pass the concept check.

Read first: `vybe-marketing/concept.md` (the pillars-by-job table and the
crowded list), `vybe-marketing/brand-brief.md` (the Claim Register) and
`vybe-marketing/seo-plan.md`.

## Procedure

### 1. Name the question and the pillar

Write the searcher's question in their words, and the pillar it belongs
to. Vitals leads search; Restore is proof; Nourish, Connect (daylight) and
Move have smaller, more specific demand (see `concept.md`).

### 2. Size it with DataForSEO

Load Composio (`ToolSearch "select:mcp__Composio__COMPOSIO_SEARCH_TOOLS,mcp__Composio__COMPOSIO_MULTI_EXECUTE_TOOL,mcp__Composio__COMPOSIO_GET_TOOL_SCHEMAS"`)
and search for the DataForSEO tools. The ones used so far:

| Need | DataForSEO endpoint |
|---|---|
| Monthly volume, CPC, competition, 12-month series | Keywords Data, Google Ads search volume (task post, then get) |
| Keyword difficulty, 0 to 100 | Labs, Google bulk keyword difficulty (live) |
| Related keywords | Keywords Data, Google Ads keywords for keywords (live) |
| People Also Ask, who ranks, AI Overview | SERP, Google organic (task post, then get) |
| Trend over 5 years | Keywords Data, Google Trends explore (task post, then get) |

Rules:
- US, English, `location_code 2840`. Batch keywords; one batch of up to
  about 150 terms costs cents. Stay under about 10 calls a session.
- Google Ads **merges close variants** ("hrv" and "heart rate variability"
  both return 110,000). Never add merged variants together.
- Volumes are rounded into buckets. Report them as buckets, not exact counts.
- Compare the same weeks a year apart for trend; a 2026 bump in every
  Trends series is probably an artifact.
- Date every number, and say which pull backs each trend figure: the
  12-month Google Ads series (last 3 months against the first 3), or Google
  Trends (the same weeks a year apart). Never quote a growth percentage you
  cannot point to.

### 3. Check what Vybe already earns

Google Search Console via Composio, property `sc-domain:vybe.health`, last
90 days, by query and page. Check the **query**, not just the page: if a
page already gets impressions for this exact question, improve it. If its
impressions come from a different question, write a new page and link the
two.

### 4. Read the results page

From the SERP pull: who ranks in the top five, whether there is an AI
Overview and what it says, the People Also Ask questions, and any Reddit
or forum result. A Reddit thread in the top three means the existing
answers feel unsatisfying, which is Vybe's opening.

### 5. Choose the page type

| Searcher intent | Page type | Rule |
|---|---|---|
| A question ("what is a good hrv") | Explainer | Answer in the first 40 to 60 words, plainly, with no product mention. |
| A comparison ("whoop alternative", "whoop vs oura") | Fair comparison | Grant each product its strength. No price mockery, no "best" unless the list is fair and includes other no-subscription devices. |
| A category ("screenless fitness tracker") | Category page | Say what to look for in any device first, then where Vybe fits. Say "pre-launch". |
| A number ("is 37 a low HRV") | Explainer section | Explain why a single number means little without the person's own baseline. Never give a diagnostic threshold. |
| A population comparison ("hrv by age") | Explainer section | A published reference range may be cited **as context**, with its source, its measurement method and its spread, and the line that it is not a target or a verdict. Then turn to the person's own baseline. |
| A safety question ("what is an unsafe hrv") | One short answer | No number. Say that HRV alone does not tell anyone they are unwell, and that symptoms or worry are for a clinician. The boundary is on the claim, not on the person's data. |

### 6. Write the brief

Use the template below. The page answers first. Then it shows Vybe's
angle once, using the unclaimed ideas: a calibrated answer (its
confidence with a countable reason, the likely explanations, one next
step), and the person's own baseline. Every product claim comes from the
Claim Register, with "designed to" for rows 14 to 17 and 19.

### 7. Check it

- Run the concept check from `concept.md` and write the answers under the brief.
- Run `python3 vybe-marketing/evals/check_marketing.py <file>`. It must pass.
- No medical thresholds, no diagnosis, no "detects". HRV and heart rate only;
  never "heart rhythm" or "ECG".

### 8. Set the measure

Target query and page, the current position (Search Console), the target
position, the review date (8 weeks after publishing) and the decision rule
(for example, rewrite the title if impressions rise but the click rate
stays under 1%).

## Brief template

```
# Brief: <page title>

Question: <the searcher's words>      Pillar: <pillar>
Target query: <term> — <volume>/mo, KD <n>, CPC $<n> (DataForSEO, <date>)
Supporting queries: <3 to 6, with volumes>
People Also Ask to answer: <list>
Vybe today: <Search Console impressions and position, or none>
Who ranks: <top 3 and what they miss>
Page type: <explainer | comparison | category>

## Answer first (40 to 60 words)
<the plain answer, no product>

## Outline
<H2s, each answering one PAA question>

## The Vybe angle (one section)
<what Vybe is designed to add, with Register row numbers>

## Proof and sources
<studies or primary pages for each health statement>

## Call to action
<one: waitlist, or "talk to us" for builders>

## Schema and AI search
<Article schema with clear question headings. FAQPage markup is optional: since 2023 Google shows FAQ rich results only for well-known government and health sites, so it earns no rich result here, though it does no harm. The answer-first paragraph is the AI Overview candidate.>

## Measure
<current position, target, review date, decision rule>

## Concept check
<eight one-line answers>
```

## Current priorities

DataForSEO US figures pulled 3 October 2026. Refresh them before relying
on them after January 2027.

| Query | Vol/mo | KD | Why now |
|---|---|---|---|
| what is a good hrv | 14,800 | 17 | Moved up a volume bucket over the year (12,100 to 14,800). Vybe has no impressions for it yet: the HRV page's ~63 impressions are definition queries, so this needs its own page |
| what does hrv mean | 5,400 | low | The existing HRV page's natural target |
| hrv tracker | 2,400 | 8 | Commercial; rising (last 3 vs first 3 months of the 12-month series) |
| screenless fitness tracker | ~40,500 (110,000 at the mid-2026 peak) | to check | Surged after Fitbit Air; commercial |
| best fitness tracker without subscription | 1,600 | 29 | Grew from 210 |
| whoop alternative | 2,400 | 0 | Easy to rank; Reddit holds position 2 |
| oura ring alternative | 6,600 | 2 | Easy to rank |
| whoop vs oura | 9,900 | 0 | Easy to rank; must be a fair comparison |
| meal timing | low thousands | 7 | Nourish lead; CPC is high ($21.82), so organic only |
| sunlight exposure / morning sunlight benefits | rising 73 to 97% | low | Connect as daylight, only if the band has a light sensor |
| overtraining symptoms | 3,600 | 8 | Move for consumers |

## Pitfalls

- Writing for the keyword and forgetting the person: the first lines must
  answer the question someone actually typed.
- Turning an explainer into an ad. One Vybe section, once.
- Quoting a population "good HRV" range. Explain the personal baseline instead.
- Targeting emotional-distress searches ("im so lonely"). A wellness band
  does not belong on those results.
- Treating builder keywords as a paid channel: "wearable api" gets about
  20 searches a month at $14 a click. Builders come from outreach.
