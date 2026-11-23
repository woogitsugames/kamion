"""Objective QA of speech files (GPS voice, ADR 0328): loudness, noise floor, F0, rate, clipping, spectrogram PNG.

usage: uv run --project tools/audio python tools/audio/gps/voice_qa.py <file-or-dir> [--png <dir>] [--chars-json <json>]
Decodes anything ffmpeg reads (mp3/wav) to 44.1 kHz mono float. No network, no third-party audio.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

SR = 44100


def decode(path: Path, sr: int = SR) -> np.ndarray:
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"],
                         check=True, capture_output=True).stdout
    return np.frombuffer(raw, dtype=np.float32).astype(np.float64)


def k_weight(x: np.ndarray, sr: int) -> np.ndarray:
    """ITU-R BS.1770-4 K-weighting (shelf + RLB high-pass), coefficients re-derived for sr."""
    from scipy.signal import lfilter
    import math
    # stage 1: high shelf
    f0, G, Q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    K = math.tan(math.pi * f0 / sr)
    Vh, Vb = 10 ** (G / 20), (10 ** (G / 20)) ** 0.4996667741545416
    a0 = 1 + K / Q + K * K
    b = [(Vh + Vb * K / Q + K * K) / a0, 2 * (K * K - Vh) / a0, (Vh - Vb * K / Q + K * K) / a0]
    a = [1, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    y = lfilter(b, a, x)
    # stage 2: high-pass
    f0, Q = 38.13547087602444, 0.5003270373238773
    K = math.tan(math.pi * f0 / sr)
    a0 = 1 + K / Q + K * K
    b = [1, -2, 1]
    a = [1, 2 * (K * K - 1) / a0, (1 - K / Q + K * K) / a0]
    return lfilter(b, a, y)


def integrated_lufs(x: np.ndarray, sr: int = SR) -> float:
    y = k_weight(x, sr)
    blk, hop = int(0.4 * sr), int(0.1 * sr)
    if len(y) < blk:
        y = np.pad(y, (0, blk - len(y)))
    ms = np.array([np.mean(y[i:i + blk] ** 2) for i in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(ms + 1e-20)
    g = ms[lk > -70]
    if len(g) == 0:
        return -99.0
    rel = -0.691 + 10 * np.log10(np.mean(g)) - 10
    g2 = ms[(lk > -70) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(np.mean(g2)))


def frame_rms_db(x: np.ndarray, sr: int = SR, win: float = 0.02) -> np.ndarray:
    n = int(win * sr)
    m = len(x) // n
    f = x[: m * n].reshape(m, n)
    return 20 * np.log10(np.sqrt(np.mean(f ** 2, axis=1)) + 1e-12)


def f0_track(x: np.ndarray, sr: int = SR) -> np.ndarray:
    """Autocorrelation F0 (75-400 Hz) on voiced 40 ms frames."""
    n, hop = int(0.04 * sr), int(0.01 * sr)
    lo, hi = int(sr / 400), int(sr / 75)
    peak = np.max(np.abs(x)) + 1e-9
    out = []
    for i in range(0, len(x) - n, hop):
        f = x[i:i + n] * np.hanning(n)
        if np.sqrt(np.mean(f ** 2)) < 0.05 * peak:
            continue
        ac = np.correlate(f, f, "full")[n - 1:]
        if ac[0] <= 0:
            continue
        seg = ac[lo:hi]
        k = int(np.argmax(seg)) + lo
        if ac[k] / ac[0] > 0.45:
            out.append(sr / k)
    return np.array(out)


def analyse(path: Path, chars: int | None = None) -> dict:
    x = decode(path)
    db = frame_rms_db(x)
    voiced = db > (np.max(db) - 35)
    idx = np.where(voiced)[0]
    lead = idx[0] * 0.02 if len(idx) else 0.0
    tail = (len(db) - 1 - idx[-1]) * 0.02 if len(idx) else 0.0
    f0 = f0_track(x)
    from scipy.signal import welch
    fr, p = welch(x, SR, nperseg=4096)
    centroid = float(np.sum(fr * p) / np.sum(p))
    hf = float(10 * np.log10(np.sum(p[fr > 8000]) / np.sum(p) + 1e-12))
    r = {
        "file": path.name,
        "dur_s": round(len(x) / SR, 3),
        "lufs": round(integrated_lufs(x), 2),
        "peak_dbfs": round(20 * np.log10(np.max(np.abs(x)) + 1e-12), 2),
        "clip_samples": int(np.sum(np.abs(x) >= 0.999)),
        "noise_floor_db": round(float(np.percentile(db, 5)), 1),
        "lead_sil_s": round(lead, 3),
        "tail_sil_s": round(tail, 3),
        "f0_median_hz": round(float(np.median(f0)), 1) if len(f0) else None,
        "f0_iqr_hz": round(float(np.subtract(*np.percentile(f0, [75, 25]))), 1) if len(f0) else None,
        "centroid_hz": round(centroid, 0),
        "hf_above_8k_db": round(hf, 1),
    }
    if chars:
        speech = max(1e-3, (idx[-1] - idx[0] + 1) * 0.02) if len(idx) else 1e-3
        r["chars_per_s"] = round(chars / speech, 2)
    return r


def spectrogram_png(path: Path, out: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    x = decode(path)
    fig, ax = plt.subplots(2, 1, figsize=(9.6, 5), sharex=True, gridspec_kw={"height_ratios": [1, 3]})
    t = np.arange(len(x)) / SR
    ax[0].plot(t, x, lw=0.4, color="#333")
    ax[0].set_ylim(-1, 1)
    ax[0].set_title(path.name, fontsize=9)
    ax[1].specgram(x, NFFT=1024, Fs=SR, noverlap=768, cmap="magma", vmin=-140)
    ax[1].set_ylim(0, 12000)
    ax[1].set_xlabel("s")
    ax[1].set_ylabel("Hz")
    fig.tight_layout()
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=100)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--png")
    ap.add_argument("--chars-json", help="json {file name: char count} for chars/s")
    ap.add_argument("--out-json")
    a = ap.parse_args()
    p = Path(a.path)
    files = sorted([f for f in p.iterdir() if f.suffix.lower() in (".wav", ".mp3")]) if p.is_dir() else [p]
    chars = json.loads(Path(a.chars_json).read_text(encoding="utf-8")) if a.chars_json else {}
    rows = []
    for f in files:
        r = analyse(f, chars.get(f.name))
        rows.append(r)
        print(json.dumps(r, ensure_ascii=False))
        if a.png:
            spectrogram_png(f, Path(a.png) / (f.stem + ".png"))
    if a.out_json:
        Path(a.out_json).write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
