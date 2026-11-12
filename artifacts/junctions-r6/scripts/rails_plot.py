"""rails_plot.py E0 E1 N0 N1 out.png: top view of barrier_steel vertices (furniture = red, bridge = blue) in the exported High chunks."""
import json, struct, sys, glob
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
E0, E1, N0, N1 = (float(v) for v in sys.argv[1:5])
fig, ax = plt.subplots(figsize=(12, 6))
for f in sorted(glob.glob("Data/raw/derived/bialystok-industrial-c/world/chunk_*_*.glb")):
    if f.endswith(".low.glb"):
        continue
    b = open(f, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl]); bin0 = 20 + jl + 8
    for node in js["nodes"]:
        if "mesh" not in node:
            continue
        tr = np.array(node.get("translation", [0, 0, 0]), float)
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            mat = js["materials"][prim["material"]]["name"] if "material" in prim else "?"
            if mat not in ("barrier_steel", "curb_concrete", "bridge_kerb"):
                continue
            acc = js["accessors"][prim["attributes"]["POSITION"]]
            bv = js["bufferViews"][acc["bufferView"]]
            if bv.get("byteStride", 12) != 12:
                continue
            P = np.frombuffer(b, np.float32, count=acc["count"] * 3, offset=bin0 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)).reshape(-1, 3) + tr
            e, n, z = -P[:, 0], P[:, 2], P[:, 1]
            m = (e > E0) & (e < E1) & (n > N0) & (n < N1)
            if m.any():
                c = {"barrier_steel": "red" if node["name"] == "furniture" else "blue"}.get(mat, "0.7")
                sc = ax.scatter(e[m], n[m], s=3, c=c, marker="o" if node["name"] == "furniture" else "x")

ax.set_xlim(E0, E1); ax.set_ylim(N0, N1); ax.grid(True)
fig.savefig(sys.argv[5], dpi=80, bbox_inches="tight")
