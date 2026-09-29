# Baby Gear Scout

The working half of the [Baby Gear Deals & Safety Scout](../specialized/baby-gear-deals-safety-scout.md)
agent. It tracks prices for a household's baby-gear watchlist, judges each
price against that product's own history, checks every product against CPSC
recalls and hard safety gates, and lays out a buy plan against the due date.

Python 3.11+ standard library only. pytest is the only dev dependency.

```
data/watchlist.toml ─▶ collect prices ──▶ data/prices.jsonl ──▶ deal score ─┐
                       (JSON-LD / manual)                                   │
                      CPSC recall API ──▶ recall match ──▶ safety gates ────┼─▶ data/reports/YYYY-MM-DD.json
data/purchases.jsonl ─▶ spending & savings                                  │         (one per day, kept)
due date ─────────────▶ buy plan ───────────────────────────────────────────┘                │
                                                                                             ▼
                                                              site/index.html  (daily dashboard + archive)
```

## The daily dashboard

`site/index.html` is one self-contained page (no external requests) built
from every saved report:

- **Headline numbers:** days until the due date, spent vs. budget, saved vs.
  typical prices, buy-now deals, safety alerts, and the estimate still to buy.
- **What changed:** today's differences from the previous report, such as new
  recalls, buy-now prices, items hitting your target, new 12-month lows, price
  moves of 3% or more, stock changes, purchases, and sale windows opening.
- **Watchlist:** each item's verdict, best price, 90-day median, 12-month low,
  a price-history line you can hover over (or step through with the arrow keys),
  and its safety checks.
- **Buy plan:** need-by dates and sale windows, marked Bought, Sale window
  open or Overdue.
- **Spending:** every purchase and what it saved against its typical price.
- **Report archive:** every past day. Choose a day (or use the Report picker)
  and the whole page shows that day's report.

`site/data.json` and `site/reports/*.json` hold the same data for anything
else that wants it.

## Quick start

```bash
cd baby-scout
# data/watchlist.toml holds your due date, budget and products (fictional
# placeholders to start -- replace them).

# Log a price you saw (store shelf, app, flyer). Per-unit for consumables.
python3 -m baby_scout add-price --key bramble-roam-convertible --retailer Target --price 239.99 --list-price 349.99 --sold-by-retailer yes
python3 -m baby_scout add-price --key store-brand-diapers-size1 --retailer Costco --price 42.99 --unit-count 198 --unit-label diaper

# Log what you actually bought -- this drives spending and savings.
python3 -m baby_scout bought --key bramble-roam-convertible --price 229.99 --retailer Target

# Collect prices, check recalls, save today's report, rebuild the dashboard.
python3 -m baby_scout run

# Same, but no network (uses saved prices; the recall check shows "CHECK").
python3 -m baby_scout run --offline
```

Open `site/index.html` in a browser.

## Running it every day

`.github/workflows/baby-scout-daily.yml` runs at 11:52 UTC every day (and on
demand from the Actions tab). It runs the tests, then `run`, then commits
`data/` and `site/` back to the repository, so every report is kept and the
archive grows by one day per run. Scheduled workflows only run from the
default branch, so this starts after the branch is merged.

**Viewing it:** the dashboard is its own Netlify project, separate from the
sites that build from the repository root. Set it up once:

1. In Netlify: **Add new site → Import an existing project → GitHub →**
   this repository, branch `main`.
2. Set **Base directory** to `baby-scout`. Leave the build command and
   publish directory empty; `baby-scout/netlify.toml` supplies them.
3. Deploy. The page is `site/` at the site root and redeploys after each
   daily commit. Rename the site, or add a custom domain, under *Site configuration*.

`baby-scout/netlify.toml` only redeploys when something under `baby-scout/`
changed, and the root `netlify.toml` skips rebuilding the other sites when a
commit touches only `baby-scout/`, so the daily run never redeploys them. The
dashboard is served with `X-Robots-Tag: noindex` so search engines leave it out.

**Privacy:** this repository is public. Anything in `data/` and `site/` is
public, including the due date, budget, prices and purchases. To keep the
watchlist file itself out of the repo, put its contents in the repository
secret `BABY_SCOUT_WATCHLIST`; the workflow uses it and never commits it. For
fully private reports, run the workflow in a private repository.

## How it decides

**Deal verdicts** are judged against the product's own history, never the list price:

| Verdict | Rule |
|---|---|
| 🟢 Buy now | within 3% of the 365-day low |
| 🟡 Good | ≥ 15% under the 90-day median |
| 🟠 Fair / Wait | < 15% under the 90-day median |
| ⚪ Tracking | fewer than 5 price points in 90 days, so no verdict yet |
| 🔴 Skip | failed a safety gate, whatever the price |

The daily price is the lowest in-stock price across retailers. Consumables with
`unit_count` are compared per unit. When the advertised "% off list" is 15+
points bigger than the real discount against history, the board flags it as a
fake discount.

**Safety gates** run first and are pass/fail:

1. No open CPSC recall matching brand + model name or model number (unless listed in `remedy_applied`).
2. Car seats: link to NHTSA's recall lookup. Car seats are NHTSA-regulated, so CPSC coverage isn't claimed.
3. Not a banned or discouraged type: inclined sleepers, crib bumpers, drop-side cribs, sleep positioners, weighted sleep products, sleep wedges.
4. Mandatory federal standard for the category (FMVSS 213, 16 CFR 1218/1220/…) is listed so you can confirm the label.
5. Used gear: single-user breast pumps and crib mattresses fail. Used car seats need a known, unexpired expiration date, a known crash-free history and intact labels.

Only items that pass all gates get a 0–100 confidence score from five factors:
JPMA certification, sold by the retailer vs. a marketplace seller, the brand's
5-year recall count, NHTSA ease-of-use stars (car seats) and condition. Unknown
factors get half credit and are listed as unverified.

**The buy plan** picks the latest historical sale window that closes before
each item's need-by date. Sale windows are patterns from past years, not
announcements, so confirm the dates each year.

## Data collection rules

- Product pages are read only through their schema.org `Product`/`Offer`
  JSON-LD, which is the price data the retailer publishes for search engines.
- `robots.txt` is checked before every fetch. Requests to a host are at least 2 s
  apart, and the user agent says what the tool is.
- A 401/403, a CAPTCHA page or a page without markup is reported, never worked
  around. Log those prices with `add-price` instead.
- Recalls come from the keyless CPSC SaferProducts.gov REST API.

## Files

| Path | Purpose |
|---|---|
| `data/watchlist.toml` | your household and products (or the `BABY_SCOUT_WATCHLIST` secret) |
| `data/prices.jsonl` | append-only price history |
| `data/purchases.jsonl` | what you bought, when, for how much |
| `data/reports/YYYY-MM-DD.json` | one saved report per day |
| `site/` | the dashboard (`index.html`), `data.json` and a copy of the reports |
| `tests/fixtures/` | recorded sample data with **fictional** brands, for offline tests |

Run the tests with `python3 -m pytest tests -q`.

Not medical advice. Recall and standards data changes, so re-check before you buy.
