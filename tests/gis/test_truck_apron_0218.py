"""ADR 0218: authored truck apron (`truck_apron` override on a roundabout ring way) on a synthetic 4-arm roundabout.

* with the override the ISLAND side of every ring chain carries the given width, lip height and surface, the meshed
  apron strip is that wide and the island kerb moves inward by the extra width (smaller island);
* without the override (or with an override on another way) nothing changes: default 2.0 m sett apron, 4 cm lip;
* malformed / out-of-range values and a target that is not a ring are reported stale and change nothing.
Pure Python, no Data/raw.  Run: uv run --project tools/worldgen python -m pytest tests/gis -k 0218 -q
"""
import copy
import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "worldgen"))

from roads import meshing as M  # noqa: E402
from roads import network as Nw  # noqa: E402
from roads import standards as S  # noqa: E402

R_AXIS = 8.8          # Knyszyn ring axis radius (OSM way 1426801304, K1: diameter ~17.6 m)
RING_WAY = 900
ARM_WAY = 901


def _attr(v, src="osm"):
    return {"v": v, "src": src, "conf": "high"}


def _graph(ring_width=None):
    """4 ring edges counter-clockwise (one OSM way) between 4 arm nodes at 0/90/180/270 deg + 4 radial arms."""
    nodes, edges = [], []
    ang = [0.0, 90.0, 180.0, 270.0]
    for k, a in enumerate(ang):
        t = math.radians(a)
        nodes.append({"id": f"r{k}", "x": R_AXIS * math.cos(t), "y": R_AXIS * math.sin(t)})
        nodes.append({"id": f"o{k}", "x": (R_AXIS + 40) * math.cos(t), "y": (R_AXIS + 40) * math.sin(t)})
    ring_attrs = {"highway": _attr("primary"), "junction": _attr("roundabout"), "oneway": _attr("yes", "derived"),
                  "lanes": _attr(1, "default"), "surface": _attr("asphalt")}
    if ring_width is not None:
        ring_attrs["width"] = _attr(ring_width, "bdot10k")
    for k in range(4):
        a0, a1 = math.radians(ang[k]), math.radians(ang[k] + 90.0)
        t = np.linspace(a0, a1, 16)
        geo = np.column_stack([R_AXIS * np.cos(t), R_AXIS * np.sin(t)]).tolist()
        edges.append({"id": f"w{RING_WAY}:{k}", "from": f"r{k}", "to": f"r{(k + 1) % 4}", "osm_way": RING_WAY,
                      "geometry": geo, "attrs": copy.deepcopy(ring_attrs), "length_m": R_AXIS * math.pi / 2})
        a = math.radians(ang[k])
        d = np.array([math.cos(a), math.sin(a)])
        geo = [(d * R_AXIS).tolist(), (d * (R_AXIS + 20)).tolist(), (d * (R_AXIS + 40)).tolist()]
        edges.append({"id": f"w{ARM_WAY}:{k}", "from": f"r{k}", "to": f"o{k}", "osm_way": ARM_WAY, "geometry": geo,
                      "attrs": {"highway": _attr("primary"), "oneway": _attr("no"), "lanes": _attr(2),
                                "surface": _attr("asphalt")}, "length_m": 40.0})
    return {"nodes": nodes, "edges": edges}


def _net(overrides=None):
    net = Nw.load(_graph(), (0.0, 0.0), overrides or [])
    Nw.assign_sides(net, [], built_up=True, walkways=[])
    return net


def _rings(net):
    rings = [c for c in net.chains if c.roundabout]
    assert len(rings) == 4
    return rings


def _island_side(c):
    side = "L" if (c.dirn > 0).mean() >= 0.5 else "R"
    assert (c.side[side]["kind"] == Nw.ISLAND).all()
    return side


def _mesh(net):
    """Flat (z = 0) meshes of the ring chains; returns MeshBuf."""
    buf = M.MeshBuf()
    for c in _rings(net):
        c.z = np.zeros(len(c.line.s))
        c.e = np.zeros(len(c.line.s))
        M.build_ribbon(buf, net, c)
    return buf


def _radii(buf, mat):
    V = np.vstack([p.V for p in buf.parts if p.mat == mat and p.layer == "road" and len(p.T)])
    return np.hypot(V[:, 0], V[:, 1]), V[:, 2]


def _ov(**apron):
    return [{"id": "test-apron", "target": {"osm_way": RING_WAY}, "set": {"truck_apron": apron}}]


def test_default_ring_is_unchanged_without_override():
    net = _net()
    for c in _rings(net):
        side = _island_side(c)
        d = c.side[side]
        assert np.allclose(d["raw"]["w"], S.ROUNDABOUT_APRON_W)
        assert (d["mat"] == 0).all()
        assert all(net.sec_list[int(i)].truck_apron is None for i in np.unique(c.sec_idx))
    r, z = _radii(_mesh(net), "apron_sett")
    hw = 2.0                                     # single-lane ring: S.SINGLE_LANE_DEFAULT 4.0 m
    assert r.max() == pytest.approx(R_AXIS - hw, abs=0.15)
    assert r.min() == pytest.approx(R_AXIS - hw - S.ROUNDABOUT_APRON_W, abs=0.15)
    assert z.min() == pytest.approx(S.KERB_HEIGHT_APRON, abs=1e-6)


