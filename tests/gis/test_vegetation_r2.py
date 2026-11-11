"""ADR0088: shape / stable card LOD / licensed bark fallback contracts."""
import math
from pathlib import Path
import numpy as np

from streetscape.foliage_policy import crown_opening, leaf_lod_indices
from streetscape.leaf_textures import pine_scan


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


def test_cc0_bark_clean_clone_fallback_stays_useful(tmp_path, caplog):
    image = pine_scan(root=tmp_path, n=64)
    assert image.size == (64, 64)
    assert np.asarray(image)[..., :3].std() > 2
    assert 'procedural bark retained' in caplog.text
