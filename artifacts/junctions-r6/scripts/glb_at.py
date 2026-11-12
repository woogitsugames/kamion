"""glb_at.py E N R [node-substr]: primitives of the exported world chunks (High GLB) with vertices within R of (E, N):
node, material, vertex count near, z range. Minimal GLB reader (JSON + BIN, float32 POSITION). ADR 0110 debugging."""
import json, struct, sys, glob
import numpy as np
E, N, R = float(sys.argv[1]), float(sys.argv[2]), float(sys.argv[3])
sub = sys.argv[4] if len(sys.argv) > 4 else ""
man = json.load(open("Data/Regions/bialystok-industrial-c/generated/world_manifest.json", encoding="utf-8"))
axes = None
for f in sorted(glob.glob("Data/raw/derived/bialystok-industrial-c/world/chunk_*_*.glb")):
    if f.endswith(".low.glb"):
        continue
    b = open(f, "rb").read()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl])
    bin0 = 20 + jl + 8
    ex = js.get("extras", {}) or js.get("asset", {}).get("extras", {})
    for node in js["nodes"]:
        if "mesh" not in node or sub not in node.get("name", ""):
            continue
        tr = np.array(node.get("translation", [0, 0, 0]), float)
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            acc = js["accessors"][prim["attributes"]["POSITION"]]
            bv = js["bufferViews"][acc["bufferView"]]
            off = bin0 + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            st = bv.get("byteStride", 12)
            raw = np.frombuffer(b, np.float32, count=acc["count"] * 3, offset=off).reshape(-1, 3) if st == 12 else None
            if raw is None:
                continue
            P = raw + tr
            # glTF axes of the exporter (terrain_mesh.gltf.GLTF_AXES): (x, y, z) = (-E, U, N)
            e, n, z = -P[:, 0], P[:, 2], P[:, 1]
            m = np.hypot(e - E, n - N) < R
            if m.any():
                mat = js["materials"][prim["material"]]["name"] if "material" in prim else "?"
                print(f"{f[-18:]} {node['name']:14s} {mat:22s} n={int(m.sum()):5d} z {z[m].min():.2f}..{z[m].max():.2f}  E {e[m].min():.1f}..{e[m].max():.1f} N {n[m].min():.1f}..{n[m].max():.1f}")
