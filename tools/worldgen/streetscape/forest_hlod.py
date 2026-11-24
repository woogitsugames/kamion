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

import hashlib
import json
import math

import numpy as np
import shapely
from scipy.spatial import cKDTree
from shapely.geometry import box

from roads import pipeline
from terrain_mesh import chunks as CH

from . import paved as PV

CELL_M = 64.0
MIN_TREES = 8
CANOPY_GRID_M = 12.0
WALL_SEG_M = 6.0
CROWN_R = 4.5
# ADR 0187 mantle skirt: a second, low wall SKIRT_OFF_M in front of every outer wall, textured with the mantle strip
# of the edge texture (v above "v_main" of trees_meta.json, stored upside down: v = 1 at the ground). Same mesh
# primitive and material as the wall (no extra draw). A stand seen from the side then steps down shrub - young
# trees - canopy instead of ending in one vertical plane.
SKIRT_OFF_M = 3.5
SKIRT_KEEP = 0.45          # M68 had 0.18 (shrub skirt on ~15-20 % of outer edges); ADR 0324: the far stand read as a
#                            flat curtain with a ruler foot (critic s24 wave 6 # 4.3) - nearly half of the outer edge
#                            carries the skirt, its height varies along the edge (SKIRT_H_VAR)
SKIRT_H_VAR = (0.55, 1.25)
# ADR 0324 (WORKING_VALUE): the wall top follows a smooth noise (TOP_VAR x the stand height over TOP_NOISE_M) instead
# of one height per 12 trees = a ruler line; a second wall BACK_OFF_M behind every outer wall, taller by BACK_H and
# with another part of the edge texture, shows through the gaps of the first one and breaks its silhouette (depth
# parallax when driving past); corners step down further and over two segments.
TOP_VAR = (0.82, 1.14)
TOP_NOISE_M = 16.0
BACK_OFF_M = 6.0
BACK_H = (1.04, 1.22)
CANOPY_EDGE_M = 5.0        # canopy vertices this close to an outer stand edge are lowered ...
CANOPY_EDGE_DROP = (0.62, 0.86)   # ... to this share of the crown height at the edge itself
SKIRT_SEG_M = 18.0
# ADR 0339: on a tile with a canopy height model (streetscape.forest_chm) the canopy sheet and the wall tops take the
# measured crown tops instead of the heights of the generated trees: the top line of a stand is the surveyed one (old
# stand next to a pole stand, veterans, sagging edges). The model already carries the variation, so the wall-top
# noise of ADR 0324 shrinks to CHM_TOP_VAR; under CHM_TRUST_M the model has no crowns (cell outside its mask, small
# hole) and the tree-based value is used.
CHM_TOP_VAR = (0.94, 1.05)
CHM_TRUST_M = 3.0
# top of the crowns in the baked edge picture / height of the picture (90th percentile of the topmost opaque texel
# per column of forest_edge_<mix>.png, v 0 .. v_main; measured 2026-11-24, test_forest_chm_0339): the wall quad is
# sized so that these crowns stand at the measured dominant height. The class rule sizes the quad by the median
# height of ALL plants of the picture (h_median_m 10.9-13.9 m incl. the understorey), which puts the crown line of a
# broadleaf stand at ~1.5 x the height of its trees - tiles with a height model no longer have that step.
CHM_WALL_TOP_FRAC = {"conifer": 0.888, "mixed": 0.833, "broadleaf": 0.766}
CHM_BACK_VAR = (0.97, 1.06)   # second wall: the measured tops 6 m further in x this (class rule: BACK_H x the front)
CHM_CANOPY_K = 0.84        # canopy sheet under the crown tops: it only closes the stand from above, the ribs carry the tops
# Ribs: with measured heights a stand is no longer level - taller parts stand behind lower ones, and from the road the
# canopy sheet of the taller part showed over the front wall as a smooth green hill (render r1, dk65-04
# fh_cab_approach). Alpha-tested walls of the same edge picture cross the stand every RIB_M in both directions (lines
# of the absolute metre grid, so they continue from cell to cell), tops at the measured crowns: every height step
# of the stand has a ragged crown line. Same primitive and material as the walls (no extra draw).
RIB_M = 16.0
RIB_SEG_M = 8.0
RIB_MIN_LEN_M = 8.0
RIB_WAVE_M = 40.0
RIB_WAVE_AMP_M = 4.5


