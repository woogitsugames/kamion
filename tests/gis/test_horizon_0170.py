"""ADR 0170: measured forest stands (authored `kind: forest_stand`), no pine in broadleaf stands, taller thuja walls,
spruce core. Synthetic inputs only (no region data)."""
import numpy as np
import pytest

from streetscape import plantings as PG
from streetscape import plot_kit as PK
from streetscape import plots as PLT
from streetscape import vegetation as VG
from test_house_greenery_0163 import _forest_src, _place

RING = [[0, 0], [200, 0], [200, 200], [0, 200]]


def test_forest_stand_sets_heights_mix_spacing_and_reports_stale():
    src = _forest_src("F1:0", RING)
    ov = [{"id": "young", "kind": "forest_stand", "target": {"bdot": "F1"}, "height_m": [6.5, 11.0], "spacing_m": 3.2,
           "mix": {"birch": 0.6, "maple": 0.4}, "emergent": {"share": 0.02, "height_m": [14.0, 19.0]}},
          {"id": "gone", "kind": "forest_stand", "target": {"bdot": "NOPE"}, "height_m": [5, 6]}]
    t0, _, _ = _place(src, [])
    t1, _, rep = _place(src, ov)
    stand = [t for t in t1 if t["src"] == "bdot:F1:0"]
    assert {t["p"] for t in stand} == {"tree_birch", "tree_maple"}
    h = np.array([t["h"] for t in stand])
    assert len(stand) > 1.5 * sum(1 for t in t0 if t["src"] == "bdot:F1:0"), "authored grid instead of the class spacing"
    canopy = h[h <= 11.0]
    assert canopy.min() >= 6.5 and 0.005 < (h > 11.0).mean() < 0.05 and h.max() <= 19.0
    edge = [t for t in t1 if t["src"].endswith(":edge") and t["p"] != "tree_shrub"]
    assert edge and max(t["h"] for t in edge if t["h"] < 14.0) <= 11.0 * 0.6 + 0.05, "edge row follows the stand's range"
    a = rep["forest_stands"]["applied"][0]
    assert a["id"] == "young" and 6.5 <= a["h_median_m"] <= 11.0 and a["emergent"] >= 1
    assert [s["id"] for s in rep["forest_stands"]["stale"]] == ["gone"]


def test_forest_stand_rejects_bad_input():
    for bad in ({"height_m": [0, 5]}, {"height_m": [9, 5]}, {"height_m": [5, 9], "mix": {"oak": 1.0}}):
        with pytest.raises(ValueError):
            VG.forest_stands([{"id": "x", "kind": "forest_stand", "target": {"bdot": "F"}, **bad}])


def test_broadleaf_stands_have_no_pine():
    assert VG.MIX["liściasty"][VG.SPECIES.index("pine")] == 0.0
    assert abs(sum(VG.MIX["liściasty"]) - 1.0) < 1e-9
    src = _forest_src("F1:0", RING)
    src["bdot10k"]["OT_PTLZ_A"][0]["props"]["kategoria"] = "liściasty"
    src["bdot10k"]["OT_PTLZ_A"][0]["props"]["rodzaj"] = "zadrzewienie"      # no understorey (young pine) in this class
    trees, _, _ = _place(src, [])
    assert not [t for t in trees if t["p"] == "tree_pine" and t["src"] == "bdot:F1:0"]


def test_thuja_wall_clears_the_fences():
    lo, hi = PG.G7["thuja_h_m"]
    assert lo >= 2.4 and hi <= 3.6 and PG.G7["thuja_corner_h_m"] <= 4.0
    assert lo - max(PLT.PK.ROW_H_M[k] for k in ("picket", "boards_brown", "concrete", "lamella")) >= 0.59


