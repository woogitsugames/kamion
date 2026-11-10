"""Forest HLOD (v3.1): per 64 m cell, a canopy surface + alpha-tested edge walls that replace the individual
forest trees beyond a switch distance (LOD_POLICY["High"/"Low"]["forest_hlod_m"] in roads/build_world.py).

Why: the DK8 forest frame cost 8.2 M triangles on High (REVIEW r2 #12), almost all of it LOD1 trees at 80-250 m.
Classic flight-sim / open-world approach: near trees stay individual instances (LOD0 / LOD1 / impostor), and
whole stands far away become one cheap mesh per cell.

Per cell (CELL_M grid aligned to the tile, cell id "<i>_<j>", i east, j south, like chunks):
  piece      = forest polygons (BDOT10k OT_PTLZ_A, + 1 m for the edge band) minus roads, yards and buildings
               + 12 m (2.5 m clearance of vegetation.place + EDGE_ROW_M), clipped to the cell. The roadside row of
               trees in those 12 m is never replaced: it stays individual instances (impostors far away) in front
               of the HLOD wall, so the stand edge along a road keeps real depth at grazing angles.
  canopy     = piece triangulated on a 12 m grid (streetscape.paved.triangulate); vertex height = top of the
               crowns of the real tree instances around it (max of z + h * (0.82 + 0.18 (1 - (d / 4.5)^2)),
               d <= 4.5 m), else the local median crown height; material forest_canopy_<mix>, UV = (E, N) / 48 m.
  outer wall = piece boundary that is a real stand edge (not a cell border), split every <= 6 m; vertical quad
               from the ground - 0.3 m to the ground + EDGE_H * h_local / h_median_bake (so the trees in the
               texture have the local stand height); material forest_edge_<mix> (alpha mask, double sided),
               u = metres along the edge / 48 (continuous along each edge line), v = 0..1 bottom to top.
  inner wall = piece boundary on a cell border (also full height: when the neighbour cell is drawn as
               individual trees it is the visible stand edge; a wall cut below the canopy showed the canopy as a
               smooth hill in the first v3.1 render). Strips of consecutive segments share their vertices.
Mixes (texture sets) follow the BDOT10k forest category: iglasty -> conifer, liściasty -> broadleaf, else mixed.
Textures are baked from the same LOD0 trees by tools/blender/world/make_trees.py (forest_edge_<mix>.png,
forest_canopy_<mix>.png, sizes in trees_meta.json "forest_hlod"). A cell needs >= MIN_TREES forest trees;
its trees get "fc": <cell id> in the instance files, the engine draws either the trees or the cell mesh.
Deterministic (pure geometry of the inputs). Constants: WORKING_VALUE.
"""

from __future__ import annotations

import json
import math

import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import LineString, box

from roads import pipeline
from terrain_mesh import chunks as CH

from . import paved as PV

CELL_M = 64.0
MIN_TREES = 8
CANOPY_GRID_M = 12.0
WALL_SEG_M = 6.0
CROWN_R = 4.5
EDGE_ROW_M = 9.5          # + the 2.5 m clearance in no_forest = trees within 12 m of a road / yard stay individual
MIX_OF_CATEGORY = {"iglasty": "conifer", "liściasty": "broadleaf", "mieszany": "mixed", None: "mixed"}
TEX_REF = "art-source/world/vegetation/{}.png"


def materials():
    out = {}
    for mix in ("conifer", "mixed", "broadleaf"):
        out[f"forest_edge_{mix}"] = {"color": [1, 1, 1], "rough": 0.95, "alpha_cutoff": 0.5, "hlod": True,
                                     "texture_ref": TEX_REF.format(f"forest_edge_{mix}"),
                                     "normal_ref": TEX_REF.format(f"forest_edge_{mix}_n")}
        out[f"forest_canopy_{mix}"] = {"color": [1, 1, 1], "rough": 0.95, "hlod": True,
                                       "texture_ref": TEX_REF.format(f"forest_canopy_{mix}")}
    return out


def bake_info():
    p = pipeline.REPO / "art-source" / "world" / "vegetation" / "trees_meta.json"
    fh = json.loads(p.read_text(encoding="utf-8")).get("forest_hlod") if p.exists() else None
    if not fh:     # tree library built before v3.1: defaults of make_trees.py
        fh = {m: {"edge": {"w_m": 48.0, "h_m": 24.0, "z0_m": -0.3, "h_median_m": 15.0}, "canopy": {"w_m": 48.0}}
              for m in ("conifer", "mixed", "broadleaf")}
    return fh


