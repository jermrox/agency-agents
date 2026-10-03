#!/usr/bin/env python3
"""Split dashboards/vybe-social/all.json into one gzip+base64 file per collection.

The daily data pull uploads these to the Composio sandbox, which is where the
Netlify deploy runs (this container can't reach Netlify). Only collections whose
md5 changed need to go up; manifest.txt lists "<collection> <md5>" so the
routine can compare with the sandbox's copy.

usage: parts.py <out dir>
"""
import base64
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "dashboards", "vybe-social")


def main():
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(HERE, "all.json")) as f:
        cols = json.load(f)["collections"]
    lines = []
    for name, docs in sorted(cols.items()):
        raw = json.dumps(docs, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
        md5 = hashlib.md5(raw).hexdigest()
        with open(os.path.join(out, name + ".b64"), "w") as f:
            f.write(base64.b64encode(gzip.compress(raw, 9, mtime=0)).decode())
        lines.append(f"{name} {md5}")
    with open(os.path.join(out, "manifest.txt"), "w") as f:
        f.write("\n".join(lines) + "\n")
    for line in lines:
        name = line.split()[0]
        print(line, os.path.getsize(os.path.join(out, name + ".b64")), "bytes")


if __name__ == "__main__":
    main()
