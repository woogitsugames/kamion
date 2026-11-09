"""Road surface decals that are placed by rule (layer 'markings', below the paint): asphalt repair patches
and oil stains. Both lie on the road surface (crossfall + vertical profile; patches on a 2.5 x 2 m grid and never
across the crown of a two-way road, where the surface is not planar) and are
lifted LESS than the markings so they never z-fight with them:
    patch  DECAL_LIFT_PATCH (2 mm)  <  oil  DECAL_LIFT_OIL (3.5 mm)  <  paint MARKING_LIFT (6 mm).

Patches (`decal_patch`): 0-3 per 50 m of carriageway, never on a grid: per 50 m window the count is drawn from
(0.45, 0.30, 0.17, 0.08) (WORKING_VALUE, older industrial streets), position, length 1.2-7 m, width (a full
lane, a wheel path 0.8-1.4 m, or a small 0.6-1.5 m square), rotation +-6 deg and age (UV1.x: 0 fresh/black ..
1 old/grey) are hashed from the chain id + window. Bridges and roundabout rings are skipped.
Oil (`decal_oil`): only where vehicles stand: the 2-8 m in front of the stop position of inbound lanes at
signalised junctions, roundabout entries and minor arms of priority junctions (gate and parking stains are
added by streetscape.life / gate). Each stain is an irregular 9-gon 0.25-0.6 m with radial UV (centre 0.5).
"""

from __future__ import annotations

import hashlib
import math

import numpy as np

from . import standards as S
from .markings import RANK, lane_layout

LIFT_PATCH = 0.002
LIFT_OIL = 0.0035


