---
name: tactical-research-sweep
description: >
  Run the MOPs and MOEs tactical human performance research routine: sweep official
  channels for military health, Holistic Health and Fitness (H2F), and human performance
  policy, doctrine, research, surveillance and funding; verify every link; grade the
  evidence; and produce findings.json, an embeddable light-theme HTML research board for
  the Squarespace site (mopsnmoes.com), and a one-page research summary. Use this skill
  whenever the user mentions the research board, research sweep, "what's new in H2F",
  fitness/body-composition standards changes, MSMR or surveillance numbers, CDMRP funding,
  military human performance studies, or the weekly research summary — even if they don't
  name the skill.
---

# Tactical Human Performance Research Sweep

The research sibling of `tactical-job-sweep`. Same brand, same board conventions, same
non-negotiable: **the board's credibility rests on the links working and the sourcing being
honest**. A confident summary of a document nobody opened is worse than no entry at all.

Two rules run the whole routine:

1. **Official channels only.** `.mil`, `.gov`, indexed peer-reviewed literature, NASEM,
   and allied defence research. Never a supplement or equipment vendor, a coaching blog, a
   social post where a document exists, a news aggregator, or an AI-generated summary site.
2. **No link, no claim.** Every entry says where its text came from — a fetched document,
   or a search-result snippet. Those are not the same thing and the board must not blur them.

## Modes

- **Sweep** (default): sweep → verify → grade → deliver `findings.json` + `tactical-research-board.html`.
- **Weekly summary** (when asked for "the summary" / "the research report"): everything
  above, plus the one-page brief — see "Weekly research summary" below.

## Step 1 — Sweep the registry

Search with WebSearch and fetch documents with WebFetch across the standing registry.
Restrict searches by domain (`allowed_domains`) so results come back pre-filtered:

| Channel | What it carries |
|---|---|
| Army Publishing Directorate (`armypubs.army.mil`) | FM 7-22, ARs, Army Directives |
| `media.defense.gov`, `war.gov`, `esd.whs.mil` | SecWar/SecDef memoranda, DoDIs |
| `h2f.army.mil`, `army.mil/aft` | H2F program, Army Fitness Test |
| `marines.mil`, `mynavyhr.navy.mil`, `af.mil`, `spaceforce.mil` | service standards messages (MARADMIN / NAVADMIN / DTM) |
| `health.mil` (MSMR, TBICoE, DHA policy) | surveillance, clinical guidance |
| `ph.health.mil` (DCPH-A) | injury-prevention and behavioral-health surveillance |
| `usariem.health.mil`, `med.navy.mil` (NHRC), `afrl.af.mil` (711 HPW) | service research labs |
| `hprc-online.org`, `champ.usuhs.edu` | evidence translation, OPSS |
| `cdmrp.health.mil` | funding — read as a 12–24 month leading indicator |
| `apps.dtic.mil` | technical reports |
| `gao.gov`, `dodig.mil`, `crsreports.congress.gov` | independent oversight, budget |
| `nationalacademies.org` | consensus reports |
| `sto.nato.int` | allied research |
| `pubmed.ncbi.nlm.nih.gov`, PMC, `clinicaltrials.gov` | peer-reviewed, trials in progress |

Cover all five H2F domains — physical, nutritional, mental, sleep, spiritual — plus injury,
brain health, women's health, environmental extremes, wearables, and the standards chain.
**Sweep every service**, not just the Army: a standards change in one service almost always
has siblings in the other four, and the Space Force is the one most often missed.

## Step 2 — Link verification (top priority)

Attempt to WebFetch **every URL you would list**.

- Fetched and confirmed → `verified: true`. Record the retrieval date.
- 404/410, moved, or paywalled → drop it, or replace it with the document's current home;
  log it in `dropped_dead`. `.mil` sites reorganise constantly (USARIEM moved from
  `army.mil` to `usariem.health.mil`; the Army Public Health Center is now DCPH-A).
