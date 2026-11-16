"""ADR 0238 - building typology of Białystok: subtype rule (wielka płyta, kamienica, pawilon, ...), roof shape from
override / OSM roof:shape / measured LoD2 rise, observed block palette, rule shopfront of pavilions, the measured
height allowance of buildings.py, and the triangle budget of regions C and Dojlidy against the generator before the
change (tests/gis/data/typology_0238_baseline_*.json, written by tools/worldgen/qa/typology_budget.py on origin/main
25924f60b)."""
import glob
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import yaml
from shapely.geometry import box
from shapely.geometry.polygon import orient

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
REGIONS = {"bialystok-industrial-c": (777995.0, 596223.0), "bialystok-dojlidy": (780043.0, 590079.0)}
DATA = Path(__file__).parent / "data"
C_TRIS_HIGH_LIMIT = 2_000_000                       # tile C per-frame High triangle limit (test_world_v31, ADR 0221)
_HF = SimpleNamespace(sample=lambda x, y: np.full(np.shape(x), 100.0))
ROAD = box(-50, -30, 80, -10)                       # a road south of the synthetic buildings


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kw):
        self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V, float), T=np.asarray(T).reshape(-1, 3)))

    def mats(self, layer):
        return {p.mat for p in self.parts if p.layer == layer}

    def tris(self, layer):
        return sum(len(p.T) for p in self.parts if p.layer == layer)


def _b(props, w=30.0, d=12.0, ovr=None, bid="t:1"):
    from streetscape import buildings_mesh as BM
    from streetscape import typology as TY
    poly = orient(box(0, 0, w, d))
    p = {"height_m": 6.0, "height_source": "gugik_lod1_2024", **props}
    ovr = ovr or {}
    typ = BM.classify(p, poly.area, ovr)
    return {"id": bid, "poly": poly, "props": p, "ovr": ovr, "typ": typ, "sub": TY.subtype(typ, p, poly.area, ovr)}


def _build(*bs):
    from streetscape import buildings_mesh as BM
    buf, rep = _Buf(), {}
    BM.build(buf, list(bs), _HF, None, None, ROAD, rep, sign_out=[])
    return buf, rep


def _load(rid):
    from streetscape import buildings_mesh as BM
    d = REPO / "Data" / "Regions" / rid
    fc = json.loads((d / "buildings.geojson").read_text(encoding="utf-8"))
    ov = (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])
    return fc, BM.load(fc, REGIONS[rid], ov)


# ------------------------------------------------------------------------------------------- rule
BLOCK = {"function": "budynek wielorodzinny", "storeys": 5, "height_m": 15.8}
TENEMENT = {"function": "budynek wielorodzinny", "storeys": 3, "height_m": 11.5, "roof_type_lod2": "1030",
            "height_lod2_2017_m": 13.4, "lod2_eave_rel_m": 10.2}
PAVILION = {"function": "obiekt handlowo-usługowy", "storeys": 1, "height_m": 4.4}
OFFICE = {"function": "siedziba firmy lub firm", "storeys": 3, "height_m": 11.0}
HOUSE = {"function": "budynek jednorodzinny", "storeys": 2, "height_m": 7.7}
HALL = {"function": "magazyn", "height_m": 9.0}
SHED = {"function": "garaż", "height_m": 2.8}


def test_subtype_of_every_type():
    got = {n: (_b(p)["typ"], _b(p)["sub"]) for n, p in (("block", BLOCK), ("tenement", TENEMENT), ("pavilion", PAVILION),
                                                         ("office", OFFICE), ("house", HOUSE), ("hall", HALL), ("shed", SHED))}
    assert got == {"block": ("block", "wielka_plyta"), "tenement": ("block", "kamienica"),
                   "pavilion": ("office", "pawilon"), "office": ("office", "biurowiec"), "house": ("house", "dom"),
                   "hall": ("hall", "hala"), "shed": ("shed", "gospodarczy")}


