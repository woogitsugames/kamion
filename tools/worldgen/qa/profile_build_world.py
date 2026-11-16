"""Stage profiler of roads/build_world.py (D22, docs/reports/WORLDGEN-PERF-2026-11-16.md). Analysis only: it changes no
generator module - it wraps a fixed list of generator functions with wall-clock timers (monkeypatched module
attributes, restored on exit) and optionally runs the whole build under cProfile.

    # real tile (lead machine, Data/raw present); writes the GLBs to a scratch out-root, not to Data/raw/derived
    uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c \
        --out-root artifacts/perf/c/world --prof artifacts/perf/c/bw_c.prof --json artifacts/perf/c/stages.json

    # cloud / CI without Data/raw: synthetic NMT (flat at origin.z, or a smooth 'wave' relief) instead of the r16
    uv run --project tools/worldgen python tools/worldgen/qa/profile_build_world.py --region bialystok-industrial-c \
        --nmt flat --skip-far-field --out-root <scratch>/world --prof <scratch>/bw.prof

CAUTION: build_world.build writes the QA JSONs to Data/Regions/<id>/generated/ (world_manifest.json, roads_qa.json,
streetscape_qa.json, landmarks/*.spec.json, ...) and the hero landmark assets to art-source/world/landmarks/ (git) -
with a synthetic NMT those files are WRONG. Run it in a throwaway worktree (or afterwards
`git checkout -- Data/Regions/<id>/generated art-source/world/landmarks`); the script refuses to run unless
--i-know-generated-is-dirtied is given. Measured in the cloud (C, no Data/raw / LFS): the hero assets are STALE there,
the far field is skipped, so the numbers are a lower bound of the lead build.

Output: a table of the wrapped stages (calls, total s, share of the build), sorted by total; nested stages are
counted in their parent too (pipeline.build contains assign_sides, build_ribbon, ...), so the shares do not add up.
Read the cProfile dump with:
    uv run --project tools/worldgen python -c "import pstats; pstats.Stats('bw_c.prof').sort_stats('cumulative').print_stats(40)"
    uv run --project tools/worldgen python -c "import pstats; pstats.Stats('bw_c.prof').sort_stats('tottime').print_stats(40)"
or as a flame graph: `uvx snakeviz bw_c.prof` (browser) / `uvx flameprof bw_c.prof > bw_c.svg`.
"""

from __future__ import annotations

import argparse
import cProfile
import functools
import importlib
import json
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

WG = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(WG))          # never tools/worldgen/roads: roads/profile.py would shadow the stdlib `profile`

