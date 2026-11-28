"""Supports without conductors in every tile (ADR 0351, CRITIC s24 wave 11 # 1: lattice pylons with no wires).

Usage (repo root):
    uv run --project tools/worldgen python tools/worldgen/qa/hv_wires_audit.py [--json out.json] [--far-recompute]

In-tile (read-only on Data/Regions/<id>/generated/streetscape_sources.json, git): re-runs the support rule of
streetscape.furniture (points() for OSM power=tower / power=pole and BDOT10k OT_BUWT_P "slup energetyczny", then
plan_power_lines() for BDOT10k OT_SULN_L + OSM power=line|minor_line, no carriageway mask) and classifies bare
mapped supports into:
  - unwired:      a power line (BDOT10k or OSM) runs within SUPPORT_SNAP_M, yet no span (>= 5 m) ends on the support
  - without_line: no power line in BDOT10k or OSM runs within SUPPORT_SNAP_M (e.g. stork-nest pole, isolated node)

Far field (Data/Regions/<id>/generated/far_field_qa.json, git): `tiers.<tier>.power_lod` reports HV pylons and
spans after selection, separately for Low and High. Older QA reports lack this measurement.
`--far-recompute` re-extracts the ring GIS (Data/raw: BDOT10k, LoD1, OSM PBF) into this checkout's Data/raw/derived
cache and evaluates the ADR 0351 plan and selection without building meshes (slow on a cache miss).
"""
from __future__ import annotations

import argparse
import functools
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roads import pipeline                      # noqa: E402
from streetscape import furniture as FU         # noqa: E402
from streetscape import sources as SSRC         # noqa: E402

ADR0351 = "mapped_supports" in Path(FU.__file__).read_text(encoding="utf-8")   # same rule as the checked-out generator


def _origin(region_id: str) -> np.ndarray:
    import yaml
    r = yaml.safe_load((pipeline.REGIONS / region_id / "region.yaml").read_text(encoding="utf-8"))
    return np.array([float(r["origin"]["x"]), float(r["origin"]["y"])])


@functools.lru_cache(maxsize=1)
def _pbf_power_ways() -> dict[str, list[dict]]:
    """Read-only in-memory supplement of OSM power=line|minor_line ways for schema-v1 streetscape_sources.json."""
    try:
        from fetch_osm import download
        pbf = download()
    except Exception:
        return {}
    if not Path(pbf).exists():
        return {}
    bboxes = {}
    for d in sorted(pipeline.REGIONS.iterdir()):
        p = d / "generated" / "streetscape_sources.json"
        if p.exists() and (d / "region.yaml").exists():
            src = json.loads(p.read_text(encoding="utf-8"))
            if src.get("schema") == "truck-sim-pl/streetscape-sources/1":
                b = src["bbox"]
                bboxes[d.name] = (b[0], b[1], b[2], b[3])
    return SSRC.extract_osm_power_ways_by_bboxes(bboxes, pbf) if bboxes else {}


def _with_pbf_power_ways(region_id: str, src: dict) -> dict:
    if src.get("schema") != "truck-sim-pl/streetscape-sources/1":
        return src
    extra = _pbf_power_ways().get(region_id)
    if not extra:
        return src
    ways = [w for w in src.get("osm", {}).get("ways", [])
            if w.get("tags", {}).get("power") not in ("line", "minor_line")] + extra
    return {**src, "osm": {**src["osm"], "ways": ways}}


