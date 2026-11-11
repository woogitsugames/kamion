"""Pitched roofs of houses over the real footprint (ADR 0091): gable, hip, mono-pitch.

The roof is a height field over the plan, defined in the frame of a rectangle R (centre c, unit axes eu / ev, half
sizes hu / hv; ev = across the ridge):
    gable  z = zeave + s * (hv - |v|)                      ridge along eu at v = 0
    hip    z = zeave + s * min(hv - |v|, hu - |u|)         (hu >= hv; ridge shortened by hv at both ends)
    mono   z = zeave + s * (v + hv)                        high side at v = +hv (the party wall of a semi / terrace)
The roof covering is the footprint grown by the overhang, cut along the creases of the height field; the walls of
the footprint rise to the field (gable ends and the taller walls of re-entrant corners come out by themselves), so an
L- or T-shaped house keeps its real plan instead of being replaced by its bounding rectangle.

Heights (measured on the 229 houses of bialystok-industrial-c that have GUGiK LoD2 2017 data, see the ADR):
the LoD1 2024 height of a pitched house is not the ridge but about eave + 0.55 x (ridge - eave) (p10 / p50 / p90 =
0.46-0.49 / 0.54-0.59 / 0.73), LoD2 ridge / LoD1 height = 1.2-1.24 median. So the ridge comes from `height_lod2_2017_m`
and the eave from `lod2_eave_rel_m` when present; otherwise both are derived from the LoD1 height with K_LOD1 and the
default pitch (WORKING_VALUE = the median of the measured pitches, 36 deg for type 1030 n = 15, 46 deg for 1130 n = 157).
"""
from __future__ import annotations

import math

import numpy as np
import shapely
from shapely.geometry import Point, Polygon

K_LOD1 = 0.55                   # (LoD1 height - eave) / (ridge - eave), measured (module docstring)
PITCH_DEFAULT = {"gable": 40.0, "hip": 30.0, "mono": 25.0}      # deg, WORKING_VALUE (gable: between the two medians)
PITCH_RANGE = {"gable": (22.0, 50.0), "hip": (18.0, 40.0), "mono": (8.0, 45.0)}
OVERHANG = 0.5                  # eaves / verge overhang, m (WORKING_VALUE: 0.4-0.7 m is the usual Polish house eave)
T_TOP = 0.14                    # covering + battens above the structural plane (= wall top), m
T_SOFFIT = 0.04                 # soffit below the structural plane, m -> fascia board 0.18 m
EAVE_MIN = 2.5                  # lowest eave above the ground, m
# ADR 0094: overhang of a wall that faces UP the roof, m. The roof is one height field over the whole plan, so in the
# re-entrant corner of an L / T plan a wall can face the ridge: the field rises away from it and a full 0.5 m overhang
# there stuck out above the lower wing like a dark sail (review s9 P1-4); 0.15 m = a flashing, not an eave
OVERHANG_NOTCH = 0.15
MULTI = True                    # ADR 0097: rectangle decomposition + upper envelope for L / T / U plans (MultiRoof)


