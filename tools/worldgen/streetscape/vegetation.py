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

# ADR 0187: "spruce" (Norway spruce) joins the canopy species. Pine / spruce stands (bor mieszany swiezy) are the
# stands of Puszcza Knyszynska and of the forests south of Krywlany; shares WORKING_VALUE (pine clearly dominant,
# spruce the second conifer; not read from a forest inventory). make_trees.py FOREST_MIX bakes the same mixes.
SPECIES = ["pine", "birch", "alder", "maple", "linden", "shrub", "spruce"]
MIX = {"iglasty": [0.64, 0.10, 0.02, 0.02, 0.02, 0.0, 0.20], "mieszany": [0.36, 0.24, 0.10, 0.08, 0.08, 0.0, 0.14],
       # ADR 0170: no Scots pine in "liściasty" stands. The 8 % pines of 14-24 m stood above every broadleaf stand
       # as flat "stone pine" crowns (review s17 0163 P1 / P2); same weights in make_trees.py FOREST_MIX (HLOD bake).
       "liściasty": [0.0, 0.36, 0.26, 0.22, 0.16, 0.0, 0.0], None: [0.4, 0.3, 0.1, 0.1, 0.1, 0.0, 0.0]}
HEIGHT = {"pine": (14, 24), "birch": (9, 19), "alder": (9, 17), "maple": (8, 16), "linden": (9, 18), "shrub": (1.5, 4.0),
          "spruce": (14, 25), "pineyoung": (1.5, 5.0), "birchyoung": (2.0, 6.5), "floor": (0.45, 0.9),
          "poplar": (18, 28)}      # ADR 0308: roadside poplar (tree_rows / overrides only; WORKING_VALUE)
# Prototype variants per species (make_trees.py NVAR; 3 when not listed). The variant is drawn from 0..2 for every
# tree (unchanged random stream) and folded: spruce canopy trees take the stand forms 0 / 1, young spruce and the
# open side of a stand take variant 2 (boughs to the ground).
NVAR = {"pineyoung": 1, "birchyoung": 1, "floor": 2, "poplar": 2}
SPRUCE_OPEN = 2
SPACING = {"las": 4.5, "zagajnik": 3.2, "zadrzewienie": 6.0}
# Understorey of a Podlasie pine / mixed stand (v3.4, review r3 X4 "trunks like a fence", r4 W-H8): hazel and
# young pine / birch under the canopy, so the boles do not stand in an empty, swept hall. species -> (h min, h max,
# weight), one plant per UNDER_SPACING^2 (~60 m2). WORKING_VALUE (forest-inventory classes, not measured here);
# tools/blender/world/make_trees.py UNDER_SPECIES bakes the same mix into the HLOD edge texture.
# ADR 0187: the young trees are their own prototypes (a mature pine scaled to 5 m was a bare pole with a tuft: the
# "trunks with detached balls of leaves" of review s19 0179), spruce regeneration under the pines is the commonest
# second storey of these stands, and the storey is twice as dense (one plant per ~30 m2).
UNDERSTOREY = {"shrub": (1.2, 3.5, 0.55), "birchyoung": (2.5, 7.0, 0.20), "spruce": (1.5, 8.0, 0.15),
               "maple": (1.5, 5.0, 0.10)}
UNDER_SPACING = 5.5
CANOPY_SPECIES = ("pine", "birch", "alder", "maple", "linden", "spruce")
# Stand edge (mantle): three bands with rising height instead of one row, so a stand does not end in a vertical cut
# of bare boles (review s19 0179 "like a theatre flat"). (band inner offset, outer offset [m, + = outside the BDOT
# outline], grid step, {species: (weight, h lo, h hi)}); "canopy" = the stand's own mix at 0.55-0.8 of its height.
# M68 measurement (REVIEW-2026-11-14-s20-cloud-m68.md): outer shrub belt 3.0-5.0 m appears on ~15-20% of edges,
# inner young-tree belt on ~50-65%, leaving pine trunks + understorey visible in the lower 1/4-1/3 elsewhere.
# ADR 0324 (critic s24 wave 6 # 4.3 / top-5 # 4 "skraj lasu z podszytem"): shrub belt on ~40 % and young-tree belt on
# ~75 % of the outline (M68 had 0.18 / 0.58 - most of a stand edge was bare boles behind a ruler line). WORKING_VALUE.
MANTLE_BAND_KEEP = (0.40, 0.75, 1.0)
MANTLE_SEG_M = 18.0
MANTLE = {
    "conifer": [(0.0, 4.0, 2.6, {"shrub": (0.55, 3.0, 5.0), "birchyoung": (0.20, 3.0, 5.0), "pineyoung": (0.25, 3.0, 5.0)}),
                (-5.0, 0.0, 2.8, {"birchyoung": (0.30, 3.0, 7.0), "pineyoung": (0.28, 2.5, 6.0), "spruce": (0.24, 3.0, 9.0),
                                  "shrub": (0.18, 2.0, 3.8)}),
                (-11.0, -5.0, 4.6, {"spruce": (0.45, 8.0, 15.0), "birch": (0.35, 8.0, 13.0), "pine": (0.20, 9.0, 14.0)})],
    "broadleaf": [(0.0, 4.0, 2.6, {"shrub": (0.70, 3.0, 5.0), "birchyoung": (0.30, 3.0, 5.0)}),
                  (-5.0, 0.0, 2.8, {"birchyoung": (0.42, 3.0, 7.0), "shrub": (0.28, 2.0, 3.8), "alder": (0.15, 4.5, 8.0),
                                    "maple": (0.15, 4.0, 7.5)}),
                  (-11.0, -5.0, 4.6, {"birch": (0.5, 7.0, 12.0), "alder": (0.25, 7.0, 11.0), "maple": (0.25, 6.0, 10.0)})],
}
MANTLE["mixed"] = MANTLE["conifer"]
# Forest floor plants (bilberry / fern / seedlings, prototype tree_floor): only where a driver can see the floor -
# within FLOOR_ROAD_M of a road / yard - and only on the High tier ("tier": "high"), one per FLOOR_SPACING^2.
FLOOR_ROAD_M = 45.0
FLOOR_SPACING = 3.4
# Self-seeded land (OT_PTNZ_A / OT_PTTR_A): species of the old rule -> young prototypes (same positions and draws).
SELF_SEEDED = {"pine": "pineyoung", "birch": "birchyoung", "alder": "birchyoung", "maple": "shrub", "linden": "shrub",
               "shrub": "shrub", "spruce": "pineyoung"}


def _seed(key):
    return int(hashlib.sha1(key.encode()).hexdigest()[:8], 16)


def _scatter(poly, spacing, rng):
    if poly.is_empty:      # ADR 0204: a sliver of forest vanishes under the inward buffer (bounds = nan)
        return np.zeros((0, 2))
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
        for k, ln in enumerate(o.get("lines", [])):
            out.append((shapely.LineString(np.asarray(ln["line_epsg2180"], float) - origin), prm, f"override:{o['id']}:{k}"))
    return out


def _tree_point_overrides(overrides):
    """ADR 0186: `points_en` of an authored `kind: tree_groups` - stems traced one by one from the orthophoto
    (region-local [E, N] or [E, N, height m]); `species` as for the lines (one species per override, drawn by the
    id), `height_m: [lo, hi]` for points without their own height (default: the species range). The stems are only
    refused on a road / paved surface / building itself, not within the 3 m rule clearance: a traced tree stands
    where the orthophoto shows it, e.g. on a lawn island between two footways."""
    out = []
    for o in overrides or []:
        if o.get("kind") != "tree_groups" or not o.get("points_en") or o.get("form") == "kit":
            continue                        # form kit: meshed by streetscape.plantings.authored_trees
        sp = o.get("species") or TREE_GROUP_DEFAULTS["species"]
        hr = o.get("height_m")
        if hr is not None and not (0 < float(hr[0]) <= float(hr[1])):
            raise ValueError(f"tree_groups {o['id']}: height_m must be [lo, hi] with 0 < lo <= hi")
        out.append((np.asarray([q[:2] for q in o["points_en"]], float),
                    [float(q[2]) if len(q) > 2 else None for q in o["points_en"]],
                    sp, tuple(float(v) for v in hr) if hr is not None else None, f"override:{o['id']}:points"))
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


_DIR_VEC = {"N": (0.0, 1.0), "NE": (0.7071, 0.7071), "E": (1.0, 0.0), "SE": (0.7071, -0.7071),
            "S": (0.0, -1.0), "SW": (-0.7071, -0.7071), "W": (-1.0, 0.0), "NW": (-0.7071, 0.7071)}


