"""Probe: hash road geometry after each early stage of build_world.build. Usage: probe_stages.py <out.json>"""
import hashlib, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np
from roads import pipeline, markings as MK, decals as DC, standards as S
from terrain_mesh import conform as CF

def parts_hash(buf):
    tot = hashlib.sha256(); rows = []
    for i, p in enumerate(buf.parts):
        h = hashlib.sha256()
        h.update(f"{p.layer}|{p.mat}|{p.src}".encode())
        h.update(np.ascontiguousarray(np.asarray(p.V, float)).tobytes())
        h.update(np.ascontiguousarray(np.asarray(p.T, np.int64)).tobytes())
        d = h.hexdigest()[:16]; tot.update(d.encode())
        rows.append([i, p.layer, p.mat, p.src, len(p.V), len(p.T), d])
    return tot.hexdigest(), rows
out = {}
rid = "bialystok-industrial-c"
w0 = pipeline.build(rid)
out["pass1"] = parts_hash(w0.buf)
deck_parts = [p for p in w0.buf.parts if p.layer == "bridge" and not p.src.endswith(":parapet")]
for p in deck_parts: p.footprint = True
deck, deck_mask = CF.rasterise(deck_parts, w0.hf)
thick = S.BRIDGE_DECK_THICKNESS + S.BRIDGE_KERB_H
clean, bad = CF.clean_under_bridges(w0.hf.z, deck, deck_mask, thick)
out["clean_hf"] = (hashlib.sha256(np.ascontiguousarray(clean).tobytes()).hexdigest(), int(bad.sum()))
hf = pipeline.P.Heightfield(clean, w0.hf.bbox, (w0.hf.ox, w0.hf.oy))
w = pipeline.build(rid, hf=hf)
out["pass2"] = parts_hash(w.buf)
out["pass2_culled"] = w.stats.get("sides_on_carriageway_culled")
rep = {}
MK.build_markings(w.buf, w.net, w.junctions, w.ctx["points"], rep)
out["markings"] = parts_hash(w.buf)
DC.build(w.buf, w.net, w.junctions, rep)
out["decals"] = parts_hash(w.buf)
road_z, rmask = CF.rasterise([p for p in w.buf.parts if p.layer == "road"], w.hf)
out["road_z"] = (hashlib.sha256(np.ascontiguousarray(road_z).tobytes()).hexdigest(), int(rmask.sum()))
Path(sys.argv[1]).write_text(json.dumps(out, default=str), encoding="utf-8")
print({k: (v[0][:12] if isinstance(v, (tuple, list)) else v) for k, v in out.items()})
