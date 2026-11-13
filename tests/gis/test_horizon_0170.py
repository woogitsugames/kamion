"""ADR 0170: measured forest stands (authored `kind: forest_stand`), no pine in broadleaf stands, taller thuja walls,
spruce core. Synthetic inputs only (no region data)."""
import numpy as np
import pytest

from streetscape import plantings as PG
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


def test_spruce_has_a_dark_core_inside_the_cards():
    kit = PLT.Kit()
    h = 10.0
    PLT.spruce(kit, np.array([0.0, 0.0]), 0.0, h, "k")
    assert sum(len(t) for t in kit.T) == 4 * 2 + 3 * 2 + 12, "trunk + three cards + the 12-triangle core"
    core = kit.V[-1]
    W = 0.40 * h + 0.9
    assert np.hypot(core[:, 0], core[:, 1]).max() <= 0.18 * W + 1e-6, "core stays well inside the silhouette cards"
    occ = np.linalg.norm(kit.C[-1][:, :3] * 2 - 1, axis=1)
    assert occ.max() <= 0.5, "core is in the tree's own shade"


def test_near_lite_garden_tree_gets_core_and_shoulders():
    def tris(**kw):
        kit = PLT.Kit()
        PG.garden_tree(kit, np.array([0.0, 0.0]), 0.0, 2.5, 7.0, 1.3, "maple", "k", lite=True, cards=3, **kw)
        return sum(len(t) for t in kit.T)
    assert tris(core=True) - tris() == 16
    kit = PLT.Kit()
    PG.garden_tree(kit, np.array([0.0, 0.0]), 0.0, 2.5, 7.0, 1.3, "birch", "k", lite=True, cards=3, core=True)
    assert sum(len(t) for t in kit.T) == 10, "open habit (birch) keeps the light lite crown"
