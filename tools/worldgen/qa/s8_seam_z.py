"""ADR 0288 (s24): height step of the S8 carriageways across the seams of the loop tiles, read off the built GLBs.

    uv run --project tools/worldgen python tools/worldgen/qa/s8_seam_z.py [--json out.json]   # exit 1 when > TOL_M

For every S8 boundary node shared by two neighbour tiles (same EPSG:2180 position in both graphs): asphalt height
(road + bridge deck nodes, highest triangle) 0.3 m inside each tile at the node and +-1 m across. The generator
solves heights per tile; a deck crossing a seam has no NMT height at the seam node (roads/profile.node_heights), so
both sides can disagree (s8-02 | s8-03, r10: 1.35 m / 0.79 m) - fixed with an authored node `z` in both tiles.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools" / "worldgen" / "qa"))
import seam_section as SS  # noqa: E402

TILES = ["dk65-01", "s8-01", "s8-02", "s8-03", "s8-04", "s8-05"]
TOL_M = 0.10
INSIDE_M = 0.3


def _s8_boundary(tile: str) -> list[tuple[float, float, int]]:
    g = json.loads((ROOT / "Data/Regions" / tile / "roads.graph.json").read_text(encoding="utf-8"))
    ids = {n["id"]: n for n in g["nodes"]}
    out = []
    for e in g["edges"]:
        a = e["attrs"]
        if a["highway"]["v"] != "motorway" or "S8" not in str((a.get("ref") or {}).get("v") or ""):
            continue
        for k in ("from", "to"):
            n = ids[e[k]]
            if n.get("boundary"):
                out.append((round(n["x"], 2), round(n["y"], 2), int(e["osm_way"])))
    return out


def _z(tile: str, xy, inward) -> float | None:
    r = yaml.safe_load((ROOT / "Data/Regions" / tile / "region.yaml").read_text(encoding="utf-8"))
    loc = np.asarray(xy, float) - np.array([r["origin"]["x"], r["origin"]["y"]]) + INSIDE_M * inward
    T = [v for k, v in list(SS.tris(ROOT, tile, "road", loc).items()) + list(SS.tris(ROOT, tile, "bridge", loc).items())
         if k.startswith("road_asphalt")]
    if not T:
        return None
    z = SS.locate(np.concatenate(T), loc[None, :])[0]
    return None if np.isnan(z) else float(z)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json")
    a = ap.parse_args()
    nodes = {t: _s8_boundary(t) for t in TILES}
    bbox = {t: yaml.safe_load((ROOT / "Data/Regions" / t / "region.yaml").read_text(encoding="utf-8"))["bbox"] for t in TILES}
    rows, bad = [], 0
    for i, ta in enumerate(TILES):
        for tb in TILES[i + 1:]:
            for x, y, w in nodes[ta]:
                if not any(abs(x - x2) < 0.05 and abs(y - y2) < 0.05 for x2, y2, _ in nodes[tb]):
                    continue
                ca = np.array([(bbox[ta]["xmin"] + bbox[ta]["xmax"]) / 2, (bbox[ta]["ymin"] + bbox[ta]["ymax"]) / 2])
                cb = np.array([(bbox[tb]["xmin"] + bbox[tb]["xmax"]) / 2, (bbox[tb]["ymin"] + bbox[tb]["ymax"]) / 2])
                d = cb - ca
                ax = np.array([np.sign(d[0]), 0.0]) if abs(d[0]) > abs(d[1]) else np.array([0.0, np.sign(d[1])])
                za, zb = _z(ta, (x, y), -ax), _z(tb, (x, y), ax)
                dz = None if za is None or zb is None else round(zb - za, 3)
                ok = dz is not None and abs(dz) <= TOL_M
                bad += 0 if ok else 1
                rows.append({"a": ta, "b": tb, "osm_way": w, "xy": [x, y], "z_a": za and round(za, 3),
                             "z_b": zb and round(zb, 3), "dz": dz, "ok": ok})
                print(f"{ta} | {tb} way {w} ({x}, {y}): {za} / {zb} dz {dz} {'OK' if ok else 'FAIL'}")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
