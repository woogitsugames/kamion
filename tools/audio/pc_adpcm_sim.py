"""ADR 0284: SIMULATION of the mobile ADPCM import on representative vehicle clips (why Standalone gets PCM).

    uv run python pc_adpcm_sim.py <out_dir>

Unity's ADPCM is a 4-bit IMA-style codec (3.5:1 per the Unity manual). This script runs the reference IMA ADPCM
algorithm (step table + index table of the IMA/DVI spec, one predictor per clip, no block resets) on the 16-bit
sources and reports the signal-to-noise ratio and the error spectrum. It is NOT Unity's encoder - the numbers show the
order of magnitude of the quantisation noise, not the exact Unity output.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

import dsp  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "game/Assets/_Project/Audio/Generated/Clips"
EL = ROOT / "game/Assets/_Project/Audio/ElevenLabs/Clips"
CLIPS = {
    "turbo_whistle_loop (synteza)": GEN / "sfx/turbo_whistle_loop.wav",
    "engine cab mid 1300 (synteza)": next(iter(sorted((GEN / "engine/cab").glob("*mid*1300*.wav"))), None),
    "engine ext on 1800 (synteza)": next(iter(sorted((GEN / "engine/ext").glob("*on*1800*.wav"))), None),
    "el_turbo_whine_cab_loop (EL)": next(iter(sorted(EL.rglob("el_turbo_whine_cab_loop.wav"))), None),
    "el_tyre_wet_cab_loop (EL)": next(iter(sorted(EL.rglob("el_tyre_wet_cab_loop.wav"))), None),
    "wind_cab_loop (synteza)": GEN / "sfx/wind_cab_loop.wav",
}

STEP = [7, 8, 9, 10, 11, 12, 13, 14, 16, 17, 19, 21, 23, 25, 28, 31, 34, 37, 41, 45, 50, 55, 60, 66, 73, 80, 88, 97, 107,
        118, 130, 143, 157, 173, 190, 209, 230, 253, 279, 307, 337, 371, 408, 449, 494, 544, 598, 658, 724, 796, 876, 963,
        1060, 1166, 1282, 1411, 1552, 1707, 1878, 2066, 2272, 2499, 2749, 3024, 3327, 3660, 4026, 4428, 4871, 5358, 5894,
        6484, 7132, 7845, 8630, 9493, 10442, 11487, 12635, 13899, 15289, 16818, 18500, 20350, 22385, 24623, 27086, 29794,
        32767]
IDX = [-1, -1, -1, -1, 2, 4, 6, 8]


def ima_roundtrip(x16: np.ndarray) -> np.ndarray:
    pred, idx = int(x16[0]), 0
    out = np.empty_like(x16)
    for i, s in enumerate(x16.tolist()):
        step = STEP[idx]
        diff = s - pred
        code = 0
        if diff < 0:
            code, diff = 8, -diff
        d = step >> 3
        if diff >= step: code |= 4; diff -= step; d += step  # noqa: E702
        step >>= 1
        if diff >= step: code |= 2; diff -= step; d += step  # noqa: E702
        step >>= 1
        if diff >= step: code |= 1; d += step  # noqa: E702
        pred = pred - d if code & 8 else pred + d
        pred = max(-32768, min(32767, pred))
        idx = max(0, min(88, idx + IDX[code & 7]))
        out[i] = pred
    return out


def main() -> int:
    out = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "artifacts/audio-pc-s23/adpcm")
    out.mkdir(parents=True, exist_ok=True)
    rep = {"note": "SIMULATION: reference IMA ADPCM, not Unity's encoder", "clips": {}}
    fig, axes = plt.subplots(len(CLIPS), 1, figsize=(10, 2.2 * len(CLIPS)), sharex=True)
    for ax, (name, path) in zip(axes, CLIPS.items()):
        if path is None or not Path(path).exists():
            rep["clips"][name] = "missing"
            continue
        x, fs = sf.read(path, dtype="int16", always_2d=True)
        x = x[:, 0].astype(np.int64)[: fs * 4]
        y = ima_roundtrip(x)
        e = (y - x).astype(np.float64) / 32768
        xs = x.astype(np.float64) / 32768
        snr = 10 * np.log10(np.mean(xs ** 2) / max(np.mean(e ** 2), 1e-20))
        f, px = signal.welch(xs, fs, nperseg=4096)
        _, pe = signal.welch(e, fs, nperseg=4096)
        hf = f > 4000
        rep["clips"][name] = {"file": str(Path(path).relative_to(ROOT)), "snr_db": round(float(snr), 1),
                              "signal_rms_dbfs": round(dsp.db(np.sqrt(np.mean(xs ** 2))), 1),
                              "noise_rms_dbfs": round(dsp.db(np.sqrt(np.mean(e ** 2))), 1),
                              "snr_above_4k_db": round(float(10 * np.log10(np.sum(px[hf]) / max(np.sum(pe[hf]), 1e-30))), 1)}
        ax.semilogx(f[1:], 10 * np.log10(px[1:] + 1e-20), lw=0.8, label="sygnał")
        ax.semilogx(f[1:], 10 * np.log10(pe[1:] + 1e-20), lw=0.8, label="błąd ADPCM (sym.)")
        ax.set_title(f"{name}: SNR {snr:.1f} dB", fontsize=9)
        ax.set_ylim(-160, -30)
        ax.legend(fontsize=7, loc="lower left")
    axes[-1].set_xlabel("Hz")
    fig.tight_layout()
    dsp.save_png_small(fig, out / "adpcm_sim_spectra.png", dpi=80)
    (out / "adpcm_sim.json").write_text(json.dumps(rep, indent=2, ensure_ascii=False), encoding="utf-8")
    print(json.dumps(rep, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