def _in_facing_edge(poly, P, width_m, facing):
    """Boolean mask of points P within `width_m` of `poly.exterior` on the side facing `facing`."""
    if not len(P):
        return np.zeros(0, bool)
    vx, vy = _DIR_VEC[facing]
    ext = poly.exterior
    pts = shapely.points(P)
    d = shapely.distance(ext, pts)
    near = d <= width_m
    if not near.any():
        return near
    s = shapely.line_locate_point(ext, pts[near])
    bpts = shapely.get_coordinates(shapely.line_interpolate_point(ext, s))
    dx = bpts[:, 0] - P[near, 0]
    dy = bpts[:, 1] - P[near, 1]
    nrm = np.hypot(dx, dy)
    dot = np.where(nrm > 1e-6, (dx * vx + dy * vy) / np.maximum(nrm, 1e-6), 1.0)
    out = np.zeros(len(P), bool)
    out[near] = dot > 0.3
    return out


def _mantle_keep(poly, P, key, bi):
    """Deterministic segment-hash mask for partial mantle belts (M68)."""
    keep_rate = MANTLE_BAND_KEEP[bi]
    if keep_rate >= 1.0 or not len(P):
        return np.ones(len(P), bool)
    s = shapely.line_locate_point(poly.exterior, shapely.points(P))
    segs = np.floor(s / MANTLE_SEG_M).astype(int)
    cache = {}
    mask = np.empty(len(P), bool)
    for k, seg in enumerate(segs):
        val = cache.get(int(seg))
        if val is None:
            val = (_seed(f"{key}:m:{bi}:{int(seg)}") % 1000) < int(round(keep_rate * 1000))
            cache[int(seg)] = val
        mask[k] = val
    return mask


def forest_stands(overrides):
    """Authored `kind: forest_stand` (ADR 0170): measured character of one BDOT10k OT_PTLZ_A stand, where the class
    defaults (HEIGHT / MIX / SPACING) contradict the orthophoto and the photos. {bdot id: params}:
      height_m   [lo, hi] of the canopy trees (replaces HEIGHT[species]; shrubs keep theirs; the edge row keeps its
                 0.6 factor on this range)
      mix        {species: weight} (replaces MIX[kategoria])
      spacing_m  jittered grid step (replaces SPACING[rodzaj])
      emergent   {share, height_m: [lo, hi]}: a few taller trees standing above the canopy (chosen by position hash)
      young_edge {width_m, height_m: [lo, hi], facing}: young regrowth belt along one facing edge (M68)
    Keyed by the BDOT id like forest_clearing; a target missing from the source data is reported as stale."""
    out = {}
    for o in overrides or []:
        if o.get("kind") != "forest_stand":
            continue
        prm = {"id": o["id"], "height_m": tuple(float(v) for v in o["height_m"])}
        if prm["height_m"][0] <= 0 or prm["height_m"][1] < prm["height_m"][0]:
            raise ValueError(f"forest_stand {o['id']}: height_m must be [lo, hi] with 0 < lo <= hi")
        if "mix" in o:
            unknown = set(o["mix"]) - set(SPECIES)
            if unknown:
                raise ValueError(f"forest_stand {o['id']}: unknown species {sorted(unknown)}")
            prm["mix"] = [float(o["mix"].get(k, 0.0)) for k in SPECIES]
        if "spacing_m" in o:
            prm["spacing_m"] = float(o["spacing_m"])
        if "emergent" in o:
            prm["emergent"] = (float(o["emergent"]["share"]), tuple(float(v) for v in o["emergent"]["height_m"]))
        if "young_edge" in o:
            ye = o["young_edge"]
            prm["young_edge"] = (float(ye["width_m"]), tuple(float(v) for v in ye["height_m"]), str(ye["facing"]))
        out[str(o["target"]["bdot"])] = prm
    return out


def park_replacements(overrides):
    """BDOT wooded polygons explicitly represented as maintained parks, not forests.

    An opted-in feature contributes neither forest trees, mantle nor HLOD/forest-floor
    masks. Individually sourced park trees are supplied via tree_groups points.
    """
    return {str(o["target"]["bdot"]): o["id"] for o in overrides or []
            if o.get("kind") == "park_replacement"}


