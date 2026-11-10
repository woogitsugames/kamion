"""Vegetation placement (instances of our own procedural tree models, tools/blender/world/make_trees.py) and
terrain ground-cover masks.

Positions (GUGiK "Modele 3D drzew" are not ingested - 1.07 GB, optional - so BDOT10k + OSM are used):
  forests      BDOT10k OT_PTLZ_A: jittered grid (las 4.5 m, zagajnik 3.2 m, zadrzewienie 6 m); species mix by
               KATEGORIA (iglasty / mieszany / liściasty) for Podlasie stands: Scots pine, silver birch,
               black alder, Norway maple, small-leaved linden (WORKING_VALUE proportions).
  forest edge  shrubs + young birch/alder within 5 m inside and 3 m outside the forest outline.
  single trees BDOT10k OT_OIPR_P (drzewo lub grupa drzew -> 1-3 trees, kępa krzewów -> shrubs, mały las -> clump),
               OSM natural=tree; rows: BDOT10k OT_OIPR_L rząd drzew (8 m spacing, linden/maple).
  self-seeded  sparse birch/pine saplings and shrubs on unmown land (BDOT10k OT_PTNZ_A / OT_PTTR_A) > 6 m from roads.
Everything is kept >= 2.5 m from road surfaces, paved areas and buildings. Deterministic (seeded per polygon id).

Ground-cover masks per terrain node -> COLOR_0 of the terrain mesh:
  R = distance to the nearest road / paved edge (0..1 = 0..20 m)  (dirt and mown strip near kerbs)
  G = forest floor (inside OT_PTLZ_A)
  B = unmown / rough grass (1) vs mown verge and lawns (0)
  A = bare soil / industrial ground (OT_PTNZ_A, brownfield, construction)
"""

from __future__ import annotations

import hashlib

import numpy as np
import shapely
from scipy import ndimage
from shapely.geometry import Polygon

from . import paved as PV

SPECIES = ["pine", "birch", "alder", "maple", "linden", "shrub"]
MIX = {"iglasty": [0.82, 0.12, 0.02, 0.02, 0.02, 0.0], "mieszany": [0.45, 0.25, 0.10, 0.10, 0.10, 0.0],
       "liściasty": [0.08, 0.32, 0.25, 0.20, 0.15, 0.0], None: [0.4, 0.3, 0.1, 0.1, 0.1, 0.0]}
HEIGHT = {"pine": (14, 24), "birch": (9, 19), "alder": (9, 17), "maple": (8, 16), "linden": (9, 18), "shrub": (1.5, 4.0)}
SPACING = {"las": 4.5, "zagajnik": 3.2, "zadrzewienie": 6.0}
# Understorey of a Podlasie pine / mixed stand (v3.4, review r3 X4 "trunks like a fence", r4 W-H8): hazel and
# young pine / birch under the canopy, so the boles do not stand in an empty, swept hall. species -> (h min, h max,
# weight), one plant per UNDER_SPACING^2 (~60 m2). WORKING_VALUE (forest-inventory classes, not measured here);
# tools/blender/world/make_trees.py UNDER_SPECIES bakes the same mix into the HLOD edge texture.
UNDERSTOREY = {"shrub": (1.2, 3.5, 0.55), "pine": (3.0, 7.0, 0.2), "birch": (3.0, 7.5, 0.25)}
UNDER_SPACING = 7.75


def _seed(key):
    return int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)


def _scatter(poly, spacing, rng):
    x0, y0, x1, y1 = poly.bounds
    gx, gy = np.meshgrid(np.arange(x0, x1, spacing), np.arange(y0, y1, spacing))
    P = np.column_stack([gx.ravel(), gy.ravel()]) + rng.uniform(-spacing * 0.45, spacing * 0.45, (gx.size, 2))
    shapely.prepare(poly)
    return P[shapely.contains_xy(poly, P[:, 0], P[:, 1])] if len(P) else P


