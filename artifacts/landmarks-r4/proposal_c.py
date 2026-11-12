"""Geometry-only alternate idea while B queues; never edits production inputs."""
import ast
import copy
import hashlib
import json
import math
from pathlib import Path

import numpy as np

out = Path(__file__).resolve().parent
root = out.parents[1]
base = out / "baseline-generated"
source = (base / "make_fire_station.py").read_text(encoding="utf-8")
tree = ast.parse(source)
names = {"h01", "conifer_core_uv", "build_conifer"}
functions = "\n\n".join(ast.get_source_segment(source, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in names)
candidate = functions.replace('count = 6 if lod == 0 else', 'count = D["spruce"]["high_bough_counts_WORKING_VALUE"][j] if lod == 0 else')
candidate = candidate.replace('min(length*.65,height*f*.90)', 'min(length*(.27 if lod == 0 else .18),height*f*.90)')
assert candidate != functions
collector_tree = ast.parse((out / "crown_proposal.py").read_text(encoding="utf-8-sig"))
collector_tree.body = [n for n in collector_tree.body if isinstance(n, ast.ClassDef) and n.name == "Collector"]
ns_collector = {"np": np}; exec(compile(collector_tree, "collector_only", "exec"), ns_collector)
Collector = ns_collector["Collector"]
layout = json.loads((root / "art-source/world/landmarks/fire_station_jrg2/atlas_layout.json").read_text(encoding="utf-8"))
dims = json.loads((base / "dims.json").read_text(encoding="utf-8"))
spec = json.loads((base / "fire_station_jrg2.spec.json").read_text(encoding="utf-8"))
proposed = copy.deepcopy(dims)
proposed["spruce"].update(inner_core_fill_r_WORKING_VALUE=.60,
    core_profile_WORKING_VALUE=[[.045,.5],[.25,1.0],[.5,.65],[.75,.3],[.975,.025]],
    low_bough_counts=[4,4,3,3,3,3,3,2,2], high_bough_counts_WORKING_VALUE=[10,10,10,9,9,8,8,7,7])
rows = []
for phase, code, config in (("baseline", functions, dims), ("proposalC", candidate, proposed)):
    ns = dict(np=np, math=math, hashlib=hashlib, D=config, LAY=layout["atlas"], ALAY=layout["alpha"],
              UP=np.array([0.,0.,1.]), MAT="opaque", ALPHA="alpha")
    exec(code, ns)
    for index, (_,_,_,height,radius,key) in enumerate(spec["ground"]["spruce"]):
        for lod in (0,1):
            mesh=Collector();ns["build_conifer"](mesh,np.zeros(3),height,radius,key,lod)
            rows.append(dict(phase=phase,tree=index,lod=lod,**mesh.summary()))
for row in rows:
    if row["phase"] != "proposalC": continue
    old=next(r for r in rows if r["phase"]=="baseline" and r["tree"]==row["tree"] and r["lod"]==row["lod"])
    assert old["tris"]==row["tris"]==(224 if row["lod"]==0 else 98)
    row["alpha_area_ratio"]=row["alpha_surface_m2"]/old["alpha_surface_m2"]
    assert row["alpha_area_ratio"] <= 1.0
result=dict(status="Unrendered alternate C; production B untouched; no GIS or GPU claim", rows=rows,
            low_core_normal_corners_three_trees=3*5*4*4, original_minimum=216)
assert result["low_core_normal_corners_three_trees"] >= result["original_minimum"]
(out / "proposal-c-metrics.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps([r for r in rows if r["phase"]=="proposalC"],indent=2))
