"""Small DSP toolkit for the procedural truck audio pipeline.

Everything here is our own code (RBJ "Audio EQ Cookbook" biquad formulas are public
domain math). Key idea for seamless loops: every source is built to be *periodic*
with the loop length L, and every causal filter is applied with ``periodic_sosfilt``
(signal tiled several times, last period kept), which yields the exact steady-state
periodic response. The loop seam is therefore mathematically continuous.
"""

from __future__ import annotations

import numpy as np
from scipy import signal

FS = 48_000


# --------------------------------------------------------------------------- biquads
def _rbj(kind: str, f0: float, q: float = 0.7071, gain_db: float = 0.0, fs: int = FS) -> np.ndarray:
    """One RBJ cookbook biquad as an sos row [b0 b1 b2 a0 a1 a2] (normalised a0=1)."""
    f0 = min(f0, 0.49 * fs)
    w0 = 2.0 * np.pi * f0 / fs
    cw, sw = np.cos(w0), np.sin(w0)
    alpha = sw / (2.0 * q)
    a_lin = 10.0 ** (gain_db / 40.0)
    if kind == "lp":
        b = [(1 - cw) / 2, 1 - cw, (1 - cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "hp":
        b = [(1 + cw) / 2, -(1 + cw), (1 + cw) / 2]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "bp":  # constant 0 dB peak gain
        b = [alpha, 0.0, -alpha]
        a = [1 + alpha, -2 * cw, 1 - alpha]
    elif kind == "peak":
        b = [1 + alpha * a_lin, -2 * cw, 1 - alpha * a_lin]
        a = [1 + alpha / a_lin, -2 * cw, 1 - alpha / a_lin]
    elif kind == "lowshelf":
        sq = 2 * np.sqrt(a_lin) * alpha
        b = [a_lin * ((a_lin + 1) - (a_lin - 1) * cw + sq), 2 * a_lin * ((a_lin - 1) - (a_lin + 1) * cw),
             a_lin * ((a_lin + 1) - (a_lin - 1) * cw - sq)]
        a = [(a_lin + 1) + (a_lin - 1) * cw + sq, -2 * ((a_lin - 1) + (a_lin + 1) * cw),
             (a_lin + 1) + (a_lin - 1) * cw - sq]
    elif kind == "highshelf":
        sq = 2 * np.sqrt(a_lin) * alpha
        b = [a_lin * ((a_lin + 1) + (a_lin - 1) * cw + sq), -2 * a_lin * ((a_lin - 1) + (a_lin + 1) * cw),
             a_lin * ((a_lin + 1) + (a_lin - 1) * cw - sq)]
        a = [(a_lin + 1) - (a_lin - 1) * cw + sq, 2 * ((a_lin - 1) - (a_lin + 1) * cw),
             (a_lin + 1) - (a_lin - 1) * cw - sq]
    else:
        raise ValueError(kind)
    b = np.asarray(b, dtype=np.float64) / a[0]
    a = np.asarray(a, dtype=np.float64) / a[0]
    return np.concatenate([b, a])


def lp(f, q=0.7071):
    return _rbj("lp", f, q)


def hp(f, q=0.7071):
    return _rbj("hp", f, q)


def bp(f, q):
    return _rbj("bp", f, q)


def peak(f, q, g):
    return _rbj("peak", f, q, g)


def lowshelf(f, g, q=0.7071):
    return _rbj("lowshelf", f, q, g)


def highshelf(f, g, q=0.7071):
    return _rbj("highshelf", f, q, g)


def chain(*rows: np.ndarray) -> np.ndarray:
    return np.vstack(rows)


# --------------------------------------------------------------------------- periodic processing
def periodic_sosfilt(x: np.ndarray, sos: np.ndarray, periods: int = 3) -> np.ndarray:
    """Steady-state response of a causal IIR filter to the infinitely repeated signal ``x``.

    Valid while the filter's impulse response decays within (periods-1)*len(x) samples,
    which holds for every filter used here (longest tau ~ 50 ms vs loops of >= 2 s).
    """
    y = signal.sosfilt(sos, np.tile(x, periods))
    return y[-len(x):]


def periodic_noise(rng: np.random.Generator, n: int) -> np.ndarray:
    return rng.standard_normal(n)


def periodic_lfo(n: int, cycles: int, phase: float = 0.0) -> np.ndarray:
    """Sine with an integer number of cycles over n samples (wraps seamlessly)."""
    t = np.arange(n) / n
    return np.sin(2 * np.pi * cycles * t + phase)


def smooth_random_periodic(rng: np.random.Generator, n: int, max_cycles: int, n_terms: int = 6) -> np.ndarray:
    """Band-limited random wobble in [-1, 1] that is periodic over n samples."""
    out = np.zeros(n)
    for _ in range(n_terms):
        c = int(rng.integers(1, max_cycles + 1))
        out += rng.uniform(0.3, 1.0) * periodic_lfo(n, c, rng.uniform(0, 2 * np.pi))
    m = np.max(np.abs(out))
    return out / m if m > 0 else out


def add_kernel_circular(buf: np.ndarray, t0: float, kernel_of_t, length: int, amp: float = 1.0) -> None:
    """Add ``amp * kernel(t)`` starting at fractional sample t0, wrapping around the loop."""
    n_buf = len(buf)
    i0 = int(np.floor(t0))
    frac = t0 - i0
    n = np.arange(length)
    k = kernel_of_t((n - frac) / FS)
    idx = (i0 + n) % n_buf
    if length <= n_buf:
        buf[idx] += amp * k
    else:  # kernel longer than loop: accumulate safely
        np.add.at(buf, idx, amp * k)


# --------------------------------------------------------------------------- non-linear / util
def soft_clip(x: np.ndarray, drive: float) -> np.ndarray:
    """Memoryless tanh saturation, unity small-signal gain (keeps loops periodic)."""
    if drive <= 0:
        return x
    return np.tanh(drive * x) / drive


def db(x: float) -> float:
    return 20.0 * np.log10(max(float(x), 1e-12))


def rms(x: np.ndarray) -> float:
    return float(np.sqrt(np.mean(np.square(x))))


def fade_edges(x: np.ndarray, fade_in_s: float, fade_out_s: float) -> np.ndarray:
    y = x.copy()
    ni, no = int(fade_in_s * FS), int(fade_out_s * FS)
    if ni > 0:
        y[:ni] *= 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, ni))
    if no > 0:
        y[-no:] *= 0.5 + 0.5 * np.cos(np.linspace(0, np.pi, no))
    return y


def save_png_small(fig, path, dpi: int = 80, colors: int = 96) -> None:
    """Save a matplotlib figure as a palette PNG (keeps report images well under 300 KB)."""
    import io

    from PIL import Image

    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi)
    buf.seek(0)
    img = Image.open(buf).convert("RGB").quantize(colors=colors, method=Image.Quantize.MEDIANCUT)
    img.save(path, optimize=True)


def write_ogg(path, x: np.ndarray, compression_level: float = 0.55, fs: int = FS) -> None:
    """Write mono Ogg Vorbis in small blocks (libsndfile's Vorbis encoder overflows the
    stack on Windows when handed a long buffer in one call)."""
    from pathlib import Path

    import soundfile as sf

    Path(path).parent.mkdir(parents=True, exist_ok=True)
    data = np.asarray(x, dtype=np.float32)
    with sf.SoundFile(path, "w", fs, 1, format="OGG", subtype="VORBIS", compression_level=compression_level) as f:
        for i in range(0, len(data), 4096):
            f.write(data[i:i + 4096])
