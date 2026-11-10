"""Curtainsider semi-trailer 13.6 m, tridem (fictional, no brand) - source geometry + authoring materials.

Frame (Blender): 1 unit = 1 m, Z up, +Y forward, +X right (kerb side), origin = ground below the kingpin
(= physics trailer frame, docs/VEHICLE_REFERENCE_DATA.md "Semi-trailer"). Unity = (x, z, y).
Every dimension shared with physics comes from art-source/truck/dims.json (trailer_* keys, ADR 0014).

Built from code only (trailer_export.py calls build()). Each object carries:
  ob["part"]  rig part (CHASSIS, CURTAIN_L/R, DOOR_RL/RR, WHEEL_1L..3R, LEG_L/R, CRANK, MUDFLAP_L/R)
  ob["group"] logical group (frame, body, curtain, wheels, lamps, gear, rear)
High-detail curtain sheets (normal-map source only) are tagged ob["bake_only"] = True.
"""
import math
import os
import random
import sys

import bmesh
import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
EXT = os.path.join(HERE, "..", "exterior")
sys.path.insert(0, os.path.abspath(EXT))
import geom as G  # noqa: E402
import materials as M  # noqa: E402
from geom import V, cyl, rod, tube, lathe, extrude_poly, bevel, boolean  # noqa: E402

D = G.D
# ---------------------------------------------------------------- dimensions (dims.json, trailer_* keys)
LEN = D("trailer_body_length_m")             # 13.6
Y_FRONT = D("trailer_kingpin_to_front_m")    # 1.60 front wall outer face
Y_REAR = Y_FRONT - LEN                       # -12.00 rear end
HW = D("max_width_m") / 2                    # 1.275
ROOF = D("trailer_overall_height_m")         # 4.00
FLOOR = D("trailer_floor_height_m")          # 1.30
KP_H = D("fifth_wheel_height_m")             # 1.15 = kingpin height (ADR 0014)
AXLES = D("trailer_axle_z_m")                # [-6.39, -7.70, -9.01]
TRACK = D("trailer_track_m")                 # 2.04
WC = D("trailer_wheel_centre_m")             # 0.515
TYRE_R = D("trailer_tyre_diameter_m") / 2    # 0.536
TYRE_W = D("trailer_tyre_section_width_m")   # 0.385
LG = D("trailer_landing_gear_m")             # {z, half_track, raised_foot_y, lowered_foot_y}
PCD_R = D("wheel_pcd_m") / 2

# art-only working values (no physics counterpart), class-typical EU curtainsider
BEAM_X = 0.50            # main I-beam web centre (beam spacing 1.0 m)
RAIL_OUT = 1.248         # side rail outer face
CURT_X = 1.250           # curtain base plane (hangs outside the side rail)
CURT_Z0, CURT_Z1 = 1.205, 3.88
HEM_TOP = 1.29           # top of the bottom hem / buckle strap entry
TOPRAIL_Z = 3.88         # underside of the top rail (curtain track); clear side height = 2.58 m
POST_IN = 1.135          # rear portal post inner edge (door opening half width)
DOOR_Z0, DOOR_Z1 = 1.335, 3.865
DOOR_FACE = Y_REAR + 0.025
N_STRAPS = 23            # curtain straps per side (22 bays of ~0.6 m)
STRAP_Y0, STRAP_Y1 = Y_FRONT - 0.22, Y_REAR + 0.24
CURT_Y0, CURT_Y1 = Y_FRONT - 0.075, Y_REAR + 0.10
RNG = random.Random(1306)

STATE = {"part": "CHASSIS"}


def box_mm(name, x0, x1, y0, y1, z0, z1, m, bev=0.0, seg=2):
    """geom.box_mm (2-segment chamfer, harden normals: catches a highlight on every edge)."""
    return G.box_mm(name, x0, x1, y0, y1, z0, z1, m, bev, seg)


def part(name, group=None):
    """Switch the current rig part; everything created so far without a part belongs to the previous one."""
    for o in bpy.data.objects:
        if "part" not in o:
            o["part"] = STATE["part"]
    STATE["part"] = name
    if group:
        G.set_group(group)


def tag_new(before):
    for o in bpy.data.objects:
        if o.name not in before and "part" not in o:
            o["part"] = STATE["part"]


def smooth01(e0, e1, x):
    t = min(max((x - e0) / (e1 - e0), 0.0), 1.0)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- authoring materials
def _grime(nt, b, rgb, rough, h0=1.2, amount=0.6, film=0.0, streak=0.0, back=0.0, spray=0.0, cav=0.8,
           dust=(0.15, 0.135, 0.11), band=0.0, band_z0=0.0):
    """M.grime + tyre spray over the tridem (y between the first-axle front and the last-axle rear, low z):
    the spray term is added to the same grime factor so the A6 bake (labels grime_mix / grime_rough) sees it."""
    f = M.grime(nt, b, rgb, rough, h0=h0, amount=amount, film=film, streak=streak, back=back, cav=cav, dust=dust)
    if band > 0:
        f = _road_band(nt, band, band_z0)
    if spray <= 0:
        return f
    mix = next(n for n in nt.nodes if n.label == "grime_mix")
    rr = next(n for n in nt.nodes if n.label == "grime_rough")
    geo = M.N(nt, "ShaderNodeNewGeometry")
    sep = M.N(nt, "ShaderNodeSeparateXYZ")
    M.L(nt, geo.outputs["Position"], sep.inputs[0])
    y = sep.outputs[1]
    y0, y1 = AXLES[0] + 0.9, AXLES[-1] - 1.2
    inside = M.math_node(nt, "MULTIPLY", M.math_node(nt, "DIVIDE", M.math_node(nt, "SUBTRACT", y0, y), 0.8,
                                                     clamp=True),
                         M.math_node(nt, "DIVIDE", M.math_node(nt, "SUBTRACT", y, y1), 1.6, clamp=True))
    hz = M.math_node(nt, "DIVIDE", M.math_node(nt, "SUBTRACT", 2.35, sep.outputs[2]), 1.25, clamp=True)
    n = M.N(nt, "ShaderNodeTexNoise", Scale=5.0, Detail=8.0, Roughness=0.62)
    M.L(nt, geo.outputs["Position"], n.inputs["Vector"])
    nm = M.N(nt, "ShaderNodeMapRange", **{"From Min": 0.32, "From Max": 0.62, "To Min": 0.3})
    M.L(nt, n.outputs["Fac"], nm.inputs["Value"])
    s = M.math_node(nt, "MULTIPLY", M.math_node(nt, "MULTIPLY", inside, hz),
                    M.math_node(nt, "MULTIPLY", nm.outputs[0], spray * M.PARAMS["dirt"]))
    old = mix.inputs[0].links[0].from_socket
    tot = M.math_node(nt, "ADD", old, s, clamp=True)
    M.L(nt, tot, mix.inputs[0])
    # roughness: grime_rough = f * 0.35 + rough; add the spray share the same way
    r_in = rr.inputs[0].links[0].from_socket if rr.inputs[0].links else None
    if r_in is not None:
        M.L(nt, M.math_node(nt, "ADD", r_in, M.math_node(nt, "MULTIPLY", s, 0.35)), rr.inputs[0])
    return tot


def _road_band(nt, band, z0):
    """Road film on the lowest 0.6 m of a surface that starts at z0 (curtain hem): the spray mist from the tractor
    drive axle and the own tridem settles as a soft band with an uneven upper edge, streaky along y (airflow),
    denser towards the rear (wake). Added to the grime factor like the spray term (the A6 bake sees it)."""
    mix = next(n for n in nt.nodes if n.label == "grime_mix")
    rr = next(n for n in nt.nodes if n.label == "grime_rough")
    geo = M.N(nt, "ShaderNodeNewGeometry")
    sep = M.N(nt, "ShaderNodeSeparateXYZ")
    M.L(nt, geo.outputs["Position"], sep.inputs[0])
    sc = M.N(nt, "ShaderNodeVectorMath", _operation="MULTIPLY")
    sc.inputs[1].default_value = (3.0, 0.35, 7.0)          # long along y (airflow), tight in z
    M.L(nt, geo.outputs["Position"], sc.inputs[0])
    n = M.N(nt, "ShaderNodeTexNoise", Scale=2.2, Detail=10.0, Roughness=0.68)
    M.L(nt, sc.outputs[0], n.inputs["Vector"])
    top = M.math_node(nt, "ADD", z0 + 0.30, M.math_node(nt, "MULTIPLY", n.outputs["Fac"], 0.45))
    hz = M.math_node(nt, "DIVIDE", M.math_node(nt, "SUBTRACT", top, sep.outputs[2]), 0.45, clamp=True)
    hz = M.math_node(nt, "POWER", hz, 1.6)
    rw = M.math_node(nt, "ADD", 0.45, M.math_node(nt, "MULTIPLY", M.math_node(
        nt, "DIVIDE", M.math_node(nt, "SUBTRACT", Y_FRONT, sep.outputs[1]), LEN, clamp=True), 0.55))
    n2 = M.N(nt, "ShaderNodeTexNoise", Scale=11.0, Detail=8.0, Roughness=0.62)
    M.L(nt, geo.outputs["Position"], n2.inputs["Vector"])
    m2 = M.N(nt, "ShaderNodeMapRange", **{"From Min": 0.30, "From Max": 0.66, "To Min": 0.35})
    M.L(nt, n2.outputs["Fac"], m2.inputs["Value"])
    s = M.math_node(nt, "MULTIPLY", M.math_node(nt, "MULTIPLY", hz, rw),
                    M.math_node(nt, "MULTIPLY", m2.outputs[0], band * M.PARAMS["dirt"]))
    old = mix.inputs[0].links[0].from_socket
    tot = M.math_node(nt, "ADD", old, s, clamp=True)
    M.L(nt, tot, mix.inputs[0])
    r_in = rr.inputs[0].links[0].from_socket if rr.inputs[0].links else None
    if r_in is not None:
        M.L(nt, M.math_node(nt, "ADD", r_in, M.math_node(nt, "MULTIPLY", s, 0.30)), rr.inputs[0])
    return tot


# r10 (ADR 0083): fleet graphic on the curtain without any name or logo - a broad diagonal band and a pinstripe left in
# the untinted fabric white (tint mask 0), so every curtain colour of the game gets a two-tone livery from one bake.
# (u = distance from the front edge minus 0.8 x height above the hem; both sides share the same y, so the band leans
# back on both.) LIVERY_BAND = False restores the plain r9 curtain. WORKING_VALUE (art direction, owner may veto).
LIVERY_BAND = True
LIVERY_BANDS = ((1.00, 2.60), (2.95, 3.22))


def _livery_mask(nt):
    N, mn = M.N, M.math_node
    geo = N(nt, "ShaderNodeNewGeometry")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    M.L(nt, geo.outputs["Position"], sep.inputs[0])
    u = mn(nt, "SUBTRACT", mn(nt, "SUBTRACT", Y_FRONT, sep.outputs[1]),
           mn(nt, "MULTIPLY", mn(nt, "SUBTRACT", sep.outputs[2], CURT_Z0), 0.8))
    w = 0.010
    tot = None
    for a, b in LIVERY_BANDS:
        t = mn(nt, "MULTIPLY", mn(nt, "DIVIDE", mn(nt, "SUBTRACT", u, a), w, clamp=True),
               mn(nt, "DIVIDE", mn(nt, "SUBTRACT", b, u), w, clamp=True))
        tot = t if tot is None else mn(nt, "MAXIMUM", tot, t)
    out = nt.nodes.new("ShaderNodeMath")
    out.operation = "SUBTRACT"
    out.label = "tint_mask"
    out.inputs[0].default_value = 1.0
    M.L(nt, tot, out.inputs[1])


ROOF_OWN_COLOUR = True
# r2 had 0.62: clipped to white through the D23 curve in the chase view (roof luma 100 %); WORKING_VALUE
ROOF_RGB = (0.36, 0.365, 0.37)
ROOF_BOWS = 18              # = top_rails_and_roof nb


