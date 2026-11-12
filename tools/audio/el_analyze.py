"""Analysis of the owner's ElevenLabs Sound Effects v3 files (ADR 0137).

    uv run python el_analyze.py [--src <dir>] [--out <dir>]

Scans <src> (default: main repo art-source/audio/elevenlabs, the owner keeps adding files)
for "<ID> (n).wav", and writes to <out> (default: artifacts/audio-el/analysis):
  analysis.json / analysis.csv   one row per file
  sheets/eng_<rpm>.png           engine loops: 0-500 Hz spectrograms, nominal firing harmonics dotted
  sheets/<ID>.png                other files: full-range spectrogram + waveform

Per file: duration, rate, channels, peak dBFS, integrated LUFS (BS.1770), level drift (RMS of
first vs last second), seam (end->start jump vs in-loop 99.9th percentile of |dx|, and
broadband/HF level step across the seam), stereo correlation.

Engine constant-rpm loops (ENG_<EXT|CAB>_<ON|OFF>_<rpm>): firing frequency of an inline six,
four-stroke = rpm * 6 / 120 = rpm / 20 Hz. Two independent estimators:
  comb  harmonic comb on the Welch spectrum (mean prominence of harmonics k*f, k<=12, f<=1.5 kHz,
        candidates 12..160 Hz; octave check against f/2 and 2f)
  env   autocorrelation of the 80 Hz..3 kHz Hilbert envelope (firing pulses)
Stability: the strongest harmonic of the comb estimate is tracked in 1 s windows (0.25 s hop)
with parabolic interpolation; reported as rpm range / std over the file.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402

MAIN = Path(r"C:\Users\matma\Documents\Claude\kamion")
ENG_RE = re.compile(r"^ENG_(EXT|CAB)_(ON|OFF)_(\d+)$")
# REGEN-01 (ADR 0138): loops described in words, no rpm number. Nominal rpm = the grid cell they were asked for.
ENG_ALIAS = {
    "ENG_EXT_ON_HIGH": ("EXT", "ON", 2100), "ENG_EXT_OFF_HIGH": ("EXT", "OFF", 2100),
    "ENG_CAB_ON_HIGH": ("CAB", "ON", 2100), "ENG_CAB_OFF_HIGH": ("CAB", "OFF", 2100),
    "ENG_EXT_IDLE_SLOW": ("EXT", "OFF", 600), "ENG_CAB_IDLE_SLOW": ("CAB", "OFF", 600),
}


def engine_id(fid: str) -> tuple[str, str, int] | None:
    """(perspective EXT|CAB, load ON|OFF, nominal rpm) of a constant-rpm engine loop ID, else None."""
    m = ENG_RE.match(fid)
    if m:
        return m[1], m[2], int(m[3])
    return ENG_ALIAS.get(fid)


NAME_RE = re.compile(r"^(?P<id>.+?) \((?P<n>\d+)\)\.wav$")


# --------------------------------------------------------------------------- basics
def lufs(x: np.ndarray, fs: int) -> float:
    """ITU-R BS.1770-4 integrated loudness of a mono signal (K-weighting designed for fs)."""
    # K-weighting: high shelf +4 dB @ 1.5 kHz + RLB high-pass 38 Hz (bilinear designs)
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
    b2 = [1, -2, 1]
    y = signal.lfilter(b2, a2, signal.lfilter(b1, a1, x))
    blk, hop = int(0.4 * fs), int(0.1 * fs)
    if len(y) < blk:
        return float(-0.691 + 10 * np.log10(np.mean(y ** 2) + 1e-20))
    ms = np.array([np.mean(y[i:i + blk] ** 2) for i in range(0, len(y) - blk + 1, hop)])
    lk = -0.691 + 10 * np.log10(ms + 1e-20)
    gm = ms[lk > -70]
    if len(gm) == 0:
        return -99.0
    rel = -0.691 + 10 * np.log10(np.mean(gm)) - 10
    gm = ms[(lk > -70) & (lk > rel)]
    return float(-0.691 + 10 * np.log10(np.mean(gm)))


def db(v: float) -> float:
    return float(20 * np.log10(max(v, 1e-12)))


def seam(x: np.ndarray, fs: int) -> dict:
    d1 = np.abs(np.diff(x))
    jump = abs(x[0] - x[-1])
    n = int(0.05 * fs)
    hp = signal.butter(4, 4000, "hp", fs=fs, output="sos")
    head, tail = x[:n], x[-n:]
    joined = np.concatenate([x[-fs // 2:], x[:fs // 2]])
    h = signal.sosfiltfilt(hp, joined)
    e = h ** 2
    w = int(0.005 * fs)
    env = np.convolve(e, np.ones(w) / w, "same")
    mid = len(joined) // 2
    around = env[mid - 2 * w: mid + 2 * w].max()
    base = np.median(env) + 1e-20
    return {
        "seam_jump_ratio": float(jump / (np.percentile(d1, 99.9) + 1e-12)),
        "seam_level_step_db": float(db(np.sqrt(np.mean(head ** 2))) - db(np.sqrt(np.mean(tail ** 2)))),
        "seam_hf_spike_db": float(10 * np.log10(around / base)),
    }


# --------------------------------------------------------------------------- engine pitch
def welch_db(x: np.ndarray, fs: int, nper: int = 1 << 15):
    nper = min(nper, len(x))
    f, p = signal.welch(x, fs, nperseg=nper, noverlap=nper * 3 // 4, window="hann")
    return f, 10 * np.log10(p + 1e-20)


def prominence_db(f: np.ndarray, pdb: np.ndarray) -> np.ndarray:
    """Spectrum minus a running median over ~±25 Hz (local floor)."""
    df = f[1] - f[0]
    w = int(50 / df) | 1
    from scipy.ndimage import median_filter

    return pdb - median_filter(pdb, size=w, mode="nearest")


def comb_score(f: np.ndarray, prom: np.ndarray, f0: float, fmax: float = 1500.0, kmax: int = 12) -> float:
    ks = np.arange(1, kmax + 1)
    fk = ks * f0
    fk = fk[fk < fmax]
    if len(fk) < 3:
        return -1e9
    df = f[1] - f[0]
    vals = []
    for fr in fk:
        i = int(round(fr / df))
        tol = max(1, int(round(0.012 * fr / df)))  # allow 1.2 % mistuning per harmonic
        vals.append(prom[max(0, i - tol): i + tol + 1].max())
    return float(np.mean(np.clip(vals, -6, 30)))


def comb_estimate(x: np.ndarray, fs: int) -> dict:
    f, pdb = welch_db(x, fs)
    prom = prominence_db(f, pdb)
    cands = np.arange(12.0, 160.0, 0.05)
    sc = np.array([comb_score(f, prom, c) for c in cands])
    # local maxima, top 4
    pk, _ = signal.find_peaks(sc, distance=int(2.0 / 0.05))
    pk = pk[np.argsort(sc[pk])[::-1]][:4]
    tops = [(float(cands[i]), float(sc[i])) for i in pk]
    best = tops[0][0]
    # octave correction: prefer f/2 if its comb is nearly as good (half orders present), else 2f if better
    s_half = comb_score(f, prom, best / 2)
    s_dbl = comb_score(f, prom, best * 2)
    return {"comb_f": best, "comb_score": tops[0][1], "comb_top": tops, "comb_half": s_half, "comb_double": s_dbl,
            "_f": f, "_prom": prom}


def env_estimate(x: np.ndarray, fs: int) -> float:
    sos = signal.butter(4, [80, 3000], "bp", fs=fs, output="sos")
    e = np.abs(signal.hilbert(signal.sosfiltfilt(sos, x)))
    dec = 8
    e = signal.decimate(e, dec, ftype="fir")
    fsd = fs / dec
    e = e - e.mean()
    ac = signal.fftconvolve(e, e[::-1], "full")[len(e) - 1:]
    ac /= ac[0] + 1e-20
    lo, hi = int(fsd / 160), int(fsd / 12)
    seg = ac[lo:hi]
    pk, _ = signal.find_peaks(seg)
    if len(pk) == 0:
        return float("nan")
    i = lo + pk[np.argmax(seg[pk])]
    if 0 < i < len(ac) - 1:  # parabolic refine
        a, b, c = ac[i - 1], ac[i], ac[i + 1]
        i = i + 0.5 * (a - c) / (a - 2 * b + c + 1e-20)
    return float(fsd / i)


def track(x: np.ndarray, fs: int, f_fire: float, f: np.ndarray, prom: np.ndarray, force_k: int | None = None) -> dict:
    """Track the most prominent harmonic of f_fire (k = 1..8, below 800 Hz) over time."""
    df = f[1] - f[0]
    best_k, best_p = 1, -1e9
    for k in range(1, 9):
        fr = k * f_fire
        if fr > 800:
            break
        i = int(round(fr / df))
        p = prom[max(0, i - 2): i + 3].max()
        if p > best_p:
            best_k, best_p = k, p
    if force_k:
        best_k = force_k
    fc = best_k * f_fire
    win, hop = fs, fs // 4
    nfft = 1 << 18  # 0.18 Hz bins (zero padded)
    w = signal.windows.hann(win)
    out = []
    for i0 in range(0, len(x) - win + 1, hop):
        X = np.abs(np.fft.rfft(x[i0:i0 + win] * w, nfft))
        ff = np.fft.rfftfreq(nfft, 1 / fs)
        lo, hi = np.searchsorted(ff, fc * 0.92), np.searchsorted(ff, fc * 1.08)
        j = lo + int(np.argmax(X[lo:hi]))
        a, b, c = np.log(X[j - 1] + 1e-20), np.log(X[j] + 1e-20), np.log(X[j + 1] + 1e-20)
        jj = j + 0.5 * (a - c) / (a - 2 * b + c + 1e-20)
        out.append(jj * fs / nfft / best_k)
    arr = np.array(out)
    rpm = arr * 20.0
    return {"track_harmonic": best_k, "track_prom_db": float(best_p), "track_rpm": rpm.tolist(),
            "rpm_med": float(np.median(rpm)), "rpm_min": float(rpm.min()), "rpm_max": float(rpm.max()),
            "rpm_std": float(rpm.std()), "rpm_slope_per_s": float(np.polyfit(np.arange(len(rpm)) * 0.25, rpm, 1)[0]) if len(rpm) > 2 else 0.0}


def yin_f0(x: np.ndarray, fs: int, fmin: float = 25.0, fmax: float = 160.0, thr: float = 0.35) -> tuple[float, float]:
    """Periodicity (YIN, de Cheveigne & Kawahara 2002) of the 25-600 Hz band: median f0 over 0.25 s frames and the median
    aperiodicity (cumulative-mean-normalised difference at the chosen lag; < ~0.35 = clearly periodic). Used as the octave
    check of a grid cell (ADR 0138): the dominant-line convention can sit an octave above the actual period."""
    sos = signal.butter(4, [25, 600], "bp", fs=fs, output="sos")
    dec = 8
    y = signal.decimate(signal.sosfiltfilt(sos, x), dec, ftype="fir")
    fsd = fs / dec
    w, tmax, tmin = int(0.25 * fsd), int(fsd / fmin), int(fsd / fmax)
    res = []
    for i0 in range(0, len(y) - w - tmax, w // 2):
        seg = y[i0:i0 + w + tmax]
        d = np.array([np.sum((seg[:w] - seg[t:t + w]) ** 2) for t in range(tmax + 1)])
        cm = np.concatenate([[1.0], d[1:] * np.arange(1, tmax + 1) / np.maximum(np.cumsum(d[1:]), 1e-20)])
        r = cm[tmin:]
        idx = np.where(r < thr)[0]
        if len(idx):
            j = idx[0]
            while j + 1 < len(r) and r[j + 1] < r[j]:
                j += 1
        else:
            j = int(np.argmin(r))
        res.append((fsd / (j + tmin), r[j]))
    a = np.array(res)
    return float(np.median(a[:, 0])), float(np.median(a[:, 1]))


# --------------------------------------------------------------------------- per file
def analyse(path: Path) -> dict:
    data, fs = sf.read(path, always_2d=True)
    ch = data.shape[1]
    x = data.mean(axis=1)
    m = NAME_RE.match(path.name)
    fid, var = (m["id"], int(m["n"])) if m else (path.stem, 0)
    r = {"file": path.name, "id": fid, "variant": var, "fs": fs, "channels": ch, "dur_s": len(x) / fs,
         "peak_dbfs": db(np.abs(data).max()), "lufs": lufs(x, fs)}
    if ch == 2:
        r["stereo_corr"] = float(np.corrcoef(data[:, 0], data[:, 1])[0, 1])
    sec = min(fs, len(x) // 3)
    r["drift_db"] = db(np.sqrt(np.mean(x[-sec:] ** 2))) - db(np.sqrt(np.mean(x[:sec] ** 2)))
    r.update(seam(x, fs))
    em = engine_id(fid)
    if em:
        rpm_nom = em[2]
        r.update({"persp": em[0], "load": em[1], "rpm_nominal": rpm_nom})
        c = comb_estimate(x, fs)
        r["comb_rpm"] = c["comb_f"] * 20
        r["comb_score"] = c["comb_score"]
        r["comb_top_rpm"] = [round(t[0] * 20) for t in c["comb_top"]]
        r["comb_half_score"], r["comb_double_score"] = c["comb_half"], c["comb_double"]
        r["env_rpm"] = env_estimate(x, fs) * 20
        r["nominal_comb_score"] = comb_score(c["_f"], c["_prom"], rpm_nom / 20)
        f, prom = c["_f"], c["_prom"]
        df = f[1] - f[0]
        lo, hi = int(20 / df), int(120 / df)
        pk, _ = signal.find_peaks(prom[lo:hi], height=8.0)
        if len(pk):
            i = lo + pk[np.argmax(prom[lo:hi][pk])]
            fd = float(f[i]); r["dom_prom_db"] = float(prom[i])
            lad = []
            for k in range(2, 7):
                j = int(round(k * fd / df)); tol = max(1, int(round(0.015 * k * fd / df)))
                lad.append(float(prom[max(0, j - tol): j + tol + 1].max()))
            r["ladder_db"] = [round(v, 1) for v in lad]
            r["ladder_n"] = int(sum(v >= 6.0 for v in lad))
        else:
            fd = c["comb_f"]; r["dom_prom_db"] = 0.0; r["ladder_db"] = []; r["ladder_n"] = 0
        r["dom_hz"] = fd
        r["rpm_actual"] = fd * 20.0
        t = track(x, fs, fd, f, prom, force_k=1)
        r.update(t)
        r["dev_pct"] = 100 * (r["rpm_med"] - rpm_nom) / rpm_nom
    return r


# --------------------------------------------------------------------------- plots
def spec(ax, x, fs, fmax, nper, title, lines=None, vmin=-100):
    f, t, S = signal.spectrogram(x, fs, nperseg=nper, noverlap=nper * 7 // 8, window="hann")
    k = f <= fmax
    ax.pcolormesh(t, f[k], 10 * np.log10(S[k] + 1e-20), shading="auto", cmap="magma",
                  vmin=max(vmin, 10 * np.log10(S[k].max() + 1e-20) - 70))
    if lines:
        for fl in lines:
            if fl < fmax:
                ax.axhline(fl, color="cyan", lw=0.5, ls=":")
    ax.set_title(title, fontsize=7)
    ax.tick_params(labelsize=6)


def engine_sheet(rows: list[dict], src: Path, rpm: int, out: Path) -> None:
    ids = [f"ENG_{p}_{l}_{rpm}" for p in ("EXT", "CAB") for l in ("ON", "OFF")]
    nvar = max([r["variant"] for r in rows if r["id"] in ids] + [1])
    fig, axs = plt.subplots(4, nvar, figsize=(3.2 * nvar, 9), squeeze=False)
    ff = rpm / 20
    for i, fid in enumerate(ids):
        for j in range(nvar):
            ax = axs[i, j]
            rr = [r for r in rows if r["id"] == fid and r["variant"] == j + 1]
            if not rr:
                ax.axis("off")
                continue
            r = rr[0]
            d, fs = sf.read(src / r["file"], always_2d=True)
            spec(ax, d.mean(axis=1), fs, 420, 1 << 14, f"{fid} ({j + 1})  med {r['rpm_med']:.0f}  "
                 f"[{r['rpm_min']:.0f}-{r['rpm_max']:.0f}]", [k * ff for k in range(1, 9)])
    fig.suptitle(f"{rpm} rpm nominal - dotted = k * {ff:.1f} Hz (firing rpm/20)", fontsize=9)
    fig.tight_layout()
    fig.savefig(out, dpi=72)
    plt.close(fig)


def other_sheet(rows: list[dict], src: Path, fid: str, out: Path) -> None:
    rr = sorted([r for r in rows if r["id"] == fid], key=lambda r: r["variant"])
    fig, axs = plt.subplots(2, len(rr), figsize=(3.2 * len(rr), 5), squeeze=False)
    for j, r in enumerate(rr):
        d, fs = sf.read(src / r["file"], always_2d=True)
        x = d.mean(axis=1)
        spec(axs[0, j], x, fs, 12000, 2048, f"{r['file']}  {r['lufs']:.1f} LUFS")
        t = np.arange(len(x)) / fs
        axs[1, j].plot(t, x, lw=0.3)
        axs[1, j].set_ylim(-1, 1)
        axs[1, j].tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out, dpi=72)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(MAIN / "art-source" / "audio" / "elevenlabs"))
    ap.add_argument("--out", default=str(Path(__file__).resolve().parents[2] / "artifacts" / "audio-el" / "analysis"))
    ap.add_argument("--no-sheets", action="store_true")
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    (out / "sheets").mkdir(parents=True, exist_ok=True)
    files = sorted(p for p in src.glob("*.wav"))
    rows = []
    for p in files:
        try:
            rows.append(analyse(p))
        except Exception as e:  # keep going, report
            rows.append({"file": p.name, "error": repr(e)})
        print(p.name, {k: (round(v, 1) if isinstance(v, float) else v) for k, v in rows[-1].items()
                       if k in ("dur_s", "lufs", "peak_dbfs", "rpm_actual", "ladder_n", "rpm_min", "rpm_max", "seam_jump_ratio", "error")})
    (out / "analysis.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    keys = ["file", "id", "variant", "fs", "channels", "dur_s", "peak_dbfs", "lufs", "drift_db", "stereo_corr",
            "seam_jump_ratio", "seam_level_step_db", "seam_hf_spike_db", "rpm_nominal", "comb_rpm", "env_rpm",
            "comb_top_rpm", "rpm_med", "rpm_min", "rpm_max", "rpm_std", "rpm_slope_per_s", "dev_pct", "track_harmonic",
            "track_prom_db", "comb_score", "nominal_comb_score", "dom_hz", "dom_prom_db", "rpm_actual", "ladder_n", "ladder_db"]
    with open(out / "analysis.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, keys, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    if a.no_sheets:
        return
    ok = [r for r in rows if "error" not in r]
    for rpm in sorted({r["rpm_nominal"] for r in ok if "rpm_nominal" in r}):
        engine_sheet(ok, src, rpm, out / "sheets" / f"eng_{rpm:04d}.png")
    for fid in sorted({r["id"] for r in ok if "rpm_nominal" not in r}):
        other_sheet(ok, src, fid, out / "sheets" / f"{fid}.png")


if __name__ == "__main__":
    main()
