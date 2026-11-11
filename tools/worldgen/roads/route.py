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
    does not turn, the lateral gap is taken up as a lane change on the carriageway with more lanes (the wider one
    when the lane counts are equal), smoothstep over LANE_CHANGE_RATIO x gap (>= LANE_CHANGE_MIN_M),
  * at real turns (junction, roundabout entry, diverge onto a link) the lane lines of the two pieces cross or
    overshoot each other by up to the lateral lane offset (the route ran 1-2 m forward and back: 10 false "steps"
    in test_route_profile_has_no_steps): both pieces are cut at their crossing (or the overshooting points are
    dropped) and the corner is rounded with a quadratic Bezier over JOINT_ROUND_M each side
    (JOINT_ROUND_MILD_M at turns up to JOINT_MILD_TURN_DEG).
"""

from __future__ import annotations

import math

import numpy as np

from .markings import lane_layout

SAMPLE_M = 0.5
LANE_CHANGE_RATIO = 12.0     # WORKING_VALUE: lane change length = 12 x lateral offset (3.5 m -> 42 m, ~2.5 s at 60 km/h)
LANE_CHANGE_MIN_M = 20.0
LANE_CHANGE_MAX_TURN_DEG = 30.0
JOINT_SEARCH_M = 8.0         # how far from a joint the two lane lines are searched for their crossing
JOINT_ROUND_M = 4.0          # WORKING_VALUE: corner rounding length each side of a turning joint
JOINT_ROUND_MILD_M = 10.0    # WORKING_VALUE: the same at mild turns (a diverge onto a link), <= JOINT_MILD_TURN_DEG
JOINT_MILD_TURN_DEG = 60.0
# ADR 0095: on a roundabout ring and on the one-way arms next to it the route follows the carriageway axis, not the
# centre of the rightmost lane, blending back to the lane over RING_BLEND_M. With the lane centre (ADR 0076) the
# line hugged the outer kerb of the ring and cut the inner corner of the exit: the tridem of the 16.5 m combination
# ran 2.9 m (Rondo Biezenstwa, E 559 N -689) / 1.0 m (Rondo Putry, E -535 N 52) off the carriageway in
# tests/physics/test_swept_path_gate3 (was 1.1 m / clear on the OSM axes). A truck straddles the ring lanes anyway.
RING_BLEND_M = 30.0          # WORKING_VALUE


def _seg_x(p, q, a, b):
    """Intersection of segments pq and ab (None if they do not cross)."""
    r, d = q - p, b - a
    den = r[0] * d[1] - r[1] * d[0]
    if abs(den) < 1e-12:
        return None
    w = a - p
    t = (w[0] * d[1] - w[1] * d[0]) / den
    u = (w[0] * r[1] - w[1] * r[0]) / den
    return p + t * r if (0.0 <= t <= 1.0 and 0.0 <= u <= 1.0) else None


def _unit(v):
    n = float(np.hypot(*v))
    return v / n if n > 1e-9 else None


def _trim_joint(A, hA, B, hB):
    """Cut piece A (ends at the joint) and piece B (starts there) so the path does not run back on itself."""
    m = int(JOINT_SEARCH_M / SAMPLE_M)
    for i in range(len(A) - 2, max(len(A) - 2 - m, -1), -1):          # crossing nearest the joint first
        for j in range(0, min(m, len(B) - 1)):
            X = _seg_x(A[i], A[i + 1], B[j], B[j + 1])
            if X is not None and i >= 1 and j + 2 < len(B):
                return (np.vstack([A[:i + 1], X]), np.append(hA[:i + 1], hA[i + 1]),
                        np.vstack([X, B[j + 1:]]), np.append(hB[j], hB[j + 1:]))
    ta = _unit(A[-1] - A[max(len(A) - 5, 0)])
    tb = _unit(B[min(4, len(B) - 1)] - B[0])
    if ta is None or tb is None:
        return A, hA, B, hB
    turn = math.degrees(math.acos(float(np.clip(np.dot(ta, tb), -1, 1))))
    if turn <= LANE_CHANGE_MAX_TURN_DEG and float(np.hypot(*(B[0] - A[-1]))) >= 0.3:
        return A, hA, B, hB                                            # a lane change, handled by the caller
    j = 0
    while j < min(m, len(B) - 3) and float(np.dot(B[j] - A[-1], ta)) < 0.0:   # B starts behind the end of A
        j += 1
    B, hB = B[j:], hB[j:]
    i = len(A)
    while i > max(len(A) - m, 3) and float(np.dot(A[i - 1] - B[0], tb)) > 0.0:   # A ends ahead of the start of B
        i -= 1
    return A[:i], hA[:i], B, hB


def _round_corner(P, k, d=JOINT_ROUND_M):
    """Replace the points within d of the joint P[k-1] | P[k] by a quadratic Bezier (in place, same count)."""
    s = np.concatenate([[0.0], np.cumsum(np.hypot(*np.diff(P, axis=0).T))])
    sk = 0.5 * (s[k - 1] + s[k])
    m = np.where(np.abs(s - sk) <= d)[0]
    if len(m) < 3 or m[0] == 0 or m[-1] == len(P) - 1:
        return
    a, b = P[m[0]].copy(), P[m[-1]].copy()
    c = 0.5 * (P[k - 1] + P[k])
    u = (s[m] - s[m[0]]) / max(s[m[-1]] - s[m[0]], 1e-9)
    P[m] = ((1 - u) ** 2)[:, None] * a + (2 * u * (1 - u))[:, None] * c + (u ** 2)[:, None] * b


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


def _through_lane(sec):
    """Index (from the left) of the rightmost lane a vehicle going straight on may use, by turn:lanes; None = the
    rightmost lane. ADR 0095: the right lane of Andersa before the side street at n10015785253 is a right-turn lane
    that ends at a kerbed island - the route keeps to the lane beside it."""
    tl = sec.turn_fwd if sec.oneway else None
    if not tl or len(tl) != sec.lanes:
        return None
    ok = [i for i, t in enumerate(tl) if not t or t == "none" or "through" in t.split(";")]
    return ok[-1] if ok and ok[-1] != len(tl) - 1 else None


def _right_lane_lat(c, sec, s, trav, lane=None):
    """Chain lateral (left +) of the rightmost lane centre for travel sign `trav` along the chain (`lane`: index
    from the left on a one-way carriageway instead of the rightmost one)."""
    hw = float(c.hw_at(s))
    dirn = int(c.dirn[c.idx(s)])
    _, _, cen = lane_layout(sec, hw, dirn or 1)
    if sec.oneway:
        lat = cen["fwd"][-1 if lane is None else lane] if cen["fwd"] else 0.0
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
    spans = []
    for eid, u, v in path_edges:
        c, sa, sb = _edge_span(net, eid)
        fw = float(np.hypot(*(c.line.point(sa) - np.asarray(node_xy[u], float)))) <= \
            float(np.hypot(*(c.line.point(sb) - np.asarray(node_xy[u], float))))
        s_in, s_out = (sa, sb) if fw else (sb, sa)
        sg = 1.0 if fw else -1.0
        spans.append((c.line.frame(s_in)[0] * sg, c.line.frame(s_out)[0] * sg))
    # path distance from the end of the last roundabout edge before / to the first one after every edge
    elen = [abs(_edge_span(net, e_)[2] - _edge_span(net, e_)[1]) for e_, _, _ in path_edges]
    isr = [bool(net.sections[e_].roundabout) for e_, _, _ in path_edges]
    ring_before, ring_after = [1e9] * len(elen), [1e9] * len(elen)
    acc = 1e9
    for i_ in range(len(elen)):
        ring_before[i_] = acc
        acc = 0.0 if isr[i_] else acc + elen[i_]
    acc = 1e9
    for i_ in range(len(elen) - 1, -1, -1):
        ring_after[i_] = acc
        acc = 0.0 if isr[i_] else acc + elen[i_]
    for i_e, (eid, u, v) in enumerate(path_edges):
        c, sa, sb = _edge_span(net, eid)
        pa, pb = c.line.point(sa), c.line.point(sb)
        xu = np.asarray(node_xy[u], float)
        fwd = float(np.hypot(*(pa - xu))) <= float(np.hypot(*(pb - xu)))
        s0, s1, trav = (sa, sb, 1) if fwd else (sb, sa, -1)
        n = max(2, int(math.ceil(abs(s1 - s0) / SAMPLE_M)) + 1)
        ss = np.linspace(s0, s1, n)
        sec = net.sections[eid]
        lane = None
        if i_e + 1 < len(path_edges):       # going straight on at the end of this edge: not in a turn-only lane
            if float(np.dot(spans[i_e][1], spans[i_e + 1][0])) > math.cos(math.radians(20.0)):
                lane = _through_lane(sec)
        lat = np.array([_right_lane_lat(c, sec, float(s), trav, lane) for s in ss])
        if sec.roundabout:
            lat[:] = 0.0
        elif sec.oneway:
            lat *= _smoothstep((ring_before[i_e] + np.abs(ss - s0)) / RING_BLEND_M) * \
                _smoothstep((ring_after[i_e] + np.abs(s1 - ss)) / RING_BLEND_M)
        P = c.line.offset_point(ss, lat)
        hw = np.asarray(c.hw_at(ss), float)
        if pieces:
            A, hA, e0 = pieces[-1]
            A, hA, P, hw = _trim_joint(A, hA, P, hw)
            pieces[-1] = (A, hA, e0)
        pieces.append((P, hw, eid))
    # lane changes at joints that do not turn
    P = np.concatenate([p for p, _, _ in pieces])
    HW = np.concatenate([h for _, h, _ in pieces])
    E = [e for p, _, e in pieces for _ in range(len(p))]
    starts = np.cumsum([0] + [len(p) for p, _, _ in pieces])
    shift = np.zeros_like(P)
    corners = []
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
        if turn > LANE_CHANGE_MAX_TURN_DEG:
            corners.append((k, JOINT_ROUND_MILD_M if turn <= JOINT_MILD_TURN_DEG else JOINT_ROUND_M))
            continue
        if g < 0.3:
            continue
        L = max(LANE_CHANGE_MIN_M, LANE_CHANGE_RATIO * g)
        la, lb = net.sections[E[k - 1]].lanes, net.sections[E[k]].lanes
        # change lanes on the carriageway with more lanes (a 1-lane merge branch has its gore / the other branch
        # beside it: the lane change before the joint ran over the nose kerb at j:n3341716400, 4 steps at s = 618 m);
        # equal lane counts: on the wider one
        if la > lb or (la == lb and HW[k - 1] >= HW[k]):
            m = (np.arange(len(P)) < k) & (s[k - 1] - s < L)
            shift[m] += gap[None, :] * _smoothstep(1.0 - (s[k - 1] - s[m]) / L)[:, None]
        else:                                  # merge onto the wider carriageway: change lanes after the joint
            m = (np.arange(len(P)) >= k) & (s - s[k] < L)
            shift[m] -= gap[None, :] * _smoothstep(1.0 - (s[m] - s[k]) / L)[:, None]
    P = P + shift
    for k, d in corners:
        _round_corner(P, k, d)
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
