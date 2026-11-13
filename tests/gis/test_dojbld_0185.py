"""ADR 0185 - Dojlidy building follow-ups of review 0179: merged override sets, authored storeys / hall_windows,
the opt-in LoD1 base datum rule, the west wing of the plant hall, the new cladding sets and materials.

Region C has none of the new keys, so its output cannot change (asserted on the data, like test_dojlidy_0179)."""
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

DOJ = REPO / "Data" / "Regions" / "bialystok-dojlidy"
C = REPO / "Data" / "Regions" / "bialystok-industrial-c"
ROSTI = "bdot:2BE4B431-BC59-1BF0-E053-CC2BA8C0D140"


def _ov(d):
    return (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])


def _targets(ov):
    return [o["target"]["building"] for o in ov if isinstance(o.get("target"), dict) and o["target"].get("building")]


def test_region_c_cannot_change():
    ov = _ov(C)
    t = _targets(ov)
    assert len(t) == len(set(t))                                  # no building targeted twice: merged == last one
    assert not any(x.startswith("override:") for x in t)
    assert not [o["id"] for o in ov if o.get("kind") == "building_rules"]
    sets = [o.get("set") or {} for o in ov]
    assert not any("hall_windows" in s or "storeys" in s or "hall_sign" in s for s in sets)
    assert not any(s.get("wall_material") in ("hall_wall_smooth", "cladding_vertical_grey") for s in sets)
    assert not any(o.get("kind") == "building_part" for o in ov)  # so no ground_z_evrf2007 of a part either


def test_sets_of_one_building_are_merged_in_file_order():
    from streetscape import buildings_mesh as BM
    ov = [{"id": "a", "target": {"building": "b1"}, "set": {"wall_material": "x", "hall_bands": False}},
          {"id": "b", "target": {"building": "b1"}, "set": {"wall_material": "y", "hall_windows": False}},
          {"id": "c", "target": {"building": "b2"}, "set": {"wall_material": "z"}}, {"id": "d", "kind": "life_rules"}]
    assert BM.target_sets(ov) == {"b1": {"wall_material": "y", "hall_bands": False, "hall_windows": False},
                                  "b2": {"wall_material": "z"}}
    assert BM.target_sets(ov[2:]) == {"b2": {"wall_material": "z"}}


def test_lod1_base_datum_is_opt_in_and_bounded():
    from streetscape import buildings_mesh as BM
    assert BM.lod1_base_datum([]) is False and BM.lod1_base_datum([{"id": "x", "kind": "life_rules"}]) is False
    assert BM.lod1_base_datum([{"id": "x", "kind": "building_rules", "lod1_base_datum": True}])
    p = {"height_m": 18.92, "ground_z_evrf2007": 152.06, "height_source": "gugik_lod1_2024"}
    assert BM.roof_height({"props": p}, 153.89) == 18.92                              # rule off: as before
    assert BM.roof_height({"props": p, "lod1_datum": True}, 153.89) == pytest.approx(17.09)
    assert BM.roof_height({"props": {**p, "ground_z_evrf2007": None}, "lod1_datum": True}, 153.89) == 18.92
    assert BM.roof_height({"props": {**p, "height_source": "osm_levels"}, "lod1_datum": True}, 153.89) == 18.92
    assert BM.roof_height({"props": p, "lod1_datum": True}, 175.0) == pytest.approx(0.6 * 18.92)   # never below 60 %
    assert BM.roof_height({"props": {}}, 100.0) == 6.0


def test_hall_windows_key_drops_the_hashed_row():
    from streetscape import buildings_mesh as BM
    keys = [f"k{i}" for i in range(40)]
    with_row = [k for k in keys if any(o[5] == "window" for o in BM.facade_openings("hall", 60.0, 0.0, 12.0, 1, k, False, False, {}))]
    assert with_row                                                                    # the rule draws it on ~55 %
    for k in with_row:
        ops = BM.facade_openings("hall", 60.0, 0.0, 12.0, 1, k, False, False, {"hall_windows": False})
        assert not any(o[5] == "window" for o in ops)


def test_dojlidy_buildings_after_overrides():
    from streetscape import buildings_mesh as BM
    fc = json.loads((DOJ / "buildings.geojson").read_text(encoding="utf-8"))
    blds = {b["id"]: b for b in BM.load(fc, (780043.0, 590079.0), _ov(DOJ))}
    hall, wing, k3 = blds[ROSTI], blds["override:rosti-west-wing"], blds["override:kuronia3-office-block"]
    # the main hall keeps the BDOT10k id (one piece) and both sets (0179 colour entry + 0185 cladding entry)
    assert not [i for i in blds if i.startswith(ROSTI + "#cut")]
    assert hall["ovr"] == {"wall_material": "hall_wall_smooth", "hall_bands": False, "hall_windows": False,
                           "hall_sign": False}
    assert hall["poly"].intersection(wing["poly"]).area < 0.5
    assert wing["poly"].area == pytest.approx(3234, rel=0.02) and wing["typ"] == "hall"
    # wing roof 5.5 m under the hall roof (LoD1 base 152.06 + 18.92 / + 13.4)
    assert BM.roof_height(hall, 152.06) - BM.roof_height(wing, 152.06) == pytest.approx(5.52, abs=0.01)
    # north wall of the tall hall: 83.4 m of the outline minus the 13.8 m wing
    from shapely.geometry import LineString
    north = LineString([(747.2, 356.6), (683.3, 384.1)])
    assert hall["poly"].exterior.intersection(north.buffer(0.3)).length == pytest.approx(69.6, abs=1.0)
    assert k3["typ"] == "office" and k3["props"]["storeys"] == 3 and k3["ovr"]["wall_material"] == "cladding_vertical_grey"
    assert BM.storey_plan("office", 14.0, k3["props"])[0] == 3
    from streetscape import frontage as FR
    rules = FR.facade_rules(k3["ovr"]["facades"], k3["ovr"]["wall_material"])
    assert [r["windows"] for r in rules] == ["column", "ribbon", "blank"]
    assert FR.facade_rule(rules, [-1.0, 0.0], 12.6)["windows"] == "column"             # west gable
    assert FR.facade_rule(rules, [0.0, -1.0], 46.8)["windows"] == "ribbon"             # long south wall
    assert FR.facade_rule(rules, [0.0, 1.0], 5.6)["windows"] == "blank"


def test_materials_and_sets():
    from streetscape import materials as MT
    spec = json.loads((REPO / "art-source/world/materials/materials_spec.json").read_text(encoding="utf-8"))["sets"]
    for mat, st in (("hall_wall_smooth", "sandwich_smooth"), ("cladding_vertical_grey", "cladding_vertical")):
        m = MT.M[mat]
        assert m["texture_set"] == st and m["set_tile"] and m["tint_linear"] and st in spec
        assert spec[st]["files"]["High"]["res"] == [1024, 1024]                        # a quarter of a 2048 set
    assert MT.M["hall_wall_smooth"]["panel_m"] == [6.0, 1.15] and spec["sandwich_smooth"]["tile_m"] == [3.45, 3.45]
    for k in ("office", "ribbon"):
        assert MT.M[f"cladding_vertical_grey__far_{k}"]["base"] == "cladding_vertical_grey"
    assert "hall_wall_smooth" not in sys.modules["streetscape.buildings_mesh"].HALL_WALLS   # never a hashed pick


def test_fence_mesh_mips_do_not_preserve_coverage():
    src = (REPO / "game/Assets/_Project/World/Import/InstanceImporter.cs").read_text(encoding="utf-8")
    assert 'ti.mipMapsPreserveCoverage = alpha && !file.StartsWith("fence_");' in src
