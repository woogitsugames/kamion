"""Parked-vehicle prototypes (ADR 0041 par. 6): generic passenger cars and a light van, built from a side
profile (the way a car body is drawn) instead of a box loft. Frame as streetscape.props: x = right, y = nose,
z = up, origin = centre of the footprint on the ground.

No make or model is reproduced: each body is a class average (lengths, wheelbases and heights below are typical
values of the European B/C/D segments, B/C-SUV and car-derived light vans, all WORKING_VALUE) with no grille
shape, lamp signature or badge of any real vehicle. Registration plates are blank white rectangles.

A body is a closed side profile of named points (rear bumper -> tail -> rear glass -> roof -> windscreen -> hood
-> nose -> front bumper), each with its own half width (plan taper at the nose and tail, tumblehome of the
greenhouse). The top strip is the profile swept across x; the sides are the profile polygon itself.
  LOD0  rounded shoulders (a chamfer station across x, so A/C pillars and roof rails come out body-coloured
        for free), wheel-arch cut-outs with dark liners, recessed wheels (tyre tube, sidewall, rim), framed side
        windows split at the B pillar, door shut lines and handles, lamps, grille, plates, mirrors, dark lower
        valances and sills, roof rails (estate / SUV), arch cladding (SUV)
  LOD1  same profile without the chamfer; round tyre + rim discs on the body side, framed side windows, lamps,
        plates, mirrors, sills: at 12-45 m it still has a hood, a raked windscreen, pillars and four round wheels
  LOD2  the LOD1 body with a glazed greenhouse and one dark under-body block (far parking rows)
"""

from __future__ import annotations

import math
import zlib

import numpy as np

from .props import Mesh

CAR_COLOURS = ["silver", "grey", "black", "white", "blue", "red"]
VAN_COLOURS = ["white", "silver", "white2"]

# WORKING_VALUE class-typical dimensions (m). L/W/H overall, wb wheelbase, foh front overhang, r tyre radius,
# sill = lower body edge, belt = window line at the cowl, nose = hood leading edge height, hood = nose -> cowl,
# ws = horizontal run of the windscreen, tail = (y from the rear, z) of the tail top edge, deck = boot lid
# length (three-box only), rg = (y from the rear, drop below the roof) of the roof rear edge,
# tumble = greenhouse inset per side at the roof, bp = cowl -> B pillar, qp = B pillar -> C pillar (bodies with
# a third side window), cp / ap = C and A pillar widths, cargo = no glass behind the B pillar.
CARS = {
    "hatch": dict(L=4.08, W=1.77, H=1.46, wb=2.58, foh=0.86, r=0.315, sill=0.20, belt=1.00, nose=0.81, hood=0.94,
                  ws=0.92, tail=(0.10, 1.06), deck=0.0, rg=(0.50, 0.05), tumble=0.18, bp=1.40, qp=None, cp=0.26,
                  ap=0.10, face="swept"),
    "sedan": dict(L=4.66, W=1.81, H=1.43, wb=2.72, foh=0.91, r=0.325, sill=0.20, belt=0.98, nose=0.79, hood=1.08,
                  ws=0.96, tail=(0.07, 1.03), deck=0.40, rg=(1.12, 0.05), tumble=0.19, bp=1.40, qp=None, cp=0.22,
                  ap=0.10, face="wide"),
    "estate": dict(L=4.70, W=1.81, H=1.47, wb=2.72, foh=0.91, r=0.325, sill=0.20, belt=0.98, nose=0.79, hood=1.08,
                   ws=0.96, tail=(0.10, 1.06), deck=0.0, rg=(0.42, 0.045), tumble=0.18, bp=1.40, qp=0.98, cp=0.14,
                   ap=0.10, rails=True, face="swept"),
    "suv": dict(L=4.40, W=1.84, H=1.63, wb=2.64, foh=0.89, r=0.36, sill=0.27, belt=1.12, nose=0.99, hood=1.00,
                ws=0.86, tail=(0.10, 1.20), deck=0.0, rg=(0.46, 0.05), tumble=0.16, bp=1.36, qp=0.90, cp=0.22,
                ap=0.10, rails=True, clad=True, face="tall"),
}
VAN = dict(L=4.52, W=1.83, H=1.85, wb=2.78, foh=0.88, r=0.325, sill=0.23, belt=1.14, nose=1.00, hood=0.72,
           ws=0.72, tail=(0.035, 1.14), deck=0.0, rg=(0.10, 0.05), tumble=0.08, bp=1.30, qp=None, cp=0.10, ap=0.10,
           cargo=True, face="tall")

# Front faces (generic 2015-2024 class looks, no make reproduced), fractions of the fascia edge (hood lip -> bumper
# peak): drop / run of the fascia, lamp top / bottom at the inner and outer end, grille half width (in top half
# widths) and its top, light bar across the tail.
FACES = {
    "swept": dict(drop=0.34, run=0.20, lamp=(0.03, 0.26, 0.00, 0.44), gw=0.62, gt=0.24, bar=False),
    "wide": dict(drop=0.32, run=0.18, lamp=(0.03, 0.24, 0.00, 0.36), gw=0.62, gt=0.14, bar=True),
    "tall": dict(drop=0.42, run=0.14, lamp=(0.02, 0.20, 0.00, 0.32), gw=0.64, gt=0.10, bar=False),
}


# ------------------------------------------------------------------------------------------- geometry helpers
def _earclip(P):
    """Triangulate a simple polygon ((n, 2) array). Returns CCW index triples; picks the best-shaped ear."""
    P = np.asarray(P, float)
    n = len(P)
    idx = list(range(n))
    if sum(P[i][0] * P[(i + 1) % n][1] - P[(i + 1) % n][0] * P[i][1] for i in range(n)) < 0:
        idx.reverse()

    def cr(a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])
    T = []
    while len(idx) > 3:
        best, bk = -1.0, None
        m = len(idx)
        for k in range(m):
            i0, i1, i2 = idx[k - 1], idx[k], idx[(k + 1) % m]
            a, b, c = P[i0], P[i1], P[i2]
            ar = cr(a, b, c)
            if ar <= 1e-10:
                continue
            if any(cr(a, b, P[j]) > 1e-10 and cr(b, c, P[j]) > 1e-10 and cr(c, a, P[j]) > 1e-10
                   for j in idx if j not in (i0, i1, i2)):
                continue
            q = ar / max(np.sum((b - a) ** 2), np.sum((c - b) ** 2), np.sum((a - c) ** 2))
            if q > best:
                best, bk = q, k
        if bk is None:                      # only collinear vertices left: drop one
            k = min(range(m), key=lambda k: abs(cr(P[idx[k - 1]], P[idx[k]], P[idx[(k + 1) % m]])))
            idx.pop(k)
            continue
        T.append((idx[bk - 1], idx[bk], idx[(bk + 1) % len(idx)]))
        idx.pop(bk)
    if len(idx) == 3 and abs(cr(P[idx[0]], P[idx[1]], P[idx[2]])) > 1e-10:
        T.append(tuple(idx))
    return T


def _clip(poly, a, b, c):
    """Sutherland-Hodgman: keep the part of a convex (y, z) polygon where a*y + b*z >= c."""
    out = []
    n = len(poly)
    for i in range(n):
        p, q = poly[i], poly[(i + 1) % n]
        dp, dq = a * p[0] + b * p[1] - c, a * q[0] + b * q[1] - c
        if dp >= 0:
            out.append(p)
        if (dp >= 0) != (dq >= 0):
            t = dp / (dp - dq)
            out.append((p[0] + t * (q[0] - p[0]), p[1] + t * (q[1] - p[1])))
    return out


def _oq(m, mat, q, want):
    """Quad (or n-gon fan) wound so that its normal points along `want`."""
    q = [np.asarray(p, float) for p in q]
    nrm = np.zeros(3)
    for i in range(1, len(q) - 1):
        nrm += np.cross(q[i] - q[0], q[i + 1] - q[0])
    if float(np.dot(nrm, want)) < 0:
        q = q[::-1]
    m.add(mat, q, [(0, i, i + 1) for i in range(1, len(q) - 1)], [[p[1], p[2]] for p in q])


