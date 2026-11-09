"""D4: analyse Białystok OSM data and evaluate start-area candidates (industrial zone + exit
onto a national / expressway road, 2-3 km drivable route).

Reproduce everything (from repo root):
    uv run tools/worldgen/analyze_candidates.py

Inputs : Geofabrik podlaskie extract (downloaded + manifested by fetch_osm.py, cached in Data/raw/)
Outputs: docs/reports/map/overview_bialystok.png
         docs/reports/map/candidate_<id>.png
         docs/reports/map/candidates.json      (all numbers quoted in docs/map-decisions.md)

Sources: OpenStreetMap only (ODbL, © OpenStreetMap contributors). No Google anything (ADR 0002).
Work CRS: EPSG:2180. Candidate geometry (waypoints, boxes) is defined below in EPSG:2180 metres;
the waypoints were chosen by a human/agent reading the zone maps and are the only "authored" input.
"""

from __future__ import annotations

import io
import json
import math
from collections import defaultdict
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as pe  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import networkx as nx  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from PIL import Image  # noqa: E402
from pyproj import Transformer  # noqa: E402

from fetch_osm import REPO_ROOT, load_manifest  # noqa: E402
from osm_extract import WORK_CRS, load_layers  # noqa: E402

OUT_DIR = REPO_ROOT / "docs" / "reports" / "map"
TO_WGS = Transformer.from_crs(WORK_CRS, "EPSG:4326", always_xy=True)
FROM_WGS = Transformer.from_crs("EPSG:4326", WORK_CRS, always_xy=True)

DRIVABLE = {
    "motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
    "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
    "residential", "living_street", "service",
}
PUBLIC = DRIVABLE - {"service"}
MAJOR = {"motorway", "trunk", "primary", "secondary", "tertiary",
         "motorway_link", "trunk_link", "primary_link", "secondary_link", "tertiary_link"}

# ----------------------------------------------------------------------------------------------
# Candidates. Waypoints in EPSG:2180 (x=east, y=north) metres; route = shortest drivable path
# through consecutive waypoints (respecting oneway). Area = 3 km x 2 km box (docs/05 §2) centred
# on the route. See docs/map-decisions.md for reasoning.
# ----------------------------------------------------------------------------------------------
CANDIDATES: list[dict] = [
    {
        "id": "A_dojlidy_dywizjonu303",
        "title": "A — Dojlidy / Kuronia (strefa SSE) → DK19 Suchowolca (kier. Zabłudów)",
        # depot = hall with mapped loading docks at Karpińskiego; exit at signalised junction with DK19
        "waypoints": [(781240, 590215, "service"), (781700, 590900, "major"), (782720, 590020, "trunk")],
        "label_offsets": {"start": (-70, -38)},
    },
    {
        "id": "B_przedzalniana_kleeberga",
        "title": "B — Przędzalniana / Kleeberga (DK8/DK65) → w stronę S8 Białystok Zachód",
        "waypoints": [(772820, 595880, "service"), (773080, 595660, "major"), (770900, 594880, "trunk")],
        # continuation to the S8 on-ramp, reported separately (outside the 2-3 km core route)
        "extension": [(769300, 595330, "trunk")],
    },
    {
        "id": "C_andersa_putry",
        "title": "C — Andersa (DK19/DK65) / Rondo Putry → DK8/DK19 Al. Tysiąclecia (północ)",
        "waypoints": [(778700, 595850, "service"), (777450, 597050, "trunk")],
    },
]

BOX_W, BOX_H = 3000.0, 2000.0
# Routing cost multipliers: a 40 t articulated truck should stay on the main network; side streets
# are allowed but expensive (the depot access on `service` is forced by the first waypoint anyway).
TRUCK_COST = {"service": 3.0, "residential": 4.0, "living_street": 20.0, "unclassified": 1.5}


# ----------------------------------------------------------------------------------------------
# Graph
# ----------------------------------------------------------------------------------------------
def build_graph(roads: gpd.GeoDataFrame):
    """Directed graph on OSM node ids. Coordinates taken from the reprojected way geometry.
    Returns (graph, coords, snap_sets) where snap_sets maps "service"/"public" to node-id sets."""
    g = nx.MultiDiGraph()
    coords: dict[int, tuple[float, float]] = {}
    snap = {"service": set(), "public": set(), "major": set(), "trunk": set()}
    drv = roads[roads.highway.isin(DRIVABLE)]
    for idx, row in drv.iterrows():
        if row.service in ("parking_aisle", "drive-through"):
            continue
        if row.access in ("private", "no") and row.highway != "service":
            continue
        pts = list(row.geometry.coords)
        nids = row.node_ids
        for nid, xy in zip(nids, pts):
            coords[nid] = xy
        snap["service" if row.highway == "service" else "public"].update(nids)
        if row.highway in MAJOR:
            snap["major"].update(nids)
        if row.highway in ("motorway", "trunk") and row.junction not in ("roundabout", "circular"):
            snap["trunk"].update(nids)
        w = TRUCK_COST.get(row.highway, 1.0)
        ow = row.oneway
        implied = row.junction in ("roundabout", "circular") or row.highway in ("motorway", "motorway_link")
        fwd = True
        bwd = not (ow in ("yes", "true", "1") or (implied and ow != "no"))
        if ow == "-1":
            fwd, bwd = False, True
        for i in range(len(nids) - 1):
            a, b = nids[i], nids[i + 1]
            seg_len = math.dist(pts[i], pts[i + 1])
            if fwd:
                g.add_edge(a, b, way=idx, length=seg_len, cost=seg_len * w)
            if bwd:
                g.add_edge(b, a, way=idx, length=seg_len, cost=seg_len * w)
    return g, coords, snap