def test_subtype_limits_and_sources():
    from streetscape import typology as TY
    sub = lambda p, area=360.0, ovr=None, typ=None: TY.subtype(typ or _b(p)["typ"], p, area, ovr)
    assert sub({**PAVILION, "storeys": 2}) == "biurowiec"                       # two storeys: not a pavilion
    assert sub({**PAVILION, "height_m": 8.2}) == "biurowiec"                    # a tall one-storey box
    assert sub({**PAVILION, "storeys": None, "height_m": 6.0, "height_source": "default"}) == "biurowiec"
    assert sub({"function": "yes", "osm_building": "retail", "storeys": 1, "height_m": 4.0}) == "pawilon"   # OSM tag
    assert sub({**TENEMENT, "storeys": 5}) == "wielka_plyta"                    # above KAMIENICA_MAX_STOREYS
    assert sub(TENEMENT, area=1200.0) == "wielka_plyta"
    assert sub({**BLOCK, "storeys": 3, "roof_shape_osm": "hipped"}) == "kamienica"          # OSM roof:shape
    # override: a subtype names its render class; a render class keeps the plain subtype
    from streetscape import buildings_mesh as BM
    assert BM.classify(OFFICE, 300.0, {"typology": "kamienica"}) == "block"
    assert sub(OFFICE, ovr={"typology": "kamienica"}, typ="block") == "kamienica"
    assert BM.classify(PAVILION, 300.0, {"typology": "office"}) == "office"
    assert sub(PAVILION, ovr={"typology": "office"}) == "biurowiec"
    assert BM.classify(BLOCK, 300.0, {"typology": "hall"}) == "hall"            # as before ADR 0238
    with pytest.raises(ValueError):
        BM.classify(BLOCK, 300.0, {"typology": "palac"})


def test_roof_shape_order_and_measured_rise():
    from streetscape import typology as TY
    low = {**TENEMENT, "height_lod2_2017_m": 9.4, "lod2_eave_rel_m": 8.9, "height_m": 9.2}     # 1030, rise 0.5 m
    porch = {**TENEMENT, "height_lod2_2017_m": 14.2, "lod2_eave_rel_m": 2.8, "height_m": 11.4}  # eave of a porch
    assert TY.roof_shape("block", TENEMENT, {}) == ("gable", "lod2_rise")
    assert TY.roof_shape("block", low, {}) == (None, None) and TY.roof_shape("block", porch, {}) == (None, None)
    assert TY.roof_shape("house", TENEMENT, {}) == (None, None)                 # houses: roofs.plan's own LoD2 rule
    assert TY.roof_shape("block", {**low, "roof_shape_osm": "hipped"}, {}) == ("hip", "osm")
    assert TY.roof_shape("house", {"roof_shape_osm": "flat"}, {}) == ("flat", "osm")
    assert TY.roof_shape("house", {"roof_shape_osm": "onion"}, {}) == (None, None)        # cannot build: data rule
    assert TY.roof_shape("block", {**TENEMENT, "roof_shape_osm": "hipped"}, {"roof_shape": "flat"}) == ("flat", "override")
    with pytest.raises(ValueError):
        TY.roof_shape("block", {}, {"roof_shape": "dome"})


def test_block_roofs_coded_gable_are_low_slope_in_the_data():
    """The measurement behind ROOF_MIN_RISE_M: multi-family buildings coded 1030 in LoD2 2017."""
    from streetscape import typology as TY
    rises = []
    for rid in REGIONS:
        for f in json.loads((REPO / "Data" / "Regions" / rid / "buildings.geojson").read_text(encoding="utf-8"))["features"]:
            p = f["properties"]
            if p["function"] == "budynek wielorodzinny" and p["roof_type_lod2"] == "1030":
                rises.append(TY.lod2_rise(p))
    assert len(rises) == 10 and None not in rises
    assert sum(r < 1.0 for r in rises) == 9 and max(r for r in rises if r < 1.0) < 0.85
    assert sum(r >= TY.ROOF_MIN_RISE_M for r in rises) == 1


def test_pavilion_heights_measured():
    from streetscape import typology as TY
    hs = []
    for rid in REGIONS:
        for f in json.loads((REPO / "Data" / "Regions" / rid / "buildings.geojson").read_text(encoding="utf-8"))["features"]:
            p = f["properties"]
            if (p["function"] in TY.PAVILION_FUNCS and p["storeys"] == 1 and p["area_m2"] < 1500
                    and p["height_source"].startswith("gugik_lod1")):
                hs.append(p["height_m"])
    assert len(hs) == 71
    assert [round(float(x), 1) for x in np.percentile(hs, [10, 50, 90])] == [3.0, 4.2, 6.8]
    assert np.mean(np.array(hs) <= TY.PAVILION_MAX_H) > 0.9


