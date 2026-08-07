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

## Retiring dead listings

A job board that shows closed requisitions is worse than no board: someone
spends an evening on an application for a role that closed weeks ago and only
finds out after they submit.

Sources cannot solve this. They report what is on a board *today*; a posting
that came down simply stops appearing, and "stopped appearing" is
indistinguishable from "the source errored" or "the ATS paginated
differently". So every run walks the already-published board and asks each
posting's own URL whether it still exists (`liveness.py`).

**The bias is one-way and deliberate.** A listing is removed only on
unambiguous evidence:

| Signal | Verdict |
|---|---|
| HTTP 404 / 410 | **gone** — removed |
| Page says "no longer accepting applications", "this job has expired", … | **gone** — removed |
| HTTP 403, 401, 5xx, timeout, connection reset | unknown — **kept** |
| Redirected off the posting to a search page | live, flagged in the reason |
| Anything else that answers | live |

403 is explicitly *not* a removal signal: KBR's public job HTML 403s every
non-browser fetcher while the requisition is perfectly live, so treating it as
"gone" would empty the board of the employers that matter most.

Wrongly dropping a live job is invisible to us and expensive for the
candidate. Wrongly keeping a dead one is visible and self-corrects on the next
pass. That asymmetry is why every ambiguous answer keeps the job.

Two schedules run this: 07:00 and 19:00 UTC, so a requisition that closes
during the US working day comes off the board the same day.

Run it by hand against any feed:

```bash
python -m tactical_jobs recheck --feed output/jobs.json --dry-run
```

---

## Filter facets

`classify.py` decides whether a job belongs on the board. `facets.py` answers
the four questions a candidate standing in front of the board actually asks,
and they become the filter controls in `embed/board.html`.

| Facet | Values | Notes |
|---|---|---|
| `discipline` | `strength-conditioning`, `athletic-training`, `physical-therapy`, `occupational-therapy`, `nutrition`, `cognitive-performance`, `behavioral-health`, `sport-science`, `human-performance`, `other` | The primary filter — a PT does not care what strength jobs exist |
| `location_classes` | any of `remote`, `conus`, `oconus` | A **set**: these reqs routinely span both |
| `contingency` | `contingent`, `funded`, `unknown` | Whether the seat depends on winning work |
| `lead` | boolean | Seniority, kept off the discipline axis |
| `salary_floor_annual` | number or null | Read from enrichment, hourly annualized at 2080h |

Three rules keep it honest:

- **The title decides the discipline.** Descriptions on these contracts list
  the whole embedded team ("works alongside the ATC, RD, and CPS"), so scoring
  the description hands every job every label. The description is a fallback
  that only runs when the title is silent, and only reads its first 400
  characters.
- **Seniority is not a discipline.** "Installation Lead Strength &
  Conditioning Coach" is a strength job. Filing it under "leadership" would
  hide it from every strength coach browsing the board.
- **Unknown always shows.** Every facet returns an explicit unknown rather
  than a plausible default, and the board treats unknown as "always show". A
  filtered-out posting is invisible, and the candidate never learns they were
  filtered.

`contingency` deserves its own note, because it is the one that costs people
real time. A contingent posting is a resume collector: the employer has bid on
work and is building a pipeline in case they win it. The word "contingent",
though, also appears in near-universal offer boilerplate — "employment is
contingent upon a background check" — so matching it bare would flag the
entire board. The rule instead splits on grammar:

- `contingent <noun>` ("contingent posting", "contingency hire") → **contingent**.
  Term of art in government contracting; conclusive on its own.
- `contingent upon <X>` → depends on X. Award, funding, task order, or
  *vacancy* → contingent. Background check, drug screen, E-Verify → ignored.
