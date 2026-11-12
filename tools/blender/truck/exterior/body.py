"""TRAKT cab + frame-mounted lower fairing (concept B, A3/A4, round 3 after visual review R2).

Shape parameters live in CFG (profiles in metres, see ART_BIBLE exterior section) so a different
concept/front can be tried by editing data, not code. Interior alignment: the door opening, glass and
step data are written to art-source/truck/exterior/door_interface.json (door_interface()) for the
interior generator; eye point unchanged (-0.55, 0.45, 2.50).

R2 #2 layout (real EU cab-over): front wheel under the front half of the door, a fixed body-colour corner
panel ahead of the door, door rear shut line 0.60 m behind the axle, the door's lower rear corner drops
over the top step as a skirt, three steps behind the wheel in a body-colour step well.
B2.1 (owner sheets 2026-11-09): the door ends at the cab's lower edge, ahead of / above the steps (no skirt), the
steps come down 0.05-0.06 m so the top tread keeps foot clearance under the door sill.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import geom as G
from geom import (CAB_BACK_Y, CAB_HALF_W, WHEEL_Z, EYE, Loft, V, box, box_mm, cyl, rod, sphere, tube,
                  set_group, boolean, bevel, extrude_poly, rrect, arch)

# B2 + owner correction (2026-11-09): the front in side view is ONE line - bumper, grille, windscreen and roof edge
# in a single, nearly upright plane leaning back at a constant RAKE (2020s cab-overs), no step between the glass
# and the grille (r4 had a vertical face under a 19 deg screen = the ~2008 'step'). RAKE is a WORKING_VALUE chosen
# in the owner's 5-8 deg band; the interior reads it from glass_interface.json (rake_deg_from_vertical).
RAKE = 7.0
TAN = math.tan(math.radians(RAKE))
FACE_Y0 = 1.480                      # front plane at the cab lower edge (z = CAB_Z0); bumper top continues it
WS_Z0, WS_Z1 = 1.94, 3.12            # visible glass bottom/top (B2: 2.06-2.96 -> 1.94-3.12, 1.18 m visible)
# B2 owner note 'forehead too big' (0.9 m of paint over the glass): cab roof 3.95 -> 3.75 m (WORKING_VALUE; dims.json
# overall_height_m synced) and the glass top 2.96 -> 3.12 m:
# black frit + sun visor read as one dark band up to ~3.20 m, painted header ~0.45 m flat + R 0.10 roof edge.
# Interior headliner stays at 3.62 m (2.22 m standing height over the 1.40 m floor), 0.13 m roof package.
ROOF_Z = G.ROOF_Z                    # 3.75 m: dims.json overall_height_m (owner decision 2026-11-09, B2 v2)
# black ceramic frit inside the visible opening (A6: bottom 75 mm, real screens 60-120 mm; hides the cowl, the
# wiper spindles and the dash top edge from outside and from the seat - REVIEW r2 §2 #2). Published in
# glass_interface.json; the interior prints the same band on the inner face.
FRIT_BOTTOM, FRIT_TOP, FRIT_SIDE = 0.075, 0.10, 0.028
CAB_Z0 = 1.225                       # cab shell lower edge = tilt line
FAIR_TOP = 1.21                      # frame-mounted lower fairing top
BELT_Z, WIN_TOP = 2.17, 2.94         # side glass (interior: 2.17..2.96)
DOOR_REAR = -0.60                    # door rear shut line (R2 #2: was -0.28, moved 0.32 m rearward)
DOOR_SEAL = 0.04                     # shut line -> aperture edge (seal overlap)
DOOR_FRONT_LOW = 0.80                # door front shut line below the corner panel (fixed panel ahead of it)
DOOR_KINK_Z = (1.90, 2.14)           # front shut line runs diagonally from the corner panel up to the A-pillar
WIN_REAR = DOOR_REAR + DOOR_SEAL + 0.07   # door glass rear edge (-0.49; interior: aperture rear + 0.07)
SKIRT_Z = None                       # B2.1: no door skirt - the door ends at CAB_Z0, the steps stay open below it
ARCH_R = 0.60                        # front wheel arch radius (tyre r 0.538 + 6 cm)
ARCH_OUT = ARCH_R + 0.035            # outer edge of the arch flare
FAIR_BACK = -1.14                    # lower fairing (step boxes) ends 0.19 m behind the cab back wall
# steps behind the front wheel: (z of tread top, y rear, y front); widths 0.42 / 0.485 / 0.60 m
# B2.1: top tread 1.114 -> 1.054 m (0.17 m toe room under the 1.225 m cab edge now that the door skirt is gone);
# rises 0.32 / 0.28 m and 0.35 m tread -> 1.40 m floor (ISO 2867 class: <= 0.40 m)
STEPS = ((0.45, -1.08, -0.66), (0.77, -1.07, -0.585), (1.04, -1.06, -0.46))
STEP_DEPTH = 0.21                    # tread depth (x)
HANDLE_Y = (-0.83, -0.74)            # recessed grab handle in the fixed rear side panel, behind the door
PIVOT = Vector((0.0, 1.34, 1.19))    # cab tilt pivot (front cab mount on the frame horns)


def face_y(z):
    """The single front plane (A2 y at height z): lower face, grille, windscreen outer surface, header."""
    return FACE_Y0 - (z - CAB_Z0) * TAN


def ws_y(z):
    return face_y(z)


WS_Y0 = face_y(2.04)                 # windscreen outer surface at z = 2.04 (kept for older callers)


def arch_y(z, r=ARCH_OUT, rear=True):
    """y of the arch flare outer edge at height z (behind or ahead of the front axle)."""
    dz = z - WHEEL_Z
    d = math.sqrt(max(r * r - dz * dz, 0.0))
    return -d if rear else d


CFG = {
    # B2/owner: one straight front line from the cab lower edge to the roof edge (the roof radius takes the top);
    # the bumper below continues the same plane (lower_fairing). Extra keys only add section rings.
    "front": [(CAB_Z0, face_y(CAB_Z0)), (WS_Z0 - 0.08, face_y(WS_Z0 - 0.08)), (WS_Z0, face_y(WS_Z0)),
              (WS_Z1 + 0.02, face_y(WS_Z1 + 0.02)), (ROOF_Z, face_y(ROOF_Z))],
    "w": [(CAB_Z0, CAB_HALF_W), (2.70, CAB_HALF_W), (3.50, CAB_HALF_W - 0.02), (ROOF_Z, CAB_HALF_W - 0.045)],
    # B2: plan corner under the screen R 0.32 -> 0.16 (crisp corner deflector), blending into the windscreen's
    # wrap radius (glass contract) over the cowl band; header corner as before
    # B2 v2: the glass-zone corner tightened too (0.36-0.40 -> 0.22-0.26): the R 0.16 face corner no longer
    # steps out under a softer glass corner (a visible notch at the cowl), and the screen wraps ~50 deg instead of
    # ~70 deg (the 90s 'wrapped' screen, REVIEW r3.1 cause 2)
    "rf": [(CAB_Z0, 0.16), (WS_Z0 - 0.10, 0.16), (WS_Z0 - 0.015, 0.22), (WS_Z1 + 0.02, 0.26), (ROOF_Z, 0.28)],
    "rb": 0.10,
    # B2: roof edge R 0.40 'bubble' -> 0.10 m edge (flat header wall + sun visor, roof shoulder)
    "roof_r": 0.10,
    # front face (front-projection params: x = lateral, wraps round the corner beyond the flat part)
    # B2 v2 face (owner reference sheets 2026-11-09): one wide rectangular grille (+-0.80 m, 1.235-1.82 m) with
    # horizontal graphite louvres filling the space between the lamps, a flush body-colour strip on top carrying
    # the TRAKT wordmark, the honeycomb lower intake below it in the bumper. Slim horizontal lamps sit in the
    # grille's upper corners right against its frame (28 mm) and wrap ~10 cm round the R 0.16 corner.
    "lamp": [(0.828, 1.600), (1.300, 1.600), (1.312, 1.762), (0.828, 1.762)],
    # DRL light guides (right lamp): line along the top + a short vertical guide on the grille side, inset behind
    # the lens and split at the corner
    # B2.1: vertical guide 21 mm further in from the lens edge (the thicker lens rim mirrored it away at 3/4 views)
    "drl": [((0.866, 1.738), (1.296, 1.738)), ((0.866, 1.724), (0.866, 1.618))],
    "stem": [(-0.80, 1.235), (0.80, 1.235), (0.80, 1.600), (-0.80, 1.600)],   # lower grille field
    "bar": [(-0.80, 1.585), (0.80, 1.585), (0.80, 1.852), (-0.80, 1.852)],    # upper field + black wordmark band
    "bumper_road": [(-0.80, 0.885), (0.80, 0.885), (0.80, 1.21), (-0.80, 1.21)],   # lower intake (honeycomb)
    "emblem_z": None, "emblem_w": 0.15,          # B2 v2: no grille badge, the wordmark carries the brand
    # B2.2: the grille frame covered the band's top 22 mm, so the old 80 mm letters at 1.799 lost their top 9 mm (T
    # bars, R/A shoulders). The frame's top lip is now 8 mm (sides/bottom stay 22 mm) and the band nose radius 4 mm:
    # flat visible face 1.749-1.844 m = 95 mm, letters 91 mm centred in it (2 mm clear top and bottom)
    "wordmark_z": 1.7965, "wordmark_h": 0.091,
    # (z_centre, height, depth, material): flush black band carrying the silver TRAKT letters (owner sheets: light
    # lettering on a dark strip, the band runs up to the cowl so screen-band-grille read as one dark mass) + 6 louvres
    "grille_bars": [(1.7985, 0.107, 0.040, "plastic_satin"),
                    (1.705, 0.020, 0.058, "trim_graphite"), (1.623, 0.020, 0.058, "trim_graphite"),
                    (1.541, 0.020, 0.058, "trim_graphite"), (1.459, 0.020, 0.058, "trim_graphite"),
                    (1.377, 0.020, 0.058, "trim_graphite"), (1.295, 0.020, 0.058, "trim_graphite")],
    "bumper_split": 0.67,             # body colour above, dark textured lower bumper below
    "side_split": 0.55,               # body colour on the step boxes / corner above, dark skirt below
    "ws_bottom_x": 1.22, "ws_top_x": 1.12,
}
CAB = None    # Loft of the cab shell

# ---------------------------------------------------------------- rounding pass (owner 2026-11-10, STAGE 1 proposal)
# 'ciezarowka jest zbyt kanciasta, aktualne sa bardziej zaokraglone'. SHAPE 'b2' = the exported cab (default until the
# owner approves, so the door/glass interfaces and the A6 export stay untouched); 'round' = the proposal, selected with
# build.py --shape round. Kept owner constraints: the centreline front is still one 7 deg plane, glass 1.94-3.12 m,
# roof 3.75 m, all dims.json values. Every radius is a WORKING_VALUE read off photos of 2020+ European long-haul cabs
# (docs/REFERENCES.md, 'Zaokraglenia kabiny'): reference for the amount of rounding only, no maker's design is copied.
SHAPE = "b2"
ROUND = {
    "crown": 10.0,                    # plan radius of the front face: 40 mm sagitta at the corner start (x = 0.89 m)
    # plan corner (deflector) radius bumper-to-roof: one continuous R 0.32-0.36 wrap into the doors (was 0.16-0.28)
    "rf": [(CAB_Z0, 0.36), (WS_Z0 - 0.10, 0.36), (WS_Z0 - 0.015, 0.34), (WS_Z1 + 0.02, 0.32), (ROOF_Z, 0.34)],
    "roof_h": 0.22,                   # height of the roof-edge zone (painted header stays flat up to 3.53 m)
    "roof_rr": (0.24, 0.20, 0.07),    # roof edge radius to the front / to the sides / to the rear wall (was 0.10)
    "low_rf": [(0.38, 0.40), (FAIR_TOP, 0.37)],   # bumper ends wrap with the cab corner (was 0.22-0.17)
    "ws_bottom_x": 1.16, "ws_top_x": 1.07,        # glass stops ~46 deg round the corner; painted A-pillar wraps the rest
    "win_front": 0.08,                # side glass front edge ahead of the corner arc centre (flat part of the door)
    "marker_dz": 0.27,                # roof marker lamps below the roof radius
}


# ---------------------------------------------------------------- modern front (owner 2026-11-10, STAGE 1 proposal)
# 'nowy front, nowoczesny, od zera': 2020+ generation long-haul face in TRAKT's own language, built on the rounded
# loft (crown R 10 m in plan, side view still one 7 deg plane). TRAKT graphic = the brand's road-T as ONE gloss-black
# mask: the T bar is a full-width band under the windscreen (wraps the corners with the glass, carries the wordmark),
# the T stem runs down through the bumper to the number plate; a dashed 'lane line' of brushed-aluminium dashes runs
# down the stem's centre. Slim wrap-round LED lamps sit low in the corner panels beside the stem. No maker's
# signature is used (no lamp brows, no stepped bar signature, no roof-lamp pods). All values WORKING_VALUE.
MODERN = {
    # r2 (owner: A-pillar too wide from the seat): left pillar 15.3 deg of azimuth at eye height -> 4.5 deg (b2: 4.2):
    # the screen wraps ~60 deg round the R 0.36 corner and the door glass starts 0.17 m ahead of the arc centre
    "round": {"roof_h": 0.30, "roof_rr": (0.34, 0.26, 0.08), "marker_dz": 0.40,
              "ws_bottom_x": 1.25, "ws_top_x": 1.16, "win_front": 0.17,
              "rf": [(CAB_Z0, 0.38), (WS_Z0 - 0.10, 0.38), (WS_Z0 - 0.015, 0.36), (WS_Z1 + 0.02, 0.34), (ROOF_Z, 0.36)],
              "low_rf": [(0.38, 0.40), (FAIR_TOP, 0.38)]},
    "cfg": {
        # tumblehome above the belt line (22 mm at the window top, 60 mm at the roof): reflections flow
        "w": [(CAB_Z0, CAB_HALF_W), (BELT_Z, CAB_HALF_W), (WIN_TOP, CAB_HALF_W - 0.022),
              (3.45, CAB_HALF_W - 0.05), (ROOF_Z, CAB_HALF_W - 0.06)],
        "stem": [(-0.795, 1.221), (0.795, 1.221), (0.85, 1.640), (-0.85, 1.640)],     # T stem (cab part), tapered
        "bar": [(-1.21, 1.618), (1.21, 1.618), (1.21, 1.866), (-1.21, 1.866)],       # T bar under the windscreen
        "bumper_road": [(-0.72, 0.70), (0.72, 0.70), (0.793, 1.216), (-0.793, 1.216)],  # T stem (bumper part)
        # slim wrap-round lamp low in the corner panel beside the stem (taller towards the corner)
        # r2 (owner: lamps too small at distance): lens 0.19-0.28 m tall (was 0.12-0.18), 100 mm modules, half-T DRL
        "lamp": [(0.875, 1.318), (1.360, 1.268), (1.385, 1.545), (0.875, 1.505)],
        "louvres": (1.272, 0.075, 5, 0.050),   # first centre z, pitch, count, height (cab); the bumper continues it
        "wordmark_z": 1.742, "wordmark_h": 0.150,   # r6 E-N4: 100 -> 150 mm cap height, 1.8x stroke (Low tier legibility)
        "bumper_split": 0.45,
    },
}


def set_rake(deg):
    """Owner 2026-11-10 ('z profilu zbyt duzy kat'): rake of the single front plane for the modern proposal. The plane
    pivots at the cab lower edge (FACE_Y0 fixed), so the bumper stays and the header moves forward."""
    global RAKE, TAN, WS_Y0
    RAKE = float(deg)
    TAN = math.tan(math.radians(RAKE))
    WS_Y0 = face_y(2.04)
    CFG["front"] = [(z, face_y(z)) for z in (CAB_Z0, WS_Z0 - 0.08, WS_Z0, WS_Z1 + 0.02, ROOF_Z)]


import copy as _copy  # noqa: E402
_CFG0, _ROUND0 = _copy.deepcopy(CFG), _copy.deepcopy(ROUND)
DEFAULT_SHAPE = "modern"            # owner decisions D28 / D29 (2026-11-10, ADR 0047): modern front, 1.5 deg rake
SHAPE_RAKE = {"b2": 7.0, "round": 7.0, "modern": 1.5}
# modern: the front plane sits 0.08 m further back, so the upright face (visor nose = front-most body point,
# 1.444 m ahead of the axle) stays inside dims.json front_overhang_m 1.45 m -> combination 16.47 m (b2 measured 1.56 m)
SHAPE_FACE_Y0 = {"b2": 1.480, "round": 1.480, "modern": 1.400}


def set_shape(name, rake=None):
    """Select the cab variant (resets CFG/ROUND first, so it can be called again) and its front rake."""
    global SHAPE, FACE_Y0
    assert name in ("b2", "round", "modern"), name
    SHAPE = name
    FACE_Y0 = SHAPE_FACE_Y0[name]
    CFG.clear()
    CFG.update(_copy.deepcopy(_CFG0))
    ROUND.clear()
    ROUND.update(_copy.deepcopy(_ROUND0))
    set_rake(SHAPE_RAKE[name] if rake is None else rake)
    if name == "modern":
        ROUND.update(MODERN["round"])
        CFG.update(MODERN["cfg"])
    if name in ("round", "modern"):
        for k in ("rf", "ws_bottom_x", "ws_top_x"):
            CFG[k] = ROUND[k]
        CFG["roof_r"] = ROUND["roof_h"]


def rounded():
    return SHAPE in ("round", "modern")


def modern():
    return SHAPE == "modern"


class ShiftLoft(Loft):
    """View of a loft whose front parametrisation is shifted (lamp unit placed elsewhere on the same surface)."""

    def __init__(self, base, dx, dz):
        self.__dict__.update(base.__dict__)
        self._b, self._dx, self._dz = base, dx, dz

    def front_pt(self, z, x, off):
        return self._b.front_pt(z + self._dz, x + (self._dx if x >= 0 else -self._dx), off)


def lamp_loft():
    dx, dz = CFG.get("lamp_shift", (0.0, 0.0))
    return ShiftLoft(CAB, dx, dz) if (dx or dz) else CAB
LOW = None    # Loft of the lower fairing


def mirror_poly(poly):
    return [(-x, z) for x, z in reversed(poly)]


def full_grille(poly_r):
    left = [(-x, z) for x, z in reversed(poly_r[1:-1])]
    return poly_r[:-1] + [(0.0, poly_r[-1][1])] + left


def round_poly(pts, r, n=4):
    """Convex polygon [(a, b)] with every corner replaced by an arc of radius r tangent to both edges."""
    out = []
    m = len(pts)
    for i in range(m):
        p0, p1, p2 = V((*pts[i - 1], 0)), V((*pts[i], 0)), V((*pts[(i + 1) % m], 0))
        u, w = (p0 - p1).normalized(), (p2 - p1).normalized()
        half = math.acos(max(-1.0, min(1.0, u.dot(w)))) / 2
        t = r / math.tan(half)
        c = p1 + (u + w).normalized() * (r / math.sin(half))
        a, b = p1 + u * t - c, p1 + w * t - c
        ang = a.angle(b)
        axis = 1.0 if a.cross(b).z > 0 else -1.0
        for k in range(n + 1):
            q = Matrix.Rotation(axis * ang * k / n, 3, "Z") @ a
            out.append((c.x + q.x, c.y + q.y))
    return out


WIN_R = 0.08     # side window corner radius (modern, owner r2: R 60-100 mm)


def win_outline(grow=0.0, front=None, rear=None):
    """Side window outline (y, z), CCW; modern: rounded corners. grow = outward offset (frame outer edge)."""
    y0 = (WIN_REAR if rear is None else rear) - grow
    zb, zt = BELT_Z - grow * 0.85, WIN_TOP + grow
    wf = lambda z: (win_front(z) if front is None else front(z)) + grow  # noqa: E731
    quad = [(y0, zb), (wf(zb), zb), (wf(zt), zt), (y0, zt)]
    return round_poly(quad, WIN_R + grow, 4) if modern() else quad


def win_front(z):
    """Side window front edge (y): just onto the corner arc, parallel to the A-pillar."""
    yf, yb, w, rf, rb = CAB.sec(z)
    if rounded():
        return CAB.plan(z)[6] + ROUND["win_front"]
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
               arc_n=16, step=0.035, flat_n=6, roof_n=9)   # B2 v2: denser shell (smooth corner highlights, budget 140k)
    if rounded():   # 2 cm arc chords on the R 0.34 corners and 3 cm on the roof radius: no facets in the highlights
        CAB = Loft(CFG["front"], CAB_BACK_Y, CFG["w"], CFG["rf"], CFG["rb"], CAB_Z0, ROOF_Z, roof_r=CFG["roof_r"],
                   arc_n=20 if modern() else 26, step=0.045 if modern() else 0.035, flat_n=6,
                   roof_n=10 if modern() else 12, crown=ROUND["crown"], roof_rr=ROUND["roof_rr"],
                   front_n=10 if modern() else 12)
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
        if modern():
            cut.append(CAB.poly_patch(f"cut_win_{s}", "gap", "side", win_outline(), off=-0.10, thick=0.25, side=s,
                                      sub=4))
        else:
            cut.append(CAB.quad_patch(f"cut_win_{s}", "gap", "side",
                                      [(WIN_REAR, BELT_Z), (win_front(BELT_Z), BELT_Z),
                                       (win_front(WIN_TOP), WIN_TOP), (WIN_REAR, WIN_TOP)],
                                      off=-0.10, thick=0.25, side=s, nu=28, nv=6))
        lamp = CFG["lamp"] if s > 0 else mirror_poly(CFG["lamp"])
        cut.append(lamp_loft().poly_patch(f"cut_lamp_{s}", "lamp_inner", "front", lamp, off=-0.07, thick=0.20, sub=6))
        cut.append(CAB.patch(f"cut_handle_{s}", "plastic", "side", 1.38, 2.32, HANDLE_Y[0], HANDLE_Y[1], off=-0.06,
                             thick=0.15, side=s, nz=2, npar=2))
    for k in ("stem", "bar"):
        if modern():   # the T bar wraps the corners: dense quad cutter
            cut.append(CAB.quad_patch("cut_" + k, "plastic", "front", CFG[k], off=-MASK_POCKET, thick=0.20, nu=48,
                                      nv=3))
        else:
            cut.append(CAB.poly_patch("cut_" + k, "grille_mesh", "front", CFG[k], off=-0.07, thick=0.20, sub=5))
    boolean(sh, cut)
    sh.data.shade_smooth()
    if hasattr(sh.data, "set_sharp_from_angle"):
        sh.data.set_sharp_from_angle(angle=math.radians(50))
    cab_floor_pan()
    return sh


FLOOR_PAN_DZ = 0.025     # m above the cab's lower edge (interior floor slab underside: +0.075 m)


def cab_floor_pan():
    """r7c (ADR 0047): underside of the cab. The shell is a tube without a bottom; through the 15 mm tilt joint
    between the cab and the frame-mounted fairing a low camera in front of the truck looked up at the underside of
    the interior floor slab (front_leak.py, eye front-low: 65 rays). One dark sheet 25 mm above the cab's lower edge,
    its outline 18 mm inside the skin (within the 30 mm wall), facing down."""
    z = CAB_Z0 + FLOOR_PAN_DZ
    ring = CAB.ring(z)
    xs, ys = [p[0] for p in ring], [p[1] for p in ring]
    cy = (max(ys) + min(ys)) / 2
    fx = 1.0 - 0.018 / max(xs)
    fy = 1.0 - 0.018 / ((max(ys) - min(ys)) / 2)
    pts = [(x * fx, cy + (y - cy) * fy) for x, y in ring[::3]]   # chords of the corner arcs lie inside them
    bm = bmesh.new()
    bm.faces.new([bm.verts.new((x, y, z)) for x, y in pts])
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    ob = G.obj_from_bm("cab_floor_pan", bm, "interior", smooth=False)
    if ob.data.polygons[0].normal.z > 0:
        ob.data.flip_normals()
    return ob


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
        if modern():   # rounded glass + one frame band following the rounded outline
            ribbon(f"win_frame_r_{s}", win_outline(grow=0.034), 0.044, "plastic_satin", off=0.002, thick=0.0,
                   kind="side", side=s, nu=1)
            CAB.poly_patch(f"side_glass_{s}", "glass", "side", win_outline(), off=0.0045, side=s, sub=4)
            CAB.gap_h(f"belt_seal_{s}", s, BELT_Z - 0.012, y0 - 0.03 + WIN_R, win_front(BELT_Z) + 0.03 - WIN_R,
                      w=0.012, off=0.006, m="rubber")
            continue
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
        # B2.1 (owner sheets): no door skirt - the door's lower edge is the cab edge (1.225 m) and the step well
        # behind the wheel stays open below it; a dark seal lip marks the door bottom over the steps
        CAB.gap_h(f"door_gap_b_{s}", s, CAB_Z0 + 0.006, DOOR_REAR - 0.006, DOOR_FRONT_LOW + 0.006, w=0.008, off=0.004)
        if modern():   # dark sill cladding with a soft kick-up towards the rear, running into the lamp's lower edge
            ya, yb = CAB_BACK_Y + 0.10, 1.19
            zt = lambda y: 1.430 + (1.300 - 1.430) * (y - ya) / (yb - ya)  # noqa: E731
            for nm, y0, y1, nu in ((f"sill_clad_r_{s}", ya, DOOR_REAR - 0.006, 4),
                                   (f"door_skirt_clad_{s}", DOOR_REAR + 0.006, DOOR_FRONT_LOW - 0.006, 6),
                                   (f"sill_clad_f_{s}", DOOR_FRONT_LOW + 0.006, yb, 14)):
                CAB.quad_patch(nm, "plastic", "side", [(y0, CAB_Z0 + 0.004), (y1, CAB_Z0 + 0.004), (y1, zt(y1)),
                                                       (y0, zt(y0))], off=0.003, side=s, nu=nu, nv=1, thick=0.006)
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
    if modern():      # the mask itself is the service flap, its pocket edge is the joint
        return
    hx, ht = 0.815, WS_Z0 - 0.085     # B2 v2: the grille is the tilting flap; top under the cowl
    CAB.patch("hatch_gap_top", "gap", "front", ht - 0.0035, ht + 0.0035, -hx, hx, off=0.0012, nz=1, npar=30)
    for s in (-1, 1):
        z_l = CAB_Z0 + 0.012
        CAB.patch(f"hatch_gap_side_{s}", "gap", "front", z_l, ht, s * hx - 0.0035, s * hx + 0.0035, off=0.0012,
                  nz=4, npar=1)


# ---------------------------------------------------------------- front face: grille, brand, cowl, wipers
# r8 (ADR 0061): stroke = 2.2 x the SVG width = 28 mm at the 150 mm cap height (1.8 = 24 mm): 3.5 px in truck-34 at the
# Low tier's 0.75 render scale. Counters stay open (R bowl 36 x 57 mm). WORKING_VALUE
WORDMARK_WEIGHT = 2.2
LOUVRE_TILT = 20.0   # deg, WORKING_VALUE: lamella faces look down at the road, not at the sky (ADR 0047 r4)


def lane_dash(name, loft, zc, hgt, off, tilt=0.0):
    """TRAKT motif: one dash of the road centre line (brushed aluminium) on the mask's centreline.
    tilt: the dash lies on a face-down lamella (same angle), off is then measured at the lamella's mid height."""
    box(name, V(loft.front_pt(zc, 0.0, off)), (0.024, 0.005, hgt), "alu_brushed", bev=0.0015, seg=1,
        rot=Matrix.Rotation(math.radians(RAKE - tilt), 3, "X"))