def _sides(m, mat, pts, lift=0.0):
    """Mirror pair of side polygons. pts = [(half width, y, z)] of the right side, triangulated in (y, z)."""
    P = np.asarray(pts, float)
    T = _earclip(P[:, 1:])
    if not T:
        return
    for sx in (1, -1):
        V = np.column_stack([sx * (P[:, 0] + lift), P[:, 1], P[:, 2]])
        m.add(mat, V, T if sx > 0 else [(a, c, b) for a, b, c in T], P[:, 1:])


def _disc(m, mat, c, r, seg, sx, phase=0.0):
    a = np.linspace(0, 2 * math.pi, seg + 1)[:-1] + phase
    V = [[c[0], c[1] + math.cos(t) * r, c[2] + math.sin(t) * r] for t in a]
    T = [(0, i, i + 1) for i in range(1, seg - 1)]
    m.add(mat, V, T if sx > 0 else [(a_, c_, b_) for a_, b_, c_ in T])


def _box5(m, mat, c, hx, hy, hz, skip):
    """Box without the face whose outward normal is `skip` (hidden against the body)."""
    c = np.asarray(c, float)
    for ax in range(3):
        for s in (-1, 1):
            nrm = np.zeros(3)
            nrm[ax] = s
            if tuple(nrm) == tuple(skip):
                continue
            u, v = [(1, 2), (0, 2), (0, 1)][ax]
            h = [hx, hy, hz]
            q = []
            for su, sv in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                p = c + nrm * h[ax]
                p[u] += su * h[u]
                p[v] += sv * h[v]
                q.append(p)
            _oq(m, mat, q, nrm)


def _paint_uv(m):
    """UV of every car_paint_* primitive = (y, z) in metres (side projection), so the car_grime set puts road
    film on the sills and bumpers and dust on the roof whatever helper built the part."""
    for mat, p in m.prims.items():
        if mat.startswith("car_paint_"):
            p[2] = [np.asarray(V, float)[:, [1, 2]] for V in p[0]]
    return m


# ------------------------------------------------------------------------------------------- body
def _profile(d, lod):
    """Top outline rear -> front: list of dicts(name, y, z, w, r, mat) where mat = material of the strip edge
    that STARTS at the point ("paint" / "glass" / "trim")."""
    L, hw, H = d["L"], d["W"] / 2, d["H"]
    y0, y1 = -L / 2, L / 2
    sill, belt = d["sill"], d["belt"]
    zr, zf = sill + 0.05, sill + 0.03
    ty, tz = d["tail"]
    yA = y1 - d["hood"]
    yF = yA - d["ws"]
    yR = y0 + d["rg"][0]
    cargo = d.get("cargo", False)
    rb, rr = 0.06, 0.075
    pts = [dict(name="R0", y=y0 + 0.08, z=zr, w=hw - 0.10, r=0.0, mat="trim"),
           dict(name="R1", y=y0, z=zr + 0.17, w=hw - 0.07, r=rb, mat="paint"),
           dict(name="R2", y=y0 + 0.012, z=tz - 0.10, w=hw - 0.03, r=rb, mat="paint"),
           dict(name="R3", y=y0 + ty, z=tz, w=hw, r=rb, mat="paint")]
    if d["deck"] > 0:
        pts.append(dict(name="G0", y=y0 + ty + d["deck"], z=tz + 0.015, w=hw, r=rb, mat="glass"))
    else:
        pts[-1].update(name="G0", mat="paint" if cargo else "glass")
    pts += [dict(name="G1", y=yR, z=H - d["rg"][1], w=hw - d["tumble"], r=rr, mat="paint"),
            dict(name="G2", y=(yR + yF) / 2, z=H, w=hw - d["tumble"], r=rr, mat="paint"),
            dict(name="G3", y=yF, z=H - 0.03, w=hw - d["tumble"], r=rr, mat="glass"),
            dict(name="G4", y=yA, z=belt, w=hw, r=rb, mat="paint"),
            dict(name="H0", y=(yA + y1 - 0.17) / 2, z=(belt + d["nose"]) / 2 + 0.04, w=hw - 0.015, r=rb, mat="paint"),
            dict(name="H1", y=y1 - (0.17 if lod == 0 else 0.07), z=d["nose"], w=hw - 0.05, r=rb, mat="paint"),
            dict(name="F1", y=y1 - 0.035, z=d["nose"] - 0.17, w=hw - 0.10, r=rb, mat="paint"),
            dict(name="F2", y=y1, z=zf + 0.17, w=hw - 0.13, r=rb, mat="trim"),
            dict(name="F3", y=y1 - 0.09, z=zf, w=hw - 0.13, r=0.0, mat="trim")]
    if lod > 0:
        pts = [p for p in pts if p["name"] not in ("R2", "G2", "H0", "F1")]
        for p in pts:
            p["r"] = 0.0
    return pts


