"""TRAKT cab + frame-mounted lower fairing (concept B, A3/A4, round 3 after visual review R2).

Shape parameters live in CFG (profiles in metres, see ART_BIBLE exterior section) so a different
concept/front can be tried by editing data, not code. Interior alignment: the door opening, glass and
step data are written to art-source/truck/exterior/door_interface.json (door_interface()) for the
interior generator; eye point unchanged (-0.55, 0.45, 2.50).

R2 #2 layout (real EU cab-over): front wheel under the front half of the door, a fixed body-colour corner
panel ahead of the door, door rear shut line 0.60 m behind the axle, the door's lower rear corner drops
over the top step as a skirt, three steps behind the wheel in a body-colour step well.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import geom as G
from geom import (CAB_BACK_Y, CAB_HALF_W, ROOF_Z, WHEEL_Z, EYE, Loft, V, box, box_mm, cyl, rod, sphere, tube,
                  lerp_tab, set_group, boolean, bevel, extrude_poly, rrect, arch)

RAKE = 19.0
TAN = math.tan(math.radians(RAKE))
WS_Z0, WS_Z1 = 2.06, 2.96            # visible glass bottom/top
# black ceramic frit inside the visible opening (A6: bottom 35 -> 75 mm, real screens 60-120 mm; hides the cowl, the
# wiper spindles and the dash top edge from outside and from the seat - REVIEW r2 §2 #2). Published in
# glass_interface.json; the interior prints the same band on the inner face.
FRIT_BOTTOM, FRIT_TOP, FRIT_SIDE = 0.075, 0.10, 0.028
WS_Y0 = 1.405                        # windscreen outer surface at z = 2.04
CAB_Z0 = 1.225                       # cab shell lower edge = tilt line
FAIR_TOP = 1.21                      # frame-mounted lower fairing top
BELT_Z, WIN_TOP = 2.17, 2.94         # side glass (interior: 2.17..2.96)
DOOR_REAR = -0.60                    # door rear shut line (R2 #2: was -0.28, moved 0.32 m rearward)
DOOR_SEAL = 0.04                     # shut line -> aperture edge (seal overlap)
DOOR_FRONT_LOW = 0.80                # door front shut line below the corner panel (fixed panel ahead of it)
DOOR_KINK_Z = (1.90, 2.14)           # front shut line runs diagonally from the corner panel up to the A-pillar
WIN_REAR = DOOR_REAR + DOOR_SEAL + 0.07   # door glass rear edge (-0.49; interior: aperture rear + 0.07)
SKIRT_Z = 0.98                       # door skirt bottom (lower rear corner of the door, covers the top step)
ARCH_R = 0.60                        # front wheel arch radius (tyre r 0.538 + 6 cm)
ARCH_OUT = ARCH_R + 0.035            # outer edge of the arch flare
FAIR_BACK = -1.14                    # lower fairing (step boxes) ends 0.19 m behind the cab back wall
# steps behind the front wheel: (z of tread top, y rear, y front); widths 0.42 / 0.485 / 0.60 m
STEPS = ((0.45, -1.08, -0.66), (0.79, -1.07, -0.585), (1.10, -1.06, -0.46))
STEP_DEPTH = 0.21                    # tread depth (x)
HANDLE_Y = (-0.83, -0.74)            # recessed grab handle in the fixed rear side panel, behind the door
PIVOT = Vector((0.0, 1.42, 1.19))    # cab tilt pivot (front cab mount on the frame horns)


def ws_y(z):
    return WS_Y0 - (z - 2.04) * TAN


def arch_y(z, r=ARCH_OUT, rear=True):
    """y of the arch flare outer edge at height z (behind or ahead of the front axle)."""
    dz = z - WHEEL_Z
    d = math.sqrt(max(r * r - dz * dz, 0.0))
    return -d if rear else d


CFG = {
    # flush header (R2 #8: the forward lip at z 3.0-3.13 read as a 90s 'beak'); windscreen rake eases into
    # the roof curve
    "front": [(CAB_Z0, 1.462), (1.60, 1.455), (1.90, 1.440), (1.985, 1.432), (2.000, 1.418), (2.04, WS_Y0),
              (2.98, ws_y(2.98)), (3.10, 1.052), (3.30, 1.012), (3.50, 0.980), (3.70, 0.952), (ROOF_Z, 0.920)],
    "w": [(CAB_Z0, CAB_HALF_W), (2.70, CAB_HALF_W), (3.50, CAB_HALF_W - 0.02), (ROOF_Z, CAB_HALF_W - 0.045)],
    "rf": [(CAB_Z0, 0.32), (1.985, 0.34), (2.04, 0.36), (2.98, 0.40), (ROOF_Z, 0.46)],
    "rb": 0.10,
    "roof_r": 0.40,
    # front face (front-projection params: x = lateral, wraps round the corner beyond the flat part)
    # TRAKT face: the grille is the brand's T (wide upper bar, stem widening downwards like a road in
    # perspective); headlamps sit under the bar ends, their inner edges parallel to the 'road' edges.
    # R2 #3: slimmer lamp (0.23 m tall), inner edge still parallel to the grille 'road' edge
    "lamp": [(0.90, 1.30), (1.30, 1.30), (1.30, 1.53), (0.72, 1.53)],
    # DRL light guides inside the lens: T-bar along the top + road edge down the inner side (right lamp)
    "drl": [((0.752, 1.508), (1.272, 1.508)), ((0.758, 1.492), (0.918, 1.318))],
    "stem": [(-0.80, 1.235), (0.80, 1.235), (0.50, 1.64), (-0.50, 1.64)],   # road: narrow at the top
    "bar": [(-0.84, 1.625), (0.84, 1.625), (0.84, 1.86), (-0.84, 1.86)],    # T-bar
    "bumper_road": [(-0.86, 0.885), (0.86, 0.885), (0.806, 1.21), (-0.806, 1.21)],
    "emblem_z": 1.742, "emblem_w": 0.22,
    # one grille field, three bar weights: 2 thick body-colour bars in the T-bar, 3 thin graphite bars in the
    # stem (pitch opening downwards), fine honeycomb behind everything. (z_centre, height, depth, material)
    "grille_bars": [(1.800, 0.050, 0.040, "paint"), (1.684, 0.044, 0.046, "paint"),
                    (1.548, 0.020, 0.058, "trim_graphite"), (1.448, 0.020, 0.058, "trim_graphite"),
                    (1.330, 0.020, 0.058, "trim_graphite")],
    "bumper_split": 0.67,             # body colour above, dark textured lower bumper below
    "side_split": 0.55,               # body colour on the step boxes / corner above, dark skirt below
    "ws_bottom_x": 1.27, "ws_top_x": 1.15,
}
CAB = None    # Loft of the cab shell
LOW = None    # Loft of the lower fairing


def mirror_poly(poly):
    return [(-x, z) for x, z in reversed(poly)]


def full_grille(poly_r):
    left = [(-x, z) for x, z in reversed(poly_r[1:-1])]
    return poly_r[:-1] + [(0.0, poly_r[-1][1])] + left


def win_front(z):
    """Side window front edge (y): just onto the corner arc, parallel to the A-pillar."""
    yf, yb, w, rf, rb = CAB.sec(z)
    return yf - rf + 0.15


def door_front_y(z):
    """Door front shut line: y 0.80 behind the fixed body-colour corner panel, a diagonal from z 1.90 up to
    the A-pillar at the belt, then parallel to the A-pillar."""
    za, zb = DOOR_KINK_Z
    ya = DOOR_FRONT_LOW
    yb = win_front(zb) + 0.04
    if z <= za:
        return ya
    if z <= zb:
        return ya + (yb - ya) * (z - za) / (zb - za)
    return win_front(z) + 0.04


# ---------------------------------------------------------------- shell
def cab_shell():
    global CAB
    set_group("cab")
    CAB = Loft(CFG["front"], CAB_BACK_Y, CFG["w"], CFG["rf"], CFG["rb"], CAB_Z0, ROOF_Z, roof_r=CFG["roof_r"],
               arc_n=10, step=0.05, flat_n=5, roof_n=9)
    sh = CAB.build("cab_shell", "paint", sharp=50, cap_bottom=False)
    sh.data.materials.append(G.mat("interior"))
    so = sh.modifiers.new("solid", "SOLIDIFY")
    so.thickness = 0.03
    so.offset = -1
    so.material_offset = 1
    so.material_offset_rim = 1
    so.use_even_offset = True
    G.apply_mods(sh)
    # openings: windscreen, side windows, headlamp pockets, grille pocket, recessed grab handles
    cut = []
    xb, xt = CFG["ws_bottom_x"], CFG["ws_top_x"]
    cut.append(CAB.quad_patch("cut_ws", "gap", "front", [(-xb, WS_Z0), (xb, WS_Z0), (xt, WS_Z1), (-xt, WS_Z1)],
                              off=-0.10, thick=0.25, nu=40, nv=8))
    for s in (-1, 1):
        cut.append(CAB.quad_patch(f"cut_win_{s}", "gap", "side",
                                  [(WIN_REAR, BELT_Z), (win_front(BELT_Z), BELT_Z),
                                   (win_front(WIN_TOP), WIN_TOP), (WIN_REAR, WIN_TOP)],
                                  off=-0.10, thick=0.25, side=s, nu=28, nv=6))
        lamp = CFG["lamp"] if s > 0 else mirror_poly(CFG["lamp"])
        cut.append(CAB.poly_patch(f"cut_lamp_{s}", "lamp_inner", "front", lamp, off=-0.07, thick=0.20, sub=6))
        cut.append(CAB.patch(f"cut_handle_{s}", "plastic", "side", 1.38, 2.32, HANDLE_Y[0], HANDLE_Y[1], off=-0.06,
                             thick=0.15, side=s, nz=2, npar=2))
    for k in ("stem", "bar"):
        cut.append(CAB.poly_patch("cut_" + k, "grille_mesh", "front", CFG[k], off=-0.07, thick=0.20, sub=5))
    boolean(sh, cut)
    sh.data.shade_smooth()
    if hasattr(sh.data, "set_sharp_from_angle"):
        sh.data.set_sharp_from_angle(angle=math.radians(50))
    return sh


# ---------------------------------------------------------------- glazing
def glazing():
    set_group("cab")
    xb, xt = CFG["ws_bottom_x"], CFG["ws_top_x"]
    e = 0.012  # glass overlaps the opening
    CAB.quad_patch("windscreen", "glass", "front", [(-xb - e, WS_Z0 - e), (xb + e, WS_Z0 - e), (xt + e, WS_Z1 + e),
                                                     (-xt - e, WS_Z1 + e)], off=0.004, nu=36, nv=6)
    # black ceramic frit border (bonded flush glazing) just under the glass surface
    f = FRIT_SIDE
    CAB.quad_patch("frit_bottom", "frit", "front", [(-xb - e, WS_Z0 - e), (xb + e, WS_Z0 - e), (xb, WS_Z0 + FRIT_BOTTOM),
                                                     (-xb, WS_Z0 + FRIT_BOTTOM)], off=0.0055, nu=48, nv=1)
    CAB.quad_patch("frit_top", "frit", "front", [(-xt, WS_Z1 - FRIT_TOP), (xt, WS_Z1 - FRIT_TOP), (xt + e, WS_Z1 + e),
                                                  (-xt - e, WS_Z1 + e)], off=0.0055, nu=48, nv=2)
    for s in (-1, 1):
        a0, a1 = s * (xb + e), s * (xb - f)
        b0, b1 = s * (xt + e), s * (xt - f)
        CAB.quad_patch(f"frit_side_{s}", "frit", "front", [(a1, WS_Z0), (a0, WS_Z0), (b0, WS_Z1), (b1, WS_Z1)],
                       off=0.0055, nu=3, nv=10)
        # side glass in a black frame (door window channel)
        y0 = WIN_REAR
        # black frame as a ring (4 strips) round the door glass
        fb, ft, fr = BELT_Z - 0.03, WIN_TOP + 0.035, y0 - 0.035
        wf = lambda z: win_front(z) + 0.035
        for nm, cs in (("b", [(fr, fb), (wf(fb), fb), (wf(BELT_Z + 0.01), BELT_Z + 0.01), (fr, BELT_Z + 0.01)]),
                       ("t", [(fr, WIN_TOP - 0.01), (wf(WIN_TOP - 0.01), WIN_TOP - 0.01), (wf(ft), ft), (fr, ft)]),
                       ("r", [(fr, fb), (y0 + 0.01, fb), (y0 + 0.01, ft), (fr, ft)]),
                       ("f", [(win_front(fb) - 0.008, fb), (win_front(fb) + 0.02, fb), (win_front(ft) + 0.02, ft),
                              (win_front(ft) - 0.008, ft)])):
            CAB.quad_patch(f"win_frame_{nm}_{s}", "plastic_satin", "side", cs, off=0.002, side=s, nu=12, nv=2)
        CAB.quad_patch(f"side_glass_{s}", "glass", "side",
                       [(y0, BELT_Z), (win_front(BELT_Z), BELT_Z), (win_front(WIN_TOP), WIN_TOP), (y0, WIN_TOP)],
                       off=0.0045, side=s, nu=20, nv=6)
        CAB.gap_h(f"belt_seal_{s}", s, BELT_Z - 0.012, y0 - 0.03, win_front(BELT_Z) + 0.03, w=0.012, off=0.006,
                  m="rubber")


# ---------------------------------------------------------------- panel gaps, doors, handles
def doors_and_gaps():
    set_group("cab")
    for s in (-1, 1):
        # door front shut line: vertical behind the fixed corner panel, then a diagonal up to the A-pillar
        CAB.gap_v(f"door_gap_f_{s}", s, door_front_y, CAB_Z0 + 0.01, 3.00, w=0.012)
        CAB.gap_v(f"door_gap_r_{s}", s, DOOR_REAR, CAB_Z0 - 0.01, 3.00, w=0.012)
        CAB.gap_h(f"door_gap_t_{s}", s, 3.00, DOOR_REAR, win_front(3.0) + 0.04, w=0.012)
        # door skirt: the door's lower rear corner drops below the tilt line, behind the arch, over the top step
        CAB.patch(f"door_skirt_{s}", "paint", "side", SKIRT_Z, CAB_Z0 + 0.012, DOOR_REAR + 0.006,
                  lambda z: arch_y(min(z, WHEEL_Z + ARCH_OUT - 0.006)) - 0.008, off=-0.012, thick=0.018, side=s,
                  nz=10, npar=10)
        CAB.gap_v(f"skirt_gap_r_{s}", s, DOOR_REAR, SKIRT_Z - 0.006, CAB_Z0 + 0.01, w=0.012, off=0.0075)
        CAB.gap_h(f"skirt_gap_b_{s}", s, SKIRT_Z - 0.002, DOOR_REAR - 0.006, arch_y(SKIRT_Z) - 0.004, w=0.010,
                  off=0.0075)
        # rear side panel / roof split and the side extender line (stamping joints)
        CAB.gap_h(f"roofjoint_{s}", s, 3.30, CAB_BACK_Y + 0.12, win_front(3.30) + 0.08, w=0.005)
        # flush door handle with recess and key cylinder (near the rear edge, reachable from the steps)
        CAB.patch(f"door_handle_recess_{s}", "plastic", "side", 1.58, 1.665, DOOR_REAR + 0.06, DOOR_REAR + 0.24,
                  off=0.001, side=s, nz=2, npar=4)
        CAB.patch(f"door_handle_{s}", "plastic_satin", "side", 1.60, 1.645, DOOR_REAR + 0.075, DOOR_REAR + 0.225,
                  off=0.006, side=s, nz=1, npar=4, thick=0.008)
        p = V(CAB.side_pt(1.62, DOOR_REAR + 0.27, s, 0.002))
        cyl(f"door_lock_{s}", p, 0.011, 0.008, "satin_alu", axis="X", seg=16)
        # recessed grab handle in the fixed panel behind the door (stays inside the 2.55 m limit)
        CAB.patch(f"handle_back_{s}", "plastic", "side", 1.38, 2.32, HANDLE_Y[0], HANDLE_Y[1], off=-0.045, side=s,
                  nz=1, npar=1)
        x = s * (CAB_HALF_W - 0.02)
        hy = (HANDLE_Y[0] + HANDLE_Y[1]) / 2
        rod(f"handle_bar_{s}", (x, hy, 1.42), (x, hy, 2.28), 0.015, "plastic_satin")
        # cab tilt line (cab lower edge over the frame-mounted fairing)
    CAB.patch("tilt_gap_front", "gap", "front", CAB_Z0 - 0.006, CAB_Z0 + 0.004, -1.6, 1.6, off=0.001, nz=1, npar=60)
    # service hatch (tilting front flap) outline
    hx, ht = 0.92, 1.975
    CAB.patch("hatch_gap_top", "gap", "front", ht - 0.0035, ht + 0.0035, -hx, hx, off=0.0012, nz=1, npar=30)
    for s in (-1, 1):
        lamp = CFG["lamp"]
        z_l = lamp[3][1] + 0.01
        CAB.patch(f"hatch_gap_side_{s}", "gap", "front", z_l, ht, s * hx - 0.0035, s * hx + 0.0035, off=0.0012,
                  nz=4, npar=1)


# ---------------------------------------------------------------- front face: grille, brand, cowl, wipers
def front_face(feathers, strokes):
    set_group("cab")
    # one T-shaped grille field: honeycomb insert deep in the pocket, bars of three weights in front of it,
    # a graphite frame round the whole T (the brand idea lives in the frame and the DRL, not in slat fields)
    for k in ("stem", "bar"):
        CAB.poly_patch("grille_back_" + k, "grille_honey", "front", CFG[k], off=-0.066, sub=5)

    def gx(z):  # grille half width at z: road stem below, T-bar above
        st, br = CFG["stem"], CFG["bar"]
        if z >= br[0][1]:
            return br[1][0]
        t = (z - st[1][1]) / (st[2][1] - st[1][1])
        return st[1][0] + (st[2][0] - st[1][0]) * t
    for k, (zc, hgt, depth, m_) in enumerate(CFG["grille_bars"]):
        grille_bar(f"grille_bar{k}", zc, hgt, depth, gx(zc) - 0.004, m_, round_front=(m_ == "paint"))
    # frame: raised graphite band along the T outline (outer edge flush with the pocket edge)
    outline = [(-0.80, 1.235), (0.80, 1.235), (0.51, 1.625), (0.84, 1.625), (0.84, 1.86), (-0.84, 1.86),
               (-0.84, 1.625), (-0.51, 1.625)]
    ribbon("grille_frame", outline, 0.026, "trim_graphite", off=-0.004, thick=0.010)
    emblem(feathers)
    wordmark(strokes)
    # cowl (wiper panel) between hatch and windscreen
    CAB.patch("cowl", "plastic", "front", 1.978, 2.048, -1.12, 1.12, off=0.002, nz=3, npar=40)
    for k, x in enumerate(np.linspace(-0.9, 0.9, 14) if False else [-0.9 + 1.8 * i / 13 for i in range(14)]):
        CAB.patch(f"cowl_slot{k}", "gap", "front", 1.995, 2.03, x - 0.035, x + 0.035, off=0.0035, nz=1, npar=1)
    wipers()


def emblem(subpaths):
    """TRAKT road-T mark from art-source/truck/brand/trakt.svg: chrome outline (the only chrome on the
    truck), the two lane dashes as dark inlays (the SVG holes), centred on the grille's upper bar."""
    outline, holes = subpaths[0], subpaths[1:]
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    sc = CFG["emblem_w"] / (max(xs) - min(xs))
    zc = CFG["emblem_z"]
    y = CAB.front_pt(zc, 0.0, 0.0)[1] + 0.001
    pts = [(-(px - cx) * sc, zc - (py - cy) * sc) for px, py in outline]
    # SVG outline is clockwise in screen space; plane flip keeps it valid after recalc_face_normals
    extrude_poly("emblem", pts, 0.007, "chrome", plane="XZ", origin=(0, y, 0), bev=0.0015, bseg=2)
    for k, h in enumerate(holes):
        hp = [(-(px - cx) * sc, zc - (py - cy) * sc) for px, py in h]
        extrude_poly(f"emblem_dash{k}", hp, 0.0075, "plastic_satin", plane="XZ", origin=(0, y + 0.0002, 0))


