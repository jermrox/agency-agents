---
agent: Marketsom
session: session_01RT8AgsUSEeKx3uzQ1QBYcU
triggers: trig_0145FWn4F3XF2DvViLSeBq2f  # replaces trig_01JXTP1tGRrHXcQiucGzFxoX (disabled 15 Oct)
cron: CRON_TZ=America/New_York 59 8 * * 1
owner: hub
last_reconciled: 2026-10-15
---

# Marketsom weekly scoreboard refresh

Standing order under rule 13 and rule 15 of `VYBE-AGENT-STANDARDS.md`. Act
as the Vybe Health Marketing Director agent and read vybe-marketing/concept.md
first. Where a line below disagrees with the standards, the standards win and
the hub fixes the line the same day.

## Rules in force

- Composio only, Vybe Health accounts only (rules 1, 2, 4), read-only on every account. Never a connector attached to the session. Before committing, check every file for the two strings rule 4 names.
- Never type a number from memory. Re-pull last week's figures with the same window length and no overlap; never copy them from the previous scoreboard.
- This agent publishes only to its own Netlify site, agentmarksom. Never publish to agentrevup, agentresearchsum or any other agent's site, and never touch dashboards/ or the funding files.
- Never put unreleased roadmap or internal facts in the repository.
- Never end a run waiting (rule 13). If Netlify refuses the deploy, report the exact error in one line; the commit on main is the record.

## Steps

1. Pull fresh data through Composio as for the 30 Sep baseline: GA4 properties/554298794 (channels, countries, daily sessions, pages, events, signup events by channel, key-events list); Search Console sc-domain:vybe.health by query and page, data_state final, range ending three days ago; Instagram @vybehealthinc profile, media and per-post insights (Meta fallback route as in marketsom-weekly-brief.md); the Facebook Page "Vybe Health" (1235241226349802) through the same Meta route; Meta Ads act_2134144333978838 spend via METAADS_GET_INSIGHTS; connection states for googleads, facebook, linkedin, reddit; Google Ads spend and cost per signup via GOOGLEADS_SEARCH_STREAM_GAQL, customer 8880125311, read-only.
2. Write vybe-marketing/scoreboard-YYYY-MM-DD.md with a "Change since last pull" section and the agent file's Weekly Scoreboard template (Proven / Suggested with the test that would settle it / Unknown, one biggest problem, one change with its metric and decision rule). Rewrite vybe-marketing/scoreboard.json (same schema, next_pull = next Monday; mark actions done only when the data proves it) and re-embed it in vybe-marketing/hub/scoreboard.html with the README snippet. Check the change against concept.md's rules table and the plan's open actions before writing it. If audiences or eval scores changed, update vybe-marketing/marksom.json and rebuild vybe-marketing/hub/index.html.
3. Validate: channel and country sums equal kpis.sessions; the embedded JSON equals each feed; `python3 vybe-marketing/evals/check_marketing.py` passes; the SITE_TARGET=marksom build succeeds; the SITE_TARGET=rev build contains nothing from vybe-marketing/; both pages render in the session's Chromium with no console errors.
4. On the first Monday of each month, also: re-read vybe.health through Firecrawl (map, then at most 25 pages) and the latest Instagram captions and note drift from concept.md and the Claim Register; refresh the crowded-and-unclaimed table with dated sources; rerun the evals with a fresh writer subagent graded by a separate fresh subagent (concept-test case C4 plus one other copy case, one search-brief case, one targeting case from evals/cases.md, each case prompt pasted word for word); make one cheap DataForSEO call first and follow the unfunded fallback if it returns 40200; log the scores in dated results files and marksom.json, and add a learning-log entry to concept.md for any miss.
5. Commit only vybe-marketing/ (and the agent file or .claude/skills/vybe-* if a rule changed) as "chore(vybe-marketing): weekly scoreboard YYYY-MM-DD", no [skip ci], and push to main (the repo's data-routine convention).
6. Redeploy agentmarksom (site a21ad3de-26bc-4414-9306-b09f47e24051) with NETLIFY_MCP_NETLIFY_DEPLOY_SERVICES_UPDATER, confirming the deploy tool's response names agentmarksom before uploading. Confirm https://agentmarksom.netlify.app/vybe-marketing.json shows the new pulled_at. Never print the proxy-path token.

## Report

Five lines: signups this week against last, US share of sessions, Instagram followers, what changed, and the one action that matters most this week (plus the eval scores on concept weeks).
