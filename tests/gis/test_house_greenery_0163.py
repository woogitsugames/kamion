"""ADR 0163: greenery of the house streets by the G7 measurements (research/g7-street-greenery/README.md, table
"Parametry dla generatora"). Replaces the ADR 0154 tests (test_garden_fronts.py): no widened / raised library crowns,
garden trees and front hedges are kit geometry on every tier."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import LineString, Point, Polygon, box
from shapely.ops import unary_union

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REGION = REPO / "Data" / "Regions" / "bialystok-industrial-c"

from roads.meshing import MeshBuf                     # noqa: E402
from streetscape import plantings as PT               # noqa: E402
from streetscape import plot_kit as PK                # noqa: E402
from streetscape import plots as PLT                  # noqa: E402
from streetscape.vegetation import garden_canopies    # noqa: E402

# G7 # 4: crown radius of the garden trees along the house streets (orthophoto, n = 131)
R_Q1, R_MED, R_Q3, R_P90 = 1.5, 1.95, 2.55, 3.05
HOUSE_STREETS = ["Kowieńska", "Lidzka", "Skidelska", "Wołkowyska", "Świsłocka", "Wileńska", "Grodzieńska"]   # G7 # 2


def _plot(pid, style="picket", key=None, gate=True):
    key = key or f"qa-{pid}"
    g = {"m": np.array([0.0, -20.0]), "n": np.array([0.0, -1.0]), "t": np.array([1.0, 0.0]), "w": 4.0} if gate else None
    return {"id": pid, "key": key, "age": "old", "front_style": style, "front_h": 1.3, "house_h": 8.0,
            "poly": Polygon([(-20, -20), (20, -20), (20, 20), (-20, 20)]), "foot": Polygon([(-5, 0), (5, 0), (5, 10), (-5, 10)]),
            "hard": Polygon([(-2.5, -20), (2.5, -20), (2.5, 0), (-2.5, 0)]) if gate else None, "front": np.array([0.0, -1.0]),
            "lay": {"runs": [{"a": np.array([-20.0, -20.0]), "b": np.array([20.0, -20.0]), "n": np.array([0.0, -1.0]), "front": True}],
                    "gate": g, "wicket": None, "wickets": []}}


def _buf():
    """a buffer that already holds the plot kit of the test plot on both chunk variants (as plots.build leaves it)"""
    buf = MeshBuf()
    for layer in (PLT.KIT_LAYER, PLT.KIT_LAYER_LOW):
        kit = PLT.Kit()
        for x in (-10, 10):
            for y in (-10, 10):
                kit.box(np.array([x, y]), np.array([1.0, 0.0]), 10.0, 10.0, 139.8, 141.0, [0.0, 0.0])
        o = kit.out()
        buf.add(layer, "plot_kit", o[0], o[1], o[2], COL=o[3])
    return buf


def _key_of_kind(kind):
    """a plot key whose single-plot plan gives `kind`"""
    for i in range(4000):
        p = _plot("t", key=f"k{i}")
        rp = {"plots": [p, *[_plot(f"o{j}", key=f"o{j}") for j in range(19)]]}
        if PT.plan_house_greenery(rp)["t"] == kind:
            return f"k{i}", rp
    raise AssertionError(kind)


def test_front_plan_is_the_g7_quota():
    """G7 # 15-18: 40 % hedge >= 1.2 m (70 % thuja), 25 % low shrubs, 35 % fence only - quotas, not coin flips."""
    styles = ["picket", "chainlink", "concrete", "wall", "bars", "boards_brown", "lamella", "brick_picket"]
    rp = {"plots": [_plot(f"p{i}", style=styles[i % len(styles)]) for i in range(100)]}
    rep = {}
    kinds = PT.plan_house_greenery(rp, rep)
    n = {k: sum(1 for v in kinds.values() if v == k) for k in ("thuja", "broadleaf", "low", "none")}
    assert n == {"thuja": 28, "broadleaf": 12, "low": 25, "none": 35}
    assert rep["garden_plan"]["plots_with_front"] == 100 and rp["garden_trees"] == []
    by = {p["id"]: p["front_style"] for p in rp["plots"]}
    # what does not rise above a fence goes behind the see-through ones
    assert all(by[i] in PLT.SEE_THROUGH for i, k in kinds.items() if k == "low")
    assert all(by[i] in PLT.SEE_THROUGH for i, k in kinds.items() if k == "broadleaf")
    assert PT.plan_house_greenery(rp) == kinds                                   # deterministic
    no_front = _plot("nf")
    no_front["lay"]["runs"][0]["front"] = False
    assert PT.plan_house_greenery({"plots": [no_front]}) == {"nf": "none"}


