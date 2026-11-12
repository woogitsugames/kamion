"""rail_far.py [thr_m]: ground W-beam runs (streetscape_qa.json furniture.guardrail_runs) with points further than thr (default 3.0 m)
from the nearest carriageway / paved surface of the exported High chunks (sampled triangle points). ADR 0144 check for
"a rail wandering off into the grass" (REVIEW s14-0123 P2-8)."""
import json, struct, sys, glob
import numpy as np
from scipy.spatial import cKDTree
thr = float(sys.argv[1]) if len(sys.argv) > 1 else 3.0
MATS = ("road_asphalt", "road_asphalt_new", "apron_sett", "sidewalk_paving", "curb_concrete", "island_gravel", "bridge_concrete", "bridge_kerb")
pts = []
for f in sorted(glob.glob("Data/raw/derived/bialystok-industrial-c/world/chunk_*_*.glb")):
    if f.endswith(".low.glb"):
        continue
    b = open(f, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl]); bin0 = 20 + jl + 8
    for node in js["nodes"]:
        if "mesh" not in node or node["name"] not in ("road", "paved", "bridge"):
            continue
        tr = np.array(node.get("translation", [0, 0, 0]), float)
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            mat = js["materials"][prim["material"]]["name"] if "material" in prim else "?"
            if not mat.startswith(MATS):
                continue
            acc = js["accessors"][prim["attributes"]["POSITION"]]
            bv = js["bufferViews"][acc["bufferView"]]
            P = np.frombuffer(b, np.float32, count=acc["count"] * 3, offset=bin0 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)).reshape(-1, 3) + tr
            ia = js["accessors"][prim["indices"]]; ib = js["bufferViews"][ia["bufferView"]]
            dt = {5123: np.uint16, 5125: np.uint32}[ia["componentType"]]
            I = np.frombuffer(b, dt, count=ia["count"], offset=bin0 + ib.get("byteOffset", 0) + ia.get("byteOffset", 0)).reshape(-1, 3)
            A = np.column_stack([-P[:, 0], P[:, 2]])[I]
            for w in ((1, 0, 0), (0, 1, 0), (0, 0, 1), (1 / 3, 1 / 3, 1 / 3), (.5, .5, 0), (0, .5, .5), (.5, 0, .5)):
                pts.append(A[:, 0] * w[0] + A[:, 1] * w[1] + A[:, 2] * w[2])
tree = cKDTree(np.concatenate(pts))
runs = json.load(open("Data/Regions/bialystok-industrial-c/generated/streetscape_qa.json", encoding="utf-8"))["furniture"]["guardrail_runs"]
worst = []
for r in runs:
    A = np.asarray(r["pts"], float)
    d, _ = tree.query(A[:, :2])
    worst.append((float(d.max()), r["key"], A[int(d.argmax())][:2].tolist(), int((d > thr).sum()), len(A)))
worst.sort(reverse=True)
print(f"runs {len(runs)}, with a point > {thr} m from a road / paved surface: {sum(1 for w in worst if w[0] > thr)}")
for w in worst[:12]:
    print(f"  max {w[0]:5.2f} m  {w[1]:58s} at {w[2]}  pts>{thr}: {w[3]}/{w[4]}")
