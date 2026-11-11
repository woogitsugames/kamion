"""Vertical alignment (niweleta) of every chain from the 1 m NMT, and crossfall.

Profile = Whittaker smoother of the NMT road-surface samples (median across the carriageway), with
hard constraints at junction nodes so all chains meeting at a node share its height. The smoothing
weight λ is increased until the vertical curvature satisfies the class minimum radius
(standards.VCURVE_MIN_R): where a small λ breaks it, a least-squares fit with bounded curvature. Elevated stations (OSM `bridge` or `layer` >= 1) carry zero data weight (the
NMT is bare ground under a deck and under ramps the classifier removed), so a deck is a smooth curve between
known nodes. Grade separation: wherever an elevated station lies over a ground road, the deck surface is held at
the ground road + standards.BRIDGE_CLEARANCE + margin + deck thickness (hard constraint). Without it the NMT
pulled both Andersa viaducts down to ~1.5 m above the rings they cross (photos show multi-span viaducts).
Nodes where only elevated chains meet get their height from the decks solved first (low confidence, flagged).
"""

from __future__ import annotations

import math

import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve

from . import standards as S
from .network import DENSE


class Heightfield:
    def __init__(self, z: np.ndarray, bbox, origin):
        self.z = z
        self.bbox = bbox
        self.ox, self.oy = origin
        self.x0 = bbox[0] - self.ox      # local E of column 0
        self.y1 = bbox[3] - self.oy      # local N of row 0

    def sample(self, e, n):
        e = np.asarray(e, float)
        n = np.asarray(n, float)
        fi = e - self.x0
        fj = self.y1 - n
        i = np.clip(np.floor(fi).astype(int), 0, self.z.shape[1] - 2)
        j = np.clip(np.floor(fj).astype(int), 0, self.z.shape[0] - 2)
        tx = np.clip(fi - i, 0, 1)
        ty = np.clip(fj - j, 0, 1)
        z = self.z
        a = z[j, i] * (1 - tx) + z[j, i + 1] * tx
        b = z[j + 1, i] * (1 - tx) + z[j + 1, i + 1] * tx
        return a * (1 - ty) + b * ty


def load_heightfield(terrain_meta: dict, repo_root, origin) -> Heightfield:
    enc = terrain_meta["encoding"]
    raw = np.fromfile(repo_root / enc["file"], dtype="<u2")
    h, w = terrain_meta["samples"][1], terrain_meta["samples"][0]
    z = enc["offset_m"] + raw.reshape(h, w).astype(np.float64) * enc["scale_m_per_unit"]
    return Heightfield(z, terrain_meta["bbox"], origin)


def elevated(net, c) -> np.ndarray:
    """Per station: on a structure or a raised ramp (OSM bridge, or layer >= 1)."""
    return np.array([bool(net.sec_list[i].bridge) or net.sec_list[i].layer >= 1 for i in c.sec_idx])


def node_heights(net, hf: Heightfield) -> dict:
    """Ground height at every chain-end node (median of NMT within 3 m); None where only elevated chains meet."""
    zs = {}
    bridge_end = {}
    for c in net.chains:
        el = elevated(net, c)
        for node, i in ((c.node_a, 0), (c.node_b, -1)):
            bridge_end.setdefault(node, []).append(bool(el[i]))
    off = np.array([(dx, dy) for dx in (-3, -1.5, 0, 1.5, 3) for dy in (-3, -1.5, 0, 1.5, 3) if dx * dx + dy * dy <= 9.1])
    for nid in sorted(bridge_end):
        ov = net.nodes[nid].get("override", {})
        if "z" in ov:
            zs[nid] = float(ov["z"])
            continue
        if all(bridge_end[nid]):
            zs[nid] = None
            continue
        p = net.nodes[nid]["xy"]
        zs[nid] = float(np.median(hf.sample(p[0] + off[:, 0], p[1] + off[:, 1])))
    return zs


