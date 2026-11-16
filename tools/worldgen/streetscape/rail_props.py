"""Level-crossing devices of the rail stage (ADR 0217, FIX 4): St Andrew's crosses G-3 / G-4, half-barriers with their
drives, road signals and the bell, as prototypes of the street-prop library + their instances.

Spawner = the generator: `place()` turns the markers of streetscape.rail.Plan (one list for rail.json and for the
scene) into ordinary furniture instances (Placer items), so they ride the existing instance import, LOD and collision
path of the engine - no prefab is clicked by hand and nothing new is needed in C#. Prototypes are registered only when
a region with the rail stage places a marker (PROTOS, read by props.build_all like gate3_landmarks.PROTOS): the prop
library of every other region is unchanged. Only materials that already exist in streetscape.materials are used.

Frame of every prototype: origin on the ground at the post / drive axis, +y = the direction the face looks (signs,
signals: towards the oncoming driver) or the direction the lowered boom points (barriers), +z up.

What the references show (DW671 x line 38, Mapillary 1569863873404925 of 2020-06-23 and 828893548045009 of 2019-07-03,
CC BY-SA, reference only; GUGiK orthophoto 2025 0.1 m): raised red-white booms on orange drive cabinets on both sides
of each approach, a grey mast with two red lamps side by side on round black backboards beside each drive. Every
dimension below is WORKING_VALUE read off those photos against the 7 m road unless it names a source.
"""

from __future__ import annotations

import math

import numpy as np

from . import props as PP

PROTOS = {}                   # prototype name -> (lod0, lod1, collision); filled by place()
# Prototype names start with `signal_`: the instance LOD rule of that class (LOD1 from 50 m, culled at 250 m, both in
# roads.build_world.lod_ends and Game.World.Import.InstanceImporter) instead of the default 30 / 120 m - a barrier
# must be seen from the whole approach.

# ------------------------------------------------------------------------------------------------ dimensions
POST_D_M = 0.06               # Ø60 mm sign post (roads.standards.SIGN_POST_D)
SALTIRE_BORDER_M = 0.025      # red border of the white arms (WORKING_VALUE; drawing of G-3 in Dz.U. 2019 poz. 2311
#                               zał. 1 not re-read: white cross with a red border, UNVERIFIED proportions)
SALTIRE_G4_DROP_M = 0.30      # G-4: the second (half) cross under the first one (WORKING_VALUE)
SIGNAL_MAST_H_M = 3.0
SIGNAL_MAST_D_M = 0.10
SIGNAL_LAMP_Z_M = 2.35        # centre of the two red lamps
SIGNAL_LAMP_D_M = 0.20
SIGNAL_DISC_D_M = 0.50        # round black backboard of each lamp
SIGNAL_LAMP_GAP_M = 0.60      # lamp centre to lamp centre
DRIVE_M = (0.45, 0.50, 1.05)  # drive cabinet (across the boom, along the boom, height)
BOOM_PIVOT_Z_M = 0.95
BOOM_SECTION_M = (0.09, 0.045)
BOOM_RAISED_DEG = 86.0        # open crossing: boom almost vertical (no train traffic is simulated)
BOOM_TAIL_M = 0.60            # counterweight arm behind the pivot
BOOM_BAND_M = 0.50            # red / white bands of the boom (Mapillary 1569863873404925: ~8 bands on the raised boom)
BELL_Z_M = 2.75
MAST_BAND_M = 0.40            # red / white bands of the signal mast (Mapillary 1832769196903759: banded mast; band
#                               length WORKING_VALUE). REVIEW s22 0217 visual P1-3
# G-3 / G-4 arms (colour pattern Dz.U. 2019 poz. 2310, PDF p. 51, viewed 2026-11-15): white arms with two red bands
# on each half, the outer one at the tip. Band positions as fractions of the half arm, WORKING_VALUE read off the
# pattern (the construction drawing in Dz.U. 2019 poz. 2311 zał. 1 was not read).
SALTIRE_BANDS = ((0.00, 0.28, "paint_white_reflective"), (0.28, 0.52, "paint_ral3020"),
                 (0.52, 0.78, "paint_white_reflective"), (0.78, 1.00, "paint_ral3020"))
G2_TOP_UNDER_LAMPS_M = 2.00   # G-2 on the signal mast "poniżej głowic sygnałowych" (§ 81 ust. 1 pkt 1): top edge, the
#                               lamp backboards end at SIGNAL_LAMP_Z_M - SIGNAL_DISC_D_M / 2 = 2.10 m (WORKING_VALUE)
G2_GAP_UNDER_CROSS_M = 0.05   # G-2 under the G-3 / G-4 on its post (§ 81 ust. 1 pkt 2)
U1_H_M = 1.00                 # guide post U-1a: height / section WORKING_VALUE (Dz.U. 2019 poz. 2311 zał. 4 not read)
U1_SECTION_M = (0.12, 0.04)


