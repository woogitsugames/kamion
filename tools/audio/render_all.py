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
import sfx_layers as sl
import sfx_synth as sx
from dsp import FS

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "art-source" / "audio" / "generated"
# ADR 0145: clip loudness (LUFS ext, cab) of the tyre slip layers, shared with the REGEN-03 recordings (el_fx.py)
TYRE_SLIP_LUFS = {"tyre_squeal_loop": (-16.0, -20.0), "tyre_scrub_loop": (-18.0, -22.0)}
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

    def write_sfx(name, x, is_loop, perspective="ext", group="base", cab_of=None):
        path = OUT / "sfx" / f"{name}.wav"
        path.parent.mkdir(parents=True, exist_ok=True)
        sf.write(path, x.astype(np.float32), FS, subtype="PCM_16")
        manifest["sfx"].append({"name": name, "file": str(path.relative_to(ROOT)).replace("\\", "/"),
                                "loop": is_loop, "samples": len(x), "peak_dbfs": dsp.db(np.max(np.abs(x))),
                                "rms_dbfs": dsp.db(dsp.rms(x)), "perspective": perspective, "group": group})

    def norm_peak(x, is_loop):
        target = -1.0 if not is_loop else -6.0
        return x * (10 ** (target / 20) / np.max(np.abs(x)))

    def limit(x, ceiling_db=-1.0):
        pk = np.max(np.abs(x))
        c = 10 ** (ceiling_db / 20)
        return x * (c / pk) if pk > c else x

    for name, (x, is_loop) in sfx.items():
        x = norm_peak(x, is_loop)
        write_sfx(name, x, is_loop)
        if not args.no_previews and name in ("turbo_whistle_loop", "air_brake_release", "parking_brake_set", "turbo_liftoff"):
            write_ogg(PREV / f"{name}.ogg", np.tile(x, 2) if is_loop else x)
        # cabin perspective of the original layers (prerendered filter, ADR 0012)
        cab_profile = {"air_brake_release": "pneu", "parking_brake_set": "pneu", "air_dryer_purge": "pneu",
                       "gearshift_air": "pneu", "road_roll_loop": "road", "wind_loop": "wind"}.get(name)
        if cab_profile:
            write_sfx(name.replace("_loop", "_cab_loop") if is_loop else name + "_cab", limit(sl.cab_filter(x, is_loop, cab_profile)), is_loop, "cab", "base")

    # --- layers added in the audio-layers pass (tyres x surface, squeal, retarder, compressor, relay, ambience) ---
    asphalt = sfx["road_roll_loop"][0]
    asphalt = norm_peak(asphalt, True)
    ref_rms = dsp.rms(asphalt)
    tyres = {
        "tyre_wet_loop": sl.tyre_asphalt_wet_loop(),
        "tyre_concrete_loop": sl.tyre_concrete_loop(),
        "tyre_cobbles_loop": sl.tyre_cobbles_loop(),
        "tyre_gravel_loop": sl.tyre_gravel_loop(),
        "tyre_grass_loop": sl.tyre_grass_loop(),
    }
    for name, x in tyres.items():
        x = limit(x * (ref_rms / dsp.rms(x)))  # equal RMS; per-surface level lives in the game's surface table
        write_sfx(name, x, True, "ext", "tyre")
        write_sfx(name.replace("_loop", "_cab_loop"), limit(sl.cab_filter(x, True, "road")), True, "cab", "tyre")
    # ADR 0145: squeal v2 (noise, no 930 Hz line) + tyre scrub (trailer axles dragged sideways in tight slow turns),
    # placeholders for the REGEN-03 recordings. Loudness-normalised (BS.1770) to the same clip LUFS as the recordings
    # (el_fx.REGEN03_SLOTS), so the runtime volumes mean the same in both sets.
    from el_analyze import lufs as _lufs
    for name, fn in (("tyre_squeal_loop", sl.tyre_squeal_loop), ("tyre_scrub_loop", sl.tyre_scrub_loop)):
        ext_l, cab_l = TYRE_SLIP_LUFS[name]
        x = fn()
        x = limit(x * 10 ** ((ext_l - _lufs(x, FS)) / 20))
        z = sl.cab_filter(x, True, "road")
        z = limit(z * 10 ** ((cab_l - _lufs(z, FS)) / 20))
        write_sfx(name, x, True, "ext", "tyre")
        write_sfx(name.replace("_loop", "_cab_loop"), z, True, "cab", "tyre")
    for name, fn, prof in (("retarder_loop", sl.retarder_loop, "mech"), ("compressor_loop", sl.compressor_loop, "mech"),
                           ("ambient_bed_loop", sl.ambient_industrial_bed_loop, "ambient"),
                           ("forklift_loop", sl.forklift_loop, "ambient")):
        x = norm_peak(fn(), True)
        grp = "ambient" if "ambient" in name or "forklift" in name else "mech"
        write_sfx(name, x, True, "ext", grp)
        write_sfx(name.replace("_loop", "_cab_loop"), limit(sl.cab_filter(x, True, prof)), True, "cab", grp)
    for name, fn, prof in (("parking_brake_release", sl.parking_brake_release, "pneu"), ("air_dryer_purge_b", sl.air_dryer_purge_b, "pneu"),
                           ("bird_sparrow", sl.bird_sparrow, None), ("bird_tit", sl.bird_tit, None),
                           ("bird_crow_caw", sl.bird_crow_caw, "ambient")):
        x = norm_peak(fn(), False)
        if name.startswith("bird"):
            x *= 10 ** (-3 / 20)
        grp = "ambient" if name.startswith("bird") else "pneumatics"
        write_sfx(name, x, False, "ext", grp)
        if prof:  # sparrow / tit: 3-5 kHz chirps are inaudible through closed glass -> exterior only
            write_sfx(name + "_cab", limit(sl.cab_filter(x, False, prof)), False, "cab", grp)
    for name, fn in (("indicator_tick", sl.indicator_tick), ("indicator_tock", sl.indicator_tock)):
        x = norm_peak(fn(), False)
        write_sfx(name + "_cab", limit(sl.cab_filter(x, False, "dash")), False, "cab", "relay")
        write_sfx(name, limit(sl.cab_filter(x, False, "relay_ext")), False, "ext", "relay")

    if not args.no_previews:
        for n_ in ("tyre_concrete_loop", "tyre_cobbles_loop", "tyre_squeal_loop", "retarder_loop", "compressor_loop"):
            x, _ = sf.read(OUT / "sfx" / f"{n_}.wav")
            write_ogg(PREV / f"{n_}.ogg", np.tile(x, 2))

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