def whittaker(y, w, lam, h):
    """lam: scalar or one value per second-difference row (len(y) - 2): locally stiffer where it is larger."""
    n = len(y)
    if n < 4:
        return np.where(w > 0, y, np.nanmean(y))
    D = sp.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n)) / (h * h)
    L = sp.diags(np.broadcast_to(np.asarray(lam, float), (n - 2,)))
    A = sp.diags(w) + D.T @ L @ D
    return spsolve(A.tocsc(), w * np.nan_to_num(y))


def bounded_curvature_fit(y, w, kmax, h, lam, z0, lower=None, iters=150):
    """Whittaker smoother whose λ is raised row by row (x 2.5, rows breaking the bound and their 1 m neighbourhood)
    until |k| <= kmax (k = second difference / h^2), with z >= lower (nan = no bound) enforced by pinning the stations
    that fall below it. Stiffening only where the radius is broken keeps the rest of the chain on its data.
    Returns (z, converged)."""
    n = len(y)
    D = (sp.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n)) / (h * h)).tocsr()
    yy = w * np.nan_to_num(y)
    lo = np.full(n, np.nan) if lower is None else lower
    has_lo = ~np.isnan(lo)
    lamv = np.full(n - 2, float(lam))
    pin_lo = np.zeros(n, bool)
    z = z0
    ok = False
    grow = max(1, int(round(1.0 / h)))
    for _ in range(iters):
        k = np.abs(D @ z)
        bad = k > kmax * 1.002
        new_lo = has_lo & ~pin_lo & (z < np.nan_to_num(lo) - 0.01)
        if not bad.any() and not new_lo.any():
            ok = True
            break
        if bad.any():
            idx = np.nonzero(bad)[0]
            m = np.zeros(n - 2, bool)
            for d in range(-grow, grow + 1):
                m[np.clip(idx + d, 0, n - 3)] = True
            lamv[m] *= 2.5
        pin_lo |= new_lo
        wl = np.where(pin_lo, 1e6, 0.0)
        A = sp.diags(w + wl) + D.T @ sp.diags(lamv) @ D
        z = spsolve(A.tocsc(), yy + wl * np.nan_to_num(lo))
    return z, ok


def chain_profile(c, hf: Heightfield, z_a, z_b, rmin: float, el=None, req=None, adj=None):
    """el: elevated stations (zero data weight); req: {station: required deck height} (hard constraints);
    adj: {station: centreline height that puts this edge on the surface of an adjacent road} (adjacent_targets)."""
    s = c.line.s
    n = len(s)
    _, nrm = c.line.frame(s)
    offs = np.array([-0.7, -0.35, 0.0, 0.35, 0.7])
    samp = []
    for f in offs:
        q = c.line.p + nrm * (c.hw * f)[:, None]
        samp.append(hf.sample(q[:, 0], q[:, 1]))
    y = np.median(np.array(samp), axis=0)
    w = np.where(c.bridge if el is None else el, 0.0, 1.0)
    for i, zr in (adj or {}).items():
        y[i] = zr
        w[i] = S.ADJ_WEIGHT
    # clearance: a lower bound on the deck surface (z >= required), not an equality
    lower = np.full(n, np.nan)
    for i, zr in (req or {}).items():
        lower[i] = zr
    if w.sum() == 0:
        w[:] = 1e-3
    for zz, i in ((z_a, 0), (z_b, n - 1)):
        if zz is not None:
            y[i] = zz
            w[i] = 1e8
    kmax = 1.0 / rmin
    # λ: the smallest (x 2.5 steps from 2) at which the *data alone* (NMT samples, constraint rows down-weighted to
    # 1) keep the class minimum radius, i.e. the NMT noise is smoothed out. The hard constraints (node heights,
    # viaduct clearance) and the adjacent-edge targets then bend the profile only where they must: rows whose
    # curvature still breaks the radius are bounded (bounded_curvature_fit), not the whole chain stiffened. v3
    # raised one λ until the radius held everywhere: the clearance constraint at a viaduct then straightened the
    # entire chain (Andersa westbound at Rondo Bieżeństwa: λ 2.8e9, the ramp 2.2 m above the NMT and above the
    # on-ramp whose edge it touches, 250 m from the deck -> route_start blocked at s = 571 m, r4).
    wd = np.minimum(w, 1.0)
    if wd.sum() == 0:
        wd[:] = 1e-3
    lam = 2.0
    z = whittaker(y, wd, lam, DENSE)
    for _ in range(30):
        k = np.abs(np.diff(z, 2)) / DENSE ** 2 if n >= 3 else np.zeros(1)
        if k.max() <= kmax:
            break
        lam *= 2.5
        z = whittaker(y, wd, lam, DENSE)
    z = whittaker(y, w, lam, DENSE)
    k = np.abs(np.diff(z, 2)) / DENSE ** 2 if n >= 3 else np.zeros(1)
    below = np.nan_to_num(lower, nan=-np.inf) - z
    converged = True
    if n >= 4 and (k.max() > kmax or below.max() > 1e-3):
        z, converged = bounded_curvature_fit(y, w, kmax, DENSE, lam, z, lower)
    data = w > 0.5
    data[[0, -1]] = False
    rms = float(np.sqrt(np.mean((z[data] - y[data]) ** 2))) if data.any() else 0.0
    return z, {"lambda": lam, "bounded_fit_converged": converged, "rms_vs_nmt_m": round(rms, 3),
               "max_vcurv_1_per_m": float(np.abs(np.diff(z, 2)).max() / DENSE ** 2) if n >= 3 else 0.0}