def ribbon(name, poly, width, m, off=-0.004, thick=0.01, kind="front", loft=None):
    """Frame band of `width` running inside a closed CCW polygon [(x, z)] on the cab surface (one strip per
    edge, mitred corners), raised `thick` from `off`."""
    n = len(poly)

    def inward(i):
        (x0, z0), (x1, z1) = poly[i], poly[(i + 1) % n]
        ln = math.hypot(x1 - x0, z1 - z0)
        return (-(z1 - z0) / ln, (x1 - x0) / ln)
    inner = []
    for i in range(n):
        na, nb = inward(i - 1), inward(i)
        k = width / max(1.0 + na[0] * nb[0] + na[1] * nb[1], 0.2)   # mitre: distance `width` to both edges
        inner.append((poly[i][0] + (na[0] + nb[0]) * k, poly[i][1] + (na[1] + nb[1]) * k))
    for i in range(n):
        j = (i + 1) % n
        (xa, za), (xb, zb) = poly[i], poly[j]
        (ia, ka), (ib, kb) = inner[i], inner[j]
        (loft or CAB).quad_patch(f"{name}_{i}", m, kind, [(xa, za), (xb, zb), (ib, kb), (ia, ka)], off=off, nu=6, nv=1,
                       thick=thick)


def grille_bar(name, zc, hgt, depth, hw, m, round_front=True, n=2):   # flat part of the front: n=2 is exact
    """Horizontal grille bar following the cab front: body-colour bars get a rounded nose, graphite bars a
    louvre face tilted up (different depth and section, so the field never reads as identical slats)."""
    h = hgt / 2
    if round_front:
        prof = [(-h, -depth), (-h, -0.018), (-h * 0.85, -0.009), (-h * 0.5, -0.0045), (0.0, -0.003),
                (h * 0.5, -0.0045), (h * 0.85, -0.009), (h, -0.018), (h, -depth)]
    else:
        prof = [(-h, -depth), (-h, -0.024), (-h * 0.6, -0.022), (h, -0.011), (h, -depth)]
    bm = bmesh.new()
    rows = []
    for dz, o in prof:
        rows.append([bm.verts.new(CAB.front_pt(zc + dz, -hw + 2 * hw * j / n, o)) for j in range(n + 1)])
    k = len(rows)
    for a in range(k):
        r0, r1 = rows[a], rows[(a + 1) % k]
        for j in range(n):
            bm.faces.new((r0[j], r0[j + 1], r1[j + 1], r1[j]))
    for j in (0, n):
        bm.faces.new([r[j] for r in rows])
    return G.obj_from_bm(name, bm, m, sharp=55)


