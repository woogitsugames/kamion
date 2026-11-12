"""Track A5 — brand-neutral cab interior of the fictional EU long-haul tractor (high roof, flat floor, LHD).

Run headless (Blender 4.2 LTS), textures first (once):
    uv run --no-project --with pillow --with numpy python tools/blender/truck/interior/make_textures.py
    blender -b --factory-startup --python tools/blender/truck/interior/build_interior.py -- \
        --out docs/reports/visual/truck-A5 [--cams all] [--light overcast,lowsun] [--trim koniak] \
        [--badge trakt|none|bielik|narew] [--rake 19] [--samples 384] [--blend path.blend]

Everything is generated here: no hand-edited .blend. Frame = A2 blockout frame (dims.json):
1 unit = 1 m, Z up, truck faces +Y, driver side (LHD) = -X, origin = ground under front axle centre.
Ergonomic values are WORKING_VALUE unless marked; table with sources: docs/reports/visual/truck-A5/README.md.
Owner decisions 2026-11-09: concept B + TRAKT (--rake 19, --badge trakt), trim koniak, digital-only cluster. The other
values stay as switches (--trim, --badge, --rake: A/C ~3-5 deg); everything else is the shared cab shell.
Rake = windscreen lean BACK from vertical (top edge further rearward, -Y), as in exterior/body.py.
"""
import argparse
import json
import math
import os
import re
import sys
import time

import bmesh
import bpy
from mathutils import Matrix, Vector, geometry

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import geom as G  # noqa: E402
import materials as M  # noqa: E402
import backdrop as BD  # noqa: E402
from geom import (V, bevel, box, box_mm, cyl, loft, panel, plane_uv, quad_on, rod, rrect, solidify,  # noqa: E402
                  strip, tube)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
DIMS = json.load(open(os.path.join(REPO, "art-source", "truck", "dims.json"), encoding="utf-8"))
M.TEX = os.path.join(REPO, "art-source", "truck", "interior", "textures")


def D(k):
    return DIMS["values"][k]["value"]


# ---------------------------------------------------------------- key dimensions (WORKING_VALUE unless noted)
EYE = Vector(D("driver_eye_point_m"))          # (-0.55, 0.45, 2.50) from dims.json
HPT = EYE - Vector((0, 0, 0.635))              # R/H-point: UNECE R46 ocular points 635 mm above R (SOURCED)
FLOOR = D("cab_interior_floor_m")              # 1.40 flat floor
HALF_OUT = D("cab_width_m") / 2                # 1.245 outer skin
XI = HALF_OUT - 0.08                           # 1.165 inner trim surface (80 mm wall: skin+insulation+trim)
YB = D("cab_back_behind_front_axle_m") * -1 + 0.07  # -0.88 inner back wall
ROOF_OUT = D("overall_height_m")               # 3.75 (B2 v2)
CEIL = 3.62                                    # headliner centre: 2.22 m standing height over flat floor
CEIL_SIDE = 3.36                               # headliner meets side wall
WS_Z0, WS_Z1 = 2.07, 3.02                      # windscreen visible glass bottom/top (inner)
WS_Y0 = 1.345                                  # windscreen inner surface at bottom edge
FRONT_WALL_Y = 1.43                            # footwell front wall
SEAT_X = HPT.x                                 # -0.55 driver seat centreline
WHEEL_C = Vector((SEAT_X, 0.875, 2.12))        # steering-wheel centre
BRAKE_PIVOT = Vector((SEAT_X + 0.07, 1.27, 1.86))    # pendant brake arm pivot (= export pivot PEDAL_Brake); r7b: y 1.33
ACCEL_HINGE = Vector((SEAT_X + 0.235, 1.095, 1.42))  # organ pedal floor hinge (= export pivot PEDAL_Accel); r7b: y 1.16
WHEEL_TILT = 38.0                              # rim plane vs horizontal (deg)
WHEEL_R = 0.235                                # rim centre line 470 mm, 499 mm over the leather (WORKING_VALUE, class 450-500 mm)
RIM_R = (0.0175, 0.0145)                       # rim section half-axes: 35 x 29 mm
TRIMS = {  # insert colour (linear albedo) — the only interior colour that changes with the brand
    "grafit": (0.050, 0.050, 0.053),
    "piasek": (0.205, 0.175, 0.135),
    "koniak": (0.150, 0.068, 0.032),
    "lupek": (0.060, 0.074, 0.090),
}
RAKE = 19.0                                    # concept B (TRAKT), same as exterior/body.py RAKE


def ws_y(z):
    """Windscreen inner surface y at height z. A6 r3 fix: the screen leans back (y decreases upwards); before r3 the
    sign was inverted, so '--rake 19' leaned the glass forward."""
    return WS_Y0 - (z - WS_Z0) * math.tan(math.radians(RAKE))


# ---------------------------------------------------------------- door / shell interface with the exterior (A3/A4)
# The exterior generator (tools/blender/truck/exterior/body.py, round 3) owns the door opening, the side glass and the
# shell lower edge and publishes them in art-source/truck/exterior/door_interface.json (REVIEW-2026-11-09-r2 top-12 #2:
# door opening ~0.3 m rearward, fixed body-colour corner panel ahead of it). The interior reads that file; without it
# (old checkouts) it falls back to the A6 values, which matched the r2 exterior.
DOOR_IF_PATH = os.path.join(REPO, "art-source", "truck", "exterior", "door_interface.json")
DOOR_IF_A6 = {"door_y0": -0.24, "door_front_yz": [(1.13, 1.0), (1.13, 3.2)], "side_glass_z": (2.17, 2.96),
              "side_glass_front_yz": None, "shell_bottom_z": 1.225, "source": "A6 fallback (r2 exterior)"}


def load_door_interface():
    """-> door_y0 (aperture rear edge), door_front_yz (aperture front edge polyline (y, z), = exterior front shut line
    moved inboard by the seal overlap), side_glass_z, side_glass_front_yz, shell_bottom_z (door/shell lower edge)."""
    d = dict(DOOR_IF_A6)
    if not os.path.exists(DOOR_IF_PATH):
        print("door interface: no file, using A6 values")
        return d
    src = json.load(open(DOOR_IF_PATH, encoding="utf-8"))
    door, ap, gl = src["door"], src["aperture_for_interior"], src["side_glass"]
    ov = door.get("seal_overlap_m", 0.04)
    d["door_y0"] = ap["DOOR_Y0_rear_m"]
    d["door_front_yz"] = sorted(((y - ov, z) for y, z in door["front_shut_line_yz_m"]), key=lambda t: t[1])
    d["side_glass_z"] = (gl["belt_z_m"], gl["top_z_m"])
    d["side_glass_front_yz"] = sorted((tuple(p) for p in gl["front_edge_yz_m"]), key=lambda t: t[1])
    d["shell_bottom_z"] = door["bottom_edge_z_m"]
    d["source"] = os.path.relpath(DOOR_IF_PATH, REPO).replace("\\", "/")
    print("door interface:", d)
    return d


DOOR_IF = load_door_interface()


# ---------------------------------------------------------------- windscreen interface with the exterior (A6)
# The exterior export (tools/blender/truck/exterior/a6_export.py) owns the single windscreen and publishes its inner
# face in art-source/truck/exterior/glass_interface.json. The interior fits its trims, dash top and frit print to it;
# its own CAB_Glass_Windows is only a placeholder for interior-only renders (hidden in the game with the exterior).
GLASS_IF_PATH = os.path.join(REPO, "art-source", "truck", "exterior", "glass_interface.json")


