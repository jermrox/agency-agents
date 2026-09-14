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
| `sweep.py` | The weekly sweep: crawl the registry, cluster, fetch primary documents, emit candidates. Also renders the pages. |
| `tactical_research/extract.py` | Reading a listing page for links and a primary document for its title, date and text. |
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

## What the sweep does, and what it refuses to do

`sweep.py` crawls all 17 registry sources, turns their listing links into
sightings, clusters them into one item per primary document, fetches each of
those documents, and writes `candidates.json`.

It **does not write blurbs**, and a test pins that. The brief requires a blurb
to come from the fetched document rather than from coverage of it — *"the agent
cannot get context right from search snippets any better than those outlets
did"* — so the sweep's job is to put the document in front of whoever writes and
stop there. Each candidate carries the document's own text.

### Coverage, as measured rather than intended

The first live runs crawled **9 of the 17 registry sources usefully**. The rest
contributed nothing:

- **Refused outright (5):** NIOSH, FEMA AFG/FP&S/SAFER, FBI LEOKA, NSCA TSAC,
  First H.E.L.P./BLS CFOI.
- **Answered 200 and returned no links (3):** NFPA, the OSHA docket, and
  NLEOMF/ODMP — client-side listings the crawler cannot read.

NLEOMF/ODMP gave 40 links on one run and none on the next, so at least one
source is intermittent rather than simply unreadable.

Those entries are deliberately left as they are. Finding a fetchable equivalent
for each is a judgement about what the registry should point at, and the run now
names them every week so the gap is visible rather than assumed away.

Two refusals matter more than anything the sweep produces:

- **An unreadable page never becomes a candidate.** A 200 that yields a
  JavaScript shell, a login wall or an undecodable PDF is discarded and counted.
  Keeping it would mean writing a blurb from the headline, which is exactly the
  failure the brief names.
- **`--render` refuses to render at all if any item fails validation**, and
  reports every problem rather than the first. Rendering the valid half would
  drop items silently and leave the board looking complete when it is not.

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

## Known gaps against the brief

Found by auditing the brief against the code rather than by a run failing, which
is why they are written down here: nothing red will remind anyone.

**The 61 search terms in `sources.json` are stored and never used (§9).**
`sweep.py` is a crawler — it walks the registry's listing pages. The brief's
vocabulary exists to *search* ("cancer presumption", "CPAT", "POST physical
ability test"), and searching needs a search API, which a CI runner does not
have. So those terms can only ever drive the agent step, never `sweep.py`. That
also means "the agent sweeps weekly" cannot be entirely a cron job, which is a
constraint worth being explicit about rather than discovering later.

**`supersedes` is never populated (§5).** The brief's own example works: a
MARADMIN and its change messages carry the same number, so they cluster into one
item already. What is missing is the case where a *different* document replaces
an earlier one — a new issuance number superseding an old one. Nothing detects
that, so nothing links back.

**`score` is always 0.0 (§4).** Deliberate, and noted in the schema: reach,
usefulness and hiring-signal are judgements about what a document means for a
reader, made when the blurb is written from it. A score derived from link counts
would be worse than an honest zero.

**There is no weekly dead-link check for this board (§7.8).** The existing
`verify-board-links.yml` reads the *old* board's HTML. The new pipeline has
nothing to check: `findings.json` is gitignored and `candidates.json` is a
30-day CI artifact, so the board's own links are never persisted anywhere a
weekly job could read them. The registry's links *are* checked weekly, by the
sweep itself. Deciding where `findings.json` lives is the prerequisite — it is
also what publishing needs.

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
