# Research sweep — running lessons

Read this before every sweep. Append one dated block after every sweep: what broke,
what worked, which gap you closed, which gap remains. When the same lesson shows up in
three blocks, fold it into SKILL.md as a rule and note "promoted" here.

## Standing facts (keep current)

- **The brief is the spec:** `Tactical_HP_Board_Brief_for_Coder_v2.pdf` (13 SEP 2026). Read the
  section in SKILL.md that summarises it. Check work against the brief, not against memory.
- **Live board:** rendered by `research-board/sweep.py --publish` from `research-board/findings.json`
  into `healthcare/dashboards/h2f-scout-board.html` (+ `h2f-archive.html`), then published to
  `agentresearchsum.netlify.app` by `scripts/build-netlify-site.sh` when `main` changes.
  Never hand-edit the HTML; edit the data and re-render.
- **Fetch:** `mcp__Exa__web_fetch_exa` reads .mil pages and PDFs; PubMed connector reads abstracts.
  WebFetch/curl are blocked in the cloud sandbox.
- **Dedupe by document:** normalised URL *and* identifier (DOI, PMID, issuance number).

## 2026-10-08 — daily run

- +3 items, all PubMed: MIL 2 (Marine pull-up requirement and upper-extremity injury trend; Tabata
  with or without cinnamon in cadets, blurb says cinnamon did not separate on performance), FIRE 1
  (machine-learning core temperature in encapsulated PPE). Board 68, archive 57. EMS and LE: nothing
  qualifying. Exa still 402 (fifth day); "no new policy" is unverified.
- PR #67 was still unmerged, so the run stacked on its branch and merged `main` in (the stop hook's
  "15 unpushed commits" were main's commits arriving through that merge).
- PubMed `date_from` wants `YYYY/MM/DD`, not dashes.
- Still open: `verify-research-site.yml` v2 update; COPS LEMHWA (due 22 Oct) and Fairmont WV AFG leads.

## 2026-10-07 — daily run

- +3 items, all PubMed: MIL 2 (burnout interventions for military physicians; cardiac emergency
  planning for the military), FIRE 1 (low back pain in Brazilian firefighters). Board 66, archive 56.
  EMS and LE: nothing qualifying again. Exa still 402 (fourth day); "no new policy" is unverified.
- PR #56 merged on 6 Oct and its branch was deleted upstream, so this run started cleanly from
  `main`. Reset the local branch with `git checkout -B <branch> origin/main` only after confirming
  `git rev-list --count origin/main..HEAD` is 0.
- Still open: update `verify-research-site.yml` to the v2 layout (it checks the old page); confirm
  COPS LEMHWA (due 22 Oct) and the Fairmont WV AFG award once fetch works.

## 2026-10-06 — daily run

- +1 item (MIL: night-owl chronotype and PTSD/depression/insomnia in veterans). Board 62.
  Exa still 402 (third day): PubMed-only. Lead: Army waist-to-height deadline ~5 Oct under
  Directive 2026-13 (trade press only).
- A container restart overnight wiped scratch space (sweep rules, merge script) and recreated
  the local branch from main. Rules now live in `references/sweep-rules.md`; merging is
  `research-board/merge_items.py`. On start, confirm the local branch matches its origin.
- The cited-items check passed with no edits as items aged out — working as intended.

## 2026-10-05 — daily run

- +1 item (MIL: USARIEM review, cadets injured about as often as soldiers in initial training).
  Board 62, archive 56. Exa still out of credits (402): PubMed-only again, Monday link re-check
  skipped. Unverified leads to confirm when fetch returns: COPS FY26 LEMHWA NOFO (due 22 Oct),
  Fairmont WV $246K AFG health/cancer-screening award.
- Stale hot-topic paragraphs happened again (caffeine meta-analysis, 15 kg kit study aged out).
  Second time in two days, so it is now enforced in code: hot-notes.json carries `cites` and
  `sweep.py --publish` refuses while any cited item is out of the window.

## 2026-10-04 — first daily run

- +4 items, all research from PubMed: MIL 2 (SF selection ruck times; neuroticism and fitness in
  airmen/guardians), LE 1, CROSS 1 (WTC exposure and cortical thinning). Board 64, archive 53.
- **Exa ran out of credits (HTTP 402) mid-run.** Without it no .mil/.gov page can be read here, so
  policy checks were search-only and nothing policy-side could be added. PubMed still worked.
  If Exa is down, say so in the report and treat "no new policy" as unverified, not as a quiet day.
- Items age out daily: two 03 Sep items left the window and two hot-topic paragraphs still named
  them. Re-read every hot note against the current window each run, not only new topics.
- PR #56 was unmerged, so the run stacked on its branch instead of branching from main.
- Next gaps: COPS LEMHWA/CHP awards, POTFF III final RFP, NHRC shipboard sleep study (DVIDS),
  any NAVADMIN/MARADMIN/ALCOAST — all need a working fetch.

## 2026-10-03 — rebuilt to the brief (second attempt)

- First attempt (PR #56) ignored the brief and the existing `research-board/` engine: kept
  grades, caveats, banner, sections, an 18-month archive as the main board. Only 2 of 238 items
  were inside the 30-day window. Lesson: read the spec and the repo before building.
- Exa fetch works where WebFetch is blocked — that is what makes "write from the document" possible.
- The old 238 entries were snippet-written; only those whose primary document could be re-read
  were carried into the archive.

## 2026-10-03 — v2 rebuild (238 entries) — superseded

- Outbound WebFetch was blocked (EGRESS_BLOCKED) for every domain; WebSearch worked. All
  entries ship `verified: false` with the red banner. Next run: also try `curl` through the
  session proxy (see `/root/.ccr/README.md`) and the PubMed MCP tools for PMIDs before giving up.
- Non-standard grades (Doctrine, Portal, Reference, Funding) broke the badge CSS. Map them to
  `Policy` or `Program` before writing.
- New top-level folders fail the `check-divisions` CI gate unless listed in
  `NON_DIVISION_DIRS` in `scripts/check-divisions.sh`. Keep sweep output inside existing folders.
- Coverage gaps: EMS has 1 entry, LE has 7. Search NAEMT, NHTSA Office of EMS, NREMT, EMS1
  research summaries (as secondary), FBI/POST fitness standards, and COPS Office wellness grants first.
