"""ADR 0300: obstacles in the swept path of the autopilot truck along the corridor routes (exported world chunks).

The owner's autopilot run Bialystok -> Tykocin (s24) drove into a noise barrier standing in the right lane of the
Kleeberga viaduct ramp: the barrier existed in no QA because every check tested source lines against the ground
road footprint, none tested the built meshes against the line the truck actually follows. This one does:

  for every tile of a corridor (Resources/WorldStreaming/route_links.json `corridors`), the tile's start route
  (Data/Regions/<tile>/route_start.json, centre of the rightmost lane, step 2 m) and the route links lying in the tile
  are swept with the truck body envelope (half width ENVELOPE_HALF_W_M, from ENVELOPE_FLOOR_M to ENVELOPE_TOP_M over
  the drivable collision surface under the line), against the High GLB chunks of the tile:
    collider   road_collision triangles that are not drivable surface (collision_fence / _steel / _building / ...):
               the truck hits them -> FAIL;
    visual     furniture / bridge / building triangles (not road surface): a wall seen in the lane -> WARN.
  The surface level under the line follows the previous sample (decks over ground roads), so a deck soffit far above
  a ground road and a ground barrier far under a deck are not in the envelope.

  uv run --project tools/worldgen python tools/worldgen/qa/route_obstacles.py [--corridor bialystok-tykocin]
      [--tiles a,b] [--out artifacts/.../route_obstacles.json]      exit 1 = a collider in the envelope
"""
from __future__ import annotations

import argparse
import glob
import json
import struct
import sys
from pathlib import Path

import numpy as np
import shapely

REPO = Path(__file__).resolve().parents[3]
LINKS = REPO / "game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/route_links.json"

ENVELOPE_HALF_W_M = 1.2    # WORKING_VALUE: inside the 2.55 m body of the TRAKT tractor / trailer (lane keeping +-0.05 m)
ENVELOPE_FLOOR_M = 0.35    # over the kerb heights (0.13-0.2 m): a kerb under a wheel is not an obstacle here
ENVELOPE_TOP_M = 3.8       # under the 4.0 m body; overhead structures above it (gantries, decks, soffits) are not hits
SURFACE_MATS = ("collision_asphalt", "collision_paving", "collision_grass", "collision_gravel")
VISUAL_NODES = ("furniture", "bridge", "buildings", "plots")
VISUAL_SKIP = ("road_asphalt", "shoulder_gravel", "sidewalk_paving", "verge_grass", "bridge_soffit")


def read_glb(path):
    """[(node name, material name, V (n,3) in region-local E, N, Z, T (m,3))] of a world chunk GLB (exporter axes
    (x, y, z) = (-E, U, N), terrain_mesh.gltf)."""
    b = Path(path).read_bytes()
    jl = struct.unpack("<I", b[12:16])[0]
    js = json.loads(b[20:20 + jl])
    bin0 = 20 + jl + 8
    out = []

    def acc_arr(i, comps, dtype_map={5126: np.float32, 5125: np.uint32, 5123: np.uint16, 5121: np.uint8}):
        a = js["accessors"][i]
        bv = js["bufferViews"][a["bufferView"]]
        dt = np.dtype(dtype_map[a["componentType"]])
        off = bin0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
        st = bv.get("byteStride", 0)
        if st and st != dt.itemsize * comps:
            raw = np.frombuffer(b, np.uint8, count=st * a["count"], offset=off).reshape(-1, st)
            return raw[:, :dt.itemsize * comps].copy().view(dt).reshape(-1, comps)
        return np.frombuffer(b, dt, count=a["count"] * comps, offset=off).reshape(-1, comps)
    for node in js["nodes"]:
        if "mesh" not in node:
            continue
        tr = np.array(node.get("translation", [0, 0, 0]), float)
        for prim in js["meshes"][node["mesh"]]["primitives"]:
            if prim.get("mode", 4) != 4 or "indices" not in prim:
                continue
            P = acc_arr(prim["attributes"]["POSITION"], 3).astype(float) + tr
            V = np.column_stack([-P[:, 0], P[:, 2], P[:, 1]])
            T = acc_arr(prim["indices"], 1).reshape(-1, 3).astype(np.int64)
            mat = js["materials"][prim["material"]]["name"] if "material" in prim else "?"
            out.append((node.get("name", ""), mat, V, T))
    return out


