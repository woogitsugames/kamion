"""Synthetic tests for carriageway prop clearing and authored gate-island collision preservation (agy-props-carriageway-s25)."""

from __future__ import annotations

import numpy as np
import pytest
from shapely.geometry import Point, box

from roads import consistency as CQ
from roads import meshing as M
from streetscape import furniture as FU


def _flat_z(e, n):
    return np.full(np.shape(e), 140.0, dtype=float)


def test_clear_carriageway_pushes_edge_props_within_5cm():
    """Props within 0..5 cm inside the carriageway boundary (previously missed by buffer(-0.05)) are pushed 0.8 m out."""
    carriage = box(0.0, -5.0, 20.0, 5.0)
    pl = FU.Placer(_flat_z)
    # 2 mm, 20 mm, and 49 mm inside the north carriageway edge (y = 5.0)
    pl.add("bollard", (4.0, 4.998), 0.0, src="osm:node/1")
    pl.add("sign_post", (8.0, 4.980), 0.0, src="osm:node/2")
    pl.add("plate_D-6", (8.0, 4.980), 0.0, z=142.3, src="osm:node/2")
    pl.add("lamp_11m", (12.0, 4.951), 0.0, src="rule:c1")

    rep = {}
    FU.clear_carriageway(pl, carriage, _flat_z, rep)

    assert rep["props_off_carriageway"]["moved"] == 3
    for it in pl.items:
        assert not carriage.contains(Point(it["e"], it["n"])), it
        assert it["n"] == pytest.approx(5.8, abs=1e-3), it
    # Stacked plate stays at the same (e, n) and preserves vertical offset above its post
    post = [it for it in pl.items if it["p"] == "sign_post"][0]
    plate = [it for it in pl.items if it["p"] == "plate_D-6"][0]
    assert (post["e"], post["n"]) == (plate["e"], plate["n"])
    assert plate["z"] - post["z"] == pytest.approx(2.3, abs=1e-3)


def test_clear_carriageway_moves_signal_rail_and_plate_g2():
    """Rail crossing signals (`signal_rail_*`) inside a carriageway move off it together with stacked `plate_G-2`."""
    carriage = box(-10.0, -4.0, 10.0, 4.0)
    pl = FU.Placer(_flat_z)
    pl.add("signal_rail_saltire_g3", (0.0, 2.1), 0.0, z=140.0, src="rail:crossing:0:sign")
    pl.add("plate_G-2", (0.0, 2.1), 0.0, z=141.15, src="rail:crossing:0:G-2")

    rep = {}
    FU.clear_carriageway(pl, carriage, _flat_z, rep)

    assert rep["props_off_carriageway"]["moved"] == 1
    assert len(pl.items) == 2
    for it in pl.items:
        assert it["n"] == pytest.approx(4.8, abs=1e-3)
        assert not carriage.contains(Point(it["e"], it["n"]))
    # Also check consistency / clear_level_carriageways recognises signal_rail_*
    assert "signal_rail" in CQ.GROUND_PROPS
    assert "signal_rail" in FU.GROUND_PROPS


def test_clear_carriageway_preserves_authored_island_props():
    carriage = box(0.0, -5.0, 20.0, 5.0)
    pl = FU.Placer(_flat_z)
    pl.add("signal_mast", (10.0, 0.0), 0.0, src="override:island-sig")
    pl.on_authored_island = {(10.0, 0.0)}

    rep = {}
    FU.clear_carriageway(pl, carriage, _flat_z, rep)

    assert rep["props_off_carriageway"]["moved"] == 0
    assert (pl.items[0]["e"], pl.items[0]["n"]) == (10.0, 0.0)


def test_cull_sides_on_carriageway_keeps_override_gate_island_collision():
    """Gate kit islands (`override:<id>:island`) keep their `collision_curb` even when laid over a carriageway patch."""
    buf = M.MeshBuf()
    # Road carriageway in [0..20, 0..20] at z = 140.0
    vr = np.array([[0.0, 0.0, 140.0], [20.0, 0.0, 140.0], [20.0, 20.0, 140.0], [0.0, 20.0, 140.0]])
    buf.add("road", "road_asphalt", vr, vr[:, :2].copy(), [[0, 1, 2], [0, 2, 3]], src="c_road")
    # Gate island collision_curb in [8..12, 8..12] at z = 140.16
    vi = np.array([[8.0, 8.0, 140.16], [12.0, 8.0, 140.16], [12.0, 12.0, 140.16], [8.0, 12.0, 140.16]])
    buf.add("collision", "collision_curb", vi, vi[:, :2].copy(), [[0, 1, 2], [0, 2, 3]],
            src="override:kwadrat-park-gate-kit:island")
    # Stray ribbon collision_curb in [2..6, 2..6] at z = 140.12 (must still be culled)
    vs = np.array([[2.0, 2.0, 140.12], [6.0, 2.0, 140.12], [6.0, 6.0, 140.12], [2.0, 6.0, 140.12]])
    buf.add("collision", "collision_curb", vs, vs[:, :2].copy(), [[0, 1, 2], [0, 2, 3]], src="c_stray")

    out = M.cull_sides_on_carriageway(buf)

    srcs = [p.src for p in buf.parts]
    assert "override:kwadrat-park-gate-kit:island" in srcs
    assert "c_stray" not in srcs
    assert out["kerb_tris"] == 2
