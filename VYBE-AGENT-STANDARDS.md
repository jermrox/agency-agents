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

The operations console (`vybe-ops.netlify.app`) is the reference. It is the
hub's own site: it reads every agent's dashboard live, toggles between the
roll-up and each agent, and embeds each agent's real page. The four-hourly
snapshot at `agentrevup.netlify.app/vybe-hub.html` is its fallback. Every Vybe
dashboard follows the console:

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
6. **Every dashboard links to the console, and the console links to every
   dashboard.** One front door, no orphans.

An agent regenerating its dashboard brings it to this shape on its next run.
A new page that does not follow it is a defect, not a style choice. The hub's
`needs_you` feed in `vybe-agents.json` is the canonical card format; an agent
may publish its own items in that shape and the hub will carry them.

7. **Every lead carries the decision fields.** The founder, 12 October: "I
   need metrics and data points… who answered, what are they, what are they
   offering, why we need them or why they need us, scale 1–10, good choice and
   why… you need to help me make a decision." The console scores every lead
   1–10 from the agents' own fields and prints the reasoning. It can only do
   that when the fields exist. So every outreach row, target or opportunity
   an agent publishes carries, as separate machine-readable fields, never
   folded into a sentence:

   | Field | What goes in it |
   |---|---|
   | `org` | the organisation (never a person; rule 7) |
   | `what_is` | one plain sentence: what they are, who they serve, how big (members, users, followers, cheque size), with the source |
   | `status` | one of `drafted`, `waiting`, `replied`, `booked`, `declined`, `closed` — what *they* have done, not what we have drafted |
   | `offer` | what they offered or asked for, in their words, or empty |
   | `we_need` | why Vybe needs them: the collaboration, cheque or revenue in one sentence |
   | `they_need` | why they need Vybe, or what they asked us for, in one sentence |
   | `cost` | a number in dollars; 0 is a value, missing is a defect |
   | `next_date` | ISO date of the next step or deadline, or empty |
   | `size` | the audience, member count or cheque as a number, with `size_source` |

   The console treats a missing field as "unavailable" and scores it down. An
   agent is not done with a lead until a stranger could read these nine
   fields and decide. Marketsom's `outreach[]`, Growsom's `targets[]` and
   `followups.threads[]`, and Revsom's `opportunities[]` all conform by their
   next run; Instasom's `people` already carries the equivalent.
8. **Vendors, suppliers and paid slots are never leads.** They do not get a
   score, a card or a milestone on any Vybe dashboard. The console lists them
   once, by name, under "out of scope", and nowhere else. An agent that keeps
   one in its outreach table marks it `status: closed` with `why: rule 7`.

## 10. The hub orchestrates. Agents implement.

The founder, 11 October: "I ask them to add something and they add it, but it
is not holistic or even thought about in their current design." Five agents
were taking requests as bolt-ons because nobody had said there is a system, a
shape, and someone responsible for the whole.

There is. The hub — the operations console at `vybe-ops.netlify.app` and the
session that runs it — is the orchestrator of every agent with Vybe in its
name. Agents own their lane and their craft. The hub owns how the lanes fit.

**When the founder asks an agent for a change, the agent does this, in order:**

1. **Check the system first.** Read rules 1–9 and the agent's own charter.
   Ask: where does this appear in the console, which card does it become,
   which other agent's lane does it touch, and what breaks if it is bolted
   on? If the answer is "it does not fit", that is the finding — not a reason
   to bolt it on anyway.
2. **Say how it fits before building it.** One paragraph, BLUF form: what the
   change is, where it lives in the shared shape, what it touches, and what
   the founder will see on the console afterwards. If it needs another
   agent's lane or a change to the shared shape, hand it to the hub instead
   of building it.
3. **Build it so the console shows it.** Every new thing an agent produces
   is a card — what it is, why it matters, what you do, a link — or it is a
   number in the agent's feed with a timestamp. A page element the console
   cannot read does not count as done.
4. **Report to the hub, not just the founder.** The run report names the
   change, the card or field it became, and the live URL where it is.

**What the hub does:**

- Holds the shared shape (rule 9) and the card format, and changes them for
  everyone or for no one.
- Reads every live surface and the feeds behind them, and turns red when a
  dashboard stops linking to the console, drops the fields the console reads,
  or carries anything the standards forbid.
- Receives anything that crosses lanes or needs the shape to change, and
  decides it — or puts the decision to the founder as a question with
  options.
- Issues standing orders into each agent's session when the system needs
  them, and expects a reply.

**What this is not.** The hub does not do the agents' jobs, does not rewrite
their research, and does not run their routines. It also does not touch any
agent without Vybe in its name — rule 6 binds the hub hardest of all.

A change made without steps 1 and 2 is not an improvement, whoever asked for
it. The founder asking is the start of the design check, not a substitute for
it.

**The hub teaches, every day.** The founder, 11 October: "make sure you help
teach and make them learn every day — that's your additional duty." So once a
day, after every agent has run, the hub reads each Vybe agent's latest report
and live page against rules 1–9 and its charter, and sends each agent one
lesson: the single most useful correction from that day's work, with the rule
it comes from and what to do differently tomorrow. One lesson, not a list;
specific to that day's output, never generic. The agent carries the lesson
into its next run and says in one line what it changed. Lessons are logged in
`VYBE-LESSONS.md` so a repeated mistake is visible as a pattern and a fixed one
is visible as progress. The hub does not grade agents against each other; it
raises each one against its own standard.

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
