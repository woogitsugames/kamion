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


def forest_clearings(overrides, origin):
    """Authored `kind: forest_clearing` (ADR 0163): parts of a BDOT10k OT_PTLZ_A polygon that the GUGiK orthophoto
    shows cleared (sand, no trees). {bdot id: (cleared polygon, override id)}; `cleared_epsg2180` rings minus the
    `keep_epsg2180` rings (tree clumps left standing inside the clearing). Keyed by the BDOT id, so it survives
    every regeneration; a target missing from the source data is reported as stale."""
    out = {}
    o0 = np.asarray(origin, float)
    for o in overrides or []:
        if o.get("kind") != "forest_clearing":
            continue
        cut = shapely.union_all([shapely.make_valid(shapely.Polygon(np.asarray(r, float) - o0))
                                 for r in o["cleared_epsg2180"]])
        keep = [shapely.make_valid(shapely.Polygon(np.asarray(r, float) - o0)) for r in o.get("keep_epsg2180", [])]
        if keep:
            cut = cut.difference(shapely.union_all(keep))
        bid = str(o["target"]["bdot"])
        prev = out.get(bid)
        out[bid] = (cut if prev is None else prev[0].union(cut), o["id"])
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
        # ADR 0173: the attributes are drawn for EVERY candidate point (same calls, same order as before), and the
        # clearance test only drops the tree afterwards. Before, a tree dropped by a new kerb / paved area / building
        # skipped its draws and shifted the random stream of every later tree of the same BDOT feature or group
        # (trees changed far outside an edited spot). Features with no dropped candidate keep their exact stream.
        for (x, y), zz, sp, g in zip(P, z, species, good):
            lo, hi = HEIGHT[sp]
            h = rng.uniform(lo, hi) * hscale
            v = int(rng.integers(0, 3))
            yaw = float(rng.uniform(0, 6.2832))
            lean = float(rng.uniform(0, 0.05))
            if not g:
                continue
            out.append({"p": f"tree_{sp}", "v": v, "e": round(float(x), 2), "n": round(float(y), 2),
                        "z": round(float(zz), 2), "h": round(float(h), 1), "yaw": round(yaw, 3),
                        "lean": round(lean, 3), "src": src_id})
            if fk:
                out[-1]["fk"] = fk          # forest stand tree (texture mix of the forest HLOD, forest_hlod.py)

    def pick(rng, mix, n):
        return rng.choice(SPECIES, size=n, p=np.asarray(mix) / np.sum(mix))

    forests = []
    forest_mix = []
    clear = forest_clearings(overrides, origin)
    crep = {"applied": [], "stale": []}
    hit = set()
    cleared = []                            # cleared parts of the forest: sand on the orthophoto -> bare ground mask
    for f in src["bdot10k"]["OT_PTLZ_A"]:
        poly = PV._poly_local(f["geometry"]["coordinates"], origin)
        if not poly.is_valid:
            poly = shapely.make_valid(poly)
        full = poly                         # trees are generated on the BDOT outline and the cleared ones dropped
        cut = None                          # afterwards: the stand left standing keeps every tree (same seed stream)
        ck = f["id"] if f["id"] in clear else str(f["id"]).split(":")[0]     # BDOT id without the ":<part>" index
        if ck in clear:
            cut, oid = clear[ck]
            hit.add(ck)
            cleared.append(shapely.make_valid(full.intersection(cut)))
            poly = shapely.make_valid(full.difference(cut))
            crep["applied"].append({"id": oid, "bdot": f["id"], "area_m2_before": round(full.area, 1),
                                    "area_m2_after": round(poly.area, 1)})
        n_stand = len(out)
        kat = f["props"].get("kategoria")
        fk = {"iglasty": "conifer", "liściasty": "broadleaf"}.get(kat, "mixed")
        forests.append(poly)
        forest_mix.append((poly, fk))
        rng = np.random.default_rng(_seed(f["id"]))
        rodzaj = f["props"].get("rodzaj", "las")
        P = _scatter(full, SPACING.get(rodzaj, 4.5), rng)
        sp = pick(rng, MIX.get(kat, MIX[None]), len(P))
        emit(P, sp, rng, f"bdot:{f['id']}", 0.7 if rodzaj == "zagajnik" else 1.0, fk=fk)
        if rodzaj == "las":
            P = _scatter(full.buffer(-2.0), UNDER_SPACING, rng)
            names = list(UNDERSTOREY)
            w = np.array([UNDERSTOREY[k][2] for k in names])
            sp = rng.choice(names, size=len(P), p=w / w.sum())
            n0 = len(out)
            emit(P, sp, rng, f"bdot:{f['id']}:under", 1.0, fk=fk)
            for t in out[n0:]:
                lo, hi = UNDERSTOREY[t["p"][5:]][:2]
                t["h"] = round(float(lo + (hi - lo) * ((_seed(f"{t['e']},{t['n']}") % 1000) / 999.0)), 1)
        # edge: shrubs + young deciduous along the outline
        edge = full.buffer(3.0).difference(full.buffer(-5.0))
        P = _scatter(edge, 3.0, rng)
        sp = pick(rng, [0.0, 0.25, 0.15, 0.05, 0.0, 0.55], len(P))
        emit(P, sp, rng, f"bdot:{f['id']}:edge", 0.6, fk=fk)
        if cut is not None and len(out) > n_stand:
            Q = np.array([[t["e"], t["n"]] for t in out[n_stand:]])
            gone = shapely.contains_xy(cut, Q[:, 0], Q[:, 1])
            crep["applied"][-1]["trees_removed"] = int(gone.sum())
            out[n_stand:] = [t for t, g in zip(out[n_stand:], gone) if not g]
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
    crep["stale"] = [{"id": oid, "bdot": bid} for bid, (_, oid) in clear.items() if bid not in hit]
    report["forest_clearings"] = crep
    report["_forest_cleared"] = cleared
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