def crossfall(c):
    """One-sided crossfall e(s) (z = zc + e * lat, lat > 0 left) or NaN for a roof (crowned) profile."""
    n = len(c.line.s)
    e = np.full(n, np.nan)
    one = c.dirn != 0
    if not one.any():
        return e
    from .geom import smooth_1d
    kap = smooth_1d(c.line.kappa, 10.0 / DENSE)
    base = S.CROSSFALL * c.dirn.astype(float)        # falls to the right of travel
    if c.roundabout:
        val = S.ROUNDABOUT_CROSSFALL * c.dirn.astype(float)   # falls outward (right of travel)
    else:
        curve = np.abs(kap) > 1.0 / S.CURVE_R
        val = np.where(curve, -np.sign(kap) * S.CROSSFALL_CURVE, base)
    val = smooth_1d(val, S.CROSSFALL_RAMP_SIGMA_M / DENSE)
    e[one] = val[one]
    return e


def match_crossfall_at_nodes(net) -> int:
    """Chains continuing through a node (outward directions within 60 deg of opposite: straight continuations and the
    branches of a fork) get one crossfall at the node, ramped linearly over CROSSFALL_MATCH_M from each end. Pairs
    are taken straightest first: the first pair meets at the mean of its two end values, a later branch takes the
    value already fixed for the chain it leaves (a slip road keeps the main carriageway's crossfall at the gore).
    Crossfall was computed per chain, so the DK8 slip road's 2.5 % curve banking met the 2 % of the carriageway it
    leaves the other way round at the Putry ramp fork: a 4.5 % twist, 4-5 cm per 0.5 m under the wheels
    (route_start s = 1422 m). Returns the number of matched chain ends."""
    ends = {}
    for c in net.chains:
        if c.e is None or c.closed or len(c.line.s) < 3:
            continue
        ends.setdefault(c.node_a, []).append((c, 0))
        ends.setdefault(c.node_b, []).append((c, -1))
    n = 0
    L = S.CROSSFALL_MATCH_M

    def ramp(C, ec, tv):
        d = C.line.s if ec == 0 else C.length - C.line.s
        f = np.clip(1.0 - d / L, 0.0, 1.0)
        C.e = C.e + (tv - C.e[ec]) * f

    for node in sorted(ends):
        lst = [(C, ec) for C, ec in ends[node] if not np.isnan(C.e[ec])]
        pairs = []
        for ia in range(len(lst)):
            for ib in range(ia + 1, len(lst)):
                (A, ea), (B, eb) = lst[ia], lst[ib]
                if A is B:
                    continue
                ta, tb = A.line.t[ea], B.line.t[eb]
                oa = -ta if ea == 0 else ta
                ob = -tb if eb == 0 else tb
                dot = float(np.dot(oa, ob))
                if dot <= -0.5:
                    pairs.append((dot, ia, ib))
        fixed = {}
        for dot, ia, ib in sorted(pairs):
            (A, ea), (B, eb) = lst[ia], lst[ib]
            sg = 1.0 if float(np.dot(A.line.t[ea], B.line.t[eb])) > 0 else -1.0   # B's lateral frame vs A's
            if ia in fixed and ib in fixed:
                continue
            if ia in fixed:
                tv = fixed[ia]
            elif ib in fixed:
                tv = sg * fixed[ib]
            else:
                tv = 0.5 * (A.e[ea] + sg * B.e[eb])
            if ia not in fixed:
                ramp(A, ea, tv)
                fixed[ia] = tv
                n += 1
            if ib not in fixed:
                ramp(B, eb, sg * tv)
                fixed[ib] = sg * tv
                n += 1
    return n