def wordmark(strokes, z_c=1.918, height=0.052, spacing=30.0, mat="wordmark", name="wordmark", origin=None):
    """TRAKT letters from the SVG polylines (own geometric monoline), letter-spaced, extruded 3 mm."""
    ys = [p[1] for pl, w in strokes for p in pl]
    y0, y1 = min(ys), max(ys)
    sc = height / (y1 - y0 + strokes[0][1])
    bounds = [192, 239, 293, 347, 401, 460]  # letter x-ranges in trakt.svg: T R A K T
    def idx(x):
        for i, b in enumerate(bounds[1:]):
            if x < b:
                return i
        return len(bounds) - 2
    allx = []
    for pl, w in strokes:
        for x, yv in pl:
            allx.append(x + idx(min(p[0] for p in pl)) * spacing)
    xc = (min(allx) + max(allx)) / 2
    yfr = CAB.front_pt(z_c, 0.0, 0.0)[1] if origin is None else origin
    for k, (pl, w) in enumerate(strokes):
        off = idx(min(p[0] for p in pl)) * spacing
        for j, (a, b) in enumerate(zip(pl, pl[1:])):
            ax, az = -(a[0] + off - xc) * sc, z_c - (a[1] - (y0 + y1) / 2) * sc   # viewer's left = +X
            bx, bz = -(b[0] + off - xc) * sc, z_c - (b[1] - (y0 + y1) / 2) * sc
            d = V((bx - ax, 0, bz - az))
            ln = d.length
            if ln < 1e-6:
                continue
            ang = math.atan2(d.z, d.x)
            hw = w * sc / 2
            box(f"{name}_{k}_{j}", ((ax + bx) / 2, yfr + 0.0015, (az + bz) / 2), (ln + 2 * hw, 0.003, 2 * hw), mat,
                rot=Matrix.Rotation(-ang, 3, "Y"))


