"""Find loops that sound like a 'siren' (ADR 0142 bug from the owner, APK 0138): a tonal whine whose pitch or level
rises and falls every few seconds, heard at idle and while driving, in both sound sets.

    uv run python siren_scan.py

For every loop of the procedural set (main art-source/audio/generated) and the ElevenLabs set (el_manifest.json):
  - tonal salience track: per 50 ms frame the strongest peak 150-4000 Hz over the median spectrum (dB) and its frequency
  - pitch sweep: (p95 - p5) of that frequency in semitones where the peak is salient (> 12 dB)
  - periodicity of the tonal level envelope: max autocorrelation for lags 1.5-8 s (the loop wraps, circular ACF)
A loop is flagged when it carries a salient tone (> 12 dB in > 30 % of frames) that sweeps > 3 semitones or whose level
envelope repeats with ACF > 0.5 at a multi-second period. Output: artifacts/audio-fx/siren_scan.txt
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal

from el_analyze import MAIN
from el_prepare import ROOT

FS = 48000


def scan(x: np.ndarray) -> dict:
    nper = 4096
    f, t, Z = signal.stft(x, FS, nperseg=nper, noverlap=nper - 2400)
    m = 20 * np.log10(np.abs(Z) + 1e-12)
    band = (f > 150) & (f < 4000)
    mb = m[band]
    floor = np.median(mb, axis=0, keepdims=True)
    # local prominence: peak vs a running median over frequency
    k = 15
    from scipy.ndimage import median_filter
    loc = median_filter(mb, size=(k, 1), mode="nearest")
    prom = mb - loc
    idx = np.argmax(prom, axis=0)
    sal = prom[idx, np.arange(prom.shape[1])]
    fr = f[band][idx]
    lvl = mb[idx, np.arange(prom.shape[1])] - floor[0]
    tonal = sal > 12
    share = float(tonal.mean())
    sweep = 0.0
    if tonal.sum() > 5:
        ft = fr[tonal]
        sweep = 12 * math.log2(np.percentile(ft, 95) / max(np.percentile(ft, 5), 1.0))
    env = np.where(tonal, lvl, np.min(lvl))
    env = env - env.mean()
    hop = (nper - 2400) / FS
    acf_best, lag_best = 0.0, 0.0
    if np.std(env) > 1e-6:
        F = np.fft.rfft(env)
        ac = np.fft.irfft(F * np.conj(F), len(env))
        ac /= ac[0]
        lo, hi = int(1.5 / hop), min(int(8.0 / hop), len(env) // 2)
        if hi > lo:
            j = lo + int(np.argmax(ac[lo:hi]))
            acf_best, lag_best = float(ac[j]), j * hop
    return {"tonal_share": share, "sweep_st": sweep, "env_acf": acf_best, "env_period_s": lag_best,
            "f_median": float(np.median(fr[tonal])) if tonal.any() else 0.0}


def main() -> None:
    items = []
    syn = MAIN / "art-source" / "audio" / "generated" / "manifest.json"
    for s in json.loads(syn.read_text(encoding="utf-8"))["sfx"]:
        if s["name"].endswith("_loop"):
            items.append(("synth", s["name"], MAIN / s["file"]))
    el = ROOT / "game" / "Assets" / "_Project" / "Audio" / "ElevenLabs" / "el_manifest.json"
    for s in json.loads(el.read_text(encoding="utf-8"))["sfx"]:
        if s["loop"]:
            items.append(("el", s["name"], ROOT / s["file"]))
    lines = []
    for setname, name, path in items:
        x, fs = sf.read(path, always_2d=True)
        x = x.mean(axis=1)
        if len(x) < 2 * FS:
            x = np.tile(x, int(math.ceil(2 * FS / len(x))) + 1)
        r = scan(np.tile(x, 2))  # two wraps: periods up to the loop length are visible
        flag = r["tonal_share"] > 0.3 and (r["sweep_st"] > 3 or (r["env_acf"] > 0.5 and r["env_period_s"] >= 1.5))
        lines.append(f"{'SIREN?' if flag else '      '} {setname:5s} {name:28s} tonal {100 * r['tonal_share']:5.1f}%  f {r['f_median']:6.0f} Hz  "
                     f"sweep {r['sweep_st']:5.1f} st  env ACF {r['env_acf']:.2f} @ {r['env_period_s']:.1f} s")
    out = ROOT / "artifacts" / "audio-fx" / "siren_scan.txt"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
