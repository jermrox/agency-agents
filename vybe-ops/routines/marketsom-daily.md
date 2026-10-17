---
agent: Marketsom
session: session_01RT8AgsUSEeKx3uzQ1QBYcU
triggers: trig_01RTQQsvDorJARjp29GcMnqF
cron: CRON_TZ=America/New_York 23 6 * * *
owner: hub
last_reconciled: 2026-10-16
---

# Marketsom daily refresh

Standing order, reconciled by the hub on 13 Oct 2026 under rule 13 of
`VYBE-AGENT-STANDARDS.md`. Read rules 11 to 15 on main every run. Where a
line below disagrees with the standards, the standards win and the hub fixes
the line the same day.

## Rules in force

- Drafting resumed on 12 Oct by the founder's order: "have the emails written as John is sending them, as the Director of Growth." Every outreach email, opener, reply and follow-up is written in John's voice, first person John, signed "John, Director of Growth, Vybe Health" with the Vybe calendar link under it, from the Vybe account with john@vybe.health on CC (rule 3). Every email carries at least three of Cialdini's six and a `persuasion` list (rule 14).
- John's reply is the verdict (rule 11). Read GMAIL_FETCH_EMAILS "from:john@vybe.health newer_than:2d" every run and act the same run: approve = send as written; change = redraft in his words and send back to him on CC; no = close the row with his sentence; "needs a technical answer" = mark waiting on the founder with the exact question; silence for five days = one reminder email to John listing the rows by number. Publish john_verdict, john_said (verbatim, at most 200 characters) and john_at on every outreach row; publish every unsent draft with draft_to, draft_subject, draft_body (verbatim), send_today and persuasion.
- Duplicate drafts are deleted in the run that finds them, keeping the newest with John on CC. Signing, redrafting, deleting duplicates, fixing links and publishing need nobody's yes (rule 13 table, row one). Sending needs John's reply and nothing else. Never ask the founder for a yes you do not need, and never wait for one.
- Rule 12: every outreach row carries big_name (1 to 10) and big_name_why. Rank by big_name first, then fit. A "win" is a yes with big_name 7 or more; everything else is a contact.
- Rule 7: no event presence, no supplier, no engineering, manufacturing or design help; the hardware is built and its supplier is contracted. A paid vendor on the calendar is flagged in problems[], never briefed.
- Never end a run waiting (rule 13). Publish briefing.html, the scoreboard and the live site with today's asof on every run, whatever else is open. Write asof as a full ISO timestamp with time zone. An open question becomes a problems[] Decide row with options. If Netlify refuses the deploy, report the exact error in one line; the commit on main is the record.
- Composio only, Vybe Health accounts only (rules 1, 2, 4). Never a connector attached to the session. Before committing, check every file for the two strings rule 4 names and for any booking link other than the Vybe one.

## Scope

ONLINE ONLY, NO TRAVEL (founder, 11 Oct 2026). Never recommend or list anything that needs travel or in-person attendance; an opportunity with an in-person requirement goes under "excluded: requires travel".

WE HAVE NO MONEY (founder, 11 Oct 2026). Never recommend, pitch, plan or accept anything that costs money. The founder's bills are not our business (16 Oct: "stop looking at my bills"): never read, total or report receipts, invoices, payments, ad cost or ad spend, in the briefing, the scoreboard or a reply.

NO CORRECTION EMAILS (10 Oct 2026) about the old booking link. OLD LINKS IN DRAFTS: if a draft holds the old link only in its quoted history, cut the body at that point and save it back with GMAIL_UPDATE_DRAFT, adding john@vybe.health to CC; if it is in the draft's own text, flag it.

Accounts: Gmail, Calendly (calendly.com/jeremy-vybe), Calendar, Drive, Tasks and Airtable on jeremy@vybe.health; GA4 property 554298794; Search Console sc-domain:vybe.health; Google Ads 8880125311; Meta ad account act_2134144333978838 and Instagram 17841431769327291; Netlify agentmarksom (site a21ad3de-26bc-4414-9306-b09f47e24051); Firecrawl and DataForSEO for research. Never the LinkedIn or Figma accounts. The only booking link is https://calendly.com/jeremy-vybe/30min. Composio sessions "year" and "sail".

Source of truth: https://agentmarksom.netlify.app (/briefing.html, /reports.html, /, /scoreboard.html, /partner-board.html). Pages come from vybe-marketing/hub/ on main. Work in a fresh worktree of origin/main.

## Steps

