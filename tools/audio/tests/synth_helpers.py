"""Synthetic signals generated in-test (no repo audio files)."""

from __future__ import annotations

import numpy as np

FS = 48_000


def firing_hz(rpm: float) -> float:
    """Firing frequency of an inline six, four-stroke: order 3 -> f = rpm/60*3 = rpm/20 Hz."""
    return rpm / 20.0


def harmonic_engine(fs: int, rpm: float, dur_s: float, n_harm: int = 8,
                    snr_db: float | None = None, seed: int = 7) -> np.ndarray:
    """Synthetic constant-rpm engine loop: harmonic ladder of the firing frequency (+ noise)."""
    n = int(dur_s * fs)
    t = np.arange(n) / fs
    f = firing_hz(rpm)
    x = np.zeros(n)
    for k in range(1, n_harm + 1):
        x += (1.0 / k) * np.sin(2 * np.pi * k * f * t + 0.7 * k)
    x /= np.abs(x).max()
    x *= 0.7
    if snr_db is not None:
        rng = np.random.default_rng(seed)
        p_sig = float(np.mean(x ** 2))
        x = x + rng.standard_normal(n) * np.sqrt(p_sig / 10 ** (snr_db / 10))
    return x


def linear_chirp(fs: int, f0: float, f1: float, dur_s: float, n_harm: int = 3) -> np.ndarray:
    """Synthetic rpm sweep: spectral line rising linearly f0 -> f1 over dur_s, with harmonics."""
    n = int(dur_s * fs)
    t = np.arange(n) / fs
    phase = 2 * np.pi * (f0 * t + 0.5 * (f1 - f0) / dur_s * t ** 2)
    x = np.zeros(n)
    for k in range(1, n_harm + 1):
        x += (1.0 / k) * np.sin(k * phase + 0.3 * k)
    return x / np.abs(x).max() * 0.7


def dominant_hz(x: np.ndarray, fs: int, lo: float, hi: float) -> float:
    """Interpolated peak of the zero-padded FFT magnitude inside [lo, hi] Hz."""
    nfft = 1 << 20
    X = np.abs(np.fft.rfft(x * np.hanning(len(x)), nfft))
    ff = np.fft.rfftfreq(nfft, 1 / fs)
    band = np.where((ff >= lo) & (ff <= hi))[0]
    j = band[int(np.argmax(X[band]))]
    a, b, c = np.log(X[j - 1] + 1e-20), np.log(X[j] + 1e-20), np.log(X[j + 1] + 1e-20)
    return float((j + 0.5 * (a - c) / (a - 2 * b + c + 1e-20)) * fs / nfft)