def classify(prims):
    """-> (surface triangles (n,3,3), [(kind, label, triangles)] obstacle groups)."""
    surf, obst = [], []
    for name, mat, V, T in prims:
        tri = V[T]
        if name == "road_collision":
            if mat in SURFACE_MATS:
                surf.append(tri)
            else:
                obst.append(("collider", f"{name}|{mat}", tri))
        elif name in VISUAL_NODES and mat not in VISUAL_SKIP:
            obst.append(("visual", f"{name}|{mat}", tri))
    S = np.concatenate(surf) if surf else np.zeros((0, 3, 3))
    return S, obst


def _surface_z(S, tree, p, z_prev):
    """Collision surface heights under p (barycentric); the one nearest z_prev (lowest when z_prev is None)."""
    idx = tree.query(shapely.Point(p))
    zs = []
    for k in idx:
        a, b, c = S[k]
        d = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
        if abs(d) < 1e-12:
            continue
        l1 = ((b[1] - c[1]) * (p[0] - c[0]) + (c[0] - b[0]) * (p[1] - c[1])) / d
        l2 = ((c[1] - a[1]) * (p[0] - c[0]) + (a[0] - c[0]) * (p[1] - c[1])) / d
        l3 = 1.0 - l1 - l2
        if min(l1, l2, l3) >= -1e-6:
            zs.append(l1 * a[2] + l2 * b[2] + l3 * c[2])
    if not zs:
        return None
    zs = np.array(zs)
    return float(zs.min() if z_prev is None else zs[np.argmin(np.abs(zs - z_prev))])


def sweep(route, S, obst, step=2.0):
    """Hits of obstacle triangles in the envelope along route (n,2). -> (hits, n_no_surface). Each hit:
    (kind, label, s, e, n, dz_min, dz_max) per route sample (one per label and sample)."""
    route = np.asarray(route, float)
    stree = shapely.STRtree(shapely.polygons(np.concatenate([S[:, :, :2], S[:, :1, :2]], axis=1))) if len(S) else None
    zs, z_prev, miss = [], None, 0
    for p in route:
        z = _surface_z(S, stree, p, z_prev) if stree is not None else None
        if z is None:
            miss += 1
        else:
            z_prev = z
        zs.append(z if z is not None else z_prev)
    hits = []
    line = shapely.LineString(route)
    corridor = line.buffer(ENVELOPE_HALF_W_M + 0.5)
    from scipy.spatial import cKDTree
    rtree = cKDTree(route)
    for kind, label, tri in obst:
        c = tri[:, :, :2].mean(1)                     # cheap pre-filter: centroid within (radius + envelope) of a sample
        rad = np.linalg.norm(tri[:, :, :2] - c[:, None, :], axis=2).max(1)
        d, _ = rtree.query(c, distance_upper_bound=float(rad.max()) + ENVELOPE_HALF_W_M + 2.5)
        tri = tri[d <= rad + ENVELOPE_HALF_W_M + 2.5]
        if not len(tri):
            continue
        polys = shapely.polygons(np.concatenate([tri[:, :, :2], tri[:, :1, :2]], axis=1))
        flat = shapely.area(polys) < 1e-6
        polys = np.where(flat, shapely.buffer(shapely.linestrings(tri[:, :, :2]), 0.01), polys)
        near = np.nonzero(shapely.intersects(polys, corridor))[0]
        if not len(near):
            continue
        ptree = shapely.STRtree(polys[near])
        for i in range(len(route) - 1):
            if zs[i] is None:
                continue
            seg = shapely.LineString(route[i:i + 2]).buffer(ENVELOPE_HALF_W_M, cap_style="flat")
            cand = ptree.query(seg, predicate="intersects")
            if not len(cand):
                continue
            lo, hi = zs[i] + ENVELOPE_FLOOR_M, zs[i] + ENVELOPE_TOP_M
            best = None
            for c in cand:
                t = tri[near[c]]
                part = shapely.intersection(polys[near[c]], seg)
                zmn, zmx = _tri_z_range_over(t, part)
                if zmx >= lo and zmn <= hi:
                    best = (min(best[0], zmn), max(best[1], zmx)) if best else (zmn, zmx)
            if best:
                hits.append((kind, label, round(i * step, 1), round(float(route[i, 0]), 1),
                             round(float(route[i, 1]), 1), round(best[0] - zs[i], 2), round(best[1] - zs[i], 2)))
    return hits, miss