def test_thuja_wall_has_the_g7_size_and_stays_in_the_live_row():
    """G7 # 19: 2.0-2.5 m high, 0.8-1.2 m wide, behind the fence; Low is the same wall with fewer triangles."""
    a, b, n = np.array([0.0, 0.0]), np.array([24.0, 0.0]), np.array([0.0, -1.0])
    out, body = {}, {}
    for low in (False, True):
        kit = PLT.Kit()
        assert PT.thuja_hedge(kit, a, b, n, lambda q: 100.0, 2.3, "h", thick=1.0, low=low) == pytest.approx(24.0)
        out[low], body[low] = kit.out(), len(kit.V[0])                          # the wall body, then the tip cards
    V, UV, T, C = out[False]
    inner = (V[:, 0] > 2.0) & (V[:, 0] < 22.0)
    # ADR 0170: the body's crest stands 0.5-0.6 m under the nominal height, the plants' tip cards rise to it (+ <= 0.45 m)
    assert 2.3 - 0.25 <= V[inner][:, 2].max() - 100.0 <= 2.3 + 0.45
    assert 0.8 <= np.ptp(V[inner][:, 1]) <= 1.25
    assert (C[:, 3] > 0.5).all()                                                 # foliage vertices (normal + occlusion)
    occ = np.linalg.norm(C[:, :3] * 2 - 1, axis=1)
    assert occ[V[:, 2] < 100.1].max() < 0.5 < occ[V[:, 2] > 102.0].min()         # dark foot, lit shoulders
    v0, v1 = PK.row("thuja")
    ub = UV[:body[False]]
    assert ub[:, 1].min() >= v0 and ub[:, 1].max() <= v1
    assert ub[:, 0].min() >= 0.0 and ub[:, 0].max() <= PK.THUJA_GREEN_U          # never the browned stretch of the row
    # drawn 1 : 1 on High: v advances by the arc length of the cross-section (1 m of twigs per row)
    side = np.argsort(V[:5, 2])
    dz = np.hypot(np.diff(V[:5][side][:, 2]), np.diff(V[:5][side][:, 1]))
    dvv = np.abs(np.diff(UV[:5][side][:, 1])) / (v1 - v0)
    assert np.allclose(dvv[:3], np.minimum(dz[:3], 0.9), atol=0.12)
    # review s17 0170 P2: a row of plants, not a ruled box - one tip card per plant (~1 m) on High too. Build 4 drew the
    # plants as stations (61 triangles / m) and broke the stretch_04 2 M frame cap: High <= 17 triangles per metre
    kit = PLT.Kit()
    PT.thuja_hedge(kit, a, b, n, lambda q: 100.0, 2.3, "h", thick=1.0)
    assert 20 <= len(kit.V) - 1 <= 26 and all(len(v) == 4 for v in kit.V[1:])       # body + a quad per plant
    assert len(T) <= 17.0 * 24
    # Low (ADR 0132 budget; was <= 4.6 / m): the sparse wall + one tip card per plant, <= 8 triangles per metre
    assert len(out[True][2]) <= 0.6 * len(T) and len(out[True][2]) <= 8.0 * 24
    assert out[True][0][:, 2].max() == pytest.approx(V[:, 2].max(), abs=0.35)
    # Low: the twig row is no longer stretched ~2.8x over the wall's side (four rows, each <= 1.3 m of wall per row)
    Vl, UVl = out[True][0], out[True][1]
    side = np.argsort(Vl[:5, 2])
    dzl = np.hypot(np.diff(Vl[:5][side][:, 2]), np.diff(Vl[:5][side][:, 1]))
    dvl = np.abs(np.diff(UVl[:5][side][:, 1])) / (v1 - v0)
    assert (dzl[:3] / np.maximum(dvl[:3], 1e-6) <= 1.3).all()


def test_corner_plants_are_taller_but_never_above_three_metres():
    a, b, n = np.array([0.0, 0.0]), np.array([20.0, 0.0]), np.array([0.0, -1.0])
    kit = PLT.Kit()
    PT.thuja_hedge(kit, a, b, n, lambda q: 0.0, 2.2, "c", thick=1.0, raise_ends=(0.8, 0.0))
    V = kit.out()[0]
    assert 2.6 < V[V[:, 0] < 1.9][:, 2].max() <= 3.0 + 0.15
    assert V[V[:, 0] > 8.0][:, 2].max() < 2.2 + 0.45                              # the plants' tip cards (ADR 0170)


