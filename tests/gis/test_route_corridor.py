"""route_start drives clear: swept corridor and wheel-track profile against the collision Unity builds (r4 blocker).

Corridor: vehicle 2.55 m + 0.5 m margin each side, 0.30-4.0 m above the driven surface, the whole route; no
collision triangle of road_collision / terrain_lod2 (`chunk_*.low.glb`) or prop collider box (street_props.glb)
inside it. Profile: on the wheel tracks (+-1.0 m) and the centre no height jump > 3 cm per 0.5 m beyond the local
grade. Checks the regenerated world in Data/raw/derived/<id>/world (build_world.py CLI output); details and the
collider model in tests/gis/route_corridor.py. Before the fix (v3.1): 85 obstructed stations (Andersa walled ramp
cap, wall and guard rail at s = 567-609 m) and 18 steps (kerb ridges of 13-20 cm at s = 602-634 m).
"""

from __future__ import annotations

import pytest

import route_corridor as RC
from conftest import REGION_DIR, REGION_ID, REPO, require_lfs

WORLD = REPO / "Data" / "raw" / "derived" / REGION_ID / "world"
PROPS = REPO / "art-source" / "world" / "props" / "street_props.glb"
ROUTE = REGION_DIR / "route_start.json"


@pytest.fixture(scope="module")
def corridor():
    if not (WORLD / "chunk_0_0.low.glb").exists():
        pytest.skip("world not built (run tools/worldgen/roads/build_world.py)")
    require_lfs(PROPS)
    return RC.check(WORLD, PROPS, ROUTE)


def test_route_has_surface_everywhere(corridor):
    assert corridor["length_m"] > 2300
    assert not corridor["no_surface"], corridor["no_surface"][:20]


def test_route_corridor_is_clear(corridor):
    hits = corridor["hits"]
    first = {}
    for h in hits:
        first.setdefault(h["obj"], h)
    assert not hits, f"{len({h['s'] for h in hits})} obstructed stations; first per object: {list(first.values())}"


def test_route_profile_has_no_steps(corridor):
    st = corridor["steps"]
    assert not st, f"{len(st)} steps > {RC.STEP_MAX} m per {RC.STEP} m (s, lat, jump): {st[:20]}"