def place(src, origin, hf, zc, blocked, report, overrides=None, hard=None, tree_rows=None, field_plants_on=True):
    """blocked: bool grid (1 m nodes) of roads + paved + buildings (dilated). Returns instance list.
    hard (ADR 0186): the same grid before the dilation - the only clearance of authored `points_en` stems.
    tree_rows (ADR 0222, opt-in): streetscape.tree_rows.region_plan() - the rows it took over are laid out by it
    (rhythm, set-back, sight cuts) instead of the 8 m BDOT row rule below; None = the rule unchanged."""
    out = []
    H, W = zc.shape

    def ok(P):
        i = np.clip(np.rint(P[:, 0] - hf.x0).astype(int), 0, W - 1)
        j = np.clip(np.rint(hf.y1 - P[:, 1]).astype(int), 0, H - 1)
        return ~blocked[j, i], zc[j, i]

    def emit(P, species, rng, src_id, hscale=1.0, fk=None, hrange=None, spruce_v=None, tier=None, keep=None):
        if not len(P):
            return
        good, z = ok(P)
        if keep is not None:                    # ADR 0222 / 0245: candidates outside the part left to this rule (tree
            good = good & keep                  # rows; forest floor near a road); like the clearance test they are
                                                # dropped after their draws, so the stream does not depend on it (0173)
        # ADR 0173: the attributes are drawn for EVERY candidate point (same calls, same order as before), and the
        # clearance test only drops the tree afterwards. Before, a tree dropped by a new kerb / paved area / building
        # skipped its draws and shifted the random stream of every later tree of the same BDOT feature or group
        # (trees changed far outside an edited spot). Features with no dropped candidate keep their exact stream.
        for (x, y), zz, sp, g in zip(P, z, species, good):
            lo, hi = hrange if hrange and sp in CANOPY_SPECIES else HEIGHT[sp]
            h = rng.uniform(lo, hi) * hscale
            v = int(rng.integers(0, 3))
            if sp == "spruce":
                v = SPRUCE_OPEN if spruce_v == "open" else v % 2
            else:
                v %= NVAR.get(sp, 3)
            yaw = float(rng.uniform(0, 6.2832))
            lean = float(rng.uniform(0, 0.05))
            if not g:
                continue
            out.append({"p": f"tree_{sp}", "v": v, "e": round(float(x), 2), "n": round(float(y), 2),
                        "z": round(float(zz), 2), "h": round(float(h), 1), "yaw": round(yaw, 3),
                        "lean": round(lean, 3), "src": src_id})
            if fk:
                out[-1]["fk"] = fk          # forest stand tree (texture mix of the forest HLOD, forest_hlod.py)
            if tier:
                out[-1]["tier"] = tier

    def pick(rng, mix, n):
        return rng.choice(SPECIES[:len(mix)], size=n, p=np.asarray(mix) / np.sum(mix))   # 6-weight mixes: no spruce

    def ranged(n0, table):
        """Heights of out[n0:] from table {species: (.., lo, hi)}: position hash, not the stream (like the understorey)."""
        for t in out[n0:]:
            lo, hi = table[t["p"][5:]][-2:]
            t["h"] = round(float(lo + (hi - lo) * ((_seed(f"{t['e']},{t['n']}") % 1000) / 999.0)), 1)

    from scipy import ndimage as _ndi
    road_dist = _ndi.distance_transform_edt(~blocked)       # metres to the nearest road / yard / building (1 m nodes)
    if not blocked.any():                   # ADR 0245: with no blocked node scipy measures to a phantom point off the
        road_dist = np.full(blocked.shape, np.inf)          # grid corner (floor plants appeared in one corner)

    def near_road(P, lim):
        i = np.clip(np.rint(P[:, 0] - hf.x0).astype(int), 0, W - 1)
        j = np.clip(np.rint(hf.y1 - P[:, 1]).astype(int), 0, H - 1)
        return road_dist[j, i] <= lim

    forests = []
    forest_mix = []
    n_floor = 0
    clear = forest_clearings(overrides, origin)
    crep = {"applied": [], "stale": []}
    hit = set()
    stands = forest_stands(overrides)
    parks = park_replacements(overrides)
    park_hits = set()
    srep = {"applied": [], "stale": []}
    shit = set()
    cleared = []                            # cleared parts of the forest: sand on the orthophoto -> bare ground mask
    for f in src["bdot10k"]["OT_PTLZ_A"]:
        park_id = str(f["id"]).split(":")[0]
        if park_id in parks:
            park_hits.add(park_id)
            continue
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
        sk = f["id"] if f["id"] in stands else str(f["id"]).split(":")[0]
        st = stands.get(sk)                 # measured stand (ADR 0170), else the class defaults
        hr = st["height_m"] if st else None
        if st:
            shit.add(sk)
        P = _scatter(full, st.get("spacing_m", SPACING.get(rodzaj, 4.5)) if st else SPACING.get(rodzaj, 4.5), rng)
        sp = pick(rng, st.get("mix", MIX.get(kat, MIX[None])) if st else MIX.get(kat, MIX[None]), len(P))
        emit(P, sp, rng, f"bdot:{f['id']}", 1.0 if hr else (0.7 if rodzaj == "zagajnik" else 1.0), fk=fk, hrange=hr)
        if st:
            ye_mask = np.zeros(len(out) - n_stand, bool)
            if "young_edge" in st and len(out) > n_stand:
                yw, (ylo, yhi), ydir = st["young_edge"]
                TP = np.array([[t["e"], t["n"]] for t in out[n_stand:]])
                ye_mask = _in_facing_edge(full, TP, yw, ydir)
                for t, is_ye in zip(out[n_stand:], ye_mask):
                    if is_ye and t["p"] != "tree_shrub":
                        u = (_seed(f"ye:{t['e']},{t['n']}") % 1000) / 999.0
                        t["h"] = round(float(ylo + (yhi - ylo) * u), 1)
                        if t["p"] == "tree_pine":
                            t["p"], t["v"] = "tree_pineyoung", 0
                        elif t["p"] == "tree_birch":
                            t["p"], t["v"] = "tree_birchyoung", 0
                        elif t["p"] == "tree_spruce":
                            t["v"] = SPRUCE_OPEN
            n_em = 0
            if "emergent" in st:
                share, (elo, ehi) = st["emergent"]
                for t, is_ye in zip(out[n_stand:], ye_mask):
                    if is_ye:
                        continue
                    u = (_seed(f"em:{t['e']},{t['n']}") % 100000) / 99999.0
                    if t["p"] != "tree_shrub" and u < share:
                        t["h"] = round(float(elo + (ehi - elo) * u / share), 1)
                        n_em += 1
            hs = [t["h"] for t in out[n_stand:] if t["p"] != "tree_shrub"]
            srep["applied"].append({"id": st["id"], "bdot": f["id"], "trees": len(hs), "emergent": n_em,
                                    "h_median_m": round(float(np.median(hs)), 1) if hs else None,
                                    "h_max_m": round(float(max(hs)), 1) if hs else None})
        if rodzaj == "las":
            P = _scatter(full.buffer(-2.0), UNDER_SPACING, rng)
            names = list(UNDERSTOREY)
            w = np.array([UNDERSTOREY[k][2] for k in names])
            sp = rng.choice(names, size=len(P), p=w / w.sum())
            if fk == "broadleaf":           # no conifer regeneration under a broadleaf stand
                sp = np.array([{"spruce": "birchyoung", "pineyoung": "shrub"}.get(k, k) for k in sp])
            n0 = len(out)
            emit(P, sp, rng, f"bdot:{f['id']}:under", 1.0, fk=fk, spruce_v="open")
            ranged(n0, {k: v[:2] for k, v in UNDERSTOREY.items()})
            # forest floor plants where the floor is seen from a road (High tier only)
            # ADR 0245: every candidate draws its attributes and the near-road test only drops it afterwards. Before,
            # the candidates were filtered first, so a new kerb / paved area changed the number of draws and shifted
            # the stream of the stand mantle (:edge) drawn next - trees moved far outside the edited spot (ADR 0173).
            P = _scatter(full.buffer(-1.0), FLOOR_SPACING, rng)
            n0 = len(out)
            emit(P, ["floor"] * len(P), rng, f"bdot:{f['id']}:floor", 1.0, tier="high",
                 keep=near_road(P, FLOOR_ROAD_M) if len(P) else None)
            n_floor += len(out) - n0
        # edge (ADR 0187): mantle of three bands with rising height along the outline (partial by segment hash, M68)
        for bi, (d_in, d_out, step, table) in enumerate(MANTLE[fk]):
            band = full.buffer(d_out).difference(full.buffer(d_in))
            P = _scatter(band, step, rng)
            keep = _mantle_keep(full, P, f["id"], bi)
            if bi == 1 and st and "young_edge" in st and len(P):
                yw, _, ydir = st["young_edge"]
                keep = keep | _in_facing_edge(full, P, yw, ydir)
            P = P[keep]
            names = list(table)
            w = np.array([table[k][0] for k in names])
            sp = rng.choice(names, size=len(P), p=w / w.sum()) if len(P) else []
            n0 = len(out)
            emit(P, sp, rng, f"bdot:{f['id']}:edge", 1.0, fk=fk, spruce_v="open")
            ranged(n0, table)
            if hr:                          # measured stand (ADR 0170): the mantle stays under 0.6 of its canopy
                for t in out[n0:]:
                    if t["p"] != "tree_shrub":
                        t["h"] = round(min(t["h"], hr[1] * 0.6 * (0.5 + 0.25 * bi)), 1)
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
    srep["stale"] = [{"id": st["id"], "bdot": bid} for bid, st in stands.items() if bid not in shit]
    report["forest_stands"] = srep
    if parks:  # ADR 0227: key only where `kind: park_replacement` is authored (no QA diff in other regions)
        report["park_replacements"] = {"applied": sorted(parks[k] for k in park_hits),
                                       "stale": sorted(v for k, v in parks.items() if k not in park_hits)}
    # ADR 0187: authored `kind: tree_stand` - wooded land that is no BDOT10k forest (allotment gardens, a park
    # wood) but closes the horizon on the photos. `polygons_en` (region-local E/N rings, like open_ground),
    # `height_m` [lo, hi] of its trees, `mix` {species: weight}, `spacing_m`, `category` (HLOD texture mix, default
    # broadleaf), `mantle: true` for the two outer mantle bands of a wood (gardens end at a fence, not in a mantle).
    # Laid out like a forest stand (canopy grid, no understorey, no forest floor) and merged into forest HLOD cells far away, so it is a continuous line at any distance. Source ids start
    # with "override:" (open_ground keeps them); the ground mask stays grass.
    trep = []
    for o in overrides or []:
        if o.get("kind") != "tree_stand":
            continue
        hr = tuple(float(v) for v in o["height_m"])
        unknown = set(o["mix"]) - set(SPECIES)
        if unknown or hr[0] <= 0 or hr[1] < hr[0]:
            raise ValueError(f"tree_stand {o['id']}: bad height_m or unknown species {sorted(unknown)}")
        mix = [float(o["mix"].get(k, 0.0)) for k in SPECIES]
        fk = o.get("category", "broadleaf")
        n_before = len(out)
        area = 0.0
        for k, ring in enumerate(o["polygons_en"]):
            poly = shapely.make_valid(shapely.Polygon(np.asarray(ring, float)))
            key = f"override:{o['id']}:{k}"
            rng = np.random.default_rng(_seed(key))
            P = _scatter(poly, float(o.get("spacing_m", 6.0)), rng)
            emit(P, pick(rng, mix, len(P)), rng, key, 1.0, fk=fk, hrange=hr, spruce_v="open")
            for bi, (d_in, d_out, step, table) in enumerate(MANTLE[fk][:2] if o.get("mantle") else []):
                band = poly.buffer(d_out).difference(poly.buffer(d_in))
                P = _scatter(band, step, rng)
                P = P[_mantle_keep(poly, P, key, bi)]
                names = list(table)
                w = np.array([table[n_][0] for n_ in names])
                sp = rng.choice(names, size=len(P), p=w / w.sum()) if len(P) else []
                n0 = len(out)
                emit(P, sp, rng, f"{key}:edge", 1.0, fk=fk, spruce_v="open")
                ranged(n0, table)
                for t in out[n0:]:
                    if t["p"] != "tree_shrub":
                        t["h"] = round(min(t["h"], hr[1] * 0.6 * (0.5 + 0.25 * bi)), 1)
            forest_mix.append((poly, fk))
            area += poly.area
        if "emergent" in o:
            share = float(o["emergent"]["share"])
            elo, ehi = (float(v) for v in o["emergent"]["height_m"])
            for t in out[n_before:]:
                if t["p"] == "tree_shrub" or t["src"].endswith(":edge"):
                    continue
                u = (_seed(f"em:{t['e']},{t['n']}") % 100000) / 99999.0
                if u < share:
                    t["h"] = round(float(elo + (ehi - elo) * u / share), 1)
        trep.append({"id": o["id"], "area_m2": round(area, 1), "trees": len(out) - n_before})
    report["tree_stands"] = trep
    report["_forest_cleared"] = cleared
    groups = _tree_group_overrides(overrides, np.asarray(origin, float))
    grep = {"lines": len(groups), "trees": 0, "groups": 0, "rows_grouped": 0}
    tr_handled = tree_rows["handled"] if tree_rows else set()
    tr_fallback = tree_rows.get("fallback", {}) if tree_rows else {}
    tr_cuts = shapely.union_all(tree_rows["cuts"]) if tr_fallback and tree_rows.get("cuts") else None
    n_fb = 0

    def tr_keep(f, line, P0, P):
        """ADR 0222: a BDOT row the tree_rows plan took over only in part keeps the trees of this rule on the rest of
        it (`fallback` geometry): candidates P0 (on the line) nearer to the taken / out-of-tile part are dropped, so
        are trunks P in the sight fields of the plan. None = the line is all this rule's (unchanged path)."""
        fb = tr_fallback.get(f"bdot:{f['id']}")
        if fb is None or not len(P0):
            return None
        rest = line.difference(fb.buffer(0.01))
        pts = shapely.points(np.asarray(P0, float))
        keep = np.ones(len(P0), bool) if rest.is_empty else shapely.distance(fb, pts) <= shapely.distance(rest, pts)
        if tr_cuts is not None:
            keep &= ~shapely.contains_xy(tr_cuts, P[:, 0], P[:, 1])
        return keep
    for f in src["bdot10k"]["OT_OIPR_L"]:
        if f["props"].get("rodzaj") != "rząd drzew":
            continue
        if f"bdot:{f['id']}" in tr_handled:     # ADR 0222: laid out by streetscape.tree_rows below
            continue
        line = shapely.LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
        rng = np.random.default_rng(_seed(f["id"]))
        near = next((prm for gl, prm, _ in groups if line.distance(gl) <= prm["rows_replace_m"]), None)
        if near is not None:                    # the photos show clumps here, not the BDOT row (ADR 0069)
            P, _ = group_positions(line, rng, near)
            names = list(near["species"])
            w = np.array([near["species"][k] for k in names], float)
            n0 = len(out)
            emit(P, rng.choice(names, size=len(P), p=w / w.sum()), rng, f"bdot:{f['id']}:groups",
                 keep=tr_keep(f, line, P, P))
            n_fb += (len(out) - n0) if f"bdot:{f['id']}" in tr_fallback else 0
            grep["rows_grouped"] += 1
            continue
        P = np.array([line.interpolate(s).coords[0] for s in np.arange(2.0, line.length, 8.0)]).reshape(-1, 2)
        sp = [["linden", "maple"][_seed(f["id"]) % 2]] * len(P)
        Pj = P + rng.normal(0, 0.3, P.shape)
        n0 = len(out)
        emit(Pj, sp, rng, f"bdot:{f['id']}", keep=tr_keep(f, line, P, Pj))
        n_fb += (len(out) - n0) if f"bdot:{f['id']}" in tr_fallback else 0
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
    if tree_rows:                               # ADR 0222: roadside rows (positions + species from the plan)
        n_tr = len(out)
        for row in tree_rows["rows"]:
            if len(row["P"]):
                rng = np.random.default_rng(_seed(row["key"]) + 1)
                emit(row["P"], row["species"], rng, row["key"], hrange=tree_rows["height_m"].get(row["key"]))
        planned = sum(len(r["P"]) for r in tree_rows["rows"])
        # blocked_dropped: planned trunks the clearance grid (roads / yards / buildings, dilated) refused - a trunk
        # the plan moved to the minimum set-back usually ends here (review of PR #101, FIX 3)
        report["tree_rows"] = {"planned": planned, "placed": len(out) - n_tr,
                               "blocked_dropped": planned - (len(out) - n_tr),
                               "lines_handled": len(tr_handled), "lines_partly_handled": len(tr_fallback),
                               "fallback_trees": n_fb, "plan": tree_rows["report"]}
    tpts = _tree_point_overrides(overrides)
    if tpts:
        grep["points"], grep["points_refused"] = 0, []
        for P, hs, spw, hr, key in tpts:
            rng = np.random.default_rng(_seed(key))
            names = list(spw)
            w = np.array([spw[k] for k in names], float)
            sp = str(rng.choice(names, p=w / w.sum()))
            i = np.clip(np.rint(P[:, 0] - hf.x0).astype(int), 0, W - 1)
            j = np.clip(np.rint(hf.y1 - P[:, 1]).astype(int), 0, H - 1)
            free = ~(hard if hard is not None else blocked)[j, i]
            for (x, y), zz, h0, g in zip(P, zc[j, i], hs, free):
                lo, hi = hr if hr and sp != "shrub" else HEIGHT[sp]
                h = h0 if h0 is not None else float(rng.uniform(lo, hi))
                v = int(rng.integers(0, 3))
                yaw = float(rng.uniform(0, 6.2832))
                lean = float(rng.uniform(0, 0.05))
                if not g:
                    grep["points_refused"].append({"src": key, "at": [round(float(x), 1), round(float(y), 1)]})
                    continue
                out.append({"p": f"tree_{sp}", "v": v, "e": round(float(x), 2), "n": round(float(y), 2),
                            "z": round(float(zz), 2), "h": round(float(h), 1), "yaw": round(yaw, 3),
                            "lean": round(lean, 3), "src": key})
                grep["points"] += 1
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
            u = rng.uniform(0, 1, len(P))
            if layer == "OT_PTTR_A" and len(P):
                # ADR 0298 (review 2026-11-18 N4 "część pojedynczo na polu"): OT_PTTR_A is grassland / arable land in use -
                # owner drone photo 11 and the 2025 orthophoto show clean fields with scrub along the margins, not a
                # tree every 20 m. Keep SELF_SEED_EDGE_KEEP within SELF_SEED_EDGE_M of the polygon boundary (field
                # margins, ditches), SELF_SEED_FIELD_KEEP inside (a lone pear / willow). Same random stream.
                d_edge = shapely.distance(shapely.points(P), poly.boundary)
                P = P[u < np.where(d_edge <= SELF_SEED_EDGE_M, SELF_SEED_EDGE_KEEP, SELF_SEED_FIELD_KEEP)]
            else:
                P = P[u < 0.45]
            sp = pick(rng, [0.2, 0.35, 0.05, 0.05, 0.0, 0.35], len(P))
            emit(P, [SELF_SEEDED[k] for k in sp], rng, f"bdot:{f['id']}:self", 1.0)
    # ADR 0334: scrub and lone trees on the baulks between the strips of the field mosaic, samosiew on fallow strips
    # (positions and species from the layout hash - the same plant whichever tile builds it; one rng per plant)
    n0 = len(out)
    for P, sp, key, tag in (field_plants(src, origin, hf, road_dist) if field_plants_on else ()):
        emit(P[None], [sp], np.random.default_rng(key), f"field:{tag}", 1.0)
    report["field_plants"] = {"baulk": sum(1 for t in out[n0:] if t["src"] == "field:baulk"),
                              "fallow": sum(1 for t in out[n0:] if t["src"] == "field:fallow")}
    # ADR 0179: authored open ground (override `kind: open_ground`, `polygons_en`: region-local E/N rings) - land the
    # orthophoto / photos show mown or bare (an airfield meadow) where the BDOT grass layers self-seed trees. Rule
    # trees inside are dropped after generation (the random streams of the features are untouched, ADR 0173);
    # trees of authored tree_groups stay.
    og = [o for o in overrides or [] if o.get("kind") == "open_ground"]
    if og:
        orep = []
        for o in og:
            area = shapely.union_all([shapely.make_valid(shapely.Polygon(np.asarray(r, float))) for r in o["polygons_en"]])
            if out:
                Q = np.array([[t["e"], t["n"]] for t in out])
                gone = shapely.contains_xy(area, Q[:, 0], Q[:, 1])
                gone &= np.array([not str(t.get("src", "")).startswith("override:") for t in out])
                out = [t for t, g in zip(out, gone) if not g]
                orep.append({"id": o["id"], "area_m2": round(area.area, 1), "trees_removed": int(gone.sum())})
        report["open_ground"] = orep
    # ADR 0186: no rule tree within 2.5 m of the stem of an authored kit tree (plantings.authored_trees)
    kpts = [q[:2] for o in overrides or [] if o.get("kind") == "tree_groups" and o.get("form") == "kit"
            for q in o.get("points_en", [])]
    if kpts and out:
        from scipy.spatial import cKDTree as _KD
        dk, _ = _KD(np.asarray(kpts, float)).query(np.array([[t["e"], t["n"]] for t in out]))
        report["tree_groups"]["rule_trees_at_kit_stems"] = int((dk < 2.5).sum())
        out = [t for t, d in zip(out, dk) if d >= 2.5]
    # thin out overlaps (< 1.8 m between trunks), deterministic order
    if out:
        P = np.array([[t["e"], t["n"]] for t in out])
        from scipy.spatial import cKDTree
        tree = cKDTree(P)
        keep = np.ones(len(P), bool)
        auth = np.array([str(t.get("src", "")).endswith(":points") for t in out])     # ADR 0186: traced stems stay
        floor = np.array([t["p"] == "tree_floor" for t in out])    # floor plants grow between the trunks (ADR 0187)
        for i, j in sorted(tree.query_pairs(1.8)):
            if keep[i] and keep[j] and not floor[i] and not floor[j]:
                if auth[j] and not auth[i]:
                    keep[i] = False
                else:
                    keep[j] = False
        out = [t for t, k in zip(out, keep) if k]
    cnt = {}
    for t in out:
        cnt[t["p"]] = cnt.get(t["p"], 0) + 1
    report["trees"] = cnt
    report["understorey"] = sum(1 for t in out if t["src"].endswith(":under"))
    report["forest_floor"] = sum(1 for t in out if t["src"].endswith(":floor"))
    report["forest_mantle"] = sum(1 for t in out if t["src"].endswith(":edge"))
    report["_forest_mix"] = forest_mix
    return out, forests


