import copy

import numpy as np
import pytest

from streetscape import plantings as PT, vegetation as VG


class Buffer:
    def __init__(self):
        self.vertices = []
        self.parts = []

    def add(self, layer, mat, V, UV, T, src="", **kwargs):
        self.vertices.append(np.asarray(V))


def group(**kwargs):
    return {"id": "trial", "kind": "tree_groups", "form": "kit",
            "points_en": [[5, 5, 17, 10, "linden"], [20, 5, 17, 10, "linden"]],
            "species": {"linden": 1.0}, **kwargs}


def build(o):
    buf, report = Buffer(), {}
    PT.authored_trees(buf, [o], lambda p: 100., report)
    return buf, report["authored_trees"]


def test_trial_has_both_lods_and_does_not_create_tree_instances():
    o = group(crown_model="garden_trial")
    buf, rep = build(o)
    assert rep["trees"] == 2 and rep["tris_high"] > rep["tris_low"] > 0
    assert all(x["crown_model"] == "garden_trial" and x["species"] == "linden" for x in rep["list"])
    vertices = np.vstack(buf.vertices)
    assert vertices[:, 2].min() < 100 and vertices[:, 2].max() > 115
    assert VG._tree_point_overrides([o]) == []


def test_default_and_explicit_kit_are_identical():
    default_buf, default = build(group())
    explicit_buf, explicit = build(group(crown_model="kit"))
    assert default == explicit
    assert len(default_buf.vertices) == len(explicit_buf.vertices)
    assert all(np.array_equal(a, b) for a, b in zip(default_buf.vertices, explicit_buf.vertices))


def test_invalid_model_or_species_fails():
    with pytest.raises(ValueError, match="unknown crown_model"):
        build(group(crown_model="invalid"))
    bad = copy.deepcopy(group(crown_model="garden_trial"))
    bad["points_en"][0][4] = "shrub"
    with pytest.raises(ValueError, match="does not support species"):
        build(bad)
