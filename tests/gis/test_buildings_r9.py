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
    # another fence closes the east side from y = 4.2 on, 1.5 m beyond it and parallel: only a 2.5 m stub would remain
    near.add([(np.array([21.5, 4.2]), np.array([21.5, 30.0]))])
    lay = PL.layout(plot, None, near)
    east = [r for r in lay["runs"] if not r["front"] and abs(r["a"][0] - 20.0) < 1e-6 and abs(r["b"][0] - 20.0) < 1e-6]
    assert not east and lay.get("stubs_dropped", 0) >= 1
    assert any(r["front"] for r in lay["runs"])
    lay2 = PL.layout(plot, None, PL._Near())
    assert sum(1 for r in lay2["runs"] if not r["front"]) >= 3 and not lay2.get("stubs_dropped")


def _diag_deg(run, front, frame_ax):
    # deviation of the run direction from the nearest frame axis (same metric as plots._diag_deg)
    t = (run["b"] - run["a"]) / np.hypot(*(run["b"] - run["a"]))
    return float(np.degrees(np.arccos(np.clip(max(abs(float(t @ front)), abs(float(t @ frame_ax))), 0.0, 1.0))))


def _plot_with(poly, drive_side=1):
    return {"key": "k", "frame": (np.array([10.0, 15.0]), np.array([1.0, 0.0]), np.array([0.0, 1.0])),
            "front": np.array([0.0, -1.0]), "bbox": (-5.0, 5.0, -5.0, 5.0), "poly": poly,
            "front_style": "lamella", "side_style": "boards_grey", "front_h": 1.6, "side_h": 1.9,
            "drive_side": drive_side, "houses": ["a"], "house_pts": [np.array([10.0, 15.0])], "road_d": 3.0,
            "foot": box(5, 10, 15, 20), "gate_kind": "swing", "steps": []}


def test_skewed_corner_tooth_is_dropped_but_a_long_diagonal_boundary_stays():
    """M30 / r16_drive_3: a clipped plot polygon leaves a short zigzag tooth on a side edge; joined at both ends,
    so the free-end stub rule alone does not catch it. A tooth (shorter than STUB_M, deviating from both frame
    axes by > SKEW_DROP_DEG) is not built; a long skewed run follows a real boundary and stays."""
    from shapely.geometry import Polygon
    from streetscape import plots as PL
    front, ax = np.array([0.0, -1.0]), np.array([1.0, 0.0])
    # east edge with a 45 deg tooth at (21, 11) - the r16_drive_3 shape
    zig = Polygon([(0, 0), (20, 0), (20, 10), (21, 11), (20, 12), (20, 30), (0, 30)])
    lay = PL.layout(_plot_with(zig), None, PL._Near())
    assert lay.get("stubs_dropped", 0) >= 2
    assert all(_diag_deg(r, front, ax) <= PL.SKEW_DROP_DEG for r in lay["runs"])
    assert any(r["front"] for r in lay["runs"])                                   # the front stays closed
    assert sum(1 for r in lay["runs"] if not r["front"]) >= 3                     # the straight sides stay
    # ADR 0159 (review of PR #38): the two teeth are replaced by their chord - no 2 m hole in the east fence line
    assert lay.get("teeth_bridged") == 1
    chord = [r for r in lay["runs"] if abs(r["a"][0] - 20.0) < 1e-6 and abs(r["b"][0] - 20.0) < 1e-6
             and {round(float(r["a"][1])), round(float(r["b"][1]))} == {10, 12}]
    assert len(chord) == 1 and not chord[0]["front"]
    # a long diagonal side (a road clearance line), 22.4 m at 26.6 deg: kept
    diag = Polygon([(0, 0), (20, 0), (30, 20), (30, 30), (0, 30)])
    lay2 = PL.layout(_plot_with(diag), None, PL._Near())
    long_diag = [r for r in lay2["runs"] if _diag_deg(r, front, ax) > PL.SKEW_DROP_DEG]
    assert len(long_diag) == 1 and np.hypot(*(long_diag[0]["b"] - long_diag[0]["a"])) > PL.STUB_M
    assert not lay2.get("stubs_dropped")


@pytest.fixture(scope="module")
def region_fence_runs():
    """The fence runs of every plot of the built region, planned from the repo data only (tracked region files,
    a flat synthetic heightfield - Data/raw is not needed): roads -> plots -> layout."""
    import shapely
    from roads import pipeline
    from roads.profile import Heightfield
    from streetscape import buildings_mesh as BM
    from streetscape import paved as PV
    from streetscape import plots as PL
    from streetscape import sources as SRC

    rid = "bialystok-industrial-c"
    region = pipeline.load_region(rid)
    origin = (region["origin"]["x"], region["origin"]["y"])
    tm = json.loads((pipeline.REGIONS / rid / "terrain.json").read_text(encoding="utf-8"))
    h, w = tm["samples"][1], tm["samples"][0]
    wd = pipeline.build(rid, hf=Heightfield(np.full((h, w), 131.0), tm["bbox"], origin))
    road_parts = [p for p in wd.buf.parts if p.layer == "road"]
    roads_poly = PV.road_footprint_polygon(road_parts)
    carriage = PV.road_footprint_polygon([p for p in road_parts if p.mat.startswith("road_")])
    src = SRC.load(rid)
    overrides = pipeline.load_overrides(rid)
    blds = BM.load(json.loads((pipeline.REGIONS / rid / "buildings.geojson").read_text(encoding="utf-8")), origin, overrides)
    yards = []
    for f in src["bdot10k"]["OT_PTPL_A"]:
        if f["props"].get("materialnawierzchni") != "grunt naturalny":
            yards += [g for g in getattr(shapely.make_valid(PV._poly_local(f["geometry"]["coordinates"], origin)), "geoms",
                                         [shapely.make_valid(PV._poly_local(f["geometry"]["coordinates"], origin))])
                      if g.geom_type == "Polygon"]
    bpoly = shapely.union_all([b["poly"] for b in blds])
    rp = PL.region_plan(blds, roads_poly, carriage, yards, src, origin, bpoly, net=wd.net)
    return rp["plots"]


