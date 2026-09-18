"""The rendered board: hot block on top, one feed below.

Build step 5, and the page half of step 3. The brief's layout argument is that
pillars force a reader to learn our sorting before they can find anything, so
there is exactly one list here and the tags are filters rather than sections.

Everything the old board carried and the brief removed stays removed: no
evidence grades, no verify-before-citing banner, no Secondary caveats, no
fetch-verified counter. A test asserts their absence, because those are the
kind of thing that drifts back in one helpful addition at a time.

Every value that reaches the page goes through ``escape``. Headlines and blurbs
are written from documents the sweep fetched off the open internet, so treating
them as trusted markup is how a board like this ends up serving someone else's
script.
"""

from __future__ import annotations

from datetime import date, datetime
from html import escape

from .hot import HotTopic, hot_topics
from .models import SECTORS, TAGS, TYPES, BoardItem, split_window

# Visible cap from section 3. The rest of the month stays in the DOM behind
# "show all" rather than a second request, so the filters work over everything.
VISIBLE_CAP = 25

PALETTE = """
:root {
  --ink: #1c1e1c;
  --muted: #5c635c;
  --rule: #e3e5e2;
  --accent: #2f3e33;
  --ground: #ffffff;
  --raise: #f7f8f6;
  --radius: 10px;
  --shadow: 0 1px 2px rgba(28, 30, 28, .06);
  --shadow-lift: 0 4px 14px rgba(28, 30, 28, .10);
  --gutter: 20px;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--ground); color: var(--ink);
  font: 16px/1.55 "Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}
.wrap { max-width: 900px; margin: 0 auto; padding: 40px var(--gutter) 80px; }
header h1 { font-size: 1.7rem; margin: 0 0 6px; letter-spacing: -.01em; }
header p.sub { margin: 0 0 28px; color: var(--muted); font-size: .95rem; }
h2 { font-size: 1.05rem; text-transform: uppercase; letter-spacing: .08em; margin: 36px 0 14px; }

.hot { background: var(--raise); border: 1px solid var(--rule); border-radius: var(--radius);
       padding: 20px var(--gutter); box-shadow: var(--shadow); }
.hot h2 { margin-top: 0; }
.hot p { margin: 0 0 14px; }
.hot p:last-child { margin-bottom: 0; }
.hot .links a { margin-right: 10px; font-size: .88rem; }
.hot .empty { color: var(--muted); }

.controls { position: sticky; top: 0; z-index: 5; background: rgba(255,255,255,.92);
            backdrop-filter: blur(6px); padding: 12px 0; border-bottom: 1px solid var(--rule);
            margin-bottom: 18px; }
.controls fieldset { border: 0; margin: 0 0 8px; padding: 0; display: flex; flex-wrap: wrap; gap: 6px; align-items: center; }
.controls legend, .controls .label { font-size: .72rem; text-transform: uppercase;
            letter-spacing: .08em; color: var(--muted); margin-right: 6px; }
.controls button { font: inherit; font-size: .85rem; padding: 4px 12px; border-radius: 999px;
            border: 1px solid var(--rule); background: var(--ground); color: var(--muted); cursor: pointer; }
.controls button:hover { border-color: var(--accent); color: var(--ink); }
.controls button[aria-pressed="true"] { background: var(--accent); border-color: var(--accent); color: #fff; }
.controls button:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

.card { border: 1px solid var(--rule); border-radius: var(--radius); padding: 18px var(--gutter);
        margin-bottom: 14px; box-shadow: var(--shadow); transition: box-shadow .15s ease; }
.card:hover, .card:focus-within { box-shadow: var(--shadow-lift); }
.card h3 { margin: 0 0 8px; font-size: 1.08rem; line-height: 1.35; }
.card h3 a { color: inherit; text-decoration: none; border-bottom: 1px solid var(--rule); }
.card h3 a:hover { border-bottom-color: var(--accent); }
.card p { margin: 0 0 12px; }
.meta { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; font-size: .8rem; color: var(--muted); }
.badge { border-radius: 4px; padding: 2px 8px; font-size: .74rem; letter-spacing: .03em;
         border: 1px solid var(--rule); }
.badge.type { background: var(--accent); border-color: var(--accent); color: #fff; }
.badge.sector { background: var(--raise); color: var(--ink); }
.tag { font-size: .78rem; color: var(--muted); }
.tag::before { content: "#"; opacity: .5; }
.coverage { margin-top: 10px; font-size: .85rem; }
.coverage summary { cursor: pointer; color: var(--muted); }
.coverage ul { margin: 8px 0 0; padding-left: 20px; }
.supersedes { font-size: .82rem; color: var(--muted); margin-top: 8px; }

a { color: var(--accent); }
.more { margin: 18px 0 0; }
.more button { font: inherit; font-size: .9rem; padding: 8px 18px; border-radius: 999px;
        border: 1px solid var(--accent); background: var(--ground); color: var(--accent); cursor: pointer; }
.hidden { display: none !important; }
.count { color: var(--muted); font-size: .85rem; margin: 0 0 12px; }
footer { margin-top: 48px; padding-top: 18px; border-top: 1px solid var(--rule);
         color: var(--muted); font-size: .85rem; }

@media (max-width: 600px) {
  .wrap { padding-top: 24px; }
  header h1 { font-size: 1.35rem; }
}
@media print {
  .controls, .more { display: none; }
  .card { break-inside: avoid; box-shadow: none; }
  .card h3 a::after { content: " (" attr(href) ")"; font-size: .75rem; font-weight: normal; }
}
"""

