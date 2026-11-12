"""Short A/B listening files for ADR 0142 (owner: phone speaker + headphones), each <= 30 s, OGG.

    uv run python el_fx_ab.py
Output artifacts/audio-fx/ab/:
  ab_pneumatics.ogg  synthesis then ElevenLabs, pairs: service-brake release, parking set, parking release, dryer purge
                     A/B, AMT shift (synthesis) vs ElevenLabs up / down
  ab_cab.ogg         relay tick/tock x4 (synthesis, then ElevenLabs), then ElevenLabs only: cab switch, door open, door
                     close, horn 1.2 s, fifth-wheel coupling, suspension bump, reversing beeper 3 s
  ab_loops.ogg       3 s synthesis -> 3 s ElevenLabs each: tyres wet / concrete / gravel (exterior), dry tyres in the cab,
                     wind in the cab, compressor, ambience bed
  ab_turbo.ogg       boost ramp 0 -> 1 -> 0 over 9 s at the runtime pitch/gain mapping: v1 whistle, then v2 (REGEN-02
                     whine + procedural rush)
Levels are the clips' own (loudness-matched to the synthesis) times the runtime mix constants where relevant.
"""

from __future__ import annotations

import json
import subprocess

import numpy as np
import soundfile as sf

from el_analyze import MAIN
from el_prepare import ROOT

FS = 48000
OUT = ROOT / "artifacts" / "audio-fx" / "ab"


def _index() -> tuple[dict, dict]:
    syn = json.loads((MAIN / "art-source/audio/generated/manifest.json").read_text(encoding="utf-8"))
    el = json.loads((ROOT / "game/Assets/_Project/Audio/ElevenLabs/el_manifest.json").read_text(encoding="utf-8"))
    return {s["name"]: MAIN / s["file"] for s in syn["sfx"]}, {s["name"]: ROOT / s["file"] for s in el["sfx"]}


SYN, EL = _index()


def load(name: str, el: bool) -> np.ndarray:
    x = sf.read((EL if el else SYN)[name])[0]
    return x.mean(axis=1) if x.ndim > 1 else x


def gap(s: float) -> np.ndarray:
    return np.zeros(int(s * FS))


def loop_for(x: np.ndarray, s: float) -> np.ndarray:
    n = int(s * FS)
    y = np.tile(x, n // len(x) + 1)[:n]
    r = int(0.03 * FS)
    y[:r] *= np.linspace(0, 1, r)
    y[-r:] *= np.linspace(1, 0, r)
    return y


def varispeed(x: np.ndarray, pitch: np.ndarray) -> np.ndarray:
    """Loop playback with a time-varying pitch (like AudioSource.pitch)."""
    pos = np.cumsum(pitch) % len(x)
    return np.interp(pos, np.arange(len(x)), x)


def write(name: str, parts: list[np.ndarray]) -> None:
    y = np.concatenate(parts)
    pk = np.abs(y).max()
    if pk > 0.89:
        y *= 0.89 / pk
    assert len(y) / FS <= 30.0, (name, len(y) / FS)
    OUT.mkdir(parents=True, exist_ok=True)
    # libsndfile's Vorbis encoder overflows the stack on Windows for long single writes: WAV + ffmpeg (libvorbis q5)
    wav = OUT / (name[:-4] + ".wav")
    sf.write(wav, y.astype(np.float32), FS, subtype="PCM_16")
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(wav), "-c:a", "libvorbis", "-q:a", "5", str(OUT / name)], check=True)
    wav.unlink()
    print(f"{name}: {len(y) / FS:.1f} s")


def main() -> None:
    p = []
    for s, e in (("air_brake_release", "el_air_brake_release"), ("parking_brake_set", "el_parking_brake_set"),
                 ("parking_brake_release", "el_parking_brake_release"), ("air_dryer_purge", "el_air_dryer_purge"),
                 ("air_dryer_purge_b", "el_air_dryer_purge_b")):
        p += [0.55 * load(s, False), gap(0.6), 0.55 * load(e, True), gap(1.0)]
    p += [0.33 * load("gearshift_air_cab", False), gap(0.6), 0.33 * load("el_gearshift_up", True), gap(0.5),
          0.33 * load("el_gearshift_down", True), gap(0.5)]
    write("ab_pneumatics.ogg", p)

    def relay(el: bool) -> list[np.ndarray]:
        tk, tc = (load("el_indicator_tick", True), load("el_indicator_tock", True)) if el else \
                 (load("indicator_tick_cab", False), load("indicator_tock_cab", False))
        out = []
        for _ in range(4):
            out += [0.55 * tk, gap(0.333 - len(tk) / FS), 0.55 * tc, gap(0.333 - len(tc) / FS)]
        return out
    c = relay(False) + [gap(0.5)] + relay(True) + [gap(0.8)]
    c += [0.45 * load("el_cab_switch", True), gap(0.6), 0.8 * load("el_door_open", True), gap(0.3),
          0.8 * load("el_door_close", True), gap(0.5), 0.9 * loop_for(load("el_horn_loop", True), 1.2), gap(0.6),
          0.9 * load("el_trailer_couple", True), gap(0.4), 0.8 * load("el_susp_bump", True), gap(0.4),
          0.45 * loop_for(load("el_reverse_beeper_loop", True), 3.0)]
    write("ab_cab.ogg", c)

    l = []
    for s, e in (("tyre_wet_loop", "el_tyre_wet_loop"), ("tyre_concrete_loop", "el_tyre_concrete_loop"),
                 ("tyre_gravel_loop", "el_tyre_gravel_loop"), ("road_roll_cab_loop", "el_tyre_dry_cab_loop"),
                 ("wind_cab_loop", "el_wind_cab_loop"), ("compressor_loop", "el_compressor_loop"),
                 ("ambient_bed_loop", "el_ambient_bed_loop")):
        l += [0.5 * loop_for(load(s, False), 1.9), gap(0.1), 0.5 * loop_for(load(e, True), 1.9), gap(0.15)]
    write("ab_loops.ogg", l)

    n = int(9 * FS)
    t = np.arange(n) / n
    boost = np.sin(np.pi * t) ** 2
    thr = np.clip(boost * 1.4, 0, 1)
    v1 = 0.11 * boost ** 1.5 * (0.35 + 0.65 * thr) * varispeed(load("turbo_whistle_loop", False), 0.6 + 0.85 * boost)
    rpm_n = boost
    wg = boost ** 1.5 * (0.35 + 0.65 * thr)
    rg = (0.15 * rpm_n + 0.85 * boost ** 1.2 * (0.4 + 0.6 * rpm_n)) * (0.5 + 0.5 * thr)
    v2 = (0.10 * wg * varispeed(load("el_turbo_whine_loop", True), 0.55 + 0.9 * boost)
          + 0.18 * rg * varispeed(load("el_turbo_rush_loop", True), 0.85 + 0.3 * boost + 0.1 * rpm_n))
    g = 4.0  # turbo alone is quiet by design (it sits under the engine): +12 dB for listening
    write("ab_turbo.ogg", [g * v1, gap(1.0), g * v2])


if __name__ == "__main__":
    main()
