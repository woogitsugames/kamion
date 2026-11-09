"""Swept-volume check of the start route (route_start.json) against the collision the Unity importer builds.

What Unity collides with (game/Assets/_Project/World/Import/RegionImporter.cs, InstanceImporter.cs):
  * every primitive of the `road_collision` node of `chunk_<ci>_<cj>.low.glb` (roads, kerbs, verges, yards,
    ramp walls, guard rails, fences, buildings),
  * `terrain_lod2` of the same file (terrain fallback collider),
  * one box per prop instance: bounds of the prototype's `.col` mesh below 2.6 m (posts / feet), extended to
    2.6 m (street_props.glb), only in chunks within 320 m of the route.

Corridor (task 2026-11-09, r4 blocker): vehicle width 2.55 m + 0.5 m margin each side (half width 1.775 m),
from ROAD_CLEAR_LO above the driven surface up to 4.0 m. ROAD_CLEAR_LO = 0.30 m: kerbs (<= 0.2 m) are
wheel-only colliders in Unity (layer WorldKerb) and the graybox bumper rides at 0.35 m; anything taller than that
inside the corridor is a wall for the cab.

Driven surface: vertical rays at the route point and on the wheel lines (+-WHEEL_LAT) against the drivable
collision surfaces (asphalt, kerb, paving, grass of road_collision and the terrain), taking the hit nearest the
previous station (the vehicle follows the surface continuously; viaduct decks over it do not count).
Step check: along each wheel line the height change per 0.5 m minus the local trend (median of the
neighbouring steps, so grades and vertical curves do not count) must stay <= STEP_MAX.

Frames: glTF (x, y, z) = (-E, U, N) (docs/WORLD_GENERATION.md); props local (x right, y front, z up), yaw CCW in
the E-N plane (InstanceImporter: Euler(0, -yaw, 0) in Unity's X=E, Z=N).
"""
from __future__ import annotations

import json
import math
import struct
from pathlib import Path

import numpy as np

HALF_W = 2.55 / 2 + 0.5           # vehicle 2.55 m + 0.5 m margin each side
HEIGHT = 4.0
ROAD_CLEAR_LO = 0.30
STEP = 0.5
STEP_MAX = 0.03
WHEEL_LAT = (-1.0, 0.0, 1.0)      # wheel tracks of a 2.55 m truck (track ~2.0 m) and the centre
PROP_COL_H = 2.6
CORRIDOR_CHUNK_M = 320.0
DRIVABLE = {"collision_asphalt", "collision_curb", "collision_paving", "collision_grass"}


# ------------------------------------------------------------------------------------------------ GLB
def read_glb(path: Path):
    data = path.read_bytes()
    jlen, = struct.unpack("<I", data[12:16])
    doc = json.loads(data[20:20 + jlen])
    binoff = 20 + jlen + 8
    return doc, data, binoff


def _acc(doc, data, binoff, ai):
    acc = doc["accessors"][ai]
    bv = doc["bufferViews"][acc["bufferView"]]
    off = binoff + bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
    n = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[acc["type"]]
    dt = {5126: "<f4", 5125: "<u4", 5123: "<u2", 5121: "<u1", 5120: "<i1"}[acc["componentType"]]
    assert bv.get("byteStride") in (None, n * np.dtype(dt).itemsize), "strided accessor"
    return np.frombuffer(data, dt, acc["count"] * n, off).reshape(acc["count"], n) if n > 1 else \
        np.frombuffer(data, dt, acc["count"], off)


def node_triangles(doc, data, binoff, node_name):
    """{material name: (k,3,3) triangles in ENU}"""
    out = {}
    for node in doc["nodes"]:
        if node["name"] != node_name:
            continue
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            P = _acc(doc, data, binoff, prim["attributes"]["POSITION"]).astype(np.float64)
            V = np.column_stack([-P[:, 0], P[:, 2], P[:, 1]])           # (-E, U, N) -> (E, N, U)
            I = _acc(doc, data, binoff, prim["indices"]).astype(np.int64).reshape(-1, 3)
            mat = doc["materials"][prim["material"]]["name"]
            out.setdefault(mat, []).append(V[I])
    return {k: np.concatenate(v) for k, v in out.items()}


