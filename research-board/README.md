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
| `tactical_research/watch.py` | The standards-panel watcher: what counts as a page change worth an editor's attention. |
| `watch_standards.py` | The CI runner for that watch — the only part that touches the network. |
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

## The watcher is the alarm, not the editor

Section 6 puts a person in charge of the standards table. `watch.py` only
compares each row's official page week to week and raises a flag when the title
or the dates on it move.

The judgement call is what *doesn't* raise a flag. A raw content diff would flag
nearly every row nearly every week — federal pages carry rotating banners and
counters — and a watcher that cries wolf weekly is one the editor learns to
ignore, which is worse than no watcher. So a content-hash difference alone is
recorded and not flagged, and a week a page could not be fetched keeps the old
baseline rather than overwriting it with a blank, so the real change that lands
afterwards still has something to compare against.

### Six rows the bot cannot read

Every `.mil` row in the panel — army.mil, af.mil, mynavyhr, marines.mil,
spaceforce.mil, esd.whs.mil — answers an automated request with 403. A full
browser header set does not clear DoD's filter. That is the host declining the
robot, not a standard disappearing, so it is never treated as a change.

But a row refused week after week looks exactly like a row that never changes,
and the panel would happily report "nothing changed" about a page it has never
once read. So refusals are counted, and after four consecutive runs the row is
flagged as unread with a note to check it by hand. Half the panel is military,
so this is the difference between a watcher and the appearance of one.

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