class Roof:
    def __init__(self, kind, c, eu, ev, hu, hv, slope, zeave, source):
        self.kind, self.c, self.eu, self.ev = kind, np.asarray(c, float), np.asarray(eu, float), np.asarray(ev, float)
        self.hu, self.hv, self.s, self.zeave, self.source = float(hu), float(hv), float(slope), float(zeave), source
        self.sl = math.sqrt(1.0 + self.s * self.s)       # slope length per plan metre

    def uv(self, p):
        q = np.asarray(p, float)[..., :2] - self.c
        return q @ self.eu, q @ self.ev

    def d(self, p):
        u, v = self.uv(p)
        if self.kind == "gable":
            return self.hv - np.abs(v)
        if self.kind == "hip":
            return np.minimum(self.hv - np.abs(v), self.hu - np.abs(u))
        return v + self.hv

    def z(self, p):
        """Structural plane (wall top) above the plan point(s) p."""
        return self.zeave + self.s * self.d(p)

    def eave_dist(self, p):
        """Plan distance on the slope above the eave line (0 on an eave)."""
        return self.d(p)

    def ridge_lines(self, ov):
        """Ridge / hip lines [(p0, p1)] of the covering grown by ov (caps, ADR 0094)."""
        lines = []
        if self.kind in ("gable", "hip"):
            k = self.hu + ov if self.kind == "gable" else self.hu - self.hv
            W = lambda u, v: self.c + self.eu * u + self.ev * v
            lines.append((W(-k, 0.0), W(k, 0.0)))
            if self.kind == "hip":
                hu, hv = self.hu + ov, self.hv + ov
                lines += [(W(sx * k, 0.0), W(sx * hu, sy * hv)) for sx in (-1, 1) for sy in (-1, 1)]
        return lines

    def valley_lines(self, ov):
        return []

    @property
    def zridge(self):
        return self.zeave + self.s * (2 * self.hv if self.kind == "mono" else self.hv)

    def _creases(self):
        """Crease lines a u + b v = c of the height field."""
        if self.kind == "gable":
            return [(0.0, 1.0, 0.0)]
        if self.kind == "hip":
            k = self.hu - self.hv
            return [(0.0, 1.0, 0.0), (1.0, -1.0, k), (1.0, -1.0, -k), (1.0, 1.0, k), (1.0, 1.0, -k)]
        return []

    def profile(self, a, b):
        """Wall top along the plan edge a -> b: [(distance from a, z)], linear between the entries."""
        a, b = np.asarray(a, float)[:2], np.asarray(b, float)[:2]
        L = float(np.hypot(*(b - a)))
        ts = {0.0, 1.0}
        ua, va = self.uv(a)
        ub, vb = self.uv(b)
        for ca, cb, cc in self._creases():
            ga, gb = ca * ua + cb * va - cc, ca * ub + cb * vb - cc
            if ga * gb < 0:
                t = ga / (ga - gb)
                if 0.02 / max(L, 1e-6) < t < 1 - 0.02 / max(L, 1e-6):
                    ts.add(float(t))
        return [(t * L, float(self.z(a + (b - a) * t))) for t in sorted(ts)]

    def faces(self, ov):
        """Planar faces of the covering over R grown by ov: [(plan polygon, eave direction, d0)] with
        d0(p) = plan distance from the face's (grown) eave line, for the UV up the slope."""
        hu, hv = self.hu + ov, self.hv + ov
        W = lambda u, v: tuple(self.c + self.eu * u + self.ev * v)
        P = lambda *uv: Polygon([W(*q) for q in uv])
        eu, ev = self.eu, self.ev
        if self.kind == "mono":
            top = self.hv + 0.03                 # no overhang past the party wall (the neighbour's half starts there)
            return [(P((-hu, -hv), (hu, -hv), (hu, top), (-hu, top)), eu, lambda p: self.uv(p)[1] + hv)]
        if self.kind == "gable":
            return [(P((-hu, 0), (hu, 0), (hu, hv), (-hu, hv)), eu, lambda p: hv - self.uv(p)[1]),
                    (P((-hu, -hv), (hu, -hv), (hu, 0), (-hu, 0)), eu, lambda p: hv + self.uv(p)[1])]
        k = self.hu - self.hv
        return [(P((-k, 0), (k, 0), (hu, hv), (-hu, hv)), eu, lambda p: hv - self.uv(p)[1]),
                (P((-hu, -hv), (hu, -hv), (k, 0), (-k, 0)), eu, lambda p: hv + self.uv(p)[1]),
                (P((k, 0), (hu, -hv), (hu, hv)), ev, lambda p: hu - self.uv(p)[0]),
                (P((-k, 0), (-hu, hv), (-hu, -hv)), ev, lambda p: hu + self.uv(p)[0])]


def _clip_half(coords, nrm, k):
    """Convex polygon (list of xy) clipped to the half-plane nrm . p + k > 0 (Sutherland-Hodgman)."""
    out = []
    n = len(coords)
    for i in range(n):
        a, b = coords[i], coords[(i + 1) % n]
        fa, fb = float(nrm @ a + k), float(nrm @ b + k)
        if fa > 0:
            out.append(a)
        if (fa > 0) != (fb > 0):
            t = fa / (fa - fb)
            out.append(a + (b - a) * t)
    return out


