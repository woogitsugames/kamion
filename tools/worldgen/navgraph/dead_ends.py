"""ADR 0169: can the routing graph lead the truck into a dead end at the region edge? (read-only audit)

The 2 km tile cuts the one-way carriageways that leave it. Three kinds of parts outside the main strongly connected
component of the directed graph:
- off-reach (M27 flags in the file): cannot be driven to from the main part - the truck never gets there;
- entry-only: one-way entries from the tile edge - a start there routes into the main part, fine;
- NO-RETURN ("trap"): can be driven to from the main part, but no directed path leads back into it. The road ends
  at the closure 60 m before the tile edge (WorldEdgeBuilder), so a truck that passes the point of no return can
  only stop at the barrier: no junction, no U-turn on a one-way carriageway. The file does not flag these, so the
  destination pin may be set there and the planner routes onto them (after arrival every plan is NoPath).

CLI: uv run --project tools/worldgen python tools/worldgen/navgraph/dead_ends.py [--region bialystok-industrial-c]
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import build_route_graph as brg  # noqa: E402


def analyze(t: dict) -> dict:
    """t = build_route_graph.build(...) or .parse(bytes). Returns the report; "trap_edge_index" lists the edges."""
    n, edges = len(t["nodes"]), t["edges"]
    comps, _ = brg.strongly_connected_components(n, edges)
    fwd = [[] for _ in range(n)]
    bwd = [[] for _ in range(n)]
    for e in edges:
        fwd[e["from"]].append(e["to"])
        bwd[e["to"]].append(e["from"])
        if not e["flags"] & brg.F_ONEWAY:
            fwd[e["to"]].append(e["from"])
            bwd[e["from"]].append(e["to"])

    def closure(adj):
        seen = [False] * n
        stack = list(comps[0])
        for v in stack:
            seen[v] = True
        while stack:
            v = stack.pop()
            for w in adj[v]:
                if not seen[w]:
                    seen[w] = True
                    stack.append(w)
        return seen

    reach, back = closure(fwd), closure(bwd)
    trap = [reach[i] and not back[i] for i in range(n)]

    def ends_in_trap(e):
        return trap[e["to"]] if e["flags"] & brg.F_ONEWAY else (trap[e["from"]] and trap[e["to"]])

    idx = [i for i, e in enumerate(edges) if ends_in_trap(e)]
    by = collections.defaultdict(lambda: [0, 0.0])
    for i in idx:
        k = t["names"][edges[i]["name"]] or "(unnamed)"
        by[k][0] += 1
        by[k][1] += edges[i]["length"]
    gates = [edges[i] for i in idx if back[edges[i]["from"]]]   # first trap edge of a chain: from-node still has a way back
    return {
        "nodes": n, "edges": len(edges), "main_scc_nodes": len(comps[0]),
        "off_reach_nodes": sum(1 for r in reach if not r),
        "entry_only_nodes": sum(1 for i in range(n) if back[i] and not reach[i]),
        "trap_nodes": sum(trap),
        "trap_nodes_on_boundary": sum(1 for i in range(n) if trap[i] and t["nodes"][i][2] & 1),
        "trap_edges": len(idx),
        "trap_edges_length_m": round(sum(edges[i]["length"] for i in idx), 1),
        "trap_edges_two_way": sum(1 for i in idx if not edges[i]["flags"] & brg.F_ONEWAY),
        "trap_edges_flagged_off_reach": sum(1 for i in idx if edges[i]["flags"] & brg.F_OFF_REACH),
        "trap_by_street": {k: [v[0], round(v[1], 1)] for k, v in sorted(by.items(), key=lambda kv: -kv[1][1])},
        "points_of_no_return": sorted(
            ({"street": t["names"][e["name"]], "e": round(t["nodes"][e["from"]][0], 1), "n": round(t["nodes"][e["from"]][1], 1)}
             for e in gates), key=lambda g: (g["e"], g["n"])),
        "trap_edge_index": idx,
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--region", default="bialystok-industrial-c")
    a = ap.parse_args(argv)
    path = os.path.join(brg.REPO, "game", "Assets", "_Project", "UI", "Resources", "CabDisplay", "Nav", a.region + "_route.bytes")
    rep = analyze(brg.parse(open(path, "rb").read()))
    print(json.dumps(rep, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main())
