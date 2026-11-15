"""Opt-in park paving must meet terrain without changing ordinary surfaces."""
from types import SimpleNamespace

import numpy as np
from shapely.geometry import Polygon

from streetscape import paved as PV


class Accumulator:
    def __init__(self):
        self.parts = []

    def add(self, *args, **kwargs):
        self.parts.append((args, kwargs))


def test_park_flush_raises_terrain_without_touching_hard_surfaces():
    ground = np.full((11, 11), 9.65)
    paving = np.full((11, 11), np.nan)
    park = np.zeros((11, 11), dtype=bool)
    park[4:7, 4:7] = True
    paving[park] = 10.0
    hard = np.zeros_like(park)
    hard[5, 6] = True
    out = PV.conform_park_flush(ground, paving, park, hard)
    assert out[5, 5] == 9.97
    assert out[5, 6] == ground[5, 6]
    assert ground[5, 7] < out[5, 7] < 9.97
    assert out[0, 0] == ground[0, 0]
    assert np.isfinite(out).all()
    assert np.array_equal(PV.conform_park_flush(ground, paving, np.zeros_like(park), hard), ground)


def test_flush_paving_omits_skirt_ordinary_paving_keeps_it():
    item = {"poly": Polygon([(1, 1), (5, 1), (5, 5), (1, 5)]), "mat": "yard_paving", "id": "x"}
    hf = SimpleNamespace(x0=0., y1=10.)
    z = np.ones((11, 11))
    ordinary, flush = Accumulator(), Accumulator()
    PV._edges(ordinary, item, z, hf)
    PV._edges(flush, {**item, "park_flush": True}, z, hf)
    assert len(ordinary.parts) == 1
    assert ordinary.parts[0][0][1] == "curb_concrete"
    assert flush.parts == []


def test_collect_propagates_only_explicit_authored_opt_in():
    src = {"osm": {"areas": []}, "bdot10k": {"OT_PTPL_A": [], "OT_KUKO_A": [], "OT_SKRP_L": []}}
    overrides = [
        {"id": "park", "kind": "paved_area", "material": "yard_paving", "park_flush": True,
         "polygon_epsg2180": [[0, 0], [5, 0], [5, 5], [0, 5]]},
        {"id": "yard", "kind": "paved_area", "material": "yard_paving",
         "polygon_epsg2180": [[10, 0], [15, 0], [15, 5], [10, 5]]},
    ]
    result = PV.collect(src, np.array([0., 0.]), overrides, [], Polygon(), None, {})
    assert len(result) == 2
    assert result[0]["park_flush"] is True
    assert "park_flush" not in result[1]