def prop_boxes(props_glb: Path):
    """prototype -> (xmin, ymin, zmin, xmax, ymax, zmax) local, the importer's collider box"""
    doc, data, binoff = read_glb(props_glb)
    out = {}
    for node in doc["nodes"]:
        if not node["name"].endswith(".col"):
            continue
        name = node["name"][:-4]
        if name.startswith("tree_") or name.endswith("_gate"):
            continue
        pts = []
        for prim in doc["meshes"][node["mesh"]]["primitives"]:
            P = _acc(doc, data, binoff, prim["attributes"]["POSITION"]).astype(np.float64)
            pts.append(np.column_stack([-P[:, 0], P[:, 2], P[:, 1]]))  # local (x, y front, z up)
        P = np.concatenate(pts)
        P = P[P[:, 2] <= PROP_COL_H]
        if len(P):
            lo, hi = P.min(0), P.max(0)
            hi[2] = PROP_COL_H
            out[name] = np.concatenate([lo, hi])
    return out


def box_triangles(b, e, n, z, yaw, sz):
    x0, y0, z0, x1, y1, z1 = b
    C = np.array([[x, y, zz] for zz in (z0, z1) for y in (y0, y1) for x in (x0, x1)])
    ca, sa = math.cos(yaw), math.sin(yaw)
    W = np.column_stack([e + C[:, 0] * ca - C[:, 1] * sa, n + C[:, 0] * sa + C[:, 1] * ca, z + C[:, 2] * sz])
    F = [(0, 1, 3), (0, 3, 2), (4, 6, 7), (4, 7, 5), (0, 4, 5), (0, 5, 1), (2, 3, 7), (2, 7, 6), (0, 2, 6), (0, 6, 4),
         (1, 5, 7), (1, 7, 3)]
    return W[np.array(F)]


# ------------------------------------------------------------------------------------------------ route
def route_stations(route_json: Path, step=STEP):
    r = json.loads(route_json.read_text(encoding="utf-8"))
    P = np.asarray(r["points_en"], float)
    d = np.hypot(*np.diff(P, axis=0).T)
    keep = np.concatenate([[True], d > 1e-6])
    P = P[keep]
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    ss = np.arange(0.0, s[-1], step)
    Q = np.column_stack([np.interp(ss, s, P[:, 0]), np.interp(ss, s, P[:, 1])])
    T = np.gradient(Q, axis=0)
    T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
    Nl = np.column_stack([-T[:, 1], T[:, 0]])       # left normal
    return ss, Q, T, Nl


# ------------------------------------------------------------------------------------------------ geometry
class TriGrid:
    """2D uniform grid over triangle bboxes (E, N)."""

    def __init__(self, tris, cell=4.0):
        self.tris = tris
        self.cell = cell
        lo = np.floor(tris[:, :, :2].min(1) / cell).astype(np.int64)
        hi = np.floor(tris[:, :, :2].max(1) / cell).astype(np.int64)
        self.map = {}
        for t, (a, b) in enumerate(zip(lo, hi)):
            for i in range(a[0], b[0] + 1):
                for j in range(a[1], b[1] + 1):
                    self.map.setdefault((i, j), []).append(t)

    def query(self, xmin, ymin, xmax, ymax):
        c = self.cell
        out = set()
        for i in range(int(math.floor(xmin / c)), int(math.floor(xmax / c)) + 1):
            for j in range(int(math.floor(ymin / c)), int(math.floor(ymax / c)) + 1):
                out.update(self.map.get((i, j), ()))
        return np.fromiter(sorted(out), np.int64)


def ray_heights(tris, x, y):
    """Heights of the vertical line through (x, y) on each triangle (nan where it misses)."""
    if not len(tris):
        return np.zeros(0)
    a, b, c = tris[:, 0], tris[:, 1], tris[:, 2]
    v0, v1 = b[:, :2] - a[:, :2], c[:, :2] - a[:, :2]
    p = np.array([x, y]) - a[:, :2]
    den = v0[:, 0] * v1[:, 1] - v1[:, 0] * v0[:, 1]
    ok = np.abs(den) > 1e-12
    den = np.where(ok, den, 1.0)
    u = (p[:, 0] * v1[:, 1] - v1[:, 0] * p[:, 1]) / den
    v = (v0[:, 0] * p[:, 1] - p[:, 0] * v0[:, 1]) / den
    inside = ok & (u >= -1e-9) & (v >= -1e-9) & (u + v <= 1 + 1e-9)
    z = a[:, 2] + u * (b[:, 2] - a[:, 2]) + v * (c[:, 2] - a[:, 2])
    return np.where(inside, z, np.nan)


