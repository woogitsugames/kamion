"""Procedural truck layers beyond the first bank (sfx_synth.py): tyre surfaces + squeal, retarder,
air compressor, parking-brake release, dryer 'psst', indicator relay, industrial-yard ambience,
and the cab (interior) filter that turns any exterior layer into its cabin perspective.

Same rules as sfx_synth.py: loops are periodic by construction (dsp.periodic_sosfilt / circular
kernels), one-shots get raised-cosine edges, everything is our own synthesis (no recordings).
All numbers are WORKING_VALUE design choices, to be judged by the owner's ears.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

import dsp
from dsp import FS, bp, chain, highshelf, hp, lowshelf, lp, peak, periodic_sosfilt
import sfx_synth as sx


def _unit(x: np.ndarray) -> np.ndarray:
    return x / (np.max(np.abs(x)) + 1e-12)


def _pf(rng, n, sos) -> np.ndarray:
    """Periodic-filtered white noise, unit peak."""
    return _unit(periodic_sosfilt(dsp.periodic_noise(rng, n), sos))


def _add_circ(buf: np.ndarray, i0: int, kernel: np.ndarray, amp: float = 1.0) -> None:
    idx = (i0 + np.arange(len(kernel))) % len(buf)
    np.add.at(buf, idx, amp * kernel)


def _damped_sine(f: float, tau: float, length_s: float, phase: float = 0.0) -> np.ndarray:
    t = np.arange(int(length_s * FS)) / FS
    return np.sin(2 * np.pi * f * t + phase) * np.exp(-t / tau)


def _noise_burst(rng, f_lo: float, f_hi: float, tau: float, length_s: float) -> np.ndarray:
    n = int(length_s * FS)
    w = signal.sosfilt(chain(hp(f_lo, 0.7), lp(f_hi, 0.7)), rng.standard_normal(n))
    t = np.arange(n) / FS
    return _unit(w) * np.exp(-t / tau) * np.minimum(1.0, t / 0.0009)  # ~1 ms attack: no digital click on the onset


# =========================================================================== TYRES x SURFACE
# Surface ids follow SurfaceKind in game/Assets/_Project/Vehicle/Runtime/SurfaceTable.cs:
# 0 dry asphalt (= road_roll_loop of sfx_synth), 1 wet asphalt, 2 concrete, 3 cobbles, 4 gravel, 5 grass.
def tyre_asphalt_wet_loop(seconds: float = 4.0, seed: int = 42) -> np.ndarray:
    """Wet asphalt: dry tyre band thinner, spray/'swish' 2-8 kHz dominates, rumble intact."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    spray = _pf(rng, n, chain(hp(1700.0, 0.7), lp(9500.0, 0.7), peak(4200.0, 1.0, 4.0)))
    tyre = _pf(rng, n, chain(hp(250.0, 0.6), lp(2400.0, 0.6), peak(1000.0, 1.2, 4.0)))
    rumble = _pf(rng, n, chain(hp(28.0), lp(150.0, 0.9), peak(75.0, 2.0, 4.0)))
    am = 1.0 + 0.12 * dsp.smooth_random_periodic(rng, n, max_cycles=int(10 * seconds), n_terms=8)
    return (0.65 * spray * am + 0.55 * tyre + 0.8 * rumble)


