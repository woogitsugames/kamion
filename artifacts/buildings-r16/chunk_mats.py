"""Per-chunk material lists and triangle counts of the generated GLBs (draw-call accounting: one material = one
submesh = one draw per chunk and LOD).   python chunk_mats.py <world dir> <out.json>"""
import json, struct, sys
from pathlib import Path

def read(p):
    b = p.read_bytes()
    n = struct.unpack_from("<I", b, 12)[0]
    j = json.loads(b[20:20 + n])
    out = {}
    for m in j.get("meshes", []):
        for pr in m["primitives"]:
            mat = j["materials"][pr["material"]]["name"] if "material" in pr else "?"
            tris = j["accessors"][pr["indices"]]["count"] // 3 if "indices" in pr else 0
            k = f'{m.get("name", "?")}|{mat}'
            out[k] = out.get(k, 0) + tris
    return out

d = Path(sys.argv[1])
res = {p.name: read(p) for p in sorted(d.glob("chunk_*.glb"))}
Path(sys.argv[2]).write_text(json.dumps(res, indent=0))
tot = {}
for f, o in res.items():
    lod = "low" if f.endswith(".low.glb") else "high"
    t = tot.setdefault(lod, [0, 0])
    t[0] += len(o); t[1] += sum(o.values())
print({k: {"submeshes": v[0], "tris": v[1]} for k, v in tot.items()})
