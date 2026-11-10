"""Fidelity metrics of generated roads vs OSM / orthophoto / BDOT10k (ADR 0075).

(a) axis vs OSM            per edge: distance of the generated axis (dense, smoothed) to the OSM way (fresh extract)
(b) edges vs ortho / BDOT  per station: detected carriageway edge on a perpendicular ortho profile vs generated edge;
                           per window: IoU of carriageway masks, gen-only / ortho-only components
(c) lanes                  per edge: generated lanes / directions / turn lanes vs OSM tags; lane lines on hi-res ortho
(d) separations            generated islands / medians vs ortho (road under island?) and ortho islands missing in gen
(e) roundabouts            ring radius, lanes, entries / exits: OSM vs generated
(f) arrows / stop lines    generated arrows per approach lane vs OSM turn:lanes vs paint on ortho
(g) connectivity           every OSM drivable way touching the tile exists in the graph and as a junction arm

Every finding carries `cause` = generator module.function that produced the deviation (or `osm` / `ortho`
when the source itself is wrong / ambiguous) and a `confidence`.
"""
from __future__ import annotations

import math
from collections import Counter, defaultdict

import numpy as np
from scipy import ndimage as ndi
from shapely.geometry import LineString, Point, Polygon

from . import gen as G
from . import imaging as I

DRIVABLE = {"motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link", "secondary",
            "secondary_link", "tertiary", "tertiary_link", "unclassified", "residential", "living_street", "service",
            "road"}
EXTRA_LANE_TAGS = ("placement", "placement:forward", "placement:backward", "width:lanes", "width:lanes:forward",
                   "width:lanes:backward", "change:lanes", "change:lanes:forward", "change:lanes:backward",
                   "destination:lanes", "lanes:psv", "lanes:bus", "lanes:both_ways", "turn:lanes:both_ways")
PROFILE_STEP = 2.0        # m between edge stations
ALONG_HALF = 1.2          # m along-track half window of a profile (median)
OUT_MARGIN = 6.0          # m searched outside the generated edge
RUN_MIN = 0.6             # m of continuous non-road that ends the carriageway (WORKING_VALUE)


def pct(a, q):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    return round(float(np.percentile(a, q)), 3) if len(a) else None


def stats(a):
    a = np.asarray(a, float)
    a = a[np.isfinite(a)]
    if not len(a):
        return {"n": 0}
    return {"n": int(len(a)), "p50": pct(a, 50), "p95": pct(a, 95), "max": round(float(a.max()), 3)}


# ------------------------------------------------------------------ context
class Ctx:
    def __init__(self, region, g: G.Generated, osm, ortho, route_pts):
        self.region, self.g, self.osm, self.ortho = region, g, osm, ortho
        self.net = g.world.net
        self.ox, self.oy = g.origin
        self.route = LineString(route_pts)
        self.ways = {w["id"]: w for w in osm["ways"]}
        self.chain_of_edge = {}
        for c in self.net.chains:
            for eid, _ in c.edges:
                self.chain_of_edge[eid] = c
        self.bridge_tris = g.tris[g.tri_layer == "bridge"]
        # chains under a bridge deck: stations covered by a deck of another chain are hidden on the ortho
        import shapely
        self._deck = shapely.union_all(shapely.polygons(np.concatenate([self.bridge_tris, self.bridge_tris[:, :1]], 1))
                                       ) if len(self.bridge_tris) else None
        if self._deck is not None:
            shapely.prepare(self._deck)

    def osm_line(self, way_id):
        w = self.ways.get(int(way_id))
        if not w:
            return None
        return LineString(np.array(w["geometry"]) - [self.ox, self.oy])

    def under_deck(self, xy):
        return self._deck is not None and self._deck.contains(Point(xy))


def way_of(eid):
    return int(eid.split(":")[0].lstrip("w"))


