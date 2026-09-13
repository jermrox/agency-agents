# Tactical human performance research board

The rebuild described in *Tactical HP Board: Brief for the Coder (v2)*, 13 SEP 2026.

## What is here

| Module | What it does |
|---|---|
| `tactical_research/identifiers.py` | Recognises document identifiers in messy text and resolves each to its official host. Also holds the fetch allowlist. |
| `tactical_research/cluster.py` | Collapses many sightings of one document into one item, with articles as coverage underneath. |

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

Sections 3, 4, 6 and 7 of the brief — the 30-day feed, the hot-this-month block,
the card design, the standards panel, and the archive. The brief puts the
resolver before anything visual, so that is what exists.

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