# ADR 0334: plants of the field mosaic. WORKING_VALUE (orthophoto of Knyszyn / Tykocin read by eye: scrub stands on
# some baulks in runs of a few dozen metres, most baulks are bare grass; a lone pear / willow / birch every few hundred
# metres; fallow strips green over with birch / pine seedlings in patches). Review fields-s24 r1: evenly scattered
# lone saplings read as a sprinkle, so runs are rarer and denser, lone plants rarer, samosiew clustered.
BAULK_CELL_M = 7.0              # one candidate per this length of a strip edge
BAULK_SEG_M = 50.0              # scrub runs: a segment of a baulk is either a run or bare
BAULK_SEG_SHARE = 0.09          # share of segments that carry a run of scrub
BAULK_RUN_KEEP = 0.85           # candidates kept inside a run
BAULK_LONE_KEEP = 0.004         # candidates kept on bare segments (lone shrub / tree)
BAULK_SPECIES = (("shrub", 0.76), ("birchyoung", 0.12), ("pineyoung", 0.05), ("birch", 0.04), ("alder", 0.03))
FALLOW_SPACING_M = 12.0
FALLOW_KEEP = 0.30
FALLOW_PATCH_M = 36.0           # samosiew in patches (seed trees nearby, wet hollows), not an even scatter
FALLOW_PATCH_SHARE = 0.25
FALLOW_SPECIES = (("birchyoung", 0.45), ("pineyoung", 0.35), ("shrub", 0.20))
FIELD_PLANT_ROAD_M = 8.0
FIELD_PLANT_MIN_M2 = 20000.0     # strip farms only on a BDOT polygon >= 2 ha (small grass patches are not fields)


