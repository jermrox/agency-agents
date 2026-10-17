---
agent: Hub
session: session_013HHJWeDrTdszmAhpng4tZh
triggers: trig_01XFpoqXFt2Tsi4FoWBqLFnY
cron: 5 13,21 * * 1-5
owner: hub
last_reconciled: 2026-10-17
---

# Hub inbox triage

Standing order under rule 13 and rule 15 of `VYBE-AGENT-STANDARDS.md`. The
founder, 15 Oct: "we need to be proactive here and make sure we are looking
at the emails." Twice each weekday the hub reads the Vybe inbox itself, so a
reply or an approval never waits on an agent that is stuck. On 15 Oct
the first pass found four follow-ups John had approved three days earlier
that no agent had sent and a partner asking
to reschedule.

## Rules in force

- Composio only, jeremy@vybe.health only (Gmail account gmail_roust-maim), read through Composio. Never a connector attached to the session. Before any send or draft, check the body for the two strings rule 4 names and stop if either appears.
- Rule 11: John's reply is the verdict. When John has said APPROVE on a numbered row and the agent that owns it has not sent it within one working day of the due date, the hub sends exactly the approved text as a reply on the original thread, signed "John, Director of Growth, Vybe Health" with john@vybe.health on CC and the Vybe Calendly link, then tells the owning agent with a one-shot note so it never sends it again. A NO or a CANCEL closes the row; a conditional or reserve is never sent.
- Rule 7 overrides an approval: a booth, table, expo, stand, travel or supplier ask is never sent, even if approved; it goes to the founder's report as a decision.
- Everything else outward (a reply to a partner, a reschedule, a decline) is drafted in Gmail on its thread for the founder or John to send, and named in the report with its draft link. Rule 14 applies to every new outreach draft (at least three of Cialdini's six and a persuasion list).
- The founder's bills are not the hub's business (founder, 16 Oct: "stop looking at my bills"). Never open, total or report a receipt, invoice, payment, billing or ad-spend message. Spend is never started or stopped by the hub.
- Never end a run waiting (rule 13). A blocked tool is one line in the report.

## Steps

1. GMAIL_FETCH_EMAILS for `in:inbox newer_than:2d -category:promotions -category:social` (metadata only), plus `from:john@vybe.health newer_than:5d` and `in:sent newer_than:2d`.
2. Sort every message into one of: John's verdicts; partner replies; account or security notices; waitlist sign-ups; noise. Bills, receipts, payments and ad-account mail are skipped unread. Open the full thread only for the first two.
3. For John's verdicts, cross-check the sent folder: anything approved and past due is sent under the rule above; anything sent twice is flagged.
4. For partner replies, draft the reply on its thread and record the draft id.
5. Check that nothing sent from the Vybe inbox in the last two days carries the two strings rule 4 names or a booking link other than calendly.com/jeremy-vybe, and that nothing Vybe went to jeremy@socialsips.io or any address outside vybe.health that the founder has not named.

## Report

At most six lines to the founder, no bills or spend: what the hub sent and why; each draft waiting for a human, with who it is to and the one decision it needs; anything urgent with a date; and any rule-4 or wrong-link finding.
