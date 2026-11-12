"""Tests for tools/worldgen/validate (M37 world validator).

Each check is tested on a synthetic World: first the clean world yields no findings of that category
(negative control), then the same check with one injected error must catch it (mutation test, requirement B
of M37: "wstrzyknii błąd w kopię danych testowych -> musi być wykryty"). Plus a smoke test on the real
region data (skipped when the committed files are missing).
"""

from __future__ import annotations

import json

import pytest
from shapely.geometry import LineString, Polygon

from conftest import REGION_ID
from validate import buildings, common, continuity, overlaps, report, signs, terrain


def synth_world() -> common.World:
    """One straight 7 m road along N=0 (E -100..100), one building at (15..25, 15..25), one route along the road."""
    w = common.World(region_id="synth", origin=(777995.0, 596223.0))
    w.edges.append({"id": "w1:a-b", "osm_way": 1, "coords": [[-100.0, 0.0], [100.0, 0.0]], "width_m": 7.0,
                    "highway": "primary", "lanes": 2, "bridge": False, "name": "Testowa"})
    w.buildings.append({"id": "bld:1", "poly": Polygon([(15, 15), (25, 15), (25, 25), (15, 25)]),
                        "height_m": 9.0, "storeys": 3, "height_source": "osm_levels", "ground_z": 130.0,
                        "is_roof_only": False, "name": None})
    w.route = [[-100.0, 1.75], [100.0, 1.75]]
    w.manifest = {"chunks": [{"id": "0_0", "file": "Data/raw/derived/synth/world/chunk_0_0.glb",
                              "bounds_local_m": {"e_min": -1024.0, "n_min": -1024.0,
                                                 "e_max": 1024.0, "n_max": 1024.0}}]}
    return w


def cats(fs):
    return {f.category for f in fs}


# ---------------------------------------------------------------- check 1: overlaps (mutation tests)
def test_overlaps_clean_world_is_clean():
    w = synth_world()
    w.points.append({"id": "osm:node/1", "kind": "power_pole", "e": 0.0, "n": 10.0, "tags": {}})
    w.trees.append({"id": "canopy:1", "e": 30.0, "n": 8.0, "r": 2.0, "conifer": False})
    fs = overlaps.check(w)
    assert not (cats(fs) & {"object_in_carriageway", "object_on_kerb", "object_in_object", "tree_in_building",
                            "building_in_carriageway"})


def test_mutation_pole_in_carriageway_detected():
    w = synth_world()
    w.points.append({"id": "osm:node/1", "kind": "power_pole", "e": 0.0, "n": 1.0, "tags": {}})  # inside ribbon
    fs = overlaps.check(w)
    hit = [f for f in fs if f.category == "object_in_carriageway" and f.id == "osm:node/1"]
    assert hit and hit[0].severity == "error" and hit[0].extra["depth_m"] > 2.0


def test_overhead_gantry_board_is_not_in_carriageway():
    """Integration r6: a board on a sign_gantry override hangs over the road (M37 flagged 4 such boards on the
    G3 route as errors); the same sign as a post-mounted sign is still an error."""
    w = synth_world()
    w.overrides = [{"id": "portal-x", "kind": "sign_gantry"}]
    w.signs.append({"id": "override:portal-x", "code": "OB_1", "e": 0.0, "n": 1.0, "faces_route_driver": True,
                    "offset_m": 1.6, "src": "override:portal-x"})
    w.signs.append({"id": "osm:node/7", "code": "B-33_50", "e": 5.0, "n": 1.0, "faces_route_driver": True,
                    "offset_m": 0.0, "src": "osm:node/7"})
    ids = {f.id for f in overlaps.check(w) if f.category == "object_in_carriageway"}
    assert "sign:osm:node/7" in ids
    assert "sign:override:portal-x" not in ids


