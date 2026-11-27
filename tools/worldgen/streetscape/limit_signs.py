"""B-16 / B-18 at the entries of bridges and tunnels with a height / weight limit in the road graph (ADR 0307, D91).

Rule: every run of a chain on a structure (`bridge` / `tunnel` edge) whose graph edge carries `maxheight` and / or
`maxweight:hgv` (else `maxweight`) gets one post per direction of travel, BEFORE_M before the structure, on the right,
facing the traffic: B-16_<m> on top (Z1 pkt 3.2.17 "zakaz wjazdu pojazdów o wysokości ponad ... m"), B-18_<t> below
(pkt 3.2.19). Values are the OSM values of the edge (same parsers as the GPS graph, navgraph.build_route_graph), so
the sign, the GPS warning and the cab warning read one source.

Scope on purpose: structures only. A `maxweight` on an ordinary street (e.g. the 6 t / 12 t streets of Tykocin) is
signed at its junctions in reality; that is a different rule and is not built here.
`maxaxleload` (B-19) is not signed: the only values in the corridor are the stale 10 t of ADR 0303.

Reference for the DW671 bridge over the Narew in Tykocin (OSM w96942026): B-16 "3,7 m" stands at both entries
(Mapillary 2020-06-23 / 2020-09-20, Commons 2025-09-20; ADR 0307); B-18 12 t is OSM only (edit of 2026-08-22, newer
than every photo) = WORKING_VALUE.
"""

from __future__ import annotations

import numpy as np

from navgraph.build_route_graph import parse_length_m, parse_weight_t

from . import built_up as BU

BEFORE_M = 15.0          # WORKING_VALUE: post this far before the structure (photos of w96942026: ~15-20 m)
RETRY_STEP_M = 4.0       # when another sign post stands there (e.g. the B-33 of the same entry): further out
RETRIES = 3
END_CLEAR_M = 1.0


def _v(attrs, key):
    a = attrs.get(key)
    return a.get("v") if isinstance(a, dict) else a


def _fmt(x):
    x = round(float(x), 1)
    return str(int(x)) if x.is_integer() else f"{x:.1f}"


def edge_limits(attrs):
    """(height m | None, weight t | None) of a graph edge on a structure, else (None, None)."""
    if not (_v(attrs, "bridge") or _v(attrs, "tunnel")):
        return None, None
    h = parse_length_m(_v(attrs, "maxheight"))
    w = parse_weight_t(_v(attrs, "maxweight:hgv"))
    if w is None:
        w = parse_weight_t(_v(attrs, "maxweight"))
    return h, w


def plates_for(h, w):
    """Plates top first."""
    out = []
    if h:
        out.append(f"B-16_{_fmt(h)}")
    if w:
        out.append(f"B-18_{_fmt(w)}")
    return out


def runs(net, graph_attrs):
    """[(chain, s0, s1, (h, w), edge_id)]: maximal stretches of a chain with one constant limit."""
    res = []
    for c in net.chains:
        if c.roundabout or c.sec_idx is None:
            continue
        lims = []
        for i in c.sec_idx:
            sec = net.sec_list[int(i)]
            lims.append((edge_limits(graph_attrs.get(sec.edge_id, {})), sec.edge_id))
        k, n = 0, len(lims)
        while k < n:
            lim, eid = lims[k]
            j = k
            while j + 1 < n and lims[j + 1][0] == lim:
                j += 1
            if lim != (None, None):
                res.append((c, float(c.line.s[k]), float(c.line.s[j]), lim, eid))
            k = j + 1
    return res


def limit_signs(pl, net, graph_attrs, report, codes):
    """Place the posts; report["limit_signs"] = what was built and what was not."""
    rep = {"placed": {}, "structures": [], "rule": f"ADR 0307: B-16 / B-18 {BEFORE_M:.0f} m before a bridge / tunnel "
                                                    "with maxheight / maxweight in roads.graph.json"}
    for c, s0, s1, (h, w), eid in runs(net, graph_attrs):
        plates = plates_for(h, w)
        rec = {"edge": eid, "chain": str(c.id), "s0": round(s0, 1), "s1": round(s1, 1), "maxheight_m": h,
               "maxweight_t": w, "plates": plates, "entries": []}
        lo, hi = c.t_a + END_CLEAR_M, c.length - c.t_b - END_CLEAR_M
        for dn, s_edge in ((1, s0), (-1, s1)):
            sgn = int(np.sign(c.dirn[c.idx(s_edge)]))
            if sgn not in (0, dn):
                continue                                      # one-way against this entry
            p, s_used = None, None
            for k in range(RETRIES):
                s = float(np.clip(s_edge - dn * (BEFORE_M + k * RETRY_STEP_M), lo, hi))
                p = BU._place(pl, c, s, dn, plates, f"rule:limit:{eid}:{'fwd' if dn > 0 else 'bwd'}", codes, rep, net=net)
                if p is not None:
                    s_used = s
                    break
            rec["entries"].append({"dir": "forward" if dn > 0 else "backward",
                                   "s": None if s_used is None else round(s_used, 1),
                                   "e": None if p is None else round(float(p[0]), 1),
                                   "n": None if p is None else round(float(p[1]), 1),
                                   "before_m": None if s_used is None else round(abs(s_edge - s_used), 1),
                                   "placed": p is not None})
        rep["structures"].append(rec)
    report["limit_signs"] = rep
    return rep