def clearance_requirements(net, el_of, ground_z) -> dict:
    """{chain id: {station: required deck surface z}} for bridge stations (OSM `bridge`) whose footprint overlaps
    a ground road. Ground roads sharing a node with the bridge chain are ignored within 30 m of that node (a
    bridge over a stream meets its own approach roads at grade). ground_z: {chain id: solved profile}."""
    from scipy.spatial import cKDTree
    gp, gz, ghw, gk, gs, gcl = [], [], [], [], [], []
    ground = [c for c in net.chains if c.id in ground_z]
    for k, c in enumerate(ground):
        gp.append(c.line.p); gz.append(ground_z[c.id]); ghw.append(c.hw)
        gk.append(np.full(len(c.line.s), k)); gs.append(c.line.s)
        gcl.append(np.array([S.clearance_height(net.sec_list[i].cls) for i in c.sec_idx]))
    if not gp:
        return {}
    gp, gz, ghw, gk, gs, gcl = (np.concatenate(x) for x in (gp, gz, ghw, gk, gs, gcl))
    tree = cKDTree(gp)
    # deck surface >= road below + skrajnia of that road's class (PTB2022 § 80 ust. 1) + margin + deck depth
    extra = S.BRIDGE_CLEARANCE_MARGIN + S.BRIDGE_DECK_THICKNESS
    out = {}
    for c in net.chains:
        if not c.bridge.any():
            continue
        ends = {c.node_a, c.node_b}
        req = {}
        for i in np.nonzero(c.bridge)[0]:
            for k in tree.query_ball_point(c.line.p[i], float(c.hw[i]) + float(ghw.max()) + 0.5):
                if np.hypot(*(gp[k] - c.line.p[i])) > float(c.hw[i]) + float(ghw[k]) + 0.5:
                    continue
                g = ground[int(gk[k])]
                if (g.node_a in ends and gs[k] < 30.0) or (g.node_b in ends and g.length - gs[k] < 30.0):
                    continue
                req[int(i)] = max(req.get(int(i), -1e9), float(gz[k]) + float(gcl[k]) + extra)
        if req:
            out[c.id] = req
    return out


def _surface_offset(e, roof, lat):
    return -S.CROSSFALL * abs(lat) if roof else e * lat


