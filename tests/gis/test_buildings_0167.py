"""ADR 0167: building overrides of the gate-3 frames cm92458760 / cm109685822 (EC kiosk, blue EC outbuilding, heat
accumulator tank, blue Kwadrat pavilion, tower colour) and the `height_m` override key of buildings_mesh.load."""
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import yaml
from shapely.geometry import Point, box
from shapely.geometry.polygon import orient

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REGION_DIR = REPO / "Data" / "Regions" / "bialystok-industrial-c"
ORIGIN = (777995.0, 596223.0)
KIOSK, OFFICE, TANK = "osm:way/591365138", "bdot:2BE4B431-CA0E-1BF0-E053-CC2BA8C0D140", "osm:way/279896715"
PAVILION, TOWER = "bdot:ffe33067-f96d-4676-9355-469cfe147783", "bdot:2BE4B431-CA0F-1BF0-E053-CC2BA8C0D140"


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **kw):
        self.parts.append(SimpleNamespace(layer=layer, mat=mat, V=np.asarray(V, float), T=np.asarray(T).reshape(-1, 3)))

    def mats(self, layer):
        return {p.mat for p in self.parts if p.layer == layer}

    def ztop(self, layer, mat):
        return max(float(p.V[:, 2].max()) for p in self.parts if p.layer == layer and p.mat == mat)


_HF = SimpleNamespace(sample=lambda x, y: np.full(np.shape(x), 100.0))