def place(src, origin, hf, zc, blocked, report):
    """blocked: bool grid (1 m nodes) of roads + paved + buildings (dilated). Returns instance list."""
    out = []
    H, W = zc.shape

    def ok(P):
        i = np.clip(np.rint(P[:, 0] - hf.x0).astype(int), 0, W - 1)
        j = np.clip(np.rint(hf.y1 - P[:, 1]).astype(int), 0, H - 1)
        return ~blocked[j, i], zc[j, i]

    def emit(P, species, rng, src_id, hscale=1.0, fk=None):
        if not len(P):
            return
        good, z = ok(P)
        for (x, y), zz, sp, g in zip(P, z, species, good):
            if not g:
                continue
            lo, hi = HEIGHT[sp]
            h = rng.uniform(lo, hi) * hscale
            out.append({"p": f"tree_{sp}", "v": int(rng.integers(0, 3)), "e": round(float(x), 2), "n": round(float(y), 2),
                        "z": round(float(zz), 2), "h": round(float(h), 1), "yaw": round(float(rng.uniform(0, 6.2832)), 3),
                        "lean": round(float(rng.uniform(0, 0.05)), 3), "src": src_id})
            if fk:
                out[-1]["fk"] = fk          # forest stand tree (texture mix of the forest HLOD, forest_hlod.py)

    def pick(rng, mix, n):
        return rng.choice(SPECIES, size=n, p=np.asarray(mix) / np.sum(mix))

    forests = []
    forest_mix = []
    for f in src["bdot10k"]["OT_PTLZ_A"]:
        poly = PV._poly_local(f["geometry"]["coordinates"], origin)
        if not poly.is_valid:
            poly = shapely.make_valid(poly)
        kat = f["props"].get("kategoria")
        fk = {"iglasty": "conifer", "liściasty": "broadleaf"}.get(kat, "mixed")
        forests.append(poly)
        forest_mix.append((poly, fk))
        rng = np.random.default_rng(_seed(f["id"]))
        rodzaj = f["props"].get("rodzaj", "las")
        P = _scatter(poly, SPACING.get(rodzaj, 4.5), rng)
        sp = pick(rng, MIX.get(kat, MIX[None]), len(P))
        emit(P, sp, rng, f"bdot:{f['id']}", 0.7 if rodzaj == "zagajnik" else 1.0, fk=fk)
        if rodzaj == "las":
            P = _scatter(poly.buffer(-2.0), UNDER_SPACING, rng)
            names = list(UNDERSTOREY)
            w = np.array([UNDERSTOREY[k][2] for k in names])
            sp = rng.choice(names, size=len(P), p=w / w.sum())
            n0 = len(out)
            emit(P, sp, rng, f"bdot:{f['id']}:under", 1.0, fk=fk)
            for t in out[n0:]:
                lo, hi = UNDERSTOREY[t["p"][5:]][:2]
                t["h"] = round(float(lo + (hi - lo) * ((_seed(f"{t['e']},{t['n']}") % 1000) / 999.0)), 1)
        # edge: shrubs + young deciduous along the outline
        edge = poly.buffer(3.0).difference(poly.buffer(-5.0))
        P = _scatter(edge, 3.0, rng)
        sp = pick(rng, [0.0, 0.25, 0.15, 0.05, 0.0, 0.55], len(P))
        emit(P, sp, rng, f"bdot:{f['id']}:edge", 0.6, fk=fk)
    for f in src["bdot10k"]["OT_PTRK_A"]:
        poly = PV._poly_local(f["geometry"]["coordinates"], origin)
        rng = np.random.default_rng(_seed(f["id"]))
        P = _scatter(poly, 2.5, rng)
        emit(P, ["shrub"] * len(P), rng, f"bdot:{f['id']}")
    for f in src["bdot10k"]["OT_OIPR_P"]:
        q = np.asarray(f["geometry"]["coordinates"], float) - origin
        rng = np.random.default_rng(_seed(f["id"]))
        r = f["props"].get("rodzaj")
        if r == "kępa krzewów lub kosodrzewiny":
            P = q + rng.normal(0, 1.5, (5, 2))
            emit(P, ["shrub"] * 5, rng, f"bdot:{f['id']}")
        elif r == "mały las":
            P = q + rng.normal(0, 6.0, (10, 2))
            emit(P, pick(rng, MIX[None], 10), rng, f"bdot:{f['id']}")
        else:
            k = int(rng.integers(1, 4))
            P = q + rng.normal(0, 2.5, (k, 2)) * (k > 1)
            emit(P, pick(rng, [0.05, 0.3, 0.05, 0.3, 0.3, 0.0], k), rng, f"bdot:{f['id']}")
    for f in src["bdot10k"]["OT_OIPR_L"]:
        if f["props"].get("rodzaj") != "rząd drzew":
            continue
        line = shapely.LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        rng = np.random.default_rng(_seed(f["id"]))
        P = np.array([line.interpolate(s).coords[0] for s in np.arange(2.0, line.length, 8.0)]).reshape(-1, 2)
        sp = [["linden", "maple"][_seed(f["id"]) % 2]] * len(P)
        emit(P + rng.normal(0, 0.3, P.shape), sp, rng, f"bdot:{f['id']}")
    for nd in src["osm"]["nodes"]:
        if nd["tags"].get("natural") == "tree":
            q = np.asarray(nd["geometry"]["coordinates"], float)[None] - origin
            rng = np.random.default_rng(nd["osm_node"])
            emit(q, ["linden"], rng, f"osm:node/{nd['osm_node']}")
    # self-seeded vegetation on unmown land
    for layer in ("OT_PTNZ_A", "OT_PTTR_A"):
        for f in src["bdot10k"][layer]:
            poly = PV._poly_local(f["geometry"]["coordinates"], origin)
            rng = np.random.default_rng(_seed(f["id"]) + 7)
            P = _scatter(poly, 14.0, rng)
            P = P[rng.uniform(0, 1, len(P)) < 0.45]
            sp = pick(rng, [0.2, 0.35, 0.05, 0.05, 0.0, 0.35], len(P))
            emit(P, sp, rng, f"bdot:{f['id']}:self", 0.5)
    # thin out overlaps (< 1.8 m between trunks), deterministic order
    if out:
        P = np.array([[t["e"], t["n"]] for t in out])
        from scipy.spatial import cKDTree
        tree = cKDTree(P)
        keep = np.ones(len(P), bool)
        for i, j in sorted(tree.query_pairs(1.8)):
            if keep[i] and keep[j]:
                keep[j] = False
        out = [t for t, k in zip(out, keep) if k]
    cnt = {}
    for t in out:
        cnt[t["p"]] = cnt.get(t["p"], 0) + 1
    report["trees"] = cnt
    report["understorey"] = sum(1 for t in out if t["src"].endswith(":under"))
    report["_forest_mix"] = forest_mix
    return out, forests


