#!/usr/bin/env python3
"""Build the Netlify copy of the Vybe Health dashboard.

The dashboard lives on claude.ai (dashboards/vybe-social/source.html is its
page) and keeps its data in the artifact database. Netlify can't reach that
database, so the daily data pull dumps every collection with ArtifactData
(out_dir=<dump>) and this script:

  1. folds the dump into dashboards/vybe-social/all.json, and
  2. writes dashboards/vybe-social/index.html: the same page, unchanged, with a
     small stand-in for window.claude placed ahead of its script, so every
     section renders from all.json. Edits made on Netlify (ticks, statuses,
     comments, logged Insights) are kept in the browser and posted to the
     Netlify form "vybe-edits"; sync_edits.py writes them into the claude.ai
     database at the daily pull, holding any edit whose field changed on
     claude.ai first.

usage: snapshot.py <dump dir>
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dashboards", "vybe-social")
COLLECTIONS = ("research", "people", "plan", "weeks", "daily", "followers",
               "igaudience", "igdaily", "igposts", "reports", "insights", "igexport", "sync")

FORM = """<form name="vybe-edits" data-netlify="true" netlify-honeypot="bot-field" hidden>
<input type="hidden" name="form-name" value="vybe-edits">
<input name="bot-field"><input name="op"><input name="coll"><input name="id"><input name="at"><input name="page">
<textarea name="patch"></textarea><textarea name="base"></textarea>
</form>
"""

SHIM = """<script>
/* Stand-in for the claude.ai runtime on Netlify. Reads from all.json; every edit is
   kept on this device and sent to Netlify Forms, and the daily pull writes it into the
   claude.ai dashboard unless the same field changed there first (then it is held and
   listed here as a conflict). */
(function () {
  var KEY = "vybe-edits";
  var cols = {}, generatedAt = "", sync = null;
  var colSubs = {}, docSubs = {};
  function clone(v) { return v == null ? undefined : JSON.parse(JSON.stringify(v)); }
  function snap(id, v) { return { id: id, exists: v != null, data: function () { return clone(v); } }; }
  function pending() { try { return JSON.parse(localStorage.getItem(KEY) || "[]"); } catch (e) { return []; } }
  function remember(e) { try { var l = pending(); l.push(e); localStorage.setItem(KEY, JSON.stringify(l.slice(-500))); } catch (x) {} }
  function applyLocal(e) {
    var c = cols[e.coll] || (cols[e.coll] = {});
    if (e.op === "delete") { delete c[e.id]; return; }
    if (e.op === "set") { c[e.id] = clone(e.patch); return; }
    var cur = c[e.id] || {}; var k; for (k in e.patch) { if (e.patch[k] === null) delete cur[k]; else cur[k] = clone(e.patch[k]); } c[e.id] = cur;
  }
  function notify(coll, id) {
    (colSubs[coll] || []).forEach(function (cb) { var c = cols[coll] || {}; cb({ docs: Object.keys(c).sort().map(function (k) { return snap(k, c[k]); }) }); });
    ((docSubs[coll] || {})[id] || []).forEach(function (cb) { cb(snap(id, (cols[coll] || {})[id])); });
  }
  function send(e) {
    var body = new URLSearchParams();
    body.set("form-name", "vybe-edits"); body.set("op", e.op); body.set("coll", e.coll); body.set("id", e.id);
    body.set("at", e.at); body.set("page", e.page); body.set("patch", JSON.stringify(e.patch == null ? null : e.patch)); body.set("base", JSON.stringify(e.base == null ? null : e.base));
    return fetch("/", { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body.toString() })
      .then(function (r) { if (!r.ok) throw new Error("save failed " + r.status); });
  }
  function edit(op, coll, id, patch) {
    var prev = (cols[coll] || {})[id];
    var base = null;
    if (op === "update" && prev) { base = {}; Object.keys(patch).forEach(function (k) { base[k] = prev[k] === undefined ? null : clone(prev[k]); }); }
    else if (prev) { base = clone(prev); }
    var e = { op: op, coll: coll, id: id, patch: patch == null ? null : clone(patch), base: base, at: new Date().toISOString(), page: generatedAt };
    applyLocal(e); remember(e); notify(coll, id); banner();
    return send(e);
  }
  function docRef(coll, id) {
    return {
      onSnapshot: function (cb) { ((docSubs[coll] = docSubs[coll] || {})[id] = (docSubs[coll][id] || [])).push(cb); ready.then(function () { cb(snap(id, (cols[coll] || {})[id])); }); return function () {}; },
      set: function (d) { return edit("set", coll, id, d); },
      update: function (d) { return edit("update", coll, id, d); },
      delete: function () { return edit("delete", coll, id, null); }
    };
  }
  var db = {
    collection: function (name) {
      return {
        onSnapshot: function (cb) { (colSubs[name] = colSubs[name] || []).push(cb); ready.then(function () { var c = cols[name] || {}; cb({ docs: Object.keys(c).sort().map(function (k) { return snap(k, c[k]); }) }); }); return function () {}; },
        doc: function (id) { return docRef(name, id); }
      };
    },
    doc: function (path) { var p = path.split("/"); return docRef(p[0], p[1]); }
  };
  function banner() {
    var el = document.getElementById("dbBanner"); if (!el) return;
    var local = pending().filter(function (e) { return e.at > generatedAt; }).length;
    var txt = "Live copy. Data as of " + new Date(generatedAt).toLocaleString([], { dateStyle: "medium", timeStyle: "short" }) + ". Edits save here and are written into the claude.ai dashboard at the next pull (6:38 ET).";
    if (local) txt += " " + local + " edit" + (local > 1 ? "s" : "") + " from this device waiting to sync.";
    if (sync && sync.conflicts && sync.conflicts.length) txt += " Held (changed on claude.ai first): " + sync.conflicts.map(function (c) { return c.coll + "/" + c.id + " " + (c.fields || []).join(", "); }).join("; ") + ".";
    el.hidden = false; el.textContent = txt;
  }
  var ready = fetch("all.json", { cache: "no-store" }).then(function (r) { return r.json(); }).then(function (d) {
    cols = d.collections || {}; generatedAt = d.generatedAt || "";
    sync = (cols.sync || {}).latest || null;
    var keep = pending().filter(function (e) { return e.at > generatedAt; });
    try { localStorage.setItem(KEY, JSON.stringify(keep)); } catch (x) {}
    keep.forEach(applyLocal);
    banner();
  });
  window.claude = {
    use: function (name) {
      if (name === "db") return ready.then(function () { return db; });
      if (name === "user") return Promise.resolve({ canEdit: function () { return Promise.resolve(true); } });
      return Promise.resolve(null);
    }
  };
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
    page = page[:i] + FORM + SHIM + page[i:]
    # claude.ai wraps artifact pages in a document skeleton; Netlify needs its own.
    page = ('<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            '<meta name="robots" content="noindex">\n</head>\n<body>\n' + page + '\n</body>\n</html>\n')
    with open(os.path.join(HERE, "index.html"), "w") as f:
        f.write(page)
    print("wrote all.json (" + ", ".join(f"{k} {len(v)}" for k, v in cols.items()) + ") and index.html")


if __name__ == "__main__":
    main()
