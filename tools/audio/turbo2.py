"""Turbo layer v2 for the ElevenLabs set (ADR 0142): compressor whine + intake rush as two seamless loops.

The v1 whistle (sfx_synth.turbo_whistle_loop) is one near-pure 3.2 kHz sine with 0.4 % FM: the owner heard it as
artificial or absent (APK 0138). A turbocharger compressor is heard as (a) broadband intake/compressor-outlet rush whose
level and brightness follow the mass flow (boost x rpm) and (b) a quieter tonal whine at shaft-order / blade-pass
frequencies that rises with shaft speed and is never perfectly steady (shaft speed and flow fluctuate, two close
partials beat). Runtime (EngineAudio): whine pitch and gain from Engine.Boost (shaft speed proxy, first-order lag in the
physics), rush gain from boost and rpm (flow), both far quieter in the cab (behind the firewall). All parameters are
WORKING_VALUE design choices, judged by the owner on the phone.

Swap for a recording (REGEN-02 TURBO_*): el_fx.TURBO = {"whine": "<ID> (n).wav", ...} - same runtime slots.
"""

from __future__ import annotations

import numpy as np

import dsp
from dsp import FS, bp, chain, hp, lp, peak, periodic_sosfilt

WHINE_REF_HZ = 2600.0  # whine centre at runtime pitch 1.0 (EngineAudio: pitch 0.55 + 0.9 * boost)


def _tone(rng: np.random.Generator, n: int, f: float, fm_depth: float, seconds: float) -> np.ndarray:
    """Sine with slow periodic FM, total cycles rounded to an integer (clean wrap)."""
    fm = fm_depth * dsp.smooth_random_periodic(rng, n, max_cycles=int(3 * seconds), n_terms=5)
    phase = 2 * np.pi * np.cumsum(f * (1.0 + fm)) / FS
    cyc = phase[-1] / (2 * np.pi)
    return np.sin(phase * np.round(cyc) / cyc + rng.uniform(0, 2 * np.pi))


def whine_loop(seconds: float = 4.0, seed: int = 142) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    f1 = WHINE_REF_HZ
    tone = (1.00 * _tone(rng, n, f1, 0.005, seconds)
            + 0.55 * _tone(rng, n, f1 * 1.0062, 0.006, seconds)   # close partial: ~16 Hz beating shimmer
            + 0.22 * _tone(rng, n, 2 * f1, 0.005, seconds)
            + 0.07 * _tone(rng, n, f1 / 6.0, 0.004, seconds))     # faint shaft-order line
    am = 1.0 + 0.18 * dsp.smooth_random_periodic(rng, n, max_cycles=int(7 * seconds), n_terms=6)
    narrow = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(bp(f1, 18.0), bp(f1 * 1.003, 18.0)))
    narrow /= np.max(np.abs(narrow)) + 1e-9
    x = 0.6 * tone * am / np.max(np.abs(tone)) + 0.4 * narrow
    return x / (np.max(np.abs(x)) + 1e-9)


def rush_loop(seconds: float = 4.0, seed: int = 143) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    w = dsp.periodic_noise(rng, n)
    x = periodic_sosfilt(w, chain(hp(500.0, 0.7), bp(2200.0, 0.7), peak(4600.0, 1.2, 4.0), lp(10000.0, 0.7)))
    am = 1.0 + 0.10 * dsp.smooth_random_periodic(rng, n, max_cycles=int(5 * seconds), n_terms=6)
    x = x * am
    return x / (np.max(np.abs(x)) + 1e-9)