FILTER_SCRIPT = """
(function () {
  var state = { tag: 'all', type: 'all', sector: 'all', month: 'all' };
  var cards = Array.prototype.slice.call(document.querySelectorAll('[data-item]'));
  var counter = document.querySelector('[data-count]');
  var more = document.querySelector('[data-more]');
  var cap = parseInt(document.body.getAttribute('data-cap') || '0', 10);
  var expanded = false;

  function matches(card, facet) {
    var want = state[facet];
    if (want === 'all') return true;
    // Split on the separator rather than substring-matching: "Men's health"
    // is inside "Women's health", and indexOf would quietly conflate them.
    var have = (card.getAttribute('data-' + facet) || '').split('|');
    return have.indexOf(want) !== -1;
  }

  function apply() {
    var shown = 0;
    cards.forEach(function (card) {
      var ok = matches(card, 'tag') && matches(card, 'type')
            && matches(card, 'sector') && matches(card, 'month');
      if (ok) shown += 1;
      var over = cap > 0 && !expanded && shown > cap;
      card.classList.toggle('hidden', !ok || over);
    });
    if (counter) {
      counter.textContent = shown === 1 ? '1 item' : shown + ' items';
    }
    if (more) {
      var overflow = cap > 0 && shown > cap && !expanded;
      more.classList.toggle('hidden', !overflow);
      if (overflow) {
        more.querySelector('button').textContent = 'Show all ' + shown + ' from this month';
      }
    }
  }

  document.querySelectorAll('[data-facet]').forEach(function (button) {
    button.addEventListener('click', function () {
      var facet = button.getAttribute('data-facet');
      state[facet] = button.getAttribute('data-value');
      document.querySelectorAll('[data-facet="' + facet + '"]').forEach(function (sibling) {
        sibling.setAttribute('aria-pressed', String(sibling === button));
      });
      expanded = false;
      apply();
    });
  });

  if (more) {
    more.querySelector('button').addEventListener('click', function () {
      expanded = true;
      apply();
    });
  }

  apply();
})();
"""


def render_card(item: BoardItem) -> str:
    """One item card, exactly the fields section 4 lists and nothing else."""
    tags = "".join(f'<span class="tag">{escape(tag)}</span>' for tag in item.tags)
    coverage = ""
    if item.coverage_urls:
        entries = "".join(
            f'<li><a href="{escape(url)}" rel="noopener noreferrer">{escape(_host(url))}</a></li>'
            for url in item.coverage_urls
        )
        label = "1 article" if len(item.coverage_urls) == 1 else f"{len(item.coverage_urls)} articles"
        coverage = (
            f'<details class="coverage"><summary>Reporting ({label})</summary>'
            f"<ul>{entries}</ul></details>"
        )
    supersedes = ""
    if item.supersedes:
        supersedes = (
            f'<p class="supersedes">Replaces an earlier item: '
            f'<a href="{escape(item.supersedes)}" rel="noopener noreferrer">previous version</a></p>'
        )
    return (
        f'<article class="card" data-item '
        f'data-tag="{escape("|".join(item.tags))}" '
        f'data-type="{escape(item.type)}" '
        f'data-sector="{escape(item.sector)}" '
        f'data-month="{escape(item.date_published[:7])}">'
        f'<h3><a href="{escape(item.primary_url)}" rel="noopener noreferrer">{escape(item.headline)}</a></h3>'
        f"<p>{escape(item.blurb)}</p>"
        f'<div class="meta">'
        f'<span class="badge type">{escape(item.type)}</span>'
        f'<span class="badge sector">{escape(item.sector)}</span>'
        f"<time datetime=\"{escape(item.date_published)}\">{escape(_long_date(item.date_published))}</time>"
        f"{tags}</div>"
        f"{supersedes}{coverage}</article>"
    )


def render_hot(topics: list[HotTopic]) -> str:
    """The block at the top: one plain-English line per topic, linking its items."""
    if not topics:
        return (
            '<section class="hot"><h2>Hot this month</h2>'
            "<p class=\"empty\">No topic drew three or more independent items this window. "
            "The feed below is the whole month.</p></section>"
        )
    lines = []
    for topic in topics:
        links = "".join(
            f'<a href="{escape(item.primary_url)}" rel="noopener noreferrer">{escape(_short(item.headline))}</a>'
            for item in topic.items
        )
        lines.append(f"<p>{escape(_hot_sentence(topic))}<br><span class=\"links\">{links}</span></p>")
    return '<section class="hot"><h2>Hot this month</h2>' + "".join(lines) + "</section>"


