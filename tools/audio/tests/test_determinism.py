"""Determinism: seeded synthesis must be bit-identical across calls."""

import numpy as np

import dsp
import el_sweepcut as es
import engine_synth as eng
from synth_helpers import FS


def test_smooth_random_periodic_same_seed_identical():
    a = dsp.smooth_random_periodic(np.random.default_rng(42), 48000, 12)
    b = dsp.smooth_random_periodic(np.random.default_rng(42), 48000, 12)
    assert np.array_equal(a, b)


def test_stretch_psola_same_seed_identical():
    n = 2 * FS
    y = np.sin(2 * np.pi * 60.0 * np.arange(n) / FS)
    a = es.stretch_psola(y, FS, 60.0, 3 * FS, seed=138)
    b = es.stretch_psola(y, FS, 60.0, 3 * FS, seed=138)
    assert np.array_equal(a, b)


def test_render_loop_same_seed_identical():
    a, _ = eng.render_loop(1500, 1.0, target_s=2.0, seed=7)
    b, _ = eng.render_loop(1500, 1.0, target_s=2.0, seed=7)
    assert np.array_equal(a["ext"], b["ext"])
    assert np.array_equal(a["cab"], b["cab"])


def test_render_loop_different_seed_differs():
    a, _ = eng.render_loop(1500, 1.0, target_s=2.0, seed=7)
    b, _ = eng.render_loop(1500, 1.0, target_s=2.0, seed=8)
    assert not np.array_equal(a["ext"], b["ext"])
