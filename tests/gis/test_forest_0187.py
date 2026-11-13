"""ADR 0187: forest wall - spruce in the conifer stands, young-tree prototypes instead of scaled-down mature trees,
a stand mantle with rising height, forest floor plants near roads (High only), mantle strip of the HLOD edge texture.
Synthetic inputs + the shipped tree library."""
import json
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import shapely

from streetscape import forest_hlod as FH
from streetscape import vegetation as VG
from test_house_greenery_0163 import _forest_src

REPO = Path(__file__).resolve().parents[2]
VEG = REPO / "art-source" / "world" / "vegetation"
RING = [[0, 0], [200, 0], [200, 200], [0, 200]]
YOUNG = {"tree_pineyoung", "tree_birchyoung", "tree_shrub", "tree_spruce"}


def _place(src, road_x=None):
    hf = SimpleNamespace(x0=-10.0, y1=210.0)
    zc = np.zeros((221, 221))
    blocked = np.zeros_like(zc, bool)
    if road_x is not None:                       # a north-south road strip, 6 m wide
        blocked[:, int(road_x + 10) - 3:int(road_x + 10) + 3] = True
    rep = {}
    trees, _ = VG.place(src, (0.0, 0.0), hf, zc, blocked, rep, [])
    return trees, rep


def test_mixes_have_spruce_and_sum_to_one():
    for kat in ("iglasty", "mieszany", "liściasty", None):
        assert len(VG.MIX[kat]) == len(VG.SPECIES) and abs(sum(VG.MIX[kat]) - 1.0) < 1e-9, kat
    i = VG.SPECIES.index("spruce")
    assert VG.MIX["iglasty"][i] >= 0.15 and VG.MIX["mieszany"][i] >= 0.10 and VG.MIX["liściasty"][i] == 0.0
    assert VG.MIX["iglasty"][VG.SPECIES.index("pine")] > VG.MIX["iglasty"][i], "pine stays the dominant conifer"


def test_understorey_and_self_seeded_are_young_prototypes():
    src = _forest_src("F1:0", RING)
    src["bdot10k"]["OT_PTTR_A"] = [{"id": "G1", "props": {}, "geometry": {"coordinates": [[[0, -150], [200, -150], [200, -20], [0, -20]]]}}]
    hf = SimpleNamespace(x0=-10.0, y1=210.0)
    zc = np.zeros((381, 221))
    rep = {}
    trees, _ = VG.place(src, (0.0, 0.0), hf, zc, np.zeros_like(zc, bool), rep, [])
    under = [t for t in trees if t["src"].endswith(":under")]
    assert len(under) > 600 and {t["p"] for t in under} <= YOUNG, {t["p"] for t in under}
    assert all(t["v"] == VG.SPRUCE_OPEN for t in under if t["p"] == "tree_spruce"), "young spruce: boughs to the ground"
    assert max(t["h"] for t in under) <= 8.0
    seeded = [t for t in trees if t["src"].endswith(":self")]
    assert seeded and {t["p"] for t in seeded} <= {"tree_pineyoung", "tree_birchyoung", "tree_shrub"}
    assert max(t["h"] for t in seeded) <= 6.5, "no scaled-down mature trees (stick saplings) on self-seeded land"
    stand = [t for t in trees if t["src"] == "bdot:F1:0" and t["p"] == "tree_spruce"]
    assert stand and all(t["v"] in (0, 1) for t in stand), "canopy spruce uses the stand forms"
    for t in trees:
        assert t["v"] < VG.NVAR.get(t["p"][5:], 3), t


def test_mantle_height_rises_from_the_outline_into_the_stand():
    trees, rep = _place(_forest_src("F1:0", RING))
    poly = shapely.Polygon(RING)
    edge = [t for t in trees if t["src"].endswith(":edge")]
    d = np.array([poly.exterior.distance(shapely.Point(t["e"], t["n"])) * (1 if poly.contains(shapely.Point(t["e"], t["n"])) else -1)
                  for t in edge])
    h = np.array([t["h"] for t in edge])
    out, young, sub = h[d < 0], h[(d >= 0) & (d < 5)], h[d >= 5.5]
    assert len(out) > 100 and len(young) > 100 and len(sub) > 50
    assert out.max() <= 3.5 and np.median(out) < np.median(young) < np.median(sub) < 14.0
    assert sub.max() <= 15.0 < np.median([t["h"] for t in trees if t["src"] == "bdot:F1:0"])
    assert rep["forest_mantle"] == len(edge)


def test_forest_floor_only_near_roads_and_high_tier():
    trees, rep = _place(_forest_src("F1:0", RING), road_x=100)
    floor = [t for t in trees if t["p"] == "tree_floor"]
    assert len(floor) > 300 and rep["forest_floor"] == len(floor)
    assert all(t.get("tier") == "high" for t in floor), "Low keeps its instance count"
    assert max(abs(t["e"] - 100) for t in floor) <= VG.FLOOR_ROAD_M + 3.5
    assert all(0.4 <= t["h"] <= 0.95 for t in floor)
    assert not [t for t in trees if t["p"] != "tree_floor" and t.get("tier") == "high"]