# ------------------------------------------------------------------ (a) axis
def axis_metrics(ctx: Ctx, edges=None):
    out = {}
    graph_dev = []
    for c in ctx.net.chains:
        if c.meta.get("absorbed"):
            continue
        L_raw = c.raw_spans[-1][1]
        s_raw = c.line.s * (L_raw / max(c.line.length, 1e-9))
        for (s0, s1, eid, _rev) in c.raw_spans:
            if edges is not None and eid not in edges:
                continue
            ol = ctx.osm_line(way_of(eid))
            if ol is None:
                out[eid] = {"missing_in_osm": True}
                continue
            sel = (s_raw >= s0) & (s_raw <= s1)
            pts = c.line.p[sel][::2]
            if not len(pts):
                continue
            d = np.array([ol.distance(Point(p)) for p in pts])
            out[eid] = stats(d)
            # graph geometry vs fresh OSM (same snapshot -> ~0; > 0.05 m means the graph is stale)
            raw = np.array(c.raw)
            k = (np.r_[0, np.cumsum(np.hypot(*np.diff(raw, axis=0).T))] >= s0 - 1e-6) & \
                (np.r_[0, np.cumsum(np.hypot(*np.diff(raw, axis=0).T))] <= s1 + 1e-6)
            if k.any():
                graph_dev.append(max(ol.distance(Point(p)) for p in raw[k]))
    return out, stats(graph_dev)


# ------------------------------------------------------------------ (b) edges on profiles
def _bilinear(img, rows, cols):
    out = np.empty(rows.shape + (img.shape[2],), np.float32)
    for k in range(img.shape[2]):
        out[..., k] = ndi.map_coordinates(img[..., k], [rows, cols], order=1, mode="nearest")
    return out


def chain_edge_profiles(ctx: Ctx, c, s_from, s_to, res_pref=0.08, step=PROFILE_STEP):
    """Detected edge offsets (left, right) along chain c between stations; returns list of station dicts."""
    res_list = []
    hw_max = float(c.hw.max())
    span = OUT_MARGIN + hw_max + 1.5
    blk = 36.0
    s = s_from
    while s < s_to - 1e-6:
        sb = min(s_to, s + blk)
        st = np.arange(s + step / 2, sb, step)
        if not len(st):
            s = sb
            continue
        P = c.line.point(st)
        x0, y0 = P.min(0) - span
        x1, y1 = P.max(0) + span
        bbox = (x0 + ctx.ox, y0 + ctx.oy, x1 + ctx.ox, y1 + ctx.oy)
        hr = ctx.ortho.has_hr(bbox)
        res = res_pref if hr else 0.25
        rgb, src = ctx.ortho.window(bbox, res, prefer_hr=hr)
        lab = I.rgb2lab(rgb)
        gm = G.rasterize(ctx.g.tris, x0, y1, res, rgb.shape[:2])
        green = I.exg(rgb) > I.EXG_GREEN
        model = I.road_model(lab, ndi.binary_erosion(gm, structure=I.disk(1.0 / res)) & ~green)
        if model is None:
            s = sb
            continue
        dist = I._dist(lab, model["centers"])
        nonroad = ((dist >= model["thr"]) | green).astype(np.float32)
        paint = ((lab[..., 0] > model["L_med"] + I.PAINT_DL)).astype(np.float32)
        for si in st:
            hw = float(c.hw_at(si))
            p0 = c.line.point(si)
            t, nrm = c.line.frame(si)
            if ctx.under_deck(p0) and not bool(c.bridge[c.idx(si)]):
                res_list.append({"s": float(si), "skip": "under_deck"})
                continue
            lat = np.arange(-(hw + OUT_MARGIN), hw + OUT_MARGIN + 1e-9, res)
            along = np.arange(-ALONG_HALF, ALONG_HALF + 1e-9, max(res, 0.2))
            XY = p0 + lat[None, :, None] * nrm + along[:, None, None] * t
            cols = (XY[..., 0] - x0) / res - 0.5
            rows = (y1 - XY[..., 1]) / res - 0.5
            nr = ndi.map_coordinates(nonroad, [rows, cols], order=0, mode="nearest")
            gmv = ndi.map_coordinates(gm.astype(np.float32), [rows, cols], order=0, mode="nearest")
            prof = np.median(nr, axis=0)               # 1 = not road
            gprof = np.median(gmv, axis=0)              # generated carriageway (any chain)
            rec = {"s": float(si), "hw": hw, "res": res, "src": src}
            ic = len(lat) // 2
            core = np.abs(lat) < max(0.5, hw - 1.2)
            if prof[core].mean() > 0.45:
                rec["skip"] = "centre_not_road"
                res_list.append(rec)
                continue
            for side, sgn in (("L", 1), ("R", -1)):
                # adjacent generated carriageway just outside this edge -> edge is shared / ambiguous
                k_out = np.argmin(np.abs(lat - sgn * (hw + 1.2)))
                if gprof[k_out] > 0.5:
                    rec[side] = None
                    rec[side + "_why"] = "adjacent_carriageway"
                    continue
                idx = range(ic, len(lat)) if sgn > 0 else range(ic, -1, -1)
                run, start, found = 0, None, None
                need = int(math.ceil(RUN_MIN / res))
                for k in idx:
                    if prof[k] > 0.5:
                        if run == 0:
                            start = k
                        run += 1
                        if run >= need:
                            found = start
                            break
                    else:
                        run = 0
                if found is None:
                    rec[side] = None
                    rec[side + "_why"] = "no_edge_within_margin"
                    continue
                det = abs(lat[found]) - res / 2
                rec[side] = round(float(det - hw), 3)      # + = real carriageway extends beyond the generated edge
            res_list.append(rec)
        s = sb
    return res_list


