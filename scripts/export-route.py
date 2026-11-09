"""Export the start route of a region (depot gate -> national road) as a lane polyline for Unity.

    uv run --project tools/worldgen python scripts/export-route.py --region bialystok-industrial-c

Reads (never writes) the worldgen inputs: Data/Regions/<id>/region.yaml, roads.graph.json and
docs/reports/map/candidates.json; the path is the same shortest drivable path as
tools/worldgen/roads/build_world.py::route_polyline (networkx over roadgraph.to_digraph).
Writes Data/Regions/<id>/route_start.json:
    points  [[e, n], ...]  region-local metres (E = x - origin.x, N = y - origin.y), resampled every 2 m,
            offset to the centre of the right-hand lane on two-way roads (lane width/2 from the centreline,
            lane width from `width`/`lanes` attrs or 3.0 m WORKING_VALUE); one-way carriageways keep the centreline.
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
    cand = json.loads((REPO / "docs/reports/map/candidates.json").read_text(encoding="utf-8"))
    route = next(c for c in cand["candidates"] if c["id"] == region["candidate"])["route"]
    ox, oy = region["origin"]["x"], region["origin"]["y"]

    def nearest(xy):
        return min(graph["nodes"], key=lambda n: math.hypot(n["x"] - xy[0], n["y"] - xy[1]))["id"]

    g = roadgraph.to_digraph(graph)
    path = nx.shortest_path(g, nearest(route["start_epsg2180"]), nearest(route["end_epsg2180"]), weight="length")
    edges = {e["id"]: e for e in graph["edges"]}

    segs = []  # (polyline local, offset m, maxspeed, edge id)
    for u, v in zip(path, path[1:]):
        e = edges[g[u][v]["id"]]
        geo = e["geometry"] if e["from"] == u else e["geometry"][::-1]
        P = np.array([(x - ox, y - oy) for x, y in geo], dtype=float)
        at = e["attrs"]
        oneway = at["oneway"]["v"] != "no"
        lanes = max(1, int(at.get("lanes", {}).get("v", 2) or 2))
        width = at.get("width", {}).get("v")
        lane_w = min(3.5, max(2.75, (float(width) / lanes) if width else 3.0))
        off = 0.0 if oneway else lane_w / 2.0
        ms = at.get("maxspeed", {}).get("v")
        try:
            ms = float(ms)
        except (TypeError, ValueError):
            ms = 0.0
        segs.append((P, off, ms, e["id"]))

    pts, spd, eid = [], [], []
    for P, off, ms, ei in segs:
        if off:
            T = np.gradient(P, axis=0)
            T /= np.maximum(np.linalg.norm(T, axis=1, keepdims=True), 1e-9)
            right = np.stack([T[:, 1], -T[:, 0]], axis=1)  # (E, N): right of travel
            P = P + right * off
        for i, p in enumerate(P):
            if pts and i == 0 and np.hypot(*(np.array(pts[-1]) - p)) < 0.5:
                continue
            pts.append(p.tolist()); spd.append(ms); eid.append(ei)
    P = np.array(pts)
    s = np.concatenate([[0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    n = int(s[-1] // a.step) + 1
    si = np.linspace(0, s[-1], n)
    R = np.stack([np.interp(si, s, P[:, 0]), np.interp(si, s, P[:, 1])], axis=1)
    idx = np.clip(np.searchsorted(s, si, side="right") - 1, 0, len(spd) - 1)
    out = {
        "schema": "truck-sim-pl/route/1",
        "region": a.region,
        "route": "start",
        "note": "Depot gate (Kwadrat Park) -> DK8/DK19; centreline of one-way carriageways, right-lane centre on two-way roads",
        "frame": "region-local metres, E = x - origin.x, N = y - origin.y (EPSG:2180)",
        "length_m": round(float(s[-1]), 2),
        "step_m": a.step,
        "points_en": [[round(float(x), 3), round(float(y), 3)] for x, y in R],
        "maxspeed_kmh": [spd[i] for i in idx],
        "edge": [eid[i] for i in idx],
        "graph_nodes": path,
    }
    dst = rdir / "route_start.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=None, sort_keys=True) + "\n", encoding="utf-8")
    print(f"route {a.region}: {len(R)} points, {s[-1]:.0f} m -> {dst.relative_to(REPO)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
