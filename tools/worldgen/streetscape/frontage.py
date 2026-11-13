"""ADR 0126 - authored frontage of trade pavilions (pawilony handlowo-usługowe) along the route.

The generic generator gives every "obiekt handlowo-usługowy" under 1500 m2 the office facade (punched windows in
light render) and every "magazyn" the sheet-clad hall. The showrooms along the G3-B stretch are what a driver knows
the place by: a brown box with a dark band of glazing under an overhanging roof, a dark-fascia car showroom with a
glazed front, flag masts, an advertising totem and a lattice mast with an oval board. A building override
(`set.frontage` in overrides.yaml, an authored_override that survives every re-import) describes that per building:

    frontage:
      wall: <material>                       # wall colour (existing material of streetscape.materials.M)
      walls: {SW: <material>}                # other colour per facing (rear / side walls), optional
      plinth_m: 0.3
      fascia: {material, height_m, overhang_m, facings}     # band under the roof edge; overhang_m > 0 = roof slab
      glass: showroom_glass                  # pane material (default; ADR 0129: sky gradient instead of black)
      glass_lod1: hall_flashing              # optional pane material of LOD1 only (ADR 0167: a chunk whose LOD1 has
                                             # no glass draws the panes with the frame material instead of one more
                                             # primitive on the Low tier); mullions of such a run are not drawn
      frame: {material: window_frame, material_lod1: plaster_grey, width_m: 0.12}
                                             # optional light window frame (ADR 0171): a ring around every glazed run
                                             # and its mullions, flush with the wall on both LODs (LOD1: front faces
                                             # only, in material_lod1 - a material the LOD1 of the chunk draws already)
      glazing:                               # glazed runs (shopfronts, ribbon bands); z above the floor level
        - {facing: NE, span: [0, 1], z: [0.3, 3.6], pitch_m: 2.4, min_len_m: 6, margin_m: 0.6, transom_m: 2.4}
        - {facing: NW, z: [4.9, 6.3], window_m: [1.5, 1.5]}    # window_m [width, gap] (ADR 0171): the run is split
                                             # into separate punched windows of that width, centred on the run
      accents:                               # wall fields in another colour
        - {facing: NE, span: [0, 0.3], material: <material>, z: [0, 99]}
      props:                                 # advertising structures in front of a wall (no lettering, no brands)
        - {kind: flag_row | totem | sign_mast | car_row, facing: NE, u: 0.5, out_m: 8, ...}
      sign: {code: serwis, facing: NE, u: 0.5, z_m: 4.9}    # functional fascia board (life_props facade_sign_<code>)

facing: N / NE / E / SE / S / SW / W / NW = the compass direction the wall looks to (+-30 deg); span: fractions of the
wall edge from left to right as seen from outside. Every piece is drawn on both building layers (LOD0 `buildings`,
LOD1 `buildings_low`) from the same numbers, so Low and High show the same frontage; only materials that already
exist are used (no new material = no new shader variant; a material new to a chunk is one draw per layer).

ADR 0129 (round 2, review REVIEW-2026-11-12-s12-0126): two material-parameter entries of the existing world shader
(`showroom_glass`: the large panes mirror the sky as a gradient instead of reading black; `frontage_galv`: matt
galvanised grey for masts - the metallic `downpipe` clipped to white under the overcast sky), a two-tone oval board
with a rim and thickness (still no lettering), bowed feather banners on a top arm, and `car_row`: display vehicles
on the lot of a car dealer (existing life_cars prototypes, placed as instances by `place_cars`).
"""
import math

import numpy as np

from . import facade_atlas as FA
from . import facade_kit as FK

BEARING = {"N": 0.0, "NE": 45.0, "E": 90.0, "SE": 135.0, "S": 180.0, "SW": 225.0, "W": 270.0, "NW": 315.0}
FACING_TOL_DEG = 30.0
GLASS_DEPTH = 0.10
FRAME = "hall_flashing"            # dark aluminium profiles; drawn by every building chunk already
MAST = "frontage_galv"             # matt galvanised grey (ADR 0129; `downpipe`, metal 0.7, read white at overcast)
GLASS = "showroom_glass"           # shopfront panes: sky gradient (ADR 0129), same shader and pass as `glass`
RIM = "window_frame"               # light rim / blank field of a sign board
PROP_KINDS = ("flag_row", "totem", "sign_mast", "car_row")


def bearing(nout):
    """Compass bearing (deg, 0 = north, clockwise) of an outward wall normal (E, N)."""
    return (math.degrees(math.atan2(float(nout[0]), float(nout[1]))) + 360.0) % 360.0


def faces(nout, facing):
    if facing in (None, "all", "*"):
        return True
    names = facing if isinstance(facing, (list, tuple)) else [facing]
    b = bearing(nout)
    return any(abs((b - BEARING[n] + 180.0) % 360.0 - 180.0) <= FACING_TOL_DEG for n in names)