def load_glass_interface():
    if not os.path.exists(GLASS_IF_PATH):
        print("glass interface: no file, using A6 r3 interior values")
        return None
    w = json.load(open(GLASS_IF_PATH, encoding="utf-8"))["windscreen"]
    g = w.get("inner_face_grid_a2_13x49")
    if not g:
        return None
    src = json.load(open(GLASS_IF_PATH, encoding="utf-8"))
    rows = [sorted(((p[0], p[1]) for p in r), key=lambda t: t[0]) for r in g["points"]]
    zs = [r[len(r) // 2][2] for r in g["points"]]
    fr = w["frit_on_exterior_glass_m"].get("inside_visible_opening_m", {})
    sh = src.get("shell_sections", {})
    return {"z_vis": tuple(w["visible_opening_z_m"]), "rows": rows, "zs": zs, "frit": fr,
            "rake": w.get("rake_deg_from_vertical"),
            "shell": sh.get("z_yf_yb_w_rf_rb"), "wall": sh.get("wall_m", 0.03),
            "opening_x": g.get("opening_edge_abs_x_per_row"),
            "crown": sh.get("front_crown_r_m"), "pockets": sh.get("front_pockets") or [],
            "source": os.path.relpath(GLASS_IF_PATH, REPO).replace("\\", "/")}


GLASS_IF = load_glass_interface()


def glass_y(x, z):
    """Inner face of the exterior windscreen (A2 y) at lateral x and height z (clamped to the glass)."""
    if GLASS_IF is None:
        return ws_y(z) + 0.012 + 0.018 * (1 - min(1.0, (x / (XI - 0.055)) ** 2))
    zs, rows = GLASS_IF["zs"], GLASS_IF["rows"]

    def row_y(r):
        if x <= r[0][0]:
            return r[0][1]
        for (x0, y0), (x1, y1) in zip(r[:-1], r[1:]):
            if x <= x1:
                return y0 + (y1 - y0) * (x - x0) / max(1e-9, x1 - x0)
        return r[-1][1]
    if z <= zs[0]:
        k, t = 0, (z - zs[0]) / (zs[1] - zs[0])
    elif z >= zs[-1]:
        k, t = len(zs) - 2, (z - zs[-2]) / (zs[-1] - zs[-2])
    else:
        k = max(i for i in range(len(zs) - 1) if zs[i] <= z)
        t = (z - zs[k]) / (zs[k + 1] - zs[k])
    return row_y(rows[k]) + (row_y(rows[k + 1]) - row_y(rows[k])) * t


def shell_sec(z):
    tab = GLASS_IF["shell"]
    if z <= tab[0][0]:
        return tab[0][1:]
    for a, b in zip(tab[:-1], tab[1:]):
        if z <= b[0]:
            t = (z - a[0]) / (b[0] - a[0])
            return [a[i] + (b[i] - a[i]) * t for i in range(1, 6)]
    return tab[-1][1:]


# r7b: parts cut after the first fit (name -> bisect planes), see fit_to_exterior(). The footwell wall gets vertices at
# the top and bottom of the T bar pocket band and 0.92 m either side of the centre line (inside of it the wall is
# > 85 mm behind the skin and does not move).
FIT_CUTS = {"footwell_wall": [((0.92, 0, 0), (1, 0, 0)), ((-0.92, 0, 0), (1, 0, 0)),
                              ((0, 0, 1.60), (0, 0, 1)), ((0, 0, 1.88), (0, 0, 1))]}
POCKET_CLEAR = 0.015   # m: the interior stays this far behind the floor of an exterior front pocket
POCKET_EDGE = (0.02, 0.03)   # m: full pocket depth this far beyond the pocket outline, then a ramp back to the wall


def front_wall(p, z, wall):
    """Wall thickness the interior has to respect at front-skin parameter p (arc length from the centre line) and
    height z: `wall` on the skin, pocket depth + POCKET_CLEAR behind the published mask pockets (r7b, ADR 0047)."""
    we = wall
    for pk in GLASS_IF.get("pockets") or []:
        ps, zs = [c[0] for c in pk["param_z_quad"]], [c[1] for c in pk["param_z_quad"]]   # bounding box of the quad
        p0, p1, z0, z1 = min(ps), max(ps), min(zs), max(zs)
        pp = abs(p) if pk.get("mirror") else p
        full, ramp = POCKET_EDGE
        k = min(1.0 - max(0.0, max(p0 - pp, pp - p1) - full) / ramp,
                1.0 - max(0.0, max(z0 - z, z - z1) - full) / ramp)
        if k > 0.0:
            we = max(we, wall + (pk["depth_m"] + POCKET_CLEAR - wall) * min(1.0, k))
    return we


def front_fit(ax, y, z, wall):
    """Crowned front of the exterior (r7b): (|x|, y) pulled back inside the real skin at height z. The skin is
    exterior/geom.Loft.plan(): a crowned face of plan radius R about (0, yf - R) up to the tangent angle th0, then the
    corner arc rf about (w - rf, cyc). Both parts are clamped radially about their own centre (the old flat section
    moved y only, which throws a vertex near the side of the arc a long way), by the wall of front_wall()."""
    yf, yb, w, rf, rb = shell_sec(z)
    R = GLASS_IF["crown"]
    cx = w - rf
    d = math.sqrt((R - rf) ** 2 - cx ** 2)
    th0, cyc, ycr = math.atan2(cx, d), yf - R + d, yf - R
    if math.atan2(ax, y - ycr) <= th0:                       # crowned face
        lim, rho = R - front_wall(ax, z, wall), math.hypot(ax, y - ycr)
        return (ax, y) if rho <= lim else (ax * lim / rho, ycr + (y - ycr) * lim / rho)
    dx, dy = ax - cx, y - cyc
    if dy <= 0.0:                                            # behind the corner centre: the side wall
        return min(ax, w - wall), y
    a = math.atan2(dx, dy)
    lim, rho = max(0.002, rf - front_wall(R * math.sin(th0) + rf * (a - th0), z, wall)), math.hypot(dx, dy)
    # (front_wall takes the unsigned parameter: every published pocket is symmetric about the centre line)
    return (ax, y) if rho <= lim else (cx + dx * lim / rho, cyc + dy * lim / rho)


def fit_to_exterior(objs, margin=0.004):
    """A6 fit (glass_interface.json): pull every vertex that lies outside the exterior cab (shell inner surface =
    outer - wall, or the windscreen inner face inside the glazed opening) back inside, by `margin`. Run on the
    export meshes (modifiers applied, transforms baked). The exterior is the only skin and glazing in the game, so
    any interior vertex beyond it would show through the glass or poke through the paint. Returns per-object stats."""
    if GLASS_IF is None or not GLASS_IF.get("shell"):
        return {}
    wall = GLASS_IF["wall"] + margin
    z_lo, z_hi = GLASS_IF["shell"][0][0], GLASS_IF["shell"][-1][0]
    zg0, zg1 = GLASS_IF["zs"][0], GLASS_IF["zs"][-1]

    def glass_half(z):
        """|x| up to which the shell is cut (visible opening, 5 mm inside its edge); beyond it the A-pillar skin."""
        t = min(1.0, max(0.0, (z - zg0) / (zg1 - zg0)))
        f = t * (len(GLASS_IF["zs"]) - 1)
        k = min(len(GLASS_IF["zs"]) - 2, int(f))
        if GLASS_IF.get("opening_x"):
            ox = GLASS_IF["opening_x"]
            return ox[k] + (ox[k + 1] - ox[k]) * (f - k) - 0.005
        return GLASS_IF["rows"][k][-1][0] - 0.03
    out = {}

    def fit_obj(o):
        me = o.data
        n, dmax = 0, 0.0
        for v in me.vertices:
            x, y, z = v.co
            if not (z_lo <= z <= z_hi):
                continue
            yf, yb, w, rf, rb = shell_sec(z)
            ax = abs(x)
            nx, ny = ax, y
            # side wall
            nx = min(nx, w - wall)
            # front: glazed opening -> glass inner face, else shell (flat + plan corner arc)
            if WS_Z0 <= z <= WS_Z1 and ax <= glass_half(z):
                yl = glass_y(x, z) - 2 * margin    # y margin: the wrapped corners slope ~45 deg in plan
            else:
                cx, r = w - rf, max(0.002, rf - wall)
                if ax <= cx:
                    yl = yf - wall
                else:
                    yl = (yf - rf) + math.sqrt(max(0.0, r * r - min(r, ax - cx) ** 2))
                    if ax - cx > r:
                        nx = min(nx, cx + r)
                if GLASS_IF.get("crown") and (z < WS_Z0 or z > WS_Z1):
                    # r7b (review r6 E-N2): below the glazing the limit follows the real skin - crowned face, corner
                    # arc behind it, mask pockets. The flat section above put the dash carcass up to 5 mm outside
                    # the skin at the corner start and 36 mm in front of the pocket floor: the game camera saw the
                    # cab through the T bar. Faded into the old section over the last 40 mm below the glass edge
                    # (the pillar trims above it were fitted and reviewed against that one). Applied on top of the
                    # old clamp, so that everything already inside the real skin stays where it was reviewed.
                    # r7c: the same above the glazing. With the flat section the header shelf, the visor mounts and
                    # the roof lining reached the OUTER skin 0.83-0.97 m off the centre line (crown sag there 34-47 mm
                    # > the 30 mm wall): front_leak.py saw them from outside at z 3.23-3.53 m (42-52 rays per eye,
                    # the "roof marker pockets" of r7b). Faded in over the first 40 mm above the glass edge.
                    t = smooth(WS_Z0 - 0.04, WS_Z0, z) if z < WS_Z0 else 1.0 - smooth(WS_Z1, WS_Z1 + 0.04, z)
                    xc, yc = front_fit(nx, min(y, yl), z, wall)
                    nx, yl = xc + (nx - xc) * t, yc + (min(y, yl) - yc) * t
            ny = min(ny, yl)
            # back: flat + plan corner arc
            cxb, r = w - rb, max(0.002, rb - wall)
            ylb = yb + wall if nx <= cxb else (yb + rb) - math.sqrt(max(0.0, r * r - min(r, nx - cxb) ** 2))
            ny = max(ny, ylb)
            d = math.hypot(nx - ax, ny - y)
            if d > 1e-6:
                v.co.x = math.copysign(nx, x) if x != 0 else 0.0
                v.co.y = ny
                n += 1
                dmax = max(dmax, d)
        if n:
            me.update()
            prev = out.get(o.name, {"verts_moved": 0, "max_move_m": 0.0})
            out[o.name] = {"verts_moved": prev["verts_moved"] + n,
                           "max_move_m": max(prev["max_move_m"], round(dmax, 4))}

    for o in objs:
        fit_obj(o)
        cuts = FIT_CUTS.get(o.name)
        if cuts and GLASS_IF.get("pockets"):
            # r7b: a part with too few vertices for the vertex clamp (the footwell wall is one box across the whole
            # cab: its corners were fitted, its end edges still ran through the wrapped ends of the T bar pocket).
            # Cut after the first fit (the reviewed plane stays where it was), keep the cab-facing sheet (the other
            # faces of the box face the skin) and clamp the new vertices.
            bm = bmesh.new()
            bm.from_mesh(o.data)
            for co, no in cuts:
                bmesh.ops.bisect_plane(bm, geom=bm.verts[:] + bm.edges[:] + bm.faces[:], plane_co=co, plane_no=no,
                                       dist=1e-5)
            bm.normal_update()
            bmesh.ops.delete(bm, geom=[f for f in bm.faces if f.normal.y > -0.5], context="FACES")
            bm.to_mesh(o.data)
            bm.free()
            o.data.update()
            fit_obj(o)
    return out


if GLASS_IF is not None:
    # A6 fit: visible opening and the glass plane from the exterior. ws_y() stays the reference plane of the trims
    # (12 mm behind the glass inner face on the centre line, as the r3 trims were designed against the glass edge).
    WS_Z0, WS_Z1 = GLASS_IF["z_vis"]
    WS_Y0 = glass_y(0.0, WS_Z0) - 0.012
    # B2 (2026-11-09): the trims' reference plane takes the exterior's rake (7 deg, one-line front) and the placeholder
    # roof the exterior roof height (3.75 m); --rake still overrides for concept studies
    if GLASS_IF.get("rake") is not None:
        RAKE = float(GLASS_IF["rake"])
    if GLASS_IF.get("shell"):
        ROOF_OUT = GLASS_IF["shell"][-1][0]
    print(f"glass interface: WS_Z0 {WS_Z0}, WS_Z1 {WS_Z1}, WS_Y0 {WS_Y0:.4f} ({GLASS_IF['source']})")
SKIN_Z0 = DOOR_IF["shell_bottom_z"]             # A6 r3: placeholder skins end at the exterior shell edge (was 1.15)


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def lerp_tab(tab, x):
    if x <= tab[0][0]:
        return tab[0][1]
    for (x0, y0), (x1, y1) in zip(tab[:-1], tab[1:]):
        if x <= x1:
            t = (x - x0) / (x1 - x0)
            return y0 + (y1 - y0) * t
    return tab[-1][1]


# ---------------------------------------------------------------- args
def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--cams", default="all")
    p.add_argument("--light", default="overcast,lowsun")
    p.add_argument("--trim", default="koniak", choices=sorted(TRIMS))
    p.add_argument("--badge", default="trakt", choices=["none", "trakt", "bielik", "narew"])
    p.add_argument("--paint", default="0.70,0.70,0.68")
    p.add_argument("--rake", type=float, default=None, help="default: glass_interface.json rake (exterior)")
    p.add_argument("--res", default="1600x900")
    p.add_argument("--samples", type=int, default=384)
    p.add_argument("--blend", default="")
    p.add_argument("--stats", default="")
    p.add_argument("--suffix", default="")
    p.add_argument("--hide", default="", help="comma list of objects-name prefixes to hide (debug views)")
    p.add_argument("--camxyz", default="", help="debug camera 'x,y,z:tx,ty,tz:hfov' (name 'debug')")
    p.add_argument("--lod", type=int, default=0, help="0 = full (High), 1 = Medium, 2 = Low tessellation")
    p.add_argument("--no-backdrop", action="store_true", help="skip the render backdrop (tests, export)")
    return p.parse_args(argv)


# ---------------------------------------------------------------- collections / groups
COLLS = {}


def group(name):
    if name not in COLLS:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
        COLLS[name] = c
    G.STATE["coll"] = COLLS[name]


# ---------------------------------------------------------------- materials
def build_materials(a):
    trim = TRIMS[a.trim]
    paint_rgb = tuple(float(v) for v in a.paint.split(","))
    # A6 (critic #5, #12): soft-touch stays dark and velvety (rougher, lower specular, no bright dust film);
    # lower dash, door and pillar trims step up to clear mid-tones so the cab reads without bounce light (URP).
    M.pbr("dash_soft", (0.045, 0.046, 0.048), "dashgrain", 0.10, rough_add=0.24, nstr=1.25, spec=0.16,
          dust=(0.18, (0.070, 0.068, 0.062), 0.05))
    # B2.1 (owner sheets D19/D20): charcoal mouldings round the koniak leather (r3 warm-grey lower dash read as a
    # 2000s cab); still a clear step above the soft top so the parting lines and grain read in the URP look
    M.pbr("dash_lower", (0.088, 0.087, 0.085), "hardgrain", 0.08, nstr=0.9, rough_add=0.05, spec=0.42,
          wear=(0.30, 1.45), dust=(0.22, (0.105, 0.100, 0.090), 0.06))
    # B2.2: grain normal up on the stack / lower mouldings (read as smooth paint in the r4 frames)
    M.pbr("dash_mid", (0.066, 0.066, 0.066), "dashgrain", 0.08, nstr=1.2, rough_add=0.08, spec=0.40)
    M.pbr("trim_light", (0.270, 0.262, 0.245), "hardgrain", 0.08, nstr=0.7, rough_add=0.06, spec=0.40)
    M.pbr("dash_dark", (0.030, 0.030, 0.032), "hardgrain", 0.06, nstr=1.0, rough_add=0.04)
    M.pbr("trim_insert", trim, "dashgrain", 0.10, nstr=0.8)
    # B2.1: koniak leather inserts (passenger dash, door cards, armrests, stack flank), stitched; slight wear
    M.pbr("leather_trim", tuple(c * 1.05 for c in trim), "leather", 0.12, nstr=0.9, wear=(0.20, 1.6))
    M.pbr("leather", (0.034, 0.033, 0.032), "leather", 0.12, nstr=1.0, wear=(0.26, 2.3), coat=0.0)
    # B2.2: rim leather has a soft satin sheen (hand oils), polished smoother at 10 and 2 o'clock
    M.pbr("leather_wheel", (0.030, 0.029, 0.028), "leather", 0.05, rough_mul=0.82, nstr=0.8, wear=(0.15, 2.1))
    # r8: perforated grip leather on the rim sides (3 / 9 o'clock up to the cross seams), same hide
    M.pbr("leather_wheel_perf", (0.030, 0.029, 0.028), "leather", 0.05, rough_mul=0.82, nstr=0.8,
          wear=(0.15, 2.1), perforate=0.04)
    # r8: hub wordmark embossed tone-on-tone (graphite satin, a step above the soft cover, not chrome)
    M.simple("emboss", (0.120, 0.120, 0.124), rough=0.34)
    centre = (0.040, 0.039, 0.038) if a.trim == "grafit" else tuple(c * 0.85 for c in trim)
    M.pbr("leather_centre", centre, "leather", 0.12, nstr=0.7, perforate=0.04, wear=(0.34, 1.5))
    M.pbr("seat_fabric", tuple(c * 0.9 + 0.01 for c in trim), "seatfabric", 0.06, nstr=1.0, sheen=0.3)
    M.pbr("headliner", (0.31, 0.30, 0.28), "fabric", 0.05, nstr=0.6, sheen=0.2)
    M.pbr("wall_fabric", (0.165, 0.160, 0.152), "fabric", 0.05, nstr=0.8, sheen=0.25)
    M.pbr("mattress", (0.085, 0.088, 0.095), "seatfabric", 0.06, nstr=1.0, sheen=0.3)
    M.pbr("curtain", (0.100, 0.102, 0.106), "fabric", 0.04, nstr=0.9, sheen=0.4)
    M.pbr("floor_mat", (0.040, 0.040, 0.039), "rubbermat", 0.40, nstr=1.0, wear=(0.55, 2.4),
          dust=(0.6, (0.13, 0.12, 0.10), 0.10))
    M.pbr("satin", (0.50, 0.50, 0.50), "brushed", 0.10, metal=0.85, rough_add=0.05, nstr=0.3)
    M.pbr("metal_dark", (0.050, 0.050, 0.052), "brushed", 0.10, metal=0.0, rough_add=0.15, nstr=0.3)
    M.pbr("scuff_plate", (0.42, 0.42, 0.42), "brushed", 0.08, metal=0.9, rough_add=0.10, nstr=0.5,
          wear=(0.18, 1.3), dust=(0.5, (0.12, 0.11, 0.09), 0.04))
    M.simple("piano", (0.010, 0.010, 0.011), rough=0.16, spec=0.5)
    # B2.2: grab handles (door pulls) - same moulding as dash_dark, but they polish where the hand closes
    M.pbr("grab_dark", (0.030, 0.030, 0.032), "hardgrain", 0.06, nstr=1.0, rough_add=0.04, wear=(0.17, 1.7))
    M.simple("rubber", (0.028, 0.028, 0.028), rough=0.82)
    M.simple("gap", (0.004, 0.004, 0.004), rough=0.9)
    # B2.2: keys are textured matt ABS that polishes where the thumb lands (wear -> smoother, a touch lighter)
    M.pbr("switch", (0.021, 0.021, 0.022), "hardgrain", 0.03, nstr=0.6, rough_add=0.10, spec=0.40, wear=(0.20, 1.35))
    M.simple("knob", (0.025, 0.025, 0.026), rough=0.36)
    M.simple("webbing", (0.062, 0.062, 0.066), rough=0.78, spec=0.3)
    M.simple("led_off", (0.16, 0.15, 0.13), rough=0.35)        # A6.1: unlit LED slit, not a white dot
    M.simple("hazard_red", (0.30, 0.035, 0.03), rough=0.40)
    M.simple("lamp_lens", (0.80, 0.80, 0.78), rough=0.25, emit=((1.0, 0.95, 0.85), 0.0))
    M.simple("yellow", (0.50, 0.33, 0.02), rough=0.5)
    # A6 r3: mirror glass shows a placeholder 'probe' image (the game uses camera RenderTextures), not a white slab
    M.mirror_rt("mirror", "mirror_rt_side.png")
    M.mirror_rt("mirror_down", "mirror_rt_down.png")
    # A6 r3: black ceramic frit (enamel on the inner face of the windscreen), geometry -> same in Cycles, URP and game
    M.simple("frit", (0.011, 0.011, 0.012), rough=0.42, spec=0.5)
    M.simple("ext_plastic", (0.032, 0.032, 0.034), rough=0.6)
    M.simple("chrome", (0.75, 0.75, 0.75), rough=0.12, metal=1.0)
    M.paint("paint", paint_rgb)
    M.thin_glass("windscreen", grime=0.10, sunstrip=(2.86, 3.02, (0.36, 0.42, 0.44)))
    M.thin_glass("side_glass", grime=0.06)
    M.thin_glass("cover_glass", tint=(0.96, 0.96, 0.96))
    M.display("disp_cluster", "display_cluster.png", strength=1.5, rough=0.10, fingerprints=0.10)
    M.display("disp_info", "display_infotainment.png", strength=1.1, rough=0.12, fingerprints=0.18)
    M.display("disp_gauges", "display_gauges.png", strength=1.2, rough=0.06)
    M.display("disp_din", "display_din.png", strength=1.0, rough=0.2)
    # A6 r3: warm-grey thread, a step above the leather, not a white dotted line (critic r2 #5)
    M.decal("stitch", "stitch_rgba.png", (0.34, 0.31, 0.27), rough=0.7)
    M.decal("stitch_dark", "stitch_rgba.png", (0.27, 0.265, 0.25), rough=0.7)   # B2.2: thread reads on the rim
    # r8: contrasting rim thread in the trim colour (koniak: tan), not a white dotted line
    M.decal("stitch_wheel", "stitch_rgba.png", tuple(min(0.9, c * 6.0 + 0.02) for c in trim), rough=0.7)
    M.simple("thread_wheel", tuple(min(0.9, c * 4.5 + 0.03) for c in trim), rough=0.8, spec=0.3)   # LOD0 stitches
    M.decal("icons", "icons_atlas.png", (0.80, 0.80, 0.76), rough=0.4, alpha_from="mask")
    M.decal("grille", "grille_mask.png", (0.02, 0.02, 0.02), rough=0.6, alpha_from="mask")
    M.decal("grille_dash", "grille_mask.png", (0.040, 0.041, 0.043), rough=0.65, alpha_from="mask")
    M.grass("grass")
    M.line_paint("line_paint")
    M.blind("blind")


# ---------------------------------------------------------------- wear attribute helper
def set_wear(ob, fn):
    """Per-vertex float attribute 'wear' (0..1) evaluated in object-local coordinates."""
    me = ob.data
    at = me.attributes.get("wear") or me.attributes.new("wear", "FLOAT", "POINT")
    for v in me.vertices:
        at.data[v.index].value = max(0.0, min(1.0, fn(v.co)))


def set_wear_w(ob, fn, add=False):
    """Like set_wear, but fn gets world coordinates; add=True keeps the larger of the old and the new value."""
    me = ob.data
    at = me.attributes.get("wear") or me.attributes.new("wear", "FLOAT", "POINT")
    mw = ob.matrix_world.copy()
    for v in me.vertices:
        w = max(0.0, min(1.0, fn(mw @ v.co)))
        at.data[v.index].value = max(at.data[v.index].value, w) if add else w


def set_attr_w(ob, name, fn, add=True):
    """Per-vertex float attribute `name` from fn(world co, world normal). r6b: 'tint_add' (vertex tint x (1 + v)) and
    'rough_add' (roughness + v) carry authored zones (dust, polish) into the export's vertex colour; no texture."""
    me = ob.data
    at = me.attributes.get(name) or me.attributes.new(name, "FLOAT", "POINT")
    mw = ob.matrix_world.copy()
    m3 = mw.to_3x3()
    for v in me.vertices:
        val = fn(mw @ v.co, (m3 @ v.normal).normalized())
        at.data[v.index].value = at.data[v.index].value + val if add else val


def vnoise(x, y, z=0.0):
    """Smooth value noise 0..1 (trilinear hash01 lattice): wear break-up that does not alias on the vertex grid."""
    xi, yi, zi = math.floor(x), math.floor(y), math.floor(z)
    fx, fy, fz = x - xi, y - yi, z - zi
    fx, fy, fz = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy), fz * fz * (3 - 2 * fz)
    r = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                r += (hash01(xi + dx, yi + dy, zi + dz) * (fx if dx else 1 - fx) * (fy if dy else 1 - fy)
                      * (fz if dz else 1 - fz))
    return r


def hash01(x, y, z):
    s = math.sin(x * 127.1 + y * 311.7 + z * 74.7) * 43758.5453
    return s - math.floor(s)


# ---------------------------------------------------------------- cab shell (inner trim + outer skin)
def build_shell():
    group("shell")
    T = 0.08
    # floor slab under the mat, outer floor
    box_mm("floor_slab", -HALF_OUT, HALF_OUT, YB - T, FRONT_WALL_Y + 0.06, FLOOR - 0.10, FLOOR - 0.005, "metal_dark")
    # back wall (inner fabric face) and outer skin
    box_mm("back_wall", -XI, XI, YB - 0.02, YB, FLOOR, CEIL_SIDE + 0.15, "wall_fabric", bev=0.004)
    box_mm("back_skin", -HALF_OUT, HALF_OUT, YB - T, YB - 0.02, SKIN_Z0, ROOF_OUT - 0.05, "paint", bev=0.03)
    # headliner: lofted vault along Y
    prof = []
    for i in range(25):
        t = -1 + 2 * i / 24
        x = t * XI
        z = CEIL_SIDE + (CEIL - CEIL_SIDE) * (1 - abs(t) ** 2.4) ** 0.8
        prof.append((x, z))
    ys = [YB - 0.01, 0.0, 0.6, ws_y(WS_Z1) + 0.06]
    loops = [[V(x, y, z) for x, z in prof] for y in ys]
    hl = loft("headliner", loops, "headliner", closed=False)
    solidify(hl, 0.02, offset=1.0)
    # roof outer skin (box, rounded)
    box_mm("roof_skin", -HALF_OUT, HALF_OUT, YB - T, ws_y(WS_Z1) + 0.16, CEIL + 0.02, ROOF_OUT, "paint", bev=0.12, seg=4)
    # side walls: door opening y in [DOOR_Y0, DOOR_Y1]; walls behind door, under, over window
    for s in (-1, 1):
        xin, xout = s * XI, s * HALF_OUT
        # rear side wall (behind door, bunk area)
        box_mm(f"side_rear_{s}", xin, xin + s * 0.02, YB, DOOR_Y0, FLOOR, CEIL_SIDE + 0.05, "wall_fabric", bev=0.003)
        box_mm(f"skin_rear_{s}", xin + s * 0.02, xout, YB - T, DOOR_Y0 + 0.01, SKIN_Z0, ROOF_OUT - 0.08, "paint",
               bev=0.02)
        # header over door (inside: fabric strip under headliner)
        box_mm(f"side_top_{s}", xin, xin + s * 0.02, DOOR_Y0, ws_y(3.0) - 0.10, WIN_Z1 + 0.06, CEIL_SIDE + 0.05,
               "wall_fabric", bev=0.003)
        box_mm(f"skin_top_{s}", xin + s * 0.02, xout, DOOR_Y0, ws_y(3.0) + 0.05, WIN_Z1 - 0.01, ROOF_OUT - 0.08, "paint",
               bev=0.02)
        # lower front corner skin (between door and front wall, below the A-pillar)
        box_mm(f"skin_front_{s}", xin + s * 0.02, xout, DOOR_Y1 - 0.02, FRONT_WALL_Y + 0.10, SKIN_Z0, WS_Z0, "paint",
               bev=0.02)
        box_mm(f"side_front_{s}", xin, xin + s * 0.02, DOOR_Y1 - 0.02, FRONT_WALL_Y, FLOOR, WS_Z0, "dash_dark")
        # r4: A-pillar foot trim. Since the modern cab (ADR 0047) the door shut line runs diagonally to the pillar, and
        # between it, the dash end and the pillar base the painted corner skin (body colour) and the lit top of
        # side_front showed as a light wedge from the driver's eye. A dark moulding from the floor to the beltline
        # (kick panel ahead of the door) closes it.
        zs_f = [FLOOR + 0.01 + (WIN_Z0 - 0.004 - FLOOR - 0.01) * i / 12 for i in range(13)]
        loops = []
        for z in zs_f:
            ya, yb = door_front(z) + 0.004, FRONT_WALL_Y - 0.16
            if yb - ya < 0.02:
                yb = ya + 0.02
            loops.append([V(xin - s * 0.003, ya, z), V(xin - s * 0.003, yb, z), V(xin + s * 0.045, yb, z),
                          V(xin + s * 0.045, ya, z)])
        loft(f"apillar_foot_{s}", loops, "dash_dark", closed=True, cap0=True, cap1=True, sharp=40)
        # r6b (review r6 C-N7): footwell corner moulding. The headlamp bucket of the modern front (ADR 0047) reaches up
        # to 75 mm inside the fitted interior wall in the lower front corner (plan radius 0.286 m about the corner
        # centre against the trim's 0.346 m, x 0.87-1.2, z up to 1.545): the lit DRL guide stood inside the cab as a
        # white L in cab-dash. A real cab has the lamp box / wheel-arch intrusion trimmed there: a quarter-round
        # moulding (plan radius 0.262 m), floor to 1.60 m, shoulder rolled back to the wall.
        yf_c, _, w_c, rf_c, _ = shell_sec(FLOOR + 0.06) if GLASS_IF and GLASS_IF.get("shell") else (1.395, 0, HALF_OUT, 0.38, 0)
        ccx, ccy = w_c - rf_c, yf_c - rf_c
        na = G.Q(12, 4)
        loops = []
        zs_c = (((FLOOR - 0.004, 0.0), (1.575, 0.0), (1.593, 0.007), (1.600, 0.022)) if G.STATE["q"] > 0.5 else
                ((FLOOR - 0.004, 0.0), (1.600, 0.0)))     # LOD2: one band + cap (22k budget)
        for z, ins in zs_c:
            r = rf_c - 0.118 + ins
            ring = [V(s * (ccx - 0.045 + ins), yf_c - 0.03, z), V(s * (ccx - 0.045 + ins), ccy + r - 0.004, z)]
            ring += [V(s * (ccx + r * math.cos(a)), ccy + r * math.sin(a), z)
                     for a in (math.radians(90 - 90 * i / na) for i in range(na + 1))]
            ring += [V(s * (ccx + r), ccy - 0.03 + ins, z), V(s * (XI + 0.03), ccy - 0.065 + ins, z),
                     V(s * (XI + 0.03), yf_c - 0.03, z)]
            loops.append(ring if s > 0 else ring[::-1])
        loft(f"footwell_wall_cnr_{s}", loops, "dash_dark", closed=True, cap1=True, sharp=40)
    # front: wall under the windscreen (outer) + inner footwell wall
    box_mm("front_skin", -HALF_OUT, HALF_OUT, FRONT_WALL_Y + 0.0, FRONT_WALL_Y + 0.10, SKIN_Z0, WS_Z0 - 0.02,
           "paint", bev=0.03)
    box_mm("footwell_wall", -XI, XI, FRONT_WALL_Y - 0.02, FRONT_WALL_Y, FLOOR, 1.95, "dash_dark")
    # header strip above the windscreen (inside, mostly hidden by overhead storage)
    box_mm("ws_header", -XI, XI, ws_y(WS_Z1) - 0.02, ws_y(WS_Z1) + 0.12, WS_Z1 - 0.01, CEIL + 0.02, "headliner")


def door_front(z):
    """Aperture front edge y at height z (exterior front shut line - seal overlap): vertical behind the fixed corner
    panel, then diagonal to the A-pillar."""
    return lerp_tab([(zz, yy) for yy, zz in DOOR_IF["door_front_yz"]], z)


DOOR_Y0 = DOOR_IF["door_y0"]                    # aperture rear edge (B-pillar side)
DOOR_Y1 = door_front(FLOOR)                     # aperture front edge at floor height (fixed corner panel ahead)
WIN_Z0, WIN_Z1 = DOOR_IF["side_glass_z"]        # side window (beltline, top)


def door_y(y, z, margin=0.0):
    """Door-card features keep their A6 positions (they belong to the seat, which did not move) but never run past the
    aperture front edge at their height."""
    return min(y, door_front(z) - margin)


def side_win_front(z):
    """Side-glass front edge (follows the A-pillar); from the exterior interface when present."""
    pts = DOOR_IF["side_glass_front_yz"]
    if not pts:
        return ws_y(z) - 0.15
    (y0, z0), (y1, z1) = pts[0], pts[-1]
    return y0 + (y1 - y0) * (z - z0) / (z1 - z0)


def shell_in_x(y, z, inset=0.0):
    """|x| of the exterior shell's inner face at (y, z) on the side wall / front corner arc (glass_interface.json
    sections); None without the interface."""
    if GLASS_IF is None or not GLASS_IF.get("shell"):
        return None
    yf, yb, w, rf, rb = shell_sec(min(max(z, GLASS_IF["shell"][0][0]), GLASS_IF["shell"][-1][0]))
    r = max(0.01, rf - GLASS_IF["wall"])
    return (w - rf) + math.sqrt(max(0.0, r * r - min(r, max(0.0, y - (yf - rf))) ** 2)) - inset


def ws_open_x(z):
    """|x| of the exterior windscreen's visible opening edge at height z (glass_interface.json), else None."""
    if GLASS_IF is None or not GLASS_IF.get("opening_x"):
        return None
    zc = min(max(z, WS_Z0), WS_Z1)
    zs, ox = GLASS_IF["zs"], GLASS_IF["opening_x"]
    f = (zc - zs[0]) / (zs[-1] - zs[0]) * (len(zs) - 1)
    k = min(len(zs) - 2, int(f))
    return ox[k] + (ox[k + 1] - ox[k]) * (f - k)


def apillar_frame(s, z):
    """Modern cab (ADR 0047 r3): the A-pillar as the driver sees it = the strip between the windscreen's clear edge and
    the side-glass front edge on the rounded corner. Returns (A, B, t, n) in plan (x, y): A = inner glass face just
    inside the windscreen's side frit, B = shell inner face at the side-glass front edge, t = unit A->B, n = unit
    normal pointing into the cab (almost exactly along the driver's sight line, so trim depth costs no view angle).
    None when the exterior publishes no opening (old interface): the A6 box pillar is built instead."""
    if GLASS_IF is None or not GLASS_IF.get("opening_x") or not GLASS_IF.get("shell"):
        return None
    zc = min(max(z, WS_Z0), WS_Z1)
    xe = ws_open_x(z) - 0.014          # 14 mm in x = behind the 28 mm side frit on the arc
    a = V(xe, glass_y(xe, zc) - 0.004, 0)
    ys = side_win_front(z) + 0.006
    b = V(shell_in_x(ys, zc), ys, 0)
    t = (b - a).normalized()
    n = V(-t.y, t.x, 0)
    if n.x > 0:
        n = -n
    m = lambda v: V(s * v.x, v.y, 0)  # noqa: E731
    return m(a), m(b), m(t), m(n)


# ---------------------------------------------------------------- windscreen, A-pillars, side glass
def build_glass():
    group("glass")
    # windscreen: one sheet, curved into the pillars at the outer 120 mm (slight wrap)
    hw = XI - 0.055
    if ws_open_x(WS_Z0) is not None and GLASS_IF.get("shell"):
        hw = max(hw, ws_open_x(WS_Z0))       # r3: the placeholder screen and its frit follow the exterior opening
    nwx, nwz = G.Q(40, 10), G.Q(8, 3)
    xs = [-1 + 2 * i / nwx for i in range(nwx + 1)]
    loops = []
    for zi in range(nwz + 1):
        z = WS_Z0 - 0.02 + (WS_Z1 - WS_Z0 + 0.04) * zi / nwz
        lp = []
        for t in xs:
            x = t * hw
            y = glass_y(x, z)          # A6: inner face of the exterior windscreen (placeholder glass)
            lp.append(V(x, y, z))
        loops.append(lp)
    loft("windscreen", list(zip(*loops)), "windscreen", closed=False, sharp=None)
    # (loft along x: loops transposed so faces span z)
    build_frit(hw)
    # rubber gasket around the windscreen (outside face)
    for z in (WS_Z0 - 0.025, WS_Z1 + 0.025):
        box_mm(f"ws_gasket_{z:.2f}", -hw - 0.02, hw + 0.02, ws_y(z) + 0.012, ws_y(z) + 0.05, z - 0.015, z + 0.015, "rubber")
    # side windows (door glass) + rubber channels
    for s in (-1, 1):
        x = s * (XI + 0.035)
        yf0, yf1 = side_win_front(WIN_Z0), side_win_front(WIN_Z1)
        corners = [V(x, DOOR_Y0 + 0.07, WIN_Z0), V(x, yf0, WIN_Z0), V(x, yf1, WIN_Z1), V(x, DOOR_Y0 + 0.07, WIN_Z1)]
        if apillar_frame(s, 2.5) is not None:   # r3: the glass front edge sits on the corner arc of the modern cab
            corners[1] = V(s * min(abs(x), shell_in_x(yf0, WIN_Z0, 0.004)), yf0, WIN_Z0)
            corners[2] = V(s * min(abs(x), shell_in_x(yf1, WIN_Z1, 0.004)), yf1, WIN_Z1)
        bm = bmesh.new()
        vs = [bm.verts.new(c) for c in corners]
        bm.faces.new(vs)
        bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=3, use_grid_fill=True)
        G.finish(f"side_glass_{s}", bm, "side_glass", smooth=False)
        # window frame / channel (inside)
        tube(f"win_channel_{s}", [c + V(-s * 0.012, 0, 0) for c in corners] + [corners[0] + V(-s * 0.012, 0, 0)],
             0.011, "rubber", seg=8, cap=False)
        # outer skin around the side window: below beltline is the door skin
        box_mm(f"door_skin_{s}", s * (XI + 0.05), s * HALF_OUT, DOOR_Y0 + 0.01, DOOR_Y1 + 0.02, SKIN_Z0, WIN_Z0,
               "paint", bev=0.015)
        # B-pillar strip between glass and rear wall (outer)
        box_mm(f"bpillar_skin_{s}", s * (XI + 0.02), s * HALF_OUT, DOOR_Y0, DOOR_Y0 + 0.07, WIN_Z0, WIN_Z1 + 0.07, "paint")
    # A-pillars: inner trim lofted along the windscreen edge, outer skin behind it
    for s in (-1, 1):
        if apillar_frame(s, 2.5) is not None:
            # slim padded pillar following the glass edges of the rounded corner: 62 mm deep along the sight line,
            # only 10 mm wider than the opaque strip on each side; grab handle and tweeter sit in its shadow
            loops, skin = [], []
            for zi in range(9):
                z = WS_Z0 - 0.06 + (WS_Z1 + 0.08 - WS_Z0 + 0.06) * zi / 8
                a, b, t, n = apillar_frame(s, z)
                mid = (a + b) / 2
                sec = [a - t * 0.010 + n * 0.006, a + t * 0.004 + n * 0.040, mid + n * 0.062, b - t * 0.004 + n * 0.040,
                       b + t * 0.010 + n * 0.006, b + t * 0.006 - n * 0.004, a - t * 0.006 - n * 0.004]
                loops.append([V(q.x, q.y, z) for q in sec])
                skin.append([V(q.x, q.y, z) for q in (a - n * 0.004, b - n * 0.004, b - n * 0.028, a - n * 0.028)])
            ap = loft(f"apillar_trim_{s}", loops, "trim_light", closed=True, cap0=True, cap1=True)
            bevel(ap, 0.008, 2, angle=30)
            loft(f"apillar_skin_{s}", skin, "paint", closed=True, cap0=True, cap1=True)
            z0, z1 = 2.22, 2.80

            def on_pillar(z, depth):
                # along the driver's sight line through the pillar centre: hidden in the pillar's shadow
                a, b, t, n = apillar_frame(s, z)
                mid = (a + b) / 2
                d = V(EYE[0] - mid.x, EYE[1] - mid.y, 0).normalized()
                q = mid + n * min(depth, 0.058) + d * max(0.0, depth - 0.058)
                return V(q.x, q.y, z)
            pts = [on_pillar(z0, 0.058), on_pillar(z0 + 0.04, 0.098), on_pillar(z1 - 0.04, 0.098), on_pillar(z1, 0.058)]
            tube(f"grab_A_{s}", G.polyline_smooth(pts, 6), 0.0135, "dash_dark", seg=12)
            a, b, t, n = apillar_frame(s, 2.08)
            c = on_pillar(2.08, 0.060)
            cyl(f"tweeter_{s}", c, 0.022, 0.008, "dash_dark", seg=20, rot=n.to_track_quat("Z", "Y").to_matrix())
            plane_uv(f"tweeter_grille_{s}", quad_on(c, n, V(0, 0, 1), 0.04, 0.04, off=0.0045), "grille",
                     uv=((0, 0), (1, 0), (1, 1), (0, 1)))
            continue
        loops = []
        for zi in range(7):
            z = WS_Z0 - 0.06 + (WS_Z1 + 0.08 - WS_Z0 + 0.06) * zi / 6
            # A6: the exterior glass wraps round the corner; keep the trim's front face 8 mm behind its inner face
            y = min(ws_y(z), glass_y(s * (XI - 0.05), min(max(z, WS_Z0), WS_Z1)) - 0.058)
            sec = [(XI - 0.085, y + 0.025), (XI - 0.05, y + 0.05), (XI + 0.01, y + 0.045), (XI + 0.01, side_win_front(z) - 0.02),
                   (XI - 0.03, side_win_front(z) - 0.035), (XI - 0.075, y - 0.07), (XI - 0.095, y - 0.02)]
            loops.append([V(s * px, py, z) for px, py in sec])
        ap = loft(f"apillar_trim_{s}", loops, "trim_light", closed=True, cap0=True, cap1=True)
        bevel(ap, 0.008, 2, angle=30)
        # outer pillar skin (paint) between windscreen and door glass
        loops = []
        for zi in range(5):
            z = WS_Z0 - 0.05 + (WS_Z1 + 0.12 - WS_Z0) * zi / 4
            y = ws_y(z)
            sec = [(XI - 0.02, y + 0.05), (HALF_OUT, y + 0.03), (HALF_OUT, side_win_front(z) - 0.03), (XI + 0.02, side_win_front(z) - 0.03)]
            loops.append([V(s * px, py, z) for px, py in sec])
        loft(f"apillar_skin_{s}", loops, "paint", closed=True, cap0=True, cap1=True)
        # grab handle on the A-pillar (entry aid), satin with rubber inserts
        z0, z1 = 2.22, 2.80
        yy = lambda z: ws_y(z) - 0.065
        xg = s * (XI - 0.11)
        pts = [V(xg + s * 0.035, yy(z0), z0), V(xg, yy(z0) - 0.02, z0 + 0.04), V(xg, yy(z1) - 0.02, z1 - 0.04),
               V(xg + s * 0.035, yy(z1), z1)]
        tube(f"grab_A_{s}", G.polyline_smooth(pts, 6), 0.0155, "dash_dark", seg=12)
        # tweeter in the pillar
        c = V(s * (XI - 0.06), ws_y(2.42) - 0.05, 2.42)
        n = V(-s * 0.7, -0.6, 0.1).normalized()
        cyl(f"tweeter_{s}", c, 0.028, 0.008, "dash_dark", seg=20, rot=n.to_track_quat("Z", "Y").to_matrix())
        plane_uv(f"tweeter_grille_{s}", quad_on(c, n, V(0, 0, 1), 0.05, 0.05, off=0.0045), "grille",
                 uv=((0, 0), (1, 0), (1, 1), (0, 1)))
    # A6.1 (critic r2 #7): wipers parked on the glass just above the bottom frit, as the exterior parks them
    # (tools/blender/truck/exterior/body.py wipers(): pivots x -1.00 / -0.08, 0.86 m arms, blade rising 2.142 -> 2.158 m
    # over its length). Placeholder for interior-only renders (CAB_ShellPlaceholder); the game uses WIPER_L/R.
    for i, (px, ln) in enumerate(WIPERS):
        def on_glass(x, z, off):
            return V(x, glass_y(x, min(max(z, WS_Z0), WS_Z1)) + 0.006 + off, z)
        xb0, xb1 = px + 0.06, px + ln + 0.02
        pts = [on_glass(xb0 + (xb1 - xb0) * k / 10, wiper_z(xb0 + (xb1 - xb0) * k / 10, px, ln), 0.010) for k in range(11)]
        tube(f"wiper_blade_{i}", pts, 0.0085, "rubber", seg=6)
        spine = [p_ + V(0, 0.010, 0.004) for p_ in pts]
        tube(f"wiper_spine_{i}", spine, 0.0055, "ext_plastic", seg=6)
        p0 = on_glass(px, WS_Z0 - 0.025, 0.030)
        tip = on_glass(xb1 - 0.02, wiper_z(xb1, px, ln) + 0.018, 0.022)
        mid = p0.lerp(tip, 0.5) + V(0, 0.012, 0)
        tube(f"wiper_arm_{i}", [p0, mid, tip], 0.0075, "ext_plastic", seg=8)