def nearest_node(coords: dict[int, tuple[float, float]], allowed: set[int], xy: tuple[float, float]) -> int:
    best, bd = None, float("inf")
    for nid in allowed:
        c = coords[nid]
        d = (c[0] - xy[0]) ** 2 + (c[1] - xy[1]) ** 2
        if d < bd:
            best, bd = nid, d
    return best


def route_through(g, coords, snap, waypoints, start_node=None) -> list[int]:
    nodes = set(g.nodes)
    snapped = [start_node] if start_node is not None else []
    for x, y, cls in waypoints:
        snapped.append(nearest_node(coords, snap[cls] & nodes, (x, y)))
    path: list[int] = []
    for a, b in zip(snapped, snapped[1:]):
        seg = nx.shortest_path(g, a, b, weight="cost")
        path.extend(seg if not path else seg[1:])
    return path


def path_edges(g, path):
    """For each consecutive node pair pick the shortest parallel edge; returns list of (a,b,data)."""
    out = []
    for a, b in zip(path, path[1:]):
        data = min(g.get_edge_data(a, b).values(), key=lambda d: d["cost"])
        out.append((a, b, data))
    return out


# ----------------------------------------------------------------------------------------------
# Stats
# ----------------------------------------------------------------------------------------------
def node_way_index(roads: gpd.GeoDataFrame) -> dict[int, set[int]]:
    idx: dict[int, set[int]] = defaultdict(set)
    drv = roads[roads.highway.isin(DRIVABLE)]
    for i, row in drv.iterrows():
        if row.service in ("parking_aisle", "drive-through"):
            continue
        for n in row.node_ids:
            idx[n].add(i)
    return idx


_RINGS_CACHE: dict = {}


def roundabout_rings(roads: gpd.GeoDataFrame) -> dict:
    """Group junction=roundabout ways into rings (union-find over shared nodes)."""
    if _RINGS_CACHE:
        return _RINGS_CACHE
    rb = roads[roads.junction.isin(["roundabout", "circular"]) & roads.highway.isin(DRIVABLE)]
    parent = {i: i for i in rb.index}

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    node_ways = defaultdict(list)
    for i, row in rb.iterrows():
        for n in row.node_ids:
            node_ways[n].append(i)
    for ws in node_ways.values():
        for w in ws[1:]:
            parent[find(w)] = find(ws[0])
    by_node = defaultdict(set)
    names = defaultdict(set)
    for n, ws in node_ways.items():
        for w in ws:
            by_node[n].add(find(w))
    for i, row in rb.iterrows():
        if isinstance(row["name"], str):
            names[find(i)].add(row["name"])
    _RINGS_CACHE.update({"by_node": by_node,
                         "name": defaultdict(lambda: "(rondo bez nazwy w OSM)",
                                             {k: " / ".join(sorted(v)) for k, v in names.items()})})
    return _RINGS_CACHE


def collapse(seq):
    out = []
    for s in seq:
        if not out or out[-1] != s:
            out.append(s)
    return out


