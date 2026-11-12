"""Light analysis of six isolated crowns, not a world build or a GIS substitute."""
import ast
import hashlib
import json
import math
from pathlib import Path

import numpy as np

out = Path(__file__).resolve().parent
root = out.parents[1]
base = out / "baseline-generated"
layout = json.loads((root / "art-source/world/landmarks/fire_station_jrg2/atlas_layout.json").read_text(encoding="utf-8"))
old_dims = json.loads((base / "dims.json").read_text(encoding="utf-8"))
new_dims = json.loads((root / "art-source/world/landmarks/fire_station_jrg2/dims.json").read_text(encoding="utf-8"))
spec = json.loads((base / "fire_station_jrg2.spec.json").read_text(encoding="utf-8"))
def functions(source):
    names = {"h01", "conifer_core_uv", "build_conifer"}
    tree = ast.parse(source)
    return "\n\n".join(ast.get_source_segment(source, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names)
old_code = functions((base / "make_fire_station.py").read_text(encoding="utf-8"))
new_code = functions((root / "tools/blender/world/landmarks/make_fire_station.py").read_text(encoding="utf-8"))
class Collector:
    def __init__(self): self.faces = []
    def face(self, vertices, uv, material, *args, **kwargs):
        self.faces.append((np.asarray(vertices), np.asarray(uv), material, kwargs.get("normals")))
    def signature(self):
        return [(v.tobytes(), uv.tobytes(), m, None if nr is None else np.asarray(nr).tobytes()) for v, uv, m, nr in self.faces]
    def alpha(self): return [(v.tobytes(), uv.tobytes()) for v, uv, m, _ in self.faces if m == "alpha"]
def build(code, dims, height, radius, key, lod):
    ns = dict(np=np, math=math, hashlib=hashlib, D=dims, LAY=layout["atlas"], ALAY=layout["alpha"],
              UP=np.array([0., 0., 1.]), MAT="opaque", ALPHA="alpha")
    exec(code, ns)
    mesh = Collector(); ns["build_conifer"](mesh, np.zeros(3), height, radius, key, lod)
    return mesh
rows = []
for index, (_, _, _, height, radius, key) in enumerate(spec["ground"]["spruce"]):
    for lod in (0, 1):
        old = build(old_code, old_dims, height, radius, key, lod)
        fallback = build(new_code, old_dims, height, radius, key, lod)
        assert old.signature() == fallback.signature(), "Disabled data flag changed previous geometry"
        new = build(new_code, new_dims, height, radius, key, lod)
        assert old.alpha() == new.alpha(), "Needle cards changed"
        old_tris = sum(len(v)-2 for v, _, _, _ in old.faces)
        new_tris = sum(len(v)-2 for v, _, _, _ in new.faces)
        assert new_tris == old_tris == (224 if lod == 0 else 98)
        shared = {}; checked = 0
        for vertices, _, _, normals in new.faces:
            assert np.isfinite(vertices).all()
            if normals is None: continue
            for vertex, normal in zip(vertices, normals):
                assert np.isfinite(normal).all() and np.linalg.norm(normal) > 0
                radial = vertex.copy(); radial[2] = 0
                assert np.dot(radial, normal) > 0
                assert 0 <= vertex[2] <= height
                point = tuple(vertex)
                if point in shared: np.testing.assert_array_equal(shared[point], normal)
                shared[point] = normal; checked += 1
        rows.append(dict(tree=index, lod=lod, tris=new_tris, alpha_cards=sum(m == "alpha" for _, _, m, _ in new.faces),
                         alpha_geometry_uv_identical=True, finite_shared_outward_normal_corners=checked,
                         disabled_flag_geometry_identical=True))
(out / "crown-geometry-b.json").write_text(json.dumps(dict(complete=True, scope="Six isolated crowns only; no GLB/runtime/GIS pass claim", rows=rows), indent=2), encoding="utf-8")
print(json.dumps(rows, indent=2))
