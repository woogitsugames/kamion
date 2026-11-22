"""ADR 0326: an OSM gate beside a road must not be turned across that road (build #4 P1, gen. Maczka)."""
import math
from types import SimpleNamespace

import numpy as np
import pytest

from roads.geom import Polyline
from streetscape import furniture as FU

pytestmark = pytest.mark.unit


def _chain(p0, p1, hw):
    pts = np.linspace(p0, p1, 101)
    line = Polyline(pts)
    return SimpleNamespace(line=line, length=line.length, hw_at=lambda s, hw=hw: np.full(np.shape(s), hw, float))


def _clear_of(chain, proto, p, yaw):
    for P in FU._gate_span_points(proto, p, yaw, step=0.1):
        s, lat = chain.line.project(P)
        if 0.0 < s < chain.length and abs(lat) < float(chain.hw_at(s)):
            return False
    return True


@pytest.mark.parametrize("proto", ["sliding_gate", "lift_gate"])
def test_gate_beside_road_stays_on_its_side_way(proto):
    # Maczka: northern carriageway hw 3.5 m along x; track gate 5 m outside the north edge (old code: snapped across)
    road = _chain((-200.0, 0.0), (200.0, 0.0), 3.5)
    net = SimpleNamespace(chains=[road])
    q = (10.0, 3.5 + 5.0)
    p, yaw = FU.gate_pose(net, proto, q)
    assert _clear_of(road, proto, p, yaw)
    assert abs(math.sin(yaw)) < 1e-6                       # spans the side way = parallel to the road
    assert np.hypot(*(np.asarray(p) - q)) < 3.0


def test_gate_on_carriageway_spans_it():
    lane = _chain((0.0, -100.0), (0.0, 100.0), 2.5)        # private service road, gate node on its centreline
    net = SimpleNamespace(chains=[lane])
    p, yaw = FU.gate_pose(net, "sliding_gate", (0.2, 10.0))
    assert abs(math.sin(yaw)) < 1e-6 and abs(p[0]) < 1e-6   # span along x = across the lane, on its centreline


def test_gate_that_would_close_another_road_is_dropped():
    lane = _chain((0.0, 4.0), (0.0, 100.0), 2.5)           # side road ending at the main road edge
    main = _chain((-200.0, 0.0), (200.0, 0.0), 3.0)
    net = SimpleNamespace(chains=[main, lane])
    # node on the side road but 4.5 m from the main centreline: an 8.4 m gate across the side road is fine,
    # a gate whose span enters the main carriageway is not
    assert FU.gate_pose(net, "sliding_gate", (0.0, 9.0)) is not None
    assert FU.gate_on_foreign_carriageway(net, "sliding_gate", (0.0, 1.0), 0.0, host=lane)


# ------------------------------------------------------------------------------- data: built corridor tiles
def _corridor_tiles():
    import json
    from qa import route_obstacles as RO
    if not RO.LINKS.exists():
        return [], []
    L = json.loads(RO.LINKS.read_text(encoding="utf-8"))
    tiles = sorted({t for c in L["corridors"] for t in c["tiles"]})
    return tiles, L["links"]


@pytest.mark.parametrize("tile", _corridor_tiles()[0] or ["bialystok-maczka"])
def test_no_gate_across_a_route_lane(tile):
    """No OSM gate instance (sliding / lift gate) spans the truck envelope of a route lying in the tile (start
    route + corridor links). Build #4 P1: osm:node/13072640312 across gen. Maczka at (377, 2)."""
    from qa import route_obstacles as RO
    gates = RO.gate_instances(tile)
    if not gates and not (RO.REPO / "Data/raw/derived" / tile / "world").exists():
        pytest.skip(f"{tile} not built")
    _, links = _corridor_tiles()
    bad = [(name, h) for name, pts in RO.tile_routes(tile, links) for h in RO.gate_hits(pts, gates)]
    assert not bad, bad