def test_front_hedge_keeps_gate_free_stays_in_the_plot_and_is_on_low_too():
    key, rp = _key_of_kind("thuja")
    buf = _buf()
    rep = PT.front_gardens(buf, rp, lambda q: 140.0, {})
    mine = [p for p in buf.parts if p.src == "plot:t:g7-front"]
    assert {p.layer for p in mine} == {"plots", "plots_low"} and all(p.mat == "plot_kit" for p in mine)
    for part in mine:
        assert not np.any((np.abs(part.V[:, 0]) < 2.5) & (part.V[:, 1] < -15.0)), "gate / driveway blocked"
        assert part.V[:, 1].min() >= -20.0 and np.abs(part.V[:, 0]).max() <= 20.0          # inside the plot, behind the fence
        assert part.V[:, 1].max() <= -20.0 + 0.6 + 1.2 + 0.1                               # gap + width (G7 # 19)
        assert 2.4 - 0.2 <= part.V[:, 2].max() - 140.0 <= 4.0 + 0.2                        # ADR 0170: 2.4-3.6 m, corner <= 4.0
    row = next(x for x in rep["list"] if x["plot"] == "t")
    assert row["kind"] == "thuja" and 2.4 <= row["h_m"] <= 3.6 and 0.8 <= row["w_m"] <= 1.2
    assert 0.6 <= row["m"] / row["front_m"] <= 0.92                              # G7 # 21: ~80 % of the front
    assert 0 < rep["tris_low"] < rep["tris_high"]


def test_low_shrub_strip_and_broadleaf_hedge():
    for kind in ("low", "broadleaf"):
        key, rp = _key_of_kind(kind)
        buf = _buf()
        rep = PT.front_gardens(buf, rp, lambda q: 140.0, {})
        mine = [p for p in buf.parts if p.src == "plot:t:g7-front"]
        assert {p.layer for p in mine} == {"plots", "plots_low"}, kind
        top = max(p.V[:, 2].max() for p in mine) - 140.0
        if kind == "low":
            assert rep["shrubs"] >= 4 and 0.5 <= top <= 1.2 * 1.3 + 0.1
        else:
            assert 1.2 - 0.1 <= top <= 1.5 + 0.45                                # hedge + its loose shoots
        for part in mine:
            assert not np.any((np.abs(part.V[:, 0]) < 2.3) & (part.V[:, 1] < -15.0)), "gate blocked"


def test_nothing_is_built_into_a_new_renderer_group():
    """Budget: plot greenery joins the chunk groups of the plots; it never opens a draw call of its own."""
    key, rp = _key_of_kind("thuja")
    buf = MeshBuf()
    rep = PT.front_gardens(buf, rp, lambda q: 140.0, {})
    assert not buf.parts and rep["skipped"]["new_renderer_group"] >= 1 and rep["plots"]["thuja"] == 0
    rp["garden_trees"] = [{"plot": "t", "key": ("k", 1), "p": np.array([8.0, -12.0]), "r": 2.0, "in_plot": True, "near": True,
                           "kind": "broadleaf"}]
    out = PT.garden_trees(buf, rp, lambda q: 140.0, {})
    assert not buf.parts and out["trees"] == 0 and out["skipped"]["new_renderer_group"] == 1


def test_a_tree_far_off_the_plots_of_its_chunk_does_not_stretch_the_group():
    """Budget (route frames g3b_rondo_put_approach / g3b_ext34_s1658, build 5: +1 draw on Low): a garden tree may grow a
    chunk group only GROUP_GROW_M past the plot kit it holds, else the group passes the frustum test of new cameras."""
    buf = _buf()                                       # plot kit within E / N -20..20
    near = {"plot": "t", "key": ("k", 1), "p": np.array([8.0, -12.0]), "r": 2.0, "in_plot": True, "near": True, "kind": "broadleaf"}
    far = dict(near, key=("k", 2), p=np.array([8.0, -60.0]))
    rp = {"plots": [], "garden_trees": [near, far]}
    out = PT.garden_trees(buf, rp, lambda q: 140.0, {})
    assert out["trees"] == 1 and out["skipped"]["group_bounds_growth"] == 1
    assert out["list"][0]["n"] == -12.0


@pytest.mark.parametrize("species", ["linden", "maple", "chestnut", "ash", "birch"])
def test_tree_size_follows_g7(species):
    """G7 # 4, 6, 7, 12, 13: the typical garden tree (crown radius 1.5-2.55 m) is 5-8 m, the crown starts low, no tree
    exceeds its species ceiling (birch 20 m, not the 23 m of ADR 0154)."""
    hs, bases = [], []
    for i in range(200):
        for r in (R_Q1, R_MED, R_Q3):
            H, cb, sprite = PT.tree_dims(r, species, ("t", i))
            hs.append(H)
            bases.append(cb / H)
            assert cb >= 1.3 and sprite in (PT.HABIT[species], "crown_ovoid")
            assert species not in ("birch", "linden") or sprite == PT.HABIT[species]
            wm, hm = PK.SPRITE_M[sprite]
            st = 2 * r / (H - cb) / (wm / hm)
            assert PT.CARD_STRETCH[0] - 0.02 <= st <= PT.CARD_STRETCH[1] + 0.02     # the card keeps its habit
    assert 4.5 <= np.median(hs) <= 8.5, np.median(hs)
    assert np.max(bases) <= 0.33 and np.median(bases) <= 0.27                       # 0.15 H, but >= 1.3 m on a small tree
    for i in range(50):
        H, cb, _ = PT.tree_dims(6.5, species, ("big", i))
        assert H <= PT.G7["ceiling_m"][species] and 0.14 <= cb / H <= 0.2
    assert PT.G7["ceiling_m"]["birch"] == 20.0
    H, cb, _ = PT.tree_dims(R_MED, species, ("s", 1), in_plot=False)
    assert cb >= 1.6                                                              # open ground beside the street


