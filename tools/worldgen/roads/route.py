"""Start route as a lane path on the generated network (ADR 0076).

The route used to be the raw OSM way geometry (carriageway axis). Since network.align_forks / abreast_forks lay the
branches of a diverge / merge under the lanes they continue, the generated carriageway no longer sits on the OSM
axis near such nodes: the route ran 0.45 m outside the Andersa -> Rondo Putry link, along its kerb
(tests/gis/test_route_corridor: 64 obstructed stations). The route is now read from the same chains the meshes are
built from:

  * every graph edge of the path -> its span of the chain centre line (after all fork shifts),
  * lateral position = centre of the rightmost lane in the direction of travel (lane_layout: what the markings
    paint), on one-way carriageways and on two-way roads alike (a truck keeps right; a 1-lane link = its centre),
  * where two consecutive pieces do not meet (lane count changes, a merge lane ends, a diverge) and the heading
    does not turn, the lateral gap is taken up as a lane change on the wider carriageway, smoothstep over
    LANE_CHANGE_RATIO x gap (>= LANE_CHANGE_MIN_M); at real turns the pieces are simply joined, as before.
"""

from __future__ import annotations

import math

import numpy as np

from .markings import lane_layout

SAMPLE_M = 0.5
LANE_CHANGE_RATIO = 12.0     # WORKING_VALUE: lane change length = 12 x lateral offset (3.5 m -> 42 m, ~2.5 s at 60 km/h)
LANE_CHANGE_MIN_M = 20.0
LANE_CHANGE_MAX_TURN_DEG = 30.0


def _smoothstep(x):
    x = np.clip(x, 0.0, 1.0)
    return x * x * (3 - 2 * x)


def _edge_span(net, eid):
    for c in net.chains:
        for s0, s1, x, _rev in c.raw_spans:
            if x == eid:
                k = c.length / max(c.raw_spans[-1][1], 1e-9)
                return c, s0 * k, s1 * k
    raise KeyError(eid)


def _right_lane_lat(c, sec, s, trav):
    """Chain lateral (left +) of the rightmost lane centre for travel sign `trav` along the chain."""
    hw = float(c.hw_at(s))
    dirn = int(c.dirn[c.idx(s)])
    _, _, cen = lane_layout(sec, hw, dirn or 1)
    if sec.oneway:
        lat = cen["fwd"][-1] if cen["fwd"] else 0.0
    else:
        lanes = cen["fwd"] if trav > 0 else cen["bwd"]
        lat = lanes[-1] if lanes else (-0.5 * hw if trav > 0 else 0.5 * hw)
    lim = max(hw - 1.4, 0.0)                 # never closer than half a truck to the carriageway edge (tapers)
    return float(np.clip(lat, -lim, lim))


def lane_route(net, path_edges, node_xy, step=2.0):
    """path_edges: [(edge id, from node, to node)] along the path; node_xy: {node id: local (E, N)}.
    Returns (points (n, 2) every `step` m, edge id per point, half carriageway width per point)."""
    secs = net.sec_list
    pieces = []
    for eid, u, v in path_edges:
        c, sa, sb = _edge_span(net, eid)
        pa, pb = c.line.point(sa), c.line.point(sb)
        xu = np.asarray(node_xy[u], float)
        fwd = float(np.hypot(*(pa - xu))) <= float(np.hypot(*(pb - xu)))
        s0, s1, trav = (sa, sb, 1) if fwd else (sb, sa, -1)
        n = max(2, int(math.ceil(abs(s1 - s0) / SAMPLE_M)) + 1)
        ss = np.linspace(s0, s1, n)
        sec = net.sections[eid]
        lat = np.array([_right_lane_lat(c, sec, float(s), trav) for s in ss])
        P = c.line.offset_point(ss, lat)
        hw = np.asarray(c.hw_at(ss), float)
        pieces.append((P, hw, eid))
    # lane changes at joints that do not turn
    P = np.concatenate([p for p, _, _ in pieces])
    HW = np.concatenate([h for _, h, _ in pieces])
    E = [e for p, _, e in pieces for _ in range(len(p))]
    starts = np.cumsum([0] + [len(p) for p, _, _ in pieces])
    shift = np.zeros_like(P)
    seg = np.hypot(*np.diff(P, axis=0).T)
    for k in starts[1:-1]:
        seg[k - 1] = 0.0                       # the joint itself is not travelled
    s = np.concatenate([[0.0], np.cumsum(seg)])
    for k in starts[1:-1]:
        a, b = P[k - 1], P[k]
        pi = int(np.searchsorted(starts, k, side="right")) - 1        # piece that starts at k
        ta = P[k - 1] - P[max(k - 5, starts[pi - 1])]
        tb = P[min(k + 4, starts[pi + 1] - 1)] - P[k]
        if np.hypot(*ta) < 1e-6 or np.hypot(*tb) < 1e-6:
            continue
        ta, tb = ta / np.hypot(*ta), tb / np.hypot(*tb)
        turn = math.degrees(math.acos(float(np.clip(np.dot(ta, tb), -1, 1))))
        gap = b - a
        g = float(np.hypot(*gap))
        if g < 0.3 or turn > LANE_CHANGE_MAX_TURN_DEG:
            continue
        L = max(LANE_CHANGE_MIN_M, LANE_CHANGE_RATIO * g)
        if HW[k - 1] >= HW[k]:                 # the approach is the wider carriageway: change lanes before the joint
            m = (np.arange(len(P)) < k) & (s[k - 1] - s < L)
            shift[m] += gap[None, :] * _smoothstep(1.0 - (s[k - 1] - s[m]) / L)[:, None]
        else:                                  # merge onto the wider carriageway: change lanes after the joint
            m = (np.arange(len(P)) >= k) & (s - s[k] < L)
            shift[m] -= gap[None, :] * _smoothstep(1.0 - (s[m] - s[k]) / L)[:, None]
    P = P + shift
    d = np.hypot(*np.diff(P, axis=0).T)
    keep = np.concatenate([[True], d > 0.05])
    P, E = P[keep], [e for e, kk in zip(E, keep) if kk]
    HW = HW[keep]
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    n = int(s[-1] // step) + 1
    si = np.linspace(0.0, s[-1], n)
    R = np.column_stack([np.interp(si, s, P[:, 0]), np.interp(si, s, P[:, 1])])
    idx = np.clip(np.searchsorted(s, si, side="right") - 1, 0, len(E) - 1)
    return R, [E[i] for i in idx], HW[idx], float(s[-1])
