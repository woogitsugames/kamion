"""Clip detection: peak dBFS via el_analyze.db / analyse, and el_prepare.soft_limit ceiling."""

import numpy as np
import soundfile as sf

import el_analyze as ea
import el_prepare as ep
from synth_helpers import FS


def test_peak_dbfs_detects_hard_clip(tmp_path):
    n = FS
    t = np.arange(n) / FS
    x = np.sin(2 * np.pi * 100.0 * t)
    xc = np.clip(x, -0.5, 0.5)
    assert int(np.sum(np.abs(xc) >= 0.5 - 1e-12)) > 100, "expected many samples at the ceiling"
    assert abs(ea.db(float(np.abs(xc).max())) - ea.db(0.5)) < 1e-6
    assert ea.db(float(np.abs(x).max())) > ea.db(0.5)
    p = tmp_path / "CLIP (1).wav"
    sf.write(str(p), xc.astype(np.float32), FS)
    r = ea.analyse(p)
    assert abs(r["peak_dbfs"] - ea.db(0.5)) < 0.05, r["peak_dbfs"]


def test_soft_limit_caps_peak_at_ceiling():
    n = FS
    t = np.arange(n) / FS
    x = 0.95 * np.sin(2 * np.pi * 100.0 * t)
    y, red = ep.soft_limit(x, ceil_db=-1.0)
    assert np.abs(y).max() <= 10 ** (-1.0 / 20) + 1e-9
    assert red > 0


def test_soft_limit_leaves_quiet_signal_untouched():
    n = FS
    t = np.arange(n) / FS
    x = 0.3 * np.sin(2 * np.pi * 100.0 * t)  # peak below knee*ceiling
    y, red = ep.soft_limit(x, ceil_db=-1.0)
    assert red == 0.0
    assert np.array_equal(y, x)