def tyre_concrete_loop(seconds: float = 4.0, seed: int = 43) -> np.ndarray:
    """Concrete slabs: tonal groove hum around 1.2 kHz + the rhythmic 'ta-dum, ta-dum' of expansion joints
    (12 joints per loop; at runtime pitch 1.0 the joint rate follows the vehicle speed)."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    tyre = _pf(rng, n, chain(hp(220.0, 0.6), lp(2600.0, 0.6), peak(1250.0, 1.6, 6.0)))
    hum = _pf(rng, n, bp(1250.0, 14.0))
    hum *= 1.0 + 0.4 * dsp.periodic_lfo(n, int(2 * seconds), 0.7)
    rumble = _pf(rng, n, chain(hp(28.0), lp(130.0, 0.9), peak(65.0, 2.0, 4.0)))
    joints = np.zeros(n)
    thump = _damped_sine(68.0, 0.05, 0.30)
    slap = _noise_burst(rng, 250.0, 1400.0, 0.025, 0.2)
    n_j = int(round(3.0 * seconds))
    for k in range(n_j):
        t0 = (k + 0.1 * rng.standard_normal()) / n_j * seconds
        a = rng.uniform(0.8, 1.0)
        # front axle, rear tractor axle, trailer bogie: three hits per joint (spacing ~ wheelbase / speed)
        for dt_s, g in ((0.0, 1.0), (0.215, 0.85), (0.43, 0.7)):
            i0 = int((t0 + dt_s) * FS)
            _add_circ(joints, i0, thump, a * g * 0.9)
            _add_circ(joints, i0, slap, a * g * 0.55)
    return 0.8 * tyre + 0.35 * hum + 0.85 * rumble + 0.55 * joints


def tyre_cobbles_loop(seconds: float = 4.0, seed: int = 44) -> np.ndarray:
    """Cobbles (kostka brukowa): strong irregular stone impacts + low rumble + rattle of the load."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    rumble = _pf(rng, n, chain(hp(55.0, 0.7), lp(520.0, 0.7), peak(170.0, 1.0, 6.0)))
    rumble *= 1.0 + 0.35 * dsp.smooth_random_periodic(rng, n, max_cycles=int(7 * seconds), n_terms=8)
    mid = _pf(rng, n, chain(hp(380.0, 0.7), lp(3200.0, 0.7), peak(1400.0, 1.0, 4.0)))
    hits = np.zeros(n)
    for _ in range(int(55 * seconds)):  # ~55 stone hits/s at runtime pitch 1
        f = rng.uniform(260.0, 1500.0)
        k = _damped_sine(f, rng.uniform(0.003, 0.010), 0.05, rng.uniform(0, 6.28))
        _add_circ(hits, int(rng.integers(0, n)), k, rng.lognormal(-0.5, 0.55))
    return 0.9 * rumble + 0.35 * mid + 0.55 * _unit(hits)


def tyre_gravel_loop(seconds: float = 4.0, seed: int = 45) -> np.ndarray:
    """Gravel: dense granular crackle (heavy-tailed amplitude noise) over a soft tyre band."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    g = np.abs(rng.standard_normal(n)) ** 3
    g = periodic_sosfilt(g, chain(lp(900.0, 0.7)))  # ~ 1 ms smoothing -> crackle grains
    grains = periodic_sosfilt(dsp.periodic_noise(rng, n) * _unit(g), chain(hp(900.0, 0.7), lp(7000.0, 0.7), peak(2800.0, 1.0, 4.0)))
    band = _pf(rng, n, chain(hp(200.0, 0.7), lp(1800.0, 0.7), peak(700.0, 1.0, 4.0)))
    rumble = _pf(rng, n, chain(hp(35.0), lp(200.0, 0.9)))
    am = 1.0 + 0.25 * dsp.smooth_random_periodic(rng, n, max_cycles=int(9 * seconds), n_terms=8)
    return 0.85 * _unit(grains) * am + 0.5 * band + 0.6 * rumble


def tyre_grass_loop(seconds: float = 4.0, seed: int = 46) -> np.ndarray:
    """Grass / soft ground: muffled swish and low thud, almost no tyre band."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    swish = _pf(rng, n, chain(hp(120.0), lp(1500.0, 0.7), peak(450.0, 0.8, 4.0)))
    thud = _pf(rng, n, chain(hp(25.0), lp(120.0, 0.9), peak(60.0, 1.5, 4.0)))
    thud *= 1.0 + 0.4 * dsp.smooth_random_periodic(rng, n, max_cycles=int(5 * seconds), n_terms=5)
    air = _pf(rng, n, chain(hp(2500.0), lp(7000.0)))
    return 0.8 * swish + 0.8 * thud + 0.08 * air