def _vnoise2(x, y, period, salt=""):
    """Smooth value noise in 0..1 on a hash lattice (deterministic, the same in every tile: absolute local metres)."""
    fx, fy = x / period, y / period
    ix, iy = math.floor(fx), math.floor(fy)
    tx, ty = fx - ix, fy - iy
    tx, ty = tx * tx * (3 - 2 * tx), ty * ty * (3 - 2 * ty)

    def h(i, j):
        return int(hashlib.sha1(f"fh:{salt}:{i}:{j}".encode()).hexdigest()[:8], 16) / 0xFFFFFFFF
    return ((h(ix, iy) * (1 - tx) + h(ix + 1, iy) * tx) * (1 - ty)
            + (h(ix, iy + 1) * (1 - tx) + h(ix + 1, iy + 1) * tx) * ty)


def _skirt_keep(a, b):
    """Deterministic spatial-bucket hash (~18% of outer wall segments get the low shrub skirt)."""
    mx, my = 0.5 * (float(a[0]) + float(b[0])), 0.5 * (float(a[1]) + float(b[1]))
    key = f"skirt:{int(round(mx / SKIRT_SEG_M))}:{int(round(my / SKIRT_SEG_M))}"
    return (int(hashlib.sha1(key.encode()).hexdigest()[:8], 16) % 1000) < int(round(SKIRT_KEEP * 1000))
CORNER_COS = 0.72          # outer edge turning by more than ~44 degrees at a point = a stand corner
CORNER_DROP = 0.62         # wall height factor at the corner (ADR 0324: was 0.80; 0.81 one point either side)
EDGE_ROW_M = 9.5          # + the 2.5 m clearance in no_forest = trees within 12 m of a road / yard stay individual
MIX_OF_CATEGORY = {"iglasty": "conifer", "liściasty": "broadleaf", "mieszany": "mixed", None: "mixed"}
TEX_REF = "art-source/world/vegetation/{}.png"


# ADR 0330: hazed copies of the edge textures for the far-field ring (streetscape.far_field.HAZE_BANDS). The ring is
# foreshortened, so the scene haze sees a 1.5-4 km stand at <= ~1.7 km; the missing extinction of the band is baked
# into the albedo: linear rgb -> lerp(rgb, HAZE_ALBEDO, k), alpha and the normal / visibility map unchanged.
# k = 1 - exp(-beta * (d_true - d_eff)) at the band's typical stand (1.4 km: 0.16, 3.0 km: 0.37; beta = 3.912 / 20 km).
HAZE_ALBEDO = (0.36, 0.42, 0.50)       # WORKING_VALUE (see far_field.HAZE_ALBEDO)
HAZE_SUFFIX_K = {"_haze1": 0.16, "_haze2": 0.37}
HAZE_MIXES = ("conifer", "mixed", "broadleaf")


def _srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _lin_to_srgb(c):
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0.0), 1.0 / 2.4) - 0.055)


