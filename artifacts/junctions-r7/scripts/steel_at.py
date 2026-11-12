"""steel_at.py E0 E1 N0 N1 [mat,...]: per 1 m of E: z range of the vertices of the given materials (default barrier_steel) per node, exported High chunks."""
import json, struct, sys, glob
import numpy as np
E0, E1, N0, N1 = (float(v) for v in sys.argv[1:5])
mats = sys.argv[5].split(",") if len(sys.argv) > 5 else ["barrier_steel"]
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
            mat = js["materials"][prim["material"]]["name"] if "material" in prim else "?"
            if mat not in mats:
                continue
            acc = js["accessors"][prim["attributes"]["POSITION"]]
            bv = js["bufferViews"][acc["bufferView"]]
            P = np.frombuffer(b, np.float32, count=acc["count"] * 3, offset=bin0 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)).reshape(-1, 3) + tr
            e, n, z = -P[:, 0], P[:, 2], P[:, 1]
            m = (e > E0) & (e < E1) & (n > N0) & (n < N1)
            for ee, nn, zz in zip(e[m], n[m], z[m]):
                rows.setdefault((node["name"], mat, int(np.floor(ee))), []).append((nn, zz))
for k in sorted(rows, key=lambda k: (k[2], k[0], k[1])):
    a = np.array(rows[k])
    print(f"E {k[2]:5d} {k[0]:10s} {k[1]:14s} n {len(a):4d} N {a[:,0].min():7.2f}..{a[:,0].max():7.2f} z {a[:,1].min():7.2f}..{a[:,1].max():7.2f}")
