"""ADR 0194: road stains follow the traffic (class, junction approaches, wheel paths), oil stays matt and dark."""
from types import SimpleNamespace

import numpy as np

from roads import decals as DC
from streetscape.materials import M


def _sec(oneway, lanes=2, lane_w=3.5, edge=0.25, cls="Z"):
    return SimpleNamespace(oneway=oneway, lanes=lanes, lane_w=lane_w, edge_strip=edge, cls=cls)


def test_class_rates_follow_pavement_age():
    r = DC.PATCH_RATE_CLASS
    assert r["GP"] < r["G"] < r["Z"] < r["L"] <= r["D"]
    assert DC.JUNCTION_BOOST > 1.0 > DC.MIDBLOCK_RATE


def test_wheel_path_patches_sit_in_wheel_paths():
    """Every hashed wheel-path offset is within 0.15 m (jitter) of 0.26 / 0.74 of a lane, the _ROADWEAR paths."""
    for oneway in (True, False):
        sec = _sec(oneway)
        hw = sec.edge_strip + sec.lanes * sec.lane_w / (1 if oneway else 2) if oneway else 3.75
        outer = 0
        for k in range(400):
            lat = DC.wheel_path_lat(None, sec, hw, ("t", oneway, k))
            lane_pos = (lat + hw - sec.edge_strip) / sec.lane_w
            lc = lane_pos - np.floor(lane_pos)
            assert abs(abs(lc - 0.5) - DC.WHEEL_PATH_FRAC) <= 0.15 / sec.lane_w + 1e-9, (oneway, lat, lc)
            outer += (lc < 0.5) if (oneway or lat < 0) else (lc > 0.5)
        assert 0.55 < outer / 400 < 0.75          # OUTER_PATH_SHARE 0.65


def test_oil_look_is_matt_dark_and_opt_in():
    look = M["decal_oil"]["oil_look"]
    asphalt_smooth = 0.094                     # materials_spec asphalt_worn smoothness_mean (Low)
    assert look["smooth_aged"] <= asphalt_smooth * 1.2 and look["smooth_fresh"] < 0.3
    assert 0.4 <= look["coverage_gamma"] < 1.0
    # manhole / drain covers share _DECAL_ALPHA; they must not get the oil look
    assert all("oil_look" not in v for k, v in M.items() if k != "decal_oil")


def test_plate_uv1_spread_encoding_round_trips():
    """ADR 0194: plate UV1.y = 20 + 100 * spread + min(edge, 1); decode like KamionPlateWear."""
    from roads import meshing as MS
    for spread in (0.0, 0.3, 1.0):
        for edge in (0.0, 0.2, 0.64, 3.0):
            enc = MS.PLATE_EDGE_FLAG + MS.PLATE_SPREAD_SCALE * spread + min(edge, 1.0)
            assert enc > 15.0
            v = enc - MS.PLATE_EDGE_FLAG
            dec_spread = min(max((v - 1.0) / MS.PLATE_SPREAD_SCALE, 0.0), 1.0)
            if spread == 0.0:
                assert dec_spread == 0.0 and abs(min(max(v, 0.0), 1.0) - min(edge, 1.0)) < 1e-9
            else:
                assert abs(dec_spread - spread) <= 1.0 / MS.PLATE_SPREAD_SCALE + 1e-9
