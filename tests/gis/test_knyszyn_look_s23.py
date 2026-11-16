"""knyszyn-look-s23: roof tones read off the orthophoto (generated override file), house wall / wooden overrides,
landmark overrides of Knyszyn outside the Rynek park."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest

from roads import pipeline
from streetscape import buildings_mesh as BM
from streetscape import facade_kit as FK
from streetscape import materials as MT
from test_buildings_0167 import _build

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools/worldgen/qa"))
import roof_tones_ortho as RT  # noqa: E402

R = ROOT / "Data/Regions/knyszyn"
ORIGIN = (761611.0, 612607.0)
POST = "bdot:2002917F-AB81-5C99-E053-CC2BA8C01CFC"
KLATT = "bdot:2002917F-2F22-5C99-E053-CC2BA8C01CFC"
CORNER = "bdot:2002917F-2E17-5C99-E053-CC2BA8C01CFC"
LIBRARY = "bdot:2002917F-46DA-5C99-E053-CC2BA8C01CFC"
STORE = "bdot:2002917F-468D-5C99-E053-CC2BA8C01CFC"


@pytest.fixture(scope="module")
def blds():
    fc = json.loads((R / "buildings.geojson").read_text(encoding="utf8"))
    return {b["id"]: b for b in BM.load(fc, ORIGIN, pipeline.load_overrides("knyszyn"))}


def _mats(b, layer="buildings"):
    return {p.mat for p in _build(b).parts if p.layer == layer}


def test_classifier_reads_reference_tones():
    # median sRGB of the four hand-read Rynek roofs (ADR 0227) and of the discount store, measured on the 2025 sheet
    got = list(RT.classify_rgb(np.array([[68, 84, 96], [154, 116, 96], [104, 135, 152], [168, 101, 92], [172, 98, 97],
                                         [176, 180, 184], [60, 160, 60]])))
    assert got == ["graphite", "red", "graphite", "red", "red", "light_grey", ""]
    assert set(RT.MATERIAL.values()) <= BM.ROOF_OVERRIDES


def test_generated_file_is_consistent_and_authored_wins():
    gen = json.loads((R / "overrides.ortho_roofs.json").read_text(encoding="utf8"))
    ovs = gen["overrides"]
    assert len(ovs) == gen["summary"]["kept"] > 1000
    assert len({o["target"]["building"] for o in ovs}) == len(ovs)
    assert {o["set"]["roof_material"] for o in ovs} <= BM.ROOF_OVERRIDES
    assert all(set(o["set"]) <= BM.OVR_ROOF_ONLY and o["reason"] and o["confidence"] for o in ovs)
    allo = pipeline.load_overrides("knyszyn")
    fixes = json.loads((R / "overrides.class_fixes.json").read_text(encoding="utf8"))["overrides"]
    assert allo[:len(fixes) + len(ovs)] == fixes + ovs       # generated first, hand-authored after = authored wins
    assert not any(str(o.get("id", "")).startswith(("roof-ortho:", "class-fix:")) for o in allo[len(fixes) + len(ovs):])
    sets = BM.target_sets(allo)
    by = {o["target"]["building"]: o["set"]["roof_material"] for o in ovs}
    for bid, cls in RT.CHECK.items():                  # the classifier agrees with the hand-read roofs
        assert by[bid] == RT.MATERIAL[cls] == sets[bid]["roof_material"]
    fc = json.loads((R / "buildings.geojson").read_text(encoding="utf8"))
    assert set(by) <= {f["id"] for f in fc["features"]}      # no stale target


def test_regions_without_the_file_are_untouched():
    assert pipeline.generated_overrides("bialystok-industrial-c") == []
    assert not (ROOT / "Data/Regions/bialystok-industrial-c/overrides.ortho_roofs.json").exists()
    assert "roof_sheet_grey" not in {m for m, _ in BM.HOUSE_ROOFS} and "roof_sheet_grey" not in BM.ROOFS_PITCHED


def test_light_grey_sheet_roof_material():
    assert '"roof_sheet_grey"' in Path(MT.__file__).read_text(encoding="utf8")
    assert FK.L1_MAT["roof_sheet_grey"] == "downpipe"            # small LOD1 pieces (canopies) reuse the downpipe grey
    assert BM.house_roof_material({"id": "h", "ovr": {"roof_material": "roof_sheet_grey"}}, "roof_tiles_red") == "roof_sheet_grey"
    with pytest.raises(ValueError, match="unsupported roof_material"):
        BM.house_roof_material({"id": "h", "ovr": {"roof_material": "plaster_white"}}, "roof_tiles_red")


def test_roof_tone_reaches_the_mesh(blds):
    sets = BM.target_sets(pipeline.load_overrides("knyszyn"))
    grey = next(b for i, b in sorted(blds.items()) if b["typ"] == "house" and b["ovr"].get("roof_material") == "roof_sheet_grey"
                and len(b["ovr"]) == 1 and b["poly"].area > 80)
    assert "roof_sheet_grey" in _mats(grey) and "roof_sheet_grey" in _mats(grey, "buildings_low")   # same roof on both LODs
    assert sets[LIBRARY]["roof_material"] == "roof_tiles_red"
    assert blds[LIBRARY]["typ"] != "house" and "roof_tiles_red" in _mats(blds[LIBRARY])     # pitched non-house roof


def test_landmark_overrides(blds):
    assert blds[KLATT]["sub"] == "dom_drewniany" and "wood_planks" in _mats(blds[KLATT])
    assert not {"plaster_light", "plaster_grey", "plaster_beige", "plaster_cream"} & _mats(blds[KLATT])
    assert "plaster_white" in _mats(blds[CORNER])
    assert "plaster_peach" in _mats(blds[POST])
    assert {"roof_tiles_red", "roof_tiles_brown", "roof_metal_graphite", "roof_sheet_grey"} & _mats(blds[POST])   # hipped roof
    assert set(blds[STORE]["ovr"]) <= BM.OVR_ROOF_ONLY          # the rule shopfront of the pavilion survives


def test_class_fixes_from_data(blds):
    gen = json.loads((R / "overrides.class_fixes.json").read_text(encoding="utf8"))
    n = gen["summary"]
    assert (n["osm_only_shed"], n["osm_only_house"], n["pitched_service"]) == (99, 49, 20)
    fc = json.loads((R / "buildings.geojson").read_text(encoding="utf8"))
    plain = {b["id"]: b for b in BM.load(fc, ORIGIN, [])}
    for o in gen["overrides"]:
        bid, s = o["target"]["building"], o["set"]
        assert plain[bid]["typ"] in ("office", "block")
        if "typology" in s:                   # OSM-only footprint with the default height: never an office box
            assert plain[bid]["props"]["height_source"] == "default" and plain[bid]["props"]["footprint_source"] == "osm"
            assert blds[bid]["typ"] == {"gospodarczy": "shed", "dom": "house"}[s["typology"]]
            if s["typology"] == "gospodarczy":
                assert blds[bid]["props"]["height_m"] == 3.0 and plain[bid]["poly"].area < 60
        else:                                 # measured LoD2 rise -> pitched
            assert s["roof_shape"] in ("gable", "mono") and blds[bid]["typ"] == plain[bid]["typ"]
    left = [b for b in blds.values() if b["typ"] == "office" and b["props"].get("height_source") == "default"
            and b["props"].get("function") == "yes" and b["poly"].area < 250]
    assert left == []
    funeral = blds["bdot:2002917F-465F-5C99-E053-CC2BA8C01CFC"]         # LoD2 1130, rise 1.8 m
    assert funeral["ovr"].get("roof_shape") == "gable" and BM.ROOF_OVERRIDES & _mats(funeral)


def test_house_wall_override_is_validated():
    fc = json.loads((R / "buildings.geojson").read_text(encoding="utf8"))
    bad = [{"id": "x", "target": {"building": CORNER}, "set": {"wall_material": "hall_wall_silver"}}]
    b = next(b for b in BM.load(fc, ORIGIN, bad) if b["id"] == CORNER)
    with pytest.raises(ValueError, match="unsupported house wall_material"):
        _build(b)
