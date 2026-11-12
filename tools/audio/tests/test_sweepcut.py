"""Cutting constant-rpm cells out of a synthetic linear sweep onto the rpm grid
(el_regen01.line_follow + el_sweepcut: choose_segment / warp_to_constant / flatten_level)."""

import numpy as np
import pytest

import el_regen01 as er
import el_sweepcut as es
from synth_helpers import FS, dominant_hz, linear_chirp

F0, F1, DUR = 30.0, 90.0, 20.0  # firing line 30 -> 90 Hz over 20 s  ==  600 -> 1800 rpm


@pytest.fixture(scope="module")
def sweep():
    return linear_chirp(FS, F0, F1, DUR)


@pytest.fixture(scope="module")
def track(sweep):
    tr = er.line_follow(sweep, FS, 1.0, DUR - 1.0, (25.0, 100.0))
    t = tr["t"]
    return t, es.smooth_track(t, tr["f0"])


def test_line_follow_recovers_sweep(track):
    t, fsm = track
    f_theory = F0 + (F1 - F0) / DUR * t
    rel = np.abs(fsm - f_theory) / f_theory
    assert np.median(rel) < 0.03, f"median rel err {np.median(rel):.3f}"


def test_choose_segment_around_target_rpm(track):
    t, fsm = track
    rpm = 1200
    seg = es.choose_segment(t, fsm, rpm / 20.0)
    assert seg is not None, "no segment found for 1200 rpm"
    ta, tb = seg
    assert es.MIN_LEN_S <= tb - ta <= es.MAX_LEN_S + 1e-9, f"segment {tb - ta:.2f} s"
    f_mid = float(np.interp(0.5 * (ta + tb), t, fsm))
    assert abs(f_mid - rpm / 20.0) / (rpm / 20.0) < 0.05, f_mid


def test_choose_segment_returns_none_outside_sweep(track):
    t, fsm = track
    assert es.choose_segment(t, fsm, 200.0) is None  # 4000 rpm, above the sweep top


def test_grow_respects_max_len(track):
    t, fsm = track
    ratio = fsm / 60.0 - 1.0
    i = int(np.argmin(np.abs(ratio)))
    l, r = es.grow(ratio, i, t[1] - t[0])
    assert (r - l) * (t[1] - t[0]) <= es.MAX_LEN_S + 1e-9


def test_warp_to_constant_flattens_to_grid_rpm(sweep, track):
    t, fsm = track
    rpm = 1200
    f_t = rpm / 20.0
    ta, tb = es.choose_segment(t, fsm, f_t)
    y, info = es.warp_to_constant(sweep, FS, t, fsm, ta, tb, f_t)
    f_meas = dominant_hz(y, FS, f_t * 0.9, f_t * 1.1)
    assert abs(f_meas - f_t) / f_t < 0.01, f"warped line {f_meas:.2f} Hz vs target {f_t:.2f} Hz"
    assert abs(f_meas * 20 - rpm) < 0.01 * rpm
    f_mean = float(np.interp(0.5 * (ta + tb), t, fsm))
    assert abs(len(y) / FS - (tb - ta) * f_mean / f_t) < 0.5, f"out {len(y)/FS:.2f} s"
    assert 0.8 < info["warp_min"] and info["warp_max"] < 1.25


def test_flatten_level_removes_slow_ramp():
    n = 5 * FS
    ramp = np.exp(np.linspace(0, np.log(4.0), n))  # x4 (12 dB) level ramp over 5 s
    x = ramp * np.sin(2 * np.pi * 60.0 * np.arange(n) / FS)
    y, range_db = es.flatten_level(x, FS)
    w = FS // 4
    r_in = np.array([np.sqrt(np.mean(x[i:i + w] ** 2)) for i in range(0, n - w, w)])
    r_out = np.array([np.sqrt(np.mean(y[i:i + w] ** 2)) for i in range(0, n - w, w)])
    in_db = 20 * np.log10(r_in.max() / r_in.min())
    out_db = 20 * np.log10(r_out.max() / r_out.min())
    assert out_db < in_db - 6, f"ramp {in_db:.1f} dB -> {out_db:.1f} dB"
    assert range_db > 0


def test_stretch_psola_deterministic_and_pitch_preserving():
    n = 3 * FS
    y = np.sin(2 * np.pi * 60.0 * np.arange(n) / FS)
    a = es.stretch_psola(y, FS, 60.0, int(4 * FS), seed=138)
    b = es.stretch_psola(y, FS, 60.0, int(4 * FS), seed=138)
    assert len(a) == int(4 * FS)
    assert np.array_equal(a, b)
    f_meas = dominant_hz(a, FS, 54.0, 66.0)
    assert abs(f_meas - 60.0) / 60.0 < 0.03, f"psola line {f_meas:.2f} Hz vs 60 Hz"
