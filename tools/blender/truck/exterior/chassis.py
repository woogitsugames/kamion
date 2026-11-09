"""TRAKT chassis, wheels and frame-mounted equipment (A3/A4).

Asymmetric like real EU tractors: fuel + AdBlue tanks on the left (driver side), aftertreatment (EATS) box
and battery box on the right. Wheels: forged-aluminium 22.5x9.00 discs; front ET +120 mm (disc outboard),
rear duals mounted back to back (outer wheel shows the deep dish). ET values WORKING_VALUE (class typical).
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import geom as G
from geom import (WB, WHEEL_Z, TYRE_R, FRONT_TRACK, REAR_TRACK, DUAL_SPACING, FIFTH_H, FIFTH_LEAD, REAR_OH,
                  CAB_BACK_Y, CAB_HALF_W, FRAME_HALF_W, FRAME_TOP, PCD_R, V, box, box_mm, cyl, rod, sphere, tube,
                  lathe, arch, extrude_poly, rrect, boolean, bevel, set_group)

Y_END = -WB - REAR_OH


# ---------------------------------------------------------------- tyre
def tyre_profile():
    """(r, x) from the inner bead to the outer bead for a 315/80 R22.5 (section height 252 mm)."""
    Ro = TYRE_R
    side_in = [(0.296, -0.108), (0.322, -0.132), (0.36, -0.149), (0.40, -0.1565), (0.44, -0.1575),
               (0.475, -0.153), (0.503, -0.143), (0.522, -0.131), (0.533, -0.119)]
    tread = [(Ro - 0.002, -0.112)]
    for c in (-0.072, -0.024, 0.024, 0.072):
        tread += [(Ro, c - 0.010), (Ro - 0.016, c - 0.005), (Ro - 0.016, c + 0.005), (Ro, c + 0.010)]
    tread += [(Ro - 0.002, 0.112)]
    side_out = [(r, -x) for r, x in reversed(side_in)]
    prof = side_in + tread + side_out
    s = [0.0]
    for (r0, x0), (r1, x1) in zip(prof, prof[1:]):
        s.append(s[-1] + math.hypot(r1 - r0, x1 - x0))
    v = [t / s[-1] for t in s]
    i0, i1 = len(side_in), len(side_in) + len(tread) - 1
    j0 = len(prof) - 1 - 7     # outer sidewall band r 0.322 .. 0.503
    j1 = len(prof) - 1 - 1
    return prof, v, (v[i0], v[i1]), (v[j0], v[j1])


def make_tyre_materials():
    import materials as M
    prof, v, vt, vs = tyre_profile()
    imgs = M.make_tread_images()
    ROUND = 2 * math.pi * TYRE_R
    for kind, pitch in (("steer", 0.105), ("drive", 0.12)):
        side = M.make_sidewall_image(kind)
        M.tyre_material(f"tyre_{kind}", kind, imgs[kind], side, vt, (vs[0], vs[1]), round(ROUND / pitch))


# ---------------------------------------------------------------- wheel
RIM_PROF = [(0.300, 0.112), (0.302, 0.124), (0.294, 0.128), (0.286, 0.121), (0.284, 0.100), (0.264, 0.082),
            (0.258, 0.050), (0.258, -0.050), (0.264, -0.082), (0.284, -0.100), (0.286, -0.121), (0.294, -0.128),
            (0.302, -0.124), (0.300, -0.112)]


def wheel(name, xc, y, out, et, tyre_mat, nuts=True, hub="front", seg=48):
    """One tyre + alloy rim. out: +1/-1 = direction of the visible face (x). et: disc offset from the rim
    centre towards `out` (m)."""
    c = V((xc, y, WHEEL_Z))
    prof, v, _, _ = tyre_profile()
    lathe(name + "_tyre", prof, c, tyre_mat, seg=seg, side=out, uv_v=v, sharp=60)
    inner = [(r - 0.010, x) for r, x in reversed(RIM_PROF)]
    lathe(name + "_rim", RIM_PROF + inner, c, "alu_wheel", seg=40, side=out, sharp=45)
    xd = et
    # dish: barrel -> disc
    sgn = 1 if et >= 0 else -1
    dish = [(0.259, sgn * 0.06), (0.250, sgn * 0.09), (0.236, xd - sgn * 0.004), (0.226, xd + sgn * 0.008),
            (0.244, sgn * 0.085), (0.250, sgn * 0.055)]
    if abs(et) > 0.09:
        lathe(name + "_dish", dish, c, "alu_wheel", seg=48, side=out, sharp=40)
    disc = lathe(name + "_disc", [(0.112, xd - 0.011), (0.236, xd - 0.011), (0.236, xd + 0.011),
                                  (0.112, xd + 0.011)], c, "alu_wheel", seg=40, side=out, sharp=40, closed_ends=False)
    cutters = []
    for k in range(10):
        a = 2 * math.pi * (k + 0.5) / 10
        cutters.append(cyl(f"{name}_hh{k}", (xc + out * xd, y + 0.200 * math.cos(a), WHEEL_Z + 0.200 * math.sin(a)),
                           0.028, 0.06, "alu_wheel", seg=16))
    boolean(disc, cutters)
    xf = xc + out * (xd + 0.011)   # disc outer face
    if nuts:
        for k in range(10):
            a = 2 * math.pi * k / 10
            p = (xf + out * 0.016, y + PCD_R * math.cos(a), WHEEL_Z + PCD_R * math.sin(a))
            cyl(f"{name}_nut{k}", p, 0.0175, 0.032, "steel", seg=6, axis="X")
            cyl(f"{name}_washer{k}", (xf + out * 0.002, p[1], p[2]), 0.022, 0.004, "steel", seg=12)
    if hub == "front":
        lathe(name + "_hubcap", [(0.105, 0.0), (0.105, 0.035), (0.095, 0.060), (0.06, 0.085), (0.0, 0.095)],
              V((xf, y, WHEEL_Z)), "satin_alu", seg=40, side=out, sharp=40)
    elif hub == "rear":
        lathe(name + "_hub", [(0.118, 0.0), (0.118, 0.09), (0.125, 0.10), (0.125, 0.135), (0.10, 0.16),
                              (0.07, 0.175), (0.0, 0.178)], V((xf, y, WHEEL_Z)), "steel", seg=40, side=out, sharp=40)
        for k in range(8):
            a = 2 * math.pi * k / 8
            cyl(f"{name}_hubbolt{k}", (xf + out * 0.138, y + 0.10 * math.cos(a), WHEEL_Z + 0.10 * math.sin(a)),
                0.009, 0.016, "steel", seg=6, axis="X")


def wheels():
    set_group("wheels")
    fx = FRONT_TRACK / 2
    for s in (-1, 1):
        sd = "L" if s < 0 else "R"
        wheel(f"wheel_F{sd}", s * fx, 0.0, s, 0.120, "tyre_steer", hub="front")
        half = DUAL_SPACING / 2
        wheel(f"wheel_R{sd}o", s * (REAR_TRACK / 2 + half), -WB, s, -half + 0.011, "tyre_drive", hub="rear")
        wheel(f"wheel_R{sd}i", s * (REAR_TRACK / 2 - half), -WB, s, half - 0.011, "tyre_drive", nuts=False, hub=None,
              seg=32)


# ---------------------------------------------------------------- frame, axles, suspension, driveline
def frame_and_axles():
    set_group("frame")
    for s in (-1, 1):
        x0, x1 = s * (FRAME_HALF_W - 0.08), s * FRAME_HALF_W
        box_mm(f"frame_rail_{s}", x0, x1, Y_END, 1.20, FRAME_TOP - 0.29, FRAME_TOP, "chassis", bev=0.004)
        for y in (-1.20, -2.30, -3.05, -3.85, Y_END + 0.06):  # bolt rows at the crossmembers
            for dz in (-0.06, -0.12, -0.18, -0.24):
                for dy in (-0.045, 0.045):
                    cyl(f"frame_bolt_{s}_{y}_{dz}_{dy}", (x1 + s * 0.004, y + dy, FRAME_TOP + dz), 0.011, 0.012,
                        "steel", seg=6, axis="X")
        # front frame horns: bumper brackets + cab tilt pivot brackets
        box_mm(f"frame_horn_{s}", s * 0.36, s * 0.44, 1.18, 1.46, 0.95, 1.12, "chassis", bev=0.01)
        cyl(f"cab_pivot_{s}", (s * 0.40, 1.44, 1.19), 0.035, 0.12, "steel", axis="X", seg=16)
        box_mm(f"cab_pivot_brk_{s}", s * 0.37, s * 0.43, 1.40, 1.48, 1.10, 1.20, "chassis", bev=0.006)
    for y in (-1.20, -2.30, -3.05, -3.85, Y_END + 0.06):
        box_mm(f"frame_cross_{y}", -FRAME_HALF_W + 0.08, FRAME_HALF_W - 0.08, y - 0.05, y + 0.05,
               FRAME_TOP - 0.24, FRAME_TOP - 0.04, "chassis")
    box_mm("frame_front_cross", -0.44, 0.44, 1.12, 1.20, 0.80, 1.02, "chassis", bev=0.01)
    # front axle: I-beam with drop, kingpins, brake discs and calipers, tie rod, drag link, steering box
    fx = FRONT_TRACK / 2
    box_mm("front_axle", -0.62, 0.62, -0.05, 0.05, 0.40, 0.50, "chassis", bev=0.012)
    for s in (-1, 1):
        rod(f"axle_arm_{s}", (s * 0.60, 0, 0.45), (s * (fx - 0.17), 0, WHEEL_Z), 0.05, "chassis")
        cyl(f"kingpin_{s}", (s * (fx - 0.17), 0, WHEEL_Z), 0.06, 0.22, "chassis", axis="Z", seg=16)
        cyl(f"brake_disc_F_{s}", (s * (fx - 0.10), 0, WHEEL_Z), 0.205, 0.045, "steel", seg=40)
        box(f"caliper_F_{s}", (s * (fx - 0.10), -0.14, WHEEL_Z + 0.12), (0.12, 0.10, 0.18), "chassis", bev=0.015,
            rot=Matrix.Rotation(math.radians(-40), 3, "X"))
        cyl(f"brake_chamber_F_{s}", (s * (fx - 0.24), -0.20, WHEEL_Z + 0.20), 0.075, 0.12, "chassis", axis="X",
            seg=20, bev=0.01)
        # parabolic leaf spring (2 leaves) + shackle + damper
        pts = [V((s * 0.40, -0.72, 0.70)), V((s * 0.40, -0.35, 0.62)), V((s * 0.40, 0.0, 0.57)),
               V((s * 0.40, 0.35, 0.62)), V((s * 0.40, 0.72, 0.70))]
        for k, dz in enumerate((0.0, -0.03)):
            tube(f"leaf_{s}_{k}", [p + V((0, 0, dz)) for p in pts], 0.014, "chassis", seg=8)
        rod(f"damper_F_{s}", (s * 0.48, 0.18, 0.52), (s * 0.48, 0.30, 0.92), 0.03, "chassis")
        box_mm(f"spring_hanger_{s}", s * 0.36, s * 0.44, 0.68, 0.78, 0.62, 0.72, "chassis")
    rod("tie_rod", (-(fx - 0.22), -0.25, WHEEL_Z - 0.02), (fx - 0.22, -0.25, WHEEL_Z - 0.02), 0.022, "chassis")
    box_mm("steering_box", -0.58, -0.44, 0.90, 1.12, 0.78, 0.96, "chassis", bev=0.02)
    rod("drag_link", (-0.50, 0.95, 0.70), (-(fx - 0.25), 0.15, WHEEL_Z + 0.12), 0.022, "chassis")
    # engine, gearbox, propshaft, radiator stack
    box_mm("engine", -0.40, 0.40, -0.95, 0.75, 0.58, 1.12, "chassis", bev=0.04, seg=2)
    box_mm("oil_pan", -0.28, 0.28, -0.70, 0.40, 0.44, 0.60, "chassis", bev=0.03)
    box_mm("radiator", -0.48, 0.48, 1.00, 1.10, 0.62, 1.20, "chassis", bev=0.01)
    box_mm("gearbox", -0.24, 0.24, -1.85, -0.95, 0.62, 0.96, "chassis", bev=0.04)
    rod("propshaft", (0, -1.85, 0.74), (0, -WB + 0.30, WHEEL_Z + 0.03), 0.055, "steel")
    # rear axle: housing, differential, brake chambers, 4 air bellows, trailing arms, dampers
    y = -WB
    rod("axle_rear", (-(REAR_TRACK / 2 - 0.05), y, WHEEL_Z), ((REAR_TRACK / 2 - 0.05), y, WHEEL_Z), 0.075, "chassis",
        seg=20)
    G.sphere("diff", (0, y, WHEEL_Z), 0.25, "chassis", scale=(0.85, 1.0, 0.95))
    cyl("diff_nose", (0, y + 0.28, WHEEL_Z + 0.02), 0.11, 0.18, "chassis", axis="Y", seg=20)
    for s in (-1, 1):
        cyl(f"brake_chamber_R_{s}", (s * 0.58, y + 0.22, WHEEL_Z + 0.12), 0.085, 0.20, "chassis", axis="X", seg=20,
            bev=0.01)
        box_mm(f"trailing_arm_{s}", s * 0.46, s * 0.58, y - 0.55, y + 0.95, 0.46, 0.58, "chassis", bev=0.02)
        for dy in (-0.45, 0.45):
            cyl(f"bellow_{s}_{dy}", (s * 0.54, y + dy, 0.75), 0.13, 0.26, "rubber", axis="Z", seg=24, bev=0.04, bseg=3)
            cyl(f"bellow_plate_{s}_{dy}", (s * 0.54, y + dy, 0.895), 0.12, 0.03, "chassis", axis="Z", seg=24)
        rod(f"damper_R_{s}", (s * 0.66, y - 0.15, 0.52), (s * 0.48, y - 0.25, 0.88), 0.03, "chassis")
    rod("anti_roll_bar", (-0.5, y - 0.6, 0.62), (0.5, y - 0.6, 0.62), 0.025, "chassis")


# ---------------------------------------------------------------- tanks, EATS, batteries, air
def equipment():
    set_group("frame")
    xo = -(FRAME_HALF_W + 0.02)
    # fuel tank (aluminium, left), 600 x 620 section, ~1.1 m long (~400 l WORKING_VALUE)
    w, h, y0, y1, zc = 0.60, 0.62, -2.22, -1.12, 0.73
    xc = xo - w / 2
    sec = [(xc + px, zc + pz) for px, pz in rrect(w, h, 0.13, 5)]
    extrude_poly("fuel_tank", sec, y1 - y0, "alu_brushed", plane="XZ", origin=(0, y0, 0), bev=0.02, bseg=3)
    for k, yb in enumerate((y0 + 0.15, y1 - 0.15)):
        sec2 = [(xc + px, zc + pz) for px, pz in rrect(w + 0.012, h + 0.012, 0.135, 5)]
        extrude_poly(f"tank_strap{k}", sec2, 0.05, "chassis", plane="XZ", origin=(0, yb - 0.025, 0))
        box_mm(f"tank_saddle{k}", xo, xo - 0.05, yb - 0.04, yb + 0.04, zc - 0.25, FRAME_TOP - 0.05, "chassis")
    for k, yb in enumerate((y0 + 0.40, y1 - 0.40)):  # pressed beads
        sec3 = [(xc + px, zc + pz) for px, pz in rrect(w + 0.006, h + 0.006, 0.132, 5)]
        extrude_poly(f"tank_bead{k}", sec3, 0.012, "alu_brushed", plane="XZ", origin=(0, yb, 0))
    cyl("fuel_neck", (xc - 0.18, y1 - 0.15, zc + h / 2 + 0.02), 0.045, 0.05, "alu_brushed", axis="Z", seg=20)
    cyl("fuel_cap", (xc - 0.18, y1 - 0.15, zc + h / 2 + 0.055), 0.055, 0.03, "chassis", axis="Z", seg=24, bev=0.006)
    # AdBlue tank behind it, black plastic with a blue cap
    w2, h2, a0, a1 = 0.44, 0.50, -2.66, -2.28
    xc2 = xo - w2 / 2
    sec = [(xc2 + px, 0.70 + pz) for px, pz in rrect(w2, h2, 0.08, 4)]
    extrude_poly("adblue_tank", sec, a1 - a0, "plastic", plane="XZ", origin=(0, a0, 0), bev=0.01)
    cyl("adblue_cap", (xc2 - 0.10, -2.40, 0.97), 0.045, 0.035, "adblue_blue", axis="Z", seg=20, bev=0.005)
    # right: aftertreatment box (DPF+SCR) with perforated heat shield and down-angled outlet
    xi = FRAME_HALF_W + 0.02
    box_mm("eats_box", xi, 1.17, -1.95, -1.05, 0.44, 1.04, "chassis", bev=0.05, seg=3)
    box_mm("eats_shield", 1.17, 1.185, -1.90, -1.10, 0.50, 0.98, "perforated", bev=0.01)
    for z in (0.52, 0.96):
        box_mm(f"eats_band_{z}", 1.165, 1.19, -1.92, -1.08, z - 0.012, z + 0.012, "steel", bev=0.003)
    rod("exhaust_out", (1.00, -1.92, 0.50), (1.12, -2.06, 0.36), 0.05, "steel", seg=16)
    cyl("exhaust_tip", (1.125, -2.07, 0.35), 0.054, 0.02, "chassis", axis="Z", seg=16)
    # battery box with lid and latches
    box_mm("battery_box", xi, 1.10, -2.70, -2.02, 0.56, 1.00, "plastic", bev=0.02)
    box_mm("battery_lid_gap", 1.10, 1.103, -2.68, -2.04, 0.94, 0.945, "gap")
    for y in (-2.20, -2.52):
        box_mm(f"battery_latch_{y}", 1.10, 1.115, y - 0.03, y + 0.03, 0.84, 0.95, "steel", bev=0.004)
    # air tanks (across, under the frame)
    for y in (-2.80, -3.00):
        cyl(f"air_tank_{y}", (0, y, 0.66), 0.105, 0.66, "alu_brushed", axis="X", seg=24, bev=0.04, bseg=3)
        for x in (-0.2, 0.2):
            cyl(f"air_tank_strap_{y}_{x}", (x, y, 0.66), 0.11, 0.03, "chassis", axis="X", seg=24)
    # low side fairings under tanks/boxes, with side marker lamps (amber)
    for s in (-1, 1):
        box_mm(f"side_fairing_{s}", s * (CAB_HALF_W - 0.03), s * (CAB_HALF_W - 0.01), -3.02, CAB_BACK_Y - 0.01,
               0.36, 0.48, "plastic", bev=0.006)
        for y in (-1.55, -2.60):
            box_mm(f"side_marker_{s}_{y}", s * (CAB_HALF_W - 0.012), s * (CAB_HALF_W + 0.002), y - 0.05, y + 0.05,
                   0.41, 0.44, "lens_amber", bev=0.003)
        for y in (-1.5, -2.5):
            box_mm(f"fairing_brk_{s}_{y}", s * FRAME_HALF_W, s * (CAB_HALF_W - 0.03), y - 0.02, y + 0.02, 0.40,
                   0.44, "chassis")
    # catwalk with checker plate + access ladder on the left behind the cab steps
    box_mm("catwalk", -0.46, 0.46, -1.72, -1.02, FRAME_TOP + 0.02, FRAME_TOP + 0.034, "checker", bev=0.004)
    for y in (-1.06, -1.68):
        box_mm(f"catwalk_brk_{y}", -0.46, 0.46, y - 0.02, y + 0.02, FRAME_TOP, FRAME_TOP + 0.02, "chassis")
    for k, z in enumerate((0.62, 0.84)):
        box_mm(f"catwalk_step{k}", -1.08, -0.82, -1.10, -0.98, z, z + 0.02, "checker", bev=0.003)
    rod("catwalk_ladder_a", (-1.08, -1.04, 0.58), (-1.08, -1.04, 0.98), 0.012, "chassis")
    rod("catwalk_ladder_b", (-0.82, -1.04, 0.58), (-0.82, -1.04, 0.98), 0.012, "chassis")
    set_group("cab")   # grab handle is on the cab back corner
    tube("catwalk_grab", [(-1.18, CAB_BACK_Y - 0.01, 1.35), (-1.18, CAB_BACK_Y - 0.06, 1.40),
                          (-1.18, CAB_BACK_Y - 0.06, 2.10), (-1.18, CAB_BACK_Y - 0.01, 2.15)], 0.014, "plastic_satin")
    set_group("frame")


# ---------------------------------------------------------------- fifth wheel, couplings, rear end
def fifth_wheel_and_rear():
    set_group("frame")
    fy = -WB + FIFTH_LEAD
    top = FIFTH_H
    # plate outline (plan): rounded front, two horns and a V throat at the rear
    pts = []
    for i in range(17):
        a = math.radians(180 - 180 * i / 16)
        pts.append((0.45 * math.cos(a), 0.05 + 0.38 * math.sin(a)))
    pts += [(0.45, -0.30), (0.40, -0.40), (0.16, -0.40), (0.04, -0.06), (-0.04, -0.06), (-0.16, -0.40),
            (-0.40, -0.40), (-0.45, -0.30)]
    pts = [(x, fy + y) for x, y in pts]
    bm = bmesh.new()
    vb = [bm.verts.new((x, y, top - 0.055)) for x, y in pts]
    vt = [bm.verts.new((x, y, top)) for x, y in pts]
    n = len(pts)
    bm.faces.new(vb[::-1])
    bm.faces.new(vt)
    for i in range(n):
        bm.faces.new((vb[i], vb[(i + 1) % n], vt[(i + 1) % n], vt[i]))
    bmesh.ops.triangulate(bm, faces=[f for f in bm.faces if len(f.verts) > 4])
    bevel(G.obj_from_bm("fifth_plate", bm, "steel", sharp=40), 0.008, 2)
    # grease film on top (two lubrication grooves read via gaps)
    bm = bmesh.new()
    inner = [(x * 0.96 + (1 - 0.96) * 0, fy + (y - fy) * 0.96) for x, y in pts]
    vg = [bm.verts.new((x, y, top + 0.0015)) for x, y in inner]
    bm.faces.new(vg)
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    G.obj_from_bm("fifth_grease", bm, "grease", sharp=80)
    for x in (-0.25, 0.25):
        box_mm(f"fifth_groove_{x}", x - 0.006, x + 0.006, fy - 0.20, fy + 0.30, top + 0.0015, top + 0.003, "gap")
    for s in (-1, 1):
        box_mm(f"fifth_bracket_{s}", s * 0.30, s * 0.46, fy - 0.15, fy + 0.15, FRAME_TOP + 0.01, top - 0.055,
               "chassis", bev=0.01)
        cyl(f"fifth_pin_{s}", (s * 0.38, fy, top - 0.09), 0.04, 0.20, "steel", axis="X", seg=16)
        box_mm(f"fifth_mount_{s}", s * 0.30, s * (FRAME_HALF_W + 0.01), fy - 0.30, fy + 0.30, FRAME_TOP,
               FRAME_TOP + 0.015, "chassis")
    box_mm("fifth_lock", -0.10, 0.10, fy - 0.12, fy + 0.10, top - 0.13, top - 0.055, "chassis", bev=0.01)
    tube("fifth_handle", [(-0.10, fy - 0.02, top - 0.10), (-0.52, fy - 0.06, top - 0.11),
                          (-0.60, fy - 0.06, top - 0.08), (-0.60, fy + 0.04, top - 0.08)], 0.012, "steel")
    cyl("fifth_handle_grip", (-0.60, fy - 0.01, top - 0.08), 0.018, 0.10, "plastic_satin", axis="Y", seg=12)
    # gooseneck holder for the coiled lines
    gy = -1.78
    tube("gooseneck", [(0, gy, FRAME_TOP + 0.02), (0, gy, 1.80), (0, gy + 0.10, 1.95), (0, gy + 0.25, 1.98)],
         0.03, "chassis", seg=12)
    box_mm("gooseneck_rack", -0.32, 0.32, gy + 0.20, gy + 0.30, 1.94, 1.99, "chassis", bev=0.008)
    for k, (x, m_) in enumerate(((-0.24, "coupling_red"), (-0.12, "coupling_yellow"), (0.08, "plastic"),
                                 (0.22, "plastic"))):
        coil(f"coil{k}", (x, CAB_BACK_Y - 0.12, 1.41), (x * 0.9, gy + 0.25, 1.96), m_ if k < 2 else "plastic")
        cyl(f"coil_head{k}", (x * 0.9, gy + 0.25, 2.01), 0.035, 0.06, m_ if k < 2 else "plastic_satin", axis="Z",
            seg=16)
    # rear mudguards over the duals (3-piece), mudflaps with brackets
    for s in (-1, 1):
        x0, x1 = s * 0.56, s * 1.27
        arch(f"rear_guard_{s}", -WB, WHEEL_Z, 0.60, 0.613, x0, x1, 28, 155, "plastic", n=24)
        arch(f"rear_guard_lip_{s}", -WB, WHEEL_Z, 0.60, 0.64, x1 - s * 0.012, x1, 28, 155, "plastic", n=24)
        box_mm(f"mudflap_{s}", x0, x1, -WB - 0.66, -WB - 0.645, 0.20, 0.86, "rubber", bev=0.004)
        for k in range(6):
            box_mm(f"mudflap_rib_{s}_{k}", x0 + s * 0.05, x1 - s * 0.05, -WB - 0.668, -WB - 0.66, 0.30 + k * 0.08,
                   0.33 + k * 0.08, "rubber")
        tube(f"guard_arm_{s}", [(s * FRAME_HALF_W, -WB + 0.05, 0.80), (s * 0.70, -WB + 0.05, 1.05),
                                (s * 0.80, -WB, 1.10)], 0.022, "chassis")
        tube(f"flap_arm_{s}", [(s * FRAME_HALF_W, -WB - 0.62, 0.80), (s * 0.95, -WB - 0.64, 0.84)], 0.02, "chassis")
        # rear combination lamps on brackets at the frame end
        box_mm(f"rear_lamp_brk_{s}", s * 0.42, s * 1.18, Y_END + 0.04, Y_END + 0.12, 0.78, 0.82, "chassis")
        box_mm(f"rear_lamp_{s}", s * 0.74, s * 1.18, Y_END - 0.02, Y_END + 0.06, 0.74, 0.90, "plastic_satin",
               bev=0.01)
        for k, (a, b_, m_) in enumerate(((0.76, 0.92, "lens_amber"), (0.92, 1.08, "lens_red"),
                                         (1.08, 1.16, "lens_clear"))):
            box_mm(f"rear_lens_{s}_{k}", s * a, s * b_, Y_END - 0.026, Y_END - 0.016, 0.755, 0.885, m_, bev=0.003)
    box_mm("rear_plate", 0.48, 0.70, Y_END - 0.03, Y_END - 0.02, 0.62, 0.734, "plate")
    box_mm("trailer_socket_brk", -0.20, 0.20, Y_END - 0.01, Y_END + 0.02, 0.86, 0.94, "chassis")


def coil(name, p0, p1, m, r=0.042, turns=10):
    cu = bpy.data.curves.new(name, "CURVE")
    cu.dimensions = "3D"
    cu.bevel_depth = 0.0075
    cu.bevel_resolution = 0
    sp = cu.splines.new("POLY")
    p0, p1 = Vector(p0), Vector(p1)
    ax = p1 - p0
    u = ax.orthogonal().normalized()
    v = ax.normalized().cross(u)
    n = turns * 9
    sp.points.add(n)
    for i in range(n + 1):
        t = i / n
        a = 2 * math.pi * turns * t
        sag = Vector((0, 0, -0.30 * math.sin(math.pi * t)))
        rr = r if 0.08 < t < 0.92 else r * 0.3
        p = p0 + ax * t + (u * math.cos(a) + v * math.sin(a)) * rr + sag
        sp.points[i].co = (*p, 1)
    ob = bpy.data.objects.new(name, cu)
    cu.materials.append(G.mat(m))
    return G.link(ob)


def build_all():
    frame_and_axles()
    equipment()
    fifth_wheel_and_rear()
    wheels()
