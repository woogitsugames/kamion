"""ADR 0262: the start of every region of the start-menu catalog is behind the region-edge closure and on an open road.

Owner report 2026-11-15 (A16, APK d67-full): every start stood OUTSIDE a barrier row ("road end behind, blocks ahead"),
dk65-05 inside the row. Cause: the start route of a corridor tile begins ON the tile edge (first graph node = boundary),
the importer closes the road up to 60 m inside the tile (WorldEdgeBuilder.ClosureSetbackM, ADR 0169) and the start was a
fixed 12 m (ADR 0229).

This file checks the committed data only (stdlib, no Data/raw):
  - the catalog is what scripts/export-region-catalog.py derives (not stale),
  - a route that starts on the region edge starts far enough inside for the whole combination to stand behind the
    closure with the required margin (the bound below is the worst case, closure at the full setback),
  - the first 300 m of the route after the start use no road that is closed or under construction (D65: the new DK65
    carriageway in dk65-05 / dk65-06 is a building site; the old road is the open one).
The exact closure geometry (resolved rows, short edges) and the scene colliders are checked in Unity:
game/Assets/_Project/Tests/EditMode/StartClearanceTests.cs (ADR 0169 p.2: no Python copy of ReadExits).
"""
import importlib.util
import json
import math
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CATALOG = REPO / "game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json"
REGIONS = REPO / "Data/Regions"

CLOSURE_SETBACK_M = 60.0     # WorldEdgeBuilder.ClosureSetbackM
REAR_M = 11.30               # StartClearance.RearM: tractor origin -> rear end of the 13.6 m trailer
BOARDS_M = 0.75              # U-20 boards in front of the barrier row (inner side)
MARGIN_M = 0.5               # task: free space around the combination
AHEAD_FREE_M = 300.0         # task: open route ahead of the start
MIN_AHEAD_M = 100.0          # RegionStart.MinAheadM


def _catalog():
    return json.loads(CATALOG.read_text(encoding="utf-8"))["regions"]


REGION_IDS = [r["id"] for r in _catalog()]


def _exporter():
    spec = importlib.util.spec_from_file_location("export_region_catalog", REPO / "scripts/export-region-catalog.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _load(region):
    rdir = REGIONS / region
    route = json.loads((rdir / "route_start.json").read_text(encoding="utf-8"))
    graph = json.loads((rdir / "roads.graph.json").read_text(encoding="utf-8"))
    return rdir, route, graph


def _stations(points):
    s = [0.0]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        s.append(s[-1] + math.hypot(x1 - x0, y1 - y0))
    return s


def test_catalog_has_all_regions():
    # 21 regions before the ring of ADR 0231; the ring tiles join the catalog one by one as they are built (up to 39);
    # ADR 0288: + the 15 tiles of the loop S8 <-> DW671 <-> Tykocin (5 built on 2026-11-17) = up to 54;
    # + 3 tiles of ADR 0278 / D81 (wygoda, bojary, mickiewicza) = up to 57
    assert 21 <= len(REGION_IDS) <= 57 and len(set(REGION_IDS)) == len(REGION_IDS)


def test_catalog_is_what_the_exporter_derives():
    exp = _exporter()
    stale = []
    for r in _catalog():
        d = exp.derived(r["id"])
        stale += [f"{r['id']}.{k}: {r.get(k)} -> {v}" for k, v in d.items() if r.get(k) != v]
    assert not stale, "python scripts/export-region-catalog.py:\n" + "\n".join(stale)


@pytest.mark.parametrize("region", REGION_IDS)
def test_start_is_inside_the_edge_closure(region):
    entry = next(r for r in _catalog() if r["id"] == region)
    _, route, graph = _load(region)
    boundary = {n["id"] for n in graph["nodes"] if n.get("boundary")}
    start, length = float(entry["startS"]), float(route["length_m"])
    if entry.get("noStart"):
        # ADR 0231 §5a: corner tile without any standalone start; allowed only when no start can exist on the route: behind
        # the entry closure there is no AHEAD_FREE_M of open route before the exit closure (60 m before the far edge)
        need = CLOSURE_SETBACK_M + BOARDS_M + REAR_M + MARGIN_M
        assert route["graph_nodes"][0] in boundary and length < need + AHEAD_FREE_M + CLOSURE_SETBACK_M, (
            f"{region}: noStart on a route of {length} m - a start behind the closure exists, remove the marker")
        return
    assert 0.0 <= start <= length - MIN_AHEAD_M, f"{region}: startS {start} on a route of {length} m"
    if route["graph_nodes"][0] in boundary:
        need = CLOSURE_SETBACK_M + BOARDS_M + REAR_M + MARGIN_M
        assert start >= need, (
            f"{region}: the start route begins on the region edge; the closure stands up to {CLOSURE_SETBACK_M:.0f} m inside, "
            f"startS {start} m leaves the combination outside / in the barrier row (need >= {need:.2f} m)")


@pytest.mark.parametrize("region", REGION_IDS)
def test_route_after_the_start_uses_open_roads_only(region):
    entry = next(r for r in _catalog() if r["id"] == region)
    rdir, route, graph = _load(region)
    edges = {e["id"]: e for e in graph["edges"]}
    dropped = set()
    filt = rdir / "graph_filter.authored.json"
    if filt.exists():
        dropped = set(json.loads(filt.read_text(encoding="utf-8")).get("drop_osm_ways", []))
    s = _stations(route["points_en"])
    start = float(entry["startS"])
    bad = []
    for station, eid in zip(s, route["edge"]):
        if station < start - REAR_M or station > start + AHEAD_FREE_M:
            continue
        e = edges.get(eid)
        assert e is not None, f"{region}: route edge {eid} is not in roads.graph.json (route_start.json stale)"
        attrs = e.get("attrs", {})
        hw = (attrs.get("highway") or {}).get("v")
        closed = hw in ("construction", "proposed") or bool((attrs.get("construction") or {}).get("v")) or e.get("osm_way") in dropped
        if closed:
            bad.append((round(station, 1), eid, hw))
    assert not bad, f"{region}: closed / building-site road within {AHEAD_FREE_M:.0f} m of the start: {bad[:5]}"


# ADR 0231 §5a: only the corner tiles of the ring (< 0.5 km of corridor) may carry noStart; any other tile that cannot
# host a start is a data error to fix, not to mark
CORNER_TILES_0231 = {"dk65-monki-03", "dk65-monki-05", "monki-e", "dw671-tykocin-02",
                     "bialystok-wygoda"}   # D81: 91 m of Andersa across the SW corner of the tile (ADR 0278 tile 5)


def test_no_start_marker_only_on_corner_tiles_and_matches_route_endpoints():
    marked = {r["id"] for r in _catalog() if r.get("noStart")}
    assert marked <= CORNER_TILES_0231, f"noStart outside the ADR 0231 corner tiles: {sorted(marked - CORNER_TILES_0231)}"
    for rid in REGION_IDS:
        ep = REGIONS / rid / "route_endpoints.json"
        authored = ep.exists() and bool(json.loads(ep.read_text(encoding="utf-8")).get("no_standalone_start"))
        assert authored == (rid in marked), f"{rid}: route_endpoints.json no_standalone_start {authored} vs catalog noStart"
