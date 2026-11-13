"""Vegetation placement (instances of our own procedural tree models, tools/blender/world/make_trees.py) and
terrain ground-cover masks.

Positions (GUGiK "Modele 3D drzew" are not ingested - 1.07 GB, optional - so BDOT10k + OSM are used):
  forests      BDOT10k OT_PTLZ_A: jittered grid (las 4.5 m, zagajnik 3.2 m, zadrzewienie 6 m); species mix by
               KATEGORIA (iglasty / mieszany / liściasty) for Podlasie stands: Scots pine, silver birch,
               black alder, Norway maple, small-leaved linden (WORKING_VALUE proportions).
  forest edge  shrubs + young birch/alder within 5 m inside and 3 m outside the forest outline.
  single trees BDOT10k OT_OIPR_P (drzewo lub grupa drzew -> 1-3 trees, kępa krzewów -> shrubs, mały las -> clump),
               OSM natural=tree; rows: BDOT10k OT_OIPR_L rząd drzew (8 m spacing, linden/maple).
  tree groups  authored `kind: tree_groups` lines (ADR 0069, Mapillary): clumps of 3-7 trees with open gaps; BDOT
               rows near such a line are laid out as clumps too.
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

from . import paved as PV
from .foliage_policy import metric_patch_field, osm_tree_species

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


# Roadside tree groups (ADR 0069, Mapillary p26 / p30 / p55: lindens / pines / birches stand in clumps of 3-7 with
# open verge between, not in an even row). Defaults of the authored `kind: tree_groups` override; WORKING_VALUE read
# off the photos (group length ~10-25 m, gaps ~15-40 m).
TREE_GROUP_DEFAULTS = {"group_size": [3, 7], "in_group_m": [3.0, 5.5], "gap_m": [15.0, 40.0], "depth_m": 3.0,
                       "rows_replace_m": 12.0, "species": {"linden": 0.5, "pine": 0.2, "birch": 0.2, "maple": 0.1}}


def group_positions(line, rng, prm):
    """Clumps along `line` (shapely LineString): n trees (group_size) spaced in_group_m along the line with lateral
    scatter +-depth_m / 2, then an open gap (gap_m). Starts with a random part of a gap so neighbouring lines do not
    start in phase. Returns (positions [k, 2], group index per tree)."""
    L = line.length
    s = float(rng.uniform(0, prm["gap_m"][1] * 0.5))
    P, G, g = [], [], 0
    while s < L:
        n = int(rng.integers(prm["group_size"][0], prm["group_size"][1] + 1))
        for _ in range(n):
            if s >= L:
                break
            x, y = line.interpolate(s).coords[0]
            p1 = np.array(line.interpolate(min(L, s + 0.5)).coords[0]) - np.array(line.interpolate(max(0, s - 0.5)).coords[0])
            nrm = np.array([-p1[1], p1[0]]) / max(np.hypot(*p1), 1e-9)
            P.append(np.array([x, y]) + nrm * rng.uniform(-prm["depth_m"] / 2, prm["depth_m"] / 2))
            G.append(g)
            s += float(rng.uniform(*prm["in_group_m"]))
        s += float(rng.uniform(*prm["gap_m"]))
        g += 1
    return (np.array(P).reshape(-1, 2), np.array(G, int))


def _tree_group_overrides(overrides, origin):
    out = []
    for o in overrides or []:
        if o.get("kind") != "tree_groups":
            continue
        prm = {**TREE_GROUP_DEFAULTS, **{k: v for k, v in o.items() if k in TREE_GROUP_DEFAULTS}}
        for k, ln in enumerate(o["lines"]):
            out.append((shapely.LineString(np.asarray(ln["line_epsg2180"], float) - origin), prm, f"override:{o['id']}:{k}"))
    return out


def place(src, origin, hf, zc, blocked, report, overrides=None):
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
    groups = _tree_group_overrides(overrides, np.asarray(origin, float))
    grep = {"lines": len(groups), "trees": 0, "groups": 0, "rows_grouped": 0}
    for f in src["bdot10k"]["OT_OIPR_L"]:
        if f["props"].get("rodzaj") != "rząd drzew":
            continue
        line = shapely.LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        rng = np.random.default_rng(_seed(f["id"]))
        near = next((prm for gl, prm, _ in groups if line.distance(gl) <= prm["rows_replace_m"]), None)
        if near is not None:                    # the photos show clumps here, not the BDOT row (ADR 0069)
            P, _ = group_positions(line, rng, near)
            names = list(near["species"])
            w = np.array([near["species"][k] for k in names], float)
            emit(P, rng.choice(names, size=len(P), p=w / w.sum()), rng, f"bdot:{f['id']}:groups")
            grep["rows_grouped"] += 1
            continue
        P = np.array([line.interpolate(s).coords[0] for s in np.arange(2.0, line.length, 8.0)]).reshape(-1, 2)
        sp = [["linden", "maple"][_seed(f["id"]) % 2]] * len(P)
        emit(P + rng.normal(0, 0.3, P.shape), sp, rng, f"bdot:{f['id']}")
    for gl, prm, key in groups:
        rng = np.random.default_rng(_seed(key))
        P, G = group_positions(gl, rng, prm)
        names = list(prm["species"])
        w = np.array([prm["species"][k] for k in names], float)
        # one species per clump (a clump of lindens, a clump of pines), as on the photos
        gsp = rng.choice(names, size=int(G.max()) + 1 if len(G) else 0, p=w / w.sum())
        n0 = len(out)
        emit(P, [gsp[g] for g in G], rng, key)
        grep["trees"] += len(out) - n0
        grep["groups"] += int(G.max()) + 1 if len(G) else 0
    report["tree_groups"] = grep
    for nd in src["osm"]["nodes"]:
        if nd["tags"].get("natural") == "tree":
            q = np.asarray(nd["geometry"]["coordinates"], float)[None] - origin
            rng = np.random.default_rng(nd["osm_node"])
            emit(q, [osm_tree_species(nd["tags"])], rng, f"osm:node/{nd['osm_node']}")
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
    mapped_lawn = PV.rasterize_polys(lawns, hf)
    east = hf.x0 + np.arange(W)
    north = hf.y1 - np.arange(H)
    # ADR0109 r1: road proximity is not evidence of a uniformly maintained lawn.
    # Keep the mapped lawns quieter, but let the verges retain metre-scale
    # patches of green regrowth and straw. The secondary field breaks the large
    # cell shape without leaf-sized procedural noise. All values WORKING_VALUE,
    # not surveyed moisture, salt damage or pedestrian paths.
    large = metric_patch_field(east, north, 8.0, 881)
    small = metric_patch_field(east, north, 2.5, 883)
    dry = np.clip((.8 * large + .2 * small - .5) * 2.4 + .5, 0, 1)
    B = np.where(mapped_lawn, .06 + dry * .40,
                 np.where(dist_road < 4.0, .08 + dry * .84, .25 + dry * .75))
    bare_polys = [PV._poly_local(f["geometry"]["coordinates"], origin) for f in src["bdot10k"]["OT_PTNZ_A"]]
    bare_polys += [PV._poly_local(a["geometry"]["coordinates"], origin) for a in src["osm"]["areas"]
                   if a["tags"].get("landuse") in ("construction", "brownfield")]
    A = PV.rasterize_polys(bare_polys, hf).astype(float)
    A *= .40 + .60 * metric_patch_field(east, north, 3.5, 882)
    C = np.stack([R, G, B, A], axis=-1)
    C = ndimage.gaussian_filter(C, sigma=(1.5, 1.5, 0))
    C[..., 0] = np.where(dist_road <= 0.0, 0.0, C[..., 0])      # exactly 0 under roads / yards (no grass there)
    return C.astype(np.float32)


# ADR 0154: the plot implementation is read-only; use its existing species ranges.
from . import plots as PLT


def garden_canopies(trees, rp, report):
    """ADR0154: broader existing High garden crowns, no added instances.

    Width multipliers are WORKING_VALUE from typology P07/P08/P12:
    maple/linden1.35, birch1.20, pine unchanged. Tree positions/radii source
    remains the original orthophoto extraction; species are existing rules.
    """
    lookup={f"plot:{p['id']}":p for p in rp.get('plots',[])}
    widths={'tree_maple':1.35,'tree_linden':1.35,'tree_birch':1.20}
    rows=[];result=[]
    for tree in trees:
        plot=lookup.get(tree.get('src','').rsplit(':',1)[0])
        width=widths.get(tree.get('p'))
        if tree.get('tier')!='high' or plot is None or width is None:
            result.append(tree);continue
        changed=dict(tree);changed['garden_canopy_width']=width
        species=tree['p'].removeprefix('tree_')
        # Height relation is a working typology, not an ortho height measurement.
        required=float(plot.get('house_h') or 6.)+3.5
        changed['h']=round(min(PLT.INST_H_M[species][1],max(float(tree['h']),required)),1)
        result.append(changed)
        rows.append({'src':tree['src'],'species':species,'height_before_m':tree['h'],'height_after_m':changed['h'],'width_multiplier':width,'position':[tree['e'],tree['n']]})
    report['garden_canopies']={'source':'WORKING_VALUE width/height; P07/P08/P12 typology; original ortho positions retained','modified':len(rows),'added_instances':0,'high_only':True,'list':rows}
    return result
