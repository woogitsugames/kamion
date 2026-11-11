"""Probe: hash the road stage (pipeline.build, pass 1) part by part. Usage: probe_roads.py <out.json>"""
import hashlib, json, sys, collections
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np
from roads import pipeline
w = pipeline.build("bialystok-industrial-c")
tot = hashlib.sha256()
by = collections.OrderedDict()
rows = []
for i, p in enumerate(w.buf.parts):
    h = hashlib.sha256()
    h.update(f"{p.layer}|{p.mat}|{p.src}".encode())
    h.update(np.ascontiguousarray(np.asarray(p.V, float)).tobytes())
    h.update(np.ascontiguousarray(np.asarray(p.T, np.int64)).tobytes())
    d = h.hexdigest()[:16]
    tot.update(d.encode())
    rows.append([i, p.layer, p.mat, p.src, len(p.V), len(p.T), d])
def clean(o):
    if isinstance(o, dict): return {str(k): clean(v) for k, v in sorted(o.items(), key=lambda kv: str(kv[0]))}
    if isinstance(o, (list, tuple)): return [clean(x) for x in o]
    if isinstance(o, np.ndarray): return o.tolist()
    if isinstance(o, (np.floating, np.integer)): return o.item()
    if isinstance(o, (set, frozenset)): return sorted(clean(x) for x in o)
    return o if isinstance(o, (int, float, str, bool, type(None))) else repr(type(o))
Path(sys.argv[1]).write_text(json.dumps({"total": tot.hexdigest(), "n": len(rows), "stats": clean(w.stats), "parts": rows}, indent=0), encoding="utf-8")
print("TOTAL", tot.hexdigest(), len(rows))
