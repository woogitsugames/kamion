"""ADR0088: shape / stable card LOD / licensed bark fallback contracts."""
import math
from pathlib import Path
import numpy as np

from streetscape.foliage_policy import crown_opening, leaf_lod_indices, metric_patch_field, osm_tree_species
from streetscape.leaf_textures import pine_scan
from streetscape.vegetation_metrics import foliage_mask


def test_canopy_has_coherent_openings_and_retains_stem_foliage():
    angles = np.linspace(0, 2 * math.pi, 360, endpoint=False)
    gaps = np.array([crown_opening((4*math.cos(a), 4*math.sin(a), 0), (0, 0, 0), 15, 0) for a in angles])
    assert .10 < gaps.mean() < .40
    # Neighbouring leaves form actual windows rather than a salt-and-pepper mask.
    assert np.count_nonzero(gaps != np.roll(gaps, 1)) == 4
    assert not crown_opening((.1, .1, 0), (0, 0, 0), 15, 0)


def test_lod_leaf_subset_is_deterministic_and_budgeted():
    a, b = leaf_lod_indices(1000, 48), leaf_lod_indices(1000, 48)
    np.testing.assert_array_equal(a, b)
    assert 330 < len(a) < 470
    assert np.all(np.diff(a) > 0) and 0 <= a.min() < a.max() < 1000
    assert len(leaf_lod_indices(1000, 48, maximum=140)) == 140


def test_cc0_bark_clean_clone_fallback_stays_useful(tmp_path, caplog):
    image = pine_scan(root=tmp_path, n=64)
    assert image.size == (64, 64)
    assert np.asarray(image)[..., :3].std() > 2
    assert 'procedural bark retained' in caplog.text


def test_metric_patches_are_world_anchored_without_chunk_seams():
    east, north = np.arange(-30., 31), np.arange(45., -16., -1)
    full = metric_patch_field(east, north)
    piece = metric_patch_field(east[13:43], north[7:27])
    np.testing.assert_array_equal(piece, full[7:27, 13:43])
    assert .05 < full.std() < .35 and 0 <= full.min() <= full.max() <= 1
    # No leaf-size salt noise: adjacent one-metre samples vary smoothly.
    assert np.abs(np.diff(full, axis=1)).mean() < .12


def test_explicit_osm_botany_is_not_replaced_by_generic_linden():
    assert osm_tree_species({'genus': 'Betula'}) == 'birch'
    assert osm_tree_species({'species': 'Pinus sylvestris'}) == 'pine'
    assert osm_tree_species({'species:pl': 'lipa drobnolistna'}) == 'linden'
    assert osm_tree_species({'natural': 'tree'}) == 'linden'


def test_crown_mask_retains_crushed_foliage_and_excludes_sky_bark():
    pixels = np.array([[[45, 65, 35], [8, 8, 8], [205, 215, 230], [90, 75, 61]]], dtype=np.uint8)
    assert foliage_mask(pixels).tolist() == [[True, True, False, False]]