def route_stats(cand, path, edges, coords, roads, layers, nwi) -> dict:
    pts = layers["points"]
    route_line = shapely.LineString([coords[n] for n in path])
    total = sum(d["length"] for _, _, d in edges)

    # length by way attribute
    by_class = defaultdict(float)
    tag_len = defaultdict(float)
    low_conf = []
    names_seq = []
    for a, b, d in edges:
        w = roads.loc[d["way"]]
        by_class[w.highway] += d["length"]
        for tag in ("lanes", "maxspeed", "turn:lanes", "surface", "name", "lit", "sidewalk"):
            val = w[tag]
            if tag == "turn:lanes":
                val = val or w["turn:lanes:forward"] or w["turn:lanes:backward"]
            if isinstance(val, str) and val:
                tag_len[tag] += d["length"]
        label = w["name"] if isinstance(w["name"], str) else f"<bez nazwy: {w.highway}>"
        if w.junction in ("roundabout", "circular") and not (isinstance(w["name"], str) and "Rondo" in w["name"]):
            label = f"rondo ({label})"
        names_seq.append(label)
    bridge_len = sum(d["length"] for _, _, d in edges if isinstance(roads.loc[d["way"]]["bridge"], str)
                     and roads.loc[d["way"]]["bridge"] != "no")
    # low-confidence ways (missing lanes or maxspeed) on route
    seen = set()
    for a, b, d in edges:
        wi = d["way"]
        if wi in seen:
            continue
        seen.add(wi)
        w = roads.loc[wi]
        missing = [t for t in ("lanes", "maxspeed") if not isinstance(w[t], str)]
        if missing and w.highway != "service":
            low_conf.append({"osm_way": int(w.osm_id), "name": w["name"] if isinstance(w["name"], str) else None,
                             "highway": w.highway, "missing": missing})

    # intersections: route nodes touched by >=1 other drivable way (excluding the route's own ways)
    route_ways = {d["way"] for _, _, d in edges}
    inter_public, inter_service = [], []
    for n in path[1:-1]:
        others = nwi.get(n, set()) - route_ways
        # a node where two route ways meet and a third way joins also counts
        if not others:
            continue
        classes = {roads.loc[o].highway for o in others}
        (inter_public if classes & PUBLIC else inter_service).append(n)
    # roundabouts: rings (connected roundabout ways) traversed or entered by the route
    rings = roundabout_rings(roads)
    ring_seq = []
    for n in path:
        for ring_id in rings["by_node"].get(n, ()):
            if ring_id not in ring_seq:
                ring_seq.append(ring_id)
    rb_groups = len(ring_seq)
    rb_names = [rings["name"][r] for r in ring_seq]
    # signals
    sig = pts[pts.kind == "highway=traffic_signals"]
    sig_on = sig[sig.distance(route_line) < 15]
    clusters = []
    for geom in sig_on.geometry:
        for c in clusters:
            if c.distance(geom) < 80:
                break
        else:
            clusters.append(geom)
    # crossings, give_way, stop, bus stops near route
    path_set = set(path)

    def count_near(kind, dist=None):
        """dist=None: count nodes that lie ON the route (OSM node id in path); else within dist metres."""
        s = pts[pts.kind == kind]
        if dist is None:
            return int(s.osm_id.isin(path_set).sum())
        return int((s.distance(route_line) < dist).sum())

    # depot candidates around route start
    start = shapely.Point(coords[path[0]])
    lu = layers["landuse"]
    workzone = lu[lu.landuse.isin(["industrial", "commercial", "retail"])].union_all()
    b = layers["buildings"]
    near_b = b[b.distance(start) < 400].copy()
    near_b["area_m2"] = near_b.area
    halls = near_b[(near_b.area_m2 > 2000) & (near_b.building.isin(["warehouse", "industrial", "yes", "commercial",
                                                                     "retail", "service", "hangar"]))]
    halls = halls[halls.intersects(workzone) | halls.building.isin(["warehouse", "industrial"])]
    docks = pts[(pts.kind.isin(["amenity=loading_dock", "door=loading_dock"])) & (pts.distance(start) < 400)]
    hall_list = [{"osm_id": int(r.osm_id), "osm_type": r.osm_type, "name": r["name"] if isinstance(r["name"], str) else None,
                  "building": r.building, "area_m2": round(r.area_m2),
                  "dist_from_start_m": round(r.geometry.distance(start))}
                 for _, r in halls.sort_values("area_m2", ascending=False).head(8).iterrows()]

    # area box
    rx0, ry0, rx1, ry1 = route_line.bounds
    cx, cy = (rx0 + rx1) / 2, (ry0 + ry1) / 2
    bw, bh = (BOX_W, BOX_H) if (rx1 - rx0) >= (ry1 - ry0) else (BOX_H, BOX_W)  # 3x2 km or 2x3 km
    box = shapely.box(cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2)
    rb_in_box = roads[roads.intersects(box) & roads.junction.isin(["roundabout", "circular"])]
    sig_in_box = sig[sig.within(box)]
    major_in_box = roads[roads.intersects(box) & roads.highway.isin(MAJOR)]
    clipped = major_in_box.geometry.intersection(box).length
    major_len = clipped.sum()

    def cov(tag):
        has = major_in_box[tag].apply(lambda v: isinstance(v, str) and v != "")
        if tag == "turn:lanes":
            has = has | major_in_box["turn:lanes:forward"].notna() | major_in_box["turn:lanes:backward"].notna()
        return round(float(clipped[has].sum() / major_len), 3) if major_len else None

    lon0, lat0 = TO_WGS.transform(*coords[path[0]])
    lon1, lat1 = TO_WGS.transform(*coords[path[-1]])
    return {
        "id": cand["id"],
        "title": cand["title"],
        "route": {
            "length_m": round(total),
            "start_epsg2180": [round(v, 1) for v in coords[path[0]]],
            "end_epsg2180": [round(v, 1) for v in coords[path[-1]]],
            "start_wgs84": [round(lat0, 6), round(lon0, 6)],
            "end_wgs84": [round(lat1, 6), round(lon1, 6)],
            "streets_in_order": collapse(names_seq),
            "length_by_highway_class_m": {k: round(v) for k, v in sorted(by_class.items(), key=lambda kv: -kv[1])},
            "intersections_with_public_roads": len(inter_public),
            "junctions_with_service_roads_or_driveways": len(inter_service),
            "roundabouts_traversed": rb_groups,
            "roundabout_names": rb_names,
            "traffic_signal_nodes_on_route": len(sig_on),
            "signalised_junctions_or_crossings": len(clusters),
            "pedestrian_crossings": count_near("highway=crossing"),
            "give_way_signs": count_near("highway=give_way"),
            "stop_signs": count_near("highway=stop"),
            "bus_stops_within_25m": count_near("highway=bus_stop", 25),
            "level_crossings": count_near("railway=level_crossing"),
            "length_on_bridges_m": round(bridge_len),
            "tag_coverage_by_length": {t: round(tag_len[t] / total, 3) for t in
                                       ("name", "lanes", "maxspeed", "turn:lanes", "surface", "lit", "sidewalk")},
            "low_confidence_ways": low_conf,
        },
        "depot": {
            "large_buildings_within_400m_of_start": hall_list,
            "loading_dock_nodes_within_400m": int(len(docks)),
        },
        "area_3x2km": {
            "bbox_epsg2180": [round(v) for v in box.bounds],
            "roundabout_ways": int(len(rb_in_box)),
            "roundabouts_distinct": int(len(set(rb_in_box.name.fillna("") + "|" +
                                               rb_in_box.geometry.centroid.x.round(-2).astype(str)))),
            "traffic_signal_nodes": int(len(sig_in_box)),
            "buildings": int(b.within(box).sum()),
            "industrial_landuse_ha": round(float(lu[lu.landuse == "industrial"].geometry.intersection(box).area.sum() / 1e4), 1),
            "major_road_length_m": round(major_len),
            "major_road_tag_coverage_by_length": {t: cov(t) for t in ("lanes", "maxspeed", "turn:lanes", "surface")},
            "refs_present": sorted(set(major_in_box.ref.dropna())),
            "bridge_or_viaduct_ways_drivable": int((roads[roads.intersects(box) & roads.highway.isin(DRIVABLE)]
                                                    .bridge.fillna("no") != "no").sum()),
        },
        "_route_line": route_line,
        "_box": box,
        "_signal_points": sig_on,
        "_inter_public": [coords[n] for n in inter_public],
    }