# ------------------------------------------------------------------ window masks, IoU, islands
def window_masks(ctx: Ctx, center, half, res=0.1, yards=None, walk_tris=None):
    x0, y0 = center[0] - half, center[1] - half
    x1, y1 = center[0] + half, center[1] + half
    bbox = (x0 + ctx.ox, y0 + ctx.oy, x1 + ctx.ox, y1 + ctx.oy)
    hr = ctx.ortho.has_hr(bbox)
    res = res if hr else 0.25
    rgb, src = ctx.ortho.window(bbox, res, prefer_hr=hr)
    gm = G.rasterize(ctx.g.tris, x0, y1, res, rgb.shape[:2])
    om, green, paint, model = I.road_mask(rgb, gm, res)
    other = np.zeros_like(gm)
    if walk_tris is not None and len(walk_tris):
        other |= G.rasterize(walk_tris, x0, y1, res, rgb.shape[:2])
    if yards is not None:
        from rasterio import features
        from rasterio.transform import from_origin
        shapes = [(p, 1) for p in yards if p.intersects(Polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)]))]
        if shapes:
            other |= features.rasterize(shapes, out_shape=gm.shape, transform=from_origin(x0, y1, res, res)).astype(bool)
    return {"rgb": rgb, "src": src, "res": res, "x0": x0, "y1": y1, "gen": gm, "ortho": om, "green": green,
            "paint": paint, "other": other, "model": model}


def iou(wm, band_m=6.0):
    res = wm["res"]
    band = ndi.binary_dilation(wm["gen"], structure=I.disk(band_m / res))
    g = wm["gen"] & band
    o = wm["ortho"] & band & ~(wm["other"] & ~wm["gen"])
    inter = (g & o).sum()
    uni = (g | o).sum()
    return {"iou": round(float(inter / max(uni, 1)), 4), "gen_m2": round(float(g.sum() * res * res), 1),
            "ortho_m2": round(float(o.sum() * res * res), 1)}


def _components(mask, res, min_m2):
    lbl, n = ndi.label(mask)
    out = []
    if not n:
        return out, lbl
    idx = np.arange(1, n + 1)
    area = ndi.sum(np.ones_like(lbl), lbl, idx) * res * res
    com = ndi.center_of_mass(mask, lbl, idx)
    for k, a, cm in zip(idx, area, com):
        if a >= min_m2:
            out.append({"label": int(k), "area_m2": round(float(a), 1), "rc": cm})
    return out, lbl


