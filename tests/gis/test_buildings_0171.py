"""ADR 0171: follow-up of ADR 0167 (review REVIEW-2026-11-13-s17-0167): slate-blue pavilion cladding with punched
upper-floor windows, lighter plaster_blue, white window frames of the EC outbuilding on both LODs, the tower without
the grey ribbon rows. Keys: frontage `frame`, glazing `window_m`, building override `ribbon`."""
import numpy as np

from test_buildings_0167 import OFFICE, PAVILION, TOWER, _build, _loaded


def _tris(buf, layer, mat):
    return sum(len(p.T) for p in buf.parts if p.layer == layer and p.mat == mat)


def test_tower_has_no_hashed_ribbon_rows_or_spandrel_bands():
    # ADR 0180 replaced the punched rows of ADR 0171 on the four main walls by authored facades (test_buildings_0180);
    # `ribbon: false, bands: false` still hold for the walls no rule covers
    b = _loaded({TOWER})[TOWER]
    assert b["ovr"]["ribbon"] is False and b["ovr"]["bands"] is False
    buf = _build(b)
    assert "plaster_band_grey" not in buf.mats("buildings")
    assert not any(x.endswith("__far_ribbon") and not x.startswith("plaster_white") for x in buf.mats("buildings_low"))


def test_ribbon_override_is_authored_only():
    from streetscape import buildings_mesh as BM
    import json
    from test_buildings_0167 import ORIGIN, REGION_DIR
    fc = json.loads((REGION_DIR / "buildings.geojson").read_text(encoding="utf-8"))
    plain = BM.load({"features": [f for f in fc["features"] if f["id"] == TOWER]}, ORIGIN, [])[0]
    assert any(x.endswith("__far_ribbon") for x in _build(plain).mats("buildings_low"))   # the hashed pick is kept


def test_pavilion_upper_floor_is_a_row_of_separate_windows():
    b = _loaded({PAVILION})[PAVILION]
    buf = _build(b)
    for layer in ("buildings", "buildings_low"):
        assert "plaster_slate_blue" in buf.mats(layer) and "hall_plinth" not in buf.mats(layer)
    g = [p for p in buf.parts if p.layer == "buildings" and p.mat == "showroom_glass"]
    tri = np.concatenate([p.V[p.T] for p in g])                  # (n, 3, 3)
    upper = tri[tri[:, :, 2].min(1) > 104.5]
    widths = [float(np.hypot(*(t[:, :2].max(0) - t[:, :2].min(0)))) for t in upper]
    upper = upper[::2]                                           # one pane = 2 triangles
    assert len(upper) >= 8 and max(widths) < 1.6, (len(upper), widths)


def test_outbuilding_has_light_frames_on_both_lods_without_a_new_lod1_material():
    b = _loaded({OFFICE})[OFFICE]
    buf = _build(b)
    assert _tris(buf, "buildings", "window_frame") > 0
    n1 = _tris(buf, "buildings_low", "plaster_grey")
    assert n1 == 11 * 5 * 2, n1                      # 11 windows x (4 ring bars + 1 mullion) x 2 triangles
    assert "window_frame" not in buf.mats("buildings_low")
    # frames are flush with the wall plane inside the opening: no frame vertex outside the wall's bounding box
    w = np.concatenate([p.V[:, :2] for p in buf.parts if p.layer == "buildings_low" and p.mat == "plaster_blue"])
    f = np.concatenate([p.V[:, :2] for p in buf.parts if p.layer == "buildings_low" and p.mat == "plaster_grey"])
    assert (f.min(0) >= w.min(0) - 1e-6).all() and (f.max(0) <= w.max(0) + 1e-6).all()


def test_frame_and_window_keys_are_optional_and_validated():
    from streetscape import frontage as FR
    from streetscape import materials as MT
    s = FR.plan({"wall": "plaster_light", "glazing": [{"facing": "N"}]}, MT.M)
    assert s["frame"] is None and s["glazing"][0]["window_m"] is None
    s = FR.plan({"wall": "plaster_light", "frame": {"material_lod1": "plaster_grey"}}, MT.M)
    assert s["frame"] == {"material": "window_frame", "width_m": 0.12, "material_lod1": "plaster_grey"}
    try:
        FR.plan({"wall": "plaster_light", "frame": {"material": "no_such_material"}}, MT.M)
    except ValueError:
        pass
    else:
        raise AssertionError("unknown frame material accepted")


def test_blue_materials():
    from streetscape import materials as MT
    c = MT.M["plaster_blue"]["color"]
    assert c[2] > c[1] > c[0] and 0.40 <= c[2] <= 0.50          # lighter and bluer than ADR 0167 (0.31)
    s = MT.M["plaster_slate_blue"]
    assert s["color"][2] > s["color"][0] and max(s["color"]) <= 0.25 and s.get("tint_linear")
    assert not any(k.startswith("plaster_slate_blue__far") for k in MT.M)