class MultiRoof:
    """ADR 0097 (review 0094 P1-c): gable roofs over a rectangle decomposition of an L / T / U plan. Every part is a
    gable over its own rectangle (wings that meet the main body on its long side run their rectangle on to the main
    ridge); the roof is the UPPER ENVELOPE of the parts: z(p) = max over the parts whose rectangle (grown by the
    overhang) holds p. The max of two roof planes folds upwards, so where a wing roof runs into the main slope the
    envelope makes the valley (kosz) by itself, and the wing ridge dies into the main slope below the main ridge.
    Same interface as Roof (z, profile, faces, eave_dist, ridge_lines, valley_lines)."""
    kind = "gable"

    def __init__(self, parts, source):
        self.parts = parts                         # Roof("gable", ...) each; parts[0] = the main body
        m = parts[0]
        self.c, self.eu, self.ev, self.hu, self.hv, self.s, self.sl = m.c, m.eu, m.ev, m.hu, m.hv, m.s, m.sl
        self.zeave, self.source = m.zeave, source
        self._faces = {}
        self._regions = []

    @property
    def zridge(self):
        return max(p.zridge for p in self.parts)

    def _inside(self, part, q, ov):
        u, v = part.uv(q)
        return (np.abs(u) <= part.hu + ov + 1e-6) & (np.abs(v) <= part.hv + ov + 1e-6)

    def z(self, p, ov=None):
        ov = OVERHANG + 0.05 if ov is None else ov
        q = np.asarray(p, float)[..., :2]
        best = np.full(q.shape[:-1], -np.inf)
        for part in self.parts:
            zi = part.z(q)
            best = np.where(self._inside(part, q, ov) & (zi > best), zi, best)
        return np.where(np.isfinite(best), best, self.parts[0].z(q))

    def eave_dist(self, p):
        return (self.z(p) - self.zeave) / self.s

    def d(self, p):
        return self.eave_dist(p)

    def _planes(self):
        """[(grad xy, const)]: face planes z = grad . p + const of every part."""
        out = []
        for pt in self.parts:
            for sg in (1, -1):
                out.append((-sg * pt.s * pt.ev, pt.zeave + pt.s * pt.hv + sg * pt.s * float(pt.ev @ pt.c)))
        return out

    def profile(self, a, b):
        a, b = np.asarray(a, float)[:2], np.asarray(b, float)[:2]
        L = float(np.hypot(*(b - a)))
        ts = {0.0, 1.0}
        pl = self._planes()
        for i in range(len(pl)):                           # plane switches along the edge
            for j in range(i + 1, len(pl)):
                fa = float((pl[i][0] - pl[j][0]) @ a + pl[i][1] - pl[j][1])
                fb = float((pl[i][0] - pl[j][0]) @ b + pl[i][1] - pl[j][1])
                if fa * fb < 0:
                    ts.add(fa / (fa - fb))
        for pt in self.parts:                              # rectangle (domain) edges: a step in the field
            for ax, h in ((pt.eu, pt.hu), (pt.ev, pt.hv)):
                for sg in (1, -1):
                    fa = float(ax @ (a - pt.c)) - sg * (h + OVERHANG + 0.05)
                    fb = float(ax @ (b - pt.c)) - sg * (h + OVERHANG + 0.05)
                    if fa * fb < 0:
                        t = fa / (fa - fb)
                        ts.update((max(0.0, t - 1e-4), min(1.0, t + 1e-4)))
        tt = np.array(sorted(ts))
        keep_t = [tt[0]]
        for t in tt[1:]:
            if (t - keep_t[-1]) * L > 0.02:
                keep_t.append(t)
        if keep_t[-1] < 1.0:
            keep_t[-1] = 1.0
        tt = np.array(keep_t)
        zz = self.z(a[None, :] + (b - a)[None, :] * tt[:, None])
        keep = [0]                                         # drop collinear interior points
        for k in range(1, len(tt) - 1):
            t0, t1 = tt[keep[-1]], tt[k + 1]
            zi = zz[keep[-1]] + (zz[k + 1] - zz[keep[-1]]) * (tt[k] - t0) / max(t1 - t0, 1e-9)
            if abs(zi - zz[k]) > 0.01:
                keep.append(k)
        keep.append(len(tt) - 1)
        return [(float(tt[k] * L), float(zz[k])) for k in keep]

    def faces(self, ov):
        """Upper-envelope regions: [(plan polygon, eave direction, d0)] - each face of each part minus where another
        part's face is higher (ties: the earlier part wins)."""
        key = round(float(ov), 4)
        if key in self._faces:
            return self._faces[key]
        dom = []
        for i, pt in enumerate(self.parts):
            hu, hv = pt.hu + ov, pt.hv + ov
            W = lambda u, v, pt=pt: pt.c + pt.eu * u + pt.ev * v
            for sg in (1, -1):
                cs = [W(-hu, 0), W(hu, 0), W(hu, sg * hv), W(-hu, sg * hv)]
                g = -sg * pt.s * pt.ev
                k = pt.zeave + pt.s * pt.hv + sg * pt.s * float(pt.ev @ pt.c)
                dom.append((i, sg, cs, g, k))
        out, regions = [], []
        for i, sg, cs, g, k in dom:
            reg = Polygon(cs).buffer(0)
            for j, sg2, cs2, g2, k2 in dom:
                if j == i:
                    continue
                eps = 1e-4 if j < i else -1e-4             # earlier part wins ties
                cut = _clip_half([np.asarray(q) for q in cs2], g2 - g, k2 - k + eps)
                if len(cut) >= 3:
                    reg = reg.difference(Polygon(cut).buffer(0))
                if reg.is_empty:
                    break
            if reg.is_empty or reg.area < 1e-3:
                continue
            pt = self.parts[i]
            hv = pt.hv + ov
            k_sl = pt.sl / self.sl
            if sg > 0:
                d0 = lambda p, pt=pt, hv=hv, k_sl=k_sl: (hv - pt.uv(p)[1]) * k_sl
            else:
                d0 = lambda p, pt=pt, hv=hv, k_sl=k_sl: (hv + pt.uv(p)[1]) * k_sl
            out.append((reg, pt.eu, d0))
            regions.append((i, reg))
        self._faces[key] = out
        self._regions = regions
        return out

    def ridge_lines(self, ov):
        self.faces(ov + 0.05)
        out = []
        for i, pt in enumerate(self.parts):
            top = shapely.unary_union([r for j, r in self._regions if j == i]).buffer(0.02)
            seg = top.intersection(shapely.LineString([pt.c - pt.eu * (pt.hu + ov), pt.c + pt.eu * (pt.hu + ov)]))
            for ls in getattr(seg, "geoms", [seg]):
                if ls.geom_type == "LineString" and ls.length > 0.3:
                    out.append(tuple(np.asarray(c_) for c_ in ls.coords[:2]))
        return out

    def valley_lines(self, ov):
        """Shared boundaries of the regions of different parts (the valleys of the envelope) [(p0, p1)]."""
        self.faces(ov + 0.05)
        out = []
        regs = self._regions
        for a_ in range(len(regs)):
            for b_ in range(a_ + 1, len(regs)):
                if regs[a_][0] == regs[b_][0]:
                    continue
                sh = regs[b_][1].boundary.intersection(regs[a_][1].buffer(0.01))
                lines = [g for g in getattr(sh, "geoms", [sh]) if g.geom_type in ("LineString", "MultiLineString")]
                if not lines:
                    continue
                sh = shapely.line_merge(shapely.unary_union(lines))
                for ls in getattr(sh, "geoms", [sh]):
                    if ls.geom_type != "LineString" or ls.length < 0.3:
                        continue
                    cs = np.asarray(ls.coords)
                    for k in range(len(cs) - 1):
                        q0, q1 = cs[k], cs[k + 1]
                        # a valley climbs from the eave to a ridge; the touching edges of two overhangs are level
                        if np.hypot(*(q1 - q0)) > 0.3 and abs(float(self.z(q1)) - float(self.z(q0))) > 0.2:
                            out.append((q0, q1))
        return out