def test_mutation_object_on_kerb_detected():
    w = synth_world()
    w.points.append({"id": "osm:node/2", "kind": "sign", "e": 0.0, "n": -3.7, "tags": {}})  # 0.2 m outside edge
    fs = overlaps.check(w)
    assert any(f.category == "object_on_kerb" and f.id == "osm:node/2" for f in fs)


def test_mutation_objects_in_each_other_detected():
    w = synth_world()
    w.points.append({"id": "osm:node/1", "kind": "power_pole", "e": 0.0, "n": 10.0, "tags": {}})
    w.points.append({"id": "osm:node/2", "kind": "lamp", "e": 0.2, "n": 10.1, "tags": {}})
    fs = overlaps.check(w)
    assert any(f.category == "object_in_object" for f in fs)


def test_mutation_tree_in_building_detected():
    w = synth_world()
    w.trees.append({"id": "canopy:9", "e": 20.0, "n": 20.0, "r": 2.0, "conifer": False})  # trunk inside bld:1
    fs = overlaps.check(w)
    hit = [f for f in fs if f.category == "tree_in_building" and f.id == "canopy:9"]
    assert hit and hit[0].extra["building"] == "bld:1"


def test_mutation_building_in_carriageway_detected():
    w = synth_world()
    w.buildings.append({"id": "bld:2", "poly": Polygon([(-5, -4), (5, -4), (5, 4), (-5, 4)]),
                        "height_m": 8.0, "storeys": 2, "height_source": "bdot10k_storeys", "ground_z": 130.0,
                        "is_roof_only": False, "name": None})
    fs = overlaps.check(w)
    assert any(f.category == "building_in_carriageway" and f.id == "bld:2" for f in fs)


# ---------------------------------------------------------------- check 2: continuity (mutation tests)
def _fence_world() -> common.World:
    w = synth_world()
    w.lines.append({"id": "osm:way/10:0", "source_id": "osm:way/10", "kind": "fence",
                    "line": LineString([(-50, 8), (-20, 8)])})
    w.lines.append({"id": "osm:way/10:1", "source_id": "osm:way/10", "kind": "fence",
                    "line": LineString([(-19, 8), (10, 8)])})   # 1.0 m gap to the first segment
    return w


def test_continuity_gap_detected():
    fs = continuity.check(_fence_world())
    hit = [f for f in fs if f.category == "suspicious_gap"]
    assert hit and 0.9 < hit[0].extra["gap_m"] < 1.1


def test_continuity_gap_at_bridge_end_excluded():
    w = _fence_world()
    w.edges.append({"id": "w2:c-d", "osm_way": 2, "coords": [[-25, 5], [-15, 5]], "width_m": 8.0,
                    "highway": "primary", "lanes": 2, "bridge": True, "name": " wiadukt"})
    fs = continuity.check(w)
    assert not [f for f in fs if f.category == "suspicious_gap"]   # gap endpoints next to the deck: M29's


def test_mutation_duplicate_parallel_detected():
    w = synth_world()
    w.lines.append({"id": "osm:way/10", "source_id": "osm:way/10", "kind": "fence",
                    "line": LineString([(-50, 8), (50, 8)])})
    w.lines.append({"id": "osm:way/11", "source_id": "osm:way/11", "kind": "fence",
                    "line": LineString([(-50, 8.3), (50, 8.3)])})   # 0.3 m parallel
    fs = continuity.check(w)
    assert any(f.category == "duplicate_parallel" and f.severity == "warn" for f in fs)


# ---------------------------------------------------------------- check 3: terrain (mutation tests)
def test_terrain_clean_world_is_clean():
    w = synth_world()
    w.chains_qa = [{"id": "c:w1:a-b", "profile_rms_vs_nmt_m": 0.05, "max_grade": 0.03, "grade_limit": 0.09,
                    "highway": ["primary"]}]
    w.terrain_walls = {"worst": [{"e": 0, "n": 0, "h": 0.2, "kind": "skirt", "src": "x"}], "verge_strips": {}}
    assert terrain.check(w) == []


