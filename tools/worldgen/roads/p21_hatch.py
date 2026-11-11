"""P-21 hatching as analytic quads (ADR 0100, REVIEW s10-0095 P0-1).

The ADR 0093/0095 zones were painted as ONE shapely polygon (border ring union stripes) cut by constrained
Delaunay with 1.5 m segmentisation and draped at the triangle corners only. Long thin triangles spanning a crowned
carriageway sank under the asphalt between their corners (paint lift 6 mm), so the stripes rendered as fragments,
"Z" shapes and empty frames (REVIEW s10-0095 P0-1). Here:

* every stripe is clipped to the zone analytically: the stripe box is intersected with the (inset) polygon and
  each piece is reduced to the quad spanned by the two stripe edge lines (pieces shorter than STRIPE_MIN_M on
  either edge = fragments at a tip, dropped);
* the stripe direction comes from ONE axis per zone (the direction of traffic along the zone): `chevron_axis`
  (polyline, stripes mirrored about it = jodelka / chevrons) or `axis` (polyline, parallel stripes at
  `stripe_rel_deg` to it); legacy `stripe_az_deg` (absolute) is still read;
* the border is a ring of quads with mitred (clamped) inner corners - one quad per polygon edge;
* every quad is draped as a strip of cells <= DRAPE_STEP_M long, sampled at every vertex.

Pure geometry (no mesh buffer) so tests can check "every stripe is a quad, stripes in a field are parallel".
"""

from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import LineString, Polygon

STRIPE_W_M = 0.5          # WORKING_VALUE: read off the 0.08 m orthophoto (ADR 0077)
STRIPE_GAP_M = 1.0        # WORKING_VALUE: same source
BORDER_W_M = 0.24         # = standards.LINE_W_WIDE
STRIPE_REL_DEG = 45.0     # WORKING_VALUE: stripe angle to the axis (traffic direction); orthophoto reads 40-50 deg
STRIPE_MIN_M = 0.35       # a stripe piece shorter than this on either edge is a fragment at a tip -> dropped
MITRE_MAX = 3.0           # border inner corner at most MITRE_MAX x width from the outer corner (acute tips)
DRAPE_STEP_M = 0.35       # quad cells along the stripe / border edge (crowned carriageway, lift 6 mm)
MAX_LIFT_M = 0.03         # a cell whose surface rises more than this above its lowest corner is over a step: dropped


def _unit(v):
    n = float(np.hypot(*v))
    return v / n if n > 1e-12 else v


def _left(v):
    return np.array([-v[1], v[0]])


def _ccw(P):
    P = np.asarray(P, float)
    a = 0.5 * float(np.sum(P[:, 0] * np.roll(P[:, 1], -1) - np.roll(P[:, 0], -1) * P[:, 1]))
    return P if a > 0 else P[::-1]


def border_quads(P, w=BORDER_W_M, edges=None):
    """[(4, 2) quad per polygon edge] of the border ring and the inner polygon (n, 2) the hatching fills.
    `edges`: indices i of the edges P[i] -> P[i+1] (authored order) that carry a border line (default: all)."""
    P = np.asarray(P, float)
    flip = not np.array_equal(_ccw(P), P)
    P = _ccw(P)
    n = len(P)
    inner = np.zeros_like(P)
    for i in range(n):
        a, b, c = P[i - 1], P[i], P[(i + 1) % n]
        n0, n1 = _left(_unit(b - a)), _left(_unit(c - b))      # inward normals of a CCW ring
        m = _unit(n0 + n1)
        cosh = float(np.dot(m, n0))
        d = w / max(cosh, 1e-6)
        if d > MITRE_MAX * w or float(np.dot(m, m)) < 0.5:
            d = MITRE_MAX * w
            if float(np.dot(m, m)) < 0.5:                     # reflex-straight / degenerate: plain normal
                m = n0
        inner[i] = b + m * d
    keep = range(n) if edges is None else {((n - 2 - int(e)) % n if flip else int(e) % n) for e in edges}
    quads = [np.array([P[i], P[(i + 1) % n], inner[(i + 1) % n], inner[i]]) for i in range(n) if i in keep]
    return quads, inner


def _axis_line(axis):
    A = np.asarray(axis, float)
    d0, d1 = _unit(A[1] - A[0]), _unit(A[-1] - A[-2])
    return np.vstack([A[0] - d0 * 500.0, A[1:-1], A[-1] + d1 * 500.0]) if len(A) > 2 else \
        np.vstack([A[0] - d0 * 500.0, A[-1] + d1 * 500.0])


