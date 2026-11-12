"""Procedural non-combustion truck sounds: turbo, pneumatics, road, wind.

Loops are periodic by construction (see dsp.py); one-shots get short raised-cosine edges.
All parameters are WORKING_VALUE design choices.
"""

from __future__ import annotations

import numpy as np

import dsp
from dsp import FS, bp, chain, hp, lp, peak, periodic_sosfilt
from scipy import signal

TURBO_REF_HZ = 3200.0  # whistle centre frequency at runtime pitch 1.0


# --------------------------------------------------------------------------- loops
def turbo_whistle_loop(seconds: float = 3.0, seed: int = 31) -> np.ndarray:
    """Compressor whistle: narrow tonal core with slow periodic FM + 2nd partial + air rush.

    Runtime maps boost -> pitch (frequency scales with shaft speed) and boost/throttle -> gain.
    """
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    t = np.arange(n) / FS
    fm = 0.004 * dsp.smooth_random_periodic(rng, n, max_cycles=int(4 * seconds), n_terms=5)
    # instantaneous frequency integrated -> phase; make total cycles integer for a clean wrap
    inst = TURBO_REF_HZ * (1.0 + fm)
    phase = 2 * np.pi * np.cumsum(inst) / FS
    total_cycles = phase[-1] / (2 * np.pi)
    phase *= np.round(total_cycles) / total_cycles
    am = 1.0 + 0.12 * dsp.smooth_random_periodic(rng, n, max_cycles=int(9 * seconds), n_terms=6)
    tone = np.sin(phase) * am + 0.22 * np.sin(2 * phase + 0.4) + 0.06 * np.sin(3 * phase + 1.1)
    narrow = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(bp(TURBO_REF_HZ, 45.0), bp(TURBO_REF_HZ, 45.0)))
    narrow /= np.max(np.abs(narrow)) + 1e-9
    rush = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(hp(1400.0, 0.7), lp(7500.0, 0.7), peak(TURBO_REF_HZ * 1.25, 1.0, 4.0)))
    rush /= np.max(np.abs(rush)) + 1e-9
    x = 0.55 * tone + 0.30 * narrow + 0.10 * rush
    del t
    return x


def road_roll_loop(seconds: float = 4.0, seed: int = 41) -> np.ndarray:
    """Tyre/road rolling noise on dry asphalt (pitch ~ speed at runtime): ~1 kHz tyre band + low rumble."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    w = dsp.periodic_noise(rng, n)
    tyre = periodic_sosfilt(w, chain(hp(250.0, 0.6), lp(2200.0, 0.6), peak(900.0, 1.2, 5.0)))
    rumble = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(hp(28.0), lp(140.0, 0.9), peak(70.0, 2.0, 4.0)))
    # tread/road-texture flutter: slow random amplitude modulation
    am = 1.0 + 0.18 * dsp.smooth_random_periodic(rng, n, max_cycles=int(12 * seconds), n_terms=8)
    x = tyre * am / (np.max(np.abs(tyre)) + 1e-9) + 0.9 * rumble / (np.max(np.abs(rumble)) + 1e-9)
    return x


def wind_loop(seconds: float = 6.0, seed: int = 51) -> np.ndarray:
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    base = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(hp(60.0), lp(900.0, 0.6), peak(350.0, 0.8, 3.0)))
    whistle = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(bp(1150.0, 12.0)))  # mirror-arm edge tone
    gust = 1.0 + 0.25 * dsp.smooth_random_periodic(rng, n, max_cycles=int(0.8 * seconds), n_terms=4)
    x = base / np.max(np.abs(base)) * gust + 0.08 * whistle / np.max(np.abs(whistle)) * gust ** 2
    return x


def gear_whine_loop(seconds: float = 2.0, seed: int = 61, f_ref: float = 1000.0) -> np.ndarray:
    """Transmission/retarder-style whine at f_ref (runtime pitch ~ output-shaft speed)."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    cycles = int(round(f_ref * seconds))
    ph = 2 * np.pi * cycles * np.arange(n) / n
    am = 1.0 + 0.2 * dsp.smooth_random_periodic(rng, n, max_cycles=int(6 * seconds))
    side = 0.25 * np.sin(ph * 0.5 + 0.3)  # half-order mesh modulation (shaft run-out)
    x = (np.sin(ph) + 0.3 * np.sin(2 * ph + 0.9) + side) * am
    x += 0.15 * periodic_sosfilt(dsp.periodic_noise(rng, n), chain(bp(f_ref, 8.0)))
    return x


# --------------------------------------------------------------------------- one-shots
def _env_attack_decay(n: int, attack_s: float, tau_s: float, hold_s: float = 0.0) -> np.ndarray:
    t = np.arange(n) / FS
    a = np.clip(t / attack_s, 0, 1) ** 1.5
    d = np.where(t < attack_s + hold_s, 1.0, np.exp(-(t - attack_s - hold_s) / tau_s))
    return a * d


def _time_varying_hiss(rng, n: int, bright_sos, dark_sos, brightness: np.ndarray) -> np.ndarray:
    w = rng.standard_normal(n + 4096)
    b = signal.sosfilt(bright_sos, w)[4096:]
    d = signal.sosfilt(dark_sos, w)[4096:]
    b /= np.max(np.abs(b)); d /= np.max(np.abs(d))
    return brightness * b + (1 - brightness) * d


