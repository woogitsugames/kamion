"""ADR 0232: turbo and pneumatic layers re-synthesised from the physics the game already simulates.

Drop-in replacements (same clip names, same runtime laws, no C# change) for four layers of the first
bank (sfx_synth.py), which shaped a noise burst with a hand-drawn envelope:

* ``turbo_whistle_loop``  -- blade-pass tone with shaft-order side bands inside a compressor flow rush
  (the first version was an almost bare sine: tone 20 dB+ over its own noise floor).
* ``turbo_liftoff``       -- charge-air relief: the boosted intake volume blows down through the relief
  orifice (same adiabatic discharge model as the ADR 0176 dryer), the compressor spools down with the
  physics boost time constant.
* ``air_brake_release``   -- service-brake chambers exhaust through the quick-release / relay valves.
* ``parking_brake_set``   -- spring-brake chambers exhaust; the spring clunk lands where the chamber
  pressure crosses the physics spring-release pressure.

Pressures and time constants come from the vehicle definition (physics_params); volumes, orifices and
mix levels are WORKING_VALUE (fictional truck, nothing measured on a product). 100 % own synthesis.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

import dsp
import physics_params as pp
import synth0176 as s76
from dsp import FS, bp, chain, highshelf, hp, lp, peak, periodic_sosfilt
from sfx_synth import TURBO_REF_HZ

# --------------------------------------------------------------------------- turbo
COMPRESSOR_BLADES = 7          # main blades of the compressor wheel (WORKING_VALUE)
TURBO_PITCH_BASE = 0.6         # EngineAudio.turboPitchBase / turboPitchRange (runtime law, unchanged)
TURBO_PITCH_RANGE = 0.85
CHARGE_VOLUME_L = 18.0         # intercooler + charge pipes (WORKING_VALUE)
CHARGE_PRESSURE_BAR_G = 1.8    # boost at full load (WORKING_VALUE, UNVERIFIED: no sourced figure for the fictional engine)
RELIEF_ORIFICE_MM = 14.0       # relief / wastegate actuator vent path (WORKING_VALUE)


def turbo_whistle_loop(seconds: float = 3.0, seed: int = 2321) -> np.ndarray:
    """Compressor whine at runtime pitch 1 (blade-pass tone at TURBO_REF_HZ, as in the first bank).

    The loop holds a whole number of shaft revolutions, so the blade-pass tone, its shaft-order side
    bands (blade-to-blade spacing is never perfectly even) and the periodic noise all wrap exactly."""
    rng = np.random.default_rng(seed)
    n = int(seconds * FS)
    fm = 0.004 * dsp.smooth_random_periodic(rng, n, max_cycles=int(4 * seconds), n_terms=5)
    phase = 2 * np.pi * np.cumsum(TURBO_REF_HZ * (1.0 + fm)) / FS
    cycles = phase[-1] / (2 * np.pi)
    phase *= (np.round(cycles / COMPRESSOR_BLADES) * COMPRESSOR_BLADES) / cycles
    shaft = phase / COMPRESSOR_BLADES
    # flow turbulence modulates the tone (deeper and faster than the first version: 0.12 -> 0.28)
    am = 1.0 + 0.28 * dsp.smooth_random_periodic(rng, n, max_cycles=int(14 * seconds), n_terms=8)
    tone = np.sin(phase) * am + 0.16 * np.sin(2 * phase + 0.4)
    side = 0.20 * np.sin(phase - shaft + 0.9) + 0.14 * np.sin(phase + shaft + 2.1) \
        + 0.07 * np.sin(phase - 2 * shaft + 1.7)
    narrow = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(bp(TURBO_REF_HZ, 18.0), bp(TURBO_REF_HZ, 18.0)))
    narrow /= np.max(np.abs(narrow)) + 1e-9
    rush = periodic_sosfilt(dsp.periodic_noise(rng, n),
                            chain(hp(1100.0, 0.7), lp(9000.0, 0.7), peak(TURBO_REF_HZ * 1.25, 0.8, 5.0)))
    rush *= 1.0 + 0.35 * dsp.smooth_random_periodic(rng, n, max_cycles=int(6 * seconds), n_terms=6)
    rush /= np.max(np.abs(rush)) + 1e-9
    return 0.34 * (tone + side) + 0.30 * narrow + 0.42 * rush


def _discharge(rng, n: int, volume_l: float, p0_bar_g: float, d_mm: float, fpeak_max: float,
               at_s: float = 0.0, open_s: float = 0.004, seconds: float = 1.6):
    """Jet noise of a vessel blowing down through an orifice (ADR 0176 model). Returns (signal, blow-down)."""
    bd = s76.blowdown(volume_l, p0_bar_g, d_mm, seconds=seconds)
    pw = bd["mdot"] * np.maximum(bd["u"], 1.0) ** 5          # acoustic power ~ mdot U^5; amplitude = sqrt
    amp = np.sqrt(pw / pw[0]) * np.clip(bd["t"] / open_s, 0.0, 1.0)   # valve opening ramp
    d_j = d_mm * 1e-3 * np.maximum(1.0, bd["p"] / s76.P_AMB) ** 0.25
    fpk = np.clip(0.2 * bd["u"] / d_j, 700.0, fpeak_max)
    m = n - int(at_s * FS)
    jet = s76._jet_noise(rng, m, bd["t"], amp, fpk)
    out = np.zeros(n)
    out[n - m:] = jet
    return out, bd


def turbo_liftoff(seed: int = 2322) -> np.ndarray:
    """Throttle lift at boost: charge-air relief 'pssst' + the compressor spooling down."""
    rng = np.random.default_rng(seed)
    n = int(0.9 * FS)
    t = np.arange(n) / FS
    jet, _ = _discharge(rng, n, CHARGE_VOLUME_L, CHARGE_PRESSURE_BAR_G, RELIEF_ORIFICE_MM,
                        fpeak_max=4500.0, open_s=0.010, seconds=0.85)
    jet /= np.max(np.abs(jet)) + 1e-12
    # spool-down: shaft speed follows the physics boost state (first order, Engine.boostTimeConstant)
    tau = float(pp.engine()["boostTimeConstant"])
    f = TURBO_REF_HZ * (TURBO_PITCH_BASE + TURBO_PITCH_RANGE * np.exp(-t / tau))
    ph = 2 * np.pi * np.cumsum(f) / FS
    chirp = (np.sin(ph) + 0.12 * np.sin(ph * (1.0 - 1.0 / COMPRESSOR_BLADES) + 0.9)) * np.exp(-t / (0.7 * tau))
    chirp *= np.clip(t / 0.02, 0.0, 1.0)
    snap = s76._modes(n, 0.0, [(240.0, 0.018, 0.5), (1300.0, 0.004, 0.25)], rng, 0.02)
    x = jet + 0.22 * chirp + 0.12 * snap
    x = signal.sosfilt(chain(hp(180.0), lp(11000.0, 0.7)), x)
    return s76._finish(x, 0.15)


# --------------------------------------------------------------------------- pneumatic brakes
FRONT_CHAMBERS_L = 2.0         # two front service chambers at working stroke (WORKING_VALUE)
REAR_CHAMBERS_L = 2.8          # two rear service chambers (WORKING_VALUE)
SERVICE_EXHAUST_MM = 9.0       # quick-release / relay valve exhaust port (WORKING_VALUE)
SPRING_CHAMBERS_L = 3.6        # two spring-brake sections (WORKING_VALUE)
SPRING_EXHAUST_MM = 6.5        # parking relay valve exhaust (WORKING_VALUE)
REAR_DELAY_S = 0.025           # rear relay valve answers later than the front quick-release (WORKING_VALUE)


def chamber_pressure_bar() -> float:
    return float(pp.vehicle()["brakes"]["maxChamberPressureBar"])


def air_brake_release(seed: int = 2323) -> np.ndarray:
    """Service-brake release after a full application: front and rear chambers exhaust in parallel."""
    rng = np.random.default_rng(seed)
    n = int(0.8 * FS)
    p0 = chamber_pressure_bar()
    front, _ = _discharge(rng, n, FRONT_CHAMBERS_L, p0, SERVICE_EXHAUST_MM, fpeak_max=6500.0, seconds=0.75)
    rear, _ = _discharge(rng, n, REAR_CHAMBERS_L, p0, SERVICE_EXHAUST_MM, fpeak_max=5600.0,
                         at_s=REAR_DELAY_S, seconds=0.75)
    jets = front / (np.max(np.abs(front)) + 1e-12) + 0.9 * rear / (np.max(np.abs(rear)) + 1e-12)
    jets /= np.max(np.abs(jets)) + 1e-12
    chuck = s76._modes(n, 0.0, [(95.0, 0.03, 0.45), (1900.0, 0.004, 0.25)], rng, 0.02) \
        + 0.6 * s76._modes(n, REAR_DELAY_S, [(120.0, 0.025, 0.4), (1500.0, 0.004, 0.2)], rng, 0.02)
    x = jets + 0.35 * chuck
    x = signal.sosfilt(chain(hp(60.0), highshelf(8000.0, -3.0), lp(12000.0, 0.7)), x)
    return s76._finish(x, 0.2)


def spring_clunk_time() -> float:
    """Time after the valve opens at which the spring-brake chambers fall to the physics spring-release
    pressure (AirDefinition.springReleaseStartBar): the springs take over and the push rods seat."""
    bd = s76.blowdown(SPRING_CHAMBERS_L, chamber_pressure_bar(), SPRING_EXHAUST_MM, seconds=3.0)
    target = float(pp.vehicle()["air"]["springReleaseStartBar"]) * 1e5 + s76.P_AMB
    below = np.nonzero(bd["p"] <= target)[0]
    return float(bd["t"][below[0]]) if len(below) else float(bd["t"][-1])


def parking_brake_set(seed: int = 2324) -> np.ndarray:
    """Spring-brake application: long exhaust of the spring chambers, valve knock, spring clunk."""
    rng = np.random.default_rng(seed)
    n = int(1.7 * FS)
    jet, _ = _discharge(rng, n, SPRING_CHAMBERS_L, chamber_pressure_bar(), SPRING_EXHAUST_MM,
                        fpeak_max=5200.0, open_s=0.008, seconds=1.6)
    jet /= np.max(np.abs(jet)) + 1e-12
    t_clunk = spring_clunk_time()
    knock = s76._modes(n, 0.0, [(70.0, 0.05, 0.6), (1400.0, 0.006, 0.35)], rng, 0.02)
    clunk = s76._modes(n, t_clunk, [(88.0, 0.045, 0.5), (340.0, 0.02, 0.35), (900.0, 0.01, 0.2)], rng, 0.02)
    x = jet + 0.35 * knock + 0.30 * clunk
    x = signal.sosfilt(chain(hp(50.0), highshelf(7500.0, -3.0), lp(12000.0, 0.7)), x)
    return s76._finish(x, 0.25)


# --------------------------------------------------------------------------- registry
#  clip name in the bank: (function, is_loop)
LAYERS = {
    "turbo_whistle_loop": (turbo_whistle_loop, True),
    "turbo_liftoff": (turbo_liftoff, False),
    "air_brake_release": (air_brake_release, False),
    "parking_brake_set": (parking_brake_set, False),
}
