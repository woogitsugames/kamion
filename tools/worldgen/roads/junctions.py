"""Junction clusters, curb-return fillets, arm trims and junction patch boundaries.

A junction = one or more graph nodes of degree >= 3 merged when the chain between them is shorter than
the space both corners need. Arms = chains leaving the cluster, oriented outward. Between every pair of
angularly adjacent arms there is a corner:
  * fillet  – kerb return of radius R tangent to both gutter lines (centre = intersection of the gutter
              lines offset outward by R);
  * nose    – arms almost parallel (median / splitter island): semicircle between the gutters;
  * straight– arms almost opposite (continuation / ring): gutter lines joined at their intersection.
Each arm's ribbon is trimmed at the largest tangent station of its two corners; the patch polygon is
end sections + gutter pieces + arcs, CCW.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np

from . import standards as S
from .geom import cumlen, polyline_intersections, polygon_area

LOOK = 70.0     # m of arm used for corner construction
STEP = 0.5


@dataclass
class Arm:
    chain: object
    end: str            # 'a' (outward = +s) or 'b' (outward = -s)
    node: str

    @property
    def key(self):
        return (self.chain.id, self.end)

    @property
    def L(self):
        return self.chain.length

    def s(self, d):
        d = np.asarray(d, float)
        return d if self.end == "a" else self.chain.length - d

    def lat_sign(self):
        return 1.0 if self.end == "a" else -1.0

    def gutter(self, d, side, extra=0.0):
        """Point on the arm's gutter (side +1 = left of outward direction), optionally offset `extra`
        further outward (away from the road)."""
        d = np.asarray(d, float)
        s = self.s(np.maximum(d, 0.0))
        hw = self.chain.hw_at(s)
        lat = side * (hw + extra) * self.lat_sign()
        p = self.chain.line.offset_point(s, lat)
        if np.any(d < 0):     # straight extrapolation behind the arm start (inside clusters)
            back = self.direction(0.0) * np.minimum(d, 0.0)[..., None]
            p = p + back
        return p

    def line(self, side, extra, dmax, dmin=0.0):
        d = np.arange(dmin, dmax + 1e-9, STEP)
        if d[-1] < dmax:
            d = np.append(d, dmax)
        return self.gutter(d, side, extra), d

    def direction(self, d=0.0):
        t, _ = self.chain.line.frame(self.s(d))
        return t * self.lat_sign()

    def cls(self, sections):
        return self.chain.section(self.s(1.0), sections).cls

    def is_ring(self):
        return self.chain.roundabout

    def inbound_dirn(self):
        """+1 if traffic on this arm travels toward the junction, -1 away, 0 two-way."""
        i = self.chain.idx(self.s(1.0))
        dn = int(self.chain.dirn[i])
        if dn == 0:
            return 0
        return -dn if self.end == "a" else dn


@dataclass
class Corner:
    kind: str
    k: int
    k1: int
    R: float = 0.0
    center: np.ndarray | None = None
    tau_k: float = 0.0       # tangent station on arm k (left gutter)
    tau_k1: float = 0.0      # tangent station on arm k+1 (right gutter)
    arc: np.ndarray | None = None   # points from arm k gutter to arm k+1 gutter (excluding gutter pieces)


@dataclass
class Junction:
    id: str
    nodes: list
    arms: list = field(default_factory=list)
    center: np.ndarray | None = None
    corners: list = field(default_factory=list)
    trims: dict = field(default_factory=dict)       # arm index -> trim station d
    signalized: bool = False
    emergency_signals: bool = False     # traffic_signals=emergency only (fire-station exit, ADR 0074)
    roundabout: bool = False
    give_way: bool = False
    boundary: list = field(default_factory=list)    # [(xy, tag)] CCW
    notes: list = field(default_factory=list)
    internal: list = field(default_factory=list)    # absorbed chains inside the cluster (their surface shapes the patch)


def _ang(v):
    return math.atan2(v[1], v[0])


def _wrap(a):
    return (a + math.pi) % (2 * math.pi) - math.pi


def chain_ends(net):
    ends = {}
    for c in net.chains:
        if c.closed:
            continue
        ends.setdefault(c.node_a, []).append((c, "a"))
        ends.setdefault(c.node_b, []).append((c, "b"))
    return ends


def corner_radius(net, arm_k, arm_k1, override=None):
    if override is not None:
        return float(override)
    secs = net.sec_list
    order = ["A", "S", "GP", "G", "Z", "L", "D"]
    ck, ck1 = arm_k.cls(secs), arm_k1.cls(secs)
    # kerb return governed by the lower class road (turning into it), WORKING_VALUE
    lo = max(order.index(ck), order.index(ck1))
    R = S.CURB_RADIUS[order[lo]]
    if arm_k.is_ring() or arm_k1.is_ring():
        R = min(R, 12.0)
    return R


def _facing_gap(A, B, d=6.0):
    """Signed clear width between the facing gutters of two angularly adjacent arms (A left, B right), d m out
    from the junction: < 0 where the carriageways overlap."""
    d = min(d, A.L, B.L)
    pa, pb = A.gutter(d, +1), B.gutter(min(d, B.L), -1)
    t = A.direction(d)
    nl = np.array([-t[1], t[0]])
    return float(np.dot(pb - pa, nl))


def compute_corners(net, j: Junction, max_trim: dict, r_override=None):
    arms = j.arms
    n = len(arms)
    corners = []
    tau = {i: [S.JUNCTION_MIN_TRIM, S.JUNCTION_MIN_TRIM] for i in range(n)}   # [right, left]
    for k in range(n):
        k1 = (k + 1) % n
        A, B = arms[k], arms[k1]
        if n == 1:
            break
        dA, dB = A.direction(min(4.0, A.L / 2)), B.direction(min(4.0, B.L / 2))
        alpha = (_ang(dB) - _ang(dA)) % (2 * math.pi)
        mA, mB = max_trim[k] - 0.3, max_trim[k1] - 0.3
        alpha_deg = math.degrees(alpha)
        back = 25.0 if len(j.nodes) > 1 else 0.0

        def hit(extra, look=LOOK):
            la, da = A.line(+1, extra, min(look, A.L), -back)
            lb, db = B.line(-1, extra, min(look, B.L), -back)
            ok = None
            for sa, sb, pt in polyline_intersections(la, lb):
                ta = float(np.interp(sa, cumlen(la), da))
                tb = float(np.interp(sb, cumlen(lb), db))
                if ta <= mA and tb <= mB and (ok is None or ta + tb < ok[0] + ok[1]):
                    ok = (ta, tb, pt)
            return ok

        c = None
        # ADR 0095: node override `nose_max_angle` - a fork whose branch leaves at a wider angle than
        # NOSE_MAX_ANGLE_DEG in the first metres (OSM kinks the link off the main axis) but then runs beside the
        # main carriageway behind a kerbed separator: gore nose where the gutters cross, not a 2.5 m fillet 50 m on
        nose_ang = S.NOSE_MAX_ANGLE_DEG
        for n_ in j.nodes:
            nose_ang = max(nose_ang, float(net.nodes[n_].get("override", {}).get("nose_max_angle", 0.0)))
        if alpha_deg < nose_ang:
            h0 = hit(0.0, 160.0)
            if h0 is not None:   # fork: gutters cross -> gore nose just after the carriageways separate
                c = Corner("nose", k, k1, tau_k=min(h0[0] + 1.5, mA), tau_k1=min(h0[1] + 1.5, mB))
                c.meta_fork = True
            elif _facing_gap(A, B) >= S.NOSE_MIN_GAP_M:   # parallel (median): nose at the trims
                c = Corner("nose", k, k1, tau_k=-1.0, tau_k1=-1.0)
            else:                # parallel carriageways that touch or overlap (merge of an on-ramp into the main
                # road, Andersa / Rondo Bieżeństwa): no island between them, the surfaces join (straight corner)
                j.notes.append(f"corner {k}-{k1}: arms touch (gap {_facing_gap(A, B):.2f} m) -> no nose")
        elif alpha_deg <= S.STRAIGHT_MIN_ANGLE_DEG:
            R = corner_radius(net, A, B, r_override)
            while R >= 0.75:
                ok = hit(R)
                if ok is not None:
                    ta, tb, C = ok
                    Ta, Tb = A.gutter(ta, +1), B.gutter(tb, -1)
                    a0, a1 = _ang(Ta - C), _ang(Tb - C)
                    sweep = _wrap(a1 - a0)
                    m = max(2, int(math.ceil(abs(sweep) * R / 1.0)))
                    angs = a0 + sweep * np.linspace(0, 1, m + 1)
                    arc = C + R * np.column_stack([np.cos(angs), np.sin(angs)])
                    arc[0], arc[-1] = Ta, Tb
                    c = Corner("fillet", k, k1, R=R, center=C, tau_k=ta, tau_k1=tb, arc=arc)
                    break
                R *= 0.7
            if c is None:
                j.notes.append(f"corner {k}-{k1}: no fillet fits (alpha {alpha_deg:.0f} deg) -> sharp")
        if c is None:
            best = hit(0.0)
            if best is not None:
                c = Corner("straight", k, k1, tau_k=best[0], tau_k1=best[1], arc=np.array([best[2]]))
            else:   # gutters do not meet (width change / taper): join the two end-section corners directly
                c = Corner("straight", k, k1, tau_k=-1.0, tau_k1=-1.0, arc=None)
        corners.append(c)
        tau[k][1] = max(tau[k][1], c.tau_k)
        tau[k1][0] = max(tau[k1][0], c.tau_k1)
    trims = {}
    for i in range(n):
        t = max(tau[i]) + 0.25
        trims[i] = min(t, max_trim[i])
    # width-change joins ("straight" corners whose gutters never meet, e.g. a two-way road splitting into
    # one-way entry/exit lanes around a gatehouse island): instead of a lateral kerb step at the trims,
    # extend the wider arm so the kerb runs as a chamfer of 1 : S.CHAMFER_RATIO from the narrow arm's
    # gutter end to the wider arm's gutter (WORKING_VALUE ratio, typical kerb taper at splitter islands).
    for c in corners:
        if c.kind != "straight" or c.arc is not None or n < 3:
            continue
        A, B = arms[c.k], arms[c.k1]
        hA, hB = float(A.chain.hw_at(A.s(trims[c.k]))), float(B.chain.hw_at(B.s(trims[c.k1])))
        if abs(hA - hB) < 0.4:
            continue
        wide, narrow, ws, ns = (c.k, c.k1, +1, -1) if hA > hB else (c.k1, c.k, -1, +1)
        W, Nn = arms[wide], arms[narrow]
        P = Nn.gutter(trims[narrow], ns)
        gl, gd = W.line(ws, 0.0, min(LOOK, W.L))
        dist = np.hypot(*(gl - P).T)
        i0 = int(np.argmin(dist))
        delta = float(dist[i0])
        if not 0.3 < delta < 4.0:
            continue
        t_need = float(gd[i0]) + S.CHAMFER_RATIO * delta
        t_w = min(t_need, max_trim[wide])
        if t_w <= trims[wide] + 0.05:
            continue                  # already long enough (or capped by the next junction)
        trims[wide] = t_w
        c.kind = "chamfer"            # joined end corner to end corner at the (final) trims, like "straight"
        j.notes.append(f"corner {c.k}-{c.k1}: kerb chamfer 1:{S.CHAMFER_RATIO:g} over {t_w - float(gd[i0]):.1f} m "
                       f"(width step {delta:.2f} m)")
    # median noses sit at the trims and bulge back toward the junction by r = gap / 2: push the
    # trims out by r so the nose does not intrude into the crossing carriageway
    for c in corners:
        if c.kind == "nose" and c.tau_k < 0:
            A, B = arms[c.k], arms[c.k1]
            # abreast first (ADR 0074): with different trims (a kerb return on one carriageway only, e.g. the
            # fire-station median crossing on Andersa) the "semicircle" on the diagonal end-to-end chord was a 13 m
            # disc lying across the inner lane of the longer-trimmed carriageway.
            u = A.direction(trims[c.k]) + B.direction(trims[c.k1])
            u = u / max(float(np.hypot(*u)), 1e-9)
            for _ in range(3):
                xa = float(np.dot(A.gutter(trims[c.k], +1), u))
                xb = float(np.dot(B.gutter(trims[c.k1], -1), u))
                if abs(xa - xb) < 0.2:
                    break
                if xa < xb:
                    trims[c.k] = min(trims[c.k] + (xb - xa), max_trim[c.k])
                else:
                    trims[c.k1] = min(trims[c.k1] + (xa - xb), max_trim[c.k1])
            gap = float(np.hypot(*(A.gutter(trims[c.k], +1) - B.gutter(trims[c.k1], -1))))
            need = gap / 2 + 0.5
            trims[c.k] = min(trims[c.k] + need, max_trim[c.k])
            trims[c.k1] = min(trims[c.k1] + need, max_trim[c.k1])
    return corners, trims


def build_junctions(net, ctx_points=None) -> list[Junction]:
    ends = chain_ends(net)
    jn = sorted(n for n, lst in ends.items() if len(lst) >= 3 or (len(lst) == 2 and net.nodes[n]["deg"] >= 3))
    parent = {n: n for n in jn}

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def make(cluster_nodes):
        nodes = sorted(cluster_nodes)
        arms = []
        nodeset = set(nodes)
        for c in net.chains:
            if c.closed:
                continue
            ina, inb = c.node_a in nodeset, c.node_b in nodeset
            if ina and inb and not c.roundabout and c.length < 40.0 and len(nodes) > 1:
                continue        # internal (absorbed) chain
            if ina:
                arms.append(Arm(c, "a", c.node_a))
            if inb:
                arms.append(Arm(c, "b", c.node_b))
        ctr = np.mean([net.nodes[n]["xy"] for n in nodes], axis=0)
        arms.sort(key=lambda a: (_ang(a.gutter(min(6.0, a.L * 0.5), 0) - ctr), a.key))
        j = Junction(id="j:" + nodes[0], nodes=nodes, arms=arms, center=ctr)
        return j

    def max_trims(j, assume_half=True):
        mt = {}
        for i, a in enumerate(j.arms):
            other = a.chain.node_b if a.end == "a" else a.chain.node_a
            if other in parent and find(other) == find(j.nodes[0]) and other != a.node:
                mt[i] = a.L * 0.5 - 0.25      # chain loops back into the same cluster
            elif other in parent:
                mt[i] = a.L * 0.5 - 0.25 if assume_half else a.L - 0.5
            else:
                mt[i] = a.L - 0.5
        return mt

    # iterative clustering
    for _it in range(8):
        groups = {}
        for n in jn:
            groups.setdefault(find(n), []).append(n)
        trims = {}
        for root in sorted(groups):
            j = make(groups[root])
            mt = {i: a.L - 0.5 for i, a in enumerate(j.arms)}
            ovr = _radius_override(net, j)
            _, tr = compute_corners(net, j, mt, ovr)
            for i, a in enumerate(j.arms):
                trims[a.key] = tr[i]
        merged = False
        for c in net.chains:
            if c.closed or c.roundabout:
                continue
            if c.node_a in parent and c.node_b in parent and find(c.node_a) != find(c.node_b):
                ta, tb = trims.get((c.id, "a"), 0), trims.get((c.id, "b"), 0)
                if c.length < ta + tb + 1.0:
                    ga = [n for n in jn if find(n) == find(c.node_a)]
                    gb = [n for n in jn if find(n) == find(c.node_b)]
                    pts = np.array([net.nodes[n]["xy"] for n in ga + gb])
                    diam = float(np.max(np.hypot(*(pts[:, None, :] - pts[None, :, :]).transpose(2, 0, 1))))
                    if diam <= 30.0:
                        parent[find(c.node_a)] = find(c.node_b)
                        merged = True
        if not merged:
            break

    groups = {}
    for n in jn:
        groups.setdefault(find(n), []).append(n)
    juncs = []
    for root in sorted(groups):
        j = make(groups[root])
        juncs.append(j)
    # final corners with shared-chain trim limits (two junctions on one chain split it)
    key2j = {}
    for j in juncs:
        for i, a in enumerate(j.arms):
            key2j[a.key] = (j, i)
    for j in juncs:
        mt = max_trims(j)
        j.corners, j.trims = compute_corners(net, j, mt, _radius_override(net, j))
        j.roundabout = any(a.is_ring() for a in j.arms)
        # traffic_signals=emergency (fire-station exits: dark / flashing amber for road users, ADR 0074) is not a
        # signal-controlled junction: no P-14, no P-2a, no arrows, no S-1 heads of a junction. roadgraph marks any
        # signal within 15 m as `signals_nearby`, so that flag only counts when a non-emergency signal is near.
        sig_pts = [p for p in (ctx_points or []) if p["kind"] == "highway=traffic_signals"]
        real = [p for p in sig_pts if p.get("traffic_signals") != "emergency"]
        emerg = [p for p in sig_pts if p.get("traffic_signals") == "emergency"]
        emerg_ids = {f"n{p['osm_node']}" for p in emerg}

        def node_sig(n):
            nd = net.nodes[n]
            if nd["feature"] == "highway=traffic_signals" and n not in emerg_ids:
                return True
            if not nd["signals"]:
                return False
            if not ctx_points:
                return True
            return any(math.hypot(p["e"] - nd["xy"][0], p["n"] - nd["xy"][1]) <= 16.0 for p in real)
        j.signalized = any(node_sig(n) for n in j.nodes)
        j.give_way = any(net.nodes[n]["feature"] in ("highway=give_way", "highway=stop") for n in j.nodes)
        if ctx_points:
            r = 25.0 + max((float(np.hypot(*(net.nodes[n]["xy"] - j.center))) for n in j.nodes), default=0)
            for p in real:
                if math.hypot(p["e"] - j.center[0], p["n"] - j.center[1]) < r:
                    j.signalized = True
            j.emergency_signals = (not j.signalized) and any(
                math.hypot(p["e"] - j.center[0], p["n"] - j.center[1]) < r for p in emerg)
        # ADR 0186: authored node override `set: {signalized: false | true}` - a junction the proximity rule above
        # gets wrong (a U-turn gap 20 m before the stop line of the next junction is not signal-controlled itself)
        for n in j.nodes:
            ov = net.nodes[n].get("override", {})
            if "signalized" in ov:
                j.signalized = bool(ov["signalized"])
                j.emergency_signals = False
    for j in juncs:
        for i, a in enumerate(j.arms):
            if a.end == "a":
                a.chain.t_a = max(a.chain.t_a, j.trims[i])
            else:
                a.chain.t_b = max(a.chain.t_b, j.trims[i])
    # absorbed chains (internal to a cluster) are flagged so no ribbon is built for them
    arm_keys = {a.key for j in juncs for a in j.arms}
    for c in net.chains:
        if not c.closed and (c.id, "a") not in arm_keys and (c.id, "b") not in arm_keys and \
                c.node_a in parent and c.node_b in parent:
            c.meta["absorbed"] = True
            for j in juncs:
                if c.node_a in j.nodes and c.node_b in j.nodes:
                    j.internal.append(c)
    for j in juncs:
        j.boundary = patch_boundary(j)
    return juncs


def _radius_override(net, j):
    for n in j.nodes:
        ov = net.nodes[n].get("override", {})
        if "curb_radius" in ov:
            return ov["curb_radius"]
    return None


def patch_boundary(j: Junction):
    """CCW boundary of the junction patch as [(xy, tag)], tag describes how to evaluate height:
       ("end", arm_i, side_frac)   point of arm end section (side_frac -1..1 right..left)
       ("gutter", arm_i, d, side)  arm gutter at station d
       ("arc", corner_i, frac)     fillet / nose / straight join
    """
    out = []
    n = len(j.arms)
    if n < 2:
        return out
    corner_by_k = {c.k: (ci, c) for ci, c in enumerate(j.corners)}
    for i, a in enumerate(j.arms):
        t = j.trims[i]
        # end section right -> left (sample: gutter, lane points every <= 1.75 m, gutter)
        out.append((a.gutter(t, -1), ("end", i, -1.0)))
        hw = float(a.chain.hw_at(a.s(t)))
        m = a.chain.m_lat          # must equal the ribbon's lateral sampling (shared seam vertices)
        for q in np.linspace(-1, 1, m + 1)[1:-1]:
            s = a.s(t)
            p = a.chain.line.offset_point(s, q * hw * a.lat_sign())
            out.append((p, ("end", i, float(q))))
        out.append((a.gutter(t, +1), ("end", i, 1.0)))
        ci, c = corner_by_k[i]
        B = j.arms[(i + 1) % n]
        tb = j.trims[(i + 1) % n]
        # gutter of arm i (left) from trim inward to tau
        nose_at_trim = c.kind in ("nose", "straight", "chamfer") and c.tau_k < 0
        tk = t if nose_at_trim else c.tau_k
        tk1 = tb if nose_at_trim else c.tau_k1
        x_pt = None
        if c.kind == "straight" and nose_at_trim and \
                float(np.hypot(*(a.gutter(t, +1) - B.gutter(tb, -1)))) > 6.0:
            # trims differ a lot: keep the shorter arm's end corner and walk down the longer arm's gutter
            # to the point nearest to it (a taper), instead of a long diagonal across the patch
            # If the longer arm's gutter starts INSIDE the shorter arm's carriageway (a narrow lane leaving a
            # wide road, e.g. one-way gate lanes splitting off a two-way access road), the nearest point lies
            # under the wide road and the kerb made a Z-step. Then continue the shorter arm's kerb line
            # straight to where the longer arm's gutter emerges from under it (X) and follow that gutter.
            dd = np.linspace(0.0, max(t, tb), 120)
            if t <= tb:
                g = B.gutter(dd, -1)
                PA, dA = a.gutter(t, +1), a.direction(t)
                sd = (g - PA) @ np.array([-dA[1], dA[0]])
                k = np.nonzero(sd >= 0.0)[0]
                if len(k) and k[0] > 0 and dd[k[0]] < tb:
                    tk1 = float(dd[k[0]])
                    x_pt = PA + dA * float((g[k[0]] - PA) @ dA)
                else:
                    tk1 = float(min(dd[int(np.argmin(np.hypot(*(g - PA).T)))], tb))
            else:
                g = a.gutter(dd, +1)
                PB, dB = B.gutter(tb, -1), B.direction(tb)
                sd = (g - PB) @ np.array([dB[1], -dB[0]])
                k = np.nonzero(sd >= 0.0)[0]
                if len(k) and k[0] > 0 and dd[k[0]] < t:
                    tk = float(dd[k[0]])
                    x_pt = PB + dB * float((g[k[0]] - PB) @ dB)
                else:
                    tk = float(min(dd[int(np.argmin(np.hypot(*(g - PB).T)))], t))
        for d in _desc(t, tk):
            out.append((a.gutter(d, +1), ("gutter", i, d, +1)))
        if x_pt is not None and c.kind == "straight":
            out.append((x_pt, ("arc", ci, 0.5)))
            j.notes.append(f"corner {c.k}-{c.k1}: kerb line continued to the emerging lane edge (gate-type split)")
        if c.kind == "fillet":
            for f, p in zip(np.linspace(0, 1, len(c.arc))[1:-1], c.arc[1:-1]):
                out.append((p, ("arc", ci, float(f))))
        elif c.kind == "nose":
            if not nose_at_trim:
                out.append((a.gutter(tk, +1), ("gutter", i, tk, +1)))
            P, Q = a.gutter(tk, +1), B.gutter(tk1, -1)
            r = float(np.hypot(*(Q - P))) / 2
            if r > 0.3:
                M = (P + Q) / 2
                out_dir = a.direction(t) + B.direction(tb)
                nrm = np.hypot(*out_dir)
                out_dir = out_dir / nrm if nrm > 1e-6 else np.array([0.0, 0.0])
                a0 = _ang(P - M)
                a1 = _ang(Q - M)
                sweep = _wrap(a1 - a0)
                mid = a0 + sweep / 2
                # the nose must bulge toward the junction (against out_dir)
                if np.dot(np.array([math.cos(mid), math.sin(mid)]), out_dir) > 0:
                    sweep = sweep - math.copysign(2 * math.pi, sweep)
                mm = max(3, int(math.ceil(abs(sweep) * r / 0.6)))
                angs = a0 + sweep * np.linspace(0, 1, mm + 1)
                arc = M + r * np.column_stack([np.cos(angs), np.sin(angs)])
                c.arc = arc
                c.R = r
                c.center = M
                for f, p in zip(np.linspace(0, 1, mm + 1)[1:-1], arc[1:-1]):
                    out.append((p, ("arc", ci, float(f))))
        elif c.kind == "straight" and c.arc is not None and len(c.arc) == 1:
            out.append((c.arc[0], ("arc", ci, 0.5)))
        for d in _asc(tk1, tb):
            out.append((B.gutter(d, -1), ("gutter", (i + 1) % n, d, -1)))
    # remove consecutive duplicates
    clean = []
    for p, tag in out:
        if clean and np.hypot(*(p - clean[-1][0])) < 0.02:
            continue
        clean.append((np.asarray(p, float), tag))
    if len(clean) > 2 and np.hypot(*(clean[0][0] - clean[-1][0])) < 0.02:
        clean.pop()
    poly = np.array([p for p, _ in clean])
    if len(poly) >= 3 and polygon_area(poly) < 0:
        j.notes.append("boundary orientation CW (unexpected)")
    return clean


def _desc(t, tau, step=1.5):
    """Stations from t (exclusive) down to tau (inclusive)."""
    if t - tau < 0.05:
        return []
    m = max(1, int(math.ceil((t - tau) / step)))
    return list(np.linspace(t, tau, m + 1)[1:])


def _asc(tau, t, step=1.5):
    """Stations from tau (inclusive) up to t (exclusive)."""
    if t - tau < 0.05:
        return []
    m = max(1, int(math.ceil((t - tau) / step)))
    return list(np.linspace(tau, t, m + 1)[:-1])
