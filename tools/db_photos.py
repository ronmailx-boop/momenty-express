#!/usr/bin/env python3
"""Rebuild the uploaded photos from the test page's database (the asset store is not always reachable from a session).

The page keeps each photo as base64 chunks in `photodata/<assetId>-<k>` and the order + taps in `session/photos`.
Save them with the ArtifactData tool (out_dir = DB_DIR): get session/photos, and list photodata (query.limit 1000), then:

  python3 db_photos.py DB_DIR OUT_DIR      # writes OUT_DIR/01.jpg ... and prints the run_set.py photo arguments (@x,y = tap)
"""
import base64, glob, json, math, os, shlex, sys


def tap(v):
    """A tap coordinate from the page's database: a number in 0..1, or the photo is stopped. The database is shared,
    so a string here could carry shell text into the run_set.py command line (security audit 20.11.2026)."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or not 0 <= v <= 1:
        sys.exit(f"bad tap coordinate in session/photos: {v!r}")
    return float(v)


db, out = sys.argv[1], sys.argv[2]
os.makedirs(out, exist_ok=True)
load = lambda p: (lambda d: d.get("data", d))(json.load(open(p)))
session = load(os.path.join(db, "session", "photos.json"))
chunks = {}
for p in glob.glob(os.path.join(db, "photodata", "*.json")):
    c = load(p)
    chunks.setdefault(c["id"], {})[c["k"]] = c
args, missing = [], []
for i, it in enumerate(session["items"], 1):
    parts = chunks.get(it["id"], {})
    n = next(iter(parts.values()))["n"] if parts else 0
    if not parts or len(parts) != n:
        missing.append(f"{i} ({len(parts)}/{n or it.get('chunks', '?')} chunks)")
        continue
    dst = os.path.join(out, f"{i:02d}.jpg")
    open(dst, "wb").write(base64.b64decode("".join(parts[k]["b64"] for k in range(n))))
    s = it.get("subject")
    args.append(dst + (f"@{tap(s.get('x'))},{tap(s.get('y'))}" if s else ""))
if missing:
    sys.exit("missing photo data for: " + ", ".join(missing))
print(" ".join(shlex.quote(a) for a in args))