def test_crown_cards_have_the_habit_of_the_species():
    """G7 # 13 / 14: linden ovate (W / H 0.5-0.6 of the tree), maple round (0.65-0.75), birch narrow and open."""
    aspect = {k: PK.SPRITE_M[k][0] / PK.SPRITE_M[k][1] for k in ("crown_ovoid", "crown_round", "crown_birch")}
    assert 0.58 <= aspect["crown_ovoid"] <= 0.68 and 0.68 <= aspect["crown_round"] <= 0.8 and 0.4 <= aspect["crown_birch"] <= 0.5
    im = np.asarray(PK.atlas())
    y0, h = PK.ROW_Y["tall"]
    cover = {}
    for name in aspect:
        x0, w = PK._SPR_X[name]
        a = im[y0:y0 + h, x0:x0 + w, 3] >= 128
        cover[name] = a.mean()
        rows = np.nonzero(a.any(1))[0]
        cols_low = a[int(h * 0.80):int(h * 0.97)].any(0).sum() / w
        cols_mid = a[int(h * 0.35):int(h * 0.65)].any(0).sum() / w
        assert rows.min() <= 0.08 * h and rows.max() >= 0.97 * h                   # the crown fills the card top to foot
        assert cols_mid >= 0.9                                                    # widest in the middle ...
        assert cols_low >= (0.5 if name != "crown_birch" else 0.3)                # ... and still wide low down: no umbrella
        px = PK.SPRITE_M[name][0] * PK.SPRITE_M[name][1]
        assert w * h / px >= 1800                                                 # >= 42 px / m on both axes
    assert cover["crown_ovoid"] > 0.6 and cover["crown_round"] > 0.6            # dense (zwarta)
    assert 0.2 < cover["crown_birch"] < 0.55                                    # open (otwarta)
    assert PK.sprite("tree_a") == PK.sprite("crown_round")                     # plots.big_tree (rule path) follows


def test_garden_tree_geometry_full_and_lite():
    for sp in ("linden", "maple", "birch", "ash"):
        H, cb, sprite = PT.tree_dims(R_MED, sp, ("g", sp))
        full, lite = PLT.Kit(), PLT.Kit()
        PT.garden_tree(full, np.array([0.0, 0.0]), 10.0, R_MED, H, cb, sp, ("g", sp))
        PT.garden_tree(lite, np.array([0.0, 0.0]), 10.0, R_MED, H, cb, sp, ("g", sp), lite=True)
        for kit, cap in ((full, 44), (lite, 10)):
            V, UV, T, C = kit.out()
            fol = C[:, 3] > 0.5
            assert len(T) <= cap
            assert V[fol][:, 2].min() - 10.0 == pytest.approx(cb, abs=0.2)        # the crown starts at the crown base ...
            assert (V[fol][:, 2].min() - 10.0) / H <= 0.33                        # ... low: no bare stem under an umbrella
            assert V[:, 2].max() - 10.0 == pytest.approx(H, rel=0.06)
            assert np.ptp(V[fol][:, 0]) == pytest.approx(2 * R_MED, rel=0.3)      # as wide as the crown on the orthophoto
            assert V[~fol][:, 2].min() < 10.0 and V[~fol][:, 2].max() > 10.0 + cb  # the stem reaches into the crown
        u = full.out()[1][:, 0]
        s0, s1 = PK.SPRITE[sprite]
        assert ((u >= s0 - 1e-6) & (u <= s1 + 1e-6)).sum() >= 12                  # three crossed cards of the habit
    dense, open_ = PLT.Kit(), PLT.Kit()
    PT.garden_tree(dense, np.array([0.0, 0.0]), 0.0, 2.0, 6.5, 1.3, "linden", "d")
    PT.garden_tree(open_, np.array([0.0, 0.0]), 0.0, 2.0, 8.0, 1.3, "birch", "d")
    assert len(dense.out()[2]) > len(open_.out()[2]) + 15                         # core + sprays only in the dense habits


def _crowns(n, seed=7):
    rng = np.random.default_rng(seed)
    r = np.clip(rng.lognormal(np.log(R_MED), 0.33, n), 1.25, 6.5)
    return [{"plot": "t", "key": ("c", i), "p": np.array([-18.0 + 36.0 * rng.random(), 12.0 + 6.0 * rng.random()]), "r": float(r[i]),
             "in_plot": True, "near": i % 2 == 0, "kind": "broadleaf"} for i in range(n)]


