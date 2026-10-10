# Vybe Growth Scout

The working half of the [Vybe Growth Scout](../marketing/marketing-vybe-growth-scout.md)
agent. It scouts the whole wearable-technology market for Vybe Health: investors
putting money into health wearables (or looking to), quick growth wins, builders
who could become design partners, people to contact on social, and ways into sports sponsorship. Every target
is verified, scored and ranked, and published to its own dashboard.

Everything under `growth-scout/` belongs to the scout. No other agent, board or
Netlify site reads or writes it, and it reads nothing of theirs.

```
params.toml ──▶ research lanes (parallel) ──▶ data/raw/<lane>.json
                                                   │  gates: source URL, fit ≥ 7, no guessed
                                                   │  contacts, no passed deadlines, no grants
                                                   ▼
                                    build.py ──▶ data/targets.json   (ranked record)
                                             └─▶ site/index.html     (dashboard)
                                             └─▶ site/data.json
```

## Files

| Path | What it is |
|---|---|
| `params.toml` | The search parameters: scope, the six lanes and their queries, quality gates, the priority formula, the sprint waves and the outreach rules. Change scope here. |
| `data/raw/SCHEMA.md` | The row format every lane writes, with the fit rubric and hard rules. |
| `data/raw/<lane>.json` | One file per research lane (and per follow-up wave). |
| `build.py` | Validates, de-duplicates, scores and ranks the rows, then writes the record and the dashboard. Standard library only. |
| `template.html` | The dashboard page. `build.py` fills in the data. |
| `site/` | What Netlify publishes. |
| `tests/` | `python3 -m pytest tests -q` |

## Lanes

| Lane | Hunt | Looks for |
|---|---|---|
| `vc` | investor | Funds and partners that led or joined wearable or health-hardware rounds in the last two years |
| `angels` | investor | Angels, angel groups (Ohio and Midwest first), founder-identity networks and syndicates |
| `accel_events` | investor | Equity accelerators, corporate VCs in sensors and wearables, and investor events with deadlines |
| `builders` | growth | Teams blocked on wearable hardware or data access, and labs and tactical programs running wearable studies |
| `social` | social | Honest gear reviewers, wearables journalists, communities and free launch listings |
| `signals` | investor | Dated funding rounds, acquisitions, API sunsets and launches that make outreach timely |
| `sponsor_competitors` | sponsorship | What competing wearable brands sponsor in sport, the small version Vybe could run, and open ambassador or NIL programs |
| `sponsor_targets` | sponsorship | Athletes without a competing wearable deal, Ohio teams and clubs, and events with entry-level sponsor or vendor packages |

## Ranking

`score = fit × 10`, plus 10 for a deadline in the next 45 days, 5 for a signal in
the last 120 days, 5 for a verified (primary or two-source) row and 5 for an open
public channel. Growth rows also move up or down by their ICE average. The score is
capped at 100. High is a full 100 (roughly the top 15%) and Medium is 90 or more, so "High" stays a short list worth acting on today.

## Run a sweep

1. Run the lanes. Each writes `data/raw/<lane>.json` following `SCHEMA.md`.
2. `python3 build.py`. It prints what it kept and why it dropped the rest.
3. `python3 -m pytest tests -q`
4. Commit `growth-scout/`. The push redeploys the dashboard.

`python3 build.py --check` validates without writing.

## The dashboard

`site/index.html` is one self-contained page with no external requests:

- **Headline numbers:** verified targets, investors, growth wins, social contacts,
  high-priority targets, targets ready to send, and deadlines in the next 30 days.
- **Send today:** the 10 best targets with an open channel and a drafted opener,
  a copy button, and links to the contact and the source.
- **All targets:** a filterable, sortable table. Click a row for its evidence,
  ask, opener, warm path, check size and ICE.
- **What competing wearables sponsor**, **coverage by lane**, and a **market signals** timeline.

Status marks (Contacted, Replied, Meeting…) are saved in your browser only.

## Netlify setup (once)

Add new site → Import from Git → this repository, then set **Base directory**
to `growth-scout`. Leave the build command and publish directory empty, because
`growth-scout/netlify.toml` sets them. The page is served `noindex`.

Netlify runs no build here: its command only asserts `site/index.html` exists
and then publishes the folder. So `site/` is **committed output, not build
output** — after changing anything under `data/`, run `python3 build.py` and
commit `site/` in the same change, or the deploy publishes yesterday's page (or
fails, if `site/` was never committed at all). The root `.gitignore` ignores
`site/` for the sites that *are* built on Netlify and names this one as an
exception; keep it there.

This repository is public, so the dashboard and its data are public too, even
though search engines are told not to index them. Every row is public
professional information, but if the drafted openers should stay private, move
the scout to a private repository or put the Netlify site behind password
protection.