def _pick_species(table, u):
    names = [n for n, _ in table]
    c = np.cumsum([w for _, w in table])
    return [names[min(int(np.searchsorted(c, v * c[-1], side="right")), len(names) - 1)] for v in u]


def field_plants(src, origin, hf, road_dist=None):
    """[(P (2,) region-local, species, rng key, tag)] for the baulks and fallow strips of the field mosaic inside
    BDOT10k OT_PTTR_A, SELF_SEED_EDGE_M off the polygon border (the margin rule plants there) and FIELD_PLANT_ROAD_M
    off roads / yards (road_dist: metres, 1 m grid of hf; None = no test). Deterministic: hash of the layout."""
    feats = (src.get("bdot10k") or {}).get("OT_PTTR_A") or []
    if not feats:
        return []
    polys = {r: [] for r in FIELD_FLAG_B}
    for f in feats:
        r = (f.get("props") or {}).get("rodzaj")
        if r in polys:
            g = shapely.make_valid(PV._poly_local(f["geometry"]["coordinates"], origin))
            if g.area >= FIELD_PLANT_MIN_M2:
                polys[r].append(g)
    areas = {r: shapely.union_all(p) if p else shapely.Polygon() for r, p in polys.items()}
    arable_area = areas["uprawa na gruntach ornych"]
    all_area = shapely.union_all(list(areas.values()))
    if all_area.is_empty:
        return []
    inner = all_area.buffer(-SELF_SEED_EDGE_M)
    if inner.is_empty:
        return []
    shapely.prepare(inner)
    shapely.prepare(arable_area)
    H, W = hf.z.shape
    x0, y1 = hf.x0, hf.y1
    ox, oy = origin

    def keep_ok(Q):
        ins = shapely.contains_xy(inner, Q[:, 0], Q[:, 1])
        ins &= (Q[:, 0] >= x0) & (Q[:, 0] < x0 + W - 1) & (Q[:, 1] <= y1) & (Q[:, 1] > y1 - H + 1)
        if road_dist is not None and ins.any():
            i = np.clip(np.rint(Q[:, 0] - x0).astype(int), 0, W - 1)
            j = np.clip(np.rint(y1 - Q[:, 1]).astype(int), 0, H - 1)
            ins &= road_dist[j, i] > FIELD_PLANT_ROAD_M
        return ins

    out = []
    # --- baulks: candidates on a coarse grid snapped to the nearest strip edge, one per BAULK_CELL_M of edge
    # (4 m grid: every 7 m x >= 22 m catchment of an edge cell holds a node at any rotation, so a cell is found by
    # whichever tile owns its plant; the grid overhangs the tile by 25 m for the cells whose catchment crosses the seam)
    gx, gy = np.meshgrid(np.arange(x0 - 25.0, x0 + W + 25.0, 4.0), np.arange(y1 - H - 25.0, y1 + 25.0, 4.0))
    G = np.column_stack([gx.ravel(), gy.ravel()])
    G = G[shapely.contains_xy(all_area, G[:, 0], G[:, 1])]
    if len(G):
        L = field_layout(G[:, 0] + ox, G[:, 1] + oy)
        up = L["across"] >= 0.5 * L["w"]
        kE = L["k"] + up
        cell = np.floor(L["along"] / BAULK_CELL_M)
        key = np.unique(np.column_stack([L["bid"].astype(np.float64), kE, cell]), axis=0)
        bid, kE, cell = key[:, 0], key[:, 1], key[:, 2]
        # edge geometry of each key from one representative point of its block (seed, th, w)
        rep = {}
        for b, i in zip(L["bid"], range(len(G))):
            rep.setdefault(int(b), i)
        ri = np.array([rep[int(b)] for b in bid])
        th, w, sx, sy = L["th"][ri], L["w"][ri], L["sx"][ri], L["sy"][ri]
        jit = (_u01(_h32(bid, kE * 4099 + cell, 959)) - 0.5) * 0.7 * BAULK_CELL_M
        lat = (_u01(_h32(bid, kE * 4099 + cell, 960)) - 0.5) * 0.6
        s_c = (cell + 0.5) * BAULK_CELL_M + jit
        n = kE * w + lat
        qx = sx + n * np.cos(th) - s_c * np.sin(th)
        qy = sy + n * np.sin(th) + s_c * np.cos(th)
        Lq = field_layout(qx, qy)
        same = (Lq["bid"] == bid.astype(np.uint32)) & (Lq["block_edge"] > 3.0)
        seg = np.floor(s_c / BAULK_SEG_M)
        run = _u01(_h32(bid, kE * 4099 + seg, 961)) < BAULK_SEG_SHARE
        u = _u01(_h32(bid, kE * 4099 + cell, 963))
        sel = same & (u < np.where(run, BAULK_RUN_KEEP, BAULK_LONE_KEEP))
        Q = np.column_stack([qx - ox, qy - oy])[sel]
        ok = keep_ok(Q)
        hs = _h32(bid[sel], kE[sel] * 4099 + cell[sel], 965)
        sp = _pick_species(BAULK_SPECIES, _u01(hs))
        for q, s_, h, g in zip(Q, sp, hs, ok):
            if g:
                out.append((q, s_, int(h), "baulk"))
    # --- fallow strips: samosiew
    sp_ = FALLOW_SPACING_M          # lattice in EPSG:2180 (the same nodes for every tile)
    fx, fy = np.meshgrid(np.arange(np.floor((x0 + ox) / sp_) * sp_ - ox, x0 + W, sp_),
                         np.arange(np.floor((y1 - H + oy) / sp_) * sp_ - oy, y1 + sp_, sp_))
    F = np.column_stack([fx.ravel(), fy.ravel()])
    F = F[shapely.contains_xy(arable_area, F[:, 0], F[:, 1])] if not arable_area.is_empty else F[:0]
    if len(F):
        ax, ay = F[:, 0] + ox, F[:, 1] + oy
        hj = _h32(np.floor(ax), np.floor(ay), 967)
        F = F + (np.column_stack([_u01(hj), _u01(_h32(np.floor(ax), np.floor(ay), 968))]) - 0.5) * FALLOW_SPACING_M * 0.8
        L = field_layout(F[:, 0] + ox, F[:, 1] + oy)
        use = field_use(L, True)
        u = _u01(_h32(np.floor(F[:, 0] + ox), np.floor(F[:, 1] + oy), 969))
        patch = _u01(_h32(np.floor((F[:, 0] + ox) / FALLOW_PATCH_M), np.floor((F[:, 1] + oy) / FALLOW_PATCH_M), 979))
        sel = (use == FIELD_USES.index("fallow")) & (u < FALLOW_KEEP) & (patch < FALLOW_PATCH_SHARE) & (L["block_edge"] > 3.0)
        sel &= np.minimum(L["across"], L["w"] - L["across"]) > 2.0
        Q = F[sel]
        ok = keep_ok(Q) & shapely.contains_xy(arable_area, Q[:, 0], Q[:, 1])
        hs = _h32(np.floor(Q[:, 0] + ox), np.floor(Q[:, 1] + oy), 971)
        sp = _pick_species(FALLOW_SPECIES, _u01(hs))
        for q, s_, h, g in zip(Q, sp, hs, ok):
            if g:
                out.append((q, s_, int(h), "fallow"))
    return out