def wipers():
    for k, (px, length) in enumerate(((-1.00, 0.86), (-0.08, 0.86))):
        z = 2.085
        y = CAB.front_pt(z, px, 0.02)[1]
        p0 = V((px, y + 0.01, 2.035))
        cyl(f"wiper_pivot{k}", (px, CAB.front_pt(2.02, px, 0)[1] + 0.012, 2.02), 0.022, 0.03, "plastic_satin",
            axis="Z", seg=16)
        tip = V((px + length, CAB.front_pt(z + 0.03, px + length, 0.03)[1], z + 0.03))
        rod(f"wiper_arm{k}", p0, tip, 0.008, "plastic_satin", seg=8)
        # blade lying on the glass along the base
        pts = []
        for i in range(9):
            x = px + 0.06 + (length - 0.04) * i / 8
            pts.append(V(CAB.front_pt(z + 0.01, x, 0.016)))
        tube(f"wiper_blade{k}", pts, 0.009, "rubber", seg=6)
        # washer nozzle on the cowl next to each pivot
        box((f"washer_nozzle{k}"), (px + 0.12, CAB.front_pt(2.03, px + 0.12, 0)[1] + 0.006, 2.033),
            (0.022, 0.012, 0.010), "plastic_satin", bev=0.003)


# ---------------------------------------------------------------- headlamps (TRAKT signature)
def drl_guide(name, s, p0, p1, wdt=0.016, n=12):
    """LED light guide between two front-projection points (x, z) with a dark-chrome carrier behind it."""
    bm = bmesh.new()
    (x0, z0), (x1, z1) = p0, p1
    dx, dz = x1 - x0, z1 - z0
    ln = math.hypot(dx, dz)
    nx, nz = -dz / ln * wdt / 2, dx / ln * wdt / 2
    layers = []
    for o in (-0.034, -0.012):
        rows = []
        for sg in (-1, 1):
            rows.append([bm.verts.new(CAB.front_pt(z0 + dz * j / n + sg * nz, s * (x0 + dx * j / n + sg * nx), o))
                         for j in range(n + 1)])
        layers.append(rows)
    (a, b), (c, d) = layers
    for j in range(n):
        for r0, r1 in ((c, d), (d, b), (b, a), (a, c)):
            bm.faces.new((r0[j], r0[j + 1], r1[j + 1], r1[j]))
    for j in (0, n):
        bm.faces.new((a[j], b[j], d[j], c[j]))
    G.obj_from_bm(name, bm, "led_drl", sharp=40)
    k = 2.2
    CAB.quad_patch(name + "_carrier", "dark_chrome", "front",
                   [(s * (x0 - k * nx), z0 - k * nz), (s * (x1 - k * nx), z1 - k * nz),
                    (s * (x1 + k * nx), z1 + k * nz), (s * (x0 + k * nx), z0 + k * nz)], off=-0.045, nu=n, nv=1)