# ------------------------------------------------------------------------------------------- palette / tables
def test_palettes_use_materials_the_far_set_has():
    from streetscape import buildings_mesh as BM
    from streetscape import materials as MT
    from streetscape import typology as TY
    assert BM.BLOCK_WALLS is TY.BLOCK_WALLS
    for w in set(TY.BLOCK_WALLS) | set(TY.KAMIENICA_WALLS):
        assert w in MT.M and f"{w}__far_block" in MT.M, w
    for w in set(TY.PAVILION_WALLS):
        assert w in MT.M and f"{w}__far_office" in MT.M, w
    # observed shares (9 photographed blocks, research/mistral/p3-buildings-2): white 3, grey 3, beige 2, orange 1
    n = {w: TY.BLOCK_WALLS.count(w) for w in set(TY.BLOCK_WALLS)}
    assert n == {"plaster_white": 3, "plaster_grey": 3, "plaster_cream": 2, "plaster_peach": 1}
    for old in ("plaster_pastel_blue", "plaster_yellow", "plaster_sage"):      # still valid as authored wall_material
        assert f"{old}__far_block" in MT.M
    for c in (TY.PAVILION_FRONT["glass"], TY.PAVILION_FRONT["glass_lod1"], TY.PAVILION_FRONT["fascia_material"]):
        assert c in MT.M


def test_block_colours_of_m53_rows_match_the_palette_source():
    import csv
    rows = list(csv.DictReader((REPO / "research/mistral/p3-buildings-2/manifest_v2.csv").open(encoding="utf-8-sig"), delimiter=";"))
    ok = [r for r in rows if r["status"].startswith("OK") and r["typ_budynku"].startswith("blok mieszkalny")
          and not r["kolor_elewacji"].startswith("UNVERIFIED")]
    tone = lambda t: next(k for k in ("biał", "szar", "beż", "pomarańcz") if k in t.split(" z ")[0].split("(")[0].lower())
    cnt = {}
    for r in ok:
        cnt[tone(r["kolor_elewacji"])] = cnt.get(tone(r["kolor_elewacji"]), 0) + 1
    assert cnt == {"biał": 3, "szar": 3, "beż": 2, "pomarańcz": 1}


def test_proportions_carry_a_status():
    from streetscape import buildings_mesh as BM
    from streetscape import typology as TY
    for sub, pr in TY.PROPORTIONS.items():
        assert sub in TY.SUBTYPES
        for k in ("storey_status", "plinth_status", "axis_status"):
            assert pr[k] in ("SOURCED", "MEASURED", "ESTIMATED", "WORKING_VALUE"), (sub, k)
    wp = TY.PROPORTIONS["wielka_plyta"]
    assert wp["storey_m"] == BM.STOREY_H["block"] == 2.8 and wp["storey_status"] == "SOURCED"
    assert "R4-075" in wp["storey_source"] and "NOT used" in wp["storey_source"]          # review errata E1
    assert wp["plinth_m"] == BM.ZBASE["block"] and TY.PROPORTIONS["biurowiec"]["storey_m"] == BM.STOREY_H["office"]
    assert BM.storey_plan("block", 11.5, {"storeys": 3}, "kamienica") == (3, pytest.approx((11.5 - 0.6 - 0.8) / 3), 0.6)
    assert BM.storey_plan("block", 15.8, {"storeys": 5}) == BM.storey_plan("block", 15.8, {"storeys": 5}, "wielka_plyta")


