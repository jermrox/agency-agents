#!/usr/bin/env python3
"""Collapse an ArtifactData dump of the Vybe Health dashboard into one JSON file.

The live dashboard lives on claude.ai and keeps its history in the artifact's
database. Netlify can't reach that database, so the daily data pull dumps the
collections below with ArtifactData (out_dir=<dump>) and this script folds the
dump into dashboards/vybe-social/data.json, which build.py then bakes into the page.

Only public-safe fields are kept for `people`: who we followed and whether they
followed back, never the private notes.

usage: snapshot.py <dump dir> [out json]
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

PEOPLE_FIELDS = ("name", "handle", "url", "category", "tier", "followers",
                 "segments", "addedOn", "followedAt", "followedBack", "followedBackAt")
INSIGHT_FIELDS = ("profileViews", "views", "reach", "websiteTaps",
                  "accountsEngaged", "interactions")
POST_FIELDS = ("permalink", "timestamp", "type", "product", "caption", "likes",
               "comments", "views", "reach", "saved", "shares")


def load(dump, collection):
    out = {}
    for path in sorted(glob.glob(os.path.join(dump, collection, "*.json"))):
        with open(path) as f:
            out[os.path.splitext(os.path.basename(path))[0]] = json.load(f)
    return out


def pick(d, fields):
    return {k: d[k] for k in fields if k in d and d[k] is not None}


def main():
    dump = sys.argv[1]
    dest = sys.argv[2] if len(sys.argv) > 2 else "dashboards/vybe-social/data.json"

    followers = [dict(date=k, **pick(v, ("ig", "igFollowing", "igPosts", "fb")))
                 for k, v in load(dump, "followers").items()]
    insights = [dict(date=k, **pick(v, INSIGHT_FIELDS))
                for k, v in load(dump, "igdaily").items()]
    posts = [dict(id=k, **pick(v, POST_FIELDS)) for k, v in load(dump, "igposts").items()]
    posts.sort(key=lambda p: p.get("timestamp", ""), reverse=True)
    people = [pick(v, PEOPLE_FIELDS) for v in load(dump, "people").values()]
    people.sort(key=lambda p: p.get("handle", "").lower())

    targets = {}
    tpath = os.path.join(dump, "plan", "targets.json")
    if os.path.exists(tpath):
        with open(tpath) as f:
            t = json.load(f)
        targets = pick(t, ("followerTarget", "start", "end", "label"))

    snap = {
        "generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source": "Instagram Graph API via Composio, logged daily to the Vybe dashboard",
        "targets": targets,
        "followers": sorted(followers, key=lambda r: r["date"]),
        "insights": sorted(insights, key=lambda r: r["date"]),
        "posts": posts,
        "people": people,
    }
    with open(dest, "w") as f:
        json.dump(snap, f, indent=1, ensure_ascii=False)
        f.write("\n")
    print(f"wrote {dest}: {len(followers)} follower days, {len(insights)} insight days, "
          f"{len(posts)} posts, {len(people)} people")


if __name__ == "__main__":
    main()
