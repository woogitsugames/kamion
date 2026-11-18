"""Pre-import check of the world-edge closures of a region (ADR 0292, agent dk8-s8-s24).

    uv run --project tools/worldgen python tools/worldgen/qa/edge_closures_check.py <region> [--tol 0.5]   # exit 1 = suspects

The Unity importer (game/Assets/_Project/World/Import/WorldEdgeBuilder.cs) closes every road that leaves the tile with a
barrier row ClosureSetbackM = 60 m inside the edge (ReadExits -> PlanClosures -> ResolveClosures) and aborts the import
with "world edge: N closure rows overlap after ResolveClosures" when two rows still touch (FindClosureConflicts,
ClosureConflictM = 0.5 m). The import takes ~20 min; this script ports ReadExits / PlanClosures (setback walk through
degree-2 nodes, width = attr width or lanes x 3.5 m clamped 3..16 m, span = width + 5 m) and lists the pairs of rows that
touch BEFORE ResolveClosures. ResolveClosures resolves parallel carriageways / slip lanes (headings <= merge angle) and
crossing rows in front of each other's road - so a listed pair is a suspect, not a certain failure. The pair it cannot
resolve and that this script makes easy to see: one way leaving and re-entering across the same edge (two parallel rows of
opposite heading, e.g. bialystok-porosly service loop 248109972, r5).
Not ported: RoadY (exits without a road mesh under the closure are skipped by the importer).
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from shapely.geometry import LineString

REPO = Path(__file__).resolve().parents[3]
SETBACK_M = 60.0     # WorldEdgeBuilder.ClosureSetbackM


def closures(rid: str) -> list[dict]:
    g = json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))
    bnd = {n["id"] for n in g["nodes"] if n.get("boundary")}
    at: dict[str, list] = {}
    for e in g["edges"]:
        for k in (e["from"], e["to"]):
            at.setdefault(k, []).append(e)
    out = []
    for e in g["edges"]:
        fb, tb = e["from"] in bnd, e["to"] in bnd
        if not fb and not tb:
            continue
        pts = [tuple(p) for p in e["geometry"]]
        if fb:
            pts = pts[::-1]                      # last point on the edge
        have = sum(math.dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))
        cur, inner = e, (e["to"] if fb else e["from"])
        for _ in range(16):
            if have >= SETBACK_M / 0.8:
                break
            lst = at.get(inner, [])
            if inner in bnd or len(lst) != 2:
                break
            nxt = lst[1] if lst[0] is cur else lst[0]
            if nxt is cur:
                break
            np_ = [tuple(p) for p in nxt["geometry"]]
            ends = nxt["to"] == inner
            if not ends:
                np_ = np_[::-1]
            have += sum(math.dist(np_[i - 1], np_[i]) for i in range(1, len(np_)))
            pts = np_[:-1] + pts
            inner, cur = (nxt["from"] if ends else nxt["to"]), nxt
        a = e["attrs"]
        try:
            w = float((a.get("width") or {}).get("v") or 0)
        except (TypeError, ValueError):
            w = 0.0
        if w <= 0:
            w = max(1.0, float((a.get("lanes") or {}).get("v") or 1)) * 3.5
        w = min(max(w, 3.0), 16.0)
        total = sum(math.dist(pts[i - 1], pts[i]) for i in range(1, len(pts)))
        back, acc, cp, cd = min(SETBACK_M, total * 0.8), 0.0, pts[-1], None
        for i in range(len(pts) - 1, 0, -1):
            seg = math.dist(pts[i - 1], pts[i])
            if acc + seg >= back and seg > 1e-3:
                t = (back - acc) / seg
                cp = (pts[i][0] + (pts[i - 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i - 1][1] - pts[i][1]) * t)
                cd = ((pts[i][0] - pts[i - 1][0]) / seg, (pts[i][1] - pts[i - 1][1]) / seg)
                break
            acc += seg
        if cd is None:
            continue
        h, r = (w + 5.0) / 2.0, (cd[1], -cd[0])
        out.append({"way": e["osm_way"], "highway": a["highway"]["v"], "edge_xy": [round(v, 1) for v in pts[-1]],
                    "heading_deg": round(math.degrees(math.atan2(cd[0], cd[1])), 1),
                    "row": LineString([(cp[0] - r[0] * h, cp[1] - r[1] * h), (cp[0] + r[0] * h, cp[1] + r[1] * h)])})
    return out


def suspects(rid: str, tol: float = 0.5) -> list[tuple[dict, dict, float]]:
    cl = closures(rid)
    res = []
    for i, x in enumerate(cl):
        for y in cl[i + 1:]:
            d = x["row"].distance(y["row"])
            if d < tol:
                res.append((x, y, round(d, 2)))
    return res


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("region")
    ap.add_argument("--tol", type=float, default=0.5)
    a = ap.parse_args(argv)
    s = suspects(a.region, a.tol)
    for x, y, d in s:
        dh = abs((x["heading_deg"] - y["heading_deg"] + 180) % 360 - 180)
        same = " SAME WAY" if x["way"] == y["way"] else ""
        print(f"{x['way']} {x['highway']} {x['edge_xy']} | {y['way']} {y['highway']} {y['edge_xy']}  gap {d} m, "
              f"heading diff {dh:.0f} deg{same}")
    print(f"{a.region}: {len(s)} suspect pair(s) before ResolveClosures")
    return 1 if s else 0


if __name__ == "__main__":
    sys.exit(main())