def test_storey_plan_keeps_the_kamienica_fit_with_the_0242_storeys_fixed_rule():
    """Merge #122 x #123 (review s22 #123): the storey range of the subtype must survive the storeys_fixed branch -
    a reset `lo, hi = block range` after it would drop a 3.9 m kamienica storey (fits 2.8-4.0, not 2.6-3.8)."""
    from streetscape import buildings_mesh as BM
    h = 0.6 + 0.8 + 2 * 3.9
    assert BM.storey_plan("block", h, {"storeys": 2}, "kamienica") == (2, pytest.approx(3.9), 0.6)
    assert BM.storey_plan("block", h, {"storeys": 2}, "kamienica") == BM.storey_plan(
        "block", h, {"storeys": 2, "storeys_fixed": True}, "kamienica")
    # ADR 0242: an authored count is kept whatever the storey height, for an office as before
    n, sh, zb = BM.storey_plan("office", 15.4, {"storeys": 3, "storeys_fixed": True})
    assert n == 3 and zb == BM.ZBASE["office"] and sh > 4.6


# ------------------------------------------------------------------------------------------- meshes
def test_tenement_has_a_pitched_roof_and_window_rows_on_both_lods():
    buf, rep = _build(_b(TENEMENT, w=22.0, d=11.0))
    blk, brep = _build(_b({**TENEMENT, "roof_type_lod2": "1000"}, w=22.0, d=11.0))
    assert rep["subtypes"] == {"kamienica": 1} and rep["roofs_other"] == {"kamienica:gable:lod2_rise": 1}
    for layer in ("buildings", "buildings_low"):
        assert any(m.startswith("roof_") and m != "roof_membrane" for m in buf.mats(layer)), layer
        assert "roof_membrane" not in buf.mats(layer)
    assert any(m.endswith("__far_block") for m in buf.mats("buildings_low"))            # window rows on LOD1
    assert rep["balconies"] == 0 and brep["balconies"] > 0 and brep["subtypes"] == {"wielka_plyta": 1}
    assert "chimney_brick" not in buf.mats("buildings")
    ridge = max(float(p.V[:, 2].max()) for p in buf.parts if p.layer == "buildings" and p.mat.startswith("roof_"))
    assert 100.0 + 11.5 < ridge < 100.0 + 15.0
    # LOD1 costs no more than the flat-roofed block it replaces; LOD0 far less (no balconies, vents, machine room)
    assert buf.tris("buildings_low") <= blk.tris("buildings_low") and buf.tris("buildings") < blk.tris("buildings")


def test_pavilion_front_faces_the_road_on_both_lods():
    from streetscape import typology as TY
    buf, rep = _build(_b(PAVILION, w=24.0, d=10.0))
    assert rep["subtypes"] == {"pawilon": 1} and rep["pavilion_fronts"] == 1
    glass = [p for p in buf.parts if p.layer == "buildings" and p.mat == "showroom_glass"]
    assert glass and all(abs(float(p.V[:, 1].mean())) < 0.2 for p in glass)             # the south wall (y = 0): road side
    z0, z1 = min(float(p.V[:, 2].min()) for p in glass), max(float(p.V[:, 2].max()) for p in glass)
    assert z0 == pytest.approx(100.0 + TY.PAVILION_FRONT["glass_z"][0]) and z1 == pytest.approx(100.0 + 2.75)
    assert "showroom_glass" not in buf.mats("buildings_low")                            # LOD1: no new material
    low = np.concatenate([p.V for p in buf.parts if p.layer == "buildings_low" and p.mat == "hall_flashing"])
    pane = low[np.isclose(low[:, 1], -0.05)]                                            # one quad 5 cm proud of the wall
    assert len(pane) == 4 and pane[:, 2].min() == pytest.approx(z0) and pane[:, 2].max() == pytest.approx(z1)
    # the other walls keep the office windows (far rows on LOD1)
    assert any(m.endswith("__far_office") for m in buf.mats("buildings_low"))
    # an authored set keeps the facade its review approved: no rule front
    _, rep2 = _build(_b(PAVILION, w=24.0, d=10.0, ovr={"wall_material": "plaster_beige"}))
    assert rep2["subtypes"] == {"pawilon": 1} and rep2["pavilion_fronts"] == 0
    # too low for a glazed run under the fascia
    assert TY.pavilion_front("plaster_white", (0.0, -1.0), 2.9) is None
    spec = TY.pavilion_front("plaster_white", (0.0, -1.0), 4.4)
    assert spec["glazing"][0]["facing"] == "S" and spec["fascia"]["facings"] == ["S"]