- **If outbound fetches are blocked in the environment, say so on the board.** Set every
  `verified` to false, keep the red banner, and keep the `Fetch-verified` tally at 0.
  Do not quietly present search-index text as if a document had been read.

## Step 3 — Classify each finding

- `kind`: `policy` | `research` | `surv` | `program`
- `grade`: `Policy` (a requirement, silent on efficacy) · `A` (RCT or systematic review in
  a military population) · `B` (large prospective cohort or strong civilian RCT) · `C`
  (small, cross-sectional, retrospective) · `D` (pilot, abstract, preprint) · `S`
  (surveillance — incidence only, no causation)
- `type`: the document type, from a controlled vocabulary — Memorandum, Directive,
  Regulation, Doctrine, Administrative message, Order, Gov report, Technical report,
  Surveillance report, Surveillance data, Fact sheet, Peer-reviewed, Trial protocol,
  Press release, Practitioner post, News article, Program page, Reference guide, Report index
- `secondary`: true when the link is coverage **about** a primary document rather than the
  document. Every secondary entry's caveat must name the primary source to cite instead.
- `domains`: any of `standards physical injury sleep nutrition mental brain women environment tech h2f`
- `cui`: **never list a document marked CUI, FOUO, or CAC-gated**, even when a public URL
  indexes it. Drop it and note why.

Grade on design, not on how interesting the finding is. A policy memo is not evidence; a
program page is not a study; a press release about a study is neither.

## Step 4 — Outputs (deliver via SendUserFile)

1. **`findings.json`** —
   `{generated, fetch_verified:<bool>, findings:[{kind, grade, type, secondary, verified, domains, title, pub, date, notes, caveat, url}], watch_list:[{topic, why, sources_n}], registry:[{name,url}], dropped_dead:[...]}`.
   Order by what changes a decision first: policy that binds, then evidence that redirects,
   then surveillance, then funding.
2. **`tactical-research-board.html`** — self-contained embeddable section for the LIGHT
   Squarespace site. Use the bundled template `assets/research-board-template.html`.
   Replace only the `FINDINGS` array and the "Last sweep" date in the footer; keep the
   style spec intact (`.mm-board` wrapper, `font-family:inherit`, white bg, `#1c1e1c` text,
   `#e3e5e2` borders, `#2f3e33` accent; badges policy `#a87b1f` / strong `#2e7d43` /
   weak `#6b7280` / surveillance `#2f3e33` / secondary outlined `#b3502f`; legend box; live
   count; empty state with Clear filters; filters full-width under 560px).
3. **Watch list** — a topic earns a line only when it appears independently across three or
   more channels *inside the same sweep window* (e.g. policy + funding + new research). Two
   is a note, not a trend. State which channels converged.

### Weekly research summary

A **one-page** brief — the thing a leader reads in ninety seconds. Read the `pdf` skill's
SKILL.md before building a PDF version:

- **What changed that binds you** — new or amended policy, with effective dates.
- **What changed that should redirect you** — Grade A/B findings only.
- **The numbers** — current surveillance figures worth quoting, with their year.
- **What's coming** — watch-list topics and new funding lines.
- **Verification status** — how many links were fetched vs. taken from search text. Always.

One page. No appendix.

## Step 5 — Report back

If running unattended (scheduled), send a PushNotification wrapped in `<routine_summary>`
tags: findings added, how many were link-verified, policy changes with effective dates, and
anything new since the previous run. Keep the chat summary to a couple of sentences — the
files carry the detail. Diff against the previous `findings.json` to compute "new since last
sweep"; without it, say the baseline was unavailable rather than implying everything is new.

## Related

- `healthcare/healthcare-military-fitness-research-scout.md` — the agent persona, source
  registry, and evidence-grading rationale this routine executes.
- `tactical-job-sweep` — the jobs sibling. Same board conventions; run them from the same
  brand palette so the two embeds look like one site.
