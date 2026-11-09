"""Data-QA renders + stats for a built region (renders from our own OSM/GUGiK data only).

Usage (from repo root, after build_region.py):
    uv run --project tools/worldgen tools/worldgen/qa_report.py --region bialystok-industrial-c

Writes docs/reports/map/<id>_*.png (each <= 400 KB) and docs/reports/map/<id>_qa.json.
The numbers quoted in docs/DATA_QA.md come from the JSON.

Road-vs-orthophoto alignment (rough, automated, then eyeballed on the crops PNG):
  For straight OSM edges of major roads (>= 60 m, chord/length >= 0.995) we sample a point every 4 m,
  take a 40 m profile perpendicular to the edge in the 0.25 m orthophoto, classify "pavement" pixels
  (low saturation: max(RGB)-min(RGB) <= 22, brightness 45..150), close gaps <= 0.75 m (lane markings,
  cars), and take the pavement run containing (or nearest to) the OSM line. Offset = signed distance
  from the OSM line to the run centre (+ = left of edge direction). Reported: median and IQR per edge.
  Caveat: OSM maps each carriageway of a dual road as its own line, so the run is one carriageway;
  a correctly placed OSM line should sit near its centre (|offset| ~ 0-1 m). Shadows, parked trucks and
  adjacent car parks bias the run; we report the per-edge spread and look at the crops.
  Second, independent check: distance from the OSM edge midpoint to the matched BDOT10k carriageway
  centreline (BDOT10k road geometry is digitised mostly from orthophoto).
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
import rasterio  # noqa: E402
import shapely  # noqa: E402
from matplotlib.collections import LineCollection, PatchCollection  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Polygon as MplPolygon  # noqa: E402
from shapely.geometry import LineString  # noqa: E402

import regions  # noqa: E402
import roadgraph  # noqa: E402
import terrain  # noqa: E402
from analyze_candidates import draw_north, draw_scalebar, save_png  # noqa: E402
from sources import REPO_ROOT  # noqa: E402

OUT = REPO_ROOT / "docs" / "reports" / "map"
ATTR = "© OpenStreetMap contributors (ODbL) · NMT, ortofotomapa, BDOT10k, modele 3D: GUGiK (geoportal.gov.pl)"
CLASS_STYLE = {  # highway -> (colour, width)
    "trunk": ("#c0392b", 2.6), "trunk_link": ("#c0392b", 1.6), "primary": ("#e67e22", 2.2),
    "primary_link": ("#e67e22", 1.4), "secondary": ("#d4ac0d", 2.0), "secondary_link": ("#d4ac0d", 1.3),
    "tertiary": ("#7d3c98", 1.7), "tertiary_link": ("#7d3c98", 1.2), "unclassified": ("#2c3e50", 1.1),
    "residential": ("#2c3e50", 1.0), "living_street": ("#2c3e50", 0.9), "service": ("#566573", 0.7),
}
PAV_SAT_MAX, PAV_VAL = 22, (45, 150)   # pavement classifier; calibrated so run width ~ BDOT10k width (DATA_QA)
GAP_PX = 3                               # close gaps <= 0.75 m (lane markings)
MAJOR = {"trunk", "trunk_link", "primary", "primary_link", "secondary", "secondary_link", "tertiary", "tertiary_link"}


def load(region):
    d = REPO_ROOT / "Data" / "Regions" / region.id
    graph = json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))
    bld = json.loads((d / "buildings.geojson").read_text(encoding="utf-8"))
    tmeta = json.loads((d / "terrain.json").read_text(encoding="utf-8"))
    raw = REPO_ROOT / tmeta["encoding"]["file"]
    n = tmeta["samples"][0]
    q = np.frombuffer(raw.read_bytes(), dtype="<u2").reshape(n, n)
    z = tmeta["encoding"]["offset_m"] + q.astype(np.float64) * tmeta["encoding"]["scale_m_per_unit"]
    return graph, bld, tmeta, z


def route_path(graph, region):
    import analyze_candidates as ac
    g = roadgraph.to_digraph(graph)
    cand = next(c for c in ac.CANDIDATES if c["id"] == region.candidate)
    nodes = graph["nodes"]

    def near(x, y):
        return min(nodes, key=lambda n: math.hypot(n["x"] - x, n["y"] - y))["id"]

    # start/end = endpoints recorded by the D4 analysis (candidates.json)
    cj = json.loads((OUT / "candidates.json").read_text(encoding="utf-8"))
    r = next(c for c in cj["candidates"] if c["id"] == cand["id"])["route"]
    s, t = near(*r["start_epsg2180"]), near(*r["end_epsg2180"])
    path = nx.shortest_path(g, s, t, weight="length")
    eids = {g[a][b]["id"] for a, b in zip(path, path[1:])}
    return path, eids, g


def frame(ax, region, title):
    x0, y0, x1, y1 = region.bbox
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_title(title, fontsize=11, loc="left")
    draw_scalebar(ax, x0 + 60, y0 + 60, 500, "500 m")
    draw_north(ax, x1 - 110, y1 - 230, 120)
    ax.text(x0 + 10, y1 - 15, f"EPSG:2180  bbox {int(x0)} {int(y0)} {int(x1)} {int(y1)}", fontsize=6.5,
            va="top", path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
    ax.figure.text(0.01, 0.005, ATTR, fontsize=6.5, color="#333")


def edge_lines(graph, pred=lambda e: True):
    return [e for e in graph["edges"] if pred(e)]


# ---------------------------------------------------------------------------------------------
def render_hillshade(region, graph, z, route_eids, out):
    fig, ax = plt.subplots(figsize=(9.2, 10.6), dpi=110)
    hs = terrain.hillshade(z, zf=3.0)
    x0, y0, x1, y1 = region.bbox
    ax.imshow(hs, cmap="gray", extent=(x0 - 0.5, x1 + 0.5, y0 - 0.5, y1 + 0.5), vmin=0, vmax=1,
              interpolation="bilinear", zorder=1)
    im = ax.imshow(z, cmap="terrain", alpha=0.35, extent=(x0 - 0.5, x1 + 0.5, y0 - 0.5, y1 + 0.5), zorder=2,
                   vmin=np.nanpercentile(z, 1) - 10, vmax=np.nanpercentile(z, 99) + 5)
    cb = fig.colorbar(im, ax=ax, fraction=0.035, pad=0.01)
    cb.set_label("NMT 2025, m n.p.m. (PL-EVRF2007-NH)", fontsize=8)
    for hw, (col, lw) in sorted(CLASS_STYLE.items()):
        segs = [e["geometry"] for e in graph["edges"] if e["attrs"]["highway"]["v"] == hw]
        ax.add_collection(LineCollection(segs, colors=col, linewidths=lw, zorder=5))
    rs = [e["geometry"] for e in graph["edges"] if e["id"] in route_eids]
    ax.add_collection(LineCollection(rs, colors="#00e5ff", linewidths=5, alpha=0.55, zorder=4))
    br = [e["geometry"] for e in graph["edges"] if "bridge" in e["attrs"]]
    ax.add_collection(LineCollection(br, colors="black", linewidths=4.5, zorder=4.5))
    frame(ax, region, f"{region.id}: cieniowanie NMT 1 m (GUGiK 2025) + graf dróg OSM")
    ax.legend(handles=[Line2D([], [], color=CLASS_STYLE[k][0], lw=CLASS_STYLE[k][1], label=k)
                       for k in ("trunk", "primary", "secondary", "tertiary", "residential", "service")] +
              [Line2D([], [], color="#00e5ff", lw=5, alpha=0.55, label="trasa Kwadrat Park → DK8/DK19"),
               Line2D([], [], color="black", lw=4.5, label="most / wiadukt (bridge=*)")],
              loc="upper center", bbox_to_anchor=(0.5, -0.005), ncol=3, fontsize=7, framealpha=0.9)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    return save_png(fig, out)


HS_COL = {"gugik_lod1_2024": "#1b9e77", "gugik_lod2_2017": "#66a61e", "bdot10k_storeys": "#7570b3",
          "osm_height": "#e6ab02", "osm_levels": "#d95f02", "default": "#e7298a"}


def render_buildings(region, graph, bld, out):
    fig, ax = plt.subplots(figsize=(9.2, 10.6), dpi=110)
    ax.set_facecolor("#f4f4f2")
    segs = [e["geometry"] for e in graph["edges"]]
    ax.add_collection(LineCollection(segs, colors="#b8b8b8", linewidths=0.8, zorder=1))
    patches, cols, eds = [], [], []
    for f in bld["features"]:
        p = f["properties"]
        for poly in f["geometry"]["coordinates"]:
            patches.append(MplPolygon(poly[0], closed=True))
            cols.append(HS_COL[p["height_source"]])
            eds.append("black" if p.get("is_roof_only") else "none")
    ax.add_collection(PatchCollection(patches, facecolors=cols, edgecolors=eds, linewidths=0.4, zorder=3))
    cnt = Counter(f["properties"]["height_source"] for f in bld["features"])
    frame(ax, region, f"{region.id}: budynki wg źródła wysokości (n={len(bld['features'])})")
    ax.legend(handles=[Patch(color=HS_COL[k], label=f"{k} ({cnt.get(k, 0)})") for k in HS_COL] +
              [Patch(fc="white", ec="black", label="building=roof (wiata, bez ścian)")],
              loc="upper center", bbox_to_anchor=(0.5, -0.005), ncol=3, fontsize=7.5, framealpha=0.9)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    return save_png(fig, out)


def conf_level(e):
    lc = set(e["low_confidence"])
    if e["attrs"]["highway"]["v"] not in MAJOR:
        return "local" if lc else "ok"   # residential/service: defaults are acceptable, shown separately
    crit = lc & {"lanes", "maxspeed"}
    if not lc:
        return "ok"
    if crit:
        return "critical" if len(crit) == 2 else "partial"
    return "minor"


CONF_COL = {"local": "#a9b4c2", "ok": "#1a9850", "minor": "#91cf60", "partial": "#fc8d59", "critical": "#d73027"}


def render_confidence(region, graph, route_eids, out):
    fig, ax = plt.subplots(figsize=(9.2, 10.6), dpi=110)
    ax.set_facecolor("#fbfbf8")
    lv = Counter()
    for lvl in ("local", "ok", "minor", "partial", "critical"):
        es = [e for e in graph["edges"] if conf_level(e) == lvl]
        lv[lvl] = len(es)
        ax.add_collection(LineCollection([e["geometry"] for e in es], colors=CONF_COL[lvl],
                                         linewidths=[2.4 if e["attrs"]["highway"]["v"] in MAJOR else 1.0 for e in es],
                                         zorder=3 + ["local", "ok", "minor", "partial", "critical"].index(lvl)))
    rs = [e["geometry"] for e in graph["edges"] if e["id"] in route_eids]
    ax.add_collection(LineCollection(rs, colors="#2b6cb0", linewidths=6, alpha=0.25, zorder=2))
    bnd = [n for n in graph["nodes"] if n.get("boundary")]
    ax.scatter([n["x"] for n in bnd], [n["y"] for n in bnd], s=10, marker="s", c="black", zorder=9)
    g = roadgraph.to_digraph(graph)
    comps = sorted(nx.weakly_connected_components(g), key=len, reverse=True)
    iso = [n for c in comps[1:] for n in c]
    pos = {n["id"]: (n["x"], n["y"]) for n in graph["nodes"]}
    ax.scatter([pos[n][0] for n in iso], [pos[n][1] for n in iso], s=26, facecolors="none", edgecolors="#6a1b9a",
               linewidths=1.0, zorder=10)
    frame(ax, region, f"{region.id}: graf dróg wg pewności tagów (lanes / maxspeed / surface / turn:lanes)")
    ax.legend(handles=[
        Line2D([], [], color=CONF_COL["ok"], lw=2.4, label=f"wszystko z OSM ({lv['ok']})"),
        Line2D([], [], color=CONF_COL["local"], lw=1.0, label=f"lokalne/service z domyślnymi ({lv['local']})"),
        Line2D([], [], color=CONF_COL["minor"], lw=2.4, label=f"główne: brak surface/turn:lanes ({lv['minor']})"),
        Line2D([], [], color=CONF_COL["partial"], lw=2.4, label=f"główne: brak lanes ALBO maxspeed ({lv['partial']})"),
        Line2D([], [], color=CONF_COL["critical"], lw=2.4, label=f"główne: brak lanes I maxspeed ({lv['critical']})"),
        Line2D([], [], color="#2b6cb0", lw=6, alpha=0.25, label="trasa startowa"),
        Line2D([], [], marker="s", ls="", color="black", ms=4, label="cięcie na granicy kafla"),
        Line2D([], [], marker="o", ls="", mfc="none", mec="#6a1b9a", ms=6, label="węzły poza główną składową"),
    ], loc="upper center", bbox_to_anchor=(0.5, -0.005), ncol=3, fontsize=7.2, framealpha=0.92)
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    return save_png(fig, out)


# ---------------------------------------------------------------------------------------------
def alignment(region, graph, ortho_path, n_spots=8):
    """Return per-edge offsets (see module doc)."""
    cands = []
    for e in graph["edges"]:
        if e["attrs"]["highway"]["v"] not in MAJOR or e["length_m"] < 60 or "bridge" in e["attrs"]:
            continue
        line = LineString(e["geometry"])
        p0, p1 = e["geometry"][0], e["geometry"][-1]
        if math.dist(p0, p1) / line.length < 0.995:
            continue
        cands.append((e, line))
    # spread spots: greedy farthest-point selection starting from the longest edge (deterministic)
    cands.sort(key=lambda t: (-t[1].length, t[0]["id"]))
    chosen = [cands[0]] if cands else []
    while len(chosen) < n_spots and len(chosen) < len(cands):
        best = max(cands, key=lambda c: min(c[1].centroid.distance(o[1].centroid) for o in chosen))
        chosen.append(best)
    res = []
    with rasterio.open(ortho_path) as src:
        img = src.read()  # 3 x H x W
        inv = ~src.transform
        H, W = img.shape[1:]
        for e, line in chosen:
            offs, widths = [], []
            L = line.length
            for s in np.arange(10.0, L - 10.0, 4.0):
                p = line.interpolate(s)
                a = line.interpolate(max(0, s - 2))
                b = line.interpolate(min(L, s + 2))
                tx, ty = (b.x - a.x), (b.y - a.y)
                tn = math.hypot(tx, ty)
                nx_, ny_ = -ty / tn, tx / tn            # left normal
                ts = np.arange(-20.0, 20.0001, 0.25)
                xs, ys = p.x + ts * nx_, p.y + ts * ny_
                cols, rows = inv * (xs, ys)
                ci, ri = np.floor(cols).astype(int), np.floor(rows).astype(int)
                ok = (ci >= 0) & (ci < W) & (ri >= 0) & (ri < H)
                if not ok.all():
                    continue
                rgb = img[:, ri, ci].astype(int)
                sat = rgb.max(0) - rgb.min(0)
                val = rgb.mean(0)
                pav = (sat <= PAV_SAT_MAX) & (val >= PAV_VAL[0]) & (val <= PAV_VAL[1])
                # close gaps <= 1.5 m (6 px)
                pav2 = pav.copy()
                idx = np.where(pav)[0]
                for i0, i1 in zip(idx, idx[1:]):
                    if 1 < i1 - i0 <= GAP_PX:
                        pav2[i0:i1] = True
                runs, i = [], 0
                while i < len(pav2):
                    if pav2[i]:
                        j = i
                        while j + 1 < len(pav2) and pav2[j + 1]:
                            j += 1
                        runs.append((ts[i], ts[j]))
                        i = j + 1
                    else:
                        i += 1
                runs = [r for r in runs if r[1] - r[0] >= 5.0]   # a carriageway is >= ~5 m wide
                if not runs:
                    continue
                run = min(runs, key=lambda r: 0 if r[0] <= 0 <= r[1] else min(abs(r[0]), abs(r[1])))
                if not (run[0] <= 0 <= run[1]) and min(abs(run[0]), abs(run[1])) > 3:
                    continue
                offs.append((run[0] + run[1]) / 2)
                widths.append(run[1] - run[0])
            if len(offs) >= 5:
                o = np.array(offs)
                res.append({"edge": e["id"], "name": e["attrs"].get("name", {}).get("v"),
                            "highway": e["attrs"]["highway"]["v"], "samples": len(o),
                            "offset_median_m": round(float(np.median(o)), 2),
                            "offset_iqr_m": round(float(np.subtract(*np.percentile(o, [75, 25]))), 2),
                            "pavement_width_median_m": round(float(np.median(widths)), 1),
                            "osm_lanes": e["attrs"]["lanes"]["v"], "lanes_src": e["attrs"]["lanes"]["src"],
                            "bdot10k_dist_m": e.get("bdot10k", {}).get("dist_m"),
                            "bdot10k_width_m": e.get("bdot10k", {}).get("width_m"),
                            "mid": [round(line.centroid.x, 1), round(line.centroid.y, 1)]})
    return res, [c[0]["id"] for c in chosen]


def render_alignment(region, graph, ortho_path, spots, out):
    sel = spots[:6]
    fig, axs = plt.subplots(2, 3, figsize=(10.0, 8.9), dpi=100)
    with rasterio.open(ortho_path) as src:
        for ax, s in zip(axs.flat, sel):
            cx, cy = s["mid"]
            r = 45.0
            win = rasterio.windows.from_bounds(cx - r, cy - r, cx + r, cy + r, src.transform)
            arr = src.read(window=win, out_shape=(3, 360, 360))
            ax.imshow(np.moveaxis(arr, 0, -1), extent=(cx - r, cx + r, cy - r, cy + r))
            for e in graph["edges"]:
                g = np.array(e["geometry"])
                ax.plot(g[:, 0], g[:, 1], color="#ff1744" if e["id"] == s["edge"] else "#ffd600",
                        lw=1.6 if e["id"] == s["edge"] else 1.0)
            ax.set_xlim(cx - r, cx + r)
            ax.set_ylim(cy - r, cy + r)
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_title(f"{(s['name'] or s['highway'])[:28]}\nprzes. {s['offset_median_m']:+.2f} m "
                         f"(IQR {s['offset_iqr_m']:.2f}), jezdnia ~{s['pavement_width_median_m']:.0f} m",
                         fontsize=7.5)
            ax.plot([cx - r + 5, cx - r + 25], [cy - r + 5, cy - r + 5], color="white", lw=3)
            ax.text(cx - r + 15, cy - r + 7, "20 m", color="white", ha="center", fontsize=7)
    for ax in list(axs.flat)[len(sel):]:
        ax.axis("off")
    fig.suptitle(f"{region.id}: osie OSM (czerwona = mierzona) na ortofotomapie GUGiK 0,25 m (2024-05-27)",
                 fontsize=10)
    fig.text(0.01, 0.005, ATTR, fontsize=6.5, color="#333")
    fig.tight_layout(rect=(0, 0.02, 1, 0.96))
    return save_png(fig, out)


# ---------------------------------------------------------------------------------------------
def stats(region, graph, bld, tmeta, z, route_eids, g):
    edges = graph["edges"]
    tot = sum(e["length_m"] for e in edges)
    major = [e for e in edges if e["attrs"]["highway"]["v"] in MAJOR]
    mtot = sum(e["length_m"] for e in major)

    def cov(es, key, src=("osm",)):
        t = sum(e["length_m"] for e in es)
        return round(sum(e["length_m"] for e in es if key in e["attrs"] and e["attrs"][key]["src"] in src) / t, 3) if t else None

    route = [e for e in edges if e["id"] in route_eids]
    comps = sorted(nx.weakly_connected_components(g), key=len, reverse=True)
    deg = Counter(n["degree"] for n in graph["nodes"])
    dangles = [n for n in graph["nodes"] if n["degree"] == 1 and not n.get("boundary")]
    bridges = [e for e in edges if "bridge" in e["attrs"]]
    bridge_no_layer = [e["id"] for e in bridges if e["attrs"].get("layer", {}).get("src") == "default"]
    short = [e["id"] for e in edges if e["length_m"] < 0.5]
    # sharp angles between consecutive vertices within an edge
    sharp = []
    for e in edges:
        pts = np.array(e["geometry"])
        for i in range(1, len(pts) - 1):
            v1, v2 = pts[i] - pts[i - 1], pts[i + 1] - pts[i]
            n1, n2 = np.linalg.norm(v1), np.linalg.norm(v2)
            if n1 < 1e-6 or n2 < 1e-6:
                continue
            ang = math.degrees(math.acos(np.clip(np.dot(v1, v2) / (n1 * n2), -1, 1)))
            if ang > 100:
                sharp.append({"edge": e["id"], "vertex": i, "turn_deg": round(ang, 1)})
    width_disagree = []
    for e in major:
        w_osm = e["attrs"].get("width", {})
        b = e.get("bdot10k", {})
        if w_osm.get("src") == "osm" and b.get("width_m") and abs(w_osm["v"] - b["width_m"]) > 2:
            width_disagree.append({"edge": e["id"], "osm": w_osm["v"], "bdot10k": b["width_m"]})
    # BDOT lane sanity: width / lanes on major roads
    lane_w = []
    for e in major:
        b = e.get("bdot10k", {})
        if b.get("width_m") and e["attrs"]["lanes"]["src"] == "osm":
            lanes = e["attrs"]["lanes"]["v"]
            lane_w.append(b["width_m"] / lanes)
    hs = Counter(f["properties"]["height_source"] for f in bld["features"])
    d12 = [f["properties"]["height_lod1_2024_m"] - f["properties"]["height_lod2_2017_m"]
           for f in bld["features"] if f["properties"]["height_lod1_2024_m"] and f["properties"]["height_lod2_2017_m"]]
    # route profile: NMT along the route edges (ground; bridges flagged)
    prof = []
    for e in route:
        line = LineString(e["geometry"])
        for s in np.arange(0, line.length, 5.0):
            p = line.interpolate(s)
            prof.append(terrain.sample(z, region.bbox, p.x, p.y))
    prof = np.array([v for v in prof if not math.isnan(v)])
    gy, gx = np.gradient(z, 1.0)
    slope = np.degrees(np.arctan(np.hypot(gx, gy)))
    return {
        "region": region.id, "bbox": list(region.bbox),
        "terrain": {**tmeta["stats_m"], "missing_samples": tmeta["missing_samples"],
                    "slope_deg_p50": round(float(np.percentile(slope, 50)), 2),
                    "slope_deg_p99": round(float(np.percentile(slope, 99)), 2),
                    "route_ground_min_max_m": [round(float(prof.min()), 2), round(float(prof.max()), 2)]},
        "graph": {
            "nodes": len(graph["nodes"]), "edges": len(edges), "length_km": round(tot / 1000, 2),
            "length_by_class_m": {hw: round(sum(e["length_m"] for e in edges if e["attrs"]["highway"]["v"] == hw))
             for hw in sorted({e["attrs"]["highway"]["v"] for e in edges})},
            "boundary_nodes": sum(1 for n in graph["nodes"] if n.get("boundary")),
            "weak_components": len(comps), "largest_component_nodes": len(comps[0]),
            "small_components": [sorted(c)[:3] + (["..."] if len(c) > 3 else []) for c in comps[1:]],
            "strong_largest_nodes": len(max(nx.strongly_connected_components(g), key=len)),
            "degree_hist": dict(sorted(deg.items())), "dangling_non_boundary_nodes": len(dangles),
            "zero_length_edges": short, "sharp_vertices_gt100deg": sharp[:30], "sharp_count": len(sharp),
            "bridges": len(bridges), "bridge_without_layer": bridge_no_layer,
            "low_confidence_counts": dict(Counter(x for e in edges for x in e["low_confidence"])),
            "major_coverage_by_length_osm": {k: cov(major, k) for k in ("lanes", "maxspeed", "surface", "turn:lanes")},
            "major_length_m": round(mtot),
            "route_coverage_by_length_osm": {k: cov(route, k) for k in ("lanes", "maxspeed", "surface", "turn:lanes")},
            "route_length_m": round(sum(e["length_m"] for e in route), 1), "route_edges": len(route),
            "width_from": dict(Counter(e["attrs"]["width"]["src"] for e in edges if "width" in e["attrs"])),
            "bdot10k_matched_edges": sum(1 for e in edges if "bdot10k" in e),
            "bdot10k_width_per_osm_lane_major_m": None if not lane_w else
            {"p10": round(float(np.percentile(lane_w, 10)), 2), "p50": round(float(np.median(lane_w)), 2),
             "p90": round(float(np.percentile(lane_w, 90)), 2), "n": len(lane_w)},
            "width_osm_vs_bdot10k_disagree_gt2m": width_disagree,
        },
        "buildings": {
            "count": len(bld["features"]), "height_source": dict(hs),
            "footprint_source": dict(Counter(f["properties"]["footprint_source"] for f in bld["features"])),
            "roof_only": sum(1 for f in bld["features"] if f["properties"].get("is_roof_only")),
            "lod1_minus_lod2_m": None if not d12 else
            {"n": len(d12), "p10": round(float(np.percentile(d12, 10)), 2), "p50": round(float(np.median(d12)), 2),
             "p90": round(float(np.percentile(d12, 90)), 2)},
            "height_m": {"p50": round(float(np.median([f["properties"]["height_m"] for f in bld["features"]])), 2),
                         "max": max(f["properties"]["height_m"] for f in bld["features"])},
        },
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    a = ap.parse_args()
    region = regions.get(a.region)
    graph, bld, tmeta, z = load(region)
    path, route_eids, g = route_path(graph, region)
    OUT.mkdir(parents=True, exist_ok=True)
    pid = region.id
    sizes = {
        f"{pid}_hillshade_roads.png": render_hillshade(region, graph, z, route_eids, OUT / f"{pid}_hillshade_roads.png"),
        f"{pid}_buildings_height_source.png": render_buildings(region, graph, bld, OUT / f"{pid}_buildings_height_source.png"),
        f"{pid}_roads_confidence.png": render_confidence(region, graph, route_eids, OUT / f"{pid}_roads_confidence.png"),
    }
    st = stats(region, graph, bld, tmeta, z, route_eids, g)
    ortho = json.loads((REPO_ROOT / "Data" / "Regions" / pid / "ortho.json").read_text(encoding="utf-8"))
    op = REPO_ROOT / ortho["file"]
    al, chosen = alignment(region, graph, op)
    st["alignment"] = {"method": "see tools/worldgen/qa_report.py docstring", "ortho": ortho["source_manifest"],
                       "edges_tested": chosen, "results": al}
    if al:
        sizes[f"{pid}_ortho_alignment.png"] = render_alignment(region, graph, op, al, OUT / f"{pid}_ortho_alignment.png")
    st["png_bytes"] = sizes
    (OUT / f"{pid}_qa.json").write_text(json.dumps(st, indent=1, ensure_ascii=False, allow_nan=False) + "\n",
                                        encoding="utf-8", newline="\n")
    print(json.dumps({k: st[k] for k in ("terrain", "buildings")}, indent=1, ensure_ascii=False))
    print(json.dumps(st["alignment"]["results"], indent=1, ensure_ascii=False))
    print(sizes)


if __name__ == "__main__":
    main()
