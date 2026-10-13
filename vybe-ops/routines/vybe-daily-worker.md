---
agent: Daily worker (runs inside the hub session)
session: session_013HHJWeDrTdszmAhpng4tZh
triggers: trig_01DoSjEdMyKjVQrxiJv8tRAK
cron: 0 12 * * 1-5
owner: hub
last_reconciled: 2026-10-13
---

# Vybe daily worker

Standing order under `VYBE-AGENT-STANDARDS.md`. Never end the run waiting (rule 13): a blocked step is reported with its exact error and the rest still ships.

Three deliverables every weekday, then merge your own PR so the work goes live the same day: (1) a new React Native screen, (2) at least 3 new verified funding opportunities, (3) one new application packet on the Apply page.

Composio only, Vybe Health only (rules 1, 2, 4): this run normally touches no account; reading public grant pages is allowed. Before committing, grep the diff for the two strings rule 4 names.

Branch fresh from main: claude/vybe-daily-<date>. Never stack on yesterday's branch.

1. Screen rotation (check vybe-app/src/screens/ first, never repeat): Mon dimension detail (Restore → Move → Nourish → Connect → Vitals), Tue Ask, Wed onboarding or first run, Thu history or trend, Fri settings and permissions or the outcome review. Plain JavaScript, React Native core only, theme tokens from vybe-app/src/theme.js, sample data in a named module with an on-screen note, accessibility props, no identical card rows, no Inter or Fraunces. RestoreScreen.js and MoveTrendScreen.js are the house references.
2. Funding, health-wearable money first: wearable and digital-health prizes and no-fee pitch competitions; DoD SBIR/STTR topics on wearables, sleep, physiological monitoring, human performance; veteran-, woman- and minority-owned programmes. Rows go in funding-scraper/sources.toml under [[sources.curated.entry]] with a real verified date, big_name and big_name_why (rule 12). Read funding.json and CANDIDATES.md first; record dead or ineligible leads in CANDIDATES.md. Never an expired, fee-charging, clinical-trial, single-disease, medical-device or R01-type row. Read the programme's own page.
3. One application packet in funding-scraper/applications/packets.py for the best undrafted opportunity, answering the questions the form actually asks, with every hard gate mapped to GATES, founders' facts as {{KEY}} placeholders, no invented names, dates, revenue, headcount, users, partners or budgets; Vybe contact details only. Then build.py and republish the Apply artifact in place (https://claude.ai/artifact/ATFLtCRwNNuuvUT2qqYSR5).
4. Before pushing: scripts/check-divisions.sh, sources.toml parses, the dry-run sweep. Push, open a ready PR, wait for green checks, merge with merge_method "merge", then dispatch funding-sweep.yml on main.
5. Rule 5: after the sweep, fetch the live funding.json and compare `generated` with main; if they differ, report "committed, not live: <error>" rather than "live".

Report in at most eight lines: the screen, the application and its deadline, the PR number and merge SHA, the funding rows with sources, any gate that blocks a big award, and the live-versus-main check. Never email anyone and never submit an application.
