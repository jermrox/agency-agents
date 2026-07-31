# Tactical Human Performance Jobs Scraper

Finds open roles in tactical human performance — strength and conditioning,
sports medicine, performance nutrition, cognitive performance — and publishes
them to a feed the MOPs & MOEs site can render, to Discord, or to a review
queue for a human to approve.

Zero third-party dependencies. Python 3.11+ standard library only, so it runs
in a bare GitHub Actions container with no install step.

```
sources ──▶ classify ──▶ dedupe ──▶ publish
  ATS        two-axis     seen.json   jobs.json / RSS / Discord / review queue
  USAJOBS    scoring
  RSS
```

---

## Quick start

```bash
cd jobs-scraper
cp sources.example.toml sources.toml

# See what it would collect without publishing or writing state.
python3 -m tactical_jobs run --config sources.toml --dry-run

# For real.
python3 -m tactical_jobs run --config sources.toml
```

Other commands:

```bash
python3 -m tactical_jobs sources            # list available adapters
python3 -m tactical_jobs classify \
  --title "Tactical Strength and Conditioning Coach" \
  --description "THOR3 program supporting special operations soldiers."
```

Run the tests with `python3 -m pytest tests/ -q` (pytest is the only dev
dependency; the package itself needs nothing).

---

## How relevance scoring works

This is the part that matters, because "performance" and "tactical" are two
of the most overloaded words in job listings. A single keyword list produces a
board full of Performance Marketing Managers and Tactical Category Buyers.

So every posting is scored on **two independent axes**, and must clear a floor
on **both**:

| Axis | Question | Example terms |
|---|---|---|
| **domain** | Is the population tactical? | THOR3, POTFF, H2F, SOCOM, firefighter, law enforcement, soldier |
| **discipline** | Is the work human performance? | strength and conditioning, TSAC-F, athletic trainer, performance dietitian, cognitive performance |

| Posting | domain | discipline | Verdict |
|---|---|---|---|
| Tactical S&C Coach, USASOC | ✅ | ✅ | **match** |
| Strength Coach, Ohio State | ❌ | ✅ | reject |
| Performance Engineer, Lockheed | ✅ | ❌ | reject |
| Performance Marketing Manager | — | — | reject (hard exclusion) |

Three more rules keep the signal clean:

- **Title matches count 2.5×** a description match. A title naming the job is
  much stronger evidence than a passing mention in the body.
- **Description hits are capped at 3 per term.** Long federal postings repeat
  "Soldier" forty times; without a cap one verbose listing outranks everything.
- **Hard exclusions veto outright**, before scoring. `performance marketing`,
  `performance engineer`, `tactical buyer`, and friends are never a match no
  matter what else the posting says.

Tune the weights in `tactical_jobs/classify.py` and the cutoffs in the
`[thresholds]` block of your config. Use the `classify` command to check a
change before committing to it.

---

## Sources

Every adapter talks to a vendor's **documented public job-board API** — the
same JSON that powers the employer's own careers page.

| kind | Required options |
|---|---|
| `usajobs` | `api_key`, `user_agent` |
| `greenhouse` | `board_token` |
| `lever` | `board_token` |
| `ashby` | `board_token` |
| `workable` | `board_token` |
| `smartrecruiters` | `company_id` |
| `recruitee` | `board_token` |
| `rss` | `url` |

**USAJOBS is the highest-value source for this niche** — Army H2F, Navy and
Air Force human performance billets, and DoD sports-medicine roles post there
first and often nowhere else. Get a free key at
<https://developer.usajobs.gov/apirequest/>.

### Not included, on purpose

Indeed, ZipRecruiter, LinkedIn, and Glassdoor are **deliberately absent**.
Their terms prohibit automated collection and they actively block it. Adding
them would put the project on bad legal footing and would break constantly.
If you want that inventory, license it.

### Adding an employer

The board tokens in `sources.example.toml` are **unverified placeholders**.
Confirm each one before relying on it — find the employer's careers page, note
which ATS it redirects to, and check the token returns JSON:

```bash
curl -s "https://boards-api.greenhouse.io/v1/boards/<token>/jobs" | head -c 300
curl -s "https://api.lever.co/v0/postings/<token>?mode=json"      | head -c 300
```

Then add a block and confirm with a dry run — a wrong token shows up as an
`ERROR` line in the run summary, not a silent zero:

```toml
[[source]]
kind = "greenhouse"
name = "example"
board_token = "example"
employer = "Example Employer"
```

The contractors holding H2F, POTFF, and THOR3 work are where most non-federal
hiring in this space happens, so they are the highest-yield boards to add.

---

## Publishing to the site

mopsnmoes.com runs on **Squarespace** — confirmed, not assumed. Any Squarespace
page returns its own config as JSON:

```bash
curl -s "https://www.mopsnmoes.com/about?format=json-pretty" | head -40
# "primaryDomain": "www.mopsnmoes.com"
# "internalUrl":   "https://puma-lizard-mnxz.squarespace.com"
# "timeZone":      "America/Chicago"
```

**Squarespace has no public content-write API for pages or blog posts.**
Nothing can POST a job directly into the site — so the working approach is a
static feed plus a client-side embed:

1. The `jsonfeed` publisher writes `output/jobs.json`.
2. That file is hosted anywhere with CORS and HTTPS (GitHub Pages is free and
   works out of the box).
3. A **Code Block** on the Squarespace page fetches and renders it.

