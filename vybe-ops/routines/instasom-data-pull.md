---
agent: Instasom
session: session_01NdJPDj7shKEpQA4scTx2Bh
triggers: trig_01WyHWCsvCn4PYS57tJciseL  # replaces trig_018GS6gCGFFrK8w9krA4oniv (disabled 15 Oct)
cron: CRON_TZ=America/New_York 38 6 * * *
owner: hub
last_reconciled: 2026-10-15
---

# Instasom daily Instagram data pull

Standing order under rule 13 and rule 15 of `VYBE-AGENT-STANDARDS.md`. Do
only this, quietly, then end the turn with one line of numbers. The founder's
dashboard is https://instasum.netlify.app; never send the founder a claude.ai
link. Where a line below disagrees with the standards, the standards win and
the hub fixes the line the same day.

## Rules in force

- Composio only, Vybe Health accounts only (rules 1, 2, 4). Never a connector attached to the session. Never echo any page access token.
- Never end a run waiting (rule 13). The Netlify deploy comes BEFORE the store write (changed 15 Oct): on 12, 13, 14 and 15 Oct an unanswered ArtifactData permission prompt stopped the run before anything reached the live page. The live page and the closing line must never depend on that prompt.
- Never invent a number; use only values the API returned.

## Steps

1. Through Composio (session "very"; load COMPOSIO_MULTI_EXECUTE_TOOL with ToolSearch), in one multi-execute call: INSTAGRAM_GET_USER_INFO (me; followers_count, follows_count, media_count); INSTAGRAM_GET_IG_USER_MEDIA (me, limit 100, fields id,caption,media_type,media_product_type,permalink,timestamp,like_count,comments_count); INSTAGRAM_GET_USER_INSIGHTS reach time_series for the last three days (since and until as Unix integers); INSTAGRAM_GET_USER_INSIGHTS total_value (profile_views, accounts_engaged, total_interactions, views, website_clicks) for yesterday only; INSTAGRAM_GET_IG_MEDIA_INSIGHTS (views, reach, saved, shares, likes, comments) for every post from the last 30 days; FACEBOOK_GET_PAGE_DETAILS with connected account facebook_claque-banal and page_id "1235241226349802" (fields followers_count, fan_count, name; do not rely on FACEBOOK_LIST_MANAGED_PAGES). Once trusted followers reach 100, also request follower_count time_series and audience demographics (follower_demographics and engaged_audience_demographics, period lifetime, timeframe this_month, metric_type total_value, one call per breakdown: age, gender, country, city; empty breakdowns mean skip). If a tik_hub connection is active, also call TIK_HUB_INSTAGRAM_V2_FETCH_USER_FOLLOWING and TIK_HUB_INSTAGRAM_V2_FETCH_USER_FOLLOWERS for vybehealthinc (page through all results) to set followedAt and followedBack on matching people docs.
2. Build the day's docs in memory: followers/<today> {ig, igFollowing, igPosts, fb, fbFans, fbPageId "1235241226349802", source, loggedAt}; igdaily/<yesterday> {profileViews, accountsEngaged, interactions, views, websiteTaps, reach, source, pulledOn} (reach end_time date minus one day is the day it belongs to; backfill reach into the two days before when missing); igposts/<media id> per post {permalink, timestamp, type, product, caption (first 80 characters), likes, comments, views, reach, saved, shares, pulledOn}; igaudience/<today> only when demographics came back non-empty. If Facebook failed, keep the Instagram numbers and say "fb: failed" in the closing line.
3. Netlify redeploy, every run (founder, 7 Oct: "everything needs to be in that netlify link"; no permission needed). Patch = {collection: {doc_id: fields}} of the step-2 docs (for people docs drop audience, auditSource, auditReason, backing, segments, verification, sizeBand, postCount, verifiedFollowers, lane, wears, role, previousCategory, auditCaution). Save it in the scratchpad, encode with `xz -9 -c | base64 -w0` and note its md5. In COMPOSIO_REMOTE_WORKBENCH (session "very") paste it (split across two cells if over about 12K characters), check the md5, decode, load the live https://instasum.netlify.app/all.json, set each collection's doc to the patch fields, set generatedAt to now UTC, write /home/user/vs/all.json, and fetch index.html and netlify.toml from https://raw.githubusercontent.com/jermrox/agency-agents/claude/new-agent-isolated-env-sfcqsc/dashboards/vybe-social/ into /home/user/vs. Get a fresh command from NETLIFY_MCP_NETLIFY_DEPLOY_SERVICES_UPDATER (deploy-site, siteId 9cafd9ea-c78c-46ff-a225-76dc839864c7) and confirm the response names instasum before deploying. In COMPOSIO_REMOTE_BASH_TOOL: `rm -rf /tmp/vsd && mkdir /tmp/vsd && cp /home/user/vs/* /tmp/vsd/ && cd /tmp/vsd && <command>` (running it inside /home/user/vs fails with EACCES). Confirm https://instasum.netlify.app/all.json shows the new generatedAt. Never commit all.json or push anything from this routine.
4. Write the same docs to the ArtifactData store at https://claude.ai/artifact/21PLwmyjPGyBtWffSzsUUY in one batch (read existing docs first and pin if_version on any that exist; if a pinned write is refused with "no approval record", write the new unpinned docs first and retry the pinned ones). Never delete old docs.
5. Sync edits made on https://instasum.netlify.app: NETLIFY_MCP_NETLIFY_PROJECT_SERVICES_UPDATER manage-form-submissions get-submissions (siteId 9cafd9ea-c78c-46ff-a225-76dc839864c7, form "vybe-edits", page until empty) to <scratchpad>/sync/subs.json; if none, skip. Otherwise ArtifactData list (limit 1000) every collection the submissions touch into <scratchpad>/sync/dump, write <scratchpad>/sync/versions.json, run `python3 scripts/vybe-social/sync_edits.py <scratchpad>/sync/subs.json <scratchpad>/sync/dump <scratchpad>/sync/out <scratchpad>/sync/versions.json`, send out/writes.json as one ArtifactData batch plus sync/latest from out/sync.json, re-read and rerun on a version mismatch, never force a held edit, then delete each submission id in out/applied.txt. Redeploy once more as in step 3 if any edit was applied.

## Report

One line: Instagram, Facebook and reach numbers; "netlify: deployed <generatedAt>" or the exact error; "store: written" or "store: waiting on ArtifactData permission"; "edits: <applied> applied, <held> held". If Composio fails, say so in one line and write nothing.
