"""Procedural pneumatic truck air horn loop and trailer/fifth-wheel metallic rattle one-shots (ADR 0355 addendum)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

import dsp
from dsp import FS, chain, hp, lp, peak, periodic_sosfilt
from sfx_layers import cab_filter


def _unit(x: np.ndarray) -> np.ndarray:
    m = float(np.max(np.abs(x)))
    return x / m if m > 1e-12 else x


def _taper(t: np.ndarray, duration: float, attack: float, release: float) -> np.ndarray:
    return np.sin(np.pi / 2 * np.minimum(
        np.clip(t / max(attack, 1e-6), 0.0, 1.0),
        np.clip((duration - t) / max(release, 1e-6), 0.0, 1.0),
    )) ** 2


def _metal_strike(t: np.ndarray, t0: float, freqs: tuple[float, ...], taus: tuple[float, ...], amps: tuple[float, ...],
                  rng: np.random.Generator, noise_amp: float = 0.0) -> np.ndarray:
    dt = t - t0
    active = dt >= 0.0
    if not np.any(active):
        return np.zeros_like(t)
    dt_a = np.where(active, dt, 0.0)
    out = np.zeros_like(t)
    for f, tau, a in zip(freqs, taus, amps):
        ph = float(rng.uniform(0.0, 2.0 * np.pi))
        out += a * np.sin(2.0 * np.pi * f * dt_a + ph) * np.exp(-dt_a / tau)
    if noise_amp > 0.0:
        n = rng.standard_normal(len(t))
        band = signal.sosfilt(chain(hp(750.0, 0.7), lp(4800.0, 0.7)), n)
        out += noise_amp * _unit(band) * np.exp(-dt_a / 0.012)
    env = np.where(active, np.minimum(1.0, dt_a / 0.0008), 0.0)
    return out * env


def horn_air_loop(duration: float = 1.0, seed: int = 3551) -> np.ndarray:
    """Dual-trumpet pneumatic truck air horn (seamless 1.0 s loop, integer cycles, no recordings)."""
    rng = np.random.default_rng(seed)
    n = round(duration * FS)
    t = np.arange(n) / FS
    # Exact integer frequencies in 1.0 s loop so phase wraps seamlessly at end->start.
    f1, f2 = 340.0, 428.0
    # Gentle pneumatic air-supply flutter (integer cycles per loop).
    pressure = 1.0 + 0.032 * dsp.smooth_random_periodic(rng, n, max_cycles=14, n_terms=6)
    fm = 0.003 * dsp.smooth_random_periodic(rng, n, max_cycles=10, n_terms=4)

    def trumpet(f0: float, phase0: float) -> np.ndarray:
        inst_f = f0 * (1.0 + fm)
        ph = 2.0 * np.pi * np.cumsum(inst_f) / FS
        # Wrap phase adjustment so end matches start seamlessly (fm has zero mean -> integral ~ integer cycles).
        ph = ph - ph[0] + phase0
        sig = np.zeros(n)
        weights = (1.00, 0.72, 0.56, 0.42, 0.30, 0.22, 0.16, 0.11, 0.08, 0.05)
        for k, w in enumerate(weights, start=1):
            sig += w * np.sin(k * ph + 0.18 * (k % 2))
        return sig

    raw = 0.54 * trumpet(f1, 0.0) + 0.48 * trumpet(f2, 1.1)
    # Flared horn bell resonance & upper roll-off (periodic steady-state IIR).
    horn_sos = chain(hp(160.0, 0.7), peak(1150.0, 1.3, 4.5), peak(1850.0, 1.8, 3.0), lp(3600.0, 0.7))
    body = periodic_sosfilt(raw * pressure, horn_sos)
    # Subtle compressed-air reed turbulence.
    reed_air = periodic_sosfilt(dsp.periodic_noise(rng, n), chain(hp(1100.0, 0.7), lp(4600.0, 0.7)))
    mixed = dsp.soft_clip(_unit(body) + 0.045 * _unit(reed_air) * pressure, 0.45)
    return _unit(mixed) * (10.0 ** (-3.0 / 20.0))


def trailer_rattle_chain_a(seed: int = 3552) -> np.ndarray:
    """Loose lashing chain / binder ring metallic jingle."""
    rng = np.random.default_rng(seed)
    duration = 0.24
    t = np.arange(round(duration * FS)) / FS
    x = np.zeros_like(t)
    for t0, scale in ((0.004, 1.0), (0.032, 0.72), (0.068, 0.58), (0.110, 0.42), (0.155, 0.28)):
        f_jit = float(rng.uniform(0.94, 1.07))
        x += scale * _metal_strike(
            t, t0,
            (840.0 * f_jit, 1580.0 * f_jit, 2340.0 * f_jit, 3490.0 * f_jit, 4620.0 * f_jit),
            (0.025, 0.028, 0.022, 0.016, 0.011),
            (0.42, 0.65, 0.85, 0.60, 0.32),
            rng, noise_amp=0.18,
        )
    x = signal.sosfilt(chain(hp(220.0, 0.7), lp(7500.0, 0.7)), x)
    return _unit(x) * _taper(t, duration, 0.002, 0.035) * (10.0 ** (-4.0 / 20.0))


def trailer_rattle_chain_b(seed: int = 3553) -> np.ndarray:
    """Heavier steel hook / sideboard latch clatter."""
    rng = np.random.default_rng(seed)
    duration = 0.28
    t = np.arange(round(duration * FS)) / FS
    x = np.zeros_like(t)
    for t0, scale in ((0.005, 1.0), (0.044, 0.65), (0.095, 0.48), (0.148, 0.26)):
        f_jit = float(rng.uniform(0.93, 1.06))
        x += scale * _metal_strike(
            t, t0,
            (210.0, 620.0 * f_jit, 1180.0 * f_jit, 1960.0 * f_jit, 3120.0 * f_jit),
            (0.020, 0.030, 0.025, 0.019, 0.013),
            (0.42, 0.70, 0.82, 0.65, 0.38),
            rng, noise_amp=0.22,
        )
    x = signal.sosfilt(chain(hp(140.0, 0.7), lp(6800.0, 0.7)), x)
    return _unit(x) * _taper(t, duration, 0.002, 0.045) * (10.0 ** (-4.0 / 20.0))


def trailer_rattle_tarp_a(seed: int = 3554) -> np.ndarray:
    """Curtain-sider buckle click + taut tarpaulin slap."""
    rng = np.random.default_rng(seed)
    duration = 0.22
    t = np.arange(round(duration * FS)) / FS
    slap = signal.sosfilt(chain(hp(90.0, 0.7), lp(950.0, 0.7)), rng.standard_normal(len(t)))
    slap = _unit(slap) * np.exp(-t / 0.024) * 0.55
    x = slap + _metal_strike(t, 0.003, (145.0, 980.0, 1840.0, 2950.0), (0.022, 0.020, 0.015, 0.010), (0.55, 0.68, 0.72, 0.40), rng, noise_amp=0.25)
    x += 0.55 * _metal_strike(t, 0.058, (1120.0, 2150.0, 3320.0), (0.018, 0.014, 0.010), (0.55, 0.65, 0.35), rng, noise_amp=0.15)
    return _unit(x) * _taper(t, duration, 0.002, 0.040) * (10.0 ** (-4.0 / 20.0))


def trailer_rattle_kingpin(seed: int = 3555) -> np.ndarray:
    """Heavy fifth-wheel jaw / kingpin slack thud-clank."""
    rng = np.random.default_rng(seed)
    duration = 0.26
    t = np.arange(round(duration * FS)) / FS
    x = _metal_strike(
        t, 0.004,
        (145.0, 310.0, 540.0, 1420.0, 2480.0),
        (0.032, 0.028, 0.022, 0.018, 0.012),
        (0.90, 0.78, 0.58, 0.48, 0.28),
        rng, noise_amp=0.30,
    )
    x += 0.42 * _metal_strike(t, 0.048, (175.0, 460.0, 1650.0), (0.024, 0.018, 0.013), (0.65, 0.50, 0.36), rng, noise_amp=0.14)
    x = signal.sosfilt(chain(hp(70.0, 0.7), lp(5500.0, 0.7)), x)
    return _unit(x) * _taper(t, duration, 0.002, 0.045) * (10.0 ** (-3.5 / 20.0))


def clips():
    horn_ext = horn_air_loop()
    horn_cab = cab_filter(horn_ext, is_loop=True, profile="pneu")
    horn_cab = np.clip(horn_cab, -0.95, 0.95)
    yield "horn_air_loop", horn_ext, "ext", True
    yield "horn_air_cab_loop", horn_cab, "cab", True

    rattle_specs = (
        ("trailer_rattle_chain_a", trailer_rattle_chain_a(), "mech"),
        ("trailer_rattle_chain_b", trailer_rattle_chain_b(), "mech"),
        ("trailer_rattle_tarp_a", trailer_rattle_tarp_a(), "ambient"),
        ("trailer_rattle_kingpin", trailer_rattle_kingpin(), "mech"),
    )
    for name, ext, cab_prof in rattle_specs:
        cab = cab_filter(ext, is_loop=False, profile=cab_prof)
        cab = np.clip(cab, -0.95, 0.95)
        yield name, ext, "ext", False
        yield name + "_cab", cab, "cab", False


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, samples, _, _ in clips():
        wavfile.write(args.output / f"{name}.wav", FS, np.rint(np.clip(samples, -1.0, 1.0) * 32767).astype(np.int16))
