"""Confirmed crowns can replace synthetic broadleaf trees without adding banks."""
from copy import deepcopy
from types import SimpleNamespace

import numpy as np
import pytest

from streetscape.vegetation import _replace_orthophoto_trees, place

ORIGIN = np.array([777995., 596223.])


def context():
    hf = SimpleNamespace(x0=-350., y1=-150., z=np.zeros((129, 129)))
    return hf, np.full(hf.z.shape, 130.), np.zeros(hf.z.shape, bool)


def donor():
    return dict(p="tree_birch", v=2, e=-229.7, n=-209.61, z=130.51, h=4.6,
                yaw=4.063, lean=.005, src="bdot:synthetic-zone:self")


def run(items=None, blocked=None, origin=ORIGIN):
    hf, zc, mask = context()
    if blocked is not None:
        mask = blocked
    report = {}
    result = _replace_orthophoto_trees(deepcopy(items if items is not None else [donor()]),
                                      origin, hf, zc, mask, report)
    return result, report


def test_confirmed_crown_replaces_a_synthetic_tree_stably_without_new_instances():
    result, report = run()
    assert result == run()[0]
    assert len(result) == 1
    new, old = result[0], donor()
    assert new["src"].startswith("ortho:gugik-2024:")
    assert (new["e"], new["n"]) == (-233., -202.)
    assert new["z"] == 130. and 12.5 <= new["h"] <= 15.
    assert all(new[k] == old[k] for k in ("p", "v", "yaw", "lean"))
    assert report["orthophoto_trees"]["new_instances"] == 0
    assert report["orthophoto_trees"]["replaced_self_seeded"] == 1


def test_root_uncertainty_search_stays_outside_blocked_and_within_three_metres():
    hf, _, mask = context()
    mask[52, 117] = True  # centre (-233, -202)
    original = mask.copy()
    result, _ = run(blocked=mask)
    new = result[0]
    assert new["src"].startswith("ortho:")
    assert 0 < np.hypot(new["e"]+233., new["n"]+202.) <= 3.
    i, j = round(new["e"]-hf.x0), round(hf.y1-new["n"])
    assert not mask[j, i]
    assert np.array_equal(mask, original)


def test_fully_blocked_area_is_never_overridden():
    _, _, mask = context()
    result, report = run(blocked=np.ones_like(mask))
    assert result == [donor()]
    assert report["orthophoto_trees"]["blocked"] == 4
    assert report["orthophoto_trees"]["placed"] == 0


def test_recorded_tree_cannot_be_used_as_a_synthetic_donor():
    old = {**donor(), "src": "osm:node/1"}
    result, report = run([old])
    assert result == [old]
    assert report["orthophoto_trees"]["new_instances"] == 0
    assert report["orthophoto_trees"]["placed"] == 0


def test_existing_tree_near_the_crown_prevents_a_duplicate():
    mapped = {**donor(), "e": -233., "n": -202., "src": "osm:node/2"}
    result, report = run([donor(), mapped])
    assert result == [donor(), mapped]
    assert report["orthophoto_trees"]["already_mapped"] == 1


@pytest.mark.parametrize("prototype", ["tree_pine", "tree_shrub"])
def test_conifers_and_shrubs_are_not_relabelled_as_mature_broadleaf(prototype):
    old = {**donor(), "p": prototype}
    assert run([old])[0] == [old]


def test_replacement_cannot_cross_the_importers_64m_cell_boundary():
    old = {**donor(), "e": -221., "n": -202.}
    assert run([old])[0] == [old]


def test_source_points_cannot_leak_into_an_unrelated_region():
    result, report = run(origin=np.zeros(2))
    assert result == [donor()]
    assert "orthophoto_trees" not in report


def test_empty_world_does_not_gain_new_draw_banks_for_unmatched_points():
    hf, zc, blocked = context()
    src = {"bdot10k": {k: [] for k in (
        "OT_PTLZ_A", "OT_PTRK_A", "OT_OIPR_P", "OT_OIPR_L", "OT_PTNZ_A", "OT_PTTR_A")},
        "osm": {"nodes": [], "ways": [], "areas": []}}
    report = {}
    trees, _ = place(src, ORIGIN, hf, zc, blocked, report)
    assert trees == []
    assert report["orthophoto_trees"]["deferred_budget"] == 4
