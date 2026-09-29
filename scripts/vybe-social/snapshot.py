#!/usr/bin/env python3
"""Build the Netlify copy of the Vybe Health dashboard.

The dashboard lives on claude.ai (dashboards/vybe-social/source.html is its
page) and keeps its data in the artifact database. Netlify can't reach that
database, so the daily data pull dumps every collection with ArtifactData
(out_dir=<dump>) and this script:

  1. folds the dump into dashboards/vybe-social/all.json, and
  2. writes dashboards/vybe-social/index.html: the same page, unchanged, with a
     small read-only stand-in for window.claude placed ahead of its script, so
     every section renders from all.json. Edit controls stay hidden because the
     stand-in reports that the viewer can't edit, and the live Instagram bar
     falls back to the saved history.

usage: snapshot.py <dump dir>
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dashboards", "vybe-social")
COLLECTIONS = ("research", "people", "plan", "weeks", "daily", "followers",
               "igaudience", "igdaily", "igposts", "reports", "insights")

SHIM = """<script>
/* Read-only stand-in for the claude.ai runtime. Serves the page from all.json. */
(function () {
  var data = fetch("all.json", { cache: "no-store" }).then(function (r) { return r.json(); });
  function snap(id, v) { return { id: id, exists: v != null, data: function () { return v == null ? undefined : JSON.parse(JSON.stringify(v)); } }; }
  function ro() { return Promise.reject(new Error("This copy is read-only. Edit on claude.ai.")); }
  function docRef(coll, id) {
    return {
      onSnapshot: function (cb) { data.then(function (d) { var c = d.collections[coll] || {}; cb(snap(id, c[id])); }); return function () {}; },
      set: ro, update: ro, delete: ro
    };
  }
  var db = {
    collection: function (name) {
      return {
        onSnapshot: function (cb) {
          data.then(function (d) {
            var c = d.collections[name] || {};
            cb({ docs: Object.keys(c).sort().map(function (k) { return snap(k, c[k]); }) });
          });
          return function () {};
        },
        doc: function (id) { return docRef(name, id); }
      };
    },
    doc: function (path) { var p = path.split("/"); return docRef(p[0], p[1]); }
  };
  window.claude = {
    use: function (name) {
      if (name === "db") return data.then(function () { return db; });
      if (name === "user") return Promise.resolve({ canEdit: function () { return Promise.resolve(false); } });
      return Promise.resolve(null);
    }
  };
  data.then(function (d) {
    var el = document.getElementById("dbBanner");
    if (el) { el.hidden = false; el.textContent = "Read-only copy. Data as of " + new Date(d.generatedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) + ", refreshed every morning from Instagram. Edit and tick follows on claude.ai."; }
  });
})();
</script>
"""


def main():
    dump = sys.argv[1]
    cols = {}
    for name in COLLECTIONS:
        docs = {}
        for path in sorted(glob.glob(os.path.join(dump, name, "*.json"))):
            with open(path) as f:
                docs[os.path.splitext(os.path.basename(path))[0]] = json.load(f)
        cols[name] = docs
    out = {"generatedAt": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "collections": cols}
    with open(os.path.join(HERE, "all.json"), "w") as f:
        json.dump(out, f, ensure_ascii=False, separators=(",", ":"))

    with open(os.path.join(HERE, "source.html")) as f:
        page = f.read()
    marker = "<script"
    i = page.index(marker)
    page = page[:i] + SHIM + page[i:]
    # claude.ai wraps artifact pages in a document skeleton; Netlify needs its own.
    page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="noindex">\n</head>\n<body>\n' + page + '\n</body>\n</html>\n')
    with open(os.path.join(HERE, "index.html"), "w") as f:
        f.write(page)
    print("wrote all.json (" + ", ".join(f"{k} {len(v)}" for k, v in cols.items()) + ") and index.html")


if __name__ == "__main__":
    main()