def oriented_lathe(name, prof, p, nrm, m, seg=18):
    """Lathe around the local axis (+x along `nrm`), placed at p (lamp bowls, projector lenses)."""
    ob = G.lathe(name, prof, (0, 0, 0), m, seg=seg, axis="Z", sharp=50)
    rot = V((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4()
    ob.data.transform(Matrix.Translation(p) @ rot)
    ob.data.update()
    return ob


def headlamps():
    """2020s lamp (R2 #3): thick clear outer lens in a black gasket, black inner mask, two projector modules
    in reflector bowls, a slim LED high-beam line in a black mask, amber indicator strip. The DRL light guides
    (T-bar along the top + road edge down the inner side) are half of the TRAKT mark per lamp: both lamps
    and the T-shaped grille frame read as the brand's road-T."""
    set_group("cab")
    for s in (-1, 1):
        poly = CFG["lamp"] if s > 0 else mirror_poly(CFG["lamp"])
        CAB.poly_patch(f"lamp_back_{s}", "lamp_inner", "front", poly, off=-0.062, sub=6)
        for k, ((x0, z0), (x1, z1)) in enumerate(CFG["drl"]):
            drl_guide(f"drl_{s}_{k}", s, (x0, z0), (x1, z1))
        # projector modules: reflector bowl, dark-chrome shroud ring, dark projector lens
        for k, x in enumerate((0.99, 1.15)):
            z = 1.424
            nrm = CAB.normal_front(z, s * x)
            p = V(CAB.front_pt(z, s * x, 0.0))
            oriented_lathe(f"proj_bowl_{s}_{k}", [(0.058, -0.012), (0.052, -0.026), (0.040, -0.042), (0.024, -0.055),
                                                  (0.010, -0.060)], p, nrm, "reflector")
            oriented_lathe(f"proj_shroud_{s}_{k}", [(0.038, -0.050), (0.038, -0.030), (0.034, -0.026),
                                                    (0.030, -0.028)], p, nrm, "dark_chrome")
            oriented_lathe(f"proj_lens_{s}_{k}", [(0.030, -0.031), (0.028, -0.024), (0.023, -0.017), (0.014, -0.012),
                                                  (0.0, -0.010)], p, nrm, "projector")
        # LED high-beam line inside a black mask (no 'cubes')
        CAB.quad_patch(f"hb_mask_{s}", "plastic_satin", "front",
                       [(s * 0.95, 1.334), (s * 1.255, 1.334), (s * 1.255, 1.362), (s * 0.95, 1.362)], off=-0.034,
                       nu=14, nv=1, thick=0.010)
        CAB.quad_patch(f"hb_led_{s}", "led_off", "front",
                       [(s * 0.965, 1.344), (s * 1.24, 1.344), (s * 1.24, 1.352), (s * 0.965, 1.352)], off=-0.023,
                       nu=14, nv=1, thick=0.003)
        # amber indicator strip (reflector look behind the clear lens)
        CAB.quad_patch(f"indicator_{s}", "lens_amber", "front",
                       [(s * 0.95, 1.307), (s * 1.27, 1.307), (s * 1.27, 1.325), (s * 0.95, 1.325)],
                       off=-0.026, nu=16, nv=1, thick=0.008)
        # clear outer lens with thickness (two Fresnel surfaces) + black gasket round it
        CAB.poly_patch(f"lamp_lens_{s}", "lens_clear", "front", poly, off=-0.002, thick=0.006, sub=6)
        ribbon(f"lamp_gasket_{s}", poly, 0.011, "plastic_satin", off=-0.003, thick=0.0065)


# ---------------------------------------------------------------- corner deflectors, roof, rear wall
def corners_roof_rear():
    set_group("cab")
    for s in (-1, 1):
        # air deflector standing off the front corner, from above the lamp up to the A-pillar base
        # roof marker lamps (front white, rear red), side marker on the roof edge
        p = V(CAB.front_pt(ROOF_Z - 0.20, s * 0.80, 0.0))
        box(f"marker_front_{s}", p + V((0, 0.005, 0)), (0.12, 0.03, 0.04), "lens_clear", bev=0.008)
        box(f"marker_front_led_{s}", p - V((0, 0.006, 0)), (0.10, 0.01, 0.025), "led_off")
        box(f"marker_rear_{s}", (s * (CAB_HALF_W - 0.24), CAB_BACK_Y - 0.012, ROOF_Z - 0.17), (0.12, 0.025, 0.045),
            "lens_red", bev=0.006)
        # side extenders (aero flaps behind the cab), plastic with a rubber trailing edge
        xo = s * (CAB_HALF_W - 0.015)
        prof = [(CAB_BACK_Y + 0.10, 1.55), (CAB_BACK_Y - 0.30, 1.62), (CAB_BACK_Y - 0.34, 3.30),
                (CAB_BACK_Y + 0.05, 3.42)]
        extrude_poly(f"side_extender_{s}", prof, 0.016, "plastic", plane="YZ", origin=(xo - s * 0.016, 0, 0),
                     bev=0.004)
        rub = [(CAB_BACK_Y - 0.30, 1.62), (CAB_BACK_Y - 0.38, 1.625), (CAB_BACK_Y - 0.42, 3.29),
               (CAB_BACK_Y - 0.34, 3.30)]
        extrude_poly(f"extender_flap_{s}", rub, 0.008, "rubber", plane="YZ", origin=(xo - s * 0.012, 0, 0))
        for z in (1.9, 2.6, 3.25):
            box(f"extender_hinge_{s}_{z}", (xo - s * 0.03, CAB_BACK_Y - 0.02, z), (0.03, 0.06, 0.05), "plastic_satin")
    # roof: rear spoiler lip, roof hatch, antenna base
    box_mm("roof_lip", -1.10, 1.10, CAB_BACK_Y - 0.06, CAB_BACK_Y + 0.08, ROOF_Z - 0.035, ROOF_Z - 0.005,
           "plastic", bev=0.01)
    box_mm("roof_hatch", -0.36, 0.36, -0.55, 0.05, ROOF_Z - 0.02, ROOF_Z + 0.015, "plastic", bev=0.012, seg=3)
    box_mm("roof_hatch_glass", -0.30, 0.30, -0.49, -0.01, ROOF_Z + 0.012, ROOF_Z + 0.019, "frit")
    box_mm("antenna_base", 0.62, 0.70, -0.70, -0.55, ROOF_Z - 0.03, ROOF_Z + 0.03, "plastic_satin", bev=0.012)
    # rear wall: panel joints, work lamp, coupling panel
    y = CAB_BACK_Y - 0.002
    for x in (-0.62, 0.62):
        box_mm(f"rear_joint_{x}", x - 0.003, x + 0.003, y - 0.002, y, CAB_Z0 + 0.05, 3.55, "gap")
    box_mm("rear_joint_h", -1.05, 1.05, y - 0.002, y, 2.30, 2.306, "gap")
    box_mm("work_lamp", -0.18, 0.18, y - 0.05, y, 3.70, 3.76, "plastic_satin", bev=0.01)
    box_mm("work_lamp_lens", -0.16, 0.16, y - 0.052, y - 0.049, 3.71, 3.75, "led_off")
    box_mm("rear_lower_panel", -1.18, 1.18, y - 0.018, y, CAB_Z0, 1.55, "plastic", bev=0.006)
    # coupling panel (cab-back mounted): red supply / yellow control palm couplings, ISO 7638 + 15-pin sockets
    box_mm("coupling_panel", -0.34, 0.34, y - 0.04, y - 0.018, 1.30, 1.52, "chassis", bev=0.006)
    for k, (x, m_) in enumerate(((-0.24, "coupling_red"), (-0.12, "coupling_yellow"))):
        cyl(f"palm_{k}", (x, y - 0.075, 1.41), 0.042, 0.07, m_, axis="Y", seg=24, bev=0.006)
        cyl(f"palm_face_{k}", (x, y - 0.112, 1.41), 0.030, 0.006, "rubber", axis="Y", seg=20)
    for k, x in enumerate((0.08, 0.22)):
        cyl(f"socket_{k}", (x, y - 0.065, 1.41), 0.038, 0.05, "plastic_satin", axis="Y", seg=20, bev=0.004)
        cyl(f"socket_lid_{k}", (x, y - 0.092, 1.425), 0.034, 0.008, "plastic", axis="Y", seg=20)


# ---------------------------------------------------------------- mirrors
def mirror_aim(c, view):
    """Rotation turning a mirror head (glass facing local -Y) so that a ray from the eye point reflects into
    `view` (UNECE R46 adjustment from the driver's ocular point)."""
    to_eye = (EYE - V(c)).normalized()
    n = (to_eye + V(view).normalized()).normalized()
    fwd = -n                                    # local +Y (back of the head)
    up = V((0, 0, 1))
    right = fwd.cross(up).normalized()
    up = right.cross(fwd).normalized()
    return Matrix((right, fwd, up)).transposed()


def mirrors(kind="classic", front=True):
    set_group("mirrors" if kind == "classic" else "mirrors_cam")
    for s in (-1, 1):
        base = V(CAB.side_pt(2.90, win_front(2.90) + 0.02, s, 0.0))
        if kind == "classic":
            xh = s * 1.50
            yh = base.y - 0.10
            # arm: upper beam + lower strut, satin black
            tube(f"mirror_arm_{s}", [base + V((s * 0.0, 0, 0.03)), V((s * 1.33, yh + 0.02, 2.99)),
                                     V((xh, yh, 2.94))], 0.015, "plastic_satin", seg=10)
            tube(f"mirror_strut_{s}", [V(CAB.side_pt(2.25, win_front(2.25) - 0.02, s, 0.0)),
                                       V((xh - s * 0.02, yh, 2.08))], 0.014, "plastic_satin", seg=10)
            # class II main + class IV wide-angle heads; body-colour back caps. R2 #7: each glass is aimed so
            # that the eye point sees the field it must show (glass normal = bisector of the direction to the
            # eye and the required view direction), not left facing straight back (edge-on from the seat)
            for nm, zc, hgt, view in (("main", 2.60, 0.42, (s * 0.06, -1.0, -0.02)),
                                      ("wide", 2.20, 0.20, (s * 0.40, -1.0, -0.22))):
                c = V((xh, yh, zc))
                rot = mirror_aim(c, view)
                box(f"mirror_{nm}_{s}", c, (0.24, 0.085, hgt), "plastic_satin", bev=0.03, seg=4, rot=rot)
                box(f"mirror_{nm}_cap_{s}", c + rot @ V((0, 0.02, 0)), (0.235, 0.06, hgt - 0.01), "paint", bev=0.03,
                    seg=4, rot=rot)
                box(f"mirror_{nm}_glass_{s}", c + rot @ V((0, -0.044, 0)), (0.215, 0.006, hgt - 0.03), "mirror",
                    bev=0.004, rot=rot)
            if s > 0:  # class V kerb mirror on the passenger side, under the main mirrors, looking down
                c = V((s * 1.42, yh + 0.04, 1.98))
                rot = mirror_aim(c, (0.25, -0.35, -1.0))
                box("mirror_kerb", c, (0.20, 0.08, 0.14), "plastic_satin", bev=0.03, seg=3, rot=rot)
                box("mirror_kerb_glass", c + rot @ V((0, -0.041, 0)), (0.18, 0.006, 0.12), "mirror", bev=0.003,
                    rot=rot)
        else:
            # camera monitor system: short aero arm with a camera pod (class II/IV)
            yh = base.y - 0.05
            tube(f"cam_arm_{s}", [base + V((0, 0, 0.04)), V((s * 1.36, yh, 2.98)), V((s * 1.44, yh - 0.03, 2.96))],
                 0.022, "plastic_satin", seg=10)
            sphere(f"cam_pod_{s}", (s * 1.46, yh - 0.06, 2.95), 0.05, "plastic_satin", scale=(1.1, 2.2, 1.0))
            cyl(f"cam_lens_{s}", (s * 1.46, yh - 0.165, 2.95), 0.016, 0.008, "glass_tint", axis="Y", seg=16)
            if s > 0:
                sphere("cam_pod_kerb", (s * 1.36, yh - 0.03, 2.86), 0.035, "plastic_satin", scale=(1, 1.6, 1))
    # class VI front mirror over the passenger-side corner (kept with camera mirrors too)
    if not front:
        return
    set_group("mirrors")
    p = V(CAB.front_pt(3.25, 0.98, 0.0))
    tube("front_mirror_arm", [p + V((0, -0.05, 0.10)), p + V((0, 0.12, 0.10)), p + V((0, 0.20, 0.0))], 0.014,
         "plastic_satin", seg=10)
    box("front_mirror", p + V((0, 0.22, -0.10)), (0.26, 0.07, 0.17), "plastic_satin", bev=0.03, seg=3,
        rot=Matrix.Rotation(math.radians(-35), 3, "X"))
    box("front_mirror_glass", p + V((0, 0.20, -0.135)), (0.24, 0.006, 0.15), "mirror", bev=0.003,
        rot=Matrix.Rotation(math.radians(-35), 3, "X"))


# ---------------------------------------------------------------- frame-mounted lower fairing (bumper + step boxes)
def lower_fairing():
    """One loft (bumper + side step boxes) minus centre, wheel arches, step recesses and pockets."""
    global LOW
    set_group("lower")
    sp = CFG["bumper_split"]
    LOW = Loft(front=[(0.38, 1.495), (0.50, 1.522), (1.00, 1.522), (FAIR_TOP, 1.505)], back=FAIR_BACK,
               w=[(0.38, CAB_HALF_W - 0.02), (0.55, CAB_HALF_W), (sp, CAB_HALF_W), (FAIR_TOP, CAB_HALF_W)],
               rf=[(0.38, 0.30), (FAIR_TOP, 0.32)], rb=0.05, z0=0.38, ztop=FAIR_TOP, roof_r=0.015, arc_n=14,
               step=0.04, flat_n=8, roof_n=3)
    lo = LOW.build("lower_fairing", "plastic", sharp=45)
    lo.data.materials.append(G.mat("paint"))
    cuts = [G.box_mm("cut_centre", -0.94, 0.94, FAIR_BACK - 0.2, 1.17, 0.2, 1.4, "gap")]
    for s in (-1, 1):
        c = cyl(f"cut_arch_{s}", (s * 1.10, 0.0, WHEEL_Z), ARCH_R, 0.6, "plastic", axis="X", seg=48)
        cuts.append(c)
        # step well behind the wheel: three open recesses, walls in body colour (R2 #2/#3: no black boxes)
        xo, xi = s * (CAB_HALF_W + 0.1), s * (CAB_HALF_W - STEP_DEPTH)
        for k, (z, y0, y1) in enumerate(STEPS):
            cuts.append(box_mm(f"cut_step{k}_{s}", min(xo, xi), max(xo, xi), y0, y1, z,
                               z + (0.30 if k == 2 else 0.24), "paint"))
    # bumper pockets: lower intake, the T 'road' continued in the bumper, fog lamps, two cleaning steps
    cuts.append(LOW.patch("cut_intake", "grille_honey_coarse", "front", 0.45, 0.62, -0.80, 0.80, off=-0.06,
                          thick=0.15, nz=2, npar=24))
    cuts.append(LOW.quad_patch("cut_road", "trim_graphite", "front", CFG["bumper_road"], off=-0.034, thick=0.15,
                               nu=16, nv=3))
    for s in (-1, 1):
        cuts.append(LOW.patch(f"cut_fog_{s}", "lamp_inner", "front", 0.70, 0.79, s * 0.80, s * 1.20, off=-0.05,
                              thick=0.12, nz=2, npar=10))
        cuts.append(LOW.patch(f"cut_bstep_{s}", "plastic", "front", 1.00, 1.08, s * 0.92, s * 1.12, off=-0.12,
                              thick=0.2, nz=1, npar=4))
    boolean(lo, cuts)
    # R2 #3: break the dark plinth. Body colour on every outward face above the split (bumper top, corners,
    # the panel ahead of the arch and the step boxes); dark textured plastic only on the lower bumper, the
    # skirt under the bottom step, the arch flare and inside the arch
    me = lo.data
    for p in me.polygons:
        c, n = p.center, p.normal
        if p.material_index != 0 or c.z <= sp or n.z < -0.5:
            continue
        sx = 1 if c.x > 0 else -1
        outward = n.x * sx > 0.55 or (n.y > 0.55 and c.y > 1.2) or (c.y > 0.62 and n.y > 0.2 and n.x * sx > 0.2)
        if outward or n.z > 0.5:
            p.material_index = 1
    me.shade_smooth()
    if hasattr(me, "set_sharp_from_angle"):
        me.set_sharp_from_angle(angle=math.radians(45))
    # no bevel modifier here: on the booleaned n-gons it spiked a vertex to the ground (seen in A4 ortho
    # renders); edges stay crisp via sharp-edge smoothing, the bevel comes back with the A6 retopo
    for s in (-1, 1):
        # arch flare (defined edge, ~65 mm) and inner wheelhouse liner
        arch(f"arch_flare_{s}", 0.0, WHEEL_Z, ARCH_R - 0.004, ARCH_OUT, s * (CAB_HALF_W - 0.03),
             s * (CAB_HALF_W + 0.006), -12, 192, "plastic")
        arch(f"arch_liner_{s}", 0.0, WHEEL_Z, ARCH_R - 0.012, ARCH_R, s * 0.93, s * (CAB_HALF_W - 0.02), -12, 192,
             "plastic")
        # spray-suppression brush strip inside the flare lip and a front mud flap behind the wheel (R2 #4)
        arch(f"arch_brush_{s}", 0.0, WHEEL_Z, ARCH_R - 0.030, ARCH_R - 0.004, s * (CAB_HALF_W - 0.13),
             s * (CAB_HALF_W - 0.01), -10, 190, "brush", n=24)
        box_mm(f"front_mudflap_{s}", s * 0.86, s * 1.205, -0.604, -0.594, 0.20, 0.66, "rubber", bev=0.003)
        for k in range(4):
            box_mm(f"front_mudflap_rib_{s}_{k}", s * 0.89, s * 1.175, -0.611, -0.603, 0.26 + k * 0.09,
                   0.285 + k * 0.09, "rubber")
        box_mm(f"front_mudflap_clamp_{s}", s * 0.86, s * 1.205, -0.612, -0.590, 0.62, 0.66, "chassis", bev=0.003)
        # step treads (aluminium tread plate) with a dark nosing
        xo, xi = s * (CAB_HALF_W - 0.004), s * (CAB_HALF_W - STEP_DEPTH)
        for k, (z, y0, y1) in enumerate(STEPS):
            box_mm(f"step_tread{k}_{s}", min(xo, xi), max(xo, xi), y0 + 0.004, y1 - 0.004, z, z + 0.014, "checker",
                   bev=0.003)
            box_mm(f"step_nose{k}_{s}", xo - s * 0.025, xo, y0 + 0.004, y1 - 0.004, z - 0.02, z + 0.016,
                   "plastic_satin", bev=0.004)
        # amber side repeater on the bumper corner ahead of the arch
        p = V(LOW.side_pt(0.98, 0.86, s, 0.002))
        box(f"side_repeater_{s}", p, (0.012, 0.09, 0.035), "lens_amber", bev=0.004)
        # fog / cornering lamps in their pockets
        LOW.patch(f"fog_lens_{s}", "lens_clear", "front", 0.705, 0.785, s * 0.805, s * 1.195, off=0.0, nz=2, npar=10)
        LOW.patch(f"fog_back_{s}", "lamp_inner", "front", 0.70, 0.79, s * 0.80, s * 1.20, off=-0.045, nz=1, npar=10)
        LOW.patch(f"fog_led_{s}", "led_off", "front", 0.735, 0.755, s * 0.84, s * 1.16, off=-0.03, nz=1, npar=8,
                  thick=0.01)
        for k, x in enumerate((0.92, 1.06)):
            p = V(LOW.front_pt(0.745, s * x, -0.035))
            cyl(f"fog_bowl_{s}_{k}", p, 0.032, 0.02, "reflector", axis="Y", seg=20)
        # cleaning steps in the bumper (folding treads) + tow pin cover outline
        LOW.patch(f"bstep_tread_{s}", "checker", "front", 1.003, 1.012, s * 0.925, s * 1.115, off=-0.115,
                  thick=0.11, nz=1, npar=4)
    LOW.patch("bumper_split", "gap", "front", sp - 0.004, sp + 0.004, -1.6, 1.6, off=0.001, nz=1, npar=60)
    # number plate (PL/EU 520 x 114 mm) on a dark holder
    LOW.patch("plate_holder", "plastic", "front", 0.765, 0.905, -0.275, 0.275, off=0.001, thick=0.008, nz=2, npar=8)
    G.plate_uv(LOW.patch("plate", "plate", "front", 0.778, 0.892, -0.26, 0.26, off=0.0105, nz=1, npar=4), 1)
    LOW.patch("tow_cover", "gap", "front", 1.02, 1.025, -0.12, 0.12, off=0.001, nz=1, npar=2)
    LOW.patch("tow_cover_b", "gap", "front", 0.93, 0.935, -0.12, 0.12, off=0.001, nz=1, npar=2)
    for s in (-1, 1):
        LOW.patch(f"tow_cover_s{s}", "gap", "front", 0.93, 1.025, s * 0.12 - 0.0025, s * 0.12 + 0.0025, off=0.001,
                  nz=1, npar=1)
    # bumper 'road' (the grille's T stem continued): coarse honeycomb in a graphite frame, no slats
    LOW.quad_patch("road_back", "grille_honey_coarse", "front", CFG["bumper_road"], off=-0.029, nu=16, nv=3)
    ribbon("road_frame", CFG["bumper_road"], 0.022, "trim_graphite", off=-0.004, thick=0.008, loft=LOW)
    # lower intake: coarse honeycomb (different texture and scale from the grille), horns visible behind it
    LOW.patch("intake_mesh", "grille_honey_coarse", "front", 0.45, 0.62, -0.80, 0.80, off=-0.052, nz=1, npar=16)
    for s in (-1, 1):
        cyl(f"horn_{s}", (s * 0.45, 1.44, 0.53), 0.055, 0.04, "plastic_satin", axis="Y", seg=24)
    # lower spoiler lip
    LOW.patch("spoiler_lip", "rubber", "front", 0.375, 0.40, -1.15, 1.15, off=0.006, thick=0.01, nz=1, npar=40)


# ---------------------------------------------------------------- interface for the interior (door card, glass)
def door_interface(path):
    """Write the door opening / glass / step coordinates the interior generator must match (R2 #2)."""
    import json
    r = lambda v: round(float(v), 4)
    front = [[r(door_front_y(z)), r(z)] for z in (CAB_Z0, 1.60, DOOR_KINK_Z[0], 2.02, DOOR_KINK_Z[1], BELT_Z,
                                                   2.50, 2.80, 3.00)]
    data = {
        "asset": "TRAKT tractor exterior, round 3 (visual review R2 #2)",
        "frame": "1 unit = 1 m, Z up, truck faces +Y, driver (LHD) = -X, origin = ground under the front axle "
                 "centre (same as dims.json). Values are for the left (driver) door; the right door is the mirror "
                 "image (x -> -x).",
        "status": "WORKING_VALUE (class-typical layout, to be confirmed with owner photos + tape: hub centre -> "
                  "door rear edge, step widths, sill height)",
        "generator": "tools/blender/truck/exterior/body.py (door_interface)",
        "eye_point_m": [r(v) for v in EYE],
        "cab_floor_z_m": G.FLOOR_Z,
        "cab_outer_half_width_m": r(CAB_HALF_W),
        "door": {
            "rear_shut_line_y_m": DOOR_REAR,
            "front_shut_line_yz_m": front,
            "front_shut_line_note": "vertical at y 0.80 behind the fixed body-colour corner panel up to z 1.90, "
                                    "diagonal to the A-pillar at z 2.14, then parallel to the A-pillar",
            "top_shut_line_z_m": 3.00,
            "bottom_edge_z_m": CAB_Z0,
            "skirt": {"note": "lower rear corner of the door drops below the tilt line over the top step",
                      "y_rear_m": DOOR_REAR, "y_front_m_at_bottom": r(arch_y(SKIRT_Z)), "z_bottom_m": SKIRT_Z,
                      "front_edge": "follows the wheel-arch flare (radius 0.635 m about the front axle)"},
            "seal_overlap_m": DOOR_SEAL,
        },
        "aperture_for_interior": {
            "note": "interior opening = shut line moved inwards by the seal overlap; replaces DOOR_Y0/DOOR_Y1 "
                    "(-0.24 / 1.13) in tools/blender/truck/interior/build_interior.py",
            "DOOR_Y0_rear_m": r(DOOR_REAR + DOOR_SEAL),
            "DOOR_Y1_front_at_floor_m": r(DOOR_FRONT_LOW - DOOR_SEAL),
            "DOOR_Y1_front_at_belt_m": r(door_front_y(BELT_Z) - DOOR_SEAL),
            "sill_z_m": G.FLOOR_Z,
            "head_z_m": 2.98,
            "door_card_y_range_m": [r(DOOR_REAR + DOOR_SEAL + 0.03), r(DOOR_FRONT_LOW - DOOR_SEAL - 0.02)],
        },
        "side_glass": {
            "rear_edge_y_m": r(WIN_REAR),
            "front_edge": "follows the A-pillar: y = win_front(z) in body.py",
            "front_edge_yz_m": [[r(win_front(BELT_Z)), BELT_Z], [r(win_front(WIN_TOP)), WIN_TOP]],
            "belt_z_m": BELT_Z, "top_z_m": WIN_TOP,
        },
        "fixed_corner_panel": {"y_from_m": DOOR_FRONT_LOW, "to": "front corner", "z_to_m": DOOR_KINK_Z[1]},
        "grab_handle_behind_door_y_m": list(HANDLE_Y),
        "steps_behind_front_wheel": [
            {"tread_top_z_m": r(z + 0.014), "y_rear_m": y0, "y_front_m": y1, "width_m": r(y1 - y0),
             "depth_m": STEP_DEPTH} for z, y0, y1 in STEPS],
        "previous_r2": {"door_rear_shut_line_y_m": -0.28, "aperture_y_m": [-0.24, 1.13]},
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print("WROTE", path)
    return data


# ---------------------------------------------------------------- interior proxies (seen through the glass)
def interior_proxies():
    """Simple dark volumes standing in for the A5 interior: dash, wheel, seats, curtain, overhead shelf.
    Kept out of the exterior triangle budget (group 'interior_proxy')."""
    set_group("interior_proxy")
    box_mm("ip_dash", -1.04, 1.04, 1.00, 1.33, 1.60, 2.09, "interior", bev=0.04, seg=3)
    box_mm("ip_hood", -0.85, -0.25, 1.00, 1.18, 2.09, 2.17, "interior", bev=0.03, seg=3)
    import bmesh as _b
    bm = _b.new()
    _b.ops.create_circle(bm, segments=40, radius=0.235)
    ring = bpy.data.objects.new("ip_wheel_path", None)
    tube_pts = [V((-0.55 + 0.235 * math.cos(a), 0.875 + 0.235 * math.sin(a) * math.sin(math.radians(38)) * -1,
                   2.12 + 0.235 * math.sin(a) * math.cos(math.radians(38))))
                for a in [2 * math.pi * i / 40 for i in range(40)]]
    bm.free()
    tube("ip_wheel", tube_pts, 0.017, "interior", seg=8, closed=True)
    for x in (-0.55, 0.55):
        box_mm(f"ip_seat_{x}", x - 0.26, x + 0.26, 0.15, 0.62, 1.40, 1.95, "interior", bev=0.05, seg=3)
        box_mm(f"ip_back_{x}", x - 0.25, x + 0.25, 0.02, 0.20, 1.90, 2.72, "interior", bev=0.06, seg=3)
    box_mm("ip_curtain", -1.18, 1.18, -0.36, -0.33, 1.40, 3.40, "curtain")
    box_mm("ip_shelf", -1.00, 1.00, 0.50, 0.88, 3.05, 3.40, "interior", bev=0.03)   # clear of the flush header


import numpy as np  # noqa: E402  (used in front_face)