def _roof_stains(nt, amount=1.0):
    """Dirt on the roof sheet: pooled in the sag between two bows (strongest mid-bay, fading to the edges where the
    sheet runs off over the rail), a dusty film overall and darker run-off along both edges. Added to the grime
    factor like the spray term (the bake labels grime_mix / grime_rough see it)."""
    mn, N = M.math_node, M.N
    mix = next(n for n in nt.nodes if n.label == "grime_mix")
    rr = next(n for n in nt.nodes if n.label == "grime_rough")
    geo = N(nt, "ShaderNodeNewGeometry")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    M.L(nt, geo.outputs["Position"], sep.inputs[0])
    pitch = (LEN - 0.25) / ROOF_BOWS
    t = mn(nt, "FRACT", mn(nt, "DIVIDE", mn(nt, "SUBTRACT", Y_FRONT - 0.13, sep.outputs[1]), pitch))
    sag = mn(nt, "POWER", mn(nt, "SINE", mn(nt, "MULTIPLY", t, math.pi)), 3.0)
    ax = mn(nt, "ABSOLUTE", sep.outputs[0])
    mid = mn(nt, "SUBTRACT", 1.0, mn(nt, "POWER", mn(nt, "DIVIDE", ax, 1.22, clamp=True), 2.0))
    n1 = N(nt, "ShaderNodeTexNoise", Scale=1.7, Detail=9.0, Roughness=0.66)
    M.L(nt, geo.outputs["Position"], n1.inputs["Vector"])
    m1 = N(nt, "ShaderNodeMapRange", **{"From Min": 0.36, "From Max": 0.68})
    M.L(nt, n1.outputs["Fac"], m1.inputs["Value"])
    pool = mn(nt, "MULTIPLY", mn(nt, "MULTIPLY", sag, mid), m1.outputs[0])
    edge = mn(nt, "MULTIPLY", mn(nt, "DIVIDE", mn(nt, "SUBTRACT", ax, 0.95), 0.30, clamp=True), 0.55)
    n2 = N(nt, "ShaderNodeTexNoise", Scale=9.0, Detail=8.0, Roughness=0.6)
    M.L(nt, geo.outputs["Position"], n2.inputs["Vector"])
    film = mn(nt, "MULTIPLY", n2.outputs["Fac"], 0.28)
    s_ = mn(nt, "MULTIPLY", mn(nt, "ADD", mn(nt, "ADD", pool, edge), film), amount * M.PARAMS["dirt"])
    old = mix.inputs[0].links[0].from_socket
    tot = mn(nt, "ADD", old, s_, clamp=True)
    M.L(nt, tot, mix.inputs[0])
    r_in = rr.inputs[0].links[0].from_socket if rr.inputs[0].links else None
    if r_in is not None:
        M.L(nt, mn(nt, "ADD", r_in, mn(nt, "MULTIPLY", s_, 0.25)), rr.inputs[0])


def materials():
    """Trailer authoring library on top of the TRAKT library (rubber, chassis, steel, lenses, plate, ...)."""
    M.build_library("white")
    P, N, L, mn = M.principled, M.N, M.L, M.math_node
    # body paint (front wall, front posts/header, door panels): white, the game tints by _PaintColor
    m, nt, b = P("trl_paint", "PAINT", (0.80, 0.80, 0.79), 0.36, coat=0.6)
    M.micro_bump(nt, b, 240.0, 0.02, 0.0002, target="Coat Normal")
    _grime(nt, b, (0.80, 0.80, 0.79), 0.36, h0=1.9, amount=0.55, film=1.5, streak=1.0, back=3.2, cav=1.6)
    # curtain: PVC-coated polyester ~900 g/m2, satin; albedo white (tinted in game by _CurtainColor)
    m, nt, b = P("curtain_pvc", "CURTAIN", (0.80, 0.80, 0.80), 0.55, spec=0.45)
    b.inputs["Sheen Weight"].default_value = 0.15
    _grime(nt, b, (0.80, 0.80, 0.80), 0.55, h0=2.1, amount=0.45, film=1.3, streak=1.15, cav=1.3, spray=1.7,
           dust=(0.17, 0.15, 0.12), band=0.9, band_z0=CURT_Z0)
    if LIVERY_BAND:
        _livery_mask(nt)
    # r10 (ADR 0083): the roof sheet is its own light-grey PVC (not the curtain colour: tint mask 0), with dirt pooled
    # in the sags between the bows and along the edges - what the chase camera looks down on
    m, nt, b = P("roof_tarp", "CURTAIN", ROOF_RGB, 0.62)
    _grime(nt, b, ROOF_RGB, 0.62, h0=5.0, amount=0.25, cav=0.6)
    if ROOF_OWN_COLOUR:
        _roof_stains(nt)
        z = nt.nodes.new("ShaderNodeValue")
        z.label = "tint_mask"
        z.outputs[0].default_value = 0.0
    # webbing straps welded to the curtain: same coated fabric, a shade darker (tinted with the curtain in game)
    m, nt, b = P("strap", "CURTAIN", (0.52, 0.52, 0.52), 0.68, spec=0.35)
    M.micro_bump(nt, b, 900.0, 0.3, 0.0003)
    _grime(nt, b, (0.52, 0.52, 0.52), 0.68, h0=2.0, amount=0.7, film=1.0, streak=0.5, spray=1.2,
           band=0.9, band_z0=CURT_Z0)
    # galvanised steel (lock bars, portal, hinges, buckles, side guard brackets): spangle + white rust spots
    rgb = (0.52, 0.53, 0.53)
    m, nt, b = P("galv", "METAL", rgb, 0.42, metal=0.85)
    M.micro_bump(nt, b, 60.0, 0.05, 0.0003, kind="voronoi")
    _grime(nt, b, rgb, 0.42, h0=1.6, amount=0.8, film=1.0, streak=0.7, back=1.5, dust=(0.20, 0.19, 0.17))
    # extruded aluminium (top rails, side guard profiles, door edge frames)
    rgb = (0.78, 0.79, 0.80)
    m, nt, b = P("alu_extr", "METAL", rgb, 0.34, metal=1.0, aniso=0.4)
    _grime(nt, b, rgb, 0.34, h0=1.4, amount=0.65, film=1.0, streak=0.45)
    # steel disc wheel, silver paint over steel: dielectric paint with a fine metallic pigment
    rgb = (0.55, 0.56, 0.57)
    m, nt, b = P("steel_wheel", "METAL", rgb, 0.40, metal=0.45, coat=0.2)
    # brake dust + rust bloom round the hand holes and nuts (cavity term), road film low down
    _grime(nt, b, rgb, 0.40, h0=1.2, amount=1.6, dust=(0.060, 0.045, 0.032), film=1.0, cav=2.6)
    # hub barrel + bearing cover: cast steel, dark grey paint; grease weep and brake dust darken it (on a working
    # trailer the hub reads dark, not beige)
    rgb = (0.060, 0.061, 0.063)
    m, nt, b = P("hub_cast", "METAL", rgb, 0.48, metal=0.55)
    M.micro_bump(nt, b, 180.0, 0.10, 0.0003)
    _grime(nt, b, rgb, 0.48, h0=1.2, amount=0.9, dust=(0.035, 0.028, 0.022), cav=1.8)
    # black chassis paint, heavier road dirt than the tractor (no mudguard spray guard over the frame)
    rgb = (0.022, 0.022, 0.023)
    m, nt, b = P("trl_chassis", "TRIM", rgb, 0.5)
    _grime(nt, b, rgb, 0.5, h0=1.45, amount=1.25, film=1.1, dust=(0.13, 0.12, 0.10), spray=0.8)
    # mudguard / toolbox plastic
    rgb = (0.03, 0.03, 0.031)
    m, nt, b = P("trl_plastic", "TRIM", rgb, 0.58, spec=0.45)
    M.micro_bump(nt, b, 900.0, 0.25, 0.0003)
    _grime(nt, b, rgb, 0.58, h0=1.3, amount=1.1, film=1.2, spray=1.0)
    # mudflap rubber (heavier dirt)
    rgb = (0.02, 0.02, 0.02)
    m, nt, b = P("flap_rubber", "TRIM", rgb, 0.8, spec=0.3)
    _grime(nt, b, rgb, 0.8, h0=1.1, amount=1.4, film=1.4, dust=(0.12, 0.105, 0.085))
    # retro-reflective contour marking (ECE R104): yellow on the sides, red at the rear; prismatic, satin
    P("reflex_yellow", "TRIM", (0.80, 0.55, 0.02), 0.28, spec=0.6)
    P("reflex_red", "TRIM", (0.55, 0.02, 0.015), 0.28, spec=0.6)
    P("reflex_white", "TRIM", (0.80, 0.80, 0.78), 0.28, spec=0.6)
    # floor edge (phenolic-coated plywood) and dock buffers
    P("plywood", "TRIM", (0.10, 0.065, 0.035), 0.6)
    # R70 rear marking plates: red fluorescent / yellow retro-reflective diagonal stripes (image)
    m, nt, b = P("r70", "TRIM", (0.8, 0.8, 0.8), 0.35, spec=0.6)
    ti = N(nt, "ShaderNodeTexImage", _image=r70_image())
    L(nt, ti.outputs["Color"], b.inputs["Base Color"])
    # lamp lenses: red / amber / clear rear lamp chambers (opaque in the bake, see A6 r4 note on transmission)
    P("lens_red_o", "LIGHTS", (0.45, 0.012, 0.010), 0.06, spec=0.7)
    P("lens_amber_o", "LIGHTS", (0.80, 0.30, 0.02), 0.06, spec=0.7)
    P("lens_white_o", "LIGHTS", (0.70, 0.70, 0.70), 0.05, spec=0.7)
    P("lamp_body", "LIGHTS", (0.025, 0.025, 0.027), 0.45, spec=0.5)
    for n in G.STATE["mats"]["plate"].node_tree.nodes:
        if n.type == "TEX_IMAGE":
            n.image = trailer_plate_image()
    # tyre 385/65 R22.5 (own sidewall text, rib tread)
    tyre_material()
    return G.STATE["mats"]


def trailer_plate_image():
    """Fictional Polish trailer plate (TRAKT plate layout, other registration)."""
    W, H = 1040, 228
    blue, yellow, k = (0.0, 0.06, 0.40), (0.95, 0.75, 0.0), (0.02, 0.02, 0.02)
    items = [("PL", 58, 52, 52, 0, (1, 1, 1), 0.02, "CENTER"),
             ("BI 8N402", 590, 112, 170, 0, (0.01, 0.01, 0.01), 0.035, "CENTER")]
    shapes = [("band", [(8, 8), (110, 8), (110, 220), (8, 220)], blue),
              ("b", [(0, 0), (W, 0), (W, 6), (0, 6)], k), ("b", [(0, H - 6), (W, H - 6), (W, H), (0, H)], k),
              ("b", [(W - 6, 0), (W, 0), (W, H), (W - 6, H)], k), ("b", [(0, 0), (6, 0), (6, H), (0, H)], k)]
    for j in range(12):
        a = 2 * math.pi * j / 12
        sx, sy = 59 + 30 * math.cos(a), 150 + 30 * math.sin(a)
        shapes.append(("star", [(sx + (6.5 if i % 2 == 0 else 2.6) * math.cos(math.pi / 2 + i * math.pi / 5),
                                 sy + (6.5 if i % 2 == 0 else 2.6) * math.sin(math.pi / 2 + i * math.pi / 5))
                                for i in range(10)], yellow))
    return M.render_text_texture("trl_plate", items, W, H, bg=(0.85, 0.85, 0.84), shapes=shapes, colorspace="sRGB")


