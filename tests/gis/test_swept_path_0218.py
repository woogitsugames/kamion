"""ADR 0218: kinematic swept path of the 16.47 m tractor + semitrailer through the Knyszyn roundabout.
Run: uv run --project tools/worldgen python -m pytest tests/gis -k 0218 -q"""
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))

from roads import standards as S  # noqa: E402
from roads import swept_path as SP  # noqa: E402


def test_combination_matches_dims_json():
    import json
    dims = json.loads((Path(__file__).resolve().parents[2] / "art-source/truck/dims.json").read_text(encoding="utf-8"))["values"]
    v = SP.Combination()
    assert v.L1 == dims["wheelbase_m"]["value"] and v.c == dims["fifth_wheel_lead_m"]["value"]
    assert v.kp_rear == dims["semitrailer_kingpin_to_rear_m"]["value"]
    assert tuple(-z for z in dims["trailer_axle_z_m"]["value"]) == v.trailer_axles
    assert v.length == pytest.approx(dims["artic_length_m"]["value"], abs=1e-9)


def test_simulation_converges_to_the_closed_form_on_a_circle():
    """Front axle driven around a circle for 3 turns: radii approach R2 = sqrt(Rk^2 - L2^2) (tractrix steady state)."""
    v = SP.Combination()
    Rf = 9.12
    R1 = math.sqrt(Rf * Rf - v.L1 ** 2)
    ss = SP.steady_state(R1, v)
    lead = np.column_stack([np.full(3000, Rf), np.linspace(-60.0, 0.0, 3000, endpoint=False)])
    t = np.linspace(0.0, 6 * math.pi, int(6 * math.pi * Rf / 0.02))
    circ = np.column_stack([Rf * np.cos(t), Rf * np.sin(t)])
    path = SimpleNamespace(pts=np.vstack([lead, circ]), phase=np.r_[np.zeros(len(lead)), np.full(len(circ), 2)],
                           ring_arc_deg=1080.0)
    r = SP.simulate(path, v)
    assert r["tyre_min_r_trailer"] == pytest.approx(ss["trailer_inner_tyre"], abs=0.05)
    assert r["steer_max_deg"] == pytest.approx(ss["steer_deg"], abs=0.5)
    assert r["body_max_r_ring"] == pytest.approx(ss["front_outer_corner"], abs=0.05)


def test_generator_default_ring_passes_straight_on_but_not_left():
    """Knyszyn as the generator builds it today (axis r 8.8, ring 4.0 m -> outer kerb r 10.8, default 2.0 m apron,
    island kerb r 4.8): straight on clears the island, the left turn (return Rynek -> Bialystok) does not."""
    island = 8.8 - 2.0 - S.ROUNDABOUT_APRON_W
    assert SP.required(10.8, 174.0)["tyre_min_r"] > island
    assert SP.required(10.8, 262.0)["tyre_min_r"] < island - 1.0


def test_proposed_knyszyn_apron_clears_every_manoeuvre():
    """ADR 0218 proposal: ring 5.0 m (outer r 11.3) + 3.2 m truck apron -> island kerb r 3.1 m."""
    island = 11.3 - 5.0 - 3.2
    for turn in (98.0, 174.0, 262.0, 282.0, 360.0):
        r = SP.required(11.3, turn)
        assert r["tyre_min_r"] >= island + SP.ISLAND_CLEARANCE, turn
        assert r["steer_max_deg"] <= SP.Combination().max_steer_deg
        assert r["tyre_max_r_ring"] <= 11.3 - 0.5 + 0.02           # outer front tyre inside the outer kerb


def test_bigger_roundabout_needs_less_apron():
    a = SP.apron_needed(11.3, 5.0, 262.0)["apron_w_needed"]
    b = SP.apron_needed(13.0, 6.0, 262.0)["apron_w_needed"]
    assert b < a


def test_knyszyn_ring_sectors_clear_the_u_turn():
    """The prepared override on the real Knyszyn graph (in memory, region files untouched): in every generated ring
    chain (smoothed OSM axis, not a perfect circle) the U-turn tyre path for that chain's outer kerb radius stays
    ISLAND_CLEARANCE off the island kerb face."""
    import json
    import yaml
    from roads import network as Nw
    root = Path(__file__).resolve().parents[2]
    d = root / "Data/Regions/knyszyn"
    reg = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
    origin = (reg["origin"]["x"], reg["origin"]["y"])
    ov = yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    ex = yaml.safe_load((root / "tools/worldgen/roads/examples/knyszyn-roundabout-apron.yaml").read_text(encoding="utf-8"))
    net = Nw.load(json.loads((d / "roads.graph.json").read_text(encoding="utf-8")), origin, ov + ex["overrides"])
    Nw.assign_sides(net, [], built_up=True, walkways=[])
    assert "knyszyn-roundabout-truck-apron" not in net.overrides_stale
    pts = np.vstack([np.asarray(e["geometry"]) for e in json.loads((d / "roads.graph.json").read_text(encoding="utf-8"))["edges"]
                     if e["osm_way"] == 1426801304])
    ctr = pts.mean(0) - np.array(origin)
    rings = [c for c in net.chains if c.roundabout and any(e.startswith("w1426801304") for e, _ in c.edges)]
    assert rings
    cache = {}
    for c in rings:
        side = "L" if (c.dirn > 0).mean() >= 0.5 else "R"
        r_axis = float(np.hypot(*(c.line.p - ctr).T).mean())
        hw, w = float(c.hw.mean()), float(c.side[side]["w"].mean())
        assert w == pytest.approx(3.2) and (c.side[side]["mat"] == 5).all()
        R_ext = round(r_axis + hw, 2)
        if R_ext not in cache:
            cache[R_ext] = SP.required(R_ext, 360.0)["tyre_min_r"]
        assert cache[R_ext] >= r_axis - hw - w + SP.ISLAND_CLEARANCE, (c.id, R_ext)
