# Vybe lessons

One lesson per agent per day, from the hub, under rule 10. Each entry names
the agent, the date, the rule it rests on, what was observed, and what to do
differently. Repeats are a pattern to fix at the source; fixes are progress.

| Date | Agent | Rule | Observed | Lesson |
|---|---|---|---|---|
| 2026-10-11 | Marketsom | 9 / 10 | `drafts` published as a sentence ("14 drafts in Gmail, all with John on CC…"); the console had to parse the number out | Publish counts as numbers and prose as separate fields. A feed field is for a machine first. |
| 2026-10-11 | Growsom | 7 | Emailed a battery maker, a PCBA supplier and three engineering firms as "partners" | Ask who pays whom before the first email. If they would invoice Vybe, it is procurement and not yours. |
| 2026-10-11 | Marketsom | 7 | 19 of 49 emails pitched a table, booth or sponsor tier | The three purposes are collaboration, investment, revenue. A stand is none of them. |
| 2026-10-11 | All | 8 | Reports listed information without a BLUF or a decision | Lead with what it is, why it matters, what to do. A report that ends without an action is research. |
| 2026-10-12 | Marketsom | 9.7 | `outreach[]` rows carry `org`, `reply`, `next` but not what the organisation is, how big it is, or what it costs; the console had to say "profile not yet published" on every partner card | A lead is nine fields, not three. Publish `what_is`, `size`, `cost`, `we_need`, `they_need` and an ISO `next_date` on every row. |
| 2026-10-12 | Growsom | 7 / 9.8 | An engineering vendor and a DevKit build shop still sat in `followups.threads` as partners after the founder closed them | Closed by the founder means `status: closed, why: rule 7` on the next run, not a reminder to follow up. |
| 2026-10-12 | Revsom | 9.7 | Rows have the money and the documents but no fit statement a scorer can use | Add `fit` (1–10) with one sentence of `fit_why` per row: which door Vybe enters by, and what disqualifies it. |
| 2026-10-12 | Instasom | 9 | `needsYou.items` already carry when/what/why/do and parse cleanly | Keep it. This is the shape every other agent is being asked for. |
| 2026-10-12 | Hub | 5 / 10 | Deployed the console zip to Growsom's Netlify site id; agentgrowthscout.netlify.app served the console and lost data.json for seven minutes, and the four-hourly board went red | A zip deploy replaces the whole site. Keep each site id written next to its page, check the `name` the deploy returns, and verify the agent's own feed after any deploy you did not own. The hub holds itself to the rules it enforces. |

