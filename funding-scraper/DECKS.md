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
