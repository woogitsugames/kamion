"""Tests for the 16 wave-14 unknown OSM sign codes (Dz.U. 2019 poz. 2310 / 2311)."""
from __future__ import annotations

import numpy as np
import pytest

from roads import network
from roads.junctions import build_junctions
from streetscape import furniture as FU
from streetscape import props as PP
from streetscape import signs as SG
from streetscape import signs_route as SR
from streetscape import sources as SRC

EXPECTED_SHAPES = {
    "A-3": "triangle_up",
    "A-4": "triangle_up",
    "A-5": "triangle_up",
    "A-11": "triangle_up",
    "A-11a": "triangle_up",
    "A-12a": "triangle_up",
    "A-17": "triangle_up",
    "B-21": "disc",
    "B-31": "disc",
    "B-35": "disc",
    "D-4a": "square",
    "D-5": "square",
    "D-51": "rect",
    "D-52": "rect",
}

ORIGIN = (777995.0, 596223.0)


@pytest.mark.parametrize("code,want_shape", sorted(EXPECTED_SHAPES.items()))
def test_wave14_sign_face_and_plate_geometry(code, want_shape):
    assert SG.is_known(code)
    shape, im = SG.face(code)
    assert shape == want_shape
    assert im.size[0] >= 256 and im.size[1] >= 200
    assert SG.png_bytes(im) == SG.png_bytes(SG.face(code)[1])

    arr = np.asarray(im)
    worn = np.asarray(SG.weather(im, code))
    assert np.array_equal(worn[..., 3], arr[..., 3])

    high, low, collision = PP.plate(code)
    assert collision is None
    assert {p["mat"] for p in high.out()} == {"plate_back", f"sign_{code}", "steel_galv"}
    assert {p["mat"] for p in low.out()} == {"plate_back", f"sign_{code}"}
    for part in low.out():
        assert np.all((part["UV"] >= 0.0) & (part["UV"] <= 1.0))


def test_d51_and_d52_rect_dimensions():
    assert SG.rect_size("D-51") == pytest.approx((0.60, 0.75))
    assert SG.rect_size("D-52") == pytest.approx((0.90, 0.42))


def test_b16_maxheight_parsing_and_keep_tags():
    assert "maxheight" in SRC.KEEP_TAGS
    assert "maxweight" in SRC.KEEP_TAGS
    assert SR.parse_traffic_sign("PL:B-16", {"maxheight": "3.7"}) == ["B-16_3.7"]
    assert SR.parse_traffic_sign("PL:B-16", {"maxheight": "3,7 m"}) == ["B-16_3.7"]
    assert SR.parse_traffic_sign("PL:B-16[3.7]", {}) == ["B-16_3.7"]
    assert SR.parse_traffic_sign("PL:B-16", {}) == ["B-16"]
    assert not SG.is_known("B-16")


def test_osm_signs_places_all_16_wave14_codes():
    ox, oy = ORIGIN
    g = {
        "nodes": [{"id": "n0", "x": ox - 200.0, "y": oy}, {"id": "n1", "x": ox + 200.0, "y": oy}],
        "edges": [{
            "id": "e1", "from": "n0", "to": "n1",
            "geometry": [[ox - 200.0, oy], [ox + 200.0, oy]],
            "attrs": {"highway": {"v": "secondary"}, "oneway": {"v": "no"}, "lanes": {"v": 2}},
        }],
    }
    net = network.load(g, ORIGIN)
    for c in net.chains:
        c.z = np.zeros(len(c.line.s))
        c.e = np.zeros(len(c.line.s))
    juncs = build_junctions(net, [])
    network.assign_sides(net, [], built_up=True)

    codes_tags = [(c, {}) for c in sorted(EXPECTED_SHAPES)]
    codes_tags += [("B-16", {"maxheight": "3.7"}), ("B-18", {"maxweight": "10"})]
    nodes = [
        {
            "osm_node": 100 + i,
            "tags": {"traffic_sign": f"PL:{cd}", "direction": "forward", **extra},
            "geometry": {"type": "Point", "coordinates": [ox - 180.0 + i * 20.0, oy - 4.0]},
        }
        for i, (cd, extra) in enumerate(codes_tags)
    ]
    # Bare B-16 without maxheight stays reported as unknown / needs_value (never invented)
    nodes.append({
        "osm_node": 999,
        "tags": {"traffic_sign": "PL:B-16", "direction": "forward"},
        "geometry": {"type": "Point", "coordinates": [ox + 180.0, oy - 4.0]},
    })

    src = {"osm": {"nodes": nodes, "areas": []}, "bdot10k": {}}
    pl = FU.Placer(lambda e, n: np.zeros(np.shape(e)))
    rep, codes = {}, set()
    SR.osm_signs(pl, net, src, np.array(ORIGIN), juncs, rep, codes)

    placed = rep["osm_signs"]["placed"]
    for cd in EXPECTED_SHAPES:
        assert placed.get(cd) == 1, cd
    assert placed.get("B-16_3.7") == 1
    assert placed.get("B-18_10") == 1
    assert rep["osm_signs"]["unknown"] == {"B-16": 1}
    assert rep["osm_signs"]["needs_value"] == [{"osm_node": 999, "code": "B-16", "tag": "maxheight"}]


def test_verified_sign_face_geometry_dz_u_2019_2310():
    """Regression checks against Dz.U. 2019 poz. 2310 / 2311 patterns for D-51, D-52, B-21, A-11, A-11a."""
    # B-21: diagonal red slash runs top-right -> bottom-left (/), NOT top-left -> bottom-right (\)
    b21 = np.asarray(SG.face("B-21")[1])
    s = b21.shape[0]
    p_tr = b21[int(s * 0.25), int(s * 0.75), :3]          # on slash (top-right inside white disc)
    p_tl = b21[int(s * 0.25), int(s * 0.25), :3]          # off slash (top-left inside white disc)
    assert p_tr[0] > 150 and p_tr[1] < 60                 # red
    assert p_tl[0] > 200 and p_tl[1] > 200                # white

    # A-11 (2 humps) vs A-11a (1 hump): at peak height center x is yellow in A-11 and black in A-11a
    a11 = np.asarray(SG.face("A-11")[1])
    a11a = np.asarray(SG.face("A-11a")[1])
    y_peak = int(s * 0.72)
    assert a11[y_peak, s // 2, 0] > 200                   # yellow valley in A-11
    assert a11a[y_peak, s // 2, 0] < 60                   # black central hump in A-11a
    assert a11[y_peak, int(s * 0.36), 0] < 60             # left hump peak in A-11

    # D-51: retains upper/lower white text zones ("Kontrola prędkości" / "Fotoradar") and radar waves
    d51 = np.asarray(SG.face("D-51")[1])
    w51, h51 = d51.shape[1], d51.shape[0]
    assert np.any(d51[:int(h51 * 0.28), :, 0] > 200)      # top text present
    assert np.any(d51[int(h51 * 0.80):, :, 0] > 200)      # bottom text present
    # Top-center above camera body is blue (small shutter button is on the left, no central prism)
    assert d51[int(h51 * 0.44), int(w51 * 0.30), 2] > 120

    # D-52: compact top car (sides white at top) and bottom text spanning wide
    d52 = np.asarray(SG.face("D-52")[1])
    w52, h52 = d52.shape[1], d52.shape[0]
    assert d52[int(h52 * 0.30), int(w52 * 0.25), 0] > 200 # white beside compact car
    assert np.any(d52[int(h52 * 0.65):int(h52 * 0.80), int(w52 * 0.12), 0] < 60)  # wide "Strefa ruchu" text

