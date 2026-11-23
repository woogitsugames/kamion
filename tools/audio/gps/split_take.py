"""Split an ElevenLabs batch take (sentences separated by <break time="1.5s" />) into one clip per sentence (ADR 0328).

Silence detection on 10 ms RMS frames relative to the take's peak; gaps >= MIN_GAP_S split. The number of segments must
equal the number of sentences, else the take is rejected (a swallowed break = regenerate). Each segment keeps PAD_S of
the original audio around the speech (natural attack/decay, no clicks) plus a 5 ms raised-cosine fade at both ends.
"""
from __future__ import annotations

import numpy as np

FRAME_S = 0.01
THRESH_DB = -45.0      # below peak - WORKING_VALUE: the takes have a digital-silence floor (-90 dB) between sentences
MIN_GAP_S = 0.7        # breaks are 1.5 s; Polish intra-sentence pauses stay < 0.4 s in the test take (WORKING_VALUE)
PAD_S = 0.04
FADE_S = 0.005


def speech_segments(x: np.ndarray, sr: int, thresh_db: float = THRESH_DB, min_gap_s: float = MIN_GAP_S):
    n = int(FRAME_S * sr)
    m = len(x) // n
    rms = np.sqrt(np.mean(x[: m * n].reshape(m, n) ** 2, axis=1))
    db = 20 * np.log10(rms + 1e-12)
    on = db > (np.max(db) + thresh_db)
    idx = np.where(on)[0]
    if len(idx) == 0:
        return []
    segs = []
    start = prev = idx[0]
    gap = int(round(min_gap_s / FRAME_S))
    for i in idx[1:]:
        if i - prev > gap:
            segs.append((start * n, (prev + 1) * n))
            start = i
        prev = i
    segs.append((start * n, (prev + 1) * n))
    return segs


def cut(x: np.ndarray, sr: int, seg) -> np.ndarray:
    pad = int(PAD_S * sr)
    a, b = max(0, seg[0] - pad), min(len(x), seg[1] + pad)
    y = x[a:b].copy()
    f = int(FADE_S * sr)
    if len(y) > 2 * f and f > 0:
        w = 0.5 - 0.5 * np.cos(np.linspace(0, np.pi, f))
        y[:f] *= w
        y[-f:] *= w[::-1]
    return y