# ----------------------------------------------------------------------------------------------
# Rendering
# ----------------------------------------------------------------------------------------------
STYLE = {  # highway class -> (colour, linewidth at 3 km view, zorder)
    "motorway": ("#c0392b", 4.2, 9), "motorway_link": ("#c0392b", 2.0, 9),
    "trunk": ("#e67e22", 3.6, 8), "trunk_link": ("#e67e22", 1.8, 8),
    "primary": ("#d4a017", 3.0, 7), "primary_link": ("#d4a017", 1.5, 7),
    "secondary": ("#9a8c2a", 2.4, 6), "secondary_link": ("#9a8c2a", 1.3, 6),
    "tertiary": ("#6b6b6b", 2.0, 5), "tertiary_link": ("#6b6b6b", 1.2, 5),
    "unclassified": ("#8a8a8a", 1.2, 4), "residential": ("#8a8a8a", 1.1, 4),
    "living_street": ("#8a8a8a", 0.9, 4), "service": ("#b5b5b5", 0.6, 3),
}
ROUTE_COLOUR = "#1f5fbf"
LANDUSE_COLOUR = {"industrial": "#e6d9ef", "railway": "#ece8df", "commercial": "#f6e3e3", "retail": "#f6e3e3"}


def draw_scalebar(ax, x0, y0, length_m, label):
    ax.add_patch(plt.Rectangle((x0, y0), length_m / 2, length_m * 0.018, fc="black", ec="black", zorder=30))
    ax.add_patch(plt.Rectangle((x0 + length_m / 2, y0), length_m / 2, length_m * 0.018, fc="white", ec="black", zorder=30))
    for frac, txt in ((0, "0"), (0.5, f"{int(length_m / 2)}"), (1, label)):
        ax.text(x0 + frac * length_m, y0 + length_m * 0.035, txt, ha="center", va="bottom", fontsize=8, zorder=30,
                path_effects=[pe.withStroke(linewidth=3, foreground="white")])


def draw_north(ax, x, y, size):
    """Arrow to TRUE north (computed), with grid convergence noted (EPSG:2180 grid north ≠ true north)."""
    lon, lat = TO_WGS.transform(x, y)
    x2, y2 = FROM_WGS.transform(lon, lat + 0.01)
    ang = math.atan2(x2 - x, y2 - y)  # radians clockwise from grid north
    dx, dy = size * math.sin(ang), size * math.cos(ang)
    ax.annotate("", xy=(x + dx, y + dy), xytext=(x, y),
                arrowprops=dict(arrowstyle="-|>", lw=2, color="black", mutation_scale=18), zorder=30)
    ax.text(x + dx * 1.18, y + dy * 1.18, "N", ha="center", va="center", fontsize=12, weight="bold", zorder=30,
            path_effects=[pe.withStroke(linewidth=3, foreground="white")])
    ax.text(x, y - size * 0.22, f"pn. geogr.\n(zbieżność {math.degrees(ang):+.1f}°)", ha="center", va="top",
            fontsize=6.5, zorder=30, path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])


