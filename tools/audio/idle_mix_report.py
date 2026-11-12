"""ADR 0148: per-layer levels and spectra of a captured runtime mix (IdleAudioCaptureTests) vs the owner's recording.

    uv run --project tools/audio python tools/audio/idle_mix_report.py <capture.csv> <outdir> [--owner audio.wav]

Renders the whole mix and each layer group (engine grid, compressor, tyres, wind, ambience, turbo, clatter, other),
measures RMS in the pull and coast phases, the 14 Hz-band amplitude modulation of 60-130 Hz (compressor strokes) and
writes mix.wav, levels.json, spectra.png. Group = AudioSource GameObject name prefix (see TruckAudioController/EngineAudio).
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

import idle_render as ir

GROUPS = {
    "engine": ("engCab", "engExt"),
    "ebrake": ("brkCab", "brkExt"),
    "compressor": ("Compressor",),
    "tyres": ("Tyre", "Scrub", "Squeal"),
    "wind": ("Wind",),
    "ambient": ("Ambient", "Bed", "bird", "Bird", "Forklift", "forklift"),
    "turbo": ("turbo",),
    "clatter": ("idleClatter",),
}


def group_of(name: str) -> str:
    for g, keys in GROUPS.items():
        if any(name.startswith(k) or k in name for k in keys):
            return g
    return "other"


def rms_db(x: np.ndarray) -> float:
    return float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12))


def am(x: np.ndarray, fs: int = 48000, band=(60, 130)) -> tuple[float, float]:
    sos = signal.butter(4, band, btype="band", fs=fs, output="sos")
    e = np.abs(signal.hilbert(signal.sosfiltfilt(sos, x)))
    e = signal.decimate(signal.decimate(e, 8), 6)
    efs = fs / 48
    cv = float(e.std() / (e.mean() + 1e-12))
    e = e - e.mean()
    f, p = signal.welch(e, efs, nperseg=min(len(e), 2048))
    m = (f > 1.5) & (f < 60)
    return cv, float(f[m][np.argmax(p[m])])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("out")
    ap.add_argument("--owner")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    names, rows = ir.parse(Path(a.csv))
    fs, n = ir.FS, int(0.01 * ir.FS)
    phase = np.repeat(np.array([r[0]["phase"] for r in rows]), n)
    t_coast0 = next(r[0]["t"] for r in rows if r[0]["phase"] == "coast")
    # steady windows: last 3.5 s of the pull, coast from +2 s
    pull = (np.arange(len(phase)) / fs > t_coast0 - 3.5) & (phase == "pull")
    coast = (np.arange(len(phase)) / fs > t_coast0 + 2.0) & (phase == "coast")
    groups = sorted({group_of(nm) for nm in names})
    mix = ir.render(names, rows)
    sf.write(out / "mix.wav", mix.astype(np.float32), fs)
    rep = {"t_coast0": t_coast0, "mix": {"pull_db": rms_db(mix[pull]), "coast_db": rms_db(mix[coast]),
                                         "coast_am": am(mix[coast]), "pull_am": am(mix[pull])}}
    tel = [r[0] for r in rows]
    co = [r for r in tel if r["phase"] == "coast" and r["t"] > t_coast0 + 2]
    rep["coast_tel"] = {"rpm": [min(r["rpm"] for r in co), max(r["rpm"] for r in co)],
                        "load_max": max(r["load"] for r in co), "kmh": [min(r["kmh"] for r in co), max(r["kmh"] for r in co)],
                        "gear": sorted({r["gear"] for r in co}), "compressor_loaded_frac": float(np.mean([r["comp"] for r in co])),
                        "air": [min(r["air"] for r in co), max(r["air"] for r in co)], "ebrake_max": max(r["ebrake"] for r in co)}
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(1, 2, figsize=(14, 5), sharey=True)
    for ax, msk, lab in ((axs[0], pull, "pull (gas)"), (axs[1], coast, "coast (lift-off)")):
        f, p = signal.welch(mix[msk], fs, nperseg=8192)
        ax.semilogx(f, 10 * np.log10(p + 1e-20), "k", lw=2, label="mix")
        ax.set_title(lab)
    for g in groups:
        idx = [i for i, nm in enumerate(names) if group_of(nm) == g]
        y = ir.render([nm if i in idx else "\0skip" for i, nm in enumerate(names)],
                      [(t, [s if i in idx else None for i, s in enumerate(src)]) for t, src in rows])
        if not np.any(y):
            continue
        rep[g] = {"pull_db": rms_db(y[pull]), "coast_db": rms_db(y[coast]), "coast_am": am(y[coast])}
        for ax, msk in ((axs[0], pull), (axs[1], coast)):
            f, p = signal.welch(y[msk], fs, nperseg=8192)
            ax.semilogx(f, 10 * np.log10(p + 1e-20), lw=0.9, label=g)
    if a.owner:
        x, ofs = sf.read(a.owner)
        for ax, (t0, t1) in ((axs[0], (11, 14.5)), (axs[1], (17, 25))):
            f, p = signal.welch(x[int(t0 * ofs):int(t1 * ofs)], ofs, nperseg=8192)
            d = 10 * np.log10(p + 1e-20)
            ax.semilogx(f, d - d.max() + (ax.get_ylim()[1] - 3), "m--", lw=1.2, label=f"owner {t0}-{t1}s (shifted)")
        rep["owner"] = {"gas_am": am(x[int(11 * ofs):int(14.5 * ofs)], ofs), "lift_am": am(x[int(17 * ofs):int(25 * ofs)], ofs)}
    for ax in axs:
        ax.set_xlim(20, 4000)
        ax.set_ylim(-130, -30)
        ax.grid(True, which="both", alpha=0.3)
        ax.legend(fontsize=7)
        ax.set_xlabel("Hz")
    axs[0].set_ylabel("dB")
    fig.tight_layout()
    fig.savefig(out / "spectra.png", dpi=80)
    (out / "levels.json").write_text(json.dumps(rep, indent=1))
    print(json.dumps(rep, indent=1))


if __name__ == "__main__":
    main()
