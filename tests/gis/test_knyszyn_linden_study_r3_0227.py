"""Experimental local opt-in; this is not visual or budget acceptance."""
import numpy as np
import pytest

from streetscape import plantings as pt, plots, vegetation


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, vertices, uv, triangles, **kwargs):
        self.parts.append((layer, mat, vertices, uv, triangles, kwargs["COL"]))


def run():
    group = {"id": "test-linden-study", "kind": "tree_groups", "form": "kit",
             "crown_model": "linden_study_r3", "species": {"linden": 1},
             "points_en": [[-677, -195.2, 17, 10, "linden"]]}
    buf, report = Buffer(), {}
    pt.authored_trees(buf, [group], lambda _: 125., report)
    return group, buf, report["authored_trees"]


def test_r3_opt_in_deterministic_valid_atlas_and_separate_lods():
    group, one, rep = run()
    _, two, rep2 = run()
    assert vegetation._tree_point_overrides([group]) == []
    assert rep == rep2 and rep["trees"] == 1
    assert rep["tris_high"] == 1440 and rep["tris_low"] == 16
    assert [p[0] for p in one.parts] == ["plots", "plots_low"]
    u0, u1, v0, v1 = plots.PK.sprite("shrub_a")
    trunk = np.array(plots.PK.SWATCH["trunk"])
    for left, right in zip(one.parts, two.parts):
        layer, mat, v, uv, t, color = left
        assert mat == "plot_kit"
        for a, b in zip(left[2:], right[2:]):
            np.testing.assert_array_equal(a, b)
        assert np.isfinite(v).all() and np.isfinite(uv).all() and np.isfinite(color).all()
        assert t.min() >= 0 and t.max() < len(v)
        assert np.linalg.norm(np.cross(v[t[:,1]]-v[t[:,0]], v[t[:,2]]-v[t[:,0]]), axis=1).min() > 1e-9
        leaf = color[:, 3] == 1
        assert leaf.any() and (~leaf).any()
        if layer == "plots":
            assert np.all((uv[leaf,0] >= u0) & (uv[leaf,0] <= u1))
            assert np.all((uv[leaf,1] >= v0) & (uv[leaf,1] <= v1))
        np.testing.assert_allclose(uv[~leaf], np.tile(trunk, ((~leaf).sum(), 1)))


def test_study_low_is_identical_to_previous_garden_trial():
    group, study, _ = run()
    group["crown_model"] = "garden_trial"
    previous, report = Buffer(), {}
    pt.authored_trees(previous, [group], lambda _: 125., report)
    old_low = next(p for p in previous.parts if p[0] == "plots_low")
    new_low = next(p for p in study.parts if p[0] == "plots_low")
    assert old_low[:2] == new_low[:2] == ("plots_low", "plot_kit")
    for before, after in zip(old_low[2:], new_low[2:]):
        np.testing.assert_array_equal(before, after)


def test_r3_rejects_wrong_species_and_invalid_size():
    with pytest.raises(ValueError, match="positive finite"):
        pt._linden_study_r3(plots.Kit(), np.array([0., 0.]), 0., 0., 10., False)
    with pytest.raises(ValueError, match="requires linden"):
        pt.authored_trees(Buffer(), [{"id":"x", "kind":"tree_groups", "form":"kit",
            "crown_model":"linden_study_r3", "points_en":[[0,0,17,10,"maple"]]}],
            lambda _: 0., {})