def label_streets(ax, roads_view, box, min_len=250, fontsize=7.5):
    placed: list[shapely.Point] = []
    named = roads_view[roads_view.highway.isin(MAJOR | {"residential", "unclassified"}) & roads_view["name"].notna()]
    named = named[~named["name"].str.startswith("Rondo")]
    inner = box.buffer(-120)
    for name, grp in sorted(named.groupby("name"), key=lambda kv: -kv[1].geometry.intersection(box).length.sum()):
        merged = shapely.line_merge(grp.geometry.intersection(inner).union_all())
        parts = list(getattr(merged, "geoms", [merged]))
        parts = [p for p in parts if p.geom_type == "LineString" and p.length >= min_len]
        if not parts:
            continue
        line = max(parts, key=lambda p: p.length)
        mid = line.interpolate(0.5, normalized=True)
        if any(mid.distance(q) < 350 for q in placed):
            mid = line.interpolate(0.3, normalized=True)
            if any(mid.distance(q) < 350 for q in placed):
                continue
        d = line.project(mid)
        p1, p2 = line.interpolate(max(d - 30, 0)), line.interpolate(min(d + 30, line.length))
        ang = math.degrees(math.atan2(p2.y - p1.y, p2.x - p1.x))
        if ang > 90:
            ang -= 180
        if ang < -90:
            ang += 180
        short = (name.replace("Generała ", "gen. ").replace("Księdza ", "ks. ").replace("Aleja ", "al. ")
                 .replace("Konstantego ", "").replace("Władysława ", "").replace("Stanisława ", ""))
        ax.text(mid.x, mid.y, short, rotation=ang, rotation_mode="anchor", ha="center", va="center",
                fontsize=fontsize, color="#202020", zorder=25,
                path_effects=[pe.withStroke(linewidth=2.8, foreground="white")])
        placed.append(mid)


def save_png(fig, path: Path, max_kb=400):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=fig.dpi)
    plt.close(fig)
    buf.seek(0)
    img = Image.open(buf).convert("RGB")
    img.save(path, format="PNG", optimize=True)
    if path.stat().st_size <= max_kb * 1024:
        return path.stat().st_size
    colours = 256
    while True:
        q = img.quantize(colors=colours, method=Image.Quantize.FASTOCTREE, dither=Image.Dither.NONE)
        q.save(path, format="PNG", optimize=True)
        if path.stat().st_size <= max_kb * 1024 or colours <= 48:
            break
        colours //= 2
    return path.stat().st_size


