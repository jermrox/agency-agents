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

Each agent's own task, purpose, conditions and standards — and the live figures
it is actually pulling — are in [VYBE-AGENT-CHARTERS.md](VYBE-AGENT-CHARTERS.md).

## 6. Only Vybe agents

An agent with Vybe in its name touches Vybe work and nothing else. Never read,
edit, enable, disable, delete, wake or interrupt a routine, session, dashboard
or account belonging to an agent without Vybe in its name — Leadsom (i-Grow),
Researchsom and Crawlsom (MOPs and MOEs), Babysom. Not to audit them, not to
compare them, not to check whether they are healthy. Their prompts hold another
venture's accounts, record ids and customer names, and reading one is how that
material ends up quoted back into Vybe work.

Set by the founder on 11 October 2026, after an audit of every routine on the
account read the other ventures' prompts and summarised them in a Vybe thread.
Nothing was changed in them; reading them was already outside the remit.

When something needs checking across the whole account, check only the Vybe
rows and say so. A Vybe agent that cannot answer a question without reading
another venture's agent reports that it cannot, and stops.

**The mechanism, because the rule alone did not hold.** The violation came from
listing every routine on the account and reading the results. So: never list
all routines or all sessions to audit them. Look up the Vybe ones by their own
ids, one at a time. The Vybe routines and sessions are named in the charters;
anything not on that list is not ours to open. If a listing is unavoidable,
read only the rows whose session is a Vybe session and do not quote, summarise
or act on any other row — not even to say it looks healthy.

The founder restated this on 11 October after the rule was already written:
"only vybe agents, do not touch the others whatsoever." There is no audit, no
comparison and no health check that justifies opening one.

## 7. What outreach is for

Vybe outreach has three purposes and no others: **collaboration, investment,
and revenue**. Set by the founder on 11 October 2026 — "there are ways to make
money and that's the goal for all of these in reality."

**Never an event presence.** No table, booth, tent, expo stand, vendor slot,
exhibitor space, sampling stand or race activation, paid or free. Vybe does not
have the bandwidth to staff one. The only allowed use of those words is
declining one that was already offered. By 11 October, 19 of Marketsom's 49
logged emails had pitched exactly this, four of them already dead.

**Never a supplier.** Battery manufacturers, PCBA and sensor vendors, contract
engineering and product-development firms sell *to* Vybe. Approaching one is
procurement, it belongs to the founders, and it is not an outreach lane. Growsom
had emailed a battery maker, an ECG-patch PCBA supplier and three engineering
firms as "partners", and one of them has a call booked.

**Never an individual.** Outreach goes to organisations and role inboxes.

**One organisation, one owning agent, one ask.** Ownership follows what the
organisation is, not which agent emailed first, because the first email was
often the wrong ask:

| Lane | Owner |
|---|---|
| Investors; apps, data platforms, aggregators, SDK and integration partners, developer communities, research labs as design partners | **Growsom** |
| Communities of adults: leagues, clubs, associations, race organisers, member bodies, employer and first-responder programmes | **Marketsom** |
| Suppliers, manufacturers, contract engineering | **Nobody** — the founders |

[OUTREACH-OWNERS.json](OUTREACH-OWNERS.json) holds the assignment for every
contested organisation. An agent that finds an organisation owned by the other
one does not email it, does not reply in its threads, and says so instead.

`scripts/check-vybe-outreach.py` enforces this in CI. Emails logged before
11 October are reported as the record and never fail the build; a post-rule
email that pitches a stand or a supplier, or a second agent touching an
organisation with no owner, does.

## 8. BLUF, then task, conditions, standards

Every report, brief, email and dashboard page leads with the bottom line. The
founder has asked for this more than once, in these words: the agents give
"a lot of information but not a BLUF, tasks, conditions, standards, and what
it is, what needs to happen."

The order is fixed:

1. **BLUF** — the bottom line in three sentences or fewer. What it is, what
   state it is in, what has to happen next. A reader who stops here is not
   missing the point.
2. **What it is** — the thing or the counterparty in plain words. Who they
   are, what they do, how big, where. Never a name the reader has to go and
   research.
3. **Task / Conditions / Standards** — the task in one sentence; the
   conditions actually in force; the standards as numbered, measurable rows.
4. **What has to happen** — named actions with an owner and a date, and
   separately the decisions only a human makes, each stated as a question
   with the options.

A report that ends without a decision or an action is not a report, it is
research. Volume is not the deliverable: if a reader has to go and find out
who a company is, what a term means, or what is being asked of them, the
report has failed and the agent has handed its work back to the founder.

Three rules of thumb that follow from this:

- **Define on first use.** An acronym, a part number, a certification or a
  programme name gets a clause explaining it the first time it appears.
- **One page if one page does it.** Length is never evidence of effort.
- **Never bury the ask.** If something is needed from the reader, it is in the
  BLUF, not at the bottom.

## 9. One shape for every dashboard

Five agents built five dashboards that look and read like five different
companies. The founder, 11 October: "look at all the agents' dashboards — you
should literally be designing the same. There is no organisation here."

The hub (`agentrevup.netlify.app/vybe-hub.html`) is the reference. Every Vybe
dashboard follows it:

1. **The first screen answers "what needs a human" before anything else.**
   Each item is a card in a fixed order: *when — what* · **What it is** (who
   the counterparty is, in one plain sentence) · **Why it matters** (the
   honest so-what, including "this would cost us money" or "this is not for
   the company") · **What you do** (numbered steps a person can follow) · the
   two links (the thing itself, and our drafted material).
2. **Numbers after decisions, never instead of them.** Counts and tables come
   below the cards.
3. **One palette, one type scale.** The tokens in `scripts/vybe-agent-board.py`
   (`--brand #1f8e78`, `--good`, `--crit`, `--warn`, the surface greys, dark
   mode) are the only ones. A dashboard that needs a colour the tokens do not
   have does not need it.
4. **Phone first.** A card is readable at 390px without zooming or sideways
   scrolling. If it is not, it is not finished.
5. **Define on first use.** A programme, a company, a part, an acronym gets
   its clause the first time it appears. Rule 8 applies to pages as much as to
   emails.
6. **Every dashboard links to the hub, and the hub links to every dashboard.**
   One front door, no orphans.

An agent regenerating its dashboard brings it to this shape on its next run.
A new page that does not follow it is a defect, not a style choice. The hub's
`needs_you` feed in `vybe-agents.json` is the canonical card format; an agent
may publish its own items in that shape and the hub will carry them.

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
accounts. Their own domains belong in their own files, and by rule 6 no Vybe
agent reads or changes anything of theirs.