def mask_tray(name, m, quad, nu, nv, off=-0.066, rim=-0.026, grow=0.002):
    """Back of a mask pocket as a tray: the panel `off` below the skin plus a rim up to the inner face of the 30 mm
    shell wall (r7b, review r6 E-N2). The pockets are holes through the shell; with a flat panel alone a 36 mm slot
    stayed open all round between the wall and the panel, and a camera looking along the 4 mm joint of the T bar or
    between the louvres at an angle saw past the panel into the cab. The tray is 2 mm wider than the opening, so its
    rim hides behind the wall edge."""
    (p00, z00), (p10, z10), (p11, z11), (p01, z01) = quad
    g = grow
    q = [(p00 - g, z00 - g), (p10 + g, z10 - g), (p11 + g, z11 + g), (p01 - g, z01 + g)]

    def at(u, v):
        pp = (q[0][0] * (1 - u) + q[1][0] * u) * (1 - v) + (q[3][0] * (1 - u) + q[2][0] * u) * v
        zz = (q[0][1] * (1 - u) + q[1][1] * u) * (1 - v) + (q[3][1] * (1 - u) + q[2][1] * u) * v
        return pp, zz
    bm = bmesh.new()
    grid = [[bm.verts.new(CAB.front_pt(at(j / nu, i / nv)[1], at(j / nu, i / nv)[0], off)) for j in range(nu + 1)]
            for i in range(nv + 1)]
    for i in range(nv):
        for j in range(nu):
            bm.faces.new((grid[i][j], grid[i][j + 1], grid[i + 1][j + 1], grid[i + 1][j]))
    edge = ([(0, j) for j in range(nu)] + [(i, nu) for i in range(nv)] + [(nv, j) for j in range(nu, 0, -1)]
            + [(i, 0) for i in range(nv, 0, -1)])
    top = [bm.verts.new(CAB.front_pt(at(j / nu, i / nv)[1], at(j / nu, i / nv)[0], rim)) for i, j in edge]
    k = len(edge)
    for e in range(k):
        (i0, j0), (i1, j1) = edge[e], edge[(e + 1) % k]
        bm.faces.new((grid[i0][j0], grid[i1][j1], top[(e + 1) % k], top[e]))
    ob = G.obj_from_bm(name, bm, m, sharp=60)
    me = ob.data          # the tray is seen from the front: the panel faces forward, the rim faces the pocket
    mid = me.polygons[(nv // 2) * nu + nu // 2]
    if mid.normal.dot(CAB.normal_front(at(0.5, 0.5)[1], at(0.5, 0.5)[0])) < 0:
        me.flip_normals()
    return ob


def front_face_modern(strokes):
    """Gloss-black road-T mask (see MODERN): T bar panel + louvred stem with the lane-line dashes."""
    st, br = CFG["stem"], CFG["bar"]
    mask_tray("grille_back_stem", "grille_honey", st, nu=24, nv=4)
    mask_tray("grille_back_bar", "plastic", br, nu=48, nv=2)
    zb0, zb1 = br[0][1] + 0.004, br[2][1] - 0.004
    hw_bar = br[1][0] - 0.004 - MASK_CAP_W - 0.0012
    mask_bar("grille_bar_mask", (zb0 + zb1) / 2, zb1 - zb0, 0.060, hw_bar)
    for s in (-1, 1):   # brushed-aluminium end cap of the T bar (same metal as the letters and the lane dashes)
        x0, x1 = s * (hw_bar + 0.0012), s * (hw_bar + 0.0012 + MASK_CAP_W)
        cap = CAB.quad_patch(f"grille_bar_endcap_{s}", "alu_brushed", "front",
                             [(min(x0, x1), zb0 + 0.010), (max(x0, x1), zb0 + 0.010), (max(x0, x1), zb1 - 0.010),
                              (min(x0, x1), zb1 - 0.010)], off=-0.014, thick=0.0125, nu=1, nv=6)
        G.apply_mods(bevel(cap, 0.003, seg=2, angle=50))
    z0, pitch, cnt, hgt = CFG["louvres"]
    for k in range(cnt):
        zc = z0 + pitch * k
        hw = st[1][0] + (st[2][0] - st[1][0]) * (zc - st[1][1]) / (st[2][1] - st[1][1]) - 0.006
        grille_bar(f"grille_bar_l{k}", zc, hgt, 0.052, hw, "mask_gloss", nose=-0.004, tilt=LOUVRE_TILT)
        lane_dash(f"lane_dash{k}", CAB, zc, hgt - 0.016, louvre_mid(hgt) + 0.0015, tilt=LOUVRE_TILT)
    wordmark(strokes, z_c=CFG["wordmark_z"], height=CFG["wordmark_h"], spacing=24.0, mat="alu_brushed",
             name="badge_trakt", weight=WORDMARK_WEIGHT, depth=0.004, on_face=True)
    # r7c: 2 -> 4 mm off the skin. The hidden-face test starts 3 mm above a face, so the paint under a 2 mm cowl
    # counted as visible, stayed in the mesh and came through the cowl as white shards once LOD2 had collapsed it
    CAB.patch("cowl", "plastic_satin", "front", WS_Z0 - 0.082, WS_Z0 - 0.012, -1.21, 1.21, off=0.004, nz=3, npar=48)
    wipers()


def front_face(feathers, strokes):
    set_group("cab")
    if modern():
        return front_face_modern(strokes)
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
        grille_bar(f"grille_bar{k}", zc, hgt, depth, gx(zc) - 0.004, m_, round_front=(k == 0 or m_ == "paint"),
                   nose=0.0 if k == 0 else -0.003,
                   nose_r=0.004 if k == 0 else 0.015)   # B2.2: 99 mm flat face for the 91 mm letters
    # frame: raised graphite band along the T outline (outer edge flush with the pocket edge)
    st, br = CFG["stem"], CFG["bar"]
    xs = gx(br[0][1] - 1e-6)
    outline = [st[0], st[1], (xs, br[0][1]), br[1], br[2], br[3], br[0], (-xs, br[0][1])]
    outline = [p for i, p in enumerate(outline)          # B2 v2: rectangular grille -> drop repeated corners
               if math.hypot(p[0] - outline[i - 1][0], p[1] - outline[i - 1][1]) > 1e-4]
    top = br[2][1]                                        # B2.2: 8 mm top lip over the wordmark band, 22 mm elsewhere
    fw = [0.008 if abs(p[1] - top) < 1e-6 and abs(outline[(i + 1) % len(outline)][1] - top) < 1e-6 else 0.022
          for i, p in enumerate(outline)]
    ribbon("grille_frame", outline, fw, "trim_graphite", off=-0.004, thick=0.010)
    if CFG["emblem_z"] is not None:
        emblem(feathers)
    # B2 v2: real satin-silver letters (3 mm) on the black band - kept as game geometry ('badge_'), not the
    # paint-slot decal (a decal can only tint the Paint slot, it cannot draw light letters on dark trim)
    # B2.2: letters lie in the raked band, 1.6x stroke (12 mm at 80 mm cap height), 4 mm deep, 1.2 mm chamfer,
    # brushed aluminium (bright, anisotropic) so the A crossbar and the R leg survive a 3/4 view on a phone
    wordmark(strokes, z_c=CFG["wordmark_z"], height=CFG["wordmark_h"], spacing=16.0, mat="alu_brushed",
             name="badge_trakt", weight=1.6, depth=0.004, on_face=True, bev=0.0012)
    # flush cowl (wiper panel) in the same plane, between the service flap and the glass edge
    CAB.patch("cowl", "plastic", "front", WS_Z0 - 0.082, WS_Z0 - 0.012, -1.12, 1.12, off=0.002, nz=3, npar=40)
    # B2 v2: no slot row - in the game atlas it baked into a black/grey comb; the plain black cowl now merges with
    # the black wordmark band below and the frit above (owner sheets: one dark band from the grille to the glass)
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


def ribbon(name, poly, width, m, off=-0.004, thick=0.01, kind="front", loft=None, side=1, nu=6):
    """Frame band of `width` running inside a closed CCW polygon [(x, z)] on the cab surface (one strip per
    edge, mitred corners), raised `thick` from `off`. `width` may be a list with one width per edge i -> i+1."""
    n = len(poly)
    wd = list(width) if isinstance(width, (list, tuple)) else [width] * n

    def inward(i):
        (x0, z0), (x1, z1) = poly[i], poly[(i + 1) % n]
        ln = math.hypot(x1 - x0, z1 - z0)
        return (-(z1 - z0) / ln, (x1 - x0) / ln)
    inner = []
    for i in range(n):
        na, nb = inward(i - 1), inward(i)
        wa, wb = wd[i - 1], wd[i]
        det = na[0] * nb[1] - na[1] * nb[0]
        if abs(wa - wb) < 1e-9 or abs(det) < 0.05:
            k = wb / max(1.0 + na[0] * nb[0] + na[1] * nb[1], 0.2)   # mitre: distance `width` to both edges
            inner.append((poly[i][0] + (na[0] + nb[0]) * k, poly[i][1] + (na[1] + nb[1]) * k))
        else:                                                # unequal widths: q with q.na = wa, q.nb = wb
            inner.append((poly[i][0] + (wa * nb[1] - wb * na[1]) / det, poly[i][1] + (wb * na[0] - wa * nb[0]) / det))
    for i in range(n):
        j = (i + 1) % n
        (xa, za), (xb, zb) = poly[i], poly[j]
        (ia, ka), (ib, kb) = inner[i], inner[j]
        (loft or CAB).quad_patch(f"{name}_{i}", m, kind, [(xa, za), (xb, zb), (ib, kb), (ia, ka)], off=off, nu=nu, nv=1,
                       thick=thick, side=side)


MASK_ROLL = 0.010      # m, WORKING_VALUE: the T bar's top and bottom 40 mm roll back by this much (r6 E-N2)
MASK_FLAT = 0.080      # m: half height of the flat band that carries the letters
MASK_CHAMFER = 0.014   # m: chamfer at the bar's two wrapped ends
MASK_CAP_W = 0.016     # m: brushed-aluminium end cap
# m: depth of the mask pockets (T bar and stem) below the cab skin. Deeper than the 30 mm wall of the shell contract, so
# it is published to the interior (glass_interface.json shell_sections.front_pockets, ADR 0047 r7b): the interior has to
# stay behind the pocket floor there, or the game camera sees it past the bar and between the louvres.
MASK_POCKET = 0.070
LAMP_POCKET = 0.052    # m: back of the headlamp housing below the skin (published the same way)


def mask_bar(name, zc, hgt, depth, hw, m="mask_gloss", nose=0.001, n=72, nose_r=0.016):
    """Gloss-black T bar of the modern mask (review r6 E-N2: its wrapped corners read as flat black holes with a knife
    edge against the paint). The section is no longer one flat face: the middle band (letters) stays flat, the top
    and bottom 40 mm roll back (the top mirrors the sky, the bottom the ground: a vertical gradient instead of one
    horizon-coloured slab); 72 columns keep the R 0.36 m corner at < 3 deg per facet; both ends finish in a 14 mm
    chamfer facing outboard."""
    h = hgt / 2
    r = min(nose_r, h * 0.3)

    def fo(dz):
        t = max(0.0, (abs(dz) - MASK_FLAT) / (h - MASK_FLAT))
        return nose - MASK_ROLL * t * t
    zs = [-h + r, -h + r + 0.008, -h + r + 0.016, -MASK_FLAT, 0.0, MASK_FLAT, h - r - 0.016, h - r - 0.008, h - r]
    e = fo(h - r)
    sec = ([(-h, -depth, 0), (-h, e - r, 1), (-h + r * 0.3, e - r * 0.3, 1)] + [(dz, fo(dz), 1) for dz in zs]
           + [(h - r * 0.3, e - r * 0.3, 1), (h, e - r, 1), (h, -depth, 0)])
    c = MASK_CHAMFER
    cols = [(-hw, -c)] + [(-hw + c + 2 * (hw - c) * j / n, 0.0) for j in range(n + 1)] + [(hw, -c)]
    bm = bmesh.new()
    rows = [[bm.verts.new(CAB.front_pt(zc + dz, x, o + d * k)) for x, d in cols] for dz, o, k in sec]
    k = len(rows)
    for a in range(k):
        r0, r1 = rows[a], rows[(a + 1) % k]
        for j in range(len(cols) - 1):
            bm.faces.new((r0[j], r0[j + 1], r1[j + 1], r1[j]))
    for j in (0, len(cols) - 1):
        bm.faces.new([rw[j] for rw in rows])
    return G.obj_from_bm(name, bm, m, sharp=40)


def louvre_mid(hgt, nose=-0.004, tilt=None):
    """Offset of a face-down lamella's face from the front surface at its mid height."""
    return nose - 0.5 * hgt * math.tan(math.radians(LOUVRE_TILT if tilt is None else tilt))


def grille_bar(name, zc, hgt, depth, hw, m, round_front=True, n=2, nose=-0.003, nose_r=0.015, loft=None,
               tilt=0.0):   # flat front: n=2 is exact
    """Horizontal grille bar following the cab front: body-colour bars get a rounded nose, graphite bars a
    louvre face tilted up (different depth and section, so the field never reads as identical slats).
    nose = offset of the bar face from the cab surface (0 = flush, carries the wordmark decal)."""
    h = hgt / 2
    if tilt:
        # face-down lamella (modern mask): the top edge is the nose, the face falls back towards the bottom edge
        # by hgt * tan(tilt), so its normal points forward and DOWN: it mirrors the road / the dark ground instead
        # of the sky, and the top land (4 mm radius + the shadowed gap above) is all that looks up
        t = hgt * math.tan(math.radians(tilt))
        r = 0.004
        fo = lambda dz: nose - t * (h - dz) / hgt          # noqa: E731  face offset at height dz
        prof = [(-h, -depth), (-h, fo(-h)), (h - r, fo(h - r)), (h - r * 0.3, fo(h - r * 0.3) - r * 0.25),
                (h, nose - r), (h, -depth)]
    elif round_front:
        r = min(nose_r, h * 0.6)
        prof = [(-h, -depth), (-h, nose - r), (-h + r * 0.3, nose - r * 0.3), (-h + r, nose), (h - r, nose),
                (h - r * 0.3, nose - r * 0.3), (h, nose - r), (h, -depth)]
    else:
        prof = [(-h, -depth), (-h, -0.024), (-h * 0.6, -0.022), (h, -0.011), (h, -depth)]
    bm = bmesh.new()
    rows = []
    if rounded():
        n = max(n, 12 if modern() else 16)            # crowned face: the bar follows the plan curve
    for dz, o in prof:
        rows.append([bm.verts.new((loft or CAB).front_pt(zc + dz, -hw + 2 * hw * j / n, o)) for j in range(n + 1)])
    k = len(rows)
    for a in range(k):
        r0, r1 = rows[a], rows[(a + 1) % k]
        for j in range(n):
            bm.faces.new((r0[j], r0[j + 1], r1[j + 1], r1[j]))
    for j in (0, n):
        bm.faces.new([r[j] for r in rows])
    return G.obj_from_bm(name, bm, m, sharp=55)


def wordmark(strokes, z_c=1.918, height=0.052, spacing=30.0, mat="wordmark", name="wordmark", origin=None,
             weight=1.0, depth=0.003, on_face=False, bev=0.0):
    """TRAKT letters from the SVG polylines (own geometric monoline), letter-spaced, extruded `depth`.
    weight scales the SVG stroke width; on_face=True lays every stroke in the raked front plane (each stroke
    centred on the face at its own height and tilted by RAKE) instead of an upright box at the plane's z_c point."""
    if on_face:
        return _wordmark_on_face(strokes, z_c, height, spacing, mat, name, weight, depth, bev)
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


def _wordmark_on_face(strokes, z_c, height, spacing, mat, name, weight, depth, bev):
    """Badge letters lying in the front face: ONE welded prism per letter (`name`_<letter index>).
    r8 (ADR 0061): until r7c every stroke was its own bevelled box, overlapping its neighbours at the joints with a
    0.15-0.2 mm depth stagger. In the game frames the joints showed as dark notches (AO baked on the buried part of
    the lower stroke, depth fighting at 12 m), every stroke had its own 3 px atlas island and its own 1.2 mm chamfer
    (a highlight line far below a pixel): the letters crawled and broke up on the Low tier. Now the strokes of a
    letter are united (EXACT boolean on prisms that share the front and back plane), the front is one flat face, the
    4 mm walls are plain (bev is ignored: a chamfer that never reaches a pixel only aliases).
    Stroke ends as before (B2.2): square cap at a free end, mitre at an inner joint; an end that butts into another
    stroke runs into it."""
    ys = [p[1] for pl, w in strokes for p in pl]
    y0, y1 = min(ys), max(ys)
    wmax = max(w for _, w in strokes) * weight
    sc = height / (y1 - y0 + wmax)
    bounds = [192, 239, 293, 347, 401, 460]  # letter x-ranges in trakt.svg: T R A K T

    def idx(x):
        for i, b in enumerate(bounds[1:]):
            if x < b:
                return i
        return len(bounds) - 2
    allx = [x + idx(min(p[0] for p in pl)) * spacing for pl, w in strokes for x, _ in pl]
    xc = (min(allx) + max(allx)) / 2

    def turn(p0, p1, p2):   # turn angle at p1 between segments p0-p1 and p1-p2 (0 = straight on)
        u = V((p1[0] - p0[0], 0, p1[1] - p0[1])).normalized()
        v = V((p2[0] - p1[0], 0, p2[1] - p1[1])).normalized()
        return math.acos(max(-1.0, min(1.0, u.dot(v))))

    def butts(p, k, j):     # does point p (SVG units) lie on a segment other than its own (k, j)?
        for k2, (pl2, _) in enumerate(strokes):
            for j2, (q0, q1) in enumerate(zip(pl2, pl2[1:])):
                if (k2, j2) == (k, j):
                    continue
                ex, ey = q1[0] - q0[0], q1[1] - q0[1]
                t = max(0.0, min(1.0, ((p[0] - q0[0]) * ex + (p[1] - q0[1]) * ey) / (ex * ex + ey * ey)))
                if math.hypot(p[0] - q0[0] - t * ex, p[1] - q0[1] - t * ey) < 0.5:
                    return True
        return False
    letters = {}            # letter index -> stroke rectangles in the letter plane: (centre x, centre z, len, 2 hw, angle)
    for k, (pl, w) in enumerate(strokes):
        li = idx(min(p[0] for p in pl))
        off = li * spacing
        for j, (a, b) in enumerate(zip(pl, pl[1:])):
            ax, az = -(a[0] + off - xc) * sc, -(a[1] - (y0 + y1) / 2) * sc   # viewer's left = +X
            bx, bz = -(b[0] + off - xc) * sc, -(b[1] - (y0 + y1) / 2) * sc
            d = V((bx - ax, 0, bz - az))
            ln = d.length
            if ln < 1e-6:
                continue
            hw = w * weight * sc / 2
            e0 = (0.0 if butts(a, k, j) else hw) if j == 0 else hw * min(1.0, math.tan(turn(pl[j - 1], a, b) / 2))
            e1 = ((0.0 if butts(b, k, j) else hw) if j == len(pl) - 2
                  else hw * min(1.0, math.tan(turn(a, b, pl[j + 2]) / 2)))
            # a butting end runs 40 % of a stroke width into the stroke it meets: the union needs a real overlap
            e0 = e0 if e0 > 0 else 0.4 * hw
            e1 = e1 if e1 > 0 else 0.4 * hw
            dn = d / ln
            ax, az = ax - dn.x * e0, az - dn.z * e0
            bx, bz = bx + dn.x * e1, bz + dn.z * e1
            letters.setdefault(li, []).append(((ax + bx) / 2, (az + bz) / 2, ln + e0 + e1, 2 * hw,
                                               math.atan2(d.z, d.x)))
    out = []
    for li, rects in sorted(letters.items()):
        cx = sum(r[0] for r in rects) / len(rects)
        prisms = []
        for q, (mx, mz, ln, wd, ang) in enumerate(rects):
            bm = bmesh.new()
            bmesh.ops.create_cube(bm, size=1.0)
            # letter plane: x across, z up, y = out of the face (0 .. depth)
            bmesh.ops.scale(bm, vec=V((ln, depth, wd)), verts=bm.verts)
            bmesh.ops.rotate(bm, verts=bm.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-ang, 3, "Y"))
            bmesh.ops.translate(bm, vec=V((mx - cx, depth / 2, mz)), verts=bm.verts)
            prisms.append(G.obj_from_bm(f"{name}_{li}_p{q}", bm, mat, smooth=False))
        ob = prisms[0]
        ob.name = f"{name}_{li}"
        if len(prisms) > 1:
            G.boolean(ob, prisms[1:], op="UNION")
        # weld the union, merge coplanar triangles, then lay the letter on the face: origin on the surface at the
        # letter centre, x along the surface, z up the raked face, y = the surface normal
        o = V(CAB.front_pt(z_c, cx, 0.0))
        n = CAB.normal_front(z_c, cx)
        up = (V(CAB.front_pt(z_c + 0.05, cx, 0.0)) - V(CAB.front_pt(z_c - 0.05, cx, 0.0))).normalized()
        rt = up.cross(n).normalized()
        if rt.x < 0:
            rt = -rt
        up = n.cross(rt).normalized()
        if up.z < 0:
            up = -up
        bm = bmesh.new()
        bm.from_mesh(ob.data)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        for _ in range(3):
            bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), verts=bm.verts, edges=bm.edges)
            # vertices left on a straight outline edge (two collinear edges, nothing else)
            lone = [v for v in bm.verts if len(v.link_edges) == 2 and abs(
                (v.link_edges[0].other_vert(v).co - v.co).normalized().dot(
                    (v.link_edges[1].other_vert(v).co - v.co).normalized()) + 1.0) < 1e-6]
            if not lone:
                break
            bmesh.ops.dissolve_verts(bm, verts=lone)
        # triangles here, not in the exporter: the union leaves vertices on straight outline edges (where a wall of
        # one stroke ends on the face of another), the n-gon fill made zero-area triangles of them and the FBX
        # round trip dropped those (check_export: 9 triangles fewer than the manifest)
        bmesh.ops.triangulate(bm, faces=bm.faces, ngon_method="BEAUTY")
        bmesh.ops.dissolve_degenerate(bm, dist=2e-5, edges=bm.edges)
        flat = [f for f in bm.faces if f.calc_area() < 1e-10]
        if flat:    # collinear leftovers: no area, so no crack opens when they go
            bmesh.ops.delete(bm, geom=flat, context="FACES")
        print(f"  {ob.name}: {len(bm.faces)} triangles ({len(flat)} zero-area dropped)")
        for v in bm.verts:
            v.co = o + rt * v.co.x + n * (v.co.y + 0.0010) + up * v.co.z
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(ob.data)
        bm.free()
        ob.data.shade_flat()
        if ob.data.validate():      # what the FBX importer would drop (doubled / degenerate faces): drop it here, so
            ob.data.update()        # the manifest counts the triangles that really reach the game
            print(f"  {ob.name}: validate() removed invalid faces, {len(ob.data.polygons)} triangles left")
        out.append(ob)
    return out


