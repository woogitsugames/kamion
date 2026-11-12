"""Check the prepared ElevenLabs layers (ADR 0137): pitch on the nominal rpm, seamless wrap, levels.

    uv run python el_verify.py

Reads game/Assets/_Project/Audio/ElevenLabs/el_manifest.json, writes artifacts/audio-el/verify/{verify.json,grid_*.png,seams.png}.
Per loop: dominant 20-120 Hz line vs rpm_exact/20 (error %), seam jump ratio (|x[0]-x[-1]| / p99.9 |dx|),
HF spike at the wrap of the loop played twice (dB over median), LUFS and peak. Exit 1 when a loop fails
(pitch error > 4 %, seam ratio >= 1, wrap spike >= 6 dB, peak > -1 dBFS).
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

from el_analyze import db, lufs, prominence_db, seam, welch_db, yin_f0  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MAN = ROOT / "game" / "Assets" / "_Project" / "Audio" / "ElevenLabs" / "el_manifest.json"
OUT = ROOT / "artifacts" / "audio-regen01" / "verify"


def dominant(x: np.ndarray, fs: int, near: float) -> float:
    f, p = welch_db(np.tile(x, 2), fs, 1 << 16)
    pr = prominence_db(f, p)
    k = (f > near * 0.85) & (f < near * 1.15)
    return float(f[k][np.argmax(pr[k])])


def band_levels(x: np.ndarray, fs: int) -> np.ndarray:
    """1/3-octave band levels 50 Hz-12.5 kHz (dB) after removing the broadband level (mean over bands)."""
    f, p = signal.welch(x, fs, nperseg=1 << 14)
    centers = 1000 * 2 ** (np.arange(-13, 12) / 3)
    lv = []
    for c in centers:
        k = (f >= c * 2 ** (-1 / 6)) & (f < c * 2 ** (1 / 6))
        lv.append(10 * np.log10(p[k].sum() + 1e-20))
    lv = np.array(lv)
    return lv - lv.mean()


def timbre_steps(man: dict, root: Path) -> dict:
    """Spectral-shape distance between adjacent rpm cells of each row (mean |delta| of normalised 1/3-octave levels, dB).
    Cells from different recordings jump; one source keeps it low (ADR 0138: ext/on row cut from one sweep)."""
    out = {}
    for persp in ("ext", "cab"):
        for layer in ("off", "on"):
            cells = sorted([c for c in man["clips"] if c["kind"] == "engine" and c["perspective"] == persp and c["layer"] == layer],
                           key=lambda c: c["rpm"])
            bl = [band_levels(sf.read(root / c["file"])[0], 48000) for c in cells]
            steps = [float(np.mean(np.abs(bl[i + 1] - bl[i]))) for i in range(len(bl) - 1)]
            out[f"{persp}_{layer}"] = {"steps_db": [round(v, 2) for v in steps], "mean_db": round(float(np.mean(steps)), 2),
                                       "sources": len({c["source"] for c in cells})}
    return out


def main() -> int:
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(ROOT), help="repo root whose el_manifest.json + clips to check (e.g. main, for A/B)")
    ap.add_argument("--timbre-only", action="store_true")
    a = ap.parse_args()
    root = Path(a.root)
    man = json.loads((root / MAN.relative_to(ROOT)).read_text(encoding="utf-8"))
    ts = timbre_steps(man, root)
    print("timbre steps between adjacent cells:", json.dumps(ts))
    if a.timbre_only:
        return 0
    (OUT).mkdir(parents=True, exist_ok=True)
    (OUT / "timbre.json").write_text(json.dumps(ts, indent=1), encoding="utf-8")
    OUT.mkdir(parents=True, exist_ok=True)
    res, bad = [], []
    loops = [dict(c, loop=True) for c in man["clips"]] + [s for s in man["sfx"] if s["loop"]]
    for c in loops:
        x, fs = sf.read(ROOT / c["file"])
        s = seam(x, fs)
        r = {"name": c["name"], "lufs": lufs(x, fs), "peak_dbfs": db(np.abs(x).max()), **s, "dur_s": len(x) / fs}
        if "rpm_exact" in c:
            f_exp = c["rpm_exact"] / 20
            fd = dominant(x, fs, f_exp)
            r["dom_hz"], r["expected_hz"], r["pitch_err_pct"] = fd, f_exp, 100 * (fd - f_exp) / f_exp
            # octave check (ADR 0138, report only): period of the cell vs the grid line; ratio ~0.5 at low
            # aperiodicity = the loop is heard an octave below its neighbours
            f_y, ap = yin_f0(x, fs)
            r["yin_ratio"], r["yin_aperiodicity"] = f_y / f_exp, ap
            r["octave_low"] = bool(ap < 0.35 and f_y / f_exp < 0.7)
        fail = (abs(r.get("pitch_err_pct", 0)) > 4 or s["seam_jump_ratio"] >= 1 or s["seam_hf_spike_db"] >= 6
                or r["peak_dbfs"] > -1)
        r["pass"] = not fail
        if fail:
            bad.append(c["name"])
        res.append(r)
        print(f"{c['name']:28s} {r['lufs']:6.1f} LUFS pk {r['peak_dbfs']:5.1f}  seam {s['seam_jump_ratio']:.2f} "
              f"wrapHF {s['seam_hf_spike_db']:4.1f} dB  pitch {r.get('pitch_err_pct', 0):+5.1f}%  "
              f"yin {r.get('yin_ratio', 0):4.2f} ap {r.get('yin_aperiodicity', 0):4.2f}{' OCTAVE-LOW' if r.get('octave_low') else ''}  "
              f"{'OK' if not fail else 'FAIL'}")
    (OUT / "verify.json").write_text(json.dumps(res, indent=1), encoding="utf-8")

    # grid sheet: every engine cell, loop played twice (wrap in the middle), 0-300 Hz with rpm/20 harmonics
    for persp in ("ext", "cab"):
        cells = [c for c in man["clips"] if c["kind"] == "engine" and c["perspective"] == persp]
        fig, axs = plt.subplots(2, 6, figsize=(18, 6), squeeze=False)
        for c in cells:
            i = 0 if c["layer"] == "off" else 1
            j = man["rpm_grid"].index(c["rpm"])
            x, fs = sf.read(ROOT / c["file"])
            y = np.tile(x, 2)
            f, t, S = signal.spectrogram(y, fs, nperseg=1 << 14, noverlap=(1 << 14) * 7 // 8)
            k = f <= 300
            ax = axs[i, j]
            ax.pcolormesh(t, f[k], 10 * np.log10(S[k] + 1e-20), shading="auto", cmap="magma",
                          vmin=10 * np.log10(S[k].max()) - 60)
            for h in range(1, 6):
                ax.axhline(h * c["rpm"] / 20, color="cyan", lw=0.5, ls=":")
            ax.axvline(len(x) / fs, color="w", lw=0.6)
            ax.set_title(f"{c['name']}  src {c['source']}  x{c['pitch_ratio']:.2f}", fontsize=6)
            ax.tick_params(labelsize=6)
        fig.suptitle(f"ElevenLabs engine grid ({persp}) - loop x2 (white = wrap), dotted = k*rpm/20", fontsize=9)
        fig.tight_layout()
        fig.savefig(OUT / f"grid_{persp}.png", dpi=70)
        plt.close(fig)
    low = [r["name"] for r in res if r.get("octave_low")]
    print("octave-low cells (report):", low if low else "none")
    print("FAIL:", bad if bad else "none")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
