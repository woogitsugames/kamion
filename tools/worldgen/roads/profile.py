"""Vertical alignment (niweleta) of every chain from the 1 m NMT, and crossfall.

Profile = Whittaker smoother of the NMT road-surface samples (median across the carriageway), with
hard constraints at junction nodes so all chains meeting at a node share its height. The smoothing
weight λ is increased until the vertical curvature satisfies the class minimum radius
(standards.VCURVE_MIN_R). Elevated stations (OSM `bridge` or `layer` >= 1) carry zero data weight (the
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
    n = len(y)
    if n < 4:
        return np.where(w > 0, y, np.nanmean(y))
    D = sp.diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(n - 2, n)) / (h * h)
    A = sp.diags(w) + lam * (D.T @ D)
    return spsolve(A.tocsc(), w * np.nan_to_num(y))


def chain_profile(c, hf: Heightfield, z_a, z_b, rmin: float, el=None, req=None):
    """el: elevated stations (zero data weight); req: {station: required deck height} (hard constraints)."""
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
    for i, zr in (req or {}).items():
        y[i] = zr
        w[i] = 1e8
    if w.sum() == 0:
        w[:] = 1e-3
    for zz, i in ((z_a, 0), (z_b, n - 1)):
        if zz is not None:
            y[i] = zz
            w[i] = 1e8
    kmax = 1.0 / rmin
    lam = 2.0
    z = whittaker(y, w, lam, DENSE)
    for _ in range(30):
        k = np.abs(np.diff(z, 2)) / DENSE ** 2 if n >= 3 else np.zeros(1)
        if k.max() <= kmax:
            break
        lam *= 2.5
        z = whittaker(y, w, lam, DENSE)
    data = w > 0.5
    data[[0, -1]] = False
    rms = float(np.sqrt(np.mean((z[data] - y[data]) ** 2))) if data.any() else 0.0
    return z, {"lambda": lam, "rms_vs_nmt_m": round(rms, 3),
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
    # 2) grade separation: deck heights over the ground roads
    req = clearance_requirements(net, el_of, ground)
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
        c.z, stats[c.id] = chain_profile(c, hf, za, zb, rmin_of[c.id], el, req.get(c.id))
        for node, zz in ((c.node_a, c.z[0]), (c.node_b, c.z[-1])):
            if zn.get(node) is None:
                pending.setdefault(node, []).append(float(zz))
    if pending:
        for node, vals in sorted(pending.items()):
            zn[node] = float(np.mean(vals))
        for c in net.chains:
            if c.node_a in pending or c.node_b in pending:
                c.z, stats[c.id] = chain_profile(c, hf, zn[c.node_a], zn[c.node_b], rmin_of[c.id], el_of[c.id],
                                                 req.get(c.id))
    for c in net.chains:
        if c.id in req:
            ii = np.array(sorted(req[c.id]))
            zr = np.array([req[c.id][i] for i in ii])
            stats[c.id]["clearance"] = {"stations": int(len(ii)), "required_max": round(float(zr.max()), 2),
                                        "min_margin_m": round(float((c.z[ii] - zr).min()), 3)}
    for c in net.chains:
        c.e = crossfall(c)
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
    return {"node_z": zn, "chains": stats}


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