def test_mutation_profile_deviation_and_grade_detected():
    w = synth_world()
    w.chains_qa = [{"id": "c:w1:a-b", "profile_rms_vs_nmt_m": 0.9, "max_grade": 0.15, "grade_limit": 0.09,
                    "highway": ["primary"]}]
    fs = terrain.check(w)
    assert any(f.category == "road_profile_deviation" for f in fs)
    assert any(f.category == "road_grade_exceeded" for f in fs)


def test_mutation_terrain_wall_detected():
    w = synth_world()
    w.terrain_walls = {"worst": [{"e": 5.0, "n": 6.0, "h": 0.8, "kind": "skirt", "mat": "verge_grass", "src": "s"}],
                       "verge_strips": {}}
    fs = terrain.check(w)
    assert any(f.category == "terrain_wall" and f.e == 5.0 for f in fs)


def test_terrain_wall_uses_generator_threshold_and_verge_format():
    """Integration r6: ADR 0146 Open lists 4 walls 0.317-0.345 m found by the generator (thresh_m 0.15); the
    verge-strip 'worst' entry is [kind, id, e, n] (4 items) as in terrain_walls_qa.json."""
    w = synth_world()
    w.terrain_walls = {"thresh_m": 0.15,
                       "worst": [{"e": 486.1, "n": -1024.0, "h": 0.317, "kind": "skirt", "mat": "yard_concrete", "src": "a"}],
                       "verge_strips": {"max_m": 0.627, "worst": ["steep_grass", "j:x:vg", -482.0, -461.3]}}
    fs = [f for f in terrain.check(w) if f.category == "terrain_wall"]
    assert {f.e for f in fs} == {486.1, -482.0}


# ---------------------------------------------------------------- check 4: signs (mutation tests)
def test_signs_clean_world_is_clean():
    w = synth_world()
    w.signs.append({"id": "rule:maxspeed:c:w1", "code": "B-33_50", "e": 10.0, "n": 5.0,
                    "faces_route_driver": True, "offset_m": 2.0, "src": "rule:maxspeed:c:w1"})
    fs = signs.check(w)
    assert not (cats(fs) & {"sign_facing_away", "sign_occluded"})
    assert not [f for f in fs if f.category == "sign_height_rule"]  # standards inside the band


def test_mutation_sign_facing_away_detected():
    w = synth_world()
    w.signs.append({"id": "osm:node/99", "code": "D-6", "e": 10.0, "n": 5.0, "faces_route_driver": False,
                    "offset_m": 2.0, "src": "osm:node/99"})
    fs = signs.check(w)
    assert any(f.category == "sign_facing_away" and f.id == "osm:node/99" for f in fs)


def test_mutation_sign_occluded_by_tree_detected():
    w = synth_world()
    w.signs.append({"id": "rule:x", "code": "A-7", "e": 30.0, "n": 6.0, "faces_route_driver": True,
                    "offset_m": 2.0, "src": "rule:x"})
    w.trees.append({"id": "canopy:5", "e": 15.0, "n": 4.0, "r": 3.0, "conifer": True})  # between driver and sign
    fs = signs.check(w)
    hit = [f for f in fs if f.category == "sign_occluded" and f.id == "rule:x"]
    assert hit and hit[0].extra["blocker"].startswith("tree:")


# ---------------------------------------------------------------- extension (c): buildings
def test_mutation_building_checks_detected():
    w = synth_world()
    w.buildings.append({"id": "bld:roof", "poly": Polygon([(30, 30), (36, 30), (36, 36), (30, 36)]),
                        "height_m": 3.0, "storeys": None, "height_source": "default", "ground_z": 130.0,
                        "is_roof_only": True, "name": None})
    w.buildings.append({"id": "bld:tall", "poly": Polygon([(40, 40), (46, 40), (46, 46), (40, 46)]),
                        "height_m": 24.0, "storeys": 3, "height_source": "osm_levels", "ground_z": 130.0,
                        "is_roof_only": False, "name": None})
    fs = buildings.check(w)
    assert any(f.category == "building_roof_only" and f.id == "bld:roof" for f in fs)
    assert any(f.category == "building_height_default" and f.id == "bld:roof" for f in fs)
    assert any(f.category == "building_height_vs_storeys" and f.id == "bld:tall" for f in fs)


