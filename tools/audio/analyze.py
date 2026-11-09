"""Objective checks for the rendered bank ("listening by analysis") + report PNGs.

    uv run python analyze.py

Reads art-source/audio/generated/manifest.json and the WAVs as written (16-bit),
writes docs/reports/audio/analysis.json and spectral PNGs. Exit code 1 if a check fails.

Checks per engine/engine-brake loop:
  clip      peak < -0.5 dBFS
  seam      |x[0]-x[-1]| and the 2nd difference across the seam are below the 99.9th
            percentile of the same quantities inside the loop (seam_ratio < 1.0)
  pitch     common spacing of the 3 strongest engine-order peaks == rpm/20 (firing freq.)
  orders    strongest low-frequency peak sits on an engine-order bin; firing orders
            (multiples of 6 cycle orders) dominate the half orders by >= 6 dB, and half
            orders are present (cylinder variation) at > -40 dB
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

from dsp import save_png_small  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "art-source" / "audio" / "generated"
REP = ROOT / "docs" / "reports" / "audio"


def seam_metrics(x: np.ndarray) -> dict:
    d1 = np.abs(np.diff(x))
    d2 = np.abs(np.diff(x, 2))
    seam1 = abs(x[0] - x[-1])
    seam2 = abs(x[1] - 2 * x[0] + x[-1])
    r1 = seam1 / (np.percentile(d1, 99.9) + 1e-12)
    r2 = seam2 / (np.percentile(d2, 99.9) + 1e-12)
    return {"seam_jump": float(seam1), "seam_ratio_d1": float(r1), "seam_ratio_d2": float(r2)}


def order_metrics(x: np.ndarray, fs: int, n_cycles: int, rpm: float) -> dict:
    X = np.abs(np.fft.rfft(x)) / len(x)
    P = X ** 2
    df = fs / len(x)
    f_fire = rpm / 20.0
    fire_bin = 6 * n_cycles  # loop holds exactly n_cycles engine cycles
    # strongest bin 15..300 Hz
    lo, hi = int(15 / df), int(300 / df)
    kmax = lo + int(np.argmax(P[lo:hi]))
    order = kmax / n_cycles  # in cycle orders (half-orders of crank)
    on_order = abs(order - round(order)) * n_cycles <= 1.0
    # firing vs non-firing cycle orders, up to 12 firing harmonics (cap 1.5 kHz)
    h_max = int(min(12, 1500 / f_fire))
    fire_p, half_p = [], []
    for k in range(1, 6 * h_max + 1):
        b = k * n_cycles
        pw = P[b - 1:b + 2].sum()
        (fire_p if k % 6 == 0 else half_p).append(pw)
    dom = 10 * np.log10(np.mean(fire_p) / (np.mean(half_p) + 1e-30))
    # f0 estimate = common spacing (gcd, in cycle orders) of the 3 strongest engine-order
    # peaks below 1.5 kHz. 6 cycle orders = firing frequency. A half order among the top 3
    # would drop the gcd to 3/2/1 and fail the check. (Top-5 is reported for information:
    # half orders such as 1.5x firing legitimately enter it once the muffler/cab low-pass
    # attenuates the higher firing harmonics.)
    ks = np.arange(1, 6 * h_max + 1)
    pw = np.array([P[k * n_cycles - 1:k * n_cycles + 2].sum() for k in ks])
    top = ks[np.argsort(pw)[::-1][:5]]
    g = int(np.gcd.reduce(top[:3]))
    f0 = g * rpm / 120.0
    return {
        "f_fire_expected": f_fire, "f0_estimate": f0, "top5_cycle_orders": [int(k) for k in top], "f0_err_pct": 100 * (f0 - f_fire) / f_fire,
        "low_peak_hz": kmax * df, "low_peak_order_cycle": order, "low_peak_firing_harmonic": order / 6.0,
        "low_peak_on_engine_order": bool(on_order),
        "firing_over_half_orders_db": float(dom),
    }


def band_balance(x: np.ndarray, fs: int) -> dict:
    P = np.abs(np.fft.rfft(x)) ** 2
    f = np.fft.rfftfreq(len(x), 1 / fs)
    out = {}
    for lo, hi in [(20, 200), (200, 1000), (1000, 4000), (4000, 16000)]:
        out[f"{lo}-{hi}"] = 10 * np.log10(P[(f >= lo) & (f < hi)].sum() + 1e-20)
    ref = max(out.values())
    return {k: round(v - ref, 1) for k, v in out.items()}


def plot_loop_spectra(clips, path: Path) -> None:
    sel = [("ext", "on", 600), ("ext", "on", 1300), ("ext", "on", 2100),
           ("cab", "mid", 600), ("cab", "mid", 1300), ("ext", "off", 1300)]
    fig, axes = plt.subplots(3, 2, figsize=(12, 9), sharey=True)
    for ax, (p, layer, rpm) in zip(axes.T.ravel(), sel):
        c = next(c for c in clips if c["kind"] == "engine" and c["perspective"] == p
                 and c["layer"] == layer and c["rpm"] == rpm)
        x, fs = sf.read(ROOT / c["file"])
        X = np.abs(np.fft.rfft(x)) / len(x)
        f = np.fft.rfftfreq(len(x), 1 / fs)
        # smooth to ~1/3 of a cycle-order bin for readability (still exact on bins)
        ax.semilogx(f[1:], 20 * np.log10(X[1:] + 1e-9), lw=0.5, color="0.2")
        ff = c["rpm_exact"] / 20.0
        for h in range(1, int(2000 / ff) + 1):
            ax.axvline(h * ff, color="tab:red", lw=0.6, alpha=0.5, ls="--")
        ax.set_xlim(15, 8000)
        ax.set_ylim(-130, -20)
        ax.set_title(f"{p} {layer} {rpm} rpm  (red = firing harmonics, f_fire={ff:.1f} Hz)", fontsize=9)
        ax.grid(alpha=0.3, which="both")
    for ax in axes[-1]:
        ax.set_xlabel("Hz")
    for ax in axes[:, 0]:
        ax.set_ylabel("dB (rel FS)")
    fig.suptitle("Engine loop spectra (whole loop FFT; loop = integer number of 720° cycles)")
    fig.tight_layout()
    save_png_small(fig, path, dpi=80)
    plt.close(fig)


def plot_waveforms(clips, path: Path) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(12, 8))
    for ax, (p, layer, rpm, kind) in zip(axes, [("ext", "on", 1300, "engine"), ("ext", "mid", 600, "engine"),
                                              ("ext", None, 1800, "ebrake")]):
        c = next(c for c in clips if c["kind"] == kind and c["perspective"] == p
                 and c["layer"] == layer and c["rpm"] == rpm)
        x, fs = sf.read(ROOT / c["file"])
        spc = c["samples"] / c["cycles"]
        n = int(2 * spc)
        t = np.arange(n) / fs * 1000
        ax.plot(t, x[:n], lw=0.6, color="0.15")
        for k in range(13):
            ax.axvline((60.0 / 720.0 + k / 6) * spc / fs * 1000, color="tab:red", lw=0.5, alpha=0.4)
        ax.set_title(f"{c['name']}: 2 engine cycles (720°×2); red = firing TDCs (every 120°)", fontsize=9)
        ax.set_xlabel("ms")
    fig.tight_layout()
    save_png_small(fig, path, dpi=80)
    plt.close(fig)


def plot_sfx(manifest, path: Path) -> None:
    items = ["turbo_whistle_loop", "air_brake_release", "parking_brake_set", "turbo_liftoff"]
    fig, axes = plt.subplots(2, 3, figsize=(13, 7))
    files = {s["name"]: s["file"] for s in manifest["sfx"]}
    eb = next(c for c in manifest["clips"] if c["name"] == "ebrake_ext_1800")
    ws = [(n, files[n]) for n in items] + [("ebrake_ext_1800", eb["file"]),
                                          ("engine_cab_mid_1300", next(c["file"] for c in manifest["clips"] if c["name"] == "engine_cab_mid_1300"))]
    for ax, (name, fpath) in zip(axes.ravel(), ws):
        x, fs = sf.read(ROOT / fpath)
        x = x[: int(2.0 * fs)]
        f, t, S = signal.spectrogram(x, fs, nperseg=1024, noverlap=768)
        ax.pcolormesh(t, f, 10 * np.log10(S + 1e-14), shading="auto", vmin=-130, vmax=-40, cmap="magma")
        ax.set_ylim(0, 12000 if "engine" not in name and "ebrake" not in name else 4000)
        ax.set_title(name, fontsize=9)
        ax.set_xlabel("s")
        ax.set_ylabel("Hz")
    fig.tight_layout()
    save_png_small(fig, path, dpi=75, colors=64)
    plt.close(fig)


def main() -> int:
    manifest = json.loads((GEN / "manifest.json").read_text(encoding="utf-8"))
    REP.mkdir(parents=True, exist_ok=True)
    results, failures = [], []
    for c in manifest["clips"]:
        x, fs = sf.read(ROOT / c["file"])
        r = {"name": c["name"], "peak_dbfs": round(20 * np.log10(np.max(np.abs(x))), 2),
             "rms_dbfs": round(20 * np.log10(np.sqrt(np.mean(x ** 2))), 2)}
        r.update(seam_metrics(x))
        r.update(order_metrics(x, fs, c["cycles"], c["rpm_exact"]))
        r["bands_db"] = band_balance(x, fs)
        checks = {
            "clip": r["peak_dbfs"] < -0.5,
            "seam": r["seam_ratio_d1"] < 1.0 and r["seam_ratio_d2"] < 1.0,
            "pitch": abs(r["f0_err_pct"]) < 1.0,
            "low_peak_on_order": r["low_peak_on_engine_order"],
            "firing_dominates": r["firing_over_half_orders_db"] >= 6.0,
            "half_orders_present": r["firing_over_half_orders_db"] < 40.0,
        }
        r["checks"] = checks
        if not all(checks.values()):
            failures.append((c["name"], [k for k, v in checks.items() if not v]))
        results.append(r)
    sfx_res = []
    for s in manifest["sfx"]:
        x, fs = sf.read(ROOT / s["file"])
        r = {"name": s["name"], "peak_dbfs": round(20 * np.log10(np.max(np.abs(x))), 2),
             "rms_dbfs": round(20 * np.log10(np.sqrt(np.mean(x ** 2))), 2)}
        if s["loop"]:
            r.update(seam_metrics(x))
            ok = r["seam_ratio_d1"] < 1.0 and r["seam_ratio_d2"] < 1.0
        else:
            r["edge_abs_first_last"] = [float(abs(x[0])), float(abs(x[-1]))]
            ok = abs(x[0]) < 1e-3 and abs(x[-1]) < 1e-3
        ok = ok and r["peak_dbfs"] < -0.5
        r["ok"] = bool(ok)
        if not ok:
            failures.append((s["name"], ["seam/edge/clip"]))
        sfx_res.append(r)

    summary = {
        "n_loops": len(results),
        "max_seam_ratio_d1": max(r["seam_ratio_d1"] for r in results),
        "max_seam_ratio_d2": max(r["seam_ratio_d2"] for r in results),
        "max_abs_f0_err_pct": max(abs(r["f0_err_pct"]) for r in results),
        "min_firing_over_half_orders_db": min(r["firing_over_half_orders_db"] for r in results),
        "max_firing_over_half_orders_db": max(r["firing_over_half_orders_db"] for r in results),
        "max_peak_dbfs": max(r["peak_dbfs"] for r in results),
        "failures": failures,
    }
    (REP / "analysis.json").write_text(json.dumps({"summary": summary, "loops": results, "sfx": sfx_res},
                                                  indent=1, default=float), encoding="utf-8")
    plot_loop_spectra(manifest["clips"], REP / "engine_loop_spectra.png")
    plot_waveforms(manifest["clips"], REP / "engine_waveforms.png")
    plot_sfx(manifest, REP / "sfx_spectrograms.png")

    print(json.dumps(summary, indent=1, default=float))
    print(f"{'clip':26s} {'rms':>6s} {'f_fire':>7s} {'f0est':>7s} {'pk_Hz':>7s} {'pk_h':>5s} {'fire/half':>9s} {'seam':>5s}  bands")
    for r in results:
        print(f"{r['name']:26s} {r['rms_dbfs']:6.1f} {r['f_fire_expected']:7.2f} {r['f0_estimate']:7.2f} "
              f"{r['low_peak_hz']:7.1f} {r['low_peak_firing_harmonic']:5.2f} {r['firing_over_half_orders_db']:9.1f} "
              f"{r['seam_ratio_d1']:5.2f}  {r['bands_db']}")
    for r in sfx_res:
        print(r)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