def test_pavilion_costs_no_more_than_the_office_facade():
    pav, _ = _build(_b(PAVILION, w=24.0, d=10.0))
    off, _ = _build(_b(PAVILION, w=24.0, d=10.0, ovr={"typology": "office"}))
    assert pav.tris("buildings") <= off.tris("buildings") and pav.tris("buildings_low") <= off.tris("buildings_low")


def test_house_roof_follows_override_and_osm_shape():
    flat, rep = _build(_b({**HOUSE, "roof_shape_osm": "flat"}, w=11.0, d=9.0))
    assert rep["house_roofs"] == {"flat": 1} and "roof_membrane" in flat.mats("buildings")
    _, rep = _build(_b({**HOUSE, "roof_type_lod2": "1030"}, w=11.0, d=9.0, ovr={"roof_shape": "hip"}))
    assert list(rep["house_roofs"]) == ["hip:lod1"]
    _, rep = _build(_b({**HOUSE, "roof_type_lod2": "1000"}, w=11.0, d=9.0, ovr={"roof_shape": "gable"}))
    assert list(rep["house_roofs"])[0].startswith("gable")
    _, rep = _build(_b({**HOUSE, "roof_shape_osm": "skillion"}, w=11.0, d=9.0))
    assert list(rep["house_roofs"]) == ["mono:lod1"]


def test_halls_sheds_and_plain_types_build():
    buf, rep = _build(_b(HALL, w=60.0, d=30.0, bid="t:h"), _b(SHED, w=6.0, d=5.0, bid="t:s"), _b(OFFICE, bid="t:o"),
                      _b(BLOCK, w=48.0, d=12.0, bid="t:b"))
    assert rep["subtypes"] == {"biurowiec": 1, "gospodarczy": 1, "hala": 1, "wielka_plyta": 1}
    assert rep["roofs_other"] == {} and rep["pavilion_fronts"] == 0
    assert {"roof_membrane"} <= buf.mats("buildings") and "showroom_glass" not in buf.mats("buildings")


# ------------------------------------------------------------------------------------------- data in git
SUBTYPES = {
    "bialystok-industrial-c": {"biurowiec": 67, "dom": 270, "gospodarczy": 121, "hala": 78, "kamienica": 1,
                               "pawilon": 43, "wiata": 14, "wielka_plyta": 50},
    "bialystok-dojlidy": {"biurowiec": 90, "dom": 172, "gospodarczy": 76, "hala": 41, "pawilon": 21, "wiata": 3,
                          "wielka_plyta": 12},
}