def separations(wm, close_m=7.0, min_m2=4.0):
    """Generated islands/medians = closed-gen minus gen; per component: fraction that is road / green on ortho.
    Ortho islands = closed-ortho minus ortho, overlapping generated carriageway."""
    res = wm["res"]
    gen, orth = wm["gen"], wm["ortho"]
    st = I.disk(close_m / res)
    g_closed = ndi.binary_closing(np.pad(gen, int(close_m / res) + 2), structure=st)[
        int(close_m / res) + 2:-int(close_m / res) - 2, int(close_m / res) + 2:-int(close_m / res) - 2]
    g_closed |= ndi.binary_fill_holes(gen)
    gsep = g_closed & ~gen
    comps, lbl = _components(gsep, res, min_m2)
    gen_islands = []
    ok_m = np.zeros_like(gen)
    bad_m = np.zeros_like(gen)
    miss_m = np.zeros_like(gen)
    for cpt in comps:
        m = lbl == cpt["label"]
        inner = ndi.binary_erosion(m, structure=I.disk(0.4 / res))
        if inner.sum() < 10:
            inner = m
        rf = float(orth[inner].mean())
        gf = float(wm["green"][inner].mean())
        r, c = cpt["rc"]
        verdict = "absent_on_ortho" if rf >= 0.6 else ("partial" if rf >= 0.3 else "present")
        (bad_m if verdict == "absent_on_ortho" else ok_m)[m] = True
        gen_islands.append({"xy": [wm["x0"] + (c + 0.5) * res, wm["y1"] - (r + 0.5) * res], "area_m2": cpt["area_m2"],
                            "ortho_road_frac": round(rf, 3), "ortho_green_frac": round(gf, 3), "verdict": verdict})
    o_closed = ndi.binary_closing(np.pad(orth, int(close_m / res) + 2), structure=st)[
        int(close_m / res) + 2:-int(close_m / res) - 2, int(close_m / res) + 2:-int(close_m / res) - 2]
    o_closed |= ndi.binary_fill_holes(orth)
    osep = o_closed & ~orth
    comps, lbl = _components(osep, res, 6.0)
    missing = []
    for cpt in comps:
        m = lbl == cpt["label"]
        gfrac = float(wm["green"][m].mean())
        on_gen = float(gen[m].mean())
        if on_gen < 0.6 or (gfrac < 0.3 and cpt["area_m2"] < 25):
            continue          # not on our carriageway, or a car / shadow
        r, c = cpt["rc"]
        miss_m[m] = True
        missing.append({"xy": [wm["x0"] + (c + 0.5) * res, wm["y1"] - (r + 0.5) * res], "area_m2": cpt["area_m2"],
                        "green_frac": round(gfrac, 3), "on_gen_carriageway": round(on_gen, 3)})
    return gen_islands, missing, {"ok": ok_m, "bad": bad_m}, miss_m


def area_diffs(wm, min_m2=8.0, band_m=6.0):
    res = wm["res"]
    band = ndi.binary_dilation(wm["gen"], structure=I.disk(band_m / res))
    gen_only = wm["gen"] & ~wm["ortho"]
    gen_only = ndi.binary_opening(gen_only, structure=I.disk(0.5 / res))
    o_only = wm["ortho"] & ~wm["gen"] & ~wm["other"] & band
    o_only = ndi.binary_opening(o_only, structure=I.disk(0.5 / res))
    out = []
    for kind, m in (("gen_only", gen_only), ("ortho_only", o_only)):
        comps, _ = _components(m, res, min_m2)
        for cpt in comps:
            r, c = cpt["rc"]
            out.append({"kind": kind, "xy": [wm["x0"] + (c + 0.5) * res, wm["y1"] - (r + 0.5) * res],
                        "area_m2": cpt["area_m2"]})
    return sorted(out, key=lambda d: -d["area_m2"]), gen_only, o_only


# ------------------------------------------------------------------ (c) lanes
def osm_lane_truth(tags):
    t = {k: tags.get(k) for k in ("lanes", "lanes:forward", "lanes:backward", "oneway", "turn:lanes",
                                  "turn:lanes:forward", "turn:lanes:backward", "junction") if tags.get(k)}
    t["extra"] = {k: tags[k] for k in EXTRA_LANE_TAGS if k in tags}
    return t


