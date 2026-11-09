"""Vertical alignment (niweleta) of every chain from the 1 m NMT, and crossfall.

Profile = Whittaker smoother of the NMT road-surface samples (median across the carriageway), with
hard constraints at junction nodes so all chains meeting at a node share its height. The smoothing
weight λ is increased until the vertical curvature satisfies the class minimum radius
(standards.VCURVE_MIN_R). Bridge stations carry zero data weight (NMT = ground under the deck), so the
deck is a smooth interpolation between the abutments (low confidence, flagged).
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


def node_heights(net, hf: Heightfield) -> dict:
    """Ground height at every chain-end node (median of NMT within 3 m); None on bridges."""
    zs = {}
    bridge_end = {}
    for c in net.chains:
        for node, i in ((c.node_a, 0), (c.node_b, -1)):
            bridge_end.setdefault(node, []).append(bool(c.bridge[i]))
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


def chain_profile(c, hf: Heightfield, z_a, z_b, rmin: float):
    s = c.line.s
    n = len(s)
    _, nrm = c.line.frame(s)
    offs = np.array([-0.7, -0.35, 0.0, 0.35, 0.7])
    samp = []
    for f in offs:
        q = c.line.p + nrm * (c.hw * f)[:, None]
        samp.append(hf.sample(q[:, 0], q[:, 1]))
    y = np.median(np.array(samp), axis=0)
    w = np.where(c.bridge, 0.0, 1.0)
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


def build_profiles(net, hf: Heightfield) -> dict:
    zn = node_heights(net, hf)
    stats = {}
    # pass 1: chains with known end heights; unknown (bridge) nodes get the mean of solved ends
    pending = {}
    for c in net.chains:
        rmin = min(S.VCURVE_MIN_R[net.sec_list[i].cls] for i in np.unique(c.sec_idx))
        za, zb = zn.get(c.node_a), zn.get(c.node_b)
        z, st = chain_profile(c, hf, za, zb, rmin)
        c.z = z
        stats[c.id] = st
        for node, zz in ((c.node_a, z[0]), (c.node_b, z[-1])):
            if zn.get(node) is None:
                pending.setdefault(node, []).append(float(zz))
    if pending:
        for node, vals in sorted(pending.items()):
            zn[node] = float(np.mean(vals))
        for c in net.chains:
            if c.node_a in pending or c.node_b in pending:
                rmin = min(S.VCURVE_MIN_R[net.sec_list[i].cls] for i in np.unique(c.sec_idx))
                c.z, stats[c.id] = chain_profile(c, hf, zn[c.node_a], zn[c.node_b], rmin)
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