def _vehicle(d, paint, lod):
    m = Mesh()
    L, hw, H = d["L"], d["W"] / 2, d["H"]
    sill, belt, r = d["sill"], d["belt"], d["r"]
    cargo = d.get("cargo", False)
    pts = _profile(d, lod)
    n = len(pts)
    P = np.array([[p["y"], p["z"]] for p in pts])
    # outward normals of the profile (rear -> front along the top: left of the travel direction)
    E = np.diff(P, axis=0)
    EN = np.column_stack([-E[:, 1], E[:, 0]])
    EN /= np.linalg.norm(EN, axis=1)[:, None]
    PN = np.zeros_like(P)
    for i in range(n):
        v = (EN[i - 1] if i > 0 else EN[0]) + (EN[i] if i < n - 1 else EN[-1])
        PN[i] = v / np.linalg.norm(v)
    S = np.array([P[i] - PN[i] * pts[i]["r"] for i in range(n)])        # side (shoulder) points
    W = np.array([p["w"] for p in pts])
    R = np.array([p["r"] for p in pts])
    ix = {p["name"]: i for i, p in enumerate(pts)}
    matname = {"paint": paint, "glass": "car_glass", "trim": "car_trim"}

    # ---- top strip
    for i in range(n - 1):
        mat = matname[pts[i]["mat"]]
        want = np.array([0.0, EN[i][0], EN[i][1]])
        a, b = i, i + 1
        if lod == 0:
            xa, xb = W[a] - R[a], W[b] - R[b]
            _oq(m, mat, [[xa, *P[a]], [-xa, *P[a]], [-xb, *P[b]], [xb, *P[b]]], want)
            if R[a] > 0 or R[b] > 0:
                cm = paint if mat == "car_glass" else mat
                for sx in (-1, 1):
                    _oq(m, cm, [[sx * W[a], *S[a]], [sx * xa, *P[a]], [sx * xb, *P[b]], [sx * W[b], *S[b]]],
                        want + np.array([sx, 0, 0]))
        else:
            _oq(m, mat, [[W[a], *P[a]], [-W[a], *P[a]], [-W[b], *P[b]], [W[b], *P[b]]], want)

    def on_edge(a, mat, x0, x1, z0, z1, lift=0.006):
        """Quad lying on strip edge a -> a+1 between heights z0..z1 and x0..x1."""
        pa, pb = P[a], P[a + 1]
        q = []
        for z, x in ((z0, x0), (z0, x1), (z1, x1), (z1, x0)):
            t = (z - pa[1]) / (pb[1] - pa[1])
            p = pa + t * (pb - pa) + EN[a] * lift
            q.append([x, p[0], p[1]])
        _oq(m, mat, q, np.array([0.0, EN[a][0], EN[a][1]]))

    # ---- axles, arches
    yfa = L / 2 - d["foh"]
    yra = yfa - d["wb"]
    ra = r + 0.055
    a0 = math.asin((sill - r) / ra)
    seg = 6

    def arch(yc):                       # rear -> front (increasing y) along the cut-out
        return [(yc - ra * math.cos(t), r + ra * math.sin(t)) for t in np.linspace(a0, math.pi - a0, seg + 1)]
    bottom = []
    if lod == 0:
        for yc in (yra, yfa):
            bottom += [(hw, y, z) for y, z in arch(yc)]
    g0, g4 = ix["G0"], ix["G4"]
    top_front = [(W[i], *S[i]) for i in range(n - 1, g4 - 1, -1)]         # F3 .. G4
    top_rear = [(W[i], *S[i]) for i in range(g0, -1, -1)]                 # G0 .. R0
    _sides(m, paint, bottom + top_front + top_rear)
    green = [(W[i], *S[i]) for i in range(g0, g4 + 1)]
    _sides(m, "car_glass" if (lod == 2 and not cargo) else paint, green)

    # ---- side windows (framed, split at the B pillar)
    if lod < 2:
        G = [np.array(S[i]) for i in range(g0, g4 + 1)]
        zroof = max(g[1] for g in G)
        cp, ap, fr = d["cp"], d["ap"], 0.05
        inner = [(G[0][0] + cp, G[0][1])] + [(g[0] + (cp if k == 0 else 0.0) - (ap * 0.7 if k == len(G) - 3 else 0.0),
                                              g[1] - fr) for k, g in enumerate(G[1:-1])] + [(G[-1][0] - ap, G[-1][1])]
        zb = max(G[0][1], G[-1][1]) + 0.03 if not d["deck"] else belt + 0.03
        zb = belt + 0.035
        yB = G[-1][0] - d["bp"]
        cuts = [(yB + 0.035, 1e9)]
        if not cargo:
            if d["qp"] and lod == 0:
                cuts += [(yB - d["qp"] + 0.03, yB - 0.035), (-1e9, yB - d["qp"] - 0.03)]
            else:
                cuts += [(-1e9, yB - 0.035)]
        tum = d["tumble"]

        def xs(z):
            return hw - tum * max(0.0, z - belt) / (zroof - belt)
        for ya, yb in cuts:
            poly = _clip(_clip(_clip(inner, 0, 1, zb), 1, 0, ya), -1, 0, -yb)
            # the rear belt rises on wedge bodies: keep the glass above the rising body line
            zr0, zr1 = G[0][1], G[-1][1]
            if zr0 > zr1 + 0.01:
                yy0, yy1 = G[0][0], G[-1][0]
                k = (zr1 - zr0) / (yy1 - yy0)
                # z >= zr0 + k (y - yy0) + 0.035  ->  -k y + z >= zr0 - k yy0 + 0.035
                poly = _clip(poly, -k, 1, zr0 - k * yy0 + 0.035)
            if len(poly) >= 3:
                _sides(m, "car_glass", [(xs(z), y, z) for y, z in poly], lift=0.012 if lod == 0 else 0.008)

    # ---- wheels
    if lod == 0:
        from .life_props import wheel
        for yc in (yra, yfa):
            A = arch(yc)
            for sx in (-1, 1):
                wheel(m, [sx * (hw - 0.125), yc, r], r, 0.21, 10, out_sign=sx)
                for (ya, za), (yb, zb_) in zip(A[:-1], A[1:]):
                    mid = np.array([0, yc - (ya + yb) / 2, r - (za + zb_) / 2])
                    _oq(m, "car_trim", [[sx * hw, ya, za], [sx * hw, yb, zb_], [sx * (hw - 0.30), yb, zb_],
                                        [sx * (hw - 0.30), ya, za]], mid)
                    if d.get("clad"):
                        k = (ra + 0.055) / ra
                        _oq(m, "car_sill", [[sx * (hw + 0.006), ya, za], [sx * (hw + 0.006), yb, zb_],
                                            [sx * (hw + 0.006), yc + (yb - yc) * k, r + (zb_ - r) * k],
                                            [sx * (hw + 0.006), yc + (ya - yc) * k, r + (za - r) * k]], [sx, 0, 0])
        _oq(m, "car_trim", [[hw - 0.05, -L / 2 + 0.15, sill + 0.03], [-hw + 0.05, -L / 2 + 0.15, sill + 0.03],
                            [-hw + 0.05, L / 2 - 0.15, sill + 0.03], [hw - 0.05, L / 2 - 0.15, sill + 0.03]], [0, 0, -1])
    elif lod == 1:
        for yc in (yra, yfa):
            for sx in (-1, 1):
                _disc(m, "tyre", [sx * (hw + 0.008), yc, r], r, 8, sx, math.pi / 8)
                _disc(m, "rim", [sx * (hw + 0.016), yc, r], r * 0.62, 8, sx, math.pi / 8)
            for s in ((-1,) if yc == yra else (1,)):            # tread seen from the front / rear, under the body
                yy = yc + s * r * 0.75
                _oq(m, "tyre", [[hw - 0.01, yy, 0.0], [-hw + 0.01, yy, 0.0], [-hw + 0.01, yy, sill + 0.02],
                                [hw - 0.01, yy, sill + 0.02]], [0, s, 0])
    else:
        ya, yb = yra - r, yfa + r
        for sx in (-1, 1):
            _oq(m, "tyre", [[sx * (hw - 0.01), ya, 0], [sx * (hw - 0.01), yb, 0], [sx * (hw - 0.01), yb, sill + 0.02],
                            [sx * (hw - 0.01), ya, sill + 0.02]], [sx, 0, 0])
        for yy, s in ((ya, -1), (yb, 1)):
            _oq(m, "tyre", [[hw - 0.01, yy, 0.0], [-hw + 0.01, yy, 0.0], [-hw + 0.01, yy, sill + 0.02],
                            [hw - 0.01, yy, sill + 0.02]], [0, s, 0])

    # ---- lamps, grille, plates
    if lod < 2:
        ef = ix["H1"]                                            # lamp / grille band (LOD1: whole front face)
        za, zb2 = P[ef][1], P[ef + 1][1]
        zl0 = za - 0.035
        zl1 = zl0 - 0.105
        er = ix["R1"]                                            # tail face
        zt = P[er + 1][1] - (0.03 if lod == 0 else 0.12)
        wl = hw - (0.13 if lod == 0 else 0.11)
        for sx in (-1, 1):
            on_edge(ef, "car_light_head", sx * (wl - 0.36), sx * wl, zl0, zl1)
            if cargo:
                on_edge(er, "car_light_tail", sx * (wl - 0.10), sx * wl, zt, zt - 0.42)
            else:
                on_edge(er, "car_light_tail", sx * (wl - 0.34), sx * wl, zt, zt - 0.13)
        on_edge(ef, "car_trim", -(wl - 0.40), wl - 0.40, zl0 - 0.01, zl1 - (0.0 if lod == 0 else 0.10))
        pf = ix["F1"] if lod == 0 else ef
        zc = (P[pf][1] + P[pf + 1][1]) / 2 if lod == 0 else P[pf + 1][1] + 0.10
        on_edge(pf, "car_plate", -0.26, 0.26, zc + 0.056, zc - 0.056, lift=0.012)
        zc = P[er][1] + (0.20 if not cargo else 0.24)
        on_edge(er, "car_plate", -0.26, 0.26, zc + 0.056, zc - 0.056, lift=0.012)

    # ---- sills, mirrors, shut lines, handles, rails
    if lod < 2:
        ys0, ys1 = yra + ra + 0.02, yfa - ra - 0.02
        zs = sill + (0.16 if d.get("clad") else 0.09)
        for sx in (-1, 1):
            x = sx * (hw + 0.005)
            _oq(m, "car_sill", [[x, ys0, sill], [x, ys1, sill], [x, ys1, zs], [x, ys0, zs]], [sx, 0, 0])
        yM, zM = P[g4][0] - 0.20, belt + 0.075
        for sx in (-1, 1):
            c = [sx * (hw + 0.085), yM, zM]
            if lod == 0:
                _box5(m, paint, c, 0.085, 0.04, 0.055, (-sx, 0, 0))
            else:
                for s in (-1, 1):
                    _oq(m, paint, [[c[0] - 0.085, yM + s * 0.03, zM - 0.055], [c[0] + 0.085, yM + s * 0.03, zM - 0.055],
                                   [c[0] + 0.085, yM + s * 0.03, zM + 0.055], [c[0] - 0.085, yM + s * 0.03, zM + 0.055]],
                        [0, s, 0])
    if lod == 0:
        yB = P[g4][0] - d["bp"]
        zt = belt - 0.005
        lines = [(yfa - ra - 0.07, sill + 0.10, zt), (yB, sill + 0.10, zt),
                 ((yra + 0.16) if not cargo else (yB - 1.05), (r + ra + 0.03) if not cargo else sill + 0.10, zt)]
        handles = [yB + 0.16, (yra + 0.34) if not cargo else (yB - 0.90)]
        for sx in (-1, 1):
            x = sx * (hw + 0.004)
            for y, za_, zb_ in lines:
                _oq(m, "car_trim", [[x, y - 0.007, za_], [x, y + 0.007, za_], [x, y + 0.007, zb_], [x, y - 0.007, zb_]],
                    [sx, 0, 0])
            for y in handles:
                _oq(m, "car_trim", [[x, y, belt - 0.085], [x, y + 0.13, belt - 0.085], [x, y + 0.13, belt - 0.055],
                                    [x, y, belt - 0.055]], [sx, 0, 0])
        if d.get("rails"):
            g1, g3 = P[ix["G1"]], P[ix["G3"]]
            for sx in (-1, 1):
                _box5(m, "car_trim", [sx * (hw - d["tumble"] - 0.13), (g1[0] + g3[0]) / 2 - 0.05, H + 0.012],
                      0.018, (g3[0] - g1[0]) / 2 - 0.22, 0.02, (0, 0, -1))
    return _paint_uv(m)