def adjacent_targets(c, ground: list, el, min_dot: float = 0.9) -> dict:
    """Stations of chain c (not elevated) whose edge touches or overlaps a roughly parallel, already solved ground
    road (gap between the edges < ADJ_TOUCH_M): the centreline height that puts this edge on that road's surface.
    Two carriageways side by side (a merge, an on-ramp along a main road) share their edge height; the NMT alone
    left the Andersa westbound ramp 0.6-2.2 m above the on-ramp from Rondo Bieżeństwa whose edge it touches, so the
    on-ramp ran into its kerb / wall (route_start blocked at s = 571 m, r4)."""
    if not ground:
        return {}
    from shapely import STRtree
    from shapely.geometry import LineString, Point
    tree = STRtree([LineString(g.line.p) for g in ground])
    ce = crossfall(c)
    out = {}
    for i in range(0, len(c.line.s)):
        if el[i]:
            continue
        p, t = c.line.p[i], c.line.t[i]
        best = None
        for k in tree.query(Point(*p).buffer(float(c.hw[i]) + 8.0 + S.ADJ_TOUCH_M)):
            g = ground[int(k)]
            if g is c:
                continue
            s_o, lat_o = g.line.project(p)
            if s_o <= 0.0 or s_o >= g.length:
                continue
            io = g.idx(s_o)
            if abs(float(np.dot(g.line.t[io], t))) < min_dot:
                continue
            hw_o = float(g.hw_at(s_o))
            if abs(lat_o) - hw_o - float(c.hw[i]) >= S.ADJ_TOUCH_M:
                continue
            sg = 1.0 if float(np.dot(g.line.point(s_o) - p, c.line.n[i])) > 0 else -1.0
            edge = p + c.line.n[i] * sg * float(c.hw[i])
            s_e, lat_e = g.line.project(edge)
            z_edge = float(g.crossfall_z(s_e, lat_e))
            zt = z_edge - _surface_offset(0.0 if np.isnan(ce[i]) else ce[i], np.isnan(ce[i]), sg * float(c.hw[i]))
            if best is None or abs(lat_o) < best[0]:
                best = (abs(lat_o), zt)
        if best is not None:
            out[i] = best[1]
    return out


ABREAST_TIE_DOT = 0.7        # = the parallel test of network._push_abreast (a merge closes at up to ~45 deg)
SHIFTED_END_MIN_M = 0.3      # chain ends nearer than this to their node keep the node height
SHIFTED_STEM_MAX_M = 2.0     # an authored placement moves a stem end at most this far off its node (ADR 0095)


def shifted_end_heights(net, ground: dict) -> dict:
    """{(chain id, 0 | -1): height} for ground chain ends that no longer sit on their node (fork shifts): the
    surface of the widest unshifted ground chain ending at that node (its end section extended as a plane: end
    height + grade x distance along + crossfall x lateral) at the shifted end point."""
    ends = {}
    for c in net.chains:
        if c.id not in ground or c.closed or len(c.line.s) < 3:
            continue
        for node, e in ((c.node_a, 0), (c.node_b, -1)):
            d = float(np.hypot(*(c.line.p[e] - net.nodes[node]["xy"])))
            ends.setdefault(node, []).append((c, e, d))
    out = {}
    for node in sorted(ends):
        stems = [(c, e) for c, e, d in ends[node] if d < SHIFTED_END_MIN_M]
        moved = [(c, e) for c, e, d in ends[node] if d >= SHIFTED_END_MIN_M]
        if not stems and len(moved) >= 2:
            # ADR 0095: every end is off the node because the carriageways have authored placements (measured centre
            # 0.5-1.6 m off the OSM way). The widest end is the stem; the others are "moved" when they do not start on
            # its end point (the link to Rondo Putry starts 4.9 m right of the 3-lane Andersa: it took the node
            # height, 0.10 m above the stem's surface there -> two 5 cm steps in the route profile at s 1411-1413)
            st0 = max(moved, key=lambda x: (float(x[0].hw[x[1]]), x[0].id))
            d0 = float(np.hypot(*(st0[0].line.p[st0[1]] - net.nodes[node]["xy"])))
            if d0 <= SHIFTED_STEM_MAX_M:
                stems = [st0]
                moved = [(c, e) for c, e in moved if c is not st0[0] and
                         float(np.hypot(*(c.line.p[e] - st0[0].line.p[st0[1]]))) >= SHIFTED_END_MIN_M]
        if not stems or not moved:
            continue
        st, se = max(stems, key=lambda x: (float(x[0].hw[x[1]]), x[0].id))
        ce = crossfall(st)[se]
        P0, t0, n0 = st.line.p[se], st.line.t[se], st.line.n[se]
        k = min(len(st.z) - 1, max(2, int(5.0 / DENSE)))
        g = float((st.z[-1] - st.z[-1 - k]) / (st.line.s[-1] - st.line.s[-1 - k])) if se == -1 else             float((st.z[k] - st.z[0]) / (st.line.s[k] - st.line.s[0]))
        for c, e in moved:
            v = c.line.p[e] - P0
            lat = float(np.clip(v @ n0, -float(st.hw[se]), float(st.hw[se])))
            out[(c.id, e)] = float(st.z[se]) + g * float(v @ t0) +                 _surface_offset(0.0 if np.isnan(ce) else float(ce), bool(np.isnan(ce)), lat)
    return out


