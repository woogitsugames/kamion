"""ADR 0285: loudness / peak / spectrogram report of a Windows player output capture.

The player records the AudioListener mix with ``-audio_capture out.wav`` (game/Assets/_Project/Audio/PcAudioRuntime.cs,
32-bit float, interleaved, the output rate). This script measures it per segment:

    uv run python pc_capture.py <capture.wav> <out_dir> [--seg cab:0:28 --seg chase:32:60] [--label run]

Per segment: ITU-R BS.1770-4 integrated loudness (multichannel sum, K-weighting designed for the file rate, absolute
-70 LUFS and relative -10 LU gates), max short-term (3 s) and momentary (0.4 s) loudness, loudness range (EBU Tech 3342:
10th-95th percentile of gated short-term values), sample peak, true peak (4x polyphase oversampling, BS.1770-4 Annex 2),
count of samples at or above full scale (|x| >= 1.0, i.e. clipped in a fixed-point output) and of samples above
-0.1 dBFS, DC offset, inter-channel correlation. Writes report.json, a spectrogram PNG and a loudness-over-time PNG
(both <= 960 px wide). The capture tap sits on the listener object: the level does not include AudioListener.volume
(the master slider), which the report records from the player log when given.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

import dsp  # noqa: E402


def k_weight(x: np.ndarray, fs: int) -> np.ndarray:
    """BS.1770-4 K-weighting (pre-filter shelf + RLB high-pass), coefficients designed for ``fs``; x is (n, ch)."""
    f0, g, q = 1681.974450955533, 3.999843853973347, 0.7071752369554196
    k = np.tan(np.pi * f0 / fs)
    vh = 10 ** (g / 20)
    vb = vh ** 0.4996667741545416
    a0 = 1 + k / q + k * k
    b1 = [(vh + vb * k / q + k * k) / a0, 2 * (k * k - vh) / a0, (vh - vb * k / q + k * k) / a0]
    a1 = [1, 2 * (k * k - 1) / a0, (1 - k / q + k * k) / a0]
    f0, q = 38.13547087602444, 0.5003270373238773
    k = np.tan(np.pi * f0 / fs)
    a2 = [1, 2 * (k * k - 1) / (1 + k / q + k * k), (1 - k / q + k * k) / (1 + k / q + k * k)]
    return signal.lfilter([1, -2, 1], a2, signal.lfilter(b1, a1, x, axis=0), axis=0)


def _blocks(y: np.ndarray, fs: int, win: float, hop: float) -> np.ndarray:
    """Mean-square per block summed over channels (weights 1.0: L/R/C; surround channels would be 1.41 - not used)."""
    b, h = int(win * fs), int(hop * fs)
    if len(y) < b:
        return np.array([np.sum(np.mean(y ** 2, axis=0))])
    e = np.cumsum(np.concatenate([np.zeros((1, y.shape[1])), y ** 2]), axis=0)
    starts = np.arange(0, len(y) - b + 1, h)
    return np.sum((e[starts + b] - e[starts]) / b, axis=1)


def _lk(ms: np.ndarray) -> np.ndarray:
    return -0.691 + 10 * np.log10(ms + 1e-20)


def integrated(y: np.ndarray, fs: int) -> float:
    ms = _blocks(y, fs, 0.4, 0.1)
    g = ms[_lk(ms) > -70]
    if len(g) == 0:
        return -99.0
    rel = _lk(np.mean(g)) - 10
    g = ms[(_lk(ms) > -70) & (_lk(ms) > rel)]
    return float(_lk(np.mean(g)))


def lra(y: np.ndarray, fs: int) -> float:
    st = _lk(_blocks(y, fs, 3.0, 1.0))
    st = st[st > -70]
    if len(st) < 2:
        return 0.0
    st = st[st > 10 * np.log10(np.mean(10 ** (st / 10))) - 20]
    return float(np.percentile(st, 95) - np.percentile(st, 10))


def true_peak(x: np.ndarray) -> float:
    up = signal.resample_poly(x, 4, 1, axis=0)
    return float(np.max(np.abs(up)))


def clicks(x: np.ndarray, fs: int, rise_db: float = 20.0, floor_db: float = -70.0) -> list[float]:
    """Discontinuity scan: a click is broadband, so the mono sum is high-passed at 12 kHz (4th-order Butterworth, where the
    truck mix has little energy) and cut into 128-sample frames; a frame whose RMS is ``rise_db`` above the median of the
    surrounding 1 s and above ``floor_db`` dBFS is a hit; hits closer than 20 ms are one event. Returns event times [s].
    A real broadband transient (air valve, door) can trigger it too - every hit is listed for listening, not counted
    as a defect."""
    m = x.mean(axis=1)
    h = signal.sosfilt(signal.butter(4, 12000 / (fs / 2), "highpass", output="sos"), m)
    fr = 128
    n = len(h) // fr
    if n < 10:
        return []
    e = np.sqrt(np.mean(h[: n * fr].reshape(n, fr) ** 2, axis=1) + 1e-20)
    w = max(3, int(fs / fr))
    pad = np.pad(e, w // 2, mode="edge")
    from numpy.lib.stride_tricks import sliding_window_view
    med = np.median(sliding_window_view(pad, w)[: n], axis=1)
    hit = np.flatnonzero((20 * np.log10(e / (med + 1e-20)) > rise_db) & (20 * np.log10(e) > floor_db))
    ev: list[float] = []
    for i in hit:
        t = i * fr / fs
        if not ev or t - ev[-1] > 0.02:
            ev.append(round(t, 3))
    return ev


def measure(x: np.ndarray, fs: int) -> dict:
    y = k_weight(x, fs)
    st = _lk(_blocks(y, fs, 3.0, 1.0))
    mo = _lk(_blocks(y, fs, 0.4, 0.1))
    peak = float(np.max(np.abs(x)))
    tp = true_peak(x)
    corr = float(np.corrcoef(x[:, 0], x[:, 1])[0, 1]) if x.shape[1] > 1 and np.std(x[:, 0]) > 0 and np.std(x[:, 1]) > 0 else 1.0
    return {
        "seconds": round(len(x) / fs, 2),
        "lufs_integrated": round(integrated(y, fs), 2),
        "lufs_shortterm_max": round(float(np.max(st)), 2),
        "lufs_momentary_max": round(float(np.max(mo)), 2),
        "lra_lu": round(lra(y, fs), 2),
        "sample_peak_dbfs": round(dsp.db(peak), 2),
        "true_peak_dbtp": round(dsp.db(tp), 2),
        "samples_at_or_over_0dbfs": int(np.sum(np.abs(x) >= 1.0)),
        "samples_over_m0_1dbfs": int(np.sum(np.abs(x) > 10 ** (-0.1 / 20))),
        "dc": [round(float(v), 6) for v in np.mean(x, axis=0)],
        "lr_correlation": round(corr, 3),
        "click_events_s": clicks(x, fs)[:50],
    }


def plot(x: np.ndarray, fs: int, segs: list[tuple[str, float, float]], out: Path, title: str) -> None:
    mono = x.mean(axis=1)
    fig, axes = plt.subplots(2, 1, figsize=(12, 7), sharex=True)
    f, t, s = signal.spectrogram(mono, fs, nperseg=4096, noverlap=3072, scaling="spectrum")
    axes[0].pcolormesh(t, f, 10 * np.log10(s + 1e-14), shading="auto", cmap="magma", vmin=-110, vmax=-20)
    axes[0].set_yscale("symlog", linthresh=200)
    axes[0].set_ylim(20, fs / 2)
    axes[0].set_ylabel("Hz")
    axes[0].set_title(f"{title}: spektrogram miksu (mono suma)")
    y = k_weight(x, fs)
    mo = _lk(_blocks(y, fs, 0.4, 0.1))
    st = _lk(_blocks(y, fs, 3.0, 0.1))
    axes[1].plot(np.arange(len(mo)) * 0.1 + 0.2, mo, lw=0.6, label="momentary 0,4 s")
    axes[1].plot(np.arange(len(st)) * 0.1 + 1.5, st, lw=1.2, label="short-term 3 s")
    for name, a, b in segs:
        axes[1].axvspan(a, b, alpha=0.08)
        axes[1].text(a + 0.3, -12, name)
    for ref in (-16, -18, -23):
        axes[1].axhline(ref, ls=":", lw=0.7, c="k")
    axes[1].set_ylim(-50, -5)
    axes[1].set_ylabel("LUFS")
    axes[1].set_xlabel("s")
    axes[1].legend(loc="lower right")
    fig.tight_layout()
    dsp.save_png_small(fig, out, dpi=80)
    plt.close(fig)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("wav", type=Path)
    ap.add_argument("out", type=Path)
    ap.add_argument("--seg", action="append", default=[], help="name:t0:t1 (seconds into the capture)")
    ap.add_argument("--label", default="capture")
    a = ap.parse_args()
    x, fs = sf.read(a.wav, always_2d=True, dtype="float64")
    a.out.mkdir(parents=True, exist_ok=True)
    segs = [(s.split(":")[0], float(s.split(":")[1]), float(s.split(":")[2])) for s in a.seg] or [("all", 0.0, len(x) / fs)]
    rep = {"file": str(a.wav), "rate": fs, "channels": x.shape[1], "label": a.label, "whole": measure(x, fs), "segments": {}}
    for name, t0, t1 in segs:
        rep["segments"][name] = measure(x[int(t0 * fs):int(t1 * fs)], fs)
    (a.out / f"{a.label}_report.json").write_text(json.dumps(rep, indent=2), encoding="utf-8")
    plot(x, fs, segs, a.out / f"{a.label}_spectrogram.png", a.label)
    print(json.dumps(rep, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
