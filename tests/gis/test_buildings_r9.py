"""ADR 0132 (buildings r9): house plots closer to the reference frames - review REVIEW-2026-11-12-s12-0124 P1-a..e, P2."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Point, box

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
REGION = REPO / "Data" / "Regions" / "bialystok-industrial-c"


def _kit():
    from streetscape import plots as PL
    return PL, PL.Kit()


class _Buf:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, V, UV, T, **k):
        self.parts.append((layer, mat, len(T)))


def test_hedge_is_rounded_wanders_and_carries_occlusion():
    """P1-b: no flat shelf that overhangs the sides; rounded crown, uneven top, dark foot."""
    PL, kit = _kit()
    a, b, n = np.array([0.0, 0.0]), np.array([12.8, 0.0]), np.array([0.0, -1.0])
    L = PL.hedge(kit, a, b, n, lambda q: 0.0, 1.8, "h", thick=0.7)
    V, UV, T, C = kit.out()
    assert L == pytest.approx(12.8)
    assert (C[:, 3] > 0.5).all()
    inner = (V[:, 0] > 1.0) & (V[:, 0] < 11.8)                                   # away from the narrowed ends
    half = np.abs(V[:, 1])
    top_band = inner & (V[:, 2] > 1.8 * 0.93)
    mid_band = inner & (V[:, 2] > 1.8 * 0.4) & (V[:, 2] < 1.8 * 0.85)
    # the cross-section narrows towards the crown line (no shelf wider than the sides), the foot is narrower too
    assert half[top_band].max() < 0.75 * half[mid_band].max()
    assert half[inner & (V[:, 2] < 0.05)].max() < half[mid_band].max()
    # the crown line is not a ruler: >= 5 cm of height variation between stations
    crown = V[inner & (half < 0.06) & (V[:, 2] > 1.6) & (V[:, 2] < 1.8 + 0.12)]
    assert np.ptp(crown[:, 2]) >= 0.05
    # occlusion: normal length ~0.4 at the foot, ~1 at the top
    occ = np.linalg.norm(C[:, :3] * 2 - 1, axis=1)
    assert occ[V[:, 2] < 0.05].max() < 0.5 and occ[top_band].min() > 0.95
    from streetscape import plot_kit as PK
    v0, v1 = PK.row("hedge")
    assert UV[:, 1].min() >= v0 - 1e-6 and UV[:, 1].max() <= v1 + 1e-6
    assert len(T) / (12.8 / PL.HEDGE_STEP_M) <= 26                              # triangle budget per station


def test_bush_and_fruit_tree_are_volumes_not_crossed_cards():
    """P1-e / P1-a: a dark core + sprays on the skin facing all round + a top; budget per plant."""
    PL, kit = _kit()
    PL.bush(kit, np.array([0.0, 0.0]), 0.0, 1.1, 2.2, "b")
    V, UV, T, C = kit.out()
    assert len(T) <= 40
    occ = np.linalg.norm(C[:, :3] * 2 - 1, axis=1)
    assert occ.min() < 0.4 and occ.max() > 0.84                                 # shaded core, lit skin
    nrm = (C[:, :3] * 2 - 1) / occ[:, None]
    az = np.degrees(np.arctan2(nrm[:, 1], nrm[:, 0]))[np.hypot(nrm[:, 0], nrm[:, 1]) > 0.3]
    assert len(np.unique(np.round(az / 45.0) % 8)) >= 6                         # skin normals look in >= 6 of 8 octants
    PL, kit = _kit()
    PL.fruit_tree(kit, np.array([0.0, 0.0]), 0.0, 4.2, "f", r=1.9)
    V, UV, T, C = kit.out()
    assert len(T) <= 80
    fol = C[:, 3] > 0.5
    assert V[fol][:, 2].max() <= 4.2 + 0.6 and V[fol][:, 2].min() >= 0.3         # a crown on a trunk, not a bush on the ground
    r = np.hypot(V[fol][:, 0], V[fol][:, 1])
    assert 1.5 <= r.max() <= 1.9 * 1.75                                         # the crown radius asked for (orthophoto)
    assert (~fol).sum() >= 8 + 12                                               # trunk + three limbs (hard surface)


def test_letter_box_has_a_post_and_a_contrasting_colour():
    """P1-d: the box of r16_drive_0 was black on a black 10 cm post in front of black lamellae."""
    PL, kit = _kit()
    from streetscape import plot_kit as PK
    g = {"m": np.array([0.0, 0.0]), "n": np.array([0.0, -1.0]), "t": np.array([1.0, 0.0]), "w": 1.0, "kind": "wicket", "ph": 0.05}
    PL.gate_geo(kit, g, "lamella", 1.7, 0.0, "g")
    V, UV, T, C = kit.out()
    box_v = (V[:, 2] > 0.97) & (V[:, 2] < 1.32) & (V[:, 1] < -0.06) & (V[:, 0] > 0.4)
    assert box_v.sum() >= 16
    assert not np.allclose(UV[box_v], np.asarray(PK.SWATCH["steel_graphite"]), atol=1e-4)      # not the frame colour
    assert not np.allclose(UV[box_v], np.asarray(PK.SWATCH["steel_black"]), atol=1e-4)
    post = (np.abs(V[:, 0] - 0.55) < 0.075) & (np.abs(V[:, 1]) < 0.075) & (V[:, 2] > 1.75)
    assert post.sum() >= 4 and np.ptp(V[post][:, 0]) >= 0.115                    # a 12 cm post rises behind the box


def test_free_fence_stub_is_dropped_and_front_is_kept():
    """P1-d: a side-fence stretch shorter than STUB_M with a free end (r16_drive_3) is not built."""
    from streetscape import plots as PL
    poly = box(0, 0, 20, 30)
    front = np.array([0.0, -1.0])
    plot = {"key": "k", "frame": (np.array([10.0, 15.0]), np.array([1.0, 0.0]), np.array([0.0, 1.0])), "front": front,
            "bbox": (-5.0, 5.0, -5.0, 5.0), "poly": poly, "front_style": "lamella", "side_style": "boards_grey",
            "front_h": 1.6, "side_h": 1.9, "drive_side": 0, "houses": ["a"], "house_pts": [np.array([10.0, 15.0])],
            "road_d": 3.0, "foot": box(5, 10, 15, 20), "gate_kind": "swing", "steps": []}
    near = PL._Near()
    # another fence closes the east side from y = 2.5 on, 1.5 m beyond it and parallel: only a 2.5 m stub would remain
    near.add([(np.array([21.5, 2.5]), np.array([21.5, 30.0]))])
    lay = PL.layout(plot, None, near)
    east = [r for r in lay["runs"] if not r["front"] and abs(r["a"][0] - 20.0) < 1e-6 and abs(r["b"][0] - 20.0) < 1e-6]
    assert not east and lay.get("stubs_dropped", 0) >= 1
    assert any(r["front"] for r in lay["runs"])
    lay2 = PL.layout(plot, None, PL._Near())
    assert sum(1 for r in lay2["runs"] if not r["front"]) >= 3 and not lay2.get("stubs_dropped")


def test_canopy_crowns_drive_trees_of_a_plot():
    """P1-a: crowns of the orthophoto become instances (big), kit trees (small), bushes; nothing on the house / driveway."""
    from streetscape import plots as PL
    poly, foot = box(0, 0, 24, 30), box(7, 12, 17, 22)
    front = np.array([0.0, -1.0])
    runs = [{"style": "picket" if float(e[4] @ front) > 0.7 else "chainlink", "h": 1.3, "a": e[0], "b": e[1], "n": e[4],
             "front": float(e[4] @ front) > 0.7} for e in PL._edges(poly)]
    plot = {"key": "k", "id": "x", "age": "old", "front_style": "picket", "side_style": "chainlink", "front_h": 1.3, "side_h": 1.3,
            "poly": poly, "foot": foot, "front": front, "house_polys": [foot], "door_zones": [], "hard": box(1, 0, 4, 20),
            "lay": {"runs": runs, "gate": None, "wicket": None, "wickets": []}, "drive": None}
    can = np.array([[20.0, 5.0, 3.5, 0, 60], [12.0, 26.0, 1.8, 0, 60], [3.0, 26.0, 0.9, 0, 60], [21.0, 25.0, 2.0, 1, 50],
                    [10.0, -4.5, 3.0, 0, 60], [12.0, 17.0, 3.0, 0, 60], [2.5, 8.0, 3.0, 0, 60], [10.0, -7.5, 3.0, 0, 60]])
    rp = {"plots": [plot], "drops": [], "canopy": can, "roads_poly": box(-50, -20, 80, -6), "carriage": box(-50, -20, 80, -8),
          "bpoly": foot}
    rep = {}
    out = PL.build(_Buf(), rp, lambda q: 0.0, None, rep)
    r = rep["plots"]
    trees = out["trees"]
    assert r["canopy"] is True and r["inst_trees"] == len(trees) >= 2
    for t in trees:
        q = Point(t["e"], t["n"])
        assert t["p"].startswith("tree_") and t["p"][5:] in dict(PL.INST_SPECIES) and 0 <= t["v"] <= 2
        assert PL.INST_H_M[t["p"][5:]][0] <= t["h"] <= PL.INST_H_M[t["p"][5:]][1]
        assert foot.distance(q) >= 1.8 - 1e-6 and not plot["hard"].contains(q)
        assert rp["carriage"].distance(q) >= PL.STREET_TREE_CW_M - 1e-6 and rp["roads_poly"].distance(q) >= 0.8 - 1e-6
    assert r["inst_trees_street"] == 1                         # (10, -4.5) stands on the strip; (10, -7.5) is on the road
    assert any(abs(t["e"] - 2.5) < 2.5 and abs(t["n"] - 8.0) < 2.5 for t in trees)        # moved off the driveway, not lost
    assert r["fruit_trees"] >= 1 and r["spruces"] >= 1 and r["bushes"] >= 1
    assert 0 < r["overgrowth"] <= PL.OVERGROWTH["old"][1]
    rep2 = {}
    PL.build(_Buf(), dict(rp, canopy=None), lambda q: 0.0, None, rep2)          # rule fallback without the product
    assert rep2["plots"]["canopy"] is False


def test_canopy_product_is_current_and_sane():
    """The committed crowns come from the orthophoto named in ortho.json and are separated as the method says."""
    from streetscape import plot_canopy as PCN
    f = REGION / "plot_canopy.json"
    if not f.exists():
        pytest.skip("no canopy product")
    doc = json.loads(f.read_text(encoding="utf-8"))
    meta = json.loads((REGION / "ortho.json").read_text(encoding="utf-8"))
    assert doc["ortho_sha256"] == meta["sha256"] and doc["version"] == PCN.VERSION
    assert doc["params"]["G_MIN"] == PCN.G_MIN and doc["params"]["STD_MIN"] == PCN.STD_MIN
    C = np.asarray(doc["crowns"], float)
    assert len(C) > 500 and C.shape[1] == 5
    assert (C[:, 2] >= PCN.R_SHRUB_M - 0.01).all() and (C[:, 2] <= PCN.R_MAX_M + 0.01).all()
    assert 0.05 < doc["counts"]["crown_cover_of_zone"] < 0.5
    from scipy.spatial import cKDTree
    kd = cKDTree(C[:, :2])
    for i, j in kd.query_pairs(2 * PCN.R_MAX_M):
        assert np.hypot(*(C[i, :2] - C[j, :2])) >= 0.8 * (C[i, 2] + C[j, 2]) - 0.3


def test_plots_report_of_the_built_region():
    """The generated report of the region (after build_world): data-driven trees are there, the kit stays in budget."""
    qa = json.loads((REGION / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))["plots"]
    if "inst_trees" not in qa:
        pytest.skip("region not rebuilt with ADR 0132 yet")
    assert qa["canopy"] is True
    assert qa["inst_trees_kept"] >= 0.3 * qa["plots"]          # review P1-a: grown trees, >= 0.3 per plot on average
    assert qa["overgrowth"] >= 0.5 * qa["plots"] and qa["bushes"] + qa["shrubs"] >= 2 * qa["plots"]
    assert qa["fence_step_zone_hits"] == 0
    assert qa["tris"] <= 120_000                               # kit triangles of the whole region (ADR 0124: 52 k)