def tyre_squeal_loop(seconds: float = 4.0, seed: int = 47) -> np.ndarray:
    """Heavy-truck tyre squeal v2 (ADR 0145): rough, low, wavering rubber squeal, no clean tone.

    The v1 loop (ADR 0007..0142) was a stick-slip tone at 930 Hz with harmonics: the owner heard a whistle. v2 builds
    the squeal from noise: three formant bands (~520 / 1150 / 2100 Hz, Q 4-6) whose level is chopped by irregular
    stick-slip bursts (15-40 Hz random AM), a wide random wobble of the dominant band (via two overlapping bands
    cross-faded slowly), grit (HF grains) and tyre roar underneath. The long-term spectrum has no narrow line
    (el_regen03.measure tone_db < 12 dB). Placeholder until the REGEN-03 recording (el_tyre_squeal_loop) is imported;
    the runtime uses the recording when it exists.

    Runtime: gain from combined slip above the squeal onset and speed (LayerMath.SquealGain), pitch 0.9..1.15."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    lo_a = _pf(rng, n, chain(bp(480.0, 5.0), bp(480.0, 3.0)))
    lo_b = _pf(rng, n, chain(bp(600.0, 5.0), bp(600.0, 3.0)))
    xf = 0.5 + 0.5 * dsp.smooth_random_periodic(rng, n, max_cycles=int(3 * seconds), n_terms=4)
    low = lo_a * np.sqrt(xf) + lo_b * np.sqrt(1.0 - xf)
    mid = _pf(rng, n, chain(bp(1150.0, 4.0), bp(1150.0, 2.5)))
    high = _pf(rng, n, chain(bp(2100.0, 4.0), lp(4000.0, 0.7)))
    # stick-slip chatter: irregular AM 15-40 Hz, never fully closed
    chatter = np.abs(dsp.smooth_random_periodic(rng, n, max_cycles=int(40 * seconds), n_terms=14))
    chatter = 0.45 + 0.55 * chatter
    swell = 1.0 + 0.35 * dsp.smooth_random_periodic(rng, n, max_cycles=int(2 * seconds), n_terms=4)
    grit = np.abs(rng.standard_normal(n)) ** 3
    grit = periodic_sosfilt(dsp.periodic_noise(rng, n) * _unit(periodic_sosfilt(grit, chain(lp(700.0, 0.7)))),
                            chain(hp(1500.0, 0.7), lp(6500.0, 0.7)))
    roar = _pf(rng, n, chain(hp(90.0, 0.7), lp(900.0, 0.7), peak(250.0, 1.0, 3.0)))
    x = (1.0 * low + 0.55 * mid + 0.25 * high) * chatter * swell + 0.35 * _unit(grit) + 0.45 * roar
    return dsp.soft_clip(_unit(x), 1.5)


def tyre_scrub_loop(seconds: float = 6.0, seed: int = 48) -> np.ndarray:
    """Tyre scrub (ADR 0145, placeholder synthesis): trailer axles dragged sideways in a tight slow turn.

    Low rubbery groan (noise, formant ~180 / 420 Hz, slow irregular swell) + irregular creaks (Poisson-timed
    stick-slip bursts: 15-60 ms trains of band noise 500-1800 Hz, random spacing, no rhythm) + faint grit
    (gravel / tread blocks). Replaced by the REGEN-03 recording (el_tyre_scrub_loop) when it is imported.

    Runtime: gain from the lateral slip angle of the trailer axles at low speed (LayerMath.ScrubGain), pitch by
    the sliding speed (LayerMath.ScrubPitch)."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    g1 = _pf(rng, n, chain(hp(60.0, 0.7), bp(180.0, 2.0)))
    g2 = _pf(rng, n, chain(bp(420.0, 2.5), lp(900.0, 0.7)))
    swell = 1.0 + 0.45 * dsp.smooth_random_periodic(rng, n, max_cycles=int(1.5 * seconds), n_terms=5)
    rough = 0.6 + 0.4 * np.abs(dsp.smooth_random_periodic(rng, n, max_cycles=int(25 * seconds), n_terms=12))
    groan = (g1 + 0.7 * g2) * swell * rough
    creaks = np.zeros(n)
    t = 0.0
    while True:
        t += rng.exponential(0.35)            # mean 2.9 creaks/s, exponential spacing = no rhythm
        if t >= seconds:
            break
        dur = rng.uniform(0.015, 0.06)
        fc = rng.uniform(500.0, 1800.0)
        k = _noise_burst(rng, fc * 0.7, fc * 1.4, dur * 0.5, dur * 2.5)
        # stick-slip train inside the creak: 60-140 Hz chopping
        tt = np.arange(len(k)) / FS
        k *= 0.5 + 0.5 * np.abs(np.sin(np.pi * rng.uniform(60.0, 140.0) * tt))
        _add_circ(creaks, int(t * FS), k, rng.uniform(0.25, 1.0))
    grit = np.abs(rng.standard_normal(n)) ** 3
    grit = periodic_sosfilt(dsp.periodic_noise(rng, n) * _unit(periodic_sosfilt(grit, chain(lp(500.0, 0.7)))),
                            chain(hp(1200.0, 0.7), lp(5000.0, 0.7)))
    x = 1.0 * _unit(groan) + 0.55 * _unit(creaks) + 0.12 * _unit(grit)
    return dsp.soft_clip(_unit(x), 1.3)


