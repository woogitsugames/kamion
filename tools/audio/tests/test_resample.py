"""FFT resampling (el_prepare.resample_periodic): output length and pitch follow
theory (m = round(n/ratio), exact = n/m, f_new = f_old * exact) and the loop seam survives."""

import numpy as np

import el_analyze as ea
import el_prepare as ep
from synth_helpers import FS, dominant_hz


def _periodic_loop(f0: float, dur_s: float = 4.0):
    cycles = int(round(dur_s * f0))
    n = int(round(cycles * FS / f0))  # whole number of cycles over the loop
    t = np.arange(n) / FS
    return np.sin(2 * np.pi * f0 * t), n


def test_resample_length_matches_theory():
    x, n = _periodic_loop(75.0)
    ratio = 1.25
    y, exact = ep.resample_periodic(x, ratio)
    m = int(round(n / ratio))
    assert len(y) == m
    assert abs(exact - ratio) <= ratio / (2 * m) + 1e-12


def test_resample_pitch_scales_by_exact_ratio():
    f0 = 75.0
    x, _n = _periodic_loop(f0)
    for ratio in (1.25, 0.8):
        y, exact = ep.resample_periodic(x, ratio)
        f_exp = f0 * exact
        f_meas = dominant_hz(y, FS, f_exp * 0.9, f_exp * 1.1)
        assert abs(f_meas - f_exp) / f_exp < 0.005, \
            f"ratio {ratio}: f_meas {f_meas:.3f} Hz vs f0*exact {f_exp:.3f} Hz"


def test_resampled_loop_stays_seamless():
    n = int(4.0 * FS)
    t = np.arange(n) / FS
    x = np.zeros(n)
    for k in range(1, 9):
        x += (1.0 / k) * np.sin(2 * np.pi * k * 75.0 * t + 0.7 * k)
    y, _exact = ep.resample_periodic(x, 1.25)
    s = ea.seam(y, FS)
    assert s["seam_jump_ratio"] < 0.3, s