def test_garden_trees_are_kit_geometry_on_both_tiers_with_the_g7_mix():
    rp = {"plots": [_plot("t")], "garden_trees": _crowns(600)}
    buf = _buf()
    rep = PT.garden_trees(buf, rp, lambda q: 140.0, {})
    assert rep["trees"] + len(rep["conifers"]) == 600 and rep["skipped"] == {}
    n = rep["trees"]
    mine = [p for p in buf.parts if p.src == "plot:t:g7-trees"]
    assert {p.layer for p in mine} == {"plots", "plots_low"}                       # Low / Medium draw them too (A16)
    # ADR 0170: lite trees near the street carry a dark core + two shoulder sprays (+ 16 triangles)
    assert 0 < rep["tris_low"] <= 26 * 600 and rep["tris_low"] < rep["tris_high"] <= 66 * 600
    share = {k: v / n for k, v in rep["species"].items()}
    for sp, want in PT.G7["broadleaf_mix"].items():                               # G7 # 11
        assert abs(share.get(sp, 0.0) - want) <= 0.07, (sp, share)
    assert all(t["r_m"] <= PT.FRUIT_R_MAX_M for t in rep["list"] if t["species"] == "fruit")
    hs = np.array([t["h_m"] for t in rep["list"]])
    assert 5.0 <= np.median(hs) <= 8.0                                           # the typical tree of the house streets
    assert (hs <= 25.0).all() and max(t["h_m"] for t in rep["list"] if t["species"] == "birch") <= 20.0
    cb = np.array([t["crown_base_m"] / t["h_m"] for t in rep["list"] if t["crown_base_m"] is not None])
    assert cb.max() <= 0.33 and np.median(cb) <= 0.27
    # deterministic
    buf2 = _buf()
    PT.garden_trees(buf2, {"plots": [_plot("t")], "garden_trees": _crowns(600)}, lambda q: 140.0, {})
    for a, b in zip(buf.parts, buf2.parts):
        assert np.array_equal(a.V, b.V) and np.array_equal(a.T, b.T) and np.array_equal(a.COL, b.COL)


def test_conifers_are_topped_up_to_the_g7_share_from_the_darkest_crowns():
    """G7 # 8-10: 25 % of the garden trees are conifers (spruce / columnar thuja 4-6 m); the detector's 11 % is topped up
    from the darkest small and medium crowns, never from the big ones."""
    crowns = _crowns(400)
    rng = np.random.default_rng(3)
    for t in crowns:
        t["luma"] = float(rng.uniform(40, 110))
    rep = PT.garden_trees(_buf(), {"plots": [_plot("t")], "garden_trees": crowns}, lambda q: 140.0, {})
    con = rep["conifers"]
    assert len(con) + rep["trees"] == 400 and abs(len(con) / 400 - 0.25) <= 0.01
    assert all(c["converted"] and c["r_m"] <= PT.CONIFER_R_MAX_M for c in con)
    lum = {(round(float(t["p"][0]), 2), round(float(t["p"][1]), 2)): t["luma"] for t in crowns}
    dark = np.mean([lum[(c["e"], c["n"])] for c in con])
    assert dark < np.mean([lum[(t["e"], t["n"])] for t in rep["list"]]) - 15
    th = [c for c in con if c["kind"] == "thuja"]
    assert 0.2 <= len(th) / len(con) <= 0.5 and all(4.0 <= c["h_m"] <= 6.0 for c in th)
    assert all(c["h_m"] <= 14.0 * 1.1 for c in con if c["kind"] == "spruce")


def test_no_garden_tree_on_top_of_a_region_tree():
    crowns = _crowns(20)
    region = [{"e": float(crowns[3]["p"][0]) + 1.0, "n": float(crowns[3]["p"][1])}]
    rep = PT.garden_trees(_buf(), {"plots": [_plot("t")], "garden_trees": crowns}, lambda q: 140.0, {}, region_trees=region)
    assert rep["skipped"]["region_tree_within_2.5m"] >= 1
    assert rep["trees"] + len(rep["conifers"]) == 20 - rep["skipped"]["region_tree_within_2.5m"]


def test_library_instances_are_only_capped_never_widened_or_raised():
    """ADR 0154 widened (x 1.2-1.35) and raised library crowns to 11-20 m; ADR 0163 leaves what is still an instance
    alone except for the G7 ceiling (birch 20 m)."""
    rp = {"plots": [_plot("test")]}
    birch = {"p": "tree_birch", "v": 1, "h": 23.0, "e": 0.0, "n": 0.0, "z": 140.0, "src": "plot:test:rule", "tier": "high"}
    maple = {"p": "tree_maple", "v": 2, "h": 11.0, "e": 0.0, "n": 0.0, "z": 140.0, "src": "plot:test:rule", "tier": "high"}
    forest = {**birch, "src": "forest:sample"}
    before = [dict(x) for x in (birch, maple, forest)]
    rep = {}
    out = garden_canopies([birch, maple, forest], rp, rep)
    assert [birch, maple, forest] == before
    assert out[0]["h"] == 20.0 and out[1] == maple and out[2] == forest
    assert all("garden_canopy_width" not in t for t in out)
    assert rep["garden_canopies"]["capped"] == 1 and rep["garden_canopies"]["added_instances"] == 0


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **k):
        self.parts.append((layer, mat, len(T), k.get("src", "")))


