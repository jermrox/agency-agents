# Vybe Health marketing

Working files for the [Vybe Health Marketing Director](../marketing/marketing-vybe-health-marketing-director.md)
agent. The Reels program has its own dashboard and lives with the
[Vybe Reels Strategist](../marketing/marketing-vybe-reels-strategist.md).

| File | What it is |
|---|---|
| `concept.md` | **Read first.** The concept in one line, the product promises, crowded vs unclaimed claims, which half leads on which channel, the eight-question concept check, open founder tensions and the learning log. |
| `scoreboard-YYYY-MM-DD.md` | A dated scoreboard pulled from the connected sources. One per pull; the newest is current. |
| `plan-2026-q4.md` | The quarter's plan, with the week-1 fixes at the top. |
| `brand-brief.md` | Messaging House and Claim Register. The Claim Register is the gate every piece of copy passes. |
| `scoreboard.json` | The latest scoreboard as data. The dashboard reads it. |
| `marksom.json` | Audiences, wedge scores, 35 sourced targets, channels, platform targeting rules and eval runs. The Marksom hub reads it. |
| `hub/` | The Marksom site. `template.html` is the hub source; `index.html` is the template with `marksom.json` embedded; `scoreboard.html` is the weekly scoreboard. |
| `evals/` | The agent's self-evaluation: `rubric.md` and `cases.md` (targeting), `concept-test.md` (concept knowledge and copy fidelity), `check_marketing.py` (guardrail) and dated results. |
| `linkedin-company-page.md` | LinkedIn company page tagline, About and fields, with the concept check. |
| `seo-plan.md` | Search plan: commercial pages, pillar pages, headline bank, and what must be measured before production order is locked. |

## Dashboard

[`hub/scoreboard.html`](hub/scoreboard.html) is published only by the
agent's own Netlify site, agentmarksom, at
`https://agentmarksom.netlify.app/scoreboard.html`. No other site (agentrevup,
agentresearchsum) publishes anything from this folder. The build
(`scripts/build-netlify-site.sh`, target `marksom`) copies `scoreboard.json` to
`/vybe-marketing.json`; the page fetches it and falls back to the copy built
into the page if the feed is missing. When the feed changes, also re-embed it
in the page so both stay identical:

```
python3 - <<'PY'
import re
p = "vybe-marketing/hub/scoreboard.html"
h = open(p).read()
feed = open("vybe-marketing/scoreboard.json").read().replace("</", "<\\/")
h = re.sub(r'(<script type="application/json" id="fallback">).*?(</script>)',
           lambda m: m.group(1) + feed + m.group(2), h, flags=re.S)
open(p, "w").write(h)
PY
```

The repository and the Netlify URL are public. The page carries `noindex`,
which keeps it out of search results but does not make it private.

## Data sources

All reads go through the Composio connections on the founder's account.
Nothing in these files is typed from memory.

| Source | What it gives | State on 30 Sep 2026 |
|---|---|---|
| Google Analytics 4, property `properties/554298794` | Sessions, users, channels, countries, pages, events, key events | Connected |
| Google Search Console, `sc-domain:vybe.health` | Impressions, clicks, queries, pages, position | Connected, site owner |
| Instagram @vybehealthinc (business account `28956456617305868`) | Followers, media, per-post reach, saves, shares, account reach | Connected |
| Facebook | Page followers and posts | Connected as a personal profile only; no Page access yet |
| Firecrawl | Reads vybe.health pages as markdown (the agent sandbox cannot reach the site directly) | Connected, 1,400 credits |
| Airtable, base "Vybe Intelligence" | Could hold the lead and claim registers; empty today | Connected |
| Netlify | Site deploys; route for shipping `llms.txt` and schema | Connected |
| Google Ads | Spend, campaigns, cost per signup | Not connected |
| LinkedIn, Reddit | Founder posts; community listening | Not connected |

## Refreshing the scoreboard

Ask the Marketing Director agent to "pull the scoreboard". It reads GA4
(channels, countries, daily sessions, pages, events), Search Console (queries,
pages), Instagram (profile, media, per-post insights) and writes a new dated
`scoreboard-YYYY-MM-DD.md`, rewrites `scoreboard.json`, and re-embeds it in the
dashboard. A weekly routine does this every Monday morning.

## Marksom (the agent's own site)

The Netlify site `agentmarksom` builds from this repository with
`scripts/build-netlify-site.sh` (target `marksom`): the hub at `/`, the
scoreboard at `/scoreboard.html`, and both JSON feeds. After changing
`marksom.json` or `hub/template.html`, rebuild the hub page:

```
python3 - <<'PY'
h = open("vybe-marketing/hub/template.html").read()
feed = open("vybe-marketing/marksom.json").read().replace("</", "<\\/")
open("vybe-marketing/hub/index.html", "w").write(h.replace("__DATA__", feed))
PY
```

Then run `python3 vybe-marketing/evals/check_marketing.py`. Like the
scoreboard, the hub is public; `noindex` keeps it out of search results only.