# =========================================================================== RETARDER
def retarder_loop(seconds: float = 3.0, seed: int = 62, f_blade: float = 340.0) -> np.ndarray:
    """Hydrodynamic retarder (Intarder class): blade-pass whine + oil swirl rush + deep body.

    Runtime: gain from Retarder.Fill, pitch ~ gearbox output shaft speed (0.5..1.5)."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    fm = 0.006 * dsp.smooth_random_periodic(rng, n, max_cycles=int(5 * seconds), n_terms=5)
    ph = 2 * np.pi * np.cumsum(f_blade * (1 + fm)) / FS
    cyc = ph[-1] / (2 * np.pi)
    ph *= np.round(cyc) / cyc
    am = 1.0 + 0.15 * dsp.smooth_random_periodic(rng, n, max_cycles=int(7 * seconds), n_terms=5)
    whine = (np.sin(ph) + 0.55 * np.sin(2 * ph + 0.7) + 0.3 * np.sin(3 * ph + 1.3) + 0.14 * np.sin(5 * ph)) * am
    swirl = _pf(rng, n, chain(hp(140.0, 0.7), lp(1900.0, 0.7), peak(620.0, 1.0, 6.0), peak(1250.0, 1.5, 3.0)))
    swirl *= 1.0 + 0.3 * dsp.smooth_random_periodic(rng, n, max_cycles=int(11 * seconds), n_terms=8)
    body = _pf(rng, n, chain(hp(30.0), lp(160.0, 0.9), peak(85.0, 1.5, 4.0)))
    return 0.40 * whine / (np.max(np.abs(whine)) + 1e-9) + 0.55 * swirl + 0.5 * body


# =========================================================================== COMPRESSOR
def compressor_loop(seconds: float = 2.0, seed: int = 63, rate_hz: float = 14.0) -> np.ndarray:
    """Two-cylinder piston compressor: rhythmic 'pu-pu-pu' (alternating cylinders) + valve ticks + hum.

    28 strokes per 2 s loop. Runtime: gain while Air.CompressorLoaded and the engine runs, pitch ~ engine rpm / 1000."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    n_p = int(round(rate_hz * seconds))
    puff = _noise_burst(rng, 250.0, 1500.0, 0.014, 0.09) * 0.9
    thump = _damped_sine(88.0, 0.022, 0.11)
    tick = _damped_sine(2900.0, 0.0016, 0.012)
    clack = _damped_sine(1300.0, 0.004, 0.04)
    x = np.zeros(n)
    for k in range(n_p):
        t = (k + 0.04 * rng.standard_normal()) / n_p * seconds
        a = 1.0 if k % 2 == 0 else 0.72
        i0 = int(t * FS)
        _add_circ(x, i0, puff, 0.75 * a)
        _add_circ(x, i0, thump, 0.9 * a)
        _add_circ(x, i0 + int(0.011 * FS), tick, 0.30 * a)
        _add_circ(x, i0 + int(0.026 * FS), clack, 0.20 * a)
    hum = _pf(rng, n, chain(hp(45.0), lp(260.0, 0.8), peak(120.0, 1.5, 4.0))) * 0.25
    return _unit(x) + hum


