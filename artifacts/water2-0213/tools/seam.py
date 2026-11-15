"""ADR 0213: water / terrain continuity on the dk65-02 (W edge) | dk65-03 (E edge) seam, from the exported GLBs.
uv run --project tools/worldgen python artifacts/water2-0213/tools/seam.py [n_min n_max]
Per tile: water-sheet vertices on the seam line (|e - seam| < 0.05 m) and terrain_lod0 vertices there; prints the
water level / extent on both sides and the max terrain height difference at equal n."""
import json
import struct
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
N0, N1 = (float(sys.argv[1]), float(sys.argv[2])) if len(sys.argv) > 2 else (-600.0, 0.0)
SEAM_X = 768779.0


def glb_nodes(p):
    b = p.read_bytes()
    jl = struct.unpack_from("<I", b, 12)[0]
    js = json.loads(b[20:20 + jl])
    bin_ = b[20 + jl + 8:]
    out = {}
    for nd in js["nodes"]:
        if "mesh" not in nd:
            continue
        m = js["meshes"][nd["mesh"]]
        P = []
        for pr in m["primitives"]:
            a = js["accessors"][pr["attributes"]["POSITION"]]
            bv = js["bufferViews"][a["bufferView"]]
            off = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
            P.append(np.frombuffer(bin_, np.float32, a["count"] * 3, off).reshape(-1, 3))
        out[nd.get("name", m.get("name"))] = (np.concatenate(P), nd.get("translation", [0, 0, 0]))
    return out


def tile(reg):
    ry = (ROOT / "Data/Regions" / reg / "region.yaml").read_text(encoding="utf-8")
    import yaml
    y = yaml.safe_load(ry)
    ox, oy, oz = y["origin"]["x"], y["origin"]["y"], y["origin"].get("z", 0.0)
    W, T = [], []
    for g in sorted((ROOT / "Data/raw/derived" / reg / "world").glob("chunk_*_*.glb")):
        if g.name.endswith(".low.glb"):
            continue
        nodes = glb_nodes(g)
        for name, acc in (("water", W), ("terrain_lod0", T)):
            if name in nodes:
                P, t = nodes[name]
                P = P + np.asarray(t, np.float32)
                # glTF axes (terrain_mesh.gltf GLTF_AXES): x = -E, y = up, z = N
                acc.append(np.column_stack([-P[:, 0] + ox, P[:, 2] + oy, P[:, 1]]))
    return (np.concatenate(W) if W else np.zeros((0, 3))), np.concatenate(T)


for reg in ("dk65-02", "dk65-03"):
    W, T = tile(reg)
    on = lambda A: A[(np.abs(A[:, 0] - SEAM_X) < 0.05) & (A[:, 1] - 598271 > N0) & (A[:, 1] - 598271 < N1)]
    w, t = on(W), on(T)
    globals()[reg.replace("-", "_")] = (w, t)
    if len(w):
        print(f"{reg}: water on seam n {w[:, 1].min() - 598271:.1f}..{w[:, 1].max() - 598271:.1f} local, "
              f"z {w[:, 2].min():.3f}..{w[:, 2].max():.3f} ({len(w)} verts); terrain verts {len(t)}")
    else:
        print(f"{reg}: no water vertex on the seam; terrain verts {len(t)}, z range of all water {W[:, 2].min() if len(W) else 0:.2f}")
(wa, ta), (wb, tb) = dk65_02, dk65_03
if len(ta) and len(tb):
    da = {round(n, 2): z for _, n, z in ta}
    diffs = [(n, z - da[round(n, 2)]) for _, n, z in tb if round(n, 2) in da]
    if diffs:
        d = np.array(diffs)
        k = np.argmax(np.abs(d[:, 1]))
        print(f"terrain seam: {len(d)} shared verts, max |dz| {abs(d[k, 1]):.3f} m at n {d[k, 0] - 598271:.1f}")
if "--profile" in sys.argv:
    for n in np.arange(-345, -290, 1.0):
        za = ta[np.abs(ta[:, 1] - 598271 - n) < 0.01][:, 2]
        zb = tb[np.abs(tb[:, 1] - 598271 - n) < 0.01][:, 2]
        print(f"n {n:6.1f}  02 {za[0] if len(za) else float('nan'):8.3f}  03 {zb[0] if len(zb) else float('nan'):8.3f}")
