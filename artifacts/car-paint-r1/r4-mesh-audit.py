"""Read-only source/library audit before G R4; no product writes."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/worldgen"))
from streetscape import life_cars as LC
from streetscape.export import crease_normals

rows = []
for body, d in {**LC.CARS, "van": LC.VAN}.items():
    variants = LC.VAN_COLOURS if body == "van" else LC.CAR_COLOURS
    for colour in variants:
        meshes = LC.van(colour) if body == "van" else LC.car(body, colour)
        for lod, mesh in enumerate((meshes[0], meshes[1], meshes[3])):
            prims = [p for p in crease_normals(mesh.out()) if p["mat"].startswith("car_paint_")]
            v = np.concatenate([p["V"] for p in prims])
            uv = np.concatenate([p["UV"] for p in prims])
            n = np.concatenate([p["N"] for p in prims])
            edges = np.concatenate([np.linalg.norm(p["V"][p["T"][:, a]] - p["V"][p["T"][:, b]], axis=1)
                                    for p in prims for a,b in ((0,1),(1,2),(2,0))])
            rows.append(dict(prototype=f"car_{body}_{colour}", lod=lod, sill=d["sill"],
                axle_front=d["L"]/2-d["foh"], axle_rear=d["L"]/2-d["foh"]-d["wb"],
                tyre_radius=d["r"], arch_radius=d["r"]+.045,
                bbox_generator=[v.min(0).tolist(), v.max(0).tolist()],
                uv0_max_error_m=float(np.max(np.abs(uv-v[:,[1,2]]))),
                uv1_present=any(p.get("UV1") is not None for p in prims),
                triangles=sum(len(p["T"]) for p in prims), vertices=len(v), paint_groups=len(prims),
                maximum_triangle_edge_m=float(edges.max()),
                rear_vertices=int(np.count_nonzero(n[:,1]<-.7)),
                front_vertices=int(np.count_nonzero(n[:,1]>.7))))

p=ROOT / "art-source/world/props/street_props.glb"
b=p.read_bytes()
size,kind=struct.unpack_from("<II",b,12)
g=json.loads(b[20:20+size])
actual=[]
for node in g["nodes"]:
    name=node.get("name","")
    if not name.startswith("car_") or "mesh" not in node or name.endswith((".col",".contact")):
        continue
    for prim in g["meshes"][node["mesh"]]["primitives"]:
        mat=g["materials"][prim["material"]].get("name","")
        if mat.startswith("car_paint_"):
            actual.append(dict(node=name, material=mat, attributes=sorted(prim["attributes"])))

out=dict(source_head="bc506639", method="generated source mesh plus current main-selected GLB metadata; no Unity",
         coordinate_contract="generator right,nose,up; GLB (-x,z,y); glTFast Unity (x,z,y), subject to runtime verification",
         library_sha256=hashlib.sha256(b).hexdigest(), source_rows=rows, library_paint_primitives=actual,
         source_uv1_count=sum(x["uv1_present"] for x in rows),
         library_uv1_count=sum("TEXCOORD_1" in x["attributes"] for x in actual))
dest=ROOT/"artifacts/car-paint-r1/r4-mesh-audit.json"
dest.write_text(json.dumps(out,indent=2)+"\n",encoding="utf-8")
print(json.dumps(dict(source_lod_rows=len(rows), library_paint_primitives=len(actual),
    source_uv1_count=out["source_uv1_count"],library_uv1_count=out["library_uv1_count"],
    maximum_uv0_error=max(x["uv0_max_error_m"] for x in rows),
    max_edge=max(x["maximum_triangle_edge_m"] for x in rows))))