def in_tile(region_id: str | None = None, *, src: dict | None = None, origin=None,
            use_pbf: bool = True, osm_lines: bool = True) -> dict | None:
    if src is None:
        if region_id is None:
            raise ValueError("region_id or src is required")
        p = pipeline.REGIONS / region_id / "generated" / "streetscape_sources.json"
        if not p.exists():
            return None
        src = json.loads(p.read_text(encoding="utf-8"))
        if use_pbf:
            src = _with_pbf_power_ways(region_id, src)
    origin = np.asarray(_origin(region_id) if origin is None else origin, float)
    zero = lambda e, n: np.zeros_like(np.asarray(e, float))
    pl = FU.Placer(zero)
    plan_src = src if osm_lines else {**src, "osm": {**src.get("osm", {}), "ways": []}}
    FU.place_mapped_power_supports(pl, plan_src, origin)
    mapped = [dict(it) for it in pl.items]
    from shapely.geometry import Point
    hv_lines_geom, all_lines_geom, line_counts = FU.power_line_geoms(src, origin, pl)
    wired = set()
    for S, _hv, _sid in FU.plan_power_lines(plan_src, origin, pl):
        for a, b in zip(S, S[1:]):
            if float(np.hypot(*(b - a))) < 5:
                continue
            for q in (a, b):
                wired.add((round(float(q[0]), 2), round(float(q[1]), 2)))
    out = {**line_counts, "carriageway_mask": False}
    for proto in ("pylon", "power_pole"):
        items = [it for it in mapped if it["p"] == proto]
        bare = [it for it in items if (round(it["e"], 2), round(it["n"], 2)) not in wired]
        lines_for_proto = hv_lines_geom if proto == "pylon" else all_lines_geom
        snap_r = FU.SUPPORT_SNAP_M[proto]
        unwired, without_line = [], []
        for it in bare:
            pt = Point(it["e"], it["n"])
            if any(ln.distance(pt) <= snap_r for ln in lines_for_proto):
                unwired.append(it)
            else:
                without_line.append(it)
        out[proto] = {
            "mapped": len(items),
            "unwired": len(unwired),
            "without_line": len(without_line),
            "unwired_at": [[round(it["e"], 1), round(it["n"], 1), it["src"]] for it in unwired],
            "without_line_at": [[round(it["e"], 1), round(it["n"], 1), it["src"]] for it in without_line],
        }
    return out


def far_field(region_id: str, recompute: bool) -> dict | None:
    p = pipeline.REGIONS / region_id / "generated" / "far_field_qa.json"
    if not p.exists():
        return None
    qa = json.loads(p.read_text(encoding="utf-8"))
    out = {"plan": qa.get("power_plan"),
           "tiers": {tier: qa.get("tiers", {}).get(tier, {}).get("power_lod") for tier in ("Low", "High")}}
    if recompute:
        from streetscape import far_field as FF
        r = pipeline.load_region(region_id)
        half = float(r["bbox"]["width_m"]) / 2.0
        gis = FF.extract_ring_gis(region_id, float(r["origin"]["x"]), float(r["origin"]["y"]), half=half)
        plan = FF.power_plan(gis, half, region_id)
        out["plan"] = plan["stats"]
        out["tiers"] = {tier: FF.far_hv_lod_stats(*FF._select_far_hv(plan, half, tier))
                        for tier in ("Low", "High")}
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json")
    ap.add_argument("--far-recompute", action="store_true")
    ap.add_argument("--regions", nargs="*")
    a = ap.parse_args()
    regions = a.regions or sorted(d.name for d in pipeline.REGIONS.iterdir() if (d / "region.yaml").exists())
    rep, tot = {}, {"tile_pylons": 0, "tile_pylons_unwired": 0, "tile_pylons_without_line": 0,
                    "tile_poles": 0, "tile_poles_unwired": 0, "tile_poles_without_line": 0,
                    "far": {tier: {"tiles_measured": 0, "pylons": 0, "unwired_power_pylons": 0}
                            for tier in ("Low", "High")}}
    for rid in regions:
        t, f = in_tile(rid), far_field(rid, a.far_recompute)
        rep[rid] = {"tile": t, "far": f}
        if t:
            tot["tile_pylons"] += t["pylon"]["mapped"]
            tot["tile_pylons_unwired"] += t["pylon"]["unwired"]
            tot["tile_pylons_without_line"] += t["pylon"]["without_line"]
            tot["tile_poles"] += t["power_pole"]["mapped"]
            tot["tile_poles_unwired"] += t["power_pole"]["unwired"]
            tot["tile_poles_without_line"] += t["power_pole"]["without_line"]
        far_summary = []
        for tier, totals in tot["far"].items():
            stats = f["tiers"][tier] if f else None
            if stats is None:
                far_summary.append(f"{tier} -")
                continue
            totals["tiles_measured"] += 1
            totals["pylons"] += stats["pylons"]
            totals["unwired_power_pylons"] += stats["unwired_power_pylons"]
            far_summary.append(f"{tier} {stats['unwired_power_pylons']}/{stats['pylons']}")
        print(f"{rid:24s} tile pylons {t['pylon']['unwired'] if t else '-':>3}/{t['pylon']['mapped'] if t else '-':<3} "
              f"poles {t['power_pole']['unwired'] if t else '-':>3}/{t['power_pole']['mapped'] if t else '-':<3} "
              f"(no-line {t['power_pole']['without_line'] if t else '-':>2}) "
              "| far WN unwired " + ", ".join(far_summary))
    print("TOTAL", tot)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"total": tot, "regions": rep}, ensure_ascii=False, indent=1,
                                           sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