def _rot_x(mesh, deg, pivot_z):
    """Rotate every vertex of `mesh` about the x axis through (y = 0, z = pivot_z): +deg lifts +y towards +z."""
    a = math.radians(deg)
    ca, sa = math.cos(a), math.sin(a)
    for Vs, _, _ in mesh.prims.values():
        for V in Vs:
            y, z = V[:, 1].copy(), V[:, 2].copy() - pivot_z
            V[:, 1] = y * ca - z * sa
            V[:, 2] = y * sa + z * ca + pivot_z


def _arm_quads(m, mat, cx, cz, half_l, half_w, ang_deg, y, flip=False, l0=None):
    """One arm of a cross in the x-z plane at depth y: rectangle centred (cx, cz), half length / width, rotated by
    ang_deg from +x. l0 = start along the arm (default -half_l; 0 = half arm from the centre). Faces +y (or -y)."""
    a = math.radians(ang_deg)
    d = np.array([math.cos(a), math.sin(a)])
    n = np.array([-d[1], d[0]])
    s0 = -half_l if l0 is None else l0
    pts = [np.array([cx, cz]) + d * s + n * w for s, w in ((s0, -half_w), (half_l, -half_w), (half_l, half_w), (s0, half_w))]
    V = [[p[0], y, p[1]] for p in pts]
    L, W = half_l - s0, 2 * half_w
    UV = [[0, 0], [L, 0], [L, W], [0, W]]
    # (x, z) counter-clockwise seen from -y; the front (+y) needs the opposite winding
    T = [(0, 1, 2), (0, 2, 3)] if flip else [(0, 2, 1), (0, 3, 2)]
    m.add(mat, V, T, UV)


def saltire(code="G-3", arm_l=1.20, arm_w=0.20, arm_angle=50.0, bottom_z=1.50):
    """St Andrew's cross on its own post: G-3 (one track) = one cross; G-4 (more tracks) = the cross + a half cross
    under it. White arms with red bands (SALTIRE_BANDS; materials paint_white_reflective / paint_ral3020), grey
    back."""
    m, l1, col = PP.Mesh(), PP.Mesh(), PP.Mesh()
    half = arm_angle / 2.0
    hl, hw = arm_l / 2, arm_w / 2
    rise = hl * math.sin(math.radians(half)) + hw * math.cos(math.radians(half))     # centre -> top of the cross
    zc = bottom_z + rise + (SALTIRE_G4_DROP_M if code == "G-4" else 0.0)
    top = zc + rise
    yf = POST_D_M / 2 + 0.014
    arms = [(zc, half, None), (zc, -half, None)]
    if code == "G-4":                          # lower half cross: the two downward half arms, one drop lower
        arms += [(zc - SALTIRE_G4_DROP_M, 180.0 + half, 0.0), (zc - SALTIRE_G4_DROP_M, -half, 0.0)]
    for mm, full in ((m, True), (l1, False)):
        mm.tube("steel_galv", [0, 0, -0.03], [0, 0, top + 0.03], POST_D_M / 2, None, 10 if full else 4)
        for z0, ang, l0 in arms:
            for f0, f1, mat in SALTIRE_BANDS:                  # red / white bands, mirrored about the arm centre
                for sgn in ((1,) if l0 is not None else (1, -1)):
                    a_, b_ = sorted((sgn * f0 * hl, sgn * f1 * hl))
                    _arm_quads(mm, mat, 0.0, z0, b_, hw, ang, yf, l0=a_)
            _arm_quads(mm, "steel_galv", 0.0, z0, hl, hw, ang, yf - 0.003, flip=True, l0=l0)         # back
    col.tube("collision_steel", [0, 0, 0], [0, 0, top], 0.05, None, 4)
    return m, l1, col


