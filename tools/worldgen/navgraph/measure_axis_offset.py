"""Measure the lateral offset of the routing-graph edge lines from the generated carriageway axes (ADR 0144).

For every road graph edge that has a carriageway axis (roads.pipeline.build_network, see
build_route_graph.load_carriageway_axes) this samples the edge's routing-graph polyline (with the raw OSM
axis = "before", or with the carriageway axis = "after") and measures the distance of each sample point to
the carriageway axis polyline: max and mean per edge, top 10 by max.

Usage:
  uv run --project tools/worldgen python tools/worldgen/navgraph/measure_axis_offset.py --region bialystok-industrial-c
  uv run --project tools/worldgen python tools/worldgen/navgraph/measure_axis_offset.py --region bialystok-industrial-c --after
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import build_route_graph as brg  # noqa: E402


def _pt_seg_dist(q, a, b) -> float:
    ax, ay = a
    bx, by = b
    dx, dy = bx - ax, by - ay
    l2 = dx * dx + dy * dy
    t = 0.0 if l2 == 0 else max(0.0, min(1.0, ((q[0] - ax) * dx + (q[1] - ay) * dy) / l2))
    return math.hypot(q[0] - (ax + t * dx), q[1] - (ay + t * dy))


def edge_offsets(route_pts, axis) -> tuple[float, float]:
    """(max, mean) distance of the route polyline points from the carriageway axis polyline, metres."""
    ds = [min(_pt_seg_dist(q, axis[i], axis[i + 1]) for i in range(len(axis) - 1)) for q in route_pts]
    return max(ds), sum(ds) / len(ds)


def measure(region: str, after: bool):
    """-> (rows, n_axes): rows = [(max_m, mean_m, edge_id, osm_way)] sorted by max desc, over edges with an axis."""

    rdir = os.path.join(brg.REPO, "Data", "Regions", region)
    graph = json.load(open(os.path.join(rdir, "roads.graph.json"), encoding="utf-8"))
    rows = json.load(open(os.path.join(rdir, "turn_restrictions.json"), encoding="utf-8"))["restrictions"]
    origin = brg.read_origin(rdir)
    axes = brg.load_carriageway_axes(region, graph)
    t = brg.build(graph, origin, rows, axes if after else None)
    by_id = {e["id"]: e for e in graph["edges"]}
    out = []
    for e in t["edges"]:
        src = by_id.get(e["id"])
        if src is None or e["id"] not in axes:
            continue
        mx, mn = edge_offsets(e["pts"], axes[e["id"]])
        out.append((mx, mn, e["id"], src.get("osm_way")))
    out.sort(key=lambda r: r[0], reverse=True)
    return out, len(axes)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--after", action="store_true", help="measure the build WITH carriageway-axis geometry")
    args = ap.parse_args(argv)
    rows, n_axes = measure(args.region, args.after)
    label = "PO (geometria = oś jezdni)" if args.after else "PRZED (geometria = oś OSM)"
    print(f"{args.region} {label}: krawędzie z osią {n_axes}, zmierzone {len(rows)}")
    print(f"{'max_m':>8} {'mean_m':>8}  edge  osm_way")
    for mx, mn, eid, way in rows[:10]:
        print(f"{mx:8.3f} {mn:8.3f}  {eid}  {way}")
    allmx = [r[0] for r in rows]
    if allmx:
        print(f"wszystkie: max {max(allmx):.3f} m, średnia maxów {sum(allmx) / len(allmx):.3f} m, "
              f"krawędzi > 0,5 m: {sum(1 for m in allmx if m > 0.5)} / {len(allmx)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