def _hot_sentence(topic: HotTopic) -> str:
    """Name the trend in one sentence: what converged, from where, of what kind."""
    sectors = topic.sectors
    where = sectors[0] if len(sectors) == 1 else ", ".join(sectors[:-1]) + " and " + sectors[-1]
    kinds = [t.lower() for t in topic.types]
    what = kinds[0] if len(kinds) == 1 else ", ".join(kinds[:-1]) + " and " + kinds[-1]
    return f"{topic.tag}: {topic.count} independent items this month across {where} — {what}."


def _facet_row(label: str, facet: str, values) -> str:
    buttons = [
        f'<button type="button" data-facet="{facet}" data-value="all" aria-pressed="true">All</button>'
    ]
    for value in values:
        buttons.append(
            f'<button type="button" data-facet="{facet}" data-value="{escape(value)}" '
            f'aria-pressed="false">{escape(value)}</button>'
        )
    return (
        f'<fieldset><span class="label">{escape(label)}</span>' + "".join(buttons) + "</fieldset>"
    )


def _page(title: str, subtitle: str, body: str, cap: int, generated: str) -> str:
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width, initial-scale=1">'
        f"<title>{escape(title)}</title><style>{PALETTE}</style></head>"
        f'<body data-cap="{cap}"><div class="wrap">'
        f"<header><h1>{escape(title)}</h1><p class=\"sub\">{escape(subtitle)}</p></header>"
        f"{body}"
        f'<footer>Swept weekly. Generated {escape(generated)}. '
        "Every blurb is written from the primary source, which is the link on each headline."
        "</footer>"
        f"</div><script>{FILTER_SCRIPT}</script></body></html>\n"
    )


def render_board(items: list[BoardItem], today: date | None = None, generated: str = "") -> str:
    """The 30-day main board: hot block, then one chronological feed."""
    board, _ = split_window(items, today)
    present = _present(board)
    controls = (
        '<section class="controls">'
        + _facet_row("Tag", "tag", [t for t in TAGS if t in present["tag"]])
        + _facet_row("Type", "type", [t for t in TYPES if t in present["type"]])
        + _facet_row("Sector", "sector", [s for s in SECTORS if s in present["sector"]])
        + "</section>"
    )
    feed = "".join(render_card(item) for item in board)
    more = (
        '<p class="more" data-more><button type="button">Show all from this month</button></p>'
        if len(board) > VISIBLE_CAP
        else ""
    )
    body = (
        render_hot(hot_topics(board))
        + "<h2>This month</h2>"
        + controls
        + f'<p class="count" data-count>{len(board)} items</p>'
        + feed
        + more
    )
    return _page(
        "Tactical Human Performance Board",
        "Research, policy, and news from the last 30 days — military, fire and rescue, EMS, and law enforcement.",
        body,
        VISIBLE_CAP,
        generated or _stamp(),
    )


def render_archive(items: list[BoardItem], today: date | None = None, generated: str = "") -> str:
    """The 12-month archive: same cards, filterable by tag and month."""
    _, archive = split_window(items, today)
    present = _present(archive)
    months = sorted(present["month"], reverse=True)
    controls = (
        '<section class="controls">'
        + _facet_row("Tag", "tag", [t for t in TAGS if t in present["tag"]])
        + _facet_row("Month", "month", months)
        + "</section>"
    )
    body = (
        controls
        + f'<p class="count" data-count>{len(archive)} items</p>'
        + "".join(render_card(item) for item in archive)
    )
    return _page(
        "Archive — Tactical Human Performance Board",
        "Everything that has left the 30-day board, kept for 12 months. Nothing is deleted.",
        body,
        0,                       # no cap: the archive is what you came here for
        generated or _stamp(),
    )


def _present(items: list[BoardItem]) -> dict[str, set]:
    """Which facet values actually occur. A filter for nothing is a dead button."""
    found: dict[str, set] = {"tag": set(), "type": set(), "sector": set(), "month": set()}
    for item in items:
        found["tag"].update(item.tags)
        found["type"].add(item.type)
        found["sector"].add(item.sector)
        found["month"].add(item.date_published[:7])
    return found


def _host(url: str) -> str:
    stripped = url.split("://", 1)[-1]
    return stripped.split("/", 1)[0] or url


def _short(headline: str, limit: int = 60) -> str:
    return headline if len(headline) <= limit else headline[: limit - 1].rstrip() + "…"


def _long_date(value: str) -> str:
    try:
        return datetime.strptime(value[:10], "%Y-%m-%d").strftime("%d %b %Y")
    except ValueError:
        return value


def _stamp() -> str:
    return datetime.utcnow().strftime("%d %b %Y")
