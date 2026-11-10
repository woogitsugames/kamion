r"""Road fidelity report (ADR 0075): generated roads vs OSM / GUGiK orthophoto / BDOT10k.

    uv run --project tools/worldgen tools/worldgen/fidelity/run.py --region bialystok-industrial-c [--fetch] [--no-tile]

Inputs: Data/Regions/<id>/{roads.graph.json, overrides.yaml, route_start.json}, OSM extract (manifest), ortho sheet
0.25 m + hi-res WMS cells (Data/raw/refs/gugik-ortho-hr, `--fetch` downloads missing cells along the route).
Outputs: Data/Regions/<id>/generated/fidelity_qa.json (in git; the pytest ratchet reads it),
         artifacts/fidelity-r9/{overlays/*.jpg, DIFFS.md, fidelity_summary.json}.
Deterministic for the same inputs (no randomness; k-means with fixed init).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fidelity import gen as G  # noqa: E402
from fidelity import imaging as I  # noqa: E402
from fidelity import metrics as Mx  # noqa: E402
from fidelity import ortho as O  # noqa: E402
from fidelity import osm_truth  # noqa: E402
from fidelity import overlays as OV  # noqa: E402
from roads import markings as MK  # noqa: E402
from roads import pipeline  # noqa: E402

REPO = pipeline.REPO
# route sites: (id, name, centre E/N local, half window m)
ROUTE_SITES = [
    ("01_gate", "Brama Kwadrat Park (start)", (712, -412), 55),
    ("02_s230_approach", "Dojazd do Ronda Bieżeństwa (s 230-300)", (612, -612), 55),
    ("03_rondo_biezenstwa", "Rondo Pamięci Bieżeństwa (dwupoziomowe)", (555, -705), 120),
    ("04_s610_ramps", "Andersa: łącznice przy s 610", (322, -578), 60),
    ("05_s900", "Andersa s 900 (n1881569071)", (62, -442), 70),
    ("06_s1060_merge", "Andersa s 1060-1130 (włączenie)", (-88, -348), 60),
    ("07_s1270", "Andersa s 1270 (n10015785253)", (-221, -234), 55),
    ("08_signals", "Skrzyżowanie z sygnalizacją s 1355-1415", (-322, -172), 70),
    ("09_s1600", "Andersa s 1600 (przed Rondem Putry)", (-463, -11), 55),
    ("10_rondo_putry", "Rondo Putry (dwupoziomowe)", (-548, 62), 125),
    ("11_dk8", "DK8/DK19 za Rondem Putry (s 1780-1950)", (-556, 215), 100),
]


def sha_file(p: Path):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def route_edges(rdir):
    r = json.loads((rdir / "route_start.json").read_text(encoding="utf-8"))
    seen, order = set(), []
    for e in r["edge"]:
        if e not in seen:
            seen.add(e)
            order.append(e)
    return r, order


def chain_span_of_edge(c, eid):
    L_raw = c.raw_spans[-1][1]
    f = c.line.length / max(L_raw, 1e-9)
    for s0, s1, e, _ in c.raw_spans:
        if e == eid:
            return s0 * f, s1 * f
    return None


def yards_polys(rdir, origin):
    from shapely.geometry import Polygon
    p = rdir / "generated" / "streetscape_sources.json"
    if not p.exists():
        return []
    src = json.loads(p.read_text(encoding="utf-8"))
    out = []
    for f in src["bdot10k"].get("OT_PTPL_A", []):
        out.append(Polygon(np.array(f["geometry"]["coordinates"][0]) - origin))
    for a in src["osm"].get("areas", []):
        if a["tags"].get("amenity") == "parking":
            out.append(Polygon(np.array(a["geometry"]["coordinates"][0]) - origin))
    return [q.buffer(0) for q in out if q.is_valid or q.buffer(0).area > 0]


def lane_into_island(ctx, gmask, gsep, x0, y1, res, ahead=20.0):
    """Inbound lanes at every junction arm: march straight ahead from the arm end; a lane whose path leaves the
    carriageway into a generated separation within 12 m is a 'lane into island' candidate."""
    net = ctx.net
    arrows_by = {}
    for a in ctx.g.arrows:
        arrows_by.setdefault(a["chain"], []).append(a)
    out = []

    def at(m, p):
        i = int((y1 - p[1]) / res)
        j = int((p[0] - x0) / res)
        if 0 <= i < m.shape[0] and 0 <= j < m.shape[1]:
            return bool(m[i, j])
        return False
    for jn in ctx.g.world.junctions:
        for ai, a in enumerate(jn.arms):
            c = a.chain
            if c.meta.get("absorbed") or a.is_ring():
                continue
            if jn.roundabout:
                continue      # entering a roundabout the lane follows the ring: straight ahead is the central island
            inb = a.inbound_dirn()
            t = jn.trims[ai]
            if t >= a.L - 2:
                continue
            sec = c.section(a.s(min(t + 1.0, a.L)), net.sec_list)
            hw = float(c.hw_at(a.s(t)))
            dirn = int(c.dirn[c.idx(a.s(t))]) or 1
            _, _, cen = MK.lane_layout(sec, hw, dirn)
            if sec.oneway:
                if inb != 1:
                    continue
                lanes = cen["fwd"]
                turns = sec.turn_fwd
            else:
                lanes = cen["bwd"] if a.end == "a" else cen["fwd"]
                turns = sec.turn_bwd if a.end == "a" else sec.turn_fwd
            d_in = -a.direction(t)
            for k, lat in enumerate(lanes):
                p0 = c.line.offset_point(a.s(t), lat)
                hit = None
                for d in np.arange(0.5, ahead, 0.5):
                    p = p0 + d_in * d
                    if not at(gmask, p):
                        hit = (d, p)
                        break
                if hit is None or hit[0] > 12.0 or not at(gsep, hit[1]):
                    continue
                tl = turns[k] if turns and len(turns) == len(lanes) else None
                out.append({"junction": jn.id, "chain": c.id, "lane_index_from_left": k, "turn": tl,
                            "dist_m": float(hit[0]), "xy": [round(float(v), 2) for v in hit[1]],
                            "lane_start_xy": [round(float(v), 2) for v in p0]})
    return out


def arrow_on_ortho(ctx, arr, res=0.08):
    """Paint share in a 5 x 0.9 m lane box at the generated arrow and the best box +-12 m along the lane."""
    xy = np.array(arr["xy"])
    h = np.array(arr["heading"])
    h = h / (np.linalg.norm(h) + 1e-9)
    n = np.array([-h[1], h[0]])
    half = 16.0
    bbox = (xy[0] - half + ctx.ox, xy[1] - half + ctx.oy, xy[0] + half + ctx.ox, xy[1] + half + ctx.oy)
    if not ctx.ortho.has_hr(bbox):
        return None
    rgb, _ = ctx.ortho.window(bbox, res)
    lab = I.rgb2lab(rgb)
    gm = G.rasterize(ctx.g.tris, xy[0] - half, xy[1] + half, res, rgb.shape[:2])
    from scipy import ndimage as ndi
    model = I.road_model(lab, I.erode(gm, 1.0 / res))
    if model is None:
        return None
    paint = (lab[..., 0] > model["L_med"] + I.PAINT_DL).astype(np.float32)

    def box_frac(off):
        u = np.arange(0, 5.0, 0.1)
        v = np.arange(-0.45, 0.45 + 1e-9, 0.1)
        P = xy + (off + u)[:, None, None] * h + v[None, :, None] * n
        cols = (P[..., 0] - (xy[0] - half)) / res - 0.5
        rows = ((xy[1] + half) - P[..., 1]) / res - 0.5
        return float(ndi.map_coordinates(paint, [rows, cols], order=0, mode="constant").mean())
    here = box_frac(0.0)
    offs = np.arange(-12, 12.01, 0.5)
    fr = np.array([box_frac(o) for o in offs])
    k = int(fr.argmax())
    return {"paint_here": round(here, 3), "best_frac": round(float(fr[k]), 3), "best_offset_m": float(offs[k]),
            "present": bool(fr[k] >= 0.22)}


def stopline_on_ortho(ctx, tr, res=0.08):
    """Transverse paint across the stop-line span: offset (m, + = downstream) of the strongest transverse band."""
    c = next((c for c in ctx.net.chains if c.id == tr["chain"]), None)
    if c is None or "lat0" not in tr and "lat" not in tr:
        return None
    s_mid = tr["s"]
    lat0, lat1 = (tr["lat0"], tr["lat1"]) if "lat0" in tr else (tr["lat"] - 1.5, tr["lat"] + 1.5)
    xy = c.line.offset_point(s_mid, 0.5 * (lat0 + lat1))
    half = 16.0
    bbox = (xy[0] - half + ctx.ox, xy[1] - half + ctx.oy, xy[0] + half + ctx.ox, xy[1] + half + ctx.oy)
    if not ctx.ortho.has_hr(bbox):
        return None
    rgb, _ = ctx.ortho.window(bbox, res)
    lab = I.rgb2lab(rgb)
    gm = G.rasterize(ctx.g.tris, xy[0] - half, xy[1] + half, res, rgb.shape[:2])
    from scipy import ndimage as ndi
    model = I.road_model(lab, I.erode(gm, 1.0 / res))
    if model is None:
        return None
    paint = (lab[..., 0] > model["L_med"] + I.PAINT_DL).astype(np.float32)
    ds = np.arange(-10, 10.01, 0.1)
    lats = np.linspace(min(lat0, lat1), max(lat0, lat1), 30)
    S, Lt = np.meshgrid(np.clip(s_mid + ds, 0, c.length), lats, indexing="ij")
    P = c.line.offset_point(S.ravel(), Lt.ravel()).reshape(S.shape + (2,))
    cols = (P[..., 0] - (xy[0] - half)) / res - 0.5
    rows = ((xy[1] + half) - P[..., 1]) / res - 0.5
    prof = ndi.map_coordinates(paint, [rows, cols], order=0, mode="constant").mean(1)
    prof = ndi.uniform_filter1d(prof, 3)
    k = int(prof.argmax())
    return {"band_frac": round(float(prof[k]), 3), "offset_m": round(float(ds[k]), 2), "present": bool(prof[k] >= 0.3)}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--fetch", action="store_true", help="download missing hi-res ortho cells (GUGiK WMS)")
    ap.add_argument("--no-tile", action="store_true", help="route only (skip the rest of the tile)")
    ap.add_argument("--art", default="artifacts/fidelity-r9")
    a = ap.parse_args(argv)
    t0 = time.time()
    log = lambda *x: print(f"[fidelity {time.time() - t0:6.1f}s]", *x, flush=True)  # noqa: E731
    reg = pipeline.load_region(a.region)
    rdir = pipeline.REGIONS / a.region
    art = REPO / a.art
    (art / "overlays").mkdir(parents=True, exist_ok=True)
    osm = osm_truth.extract(reg)
    log(f"osm: {len(osm['ways'])} ways, snapshot {osm['source']['snapshot']}")
    route, r_edges = route_edges(rdir)
    ortho = O.Ortho(reg)
    if a.fetch:
        from shapely.geometry import LineString, Point
        ox, oy = reg["origin"]["x"], reg["origin"]["y"]
        P = np.array(route["points_en"]) + [ox, oy]
        geoms = [LineString(P).buffer(45)] + [Point(c[0] + ox, c[1] + oy).buffer(h) for _, _, c, h in ROUTE_SITES]
        O.fetch_cells(reg, O.cells_for(reg, geoms), log=log)
        ortho = O.Ortho(reg)
    g = G.build(a.region)
    log(f"generated: {len(g.tris)} carriageway tris, {len(g.arrows)} arrows")
    ctx = Mx.Ctx(reg, g, osm, ortho, np.array(route["points_en"]))
    origin = np.array(g.origin)
    yards = yards_polys(rdir, origin)

    # ---------------- (a) axis
    axis, graph_vs_osm = Mx.axis_metrics(ctx)
    r_axis = [axis[e] for e in r_edges if e in axis and axis[e].get("n")]
    log("axis done")

    # ---------------- (b) edges on route chains (hi-res) + tile (sheet)
    edge_rows = {}
    for eid in r_edges:
        c = ctx.chain_of_edge.get(eid)
        if c is None:
            continue
        sp = chain_span_of_edge(c, eid)
        s0, s1 = max(sp[0], c.t_a), min(sp[1], c.length - c.t_b)
        edge_rows[eid] = Mx.chain_edge_profiles(ctx, c, s0, s1) if s1 - s0 > 2 else []
    log("route edge profiles done")
    tile_rows = {}
    if not a.no_tile:
        for c in ctx.net.chains:
            if c.meta.get("absorbed"):
                continue
            hwset = {ctx.net.sections[e].highway for e, _ in c.edges}
            if hwset <= {"service", "living_street", "track", "path"}:
                continue
            if any(e in edge_rows for e, _ in c.edges):
                continue
            s0, s1 = c.t_a, c.length - c.t_b
            if s1 - s0 > 4:
                tile_rows[c.id] = Mx.chain_edge_profiles(ctx, c, s0, s1, step=4.0)
        log(f"tile edge profiles done ({len(tile_rows)} chains)")

    def edge_summary(rows):
        offs, signed, rel, rel_s, n_st, n_valid = [], [], [], [], 0, 0
        for r in rows:
            if r.get("skip"):
                continue
            n_st += 1
            for k in ("L", "R"):
                if r.get(k) is not None:
                    offs.append(abs(r[k]))
                    signed.append(r[k])
                    n_valid += 1
                    if r.get(k + "_green") and not r.get(k + "_walk"):
                        rel.append(abs(r[k]))
                        rel_s.append(r[k])
        out = Mx.stats(rel)                       # primary: kerb/verge edges (road -> vegetation), see ADR 0075
        out["signed_p50"] = Mx.pct(rel_s, 50)
        out["all_sides"] = Mx.stats(offs)         # includes road -> sidewalk / parking (classifier-ambiguous)
        out["stations"] = n_st
        out["valid_sides"] = len(rel)
        out["detected_sides"] = n_valid
        return out
    route_edge_all = [r for rows in edge_rows.values() for r in rows]
    tile_edge_all = [r for rows in tile_rows.values() for r in rows]

    # ---------------- (c) lanes
    lanes_all = {eid: Mx.lane_compare(ctx, eid) for eid in sorted(ctx.net.sections)}
    route_lanes = []
    for eid in r_edges:
        lc = lanes_all[eid]
        c = ctx.chain_of_edge.get(eid)
        sp = chain_span_of_edge(c, eid) if c else None
        oc = None
        if c is not None and sp:
            oc = Mx.ortho_lane_count(ctx, c, max(sp[0], c.t_a), min(sp[1], c.length - c.t_b), edge_rows.get(eid, []))
        lanes_osm = lc["osm"].get("lanes")
        truth, tsrc = None, None
        if lanes_osm and lanes_osm.isdigit():
            truth, tsrc = int(lanes_osm), "osm"
        elif oc and oc["agree"] >= 0.6 and (oc["lanes"] >= 2 or lc["gen"]["oneway"]):
            # an unmarked two-way road shows no separator line: paint cannot tell 1 from 2 lanes there
            truth, tsrc = oc["lanes"], "ortho"
        lc = dict(lc, ortho=oc, truth=truth, truth_src=tsrc,
                  length_m=round(sp[1] - sp[0], 1) if sp else None,
                  match=(truth == lc["gen"]["lanes"]) if truth is not None else None,
                  ortho_vs_osm=(oc["lanes"] == truth) if (oc and tsrc == "osm" and oc["agree"] >= 0.6) else None)
        route_lanes.append(lc)
    log("lanes done")

    # ---------------- sites: IoU, islands, area diffs, overlays
    full_res = 0.25
    b = reg["bbox"]
    gx0, gy1 = b["xmin"] - origin[0], b["ymax"] - origin[1]
    W = int(b["width_m"] / full_res)
    gmask_tile = G.rasterize(g.tris, gx0, gy1, full_res, (W, W))
    from scipy import ndimage as ndi
    r7 = int(7.0 / full_res)
    gsep_tile = I.close(gmask_tile, r7)
    gsep_tile = (gsep_tile | ndi.binary_fill_holes(gmask_tile)) & ~gmask_tile
    lii = lane_into_island(ctx, gmask_tile, gsep_tile, gx0, gy1, full_res)
    log(f"lane-into-island candidates: {len(lii)}")

    def classify_lii(item):
        half = 12.0
        wm = Mx.window_masks(ctx, item["xy"], half, res=0.1, yards=yards, walk_tris=g.walk_tris)
        i = int((wm["y1"] - item["xy"][1]) / wm["res"])
        j = int((item["xy"][0] - wm["x0"]) / wm["res"])
        r = int(1.0 / wm["res"])
        win = wm["ortho"][max(0, i - r):i + r + 1, max(0, j - r):j + r + 1]
        grn = wm["green"][max(0, i - r):i + r + 1, max(0, j - r):j + r + 1]
        item["ortho_road_frac"] = round(float(win.mean()), 3)
        item["ortho_green_frac"] = round(float(grn.mean()), 3)
        item["ortho_src"] = wm["src"]
        item["verdict"] = "generator_island_on_real_road" if win.mean() >= 0.6 else (
            "real_island_lane_must_turn" if win.mean() < 0.3 else "ambiguous")
        return item
    route_line = ctx.route
    from shapely.geometry import Point
    for it in lii:
        it["on_route"] = bool(route_line.distance(Point(it["lane_start_xy"])) < 6.0)
        classify_lii(it)

    sites = []
    for sid, name, cen, half in ROUTE_SITES:
        wm = Mx.window_masks(ctx, cen, half, res=0.1, yards=yards, walk_tris=g.walk_tris)
        io = Mx.iou(wm, band_m=4.0)
        gi, miss, imask, mmask = Mx.separations(wm)
        for x in gi + miss:
            x["route_dist_m"] = round(route_line.distance(Point(x["xy"])), 1)
        diffs, gen_only, o_only = Mx.area_diffs(wm)
        x0, y1, res = wm["x0"], wm["y1"], wm["res"]
        x1, y0 = x0 + wm["gen"].shape[1] * res, y1 - wm["gen"].shape[0] * res
        inwin = lambda p: x0 <= p[0] <= x1 and y0 <= p[1] <= y1  # noqa: E731
        det = []
        for eid, rows in edge_rows.items():
            c = ctx.chain_of_edge[eid]
            for r in rows:
                for k, sg in (("L", 1), ("R", -1)):
                    if r.get(k) is not None:
                        p = c.line.offset_point(r["s"], sg * (r["hw"] + r[k]))
                        if inwin(p):
                            det.append(tuple(p))
        notes = []
        for k, isl in enumerate([x for x in gi if x["verdict"] == "absent_on_ortho"]):
            notes.append({"xy": isl["xy"], "label": f"I{k + 1}"})
        site_lii = [x for x in lii if inwin(x["xy"])]
        for k, x in enumerate(site_lii):
            notes.append({"xy": x["xy"], "label": f"L{k + 1}:{x['turn'] or '?'}"})
        site_arrows = [ar for ar in g.arrows if ar["emitted"] and inwin(ar["xy"])]
        for ar in site_arrows:
            ar["ortho"] = arrow_on_ortho(ctx, ar)
        site_stops = [tr for tr in g.transverse if inwin(tr["xy"]) and tr.get("kind") in ("P-14", "P-13")]
        seen_stop = set()
        stops = []
        for tr in site_stops:
            key = (tr["chain"], round(tr["s"], 0))
            if key in seen_stop:
                continue
            seen_stop.add(key)
            stops.append(dict(kind=tr["kind"], chain=tr["chain"], s=tr["s"], xy=tr["xy"],
                              ortho=stopline_on_ortho(ctx, tr)))
        title = (f"{sid} {name} | IoU {io['iou']:.3f} | gen islands {len(gi)} "
                 f"(absent on ortho {sum(x['verdict'] == 'absent_on_ortho' for x in gi)}) | ortho islands missing "
                 f"{len(miss)} | lane->island {len(site_lii)}")
        f = art / "overlays" / f"{sid}.jpg"
        OV.render(f, wm, g, title, imask, mmask, gen_only, o_only, det_pts=det, notes=notes)
        sites.append({"id": sid, "name": name, "center_en": list(cen), "half_m": half, "ortho_src": wm["src"],
                      "iou": io, "gen_islands": gi, "ortho_islands_missing_in_gen": miss,
                      "area_diffs_top": diffs[:12], "lane_into_island": site_lii,
                      "arrows": [{k: v for k, v in ar.items() if k != "emitted"} for ar in site_arrows],
                      "stop_lines": stops, "overlay": str(f.relative_to(REPO)).replace("\\", "/")})
        log(f"site {sid}: IoU {io['iou']}, islands {len(gi)}, missing {len(miss)}")

    # rest of tile: junction windows ranked by IoU (sheet 0.25 m)
    tile_sites = []
    if not a.no_tile:
        for jn in ctx.g.world.junctions:
            if route_line.distance(Point(jn.center)) < 60:
                continue
            classes = {a_.cls(ctx.net.sec_list) for a_ in jn.arms}
            if classes <= {"D"}:
                continue
            wm = Mx.window_masks(ctx, jn.center, 35.0, res=0.25, yards=yards, walk_tris=g.walk_tris)
            if wm["model"] is None:
                continue
            io = Mx.iou(wm, band_m=4.0)
            gi, miss, _, _ = Mx.separations(wm)
            tile_sites.append({"junction": jn.id, "center_en": [round(float(v), 1) for v in jn.center],
                               "iou": io, "gen_islands_absent_on_ortho": sum(x["verdict"] == "absent_on_ortho" for x in gi),
                               "ortho_islands_missing": len(miss), "roundabout": jn.roundabout,
                               "signalized": jn.signalized})
        tile_sites.sort(key=lambda d: d["iou"]["iou"])
        for k, ts in enumerate(tile_sites[:6]):
            wm = Mx.window_masks(ctx, ts["center_en"], 45.0, res=0.1, yards=yards, walk_tris=g.walk_tris)
            gi, miss, imask, mmask = Mx.separations(wm)
            diffs, gen_only, o_only = Mx.area_diffs(wm)
            io = Mx.iou(wm, band_m=4.0)
            f = art / "overlays" / f"tile_{k + 1:02d}_{ts['junction'].replace(':', '_')}.jpg"
            OV.render(f, wm, g, f"tile worst #{k + 1} {ts['junction']} | IoU {io['iou']:.3f}", imask, mmask,
                      gen_only, o_only)
            ts["overlay"] = str(f.relative_to(REPO)).replace("\\", "/")
        log(f"tile junction windows: {len(tile_sites)}")

    # ---------------- (e) roundabouts, (g) connectivity
    rbs = Mx.roundabouts(ctx)
    conn = Mx.connectivity(ctx)
    route_nodes = route.get("graph_nodes", [])
    arms = Mx.node_arm_check(ctx, route_nodes)
    log("roundabouts / connectivity done")

    # ---------------- summary
    def lanes_ok(rows):
        ver = [r for r in rows if r["match"] is not None]
        return {"segments": len(rows), "verified": len(ver), "match": sum(r["match"] for r in ver),
                "mismatch": [r["edge"] for r in ver if not r["match"]],
                "unverified": [r["edge"] for r in rows if r["match"] is None]}
    route_ax = Mx.stats([x for e in r_edges if e in axis for x in []])
    # pooled axis distances on the route (recompute pooled percentiles from per-edge samples)
    pooled = []
    for eid in r_edges:
        c = ctx.chain_of_edge.get(eid)
        ol = ctx.osm_line(Mx.way_of(eid))
        sp = chain_span_of_edge(c, eid) if c else None
        if ol is None or not sp:
            continue
        ss = np.arange(sp[0], sp[1], 1.0)
        pooled += [ol.distance(Point(p)) for p in c.line.point(ss)]
    route_ax = Mx.stats(pooled)
    rs = edge_summary(route_edge_all)
    summary = {
        "osm_snapshot": osm["source"]["snapshot"], "osm_sha256": osm["source"]["sha256"],
        "route": {
            "edges": len(r_edges),
            "axis_vs_osm_m": route_ax,
            "edge_vs_ortho_m": rs,
            "lanes": lanes_ok(route_lanes),
            "sites_iou": {s["id"]: s["iou"]["iou"] for s in sites},
            "gen_islands_absent_on_ortho": len({tuple(np.round(x["xy"], 0)) for s in sites for x in s["gen_islands"]
                                                if x["verdict"] == "absent_on_ortho" and x["route_dist_m"] <= 20}),
            "gen_islands_absent_on_ortho_windows": len({tuple(np.round(x["xy"], 0)) for s in sites for x in
                                                        s["gen_islands"] if x["verdict"] == "absent_on_ortho"}),
            "ortho_islands_missing_in_gen": len({tuple(np.round(x["xy"], 0)) for s in sites for x in
                                                 s["ortho_islands_missing_in_gen"] if x["route_dist_m"] <= 20}),
            "lane_into_island": sum(1 for x in lii if x["on_route"]),
            "lane_into_island_generator_bug": sum(1 for x in lii if x["on_route"] and
                                                  x["verdict"] == "generator_island_on_real_road"),
            "arrows_checked": sum(1 for s in sites for ar in s["arrows"] if ar.get("ortho")),
            "arrows_not_on_ortho": sum(1 for s in sites for ar in s["arrows"] if ar.get("ortho") and
                                       not ar["ortho"]["present"]),
            "stop_lines_checked": sum(1 for s in sites for st in s["stop_lines"] if st.get("ortho")),
            "stop_lines_not_on_ortho": sum(1 for s in sites for st in s["stop_lines"] if st.get("ortho") and
                                           not st["ortho"]["present"]),
        },
        "tile": {
            "axis_vs_osm_m": Mx.stats([v["p95"] for v in axis.values() if v.get("n")]),
            "graph_vs_fresh_osm_max_m": graph_vs_osm,
            "edge_vs_ortho_m": edge_summary(tile_edge_all),
            "junction_windows": len(tile_sites),
            "junction_iou": Mx.stats([t["iou"]["iou"] for t in tile_sites]),
            "lane_into_island": len(lii),
            "lane_issue_counts": {},
            "osm_drivable_ways_missing_in_graph": len(conn["missing_in_graph"]),
        },
    }
    from collections import Counter
    cnt = Counter(i["kind"] for v in lanes_all.values() for i in v["issues"])
    summary["tile"]["lane_issue_counts"] = dict(sorted(cnt.items()))
    inputs = {p: sha_file(rdir / p) for p in ("roads.graph.json", "overrides.yaml", "route_start.json")}
    for p in sorted((REPO / "tools/worldgen/roads").glob("*.py")):
        inputs["tools/worldgen/roads/" + p.name] = sha_file(p)
    qa = {"schema": "kamion/fidelity/1", "region": a.region, "adr": "0075", "inputs_sha256": inputs,
          "ortho_hr_cells": len(ortho.man), "summary": summary,
          "route_edges": [{"edge": e, "axis": axis.get(e), "edges": edge_summary(edge_rows.get(e, [])),
                           "lanes": next(r for r in route_lanes if r["edge"] == e)} for e in r_edges],
          "sites": sites, "tile_sites": tile_sites, "roundabouts": rbs, "connectivity": conn,
          "route_node_arms": arms, "lane_into_island": lii,
          "lane_issues_tile": {k: v for k, v in lanes_all.items() if any(
              i["kind"] != "lanes_default" for i in v["issues"])}}

    def clean(o):
        if isinstance(o, dict):
            return {str(k): clean(v) for k, v in o.items() if k != "rc"}
        if isinstance(o, (list, tuple)):
            return [clean(v) for v in o]
        if isinstance(o, (np.floating, float)):
            return None if not math.isfinite(float(o)) else round(float(o), 3)
        if isinstance(o, (np.integer,)):
            return int(o)
        if isinstance(o, np.bool_):
            return bool(o)
        if isinstance(o, np.ndarray):
            return clean(o.tolist())
        return o
    qa = clean(qa)
    out = rdir / "generated" / "fidelity_qa.json"
    out.write_text(json.dumps(qa, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    (art / "fidelity_summary.json").write_text(json.dumps(qa["summary"], ensure_ascii=False, indent=1), encoding="utf-8")
    log(f"wrote {out}")
    print(json.dumps(qa["summary"], ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
