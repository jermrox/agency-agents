"""Render packets.py into index.html, the Apply page. python3 build.py"""
import json, pathlib, datetime
import packets as P

here = pathlib.Path(__file__).parent
data = {
    "facts": [{"key": k, "label": l, "hint": h} for k, l, h in P.FACTS],
    "gates": [{"key": k, "label": l} for k, l in P.GATES],
    "packets": P.PACKETS,
    "shared": [{"q": q, "a": a} for q, a in P.SHARED],
    "built": datetime.date.today().isoformat(),
}
blob = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
html = (here / "template.html").read_text().replace("/*DATA*/", blob)
(here / "index.html").write_text(html)
print(f"index.html: {len(P.PACKETS)} packets, {sum(len(p['fields']) for p in P.PACKETS)} answers")