WIPERS = ((-1.00, 0.86), (-0.08, 0.86))   # (pivot x, arm length): same as exterior/body.py wipers()
WIPER_Z0, WIPER_RISE = WS_Z0 + 0.075 + 0.007, 0.016   # blade lower edge just above the 75 mm frit (B2: 2.022 m)


def wiper_z(x, px, ln):
    return WIPER_Z0 + 0.0085 + WIPER_RISE * min(1.0, max(0.0, (x - px) / ln))


FRIT_BOTTOM, FRIT_TOP, FRIT_SIDE = 0.075, 0.05, 0.045   # frit band widths above/below the visible glass edge (m)
if GLASS_IF is not None and GLASS_IF["frit"]:   # A6: one print, same widths as the exterior band
    FRIT_BOTTOM, FRIT_TOP, FRIT_SIDE = (GLASS_IF["frit"][k] for k in ("bottom", "top", "sides"))


def build_frit(hw):
    """A6 r3 (critic r2 #2): black ceramic frit printed on the inner face of the windscreen. Real screens carry a
    60-120 mm opaque band at the bottom (hides the cowl, wiper spindles and the bonding bead) with a dot-matrix fade
    on its inner edge, a narrower band at the top and down the sides. Built as geometry 1.5 mm inboard of the glass so
    Cycles, the URP-like preview and the game all get it without a shader mask; normals face the cab."""
    def gy(x, z):
        return glass_y(x, z) - 0.0015

    def patch(name, x0, x1, z0, z1, nx, nz):
        bm = bmesh.new()
        rows = [[bm.verts.new(V(x0 + (x1 - x0) * i / nx, gy(x0 + (x1 - x0) * i / nx, z0 + (z1 - z0) * j / nz),
                                 z0 + (z1 - z0) * j / nz)) for i in range(nx + 1)] for j in range(nz + 1)]
        for j in range(nz):
            for i in range(nx):
                bm.faces.new((rows[j][i], rows[j][i + 1], rows[j + 1][i + 1], rows[j + 1][i]))   # normal -> -Y
        ob = G.finish(name, bm, "frit", smooth=True, sharp=None, recalc=False)
        ob["fixed_uv"] = True          # no AO-atlas island of its own (inherits the occlusion of the cowl under it)
        return ob

    zb, zt = WS_Z0 + FRIT_BOTTOM, WS_Z1 - FRIT_TOP
    patch("ws_frit_bottom", -hw, hw, WS_Z0 - 0.02, zb, G.Q(40, 10), 1)
    patch("ws_frit_top", -hw, hw, zt, WS_Z1 + 0.02, G.Q(40, 10), 1)
    for s in (-1, 1):
        if ws_open_x(zb) is not None and GLASS_IF.get("shell"):
            # r3: side band on the wrapped part of the glass, following the opening edge row by row (16 mm in x
            # = the exterior's 28 mm band on the ~55 deg arc); the old band at +-1.11 m stood in the clear glass
            nz = G.Q(8, 3)
            bm = bmesh.new()
            rows = []
            for j in range(nz + 1):
                z = zb + (zt - zb) * j / nz
                xo = ws_open_x(z)
                xa, xb = sorted((s * (xo + 0.004), s * (xo - 0.016)))
                rows.append([bm.verts.new(V(x, gy(x, z), z)) for x in (xa, xb)])
            for j in range(nz):
                bm.faces.new((rows[j][0], rows[j][1], rows[j + 1][1], rows[j + 1][0]))
            ob = G.finish(f"ws_frit_side_{s}", bm, "frit", smooth=True, sharp=None, recalc=False)
            ob["fixed_uv"] = True
            continue
        xa, xb = sorted((s * hw, s * (hw - FRIT_SIDE)))
        patch(f"ws_frit_side_{s}", xa, xb, zb, zt, 1, G.Q(8, 3))
    # dot-matrix fade above the bottom band and below the top band: two rows of shrinking hexagonal dots
    bm = bmesh.new()
    pitch = 0.014
    for zc_, dz, r in ((zb, 1, 0.0042), (zb, 2, 0.0026), (zt, -1, 0.0042), (zt, -2, 0.0026)):
        z = zc_ + dz * pitch * 0.62
        n = int((2 * (hw - FRIT_SIDE)) / pitch)
        for i in range(n):
            x = -(hw - FRIT_SIDE) + (i + 0.5 + 0.5 * (abs(dz) % 2 == 0)) * pitch
            if abs(x) > hw - FRIT_SIDE:
                continue
            vs = [bm.verts.new(V(x + r * math.cos(a), gy(x, z + r * math.sin(a)), z + r * math.sin(a)))
                  for a in (2 * math.pi * k / 6 for k in range(6))]
            bm.faces.new(vs)
    dots = G.finish("ws_frit_dots", bm, "frit", smooth=False, recalc=False)
    dots["fixed_uv"] = True


# ---------------------------------------------------------------- dashboard
def dash_face_y(x):
    # plan shape of the dash face: driver zone deep for knees, centre stack proud, passenger tray
    return lerp_tab([(-XI, 1.12), (-1.02, 1.08), (-0.86, 1.045), (-0.30, 1.045), (-0.16, 0.985), (0.22, 0.985),
                     (0.36, 1.00), (0.95, 1.00), (1.06, 1.06), (XI, 1.12)], x)


def dash_top_z_base(x):
    return lerp_tab([(-XI, 2.10), (-0.9, 2.085), (-0.78, 2.075), (-0.32, 2.075), (-0.2, 2.10), (0.3, 2.12),
                     (0.95, 2.12), (XI, 2.10)], x)


# Cluster tub (A6, critic #4): the dash top dips under the binnacle hood so that the 12.3" screen sits inside the
# upper steering-wheel window seen from the eye point (sightline_test.py proves it). The hood cheeks hide the step.
CLUSTER_W, CLUSTER_H = 0.292, 0.1123            # 12.3 in class screen (WORKING_VALUE)
CLUSTER_C = V(-0.55, 1.178, 2.083)              # screen centre: bottom ~2.027, top ~2.139 (tuned by sightline test)
TUB_DIP, TUB_HW, TUB_FADE = 0.058, 0.170, 0.300


def tub_dip(x):
    return TUB_DIP * (1.0 - smooth(TUB_HW, TUB_FADE, abs(x - CLUSTER_C.x)))


def dash_top_z(x):
    return dash_top_z_base(x) - tub_dip(x)


def knee(x):
    """(y, z) of the lower knee-bolster edge; passenger side open footwell, driver side knee panel."""
    y = lerp_tab([(-XI, 1.20), (-0.85, 1.12), (-0.30, 1.12), (-0.16, 1.02), (0.22, 1.02), (0.36, 1.18), (XI, 1.20)], x)
    z = lerp_tab([(-XI, 1.78), (-0.85, 1.76), (-0.30, 1.76), (-0.16, 1.55), (0.22, 1.55), (0.36, 1.74), (XI, 1.74)], x)
    return y, z


def dash_profile(x, n=44):
    fy, tz, (ky, kz) = dash_face_y(x), dash_top_z(x), knee(x)
    wsb = ws_y(WS_Z0)
    vis = [(wsb - 0.005, WS_Z0 - 0.012), (wsb - 0.10, tz - 0.012), (fy + 0.16, tz), (fy + 0.05, tz - 0.004),
           (fy + 0.008, tz - 0.035), (fy, tz - 0.09), (fy + 0.004, tz - 0.20),
           (min(ky, fy + 0.06) - 0.01, kz + 0.10), (ky, kz), (ky + 0.08, kz - 0.06), (FRONT_WALL_Y - 0.03, kz - 0.10)]
    vis = G.polyline_smooth(vis, 5)
    back = [(FRONT_WALL_Y - 0.03, kz - 0.14), (FRONT_WALL_Y - 0.03, WS_Z0 - 0.05), (wsb - 0.005, WS_Z0 - 0.04)]
    pts = G.resample(vis, n - 3) + back
    return [V(x, y, z) for y, z in pts]


def build_dash():
    group("dash")
    nd = G.Q(46, 20)
    xs = [lerp_tab([(0, -XI + 0.005), (1, XI - 0.005)], i / nd) for i in range(nd + 1)]
    loops = [dash_profile(x) for x in xs]

    # material split at a fixed profile index (uniform arc-length resampling -> clean, continuous parting line)
    ref = dash_profile(0.6)
    # B2: the profile now starts at the lower glass edge (1.93 m, below the parting height), so search on the face side
    i_top = min(range(len(ref)), key=lambda i: abs(ref[i].y - (dash_face_y(0.6) + 0.05)))
    split = next(i for i, p in enumerate(ref) if i > i_top and p.z < dash_top_z(0.6) - 0.075)

    def mat_seg(i, li):  # 0 = soft top (dark, anti-reflection), 1 = lower dash (warm grey)
        return 0 if i < split else 1

    d = loft("dash_main", loops, ["dash_soft", "dash_lower"], closed=True, cap0=True, cap1=True, mat_seg=mat_seg, sharp=50)

    # r4 wear (lower moulding only; the soft top has no wear channel): trouser polish where the knees rest left and
    # right of the column, boot scuffs along the kick edge under it, hand rub round the park brake / light switch
    def dash_wear(co):
        if co.y > FRONT_WALL_Y - 0.06:      # back of the loft (hidden)
            return 0.0
        ky, kz = knee(co.x)
        h = co.z - kz                        # height above the knee edge
        knees = (sum(math.exp(-((co.x - kx) / 0.11) ** 2) for kx in (-0.80, -0.36)) * smooth(-0.02, 0.03, h)
                 * (1 - smooth(0.10, 0.24, h)))
        streak = vnoise(co.x * 34.0, co.z * 7.0) * 0.6 + vnoise(co.x * 11.0, co.z * 3.0, 3.0) * 0.4
        kick = (smooth(-1.10, -0.95, co.x) * (1 - smooth(-0.30, -0.18, co.x)) * (1 - smooth(-0.02, 0.05, h))
                * smooth(0.25, 0.7, streak))
        hand = math.exp(-(((co.x + 0.21) / 0.07) ** 2 + ((co.z - 1.90) / 0.06) ** 2))
        hand += 0.7 * math.exp(-(((co.x + 1.02) / 0.06) ** 2 + ((co.z - 1.94) / 0.05) ** 2))
        return 0.75 * knees * (0.55 + 0.45 * vnoise(co.x * 17.0, co.z * 17.0, 1.0)) + 0.9 * kick + 0.5 * hand
    set_wear_w(d, dash_wear)

    # r6b (review r6 C-R2): the soft top was one grey from the glass to the lip. Authored zones, no noise:
    #  - dust band at the windscreen base (the cloth does not reach under the raked glass; thicker in the corners):
    #    paler and matt;
    #  - polish along the front lip where things get handled: right of the binnacle (hand on the way to the stack),
    #    the passenger stretch (boots / forearms on the dash), the door end by the A-pillar. Gloss only: the black
    #    pad keeps its albedo (ADR 0044 r6), flattened grain is slightly darker.
    yg = ws_y(WS_Z0)

    def top_zones(co, nr):
        if co.y > FRONT_WALL_Y - 0.03 or nr.z < 0.35:
            return 0.0, 0.0
        up = smooth(0.35, 0.8, nr.z)
        dust = up * (0.12 + 0.88 * smooth(yg - 0.26, yg - 0.07, co.y) * (0.45 + 0.55 * smooth(0.45, 1.05, abs(co.x))))
        zone = max(math.exp(-((co.x - 0.13) / 0.17) ** 2), 0.9 * math.exp(-((co.x - 0.70) / 0.20) ** 2),
                   0.7 * math.exp(-((co.x + 1.00) / 0.10) ** 2))
        pol = up * (1 - smooth(dash_face_y(co.x) + 0.035, dash_face_y(co.x) + 0.105, co.y)) * (0.25 + 0.75 * zone)
        return dust, pol
    # dust film: tint x up to 1.6 (albedo 0.046 -> ~0.07 at the glass in the corners; a film on the pad, not wear of the
    # black part), polish: tint x 0.88, roughness -0.42 (WORKING_VALUE, read in cab-dash at 1024 px)
    set_attr_w(d, "tint_add", lambda co, nr: (lambda dp: 0.60 * dp[0] * (1 - dp[1]) - 0.12 * dp[1])(top_zones(co, nr)))
    set_attr_w(d, "rough_add", lambda co, nr: (lambda dp: 0.10 * dp[0] * (1 - dp[1]) - 0.42 * dp[1])(top_zones(co, nr)))
    # parting line between the two mouldings
    pts = [lp[split] + V(0, -0.0015, 0) for lp in loops[1:-1]]
    strip("dash_parting", pts, V(0, -1, 0.2).normalized(), 0.003, "gap", offset=0.0005)
    # B2.1 (owner sheets): padded koniak leather band across the passenger dash face, from the stack flank to the
    # end vent, crowned 8 mm, stitched top and bottom (twin needle line 6 mm in from each edge)
    def face_at(x, z):
        """y of the dash face at (x, z): front part of the lofted profile (between the top lip and the knee)."""
        tz = dash_top_z(x)
        pr = sorted((p.z, p.y) for p in dash_profile(x)[:34] if tz - 0.30 < p.z < tz - 0.004 and
                    p.y < dash_face_y(x) + 0.06)
        return lerp_tab(pr, z)

    nl = G.Q(30, 10)
    xs_l = [0.345 + (0.955 - 0.345) * i / nl for i in range(nl + 1)]
    band = [(-0.026, 0.002), (-0.034, 0.007), (-0.060, 0.011), (-0.100, 0.012), (-0.140, 0.011), (-0.162, 0.007),
            (-0.170, 0.002)]
    lps = []
    for x in xs_l:
        tz = dash_top_z(x)
        end = smooth(0.0, 0.02, min(x - 0.345, 0.955 - x))           # rounded ends: lift fades to the face
        lp = [V(x, face_at(x, tz + dz) - lift * (0.35 + 0.65 * end), tz + dz) for dz, lift in band]
        lp += [V(x, face_at(x, tz - 0.170) + 0.012, tz - 0.170), V(x, face_at(x, tz - 0.026) + 0.012, tz - 0.026)]
        lps.append(lp)
    loft("dash_insert", lps, "leather_trim", closed=True, cap0=True, cap1=True, sharp=70)
    for k, dz in enumerate((-0.033, -0.163)):
        pts = [V(x, face_at(x, dash_top_z(x) + dz) - 0.0068, dash_top_z(x) + dz) for x in xs_l[1:-1]]
        strip(f"dash_insert_stitch_{k}", pts, V(0, -1, 0.15).normalized(), 0.005, "stitch", offset=0.0004,
              u_len=0.017)
    # ---- passenger dash (A6, critic #12): open tray with a ribbed rubber mat and a raised lip on the dash top,
    # document clip on the face, speaker grille in the corner, cup holder by the stack, parting lines that break
    # the slab into real mouldings (insert band, upper glovebox lid, lower glovebox)
    def drape(x, y, lift):
        return V(x, y, dash_surface_z(x, y) + lift)

    # r6b C-R2: the soft pad is a wrapped skin, not a moulding: twin-needle seam 38 mm behind the front lip, from the
    # binnacle to the passenger end and on the short stretch by the driver door
    for k, (xa, xb) in enumerate(((CLUSTER_C.x + TUB_FADE + 0.03, 1.08), (-1.08, CLUSTER_C.x - TUB_FADE - 0.03))):
        nseam = max(4, int(round((xb - xa) / (0.022 / max(0.35, G.STATE["q"])))))
        pts, nrs = [], []
        for i in range(nseam + 1):
            x = xa + (xb - xa) * i / nseam
            y = dash_face_y(x) + 0.038
            pts.append(drape(x, y, 0.0))
            nrs.append(V(0, -(dash_surface_z(x, y + 0.004) - dash_surface_z(x, y - 0.004)) / 0.008, 1).normalized())
        strip(f"dash_top_stitch_{k}", pts, nrs, 0.006, "stitch_dark", offset=0.0005, u_len=0.017)
    for ti, (tx0, tx1) in enumerate(((0.00, 0.38), (0.44, 0.90))):    # centre tray + passenger tray
        ty0, ty1 = dash_face_y(0.6) + 0.085, dash_face_y(0.6) + 0.245
        nmx, nmy = G.Q(12, 5), G.Q(6, 3)
        bm = bmesh.new()
        uvl = bm.loops.layers.uv.new("UVMap")
        grid = [[bm.verts.new(drape(tx0 + (tx1 - tx0) * i / nmx, ty0 + (ty1 - ty0) * j / nmy, 0.0015))
                 for j in range(nmy + 1)] for i in range(nmx + 1)]
        for i in range(nmx):
            for j in range(nmy):
                bm.faces.new((grid[i][j], grid[i + 1][j], grid[i + 1][j + 1], grid[i][j + 1]))
        G.finish(f"dash_tray_mat_{ti}", bm, "floor_mat", smooth=True, sharp=None)
        lip = []
        for (x, y) in ([(tx0 + (tx1 - tx0) * i / 10, ty0) for i in range(11)] + [(tx1, ty0 + (ty1 - ty0) * j / 4) for j in range(1, 5)] +
                       [(tx1 - (tx1 - tx0) * i / 10, ty1) for i in range(1, 11)] + [(tx0, ty1 - (ty1 - ty0) * j / 4) for j in range(1, 5)]):
            lip.append(drape(x, y, 0.004))
        tube(f"dash_tray_lip_{ti}", lip, 0.0055, "dash_mid", seg=8)
    # speaker grille in the passenger corner of the dash top
    sx0, sx1, sy0, sy1 = 0.93, 1.07, dash_face_y(1.0) + 0.09, dash_face_y(1.0) + 0.20
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    vs = [bm.verts.new(drape(x, y, 0.0012)) for x, y in ((sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1))]
    f = bm.faces.new(vs)
    for lp, t in zip(f.loops, ((0, 0), (2.8, 0), (2.8, 1.0), (0, 1.0))):
        lp[uvl].uv = t
    gob = G.finish("dash_spk_grille", bm, "grille_dash", smooth=False, recalc=False)
    gob["fixed_uv"] = True
    tube("dash_spk_rim", [drape(x, y, 0.002) for x, y in ((sx0, sy0), (sx1, sy0), (sx1, sy1), (sx0, sy1), (sx0, sy0))],
         0.003, "dash_dark", seg=6, cap=False)
    # (B2.1: the r3 document clip sat on the leather band; the band takes its place, as in the owner sheets)
    # parting line between the insert band and the glovebox panel (breaks the slab into real mouldings)
    pts = []
    for i in range(25):
        xx = 0.30 + 0.76 * i / 24
        prof = dash_profile(xx)
        best = min(prof[:40], key=lambda p: abs(p.z - 1.955))
        pts.append(V(xx, best.y - 0.0015, 1.955))
    strip("pdash_parting", pts, V(0, -1, 0), 0.003, "gap", offset=0.0)
    # cup holder (fold-out ring) and USB-C pair by the centre stack
    x = 0.33
    cyl("cup_p_ring", (x, dash_face_y(x) - 0.045, 1.88), 0.042, 0.010, "satin", seg=32, bev=0.002)
    cyl("cup_p_well", (x, dash_face_y(x) - 0.045, 1.876), 0.037, 0.012, "gap", seg=24)
    box("cup_p_arm", (x, dash_face_y(x) - 0.012, 1.88), (0.03, 0.03, 0.008), "dash_dark", bev=0.002)
    for k in range(2):
        box(f"usb_p_{k}", (0.42 + k * 0.022, dash_face_y(0.42) - 0.002, 1.895), (0.010, 0.004, 0.0045), "gap")
    # glovebox shut-lines on the lower passenger dash
    for (a, b) in (((0.42, 1.68), (1.00, 1.68)), ((0.42, 1.68), (0.42, 1.92)), ((1.00, 1.68), (1.00, 1.92)),
                   ((0.42, 1.92), (1.00, 1.92))):
        pts = []
        for i in range(9):
            t = i / 8
            x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            prof = dash_profile(x)
            best = min(prof[:40], key=lambda p: abs(p.z - z))
            pts.append(V(x, best.y - 0.0015, z))
        strip(f"glove_gap_{a}{b}", pts, V(0, -1, 0), 0.003, "gap", offset=0.0)
    # glovebox handle
    box("glove_handle", (0.71, dash_face_y(0.71) + 0.004, 1.90), (0.12, 0.02, 0.025), "satin", bev=0.006)
    # defroster grille along the windscreen base
    for side in (-1, 1):  # two long demister grilles: dark recess + punched grille decal, following the dash top
        xa, xb = sorted((side * 0.10, side * 0.98))
        y = ws_y(WS_Z0) - 0.07
        n_t = 8
        for k in range(n_t):
            xc = xa + (xb - xa) * (k + 0.5) / n_t
            if abs(xc - CLUSTER_C.x) < TUB_FADE:
                continue  # under the binnacle hood
            z = WS_Z0 - 0.012 + (dash_top_z_base(xc) - WS_Z0) * (0.065 / 0.095)
            box_mm(f"defrost_recess_{side}_{k}", xc - (xb - xa) / n_t / 2, xc + (xb - xa) / n_t / 2, y - 0.017, y + 0.017,
                   z - 0.012, z - 0.0015, "gap")
            plane_uv(f"defrost_grille_{side}_{k}", quad_on(V(xc, y, z + 0.001), V(0, 0, 1), V(0, 1, 0), (xb - xa) / n_t,
                     0.036), "grille_dash", uv=((0, 0), (6, 0), (6, 0.27), (0, 0.27)))
    build_binnacle()
    build_centre_stack()
    build_vents()
    build_dash_switches()


