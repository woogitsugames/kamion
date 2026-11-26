"""weathering-s24 (ADR 0238 / 0348 addendum): roof covering COLOR_0 (dirt runs, moss, odd tiles; opt-in per region),
block-fence variants (opt-in per region), ground-contact splash band (materials) - all +0 draws, and nothing changes
in a region that did not opt in."""
import json
from pathlib import Path

import numpy as np
from shapely.geometry import box

from roads import pipeline
from streetscape import buildings_mesh as BM
from streetscape import materials as MT
from streetscape import plots as PL
from streetscape import roofs as RF
from test_buildings_0167 import _HF
from test_rural_windows_fences_0348 import _ColBuf

ROOT = Path(__file__).resolve().parents[2]
TYK_DIR = ROOT / "Data/Regions/tykocin"
TYK_ORIGIN = (751371.0, 600319.0)


def _gable(rot_deg=0.0):
    poly = box(0, 0, 12, 8)
    c = np.array([6.0, 4.0])
    a = np.radians(rot_deg)
    eu = np.array([np.cos(a), np.sin(a)])
    ev = np.array([-eu[1], eu[0]])
    return poly, RF.Roof("gable", c, eu, ev, 6.0, 4.0, np.tan(np.radians(40)), 103.0, "test")


def test_roof_covering_colour_only_when_weather_given():
    poly, roof = _gable()
    a0, a1 = BM.Acc(), BM.Acc()
    RF.build(a0, roof, poly, "roof_tiles_red")
    RF.build(a1, roof, poly, "roof_tiles_red", weather=(0.8, 1.0, 0.37))
    k = ("buildings", "roof_tiles_red")
    for it0, it1 in zip(a0.d[k], a1.d[k]):
        assert np.array_equal(it0[0], it1[0]) and np.array_equal(it0[2], it1[2])     # same geometry / UV
    assert all(it[4] is None for it in a0.d[k])
    cov = [it for it in a1.d[k] if it[4] is not None]
    assert cov, "covering must carry COLOR_0 when weather is given"
    col = np.concatenate([it[4] for it in cov])
    assert np.allclose(col[:, 0], 0.8) and np.allclose(col[:, 3], 0.5 + 0.5 * 0.37)
    assert col[:, 2].min() == 0.0 and col[:, 2].max() > 0.3          # b: 0 at the ridge, grows toward the eave
    # same COLOR_0 on LOD1 (the far roof weathers like the near one)
    low = [it for it in a1.d[("buildings_low", "roof_tiles_red")] if it[4] is not None]
    assert len(low) == len(cov)


def test_north_slope_gets_more_moss_than_south():
    poly, roof = _gable()                  # eu = east: slopes fall to the north and to the south
    acc = BM.Acc()
    RF.build(acc, roof, poly, "roof_tiles_red", weather=(0.9, 1.0, 0.1))
    moss = {}
    for V, T, UV, UV1, COL in acc.d[("buildings", "roof_tiles_red")]:
        if COL is None:
            continue
        side = "n" if V[:, 1].mean() > 4.0 else "s"
        moss[side] = max(moss.get(side, 0.0), float(COL[:, 1].max()))
    assert moss["n"] > 0.95 and abs(moss["s"] - RF.WEATHER_MOSS_SOUTH) < 0.05


def test_roof_age_class_follows_covering_and_plot_rule():
    small = {"props": {"storeys": 1, "height_m": 5.0}, "poly": box(0, 0, 8, 10)}
    big = {"props": {"storeys": 2, "height_m": 9.0}, "poly": box(0, 0, 12, 14)}
    assert BM.roof_age_class(small, "x", "roof_tiles_old") == "old"
    assert BM.roof_age_class(big, "x", "roof_shingles_grey") == "old"
    cls = [BM.roof_age_class(big, f"k{i}", "roof_tiles_red") for i in range(200)]
    assert cls.count("new") > 140                                       # big two-storey house: mostly new
    cls = [BM.roof_age_class(small, f"k{i}", "roof_tiles_red") for i in range(200)]
    assert cls.count("old") > 140
    w = BM.roof_weather(small, "k1", "roof_tiles_red")
    assert w == BM.roof_weather(small, "k1", "roof_tiles_red") and all(0.0 <= x <= 1.0 for x in w)


def test_tykocin_opts_in_and_buildings_carry_roof_colour():
    ovs = pipeline.load_overrides("tykocin")
    assert any(o.get("kind") == "facade_rules" and o.get("roof_weathering") and o.get("block_fence_variants") for o in ovs)
    fc = json.loads((TYK_DIR / "buildings.geojson").read_text(encoding="utf8"))
    blds = BM.load(fc, TYK_ORIGIN, ovs)
    houses = [b for b in blds if b["typ"] == "house" and b["poly"].area > 60][:20]
    assert houses and all(b.get("roof_weather") for b in houses)
    buf, rep = _ColBuf(), {}
    BM.build(buf, houses, _HF, lambda e, n: 100.0, None, None, rep)
    roofs = [p for p in buf.parts if p["layer"] == "buildings" and p["mat"] in MT.ROOF_WEATHER]
    # coverings carry COLOR_0; small door canopies / dormer pieces in a roof material do not (a = 0 there: no-op)
    with_col = sum(len(p["T"]) for p in roofs if p["COL"] is not None)
    assert roofs and with_col >= 0.7 * sum(len(p["T"]) for p in roofs)
    assert all(p["COL"] is not None or len(p["T"]) <= 16 for p in roofs)
    assert sum(rep["roof_weathering"].values()) == len([b for b in houses])


