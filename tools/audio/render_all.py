"""Render the full procedural engine/SFX bank.

    uv run python render_all.py            # full bank -> art-source/audio/generated/ (gitignored)
    uv run python render_all.py --quick    # coarse grid for iteration

Outputs 48 kHz mono 16-bit WAV + ``manifest.json`` (grid, exact loop rpm, cycles, levels)
and small OGG previews in ``art-source/audio/previews/`` (committed).
"""

from __future__ import annotations

import argparse
import json
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import soundfile as sf

import dsp
import engine_synth as es
import sfx_synth as sx
from dsp import FS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "art-source" / "audio" / "generated"
PREV = ROOT / "art-source" / "audio" / "previews"

RPM_GRID = list(range(600, 2101, 100))
LOAD_LAYERS = {"off": 0.0, "mid": 0.4, "on": 1.0}
EBRAKE_GRID = list(range(900, 2101, 100))
PERSPECTIVES = ("ext", "cab")
ENGINE_PEAK_DBFS = -3.0   # common gain for the whole engine set (relative levels preserved)


def _job(args):
    kind, rpm, layer, load = args
    loops, geo = es.render_loop(rpm, load, engine_brake=(kind == "ebrake"))
    return kind, rpm, layer, loops, geo


def clip_name(kind: str, persp: str, rpm: int, layer: str | None) -> str:
    if kind == "ebrake":
        return f"ebrake_{persp}_{rpm:04d}"
    return f"engine_{persp}_{layer}_{rpm:04d}"


def write_ogg(path: Path, x: np.ndarray, quality: float = 0.45) -> None:
    dsp.write_ogg(path, x, compression_level=1.0 - quality)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--quick", action="store_true")
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--no-previews", action="store_true",
                    help="do not rewrite the committed OGG previews (build scripts: keeps the git tree clean)")
    args = ap.parse_args()

    rpm_grid = RPM_GRID[::3] if args.quick else RPM_GRID
    eb_grid = EBRAKE_GRID[::3] if args.quick else EBRAKE_GRID
    jobs = [("engine", r, name, ld) for name, ld in LOAD_LAYERS.items() for r in rpm_grid]
    jobs += [("ebrake", r, None, 0.0) for r in eb_grid]

    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as ex:
        results = list(ex.map(_job, jobs))
    print(f"rendered {len(results)} operating points in {time.time() - t0:.1f}s")

    # common normalisation per perspective (engine + ebrake share one gain)
    gains = {}
    for p in PERSPECTIVES:
        pk = max(np.max(np.abs(r[3][p])) for r in results)
        gains[p] = 10 ** (ENGINE_PEAK_DBFS / 20) / pk

    manifest = {
        "sample_rate": FS,
        "generator": "tools/audio/render_all.py (procedural synthesis, no recordings)",
        "rpm_grid": rpm_grid,
        "load_layers": LOAD_LAYERS,
        "ebrake_rpm_grid": eb_grid,
        "perspectives": list(PERSPECTIVES),
        "engine_gain_db": {p: dsp.db(g) for p, g in gains.items()},
        "clips": [],
    }
    for kind, rpm, layer, loops, geo in results:
        for p in PERSPECTIVES:
            x = loops[p] * gains[p]
            name = clip_name(kind, p, rpm, layer)
            sub = "engine" if kind == "engine" else "ebrake"
            path = OUT / sub / p / f"{name}.wav"
            path.parent.mkdir(parents=True, exist_ok=True)
            sf.write(path, x.astype(np.float32), FS, subtype="PCM_16")
            manifest["clips"].append({
                "name": name, "file": str(path.relative_to(ROOT)).replace("\\", "/"), "kind": kind,
                "perspective": p, "rpm": rpm, "layer": layer, "load": LOAD_LAYERS.get(layer, 0.0) if layer else 0.0,
                "rpm_exact": geo.rpm_exact, "cycles": geo.n_cycles, "samples": geo.n_samples,
                "peak_dbfs": dsp.db(np.max(np.abs(x))), "rms_dbfs": dsp.db(dsp.rms(x)),
            })

    # --- SFX ---
    sfx = {
        "turbo_whistle_loop": (sx.turbo_whistle_loop(), True),
        "road_roll_loop": (sx.road_roll_loop(), True),
        "wind_loop": (sx.wind_loop(), True),
        "gear_whine_loop": (sx.gear_whine_loop(), True),
        "air_brake_release": (sx.air_brake_release(), False),
        "parking_brake_set": (sx.parking_brake_set(), False),
        "air_dryer_purge": (sx.air_dryer_purge(), False),
        "gearshift_air": (sx.gearshift_air(), False),
        "turbo_liftoff": (sx.turbo_liftoff(), False),
    }
    manifest["sfx"] = []
    for name, (x, is_loop) in sfx.items():
        target = -1.0 if not is_loop else -6.0
        x = x * (10 ** (target / 20) / np.max(np.abs(x)))
        path = OUT / "sfx" / f"{name}.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(path, x.astype(np.float32), FS, subtype="PCM_16")
        manifest["sfx"].append({"name": name, "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                                "loop": is_loop, "samples": len(x), "peak_dbfs": dsp.db(np.max(np.abs(x))),
                                "rms_dbfs": dsp.db(dsp.rms(x))})
        if not args.no_previews and name in ("turbo_whistle_loop", "air_brake_release", "parking_brake_set", "turbo_liftoff"):
            write_ogg(PREV / f"{name}.ogg", np.tile(x, 2) if is_loop else x)

    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")

    # --- previews: each loop played twice back-to-back (demonstrates the seamless seam) ---
    if not args.quick and not args.no_previews:
        want = [("engine", "ext", 600, "mid"), ("engine", "ext", 1300, "on"), ("engine", "ext", 2100, "on"),
                ("engine", "ext", 1300, "off"), ("engine", "cab", 1300, "mid"), ("engine", "cab", 600, "mid"),
                ("ebrake", "ext", 1800, None), ("ebrake", "cab", 1800, None)]
        for kind, p, rpm, layer in want:
            name = clip_name(kind, p, rpm, layer)
            sub = "engine" if kind == "engine" else "ebrake"
            x, _ = sf.read(OUT / sub / p / f"{name}.wav")
            write_ogg(PREV / f"{name}_x2.ogg", np.tile(x, 2))
    print(f"done in {time.time() - t0:.1f}s; gains {manifest['engine_gain_db']}")


if __name__ == "__main__":
    main()
