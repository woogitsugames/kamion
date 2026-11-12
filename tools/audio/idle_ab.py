"""ADR 0148: 8 s before/after listening clips and spectra for the owner (cab perspective, compressor loaded).

    uv run --project tools/audio python tools/audio/idle_ab.py

A) Fixed operating points through the runtime mirror (runtime_sim.LayerGrid, same crossfade as EngineLayerGrid):
   600 rpm idle, 900 rpm no load, 900 rpm full load, 900 rpm engine brake (ebrake bank, brake 1, engine grid at load 0), standstill
   (no tyres/wind), engine + loaded air compressor at the runtime gains of TruckAudioController / EngineAudio:
   compressor cab gain = compressorVolume x cabCompressorFactor (0.35 x 0.75 before, 0.06 x 0.75 after), pitch rpm/1000;
   ElevenLabs cab engine x elCabEngineScale 0.7, engine brake x cabMix.engineBrake 0.85.
B) The coast from the PlayMode capture (IdleAudioCaptureTests, real TruckAudioController, D9 ~37 km/h, ~1100 rpm,
   load 0): mix_<set>/mix.wav, 8 s from coast start + 2 s.
Outputs artifacts/audio-idle/ab/*.wav (16-bit, peak-normalised per pair with one common gain) and ab_spectra.png.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

import el_demo as ed
import idle_render as ir
import runtime_sim as rs

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "artifacts" / "audio-idle"
FS = 48000
DUR = 8.0
COMP_BEFORE, COMP_AFTER, CAB_COMP = 0.35, 0.06, 0.75


def synth_dir() -> Path:
    for d in ir.DIRS[::-1]:
        if (d / "manifest.json").exists():
            return d
    raise FileNotFoundError("art-source/audio/generated/manifest.json")


def grid_render(g: rs.LayerGrid, rpm: float, load: float, gain: float) -> np.ndarray:
    out = []
    for _ in range(int(DUR * rs.FRAME_HZ)):
        g.update(rpm, load, gain)
        out.append(g.render(int(FS / rs.FRAME_HZ), FS))
    return np.concatenate(out)


def loop(x: np.ndarray, pitch: float, n: int, start: int = 0) -> np.ndarray:
    idx = start + pitch * np.arange(n)
    i0 = np.floor(idx).astype(np.int64)
    fr = idx - i0
    L = len(x)
    return x[i0 % L] * (1 - fr) + x[(i0 + 1) % L] * fr


def main():
    gen = synth_dir()
    rs.GEN = gen
    rs.ROOT = gen.parents[2]
    synth_man = json.loads((gen / "manifest.json").read_text(encoding="utf-8"))
    el_man = json.loads(ed.EL_MAN.read_text(encoding="utf-8"))
    comp = {"synth": ir.clip("compressor_cab_loop")[0], "el": ir.clip("el_compressor_cab_loop")[0]}
    abdir = OUT / "ab"
    abdir.mkdir(parents=True, exist_ok=True)
    n = int(DUR * FS)
    res = {}
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 5, figsize=(22, 8), sharey=True)
    for row, sset in enumerate(("synth", "el")):
        eng_scale = 0.7 if sset == "el" else 1.0
        cases = {}
        for case, rpm, load, brake in (("600_idle", 600.0, 0.0, 0.0), ("900_noload", 900.0, 0.0, 0.0), ("900_load", 900.0, 1.0, 0.0),
                                       ("900_ebrake", 900.0, 0.0, 1.0)):
            g = ed.load_grid_el(el_man, "engine", "cab", 6) if sset == "el" else rs.load_grid(synth_man, "engine", "cab", 6)
            rs.XFADE_COHERENCE = 0.0 if sset == "el" else 0.9
            eng = grid_render(g, rpm, load, eng_scale)
            if brake > 0:
                b = ed.load_grid_el(el_man, "ebrake", "cab", 3) if sset == "el" else rs.load_grid(synth_man, "ebrake", "cab", 3)
                eng = eng + grid_render(b, rpm, 0.0, 0.85 * eng_scale * brake)
            c = loop(comp[sset], rpm / 1000.0, n)
            cases[case] = (eng, c)
        # coast from the capture
        for tag in ("before", "after"):
            p = OUT / f"mix_{sset}{'_before' if tag == 'before' else ''}" / "mix.wav"
            if p.exists():
                lv = json.loads((p.parent / "levels.json").read_text())
                x, _ = sf.read(p)
                t0 = int((lv["t_coast0"] + 2.0) * FS)
                cases.setdefault("coast_capture", {})[tag] = x[t0:t0 + n]
        for ci, (case, val) in enumerate(cases.items()):
            if case == "coast_capture":
                before, after = val["before"], val["after"]
            else:
                eng, c = val
                before = eng + COMP_BEFORE * CAB_COMP * c
                after = eng + COMP_AFTER * CAB_COMP * c
            g = 0.5 / max(np.max(np.abs(before)), np.max(np.abs(after)))  # one gain per pair
            for tag, y in (("before", before), ("after", after)):
                fade = np.ones(n)
                k = int(0.02 * FS)
                fade[:k] = np.linspace(0, 1, k)
                fade[-k:] = np.linspace(1, 0, k)
                sf.write(abdir / f"{sset}_{case}_{tag}.wav", (y * g * fade).astype(np.float32), FS, subtype="PCM_16")
                f, P = signal.welch(y, FS, nperseg=8192)
                axs[row, ci].semilogx(f, 10 * np.log10(P + 1e-20), lw=1.4 if tag == "after" else 0.9,
                                      label=f"{tag}")
                env = np.abs(signal.hilbert(signal.sosfiltfilt(signal.butter(4, (60, 130), "bp", fs=FS, output="sos"), y)))
                res[f"{sset}_{case}_{tag}"] = {"rms_dbfs": round(float(20 * np.log10(np.sqrt(np.mean(y ** 2)))), 1),
                                               "am_cv_60_130": round(float(env.std() / env.mean()), 2)}
            if case != "coast_capture":
                eng, c = val
                res[f"{sset}_{case}_comp_minus_engine_db"] = {
                    "before": round(float(20 * np.log10(COMP_BEFORE * CAB_COMP * np.std(c) / np.std(eng))), 1),
                    "after": round(float(20 * np.log10(COMP_AFTER * CAB_COMP * np.std(c) / np.std(eng))), 1)}
            ax = axs[row, ci]
            ax.set_title(f"{sset} {case}")
            ax.set_xlim(20, 4000)
            ax.set_ylim(-120, -30)
            ax.grid(True, which="both", alpha=0.3)
            ax.legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(OUT / "ab_spectra.png", dpi=70)
    (OUT / "ab_levels.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    main()
