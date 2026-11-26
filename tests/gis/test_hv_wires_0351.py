"""ADR 0351 (CRITIC s24 wave 11 # 1): no lattice tower without conductors - in the tile and in the far-field ring.

No Unity, raw data or world build needed (synthetic lines + the committed streetscape sources of one tile)."""
import json

import numpy as np
import pytest

from conftest import REPO
from streetscape import far_field as FF
from streetscape import furniture as FU


def _gis(lines, pylons):
    return {"power_lines": lines, "pylons": pylons}


def test_in_tile_mapped_tower_between_bdot_vertices_is_a_support():
    """A tower 150 m along a 600 m BDOT segment: the old equal subdivision put rule supports at 0 / 300 / 600 m
    and left the tower beside the conductor."""
    pl = FU.Placer(lambda e, n: np.zeros_like(np.asarray(e, float)))
    pl.add("pylon", np.array([150.0, 3.0]), 0.0, src="osm:node/1", group="pylon")
    rep = {}
    S = FU.power_supports(pl, np.array([[0.0, 0.0], [600.0, 0.0]]), True, "t", None, rep)
    assert any(np.hypot(*(s - [150.0, 3.0])) < 1e-6 for s in S)
    assert rep["mapped_supports"] == 1
    # no rule tower within one gap of the mapped one, every gap <= the span maximum
    gaps = np.hypot(*np.diff(S, axis=0).T)
    assert gaps.max() <= FU.SPAN_MAX_M["pylon"] + 1e-6 and gaps.min() > 100.0
    assert np.all(np.diff(S[:, 0]) > 0)   # ordered along the line


def test_far_field_towers_only_on_hv_lines_and_all_wired():
    half = 1024.0
    hv = {"pts": [[half, 200.0], [half + 900.0, 260.0], [half + 1600.0, 900.0]], "hv": True, "src": "bdot10k", "id": "h"}
    mv = {"pts": [[-half - 50.0, 0.0], [-half - 900.0, 40.0]], "hv": False, "src": "bdot10k", "id": "m"}
    osm_dup = {"pts": [[half + 5.0, 210.0], [half + 905.0, 270.0]], "hv": True, "src": "osm", "id": "osm_w1"}
    untagged = {"pts": [[0.0, -half - 200.0], [400.0, -half - 900.0]], "hv": None, "src": "osm", "id": "osm_w2"}
    pylons = [{"id": "t1", "e": half + 400.0, "n": 228.0, "kind": "słup energetyczny"},     # on the HV line
              {"id": "p1", "e": -half - 400.0, "n": 21.0, "kind": "słup energetyczny"},     # MV pole: dropped
              {"id": "m1", "e": 0.0, "n": half + 900.0, "kind": "maszt lub wieża telekomunikacyjna"}]
    plan = FF.power_plan(_gis([hv, mv, osm_dup, untagged], pylons), half)
    st = plan["stats"]
    assert st["lines_hv_bdot"] == 1 and st["osm_hv_duplicates_of_bdot"] == 1 and st["osm_untagged_dropped"] == 1
    assert st["unwired_power_pylons"] == 0 and st["seam_supports"] == 1
    assert st["dropped_towers_off_hv_lines"] == {"słup energetyczny": 1}
    assert [m["id"] for m in plan["masts"]] == ["m1"]
    assert any(p["id"] == "t1" for p in plan["pylons"])
    # every drawn tower ends a span; spans <= span max; the seam support is not drawn (the tile owns it)
    ends = {id(x) for ab in plan["spans"] for x in ab}
    assert all(id(p) in ends for p in plan["pylons"])
    assert not any(p["seam"] for p in plan["pylons"])
    for a, b in plan["spans"]:
        assert 5.0 <= np.hypot(a["e"] - b["e"], a["n"] - b["n"]) <= FU.SPAN_MAX_M["pylon"] + 1e-6


