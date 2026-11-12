"""Regression tests for the comb_estimate octave bug (fix commit b54a33bd, M16).

Review REVIEW-2026-11-12-s15-mistral-r3 (item 1): the existing test_comb_octave.py
passes on the pre-fix implementation too, so it does not guard the octave
correction. These tests use synthetic signals only (no WAV/LFS) whose comb at
2*f0 outscores the comb at f0 unless the octave correction is applied:
  - harmonic comb with odd harmonics (k >= 3) heavily damped and the 2nd
    harmonic boosted: the old code reports 2*f0 (one octave up);
  - the same comb buried in pink noise (diesel-idle-like floor);
  - f0 in the 30-60 Hz firing range of an inline-six at idle (rpm/20).

They PASS on the current el_analyze.comb_estimate and FAIL on the pre-fix one.
Proof run against the old implementation (tests/legacy_comb.py, verbatim from
git b54a33bd~1):

    KAMION_COMB_IMPL=legacy uv run --project tools/audio --with pytest \
        pytest tools/audio/tests/test_comb_octave_regression.py -q
"""

import os

import numpy as np
import pytest

import el_analyze as ea
import legacy_comb
from synth_helpers import FS


@pytest.fixture()
def comb_estimate():
    """comb_estimate under test: current code by default, pre-fix code when
    KAMION_COMB_IMPL=legacy (used only for the regression proof run)."""
    if os.environ.get("KAMION_COMB_IMPL", "current") == "legacy":
        return legacy_comb.comb_estimate
    return ea.comb_estimate


def pink_noise(n: int, seed: int) -> np.ndarray:
    """Pink (1/sqrt(f)) noise via FFT shaping, peak-normalised."""
    rng = np.random.default_rng(seed)
    white = rng.standard_normal(n)
    X = np.fft.rfft(white)
    f = np.fft.rfftfreq(n, 1 / FS)
    f[0] = f[1]
    x = np.fft.irfft(X / np.sqrt(f), n)
    return x / np.abs(x).max()


def comb_damped_odd(f0: float, dur_s: float = 6.0, n_harm: int = 24, second_boost: float = 3.0,
                    odd_att: float = 0.08, pink: float = 0.0, seed: int = 7) -> np.ndarray:
    """Harmonic comb at f0: even harmonics at 1/k, odd harmonics (k odd) damped to
    odd_att, 2nd harmonic boosted by second_boost; optional pink-noise floor."""
    n = int(dur_s * FS)
    t = np.arange(n) / FS
    x = np.zeros(n)
    for k in range(1, n_harm + 1):
        if k == 2:
            a = second_boost
        elif k % 2 == 1:
            a = odd_att
        else:
            a = 1.0 / k
        x += a * np.sin(2 * np.pi * k * f0 * t + 0.7 * k)
    if pink > 0:
        x = x + pink * pink_noise(n, seed) * np.abs(x).max()
    return x / np.abs(x).max() * 0.7


@pytest.mark.parametrize("f0,second_boost,odd_att", [
    (30.0, 2.0, 0.30),
    (37.5, 3.0, 0.08),
    (46.0, 3.0, 0.08),
    (50.0, 3.0, 0.08),
    (60.0, 3.0, 0.08),
])
def test_damped_odd_harmonics_recover_f0(comb_estimate, f0, second_boost, odd_att):
    """Clean comb, odd harmonics damped, strong 2nd harmonic: pre-fix code picks 2*f0."""
    x = comb_damped_odd(f0, second_boost=second_boost, odd_att=odd_att)
    c = comb_estimate(x, FS)
    assert abs(c["comb_f"] - f0) / f0 < 0.03, \
        f"f0={f0} Hz: comb_f={c['comb_f']:.2f} Hz, top={c['comb_top']}"


@pytest.mark.parametrize("f0", [30.0, 37.5, 46.0, 60.0])
@pytest.mark.parametrize("seed", [1, 7, 42])
def test_pink_noise_plus_damped_odd_harmonics_recover_f0(comb_estimate, f0, seed):
    """Same comb under a pink-noise floor (diesel idle): pre-fix code picks 2*f0."""
    x = comb_damped_odd(f0, odd_att=0.08, pink=1.0, seed=seed)
    c = comb_estimate(x, FS)
    assert abs(c["comb_f"] - f0) / f0 < 0.03, \
        f"f0={f0} Hz seed={seed}: comb_f={c['comb_f']:.2f} Hz, top={c['comb_top']}"
