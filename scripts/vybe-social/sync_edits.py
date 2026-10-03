#!/usr/bin/env python3
"""Turn Netlify form submissions from the Vybe dashboard copy into ArtifactData writes.

The Netlify copy of the dashboard posts every edit to the form "vybe-edits"
(fields: op, coll, id, at, page, patch, base). The daily pull fetches those
submissions with the Netlify MCP (manage-form-submissions / get-submissions),
saves them as JSON, dumps the current claude.ai collections with ArtifactData
(out_dir=<dump>) and runs:

    sync_edits.py <submissions.json> <dump dir> <out dir> [versions.json]

It writes to <out dir>:
  writes.json    batch entries for ArtifactData (op, collection, doc_id, data,
                 and if_version when versions.json maps "<coll>/<id>" to one)
  sync.json      the sync/latest document: applied, held conflicts, run time
  applied.txt    submission ids that were applied or held (delete them after
                 the batch succeeds)

Lock rule: an "update" is held when any field it touches changed on claude.ai
since the edit was made (current value != the base the page recorded and !=
the new value). A "set" or "delete" is held when the document changed at all.
Edits to the same document are applied in time order and merged into one write.
"""
import glob
import json
import os
import sys
from datetime import datetime, timezone


def load_submissions(path):
    with open(path) as f:
        raw = json.load(f)
    if isinstance(raw, dict):
        raw = raw.get("data", raw.get("submissions", []))
    if isinstance(raw, str):
        raw = json.loads(raw)
    out = []
    for s in raw:
        d = s.get("data", s) if isinstance(s, dict) else {}
        try:
            e = {
                "sid": s.get("id") or s.get("submission_id") or "",
                "op": d.get("op"), "coll": d.get("coll"), "id": d.get("id"),
                "at": d.get("at") or s.get("created_at") or "",
                "page": d.get("page") or "",
                "patch": json.loads(d.get("patch") or "null"),
                "base": json.loads(d.get("base") or "null"),
            }
        except (ValueError, AttributeError):
            continue
        if e["op"] in ("set", "update", "delete") and e["coll"] and e["id"]:
            out.append(e)
    out.sort(key=lambda e: e["at"])
    return out


def load_dump(dump):
    cols = {}
    for path in glob.glob(os.path.join(dump, "*", "*.json")):
        coll = os.path.basename(os.path.dirname(path))
        with open(path) as f:
            cols.setdefault(coll, {})[os.path.splitext(os.path.basename(path))[0]] = json.load(f)
    return cols


def main():
    subs, dump, out = sys.argv[1], sys.argv[2], sys.argv[3]
    versions = {}
    if len(sys.argv) > 4:
        with open(sys.argv[4]) as f:
            versions = json.load(f)
    os.makedirs(out, exist_ok=True)
    edits = load_submissions(subs)
    cols = load_dump(dump)
    docs = {}      # key -> working copy (None = deleted)
    ops = {}       # key -> "set" | "update" | "delete"
    held = []
    touched = []
    for e in edits:
        key = f"{e['coll']}/{e['id']}"
        touched.append(e["sid"])
        current = docs[key] if key in docs else cols.get(e["coll"], {}).get(e["id"])
        if e["op"] == "update":
            patch = e["patch"] or {}
            base = e["base"] or {}
            changed = [k for k in patch if current is not None and base.get(k) != current.get(k) and current.get(k) != patch.get(k)]
            if changed:
                held.append({"coll": e["coll"], "id": e["id"], "at": e["at"], "fields": changed, "wanted": {k: patch[k] for k in changed}})
                continue
            cur = dict(current or {})
            for k, v in patch.items():
                if v is None:
                    cur.pop(k, None)
                else:
                    cur[k] = v
            docs[key] = cur
            ops[key] = "set" if ops.get(key) == "set" or current is None else "update"
        elif e["op"] == "set":
            if current is not None and e["base"] is not None and e["base"] != current:
                held.append({"coll": e["coll"], "id": e["id"], "at": e["at"], "fields": ["*"], "wanted": e["patch"]})
                continue
            docs[key] = dict(e["patch"] or {})
            ops[key] = "set"
        else:  # delete
            if current is not None and e["base"] is not None and e["base"] != current:
                held.append({"coll": e["coll"], "id": e["id"], "at": e["at"], "fields": ["*"], "wanted": None})
                continue
            docs[key] = None
            ops[key] = "delete"
    writes = []
    for key, op in ops.items():
        coll, doc_id = key.split("/", 1)
        exists = doc_id in cols.get(coll, {})
        w = {"op": op, "collection": coll, "doc_id": doc_id}
        if op != "delete":
            if op == "update":
                # send only fields that differ from the dump, so the merge stays small
                before = cols.get(coll, {}).get(doc_id, {})
                w["data"] = {k: v for k, v in docs[key].items() if before.get(k) != v}
                removed = [k for k in before if k not in docs[key]]
                for k in removed:
                    w["data"][k] = {"__delete__": True}
                if not w["data"]:
                    continue
            else:
                w["data"] = docs[key]
        if exists:
            v = versions.get(key)
            if v:
                w["if_version"] = v
        elif op == "delete":
            continue
        writes.append(w)
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    sync = {"ranAt": now, "submissions": len(edits), "applied": len(writes), "held": len(held), "conflicts": held[-20:]}
    with open(os.path.join(out, "writes.json"), "w") as f:
        json.dump(writes, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, "sync.json"), "w") as f:
        json.dump(sync, f, ensure_ascii=False, indent=1)
    with open(os.path.join(out, "applied.txt"), "w") as f:
        f.write("\n".join(s for s in touched if s) + ("\n" if touched else ""))
    need = [w["collection"] + "/" + w["doc_id"] for w in writes if w["doc_id"] in cols.get(w["collection"], {}) and "if_version" not in w]
    print(f"{len(edits)} submissions -> {len(writes)} writes, {len(held)} held")
    if need:
        print("needs versions (read each with ArtifactData get, then rerun with versions.json):", ", ".join(need))


if __name__ == "__main__":
    main()
