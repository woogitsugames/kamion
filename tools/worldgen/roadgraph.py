"""Canonical road graph for a tile, from OSM (ODbL) with per-field provenance + confidence.

Graph model
  node  = OSM node that is a way end, shared by >= 2 drivable ways, or a synthetic tile-boundary cut.
  edge  = directed-agnostic piece of one OSM way between two graph nodes (direction rules in `oneway`).
Every attribute in `edge.attrs` is {"v": value, "src": provenance, "conf": confidence}:
  src  ∈ osm | derived | default | bdot10k | authored_override
  conf ∈ high | medium | low
`edge.low_confidence` lists attribute names whose conf == "low" (= must be checked / photographed).

Defaults (WORKING_VALUE, documented, never silent):
  maxspeed  50 km/h in built-up area (Prawo o ruchu drogowym art. 20 ust. 1 pkt 1, 05:00–23:00), conf low
  lanes     1 per direction (oneway: 1; two-way: 2) except trunk/primary two-way = 2, conf low
  surface   asphalt, conf low
  oneway    no (unless implied by junction=roundabout / motorway), conf medium
"""

from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
import shapely
from shapely.geometry import LineString

DRIVABLE = {
    "motorway", "motorway_link", "trunk", "trunk_link", "primary", "primary_link",
    "secondary", "secondary_link", "tertiary", "tertiary_link", "unclassified",
    "residential", "living_street", "service",
}
# ADR 0164: truck-limit tags beyond maxweight/maxheight/hgv. They must reach roads.graph.json (and from there KRTG v2,
# navgraph/build_route_graph.py) - dropping them silently made the GPS route a 11.5 t drive axle over maxaxleload=10 roads.
# Every tag here must also be extracted by osm_extract.ROAD_TAGS (test_truck_tags_0164 keeps both lists in sync).
TRUCK_LIMIT_TAGS = ("maxaxleload", "maxlength", "maxweight:hgv", "hgv:conditional", "maxgvweightrating:hgv")
RAW_TAGS = ("name", "ref", "lanes", "lanes:forward", "lanes:backward", "turn:lanes", "turn:lanes:forward",
            "turn:lanes:backward", "maxspeed", "oneway", "junction", "surface", "bridge", "tunnel", "layer",
            "width", "maxweight", "maxheight", "hgv", "access", "service", "destination", "destination:ref", "int_ref",
            *TRUCK_LIMIT_TAGS)
GRAPH_SCHEMA = "truck-sim-pl/road-graph/1"
# BDOT10k MATERIALNAWIERZCHNI -> OSM surface (used only when OSM has no surface tag)
BDOT_SURFACE = {"masa bitumiczna": "asphalt", "kostka prefabrykowana": "paving_stones", "beton": "concrete",
                "płyty betonowe": "concrete:plates", "grunt naturalny": "ground", "żwir": "gravel",
                "kostka kamienna": "sett", "tłuczeń": "compacted"}


def _num(v):
    try:
        return float(str(v).split(";")[0].strip().replace(",", "."))
    except (TypeError, ValueError):
        return None


def _a(v, src, conf):
    return {"v": v, "src": src, "conf": conf}


