"""ADR 0162: street furniture and direction boards after research G5 (Białystok documents) and G3 (S8 / DK8 signs).

Sources quoted in the asserts (research/g5-street-furniture/manifest.csv, files/G5-001, G5-004, G5-005, G5-010):
- BKM "Wzór plastyczny wiaty przystankowej" (2019 zał. 1, 2020 zał. 6): "2 m (Moduł)", "n x 2 m (budowa modułowa)",
  "ilością modułów + dwa występy boczne zadaszenia po min 0,5 m", "Jako wiatę standardową przyjmuje się obiekt
  składający się z 3 modułów po 2 m (długość zadaszenia 7 m)", "2,6 m", "0,15 m od chodnika", "1,07 m (0,6 m)",
  "szybami ... o wymiarach 0,6 m x 0,99 m", "0,4 m" (seat), "kolor czerwony - RAL 3020".
- BKM zał. 07c "Projekt stelaży": D-15 rack 55 cm x 80,5 cm.
- ZDM standard 2018: U-12a "olsztyński" - posts "rura stalowa ocynkowana o średnicy 60,3 mm", "przęsło ... o średnicy
  48,3 mm", 2000 / 1100 / 1500 mm, RAL 1012; U-12 "2,50 x 0,83 m"; U-5a "wysokość-90 cm, średnica 20 cm, podstawa 30-cm".
- ZDM PFU lighting: oprawy "do 11 m", wnęka "min 600x130 mm", dolne ok. 0,3 m słupa malowane na szaro.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from roads import standards as S  # noqa: E402
from streetscape import furniture as FU  # noqa: E402
from streetscape import furniture_textures as FT  # noqa: E402
from streetscape import props as PP  # noqa: E402
from streetscape import signs as SG  # noqa: E402


def _verts(mesh, mat=None):
    if mat == "roof":                                   # the roof sheet: atlas swatch "roof" of shelter_paint
        u = PP.SHELTER_UV["roof"]
        return np.concatenate([p["V"][np.all(np.isclose(p["UV"], u), axis=1)] for p in mesh.out()
                               if p["mat"] == "shelter_paint"])
    return np.concatenate([p["V"] for p in mesh.out() if mat is None or p["mat"] == mat])


@pytest.mark.parametrize("modules,roof", [(2, 5.0), (3, 7.0), (4, 9.0)])
def test_shelter_roof_length_is_modules_plus_two_overhangs(modules, roof):
    """'n x 2 m' + 'dwa występy boczne zadaszenia po min 0,5 m' -> 5 / 7 / 9 m."""
    m, _, _ = PP.bus_shelter_bkm(modules)
    R = _verts(m, "roof")
    assert R[:, 0].max() - R[:, 0].min() == pytest.approx(roof, abs=1e-6)
    posts = modules * PP.SHELTER_MODULE_M
    assert (R[:, 0].max() - posts / 2) >= 0.5 - 1e-9


def test_standard_shelter_is_three_modules_7m_red():
    """'wiatę standardową ... 3 modułów po 2 m (długość zadaszenia 7 m)', 'kolor czerwony - RAL 3020'."""
    assert PP.SHELTER_MODULES["bus_shelter"] == 3
    m, _, _ = PP.bus_shelter()
    R = _verts(m, "roof")
    assert np.ptp(R[:, 0]) == pytest.approx(7.0)
    atlas = np.asarray(FT.shelter_atlas(), float)
    u, v = PP.SHELTER_UV["red"]
    px = atlas[int((1 - v) * 512), int(u * 512)]
    assert np.abs(px - np.array(FT.RAL3020_SRGB)).max() < 20


def test_shelter_height_wall_glass_seat():
    """'2,6 m' to the roof, wall '1,07 m', glass '0,6 m x 0,99 m' from '0,15 m', seat '0,4 m'."""
    m, l1, col = PP.bus_shelter()
    R = _verts(m, "roof")
    assert R[:, 2].min() - 0.06 == pytest.approx(2.6)           # underside of the low edge (sheet sits 6 cm up)
    G = _verts(m, "shelter_glass_clear")
    assert G[:, 2].min() == pytest.approx(0.15)
    assert (G[:, 2].max() - G[:, 2].min()) == pytest.approx(3 * 0.6)
    assert PP.SHELTER_PANE_W_M == 0.99 and PP.SHELTER_PANE_H_M == 0.6
    # two panes of 0.99 m per 2 m module, one pane across the 1.07 m side wall
    assert 2 * PP.SHELTER_PANE_W_M <= PP.SHELTER_MODULE_M and PP.SHELTER_PANE_W_M <= PP.SHELTER_WALL_D_M
    side = G[np.isclose(np.abs(G[:, 0]), 3.0)]
    assert np.ptp(side[:, 1]) == pytest.approx(1.07)
    assert PP.SHELTER_SEAT_H_M == 0.4
    # depth of the roof: 0.55 m behind the back posts + 1.4 m to the road-side edge
    assert np.ptp(R[:, 1]) == pytest.approx(0.55 + 1.4)


def test_shelter_material_slots_and_lod():
    """Two slots (one atlas for frame / roof / bench / boards), LOD1 lighter than LOD0, collision covers the roof."""
    for name in ("bus_shelter", "bus_shelter_5m", "bus_shelter_9m", "bus_shelter_black"):
        P = PP.build_all(set(), {})[name]
        m, l1, col = P[:3]
        assert {p["mat"] for p in m.out()} == {"shelter_paint", "shelter_glass_clear"}
        t0 = sum(len(p["T"]) for p in m.out())
        t1 = sum(len(p["T"]) for p in l1.out())
        assert t1 < 0.4 * t0 and t0 < 800
        C = _verts(col)
        assert C[:, 2].max() >= 2.85


def test_d15_rack_size():
    """BKM zał. 07c: rack panel 55 x 80.5 cm."""
    assert (PP.D15_RACK_W_M, PP.D15_RACK_H_M) == (0.55, 0.805)


def test_shelter_variant_shares():
    """2020 order: 44 x 3 modules, 29 x 2, 7 x 4 of 80 (G5 zał. 8). Black share WORKING_VALUE."""
    rng = np.random.default_rng(0)
    names = [FU.shelter_variant(q) for q in rng.uniform(-1000, 1000, (4000, 2))]
    n = len(names)
    black = names.count("bus_shelter_black") / n
    assert abs(black - FU.SHELTER_BLACK_SHARE) < 0.03
    red = [x for x in names if x != "bus_shelter_black"]
    assert abs(red.count("bus_shelter") / len(red) - 44 / 80) < 0.04
    assert abs(red.count("bus_shelter_5m") / len(red) - 29 / 80) < 0.04
    assert abs(red.count("bus_shelter_9m") / len(red) - 7 / 80) < 0.03
    assert FU.shelter_variant((12.3, 45.6)) == FU.shelter_variant((12.3, 45.6))


def test_u12a_dimensions():
    """'rura ... 60,3 mm', przęsło '48,3 mm', 2000 / 1100 mm, loop 0.64 m (G5 manifest)."""
    m, _, _ = PP.railing_u12a()
    V = _verts(m)
    assert PP.U12A_POST_D == 0.0603 and PP.U12A_RAIL_D == 0.0483
    assert V[:, 2].max() == pytest.approx(1.10)
    assert PP.U12A_BAY_M == 2.0
    loop = V[V[:, 0] > -0.95]
    assert (loop[:, 2].max() - loop[:, 2].min()) == pytest.approx(0.64 + 0.0483, abs=0.01)
    assert {p["mat"] for p in m.out()} == {"paint_ral1012"}


def test_u12_and_u5a_dimensions():
    """U-12 '2,50 x 0,83 m' yellow with red posts; U-5a 0.90 m, Ø0.20 m, base 0.30 m."""
    m, _, _ = PP.fence_u12()
    Y = _verts(m, "paint_ral1012")
    assert np.ptp(Y[:, 2]) == pytest.approx(0.83 + 0.0075 * 2, abs=1e-3)
    assert np.ptp(Y[:, 0]) == pytest.approx(2.50, abs=0.05)
    assert "paint_ral3020" in {p["mat"] for p in m.out()}
    m, _, _ = PP.pylon_u5a()
    V = _verts(m)
    assert V[:, 2].max() == pytest.approx(0.90)
    assert np.ptp(V[:, 0]) == pytest.approx(0.30)


def test_lamp_heights_door_and_grey_base():
    """'do 11 m'; door recess 600 x 130 mm on LOD0; grey foot band 0.3 m in the galv atlas."""
    assert max(d["h"] for d in S.LAMP.values()) <= 11.0
    m, l1, _ = PP.lamp(11.0, 1.5)
    assert _verts(m)[:, 2].max() <= 11.1
    assert PP.LAMP_DOOR == (0.60, 0.13)
    galv = np.asarray(FT.textures()["furniture_galv"], float)
    h = galv.shape[0]
    row = lambda z: int((1 - z / 9.0) * h)                      # noqa: E731
    band = galv[row(0.15)].mean(0)
    above = galv[row(0.6)].mean(0)
    assert np.abs(band[0] - band[2]) < 12                       # neutral grey paint
    assert band.mean() < above.mean() - 40                      # darker than the zinc above it


def test_sunk_mast_keeps_grey_band_at_real_ground():
    """A DK8 mast sunk 7.5 m under the deck: atlas v counts from its real foot, not from the deck level."""
    m, _, _ = PP.lamp_y(10.3, sink=7.5)
    galv = [p for p in m.out() if p["mat"] == "furniture_galv"][0]
    z = galv["V"][:, 2]
    v = galv["UV"][:, 1]
    assert np.allclose(v, np.clip((z + 7.5) / 9.0, 0.002, 0.998), atol=2e-4)
    assert v[np.argmin(z)] <= 0.01


def test_power_pole_one_height():
    """Mesh, wire attachment and the deck-clearance height are the same number (was 10 vs 12 m)."""
    m, _, col = PP.power_pole()
    assert _verts(m)[:, 2].max() == pytest.approx(S.GROUND_PROP_H["power_pole"])
    assert S.ground_prop_height("power_pole") == S.GROUND_PROP_H["power_pole"] == 12.0


def test_d15_face_is_side_view_bus_without_text():
    """Wzór D-15: bus pictogram only - the face has no lettering band under the bus."""
    im = np.asarray(SG.square("D-15").convert("RGB"), float)
    strip = im[int(512 * 0.74):int(512 * 0.84), int(512 * 0.3):int(512 * 0.7)]
    assert strip.min() > 200                                   # white, no "BUS"


def test_panel_board_arrows_and_country_ovals():
    """G3-P001..P004: stacked panels, ↑ left, → right, PL / BY ovals; G3-P009: E-1 cross; G3-P010: VMS."""
    im, w, h = SG.panel_board([{"rows": [(["8", "E67"], "Warszawa"), (["65"], "Ełk")], "arrow": "up"},
                               {"rows": [(["8", "E67"], "Augustów"), (["19"], "Kuźnica PL BY")], "arrow": "right"}],
                              size_m=(5.0, 2.3))
    assert (w, h) == pytest.approx((5.0, 2.3), abs=0.02)
    assert SG._split_dest("Kuźnica PL/BY") == ("Kuźnica", ["PL", "BY"])
    assert SG._split_dest("Kuźnica B. PL BY") == ("Kuźnica B.", ["PL", "BY"])
    assert SG._split_dest("Centrum") == ("Centrum", [])
    a = np.asarray(im.convert("RGB"), float)
    H, W = a.shape[:2]
    right_arrow = a[int(H * 0.6):int(H * 0.95), int(W * 0.9):int(W * 0.97)]
    left_arrow = a[int(H * 0.6):int(H * 0.95), int(W * 0.03):int(W * 0.08)]
    assert (right_arrow.min(axis=2) > 200).mean() > 0.03      # white arrow on the right of the lower panel
    assert (left_arrow.min(axis=2) > 200).mean() < 0.03
    im, w, h = SG.e1_cross_board((["675"], "Centrum"), [(["65"], "Bobrowniki PL BY")], [(["8", "E67"], "Warszawa")],
                                 (6.1, 1.8))
    assert (w, h) == pytest.approx((6.1, 1.8), abs=0.01)
    im, w, h = SG.vms_board(["CENTRUM PRZEZ:"], (3.6, 1.1))
    a = np.asarray(im.convert("RGB"), float)
    assert a.mean() < 80 and (a.min(axis=2) > 200).mean() > 0.005


def test_overhead_board_is_one_material_with_plain_back_band():
    """Budget: face + grey back sheet + rails of a gantry board share the board's own texture (1 draw, not 3);
    the back samples the plain grey band under the face (ADR 0127 plain back kept)."""
    PP.BOARD_BAND["OB_band_test"] = 0.05
    try:
        m, l1, _ = PP.board("OB_band_test", 4.0, 2.0)
    finally:
        PP.BOARD_BAND.pop("OB_band_test")
    assert set(m.prims) == {"sign_OB_band_test"} and l1 is m
    V, T, UV = (np.concatenate(x) for x in m.prims["sign_OB_band_test"])
    face = V[:, 1] > 0.055
    assert UV[face][:, 1].min() == pytest.approx(0.05)             # the face never samples the band
    assert np.allclose(UV[~face], [0.5, 0.025])                    # back + rails: band centre
    r, g, b = (c / 255 for c in PP.BOARD_BACK_SRGB)
    lin = [((c + 0.055) / 1.055) ** 2.4 for c in (r, g, b)]
    assert lin == pytest.approx([0.21, 0.22, 0.22], abs=0.01)