# =========================================================================================== v2 bodies (ADR 0041 par. 7)
# LOD0 / LOD1 of the 2026-11-10 second pass: curved shell (crowned roof / hood / glass, rounded shoulders, barrel
# sides, rounded plan corners), wheel arches cut into the side with the tyres set inside, revolved tyres and rims,
# see-through tinted glass with a dark interior (LOD0). The first-pass _vehicle(lod=1) above is now LOD2.
def _controls(d):
    L, H = d["L"], d["H"]
    y0, y1 = -L / 2, L / 2
    sill, belt = d["sill"], d["belt"]
    zr, zf = sill + 0.05, sill + 0.03
    ty, tz = d["tail"]
    yA = y1 - d["hood"]
    yF = yA - d["ws"]
    yR = y0 + d["rg"][0]
    cargo = d.get("cargo", False)
    f = FACES[d.get("face", "swept")]
    yH = y1 - 0.012 - f["run"]
    C = [("R0", y0 + 0.10, zr, 0.03, 0.0, "trim"),
         ("R1", y0, zr + 0.17, 0.08, 0.04, "paint"),
         ("R2", y0 + 0.02, tz - 0.12, 0.09, 0.04, "paint"),
         ("R3", y0 + ty, tz, 0.09, 0.035, "paint")]
    if d["deck"] > 0:
        C.append(("G0", y0 + ty + d["deck"], tz + 0.015, 0.085, 0.03, "glass"))
    else:
        C[-1] = ("G0", y0 + ty, tz, 0.085, 0.03, "paint" if cargo else "glass")
    C += [("G1", yR, H - d["rg"][1], 0.10, 0.04, "paint"),
          ("G2", (yR + yF) / 2, H, 0.10, 0.04, "paint"),
          ("G3", yF, H - 0.03, 0.10, 0.04, "glass"),
          ("G4", yA, belt, 0.08, 0.035, "paint"),
          ("H0", yA + 0.52 * (yH - yA), belt + 0.52 * (d["nose"] - belt) + 0.05, 0.09, 0.035, "paint"),
          ("H1", yH, d["nose"], 0.10, 0.04, "paint"),                      # bonnet leading edge
          ("F1", y1 - 0.012, d["nose"] - f["drop"], 0.10, 0.05, "paint"),  # bumper peak (fascia: lamps, grille)
          ("F2", y1 - 0.035, zf + 0.085, 0.08, 0.05, "trim"),
          ("F3", y1 - 0.15, zf, 0.03, 0.0, "trim")]
    return C


class _Shell:
    def __init__(self, d, lod):
        self.d, self.lod = d, lod
        C = _controls(d)
        P, R, CR, tag = [], [], [], []           # dense points; tag = (control index, part) part: 0 QA, 1 M, 2 QB
        cp = np.array([[c[1], c[2]] for c in C])
        for k, c in enumerate(C):
            if k in (0, len(C) - 1) or lod > 0:
                P.append(cp[k]); R.append(c[3]); CR.append(c[4]); tag.append((k, 1))
                continue
            a, b = cp[k - 1] - cp[k], cp[k + 1] - cp[k]
            la, lb = np.linalg.norm(a), np.linalg.norm(b)
            kl = min(0.25 * la, 0.25 * lb, 0.11 if c[0] in ("H1", "F1", "G1") else 0.07)
            qa, qb = cp[k] + a / la * kl, cp[k] + b / lb * kl
            for part, q in ((0, qa), (1, 0.25 * qa + 0.5 * cp[k] + 0.25 * qb), (2, qb)):
                P.append(q); R.append(c[3]); CR.append(c[4]); tag.append((k, part))
        self.C, self.P, self.R, self.CR, self.tag = C, np.array(P), np.array(R), np.array(CR), tag
        if lod > 0:
            self.CR = self.CR * 0.0
        n = len(P)
        E = np.diff(self.P, axis=0)
        EN = np.column_stack([-E[:, 1], E[:, 0]])
        EN /= np.linalg.norm(EN, axis=1)[:, None]
        N = np.zeros((n, 2))
        for i in range(n):
            v = (EN[i - 1] if i > 0 else EN[0]) + (EN[i] if i < n - 1 else EN[-1])
            N[i] = v / np.linalg.norm(v)
        self.EN, self.N = EN, N
        S = self.P - N * (self.R + self.CR)[:, None]
        for i in range(1, n):                                  # the side chain must be a function of y
            if S[i, 0] <= S[i - 1, 0] + 1e-3:
                S[i, 0] = S[i - 1, 0] + 1e-3
        self.S = S
        names = [c[0] for c in C]
        self.mid = {names[k]: i for i, (k, part) in enumerate(tag) if part == 1}
        self.seg = {}                                          # control name -> dense edge index of its straight part
        self.emat = []
        for i in range(n - 1):
            (ka, pa), (kb, pb) = tag[i], tag[i + 1]
            if ka != kb:
                self.seg[names[ka]] = i
                self.emat.append(C[ka][5])
            else:
                m0, m1 = C[ka - 1][5], C[ka][5]
                self.emat.append(m0 if m0 == m1 else "paint")
        self.hw = d["W"] / 2
        self.sill, self.belt = d["sill"], d["belt"]
        self.bl0, self.bl1 = S[self.mid["G0"]], S[self.mid["G4"]]
        self.zroof = float(S[:, 1].max())
        self.y0, self.y1 = -d["L"] / 2, d["L"] / 2

    def zbelt(self, y):
        (ya, za), (yb, zb) = self.bl0, self.bl1
        return za + (zb - za) * (y - ya) / (yb - ya)

    def plan(self, y):
        w = self.hw
        Rf, tf, Rr, tr = 0.80, 0.27, 0.50, 0.15
        u = min(1.0, max(0.0, (y - (self.y1 - Rf)) / Rf))
        w -= tf * (1 - math.sqrt(max(0.0, 1 - u * u)))
        u = min(1.0, max(0.0, ((self.y0 + Rr) - y) / Rr))
        w -= tr * (1 - math.sqrt(max(0.0, 1 - u * u)))
        return w

    def X(self, y, z):
        """Half width of the body side at (y, z): plan taper, barrel below the belt, tumblehome above it."""
        w = self.plan(y)
        zw = self.sill + 0.55 * (self.belt - self.sill)
        if z <= zw:
            return w - 0.05 * min(1.3, (zw - z) / (zw - self.sill)) ** 2
        zb = self.zbelt(y) if self.bl0[0] <= y <= self.bl1[0] else 1e9
        if z <= zb:
            return w - 0.012 * min(1.0, (z - zw) / max(min(zb, self.belt) - zw, 1e-3)) ** 2
        return w - 0.012 - self.d["tumble"] * (z - zb) / max(self.zroof - zb, 1e-3)

    def pt(self, i, g):
        """Surface point and normal at dense profile index i, signed across coordinate g: |g| <= 1 crowned top
        (g = x / top half width), 1 < |g| <= 2 the shoulder arc down to the side line."""
        sx = 1.0 if g >= 0 else -1.0
        a = abs(g)
        Pi, Ni, Si = self.P[i], self.N[i], self.S[i]
        wS = self.X(Si[0], Si[1])
        xt = max(0.05, wS - self.R[i])
        c = self.CR[i]
        if a <= 1.0:
            off = -c * a * a
            return (np.array([sx * xt * a, Pi[0] + Ni[0] * off, Pi[1] + Ni[1] * off]),
                    np.array([sx * 2 * c * a / max(xt, 1e-3), Ni[0], Ni[1]]))
        ph = (a - 1.0) * math.pi / 2
        Ept = Pi - Ni * c
        q = Ept + (Si - Ept) * (1 - math.cos(ph))
        return (np.array([sx * (xt + (wS - xt) * math.sin(ph)), q[0], q[1]]),
                np.array([sx * math.sin(ph), Ni[0] * math.cos(ph), Ni[1] * math.cos(ph)]))

    def ptf(self, i, t, g):
        a, na = self.pt(i, g)
        b, nb = self.pt(i + 1, g)
        n = na + (nb - na) * t
        return a + (b - a) * t, n / np.linalg.norm(n)