# (module, attribute) - attribute may be "Class.method". Calls go through module attributes in the generator
# (pipeline.build, SS.run, CF.rasterise, M.build_ribbon ...), so patching the module attribute times every call.
STAGES = [
    ("roads.pipeline", "build"),
    ("roads.pipeline", "build_network"),
    ("roads.network", "assign_sides"),
    ("roads.junctions", "build_junctions"),
    ("roads.profile", "build_profiles"),
    ("roads.profile", "mark_walled_ramps"),
    ("roads.gores", "plan"),
    ("roads.gores", "build"),
    ("roads.gores", "drop_kerbs_in_fills"),
    ("roads.gores", "kerbs_in_fills"),
    ("roads.meshing", "build_ribbon"),
    ("roads.meshing", "build_patch"),
    ("roads.meshing", "build_median_fills"),
    ("roads.meshing", "cull_sides_on_carriageway"),
    ("roads.meshing", "build_bridge_supports"),
    ("roads.compact_roundabout", "build"),
    ("roads.markings", "build_markings"),
    ("roads.decals", "build"),
    ("roads.tunnels", "build"),
    ("roads.consistency", "check"),
    ("streetscape.cycleways", "plan"),
    ("streetscape.stage", "plan_plots"),
    ("streetscape.stage", "run"),
    ("streetscape.sources", "load"),
    ("streetscape.paved", "road_footprint_polygon"),
    ("streetscape.paved", "rasterize_polys"),
    ("streetscape.paved", "collect"),
    ("streetscape.paved", "paved_heights"),
    ("streetscape.plots", "region_plan"),
    ("streetscape.plots", "build"),
    ("streetscape.buildings_mesh", "load"),
    ("streetscape.buildings_mesh", "build"),
    ("streetscape.plots", "plan"),
    ("streetscape.plots", "layout"),
    ("streetscape.plots", "plan_access"),
    ("streetscape.plots", "gate_access"),
    ("streetscape.plots", "door_zones"),
    ("streetscape.plots", "paved_items"),
    ("streetscape.paved", "build_meshes"),
    ("streetscape.cycleways", "paint"),
    ("terrain_mesh.conform", "conform"),
    ("streetscape.furniture", "fences"),
    ("streetscape.furniture", "guardrails"),
    ("streetscape.furniture", "lamps"),
    ("streetscape.furniture", "power_lines"),
    ("streetscape.furniture", "junction_signs"),
    ("streetscape.furniture", "clear_carriageway"),
    ("streetscape.furniture", "pier_guardrails"),
    ("streetscape.vegetation", "place"),
    ("streetscape.vegetation", "ground_masks"),
    ("streetscape.forest_hlod", "build"),
    ("streetscape.plantings", "build"),
    ("streetscape.plantings", "front_gardens"),
    ("streetscape.plantings", "garden_trees"),
    ("streetscape.life", "place"),
    ("streetscape.hero_depot", "apply"),
    ("streetscape.signs_route", "osm_signs"),
    ("streetscape.hero_bridge", "plan"),
    ("streetscape.hero_bridge", "apply"),
    ("streetscape.pavements", "run"),
    ("streetscape.export", "export"),
    ("streetscape.far_field", "build_far_field"),
    ("terrain_mesh.conform", "rasterise"),
    ("terrain_mesh.conform", "clean_under_bridges"),
    ("terrain_mesh.conform", "tidy"),
    ("terrain_mesh.conform", "terrain_walls"),
    ("terrain_mesh.chunks", "build_chunks"),
    ("terrain_mesh.gltf", "GLB.add_mesh"),
    ("terrain_mesh.gltf", "GLB.bytes"),
    ("roads.build_world", "merge_verge_into_terrain"),
    ("roads.build_world", "assemble"),
    ("roads.build_world", "mesh_budget"),
    ("roads.build_world", "qa_report"),
    ("roads.build_world", "cameras"),
    ("roads.build_world", "write_json"),
    ("roads.build_world", "_src_tally"),
]

TIMES: dict[str, list] = {}


def _wrap(key, fn):
    @functools.wraps(fn)
    def inner(*a, **k):
        t = time.perf_counter()
        try:
            return fn(*a, **k)
        finally:
            rec = TIMES.setdefault(key, [0, 0.0])
            rec[0] += 1
            rec[1] += time.perf_counter() - t
    inner.__wrapped_stage__ = fn
    return inner


def install(stages):
    undo, missing = [], []
    for mod_name, attr in stages:
        try:
            mod = importlib.import_module(mod_name)
        except Exception as e:                   # noqa: BLE001 - a module may need optional deps; report and go on
            missing.append(f"{mod_name} ({type(e).__name__}: {e})")
            continue
        owner, name = mod, attr
        if "." in attr:
            cls, name = attr.split(".", 1)
            owner = getattr(mod, cls, None)
        fn = getattr(owner, name, None) if owner is not None else None
        if fn is None or not callable(fn):
            missing.append(f"{mod_name}.{attr}")
            continue
        key = f"{mod_name}.{attr}"
        setattr(owner, name, _wrap(key, fn))
        undo.append((owner, name, fn))
    # modules that did `from x import f` keep the original binding: build_world imports modules, not functions, so
    # only these aliases matter (sys.modules["roads.build_world"] vs "build_world" are the same file, two names)
    return undo, missing