def _pieces_quads(region, direction, origin, w=STRIPE_W_M, gap=STRIPE_GAP_M):
    """Analytic stripe quads of stripes running along `direction`, spaced from `origin`, clipped to `region`."""
    if region.is_empty:
        return []
    d = _unit(np.asarray(direction, float))
    nrm = _left(d)
    o = np.asarray(origin, float)
    minx, miny, maxx, maxy = region.bounds
    corners = np.array([[minx, miny], [maxx, miny], [maxx, maxy], [minx, maxy]])
    off = (corners - o) @ nrm
    along = (corners - o) @ d
    L0, L1 = float(along.min()) - 1.0, float(along.max()) + 1.0
    pitch = w + gap
    k0, k1 = int(math.floor(off.min() / pitch)) - 1, int(math.ceil(off.max() / pitch)) + 1
    out = []
    eps = 1e-6
    for k in range(k0, k1 + 1):
        c = k * pitch                       # stripe centre line offset
        ha, hb = c - w / 2, c + w / 2
        box = Polygon([o + d * L0 + nrm * ha, o + d * L1 + nrm * ha, o + d * L1 + nrm * hb, o + d * L0 + nrm * hb])
        piece = box.intersection(region)
        for pc in getattr(piece, "geoms", [piece]):
            if pc.is_empty or pc.geom_type != "Polygon" or pc.area < 1e-4:
                continue
            ends = []
            for h in (ha, hb):
                ln = LineString([o + d * L0 + nrm * (h + (eps if h == ha else -eps)),
                                 o + d * L1 + nrm * (h + (eps if h == ha else -eps))])
                seg = ln.intersection(pc)
                pts = [np.asarray(g.coords, float) for g in getattr(seg, "geoms", [seg])
                       if not g.is_empty and g.geom_type in ("LineString", "Point")]
                if not pts:
                    ends.append(None)
                    continue
                Q = np.vstack(pts)
                t = (Q - o) @ d
                ends.append((float(t.min()), float(t.max()), h))
            if any(e is None or e[1] - e[0] < STRIPE_MIN_M for e in ends):
                continue
            (a0, a1, ha_), (b0, b1, hb_) = ends
            q = np.array([o + d * a0 + nrm * ha_, o + d * a1 + nrm * ha_, o + d * b1 + nrm * hb_, o + d * b0 + nrm * hb_])
            out.append(q)
    return out


def hatch(o):
    """Geometry of a painted_zone override: {"border": [quads], "stripes": [quads], "fields": [(dir_deg, n)], "mode"}.

    Raises ValueError on a bad polygon (the caller turns it into overrides_stale)."""
    P = np.asarray(o.get("polygon_en") or [], float)
    if P.ndim != 2 or len(P) < 3:
        raise ValueError("polygon_en needs >= 3 points")
    pg = Polygon(P)
    if not pg.is_valid:
        raise ValueError("self-intersecting polygon: " + shapely.is_valid_reason(pg))
    if pg.area < 1.0:
        raise ValueError("polygon smaller than 1 m2")
    border, inner_pts = border_quads(P, edges=o.get("border_edges")) if o.get("border", True) else ([], _ccw(P))
    inner = Polygon(inner_pts)
    if not inner.is_valid or inner.is_empty:
        inner = pg.buffer(-BORDER_W_M, join_style=2)
    inner = inner.intersection(pg)
    rel = float(o.get("stripe_rel_deg", STRIPE_REL_DEG))
    sw, sg_ = float(o.get("stripe_w_m", STRIPE_W_M)), float(o.get("stripe_gap_m", STRIPE_GAP_M))
    # chevrons: the apex of every V points to `chevron_apex` (tip = first axis point, nose = last), read off the
    # orthophoto per zone (DK8 E -782: nose; s 1440 diverge: tip)
    apex = -1.0 if o.get("chevron_apex", "tip") == "nose" else 1.0
    stripes, fields, mode = [], [], "none"
    if not inner.is_empty and o.get("stripes", True):
        if o.get("chevron_axis"):
            mode = "chevron"
            A = np.asarray(o["chevron_axis"], float)
            ax = _axis_line(A)
            ln = LineString(ax)
            ext = float(np.hypot(*(np.asarray(pg.bounds[2:]) - np.asarray(pg.bounds[:2])))) + 10.0
            left = ln.buffer(ext, single_sided=True)
            right = ln.buffer(-ext, single_sided=True)
            # one stripe direction per side (the axis direction where the zone lies: first segment, i.e. at the tip)
            seg = _unit(A[1] - A[0])
            az = math.degrees(math.atan2(seg[1], seg[0]))
            for side, sg in ((left, 1.0), (right, -1.0)):
                part = inner.intersection(side)
                dd = az + apex * sg * rel
                q = _pieces_quads(part, (math.cos(math.radians(dd)), math.sin(math.radians(dd))), A[0], sw, sg_)
                stripes += q
                fields.append((round(dd, 2), len(q)))
        else:
            if o.get("axis"):
                A = np.asarray(o["axis"], float)
                seg = _unit(A[-1] - A[0])
                dd = math.degrees(math.atan2(seg[1], seg[0])) + rel   # rel < 0: clockwise from the axis
                mode = "axis"
            elif "stripe_az_deg" in o:
                dd = float(o["stripe_az_deg"])
                mode = "absolute"
            else:      # long side of the minimum rotated rectangle = traffic direction
                R = np.asarray(pg.minimum_rotated_rectangle.exterior.coords)[:4]
                e0, e1 = R[1] - R[0], R[2] - R[1]
                seg = _unit(e0 if np.hypot(*e0) >= np.hypot(*e1) else e1)
                dd = math.degrees(math.atan2(seg[1], seg[0])) + rel
                mode = "auto"
            cen = np.asarray(pg.centroid.coords[0])
            q = _pieces_quads(inner, (math.cos(math.radians(dd)), math.sin(math.radians(dd))), cen, sw, sg_)
            stripes += q
            fields.append((round(dd, 2), len(q)))
    return {"border": border, "stripes": stripes, "fields": fields, "mode": mode, "polygon": pg}