# ADR 0298: self-seeded trees on BDOT10k OT_PTTR_A (land in agricultural use) - margins only. WORKING_VALUE.
SELF_SEED_EDGE_M = 8.0
SELF_SEED_EDGE_KEEP = 0.35
SELF_SEED_FIELD_KEEP = 0.02


# ------------------------------------------------------------------------------------------- farmland (ADR 0295, P1-4)
# Review 2026-11-18 P1-4: the dryness mask (COLOR_0.b) was the same 8 m / 2.5 m patch noise on every square metre away
# from the roads, so meadows and arable land read as one mottled carpet from the roundabout to the horizon; the owner's
# drone photo 11 and the GUGiK orthophoto show smooth strip fields, each of one tone, with sharp baulks. Inside BDOT10k
# OT_PTTR_A (grassland / arable land) the mask is now a mosaic of fields: one dryness level per field, a faint 40 m
# drift inside it and a rough baulk line between neighbours.
# The field LAYOUT is ESTIMATED: the repo has no cadastral parcels (EGiB), so blocks of parallel strips are laid out
# as a function of the EPSG:2180 position only (same pattern on both sides of a tile seam). Sizes WORKING_VALUE, read
# off the orthophoto of Knyszyn (strips 20-45 m wide, blocks 200-400 m).
FIELD_BLOCK_M = 300.0           # mean size of a block of parallel strips, m
FIELD_STRIP_M = (16.0, 40.0)    # strip width range per block, m (ADR 0334: narrower Podlasie strips)
FIELD_BAULK_M = 1.0             # half-width of the rough baulk line between two fields, m (mask grid = 1 m)
FIELD_BAULK_B = 0.78
FIELD_ROAD_M = 4.0              # the verge rule keeps the first metres beside a road
# dryness (COLOR_0.b) of a field by BDOT10k RODZAJ: lush sward ... dry, unmown meadow (VegetationGround.hlsl: gain
# 0.70 + 0.60 x smoothstep(0.05, 0.95, b))
FIELD_LEVELS = {"roślinność trawiasta": (0.06, 0.10, 0.16, 0.22, 0.30, 0.42, 0.58),
                "uprawa na gruntach ornych": (0.04, 0.08, 0.14, 0.24, 0.50)}
FIELD_DRIFT = 0.06              # peak-to-peak drift of the level inside one field
FIELD_STRIP_DEV = 0.05          # a strip differs from its block by up to this
FIELD_OWN_SHARE = 0.2           # share of strips with a use of their own
# Residential land (BDOT10k OT_PTZB_A of a housing RODZAJ) away from the roads = gardens and yards between houses:
# on the orthophoto mostly kept sward. Dryness GARDEN_B[0] + GARDEN_B[1] x (18 m patches with a little 2.5 m detail)
# instead of 0.25 + 0.75 x (8 m patches): the straw patches of unmanaged ground do not belong there. WORKING_VALUE.
GARDEN_RODZAJ = ("jednorodzinna", "wielorodzinna", "zagrodowa")
GARDEN_B = (0.12, 0.30)
# ADR 0298 (knyszyn-p2-s24, review 2026-11-18 N1 / N3): the mosaic levels above no longer reach the mesh. The High terrain
# band keeps 1 m vertices only near the roads (8 m elsewhere), Low is 2 m: the per-field level baked into COLOR_0.b lost
# its 2 m baulks and read as smudges, and the apron outside the tile could not carry it at all (hard seam on every tile
# edge). Farmland now carries a FLAG in COLOR_0.b and Kamion/World PBR draws the mosaic per pixel from the EPSG:2180
# position (game/Assets/_Project/Environment/Shaders/KamionFieldMosaic.hlsl: same field on both sides of any seam). Every
# other ground keeps B <= GROUND_B_MAX so it never reads as a flag.
FIELD_FLAG_B = {"roślinność trawiasta": 0.90, "uprawa na gruntach ornych": 1.00}
GROUND_B_MAX = 0.80


def _h32(a, b, salt):
    h = (a.astype(np.int64).astype(np.uint32) * np.uint32(1597334677)
         ^ b.astype(np.int64).astype(np.uint32) * np.uint32(3812015801) ^ np.uint32(salt))
    h ^= h >> np.uint32(16)
    h *= np.uint32(2246822519)
    h ^= h >> np.uint32(13)
    return h


def _u01(h):
    return (h & np.uint32(0xFFFFFF)).astype(np.float64) / float(0xFFFFFF)


# ADR 0334 (fields-s24, critic build #5 pt 3): the shader draws a USE per strip (KamionFieldMosaic.hlsl KFUse); the
# generator mirrors it to put plants where the use / layout calls for them (baulk scrub, samosiew on fallow).
# (name, cumulative share) in shader order; arable 0..10, grassland 11..15. Shares WORKING_VALUE (see the shader).
FIELD_USES_ARABLE = (("cereal_ripe", 0.18), ("cereal_pale", 0.26), ("stubble", 0.44), ("stubble_baled", 0.50),
                     ("rape_stubble", 0.54), ("maize", 0.74), ("roots", 0.78), ("disked", 0.86), ("catch_crop", 0.90),
                     ("grass_ley", 0.96), ("fallow", 1.0))
FIELD_USES_GRASS = (("meadow_regrowth", 0.30), ("pasture", 0.50), ("meadow_mown", 0.62), ("meadow_hay", 0.72),
                    ("meadow_uncut", 1.0))
FIELD_USES = tuple(n for n, _ in FIELD_USES_ARABLE + FIELD_USES_GRASS)
FIELD_OWN_SHARE_SHADER = 0.55   # KF_OWN_SHARE
FIELD_BAULK_W = (1.0, 1.6)      # KF_BAULK_MIN_M, KF_BAULK_SPAN_M


def _h32s(a, b, salt):
    """_h32 with a per-element salt (uint32 array)."""
    h = (a.astype(np.int64).astype(np.uint32) * np.uint32(1597334677)
         ^ b.astype(np.int64).astype(np.uint32) * np.uint32(3812015801) ^ salt.astype(np.uint32))
    h ^= h >> np.uint32(16)
    h *= np.uint32(2246822519)
    h ^= h >> np.uint32(13)
    return h