def test_region_data_no_short_diagonal_fence_panels(region_fence_runs):
    """M30 / r16_drive_3, on the region data: no built run shorter than STUB_M deviates from the plot's frame axes
    by more than SKEW_DROP_DEG (the clipped-corner teeth are gone); the only > 15 deg panels left are long ones
    following a road clearance line. Measured on the repo data: 43 such panels before the rule, 7 after."""
    from streetscape import plots as PL
    total = diag = 0
    for p in region_fence_runs:
        c, eu, ev = p["frame"]
        front = p["front"]
        ax = ev if abs(float(front @ eu)) > 0.5 else eu
        for r in p["lay"]["runs"]:
            total += 1
            d = _diag_deg(r, front, ax)
            if d > 15.0:
                diag += 1
                assert np.hypot(*(r["b"] - r["a"])) >= PL.STUB_M or r["front"], (p["id"], d)   # only long / gate-post-anchored
    assert total > 500 and diag <= 7          # ADR 0159: an upper bound - the exact count moves with the region data
    r16 = [p for p in region_fence_runs if p["id"] == "bdot:2BE4B431-AD81-1BF0-E053-CC2BA8C0D140"]
    assert len(r16) == 1
    c, eu, ev = r16[0]["frame"]
    ax = ev if abs(float(r16[0]["front"] @ eu)) > 0.5 else eu
    assert all(_diag_deg(r, r16[0]["front"], ax) <= 15.0 for r in r16[0]["lay"]["runs"])          # r16_drive_3 itself


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
    root = json.loads((REGION / "generated" / "streetscape_qa.json").read_text(encoding="utf-8"))
    qa = root["plots"]
    if "inst_trees" not in qa:
        pytest.skip("region not rebuilt with ADR 0132 yet")
    assert qa["canopy"] is True
    # review P1-a: grown trees, >= 0.3 per plot on average. ADR 0163: the grown garden trees are kit trees of
    # streetscape.plantings.garden_trees (every tier), no longer instances of the tree library (High / Medium only).
    grown = root["garden_trees"]["trees"] if "garden_trees" in root else qa["inst_trees_kept"]
    assert grown >= 0.3 * qa["plots"]
    assert qa["overgrowth"] >= 0.5 * qa["plots"] and qa["bushes"] + qa["shrubs"] >= 2 * qa["plots"]
    assert qa["fence_step_zone_hits"] == 0
    assert qa["tris"] <= 120_000 and qa["inst_trees_kept"] <= 3 * qa["plots"]                               # kit triangles of the whole region (ADR 0124: 52 k)


def test_low_kit_variant_is_lighter_and_selfcontained():
    """ADR 0132: the Low / Medium chunk variant gets its own plot kit (Kit.low): High-only parts are left out, lite
    variants replace the expensive plants, indices stay valid."""
    PL, kit = _kit()
    p = np.array([0.0, 0.0])
    kit.tag = "fence"
    kit.box(p, np.array([1.0, 0.0]), 0.1, 0.1, 0.0, 1.0, PL.PK.SWATCH["trunk"])
    kit.low = False
    PL.thuja(kit, p + 2, 0.0, 2.4, 0.4, ("t", 1))
    PL.fruit_tree(kit, p + 5, 0.0, 4.0, ("f", 1), r=1.6)
    PL.bush(kit, p + 8, 0.0, 0.9, 1.6, ("b", 1))
    kit.low = "only"
    PL.thuja_lite(kit, p + 2, 0.0, 2.4, 0.4, ("t", 1))
    PL.fruit_tree_lite(kit, p + 5, 0.0, 4.0, ("f", 1), r=1.6)
    kit.low = True
    hi, lo = kit.out(), kit.out(low=True)
    assert len(lo[2]) == 10 + 14 + 10 and len(hi[2]) > 10 + 39 + 60
    for V, UV, T, C in (hi, lo):
        assert T.min() == 0 and T.max() == len(V) - 1 and len(UV) == len(V) == len(C)
    assert sum(kit.by.values()) == len(hi[2]) and sum(kit.by_low.values()) == len(lo[2])
    # the lite plants keep the height and the footprint of the full ones (same silhouette from the cab)
    zh, zl = hi[0][:, 2].max(), lo[0][:, 2].max()
    assert abs(zh - zl) < 0.35