def lane_compare(ctx: Ctx, eid):
    sec = ctx.net.sections[eid]
    w = ctx.ways.get(way_of(eid))
    tags = w["tags"] if w else {}
    tr = osm_lane_truth(tags)
    issues = []
    lanes_osm = int(float(tags["lanes"])) if tags.get("lanes", "").replace(".", "").isdigit() else None
    if lanes_osm is not None and lanes_osm != sec.lanes:
        issues.append({"kind": "lanes_mismatch", "osm": lanes_osm, "gen": sec.lanes,
                       "cause": f"override {sec.provenance.get('authored_override')}" if sec.provenance.get(
                           "authored_override") else "roads.network.edge_section"})
    one = tags.get("oneway") in ("yes", "-1", "1") or tags.get("junction") in ("roundabout", "circular") or \
        tags.get("highway") in ("motorway", "motorway_link")
    if not one and lanes_osm:
        f, b = tags.get("lanes:forward"), tags.get("lanes:backward")
        if f and b and (int(f), int(b)) != (sec.lanes_fwd, sec.lanes_bwd):
            issues.append({"kind": "direction_split_mismatch", "osm": [int(f), int(b)],
                           "gen": [sec.lanes_fwd, sec.lanes_bwd], "cause": "roads.network.edge_section"})
        if not (f and b) and lanes_osm % 2 == 1:
            issues.append({"kind": "odd_two_way_split_guessed", "osm": lanes_osm,
                           "gen": [sec.lanes_fwd, sec.lanes_bwd], "cause": "roads.network.edge_section (default split)"})
    for key, gl in (("turn:lanes", sec.turn_fwd if one else None), ("turn:lanes:forward", sec.turn_fwd),
                    ("turn:lanes:backward", sec.turn_bwd)):
        v = tags.get(key)
        if not v or (key == "turn:lanes" and not one):
            continue
        n_t = len(v.split("|"))
        n_l = sec.lanes if key == "turn:lanes" else (sec.lanes_fwd if key.endswith("forward") else sec.lanes_bwd)
        if n_t != n_l:
            issues.append({"kind": "turn_lanes_count_mismatch_arrows_dropped", "tag": key, "osm": v, "lanes": n_l,
                           "cause": "roads.markings._build_markings (len(lanes) != len(tl) -> continue)"})
    if tr["extra"]:
        issues.append({"kind": "lane_tags_ignored_by_generator", "tags": tr["extra"],
                       "cause": "roadgraph.RAW_TAGS / roads.network.edge_section (placement, width:lanes, change:lanes "
                                "not read)"})
    if not tags.get("lanes"):
        issues.append({"kind": "lanes_default", "gen": sec.lanes, "cause": "roadgraph.edge_attrs default (OSM no lanes)"})
    return {"edge": eid, "way": way_of(eid), "highway": sec.highway, "name": tags.get("name"),
            "gen": {"lanes": sec.lanes, "fwd": sec.lanes_fwd, "bwd": sec.lanes_bwd, "oneway": sec.oneway,
                    "turn_fwd": sec.turn_fwd, "turn_bwd": sec.turn_bwd, "lane_w": sec.lane_w, "width": sec.width,
                    "width_src": sec.width_src},
            "osm": tr, "issues": issues}


def ortho_lane_count(ctx: Ctx, c, s0, s1, edges_found):
    """Count painted lane separators on hi-res ortho between detected carriageway edges; mode over 24 m strips."""
    if s1 - s0 < 16:
        return None
    counts = []
    strip = 24.0
    s = s0 + 4
    while s + strip <= s1 - 4 + 1e-6:
        st = np.arange(s, s + strip, 0.25)
        P = c.line.point(st)
        hw_max = float(c.hw_at(st).max())
        span = hw_max + OUT_MARGIN
        x0, y0 = P.min(0) - span
        x1, y1 = P.max(0) + span
        bbox = (x0 + ctx.ox, y0 + ctx.oy, x1 + ctx.ox, y1 + ctx.oy)
        if not ctx.ortho.has_hr(bbox) or any(ctx.under_deck(p) for p in P[::20]):
            s += strip
            continue
        res = 0.08
        rgb, _ = ctx.ortho.window(bbox, res)
        lab = I.rgb2lab(rgb)
        gm = G.rasterize(ctx.g.tris, x0, y1, res, rgb.shape[:2])
        model = I.road_model(lab, ndi.binary_erosion(gm, structure=I.disk(1.0 / res)))
        if model is None:
            s += strip
            continue
        bright = ((lab[..., 0] > model["L_med"] + I.PAINT_DL) & (np.abs(lab[..., 2]) < 20)).astype(np.float32)
        t, nrm = c.line.frame(st)
        lat = np.arange(-span, span, 0.04)
        XY = P[:, None, :] + lat[None, :, None] * nrm[:, None, :]
        cols = (XY[..., 0] - x0) / res - 0.5
        rows = (y1 - XY[..., 1]) / res - 0.5
        b = ndi.map_coordinates(bright, [rows, cols], order=0, mode="nearest")
        frac = b.mean(0)                                      # share of the strip length painted at this lateral
        # local edges from the edge profiles in this strip
        ed = [e for e in edges_found if s <= e["s"] <= s + strip]
        L = [e["hw"] + e["L"] for e in ed if e.get("L") is not None]
        R = [e["hw"] + e["R"] for e in ed if e.get("R") is not None]
        if len(L) < 4 or len(R) < 4:
            s += strip
            continue
        eL, eR = float(np.median(L)), -float(np.median(R))
        sm = ndi.uniform_filter1d(frac, 3)
        pk = (sm > 0.14) & (sm >= np.roll(sm, 1)) & (sm >= np.roll(sm, -1))
        pos = lat[pk]
        # merge peaks closer than 0.5 m (double lines, wide lines)
        merged = []
        for p in pos:
            if merged and p - merged[-1][-1] < 0.5:
                merged[-1].append(p)
            else:
                merged.append([p])
        lines = [float(np.mean(m)) for m in merged]
        inner = [p for p in lines if eR + 0.8 < p < eL - 0.8]
        width = eL - eR
        counts.append({"s": round(s + strip / 2, 1), "n_sep": len(inner), "lines": [round(p, 2) for p in inner],
                       "width": round(width, 2), "frac_max": round(float(sm.max()), 3)})
        s += strip
    if not counts:
        return None
    lanes = Counter(cn["n_sep"] + 1 for cn in counts)
    mode, n = lanes.most_common(1)[0]
    return {"lanes": mode, "agree": round(n / len(counts), 2), "strips": counts}


