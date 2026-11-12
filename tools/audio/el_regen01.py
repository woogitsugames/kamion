"""Objective analysis + ranking of the ElevenLabs REGEN-01 batch (ADR 0138).

    uv run python el_regen01.py [--src <dir>] [--out <dir>]

Input : <src>/<ID> (n).wav (owner's raw files, 48 kHz stereo; default main repo art-source/audio/elevenlabs).
Output: <out> (default artifacts/audio-regen01/analysis):
  regen01.json / regen01.csv   one row per file, every metric below + score + rank within its ID
  picks.json                   best variant per ID with the reason (numbers), PASS/FAIL against the requirement
  sweeps.json                  firing-line track of the two 30 s SWEEP IDs (rpm vs time per variant)
  sheets/<ID>.png              spectrogram (+ track where relevant) + waveform of every variant

Common metrics: duration, peak dBFS, samples >= 0.999 (clips), integrated LUFS (BS.1770), level steadiness
(std / range of 250 ms RMS in dB), -60 dB bandwidth, stereo correlation, seam (el_analyze.seam).

Per kind
  engine loop (HIGH, IDLE_SLOW): el_analyze.analyse (dominant 20-120 Hz line = firing rpm/20 of an inline six, ladder,
      1 s track); the score is the one el_prepare uses for the grid (ladder, prominence, span) plus a penalty for level
      instability (EXT_ON_HIGH variants that rev instead of holding).
  sweep: Viterbi track of the harmonic-sum salience (fundamental 15-140 Hz, 0.6 s windows, 0.1 s hop, max 12 % step);
      rising segment (start/end rpm, duration), smoothness (residual of the track against a 1 s median), salience.
      Usable for cutting grid loops when the rise is monotonic and the residual < 2 %.
  turbo whistle: most prominent narrow line 1.5-12 kHz (dB above the local floor), its stability in 0.5 s windows.
  stop: level drop (last 0.4 s vs first 1 s), fall of the dominant engine line, presence of a run-down.
  upshift: dominant engine line 60-260 Hz in 0.25 s windows: drop >= 6 % within 0.6 s, level after the drop.
  hiss: onset, -20 dB duration, share of energy > 2 kHz, number of bursts.
  wipers: sweep onsets from the 1-6 kHz envelope; period mean/CV, wrap interval vs period.
  door: first transient time (latch), level 0.4-1.5 s after it vs the pre-latch floor (outside air layer).
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import soundfile as sf  # noqa: E402
from scipy import signal  # noqa: E402
from scipy.ndimage import median_filter  # noqa: E402

from el_analyze import MAIN, NAME_RE, analyse, db, lufs, prominence_db, seam, welch_db  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]

# REGEN-01 prompts (docs/owner/ELEVENLABS-REGEN-01.md); the owner's generation-manifest.json covers only batch 1.
REGEN01 = {
    "ENG_EXT_ON_HIGH": ("Heavy truck inline-six turbo diesel at high revs near its governed maximum, recorded outside by the exhaust stack, pulling hard uphill in a low gear, fast busy firing rhythm blending into a gritty high drone, loud turbo whistle, held perfectly steady, no gear change, no pitch change, seamless loop, no music, no voices", 6, 80, True),
    "ENG_EXT_OFF_HIGH": ("Heavy truck inline-six diesel spinning at high revs with the throttle closed, recorded outside, fast light firing rhythm, hollow high-pitched drone, no turbo whistle, held perfectly steady, no pitch change, seamless loop, no music, no voices", 6, 80, True),
    "ENG_CAB_ON_HIGH": ("Inside a heavy truck cab while the inline-six diesel works hard at high revs in a low gear, fast busy engine drone through the floor and firewall, buzzing cab panels, turbo whine, held perfectly steady, no road noise, no pitch change, seamless loop, no music, no voices", 6, 80, True),
    "ENG_CAB_OFF_HIGH": ("Inside a heavy truck cab, diesel engine spinning fast with the throttle closed, light high-pitched drone through the floor, faint mechanical whir, held perfectly steady, no road noise, no pitch change, seamless loop, no music, no voices", 6, 80, True),
    "ENG_EXT_IDLE_SLOW": ("Big heavy truck diesel engine at a very slow low idle, recorded outside, deep lazy lumpy rhythm with each combustion thump clearly separate, soft exhaust puffs, faint injector tick, steady, no revving, no pitch change, seamless loop, no music, no voices", 8, 80, True),
    "ENG_CAB_IDLE_SLOW": ("Inside a parked heavy truck cab with the diesel engine at a very slow low idle, deep slow throb felt through the seat, each combustion thump separate and muffled, very faint ticking, steady, no road noise, no revving, no pitch change, seamless loop, no music, no voices", 8, 80, True),
    "TURBO_WHISTLE_LOOP": ("Steady high-pitched whistle of a heavy truck turbocharger at constant boost, close to the engine, clean continuous tone with soft air rush, no engine rumble, no pitch change, seamless loop, no music, no voices", 5, 80, True),
    "ENG_EXT_ON_SWEEP": ("Heavy truck inline-six turbo diesel recorded outside by the exhaust stack, accelerating slowly and continuously from low idle all the way to maximum revs in one gear under heavy load, smooth steady rise in engine speed with no gear change, no pauses, no music, no voices", 30, 80, False),
    "ENG_CAB_ON_SWEEP": ("Inside a heavy truck cab, the inline-six diesel accelerates slowly and continuously from low idle to maximum revs in one gear under heavy load, smooth steady rise of the engine drone through the floor, no gear change, no pauses, no road noise, no music, no voices", 30, 80, False),
    "ENG_STOP_CAB": ("Inside a heavy truck cab, the idling diesel engine is switched off, the cab shudders once and the engine runs down to silence, a soft dashboard click at the end, no music, no voices", 3, 60, False),
    "GEAR_UPSHIFT_CAB": ("Inside a heavy truck cab while accelerating: the diesel engine drones steadily, then drops in pitch as the automated gearbox shifts up with a short pneumatic click and a soft clunk, and immediately keeps pulling at a lower engine speed until the end, engine audible the whole time, no music, no voices", 2.5, 70, False),
    "BRAKE_SERVICE_HISS": ("Single short sharp hiss of compressed air released from a heavy truck brake valve right after the brake pedal is let go, starts immediately, clean, nothing else, no music, no voices", 1, 70, False),
    "CAB_WIPERS_LOOP": ("Truck windscreen wipers sweeping at a perfectly even slow rhythm, exactly one sweep every second, rubber squeak on wet glass and soft motor hum, steady, seamless loop, no music, no voices", 6, 70, True),
    "CAB_DOOR_OPEN": ("Heavy truck cab door opened from inside: the metal latch clunks immediately at the start, the door swings open and outside air and distant traffic become audible, no music, no voices", 2, 70, False),
}
VARIANTS = {k: ((5, 6, 7, 8) if k in ("GEAR_UPSHIFT_CAB", "BRAKE_SERVICE_HISS", "CAB_WIPERS_LOOP", "CAB_DOOR_OPEN") else (1, 2, 3, 4))
            for k in REGEN01}
ENGINE_LOOPS = [k for k in REGEN01 if k.endswith("_HIGH") or k.endswith("_IDLE_SLOW")]
SWEEPS = ["ENG_EXT_ON_SWEEP", "ENG_CAB_ON_SWEEP"]


def prompt_entry(fid: str) -> dict:
    p, d, i, loop = REGEN01[fid]
    return {"id": fid, "prompt": p, "duration": d, "influence": i, "loop": loop, "batch": "REGEN-01"}


# --------------------------------------------------------------------------------------------------- common
def rms_db(x: np.ndarray) -> float:
    return db(float(np.sqrt(np.mean(x ** 2))))


def env_db(x: np.ndarray, fs: int, win_s: float = 0.25, hop_s: float | None = None) -> np.ndarray:
    w = int(win_s * fs)
    h = int((hop_s or win_s) * fs)
    return np.array([rms_db(x[i:i + w]) for i in range(0, len(x) - w + 1, h)])


def bandwidth_60(x: np.ndarray, fs: int) -> float:
    f, p = signal.welch(x, fs, nperseg=4096)
    pdb = 10 * np.log10(p + 1e-20)
    sm = median_filter(pdb, 9)
    above = np.where(sm > sm.max() - 60)[0]
    return float(f[above[-1]])


def common(path: Path) -> tuple[dict, np.ndarray, int]:
    d, fs = sf.read(path, always_2d=True)
    x = d.mean(axis=1)
    m = NAME_RE.match(path.name)
    e = env_db(x, fs)
    e = e[e > e.max() - 60] if len(e) else e
    r = {"file": path.name, "id": m["id"], "variant": int(m["n"]), "fs": fs, "dur_s": len(x) / fs,
         "peak_dbfs": db(float(np.abs(d).max())), "clips": int(np.sum(np.abs(d) >= 0.999)), "lufs": lufs(x, fs),
         "level_std_db": float(np.std(e)) if len(e) else 0.0, "level_range_db": float(np.ptp(e)) if len(e) else 0.0,
         "bw60_hz": bandwidth_60(x, fs)}
    if d.shape[1] == 2:
        r["stereo_corr"] = float(np.corrcoef(d[:, 0], d[:, 1])[0, 1])
    return r, x, fs


# --------------------------------------------------------------------------------------------------- sweep track
def salience_track(x: np.ndarray, fs: int, fmin: float = 15.0, fmax: float = 140.0, win_s: float = 0.6,
                   hop_s: float = 0.1, kmax: int = 6, max_step: float = 0.12) -> dict:
    """Viterbi-smoothed fundamental of the strongest harmonic ladder. Returns times, f0, salience per frame."""
    dec = 12
    y = signal.decimate(signal.decimate(x, 4, ftype="fir"), 3, ftype="fir")
    fsd = fs / dec
    w, h = int(win_s * fsd), int(hop_s * fsd)
    nfft = 1 << 15
    ff = np.fft.rfftfreq(nfft, 1 / fsd)
    df = ff[1]
    win = signal.windows.hann(w)
    cands = np.exp(np.linspace(np.log(fmin), np.log(fmax), 420))
    medw = int(30 / df) | 1
    frames, times = [], []
    for i0 in range(0, len(y) - w + 1, h):
        X = 20 * np.log10(np.abs(np.fft.rfft(y[i0:i0 + w] * win, nfft)) + 1e-12)
        prom = X - median_filter(X, medw, mode="nearest")
        sal = np.zeros(len(cands))
        for k in range(1, kmax + 1):
            idx = np.clip(np.round(k * cands / df).astype(int), 0, len(ff) - 1)
            # max over +-1.5 % around k*f
            tol = np.maximum(1, np.round(0.015 * k * cands / df).astype(int))
            v = np.array([prom[max(0, j - t): j + t + 1].max() for j, t in zip(idx, tol)])
            sal += np.clip(v, -3, 25) / math.sqrt(k)
        frames.append(sal / sum(1 / math.sqrt(k) for k in range(1, kmax + 1)))
        times.append((i0 + w / 2) / fsd)
    S = np.array(frames)
    # Viterbi: transitions limited to +-max_step in log frequency, cost proportional to |log ratio|
    lc = np.log(cands)
    n, m = S.shape
    cost = np.full((n, m), -1e9)
    back = np.zeros((n, m), dtype=int)
    cost[0] = S[0]
    step = np.log(1 + max_step)
    span = int(np.ceil(step / (lc[1] - lc[0])))
    for t in range(1, n):
        for j in range(m):
            lo, hi = max(0, j - span), min(m, j + span + 1)
            prev = cost[t - 1, lo:hi] - 30 * np.abs(lc[lo:hi] - lc[j])
            b = int(np.argmax(prev))
            back[t, j] = lo + b
            cost[t, j] = prev[b] + S[t, j]
    path = np.zeros(n, dtype=int)
    path[-1] = int(np.argmax(cost[-1]))
    for t in range(n - 1, 0, -1):
        path[t - 1] = back[t, path[t]]
    f0 = cands[path]
    sal = S[np.arange(n), path]
    return {"t": np.array(times), "f0": f0, "sal": sal}


def line_follow(x: np.ndarray, fs: int, t0: float, t1: float, band: tuple[float, float], win_s: float = 0.4,
                hop_s: float = 0.05, tol: float = 0.06) -> dict:
    """Follow one spectral line from t0 to t1: start at the strongest peak in `band` at t0, then each frame take the
    strongest peak within +-tol of the previous frequency (parabolic interpolation). Returns t, f0, sal (prominence dB)."""
    w, h = int(win_s * fs), int(hop_s * fs)
    nfft = 1 << 18
    ff = np.fft.rfftfreq(nfft, 1 / fs)
    df = ff[1]
    win = signal.windows.hann(w)
    ts, fo, pr = [], [], []
    f_prev = None
    medw = int(30 / df) | 1
    lo_all = int(10 / df)
    hi_all = int(max(band[1] * 3, 400) / df)
    for i0 in range(max(0, int(t0 * fs) - w // 2), min(len(x) - w, int(t1 * fs) - w // 2) + 1, h):
        X = 20 * np.log10(np.abs(np.fft.rfft(x[i0:i0 + w] * win, nfft))[:hi_all] + 1e-12)
        prom = X - median_filter(X, medw, mode="nearest")
        lo, hi = band if f_prev is None else (f_prev * (1 - tol), f_prev * (1 + tol))
        a, b = max(lo_all, int(lo / df)), int(hi / df)
        j = a + int(np.argmax(X[a:b]))
        y0, y1, y2 = X[j - 1], X[j], X[j + 1]
        jj = j + 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
        f_prev = jj * df
        ts.append((i0 + w / 2) / fs)
        fo.append(f_prev)
        pr.append(prom[j])
    return {"t": np.array(ts), "f0": np.array(fo), "sal": np.array(pr)}


# Rising windows of the two SWEEP IDs (authored after reviewing artifacts/audio-regen01/analysis/sheets/*SWEEP*.png):
# file -> (t0, t1, start band Hz, harmonic number of the followed line). The followed line is the brightest moving line.
SWEEP_WINDOWS = {
    "ENG_EXT_ON_SWEEP (1).wav": (5.6, 18.4, (60, 80), 2),   # brightest line is 2x the ladder spacing (160/240 Hz pair at 16 s)
    "ENG_EXT_ON_SWEEP (2).wav": (10.6, 20.2, (50, 62), 1),  # rise 10.6-15 s, plateau ~95 Hz 15-18 s, ~107 Hz 19-20 s
    "ENG_EXT_ON_SWEEP (3).wav": (10.0, 21.0, (38, 48), 1),  # rise 10-15 s, plateau ~90 Hz 15-21 s
    "ENG_EXT_ON_SWEEP (4).wav": (9.0, 15.4, (40, 50), 1),   # rise 9-15 s, then fast fall
    "ENG_CAB_ON_SWEEP (1).wav": (3.5, 22.0, (65, 80), 1),   # stepped, mostly flat ~75 Hz
    "ENG_CAB_ON_SWEEP (2).wav": (7.0, 24.0, (68, 80), 1),   # stair steps
    "ENG_CAB_ON_SWEEP (3).wav": (8.0, 17.5, (65, 75), 1),   # two humps (8-12.5 s, 13.5-17 s)
    "ENG_CAB_ON_SWEEP (4).wav": (8.5, 15.5, (42, 52), 1),   # rise with a step at 10-11 s
}


def sweep_window_metrics(x: np.ndarray, fs: int, name: str) -> tuple[dict, dict]:
    t0, t1, band, k = SWEEP_WINDOWS[name]
    tr = line_follow(x, fs, t0, t1, band)
    rpm = tr["f0"] / k * 20
    sm = signal.savgol_filter(rpm, 31, 2) if len(rpm) > 31 else rpm
    resid = 100 * np.median(np.abs(rpm - sm) / sm)
    d = np.diff(sm)
    runmax = np.maximum.accumulate(sm)
    mono = float(np.mean(sm >= 0.99 * runmax))
    grid = [g for g in (600, 900, 1200, 1500, 1800, 2100) if sm.min() * 0.97 <= g <= sm.max() * 1.03]
    r = {"win_t0": t0, "win_t1": t1, "line_k": k, "rpm_start": float(sm[0]), "rpm_end": float(sm[-1]),
         "rpm_lo": float(sm.min()), "rpm_hi": float(sm.max()),
         "rise_rate_rpm_s": float(np.median(d[d > 0]) / 0.05) if (d > 0).any() else 0.0,
         "track_resid_pct": float(resid), "monotonic_frac": mono, "line_prom_db": float(np.median(tr["sal"])),
         "grid_covered": grid}
    r["usable"] = bool(len(grid) >= 3 and resid < 2.0 and mono >= 0.85 and r["line_prom_db"] >= 10)
    return r, tr


# --------------------------------------------------------------------------------------------------- events
def line_track(x: np.ndarray, fs: int, lo: float, hi: float, win_s: float = 0.25, hop_s: float = 0.05) -> tuple[np.ndarray, np.ndarray]:
    w, h = int(win_s * fs), int(hop_s * fs)
    nfft = 1 << 17
    ff = np.fft.rfftfreq(nfft, 1 / fs)
    k = (ff >= lo) & (ff <= hi)
    out, ts = [], []
    for i0 in range(0, len(x) - w + 1, h):
        X = np.abs(np.fft.rfft(x[i0:i0 + w] * signal.windows.hann(w), nfft))
        out.append(ff[k][np.argmax(X[k])])
        ts.append((i0 + w / 2) / fs)
    return np.array(ts), np.array(out)


def onset_s(x: np.ndarray, fs: int, thr_db: float = -20.0) -> float:
    e = np.convolve(np.abs(x), np.ones(96) / 96, "same")
    i = np.argmax(e > e.max() * 10 ** (thr_db / 20))
    return i / fs


def turbo_metrics(x: np.ndarray, fs: int) -> dict:
    f, p = signal.welch(x, fs, nperseg=1 << 14)
    pdb = 10 * np.log10(p + 1e-20)
    prom = pdb - median_filter(pdb, int(400 / (f[1] - f[0])) | 1, mode="nearest")
    k = (f >= 1500) & (f <= 12000)
    i = np.argmax(np.where(k, prom, -99))
    fl, pr = float(f[i]), float(prom[i])
    w = int(0.5 * fs)
    tr = []
    for i0 in range(0, len(x) - w + 1, w // 2):
        ff, pp = signal.welch(x[i0:i0 + w], fs, nperseg=8192)
        kk = (ff > fl * 0.9) & (ff < fl * 1.1)
        tr.append(ff[kk][np.argmax(pp[kk])])
    tr = np.array(tr)
    # share of energy in a +-3 % band around the line vs 1-12 kHz
    band = (f > fl * 0.97) & (f < fl * 1.03)
    hf = (f >= 1000) & (f <= 12000)
    return {"whistle_hz": fl, "whistle_prom_db": pr, "whistle_span_pct": float(100 * np.ptp(tr) / fl),
            "whistle_band_share_pct": float(100 * p[band].sum() / p[hf].sum()),
            "lf_share_pct": float(100 * p[f < 300].sum() / p.sum())}


def strongest_line_band(x: np.ndarray, fs: int, lo: float, hi: float) -> tuple[float, float]:
    f, p = signal.welch(x[: int(0.6 * fs)], fs, nperseg=1 << 14)
    k = (f >= lo) & (f <= hi)
    fl = float(f[k][np.argmax(p[k])])
    return fl * 0.97, fl * 1.03


def stop_metrics(x: np.ndarray, fs: int) -> dict:
    e = env_db(x, fs, 0.1)
    head = rms_db(x[: fs])
    tail = rms_db(x[-int(0.4 * fs):])
    fl = line_follow(x, fs, 0.25, len(x) / fs - 0.25, strongest_line_band(x, fs, 25, 200), tol=0.08)["f0"]
    q = len(fl) // 4
    fall = 100 * (np.median(fl[-q:]) - np.median(fl[:q])) / np.median(fl[:q])
    # time where the 100 ms level first stays 12 dB below the first-second level
    below = np.where(e < head - 12)[0]
    t_drop = float(below[0] * 0.1) if len(below) else None
    return {"stop_tail_vs_head_db": tail - head, "stop_line_fall_pct": float(fall), "stop_t_minus12db_s": t_drop,
            "stop_rundown": bool(tail - head <= -15 and (t_drop is not None and t_drop < len(x) / fs - 0.3))}


def upshift_metrics(x: np.ndarray, fs: int) -> dict:
    tr = line_follow(x, fs, 0.25, len(x) / fs - 0.25, strongest_line_band(x, fs, 60, 260), tol=0.08)
    ts, fl = tr["t"], tr["f0"]
    sm = median_filter(fl, 5, mode="nearest")
    best, at = 0.0, None
    for i in range(len(sm)):
        j = min(len(sm) - 1, i + int(0.6 / 0.05))
        d = (sm[i] - sm[i:j + 1].min()) / sm[i]
        if d > best:
            best, at = d, ts[i]
    e = env_db(x, fs, 0.1)
    after = float(np.median(e[int((at or 0) / 0.1) + 6:])) if at is not None and int(at / 0.1) + 6 < len(e) else -99.0
    before = float(np.median(e[: max(1, int((at or 0) / 0.1))]))
    hp = signal.sosfiltfilt(signal.butter(4, 2000, "hp", fs=fs, output="sos"), x)
    eh = env_db(hp, fs, 0.02)[3:-3]  # ignore the generator's fade-in/out
    click = float(np.max(eh - median_filter(eh, 25, mode="nearest")))
    return {"shift_drop_pct": float(100 * best), "shift_at_s": None if at is None else float(at),
            "level_after_minus_before_db": after - before, "click_db": click, "engine_line_hz_med": float(np.median(fl)),
            "shift_ok": bool(best >= 0.06 and after - before > -6 and click >= 10)}


def hiss_metrics(x: np.ndarray, fs: int) -> dict:
    sos = signal.butter(4, 2000, "hp", fs=fs, output="sos")
    h = signal.sosfiltfilt(sos, x)
    e = env_db(h, fs, 0.01)
    pk = int(np.argmax(e))
    after = np.where(e[pk:] < e[pk] - 20)[0]
    dur = float(after[0] * 0.01) if len(after) else len(e) * 0.01 - pk * 0.01
    bursts, _ = signal.find_peaks(e, height=e.max() - 10, distance=8, prominence=6)
    return {"onset_s": onset_s(x, fs), "hiss_peak_s": pk * 0.01, "hiss_dur_m20_s": dur,
            "hf_share_pct": float(100 * np.sum(h ** 2) / (np.sum(x ** 2) + 1e-20)), "bursts": int(len(bursts)),
            "tail_floor_db": float(np.median(e[-20:]) - e.max())}


def wiper_metrics(x: np.ndarray, fs: int) -> dict:
    sos = signal.butter(4, [1000, 6000], "bp", fs=fs, output="sos")
    e = np.convolve(np.abs(signal.sosfiltfilt(sos, x)), np.ones(480) / 480, "same")
    ed = e[::48]
    pk, _ = signal.find_peaks(ed, height=np.percentile(ed, 90) * 0.6, distance=int(0.3 * 1000))
    t = pk / 1000.0
    iv = np.diff(t)
    dur = len(x) / fs
    wrap = (dur - t[-1]) + t[0] if len(t) else 0
    per = float(np.median(iv)) if len(iv) else 0
    return {"sweeps": int(len(t)), "period_s": per, "period_cv_pct": float(100 * np.std(iv) / np.mean(iv)) if len(iv) > 1 else 99,
            "wrap_s": float(wrap), "wrap_err_pct": float(100 * (wrap - per) / per) if per else 99,
            "interval_minmax_s": [float(iv.min()), float(iv.max())] if len(iv) else []}


def door_metrics(x: np.ndarray, fs: int) -> dict:
    e = env_db(x, fs, 0.01)
    pk = int(np.argmax(e))
    first = int(np.argmax(e > e.max() - 12))
    pre = float(np.median(e[: max(first - 2, 1)])) if first > 3 else float(np.percentile(e, 5))
    post = e[first + 40: first + 150]
    peaks, _ = signal.find_peaks(e, height=e.max() - 15, distance=10, prominence=8)
    return {"latch_s": first * 0.01, "main_peak_s": pk * 0.01, "transients": int(len(peaks)),
            "post_floor_vs_pre_db": float(np.median(post) - pre) if len(post) else 0.0,
            "post_floor_db_rel_peak": float(np.median(post) - e.max()) if len(post) else -99.0}


# --------------------------------------------------------------------------------------------------- scores
def score_engine(r: dict) -> float:
    span = (r["rpm_max"] - r["rpm_min"]) / r["rpm_med"]
    shift = abs(math.log2(r["rpm_nominal"] / r["rpm_med"]))
    return (2.0 * r["ladder_n"] + r["dom_prom_db"] / 4 - 60 * span - 14 * shift - 1.5 * max(0.0, r["level_range_db"] - 6)
            - 10 * (r["clips"] > 0))


def score(r: dict) -> float:
    fid = r["id"]
    if fid in ENGINE_LOOPS:
        return score_engine(r)
    if fid in SWEEPS:
        return (len(r["grid_covered"]) * 3 + r["line_prom_db"] / 3 - 4 * r["track_resid_pct"] + 10 * r["monotonic_frac"]
                + (r["win_t1"] - r["win_t0"]) / 3)
    if fid == "TURBO_WHISTLE_LOOP":
        return r["whistle_prom_db"] - r["whistle_span_pct"] - 0.2 * r["lf_share_pct"]
    if fid == "ENG_STOP_CAB":
        return -r["stop_tail_vs_head_db"] + 0.5 * max(0.0, -r["stop_line_fall_pct"])
    if fid == "GEAR_UPSHIFT_CAB":
        return r["shift_drop_pct"] + min(0.0, r["level_after_minus_before_db"] + 6) + 0.5 * min(r["click_db"], 25)
    if fid == "BRAKE_SERVICE_HISS":
        return (r["hf_share_pct"] / 10 - 20 * r["onset_s"] - 3 * max(0, r["bursts"] - 1) - 4 * abs(r["hiss_dur_m20_s"] - 0.35)
                + 0.2 * (r["lufs"] + 40))
    if fid == "CAB_WIPERS_LOOP":
        return -r["period_cv_pct"] - 0.5 * abs(r["wrap_err_pct"]) - 10 * abs(r["period_s"] - 1.0)
    if fid == "CAB_DOOR_OPEN":
        return -10 * r["latch_s"] + 0.5 * r["post_floor_vs_pre_db"] - 2 * max(0, r["transients"] - 3)
    return 0.0


def requirement(fid: str, r: dict) -> tuple[bool, str]:
    """Does the best variant meet what the prompt asked for (numbers)?"""
    if fid.endswith("_HIGH"):
        ok = (r["rpm_med"] >= 1500 and r["rpm_periodicity"] >= 1500 and (r["rpm_max"] - r["rpm_min"]) / r["rpm_med"] <= 0.15
              and r["level_range_db"] <= 8)
        return ok, f"measured {r['rpm_med']:.0f} rpm (dominant line; ladder spacing {r['rpm_periodicity']:.0f}; asked high, >= 1500), span {100 * (r['rpm_max'] - r['rpm_min']) / r['rpm_med']:.1f} %, level range {r['level_range_db']:.1f} dB"
    if fid.endswith("_IDLE_SLOW"):
        ok = r["rpm_med"] <= 750 and (r["rpm_max"] - r["rpm_min"]) / r["rpm_med"] <= 0.15
        return ok, f"measured {r['rpm_med']:.0f} rpm (asked slow idle, <= 750), span {100 * (r['rpm_max'] - r['rpm_min']) / r['rpm_med']:.1f} %"
    if fid in SWEEPS:
        return r["usable"], (f"line {r['rpm_lo']:.0f}->{r['rpm_hi']:.0f} rpm over {r['win_t1'] - r['win_t0']:.1f} s, "
                             f"resid {r['track_resid_pct']:.1f} %, monotonic {100 * r['monotonic_frac']:.0f} %, "
                             f"line {r['line_prom_db']:.1f} dB, grid {r['grid_covered']}")
    if fid == "TURBO_WHISTLE_LOOP":
        ok = r["whistle_prom_db"] >= 12 and r["whistle_span_pct"] <= 3
        return ok, f"line {r['whistle_hz']:.0f} Hz at {r['whistle_prom_db']:.1f} dB over floor (>= 12), span {r['whistle_span_pct']:.1f} %"
    if fid == "ENG_STOP_CAB":
        return r["stop_rundown"], f"tail vs head {r['stop_tail_vs_head_db']:.1f} dB (<= -15 for a run-down), line {r['stop_line_fall_pct']:+.1f} %"
    if fid == "GEAR_UPSHIFT_CAB":
        return r["shift_ok"], (f"pitch drop {r['shift_drop_pct']:.1f} % (>= 6) at {r['shift_at_s']} s, level after "
                               f"{r['level_after_minus_before_db']:+.1f} dB (> -6), shift click {r['click_db']:.1f} dB (>= 10)")
    if fid == "BRAKE_SERVICE_HISS":
        ok = r["onset_s"] <= 0.03 and r["bursts"] <= 1 and r["hf_share_pct"] >= 60 and 0.1 <= r["hiss_dur_m20_s"] <= 0.8
        return ok, f"onset {1000 * r['onset_s']:.0f} ms, >2 kHz {r['hf_share_pct']:.0f} %, -20 dB after {r['hiss_dur_m20_s']:.2f} s, bursts {r['bursts']}"
    if fid == "CAB_WIPERS_LOOP":
        ok = r["period_cv_pct"] <= 8 and abs(r["wrap_err_pct"]) <= 15
        return ok, f"period {r['period_s']:.2f} s (asked 1.0), CV {r['period_cv_pct']:.1f} %, wrap {r['wrap_s']:.2f} s ({r['wrap_err_pct']:+.0f} %)"
    if fid == "CAB_DOOR_OPEN":
        ok = r["latch_s"] <= 0.1 and r["post_floor_vs_pre_db"] >= 3
        return ok, f"latch at {r['latch_s']:.2f} s (<= 0.1), air layer {r['post_floor_vs_pre_db']:+.1f} dB over pre-latch floor"
    return True, ""


# --------------------------------------------------------------------------------------------------- sheets
def sheet(fid: str, rows: list[dict], src: Path, out: Path, tracks: dict) -> None:
    rr = sorted([r for r in rows if r["id"] == fid], key=lambda r: r["variant"])
    eng = fid in ENGINE_LOOPS or fid in SWEEPS
    fmax = 420 if eng else (500 if fid in ("GEAR_UPSHIFT_CAB", "ENG_STOP_CAB") else 12000)
    fig, axs = plt.subplots(2, len(rr), figsize=(4.0 * len(rr), 6), squeeze=False)
    for j, r in enumerate(rr):
        d, fs = sf.read(src / r["file"], always_2d=True)
        x = d.mean(axis=1)
        nper = (1 << 14) if eng else (8192 if fmax == 500 else 2048)
        f, t, S = signal.spectrogram(x, fs, nperseg=nper, noverlap=nper * 7 // 8)
        k = f <= fmax
        L = 10 * np.log10(S[k] + 1e-20)
        ax = axs[0, j]
        ax.pcolormesh(t, f[k], L, shading="auto", cmap="magma", vmin=L.max() - 70)
        if r["file"] in tracks:
            tr = tracks[r["file"]]
            ax.plot(tr["t"], tr["f0"], color="cyan", lw=0.7)
        if "rpm_med" in r:
            for h in range(1, 7):
                ax.axhline(h * r["rpm_med"] / 20, color="cyan", lw=0.4, ls=":")
        ax.set_title(f"{r['file']}  #{r['rank']}  score {r['score']:.1f}", fontsize=7)
        ax.tick_params(labelsize=6)
        axs[1, j].plot(np.arange(len(x)) / fs, x, lw=0.3)
        axs[1, j].set_ylim(-1, 1)
        axs[1, j].tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(out / f"{fid}.png", dpi=60)
    plt.close(fig)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", default=str(MAIN / "art-source" / "audio" / "elevenlabs"))
    ap.add_argument("--out", default=str(ROOT / "artifacts" / "audio-regen01" / "analysis"))
    a = ap.parse_args()
    src, out = Path(a.src), Path(a.out)
    (out / "sheets").mkdir(parents=True, exist_ok=True)
    rows, tracks, sweeps = [], {}, {}
    for fid, vs in VARIANTS.items():
        for v in vs:
            p = src / f"{fid} ({v}).wav"
            r, x, fs = common(p)
            r.update(seam(x, fs))
            if fid in ENGINE_LOOPS:
                e = analyse(p)
                r.update({k: e[k] for k in ("persp", "load", "rpm_nominal", "rpm_actual", "rpm_med", "rpm_min", "rpm_max",
                                            "rpm_std", "dom_hz", "dom_prom_db", "ladder_n", "ladder_db", "comb_rpm", "env_rpm",
                                            "drift_db", "seam_jump_ratio")})
                r["span_pct"] = 100 * (r["rpm_max"] - r["rpm_min"]) / r["rpm_med"]
                # a strong line at half the dominant one means the ladder spacing (periodicity) is an octave lower
                f, pdb = welch_db(x, fs)
                pr = prominence_db(f, pdb)
                df = f[1] - f[0]
                j = int(round(r["dom_hz"] / 2 / df))
                r["suboct_prom_db"] = float(pr[max(0, j - 3): j + 4].max())
                j = int(round(r["dom_hz"] * 1.5 / df))
                r["threehalf_prom_db"] = float(pr[max(0, j - 3): j + 4].max())  # line at 1.5x: spacing = dom/2
                half = r["suboct_prom_db"] >= 6 or r["threehalf_prom_db"] >= 6
                r["rpm_periodicity"] = r["rpm_med"] / 2 if half else r["rpm_med"]
            elif fid in SWEEPS:
                m, tr = sweep_window_metrics(x, fs, p.name)
                tracks[p.name] = tr
                r.update(m)
                sweeps[p.name] = {"t": np.round(tr["t"], 2).tolist(), "rpm": np.round(tr["f0"] * 20, 1).tolist(),
                                  "sal": np.round(tr["sal"], 2).tolist()}
            elif fid == "TURBO_WHISTLE_LOOP":
                r.update(turbo_metrics(x, fs))
            elif fid == "ENG_STOP_CAB":
                r.update(stop_metrics(x, fs))
            elif fid == "GEAR_UPSHIFT_CAB":
                r.update(upshift_metrics(x, fs))
            elif fid == "BRAKE_SERVICE_HISS":
                r.update(hiss_metrics(x, fs))
            elif fid == "CAB_WIPERS_LOOP":
                r.update(wiper_metrics(x, fs))
            elif fid == "CAB_DOOR_OPEN":
                r.update(door_metrics(x, fs))
            r["score"] = score(r)
            rows.append(r)
            print(p.name, {k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()
                           if k not in ("file", "id", "variant", "fs", "ladder_db")})
    picks = {}
    for fid in VARIANTS:
        rr = sorted([r for r in rows if r["id"] == fid], key=lambda r: r["score"], reverse=True)
        for i, r in enumerate(rr):
            r["rank"] = i + 1
        ok, why = requirement(fid, rr[0])
        picks[fid] = {"pick": rr[0]["file"], "score": round(rr[0]["score"], 2), "meets_prompt": ok, "why": why,
                      "ranking": [(r["file"], round(r["score"], 2)) for r in rr], "prompt": prompt_entry(fid)}
    (out / "regen01.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    (out / "picks.json").write_text(json.dumps(picks, indent=1), encoding="utf-8")
    (out / "sweeps.json").write_text(json.dumps(sweeps), encoding="utf-8")
    keys = sorted({k for r in rows for k in r}, key=lambda k: (k not in ("file", "id", "variant", "rank", "score"), k))
    with open(out / "regen01.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()})
    for fid in VARIANTS:
        sheet(fid, rows, src, out / "sheets", tracks)
    for fid, p in picks.items():
        print(f"{fid:20s} {p['pick']:28s} {'PASS' if p['meets_prompt'] else 'FAIL'}  {p['why']}")


if __name__ == "__main__":
    main()
