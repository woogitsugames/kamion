"""ADR 0311: cab loudness calibration decision (lufs_calibrate.plan) and BS.1770 level of a known signal."""
import numpy as np

import lufs_calibrate
import pc_capture


def test_plan_raises_quiet_mix_to_target():
    p = lufs_calibrate.plan(-20.8, -6.6, 0.0, -18.0, 1.0, -1.0)
    assert p["code"] == 1
    assert abs(p["new_gain_db"] - 2.8) < 1e-6
    assert abs(p["predicted_lufs"] + 18.0) < 1e-6
    assert abs(p["predicted_true_peak_dbtp"] + 3.8) < 1e-6


def test_plan_within_tolerance_keeps_gain():
    assert lufs_calibrate.plan(-18.4, -4.0, 2.5, -18.0, 1.0, -1.0)["code"] == 0


def test_plan_refuses_gain_that_breaks_true_peak_ceiling():
    assert lufs_calibrate.plan(-22.0, -3.0, 0.0, -18.0, 1.0, -1.0)["code"] == 2


def test_plan_refuses_gain_outside_range():
    assert lufs_calibrate.plan(-40.0, -30.0, 0.0, -18.0, 1.0, -1.0)["code"] == 2


def test_gain_shifts_measured_loudness_by_same_db():
    fs = 48000
    t = np.arange(fs * 10) / fs
    x = (0.1 * np.sin(2 * np.pi * 997 * t))[:, None].repeat(2, axis=1)
    a = pc_capture.measure(x, fs)["lufs_integrated"]
    b = pc_capture.measure(x * 10 ** (2.8 / 20), fs)["lufs_integrated"]
    assert abs((b - a) - 2.8) < 0.02