def ground_masks(src, origin, hf, dist_road, forests, cleared=()):
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
    bare_polys += list(cleared)             # authored forest clearings (ADR 0163): sand on the orthophoto
    A = PV.rasterize_polys(bare_polys, hf).astype(float)
    A *= .40 + .60 * metric_patch_field(east, north, 3.5, 882)
    C = np.stack([R, G, B, A], axis=-1)
    C = ndimage.gaussian_filter(C, sigma=(1.5, 1.5, 0))
    C[..., 0] = np.where(dist_road <= 0.0, 0.0, C[..., 0])      # exactly 0 under roads / yards (no grass there)
    return C.astype(np.float32)


# ADR 0163 (corrects ADR 0154): ceilings of mature city trees, G7 # 12 (Ebben S01-S07, measurement G7-T03). ADR 0154
# used birch 23 m and raised / widened the garden crowns of the tree library (x 1.2-1.35, up to 20.4 m): on their
# sparse stems they read as stone pines (review 2026-11-13). The broadleaf garden trees of a region with an
# orthophoto canopy are kit trees now (streetscape.plantings.garden_trees); what is left here are the rule-placed
# instances of regions without one.
MATURE_H_M = {"birch": 20.0, "linden": 24.0, "maple": 22.0, "pine": 24.0}


def garden_canopies(trees, rp, report, parts=()):
    """Garden trees that are still instances of the tree library (rule path, `tier: high`): the height is capped at
    the species ceiling of G7 # 12; nothing is widened, raised, moved or added. Other records pass through."""
    lookup = {f"plot:{p['id']}" for p in rp.get("plots", [])}
    rows, result = [], []
    for tree in trees:
        species = str(tree.get("p", "")).removeprefix("tree_")
        if tree.get("tier") != "high" or tree.get("src", "").rsplit(":", 1)[0] not in lookup or species not in MATURE_H_M:
            result.append(tree)
            continue
        changed = dict(tree)
        changed["h"] = round(min(float(tree["h"]), MATURE_H_M[species]), 1)
        result.append(changed)
        if changed["h"] != tree["h"]:
            rows.append({"src": tree["src"], "species": species, "height_before_m": tree["h"], "height_after_m": changed["h"]})
    report["garden_canopies"] = {"source": "G7 # 12 ceilings (research/g7-street-greenery/README.md)", "instances": len(result),
                                 "capped": len(rows), "added_instances": 0, "widened": 0, "list": rows}
    return result
