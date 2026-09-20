# Candidate queue — NOT on the board

Every row here is a lead, not an opportunity. Nothing moves from this file to
`sources.toml` until `probe-candidates.yml` has read the programme's own page
from a runner and confirmed three things: it is still running, its deadline,
and its eligibility gate. That rule is why the live board carries no expired
entries, and it is not relaxed for a large number.

The sandbox cannot reach these hosts (egress allowlist returns `000` /
`EGRESS_BLOCKED`), so the amounts and dates below come from search-result text
and are **unverified**. Treat every figure as a claim to check.

Eligibility confirmed by Jeremy 2026-09-20: Vybe Health qualifies as
**veteran-owned, woman-owned and minority-owned (51%+)**. That opens a
category the board had barely searched — it held 11 restricted rows out of 107.

## Priority 1 — larger than anything currently on the board

| Candidate | Claimed award | Gate | What to confirm |
|---|---|---|---|
| Google for Startups **Black Founders Fund** (US) | **$150,000 equity-free** + up to $100,000 Google Cloud credits | Black founder | Whether the US round is open as of Sep 2026; the reported opening was March 2026 |
| Google for Startups **Latino Founders Fund** (US) | **$150,000 equity-free** | Latino founder | Same — round status and next deadline |

If either is open these are the largest non-dilutive awards found for this
company so far, and both explicitly favour AI-powered startups.

## Priority 2 — women-founder

| Candidate | Claimed award | Gate | What to confirm |
|---|---|---|---|
| Fearless Fund | $20,000 | Black women founders | "Next cycle forthcoming" — is there a live cycle? |
| SoGal Black Founder Startup Grant | $5,000–$10,000, rolling | Black women / nonbinary | Rolling really means open; no revenue floor claimed |
| iFundWomen grant marketplace | varies by sponsor | women-owned | Which sponsor grants are live now |

## Priority 3 — veteran

| Candidate | Claimed award | Gate | What to confirm |
|---|---|---|---|
| StreetShares Foundation Veteran Award | $5,000–$15,000 | veteran-owned | Sources disagree on the cycle (Feb vs Oct) — resolve before adding |
| IVMF Military Founders Lab / CEOcircle (absorbed Bunker Labs) | programme, funding unclear | veteran / military spouse | Whether it carries cash or is training-only. Training-only still gets a row, labelled as such |

## Priority 4 — minority / general

| Candidate | Claimed award | Gate | What to confirm |
|---|---|---|---|
| Transform microgrant | microgrant + year-long programme | marginalised founders | Amount and cycle |
| MBDA Business Center network | advisory, some capital access | minority-owned | Whether any centre runs a direct grant |

## Explicitly rejected, do not re-add

- **Secretsos Small Business Grant** — charges an application fee. Already on
  the board; flag it so the fee is visible before anyone applies.
- **Outta Excuses** — application fee.
- Any programme requiring a clinical trial (see the blocklist in
  `sources.toml`): Vybe has no trial arm, no IRB, no clinical infrastructure.
