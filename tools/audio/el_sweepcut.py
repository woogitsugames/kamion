"""Cut constant-rpm engine loops out of a one-shot rpm sweep (ADR 0138).

A REGEN-01 SWEEP file is one recording of the engine rising slowly under load. One followed spectral line (firing
order, or a known harmonic of it) gives f(t). For a grid rpm R the cutter takes the longest segment around the moment
f(t) = R/20 in which f stays within +-MAX_DEV of R/20, and time-warps it so the followed line sits exactly on R/20 for
the whole segment ("flattening": output sample n reads the input at the time where the accumulated line phase equals
R/20 * n / fs, cubic interpolation). All other partials move with the same local ratio, so the ladder stays harmonic.
The loop seam is then made like el_prepare.seam_loop (equal-power crossfade of the last 40 ms into the first).
Targets outside the rising range use an authored steady window (idle before the rise, plateau after it) and the same
warp, which there reduces to a plain pitch shift by R / rpm_measured.
"""

from __future__ import annotations

import numpy as np
from scipy import signal
from scipy.interpolate import CubicSpline

MAX_DEV = 0.10     # max |f/f_R - 1| inside a cut segment (the warp never stretches more than this)
MIN_LEN_S = 0.8
MAX_LEN_S = 4.0


def smooth_track(t: np.ndarray, f: np.ndarray, frames: int = 31) -> np.ndarray:
    return signal.savgol_filter(f, frames, 2) if len(f) > frames else f


def grow(ratio: np.ndarray, i: int, dt: float) -> tuple[int, int]:
    """Largest window [l, r] around frame i (asymmetric, <= MAX_LEN_S) with |ratio| <= MAX_DEV."""
    l = r = i
    nmax = int(MAX_LEN_S / dt)
    while r - l < nmax:
        cl = l - 1 >= 0 and abs(ratio[l - 1]) <= MAX_DEV
        cr = r + 1 < len(ratio) and abs(ratio[r + 1]) <= MAX_DEV
        if not (cl or cr):
            break
        # grow towards the side that stays closer to the target
        if cl and (not cr or abs(ratio[l - 1]) <= abs(ratio[r + 1])):
            l -= 1
        else:
            r += 1
    return l, r


def choose_segment(t: np.ndarray, fsm: np.ndarray, f_target: float) -> tuple[float, float] | None:
    """Longest window (<= MAX_LEN_S) containing a frame with f within 3 % of f_target and |f/f_target-1| <= MAX_DEV."""
    dt = t[1] - t[0]
    ratio = fsm / f_target - 1
    best = None
    for i in np.where(np.abs(ratio) <= 0.03)[0]:
        l, r = grow(ratio, i, dt)
        if best is None or r - l > best[1] - best[0]:
            best = (l, r)
    if best is None or (best[1] - best[0]) * dt < MIN_LEN_S:
        return None
    return float(t[best[0]]), float(t[best[1]])


def top_segment(t: np.ndarray, fsm: np.ndarray) -> tuple[float, float]:
    """Window around the highest point of the track (plateau / peak), |f/f_max-1| <= MAX_DEV, <= MAX_LEN_S."""
    i = int(np.argmax(fsm))
    l, r = grow(fsm / fsm[i] - 1, i, t[1] - t[0])
    return float(t[l]), float(t[r])


def warp_to_constant(x: np.ndarray, fs: int, t: np.ndarray, fsm: np.ndarray, ta: float, tb: float, f_target: float) -> tuple[np.ndarray, dict]:
    """Resample x[ta:tb] so the followed line (fsm at times t) becomes the constant f_target."""
    a, b = int(ta * fs), int(tb * fs)
    ts = np.arange(a, b + 1) / fs
    fi = np.interp(ts, t, fsm)
    cyc = np.concatenate([[0.0], np.cumsum(fi[:-1]) / fs])  # accumulated line cycles at each input sample
    m = int(np.floor(cyc[-1] * fs / f_target))
    want = np.arange(m) * f_target / fs
    tau = np.interp(want, cyc, ts)
    seg = x[a:b + 1]
    y = CubicSpline(ts, seg)(tau)
    local = f_target / fi
    return y, {"seg_t0": ta, "seg_t1": tb, "seg_len_s": tb - ta, "warp_min": float(local.min()),
               "warp_max": float(local.max()), "rpm_measured_mean": float(fi.mean() * 20)}


def flatten_level(y: np.ndarray, fs: int, win_s: float = 0.05, smooth_s: float = 0.6) -> tuple[np.ndarray, float]:
    """Remove the slow level ramp of a sweep segment (the engine gets louder as it revs), so the loop does not pulse
    at its own period: divide by the 50 ms RMS envelope smoothed over 0.6 s. Returns (y, range of the applied gain dB)."""
    w = int(win_s * fs)
    n = len(y) // w
    e = np.sqrt(np.array([np.mean(y[i * w:(i + 1) * w] ** 2) for i in range(n)]) + 1e-20)
    k = max(3, int(smooth_s / win_s) | 1)
    es = signal.savgol_filter(np.log(e), min(k, n - (1 - n % 2)), 1) if n > 4 else np.log(e)
    g = np.exp(np.mean(es) - es)
    gs = np.interp(np.arange(len(y)), (np.arange(n) + 0.5) * w, g)
    return y * gs, float(20 * np.log10(g.max() / g.min()))