def plan(spec, materials=None):
    """Validated copy of a `frontage` override with defaults; None when the building has none.
    materials: known material names (streetscape.materials.M) - an unknown name is an authoring error."""
    if not spec:
        return None
    s = {"wall": spec.get("wall", "plaster_light"), "walls": dict(spec.get("walls") or {}),
         "glass": spec.get("glass", GLASS), "glass_lod1": spec.get("glass_lod1"),
         "plinth_m": float(spec.get("plinth_m", 0.3)), "fascia": None, "glazing": [], "accents": [], "props": [],
         "sign": dict(spec["sign"]) if spec.get("sign") else None, "frame": None}
    fr = spec.get("frame")
    if fr:
        s["frame"] = {"material": fr.get("material", RIM), "width_m": float(fr.get("width_m", 0.12))}
        s["frame"]["material_lod1"] = fr.get("material_lod1", s["frame"]["material"])
    f = spec.get("fascia")
    if f:
        s["fascia"] = {"material": f.get("material", FRAME), "height_m": float(f.get("height_m", 1.0)),
                       "overhang_m": float(f.get("overhang_m", 0.0)), "facings": f.get("facings", "all")}
    for g in spec.get("glazing") or []:
        z = g.get("z", [0.3, 3.2])
        sp = g.get("span", [0.0, 1.0])
        s["glazing"].append({"facing": g["facing"], "span": (float(sp[0]), float(sp[1])), "z": (float(z[0]), float(z[1])),
                             "pitch_m": float(g.get("pitch_m", 2.4)), "min_len_m": float(g.get("min_len_m", 6.0)),
                             "margin_m": float(g.get("margin_m", 0.6)), "transom_m": g.get("transom_m"),
                             "window_m": tuple(float(x) for x in g["window_m"]) if g.get("window_m") else None})
    for a in spec.get("accents") or []:
        z = a.get("z", [0.0, 99.0])
        sp = a.get("span", [0.0, 1.0])
        s["accents"].append({"facing": a["facing"], "span": (float(sp[0]), float(sp[1])), "material": a["material"],
                             "z": (float(z[0]), float(z[1])), "min_len_m": float(a.get("min_len_m", 3.0))})
    for p in spec.get("props") or []:
        if p.get("kind") not in PROP_KINDS:
            raise ValueError(f"frontage prop kind {p.get('kind')!r}: expected one of {PROP_KINDS}")
        if p["kind"] == "car_row":
            bad = [x for x in p.get("protos") or [None] if not _vehicle_proto(x)]
            if bad:
                raise ValueError(f"frontage car_row protos {bad}: expected car_<body>_<colour> / van_<colour> (life_cars)")
        s["props"].append(dict(p))
    names = [s["wall"], s["glass"], *([s["glass_lod1"]] if s["glass_lod1"] else []), *s["walls"].values(), *[a["material"] for a in s["accents"]],
             *[p[k] for p in s["props"] for k in ("material", "rim_material", "bar_material") if p.get(k)]]
    if s["fascia"]:
        names.append(s["fascia"]["material"])
    if s["frame"]:
        names += [s["frame"]["material"], s["frame"]["material_lod1"]]
    for k in [*s["walls"], *[g["facing"] for g in s["glazing"]], *[a["facing"] for a in s["accents"]],
              *[p["facing"] for p in s["props"]], *([s["sign"]["facing"]] if s["sign"] else []),
              *([s["fascia"]["facings"]] if s["fascia"] and s["fascia"]["facings"] != "all" else [])]:
        for n in (k if isinstance(k, (list, tuple)) else [k]):
            if n not in BEARING:
                raise ValueError(f"frontage facing {n!r}: expected one of {sorted(BEARING)}")
    hw = sorted({n for n in names if n.startswith("hall_wall")})
    if hw:      # hall_wall_* needs the wall-top TEXCOORD_1 on every triangle (test_every_hall_wall_has_runoff_uv1)
        raise ValueError(f"frontage materials {hw}: hall_wall_* is reserved for the hall cladding")
    if materials is not None:
        bad = sorted({n for n in names if n not in materials})
        if bad:
            raise ValueError(f"frontage materials not in streetscape.materials.M: {bad}")
    return s


def _vehicle_proto(name):
    from . import life_cars as LC
    t = str(name).split("_")
    return (len(t) == 3 and t[0] == "car" and t[1] in LC.CARS and t[2] in LC.CAR_COLOURS) or (
        len(t) == 2 and t[0] == "van" and t[1] in LC.VAN_COLOURS)


def wall_material(spec, nout):
    for facing, mat in spec["walls"].items():
        if faces(nout, facing):
            return mat
    return spec["wall"]


