"""ADR 0148: offline mix of a Unity AudioSource capture (IdleAudioCaptureTests -> capture_<set>.csv).

    uv run --project tools/audio python tools/audio/idle_render.py <capture.csv> <out.wav> [--t0 S --t1 S] [--only SUBSTR]

Every frame (0.01 s) the capture lists, for each AudioSource on the truck, the clip, volume, pitch and timeSamples.
The renderer plays the clips like Unity does (loop, linear-interpolation resampling, pitch, clip rate / 48 kHz),
starts each voice at the captured timeSamples (EngineLayerGrid sets it after Play: crank-phase alignment) and ramps
the volume linearly across the frame. 3D attenuation is ignored (the capture is the cab camera: exterior voices are
silent). Clip files are looked up by name in the ElevenLabs clips, game Generated clips and art-source/audio/generated.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
FS = 48000
DIRS = [ROOT / "game" / "Assets" / "_Project" / "Audio" / "ElevenLabs" / "Clips",
        ROOT / "game" / "Assets" / "_Project" / "Audio" / "Generated" / "Clips",
        ROOT / "art-source" / "audio" / "generated"]
MAIN = ROOT.parents[2] if ROOT.parent.name == "worktrees" else ROOT  # worktree -> main repo (art-source is not in git)
if MAIN != ROOT:
    DIRS.append(MAIN / "art-source" / "audio" / "generated")

_cache: dict[str, tuple[np.ndarray, int]] = {}


def clip(name: str, override: dict[str, Path] | None = None) -> tuple[np.ndarray, int]:
    if name in _cache:
        return _cache[name]
    p = (override or {}).get(name)
    if p is None:
        for d in DIRS:
            hit = list(d.rglob(name + ".wav")) if d.exists() else []
            if hit:
                p = hit[0]
                break
    if p is None:
        raise FileNotFoundError(name)
    x, fs = sf.read(p, always_2d=True)
    _cache[name] = (x.mean(1).astype(np.float64), fs)
    return _cache[name]


def parse(path: Path):
    lines = path.read_text(encoding="utf-8").splitlines()
    names = lines[0].split(";")[1:]
    rows = []
    for ln in lines[2:]:
        f = ln.split(";")
        tel = {"t": float(f[0]), "phase": f[1], "rpm": float(f[2]), "load": float(f[3]), "throttle": float(f[4]),
               "ebrake": float(f[5]), "boost": float(f[6]), "gear": int(f[7]), "kmh": float(f[8]), "air": float(f[9].split("|")[0]), "comp": f[9].split("|")[1] == "1"}
        src = []
        for s in f[10:]:
            if s == "-":
                src.append(None)
            else:
                c, v, p, _pl, ts, sp = s.split("|")
                src.append((c, float(v), float(p), int(ts), float(sp)))
        rows.append((tel, src))
    return names, rows


def render(names, rows, dt=0.01, only: str | None = None, exclude: str | None = None, override=None,
           realign: bool = False) -> np.ndarray:
    n = int(round(dt * FS))
    out = np.zeros(n * len(rows))
    ns = len(names)
    state = [None] * ns  # (clipname, pos, gain)
    for fi, (_tel, src) in enumerate(rows):
        for si in range(ns):
            s = src[si]
            if s is not None and only and only not in names[si] and only not in s[0]:
                s = None
            if s is not None and exclude and (exclude in names[si] or exclude in s[0]):
                s = None
            prev = state[si]
            if s is None:
                if prev is not None and prev[2] > 0:  # fade the last frame out (Unity stops at a frame edge)
                    pass
                state[si] = None
                continue
            cname, vol, pitch, ts, _sp = s
            data, cfs = clip(cname, override)
            L = len(data)
            if prev is None or prev[0] != cname:
                pos, g0 = float(ts % L), 0.0 if prev is None else 0.0
            else:
                pos, g0 = prev[1], prev[2]
            step = pitch * cfs / FS
            idx = pos + step * np.arange(n)
            i0 = np.floor(idx).astype(np.int64)
            fr = idx - i0
            a = data[i0 % L] * (1 - fr) + data[(i0 + 1) % L] * fr
            g = np.linspace(g0, vol, n, endpoint=False)
            out[fi * n:(fi + 1) * n] += a * g
            state[si] = (cname, (pos + step * n) % L, vol)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("csv")
    ap.add_argument("out")
    ap.add_argument("--only")
    ap.add_argument("--exclude")
    a = ap.parse_args()
    names, rows = parse(Path(a.csv))
    y = render(names, rows, only=a.only, exclude=a.exclude)
    sf.write(a.out, y.astype(np.float32), FS)
    print(f"{a.out}: {len(y) / FS:.1f} s, peak {np.max(np.abs(y)):.3f}")


if __name__ == "__main__":
    main()
