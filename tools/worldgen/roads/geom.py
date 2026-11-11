"""2D polyline helpers (metres, region-local or EPSG:2180 – callers decide)."""

from __future__ import annotations

import math

import numpy as np


def cumlen(p: np.ndarray) -> np.ndarray:
    d = np.hypot(*np.diff(p, axis=0).T)
    return np.concatenate([[0.0], np.cumsum(d)])


def resample(p: np.ndarray, step: float) -> np.ndarray:
    """Resample polyline at (almost) uniform spacing <= step, keeping both endpoints."""
    s = cumlen(p)
    L = s[-1]
    n = max(1, int(math.ceil(L / step - 1e-9)))
    t = np.linspace(0.0, L, n + 1)
    return np.column_stack([np.interp(t, s, p[:, 0]), np.interp(t, s, p[:, 1])])


def smooth_open(p: np.ndarray, sigma: float, step: float = 0.5) -> np.ndarray:
    """Gaussian smoothing of an open polyline with fixed endpoints (odd reflection at both ends).

    Odd reflection about an endpoint keeps the endpoint exactly and keeps the end tangent.
    """
    q = resample(p, step)
    if len(q) < 3 or sigma <= 0:
        return q
    r = int(math.ceil(3 * sigma / step))
    r = min(r, len(q) - 1)
    k = np.exp(-0.5 * (np.arange(-r, r + 1) * step / sigma) ** 2)
    k /= k.sum()
    head = 2 * q[0] - q[r:0:-1]
    tail = 2 * q[-1] - q[-2:-r - 2:-1]
    ext = np.vstack([head, q, tail])
    out = np.column_stack([np.convolve(ext[:, 0], k, mode="valid"), np.convolve(ext[:, 1], k, mode="valid")])
    out[0], out[-1] = q[0], q[-1]
    return out


def smooth_1d(v: np.ndarray, sigma_samples: float, mode: str = "nearest") -> np.ndarray:
    if sigma_samples <= 0 or len(v) < 3:
        return v.copy()
    from scipy.ndimage import gaussian_filter1d
    return gaussian_filter1d(v.astype(float), sigma_samples, mode=mode)


class Polyline:
    """Dense polyline with arc-length parametrisation, unit tangents, left normals, signed curvature."""

    def __init__(self, pts: np.ndarray):
        self.p = np.asarray(pts, float)
        self.s = cumlen(self.p)
        self.length = float(self.s[-1])
        d = np.gradient(self.p, axis=0)
        n = np.hypot(d[:, 0], d[:, 1])
        n[n == 0] = 1.0
        self.t = d / n[:, None]
        self.n = np.column_stack([-self.t[:, 1], self.t[:, 0]])
        ang = np.unwrap(np.arctan2(self.t[:, 1], self.t[:, 0]))
        ds = np.gradient(self.s)
        ds[ds == 0] = 1e-9
        self.kappa = np.gradient(ang) / ds

    def point(self, s):
        s = np.clip(np.asarray(s, float), 0.0, self.length)
        return np.stack([np.interp(s, self.s, self.p[:, 0]), np.interp(s, self.s, self.p[:, 1])], axis=-1)

    def frame(self, s):
        s = np.clip(np.asarray(s, float), 0.0, self.length)
        tx = np.interp(s, self.s, self.t[:, 0])
        ty = np.interp(s, self.s, self.t[:, 1])
        n = np.hypot(tx, ty)
        tx, ty = tx / n, ty / n
        t = np.stack([tx, ty], axis=-1)
        nn = np.stack([-ty, tx], axis=-1)
        return t, nn

    def curvature(self, s):
        return np.interp(np.clip(s, 0, self.length), self.s, self.kappa)

    def offset_point(self, s, lat):
        p = self.point(s)
        _, n = self.frame(s)
        return p + n * np.asarray(lat, float)[..., None]

    def project(self, q) -> tuple[float, float]:
        """(station, signed lateral) of the closest point; lateral > 0 = left."""
        q = np.asarray(q, float)
        a, b = self.p[:-1], self.p[1:]
        ab = b - a
        l2 = (ab ** 2).sum(1)
        l2[l2 == 0] = 1e-12
        t = np.clip(((q - a) * ab).sum(1) / l2, 0, 1)
        c = a + ab * t[:, None]
        d = np.hypot(*(q - c).T)
        i = int(d.argmin())
        s = self.s[i] + t[i] * math.sqrt(l2[i])
        cross = ab[i, 0] * (q[1] - a[i, 1]) - ab[i, 1] * (q[0] - a[i, 0])
        return float(s), float(math.copysign(d[i], cross))