# =========================================================================== PNEUMATIC ONE-SHOTS
def parking_brake_release(seed: int = 81) -> np.ndarray:
    """Spring-brake release (pull the yellow knob / switch off): valve click, short fill 'fff', shoe clunk."""
    rng = np.random.default_rng(seed)
    n = int(1.3 * FS)
    t = np.arange(n) / FS
    env = sx._env_attack_decay(n, 0.02, 0.26, hold_s=0.12)
    bright = chain(hp(1300.0, 0.7), peak(3000.0, 1.2, 4.0), lp(9000.0, 0.7))
    dark = chain(hp(450.0, 0.7), peak(1500.0, 1.0, 3.0), lp(3500.0, 0.7))
    bri = np.clip(0.2 + 0.8 * (t / 0.5), 0, 1) * np.exp(-np.maximum(t - 0.5, 0) / 0.4)
    hiss = sx._time_varying_hiss(rng, n, bright, dark, bri) * env
    x = 0.55 * hiss + sx._click(n, 1700.0, 0.004, 0.30)
    x += np.roll(sx._thump(n, 60.0, 0.05, 0.5), int(0.16 * FS)) * (t > 0.16)  # brake shoes leaving the drum
    x += sx._click(n, 800.0, 0.008, 0.2, at_s=0.16)
    return dsp.fade_edges(x, 0.0005, 0.15)


def air_dryer_purge_b(seed: int = 82) -> np.ndarray:
    """Softer, shorter regeneration 'psst' (variation of air_dryer_purge, avoids obvious repetition)."""
    rng = np.random.default_rng(seed)
    n = int(0.62 * FS)
    t = np.arange(n) / FS
    env = sx._env_attack_decay(n, 0.004, 0.085, hold_s=0.035)
    bright = chain(hp(1700.0, 0.7), peak(4200.0, 1.2, 5.0), lp(10500.0, 0.7))
    dark = chain(hp(600.0, 0.7), peak(1900.0, 1.0, 3.0), lp(4200.0, 0.7))
    hiss = sx._time_varying_hiss(rng, n, bright, dark, np.exp(-t / 0.12)) * env
    x = hiss * 0.9 + sx._thump(n, 85.0, 0.035, 0.35) + sx._click(n, 2100.0, 0.003, 0.2)
    return dsp.fade_edges(x, 0.0003, 0.08)


# =========================================================================== INDICATOR RELAY
def indicator_tick(seed: int = 91) -> np.ndarray:
    """Flasher relay contact closing, cab-referenced: sharp contact click + plastic dash body 'tik'."""
    rng = np.random.default_rng(seed)
    n = int(0.09 * FS)
    t = np.arange(n) / FS
    contact = signal.sosfilt(chain(hp(1800.0, 0.7), lp(7500.0, 0.7)), rng.standard_normal(n)) * np.exp(-t / 0.0013)
    body = np.sin(2 * np.pi * 1150.0 * t) * np.exp(-t / 0.011) + 0.5 * np.sin(2 * np.pi * 2380.0 * t) * np.exp(-t / 0.006)
    knock = np.sin(2 * np.pi * 430.0 * t) * np.exp(-t / 0.016)
    x = _unit(contact) * 0.7 + body * 0.55 + knock * 0.25
    return dsp.fade_edges(x, 0.0002, 0.02)


def indicator_tock(seed: int = 92) -> np.ndarray:
    """Relay contact opening: softer and lower than the 'tik' (armature drops back)."""
    rng = np.random.default_rng(seed)
    n = int(0.10 * FS)
    t = np.arange(n) / FS
    contact = signal.sosfilt(chain(hp(1100.0, 0.7), lp(5200.0, 0.7)), rng.standard_normal(n)) * np.exp(-t / 0.0016)
    body = np.sin(2 * np.pi * 820.0 * t) * np.exp(-t / 0.013) + 0.4 * np.sin(2 * np.pi * 1760.0 * t) * np.exp(-t / 0.007)
    knock = np.sin(2 * np.pi * 360.0 * t) * np.exp(-t / 0.02)
    x = _unit(contact) * 0.5 + body * 0.5 + knock * 0.3
    return dsp.fade_edges(x, 0.0002, 0.02)


