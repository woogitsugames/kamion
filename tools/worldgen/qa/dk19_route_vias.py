"""Via points of the control routes of ADR 0278 tiles 5-7 (owner D81) so that export-route.py / build_world follow the
truck route (DK19 Piastowska - pl. Antonowicza - Branickiego - rondo Meyera - Ciolkowskiego) and not the plain shortest
path of the tile.

Truck path on the graph NODES of the three tiles + Dojlidy (edge level, oneway respected; edges with hgv=no or
maxweight < 40 and service roads left out; cost x1 with ref, x2 trunk/primary without ref, x4 others - the weights of
map_plan_0278.corridor_route) from the Andersa seam with C to the Ciolkowskiego seam with Dojlidy. Per tile: start =
first node, end = last node, via = a path node about every VIA_STEP_M. Writes start/via/end into route_endpoints.json
(--write) and prints the street sequence.

  uv run --project tools/worldgen python tools/worldgen/qa/dk19_route_vias.py [--write]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import regions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
TILES = ("bialystok-wygoda", "bialystok-bojary", "bialystok-mickiewicza")
START = (779019.0, 595242.45)      # Andersa southbound on the seam with C (way 560802662)
END = (779092.4, 591103.0)         # Ciolkowskiego southbound on the seam with Dojlidy (way 279881972)
VIA_STEP_M = 300.0


def blocked(a) -> bool:
    if a.get("hgv") in ("no", "destination", "delivery") or a.get("highway") == "service":
        return True
    try:
        return float(str(a.get("maxweight", "99")).split()[0]) < 40
    except ValueError:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--write", action="store_true")
    a = ap.parse_args()
    g = nx.DiGraph()
    xy = {}
    for rid in TILES:
        G = json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))
        for n in G["nodes"]:
            xy[(round(n["x"], 2), round(n["y"], 2))] = (n["x"], n["y"])
        pos = {n["id"]: (round(n["x"], 2), round(n["y"], 2)) for n in G["nodes"]}
        for e in G["edges"]:
            at = {k: d.get("v") for k, d in e["attrs"].items()}
            if blocked(at):
                continue
            f = 1.0 if at.get("ref") else 2.0 if str(at.get("highway", "")).split("_")[0] in ("motorway", "trunk", "primary") else 4.0
            u, v, ow = pos[e["from"]], pos[e["to"]], at.get("oneway")
            kw = dict(d=e["length_m"], w=e["length_m"] * f, tile=rid, name=at.get("name") or f"(way {e['osm_way']})")
            if ow in ("yes", "no"):
                g.add_edge(u, v, **kw)
            if ow in ("-1", "no"):
                g.add_edge(v, u, **kw)
    s = min(g.nodes, key=lambda n: (n[0] - START[0]) ** 2 + (n[1] - START[1]) ** 2)
    t = min(g.nodes, key=lambda n: (n[0] - END[0]) ** 2 + (n[1] - END[1]) ** 2)
    path = nx.shortest_path(g, s, t, weight="w")
    per: dict[str, list] = {rid: [] for rid in TILES}
    names: dict[str, list] = {rid: [] for rid in TILES}
    for u, v in zip(path, path[1:]):
        ed = g[u][v]
        rid = ed["tile"]
        if not per[rid]:
            per[rid].append((u, 0.0))
        per[rid].append((v, per[rid][-1][1] + ed["d"]))
        if not names[rid] or names[rid][-1][0] != ed["name"]:
            names[rid].append([ed["name"], 0.0])
        names[rid][-1][1] += ed["d"]
    for rid in TILES:
        pts = per[rid]
        total = pts[-1][1]
        via, nxt = [], VIA_STEP_M
        for p, d in pts[1:-1]:
            if d >= nxt and total - d > 60.0:
                via.append([p[0], p[1]])
                nxt = d + VIA_STEP_M
        print(f"{rid}: {total:.1f} m, {len(via)} via, " + " > ".join(f"{n} {m:.0f}" for n, m in names[rid]))
        if a.write:
            f = REPO / "Data" / "Regions" / rid / "route_endpoints.json"
            j = json.loads(f.read_text(encoding="utf-8"))
            j["start_epsg2180"], j["end_epsg2180"] = [pts[0][0][0], pts[0][0][1]], [pts[-1][0][0], pts[-1][0][1]]
            if via:
                j["via_epsg2180"] = via
                j["via_note"] = ("graph nodes of the truck route about every 300 m (tools/worldgen/qa/dk19_route_vias.py): the plain "
                                 "shortest path of the tile leaves DK19")
            j["length_truck_route_m"] = round(total, 1)
            f.write_text(json.dumps(j, indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    assert regions.get(TILES[0]) is not None


if __name__ == "__main__":
    main()