def build_profiles(net, hf: Heightfield) -> dict:
    zn = node_heights(net, hf)
    stats = {}
    el_of = {c.id: elevated(net, c) for c in net.chains}
    rmin_of = {c.id: min(S.VCURVE_MIN_R[net.sec_list[i].cls] for i in np.unique(c.sec_idx)) for c in net.chains}
    # 1) ground chains (no elevated station): NMT with fixed node heights
    ground = {}
    for c in net.chains:
        if el_of[c.id].any():
            continue
        c.z, stats[c.id] = chain_profile(c, hf, zn.get(c.node_a), zn.get(c.node_b), rmin_of[c.id], el_of[c.id])
        ground[c.id] = c.z
    # 1c) chain ends moved off their node by network.align_forks / abreast_forks (ADR 0074 / 0076) start on the
    #     surface of the carriageway they leave, not at the node height: the Andersa -> Rondo Putry link starts
    #     3.25 m right of and 2.4 m before the node, where the 3-lane approach (grade + 2 % crossfall) is 0.11 m
    #     below the node height -> a 0.2 m ramp over 3 m under the right wheels (route_start s = 1408 m)
    zend = shifted_end_heights(net, ground)
    for c in net.chains:
        if (c.id, 0) in zend or (c.id, -1) in zend:
            c.z, stats[c.id] = chain_profile(c, hf, zend.get((c.id, 0), zn.get(c.node_a)),
                                             zend.get((c.id, -1), zn.get(c.node_b)), rmin_of[c.id], el_of[c.id])
            stats[c.id]["shifted_end_dz"] = {("a" if e == 0 else "b"): round(v - zn[n_], 3)
                                             for e, n_ in ((0, c.node_a), (-1, c.node_b))
                                             for v in [zend.get((c.id, e))] if v is not None}
            ground[c.id] = c.z
    # 1b) a ground chain laid abreast of another ground road (network.abreast_forks, ADR 0076) takes that road's
    #     surface height at the shared edge, like an elevated ramp does in step 3
    by_id = {c.id: c for c in net.chains}
    for c in net.chains:
        nb = by_id.get(c.meta.get("abreast_of"))
        if c.id not in ground or nb is None or nb.id not in ground:
            continue
        nb.e = crossfall(nb)
        adj = adjacent_targets(c, [nb], el_of[c.id])
        if adj:
            c.z, stats[c.id] = chain_profile(c, hf, zend.get((c.id, 0), zn.get(c.node_a)),
                                             zend.get((c.id, -1), zn.get(c.node_b)), rmin_of[c.id], el_of[c.id],
                                             adj=adj)
            stats[c.id]["adjacent_edge"] = {"stations": len(adj)}
            ground[c.id] = c.z
    # 2) grade separation: deck heights over the ground roads
    req = clearance_requirements(net, el_of, ground)
    ground_chains = [c for c in net.chains if c.id in ground]
    for c in ground_chains:
        c.e = crossfall(c)
    adj_of = {}
    # 3) elevated chains: decks with clearance constraints first, then the rest; unknown nodes take the mean of the
    #    chain ends solved so far (decks first), and every chain touching such a node is solved again
    order = sorted((c for c in net.chains if el_of[c.id].any()), key=lambda c: (c.id not in req, c.id))
    pending = {}
    for c in order:
        za, zb = zn.get(c.node_a), zn.get(c.node_b)
        if za is None and c.node_a in pending:
            za = float(np.mean(pending[c.node_a]))
        if zb is None and c.node_b in pending:
            zb = float(np.mean(pending[c.node_b]))
        el = el_of[c.id] if (c.id in req or za is not None or zb is not None) else None
        adj_of[c.id] = adjacent_targets(c, ground_chains, el_of[c.id])
        # an embankment ramp (OSM layer >= 1, no structure) that a ground carriageway merges into / diverges from
        # (network.abreast_forks: the carriageways overlap before the node) is on that carriageway's level over the
        # overlap, not on the straight descent to the node: the Putry viaduct ramp was 1.0 m above the on-ramp from
        # the roundabout 30 m before their node, the 45 m junction patch between them a 0.6 m ridge (MA-012)
        tied = [g for g in ground_chains if g.meta.get("abreast_of") == c.id]
        if tied:
            for i, zt in adjacent_targets(c, tied, c.bridge, min_dot=ABREAST_TIE_DOT).items():
                adj_of[c.id].setdefault(i, zt)
        c.z, stats[c.id] = chain_profile(c, hf, za, zb, rmin_of[c.id], el, req.get(c.id), adj_of[c.id])
        for node, zz in ((c.node_a, c.z[0]), (c.node_b, c.z[-1])):
            if zn.get(node) is None:
                pending.setdefault(node, []).append(float(zz))
    if pending:
        for node, vals in sorted(pending.items()):
            zn[node] = float(np.mean(vals))
        for c in net.chains:
            if c.node_a in pending or c.node_b in pending:
                c.z, stats[c.id] = chain_profile(c, hf, zn[c.node_a], zn[c.node_b], rmin_of[c.id], el_of[c.id],
                                                 req.get(c.id), adj_of.get(c.id))
    for cid, a in adj_of.items():
        if a:
            stats[cid]["adjacent_edge"] = {"stations": len(a)}
    for c in net.chains:
        if c.id in req:
            ii = np.array(sorted(req[c.id]))
            zr = np.array([req[c.id][i] for i in ii])
            stats[c.id]["clearance"] = {"stations": int(len(ii)), "required_max": round(float(zr.max()), 2),
                                        "min_margin_m": round(float((c.z[ii] - zr).min()), 3)}
    for c in net.chains:
        c.e = crossfall(c)
    n_match = match_crossfall_at_nodes(net)
    for c in net.chains:
        g = np.gradient(c.z, c.line.s) if len(c.z) > 1 else np.zeros(1)
        # grade over a 10 m base (what a vehicle feels), not sample-to-sample
        k = max(1, int(5.0 / DENSE))
        if len(c.z) > 2 * k:
            g10 = (c.z[2 * k:] - c.z[:-2 * k]) / (c.line.s[2 * k:] - c.line.s[:-2 * k])
        else:
            g10 = g
        sec = [net.sec_list[i] for i in np.unique(c.sec_idx)]
        lims = [S.grade_limit(x.highway, x.maxspeed) for x in sec]
        stats[c.id].update({"max_grade": round(float(np.abs(g10).max()), 4),
                            "grade_limit_std": max(l[0] for l in lims),
                            "grade_limit_difficult": max(l[1] for l in lims),
                            "bridge_m": round(float(c.bridge.mean() * c.length), 1)})
    return {"node_z": zn, "chains": stats, "crossfall_node_matches": n_match}