def test_unrelated_override_is_zero_change():
    """Regression: an override set for another way leaves every side array and every vertex identical."""
    a = _net()
    b = _net([{"id": "other", "target": {"osm_way": ARM_WAY}, "set": {"edge_lines": "none"}}])
    for ca, cb in zip(_rings(a), _rings(b)):
        for side in ("L", "R"):
            for k in ("kind", "mat", "h", "w", "depth"):
                assert np.array_equal(ca.side[side][k], cb.side[side][k]), (ca.id, side, k)
    ma, mb = _mesh(a), _mesh(b)
    assert [(p.mat, p.V.shape) for p in ma.parts] == [(p.mat, p.V.shape) for p in mb.parts]
    for pa, pb in zip(ma.parts, mb.parts):
        assert np.array_equal(pa.V, pb.V)


def test_truck_apron_sets_width_height_and_surface():
    net = _net(_ov(width_m=3.0, height_m=0.05, material="kostka"))
    assert "test-apron" not in net.overrides_stale
    for c in _rings(net):
        d = c.side[_island_side(c)]
        assert np.allclose(d["raw"]["w"], 3.0)
        assert np.allclose(d["raw"]["h"], 0.05)
        assert (d["mat"] == 5).all()
        sec = net.sec_list[int(c.sec_idx[0])]
        assert sec.truck_apron["material"] == "apron_sett"
        assert sec.provenance["truck_apron"] == "authored_override:test-apron"
    buf = _mesh(net)
    r, z = _radii(buf, "apron_sett")
    hw = 2.0
    assert r.max() == pytest.approx(R_AXIS - hw, abs=0.15)
    assert r.max() - r.min() == pytest.approx(3.0, abs=0.2)           # apron 3.0 m wide
    assert z.min() == pytest.approx(0.05, abs=1e-6)                   # lip 5 cm
    assert z.max() == pytest.approx(0.05 + 0.02 * 3.0, abs=1e-6)      # 2 % rise to the island kerb


def test_island_shrinks_by_the_extra_apron_width():
    def island_kerb_r(net):
        r, _ = _radii(_mesh(net), "curb_concrete")
        return float(np.median(r[r < R_AXIS - 2.0 - 0.5]))     # island kerb ring only (inside the apron)
    r0 = island_kerb_r(_net())
    r1 = island_kerb_r(_net(_ov(width_m=3.0)))
    assert r0 - r1 == pytest.approx(3.0 - S.ROUNDABOUT_APRON_W, abs=0.15)


@pytest.mark.parametrize("mat,expect", [("beton", "road_concrete"), ("asfalt", "road_asphalt")])
def test_truck_apron_other_surfaces(mat, expect):
    net = _net(_ov(width_m=2.5, height_m=0.03, material=mat))
    r, z = _radii(_mesh(net), expect)
    inner = r < R_AXIS - 2.0 + 0.05                                    # the apron strip, not the ring carriageway
    assert r[inner].max() - r[inner].min() == pytest.approx(2.5, abs=0.2)


@pytest.mark.parametrize("bad", [{"width_m": 0.2}, {"width_m": 9.0}, {"width_m": 2.0, "height_m": 0.15},
                                 {"width_m": 2.0, "material": "marble"}, {"height_m": 0.04}, "3.0"])
def test_invalid_truck_apron_is_stale_and_changes_nothing(bad):
    net = Nw.load(_graph(), (0.0, 0.0), [{"id": "bad", "target": {"osm_way": RING_WAY}, "set": {"truck_apron": bad}}])
    assert "bad" in net.overrides_stale
    assert all(s.truck_apron is None for s in net.sec_list)


def test_truck_apron_on_a_non_ring_way_is_stale():
    net = Nw.load(_graph(), (0.0, 0.0), [{"id": "arm", "target": {"osm_way": ARM_WAY},
                                         "set": {"truck_apron": {"width_m": 2.0}}}])
    assert "arm" in net.overrides_stale
    assert all(s.truck_apron is None for s in net.sec_list)


def test_knyszyn_example_override_is_valid():
    """The prepared (not applied) Knyszyn fragment parses and targets the OSM ring way of the roundabout."""
    import yaml
    p = Path(__file__).resolve().parents[2] / "tools/worldgen/roads/examples/knyszyn-roundabout-apron.yaml"
    ov = yaml.safe_load(p.read_text(encoding="utf-8"))["overrides"]
    assert len(ov) == 1 and ov[0]["target"] == {"osm_way": [1426801304]}
    ta = Nw._truck_apron(ov[0]["set"]["truck_apron"])
    assert ta is not None and ta["material"] == "apron_sett"
    # ring asphalt + apron within 6.0-8.5 m (WR-D-31-3 as quoted in ADR 0218, secondary source)
    assert 6.0 <= ov[0]["set"]["width"] + ta["width_m"] <= 8.5