def r70_image():
    """Rear marking plate of a TRAILER (UN R70 class 2/4 look): retro-reflective yellow field with a fluorescent red
    border - the oblique yellow/red chevrons belong to trucks and tractors, not to trailers and semi-trailers.
    WORKING_VALUE: border = 22 % of the plate height (R70 text not opened; plate here 565 x 110 mm)."""
    import numpy as np
    w, h = 512, 128
    y, x = np.mgrid[0:h, 0:w]
    bw = int(h * 0.22)
    img = np.zeros((h, w, 3))
    img[:] = (0.86, 0.66, 0.03)
    # honeycomb cells of the retro-reflective sheeting (faint, reads only close up)
    cell = (np.sin(x * 0.55) * np.sin((y + (x // 11 % 2) * 5) * 0.63)) * 0.035
    img += cell[..., None] * np.array((1.0, 0.8, 0.1))
    border = (x < bw) | (x > w - 1 - bw) | (y < bw) | (y > h - 1 - bw)
    img[border] = (0.66, 0.03, 0.02)
    rim = (x < 3) | (x > w - 4) | (y < 3) | (y > h - 4)       # bare aluminium plate edge
    img[rim] = (0.55, 0.56, 0.57)
    return M._save_image("trl_r70", np.clip(img, 0, 1).astype("float32"), colorspace="sRGB")


def tyre_profile():
    """(r, x) inner bead -> outer bead for 385/65 R22.5 (section height 250 mm, width 385 mm): the TRAKT 315/80
    radial stations, axial coordinates scaled by 385/315; 5-rib trailer tread (4 straight grooves)."""
    k = TYRE_W / 0.315
    Ro = TYRE_R
    side_in = [(0.296, -0.108), (0.322, -0.132), (0.36, -0.149), (0.40, -0.1565), (0.44, -0.1575), (0.475, -0.153),
               (0.503, -0.143), (0.522, -0.131), (0.531, -0.120)]
    side_in = [(r, x * k) for r, x in side_in]
    tw = 0.150
    tread = [(Ro - 0.004, -tw)]
    for c in (-0.090, -0.030, 0.030, 0.090):
        tread += [(Ro, c - 0.013), (Ro - 0.015, c - 0.006), (Ro - 0.015, c + 0.006), (Ro, c + 0.013)]
    tread += [(Ro - 0.004, tw)]
    side_out = [(r, -x) for r, x in reversed(side_in)]
    prof = side_in + tread + side_out
    s = [0.0]
    for (r0, x0), (r1, x1) in zip(prof, prof[1:]):
        s.append(s[-1] + math.hypot(r1 - r0, x1 - x0))
    v = [t / s[-1] for t in s]
    i0, i1 = len(side_in), len(side_in) + len(tread) - 1
    j0, j1 = len(prof) - 1 - 7, len(prof) - 1 - 1
    return prof, v, (v[i0], v[i1]), (v[j0], v[j1])


def tyre_material():
    prof, v, vt, vs = tyre_profile()
    tread = M._save_image("trl_tread", M.tread_height("steer"))
    W, H = 4096, 192
    g = (1, 1, 1)
    items = [("385/65 R22.5", 330, 100, 74, 0, g, 0.02, "CENTER"),
             ("160K", 880, 100, 50, 0, g, 0.01, "CENTER"),
             ("TUBELESS  RADIAL", 1400, 100, 34, 0, g, 0.0, "CENTER"),
             ("TRAILER", 1950, 100, 60, 0, g, 0.02, "CENTER"),
             ("FREE ROLLING", 2470, 100, 34, 0, g, 0.0, "CENTER"),
             ("REGROOVABLE", 2950, 100, 34, 0, g, 0.0, "CENTER"),
             ("385/65 R22.5", 3480, 100, 74, 0, g, 0.02, "CENTER"),
             ("E4 0118  DOT 7XK2 R4LM 2625", 3480, 40, 20, 0, g, 0.0, "CENTER"),
             ("MAX LOAD 4500 kg AT 900 kPa", 1400, 40, 18, 0, g, 0.0, "CENTER")]
    shapes = [("rect", [(0, 4), (W, 4), (W, 9), (0, 9)], g), ("rect", [(0, H - 9), (W, H - 9), (W, H - 4), (0, H - 4)], g)]
    side = M.render_text_texture("trl_sidewall", items, W, H, shapes=shapes)
    M.tyre_material("tyre_trailer", "steer", tread, side, vt, (vs[0], vs[1]), round(2 * math.pi * TYRE_R / 0.11))


# ---------------------------------------------------------------- mesh helpers
def sheet(name, rows, m, flip=False, smooth=True, sharp=None):
    """Grid surface from rows of Vector points (rows[i][j]); faces wound so that the normal points along
    (d row) x (d col) unless flip."""
    me = bpy.data.meshes.new(name)
    verts = [p for r in rows for p in r]
    nr, nc = len(rows), len(rows[0])
    faces = []
    for i in range(nr - 1):
        for j in range(nc - 1):
            a, b, c, d = i * nc + j, i * nc + j + 1, (i + 1) * nc + j + 1, (i + 1) * nc + j
            faces.append((a, d, c, b) if flip else (a, b, c, d))
    me.from_pydata([tuple(p) for p in verts], [], faces)
    uv = me.uv_layers.new(name="UVMap")
    for f in me.polygons:
        for li in f.loop_indices:
            vi = me.loops[li].vertex_index
            i, j = divmod(vi, nc)
            uv.data[li].uv = (j / max(nc - 1, 1), i / max(nr - 1, 1))
    me.materials.append(G.mat(m))
    ob = bpy.data.objects.new(name, me)
    if smooth:
        me.shade_smooth()
        if sharp:
            me.set_sharp_from_angle(angle=math.radians(sharp))
    return G.link(ob)


def sweep(name, path, section, m, closed_section=True, smooth=False, sharp=40):
    """Sweep a 2D section (u along X-ish 'side' axis, v along Z) along a polyline path (list of Vectors) with
    a frame whose side axis is `side` (perpendicular to the path in the XY plane rotated) - used for beams,
    rails and profiles running along Y. section: [(a, b)] in the local (side, up) plane."""
    pts = [V(p) for p in path]
    rows = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        side = V((1, 0, 0))
        up = t.cross(side).normalized()
        if up.z < 0:
            up = -up
        rows.append([p + side * a + up * b for a, b in section])
    bm = bmesh.new()
    vv = [[bm.verts.new(q) for q in r] for r in rows]
    n = len(section)
    rng = range(n) if closed_section else range(n - 1)
    for i in range(len(vv) - 1):
        for k in rng:
            k2 = (k + 1) % n
            bm.faces.new((vv[i][k], vv[i][k2], vv[i + 1][k2], vv[i + 1][k]))
    if closed_section:
        try:
            bm.faces.new(vv[0])
            bm.faces.new(list(reversed(vv[-1])))
        except ValueError:
            pass
    return G.obj_from_bm(name, bm, m, smooth=smooth, sharp=sharp)


def mirror_x(ob, name):
    c = ob.copy()
    c.data = ob.data.copy()
    c.name = name
    c.data.transform(Matrix.Scale(-1, 4, (1, 0, 0)))
    c.data.flip_normals()
    for k in ob.keys():
        c[k] = ob[k]
    G.STATE["coll"].objects.link(c)
    return c


def side_pair(fn, *a, **kw):
    """Run fn(s, sd, ...) for s = -1 (left, L) and +1 (right, R)."""
    return [fn(s, sd, *a, **kw) for s, sd in ((-1, "L"), (1, "R"))]


# ---------------------------------------------------------------- frame
def beam_bottom(y):
    """Main beam lower flange height along y (gooseneck step behind the coupler plate, rear taper)."""
    tab = [(Y_FRONT, KP_H), (-0.95, KP_H), (-1.75, 0.80), (-5.30, 0.80), (-5.75, 0.86), (-10.2, 0.86),
           (Y_REAR + 0.15, 1.02)]
    for (y0, z0), (y1, z1) in zip(tab, tab[1:]):
        if y1 <= y <= y0:
            t = (y0 - y) / (y0 - y1)
            return z0 + (z1 - z0) * t
    return tab[-1][1]


def frame():
    part("CHASSIS", "frame")
    ys = [Y_FRONT - 0.05, -0.95, -1.15, -1.35, -1.55, -1.75, -5.30, -5.75, -10.2, Y_REAR + 0.15]
    top = FLOOR - 0.04
    for s in (-1, 1):
        x = s * BEAM_X
        # web (8 mm) follows the bottom profile; flanges 120 mm x 12 mm
        poly = [(y, beam_bottom(y) + 0.012) for y in ys] + [(ys[-1], top - 0.012), (ys[0], top - 0.012)]
        web = extrude_poly(f"beam_web_{s}", poly, 0.008, "trl_chassis", plane="YZ", origin=(x - 0.004, 0, 0))
        web.data.shade_flat()
        path = [V((x, y, beam_bottom(y) + 0.006)) for y in ys]
        sweep(f"beam_flange_lo_{s}", path, [(-0.06, -0.006), (0.06, -0.006), (0.06, 0.006), (-0.06, 0.006)],
              "trl_chassis")
        box_mm(f"beam_flange_hi_{s}", x - 0.06, x + 0.06, ys[-1], ys[0], top - 0.012, top, "trl_chassis")
    # coupler plate with grease around the kingpin, kingpin (ISO 337 2" pin)
    box_mm("coupler_plate", -0.78, 0.78, -0.98, Y_FRONT - 0.06, KP_H, KP_H + 0.014, "trl_chassis", bev=0.004)
    g = cyl("kingpin_grease", (0, 0.12, KP_H - 0.0006), 0.36, 0.0012, "grease", axis="Z", seg=40)
    g.scale = (1.0, 1.25, 1.0)
    lathe("kingpin", [(0.060, 0.0), (0.060, 0.010), (0.0254, 0.016), (0.0254, 0.055), (0.0365, 0.058),
                      (0.0365, 0.078), (0.030, 0.084), (0.0, 0.084)], V((0, 0, KP_H)), "steel", seg=24,
          side=-1, axis="Z", sharp=40)
    # front bulkhead cross member and rear sill
    box_mm("front_cross", -RAIL_OUT, RAIL_OUT, Y_FRONT - 0.16, Y_FRONT - 0.02, KP_H + 0.014, FLOOR + 0.01,
           "trl_chassis", bev=0.004)
    box_mm("rear_sill", -RAIL_OUT, RAIL_OUT, Y_REAR + 0.02, Y_REAR + 0.16, 1.08, FLOOR + 0.03, "trl_chassis",
           bev=0.005)
    box_mm("rear_sill_face", -1.20, 1.20, Y_REAR + 0.012, Y_REAR + 0.02, 1.10, FLOOR + 0.02, "galv", bev=0.002)
    for s in (-1, 1):
        box_mm(f"dock_buffer_{s}", s * 0.33, s * 0.55, Y_REAR + 0.0, Y_REAR + 0.09, 0.96, 1.08, "rubber", bev=0.01)
    # side rails (C-profile, 230 mm) with lashing pockets and contour marking
    sec = [(1.17, FLOOR + 0.01), (RAIL_OUT, FLOOR + 0.01), (RAIL_OUT, 1.083), (1.205, 1.083), (1.205, 1.097),
           (RAIL_OUT - 0.012, 1.097), (RAIL_OUT - 0.012, FLOOR - 0.004), (1.17, FLOOR - 0.004)]
    for s in (-1, 1):
        pts = [(s * a, b) for a, b in sec]
        if s < 0:
            pts = list(reversed(pts))
        r = extrude_poly(f"side_rail_{s}", pts, LEN - 0.02, "trl_chassis", plane="XZ",
                         origin=(0, Y_FRONT - 0.01, 0), normal_sign=-1)
        r.data.shade_flat()
        # side line marking (UN R48 6.21, UN R104 class C retro-reflective tape, yellow, 50 mm) along the rail face,
        # interrupted only where the curtain buckles hook under the rail (90 mm gaps at the straps): the elements
        # cover ~85 % of the body length (R48 6.21.4: >= 80 % - UNVERIFIED, regulation text not opened here)
        st = strap_positions()
        for k in range(len(st) - 1):
            box_mm(f"contour_side_{s}_{k}", s * (RAIL_OUT + 0.0008), s * (RAIL_OUT + 0.0018), st[k + 1] + 0.045,
                   st[k] - 0.045, 1.125, 1.175, "reflex_yellow")
        # lashing pockets under the rail lip (every ~0.6 m)
        for j in range(21):
            yy = Y_FRONT - 0.5 - j * 0.62
            box_mm(f"lash_{s}_{j}", s * 1.17, s * 1.215, yy - 0.04, yy + 0.04, 1.10, 1.135, "galv")
    # outriggers (cantilever cross members beam -> side rail), lower over the tyres
    k = 0
    y = Y_FRONT - 0.42
    while y > Y_REAR + 0.3:
        over_wheels = AXLES[-1] - 0.75 < y < AXLES[0] + 0.75
        for s in (-1, 1):
            zb0 = 1.17 if over_wheels else min(max(beam_bottom(y), 1.08), 1.17)
            pts = [(s * (BEAM_X + 0.06), FLOOR - 0.04), (s * 1.17, FLOOR - 0.04), (s * 1.17, 1.17), (s * (BEAM_X + 0.06), zb0)]
            if s < 0:
                pts = list(reversed(pts))
            o = extrude_poly(f"outrigger_{s}_{k}", pts, 0.006, "trl_chassis", plane="XZ", origin=(0, y, 0))
            o.data.shade_flat()
            box_mm(f"outrigger_lo_{s}_{k}", s * (BEAM_X + 0.06), s * 1.17, y - 0.035, y + 0.041,
                   min(zb0, 1.17) - 0.006, min(zb0, 1.17), "trl_chassis")
        y -= 0.62
        k += 1
    # cross members between the beams (visible from below / behind the wheels)
    for j, yy in enumerate([0.4, -0.6, -2.2, -3.4, -4.6, -5.8, -6.95, -8.35, -9.7, -10.9]):
        zb = beam_bottom(yy)
        box_mm(f"crossmember_{j}", -BEAM_X + 0.004, BEAM_X - 0.004, yy - 0.05, yy + 0.05,
               min(max(zb + 0.12, FLOOR - 0.22), FLOOR - 0.06), FLOOR - 0.04, "trl_chassis")
    # air reservoir and EBS modulator
    cyl("air_tank", (0, -5.05, 0.98), 0.125, 0.82, "trl_chassis", axis="X", seg=20, bev=0.03, bseg=2)
    for s in (-1, 1):
        box_mm(f"air_tank_strap_{s}", s * 0.30 - 0.02, s * 0.30 + 0.02, -5.19, -4.91, 0.85, 1.11, "galv")
    box_mm("ebs_modulator", -0.18, 0.12, -7.05, -6.85, 1.00, 1.16, "trl_plastic", bev=0.01)
    tube("ebs_hose_a", [(0.0, -6.95, 1.0), (0.10, -6.9, 0.85), (0.42, -6.7, 0.75), (0.80, -6.45, 0.68)], 0.008,
         "rubber", seg=6)
    tube("ebs_hose_b", [(-0.05, -7.0, 1.0), (-0.12, -7.2, 0.85), (-0.45, -7.5, 0.72), (-0.80, -7.68, 0.66)], 0.008,
         "rubber", seg=6)
    tube("air_line_main", [(0.12, Y_FRONT - 0.15, 1.24), (0.38, 0.0, 1.22), (0.38, -4.6, 1.20), (0.10, -5.0, 1.05)],
         0.009, "rubber", seg=6)
    # document tube (grey PVC) under the left rail, front
    cyl("doc_tube", (-0.98, 0.35, 1.02), 0.055, 0.80, "trl_plastic", axis="Y", seg=16, bev=0.006)
    cyl("doc_tube_cap", (-0.98, 0.76, 1.02), 0.062, 0.05, "trl_plastic", axis="Y", seg=16, bev=0.008)
    for yy in (0.1, 0.6):
        box_mm(f"doc_tube_clamp_{yy}", -1.05, -0.91, yy - 0.015, yy + 0.015, 1.02, 1.12, "galv")


# ---------------------------------------------------------------- under-floor equipment (r10, ADR 0083)
def underfloor_equipment():
    """Fills the empty bay between the landing gear and the tridem (kerb side): spare wheel in a hanging carrier and
    a two-door pallet box behind the side guard. Sizes class-typical, WORKING_VALUE (no manufacturer drawing used)."""
    part("CHASSIS", "frame")
    # spare wheel 385/65 R22.5 lying flat, disc down, in a galvanised carrier
    cx, cy, z0 = 0.65, -3.32, 0.372
    zc = z0 + TYRE_W / 2
    prof, v, _, _ = tyre_profile()
    lathe("spare_tyre", prof, V((cx, cy, zc)), "tyre_trailer", seg=40, side=1, axis="Z", uv_v=v, sharp=60)
    k = 1.30
    rim = [(0.300, 0.112 * k), (0.302, 0.124 * k), (0.294, 0.128 * k), (0.284, 0.100 * k),
           (0.262, 0.080 * k), (0.256, 0.050), (0.256, -0.050), (0.262, -0.080 * k), (0.284, -0.100 * k),
           (0.294, -0.128 * k), (0.302, -0.124 * k), (0.300, -0.112 * k)]
    lathe("spare_rim", rim, V((cx, cy, zc)), "steel_wheel", seg=32, side=1, axis="Z", sharp=45)
    et = 0.120
    dprof = [(0.110, et - 0.008), (0.150, et - 0.008), (0.172, et - 0.020), (0.235, et - 0.030), (0.250, et - 0.040),
             (0.250, et - 0.052), (0.232, et - 0.042), (0.168, et - 0.032), (0.146, et - 0.020), (0.110, et - 0.020)]
    lathe("spare_disc", dprof, V((cx, cy, zc)), "steel_wheel", seg=32, side=-1, axis="Z", sharp=40)
    for j, dy in enumerate((-0.30, 0.30)):
        box_mm(f"spare_carrier_bar_{j}", cx - 0.56, cx + 0.56, cy + dy - 0.03, cy + dy + 0.03, z0 - 0.03, z0 - 0.004,
               "galv", bev=0.003)
        rod(f"spare_hanger_in_{j}", (cx - 0.545, cy + dy, z0 - 0.01), (cx - 0.545, cy + dy, 1.20), 0.011, "galv", seg=8)
        rod(f"spare_hanger_out_{j}", (cx + 0.545, cy + dy, z0 - 0.01), (cx + 0.545, cy + dy, 1.09), 0.011, "galv", seg=8)
    box_mm("spare_clamp", cx - 0.13, cx + 0.13, cy - 0.035, cy + 0.035, zc + et - 0.006, zc + et + 0.006, "galv",
           bev=0.003)
    rod("spare_rod", (cx, cy, zc + et), (cx, cy, 1.22), 0.012, "galv", seg=8)
    cyl("spare_nut", (cx, cy, zc + et + 0.02), 0.028, 0.03, "steel", axis="Z", seg=6)
    # pallet box: black powder-coated steel body, two galvanised drop-down doors with pressed ribs and paddle latches
    ya, yb, zb, zt = -3.98, -5.50, 0.50, 1.06
    ym = (ya + yb) / 2
    for s, sd in ((-1, "L"), (1, "R")):
        x0, x1 = s * 0.62, s * 1.165
        box_mm(f"pallet_box_{sd}", min(x0, x1), max(x0, x1), yb, ya, zb, zt, "trl_chassis", bev=0.008)
        for j, (d0, d1) in enumerate(((ya - 0.025, ym + 0.006), (ym - 0.006, yb + 0.025))):
            xa, xb = sorted((x1, x1 + s * 0.006))
            box_mm(f"pallet_door_{sd}_{j}", xa, xb, d1, d0, zb + 0.03, zt - 0.03, "galv", bev=0.002, seg=1)
            xa, xb = sorted((x1 + s * 0.006, x1 + s * 0.011))
            for z in (0.66, 0.90):
                box_mm(f"pallet_rib_{sd}_{j}_{z}", xa, xb, d1 + 0.06, d0 - 0.06, z - 0.018, z + 0.018, "galv",
                       bev=0.004, seg=1)
            yl = (d0 + d1) / 2
            xa, xb = sorted((x1 + s * 0.0062, x1 + s * 0.0072))
            box_mm(f"pallet_latch_pan_{sd}_{j}", xa, xb, yl - 0.055, yl + 0.055, zt - 0.14, zt - 0.07, "gap")
            xa, xb = sorted((x1 + s * 0.007, x1 + s * 0.013))
            box_mm(f"pallet_latch_{sd}_{j}", xa, xb, yl - 0.035, yl + 0.035, zt - 0.125, zt - 0.085, "steel",
                   bev=0.002, seg=1)
            for yh in (d0 - 0.12, d1 + 0.12):
                cyl(f"pallet_hinge_{sd}_{j}_{yh:.2f}", (x1 + s * 0.008, yh, zb + 0.03), 0.010, 0.09, "galv", axis="Y",
                    seg=8)
        for j, yy in enumerate((ya - 0.10, yb + 0.10)):   # hanger straps up to the outriggers
            xa, xb = sorted((x0 - s * 0.004, x1 + s * 0.002))
            box_mm(f"pallet_strap_{sd}_{j}", xa, xb, yy - 0.02, yy + 0.02, zt - 0.004, 1.17, "galv")
    # two wheel chocks in a holder between the landing gear and the toolbox (driver side)
    for j, yy in enumerate((-2.70, -2.90)):
        extrude_poly(f"chock_{j}", [(yy + 0.07, 0.66), (yy - 0.07, 0.66), (yy - 0.07, 0.69), (yy + 0.045, 0.84),
                                    (yy + 0.07, 0.84)], 0.16, "trl_plastic", plane="YZ", origin=(-1.13, 0, 0),
                     bev=0.006).data.shade_flat()
    box_mm("chock_holder", -1.15, -0.95, -2.98, -2.62, 0.635, 0.66, "galv", bev=0.002)
    for yy in (-2.96, -2.64):
        box_mm(f"chock_holder_arm_{yy}", -1.05, -1.03, yy - 0.012, yy + 0.012, 0.66, 1.17, "galv")


# ---------------------------------------------------------------- running gear
def axles_and_suspension():
    part("CHASSIS", "frame")
    for i, ya in enumerate(AXLES):
        cyl(f"axle_beam_{i}", (0, ya, WC), 0.073, 1.72, "trl_chassis", axis="X", seg=16)
        for s in (-1, 1):
            x = s * BEAM_X
            hy = ya + 0.62
            zb = beam_bottom(hy)
            # hanger bracket (welded plates) and pivot bush
            extrude_poly(f"hanger_{i}_{s}", [(hy - 0.13, zb), (hy + 0.13, zb), (hy + 0.06, 0.50), (hy - 0.07, 0.50)],
                         0.11, "trl_chassis", plane="YZ", origin=(x - 0.055, 0, 0)).data.shade_flat()
            cyl(f"hanger_bush_{i}_{s}", (x, hy, 0.56), 0.045, 0.14, "steel", axis="X", seg=14)
            # trailing arm: pivot -> under the axle -> bellows seat
            pts = [(hy, 0.58), (hy, 0.52), (ya, 0.415), (ya - 0.42, 0.445), (ya - 0.42, 0.50), (ya, 0.47),
                   (hy - 0.05, 0.585)]
            arm = extrude_poly(f"trailing_arm_{i}_{s}", pts, 0.085, "trl_chassis", plane="YZ",
                               origin=(x - 0.0425, 0, 0))
            arm.data.shade_flat()
            # U-bolts round the axle
            for dx in (-0.06, 0.06):
                box_mm(f"ubolt_{i}_{s}_{dx}", x + dx - 0.009, x + dx + 0.009, ya - 0.085, ya + 0.085, 0.40, WC + 0.08,
                       "steel")
            # air bellows (rolling lobe) between the arm end and the beam
            zb2 = beam_bottom(ya - 0.42)
            lathe(f"bellow_{i}_{s}", [(0.0, 0.0), (0.10, 0.0), (0.135, 0.03), (0.15, 0.10), (0.15, 0.20),
                                      (0.135, 0.27), (0.11, 0.30), (0.11, zb2 - 0.50 - 0.02), (0.0, zb2 - 0.50 - 0.02)],
                  V((x, ya - 0.42, 0.50)), "rubber", seg=16, side=1, axis="Z", sharp=60)
            box_mm(f"bellow_plate_{i}_{s}", x - 0.13, x + 0.13, ya - 0.55, ya - 0.29, zb2 - 0.02, zb2, "steel")
            # shock absorber (hanger top -> arm)
            rod(f"damper_{i}_{s}", (x + s * 0.08, hy - 0.05, min(zb - 0.02, 0.95)), (x + s * 0.08, ya + 0.12, 0.47),
                0.032, "trl_chassis", seg=10)
            rod(f"damper_rod_{i}_{s}", (x + s * 0.08, hy - 0.02, min(zb - 0.02, 0.95)), (x + s * 0.08, hy - 0.16, 0.80),
                0.012, "chrome", seg=8)
            # disc brake: caliper + chamber (static)
            xc = s * 0.755
            box_mm(f"caliper_{i}_{s}", xc - 0.055, xc + 0.055, ya + 0.08, ya + 0.19, WC + 0.06, WC + 0.24,
                   "trl_chassis", bev=0.012)
            cyl(f"brake_chamber_{i}_{s}", (s * 0.62, ya + 0.16, WC + 0.24), 0.085, 0.16, "trl_chassis", axis="X",
                seg=14, bev=0.02, bseg=1)
            tube(f"brake_hose_{i}_{s}", [(s * 0.55, ya + 0.16, WC + 0.24), (s * 0.48, ya + 0.3, WC + 0.40),
                                        (s * 0.40, ya + 0.35, 1.05)], 0.008, "rubber", seg=6)


def wheel(name, xc, ya, out, seg=48):
    """385/65 R22.5 on a 22.5x11.75 steel disc wheel, ET 120 (disc towards the outside: single trailer wheel).
    The rim is an open surface (well + flanges; the barrel inside the tyre is never seen)."""
    part("WHEEL_" + name.split("_")[1], "wheels")
    c = V((xc, ya, WC))
    prof, v, _, _ = tyre_profile()
    lathe(name + "_tyre", prof, c, "tyre_trailer", seg=seg, side=out, uv_v=v, sharp=60)
    k = 1.30     # 11.75 / 9.00 rim width
    rim = [(0.300, 0.112 * k), (0.302, 0.124 * k), (0.294, 0.128 * k), (0.284, 0.100 * k),
           (0.262, 0.080 * k), (0.256, 0.050), (0.256, -0.050), (0.262, -0.080 * k), (0.284, -0.100 * k),
           (0.294, -0.128 * k), (0.302, -0.124 * k), (0.300, -0.112 * k)]
    inner = [(0.290, 0.118 * k), (0.250, 0.05), (0.250, -0.05), (0.290, -0.118 * k)]   # barrel seen through holes
    lathe(name + "_rim", rim + inner[::-1], c, "steel_wheel", seg=40, side=out, sharp=45)
    et = 0.120
    # disc: pressed steel with a raised ring and 10 round hand holes; centre flat with the stud circle
    dprof = [(0.110, et - 0.008), (0.150, et - 0.008), (0.172, et - 0.020), (0.235, et - 0.030), (0.250, et - 0.040),
             (0.250, et - 0.052), (0.232, et - 0.042), (0.168, et - 0.032), (0.146, et - 0.020), (0.110, et - 0.020)]
    disc = lathe(name + "_disc", dprof, c, "steel_wheel", seg=40, side=out, sharp=40)
    cutters = []
    for j in range(10):
        a = 2 * math.pi * (j + 0.5) / 10
        cutters.append(cyl(f"{name}_hh{j}", (xc + out * (et - 0.03), ya + 0.205 * math.cos(a), WC + 0.205 * math.sin(a)),
                           0.026, 0.08, "steel_wheel", seg=10))
    boolean(disc, cutters)
    xf = xc + out * (et - 0.008)
    for j in range(10):
        a = 2 * math.pi * j / 10
        p = (xf + out * 0.016, ya + PCD_R * math.cos(a), WC + PCD_R * math.sin(a))
        # M22x1.5 flange nut (32 mm hex + captive washer) on a stud protruding ~12 mm. No loose-nut indicators:
        # rare on PL fleets, and at game distance they read as yellow sticks
        cyl(f"{name}_nutwasher{j}", (xf + out * 0.003, p[1], p[2]), 0.0205, 0.006, "steel", seg=12, axis="X")
        cyl(f"{name}_nut{j}", p, 0.0165, 0.026, "steel", seg=6, axis="X")
        cyl(f"{name}_stud{j}", (xf + out * 0.034, p[1], p[2]), 0.0095, 0.012, "hub_cast", seg=8, axis="X")
    # hub barrel visible inside the disc centre bore (dark cast steel)
    cyl(f"{name}_hub", (xf - out * 0.004, ya, WC), 0.108, 0.020, "hub_cast", seg=24, axis="X")
    # bearing cover: short flat-faced dome with a hex boss (cast, dark: not a chrome bulb, not beige)
    lathe(name + "_hubcap", [(0.090, 0.0), (0.090, 0.030), (0.084, 0.050), (0.066, 0.062), (0.040, 0.066),
                             (0.0, 0.066)], V((xf, ya, WC)), "hub_cast", seg=24, side=out, sharp=40)
    cyl(f"{name}_hubcap_hex", (xf + out * 0.074, ya, WC), 0.026, 0.016, "hub_cast", seg=6, axis="X")
    cyl(f"{name}_hubcap_plug", (xf + out * 0.083, ya, WC), 0.010, 0.004, "steel", seg=8, axis="X")


def wheels():
    for i, ya in enumerate(AXLES):
        for s, sd in ((-1, "L"), (1, "R")):
            wheel(f"wheel_{i + 1}{sd}", s * TRACK / 2, ya, s)


def mudguards():
    part("CHASSIS", "frame")
    for i, ya in enumerate(AXLES):
        for s in (-1, 1):
            x0, x1 = s * 0.80, s * 1.235
            G.arch(f"mudguard_{i}_{s}", ya, WC, 0.615, 0.622, min(x0, x1), max(x0, x1), 22, 158, "trl_plastic", n=30)
            # outer skirt lip (stiffening flange) on the outside edge
            G.arch(f"mudguard_lip_{i}_{s}", ya, WC, 0.600, 0.640, min(s * 1.225, s * 1.240), max(s * 1.225, s * 1.240),
                   24, 156, "trl_plastic", n=30)
            # stays to the outrigger
            for yy in (ya + 0.45, ya - 0.45):
                box_mm(f"mudguard_stay_{i}_{s}_{yy}", s * 0.96 - 0.012, s * 0.96 + 0.012, yy - 0.012, yy + 0.012,
                       WC + 0.56, 1.17, "galv")
    # rear mudflaps (hinged on a bracket behind the last axle)
    ya = AXLES[-1] - 0.66
    for s, sd in ((-1, "L"), (1, "R")):
        part("CHASSIS", "frame")
        box_mm(f"mudflap_brk_{s}", s * 0.78, s * 1.24, ya - 0.02, ya + 0.02, 1.08, 1.12, "galv")
        part(f"MUDFLAP_{sd}", "frame")
        pts = [(s * 0.80, 0.20), (s * 1.235, 0.20), (s * 1.235, 1.08), (s * 0.80, 1.08)]
        if s < 0:
            pts = list(reversed(pts))
        f = extrude_poly(f"mudflap_{sd}", pts, 0.008, "flap_rubber", plane="XZ", origin=(0, ya - 0.026, 0))
        f.data.shade_flat()
        for j in range(5):
            box_mm(f"mudflap_rib_{sd}_{j}", s * (0.85 + j * 0.085), s * (0.865 + j * 0.085), ya - 0.032, ya - 0.026,
                   0.24, 1.0, "flap_rubber")
    part("CHASSIS", "frame")


def side_guards():
    """Side underrun protection (UN R73): two aluminium profiles per side between landing gear and first axle."""
    part("CHASSIS", "frame")
    y0, y1 = LG["z"] - 0.32, AXLES[0] + TYRE_R + 0.22
    for s in (-1, 1):
        x = s * 1.215
        for zc in (0.50, 0.90):
            sec = [(-0.012, -0.05), (0.012, -0.05), (0.012, 0.05), (-0.012, 0.05)]
            ob = box_mm(f"sideguard_{s}_{zc}", x - 0.012, x + 0.012, y1, y0, zc - 0.05, zc + 0.05, "alu_extr", bev=0.004)
            box_mm(f"sideguard_groove_{s}_{zc}", x + s * 0.0125 - 0.001, x + s * 0.0125 + 0.001, y1 + 0.02, y0 - 0.02,
                   zc - 0.004, zc + 0.004, "gap")
            # black plastic end caps closing the hollow extrusion (real guards never end in a raw saw cut)
            for k, ye in enumerate((y0, y1)):
                d = 1 if k == 0 else -1
                box_mm(f"sideguard_cap_{s}_{zc}_{k}", x - 0.014, x + 0.014, min(ye - d * 0.004, ye + d * 0.022),
                       max(ye - d * 0.004, ye + d * 0.022), zc - 0.052, zc + 0.052, "trl_plastic")
        for yy in (y0 - 0.12, (y0 + y1) / 2, y1 + 0.12):
            box_mm(f"sideguard_post_{s}_{yy:.2f}", x - s * 0.03 - 0.025, x - s * 0.03 + 0.025, yy - 0.004, yy + 0.004,
                   0.44, 1.17, "galv")
        # amber side reflector on the upper profile
        box_mm(f"side_reflector_{s}", x + s * 0.013, x + s * 0.017, (y0 + y1) / 2 - 0.04, (y0 + y1) / 2 + 0.04, 0.88,
               0.92, "lens_amber_o")
    # toolbox behind the left guard (black plastic, two latches)
    box_mm("toolbox", -1.15, -0.82, -3.80, -3.05, 0.60, 1.07, "trl_plastic", bev=0.02)   # r10: 0.80 m forward
    for yy in (-3.62, -3.23):
        box_mm(f"toolbox_latch_{yy}", -1.16, -1.145, yy - 0.03, yy + 0.03, 0.96, 1.02, "steel")


def landing_gear():
    """Two-speed landing gear at y = LG.z, legs at +-LG.half_track; crank on the right (kerb) side.
    LEG_L/R = inner leg + sand shoe (translate along Z); CRANK rotates about X. Raised: foot bottom LG.raised_foot_y."""
    yl = LG["z"]
    hx = LG["half_track"]
    foot = LG["raised_foot_y"]
    for s, sd in ((-1, "L"), (1, "R")):
        part("CHASSIS", "gear")
        x = s * hx
        box_mm(f"leg_outer_{sd}", x - 0.075, x + 0.075, yl - 0.075, yl + 0.075, 0.56, 1.17, "trl_chassis", bev=0.006)
        box_mm(f"leg_collar_{sd}", x - 0.082, x + 0.082, yl - 0.082, yl + 0.082, 0.56, 0.60, "trl_chassis", bev=0.004)
        # mounting plate leg -> beam, diagonal brace back to the beam, cross brace
        extrude_poly(f"leg_plate_{sd}", [(s * (BEAM_X + 0.005), FLOOR - 0.05), (x - s * 0.075, FLOOR - 0.05),
                                         (x - s * 0.075, 0.82), (s * (BEAM_X + 0.005), 0.92)][::(1 if s > 0 else -1)],
                     0.010, "trl_chassis", plane="XZ", origin=(0, yl - 0.08, 0)).data.shade_flat()
        rod(f"leg_brace_{sd}", (x, yl - 0.07, 0.72), (s * (BEAM_X + 0.03), yl - 1.05, beam_bottom(yl - 1.05) + 0.02),
            0.022, "trl_chassis", seg=8)
        rod(f"leg_xbrace_{sd}", (x - s * 0.07, yl + 0.06, 0.70), (-x + s * 0.07, yl + 0.06, 1.05), 0.018,
            "trl_chassis", seg=8)
        if s > 0:   # gearbox + crank on the right leg
            box_mm("leg_gearbox", x - 0.07, x + 0.10, yl - 0.09, yl + 0.09, 0.95, 1.10, "trl_chassis", bev=0.01)
            cyl("crank_shaft_stub", (x + 0.13, yl, 1.02), 0.016, 0.07, "steel", axis="X", seg=10)
            box_mm("crank_holder", x + 0.06, x + 0.09, yl - 0.13, yl - 0.10, 0.62, 0.70, "galv")
        cyl(f"cross_shaft_{sd}", (s * hx / 2, yl, 1.02), 0.014, hx - 0.15, "steel", axis="X", seg=8)
        part(f"LEG_{sd}", "gear")
        box_mm(f"leg_inner_{sd}", x - 0.062, x + 0.062, yl - 0.062, yl + 0.062, foot + 0.06, 1.10, "trl_chassis",
               bev=0.004)
        # sand shoe on a pivot
        box_mm(f"leg_foot_{sd}", x - 0.11, x + 0.11, yl - 0.13, yl + 0.13, foot, foot + 0.02, "trl_chassis", bev=0.006)
        for dy in (-0.05, 0.05):
            box_mm(f"leg_foot_lug_{sd}_{dy}", x - 0.06, x + 0.06, yl + dy - 0.006, yl + dy + 0.006, foot + 0.02,
                   foot + 0.08, "trl_chassis")
        cyl(f"leg_foot_pin_{sd}", (x, yl, foot + 0.055), 0.014, 0.15, "steel", axis="Y", seg=10)
    part("CRANK", "gear")
    x = hx + 0.165
    # stowed: arm hangs down along the leg, grip hooked in the holder
    box_mm("crank_arm", x - 0.012, x + 0.012, yl - 0.018, yl + 0.018, 0.72, 1.04, "galv")
    cyl("crank_hub", (x, yl, 1.02), 0.022, 0.04, "galv", axis="X", seg=10)
    rod("crank_grip_rod", (x, yl, 0.73), (x, yl - 0.13, 0.73), 0.010, "galv", seg=8)
    cyl("crank_grip", (x, yl - 0.10, 0.73), 0.017, 0.10, "rubber", axis="Y", seg=10, bev=0.004)
    part("CHASSIS", "frame")


# ---------------------------------------------------------------- body
def front_wall():
    part("CHASSIS", "body")
    # corrugated steel bulkhead (vertical trapezoid ribs, pitch 0.30 m, depth 18 mm)
    xs = []
    x = -1.165
    pitch = 0.30
    n = int(round(2 * 1.165 / pitch))
    pitch = 2 * 1.165 / n
    prof = []
    for k in range(n):
        x0 = -1.165 + k * pitch
        prof += [(x0, 0.0), (x0 + 0.06, 0.0), (x0 + 0.09, 0.018), (x0 + 0.21, 0.018), (x0 + 0.24, 0.0)]
    prof.append((1.165, 0.0))
    z0, z1 = FLOOR + 0.01, TOPRAIL_Z
    rows = [[V((px, Y_FRONT - 0.028 + d, z)) for px, d in prof] for z in (z0, z1)]
    sheet("front_wall", rows, "trl_paint", flip=True, smooth=False)
    # front corner posts (rounded), header, bottom rail
    for s in (-1, 1):
        sec = G.rrect(0.11, 0.15, 0.04, n=4)
        pts = [(s * (1.275 - 0.055) + a, Y_FRONT - 0.075 + b) for a, b in sec]
        bm = bmesh.new()
        lo = [bm.verts.new((a, b, FLOOR - 0.02)) for a, b in pts]
        hi = [bm.verts.new((a, b, ROOF - 0.03)) for a, b in pts]
        nn = len(pts)
        for i in range(nn):
            j = (i + 1) % nn
            bm.faces.new((lo[i], lo[j], hi[j], hi[i]))
        bm.faces.new(list(reversed(lo)))
        bm.faces.new(hi)
        G.obj_from_bm(f"front_post_{s}", bm, "trl_paint", sharp=50)
    box_mm("front_header", -1.17, 1.17, Y_FRONT - 0.13, Y_FRONT - 0.002, TOPRAIL_Z - 0.01, ROOF - 0.03, "trl_paint",
           bev=0.006)
    box_mm("front_bottom_rail", -1.17, 1.17, Y_FRONT - 0.12, Y_FRONT - 0.004, FLOOR - 0.02, FLOOR + 0.07, "trl_paint",
           bev=0.006)
    # coupling panel: red (supply) / yellow (control) palm couplings, ISO 7638 ABS socket, 15-pin socket
    box_mm("coupling_bracket", -0.30, 0.30, Y_FRONT - 0.004, Y_FRONT + 0.006, FLOOR + 0.03, FLOOR + 0.20, "galv")
    for x, mname in ((-0.20, "coupling_red"), (-0.08, "coupling_yellow")):
        cyl(f"palm_{mname}", (x, Y_FRONT + 0.035, FLOOR + 0.115), 0.042, 0.06, mname, axis="Y", seg=16, bev=0.006)
        box_mm(f"palm_lip_{mname}", x - 0.04, x + 0.04, Y_FRONT + 0.06, Y_FRONT + 0.07, FLOOR + 0.07, FLOOR + 0.10,
               mname)
    for x in (0.08, 0.20):
        cyl(f"socket_{x}", (x, Y_FRONT + 0.03, FLOOR + 0.115), 0.035, 0.05, "plastic", axis="Y", seg=14, bev=0.005)
        box_mm(f"socket_lid_{x}", x - 0.036, x + 0.036, Y_FRONT + 0.055, Y_FRONT + 0.062, FLOOR + 0.10, FLOOR + 0.15,
               "plastic")
    # front position lamps (white) in the upper corners, stalk marker lamps out to the sides
    part("CHASSIS", "lamps")
    for s in (-1, 1):
        box_mm(f"front_lamp_body_{s}", s * 1.02, s * 1.14, Y_FRONT - 0.005, Y_FRONT + 0.025, 3.86, 3.92, "lamp_body",
               bev=0.006)
        box_mm(f"front_lamp_lens_{s}", s * 1.03, s * 1.13, Y_FRONT + 0.025, Y_FRONT + 0.03, 3.868, 3.912,
               "lens_white_o")
        # rubber stalk (outline marker) at the top front corner, lens white forward / red backward
        cyl(f"stalk_base_{s}", (s * 1.278, Y_FRONT - 0.20, 3.86), 0.022, 0.03, "rubber", axis="X", seg=10)
        rod(f"stalk_arm_{s}", (s * 1.28, Y_FRONT - 0.20, 3.86), (s * 1.38, Y_FRONT - 0.20, 3.92), 0.012, "rubber",
            seg=8)
        box_mm(f"stalk_lamp_{s}", s * 1.37, s * 1.43, Y_FRONT - 0.235, Y_FRONT - 0.165, 3.90, 3.96, "lamp_body",
               bev=0.006)
        box_mm(f"stalk_lens_w_{s}", s * 1.375, s * 1.425, Y_FRONT - 0.166, Y_FRONT - 0.162, 3.905, 3.955,
               "lens_white_o")
        box_mm(f"stalk_lens_r_{s}", s * 1.375, s * 1.425, Y_FRONT - 0.238, Y_FRONT - 0.234, 3.905, 3.955, "lens_red_o")
    part("CHASSIS", "body")


def top_rails_and_roof():
    part("CHASSIS", "body")
    sec = [(1.16, ROOF - 0.035), (1.272, ROOF - 0.035), (1.272, TOPRAIL_Z + 0.03), (1.262, TOPRAIL_Z),
           (1.19, TOPRAIL_Z), (1.19, TOPRAIL_Z + 0.02), (1.16, TOPRAIL_Z + 0.02)]
    for s in (-1, 1):
        pts = [(s * a, b) for a, b in sec]
        if s < 0:
            pts = list(reversed(pts))
        r = extrude_poly(f"top_rail_{s}", pts, LEN - 0.10, "alu_extr", plane="XZ", origin=(0, Y_FRONT - 0.05, 0),
                         normal_sign=-1)
        r.data.shade_flat()
        # rain gutter groove line
        box_mm(f"top_rail_groove_{s}", s * 1.2722, s * 1.2735, Y_REAR + 0.06, Y_FRONT - 0.06, 3.905, 3.912, "gap")
    # roof tarp over bows every ~0.75 m: sag 10 mm between bows, edge wraps over the top rails
    nb = 18
    ys = []
    for k in range(nb):
        ya, yb = Y_FRONT - 0.13 - k * (LEN - 0.25) / nb, Y_FRONT - 0.13 - (k + 1) * (LEN - 0.25) / nb
        for j in range(4):
            ys.append((ya + (yb - ya) * j / 4, j / 4))
    ys.append((Y_REAR + 0.12, 0.0))
    xs = [-1.274, -1.262, -1.22, -0.8, -0.4, 0.0, 0.4, 0.8, 1.22, 1.262, 1.274]
    zx = {-1.274: ROOF - 0.08, -1.262: ROOF - 0.018, 1.262: ROOF - 0.018, 1.274: ROOF - 0.08}
    segs = 6      # 6 roof panels (UV islands), cut on bow ridges
    for p in range(segs):
        sl = ys[p * len(ys) // segs: (p + 1) * len(ys) // segs + 1]
        rows = []
        for y, t in sl:
            sag = 0.010 * math.sin(math.pi * t)
            row = []
            for x in xs:
                z = zx.get(x, ROOF - 0.004 - sag * (1 - (abs(x) / 1.22) ** 4))
                row.append(V((x, y, z)))
            rows.append(row)
        sheet(f"roof_tarp_{p}", rows, "roof_tarp", flip=True, smooth=True, sharp=50)


def rear_portal_and_doors():
    part("CHASSIS", "body")
    yo = Y_REAR
    for s in (-1, 1):
        box_mm(f"rear_post_{s}", s * POST_IN, s * 1.275, yo, yo + 0.12, FLOOR + 0.02, ROOF - 0.005, "galv", bev=0.006)
        # contour marking (red) on the post faces
        box_mm(f"contour_rear_post_{s}", s * 1.19, s * 1.24, yo - 0.0012, yo - 0.0002, FLOOR + 0.10, 3.82, "reflex_red")
        # hinge barrels on the post (4)
        for z in (1.55, 2.30, 3.05, 3.70):
            cyl(f"hinge_barrel_{s}_{z}", (s * (POST_IN + 0.012), yo - 0.014, z), 0.016, 0.085, "galv", axis="Z",
                seg=10)
        # curtain tension pole + ratchet at the rear post (inside the curtain edge)
        cyl(f"tension_pole_{s}", (s * 1.235, yo + 0.155, 2.45), 0.03, 2.62, "galv", axis="Z", seg=12)
        box_mm(f"tension_ratchet_{s}", s * 1.20, s * 1.272, yo + 0.12, yo + 0.19, 1.34, 1.46, "galv", bev=0.008)
        rod(f"tension_lever_{s}", (s * 1.262, yo + 0.155, 1.40), (s * 1.262, yo + 0.155, 1.72), 0.012, "galv", seg=8)
        # upper rear outline marker (red) on the post top
        part("CHASSIS", "lamps")
        box_mm(f"rear_marker_body_{s}", s * 1.15, s * 1.255, yo - 0.03, yo, 3.905, 3.975, "lamp_body", bev=0.006)
        box_mm(f"rear_marker_lens_{s}", s * 1.16, s * 1.245, yo - 0.035, yo - 0.03, 3.912, 3.968, "lens_red_o")
        part("CHASSIS", "body")
    box_mm("rear_header", -POST_IN, POST_IN, yo, yo + 0.12, DOOR_Z1 + 0.01, ROOF - 0.005, "galv", bev=0.006)
    box_mm("contour_rear_header", -1.10, 1.10, yo - 0.0012, yo - 0.0002, 3.905, 3.955, "reflex_red")
    # lower horizontal of the rear full contour (UN R48 6.21: full contour at the rear of O3/O4 wider than 2.10 m),
    # red on the sill face, broken at the 4 door keepers
    xs = [-1.17, -0.90, -0.82, -0.30, -0.22, 0.22, 0.30, 0.82, 0.90, 1.17]
    for j in range(0, len(xs), 2):
        box_mm(f"contour_rear_sill_{j}", xs[j], xs[j + 1], Y_REAR + 0.0105, Y_REAR + 0.0118, 1.17, 1.22,
               "reflex_red")
    for s, sd in ((1, "RR"), (-1, "RL")):
        part(f"DOOR_{sd}", "body")
        x0, x1 = s * 0.003, s * (POST_IN - 0.004)
        lo, hi = min(x0, x1), max(x0, x1)
        box_mm(f"door_panel_{sd}", lo + 0.03, hi - 0.03, DOOR_FACE, DOOR_FACE + 0.035, DOOR_Z0 + 0.03, DOOR_Z1 - 0.03,
               "trl_paint")
        # aluminium edge frame
        for nm, a, b, c, d in (("b", lo, hi, DOOR_Z0, DOOR_Z0 + 0.035), ("t", lo, hi, DOOR_Z1 - 0.035, DOOR_Z1),
                               ("i", lo, lo + 0.035, DOOR_Z0, DOOR_Z1), ("o", hi - 0.035, hi, DOOR_Z0, DOOR_Z1)):
            box_mm(f"door_frame_{sd}_{nm}", a, b, DOOR_FACE - 0.003, DOOR_FACE + 0.035, c, d, "alu_extr", bev=0.003)
        # stiffener grooves (two horizontal)
        for z in (2.15, 2.95):
            box_mm(f"door_groove_{sd}_{z}", lo + 0.04, hi - 0.04, DOOR_FACE - 0.0008, DOOR_FACE, z - 0.004, z + 0.004,
                   "gap")
        # hinges (4 straps)
        for z in (1.55, 2.30, 3.05, 3.70):
            box_mm(f"hinge_strap_{sd}_{z}", s * (POST_IN - 0.22), s * (POST_IN + 0.004), DOOR_FACE - 0.010,
                   DOOR_FACE - 0.003, z - 0.025, z + 0.025, "galv", bev=0.002)
            for k in range(2):
                cyl(f"hinge_bolt_{sd}_{z}_{k}", (s * (POST_IN - 0.06 - 0.09 * k), DOOR_FACE - 0.013, z), 0.008, 0.008,
                    "steel", axis="Y", seg=6)
        # 2 lock bars per leaf: tube, cams top/bottom, guides, handle + catch
        for xb in (s * 0.26, s * 0.86):
            yb = DOOR_FACE - 0.004 - 0.0135
            cyl(f"lockbar_{sd}_{xb:.2f}", (xb, yb, (FLOOR + DOOR_Z1 + 0.04) / 2), 0.0135, DOOR_Z1 + 0.04 - FLOOR,
                "galv", axis="Z", seg=10)
            for z in (FLOOR + 0.05, DOOR_Z1 + 0.005):
                box_mm(f"lockcam_{sd}_{xb:.2f}_{z:.2f}", xb - 0.025, xb + 0.025, yb - 0.018, yb + 0.012, z - 0.025,
                       z + 0.025, "galv", bev=0.004)
            for z in (1.75, 2.60, 3.40):
                box_mm(f"lockguide_{sd}_{xb:.2f}_{z}", xb - 0.03, xb + 0.03, yb - 0.02, DOOR_FACE, z - 0.02, z + 0.02,
                       "galv", bev=0.003)
            hz = 1.62
            hx = xb - s * 0.32 if abs(xb) > 0.5 else xb + s * 0.30
            rod(f"lockhandle_{sd}_{xb:.2f}", (xb, yb - 0.02, hz), (hx, yb - 0.03, hz), 0.011, "galv", seg=8)
            box_mm(f"lockcatch_{sd}_{xb:.2f}", hx - 0.03, hx + 0.03, yb - 0.035, DOOR_FACE, hz - 0.04, hz + 0.03, "galv",
                   bev=0.003)
    part("CHASSIS", "body")
    # keepers on the sill / header
    for xb in (-0.86, -0.26, 0.26, 0.86):
        box_mm(f"keeper_lo_{xb}", xb - 0.035, xb + 0.035, Y_REAR - 0.035, Y_REAR, FLOOR - 0.02, FLOOR + 0.05, "galv",
               bev=0.004)
        box_mm(f"keeper_hi_{xb}", xb - 0.035, xb + 0.035, Y_REAR - 0.035, Y_REAR, DOOR_Z1 - 0.02, DOOR_Z1 + 0.05, "galv",
               bev=0.004)
    box_mm("door_centre_seal", -0.0035, 0.0035, DOOR_FACE + 0.002, DOOR_FACE + 0.03, DOOR_Z0, DOOR_Z1, "rubber")
    # cargo bay seen through the open doors: plywood floor + an inward-facing dark liner (the curtain is a single
    # sheet; without the liner the bay would be see-through from inside)
    yi0, yi1 = Y_FRONT - 0.03, DOOR_FACE + 0.036
    rows = [[V((x, y, FLOOR)) for x in (-1.24, 1.24)] for y in (yi0, yi1)]
    sheet("cargo_floor", rows, "plywood", flip=True, smooth=False)
    xi, zt = 1.236, TOPRAIL_Z - 0.005
    for nm, pts in (("cargo_liner_l", [(-xi, yi0, FLOOR), (-xi, yi1, FLOOR), (-xi, yi1, zt), (-xi, yi0, zt)]),
                    ("cargo_liner_r", [(xi, yi1, FLOOR), (xi, yi0, FLOOR), (xi, yi0, zt), (xi, yi1, zt)]),
                    ("cargo_liner_top", [(-xi, yi1, zt), (xi, yi1, zt), (xi, yi0, zt), (-xi, yi0, zt)]),
                    ("cargo_liner_front", [(xi, yi0, FLOOR), (-xi, yi0, FLOOR), (-xi, yi0, zt), (xi, yi0, zt)])):
        bm = bmesh.new()
        bm.faces.new([bm.verts.new(p) for p in reversed(pts)])   # wound to face into the bay
        me = bpy.data.meshes.new(nm)
        bm.to_mesh(me)
        bm.free()
        me.uv_layers.new(name="UVMap")
        me.materials.append(G.mat("interior"))
        G.link(bpy.data.objects.new(nm, me))


def rear_lamps_and_rup():
    part("CHASSIS", "rear")
    yo = Y_REAR
    # RUP (UN R58): galvanised bar, lower edge 0.42 m, width 2.40 m, struts + braces to the beams
    box_mm("rup_bar", -1.20, 1.20, yo + 0.02, yo + 0.12, 0.42, 0.55, "galv", bev=0.008)
    for s in (-1, 1):
        box_mm(f"rup_strut_{s}", s * BEAM_X - 0.05, s * BEAM_X + 0.05, yo + 0.06, yo + 0.14, 0.55,
               beam_bottom(yo + 0.2) + 0.01, "galv", bev=0.004)
        rod(f"rup_brace_{s}", (s * BEAM_X, yo + 0.12, 0.52), (s * BEAM_X, yo + 0.85, beam_bottom(yo + 0.85) + 0.01),
            0.025, "galv", seg=8)
        # R70 rear marking plates on the bar
        G.plate_uv(box_mm(f"r70_plate_{s}", s * 0.60, s * 1.165, yo + 0.016, yo + 0.020, 0.43, 0.54, "r70"),
                   facing=-1)     # normalised UV: the red border must frame the plate, not tile across it
        # lamp panel under the sill
        box_mm(f"lamp_panel_{s}", s * 0.60, s * 1.24, yo + 0.03, yo + 0.04, 0.80, 1.08, "trl_chassis", bev=0.003)
        box_mm(f"lamp_panel_side_{s}", s * 1.23, s * 1.24, yo + 0.04, yo + 0.20, 0.80, 1.08, "trl_chassis")
    # combination lamps (LED): housing + chambers; L/R mirrored, rear fog + reverse
    part("CHASSIS", "lamps")
    for s, sd in ((-1, "L"), (1, "R")):
        x0, x1 = s * 0.66, s * 1.18
        lo, hi = min(x0, x1), max(x0, x1)
        zc = 0.94
        box_mm(f"rear_lamp_body_{sd}", lo, hi, yo - 0.045, yo + 0.03, zc - 0.085, zc + 0.085, "lamp_body", bev=0.01)
        # one continuous multi-colour lens moulding (as on real trailer combination lamps): the sections butt against
        # each other with no bezel between them and share ONE pillow-crowned outer surface; only a thin housing lip
        # frames the whole lens. From the outside in: indicator (amber), tail/stop (red), reverse (white, right) or
        # fog (red, left only). Section widths 30/25/25/20 % of the lens.
        la, lb = lo + 0.018, hi - 0.018
        za, zb = zc - 0.066, zc + 0.066
        box_mm(f"rear_lamp_lip_{sd}", lo + 0.008, hi - 0.008, yo - 0.052, yo - 0.044, zc - 0.074, zc + 0.074,
               "lamp_body", bev=0.003)
        fr = [0.30, 0.25, 0.25, 0.20]
        kinds = ["lens_amber_o", "lens_red_o", "lens_red_o", "lens_white_o" if s > 0 else "lens_red_o"]
        names = ["ind", "tail", "stop", "rev" if s > 0 else "fog"]
        W = lb - la
        edge = 0.0
        for k, (mname, nm) in enumerate(zip(kinds, names)):
            w = W * fr[k]
            if s > 0:          # outside = +x
                b, a = lb - edge, lb - edge - w
            else:
                a, b = la + edge, la + edge + w
            edge += w
            box_mm(f"rear_lens_{nm}_{sd}", a, b, yo - 0.056, yo - 0.048, za, zb, mname, bev=0.0015, seg=1)
            nx, nz = max(3, int(round(10 * w / (W * 0.25)))), 6
            rows = []
            for iz in range(nz + 1):
                tz = iz / nz
                row = []
                for ix in range(nx + 1):
                    x = a + (b - a) * ix / nx
                    tx = (x - la) / W            # crown over the WHOLE lens, continuous across the sections
                    crown = 0.004 * math.sin(math.pi * tx) ** 0.6 * math.sin(math.pi * tz) ** 0.6
                    row.append(V((x, yo - 0.0562 - crown, za + 0.002 + (zb - za - 0.004) * tz)))
                rows.append(row)
            sheet(f"rear_lens_{nm}_{sd}_face", rows, mname, flip=False, smooth=True)
            # LED emitters seen through the lens
            for j in range(3):
                zz = zc - 0.04 + 0.04 * j
                cyl(f"rear_led_{nm}_{sd}_{j}", ((a + b) / 2, yo - 0.0545, zz), 0.010, 0.002, mname, axis="Y", seg=12)
        # triangular retro-reflector (red) inboard of the lamp
        xt = s * 0.54
        tri = [(xt - 0.075, 0.82), (xt + 0.075, 0.82), (xt, 0.95)]
        extrude_poly(f"tri_reflector_{sd}", tri, 0.006, "lens_red_o", plane="XZ", origin=(0, yo + 0.026, 0),
                     normal_sign=-1).data.shade_flat()
    # number plate (fictional PL trailer plate) + plate lamp
    part("CHASSIS", "rear")
    box_mm("plate_holder", -0.29, 0.29, yo + 0.026, yo + 0.034, 0.79, 0.96, "trl_chassis", bev=0.004)
    pl = box_mm("plate_rear", -0.26, 0.26, yo + 0.018, yo + 0.026, 0.81, 0.924, "plate")
    G.plate_uv(pl, facing=-1)
    part("CHASSIS", "lamps")
    box_mm("plate_lamp_body", -0.06, 0.06, yo - 0.02, yo + 0.026, 0.94, 0.975, "lamp_body", bev=0.006)
    box_mm("plate_lamp_lens", -0.045, 0.045, yo - 0.012, yo + 0.01, 0.936, 0.940, "lens_white_o")
    # side marker lamps (amber LED) on the rail, ~every 2.6 m (ECE R48 spacing <= 3 m), + amber reflectors
    for s in (-1, 1):
        for k, yy in enumerate([Y_FRONT - 0.65, -1.4, -4.1, AXLES[1], -10.4, Y_REAR + 0.45]):
            box_mm(f"side_marker_brk_{s}_{k}", s * (RAIL_OUT - 0.06), s * (RAIL_OUT - 0.04), yy - 0.03, yy + 0.03,
                   1.03, 1.085, "galv")
            box_mm(f"side_marker_body_{s}_{k}", s * (RAIL_OUT - 0.045), s * (RAIL_OUT - 0.005), yy - 0.055,
                   yy + 0.055, 1.025, 1.07, "lamp_body", bev=0.004)
            box_mm(f"side_marker_lens_{s}_{k}", s * (RAIL_OUT - 0.005), s * (RAIL_OUT - 0.002), yy - 0.045,
                   yy + 0.045, 1.032, 1.063, "lens_amber_o")
    part("CHASSIS", "frame")


# ---------------------------------------------------------------- curtains
def strap_positions():
    return [STRAP_Y0 + (STRAP_Y1 - STRAP_Y0) * k / (N_STRAPS - 1) for k in range(N_STRAPS)]


def curtain_offset(y, z, bays, hi=False):
    """Outward offset of the curtain from CURT_X at (y, z). Low = bulge between straps + slack wave + hem;
    hi adds the normal-map detail: buckle fan creases, roller scallops at the top, fine wrinkles."""
    ys = bays["ys"]
    # bay index + param
    k = 0
    while k < len(ys) - 2 and y < ys[k + 1]:
        k += 1
    ya, yb = ys[k], ys[k + 1]
    t = (ya - y) / (ya - yb) if ya != yb else 0.0
    t = min(max(t, 0.0), 1.0)
    # strap band (45 mm) stays flat against the strap
    hw = 0.0225 / abs(ya - yb)
    tt = min(max((t - hw) / (1 - 2 * hw), 0.0), 1.0)
    env = smooth01(HEM_TOP - 0.02, 1.70, z) * (1.0 - 0.65 * smooth01(CURT_Z1 - 0.40, CURT_Z1 - 0.02, z))
    off = bays["amp"][k] * math.sin(math.pi * tt) ** 1.2 * env
    off += 0.0028 * math.sin(2 * math.pi * y / 3.3 + bays["phi"]) * math.sin(math.pi * (z - CURT_Z0) / (CURT_Z1 - CURT_Z0))
    # bottom hem (double layer + pocket), top hem
    if z < HEM_TOP:
        off += 0.003 * smooth01(CURT_Z0, CURT_Z0 + 0.012, z)
    if z > CURT_Z1 - 0.08:
        off += 0.002
    if not hi:
        return off
    # Normal-map detail is sized for the game atlas (~170-340 px/m): features narrower than ~2 cm vanish.
    # 1) tension fans: soft diagonal ridges from each buckle (the ratchet pulls the hem down at one point)
    for ysx in (ya, yb):
        if ysx not in bays["strapset"]:
            continue
        dy = y - ysx
        if abs(dy) > 0.60 or z > 2.05:
            continue
        for ang, amp in ((52, 1.0), (68, 0.6), (112, 0.6), (128, 1.0)):
            a = math.radians(ang)
            d = V((math.cos(a), math.sin(a)))
            p = V((dy, z - HEM_TOP))
            along = p.dot(d)
            if along <= 0.0 or along > 0.62:
                continue
            dist = abs(p.x * d.y - p.y * d.x)
            f = bays["fan"][hash((round(ysx, 3), ang)) % 7]
            off += 0.0095 * amp * f * math.exp(-(dist / 0.022) ** 2) * (1 - along / 0.62) ** 1.5
    # 2) slack folds: 2-4 soft vertical waves per bay in the upper two thirds (fabric not fully tensioned)
    nf = bays["folds"][k]
    w = smooth01(1.55, 2.30, z) * (1 - 0.5 * smooth01(3.35, CURT_Z1 - 0.10, z))
    off += 0.0045 * w * math.sin(math.pi * tt) * math.sin(2 * math.pi * nf * tt + bays["fphi"][k] + 1.3 * (z - 2.0))
    # 3) roller scallops: the curtain hangs from rollers every 0.31 m
    if z > CURT_Z1 - 0.36:
        w = smooth01(CURT_Z1 - 0.36, CURT_Z1 - 0.03, z)
        off += 0.0070 * w * (0.5 - 0.5 * math.cos(2 * math.pi * (y + 0.07) / 0.31))
    # 4) low-frequency waviness (handling, wind)
    off += 0.0012 * math.sin(y * 4.1 - z * 6.3 + bays["phi"]) * smooth01(1.4, 2.0, z) * (1 - smooth01(3.2, 3.7, z))
    return off


def curtain_lift(y, z, bays):
    """Vertical hem scallop: each ratchet pulls the hem down at its strap; between two buckles the tensioned fabric
    rides up as a shallow catenary (8-15 mm at mid bay, fading out 0.55 m above the hem)."""
    ys = bays["ys"]
    k = 0
    while k < len(ys) - 2 and y < ys[k + 1]:
        k += 1
    ya, yb = ys[k], ys[k + 1]
    t = min(max((ya - y) / (ya - yb), 0.0), 1.0) if ya != yb else 0.0
    end = k == 0 or k == len(ys) - 2       # front post / rear pole bays are held along their edge
    rise = (0.0 if end else bays["lift"][k]) * math.sin(math.pi * t) ** 1.4
    return rise * (1.0 - smooth01(CURT_Z0, CURT_Z0 + 0.55, z))


def soft_cap(off, lim=HW - 0.0015 - CURT_X):
    """Keep the fabric inside the 2.55 m envelope: outward offsets saturate smoothly at lim (tanh)."""
    return lim * math.tanh(off / lim) if off > 0 else off


def curtain_side(s, sd, hi=False):
    part(f"CURTAIN_{sd}", "curtain")
    straps = strap_positions()
    ys = [CURT_Y0] + straps + [CURT_Y1]
    rng = random.Random(77 + (s > 0))
    bays = {"ys": ys, "straps": straps, "strapset": set(straps), "amp": [(0.013 + 0.007 * rng.random()) for _ in ys],
            "folds": [rng.choice((2, 3, 3, 4)) for _ in ys], "fphi": [rng.random() * 6.28 for _ in ys],
            "phi": rng.random() * 6.28, "fan": [0.6 + 0.6 * rng.random() for _ in range(7)],
            "lift": [0.008 + 0.007 * rng.random() for _ in ys]}
    bays["amp"][0] *= 0.6
    bays["amp"][-2] *= 0.6
    nseg = 22 if hi else 8
    hw = 0.0225
    cols = set()
    for k in range(len(ys) - 1):
        a, b = ys[k], ys[k + 1]
        a2 = a - hw if k > 0 else a
        b2 = b + hw if k < len(ys) - 2 else b
        for j in range(nseg + 1):
            cols.add(round(a2 + (b2 - a2) * j / nseg, 5))
        cols.add(round(a, 5))
        cols.add(round(b, 5))
    yl = sorted(cols, reverse=True)
    if hi:
        zl = [CURT_Z0 + (CURT_Z1 - CURT_Z0) * (i / 140) for i in range(141)]
    else:
        zl = [CURT_Z0, CURT_Z0 + 0.012, HEM_TOP - 0.012, HEM_TOP, 1.35, 1.43, 1.53, 1.65, 1.79, 1.95,
              2.15, 2.38, 2.62, 2.86, 3.10, 3.30, 3.46, 3.58, 3.67, 3.74, 3.80, 3.815,
              3.84, 3.86, CURT_Z1]
    # 4 panels per side (UV islands of ~3.4 x 2.7 m), cut along strap centre lines: the strap hides the shading seam
    cuts = [0] + [yl.index(round(straps[k], 5)) for k in (5, 11, 17)] + [len(yl) - 1]
    obs = []
    for p in range(4):
        sl = yl[cuts[p]: cuts[p + 1] + 1]
        # low mesh carries the folds too (one shared shape function): the normal map holds only the residual
        rows = [[V((s * (CURT_X + soft_cap(curtain_offset(y, z, bays, True))), y, z + curtain_lift(y, z, bays)))
                 for y in sl] for z in zl]
        nm = f"curtain{'_hi' if hi else ''}_{sd}_{p}"
        ob = sheet(nm, rows, "curtain_pvc", flip=(s > 0), smooth=True, sharp=None)
        if hi:
            ob["bake_only"] = True
        obs.append(ob)
    if hi:
        return obs
    # front edge: curtain wraps the front post (vertical strip), rear edge: wrapped round the tension pole
    box_mm(f"curtain_front_strip_{sd}", s * 1.262, s * 1.272, Y_FRONT - 0.10, Y_FRONT - 0.07, CURT_Z0 + 0.02,
           CURT_Z1 - 0.02, "alu_extr")
    cyl(f"curtain_rear_wrap_{sd}", (s * 1.248, Y_REAR + 0.115, (CURT_Z0 + CURT_Z1) / 2), 0.022, CURT_Z1 - CURT_Z0,
        "curtain_pvc", axis="Z", seg=10)
    # straps + ratchet buckles hooked under the side rail lip
    for k, ysx in enumerate(straps):
        x = s * (CURT_X + 0.0022)
        box_mm(f"strap_{sd}_{k}", min(x, x + s * 0.0022), max(x, x + s * 0.0022), ysx - 0.0225, ysx + 0.0225,
               HEM_TOP - 0.04, CURT_Z1 - 0.01, "strap")
        bx = s * (CURT_X + 0.004)
        box_mm(f"buckle_{sd}_{k}", min(bx, bx + s * 0.016), max(bx, bx + s * 0.016), ysx - 0.028, ysx + 0.028, 1.105,
               HEM_TOP - 0.03, "galv", bev=0.002, seg=1)
        box_mm(f"buckle_lever_{sd}_{k}", min(bx + s * 0.016, bx + s * 0.022), max(bx + s * 0.016, bx + s * 0.022),
               ysx - 0.018, ysx + 0.018, 1.14, HEM_TOP - 0.045, "galv", bev=0.0015, seg=1)
        box_mm(f"buckle_hook_{sd}_{k}", min(s * 1.205, s * (CURT_X + 0.004)), max(s * 1.205, s * (CURT_X + 0.004)),
               ysx - 0.012, ysx + 0.012, 1.075, 1.085, "galv")
    # roller trolleys peeking under the top rail
    return obs


def build(hi=True):
    """Build the whole trailer. Returns {'pieces': [...], 'high_only': [...]}."""
    G.STATE["coll"] = bpy.context.scene.collection
    materials()
    before = {o.name for o in bpy.data.objects}
    steps = [frame, axles_and_suspension, wheels, mudguards, side_guards, underfloor_equipment, landing_gear, front_wall,
             top_rails_and_roof, rear_portal_and_doors, rear_lamps_and_rup]
    for fn in steps:
        b0 = {o.name for o in bpy.data.objects}
        fn()
        tag_new(b0)
    for s, sd in ((-1, "L"), (1, "R")):
        b0 = {o.name for o in bpy.data.objects}
        curtain_side(s, sd)
        tag_new(b0)
    high = []
    if hi:      # left only: the right curtain shares the left one's UVs (normal map) in the game export
        b0 = {o.name for o in bpy.data.objects}
        high += curtain_side(-1, "L", hi=True)
        tag_new(b0)
    # wheel part names: wheel_1L_* -> WHEEL_1L
    for o in bpy.data.objects:
        if o.name.startswith("wheel_"):
            o["part"] = "WHEEL_" + o.name.split("_")[1]
            o["group"] = "wheels"
    pieces = [o for o in bpy.data.objects if o.type == "MESH" and o.name not in before and not o.get("bake_only")]
    return {"pieces": pieces, "high_only": high}
