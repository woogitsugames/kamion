"""Authored split of a two-way road into two one-way carriageways before a node (ADR 0274).

OSM often splits a road into its entry / exit carriageways only a few metres before a roundabout (DK65 in Knyszyn:
17 m before the ring), although the kerbed splitter island and the two separate lanes start much earlier. The override

    - id: ...
      kind: carriageway_split
      node: <osm node id of the present split node>
      set: {length_m: 24.0, taper_m: 14.0, lane_offset_m: 3.0}

moves the split node `length_m` further out along the two-way road and re-draws the two one-way edges that meet there:
from the new split node the lane axes leave the old centre line with a smoothstep over `taper_m` to `lane_offset_m`
either side, run parallel to it and join the mapped one-way geometry where that is at least as far from the centre
line. Only the graph handed to network.load is changed (a copy; roads.graph.json stays as ingested), so the chains,
the junctions, the markings and the start route (pipeline.build_network) all see the same lanes.

The two-way edge keeps its id; the new node is `<old id>s`. A node that is not the meeting point of exactly one
two-way and two one-way edges (one arriving, one leaving), a road shorter than length_m + MIN_LEFT_M or values out of
range make the override stale - nothing is changed.
"""

from __future__ import annotations

import math

import numpy as np

KIND = "carriageway_split"
TAG = "carriageway_splits_applied"      # ids of the overrides already applied to a graph dict
LIMITS = {"length_m": (5.0, 120.0), "taper_m": (5.0, 60.0), "lane_offset_m": (1.5, 6.0)}
MIN_LEFT_M = 5.0            # of the two-way edge beyond the new split node
STEP_M = 1.0


def _num(v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        return None
    v = float(v)
    return v if math.isfinite(v) and lo <= v <= hi else None


def _cum(P):
    return np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])


def _at(P, cum, s):
    i = int(np.clip(np.searchsorted(cum, s, side="right") - 1, 0, len(P) - 2))
    t = (P[i + 1] - P[i]) / max(cum[i + 1] - cum[i], 1e-9)
    return P[i] + t * (s - cum[i]), t


def _one(graph, o) -> bool:
    st = o.get("set")
    if not isinstance(st, dict) or set(st) - set(LIMITS) or "length_m" not in st:
        return False
    L = _num(st["length_m"], *LIMITS["length_m"])
    taper = _num(st.get("taper_m", 14.0), *LIMITS["taper_m"])
    off = _num(st.get("lane_offset_m", 3.0), *LIMITS["lane_offset_m"])
    if None in (L, taper, off) or taper > L + 30.0:
        return False
    nid = f"n{o.get('node')}"
    inc = [e for e in graph["edges"] if nid in (e["from"], e["to"])]
    two = [e for e in inc if e["attrs"]["oneway"]["v"] not in ("yes", "-1")]
    one = [e for e in inc if e["attrs"]["oneway"]["v"] == "yes"]
    if len(inc) != 3 or len(two) != 1 or len(one) != 2 or {e["from"] == nid for e in one} != {True, False}:
        return False
    e2 = two[0]
    P = np.array(e2["geometry"], float)
    P = P if e2["from"] == nid else P[::-1]
    cum = _cum(P)
    if cum[-1] < L + MIN_LEFT_M:
        return False
    new_pt, _ = _at(P, cum, L)
    k = int(np.searchsorted(cum, L, side="right"))
    tail = np.vstack([new_pt, P[k:]])
    # stations x from the new split node back to the old one
    xs = np.append(np.arange(0.0, L, STEP_M), L)
    ax, tg = zip(*[_at(P, cum, L - x) for x in xs])
    ax, tg = np.array(ax), -np.array(tg)                    # tangents point towards the old node (inward)
    nl = np.column_stack([-tg[:, 1], tg[:, 0]])             # left of the inward direction
    t = np.clip(xs / taper, 0.0, 1.0)
    lat = off * t * t * (3.0 - 2.0 * t)
    old, d_in = P[0], tg[-1]
    n_in = np.array([-d_in[1], d_in[0]])
    new_id = nid + "s"
    for e in one:
        F = np.array(e["geometry"], float)
        F = F if e["from"] == nid else F[::-1]              # from the old split node to the far (ring) end
        fc = _cum(F)
        ss = np.append(np.arange(0.0, fc[-1], 0.25), fc[-1])
        Fp = np.array([_at(F, fc, s)[0] for s in ss])
        la, al = (Fp - old) @ n_in, (Fp - old) @ d_in
        sgn = 1.0 if la[-1] >= 0 else -1.0
        hit = np.where(la * sgn >= off)[0]
        i_join = int(hit[0]) if len(hit) else len(ss) - 1
        a_join = max(float(al[i_join]), 0.0)
        ext = old + np.outer(np.arange(STEP_M, a_join - 0.5, STEP_M), d_in) + sgn * off * n_in if len(hit) else np.zeros((0, 2))
        G = np.vstack([ax + sgn * lat[:, None] * nl, ext, Fp[i_join:]])
        keep = [0] + [i for i in range(1, len(G)) if np.hypot(*(G[i] - G[i - 1])) > 0.05]
        G = G[keep]
        if e["from"] != nid:
            G = G[::-1]
        e["geometry"] = [[round(float(x), 3), round(float(y), 3)] for x, y in G]
        e["length_m"] = round(float(_cum(G)[-1]), 3)
        e["from" if e["from"] == nid else "to"] = new_id
    geo = tail if e2["from"] == nid else tail[::-1]
    e2["geometry"] = [[round(float(x), 3), round(float(y), 3)] for x, y in geo]
    e2["length_m"] = round(float(cum[-1] - L), 3)
    e2["from" if e2["from"] == nid else "to"] = new_id
    src = next(n for n in graph["nodes"] if n["id"] == nid)
    graph["nodes"] = [n for n in graph["nodes"] if n["id"] != nid]
    graph["nodes"].append({"id": new_id, "x": round(float(new_pt[0]), 3), "y": round(float(new_pt[1]), 3), "degree": 3,
                           "z_terrain": src.get("z_terrain"), "authored": o["id"], "split_of": nid})
    return True


def node_aliases(graph: dict) -> dict:
    """{id of a split node in roads.graph.json -> id of the node that replaces it in this (effective) graph}. Empty for
    a graph without applied splits. Readers that hold node ids of the ingested graph (route_start.json graph_nodes,
    OSM via nodes of turn restrictions) translate them with this; the inverse maps effective ids back."""
    return {n["split_of"]: n["id"] for n in graph.get("nodes", []) if n.get("split_of")}


def apply(graph: dict, overrides, applied: list, stale: list) -> dict:
    """The graph with every `carriageway_split` override applied (a copy when there is one, else the same object)."""
    ovs = [o for o in overrides or [] if isinstance(o, dict) and o.get("kind") == KIND]
    if not ovs:
        return graph
    done = list(graph.get(TAG, []))
    graph = dict(graph, nodes=[dict(n) for n in graph["nodes"]], edges=[dict(e) for e in graph["edges"]])
    for o in ovs:
        if o.get("id") in done:                               # a graph from pipeline.effective_graph: applied once
            applied.append({"id": o["id"], "targets": [f"n{o.get('node')}"]})
            continue
        try:
            ok = _one(graph, o)
        except (KeyError, TypeError, ValueError, StopIteration):
            ok = False
        if ok:
            applied.append({"id": o["id"], "targets": [f"n{o['node']}"]})
            done.append(o["id"])
        else:
            stale.append(o.get("id", "?"))
    graph[TAG] = done
    return graph