def mark_walled_ramps(net, hf: Heightfield) -> list:
    """Raised ramps (non-bridge stations, with or without OSM layer >= 1) whose fill is absent from the NMT are
    retaining-wall ramps,
    not 1 : 1.5 embankments (v3.1). Reasoning: the GUGiK NMT is the lidar ground class; earth embankments with
    side slopes are ground and stay in it (Maczka west of Rondo Putry: slopes 1 : 1.3-1.5 measured in the NMT),
    but a fill between vertical walls is filtered out like a building, so the NMT runs at the level of the
    ground beside the road (both Andersa ramps: the axis NMT is within ~0.5 m of the ground 15-30 m to the
    sides while the solved profile is up to 6 m higher). CC0/CC BY-SA photos (docs/REFERENCES.md:
    `Andersa,_Maczka_streets_in_Białystok_2.jpg`) show the Putry ramp ending in a block-faced retaining wall.
    A station is walled when it is not a bridge, at least RAMP_WALL_MIN_H above the NMT on the
    axis, and the NMT shows less than RAMP_WALL_FILL_FRAC of that height as fill (axis vs. 6 m beyond the
    edge). Runs shorter than 8 m are dropped; runs are extended by 4 m. The stations are added to c.bridge
    (deck geometry, no terrain conform) and listed in c.meta["walled"] (mesh: walls instead of piers)."""
    out = []
    for c in net.chains:
        if c.z is None:
            continue
        # any non-bridge station: OSM tags the eastbound Andersa ramps at Rondo Bieżeństwa layer=1, the westbound
        # ones not at all, yet both rise ~5 m to the deck with no fill in the NMT
        el = ~c.bridge
        if not el.any():
            continue
        s = c.line.s
        P = c.line.p
        _, nrm = c.line.frame(s)
        za = hf.sample(P[:, 0], P[:, 1])
        side = []
        for sg in (-1, 1):
            q = P + nrm * sg * (c.hw[:, None] + 6.0)
            side.append(hf.sample(q[:, 0], q[:, 1]))
        zs = np.minimum(side[0], side[1])
        h = c.z - zs
        fill = za - zs
        w = el & (c.z - za > S.RAMP_WALL_MIN_H) & (fill < S.RAMP_WALL_FILL_FRAC * np.maximum(h, 1e-3))
        if not w.any():
            continue
        idx = np.where(w)[0]
        runs = np.split(idx, np.where(np.diff(idx) > 1)[0] + 1)
        keep = np.zeros(len(s), bool)
        for r in runs:
            if s[r[-1]] - s[r[0]] < 8.0:
                continue
            lo = np.searchsorted(s, s[r[0]] - 4.0)
            hi = np.searchsorted(s, s[r[-1]] + 4.0, side="right")
            keep[lo:hi] = True
        keep &= el
        if not keep.any():
            continue
        c.bridge = c.bridge | keep
        c.meta["walled"] = keep
        if c.side:
            from .network import structure_sides
            structure_sides(c, keep)
        # ground at the wall foot (NMT 1.5 m beyond the deck edge cap), per side ("L" = +normal)
        zg = {}
        for name, sg in (("L", 1), ("R", -1)):
            q = P + nrm * sg * (c.hw[:, None] + S.KERB_TOP_W + S.BRIDGE_CAP_W + 1.5)
            zg[name] = hf.sample(q[:, 0], q[:, 1])
        c.meta["walled_zg"] = zg
        out.append({"chain": c.id, "walled_m": round(float(keep.sum() * (s[1] - s[0] if len(s) > 1 else 0)), 1),
                    "max_wall_h_m": round(float((c.z - za)[keep].max()), 2),
                    "nmt_fill_max_m": round(float(fill[keep].max()), 2), "confidence": "medium"})
    return out