def render_area(layers, box, title, out: Path, stats=None, sub="", grid=False):
    roads, lu, b = layers["roads"], layers["landuse"], layers["buildings"]
    view = box.buffer(50)
    bx0, by0, bx1, by1 = box.bounds
    portrait = (by1 - by0) > (bx1 - bx0)
    if portrait:  # 2 x 3 km
        fig = plt.figure(figsize=(10.4, 10.6), dpi=100)
        ax = fig.add_axes([0.01, 0.035, 0.585, 0.86])
    else:  # 3 x 2 km
        fig = plt.figure(figsize=(14, 8.4), dpi=100)
        ax = fig.add_axes([0.01, 0.04, 0.775, 0.86])
    ax.set_facecolor("#fbfaf7")
    lu_v = lu[lu.intersects(view)]
    for kind, col in LANDUSE_COLOUR.items():
        s = lu_v[lu_v.landuse == kind]
        if len(s):
            s.plot(ax=ax, color=col, edgecolor="#b9a3c9" if kind == "industrial" else "none",
                   linewidth=0.6, zorder=1)
    b_v = b[b.intersects(view)].copy()
    b_v["a"] = b_v.area
    b_v[b_v.a < 2000].plot(ax=ax, color="#cfc8bf", edgecolor="#a79f95", linewidth=0.2, zorder=2)
    big = b_v[b_v.a >= 2000]
    if len(big):
        big.plot(ax=ax, color="#9b8f84", edgecolor="#6f655c", linewidth=0.4, zorder=2)
    r_v = roads[roads.intersects(view)]
    rail = r_v.iloc[0:0]
    for hw, (col, lw, z) in sorted(STYLE.items(), key=lambda kv: kv[1][2]):
        s = r_v[r_v.highway == hw]
        if len(s):
            s.plot(ax=ax, color="white", linewidth=lw + 1.4, zorder=z - 0.5)
            s.plot(ax=ax, color=col, linewidth=lw, zorder=z)
    rb = r_v[r_v.junction.isin(["roundabout", "circular"])]
    if len(rb):
        rb.plot(ax=ax, color="#7d3c98", linewidth=2.6, zorder=10)
    sig = layers["points"]
    sig = sig[(sig.kind == "highway=traffic_signals") & sig.within(view)]
    if len(sig):
        ax.scatter(sig.geometry.x, sig.geometry.y, s=22, marker="o", c="#e3242b", edgecolors="black",
                   linewidths=0.5, zorder=21)
    docks = layers["points"]
    docks = docks[docks.kind.isin(["amenity=loading_dock", "door=loading_dock"]) & docks.within(view)]
    if len(docks):
        ax.scatter(docks.geometry.x, docks.geometry.y, s=40, marker="s", c="#2e86c1", edgecolors="black",
                   linewidths=0.6, zorder=22)
    if stats is not None:
        rl = stats["_route_line"]
        ax.plot(*rl.xy, color="white", linewidth=9, zorder=18, solid_capstyle="round")
        ax.plot(*rl.xy, color=ROUTE_COLOUR, linewidth=6, zorder=19, alpha=0.9, solid_capstyle="round")
        if "_ext_line" in stats:
            el = stats["_ext_line"]
            ax.plot(*el.xy, color="white", linewidth=7, zorder=18)
            ax.plot(*el.xy, color=ROUTE_COLOUR, linewidth=4, zorder=19, linestyle=(0, (2, 1.2)))
        if stats["_inter_public"]:
            xs, ys = zip(*stats["_inter_public"])
            ax.scatter(xs, ys, s=30, facecolors="white", edgecolors=ROUTE_COLOUR, linewidths=1.6, zorder=20)
        sx, sy = rl.coords[0]
        ex, ey = rl.coords[-1]
        for hall in stats["depot"]["large_buildings_within_400m_of_start"]:
            if hall["name"] and hall["dist_from_start_m"] <= 100:
                hg = b[(b.osm_id == hall["osm_id"]) & (b.osm_type == hall["osm_type"])].geometry.iloc[0]
                rp = hg.representative_point()
                ax.text(rp.x, rp.y, f"{hall['name']}\n({hall['area_m2']:,} m²)".replace(",", " "), fontsize=8,
                        style="italic", ha="center", va="center", zorder=24, color="#2b2118",
                        path_effects=[pe.withStroke(linewidth=2.5, foreground="white")])
                break
        offs = stats.get("_label_offsets", {})
        for key, (px, py), txt in (("start", (sx, sy), "START\n(baza)"),
                                   ("end", (ex, ey), "KONIEC\n(trasa krajowa)")):
            ax.scatter([px], [py], s=170, c=ROUTE_COLOUR, edgecolors="white", linewidths=2, zorder=26,
                       marker="o")
            ax.annotate(txt, (px, py), xytext=offs.get(key, (14, 14)), textcoords="offset points", fontsize=9, weight="bold",
                        color=ROUTE_COLOUR, zorder=27, path_effects=[pe.withStroke(linewidth=3, foreground="white")])
    label_streets(ax, r_v, box)
    x0, y0, x1, y1 = box.bounds
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    if grid:
        for gx in np.arange(math.ceil(x0 / 250) * 250, x1, 250):
            ax.axvline(gx, color="#3070ff", lw=0.3, zorder=50)
            ax.text(gx, y0 + 20, f"{gx:.0f}", fontsize=5, rotation=90, color="#3070ff", zorder=50)
        for gy in np.arange(math.ceil(y0 / 250) * 250, y1, 250):
            ax.axhline(gy, color="#3070ff", lw=0.3, zorder=50)
            ax.text(x0 + 20, gy, f"{gy:.0f}", fontsize=5, color="#3070ff", zorder=50)
    span = x1 - x0
    sb = 500 if span <= 4000 else 2000
    draw_scalebar(ax, x1 - sb - span * 0.03, y0 + (y1 - y0) * 0.03, sb, f"{sb} m" if sb < 1000 else f"{sb // 1000} km")
    draw_north(ax, x1 - span * 0.04, y1 - (y1 - y0) * 0.16, (y1 - y0) * 0.07)
    handles = [
        Line2D([], [], color=STYLE["motorway"][0], lw=3.5, label="autostrada/ekspresowa (motorway)"),
        Line2D([], [], color=STYLE["trunk"][0], lw=3, label="krajowa / trunk"),
        Line2D([], [], color=STYLE["primary"][0], lw=2.5, label="główna (primary)"),
        Line2D([], [], color=STYLE["secondary"][0], lw=2, label="secondary"),
        Line2D([], [], color=STYLE["tertiary"][0], lw=1.8, label="tertiary"),
        Line2D([], [], color=STYLE["residential"][0], lw=1.1, label="lokalna / osiedlowa"),
        Line2D([], [], color=STYLE["service"][0], lw=1, label="dojazdowa (service)"),
        Line2D([], [], color="#7d3c98", lw=2.6, label="rondo"),
        Line2D([], [], marker="o", ls="", mfc="#e3242b", mec="black", ms=6, label="sygnalizacja (węzeł OSM)"),
        Line2D([], [], marker="s", ls="", mfc="#2e86c1", mec="black", ms=6, label="rampa (amenity=loading_dock)"),
        Patch(fc=LANDUSE_COLOUR["industrial"], ec="#b9a3c9", label="landuse=industrial"),
        Patch(fc="#9b8f84", ec="#6f655c", label="budynek ≥ 2000 m² (hala)"),
        Patch(fc="#cfc8bf", ec="#a79f95", label="budynek"),
    ]
    if stats is not None:
        handles.insert(0, Line2D([], [], color=ROUTE_COLOUR, lw=5, label=f"proponowana trasa ({stats['route']['length_m'] / 1000:.2f} km)"))
        handles.insert(1, Line2D([], [], marker="o", ls="", mfc="white", mec=ROUTE_COLOUR, mew=1.6, ms=6,
                                 label="skrzyżowanie na trasie"))
        if "_ext_line" in stats:
            ext_km = stats["route"]["extension_beyond_core_route"]["length_m"] / 1000
            handles.insert(1, Line2D([], [], color=ROUTE_COLOUR, lw=3.5, ls=(0, (2, 1.2)),
                                     label=f"przedłużenie do S8 (+{ext_km:.2f} km)"))
    leg = ax.legend(handles=handles, loc="upper left", bbox_to_anchor=(1.01, 1.0), fontsize=8.5,
                    framealpha=1.0, borderpad=0.8, labelspacing=0.7, title="Legenda", title_fontsize=9.5)
    leg.set_zorder(40)
    if stats is not None:
        rt = stats["route"]
        cov = rt["tag_coverage_by_length"]
        lines = [
            f"Długość trasy: {rt['length_m'] / 1000:.2f} km",
            f"Skrzyżowania (drogi publ.): {rt['intersections_with_public_roads']}",
            f"Wjazdy/zjazdy (service): {rt['junctions_with_service_roads_or_driveways']}",
            f"Ronda na trasie: {rt['roundabouts_traversed']}",
            f"Sygnalizacje na trasie: {rt['signalised_junctions_or_crossings']}",
            f"Przejścia dla pieszych (węzły trasy): {rt['pedestrian_crossings']}",
            "Pokrycie tagów (długość trasy):",
            f"  lanes {cov['lanes']:.0%} · maxspeed {cov['maxspeed']:.0%}",
            f"  turn:lanes {cov['turn:lanes']:.0%} · surface {cov['surface']:.0%}",
        ]
        if "extension_beyond_core_route" in rt:
            lines.insert(1, f"  + przedłużenie do S8: {rt['extension_beyond_core_route']['length_m'] / 1000:.2f} km")
        axr = ax.get_position()
        fig.text(axr.x1 + 0.012, axr.y0 + 0.005, "\n".join(lines), fontsize=8.5, va="bottom", ha="left",
                 family="DejaVu Sans", linespacing=1.5,
                 bbox=dict(boxstyle="round,pad=0.6", fc="#f1f4fa", ec=ROUTE_COLOUR, lw=1))
    fig.text(0.01, 0.985, title, fontsize=13, weight="bold", va="top")
    if sub:
        fig.text(0.01, 0.935, sub, fontsize=9.5, color="#404040", va="center")
    snap = load_manifest()["snapshot"]
    fig.text(0.99, 0.012, f"© OpenStreetMap contributors (ODbL) · Geofabrik extract {snap} · EPSG:2180 · "
             f"render: tools/worldgen/analyze_candidates.py", ha="right", fontsize=8, color="#303030")
    return save_png(fig, out)