def ground_masks(src, origin, hf, dist_road, forests):
    """(H, W, 4) float32 terrain vertex colours (see module doc)."""
    H, W = hf.z.shape
    R = np.clip(dist_road / 20.0, 0, 1)
    G = PV.rasterize_polys(forests, hf).astype(float)
    lawns = [PV._poly_local(a["geometry"]["coordinates"], origin) for a in src["osm"]["areas"]
             if a["tags"].get("landuse") == "grass" or a["tags"].get("leisure") in ("park", "playground", "pitch")]
    mown = PV.rasterize_polys(lawns, hf) | (dist_road < 4.0)
    B = (~mown).astype(float)
    bare_polys = [PV._poly_local(f["geometry"]["coordinates"], origin) for f in src["bdot10k"]["OT_PTNZ_A"]]
    bare_polys += [PV._poly_local(a["geometry"]["coordinates"], origin) for a in src["osm"]["areas"]
                   if a["tags"].get("landuse") in ("construction", "brownfield")]
    A = PV.rasterize_polys(bare_polys, hf).astype(float)
    C = np.stack([R, G, B, A], axis=-1)
    C = ndimage.gaussian_filter(C, sigma=(1.5, 1.5, 0))
    C[..., 0] = np.where(dist_road <= 0.0, 0.0, C[..., 0])      # exactly 0 under roads / yards (no grass there)
    return C.astype(np.float32)