def _canopy_plot():
    poly, foot = box(0, 0, 24, 30), box(7, 12, 17, 22)
    front = np.array([0.0, -1.0])
    runs = [{"style": "picket" if float(e[4] @ front) > 0.7 else "chainlink", "h": 1.3, "a": e[0], "b": e[1], "n": e[4],
             "front": float(e[4] @ front) > 0.7} for e in PLT._edges(poly)]
    plot = {"key": "k", "id": "x", "age": "old", "front_style": "picket", "side_style": "chainlink", "front_h": 1.3, "side_h": 1.3,
            "poly": poly, "foot": foot, "front": front, "house_polys": [foot], "door_zones": [], "hard": box(1, 0, 4, 20),
            "lay": {"runs": runs, "gate": None, "wicket": None, "wickets": []}, "drive": None}
    can = np.array([[20.0, 5.0, 3.5, 0, 60], [12.0, 26.0, 1.8, 0, 60], [3.0, 26.0, 0.9, 0, 60], [21.0, 25.0, 2.0, 1, 50],
                    [10.0, -4.5, 3.0, 0, 60], [12.0, 17.0, 3.0, 0, 60], [2.5, 8.0, 3.0, 0, 60], [10.0, -7.5, 3.0, 0, 60],
                    [18.0, -4.0, 1.6, 0, 60]])
    return {"plots": [plot], "drops": [], "canopy": can, "roads_poly": box(-50, -20, 80, -6), "carriage": box(-50, -20, 80, -8),
            "bpoly": foot}


def test_plots_build_hands_broadleaf_crowns_and_the_front_over_to_the_plan():
    """With the plan, plots.build neither instances library trees nor builds its own front hedge; it records the
    broadleaf crowns (also the small ones on the street strip, which it used to drop) and still meshes the conifers."""
    rp = _canopy_plot()
    PT.plan_house_greenery(rp)
    rp["front_green"]["x"] = "thuja"
    rep = {}
    out = PLT.build(_Buf(), rp, lambda q: 0.0, None, rep)
    r = rep["plots"]
    assert out["trees"] == [] and r["inst_trees"] == 0 and r["fruit_trees"] == 0
    assert r["hedge_m"] == 0 and r["spruces"] >= 1
    plan = rp["garden_trees"]
    broad = [t for t in plan if t["kind"] == "broadleaf"]
    assert len(broad) >= 5 and any(t["kind"] == "conifer" and t.get("meshed") for t in plan)
    strip = [t for t in broad if not t["in_plot"]]
    assert {round(t["r"], 1) for t in strip} == {3.0, 1.6}                        # (10, -7.5) is on the road: not planted
    for t in broad:
        q = Point(*t["p"])
        assert rp["plots"][0]["foot"].distance(q) >= 1.8 - 1e-6 and not rp["plots"][0]["hard"].contains(q)
        assert rp["carriage"].distance(q) >= PLT.STREET_TREE_CW_M - 1e-6
    # without the plan plots.build is what it was (ADR 0132)
    rep2 = {}
    out2 = PLT.build(_Buf(), _canopy_plot(), lambda q: 0.0, None, rep2)
    assert len(out2["trees"]) >= 2 and rep2["plots"]["fruit_trees"] >= 1