Paste [`embed/squarespace-jobs.html`](embed/squarespace-jobs.html) into the
Code Block and set `FEED_URL` at the top of its script. It ships with search,
category filter chips, and inherits the site's fonts.

This is better than posting into the CMS anyway: the board is always live, so
a role that drops out of the feed disappears from the page with no stale-post
cleanup.

| publisher | What it does |
|---|---|
| `review` | Markdown queue for human triage. **Keep this on** — it is the audit trail. |
| `jsonfeed` | The live board the embed reads. Accumulates and ages out. |
| `rss` | RSS 2.0 of the live board. Squarespace Summary Blocks can consume it. |
| `discord` | Posts to a channel via incoming webhook. |
| `webhook` | Generic JSON POST — drives Zapier/Make, a Worker, or any writable CMS. |

Order matters for one pair: put `jsonfeed` **before** `rss`, since `rss`
renders the board that `jsonfeed` writes.

### Discord, optionally, on top

The MOPs & MOEs homepage already points people to Discord for "the latest
news, **job openings**, and network opportunities across tactical human
performance," so mirroring the board there costs nothing once the site is
live. Create a webhook under **Server Settings → Integrations → Webhooks**,
set `DISCORD_WEBHOOK_URL`, and uncomment the `discord` publisher.

That is an addition to the website, not a substitute for it.

Note that an uncommented publisher whose `${VAR}` is unset is a hard startup
error, not a silent no-op — so enable it and set the secret together.

---

## What publishes automatically

`auto_publish` is **on** in the example config — clear matches go live on
their own, which is the point of the thing.

The scoring splits into three buckets, so "automatic" does not mean
"unfiltered":

| Score | What happens |
|---|---|
| ≥ `publish` (14.0) | Goes live to the website feed automatically |
| ≥ `review` (8.0) | Lands in `output/review-queue.md` for a human call |
| below, or vetoed | Dropped |

Every published run is still fully auditable: the review queue records the
borderline calls, `state/seen.json` records everything ever published, and
both are committed by the workflow so the history shows up in a diff.

If you want a manual gate while you calibrate, set `auto_publish = false` and
*everything* routes to the review queue instead. Raising `thresholds.publish`
is the softer dial — it tightens what goes live without stopping the flow.

---

## Deduplication

Two levels, both persisted in `state/seen.json`:

- **identity** — same posting, same source. Exact.
- **fingerprint** — same employer + title + location across *different*
  sources, with abbreviations normalized (`Sr.` → `Senior`, `S&C` → `strength
  and conditioning`). Catches an employer that syndicates one job to both its
  own ATS and USAJOBS.

The state file is JSON so the scheduled workflow can commit it back to the
repo — no database to operate, and the history is reviewable in a diff.

---

## The two workflows

### Nightly — [`tactical-jobs.yml`](../.github/workflows/tactical-jobs.yml)

Runs the pipeline, commits the board and corpus, and **deploys to GitHub Pages**.
That deploy is the mechanism by which a job reaches mopsnmoes.com: Squarespace
has no content-write API, so the workflow publishes `jobs.json` and the Code
Block on the site renders it.

After the first successful run, the job summary prints the exact URL to paste
into the embed's `FEED_URL`:

```
https://<owner>.github.io/<repo>/jobs.json
```

Published alongside it: `dashboard.html`, `jobs.xml` (RSS), and `insights.json`.

**One-time setup:** enable Pages under *Settings → Pages → Source: GitHub
Actions*. The deploy job only runs from the default branch — a feature branch
must never repoint the live feed the website reads.

Defaults to `sources.keyless.toml`, so it works with no secrets at all. Set
`USAJOBS_API_KEY`, `USAJOBS_USER_AGENT`, or `DISCORD_WEBHOOK_URL` only if you
have them.

### Weekly — [`tactical-contracts.yml`](../.github/workflows/tactical-contracts.yml)

Scans USASpending for human performance contract awards and opens an issue
naming who just won one — see [EMPLOYERS.md](EMPLOYERS.md) for why this is the
highest-value signal in the whole system. Keyless.

The issue is gated on the award **count**, not on the rendered text, so a quiet
week or a failed scan produces no issue rather than an empty one.

---

## Scheduled runs

[`.github/workflows/tactical-jobs.yml`](../.github/workflows/tactical-jobs.yml)
runs the pipeline daily, commits the updated feed and state, and uploads the
review queue as an artifact. It only commits when something actually changed.

Add these repository secrets before enabling it:

| Secret | Needed for |
|---|---|
| `USAJOBS_API_KEY` | the `usajobs` source |
| `USAJOBS_USER_AGENT` | the `usajobs` source (your registered email) |
| `DISCORD_WEBHOOK_URL` | the `discord` publisher, if enabled |

The scheduled run publishes for real. The manual trigger from the Actions tab
exposes a dry-run checkbox for when you want to inspect scoring without
touching the board.

---

## Operational notes

- **One dead source never kills a run.** Failures are collected and reported
  in the summary; everything else still publishes. The run only exits non-zero
  if *every* source failed.
- **Postings older than `max_age_days` (default 45) are dropped.** Stale
  listings are worse than none.
- **State prunes at 3× `max_age_days`**, comfortably longer than a posting's
  life — otherwise a job that aged out would reappear as "new" while still
  listed.
- **Descriptions are excerpted to 400 characters.** Republishing a full job
  description is a copyright risk and bad for the employer, who wants the
  click.
- **The bot identifies itself** in its User-Agent with a contact URL.
