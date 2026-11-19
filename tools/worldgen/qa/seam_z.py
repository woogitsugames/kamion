"""ADR 0292: asphalt height step across the seam of two neighbour tiles, at every boundary node they share (any road
class), read off the built GLBs - the generic form of qa/s8_seam_z.py (S8 only).

    uv run --project tools/worldgen python tools/worldgen/qa/seam_z.py bialystok-porosly:dk8-s8-jeroniki [a:b ...]
        [--ways 223394828,889307875] [--json out.json] [--overrides]     # exit 1 when a measured |dz| > TOL_M

--overrides prints the authored_overrides entries (`target: {node}`, `set: {z: mean}`) for the nodes over TOL_M, one
block per tile (same node id in both graphs) - the fix of ADR 0288 s24 for decks / NMT series that differ per tile.
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
import s8_seam_z as S8Z  # noqa: E402

TOL_M = S8Z.TOL_M


def boundary(tile: str) -> dict[tuple[float, float], tuple[str, int, str]]:
    g = json.loads((ROOT / "Data/Regions" / tile / "roads.graph.json").read_text(encoding="utf-8"))
    ids = {n["id"]: n for n in g["nodes"]}
    out = {}
    for e in g["edges"]:
        for k in ("from", "to"):
            n = ids[e[k]]
            if n.get("boundary"):
                out[(round(n["x"], 2), round(n["y"], 2))] = (n["id"], int(e["osm_way"]), e["attrs"]["highway"]["v"])
    return out


def measure(ta: str, tb: str, ways: set[int] | None = None) -> list[dict]:
    na, nb = boundary(ta), boundary(tb)
    ba = yaml.safe_load((ROOT / "Data/Regions" / ta / "region.yaml").read_text(encoding="utf-8"))["bbox"]
    bb = yaml.safe_load((ROOT / "Data/Regions" / tb / "region.yaml").read_text(encoding="utf-8"))["bbox"]
    d = np.array([(bb["xmin"] + bb["xmax"] - ba["xmin"] - ba["xmax"]) / 2, (bb["ymin"] + bb["ymax"] - ba["ymin"] - ba["ymax"]) / 2])
    ax = np.array([np.sign(d[0]), 0.0]) if abs(d[0]) > abs(d[1]) else np.array([0.0, np.sign(d[1])])
    rows = []
    for xy, (nid, w, hw) in sorted(na.items()):
        if ways and w not in ways:
            continue
        m = next((v for k, v in nb.items() if abs(k[0] - xy[0]) < 0.05 and abs(k[1] - xy[1]) < 0.05), None)
        if m is None:
            continue
        za, zb = S8Z._z(ta, xy, -ax), S8Z._z(tb, xy, ax)
        dz = None if za is None or zb is None else round(zb - za, 3)
        rows.append({"a": ta, "b": tb, "osm_way": w, "highway": hw, "node_a": nid, "node_b": m[0], "xy": list(xy),
                     "z_a": None if za is None else round(za, 3), "z_b": None if zb is None else round(zb, 3), "dz": dz,
                     "ok": dz is None or abs(dz) <= TOL_M})
    return rows


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("pairs", nargs="+")
    ap.add_argument("--ways")
    ap.add_argument("--json")
    ap.add_argument("--overrides", action="store_true")
    a = ap.parse_args(argv)
    ways = {int(w) for w in a.ways.split(",")} if a.ways else None
    rows = []
    for p in a.pairs:
        ta, tb = p.split(":")
        rows += measure(ta, tb, ways)
    for r in rows:
        print(f"{r['a']} | {r['b']} way {r['osm_way']} {r['highway']} {tuple(r['xy'])}: {r['z_a']} / {r['z_b']} "
              f"dz {r['dz']} {'OK' if r['ok'] else 'FAIL'}")
    if a.overrides:
        for r in rows:
            if r["ok"]:
                continue
            zm = round((r["z_a"] + r["z_b"]) / 2, 2)
            for tile, node, own, other in ((r["a"], r["node_a"], r["z_a"], r["z_b"]), (r["b"], r["node_b"], r["z_b"], r["z_a"])):
                print(f"# {tile}\n  - id: seam-z-w{r['osm_way']}-{int(r['xy'][0])}-{int(r['xy'][1])}\n"
                      f"    target: {{node: \"{node}\"}}\n"
                      f"    reason: \"{r['highway']} way {r['osm_way']} at the {r['a']} | {r['b']} seam: {r['a']} {r['z_a']} m, "
                      f"{r['b']} {r['z_b']} m (GLB, tools/worldgen/qa/seam_z.py) -> mean in both tiles (ADR 0292)\"\n"
                      f"    confidence: \"medium (continuity across the seam; absolute height +-0.1 m)\"\n"
                      f"    verify: tools/worldgen/qa/seam_z.py {r['a']}:{r['b']} dz <= 0.1 m\n"
                      f"    set: {{z: {zm}}}")
    if a.json:
        Path(a.json).parent.mkdir(parents=True, exist_ok=True)
        Path(a.json).write_text(json.dumps(rows, indent=1), encoding="utf-8")
    return 0 if all(r["ok"] for r in rows) else 1


if __name__ == "__main__":
    sys.exit(main())
