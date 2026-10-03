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
