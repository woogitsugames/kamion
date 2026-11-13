"""ADR 0169: can the route graph lead the truck into a dead end at the region edge?
Reads the committed route .bytes. "Trap" node = can be driven to from the main strongly connected component but has
no directed way back into it (outbound one-way carriageways cut by the tile edge). Trap edge = an edge that ends in
a trap node. Usage: uv run --project tools/worldgen python artifacts/edge-0169/route_dead_ends.py"""
import json, sys, collections
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from navgraph import build_route_graph as B

t = B.parse((REPO / "game/Assets/_Project/UI/Resources/CabDisplay/Nav/bialystok-industrial-c_route.bytes").read_bytes())
n = len(t["nodes"]); E = t["edges"]
comps, comp = B.strongly_connected_components(n, E)
fwd = [[] for _ in range(n)]; bwd = [[] for _ in range(n)]
for e in E:
    fwd[e["from"]].append(e["to"]); bwd[e["to"]].append(e["from"])
    if not e["flags"] & B.F_ONEWAY:
        fwd[e["to"]].append(e["from"]); bwd[e["from"]].append(e["to"])
def closure(adj):
    seen = [False] * n; st = list(comps[0])
    for v in st: seen[v] = True
    while st:
        v = st.pop()
        for w in adj[v]:
            if not seen[w]: seen[w] = True; st.append(w)
    return seen
reach, back = closure(fwd), closure(bwd)
trap = [reach[i] and not back[i] for i in range(n)]
src = [back[i] and not reach[i] for i in range(n)]
def ends_in_trap(e):
    return trap[e["to"]] if e["flags"] & B.F_ONEWAY else (trap[e["from"]] and trap[e["to"]])
te = [e for e in E if ends_in_trap(e)]
off = [e for e in E if e["flags"] & B.F_OFF_REACH]
by = collections.defaultdict(lambda: [0, 0.0])
for e in te:
    k = t["names"][e["name"]] or "(bez nazwy)"; by[k][0] += 1; by[k][1] += e["length"]
rep = {
    "nodes": n, "edges": len(E), "main_scc_nodes": len(comps[0]),
    "off_reach_edges": len(off), "off_reach_nodes": sum(1 for i in range(n) if not reach[i]),
    "entry_only_nodes (can reach main, not reachable from it)": sum(src),
    "trap_nodes": sum(trap), "trap_nodes_boundary": sum(1 for i in range(n) if trap[i] and t["nodes"][i][2] & 1),
    "trap_edges": len(te), "trap_edges_length_m": round(sum(e["length"] for e in te), 1),
    "trap_edges_twoway": sum(1 for e in te if not e["flags"] & B.F_ONEWAY),
    "trap_by_street": {k: [v[0], round(v[1], 1)] for k, v in sorted(by.items(), key=lambda kv: -kv[1][1])},
    "trap_edges_flagged_off_reach": sum(1 for e in te if e["flags"] & B.F_OFF_REACH),
}
# first trap edge on each trap chain: its from-node is still in the main part (the point of no return)
gates = [e for e in te if back[e["from"]]]
rep["points_of_no_return"] = [{"street": t["names"][e["name"]], "at": [round(t["nodes"][e["from"]][0], 1), round(t["nodes"][e["from"]][1], 1)],
                               "length_to_end_m": round(e["length"], 1)} for e in gates]
print(json.dumps(rep, ensure_ascii=False, indent=1))
