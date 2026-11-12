"""A/B listening files for ADR 0138: the ElevenLabs set before (ADR 0137, main) and after REGEN-01 (this branch).

    uv run python el_ab.py [--before <repo root>]

Writes artifacts/audio-regen01/ab/ (OGG Vorbis q0.6, 48 kHz mono, each <= 30 s, -16 LUFS, peak <= -1 dBFS):
  drive_{ext,cab}_{0137,0138}.ogg   el_demo scenario 1.5-31.5 s (start, idle, pull away with 3 upshifts, cruise, lift-off)
  sweep_ext_on_{0137,0138}.ogg      slow 600->2100 rpm sweep at full load through the runtime mirror (ext/on row only)
  ab.json                           LUFS/peak per file
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

import el_demo as ed
import render_demo as rd
import runtime_sim as rs
from dsp import FS

OUT = ed.ROOT / "artifacts" / "audio-regen01" / "ab"
MAIN = Path(r"C:\Users\matma\Documents\Claude\kamion")


def sweep(man: dict, persp: str = "ext", load: float = 1.0, dur: float = 20.0) -> np.ndarray:
    rs.XFADE_COHERENCE = 0.0
    g = ed.load_grid_el(man, "engine", persp, 6)
    n = int(dur * FS)
    y = np.zeros(n)
    frame = int(FS / rs.FRAME_HZ)
    for i0 in range(0, n, frame):
        g.update(600 + 1500 * i0 / n, load, 1.0)
        y[i0:i0 + frame] = g.render(frame, FS)[: n - i0]
    return y


def write(path: Path, x: np.ndarray) -> dict:
    x = ed.finish(x)
    # block writes: one large Vorbis write overflows the stack in libsndfile on Windows
    with sf.SoundFile(path, "w", FS, 1, format="OGG", subtype="VORBIS") as fh:
        for i in range(0, len(x), 4096):
            fh.write(x[i:i + 4096].astype(np.float32))
    return {"file": path.name, "lufs": rd.integrated_lufs(x), "peak_dbfs": float(20 * np.log10(np.abs(x).max())),
            "dur_s": len(x) / FS, "bytes": path.stat().st_size}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--before", default=str(MAIN))
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    synth_man = rs.load_manifest()
    rep = {}
    for tag, root in (("0137", Path(a.before)), ("0138", ed.ROOT)):
        ed.CLIP_ROOT = root
        man = json.loads((root / ed.EL_MAN.relative_to(ed.ROOT)).read_text(encoding="utf-8"))
        for persp in ("ext", "cab"):
            x, _, _ = ed.render(synth_man, man, persp, True)
            x = x[int(1.5 * FS): int(31.5 * FS)]
            rep[f"drive_{persp}_{tag}"] = write(OUT / f"drive_{persp}_{tag}.ogg", x)
        rep[f"sweep_ext_on_{tag}"] = write(OUT / f"sweep_ext_on_{tag}.ogg", sweep(man))
        print(tag, {k: round(v["lufs"], 1) for k, v in rep.items() if k.endswith(tag)})
    (OUT / "ab.json").write_text(json.dumps(rep, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
