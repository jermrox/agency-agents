# Research sweep — running lessons

Read this before every sweep. Append one dated block after every sweep: what broke,
what worked, which gap you closed, which gap remains. When the same lesson shows up in
three blocks, fold it into SKILL.md as a rule and note "promoted" here.

## Standing facts (keep current)

- **Live board:** `healthcare/dashboards/h2f-scout-board.html` → `agentresearchsum.netlify.app`
  via `scripts/build-netlify-site.sh` (Netlify builds from `main`). Do not edit the build script.
- **Board v2 data:** three JS arrays in the page — `var ENTRIES = [...]`, `var WATCH = [...]`,
  `var REGISTRY = [...]`, one per line. Entry keys: `id, headline, blurb, tags, type, sector
  (MIL|FIRE|EMS|LE|CROSS), grade (Policy|A|B|C|D|S|Program), section (policy|research|surv|programs),
  date_published, first_seen, primary_url, secondary, pub, caveat, verified`.
  IDs are `<sector-lower>-NNNN`; continue the sequence, never reuse one.
- **Footer stamp:** `Last sweep: DD Month YYYY` — update it every run, even with zero new entries.
- **Dedupe by URL** (normalise trailing slash, `http`→`https`, strip query strings like `utm_*`).

## 2026-10-03 — v2 rebuild (238 entries)

- Outbound WebFetch was blocked (EGRESS_BLOCKED) for every domain; WebSearch worked. All
  entries ship `verified: false` with the red banner. Next run: also try `curl` through the
  session proxy (see `/root/.ccr/README.md`) and the PubMed MCP tools for PMIDs before giving up.
- Non-standard grades (Doctrine, Portal, Reference, Funding) broke the badge CSS. Map them to
  `Policy` or `Program` before writing.
- New top-level folders fail the `check-divisions` CI gate unless listed in
  `NON_DIVISION_DIRS` in `scripts/check-divisions.sh`. Keep sweep output inside existing folders.
- Coverage gaps: EMS has 1 entry, LE has 7. Search NAEMT, NHTSA Office of EMS, NREMT, EMS1
  research summaries (as secondary), FBI/POST fitness standards, and COPS Office wellness grants first.