# ---------------------------------------------------------------- check 5 + extension (b): report & diff
def test_report_writers_and_diff(tmp_path):
    w = synth_world()
    fs = common.finalize(w, [
        common.Finding("object_in_carriageway", 1.0, 2.0, "osm:node/1", "pole in lane", severity="error"),
        common.Finding("sign_facing_away", 10.0, 5.0, "osm:node/99", "faces away", severity="error"),
        common.Finding("building_roof_only", 30.0, 30.0, "bld:roof", "roof only", severity="info"),
    ])
    report.write_json(w, fs, tmp_path)
    report.write_md(w, fs, tmp_path)
    report.write_html(w, fs, tmp_path)
    report.write_cameras(w, fs, tmp_path, origin_z=131.14)
    doc = json.loads((tmp_path / "world_validator.json").read_text(encoding="utf-8"))
    assert doc["schema"] == report.SCHEMA and doc["summary"]["count"] == 3
    assert all({"e", "n", "lat", "lon", "chunk", "category", "id"} <= set(f) for f in doc["findings"])
    assert doc["findings"][0]["on_route"] is True            # sorted errors first, route distance
    md = (tmp_path / "report.md").read_text(encoding="utf-8")
    assert "object_in_carriageway" in md and "Top 20" in md and "chunk_0_0.glb" in md
    cams = json.loads((tmp_path / "control_cameras.json").read_text(encoding="utf-8"))
    assert cams["cameras"] and all({"pos", "look_at", "fov_deg", "note", "type"} <= set(c)
                                   for c in cams["cameras"])
    # extension (b): diff against a previous run
    prev = {"schema": report.SCHEMA, "summary": {"count": 2, "by_category": {"object_in_carriageway": 2}},
            "findings": [{"category": "object_in_carriageway", "e": 1.0, "n": 2.0, "id": "osm:node/1"},
                         {"category": "object_in_carriageway", "e": 50.0, "n": 2.0, "id": "osm:node/7"}]}
    d = report.diff(prev, doc)
    assert d["new"] == 2 and d["fixed"] == 1 and d["cur_total"] == 3


def test_route_ranking_extension_a():
    w = synth_world()
    fs = common.finalize(w, [common.Finding("object_in_carriageway", 5.0, 2.0, "a", severity="error"),
                             common.Finding("building_roof_only", 900.0, 900.0, "b", severity="info")])
    top = common.route_ranking(fs, band_m=60.0)
    assert len(top) == 1 and top[0]["id"] == "a"     # the far-away info finding is outside the +-60 m band


# ---------------------------------------------------------------- smoke test on the real region
def test_region_run_smoke():
    p = common.REPO_ROOT / "Data" / "Regions" / REGION_ID
    if not (p / "roads.graph.json").exists():
        pytest.skip("region data not built")
    w = common.load_world(REGION_ID)
    assert len(w.edges) > 500 and len(w.buildings) > 500 and len(w.route) > 1000
    all_fs = []
    for fn in (overlaps.check, continuity.check, terrain.check, signs.check, buildings.check):
        all_fs += fn(w)
    all_fs = common.finalize(w, all_fs)
    s = common.summarize(all_fs)
    assert s["count"] > 100
    for f in all_fs[:50]:
        assert -1100 < f.e < 1100 and -1100 < f.n < 1100
        assert 52.9 < f.lat < 53.4 and 22.9 < f.lon < 23.4
        assert f.chunk is not None
