"""ADR 0242 - Dojlidy recognisability follow-ups of reviews s20-0185 / s20-0196: heights of the three plants from the
GUGiK NMPT 0.5 m surface model, cassette cladding of Kuronia 3, per-material run-off strength, hall doors / gates on
the ground under them (opt-in per region), bigger gates of the north hall.

Region C has none of the new keys / materials, so its output cannot change (asserted on the data)."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

REGIONS = REPO / "Data" / "Regions"
DOJ = REGIONS / "bialystok-dojlidy"
ORIGIN = (780043.0, 590079.0)
ROSTI = "bdot:2BE4B431-BC59-1BF0-E053-CC2BA8C0D140"
K2 = "bdot:941cfc23-bd8b-40d5-a49b-d1bba751d5bd"


def _ov(d):
    return (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])


def _blds():
    from streetscape import buildings_mesh as BM
    fc = json.loads((DOJ / "buildings.geojson").read_text(encoding="utf-8"))
    return {b["id"]: b for b in BM.load(fc, ORIGIN, _ov(DOJ))}


def test_new_rules_are_opt_in_and_no_other_region_uses_them():
    from streetscape import buildings_mesh as BM
    assert BM.hall_openings_at_ground([]) is False
    assert BM.hall_openings_at_ground([{"id": "x", "kind": "building_rules", "lod1_base_datum": True}]) is False
    assert BM.hall_openings_at_ground([{"id": "x", "kind": "building_rules", "hall_openings_at_ground": True}])
    users = []
    for d in sorted(p for p in REGIONS.iterdir() if (p / "overrides.yaml").exists()):
        txt = (d / "overrides.yaml").read_text(encoding="utf-8")
        if any(k in txt for k in ("hall_openings_at_ground", "storeys_fixed", "cladding_cassette_grey")):
            users.append(d.name)
    assert users == ["bialystok-dojlidy"]
    # a region without the rule: load() sets no flag, so build() never calls openings_to_ground
    fc = {"features": [{"id": "b1", "properties": {"height_m": 8.0, "function": "produkcyjny"},
                        "geometry": {"coordinates": [[[[0, 0], [60, 0], [60, 30], [0, 30], [0, 0]]]]}}]}
    assert "hall_openings_ground" not in BM.load(fc, (0.0, 0.0), [])[0]
    assert BM.load(fc, (0.0, 0.0), [{"id": "r", "kind": "building_rules", "hall_openings_at_ground": True}])[0][
        "hall_openings_ground"] is True


def test_storey_plan_without_the_key_is_unchanged():
    from streetscape import buildings_mesh as BM
    for h in (9.0, 12.0, 14.0, 15.4, 22.0):
        for nb in (None, 2, 3, 4, 6):
            assert BM.storey_plan("office", h, {"storeys": nb}) == BM.storey_plan("office", h, {"storeys": nb,
                                                                                               "storeys_fixed": False})
    assert BM.storey_plan("office", 15.4, {"storeys": 3})[0] == 4                 # the rule: 4.77 m is over 4.6 m
    n, sh, zb = BM.storey_plan("office", 15.4, {"storeys": 3, "storeys_fixed": True})
    assert n == 3 and sh == pytest.approx((15.4 - zb - 0.8) / 3) and 4.6 < sh < 4.9


def test_openings_to_ground():
    from streetscape import buildings_mesh as BM
    ground = lambda u: 152.4 + 0.01 * u                                   # low side of a sloping plot, zref 153.9
    ops = [(10.0, 11.0, 154.05, 156.15, 0.08, "door", ("atlas", 1)),      # personnel door at zref + 0.15
           (20.0, 24.0, 153.92, 158.42, 0.2, "door", "garage_door"),
           (40.0, 45.9, 153.92, 160.52, 0.2, "gate", "dock_door"),
           (50.0, 52.0, 157.1, 158.1, 0.12, "window", ("hallw", 0)),
           (60.0, 63.0, 155.0, 158.0, 0.25, "dock", "dock_door")]
    out = BM.openings_to_ground(ops, ground, 171.0)
    assert out[3:] == ops[3:]                                             # windows and docks untouched
    assert out[0][2] == pytest.approx(152.4 + 0.11 + 0.15) and out[0][3] - out[0][2] == pytest.approx(2.1)
    assert out[1][2] == pytest.approx(152.4 + 0.24 + 0.02) and out[1][3] - out[1][2] == pytest.approx(4.5)
    assert out[2][2] == pytest.approx(152.4 + 0.459 + 0.02) and out[2][3] - out[2][2] == pytest.approx(6.6)
    assert [o[:2] + o[4:] for o in out] == [o[:2] + o[4:] for o in ops]   # u range, depth, kind, infill kept
    # sill never under the ground at either jamb; before: 1.2-1.7 m above it (review s20-0185 P1-5)
    for o in out[:3]:
        assert 0.0 <= o[2] - max(ground(o[0]), ground(o[1])) <= 0.16
    # high side: the door is lifted out of the ground; a low wall cuts the gate, never under 2 m
    assert BM.openings_to_ground(ops[:1], lambda u: 155.0, 171.0)[0][2] == pytest.approx(155.15)
    cut = BM.openings_to_ground(ops[2:3], ground, 157.0)[0]
    assert cut[3] == pytest.approx(156.4) and cut[3] - cut[2] >= 2.0
    assert BM.openings_to_ground(ops[2:3], ground, 154.5) == ops[2:3]


def test_heights_follow_the_surface_model():
    """Roof level = level the height is measured from + height; the expected levels are the NMPT 0.5 m values printed
    by tools/worldgen/qa/dsm_roof_levels.py (2026-11-15), +-0.6 m."""
    from streetscape import buildings_mesh as BM
    blds = _blds()
    ov = {o["id"]: o for o in _ov(DOJ)}
    top = lambda b: b["props"]["ground_z_evrf2007"] + b["props"]["height_m"]
    assert all(b.get("lod1_datum") for b in blds.values())
    assert "height_m" not in blds[ROSTI]["ovr"] and blds[ROSTI]["props"]["height_m"] == pytest.approx(18.92)
    assert top(blds[ROSTI]) == pytest.approx(171.1, abs=0.3)               # roof along the north wall 171.04-171.16
    dsm = {"override:rosti-west-wing": 165.25, "override:kuronia3-office-block": 169.46,
           "override:kuronia2-front-bay": 167.45, "override:kuronia2-office-wing": 167.43,
           "override:kuronia2-street-annex": 162.47, K2: 168.07}
    for k, z in dsm.items():
        assert top(blds[k]) == pytest.approx(z, abs=0.15), k
    for k in ("override:kuronia2-corner-portal", "override:kuronia2-front-portal"):
        assert 167.5 <= top(blds[k]) <= 168.75                             # roof .. highest parapet sample
    # review s20-0196 P1: the hall no longer towers over the front - its wall top is within 0.7 m of the front
    # blocks (r4: about 2.4 m above them) and the street annex is the lowest part
    hall, block, wing, annex = (top(blds[k]) for k in (K2, "override:kuronia2-corner-portal",
                                                      "override:kuronia2-office-wing", "override:kuronia2-street-annex"))
    assert abs(hall - block) < 0.7 and wing < block and annex < wing - 4.0
    # with the datum rule the roof level does not depend on the ground the generator samples
    for zref in (156.5, 157.5, 158.5):
        assert zref + BM.roof_height(blds["override:kuronia2-office-wing"], zref) == pytest.approx(167.45)
    for i in ("kuronia2-main-hall", "rosti-hall-cladding", "rosti-west-wing", "kuronia3-office-block"):
        assert "ADR 0242" in (DOJ / "overrides.yaml").read_text(encoding="utf-8").split(f"- id: {i}\n")[1].split("  - id: ")[0], i
    assert ov["rosti-north-wall-gates"]["gates"][0]["height_m"] == 6.6


def test_kuronia3_cassette_and_three_storeys():
    from streetscape import buildings_mesh as BM
    from streetscape import frontage as FR
    from streetscape import materials as MT
    k3 = _blds()["override:kuronia3-office-block"]
    assert k3["ovr"]["wall_material"] == "cladding_cassette_grey" and k3["props"]["storeys_fixed"] is True
    h = 15.4
    n, sh, zb = BM.storey_plan("office", h, k3["props"])
    rule = FR.facade_rule(FR.facade_rules(k3["ovr"]["facades"], k3["ovr"]["wall_material"]), [0.0, -1.0], 46.8)
    wins = FR.facade_windows(rule, 46.8, 0.0, zb, sh, h, n, "k")
    sills = sorted({round(w[2] / h, 2) for w in wins})
    assert n == 3 and len(sills) == 3
    assert sills == pytest.approx([0.19, 0.50, 0.81], abs=0.02)            # photo proportions of ADR 0185
    m = MT.M["cladding_cassette_grey"]
    spec = json.loads((REPO / "art-source/world/materials/materials_spec.json").read_text(encoding="utf-8"))["sets"]
    assert m["texture_set"] == "sandwich_smooth" and m["texture_set"] in spec          # no new texture set
    assert m["panel_m"][0] > 2 * m["panel_m"][1]                                       # horizontal joints dominate
    assert m["color"] == MT.M["cladding_vertical_grey"]["color"] and m["runoff"] and m["set_tile"]
    for k in ("office", "ribbon"):
        assert MT.M[f"cladding_cassette_grey__far_{k}"]["base"] == "cladding_cassette_grey"
        assert MT.M[f"cladding_cassette_grey__far_{k}"]["texture_set"] == "facade_far"


def test_runoff_strength_is_per_material():
    from streetscape import materials as MT
    with_key = {k for k, m in MT.M.items() if "runoff_strength" in m}
    assert with_key == {"hall_wall_smooth", "cladding_cassette_grey"}
    assert MT.M["hall_wall_smooth"]["runoff_strength"] == 0.25
    src = (REPO / "game/Assets/_Project/World/Import/WorldPbrMaterials.cs").read_text(encoding="utf-8")
    assert 'def.Get("runoff_strength")' in src and "* RunoffStrengthScale(def));" in src
    c_manifest = json.loads((REGIONS / "bialystok-industrial-c/generated/world_manifest.json").read_text(encoding="utf-8"))
    # the manifest lists every material of the generator; region C draws neither of the two in any chunk, so its
    # meshes and looks cannot change (the dictionary gains the unused entries at the next regeneration, as in 0185)
    drawn = {m for ch in c_manifest["chunks"] for m in ch["materials"]}
    assert not {k for k in drawn if k.startswith(("hall_wall_smooth", "cladding_cassette_grey"))}


def test_kuronia2_front_frame_and_ground_floor():
    from streetscape import frontage as FR
    from streetscape import materials as MT
    blds = _blds()
    lum = lambda k: float(np.dot([0.2126, 0.7152, 0.0722], MT.M[k]["color"]))
    for k in ("override:kuronia2-corner-portal", "override:kuronia2-front-portal"):
        fr = FR.plan(blds[k]["ovr"]["frontage"], MT.M)
        mats = {fr["fascia"]["material"], *[a["material"] for a in fr["accents"]]}
        assert mats == {"plaster_accent_grey"}                             # one material, already drawn by the parts
        assert 1.5 < lum("plaster_accent_grey") / lum(blds[K2]["ovr"]["wall_material"]) < 3.0   # photo ~1.8, frame lighter
    for k in [k for k in blds if k.startswith("override:kuronia2-")]:
        fr = FR.plan(blds[k]["ovr"]["frontage"], MT.M)
        ground = [a for a in fr["accents"] if a["z"][0] == 0.3]
        assert len(ground) == 1 and ground[0]["min_len_m"] == 0.0 and ground[0]["span"] == (0.0, 1.0)
        assert ground[0]["z"][1] < blds[k]["props"]["height_m"] - 2.0      # a light band stays above it


def test_dsm_tool_parses_a_wcs_reply():
    sys.path.insert(0, str(REPO / "tools" / "worldgen" / "qa"))
    import dsm_roof_levels as D
    from shapely.geometry import box
    rows = ["100 100 100 100 100 100", "100 110 110 110 110 100", "100 110 110 110 110 100", "100 100 100 100 100 100"]
    raw = ("\r\n--wcs\nContent-Type: image/x-aaigrid\n\nncols 6\nnrows 4\nxllcorner 10\nyllcorner 20\ncellsize 2\n"
           + "\n".join(rows) + "\n--wcs--\n").encode()
    hdr, grid = D.parse_aaigrid(raw)
    assert hdr == {"ncols": 6.0, "nrows": 4.0, "xllcorner": 10.0, "yllcorner": 20.0, "cellsize": 2.0}
    assert grid.shape == (4, 6) and grid[1, 1] == 110.0
    st = D.ring_stats(np.kron(grid, np.ones((4, 4), np.float32)), {**hdr, "cellsize": 0.5}, box(12.0, 22.0, 20.0, 26.0))
    assert st["roof_p50"] == 110.0 and st["ground_p10"] == 100.0
