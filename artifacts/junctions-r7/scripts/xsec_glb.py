"""xsec_glb.py E N dirE dirN [halfwidth=12] [slab=1.0] [zmin zmax]: cross-section of the exported High chunks at (E, N) across
the direction (dirE, dirN): per node/material the lateral offsets (left of the direction = +) and z of vertices within
`slab` m along the direction. Measures kerb face / barrier face / edge line positions in the built world (ADR 0123)."""
import json, struct, sys, glob
import numpy as np
E, N, dE, dN = (float(v) for v in sys.argv[1:5])
half = float(sys.argv[5]) if len(sys.argv) > 5 else 12.0
slab = float(sys.argv[6]) if len(sys.argv) > 6 else 1.0
zlo, zhi = (float(sys.argv[7]), float(sys.argv[8])) if len(sys.argv) > 8 else (-1e9, 1e9)
t = np.array([dE, dN]); t /= np.linalg.norm(t); nl = np.array([-t[1], t[0]])
rows = {}
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
            acc = js["accessors"][prim["attributes"]["POSITION"]]
            bv = js["bufferViews"][acc["bufferView"]]
            if bv.get("byteStride", 12) != 12:
                continue
            P = np.frombuffer(b, np.float32, count=acc["count"] * 3, offset=bin0 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)).reshape(-1, 3) + tr
            e, n, z = -P[:, 0], P[:, 2], P[:, 1]
            a = (e - E) * t[0] + (n - N) * t[1]
            l = (e - E) * nl[0] + (n - N) * nl[1]
            m = (np.abs(a) < slab) & (np.abs(l) < half) & (z > zlo) & (z < zhi)
            if m.any():
                mat = js["materials"][prim["material"]]["name"] if "material" in prim else "?"
                rows.setdefault((node["name"], mat), []).append(np.column_stack([l[m], z[m]]))
for (node, mat), v in sorted(rows.items()):
    v = np.vstack(v)
    # cluster lateral offsets to 5 cm
    key = np.round(v[:, 0] / 0.05) * 0.05
    out = []
    for k in np.unique(key):
        zz = v[key == k, 1]
        out.append(f"{k:+.2f}[{zz.min():.2f}..{zz.max():.2f}]")
    print(f"{node:10s} {mat:20s} " + " ".join(out[:60]))
