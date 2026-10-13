---
agent: Hub
session: session_013HHJWeDrTdszmAhpng4tZh
triggers: one-shot, re-armed daily by the previous run
cron: daily about 16:06 UTC
owner: hub
last_reconciled: 2026-10-13
---

# Hub compliance check (rules 9 to 15)

Standing order under `VYBE-AGENT-STANDARDS.md`. Never end the run waiting (rule 13): every finding becomes an order or a repo fix the same run.

For Revsom, Marketsom, Growsom and Instasom: read post_turn_summary, then through the Composio bash sandbox (session "love") check the live pages: a link to vybe-ops.netlify.app on every surface; the rule 9.7 fields (Marketsom briefing problems[] row "Rule 9.7 done" and outreach rows with what_is/status/offer/we_need/they_need/cost/next_date/size; Growsom data.json summary.rule_9_7 and target fields; Revsom funding.json rule_9_7 and fit/fit_why/cost/effort_hours/travel; Instasom all.json rule_9_7); no vendor, supplier or DevKit build shop in Marketsom's upcoming, problems or bookings or Growsom's open follow-ups; rules 11, 13 and 14: drafts signed as John, john_verdict/john_said/john_at and draft_body/send_today/persuasion published, no run ended waiting. If a live page is stale only because Netlify deploys are blocked by account credits, say so and judge the repo or store instead. Read dashboards/vybe-agents.json for red surfaces and confirm vybe-history.json has at least 3 points.

Report to the founder in plain words: a four-row table (agent, console link, 9.7 fields, vendors gone, rules 11/13/14), then one line on what the hub did about any "no": a one-shot order into that session naming the missing item, or a routine-file fix in this repo when the cause is the standing order. Never touch non-Vybe agents. Re-arm this check 24 hours out.