# =========================================================================== AMBIENCE (industrial yard)
def ambient_industrial_bed_loop(seconds: float = 12.0, seed: int = 101) -> np.ndarray:
    """Distant industrial yard: far road traffic passes (swells + Doppler-ish sweeps), ventilation/mains hum,
    low wind, a few far metallic clanks. Always-on bed; level set by the zone."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    t = np.arange(n) / n
    # far traffic: continuous low band + 5 passes of band-limited noise whose centre sweeps
    base = _pf(rng, n, chain(hp(40.0), lp(420.0, 0.7), peak(120.0, 0.8, 4.0)))
    base *= 1.0 + 0.3 * dsp.smooth_random_periodic(rng, n, max_cycles=int(1.5 * seconds), n_terms=4)
    passes = np.zeros(n)
    for k in range(5):
        c = (k + rng.uniform(0.2, 0.8)) / 5
        width = rng.uniform(0.03, 0.06)
        w = np.exp(-0.5 * ((((t - c + 0.5) % 1.0) - 0.5) / width) ** 2)  # circular gaussian swell
        low = _pf(rng, n, chain(hp(60.0), lp(700.0, 0.7)))
        mid = _pf(rng, n, chain(hp(500.0), lp(2600.0, 0.7)))
        brightness = 0.35 + 0.4 * w  # nearest point = brighter tyre/engine noise
        passes += w * (low + brightness * mid) * rng.uniform(0.55, 1.0)
    # mains-related hum from transformers / ventilation: 100 Hz + 200 Hz, very low level, slightly drifting
    hum = (np.sin(2 * np.pi * 100 * seconds * t) + 0.5 * np.sin(2 * np.pi * 200 * seconds * t + 1.0)
           + 0.2 * np.sin(2 * np.pi * 300 * seconds * t + 2.0))
    hum *= 1.0 + 0.2 * dsp.periodic_lfo(n, 3, 0.4)
    vent = _pf(rng, n, chain(hp(150.0), lp(1100.0, 0.7), peak(480.0, 1.5, 5.0)))
    wind = _pf(rng, n, chain(hp(90.0), lp(1300.0, 0.6), peak(300.0, 0.7, 3.0)))
    wind *= 1.0 + 0.55 * dsp.smooth_random_periodic(rng, n, max_cycles=int(0.7 * seconds), n_terms=4)
    clanks = np.zeros(n)
    for _ in range(3):
        f = rng.uniform(500.0, 1100.0)
        k = _damped_sine(f, 0.09, 0.5)
        k[:19200] += 0.6 * _damped_sine(f * 2.76, 0.05, 0.4)
        k[:14400] += 0.3 * _damped_sine(f * 5.4, 0.03, 0.3)
        _add_circ(clanks, int(rng.uniform(0.05, 0.95) * n), k, rng.uniform(0.6, 1.0))
    clanks = signal.sosfilt(chain(lp(2500.0, 0.7)), clanks)
    return (0.75 * base + 0.55 * _unit(passes) + 0.10 * hum / 1.7 + 0.22 * vent + 0.35 * wind + 0.10 * _unit(clanks))


def forklift_loop(seconds: float = 8.0, seed: int = 102) -> np.ndarray:
    """Distant electric forklift: traction motor whine that rises/falls with each manoeuvre, hydraulic pump whine
    and a reversing beeper (~1 kHz, 50 % duty, 1.25 Hz). Played far away at low level; panned by the controller."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    u = np.arange(n) / n
    # motor speed: two accelerate/decelerate manoeuvres per loop
    speed = 0.5 - 0.5 * np.cos(2 * np.pi * 2 * u)
    speed = speed ** 1.3
    f_m = 380.0 + 520.0 * speed
    ph = 2 * np.pi * np.cumsum(f_m) / FS
    cyc = ph[-1] / (2 * np.pi)
    ph *= np.round(cyc) / cyc
    motor = (np.sin(ph) + 0.4 * np.sin(2 * ph + 0.5) + 0.2 * np.sin(3 * ph + 1.1)) * (0.25 + 0.75 * speed)
    pump_on = np.clip(np.sin(2 * np.pi * 3 * u + 0.8) * 3.0, 0.0, 1.0)  # lift cylinder: 3 lifts per loop
    pf = 150.0 + 90.0 * pump_on
    pph = 2 * np.pi * np.cumsum(pf) / FS
    pc = pph[-1] / (2 * np.pi)
    pph *= np.round(pc) / pc
    pump = (np.sin(pph) + 0.5 * np.sin(2 * pph)) * pump_on
    pump += 0.25 * periodic_sosfilt(dsp.periodic_noise(rng, n), chain(bp(600.0, 1.5))) * pump_on
    # reversing beeper: 1.25 Hz, 50 % duty, only during "reverse" parts of the manoeuvre
    cycles = int(round(1.25 * seconds))
    gate = (np.sin(2 * np.pi * cycles * u) > 0).astype(float)
    gate = periodic_sosfilt(gate, chain(lp(250.0, 0.7)))  # soft edges: no clicks
    rev = (np.sin(2 * np.pi * 2 * u) < 0).astype(float)  # second half of each manoeuvre = reversing
    rev = periodic_sosfilt(rev, chain(lp(30.0, 0.7)))
    beep = np.sin(2 * np.pi * 1000.0 * seconds * u) + 0.25 * np.sin(2 * np.pi * 3000.0 * seconds * u)
    beeper = beep * gate * rev
    noise = _pf(rng, n, chain(hp(200.0), lp(2500.0, 0.7))) * (0.08 + 0.25 * speed)
    x = 0.55 * motor + 0.35 * pump + 0.28 * beeper + noise
    return x