def hf(*key):
    return int(hashlib.sha1(":".join(str(k) for k in key).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def _surf(c, s, lat, lift):
    p = c.line.offset_point(s, lat)
    z = c.crossfall_z(s, lat) + lift
    return np.column_stack([p, z])


def patch(buf, c, s_c, lat_c, length, width, rot, age, src):
    """Rectangle in the chain frame (s along, lat across) rotated by `rot`, subdivided on a 2.5 x 2 m grid."""
    hw = float(c.hw_at(s_c))
    nu = max(1, int(math.ceil(length / 2.5)))       # surface is planar across a side; vertical curve is slight
    nv = max(1, int(math.ceil(width / 2.0)))
    U, Vv = np.meshgrid(np.linspace(-length / 2, length / 2, nu + 1), np.linspace(-width / 2, width / 2, nv + 1))
    cr, sr = math.cos(rot), math.sin(rot)
    ds = U * cr - Vv * sr
    dl = U * sr + Vv * cr
    s = s_c + ds
    lat = np.clip(lat_c + dl, -hw + 0.05, hw - 0.05)
    P = _surf(c, s.ravel(), lat.ravel(), LIFT_PATCH)
    T = []
    for j in range(nv):
        for i in range(nu):
            a = j * (nu + 1) + i
            b, cc, d = a + 1, a + nu + 2, a + nu + 1
            T += [(a, b, cc), (a, cc, d)]
    T = np.array(T)
    # winding: chain frame (s, lat) is right-handed seen from above -> CCW faces up
    uv = np.column_stack([U.ravel() + length / 2, Vv.ravel() + width / 2])
    uv1 = np.column_stack([np.full(len(P), age), np.full(len(P), hf(src, "seed"))])
    buf.add("markings", "decal_patch", P, uv, T, src=src, UV1=uv1)


def stain(buf, P0, z_of, r, key, src):
    """Irregular 9-gon around P0 (E, N); z_of(points) gives the surface height (already including the lift)."""
    n = 9
    ang = np.linspace(0, 2 * math.pi, n + 1)[:-1] + hf(key, "rot") * 6.283
    rad = r * (0.7 + 0.6 * np.array([hf(key, "r", k) for k in range(n)]))
    stretch = 1.0 + hf(key, "st") * 0.8
    pts = np.column_stack([np.cos(ang) * rad * stretch, np.sin(ang) * rad])
    ca, sa = math.cos(hf(key, "a") * 3.14), math.sin(hf(key, "a") * 3.14)
    pts = pts @ np.array([[ca, sa], [-sa, ca]])
    V2 = np.vstack([[0.0, 0.0], pts]) + P0
    Z = z_of(V2)
    V = np.column_stack([V2, Z])
    T = np.array([(0, 1 + k, 1 + (k + 1) % n) for k in range(n)])
    rr = max(rad.max() * stretch, 1e-3)
    uv = np.vstack([[0.5, 0.5], 0.5 + 0.5 * (V2[1:] - P0) / rr])
    buf.add("markings", "decal_oil", V, uv, T, src=src)


def build(buf, net, juncs, report):
    cnt = {"patches": 0, "oil": 0}
    secs = net.sec_list
    for c in net.chains:
        if c.meta.get("absorbed") or c.roundabout:
            continue
        s0, s1 = c.t_a + 1.0, c.length - c.t_b - 1.0
        if s1 - s0 < 8.0:
            continue
        for w0 in np.arange(s0, s1, 50.0):
            w1 = min(w0 + 50.0, s1)
            key = (c.id, round(float(w0), 1))
            u = hf(*key, "n")
            k = 0 if u < 0.45 else 1 if u < 0.75 else 2 if u < 0.92 else 3
            k = int(round(k * (w1 - w0) / 50.0))
            for i in range(k):
                sc = w0 + hf(*key, i, "s") * (w1 - w0)
                if c.bridge[c.idx(sc)]:
                    continue
                sec = c.section(sc, secs)
                hw = float(c.hw_at(sc))
                kind = hf(*key, i, "kind")
                if kind < 0.35:              # full-lane trench / overlay patch
                    width = min(sec.lane_w * (0.9 + 0.2 * hf(*key, i, "w")), 2 * hw - 0.2)
                    length = 1.2 + hf(*key, i, "l") * 5.8
                    nl = max(1, sec.lanes)
                    lane = int(hf(*key, i, "lane") * nl)
                    lat = -hw + sec.edge_strip + (lane + 0.5) * sec.lane_w
                elif kind < 0.7:             # wheel-path patch
                    width = 0.8 + hf(*key, i, "w") * 0.6
                    length = 2.0 + hf(*key, i, "l") * 5.0
                    lat = (hf(*key, i, "lat") * 2 - 1) * max(hw - 1.0, 0.2)
                else:                        # small square pothole repair
                    width = 0.6 + hf(*key, i, "w") * 0.9
                    length = width * (0.8 + hf(*key, i, "l") * 0.8)
                    lat = (hf(*key, i, "lat") * 2 - 1) * max(hw - 0.8, 0.2)
                if abs(lat) + width / 2 > hw - 0.05:
                    lat = math.copysign(max(hw - 0.05 - width / 2, 0.0), lat)
                if width > 2 * hw - 0.1:
                    continue
                if not sec.oneway and abs(lat) < width / 2 + 0.4:   # keep two-way patches off the crown
                    lat = math.copysign(width / 2 + 0.4, lat if lat != 0 else 1.0)
                    if abs(lat) + width / 2 > hw - 0.05:
                        continue
                rot = (hf(*key, i, "rot") - 0.5) * math.radians(12)
                patch(buf, c, sc, lat, length, width, rot, hf(*key, i, "age"), f"patch:{c.id}:{w0:.0f}:{i}")
                cnt["patches"] += 1
    # oil at stop positions
    for j in juncs:
        ranks = [RANK[a.cls(secs)] for a in j.arms]
        top = min(ranks)
        for ai, a in enumerate(j.arms):
            if a.is_ring():
                continue
            minor = RANK[a.cls(secs)] > top
            if not (j.signalized or j.roundabout or minor):
                continue
            c = a.chain
            t = j.trims[ai]
            s_stop = float(a.s(t + 1.5))
            sec = c.section(s_stop, secs)
            hw = float(c.hw_at(s_stop))
            dirn_here = int(c.dirn[c.idx(s_stop)]) or 1
            _, _, lanes = lane_layout(sec, hw, dirn_here)
            # inbound = travel toward the junction: end 'a' -> travel -s, end 'b' -> travel +s
            inbound = lanes["bwd"] if (a.end == "a") != (dirn_here < 0) else lanes["fwd"]
            if sec.oneway:
                inb = a.inbound_dirn()
                if inb <= 0:
                    continue
                inbound = lanes["fwd"]
            for li, lat in enumerate(inbound):
                for m in range(1 + int(hf(j.id, ai, li, "m") * 3)):
                    d = t + 2.0 + m * (1.4 + hf(j.id, ai, li, m, "g") * 2.0)
                    if d > c.length - 2.0:
                        break
                    sc = float(a.s(d))
                    latj = lat + (hf(j.id, ai, li, m, "lat") - 0.5) * 0.5
                    P0 = c.line.offset_point(sc, latj)

                    def z_of(V2, c=c, sc=sc):
                        out = []
                        for q in V2:
                            ss, ll = c.line.project(q)
                            out.append(float(c.crossfall_z(ss, np.clip(ll, -c.hw_at(ss), c.hw_at(ss)))) + LIFT_OIL)
                        return np.array(out)
                    stain(buf, P0, z_of, 0.25 + hf(j.id, ai, li, m, "r") * 0.35, (j.id, ai, li, m),
                          f"oil:{j.id}:{ai}:{li}:{m}")
                    cnt["oil"] += 1
    report["decals"] = cnt
    return cnt
