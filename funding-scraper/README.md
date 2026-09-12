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
solicitation. Two design choices prevent that:

1. **Status is never stored, only derived.** `Opportunity.status()` computes
   open/soon/closed/rolling from the close date against the run date, every
   run. A stored status would go stale the moment the clock passed it.
2. **Hand-entered rows carry a `verified` date.** The run warns when one ages
   past `stale_days`, so the curated layer rots visibly instead of quietly.

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
of `close_date` / `amount` / `eligibility` / `pillar` / `kind` apply. Omit
`close_date` for a rolling program — that's a real state, not missing data.

## Running in CI

`.github/workflows/funding-sweep.yml` runs on the 1st and 15th, matching the
Pillar 2 biweekly rhythm, and commits the refreshed `funding.json`. It must run
in CI rather than a sandboxed agent environment: the federal APIs are open and
keyless but unreachable from behind an egress allowlist.

A failing source exits non-zero **and still writes the file** — a partially
fresh board beats no board, and the error is surfaced in the run summary and in
`source_errors` inside the JSON.
