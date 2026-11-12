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
      glazing:                               # glazed runs (shopfronts, ribbon bands); z above the floor level
        - {facing: NE, span: [0, 1], z: [0.3, 3.6], pitch_m: 2.4, min_len_m: 6, margin_m: 0.6, transom_m: 2.4}
      accents:                               # wall fields in another colour
        - {facing: NE, span: [0, 0.3], material: <material>, z: [0, 99]}
      props:                                 # advertising structures in front of a wall (no lettering, no brands)
        - {kind: flag_row | totem | sign_mast, facing: NE, u: 0.5, out_m: 8, ...}
      sign: {code: serwis, facing: NE, u: 0.5, z_m: 4.9}    # functional fascia board (life_props facade_sign_<code>)

facing: N / NE / E / SE / S / SW / W / NW = the compass direction the wall looks to (+-30 deg); span: fractions of the
wall edge from left to right as seen from outside. Every piece is drawn on both building layers (LOD0 `buildings`,
LOD1 `buildings_low`) from the same numbers, so Low and High show the same frontage; only materials that already
exist are used (no new material = no new shader variant; a material new to a chunk is one draw per layer).
"""
import math

import numpy as np

from . import facade_kit as FK

BEARING = {"N": 0.0, "NE": 45.0, "E": 90.0, "SE": 135.0, "S": 180.0, "SW": 225.0, "W": 270.0, "NW": 315.0}
FACING_TOL_DEG = 30.0
GLASS_DEPTH = 0.10
FRAME = "hall_flashing"            # dark aluminium profiles; drawn by every building chunk already
MAST = "downpipe"                  # galvanised steel grey, on both LODs already
PROP_KINDS = ("flag_row", "totem", "sign_mast")


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
         "plinth_m": float(spec.get("plinth_m", 0.3)), "fascia": None, "glazing": [], "accents": [], "props": [],
         "sign": dict(spec["sign"]) if spec.get("sign") else None}
    f = spec.get("fascia")
    if f:
        s["fascia"] = {"material": f.get("material", FRAME), "height_m": float(f.get("height_m", 1.0)),
                       "overhang_m": float(f.get("overhang_m", 0.0)), "facings": f.get("facings", "all")}
    for g in spec.get("glazing") or []:
        z = g.get("z", [0.3, 3.2])
        sp = g.get("span", [0.0, 1.0])
        s["glazing"].append({"facing": g["facing"], "span": (float(sp[0]), float(sp[1])), "z": (float(z[0]), float(z[1])),
                             "pitch_m": float(g.get("pitch_m", 2.4)), "min_len_m": float(g.get("min_len_m", 6.0)),
                             "margin_m": float(g.get("margin_m", 0.6)), "transom_m": g.get("transom_m")})
    for a in spec.get("accents") or []:
        z = a.get("z", [0.0, 99.0])
        sp = a.get("span", [0.0, 1.0])
        s["accents"].append({"facing": a["facing"], "span": (float(sp[0]), float(sp[1])), "material": a["material"],
                             "z": (float(z[0]), float(z[1])), "min_len_m": float(a.get("min_len_m", 3.0))})
    for p in spec.get("props") or []:
        if p.get("kind") not in PROP_KINDS:
            raise ValueError(f"frontage prop kind {p.get('kind')!r}: expected one of {PROP_KINDS}")
        s["props"].append(dict(p))
    names = [s["wall"], *s["walls"].values(), *[a["material"] for a in s["accents"]],
             *[p["material"] for p in s["props"] if p.get("material")]]
    if s["fascia"]:
        names.append(s["fascia"]["material"])
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
        ops.append((u0, u1, z0, z1, GLASS_DEPTH, "shopfront", "glass", g))
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
        FK.wall_pieces(wwo, acc, a, d, nout, L, zbot, zt, [o[:7] for o in ops], u_acc, zref, zs, us, mat_fn, layer=layer,
                       reveal=FRAME, ground=ground)
        low = layer == FK.L1
        for (u0, u1, z0, z1, depth, _, _, g) in ops:
            n = max(1, int(round((u1 - u0) / g["pitch_m"])))
            # mullion: a post from the glass plane to the wall plane (LOD1: its front face only)
            for i in range(1, n):
                c = np.append(a + d * (u0 + (u1 - u0) * i / n) - nout * (depth / 2), 0.5 * (z0 + z1))
                acc.box(layer, FRAME, c, d3 * 0.035, n3 * (depth / 2), [0, 0, (z1 - z0) / 2],
                        skip=(0, 1, 2, 4, 5) if low else (0, 1, 2))
            zt_ = g.get("transom_m")
            if zt_ is not None and z0 + 0.4 < zref + zt_ < z1 - 0.4:      # transom over the door height
                c = np.append(a + d * (0.5 * (u0 + u1)) - nout * (depth / 2), zref + zt_)
                acc.box(layer, FRAME, c, d3 * ((u1 - u0) / 2), n3 * (depth / 2), [0, 0, 0.04],
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
    """Row of flag masts along the wall with vertical banners (plain colour, no lettering)."""
    n, sp = int(p.get("count", 3)), float(p.get("spacing_m", 4.0))
    h, bw, bh = float(p.get("height_m", 8.0)), float(p.get("banner_w_m", 1.0)), float(p.get("banner_h_m", 3.6))
    bd = nout if p.get("banner_dir", "out") == "out" else d
    d3, n3, b3 = np.append(d, 0.0), np.append(nout, 0.0), np.append(bd, 0.0)
    for i in range(n):
        m = q + d * ((i - (n - 1) / 2) * sp)
        for layer in (FK.L0, FK.L1):
            acc.box(layer, MAST, [m[0], m[1], zg + h / 2], d3 * 0.04, n3 * 0.04, [0, 0, h / 2], skip=(0,))
            a0 = np.array([m[0], m[1], zg + h - bh - 0.1]) + b3 * 0.06
            a1 = a0 + b3 * bw
            up = np.array([0.0, 0.0, bh])
            acc.quad(layer, p.get("material", "paint_yellow"), a0, a1, a1 + up, a0 + up)
            acc.quad(layer, p.get("material", "paint_yellow"), a1, a0, a0 + up, a1 + up)


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


def sign_mast(acc, p, q, d, nout, zg):
    """Lattice mast with an oval board on top (the board is a plain colour field: no name, no logo)."""
    h, s = float(p.get("height_m", 9.0)), float(p.get("base_m", 0.9)) / 2
    bw, bh = float(p.get("board_w_m", 4.6)), float(p.get("board_h_m", 1.3))
    bd = nout if p.get("board_dir", "along") == "out" else d
    bn = np.array([bd[1], -bd[0]])
    d3, n3 = np.append(d, 0.0), np.append(nout, 0.0)
    zb = zg + h - bh
    for layer in (FK.L0, FK.L1):
        low = layer == FK.L1
        for sx in (-1, 1):
            for sy in (-1, 1):
                c = np.array([*(q + d * (sx * s) + nout * (sy * s)), zg + (h - bh) / 2])
                acc.box(layer, MAST, c, d3 * 0.035, n3 * 0.035, [0, 0, (h - bh) / 2], skip=(0, 1))
        rings = max(2, int((h - bh) // 1.5))
        for k in range(1, rings + 1):
            z = zg + (h - bh) * k / rings
            for ax_, ay_ in ((d, nout), (nout, d)):
                for sy in (-1, 1):
                    c = np.array([*(q + ay_ * (sy * s)), z])
                    acc.box(layer, MAST, c, np.append(ax_ * s, 0), np.append(ay_ * 0.02, 0), [0, 0, 0.025],
                            skip=(0, 1, 4, 5) if low else (4, 5))
            if low:
                continue
            z0 = zg + (h - bh) * (k - 1) / rings     # one diagonal per bay and side, alternating
            for ax_, ay_ in ((d, nout), (nout, d)):
                for sy in (-1, 1):
                    sg = 1 if (k + (sy > 0)) % 2 else -1
                    p0 = np.array([*(q + ay_ * (sy * s) - ax_ * (sg * s)), z0])
                    p1 = np.array([*(q + ay_ * (sy * s) + ax_ * (sg * s)), z])
                    w3 = np.array([0.0, 0.0, 0.03])
                    acc.quad(layer, MAST, p0 - w3, p1 - w3, p1 + w3, p0 + w3)
                    acc.quad(layer, MAST, p1 - w3, p0 - w3, p0 + w3, p1 + w3)
        seg = 12 if low else 20                      # oval board, both sides
        ctr = np.array([q[0], q[1], zb + bh / 2])
        ring = [ctr + np.append(bd * (bw / 2 * math.cos(2 * math.pi * i / seg)), bh / 2 * math.sin(2 * math.pi * i / seg))
                for i in range(seg)]
        mat = p.get("material", "bin_plastic_blue")
        for off, flip in ((0.04, False), (-0.04, True)):
            o3 = np.append(bn * off, 0.0)
            V = np.array([ctr + o3] + [r + o3 for r in ring])
            # bn = right of bd, so the ring (bd -> up) is counter-clockwise seen from the +bn side: flip for -bn
            T = [[0, 1 + (i + 1) % seg, 1 + i] if flip else [0, 1 + i, 1 + (i + 1) % seg] for i in range(seg)]
            acc.add(layer, mat, V, T, [[float(v[0] + v[1]), float(v[2])] for v in V])


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
        {"flag_row": flag_row, "totem": totem, "sign_mast": sign_mast}[p["kind"]](acc, p, q, d, nout, zg)
        out.append({"kind": p["kind"], "placed": True, "e": round(float(q[0]), 2), "n": round(float(q[1]), 2),
                    "z": round(zg, 2)})
    return out