# farfield-low-s24 (ADR 0330 addendum): the far-field sectors keep ONE curtain primitive on both tiers
# (test_far_field: <= 2 submeshes per sector) - the 3 mixes x 3 haze bands live in one atlas, slots stacked in v
# (v measured from the bottom of the PNG, as the edge textures), each slot = the whole edge texture squeezed to
# 1/9 of the height minus FAR_ATLAS_PAD transparent rows above and below (no mip bleed between slots at the far
# distances). Normal / visibility atlas with the same fractional layout. Deterministic, rebuilt only when a source
# changes (sha256 in forest_edge_far_atlas.json).
FAR_ATLAS_SLOTS = tuple((mix, suf) for mix in HAZE_MIXES for suf in ("",) + tuple(HAZE_SUFFIX_K))
FAR_ATLAS_SIZE = (1024, 2048)          # albedo w x h; the normal atlas is half of it
FAR_ATLAS_PAD = 4                      # transparent rows above / below each slot (albedo atlas)
FAR_ATLAS_MAT = "forest_edge_mixed_far_atlas"   # name keeps "forest_edge_mixed": canopy policy, runtime swap


def far_atlas_slot_v(mix: str, suf: str) -> tuple[float, float]:
    """(v0, v1) of a slot, v from the bottom of the atlas."""
    k = FAR_ATLAS_SLOTS.index((mix if mix in HAZE_MIXES else "mixed", suf))
    h = FAR_ATLAS_SIZE[1]
    r0 = round(k * h / len(FAR_ATLAS_SLOTS)) + FAR_ATLAS_PAD
    r1 = round((k + 1) * h / len(FAR_ATLAS_SLOTS)) - FAR_ATLAS_PAD
    return r0 / h, r1 / h


def _haze(im, k):
    out = im.copy()
    lin = _srgb_to_lin(im[..., :3])
    out[..., :3] = _lin_to_srgb(lin * (1.0 - k) + np.asarray(HAZE_ALBEDO)[None, None, :] * k)
    return out