def render_overview(layers, candidates_stats, out: Path):
    roads, lu = layers["roads"], layers["landuse"]
    box = shapely.box(764500, 586500, 786500, 602000)
    fig, ax = plt.subplots(figsize=(12, 8.8), dpi=100)
    fig.subplots_adjust(left=0.01, right=0.99, top=0.94, bottom=0.04)
    ax.set_facecolor("#fbfaf7")
    lu_v = lu[lu.intersects(box)]
    lu_v[lu_v.landuse == "industrial"].plot(ax=ax, color="#cdb4de", edgecolor="#8e6aa8", linewidth=0.4, zorder=1)
    r_v = roads[roads.intersects(box)]
    for hw in ("residential", "unclassified", "tertiary", "secondary", "primary", "trunk", "trunk_link",
               "motorway", "motorway_link"):
        col, lw, z = STYLE[hw]
        s = r_v[r_v.highway == hw]
        s.plot(ax=ax, color=col if hw not in ("residential", "unclassified") else "#d0d0d0",
               linewidth=lw * 0.55 if hw not in ("residential", "unclassified") else 0.3, zorder=z)
    # ref labels on trunk/motorway
    placed = []
    for ref, grp in r_v[r_v.highway.isin(["trunk", "motorway"]) & r_v.ref.notna()].groupby("ref"):
        geom = shapely.line_merge(grp.geometry.union_all())
        parts = sorted(getattr(geom, "geoms", [geom]), key=lambda p: -p.length)
        p = parts[0].interpolate(0.5, normalized=True)
        if any(p.distance(q) < 1200 for q in placed):
            p = parts[0].interpolate(0.2, normalized=True)
        placed.append(p)
        lab = " / ".join(("S" + x[1:] if x.startswith("S") else "DK" + x) if x.isdigit() and len(x) <= 2 or x.startswith("S")
                         else "DW" + x for x in ref.split(";"))
        ax.text(p.x, p.y, lab, fontsize=7.5, weight="bold", ha="center", va="center", zorder=35,
                bbox=dict(boxstyle="round,pad=0.25", fc="white", ec=STYLE["trunk"][0], lw=1))
    for st in candidates_stats:
        bx = st["_box"]
        ax.plot(*bx.exterior.xy, color=ROUTE_COLOUR, lw=1.8, zorder=31)
        ax.plot(*st["_route_line"].xy, color=ROUTE_COLOUR, lw=3.2, zorder=32)
        if "_ext_line" in st:
            ax.plot(*st["_ext_line"].xy, color=ROUTE_COLOUR, lw=2.4, ls=(0, (2, 1.2)), zorder=32)
        x0, y0, x1, y1 = bx.bounds
        ax.text(x0 + 60, y1 - 60, st["id"].split("_")[0], fontsize=15, weight="bold", color=ROUTE_COLOUR,
                ha="left", va="top", zorder=33, path_effects=[pe.withStroke(linewidth=3.5, foreground="white")])
    x0, y0, x1, y1 = box.bounds
    ax.set_xlim(x0, x1)
    ax.set_ylim(y0, y1)
    ax.set_aspect("equal")
    ax.set_xticks([])
    ax.set_yticks([])
    draw_scalebar(ax, x1 - 2000 - 600, y0 + 450, 2000, "2 km")
    draw_north(ax, x1 - 900, y1 - 2600, 1100)
    handles = [
        Line2D([], [], color=STYLE["motorway"][0], lw=2.5, label="ekspresowa S8 / S19"),
        Line2D([], [], color=STYLE["trunk"][0], lw=2.2, label="krajowa (trunk)"),
        Line2D([], [], color=STYLE["primary"][0], lw=1.8, label="primary"),
        Line2D([], [], color=STYLE["secondary"][0], lw=1.4, label="secondary"),
        Line2D([], [], color=STYLE["tertiary"][0], lw=1.1, label="tertiary"),
        Patch(fc="#cdb4de", ec="#8e6aa8", label="landuse=industrial"),
        Line2D([], [], color=ROUTE_COLOUR, lw=2, label="kandydat: obszar 3×2 km + trasa"),
    ]
    ax.legend(handles=handles, loc="lower left", fontsize=8.5, framealpha=0.92)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_title("Białystok — strefy przemysłowe (OSM) i kandydaci na obszar startowy (D4)", fontsize=13,
                 loc="left", weight="bold")
    snap = load_manifest()["snapshot"]
    fig.text(0.99, 0.012, f"© OpenStreetMap contributors (ODbL) · Geofabrik extract {snap} · EPSG:2180",
             ha="right", fontsize=8, color="#303030")
    return save_png(fig, out)


