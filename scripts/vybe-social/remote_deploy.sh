#!/usr/bin/env bash
# Runs in the Composio remote sandbox, which can reach Netlify.
#
# Collections live in /mnt/files/vybe-social/parts/<name>.json (persistent; the
# daily pull uploads only the ones that changed). This pulls the page from
# GitHub, assembles all.json, and leaves a ready-to-deploy folder in
# /home/user/vs. The caller then runs the npx deploy command that
# NETLIFY_MCP_NETLIFY_DEPLOY_SERVICES_UPDATER (deploy-site) returns, inside it.
#
# usage: remote_deploy.sh [git ref, default main]
set -euo pipefail
REF="${1:-main}"
STORE=/mnt/files/vybe-social/parts
WORK=/home/user/vs
RAW="https://raw.githubusercontent.com/jermrox/agency-agents/$REF/dashboards/vybe-social"
rm -rf "$WORK" && mkdir -p "$WORK"
curl -fsSL "$RAW/index.html" -o "$WORK/index.html"
curl -fsSL "$RAW/netlify.toml" -o "$WORK/netlify.toml"
python3 - "$STORE" "$WORK/all.json" <<'PY'
import glob, json, os, sys
from datetime import datetime, timezone
store, dest = sys.argv[1], sys.argv[2]
cols = {}
for p in sorted(glob.glob(os.path.join(store, "*.json"))):
    with open(p) as f:
        cols[os.path.splitext(os.path.basename(p))[0]] = json.load(f)
out = {"generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "collections": cols}
with open(dest, "w") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
print("assembled", {k: len(v) for k, v in cols.items()})
PY
ls -la "$WORK"
