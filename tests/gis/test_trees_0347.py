"""ADR 0347: road clearance of trees from the MEASURED library silhouette (critic build #8, P0 #3, t=2260).

Blender-free. The corridor test reads the built tiles (Data/raw/derived/<tile>/world: instances_*.json +
road_carriage.wkt written by build_world.py) and is skipped for tiles that were not rebuilt with ADR 0347.
"""
import json
import sys
from pathlib import Path

import pytest
import shapely
from shapely.geometry import box

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools/worldgen"))
from streetscape import tree_crown_profile as TCP      # noqa: E402
from streetscape import vegetation as VG                # noqa: E402

ROAD = box(-7.0, -200.0, 0.0, 200.0)            # carriageway edge at e = 0 (trees stand at e > 0)


def tree(p, e, h, v=0, n=0.0):
    return {"p": p, "v": v, "e": e, "n": n, "h": h, "src": "t"}


def test_profile_table_matches_the_glb():
    assert TCP.build()["source_sha256"] == TCP.table()["source_sha256"], "run: python -m streetscape.tree_crown_profile --write"


def test_measured_reach_exceeds_the_nominal_envelope_of_adr_0308():
    # the reason for 0347: the nominal radii underestimated the meshes by 25-35 %
    for sp in ("linden", "maple", "birch", "alder"):
        for v in range(3):
            n = f"tree_{sp}_{v}"
            href = TCP.table()["protos"][n]["href_m"]
            nominal = VG.CROWN_FORM[sp][0] * href
            assert TCP.table()["protos"][n]["r_cum"][-1] > nominal * 1.15, n
    # young trunk-only reach of a pine below the gauge is the trunk
    assert TCP.low_radius("tree_pine_0", 1.0, VG.CLEAR_H_M) < 1.0
    # monotone in the limit
    assert TCP.low_radius("tree_linden_0", 0.8, 3.0) <= TCP.low_radius("tree_linden_0", 0.8, 6.0)


def test_nothing_changes_when_the_tree_already_stands_clear():
    T = [tree("tree_linden", 12.0, 12.5), tree("tree_pine", 2.0, 18.0), tree("tree_floor", 0.5, 0.6, n=3.0)]
    rep = {}
    out = VG.road_clearance(T, ROAD, rep)
    assert out == T
    assert rep["road_clearance"]["violations_after"] == 0


def test_close_tree_is_moved_off_the_road_when_the_cell_is_free():
    t = tree("tree_linden", 3.0, 6.0)               # reach ~2.9 m + 0.5: needs ~0.4 m more
    rep = {}
    out = VG.road_clearance([t], ROAD, rep, free_fn=lambda P: [True] * len(P))
    assert rep["road_clearance"]["shifted"] == 1
    assert out[0]["h"] == 6.0 and out[0]["e"] > 3.0 and out[0]["n"] == 0.0
    assert VG.clearance_violations(out, ROAD, tol=0.011) == []
    assert t["e"] == 3.0, "records are copied"


def test_shift_refused_by_a_blocked_cell_falls_back_to_shrinking_or_removal():
    t = tree("tree_linden", 3.0, 6.0)
    rep = {}
    out = VG.road_clearance([t], ROAD, rep, free_fn=lambda P: [False] * len(P))
    r = rep["road_clearance"]
    assert r["shifted"] == 0 and r["violations_after"] == 0
    assert (r["lowered"] == 1 and out[0]["e"] == 3.0 and out[0]["h"] < 6.0) or (r["removed"] == 1 and not out)


def test_tree_on_the_asphalt_or_hopeless_is_removed():
    out = VG.road_clearance([tree("tree_maple", -2.0, 12.0), tree("tree_linden", 0.6, 14.0)], ROAD, {})
    assert out == []


def test_gauge_height_is_respected_not_the_whole_crown():
    # tall pine: foliage from ~5 m: only the trunk counts below the gauge; reach below the gauge ~0.7 m: 1.5 m from the edge is fine
    out = VG.road_clearance([tree("tree_pine", 1.5, 18.0)], ROAD, {})
    assert len(out) == 1 and out[0]["e"] == 1.5 and out[0]["h"] == 18.0


def test_deterministic_and_order_kept():
    T = [tree("tree_linden", 3.0 + 0.4 * i, 8.0 + i, v=i % 3, n=float(i)) for i in range(12)]
    a = VG.road_clearance(T, ROAD, {}, free_fn=lambda P: [True] * len(P))
    b = VG.road_clearance(T, ROAD, {}, free_fn=lambda P: [True] * len(P))
    assert a == b
    assert VG.clearance_violations(a, ROAD, tol=0.011) == []
    assert [t["n"] for t in a] == sorted(t["n"] for t in a)


def test_species_without_a_mesh_use_the_nominal_envelope():
    out = VG.road_clearance([tree("tree_willow", 2.0, 8.0)], ROAD, {}, free_fn=lambda P: [True] * len(P))
    assert VG.clearance_violations(out, ROAD, tol=0.011) == []


def _corridor_tiles():
    trips = json.loads((REPO / "game/Assets/_Project/Gameplay/Resources/Nav/nav_trips.json").read_text(encoding="utf-8"))["trips"]
    return next(t for t in trips if t["id"] == "tykocin")["tiles"]


@pytest.mark.parametrize("tile", _corridor_tiles())
def test_corridor_to_tykocin_no_tree_enters_the_clearance_box(tile):
    """Prism: asphalt polygon + 0.5 m, height 0..4.7 m. Every tree instance of every chunk stays out of it."""
    world = REPO / "Data/raw/derived" / tile / "world"
    wkt = world / "road_carriage.wkt"
    if not wkt.exists():
        pytest.skip(f"{tile}: not rebuilt with ADR 0347 (no road_carriage.wkt)")
    carriage = shapely.from_wkt(wkt.read_text(encoding="utf-8"))
    trees = []
    for fn in sorted(world.glob("instances_*.json")):
        trees += [i for i in json.loads(fn.read_text(encoding="utf-8"))["instances"] if i["p"].startswith("tree_")]
    assert trees, tile
    bad = VG.clearance_violations(trees, carriage, tol=0.05)       # 0.03 simplify + 0.01 rounding
    assert not bad, f"{tile}: {len(bad)} trees in the clearance box, first {[(trees[i]['p'], trees[i]['e'], trees[i]['n'], round(d, 2), round(r, 2)) for i, d, r in bad[:3]]}"
