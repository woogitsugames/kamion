"""Road surface consistency (ADR 0074, owner bug 2026-11-10 "lane into island"): markings only on carriageway,
nothing in a lane, no lane ending blind in a kerb / island, arrows only where an arm exists, no pole on the road.
Written by build_world.py (roads.consistency.check) to generated/road_consistency_qa.json."""

from __future__ import annotations

import json

import pytest

from conftest import REGION_DIR

QA = REGION_DIR / "generated" / "road_consistency_qa.json"

# Ratchet (ADR 0033 / 0074): rest of the tile. Lower whenever a fix lands, never raise. Target 0.
# Build 2026-11-10 r9: 222 -> 145 (arrow 13->8, furniture 7->5, blind end 90->56, marking 58->17, obstacle 53->58
# (tapers now excluded, new fork geometry exposed 5), prop 1->1).
RATCHET = {"arrow_no_exit": 8, "furniture_in_lane": 1, "lane_blind_end": 55, "marking_off_carriageway": 3,
           "obstacle_in_lane": 2, "prop_on_carriageway": 0,
           # ADR 0076: poles piercing a deck above them, kerbs lying on a carriageway (across / along a lane)
           "prop_through_deck": 0, "kerb_on_carriageway": 0}
# roads-p0-r10 (ADR 0076), build of 2026-11-11: 145 -> 69 on the tile (furniture 5 -> 1, markings 17 -> 3, obstacles
# 58 -> 2, poles on a carriageway 1 -> 0).
# start route G3-A / G3-B, both carriageways within route_band_m: 26 -> 2 -> 1 (open: lane_blind_end at the depot gate
# split j:n1882954015, E 602 N -645). Target 0.
ROUTE_MAX = 1


def _qa():
    if not QA.exists():
        pytest.skip("road_consistency_qa.json missing: run roads/build_world.py")
    return json.loads(QA.read_text(encoding="utf-8"))


def test_start_route_is_consistent():
    q = _qa()
    route = [c for c in q["cases"] if c["on_route"]]
    assert len(route) <= ROUTE_MAX, "\n".join(
        f"{c['kind']} {c.get('what')} at E {c['e']} N {c['n']} ({c['lat']}, {c['lon']}) {c.get('chain') or c.get('junction')}"
        for c in route[:20])


def test_tile_ratchet():
    q = _qa()
    for kind, n in q["by_kind"].items():
        assert kind in RATCHET, f"new consistency category {kind} ({n})"
        assert n <= RATCHET[kind], f"{kind}: {n} > ratchet {RATCHET[kind]}"


def test_cases_are_located():
    q = _qa()
    assert q["stats"]["marking_tris"] > 10000 and q["stats"]["lane_samples"] > 50000
    for c in q["cases"]:
        assert {"e", "n", "lat", "lon", "kind"} <= set(c)
        assert 52.9 < c["lat"] < 53.4 and 22.9 < c["lon"] < 23.4


def test_emergency_signals_are_not_junction_signals():
    rq = json.loads((REGION_DIR / "generated" / "roads_qa.json").read_text(encoding="utf-8"))
    # fire-station exit on Andersa (OSM traffic_signals=emergency 3136871040): no P-14 / arrows / S-1 of a junction
    assert "j:n12620261934" in rq["summary"]["emergency_signal_junctions"]


def test_andersa_fork_lanes_aligned():
    rq = json.loads((REGION_DIR / "generated" / "roads_qa.json").read_text(encoding="utf-8"))
    shifts = rq["summary"].get("fork_shifts", [])
    # Andersa 3 lanes -> viaduct (2) + link (1): the viaduct is moved left under the two left lanes
    assert any(s["node"] == "n2840742308" and s["shift_m"] > 1.0 for s in shifts), shifts
