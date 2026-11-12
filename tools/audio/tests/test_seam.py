"""Loop-point (seam) continuity: el_analyze.seam on periodic vs broken loops,
el_prepare.seam_loop equal-power crossfade, and the procedural engine loop."""

import numpy as np

import el_analyze as ea
import el_prepare as ep
import engine_synth as eng
from synth_helpers import FS, harmonic_engine


def _multi_sine(n: int, seed: int = 11) -> np.ndarray:
    """Deterministic band-limited signal whose wrap is NOT continuous (incommensurate lines)."""
    rng = np.random.default_rng(seed)
    t = np.arange(n) / FS
    x = np.zeros(n)
    for k, f in enumerate([41.13, 75.31, 113.77, 199.9], start=1):
        x += 0.4 / k * np.cos(2 * np.pi * f * t + rng.uniform(0, 2 * np.pi))
    return x


def test_periodic_signal_has_clean_seam():
    x = harmonic_engine(FS, 1500, dur_s=4.0)  # exactly 300 firing cycles over the loop
    s = ea.seam(x, FS)
    assert s["seam_jump_ratio"] < 0.3, s
    assert abs(s["seam_level_step_db"]) < 1.0, s
    assert s["seam_hf_spike_db"] < 6.0, s


def test_seam_flags_broken_wrap():
    x = _multi_sine(4 * FS)
    s = ea.seam(x, FS)
    assert s["seam_jump_ratio"] > 1.0, s


def test_seam_loop_makes_arbitrary_signal_continuous():
    n = 4 * FS
    x = _multi_sine(n)
    y = ep.seam_loop(x)
    L = int(ep.SEAM_S * FS)
    assert len(y) == n - L
    assert np.isclose(y[0], x[n - L])
    s = ea.seam(y, FS)
    assert s["seam_jump_ratio"] < 0.5, s


def test_rendered_engine_loop_seam_is_continuous():
    loops, _geo = eng.render_loop(1500, 1.0, target_s=4.0, seed=7)
    s = ea.seam(loops["ext"], FS)
    assert s["seam_jump_ratio"] < 0.5, s