def test_overhanging_crowns_get_their_stem_behind_the_fence():
    """G7 # 1 / # 2: a crown in front of a plot, near the carriageway, is a garden tree whose crown hangs over the fence -
    not a street tree: the stem goes >= 1 m inside the fence. Crowns away from every street are not claimed."""
    rp = _canopy_plot()
    rp["canopy"] = np.array([[10.0, -4.5, 3.0, 0, 60], [18.0, -3.0, 1.6, 0, 60], [20.0, -2.0, 2.0, 1, 50], [10.0, -7.5, 3.0, 0, 60],
                             [12.0, 45.0, 3.0, 0, 60], [40.0, 60.0, 3.0, 0, 60]])
    rp["garden_trees"] = []
    rep = {"skipped": {}}
    out = PT.claim_street_crowns(rp, rep)
    poly = rp["plots"][0]["poly"]
    assert len(out) == 4 and {t["kind"] for t in out} == {"broadleaf", "conifer"}       # the two far crowns are left out
    open_ground = [t for t in out if t["plot"] is None]      # (10, -7.5): further than 6 m from the plot, beside the road
    assert len(open_ground) == 1 and not open_ground[0]["in_plot"]
    assert rp["carriage"].distance(Point(*open_ground[0]["p"])) >= PLT.STREET_TREE_CW_M - 1e-6
    assert rp["roads_poly"].distance(Point(*open_ground[0]["p"])) >= 0.8
    for t in out:
        if t["plot"] is None:
            continue
        q = Point(*t["p"])
        assert t["in_plot"] and t["moved"] and t["claimed"] and t["plot"] == "x"
        assert poly.contains(q) and poly.exterior.distance(q) >= PT.BEHIND_FENCE_M - 1e-6
        assert not rp["plots"][0]["hard"].buffer(0.3).contains(q) and rp["plots"][0]["foot"].distance(q) >= 1.8 - 1e-6
    P = np.array([t["p"] for t in out])
    d = np.hypot(*(P[:, None] - P[None]).transpose(2, 0, 1)) + np.eye(len(P)) * 99
    assert d.min() >= PT.TREE_GAP_M - 1e-6
    # an entry plots.build recorded on the strip is moved the same way; one it meshed itself is not touched
    rp["garden_trees"] = [{"plot": "x", "key": ("k", "cn", 10.0, -4.5), "p": np.array([10.0, -4.5]), "r": 3.0, "in_plot": False,
                           "near": True, "kind": "broadleaf"},
                          {"plot": "x", "key": ("k", "cn", 21.0, 25.0), "p": np.array([21.0, 25.0]), "r": 2.0, "in_plot": True,
                           "near": False, "kind": "conifer", "meshed": True}]
    out2 = PT.claim_street_crowns(rp, {"skipped": {}})
    first = next(t for t in out2 if t["key"] == ("k", "cn", 10.0, -4.5))
    assert first["moved"] and poly.contains(Point(*first["p"]))
    assert not any(t.get("meshed") for t in out2)


def _qa():
    path = REGION / "generated" / "streetscape_qa.json"
    qa = json.loads(path.read_text(encoding="utf-8"))
    if "garden_trees" not in qa or "garden_plan" not in qa:
        pytest.skip("region not rebuilt with ADR 0163 yet")
    return qa


def test_region_fronts_match_g7_shares():
    qa = _qa()
    plan, fr = qa["garden_plan"], qa["garden_fronts"]
    n = plan["plots_with_front"]
    assert n >= 60
    built_hedge = fr["plots"]["thuja"] + fr["plots"]["broadleaf"]
    assert 0.33 <= built_hedge / n <= 0.45, built_hedge / n                       # G7 # 15: 40 % (25-55)
    assert 0.60 <= fr["plots"]["thuja"] / built_hedge <= 0.80                     # G7 # 18: 70 % thuja
    assert 0.15 <= fr["plots"]["low"] / n <= 0.30                                 # G7 # 16: 25 % (15-30)
    th = [x for x in fr["list"] if x["kind"] == "thuja"]
    assert all(2.4 <= x["h_m"] <= 3.6 and 0.8 <= x["w_m"] <= 1.2 for x in th)     # G7 # 19
    cover = sum(x["m"] for x in th) / sum(x["front_m"] for x in th)
    assert 0.6 <= cover <= 0.92, cover                                            # G7 # 21: ~80 % of the front
    assert fr["tris_low"] > 0                                                     # eye-level mass on Low (A16) too


def test_region_garden_trees_match_g7_density_and_size():
    """G7 # 2: 10 garden trees / 100 m of street axis (9-12) within 8 m of the axis of the house streets; # 1: none of
    them is a street tree of the region's library; # 4-6: the typical tree is 5-8 m."""
    qa = _qa()
    gt = qa["garden_trees"]
    assert gt["trees"] >= 300 and 0 < gt["tris_low"] <= 13_500 and gt["tris_high"] <= 34_000
    assert qa["plots"]["inst_trees_kept"] == 0                                    # no stone pines of the library in gardens
    origin = np.array([777995.0, 596223.0])
    graph = json.loads((REGION / "roads.graph.json").read_text(encoding="utf-8"))
    axes = unary_union([LineString(np.asarray(e["geometry"], float)[:, :2] - origin) for e in graph["edges"]
                        if e["attrs"].get("name", {}).get("v") in HOUSE_STREETS])
    pts = [Point(t["e"], t["n"]) for t in gt["list"]] + [Point(t["e"], t["n"]) for t in gt["conifers"]]
    per100 = {d: sum(1 for p in pts if axes.distance(p) <= d) / axes.length * 100.0 for d in (8.0, 12.0)}
    # the orthophoto has 9.9 crowns / 100 m within 8 m and 12.7 within 12 m. The stems stand behind the fences (G7 # 1:
    # no tree in the road strip), >= 1 m inside, so part of the 8 m crowns are stems of the 8-12 m band.
    assert 7.0 <= per100[8.0] <= 12.0, per100
    assert 10.5 <= per100[12.0] <= 14.0, per100
    assert gt["moved_behind_fence"] >= 50
    # none in the road strip of the house streets: every stem is behind a fence or >= 3 m from the carriageway
    assert all(t["moved"] or not t["claimed"] or t["street_strip"] for t in gt["list"])
    hs = np.array([t["h_m"] for t in gt["list"]])
    assert 5.0 <= np.median(hs) <= 8.0 and np.mean(hs >= 12.0) <= 0.15, (np.median(hs), np.mean(hs >= 12.0))
    assert np.mean([t["r_m"] >= 4.0 for t in gt["list"]]) <= 0.06                 # G7 # 5: big crowns are the exception
    assert max(t["h_m"] for t in gt["list"] if t["species"] == "birch") <= 20.0
    share = {k: v / gt["trees"] for k, v in gt["species"].items()}
    for sp, want in PT.G7["broadleaf_mix"].items():
        assert abs(share.get(sp, 0.0) - want) <= 0.08, (sp, share)
    con = len(gt["conifers"]) / (len(gt["conifers"]) + gt["trees"])
    assert 0.20 <= con <= 0.30, con                                               # G7 # 8: 25 % (15-40); detector alone: 11 %
    kinds = [t.get("kind") for t in gt["conifers"] if t.get("converted")]
    assert kinds and 0.2 <= kinds.count("thuja") / len(kinds) <= 0.5              # G7 # 9: columnar thuja 35 %