def signal(bell=False):
    """Road signal of a level crossing: mast, cross bar, two red lamps (dark at rest) side by side on round black
    backboards; optional bell on the mast top."""
    m, l1, col = PP.Mesh(), PP.Mesh(), PP.Mesh()
    r = SIGNAL_MAST_D_M / 2
    z = SIGNAL_LAMP_Z_M
    for mm, seg, n in ((m, 10, 20), (l1, 5, 8)):
        nb = int(round(SIGNAL_MAST_H_M / MAST_BAND_M))
        for k in range(nb):                                   # red / white banded mast (REVIEW s22 0217 visual P1-3)
            z0, z1 = SIGNAL_MAST_H_M * k / nb, SIGNAL_MAST_H_M * (k + 1) / nb
            mm.tube("paint_ral3020" if k % 2 == 0 else "paint_white_reflective", [0, 0, z0 - (0.05 if k == 0 else 0)],
                    [0, 0, z1], r, None, seg)
        mm.box("signal_housing", [0, r + 0.03, z], SIGNAL_LAMP_GAP_M / 2, 0.025, 0.03)               # cross bar
        for sx in (-1, 1):
            cx = sx * SIGNAL_LAMP_GAP_M / 2
            ang = [-2 * math.pi * i / n for i in range(n)]                                            # normal +y
            for mat, rad, y in (("signal_backplate", SIGNAL_DISC_D_M / 2, r + 0.06),
                                ("signal_red_off", SIGNAL_LAMP_D_M / 2, r + 0.16)):
                V = [[cx, y, z]] + [[cx + rad * math.cos(t), y, z + rad * math.sin(t)] for t in ang]
                mm.add(mat, V, [(0, 1 + i, 1 + (i + 1) % n) for i in range(n)])
                if mat == "signal_backplate":                                                         # rear face
                    Vb = [[cx, y - 0.004, z]] + [[cx + rad * math.cos(t), y - 0.004, z + rad * math.sin(t)] for t in ang]
                    mm.add(mat, Vb, [(0, 1 + (i + 1) % n, 1 + i) for i in range(n)])
            mm.box("signal_housing", [cx, r + 0.11, z], SIGNAL_LAMP_D_M / 2 + 0.02, 0.05, SIGNAL_LAMP_D_M / 2 + 0.02)
        if bell:
            mm.tube("signal_housing", [0, 0, BELL_Z_M], [0, 0, BELL_Z_M + 0.12], 0.11, 0.05, seg)
    col.tube("collision_steel", [0, 0, 0], [0, 0, SIGNAL_MAST_H_M], 0.08, None, 6)
    return m, l1, col


def barrier(boom_len):
    """Half-barrier at rest (crossing open): drive cabinet at the origin, boom raised BOOM_RAISED_DEG towards +y
    (the direction it points when lowered), short counterweight arm behind the pivot."""
    m, col = PP.Mesh(), PP.Mesh()
    dx, dy, dz = DRIVE_M
    m.box("drive_cabinet_faded", [0, 0, dz / 2], dx / 2, dy / 2, dz / 2)       # sun-faded orange (REVIEW s22 P2-11)
    m.box("steel_painted", [0, 0, dz + 0.02], dx / 2 + 0.02, dy / 2 + 0.02, 0.02)                    # cabinet cap
    m.box("concrete_base", [0, 0, -0.02], dx / 2 + 0.08, dy / 2 + 0.08, 0.06)
    boom = PP.Mesh()
    bw, bh = BOOM_SECTION_M
    x = dx / 2 + bh / 2 + 0.03                                  # the boom swings beside the cabinet
    # red / white bands as geometry (materials `gate_boom` has no texture set in materials_spec.json: plain grey)
    nb = max(2, int(round(boom_len / BOOM_BAND_M)))
    for k in range(nb):
        y0, y1 = boom_len * k / nb, boom_len * (k + 1) / nb
        boom.box("paint_ral3020" if k % 2 == 0 else "paint_white_reflective", [x, (y0 + y1) / 2, BOOM_PIVOT_Z_M],
                 bh / 2, (y1 - y0) / 2, bw / 2)
    boom.box("steel_painted", [x, -BOOM_TAIL_M / 2, BOOM_PIVOT_Z_M], bh / 2 + 0.01, BOOM_TAIL_M / 2, bw / 2 + 0.03)
    _rot_x(boom, BOOM_RAISED_DEG, BOOM_PIVOT_Z_M)
    for mat, (Vs, Ts, UVs) in boom.prims.items():
        for V, T, UV in zip(Vs, Ts, UVs):
            m.add(mat, V, T - int(T.min()), UV)
    m.tube("steel_painted", [dx / 2 - 0.02, 0, BOOM_PIVOT_Z_M], [x + bh / 2 + 0.02, 0, BOOM_PIVOT_Z_M], 0.05, None, 8)
    col.box("collision_steel", [0, 0, dz / 2], dx / 2, dy / 2, dz / 2)
    return m, m, col