def decompose(poly, c, eu, ev, tol=0.5, max_parts=4):
    """Rectangle decomposition of a near-rectilinear plan in the frame (c, eu, ev): [[u0, u1, v0, v1]] in frame
    coordinates, largest first, or None (not rectilinear within ~11 deg, too many grid lines or parts). Grid lines =
    clustered (tol) coordinates of the plan's edges; cells whose centre is inside are filled; rectangles are taken
    greedily by area."""
    ring = np.asarray(poly.exterior.coords)[:-1] - c
    uv = np.column_stack([ring @ eu, ring @ ev])
    us, vs = [], []
    for k in range(len(uv)):
        a, b = uv[k], uv[(k + 1) % len(uv)]
        du, dv = abs(b[0] - a[0]), abs(b[1] - a[1])
        ln = math.hypot(du, dv)
        if ln < 0.6:
            continue
        if min(du, dv) / ln > 0.2:
            return None
        if du > dv:
            vs.append(0.5 * (a[1] + b[1]))
        else:
            us.append(0.5 * (a[0] + b[0]))

    def cluster(xs):
        out = []
        for x in sorted(xs):
            if out and x - out[-1][-1] < tol:
                out[-1].append(x)
            else:
                out.append([x])
        return [float(np.mean(g)) for g in out]
    U, V = cluster(us), cluster(vs)
    if len(U) < 2 or len(V) < 2 or len(U) > 8 or len(V) > 8:
        return None
    pl = Polygon(uv)
    fill = np.array([[pl.contains(Point(0.5 * (U[i] + U[i + 1]), 0.5 * (V[j] + V[j + 1]))) for j in range(len(V) - 1)]
                     for i in range(len(U) - 1)])
    if not fill.any():
        return None
    parts = []
    while fill.any():
        best = None
        nu, nv = fill.shape
        for i0 in range(nu):
            for i1 in range(i0, nu):
                for j0 in range(nv):
                    for j1 in range(j0, nv):
                        if fill[i0:i1 + 1, j0:j1 + 1].all():
                            ar = (U[i1 + 1] - U[i0]) * (V[j1 + 1] - V[j0])
                            if best is None or ar > best[0] + 1e-9:
                                best = (ar, i0, i1, j0, j1)
        _, i0, i1, j0, j1 = best
        fill[i0:i1 + 1, j0:j1 + 1] = False
        parts.append([U[i0], U[i1 + 1], V[j0], V[j1 + 1]])
        if len(parts) > max_parts:
            return None
    return parts