# ---------------------------------------------------------------- forest clearing (horizon of 303305 / 320215 / 454716)
def _forest_src(fid, ring):
    empty = {k: [] for k in ("OT_PTRK_A", "OT_OIPR_P", "OT_OIPR_L", "OT_PTNZ_A", "OT_PTTR_A")}
    return {"bdot10k": {"OT_PTLZ_A": [{"id": fid, "props": {"rodzaj": "las", "kategoria": "iglasty"},
                                        "geometry": {"coordinates": [ring]}}], **empty},
            "osm": {"nodes": [], "areas": []}}


def _place(src, overrides):
    from types import SimpleNamespace
    from streetscape import vegetation as VG
    hf = SimpleNamespace(x0=-10.0, y1=210.0)
    zc = np.zeros((221, 221))
    rep = {}
    trees, forests = VG.place(src, (0.0, 0.0), hf, zc, np.zeros_like(zc, bool), rep, overrides)
    return trees, forests, rep


def test_forest_clearing_removes_trees_keeps_clumps_and_reports_stale():
    ring = [[0, 0], [200, 0], [200, 200], [0, 200]]
    src = _forest_src("F1:0", ring)                    # BDOT ids carry a ":<part>" index, the override names the object
    ov = [{"id": "clr", "kind": "forest_clearing", "target": {"bdot": "F1"},
           "cleared_epsg2180": [[[100, -10], [210, -10], [210, 210], [100, 210]]],
           "keep_epsg2180": [[[140, 90], [160, 90], [160, 110], [140, 110]]]},
          {"id": "gone", "kind": "forest_clearing", "target": {"bdot": "NOPE"}, "cleared_epsg2180": [[[0, 0], [1, 0], [1, 1]]]}]
    t0, _, _ = _place(src, [])
    t1, forests, rep = _place(src, ov)
    E = np.array([t["e"] for t in t1])
    N = np.array([t["n"] for t in t1])
    clump = (E > 141) & (E < 159) & (N > 91) & (N < 109)
    assert not np.any((E > 103) & ~clump & ~((E > 137) & (E < 163) & (N > 87) & (N < 113))), "tree left in the clearing"
    assert clump.sum() >= 5, "the authored keep clump must stay a stand of trees"
    assert sum(1 for t in t0 if t["e"] < 97) == sum(1 for t in t1 if t["e"] < 97), "the stand outside must not change"
    assert rep["forest_clearings"]["applied"][0]["area_m2_after"] < 0.6 * rep["forest_clearings"]["applied"][0]["area_m2_before"]
    assert [s["id"] for s in rep["forest_clearings"]["stale"]] == ["gone"]
    assert rep["_forest_cleared"] and rep["_forest_cleared"][0].area > 15000


def test_region_forest_clearing_targets_a_live_bdot_polygon():
    from roads import pipeline
    from streetscape import vegetation as VG
    ov = [o for o in pipeline.load_overrides("bialystok-industrial-c") if o.get("kind") == "forest_clearing"]
    assert ov, "ADR 0163 forest clearing override missing"
    clear = VG.forest_clearings(ov, (777995.0, 596223.0))
    cut, _ = clear["2BE4B432-6BC0-1BF0-E053-CC2BA8C0D140"]
    assert 4000 < cut.area < 8000                     # traced sand pit minus the three clumps (orthophoto 2024)
    assert cut.bounds[0] > 215                        # nothing west of E 215 local is cleared


def test_region_forest_clearing_is_applied_in_the_built_region():
    fc = _qa()["vegetation"]["forest_clearings"]
    assert not fc["stale"], fc["stale"]
    assert [a["id"] for a in fc["applied"]] == ["bdot-forest-6bc0-sand-clearing"]
    assert fc["applied"][0]["trees_removed"] > 100
