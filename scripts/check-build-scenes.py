#!/usr/bin/env python3
"""Pre-build check of the region scenes of a Windows build (build-hygiene-s23): which scenes `-Regions <spec>` will put
into the player, and which of them are missing in game/Assets/_Generated (not imported / imported before ADR 0235).

    python scripts/check-build-scenes.py                          # d67-full, this checkout
    python scripts/check-build-scenes.py --regions d67-full --require-tiles --require-high
    python scripts/check-build-scenes.py --log artifacts/logs/build-win-<ts>.log   # + compare with a finished build
    python scripts/check-build-scenes.py --project <other checkout>/game --json

Where the list comes from (nothing is typed by hand): EditorBuildSettings.asset holds only Boot, DrivingLab and WorldC
and is never changed; the region scenes are added in memory by Game.Editor.Build.RegionBuildList from the start-menu
catalog (game/Assets/_Project/Gameplay/Resources/Regions/region_catalog.json, sets d67 / d67-full written by
scripts/export-region-catalog.py). This script resolves the same spec with the same rules (package-windows.py
resolve_regions = RegionCatalog.Resolve) and applies RegionBuildList.ComposeScenes: per region the Low scene
(World_<id> / WorldC), its streamed tile scene World_<id>_Tile (ADR 0235, only when it exists) and with -worldHigh
(default of build-windows.ps1) the High scene + High tile.

Checks (exit 1 when one fails):
  - every region of the spec has its Low scene (else the build fails without -RegionsAllowMissing);
  - --require-tiles: every Low tile scene exists (streaming / Kamion-korytarz.cmd need them; WorldStreamer keeps a seam
    closed when the neighbour's tile scene is not in the build);
  - --require-high: every High scene exists (build-windows.ps1 only warns);
  - D86 (always with -worldHigh): no region whose Low tile scene exists without its High tile scene (one such tile
    makes PC streaming fall back to Low content, StreamingContentChoice.HighCoversLow; owner: dk65-03/04 enter the
    build only with their High content);
  - catalog coverage: every Data/Regions/<id> with route_start.json is in the catalog, and every catalog region is in
    the spec when the spec is d67-full (owner decision: the full build carries every region; ring tiles ADR 0231
    included once they are in the catalog);
  - --log: every expected scene that exists on disk is in the "[BUILD] Windows x64 ... scenes=[...]" line.
Standard library only.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
FULL_SET = "d67-full"


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parent / file)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


pw = _load("package_windows_cbs", "package-windows.py")   # resolve_regions, WORLD_ROOT, BUILD_LOG_SCENES_RE
pb = pw.postbuild


def scene_name(region: str, high: bool = False) -> str:
    """RegionScenes.SceneNameFor."""
    b = "WorldC" if region == "bialystok-industrial-c" else "World_" + region
    return b + "_High" if high else b


def scene_path(region: str, high: bool = False, tile: bool = False) -> str:
    """RegionScenes.ScenePathFor / TileScenePathFor (project-relative)."""
    return f"{pw.WORLD_ROOT}{region}/{scene_name(region, high)}{'_Tile' if tile else ''}.unity"


def region_rows(regions: list[str], exists) -> list[dict]:
    """Per region: path + exists for low / lowTile / high / highTile."""
    rows = []
    for r in regions:
        row = {"region": r}
        for key, high, tile in (("low", False, False), ("lowTile", False, True), ("high", True, False), ("highTile", True, True)):
            p = scene_path(r, high, tile)
            row[key] = {"path": p, "exists": bool(exists(p))}
        rows.append(row)
    return rows


def compose(rows: list[dict], with_high: bool = True) -> list[str]:
    """RegionBuildList.ComposeScenes for the region part (Low missing = region left out; tiles only when present)."""
    out: list[str] = []
    for row in rows:
        if not row["low"]["exists"]:
            continue
        out.append(row["low"]["path"])
        if row["lowTile"]["exists"]:
            out.append(row["lowTile"]["path"])
        if with_high and row["high"]["exists"]:
            out.append(row["high"]["path"])
            if row["highTile"]["exists"]:
                out.append(row["highTile"]["path"])
    return out


def catalog_problems(cat: dict, regions_dir: Path, spec_regions: list[str], spec: str) -> list[str]:
    ids = [r["id"] for r in cat.get("regions", [])]
    problems = []
    if regions_dir.is_dir():
        for p in sorted(regions_dir.iterdir()):
            if (p / "route_start.json").is_file() and p.name not in ids:
                problems.append(f"Data/Regions/{p.name} has route_start.json but is not in the catalog "
                                "(add it, then python scripts/export-region-catalog.py)")
    if spec.strip().lower() == FULL_SET:
        for i in ids:
            if i not in spec_regions:
                problems.append(f"catalog region {i} is not in set {FULL_SET} (scripts/export-region-catalog.py DERIVED_SETS)")
    return problems


def log_scenes(log_text: str) -> list[str]:
    hits = pw.BUILD_LOG_SCENES_RE.findall(log_text)
    if not hits:
        raise ValueError("no '[BUILD] Windows x64 ... scenes=[...]' line in the log")
    return [x.strip() for x in hits[-1].split(",") if x.strip()]


def check(spec: str, project: Path, catalog: Path, regions_dir: Path, require_tiles: bool, require_high: bool,
          with_high: bool = True, log_text: str | None = None) -> dict:
    cat = json.loads(catalog.read_text(encoding="utf-8-sig"))
    errors: list[str] = []
    regions = pw.resolve_regions(cat, spec, errors)
    rows = region_rows(regions, lambda p: (project / p).is_file())
    failures = [f"spec: {e}" for e in errors]
    failures += [f"{r['region']}: Low scene missing {r['low']['path']} (scripts/import-region.ps1 -Region {r['region']})"
                 for r in rows if not r["low"]["exists"]]
    if require_tiles:
        failures += [f"{r['region']}: tile scene missing {r['lowTile']['path']} (reimport, ADR 0235)"
                     for r in rows if r["low"]["exists"] and not r["lowTile"]["exists"]]
    if require_high:
        failures += [f"{r['region']}: High scene missing {r['high']['path']} (import-region.ps1 -Tiers Low,High)"
                     for r in rows if r["low"]["exists"] and not r["high"]["exists"]]
    if with_high:
        # D86 / StreamingContentChoice.HighCoversLow: one tile with a Low tile scene but no High one switches PC streaming
        # (tiers High / Ultra) to Low content for the whole graph - such a region must not go into the build.
        failures += [f"{r['region']}: D86 Low tile without High tile {r['highTile']['path']} - PC streaming would fall back "
                     "to Low; import -Tiers Low,High or leave the region out" for r in rows
                     if r["low"]["exists"] and r["lowTile"]["exists"] and not r["highTile"]["exists"]]
    failures += catalog_problems(cat, regions_dir, regions, spec)
    expected = compose(rows, with_high)
    result = {"spec": spec, "regions": regions, "rows": rows, "expectedRegionScenes": expected,
              "counts": {k: sum(1 for r in rows if r[k]["exists"]) for k in ("low", "lowTile", "high", "highTile")}}
    if log_text is not None:
        built = log_scenes(log_text)
        missing_in_log = [s for s in expected if s not in built]
        result["log"] = {"scenes": len(built), "missingInLog": missing_in_log,
                         "regionsInLog": pb.regions_from_log(log_text), "tileRegionsInLog": pb.tile_regions_from_log(log_text)}
        failures += [f"log: expected scene not in the build: {s}" for s in missing_in_log]
    result["failures"] = failures
    return result


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--regions", default=FULL_SET, help="spec as for build-windows.ps1 -Regions (default d67-full)")
    ap.add_argument("--project", type=Path, default=REPO / "game", help="Unity project folder (scenes under Assets/_Generated)")
    ap.add_argument("--catalog", type=Path, default=pw.REGION_CATALOG)
    ap.add_argument("--regions-dir", type=Path, default=REPO / "Data/Regions")
    ap.add_argument("--log", type=Path, help="finished build log to compare with")
    ap.add_argument("--require-tiles", action="store_true")
    ap.add_argument("--require-high", action="store_true")
    ap.add_argument("--no-high", action="store_true", help="build without -worldHigh (build-windows.ps1 -WorldLow)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    try:
        log_text = a.log.read_text(encoding="utf-8-sig", errors="replace") if a.log else None
        res = check(a.regions, a.project, a.catalog, a.regions_dir, a.require_tiles, a.require_high,
                    with_high=not a.no_high, log_text=log_text)
    except (OSError, ValueError) as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(res, indent=1))
    else:
        c = res["counts"]
        n = len(res["regions"])
        print(f"spec {res['spec']}: {n} regions; scenes on disk: Low {c['low']}/{n}, Low tile {c['lowTile']}/{n}, "
              f"High {c['high']}/{n}, High tile {c['highTile']}/{n}; region scenes in the build: {len(res['expectedRegionScenes'])}")
        for r in res["rows"]:
            flags = " ".join(f"{k}={'ok' if r[k]['exists'] else '--'}" for k in ("low", "lowTile", "high", "highTile"))
            print(f"  {r['region']:<24} {flags}")
        if "log" in res:
            print(f"log: {res['log']['scenes']} scenes, regions {len(res['log']['regionsInLog'])}, "
                  f"tile regions {len(res['log']['tileRegionsInLog'])}, missing in log {len(res['log']['missingInLog'])}")
        for f in res["failures"]:
            print("FAIL " + f)
        print("OK" if not res["failures"] else f"{len(res['failures'])} problem(s)")
    return 1 if res["failures"] else 0


if __name__ == "__main__":
    sys.exit(main())
