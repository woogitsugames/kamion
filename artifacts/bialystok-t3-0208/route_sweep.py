"""ADR 0208: passability of the control route + height match at the tile seams, from the world chunks (no phone).

    uv run --project tools/worldgen python artifacts/bialystok-t3-0208/route_sweep.py sweep <region>
    uv run --project tools/worldgen python artifacts/bialystok-t3-0208/route_sweep.py seam <region> <neighbour> <neighbour world dir>

sweep: every 2 m of Data/Regions/<region>/route_start.json (centre of the rightmost lane), lateral offsets
       -1.25 / 0 / +1.25 m (2.55 m truck body): the road collision surface must exist, and no triangle of any
       material of the finest LOD nor of terrain_lod2 (terrain collision) may lie 0.3-4.5 m above it.
seam : at every road that crosses the shared tile edge (boundary nodes of roads.graph.json) the road collision
       height 0.5 m inside each tile, and the terrain_lod2 height every 64 m along the edge, 1 m inside each tile.
After probe_lod2.py / route_sweep.py of ADR 0206 (artifacts/bialystok-dk65-t2-0206)."""
import json
import struct
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
import junction_topview as jt  # noqa: E402

jt.colour = lambda n: (0, 0, 0)


def region(rid):
    import yaml
    return yaml.safe_load((REPO / "Data" / "Regions" / rid / "region.yaml").read_text(encoding="utf-8"))


