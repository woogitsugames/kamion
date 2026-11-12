"""Small numerical tests: no Blender, world build, downloads or game-map writes."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

spec = importlib.util.spec_from_file_location('cab_cc0', Path(__file__).parents[1] / 'cc0_leather.py')
cab = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cab)


def encoded_slopes(x, y):
    vectors = np.stack((x, y, np.ones_like(x)), axis=-1)
    vectors /= np.linalg.norm(vectors, axis=-1, keepdims=True)
    return vectors * .5 + .5


def test_disabled_preserves_exact_input():
    normals = np.random.default_rng(11).random((16, 16, 3), dtype=np.float32)
    before = normals.copy()
    assert cab.highpass_normals(normals, .1, 0) is normals
    np.testing.assert_array_equal(normals, before)


def test_constant_tilt_becomes_flat_without_mutating_source():
    normals = encoded_slopes(np.full((32, 32), .4), np.full((32, 32), -.2))
    before = normals.copy()
    result = cab.highpass_normals(normals, .1, 1.5)
    np.testing.assert_allclose(result, np.broadcast_to([.5, .5, 1.], result.shape), atol=1e-6)
    np.testing.assert_array_equal(normals, before)


def test_removes_broad_wave_while_preserving_fine_grain_and_unit_length():
    size = 256
    t = np.arange(size) * (2 * np.pi / size)
    broad = np.broadcast_to(np.sin(t), (size, size))
    fine = np.broadcast_to(np.sin(32 * t), (size, size))
    result = cab.highpass_normals(encoded_slopes(.2 * broad + .1 * fine, np.zeros_like(broad)), .1, 1.5)
    normal = result * 2 - 1
    slope = normal[..., 0] / normal[..., 2]
    broad_amplitude = 2 * np.mean(slope * broad)
    fine_amplitude = 2 * np.mean(slope * fine)
    assert abs(broad_amplitude) < .002
    assert .098 < fine_amplitude < .102
    np.testing.assert_allclose(np.linalg.norm(normal, axis=-1), 1, atol=1e-6)
    assert np.all(normal[..., 2] > 0)


def test_physical_cutoff_is_independent_of_source_resolution():
    amplitudes = []
    for size in (128, 256):
        wave = np.broadcast_to(np.sin(np.arange(size) * (16 * np.pi / size)), (size, size))
        result = cab.highpass_normals(encoded_slopes(.2 * wave, np.zeros_like(wave)), .1, 1.5) * 2 - 1
        amplitudes.append(2 * np.mean(result[..., 0] / result[..., 2] * wave))
    assert abs(amplitudes[0] - amplitudes[1]) < .0005


def test_rejects_invalid_filter_and_backfacing_normals():
    normals = np.broadcast_to([.5, .5, 1.], (8, 8, 3))
    for sigma in (-1, float('nan'), float('inf'), 25):
        with pytest.raises(ValueError):
            cab.highpass_normals(normals, .1, sigma)
    with pytest.raises(ValueError):
        cab.highpass_normals(np.broadcast_to([.5, .5, 0.], (8, 8, 3)), .1, 1.5)