# ------------------------------------------------------------------ (e) roundabouts
def fit_circle(xy):
    x, y = xy[:, 0], xy[:, 1]
    A = np.c_[2 * x, 2 * y, np.ones(len(x))]
    b = x * x + y * y
    (cx, cy, k), *_ = np.linalg.lstsq(A, b, rcond=None)
    r = math.sqrt(max(k + cx * cx + cy * cy, 0))
    resid = np.hypot(x - cx, y - cy) - r
    return np.array([cx, cy]), r, float(np.abs(resid).max())


def roundabouts(ctx: Ctx):
    """Group OSM roundabout ways into rings (shared nodes) and compare with generated ring chains."""
    rb = [w for w in ctx.osm["ways"] if w["tags"].get("junction") in ("roundabout", "circular")
          and w["tags"].get("highway") in DRIVABLE]
    # union-find on shared nodes
    parent = {w["id"]: w["id"] for w in rb}

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    by_node = defaultdict(list)
    for w in rb:
        for n in w["nodes"]:
            by_node[n].append(w["id"])
    for ids in by_node.values():
        for a in ids[1:]:
            parent[find(a)] = find(ids[0])
    groups = defaultdict(list)
    for w in rb:
        groups[find(w["id"])].append(w)
    drv = [w for w in ctx.osm["ways"] if w["tags"].get("highway") in DRIVABLE
           and w["tags"].get("service") not in ("parking_aisle",)]
    out = []
    for gid, ws in sorted(groups.items()):
        pts = np.concatenate([np.array(w["geometry"]) for w in ws]) - [ctx.ox, ctx.oy]
        cen, r, resid = fit_circle(pts)
        b = ctx.region["bbox"]
        if not (b["xmin"] - ctx.ox < cen[0] < b["xmax"] - ctx.ox and b["ymin"] - ctx.oy < cen[1] < b["ymax"] - ctx.oy):
            continue
        ring_nodes = set(n for w in ws for n in w["nodes"])
        ring_ids = {w["id"] for w in ws}
        entries, exits, both = [], [], []
        for w in drv:
            if w["id"] in ring_ids:
                continue
            for end, n in (("first", w["nodes"][0]), ("last", w["nodes"][-1])):
                if n not in ring_nodes:
                    continue
                ow = w["tags"].get("oneway")
                rec = {"way": w["id"], "node": n, "highway": w["tags"].get("highway"), "name": w["tags"].get("name")}
                if ow in ("yes", "1"):
                    (entries if end == "last" else exits).append(rec)
                elif ow == "-1":
                    (entries if end == "first" else exits).append(rec)
                else:
                    both.append(rec)
            # ways passing through a ring node mid-way (rare)
            for n in w["nodes"][1:-1]:
                if n in ring_nodes:
                    both.append({"way": w["id"], "node": n, "highway": w["tags"].get("highway"), "mid": True})
        lanes_osm = sorted({w["tags"].get("lanes") for w in ws if w["tags"].get("lanes")})
        # generated: ring chains whose edges belong to these ways
        gch = [c for c in ctx.net.chains if c.roundabout and any(way_of(e) in ring_ids for e, _ in c.edges)]
        if gch:
            gp = np.concatenate([c.line.p for c in gch])
            gcen, gr, _ = fit_circle(gp)
            glanes = sorted({ctx.net.sections[e].lanes for c in gch for e, _ in c.edges if way_of(e) in ring_ids})
            ghw = sorted({round(float(c.hw.mean()) * 2, 2) for c in gch})
        else:
            gcen, gr, glanes, ghw = None, None, [], []
        # generated arms attached to ring junctions
        ring_chain_ids = {c.id for c in gch}
        arms = set()
        for j in ctx.g.world.junctions:
            if any(a.chain.id in ring_chain_ids for a in j.arms):
                for a in j.arms:
                    if a.chain.id not in ring_chain_ids:
                        arms.add(tuple(sorted({way_of(e) for e, _ in a.chain.edges})))
        osm_arm_ways = {r_["way"] for r_ in entries + exits + both}
        gen_arm_ways = {w_ for t in arms for w_ in t}
        out.append({"ring_ways": sorted(ring_ids), "center_en": [round(float(v), 2) for v in cen],
                    "radius_osm_m": round(r, 2), "ring_fit_resid_m": round(resid, 2),
                    "radius_gen_m": round(gr, 2) if gr else None,
                    "center_shift_m": round(float(np.hypot(*(gcen - cen))), 2) if gcen is not None else None,
                    "lanes_osm": lanes_osm, "lanes_gen": glanes, "ring_width_gen_m": ghw,
                    "entries": entries, "exits": exits, "two_way_arms": both,
                    "arms_missing_in_gen": sorted(osm_arm_ways - gen_arm_ways)})
    return out


