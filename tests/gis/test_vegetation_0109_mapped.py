"""D51: orthophoto-confirmed broadleaf points must respect world placement guards."""
from types import SimpleNamespace

import numpy as np

from streetscape.vegetation import place


ORIGIN = np.array([777995., 596223.])
PREFIX = "ortho:gugik-2024:g3-b-120:"


def context(block_first=False, osm_duplicate=False):
    hf = SimpleNamespace(x0=-350., y1=-150., z=np.zeros((129, 129)))
    height = np.full(hf.z.shape, 130.)
    blocked = np.zeros(hf.z.shape, bool)
    if block_first:
        blocked[28, 73] = True  # first measured crown centre, local (-277, -178)
    src = {"bdot10k": {k: [] for k in (
        "OT_PTLZ_A", "OT_PTRK_A", "OT_OIPR_P", "OT_OIPR_L", "OT_PTNZ_A", "OT_PTTR_A")},
        "osm": {"nodes": [], "ways": [], "areas": []}}
    if osm_duplicate:
        src["osm"]["nodes"].append(dict(osm_node=1, tags={"natural": "tree", "genus": "Tilia"},
            geometry={"type": "Point", "coordinates": [777718., 596045.]}))
    return src, hf, height, blocked


def run(**kwargs):
    src, hf, height, blocked = context(**kwargs)
    report = {}
    trees, _ = place(src, ORIGIN, hf, height, blocked, report)
    return trees, report


def test_confirmed_roadside_crowns_are_present_stable_and_grounded():
    trees, report = run()
    again, _ = run()
    assert trees == again
    assert len(trees) == 4
    assert all(t["src"].startswith(PREFIX) for t in trees)
    assert {(t["e"], t["n"]) for t in trees} == {
        (-277., -178.), (-263., -185.), (-251., -193.), (-233., -202.)}
    assert all(t["z"] == 130. and 12.5 <= t["h"] <= 15. for t in trees)
    assert report["orthophoto_trees"]["placed"] == 4


def test_mapped_point_cannot_override_a_blocked_surface():
    trees, report = run(block_first=True)
    assert len(trees) == 3
    assert not any((t["e"], t["n"]) == (-277., -178.) for t in trees)
    assert report["orthophoto_trees"]["blocked"] == 1


def test_existing_osm_tree_wins_over_an_orthophoto_duplicate():
    trees, report = run(osm_duplicate=True)
    assert len(trees) == 4
    assert any(t["src"] == "osm:node/1" for t in trees)
    assert report["orthophoto_trees"]["placed"] == 3
    assert report["orthophoto_trees"]["deduplicated"] == 1


def test_source_points_cannot_leak_into_an_unrelated_region():
    src, hf, height, blocked = context()
    trees, _ = place(src, np.zeros(2), hf, height, blocked, {})
    assert trees == []