def _thump(n: int, f0: float, tau: float, amp: float) -> np.ndarray:
    t = np.arange(n) / FS
    return amp * np.sin(2 * np.pi * f0 * t * (1 - 0.25 * t / (t + 0.05))) * np.exp(-t / tau)


def _click(n: int, f0: float, tau: float, amp: float, at_s: float = 0.0) -> np.ndarray:
    x = np.zeros(n)
    i0 = int(at_s * FS)
    t = np.arange(n - i0) / FS
    x[i0:] = amp * np.sin(2 * np.pi * f0 * t) * np.exp(-t / tau)
    return x


def air_brake_release(seed: int = 71) -> np.ndarray:
    """Service-brake release: valve 'chuck' then a short, bright, decaying exhaust hiss."""
    rng = np.random.default_rng(seed)
    n = int(0.95 * FS)
    t = np.arange(n) / FS
    env = _env_attack_decay(n, 0.006, 0.17, hold_s=0.03)
    bright = chain(hp(1500.0, 0.7), peak(3300.0, 1.5, 5.0), peak(6200.0, 2.0, 4.0), lp(11000.0, 0.7))
    dark = chain(hp(700.0, 0.7), peak(2200.0, 1.2, 4.0), lp(4500.0, 0.7))
    brightness = np.exp(-t / 0.25)  # pressure falls -> jet slows -> darker
    hiss = _time_varying_hiss(rng, n, bright, dark, brightness) * env
    x = 0.85 * hiss + _thump(n, 95.0, 0.03, 0.45) + _click(n, 1900.0, 0.004, 0.25)
    return dsp.fade_edges(x, 0.0005, 0.08)


def parking_brake_set(seed: int = 72) -> np.ndarray:
    """Spring-brake (parking) application: loud long 'PSSHHHT' with a valve knock."""
    rng = np.random.default_rng(seed)
    n = int(2.1 * FS)
    t = np.arange(n) / FS
    env = _env_attack_decay(n, 0.012, 0.45, hold_s=0.15)
    bright = chain(hp(1100.0, 0.7), peak(2800.0, 1.2, 6.0), peak(5200.0, 1.8, 3.0), lp(12000.0, 0.7))
    dark = chain(hp(500.0, 0.7), peak(1600.0, 1.0, 4.0), lp(3800.0, 0.7))
    brightness = 0.25 + 0.75 * np.exp(-t / 0.6)
    hiss = _time_varying_hiss(rng, n, bright, dark, brightness) * env
    x = hiss + _thump(n, 70.0, 0.05, 0.6) + _click(n, 1400.0, 0.006, 0.35) + _click(n, 900.0, 0.01, 0.2, at_s=1.75)
    return dsp.fade_edges(x, 0.0005, 0.12)


def air_dryer_purge(seed: int = 73) -> np.ndarray:
    """Compressor governor cut-out: abrupt loud purge blast, fast decay."""
    rng = np.random.default_rng(seed)
    n = int(0.9 * FS)
    t = np.arange(n) / FS
    env = _env_attack_decay(n, 0.003, 0.12, hold_s=0.06)
    bright = chain(hp(800.0, 0.7), peak(2400.0, 1.0, 5.0), lp(9000.0, 0.7))
    dark = chain(hp(300.0, 0.7), peak(1100.0, 1.0, 4.0), lp(3000.0, 0.7))
    hiss = _time_varying_hiss(rng, n, bright, dark, np.exp(-t / 0.15)) * env
    x = hiss + _thump(n, 60.0, 0.06, 0.9)
    return dsp.fade_edges(x, 0.0003, 0.1)


def gearshift_air(seed: int = 74) -> np.ndarray:
    """AMT shift-cylinder exhaust: tiny 'pft' (plays on each gear change)."""
    rng = np.random.default_rng(seed)
    n = int(0.25 * FS)
    env = _env_attack_decay(n, 0.002, 0.04)
    hiss = signal.sosfilt(chain(hp(1800.0), peak(4200.0, 1.5, 4.0), lp(9000.0)), rng.standard_normal(n)) * env
    x = hiss / np.max(np.abs(hiss)) * 0.5 + _click(n, 1200.0, 0.003, 0.4) + _click(n, 700.0, 0.006, 0.3, at_s=0.11)
    return dsp.fade_edges(x, 0.0003, 0.03)


def turbo_liftoff(seed: int = 75) -> np.ndarray:
    """Throttle lift-off at boost: short wastegate/recirculation 'psst' + falling whistle."""
    rng = np.random.default_rng(seed)
    n = int(0.75 * FS)
    t = np.arange(n) / FS
    env = _env_attack_decay(n, 0.01, 0.13, hold_s=0.02)
    bright = chain(hp(2000.0, 0.7), peak(4500.0, 1.4, 5.0), lp(10000.0, 0.7))
    dark = chain(hp(900.0, 0.7), peak(2500.0, 1.2, 3.0), lp(5000.0, 0.7))
    hiss = _time_varying_hiss(rng, n, bright, dark, np.exp(-t / 0.2)) * env
    f = TURBO_REF_HZ * (1.1 * np.exp(-t / 0.35) + 0.35)
    chirp = np.sin(2 * np.pi * np.cumsum(f) / FS) * np.exp(-t / 0.25) * 0.35
    x = 0.8 * hiss + chirp
    return dsp.fade_edges(x, 0.0005, 0.1)
