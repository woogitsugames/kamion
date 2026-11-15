"""Refresh the start-menu region catalog (ADR 0229) from the region data in git.

    python scripts/export-region-catalog.py            # rewrite routeLengthM / startS from Data/Regions/*/route_start.json
    python scripts/export-region-catalog.py --check    # exit 1 when the catalog is stale or misses a region (CI / review)

Catalog: game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json (Resources, loaded by
Game.Gameplay.RegionCatalog in the Boot menu and read by Game.Editor.Build.RegionBuildList for `-Regions`).
Authored fields (kept as they are): id, label, group, order of the list, aliases, sets.
Derived fields (rewritten here): routeLengthM (route_start.json length_m), startS (ADR 0262: 12 m from the route start
when the route starts inside the region - the depot gate of region C; EDGE_START_S_M when the route starts ON the
region edge, i.e. its first graph node is a `boundary` node of roads.graph.json - the importer closes such a road with a
barrier row up to 60 m inside the tile (WorldEdgeBuilder.ClosureSetbackM, ADR 0169) and the start has to stand behind
it; clamped so that at least MIN_AHEAD_M of route remains). The importer bakes the same startS as the scene spawn
(WorldSceneBuilder). The exact closure geometry is NOT copied here (ADR 0169 p.2): the EditMode test
StartClearanceTests checks every startS of this catalog against the real closures.
Standard library only (no uv needed).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
CATALOG = REPO / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json"
REGIONS = REPO / "Data/Regions"
SPAWN_S_M = 12.0       # StartClearance.DefaultStartS: route that starts inside the region
CLOSURE_SETBACK_M = 60.0   # WorldEdgeBuilder.ClosureSetbackM (ADR 0169): the closure stands at most this far from the edge
BEHIND_CLOSURE_M = 25.0    # StartClearance.BehindClosureM: tractor origin behind the row (trailer rear end 13.7 m clear) - WORKING_VALUE
EDGE_START_S_M = CLOSURE_SETBACK_M + BEHIND_CLOSURE_M
MIN_AHEAD_M = 100.0    # keep >= 100 m before the tile-end closure (closure 60 m before the edge, ADR 0169) - WORKING_VALUE


def starts_on_region_edge(region_id: str, route: dict) -> bool:
    """True when the first graph node of the start route is a boundary node (the road is cut by the region edge)."""
    nodes = route.get("graph_nodes") or []
    graph = REGIONS / region_id / "roads.graph.json"
    if not nodes or not graph.exists():
        raise SystemExit(f"{region_id}: route_start.json graph_nodes or roads.graph.json missing")
    first = nodes[0]
    for n in json.loads(graph.read_text(encoding="utf-8"))["nodes"]:
        if n["id"] == first:
            return bool(n.get("boundary"))
    raise SystemExit(f"{region_id}: route node {first} is not in roads.graph.json (route_start.json stale: scripts/export-route.py)")


def derived(region_id: str) -> dict:
    route = REGIONS / region_id / "route_start.json"
    if not route.exists():
        raise SystemExit(f"{region_id}: {route.relative_to(REPO)} missing (scripts/export-route.py)")
    data = json.loads(route.read_text(encoding="utf-8"))
    length = float(data["length_m"])
    wanted = EDGE_START_S_M if starts_on_region_edge(region_id, data) else SPAWN_S_M
    start = max(0.0, min(wanted, length - MIN_AHEAD_M))
    return {"routeLengthM": round(length, 2), "startS": round(start, 2)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    a = ap.parse_args()
    cat = json.loads(CATALOG.read_text(encoding="utf-8"))
    problems: list[str] = []
    ids = [r["id"] for r in cat["regions"]]
    on_disk = sorted(p.name for p in REGIONS.iterdir() if (p / "route_start.json").exists())
    for rid in on_disk:
        if rid not in ids:
            problems.append(f"region {rid} has route_start.json but no catalog entry (add id + label by hand)")
    if len(set(ids)) != len(ids):
        problems.append("duplicate region ids in the catalog")
    for r in cat["regions"]:
        d = derived(r["id"])
        for k, v in d.items():
            if r.get(k) != v:
                problems.append(f"{r['id']}.{k}: {r.get(k)} -> {v}")
                r[k] = v
    for s in cat.get("sets", []):
        for t in s["regions"]:
            if t not in ids:
                problems.append(f"set {s['name']}: unknown region {t}")
    for al in cat.get("aliases", []):
        if al["region"] not in ids:
            problems.append(f"alias {al['alias']}: unknown region {al['region']}")
    for p in problems:
        print(p)
    if a.check:
        return 1 if problems else 0
    CATALOG.write_text(json.dumps(cat, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {CATALOG.relative_to(REPO)} ({len(ids)} regions)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