# ------------------------------------------------------------------ (g) connectivity
def connectivity(ctx: Ctx):
    graph_ways = {way_of(eid) for eid in ctx.net.sections}
    b = ctx.region["bbox"]
    tile = Polygon([(b["xmin"], b["ymin"]), (b["xmax"], b["ymin"]), (b["xmax"], b["ymax"]), (b["xmin"], b["ymax"])])
    missing = []
    n_drv = 0
    for w in ctx.osm["ways"]:
        hw = w["tags"].get("highway")
        if hw not in DRIVABLE:
            continue
        ls = LineString(w["geometry"])
        if not ls.intersects(tile):
            continue
        n_drv += 1
        if w["id"] in graph_ways:
            continue
        clipped = ls.intersection(tile)
        missing.append({"way": w["id"], "highway": hw, "service": w["tags"].get("service"),
                        "name": w["tags"].get("name"), "access": w["tags"].get("access"),
                        "length_in_tile_m": round(clipped.length, 1),
                        "xy": [round(v - o, 1) for v, o in zip(clipped.interpolate(0.5, normalized=True).coords[0],
                                                               (ctx.ox, ctx.oy))]})
    return {"osm_drivable_ways_in_tile": n_drv, "missing_in_graph": missing}


def node_arm_check(ctx: Ctx, node_ids):
    """OSM degree (drivable way incidences) vs generated junction arm count at given OSM nodes."""
    inc = defaultdict(int)
    graph_ways = {way_of(eid) for eid in ctx.net.sections}
    for w in ctx.osm["ways"]:
        if w["tags"].get("highway") not in DRIVABLE or w["id"] not in graph_ways:
            continue
        ns = w["nodes"]
        for i, n in enumerate(ns):
            inc[n] += (1 if i in (0, len(ns) - 1) else 2)
    jn = {}
    for j in ctx.g.world.junctions:
        for n in j.nodes:
            jn[n] = j
    out = []
    for n in node_ids:
        nid = int(str(n).lstrip("n"))
        j = jn.get(n) or jn.get(f"n{nid}")
        gen_arms = None
        if j is not None:
            gen_arms = sum(1 for a in j.arms if a.node in (n, f"n{nid}"))
        out.append({"node": n, "osm_degree": inc.get(nid, 0), "gen_arms_at_node": gen_arms,
                    "junction": j.id if j else None})
    return out