def plan_multi(poly, c, eu, ev, heights):
    """MultiRoof of a near-rectilinear L / T / U house plan, or None. heights(main half span) -> (slope, eave above
    zref, source): the LoD2 / LoD1 height rules of a single roof applied to the main body's span. Returns
    (parts as [u0, u1, v0, v1, ridge along u], slope, eave rel, source) - the caller builds the MultiRoof."""
    parts = decompose(poly, c, eu, ev)
    if parts is None or len(parts) < 2:
        return None
    m = parts[0]
    if (m[1] - m[0]) * (m[3] - m[2]) < 0.4 * poly.area:
        return None
    along_u = (m[1] - m[0]) >= (m[3] - m[2])          # main ridge along u
    hv_m = 0.5 * ((m[3] - m[2]) if along_u else (m[1] - m[0]))
    if hv_m < 1.5:
        return None
    s, he, source = heights(hv_m)
    rects = []
    tolc = 0.05
    for k, (u0, u1, v0, v1) in enumerate(parts):
        if k == 0:
            rects.append((u0, u1, v0, v1, along_u))
            continue
        side_v = (abs(v0 - m[3]) < tolc or abs(v1 - m[2]) < tolc) and u1 > m[0] + 0.5 and u0 < m[1] - 0.5
        side_u = (abs(u0 - m[1]) < tolc or abs(u1 - m[0]) < tolc) and v1 > m[2] + 0.5 and v0 < m[3] - 0.5
        wu, wv = u1 - u0, v1 - v0
        if (along_u and side_v) or (not along_u and side_u):   # on the main body's long (eave) side: a wing
            depth, width = (wv, wu) if along_u else (wu, wv)
            perp = depth >= 0.4 * width                     # gable end out (the usual L / T); shallow bay: parallel
            if perp:
                if along_u:                                 # run the wing on to the main ridge
                    vm = 0.5 * (m[2] + m[3])
                    v0, v1 = (vm, v1) if v0 >= m[3] - tolc else (v0, vm)
                else:
                    um = 0.5 * (m[0] + m[1])
                    u0, u1 = (um, u1) if u0 >= m[1] - tolc else (u0, um)
            rects.append((u0, u1, v0, v1, (not along_u) if perp else along_u))
        else:                                               # on a gable end / not touching: its own long axis
            rects.append((u0, u1, v0, v1, wu >= wv))
    return rects, s, he, source


def _multi_roof(c, eu, ev, rects, s, zeave, source):
    roofs = []
    zr_m = None
    for k, (u0, u1, v0, v1, ru) in enumerate(rects):
        cc = c + eu * 0.5 * (u0 + u1) + ev * 0.5 * (v0 + v1)
        e_u, e_v = (eu, ev) if ru else (ev, -eu)
        hu_, hv_ = (0.5 * (u1 - u0), 0.5 * (v1 - v0)) if ru else (0.5 * (v1 - v0), 0.5 * (u1 - u0))
        if hv_ < 0.4:
            return None
        sk = s
        if k == 0:
            zr_m = zeave + s * hv_
        elif zeave + s * hv_ > zr_m - 0.3:                  # a wing never rises to the main ridge
            sk = (zr_m - 0.3 - zeave) / hv_
            if sk < math.tan(math.radians(15.0)):
                return None
        roofs.append(Roof("gable", cc, e_u, e_v, hu_, hv_, sk, zeave, source))
    return MultiRoof(roofs, source + "+multi")


