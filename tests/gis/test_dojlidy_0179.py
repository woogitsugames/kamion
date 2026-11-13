"""ADR 0179 - opt-in override kinds added for region bialystok-dojlidy and the authored data that uses them.

The reference region C has none of these overrides, so its output cannot change; that is asserted here on the data
(no such kinds / objects in C) instead of by a second 8-minute build."""
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))

DOJ = REPO / "Data" / "Regions" / "bialystok-dojlidy"
C = REPO / "Data" / "Regions" / "bialystok-industrial-c"
NEW_KINDS = {"building_part", "open_ground", "life_rules"}


def _ov(d):
    return (yaml.safe_load((d / "overrides.yaml").read_text(encoding="utf-8")) or {}).get("overrides", [])


def test_region_c_has_no_0179_overrides():
    assert not [o["id"] for o in _ov(C) if o.get("kind") in NEW_KINDS]


def test_building_part_cuts_host_and_keeps_every_piece():
    from shapely.geometry import Polygon
    from streetscape import buildings_mesh as BM
    host = {"id": "bdot:h", "poly": Polygon([(0, 0), (30, 0), (30, 10), (0, 10)]), "props": {"function": "produkcyjny",
            "height_m": 6.0}, "ovr": {}, "typ": "hall"}
    blds = [host]
    ov = [{"id": "tower", "kind": "building_part", "polygon_en": [[10, -1], [20, -1], [20, 11], [10, 11]],
           "cut_from": ["bdot:h"], "height_m": 19.0, "storeys": 5, "set": {"typology": "office"}}]
    out = BM.building_parts(blds, ov)
    ids = sorted(b["id"] for b in out)
    assert ids == ["bdot:h#cut1", "override:tower"]
    part = next(b for b in out if b["id"] == "override:tower")
    assert part["typ"] == "office" and part["props"]["height_m"] == 19.0
    # host split in two 10 x 10 pieces, neither overlapping the part
    pieces = [host["poly"]] + [b["poly"] for b in out if b["id"].startswith("bdot:h#")]
    assert sum(p.area for p in pieces) == pytest.approx(200.0, abs=3.0)
    assert all(p.intersection(part["poly"]).area < 0.01 for p in pieces)
    assert BM.building_parts(blds, []) == []


def test_tyre_scrub_keep_off_is_opt_in():
    import inspect
    from streetscape import life as LF
    assert inspect.signature(LF.tyre_scrub).parameters["keep_off"].default is None
    assert inspect.signature(LF.place).parameters["tyre_keep_off"].default is None


def test_aerodrome_land_is_not_a_paved_yard():
    from streetscape import paved as PV
    assert "lotnisko lub lądowisko" in PV.KUKO_NOT_A_SURFACE
    rep = json.loads((DOJ / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    assert rep["paved_m2_by_material"]["yard_concrete"] < 50000          # was 546 319 m2 (54 ha of slabs)
    assert rep["paved_m2_by_source"]["authored_override"][1] == pytest.approx(30150, rel=0.02)   # runway 1005 x 30 + pad


def test_dojlidy_overrides_applied():
    ov = {o["id"]: o for o in _ov(DOJ)}
    assert {"kuronia3-office-block", "krywlany-runway-09r-27l", "krywlany-open-meadow"} <= set(ov)
    for o in ov.values():
        assert o.get("reason") and o.get("confidence"), o["id"]
    rep = json.loads((DOJ / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    fu = rep["furniture"]
    row = fu["lamp_rows"]["kuronia-median-double-lamps"]
    assert row["placed"] >= 20 and row["rule_lamps_removed"] >= 30
    assert fu["life"]["tyre_scrub_passes_cut_at_road"] > 0
    og = rep["vegetation"]["open_ground"][0]
    assert og["trees_removed"] > 500
    assert rep["vegetation"]["tree_groups"]["trees"] >= 40
    assert not rep["paved_m2_by_source"].get("unpaved_area_stale")


def test_lamp_row_points_inside_tile():
    rows = json.loads((DOJ / "lamp_rows.json").read_text(encoding="utf-8"))["rows"]
    for r in rows:
        assert r["proto"] == "lamp_double_10m"
        assert all(abs(e) <= 1024 and abs(n) <= 1024 for e, n in r["points_en"])


def test_hall_bands_and_camera_pitch_are_opt_in():
    """s19: `hall_bands: false` (one-colour hall) and photo camera `pitch_deg` exist only in dojlidy data."""
    assert not [o["id"] for o in _ov(C) if "hall_bands" in (o.get("set") or {})]
    assert not (C / "control_cameras_photo.authored.json").exists()
    ov = {o["id"]: o for o in _ov(DOJ)}
    assert ov["rosti-hall-colour"]["set"] == {"wall_material": "hall_wall_white", "hall_bands": False}
    cams = {c["id"]: c for c in json.loads((DOJ / "control_cameras_photo.authored.json").read_text(encoding="utf-8"))["cameras"]}
    assert cams["photo_P11-094"]["pitch_deg"] > 0 and "pitch_deg" not in cams["photo_P11-129b"]
    gen = {c["id"]: c for c in json.loads((DOJ / "generated" / "control_cameras.json").read_text(encoding="utf-8"))["cameras"]}
    lvl, up = gen["photo_P11-129b"], gen["photo_P11-094"]
    assert lvl["look_at"][2] == lvl["pos"][2] and up["look_at"][2] > up["pos"][2] + 5.0
