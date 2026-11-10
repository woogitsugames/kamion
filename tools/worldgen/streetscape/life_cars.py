"""Parked-vehicle prototypes (ADR 0041 par. 6, ADR 0073): generic passenger cars and a mid-size panel van, built
from a side profile (the way a car body is drawn). Frame as streetscape.props: x = right, y = nose, z = up,
origin = centre of the footprint on the ground.

No make or model is reproduced: each body is a class average (lengths, wheelbases and heights below are typical
values of the European C/D segments, C-SUV and mid-size panel vans, all WORKING_VALUE; proportions checked against
street photos of the route, used as a pattern only) with no grille shape, lamp signature or badge of any real
vehicle. Registration plates: fictional strings in the Polish format (plate_atlas, REVIEW r6 W-N9), generated from
a seed, not taken from any register.

  LOD0 / LOD1  r9 shell (_Shell, _vehicle2): profile swept across x with a crowned top, shoulder arcs and side
               columns whose rows lie on the body's feature lines; lamp units, seams, wheels, glazing over a dark
               interior (LOD0), road film overlays
  LOD2         first-pass body (_vehicle): the profile without shoulders, glazed greenhouse, under-body skirt
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
    # r9 (ADR 0073): class-typical proportions re-read off street photos of the route (Mapillary, proportions only):
    # longer bonnets (cowl 0.2 m behind the front axle), 29-32 deg windscreens, near-vertical fascias, bumper ledges.
    "hatch": dict(L=4.26, W=1.79, H=1.46, wb=2.62, foh=0.88, r=0.316, sill=0.19, belt=1.05, nose=0.86, hood=1.00,
                  ws=0.76, tail=(0.11, 1.04), deck=0.0, rg=(0.44, 0.055), tumble=0.17, bp=1.30, qp=None, cp=0.34,
                  ap=0.10, face="swept", plan=(0.78, 0.23, 0.55, 0.13), flare=0.020),
    "sedan": dict(L=4.64, W=1.80, H=1.44, wb=2.70, foh=0.90, r=0.320, sill=0.19, belt=1.03, nose=0.83, hood=1.12,
                  ws=0.80, tail=(0.06, 1.06), deck=0.44, rg=(1.10, 0.05), tumble=0.18, bp=1.30, qp=None, cp=0.24,
                  ap=0.10, face="wide", plan=(0.82, 0.24, 0.60, 0.14), flare=0.018),
    "estate": dict(L=4.66, W=1.80, H=1.48, wb=2.70, foh=0.90, r=0.320, sill=0.19, belt=1.03, nose=0.83, hood=1.12,
                   ws=0.80, tail=(0.10, 1.05), deck=0.0, rg=(0.40, 0.05), tumble=0.17, bp=1.30, qp=1.00, cp=0.13,
                   ap=0.10, rails=True, face="swept", plan=(0.82, 0.24, 0.55, 0.12), flare=0.018),
    "suv": dict(L=4.42, W=1.84, H=1.65, wb=2.66, foh=0.90, r=0.350, sill=0.25, belt=1.20, nose=1.03, hood=1.04,
                ws=0.70, tail=(0.10, 1.20), deck=0.0, rg=(0.44, 0.06), tumble=0.16, bp=1.28, qp=0.92, cp=0.20,
                ap=0.10, rails=True, clad=True, face="tall", plan=(0.70, 0.20, 0.50, 0.11), flare=0.030),
}
# Mid-size panel van ("furgon", r9: replaces the 4.5 m car-derived van): short steep bonnet, upright screen, slab
# sides with a sliding-door track, barn doors, unpainted bumpers, pressed-steel wheels. WORKING_VALUE class averages.
VAN = dict(L=4.90, W=1.93, H=1.97, wb=3.00, foh=0.93, r=0.345, sill=0.27, belt=1.27, nose=1.08, hood=0.66,
           ws=0.62, tail=(0.03, 1.26), deck=0.0, rg=(0.07, 0.05), tumble=0.07, bp=1.18, qp=None, cp=0.10, ap=0.10,
           cargo=True, face="van", plan=(0.62, 0.20, 0.32, 0.06), flare=0.016, blackbump=True)

# Front faces (generic class looks, no make reproduced). Fractions t along the upper fascia edge (bonnet lip ->
# bumper peak): lamp top / bottom at the inner and outer end; g = across coordinate of the shell (1 = where the
# corner arc starts, 2 = the side line): lamp inner / outer end, grille half width, grille top; bar = light bar.
FACES = {
    "swept": dict(lean=0.060, band=0.28, lamp=(0.10, 0.70, 0.00, 0.78), lg=(0.52, 1.95), gw=0.44, gt=0.30, bar=False),
    "wide": dict(lean=0.055, band=0.27, lamp=(0.06, 0.62, 0.00, 0.70), lg=(0.58, 1.95), gw=0.52, gt=0.16, bar=True),
    "tall": dict(lean=0.040, band=0.31, lamp=(0.04, 0.56, 0.00, 0.60), lg=(0.62, 1.92), gw=0.56, gt=0.12, bar=False),
    "van": dict(lean=0.050, band=0.30, lamp=(0.06, 0.80, 0.02, 0.74), lg=(0.66, 1.92), gw=0.60, gt=0.14, bar=False),
}


# ------------------------------------------------------------------------------------------- registration plates
# Polish plate 520 x 114 mm (EU band 40 mm, white retro-reflective field, black characters). Atlas of PLATE_COLS x
# PLATE_ROWS cells (256 x 64 px, plate 248 x 54 px centred: the margin keeps the mips from bleeding); one cell per
# prototype, the last cell is the far plate (EU band + grey character band) used by LOD1.
PLATE_COLS, PLATE_ROWS = 4, 8
PRIVACY_U = 4.0         # UV0 u offset of privacy-tinted panes (car_glass_tint, decoded in WorldCarGlass.shader)
TYRE_REP = 8.0          # tread texture repeats around a tyre (car_tyre: one tile = 1 / 8 of the circumference)
LENS_U = 8.0            # UV0 u offset of clear lamp covers (r10, ADR 0078; same material and draw as the glazing)
PLATE_FAR = PLATE_COLS * PLATE_ROWS - 1
# district codes of Bialystok and the neighbouring powiats, WORKING_VALUE shares of a Bialystok car park
PLATE_DISTRICTS = [("BI", 0.55), ("BIA", 0.28), ("BSK", 0.08), ("BMN", 0.05), ("BBI", 0.04)]
# letters of the vehicle part: B D I O Z are not used there (confusable with 8 0 1 0 2; UNVERIFIED reading of the
# registration ordinance). Characters come from a seeded generator, not from any register.
PLATE_LETTERS = "ACEFGHJKLMNPRSTUVWXY"
PLATE_FORMATS = {2: ["99999", "9999A", "999AA", "9A999", "9AA99"], 3: ["9999A", "999AA", "99999", "9A99", "99AA"]}


def plate_text(k, seed=2026):
    """Fictional plate string of atlas cell k (deterministic)."""
    h = zlib.crc32(f"plate:{seed}:{k}".encode())
    u = (h & 0xFFFF) / 65536.0
    acc, code = 0.0, PLATE_DISTRICTS[-1][0]
    for c, w in PLATE_DISTRICTS:
        acc += w
        if u < acc:
            code = c
            break
    fm = PLATE_FORMATS[len(code)]
    f = fm[(h >> 16) % len(fm)]
    out = []
    for j, ch in enumerate(f):
        hj = zlib.crc32(f"plate:{seed}:{k}:{j}".encode())
        if ch == "9":
            out.append(str((hj % 9) + 1) if j == 0 else str(hj % 10))
        else:
            out.append(PLATE_LETTERS[hj % len(PLATE_LETTERS)])
    return code, "".join(out)


def plate_atlas(n=PLATE_FAR):
    """RGB atlas (PIL) of n fictional plates + the far plate in the last cell."""
    from PIL import Image, ImageDraw, ImageFilter
    from .signs import _font
    CW, CH, PW, PH, SS = 256, 64, 248, 54, 4
    atlas = Image.new("RGB", (CW * PLATE_COLS, CH * PLATE_ROWS), (200, 201, 198))
    W, H = PW * SS, PH * SS
    eu = int(round(40 / 520 * W))

    def blank(k):
        im = Image.new("RGB", (W, H), (214, 215, 211))
        d = ImageDraw.Draw(im)
        d.rectangle([0, 0, eu, H], fill=(20, 52, 138))
        cx, cy, r = eu / 2, H * 0.34, H * 0.17
        for a in range(12):                                     # ring of stars (dots at this size)
            t = a * math.pi / 6
            x, y = cx + r * math.cos(t), cy + r * math.sin(t)
            d.ellipse([x - SS * 1.1, y - SS * 1.1, x + SS * 1.1, y + SS * 1.1], fill=(214, 190, 40))
        f = _font(int(H * 0.26))
        bb = d.textbbox((0, 0), "PL", font=f)
        d.text((cx - (bb[2] - bb[0]) / 2 - bb[0], H * 0.62 - bb[1]), "PL", font=f, fill=(225, 225, 225))
        d.rectangle([0, 0, W - 1, H - 1], outline=(70, 70, 68), width=int(SS * 1.5))       # embossed rim
        return im, d
    for k in range(n + 1):
        im, d = blank(k)
        x0 = eu + SS * 6
        if k < n:
            code, rest = plate_text(k)
            f = _font(int(H * 0.80))
            # characters: rendered at the font's width, then condensed into the field (the plate font is narrow)
            txt = f"{code} {rest}"
            bb = d.textbbox((0, 0), txt, font=f)
            rb = d.textbbox((0, 0), "BI 0123", font=f)          # cap height reference (no descenders: J, Q)
            tw, th = bb[2] - bb[0], rb[3] - rb[1]
            tl = Image.new("L", (tw + 8, th + 8), 0)
            ImageDraw.Draw(tl).text((4 - bb[0], 4 - rb[1]), txt, font=f, fill=255)
            fw = W - x0 - SS * 10
            th2 = int(H * 0.62)
            tl = tl.resize((min(fw, int(tw * th2 / th * 0.80)), th2), Image.LANCZOS)
            ox = x0 + (fw - tl.size[0]) // 2
            im.paste((24, 24, 24), (ox, (H - th2) // 2), tl)
        else:                                                   # far plate: grey band where the characters are
            rng = np.random.default_rng(7)
            bw, bh = W - x0 - SS * 14, int(H * 0.58)
            band = (rng.random((6, 30)) * 50 + 120).astype(np.uint8)
            bimg = Image.fromarray(band, "L").resize((bw, bh), Image.BILINEAR).filter(ImageFilter.GaussianBlur(SS * 2))
            mask = Image.new("L", (bw, bh), 0)
            ImageDraw.Draw(mask).rectangle([SS * 3, SS * 3, bw - SS * 3, bh - SS * 3], fill=255)
            mask = mask.filter(ImageFilter.GaussianBlur(SS * 3))
            im.paste(Image.merge("RGB", (bimg, bimg, bimg)), (x0 + SS * 4, (H - bh) // 2), mask)
        # road film: darker towards the lower edge, deterministic per plate
        g = np.asarray(im, np.float32)
        v = np.linspace(0, 1, H)[:, None, None]
        amt = 0.05 + 0.10 * ((zlib.crc32(f"pdirt:{k}".encode()) & 255) / 255.0)
        g = g * (1.0 - amt * v ** 2) + np.array([92, 82, 66], np.float32) * (amt * v ** 2)
        im = Image.fromarray(np.clip(g, 0, 255).astype(np.uint8), "RGB").resize((PW, PH), Image.LANCZOS)
        c, r = k % PLATE_COLS, k // PLATE_COLS
        cell = im.resize((CW, CH), Image.LANCZOS)               # margin = edge texels of the plate (no bleed)
        cell.paste(im, ((CW - PW) // 2, (CH - PH) // 2))
        atlas.paste(cell, (c * CW, r * CH))
    return atlas


def tyre_texture(w=256, h=256, seed=5):
    """Tread / sidewall modulation of car LOD0 tyres (r10, ADR 0078), RGB, tiles in u (one tile = 1 / TYRE_REP of the
    circumference, ~0.25 m). Generator v: 0-0.5 sidewall from the rim edge to the shoulder, 0.5-1 tread across.
    Generic pattern (four circumferential grooves, siped ribs, slotted shoulders): no make's tread, no lettering."""
    from PIL import Image
    rng = np.random.default_rng(seed)
    g = np.full((h, w), 205.0)
    x = np.arange(w)[None, :]
    v = (1.0 - (np.arange(h) + 0.5) / h)[:, None]          # generator v per image row
    side = v < 0.5
    g = np.where(side & (np.abs(v - 0.055) < 0.012), 150.0, g)                       # rim protector step
    ribs = (np.floor(v * h / 3) % 2) * 26.0 - 13.0
    g = g + np.where(side & (v > 0.30) & (v < 0.40), ribs, 0.0)                       # concentric ribs band
    slot = ((x + 6) % 32) < 6
    g = np.where(side & (v > 0.435) & slot, 95.0, g)                                  # shoulder slots
    a = (v - 0.5) / 0.5                                                               # 0 outer tread edge .. 1 inner
    tread = ~side
    g = np.where(tread, 222.0, g)
    for c in (0.22, 0.41, 0.59, 0.78):
        g = np.where(tread & (np.abs(a - c) < 0.021), 62.0, g)
    slant = (x + (a * 60).astype(int)) % 16
    g = np.where(tread & (a > 0.24) & (a < 0.76) & (slant < 2) & (g > 100), 140.0, g)   # sipes in the centre ribs
    g = np.where(tread & ((a < 0.17) | (a > 0.83)) & slot, 80.0, g)                      # shoulder blocks
    g = g + rng.normal(0.0, 5.0, (h, w))
    g[-2:, :] = 205.0                                       # v ~ 0: plain row (primitives without UVs sample it)
    g = np.clip(g, 0, 255).astype(np.uint8)
    return Image.fromarray(np.dstack([g, g, g]), "RGB")