def seg_intersect(p1, p2, q1, q2):
    """Intersection of segments p1p2 and q1q2 -> (t, u, point) or None."""
    r = p2 - p1
    s = q2 - q1
    den = r[0] * s[1] - r[1] * s[0]
    if abs(den) < 1e-12:
        return None
    qp = q1 - p1
    t = (qp[0] * s[1] - qp[1] * s[0]) / den
    u = (qp[0] * r[1] - qp[1] * r[0]) / den
    if -1e-9 <= t <= 1 + 1e-9 and -1e-9 <= u <= 1 + 1e-9:
        return t, u, p1 + t * r
    return None


def polyline_intersections(a: np.ndarray, b: np.ndarray):
    """All intersections between polylines a and b -> list of (s_a, s_b, point). O(n*m), small inputs."""
    sa, sb = cumlen(a), cumlen(b)
    out = []
    # bounding box prefilter per segment
    for i in range(len(a) - 1):
        p1, p2 = a[i], a[i + 1]
        lo = np.minimum(p1, p2) - 1e-6
        hi = np.maximum(p1, p2) + 1e-6
        bl = np.minimum(b[:-1], b[1:])
        bh = np.maximum(b[:-1], b[1:])
        cand = np.where((bl[:, 0] <= hi[0]) & (bh[:, 0] >= lo[0]) & (bl[:, 1] <= hi[1]) & (bh[:, 1] >= lo[1]))[0]
        for j in cand:
            r = seg_intersect(p1, p2, b[j], b[j + 1])
            if r is not None:
                t, u, pt = r
                out.append((sa[i] + t * (sa[i + 1] - sa[i]), sb[j] + u * (sb[j + 1] - sb[j]), pt))
    return out


def polygon_area(p: np.ndarray) -> float:
    x, y = p[:, 0], p[:, 1]
    return 0.5 * float(np.dot(x, np.roll(y, -1)) - np.dot(y, np.roll(x, -1)))


def ear_clip(poly: np.ndarray) -> list[tuple[int, int, int]]:
    """Ear-clipping triangulation of a simple polygon (any orientation). Returns CCW triangles."""
    n = len(poly)
    if n < 3:
        return []
    idx = list(range(n))
    if polygon_area(poly) < 0:
        idx.reverse()
    tris = []

    def cross(o, a, b):
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    guard = 0
    while len(idx) > 3 and guard < 10 * n * n:
        guard += 1
        m = len(idx)
        ear = False
        for k in range(m):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
            a, b, c = poly[i0], poly[i1], poly[i2]
            if cross(a, b, c) <= 1e-12:
                continue
            inside = False
            for j in idx:
                if j in (i0, i1, i2):
                    continue
                p = poly[j]
                if cross(a, b, p) >= -1e-12 and cross(b, c, p) >= -1e-12 and cross(c, a, p) >= -1e-12:
                    inside = True
                    break
            if inside:
                continue
            tris.append((i0, i1, i2))
            idx.pop(k)
            ear = True
            break
        if not ear:   # degenerate remainder: fan it
            for k in range(1, len(idx) - 1):
                tris.append((idx[0], idx[k], idx[k + 1]))
            return tris
    if len(idx) == 3:
        tris.append(tuple(idx))
    return tris


def dp_keep(P, tol):
    """Douglas-Peucker: boolean mask of the points of polyline P (n, 2 or 3) kept so that no dropped point lies
    further than `tol` from the simplified line (ADR 0110: guardrail beams and verge strips were meshed at every
    1 m station also on straights)."""
    P = np.asarray(P, float)
    n = len(P)
    keep = np.zeros(n, bool)
    if n == 0:
        return keep
    keep[[0, n - 1]] = True
    stack = [(0, n - 1)]
    while stack:
        a, b = stack.pop()
        if b - a < 2:
            continue
        ab = P[b] - P[a]
        l2 = float(ab @ ab)
        q = P[a + 1:b] - P[a]
        if l2 < 1e-18:
            d2 = (q * q).sum(1)
        else:
            t = np.clip((q @ ab) / l2, 0.0, 1.0)
            r = q - t[:, None] * ab[None, :]
            d2 = (r * r).sum(1)
        k = int(d2.argmax())
        if d2[k] > tol * tol:
            m = a + 1 + k
            keep[m] = True
            stack.append((a, m))
            stack.append((m, b))
    return keep