def _quad(m, mat, a, b, c, d, want):
    q = [np.asarray(p, float) for p in (a, b, c, d)]
    if np.linalg.norm(np.cross(q[1] - q[0], q[2] - q[0])) + np.linalg.norm(np.cross(q[2] - q[0], q[3] - q[0])) < 1e-9:
        return
    _oq(m, mat, q, want)


def _puv(m, mat, q, uv, want):
    """Triangle / quad with explicit UVs, wound so that its normal points along `want`."""
    q = [np.asarray(p, float) for p in q]
    nrm = np.zeros(3)
    for i in range(1, len(q) - 1):
        nrm += np.cross(q[i] - q[0], q[i + 1] - q[0])
    if np.linalg.norm(nrm) < 1e-10:
        return
    if float(np.dot(nrm, want)) < 0:
        q, uv = q[::-1], list(uv)[::-1]
    m.add(mat, q, [(0, i, i + 1) for i in range(1, len(q) - 1)], uv)


def _tri2d(poly):
    """Constrained Delaunay triangles of a shapely polygon (holes allowed) as lists of (y, z)."""
    import shapely
    out = []
    for g in getattr(poly, "geoms", [poly]):
        if g.is_empty or g.geom_type != "Polygon":
            continue
        for t in shapely.constrained_delaunay_triangles(g).geoms:
            out.append(list(t.exterior.coords)[:3])
    return out


def _wheel2(m, x_out, yc, r, sx, seg, steel, lod, wst=0, rimm="rim", tyre="tyre"):
    """Revolved tyre + rim; x_out = x of the outer sidewall plane, the wheel extends inward (toward x = 0)."""
    w = 0.205
    rr = (0.60 if steel else 0.69) * r
    cen = np.array([x_out, yc, r])

    def ring(rad, o):
        return [np.array([x_out - sx * o, yc + rad * math.cos(t), r + rad * math.sin(t)])
                for t in np.linspace(0, 2 * math.pi, seg + 1)[:-1]]

    def band(mat, A, B, radial=0.3, inward=False):
        for k in range(seg):
            k2 = (k + 1) % seg
            want = (A[k] + A[k2] + B[k] + B[k2]) / 4 - cen
            want[0] = 0
            want = want / max(np.linalg.norm(want), 1e-6) * (-1 if inward else 1)
            _quad(m, mat, A[k], A[k2], B[k2], B[k], want * radial + np.array([sx * (1 - radial), 0, 0]))

    def fan(mat, A, want):
        A = [np.asarray(a) for a in A]
        ok = np.dot(np.cross(A[1] - A[0], A[2] - A[0]), want) > 0
        m.add(mat, A, [(0, i, i + 1) if ok else (0, i + 1, i) for i in range(1, len(A) - 1)])
    X = np.array([sx, 0.0, 0.0])
    if lod == 0:
        prof = [(rr, 0.014), (0.80 * r, 0.0), (0.95 * r, 0.010), (r, 0.04)]
        rings = [ring(*p) for p in prof]
        for A, B in zip(rings[:-1], rings[1:]):
            band(tyre, A, B)
        band(tyre, rings[-1], ring(r, w), radial=1.0)
        lip = ring(rr - 0.014, 0.014)
        rim = "rim_steel" if steel else ("rim" if wst == 3 else rimm)
        band(rim, rings[0], lip, radial=0.0)
        deep = ring(rr - 0.025, 0.03 if steel else 0.075)
        band(rim if steel else "rim_dark", lip, deep, radial=0.7, inward=True)
        fan(rim if steel else "car_trim", deep, X)
        if steel:                                              # pressed-steel wheel: dished centre + plain hub cap
            fan("rim_steel", ring(0.40 * r, 0.018)[::2], X)
            fan("rim_dark", ring(0.16 * r, 0.010)[::2], X)
        else:                                                  # five-spoke alloy + hub cap
            # alloy styles (generic): 5 wide, 10 thin, 7 medium, 5 wide dark with a bright machined lip
            ns, wi, wo, face = [(5, 0.050, 0.030, rimm), (10, 0.022, 0.015, rimm), (7, 0.036, 0.022, rimm),
                                (5, 0.062, 0.046, "rim_dark")][wst]
            for s in range(ns):
                t = 2 * math.pi * s / ns + 0.3
                u = np.array([0, math.cos(t), math.sin(t)])
                v = np.array([0, -math.sin(t), math.cos(t)])
                c0 = np.array([x_out - sx * 0.022, yc, r])
                r1 = rr - 0.016
                _quad(m, face, c0 + u * 0.05 - v * wi, c0 + u * r1 - v * wo - X * 0.006,
                      c0 + u * r1 + v * wo - X * 0.006, c0 + u * 0.05 + v * wi, X)
            fan(face, ring(0.21 * r, 0.014)[::2], X)
            fan("rim_dark", ring(0.08 * r, 0.011)[::2], X)
    else:
        A, B = ring((0.62 if steel else 0.70) * r, 0.004), ring(r, 0.03)
        band(tyre, A, B)
        band(tyre, B, ring(r, w), radial=1.0)
        fan("rim_steel" if steel else ("rim_dark" if wst == 3 else rimm), A, X)


