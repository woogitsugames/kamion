"""steel_plot.py E0 E1 N0 N1 out.png [mats]: plan (colour = z) and elevation (E vs z) of barrier / kerb / paving vertices in the exported High chunks."""
import json, struct, sys, glob
import numpy as np
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
E0, E1, N0, N1 = (float(v) for v in sys.argv[1:5])
mats = sys.argv[6].split(",") if len(sys.argv) > 6 else ["barrier_steel", "curb_concrete", "bridge_kerb", "bridge_concrete", "sidewalk_paving", "road_asphalt"]
fig, ax = plt.subplots(2, 1, figsize=(16, 12))
mk = {"barrier_steel": "o", "curb_concrete": "s", "bridge_kerb": "s", "bridge_concrete": "^", "sidewalk_paving": "x", "road_asphalt": "."}
for f in sorted(glob.glob("Data/raw/derived/bialystok-industrial-c/world/chunk_*_*.glb")):
    if f.endswith(".low.glb"):
        continue
    b = open(f, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl]); bin0 = 20 + jl + 8
    for node in js["nodes"]:
        if "mesh" not in node or node["name"].startswith("terrain") or node["name"] == "collision":
            continue
        tr = np.array(node.get("translation", [0, 0, 0]), float)
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            mat = js["materials"][prim["material"]]["name"] if "material" in prim else "?"
            if mat not in mats:
                continue
            acc = js["accessors"][prim["attributes"]["POSITION"]]
            bv = js["bufferViews"][acc["bufferView"]]
            P = np.frombuffer(b, np.float32, count=acc["count"] * 3, offset=bin0 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)).reshape(-1, 3) + tr
            e, n, z = -P[:, 0], P[:, 2], P[:, 1]
            m = (e > E0) & (e < E1) & (n > N0) & (n < N1)
            if not m.any():
                continue
            steel = mat == "barrier_steel"
            sc = ax[0].scatter(e[m], n[m], s=14 if steel else 5, c=z[m], cmap="jet", vmin=139.0, vmax=142.5, marker=mk.get(mat, "."),
                               edgecolors=("k" if node["name"] == "furniture" else "none") if steel else "none", linewidths=0.4)
            ax[1].scatter(e[m], z[m], s=10 if steel else 4, c={"barrier_steel": "red" if node["name"] == "furniture" else "blue", "road_asphalt": "0.6",
                          "sidewalk_paving": "orange", "bridge_concrete": "green"}.get(mat, "0.3"), marker=mk.get(mat, "."))
plt.colorbar(sc, ax=ax[0])
ax[0].set_xlim(E0, E1); ax[0].set_ylim(N0, N1); ax[0].grid(True); ax[0].set_aspect("equal")
ax[1].set_xlim(E0, E1); ax[1].set_ylim(138.5, 144); ax[1].grid(True)
fig.savefig(sys.argv[5], dpi=70, bbox_inches="tight")
