# Vybe Health — Marketing Scoreboard, baseline (pulled 30 Sep 2026)

First scoreboard. Every number below was read live through the Composio
connections on 30 Sep 2026; the source and window sit next to each one.
"Unknown" means no connected source can see it yet. Nothing here is estimated.

Windows: GA4 is the 30 days to 29 Sep. Search Console is 31 Aug to 27 Sep
(its data lags about three days). Instagram is lifetime per post and the 28
days to 29 Sep for account reach.

## North star

| Metric | Value | Source | Note |
|---|---|---|---|
| Waitlist signups (`waitlist_signup` event) | **4** in 30 days | GA4 | 2 from Display, 1 Organic Social, 1 Paid Search |
| Form submits (`form_submit`, any form) | 41 | GA4 | 24 Paid Search, 14 Cross-network, 2 Display, 1 Organic Social |
| Builder / partner inquiries | unknown | — | The waitlist form has a "partnership" option; where submissions land is not connected |
| Cost per waitlist signup | unknown | — | Google Ads is not connected |

## Site traffic (GA4, 30 days to 29 Sep)

| Channel | Sessions | Engaged | Share |
|---|---|---|---|
| Paid Search (Google) | 6,644 | 1,291 (19%) | 65% |
| Display, campaign "Vybe Health - 9/15" | 2,961 | 711 (24%) | 29% |
| Cross-network | 383 | 226 | 4% |
| Direct | 190 | 70 | 2% |
| Organic Social | 21 | 16 | <1% |
| Organic Search | 2 | 2 | <1% |
| **Total** | **10,242** | | |

| Country | Sessions | Engaged |
|---|---|---|
| India | 6,636 | 1,523 |
| Bangladesh | 1,594 | 321 |
| Pakistan | 899 | 221 |
| Egypt | 164 | 47 |
| **United States** | **131** | **85 (65%)** |

Daily shape: two paid bursts, 16 to 18 Sep (1,516 / 1,985 / 2,922 sessions) and
23 to 25 Sep (410 / 1,832 / 699), then a tail under 150 a day.

Pages (views): home 13,192; `/waitlist` 219 (104 users); `/workspace/login` 59;
`/ecosystem` 40; `/about` 14; `/contact` 14; `/learn` 12; `/faq` 9; `/band` 7;
all `/learn/*` articles together about 21.

## What the traffic data says

1. **Paid traffic is going to the wrong countries.** About 90% of sessions are
   from India, Bangladesh and Pakistan. The US, where the founding batch ships,
   got 131 sessions. US visitors engaged at 65%; South Asian paid visitors at
   roughly 20%. Whatever the Google Ads geo setting is, it is not "United States".
2. **Ten thousand sessions produced four waitlist signups.** The waitlist page
   was viewed 219 times. Either the signup event does not fire on every real
   signup (41 form submits versus 4 signup events) or the traffic is not buying.
   Both need checking before another dollar is spent.
3. **GA4 key events are polluted.** Fourteen events are marked as key events,
   including `page_view`, `session_start`, `first_visit`, `scroll` and
   `user_engagement` (all marked on 26 Sep). "Conversions" therefore read as
   1,000+ while real signups are 4. If Google Ads imports these, it is bidding
   toward page views. Keep `waitlist_signup`, `form_submit` and `purchase`.
   Unmark the other eleven.
4. **Organic is at zero.** 2 organic search sessions, 15 Search Console
   impressions, 0 clicks. The only queries with any impressions are HRV
   phrases, at positions 83 to 92. Two pages show early promise on single
   impressions: `/compare/oura-ring-alternative/` (position 7) and
   `/learn/screenless-health-wearable/` (position 8).

## Instagram @vybehealthinc (live 30 Sep)

| | Value |
|---|---|
| Followers / following | 29 / 117 |
| Posts | 4, all since 23 Sep, all static images |
| Account reach, 28 days | 2,207 (unexplained: the four posts reached 63 accounts combined; check whether a boost or ad ran) |

| Post (date) | Reach | Likes | Comments | Saves | Shares |
|---|---|---|---|---|---|
| "No Subscription. Now that's a Vybe" (23 Sep) | 21 | 3 | 1 | 0 | 0 |
| "30 days of battery" (25 Sep) | 17 | 1 | 0 | 0 | 0 |
| "A health band you forget you're wearing" (26 Sep) | 19 | 2 | 0 | 0 | 0 |
| "Why rent access to your own health data?" (29 Sep) | 6 | 0 | 0 | 0 | 0 |

No Reels have been posted yet. The Reels program (4 a week) has not started
on this account. Zero saves and zero shares across all posts.

## Facebook

Not readable. The connected Facebook account is a personal profile with no
Page permissions, so the Vybe Page's followers and posts cannot be pulled.
Reconnect with Page access.

## Email

Unknown. No email platform is connected and it is not known where waitlist
submissions are stored.

## Other connected sources

| Source | State |
|---|---|
| Google Search Console | Connected as site owner for `sc-domain:vybe.health` |
| Airtable | One base, "Vybe Intelligence", containing an empty default table |
| Firecrawl | Working, 1,400 credits; used to read vybe.health, which the agent sandbox cannot reach directly |
| Google Ads | Not connected (auth link issued, not completed) |
| LinkedIn, Reddit | Not connected (auth links issued, not completed) |

## Next scoreboard

Pull the same tables on Mon 5 Oct after the key-event fix and the geo fix, and
record the first clean week as the baseline for Q4 targets.
