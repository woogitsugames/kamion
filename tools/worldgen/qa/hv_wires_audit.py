"""Supports without conductors in every tile (ADR 0351, CRITIC s24 wave 11 # 1: lattice pylons with no wires).

Usage (repo root):
    uv run --project tools/worldgen python tools/worldgen/qa/hv_wires_audit.py [--json out.json] [--far-recompute]

In-tile (read-only on Data/Regions/<id>/generated/streetscape_sources.json, git): re-runs the support rule of
streetscape.furniture (points() for OSM power=tower / power=pole and BDOT10k OT_BUWT_P "slup energetyczny", then
power_supports() for every BDOT10k OT_SULN_L line, no carriageway mask) and counts mapped supports that no span
(>= 5 m) of any line ends on: they stand in the tile with no conductor.

Far field (Data/Regions/<id>/generated/far_field_qa.json, git): before ADR 0351 every far-field pylon was unwired
(feature_counts.pylons); after it the QA reports `power_plan` (pylons on HV spans, wired spans, unwired power pylons).
`--far-recompute` re-extracts the ring GIS (Data/raw: BDOT10k, LoD1, OSM PBF) into this checkout's Data/raw/derived
cache and evaluates the ADR 0351 plan for every tile without building meshes (slow: one OSM pass per tile).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from roads import pipeline                      # noqa: E402
from streetscape import furniture as FU         # noqa: E402

ADR0351 = "mapped_supports" in Path(FU.__file__).read_text(encoding="utf-8")   # same rule as the checked-out generator


def _origin(region_id: str) -> np.ndarray:
    import yaml
    r = yaml.safe_load((pipeline.REGIONS / region_id / "region.yaml").read_text(encoding="utf-8"))
    return np.array([float(r["origin"]["x"]), float(r["origin"]["y"])])


def in_tile(region_id: str) -> dict | None:
    p = pipeline.REGIONS / region_id / "generated" / "streetscape_sources.json"
    if not p.exists():
        return None
    src = json.loads(p.read_text(encoding="utf-8"))
    origin = _origin(region_id)
    zero = lambda e, n: np.zeros_like(np.asarray(e, float))
    pl = FU.Placer(zero)
    # mapped supports exactly as furniture.points() adds them (dedupe radii included)
    for nd in src["osm"]["nodes"]:
        t = nd["tags"]
        proto = {"tower": "pylon", "pole": "power_pole"}.get(t.get("power"))
        if not proto:
            continue
        q = np.asarray(nd["geometry"]["coordinates"], float) - origin
        if pl.near(proto, q, 3.0):
            continue
        pl.add(proto, q, 0.0, src=f"osm:node/{nd['osm_node']}", group=proto)
    from shapely.geometry import LineString, Point
    hv_lines = [LineString(np.asarray(f["geometry"]["coordinates"], float) - origin)
                for f in src["bdot10k"].get("OT_SULN_L", [])
                if "wysokiego" in (f["props"].get("rodzaj") or "") and len(f["geometry"]["coordinates"]) > 1]
    for f in src["bdot10k"].get("OT_BUWT_P", []):
        if f["props"].get("rodzaj") != "słup energetyczny":
            continue
        q = np.asarray(f["geometry"]["coordinates"], float) - origin
        if pl.near("power_pole", q, 4.0) or pl.near("pylon", q, 8.0):
            continue
        proto = "power_pole"
        if ADR0351 and any(ln.distance(Point(*q)) <= FU.SUPPORT_SNAP_M["pylon"] for ln in hv_lines):
            proto = "pylon"
        pl.add(proto, q, 0.0, src=f"bdot:{f['id']}", group=proto)
    mapped = [dict(it) for it in pl.items]
    wired = set()
    hv_lines = mv_lines = 0
    for f in src["bdot10k"].get("OT_SULN_L", []):
        hv = "wysokiego" in (f["props"].get("rodzaj") or "")
        hv_lines += hv
        mv_lines += not hv
        P = np.asarray(f["geometry"]["coordinates"], float) - origin
        if len(P) < 2:
            continue
        S = FU.power_supports(pl, P, hv, f["id"], None, {})
        for a, b in zip(S, S[1:]):
            if float(np.hypot(*(b - a))) < 5:
                continue
            for q in (a, b):
                wired.add((round(float(q[0]), 2), round(float(q[1]), 2)))
    out = {"hv_lines": hv_lines, "mv_lines": mv_lines}
    for proto in ("pylon", "power_pole"):
        items = [it for it in mapped if it["p"] == proto]
        bare = [it for it in items if (round(it["e"], 2), round(it["n"], 2)) not in wired]
        out[proto] = {"mapped": len(items), "unwired": len(bare),
                      "unwired_at": [[round(it["e"], 1), round(it["n"], 1), it["src"]] for it in bare]}
    return out


def far_field(region_id: str, recompute: bool) -> dict | None:
    p = pipeline.REGIONS / region_id / "generated" / "far_field_qa.json"
    if not p.exists():
        return None
    qa = json.loads(p.read_text(encoding="utf-8"))
    fc = qa["feature_counts"]
    plan = qa.get("power_plan")
    out = {"pylons_drawn": fc.get("pylons", 0),
           "unwired": plan["unwired_power_pylons"] + plan.get("masts", 0) if plan else fc.get("pylons", 0),
           "plan": plan}
    if recompute:
        from streetscape import far_field as FF
        import yaml
        r = yaml.safe_load((pipeline.REGIONS / region_id / "region.yaml").read_text(encoding="utf-8"))
        gis = FF.extract_ring_gis(region_id, float(r["origin"]["x"]), float(r["origin"]["y"]))
        out["recomputed"] = FF.power_plan(gis, region_id=region_id)["stats"]
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--json")
    ap.add_argument("--far-recompute", action="store_true")
    ap.add_argument("--regions", nargs="*")
    a = ap.parse_args()
    regions = a.regions or sorted(d.name for d in pipeline.REGIONS.iterdir() if (d / "region.yaml").exists())
    rep, tot = {}, {"tile_pylons": 0, "tile_pylons_unwired": 0, "tile_poles": 0, "tile_poles_unwired": 0,
                    "far_pylons_drawn": 0, "far_unwired": 0}
    for rid in regions:
        t, f = in_tile(rid), far_field(rid, a.far_recompute)
        rep[rid] = {"tile": t, "far": f}
        if t:
            tot["tile_pylons"] += t["pylon"]["mapped"]
            tot["tile_pylons_unwired"] += t["pylon"]["unwired"]
            tot["tile_poles"] += t["power_pole"]["mapped"]
            tot["tile_poles_unwired"] += t["power_pole"]["unwired"]
        if f:
            tot["far_pylons_drawn"] += f["pylons_drawn"]
            tot["far_unwired"] += f["unwired"]
        print(f"{rid:24s} tile pylons {t['pylon']['unwired'] if t else '-':>3}/{t['pylon']['mapped'] if t else '-':<3} "
              f"poles {t['power_pole']['unwired'] if t else '-':>3}/{t['power_pole']['mapped'] if t else '-':<4} "
              f"| far unwired {f['unwired'] if f else '-':>4}/{f['pylons_drawn'] if f else '-':<4}"
              + (f" | recomputed {f['recomputed']}" if f and 'recomputed' in f else ""))
    print("TOTAL", tot)
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps({"total": tot, "regions": rep}, ensure_ascii=False, indent=1,
                                           sort_keys=True) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
