"""cols_check.py: every column of the hero viaduct spec -> distance to the nearest ground asphalt / apron triangle of the exported High
chunks (0 = stands on a carriageway) and to the nearest kerb vertex. ADR 0144."""
import json, struct, glob
import numpy as np
from shapely.geometry import Polygon, Point
from shapely.ops import unary_union
spec = json.load(open("Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_biezenstwa.spec.json"))
cols = [(dk["chain"][-22:], pr["s"], q) for dk in spec["decks"] for pr in dk["piers"] for q in pr["cols"]]
C = np.array([q[:2] for _, _, q in cols])
lo, hi = C.min(0) - 8, C.max(0) + 8
tris = []
for f in sorted(glob.glob("Data/raw/derived/bialystok-industrial-c/world/chunk_*_*.glb")):
    if f.endswith(".low.glb"):
        continue
    b = open(f, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl]); bin0 = 20 + jl + 8
    for node in js["nodes"]:
        if "mesh" not in node or node["name"] != "road":
            continue
        tr = np.array(node.get("translation", [0, 0, 0]), float)
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            mat = js["materials"][prim["material"]]["name"] if "material" in prim else "?"
            if not (mat.startswith("road_asphalt") or mat == "apron_sett"):
                continue
            acc = js["accessors"][prim["attributes"]["POSITION"]]
            bv = js["bufferViews"][acc["bufferView"]]
            P = np.frombuffer(b, np.float32, count=acc["count"] * 3, offset=bin0 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)).reshape(-1, 3) + tr
            ia = js["accessors"][prim["indices"]]; ib = js["bufferViews"][ia["bufferView"]]
            dt = {5123: np.uint16, 5125: np.uint32}[ia["componentType"]]
            I = np.frombuffer(b, dt, count=ia["count"], offset=bin0 + ib.get("byteOffset", 0) + ia.get("byteOffset", 0)).reshape(-1, 3)
            A = np.column_stack([-P[:, 0], P[:, 2]])[I]
            Z = P[:, 1][I].mean(1)
            c = A.mean(1)
            m = (c[:, 0] > lo[0]) & (c[:, 0] < hi[0]) & (c[:, 1] > lo[1]) & (c[:, 1] < hi[1]) & (Z < 142.5)   # ground level only
            tris += [Polygon(t) for t in A[m]]
U = unary_union([t.buffer(0.01) for t in tris])
bad = 0
for (ch, s, q) in cols:
    d = U.distance(Point(q[0], q[1]))
    bad += d < 0.45
    print(f"{ch} s {s:7.2f} col {q[0]:7.2f} {q[1]:8.2f}  asphalt {d:5.2f} m{'  <-- ON / AT THE CARRIAGEWAY' if d < 0.45 else ''}")
print("columns", len(cols), "closer than 0.45 m to ground asphalt:", bad)