def dash_surface_z(x, y):
    """Height of the dash top skin at (x, y) (interpolated along the lofted dash profile at x)."""
    prof = [(p.y, p.z) for p in dash_profile(x)[:30] if p.z > dash_top_z(x) - 0.05]
    prof.sort()
    return lerp_tab(prof, y)


def build_binnacle():
    """Cluster hood (A6): sits in the dash-top tub, blends into the dash skin with a 3 mm parting seam, same grain.
    The 12.3" screen alone carries every readout (no separate round dials: they were bisected by the rim)."""
    xc = CLUSTER_C.x
    c = CLUSTER_C
    n = (EYE - c).normalized()
    up = V(0, 0, 1)
    vv = n.cross(up.cross(n).normalized()).normalized()          # screen 'up' in its plane
    top = c + vv * CLUSTER_H / 2
    # eye -> screen-top sight line, evaluated at the lip: the lip stays 8 mm above it (whole screen visible)
    y_l = c.y - 0.112
    z_l = EYE.z + (top.z - EYE.z) * (y_l - EYE.y) / (top.y - EYE.y) + 0.008
    yb = c.y + 0.064                                              # back wall of the screen recess
    full, fade = 0.178, 0.285                                     # hood cheeks: full height -> blended into the dash
    prof = [(y_l, z_l), (y_l + 0.002, z_l + 0.012), (y_l + 0.020, z_l + 0.022), (y_l + 0.070, z_l + 0.028),
            (y_l + 0.140, z_l + 0.020), (yb + 0.040, z_l - 0.012), (yb + 0.072, z_l - 0.060)]
    prof = G.polyline_smooth(prof, 3)
    under = [(yb + 0.085, None), (yb + 0.004, None), (yb + 0.004, top.z + 0.030), (y_l + 0.06, z_l + 0.004),
             (y_l + 0.012, z_l + 0.0)]
    nx = G.Q(44, 14)
    loops, cross_f, cross_b = [], [], []
    for i in range(nx + 1):
        x = xc - fade + 2 * fade * i / nx
        a = 1.0 - smooth(full, fade, abs(x - xc))
        base = dash_top_z(x) - 0.012
        lp = []
        for (y, z) in prof + under:
            yy = y + (1 - a) * 0.075 * (1 if y < yb else -0.3)
            zz = base if z is None else base + (z - base) * max(a, 0.0)
            lp.append(V(x, yy, zz))
        loops.append(lp)
    hood = loft("binnacle_hood", loops, "dash_soft", closed=True, cap0=True, cap1=True, sharp=70)
    # parting seam where the hood skin meets the dash skin (3 mm dark groove following the intersection)
    for i, lp in enumerate(loops):
        x = lp[0].x
        outer = lp[:len(prof) + 1]
        hits = []
        for p0, p1 in zip(outer[:-1], outer[1:]):
            d0 = p0.z - dash_surface_z(x, p0.y)
            d1 = p1.z - dash_surface_z(x, p1.y)
            if d0 * d1 < 0:
                t = d0 / (d0 - d1)
                q = p0.lerp(p1, t)
                hits.append(V(x, q.y, dash_surface_z(x, q.y) + 0.0008))
        if len(hits) >= 2:
            cross_f.append((i, hits[0]))
        if hits:
            cross_b.append((i, hits[-1]))
    mid = nx / 2
    seam = ([p for i, p in reversed(cross_f) if i < mid] + [p for i, p in cross_b] +
            [p for i, p in reversed(cross_f) if i > mid])
    if len(seam) > 3:
        strip("binnacle_seam", seam, V(0, 0, 1), 0.003, "gap", offset=0.0)
    # recess back wall + floor behind/under the screen
    box_mm("cluster_backwall", xc - 0.172, xc + 0.172, yb, yb + 0.016, dash_top_z(xc) - 0.02, top.z + 0.03, "dash_dark")
    # cluster screen (12.3 in class) facing the eye point, piano-black bezel, anti-glare cover glass
    plane_uv("cluster_screen", quad_on(c, n, up, CLUSTER_W, CLUSTER_H), "disp_cluster")
    panel("cluster_bezel", rrect(CLUSTER_W + 0.016, CLUSTER_H + 0.014, 0.010, 3), c - n * 0.004, n, up, 0.03, "piano",
          bev=0.0025)
    plane_uv("cluster_glass", quad_on(c, n, up, CLUSTER_W + 0.006, CLUSTER_H + 0.004, off=0.0025), "cover_glass")
    return hood


def build_centre_stack():
    """Centre stack angled ~22 deg towards the driver (wrap-around), tilted back 16 deg. B2.1 layout (owner sheets
    D19/D20, real 2020s cabs): two rectangular vents across the top, the 10.1 in screen (DISPLAY_Infotainment, runtime
    UI), two rows of seven rocker switches with icons (red hazard button in the middle of the top row), a separate
    three-switch air-suspension pack, the climate panel (two knobs, LCD, five keys) and a 12 V socket + USB.
    B2.1: yaw 22 -> 15 deg, tilt 16 -> 10 deg, 32 mm proud: at 22/16 deg the driver-side third and the top band of
    the face sank behind the dash face and the dash-top lip (half the screen and a vent cut off from the seats)."""
    yaw, tilt = math.radians(15), math.radians(10)
    n = V(-math.sin(yaw) * math.cos(tilt), -math.cos(yaw) * math.cos(tilt), math.sin(tilt)).normalized()
    up = V(0, 0, 1)
    c0 = V(0.03, 0.930, 1.845)
    u = up.cross(n).normalized()
    v = n.cross(u).normalized()
    nq = n.to_track_quat("Y", "Z").to_matrix()
    rotm = n.to_track_quat("Z", "Y").to_matrix()

    def at(du, dv, dn=0.0):
        return c0 + u * du + v * dv + n * dn
    # body (dash_mid surround) rising out of the dash, piano-dark face plate
    body = panel("stack_body", rrect(0.46, 0.52, 0.05, 6), c0, n, up, 0.22, "dash_mid", bev=0.012, bseg=3)
    panel("stack_face", rrect(0.43, 0.49, 0.036, 5), at(0, 0, 0.003), n, up, 0.006, "dash_dark", bev=0.002)
    # koniak leather pad on the passenger flank of the stack (owner sheets), stitched along its front edge
    fl = c0 + u * 0.240 - n * 0.095
    panel("stack_flank_leather", rrect(0.17, 0.40, 0.03, 4), fl, u, up, 0.010, "leather_trim", bev=0.004)
    strip("stack_flank_stitch", [fl + n * 0.072 + v * (-0.18 + 0.36 * i / 12) for i in range(13)], u,
          0.005, "stitch", offset=0.0004, u_len=0.017)
    # two rectangular vents at the top of the stack, either side of the screen (the band above v ~0.17 is under the
    # dash-top lip as seen from the seats, so the vents flank the screen instead of sitting over it)
    for k, du in enumerate((-0.171, 0.171)):
        vent_rect(f"vent_stack_{k}", at(du, 0.100, 0.004), n, w=0.060, h=0.118)
    # screen (10.1 in, 225 x 135 mm), with bezel: kept for the runtime navigation UI (DISPLAY_Infotainment)
    # B2.2 (lead: nav canvas corner read as hidden behind the bezel): thin, even 7 mm frame (was 12.5/11.5 mm with a
    # 10 mm deep proud plate whose side walls ate the driver-near edge at 35-40 deg), 4 mm proud of the face, the
    # glass-flush canvas 0.6 mm above the frame lip. Canvas size/UV contract unchanged (225 x 135 mm, 0-1 UV, ADR 0020);
    # sightline_test.py gates the whole canvas + its four corners from the driver head box.
    cs = at(0, 0.098, 0.006)
    bw, bh = 0.225 + 2 * 0.007, 0.135 + 2 * 0.007
    panel("info_bezel", rrect(bw, bh, 0.006, 3), cs + n * 0.0045, n, up, 0.0045, "piano", bev=0.0012)
    plane_uv("info_screen", quad_on(cs, n, up, 0.225, 0.135, off=0.0051), "disp_info")
    # 1 mm shadow gap where the bezel module sits in the stack face (separate part, not a moulded-in frame)
    ring = [cs + n * 0.0002 + u * x + v * y for (x, y) in rrect(bw + 0.0024, bh + 0.0024, 0.0072, 3)]
    strip("info_bezel_gap", ring + ring[:1], n, 0.0016, "gap", offset=0.0)

    # how often a driver presses each key (polish on the pressed half; WORKING_VALUE, judged from fleet cabs)
    USE = {"work_light": 0.75, "mirror_heat": 0.55, "cab_light": 0.65, "diff_lock": 0.35, "axle_lift": 0.5,
           "seat_heat": 0.6, "fog_rear": 0.3, "beacon": 0.45, "idle_up": 0.2, "plus": 0.55, "res": 0.4, "minus": 0.55,
           "blank": 0.0}

    def module(name, du, dv, w, h, icon, kind="rocker", tip=0, led=False):
        p = at(du, dv, 0.006)
        if kind == "rocker":
            nt = (Matrix.Rotation(math.radians(5 * tip), 3, u) @ n).normalized()
            sw = panel(name, rrect(w, h, 0.0035, 2), p + n * 0.013, nt, up, 0.013, "switch", bev=0.002)
            use = USE.get(icon, 0.15)
            if use > 0:
                pc = p + n * 0.013 + v * (h * 0.22 * (1 if tip >= 0 else -1))
                set_wear(sw, lambda co, pc=pc, use=use, h=h: use * max(0.0, 1.0 - (co - pc).length / (0.6 * h)) *
                         (0.75 + 0.25 * hash01(co.x * 9, co.y * 9, co.z * 9)))
            ic = quad_on(p + n * 0.0135 + v * (h / 2 - 0.0115 if h > 0.05 else 0.004 if icon != "blank" else 0.0), nt,
                         up, 0.014, 0.014, off=0.0)
        else:   # hazard push button: red, triangle icon
            sw = panel(name, rrect(w, h, 0.005, 2), p + n * 0.012, n, up, 0.012, "hazard_red", bev=0.003)
            ic = quad_on(p, n, up, 0.020, 0.020, off=0.0125)
        if icon != "blank":
            plane_uv(name.replace("rocker_", "rocker_icon_"), ic, "icons", uv=M_ICON(icon))
        if led:
            box(name.replace("rocker_", "rocker_led_"), tuple(p - v * (h / 2 - 0.005) + n * 0.0135),
                (min(0.010, w * 0.35), 0.0018, 0.0022), "led_off", rot=nq)
        return sw
    # two rows of seven 24 mm modules, hazard in the middle of the top row (latching functions carry an LED slit)
    rows = [(-0.012, [("fog_rear", 1, True), ("work_light", -1, True), ("beacon", 1, False), ("hazard", 0, False),
                      ("cab_light", -1, False), ("mirror_heat", 1, True), ("seat_heat", -1, True)]),
            (-0.055, [("diff_lock", 1, True), ("axle_lift", -1, True), ("ptos", 1, True), ("esp_off", -1, False),
                      ("lane_assist", 1, False), ("idle_up", -1, False), ("blank", 0, False)])]
    w, gap, du_c = 0.024, 0.005, -0.050
    widths = 7 * w + 6 * gap
    for r, (dv, mods) in enumerate(rows):
        panel(f"swpack_{r}", rrect(widths + 0.012, 0.042, 0.005, 2), at(du_c, dv, 0.010), n, up, 0.004, "dash_dark",
              bev=0.0015)
        ring = [at(du_c, dv, 0.0062) + u * x + v * y for (x, y) in rrect(widths + 0.0145, 0.0445, 0.006, 2)]
        strip(f"swpack_gap_{r}", ring + ring[:1], n, 0.0014, "gap", offset=0.0)
        for k, (icon, tip, led) in enumerate(mods):
            du = du_c - widths / 2 + w / 2 + k * (w + gap)
            if icon == "hazard":
                module(f"rocker_{r}_{k}", du, dv, 0.030, 0.030, icon, "push")
            else:
                module(f"rocker_{r}_{k}", du, dv, w, 0.032, icon, "rocker", tip, led)
    # air-suspension pack: three tall rockers (raise / ride height / lower) in their own carrier
    dus = [0.150 + (k - 1) * (w + gap) for k in range(3)]
    panel("swpack_susp", rrect(3 * w + 2 * gap + 0.012, 0.086, 0.006, 2), at(0.150, -0.0335, 0.010), n, up, 0.004,
          "dash_dark", bev=0.0015)
    for k, (du, icon) in enumerate(zip(dus, ("plus", "res", "minus"))):
        module(f"rocker_s_{k}", du, -0.0335, w, 0.074, icon, "rocker", (1, 0, -1)[k], led=(k == 1))
    # climate panel: recessed dark plate, two knobs with satin rings, LCD between them, five keys under the LCD
    panel("hvac_plate", rrect(0.40, 0.088, 0.010, 3), at(0, -0.150, 0.008), n, up, 0.004, "dash_dark", bev=0.0015)
    for i, du in enumerate((-0.140, 0.140)):
        p = at(du, -0.150, 0.006)
        cyl(f"hvac_ring_{i}", p + n * 0.006, 0.031, 0.006, "satin", seg=36, bev=0.001, rot=rotm)
        cyl(f"hvac_knob_{i}", p + n * 0.018, 0.025, 0.024, "knob", seg=36, bev=0.003, rot=rotm)
        box(f"hvac_knob_mark_{i}", tuple(p + n * 0.0305 + v * 0.016), (0.002, 0.0012, 0.008), "led_off", rot=nq)
    panel("hvac_lcd_bezel", rrect(0.150, 0.036, 0.004, 2), at(0, -0.132, 0.012), n, up, 0.003, "piano", bev=0.001)
    for k in range(3):       # unlit LCD segments: set temperature left / fan / set temperature right
        box(f"hvac_lcd_seg_{k}", tuple(at(-0.045 + 0.045 * k, -0.132, 0.0152)), (0.022, 0.0006, 0.010), "dash_dark",
            rot=nq)
    for k, ic in enumerate(("ac", "recirc", "defrost", "fan", "eco")):
        p = at(-0.060 + k * 0.030, -0.169, 0.006)
        panel(f"hvac_btn_{k}", rrect(0.026, 0.018, 0.004, 2), p + n * 0.009, n, up, 0.006, "switch", bev=0.0015)
        plane_uv(f"hvac_icon_{k}", quad_on(p, n, up, 0.013, 0.013, off=0.0092), "icons", uv=M_ICON(ic))
    # bottom row: small open cubby (phone), USB-C pair, 12 V socket with a hinged cap
    panel("stack_cubby", rrect(0.150, 0.034, 0.008, 3), at(-0.075, -0.217, 0.0065), n, up, 0.003, "rubber",
          bev=0.001)
    for k in range(2):
        panel(f"usb_s_{k}", rrect(0.010, 0.0045, 0.002, 1), at(0.040 + k * 0.020, -0.217, 0.008), n, up, 0.003, "gap")
    p = at(0.120, -0.217, 0.006)
    cyl("socket_12v_ring", p + n * 0.004, 0.017, 0.008, "satin", seg=28, bev=0.001, rot=rotm)
    cyl("socket_12v", p + n * 0.006, 0.0115, 0.008, "gap", seg=24, rot=rotm)
    box("socket_12v_cap", tuple(p + n * 0.010 + v * 0.019), (0.030, 0.004, 0.010), "dash_dark", bev=0.0015, rot=nq)
    # lower centre: open tray + two cup holders + 24 V socket in the lower dash face
    yt = dash_face_y(0.03)
    box_mm("tray_recess", -0.14, 0.18, yt - 0.01, yt + 0.12, 1.56, 1.585, "rubber")
    for i, x in enumerate((-0.06, 0.08)):
        cyl(f"cup_{i}", (x, yt + 0.05, 1.588), 0.042, 0.004, "gap", seg=24)
        cyl(f"socket_{i}", (x + 0.03, yt - 0.002, 1.64), 0.012, 0.006, "gap", axis="Y", seg=16)
    return body


ICON_NAMES = ["low_beam", "fog_rear", "hazard", "diff_lock", "work_light", "beacon", "esp_off", "axle_lift",
              "ac", "fan", "defrost", "recirc", "seat_heat", "mirror_heat", "cab_light", "sun_blind",
              "lane_assist", "idle_up", "ptos", "horn_air", "tyre", "eco", "hill", "cruise",
              "plus", "minus", "res", "ok", "arrow_l", "arrow_r", "phone", "vol"]


def M_ICON(name):
    i = ICON_NAMES.index(name)
    cx, cy = i % 8, i // 8
    u0, u1 = cx / 8, (cx + 1) / 8
    v1, v0 = 1 - cy / 4, 1 - (cy + 1) / 4
    return ((u0, v0), (u1, v0), (u1, v1), (u0, v1))


def vent_round(name, c, n, r=0.045):
    rotm = n.to_track_quat("Z", "Y").to_matrix()
    cyl(name + "_bezel", c, r + 0.010, 0.016, "satin", seg=32, bev=0.003, rot=rotm)
    cyl(name + "_throat", c + n * 0.003, r, 0.03, "gap", seg=32, rot=rotm)
    for k in range(-2, 3):  # horizontal vanes
        off = k * r * 0.36
        w = 2 * math.sqrt(max(r * r - off * off, 0)) * 0.96
        u = V(0, 0, 1).cross(n).normalized()
        vv = n.cross(u).normalized()
        box(f"{name}_vane{k}", tuple(c + vv * off + n * 0.006), (w, 0.012, 0.003), "dash_dark",
            rot=n.to_track_quat("Y", "Z").to_matrix() @ Matrix.Rotation(math.pi, 3, "Z"))
    cyl(name + "_hub", c + n * 0.011, 0.010, 0.012, "knob", seg=16, rot=rotm)


def vent_rect(name, c, n, w=0.11, h=0.05):
    up = V(0, 0, 1)
    panel(name + "_bezel", rrect(w + 0.014, h + 0.014, 0.008, 3), c + n * 0.006, n, up, 0.012, "satin", bev=0.002)
    panel(name + "_throat", rrect(w, h, 0.005, 2), c + n * 0.0065, n, up, 0.03, "gap")
    u = up.cross(n).normalized()
    v = n.cross(u).normalized()
    nv = max(4, int(round(h / 0.0095)))
    for k in range(nv):
        p = c + v * (-h / 2 + h * (k + 0.5) / nv) + n * 0.002
        panel(f"{name}_vane{k}", rrect(w - 0.004, 0.003, 0.0012, 1), p, (n * 0.9 + v * -0.4).normalized(), up, 0.016,
              "dash_dark")
    for k in range(-2, 3):      # rear vertical vanes (B2.1)
        panel(f"{name}_vvane{k}", rrect(0.0025, h - 0.006, 0.001, 1), c + u * (k * w / 5.2) - n * 0.012, n, up, 0.014,
              "gap")
    box(f"{name}_tab", tuple(c + n * 0.008), (0.012, 0.010, 0.02), "knob", bev=0.002)


def build_vents():
    # B2.1 (owner sheets): rectangular vents at both dash ends (side-window demist / face), satin surrounds; the
    # passenger face vent of r3 went (the leather band runs there)
    for s in (-1, 1):
        x = s * 1.035
        c = V(x, dash_face_y(x) - 0.004, dash_top_z(x) - 0.088)
        vent_rect(f"vent_end_{s}", c, V(0.25 * -s, -1, 0.12).normalized(), w=0.088, h=0.072)


def build_dash_switches():
    # light-switch rotary + mirror adjust pad left of the wheel, on the dash face
    x = -0.95
    c = V(x, dash_face_y(x) - 0.004, 1.94)
    n = V(0.15, -1, 0.1).normalized()
    rotm = n.to_track_quat("Z", "Y").to_matrix()
    cyl("light_rotary_base", c, 0.034, 0.008, "dash_dark", seg=32, bev=0.002, rot=rotm)
    lr = cyl("light_rotary", c + n * 0.014, 0.026, 0.02, "knob", seg=32, bev=0.003, rot=rotm)
    lc = c + n * 0.014
    # r4 wear: thumb / forefinger pinch on the upper right of the rim of the rotary
    set_wear_w(lr, lambda co: 0.6 * smooth(0.012, 0.024, ((co - lc) - n * (co - lc).dot(n)).length)
               * smooth(-0.6, 0.5, (co - lc).normalized().dot(V(0.6, 0, 0.8).normalized())))
    plane_uv("light_icon", quad_on(c + V(0, 0, 0.048), n, V(0, 0, 1), 0.018, 0.018, off=0.0), "icons",
             uv=M_ICON("low_beam"))
    p = V(-0.80, dash_face_y(-0.80) - 0.006, 1.90)
    panel("mirror_pad", rrect(0.06, 0.06, 0.012, 3), p, n, V(0, 0, 1), 0.012, "switch", bev=0.003)
    # parking brake: pneumatic hand-control valve lever right of the binnacle (EU trucks)
    x = -0.205
    p = V(x, dash_face_y(x) - 0.004, 1.90)
    panel("pbrake_gate", rrect(0.06, 0.12, 0.012, 3), p, V(-0.2, -1, 0.1).normalized(), V(0, 0, 1), 0.012, "dash_dark",
          bev=0.003)
    rod("pbrake_lever", p + V(0, -0.005, -0.03), p + V(-0.005, -0.075, 0.035), 0.0065, "metal_dark", seg=12)
    kn = G.sphere("pbrake_knob", p + V(-0.006, -0.083, 0.043), 0.016, "knob", scale=(1, 1.3, 0.9))
    kc = p + V(-0.006, -0.083, 0.043)
    # r4 wear: palm side (towards the driver, top) polished to a shine, the underside keeps the moulding texture
    set_wear_w(kn, lambda co: 0.45 + 0.5 * smooth(-0.3, 0.6, (co - kc).normalized().dot(V(0.1, -0.75, 0.65).normalized())))
    cyl("pbrake_ring", p + V(-0.006, -0.083, 0.030), 0.0125, 0.006, "yellow", seg=16)
    # engine start/stop button + key slot right of the column
    p = V(-0.30, dash_face_y(-0.30) - 0.006, 1.84)
    cyl("start_btn", p, 0.016, 0.012, "switch", axis="Y", seg=24, bev=0.002)
    cyl("start_ring", p + V(0, 0.002, 0), 0.02, 0.006, "satin", axis="Y", seg=24)
    # lower dash switch strip (diff lock, PTO, axle lift) left lower panel
    for k, ic in enumerate(("ptos", "tyre", "hill", "eco")):
        x = -0.98 + k * 0.045
        y, z = knee(x)
        p = V(x, y - 0.01, z + 0.09)
        panel(f"low_sw_{k}", rrect(0.028, 0.036, 0.004, 2), p, V(0, -1, -0.2).normalized(), V(0, 0, 1), 0.01, "switch",
              bev=0.002)
        plane_uv(f"low_icon_{k}", quad_on(p, V(0, -1, -0.2).normalized(), V(0, 0, 1), 0.016, 0.016, off=0.0005),
                 "icons", uv=M_ICON(ic))


# ---------------------------------------------------------------- steering wheel, column, stalks, pedals
def wheel_frame():
    tilt = math.radians(WHEEL_TILT)
    n = V(0, -math.sin(tilt), math.cos(tilt))          # towards the driver (up/back)
    u = V(1, 0, 0)
    v = n.cross(u).normalized()                         # in-plane "up" (towards 12 o'clock)
    if v.z < 0:
        v = -v
    return n, u, v