def _frame(poly):
    """(centre, long axis, half long, half short) of the minimum rotated rectangle."""
    r = np.asarray(poly.minimum_rotated_rectangle.exterior.coords)[:4]
    e0, e1 = r[1] - r[0], r[2] - r[1]
    l0, l1 = float(np.hypot(*e0)), float(np.hypot(*e1))
    c = r.mean(0)
    if l0 >= l1:
        return c, e0 / max(l0, 1e-6), l0 / 2, l1 / 2
    return c, e1 / max(l1, 1e-6), l1 / 2, l0 / 2


def _party_side(poly, c, eu, hu, hv, others):
    """Side of R that carries a party wall: (outward unit normal, shared length m) of the side with the longest
    contact with a neighbouring footprint (within 0.4 m), or None."""
    ev = np.array([-eu[1], eu[0]])
    best = None
    for n, t, hn, ht in ((ev, eu, hv, hu), (-ev, eu, hv, hu), (eu, ev, hu, hv), (-eu, ev, hu, hv)):
        m = c + n * hn
        strip = shapely.LineString([m - t * ht, m + t * ht]).buffer(0.4, cap_style="flat")
        ln = sum(o.boundary.intersection(strip).length for o in others if o.intersects(strip))
        if ln > 2.0 and (best is None or ln > best[1]):
            best = (n, float(ln))
    return best


def plan(poly, props, h, zref, key_float, others=(), wooden=False):
    """Roof of a house footprint, or None = flat roof (LoD2 type 1000, footprints with courtyards or far from
    their rectangle). props: buildings.geojson properties; h: LoD1 height; key_float(salt) -> [0, 1) per building;
    others: neighbouring footprints (party-wall test of mono-pitch halves)."""
    rt = props.get("roof_type_lod2")
    rect = poly.minimum_rotated_rectangle
    if rt == "1000" or poly.interiors or poly.area > 400:
        return None
    c, eu, hu, hv = _frame(poly)
    ev = np.array([-eu[1], eu[0]])
    fill = poly.area / max(rect.area, 1e-6)
    # ADR 0097: plans far from their rectangle (L / T / U) get a MultiRoof when the LoD2 type allows a gable
    if fill < 0.6 and (rt not in ("1030", "1130", None) or wooden or not MULTI):
        return None
    if hv < 1.5 and fill >= 0.6:
        return None
    kind = "gable"
    if rt == "1010":
        ps = _party_side(poly, c, eu, hu, hv, others)
        if ps is not None:                       # the half of a semi-detached pair: high side at the party wall
            kind = "mono"
            n = ps[0]
            if abs(float(n @ eu)) > 0.5:         # party wall on a short side: slope along the long axis
                hu, hv = hv, hu
            ev = n
            eu = np.array([ev[1], -ev[0]])
    elif rt in ("1040", "1070"):
        kind = "hip"
    elif not wooden and rt in ("1130", None) and hu / hv < 1.25 and key_float("hip") < (0.6 if rt == "1130" else 0.3):
        kind = "hip"                             # squarish 'kostka' with an envelope roof (share WORKING_VALUE)
    hr, he0 = props.get("height_lod2_2017_m"), props.get("lod2_eave_rel_m")
    lo, hi = (math.tan(math.radians(x)) for x in PITCH_RANGE[kind])
    s0 = math.tan(math.radians(PITCH_DEFAULT[kind]))

    def heights(span):
        he = he0
        source = "lod2"
        if hr and hr > EAVE_MIN + 0.8:
            if not (he and EAVE_MIN - 0.1 <= he <= hr - 0.8):      # no usable eave (porch roofs give 1.6-2.3 m)
                he = (h - K_LOD1 * hr) / (1 - K_LOD1)
                source = "lod2_ridge"
            he = min(max(he, EAVE_MIN), hr - 0.8)
            s = min(max((hr - he) / span, lo), hi)
        else:                                        # no LoD2: LoD1 height = eave + K_LOD1 x rise
            s = s0
            he = h - K_LOD1 * s * span
            source = "lod1"
            if he < EAVE_MIN:                        # low house: keep the eave, flatten the roof to the measured height
                he = EAVE_MIN
                s = min(max((h - he) / (K_LOD1 * span), lo), hi)
        return s, he, source
    if kind == "gable" and MULTI:                # ADR 0097: L / T / U plans get a roof per wing (valleys)
        pm = plan_multi(poly, c, eu, ev, heights)
        if pm is not None:
            mr = _multi_roof(c, eu, ev, pm[0], pm[1], zref + pm[2], pm[3])
            if mr is not None:
                return mr
    if fill < 0.6 or hv < 1.5:
        return None
    s, he, source = heights(2 * hv if kind == "mono" else hv)      # plan run eave -> ridge
    return Roof(kind, c, eu, ev, hu, hv, s, zref + he, source)


