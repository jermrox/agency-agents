#!/usr/bin/env bash
#
# Enforce VYBE-AGENT-STANDARDS.md on everything scoped to Vybe Health.
#
# Why this exists: the founder's other company's Calendly link was hardcoded in
# two Vybe files read by different code paths, so correcting one and not the
# other left it in half the drafted emails. It reached about fifty partner
# organisations before anyone noticed, and no instruction to an agent could
# remove it, because it was compiled into the text. A grep in CI can.
#
# What it checks:
#   1. No account belonging to another venture appears in a Vybe-scoped path.
#   2. The one Calendly URL allowed in Vybe outreach is the Vybe Health one.
#   3. Each Vybe agent spec points at the standards document.
#
# Deliberately NOT checked: marketing/marketing-{consultant,university,
# business}-outreach-strategist.md. Those are the other company's own agents
# selling its own product, so its domain belongs in them. The rule is that
# nothing of that company touches Vybe, not that the string leaves the repo.
set -uo pipefail

STANDARDS="VYBE-AGENT-STANDARDS.md"
VYBE_CALENDLY="https://calendly.com/jeremy-vybe/30min"

# Paths that belong to Vybe Health. Anything here is held to the standard.
VYBE_PATHS=(
  vybe-app
  vybe-marketing
  growth-scout
  funding-scraper
  dashboards
  marketing/marketing-vybe-growth-scout.md
  marketing/marketing-vybe-health-marketing-director.md
  marketing/marketing-vybe-reels-strategist.md
)

# Accounts belonging to the founder's other ventures. Assembled from pieces so
# this script is not itself a copyable source of the wrong strings.
FOREIGN=(
  "jeremylahn""-i-grow"
  "i""-grow.co"
  "lscops"".com"
  "debouillet"".com"
)

fail=0
note() { printf '  %s\n' "$1"; }

echo "Checking $STANDARDS across $(echo "${VYBE_PATHS[@]}" | wc -w) Vybe paths…"

# --- 1. no foreign account in a Vybe path -----------------------------------
for needle in "${FOREIGN[@]}"; do
  hits=$(grep -rIl --fixed-strings "$needle" "${VYBE_PATHS[@]}" 2>/dev/null || true)
  if [ -n "$hits" ]; then
    echo "FAIL: a non-Vybe account appears in Vybe-scoped files:"
    while IFS= read -r f; do note "$f  contains  $needle"; done <<<"$hits"
    note "Rule 2 of $STANDARDS: nothing of another venture appears in Vybe work."
    fail=1
  fi
done

# --- 2. the only booking link in Vybe outreach is the Vybe one --------------
links=$(grep -rIoh "https://calendly\.com/[A-Za-z0-9/_-]*" "${VYBE_PATHS[@]}" 2>/dev/null | sort -u || true)
while IFS= read -r link; do
  [ -z "$link" ] && continue
  if [ "$link" != "$VYBE_CALENDLY" ]; then
    echo "FAIL: non-Vybe booking link in a Vybe path: $link"
    note "Only $VYBE_CALENDLY is allowed. Rule 2 of $STANDARDS."
    grep -rIln --fixed-strings "$link" "${VYBE_PATHS[@]}" 2>/dev/null | while IFS= read -r f; do note "  in $f"; done
    fail=1
  fi
done <<<"$links"

# --- 3. every Vybe agent spec points at the standard ------------------------
# An agent whose spec does not name the standard is an agent that will not read
# it, which is how the rule got applied to Gmail and missed Calendly.
for spec in marketing/marketing-vybe-*.md; do
  [ -e "$spec" ] || continue
  if ! grep -q "$STANDARDS" "$spec"; then
    echo "FAIL: $spec does not reference $STANDARDS"
    note "Add a line linking it, so the agent loads the standard with its own spec."
    fail=1
  fi
done

if [ "$fail" -eq 0 ]; then
  n=$(ls marketing/marketing-vybe-*.md 2>/dev/null | wc -l | tr -d ' ')
  echo "PASSED: no non-Vybe account in any Vybe path; every booking link is the Vybe Calendly; $n Vybe agent specs reference the standard."
fi
exit "$fail"