SPOKE_ANG = math.radians(-14.0)                 # side spokes dropped below 3/9 o'clock (opens the cluster window)
HUB_DEPTH = -0.026                              # dish: hub moulding datum 26 mm behind the rim plane (WORKING_VALUE)
RIM_SEAM_B = math.pi - 0.62                     # long leather seam: inner side of the section, turned 35 deg to the driver
RIM_XSEAM = (math.radians(54.0), math.radians(126.0))   # cross seams: perforated grip leather below, smooth above


def hub_outline(scale=1.0, n=48):
    """Airbag-cover plan shape: rounded trapezoid, 172 mm wide at the top, 124 mm at the bottom, 112 mm tall
    (2-D, wheel plane: x = u, y = v). WORKING_VALUE (class: driver airbag module covers ~170-190 x 110-130 mm)."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        x, y = math.cos(a), math.sin(a)
        r = (abs(x) ** 3.4 + abs(y) ** 3.4) ** (-1 / 3.4)       # superellipse: flat sides, crisp shoulders
        yn = y * r
        w = 0.074 + 0.012 * yn                                  # slanted flanks: wider towards 12 o'clock
        h = 0.058 if y > 0 else 0.054
        pts.append((x * r * w * scale, yn * h * scale - 0.002))
    return pts


def _dsec(w, tf, tb, crown=0.0015, rf=0.005, nf=3, nb=6, e=2.6):
    """Closed spoke section (x across, y towards the driver, CCW): crowned front face at y = tf with rf edge radii,
    back = half super-ellipse of depth tb (moulded shell, not a plank)."""
    hw = w / 2
    rf = min(rf, hw * 0.45, tf * 0.95)
    pts = []
    for i in range(nf + 1):
        a = 0.5 * math.pi * i / nf
        pts.append((hw - rf + rf * math.cos(a), tf - rf + rf * math.sin(a)))
    pts += [(0.5 * (hw - rf), tf + 0.75 * crown), (0.0, tf + crown), (-0.5 * (hw - rf), tf + 0.75 * crown)]
    for i in range(nf + 1):
        a = 0.5 * math.pi * (1 + i / nf)
        pts.append((-hw + rf + rf * math.cos(a), tf - rf + rf * math.sin(a)))
    for j in range(nb + 1):
        a = math.pi + math.pi * j / nb
        c, s = math.cos(a), math.sin(a)
        pts.append((hw * math.copysign(abs(c) ** (2 / e), c), -tb * abs(s) ** (2 / e)))
    return pts


def _ribbon(name, rows, mat, u_len, outward):
    """Decal ribbon through parallel point rows (stitching across a seam): U = arc length of the middle row / u_len,
    V = 0..1 across the rows. `outward` = a vector on the visible side of the first face."""
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    R = [[bm.verts.new(p) for p in row] for row in rows]
    mid = rows[len(rows) // 2]
    s = [0.0]
    for i in range(1, len(mid)):
        s.append(s[-1] + (mid[i] - mid[i - 1]).length)
    nv = len(rows) - 1
    flip = (mid[1] - mid[0]).cross(rows[1][0] - rows[0][0]).dot(outward) < 0
    for k in range(nv):
        for i in range(len(mid) - 1):
            vs = [R[k][i], R[k][i + 1], R[k + 1][i + 1], R[k + 1][i]]
            uv = [(s[i] / u_len, k / nv), (s[i + 1] / u_len, k / nv), (s[i + 1] / u_len, (k + 1) / nv),
                  (s[i] / u_len, (k + 1) / nv)]
            if flip:
                vs.reverse()
                uv.reverse()
            f = bm.faces.new(vs)
            for lp, t in zip(f.loops, uv):
                lp[uvl].uv = t
    ob = G.finish(name, bm, mat, smooth=True, sharp=None, recalc=False)
    ob["decal"] = True
    return ob


def build_wheel(badge):
    """Truck steering wheel, r8 (hero part of cab-dash / cab-driver). Four spokes, rim centre line 470 mm / 499 mm over
    the leather (WORKING_VALUE; heavy-truck wheels are 450-500 mm). Rim: oval section 35 x 29 mm, fuller grip zones
    with finger ridges at the back, thumb rests above the side spokes (3 / 9 o'clock), a real seam groove along the
    inner side with two rows of contrasting thread, cross seams at 10:45 / 1:15 that end the perforated grip leather.
    Spokes: moulded D-sections that rise from the dished hub and flare into the rim; the side spokes carry the switch
    pods (gloss bezel, concave +/- rocker towards the thumb, four keys, generic pictograms), the lower pair keeps the
    satin inlays (owner sheets B2.1). Hub: bowl-shaped back shell, bezel, 1.5 mm parting gap, low crowned airbag
    cover with the TRAKT wordmark embossed tone-on-tone. Column: two-shell shroud with a wider combination-switch
    housing, rubber gaiters, flattened stalks. Everything that turns is parented to the STEERING_WHEEL pivot at
    export (A6); the pivot (WHEEL_C, wheel_frame) is unchanged. Detail scales with G.STATE['q'] (LOD0 / 1 / 2)."""
    group("wheel")
    n, u, v = wheel_frame()
    C = WHEEL_C
    hi = G.STATE["q"] >= 0.75          # LOD0
    mid = G.STATE["q"] >= 0.40         # LOD0 + LOD1

    def adiff(a, b):
        return math.atan2(math.sin(a - b), math.cos(a - b))

    # ---- rim -------------------------------------------------------------------------------------------------
    thumb = [SPOKE_ANG + math.radians(19), math.pi - SPOKE_ANG - math.radians(19)]

    def side_x(a):
        """Angle above the 3 o'clock (right) or 9 o'clock (left) position, whichever side `a` is on (rad)."""
        return adiff(a, 0.0) if math.cos(a) >= 0 else adiff(math.pi, a)

    def grip_zone(a):
        x = side_x(a)
        return smooth(-0.14, 0.06, x) * (1 - smooth(0.80, 0.94, x))

    def rim_frame(a):
        return u * math.cos(a) + v * math.sin(a)

    def rim_off(a, b, groove=True):
        """Section offset (radial, towards the driver) at wheel angle a, section angle b."""
        cb, sb = math.cos(b), math.sin(b)
        th = sum(math.exp(-(adiff(a, t) / 0.17) ** 2) for t in thumb)
        gz = grip_zone(a)
        rad = RIM_R[1] * (1.0 + 0.10 * gz + (0.10 + 0.62 * th) * max(0.0, -cb))   # fuller inner side, thumb pads
        dep = RIM_R[0] * (1.0 + 0.08 * gz - 0.10 * max(0.0, sb) - 0.10 * th * max(0.0, sb) * max(0.0, -cb))
        if sb < 0:      # finger ridges at the back of the grip zones
            dep += 0.0024 * (0.5 + 0.5 * math.cos(11 * side_x(a) / 0.94 * math.pi)) * gz * (-sb)
        k = 1.0
        if groove and hi:
            k -= 0.065 * math.exp(-(adiff(b, RIM_SEAM_B) / 0.075) ** 2)
            k -= 0.045 * sum(math.exp(-(adiff(a, s) / 0.011) ** 2) for s in RIM_XSEAM)
        return cb * rad * k, sb * dep * k

    def rim_pt(a, b, groove=True, off=0.0):
        r, z = rim_off(a, b, groove)
        radial = rim_frame(a)
        p = C + radial * (WHEEL_R + r) + n * z
        if off:
            cb, sb = math.cos(b), math.sin(b)
            p += (radial * (cb * RIM_R[0]) + n * (sb * RIM_R[1])).normalized() * off
        return p

    if hi:
        N = 128
        A = [2 * math.pi * i / N for i in range(N)]
        for s in RIM_XSEAM:
            A = [a for a in A if abs(adiff(a, s)) > 0.040] + [s + d for d in (-0.030, -0.012, 0.0, 0.012, 0.030)]
        A.sort()
        B = [2 * math.pi * k / 18 for k in range(18)]
        B = sorted([b for b in B if abs(adiff(b, RIM_SEAM_B)) > 0.24] +
                   [RIM_SEAM_B + d for d in (-0.20, -0.09, 0.0, 0.09, 0.20)])
    else:
        N, S = G.Q(96, 40), G.Q(16, 8)
        A = [2 * math.pi * i / N for i in range(N)]
        B = [2 * math.pi * k / S for k in range(S)]
    loops = [[rim_pt(a, b) for b in B] for a in A]
    loops.append(loops[0])

    def perf_seg(i, li):
        x = side_x(0.5 * (A[li] + A[(li + 1) % len(A)]) if li + 1 < len(A) else A[li] + 0.01)
        return 1 if -0.03 < x < RIM_XSEAM[0] else 0
    rim = loft("wheel_rim", loops, ["leather_wheel", "leather_wheel_perf"], closed=True, sharp=None, mat_seg=perf_seg)

    # r6b (review r6 C-R2): hand patches. Leather polished where the palms sit: 10 and 2 o'clock down to the thumb
    # rests (plateau ~17 cm of rim each, 6 deg soft edge), a lighter one-hand patch at 12; strongest on the face and
    # the outer side of the section (palm), least on the finger side at the back. r8: the thumb rests polish too.
    def rim_wear(co):
        d = co - C
        a = math.atan2(d.dot(v), d.dot(u))
        sb = d.dot(n) / RIM_R[0]
        cb = (math.hypot(d.dot(u), d.dot(v)) - WHEEL_R) / RIM_R[1]

        def patch(a0, half, soft=0.10):
            return 1 - smooth(half, half + soft, abs(math.atan2(math.sin(a - a0), math.cos(a - a0))))
        hands = max(patch(math.radians(148), 0.36), patch(math.radians(32), 0.36))
        sec = 0.30 + 0.70 * smooth(-0.6, 0.5, 0.75 * sb + 0.45 * cb)
        th = max(patch(t, 0.10, 0.08) for t in thumb) * smooth(-0.2, 0.5, sb) * smooth(0.0, 0.8, -cb)
        return max(0.95 * sec * max(hands, 0.45 * patch(math.radians(90), 0.20)), 0.8 * th)
    set_wear(rim, rim_wear)

    # Seam thread. LOD0: every stitch is a small ridge of geometry in an opaque thread material (r8: the alpha-tested
    # decal rows were 1-2 px in cab-dash and vanished in the mips); two rows 3.9 mm either side of the groove,
    # 6.5 mm pitch, 1.6 mm thread (a touch heavier than real 1 mm / 5 mm so the rows survive at phone resolution).
    # LOD1: one decal ribbon over the seam; LOD2: none (a6_export LOD2_DROP 'wheel_stitch').
    def stitch_bar(bm, a0, b0, a1, b1, w=0.0016, h=0.0004):
        p0, p1 = rim_pt(a0, b0, False, 0.00015), rim_pt(a1, b1, False, 0.00015)
        nr = (rim_pt(0.5 * (a0 + a1), 0.5 * (b0 + b1), False, 0.001) -
              rim_pt(0.5 * (a0 + a1), 0.5 * (b0 + b1), False, 0.0)).normalized()
        sd = nr.cross(p1 - p0).normalized() * (w / 2)
        vs = [bm.verts.new(q) for q in (p0 - sd, p1 - sd, p1 + nr * h, p0 + nr * h, p1 + sd, p0 + sd)]
        for f in ((0, 1, 2, 3), (3, 2, 4, 5)):
            face = bm.faces.new([vs[i] for i in f])
            face.normal_update()
            if face.normal.dot(nr) < 0:
                face.normal_flip()

    if hi:
        bm = bmesh.new()
        n_st = 228
        for i in range(n_st):
            a0, a1 = 2 * math.pi * (i + 0.14) / n_st, 2 * math.pi * (i + 0.86) / n_st
            if any(abs(adiff(0.5 * (a0 + a1), s)) < 0.016 for s in RIM_XSEAM):
                continue        # the long rows stop at the cross seams
            for db in (-0.26, 0.26):
                stitch_bar(bm, a0, RIM_SEAM_B + db, a1, RIM_SEAM_B + db)
        for s in RIM_XSEAM:      # cross seams round the section (not over the long seam)
            nb = 13
            for j in range(nb):
                b0 = RIM_SEAM_B + 0.50 + (2 * math.pi - 1.00) * (j + 0.14) / nb
                b1 = RIM_SEAM_B + 0.50 + (2 * math.pi - 1.00) * (j + 0.86) / nb
                for da in (-0.017, 0.017):
                    stitch_bar(bm, s + da, b0, s + da, b1)
        G.finish("wheel_stitch", bm, "thread_wheel", smooth=False, recalc=False)
    elif mid:
        rows = [[], [], [], [], []]
        for i in range(len(A) + 1):
            a = 2 * math.pi * i / len(A)
            for k, db in enumerate((-0.43, -0.20, 0.0, 0.20, 0.43)):
                rows[k].append(rim_pt(a, RIM_SEAM_B + db, False, 0.0007))
        _ribbon("wheel_stitch", rows, "stitch_wheel", 0.026, n - rim_frame(0.0))

    # ---- spokes: moulded D-sections, flat round the hub, rising 12 deg to the rim, flared into it ------------------
    d0 = HUB_DEPTH
    ZF = [(0.045, d0 + 0.0065), (0.095, d0 + 0.0065), (0.110, d0 + 0.0095), (0.200, d0 + 0.0290),
          (0.214, d0 + 0.0320), (0.226, d0 + 0.0345), (0.238, d0 + 0.0360)]            # front face height vs radius
    nf, nb_ = (3, 6) if hi else (2, 4) if mid else (1, 3)

    def spoke(name, ang, stations, wtab, tf, tb, dz=0.0, mat="dash_dark", crown=0.0008, rf=0.005, shift=None):
        radial = u * math.cos(ang) + v * math.sin(ang)
        side = n.cross(radial).normalized()
        if not hi:
            stations = stations[::2] + ([stations[-1]] if len(stations) % 2 == 0 else [])
        secs = []
        for r in stations:
            t_f, t_b = lerp_tab(tf, r), lerp_tab(tb, r)
            pc = C + radial * r + n * (lerp_tab(ZF, r) + dz - t_f)
            if shift:      # the upper edge sweeps up into the thumb rest
                pc += side * lerp_tab(shift, r)
            secs.append([pc + side * px + n * py for px, py in _dsec(lerp_tab(wtab, r), t_f, t_b, crown, rf, nf, nb_)])
        return loft(name, secs, mat, closed=True, cap0=True, cap1=True, sharp=50), radial, side

    pods = {}
    st_side = [0.080, 0.095, 0.110, 0.132, 0.156, 0.180, 0.193, 0.204, 0.214, 0.222, 0.230, 0.238]
    for sgn in (-1, 1):
        ang = SPOKE_ANG if sgn > 0 else math.pi - SPOKE_ANG
        ob, radial, side = spoke(f"spoke_{sgn}", ang, st_side,
                                 [(0.080, 0.094), (0.110, 0.088), (0.180, 0.074), (0.196, 0.064), (0.208, 0.060),
                                  (0.218, 0.064), (0.228, 0.080), (0.238, 0.108)],
                                 [(0.080, 0.0080), (0.200, 0.0080), (0.238, 0.0115)],
                                 [(0.080, 0.0160), (0.200, 0.0125), (0.238, 0.0150)],
                                 shift=[(0.200, 0.0), (0.220, sgn * 0.003), (0.238, sgn * 0.010)])
        pods[sgn] = (radial, side)
    # B2.1 (owner sheets): four-spoke wheel - two slim lower spokes in a V (+-32 deg off 6 o'clock), each with a
    # satin-silver inlay along its face
    st_low = [0.055, 0.080, 0.105, 0.135, 0.165, 0.190, 0.204, 0.214, 0.222, 0.230, 0.238]
    for k, sg in enumerate((-1, 1)):
        ang = -math.pi / 2 + sg * math.radians(32)
        spoke(f"spoke_low_{k}", ang, st_low,
              [(0.055, 0.052), (0.105, 0.040), (0.190, 0.032), (0.210, 0.033), (0.224, 0.044), (0.238, 0.070)],
              [(0.055, 0.0070), (0.200, 0.0070), (0.238, 0.0100)],
              [(0.055, 0.0130), (0.200, 0.0110), (0.238, 0.0130)], dz=-0.0015)
        if mid:
            spoke(f"spoke_trim_low_{k}", ang, [0.088, 0.105, 0.135, 0.165, 0.186, 0.196],
                  [(0.088, 0.0110), (0.196, 0.0090)], [(0.0, 0.0018)], [(0.0, 0.0010)], dz=-0.0015 + 0.0014,
                  mat="satin", crown=0.0003, rf=0.0012)

    # switch pods on the side spokes: gloss bezel on the 12 deg ramp (tilted to the thumb), concave +/- rocker on the
    # rim side, four keys (18 mm pitch, ~1 mm gaps), generic pictograms; satin strip under the bezel (owner sheets)
    r_c = 0.150
    slope = (lerp_tab(ZF, r_c + 0.01) - lerp_tab(ZF, r_c - 0.01)) / 0.02
    for sgn, (radial, side) in pods.items():
        np_ = (n - radial * slope).normalized()                  # pod face normal
        out = (radial + n * slope).normalized()                  # along the spoke towards the rim
        up = side * sgn                                          # across the spoke, towards 12 o'clock
        pc = C + radial * r_c + n * (lerp_tab(ZF, r_c) + 0.0030)

        def at(px, py, pz=0.0, pc=pc, out=out, up=up, np_=np_):
            return pc + out * px + up * py + np_ * pz
        # AO: the bezel buries the spoke face under it, so the pod parts take the occlusion of the open spoke face
        # just inboard of the bezel (a6_export 'ao_probe') instead of the buried point under their centre
        probe = tuple(at(-0.0345, 0.0, -0.0030))

        def pod_panel(*a, probe=probe, **k):
            ob = panel(*a, **k)
            ob["ao_probe"] = probe
            return ob

        def pod_quad(*a, probe=probe, **k):
            ob = plane_uv(*a, **k)
            ob["ao_probe"] = probe
            return ob
        # the gloss bezel keeps the dark occlusion of its recess (black frame round the keys, as moulded)
        panel(f"spoke_pod_{sgn}", rrect(0.060, 0.044, 0.0075, 3), pc, np_, up, 0.0050, "piano", bev=0.0009)
        if not mid:      # LOD2: one key block
            pod_panel(f"spoke_btn_{sgn}", rrect(0.053, 0.0372, 0.004, 1), at(0, 0, 0.0012), np_, up, 0.0016, "switch",
                  bev=0.0)
            continue
        if hi:
            pod_panel(f"spoke_trim_pod_{sgn}", rrect(0.050, 0.0020, 0.0009, 2), at(0.0, -0.0262, -0.0012), np_, up, 0.0030,
                  "satin", bev=0.0004, bseg=1)
        keys = ([["cruise", "res"], ["eco", "hill"]] if sgn < 0 else [["phone", "ok"], ["arrow_l", "arrow_r"]])
        for r in range(2):
            for k in range(2):
                # columns laid out left -> right as the driver sees them; the rocker takes the column next to the rim
                px = -0.018 + k * 0.018 if sgn > 0 else -k * 0.018
                q = at(px, 0.0092 - r * 0.0184, 0.0012)
                kb = pod_panel(f"spoke_btn_{sgn}_{r}_{k}", rrect(0.0170, 0.0174, 0.0030, 2), q, np_, up, 0.0020, "switch",
                           bev=0.0006, bseg=1)
                use = {"cruise": 0.55, "res": 0.5, "ok": 0.6, "phone": 0.35}.get(keys[r][k], 0.2)
                set_wear(kb, lambda co, use=use: use)
                pod_quad(f"spoke_icon_{sgn}_{r}_{k}", quad_on(q, np_, up, 0.0098, 0.0098, off=0.0003), "icons",
                         uv=M_ICON(keys[r][k]))
        for h, lab in ((1, "plus"), (-1, "minus")):      # rocker: two halves tilted 5 deg to a shallow saddle
            nt = (np_ * math.cos(math.radians(5)) - up * (h * math.sin(math.radians(5)))).normalized()
            q = at(0.018, h * 0.0094, 0.0012 + 0.0008)
            kb = pod_panel(f"spoke_btn_{sgn}_rk_{h}", rrect(0.0170, 0.0180, 0.0030, 2), q, nt, up, 0.0026, "switch",
                       bev=0.0006, bseg=1)
            set_wear(kb, lambda co: 0.7)
            pod_quad(f"spoke_icon_{sgn}_rk_{h}", quad_on(q + up * (h * 0.0012), nt, up, 0.0086, 0.0086, off=0.0003),
                     "icons", uv=M_ICON(lab))

    # ---- hub: bowl-shaped back shell + bezel, parting gap, low crowned airbag cover ------------------------------
    def hub_ring(scale, depth):
        return [C + n * depth + u * px + v * py for px, py in hub_outline(scale, G.Q(72, 24))]
    shell = [hub_ring(0.62, d0 - 0.046), hub_ring(1.00, d0 - 0.038), hub_ring(1.17, d0 - 0.016),
             hub_ring(1.195, d0 - 0.002), hub_ring(1.19, d0 + 0.0042), hub_ring(1.16, d0 + 0.0070),
             hub_ring(1.105, d0 + 0.0080), hub_ring(1.047, d0 + 0.0080), hub_ring(1.041, d0 + 0.0020)]
    loft("wheel_hub_shroud", shell, "dash_dark", closed=True, cap0=True, cap1=True, sharp=60)
    cover = [hub_ring(1.019, d0 + 0.0020), hub_ring(1.021, d0 + 0.0100), hub_ring(1.013, d0 + 0.0132),
             hub_ring(0.992, d0 + 0.0152), hub_ring(0.935, d0 + 0.0164), hub_ring(0.60, d0 + 0.0176),
             hub_ring(0.25, d0 + 0.0180)]
    cov = loft("wheel_hub", cover, "dash_soft", closed=True, cap1=True, sharp=80)
    # horn is pressed with the heel of the hand on the lower half of the pad: slight polish
    set_wear(cov, lambda co: 0.35 * smooth(0.035, -0.02, (co - C).dot(v)) * smooth(d0 + 0.010, d0 + 0.016, (co - C).dot(n)))
    # emblem (swappable): TRAKT wordmark embossed tone-on-tone on the cover (graphite satin, 0.6 mm proud)
    emblem(badge, C + n * (d0 + 0.0176), n, v, mat="emboss", rise=0.0002, h=0.0016)

    # ---- column: two-shell shroud (wider combination-switch housing), parting line, gaiters, adjust lever -------
    d = -n
    loops = []
    for t, w, h, rr in ((0.068, 0.118, 0.094, 0.034), (0.078, 0.150, 0.102, 0.036), (0.135, 0.150, 0.108, 0.036),
                        (0.165, 0.130, 0.116, 0.034), (0.320, 0.136, 0.126, 0.032)):
        pc = C + d * t
        loops.append([pc + u * px + v * py for px, py in rrect(w, h, rr, 4)])
    loft("column_shroud", loops, "dash_dark", closed=True, cap0=True, cap1=True)
    for s in (-1, 1):
        pts = [C + d * t + u * (s * w / 2) + v * (-0.010) for t, w in ((0.080, 0.150), (0.135, 0.150), (0.165, 0.130),
                                                                       (0.318, 0.136))]
        strip(f"column_parting_{s}", pts, u * s, 0.0016, "gap", offset=0.0004)
    rod("column_boot", C + d * 0.30, C + d * 0.42, 0.06, "rubber", seg=20)
    box("column_adj_lever", tuple(C + d * 0.205 - u * 0.050 - v * 0.066), (0.016, 0.060, 0.010), "knob", bev=0.003,
        rot=Matrix((u, d, v)).transposed())
    # stalks: left = indicators/wipers, right = retarder (upper) + AMT selector (lower)
    base = C + d * 0.10

    def capsule(name, p0, dirv, st, mat, seg=12):
        e1 = (n - dirv * n.dot(dirv)).normalized()
        e2 = dirv.cross(e1)
        k = G.Q(seg, 8)
        rings = [[p0 + dirv * s + e2 * (a * math.cos(2 * math.pi * i / k)) + e1 * (b * math.sin(2 * math.pi * i / k))
                  for i in range(k)] for s, a, b in st]
        return loft(name, rings, mat, closed=True, cap0=True, cap1=True, sharp=40)

    def stalk(name, side, dz, L, ang_down, knob):
        p0 = base + u * (side * 0.06) + v * dz
        dirv = (u * side * math.cos(math.radians(ang_down)) - v * math.sin(math.radians(ang_down)) + n * 0.15).normalized()
        p1 = p0 + dirv * L
        # flattened arm (thin towards the driver), swelling into the grip
        arm = capsule(name, p0, dirv, [(0.0, 0.0068, 0.0058), (0.035, 0.0070, 0.0052), (L * 0.62, 0.0080, 0.0050),
                                       (L - 0.006, 0.0098, 0.0064), (L, 0.0104, 0.0090)], "knob")
        if knob == "ring":
            end = capsule(name + "_end", p1, dirv, [(0.0, 0.0108, 0.0104), (0.003, 0.0116, 0.0116),
                                                    (0.046, 0.0116, 0.0116), (0.051, 0.0100, 0.0100),
                                                    (0.054, 0.0062, 0.0062)], "knob", seg=16)
            set_wear_w(end, lambda co: 0.6)      # indicator stalk end: used at every junction
            set_wear_w(arm, lambda co: 0.35 * smooth(0.02, L, (co - p0).dot(dirv)))
            if mid:
                capsule(name + "_band", p1 + dirv * 0.012, dirv, [(0.0, 0.0118, 0.0118), (0.0015, 0.0128, 0.0128),
                                                                  (0.0145, 0.0128, 0.0128), (0.016, 0.0118, 0.0118)],
                        "switch", seg=16)
                capsule(name + "_btn", p1 + dirv * 0.053, dirv, [(0.0, 0.0052, 0.0052), (0.0030, 0.0048, 0.0048)],
                        "switch", seg=10)
        elif knob == "amt":
            end = capsule(name + "_end", p1, dirv, [(0.0, 0.0110, 0.0104), (0.003, 0.0130, 0.0130),
                                                    (0.056, 0.0130, 0.0130), (0.061, 0.0112, 0.0112),
                                                    (0.064, 0.0070, 0.0070)], "knob", seg=16)
            # r4 wear: the selector is turned / pushed all day: grip polished, the arm towards it shinier too
            set_wear_w(end, lambda co: 0.85)
            set_wear_w(arm, lambda co: 0.55 * smooth(0.02, L, (co - p0).dot(dirv)))
            if mid:
                capsule(name + "_rot", p1 + dirv * 0.020, dirv, [(0.0, 0.0132, 0.0132), (0.0015, 0.0141, 0.0141),
                                                                 (0.0235, 0.0141, 0.0141), (0.025, 0.0132, 0.0132)],
                        "satin", seg=20)
                capsule(name + "_btn", p1 + dirv * 0.063, dirv, [(0.0, 0.0060, 0.0060), (0.0035, 0.0055, 0.0055)],
                        "switch", seg=10)
        else:   # retarder: flat paddle
            end = capsule(name + "_end", p1, dirv, [(0.0, 0.0106, 0.0090), (0.005, 0.0135, 0.0072),
                                                    (0.030, 0.0142, 0.0070), (0.036, 0.0118, 0.0058),
                                                    (0.0385, 0.0070, 0.0034)], "knob")
            set_wear_w(end, lambda co: 0.7)      # retarder stalk: pulled before every braking
            set_wear_w(arm, lambda co: 0.4 * smooth(0.02, L, (co - p0).dot(dirv)))
        return p1

    stalk("stalk_left", -1, 0.005, 0.15, 8, "ring")
    stalk("stalk_retarder", 1, 0.022, 0.12, -4, "plain")
    stalk("stalk_amt", 1, -0.018, 0.15, 10, "amt")
    # rubber gaiters where the stalks leave the housing
    for s in (-1, 1):
        pc = base + u * (s * 0.0745) + v * 0.004
        rings = []
        for o, w, h in ((0.0, 0.050, 0.060), (0.004, 0.046, 0.056), (0.0065, 0.034, 0.046), (0.0065, 0.026, 0.038)):
            rings.append([pc + u * (s * o) + n * px + v * py for px, py in rrect(w, h, min(w, h) * 0.45, 3)])
        loft(f"stalk_boss_{s}", rings, "rubber", closed=True, cap1=True, sharp=50)


def hub_wordmark(c, n, v, width=0.064, mat="satin", rise=0.0012, h=0.0018):
    """TRAKT wordmark on the hub (owner sheets): monoline letters from art-source/truck/brand/trakt.svg, satin metal,
    raised 1.2 mm, letter-spaced like the grille badge (exterior/body.py wordmark)."""
    path = os.path.join(REPO, "art-source", "truck", "brand", "trakt.svg")
    txt = open(path, encoding="utf-8").read()
    sw = float(re.search(r'stroke-width="([\d.]+)"', txt).group(1))
    strokes = [[tuple(float(t) for t in q.split(",")) for q in pts.split()]
               for pts in re.findall(r'<polyline points="([^"]+)"', txt)]
    bounds = [192, 239, 293, 347, 401, 460]
    spacing = 14.0

    def idx(x):
        return next((i for i, b in enumerate(bounds[1:]) if x < b), len(bounds) - 2)
    allx = [x + idx(min(q[0] for q in pl)) * spacing for pl in strokes for x, _ in pl]
    x0, x1 = min(allx), max(allx)
    ys = [y for pl in strokes for _, y in pl]
    ymid = (min(ys) + max(ys)) / 2
    sc = width / (x1 - x0 + sw)
    u = v.cross(n).normalized()
    for k, pl in enumerate(strokes):
        off = idx(min(q[0] for q in pl)) * spacing
        for j, (a, b) in enumerate(zip(pl, pl[1:])):
            pa = c + u * ((a[0] + off - (x0 + x1) / 2) * sc) + v * (-(a[1] - ymid) * sc)
            pb = c + u * ((b[0] + off - (x0 + x1) / 2) * sc) + v * (-(b[1] - ymid) * sc)
            d = pb - pa
            if d.length < 1e-6:
                continue
            ax = d.normalized()
            m3 = Matrix((ax, n.cross(ax).normalized(), n)).transposed()
            box(f"emblem_wm_{k}_{j}", tuple((pa + pb) / 2 + n * rise), (d.length + sw * sc, sw * sc, h), mat,
                rot=m3)


def emblem(badge, c, n, v, mat="satin", rise=0.0012, h=0.0018):
    if badge == "trakt":
        hub_wordmark(c, n, v, mat=mat, rise=rise, h=h)
        return
    if badge == "none":
        panel("emblem_plate", rrect(0.050, 0.022, 0.008, 3), c + n * 0.002, n, v, 0.003, "metal_dark", bev=0.001)
        return
    path = os.path.join(REPO, "art-source", "truck", "brand", f"{badge}.svg")
    txt = open(path, encoding="utf-8").read()
    g = re.search(r'<g fill="[^"]+" stroke="none">(.*?)</g>', txt, re.S).group(1)
    paths = []  # one entry per <path>: list of closed sub-polygons (even-odd inside a path, union across paths)
    for dstr in re.findall(r'd="([^"]+)"', g):
        polys = []
        for sub in re.split(r"Z", dstr):
            nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", sub)]
            if len(nums) >= 6:
                polys.append([(nums[i], nums[i + 1]) for i in range(0, len(nums), 2)])
        if polys:
            paths.append(polys)
    xs = [p[0] for polys in paths for pl in polys for p in pl]
    ys = [p[1] for polys in paths for pl in polys for p in pl]
    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
    sc = 0.045 / max(max(xs) - min(xs), max(ys) - min(ys))
    u = v.cross(n).normalized()
    bm = bmesh.new()
    for k, polys in enumerate(paths):
        vv = [[(Vector(((x - cx) * sc, -(y - cy) * sc, 0))) for x, y in pl] for pl in polys]
        tris = geometry.tessellate_polygon([[tuple(p) for p in pl] for pl in vv])
        flat = [p for pl in vv for p in pl]
        verts = [bm.verts.new(c + u * p.x + v * p.y + n * (0.002 + 0.0002 * k)) for p in flat]
        for t in tris:
            try:
                bm.faces.new((verts[t[0]], verts[t[1]], verts[t[2]]))
            except ValueError:
                pass
    ob = G.finish("emblem", bm, "satin", smooth=False)
    solidify(ob, 0.0015)


def build_pedals():
    group("pedals")
    # brake: pendant pedal, large pad (truck brake pedal ~ 120 x 90 mm)
    # r7b (ADR 0047): the firewall behind the mask is the floor of the exterior's T pocket (85 mm inside the crowned
    # skin, was a flat 34 mm); arm pivot, accelerator and footrest moved back with it so that fit_to_exterior does
    # not flatten them against it. All three pads now stand 0.74-0.75 m ahead of the H-point (the brake pad did).
    x = SEAT_X + 0.07
    top = BRAKE_PIVOT
    pad = V(x, 1.20, 1.60)
    rod("brake_arm", top, pad + V(0, 0.03, 0.02), 0.012, "metal_dark", seg=10)
    pn = V(0, -1, 0.55).normalized()
    panel("brake_pad", rrect(0.12, 0.095, 0.018, 3), pad, pn, V(0, 0, 1), 0.025, "rubber", bev=0.004)
    # accelerator: floor-hinged organ pedal
    x = SEAT_X + 0.235
    a = math.radians(48)
    p = V(x, ACCEL_HINGE.y + 0.095, 1.415 + 0.13 * math.sin(a))
    pn = V(0, -math.sin(a), math.cos(a))
    panel("accel_pad", rrect(0.085, 0.27, 0.014, 3), p, pn, V(0, 1, 0), 0.022, "rubber", bev=0.004)
    box("accel_hinge", tuple(ACCEL_HINGE), (0.09, 0.03, 0.03), "metal_dark", bev=0.006)
    # driver footrest (dead pedal) left
    x = SEAT_X - 0.23
    panel("footrest", rrect(0.10, 0.22, 0.012, 3), V(x, 1.185, 1.50), V(0, -0.8, 0.6).normalized(), V(0, 1, 1).normalized(),
          0.03, "rubber", bev=0.004)


# ---------------------------------------------------------------- seats
def seat(prefix, cx, driver):
    """Air-suspended truck seat (A6, critic #11): crowned cushion and backrest, rolled side bolsters, sitting creases
    (front of the cushion, bight, lumbar, door-side bolster of the driver seat), separate headrest on two posts,
    integrated belt (webbing, latch plate, shoulder guide), moulded back shell with a pocket, visible damper."""
    group("seats")
    c_w = 0.150              # centre-panel half width
    W2 = 0.268
    yc = HPT.y + 0.12        # cushion centre: cushion spans H-point -145 mm .. +385 mm
    zc = HPT.z - 0.200       # cushion bottom; top of foam ~90 mm above + bolsters
    Mc = Matrix.Translation((cx, yc, zc))
    sgn_door = -1 if driver else 1          # door-side bolster (entry wear, creases)
    ph = 0.37 if driver else 0.81           # crease phase: the two seats are not identical

    def ctop(x, y):
        ax = abs(x)
        u = (y + 0.265) / 0.53
        z = 0.086 + 0.011 * math.sin(math.pi * min(1.0, max(0.0, u))) * (1 - (min(ax, c_w) / c_w) ** 2)  # crown
        if ax > c_w:  # rolled bolster: rises past the seam, round top ~46 mm high, rolling towards the side wall
            b = smooth(c_w + 0.002, c_w + 0.045, ax) * (0.55 + 0.45 * smooth(-0.25, 0.05, y))
            z += 0.046 * b * math.sqrt(max(0.0, 1 - ((ax - (c_w + 0.07)) / 0.115) ** 2)) ** 0.6
        z -= 0.0065 * math.exp(-((ax - c_w) / 0.0055) ** 2)                       # seam groove
        if ax < c_w:
            for ys in (-0.075, 0.075):
                z -= 0.0035 * math.exp(-((y - ys) / 0.005) ** 2)
            # sitting creases: shallow folds along y at the front of the centre panel, and at the bight
            fr = smooth(0.06, 0.17, y) * (1 - smooth(0.20, 0.25, y))
            z -= 0.0016 * fr * (0.5 + 0.5 * math.sin(2 * math.pi * (x / 0.034 + ph) + 3.0 * y))
            bt = 1 - smooth(-0.25, -0.17, y)
            z -= 0.0020 * bt * (0.5 + 0.5 * math.sin(2 * math.pi * (x / 0.041 + 1.7 * ph)))
            z -= 0.012 * bt
        elif x * sgn_door > 0 and driver:
            # entry-side bolster: compression wrinkles across the roll, front half
            w = smooth(-0.05, 0.10, y) * (1 - smooth(0.20, 0.25, y))
            z -= 0.0022 * w * (0.5 + 0.5 * math.sin(2 * math.pi * (y / 0.028 + ph)))
        return z

    def edge(x):
        r = 0.055
        ax = abs(x)
        if ax <= W2 - r:
            return 1.0
        t = (ax - (W2 - r)) / r
        return math.sqrt(max(0.0, 1 - t * t))

    nx_, ny_ = G.Q(64, 22), G.Q(40, 16)
    xs = [-W2 + 2 * W2 * i / nx_ for i in range(nx_ + 1)]
    ys = [-0.265 + 0.53 * j / ny_ for j in range(ny_ + 1)]
    loops = []
    for y in ys:
        drop = 0.0
        if y > 0.175:                     # waterfall front edge, ~90 mm radius
            t = (y - 0.175) / 0.092
            drop = 1 - math.sqrt(max(0.0, 1 - min(t, 0.985) ** 2))
        top = [V(x * (1 - 0.05 * drop), y, max(0.02, (ctop(x, y) * edge(x)) * (1 - drop) + 0.02 * drop)) for x in xs]
        bot = [V(W2 - 0.012, y, 0.0), V(0.0, y, -0.004), V(-W2 + 0.012, y, 0.0)]
        loops.append(top + bot)

    def midx(f):
        cc = f.calc_center_median()
        return 1 if abs(cc.x) < c_w - 0.002 and cc.z > 0.05 else 0

    cush = loft(f"{prefix}_cushion", loops, ["leather", "leather_centre"], closed=True, cap0=True, cap1=True,
                mat_idx=midx, sharp=70)
    cush.matrix_world = Mc
    if driver:  # entry wear on the left (door-side) bolster, front half
        # r6b (C-R2): one shaped patch, no hash / sine pattern: the door-side bolster is rubbed flat and shiny where the
        # driver slides in and out (front two thirds, strongest on the crown and the outer flank), the front edge under
        # the thighs a little
        set_wear(cush, lambda co: 0.9 * smooth(c_w + 0.015, c_w + 0.05, -co.x) * smooth(-0.14, 0.02, co.y)
                 * (1 - 0.35 * smooth(0.22, 0.28, co.y)) + 0.30 * smooth(0.20, 0.27, co.y) * (1 - smooth(c_w, c_w + 0.03, -co.x)))
    # stitch strips along the bolster seams and across the centre panel
    for sx in (-1, 1):
        x = sx * (c_w + 0.011)
        pts, nr = [], []
        for j in range(36):
            y = -0.25 + 0.43 * j / 35
            z = ctop(x, y)
            dzx = (ctop(x + 0.002, y) - ctop(x - 0.002, y)) / 0.004
            dzy = (ctop(x, y + 0.002) - ctop(x, y - 0.002)) / 0.004
            pts.append(V(x, y, z))
            nr.append(V(-dzx, -dzy, 1).normalized())
        sobj = strip(f"{prefix}_cst_{sx}", pts, nr, 0.011, "stitch", offset=0.0012, u_len=0.017)
        sobj.matrix_world = Mc
    for ys_ in (-0.075, 0.075):
        for side in (-1, 1):
            y = ys_ + side * 0.0085
            pts = [V(-c_w + 0.004 + (2 * c_w - 0.008) * i / 24, y, 0) for i in range(25)]
            pts = [V(p.x, p.y, ctop(p.x, p.y) + 0.0004) for p in pts]
            sobj = strip(f"{prefix}_ctr_{ys_}_{side}", pts, V(0, 0, 1), 0.006, "stitch", offset=0.0012, u_len=0.017)
            sobj.matrix_world = Mc

    # ---- backrest (local: x across, y forward = face, z up along the backrest); top at s = SB, headrest above
    rec = math.radians(17)
    Mb = Matrix.Translation((cx, yc - 0.265 - 0.085, zc + 0.05)) @ Matrix.Rotation(rec, 4, "X")
    SB = 0.64
    widths = [(0.0, 0.250), (0.18, 0.258), (0.42, 0.264), (0.56, 0.258), (0.64, 0.250)]

    def cw(s):
        return lerp_tab([(0.0, 0.145), (0.50, 0.145), (0.60, 0.135), (0.7, 0.135)], s)

    def bfront(x, s):
        ax = abs(x)
        y = 0.100 + 0.024 * math.exp(-((s - 0.20) / 0.10) ** 2)                 # lumbar
        y += 0.008 * (1 - (min(ax, cw(s)) / cw(s)) ** 2)                        # crown of the centre panel
        if ax > cw(s):
            roll = smooth(cw(s) + 0.004, cw(s) + 0.05, ax)
            y += ((0.062 - 0.036 * smooth(0.30, 0.58, s)) * roll *
                  math.sqrt(max(0.0, 1 - ((ax - (cw(s) + 0.07)) / 0.12) ** 2)) ** 0.6)
        y -= 0.006 * math.exp(-((ax - cw(s)) / 0.0055) ** 2)
        if ax < cw(s):
            for ss in (0.24, 0.40):
                y -= 0.0045 * math.exp(-((s - ss) / 0.005) ** 2)
            lb = 1 - smooth(0.04, 0.13, s)                                        # creases where the back meets the seat
            y -= 0.0016 * lb * (0.5 + 0.5 * math.sin(2 * math.pi * (s / 0.022 + 0.6 * x / 0.05 + ph)))
        return y

    loops = []
    nS, nX = G.Q(44, 16), G.Q(48, 18)
    S = [SB * k / nS for k in range(nS + 1)]
    for s in S:
        w = lerp_tab(widths, s)
        top_round = 1.0
        if s > SB - 0.055:
            t = (s - (SB - 0.055)) / 0.058
            top_round = math.sqrt(max(0.02, 1 - min(t, 0.99) ** 2))
        front = []
        for i in range(nX + 1):
            xr = -1 + 2 * i / nX
            x = xr * w
            r = 0.055
            e = 1.0 if abs(x) <= w - r else math.sqrt(max(0.0, 1 - ((abs(x) - (w - r)) / r) ** 2))
            front.append(V(x * (0.95 + 0.05 * top_round), (bfront(x, s) * e) * top_round, s))
        back = [V(w - 0.01, -0.012, s), V(0.0, -0.02, s), V(-w + 0.01, -0.012, s)]
        back = [V(p.x * (0.95 + 0.05 * top_round), p.y * top_round, p.z) for p in back]
        loops.append(front + back)

    def bidx(f):
        cc = f.calc_center_median()
        return 1 if abs(cc.x) < cw(cc.z) - 0.002 and cc.y > 0.06 and cc.z < SB - 0.04 else 0

    back = loft(f"{prefix}_backrest", loops, ["leather", "leather_centre"], closed=True, cap0=True, cap1=True,
                mat_idx=bidx, sharp=70)
    back.matrix_world = Mb
    if driver:
        set_wear(back, lambda co: 0.85 * smooth(0.16, 0.22, -co.x) * smooth(0.05, 0.20, co.z) * (1 - smooth(0.45, 0.6, co.z)))
    for sx in (-1, 1):  # vertical stitch lines
        pts, nr = [], []
        for k in range(30):
            s = 0.03 + (SB - 0.10) * k / 29
            x = sx * (cw(s) + 0.011)
            y = bfront(x, s)
            dyx = (bfront(x + 0.002, s) - bfront(x - 0.002, s)) / 0.004
            dys = (bfront(x, s + 0.002) - bfront(x, s - 0.002)) / 0.004
            pts.append(V(x, y, s))
            nr.append(V(-dyx, 1, -dys).normalized())
        sobj = strip(f"{prefix}_bst_{sx}", pts, nr, 0.011, "stitch", offset=0.0012, u_len=0.017)
        sobj.matrix_world = Mb
    for ss in (0.24, 0.40):
        for side in (-1, 1):
            s = ss + side * 0.0085
            pts = [V(-cw(s) + 0.004 + (2 * cw(s) - 0.008) * i / 24, 0, s) for i in range(25)]
            pts = [V(p.x, bfront(p.x, s) + 0.0004, s) for p in pts]
            sobj = strip(f"{prefix}_btr_{ss}_{side}", pts, V(0, 1, 0), 0.006, "stitch", offset=0.0012, u_len=0.017)
            sobj.matrix_world = Mb
    # moulded back shell following the backrest silhouette, with a lower pocket (fabric, elastic top band)
    sh_loops = []
    for s_ in [0.02 + (SB - 0.03) * k / 20 for k in range(21)]:
        w = lerp_tab(widths, s_) - 0.006
        rnd_top = 1.0 if s_ < SB - 0.05 else max(0.30, 1 - (s_ - (SB - 0.05)) / 0.04)
        sh_loops.append([V(px * rnd_top, -0.022 + py, s_) for px, py in rrect(2 * w, 0.034, 0.016, 3, 0, -0.017)])
    bc = loft(f"{prefix}_backcover", sh_loops, "dash_mid", closed=True, cap0=True, cap1=True, sharp=50)
    bc.matrix_world = Mb
    pk_loops = []
    for k in range(9):
        s_ = 0.10 + 0.27 * k / 8
        bulge = 0.010 + 0.012 * math.sin(math.pi * k / 8) ** 0.7
        pk_loops.append([V(-0.19 + 0.38 * i / 16, -0.059 - bulge * (1 - ((-0.19 + 0.38 * i / 16) / 0.19) ** 4), s_)
                         for i in range(17)])
    pk = loft(f"{prefix}_backpocket", list(zip(*pk_loops)), "seat_fabric", closed=False)
    solidify(pk, 0.004)
    pk.matrix_world = Mb
    eb = box(f"{prefix}_pocket_edge", (0, -0.068, 0.372), (0.39, 0.016, 0.022), "webbing", bev=0.006, seg=2)
    eb.matrix_world = Mb
    # ---- separate headrest on two posts (gap 25 mm above the backrest)
    hr_z0, hr_h, hr_w, hr_d = SB + 0.025, 0.170, 0.270, 0.085
    hl = []
    # A6.1 (critic r2 #9: polygon steps on the headrest top against the bright window, seen from the bunk): cosine
    # spacing of the sections (dense where the outline turns down at the ends), more sections, rounder corners, and a
    # superellipse end (the old 1 - t^6 law made a flat 'pill' cap with a shading crease at each end)
    nh = G.Q(30, 12)
    for i in range(nh + 1):
        t = -math.cos(math.pi * i / nh)
        x = t * hr_w / 2
        k = max(0.18, (1 - abs(t) ** 4) ** 0.25)          # superellipse end: rounds off without a crease
        wing = 0.018 * abs(t) ** 3                       # slight forward wings
        hl.append([V(x, 0.045 + wing + py * (0.5 + 0.5 * k), hr_z0 + hr_h / 2 + pz * (0.55 + 0.45 * k))
                   for py, pz in rrect(hr_d, hr_h, 0.038, 6)])
    hrest = loft(f"{prefix}_headrest", hl, "leather", closed=True, cap0=True, cap1=True, sharp=70)
    hrest.matrix_world = Mb
    for hx in (-0.075, 0.075):
        post = rod(f"{prefix}_hr_post_{hx}", (hx, 0.040, SB - 0.04), (hx, 0.042, hr_z0 + 0.04), 0.0055, "satin", seg=12)
        post.matrix_world = Mb
        col = cyl(f"{prefix}_hr_collar_{hx}", (hx, 0.040, SB - 0.004), 0.011, 0.012, "dash_dark", seg=16)
        col.matrix_world = Mb
    # ---- integrated belt: shoulder guide at the top outer corner, webbing down the outer bolster, latch plate
    sx = -1 if driver else 1
    pts = []
    for k in range(16):
        s = SB - 0.035 - (SB - 0.08) * k / 15
        x = sx * (cw(s) + 0.050 - 0.012 * k / 15)
        pts.append(V(x, bfront(x, s) + 0.007, s))
    belt = strip(f"{prefix}_belt", pts, V(0, 1, 0), 0.047, "webbing", offset=0.0, u_len=0.2)
    belt.matrix_world = Mb
    solidify(belt, 0.0016)
    guide = box(f"{prefix}_belt_guide", (sx * (cw(SB) + 0.050), 0.090, SB - 0.022), (0.065, 0.040, 0.030), "dash_dark",
                bev=0.008)
    guide.matrix_world = Mb
    lp_ = pts[-1]
    latch = box(f"{prefix}_belt_latch", (lp_.x, lp_.y + 0.006, lp_.z - 0.02), (0.050, 0.006, 0.060), "satin", bev=0.003)
    latch.matrix_world = Mb
    lpb = box(f"{prefix}_belt_latch_grip", (lp_.x, lp_.y + 0.008, lp_.z + 0.012), (0.054, 0.012, 0.024), "dash_dark",
              bev=0.004)
    lpb.matrix_world = Mb
    # buckle on the inner side
    bx = cx - sx * 0.29
    rod(f"{prefix}_buckle_stalk", (bx, yc - 0.22, zc + 0.02), (bx, yc - 0.20, zc + 0.12), 0.012, "webbing", seg=8)
    box(f"{prefix}_buckle", (bx, yc - 0.20, zc + 0.15), (0.03, 0.022, 0.07), "dash_dark", bev=0.006)
    # gas damper of the air suspension, visible behind the bellows
    rod(f"{prefix}_damper", (cx + 0.12, yc - 0.27, FLOOR + 0.06), (cx - 0.05, yc - 0.25, zc - 0.05), 0.014, "metal_dark",
        seg=12)
    rod(f"{prefix}_damper_rod", (cx - 0.05, yc - 0.25, zc - 0.05), (cx - 0.12, yc - 0.24, zc - 0.035), 0.006, "satin",
        seg=10)
    # side shields (plastic covers over the mechanism) + levers
    for s in (-1, 1):
        box(f"{prefix}_shield_{s}", (cx + s * (W2 + 0.012), yc - 0.02, zc + 0.01), (0.022, 0.46, 0.10), "dash_dark",
                 bev=0.012, seg=3)
    rod(f"{prefix}_lever_h", (cx - (W2 + 0.03), yc + 0.12, zc + 0.02), (cx - (W2 + 0.045), yc + 0.22, zc + 0.0), 0.007,
        "knob", seg=8)
    G.sphere(f"{prefix}_lever_knob", (cx - (W2 + 0.045), yc + 0.225, zc), 0.014, "knob", scale=(0.7, 1.2, 0.8))
    # seat pan + suspension: rubber gaiter (bellows) between pan and base, rails on the floor
    box_mm(f"{prefix}_pan", cx - 0.235, cx + 0.235, yc - 0.25, yc + 0.22, zc - 0.035, zc + 0.005, "metal_dark", bev=0.008)
    ztop, zbot = zc - 0.035, FLOOR + 0.045
    loops = []
    nf = 9
    for k in range(nf * 2 + 1):
        z = ztop + (zbot - ztop) * k / (nf * 2)
        g = 0.0 if k % 2 else 0.018
        loops.append([V(cx + px, yc - 0.02 + py, z) for px, py in rrect(0.40 - g, 0.40 - g, 0.04, 3)])
    loft(f"{prefix}_bellows", loops, "rubber", closed=True, sharp=50)
    box_mm(f"{prefix}_base", cx - 0.22, cx + 0.22, yc - 0.24, yc + 0.20, FLOOR, FLOOR + 0.045, "metal_dark", bev=0.006)
    for s in (-1, 1):
        box_mm(f"{prefix}_rail_{s}", cx + s * 0.17 - 0.02, cx + s * 0.17 + 0.02, yc - 0.33, yc + 0.27, FLOOR, FLOOR + 0.03,
               "satin", bev=0.004)
    # armrest on the inner side, folded down
    ax = cx + (0.30 if driver else -0.30)
    arm_loops = []
    for t in range(9):
        yy = HPT.y - 0.12 + 0.30 * t / 8
        zz = zc + 0.235 + 0.015 * math.sin(math.pi * t / 8)
        arm_loops.append([V(ax + px, yy, zz + py) for px, py in rrect(0.065, 0.06, 0.024, 3)])
    loft(f"{prefix}_armrest", arm_loops, "leather", closed=True, cap0=True, cap1=True, sharp=60)
    box(f"{prefix}_arm_pivot", (ax, HPT.y - 0.13, zc + 0.23), (0.05, 0.05, 0.05), "dash_dark", bev=0.01)


# ---------------------------------------------------------------- doors
def build_doors():
    """Door cards on the r3 aperture from the exterior interface (DOOR_IF_PATH): rear edge -0.56, front edge vertical
    at 0.76 up to z 1.90, then diagonal to the A-pillar. The card outline follows that edge; armrest, switches, pull,
    pocket and speaker stay where the seated driver uses them (the seat did not move) and are clipped to the edge.
    The rear 0.45 m of the card is a plain panel: it closes against the end of the bunk (bunk is inset to clear it)."""
    group("doors")
    for s in (-1, 1):
        xw = s * XI
        y0 = DOOR_Y0 + 0.03
        y1 = lambda z: door_front(z) - 0.02                          # noqa: E731  card front edge at height z
        # main door trim: lower panel (dash_lower), shaped in plan (y,z grid pushed inward); front edge follows the
        # aperture (vertical, then the diagonal towards the A-pillar)
        zs = [FLOOR + 0.05, 1.60, 1.80, 1.93, 2.02, 2.10, WIN_Z0 - 0.01]
        inset = [0.045, 0.050, 0.056, 0.060, 0.064, 0.070, 0.050]   # how far the trim stands proud of the wall
        loops = []
        for yi in range(G.Q(17, 9)):
            t = yi / (G.Q(17, 9) - 1)
            lp = [V(xw - s * d, y0 + (y1(z) - y0) * t, z) for z, d in zip(zs, inset)]
            lp += [V(xw, y0 + (y1(WIN_Z0 - 0.01) - y0) * t, WIN_Z0 - 0.01), V(xw, y0 + (y1(FLOOR + 0.05) - y0) * t, FLOOR + 0.05)]
            loops.append(lp)
        dp = loft(f"door_trim_{s}", loops, "dash_lower", closed=True, cap0=True, cap1=True)
        set_wear_w(dp, lambda co, s=s: (0.8 if s < 0 else 0.45) * (1 - smooth(1.48, 1.72, co.z)) * smooth(-0.10, 0.25, co.y)
                   * smooth(0.2, 0.75, vnoise(co.y * 16.0, co.z * 5.0, 2.0)) * (1.0 if abs(co.x) < XI - 0.01 else 0.0))
        bevel(dp, 0.006, 2, angle=30)
        # sill cap (soft) along the beltline
        loops = []
        for yi in range(13):
            y = y0 + (y1(WIN_Z0 - 0.03) - y0) * yi / 12
            loops.append([V(xw - s * px, y, WIN_Z0 - 0.06 + pz) for px, pz in
                          ((0.0, 0.0), (0.075, 0.0), (0.083, 0.03), (0.07, 0.058), (0.02, 0.066), (0.0, 0.066))])
        loft(f"door_sill_{s}", loops, "dash_soft", closed=True, cap0=True, cap1=True)
        # B2.1 (owner sheets): padded koniak leather panel between armrest and sill (was a 7 cm painted strip),
        # crowned 6 mm, twin stitch lines along its top and bottom edges
        loops = []
        ny = G.Q(12, 5)
        for yi in range(ny + 1):
            y = door_y(0.02 + 0.92 * yi / ny, 2.03, 0.04)
            loops.append([V(xw - s * 0.071, y, 1.992), V(xw - s * 0.077, y, 2.010), V(xw - s * 0.080, y, 2.050),
                          V(xw - s * 0.077, y, 2.092), V(xw - s * 0.071, y, 2.104), V(xw - s * 0.058, y, 2.104),
                          V(xw - s * 0.058, y, 1.992)])
        loft(f"door_insert_{s}", loops, "leather_trim", closed=True, cap0=True, cap1=True, sharp=70)
        for k, (z, d) in enumerate(((1.999, 0.0737), (2.097, 0.0745))):
            pts = [V(xw - s * d, door_y(0.04 + 0.88 * i / 16, z, 0.04), z) for i in range(17)]
            strip(f"door_insert_stitch_{s}_{k}", pts, V(-s, 0, 0), 0.005, "stitch", offset=0.0006, u_len=0.017)
        # armrest with pull cup, window switch pad at the front
        loops = []
        for yi in range(15):
            y = door_y(-0.02 + 0.80 * yi / 14, 1.93, 0.04)
            h = 0.055
            loops.append([V(xw - s * (0.060 + px), y, 1.955 + pz) for px, pz in rrect(0.085, h, 0.022, 3, 0.04, 0)])
        arm = loft(f"door_armrest_{s}", loops, "leather_trim", closed=True, cap0=True, cap1=True, sharp=60)
        # elbow polish on the top: strongest where the forearm lies (driver door), light everywhere else
        set_wear_w(arm, lambda co, s=s: smooth(1.97, 1.982, co.z) * (0.35 + (0.6 if s < 0 else 0.25) *
                   math.exp(-((co.y - 0.50) / 0.17) ** 2)) * (0.75 + 0.25 * vnoise(co.x * 30, co.y * 30)))
        pts = [V(xw - s * 0.1015, door_y(-0.01 + 0.76 * i / 14, 1.93, 0.04), 1.979) for i in range(15)]
        strip(f"door_arm_stitch_{s}", pts, V(-s * 0.4, 0, 1).normalized(), 0.005, "stitch", offset=0.0007,
              u_len=0.017)
        sp = V(xw - s * 0.12, door_y(0.66, 1.93, 0.08), 1.987)
        panel(f"winswitch_pad_{s}", rrect(0.07, 0.11, 0.012, 3), sp, V(0, 0, 1), V(0, 1, 0), 0.008, "piano", bev=0.002)
        for k in range(2):
            box(f"winswitch_{s}_{k}", tuple(sp + V(s * (-0.015 + 0.03 * k) * 0, -0.03 + 0.04 * k, 0.006)),
                (0.026, 0.018, 0.012), "switch", bev=0.003)
        box(f"mirrorswitch_{s}", tuple(sp + V(0, 0.035, 0.006)), (0.03, 0.026, 0.008), "switch", bev=0.003)
        # pull handle (vertical grab) under the armrest front
        pts = [V(xw - s * 0.07, 0.42, 1.93), V(xw - s * 0.125, 0.44, 1.91), V(xw - s * 0.125, 0.62, 1.91),
               V(xw - s * 0.07, 0.64, 1.93)]
        pull = tube(f"door_pull_{s}", G.polyline_smooth(pts, 4), 0.013, "grab_dark", seg=10)
        mw = pull.matrix_world
        set_wear(pull, lambda co, mw=mw: 0.85 * smooth(0.46, 0.50, (mw @ co).y) * (1 - smooth(0.58, 0.62, (mw @ co).y)) *
                 (0.7 + 0.3 * hash01(co.x * 40, co.y * 40, co.z * 40)))
        # interior opener lever (satin) near the front top
        lp = V(xw - s * 0.072, door_y(0.92, 2.06, 0.08), 2.06)
        panel(f"opener_cup_{s}", rrect(0.10, 0.045, 0.015, 3), lp, V(-s, 0, 0), V(0, 0, 1), 0.006, "dash_dark", bev=0.002)
        box(f"opener_lever_{s}", tuple(lp + V(-s * 0.008, -0.01, 0)), (0.012, 0.075, 0.016), "satin", bev=0.005)
        # map pocket with bottle holder
        loops = []
        for yi in range(11):
            y = -0.08 + (door_y(0.85, 1.50, 0.04) + 0.08) * yi / 10      # starts ahead of the bunk end
            loops.append([V(xw - s * px, y, pz) for px, pz in
                          ((0.050, 1.50), (0.105, 1.50), (0.112, 1.66), (0.098, 1.70), (0.088, 1.66), (0.085, 1.54),
                           (0.050, 1.54))])
        pk = loft(f"door_pocket_{s}", loops, "dash_lower", closed=True, cap0=True, cap1=True)
        bevel(pk, 0.004, 2)
        box_mm(f"pocket_mat_{s}", xw - s * 0.052, xw - s * 0.083, -0.07, door_y(0.84, 1.50, 0.05), 1.541, 1.546, "rubber")
        # speaker in the upper front of the door
        c = V(xw - s * 0.058, door_y(0.88, 1.79, 0.12), 1.79)
        cyl(f"door_spk_{s}", c, 0.075, 0.012, "dash_dark", axis="X", seg=40, bev=0.004)
        plane_uv(f"door_spk_grille_{s}", quad_on(c + V(-s * 0.0065, 0, 0), V(-s, 0, 0), V(0, 0, 1), 0.13, 0.13), "grille")
        # door seal around the aperture + scuff plate on the floor sill
        top = WIN_Z1 + 0.05
        front = [V(xw + s * 0.004, y, z) for y, z in reversed(DOOR_IF["door_front_yz"]) if FLOOR < z < top]
        pts = ([V(xw + s * 0.004, DOOR_Y0, FLOOR), V(xw + s * 0.004, DOOR_Y0, top),
                V(xw + s * 0.004, door_front(top), top)] + front + [V(xw + s * 0.004, DOOR_Y1, FLOOR)])
        tube(f"door_seal_{s}", pts, 0.012, "rubber", seg=8, cap=False)
        sp_ = box_mm(f"scuff_{s}", xw - s * 0.06, xw + s * 0.004, DOOR_Y0 + 0.02, DOOR_Y1 - 0.02, FLOOR - 0.004, FLOOR + 0.012,
                     "scuff_plate", bev=0.003)
        set_wear(sp_, lambda co: 0.8 * smooth(0.0, 0.5, co.y) * (1 - smooth(0.7, 1.0, co.y)))


# ---------------------------------------------------------------- floor, bunk, overhead storage, curtains, blinds
def build_floor():
    group("floor")
    m = box_mm("floor_mat", -XI + 0.01, XI - 0.01, -0.12, FRONT_WALL_Y - 0.03, FLOOR - 0.004, FLOOR + 0.006, "floor_mat",
               bev=0.004)
    # B2.2: the mat was 8 vertices, so the heel / entry wear below could not show; give the top a ~6 cm grid
    bm = bmesh.new()
    bm.from_mesh(m.data)
    top = [e for e in bm.edges if all(v.co.z > FLOOR + 0.005 - m.location.z for v in e.verts)]
    bmesh.ops.subdivide_edges(bm, edges=top, cuts=G.Q(36, 12), use_grid_fill=True)
    bm.to_mesh(m.data)
    bm.free()
    # mat is worn in the driver's heel area and the entry path
    set_wear(m, lambda co: 0.9 * math.exp(-(((co.x + 0.48) / 0.10) ** 2 + ((co.y - 1.14) / 0.08) ** 2)) +
             0.5 * math.exp(-(((co.x + 0.95) / 0.20) ** 2 + ((co.y - 0.45) / 0.35) ** 2)))


def build_bunk():
    group("bunk")
    yf = -0.10
    xb = XI - 0.09   # r3: the door aperture now starts at y -0.56, so the bunk ends stand 90 mm clear of the door card
    # base with drawers: left storage, centre fridge drawer, right storage
    box_mm("bunk_base", -xb, xb, YB, yf, FLOOR, 1.86, "dash_lower", bev=0.008)
    for i, (x0, x1) in enumerate(((-1.03, -0.40), (-0.36, 0.36), (0.40, 1.03))):
        box_mm(f"drawer_{i}", x0, x1, yf - 0.012, yf + 0.002, 1.47, 1.80, "dash_lower", bev=0.006)
        box_mm(f"drawer_grip_{i}", (x0 + x1) / 2 - 0.09, (x0 + x1) / 2 + 0.09, yf - 0.024, yf - 0.010, 1.755, 1.775,
               "dash_dark", bev=0.004)
    box_mm("fridge_vent", -0.25, 0.25, yf - 0.013, yf - 0.011, 1.50, 1.53, "gap")
    # mattress: rounded slab, fabric, piping along the top edge
    loops = []
    for i in range(23):
        x = -xb + 0.01 + (2 * xb - 0.02) * i / 22
        loops.append([V(x, y, z) for y, z in
                      ((YB + 0.01, 1.865), (yf - 0.01, 1.865), (yf - 0.005, 1.90), (yf - 0.012, 1.99), (yf - 0.035, 2.005),
                       (YB + 0.03, 2.005), (YB + 0.01, 1.99))])
    loft("mattress", loops, "mattress", closed=True, cap0=True, cap1=True, sharp=70)
    tube("mattress_piping", [V(-xb + 0.02, yf - 0.025, 2.0), V(xb - 0.02, yf - 0.025, 2.0)], 0.004, "mattress", seg=6)
    # pillow + folded blanket (lived-in, tidy)
    loops = []
    for i in range(11):
        t = i / 10
        y = YB + 0.06 + 0.42 * t
        h = 0.065 * math.sin(math.pi * t) ** 0.6 + 0.01
        loops.append([V(-1.02 + px, y, 2.005 + max(0.0, pz + h * 0.5)) for px, pz in rrect(0.30, h, h * 0.45, 3)])
    loft("pillow", loops, "mattress", closed=True, cap0=True, cap1=True)
    box_mm("blanket", 0.45, 0.95, YB + 0.08, YB + 0.48, 2.005, 2.045, "curtain", bev=0.015, seg=3)
    # folded upper bunk against the back wall + straps
    box_mm("upper_bunk", -XI + 0.02, XI - 0.02, YB + 0.002, YB + 0.085, 2.38, 3.08, "wall_fabric", bev=0.02, seg=3)
    for x in (-0.6, 0.6):
        box_mm(f"bunk_strap_{x}", x - 0.02, x + 0.02, YB + 0.085, YB + 0.092, 2.80, 3.12, "webbing")
        box_mm(f"bunk_buckle_{x}", x - 0.025, x + 0.025, YB + 0.088, YB + 0.10, 2.92, 2.96, "metal_dark", bev=0.003)
    # bunk control panel on the driver-side rear wall (climate, alarm, lights)
    c = V(-XI + 0.008, min(YB + 0.45, DOOR_Y0 - 0.11), 2.32)   # on the wall behind the door opening
    panel("bunk_panel", rrect(0.16, 0.10, 0.012, 3), c, V(1, 0, 0), V(0, 0, 1), 0.012, "dash_dark", bev=0.003)
    for k in range(3):
        panel(f"bunk_btn_{k}", rrect(0.03, 0.022, 0.004, 2), c + V(0.004, -0.045 + 0.045 * k, -0.02), V(1, 0, 0),
              V(0, 0, 1), 0.006, "switch", bev=0.0015)
    plane_uv("bunk_lcd", quad_on(c + V(0, 0, 0.022), V(1, 0, 0), V(0, 0, 1), 0.07, 0.025, off=0.004), "disp_din",
             uv=((0.0, 0.55), (0.6, 0.55), (0.6, 1.0), (0.0, 1.0)))
    # reading lamps on the side walls above the bunk
    for s in (-1, 1):
        cyl(f"reading_lamp_{s}", (s * (XI - 0.02), YB + 0.25, 2.55), 0.03, 0.03, "dash_dark", axis="X", seg=20, bev=0.004)


def build_overhead():
    group("overhead")
    zb, zt = WS_Z1 + 0.035, CEIL_SIDE + 0.10
    yfront = ws_y(WS_Z1) + 0.02
    yback = 0.86
    # carcass following the roof: profile in YZ extruded across X
    def prof(x):
        top = zt + (CEIL - 0.02 - zt) * (1 - (abs(x) / XI) ** 2.4) ** 0.8 - 0.01
        return [V(x, yfront, zb), V(x, yback + 0.035, zb), V(x, yback, zb + 0.03), V(x, yback - 0.01, top - 0.08),
                V(x, yback + 0.03, top), V(x, yfront, top)]
    loops = [prof(-XI + 0.005 + (2 * XI - 0.01) * i / 24) for i in range(25)]
    oh = loft("overhead_body", loops, "dash_lower", closed=True, cap0=True, cap1=True, sharp=40)
    bevel(oh, 0.012, 3, angle=30)
    # lids on the rear face: 2 left, DIN console centre, 2 right
    for i, (x0, x1) in enumerate(((-1.12, -0.70), (-0.67, -0.25), (0.25, 0.67), (0.70, 1.12))):
        box_mm(f"oh_lid_{i}", x0, x1, yback - 0.026, yback - 0.006, zb + 0.06, zb + 0.30, "dash_lower", bev=0.008)
        box_mm(f"oh_grip_{i}", (x0 + x1) / 2 - 0.06, (x0 + x1) / 2 + 0.06, yback - 0.034, yback - 0.02, zb + 0.07,
               zb + 0.085, "dash_dark", bev=0.004)
    # centre DIN console angled down towards the seats: tachograph (top) + radio/CB (bottom)
    n = V(0, -1, -0.55).normalized()
    c = V(0.0, yback - 0.02, zb + 0.15)
    panel("din_frame", rrect(0.42, 0.22, 0.015, 3), c, n, V(0, 0.45, 1).normalized(), 0.05, "dash_dark", bev=0.004)
    for k, dz in enumerate((0.05, -0.05)):
        cc = c + n * 0.004 + V(0, 0.45, 1).normalized() * dz
        panel(f"din_unit_{k}", rrect(0.182, 0.053, 0.004, 2), cc, n, V(0, 0.45, 1).normalized(), 0.012, "piano",
              bev=0.0015)
        uv = ((0, 0.5 * (1 - k)), (1, 0.5 * (1 - k)), (1, 0.5 * (2 - k)), (0, 0.5 * (2 - k)))
        plane_uv(f"din_lcd_{k}", quad_on(cc + V(0.025, 0, 0), n, V(0, 0.45, 1).normalized(), 0.09, 0.03, off=0.0005),
                 "disp_din", uv=uv)
        for b in range(3):
            panel(f"din_btn_{k}_{b}", rrect(0.012, 0.012, 0.002, 1), cc + V(-0.07 + b * 0.016, 0, 0), n,
                  V(0, 0.45, 1).normalized(), 0.004, "switch")
    # reading spots in the underside
    for x in (-0.55, 0.55):
        cyl(f"spot_{x}", (x, yback + 0.12, zb - 0.002), 0.022, 0.006, "lamp_lens", seg=20, bev=0.001)
    # rear overhead storage above the bunk
    box_mm("rear_oh", -XI + 0.005, XI - 0.005, YB + 0.002, YB + 0.38, 3.12, CEIL_SIDE + 0.12, "dash_lower", bev=0.012, seg=3)
    for i, (x0, x1) in enumerate(((-1.10, -0.38), (-0.35, 0.35), (0.38, 1.10))):
        box_mm(f"rear_lid_{i}", x0, x1, YB + 0.38, YB + 0.392, 3.15, 3.42, "dash_lower", bev=0.006)
        box_mm(f"rear_grip_{i}", (x0 + x1) / 2 - 0.06, (x0 + x1) / 2 + 0.06, YB + 0.392, YB + 0.40, 3.16, 3.175, "dash_dark")
    # roof hatch with frame and pleated blind, dome lights
    box_mm("hatch_frame", -0.40, 0.40, 0.05, 0.70, CEIL - 0.045, CEIL - 0.02, "dash_lower", bev=0.012, seg=2)
    box_mm("hatch_blind", -0.36, 0.36, 0.09, 0.66, CEIL - 0.035, CEIL - 0.025, "curtain", bev=0.004)
    for k in range(10):
        box_mm(f"hatch_pleat_{k}", -0.36, 0.36, 0.10 + k * 0.056, 0.104 + k * 0.056, CEIL - 0.039, CEIL - 0.035, "gap")
    for y in (-0.40, 0.82):
        panel(f"dome_{y}", rrect(0.22, 0.09, 0.03, 4), V(0, y, CEIL - 0.03), V(0, 0, -1), V(0, 1, 0), 0.012, "lamp_lens",
              bev=0.004)


def build_curtains():
    group("curtains")
    # rail along the windscreen header and both sides
    yr = ws_y(WS_Z1) - 0.06
    rail = [V(-XI + 0.03, DOOR_Y0, WIN_Z1 + 0.08), V(-XI + 0.03, yr, WS_Z1 + 0.025), V(XI - 0.03, yr, WS_Z1 + 0.025),
            V(XI - 0.03, DOOR_Y0, WIN_Z1 + 0.08)]
    tube("curtain_rail", rail, 0.006, "satin", seg=8)

    def bunched(name, base, along, normal, width, z0, z1, folds=7):
        loops = []
        for zi in range(9):
            z = z0 + (z1 - z0) * zi / 8
            lp = []
            nn = G.Q(folds * 6, folds * 2)
            for i in range(nn + 1):
                t = i / nn
                depth = (0.035 if G.STATE["q"] > 0.4 else 0.0) * math.sin(2 * math.pi * folds * t) * (0.85 + 0.15 * math.sin(7 * z + i))
                lp.append(base + along * (width * t) + normal * depth + V(0, 0, z - base.z))
            loops.append(lp)
        c = loft(name, loops, "curtain", closed=False, sharp=None)
        solidify(c, 0.003, 0.0)
        # B2: even-offset thickness on the ~180 deg pleats threw single vertices 0.5 m out (a black spike across the
        # windscreen once the curtain moved forward with the 7 deg glass); plain offset keeps the 3 mm sheet
        c.modifiers["solid"].use_even_offset = False
        return c

    def ceil_z(x):
        return CEIL_SIDE + (CEIL - CEIL_SIDE) * (1 - min(1.0, abs(x) / XI) ** 2.4) ** 0.8

    def hung(name, p0, along, normal, width, z0, top_z, folds, depth=0.030, seed=0.0):
        """Drawn (not bunched) curtain: irregular pleats that are tight at the gliders and open towards the hem."""
        lod2 = G.STATE["q"] <= 0.4
        nn = 3 if lod2 else G.Q(folds * 6, folds * 3)
        rows = 2 if lod2 else G.Q(8, 4)
        loops = []
        for zi in range(rows + 1):
            f = zi / rows                                   # 0 = hem, 1 = track
            lp = []
            for i in range(nn + 1):
                t = i / nn
                tw = t + 0.035 * math.sin(2 * math.pi * (1.7 * t + seed))          # uneven pleat spacing
                amp = 0.0 if lod2 else depth * (0.55 + 0.45 * (1 - f)) * (0.75 + 0.25 * math.sin(11.0 * t + 3.0 * seed))
                d = amp * math.sin(2 * math.pi * folds * tw + 0.8 * math.sin(2.2 * f + 5.0 * t))
                q = p0 + along * (width * t) + normal * d
                zt = top_z(q.x)
                lp.append(V(q.x, q.y, z0 + (zt - z0) * f + (0.012 * math.sin(2 * math.pi * folds * tw) * (1 - f) if not lod2 else 0)))
            loops.append(lp)
        c = loft(name, loops, "curtain", closed=False, sharp=None)
        solidify(c, 0.003, 0.0)
        c.modifiers["solid"].use_even_offset = False
        return c

    # r4 (lead, "aquarium" from outside): a real long-haul cab is not see-through. Sleeper privacy curtain on a ceiling
    # track just ahead of the bunk: drawn behind the passenger seat (x >= 0.45: outside the bunk camera's frame and
    # behind the driver, so no driver sight line crosses it), parked and tied back at the driver-side wall
    yt = -0.075
    tube("curtain_rail_bunk", [V(-XI + 0.04 + (2 * XI - 0.08) * i / 12, yt, ceil_z(-XI + 0.04 + (2 * XI - 0.08) * i / 12) - 0.012)
                           for i in range(13)], 0.007, "satin", seg=6)
    hung("curtain_bunk_1", V(0.45, yt, 0), V(1, 0, 0), V(0, 1, 0), XI - 0.05 - 0.45, 1.93, lambda x: ceil_z(x) - 0.022,
         folds=9, seed=0.3)
    bunched("curtain_bunk_-1", V(-XI + 0.045, yt, 0), V(1, 0, 0), V(0, 1, 0), 0.12, 1.96, ceil_z(-XI + 0.10) - 0.022, folds=6)
    box_mm("bunk_strap_tie", -XI + 0.035, -XI + 0.175, yt - 0.05, yt + 0.05, 2.52, 2.56, "webbing", bev=0.006)
    # passenger door curtain left a third drawn from the B-pillar (rear part of the glass only: the right mirrors
    # are seen through the front part) - breaks the line of sight through both door windows
    hung("curtain_pass", V(XI - 0.028, DOOR_Y0 - 0.02, 0), V(0, 1, 0), V(-1, 0, 0), 0.60, WIN_Z0 + 0.01,
         lambda x: WIN_Z1 + 0.07, folds=7, depth=0.022, seed=0.7)

    for s in (-1, 1):  # windscreen curtains parked at the A-pillars, side curtains at the B-pillars
        fr = apillar_frame(s, 2.5)
        if fr is not None:   # parked in the pillar's shadow: bunched along the sight line behind the trim
            a_, b_, t_, n_ = fr
            mid_ = (a_ + b_) / 2
            d_ = V(EYE[0] - mid_.x, EYE[1] - mid_.y, 0).normalized()
            b = mid_ + n_ * 0.058 + d_ * 0.065
            bunched(f"curtain_ws_{s}", V(b.x, b.y, 0), d_, V(-d_.y, d_.x, 0), 0.09, 2.05, WS_Z1 + 0.02, folds=5)
        else:
            b = V(s * (XI - 0.06), ws_y(WS_Z1) - 0.13, 0)
            bunched(f"curtain_ws_{s}", b, V(-s, 0.25, 0).normalized(), V(0, 1, 0), 0.10, 2.05, WS_Z1 + 0.02)
        b = V(s * (XI - 0.025), DOOR_Y0 - 0.02, 0)
        if s < 0:   # r4: the passenger one is "curtain_pass" (partly drawn)
            bunched(f"curtain_side_{s}", b, V(0, -1, 0), V(-s, 0, 0), 0.11, 2.02, WIN_Z1 + 0.07)
    # electric roller blinds in a cassette over the windscreen; driver side pulled down a little
    yb = ws_y(WS_Z1) - 0.035
    box_mm("blind_cassette", -XI + 0.07, XI - 0.07, yb - 0.035, yb + 0.015, WS_Z1 - 0.005, WS_Z1 + 0.04, "dash_dark",
           bev=0.01)
    # B2.1 (owner sheets): black inner visor band across the full width over the windscreen: two padded sun
    # visors parked up in the plane of the glass (in the top frit zone, bottom 20 mm above the visible glass edge
    # so they do not cut the view), hinge rods, satin clips, centre bracket. Glass-parallel frame from the rake.
    r = math.radians(RAKE)
    nrm, upg = V(0, -math.cos(r), -math.sin(r)), V(0, -math.sin(r), math.cos(r))
    zv0, zv1 = WS_Z1 - 0.10 + 0.02, WS_Z1 + 0.030
    zc = (zv0 + zv1) / 2
    for k, (x0, x1) in enumerate(((-0.96, -0.07), (0.07, 0.96))):
        xc, w = (x0 + x1) / 2, x1 - x0
        ymin = min(glass_y(x0 + (x1 - x0) * i / 12, zc) for i in range(13))
        c = V(xc, ymin - 0.032, zc)
        panel(f"sun_visor_{k}", rrect(w, zv1 - zv0, 0.030, G.Q(5, 2)), c, nrm, upg, 0.024, "dash_soft", bev=0.008,
              bseg=G.Q(3, 1))
        rod(f"sun_visor_hinge_{k}", c + upg * ((zv1 - zv0) / 2 - 0.006) + nrm * -0.012 + V(x0 - xc + 0.02, 0, 0),
            c + upg * ((zv1 - zv0) / 2 - 0.006) + nrm * -0.012 + V(x1 - xc - 0.02, 0, 0), 0.0065, "dash_dark", seg=10)
        xi = x1 - 0.03 if k == 0 else x0 + 0.03
        box(f"sun_visor_clip_{k}", tuple(c + V(xi - xc, 0, 0) - upg * 0.035 + nrm * 0.004), (0.022, 0.012, 0.030),
            "satin", bev=0.003)
        # stitched seam round the visor face (padded vinyl)
        e = 0.012
        loop = [c + nrm * 0.0005 + V(px, 0, 0) + upg * pz for px, pz in rrect(w - 2 * e, zv1 - zv0 - 2 * e, 0.02, 3)]
        strip(f"sun_visor_seam_{k}", loop + [loop[0]], nrm, 0.004, "stitch_dark", offset=0.0005, u_len=0.017)
    box("visor_centre_bracket", tuple(V(0.0, glass_y(0.0, zc) - 0.040, zc + 0.02)), (0.10, 0.03, 0.07), "dash_dark",
        bev=0.008)
    for x0, x1, drop in ((-XI + 0.10, -0.03, 0.10), (0.03, XI - 0.10, 0.20)):
        z1 = WS_Z1 - 0.005
        z0 = z1 - drop
        corners = [V(x0, ws_y(z0) - 0.02, z0), V(x1, ws_y(z0) - 0.02, z0), V(x1, ws_y(z1) - 0.02, z1), V(x0, ws_y(z1) - 0.02, z1)]
        bm = bmesh.new()
        bm.faces.new([bm.verts.new(c) for c in corners])
        bl = G.finish(f"blind_{x0:.2f}", bm, "blind", smooth=False)
        solidify(bl, 0.002)
        box_mm(f"blind_bar_{x0:.2f}", x0, x1, ws_y(z0) - 0.035, ws_y(z0) - 0.01, z0 - 0.012, z0 + 0.004, "dash_dark", bev=0.004)


# ---------------------------------------------------------------- mirrors (outside, seen through the windows)
def build_mirrors():
    """Outside mirrors, seen through the windows; heads placed where exterior/body.py mirrors('classic') puts them
    (A6 r3: before, the heads sat 0.4 m further forward and, with the corrected rake, hid behind the A-pillar).
    Glass faces are aimed like a driver would set them: the normal bisects 'to the eye point' and 'to the field of view'
    (class II/IV: straight back along the cab side; class V: the ground at the passenger door; class VI: the ground in
    front of the bumper). The MIRROR_* quads carry the game's RenderTextures; arms/housings are shell placeholders."""
    group("mirrors")
    my = side_win_front(2.90) - 0.125        # head y; = exterior/body.py mirrors(): win_front(2.90) + 0.02 - 0.10

    def aim(c, target):
        return ((EYE - c).normalized() + (V(*target) - c).normalized()).normalized()

    for s in (-1, 1):
        xh, yh = s * 1.50, my
        top = [V(s * HALF_OUT, side_win_front(2.90) + 0.02, 2.93), V(s * 1.33, yh + 0.02, 2.99), V(xh, yh, 2.94)]
        tube(f"mirror_arm_up_{s}", G.polyline_smooth(top, 4), 0.016, "ext_plastic", seg=12)
        low = [V(s * HALF_OUT, side_win_front(2.25) - 0.02, 2.25), V(s * 1.40, yh + 0.01, 2.12), V(xh, yh, 2.08)]
        tube(f"mirror_arm_lo_{s}", G.polyline_smooth(low, 4), 0.014, "ext_plastic", seg=12)
        for name, zc, h, w in (("main", 2.60, 0.39, 0.215), ("wide", 2.20, 0.17, 0.215)):
            c = V(xh, yh, zc)
            n = aim(c, (xh, yh - 30.0, zc - 0.6))
            panel(f"mirror_{name}_housing_{s}", rrect(w + 0.025, h + 0.025, 0.035, 4), c - n * 0.005, n, V(0, 0, 1), 0.09,
                  "ext_plastic", bev=0.02, bseg=3)
            plane_uv(f"mirror_{name}_glass_{s}", quad_on(c, n, V(0, 0, 1), w, h, off=0.002), "mirror")
        rod(f"mirror_spine_{s}", (xh, yh + 0.03, 1.95 if s > 0 else 2.08), (xh, yh + 0.03, 2.94), 0.012, "ext_plastic",
            seg=10)
    # class V kerb mirror under the passenger main mirrors, class VI front mirror over the passenger-side corner
    c = V(1.42, my + 0.012, 1.98)
    n = aim(c, (1.55, 0.6, 0.0))
    tube("kerb_arm", [V(1.50, my + 0.03, 1.97), c + n * -0.03], 0.012, "ext_plastic", seg=10)
    panel("kerb_head", rrect(0.20, 0.14, 0.03, 3), c - n * 0.004, n, V(1, 0, 0), 0.06, "ext_plastic", bev=0.01)
    plane_uv("kerb_glass", quad_on(c, n, V(1, 0, 0), 0.17, 0.11, off=0.002), "mirror_down")
    # B2: exterior front mirror hangs above the sun visor (body.py: header at WS_Z1 + 0.29, glass ~WS_Z1 + 0.155)
    c = V(0.98, ws_y(WS_Z1) + 0.18, WS_Z1 + 0.155)
    n = aim(c, (0.6, 3.2, 0.0))
    tube("front_arm", [V(0.98, ws_y(WS_Z1) + 0.02, WS_Z1 + 0.30), V(0.98, ws_y(WS_Z1) + 0.15, WS_Z1 + 0.28),
                       c - n * 0.03], 0.012,
         "ext_plastic", seg=10)
    panel("front_head", rrect(0.26, 0.15, 0.03, 3), c - n * 0.004, n, V(1, 0, 0), 0.06, "ext_plastic", bev=0.01)
    plane_uv("front_glass", quad_on(c, n, V(1, 0, 0), 0.23, 0.12, off=0.002), "mirror_down")


# ---------------------------------------------------------------- UVs
def auto_uv(objs):
    """One Smart-UV pass over every interior mesh -> shared 0-1 atlas layer 'Bake' (non-overlapping, for AO/unique
    bakes) and a world-scaled copy 'UVMap' (1 UV unit = 1 m, for the tiled detail maps). Uniform texel density."""
    todo = [o for o in objs if o.type == "MESH" and not o.get("fixed_uv") and not o.get("decal")]
    for o in todo:
        if "UVMap" not in o.data.uv_layers:
            o.data.uv_layers.new(name="UVMap")
    bpy.ops.object.select_all(action="DESELECT")
    for o in todo:
        o.select_set(True)
    bpy.context.view_layer.objects.active = todo[0]
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.uv.smart_project(angle_limit=math.radians(55), island_margin=0.0015, area_weight=0.0,
                             correct_aspect=True, scale_to_bounds=False)
    bpy.ops.object.mode_set(mode="OBJECT")
    a3 = auv = 0.0
    for o in todo:
        me = o.data
        uv = me.uv_layers["UVMap"].data
        mw = o.matrix_world
        for p in me.polygons:
            a3 += sum(0 for _ in ()) + p.area * abs(mw.determinant()) ** (2 / 3)
            pts = [uv[li].uv for li in p.loop_indices]
            ar = 0.0
            for i in range(1, len(pts) - 1):
                ar += abs((pts[i] - pts[0]).cross(pts[i + 1] - pts[0])) / 2
            auv += ar
    k = math.sqrt(a3 / max(auv, 1e-9))
    for o in todo:
        me = o.data
        me.uv_layers.new(name="Bake")  # copies the active (atlas) layout
        uv = me.uv_layers["UVMap"].data
        for d in uv:
            d.uv = d.uv * k
        me.uv_layers.active = me.uv_layers["UVMap"]
        for i, l in enumerate(me.uv_layers):
            l.active_render = (l.name == "UVMap")
    return k


# ---------------------------------------------------------------- scene, lights, cameras
def setup_render(a):
    sc = bpy.context.scene
    sc.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "OPTIX"
        prefs.get_devices()
        for d in prefs.devices:
            d.use = d.type == "OPTIX"
        sc.cycles.device = "GPU"
    except Exception:
        sc.cycles.device = "CPU"
    sc.cycles.samples = a.samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.012
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.max_bounces = 10
    sc.cycles.diffuse_bounces = 5
    sc.cycles.glossy_bounces = 4
    sc.cycles.transparent_max_bounces = 16
    sc.cycles.sample_clamp_indirect = 6.0
    sc.cycles.blur_glossy = 1.0
    sc.render.resolution_x, sc.render.resolution_y = (int(v) for v in a.res.split("x"))
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.quality = 88
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.render.use_stamp = False


# mirror placeholder level per sky: ~0.55 reflectance x sky radiance / 0.83 (sky value in the placeholder image)
MIRROR_LEVEL = {"overcast": (0.55, (1.0, 1.0, 1.0)), "lowsun": (0.55, (1.0, 0.90, 0.78))}


def set_lighting(kind):
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o)
    w = bpy.data.worlds.get("sky") or bpy.data.worlds.new("sky")
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(bg.outputs[0], out.inputs[0])
    if kind == "overcast":
        # overcast: bright horizon, slightly darker zenith, no direct sun (typical Podlasie sky)
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (0.60, 0.61, 0.62, 1)
        ramp.color_ramp.elements[1].position = 0.6
        ramp.color_ramp.elements[1].color = (0.80, 0.82, 0.86, 1)
        nt.links.new(sep.outputs["Z"], ramp.inputs[0])
        cl = nt.nodes.new("ShaderNodeTexNoise")       # low-contrast stratus texture (A6: no flat white sky)
        cl.inputs["Scale"].default_value = 3.5
        cl.inputs["Detail"].default_value = 6
        cl.inputs["Roughness"].default_value = 0.55
        nt.links.new(tc.outputs["Generated"], cl.inputs["Vector"])
        cm = nt.nodes.new("ShaderNodeMapRange")
        cm.inputs[1].default_value, cm.inputs[2].default_value = 0.35, 0.70
        cm.inputs[3].default_value, cm.inputs[4].default_value = 0.86, 1.06
        nt.links.new(cl.outputs["Fac"], cm.inputs[0])
        sky = M._mix_rgb(nt, 1.0, ramp.outputs[0], cm.outputs[0], "MULTIPLY")
        nt.links.new(sky, bg.inputs["Color"])
        bg.inputs["Strength"].default_value = 1.35
        sc.view_settings.exposure = 2.3
        M.set_mirror_level(*MIRROR_LEVEL["overcast"])
    else:
        # low sun ~9 deg from the front-left (late afternoon heading west-ish)
        sky = nt.nodes.new("ShaderNodeTexSky")
        sky.sky_type = "NISHITA"
        sky.sun_disc = False
        el, az = math.radians(9.0), math.radians(125.0)
        sky.sun_elevation = el
        sky.sun_rotation = az
        sky.air_density = 1.2
        sky.dust_density = 2.5
        nt.links.new(sky.outputs[0], bg.inputs["Color"])
        # A6: a 9 deg sun is strongly attenuated; sun:sky balance ~ 4:1 instead of ~20:1 (+1.6 EV) so sunlit dark
        # plastics stay dark grey rather than going beige-white
        bg.inputs["Strength"].default_value = 0.30
        ld = bpy.data.lights.new("sun", "SUN")
        ld.energy = 4.0
        ld.angle = math.radians(0.6)
        ld.color = (1.0, 0.80, 0.60)
        sun = bpy.data.objects.new("sun", ld)
        sc.collection.objects.link(sun)
        # Nishita rotation is measured from +X? use direction vector: sun at azimuth az (from +Y towards -X)
        to_sun = V(-math.sin(az - math.pi / 2) * 0 + math.cos(az), math.sin(az), math.tan(el)).normalized()
        sun.rotation_euler = (-to_sun).to_track_quat("-Z", "Y").to_euler()
        sc.view_settings.exposure = 1.2
        M.set_mirror_level(*MIRROR_LEVEL["lowsun"])
    sc.world = w


def look_cam(name, loc, target, hfov_deg):
    cd = bpy.data.cameras.get(name) or bpy.data.cameras.new(name)
    cd.sensor_fit = "HORIZONTAL"
    cd.sensor_width = 36
    cd.angle = math.radians(hfov_deg)
    cd.clip_start = 0.02
    cd.clip_end = 3000
    ob = bpy.data.objects.get(name) or bpy.data.objects.new(name, cd)
    if ob.name not in bpy.context.scene.collection.objects:
        bpy.context.scene.collection.objects.link(ob)
    ob.location = V(loc)
    ob.rotation_euler = (V(target) - V(loc)).to_track_quat("-Z", "Y").to_euler()
    return ob


def cameras():
    n, u, v = wheel_frame()
    cl = V(SEAT_X, 1.17, 2.15)
    return {
        # driver eye-point, forward; hFOV 80 deg ~ phone landscape cab camera
        "kierowca": (EYE, EYE + V(0.08, 1.0, -0.22), 80),
        "zegary": (EYE, cl + V(0.05, 0, 0.0), 50),
        "pasazer": (V(-SEAT_X + 0.02, HPT.y + 0.02, EYE.z - 0.02), V(-0.45, 1.25, 2.12), 80),
        "lezanka": (V(0.02, -0.52, 2.30), V(-0.22, 1.30, 2.22), 84),
        "kierownica": (V(-0.16, 0.66, 2.27), V(-0.50, 0.99, 2.05), 56),
        "fotel": (V(-0.98, 0.66, 2.24), V(-0.50, 0.36, 1.84), 55),
        "piasta": (WHEEL_C + n * 0.42 + V(0.05, 0, 0.0), WHEEL_C + n * 0.03 + V(0.02, 0, 0), 36),
        # r8 wheel review: whole wheel square-on, right thumb rest / pod, rim seam from the eye
        "kolo": (WHEEL_C + n * 0.80, WHEEL_C, 66),
        "kciuk": (WHEEL_C + n * 0.30 + u * 0.20 + v * 0.10, WHEEL_C + u * 0.185 - v * 0.02, 40),
        "szew": (EYE, WHEEL_C + v * 0.20 + u * 0.10, 22),
        "kolumna": (WHEEL_C - u * 0.42 - n * 0.10 + v * 0.16, WHEEL_C - n * 0.11, 50),
    }


EXTRA_CAMS = ["piasta", "kolo", "kciuk", "szew", "kolumna"]


LIGHT_CAMS = {"overcast": ["kierowca", "zegary", "pasazer", "lezanka", "kierownica", "fotel"],
              "lowsun": ["kierowca", "pasazer"]}


# ---------------------------------------------------------------- stats
def tri_stats():
    dg = bpy.context.evaluated_depsgraph_get()
    per = {}
    tot = 0
    for c in COLLS:
        if c == "backdrop":
            continue
        n = 0
        for o in COLLS[c].objects:
            if o.type != "MESH":
                continue
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            n += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
        per[c] = n
        tot += n
    return per, tot


# ---------------------------------------------------------------- main
def build(a):
    """Build the whole scene (interior + backdrop), UVs and stats. Used by main() and bake_ao.py."""
    global RAKE
    if a.rake is not None:
        RAKE = a.rake
    t0 = time.time()
    bpy.ops.wm.read_factory_settings(use_empty=True)
    COLLS.clear()
    M._IMG.clear()
    M.PARAMS.clear()
    G.STATE["q"] = {0: 1.0, 1: 0.55, 2: 0.27}[getattr(a, "lod", 0)]
    build_materials(a)
    build_shell()
    build_glass()
    build_dash()
    build_wheel(a.badge)
    build_pedals()
    seat("drv", SEAT_X, True)
    seat("pas", -SEAT_X, False)
    build_doors()
    build_floor()
    build_bunk()
    build_overhead()
    build_curtains()
    build_mirrors()
    interior = [o for c, col in COLLS.items() if c != "backdrop" for o in col.objects]
    k = auto_uv(interior)
    if not getattr(a, "no_backdrop", False):
        BD.build(group)
    per, tot = tri_stats()
    stats = {"tris_total_interior_incl_shell_and_mirrors": tot, "tris_per_group": per, "uv_scale_m_per_atlas": k,
             "objects": len(interior), "materials": len([m for m in bpy.data.materials if m.users]),
             "build_s": round(time.time() - t0, 1)}
    print("STATS", json.dumps(stats))
    if a.stats:
        json.dump(stats, open(a.stats, "w"), indent=2)
    # eye-point + H-point empties (for A3/A7 import)
    for nm, p in (("EYE_POINT", EYE), ("H_POINT", HPT), ("WHEEL_CENTRE", WHEEL_C)):
        e = bpy.data.objects.new(nm, None)
        e.location = p
        e.empty_display_size = 0.05
        bpy.context.scene.collection.objects.link(e)
    return stats


def main():
    a = parse_args()
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)
    build(a)
    setup_render(a)
    cams = cameras()
    if a.hide:
        for o in bpy.data.objects:
            if any(o.name.startswith(h) for h in a.hide.split(",")):
                o.hide_render = True
    if a.camxyz:
        p0, p1, f = a.camxyz.split(":")
        cams["debug"] = (V(*[float(x) for x in p0.split(",")]), V(*[float(x) for x in p1.split(",")]), float(f))
        for k in LIGHT_CAMS:
            LIGHT_CAMS[k] = LIGHT_CAMS[k] + ["debug"]
    want = None if a.cams == "all" else set(a.cams.split(","))
    for kind in a.light.split(","):
        set_lighting(kind)
        for cname in LIGHT_CAMS[kind] + (EXTRA_CAMS if kind == "overcast" else []):
            if (want and cname not in want) or (not want and cname in EXTRA_CAMS):
                continue
            loc, tgt, fov = cams[cname]
            ob = look_cam(cname, loc, tgt, fov)
            bpy.context.scene.camera = ob
            fn = os.path.join(a.out, f"{cname}_{kind}{a.suffix}.jpg")
            bpy.context.scene.render.filepath = fn
            t = time.time()
            bpy.ops.render.render(write_still=True)
            print("WROTE", fn, round(time.time() - t, 1), "s")
    if a.blend:
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend), compress=True)


if __name__ == "__main__":
    main()