def synthetic_nmt(kind):
    from roads import profile as P

    def load(terrain_meta, repo_root, origin):
        h, w = terrain_meta["samples"][1], terrain_meta["samples"][0]
        bb = terrain_meta["bbox"]
        z0 = float(terrain_meta.get("stats_m", {}).get("min", 130.0))
        if kind == "flat":
            z = np.full((h, w), z0)
        else:                                    # smooth relief of a few metres (exercises conform / walls / LoDs)
            jj, ii = np.mgrid[0:h, 0:w].astype(np.float64)
            z = z0 + 3.0 * np.sin(ii / 157.0) * np.cos(jj / 211.0) + 1.5 * np.sin((ii + jj) / 97.0)
        return P.Heightfield(z, bb, origin)
    P.load_heightfield = load


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", required=True)
    ap.add_argument("--out-root", required=True, help="GLB output directory (never Data/raw/derived/<id>/world)")
    ap.add_argument("--prof", help="write a cProfile dump here")
    ap.add_argument("--json", help="write the stage table here")
    ap.add_argument("--nmt", choices=("raw", "flat", "wave"), default="raw",
                    help="raw = Data/raw heightmap (lead); flat / wave = synthetic, no Data/raw needed")
    ap.add_argument("--skip-far-field", action="store_true", help="far field needs Data/raw (BDOT10k gpkg, OSM pbf)")
    ap.add_argument("--i-know-generated-is-dirtied", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(line_buffering=True)          # the build's own "[world t s]" lines stay in order with ours

    repo = WG.parents[1]
    gen = repo / "Data" / "Regions" / a.region / "generated"
    if not a.i_know_generated_is_dirtied:
        top = subprocess.run(["git", "-C", str(repo), "rev-parse", "--show-toplevel"], capture_output=True, text=True)
        print(f"refusing: build_world writes {gen} (tracked). Run in a throwaway worktree and pass "
              f"--i-know-generated-is-dirtied (checkout: {top.stdout.strip()})")
        return 2

    if a.nmt != "raw":
        synthetic_nmt(a.nmt)
    from roads import build_world as BW
    if a.skip_far_field:
        from streetscape import far_field as FF
        FF.build_far_field = lambda region_id, out_root=None: {"tiers": {}}
    undo, missing = install(STAGES)
    if missing:
        print("not wrapped:", ", ".join(missing), flush=True)

    out_root = Path(a.out_root).resolve()
    out_root.mkdir(parents=True, exist_ok=True)
    prof = cProfile.Profile() if a.prof else None
    t0 = time.perf_counter()
    err = None
    try:
        if prof:
            prof.enable()
        BW.build(a.region, out_root=out_root, verbose=True, route_graph=False)
    except Exception as e:                       # noqa: BLE001 - report the stages reached so far
        err = f"{type(e).__name__}: {e}"
        import traceback
        traceback.print_exc()
    finally:
        if prof:
            prof.disable()
        total = time.perf_counter() - t0
        for owner, name, fn in undo:
            setattr(owner, name, fn)
    if prof:
        Path(a.prof).parent.mkdir(parents=True, exist_ok=True)
        prof.dump_stats(a.prof)
    rows = sorted(({"stage": k, "calls": v[0], "total_s": round(v[1], 3), "share": round(v[1] / total, 4)}
                   for k, v in TIMES.items()), key=lambda r: -r["total_s"])
    print(f"\nbuild_world.build total {total:.1f} s (nmt={a.nmt}, far_field={'skipped' if a.skip_far_field else 'on'})"
          + (f"  FAILED: {err}" if err else ""))
    print(f"{'stage':55s} {'calls':>7s} {'total s':>9s} {'share':>6s}")
    for r in rows:
        print(f"{r['stage']:55s} {r['calls']:7d} {r['total_s']:9.2f} {100 * r['share']:5.1f}%")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"region": a.region, "nmt": a.nmt, "total_s": round(total, 2),
                                            "error": err, "stages": rows}, indent=1), encoding="utf-8")
    return 1 if err else 0


if __name__ == "__main__":
    sys.exit(main())
