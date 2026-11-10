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
    "hatch": dict(L=4.06, W=1.75, H=1.46, wb=2.56, foh=0.84, r=0.305, sill=0.20, belt=0.93, nose=0.78, hood=1.02,
                  ws=0.78, tail=(0.09, 1.03), deck=0.0, rg=(0.52, 0.04), tumble=0.17, bp=1.04, qp=None, cp=0.24,
                  ap=0.10),
    "sedan": dict(L=4.62, W=1.80, H=1.44, wb=2.70, foh=0.90, r=0.315, sill=0.20, belt=0.93, nose=0.77, hood=1.14,
                  ws=0.80, tail=(0.06, 1.01), deck=0.46, rg=(1.24, 0.045), tumble=0.18, bp=1.04, qp=None, cp=0.20,
                  ap=0.10),
    "estate": dict(L=4.68, W=1.80, H=1.47, wb=2.70, foh=0.90, r=0.315, sill=0.20, belt=0.93, nose=0.77, hood=1.14,
                   ws=0.80, tail=(0.09, 1.04), deck=0.0, rg=(0.40, 0.035), tumble=0.17, bp=1.04, qp=0.98, cp=0.13,
                   ap=0.10, rails=True),
    "suv": dict(L=4.36, W=1.82, H=1.62, wb=2.62, foh=0.88, r=0.345, sill=0.27, belt=1.05, nose=0.93, hood=1.06,
                ws=0.70, tail=(0.09, 1.17), deck=0.0, rg=(0.46, 0.04), tumble=0.15, bp=1.02, qp=0.92, cp=0.20,
                ap=0.10, rails=True, clad=True),
}
VAN = dict(L=4.50, W=1.83, H=1.85, wb=2.78, foh=0.87, r=0.32, sill=0.23, belt=1.10, nose=0.97, hood=0.78,
           ws=0.56, tail=(0.035, 1.12), deck=0.0, rg=(0.10, 0.05), tumble=0.07, bp=1.02, qp=None, cp=0.10, ap=0.10,
           cargo=True)


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


def _build(d, paint):
    col = Mesh()
    col.box("collision_vehicle", [0, 0, d["H"] / 2], d["W"] / 2, d["L"] / 2, d["H"] / 2)
    return _vehicle(d, paint, 0), _vehicle(d, paint, 1), col, _vehicle(d, paint, 2)


def car(body, colour):
    return _build(CARS[body], f"car_paint_{colour}")


def van(colour):
    return _build(VAN, f"car_paint_{colour}")
