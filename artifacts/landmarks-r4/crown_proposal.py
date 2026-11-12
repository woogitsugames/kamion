"""Small, read-only geometry experiment. No Blender, export, world build or production edit."""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np

root = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
landmark = root / "art-source/world/landmarks/fire_station_jrg2"
source = (out / "baseline-generated/make_fire_station.py").read_text(encoding="utf-8")
tree = ast.parse(source)
names = {"h01", "conifer_core_uv", "build_conifer"}
functions = "\n\n".join(ast.get_source_segment(source, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names)
assert all(f"def {name}(" in functions for name in names)
dims = json.loads((out / "baseline-generated/dims.json").read_text(encoding="utf-8"))
layout = json.loads((landmark / "atlas_layout.json").read_text(encoding="utf-8"))

class Collector:
    def __init__(self):
        self.faces = []

    def face(self, vertices, uv, material, *args, **kwargs):
        self.faces.append((np.asarray(vertices), material))

    def summary(self):
        alpha_area = 0.0
        triangles = 0
        for vertices, material in self.faces:
            triangles += len(vertices) - 2
            if material == "alpha":
                alpha_area += sum(np.linalg.norm(np.cross(vertices[i] - vertices[0], vertices[i + 1] - vertices[0])) / 2
                                  for i in range(1, len(vertices) - 1))
        vertices = np.concatenate([v for v, _ in self.faces])
        return dict(tris=triangles, alpha_cards=sum(m == "alpha" for _, m in self.faces),
                    alpha_surface_m2=float(alpha_area), bbox_min=vertices.min(0).tolist(), bbox_max=vertices.max(0).tolist())

candidate = functions.replace('count = 6 if lod == 0 else', 'count = D["spruce"]["high_bough_counts_WORKING_VALUE"][j] if lod == 0 else')
candidate = candidate.replace('roll = .50*(h01(key,j,i,"roll")-.5)', 'roll = .45+.35*(h01(key,j,i,"roll")-.5)')
candidate = candidate.replace('UP*math.cos(roll)+np.r_[-direction[1],direction[0],0]*math.sin(roll)',
                              'UP*math.sin(roll)+np.r_[-direction[1],direction[0],0]*math.cos(roll)')
candidate = candidate.replace('min(length*.65,height*f*.90)', 'min(length*(.24 if lod == 0 else .16),height*f*.90)')
assert candidate != functions and candidate.count('min(length*(.24') == 1
proposed = copy.deepcopy(dims)
proposed["spruce"].update(inner_core_fill_r_WORKING_VALUE=.55,
    core_profile_WORKING_VALUE=[[.045,.50],[.27,1.0],[.60,.58],[.975,.025]],
    low_bough_counts=[5,4,4,4,4,3,3,3,2], high_bough_counts_WORKING_VALUE=[12,11,10,10,10,9,9,8,7])
rows = []
for phase, code, config in (("baseline", functions, dims), ("proposal", candidate, proposed)):
    namespace = dict(np=np, math=math, hashlib=hashlib, D=config, LAY=layout["atlas"], ALAY=layout["alpha"],
                     UP=np.array([0.,0.,1.]), MAT="opaque", ALPHA="alpha")
    exec(code, namespace)
    for index, (_, _, height, radius) in enumerate(dims["spruce"]["items"]):
        for lod in (0, 1):
            mesh = Collector()
            spec = json.loads((out / "baseline-generated/fire_station_jrg2.spec.json").read_text(encoding="utf-8"))
            key = spec["ground"]["spruce"][index][-1]
            namespace["build_conifer"](mesh, np.zeros(3), height, radius, key, lod)
            rows.append(dict(phase=phase, tree=index, lod=lod, **mesh.summary()))
for row in rows:
    if row["phase"] != "proposal":
        continue
    old = next(r for r in rows if r["phase"] == "baseline" and r["tree"] == row["tree"] and r["lod"] == row["lod"])
    assert row["tris"] == old["tris"]
    row["alpha_area_ratio"] = row["alpha_surface_m2"] / old["alpha_surface_m2"]
    print(row["tree"], row["lod"], row["tris"], row["alpha_area_ratio"])
(out / "crown-proposal-metrics.json").write_text(json.dumps(dict(
    status="Geometry-only proposal, not a rendered result or GPU cost measurement", rows=rows), indent=2), encoding="utf-8")
(out / "crown-proposal-config.json").write_text(json.dumps(proposed["spruce"], indent=2), encoding="utf-8")
print(json.dumps([r for r in rows if r["phase"] == "proposal"], indent=2))
assert all(r.get("alpha_area_ratio", 0) <= 1.0 for r in rows)

