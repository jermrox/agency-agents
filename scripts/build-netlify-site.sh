#!/usr/bin/env bash
#
# Assemble the static site Netlify publishes, per target site.
#
# Netlify is connected to THIS repository, which is an agent library, not a web
# root: there is no index.html at the top level. Without this script Netlify
# publishes the bare repo, so "/" is a 404.
#
# MORE THAN ONE SITE BUILDS FROM THIS REPO
# Several Netlify projects point at this same repository and the same
# netlify.toml. Without a target they would each publish identical content,
# which is how the funding board ended up on the health research site. So the
# build reads the target from Netlify's own SITE_NAME and publishes only what
# belongs to that site:
#
#   agentresearchsum -> the H2F tactical research board (Squarespace embed)
#   agentrevup       -> the Vybe funding tracker (growth/revenue)
#   anything else    -> everything, which is what you want locally
#
# Override with SITE_TARGET=rev when testing another site's output by hand.
#
# Two deliberate constraints, unchanged:
#
#   1. Boards stay dependency-free. They have to drop into Squarespace as an
#      embed and inherit that page's typeface, so each ships its own CSS and
#      loads nothing. The named copies are those untouched embed copies.
#   2. Tailwind is additive, never load-bearing. It styles the standalone site
#      chrome only. If the compile fails we fall back to the Tailwind CDN; if
#      that is blocked too the chrome degrades to plain readable markup and the
#      board underneath is unaffected. A Tailwind problem must never fail a deploy.
set -euo pipefail

SRC_BOARD="healthcare/dashboards/h2f-scout-board.html"
SRC_FUNDING="dashboards/vybe-funding-tracker.html"
FUNDING_FEED="funding-scraper/output/funding.json"
SHELL_HEAD="scripts/netlify/shell-head.html"
SHELL_FOOT="scripts/netlify/shell-foot.html"
TW_SRC="scripts/netlify/tailwind.css"
OUT="${1:-site}"

# --------------------------------------------------------------- targeting ---
RAW_TARGET="${SITE_TARGET:-${SITE_NAME:-all}}"
case "$RAW_TARGET" in
  agentresearchsum|research|researchsum) TARGET="research" ;;
  agentrevup|rev|revup)                  TARGET="rev" ;;
  *)                                     TARGET="all" ;;
esac
echo "Building for target: $TARGET (from '${RAW_TARGET}')"

rm -rf "$OUT"
mkdir -p "$OUT"

want_research() { [ "$TARGET" = "research" ] || [ "$TARGET" = "all" ]; }
want_rev()      { [ "$TARGET" = "rev" ]      || [ "$TARGET" = "all" ]; }

# ------------------------------------------------------------------ boards ---
if want_research; then
  if [ ! -f "$SRC_BOARD" ]; then
    echo "error: $SRC_BOARD is missing; nothing to publish for the research site." >&2
    exit 1
  fi
  # The embeddable board, byte-for-byte. Squarespace pulls this one.
  cp -f "$SRC_BOARD" "$OUT/h2f-scout-board.html"
fi

if want_rev; then
  if [ ! -f "$SRC_FUNDING" ]; then
    echo "error: $SRC_FUNDING is missing; nothing to publish for the rev site." >&2
    exit 1
  fi
  cp -f "$SRC_FUNDING" "$OUT/vybe-funding-tracker.html"

  # The funding dashboard fetches /funding.json at runtime to pick up the
  # biweekly sweep. Its absence is survivable by design -- the page falls back
  # to its built-in list -- so a missing feed must not fail the build.
  if [ -f "$FUNDING_FEED" ]; then
    cp -f "$FUNDING_FEED" "$OUT/funding.json"
  else
    echo "note: $FUNDING_FEED not present; the dashboard will use its built-in list."
  fi
fi