def guide_post(style="u1a", side="right"):
    """Guide post beside the approach (Dz.U. 2025 poz. 1105 § 79 pkt 5: U-1a / U-1b). Styles:
    u1a        white post with a black band carrying the reflector - red on the right of the road, white on the left
               (UNVERIFIED appearance: Dz.U. 2019 poz. 2311 zał. 4 was not read);
    red_white  white post with red bands as on Mapillary 1832769196903759 at DW671 x line 38 (authored override
               `guide_post: red_white`)."""
    m, col = PP.Mesh(), PP.Mesh()
    hx, hy = U1_SECTION_M[0] / 2, U1_SECTION_M[1] / 2
    if style == "red_white":
        bands = (("paint_white_reflective", 0.0, 0.25), ("paint_ral3020", 0.25, 0.50),
                 ("paint_white_reflective", 0.50, 0.75), ("paint_ral3020", 0.75, 1.00))
    else:
        bands = (("paint_white_reflective", 0.0, 0.68), ("signal_backplate", 0.68, 0.90),
                 ("paint_white_reflective", 0.90, 1.00))
    for mat, f0, f1 in bands:
        z0, z1 = U1_H_M * f0 - (0.03 if f0 == 0.0 else 0.0), U1_H_M * f1
        m.box(mat, [0, 0, (z0 + z1) / 2], hx, hy, (z1 - z0) / 2)
    if style != "red_white":                                   # reflector on the face (+y: towards the driver)
        m.box("paint_ral3020" if side == "right" else "paint_white_reflective", [0, hy + 0.003, U1_H_M * 0.79],
              0.025, 0.003, 0.07)
    col.box("collision_steel", [0, 0, U1_H_M / 2], hx, hy, U1_H_M / 2)
    return m, m, col


def _vec(heading_deg):
    a = math.radians(heading_deg)
    return np.array([math.sin(a), math.cos(a)])            # compass degrees clockwise from north -> (E, N)


def proto_name(mk):
    """Prototype of one rail.json marker (None: no mesh for this kind)."""
    if mk["kind"] == "sign":
        if mk["code"] not in ("G-3", "G-4"):
            return None            # G-2 is a sign plate of the prop library (plate_G-2), see place(): no own mesh here
        return f"signal_rail_saltire_{mk['code'].replace('-', '').lower()}"
    if mk["kind"] == "guide_post":
        style = mk.get("style", "u1a")
        return f"signal_rail_guide_{style}" + ("" if style == "red_white" else "_" + mk.get("side", "right")[0])
    if mk["kind"] == "light":
        return "signal_rail_lamps"
    if mk["kind"] == "barrier":
        return f"signal_rail_barrier_{int(round(mk['boom_len_m'] * 2)) * 5:03d}"      # boom length in 0.5 m classes (dm)
    return None


def build(name, mk=None):
    if name.startswith("signal_rail_saltire_"):
        kw = {}
        if mk is not None:
            kw = {"arm_l": mk["arm_l_m"], "arm_w": mk["arm_w_m"], "arm_angle": mk["arm_angle_deg"], "bottom_z": mk["bottom_z_m"]}
        return saltire("G-4" if name.endswith("g4") else "G-3", **kw)
    if name == "signal_rail_lamps":
        return signal()
    if name == "signal_rail_lamps_bell":
        return signal(bell=True)
    if name.startswith("signal_rail_barrier_"):
        return barrier(int(name.rsplit("_", 1)[1]) / 10.0)
    if name.startswith("signal_rail_guide_"):
        if name.endswith("red_white"):
            return guide_post("red_white")
        return guide_post("u1a", "left" if name.endswith("_l") else "right")
    raise KeyError(name)


def saltire_top_bottom(mk):
    """(lower edge, top) of the cross of a G-3 / G-4 marker above the ground - as built by saltire()."""
    half = mk["arm_angle_deg"] / 2.0
    rise = mk["arm_l_m"] / 2 * math.sin(math.radians(half)) + mk["arm_w_m"] / 2 * math.cos(math.radians(half))
    drop = SALTIRE_G4_DROP_M if mk["code"] == "G-4" else 0.0
    return mk["bottom_z_m"], mk["bottom_z_m"] + 2 * rise + drop