def wiper_boss(name, px, z, r=0.022, h0=0.0025, h1=0.029, seg=16):
    """Spindle boss of a wiper: a short drum standing on the cowl along the surface normal (= the sweep axis of
    WIPER_L / WIPER_R in a6_export.frames), top edge chamfered, no bottom face.
    r7c (ADR 0047): the old cap was a vertical drum half sunk into the skin (at x -1.00 m the corner slopes away, so
    its rear and inboard faces lay inside the 30 mm shell). Wipers are moving parts and keep all their faces, and
    the selected-to-active bake gave those buried faces the colour of the first surface on the ray: the white paint
    of the shell. 4 of the 12 texel rows of the cap's atlas island were white (sRGB 0.78 beside 0.19); from 12 m
    the mips blend them and the cap showed as a light block on the dark cowl."""
    n = CAB.normal_front(WS_Z0, px)          # exactly the sweep axis: the boss turns about itself
    base = V(CAB.front_pt(z, px, 0.0))
    t = n.cross(V((0, 0, 1))).normalized()
    b = t.cross(n).normalized()
    ch = 0.004
    prof = [(r, h0), (r, h1 - ch), (r - ch, h1)]
    bm = bmesh.new()
    rings = [[bm.verts.new(base + n * h + (t * math.cos(2 * math.pi * i / seg) + b * math.sin(2 * math.pi * i / seg))
                           * rr) for i in range(seg)] for rr, h in prof]
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(seg):
            bm.faces.new((r0[i], r0[(i + 1) % seg], r1[(i + 1) % seg], r1[i]))
    bm.faces.new(rings[-1])
    ob = G.obj_from_bm(name, bm, "plastic_satin", sharp=40)
    # an open shell: recalc_face_normals may turn it inside out. Outward = away from the axis, +n on the lid
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    for f in bm.faces:
        c = f.calc_center_median()
        radial = (c - base) - n * (c - base).dot(n)
        out = n if radial.length < r * 0.5 else radial
        if f.normal.dot(out) < 0:
            f.normal_flip()
    bm.to_mesh(ob.data)
    bm.free()
    return ob


