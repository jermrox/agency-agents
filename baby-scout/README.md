# Baby Gear Scout

The working half of the [Baby Gear Deals & Safety Scout](../specialized/baby-gear-deals-safety-scout.md)
agent. It tracks prices for a household's baby-gear watchlist, judges each
price against that product's own history, checks every product against CPSC
recalls and hard safety gates, and lays out a buy plan against the due date.

Python 3.11+ standard library only. pytest is the only dev dependency.

```
watchlist.toml ──▶ collect prices ──▶ state/prices.jsonl ──▶ deal score ─┐
                   (JSON-LD / manual)                                    ├─▶ output/board.json
                  CPSC recall API ──▶ recall match ──▶ safety gates ─────┤    output/board.html
                  due date ─────────────────────────▶ buy plan ─────────┘
```

## Quick start

```bash
cd baby-scout
cp watchlist.example.toml watchlist.toml     # edit: due date, budget, products

# Log a price you saw (store shelf, app, flyer). Per-unit for consumables.
python3 -m baby_scout add-price --key bramble-roam-convertible --retailer Target --price 239.99 --list-price 349.99 --sold-by-retailer yes
python3 -m baby_scout add-price --key store-brand-diapers-size1 --retailer Costco --price 42.99 --unit-count 198 --unit-label diaper

# Collect prices from product URLs, check recalls live, write the board.
python3 -m baby_scout run

# Same, but no network (uses logged prices; recall gate shows "CHECK").
python3 -m baby_scout run --offline
```

Open `output/board.html` in a browser.

### Other commands

| Command | What it does |
|---|---|
| `recalls --brand B --model M [--model-number N]` | CPSC recall check for one product. Exit code 1 if the model matches a recall. |
| `plan --due 2027-02-10 --budget 4500` | What to buy, by when, and which sale window to aim for. |
| `stack --price 239.99 --pct 15 --gift-card 20` | True price after stacking discounts, gift cards, cash back and rebates. |
| `banned "product name"` | Checks a name against banned or discouraged sleep products. |
| `extract --file saved_page.html` | Shows the schema.org price/stock data a product page publishes. |

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
| `watchlist.toml` | your household and products (gitignored; copy from the example) |
| `state/prices.jsonl` | append-only price history (gitignored) |
| `output/board.json`, `output/board.html` | latest results (gitignored) |
| `tests/fixtures/` | recorded sample data with **fictional** brands, for offline tests |

Run the tests with `python3 -m pytest tests -q`.

Not medical advice. Recall and standards data changes, so re-check before you buy.
