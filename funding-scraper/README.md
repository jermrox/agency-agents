# Vybe funding sweep

Collects open non-dilutive funding opportunities and publishes `output/funding.json`
for the [Vybe funding dashboard](../dashboards/vybe-funding-tracker.html) to read.

```bash
cd funding-scraper
python3 -m vybe_funding run --config sources.toml --dry-run   # report only
python3 -m vybe_funding run --config sources.toml             # write funding.json
```

Standard library only — no install step, no API key, no account.

## The problem this solves

A funding board goes stale silently. A deadline passes, the row keeps sitting
there looking live, and you find out by clicking through to a closed
solicitation. Three design choices prevent that:

1. **Status is never stored, only derived.** `Opportunity.status()` computes
   soon/open/rolling/forecast/closed from the dates against the run date, every
   run. A stored status would go stale the moment the clock passed it.
2. **Hand-entered rows carry a `verified` date.** The run warns when one ages
   past `stale_days`, so the curated layer rots visibly instead of quietly.
3. **A window that has not opened is not a live row.** `forecast` is its own
   state, because status read off the close date alone published three rows as
   applicable today — including a portal that does not open until 1 November,
   which showed as "rolling", the state that means *apply whenever you like*.
   Telling someone to apply to something that cannot be applied to is the same
   failure as an expired deadline, facing the other way. Forecast rows sort
   below everything applicable today and above closed, and the run prints them
   under **Not open yet** so a near-term window is still visible.

## Two layers

**API sources** — self-maintaining. Close dates come from the agency.

| Source | Covers | Key needed |
|---|---|---|
| `sbir_gov` | All 11 federal SBIR/STTR agencies | none |
| `grants_gov` | Everything federal that isn't SBIR/STTR | none |

**Curated** — state programs, university vehicles, cloud credits and
accelerators that publish a web page and nothing machine-readable. Declared in
`sources.toml`, each with a mandatory `verified` date.

## Adding an opportunity

Prefer an API source when one exists. For anything else, add a
`[[sources.curated.entry]]` block with `name`, `url`, `verified`, and whichever
of `close_date` / `open_date` / `amount` / `eligibility` / `pillar` / `kind`
apply. Omit `close_date` for a rolling program — that's a real state, not
missing data. Set `open_date` when the window has a published start: that is
what keeps the row off the live list until it can actually be applied to, and
it is the difference between "rolling" and "opens 1 November".

## Running in CI

`.github/workflows/funding-sweep.yml` runs on the 1st and 15th, matching the
Pillar 2 biweekly rhythm, and commits the refreshed `funding.json`. It must run
in CI rather than a sandboxed agent environment: the federal APIs are open and
keyless but unreachable from behind an egress allowlist.

A failing source exits non-zero **and still writes the file** — a partially
fresh board beats no board, and the error is surfaced in the run summary and in
`source_errors` inside the JSON.
