"""ADR 0305 (klattow-s24): Dom Klattow authored from its BDOT footprint and the owner's photos."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import LineString

from roads import pipeline
from streetscape import buildings_mesh as BM
from streetscape import knyszyn_dom_klattow_0305 as K
from streetscape import materials as MT

ROOT = Path(__file__).resolve().parents[2]
ORIGIN = (761611.0, 612607.0)
Z0 = 126.4


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, src="", UV1=None, **_):
        self.parts.append((layer, mat, np.asarray(V, float), np.asarray(UV, float), np.asarray(T)))


@pytest.fixture(scope="module")
def fc():
    return json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf8"))


def _build(fc, roads_poly=None):
    hero = K.hero_targets("knyszyn", fc)
    blds = BM.load({"features": [f for f in fc["features"] if f["id"] == K.BUILDING_ID]}, ORIGIN,
                   pipeline.load_overrides("knyszyn"), hero=hero)
    buf, rep = _Buf(), {}
    res = K.build(buf, "knyszyn", blds, lambda e, n: np.full(np.shape(e), Z0), rep, roads_poly)
    return blds[0], buf, res, rep


def test_only_knyszyn_and_only_the_sourced_footprint(fc):
    assert K.hero_targets("knyszyn", fc) == {K.BUILDING_ID: K.ASSET_ID}
    assert K.hero_targets("knyszyn-w", fc) == {}
    assert K.hero_targets("knyszyn", {"features": []}) == {}
    box = {"features": [{"id": K.BUILDING_ID, "geometry": {"coordinates": [[[[0, 0], [20, 0], [20, 8], [0, 8], [0, 0]]]]}}]}
    assert K.hero_targets("knyszyn", box) == {}                 # no porch: not the house the module was written for
    rep = {}
    assert K.build(_Buf(), "knyszyn-w", [], None, rep)["status"] == "skipped" and rep == {}


def test_frame_is_the_bdot_body_with_the_porch_on_the_street_side(fc):
    b, _, res, rep = _build(fc)
    a, d, n, L, W, pu0, pu1, pd = K._frame(b["poly"])
    assert L == pytest.approx(21.10, abs=0.05) and W == pytest.approx(7.84, abs=0.05)
    assert pu1 - pu0 == pytest.approx(2.7, abs=0.1) and pd == pytest.approx(2.0, abs=0.1)
    assert n[1] < -0.9 and d[0] > 0.9                           # the street (Koscielna) lies south-south-west
    assert res["status"] == "applied" and rep[K.ASSET_ID] is res
    assert res["roof_pitch_deg"] == pytest.approx(39.7, abs=0.5)
    # street windows keep clear of the porch roof, both end windows stay on the wall
    pc = (pu0 + pu1) / 2
    for off in K.FRONT_WINDOWS:
        u0, u1 = pc + off - K.WIN_W / 2 - 0.09, pc + off + K.WIN_W / 2 + 0.09
        assert 0.3 < u0 and u1 < L - 0.3
        assert u1 < pu0 - K.PORCH_OV or u0 > pu1 + K.PORCH_OV
    for uc, w in K.BACK_WINDOWS + (K.BACK_DOOR,):
        assert 0.3 < uc - w / 2 and uc + w / 2 < L - 0.3
    spans = sorted((uc - w / 2 - 0.09, uc + w / 2 + 0.09) for uc, w in K.BACK_WINDOWS + (K.BACK_DOOR,))
    assert all(a1 < b0 for (_, a1), (b0, _) in zip(spans, spans[1:]))


def test_mesh_materials_budget_and_winding(fc):
    b, buf, res, _ = _build(fc)
    mats0 = {m for l, m, *_ in buf.parts if l == "buildings"}
    mats1 = {m for l, m, *_ in buf.parts if l == "buildings_low"}
    assert {K.LOG, K.BOARD_W, K.STAIN, K.TRIM, K.TILE, K.STONE, K.BRICK, "glass"} <= mats0
    assert {K.LOG, K.BOARD_W, K.TILE, K.BRICK} <= mats1 and K.TRIM not in mats1 and K.STONE not in mats1
    assert (mats0 | mats1) <= set(MT.M)
    assert not {"wood_planks", "roof_tiles_red", "plaster_white"} & mats0     # no raw brown boards, no rule roof
    tris = {l: sum(len(T) for ll, _, _, _, T in buf.parts if ll == l) for l in ("buildings", "buildings_low")}
    assert tris == {"buildings": res["triangles"]["lod0"], "buildings_low": res["triangles"]["lod1"]}
    assert tris["buildings"] < 6000 and tris["buildings_low"] < 150
    for l, m, V, UV, T in buf.parts:
        assert np.isfinite(V).all() and np.isfinite(UV).all() and len(UV) == len(V) and T.max() < len(V)
        e1, e2 = V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]]
        assert (np.linalg.norm(np.cross(e1, e2), axis=1) > 1e-7).all(), (l, m)
    # the log walls face out of the footprint and carry the set's courses once over their height
    c = np.asarray(b["poly"].centroid.coords[0])
    V, UV, T = next((V, UV, T) for l, m, V, UV, T in buf.parts if l == "buildings" and m == K.LOG)
    nrm = np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])
    mid = V[T].mean(axis=1)
    assert (np.einsum("ij,ij->i", nrm[:, :2], mid[:, :2] - c) > 0).all() and np.abs(nrm[:, 2]).max() < 1e-9
    assert UV[:, 1].min() == pytest.approx(0.0) and UV[:, 1].max() == pytest.approx(K.WALL_TOP - K.PLINTH_TOP)
    assert UV[:, 1].max() <= MT_SPEC()["log_whitewash"]["tile_m"][1]
    # roof: every tile triangle of the two main slopes looks up; ridge at the LoD2 height
    V, UV, T = next((V, UV, T) for l, m, V, UV, T in buf.parts if l == "buildings" and m == K.TILE)
    assert (np.cross(V[T[:, 1]] - V[T[:, 0]], V[T[:, 2]] - V[T[:, 0]])[:, 2] > 0).all()
    assert V[:, 2].max() - Z0 == pytest.approx(K.RIDGE + 0.07, abs=0.02)
    assert b["props"]["lod2_eave_rel_m"] == pytest.approx(K.WALL_TOP, abs=0.05)
    assert b["props"]["height_lod2_2017_m"] == pytest.approx(K.RIDGE, abs=0.05)


def MT_SPEC():
    return json.loads((ROOT / "art-source/world/materials/materials_spec.json").read_text(encoding="utf8"))["sets"]


def test_fence_stands_off_the_road_footprint(fc):
    b, _, res, _ = _build(fc)
    a, d, n, L, W, pu0, pu1, pd = K._frame(b["poly"])
    assert res["fence"]["offset_from_wall_m"] == pytest.approx(pd - 0.03, abs=0.01) and res["fence"]["pickets"] > 120
    road = LineString([a + n * 1.6 - d * 10, a + n * 1.6 + d * 40]).buffer(0.25)      # footway edge 1.35 m off the wall
    res2 = _build(fc, road)[2]
    assert 0.8 <= res2["fence"]["offset_from_wall_m"] <= 1.35 - K.ROAD_CLEAR_M + 1e-6
    road = LineString([a + n * 0.6 - d * 10, a + n * 0.6 + d * 40]).buffer(0.25)      # no room for a fence
    res3 = _build(fc, road)[2]
    assert res3["fence"] == {"offset_from_wall_m": None, "pickets": 0} and res3["status"] == "applied"


def test_materials_and_sets():
    for k in ("log_wall_white", "wood_planks_white", "wood_planks_stain", "roof_tiles_old", "fieldstone_plinth"):
        m = MT.M[k]
        assert m["tint_linear"] is True and m["set_tile"] is True, k
    assert MT.M["log_wall_white"]["texture_set"] == "log_whitewash" and MT.M["fieldstone_plinth"]["texture_set"] == "fieldstone"
    assert MT.M["roof_tiles_old"]["texture_set"] == "roof_tiles" and MT.M["roof_tiles_old"]["macro"][1] > MT.M["roof_tiles_red"]["macro"][1]
    assert "texture_set" not in MT.M["wood_trim_brown"]
    assert "roof_tiles_old" not in BM.ROOF_OVERRIDES and "log_wall_white" not in BM.HOUSE_WALL_OVERRIDES   # authored asset only
    sys.path.insert(0, str(ROOT / "art-source/world/materials/_src"))
    import sets_facade as F
    assert F.FACADE_SETS["log_whitewash"]["tile_m"] == [4.0, 2.2] and F.FACADE_SETS["fieldstone"]["tile_m"] == [2.4, 0.6]
    spec = MT_SPEC()
    for name in ("log_whitewash", "fieldstone"):
        assert spec[name]["kind"] == "modulation_set" and spec[name]["albedo"]["mean_lum_linear"] == pytest.approx(0.5, abs=0.01)


def test_log_courses_of_the_set():
    png = ROOT / "art-source/world/materials/log_whitewash/High/T_log_whitewash_BaseColor.png"
    if not png.exists():
        pytest.skip("log_whitewash not built (build_all.py --only log_whitewash)")
    from PIL import Image
    lum = np.asarray(Image.open(png).convert("L"), float)
    row = lum[:, : lum.shape[1]].mean(axis=1)
    row = row - np.convolve(np.pad(row, 30, mode="wrap"), np.ones(61) / 61, mode="valid")
    dark = row < -0.25 * row.std() - 2.0
    joints = int(np.sum(dark & ~np.roll(dark, 1)))
    assert 8 <= joints <= 12                                    # ten courses of 0.20-0.24 m in the 2.2 m tile


def test_plot_fence_override_and_lamus(fc):
    import shapely
    from streetscape import plots as PL
    ov = pipeline.load_overrides("knyszyn")
    blds = BM.load(fc, ORIGIN, ov, hero=K.hero_targets("knyszyn", fc))
    b = next(x for x in blds if x["id"] == K.BUILDING_ID)
    assert b["ovr"]["hero_asset"] == K.ASSET_ID and b["ovr"]["plot_fence"] == {"front": "picket", "side": "picket"}
    near = [{"id": x["id"], "poly": x["poly"], "props": x["props"], "ovr": x["ovr"]} for x in blds
            if x["typ"] == "house" and x["poly"].distance(b["poly"]) < 60]
    plots = {p["id"]: p for p in PL.plan(near, shapely.geometry.Polygon(), [])}
    assert (plots[K.BUILDING_ID]["front_style"], plots[K.BUILDING_ID]["side_style"]) == ("picket", "picket")
    rule = {p["id"]: p for p in PL.plan([{**h, "ovr": {}} for h in near], shapely.geometry.Polygon(), [])}
    assert all(rule[i]["front_style"] == plots[i]["front_style"] for i in plots if i != K.BUILDING_ID)   # others untouched
    bad = [{**h, "ovr": {"plot_fence": {"front": "marble"}}} if h["id"] == K.BUILDING_ID else h for h in near]
    with pytest.raises(ValueError, match="plot_fence"):
        PL.plan(bad, shapely.geometry.Polygon(), [])
    lamus = next(x for x in blds if x["id"] == "bdot:40f8044a-d048-4ad8-ad57-d8b8a2886fe1")
    assert lamus["typ"] == "house" and lamus["sub"] == "dom_drewniany" and lamus["props"]["height_m"] == 6.4
    assert lamus["ovr"]["roof_shape"] == "hip"