def bird_sparrow(seed: int = 111) -> np.ndarray:
    """House sparrow-like chatter: 5-9 short, sharp 'chirp' notes at 2.8-5 kHz with fast down-up FM."""
    rng = np.random.default_rng(seed)
    n = int(1.1 * FS)
    x = np.zeros(n)
    t0 = 0.05
    for _ in range(int(rng.integers(5, 8))):
        d = rng.uniform(0.045, 0.085)
        m = int(d * FS)
        tt = np.arange(m) / FS
        fc = rng.uniform(3000.0, 4600.0)
        f = fc * (1.0 + 0.22 * np.sin(2 * np.pi * rng.uniform(15, 30) * tt + rng.uniform(0, 3)) - 0.1 * tt / d)
        ph = 2 * np.pi * np.cumsum(f) / FS
        env = np.sin(np.pi * tt / d) ** 1.5
        note = (np.sin(ph) + 0.35 * np.sin(2 * ph)) * env
        i0 = int(t0 * FS)
        x[i0:i0 + m] += note * rng.uniform(0.6, 1.0)
        t0 += d + rng.uniform(0.03, 0.12)
        if t0 * FS + 0.1 * FS > n:
            break
    return dsp.fade_edges(x, 0.002, 0.05)


def bird_tit(seed: int = 112) -> np.ndarray:
    """Great-tit-like 'tsi-tsi-pe' whistle: two-note repeated phrase, clear tone 4.2 / 3.4 kHz."""
    n = int(1.3 * FS)
    x = np.zeros(n)
    t0 = 0.08
    for rep in range(3):
        for fa, fb, d in ((4500.0, 4150.0, 0.09), (3500.0, 3300.0, 0.11)):
            m = int(d * FS)
            tt = np.arange(m) / FS
            f = np.linspace(fa, fb, m)
            ph = 2 * np.pi * np.cumsum(f) / FS
            env = np.sin(np.pi * tt / d) ** 0.8
            x[int(t0 * FS):int(t0 * FS) + m] += (np.sin(ph) + 0.12 * np.sin(2 * ph)) * env
            t0 += d + 0.025
        t0 += 0.09
    return dsp.fade_edges(x, 0.004, 0.08)


