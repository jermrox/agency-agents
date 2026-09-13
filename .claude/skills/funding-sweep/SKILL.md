---
name: funding-sweep
description: >
  Run the non-dilutive funding sweep: collect open grants, cloud credits, accelerators,
  university partnership vehicles and pitch competitions from keyless federal APIs plus a
  hand-verified curated layer, derive open/closed status from real close dates, publish
  funding.json, and regenerate the funding dashboard. Use this skill whenever the user
  mentions the funding board, funding sweep, grants to apply for, SBIR/STTR deadlines,
  cloud credits, non-dilutive funding, "what can we apply for", the biweekly grant
  cadence, or adding a newly-found opportunity — even if they don't name the skill.
---

# Non-Dilutive Funding Sweep

The funding sibling of `tactical-job-sweep` and `tactical-research-sweep`. Same
non-negotiable, pointed at a different failure: **a funding board's credibility rests on
every deadline being real and every closed row being marked closed.** A confident list
containing three expired deadlines is worse than a list of five live ones, because the
reader stops trusting all of it.

## The failure this exists to prevent

Funding boards rot silently. A deadline passes, the row keeps sitting there looking live,
and the founder finds out by clicking through to a closed solicitation the week they
needed it. Two invariants prevent that, and neither is optional:

1. **Status is derived, never stored.** `Opportunity.status()` computes
   open/soon/closed/rolling from the close date against *today*, every run. Never add a
   status field to the data. A stored status is wrong the moment the clock passes it.
2. **Every hand-entered row carries `verified`,** the date a human last confirmed it. The
   run warns when one ages past `stale_days`. The curated layer must rot *visibly*.

## Running it

```bash
cd funding-scraper
python3 -m vybe_funding run --config sources.toml --dry-run   # report only
python3 -m vybe_funding run --config sources.toml             # write funding.json
cd .. && python3 scripts/sync-funding-dashboard.py            # regenerate the board
```

Standard library only. No API key, no account, no install step — same contract as the
jobs scraper. `.github/workflows/funding-sweep.yml` runs all three on the 1st and 15th.

**The federal APIs are unreachable from sandboxed agent environments** behind an egress
allowlist — they 403 at the proxy. That is expected and is why the sweep runs in CI. When
working locally, the API sources will fail and the curated layer will still produce a
board; do not "fix" that by removing them.

## Adding an opportunity

Prefer an API source if one exists — it maintains its own dates. Otherwise add a
`[[sources.curated.entry]]` block to `funding-scraper/sources.toml`:

```toml
[[sources.curated.entry]]
name = "Program name"
url = "https://..."
agency = "Who runs it"
amount = "$75K matched 1:1"
close_date = "2026-10-30"     # omit entirely for a rolling program
pillar = 2                     # 1 cost-offset · 2 grants · 3 university/partnership
kind = "grant"                 # grant | credit | accelerator | partnership | visibility
eligibility = "Who can actually file this"
note = "What a reader needs to know before spending an hour on it"
documents = [
  "What you must have in hand to apply",
]
verified = "2026-09-13"        # mandatory — the date YOU checked it
```

Then re-run the sweep and the sync script. Never hand-edit the dashboard's `GRANTS`
array: it sits between generated markers and `sync-funding-dashboard.py` overwrites it.

## Rules that are not negotiable

**Never invent an opportunity, an amount, or a deadline.** If a page cannot be reached,
say so and ask for the content rather than reconstructing it from a search snippet. A
fabricated row is the one error that destroys the board's usefulness entirely.

**Never carry a stale date forward as if it were live.** If a cycle has closed and the
next date is not published, omit `close_date` (making it rolling) and say so in `note`.
"Closed May 7, next opens ~Apr 2027" is honest; inventing an April date is not.

**Flag eligibility gates loudly.** Most state and demographic programs are geography- or
ownership-gated. A row the reader cannot file is noise unless the gate is stated. Put it
in `eligibility`, and lead the `note` with the gate when it is disqualifying
("MICHIGAN ONLY", "Cornell faculty PI must apply").

**Separate `eligibility` from `documents`.** They fail differently: an eligibility miss
means don't bother, a missing document means start now.

**Surface the registration lead times.** SAM.gov UEI, SBIR.gov SBC control number,
Grants.gov, eRA Commons and eBRAP gate every federal row and take weeks. They are free
and deadline-independent, so they belong at the top of the board as the first task, not
buried in a solicitation. Never let a founder discover them the week an application is
due.

## What good output looks like

- A count by status, and every row closing within 30 days listed by name and days left
- Any curated entry past `stale_days` flagged for re-verification
- Source failures named explicitly — a dead API is reported, never silently treated as
  zero results
- The urgent items stated plainly in the reply, not left for the reader to find

## Reporting to the user

Lead with what is on the clock. A board with 50 rows is useless as a wall of text; the
reply should say which two things close this month and what the reader must start today
regardless of any deadline. Then link the board.
