---
agent: Revsom
session: session_013cWZ8bAwri5ewFcGtvZnCm
triggers: trig_01EQdARSs51vYkoBQHum43mc  # replaces trig_019Pvh4Km7EbfzTmQPe8NVwf (disabled 15 Oct)
cron: 47 15 * * 1-5
owner: hub
last_reconciled: 2026-10-15
---

# Revsom funding research round

Standing order under rule 13 and rule 15 of `VYBE-AGENT-STANDARDS.md`. Read
rules 1 to 15 on main every run; where a line below disagrees with the
standards, the standards win and the hub fixes the line the same day. The
founder asked that research never stop.

## Rules in force

- Composio only, Vybe Health accounts only (rules 1, 2, 4). Reading a public programme page is not an account. Never a connector attached to the session. Before committing, check the diff for the two strings rule 4 names.
- Never add an expired, fee-charging, unverified, clinical-trial, single-disease, medical-device or R01-type row. A dead row is worse than a missing one.
- Every row states its amount in the funder's own words, or the literal line "amount not stated on the page (checked <date>)"; never an empty amount (lesson 14 Oct).
- Every row carries fit, fit_why, cost, effort_hours, travel (rule 9.7) and big_name with big_name_why (rule 12).
- Rule 7: no booth, stand, exhibition pod or event presence, and no supplier or engineering help; a programme that requires one goes to CANDIDATES.md as rejected, with the reason.
- Never end a run waiting (rule 13). A blocked fetch is a line in CANDIDATES.md, not a reason to stop. If Netlify refuses the deploy, report the exact error in one line; main is the record.

## Reading pages

Try a plain fetch first. When a page renders only in a browser, read the form or page data from its embed (the AgeTech form on 15 Oct was read this way) or render it with the session's Chromium. When the egress proxy blocks a host, use the Composio remote sandbox (load COMPOSIO_REMOTE_BASH_TOOL with ToolSearch; `bash /home/user/fetch.sh <URL> 8000`, or recreate the script: curl -sL with a browser user-agent, strip script and style tags, print the first N characters). WebSearch is for discovery only; nothing is added from a listicle.

## Steps

1. Fresh worktree of origin/main. Build the list of names already on the board from funding-scraper/sources.toml and the rejected and watch lists from funding-scraper/CANDIDATES.md.
2. Pick four lanes not searched in the last two rounds (the CANDIDATES.md section headers show them). One lane always re-checks the watch list for windows that have opened.
3. Launch four background research agents with these rules and a JSON output shape: name, url, agency, amount (quoted), open_date, close_date (quoted sentence), kind, sam (required, later or none), eligibility, note, documents, fit, fit_why, cost, effort_hours, travel, big_name, big_name_why, evidence; plus a rejected list with reasons.
4. Merge verified entries into funding-scraper/sources.toml under [[sources.curated.entry]] with today's verified date; log rejects and the watch list in CANDIDATES.md.
5. Run `bash scripts/check-divisions.sh`, confirm sources.toml parses, and run the dry-run sweep. Open a PR, merge it when its checks are green (auto-merge approved 1 Oct), then dispatch funding-sweep.yml on main.
6. Rule 5: fetch https://agentrevup.netlify.app/funding.json and compare `generated` with main. If they differ, report "committed, not live: <error>".

## Report

At most eight lines to the founder: what is new, sorted by deadline; the no-SAM count; anything closing within seven days; the live-versus-main check; and "Lesson applied: <what changed>" when a lesson is open.
