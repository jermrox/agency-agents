#!/usr/bin/env bash
#
# Assemble the static site Netlify publishes for the "agentresearchsum" project.
#
# Netlify is connected to THIS repository, which is an agent library, not a web
# root: there is no index.html at the top level. Without this script Netlify
# publishes the bare repo, so "/" is a 404 and the board is only reachable at
# /healthcare/dashboards/h2f-scout-board.html — which is why the site looked
# empty. This copies the boards into a clean publish directory instead.
#
# Deliberately dependency-free: no package.json, no node_modules, just cp. It
# runs identically here and in Netlify's build image.
set -euo pipefail

SRC_BOARD="healthcare/dashboards/h2f-scout-board.html"
OUT="${1:-site}"

rm -rf "$OUT"
mkdir -p "$OUT"

if [ ! -f "$SRC_BOARD" ]; then
  echo "error: $SRC_BOARD is missing; nothing to publish." >&2
  exit 1
fi

# The site is named for the research summary, so the research board is the root.
cp -f "$SRC_BOARD" "$OUT/index.html"
# Keep the named path too, so existing links and bookmarks survive.
cp -f "$SRC_BOARD" "$OUT/h2f-scout-board.html"

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
HEADERS

echo "Published $(find "$OUT" -type f | wc -l | tr -d ' ') files to $OUT/:"
find "$OUT" -type f | sort | sed 's/^/  /'
