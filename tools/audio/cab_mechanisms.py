"""Procedural wiper sweeps, park contact and service-brake squeal (ADR 0355)."""

from pathlib import Path

import numpy as np
from scipy import signal
from scipy.io import wavfile

from dsp import FS, chain, hp, lp
from sfx_layers import cab_filter


def taper(t, duration, attack, release):
    return np.sin(np.pi / 2 * np.minimum(
        np.clip(t / attack, 0, 1), np.clip((duration - t) / release, 0, 1))) ** 2


def sweep(wet):
    # Reference duration of WiperDrive.SlowSeconds. Both strokes share the
    # blade's speed envelope and reverse halfway through the clip.
    duration = 1.2
    t = np.arange(round(duration * FS)) / FS
    u = t / duration
    speed = np.abs(np.sin(2 * np.pi * u))
    rng = np.random.default_rng(355)
    noise = rng.standard_normal(len(t))
    motor_phase = 2 * np.pi * np.cumsum(105 + 34 * speed) / FS
    motor = (np.sin(motor_phase) + 0.30 * np.sin(3 * motor_phase)) * (0.40 + 0.60 * speed)
    if wet:
        blade = 0.24 * signal.sosfilt(chain(hp(500), lp(3200)), noise) * speed
    else:
        chatter = (0.6 + 0.4 * np.sin(2 * np.pi * (32 * t + 1.5 * np.sin(2 * np.pi * u)))) ** 2
        band = signal.sosfilt(chain(hp(700), lp(3300)), noise)
        blade = (0.35 * band + 0.23 * np.sin(7 * motor_phase)) * chatter * speed
    return (0.14 * motor + blade) * taper(t, duration, 0.025, 0.026)


def park():
    t = np.arange(round(0.10 * FS)) / FS
    impact = np.sin(2 * np.pi * 230 * t) + 0.34 * np.sin(2 * np.pi * 680 * t)
    return impact * np.exp(-64 * t) * taper(t, 0.10, 0.003, 0.015)


def brake():
    duration = 0.27
    t = np.arange(round(duration * FS)) / FS
    u = t / duration
    phase = 2 * np.pi * (1900 * t - 190 * t * u + 3 * np.sin(2 * np.pi * 7 * t) / (2 * np.pi * 7))
    body = (np.sin(phase) + 0.28 * np.sin(1.47 * phase) + 0.16 * np.sin(2 * phase))
    return body * (0.78 + 0.22 * np.sin(2 * np.pi * 23 * t)) * taper(t, duration, 0.044, 0.105)


def clips():
    for name, raw in (("wiper_dry", sweep(False)), ("wiper_wet", sweep(True)),
                      ("wiper_park", park()), ("brake_service_squeal", brake())):
        if name == "brake_service_squeal":
            ext = raw * (0.70 / np.max(np.abs(raw)))
            cab = cab_filter(ext, False, "pneu")
        else:
            # The motor is fixed to the cab. The rubber and stop are heard
            # through the glass and cowl from outside.
            cab = raw * (0.56 / np.max(np.abs(raw))) if name == "wiper_park" else raw
            ext = 0.68 * cab
        yield name, ext, "ext"
        yield name + "_cab", cab, "cab"


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    for name, samples, _ in clips():
        wavfile.write(args.output / f"{name}.wav", FS, np.rint(samples * 32767).astype(np.int16))