def _nearest2(x, y, cell, seed_fn):
    """Nearest and second-nearest jittered lattice seed (3 x 3 search) - the shader's loop. seed_fn(i, j) -> (sx, sy).
    Returns (i, j, s1x, s1y, s2x, s2y, d1, d2) arrays (squared distances)."""
    cx, cy = np.floor(x / cell), np.floor(y / cell)
    d1, d2 = np.full(x.shape, np.inf), np.full(x.shape, np.inf)
    s1x, s1y, s2x, s2y = (np.zeros(x.shape) for _ in range(4))
    bi, bj = np.zeros(x.shape), np.zeros(x.shape)
    for dj in (-1, 0, 1):
        for di in (-1, 0, 1):
            i, j = cx + di, cy + dj
            sx, sy = seed_fn(i, j)
            dd = (x - sx) ** 2 + (y - sy) ** 2
            m1 = dd < d1
            m2 = ~m1 & (dd < d2)
            d2 = np.where(m1, d1, np.where(m2, dd, d2))
            s2x = np.where(m1, s1x, np.where(m2, sx, s2x))
            s2y = np.where(m1, s1y, np.where(m2, sy, s2y))
            d1 = np.where(m1, dd, d1)
            s1x, s1y = np.where(m1, sx, s1x), np.where(m1, sy, s1y)
            bi, bj = np.where(m1, i, bi), np.where(m1, j, bj)
    return bi, bj, s1x, s1y, s2x, s2y, d1, d2


FIELD_DISTRICT_M = 1600.0       # KF_DISTRICT_M: one strip direction per district (a village's fields)
FIELD_BLOCK_HASH_OFS = 4096     # KF_BLOCK_HASH_OFS: _h32(i, j) == _h32(-i, -j), so signed block indices are offset
FIELD_STRETCH = 3.0             # KF_STRETCH: blocks 3x longer along the strips than across


def field_layout(x, y):
    """Strip layout of the farmland mosaic at EPSG:2180 positions x, y (arrays of one shape) - the exact mirror of
    KamionFieldMosaic.hlsl (ADR 0334): district (FIELD_DISTRICT_M lattice) -> long axis of the strips; blocks = Voronoi
    cells of the FIELD_BLOCK_M lattice in the frame stretched FIELD_STRETCH x along that axis; strip normal th (+-5.7 deg
    per block), width w; across = projection of (P - block seed) on the normal, modulo w. Returns a dict of arrays: fid,
    bid (uint32), k (strip index), across (m from the strip's lower edge), along (m), w, th, block_edge (m to the block
    / district border), sx, sy (block seed, EPSG:2180)."""
    x, y = np.asarray(x, np.float64), np.asarray(y, np.float64)
    DM = FIELD_DISTRICT_M
    di_, dj_, sdx, sdy, sdx2, sdy2, e1, e2 = _nearest2(
        x, y, DM, lambda i, j: ((i + 0.15 + 0.7 * _u01(_h32(i, j, 971))) * DM, (j + 0.15 + 0.7 * _u01(_h32(i, j, 973))) * DM))
    district_edge = (e2 - e1) / np.maximum(2.0 * np.hypot(sdx2 - sdx, sdy2 - sdy), 1e-3)
    dsalt = _h32(di_, dj_, 977)
    thD = np.pi * _u01(_h32(di_, dj_, 975))
    ax, ay = np.cos(thD), np.sin(thD)
    nx, ny = -ay, ax
    r0x, r0y = x - sdx, y - sdy
    qx = (r0x * ax + r0y * ay) / FIELD_STRETCH
    qy = r0x * nx + r0y * ny
    BM = FIELD_BLOCK_M
    HO = FIELD_BLOCK_HASH_OFS
    bi, bj, s1x, s1y, s2x, s2y, d1, d2 = _nearest2(
        qx, qy, BM, lambda i, j: ((i + 0.15 + 0.7 * _u01(_h32s(i + HO, j + HO, np.uint32(911) ^ dsalt))) * BM,
                                  (j + 0.15 + 0.7 * _u01(_h32s(i + HO, j + HO, np.uint32(913) ^ dsalt))) * BM))
    bi, bj = bi + HO, bj + HO           # hashed indices (the shader's hb)
    L = np.maximum(np.hypot(s2x - s1x, s2y - s1y), 1e-3)
    nqx, nqy = (s2x - s1x) / L, (s2y - s1y) / L
    block_edge = (d2 - d1) / np.maximum(2.0 * L, 1e-3) / np.hypot(nqx / FIELD_STRETCH, nqy)
    block_edge = np.minimum(block_edge, district_edge)
    th = thD + 0.5 * np.pi + (_u01(_h32s(bi, bj, np.uint32(917) ^ dsalt)) - 0.5) * 0.2
    w = FIELD_STRIP_M[0] + (FIELD_STRIP_M[1] - FIELD_STRIP_M[0]) * _u01(_h32s(bi, bj, np.uint32(919) ^ dsalt))
    sx = sdx + ax * (s1x * FIELD_STRETCH) + nx * s1y
    sy = sdy + ay * (s1x * FIELD_STRETCH) + ny * s1y
    rx, ry = x - sx, y - sy
    t = (rx * np.cos(th) + ry * np.sin(th)) / w
    k = np.floor(t)
    bid = _h32s(bi, bj, np.uint32(923) ^ dsalt)
    fid = _h32(bid.astype(np.float64), k, 929)
    return {"fid": fid, "bid": bid, "k": k, "across": (t - k) * w, "along": -rx * np.sin(th) + ry * np.cos(th),
            "w": w, "th": th, "block_edge": block_edge, "sx": sx, "sy": sy}


def field_ids(x, y):
    """(field id, block id), uint32, at EPSG:2180 positions x, y: the strip of the mosaic block (field_layout). A pure
    function of the position, so two tiles agree along their seam."""
    L = field_layout(x, y)
    return L["fid"], L["bid"]


def field_use(L, arable):
    """Use index (FIELD_USES) of the strips of layout L (field_layout); arable: bool array / scalar (BDOT rodzaj)."""
    fid = L["fid"].astype(np.float64)
    bid = L["bid"].astype(np.float64)
    zero = np.zeros(fid.shape)
    own = _u01(_h32(fid, zero, 931)) < FIELD_OWN_SHARE_SHADER
    r = np.where(own, _u01(_h32(fid, zero, 937)), _u01(_h32(bid, zero, 939)))
    ca = np.array([c for _, c in FIELD_USES_ARABLE])
    cg = np.array([c for _, c in FIELD_USES_GRASS])
    ua = np.minimum(np.searchsorted(ca, r, side="right"), len(ca) - 1)
    ug = len(ca) + np.minimum(np.searchsorted(cg, r, side="right"), len(cg) - 1)
    return np.where(np.asarray(arable, bool), ua, ug)


def field_mosaic(src, origin, hf, with_kind=False):
    """(level, inside[, kind]): dryness level (H, W) of the farmland mosaic and its mask - the cells inside BDOT10k
    OT_PTTR_A; kind = 1-based index into sorted(FIELD_LEVELS). level carries the baulks and the in-field drift (QA
    reference of the per-pixel shader since ADR 0298; the mesh gets the flag only)."""
    H, W = hf.z.shape
    feats = (src.get("bdot10k") or {}).get("OT_PTTR_A") or []
    inside = np.zeros((H, W), bool)
    kind = np.zeros((H, W), np.uint8)
    kinds = sorted(FIELD_LEVELS)
    for n, rodzaj in enumerate(kinds, 1):
        m = PV.rasterize_polys([PV._poly_local(f["geometry"]["coordinates"], origin) for f in feats
                                if (f.get("props") or {}).get("rodzaj") == rodzaj], hf)
        kind[m] = n
        inside |= m
    if not inside.any():
        return (np.zeros((H, W), np.float32), inside) + ((kind,) if with_kind else ())
    X = origin[0] + hf.x0 + np.arange(W)[None, :] + np.zeros((H, 1))
    Y = origin[1] + hf.y1 - np.arange(H)[:, None] + np.zeros((1, W))
    fid, bid = field_ids(X, Y)
    zero = np.zeros(fid.shape)
    # a block of strips is mostly one use (the orthophoto: neighbouring strips of a block differ a little, blocks
    # differ a lot): the block draws the level, a strip moves it by +-FIELD_STRIP_DEV, FIELD_OWN_SHARE of the strips
    # draw their own
    own = _u01(_h32(fid.astype(np.float64), zero, 931)) < FIELD_OWN_SHARE
    r = np.where(own, _u01(_h32(fid.astype(np.float64), zero, 937)), _u01(_h32(bid.astype(np.float64), zero, 939)))
    dev = (_u01(_h32(fid.astype(np.float64), zero, 943)) - 0.5) * 2.0 * FIELD_STRIP_DEV
    level = np.zeros((H, W), np.float64)
    for n, rodzaj in enumerate(kinds, 1):
        lv = np.asarray(FIELD_LEVELS[rodzaj])
        level = np.where(kind == n, lv[np.minimum((r * len(lv)).astype(int), len(lv) - 1)] + dev, level)
    level += FIELD_DRIFT * (metric_patch_field(hf.x0 + np.arange(W), hf.y1 - np.arange(H), 40.0, 941) - 0.5)
    edge = np.zeros((H, W), bool)                    # baulk: a neighbour cell belongs to another field or land class
    key = fid.astype(np.int64) * 4 + kind
    edge[:, 1:] |= key[:, 1:] != key[:, :-1]
    edge[1:, :] |= key[1:, :] != key[:-1, :]
    baulk = ndimage.distance_transform_edt(~edge) <= FIELD_BAULK_M
    level = np.where(baulk, FIELD_BAULK_B, level)
    return (np.clip(level, 0.0, 1.0).astype(np.float32), inside) + ((kind,) if with_kind else ())


