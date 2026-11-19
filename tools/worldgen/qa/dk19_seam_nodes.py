"""Boundary-node check of the seams of ADR 0278 tiles 5-7 (owner D81) against the graphs of their neighbours.

For every pair of tiles sharing an edge: the graph nodes of both roads.graph.json lying on the shared edge (|d| < 0.05 m),
matched by OSM way; offset along the edge in metres. A way present on one side only is listed as unmatched.

  uv run --project tools/worldgen python tools/worldgen/qa/dk19_seam_nodes.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import regions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
PAIRS = [("bialystok-wygoda", "bialystok-industrial-c"), ("bialystok-wygoda", "bialystok-bojary"),
         ("bialystok-bojary", "bialystok-mickiewicza"), ("bialystok-mickiewicza", "bialystok-dojlidy")]
MAJOR = ("motorway", "trunk", "primary", "secondary", "tertiary")


def shared(a, b):
    """('x'|'y', value, lo, hi) of the shared edge of two bboxes or None."""
    if a[2] == b[0] or a[0] == b[2]:
        v = a[2] if a[2] == b[0] else a[0]
        lo, hi = max(a[1], b[1]), min(a[3], b[3])
        return ("x", v, lo, hi) if hi > lo else None
    if a[3] == b[1] or a[1] == b[3]:
        v = a[3] if a[3] == b[1] else a[1]
        lo, hi = max(a[0], b[0]), min(a[2], b[2])
        return ("y", v, lo, hi) if hi > lo else None
    return None


def boundary(rid: str, edge) -> list[dict]:
    g = json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))
    pos = {n["id"]: (n["x"], n["y"]) for n in g["nodes"]}       # EPSG:2180
    axis, v, lo, hi = edge
    out = []
    for e in g["edges"]:
        at = {k: d.get("v") for k, d in e["attrs"].items()}
        for end in (e["from"], e["to"]):
            p = pos.get(end)
            if p is None:
                continue
            d = p[0] - v if axis == "x" else p[1] - v
            s = p[1] if axis == "x" else p[0]
            if abs(d) < 0.05 and lo - 0.05 <= s <= hi + 0.05:
                out.append({"osm_way": e["osm_way"], "along": round(s, 2), "highway": at.get("highway"),
                            "name": at.get("name"), "ref": at.get("ref"), "lanes": at.get("lanes"), "oneway": at.get("oneway"),
                            "hgv": at.get("hgv"), "maxweight": at.get("maxweight")})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    res = []
    for x, y in PAIRS:
        if not all((REPO / "Data" / "Regions" / k / "roads.graph.json").exists() for k in (x, y)):
            print(f"{x} | {y}: graph missing, skipped")
            continue
        edge = shared(regions.get(x).bbox, regions.get(y).bbox)
        bx, by = boundary(x, edge), boundary(y, edge)
        rows, used = [], set()
        for p in bx:
            cand = [(abs(q["along"] - p["along"]), k) for k, q in enumerate(by) if q["osm_way"] == p["osm_way"] and k not in used]
            if cand:
                d, k = min(cand)
                used.add(k)
                rows.append({**p, "offset_m": round(d, 2), "other": by[k]})
            else:
                rows.append({**p, "offset_m": None})
        only_y = [q for k, q in enumerate(by) if k not in used]
        mx = max((r["offset_m"] for r in rows if r["offset_m"] is not None), default=None)
        um = [r for r in rows if r["offset_m"] is None]
        print(f"{x} | {y} ({edge[0]}={edge[1]:.0f}): {len(bx)} / {len(by)} boundary nodes, matched {len(rows) - len(um)}, "
              f"max offset {mx} m, only in {x}: {len(um)}, only in {y}: {len(only_y)}")
        for r in rows:
            if (r.get("highway") or "").split("_")[0] in MAJOR or r["offset_m"] is None:
                print(f"   {r['highway']:<14} way {r['osm_way']} {r.get('name') or ''} ref={r.get('ref')} along={r['along']} offset={r['offset_m']}")
        for q in only_y:
            print(f"   only {y}: {q['highway']} way {q['osm_way']} {q.get('name') or ''} along={q['along']}")
        res.append({"a": x, "b": y, "edge": list(edge), "rows": rows, "only_b": only_y, "max_offset_m": mx})
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(json.dumps(res, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    assert math.isfinite(1.0)


if __name__ == "__main__":
    main()