def test_library_has_the_new_prototypes():
    meta = json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))
    tr = meta["trees"]
    for sp, n in (("spruce", 3), ("pineyoung", 2), ("birchyoung", 2), ("floor", 2)):
        for v in range(n):
            t = tr[f"tree_{sp}_{v}"]
            assert t["tris_lod1"] < t["tris_lod0"], (sp, v)
    # young trees are cheap: the understorey no longer costs a mature tree each
    assert max(tr[f"tree_{sp}_{v}"]["tris_lod0"] for sp in ("pineyoung", "birchyoung") for v in range(2)) <= 500
    assert max(tr[f"tree_spruce_{v}"]["tris_lod0"] for v in range(3)) <= 1000
    assert max(tr[f"tree_spruce_{v}"]["tris_lod1"] for v in range(3)) <= 520
    assert "impostor_views" not in tr["tree_floor_0"] and tr["tree_floor_0"]["tris_lod0"] <= 16
    assert (VEG / "leaves_spruce.png").exists()


def test_edge_texture_has_wall_and_mantle_rows():
    from PIL import Image
    meta = json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))
    for mix, f in meta["forest_hlod"].items():
        e = f["edge"]
        vm = FH.edge_v_main(e)
        assert vm == 0.75 and e["mantle"]["h_m"] == 8.0, mix
        a = np.asarray(Image.open(VEG / e["png"]).convert("RGBA"))[..., 3] > 127
        h = a.shape[0]
        cut = int(round(h * (1 - vm)))              # image row 0 = v 1 = ground line of the mantle strip
        mantle, wall = a[:cut], a[cut:]
        assert mantle[: cut // 4].mean() > 0.6, (mix, "mantle is dense at its ground line")
        assert mantle[-cut // 8:].mean() < 0.25 and wall[: wall.shape[0] // 10].mean() < 0.15, (mix, "sky sides meet")
        # review s20 0170 P1-1: no palisade of bare boles - the lowest 30 % of the wall picture is mostly covered by
        # the mantle and the understorey
        low = wall[int(wall.shape[0] * 0.70):]
        assert low.mean() > 0.80, (mix, low.mean())


def test_skirt_wall_reuses_the_edge_primitive():
    trees, _ = _place(_forest_src("F1:0", RING))
    cells = FH.build(trees, [(shapely.Polygon(RING), "conifer")], shapely.Polygon(), lambda e, n: np.zeros(len(np.atleast_1d(e))),
                     1024.0, {})
    assert cells
    v_seen = set()
    for c in cells.values():
        assert len(c["prims"]) <= 2, "canopy + one edge primitive (skirt adds no draw)"
        for p in c["prims"]:
            if p["mat"].startswith("forest_edge_"):
                v_seen |= set(np.round(p["UV"][:, 1], 3))
    assert 1.0 in v_seen and 0.75 in v_seen and 0.0 in v_seen


def test_tree_stand_override_is_a_low_stand_with_hlod_cells():
    """Authored wooded land outside the BDOT forest layer (allotment gardens): trees in the polygon, kept by
    open_ground, merged into forest HLOD cells at the stand's own height."""
    src = _forest_src("F1:0", [[900, 900], [901, 900], [901, 901]])           # no real forest
    ring = [[0, 0], [200, 0], [200, 200], [0, 200]]
    ov = [{"id": "rod", "kind": "tree_stand", "height_m": [4.0, 8.0], "spacing_m": 6.0,
           "mix": {"maple": 0.5, "spruce": 0.2, "shrub": 0.3}, "polygons_en": [ring]},
          {"id": "open", "kind": "open_ground", "polygons_en": [[[0, 0], [200, 0], [200, 60], [0, 60]]]}]
    hf = SimpleNamespace(x0=-10.0, y1=210.0)
    zc = np.zeros((221, 221))
    rep = {}
    trees, forests = VG.place(src, (0.0, 0.0), hf, zc, np.zeros_like(zc, bool), rep, ov)
    mine = [t for t in trees if t["src"].startswith("override:rod")]
    assert rep["tree_stands"] == [{"id": "rod", "area_m2": 40000.0, "trees": rep["tree_stands"][0]["trees"]}]
    assert len(mine) > 900 and any(t["n"] < 55 for t in mine), "open_ground keeps authored stands"
    canopy = [t["h"] for t in mine if t["p"] in ("tree_maple", "tree_spruce") and not t["src"].endswith(":edge")]
    assert 4.0 <= min(canopy) and max(canopy) <= 8.0
    assert all(shapely.Polygon(ring).area != f.area for f in forests), "ground mask stays grass"
    cells = FH.build(trees, rep["_forest_mix"], shapely.Polygon(), lambda e, n: np.zeros(len(np.atleast_1d(e))), 1024.0, {})
    assert len(cells) >= 6
    top = max(float(p["V"][:, 2].max()) for c in cells.values() for p in c["prims"] if p["mat"].startswith("forest_canopy"))
    assert 3.0 < top < 9.0, top