def industrial_zones(layers, top=12):
    lu = layers["landuse"]
    ind = lu[lu.landuse == "industrial"]
    d = gpd.GeoDataFrame(geometry=[ind.union_all().buffer(60).buffer(-60)], crs=WORK_CRS).explode(index_parts=False)
    d["ha"] = d.area / 1e4
    d = d.sort_values("ha", ascending=False).head(top)
    out = []
    for _, z in d.iterrows():
        c = z.geometry.representative_point()
        lon, lat = TO_WGS.transform(c.x, c.y)
        names = sorted(set(ind[ind.intersects(z.geometry)]["name"].dropna()))
        out.append({"ha": round(z.ha, 1), "point_epsg2180": [round(c.x), round(c.y)],
                    "point_wgs84": [round(lat, 5), round(lon, 5)], "osm_names": names[:6]})
    return out


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    layers = load_layers()
    roads = layers["roads"]
    g, coords, snap = build_graph(roads)
    nwi = node_way_index(roads)
    results = []
    for cand in CANDIDATES:
        path = route_through(g, coords, snap, cand["waypoints"])
        edges = path_edges(g, path)
        st = route_stats(cand, path, edges, coords, roads, layers, nwi)
        st["_label_offsets"] = cand.get("label_offsets", {})
        rt = st["route"]
        if cand.get("extension"):
            ext = route_through(g, coords, snap, cand["extension"], start_node=path[-1])
            ext_edges = path_edges(g, ext)
            st["_ext_line"] = shapely.LineString([coords[n] for n in ext])
            rt["extension_beyond_core_route"] = {
                "length_m": round(sum(d["length"] for _, _, d in ext_edges)),
                "streets_in_order": collapse(
                    roads.loc[d["way"]]["name"] if isinstance(roads.loc[d["way"]]["name"], str)
                    else f"<bez nazwy: {roads.loc[d['way']].highway}>" for _, _, d in ext_edges),
                "end_epsg2180": [round(v, 1) for v in coords[ext[-1]]],
            }
        sub = ("Obszar 3×2 km wokół proponowanej trasy (baza → wylot na drogę krajową). "
               "Liczby: docs/reports/map/candidates.json")
        png = OUT_DIR / f"candidate_{cand['id']}.png"
        size = render_area(layers, st["_box"], cand["title"], png, stats=st, sub=sub)
        st["png"] = png.relative_to(REPO_ROOT).as_posix()
        st["png_bytes"] = size
        results.append(st)
        print(f"[{cand['id']}] {rt['length_m']} m, {rt['streets_in_order']}  png={size // 1024} KB")
    ov = OUT_DIR / "overview_bialystok.png"
    size = render_overview(layers, results, ov)
    print(f"[overview] png={size // 1024} KB")
    man = load_manifest()
    report = {
        "generator": "tools/worldgen/analyze_candidates.py",
        "source": {"id": man["id"], "url": man["url"], "sha256": man["sha256"], "snapshot": man["snapshot"],
                   "license": man["license"], "attribution": man["attribution"]},
        "crs": WORK_CRS,
        "notes": [
            "Route = shortest drivable path (oneway respected) through authored waypoints.",
            "Intersections counted at route nodes shared with another drivable OSM way; service/driveway joins counted separately.",
            "Signalised junctions = clusters (<=80 m) of highway=traffic_signals nodes within 15 m of the route.",
            "Tag coverage = share of route length (or major-road length in the 3x2 km box) where the tag is present.",
            "low_confidence_ways = non-service ways on the route missing lanes and/or maxspeed (defaults would be needed).",
        ],
        "industrial_zones_top": industrial_zones(layers),
        "candidates": [{k: v for k, v in st.items() if not k.startswith("_")} for st in results],
    }
    (OUT_DIR / "candidates.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[report] {OUT_DIR / 'candidates.json'}")


if __name__ == "__main__":
    main()
