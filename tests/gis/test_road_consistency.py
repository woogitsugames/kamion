"""Road surface consistency (ADR 0074, owner bug 2026-11-10 "lane into island"): markings only on carriageway,
nothing in a lane, no lane ending blind in a kerb / island, arrows only where an arm exists, no pole on the road.
Written by build_world.py (roads.consistency.check) to generated/road_consistency_qa.json."""

from __future__ import annotations

import json

import numpy as np
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
    # ADR 0095: the 3-lane edge now has its measured placement (centre 0.8 m right of the OSM way), so the part of the
    # shift that only compensated the mis-centred carriageway is gone; the viaduct still moves left under its lanes
    assert any(s["node"] == "n2840742308" and s["shift_m"] > 0.3 for s in shifts), shifts


def _surface_index(surfaces):
    from roads.consistency import SurfaceIndex
    from roads.meshing import MeshBuf
    buf = MeshBuf()
    for material, xyz in surfaces:
        v = np.asarray(xyz, float)
        buf.add("road", material, v, v[:, :2].copy(), np.array([[0, 1, 2]]), src="test")
    return SurfaceIndex(buf.parts)


@pytest.mark.unit
@pytest.mark.parametrize("offset,expected", [(-0.24, "carriageway"), (0.15, "kerb"), (0.0, "kerb")])
def test_surface_classification_compares_heights_on_sloped_triangles(offset, expected):
    road = np.array([[0, 0, 0], [10, 0, 1], [0, 10, 0]], float)
    obstacle = road.copy()
    obstacle[:, 2] += offset
    idx = _surface_index([("road_asphalt", road), ("curb_concrete", obstacle)])
    assert idx.classify([[0.5, 0.5, 0.05]]).tolist() == [expected]


@pytest.mark.unit
def test_surface_classification_interpolates_height_instead_of_triangle_mean():
    road = [[0, 0, 0], [10, 0, 1], [0, 10, 0]]
    # At x=.5 the grass is -.09 m; its triangle mean is +.76 m.
    grass = [[0, 0, -0.24], [10, 0, 2.76], [0, 10, -0.24]]
    idx = _surface_index([("road_asphalt", road), ("verge_grass", grass)])
    assert idx.classify([[0.5, 0.5, 0.05]]).tolist() == ["carriageway"]


@pytest.mark.unit
def test_surface_classification_keeps_bridge_levels_separate():
    road = np.array([[0, 0, 0], [10, 0, 1], [0, 10, 0]], float)
    bridge, kerb = road.copy(), road.copy()
    bridge[:, 2] += 6.0
    kerb[:, 2] += 6.15
    idx = _surface_index([("road_asphalt", road), ("road_asphalt", bridge), ("curb_concrete", kerb)])
    assert idx.classify([[0.5, 0.5, 0.05], [0.5, 0.5, 6.05]]).tolist() == ["carriageway", "kerb"]


@pytest.mark.unit
def test_c_edge_paint_is_above_the_neighbouring_grass_skirt():
    # C regression, E983.06 N-934.05: interpolated road/grass heights from the generated triangles.
    xy = np.array([[982.0, -935.0], [985.0, -935.0], [982.0, -932.0]])
    road = np.column_stack([xy, np.full(3, 138.77898773515255)])
    grass = np.column_stack([xy, np.full(3, 138.53445351432129)])
    idx = _surface_index([("road_asphalt", road), ("verge_grass", grass)])
    assert idx.classify([[983.06, -934.05, 138.77898773515255]]).tolist() == ["carriageway"]
