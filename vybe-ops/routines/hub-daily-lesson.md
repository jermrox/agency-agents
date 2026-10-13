---
agent: Hub
session: session_013HHJWeDrTdszmAhpng4tZh
triggers: trig_01BS1LbPyaNwYhgt7n9D6VE6
cron: 10 17 * * *
owner: hub
last_reconciled: 2026-10-13
---

# Hub daily lesson (rule 10)

Standing order under `VYBE-AGENT-STANDARDS.md`.

Vybe agents only; never read, name or touch any other venture's agent (rule 6). No email to anyone.

For each of Revsom, Marketsom, Growsom, Instasom and the daily worker: read the latest output (post_turn_summary; the live page and feed through the Composio bash sandbox; dashboards/vybe-agents.json on main; for the worker, what landed on main today). Compare against rules 1 to 15 and the charter. Write one lesson in the exact form "LESSON <date> (rule N): Observed: <one sentence, specific to today's output>. Do tomorrow: <one concrete change>. Why: <one sentence>." Send it with a one-shot create_trigger aimed at the agent's session (never fire_trigger, which spawns a throwaway session) plus the line "Carry this into your next run. In that run's report, add one line: 'Lesson applied: <what changed>' or 'Lesson not applied: <why>'. No other reply." Append one row per agent to VYBE-LESSONS.md through a small PR merged once the standards check passes; never push to main directly. Tell the founder in five lines, one per agent, plus a sixth only when the same lesson has reached the same agent three days running: that is a pattern to fix at the source, and the hub fixes it (routine file, charter or standards), not the agent. Never end the run waiting (rule 13).