def far_atlas(root=None, log=print) -> dict:
    """Write art-source/world/vegetation/forest_edge_mixed_far_atlas.png (+ _n) from the baked edge textures."""
    from PIL import Image
    root = root or pipeline.REPO
    vdir = root / "art-source" / "world" / "vegetation"
    meta_p = vdir / "forest_edge_far_atlas.json"
    meta = json.loads(meta_p.read_text(encoding="utf-8")) if meta_p.exists() else {}
    srcs = {}
    for mix in HAZE_MIXES:
        for f in (f"forest_edge_{mix}.png", f"forest_edge_{mix}_n.png"):
            if (vdir / f).exists():
                srcs[f] = hashlib.sha256((vdir / f).read_bytes()).hexdigest()
    want = {"schema": "truck-sim-pl/forest-edge-far-atlas/1", "adr": "0330", "haze_albedo_linear": list(HAZE_ALBEDO),
            "k": HAZE_SUFFIX_K, "slots": [list(x) for x in FAR_ATLAS_SLOTS], "size": list(FAR_ATLAS_SIZE),
            "pad": FAR_ATLAS_PAD, "sources": srcs}
    out_a, out_n = vdir / f"{FAR_ATLAS_MAT}.png", vdir / f"{FAR_ATLAS_MAT}_n.png"
    if meta == want and out_a.exists() and out_n.exists():
        return {"wrote": []}
    W, H = FAR_ATLAS_SIZE
    for dst, scale, normal in ((out_a, 1, False), (out_n, 2, True)):
        w, h = W // scale, H // scale
        atlas = np.zeros((h, w, 4), np.float64)
        if normal:
            atlas[..., :] = (0.5, 0.5, 1.0, 1.0)      # flat normal, full visibility in the pads
        for mix, suf in FAR_ATLAS_SLOTS:
            f = vdir / (f"forest_edge_{mix}_n.png" if normal else f"forest_edge_{mix}.png")
            if not f.exists():
                continue
            v0, v1 = far_atlas_slot_v(mix, suf)
            r0, r1 = int(round(v0 * h)), int(round(v1 * h))       # rows from the bottom
            im = Image.open(f).convert("RGBA").resize((w, r1 - r0), Image.LANCZOS)
            a = np.asarray(im, np.float64) / 255.0
            if not normal and suf:
                a = _haze(a, HAZE_SUFFIX_K[suf])
            atlas[h - r1:h - r0] = a                               # image rows run from the top
        Image.fromarray(np.clip(np.round(atlas * 255.0), 0, 255).astype(np.uint8), "RGBA").save(dst, optimize=True)
    meta_p.write_text(json.dumps(want, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    log("forest edge far atlas", [out_a.name, out_n.name])
    return {"wrote": [out_a.name, out_n.name]}


def materials():
    out = {}
    for mix in ("conifer", "mixed", "broadleaf"):
        out[f"forest_edge_{mix}"] = {"color": [1, 1, 1], "rough": 0.95, "alpha_cutoff": 0.5, "hlod": True,
                                     "texture_ref": TEX_REF.format(f"forest_edge_{mix}"),
                                     "normal_ref": TEX_REF.format(f"forest_edge_{mix}_n")}
        out[f"forest_canopy_{mix}"] = {"color": [1, 1, 1], "rough": 0.95, "hlod": True,
                                       "texture_ref": TEX_REF.format(f"forest_canopy_{mix}")}
    out[FAR_ATLAS_MAT] = {"color": [1, 1, 1], "rough": 0.95, "alpha_cutoff": 0.5, "hlod": True,
                          "texture_ref": TEX_REF.format(FAR_ATLAS_MAT), "normal_ref": TEX_REF.format(f"{FAR_ATLAS_MAT}_n")}
    return out


def bake_info():
    p = pipeline.REPO / "art-source" / "world" / "vegetation" / "trees_meta.json"
    fh = json.loads(p.read_text(encoding="utf-8")).get("forest_hlod") if p.exists() else None
    if not fh:     # tree library built before v3.1: defaults of make_trees.py
        fh = {m: {"edge": {"w_m": 48.0, "h_m": 24.0, "z0_m": -0.3, "h_median_m": 15.0}, "canopy": {"w_m": 48.0}}
              for m in ("conifer", "mixed", "broadleaf")}
    return fh


def edge_v_main(edge_info):
    """v of the top of the main wall picture in forest_edge_<mix>.png (1.0 before ADR 0187: no mantle strip)."""
    return float(edge_info.get("v_main", 1.0))


def cell_of(e, n, half):
    """Cell index, clipped to the tile like build_world.chunk_of (edge-band trees just outside the tile)."""
    k = int(2 * half // CELL_M) - 1
    return (min(max(int(math.floor((e + half) / CELL_M)), 0), k),
            min(max(int(math.floor((half - n) / CELL_M)), 0), k))


def cell_box(ci, cj, half):
    e0 = -half + ci * CELL_M
    n1 = half - cj * CELL_M
    return box(e0, n1 - CELL_M, e0 + CELL_M, n1)


def build(trees, forests, no_forest, zground, half, report, chm=None):
    """trees: instance dicts (forest trees carry "fk": mix); forests: [(polygon, mix)];
    no_forest: geometry where no stand can be (roads, yards, buildings + clearance); zground(e, n) -> ground z.
    Returns {cell id: {"chunk": (ci, cj), "bbox": [e0, n0, e1, n1], "prims": [...], "tris": int, "trees": int}}
    and tags the trees of every HLOD cell with "fc". chm (ADR 0339): streetscape.forest_chm.Chm or None."""
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
    # ADR 0187: "stand trees" by role, not by height (a low stand - young wood, allotment gardens - has canopy trees
    # under 8 m; with the height test its cells fell back to ground + 10 m)
    from .vegetation import CANOPY_SPECIES
    tall = np.array([t["p"][5:] in CANOPY_SPECIES and not str(t.get("src", "")).endswith((":edge", ":under", ":floor"))
                     and (t["h"] >= 8.0 or str(t.get("src", "")).startswith("override:")) for t in ft])
    if not tall.any():
        tall = np.array([t["h"] >= 8.0 for t in ft])
    if not tall.any():
        report["forest_hlod"] = {"cells": 0}
        return {}
    Pc = P[tall]
    top = np.array([t["z"] + t["h"] for t in ft])[tall]
    H = np.array([t["h"] for t in ft])[tall]
    kd = cKDTree(Pc)

    def canopy_z(Q):
        Q = np.asarray(Q, float).reshape(-1, 2)
        out = np.empty(len(Q))
        measured = np.zeros(len(Q), bool)
        if chm is not None and len(Q):
            dom, _, _, ins = chm.sample(Q)
            measured = ins & (dom >= CHM_TRUST_M)
            out[measured] = np.asarray(zground(Q[measured, 0], Q[measured, 1]), float) + CHM_CANOPY_K * dom[measured]
        for k, q in enumerate(Q):
            if measured[k]:
                continue
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

    def wall_h(q, edge_info, mix, measured_only=False):
        """Height of the wall quad at q: the trees of the edge picture stand as high as the stand does there."""
        if chm is not None:                 # ADR 0339: the measured crown tops at the wall, else the stand behind it
            dom, stand, _, ins = chm.sample(q)
            if ins[0] and max(dom[0], stand[0]) >= CHM_TRUST_M:
                return float(dom[0] if dom[0] >= CHM_TRUST_M else stand[0]) / CHM_WALL_TOP_FRAC.get(mix, 0.83)
            if measured_only:
                return None
            # no crowns measured here (a small hole, a cell outside the mask of the model): the generated trees
            # around the point in the same scale, and a low wall where none stands within 15 m (the class formula
            # below takes the median of the whole tile there - a 40 m spike in a gap)
            dd, ii = kd.query(np.asarray(q, float).reshape(2), k=12, distance_upper_bound=15.0)
            ii = ii[np.isfinite(dd)]
            return (float(np.percentile(H[ii], 90)) if len(ii) else CHM_TRUST_M) / CHM_WALL_TOP_FRAC.get(mix, 0.83)
        return None if measured_only else edge_info["h_m"] * h_local(q) / edge_info["h_median_m"]

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
        # ADR 0324: the canopy surface rolls off at a real stand edge (not at a cell border: the neighbour cell
        # continues it) - a cell seen from the side or from above was a box with a flat lid and vertical faces
        outer_b = piece.boundary.difference(cb.exterior.buffer(0.1))
        if not outer_b.is_empty:
            d_edge = shapely.distance(shapely.points(XY), outer_b)
            near = d_edge < CANOPY_EDGE_M
            if near.any():
                zg_c = np.asarray(zground(XY[near, 0], XY[near, 1]), float)
                k_ = np.array([CANOPY_EDGE_DROP[0] + (CANOPY_EDGE_DROP[1] - CANOPY_EDGE_DROP[0])
                               * _vnoise2(q_[0], q_[1], TOP_NOISE_M, "c") for q_ in XY[near]])
                k_ = 1.0 - (1.0 - k_) * (1.0 - d_edge[near] / CANOPY_EDGE_M)
                Z[near] = zg_c + (Z[near] - zg_c) * k_
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
            hw = np.array([wall_h(p, edge_info, mix) for p in pts])
            tv = CHM_TOP_VAR if chm is not None else TOP_VAR
            hw *= np.array([tv[0] + (tv[1] - tv[0]) * _vnoise2(p[0], p[1], TOP_NOISE_M) for p in pts])
            # ADR 0187: where the outer stand edge turns sharply (end of a belt, corner of a block) the wall steps
            # down, so a stand seen end-on does not finish in a full-height vertical cut ("theatre flat")
            if nseg >= 2:
                dv = np.diff(pts, axis=0)
                dv /= np.maximum(np.hypot(dv[:, 0], dv[:, 1]), 1e-9)[:, None]
                closed = float(np.hypot(*(pts[0] - pts[-1]))) < 1e-6
                for p in range(len(pts)):
                    a_, b_ = p - 1, p
                    if p == 0 or p == len(pts) - 1:
                        if not closed:
                            continue
                        a_, b_ = nseg - 1, 0
                    if inner[a_] or inner[b_]:
                        continue
                    if float(dv[a_] @ dv[b_]) < CORNER_COS:
                        for q, k_ in ((p, CORNER_DROP), (p - 1, 0.5 + 0.5 * CORNER_DROP), (p + 1, 0.5 + 0.5 * CORNER_DROP),
                                      (p - 2, 0.2 + 0.8 * CORNER_DROP + 0.12), (p + 2, 0.2 + 0.8 * CORNER_DROP + 0.12)):
                            if 0 <= q < len(pts):
                                hw[q] = min(hw[q], k_ * wall_h(pts[q], edge_info, mix))
                if closed:
                    hw[-1] = hw[0] = min(hw[0], hw[-1])

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
                vm = edge_v_main(edge_info)
                UVw += [[u, 0.0] for u in us] + [[u, vm * (t - zg[p]) / hw[p]] for u, p, t in zip(us, idx, wtop)]
                Nw += list(n3) + list(n3)
                for m_ in range(k - 1):
                    b0, b1, t0, t1 = base + m_, base + m_ + 1, base + k + m_, base + k + m_ + 1
                    if face[i] > 0:
                        Tw += [[b0, b1, t1], [b0, t1, t0]]
                    else:
                        Tw += [[b0, t1, b1], [b0, t0, t1]]
                if not inner[i] and k >= 2:
                    # ADR 0324: back wall (see BACK_OFF_M)
                    qb = pts[idx] - nrm * BACK_OFF_M
                    zb_ = zground(qb[:, 0], qb[:, 1]) + edge_info["z0_m"]
                    hb_ = hw[idx] * np.array([BACK_H[0] + (BACK_H[1] - BACK_H[0]) * _vnoise2(a[0], a[1], TOP_NOISE_M * 0.6, "b")
                                              for a in qb])
                    if chm is not None:     # ADR 0339: the back wall has the measured tops of its own line
                        for kb, a in enumerate(qb):
                            hm = wall_h(a, edge_info, mix, measured_only=True)
                            if hm is not None:
                                hb_[kb] = min(hm * (CHM_BACK_VAR[0] + (CHM_BACK_VAR[1] - CHM_BACK_VAR[0])
                                                    * _vnoise2(a[0], a[1], TOP_NOISE_M * 0.6, "b")),
                                              max(hw[idx[kb]] * BACK_H[1], hm * CHM_BACK_VAR[0]))
                    base = len(Vw)
                    Vw += [[a[0], a[1], z_] for a, z_ in zip(qb, zb_)] + [[a[0], a[1], z_ + h_] for a, z_, h_ in zip(qb, zb_, hb_)]
                    usb = us + 0.53
                    UVw += [[u, 0.0] for u in usb] + [[u, vm] for u in usb]
                    Nw += list(n3) + list(n3)
                    for m_ in range(k - 1):
                        b0, b1, t0, t1 = base + m_, base + m_ + 1, base + k + m_, base + k + m_ + 1
                        if face[i] > 0:
                            Tw += [[b0, b1, t1], [b0, t1, t0]]
                        else:
                            Tw += [[b0, t1, b1], [b0, t0, t1]]
                mantle = edge_info.get("mantle")
                if mantle and not inner[i]:
                    # skirt: the strip moved SKIRT_OFF_M out of the stand on ~18% of segments, mantle height scaled like the wall
                    q = pts[idx] + nrm * SKIRT_OFF_M
                    zq = zground(q[:, 0], q[:, 1]) + edge_info["z0_m"]
                    hq = mantle["h_m"] * np.clip(hw[idx] / edge_info["h_m"], 0.5, 1.15)
                    hq = hq * np.array([SKIRT_H_VAR[0] + (SKIRT_H_VAR[1] - SKIRT_H_VAR[0]) * _vnoise2(a[0], a[1], 9.0, "s")
                                        for a in q])
                    base = len(Vw)
                    Vw += [[a[0], a[1], z_] for a, z_ in zip(q, zq)] + [[a[0], a[1], z_ + h_] for a, z_, h_ in zip(q, zq, hq)]
                    us2 = us + 0.37
                    UVw += [[u, 1.0] for u in us2] + [[u, vm] for u in us2]
                    Nw += list(n3) + list(n3)
                    for m_ in range(k - 1):
                        if not _skirt_keep(pts[idx[m_]], pts[idx[m_ + 1]]):
                            continue
                        b0, b1, t0, t1 = base + m_, base + m_ + 1, base + k + m_, base + k + m_ + 1
                        if face[i] > 0:
                            Tw += [[b0, b1, t1], [b0, t1, t0]]
                        else:
                            Tw += [[b0, t1, b1], [b0, t0, t1]]
                i = j + 1
        if chm is not None:                 # ADR 0339: ribs (see RIB_M)
            ce0, cn0, ce1, cn1 = cb.bounds
            vm = edge_v_main(edge_info)
            for axis in (0, 1):
                lo, hi = (ce0, ce1) if axis == 0 else (cn0, cn1)
                for c0 in np.arange(math.floor(lo / RIB_M) * RIB_M + RIB_M, hi - 1e-6, RIB_M):
                    if c0 - lo < 1e-6:
                        continue                          # the cell border has its own (inner) wall
                    ln = (shapely.LineString([(c0, cn0), (c0, cn1)]) if axis == 0
                          else shapely.LineString([(ce0, c0), (ce1, c0)]))
                    inter = shapely.intersection(piece, ln)
                    for seg in getattr(inter, "geoms", [inter]):
                        if seg.geom_type != "LineString" or seg.length < RIB_MIN_LEN_M:
                            continue
                        k = max(1, int(math.ceil(seg.length / RIB_SEG_M)))
                        sc = np.asarray(seg.coords)
                        rp = sc[0][None, :] + (sc[-1] - sc[0])[None, :] * (np.arange(k + 1) / k)[:, None]
                        # the ribs meander (smooth noise of the absolute position): from a bridge or a hill straight
                        # lines every 16 m would read as a waffle of hedges
                        rp[:, axis] += np.array([(_vnoise2(q_[0], q_[1], RIB_WAVE_M, f"w{axis}") - 0.5) * 2.0 * RIB_WAVE_AMP_M
                                                 for q_ in rp])
                        hr_ = np.array([wall_h(q_, edge_info, mix, measured_only=True) or 0.0 for q_ in rp])
                        if hr_.max() <= 0.0:
                            continue
                        hr_ *= np.array([CHM_TOP_VAR[0] + (CHM_TOP_VAR[1] - CHM_TOP_VAR[0])
                                         * _vnoise2(q_[0], q_[1], TOP_NOISE_M, "r") for q_ in rp])
                        hr_ = np.maximum(hr_, 2.0)        # no crowns measured at this point: the rib runs out low
                        zr = zground(rp[:, 0], rp[:, 1]) + edge_info["z0_m"]
                        along = rp[:, 1 - axis]
                        us = along / Wt + (int(hashlib.sha1(f"rib:{axis}:{c0:.0f}".encode()).hexdigest()[:6], 16) % 997) / 997.0
                        base = len(Vw)
                        Vw += [[q_[0], q_[1], z_] for q_, z_ in zip(rp, zr)] + [[q_[0], q_[1], z_ + h_] for q_, z_, h_ in zip(rp, zr, hr_)]
                        UVw += [[u, 0.0] for u in us] + [[u, vm] for u in us]
                        Nw += [[0.0, 0.0, 1.0]] * (2 * (k + 1))
                        for m_ in range(k):
                            b0, b1, t0, t1 = base + m_, base + m_ + 1, base + k + 1 + m_, base + k + 2 + m_
                            Tw += [[b0, b1, t1], [b0, t1, t0]]
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