def plate_stack(plates, bottom_z):
    """[(code, centre height above the post base)] of plates listed top first, stacked from `bottom_z` upwards with
    PLATE_GAP_M between them (as furniture.sign_assembly, for the plate shapes of ADR 0268), and the post height."""
    from roads import standards as S
    from . import rail_approach as RA
    from . import signs as SG
    out, z = [], float(bottom_z)
    for code in reversed(plates):
        shape, _ = SG.face(code)
        if shape == "rect":
            h = SG.RECT[code][1]
            out.append((code, z + h / 2))
        elif shape == "triangle_up":
            h = S.SIGN_SIZE["triangle"] * math.sqrt(3) / 2
            out.append((code, z + h / 3))                  # plate origin = centroid, 1/3 above the lower edge
        else:
            raise KeyError(f"plate_stack: shape {shape!r} of {code} not supported")
        z += h + RA.PLATE_GAP_M
    return out[::-1], z


def place(pl, plan, zroad_at, report, net=None, codes=None):
    """Instances of the crossing markers of `plan` (streetscape.rail.Plan) in the Placer `pl`: the devices at the
    crossing (ADR 0217 / 0223) and - with the road network `net` - the signs and guide posts of the approaches
    (ADR 0268, streetscape.rail_approach). `codes`: the set of sign-plate codes of the prop library (filled).
    Returns the count."""
    from roads import standards as S
    from . import rail_approach as RA
    from . import signs as SG
    from .furniture import yaw_of
    PROTOS.clear()
    codes = set() if codes is None else codes
    n = {}

    def put(name, mk, kind, ci, z=None, sz=1.0):
        zb = pl.add(name, (mk["e"], mk["n"]), yaw_of(_vec(mk["heading_deg"])), z=z, sz=sz,
                    src=f"rail:crossing:{ci}:{kind}")
        n[name] = n.get(name, 0) + 1
        return zb

    devices = [plan.markers(ci, c, zroad_at) for ci, c in enumerate(plan.crossings)]
    for ci, mks in enumerate(devices):
        rung = False
        bell = any(m["kind"] == "bell" for m in mks)
        base = {}                                              # (e, n) -> base height of the post / mast standing there
        cross = {(m["e"], m["n"]): m for m in mks if m["kind"] == "sign" and m["code"] in ("G-3", "G-4")}
        for mk in mks:
            name = proto_name(mk)
            if name is None:
                continue
            if name == "signal_rail_lamps" and bell and not rung and mk.get("side", "right") == "right":
                name, rung = "signal_rail_lamps_bell", True           # the bell rides the first right-hand signal mast
            if name not in PROTOS:
                PROTOS[name] = build(name, mk)
            base[(mk["e"], mk["n"])] = put(name, mk, mk["kind"], ci)
        for mk in mks:                                         # ADR 0223: G-2 "sieć pod napięciem" (§ 81 ust. 1)
            if mk["kind"] != "sign" or mk["code"] != "G-2":
                continue
            key = (mk["e"], mk["n"])
            zb = base.get(key)
            if zb is None:
                continue                                       # no mast / cross post here: nothing to hang it on
            h = SG.RECT["G-2"][1]
            if mk.get("mount") == "below_cross" and key in cross:
                top = saltire_top_bottom(cross[key])[0] - G2_GAP_UNDER_CROSS_M
            else:
                top = G2_TOP_UNDER_LAMPS_M
            put("plate_G-2", mk, "G-2", ci, z=zb + top - h / 2)
            codes.add("G-2")
    report["rail_crossing_devices"] = dict(sorted(n.items()))
    # ---- ADR 0268: approach signs (A-9 / A-10, board, G-1) and guide posts (U-1a)
    ap = RA.plan(plan, net, devices=[m for mks in devices for m in mks]) if net is not None else None
    if ap is not None:
        n0 = dict(n)
        for mk in ap["markers"]:
            ci = mk["crossing"]
            if mk["kind"] == "guide_post":
                name = proto_name(mk)
                if name not in PROTOS:
                    PROTOS[name] = build(name, mk)
                put(name, mk, "guide_post", ci)
                continue
            stack, top = plate_stack(mk["plates"], mk["bottom_z_m"] or S.SIGN_H_MIN)
            zb = put("sign_post", mk, "approach", ci)
            pl.items[-1]["sz"] = round(top + 0.05, 3)
            for code, zc in stack:
                put(f"plate_{code}", mk, "approach", ci, z=zb + zc)
                codes.add(code)
            pl.pts.setdefault("sign", []).append((mk["e"], mk["n"]))
        plan.report["approach"] = ap["markers"]
        plan.report["approach_rules"] = ap["rules"]
        plan.report["approach_outside_tile"] = ap["outside_tile"]
        report["rail_approach"] = {k: v - n0.get(k, 0) for k, v in sorted(n.items()) if v - n0.get(k, 0)}
    return sum(n.values())


def prototypes():
    return dict(PROTOS)