def plate_uv(k):
    """(u0, v0, u1, v1) of the plate inside atlas cell k (generator UVs: v = 0 at the image bottom)."""
    c, r = k % PLATE_COLS, k // PLATE_COLS
    du, dv = 1.0 / PLATE_COLS, 1.0 / PLATE_ROWS
    mu, mv = (256 - 248) / 2 / 256 * du, (64 - 54) / 2 / 64 * dv
    return c * du + mu, 1.0 - (r + 1) * dv + mv, (c + 1) * du - mu, 1.0 - r * dv - mv


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
        # LOD2 (far rows, 135-300 m High / 45-300 m Low): dark under-body band between the axles + one hexagonal
        # tyre disc per wheel (the round wheels are what still reads at 15-40 px; a black band reads as "legs")
        ya, yb = yra - r - 0.10, yfa + r + 0.10
        # r8 N-13: the dark under-body is a closed skirt (two side bands + two cross quads on one rectangle inside the
        # body's lower edge). Before: bands between the axles at hw - 0.01 and cross quads as wide, which stuck out
        # beside the tapered bumpers and left the far wheel discs' culled backs (= the paving) visible under the body.
        xc, z0, z1 = hw - 0.14, 0.03, sill + 0.02
        for sx in (-1, 1):
            _oq(m, "tyre", [[sx * xc, ya, z0], [sx * xc, yb, z0], [sx * xc, yb, z1], [sx * xc, ya, z1]], [sx, 0, 0])
            for yc in (yra, yfa):
                _disc(m, "tyre", [sx * (hw + 0.006), yc, r], r, 6, sx, math.pi / 6)
        for yy, s in ((ya, -1), (yb, 1)):
            _oq(m, "tyre", [[xc, yy, z0], [-xc, yy, z0], [-xc, yy, z1], [xc, yy, z1]], [0, s, 0])

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




# =========================================================================================== r9 bodies (ADR 0073)
# LOD0 / LOD1. The shell is still a side profile swept across x (crowned top, shoulder arcs, side columns down to the
# sill / wheel-arch line), but r9 re-draws WHAT is swept so that the bodies stop reading as bars of soap:
#   profile   bonnet as a convex arc from the cowl to a tight lip, near-vertical lamp band, bumper face, chin; rear
#             bumper with a ledge under the tailgate; roof with its peak over the B pillar
#   plan      super-elliptic corners (straight wings, then a real corner) instead of a boat-shaped quarter ellipse
#   section   lower-body tuck, vertical door skin, shoulder facet under the belt line (catches the sky), tumblehome;
#             the side rows sit ON those feature lines; wheel-arch flares + lip rings
#   details   lamp units with a bright lens in a dark housing that wrap into the wings, tail-lamp clusters, bonnet
#             and door shut lines, bumper seams, black B pillars, cowl panel, wipers, recessed handles, mirrors
# The first-pass _vehicle(lod=1) above is LOD2.
def _controls(d):
    L, H = d["L"], d["H"]
    y0, y1 = -L / 2, L / 2
    sill, belt = d["sill"], d["belt"]
    zr, zf = sill + 0.04, sill + 0.03
    ty, tz = d["tail"]
    yA = y1 - d["hood"]
    yF = yA - d["ws"]
    yR = y0 + d["rg"][0]
    cargo = d.get("cargo", False)
    f = FACES[d.get("face", "swept")]
    bump = "bump" if d.get("blackbump") else "paint"
    bt = d.get("bt", sill + 0.40)                      # rear bumper ledge
    zl = d["nose"]                                     # bonnet lip
    zp = zl - f["band"]                                # bumper peak under the lamp band
    yL = y1 - f["lean"]

    def c(n, y, z, R, CR, mat, rnd=1):
        return dict(n=n, y=y, z=z, R=R, CR=CR, mat=mat, rnd=rnd)

    def hood(t):                                       # convex arc cowl -> lip
        return yA + t * (yL - yA), belt + t * (zl - belt) + 0.035 * 4 * t * (1 - t)
    C = [c("R0", y0 + 0.14, zr, 0.03, 0.0, "trim", 0),
         c("R1", y0 + 0.012, zr + 0.07, 0.11, 0.035, bump, 1),
         c("RB", y0, bt, 0.11, 0.04, "paint", 0),
         c("R2", y0 + 0.035, bt + 0.025, 0.10, 0.04, "paint", 0)]
    if d["deck"] > 0:
        C += [c("R3", y0 + ty, tz, 0.09, 0.035, "paint", 1),
              c("G0", y0 + ty + d["deck"], tz + 0.02, 0.085, 0.03, "glass", 1)]
    else:
        C.append(c("G0", y0 + ty, tz, 0.085, 0.03, "paint" if cargo else "glass", 1))
    C += [c("G1", yR, H - d["rg"][1], 0.085, 0.035, "paint", 1),
          c("G2r", yF - 0.70 * (yF - yR), H - 0.012, 0.085, 0.035, "paint", 0),
          c("G2", yF - 0.30 * (yF - yR), H, 0.085, 0.035, "paint", 0),
          c("G3", yF, H - 0.035, 0.08, 0.035, "glass", 1),
          c("G4", yA, belt, 0.06, 0.03, "paint", 1),
          c("H0", *hood(0.36), 0.055, 0.04, "paint", 0),
          c("H0b", *hood(0.72), 0.06, 0.045, "paint", 0),
          c("H1", yL, zl, 0.075, 0.055, "paint", 2),
          c("F1", y1 - 0.004, zp, 0.14, 0.085, bump, 1),
          c("F2", y1 - 0.022, zf + 0.085, 0.14, 0.075, "trim", 1),
          c("F3", y1 - 0.15, zf, 0.03, 0.0, "trim", 0)]
    return C