# Any other standalone dashboard still gets a URL on the rev site.
if want_rev && [ -d "dashboards" ]; then
  for f in dashboards/*.html; do
    [ -e "$f" ] || continue
    cp -f "$f" "$OUT/$(basename "$f")"
  done
fi

# ---------------------------------------------------------------- Tailwind ---
# Only the research site's index uses the Tailwind shell, so only build it there.
TW_MODE="none"
TW_DIR="scripts/netlify"
if want_research && [ -f "$TW_SRC" ] && command -v npm >/dev/null 2>&1; then
  echo "Installing the Tailwind toolchain…"
  # Install into scripts/netlify so that `@import "tailwindcss"` inside
  # tailwind.css resolves from the stylesheet's own directory. npx alone puts
  # the packages in a temp prefix that CSS resolution never sees.
  if npm install --prefix "$TW_DIR" --no-audit --no-fund --silent >"$OUT/.tw.log" 2>&1 \
     && "$TW_DIR/node_modules/.bin/tailwindcss" \
          --input "$TW_SRC" \
          --output "$OUT/tailwind.css" \
          --content "${SHELL_HEAD},${SHELL_FOOT}" \
          --minify >>"$OUT/.tw.log" 2>&1; then
    TW_MODE="compiled"
    echo "  → $OUT/tailwind.css ($(wc -c <"$OUT/tailwind.css" | tr -d ' ') bytes)"
  else
    echo "  ! Tailwind build failed; falling back to the CDN. Log:" >&2
    sed 's/^/    /' "$OUT/.tw.log" >&2 || true
    rm -f "$OUT/tailwind.css"
    TW_MODE="cdn"
  fi
  rm -f "$OUT/.tw.log"
elif want_research; then
  echo "npm or $TW_SRC unavailable; using the Tailwind CDN."
  TW_MODE="cdn"
fi

case "$TW_MODE" in
  compiled) TW_TAG='<link rel="stylesheet" href="/tailwind.css">' ;;
  cdn)      TW_TAG='<script src="https://cdn.tailwindcss.com?plugins="></script>' ;;
  *)        TW_TAG='' ;;
esac

# ------------------------------------------------------------------- index ---
# Each site's "/" is its own primary board. On the research site that is the
# H2F board wrapped in the Tailwind shell (no iframe, so the board keeps its own
# scroll, focus order and deep links). On the rev site it is the funding
# tracker, shipped as-is because it carries its own chrome.
if [ "$TARGET" = "rev" ]; then
  cp -f "$SRC_FUNDING" "$OUT/index.html"
else
  {
    # everything up to and including the board's <style> block
    sed -n '1,/^<\/style>$/p' "$SRC_BOARD"
    printf '%s\n' "$TW_TAG"
    cat <<'CSS'
<style>
  /* The shell sits outside the board's own .wrap gutter. */
  body { padding-top: 0; }
  .mm-shellbar { margin: 0 calc(-1 * var(--gutter)); position: relative; z-index: 6; }
  .mm-shellfoot { margin: 40px calc(-1 * var(--gutter)) -72px; }
  .controls { top: 0; }
</style>
CSS
    cat "$SHELL_HEAD"
    # the board body, with the skip-link anchor attached to the wrapper
    sed -n '/^<\/style>$/,$p' "$SRC_BOARD" | tail -n +2 \
      | sed '0,/<div class="wrap">/s//<div class="wrap" id="board">/'
    cat "$SHELL_FOOT"
  } > "$OUT/index.html"
fi

# ----------------------------------------------------------------- headers ---
# The boards are meant to be embedded in the Squarespace site, so framing stays
# allowed on purpose — do not add X-Frame-Options here. Any JSON published here
# needs to be readable cross-origin, same as the jobs feed.
cat > "$OUT/_headers" <<'HEADERS'
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
/*.json
  Access-Control-Allow-Origin: *
  Cache-Control: public, max-age=300
HEADERS

# The immutable cache rule only makes sense where the file ships. Declaring it
# on a site without Tailwind is dead config, and dead config is how a reader
# ends up believing a site serves something it does not.
if [ -f "$OUT/tailwind.css" ]; then
  cat >> "$OUT/_headers" <<'HEADERS'
/tailwind.css
  Cache-Control: public, max-age=31536000, immutable
HEADERS
fi

echo "Tailwind: $TW_MODE"
echo "Published $(find "$OUT" -type f | wc -l | tr -d ' ') files to $OUT/:"
find "$OUT" -type f | sort | sed 's/^/  /'