def wiper_arm(name, p0, p1, nrm, m, w0=0.030, w1=0.022, w2=0.018, t0=0.010, t1=0.006, head=0.22):
    """Wiper arm as a flat tapered strap lying parallel to the glass: cast head (w0 -> w1 over `head` of the length),
    then the spring strap down to w2 at the blade. r8 (ADR 0061): the arm was a 16 mm eight-sided rod. Its up-facing
    facets mirrored the sky at grazing angles and were 2-3 mm wide: on the dark cowl the arm rendered as a row of
    light dots (truck-34: 2 px on High, 1.2 px on Low). The strap shows the game cameras one face, 18-30 mm wide,
    with the normal of the glass."""
    p0, p1 = V(p0), V(p1)
    d = (p1 - p0).normalized()
    wv = d.cross(V(nrm)).normalized()
    nv = wv.cross(d).normalized()
    ln = (p1 - p0).length
    bm = bmesh.new()
    rings = []
    for f, w, t in ((0.0, w0, t0), (head, w1, t1), (1.0, w2, t1)):
        c = p0 + d * (ln * f)
        rings.append([bm.verts.new(c + wv * (sx * w / 2) + nv * (sy * t / 2))
                      for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(4):
            bm.faces.new((r0[i], r0[(i + 1) % 4], r1[(i + 1) % 4], r1[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return G.obj_from_bm(name, bm, m, smooth=False)


def wiper_blade(name, base, nrm, m, wdt=0.024, foot=0.004, shoulder=0.011, ridge=0.024):
    """Flat (aero) wiper blade along `base` (points on the glass, with their surface normals `nrm`): a five-sided
    section, `wdt` wide across the glass, with the spoiler ridge on the upper side. r8: was an 18 mm round tube."""
    bm = bmesh.new()
    rings = []
    n = len(base)
    for i, (p, nn) in enumerate(zip(base, nrm)):
        t = (base[min(i + 1, n - 1)] - base[max(i - 1, 0)]).normalized()
        g = nn.cross(t).normalized()          # across the blade, in the glass plane
        if g.z < 0:
            g = -g                            # +g = up the glass
        rings.append([bm.verts.new(p + g * a + nn * h) for a, h in
                      ((-wdt / 2, foot), (wdt / 2, foot), (wdt / 2, shoulder), (wdt * 0.15, ridge),
                       (-wdt / 2, shoulder))])
    k = len(rings[0])
    for r0, r1 in zip(rings, rings[1:]):
        for i in range(k):
            bm.faces.new((r0[i], r0[(i + 1) % k], r1[(i + 1) % k], r1[i]))
    bm.faces.new(list(reversed(rings[0])))
    bm.faces.new(rings[-1])
    return G.obj_from_bm(name, bm, m, smooth=False)


def wipers():
    # A6.1 (interior critic r2 #7): parked blades lie on the glass just above the 75 mm bottom frit (frit top 2.135 m),
    # rising 16 mm towards the tip, so the driver sees them along the bottom of the screen as in real cabs (they were
    # at 2.095 m, hidden behind the frit). Pivots unchanged; the interior placeholder uses the same numbers.
    zb0, rise = WS_Z0 + FRIT_BOTTOM + 0.007 + 0.009, 0.016   # B2: follows the lower glass edge
    for k, (px, length) in enumerate(((-1.00, 0.86), (-0.08, 0.86))):
        y = CAB.front_pt(WS_Z0 + 0.025, px, 0.02)[1]
        p0 = V((px, y + 0.01, WS_Z0 - 0.025))
        wiper_boss(f"wiper_pivot{k}", px, WS_Z0 - 0.04)
        zt = zb0 + rise + 0.018
        tip = V((px + length, CAB.front_pt(zt, px + length, 0.03)[1], zt))
        wiper_arm(f"wiper_arm{k}", p0, tip, CAB.normal_front(zt, px + length * 0.5), "wiper_black")
        # blade lying on the glass along the base (the front is crowned R 10 m: 4 spans keep it within 0.5 mm)
        pts, nrm = [], []
        for i in range(5):
            x = px + 0.06 + (length - 0.04) * i / 4
            zz = zb0 + rise * (x - px) / length
            pts.append(V(CAB.front_pt(zz, x, 0.0)))
            nrm.append(CAB.normal_front(zz, x))
        wiper_blade(f"wiper_blade{k}", pts, nrm, "rubber")
        # washer nozzle on the cowl next to each pivot
        box((f"washer_nozzle{k}"), (px + 0.12, CAB.front_pt(WS_Z0 - 0.03, px + 0.12, 0)[1] + 0.006, WS_Z0 - 0.027),
            (0.022, 0.012, 0.010), "plastic_satin", bev=0.003)


def drl_guide(name, s, p0, p1, wdt=0.016, n=12):
    """LED light guide between two front-projection points (x, z) with a dark-chrome carrier behind it."""
    bm = bmesh.new()
    (x0, z0), (x1, z1) = p0, p1
    dx, dz = x1 - x0, z1 - z0
    ln = math.hypot(dx, dz)
    nx, nz = -dz / ln * wdt / 2, dx / ln * wdt / 2
    layers = []
    for o in (-0.036, -0.016):
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
    CAB.quad_patch(name + "_carrier", "lamp_housing", "front",
                   [(s * (x0 - k * nx), z0 - k * nz), (s * (x1 - k * nx), z1 - k * nz),
                    (s * (x1 + k * nx), z1 + k * nz), (s * (x0 + k * nx), z0 + k * nz)], off=-0.045, nu=n, nv=1)


def oriented_lathe(name, prof, p, nrm, m, seg=18):
    """Lathe around the local axis (+x along `nrm`), placed at p (lamp bowls, projector lenses)."""
    ob = G.lathe(name, prof, (0, 0, 0), m, seg=seg, axis="Z", sharp=50)
    rot = V((0, 0, 1)).rotation_difference(nrm).to_matrix().to_4x4()
    ob.data.transform(Matrix.Translation(p) @ rot)
    ob.data.update()
    return ob


def lens_dome(name, poly, m, crown=0.008, thick=0.005, rim_off=-0.001, sub=8):
    """Outer lamp lens: a crowned shell over a convex polygon [(x, z)] (front projection), with real edge
    thickness (outer + inner surface + rim wall), so the lens catches a highlight band along its crown and
    shows a lit edge at an angle (REVIEW r3 X1: 'no outer lens with thickness and reflection')."""
    bm = bmesh.new()
    n = len(poly)
    cp = sum(p for p, _ in poly) / n
    cz = sum(z for _, z in poly) / n
    rim = []
    for i in range(n):
        (pa, za), (pb, zb) = poly[i], poly[(i + 1) % n]
        for k in range(sub):
            t = k / sub
            rim.append((pa + (pb - pa) * t, za + (zb - za) * t))
    lv = (1.0, 0.85, 0.62, 0.36)          # ring scale towards the centroid
    rise = (0.0, 0.55, 0.88, 1.0)          # crown profile (fast rise at the edge, flat top)
    shells = []
    for o_in in (0.0, -thick):
        rings = []
        for l, r in zip(lv, rise):
            off = rim_off + crown * r + o_in
            rings.append([bm.verts.new(CAB.front_pt(cz + (z - cz) * l, cp + (p - cp) * l, off)) for p, z in rim])
        cv = bm.verts.new(CAB.front_pt(cz, cp, rim_off + crown + o_in))
        mm = len(rim)
        for ra, rb in zip(rings, rings[1:]):
            for i in range(mm):
                f = (ra[i], ra[(i + 1) % mm], rb[(i + 1) % mm], rb[i])
                bm.faces.new(f if o_in == 0.0 else tuple(reversed(f)))
        for i in range(mm):
            f = (rings[-1][i], rings[-1][(i + 1) % mm], cv)
            bm.faces.new(f if o_in == 0.0 else tuple(reversed(f)))
        shells.append(rings[0])
    a_, b_ = shells
    for i in range(len(a_)):
        j = (i + 1) % len(a_)
        bm.faces.new((a_[i], b_[i], b_[j], a_[j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return G.obj_from_bm(name, bm, m, sharp=55)


def reflector_funnel(name, s, cx, zc, rings, m="reflector"):
    """Faceted chrome funnel through rounded-rectangle rings [(w, h, r, off)] (front projection, centre (cx, zc),
    side s): flat-shaded facets between rings, normals facing out of the lamp (+y)."""
    bm = bmesh.new()
    vs = []
    for w, h, r, off in rings:
        pts = [(cx + px, zc + pz) for px, pz in rrect(w, h, r, 3)]
        vs.append([bm.verts.new(CAB.front_pt(z, s * x, off)) for x, z in pts])
    n = len(vs[0])
    for ra, rb in zip(vs, vs[1:]):
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((ra[i], ra[j], rb[j], rb[i]))
    bm.normal_update()
    if sum(f.normal.y * f.calc_area() for f in bm.faces) < 0:
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    return G.obj_from_bm(name, bm, m, sharp=20)


def lamp_cell(tag, s, x0, x1, z0, z1, beam):
    """One LED reflector module (rectangular, not a round 'eyeball'): dark-chrome frame with depth, faceted
    reflector floor, and either a slim projector lens (low beam) or an LED bar (high beam)."""
    rect = [(x0, z0), (x1, z0), (x1, z1), (x0, z1)]
    poly = rect if s > 0 else mirror_poly(rect)
    sx = lambda x: s * x  # noqa: E731
    zm = (z0 + z1) / 2
    # black module floor behind everything (the gap between reflector and lens holder reads as depth)
    CAB.quad_patch(f"proj_bowl_{tag}", "lamp_inner", "front", [(sx(x0), z0), (sx(x1), z0), (sx(x1), z1),
                                                             (sx(x0), z1)], off=-0.050, nu=4, nv=1)
    ribbon(f"proj_shroud_{tag}", poly, 0.007, "lamp_housing", off=-0.044, thick=0.026)
    cx, w, h = (x0 + x1) / 2, (x1 - x0), (z1 - z0)
    # B2.2 (lead: 'headlamp lenses read flat grey'): vacuum-metallised free-form reflector - a faceted chrome funnel
    # from the shroud's inner edge (-22 mm) down to the lens holder (-46 mm) in three rings with different
    # slopes, so each facet mirrors a different part of the sky/ground (the sparkle of a real LED lamp)
    reflector_funnel(f"proj_refl_{tag}" if beam == "low" else f"hb_refl_{tag}", s, cx, zm,
                     [(w - 0.015, h - 0.015, 0.003, -0.022), (w - 0.019, h - 0.021, 0.006, -0.031),
                      (w - 0.024, h - 0.024, 0.010, -0.039), (w - 0.022, h - 0.022, 0.012, -0.046)])
    # B2.1 (owner sheets: rectangular LED modules): every module carries a rectangular projector lens - a crowned
    # rounded-rectangle block of smoked polycarbonate (real thickness, two surfaces + wall, so it catches a
    # highlight on its crown and a lit edge at an angle) in a thin dark-chrome bezel. Low beam = the two inner
    # modules, high beam = the outer one (light groups by name: proj_lens_* / hb_lens_*).
    lw, lh = w - 0.026, h - 0.026
    rr = [(cx + px, zm + pz) for px, pz in rrect(lw, lh, 0.012, 3)]
    rr = rr if s > 0 else mirror_poly(rr)
    nm = "proj_lens" if beam == "low" else "hb_lens"
    # back face no deeper than the lamp back (-52 mm): check_fit found the interior dash behind a deeper block
    # strongly crowned (14 mm over a 44 mm block): the sky reflects only on the upper half, the lower half mirrors
    # the black lamp floor - reads as a lens with depth, not a flat grey pane under overcast light
    lens_dome(f"{nm}_{tag}", rr, "projector", crown=0.009, thick=0.012, rim_off=-0.040, sub=2)
    ribbon(f"proj_bezel_{tag}", rr, 0.0035, "reflector", off=-0.041, thick=0.005)   # B2.2: bright lens holder ring
    # LED emitter strip at the top edge of the high-beam module (reads as a different module, not a third copy)
    if beam != "low":
        CAB.quad_patch(f"hb_led_{tag}", "led_off", "front", [(sx(x0 + 0.012), z1 - 0.0085), (sx(x1 - 0.012), z1 - 0.0085),
                                                             (sx(x1 - 0.012), z1 - 0.0045), (sx(x0 + 0.012), z1 - 0.0045)],
                       off=-0.036, nu=6, nv=1, thick=0.002)


def headlamps():
    """2020s full-LED lamp (REVIEW r3 X1): slim housing, crowned clear outer lens with real thickness in a
    black gasket, black inner mask carrying the graphic - two low-beam reflector modules with slim
    projector lenses and one high-beam module (rectangular cells in dark-chrome frames, no round
    'eyeballs'), a thin amber LED indicator line along the bottom. The DRL light guides (T-bar along the top
    + road edge down the inner side, split at the corner and set back behind the lens) are half of the
    TRAKT mark per lamp: both lamps and the T-shaped grille frame read as the brand's road-T."""
    global CAB
    real = CAB
    CAB = lamp_loft()
    try:
        _headlamps_modern() if modern() else _headlamps()
    finally:
        CAB = real


def _headlamps_modern():
    """Slim full-LED unit: three reflector modules in a row under one light-guide line (DRL / position / switchback
    indicator) that runs the whole width and round the corner; crowned clear lens in a black gasket."""
    set_group("cab")
    for s in (-1, 1):
        poly = CFG["lamp"] if s > 0 else mirror_poly(CFG["lamp"])
        # r7b: housing back as a tray like the mask pockets (the clear lens showed the cab past the flat back plate)
        mask_tray(f"lamp_back_{s}", "lamp_inner", poly if s > 0 else [poly[2], poly[3], poly[0], poly[1]], nu=12, nv=3,
                  off=-LAMP_POCKET)
        # light signature = half of the road-T per lamp: a 24 mm bar along the top round the corner + a stem down
        # the inner (mask) side; both lamps and the black T mask read as the brand mark at distance
        drl_guide(f"drl_{s}_0", s, (0.895, 1.478), (1.352, 1.512), wdt=0.024, n=24)
        drl_guide(f"drl_{s}_1", s, (0.905, 1.462), (0.905, 1.338), wdt=0.020, n=6)
        for k, (x0, x1, beam) in enumerate(((0.936, 1.058, "low"), (1.070, 1.192, "low"), (1.204, 1.326, "high"))):
            lamp_cell(f"{s}_{k}", s, x0, x1, 1.348, 1.448, beam)
        CAB.quad_patch(f"indicator_{s}", "led_amber", "front",
                       [(s * 0.940, 1.3215), (s * 1.345, 1.2800), (s * 1.345, 1.2980), (s * 0.940, 1.3375)],
                       off=-0.030, nu=20, nv=1, thick=0.004)
        lens_dome(f"lamp_lens_{s}", poly, "lens_clear", crown=0.011, thick=0.006, sub=12)
        ribbon(f"lamp_gasket_{s}", poly, 0.007, "plastic_satin", off=-0.004, thick=0.006)


def _headlamps():
    set_group("cab")
    for s in (-1, 1):
        poly = CFG["lamp"] if s > 0 else mirror_poly(CFG["lamp"])
        CAB.poly_patch(f"lamp_back_{s}", "lamp_inner", "front", poly, off=-0.052, sub=6)
        for k, ((x0, z0), (x1, z1)) in enumerate(CFG["drl"]):
            drl_guide(f"drl_{s}_{k}", s, (x0, z0), (x1, z1), wdt=0.010)
        # module row: low, low, high (outboard cell wraps onto the corner)
        for k, (x0, x1, beam) in enumerate(((0.905, 1.000, "low"), (1.015, 1.110, "low"), (1.125, 1.225, "high"))):
            lamp_cell(f"{s}_{k}", s, x0, x1, 1.642, 1.712, beam)
        # outboard corner: dark-chrome fin with a vertical light-guide end of the DRL (lamp reads round the corner)
        CAB.quad_patch(f"lamp_fin_{s}", "lamp_housing", "front",
                       [(s * 1.245, 1.632), (s * 1.262, 1.632), (s * 1.275, 1.725), (s * 1.258, 1.725)]
                       if s > 0 else [(s * 1.262, 1.632), (s * 1.245, 1.632), (s * 1.258, 1.725),
                                      (s * 1.275, 1.725)], off=-0.040, nu=2, nv=2, thick=0.020)
        # B2.1 (owner sheets): indicator = amber LED diffuser strip behind the clear lens (amber also when off, as
        # in the sheets; light group IND_*), on a dark-chrome carrier, along the lamp floor round the corner
        CAB.quad_patch(f"indicator_{s}", "led_amber", "front",
                       [(s * 0.860, 1.607), (s * 1.285, 1.607), (s * 1.285, 1.625), (s * 0.860, 1.625)],
                       off=-0.030, nu=20, nv=1, thick=0.004)   # >= cage (0.02) behind the lens: bakes clean
        CAB.quad_patch(f"ind_carrier_{s}", "lamp_housing", "front",
                       [(s * 0.855, 1.602), (s * 1.290, 1.602), (s * 1.290, 1.630), (s * 0.855, 1.630)],
                       off=-0.040, nu=20, nv=1)
        # crowned clear outer lens (two Fresnel surfaces + rim) + black gasket round it
        # B2.1: crown 20 -> 11 mm: with the physical lens Fresnel (IOR 1.59) the steep 20 mm edge roll turned into a
        # mirror at 3/4 views and hid the DRL's vertical guide; 11 mm keeps a crisp highlight band on the crown
        lens_dome(f"lamp_lens_{s}", poly, "lens_clear", crown=0.011, thick=0.006, sub=12)
        ribbon(f"lamp_gasket_{s}", poly, 0.008, "plastic_satin", off=-0.004, thick=0.006)
        # B2.1 (owner sheets): small LED position / cornering lamp under the headlamp on the cab corner face - a
        # recessed black pocket with an LED bar and its own crowned lens in a gasket (light group MARKER_FRONT)
        pp = [(0.935, 1.395), (1.135, 1.395), (1.140, 1.437), (0.935, 1.437)]
        pp = pp if s > 0 else mirror_poly(pp)
        CAB.poly_patch(f"pos_back_{s}", "lamp_inner", "front", pp, off=-0.034, sub=3)
        CAB.quad_patch(f"pos_led_{s}", "led_off", "front", [(s * 0.955, 1.411), (s * 1.120, 1.411), (s * 1.122, 1.421),
                                                            (s * 0.955, 1.421)] if s > 0 else
                       [(s * 1.120, 1.411), (s * 0.955, 1.411), (s * 0.955, 1.421), (s * 1.122, 1.421)],
                       off=-0.026, nu=8, nv=1, thick=0.003)
        lens_dome(f"pos_lens_{s}", pp, "lens_clear", crown=0.006, thick=0.004, sub=4)
        ribbon(f"pos_gasket_{s}", pp, 0.005, "plastic_satin", off=-0.003, thick=0.004)


# ---------------------------------------------------------------- corner deflectors, roof, rear wall
def sun_visor():
    """B2: black sun visor over the windscreen (2020s header instead of the r4 roof 'bubble'): a thin blade
    standing 85 mm off the header plane, tilted down, ending 30 mm above the glass; follows the plan wrap."""
    set_group("cab")
    z_root, hw, n = WS_Z1 + 0.045, 1.12, 24
    # section (z, offset from the shell): root on the header, blade sloping down to a 6 mm rounded nose
    prof = [(z_root + 0.030, -0.004), (z_root + 0.026, 0.040), (z_root + 0.010, 0.086), (z_root + 0.002, 0.090),
            (z_root - 0.006, 0.084), (z_root - 0.012, 0.040), (z_root - 0.018, -0.004)]
    if modern():   # soft bulged visor: deeper rounded section, wraps the R 0.34 corners with the glass
        hw, n = 1.27, 48
        prof = [(z_root + 0.075, -0.004), (z_root + 0.070, 0.026), (z_root + 0.052, 0.063), (z_root + 0.028, 0.087),
                (z_root + 0.006, 0.094), (z_root - 0.010, 0.088), (z_root - 0.020, 0.045), (z_root - 0.026, -0.004)]
    bm = bmesh.new()
    rows = [[bm.verts.new(CAB.front_pt(z, -hw + 2 * hw * j / n, o)) for j in range(n + 1)] for z, o in prof]
    for a in range(len(rows)):
        r0, r1 = rows[a], rows[(a + 1) % len(rows)]
        for j in range(n):
            bm.faces.new((r0[j], r0[j + 1], r1[j + 1], r1[j]))
    for j in (0, n):
        bm.faces.new([r[j] for r in rows])
    G.obj_from_bm("sun_visor", bm, "plastic", sharp=40)


def corners_roof_rear():
    set_group("cab")
    sun_visor()
    # B2 v2 (owner sheets): row of five roof-front marker lamps over the header
    # B2.1: each lamp = moulded black base on the header (rubber gasket line), a recessed LED bar and a crowned
    # clear lens with real thickness standing 22 mm proud; tilted with the 7 deg front plane
    rot = Matrix.Rotation(math.radians(RAKE), 3, "X")
    for i, xm in enumerate((-0.84, 0.84) if modern() else (-0.80, -0.40, 0.0, 0.40, 0.80)):
        p = V(CAB.front_pt(ROOF_Z - (ROUND["marker_dz"] if rounded() else 0.16), xm, 0.0))
        box(f"marker_front_base_{i}", p + rot @ V((0, 0.004, 0)), (0.124, 0.012, 0.050), "plastic_satin", bev=0.005,
            seg=3, rot=rot)
        box(f"marker_front_gasket_{i}", p + rot @ V((0, 0.0005, 0)), (0.128, 0.004, 0.054), "rubber", bev=0.002, rot=rot)
        box(f"marker_front_led_{i}", p + rot @ V((0, 0.0115, 0)), (0.084, 0.004, 0.012), "led_off", rot=rot)
        box(f"marker_front_{i}", p + rot @ V((0, 0.021, 0)), (0.104, 0.010, 0.034), "lens_clear", bev=0.0045, seg=3,
            rot=rot)
    for s in (-1, 1):
        box(f"marker_rear_{s}", (s * (CAB_HALF_W - 0.24), CAB_BACK_Y - 0.012, ROOF_Z - 0.17), (0.12, 0.025, 0.045),
            "lens_red", bev=0.006)
        # side extenders (aero flaps behind the cab), plastic with a rubber trailing edge
        xo = s * (CAB_HALF_W - 0.015)
        prof = [(CAB_BACK_Y + 0.10, 1.55), (CAB_BACK_Y - 0.30, 1.62), (CAB_BACK_Y - 0.34, 3.30),
                (CAB_BACK_Y + 0.05, 3.42)]
        extrude_poly(f"side_extender_{s}", prof, 0.016, "paint", plane="YZ", origin=(xo - s * 0.016, 0, 0),
                     bev=0.004)
        rub = [(CAB_BACK_Y - 0.30, 1.62), (CAB_BACK_Y - 0.38, 1.625), (CAB_BACK_Y - 0.42, 3.29),
               (CAB_BACK_Y - 0.34, 3.30)]
        extrude_poly(f"extender_flap_{s}", rub, 0.008, "rubber", plane="YZ", origin=(xo - s * 0.012, 0, 0))
        for z in (1.9, 2.6, 3.25):
            box(f"extender_hinge_{s}_{z}", (xo - s * 0.03, CAB_BACK_Y - 0.02, z), (0.03, 0.06, 0.05), "plastic_satin")
    if modern():   # rear roof spoiler (body colour): bridges the 3.75 m roof towards the 4.00 m trailer, top 3.90 m
        y0, y1, hw = -0.58, CAB_BACK_Y - 0.07, 1.10
        top = [(y0 + (y1 - y0) * t, ROOF_Z - 0.012 + 0.122 * math.sin(math.pi / 2 * min(1.0, t * 1.2)))
               for t in (0, 0.1, 0.2, 0.32, 0.45, 0.6, 0.8, 1)]
        prof = top + [(y1 + 0.045, ROOF_Z - 0.10), (y0, ROOF_Z - 0.10)]
        extrude_poly("roof_lip_spoiler", prof, 2 * hw, "paint", plane="YZ", origin=(-hw, 0, 0), bev=0.018, bseg=3)
    # roof: rear spoiler lip, roof hatch, antenna base
    box_mm("roof_lip", -1.10, 1.10, CAB_BACK_Y - 0.06, CAB_BACK_Y + 0.08, ROOF_Z - 0.035, ROOF_Z - 0.005,
           "plastic", bev=0.01)
    box_mm("roof_hatch", -0.36, 0.36, -0.55, 0.05, ROOF_Z - 0.02, ROOF_Z + 0.015, "plastic", bev=0.012, seg=3)
    box_mm("roof_hatch_glass", -0.30, 0.30, -0.49, -0.01, ROOF_Z + 0.012, ROOF_Z + 0.019, "frit")
    box_mm("antenna_base", 0.62, 0.70, -0.70, -0.55, ROOF_Z - 0.03, ROOF_Z + 0.03, "plastic_satin", bev=0.012)
    # rear wall: panel joints, work lamp, coupling panel
    y = CAB_BACK_Y - 0.002
    for x in (-0.62, 0.62):
        box_mm(f"rear_joint_{x}", x - 0.003, x + 0.003, y - 0.002, y, CAB_Z0 + 0.05, ROOF_Z - 0.40, "gap")
    box_mm("rear_joint_h", -1.05, 1.05, y - 0.002, y, 2.30, 2.306, "gap")
    box_mm("work_lamp", -0.18, 0.18, y - 0.05, y, ROOF_Z - 0.25, ROOF_Z - 0.19, "plastic_satin", bev=0.01)
    box_mm("work_lamp_lens", -0.16, 0.16, y - 0.052, y - 0.049, ROOF_Z - 0.24, ROOF_Z - 0.20, "led_off")
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


HOUSE_W = 0.222      # modern class II + IV head width, WORKING_VALUE (glass 0.198 m wide)
# class VI front mirror (modern): the central ray from the eye point reflects to the middle of the ground field in
# front of the cab. UN ECE R46 class VI field as remembered, regulation text NOT opened -> UNVERIFIED: ground strip
# from the vehicle front plane to 2.0 m ahead, from the driver-side plane to 2.0 m outboard of the passenger side.
# r6: 2.99 -> 2.89 m: from the eye point the folded-down passenger sun visor covered the upper half of the head
FRONT_Z = 2.89               # head centre height, WORKING_VALUE (in front of the top of the windscreen)
KERB_C = (1.22, 1.42, 2.20)  # class V head centre, WORKING_VALUE (0.15 m off the passenger corner; below 2.15 m the dash hides it)
FRONT_FIELD_AHEAD = 1.0      # m ahead of the bumper face (strip middle)
FRONT_FIELD_X = 0.75         # m towards the passenger side (strip middle is ~+1.0; pulled in to keep the bumper edge)


def mirrors(kind="classic", front=True):
    set_group("mirrors" if kind == "classic" else "mirrors_cam")
    for s in (-1, 1):
        base = V(CAB.side_pt(2.90, win_front(2.90) + 0.02, s, 0.0))
        if kind == "classic" and modern():
            # one tall aero housing (class II + IV glasses) on two short faired blades; body-colour back
            xh, yh = s * 1.50, base.y - 0.10
            rot = mirror_aim(V((xh, yh, 2.60)), (s * 0.06, -1.0, -0.02))
            c = V((xh, yh, 2.47))
            # r4: slimmer head (0.25 x 0.15 -> HOUSE_W x ~0.115 m deep): seen from the eye point it must not hide
            # more than the two B2 heads did (11.5 deg); measured with pillar_obstruction.py
            box(f"mirror_main_house_{s}", c, (HOUSE_W, 0.080, 0.76), "mirror_plastic", bev=0.038, seg=4, rot=rot)
            # r6 E7: the back shell is dark grained plastic, not body colour (a white back read as a blank card)
            box(f"mirror_main_cap_{s}", c + rot @ V((0, 0.030, 0)), (HOUSE_W - 0.008, 0.085, 0.745), "plastic",
                bev=0.040, seg=5, rot=rot)
            if s > 0:
                # class V kerb mirror. r6: the old head hung under the housing at z 1.98 m, below the belt line: its
                # image was right but the line of sight from the eye point ended in the passenger door. Now it stands
                # on a short stalk at the passenger corner just above the windscreen's lower edge, seen through the
                # wrapped corner of the screen, and looks back and down along the cab side (mirror_visibility.py)
                ck = V(KERB_C)
                rk = mirror_aim(ck, V((CAB_HALF_W + 1.05, EYE.y - 0.25, 0.0)) - ck)
                foot = V(CAB.front_pt(WS_Z0 - 0.045, 1.215, 0.0))
                hb = ck + rk @ V((0, 0.030, -0.030))
                out = V((ck.x - foot.x, ck.y - foot.y, 0.0)).normalized()
                tube("mirror_kerb_arm", [foot - out * 0.01, foot + out * 0.05 + V((0, 0, 0.02)), hb + V((0, 0, -0.03)),
                                         hb], 0.011, "mirror_plastic", seg=8)
                box("mirror_kerb", ck, (0.20, 0.08, 0.14), "mirror_plastic", bev=0.03, seg=3, rot=rk)
                box("mirror_kerb_glass", ck + rk @ V((0, -0.041, 0)), (0.18, 0.006, 0.12), "mirror", bev=0.003,
                    rot=rk)
            box(f"mirror_main_glass_{s}", c + rot @ V((0, -0.041, 0.13)), (HOUSE_W - 0.024, 0.006, 0.44), "mirror",
                bev=0.004, rot=rot)
            box(f"mirror_wide_glass_{s}", c + rot @ V((0, -0.041, -0.24)), (HOUSE_W - 0.024, 0.006, 0.20), "mirror",
                bev=0.004, rot=rot)
            for nm, zb, zh in (("top", 2.84, 2.74), ("bot", 2.26, 2.20)):
                p0 = V(CAB.side_pt(zb, win_front(zb) + 0.012, s, -0.012))
                p1 = V((xh - s * 0.08, yh + 0.012, zh))
                d = p1 - p0
                box(f"mirror_arm_{nm}_{s}", (p0 + p1) / 2, (d.length, 0.040, 0.070), "mirror_plastic", bev=0.018, seg=2,
                    rot=d.to_track_quat("X", "Z").to_matrix())
        elif kind == "classic":
            xh = s * 1.50
            yh = base.y - 0.10
            # arm: upper beam + lower strut, satin black
            tube(f"mirror_arm_{s}", [base + V((s * 0.0, 0, 0.03)), V((s * 1.33, yh + 0.02, 2.99)),
                                     V((xh, yh, 2.94))], 0.015, "mirror_plastic", seg=10)
            tube(f"mirror_strut_{s}", [V(CAB.side_pt(2.25, win_front(2.25) - 0.02, s, 0.0)),
                                       V((xh - s * 0.02, yh, 2.08))], 0.014, "mirror_plastic", seg=10)
            # class II main + class IV wide-angle heads; body-colour back caps. R2 #7: each glass is aimed so
            # that the eye point sees the field it must show (glass normal = bisector of the direction to the
            # eye and the required view direction), not left facing straight back (edge-on from the seat)
            for nm, zc, hgt, view in (("main", 2.60, 0.42, (s * 0.06, -1.0, -0.02)),
                                      ("wide", 2.20, 0.20, (s * 0.40, -1.0, -0.22))):
                c = V((xh, yh, zc))
                rot = mirror_aim(c, view)
                if rounded():   # aero housing: fully rounded rim (R 42 mm) and a deeper, domed body-colour back
                    box(f"mirror_{nm}_{s}", c, (0.24, 0.085, hgt), "mirror_plastic", bev=0.042, seg=7, rot=rot)
                    box(f"mirror_{nm}_cap_{s}", c + rot @ V((0, 0.035, 0)), (0.232, 0.10, hgt - 0.012), "paint",
                        bev=0.049, seg=8, rot=rot)
                else:
                    box(f"mirror_{nm}_{s}", c, (0.24, 0.085, hgt), "mirror_plastic", bev=0.03, seg=4, rot=rot)
                    box(f"mirror_{nm}_cap_{s}", c + rot @ V((0, 0.02, 0)), (0.235, 0.06, hgt - 0.01), "paint",
                        bev=0.03, seg=4, rot=rot)
                box(f"mirror_{nm}_glass_{s}", c + rot @ V((0, -0.044, 0)), (0.215, 0.006, hgt - 0.03), "mirror",
                    bev=0.004, rot=rot)
            if s > 0:  # class V kerb mirror on the passenger side, under the main mirrors, looking down
                c = V((s * 1.42, yh + 0.04, 1.98))
                rot = mirror_aim(c, (0.25, -0.35, -1.0))
                box("mirror_kerb", c, (0.20, 0.08, 0.14), "mirror_plastic", bev=0.03, seg=3, rot=rot)
                box("mirror_kerb_glass", c + rot @ V((0, -0.041, 0)), (0.18, 0.006, 0.12), "mirror", bev=0.003,
                    rot=rot)
        else:
            # camera monitor system: short aero arm with a camera pod (class II/IV)
            yh = base.y - 0.05
            tube(f"cam_arm_{s}", [base + V((0, 0, 0.04)), V((s * 1.36, yh, 2.98)), V((s * 1.44, yh - 0.03, 2.96))],
                 0.022, "mirror_plastic", seg=10)
            sphere(f"cam_pod_{s}", (s * 1.46, yh - 0.06, 2.95), 0.05, "mirror_plastic", scale=(1.1, 2.2, 1.0))
            cyl(f"cam_lens_{s}", (s * 1.46, yh - 0.165, 2.95), 0.016, 0.008, "glass_tint", axis="Y", seg=16)
            if s > 0:
                sphere("cam_pod_kerb", (s * 1.36, yh - 0.03, 2.86), 0.035, "mirror_plastic", scale=(1, 1.6, 1))
    # class VI front mirror over the passenger-side corner (kept with camera mirrors too)
    if not front:
        return
    set_group("mirrors")
    p = V(CAB.front_pt(WS_Z1 + 0.29, 0.98, 0.0))     # above the sun visor
    if modern():
        # r4: the head hangs in front of the top of the windscreen below the visor nose (the old one sat above the
        # visor: hidden from the seat by the header, and its glass was tilted at the sky)
        c = V((0.98, face_y(FRONT_Z) + 0.235, FRONT_Z))
        tgt = V((FRONT_FIELD_X, face_y(0.6) + FRONT_FIELD_AHEAD, 0.0))
        rot = mirror_aim(c, tgt - c)
        hb = c + rot @ V((0, 0.030, 0.045))
        tube("front_mirror_arm", [p + V((0, -0.05, 0.10)), p + V((0, 0.13, 0.10)), V((p.x, hb.y + 0.01, p.z + 0.02)),
                                  hb + V((0, 0.01, 0.10)), hb], 0.013, "mirror_plastic", seg=10)
        box("front_mirror", c, (0.26, 0.07, 0.17), "mirror_plastic", bev=0.03, seg=3, rot=rot)
        box("front_mirror_glass", c + rot @ V((0, -0.0355, 0)), (0.24, 0.006, 0.15), "mirror", bev=0.003, rot=rot)
        return
    tube("front_mirror_arm", [p + V((0, -0.05, 0.10)), p + V((0, 0.12, 0.10)), p + V((0, 0.20, 0.0))], 0.014,
         "mirror_plastic", seg=10)
    box("front_mirror", p + V((0, 0.22, -0.10)), (0.26, 0.07, 0.17), "mirror_plastic", bev=0.03, seg=3,
        rot=Matrix.Rotation(math.radians(-35), 3, "X"))
    box("front_mirror_glass", p + V((0, 0.20, -0.135)), (0.24, 0.006, 0.15), "mirror", bev=0.003,
        rot=Matrix.Rotation(math.radians(-35), 3, "X"))


# ---------------------------------------------------------------- frame-mounted lower fairing (bumper + step boxes)
def lower_fairing():
    """One loft (bumper + side step boxes) minus centre, wheel arches, step recesses and pockets."""
    global LOW
    set_group("lower")
    sp = CFG["bumper_split"]
    # B2/owner: the bumper face continues the cab's front plane (one line in side view), tucking under at the lip
    fr = [(0.38, 1.530), (0.55, face_y(0.55)), (FAIR_TOP, face_y(FAIR_TOP) + 0.002)]
    if modern():   # one rounded volume: the chin rolls under in an R ~0.15 m curve instead of a straight chamfer
        fr = [(0.38, face_y(0.55) - 0.085), (0.41, face_y(0.55) - 0.048), (0.45, face_y(0.55) - 0.022),
              (0.50, face_y(0.50) - 0.007), (0.56, face_y(0.56)), (FAIR_TOP, face_y(FAIR_TOP) + 0.002)]
    ihw, iz0, iz1 = (0.66, 0.48, 0.61) if modern() else (0.80, 0.45, 0.62)     # lower intake
    LOW = Loft(front=fr, back=FAIR_BACK,
               w=[(0.38, CAB_HALF_W - 0.02), (0.55, CAB_HALF_W), (sp, CAB_HALF_W), (FAIR_TOP, CAB_HALF_W)],
               rf=ROUND["low_rf"] if rounded() else [(0.38, 0.22), (FAIR_TOP, 0.17)], rb=0.05, z0=0.38,
               ztop=FAIR_TOP, roof_r=0.015, arc_n=(18 if modern() else 24) if rounded() else 14, step=0.04, flat_n=8, roof_n=3,
               crown=ROUND["crown"] if rounded() else 0.0, front_n=12 if rounded() else None)
    lo = LOW.build("lower_fairing", "plastic", sharp=45)
    lo.data.materials.append(G.mat("paint"))
    cuts = [G.box_mm("cut_centre", -0.94, 0.94, FAIR_BACK - 0.2, 1.17, 0.2, 1.4, "gap")]
    for s in (-1, 1):
        c = cyl(f"cut_arch_{s}", (s * 1.10, 0.0, WHEEL_Z), ARCH_R, 0.6, "plastic", axis="X", seg=48)
        cuts.append(c)
        # step well behind the wheel: three open recesses. B2 (REVIEW r3 X3 'white cabinet'): rounded moulded
        # recesses (R 45 mm cutter) lined in dark textured plastic like real step inserts; the body colour stays on
        # the outer faces of the step boxes only (R2 #3: no black plinth)
        xo, xi = s * (CAB_HALF_W + 0.1), s * (CAB_HALF_W - STEP_DEPTH)
        for k, (z, y0, y1) in enumerate(STEPS):
            cuts.append(box_mm(f"cut_step{k}_{s}", min(xo, xi), max(xo, xi), y0, y1, z,
                               z + (0.30 if k == 2 else 0.24), "plastic", bev=0.07 if rounded() else 0.045,
                               seg=5 if rounded() else 3))
    # bumper pockets: lower intake, the T 'road' continued in the bumper, fog lamps, two cleaning steps
    cuts.append(LOW.patch("cut_intake", "grille_honey_coarse", "front", iz0, iz1, -ihw, ihw, off=-0.06,
                          thick=0.15, nz=2, npar=24))
    cuts.append(LOW.quad_patch("cut_road", "trim_graphite", "front", CFG["bumper_road"], off=-0.034, thick=0.15,
                               nu=16, nv=3))
    for s in (-1, 1):
        if modern():   # slim fog / cornering LED slot in line with the lower intake, wrapping the bumper corner
            cuts.append(LOW.patch(f"cut_bstep_{s}", "plastic", "front", 1.055, 1.115, s * 0.875, s * 1.30, off=-0.10,
                                  thick=0.2, nz=1, npar=16))      # integrated cleaning step under the lamp
            cuts.append(LOW.patch(f"cut_fog_{s}", "lamp_inner", "front", iz0 + 0.02, iz1 - 0.02, s * 0.80, s * 1.22,
                                  off=-0.05, thick=0.12, nz=2, npar=16))
            continue
        # B2.1 (owner sheets): compact LED fog / cornering module in each bumper corner (was a 0.40 m slot)
        cuts.append(LOW.patch(f"cut_fog_{s}", "lamp_inner", "front", 0.695, 0.785, s * 0.96, s * 1.17, off=-0.05,
                              thick=0.12, nz=2, npar=8))
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
        if c.y < -0.40 and abs(c.x) < CAB_HALF_W - 0.03 and c.z < FAIR_TOP - 0.01:
            continue          # inside a step well (back wall, floors): dark moulded insert
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
        if rounded():   # body-colour flare, 20 mm proud (2.54 m over the flares, inside 2.55 m) with an R 14 mm soft lip (was a square-edged black band)
            fl = arch(f"arch_flare_{s}", 0.0, WHEEL_Z, ARCH_R - 0.004, ARCH_OUT + 0.02, s * (CAB_HALF_W - 0.03),
                      s * (CAB_HALF_W + 0.020), -12, 192, "paint", n=40 if modern() else 56)
            G.apply_mods(bevel(fl, 0.014, seg=2 if modern() else 4, angle=50))
        else:
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
            # r4 (REVIEW r3 X3): perforated anti-slip treads (mud falls through), not flat checker plate
            box_mm(f"step_tread{k}_{s}", min(xo, xi), max(xo, xi), y0 + 0.004, y1 - 0.004, z, z + 0.014, "perforated",
                   bev=0.003)
            box_mm(f"step_nose{k}_{s}", xo - s * 0.025, xo, y0 + 0.004, y1 - 0.004, z - 0.02, z + 0.016,
                   "plastic_satin", bev=0.004)
        # B2.1 (owner sheets): amber side marker / repeater on the front wheel-arch flare, ahead of the wheel top,
        # set tangentially on the flare's outer face (light group IND_*)
        a = math.radians(62.0)
        rm = (ARCH_R + ARCH_OUT) / 2
        p = V((s * (CAB_HALF_W + 0.011), rm * math.cos(a), WHEEL_Z + rm * math.sin(a)))
        rot = Matrix.Rotation(-(math.pi / 2 - a), 3, "X")
        box(f"side_repeater_base_{s}", p - V((s * 0.003, 0, 0)), (0.006, 0.070, 0.026), "plastic_satin", bev=0.002,
            rot=rot)
        box(f"side_repeater_{s}", p + V((s * 0.002, 0, 0)), (0.006, 0.062, 0.020), "lens_amber", bev=0.003, rot=rot)
        if modern():
            LOW.patch(f"bstep_tread_{s}", "plastic_satin", "front", 1.057, 1.066, s * 0.88, s * 1.295, off=-0.095, thick=0.09,
                      nz=1, npar=16)
            a0, a1, e = s * 0.805, s * 1.215, s * 0.012
            LOW.patch(f"fog_lens_{s}", "lens_clear", "front", iz0 + 0.024, iz1 - 0.024, a0, a1, off=0.0, nz=2, npar=16)
            LOW.patch(f"fog_back_{s}", "lamp_inner", "front", iz0 + 0.02, iz1 - 0.02, a0, a1, off=-0.045, nz=1, npar=16)
            LOW.patch(f"fog_bowl_{s}", "dark_chrome", "front", iz0 + 0.03, iz1 - 0.03, a0 + e, a1 - e, off=-0.038,
                      nz=1, npar=16, thick=0.006)
            LOW.patch(f"fog_led_{s}_0", "led_off", "front", iz0 + 0.046, iz1 - 0.046, a0 + 2 * e, a1 - 2 * e, off=-0.031,
                      nz=1, npar=16, thick=0.006)
            continue
        # fog / cornering module: clear lens over two square LED cells in a dark-chrome carrier
        LOW.patch(f"fog_lens_{s}", "lens_clear", "front", 0.700, 0.780, s * 0.965, s * 1.165, off=0.0, nz=2, npar=8)
        LOW.patch(f"fog_back_{s}", "lamp_inner", "front", 0.695, 0.785, s * 0.96, s * 1.17, off=-0.045, nz=1, npar=8)
        LOW.patch(f"fog_bowl_{s}", "dark_chrome", "front", 0.708, 0.772, s * 0.975, s * 1.155, off=-0.038, nz=1,
                  npar=8, thick=0.006)
        for k, (u0, u1) in enumerate(((0.990, 1.060), (1.075, 1.145))):
            LOW.patch(f"fog_led_{s}_{k}", "led_off", "front", 0.716, 0.764, s * u0, s * u1, off=-0.031, nz=1, npar=3,
                      thick=0.006)
        # cleaning steps in the bumper (folding treads) + tow pin cover outline
        LOW.patch(f"bstep_tread_{s}", "checker", "front", 1.003, 1.012, s * 0.925, s * 1.115, off=-0.115,
                  thick=0.11, nz=1, npar=4)
    LOW.patch("bumper_split", "gap", "front", sp - 0.004, sp + 0.004, -1.6, 1.6, off=0.001, nz=1, npar=60)
    # number plate (PL/EU 520 x 114 mm) on a dark holder
    LOW.patch("plate_holder", "plastic", "front", 0.765, 0.905, -0.275, 0.275, off=0.001, thick=0.008, nz=2, npar=8)
    G.plate_uv(LOW.patch("plate", "plate", "front", 0.778, 0.892, -0.26, 0.26, off=0.0105, nz=1, npar=4), 1)
    if not modern():
        LOW.patch("tow_cover", "gap", "front", 1.02, 1.025, -0.12, 0.12, off=0.001, nz=1, npar=2)
        LOW.patch("tow_cover_b", "gap", "front", 0.93, 0.935, -0.12, 0.12, off=0.001, nz=1, npar=2)
        for s in (-1, 1):
            LOW.patch(f"tow_cover_s{s}", "gap", "front", 0.93, 1.025, s * 0.12 - 0.0025, s * 0.12 + 0.0025, off=0.001,
                      nz=1, npar=1)
    # bumper 'road' (the grille's T stem continued): coarse honeycomb in a graphite frame, no slats
    LOW.quad_patch("road_back", "grille_honey_coarse", "front", CFG["bumper_road"], off=-0.029, nu=16, nv=3)
    if modern():   # the mask's stem continues in the bumper: same louvre rhythm, then one gloss panel for the plate
        rd = CFG["bumper_road"]
        hwz = lambda z: rd[1][0] + (rd[2][0] - rd[1][0]) * (z - rd[1][1]) / (rd[2][1] - rd[1][1]) - 0.006  # noqa: E731
        _, pitch, _, hgt = CFG["louvres"]
        for k in range(3):
            zc = 1.152 - pitch * k
            grille_bar(f"grille_bar_b{k}", zc, hgt, 0.026, hwz(zc), "mask_gloss", nose=-0.004, loft=LOW,
                       tilt=LOUVRE_TILT)
            lane_dash(f"lane_dash_b{k}", LOW, zc, hgt - 0.016, louvre_mid(hgt) + 0.0015, tilt=LOUVRE_TILT)
        grille_bar("grille_bar_plate", 0.835, 0.235, 0.026, hwz(0.835), "mask_gloss", nose=-0.004, nose_r=0.020,
                   loft=LOW)
    else:
        ribbon("road_frame", CFG["bumper_road"], 0.022, "trim_graphite", off=-0.004, thick=0.008, loft=LOW)
    # lower intake: coarse honeycomb (different texture and scale from the grille), horns visible behind it
    LOW.patch("intake_mesh", "grille_honey_coarse", "front", iz0, iz1, -ihw, ihw, off=-0.052, nz=1, npar=16)
    for s in (-1, 1):
        cyl(f"horn_{s}", (s * 0.45, face_y(0.53) - 0.10, 0.53), 0.055, 0.04, "plastic_satin", axis="Y", seg=24)
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
            "skirt": None,
            "skirt_note": "B2.1: removed - the door ends at bottom_edge_z_m, the steps are open below it",
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
    bpy.data.objects.new("ip_wheel_path", None)
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



set_shape(DEFAULT_SHAPE)