def named_nodes(path, want):
    b = path.read_bytes()
    n = struct.unpack("<I", b[12:16])[0]
    j = json.loads(b[20:20 + n])
    bin0 = 20 + n + 8
    ct = {5121: np.uint8, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
    nc = {"SCALAR": 1, "VEC3": 3, "VEC2": 2, "VEC4": 4}

    def acc(i):
        a = j["accessors"][i]
        bv = j["bufferViews"][a["bufferView"]]
        off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        dt = np.dtype(ct[a["componentType"]])
        k = nc[a["type"]]
        return np.frombuffer(b, dt, a["count"] * k, off).reshape(a["count"], k)

    for node in j["nodes"]:
        if node.get("name", "") not in want or "mesh" not in node:
            continue
        t = np.array(node.get("translation", [0, 0, 0]), float)
        for pr in j["meshes"][node["mesh"]]["primitives"]:
            p = acc(pr["attributes"]["POSITION"]).astype(float) + t
            yield node["name"], np.stack([-p[:, 0], p[:, 2], p[:, 1]], 1)[acc(pr["indices"]).reshape(-1, 3)]


def collision(wdir):
    T = {"terrain_lod2": [], "road_collision": []}
    for f in sorted(Path(wdir).glob("chunk_*.glb")):
        if f.name.endswith(".low.glb"):
            continue
        for nm, tr in named_nodes(f, set(T)):
            T[nm].append(tr)
    return {k: np.concatenate(v) if v else np.zeros((0, 3, 3)) for k, v in T.items()}


def tri_z(tris, x, y):
    m = ((tris[:, :, 0].min(1) <= x) & (tris[:, :, 0].max(1) >= x)
         & (tris[:, :, 1].min(1) <= y) & (tris[:, :, 1].max(1) >= y))
    out = []
    for t in tris[m]:
        (x1, y1), (x2, y2), (x3, y3) = t[:, :2]
        d = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(d) < 1e-9:
            continue
        a = ((y2 - y3) * (x - x3) + (x3 - x2) * (y - y3)) / d
        b = ((y3 - y1) * (x - x3) + (x1 - x3) * (y - y3)) / d
        c = 1 - a - b
        if min(a, b, c) >= -1e-6:
            out.append(a * t[0, 2] + b * t[1, 2] + c * t[2, 2])
    return out


def sweep(rid):
    wdir = REPO / "Data" / "raw" / "derived" / rid / "world"
    T = collision(wdir)
    W = jt.load_world(rid)
    r = json.loads((REPO / "Data" / "Regions" / rid / "route_start.json").read_text(encoding="utf-8"))
    P = np.asarray(r["points_en"], float)[:, :2]
    blocked, holes, prev, maxstep, n = [], [], None, 0.0, 0
    for i in range(1, len(P) - 1):
        if not (abs(P[i, 0]) < 1023 and abs(P[i, 1]) < 1023):
            continue
        t = P[i + 1] - P[i - 1]
        t /= max(np.hypot(*t), 1e-9)
        nr = np.array([-t[1], t[0]])
        for off in (-1.25, 0.0, 1.25):
            x, y = P[i] + off * nr
            n += 1
            road = tri_z(T["road_collision"], x, y)
            if not road:
                holes.append((i * 2, off, round(x, 1), round(y, 1)))
                continue
            r0 = min(road, key=lambda z: abs(z - (prev if prev is not None else z)))
            if off == 0.0:
                if prev is not None:
                    maxstep = max(maxstep, abs(r0 - prev))
                prev = r0
            hit = [(round(z - r0, 2), "terrain_lod2") for z in tri_z(T["terrain_lod2"], x, y) if 0.3 < z - r0 < 4.5]
            for nm, tr, lo, hi in W:
                if lo[0] <= x <= hi[0] and lo[1] <= y <= hi[1]:
                    hit += [(round(z - r0, 2), nm) for z in tri_z(tr, x, y) if 0.3 < z - r0 < 4.5]
            if hit:
                blocked.append((i * 2, off, round(x, 1), round(y, 1), sorted(hit)[:3]))
    print(f"{rid}: route {r['length_m']:.0f} m, samples {n}, no road collision {len(holes)}, "
          f"blocked {len(blocked)}, max step of the collision surface on the lane centre {maxstep:.2f} m / 2 m")
    for h in holes[:20]:
        print("  hole", h)
    for b in blocked[:40]:
        print("  blocked", b)


def seam(rid, other, other_world):
    a, b = region(rid), region(other)
    xa = a["bbox"]["xmin"] if abs(a["bbox"]["xmin"] - b["bbox"]["xmax"]) < 0.01 else a["bbox"]["xmax"]
    sgn = 1.0 if xa == a["bbox"]["xmin"] else -1.0               # +x = into tile `rid`
    Ta = collision(REPO / "Data" / "raw" / "derived" / rid / "world")
    Tb = collision(other_world)
    oa, ob = (a["origin"]["x"], a["origin"]["y"]), (b["origin"]["x"], b["origin"]["y"])
    g = json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))
    nodes = {n["id"]: n for n in g["nodes"]}
    seen = {}
    for e in g["edges"]:
        for k in ("from", "to"):
            n = nodes[e[k]]
            if n.get("boundary") and abs(n["x"] - xa) < 0.01:
                seen[round(n["y"], 2)] = (e["osm_way"], e["attrs"]["highway"]["v"])
    print(f"seam {rid} | {other} at x = {xa:.0f}: road collision height 0.5 m inside each tile")
    worst = 0.0
    for y, (way, hw) in sorted(seen.items()):
        za = tri_z(Ta["road_collision"], xa + sgn * 0.5 - oa[0], y - oa[1])
        zb = tri_z(Tb["road_collision"], xa - sgn * 0.5 - ob[0], y - ob[1])
        if za and zb:
            dz = min(abs(p - q) for p in za for q in zb)
            worst = max(worst, dz)
            print(f"  y {y:9.2f} way {way:>10} {hw:<12} z {min(za):7.2f} | {min(zb):7.2f}  dz {dz:.2f} m")
        else:
            print(f"  y {y:9.2f} way {way:>10} {hw:<12} no road collision: here {len(za)}, neighbour {len(zb)}")
    print(f"  worst road step {worst:.2f} m")
    dt = []
    for y in np.arange(a["bbox"]["ymin"] + 32, a["bbox"]["ymax"], 64.0):
        za = tri_z(Ta["terrain_lod2"], xa + sgn * 1.0 - oa[0], y - oa[1])
        zb = tri_z(Tb["terrain_lod2"], xa - sgn * 1.0 - ob[0], y - ob[1])
        if za and zb:
            dt.append(abs(za[0] - zb[0]))
    if dt:
        print(f"  terrain_lod2 2 m apart across the edge, {len(dt)} stations: median {np.median(dt):.2f} m, "
              f"p90 {np.percentile(dt, 90):.2f} m, max {max(dt):.2f} m")


if __name__ == "__main__":
    if sys.argv[1] == "sweep":
        sweep(sys.argv[2])
    else:
        seam(sys.argv[2], sys.argv[3], sys.argv[4])