def edge_attrs(tags: dict, length_m: float) -> dict:
    hw = tags["highway"]
    a: dict[str, dict] = {"highway": _a(hw, "osm", "high")}
    for k in ("name", "ref"):
        if tags.get(k):
            a[k] = _a(tags[k], "osm", "high")
    # oneway
    ow = tags.get("oneway")
    implied = tags.get("junction") in ("roundabout", "circular") or hw in ("motorway", "motorway_link")
    if ow in ("yes", "true", "1"):
        a["oneway"] = _a("yes", "osm", "high")
    elif ow == "-1":
        a["oneway"] = _a("-1", "osm", "high")
    elif ow == "no":
        a["oneway"] = _a("no", "osm", "high")
    elif implied:
        a["oneway"] = _a("yes", "derived", "high")
    else:
        a["oneway"] = _a("no", "default", "medium")
    one = a["oneway"]["v"] != "no"
    # lanes
    if tags.get("lanes") and _num(tags["lanes"]):
        a["lanes"] = _a(int(_num(tags["lanes"])), "osm", "high")
    else:
        a["lanes"] = _a(1 if one else 2, "default", "low")
    for k in ("lanes:forward", "lanes:backward"):
        if tags.get(k) and _num(tags[k]):
            a[k] = _a(int(_num(tags[k])), "osm", "high")
    # turn lanes: only meaningful on approaches; absence is low confidence only on major roads
    for k in ("turn:lanes", "turn:lanes:forward", "turn:lanes:backward"):
        if tags.get(k):
            a[k] = _a(tags[k], "osm", "high")
    if not any(k in a for k in ("turn:lanes", "turn:lanes:forward", "turn:lanes:backward")) and \
            hw in ("trunk", "primary", "secondary", "tertiary", "trunk_link", "primary_link"):
        a["turn:lanes"] = _a(None, "default", "low")
    # maxspeed
    ms = tags.get("maxspeed")
    if ms and _num(ms):
        a["maxspeed"] = _a(int(_num(ms)), "osm", "high")
    elif ms:  # e.g. "PL:urban"
        a["maxspeed"] = _a(50 if "urban" in ms else None, "derived", "medium")
    else:
        a["maxspeed"] = _a(50, "default", "low")
    # surface
    a["surface"] = _a(tags["surface"], "osm", "high") if tags.get("surface") else _a("asphalt", "default", "low")
    # structure / layering
    br = tags.get("bridge")
    if br and br != "no":
        a["bridge"] = _a(br, "osm", "high")
        if tags.get("layer") is None:
            a["layer"] = _a(1, "default", "low")   # bridge without layer = QA issue (docs/05 §4.12)
    if tags.get("tunnel") and tags["tunnel"] != "no":
        a["tunnel"] = _a(tags["tunnel"], "osm", "high")
    if tags.get("layer") is not None and _num(tags["layer"]) is not None:
        a["layer"] = _a(int(_num(tags["layer"])), "osm", "high")
    if tags.get("width") and _num(tags["width"]):
        a["width"] = _a(_num(tags["width"]), "osm", "medium")
    for k in ("junction", "maxweight", "maxheight", "hgv", "access", "service", "destination", "destination:ref",
              *TRUCK_LIMIT_TAGS):
        if tags.get(k):
            a[k] = _a(tags[k], "osm", "high")
    return a


def build(roads, points, bbox, bdot_roads=None) -> dict:
    """roads: GeoDataFrame from osm_extract (EPSG:2180) with node_ids; points: OSM point layer."""
    x0, y0, x1, y1 = bbox
    tile = shapely.box(*bbox)
    drv = roads[roads.highway.isin(DRIVABLE)]
    drv = drv[drv.geometry.intersects(tile.buffer(1.0))]
    drv = drv[~drv.service.isin(["parking_aisle", "drive-through"]) | drv.service.isna()]

    # which OSM nodes are graph nodes
    use = defaultdict(int)
    for nids in drv.node_ids:
        for i, n in enumerate(nids):
            use[n] += 2 if i in (0, len(nids) - 1) else 1
    is_graph = {n for n, c in use.items() if c >= 2}

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    def add_node(nid: str, xy, **kw):
        if nid not in nodes:
            nodes[nid] = {"id": nid, "x": round(xy[0], 3), "y": round(xy[1], 3), **kw}

    for row in drv.sort_values("osm_id").itertuples():
        tags = {"highway": row.highway}
        src = roads.loc[row.Index]  # itertuples mangles 'turn:lanes' etc.; read the frame row
        for k in RAW_TAGS:
            if k in roads.columns and src[k] is not None and not (isinstance(src[k], float) and math.isnan(src[k])):
                tags[k] = src[k]
        coords = list(row.geometry.coords)
        nids = row.node_ids
        cut = [0] + [i for i in range(1, len(nids) - 1) if nids[i] in is_graph] + [len(nids) - 1]
        for a_i, b_i in zip(cut, cut[1:]):
            pts = coords[a_i:b_i + 1]
            line = LineString(pts)
            if not line.intersects(tile):
                continue
            na, nb = f"n{nids[a_i]}", f"n{nids[b_i]}"
            eid = f"w{row.osm_id}:{nids[a_i]}-{nids[b_i]}"
            pieces = [line] if tile.contains(line) else [g for g in getattr(line.intersection(tile), "geoms",
                                                                            [line.intersection(tile)])
                                                      if g.geom_type == "LineString" and g.length > 0.01]
            for k, piece in enumerate(pieces):
                pc = list(piece.coords)
                s_inside = math.dist(pc[0], pts[0]) < 1e-6
                e_inside = math.dist(pc[-1], pts[-1]) < 1e-6
                sid = na if s_inside else f"B{eid}:{k}s"
                tid = nb if e_inside else f"B{eid}:{k}e"
                add_node(sid, pc[0], **({"osm_node": int(nids[a_i])} if s_inside else {"boundary": True}))
                add_node(tid, pc[-1], **({"osm_node": int(nids[b_i])} if e_inside else {"boundary": True}))
                length = piece.length
                attrs = edge_attrs(tags, length)
                edges.append({
                    "id": eid if len(pieces) == 1 else f"{eid}#{k}",
                    "osm_way": int(row.osm_id), "from": sid, "to": tid, "length_m": round(length, 3),
                    "geometry": [[round(x, 3), round(y, 3)] for x, y in pc],
                    "clipped": not (s_inside and e_inside),
                    "attrs": attrs,
                    "low_confidence": sorted(k2 for k2, v in attrs.items() if v["conf"] == "low"),
                })

    # node features from OSM points (traffic signals, crossings, give way/stop)
    pt_by_osm = {}
    for prow in points.itertuples():
        pt_by_osm[int(prow.osm_id)] = prow.kind
    for n in nodes.values():
        if "osm_node" in n and n["osm_node"] in pt_by_osm:
            n["feature"] = pt_by_osm[n["osm_node"]]
    # node features also live on intermediate vertices: attach signals to nearest graph node <= 15 m
    signals = points[points.kind == "highway=traffic_signals"]
    if len(signals):
        ids = sorted(nodes)
        xy = np.array([[nodes[i]["x"], nodes[i]["y"]] for i in ids])
        for p in signals.geometry:
            if not tile.contains(p):
                continue
            d = np.hypot(xy[:, 0] - p.x, xy[:, 1] - p.y)
            j = int(d.argmin())
            if d[j] <= 15.0:
                nodes[ids[j]].setdefault("signals_nearby", True)

    if bdot_roads is not None:
        attach_bdot(edges, bdot_roads)
        for e in edges:
            e["low_confidence"] = sorted(k for k, v in e["attrs"].items() if v["conf"] == "low")

    edges.sort(key=lambda e: e["id"])
    deg = defaultdict(int)
    for e in edges:
        deg[e["from"]] += 1
        deg[e["to"]] += 1
    for nid, n in nodes.items():
        n["degree"] = deg[nid]
    return {"schema": GRAPH_SCHEMA, "crs": "EPSG:2180", "bbox": list(bbox),
            "nodes": [nodes[k] for k in sorted(nodes)], "edges": edges}


