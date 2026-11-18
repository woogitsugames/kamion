"""ADR 0281: build_world speed-ups that must not change a byte of the output (K1b, K1c, K2, K4a, K5).

Each test pins the equivalence the change relies on; the whole-build proof (sha256 of every output file before /
after on the same synthetic-NMT input) is in docs/adr/0281-build-world-perf-no-byte-change.md.

    uv run --project tools/worldgen python -m pytest tools/worldgen/tests/test_perf_0281.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import shapely

WG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WG))

from roads import network as N          # noqa: E402
from roads import standards as S        # noqa: E402
from streetscape import paved as PV     # noqa: E402


# ------------------------------------------------------------------------------------------- K1b
@pytest.mark.parametrize("r", [S.RURAL_FOOT_M / 2 + 1.0, 1.4, 3.0])
def test_point_buffer_envelope_is_exact_box(r):
    """STRtree.query(g) tests envelopes only, so query(_qbox(q, r)) == query(q.buffer(r)) iff the envelopes are equal.
    They are bit-equal (GEOS puts the circle's extreme vertices at angle 0 / pi/2 / pi / 3pi/2)."""
    rng = np.random.default_rng(281)
    xy = rng.uniform(-6000.0, 6000.0, (100_000, 2))
    xy[:500] = np.round(xy[:500])
    got = shapely.bounds(shapely.buffer(shapely.points(xy), r))
    exp = np.column_stack([xy[:, 0] - r, xy[:, 1] - r, xy[:, 0] + r, xy[:, 1] + r])
    assert np.array_equal(got, exp)
    q = shapely.Point(*xy[7])
    assert shapely.bounds(N._qbox(q, r)).tolist() == exp[7].tolist()


def test_qbox_query_same_candidates_same_order():
    rng = np.random.default_rng(2810)
    lines = [shapely.LineString(rng.uniform(-300, 300, (2, 2)) + rng.uniform(-50, 50, 2)) for _ in range(400)]
    tree = shapely.STRtree(lines)
    for x, y in rng.uniform(-350, 350, (3000, 2)):
        q = shapely.Point(x, y)
        for r in (1.4, 3.0, 4.5):
            assert tree.query(q.buffer(r)).tolist() == tree.query(N._qbox(q, r)).tolist()


# ------------------------------------------------------------------------------------------- K1c
def _chain(e):
    n = len(e)
    s = np.arange(n) * 0.5
    c = N.Chain(id="c", node_a="a", node_b="b", edges=[], raw=np.zeros((2, 2)), raw_spans=[])
    c.line = SimpleNamespace(s=s, length=float(s[-1]))
    c.hw = np.full(n, 3.5)
    c.z = 130.0 + 0.01 * s
    c.e = e
    return c


def _crossfall_ref(c, s, lat):           # the pre-0281 body of Chain.crossfall_z
    s = np.asarray(s, float)
    lat = np.asarray(lat, float)
    e = c.interp(np.nan_to_num(c.e, nan=0.0), s)
    roof = c.interp(np.isnan(c.e).astype(float), s) > 0.5
    hw = c.hw_at(s)
    latc = np.clip(lat, -hw, hw)
    return c.zc(s) + np.where(roof, -S.CROSSFALL * np.abs(latc), e * latc)


def test_crossfall_z_cached_equals_reference_and_follows_new_e():
    rng = np.random.default_rng(5)
    e = rng.uniform(-0.03, 0.03, 200)
    e[40:90] = np.nan
    c = _chain(e)
    s, lat = rng.uniform(-5, 110, 500), rng.uniform(-6, 6, 500)
    ref = _crossfall_ref(c, s, lat)
    assert np.array_equal(c.crossfall_z(s, lat), ref)
    assert np.array_equal(c.crossfall_z(s, lat), ref)              # cached path
    c.e = c.e + 0.01                                               # profile.match_crossfall_at_nodes replaces e
    ref2 = _crossfall_ref(c, s, lat)
    assert not np.array_equal(ref, ref2)
    assert np.array_equal(c.crossfall_z(s, lat), ref2)
    for i in range(20):                                            # scalar calls (meshing / furniture)
        assert c.crossfall_z(float(s[i]), float(lat[i])) == _crossfall_ref(c, float(s[i]), float(lat[i]))


def test_crossfall_cache_source_is_read_only():
    c = _chain(np.full(50, 0.02))
    c.crossfall_z(1.0, 1.0)
    with pytest.raises(ValueError):
        c.e[3] = 0.0                     # an in-place edit would leave the cache stale: it must fail loudly


# ------------------------------------------------------------------------------------------- K2
def _parts(seed, n=60):
    rng = np.random.default_rng(seed)
    out = []
    for k in range(n):
        x, y = rng.uniform(0, 400, 2)
        V = np.array([[x, y, 0.0], [x + 6, y, 0.0], [x + 6, y + 4, 0.0], [x, y + 4, 0.0]])
        out.append(SimpleNamespace(V=V, T=np.array([[0, 1, 2], [0, 2, 3]]), footprint=k % 7 != 0, mat="road_asphalt"))
    return out


def test_road_footprint_memo_same_polygon_as_union():
    PV._FOOTPRINT_MEMO.clear()
    parts = _parts(1)
    T = np.concatenate([p.V[p.T][:, :, :2] for p in parts if p.footprint])
    ref = PV._road_footprint_union(T)
    a = PV.road_footprint_polygon(parts)
    assert shapely.to_wkb(a) == shapely.to_wkb(ref)
    b = PV.road_footprint_polygon([SimpleNamespace(**vars(p)) for p in parts])     # new objects, same triangles
    assert b is a
    c = PV.road_footprint_polygon(_parts(2))
    assert c is not a and not c.equals(a)
    d = PV.road_footprint_polygon(parts, bounds=(0, 0, 200, 200))                  # bounds is part of the key
    assert d is not a and d.area < a.area
    assert PV.road_footprint_polygon([]).is_empty


def test_road_footprint_memo_is_bounded():
    PV._FOOTPRINT_MEMO.clear()
    for s in range(PV._FOOTPRINT_MEMO_MAX + 3):
        PV.road_footprint_polygon(_parts(100 + s, 8))
    assert len(PV._FOOTPRINT_MEMO) == PV._FOOTPRINT_MEMO_MAX


# ------------------------------------------------------------------------------------------- K4a
def test_build_meshes_fills_nan_grid_once(monkeypatch):
    calls = []
    real = np.nan_to_num

    def counting(*a, **k):
        if np.ndim(a[0]) == 2:
            calls.append(1)
        return real(*a, **k)

    monkeypatch.setattr(PV.np, "nan_to_num", counting)
    hf = SimpleNamespace(x0=-50.0, y1=50.0)
    z = np.full((101, 101), 130.0)
    z[:20] = np.nan
    added = []
    buf = SimpleNamespace(add=lambda *a, **k: added.append(a[0]))
    items = [{"poly": shapely.box(-40 + 9 * i, -10, -33 + 9 * i, 5), "mat": "paving_concrete", "id": f"p{i}"}
             for i in range(8)]
    PV.build_meshes(buf, items, z, hf)
    assert len(added) >= 16
    assert len(calls) == 2                 # one mean-filled grid for the surfaces, one zero-filled for the edges


# ------------------------------------------------------------------------------------------- K5
def test_textures_cached_and_equal_to_the_single_literal():
    from streetscape import export as EX
    a = EX.textures()
    b = EX.textures()
    assert a is not b and list(a) == list(b) and all(a[k] is b[k] for k in a if k not in ("viaduct_steel",
                                                                                       "fire_station_alpha"))
    ref = {**{k: EX.SG.png_bytes(im) for k, im in EX.FT.textures().items()},
           "fence_mesh": EX.SG.png_bytes(EX.fence_mesh_png()), "dock_digits": EX.SG.png_bytes(EX.SG.digits_atlas()),
           "plate_back": EX.SG.png_bytes(EX.SG.plate_back()), "car_dirt": EX.SG.png_bytes(EX.car_dirt_png()),
           "car_plates": EX.SG.png_bytes(EX.LC.plate_atlas()),
           "car_tyre": EX.SG.png_bytes(EX.LC.tyre_texture()),
           "viaduct_steel": (EX.ART / "textures" / "viaduct_steel.png").read_bytes(),
           "fire_station_alpha": (EX.ART / "textures" / "fire_station_alpha.png").read_bytes(),
           **{k: EX.SG.png_bytes(im) for k, im in EX.HT.textures().items()},
           **{k: EX.SG.png_bytes(im) for k, im in EX.PKT.textures().items()},
           **{k: EX.SG.png_bytes(im) for k, im in EX.CB.textures().items()}}
    assert list(a) == list(ref)
    assert all(a[k] == ref[k] for k in ref)


# ------------------------------------------------------------------------------------------- K4b
def test_near_road_equals_distance_on_whole_polygon():
    rng = np.random.default_rng(44)
    roads = shapely.union_all([shapely.LineString(rng.uniform(0, 800, (2, 2))).buffer(rng.uniform(2, 6))
                               for _ in range(40)])
    shapely.prepare(roads)
    for _ in range(300):
        c = rng.uniform(-50, 850, 2)
        pts = c + rng.normal(0, rng.uniform(1, 40), (rng.integers(1, 60), 2))
        ref = shapely.distance(shapely.points(pts), roads) < 0.6
        assert np.array_equal(PV.near_road(pts, roads, 0.6), ref)
    # points exactly on / around the threshold are re-measured on the whole polygon
    edge = np.asarray(roads.geoms[0].exterior.coords if roads.geom_type == "MultiPolygon" else roads.exterior.coords)
    q = edge[:50] + np.array([0.6, 0.0])
    assert np.array_equal(PV.near_road(q, roads, 0.6), shapely.distance(shapely.points(q), roads) < 0.6)
    assert not PV.near_road(np.array([[5000.0, 5000.0]]), roads, 0.6).any()