def _tris(g):
    tri = shapely.constrained_delaunay_triangles(g)
    T = np.array([np.asarray(t.exterior.coords)[:3] for t in tri.geoms if t.area > 1e-6])
    if not len(T):
        return T
    cr = (T[:, 1, 0] - T[:, 0, 0]) * (T[:, 2, 1] - T[:, 0, 1]) - (T[:, 1, 1] - T[:, 0, 1]) * (T[:, 2, 0] - T[:, 0, 0])
    T[cr < 0] = T[cr < 0][:, [0, 2, 1]]
    return T


def _polys(g):
    return [x for x in getattr(g, "geoms", [g]) if x.geom_type == "Polygon" and x.area > 1e-4]


def covering(poly, roof, ov=OVERHANG):
    """Plan outline of the roof covering: the footprint grown by the overhang; along the walls that face up the
    roof (the height field rises away from the wall) only by OVERHANG_NOTCH. Eaves and verges - also those of a
    re-entrant corner - keep the full overhang (r1-r3 of ADR 0094 cut everything inside the convex hull's notches and
    left a wedge of the verge standing at the hull line)."""
    exp = poly.buffer(ov, join_style="mitre", mitre_limit=2.5)
    c = np.asarray(shapely.geometry.polygon.orient(poly).exterior.coords)
    cut = []
    for a, b in zip(c, c[1:]):
        L = float(np.hypot(*(b - a)))
        if L < 0.3:
            continue
        n = np.array([b[1] - a[1], a[0] - b[0]]) / L                # outward (CCW ring)
        m = 0.5 * (a + b)
        if float(roof.z(m + n * ov)) - float(roof.z(m)) > 0.1 * ov:
            cut.append(Polygon([a + n * OVERHANG_NOTCH, b + n * OVERHANG_NOTCH, b + n * (ov + 0.2), a + n * (ov + 0.2)]))
    if cut:
        parts = _polys(exp.difference(shapely.unary_union(cut)))
        if parts:
            exp = max(parts, key=lambda g: g.area)
    return exp