def _tri_z_range_over(t, part):
    """z range of triangle t over the 2D region `part` (its plane at part's vertices; vertical triangles: own range)."""
    nrm = np.cross(t[1] - t[0], t[2] - t[0])
    ln = np.linalg.norm(nrm)
    if ln < 1e-12 or abs(nrm[2]) / ln < 0.3 or part.is_empty:
        return float(t[:, 2].min()), float(t[:, 2].max())
    pts = np.asarray(shapely.get_coordinates(part))
    z = t[0, 2] - (nrm[0] * (pts[:, 0] - t[0, 0]) + nrm[1] * (pts[:, 1] - t[0, 1])) / nrm[2]
    return float(z.min()), float(z.max())


def tile_routes(tile, links):
    """[(name, points (n,2) region-local)] of the start route and the links lying in the tile."""
    out = []
    rs = REPO / "Data/Regions" / tile / "route_start.json"
    if rs.exists():
        out.append(("route_start", np.array(json.loads(rs.read_text(encoding="utf-8"))["points_en"], float)))
    for l in links:
        if l["tile"] == tile:
            out.append((f"link:{l['id']}", np.column_stack([l["e"], l["n"]]).astype(float)))
    return out


def run_tile(tile, links, derived=None):
    derived = Path(derived or REPO / "Data/raw/derived")
    files = sorted(f for f in glob.glob(str(derived / tile / "world" / "chunk_*_*.glb")) if not f.endswith(".low.glb"))
    if not files:
        return {"tile": tile, "built": False}
    prims = [p for f in files for p in read_glb(f)]
    S, obst = classify(prims)
    rep = {"tile": tile, "built": True, "routes": []}
    for name, pts in tile_routes(tile, links):
        hits, miss = sweep(pts, S, obst)
        groups = {}
        for kind, label, s, e, n, d0, d1 in hits:
            g = groups.setdefault((kind, label), {"kind": kind, "label": label, "s": [s, s], "first_en": [e, n],
                                                  "dz": [d0, d1], "samples": 0})
            g["s"] = [min(g["s"][0], s), max(g["s"][1], s)]
            g["dz"] = [min(g["dz"][0], d0), max(g["dz"][1], d1)]
            g["samples"] += 1
        rep["routes"].append({"route": name, "length_m": round(float(np.sum(np.hypot(*np.diff(pts, axis=0).T))), 1),
                              "no_surface_samples": miss,
                              "colliders": [g for g in groups.values() if g["kind"] == "collider"],
                              "visual": [g for g in groups.values() if g["kind"] == "visual"]})
    return rep


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--corridor", default="bialystok-tykocin")
    ap.add_argument("--tiles", default="")
    ap.add_argument("--derived", default=None)
    ap.add_argument("--out", default=None)
    a = ap.parse_args(argv)
    L = json.loads(LINKS.read_text(encoding="utf-8"))
    if a.tiles:
        tiles = [t for t in a.tiles.split(",") if t]
    else:
        tiles = next(c["tiles"] for c in L["corridors"] if c["id"] == a.corridor)
    reps, fail = [], 0
    for t in tiles:
        r = run_tile(t, L["links"], a.derived)
        reps.append(r)
        if not r["built"]:
            print(f"{t:28s} not built")
            continue
        for rr in r["routes"]:
            nc, nv = len(rr["colliders"]), len(rr["visual"])
            fail += nc
            print(f"{t:28s} {rr['route']:32s} {rr['length_m']:7.0f} m  colliders {nc}  visual {nv}  "
                  f"no-surface {rr['no_surface_samples']}")
            for g in rr["colliders"] + rr["visual"]:
                print(f"    {g['kind']:8s} {g['label']:34s} s {g['s'][0]:.0f}..{g['s'][1]:.0f} at {g['first_en']} "
                      f"dz {g['dz'][0]:.2f}..{g['dz'][1]:.2f} ({g['samples']} samples)")
    out = {"schema": "truck-sim-pl/route-obstacles/1", "adr": "0300",
           "envelope": {"half_width_m": ENVELOPE_HALF_W_M, "floor_m": ENVELOPE_FLOOR_M, "top_m": ENVELOPE_TOP_M},
           "tiles": reps, "colliders_total": fail}
    if a.out:
        Path(a.out).parent.mkdir(parents=True, exist_ok=True)
        Path(a.out).write_text(json.dumps(out, indent=1, ensure_ascii=False), encoding="utf-8")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