class _Shell:
    def __init__(self, d, lod):
        self.d, self.lod = d, lod
        C = _controls(d)
        if lod > 0:                              # LOD1: no intermediate roof / bonnet stations
            C = [c for c in C if c["n"] not in ("G2r", "H0b", "RB")]
        P, R, CR, tag = [], [], [], []           # dense points; tag = (control index, part) part: 0 QA, 1 M, 2 QB
        cp = np.array([[c["y"], c["z"]] for c in C])
        for k, c in enumerate(C):
            rnd = c["rnd"]
            if lod > 0:                          # LOD1: only the bonnet lip and the bumper peak stay chamfered
                rnd = 1 if c["n"] in ("H1", "F1") else 0
            if k in (0, len(C) - 1) or rnd == 0:
                P.append(cp[k]); R.append(c["R"]); CR.append(c["CR"]); tag.append((k, 1))
                continue
            a, b = cp[k - 1] - cp[k], cp[k + 1] - cp[k]
            la, lb = np.linalg.norm(a), np.linalg.norm(b)
            soft = rnd == 2
            kl = min(0.30 * la, 0.30 * lb, 0.055) if soft else min(0.25 * la, 0.25 * lb, 0.11 if c["n"] == "G1" else 0.07)
            qa, qb = cp[k] + a / la * kl, cp[k] + b / lb * kl
            ts = ((0, 0.0), (3, 0.25), (1, 0.5), (4, 0.75), (2, 1.0)) if soft else ((0, 0.0), (1, 0.5), (2, 1.0))
            for part, t in ts:
                q = (1 - t) ** 2 * qa + 2 * t * (1 - t) * cp[k] + t * t * qb
                P.append(q); R.append(c["R"]); CR.append(c["CR"]); tag.append((k, part))
        self.C, self.P, self.R, self.CR, self.tag = C, np.array(P), np.array(R), np.array(CR), tag
        if lod > 0:
            self.CR = self.CR * 0.7             # LOD1 keeps most of the crown (mid point of the top, g = 0)
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
        names = [c["n"] for c in C]
        self.mid = {names[k]: i for i, (k, part) in enumerate(tag) if part == 1}
        self.first = {}
        for i, (k, part) in enumerate(tag):
            self.first.setdefault(names[k], i)
        self.seg = {}                                          # control name -> dense edge index of its straight part
        self.emat = []
        for i in range(n - 1):
            (ka, pa), (kb, pb) = tag[i], tag[i + 1]
            if ka != kb:
                self.seg[names[ka]] = i
                self.emat.append(C[ka]["mat"])
            else:
                m0, m1 = C[ka - 1]["mat"], C[ka]["mat"]
                self.emat.append(m0 if m0 == m1 else ("paint" if "glass" in (m0, m1) else m1 if m0 == "paint" else m0))
        self.hw = d["W"] / 2
        self.sill, self.belt = d["sill"], d["belt"]
        self.bl0, self.bl1 = S[self.mid["G0"]], S[self.mid["G4"]]
        self.zroof = float(S[:, 1].max())
        self.y0, self.y1 = -d["L"] / 2, d["L"] / 2
        self.pl = d.get("plan", (0.90, 0.30, 0.55, 0.13))
        self.r = d["r"]
        self.ra = d["r"] + 0.045
        self.yfa = d["L"] / 2 - d["foh"]
        self.yra = self.yfa - d["wb"]
        self.F = d.get("flare", 0.02)
        van = d.get("cargo", False)
        self.tuck, self.shd, self.shi = (0.035, 0.10, 0.016) if van else (0.050, 0.115, 0.042)
        i0, i1 = self.mid["G4"], self.first["H1"]             # bonnet edge line (cowl -> lip)
        self.hy, self.hz = S[i0:i1 + 1, 0].copy(), S[i0:i1 + 1, 1].copy()
        self.Sx = np.array([self.X(S[i, 0], S[i, 1]) for i in range(n)])

    def zbelt(self, y):
        (ya, za), (yb, zb) = self.bl0, self.bl1
        return za + (zb - za) * (y - ya) / (yb - ya)

    def ztop(self, y):
        """Upper edge of the body side: belt line beside the greenhouse, bonnet edge ahead of it, tail top behind."""
        if y < self.bl0[0]:
            return float(self.bl0[1])
        if y <= self.bl1[0]:
            return float(self.zbelt(y))
        return float(np.interp(y, self.hy, self.hz))

    def plan(self, y):
        w = self.hw
        Rf, tf, Rr, tr = self.pl
        p = 2.3
        u = min(1.0, max(0.0, (y - (self.y1 - Rf)) / Rf))
        w -= tf * (1 - (1 - u ** p) ** (1 / p))
        u = min(1.0, max(0.0, ((self.y0 + Rr) - y) / Rr))
        w -= tr * (1 - (1 - u ** p) ** (1 / p))
        return w

    def flare(self, y, z):
        f = 0.0
        for yc in (self.yra, self.yfa):
            dd = math.hypot(y - yc, z - self.r) - self.ra
            f = max(f, 1.0 if dd <= 0 else math.exp(-(dd / 0.10) ** 2))
        return self.F * f

    def X(self, y, z):
        """Half width of the body side at (y, z): plan taper, tuck below the widest line, vertical door skin, shoulder
        facet under the belt, tumblehome above it, wheel-arch flares."""
        w = self.plan(y)
        zt = self.ztop(y)
        zm = self.sill + 0.42 * (zt - self.sill)
        if z <= zm:
            x = w - self.tuck * min(1.25, (zm - z) / max(zm - self.sill, 1e-3)) ** 2
        else:
            zs = zt - self.shd
            if z <= zs:
                x = w
            elif z <= zt or not (self.bl0[0] <= y <= self.bl1[0]):
                x = w - self.shi * min(1.0, (z - zs) / self.shd)
            else:
                x = w - self.shi - self.d["tumble"] * (z - zt) / max(self.zroof - zt, 1e-3)
        return x + self.flare(y, z)

    def rows(self, y, zb, zm, nr):
        """Heights of the side rows at y between the lower edge zb and the upper edge zm, on the feature lines."""
        zt = self.ztop(y)
        zs = self.sill
        if nr >= 4:
            zz = [zb, zs + 0.17 * (zt - zs), zs + 0.42 * (zt - zs), zt - self.shd, zm]
        elif nr == 3:
            zz = [zb, zs + 0.42 * (zt - zs), zt - self.shd, zm]
        else:
            zz = [zb, zt - self.shd, zm]
        out = [zb]
        for z in zz[1:-1]:
            out.append(min(max(z, out[-1]), zm))
        return out + [zm]

    def pt(self, i, g):
        """Surface point and normal at dense profile index i, signed across coordinate g: |g| <= 1 crowned top
        (g = x / top half width), 1 < |g| <= 2 the shoulder arc down to the side line."""
        sx = 1.0 if g >= 0 else -1.0
        a = abs(g)
        Pi, Ni, Si = self.P[i], self.N[i], self.S[i]
        wS = self.Sx[i]
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
    """Revolved tyre + rim; x_out = x of the outer sidewall plane, the wheel extends inward (toward x = 0).
    r9: sidewall = 34-40 % of the radius with a bulge (the tyre reads as rubber with a profile, not a painted ring),
    rim barrel 70 mm deep with the spokes set inside the rim edge."""
    w = 0.205
    rr = (0.60 if steel else 0.66) * r
    cen = np.array([x_out, yc, r])

    def ring(rad, o, n=seg):
        return [np.array([x_out - sx * o, yc + rad * math.cos(t), r + rad * math.sin(t)])
                for t in np.linspace(0, 2 * math.pi, n + 1)[:-1]]

    def band(mat, A, B, radial=0.3, inward=False):
        n = len(A)
        for k in range(n):
            k2 = (k + 1) % n
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
        # r10: rounded shoulder between the sidewall and the tread, UVs for the tread / sidewall texture
        prof = [(rr, 0.016, 0.03), (0.84 * r, 0.0, 0.26), (0.972 * r, 0.012, 0.47), (r, 0.042, 0.52)]
        rings = [ring(*p[:2]) for p in prof]

        def tband(A, B, va, vb, radial):
            for k in range(seg):
                k2 = (k + 1) % seg
                want = (A[k] + A[k2] + B[k] + B[k2]) / 4 - cen
                want[0] = 0
                want = want / max(np.linalg.norm(want), 1e-6)
                ua, ub = TYRE_REP * k / seg, TYRE_REP * (k + 1) / seg
                _puv(m, tyre, [A[k], A[k2], B[k2], B[k]], [(ua, va), (ub, va), (ub, vb), (ua, vb)],
                     want * radial + np.array([sx * (1 - radial), 0, 0]))
        for (A, B), (pa_, pb_), rad_ in zip(zip(rings[:-1], rings[1:]), zip(prof[:-1], prof[1:]), (0.3, 0.3, 0.6)):
            tband(A, B, pa_[2], pb_[2], rad_)
        inner = ring(r, w)
        for k in range(seg):                                    # tread: not the top third (inside the arch)
            k2 = (k + 1) % seg
            if rings[-1][k][2] + rings[-1][k2][2] < 2 * r + 0.9 * r:
                want = (rings[-1][k] + rings[-1][k2]) / 2 - cen
                want[0] = 0
                ua, ub = TYRE_REP * k / seg, TYRE_REP * (k + 1) / seg
                _puv(m, tyre, [rings[-1][k], rings[-1][k2], inner[k2], inner[k]],
                     [(ua, 0.52), (ub, 0.52), (ub, 1.0), (ua, 1.0)], want)
        A_ = inner[::2]
        m.add(tyre, A_, [(0, i + 1, i) if sx > 0 else (0, i, i + 1) for i in range(1, len(A_) - 1)],
              [(0.0, 0.20)] * len(A_))                           # r8 N-13: inner sidewall (seen under the body)
        rim = "rim_steel" if steel else ("rim" if wst == 3 else rimm)
        deep = ring(rr - 0.03, 0.045 if steel else 0.085)
        band(rim if steel else "rim_dark", rings[0], deep, radial=0.7, inward=True)
        fan(rim if steel else "car_trim", deep[::2], X)
        if steel and wst % 2 == 1:
            # r10: plastic wheel cover clipped on the steel wheel (generic, no make's pattern): dished silver disc
            # with eight dark radial slots and a plain centre
            cov = "rim_dusty" if rimm == "rim_dusty" else "rim"
            ro, rc = ring(rr - 0.004, 0.006), ring(0.30 * r, 0.020)
            band(cov, rc, ro, radial=0.0)
            fan(cov, rc[::2], X)
            c0 = np.array([x_out - sx * 0.004, yc, r])
            for s in range(8):
                t = 2 * math.pi * (s + 0.5) / 8
                u = np.array([0, math.cos(t), math.sin(t)])
                v = np.array([0, -math.sin(t), math.cos(t)])
                _quad(m, "rim_dark", c0 + u * 0.56 * rr - v * 0.012 - X * 0.008, c0 + u * 0.90 * rr - v * 0.022,
                      c0 + u * 0.90 * rr + v * 0.022, c0 + u * 0.56 * rr + v * 0.012 - X * 0.008, X)
        elif steel:                                            # pressed-steel wheel: dished centre + plain hub cap
            fan("rim_steel", ring(0.42 * r, 0.024, 8), X)
            fan("rim_dark", ring(0.17 * r, 0.014, 6), X)
        else:
            # alloy styles (generic): 5 wide, 10 thin, 7 medium, 5 wide dark with a bright machined lip, 5 twin
            # r10: spokes have a ridge section (two faces: they shade as bars, not as a flat star)
            ns, wi, wo, face, twin = [(5, 0.052, 0.034, rimm, 0.0), (10, 0.024, 0.016, rimm, 0.0), (7, 0.038, 0.024, rimm, 0.0),
                                      (5, 0.064, 0.048, "rim_dark", 0.0), (5, 0.020, 0.015, rimm, 0.20)][wst % 5]
            for s in range(ns):
                for tw in ((-twin, twin) if twin else (0.0,)):
                    t = 2 * math.pi * s / ns + 0.3
                    t1 = t + tw                                   # twin spokes splay towards the rim
                    u = np.array([0, math.cos(t), math.sin(t)])
                    v = np.array([0, -math.sin(t), math.cos(t)])
                    u1 = np.array([0, math.cos(t1), math.sin(t1)])
                    v1 = np.array([0, -math.sin(t1), math.cos(t1)])
                    c0 = np.array([x_out - sx * 0.030, yc, r])
                    r1 = rr - 0.004
                    ia, ib_ = c0 + u * 0.05 - v * wi, c0 + u * 0.05 + v * wi
                    oa, ob = c0 + u1 * r1 - v1 * wo + X * 0.012, c0 + u1 * r1 + v1 * wo + X * 0.012
                    if ns * (2 if twin else 1) > 7:               # thin spokes: one face
                        _quad(m, face, ia, oa, ob, ib_, X)
                    else:
                        im, om = c0 + u * 0.05 + X * 0.012, c0 + u1 * r1 + X * 0.022
                        _quad(m, face, ia, oa, om, im, X - v * 0.6)
                        _quad(m, face, im, om, ob, ib_, X + v * 0.6)
            fan(face, ring(0.22 * r, 0.026 - 0.010, 8), X)
            fan("rim_dark", ring(0.085 * r, 0.012, 6), X)
    else:
        A, B = ring((0.62 if steel else 0.68) * r, 0.004), ring(r, 0.03)
        band(tyre, A, B)
        C2 = ring(r, w)                                  # tread: lower half only (the upper half is inside the arch)
        for k in range(seg):
            k2 = (k + 1) % seg
            if B[k][2] + B[k2][2] < 2 * r + 0.2 * r:
                want = (B[k] + B[k2]) / 2 - cen
                want[0] = 0
                _quad(m, tyre, B[k], B[k2], C2[k2], C2[k], want)
        fan(tyre, C2[::2], -X)                                  # r8 N-13: inner sidewall (seen under the body); r10: 5-gon
        cover = steel and wst % 2 == 1                          # r10: plastic wheel cover (silver disc)
        face = (rimm if cover else "rim_steel") if steel else ("rim_dark" if wst == 3 else rimm)
        fan(face, A, X)
        ra_ = (0.62 if steel else 0.68) * r
        c0 = np.array([x_out + sx * 0.002, yc, r])
        dark = "rim_dark" if not steel else "tyre"
        if steel:
            fan(dark, [c0 + np.array([0, 0.30 * r * math.cos(t), 0.30 * r * math.sin(t)])
                       for t in np.linspace(0, 2 * math.pi, 7)[:-1]], X)
        else:
            ns = (5, 5, 7, 5, 5)[wst % 5]
            wdark = "rim" if wst == 3 else dark                 # style 3: dark wheel, bright machined windows
            for s_ in range(ns):
                t0 = 2 * math.pi * (s_ + 0.24) / ns + 0.3
                t1 = 2 * math.pi * (s_ + 0.76) / ns + 0.3
                tm = (t0 + t1) / 2
                q = [c0 + np.array([0, rad * math.cos(t), rad * math.sin(t)])
                     for rad, t in ((0.30 * ra_, tm), (0.90 * ra_, t0), (0.90 * ra_, t1))]
                fan(wdark if wst == 3 else dark, q, X)


