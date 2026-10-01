# Vybe Health marketing

Working files for the [Vybe Health Marketing Director](../marketing/marketing-vybe-health-marketing-director.md)
agent. The Reels program has its own dashboard and lives with the
[Vybe Reels Strategist](../marketing/marketing-vybe-reels-strategist.md).

| File | What it is |
|---|---|
| `scoreboard-YYYY-MM-DD.md` | A dated scoreboard pulled from the connected sources. One per pull; the newest is current. |
| `plan-2026-q4.md` | The quarter's plan, with the week-1 fixes at the top. |
| `brand-brief.md` | Messaging House and Claim Register. The Claim Register is the gate every piece of copy passes. |
| `scoreboard.json` | The latest scoreboard as data. The dashboard reads it. |

## Dashboard

[`dashboards/vybe-marketing-dashboard.html`](../dashboards/vybe-marketing-dashboard.html)
is published by the agentrevup Netlify site at
`https://agentrevup.netlify.app/vybe-marketing-dashboard.html`. The build
(`scripts/build-netlify-site.sh`) copies `scoreboard.json` to
`/vybe-marketing.json`; the page fetches it and falls back to the copy built
into the page if the feed is missing. When the feed changes, also re-embed it
in the page so both stay identical:

```
python3 - <<'PY'
import re
p = "dashboards/vybe-marketing-dashboard.html"
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
