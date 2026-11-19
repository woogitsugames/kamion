"""ADR 0300 on synthetic data, no Data/raw: a noise barrier mapped on the ground beside a viaduct ramp must not come
up through the low end of the deck into its lane (bialystok-kleeberga, Kleeberga westbound w301702368: the autopilot
truck drove into the screen). A barrier under a deck high enough to clear it stays, as does one off the deck."""
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
from shapely.geometry import LineString, Polygon

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

from roads import meshing as M  # noqa: E402
from roads import standards as S  # noqa: E402
from streetscape import furniture as FU  # noqa: E402

GROUND = 126.0


def _deck(z):
    """One 40 x 8 m deck carriageway slab at height z, as a bridge-layer road part (x 0..40, y 0..8)."""
    V = np.array([[0, 0, z], [40, 0, z], [40, 8, z], [0, 8, z]], float)
    return SimpleNamespace(V=V, T=np.array([[0, 1, 2], [0, 2, 3]]), layer="bridge", mat="road_asphalt")


def _src(*lines):
    ways = [{"tags": {"barrier": "wall", "wall": "noise_barrier"}, "osm_way": 1000 + i, "part": 0,
             "geometry": {"coordinates": [list(c) for c in ln]}} for i, ln in enumerate(lines)]
    return {"bdot10k": {"OT_OIKM_L": []}, "osm": {"ways": ways}}


def _run(deck_z, lines):
    lin = FU.Lin(M.MeshBuf(), lambda e, n: np.full(np.shape(e), GROUND))
    rep = {}
    decks = [_deck(deck_z)] if deck_z is not None else None
    FU.noise_barriers(lin, _src(*lines), np.zeros(2), Polygon(), rep, overrides=None, net=None, decks=decks)
    walls = [p for p in lin.buf.parts if p.layer == "furniture" and len(p.V)]
    return walls, dict(rep["noise_barriers"], noise_barriers_m=rep["noise_barriers_m"])


def _in_deck_lane(walls, deck_z):
    """Furniture vertices over the slab that rise into its lane window (deck - LANE_FLOOR_M upwards)."""
    n = 0
    for p in walls:
        V = p.V
        over = (V[:, 0] > 0.5) & (V[:, 0] < 39.5) & (V[:, 1] > 0.5) & (V[:, 1] < 7.5)
        n += int((over & (V[:, 2] > deck_z - FU.LANE_FLOOR_M)).sum())
    return n


ALONG = [(-20.0, 5.0), (60.0, 5.0)]        # runs along the deck lane, 5 m off its left edge, past both ends


def test_ground_barrier_under_a_low_ramp_deck_is_cut_out_of_the_lane():
    deck = GROUND + 1.0                     # the low end of a ramp: 1 m over the ground the barrier stands on
    assert GROUND + S.NOISE_BARRIER_H > deck
    walls, rep = _run(deck, [ALONG])
    assert _in_deck_lane(walls, deck) == 0
    assert abs(rep["cut_on_deck_carriageway_m"] - 40.6) < 0.3          # the slab + 0.3 m at both ends
    assert abs(rep["noise_barriers_m"] - (80.0 - 40.6)) < 0.5            # both ends off the deck are still built


def test_before_the_fix_the_same_barrier_stood_in_the_lane():
    walls, rep = _run(None, [ALONG])                                     # no deck parts = the pre-ADR 0300 call
    assert _in_deck_lane(walls, GROUND + 1.0) > 0
    assert rep["cut_on_deck_carriageway_m"] == 0.0


def test_barrier_under_a_deck_that_clears_it_stays():
    deck = GROUND + S.NOISE_BARRIER_H + 2.0
    walls, rep = _run(deck, [ALONG])
    assert rep["cut_on_deck_carriageway_m"] == 0.0 and abs(rep["noise_barriers_m"] - 80.0) < 0.5


def test_barrier_off_the_deck_is_untouched():
    walls, rep = _run(GROUND + 1.0, [[(-20.0, 20.0), (60.0, 20.0)]])
    assert rep["cut_on_deck_carriageway_m"] == 0.0 and abs(rep["noise_barriers_m"] - 80.0) < 0.5