- Pipeline language with no such word at all ("talent pipeline for anticipated
  openings", "if awarded") → **contingent**.

CONUS/OCONUS use the DoD definition: CONUS is the 48 contiguous states, so
Alaska, Hawaii, and the territories are **OCONUS**. The board states this next
to the filter rather than assuming everyone reads it that way.

---

## What "verified" means

Badges are mechanical, never editorial — a badge a candidate cannot check is
decoration. The definitions ship *inside* the feed (`definitions.confidence`)
so the words shown and the value described cannot drift apart.

| Badge | Means |
|---|---|
| **Verified live** | We fetched this posting's own URL and the employer's system returned it as open, on the date shown |
| **Listed by employer** | From the employer's own careers system, but the link could not be re-checked (some sites block automated requests) |
| **Aggregator lead** | Found on a third-party board, not confirmed against the employer |

Nothing about job quality, employer, or pay is implied by any of them.

---

## The board

`embed/board.html` is the filterable board — no build step, no framework, one
fetch. Paste it into a Squarespace Code Block, or serve it standalone; the
workflow publishes it both ways (`embed.html` and as the Pages `index.html`).

- Every card links **straight to the employer's posting**. No rewritten
  summary, no interstitial.
- Rebrand by editing the custom properties in the `:root` block. Nothing else
  carries a colour.
- Repoint by editing `FEED_URL` at the bottom of the file.

To upgrade a feed that predates facets — including a hand-curated one — run:

```bash
python -m tactical_jobs feed --in jobs.json --out jobs.json
```

That adds facets, confidence, and the definitions block using the same
`enrich` and `facets` code the pipeline uses, so the rules never get
reimplemented in JavaScript and never drift.

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

## Putting it on a domain that updates itself

The nightly workflow already publishes to GitHub Pages. Two ways to point a
domain at it — pick by whether you want a **page** or a **section of an
existing page**.

### Option A — a subdomain of your own (`jobs.mopsnmoes.com`)

You get a real URL you control, updating nightly, with no Squarespace edits.

1. **Enable Pages**: repo *Settings → Pages → Source: GitHub Actions*.
2. **Set the domain**: *Settings → Secrets and variables → Actions → Variables*,
   add `JOBS_DOMAIN` = `jobs.mopsnmoes.com`. Every deploy rewrites the `CNAME`
   file from it — necessary because Pages otherwise drops a custom domain the
   first time a workflow publishes a fresh artifact.
3. **Add one DNS record** at whoever hosts mopsnmoes.com's DNS:

   | Type | Host | Value |
   |---|---|---|
   | `CNAME` | `jobs` | `<your-github-username>.github.io` |

   Use a **subdomain**, not the apex. The apex would need A records to
   GitHub's IPs and would fight Squarespace for the root domain.
4. Run the workflow once from the Actions tab. Pages issues the TLS
   certificate automatically (a few minutes).

Live at `https://jobs.mopsnmoes.com`, refreshed every night at 07:00 UTC.

### Option B — inside the existing Squarespace page

Squarespace has no content-write API, so nothing can POST a job into it. The
working pattern is a static feed plus a client-side embed, which is what
`embed/squarespace-jobs.html` is for.

1. Do steps 1–4 above (the domain is optional here — the default
   `username.github.io/repo` URL works fine).
2. On the Squarespace page: *Edit → Add Block → Code*, paste the contents of
   [`embed/squarespace-jobs.html`](embed/squarespace-jobs.html).
3. Set `FEED_URL` at the top of its script to your `jobs.json`:
   `https://jobs.mopsnmoes.com/jobs.json` (or the `github.io` URL).

The board then updates on the site with no further edits: the workflow
rewrites `jobs.json` nightly and the page renders whatever is in it. A role
that drops out of the feed disappears from the page — no stale-post cleanup.

**Both options publish the same four files**, so you can start with B and add
A later without changing anything:

| File | What it is |
|---|---|
| `jobs.json` | the feed the embed reads |
| `dashboard.html` | the full market dashboard |
| `jobs.xml` | RSS, for a Squarespace Summary Block or subscribers |
| `insights.json` | the aggregate analysis, if you want to build on it |

**One constraint worth knowing:** the deploy job only runs from the default
branch. This work is on a feature branch, so the first live deploy happens
when the PR merges — a feature branch must never repoint the feed the public
site is reading.

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