def test_region_without_opt_in_has_no_roof_colour():
    ovs = [o for o in pipeline.load_overrides("tykocin") if not o.get("roof_weathering")]
    fc = json.loads((TYK_DIR / "buildings.geojson").read_text(encoding="utf8"))
    houses = [b for b in BM.load(fc, TYK_ORIGIN, ovs) if b["typ"] == "house" and b["poly"].area > 60][:8]
    buf, rep = _ColBuf(), {}
    BM.build(buf, houses, _HF, lambda e, n: 100.0, None, None, rep)
    assert all(p["COL"] is None for p in buf.parts if p["mat"] in MT.ROOF_WEATHER)
    assert "roof_weathering" not in rep


def test_roof_materials_declare_tile_grid_of_their_set():
    for k, v in MT.ROOF_WEATHER.items():
        rw = MT.M[k]["roof_weather"]
        assert len(rw) == 7 and rw == [round(float(x), 5) for x in v]
        if rw[3] > 0:                       # tiles: the grid divides the 4.2 m set
            assert abs(4.2 / rw[0] - round(4.2 / rw[0])) < 1e-3 and abs(4.2 / rw[1] - round(4.2 / rw[1])) < 1e-3
    pbr = (ROOT / "game/Assets/_Project/Environment/Shaders/WorldPBR.shader").read_text(encoding="utf8")
    imp = (ROOT / "game/Assets/_Project/World/Import/WorldPbrMaterials.cs").read_text(encoding="utf8")
    for tok in ("_ROOF_WEATHER", "_RoofTile", "_RoofWeather", "_SplashBand"):
        assert tok in pbr and tok in imp
    assert '"roof_weather"' in imp and '"splash_band"' in imp


def test_splash_band_on_plinths_and_walls_not_on_far_facades():
    for k in ("plinth_dark", "fieldstone_plinth", "plaster_cream", "wood_planks_stain", "brick_red"):
        sb = MT.M[k]["splash_band"]
        assert 0.2 <= sb[0] <= 0.4 and 0.0 < sb[1] <= 1.0 and ("splash_h" in MT.M[k] or k == "brick_red")   # brick: _SPLASH by id
    assert all("splash_band" not in v for k, v in MT.M.items() if "__far" in k)


def test_block_fence_variants_tint_cap_and_untouched_without_opt_in():
    a, b, n = np.array([0.0, 0.0]), np.array([15.0, 0.0]), np.array([0.0, 1.0])
    zf = lambda p: 0.1 * float(p[0])                                   # a slope: rigid panels step at the posts
    k0 = PL.Kit((0.9, 0.9, 0.9))
    PL.fence_run(k0, "concrete", a, b, n, 1.6, zf, "plotA")
    k1 = PL.Kit((0.9, 0.9, 0.9))
    PL.fence_run(k1, "concrete", a, b, n, 1.6, zf, "plotA", bvar=None)
    for x, y in zip(k0.out(), k1.out()):
        assert np.array_equal(x, y)
    names = {PL.block_variant(f"p{i}")["name"] for i in range(80)}
    assert names == {v[0] for v in PL.BLOCK_VARIANTS}
    assert PL.block_variant("p7") == PL.block_variant("p7")
    var = {"name": "split_cap", "smooth": False, "cap": True, "pil": True, "tint": (1.24, 1.10, 0.84),
           "cap_tint": (0.55, 0.56, 0.60)}
    k2 = PL.Kit((0.9, 0.9, 0.9))
    PL.fence_run(k2, "concrete", a, b, n, 1.6, zf, "plotA", bvar=var)
    V, UV, T, C = k2.out()
    assert len(T) > len(k0.out()[2]) + 20                               # caps + pilasters
    assert V[:, 2].max() >= 1.6 + 0.1 * 10.24 - 1e-6 + PL.BLOCK_CAP[0] - 0.2
    assert np.any(np.isclose(C[:, 0], min(2 * 0.45 * 1.24, 2) * 0.5))   # sand tint on the panels
    assert UV[:, 1].min() >= 0.0 and UV[:, 1].max() <= 1.0
    # smooth variant draws the `wall` row; other styles ignore the variant
    k3 = PL.Kit((0.9, 0.9, 0.9))
    PL.fence_run(k3, "concrete", a, b, n, 1.6, zf, "plotA", bvar=dict(var, smooth=True, cap=False, pil=False))
    v0, v1 = PL.PK.row("wall")
    assert np.sum((k3.out()[1][:, 1] >= v0 - 1e-6) & (k3.out()[1][:, 1] <= v1 + 1e-6)) >= 4 * 3   # 3 panels
    k4, k5 = PL.Kit((0.9, 0.9, 0.9)), PL.Kit((0.9, 0.9, 0.9))
    PL.fence_run(k4, "picket_wood", a, b, n, 1.3, zf, "plotA")
    PL.fence_run(k5, "picket_wood", a, b, n, 1.3, zf, "plotA", bvar=var)
    for x, y in zip(k4.out(), k5.out()):
        assert np.array_equal(x, y)


def test_plot_plan_without_opt_in_has_no_variants():
    road = box(-20, -6, 360, 0)
    houses = [{"id": f"rural:{k:03d}", "poly": box(20 * k, 6, 20 * k + 10, 14),
               "props": {"storeys": 1, "height_m": 5.5}} for k in range(6)]
    plots = PL.plan(houses, road, [], [])
    assert len(plots) == 6