def tri_obb_overlap(tris, c, axes, h):
    """SAT: which triangles (k,3,3) overlap the oriented box (centre c, unit axes rows, half extents h)."""
    V = (tris - c) @ axes.T                      # box frame
    e = np.eye(3)
    f = np.stack([V[:, 1] - V[:, 0], V[:, 2] - V[:, 1], V[:, 0] - V[:, 2]], axis=1)  # (k,3,3)
    hit = np.ones(len(V), bool)

    def sep(ax):                                 # ax (k,3)
        p = np.einsum("kij,kj->ki", V, ax)
        r = np.abs(ax) @ h
        return (p.min(1) > r) | (p.max(1) < -r)

    for i in range(3):
        hit &= ~sep(np.broadcast_to(e[i], (len(V), 3)))
    nrm = np.cross(f[:, 0], f[:, 1])
    hit &= ~sep(nrm)
    for i in range(3):
        for j in range(3):
            ax = np.cross(np.broadcast_to(e[i], (len(V), 3)), f[:, j])
            deg = np.linalg.norm(ax, axis=1) < 1e-12
            s = sep(np.where(deg[:, None], e[i], ax))
            hit &= ~(s & ~deg)
    return hit


# ------------------------------------------------------------------------------------------------ check
def load_world(world_dir: Path, props_glb: Path, route_q: np.ndarray, pad=30.0):
    """Collision triangles near the route: (obstacles {name: tris}, drivable tris)"""
    lo, hi = route_q.min(0) - pad, route_q.max(0) + pad
    boxes = prop_boxes(props_glb)
    obst, drive = {}, []
    for f in sorted(world_dir.glob("chunk_*_*.low.glb")):
        ci, cj = f.name.split(".")[0].split("_")[1:3]
        doc, data, binoff = read_glb(f)
        col = node_triangles(doc, data, binoff, "road_collision")
        ter = node_triangles(doc, data, binoff, "terrain_lod2")
        parts = [(f"chunk_{ci}_{cj}/{m}", t) for m, t in col.items()] + \
                [(f"chunk_{ci}_{cj}/terrain", t) for t in ter.values()]
        for name, t in parts:
            sel = (t[:, :, 0].max(1) >= lo[0]) & (t[:, :, 0].min(1) <= hi[0]) & \
                  (t[:, :, 1].max(1) >= lo[1]) & (t[:, :, 1].min(1) <= hi[1])
            t = t[sel]
            if not len(t):
                continue
            obst.setdefault(name, []).append(t)
            if name.endswith("/terrain") or name.split("/")[1] in DRIVABLE:
                drive.append(t)
        inst = f.with_name(f"instances_{ci}_{cj}.json")
        if inst.exists():
            for it in json.loads(inst.read_text(encoding="utf-8"))["instances"]:
                b = boxes.get(it["p"])
                if b is None or not (lo[0] <= it["e"] <= hi[0] and lo[1] <= it["n"] <= hi[1]):
                    continue
                if np.min(np.hypot(route_q[:, 0] - it["e"], route_q[:, 1] - it["n"])) > CORRIDOR_CHUNK_M:
                    continue
                obst.setdefault(f"chunk_{ci}_{cj}/prop:{it['p']}", []).append(
                    box_triangles(b, it["e"], it["n"], it["z"], it.get("yaw", 0.0), it.get("sz", 1.0))[None])
    obst = {k: np.concatenate(v).reshape(-1, 3, 3) for k, v in obst.items()}
    return obst, np.concatenate(drive)


def surface_profile(ss, Q, Nl, drive_grid: TriGrid):
    """z of the driven surface on each wheel line (n, len(WHEEL_LAT)); continuity from the previous station."""
    tris = drive_grid.tris
    Z = np.full((len(ss), len(WHEEL_LAT)), np.nan)
    for k, lat in enumerate(WHEEL_LAT):
        prev = None
        for i in range(len(ss)):
            x, y = Q[i] + Nl[i] * lat
            cand = drive_grid.query(x, y, x, y)
            zs = ray_heights(tris[cand], x, y)
            zs = zs[~np.isnan(zs)]
            if not len(zs):
                continue
            if prev is None:
                z = zs.max()
            else:
                near = zs[(zs < prev + 1.0) & (zs > prev - 1.5)]
                if not len(near):
                    continue
                z = near.max()                   # topmost surface within the step window: kerbs / slopes count
            Z[i, k] = z
            prev = z
    return Z