def drape_quad(q, step=DRAPE_STEP_M):
    """Plan vertices (2(n+1), 2) and triangles of quad q split into n cells along its longer pair of sides."""
    q = np.asarray(q, float)
    la = max(float(np.hypot(*(q[1] - q[0]))), float(np.hypot(*(q[2] - q[3]))))
    lb = max(float(np.hypot(*(q[3] - q[0]))), float(np.hypot(*(q[2] - q[1]))))
    if lb > la:                              # make q[0]->q[1] the long side
        q = q[[1, 2, 3, 0]]
        la = lb
    n = max(1, int(math.ceil(la / step)))
    u = np.linspace(0.0, 1.0, n + 1)[:, None]
    A = q[0] + (q[1] - q[0]) * u
    B = q[3] + (q[2] - q[3]) * u
    V = np.concatenate([A[:, None], B[:, None]], axis=1).reshape(-1, 2)
    T = []
    for i in range(n):
        a, b, c, d = 2 * i, 2 * i + 2, 2 * i + 3, 2 * i + 1
        T += [(a, b, c), (a, c, d)]
    T = np.asarray(T, np.int64)
    p = V[T]
    cr = (p[:, 1, 0] - p[:, 0, 0]) * (p[:, 2, 1] - p[:, 0, 1]) - (p[:, 1, 1] - p[:, 0, 1]) * (p[:, 2, 0] - p[:, 0, 0])
    T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
    return V, T


def drape_lift(top, V, T):
    """Drape plan cells (V (n, 2), T (m, 3)) on `top` (through_lines._Top) so the paint plane never dips under the
    surface: z at every vertex; each cell sampled at its centroid and edge midpoints and its corners lifted by the
    largest excess of the surface over the paint plane there (junction plates and chain ribbons overlap with cm
    differences, the carriageway is crowned). Cells with a corner off the carriageway or over a step > MAX_LIFT_M are
    dropped. Returns (z (n,), T kept, cells dropped, max lift)."""
    z = top.z(V)
    ok = np.isfinite(z)
    keep = ok[T].all(1)
    lost = int((~keep).sum())
    T = T[keep]
    if not len(T):
        return z, T, lost, 0.0
    P3, Z3 = V[T], z[T]
    smp = np.concatenate([P3.mean(1)[:, None], 0.5 * (P3 + np.roll(P3, -1, axis=1))], axis=1)
    zpl = np.concatenate([Z3.mean(1)[:, None], 0.5 * (Z3 + np.roll(Z3, -1, axis=1))], axis=1)
    zs = top.z(smp.reshape(-1, 2)).reshape(len(T), 4)
    under = np.where(np.isfinite(zs), zs - zpl, 0.0).max(1)
    step = under > MAX_LIFT_M
    lost += int(step.sum())
    T, under = T[~step], np.maximum(under[~step], 0.0)
    lift = np.zeros(len(V))
    for k in range(3):
        np.maximum.at(lift, T[:, k], under)
    return z + lift, T, lost, float(under.max()) if len(under) else 0.0