def test_far_span_conductors_hang_from_arm_tips_with_sag():
    half = 1024.0
    elev = FF.BorderElevation(half, [100.0] * 2, [100.0] * 2, [100.0] * 2, [100.0] * 2)
    a = {"e": half, "n": 0.0, "h": 32.0, "seam": True}
    b = {"e": half + 120.0, "n": 0.0, "h": 32.0, "seam": False}     # inside the unforeshortened band
    for tier, n_cond in (("High", 7), ("Low", 2)):
        sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
        FF._add_span(sectors, a, b, elev, half, tier)
        p = sectors["far_east"].primitives()[0]
        assert p["mat"] == "far_field_buildings" and set(p["COL"][:, 3]) == {0.0}
        V = p["V"]
        # the seam end sits on the tile tower's arm tips: lateral 4.3 m, heights 20/24/28 - 1.3 m (+ earth 32 m)
        seam = V[np.isclose(V[:, 0], half)]
        lat = np.unique(np.round(np.abs(seam[:, 1]), 2))
        assert set(lat) <= {0.0, 4.3}
        zc = np.unique(np.round((seam[:, 2].reshape(-1, 2).mean(1) if len(seam) % 2 == 0 else seam[:, 2]) - 100.0, 1))
        assert zc.min() >= 18.6 and zc.max() <= 32.1
        # mid-span lower than the ends (sag), conductors count
        mid = V[(V[:, 0] > half + 20.0) & (V[:, 0] < half + 100.0)]
        assert mid[:, 2].min() < seam[:, 2].min()
        assert len(np.unique(np.round(np.abs(seam[:, 1]) + seam[:, 2], 1))) >= n_cond // 2


def test_galvanised_colour_is_grey_and_varies():
    cols = np.array([FF.galv_colour(f"t{i}") for i in range(200)])
    assert cols.max() < 0.2 and cols.min() > 0.12            # mid grey, not the old 0.27-0.30 (white in sun)
    assert np.ptp(cols[:, 1]) > 0.02                          # per-tower variation
    assert np.all(np.abs(cols[:, 0] - cols[:, 2]) < 0.025)    # no saturated tint


@pytest.mark.parametrize("region", ["bialystok-kleeberga", "dk65-monki-05"])
def test_committed_tiles_have_no_unwired_mapped_pylon(region):
    import sys
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
    import hv_wires_audit as A
    t = A.in_tile(region)
    assert t["pylon"]["mapped"] > 0 and t["pylon"]["unwired"] == 0, t["pylon"]["unwired_at"]


def test_far_field_mv_line_near_the_tile_gets_poles_and_three_conductors():
    half = 1024.0
    mv = {"pts": [[500.0, half], [520.0, half + 900.0]], "hv": False, "mv": True, "src": "bdot10k", "id": "m"}
    lv = {"pts": [[-500.0, half], [-520.0, half + 900.0]], "hv": False, "mv": False, "src": "osm", "id": "osm_w9"}
    plan = FF.power_plan(_gis([mv, lv], []), half)
    st = plan["stats"]
    assert st["mv_lines_near"] == 1 and st["mv_seam_supports"] == 1 and st["pylons"] == 0
    # clipped at MV_FAR_MAX_M; spans <= the MV span maximum; every pole wired
    assert max(p["n"] for p in plan["mv_poles"]) <= half + FF.MV_FAR_MAX_M + 1e-6
    for a, b in plan["mv_spans"]:
        assert np.hypot(a["e"] - b["e"], a["n"] - b["n"]) <= FU.SPAN_MAX_M["power_pole"] + 1e-6
    ends = {id(x) for ab in plan["mv_spans"] for x in ab}
    assert all(id(p) in ends for p in plan["mv_poles"])
    elev = FF.BorderElevation(half, [100.0] * 2, [100.0] * 2, [100.0] * 2, [100.0] * 2)
    sectors = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    a, b = plan["mv_spans"][0]
    assert a["seam"]
    FF._add_span(sectors, a, b, elev, half, "High", mv=True)
    V = sectors["far_north"].primitives()[0]["V"]
    seam = V[np.isclose(V[:, 1], half, atol=1e-6)]
    assert len(seam) and np.allclose(seam[:, 2], 111.7, atol=0.1)   # 100 + 12 - 0.3 m: the tile pole's insulators
    FF._add_pole(sectors, b, elev, half)
    lows = {s: FF.SectorBuilder(s) for s in FF.SECTORS}
    FF._add_span(lows, a, b, elev, half, "Low", mv=True)
    assert not any(x.primitives() for x in lows.values())     # MV: High only