def cell_of(e, n, half):
    """Cell index, clipped to the tile like build_world.chunk_of (edge-band trees just outside the tile)."""
    k = int(2 * half // CELL_M) - 1
    return (min(max(int(math.floor((e + half) / CELL_M)), 0), k),
            min(max(int(math.floor((half - n) / CELL_M)), 0), k))


def cell_box(ci, cj, half):
    e0 = -half + ci * CELL_M
    n1 = half - cj * CELL_M
    return box(e0, n1 - CELL_M, e0 + CELL_M, n1)


def build(trees, forests, no_forest, zground, half, report):
    """trees: instance dicts (forest trees carry "fk": mix); forests: [(polygon, mix)];
    no_forest: geometry where no stand can be (roads, yards, buildings + clearance); zground(e, n) -> ground z.
    Returns {cell id: {"chunk": (ci, cj), "bbox": [e0, n0, e1, n1], "prims": [...], "tris": int, "trees": int}}
    and tags the trees of every HLOD cell with "fc"."""
    fh = bake_info()
    ft = [t for t in trees if t.get("fk")]
    if not ft or not forests:
        report["forest_hlod"] = {"cells": 0}
        return {}
    P = np.array([[t["e"], t["n"]] for t in ft])
    # the row of trees within EDGE_ROW_M of a road / yard stays individual (impostors far away): a wall seen at a
    # grazing angle along the road smeared into vertical streaks (v3.1 render r2, DK8); the HLOD starts behind it
    keep_zone = no_forest.buffer(EDGE_ROW_M)
    shapely.prepare(keep_zone)
    edge_row = shapely.contains_xy(keep_zone, P[:, 0], P[:, 1])
    by_cell = {}
    for t, er in zip(ft, edge_row):
        if not er:
            by_cell.setdefault(cell_of(t["e"], t["n"], half), []).append(t)
    hlod = {c for c, lst in by_cell.items() if len(lst) >= MIN_TREES}
    # canopy / wall heights from the stand trees only: edge-band shrubs and saplings (< 8 m) pulled the canopy
    # down to 2-3 m at the stand edge and it showed as a sloping green sheet (v3.1 render r4)
    tall = np.array([t["h"] >= 8.0 for t in ft])
    Pc = P[tall]
    top = np.array([t["z"] + t["h"] for t in ft])[tall]
    H = np.array([t["h"] for t in ft])[tall]
    kd = cKDTree(Pc)

    def canopy_z(Q):
        Q = np.asarray(Q, float).reshape(-1, 2)
        out = np.empty(len(Q))
        for k, q in enumerate(Q):
            idx = kd.query_ball_point(q, CROWN_R)
            if idx:
                d = np.hypot(*(Pc[idx] - q).T)
                h = H[idx]
                out[k] = float(np.max(top[idx] - h + h * (0.82 + 0.18 * (1 - (d / CROWN_R) ** 2))))
            else:
                dd, ii = kd.query(q, k=6, distance_upper_bound=15.0)
                ii = ii[np.isfinite(dd)]
                out[k] = float(np.median(top[ii] - 0.15 * H[ii])) if len(ii) else float(zground(q[0:1], q[1:2])[0]) + 10.0
        return out

    def h_local(q):
        dd, ii = kd.query(q, k=12, distance_upper_bound=15.0)
        ii = ii[np.isfinite(dd)]
        return float(np.median(H[ii])) if len(ii) else float(np.median(H))

    # forest union per mix (each cell takes the mix with the largest area in it)
    fu = {}
    for poly, mix in forests:
        fu.setdefault(mix, []).append(poly.buffer(1.0))
    fu = {m: shapely.union_all(v) for m, v in fu.items()}
    allf = shapely.difference(shapely.union_all(list(fu.values())), keep_zone)
    shapely.prepare(allf)
    cells = {}
    n_tris = 0
    for (ci, cj) in sorted(hlod):
        cb = cell_box(ci, cj, half)
        piece = shapely.intersection(allf, cb)
        if piece.is_empty or piece.area < 50.0:
            continue
        piece = shapely.make_valid(piece.simplify(0.5))
        mix = max(fu, key=lambda m: shapely.intersection(fu[m], cb).area)
        edge_info = fh[mix]["edge"]
        Wt = fh[mix]["canopy"]["w_m"]
        prims = []
        # canopy
        T2 = []
        for g in getattr(piece, "geoms", [piece]):
            if g.geom_type == "Polygon" and g.area > 1.0:
                T2.append(PV.triangulate(g, CANOPY_GRID_M))
        if not T2:
            continue
        T2 = np.concatenate(T2)
        XY, inv = np.unique(np.round(T2.reshape(-1, 2), 3), axis=0, return_inverse=True)
        Z = canopy_z(XY)
        V = np.column_stack([XY, Z])
        prims.append({"V": V, "T": inv.reshape(-1, 3), "UV": XY / Wt, "mat": f"forest_canopy_{mix}",
                      "N": np.tile([0.0, 0.0, 1.0], (len(V), 1))})
        # walls
        Vw, Tw, UVw, Nw = [], [], [], []
        bnd = piece.boundary
        cbl = cb.exterior
        for line in getattr(bnd, "geoms", [bnd]):
            c = np.asarray(line.coords)
            if len(c) < 2:
                continue
            Ls = np.hypot(*np.diff(c, axis=0).T)
            # densify
            pts = [c[0]]
            for a, b, L in zip(c[:-1], c[1:], Ls):
                k = max(1, int(math.ceil(L / WALL_SEG_M)))
                pts += [a + (b - a) * (i / k) for i in range(1, k + 1)]
            pts = np.array(pts)
            s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(pts, axis=0).T))])
            u0 = ((pts[0, 0] + pts[0, 1]) % Wt) / Wt
            zg = zground(pts[:, 0], pts[:, 1]) + edge_info["z0_m"]
            # segment classes: inner (cell border towards another HLOD cell) or outer (real stand edge)
            nseg = len(pts) - 1
            inner = np.zeros(nseg, bool)
            face = np.ones(nseg)                       # +1: front face toward the right of travel
            outw = np.zeros((nseg, 2))
            for i in range(nseg):
                a, b = pts[i], pts[i + 1]
                L = float(np.hypot(*(b - a)))
                if L < 1e-6:
                    continue
                mid = (a + b) / 2
                d = (b - a) / L
                nl = np.array([-d[1], d[0]])
                left_in = piece.contains(shapely.Point(*(mid + nl * 0.6)))
                outw[i] = -nl if left_in else nl
                face[i] = 1.0 if left_in else -1.0     # stand on the left -> outside (front) on the right
                if cbl.distance(shapely.Point(*mid)) < 0.05:
                    q = mid - nl * 1.0 if left_in else mid + nl * 1.0
                    nb = cell_of(q[0], q[1], half)
                    inner[i] = nb in hlod and nb != (ci, cj)          # tile border: outer wall
            hw = np.array([edge_info["h_m"] * h_local(p) / edge_info["h_median_m"] for p in pts])

            # strips of consecutive segments of the same class and facing share their vertices
            i = 0
            while i < nseg:
                j = i
                while j + 1 < nseg and inner[j + 1] == inner[i] and face[j + 1] == face[i]:
                    j += 1
                idx = np.arange(i, j + 2)                      # point indices of the strip
                # full height on inner borders too: from the road the inner wall IS the stand edge (the neighbour
                # cell is drawn as trees); a cut wall showed the canopy above it as a smooth hill (v3.1 render r1)
                wtop = zg[idx] + hw[idx]
                nrm = np.zeros((len(idx), 2))
                nrm[:-1] += outw[i:j + 1]
                nrm[1:] += outw[i:j + 1]
                nrm /= np.maximum(np.hypot(nrm[:, 0], nrm[:, 1]), 1e-9)[:, None]
                n3 = np.column_stack([nrm, np.full(len(idx), 0.5)])
                n3 /= np.linalg.norm(n3, axis=1)[:, None]
                base = len(Vw)
                k = len(idx)
                Vw += [[pts[p][0], pts[p][1], zg[p]] for p in idx] + [[pts[p][0], pts[p][1], t] for p, t in zip(idx, wtop)]
                us = u0 + s[idx] / Wt
                UVw += [[u, 0.0] for u in us] + [[u, (t - zg[p]) / hw[p]] for u, p, t in zip(us, idx, wtop)]
                Nw += list(n3) + list(n3)
                for m_ in range(k - 1):
                    b0, b1, t0, t1 = base + m_, base + m_ + 1, base + k + m_, base + k + m_ + 1
                    if face[i] > 0:
                        Tw += [[b0, b1, t1], [b0, t1, t0]]
                    else:
                        Tw += [[b0, t1, b1], [b0, t0, t1]]
                i = j + 1
        if Tw:
            prims.append({"V": np.array(Vw), "T": np.array(Tw), "UV": np.array(UVw), "N": np.array(Nw),
                          "mat": f"forest_edge_{mix}"})
        cid = f"{ci}_{cj}"
        tris = int(sum(len(p["T"]) for p in prims))
        n_tris += tris
        for t in by_cell[(ci, cj)]:
            t["fc"] = cid
        e0, n0, e1, n1 = cb.bounds
        cx, cy = (e0 + e1) / 2, (n0 + n1) / 2
        k = int(CH.CHUNK_M // CELL_M)
        cells[cid] = {"chunk": (ci // k, cj // k), "bbox": [round(x, 2) for x in piece.bounds], "prims": prims,
                      "tris": tris, "trees": len(by_cell[(ci, cj)]), "mix": mix, "centre": [cx, cy]}
    report["forest_hlod"] = {"cells": len(cells), "cell_m": CELL_M, "triangles": n_tris,
                             "trees_replaced_far": int(sum(c["trees"] for c in cells.values())),
                             "forest_trees": len(ft)}
    return cells