def ground_masks(src, origin, hf, dist_road, forests, cleared=(), report=None):
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
    # ADR 0295 (review 2026-11-18 P1-4): farmland = a mosaic of fields, not the patch noise
    flevel, finside, fkind = field_mosaic(src, origin, hf, with_kind=True)
    fields = finside & ~mapped_lawn & (dist_road >= FIELD_ROAD_M) & ~G.astype(bool)
    if report is not None:
        report["farmland"] = {"cells_m2": int(fields.sum()), "share": round(float(fields.mean()), 4),
                              "b_std_before": round(float(B[fields].std()), 4) if fields.any() else None,
                              "b_std_after": round(float(flevel[fields].std()), 4) if fields.any() else None,
                              "b_mean_before": round(float(B[fields].mean()), 4) if fields.any() else None,
                              "b_mean_after": round(float(flevel[fields].mean()), 4) if fields.any() else None,
                              "layout": "ESTIMATED strips (no cadastral parcels in the repo)"}
    gardens = PV.rasterize_polys([PV._poly_local(f["geometry"]["coordinates"], origin)
                                  for f in (src.get("bdot10k") or {}).get("OT_PTZB_A") or []
                                  if str((f.get("props") or {}).get("rodzaj", "")).strip() in GARDEN_RODZAJ], hf)
    gardens &= ~fields & ~mapped_lawn & (dist_road >= FIELD_ROAD_M) & ~G.astype(bool)
    calm = GARDEN_B[0] + GARDEN_B[1] * (.75 * metric_patch_field(east, north, 18.0, 947) + .25 * small)
    if report is not None:
        report["farmland"].update({"garden_cells_m2": int(gardens.sum()),
                                   "garden_b_mean_before": round(float(B[gardens].mean()), 4) if gardens.any() else None,
                                   "garden_b_mean_after": round(float(calm[gardens].mean()), 4) if gardens.any() else None,
                                   "garden_b_std_before": round(float(B[gardens].std()), 4) if gardens.any() else None,
                                   "garden_b_std_after": round(float(calm[gardens].std()), 4) if gardens.any() else None})
    flag = np.zeros((H, W), np.float32)
    kinds = sorted(FIELD_LEVELS)
    for n, rodzaj in enumerate(kinds, 1):
        flag = np.where(fkind == n, FIELD_FLAG_B[rodzaj], flag)
    if report is not None:
        report["farmland"]["encoding"] = "COLOR_0.b flag (0.90 grassland, 1.00 arable), mosaic per pixel (ADR 0298)"
    B = np.where(fields, flag, np.minimum(np.where(gardens, calm, B), GROUND_B_MAX))
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


def authored_bare_ground(col, hf, origin, overrides, hard_mask):
    """Colour opted-in planting islands as bare soil without adding hard geometry.

    The alpha channel is the existing terrain bare-soil mask. The painted area
    is limited to the authored rings and never modifies hard surfaces, the hard
    mask, collision, or vegetation placement. No opt-in means an exact no-op.
    """
    from shapely.geometry import Polygon

    origin = np.asarray(origin, float)
    polys = []
    for o in overrides or []:
        if o.get("kind") == "paved_area" and o.get("bare_soil_holes") is True:
            polys.extend(Polygon(np.asarray(h, float) - origin) for h in o.get("holes_epsg2180", []))
        elif o.get("kind") == "unpaved_area" and o.get("bare_soil") is True:
            ring = np.asarray(o["polygon_en"], float) if "polygon_en" in o else np.asarray(o["polygon_epsg2180"], float) - origin
            polys.append(Polygon(ring))
    if not polys:
        return col
    if any(not p.is_valid or p.is_empty or p.area <= 0 for p in polys):
        raise ValueError("authored bare-soil polygon is invalid")
    soil = PV.rasterize_polys(polys, hf) & ~np.asarray(hard_mask, dtype=bool)
    if not soil.any():
        return col
    # WORKING_VALUE: strong soil coverage on opted-in cells. Terrain vertex
    # interpolation softens the boundary; never paint across the hard mask.
    out = col.copy()
    out[..., 3][soil] = np.maximum(out[..., 3][soil], .94)
    out[..., 1][soil] = 0.0
    return out


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


# ADR 0308: clearance of the carriageway (owner s24, DK65: crowns hang over the road at cab height). A tree whose crown
# base is under CLEAR_H_M may reach at most CLEAR_OVERHANG_M over the carriageway edge. Crown radius / H and clear
# stem / H of the library models (make_trees.CROWN; pine / stand spruce from their growers; the open-grown spruce
# variant and the young forms carry boughs to the ground). Species not listed (shrub, floor) are left alone: they are
# lower than the cab and already 2.5 m off the surface.
CLEAR_H_M = 4.7            # WORKING_VALUE: 4.5 m clearance gauge of a rural road (Dz.U. 2022 poz. 1518) + 0.2 m
CLEAR_OVERHANG_M = 0.3
CLEAR_MIN_SCALE = 0.65     # a tree that would have to shrink below this share of its height is removed instead
CROWN_FORM = {"linden": (0.33, 0.17), "maple": (0.375, 0.18), "birch": (0.235, 0.27), "alder": (0.24, 0.22),
              "poplar": (0.195, 0.19), "pine": (0.22, 0.48), "spruce": (0.185, 0.05), "willow": (0.48, 0.20),
              "pineyoung": (0.34, 0.08), "birchyoung": (0.27, 0.16)}


def road_clearance(trees, carriage, report):
    """Shrink or drop the trees whose crown would hang into the carriageway below CLEAR_H_M. Returns the new list
    (records are copied when changed); report["road_clearance"] = counts. Deterministic, order kept."""
    rep = {"checked": 0, "lowered": 0, "removed": 0, "clear_h_m": CLEAR_H_M, "overhang_m": CLEAR_OVERHANG_M}
    report["road_clearance"] = rep
    if carriage is None or carriage.is_empty or not trees:
        return trees
    import shapely
    shapely.prepare(carriage)
    idx = [i for i, t in enumerate(trees) if str(t.get("p", "")).startswith("tree_") and t["p"][5:] in CROWN_FORM]
    if not idx:
        return trees
    d = shapely.distance(carriage, shapely.points([trees[i]["e"] for i in idx], [trees[i]["n"] for i in idx]))
    out = list(trees)
    drop = set()
    for i, dist in zip(idx, d):
        t = trees[i]
        k, bole = CROWN_FORM[t["p"][5:]]
        if t["p"] == "tree_spruce" and t.get("v") != SPRUCE_OPEN:
            k, bole = 0.15, 0.36                # stand form: live crown from ~0.36 H
        h = float(t["h"])
        rep["checked"] += 1
        if bole * h >= CLEAR_H_M or k * h <= dist + CLEAR_OVERHANG_M:
            continue
        h2 = (float(dist) + CLEAR_OVERHANG_M) / k
        if h2 < CLEAR_MIN_SCALE * h:
            drop.add(i)
            rep["removed"] += 1
        else:
            out[i] = dict(t, h=round(h2, 1))
            rep["lowered"] += 1
    return [t for i, t in enumerate(out) if i not in drop]