def openings(spec, nout, L, zref, zt):
    """Glazed runs of one wall edge as wall_with_openings openings (kind `shopfront`: reveals + one glass pane)."""
    f = spec["fascia"]
    ztop = zt - (f["height_m"] if f and faces(nout, f["facings"]) else 0.0) - 0.05
    ops = []
    for g in spec["glazing"]:
        if not faces(nout, g["facing"]) or L < g["min_len_m"]:
            continue
        u0, u1 = max(g["margin_m"], L * g["span"][0]), min(L - g["margin_m"], L * g["span"][1])
        z0, z1 = zref + g["z"][0], min(zref + g["z"][1], ztop)
        if u1 - u0 < 1.0 or z1 - z0 < 0.5 or any(o[0] < u1 and o[1] > u0 and o[2] < z1 and o[3] > z0 for o in ops):
            continue
        runs = [(u0, u1)]
        if g.get("window_m"):                  # punched windows: n x width with gaps, centred on the run
            w, gap = g["window_m"]
            n = int((u1 - u0 + gap) // (w + gap))
            s0 = 0.5 * (u0 + u1) - 0.5 * (n * w + (n - 1) * gap)
            runs = [(s0 + i * (w + gap), s0 + i * (w + gap) + w) for i in range(n)]
        for ua, ub in runs:
            ops.append((ua, ub, z0, z1, GLASS_DEPTH, "shopfront", spec["glass"], g))
    return ops


def wall(acc, wwo, spec, a, c_, nout, L, zbot, zref, zt, u_acc, ground=None):
    """One wall edge of a pavilion on both LODs: plinth, wall colour (accent fields), fascia band, glazed runs with
    mullions, roof slab or coping. wwo = buildings_mesh.wall_with_openings. Returns the openings."""
    d = (c_ - a) / L
    wmat = wall_material(spec, nout)
    zpl = zref + spec["plinth_m"]
    f = spec["fascia"] if spec["fascia"] and faces(nout, spec["fascia"]["facings"]) else None
    zf = zt - f["height_m"] if f else None
    ops = openings(spec, nout, L, zref, zt)
    acc_here = [(L * x["span"][0], L * x["span"][1], zref + x["z"][0], zref + x["z"][1], x["material"])
                for x in spec["accents"] if faces(nout, x["facing"]) and L >= x["min_len_m"]]

    def mat_fn(u0, u1, z0, z1):
        if z1 <= zpl + 1e-6:
            return "plinth_dark"
        um, zm = 0.5 * (u0 + u1), 0.5 * (z0 + z1)
        if zf is not None and z0 >= zf - 1e-6:
            return f["material"]
        for x0, x1, y0, y1, m in acc_here:
            if x0 - 1e-6 <= um <= x1 + 1e-6 and y0 - 1e-6 <= zm <= y1 + 1e-6:
                return m
        return wmat
    zs = [zpl, zf] + [z for x in acc_here for z in x[2:4]]
    us = [FK.safe_u(u, ops, L) for x in acc_here for u in x[:2]]
    d3, n3 = np.append(d, 0.0), np.append(nout, 0.0)
    for layer in (FK.L0, FK.L1):
        low = layer == FK.L1
        gl1 = spec.get("glass_lod1") if low else None
        FK.wall_pieces(wwo, acc, a, d, nout, L, zbot, zt, [(*o[:6], gl1 or o[6]) for o in ops], u_acc, zref, zs, us,
                       mat_fn, layer=layer, reveal=FRAME, ground=ground)
        fr = spec.get("frame")
        fmat = (fr["material_lod1"] if low else fr["material"]) if fr else FRAME
        for (u0, u1, z0, z1, depth, _, _, g) in ops:
            if fr:                             # light frame ring flush with the wall plane (ADR 0171)
                w = fr["width_m"]
                sk = (0, 1, 2, 4, 5) if low else (2,)
                for uc, hu, zc, hz in ((u0 + w / 2, w / 2, 0.5 * (z0 + z1), (z1 - z0) / 2),
                                       (u1 - w / 2, w / 2, 0.5 * (z0 + z1), (z1 - z0) / 2),
                                       (0.5 * (u0 + u1), (u1 - u0) / 2 - w, z0 + w / 2, w / 2),
                                       (0.5 * (u0 + u1), (u1 - u0) / 2 - w, z1 - w / 2, w / 2)):
                    acc.box(layer, fmat, np.append(a + d * uc - nout * (depth / 2), zc), d3 * hu, n3 * (depth / 2),
                            [0, 0, hz], skip=sk)
            elif gl1 == FRAME:                 # panes in the frame material: mullions would not show
                continue
            n = max(1, int(round((u1 - u0) / g["pitch_m"])))
            # mullion: a post from the glass plane to the wall plane (LOD1: its front face only)
            for i in range(1, n):
                c = np.append(a + d * (u0 + (u1 - u0) * i / n) - nout * (depth / 2), 0.5 * (z0 + z1))
                mw, mz = (fr["width_m"] / 2, (z1 - z0) / 2 - fr["width_m"]) if fr else (0.035, (z1 - z0) / 2)
                acc.box(layer, fmat, c, d3 * mw, n3 * (depth / 2), [0, 0, mz],
                        skip=(0, 1, 2, 4, 5) if low else (0, 1, 2))
            zt_ = g.get("transom_m")
            if zt_ is not None and z0 + 0.4 < zref + zt_ < z1 - 0.4:      # transom over the door height
                c = np.append(a + d * (0.5 * (u0 + u1)) - nout * (depth / 2), zref + zt_)
                acc.box(layer, fmat, c, d3 * ((u1 - u0) / 2), n3 * (depth / 2), [0, 0, 0.04],
                        skip=(0, 1, 2, 4, 5) if low else (2, 4, 5))
        if f and f["overhang_m"] > 0.0:        # roof slab over the wall: soffit + edge, mitred by overlap at the corners
            o = f["overhang_m"]
            c = np.append(0.5 * (a + c_) + nout * (o / 2), zt - 0.11)
            acc.box(layer, f["material"], c, d3 * (L / 2 + o), n3 * (o / 2), [0, 0, 0.16], skip=(2,))
        elif low:                              # LOD1 coping ledge (as buildings_mesh.lod1_wall)
            P = lambda q, z: [float(q[0]), float(q[1]), float(z)]
            acc.quad(layer, FRAME, P(a + nout * 0.12, zt - 0.25), P(c_ + nout * 0.12, zt - 0.25), P(c_, zt + 0.05),
                     P(a, zt + 0.05))
        else:
            FK.coping(acc, a, c_, nout, zt, mat=FRAME)
    return ops


# --------------------------------------------------------------------------------------------- props
def _anchor(p, edges):
    """Ground point of a prop: the longest wall edge looking to p.facing, u (fraction of it, left to right from
    outside) and out_m metres in front of it. Returns (point, edge direction, outward normal) or None."""
    best = None
    for a, c_ in edges:
        L = float(np.linalg.norm(c_ - a))
        if L < 0.5:
            continue
        d = (c_ - a) / L
        nout = np.array([d[1], -d[0]])
        if faces(nout, p["facing"]) and (best is None or L > best[0]):
            best = (L, a, d, nout)
    if best is None:
        return None
    L, a, d, nout = best
    return a + d * (L * float(p.get("u", 0.5))) + nout * float(p.get("out_m", 6.0)), d, nout


def flag_row(acc, p, q, d, nout, zg):
    """Row of flag masts with feather banners (plain colour, no lettering): a sleeve along the mast, a short top arm,
    the free edge bowed by the wind (more towards the hem, a little differently on every mast; LOD1: fewer rows).
    The row runs along the wall, turned clockwise by rotate_deg (seen from above); banners hang towards banner_dir
    (out = away from the wall)."""
    n, sp = int(p.get("count", 3)), float(p.get("spacing_m", 4.0))
    rot = math.radians(float(p.get("rotate_deg", 0.0)))
    row = np.array([d[0] * math.cos(rot) + d[1] * math.sin(rot), -d[0] * math.sin(rot) + d[1] * math.cos(rot)])
    h, bw, bh = float(p.get("height_m", 8.0)), float(p.get("banner_w_m", 1.0)), float(p.get("banner_h_m", 3.6))
    bow = float(p.get("bow_m", 0.16))
    bd = nout if p.get("banner_dir", "out") == "out" else d
    d3, n3, b3 = np.append(d, 0.0), np.append(nout, 0.0), np.append(bd, 0.0)
    w3 = np.array([bd[1], -bd[0], 0.0])                  # across the banner (the way the wind pushes it)
    mat = p.get("material", "paint_yellow")
    for i in range(n):
        m = q + row * ((i - (n - 1) / 2) * sp)
        k = 0.7 + 0.6 * ((i * 0.618 + 0.25) % 1.0)       # bow of this banner
        ztop = zg + h - 0.1
        for layer in (FK.L0, FK.L1):
            low = layer == FK.L1
            acc.box(layer, MAST, [m[0], m[1], zg + h / 2], d3 * 0.04, n3 * 0.04, [0, 0, h / 2], skip=(0,))
            acc.box(layer, MAST, np.array([m[0], m[1], ztop + 0.02]) + b3 * (0.03 + bw / 2), b3 * (bw / 2 + 0.03),
                    w3 * 0.02, [0, 0, 0.02], skip=(4,) if low else ())                   # top arm
            rows, cols = (3, 1) if low else (6, 2)
            G = []
            for r in range(rows + 1):
                t = r / rows                              # 0 = top arm, 1 = hem
                off = bow * k * (t ** 1.5 + 0.25 * math.sin(math.pi * t))
                wid = bw * (1.0 - 0.12 * t * t)           # the hem swings in a little
                G.append([np.array([m[0], m[1], ztop - bh * t]) + b3 * (0.06 + wid * c / cols)
                          + w3 * (off * (c / cols) ** 1.6) for c in range(cols + 1)])
            for r in range(rows):
                for c in range(cols):
                    a0, a1, c1, c0 = G[r + 1][c], G[r + 1][c + 1], G[r][c + 1], G[r][c]
                    acc.quad(layer, mat, a0, a1, c1, c0)
                    acc.quad(layer, mat, a1, a0, c0, c1)


def totem(acc, p, q, d, nout, zg):
    """Advertising totem (pylon): a plain slab standing across the wall line, dark base."""
    w, t, h = float(p.get("width_m", 1.6)), float(p.get("depth_m", 0.4)), float(p.get("height_m", 6.0))
    wd = nout if p.get("across", True) else d
    td = np.array([wd[1], -wd[0]])
    for layer in (FK.L0, FK.L1):
        acc.box(layer, p.get("material", "plaster_white"), [q[0], q[1], zg + 0.4 + (h - 0.4) / 2], np.append(wd * w / 2, 0),
                np.append(td * t / 2, 0), [0, 0, (h - 0.4) / 2], skip=(0,))
        acc.box(layer, "plinth_dark", [q[0], q[1], zg + 0.2], np.append(wd * (w / 2 - 0.05), 0),
                np.append(td * (t / 2 - 0.05), 0), [0, 0, 0.2], skip=(0, 1))


def _poly(acc, layer, mat, pts, bd3):
    """Convex polygon (CCW seen from the front) as a fan; coincident corners are dropped (a quad may be a triangle)."""
    P = []
    for q_ in pts:
        if not P or np.linalg.norm(q_ - P[-1]) > 1e-6:
            P.append(q_)
    if len(P) > 1 and np.linalg.norm(P[0] - P[-1]) <= 1e-6:
        P.pop()
    if len(P) < 3:
        return
    V = np.array(P)
    acc.add(layer, mat, V, [[0, i, i + 1] for i in range(1, len(P) - 1)],
            [[float(np.dot(v, bd3)), float(v[2])] for v in V])


def oval_board(acc, layer, ctr, bd, bw, bh, mat, rim_mat, rim, bar, thick, seg, edge, bar_mat=None):
    """Two-sided oval sign board without lettering: a light rim, the colour field and (bar = (width, height, gap) as
    fractions of the board) two blank blocks in a mid tone where the two words of the real board are - greeking, no
    glyphs. One coplanar tessellation per side (horizontal strips, columns at the rim / field / block limits):
    nothing overlaps, so nothing z-fights. edge: the rim of the box (board thickness) is drawn too (LOD0)."""
    a, b = bw / 2, bh / 2
    ai, bi = max(a - rim, 0.0), max(b - rim, 0.0)
    bx, s = (bar[0] * a, bar[1] * b) if bar else (0.0, 0.0)
    gap = bar[2] * a if bar and len(bar) > 2 else 0.0
    bar_mat = bar_mat or rim_mat
    bd3, up = np.append(bd, 0.0), np.array([0.0, 0.0, 1.0])
    bn3 = np.array([bd[1], -bd[0], 0.0])                 # right of bd: (bd, up) is counter-clockwise seen from +bn
    lev = {round(b * math.sin(math.pi * (k / seg - 0.5)), 5) for k in range(seg + 1)} | {-b, b}
    if rim > 0.0:
        lev |= {-bi, bi}
    if bar:
        lev |= {-s, s}
    lev = sorted(lev)

    def xo(z):
        return a * math.sqrt(max(0.0, 1.0 - (z / b) ** 2))

    def xi(z):
        return ai * math.sqrt(max(0.0, 1.0 - (z / bi) ** 2)) if bi > 0.0 and abs(z) < bi else 0.0

    def cols(z):
        i_ = min(xi(z), xo(z)) if rim > 0.0 else xo(z)
        x_ = min(bx, i_)
        g_ = min(gap, x_)
        return [-xo(z), -i_, -x_, -g_, g_, x_, i_, xo(z)]
    for side, flip in ((thick / 2, False), (-thick / 2, True)):
        o3 = ctr + bn3 * side
        for z0, z1 in zip(lev[:-1], lev[1:]):
            c0, c1 = cols(z0), cols(z1)
            inbar = bar and abs(0.5 * (z0 + z1)) < s
            b_ = bar_mat if inbar else mat
            for j, m_ in enumerate((rim_mat, mat, b_, mat, b_, mat, rim_mat)):
                pts = [o3 + bd3 * c0[j] + up * z0, o3 + bd3 * c0[j + 1] + up * z0,
                       o3 + bd3 * c1[j + 1] + up * z1, o3 + bd3 * c1[j] + up * z1]
                _poly(acc, layer, m_, pts[::-1] if flip else pts, bd3)
    if edge:
        ring = [(xo(z), z) for z in lev] + [(-xo(z), z) for z in lev[-2:0:-1]]
        for (x0, z0), (x1, z1) in zip(ring, ring[1:] + ring[:1]):
            p_, q_ = ctr + bd3 * x0 + up * z0, ctr + bd3 * x1 + up * z1
            acc.quad(layer, FRAME, p_ + bn3 * (thick / 2), p_ - bn3 * (thick / 2), q_ - bn3 * (thick / 2),
                     q_ + bn3 * (thick / 2))


def sign_mast(acc, p, q, d, nout, zg):
    """Lattice mast with an oval board on top. The board has a light rim and two blank mid-tone blocks on the colour
    field (what makes it read as a sign board and not as a disc, review 0126 P1) and carries no name and no logo."""
    h, s = float(p.get("height_m", 9.0)), float(p.get("base_m", 0.9)) / 2
    bw, bh = float(p.get("board_w_m", 4.6)), float(p.get("board_h_m", 1.3))
    bd = nout if p.get("board_dir", "along") == "out" else d
    d3, n3 = np.append(d, 0.0), np.append(nout, 0.0)
    zb = zg + h - bh
    leg0 = float(p.get("leg_m", 0.11)) / 2      # LOD0: an open lattice from close up (0.16 read as scaffolding)
    rim = float(p.get("rim_m", 0.09))
    bar = p.get("bar", [0.64, 0.30, 0.03])
    for layer in (FK.L0, FK.L1):
        low = layer == FK.L1
        leg = max(leg0, 0.07) if low else leg0  # LOD1: 0.10 m legs vanished at 80 m on Low (0126 build 1)
        for sx in (-1, 1):
            for sy in (-1, 1):
                c = np.array([*(q + d * (sx * s) + nout * (sy * s)), zg + (h - bh) / 2])
                acc.box(layer, MAST, c, d3 * leg, n3 * leg, [0, 0, (h - bh) / 2], skip=(0, 1))
        rings = max(2, int((h - bh) // 1.5))
        wr = 0.04 if low else 0.03
        for k in range(1, rings + 1):
            z = zg + (h - bh) * k / rings
            for ax_, ay_ in ((d, nout), (nout, d)):
                for sy in (-1, 1):
                    c = np.array([*(q + ay_ * (sy * s)), z])
                    acc.box(layer, MAST, c, np.append(ax_ * s, 0), np.append(ay_ * wr, 0), [0, 0, wr],
                            skip=(0, 1, 4, 5) if low else (4, 5))
            z0 = zg + (h - bh) * (k - 1) / rings     # one diagonal per bay and side, alternating (both LODs: without
            for ax_, ay_ in ((d, nout), (nout, d)):  # them the mast is a ladder, not a lattice)
                for sy in (-1, 1):
                    sg = 1 if (k + (sy > 0)) % 2 else -1
                    p0 = np.array([*(q + ay_ * (sy * s) - ax_ * (sg * s)), z0])
                    p1 = np.array([*(q + ay_ * (sy * s) + ax_ * (sg * s)), z])
                    w3 = np.array([0.0, 0.0, 0.05 if low else 0.04])
                    acc.quad(layer, MAST, p0 - w3, p1 - w3, p1 + w3, p0 + w3)
                    acc.quad(layer, MAST, p1 - w3, p0 - w3, p0 + w3, p1 + w3)
        oval_board(acc, layer, np.array([q[0], q[1], zb + bh / 2]), bd, bw, bh, p.get("material", "bin_plastic_blue"),
                   p.get("rim_material", RIM), rim, bar, float(p.get("thick_m", 0.18)), 12 if low else 16, not low,
                   bar_mat=p.get("bar_material", MAST))


def car_row(p, q, d, nout):
    """Display vehicles on the lot of a car dealer: a tidy row (rotate_deg as flag_row), noses towards `nose`
    (out = away from the wall). Prototypes are the existing life_cars instances (no geometry here); a dealer row
    repeats models, so there is no neighbour rule. Returns the instances for place_cars."""
    n, sp = int(p.get("count", 4)), float(p.get("spacing_m", 2.8))
    rot = math.radians(float(p.get("rotate_deg", 0.0)))
    row = np.array([d[0] * math.cos(rot) + d[1] * math.sin(rot), -d[0] * math.sin(rot) + d[1] * math.cos(rot)])
    nose = np.array([row[1], -row[0]])
    if (float(np.dot(nose, nout)) < 0.0) == (p.get("nose", "out") == "out"):
        nose = -nose
    protos = list(p.get("protos") or ["van_white"])
    out = []
    for i in range(n):
        j = math.sin(12.9898 * (i + 1) + 78.233 * float(p.get("u", 0.5)))      # deterministic +-1
        c = q + row * ((i - (n - 1) / 2) * sp) + nose * (0.12 * j)
        yaw = math.atan2(nose[1], nose[0]) - math.pi / 2 + math.radians(1.2) * math.sin(7.1 * (i + 1))
        out.append({"p": protos[i % len(protos)], "e": round(float(c[0]), 3), "n": round(float(c[1]), 3),
                    "yaw": round(float(yaw), 4)})
    return out


def place_cars(pl, props, report=None):
    """Instances of every `car_row` (buildings report `frontage_props`) on the furniture placer; a vehicle within
    2.2 m of one already standing there (rule car park) is left out. Returns the number placed."""
    n = skipped = 0
    for pr in props or []:
        for c in pr.get("cars", []):
            if any(it["p"].startswith(("car_", "van_")) and math.hypot(it["e"] - c["e"], it["n"] - c["n"]) < 2.2
                   for it in pl.items):
                skipped += 1
                continue
            pl.add(c["p"], np.array([c["e"], c["n"]]), c["yaw"], src=f"frontage:{pr.get('building', '')}:car_row")
            n += 1
    if report is not None:
        report["frontage_cars"] = {"placed": n, "skipped": skipped}
    return n


def props(acc, spec, edges, zground):
    """Advertising structures of the frontage; zground(e, n) = terrain height. Returns their descriptions (QA)."""
    out = []
    for p in spec["props"]:
        an = _anchor(p, edges)
        if an is None:
            out.append({"kind": p["kind"], "placed": False, "reason": f"no wall faces {p['facing']}"})
            continue
        q, d, nout = an
        zg = float(zground(float(q[0]), float(q[1])))
        item = {"kind": p["kind"], "placed": True, "e": round(float(q[0]), 2), "n": round(float(q[1]), 2),
                "z": round(zg, 2)}
        if p["kind"] == "car_row":
            item["cars"] = car_row(p, q, d, nout)
        else:
            {"flag_row": flag_row, "totem": totem, "sign_mast": sign_mast}[p["kind"]](acc, p, q, d, nout, zg)
        out.append(item)
    return out


# --------------------------------------------------------------------------------------------- office facades (ADR 0180)
# Authored window rule per facing of an office building (override `set.facades`, an authored_override). The hashed
# office facade is one pattern on every wall (a grid of punched windows or ribbon rows); a photographed tower has a
# blank gable with one stair column of windows and long walls with one window band per storey in a second wall colour:
#
#     facades:
#       - {facing: [SW, NE], min_len_m: 8, windows: column, u: 0.5, window_w_m: 1.8, wall_material: plaster_beige}
#       - {facing: SE, min_len_m: 18, max_len_m: 19, windows: ribbon, spans: [[0.06, 0.4], [0.6, 1.0]]}
#       - {facing: [SE, NW], min_len_m: 5, windows: ribbon, sill_m: 1.0, head_m: 2.3}
#
# windows: ribbon (one band per storey from pier to pier of each span of the wall, in lights of ~1.5 m; spans = fractions of the wall
# from left to right seen from outside, default the whole wall), column (one window per storey at u = fraction of the
# wall), blank. sill_m / head_m: above the floor of each storey. The first rule that faces the wall (+-30 deg) and
# whose length range holds the wall applies; other walls keep the hashed rule and the building's wall colour. Both
# LODs read the same rectangles (facade_windows): LOD0 cuts them as openings with facade-atlas cells, LOD1 draws them
# as quads of the far-row atlas inside the plain strip of the same <wall>__far_<kind> material (no opening geometry),
# so a rule needs no material the generic office does not have.
FACADE_WINDOWS = ("ribbon", "column", "blank")
FACADE_GROUP = {"ribbon": "ribbon", "column": "office"}        # <wall>__far_<kind> material of the LOD1 wall; also the
# far-row group the windows are read from, except `glazing: light` bands: white-framed windows of the `office` rows
# side by side (one quad per light on LOD1) in the same __far_ribbon material - every __far_* material maps the same
# far-row atlas, so the rows of another group cost no draw
# v range of the plain wall of the far-row atlas used by authored walls: FA.FAR_PLAIN_V runs to 0.95, where the first
# row's balcony slab edge already starts (measured on T_facade_far_BaseColor: 187 / 255 up to v 0.85, 196-206 from
# 0.88) - one tall quad hides that, a plain piece between two windows of every storey would show it as a stripe
FACADE_PLAIN_V = (0.65, 0.85)
RIBBON_LIGHT_M = FA.FAR_PITCH / 2      # one light of a ribbon band
RIBBON_END_M = 0.4


def facade_rules(spec, wall, materials=None):
    """Validated `facades` override (list of rules) with defaults; None when the building has none. wall = the
    building's wall material (a rule without wall_material keeps it)."""
    if not spec:
        return None
    if materials is None:
        from . import materials as MT
        materials = MT.M
    out = []
    for r in spec:
        kind = r.get("windows", "blank")
        if kind not in FACADE_WINDOWS:
            raise ValueError(f"facades windows {kind!r}: expected one of {FACADE_WINDOWS}")
        fac = r.get("facing")
        for n in (fac if isinstance(fac, (list, tuple)) else [fac]):
            if n not in BEARING:
                raise ValueError(f"facades facing {n!r}: expected one of {sorted(BEARING)}")
        w = r.get("wall_material", wall)
        far = f"{w}__far_{FACADE_GROUP[kind]}" if kind in FACADE_GROUP else None
        bad = [m for m in (w, far) if m and m not in materials]
        if bad:
            raise ValueError(f"facades materials not in streetscape.materials.M: {bad}")
        sill, head = float(r.get("sill_m", FA.FAR_SILL["office"])), float(r.get("head_m", FA.FAR_TOP["office"]))
        if not 0.0 < sill < head:
            raise ValueError(f"facades sill_m / head_m {sill} / {head}: expected 0 < sill < head")
        u = float(r.get("u", 0.5))
        spans = sorted((float(x0), float(x1)) for x0, x1 in r.get("spans") or [(0.0, 1.0)])
        if not 0.0 <= u <= 1.0 or any(not 0.0 <= x0 < x1 <= 1.0 for x0, x1 in spans) or any(
                p[1] > q[0] for p, q in zip(spans, spans[1:])):
            raise ValueError(f"facades u {u} / spans {spans}: fractions of the wall 0..1, spans apart and ascending")
        out.append({"facing": fac, "min_len_m": float(r.get("min_len_m", 5.0)), "max_len_m": float(r.get("max_len_m", 1e9)),
                    "windows": kind, "wall": w, "far": far, "sill_m": sill, "head_m": head, "u": u, "spans": spans,
                    "window_w_m": float(r.get("window_w_m", FA.KINDS["off"][0])),
                    "from_storey": int(r.get("from_storey", 1)),
                    "group": "office" if kind == "column" or r.get("glazing", "dark") == "light" else "ribbon",
                    "variants": [int(v) for v in r["variants"]] if r.get("variants") else None})
        if r.get("glazing", "dark") not in ("dark", "light"):
            raise ValueError(f"facades glazing {r.get('glazing')!r}: expected dark or light")
        if kind != "blank" and not _bays(out[-1]["group"], out[-1]["variants"]):
            raise ValueError(f"facades variants {out[-1]['variants']}: no such window in the far rows {out[-1]['group']!r}")
    return out


def _bays(group, variants):
    """(row, bay) of the far rows of a group whose window variant is one of `variants` (None = every bay)."""
    return [(r, b) for r, row in enumerate(FA.FAR_ROWS[group]) for b, e in enumerate(row)
            if e is not None and (variants is None or e[1] in variants)]


def ribbon_lights(length):
    """Lights of a ribbon band of that length: about RIBBON_LIGHT_M each (half a bay = one `off` cell of the facade
    atlas = the mullion pitch of the far ribbon rows), stretched to fill the run (1.25-1.9 m)."""
    return int(round(length / RIBBON_LIGHT_M))


def facade_rule(rules, nout, L):
    """The rule of one wall edge: the first one facing it whose length range holds the edge; None = hashed facade."""
    for r in rules or []:
        if r["min_len_m"] <= L <= r["max_len_m"] and faces(nout, r["facing"]):
            return r
    return None


def _column_u(rule, L):
    w = min(rule["window_w_m"], L - 1.2)
    return min(max(L * rule["u"], w / 2 + 0.6), L - w / 2 - 0.6), w


def facade_runs(rule, L):
    """(u0, u1) of the window runs of one authored wall: ribbon - every span of the wall, 0.4 m kept clear at the
    wall ends (the pier at a footprint step), when at least two lights fit it (ribbon_lights: the run is divided into
    lights of about 1.5 m, so a band runs from pier to pier whatever the wall length); column - the one window."""
    if rule["windows"] == "ribbon":
        out = []
        for x0, x1 in rule["spans"]:
            ua, ub = max(L * x0, RIBBON_END_M), min(L * x1, L - RIBBON_END_M)
            if ribbon_lights(ub - ua) >= 2:
                out.append((ua, ub))
        return out
    if rule["windows"] == "column":
        uc, w = _column_u(rule, L)
        return [(uc - w / 2, uc + w / 2)] if w >= 0.6 else []
    return []


def facade_windows(rule, L, zref, zbase, sh, zt, storeys, key, door=False):
    """Window rectangles of one authored wall, the single source of both LODs, run by run and bottom-up:
    [(u0, u1, z0, z1, group, row, bay offset)]. door: the wall carries the entrance, so its ground floor has no band /
    window (the door takes the column axis or the middle of the wall). Storeys whose window head would come within
    0.3 m of the wall top are left out (as FA.far_storeys)."""
    g = rule["group"]
    bays = _bays(g, rule["variants"]) if rule["windows"] != "blank" else []
    out = []
    for i, (u0, u1) in enumerate(facade_runs(rule, L)):
        for s in range(max(rule["from_storey"] - 1, 1 if door else 0), storeys):
            z0 = zref + zbase + s * sh
            if z0 + rule["head_m"] > zt - 0.3:
                break
            row, off = bays[FA.hint(key, i, s, "bay") % len(bays)]      # a window: that bay; a band: its first light
            out.append((u0, u1, z0 + rule["sill_m"], z0 + rule["head_m"], g, row, off))
    return out


def facade_door_u(rule, L):
    """Axis of the entrance on an authored wall: under the stair column, else the middle of the wall."""
    return _column_u(rule, L)[0] if rule["windows"] == "column" else L / 2


def far_uv(win):
    """UV0 (far-row atlas metres) of a window rectangle on LOD1: the glazed part of its row - the run of a ribbon row
    from its bay offset on, or the one window of an office-row bay."""
    u0, u1, _, _, g, row, off = win
    v = FA.far_row_v(g, row)
    v0, v1 = v + FA.FAR_SILL[g], v + FA.FAR_TOP[g]
    if g == "ribbon":
        x0, x1 = off * FA.FAR_PITCH, off * FA.FAR_PITCH + ribbon_lights(u1 - u0) * RIBBON_LIGHT_M
    else:
        xc, hw = (off + 0.5) * FA.FAR_PITCH, FA.KINDS["off"][0] / 2
        x0, x1 = xc - hw, xc + hw
    return [[x0, v0], [x1, v0], [x1, v1], [x0, v1]]


def lod1_facade(acc, rule, wins, a, d, L, z0, zt):
    """LOD1 of an authored wall above the plinth (z0..zt) in the <wall>__far_<kind> material: columns from left to
    right - plain wall (the plain strip of the far-row atlas), then per window run a stack of plain piece / window
    quad (far_uv) / plain piece. Nothing overlaps (no z-fighting). Returns the number of quads."""
    pv0, pv1 = FACADE_PLAIN_V
    plain = [[0.2, pv0], [1.2, pv0], [1.2, pv1], [0.2, pv1]]
    mat = rule["far"]

    def q(u0, u1, za, zb, uv=plain):
        if u1 - u0 < 0.02 or zb - za < 0.02:
            return 0
        acc.quad(FK.L1, mat, [*(a + d * u0), za], [*(a + d * u1), za], [*(a + d * u1), zb], [*(a + d * u0), zb], uv=uv)
        return 1
    n, u = 0, 0.0
    for u0, u1 in sorted({w[:2] for w in wins}):
        n += q(u, u0, z0, zt)
        z = z0
        for w in sorted((w for w in wins if w[:2] == (u0, u1)), key=lambda w: w[2]):
            n += q(u0, u1, z, w[2])
            k = ribbon_lights(u1 - u0) if rule["windows"] == "ribbon" and w[4] == "office" else 1
            for i in range(k):                 # light band: the window of bay off + i of the office row per light
                n += q(u0 + (u1 - u0) * i / k, u0 + (u1 - u0) * (i + 1) / k, w[2], w[3],
                       far_uv((*w[:6], (w[6] + i) % FA.FAR_BAYS)))
            z = w[3]
        n += q(u0, u1, z, zt)
        u = u1
    return n + q(u, L, z0, zt)