def test_spruce_cards_darken_towards_the_bole_and_there_is_no_core_body():
    """review s17 0170 P1 (g7_p03_a): the dark cone of build 2 stood out as a seam beside the camera."""
    h = 9.0
    kit = PLT.Kit()
    PLT.spruce(kit, np.array([0.0, 0.0]), 0.0, h, "k")
    assert sum(len(t) for t in kit.T) == 4 * 2 + 3 * 4, "trunk + three cards of four triangles"
    for V, C in zip(kit.V[-3:], kit.C[-3:]):
        occ = np.linalg.norm(C[:, :3] * 2 - 1, axis=1)
        assert len(V) == 5 and occ[:4].min() > 0.9 and 0.4 <= occ[4] <= 0.6
        assert np.hypot(V[4, 0], V[4, 1]) < 1e-6 and 0.3 * h < V[4, 2] < 0.45 * h


def test_near_lite_garden_tree_has_a_shaded_middle_and_no_core_body():
    """review s17 0170 P1: the dark core body of build 2 showed as a box under the cards. The lite crown near the street
    darkens its own cards towards the axis instead (+ 2 triangles per card) and keeps the two shoulder sprays (+ 4)."""
    def build(species="maple", **kw):
        kit = PLT.Kit()
        PG.garden_tree(kit, np.array([0.0, 0.0]), 0.0, 2.5, 7.0, 1.3, species, "k", lite=True, cards=3, **kw)
        return kit
    plain, near = build(), build(core=True)
    tris = lambda k: sum(len(t) for t in k.T)                               # noqa: E731
    assert tris(near) - tris(plain) == 10
    hedge_v = PK.row("hedge")
    for V, UV, C in zip(near.V, near.UV, near.C):
        fol = C[:, 3] > 0.5
        if not fol.any():
            continue
        assert not ((UV[:, 1] > hedge_v[0]) & (UV[:, 1] < hedge_v[1])).all(), "no body of the hedge row inside the crown"
        occ = np.linalg.norm(C[:, :3] * 2 - 1, axis=1)
        if len(V) == 5:                                                       # a crown card: lit rim, shaded middle
            assert occ[:4].min() > 0.9 and 0.45 <= occ[4] <= 0.65
            assert np.hypot(V[4, 0], V[4, 1]) < 0.4, "the dark vertex is on the crown's axis"
    assert sum(1 for V in near.V if len(V) == 5) == 3
    assert tris(build("birch", core=True)) == tris(build("birch")), "open habit: no shaded middle"


def test_thuja_wall_low_has_a_tip_card_per_plant():
    """review s17 0170 P2: on Low the wall keeps its sparse stations and every plant's round tip is a silhouette card."""
    kit = PLT.Kit()
    PG.thuja_hedge(kit, np.array([0.0, 0.0]), np.array([22.0, 0.0]), np.array([0.0, -1.0]), lambda q: 0.0, 3.0, "h", low=True)
    cards = [(V, UV) for V, UV in zip(kit.V[1:], kit.UV[1:])]
    assert len(cards) == 20                                                   # 22 m at 1.1 m
    wall_top = kit.V[0][:, 2].max()
    assert 3.0 - 0.75 <= wall_top <= 3.0 - 0.3
    u0, u1, v0, v1 = PK.sprite("thuja_a")
    for V, UV in cards:
        assert V[:, 2].min() < wall_top - 0.2 and 3.0 <= V[:, 2].max() <= 3.0 + 0.45
        assert UV[:, 1].max() == pytest.approx(v1) and UV[:, 1].min() > v0 + 0.5 * (v1 - v0)   # the top of the sprite


def test_spruce_card_is_green_not_turquoise():
    """review s17 0170 P2: B <= 0.8 G over the spruce cards (the 0170 build 2 palette read turquoise under the sky)."""
    N = PK.N
    for name in ("spruce_a", "spruce_b"):
        u0, u1, v0, v1 = PK.sprite(name)
        a = np.asarray(PK.atlas().crop((int(u0 * N), int((1 - v1) * N), int(u1 * N), int((1 - v0) * N))), float)
        m = a[..., 3] > 128
        r, g, b = (a[..., i][m].mean() for i in range(3))
        assert b <= 0.72 * g and r <= 0.8 * g and g < 75, (r, g, b)
