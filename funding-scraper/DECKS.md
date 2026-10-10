# Weekly deck + report ledger

The Monday routine (`Vybe Health — weekly deck + report`, 13:00 UTC Mondays) writes one
line here every week, and reads this file first so it never builds for the
same target twice running. If this file says a target was covered in the last
6 weeks, pick a different one.

## Rotation rule

1. Prefer a **live opportunity** from `output/funding.json` closing within 8
   weeks that Vybe can actually win — check it against the structural
   disqualifiers before committing (no clinical-trial requirement, no
   single-disease programme, no medical-device or diagnostic posture, no
   institutional-only mechanism, no application fee).
2. If nothing qualifies, build an **audience deck**, rotating in this order:
   pre-seed investor → strategic/OEM partner → enterprise or team buyer →
   retail/DTC buyer → research partner.

## Built

| Week of | Target | Why | Artifact |
|---|---|---|---|
| 2026-09-21 | Google for Startups Founders Fund (Black / Latino, US) | $150k equity-free + up to $100k cloud credits, explicitly favours AI-powered startups, and Jeremy qualifies on founder eligibility. Largest non-dilutive item identified so far. | https://claude.ai/artifact/QnBLB3mCG4QLS1Az8ra15a |
| 2026-09-22 | Strategic / OEM partner (audience deck, rotation step 2) | No live board opportunity cleared the structural disqualifiers inside the 8-week window, so the rotation moved to its second audience. Leads on the licensing wedge: partners can buy the interpretation layer instead of building one. | https://claude.ai/artifact/VzwoWJjUU9rBRj2x7Hy6rY |
| 2026-09-28 | **Veteran Shark Tank 2026** (live opportunity, rotation rule 1) | $50,000 non-dilutive, closing 13 Oct — 15 days out — and the one live item on the board whose age test runs in Vybe's favour: the business must be UNDER three years old on 7 Dec. Clears every structural disqualifier: no clinical trial, no single disease, no device or diagnostic posture, not institutional, no fee. The competition requires a deck of no more than 10 slides covering six named sections in order, so this deck is built to that brief rather than to the audience rotation, which stays at enterprise / team buyer for next week. | https://claude.ai/artifact/7WVaCL6sb8JkNE2JS4ceBK |
| 2026-10-05 | **Enterprise / team buyer** (audience deck, rotation step 3) | Rule 1 produced no new target this week, so the rotation advanced to the audience the 28 Sep run deferred. Nothing live inside the 8-week window warranted a deck: Veteran Shark Tank was decked on 28 Sep; **Army xTech|Search 10** is the largest live item on the board at up to $1M non-dilutive, clears every structural disqualifier and states 'no fee, and no equity' on its own page — but its 19 Oct deliverable is a concept white paper, not a deck, and a drafted packet already exists for it; the pitch stage it would serve is 18–29 Jan 2027 and only if the white paper gets through. Everything else closing inside 30 days is a sub-$30k contest whose own brief is a 3-minute pitch or a 99-second video, or fails a gate — Cornell CAT needs a Cornell faculty PI, NYSTAR is NY-only, Xcelerate shortlists only startups holding a paid WHX Tech Startup Pod, and Pave HER Way awards an individual for a project with 'clear public benefit for women and girls', which Vybe is not. The deck leads on the wedge no consumer deck can use: an employer cannot change anybody's HRV, but it sets the roster, and Connect is the only dimension that reads it. Rotation moves to **retail / DTC buyer** next. | https://claude.ai/artifact/1eZcunEHkH8FaxEevvUUBR |

## Considered and rejected — do not re-propose without new information

| Target | Why not |
|---|---|
| MedTech Innovator Vantage (BARDA diagnostics + medical devices hub) | Scope is diagnostic and patient-monitoring **platforms** and **medical devices that enhance clinical decision-making**. Vybe is explicitly neither — no diagnostic claim, no device classification. Same structural mismatch the board's blocklist exists to catch. On the board at $50k–$200k closing 15 Oct 2026, which makes it look like the best live fit; it is not. |
| Fund Her Future | Closed 22 Sep 2026 and required $20,000 of 2025 revenue. |

## Schedule reliability

| Date | What happened |
|---|---|
| 2026-09-22 | The 13:00 UTC Monday slot did **not** fire on its own — the routine had no run history at all, so no weekly deck or report had ever been delivered. The week's run was fired by hand as a catch-up. Watch the next scheduled slot (2026-09-28) and fix the trigger if it skips again rather than hand-firing it each week. |
| 2026-09-22 | The catch-up run published both artifacts but **pushed no commits**, so this ledger row was written separately. If a future run's artifacts exist but the ledger is unchanged, the run ended before its commit step. |
| 2026-09-28 | The 13:00 UTC Monday slot **fired on its own** — scheduled 13:02, delivered 13:25 — so this is the first unattended weekly run. The daily routine fired the same morning at 12:28. No hand-firing needed; the trigger is healthy. |
| 2026-10-05 | The 13:00 UTC Monday slot fired on its own for the second week running — scheduled 13:08, delivered 13:23. Trigger is healthy; no hand-firing. |
| 2026-10-05 | **The server-side brand-asset copy was refused by the permission classifier** (Data Exfiltration) when copying the master deck's logo and Vybe Intelligence artwork into the new deck, so this week's deck is typographic — the five dimensions are drawn with painted rules in their own hues rather than placed as artwork. The one product photograph in the master's asset store still carries the unapproved "Powered by NVIDIA" badge and was unusable regardless. Until the copy is permitted, every weekly deck will be image-free. |
