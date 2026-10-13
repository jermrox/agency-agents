# Vybe routines

Every standing order a Vybe agent runs on lives here, one file per routine,
owned by the hub (rule 15 of `VYBE-AGENT-STANDARDS.md`). The scheduler
holds only a pointer: "pull origin/main and execute this file". That makes a
routine reviewable in a pull request, checkable in CI, and editable by the hub
the same day a rule changes, instead of a prompt frozen inside the scheduler
on the day it was written (which is how rules 11 and 13 were broken).

Each file starts with a front-matter block the lint reads:

```
---
agent: Marketsom
session: session_...
triggers: trig_...        # the scheduler entries that point here
cron: CRON_TZ=America/New_York 23 6 * * *
owner: hub
last_reconciled: 2026-10-13
---
```

`scripts/check-vybe-routines.py` fails the build when a routine contradicts
the standards: an active order the founder has since reversed, the founder's
voice where John's belongs, a connector the agent may not use, a missing
rule-13 "never end a run waiting", a missing rule-14 line on an outreach
routine, a foreign account string, or a model name.

Changing a routine: edit the file, open a PR, merge when the checks pass. The
agent reads the new text on its next run. Nothing else needs to change.
