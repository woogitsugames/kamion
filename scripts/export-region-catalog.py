"""Refresh the start-menu region catalog (ADR 0229) from the region data in git.

    python scripts/export-region-catalog.py            # rewrite routeLengthM / startS from Data/Regions/*/route_start.json
    python scripts/export-region-catalog.py --check    # exit 1 when the catalog is stale or misses a region (CI / review)

Catalog: game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json (Resources, loaded by
Game.Gameplay.RegionCatalog in the Boot menu and read by Game.Editor.Build.RegionBuildList for `-Regions`).
Authored fields (kept as they are): id, label, group, order of the list, aliases, sets (except the derived ones below).
Derived fields (rewritten here): routeLengthM (route_start.json length_m), startS (ADR 0262: 12 m from the route start
when the route starts inside the region - the depot gate of region C; EDGE_START_S_M when the route starts ON the
region edge, i.e. its first graph node is a `boundary` node of roads.graph.json - the importer closes such a road with a
barrier row up to 60 m inside the tile (WorldEdgeBuilder.ClosureSetbackM, ADR 0169) and the start has to stand behind
it; clamped so that at least MIN_AHEAD_M of route remains). The importer bakes the same startS as the scene spawn
(WorldSceneBuilder). The exact closure geometry is NOT copied here (ADR 0169 p.2): the EditMode test
StartClearanceTests checks every startS of this catalog against the real closures. Also derived: the DERIVED_SETS
(ADR 0267: d67-full = d67 + the D71 extras; the C# resolver does not nest sets, so the list is expanded here).
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
SKEW_ALLOWANCE_M = 5.0     # the lane centre meets a skewed row later than the road axis (measured: up to 1.2 m, bialystok-maczka) - WORKING_VALUE
EDGE_START_S_M = CLOSURE_SETBACK_M + BEHIND_CLOSURE_M + SKEW_ALLOWANCE_M
AHEAD_FREE_M = 300.0   # StartClearance.AheadFreeM: open route ahead of the start (ADR 0262 task) - WORKING_VALUE
MIN_AHEAD_M = 100.0    # keep >= 100 m before the tile-end closure (closure 60 m before the edge, ADR 0169) - WORKING_VALUE

# Ring tiles of ADR 0231 in driving order (owner decision 2026-11-16: the ring is part of d67-full).
RING_0231 = [
    "dk65-monki-02", "dk65-monki-03", "dk65-monki-04", "dk65-monki-05", "dk65-monki-06", "dk65-monki-07", "monki-e", "monki",
    "dw671-tykocin-02", "dw671-tykocin-03", "dw671-tykocin-04", "dw671-tykocin-05", "dw671-tykocin-06",
    "dw671-tykocin-07", "dw671-tykocin-08", "dw671-tykocin-09", "tykocin",
    "dw671-jasionowka-01",
]

# Derived sets (ADR 0267, owner decision D71): name -> (base set, extra region ids, note). Written after the base set.
DERIVED_SETS: dict[str, tuple[str, list[str], str]] = {
    "d67-full": (
        "d67",
        ["bialystok-dojlidy", "knyszyn-w", "dk65-monki-01", "dw671-tykocin-01", *RING_0231],
        "D71: d67 + Dojlidy, Knyszyn-W, Monki, Tykocin; owner decision 2026-11-16: + the 18 ring tiles of ADR 0231 "
        "(DK65 to Monki, DW671 to Tykocin, DW671 towards Jasionowka). Build size not measured with the ring (ADR 0267).",
    ),
}


def apply_derived_sets(cat: dict, problems: list[str]) -> None:
    """Expand DERIVED_SETS into cat["sets"] (in place); a missing / differing entry is reported in problems."""
    sets = cat.setdefault("sets", [])
    for name, (base_name, extra, note) in DERIVED_SETS.items():
        base = next((s for s in sets if s.get("name") == base_name), None)
        if base is None:
            problems.append(f"set {name}: base set {base_name} missing")
            continue
        regions: list[str] = []
        for r in list(base["regions"]) + extra:
            if r not in regions:
                regions.append(r)
        want = {"name": name, "note": note, "regions": regions}
        cur = next((i for i, s in enumerate(sets) if s.get("name") == name), None)
        if cur is None:
            problems.append(f"set {name}: missing (derived from {base_name})")
            sets.insert(sets.index(base) + 1, want)
        elif sets[cur] != want:
            problems.append(f"set {name}: stale (derived from {base_name} + {', '.join(extra)})")
            sets[cur] = want


NO_START_BELOW_M = EDGE_START_S_M + AHEAD_FREE_M + CLOSURE_SETBACK_M   # ADR 0231 §5a: 450 m


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
    on_edge = starts_on_region_edge(region_id, data)
    wanted = EDGE_START_S_M if on_edge else SPAWN_S_M
    # ADR 0231 §5a: a corner tile whose corridor stretch is too short for any start behind the entry closure carries the
    # authored marker no_standalone_start (route_endpoints.json); the catalog gets noStart = true and the start menu does
    # not offer the tile. The marker is accepted only when it is true: an edge route shorter than the rule start + the open
    # route the start needs ahead (AHEAD_FREE_M, StartClearance.AheadFreeM) + the exit closure (CLOSURE_SETBACK_M).
    endpoints_f = REGIONS / region_id / "route_endpoints.json"
    if endpoints_f.exists() and json.loads(endpoints_f.read_text(encoding="utf-8")).get("no_standalone_start"):
        if not on_edge or length >= NO_START_BELOW_M:
            raise SystemExit(f"{region_id}: no_standalone_start on a route of {length} m that has a valid start "
                             f"(edge route: {on_edge}, needs < {NO_START_BELOW_M} m) - remove the marker")
        return {"routeLengthM": round(length, 2), "startS": round(max(0.0, min(wanted, length - MIN_AHEAD_M)), 2),
                "noStart": True}
    # authored start (owner decision, survives regeneration): Data/Regions/<id>/route_endpoints.json "start_s_m" moves
    # the start further along the route (e.g. dk65-06: past the roundabout the rule start fell on); never closer to
    # the route start than the rule, so the start stays behind the region-edge closure
    endpoints = REGIONS / region_id / "route_endpoints.json"
    if endpoints.exists():
        authored = json.loads(endpoints.read_text(encoding="utf-8")).get("start_s_m")
        if authored is not None:
            if float(authored) < wanted:
                raise SystemExit(f"{region_id}: route_endpoints.json start_s_m {authored} < rule start {wanted} m")
            wanted = float(authored)
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
        if "noStart" in r and "noStart" not in d:          # marker removed from route_endpoints.json
            problems.append(f"{r['id']}.noStart: {r['noStart']} -> (none)")
            del r["noStart"]
    apply_derived_sets(cat, problems)
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