@pytest.mark.parametrize("rid", sorted(REGIONS))
def test_subtype_distribution_of_the_regions(rid):
    from streetscape import typology as TY
    _, blds = _load(rid)
    cnt, cls = {}, {}
    for b in blds:
        cnt[b["sub"]] = cnt.get(b["sub"], 0) + 1
        cls[b["typ"]] = cls.get(b["typ"], 0) + 1
        assert TY.SUBTYPES[b["sub"]] == b["typ"]
    assert cnt == SUBTYPES[rid]
    # the render classes are those of the committed build (heroes are counted apart there)
    qa = json.loads((REPO / "Data" / "Regions" / rid / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    old = dict(qa["buildings"]["typologies"])
    hero = old.pop("hero_asset", 0)
    assert sum(cls.values()) == sum(old.values()) + hero
    assert {k: cls[k] for k in ("block", "house", "office", "roof")} == {k: old[k] for k in ("block", "house", "office", "roof")}


@pytest.fixture(scope="module", params=sorted(REGIONS))
def budget(request):
    import typology_budget as TB
    rid = request.param
    base = json.loads((DATA / f"typology_0238_baseline_{rid}.json").read_text(encoding="utf-8"))
    res, man = TB.build(rid)
    return rid, base, res, TB.cameras(rid, man, res["per_chunk"], base["per_chunk"])


def test_triangle_budget_is_not_above_the_baseline(budget):
    rid, base, res, cams = budget
    for layer in ("buildings", "buildings_low"):
        assert res["total"][layer] <= base["total"][layer], (rid, layer)
        assert res["materials"][layer] <= base["materials"][layer], (rid, layer)
    assert cams and all(c["delta_high"] <= 0 and c["delta_low"] <= 0 for c in cams), [
        (c["camera"], c["delta_high"], c["delta_low"]) for c in cams if c["delta_high"] > 0 or c["delta_low"] > 0]
    # The estimate is the committed frame_estimate (read from generated/streetscape_qa.json at test time - never a
    # number copied from another world state) + the harness delta, so it must not exceed the QA and must keep the
    # 2 M High per-frame limit of tile C (docs/06 §6, ADR 0221).
    qa = json.loads((REPO / "Data" / "Regions" / rid / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    fe = {f["camera"]: f for f in qa["mesh_budget"]["frame_estimate"]}
    for c in cams:
        if "est_tris_high" in c:
            assert c["qa_tris_high"] == fe[c["camera"]]["tris_high"], c["camera"]
            assert c["est_tris_high"] <= c["qa_tris_high"] and c["est_tris_low"] <= c["qa_tris_low"], c["camera"]
    if rid == "bialystok-industrial-c":
        s4 = next(c for c in cams if c["camera"] == "stretch_04")
        assert s4["est_tris_high"] <= C_TRIS_HIGH_LIMIT, s4
        assert all(c["est_tris_high"] <= C_TRIS_HIGH_LIMIT for c in cams if "est_tris_high" in c), [
            (c["camera"], c["est_tris_high"]) for c in cams if c.get("est_tris_high", 0) > C_TRIS_HIGH_LIMIT]


def test_authored_and_untouched_buildings_are_bit_identical(budget):
    """Regression of ADR 0184 / 0185 / 0190 / 0196 and every other authored facade: a building with an override set,
    every hall, house, shed and canopy has the same triangles per (layer, material) as before; flat-roofed blocks keep
    their triangle counts (only the hashed wall colour may differ)."""
    rid, base, res, _ = budget
    _, blds = _load(rid)
    seen = set()
    n_same = n_block = 0
    for b in blds:
        k = b["id"].split("#")[0]
        if k in seen or k not in base["per_building"]:
            continue
        seen.add(k)
        old, new = base["per_building"][k], res["per_building"].get(k)
        if b["ovr"] or b["typ"] in ("hall", "house", "shed", "roof"):
            assert new == old, (rid, k, b["typ"], b["sub"])
            n_same += 1
        elif b["sub"] == "wielka_plyta":
            assert new[:2] == old[:2], (rid, k)
            n_block += 1
    assert n_same > 250 and n_block >= 10
    assert set(res["per_building"]) == set(base["per_building"])


# Houses whose triangle counts differed between the Windows build of the lead and Linux CI (main 8401944b6: 18 in
# Dojlidy, 43 in C, all `dom`, only roof / soffit / wall pieces). Before the PLAN_TOL_M clean-up of roofs.py a 1e-9 m
# translation of the footprint changed their counts (60 of those 61; 51 of 415 buildings in Dojlidy, 74 of 644 in C).
UNSTABLE_HOUSES = {
    "bialystok-dojlidy": ["bdot:2BE4B431-98D2-1BF0-E053-CC2BA8C0D140", "bdot:2BE4B431-994A-1BF0-E053-CC2BA8C0D140",
                          "bdot:2BE4B431-9ACC-1BF0-E053-CC2BA8C0D140", "bdot:2BE4B431-A7F1-1BF0-E053-CC2BA8C0D140",
                          "bdot:2BE4B431-98CA-1BF0-E053-CC2BA8C0D140"],
    "bialystok-industrial-c": ["bdot:2BE4B431-AC0F-1BF0-E053-CC2BA8C0D140", "bdot:2BE4B431-AD82-1BF0-E053-CC2BA8C0D140",
                               "bdot:2BE4B431-B46E-1BF0-E053-CC2BA8C0D140",
                               # D32 r2: CI (Linux) != cloud (Linux): attic window on a 130.65 m eave, envelope sliver
                               "bdot:2BE4B431-B14F-1BF0-E053-CC2BA8C0D140", "bdot:2BE4B431-B45E-1BF0-E053-CC2BA8C0D140"],
}


@pytest.mark.parametrize("rid", sorted(UNSTABLE_HOUSES))
def test_house_triangles_do_not_depend_on_float_noise(rid):
    """ADR 0238 (dopisek D32): the roof covering pieces and the wall profiles of a house are cleaned on a 1 mm plan
    grid (roofs.PLAN_TOL_M), so the per-(layer, material) triangle counts do not change when the footprint moves by
    1e-9 / 1e-7 m - the size of the floating-point differences between machines that broke the bit-identity test."""
    import typology_budget as TB
    from shapely import affinity
    from streetscape import buildings_mesh as BM
    fc, ov, man, origin, roads_poly, yard = TB.region_inputs(rid)
    blds = BM.load(fc, origin, ov)
    hf = SimpleNamespace(sample=TB.ground(blds))

    def counts(b, dx):
        buf, rep = TB.Buf(), {}
        BM.build(buf, [dict(b, poly=affinity.translate(b["poly"], dx, 0.7 * dx))], hf, hf.sample, yard, roads_poly,
                 rep, sign_out=[])
        out = {}
        for layer, mat, V, T, src in buf.parts:
            if layer in TB.LAYERS:
                out[(layer, mat)] = out.get((layer, mat), 0) + len(T)
        return out
    for k in UNSTABLE_HOUSES[rid]:
        b = next(x for x in blds if x["id"] == k)
        assert b["typ"] == "house"
        c0 = counts(b, 0.0)
        assert c0 and all(counts(b, dx) == c0 for dx in (1e-12, 1e-9, 1e-7)), (rid, k)


# ------------------------------------------------------------------------------------------- buildings.py
def test_base_m_is_the_measured_median():
    import buildings as B
    rows = {}
    for p in sorted(glob.glob(str(REPO / "Data" / "Regions" / "*" / "buildings.geojson"))):
        for f in json.loads(Path(p).read_text(encoding="utf-8"))["features"]:
            pr = f["properties"]
            if pr.get("height_lod1_2024_m") and pr.get("storeys") and pr["footprint_source"] == "bdot10k":
                rows[f["id"]] = (pr["storeys"], pr["height_lod1_2024_m"])
    n, h = np.array(list(rows.values()), float).T
    assert len(n) >= 8000
    res = h - n * B.STOREY_M
    assert B.BASE_M == 1.5 and abs(float(np.median(res)) - B.BASE_M) < 0.1
    mae = lambda base: float(np.mean(np.abs(res - base)))
    assert mae(B.BASE_M) < mae(1.0) and mae(B.BASE_M) < mae(2.0)


def test_merge_joins_osm_tags_and_uses_the_allowance():
    import geopandas as gpd
    import buildings as B
    bdot = gpd.GeoDataFrame({"LOKALNYID": ["A", "B"], "LICZBAKONDYGNACJI": [2.0, float("nan")],
                             "PRZEWAZAJACAFUNKCJABUDYNKU": ["budynek jednorodzinny", "obiekt handlowo-usługowy"],
                             "NAZWA": [None, None], "KATEGORIAISTNIENIA": [None, None]},
                            geometry=[box(0, 0, 10, 8), box(30, 0, 50, 10)])
    osm = gpd.GeoDataFrame({"osm_type": ["way", "way", "way"], "osm_id": [1, 2, 3], "building": ["yes", "retail", "house"],
                            "levels": [None, None, "1"], "height": [None, None, None], "name": [None, None, None],
                            "roof_shape": ["hipped", None, "gabled"]},
                           geometry=[box(0.2, 0.1, 9.8, 7.9), box(30, 0, 50, 10), box(100, 0, 110, 8)])
    feats = {f["id"]: f for f in B.merge(bdot, {}, {}, osm, (-10, -10, 200, 50))}
    a, b, c = feats["bdot:A"], feats["bdot:B"], feats["osm:way/3"]
    assert a["height_m"] == 2 * B.STOREY_M + B.BASE_M == 7.5 and a["height_source"] == "bdot10k_storeys"
    assert a["roof_shape_osm"] == "hipped" and "osm_building" not in a                   # building=yes says nothing
    assert b["osm_building"] == "retail" and "roof_shape_osm" not in b
    assert c["roof_shape_osm"] == "gabled" and c["height_m"] == 1 * B.STOREY_M + B.BASE_M
    assert len(feats) == 3                                                               # covered OSM buildings not added
