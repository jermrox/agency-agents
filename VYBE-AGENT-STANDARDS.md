# Vybe Health agent standards

Binding on every agent with Vybe in its name. Set by the founder on 10 October
2026 after the same mistake reached about fifty partner organisations.

`scripts/check-vybe-standards.sh` enforces what can be checked mechanically,
and CI runs it on every pull request. A change that breaks a rule below fails
the build rather than reaching a partner's inbox.

## 1. Composio only

Every account read, email, draft, forward and deploy goes through Composio:
`COMPOSIO_MULTI_EXECUTE_TOOL`, `COMPOSIO_REMOTE_WORKBENCH`,
`COMPOSIO_REMOTE_BASH_TOOL`.

Never a connector attached directly to a session — not `mcp__Gmail__*`,
`mcp__Calendly__*`, `mcp__Google_Drive__*`, `mcp__Google_Calendar__*`,
`mcp__Slack__*`, `mcp__Airtable__*`, `mcp__Exa__*` or `mcp__AdWhispr_Ads__*`.
Those sign in as the founder's other company, which is how a non-Vybe calendar
link ended up in every drafted opener.

Allowed outside Composio, because no account is involved: git in this
repository, reading local files, `WebSearch` and page fetches for public
research, and publishing a Claude artifact.

When a Composio call fails, retry it or use the documented Composio fallback.
Never substitute a session connector, and never report "can't" while a retry is
still available.

## 2. Vybe Health accounts only

| What | Account |
|---|---|
| Gmail | jeremy@vybe.health (Composio `gmail_roust-maim`) |
| Calendly | calendly.com/jeremy-vybe (Composio `calendly_saxe-sparm`) — one active event type, "30 Minute Meeting", slug `30min` |
| GA4 | property 554298794 |
| Google Ads | customer 8880125311 |
| Meta Ads | act_2134144333978838 |
| Instagram | @vybehealthinc (17841431769327291) |
| Facebook Page | 1235241226349802 |
| Search Console | sc-domain:vybe.health |
| Netlify | agentrevup, agentmarksom, agentgrowthscout, instasum |

Nothing belonging to the founder's other ventures appears anywhere in Vybe
work — not as a sender, a calendar, a link, a signature or a stored record.
LinkedIn and Figma are connected under non-Vybe accounts and stay unused until
Vybe accounts exist for them.

Facebook and Meta Ads are reached through personal logins. That is read-only
access to Vybe's own ad account and Instagram, and it is the one accepted
exception.

## 3. Every email has John on CC

Every email from jeremy@vybe.health carries john@vybe.health as CC, including
in-thread replies. An email that cannot include John is cleared with John
first. Agents draft; the founder sends.

## 4. Check before you send or publish

Before any send, commit or publish, search the text for `i-grow` and
`jeremylahn`. If either appears, do not send — say so instead. This is the
check that would have caught the Calendly link before it went out fifty times.

## 5. A dashboard is not updated until its live URL says so

Several agents publish to more than one surface — a Netlify site, a JSON feed
and a private Claude artifact. Fixing the repository updates none of them.
After any change, fetch each live URL and confirm the new content and a current
timestamp. Report the live URL, never the commit.

## Who this binds

| Agent | Session | Surfaces |
|---|---|---|
| Revsom | funding, apply page | agentrevup.netlify.app, `/apply` |
| Marketsom | marketing | agentmarksom.netlify.app (hub, briefing, reports, scoreboard, partner board) |
| Growsom | investors, sponsors, outreach | agentgrowthscout.netlify.app, its data feed, its private artifact |
| Instasom | Instagram and Facebook | instasum.netlify.app/all.json |
| Vybe daily/weekly worker | product screens, funding rows, packets, decks | merges to `main`; the Apply artifact |

Agents without Vybe in the name (Leadsom for i-Grow, Researchsom and Crawlsom
for MOPs and MOEs, Babysom) are outside this document and keep their own
accounts. Their own domains belong in their own files.