def _region():
    fc = json.loads((REGION_DIR / "buildings.geojson").read_text(encoding="utf-8"))
    ovr = yaml.safe_load((REGION_DIR / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    return fc, ovr


def _loaded(ids):
    from streetscape import buildings_mesh as BM
    fc, ovr = _region()
    fc = {"features": [f for f in fc["features"] if f["id"] in ids]}
    return {b["id"]: b for b in BM.load(fc, ORIGIN, ovr)}


def _build(b):
    from streetscape import buildings_mesh as BM
    buf = _Buf()
    BM.build(buf, [b], _HF, None, None, box(-5000, -5000, -4990, -4990), {}, sign_out=[])
    return buf


def test_height_override_replaces_the_default_height_only_where_authored():
    from streetscape import buildings_mesh as BM
    fc, ovr = _region()
    raw = {f["id"]: f["properties"] for f in fc["features"]}
    got = _loaded({KIOSK, TANK, TOWER})
    assert raw[KIOSK]["height_source"] == "default" and raw[TANK]["height_source"] == "default"
    assert got[KIOSK]["props"]["height_m"] == 2.0 and got[TANK]["props"]["height_m"] == 39.0
    assert got[TOWER]["props"]["height_m"] == raw[TOWER]["height_m"]            # LoD1 height untouched
    assert raw[KIOSK]["height_m"] == 6.0                                        # the source record is not rewritten
    plain = BM.load({"features": [f for f in fc["features"] if f["id"] == KIOSK]}, ORIGIN, [])
    assert plain[0]["props"]["height_m"] == 6.0


def test_kiosk_is_a_low_chamber_under_a_dark_slab():
    b = _loaded({KIOSK})[KIOSK]
    buf = _build(b)
    for layer in ("buildings", "buildings_low"):
        assert buf.ztop(layer, "plaster_light") <= 100.0 + 2.0 + 1e-6
        assert "hall_flashing" in buf.mats(layer)
    assert max(float(p.V[:, 2].max()) for p in buf.parts if p.layer == "collision") <= 102.0 + 0.1


def test_tank_is_tall_light_and_banded_on_both_lods():
    b = _loaded({TANK})[TANK]
    assert b["typ"] == "hall" and len(b["poly"].exterior.coords) > 40
    buf = _build(b)
    for layer in ("buildings", "buildings_low"):
        assert {"plaster_grey", "plaster_blue"} <= buf.mats(layer) and "plaster_white" not in buf.mats(layer)
        assert not any(m.startswith("hall_wall") for m in buf.mats(layer))
        assert abs(buf.ztop(layer, "plaster_grey") - 139.0) < 0.6
        band = [p for p in buf.parts if p.layer == layer and p.mat == "plaster_blue"]
        zs = np.concatenate([p.V[:, 2] for p in band])
        assert 128.0 <= zs.min() and zs.max() <= 131.0
        # the band goes all round: its vertices cover every quadrant about the tank axis
        c = np.asarray(b["poly"].centroid.coords[0])
        xy = np.concatenate([p.V[:, :2] for p in band]) - c
        assert {(bool(x > 0), bool(y > 0)) for x, y in xy} == {(True, True), (True, False), (False, True), (False, False)}


def test_authored_walls_and_glazing_on_both_lods_without_a_glass_primitive_on_lod1():
    got = _loaded({OFFICE, PAVILION})
    for bid, wall, n_min in ((OFFICE, "plaster_blue", 9), (PAVILION, "hall_plinth", 2)):
        buf = _build(got[bid])
        for layer in ("buildings", "buildings_low"):
            m = buf.mats(layer)
            assert wall in m
            assert not any("__far_" in x or x in ("plaster_beige", "plaster_grey") for x in m), (bid, layer, m)
        assert "plaster_blue" not in buf.mats("buildings_low") or bid == OFFICE
        panes = [p for p in buf.parts if p.layer == "buildings" and p.mat == "showroom_glass"]
        assert sum(len(p.T) for p in panes) >= 2 * n_min
        # glass_lod1: Low draws LOD1 only and chunks 6_6 / 6_7 have no glass there - the panes use the frame material
        assert "showroom_glass" not in buf.mats("buildings_low")
        l0 = sum(len(p.T) for p in buf.parts if p.layer == "buildings" and p.mat == "hall_flashing")
        l1 = sum(len(p.T) for p in buf.parts if p.layer == "buildings_low" and p.mat == "hall_flashing")
        assert 2 * n_min <= l1 < l0


def test_glass_lod1_is_optional_and_validated():
    from streetscape import frontage as FR
    from streetscape import materials as MT
    assert FR.plan({"wall": "plaster_light"}, MT.M)["glass_lod1"] is None
    assert FR.plan({"wall": "plaster_light", "glass_lod1": "hall_flashing"}, MT.M)["glass_lod1"] == "hall_flashing"
    try:
        FR.plan({"wall": "plaster_light", "glass_lod1": "no_such_material"}, MT.M)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown glass_lod1 material accepted")


def test_lod1_of_the_two_chunks_gets_no_material_it_did_not_draw_before():
    """Budget of ADR 0167: every material new to a chunk's LOD1 is one draw (plus shadow) on Low. The authored
    buildings may add plaster_blue (chunk 6_7) only because the tank no longer brings plaster_white there."""
    got = _loaded({OFFICE, PAVILION, TANK, KIOSK})
    m = {k: _build(b).mats("buildings_low") for k, b in got.items()}
    assert m[PAVILION] <= {"hall_plinth", "hall_flashing", "plinth_dark", "roof_membrane", "downpipe"}, m[PAVILION]
    assert m[KIOSK] <= {"plaster_light", "hall_flashing", "plinth_dark", "roof_membrane", "downpipe"}, m[KIOSK]
    new_67 = (m[OFFICE] | m[TANK]) - {"plaster_grey", "hall_flashing", "plinth_dark", "roof_membrane", "downpipe"}
    assert new_67 == {"plaster_blue"}, new_67


def test_outbuilding_windows_face_the_access_road():
    # the outbuilding's windows are on the long side that looks to the access road (NE), sill about 1 m
    b = _loaded({OFFICE})[OFFICE]
    buf = _build(b)
    g = np.concatenate([p.V for p in buf.parts if p.layer == "buildings" and p.mat == "showroom_glass"])
    assert 100.9 <= g[:, 2].min() and g[:, 2].max() <= 102.6
    ne = np.array([np.sin(np.radians(28.0)), np.cos(np.radians(28.0))])
    c = np.asarray(b["poly"].centroid.coords[0])
    assert float(((g[:, :2] - c) @ ne).min()) > 4.0


def test_tower_takes_a_material_with_a_far_facade_variant():
    from streetscape import materials as MT
    b = _loaded({TOWER})[TOWER]
    assert b["ovr"]["wall_material"] == "plaster_beige" and b["typ"] == "office"
    assert "plaster_beige__far_office" in MT.M
    assert "plaster_blue" in MT.M and not any(k.startswith("plaster_blue__far") for k in MT.M)


def test_overrides_point_at_buildings_of_the_region_inside_the_frames():
    fc, ovr = _region()
    ids = {f["id"] for f in fc["features"]}
    mine = [o for o in ovr if str(o.get("id", "")).startswith(("g3a-ec-", "g3a-kwadrat-blue", "g3a-office-tower"))]
    assert len(mine) == 7
    for o in mine:
        assert o["target"]["building"] in ids and o.get("reason") and o.get("confidence") and o.get("verify")
    cams = {c["id"]: c for c in json.loads((REGION_DIR / "sbs_cameras.json").read_text(encoding="utf-8"))["cameras"]}
    cam = cams["sbs-g3-a-cm92458760"]
    from shapely.geometry import shape
    kiosk = next(shape(f["geometry"]) for f in fc["features"] if f["id"] == KIOSK)
    assert kiosk.distance(Point(cam["pos"][0] + ORIGIN[0], cam["pos"][1] + ORIGIN[1])) < 45.0


def test_round_tanks_and_fuel_kiosk_are_plain_structures():
    tanks, fuel = ("osm:way/264944879", "osm:way/264944878"), "osm:way/957256518"
    got = _loaded({*tanks, fuel})
    for t in tanks:
        m = _build(got[t]).mats("buildings_low")
        assert "plaster_light" in m and not any("__far_" in x or x.startswith("brick") for x in m), m
        assert got[t]["props"]["height_m"] == 6.0                 # default height kept (no source for another)
    assert got[fuel]["props"]["height_m"] == 3.4 and got[fuel]["typ"] == "shed"