def _vehicle2(d, paint, lod, steel=False, style=None):
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    m = Mesh()
    sh = _Shell(d, lod)
    L, hw, H = d["L"], d["W"] / 2, d["H"]
    sill, belt, r = d["sill"], d["belt"], d["r"]
    cargo = d.get("cargo", False)
    n = len(sh.P)
    gmat = "car_glass_tint" if lod == 0 else "car_glass"
    matname = {"paint": paint, "glass": gmat, "trim": "car_trim"}
    style = style or dict(dirt=0.5, wheel=0, uoff=0.0)
    dl = float(style["dirt"])                       # 0 fresh from the car wash .. 1 a month of winter streets
    dmat = f"car_dirt_{1 + min(2, int(dl * 3))}"
    uo = float(style["uoff"])
    ds = 0.70 + 0.30 * dl                           # glass dust reach (UV0 of car_glass_tint, see materials.py)

    # ---- top shell: crowned centre + shoulder arcs
    NT, NS = (3, 3) if lod == 0 else (1, 1)
    gs = ([-2 + k / NS for k in range(NS)] + [-1 + k / NT for k in range(2 * NT + 1)] + [1 + (k + 1) / NS for k in range(NS)])
    for i in range(n - 1):
        mat = matname[sh.emat[i]]
        A = [sh.pt(i, g) for g in gs]
        B = [sh.pt(i + 1, g) for g in gs]
        for j in range(len(gs) - 1):
            top = abs(gs[j]) <= 1 + 1e-9 and abs(gs[j + 1]) <= 1 + 1e-9
            mm = mat if (top or mat != gmat) else paint
            nn = A[j][1] + A[j + 1][1] + B[j][1] + B[j + 1][1]
            if mm == gmat and lod == 0:             # dust mask: 1 at the lower edge and the sides, 0.75 at the top
                va, vb = (-1.0, 0.75) if sh.P[i][1] < sh.P[i + 1][1] else (0.75, -1.0)
                _puv(m, mm, [A[j][0], A[j + 1][0], B[j + 1][0], B[j][0]],
                     [(gs[j] * ds, va * ds), (gs[j + 1] * ds, va * ds), (gs[j + 1] * ds, vb * ds), (gs[j] * ds, vb * ds)], nn)
            else:
                _quad(m, mm, A[j][0], A[j + 1][0], B[j + 1][0], B[j][0], nn)

    def patch(name, t0, t1, glist, mat, lift=0.006):
        i = sh.seg[name]
        for ga, gb in zip(glist[:-1], glist[1:]):
            q, nn = [], np.zeros(3)
            for t, g in ((t0, ga), (t0, gb), (t1, gb), (t1, ga)):
                p, nrm = sh.ptf(i, t, g)
                q.append(p + nrm * lift)
                nn += nrm
            _quad(m, mat, *q, nn)

    def spatch(name, cols, mat, lift=0.006, uv=None, v0=0.0):
        """Patch on the straight part of control edge `name`; cols = [(g, t0, t1)], quads between neighbours.
        uv = (u offset, u per g): v = 0 at t0, 1 at t1 (road film: t0 is the dirty end)."""
        i = sh.seg[name]
        for (ga, a0, a1), (gb, b0, b1) in zip(cols[:-1], cols[1:]):
            q, nn = [], np.zeros(3)
            for t, g in ((a0, ga), (b0, gb), (b1, gb), (a1, ga)):
                p, nrm = sh.ptf(i, t, g)
                q.append(p + nrm * lift)
                nn += nrm
            if uv is None:
                _quad(m, mat, *q, nn)
            else:
                ua, ub = uv[0] + ga * uv[1], uv[0] + gb * uv[1]
                _puv(m, mat, q, [(ua, v0), (ub, v0), (ub, 1.0), (ua, 1.0)], nn)

    # ---- side: columns between the profile's side line and the sill / wheel-arch line
    yfa = L / 2 - d["foh"]
    yra = yfa - d["wb"]
    ra = r + 0.05
    aseg = 10 if lod == 0 else 4

    def arch(yc):
        return [(yc - ra - 0.03, sill)] + [(yc - ra * math.cos(t), r + ra * math.sin(t))
                                           for t in np.linspace(0, math.pi, aseg + 1)] + [(yc + ra + 0.03, sill)]
    B = [tuple(sh.S[0])] + arch(yra) + arch(yfa) + [tuple(sh.S[-1])]
    By, Bz = np.array([b[0] for b in B]), np.array([b[1] for b in B])
    Sy, Sz = sh.S[:, 0], sh.S[:, 1]
    ys = sorted(set(np.round(np.concatenate([Sy, By]), 4)))
    ys = [float(y) for y in ys if Sy[0] - 1e-6 <= y <= Sy[-1] + 1e-6]
    ga0, ga1 = float(sh.bl0[0]), float(sh.bl1[0])
    NR = 4 if lod == 0 else 2

    def column(y):
        zt = float(np.interp(y, Sy, Sz))
        zb = float(np.interp(y, By, Bz))
        zm = min(zt, sh.zbelt(y)) if ga0 - 1e-6 <= y <= ga1 + 1e-6 else zt
        zm = max(zm, zb)
        return [np.array([sh.X(y, z), y, z]) for z in (zb + (zm - zb) * k / NR for k in range(NR + 1))]
    cols = [column(y) for y in ys]
    for ca, cb in zip(cols[:-1], cols[1:]):
        for k in range(NR):
            for sx in (1, -1):
                f = np.array([sx, 1, 1])
                _quad(m, paint, ca[k] * f, cb[k] * f, cb[k + 1] * f, ca[k + 1] * f, [sx, 0, 0])

    # ---- road film (alpha overlay): sills, lower doors, spray fans behind the wheels, arch lips
    ya_, yb_ = sh.y0 + 0.52, sh.y1 - 0.82                       # the straight part of the plan
    arch_top = r + ra

    def ztop(y):
        z = sill + 0.15 + 0.20 * dl
        for yc in (yra, yfa):
            z += (0.18 + 0.26 * dl) * math.exp(-((y - (yc - ra - 0.24)) / 0.30) ** 2)
        return z
    kd = 12 if lod == 0 else 3
    if lod == 0:
        runs = [sorted({round(float(y), 4) for y in By if ya_ < y < yb_} | {round(ya_ + (yb_ - ya_) * k / kd, 4) for k in range(kd + 1)})]
    else:                                    # LOD1: three plain runs between / beside the arches, no arch lips
        e = ra + 0.03
        runs = [[ya_, yra - e], [yra + e, yra + e + 0.45, (yra + yfa) / 2, yfa - e], [yfa + e, yb_]]
    rows = 2 if lod == 0 else 1

    def dcol(y):
        zb = float(np.interp(y, By, Bz))
        zt = min(max(ztop(y), zb + 0.11), arch_top + 0.16)
        return [(np.array([sh.X(y, zb + (zt - zb) * k / rows) + 0.008, y, zb + (zt - zb) * k / rows]), (y / 1.7 + uo, k / rows))
                for k in range(rows + 1)]
    for dys in runs:
        dc = [dcol(y) for y in dys]
        for ca, cb in zip(dc[:-1], dc[1:]):
            for k in range(rows):
                for sx in (1, -1):
                    fx = np.array([sx, 1, 1])
                    _puv(m, dmat, [ca[k][0] * fx, cb[k][0] * fx, cb[k + 1][0] * fx, ca[k + 1][0] * fx],
                         [ca[k][1], cb[k][1], cb[k + 1][1], ca[k + 1][1]], [sx, 0, 0])

    # ---- greenhouse side: frame with window openings (LOD0: see-through glass in the openings)
    ig0, ig4 = sh.mid["G0"], sh.mid["G4"]
    topc = [(float(sh.S[i, 0]), float(sh.S[i, 1])) for i in range(ig0, ig4 + 1)]
    beltc = [(y, float(sh.zbelt(y))) for y in ys if ga0 + 1e-4 < y < ga1 - 1e-4][::-1]
    outer = Polygon(topc + beltc).buffer(0)
    below = Polygon([(ga0 - 1, sh.zbelt(ga0 - 1) + 0.035), (ga1 + 1, sh.zbelt(ga1 + 1) + 0.035), (ga1 + 1, -1), (ga0 - 1, -1)])
    inner = outer.buffer(-0.05, join_style=2).difference(below)
    yB = ga1 - d["bp"]
    bands = [(yB + 0.04, ga1 - d["ap"] * 0.3)]
    if not cargo:
        if d["qp"]:
            bands += [(yB - d["qp"] + 0.035, yB - 0.04), (ga0 + d["cp"], yB - d["qp"] - 0.035)]
        else:
            bands += [(ga0 + d["cp"], yB - 0.04)]
    wins = []
    for ya, yb in bands:
        g = inner.intersection(box(ya, 0, yb, 3)).simplify(0.004)
        wins += [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 0.01]

    def side_tris(mat, tris, lift=0.0):
        for t in tris:
            for sx in (1, -1):
                q = [np.array([sx * (sh.X(y, z) + lift), y, z]) for y, z in t]
                _oq(m, mat, q, [sx, 0, 0])
    if lod == 0:
        side_tris(paint, _tri2d(outer.difference(unary_union(wins))))
        for wn in wins:                             # dust mask rises from the lower window edge
            for t in _tri2d(wn):
                for sx in (1, -1):
                    _puv(m, gmat, [np.array([sx * sh.X(y, z), y, z]) for y, z in t],
                         [(0.0, ds * (1.0 - 0.8 * min(1.0, max(0.0, (z - sh.zbelt(y)) / 0.42)))) for y, z in t], [sx, 0, 0])
    else:
        side_tris(paint, _tri2d(outer.simplify(0.003)))
        for wn in wins:
            side_tris(gmat, _tri2d(wn.simplify(0.02)), lift=0.008)

    # ---- wheels in the arches, liners
    for yc in (yra, yfa):
        A = arch(yc)
        xo = sh.X(yc, r) - 0.035
        for sx in (-1, 1):
            _wheel2(m, sx * xo, yc, r, sx, 16 if lod == 0 else 8, steel, lod, style["wheel"],
                    "rim_dusty" if dl > 0.45 else "rim", "tyre_dusty" if dl > 0.3 else "tyre")
            dep = 0.30 if lod == 0 else 0.24
            for (ya, za), (yb, zb_) in zip(A[:-1], A[1:]):
                mid = np.array([0, yc - (ya + yb) / 2, r - (za + zb_) / 2])
                xa, xb = sh.X(ya, za), sh.X(yb, zb_)
                _quad(m, "car_trim", [sx * xa, ya, za], [sx * xb, yb, zb_], [sx * (xb - dep), yb, zb_],
                      [sx * (xa - dep), ya, za], mid)
                if d.get("clad") and lod == 0:
                    k = (ra + 0.06) / ra
                    y2a, z2a = yc + (ya - yc) * k, max(sill, r + (za - r) * k)
                    y2b, z2b = yc + (yb - yc) * k, max(sill, r + (zb_ - r) * k)
                    _quad(m, "car_sill", [sx * (xa + 0.006), ya, za], [sx * (xb + 0.006), yb, zb_],
                          [sx * (sh.X(y2b, z2b) + 0.006), y2b, z2b], [sx * (sh.X(y2a, z2a) + 0.006), y2a, z2a], [sx, 0, 0])
    zfl = sill + 0.06
    _quad(m, "car_trim", [hw - 0.10, -L / 2 + 0.2, zfl], [-hw + 0.10, -L / 2 + 0.2, zfl], [-hw + 0.10, L / 2 - 0.2, zfl],
          [hw - 0.10, L / 2 - 0.2, zfl], [0, 0, -1])

    # ---- lamps, grille, intakes, plates (patches on the shell; lamps taper inward and wrap into the wing)
    f = FACES[d.get("face", "swept")]
    li0, li1, lo0, lo1 = f["lamp"]
    lg = [0.40, 0.70, 1.0, 1.4, 1.8] if lod == 0 else [0.42, 1.0, 1.7]

    def lamp_cols(sx, a, b):                         # a, b = fractions of the lamp height (0 top .. 1 bottom)
        out = []
        for g in lg:
            k = (g - lg[0]) / (lg[-1] - lg[0])
            top, bot = li0 + (lo0 - li0) * k, li1 + (lo1 - li1) * k
            out.append((sx * g, top + (bot - top) * a, top + (bot - top) * b))
        return out
    tg = [0.34, 0.8, 1.0, 1.4, 1.8] if lod == 0 else [0.36, 1.0, 1.7]
    for sx in (-1, 1):
        spatch("H1", lamp_cols(sx, 0.0, 1.0), "car_lamp")
        if lod == 0:
            spatch("H1", lamp_cols(sx, 0.07, 0.36)[:-1], "car_light_head", lift=0.009)   # reflector / running-light strip
            spatch("H1", lamp_cols(sx, 0.50, 0.90)[1:3], "car_light_head", lift=0.009)   # main beam unit
        if cargo:
            patch("R1", 0.30, 0.97, [sx * g for g in ([1.0, 1.35, 1.7] if lod == 0 else [1.0, 1.6])], "car_light_tail")
        else:
            spatch("R1", [(sx * g, 0.82 - 0.14 * (g - tg[0]) / (tg[-1] - tg[0]), 0.97) for g in tg], "car_light_tail")
            if lod == 0:
                patch("R1", 0.05, 0.11, [sx * 1.05, sx * 1.5], "car_light_tail")           # bumper reflector
    if f["bar"] and not cargo and lod == 0:
        patch("R1", 0.905, 0.945, [-0.34, 0.0, 0.34], "car_light_tail")                    # light bar across the boot
    gw, gt = f["gw"], f["gt"]
    if lod == 0:
        spatch("H1", [(-gw, gt + 0.10, 0.80), (-0.72 * gw, gt, 0.98), (0.0, gt, 0.98), (0.72 * gw, gt, 0.98),
                      (gw, gt + 0.10, 0.80)], "car_trim")                                  # grille (chamfered corners)
        spatch("F1", [(-0.80, 0.26, 0.78), (-0.58, 0.12, 0.92), (0.0, 0.12, 0.92), (0.58, 0.12, 0.92),
                      (0.80, 0.26, 0.78)], "car_trim")                                     # lower intake
    else:
        patch("H1", gt + 0.03, 0.95, [-0.9 * gw, 0.0, 0.9 * gw], "car_trim")
        patch("F1", 0.15, 0.90, [-0.72, 0.0, 0.72], "car_trim")
    if lod == 0:
        for k in (1, 2):
            t = gt + (0.70 - gt) * k / 3
            patch("H1", t, t + 0.03, [-0.70 * gw, 0.0, 0.70 * gw], "rim_dark", lift=0.009)  # grille slats
        if d.get("face") == "wide":
            patch("H1", gt - 0.035, gt, [-0.72 * gw, 0.0, 0.72 * gw], "rim", lift=0.009)   # bright strip on the grille
        for sx in (-1, 1):                                                                 # corner intakes
            spatch("F1", [(sx * 1.05, 0.12, 0.62), (sx * 1.32, 0.06, 0.72), (sx * 1.62, 0.12, 0.56)], "car_trim")
        patch("R1", 0.0, 0.13, [-0.72, 0.0, 0.72], "car_trim")                             # rear valance insert
        if not cargo:                                                                      # roof aerial fin
            pr = sh.pt(sh.mid["G1"], 0.0)[0]
            _box5(m, "car_trim", [0, pr[1] + 0.16, pr[2] + 0.025], 0.02, 0.075, 0.03, (0, 0, -1))
    for name, tc in (("H1", 0.80), ("R1", 0.30)):
        i = sh.seg[name]
        ln = float(np.linalg.norm(sh.P[i + 1] - sh.P[i]))
        xt = sh.pt(i, 1.0)[0][0]
        patch(name, tc - 0.056 / ln, tc + 0.056 / ln, [-0.26 / xt, 0.26 / xt], "car_plate", lift=0.014)
    # road film on the tail (dirtiest face of a car) and the lower front bumper
    dg = [-1.8, -1.0, -0.34, 0.34, 1.0, 1.8] if lod == 0 else [-1.7, 0.0, 1.7]
    spatch("R1", [(g, 0.0, 0.55 + 0.40 * dl) for g in dg], dmat, lift=0.015, uv=(uo, 0.45))
    if lod == 0:
        spatch("F1", [(g, 1.0, 0.0) for g in dg], dmat, lift=0.012, uv=(uo + 0.37, 0.45), v0=0.62 - 0.30 * dl)   # thin: splatter

    # ---- sills, seams, handles, mirrors, rails
    def strip(mat, pts, wy, lift=0.004):            # vertical seam along (y, z) points, 2 * wy wide
        for (ya, za), (yb, zb_) in zip(pts[:-1], pts[1:]):
            for sx in (-1, 1):
                _quad(m, mat, [sx * (sh.X(ya, za) + lift), ya - wy, za], [sx * (sh.X(ya, za) + lift), ya + wy, za],
                      [sx * (sh.X(yb, zb_) + lift), yb + wy, zb_], [sx * (sh.X(yb, zb_) + lift), yb - wy, zb_], [sx, 0, 0])
    ys0, ys1 = yra + ra + 0.04, yfa - ra - 0.04
    zs = sill + (0.17 if d.get("clad") else 0.085)
    nsl = 4 if lod == 0 else 1
    for k in range(nsl):
        ya, yb = ys0 + (ys1 - ys0) * k / nsl, ys0 + (ys1 - ys0) * (k + 1) / nsl
        for sx in (-1, 1):
            _quad(m, "car_sill", [sx * (sh.X(ya, sill) + 0.005), ya, sill], [sx * (sh.X(yb, sill) + 0.005), yb, sill],
                  [sx * (sh.X(yb, zs) + 0.005), yb, zs], [sx * (sh.X(ya, zs) + 0.005), ya, zs], [sx, 0, 0])
    yM = ga1 - 0.16
    zM = sh.zbelt(yM) + 0.085
    for sx in (-1, 1):
        c = [sx * (sh.X(yM, zM) + 0.085), yM, zM]
        if lod == 0:
            _box5(m, paint, c, 0.085, 0.035, 0.055, (-sx, 0, 0))
            _quad(m, "car_glass", [c[0] - 0.07, yM - 0.037, zM - 0.04], [c[0] + 0.07, yM - 0.037, zM - 0.04],
                  [c[0] + 0.07, yM - 0.037, zM + 0.04], [c[0] - 0.07, yM - 0.037, zM + 0.04], [0, -1, 0])
        else:
            for s in (-1, 1):
                _quad(m, paint, [c[0] - 0.085, yM + s * 0.03, zM - 0.055], [c[0] + 0.085, yM + s * 0.03, zM - 0.055],
                      [c[0] + 0.085, yM + s * 0.03, zM + 0.055], [c[0] - 0.085, yM + s * 0.03, zM + 0.055], [0, s, 0])
    if lod == 0:
        def vline(y, za, zb_):
            return [(y, za + (zb_ - za) * k / 4) for k in range(5)]
        y1d = yfa + ra + 0.09
        y3d = (yra + 0.14) if not cargo else (yB - 1.05)
        strip("car_trim", vline(y1d, sill + 0.09, min(sh.zbelt(y1d), float(np.interp(y1d, Sy, Sz))) - 0.02), 0.006)
        strip("car_trim", vline(yB, sill + 0.09, sh.zbelt(yB) - 0.004), 0.006)
        strip("car_trim", vline(y3d, (r + ra + 0.02) if not cargo else sill + 0.09, sh.zbelt(y3d) - 0.004), 0.006)
        for y in (yB + 0.10, y3d + 0.12):                       # door handles
            zh = sh.zbelt(y) - 0.09
            for sx in (-1, 1):
                x = sx * (sh.X(y, zh) + 0.012)
                _quad(m, "car_trim" if cargo else paint, [x, y, zh], [x, y + 0.15, zh], [x, y + 0.15, zh + 0.028],
                      [x, y, zh + 0.028], [sx, 0, 0])
        for name, t in (("H0", 0.03), ("R2", 0.85)):            # bonnet shut line at the cowl, tailgate / boot line
            ln = float(np.linalg.norm(sh.P[sh.seg[name] + 1] - sh.P[sh.seg[name]]))
            patch(name, t, t + 0.012 / max(1e-3, ln), [-1.0, -0.5, 0.0, 0.5, 1.0], "car_trim", lift=0.003)
        if d.get("rails"):
            g1, g3 = sh.P[sh.mid["G1"]], sh.P[sh.mid["G3"]]
            for sx in (-1, 1):
                pr = sh.pt(sh.mid["G2"], sx * 0.93)[0]
                _box5(m, "car_trim", [pr[0], (g1[0] + g3[0]) / 2 - 0.05, pr[2] + 0.015], 0.016,
                      (g3[0] - g1[0]) / 2 - 0.25, 0.02, (0, 0, -1))

        # ---- interior seen through the glass: tub, dashboard, seats with headrests, headliner
        it = "car_interior"
        yi0, yi1 = ga0 + 0.10, ga1 + 0.05
        xi = hw - 0.13
        zf0 = sill + 0.12
        _quad(m, it, [-xi, yi0, zf0], [xi, yi0, zf0], [xi, yi1, zf0], [-xi, yi1, zf0], [0, 0, 1])
        for sx in (-1, 1):
            _quad(m, it, [sx * xi, yi0, zf0], [sx * xi, yi1, zf0], [sx * xi, yi1, sh.zbelt(yi1)],
                  [sx * xi, yi0, sh.zbelt(yi0)], [-sx, 0, 0])
        _quad(m, it, [-xi, yi0, zf0], [xi, yi0, zf0], [xi, yi0, sh.zbelt(yi0)], [-xi, yi0, sh.zbelt(yi0)], [0, 1, 0])
        zd = belt - 0.03
        _box5(m, it, [0, yi1 - 0.27, (zd + zf0) / 2], xi, 0.27, (zd - zf0) / 2, (0, 0, -1))          # dashboard
        zh_ = sh.zroof - 0.10
        g1, g3 = sh.P[sh.mid["G1"]], sh.P[sh.mid["G3"]]
        xh = hw - d["tumble"] - 0.10
        _quad(m, it, [-xh, g1[0], zh_], [xh, g1[0], zh_], [xh, g3[0], zh_], [-xh, g3[0], zh_], [0, 0, -1])
        ysb = yB + 0.02
        zs0 = zf0 + 0.20
        for sx in (-1, 1):                                                                             # front seats
            _box5(m, it, [sx * 0.37, ysb, (zs0 + belt + 0.12) / 2], 0.24, 0.07, (belt + 0.12 - zs0) / 2, (0, 0, -1))
            _box5(m, it, [sx * 0.37, ysb + 0.02, belt + 0.25], 0.12, 0.05, 0.095, (0, 0, -1))
            _box5(m, it, [sx * 0.37, ysb + 0.30, zf0 + 0.27], 0.24, 0.25, 0.07, (0, 0, -1))
        if cargo:
            _quad(m, it, [-xi, ysb - 0.12, zf0], [xi, ysb - 0.12, zf0], [xi, ysb - 0.12, H - 0.15],
                  [-xi, ysb - 0.12, H - 0.15], [0, 1, 0])
        else:
            yrs = max(yra + 0.12, ga0 + 0.55)
            _box5(m, it, [0, yrs, (zs0 + belt + 0.08) / 2], 0.64, 0.08, (belt + 0.08 - zs0) / 2, (0, 0, -1))
            for sx in (-1, 1):
                _box5(m, it, [sx * 0.36, yrs + 0.02, belt + 0.17], 0.11, 0.05, 0.075, (0, 0, -1))
            _quad(m, it, [-xi, yi0, sh.zbelt(yi0) - 0.02], [xi, yi0, sh.zbelt(yi0) - 0.02], [xi, yrs, belt - 0.02],
                  [-xi, yrs, belt - 0.02], [0, 0, 1])                                                  # parcel shelf
    return _paint_uv(m)


def _style(name):
    """Per-prototype look (deterministic): dirt level, alloy style, film pattern offset."""
    h = zlib.crc32(name.encode())
    return dict(dirt=(h & 255) / 255.0, wheel=(h >> 8) % 4, uoff=((h >> 16) & 255) / 255.0)


def _build(d, paint, steel=False, name=""):
    col = Mesh()
    col.box("collision_vehicle", [0, 0, d["H"] / 2], d["W"] / 2, d["L"] / 2, d["H"] / 2)
    st = _style(name)
    return _vehicle2(d, paint, 0, steel, st), _vehicle2(d, paint, 1, steel, st), col, _vehicle(d, paint, 1)


def car(body, colour):
    # pressed-steel wheels on the plain white hatch / estate (WORKING_VALUE fleet look), alloys elsewhere
    return _build(CARS[body], f"car_paint_{colour}", steel=(colour == "white" and body in ("hatch", "estate")),
                  name=f"{body}_{colour}")


def van(colour):
    return _build(VAN, f"car_paint_{colour}", steel=True, name=f"van_{colour}")
