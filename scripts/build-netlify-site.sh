#!/usr/bin/env bash
#
# Assemble the static site Netlify publishes for the "agentresearchsum" project.
#
# Netlify is connected to THIS repository, which is an agent library, not a web
# root: there is no index.html at the top level. Without this script Netlify
# publishes the bare repo, so "/" is a 404 and the board is only reachable at
# /healthcare/dashboards/h2f-scout-board.html — which is why the site looked
# empty. This copies the board into a clean publish directory and wraps the
# standalone copy in a small Tailwind-styled shell.
#
# Two deliberate constraints:
#
#   1. The board itself stays dependency-free. It has to drop into Squarespace
#      as an embed and inherit that page's typeface, so it ships its own CSS and
#      loads nothing. /h2f-scout-board.html is that untouched embed copy.
#   2. Tailwind is additive, never load-bearing. It styles the standalone site
#      chrome only. If the compile fails we fall back to the Tailwind CDN; if
#      that is blocked too the chrome degrades to plain readable markup and the
#      board underneath is unaffected. A Tailwind problem must never fail a deploy.
set -euo pipefail

SRC_BOARD="healthcare/dashboards/h2f-scout-board.html"
SHELL_HEAD="scripts/netlify/shell-head.html"
SHELL_FOOT="scripts/netlify/shell-foot.html"
TW_SRC="scripts/netlify/tailwind.css"
TW_VERSION="4.1.14"
OUT="${1:-site}"

rm -rf "$OUT"
mkdir -p "$OUT"

if [ ! -f "$SRC_BOARD" ]; then
  echo "error: $SRC_BOARD is missing; nothing to publish." >&2
  exit 1
fi

# The embeddable board, byte-for-byte. Squarespace pulls this one.
cp -f "$SRC_BOARD" "$OUT/h2f-scout-board.html"

# ---------------------------------------------------------------- Tailwind ---
# Compile against the shell fragments so only the utilities they use ship.
TW_MODE="none"
TW_DIR="scripts/netlify"
if [ -f "$TW_SRC" ] && command -v npm >/dev/null 2>&1; then
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
else
  echo "npm or $TW_SRC unavailable; using the Tailwind CDN."
  TW_MODE="cdn"
fi

case "$TW_MODE" in
  compiled) TW_TAG='<link rel="stylesheet" href="/tailwind.css">' ;;
  cdn)      TW_TAG='<script src="https://cdn.tailwindcss.com?plugins="></script>' ;;
  *)        TW_TAG='' ;;
esac

# ------------------------------------------------------------------- index ---
# index.html = shell chrome + the board, in one document (no iframe, so the
# board keeps its own scroll, its own focus order, and its deep links).
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

# ----------------------------------------------------------------- headers ---
# The board is meant to be embedded in the Squarespace site, so framing stays
# allowed on purpose — do not add X-Frame-Options here. Any JSON the research
# sweep publishes later needs to be readable cross-origin, same as the jobs feed.
cat > "$OUT/_headers" <<'HEADERS'
/*
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
/*.json
  Access-Control-Allow-Origin: *
  Cache-Control: public, max-age=300
/tailwind.css
  Cache-Control: public, max-age=31536000, immutable
HEADERS

echo "Tailwind: $TW_MODE"
echo "Published $(find "$OUT" -type f | wc -l | tr -d ' ') files to $OUT/:"
find "$OUT" -type f | sort | sed 's/^/  /'