def attach_bdot(edges: list[dict], bdot) -> None:
    """Attach BDOT10k carriageway width/material to edges (nearest SKJZ/SKDR line, <= 8 m, angle <= 25°).

    BDOT10k SZEROKOSCNAWIERZCHNI is carriageway surface width (m, 1:10k accuracy) -> `width` only when
    OSM has no width; provenance bdot10k, conf medium. Disagreements are left to the QA report.
    """
    geoms = list(bdot.geometry)
    tree = shapely.STRtree(geoms)
    for e in edges:
        g = e["geometry"]
        if len(g) < 2:
            continue
        line = LineString(g)
        mid = line.interpolate(0.5, normalized=True)
        p0 = line.interpolate(max(0.0, line.length / 2 - 2.0))
        p1 = line.interpolate(min(line.length, line.length / 2 + 2.0))
        ang = math.atan2(p1.y - p0.y, p1.x - p0.x)
        best, bd = None, 8.0
        for j in tree.query(mid.buffer(8.0)):
            cand = geoms[int(j)]
            d = cand.distance(mid)
            if d > bd:
                continue
            s = cand.project(mid)
            q0 = cand.interpolate(max(0.0, s - 2.0))
            q1 = cand.interpolate(min(cand.length, s + 2.0))
            ca = math.atan2(q1.y - q0.y, q1.x - q0.x)
            dang = abs((math.degrees(ang - ca) + 90) % 180 - 90)
            if dang <= 25:
                best, bd = int(j), d
        if best is None:
            continue
        r = bdot.iloc[best]
        info = {"lokalny_id": r["LOKALNYID"], "dist_m": round(bd, 2)}
        w = r.get("SZEROKOSCNAWIERZCHNI")
        if w is not None and not (isinstance(w, float) and math.isnan(w)):
            info["width_m"] = float(w)
            if "width" not in e["attrs"]:
                e["attrs"]["width"] = _a(float(w), "bdot10k", "medium")
        mat = r.get("MATERIALNAWIERZCHNI")
        if mat:
            info["material"] = mat
            if e["attrs"]["surface"]["src"] == "default" and mat in BDOT_SURFACE:
                e["attrs"]["surface"] = _a(BDOT_SURFACE[mat], "bdot10k", "medium")
        cls = r.get("KLASADROGI")
        if cls:
            info["klasa"] = cls
        e["bdot10k"] = info


def to_digraph(graph: dict):
    """networkx DiGraph honouring `oneway` (used by tests and QA)."""
    import networkx as nx
    g = nx.DiGraph()
    for n in graph["nodes"]:
        g.add_node(n["id"], x=n["x"], y=n["y"])
    for e in graph["edges"]:
        ow = e["attrs"]["oneway"]["v"]
        if ow in ("yes", "no"):
            g.add_edge(e["from"], e["to"], id=e["id"], length=e["length_m"])
        if ow in ("-1", "no"):
            g.add_edge(e["to"], e["from"], id=e["id"], length=e["length_m"])
    return g