def bird_crow_caw(seed: int = 113) -> np.ndarray:
    """Carrion-crow-like 'kraa': harsh glottal-pulse source (~420 Hz) through two sweeping formants."""
    rng = np.random.default_rng(seed)
    out = np.zeros(int(1.4 * FS))
    for k, t0 in enumerate((0.1, 0.68)):
        d = 0.42 - 0.06 * k
        m = int(d * FS)
        tt = np.arange(m) / FS
        f0 = 440.0 * (1.08 - 0.28 * (tt / d) ** 1.2) * (1 - 0.05 * k)
        ph = np.cumsum(f0) / FS
        glottal = (ph % 1.0) - 0.5  # saw
        glottal += 0.4 * rng.standard_normal(m) * 0.2  # breathiness / roughness
        glottal *= 1.0 + 0.25 * np.sin(2 * np.pi * 70.0 * tt)  # harsh amplitude flutter
        env = np.minimum(1.0, tt / 0.03) * np.exp(-np.maximum(tt - d * 0.45, 0) / (d * 0.35))
        y = np.zeros(m)
        # time-varying formants via block-wise bandpass (30 blocks, overlap-add with Hann)
        nb = 28
        for b in range(nb):
            a = int(b * m / nb)
            z = int(min(m, a + 2 * m / nb))
            if z - a < 32:
                continue
            u = b / nb
            f1 = 800.0 + 300.0 * (1 - u)
            f2 = 1500.0 + 500.0 * (1 - u)
            seg = glottal[a:z] * np.hanning(z - a)
            seg = signal.sosfilt(chain(bp(f1, 4.0), bp(f2, 5.0)), seg) * 2.0 + seg * 0.15
            y[a:z] += seg
        y *= env
        i0 = int(t0 * FS)
        out[i0:i0 + m] += y
    out = signal.sosfilt(chain(hp(250.0), lp(4500.0, 0.7)), out)
    return dsp.fade_edges(out, 0.004, 0.1)


# =========================================================================== CAB (interior) FILTER
CAB_PROFILES = {
    # name: (list of sos rows)
    # pneumatics / switches inside the shell: roll-off from 2.6 kHz, panel resonance, boomy low end
    "pneu": chain(hp(30.0), lp(2800.0, 0.6), lp(4600.0, 0.7), highshelf(1400.0, -6.0), peak(128.0, 2.0, 3.0), lowshelf(90.0, 3.0)),
    # tyre noise through the floor: heavier low-pass, floor boom
    "road": chain(hp(28.0), lp(1500.0, 0.6), lp(2600.0, 0.7), highshelf(900.0, -8.0), peak(90.0, 1.6, 4.0), peak(128.0, 2.0, 2.0)),
    # wind: leaks around doors and mirrors, whistle mostly filtered out
    "wind": chain(hp(35.0), lp(1700.0, 0.6), highshelf(700.0, -9.0), peak(110.0, 1.4, 3.0)),
    # mechanical units below the cab (compressor, retarder): transmitted structure-borne, strongly low-passed
    "mech": chain(hp(30.0), lp(2000.0, 0.6), lp(3200.0, 0.7), highshelf(1000.0, -7.0), peak(128.0, 2.0, 3.0), lowshelf(80.0, 2.5)),
    # outside world through glass and door seals: dull, quiet
    "ambient": chain(hp(40.0), lp(1100.0, 0.6), lp(1900.0, 0.7), highshelf(500.0, -10.0), lowshelf(120.0, 2.0)),
    # the relay lives in the cab: a light colouring only
    "dash": chain(hp(200.0), peak(900.0, 1.0, 2.0), lp(8000.0, 0.7)),
    # the same relay heard from outside: a faint, dull tick through the body
    "relay_ext": chain(hp(300.0), lp(1700.0, 0.7), lp(2600.0, 0.7), highshelf(900.0, -8.0)),
}


def cab_filter(x: np.ndarray, is_loop: bool, profile: str = "pneu") -> np.ndarray:
    """Interior perspective of an exterior layer. Loops stay seamless (periodic filtering);
    one-shots are zero-padded by 0.12 s so the filter ring-out is kept, then faded."""
    sos = CAB_PROFILES[profile]
    if is_loop:
        return periodic_sosfilt(x, sos)
    pad = np.concatenate([x, np.zeros(int(0.12 * FS))])
    y = signal.sosfilt(sos, pad)
    return dsp.fade_edges(y, 0.0, 0.1)
