"""ADR 0347: measured silhouette of the library trees (art-source/world/vegetation/trees.glb) for the road clearance.

The clearance pass (`vegetation.road_clearance`) used one nominal crown radius per species (`CROWN_FORM`, ADR 0308). The
real LOD0 meshes are 25-35 % wider (linden r/H 0.42-0.46 instead of 0.33, maple 0.46-0.50 instead of 0.375, alder 0.32-0.35
instead of 0.24, birch 0.29-0.31 instead of 0.235) and carry leaf cards from 1.3-2.6 m up: a tree that "passed" at
0.3 m over the kerb pushed foliage into the cab (critic build #8, t=2260). So the pass now reads the mesh itself:

    r_cum[proto][k] = max horizontal distance from the trunk axis of every vertex with y <= (k + 1) * STEP_M   (model m)

`low_radius(proto, scale, limit_m)` = the largest reach of the instance (scale = h / href_m, base sunk 0.15 m, like
InstanceImporter) below `limit_m` above the ground - conservative on every azimuth and rounded up to the next bin.
Generated file: tools/worldgen/streetscape/tree_crown_profile.json (`python -m streetscape.tree_crown_profile --write`,
`--check` fails when trees.glb / trees_meta.json changed and the table did not).
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[3]
GLB = REPO / "art-source" / "world" / "vegetation" / "trees.glb"
META = REPO / "art-source" / "world" / "vegetation" / "trees_meta.json"
TABLE = Path(__file__).with_name("tree_crown_profile.json")
STEP_M = 0.25               # model metres per bin (WORKING_VALUE: finer than a leaf card)
SUNK_M = 0.15               # InstanceImporter sinks the base of tree instances by this much


def _glb(path: Path):
    b = path.read_bytes()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl = struct.unpack("<I", b[off:off + 4])[0]
    return js, b[off + 8:off + 8 + bl]


def _positions(js, bin_, mesh_index):
    out = []
    for pr in js["meshes"][mesh_index]["primitives"]:
        a = js["accessors"][pr["attributes"]["POSITION"]]
        bv = js["bufferViews"][a["bufferView"]]
        o = bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        stride = bv.get("byteStride", 12)
        arr = np.frombuffer(bin_, np.uint8, count=(a["count"] - 1) * stride + 12, offset=o)
        out.append(np.stack([np.frombuffer(arr[i * stride:i * stride + 12].tobytes(), "<f4") for i in range(a["count"])]))
    return np.concatenate(out)


def build() -> dict:
    """Table from the GLB (glTF: Y up, the trunk axis is x = z = 0)."""
    js, bin_ = _glb(GLB)
    meta = json.loads(META.read_text(encoding="utf-8"))["trees"]
    protos = {}
    for node in js["nodes"]:
        name = node.get("name", "")
        if "mesh" not in node or name not in meta:
            continue
        p = _positions(js, bin_, node["mesh"])
        y = p[:, 1].astype(np.float64)
        r = np.hypot(p[:, 0], p[:, 2]).astype(np.float64)
        n = int(np.ceil(max(y.max(), STEP_M) / STEP_M)) + 1
        cum = np.zeros(n)
        bins = np.clip(np.floor(y / STEP_M).astype(int), 0, n - 1)
        np.maximum.at(cum, bins, r)
        cum = np.maximum.accumulate(cum)
        protos[name] = {"href_m": meta[name]["href_m"], "r_cum": [round(float(v) + 1e-9, 3) for v in cum]}
    digest = hashlib.sha256(GLB.read_bytes() + META.read_bytes()).hexdigest()
    return {"note": "ADR 0347; r_cum[k] = max trunk-axis distance of vertices with y < (k + 1) * step_m (model metres)",
            "step_m": STEP_M, "source_sha256": digest, "protos": dict(sorted(protos.items()))}


_TABLE = None


def table() -> dict:
    global _TABLE
    if _TABLE is None:
        _TABLE = json.loads(TABLE.read_text(encoding="utf-8"))
    return _TABLE


def proto_name(species: str, variant: int) -> str | None:
    """`tree_<species>_<variant>`; a variant beyond the library falls back to the widest one of the species."""
    prot = table()["protos"]
    n = f"tree_{species}_{int(variant)}"
    if n in prot:
        return n
    cand = [k for k in prot if k.startswith(f"tree_{species}_")]
    return max(cand, key=lambda k: prot[k]["r_cum"][-1]) if cand else None


def low_radius(proto: str, scale: float, limit_m: float) -> float:
    """Largest trunk-axis reach (m) of the scaled prototype below limit_m above the ground (0.0 = nothing there)."""
    ent = table()["protos"][proto]
    step = table()["step_m"]
    y_model = (limit_m + SUNK_M) / max(scale, 1e-6)
    if y_model <= 0:
        return 0.0
    k = min(int(np.ceil(y_model / step)), len(ent["r_cum"])) - 1
    return float(ent["r_cum"][max(k, 0)]) * scale


def scale_for(proto: str, h: float) -> float:
    return float(h) / table()["protos"][proto]["href_m"]


def main(argv):
    if "--write" in argv:
        TABLE.write_text(json.dumps(build(), separators=(",", ":")) + "\n", encoding="utf-8")
        print("wrote", TABLE)
        return 0
    if "--check" in argv:
        ok = build()["source_sha256"] == table()["source_sha256"]
        print("tree_crown_profile.json", "up to date" if ok else "STALE - run --write")
        return 0 if ok else 1
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
