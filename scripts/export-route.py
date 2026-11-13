"""Export the start route of a region (depot gate -> national road) as a lane polyline for Unity.

    uv run --project tools/worldgen python scripts/export-route.py --region bialystok-industrial-c

Reads (never writes) the worldgen inputs: Data/Regions/<id>/region.yaml, roads.graph.json and
docs/reports/map/candidates.json; the path is the same shortest drivable path as
tools/worldgen/roads/build_world.py::route_polyline (networkx over roadgraph.to_digraph).
Writes Data/Regions/<id>/route_start.json:
    points  [[e, n], ...]  region-local metres (E = x - origin.x, N = y - origin.y), resampled every 2 m,
            centre of the rightmost lane in the direction of travel on the GENERATED carriageways
            (roads.pipeline.build_network + roads.route.lane_route: fork shifts and lane layout of the generator;
            the raw OSM axis ran along the kerb of shifted links, ADR 0076).
    maxspeed_kmh per point, edge id per point, total length.
Unity (scripts/import-region.ps1) turns it into a WorldRoute; heights come from raycasts on the imported collision.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--step", type=float, default=2.0)
    a = ap.parse_args()

    import networkx as nx
    import yaml
    import roadgraph

    rdir = REPO / "Data" / "Regions" / a.region
    region = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    # ADR 0166/0174: a region with authored route ends (route_endpoints.json) uses them, like build_world.route_polyline;
    # otherwise the D4 candidate route (region C).
    re_f = rdir / "route_endpoints.json"
    if re_f.exists():
        route = json.loads(re_f.read_text(encoding="utf-8"))
    else:
        cand = json.loads((REPO / "docs/reports/map/candidates.json").read_text(encoding="utf-8"))
        route = next(c for c in cand["candidates"] if c["id"] == region["candidate"])["route"]
    ox, oy = region["origin"]["x"], region["origin"]["y"]

    def nearest(xy):
        return min(graph["nodes"], key=lambda n: math.hypot(n["x"] - xy[0], n["y"] - xy[1]))["id"]

    g = roadgraph.to_digraph(graph)
    path = nx.shortest_path(g, nearest(route["start_epsg2180"]), nearest(route["end_epsg2180"]), weight="length")
    edges = {e["id"]: e for e in graph["edges"]}

    # lane path on the generated network (fork shifts, lane layout), not the raw OSM axis (ADR 0076)
    from roads import pipeline
    from roads.route import lane_route
    net, _, _, _ = pipeline.build_network(a.region, graph)
    node_xy = {n["id"]: (n["x"] - ox, n["y"] - oy) for n in graph["nodes"]}
    path_edges = [(g[u][v]["id"], u, v) for u, v in zip(path, path[1:])]
    R, eid_pt, _, length = lane_route(net, path_edges, node_xy, a.step)

    def _ms(ei):
        try:
            return float(edges[ei]["attrs"].get("maxspeed", {}).get("v"))
        except (TypeError, ValueError):
            return 0.0
    spd_pt = [_ms(ei) for ei in eid_pt]
    s = [length]
    out = {
        "schema": "truck-sim-pl/route/1",
        "region": a.region,
        "route": "start",
        "note": (route["description"] if re_f.exists() else "Depot gate (Kwadrat Park) -> DK8/DK19") + "; centre of the rightmost lane of the generated carriageways (roads.route, ADR 0076)",
        "frame": "region-local metres, E = x - origin.x, N = y - origin.y (EPSG:2180)",
        "length_m": round(float(s[-1]), 2),
        "step_m": a.step,
        "points_en": [[round(float(x), 3), round(float(y), 3)] for x, y in R],
        "maxspeed_kmh": spd_pt,
        "edge": eid_pt,
        "graph_nodes": path,
    }
    dst = rdir / "route_start.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=None, sort_keys=True) + "\n", encoding="utf-8")
    print(f"route {a.region}: {len(R)} points, {s[-1]:.0f} m -> {dst.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
