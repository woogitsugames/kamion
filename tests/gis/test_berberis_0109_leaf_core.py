"""Berberis foliage-layer material and geometry regressions (ADR0109 r4).

Run through pool heavy, like all GIS tests.
"""
import numpy as np
import pytest
from shapely.geometry import box

from streetscape import plantings


def capture(plant):
    class Geometry:
        def __init__(self): self.parts = []
        def add(self, layer, material, vertices, uv, triangles, **kwargs):
            self.parts.append((layer, material, np.asarray(vertices).copy(),
                               np.asarray(uv).copy(), np.asarray(triangles).copy()))
    geometry = Geometry()
    plantings.hedge_mass(geometry, box(0, 0, 8, 1.3), lambda x, y: np.zeros_like(x),
                         ('qa', 'leaf-core-budget'), h=.65, plant=plant)
    return geometry.parts


def test_berberis_has_leaf_cover_instead_of_an_opaque_full_height_core():
    core, shell, sprig = plantings.hedge_mats('berberis_red')
    parts = capture('berberis_red')
    materials = {part[1] for part in parts}
    assert core not in materials, 'the flat opaque mass still fills the leaf gaps'
    assert materials == {shell, sprig}, 'reuse existing foliage materials only'
    assert all(np.isfinite(part[3]).all() for part in parts)


def test_leaf_core_changes_no_vertices_indices_layers_or_triangle_budget(monkeypatch):
    # The old top-clearance regression uses the labelled opaque reference.
    # Equal geometry makes that spatial invariant apply to the new layer too.
    preset = plantings.SPECIES['berberis_red']
    monkeypatch.setitem(preset, 'leaf_core', False)
    reference = capture('berberis_red')
    monkeypatch.setitem(preset, 'leaf_core', True)
    actual = capture('berberis_red')
    assert len(actual) == len(reference)
    assert sum(len(p[4]) for p in actual) == sum(len(p[4]) for p in reference)
    for old, new in zip(reference, actual):
        assert old[0] == new[0]
        np.testing.assert_array_equal(old[2], new[2])
        np.testing.assert_array_equal(old[4], new[4])


@pytest.mark.parametrize('plant', ['privet', 'hornbeam', 'thuja'])
def test_other_hedge_families_retain_their_existing_core_and_shell(plant):
    assert not plantings.SPECIES[plant].get('leaf_core', False)
    core, shell, sprig = plantings.hedge_mats(plant)
    parts = capture(plant)
    assert {part[1] for part in parts} == {core, shell, sprig}
