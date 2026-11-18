"""ADR 0288 (owner D82): the 15 tiles of the loop S8 <-> DW671 <-> Tykocin - registry, lattice, chain of control routes.

Reads the plan json in git (docs/reports/map/s8_loop_plan.json, written by tools/worldgen/qa/s8_loop_plan.py from the
pinned pbf) and tools/worldgen/regions.py; no network, no pbf."""

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
import regions  # noqa: E402
import s8_loop_plan as sp  # noqa: E402

PLAN = json.loads((REPO / "docs" / "reports" / "map" / "s8_loop_plan.json").read_text(encoding="utf-8"))
# docs/owner/MAP-DECISIONS-2026-11-16.md (b): (-5..-9, 0), (-9..-12, -1), (-12..-14, -2), (-13, -1..1)
CELLS = ({(i, 0) for i in range(-9, -4)} | {(i, -1) for i in range(-12, -8)} | {(i, -2) for i in range(-14, -11)}
         | {(-13, j) for j in range(-1, 2)})


def test_fifteen_unique_cells_of_the_owner_decision():
    cells = {(i, j) for _, i, j in sp.TILES}
    assert len(sp.TILES) == 15 and cells == CELLS


def test_registry_matches_lattice_and_plan():
    for t in PLAN["tiles"]:
        r = regions.REGIONS[t["id"]]
        i, j = t["ij"]
        assert r.bbox == sp.tile_bbox(i, j) == tuple(t["bbox"])
        assert r.origin == tuple(t["origin"]) == ((r.bbox[0] + r.bbox[2]) / 2, (r.bbox[1] + r.bbox[3]) / 2)
        assert r.width == r.height == regions.TILE_SIZE_M
        assert r.teryt_powiat == t["teryt_powiat"] and list(r.teryt_powiat_extra) == t["teryt_powiat_extra"]


def test_no_overlap_with_other_regions():
    own = {t[0] for t in sp.TILES}
    for tid in own:
        a = regions.REGIONS[tid].bbox
        for rid, r in regions.REGIONS.items():
            if rid == tid:
                continue
            b = r.bbox
            assert not (a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]), (tid, rid)


def test_driving_order_is_a_chain_of_lattice_neighbours():
    order = [(tid, i, j) for tid, i, j in sp.TILES]
    for (a, ai, aj), (b, bi, bj) in zip(order, order[1:]):
        if b == "dw671-jezewo-01":      # the DW671 leg restarts from s8-11 (the loop turns round in s8-12)
            ai, aj = next((i, j) for t, i, j in order if t == "s8-11")
        assert abs(ai - bi) + abs(aj - bj) == 1, (a, b)


def test_control_routes_are_continuous_across_the_seams():
    by = {t["id"]: t for t in PLAN["tiles"]}
    for tid, spec in sp.THROUGH.items():
        if not spec["chained"]:
            continue
        prev = by[spec["entry"][1]]["through"]["exit"]
        cur = by[tid]["through"]["entry"]
        assert (prev["osm_way"], prev["x"], prev["y"]) == (cur["osm_way"], cur["x"], cur["y"]), tid


def test_seam_with_built_dk65_01_has_no_offset():
    seam = PLAN["tiles"][0]["seams"]["E"]
    assert seam["neighbour"] == "dk65-01" and seam["max_offset_m"] == 0.0 and seam["ways_missing_in_built_graph"] == []
    assert {c["ref"] for c in seam["crossings"]} >= {"S8"}


def test_last_tile_ends_on_the_ring_tile_tykocin():
    last = PLAN["tiles"][-1]
    assert last["seams"]["N"]["neighbour"] == "tykocin" and last["through"]["exit"]["ref"] == "671"


def test_junctions_of_the_first_five_tiles():
    names = {t["id"]: sorted({q["name"] for q in t["motorway_junctions"] if q["name"]}) for t in PLAN["tiles"][:5]}
    assert "Choroszcz" in names["s8-01"] and names["s8-03"] == ["Tykocin"]
