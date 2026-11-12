"""Octave-correction behaviour of el_analyze.comb_estimate on synthetic signals.

Covers the fix for the PR #10 review finding: the octave check (comb_half/comb_double)
was computed but never applied, so a 75 Hz firing line read from a float32 WAV came
back as 149 Hz (one octave up).
"""

import numpy as np
import pytest

import el_analyze as ea
from synth_helpers import FS


def harmonic_comb(f0: float, dur_s: float = 6.0, n_harm: int = 12, second_boost: float = 1.0,
                  missing_fundamental: bool = False) -> np.ndarray:
    """Harmonic comb at f0; second_boost > 1 makes the 2nd harmonic stronger than the 1st."""
    n = int(dur_s * FS)
    t = np.arange(n) / FS
    x = np.zeros(n)
    for k in range(1, n_harm + 1):
        if missing_fundamental and k == 1:
            continue
        a = second_boost if k == 2 else 1.0 / k
        x += a * np.sin(2 * np.pi * k * f0 * t + 0.7 * k)
    return x / np.abs(x).max() * 0.7


@pytest.mark.parametrize("f0", [30.0, 46.0, 60.0, 90.0])
def test_comb_recovers_f0_with_strong_second_harmonic(f0):
    x = harmonic_comb(f0, second_boost=3.0)
    c = ea.comb_estimate(x, FS)
    assert abs(c["comb_f"] - f0) / f0 < 0.03, \
        f"f0={f0} Hz: comb_f={c['comb_f']:.2f} Hz, top={c['comb_top']}"


@pytest.mark.parametrize("f0", [46.0, 60.0])
def test_comb_recovers_missing_fundamental(f0):
    x = harmonic_comb(f0, second_boost=2.0, missing_fundamental=True)
    c = ea.comb_estimate(x, FS)
    assert abs(c["comb_f"] - f0) / f0 < 0.03, \
        f"missing fundamental f0={f0} Hz: comb_f={c['comb_f']:.2f} Hz, top={c['comb_top']}"


@pytest.mark.parametrize("seed", [1, 7, 42])
def test_comb_noise_no_false_detection(seed):
    rng = np.random.default_rng(seed)
    x = rng.standard_normal(int(6.0 * FS)) * 0.3
    c = ea.comb_estimate(x, FS)
    # 6 dB is the prominence threshold analyse() uses for a real harmonic ladder;
    # pure noise must stay well below it no matter which candidate wins.
    assert c["comb_score"] < 6.0, \
        f"seed {seed}: noise comb_score={c['comb_score']:.2f} dB at comb_f={c['comb_f']:.2f} Hz"
