"""Truck-route checks of ADR 0278 tiles 5-7 (owner D81) on the built road graphs (roads.graph.json, pinned OSM pbf).

1. Restrictions in the graph: edges with hgv / maxweight / maxspeed:hgv:conditional attributes on the named streets.
2. Named places: rondo Meyera, pl. Antonowicza, Piastowska (centroid and tile of the edges carrying the name).
3. Route C -> Dojlidy over the union of the graphs of wygoda, bojary, mickiewicza and dojlidy (oneway respected; edges
   with hgv=no or maxweight < 40 left out): from the Andersa seam with C to the route of Dojlidy (route_start.json),
   length per tile, street names in order, and whether it stays inside the built tiles.

  uv run --project tools/worldgen python tools/worldgen/qa/dk19_route_check.py [--json out.json]
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import networkx as nx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import regions  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
TILES = ("bialystok-wygoda", "bialystok-bojary", "bialystok-mickiewicza", "bialystok-dojlidy")
STREETS = ("Nowowarszawska", "Jana Klemensa Branickiego", "Piastowska", "Plac Antonowicza", "Konstantego Ciołkowskiego",
           "Generała Stanisława Sosabowskiego", "Generała Władysława Andersa", "Rondo Meyera", "Dywizjonu 303")
RESTR = ("hgv", "maxweight", "maxweight:hgv", "maxgvweightrating:hgv", "maxspeed:hgv:conditional", "maxaxleload",
         "hgv:conditional", "maxweight:conditional")


def load(rid):
    return json.loads((REPO / "Data" / "Regions" / rid / "roads.graph.json").read_text(encoding="utf-8"))


def attrs(e):
    return {k: d.get("v") for k, d in e["attrs"].items()}


def tile_of(x, y):
    for rid in TILES:
        b = regions.get(rid).bbox
        if b[0] <= x <= b[2] and b[1] <= y <= b[3]:
            return rid
    return None


def blocked(a) -> bool:
    if a.get("hgv") in ("no", "destination", "delivery"):
        return True
    try:
        return float(str(a.get("maxweight", "99")).split()[0]) < 40
    except ValueError:
        return False


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", type=Path)
    a = ap.parse_args()
    out = {"restrictions": {}, "places": {}, "route": {}}
    g = nx.DiGraph()
    key = lambda p: (round(p[0], 2), round(p[1], 2))
    allkeys = set()
    for rid in TILES:
        G = load(rid)
        for e in G["edges"]:
            at = attrs(e)
            allkeys |= set(at)
            nm = at.get("name")
            r = {k: at[k] for k in RESTR if k in at}
            if nm in STREETS:
                d = out["restrictions"].setdefault(nm, {})
                k = json.dumps(r, ensure_ascii=False, sort_keys=True)
                d.setdefault(k, {"edges": 0, "length_m": 0.0, "tiles": set(), "ways": set()})
                d[k]["edges"] += 1
                d[k]["length_m"] += e["length_m"]
                d[k]["tiles"].add(rid)
                d[k]["ways"].add(e["osm_way"])
            if nm and (at.get("junction") == "roundabout" or nm in ("Plac Antonowicza", "Piastowska")) and rid != "bialystok-dojlidy":
                p = out["places"].setdefault(nm if at.get("junction") != "roundabout" else f"rondo: {nm}", {"pts": [], "tiles": set()})
                p["pts"] += e["geometry"]
                p["tiles"].add(rid)
            if at.get("highway") in ("service", "footway", "cycleway", "path", "track", "pedestrian", "steps") or blocked(at):
                continue
            co = [key(q) for q in e["geometry"]]
            one = at.get("oneway")
            f = 1.0 if at.get("ref") else 2.0 if str(at.get("highway", "")).split("_")[0] in ("motorway", "trunk", "primary") else 4.0
            for u, v in zip(co, co[1:]):
                d = math.dist(u, v)
                if one != "-1":
                    g.add_edge(u, v, d=d, w=d * f, name=nm, way=e["osm_way"], ref=at.get("ref"))
                if one in ("no", None, "-1", False):
                    g.add_edge(v, u, d=d, w=d * f, name=nm, way=e["osm_way"], ref=at.get("ref"))
    out["attr_keys_restriction_like"] = sorted(k for k in allkeys if any(s in k for s in ("hgv", "weight", "axle", "conditional")))
    for nm, d in out["restrictions"].items():
        for k, v in d.items():
            v["tiles"], v["ways"], v["length_m"] = sorted(v["tiles"]), len(v["ways"]), round(v["length_m"], 1)
    for nm, p in out["places"].items():
        xs, ys = [q[0] for q in p["pts"]], [q[1] for q in p["pts"]]
        p["centroid"] = [round(sum(xs) / len(xs), 1), round(sum(ys) / len(ys), 1)]
        p["extent"] = [round(min(xs), 1), round(min(ys), 1), round(max(xs), 1), round(max(ys), 1)]
        p["tiles"] = sorted(p["tiles"])
        del p["pts"]
    # route: Andersa southbound carriageway at the C seam -> the first point of the Dojlidy route
    rs = json.loads((REPO / "Data/Regions/bialystok-dojlidy/route_start.json").read_text(encoding="utf-8"))
    out["route"]["dojlidy_route_start_keys"] = sorted(rs.keys())
    start_c = [n for n in g.nodes if abs(n[0] - 779019.0) < 0.05 and 595199 <= n[1] <= 595300]
    end_n = [n for n in g.nodes if abs(n[1] - 591103.0) < 0.05 and 779019 <= n[0] <= 779200]
    out["route"]["start_candidates"], out["route"]["dojlidy_n_seam_nodes"] = start_c, end_n
    best = None
    for s in start_c:
        for t in end_n:
            try:
                c, p = nx.single_source_dijkstra(g, s, t, weight="w")
            except nx.NetworkXNoPath:
                continue
            if best is None or c < best[0]:
                best = (c, p)
    if best:
        p = best[1]
        per, names = {}, []
        for u, v in zip(p, p[1:]):
            t = tile_of((u[0] + v[0]) / 2, (u[1] + v[1]) / 2)
            per[t] = per.get(t, 0.0) + g[u][v]["d"]
            n = g[u][v]["name"] or f"(way {g[u][v]['way']})"
            if not names or names[-1][0] != n:
                names.append([n, 0.0, g[u][v]["ref"]])
            names[-1][1] += g[u][v]["d"]
        out["route"]["to_dojlidy_n_seam"] = {"length_m": round(sum(per.values()), 1), "per_tile_m": {k: round(v, 1) for k, v in per.items()},
                                             "streets": [[n, round(m, 1), r] for n, m, r in names],
                                             "start": p[0], "end": p[-1]}
        # onward inside Dojlidy: how far can a truck go from the N seam without leaving the tile
        reach = nx.single_source_dijkstra_path_length(g, p[-1], weight="d")
        b = regions.get("bialystok-dojlidy").bbox
        inside = {n: d for n, d in reach.items() if b[0] <= n[0] <= b[2] and b[1] <= n[1] <= b[3]}
        out["route"]["dojlidy_reachable_nodes_from_n_seam"] = len(inside)
        out["route"]["dojlidy_graph_nodes_total"] = sum(1 for n in g.nodes if b[0] <= n[0] <= b[2] and b[1] <= n[1] <= b[3])
    else:
        out["route"]["to_dojlidy_n_seam"] = None
    txt = json.dumps(out, indent=1, ensure_ascii=False, default=list)
    print(txt)
    if a.json:
        a.json.parent.mkdir(parents=True, exist_ok=True)
        a.json.write_text(txt + "\n", encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