def build(acc, roof, poly, mat, fascia_mat="hall_flashing", ov=OVERHANG, low_layer="buildings_low", soffit_mat=None):
    """Roof covering (LOD0, LOD1, collision), soffit and fascia (LOD0). Returns the horizontal eave edges
    [(a, b, z_top)] of the covering (outward normal = right of a -> b) for the gutters.
    soffit_mat: material of the soffit under the overhang (default = fascia_mat)."""
    exp = covering(poly, roof, ov)
    soffit_mat = soffit_mat or fascia_mat
    eaves = []
    for face, e, d0 in roof.faces(ov + 0.05):
        for g in _polys(exp.intersection(face)):
            T = _tris(g)
            if not len(T):
                continue
            xy = T.reshape(-1, 2)
            V = np.column_stack([xy, roof.z(xy) + T_TOP])
            UV = np.column_stack([xy @ e, np.asarray(d0(xy)) * roof.sl])
            idx = np.arange(len(V)).reshape(-1, 3)
            acc.add("buildings", mat, V, idx, UV)
            acc.add(low_layer, mat, V, idx, UV)
            acc.add("collision", "collision_building", V, idx, UV)
            ring = np.asarray(shapely.geometry.polygon.orient(g).exterior.coords)
            for a, b in zip(ring, ring[1:]):
                if np.hypot(*(b - a)) < 0.02 or exp.exterior.distance(Point(*(0.5 * (a + b)))) > 1e-3:
                    continue
                za, zb = float(roof.z(a)), float(roof.z(b))
                acc.quad("buildings", fascia_mat, [a[0], a[1], za - T_SOFFIT], [b[0], b[1], zb - T_SOFFIT],
                         [b[0], b[1], zb + T_TOP], [a[0], a[1], za + T_TOP])
                if (abs(za - zb) < 0.01 and np.hypot(*(b - a)) > 1.5 and float(roof.eave_dist(0.5 * (a + b))) < 0.1 and
                        abs(float((b - a) @ e)) > 0.9 * np.hypot(*(b - a))):
                    eaves.append((a, b, za + T_TOP))
            for sg in _polys(g.difference(poly)):                    # soffit under the overhang, facing down
                S = _tris(sg)
                if len(S):
                    sxy = S[:, [0, 2, 1]].reshape(-1, 2)
                    # UV0.v >= 3 m: wall materials read v as metres above the ground (splash zone)
                    suv = np.column_stack([sxy[:, 0], sxy[:, 1] - np.floor(sxy[:, 1].min()) + 3.0])
                    acc.add("buildings", soffit_mat, np.column_stack([sxy, roof.z(sxy) - T_SOFFIT]),
                            np.arange(len(sxy)).reshape(-1, 3), suv)
    # ridge and hip caps (gąsiory, ADR 0094 - review s9 P2-3 "knife-edge ridge"): a three-facet cap 0.22 m wide and
    # 5 cm proud along every ridge / hip line of the height field, where the covering exists. LOD0, the roof's own
    # material; UV0 turned by 90 deg, so the course lines of the set become the joints between the cap tiles.
    lines = roof.ridge_lines(ov)
    # ADR 0097: valley flashing (kosz) of a MultiRoof - a 0.36 m sheet strip folded along the valley, 1.2 cm over the
    # covering, in the flashing material (dark sheet; LOD0)
    for p0, p1 in roof.valley_lines(ov):
        seg = exp.intersection(shapely.LineString([p0, p1]))
        for ls in getattr(seg, "geoms", [seg]):
            if ls.geom_type != "LineString" or ls.length < 0.3:
                continue
            q0, q1 = (np.asarray(c_) for c_ in ls.coords[:2])
            t = (q1 - q0) / ls.length
            n = np.array([-t[1], t[0]])
            for sg in (1, -1):
                P_ = [q0, q1, q1 + sg * n * 0.18, q0 + sg * n * 0.18]
                V_ = [[q[0], q[1], float(roof.z(q)) + T_TOP + 0.012] for q in P_]
                T_ = [[0, 1, 2], [0, 2, 3]]
                if np.cross(np.subtract(V_[1], V_[0]), np.subtract(V_[2], V_[0]))[2] < 0:
                    T_ = [tr[::-1] for tr in T_]
                acc.add("buildings", "hall_flashing", V_, T_, [[0, 0], [ls.length, 0], [ls.length, 0.18], [0, 0.18]])
    for p0, p1 in lines:
        if np.hypot(*(p1 - p0)) < 0.3:
            continue
        seg = exp.intersection(shapely.LineString([p0, p1]))
        for ls in getattr(seg, "geoms", [seg]):
            if ls.geom_type != "LineString" or ls.length < 0.3:
                continue
            q0, q1 = (np.asarray(c_) for c_ in ls.coords[:2])
            t = (q1 - q0) / ls.length
            n = np.array([-t[1], t[0]])
            V, UV = [], []
            for q, sa in ((q0, 0.0), (q1, ls.length)):
                zt_ = float(roof.z(q)) + T_TOP + 0.05
                for off, zz in ((-0.11, None), (-0.04, zt_), (0.04, zt_), (0.11, None)):
                    r = q + n * off
                    V.append([r[0], r[1], float(roof.z(r)) + T_TOP + 0.01 if zz is None else zz])
                    UV.append([off, sa])
            T = []
            for j in range(3):
                T += [[j, j + 1, j + 5], [j, j + 5, j + 4]]
            V = np.asarray(V)
            if np.cross(V[1] - V[0], V[5] - V[0])[2] < 0:       # faces look up
                T = [tr[::-1] for tr in T]
            acc.add("buildings", mat, V, T, UV)
    return eaves


def chimney_spots(roof, poly, key_float, n):
    """Up to n chimney positions [(x, y)]: near the ridge (0.5-0.9 m down the slope), inside the footprint."""
    inner = poly.buffer(-0.7)
    out = []
    for i in range(6):
        if len(out) >= n:
            break
        u = (key_float(f"chim{i}") - 0.5) * 1.3 * roof.hu
        if roof.kind == "mono":
            v = roof.hv - 0.9 - 0.8 * key_float(f"chv{i}")
        else:
            v = (0.55 + 0.4 * key_float(f"chv{i}")) * (1 if key_float(f"chs{i}") < 0.5 else -1)
            if roof.kind == "hip":
                u = (key_float(f"chim{i}") - 0.5) * 1.6 * max(roof.hu - roof.hv, 0.3)
        p = roof.c + roof.eu * u + roof.ev * v
        if inner.contains(Point(*p)) and all(np.hypot(*(p - q)) > 2.0 for q in out):
            out.append(p)
    return out