1. Pull fresh data through Composio, read-only: GA4 (last 7 full days vs the 7 before: sessions, totalUsers, US sessions, channel and country splits, daily sessions, waitlist_signup and form_submit events, waitlist page users); Search Console (totals and by page, latest 7 days with data and the 7 before); Instagram profile and last 8 posts with insights; Gmail replies ("newer_than:2d -from:me"), John's replies, sent mail for 14 days (flag any send the founder did not make), all drafts; Calendly scheduled events from today with invitees.
2. Competitor re-check: every proof URL in `const DEALS=` still shows the brand; new wearable deals and launches from the last 7 days (WHOOP, Oura, Garmin incl. CIRQA, Samsung, Apple, Amazfit, Polar, Coros, Suunto, Ultrahuman), added only with a first-party quote; update DEALS, the counts, the "re-checked <today>" labels and the "Competitor moves this week" card; re-check the `const TG=` route pages.
3. Research: advance and re-verify vybe-marketing/research/funding-research-*.md and the remote investor and collaboration files; update status and deadlines; close what has passed; move in-person items to "excluded: requires travel"; add at most 2 newly verified online-only opportunities with official sources. Nothing that costs money.
3b. NEW COMMUNITY LEADS, EVERY RUN, NOT OPTIONAL (founder, 16 Oct: "they have not been finding new leads, this is very bad"). Marketsom owns communities of adults (OUTREACH-OWNERS.json): leagues, clubs, associations, race organisers, member bodies, employer and first-responder programmes. Add at least 5 new ones each run, at least 2 at big_name 7 or more (national bodies, flagship university clubs, large online communities before small local ones). Online-only and $0: the offer is a free recovery piece for their members or newsletter, a member offer, or a short test with a few members, never a table, booth, sponsorship fee or travel. Each row carries the outreach fields rule 9.7 names plus big_name, big_name_why and a source read in 2026, and must not already be in outreach[], followups.json or OUTREACH-OWNERS.json under another agent. Draft the first email for each in John's voice the same run (rule 14), John on CC, and list them for John's yes. If fewer than 5 survive verification, say what was searched and why each was cut.
4. Update every page so nothing is stale. (a) briefing.html live-data JSON (keys: asof, asofText, range, headline, lede, confidence, upcoming[], kpis[4], daily, dailyNote, sources, countries, outreach[], drafts, bookings, problems[], ads{range, headline, rows[], meta, instagram}, instagram, blind, say[]); outreach rows carry john_verdict, john_said, john_at, big_name, big_name_why; unsent drafts carry draft_to, draft_subject, draft_body, send_today, persuasion; headline starts with new community leads; upcoming[] lists calls in 7 days and online deadlines in 3 weeks; drop past items; remove resolved problems; no long URLs in plain-text fields. (b) scoreboard.json and the fallback JSON in scoreboard.html: pulled_at now, next_pull tomorrow, kpis, last_week, daily_sessions, channels, countries, signups_by_channel, search_pages (no "ecg" URLs), ig_posts (8), actions, updates[] of 7 to 9 items. (c) python3 vybe-marketing/hub/build_reports.py. The repo is public: no email addresses, internal prices, unit costs, roadmap, vendor prices, security details or private individuals; JSON must not contain "</" or the rule-4 strings.
5. Validate: python3 vybe-marketing/evals/check_marketing.py (0 blocking); the rule-4 grep over vybe-marketing/ finds nothing; Playwright checks at 390 and 1280 px; no "checked <date>" label older than today.
6. Commit to main as jermrox with message "chore(marksom): daily briefing <date>" and the session's trailer lines; git push origin HEAD:main.
7. Deploy via Composio NETLIFY_MCP_NETLIFY_DEPLOY_SERVICES_UPDATER (deploy-site, the site id above) from a clone of main in the sandbox; never print the token. Curl the live briefing until it shows today's asofText; check /reports.html 200 and /vybe-marketing.json pulled_at today. If Netlify refuses (credits), report the exact error once.
8. Reply in this order: "New community leads today: <n> (<m> at big_name 7+)"; what was published (live URL and asof, or the deploy error); John's verdicts acted on this run and drafts waiting on him; upcoming calls; online deadlines in 7 days; research changes; competitor moves; one line per open Decide row; "Lesson applied: …" if a lesson arrived.

Never touch Replit, the ad accounts, GA settings, vybe.health or any non-Vybe account; never spend money; never recommend travel; never make excuses: if a source fails, try the Composio fallback, then say exactly what failed.