def steps(ss, Z):
    """Height jumps per 0.5 m beyond the local trend on each wheel line -> list of (s, lat, jump)."""
    out = []
    for k, lat in enumerate(WHEEL_LAT):
        z = Z[:, k]
        d = np.diff(z)
        for i in range(len(d)):
            if np.isnan(d[i]):
                continue
            win = np.concatenate([d[max(0, i - 4):i], d[i + 1:i + 5]])
            win = win[~np.isnan(win)]
            trend = float(np.median(win)) if len(win) else 0.0
            j = d[i] - trend
            if abs(j) > STEP_MAX:
                out.append((round(float(ss[i]), 1), lat, round(float(j), 3)))
    return out


def obstructions(ss, Q, T, Nl, zc, obst):
    """Corridor boxes (one per station, 0.5 m long) vs. all collision triangles -> list of hits."""
    names = sorted(obst)
    allt = np.concatenate([obst[n] for n in names])
    owner = np.concatenate([np.full(len(obst[n]), i) for i, n in enumerate(names)])
    grid = TriGrid(allt)
    hits = []
    hz = (HEIGHT - ROAD_CLEAR_LO) / 2
    for i in range(len(ss)):
        if np.isnan(zc[i]):
            continue
        c2 = Q[i]
        r = HALF_W + STEP
        cand = grid.query(c2[0] - r, c2[1] - r, c2[0] + r, c2[1] + r)
        if not len(cand):
            continue
        c = np.array([c2[0], c2[1], zc[i] + ROAD_CLEAR_LO + hz])
        axes = np.array([[T[i, 0], T[i, 1], 0.0], [Nl[i, 0], Nl[i, 1], 0.0], [0.0, 0.0, 1.0]])
        h = np.array([STEP / 2 + 0.01, HALF_W, hz])
        m = tri_obb_overlap(allt[cand], c, axes, h)
        for t in cand[m]:
            tri = allt[t]
            cen = tri.mean(0)
            lat = float(np.dot(cen[:2] - c2, Nl[i]))
            hits.append({"s": round(float(ss[i]), 1), "obj": names[owner[t]], "e": round(float(cen[0]), 2),
                         "n": round(float(cen[1]), 2), "lat": round(lat, 2),
                         "dz_top": round(float(tri[:, 2].max() - zc[i]), 2)})
    return hits


def check(world_dir: Path, props_glb: Path, route_json: Path):
    ss, Q, T, Nl = route_stations(route_json)
    obst, drive = load_world(world_dir, props_glb, Q)
    Z = surface_profile(ss, Q, Nl, TriGrid(drive))
    zc = Z[:, WHEEL_LAT.index(0.0)]
    return {"length_m": round(float(ss[-1]), 1), "stations": len(ss),
            "no_surface": [round(float(s), 1) for s in ss[np.isnan(zc)]],
            "steps": steps(ss, Z), "hits": obstructions(ss, Q, T, Nl, zc, obst)}


if __name__ == "__main__":
    import sys
    repo = Path(__file__).resolve().parents[2]
    rid = sys.argv[1] if len(sys.argv) > 1 else "bialystok-industrial-c"
    res = check(repo / "Data" / "raw" / "derived" / rid / "world", repo / "art-source" / "world" / "props" /
                "street_props.glb", repo / "Data" / "Regions" / rid / "route_start.json")
    hs = res["hits"]
    print(f"length {res['length_m']} m, stations {res['stations']}, no surface {len(res['no_surface'])}, "
          f"steps {len(res['steps'])}, obstructed stations {len({h['s'] for h in hs})}")
    for st in res["steps"][:60]:
        print("step", st)
    seen = set()
    for h in hs:
        k = (h["s"], h["obj"])
        if k in seen:
            continue
        seen.add(k)
        print("hit", h)
    if res["no_surface"]:
        print("no surface at", res["no_surface"][:20])
