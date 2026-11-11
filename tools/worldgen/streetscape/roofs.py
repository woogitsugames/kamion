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
    if rt == "1000" or poly.interiors or poly.area > 400 or poly.area / max(rect.area, 1e-6) < 0.6:
        return None
    c, eu, hu, hv = _frame(poly)
    ev = np.array([-eu[1], eu[0]])
    if hv < 1.5:
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
    span = 2 * hv if kind == "mono" else hv      # plan run eave -> ridge
    hr, he = props.get("height_lod2_2017_m"), props.get("lod2_eave_rel_m")
    lo, hi = (math.tan(math.radians(x)) for x in PITCH_RANGE[kind])
    s0 = math.tan(math.radians(PITCH_DEFAULT[kind]))
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


def build(acc, roof, poly, mat, fascia_mat="roof_fascia", ov=OVERHANG, low_layer="buildings_low"):
    """Roof covering (LOD0, LOD1, collision), soffit and fascia (LOD0). Returns the horizontal eave edges
    [(a, b, z_top)] of the covering (outward normal = right of a -> b) for the gutters."""
    exp = poly.buffer(ov, join_style="mitre", mitre_limit=2.5)
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
                if (abs(za - zb) < 0.01 and np.hypot(*(b - a)) > 1.5 and float(roof.d(0.5 * (a + b))) < 0.1 and
                        abs(float((b - a) @ e)) > 0.9 * np.hypot(*(b - a))):
                    eaves.append((a, b, za + T_TOP))
            for sg in _polys(g.difference(poly)):                    # soffit under the overhang, facing down
                S = _tris(sg)
                if len(S):
                    sxy = S[:, [0, 2, 1]].reshape(-1, 2)
                    acc.add("buildings", fascia_mat, np.column_stack([sxy, roof.z(sxy) - T_SOFFIT]),
                            np.arange(len(sxy)).reshape(-1, 3), sxy)
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
