"""Route links for the streamed world (stream-gaps-s23): continue the route autopilot across tiles whose control route
does not end on the seam towards the next tile (Knyszyn Rynek -> DW671 -> knyszyn-w -> Tykocin; C -> Maczka).

    uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py           # rewrite the json
    uv run --project tools/worldgen python tools/worldgen/streaming/route_links.py --check   # exit 1 when stale

Input (git): Data/Streaming/route_links.yaml (authored links + corridors), Data/Regions/<id>/{region.yaml,
roads.graph.json, overrides, route_start.json, route_endpoints.json}.
Output: game/Assets/_Project/World/Runtime/Streaming/Resources/WorldStreaming/route_links.json
(JsonUtility: arrays of objects / float arrays only). Link points are tile-local metres (E = x - anchorX,
N = y - anchorY) of the centre of the rightmost lane, every 2 m, computed exactly as scripts/export-route.py
(pipeline.effective_graph -> roadgraph.to_digraph shortest path by length -> pipeline.build_network + roads.route.lane_route).
A link that starts `after_route: <tile>` starts at the last graph node of that tile's route_start.json.

Corridors: every consecutive tile pair must be edge neighbours and joined (route exit or link end of A == route entry or
link start of B, both on the shared seam, <= tile_graph.PORTAL_TOL_M). The corridor is cut at the first tile that is not
in Data/Regions (main stops at dw671-tykocin-01; the ring branch adds the tiles to Tykocin); `missing` lists the rest.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import yaml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(HERE))
import tile_graph as TG  # noqa: E402

SRC = REPO / "Data" / "Streaming" / "route_links.yaml"
REGIONS = REPO / "Data" / "Regions"
OUT = TG.OUT.parent / "route_links.json"
SCHEMA = "truck-sim-pl/route-links/1"
STEP_M = 2.0
BLEND_M = 60.0     # WORKING_VALUE: length of the lateral lane shift at a link head / tail
JOIN_TOL_M = 3.0   # = WorldStreamer.routeJoinM: link start vs the path end it continues
STOP_TOL_M = 3.0   # ADR 0303: a stop point lies within this of the link lane (the lane centre, not the kerb)


def _region(rid: str, regions: Path) -> dict:
    return yaml.safe_load((regions / rid / "region.yaml").read_text(encoding="utf-8"))


def _route(rid: str, regions: Path) -> dict | None:
    f = regions / rid / "route_start.json"
    return json.loads(f.read_text(encoding="utf-8")) if f.exists() else None


def lane_path(rid: str, start_node: str | None, start_xy, end_xy, regions: Path = REGIONS, vias=(), came_from=None):
    """Lane polyline (tile-local E/N every STEP_M), speed limits, length, graph nodes - export-route.py rules.
    came_from = graph node the path arrived from at start_node (an `after_route` link continues a route): the edge back
    to it is not used, so the link drives on instead of turning the articulated truck round on the spot (seams-fix-s23:
    the knyszyn route ends at Rynek and the shortest way to DW671 was straight back)."""
    import networkx as nx
    import roadgraph
    from roads import pipeline
    from roads.route import lane_route

    rdir = regions / rid
    graph = pipeline.effective_graph(rid, json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8")))
    reg = _region(rid, regions)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    ids = {n["id"] for n in graph["nodes"]}

    def nearest(xy):
        return min(graph["nodes"], key=lambda n: math.hypot(n["x"] - xy[0], n["y"] - xy[1]))["id"]

    u = start_node if start_node in ids else (start_node + "s" if start_node and start_node + "s" in ids else nearest(start_xy))
    v = nearest(end_xy)
    g = roadgraph.to_digraph(graph)
    pre = arrival_edge(g, u, came_from)
    stops = [u, *[nearest(p) for p in vias], v]
    path = [u]
    for a_, b_ in zip(stops, stops[1:]):
        path += nx.shortest_path(g, a_, b_, weight="length")[1:]
    edges = {e["id"]: e for e in graph["edges"]}
    net, _, _, _ = pipeline.build_network(rid, graph)
    node_xy = {n["id"]: (n["x"] - ox, n["y"] - oy) for n in graph["nodes"]}
    path_edges = [(g[a][b]["id"], a, b) for a, b in zip(path, path[1:])]
    if pre is not None:
        # the edge the route arrived on goes first, so lane_route rounds the corner at start_node like any other joint
        # of a route (JOINT_ROUND_M); the link then starts where that rounded lane passes closest to the route end
        # (start_xy) and its head is blended onto that point by build()
        pre_id, pre_len = pre
        pts, eid_pt, _, _ = lane_route(net, [(pre_id, came_from, u)] + path_edges, node_xy, STEP_M)
        q = np.asarray(start_xy, float) - np.array([ox, oy])
        n_pre = int(math.ceil((pre_len + 2.0 * JOIN_TOL_M) / STEP_M)) + 1
        k = int(np.argmin(np.hypot(*(pts[:n_pre] - q).T)))
        pts, eid_pt = pts[k:], eid_pt[k:]
        length = float(np.sum(np.hypot(*np.diff(pts, axis=0).T)))
    else:
        pts, eid_pt, _, length = lane_route(net, path_edges, node_xy, STEP_M)

    def ms(ei):
        try:
            return float(edges[ei]["attrs"].get("maxspeed", {}).get("v"))
        except (TypeError, ValueError, AttributeError):
            return 0.0
    nodes = {n["id"]: n for n in graph["nodes"]}
    end_node = nodes[v]
    return {"points": [[round(float(x), 3), round(float(y), 3)] for x, y in pts],
            "maxspeed": [ms(e) for e in eid_pt], "length": float(length), "nodes": path,
            "end_node_xy": [end_node["x"], end_node["y"]], "origin": (ox, oy)}


def arrival_edge(g, u, came_from):
    """(id, length) of the edge came_from -> u the route arrived on, or None (no after_route / no such edge). Removes
    the edge back u -> came_from from g (in place) when it exists, so the link does not turn the articulated vehicle
    round on the spot. Codex review s24 (ADR 0289): the arrival edge used to be looked up only when the back edge
    existed, so a link continuing a route that came in along a ONE-WAY street got no rounded start corner."""
    if came_from is None or not g.has_edge(came_from, u):
        if came_from is not None and g.has_edge(u, came_from):
            g.remove_edge(u, came_from)
        return None
    d = g[came_from][u]
    pre = (d["id"], float(d["length"]))
    if g.has_edge(u, came_from):
        g.remove_edge(u, came_from)
    return pre


def _blend(pts: list[list[float]], target, head: bool) -> float:
    """Shift the first (head) / last (tail) BLEND_M metres of pts so that its end point lands on target, linearly fading
    the offset to 0 BLEND_M along the path (a lane change of <= ~3 m over 60 m instead of a step at the join).
    Returns the offset applied at the end point [m]."""
    idx = range(len(pts)) if head else range(len(pts) - 1, -1, -1)
    idx = list(idx)
    p0 = pts[idx[0]]
    dx, dy = target[0] - p0[0], target[1] - p0[1]
    s = 0.0
    prev = p0[:]
    for i in idx:
        q = pts[i]
        s += math.hypot(q[0] - prev[0], q[1] - prev[1])
        prev = q[:]
        w = max(0.0, 1.0 - s / BLEND_M)
        if w <= 0.0:
            break
        q[0] += dx * w
        q[1] += dy * w
    return math.hypot(dx, dy)


def _swing(pts: list[list[float]], near, left_m: float, half_m: float) -> float:
    """Shift the path sideways (left_m > 0 = to the left of the travel direction) around the path point nearest to near,
    with a raised-cosine weight over +-half_m along the path (0 at both ends, left_m at the centre). knyszyn-r24 (ADR 0289
    'Recenzja s24'): the right turn Tykocka -> DK65 W at the compact roundabout of Knyszyn follows the right-lane centre
    through a ~7 m corner, and the semitrailer cut the kerb corner between the arms (15 tyre points off the hard surface,
    qa/link_swept_check.py); a driver swings wide into the ring there. Returns the station [m] of the centre."""
    P = np.asarray(pts, float)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    k = int(np.argmin(np.hypot(*(P - np.asarray(near, float)).T)))
    d = np.gradient(P, axis=0)
    d /= np.maximum(np.linalg.norm(d, axis=1), 1e-9)[:, None]
    nrm = np.column_stack([-d[:, 1], d[:, 0]])
    u = (s - s[k]) / half_m
    w = np.where(np.abs(u) < 1.0, 0.5 * (1.0 + np.cos(np.pi * u)), 0.0)
    for i in np.nonzero(w)[0]:
        pts[i][0] += float(nrm[i, 0] * left_m * w[i])
        pts[i][1] += float(nrm[i, 1] * left_m * w[i])
    return float(s[k])


def _stop(pts: list[list[float]], maxspeed: list[float], stop_xy):
    """ADR 0303: cut the link at the lane point nearest to stop_xy (EPSG:2180): the route autopilot stops at the path
    end, the GPS goal of the trip is the same point. The stop must lie on the link (<= STOP_TOL_M from its lane), and
    not in its first or last STEP_M (a stop is an authored spot along a street, not a graph node).
    Returns (points, maxspeed, length, distance of the stop point from the lane)."""
    P = np.asarray(pts, float)
    d = np.hypot(*(P - np.asarray(stop_xy, float)).T)
    k = int(np.argmin(d))
    if d[k] > STOP_TOL_M or k < 1 or k >= len(P) - 1:
        raise SystemExit(f"stop_epsg2180 {stop_xy} not on the link (nearest lane point {d[k]:.2f} m, index {k}/{len(P)})")
    P = P[:k + 1]
    length = float(np.sum(np.hypot(*np.diff(P, axis=0).T)))
    return P.tolist(), list(maxspeed[:k + 1]), length, float(d[k])


def _resample(pts: list[list[float]], maxspeed: list[float]):
    """Back to STEP_M spacing after a swing (the outside of the bend is stretched); speed limit of the nearest
    original point. Returns (points, maxspeed, length)."""
    P = np.asarray(pts, float)
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    n = max(2, int(math.ceil(s[-1] / STEP_M)) + 1)
    si = np.linspace(0.0, s[-1], n)
    out = [[float(np.interp(x, s, P[:, 0])), float(np.interp(x, s, P[:, 1]))] for x in si]
    k = np.clip(np.searchsorted(s, si), 0, len(s) - 1)
    return out, [maxspeed[int(i)] for i in k], float(s[-1])


def build(src: Path = SRC, regions: Path = REGIONS) -> dict:
    cfg = yaml.safe_load(src.read_text(encoding="utf-8"))
    tiles = {t["id"]: t for t in TG.load_tiles(regions)}
    links = []
    for L in cfg["links"]:
        rid = L["tile"]
        if rid not in tiles:
            continue
        t = tiles[rid]
        start_node, start_xy, came_from = None, L.get("start_epsg2180"), None
        for key, idx in (("after_route", -1), ("replaces_route", 0)):
            if L.get(key):
                r = _route(L[key], regions)
                reg = _region(L[key], regions)
                start_node = r["graph_nodes"][idx]
                if key == "after_route" and len(r["graph_nodes"]) >= 2:
                    came_from = r["graph_nodes"][-2]
                e, n = r["points_en"][idx]
                start_xy = [e + reg["origin"]["x"], n + reg["origin"]["y"]]
        lp = lane_path(rid, start_node, start_xy, L["end_epsg2180"], regions, L.get("via_epsg2180", []), came_from)
        ox, oy = lp["origin"]
        assert abs(ox - t["anchorX"]) < 1e-6 and abs(oy - t["anchorY"]) < 1e-6, rid
        pts = [[p[0] + ox, p[1] + oy] for p in lp["points"]]   # EPSG:2180
        blend = {}
        if came_from is not None:     # exact join on the route end (lane_path cut the rounded corner nearest to it)
            blend["head"] = _blend(pts, start_xy, head=True)
        if L.get("head_from"):
            kind, ref = L["head_from"].split(":", 1)
            if kind == "route":       # ADR 0292: first BLEND_M m shifted onto the END of a neighbour tile's route
                r0 = _route(ref, regions)
                reg0 = _region(ref, regions)
                src_xy = [r0["points_en"][-1][0] + reg0["origin"]["x"], r0["points_en"][-1][1] + reg0["origin"]["y"]]
            else:
                src = next(x for x in links if x["id"] == ref)
                src_xy = [src["endX"], src["endY"]]
            blend["head"] = _blend(pts, src_xy, head=True)
        if L.get("tail_to"):
            r2 = _route(L["tail_to"].split(":", 1)[1], regions)
            reg2 = _region(L["tail_to"].split(":", 1)[1], regions)
            tgt = [r2["points_en"][0][0] + reg2["origin"]["x"], r2["points_en"][0][1] + reg2["origin"]["y"]]
            blend["tail"] = _blend(pts, tgt, head=False)
        maxspeed, length = lp["maxspeed"], lp["length"]
        if L.get("swing"):
            for sw in L["swing"]:
                _swing(pts, sw["near_epsg2180"], float(sw["left_m"]), float(sw["half_m"]))
                blend["swing_left"] = float(sw["left_m"])
            pts, maxspeed, length = _resample(pts, maxspeed)
        if L.get("stop_epsg2180"):    # ADR 0303: the trip ends here (parking spot), not at the end graph node
            pts, maxspeed, length, blend["stop_offset"] = _stop(pts, maxspeed, L["stop_epsg2180"])
        loc = [[round(x - ox, 3), round(y - oy, 3)] for x, y in pts]
        links.append({
            "id": L["id"], "tile": rid, "destination": L.get("destination", "any"),
            "afterRoute": L.get("after_route", ""), "replacesRoute": L.get("replaces_route", ""),
            "note": L.get("note", ""), "blendM": {k: round(v, 3) for k, v in blend.items()},
            "lengthM": round(length, 2),
            "e": [p[0] for p in loc], "n": [p[1] for p in loc],
            "maxspeedKmh": maxspeed,
            "startX": round(pts[0][0], 3), "startY": round(pts[0][1], 3),
            "endX": round(pts[-1][0], 3), "endY": round(pts[-1][1], 3),
            "graphNodes": lp["nodes"],
        })
    corridors = [corridor(c, tiles, links, regions) for c in cfg.get("corridors", [])]
    return {"schema": SCHEMA, "generator": "tools/worldgen/streaming/route_links.py (stream-gaps-s23)",
            "frame": "link points: tile-local metres E = x - anchorX, N = y - anchorY (EPSG:2180, tile_graph.json anchors)",
            "links": links, "corridors": corridors}


def _ends(rid: str, regions: Path, links: list[dict], destination: str = "any"):
    """(entries, exits) of a tile in EPSG:2180: lane points of its route start / end and of its links."""
    entries, exits = [], []
    r = _route(rid, regions)
    replaced = any(L["replacesRoute"] == rid and L["destination"] in ("any", destination) for L in links)
    if r is not None and not replaced:
        reg = _region(rid, regions)
        ox, oy = reg["origin"]["x"], reg["origin"]["y"]
        entries.append(("route", [r["points_en"][0][0] + ox, r["points_en"][0][1] + oy]))
        exits.append(("route", [r["points_en"][-1][0] + ox, r["points_en"][-1][1] + oy]))
    for L in links:
        if L["tile"] == rid and L["destination"] in ("any", destination):
            entries.append(("link:" + L["id"], [L["startX"], L["startY"]]))
            exits.append(("link:" + L["id"], [L["endX"], L["endY"]]))
    return entries, exits


def corridor(c: dict, tiles: dict, links: list[dict], regions: Path) -> dict:
    present, missing = [], []
    for rid in c["tiles"]:
        (missing if missing or rid not in tiles else present).append(rid)
    joins = []
    for a, b in zip(present, present[1:]):
        side, seam = TG.side_of(tiles[a], tiles[b])
        dest = c.get("destination", "any")
        _, exits = _ends(a, regions, links, dest)
        entries, _ = _ends(b, regions, links, dest)
        best = None
        for ka, pa in exits:
            for kb, pb in entries:
                d = math.hypot(pa[0] - pb[0], pa[1] - pb[1])
                if best is None or d < best[0]:
                    best = (d, ka, kb, pa)
        d, ka, kb, pa = best
        joins.append({"from": a, "to": b, "side": side or "", "seamM": round(seam, 3), "exit": ka, "entry": kb,
                      "x": round(pa[0], 3), "y": round(pa[1], 3), "gapM": round(d, 3)})
    return {"id": c["id"], "destination": c.get("destination", "any"), "tiles": present, "missing": missing, "joins": joins}


def dumps(d: dict) -> str:
    return json.dumps(d, ensure_ascii=False, indent=1) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--out", type=Path, default=OUT)
    a = ap.parse_args(argv)
    d = build()
    text = dumps(d)
    if a.check:
        cur = a.out.read_text(encoding="utf-8") if a.out.exists() else ""
        if cur != text:
            print(f"STALE: {a.out} (run tools/worldgen/streaming/route_links.py)")
            return 1
        print(f"OK: {a.out}")
        return 0
    a.out.parent.mkdir(parents=True, exist_ok=True)
    a.out.write_text(text, encoding="utf-8", newline="\n")
    for L in d["links"]:
        print(f"link {L['id']}: {L['tile']} {L['lengthM']:.0f} m, {len(L['e'])} pts")
    for c in d["corridors"]:
        bad = [j for j in c["joins"] if len(j["side"]) != 1 or j["gapM"] > TG.PORTAL_TOL_M]
        print(f"corridor {c['id']}: {len(c['tiles'])} tiles, missing {len(c['missing'])}, bad joins {[(j['from'], j['to'], j['gapM']) for j in bad]}")
    print(f"-> {a.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
