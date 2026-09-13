# Tactical human performance research board

The rebuild described in *Tactical HP Board: Brief for the Coder (v2)*, 13 SEP 2026.

## What is here

| Module | What it does |
|---|---|
| `tactical_research/identifiers.py` | Recognises document identifiers in messy text and resolves each to its official host. Also holds the fetch allowlist. |
| `tactical_research/cluster.py` | Collapses many sightings of one document into one item, with articles as coverage underneath. |
| `tactical_research/models.py` | The board schema, the 30-day window, and the 12-month archive split. |
| `tactical_research/hot.py` | Hot this month: a tag earns a line at three or more independent items. |
| `tactical_research/render.py` | The rendered board and archive pages: hot block on top, one filterable feed below. |
| `tactical_research/sources.json` | The source registry with a sector field, and the non-military search vocabulary. |
| `tactical_research/standards.json` | The current-standards panel. Hand-edited; the bot only watches each row's page. |

Both are pure logic with no network, and both are covered by `tests/`.

## The rule that matters

**The document is the item, never the coverage.** A DoWI update produces
articles across dozens of outlets, most of them missing the context. The board
shows that as one item, written from the issuance, with the articles collapsed
underneath.

Primacy is decided by the **host**, not by the presence of an identifier. An
article quoting "DoWI 1308.03" is coverage *of* that issuance, not the issuance.
Reading it the other way lets whichever outlet published first become the item —
the exact failure the brief is guarding against, and a bug the tests caught in
the first draft of this module.

The one exception is events and program announcements, which often have no
underlying document and may stand on coverage.

## Not built yet

The sweep that fills the board. `render.py` turns items into the page, but
something has to produce the items, and writing blurbs from primary sources
means outbound fetch — so that step has to run where fetch works.

## One thing the brief and the data disagree on

The standards panel lists the Army Fitness Test, whose page is `army.mil/aft/`.
The brief's fetch allowlist includes `armypubs.army.mil` but not bare
`army.mil`, while it does allowlist `af.mil` and `spaceforce.mil` whole — the
Army is the only service narrowed to its publishing subdomain.

Nothing here widens the allowlist to paper over that: it is a trust boundary and
changing it is a decision, not a fix. The panel's tests assert an official host
instead, which is the right bar for a page-change watch — a different job from
writing a blurb out of a document.

## The fetch dependency

The brief requires blurbs to be written from the fetched primary source, not
from search snippets: "the agent cannot get context right from search snippets
any better than those outlets did." That is right, and it is a hard dependency —
the board's current 103 entries were all written from snippets, which is why
they carry evidence grades and citation warnings.

Outbound fetches are blocked in the authoring sandbox. They are **not** blocked
on a GitHub Actions runner, which is how `verify-board-links.yml` resolves all
123 board URLs. The sweep that writes blurbs therefore belongs in CI, not in an
interactive session.
