"""Offline mirror of the Unity runtime player (game/Assets/_Project/Audio/EngineLayerGrid.cs).

Same algorithm, same constants, so the demo renders and the crossfade checks describe what
the game will do: per "frame" (60 Hz) the controller smooths the inputs, picks the
bracketing rpm x load cells, assigns pooled voices, sets pitch = rpm / clip_rpm and fades
voice gains; voices play the loops with linear-interpolation resampling (like an
AudioSource with pitch != 1). New voices start crank-phase-aligned to the loudest voice.

If you change the algorithm here, change EngineLayerGrid.cs too (and vice versa).
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
GEN = ROOT / "art-source" / "audio" / "generated"

FRAME_HZ = 60.0
VOICE_FADE_S = 0.030       # gain slew for voice (de)activation and weight changes
MIN_WEIGHT = 1e-4


def bracket(points: list[float], v: float) -> tuple[int, int, float]:
    """Index pair around v and interpolation t in [0,1] (clamped at the ends)."""
    if v <= points[0]:
        return 0, 0, 0.0
    if v >= points[-1]:
        n = len(points) - 1
        return n, n, 0.0
    i = int(np.searchsorted(points, v, side="right") - 1)
    t = (v - points[i]) / (points[i + 1] - points[i])
    return i, i + 1, float(t)


XFADE_COHERENCE = 0.9  # sweep test: 0.5 -> 1.9 dB max ripple, 0.8 -> 1.1 dB, 1.0 -> 0.7 dB


def xfade(t: float) -> tuple[float, float]:
    """Hybrid crossfade: blend of equal-gain (coherent) and equal-power (incoherent) laws.

    Crank-phase-aligned loops are mostly coherent in their low firing harmonics (which carry
    most of the energy) and incoherent in the noise. XFADE_COHERENCE = 1 is pure equal-gain,
    0 pure equal-power. Tuned with the sweep test in render_demo.py.
    """
    c = XFADE_COHERENCE
    a = c * (1.0 - t) + (1.0 - c) * math.cos(t * math.pi * 0.5)
    b = c * t + (1.0 - c) * math.sin(t * math.pi * 0.5)
    return a, b


@dataclass
class Clip:
    data: np.ndarray
    rpm: float          # exact loop rpm
    cycles: int

    @property
    def spc(self) -> float:
        return len(self.data) / self.cycles


class Voice:
    def __init__(self):
        self.clip: Clip | None = None
        self.cell = -1
        self.pos = 0.0
        self.gain = 0.0
        self.target = 0.0
        self.pitch = 1.0

    @property
    def active(self) -> bool:
        return self.clip is not None


class LayerGrid:
    """rpm x load grid of looping clips with a fixed voice pool (mirror of EngineLayerGrid.cs)."""

    def __init__(self, rpms: list[float], loads: list[float], clips: list[Clip], pool: int = 6, seed: int = 1):
        self.rpms, self.loads, self.clips = rpms, loads, clips  # clips[load_idx * n_rpm + rpm_idx]
        self.voices = [Voice() for _ in range(pool)]
        self.rng_state = seed

    def _rand(self, n: int) -> int:  # tiny LCG, same as C# (deterministic, no allocation)
        self.rng_state = (1664525 * self.rng_state + 1013904223) & 0xFFFFFFFF
        return (self.rng_state >> 8) % max(1, n)

    def update(self, rpm: float, load: float, bank_gain: float) -> None:
        nr = len(self.rpms)
        r0, r1, tr = bracket(self.rpms, rpm)
        l0, l1, tl = bracket(self.loads, load) if len(self.loads) > 1 else (0, 0, 0.0)
        gr0, gr1 = xfade(tr)
        gl0, gl1 = xfade(tl)
        cells: dict[int, float] = {}
        for li, gl in ((l0, gl0), (l1, gl1)):
            for ri, gr in ((r0, gr0), (r1, gr1)):
                c = li * nr + ri  # clamped ends map both corners to one cell; xfade(0)=(1,0) so summing is exact
                cells[c] = cells.get(c, 0.0) + gl * gr * bank_gain
        cells = {c: w for c, w in cells.items() if w > MIN_WEIGHT}
        # reference voice for phase alignment
        ref = max((v for v in self.voices if v.active), key=lambda v: v.gain, default=None)
        for v in self.voices:
            if v.active:
                v.target = cells.pop(v.cell, 0.0)
        for c, w in cells.items():  # cells that need a new voice
            free = next((v for v in self.voices if not v.active), None)
            if free is None:  # steal the quietest voice (never the phase reference)
                free = min((v for v in self.voices if v is not ref), key=lambda v: v.gain)
            clip = self.clips[c]
            free.clip, free.cell, free.gain, free.target = clip, c, 0.0, w
            k = self._rand(clip.cycles)
            phase = 0.0
            if ref is not None and ref.clip is not None:
                phase = (ref.pos / ref.clip.spc) % 1.0
            free.pos = (k + phase) * clip.spc
        for v in self.voices:
            if v.active:
                v.pitch = rpm / v.clip.rpm

    def render(self, n: int, fs: int) -> np.ndarray:
        out = np.zeros(n)
        step = 1.0 / (VOICE_FADE_S * fs)
        for v in self.voices:
            if not v.active:
                continue
            idx = v.pos + v.pitch * np.arange(n)
            L = len(v.clip.data)
            i0 = np.floor(idx).astype(np.int64)
            fr = idx - i0
            i0 %= L
            i1 = (i0 + 1) % L
            s = v.clip.data[i0] * (1 - fr) + v.clip.data[i1] * fr
            # linear gain slew toward target
            g = v.gain + np.clip(v.target - v.gain, -step * np.arange(1, n + 1), step * np.arange(1, n + 1))
            out += s * g
            v.gain = float(g[-1])
            v.pos = float((v.pos + v.pitch * n) % L)
            if v.target <= 0.0 and v.gain <= 1e-5:
                v.clip, v.cell, v.gain = None, -1, 0.0
        return out

    def active_voices(self) -> int:
        return sum(v.active for v in self.voices)


class LoopVoice:
    """Single looping clip with pitch/gain (turbo whistle, road, wind)."""

    def __init__(self, data: np.ndarray):
        self.data, self.pos, self.gain = data, 0.0, 0.0

    def render(self, n: int, pitch: float, gain: float, fs: int) -> np.ndarray:
        idx = self.pos + pitch * np.arange(n)
        L = len(self.data)
        i0 = np.floor(idx).astype(np.int64)
        fr = idx - i0
        s = self.data[i0 % L] * (1 - fr) + self.data[(i0 + 1) % L] * fr
        g = np.linspace(self.gain, gain, n, endpoint=False)
        self.gain = gain
        self.pos = float((self.pos + pitch * n) % L)
        return s * g


def load_manifest() -> dict:
    return json.loads((GEN / "manifest.json").read_text(encoding="utf-8"))


def load_grid(manifest: dict, kind: str, perspective: str, pool: int) -> LayerGrid:
    sel = [c for c in manifest["clips"] if c["kind"] == kind and c["perspective"] == perspective]
    rpms = sorted({c["rpm"] for c in sel})
    if kind == "engine":
        layer_names = sorted(manifest["load_layers"], key=lambda k: manifest["load_layers"][k])
        loads = [manifest["load_layers"][k] for k in layer_names]
    else:
        layer_names, loads = [None], [0.0]
    clips = []
    for ln in layer_names:
        for r in rpms:
            c = next(c for c in sel if c["rpm"] == r and c["layer"] == ln)
            data, _ = sf.read(ROOT / c["file"])
            clips.append(Clip(data.astype(np.float64), c["rpm_exact"], c["cycles"]))
    return LayerGrid([float(r) for r in rpms], loads, clips, pool=pool)


def load_sfx(manifest: dict, name: str) -> np.ndarray:
    s = next(s for s in manifest["sfx"] if s["name"] == name)
    data, _ = sf.read(ROOT / s["file"])
    return data.astype(np.float64)