def _vehicle2(d, paint, lod, steel=False, style=None):
    from shapely.geometry import Polygon, box
    from shapely.ops import unary_union
    m = Mesh()
    sh = _Shell(d, lod)
    L, hw, H = d["L"], d["W"] / 2, d["H"]
    sill, belt, r = d["sill"], d["belt"], d["r"]
    cargo = d.get("cargo", False)
    clad = d.get("clad", False)
    n = len(sh.P)
    gmat = "car_glass_tint" if lod == 0 else "car_glass"
    bmat = "car_sill" if d.get("blackbump") else paint          # bumper skins (unpainted plastic on the van)
    matname = {"paint": paint, "glass": gmat, "trim": "car_trim", "bump": bmat}
    style = style or dict(dirt=0.5, wheel=0, uoff=0.0)
    dl = float(style["dirt"])                       # 0 fresh from the car wash .. 1 a month of winter streets
    dmat = f"car_dirt_{1 + min(2, int(dl * 3))}"
    uo = float(style["uoff"])
    ds = 0.70 + 0.30 * dl                           # glass dust reach (UV0 of car_glass_tint, see materials.py)
    # factory privacy glass behind the B pillar (v4, WORKING_VALUE fleet look: SUVs / estates, half the hatches):
    # UV0 u of those panes is offset by PRIVACY_U, WorldCarGlass.shader decodes it (no extra material / draw)
    priv = not cargo and bool(style.get("privacy", False))

    # ---- front / rear face layout (needed before the shell: r10 cuts the lamp, grille and intake openings into it)
    f = FACES[d.get("face", "swept")]
    ti0, ti1, to0, to1 = f["lamp"]
    lg0, lg1 = f["lg"]
    lgs = [g for g in ([lg0, 1.0, 1 + 1 / 3, 1 + 2 / 3, lg1] if lod == 0 else [lg0, 1.0, lg1]) if lg0 - 1e-9 <= g <= lg1 + 1e-9]

    def lamp_cols(sx, a, b, gi=0.0, go=0.0):         # a, b = fractions of the lamp height (0 top .. 1 bottom)
        out = []
        for g in lgs:
            g = min(max(g, lg0 + gi), lg1 - go)
            if out and abs(out[-1][0]) >= g - 1e-9:
                continue
            k = (g - lg0) / (lg1 - lg0)
            top, bot = ti0 + (to0 - ti0) * k, ti1 + (to1 - ti1) * k
            out.append((sx * g, top + (bot - top) * a, top + (bot - top) * b))
        return out
    gw, gt = f["gw"], f["gt"]
    gi_ = min(0.5, 0.86 * gw)                        # inner columns on the shell's own columns (g = +-0.5)
    grille_cols = [(-gw, gt + 0.10, 0.84), (-gi_, gt, 0.95), (0.0, gt, 0.95), (gi_, gt, 0.95), (gw, gt + 0.10, 0.84)]
    intake_cols = [(-0.78, 0.60, 0.86), (-0.5, 0.52, 0.95), (0.0, 0.52, 0.95), (0.5, 0.52, 0.95), (0.78, 0.60, 0.86)]
    tg = [0.5, 1.0, 1 + 2 / 3, 2.0] if lod == 0 else [0.55, 1.0, 2.0]
    if cargo:
        tail_cols = {sx: sorted((sx * g, 0.26, 0.86) for g in (1.25, 1 + 2 / 3, 2.0)) for sx in (-1, 1)}
    else:
        tail_cols = {sx: sorted((sx * g, 0.60 - 0.18 * (g - tg[0]) / (tg[-1] - tg[0]), 0.985) for g in tg) for sx in (-1, 1)}
    head_cols = {sx: sorted(lamp_cols(sx, 0.0, 1.0)) for sx in (-1, 1)}
    holes = {}
    if lod == 0:
        holes[sh.seg["H1"]] = [head_cols[-1], grille_cols, head_cols[1]]
        holes[sh.seg["F1"]] = [intake_cols]
        holes[sh.seg["R2"]] = [tail_cols[-1], tail_cols[1]]

    # ---- top shell: crowned centre + shoulder arcs
    NT, NS = (2, 3) if lod == 0 else (1, 2)
    gs = ([-2 + k / NS for k in range(NS)] + [-1 + k / NT for k in range(2 * NT + 1)] + [1 + (k + 1) / NS for k in range(NS)])

    def bp(i, g):
        """Shell point / unit normal at dense index i. Across coordinates that are not shell columns lie on the chord
        between the two neighbouring columns, so the cut faces below share their edges with the uncut neighbours."""
        k = min(max(int(np.searchsorted(gs, g - 1e-9)), 1), len(gs) - 1)
        ga, gb = gs[k - 1], gs[k]
        (pa, na), (pb, nb) = sh.pt(i, ga), sh.pt(i, gb)
        w = min(1.0, max(0.0, (g - ga) / (gb - ga)))
        nn = na / np.linalg.norm(na) * (1 - w) + nb / np.linalg.norm(nb) * w
        return pa + (pb - pa) * w, nn / np.linalg.norm(nn)

    def hp(i, t, g):
        (a, na), (b, nb) = bp(i, g), bp(i + 1, g)
        nn = na + (nb - na) * t
        return a + (b - a) * t, nn / np.linalg.norm(nn)

    def hcol(h, g):
        gg = [c[0] for c in h]
        return float(np.interp(g, gg, [c[1] for c in h])), float(np.interp(g, gg, [c[2] for c in h]))

    for i in range(n - 1):
        mat = matname[sh.emat[i]]
        if i in holes:                              # r10: face with openings (lamp buckets, grille, intake)
            HL = holes[i]
            G = sorted({round(g, 6) for g in gs} | {round(c[0], 6) for h in HL for c in h})
            for ga, gb in zip(G[:-1], G[1:]):
                gm_ = (ga + gb) / 2
                h = next((h for h in HL if h[0][0] - 1e-9 <= gm_ <= h[-1][0] + 1e-9), None)
                spans = [(0.0, 1.0, 0.0, 1.0)]
                if h is not None:
                    (a0, a1), (b0, b1) = hcol(h, ga), hcol(h, gb)
                    spans = [(0.0, a0, 0.0, b0), (a1, 1.0, b1, 1.0)]
                for ta0, ta1, tb0, tb1 in spans:
                    q = [hp(i, ta0, ga), hp(i, tb0, gb), hp(i, tb1, gb), hp(i, ta1, ga)]
                    _quad(m, mat, *[x[0] for x in q], sum(x[1] for x in q))
            continue
        A = [sh.pt(i, g) for g in gs]
        B = [sh.pt(i + 1, g) for g in gs]
        for j in range(len(gs) - 1):
            top = abs(gs[j]) <= 1 + 1e-9 and abs(gs[j + 1]) <= 1 + 1e-9
            mm = mat if (top or mat != gmat) else paint
            nn = A[j][1] + A[j + 1][1] + B[j][1] + B[j + 1][1]
            if mm == gmat and lod == 0:             # dust mask: 1 at the lower edge and the sides, 0.75 at the top
                va, vb = (-1.0, 0.75) if sh.P[i][1] < sh.P[i + 1][1] else (0.75, -1.0)
                po = PRIVACY_U if (priv and sh.P[i][0] < 0) else 0.0          # rear screen
                _puv(m, mm, [A[j][0], A[j + 1][0], B[j + 1][0], B[j][0]],
                     [(gs[j] * ds + po, va * ds), (gs[j + 1] * ds + po, va * ds), (gs[j + 1] * ds + po, vb * ds),
                      (gs[j] * ds + po, vb * ds)], nn)
            else:
                _quad(m, mm, A[j][0], A[j + 1][0], B[j + 1][0], B[j][0], nn)

    # ---- r8 (REVIEW r7 N-13): inner skin of the greenhouse (the shell is single-sided)
    if lod == 0:
        for i in range(sh.mid["G0"], sh.mid["G4"]):
            if matname[sh.emat[i]] == gmat:
                strips = ([-2.0, -1.5, -0.85], [0.85, 1.5, 2.0])
            else:
                strips = ([-2.0, -1.0, 0.0, 1.0, 2.0],)
            for gk in strips:
                A = [sh.pt(i, g) for g in gk]
                B = [sh.pt(i + 1, g) for g in gk]
                for j in range(len(gk) - 1):
                    q = [A[j], A[j + 1], B[j + 1], B[j]]
                    _quad(m, "car_interior", *[pp - nn / np.linalg.norm(nn) * 0.005 for pp, nn in q],
                          -sum(nn / np.linalg.norm(nn) for _, nn in q))

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

    def elen(name):
        i = sh.seg[name]
        return float(np.linalg.norm(sh.P[i + 1] - sh.P[i]))

    def t_at_z(name, z):
        i = sh.seg[name]
        za, zb = sh.P[i][1], sh.P[i + 1][1]
        return min(0.95, max(0.05, (z - za) / (zb - za))) if abs(zb - za) > 1e-6 else 0.5

    def side_tris(mat, tris, lift=0.0):
        for t in tris:
            for sx in (1, -1):
                q = [np.array([sx * (sh.X(y, z) + lift), y, z]) for y, z in t]
                _oq(m, mat, q, [sx, 0, 0])

    # ---- side: columns between the profile's side line and the sill / wheel-arch line, rows on the feature lines
    yfa, yra, ra = sh.yfa, sh.yra, sh.ra
    aseg = 10 if lod == 0 else 6

    def arch(yc):
        return [(yc - ra - 0.03, sill)] + [(yc - ra * math.cos(t), r + ra * math.sin(t))
                                           for t in np.linspace(0, math.pi, aseg + 1)] + [(yc + ra + 0.03, sill)]
    B = [tuple(sh.S[0])] + arch(yra) + arch(yfa) + [tuple(sh.S[-1])]
    By, Bz = np.array([b[0] for b in B]), np.array([b[1] for b in B])
    Sy, Sz = sh.S[:, 0], sh.S[:, 1]
    Rf, _, Rr, _ = sh.pl
    extra = [sh.y1 - Rf * (1 - u) for u in ((0.40, 0.58, 0.72) if lod == 0 else ())]
    extra += [sh.y0 + Rr * (1 - u) for u in ((0.45, 0.70) if lod == 0 else ())]
    ys = sorted(set(np.round(np.concatenate([Sy, By, extra]), 4)))
    ys = [float(y) for y in ys if Sy[0] - 1e-6 <= y <= Sy[-1] + 1e-6]
    ga0, ga1 = float(sh.bl0[0]), float(sh.bl1[0])
    NR = 4 if lod == 0 else 2

    def column(y):
        zt = float(np.interp(y, Sy, Sz))
        zb = float(np.interp(y, By, Bz))
        green = ga0 - 1e-6 <= y <= ga1 + 1e-6
        zm = max(min(zt, sh.zbelt(y)) if green else zt, zb)
        zz = sh.rows(y, zb, zm, NR)
        col = [np.array([sh.X(y, z), y, z]) for z in zz[:-1]]
        xt = sh.X(y, zm) if green else float(np.interp(y, Sy, sh.Sx))      # the top edge is shared with the shell
        return col + [np.array([xt, y, zm])]
    cols = [column(y) for y in ys]
    for ca, cb in zip(cols[:-1], cols[1:]):
        for k in range(NR):
            for sx in (1, -1):
                f = np.array([sx, 1, 1])
                _quad(m, paint, ca[k] * f, cb[k] * f, cb[k + 1] * f, ca[k + 1] * f, [sx, 0, 0])
    if d.get("blackbump"):                          # unpainted bumper corners on the side (in front of / behind the arches)
        zbf = float(sh.S[sh.mid["F1"]][1]) + 0.05
        zbr = float(sh.S[sh.mid["RB" if "RB" in sh.mid else "R2"]][1])
        for ya, yb, zt_ in ((yfa + ra + 0.03, float(Sy[-1]), zbf), (float(Sy[0]), yra - ra - 0.03, zbr)):
            yy = [ya + (yb - ya) * k / 3 for k in range(4)]
            for y_a, y_b in zip(yy[:-1], yy[1:]):
                za, zb_ = float(np.interp(y_a, By, Bz)), float(np.interp(y_b, By, Bz))
                side_tris("car_sill", [[(y_a, za), (y_b, zb_), (y_b, max(zt_, zb_))],
                                       [(y_a, za), (y_b, max(zt_, zb_)), (y_a, max(zt_, za))]], lift=0.004)

    # ---- road film (alpha overlay): sills, lower doors, spray fans behind the wheels, arch lips
    ya_, yb_ = sh.y0 + 0.40, sh.y1 - 0.55                       # the straight part of the plan
    arch_top = r + ra

    def ztop(y):
        z = sill + 0.12 + 0.14 * dl
        for yc in (yra, yfa):
            z += (0.12 + 0.18 * dl) * math.exp(-((y - (yc - ra - 0.24)) / 0.28) ** 2)
        return z
    kd = 8 if lod == 0 else 3
    if lod == 0:
        # r9: the film uses the body's own columns (with the arch flares a coarser overlay cut through the skin
        # and showed as hard-edged polygons of clean paint)
        runs = [sorted({round(float(y), 4) for y in ys if ya_ < y < yb_} | {round(ya_, 4), round(yb_, 4)})]
    else:                                    # LOD1: three plain runs between / beside the arches, no arch lips
        e = ra + 0.03
        runs = [[ya_, yra - e], [yra + e, yra + e + 0.45, (yra + yfa) / 2, yfa - e], [yfa + e, yb_]]
    rows = 2 if lod == 0 else 1

    def dcol(y):
        zb = float(np.interp(y, By, Bz))
        zt = min(max(ztop(y), zb + 0.11), arch_top + 0.16)
        return [(np.array([sh.X(y, zb + (zt - zb) * k / rows) + 0.018, y, zb + (zt - zb) * k / rows]), (y / 1.7 + uo, k / rows))
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
    below = Polygon([(ga0 - 1, sh.zbelt(ga0 - 1) + 0.03), (ga1 + 1, sh.zbelt(ga1 + 1) + 0.03), (ga1 + 1, -1), (ga0 - 1, -1)])
    inner = outer.buffer(-0.045, join_style=2).difference(below)
    yB = ga1 - d["bp"]
    bands = [(yB + 0.04, ga1 - d["ap"] * 0.3)]
    if not cargo:
        if d["qp"]:
            bands += [(yB - d["qp"] + 0.035, yB - 0.04), (ga0 + d["cp"], yB - d["qp"] - 0.035)]
        else:
            bands += [(ga0 + d["cp"], yB - 0.04)]
    wins, wrear = [], []
    for kb, (ya, yb) in enumerate(bands):
        g = inner.intersection(box(ya, 0, yb, 3)).simplify(0.004)
        got = [p for p in getattr(g, "geoms", [g]) if p.geom_type == "Polygon" and p.area > 0.01]
        wins += got
        wrear += [kb > 0] * len(got)
    if lod == 0:
        frame = outer.difference(unary_union(wins))
        side_tris(paint, _tri2d(frame))
        for t in _tri2d(frame.simplify(0.01)):      # r8 N-13: inner face of the pillars / window frames
            for sx in (1, -1):
                _oq(m, "car_interior", [np.array([sx * (sh.X(y, z) - 0.005), y, z]) for y, z in t], [-sx, 0, 0])
        for wn, rear in zip(wins, wrear):           # dust mask rises from the lower window edge
            po = PRIVACY_U if (priv and rear) else 0.0
            for t in _tri2d(wn):
                for sx in (1, -1):
                    _puv(m, gmat, [np.array([sx * sh.X(y, z), y, z]) for y, z in t],
                         [(po, ds * (1.0 - 0.8 * min(1.0, max(0.0, (z - sh.zbelt(y)) / 0.42)))) for y, z in t], [sx, 0, 0])
    else:
        side_tris(paint, _tri2d(outer.simplify(0.003)))
        for wn in wins:
            side_tris(gmat, _tri2d(wn.simplify(0.02)), lift=0.008)
    if lod == 0:                                    # weatherstrip along the belt under the side glass
        wy = [ga0 + (d["cp"] if not cargo else (yB - ga0)) + 0.0, yB, ga1 - d["ap"] * 0.3] if not cargo else [yB + 0.04, ga1 - d["ap"] * 0.3]
        wy = [wy[0]] + [wy[0] + (wy[-1] - wy[0]) * k / 4 for k in (1, 2, 3)] + [wy[-1]]
        for ya, yb in zip(wy[:-1], wy[1:]):
            za, zb_ = sh.zbelt(ya) + 0.012, sh.zbelt(yb) + 0.012
            side_tris("car_trim", [[(ya, za), (yb, zb_), (yb, zb_ + 0.026)], [(ya, za), (yb, zb_ + 0.026), (ya, za + 0.026)]], lift=0.004)
    # black B pillar (and the divider of the third side window): the side glazing reads as one dark graphic
    if not cargo:
        for yp in [yB] + ([yB - d["qp"]] if d["qp"] else []):
            pil = inner.intersection(box(yp - 0.042, 0, yp + 0.042, 3))
            if not pil.is_empty:
                side_tris("car_trim", _tri2d(pil.simplify(0.01)), lift=0.005)

    # ---- wheels in the arches, liners, arch lips
    lipo = 0.010 if lod == 0 else 0.0
    for yc in (yra, yfa):
        A = arch(yc)
        xo = sh.X(yc, r) - 0.030
        for sx in (-1, 1):
            _wheel2(m, sx * xo, yc, r, sx, 14 if lod == 0 else 10, steel, lod, style["wheel"],
                    "rim_dusty" if dl > 0.45 else "rim",
                    ("car_" if lod == 0 else "") + ("tyre_dusty" if dl > 0.3 else "tyre"))
            dep = 0.28 if lod == 0 else 0.26
            # r8 N-13: back plate of the wheel housing (the gap above the tyre showed the cabin / the far side)
            xp = sh.X(yc, r) - dep
            _quad(m, "car_trim", [sx * xp, yc - ra - 0.03, sill], [sx * xp, yc + ra + 0.03, sill],
                  [sx * xp, yc + ra + 0.03, r + ra], [sx * xp, yc - ra - 0.03, r + ra], [sx, 0, 0])
            AL = A if lod == 0 else A[::2]            # r10: LOD1 liner on every other arch point (frame budget)
            for k, ((ya, za), (yb, zb_)) in enumerate(zip(AL[:-1], AL[1:])):
                mid = np.array([0, yc - (ya + yb) / 2, r - (za + zb_) / 2])
                xa, xb = sh.X(ya, za) + lipo, sh.X(yb, zb_) + lipo
                _quad(m, "car_trim", [sx * xa, ya, za], [sx * xb, yb, zb_], [sx * (xb - dep), yb, zb_],
                      [sx * (xa - dep), ya, za], mid)
                if lod == 0 and dl > 0.33 and 0 < k < len(A) - 2 and (ya + yb) / 2 < yc + 0.05:
                    # r10: spray settles on the lip behind the wheel (v = 0 dense film at the arch edge)
                    kk = (ra + (0.085 if clad else 0.06)) / ra
                    y2a, z2a = yc + (ya - yc) * kk, max(sill, r + (za - r) * kk)
                    y2b, z2b = yc + (yb - yc) * kk, max(sill, r + (zb_ - r) * kk)
                    _puv(m, dmat, [[sx * (xa + 0.007), ya, za], [sx * (xb + 0.007), yb, zb_],
                                   [sx * (sh.X(y2b, z2b) + 0.011), y2b, z2b], [sx * (sh.X(y2a, z2a) + 0.011), y2a, z2a]],
                         [(ya / 1.7 + uo, 0.25), (yb / 1.7 + uo, 0.25), (yb / 1.7 + uo, 0.95), (ya / 1.7 + uo, 0.95)], [sx, 0, 0])
                if lod == 0 and 0 < k < len(A) - 2:
                    # lip ring: 10 mm proud at the arch edge, flush 45 mm (cladding: 70 mm) outside it
                    kk = (ra + (0.07 if clad else 0.045)) / ra
                    y2a, z2a = yc + (ya - yc) * kk, max(sill, r + (za - r) * kk)
                    y2b, z2b = yc + (yb - yc) * kk, max(sill, r + (zb_ - r) * kk)
                    _quad(m, "car_sill" if clad else paint, [sx * xa, ya, za], [sx * xb, yb, zb_],
                          [sx * (sh.X(y2b, z2b) + 0.003), y2b, z2b], [sx * (sh.X(y2a, z2a) + 0.003), y2a, z2a], [sx, 0, 0])
    zfl = sill + 0.06
    _quad(m, "car_trim", [hw - 0.16, -L / 2 + 0.4, zfl], [-hw + 0.16, -L / 2 + 0.4, zfl], [-hw + 0.16, L / 2 - 0.5, zfl],
          [hw - 0.16, L / 2 - 0.5, zfl], [0, 0, -1])

    # ---- front: lamp units, grille, intakes, plate
    f = FACES[d.get("face", "swept")]
    iH = sh.seg["H1"]
    lnH = elen("H1")
    iR = sh.seg["R2"]

    def recess(i, cols, depth, wall, back, taper=0.12):
        """r10: bucket behind an opening cut into shell edge i. cols = [(g, t0, t1)] ascending in g. Walls face the
        opening's axis, the back faces out. Returns (inner top points, inner bottom points, axis)."""
        top = [hp(i, c[1], c[0]) for c in cols]
        bot = [hp(i, c[2], c[0]) for c in cols]
        cen = np.mean([x[0] for x in top + bot], axis=0)
        nav = np.sum([x[1] for x in top + bot], axis=0)
        nav /= np.linalg.norm(nav)
        ci = cen - nav * depth

        def inn(x):
            q = x[0] - x[1] * depth
            return q + (ci - q) * taper
        it, ib = [inn(x) for x in top], [inn(x) for x in bot]
        cm = cen - nav * depth / 2
        for k in range(len(cols) - 1):
            for o, e in ((top, it), (bot, ib)):
                mid = (o[k][0] + o[k + 1][0] + e[k] + e[k + 1]) / 4
                _quad(m, wall, o[k][0], o[k + 1][0], e[k + 1], e[k], cm - mid)
            _quad(m, back, it[k], it[k + 1], ib[k + 1], ib[k], nav)
        for k in (0, len(cols) - 1):
            mid = (top[k][0] + bot[k][0] + it[k] + ib[k]) / 4
            _quad(m, wall, top[k][0], bot[k][0], ib[k], it[k], cm - mid)
        return it, ib, nav

    def lens(i, cols, v_top=0.55):
        """Clear cover over an opening: the glazing material with the LENS_U code in UV0 (WorldCarGlass.shader); the dust
        mask v reaches 1 at the lower edge of dirty cars."""
        for ca, cb in zip(cols[:-1], cols[1:]):
            q = [hp(i, ca[1], ca[0]), hp(i, cb[1], cb[0]), hp(i, cb[2], cb[0]), hp(i, ca[2], ca[0])]
            _puv(m, gmat, [x[0] + x[1] * 0.0015 for x in q],
                 [(LENS_U, v_top * ds), (LENS_U, v_top * ds), (LENS_U, ds), (LENS_U, ds)], sum(x[1] for x in q))

    def along(A, u):
        """Point at fraction u along a polyline of points."""
        x = min(max(u, 0.0), 1.0) * (len(A) - 1)
        k = min(int(x), len(A) - 2)
        return A[k] + (A[k + 1] - A[k]) * (x - k)

    if lod == 0:
        for sx in (-1, 1):
            cols = head_cols[sx]
            it, ib, nav = recess(iH, cols, 0.045, "car_lamp", "car_light_head")
            # projector: dark bezel tube standing off the reflector, bright convex lens (inner third of the unit)
            u_ = 0.30 if sx > 0 else 0.70
            ct, cb_ = along(it, u_), along(ib, u_)
            c0 = (ct + cb_) / 2
            rad = min(0.042, 0.40 * float(np.linalg.norm(ct - cb_)))
            e1 = np.cross(nav, [0.0, 0.0, 1.0])
            e1 /= np.linalg.norm(e1)
            e2 = np.cross(nav, e1)
            ring0 = [c0 + (e1 * math.cos(a_) + e2 * math.sin(a_)) * rad for a_ in np.linspace(0, 2 * math.pi, 7)[:-1]]
            ring1 = [q + nav * 0.026 - (q - c0) * 0.10 for q in ring0]
            for k in range(6):
                k2 = (k + 1) % 6
                _quad(m, "car_lamp", ring0[k], ring0[k2], ring1[k2], ring1[k], (ring0[k] + ring0[k2]) / 2 - c0)
            tip = c0 + nav * 0.034
            for k in range(6):
                _puv(m, "car_light_head", [tip, ring1[k], ring1[(k + 1) % 6]], [(0, 0)] * 3, nav)
            # divider fin between the dipped-beam and the outer (indicator / main-beam) chamber
            u_ = 0.58 if sx > 0 else 0.42
            ft, fb = along(it, u_), along(ib, u_)
            fo = nav * 0.030
            for s_ in (-1.0, 1.0):
                _quad(m, "car_lamp", ft, fb, fb + fo, ft + fo, np.array([s_, 0.0, 0.0]))
            lens(iH, cols)
    else:
        for sx in (-1, 1):
            spatch("H1", lamp_cols(sx, 0.0, 1.0), "car_lamp")
            spatch("H1", lamp_cols(sx, 0.10, 0.90, 0.045, 0.07), "car_light_head", lift=0.010)
    if lg1 >= 1.85:                                  # the unit wraps into the wing (side surface)
        pa, pb = sh.ptf(iH, to0, 2.0)[0], sh.ptf(iH, to1, 2.0)[0]
        wrap = 0.20 if lod == 0 else 0.16
        yc_ = pa[1] - wrap
        zc_ = float(np.interp(yc_, sh.hy, sh.hz)) - 0.035
        A_, B_, C_ = (pa[1], pa[2]), (pb[1], pb[2]), (yc_, zc_)
        side_tris("car_lamp", [[A_, B_, C_]], lift=0.010)
        if lod == 0:
            la = lambda p, q, t: (p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t)      # noqa: E731
            side_tris("car_light_head", [[la(A_, B_, 0.16), la(A_, B_, 0.84), la(la(A_, B_, 0.4), C_, 0.62)]], lift=0.014)

    def slats(i, cols, fr, depth, hh, mat="rim_dark"):
        """Horizontal bars inside an opening: front face + top face (the top catches the sky). fr = fractions of the
        opening height; the bars sit `depth` behind the skin and run back to 2.4 x depth."""
        ln = float(np.linalg.norm(sh.P[i + 1] - sh.P[i]))
        for f_ in fr:
            row = []
            for g, t0, t1 in cols:
                tc = t0 + (t1 - t0) * f_
                (pa, na), (pb, nb) = hp(i, tc - hh / ln, g), hp(i, tc + hh / ln, g)
                row.append((pa - na * depth, pb - nb * depth, pa - na * depth * 2.4, na))
            for a_, b_ in zip(row[:-1], row[1:]):
                _quad(m, mat, a_[0], b_[0], b_[1], a_[1], a_[3] + b_[3])
                _quad(m, mat, a_[2], b_[2], b_[0], a_[0], [0, 0, 1])

    if lod == 0:
        # grille and lower intake: real openings 35-38 mm deep, dark plane behind bars (no badge, no make's shape)
        recess(iH, grille_cols, 0.038, "car_trim", "car_interior", taper=0.06)
        slats(iH, grille_cols[1:-1], (0.22, 0.50, 0.78), 0.010, 0.016)
        recess(sh.seg["F1"], intake_cols, 0.035, "car_trim", "car_interior", taper=0.06)
        slats(sh.seg["F1"], intake_cols[1:-1], (0.5,), 0.010, 0.012)
        for sx in (-1, 1):                                                                 # corner intakes / fog recesses
            spatch("F1", [(sx * 1.05, 0.40, 0.80), (sx * 1.38, 0.34, 0.86), (sx * 1.72, 0.42, 0.74)], "car_trim")
    else:
        patch("H1", gt + 0.03, 0.93, [-0.9 * gw, 0.0, 0.9 * gw], "car_trim")
        patch("F1", 0.52, 0.93, [-0.70, 0.0, 0.70], "car_trim")

    # ---- rear: lamp clusters, plate recess, bumper reflectors and valance
    for sx in (-1, 1):
        cols = tail_cols[sx]
        if lod == 0:
            # r10: red reflector tray 22 mm behind a clear cover, light-guide bar standing off it, reversing lamp
            it, ib, nav = recess(iR, cols, 0.022, "car_lamp", "car_light_tail", taper=0.10)
            o = nav * 0.004
            if cargo:
                a_, b_ = along(it, 0.5), along(ib, 0.5)
                a2, b2 = along(it, 0.5 - sx * 0.35), along(ib, 0.5 - sx * 0.35)
                _quad(m, "car_light_head", a_ + (b_ - a_) * 0.08 + o, a2 + (b2 - a2) * 0.08 + o,
                      a2 + (b2 - a2) * 0.26 + o, a_ + (b_ - a_) * 0.26 + o, nav)               # reversing lamp
            else:
                row = []
                for u_ in (0.06, 0.5, 0.94):
                    a_, b_ = along(it, u_), along(ib, u_)
                    row.append((a_ + (b_ - a_) * 0.28, a_ + (b_ - a_) * 0.52))
                for (a0, a1), (b0, b1) in zip(row[:-1], row[1:]):
                    ob = nav * 0.012
                    _quad(m, "car_light_tail", a0 + ob, b0 + ob, b1 + ob, a1 + ob, nav)
                    _quad(m, "car_light_tail", a0, b0, b0 + ob, a0 + ob, [0, 0, 1])
                ui = 0.10 if sx > 0 else 0.90                                              # reversing lamp, inner end
                a_, b_ = along(it, ui), along(ib, ui)
                a2, b2 = along(it, ui + sx * 0.16), along(ib, ui + sx * 0.16)
                _quad(m, "car_light_head", a_ + (b_ - a_) * 0.66 + o, a2 + (b2 - a2) * 0.66 + o,
                      a2 + (b2 - a2) * 0.90 + o, a_ + (b_ - a_) * 0.90 + o, nav)
                patch("R1", 0.50, 0.62, [sx * 1.10, sx * 1.60], "car_light_tail")              # bumper reflector
            lens(iR, cols, v_top=0.40)
        elif cargo:
            patch("R2", 0.26, 0.86, [sx * 1.25, sx * 2.0], "car_light_tail")
        else:
            spatch("R2", [(sx * g, 0.60 - 0.18 * (g - tg[0]) / (tg[-1] - tg[0]), 0.985) for g in tg], "car_light_tail")
        # the cluster wraps into the rear wing
        t1_, t0_ = (0.985, 0.42) if not cargo else (0.86, 0.26)
        pa, pb = sh.ptf(iR, t1_, 2.0)[0], sh.ptf(iR, t0_, 2.0)[0]
        if sx == 1:
            wa, wb_ = (0.17, 0.09) if not cargo else (0.05, 0.05)
            side_tris("car_light_tail", [[(pa[1], pa[2]), (pb[1], pb[2]), (pb[1] + wb_, pb[2] + 0.03)],
                                         [(pa[1], pa[2]), (pb[1] + wb_, pb[2] + 0.03), (pa[1] + wa, pa[2] - 0.012)]], lift=0.012)
    if f["bar"] and not cargo and lod == 0:
        patch("R2", 0.80, 0.86, [-0.52, 0.0, 0.52], "car_light_tail")                      # light bar across the boot
    if lod == 0:
        patch("R1", 0.0, 0.34, [-0.80, 0.0, 0.80], "car_trim")                             # rear valance insert
        zpl = float(sh.P[iR][1]) + 0.215
        tpl = t_at_z("R2", zpl)
        patch("R2", tpl, tpl + 0.045 / elen("R2"), [-0.40, 0.0, 0.40], "car_trim", lift=0.008)   # plate lamp / handle bar
        if not cargo:                                                                      # roof aerial fin
            pr = sh.pt(sh.mid["G1"], 0.0)[0]
            _box5(m, "car_trim", [0, pr[1] + 0.16, pr[2] + 0.025], 0.02, 0.075, 0.03, (0, 0, -1))
        else:                                                                              # barn-door split
            patch("R2", 0.02, 0.98, [-0.012, 0.012], "car_trim", lift=0.004)
            patch("G0", 0.0, 1.0, [-0.012, 0.012], "car_trim", lift=0.004)
    else:
        patch("R1", 0.0, 0.34, [-0.80, 0.80], "car_trim")
    # plates: the prototype's own cell on LOD0 and LOD1 (r8 N-14)
    pk = int(style.get("plate", 0))
    u0, v0, u1, v1 = plate_uv(pk)
    zpf = float(sh.P[sh.seg["F1"]][1]) - 0.085
    zpr = float(sh.P[iR][1]) + 0.135
    for name, tc in (("F1", t_at_z("F1", zpf)), ("R2", t_at_z("R2", zpr))):
        i = sh.seg[name]
        ln = float(np.linalg.norm(sh.P[i + 1] - sh.P[i]))
        xt = sh.pt(i, 1.0)[0][0]
        q, nn = [], np.zeros(3)
        hold = []
        for t, g in ((tc - 0.056 / ln, -0.26 / xt), (tc - 0.056 / ln, 0.26 / xt), (tc + 0.056 / ln, 0.26 / xt),
                     (tc + 0.056 / ln, -0.26 / xt)):
            pp, nrm = sh.ptf(i, t, g)
            q.append(pp + nrm * (0.014 if lod else 0.024))
            nn += nrm
            pc, _ = sh.ptf(i, tc + (t - tc) * 1.12, g * 1.03)
            hold.append((pc + nrm * 0.021, pc + nrm * 0.002))
        if lod == 0:                                 # holder frame + its edge down to the bumper skin
            cq = np.mean([h_[0] for h_ in hold], axis=0)
            _quad(m, "car_trim", *[h_[0] for h_ in hold], nn)
            for k in range(4):
                k2 = (k + 1) % 4
                _quad(m, "car_trim", hold[k][0], hold[k2][0], hold[k2][1], hold[k][1], (hold[k][0] + hold[k2][0]) / 2 - cq)
        zlo = min(pp[2] for pp in q)
        zhi = max(pp[2] for pp in q)
        front = name == "F1"                 # front plate seen from +y: its left (EU band) is +x; rear: -x
        uv = [((u0 if (pp[0] > 0) == front else u1), (v0 if pp[2] < (zlo + zhi) / 2 else v1)) for pp in q]
        _puv(m, "car_plate", q, uv, nn)
    # road film on the tail (dirtiest face of a car) and the lower front bumper
    dg = [-2.0, -0.7, 0.7, 2.0] if lod == 0 else [-1.9, 0.0, 1.9]
    spatch("R1", [(g, 0.0, 1.0) for g in dg], dmat, lift=0.016, uv=(uo, 0.45), v0=0.0)
    spatch("R2", [(g, 0.0, 0.25 + 0.45 * dl) for g in dg], dmat, lift=0.016, uv=(uo + 0.21, 0.45), v0=0.35)
    if lod == 0:
        spatch("F1", [(g, 1.0, 0.0) for g in dg], dmat, lift=0.016, uv=(uo + 0.37, 0.45), v0=0.62 - 0.30 * dl)   # thin: splatter

    # ---- sills, seams, handles, mirrors, rails, wipers
    def strip(mat, pts, wy, lift=0.004):            # seam along (y, z) points, 2 * wy wide
        for (ya, za), (yb, zb_) in zip(pts[:-1], pts[1:]):
            dy, dz = yb - ya, zb_ - za
            ln = math.hypot(dy, dz) or 1.0
            oy, oz = dz / ln * wy, -dy / ln * wy
            for sx in (-1, 1):
                _quad(m, mat, [sx * (sh.X(ya, za) + lift), ya - oy, za - oz], [sx * (sh.X(ya, za) + lift), ya + oy, za + oz],
                      [sx * (sh.X(yb, zb_) + lift), yb + oy, zb_ + oz], [sx * (sh.X(yb, zb_) + lift), yb - oy, zb_ - oz], [sx, 0, 0])
    ys0, ys1 = yra + ra + 0.04, yfa - ra - 0.04
    zs = sill + (0.15 if clad else 0.06)
    nsl = 3 if lod == 0 else 1
    for k in range(nsl):
        ya, yb = ys0 + (ys1 - ys0) * k / nsl, ys0 + (ys1 - ys0) * (k + 1) / nsl
        for sx in (-1, 1):
            _quad(m, "car_sill", [sx * (sh.X(ya, sill) + 0.005), ya, sill], [sx * (sh.X(yb, sill) + 0.005), yb, sill],
                  [sx * (sh.X(yb, zs) + 0.005), yb, zs], [sx * (sh.X(ya, zs) + 0.005), ya, zs], [sx, 0, 0])
    yM = ga1 - 0.13
    zM = sh.zbelt(yM)
    for sx in (-1, 1):
        xm = sh.X(yM, zM)
        c = [sx * (xm + 0.125), yM, zM + 0.055]
        if lod == 0:
            xi_, xo_ = sx * (xm + 0.050), sx * (xm + 0.205)
            zc = zM + 0.058
            A_ = [[xi_, yM - 0.034, zc - 0.036], [xi_, yM + 0.040, zc - 0.030], [xi_, yM + 0.040, zc + 0.034], [xi_, yM - 0.034, zc + 0.040]]
            B_ = [[xo_, yM - 0.034, zc - 0.052], [xo_, yM + 0.012, zc - 0.040], [xo_, yM + 0.012, zc + 0.040], [xo_, yM - 0.034, zc + 0.052]]
            cen = (np.mean(A_, axis=0) + np.mean(B_, axis=0)) / 2
            for k in range(4):
                k2 = (k + 1) % 4
                q = [A_[k], A_[k2], B_[k2], B_[k]]
                _oq(m, "car_glass" if k == 3 else paint, q, np.mean(q, axis=0) - cen)       # k == 3: the mirror glass face
            _oq(m, paint, A_, np.array([-sx, 0, 0]))
            _oq(m, paint, B_, np.array([sx, 0, 0]))
            _box5(m, "car_trim", [sx * (xm + 0.02), yM + 0.004, zM + 0.022], 0.045, 0.028, 0.022, (-sx, 0, 0))   # foot
        else:
            _box5(m, paint, c, 0.085, 0.03, 0.055, (0, 0, 0))
    if lod == 0:
        def vline(y, za, zb_, k=4):
            return [(y, za + (zb_ - za) * j / k) for j in range(k + 1)]
        zd0 = sill + 0.085
        y1d = yfa + ra + 0.10
        y3d = (yra + 0.12) if not cargo else (yB - 1.10)
        strip("car_trim", vline(y1d, zd0, sh.ztop(y1d) - 0.02), 0.006)
        strip("car_trim", vline(yB, zd0, sh.zbelt(yB) - 0.004), 0.006)
        strip("car_trim", vline(y3d, (r + ra + 0.05) if not cargo else zd0, sh.zbelt(y3d) - 0.004), 0.006)
        strip("car_trim", [(y1d, zd0), ((y1d + yB) / 2, zd0), (yB, zd0), ((yB + y3d) / 2, zd0), (y3d, zd0)]
              if cargo else [(y1d, zd0), ((y1d + yB) / 2, zd0), (yB, zd0), (ys0 + 0.02, zd0)], 0.005)   # door bottoms
        # bumper / wing seams: from the lamp's lower corner to the arch, from the tail lamp to the rear arch
        pa = sh.ptf(iH, to1, 2.0)[0]
        aa = math.radians(52)
        strip("car_trim", [(pa[1] - 0.004, pa[2]), (yfa + ra * math.cos(aa) + 0.012, r + ra * math.sin(aa) + 0.03)], 0.005)
        pb = sh.S[sh.mid["RB"]]
        strip("car_trim", [(pb[0] + 0.004, pb[1] + 0.012), (yra - ra * math.cos(aa) - 0.012, r + ra * math.sin(aa) + 0.03)], 0.005)
        if cargo:                                   # sliding-door track under the (blind) rear quarter
            zt_ = sh.zbelt(y3d) - 0.16
            strip("car_trim", [(y3d - 0.02, zt_), ((y3d + sh.y0 + 0.30) / 2, zt_), (sh.y0 + 0.30, zt_)], 0.014)
        for y in (yB + 0.07, y3d + 0.09):                       # door handles: dark recess + body-colour grip
            zh = sh.ztop(y) - sh.shd - 0.045
            for sx in (-1, 1):
                x = sx * (sh.X(y, zh) + 0.006)
                _quad(m, "car_trim", [x, y - 0.012, zh - 0.022], [x, y + 0.185, zh - 0.022], [x, y + 0.185, zh + 0.036],
                      [x, y - 0.012, zh + 0.036], [sx, 0, 0])
                _box5(m, "car_sill" if cargo else paint, [sx * (sh.X(y, zh) + 0.016), y + 0.0825, zh + 0.017],
                      0.011, 0.0825, 0.012, (-sx, 0, 0))
        # bonnet shut lines along the wings + the cowl panel under the wipers
        i0_, i1_ = sh.mid["G4"], sh.first["H1"] + 1
        for i in range(i0_, i1_):
            da, db = 0.006 / (sh.R[i] * 1.57), 0.006 / (sh.R[i + 1] * 1.57)
            for sx in (-1, 1):
                q, nn = [], np.zeros(3)
                for ii, g in ((i, 1.12 - da), (i, 1.12 + da), (i + 1, 1.12 + db), (i + 1, 1.12 - db)):
                    pp, nrm = sh.pt(ii, sx * g)
                    nrm = nrm / np.linalg.norm(nrm)
                    q.append(pp + nrm * 0.004)
                    nn += nrm
                _quad(m, "car_trim", *q, nn)
        patch("H1", 0.0, 0.014 / lnH, [-1.0, -0.5, 0.0, 0.5, 1.0], "car_trim", lift=0.004)                  # bonnet front edge
        lw = elen("G4")
        patch("G4", 0.0, min(0.5, 0.055 / lw), [-0.96, -0.5, 0.0, 0.5, 0.96], "car_trim", lift=0.004)      # cowl panel
        lg_ = elen("G3")
        def ridge(name, ta, ga_, tb, gb_, w, h_):
            """Bar with a roof section (two faces) on a shell edge from (ta, ga_) to (tb, gb_): wiper arms and blades."""
            i = sh.seg[name]
            (pa, na), (pb, nb) = sh.ptf(i, ta, ga_), sh.ptf(i, tb, gb_)
            dr = pb - pa
            sa = np.cross(na, dr)
            sa = sa / np.linalg.norm(sa) * w
            a0, b0 = pa + na * 0.003, pb + nb * 0.003
            a1, b1 = pa + na * h_, pb + nb * h_
            _quad(m, "car_trim", a0 - sa, b0 - sa, b1, a1, na - sa / w)
            _quad(m, "car_trim", a1, b1, b0 + sa, a0 + sa, na + sa / w)
        for ga_, gb_, gp in ((-0.80, -0.06, -0.52), (0.0, 0.74, 0.30)):                    # wipers parked on the screen
            ridge("G3", 1.0 - 0.035 / lg_, ga_, 1.0 - 0.090 / lg_, gb_, 0.011, 0.020)       # blade
            ridge("G3", 1.0 - 0.004 / lg_, gp, 1.0 - 0.062 / lg_, (ga_ + gb_) / 2, 0.007, 0.030)   # arm from the cowl pivot
        if not cargo and not d["deck"]:                                                    # rear wiper
            lr = elen("G0")
            ridge("G0", 0.070 / lr, -0.04, 0.085 / lr, 0.50, 0.010, 0.018)
        # rubber seals of the bonded screens: black band along the pillars and the header (r10)
        for name in ("G3",) + (() if cargo else ("G0",)):
            ln_ = elen(name)
            t0_, t1_ = (0.0, 1.0)
            for sx in (-1, 1):
                patch(name, t0_, t1_, [sx * 0.945, sx * 1.0], "car_trim", lift=0.003)
            th = 0.026 / ln_
            ta_, tb_ = ((0.0, th) if name == "G3" else (1.0 - th, 1.0))                    # header = the roof end of the pane
            patch(name, ta_, tb_, [-0.945, -0.5, 0.0, 0.5, 0.945], "car_trim", lift=0.003)
        if d["deck"]:                                                                      # boot lid shut line
            patch("R3", 0.04, 0.04 + 0.012 / elen("R3"), [-0.97, -0.5, 0.0, 0.5, 0.97], "car_trim", lift=0.003)
        if d.get("rails"):
            g1, g3 = sh.P[sh.mid["G1"]], sh.P[sh.mid["G3"]]
            for sx in (-1, 1):
                pr = sh.pt(sh.mid["G2"], sx * 0.93)[0]
                _box5(m, "rim_dark", [pr[0], (g1[0] + g3[0]) / 2 - 0.05, pr[2] + 0.016], 0.011,
                      (g3[0] - g1[0]) / 2 - 0.25, 0.011, (0, 0, -1))

        # ---- interior seen through the glass: tub, dashboard, seats with headrests
        it = "car_interior"
        yi0, yi1 = ga0 + 0.02, ga1 + 0.05                  # r8 N-13: the tub reaches the base of the rear glass
        xi = hw - 0.13
        zf0 = sill + 0.12
        _quad(m, it, [-xi, yi0, zf0], [xi, yi0, zf0], [xi, yi1, zf0], [-xi, yi1, zf0], [0, 0, 1])
        for sx in (-1, 1):
            _quad(m, it, [sx * xi, yi0, zf0], [sx * xi, yi1, zf0], [sx * xi, yi1, sh.zbelt(yi1)],
                  [sx * xi, yi0, sh.zbelt(yi0)], [-sx, 0, 0])
        _quad(m, it, [-xi, yi0, zf0], [xi, yi0, zf0], [xi, yi0, sh.zbelt(yi0)], [-xi, yi0, sh.zbelt(yi0)], [0, 1, 0])
        if not cargo:                                # shelf from the tub's rear wall up to the base of the rear glass
            ib = sh.mid["G0"]
            ql = [sh.pt(ib, g)[0] - np.array([0, 0, 0.006]) for g in (-2.0, -1.0, 1.0, 2.0)]
            zb0 = sh.zbelt(yi0)
            _oq(m, it, [np.array([-xi, yi0, zb0]), np.array([xi, yi0, zb0]), ql[3], ql[2], ql[1], ql[0]], [0, 0.3, 1])
        yl = [yi0, min(ga0 + 0.55, (yi0 + yi1) / 2), yi1]
        for sx in (-1, 1):                           # door tops between the cabin wall and the glass line
            for ya, yb in zip(yl[:-1], yl[1:]):
                za, zb_ = sh.zbelt(ya), sh.zbelt(yb)
                _quad(m, it, [sx * xi, ya, za], [sx * sh.X(ya, za), ya, za], [sx * sh.X(yb, zb_), yb, zb_],
                      [sx * xi, yb, zb_], [0, 0, 1])
        zbl = float(sh.zbelt(yi1))
        zd = zbl - 0.02
        zd0 = max(zf0, r + ra + 0.02)
        _box5(m, it, [0, yi1 - 0.27, (zd + zd0) / 2], xi - 0.03, 0.27, (zd - zd0) / 2, (0, 0, 0))
        xb_ = sh.X(yi1, zbl) - 0.03
        # bulkhead up to the bonnet skin at the cowl (r9: the cowl centre is crowned above the side belt)
        zc0 = float(sh.pt(sh.mid["G4"], 0.0)[0][2]) - 0.014
        zc1 = float(sh.pt(sh.mid["G4"], 0.9)[0][2]) - 0.014
        _oq(m, it, [np.array(q_) for q_ in ([-xb_, yi1, zd0], [xb_, yi1, zd0], [xb_, yi1, zbl - 0.02],
                                             [xb_ - 0.10, yi1, zc1], [0.0, yi1, zc0], [-xb_ + 0.10, yi1, zc1],
                                             [-xb_, yi1, zbl - 0.02])], [0, -1, 0])
        xw_ = sh.X(yfa, r) - 0.30                              # between the wheel housings: down to the floor
        _quad(m, it, [-xw_, yi1, zf0], [xw_, yi1, zf0], [xw_, yi1, zd0], [-xw_, yi1, zd0], [0, -1, 0])
        ysb = yB + 0.02
        zs0 = zf0 + 0.20
        zbb = float(sh.zbelt(ysb))
        for sx in (-1, 1):                                                                             # front seats
            _box5(m, it, [sx * 0.37, ysb, (zs0 + zbb + 0.12) / 2], 0.24, 0.07, (zbb + 0.12 - zs0) / 2, (0, 0, -1))
            _box5(m, it, [sx * 0.37, ysb + 0.02, zbb + 0.25], 0.12, 0.05, 0.095, (0, 0, -1))
            _box5(m, it, [sx * 0.37, ysb + 0.30, zf0 + 0.27], 0.24, 0.25, 0.07, (0, 0, -1))
        if cargo:
            # bulkhead up to the roof lining (r8 N-13: the gap under the roof opened the empty cargo bay)
            xs_ = xi - 0.14
            _oq(m, it, [np.array(q_) for q_ in ([-xi, ysb - 0.12, zf0], [xi, ysb - 0.12, zf0],
                                                 [xi, ysb - 0.12, H - 0.20], [xs_, ysb - 0.12, H - 0.03],
                                                 [-xs_, ysb - 0.12, H - 0.03], [-xi, ysb - 0.12, H - 0.20])], [0, 1, 0])
        else:
            yrs = max(yra + 0.12, ga0 + 0.55)
            zrb = float(sh.zbelt(yrs))
            _box5(m, it, [0, yrs, (zs0 + zrb + 0.08) / 2], 0.56, 0.08, (zrb + 0.08 - zs0) / 2, (0, 0, -1))
            for sx in (-1, 1):
                _box5(m, it, [sx * 0.36, yrs + 0.02, zrb + 0.17], 0.11, 0.05, 0.075, (0, 0, -1))
            _quad(m, it, [-xi, yi0, sh.zbelt(yi0) - 0.02], [xi, yi0, sh.zbelt(yi0) - 0.02], [xi, yrs, zrb - 0.02],
                  [-xi, yrs, zrb - 0.02], [0, 0, 1])                                                  # parcel shelf
    return _paint_uv(m)


def _vehicle_far(d, paint, steel=False):
    """LOD2 (r10, ADR 0078; High 127.5-300 m, Low 42.5-300 m): the r9 / r10 silhouette at its control stations instead
    of the first-pass box. Top strip across the body's own side line (plan taper at the corners, tumblehome), side
    polygon down to the sill, glazed greenhouse, hexagonal tyres with a rim, tail and head lamp blocks, closed
    under-body skirt (hole test)."""
    m = Mesh()
    sh = _Shell(d, 1)
    cargo = d.get("cargo", False)
    hw, sill, r = d["W"] / 2, d["sill"], d["r"]
    bmat = "car_sill" if d.get("blackbump") else paint
    matname = {"paint": paint, "glass": "car_glass", "trim": "car_trim", "bump": bmat}
    keep = [n_ for n_ in ("R0", "R1", "R2", "R3", "G0", "G1", "G2", "G3", "G4", "H1", "F1", "F2", "F3") if n_ in sh.mid]
    C = {c["n"]: c for c in sh.C}
    idx = [sh.mid[n_] for n_ in keep]
    P = [sh.P[i] for i in idx]                               # top line (y, z)
    S = [sh.S[i] for i in idx]                               # side line
    X = [float(sh.Sx[i]) for i in idx]
    for k in range(len(keep) - 1):
        mat = matname[C[keep[k]]["mat"]]
        e = P[k + 1] - P[k]
        _quad(m, mat, [X[k], *P[k]], [-X[k], *P[k]], [-X[k + 1], *P[k + 1]], [X[k + 1], *P[k + 1]], [0, -e[1], e[0]])
    ig0, ig4 = keep.index("G0"), keep.index("G4")
    zb = sill + 0.02
    for sx in (1, -1):
        # shoulder strip between the top line and the side line is skipped: the side polygons start at the top line
        body = [(X[k], P[k][0], P[k][1]) for k in range(ig0 + 1)] + [(X[k], P[k][0], P[k][1]) for k in range(ig4, len(keep))]
        body += [(sh.X(P[-1][0], zb), P[-1][0], zb), (sh.X(P[0][0], zb), P[0][0], zb)]
        Pb = np.array(body)
        for a, b, c in _earclip(Pb[:, 1:]):
            _oq(m, paint, [Pb[j] * [sx, 1, 1] for j in (a, b, c)], [sx, 0, 0])
        gh = np.array([(X[k], P[k][0], P[k][1]) for k in range(ig0, ig4 + 1)])
        for a, b, c in _earclip(gh[:, 1:]):
            _oq(m, paint if cargo else "car_glass", [gh[j] * [sx, 1, 1] for j in (a, b, c)], [sx, 0, 0])
        if cargo:                                            # cab side window
            ya, yb = P[ig4][0] - d["bp"] + 0.05, P[ig4][0] - 0.12
            za, zt = d["belt"] + 0.04, d["H"] - 0.22
            _oq(m, "car_glass", [[sx * (sh.X(ya, za) + 0.01), ya, za], [sx * (sh.X(yb, za) + 0.01), yb, za],
                                 [sx * (sh.X(ya, zt) + 0.01), ya + 0.1, zt]], [sx, 0, 0])
        for yc in (sh.yra, sh.yfa):
            xo = sh.X(yc, r) + 0.006
            _disc(m, "tyre", [sx * xo, yc, r], r, 6, sx, math.pi / 6)
            rr = (0.60 if steel else 0.66) * r
            _oq(m, "rim_steel" if steel else "rim", [[sx * (xo + 0.006), yc - rr * 0.8, r - rr * 0.8], [sx * (xo + 0.006), yc + rr * 0.8, r - rr * 0.8],
                                                     [sx * (xo + 0.006), yc + rr * 0.8, r + rr * 0.8], [sx * (xo + 0.006), yc - rr * 0.8, r + rr * 0.8]], [sx, 0, 0])
    # closed under-body skirt inside the lower edge (r8 N-13)
    ya, yb = sh.yra - r - 0.10, sh.yfa + r + 0.10
    xc, z0, z1 = hw - 0.16, 0.03, sill + 0.04
    for sx in (-1, 1):
        _oq(m, "tyre", [[sx * xc, ya, z0], [sx * xc, yb, z0], [sx * xc, yb, z1], [sx * xc, ya, z1]], [sx, 0, 0])
    for yy, s_ in ((ya, -1), (yb, 1)):
        _oq(m, "tyre", [[xc, yy, z0], [-xc, yy, z0], [-xc, yy, z1], [xc, yy, z1]], [0, s_, 0])
    # lamp blocks: the red tail band and the bright head band are what still reads as "car" at 20-60 px
    kr, kf = keep.index("R2"), keep.index("H1")

    def band(k, t0, t1, g0, g1, mat):
        a, b = P[k], P[k + 1]
        q = []
        for t, g in ((t0, g0), (t0, g1), (t1, g1), (t1, g0)):
            pt = a + (b - a) * t
            xx = (X[k] + (X[k + 1] - X[k]) * t) * g
            q.append([xx, pt[0], pt[1]])
        e = b - a
        nrm = np.array([0, -e[1], e[0]]) / np.linalg.norm(e)
        _oq(m, mat, [np.array(v) + nrm * 0.012 for v in q], nrm)
    for sx in (-1, 1):
        if cargo:
            band(kr, 0.26, 0.86, sx * 0.80, sx * 0.99, "car_light_tail")
        else:
            band(kr, 0.50, 0.97, sx * 0.42, sx * 0.99, "car_light_tail")
        band(kf, 0.10, 0.62, sx * 0.50, sx * 0.97, "car_light_head")
    return _paint_uv(m)


def _plate_index(name):
    """Atlas cell of a prototype (one fictional plate per prototype, 24 cars + 3 vans < PLATE_FAR)."""
    names = [f"{b}_{c}" for b in CARS for c in CAR_COLOURS] + [f"van_{c}" for c in VAN_COLOURS]
    return names.index(name) if name in names else zlib.crc32(name.encode()) % PLATE_FAR


def _style(name):
    """Per-prototype look (deterministic): dirt level, alloy style, film pattern offset, plate."""
    h = zlib.crc32(name.encode())
    body = name.split("_")[0]
    privacy = body in ("suv", "estate") or (body == "hatch" and (h >> 24) & 1 == 1)
    return dict(dirt=(h & 255) / 255.0, wheel=(h >> 8) % 5, uoff=((h >> 16) & 255) / 255.0, plate=_plate_index(name),
                privacy=privacy)


def _build(d, paint, steel=False, name=""):
    col = Mesh()
    col.box("collision_vehicle", [0, 0, d["H"] / 2], d["W"] / 2, d["L"] / 2, d["H"] / 2)
    st = _style(name)
    return _vehicle2(d, paint, 0, steel, st), _vehicle2(d, paint, 1, steel, st), col, _vehicle_far(d, paint, steel)


def car(body, colour):
    # pressed-steel wheels on the plain white hatch / estate (WORKING_VALUE fleet look), alloys elsewhere
    return _build(CARS[body], f"car_paint_{colour}", steel=(colour == "white" and body in ("hatch", "estate")),
                  name=f"{body}_{colour}")


def van(colour):
    return _build(VAN, f"car_paint_{colour}", steel=True, name=f"van_{colour}")
