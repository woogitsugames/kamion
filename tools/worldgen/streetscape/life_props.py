"""Static "life" prototypes and the depot gate kit (our own procedural meshes, same frame as streetscape.props):
x = right, y = front, z = up, origin on the ground.

  car_<body>_<colour>     passenger cars (hatch / sedan / estate / suv), origin = centre of the footprint,
                          +y = nose; built in streetscape.life_cars (profile bodies, LOD0 / LOD1 / LOD2)
  van_<colour>            car-derived light van (4.5 m), origin = centre, +y = nose (life_cars)
  trailer_<kind>_<k>      13.6 m semitrailer standing on its landing legs (dropped at a dock or in a yard),
                          origin = centre of the REAR edge on the ground, +y = toward the kingpin, so a trailer
                          backed onto a dock door is placed at the door with yaw = wall outward normal.
                          Kinds: curtain (curtainsider, plain fictional colours, no lettering), box (dry box),
                          reefer (white box + front cooling unit). No real liveries or logos anywhere.
  tractor_<colour>        4x2 tractor unit, generic cab-over shape (no make, no grille badge, plain paint),
                          origin = ground under the fifth-wheel centre, +y = forward; a coupled trailer is placed
                          with its rear edge TRAILER_KINGPIN behind that point (same yaw)
  container_<20|40>_<k>   ISO dry container (20 ft 6.06 / 40 ft 12.19 x 2.44 x 2.59 m), corrugated sides, faded
                          plain colours, no operator markings; origin = centre of the footprint, +y = long axis
  pallets_empty_<n>       stack of n empty EUR pallets (1.2 x 0.8 x 0.144 m each)
  pallet_load             one wrapped pallet load (1.2 x 0.8 m, 1.35 m high)
  bin_1100_<colour>       1100 l four-wheel waste container (PN-EN 840-3 size class), lid closed
  skip_kp7                KP-7 steel skip (7 m3, the usual Polish builders' / industrial skip)
  cone                    traffic cone U-21 type, 0.75 m (white reflective bands)
  gatehouse               depot gatehouse (portiernia): steel container booth with a glazed front, flat roof
                          with overhang, A/C unit; +y = the glazed side toward the gate lane
  barrier_arm             striped boom barrier (szlaban): housing + 6 m red/white boom + rest post
  cantilever_gate         10 m cantilever sliding gate (brama przesuwna) in the OPEN (retracted) position:
                          the leaf stands behind the fence line, +x = direction it slides to close
  facade_sign_<code>      flat fascia boards with functional lettering only (HALA A, BIURO, RECEPCJA, DOSTAWY,
                          PORTIERNIA, ...) - no brand names
Every prototype has LOD0 and LOD1 (and a simple collision box where a truck can hit it). Triangle counts per
LOD are written to props_meta.json (mesh budget). Dimensions: WORKING_VALUE typical values unless cited.
"""

from __future__ import annotations

import math

import numpy as np

from .props import Mesh
from .life_cars import CARS, CAR_COLOURS, VAN, VAN_COLOURS, car, van, _paint_uv  # noqa: F401  (ADR 0041 par. 6)

CURTAIN_COLOURS = ["grey", "blue", "white", "red", "green", "silver"]
TRACTOR_COLOURS = ["white", "silver", "blue", "red", "green", "black"]
CONTAINER_COLOURS = ["rust", "blue", "grey", "green", "beige", "white"]
BIN_COLOURS = ["green", "grey", "yellow", "blue"]
SIGNS = {"hala_a": "HALA A", "hala_b": "HALA B", "hala_c": "HALA C", "hala_d": "HALA D", "biuro": "BIURO",
         "recepcja": "RECEPCJA", "dostawy": "DOSTAWY", "portiernia": "PORTIERNIA", "magazyn": "MAGAZYN",
         "serwis": "SERWIS"}


# ------------------------------------------------------------------------------------------- helpers
def loft(m, mat, sections, ys, close_ends=True):
    """Loft of closed cross-sections (list of (k, 2) arrays in (x, z)) along y. CCW seen from +y."""
    k = len(sections[0])
    V, T, UV = [], [], []
    for sec, y in zip(sections, ys):
        for x, z in sec:
            V.append([x, y, z])
            UV.append([y, z])
    n = len(ys)
    for i in range(n - 1):
        for j in range(k):
            a, b = i * k + j, i * k + (j + 1) % k
            c, d = a + k, b + k
            T += [(a, d, b), (a, c, d)]
    m.add(mat, V, T, UV)
    if close_ends:
        for idx, flip in ((0, True), (n - 1, False)):
            sec, y = sections[idx], ys[idx]
            c = np.mean(sec, axis=0)
            Vc = [[c[0], y, c[1]]] + [[x, y, z] for x, z in sec]
            Tc = [(0, 1 + j, 1 + (j + 1) % k) for j in range(k)]
            if not flip:
                Tc = [(a, cc, b) for a, b, cc in Tc]
            m.add(mat, Vc, Tc, [[v[0], v[2]] for v in Vc])


def rounded_rect(hw, zb, zt, r=0.08, rb=0.05):
    return np.array([(hw - rb, zb), (hw, zb + rb), (hw, zt - r), (hw - r, zt), (-hw + r, zt), (-hw, zt - r),
                     (-hw, zb + rb), (-hw + rb, zb)])[::-1]


def wheel(m, c, r, w, seg, axis=(1, 0, 0), tyre="tyre", rim="rim", rim_r=0.62, out_sign=1, simple=False):
    """Tyre and recessed, vented outer rim (out_sign = vehicle side).

    The inner side is never visible. simple=True keeps the distant six-sided
    tread and discs. ADR 0122 life r4: near rims reuse existing rim/tyre groups.
    """
    c = np.asarray(c, float)
    ax = np.asarray(axis, float)
    if simple:
        # ADR 0122: retain separate axles and ground contact in the distant LOD.
        # One ring vertex points down; the former open tube lost its outer face.
        n = 6
        u = np.array([0., 0., 1.])
        if abs(np.dot(ax, u)) > 0.9:
            u = np.array([0., 1., 0.])
        u -= ax * np.dot(ax, u)
        u /= np.linalg.norm(u)
        v = np.cross(ax, u)
        ring = np.array([math.cos(t) * u + math.sin(t) * v for t in np.arange(n) * 2 * math.pi / n])
        V = np.concatenate([c - ax * w / 2 + r * ring, c + ax * w / 2 + r * ring])
        T = []
        for i in range(n):
            j = (i + 1) % n
            T += [(i, j, n + j), (i, n + j, n + i)]
        m.add(tyre, V, T)
        sgn = 1 if out_sign >= 0 else -1
        cc = c + ax * sgn * w / 2
        cap = [(0, i, i + 1) for i in range(1, n - 1)]
        if sgn < 0:
            cap = [(a, d, b) for a, b, d in cap]
        m.add(tyre, cc + r * ring, cap)
        m.add(rim, cc + ax * sgn * 0.006 + r * rim_r * ring, cap)
        return
    m.tube(tyre, c - ax * w / 2, c + ax * w / 2, r, r, seg, cap=False)
    sgn = 1 if out_sign >= 0 else -1
    cc = c + ax * sgn * w / 2
    a = np.linspace(0, 2 * math.pi, seg + 1)[:-1]
    u = np.array([0, 1.0, 0])
    v = np.cross(ax, u)
    ring = [cc + (math.cos(t) * u + math.sin(t) * v) * r for t in a]
    inner = [cc + (math.cos(t) * u + math.sin(t) * v) * r * rim_r + ax * sgn * 0.01 for t in a]
    T = []
    for i in range(seg):
        a0, a1, b0, b1 = i, (i + 1) % seg, seg + i, seg + (i + 1) % seg
        T += [(a0, a1, b1), (a0, b1, b0)] if sgn > 0 else [(a0, b1, a1), (a0, b0, b1)]
    m.add(tyre, ring + inner, T)
    # Keep the tread, nominal envelope, sidewall and outer bead exactly where
    # they were. The dish/vents replace the old almost-flat full grey fan.
    # Dimensions below are WORKING_VALUE for a generic unbranded steel rim.
    directions = np.asarray([math.cos(t) * u + math.sin(t) * v for t in a])
    rr = r * rim_r

    def rim_ring(radius, depth):
        return cc + ax * sgn * depth + directions * radius

    def face(material, points):
        # Reverse winding, not vertex order: reversing the whole quad changes
        # its diagonal and hence area-weighted crease normals on the other side.
        triangles = [(0, 1, 2), (0, 2, 3)]
        if sgn < 0:
            triangles = [(a, c, b) for a, b, c in triangles]
        m.add(material, points, triangles, [[0, 0], [1, 0], [1, 1], [0, 1]])

    def annulus(outer, inside):
        for i in range(seg):
            j = (i + 1) % seg
            face(rim, [outer[i], outer[j], inside[j], inside[i]])

    bead = np.asarray(inner)                    # existing tyre/rim seam
    dish_outer = rim_ring(rr * 0.88, -0.035)
    dish_inner = rim_ring(rr * 0.42, -0.055)
    hub = rim_ring(rr * 0.28, 0.018)            # within the old +0.020 m cap
    annulus(bead, dish_outer)
    for i in range(seg):
        j = (i + 1) % seg
        q = np.asarray([dish_outer[i], dish_outer[j], dish_inner[j], dish_inner[i]])
        if i % 2:
            face(rim, q)
            continue
        # An actual inset opening with four metal walls and a dark backing.
        # Its occluded interior reuses tyre; no decal or new draw/material.
        centre = q.mean(axis=0)
        opening = centre + (q - centre) * 0.56
        back = opening - ax * sgn * 0.035
        for k in range(4):
            nk = (k + 1) % 4
            face(rim, [q[k], q[nk], opening[nk], opening[k]])
            face(rim, [opening[k], opening[nk], back[nk], back[k]])
        face(tyre, back)
    annulus(dish_inner, hub)
    centre = cc + ax * sgn * 0.018
    fan = [(0, 1 + i, 1 + (i + 1) % seg) if sgn > 0
           else (0, 1 + (i + 1) % seg, 1 + i) for i in range(seg)]
    m.add(rim, [centre] + list(hub), fan)


def bx(m, mat, x0, x1, y0, y1, z0, z1):
    m.box(mat, [(x0 + x1) / 2, (y0 + y1) / 2, (z0 + z1) / 2], abs(x1 - x0) / 2, abs(y1 - y0) / 2, abs(z1 - z0) / 2)


# ------------------------------------------------------------------------------------------- trailer
TRAILER_L, TRAILER_W, TRAILER_FLOOR, TRAILER_H = 13.60, 2.55, 1.20, 4.00
TRAILER_AXLES = (3.05, 4.36, 5.67)          # from the rear edge (axle spread 1.31 m, WORKING_VALUE)


def trailer(kind, colour):
    L, W, zf, H = TRAILER_L, TRAILER_W, TRAILER_FLOOR, TRAILER_H
    hw = W / 2
    side = {"curtain": f"trailer_curtain_{colour}", "box": "trailer_box_white", "reefer": "trailer_box_white"}[kind]
    out = []
    for lod in (0, 1):
        m = Mesh()
        zb = zf + 0.05
        if kind == "curtain":
            # curtain sides between the top and bottom rails, roof, front bulkhead
            for sx in (-1, 1):
                x = sx * hw
                q = [[x, 0.05, zb + 0.10], [x, L - 0.05, zb + 0.10], [x, L - 0.05, H - 0.12], [x, 0.05, H - 0.12]]
                # Physical-height UVs for the explicit 2.7 m material tile.
                # Existing fleet colours also vary the horizontal wear phase.
                phase = 0.61 * CURTAIN_COLOURS.index(colour) + (0.37 if sx < 0 else 0.0)
                u0, u1 = phase, phase + L - 0.10
                v0, v1 = 0.02, 0.02 + H - 0.12 - (zb + 0.10)
                uv = [[u0, v0], [u1, v0], [u1, v1], [u0, v1]]
                m.add(side, q if sx > 0 else q[::-1], [(0, 1, 2), (0, 2, 3)],
                      uv if sx > 0 else uv[::-1])
            bx(m, "trailer_alu", -hw - 0.02, hw + 0.02, 0.0, L, H - 0.12, H)               # roof + top rail
            bx(m, "trailer_chassis", -hw + 0.02, hw - 0.02, 0.0, L, zf - 0.14, zf)          # floor
            bx(m, "trailer_alu", -hw - 0.02, hw + 0.02, 0.0, L, zf, zb + 0.10)              # bottom rail (0.15 m)
            # front bulkhead: painted steel in the fleet's dark tone on the grey / blue / green trailers, bare light
            # panel on the others (r11, review A7: every front was the same light grey plate)
            bx(m, "trailer_front_dark" if colour in ("grey", "blue", "green") else "trailer_front",
               -hw + 0.01, hw - 0.01, L - 0.06, L, zb + 0.10, H - 0.12)
            if lod == 0:                         # curtain straps (buckles) every 0.62 m: flat strips on the curtain
                for y in np.arange(0.6, L - 0.3, 0.62):
                    for sx in (-1, 1):
                        x = sx * (hw + 0.006)
                        q = [[x, y - 0.025, zb + 0.02], [x, y + 0.025, zb + 0.02], [x, y + 0.025, zb + 0.6],
                             [x, y - 0.025, zb + 0.6]]
                        m.quad("trailer_strap", *(q if sx > 0 else q[::-1]))
                for y in (L * 0.33, L * 0.66):   # sliding posts
                    for sx in (-1, 1):
                        bx(m, "trailer_alu", sx * hw - 0.02, sx * hw + 0.02, y - 0.05, y + 0.05, zb + 0.10, H - 0.12)
        else:
            bx(m, side, -hw, hw, 0.05, L, zf - 0.05, H)
            if lod == 0:                         # vertical ribs (box panels joined every ~1.2 m)
                for y in np.arange(1.2, L - 0.5, 1.2):
                    for sx in (-1, 1):
                        bx(m, "trailer_alu", sx * hw - 0.012, sx * hw + 0.012, y - 0.03, y + 0.03, zf, H - 0.02)
            if kind == "reefer":
                # Transport refrigeration unit on the front bulkhead (r12, review s9: "agregat chłodni biały sześcian"):
                # white housing, condenser grille with horizontal slats over the upper two thirds (material stripes
                # `louvre_slats`, UV v = metres up), dark service band with the control box underneath. Generic shape,
                # no product copied; sizes WORKING_VALUE. The grille is on both LODs (a plain white box at 25 m).
                yq = L + 0.425
                bx(m, "reefer_unit", -0.95, 0.95, L, L + 0.42, 2.45, 3.85)
                # quads wound to face +y (out of the unit): until r12 the grille faced into the box and was culled,
                # which is why the unit rendered as a plain white cube
                m.quad("reefer_grille", [0.84, yq, 2.98], [-0.84, yq, 2.98], [-0.84, yq, 3.76], [0.84, yq, 3.76],
                       uv=((0.0, 0.0), (1.68, 0.0), (1.68, 0.78), (0.0, 0.78)))
                if lod == 0:
                    m.quad("trailer_chassis", [0.84, yq, 2.52], [-0.84, yq, 2.52], [-0.84, yq, 2.90], [0.84, yq, 2.90])
                    m.quad("reefer_unit", [0.78, yq + 0.004, 2.57], [0.38, yq + 0.004, 2.57], [0.38, yq + 0.004, 2.85],
                           [0.78, yq + 0.004, 2.85])                                           # control box door
        if lod == 0:                             # front: corner posts, two uprights, coupling heads, marker lights
            yf = L + (0.42 if kind == "reefer" else 0.0)
            for x in (-hw + 0.04, hw - 0.04, -0.45, 0.45):
                bx(m, "trailer_alu", x - 0.04, x + 0.04, L - 0.02, L + 0.025, zf, H - 0.02)
            bx(m, "trailer_chassis", -hw + 0.02, hw - 0.02, L - 0.02, L + 0.03, zf - 0.05, zf + 0.22)
            for x, mat in ((-0.35, "coupling_red"), (-0.15, "coupling_yellow")):
                bx(m, mat, x - 0.05, x + 0.05, L - 0.3, L - 0.15, zf - 0.22, zf - 0.1)
            bx(m, "car_trim", 0.05, 0.25, L - 0.3, L - 0.15, zf - 0.24, zf - 0.08)          # electrical socket
            for sx in (-1, 1):
                m.quad("car_light_head", [sx * (hw - 0.12) - 0.05, yf + 0.03, H - 0.25],
                       [sx * (hw - 0.12) + 0.05, yf + 0.03, H - 0.25],
                       [sx * (hw - 0.12) + 0.05, yf + 0.03, H - 0.17], [sx * (hw - 0.12) - 0.05, yf + 0.03, H - 0.17])
        # rear frame + doors (seen from the dock: dark gap between the leaves), lights, under-run bar
        bx(m, "trailer_alu", -hw - 0.02, hw + 0.02, -0.06, 0.06, zf - 0.08, zf + 0.04)
        bx(m, "trailer_doors", -hw + 0.04, hw - 0.04, -0.04, 0.02, zf, H - 0.08)
        bx(m, "trailer_chassis", -1.10, 1.10, -0.15, -0.05, 0.42, 0.56)                    # under-run bar
        if lod == 0:
            for sx in (-1, 1):
                for x in (sx * 0.62, sx * 0.30):
                    m.tube("trailer_alu", [x, -0.06, zf + 0.1], [x, -0.06, H - 0.2], 0.018, None, 6)
                bx(m, "trailer_alu", sx * hw - 0.08, sx * hw, -0.07, -0.04, zf, H - 0.08)    # corner posts
                m.quad("car_light_tail", [sx * 0.95 + 0.17, -0.155, 0.62], [sx * 0.95 - 0.17, -0.155, 0.62],
                       [sx * 0.95 - 0.17, -0.155, 0.74], [sx * 0.95 + 0.17, -0.155, 0.74])
                m.quad("reflector_red", [sx * 1.15 + 0.04, -0.155, 0.85], [sx * 1.15 - 0.04, -0.155, 0.85],
                       [sx * 1.15 - 0.04, -0.155, 0.95], [sx * 1.15 + 0.04, -0.155, 0.95])
            m.quad("trailer_strap", [0.012, -0.045, zf + 0.05], [-0.012, -0.045, zf + 0.05],
                   [-0.012, -0.045, H - 0.12], [0.012, -0.045, H - 0.12])
            q = [[-0.26, -0.157, 0.62], [0.26, -0.157, 0.62], [0.26, -0.157, 0.73], [-0.26, -0.157, 0.73]]
            m.add("plate_pl", [q[1], q[0], q[3], q[2]], [(0, 1, 2), (0, 2, 3)], [[1, 0], [0, 0], [0, 1], [1, 1]])
        # chassis: two main beams, side under-run guards, landing legs, kingpin plate
        for sx in (-1, 1):
            bx(m, "trailer_chassis", sx * 0.52 - 0.06, sx * 0.52 + 0.06, 0.2, L - 0.2, zf - 0.42, zf - 0.05)
            if lod == 0:
                bx(m, "trailer_alu", sx * (hw - 0.05) - 0.02, sx * (hw - 0.05) + 0.02, 6.4, 11.0, 0.55, 0.62)
                bx(m, "trailer_alu", sx * (hw - 0.05) - 0.02, sx * (hw - 0.05) + 0.02, 6.4, 11.0, 0.80, 0.87)
            # landing gear (r11, review 2026-11-10 A4 "klockowate nogi"): 110 mm outer leg + 90 mm inner leg, sand
            # shoe 0.24 x 0.28 m, diagonal braces to the beam, cross shaft and the crank on the right side
            leg_x = sx * 0.92
            bx(m, "trailer_chassis", leg_x - 0.055, leg_x + 0.055, 11.47, 11.58, 0.52, zf - 0.14)
            bx(m, "trailer_alu", leg_x - 0.042, leg_x + 0.042, 11.483, 11.567, 0.05, 0.54)
            bx(m, "trailer_chassis", leg_x - 0.12, leg_x + 0.12, 11.385, 11.665, 0.0, 0.045)
            if lod == 0:
                m.tube("trailer_chassis", [leg_x, 11.50, 0.60], [leg_x, 10.72, zf - 0.20], 0.022, None, 4, cap=False)
                m.tube("trailer_chassis", [leg_x, 11.50, 0.62], [sx * 0.55, 11.50, zf - 0.20], 0.022, None, 4, cap=False)
                # mudguards over the axle group (three quarter shells approximated by a bent strip)
                xw = sx * (hw - 0.27)
                for ya in TRAILER_AXLES:
                    # seen from outside / above only (the tyre fills the inside): single-sided, 3 strips
                    pts = [(ya - 0.62, 0.80), (ya - 0.36, 1.12), (ya + 0.36, 1.12), (ya + 0.62, 0.80)]
                    for (y0, z0), (y1, z1) in zip(pts[:-1], pts[1:]):
                        m.quad("trailer_chassis", [xw + 0.21, y0, z0], [xw - 0.21, y0, z0], [xw - 0.21, y1, z1], [xw + 0.21, y1, z1])
                bx(m, "trailer_chassis", xw - 0.2, xw + 0.2, TRAILER_AXLES[0] - 0.66, TRAILER_AXLES[0] - 0.645, 0.20, 0.74)   # flap
                # amber side marker lamps along the bottom rail (ECE R48: every <= 3 m)
                for y in np.arange(1.0, L - 0.5, 2.9):
                    x = sx * (hw + 0.024)
                    q = [[x, y - 0.05, zf - 0.02], [x, y + 0.05, zf - 0.02], [x, y + 0.05, zf + 0.03], [x, y - 0.05, zf + 0.03]]
                    m.quad("coupling_yellow", *(q if sx > 0 else q[::-1]))
            # road film on the lower third of the body sides (blend overlay, car_dirt: dense at the bottom edge,
            # thinning upward). LOD0 only: it is the one extra submesh (= draw) the r11 detail costs per prototype; every
            # other new part reuses a material the trailer already has (Low budget, review 2026-11-10)
            # r12 (ADR 0092, review s9 "firanka odbija jak polerowana blacha"): on a CURTAIN the film is gone. It was a
            # 1.37 m high blended sheet in a pale grey-brown, dense over its lower 0.85-1.25 m, drawn with URP Lit
            # (sky SH without the baked sky visibility of Kamion/World PBR): in the shade of the hall it came out
            # lighter and warmer than the dark tarpaulin under it, with a dark ragged upper edge - a "reflection" of
            # the sunlit yard and the horizon. The curtain set already carries road grime on its lower third. Box
            # bodies keep a lower film (0.85 m: dense to ~0.55 m).
            if lod == 0 and kind != "curtain":
                x = sx * (hw + 0.028)
                q = [[x, 0.1, zf - 0.12], [x, L - 0.1, zf - 0.12], [x, L - 0.1, zf + 0.73], [x, 0.1, zf + 0.73]]
                uvq = [[0, 0], [3, 0], [3, 1], [0, 1]]
                m.add("car_dirt_3", q if sx > 0 else q[::-1], [(0, 1, 2), (0, 2, 3)], uvq if sx > 0 else uvq[::-1])
        if lod == 0:
            m.tube("trailer_alu", [-0.92, 11.525, 0.78], [0.92, 11.525, 0.78], 0.018, None, 4, cap=False)   # cross shaft
            m.tube("trailer_alu", [1.0, 11.525, 0.78], [1.21, 11.525, 0.78], 0.014, None, 4, cap=False)     # crank
            m.tube("trailer_alu", [1.21, 11.525, 0.78], [1.21, 11.36, 0.60], 0.014, None, 4, cap=False)
            bx(m, "trailer_chassis", 1.19, 1.23, 11.30, 11.37, 0.55, 0.61)                                # crank handle
            # pallet box (left) and spare wheel in a carrier (right) between the legs and the axle group
            bx(m, "trailer_chassis", -hw + 0.06, -hw + 0.70, 7.2, 9.6, 0.50, zf - 0.16)
            m.quad("trailer_alu", [-hw + 0.055, 9.55, 0.55], [-hw + 0.055, 7.25, 0.55], [-hw + 0.055, 7.25, zf - 0.21],
                   [-hw + 0.055, 9.55, zf - 0.21])                                                # lid
            m.tube("tyre", [0.35, 8.4, 0.52], [0.35, 8.4, 0.80], 0.50, None, 8)                    # spare wheel, lying flat
            # front bulkhead: document box, registration plate holder, two reflectors, spiral-hose bracket
            bx(m, "trailer_alu", -1.02, -0.70, L + 0.025, L + 0.065, zf + 0.40, zf + 0.64)
            for sx in (-1, 1):
                q = [[sx * (hw - 0.2) - 0.05, L + 0.031, zf + 0.12], [sx * (hw - 0.2) + 0.05, L + 0.031, zf + 0.12],
                     [sx * (hw - 0.2) + 0.05, L + 0.031, zf + 0.22], [sx * (hw - 0.2) - 0.05, L + 0.031, zf + 0.22]]
                m.quad("car_light_head", *q[::-1])
            for x in (-0.35, -0.15):
                m.tube("trailer_chassis", [x, L + 0.04, zf + 0.28], [x, L + 0.10, zf - 0.12], 0.016, None, 4, cap=False)   # hoses
        bx(m, "trailer_chassis", -hw + 0.1, hw - 0.1, 2.3, 6.4, zf - 0.30, zf - 0.05)         # axle bed
        for ya in TRAILER_AXLES:
            for sx in (-1, 1):
                wheel(m, [sx * (hw - 0.27), ya, 0.535], 0.535, 0.385, 10, out_sign=sx,
                      simple=lod > 0, rim="rim" if lod == 0 else "trailer_alu")
        out.append(m)
    col = Mesh()
    col.box("collision_vehicle", [0, L / 2, (H + 0.2) / 2], hw, L / 2, (H - 0.2) / 2 + 0.1)
    return out[0], out[1], col


# ------------------------------------------------------------------------------------------- yard props
# ------------------------------------------------------------------------------------------- tractor unit
TRACTOR = dict(wb=3.70, fh=1.45, cab_l=2.30, W=2.49, H=3.85, floor=1.30, fw_ahead=0.55, rear_oh=1.05)  # WORKING_VALUE
TRACTOR_SILL_Z = 1.05           # actual lowest cab-shell row; UV1 film frame (ADR 0122)
TRAILER_KINGPIN = 12.40          # rear edge -> kingpin of the 13.6 m trailer (WORKING_VALUE)


def _plan(hw, y0, y1, rf, rr, n=3):
    """Rounded-rectangle plan section (x, y), CCW seen from above: front corners radius rf, rear rr."""
    pts = []
    for cx, cy, r, a0 in ((hw - rr, y0 + rr, rr, -90), (hw - rf, y1 - rf, rf, 0), (-hw + rf, y1 - rf, rf, 90),
                          (-hw + rr, y0 + rr, rr, 180)):
        for k in range(n):
            a = math.radians(a0 + 90 * k / (n - 1))
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return np.array(pts)


def vloft(m, mat, sections, zs, cap=True):
    """Loft of CCW plan sections stacked along z (outward faces) + top cap."""
    k = len(sections[0])
    V = [[x, y, z] for sec, z in zip(sections, zs) for x, y in sec]
    T = []
    for i in range(len(zs) - 1):
        for j in range(k):
            a, b = i * k + j, i * k + (j + 1) % k
            T += [(a, b, b + k), (a, b + k, a + k)]
    m.add(mat, V, T, [[v[1], v[2]] for v in V])
    if cap:
        c = np.mean(sections[-1], axis=0)
        Vc = [[c[0], c[1], zs[-1]]] + [[x, y, zs[-1]] for x, y in sections[-1]]
        m.add(mat, Vc, [(0, 1 + j, 1 + (j + 1) % k) for j in range(k)], [[v[0], v[1]] for v in Vc])


def tractor(colour):
    """Generic 4x2 cab-over tractor (v3.1 silhouette), origin under the fifth wheel, +y forward. Dimensions typical
    for the class (WORKING_VALUE); deliberately brand-less: raked windscreen, rounded cab corners, medium roof with a
    roof deflector (owiewka dachowa) and cab side extenders, black grille panel without any badge, fuel tank and
    battery box between the axles, steps behind the front wheel, rear mudguards, mirrors. LOD0 <= 1.5 k triangles,
    LOD1 ~ 300 (props_meta.json)."""
    t = TRACTOR
    paint = f"tractor_paint_{colour}"
    hw = t["W"] / 2
    y_ra = -t["fw_ahead"]                      # rear axle
    y_fa = y_ra + t["wb"]                      # front axle
    y_front = y_fa + t["fh"]
    y_cab0 = y_front - t["cab_l"]
    z_roof, z_defl = 3.30, t["H"]
    out = []
    for lod in (0, 1):
        m = Mesh()
        n = 3 if lod == 0 else 2
        # cab: plan sections from the cab floor to the roof; the windscreen is raked back, roof edge rounded
        rows = [(TRACTOR_SILL_Z, 0.0, 0.0, 0.16), (2.05, 0.0, 0.0, 0.18), (3.00, 0.20, 0.02, 0.22), (3.20, 0.32, 0.06, 0.26),
                (z_roof, 0.50, 0.16, 0.26)]
        if lod:
            rows = [rows[0], rows[1], rows[2], rows[4]]
        secs = [_plan(hw - dx, y_cab0 + (0.0 if z < 3.1 else dx), y_front - dy, rf, 0.06, n) for z, dy, dx, rf in rows]
        vloft(m, paint, secs, [r[0] for r in rows])

        def yf(z):                             # front face y at height z (windscreen rake)
            return y_front - 0.20 * min(max((z - 2.05) / 0.95, 0.0), 1.0)
        # windscreen + side windows (just proud of the body)
        m.quad("car_glass", [hw - 0.16, yf(2.10) + 0.012, 2.10], [-hw + 0.16, yf(2.10) + 0.012, 2.10],
               [-hw + 0.20, yf(2.95) + 0.012, 2.95], [hw - 0.20, yf(2.95) + 0.012, 2.95])
        for sx in (-1, 1):
            q = [[sx * (hw + 0.005), y_front - 0.95, 2.12], [sx * (hw + 0.005), y_front - 0.22, 2.12],
                 [sx * (hw - 0.012), y_front - 0.34, 2.88], [sx * (hw - 0.012), y_front - 0.95, 2.88]]
            m.quad("car_glass", *(q if sx > 0 else q[::-1]))
        # roof deflector: wedge from the roof (0.8 m behind the front) up to z_defl at the cab rear
        yd0, yd1 = y_front - 0.85, y_cab0 + 0.04
        wf, wr = hw - 0.30, hw - 0.10
        A, B = [wf, yd0, z_roof - 0.02], [-wf, yd0, z_roof - 0.02]
        C, D = [-wr, yd1, z_defl], [wr, yd1, z_defl]
        E, F = [-wr, yd1, z_roof - 0.02], [wr, yd1, z_roof - 0.02]
        m.quad(paint, A, B, C, D)                                   # sloped front face
        m.quad(paint, D, C, E, F)                                   # rear face
        m.add(paint, [A, D, F], [(0, 1, 2)])                        # sides
        m.add(paint, [B, E, C], [(0, 1, 2)])
        # cab side extenders behind the cab (paint), front bumper, grille panel, lights
        for sx in (-1, 1):
            bx(m, paint, sx * (hw - 0.03) - 0.015, sx * (hw - 0.03) + 0.015, y_cab0 - 0.32, y_cab0, 1.50, 3.55)
        bx(m, "car_trim", -hw + 0.04, hw - 0.04, y_front - 0.30, y_front + 0.06, 0.38, 0.82)        # bumper
        bx(m, paint, -hw + 0.10, hw - 0.10, y_front - 0.35, y_front + 0.01, 0.82, 1.06)              # lower panel
        m.quad("car_trim", [hw - 0.32, y_front + 0.004, 1.12], [-hw + 0.32, y_front + 0.004, 1.12],
               [-hw + 0.32, y_front + 0.004, 1.92], [hw - 0.32, y_front + 0.004, 1.92])            # grille (no badge)
        for sx in (-1, 1):
            x0 = sx * (hw - 0.30)
            m.quad("car_light_head", [x0 + 0.22, y_front + 0.065, 0.62], [x0 - 0.22, y_front + 0.065, 0.62],
                   [x0 - 0.22, y_front + 0.065, 0.76], [x0 + 0.22, y_front + 0.065, 0.76])
        if lod == 0:
            bx(m, paint, -hw + 0.08, hw - 0.08, yf(3.0) - 0.05, yf(3.0) + 0.14, 2.98, 3.04)          # sun visor
            q = [[0.26, y_front + 0.065, 0.45], [-0.26, y_front + 0.065, 0.45], [-0.26, y_front + 0.065, 0.56],
                 [0.26, y_front + 0.065, 0.56]]
            m.add("plate_pl", q, [(0, 1, 2), (0, 2, 3)], [[0, 0], [1, 0], [1, 1], [0, 1]])
            for sx in (-1, 1):
                # mirror arm + head (camera-mirror free, classic glass mirror housing)
                bx(m, "car_trim", sx * hw, sx * (hw + 0.26), y_front - 0.30, y_front - 0.26, 2.62, 2.66)
                bx(m, "car_trim", sx * (hw + 0.22), sx * (hw + 0.32), y_front - 0.36, y_front - 0.22, 2.20, 2.72)
                # steps under the door, behind the front wheel
                bx(m, "car_trim", sx * (hw - 0.30), sx * (hw - 0.02), y_cab0 + 0.02, y_fa - 0.62, 0.45, 1.05)
                # front mudguard lip over the wheel
                bx(m, "car_trim", sx * (hw - 0.38), sx * (hw - 0.02), y_fa - 0.60, y_fa + 0.62, 1.02, 1.07)
        # chassis rails, rear crossmember, fifth wheel
        for sx in (-1, 1):
            bx(m, "trailer_chassis", sx * 0.43 - 0.05, sx * 0.43 + 0.05, y_ra - t["rear_oh"], y_cab0 + 0.3, 0.75, 1.05)
        bx(m, "trailer_chassis", -0.55, 0.55, y_ra - t["rear_oh"], y_ra - t["rear_oh"] + 0.12, 0.50, 1.05)
        if lod == 0:
            m.tube("trailer_chassis", [0, 0, 1.05], [0, 0, 1.20], 0.88, 0.88, 14)                    # fifth wheel
            for sx in (-1, 1):                                       # rear lights on the crossmember
                m.quad("car_light_tail", [sx * 0.75 - 0.14, y_ra - t["rear_oh"] - 0.005, 0.70],
                       [sx * 0.75 + 0.14, y_ra - t["rear_oh"] - 0.005, 0.70],
                       [sx * 0.75 + 0.14, y_ra - t["rear_oh"] - 0.005, 0.82],
                       [sx * 0.75 - 0.14, y_ra - t["rear_oh"] - 0.005, 0.82])
            # fuel tank (right) and battery / air-tank box (left) between the axles; AdBlue tank behind it
            m.tube("rim", [hw - 0.40, y_cab0 - 0.10, 0.80], [hw - 0.40, y_cab0 - 1.55, 0.80], 0.31, None, 12)
            bx(m, "trailer_chassis", -hw + 0.12, -hw + 0.58, y_cab0 - 1.25, y_cab0 - 0.10, 0.52, 1.08)
            m.tube("car_trim", [-hw + 0.35, y_cab0 - 1.35, 0.80], [-hw + 0.35, y_cab0 - 1.75, 0.80], 0.22, None, 8)
        else:
            bx(m, "trailer_chassis", -0.85, 0.85, -0.85, 0.85, 1.05, 1.18)
            bx(m, "rim", hw - 0.70, hw - 0.10, y_cab0 - 1.55, y_cab0 - 0.10, 0.50, 1.10)
        # rear mudguards (top + rear flap)
        for sx in (-1, 1):
            bx(m, "car_trim", sx * (hw - 0.62), sx * (hw - 0.02), y_ra - 0.62, y_ra + 0.62, 1.12, 1.16)
            if lod == 0:
                bx(m, "rubber_black", sx * (hw - 0.62), sx * (hw - 0.02), y_ra - 0.66, y_ra - 0.63, 0.30, 1.14)
        for ya, wdt in ((y_fa, 0.32), (y_ra, 0.62)):
            for sx in (-1, 1):
                wheel(m, [sx * (hw - 0.18 - (0.12 if wdt > 0.5 else 0.0)), ya, 0.51], 0.51, wdt, 14 if lod == 0 else 6,
                      out_sign=sx, simple=lod > 0)
        out.append(_paint_uv(m))
    col = Mesh()
    col.box("collision_vehicle", [0, (y_ra - t["rear_oh"] + y_front) / 2, t["H"] / 2], hw,
            (y_front - y_ra + t["rear_oh"]) / 2, t["H"] / 2)
    return out[0], out[1], col


def tractor_extent():
    """(rear, front) of the tractor along +y relative to its origin (fifth wheel)."""
    t = TRACTOR
    return -t["fw_ahead"] - t["rear_oh"], -t["fw_ahead"] + t["wb"] + t["fh"]


# ------------------------------------------------------------------------------------------- container
CONTAINER_L = {20: 6.058, 40: 12.192}
CONTAINER_W, CONTAINER_H = 2.438, 2.591


def container(ft, colour):
    L, W, H = CONTAINER_L[ft], CONTAINER_W, CONTAINER_H
    hl, hw = L / 2, W / 2
    mat = f"container_{colour}"
    out = []
    for lod in (0, 1):
        m = Mesh()
        for sx in (-1, 1):                      # corrugated side walls (UV u = metres along)
            q = [[sx * hw, -hl + 0.15, 0.15], [sx * hw, hl - 0.15, 0.15], [sx * hw, hl - 0.15, H - 0.12],
                 [sx * hw, -hl + 0.15, H - 0.12]]
            m.add(mat, q if sx > 0 else q[::-1], [(0, 1, 2), (0, 2, 3)],
                  [[0, 0], [L, 0], [L, H], [0, H]] if sx > 0 else [[L, 0], [0, 0], [0, H], [L, H]])
        bx(m, mat, -hw + 0.02, hw - 0.02, -hl, hl, H - 0.12, H)
        bx(m, "container_frame", -hw, hw, -hl, hl, 0.0, 0.15)
        bx(m, mat, -hw + 0.02, hw - 0.02, hl - 0.15, hl, 0.15, H - 0.12)
        bx(m, "container_doors" if lod == 0 else mat, -hw + 0.02, hw - 0.02, -hl, -hl + 0.15, 0.15, H - 0.12)
        if lod == 0:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    x0, x1 = (hw - 0.16, hw) if sx > 0 else (-hw, -hw + 0.16)
                    y0, y1 = (hl - 0.16, hl) if sy > 0 else (-hl, -hl + 0.16)
                    bx(m, "container_frame", x0 - 0.005 * sx, x1 + 0.005 * sx, y0, y1, 0.0, H + 0.005)
            for x in (-0.62, -0.2, 0.2, 0.62):
                m.tube("container_frame", [x, -hl - 0.03, 0.25], [x, -hl - 0.03, H - 0.2], 0.018, None, 5)
        out.append(m)
    col = Mesh()
    col.box("collision_vehicle", [0, 0, H / 2], hw, hl, H / 2)
    return out[0], out[1], col


def pallets_empty(n):
    h = 0.144 * n
    out = []
    for lod in (0, 1):
        m = Mesh()
        # one box per pallet (slight jitter: real stacks are never perfectly aligned), UV v = metres
        rnd = np.random.default_rng(n)
        for i in range(n if lod == 0 else 1):
            dx, dy = (rnd.uniform(-0.03, 0.03, 2) if lod == 0 else (0.0, 0.0))
            z0 = i * 0.144 if lod == 0 else 0.0
            z1 = z0 + (0.144 if lod == 0 else h)
            m.box("pallet_wood", [dx, dy, (z0 + z1) / 2], 0.6, 0.4, (z1 - z0) / 2 - (0.001 if lod == 0 else 0))
        out.append(m)
    col = Mesh()
    col.box("collision_steel", [0, 0, h / 2], 0.6, 0.4, h / 2)
    return out[0], out[1], col


def pallet_load():
    out = []
    for lod in (0, 1):
        m = Mesh()
        m.box("pallet_wood", [0, 0, 0.072], 0.6, 0.4, 0.072)
        m.box("pallet_foil", [0, 0, 0.144 + 0.6], 0.59, 0.39, 0.6)
        if lod == 0:
            m.box("cardboard", [0.0, 0.0, 1.30], 0.5, 0.33, 0.06)
        out.append(m)
    col = Mesh()
    col.box("collision_steel", [0, 0, 0.7], 0.6, 0.4, 0.7)
    return out[0], out[1], col


def bin_1100(colour):
    mat = f"bin_plastic_{colour}"
    out = []
    for lod in (0, 1):
        m = Mesh()
        # body tapers toward the bottom; lid with an overhang
        secs = [np.array([(-0.62, 0.0), (0.62, 0.0)]), None]
        W0, D0, W1, D1, z0, z1 = 1.20, 0.92, 1.30, 1.02, 0.18, 1.22
        V = []
        for (w, d, z) in ((W0, D0, z0), (W1, D1, z1)):
            V += [[-w / 2, -d / 2, z], [w / 2, -d / 2, z], [w / 2, d / 2, z], [-w / 2, d / 2, z]]
        T = [(0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7), (0, 3, 2), (0, 2, 1)]
        m.add(mat, V, T)
        m.box(mat, [0, 0.0, 1.27], 0.67, 0.55, 0.05)
        if lod == 0:
            m.box(mat, [0, 0.0, 1.38], 0.62, 0.30, 0.07)          # lid ridge
            for sx in (-1, 1):
                for sy in (-1, 1):
                    m.tube("rubber_black", [sx * 0.5 - 0.03, sy * 0.36, 0.09], [sx * 0.5 + 0.03, sy * 0.36, 0.09], 0.09,
                           None, 8)
                m.box("steel_galv", [sx * 0.68, 0.0, 1.0], 0.02, 0.3, 0.02)       # side trunnions
            del secs
        else:
            m.box("rubber_black", [0, 0, 0.09], 0.55, 0.4, 0.09)
        out.append(m)
    col = Mesh()
    col.box("collision_steel", [0, 0, 0.7], 0.67, 0.55, 0.7)
    return out[0], out[1], col


def skip_kp7():
    out = []
    for lod in (0, 1):
        m = Mesh()
        Lb, Lt, W, H = 3.0, 3.9, 1.75, 1.45
        V = [[-W / 2, -Lb / 2, 0.08], [W / 2, -Lb / 2, 0.08], [W / 2, Lb / 2, 0.08], [-W / 2, Lb / 2, 0.08],
             [-W / 2, -Lt / 2, H], [W / 2, -Lt / 2, H], [W / 2, Lt / 2, H], [-W / 2, Lt / 2, H]]
        # outer walls + bottom, inner walls (open top), rim
        T = [(0, 1, 5), (0, 5, 4), (1, 2, 6), (1, 6, 5), (2, 3, 7), (2, 7, 6), (3, 0, 4), (3, 4, 7), (0, 3, 2), (0, 2, 1)]
        m.add("skip_paint", V, T, [[v[1], v[2]] for v in V])
        Vi = [[v[0] * 0.97, v[1] * 0.98, v[2] + (0.05 if v[2] < 1 else -0.02)] for v in V]
        Ti = [(a, c, b) for a, b, c in T]
        m.add("skip_inside", Vi, Ti)
        if lod == 0:
            for sx in (-1, 1):
                for y in (-0.9, 0.9):
                    m.tube("skip_paint", [sx * W / 2, y, 1.05], [sx * (W / 2 + 0.12), y, 1.05], 0.05, None, 6)
                bx(m, "skip_paint", sx * W / 2 - 0.05, sx * W / 2 + 0.05, -Lb / 2, Lb / 2, 0.0, 0.10)
            for y in np.linspace(-1.2, 1.2, 4):
                for sx in (-1, 1):
                    bx(m, "skip_paint", sx * W / 2, sx * (W / 2 + 0.03), y - 0.04, y + 0.04, 0.12, H - 0.05)
            bx(m, "rubble", -W / 2 + 0.1, W / 2 - 0.1, -Lb / 2 + 0.2, Lb / 2 - 0.2, 0.1, 0.7)
        out.append(m)
    col = Mesh()
    col.box("collision_steel", [0, 0, 0.75], 0.9, 1.95, 0.75)
    return out[0], out[1], col


def cone():
    out = []
    for lod in (0, 1):
        m = Mesh()
        seg = 12 if lod == 0 else 6
        m.box("cone_base", [0, 0, 0.02], 0.2, 0.2, 0.02)
        m.tube("cone_orange", [0, 0, 0.04], [0, 0, 0.75], 0.15, 0.025, seg)
        if lod == 0:
            for z0, z1 in ((0.38, 0.48), (0.56, 0.63)):
                r0 = 0.15 - (0.125 * (z0 - 0.04) / 0.71)
                r1 = 0.15 - (0.125 * (z1 - 0.04) / 0.71)
                m.tube("paint_white_reflective", [0, 0, z0], [0, 0, z1], r0 + 0.003, r1 + 0.003, seg, cap=False)
        out.append(m)
    return out[0], out[1], None


# ------------------------------------------------------------------------------------------- gate kit
def gatehouse():
    """Container booth 3.6 x 2.4 m, 2.7 m high on a 0.15 m plinth; glazed front (+y) and ends."""
    Wx, Dy, H = 3.6, 2.4, 2.7
    m, l1, col = Mesh(), Mesh(), Mesh()
    for mm, lod in ((m, 0), (l1, 1)):
        bx(mm, "concrete_base", -Wx / 2 - 0.1, Wx / 2 + 0.1, -Dy / 2 - 0.1, Dy / 2 + 0.1, -0.2, 0.15)
        z0 = 0.15
        # back wall, side walls (panels), front: spandrel + glazing band + header
        bx(mm, "booth_panel", -Wx / 2, Wx / 2, -Dy / 2, -Dy / 2 + 0.08, z0, z0 + H)
        for sx in (-1, 1):
            bx(mm, "booth_panel", sx * Wx / 2 - 0.04, sx * Wx / 2 + 0.04, -Dy / 2, Dy / 2, z0, z0 + 1.0)
            bx(mm, "booth_panel", sx * Wx / 2 - 0.04, sx * Wx / 2 + 0.04, -Dy / 2, Dy / 2, z0 + 2.2, z0 + H)
            mm.quad("door_glass" if lod else "booth_glass",
                    *([[sx * (Wx / 2 + 0.01), -Dy / 2, z0 + 1.0], [sx * (Wx / 2 + 0.01), Dy / 2, z0 + 1.0],
                       [sx * (Wx / 2 + 0.01), Dy / 2, z0 + 2.2], [sx * (Wx / 2 + 0.01), -Dy / 2, z0 + 2.2]][::sx]))
        bx(mm, "booth_panel", -Wx / 2, Wx / 2, Dy / 2 - 0.08, Dy / 2, z0, z0 + 1.0)
        bx(mm, "booth_panel", -Wx / 2, Wx / 2, Dy / 2 - 0.08, Dy / 2, z0 + 2.2, z0 + H)
        mm.quad("booth_glass", [Wx / 2, Dy / 2 + 0.01, z0 + 1.0], [-Wx / 2, Dy / 2 + 0.01, z0 + 1.0],
                [-Wx / 2, Dy / 2 + 0.01, z0 + 2.2], [Wx / 2, Dy / 2 + 0.01, z0 + 2.2])
        mm.quad("booth_glass", [-Wx / 2, Dy / 2 + 0.01, z0 + 2.2], [Wx / 2, Dy / 2 + 0.01, z0 + 2.2],
                [Wx / 2, Dy / 2 + 0.01, z0 + 1.0], [-Wx / 2, Dy / 2 + 0.01, z0 + 1.0])
        # roof with a 0.4 m overhang (rain), fascia
        bx(mm, "hall_flashing", -Wx / 2 - 0.4, Wx / 2 + 0.4, -Dy / 2 - 0.3, Dy / 2 + 0.5, z0 + H, z0 + H + 0.18)
        if lod == 0:
            for x in np.linspace(-Wx / 2 + 0.6, Wx / 2 - 0.6, 3):      # window mullions
                bx(mm, "window_frame", x - 0.03, x + 0.03, Dy / 2, Dy / 2 + 0.04, z0 + 1.0, z0 + 2.2)
            bx(mm, "window_frame", -Wx / 2, Wx / 2, Dy / 2, Dy / 2 + 0.06, z0 + 0.96, z0 + 1.02)   # sill
            bx(mm, "door_steel", -Wx / 2 - 0.05, -Wx / 2, -Dy / 2 + 0.3, -Dy / 2 + 1.2, z0, z0 + 2.05)  # door (end)
            bx(mm, "cabinet_grey", Wx / 2 - 0.9, Wx / 2 - 0.2, -Dy / 2 - 0.32, -Dy / 2 - 0.08, z0 + 1.6, z0 + 2.15)  # A/C
            bx(mm, "steel_painted", -0.9, 0.9, Dy / 2 + 0.1, Dy / 2 + 0.16, z0 + H - 0.35, z0 + H - 0.05)  # sign rail
        if lod == 0:
            mm.quad("sign_facade_portiernia", [0.85, Dy / 2 + 0.17, z0 + H - 0.33], [-0.85, Dy / 2 + 0.17, z0 + H - 0.33],
                    [-0.85, Dy / 2 + 0.17, z0 + H - 0.07], [0.85, Dy / 2 + 0.17, z0 + H - 0.07])
    col.box("collision_building", [0, 0, (H + 0.15) / 2], Wx / 2, Dy / 2, (H + 0.15) / 2)
    return m, l1, col


BOOM_OPEN_DEG = 85.0       # raised boom (WORKING_VALUE; drives stop at 85-90 deg)


def _boom_tube(mm, p0, p1, r0, r1, seg):
    """Boom profile with UV u = metres along the boom (Mesh.tube maps the length to v and the circumference to u,
    which painted the `boom_red_white` bands lengthwise: one side of the boom red, the other white - seen in the
    r10a WorldC renders)."""
    mm.tube("gate_boom", p0, p1, r0, r1, seg, cap=False)
    uv = mm.prims["gate_boom"][2][-1]
    mm.prims["gate_boom"][2][-1] = uv[:, ::-1].copy()


def barrier_arm(L=6.0, raised=False):
    """Boom barrier: drive housing (0.4 x 0.35 x 1.05 m) at the origin, boom along +x at 0.95 m, rest post
    with a fork at the far end. The boom has UV u = metres (0.5 m red/white bands in the material).
    raised=True: boom up at BOOM_OPEN_DEG about the hinge (map audit MA-003: the booms have no collider, so a closed
    boom across the lane was driven through; the depot gate stands open in gameplay)."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    for mm, seg in ((m, 10), (l1, 5)):
        mm.box("concrete_base", [0, 0, -0.05], 0.35, 0.3, 0.1)
        mm.box("barrier_housing", [0, 0, 0.55], 0.2, 0.175, 0.5)
        mm.box("barrier_housing", [0, 0, 1.06], 0.22, 0.19, 0.02)
        p0 = np.array([0.15, 0.0, 0.95])
        if raised:
            a = math.radians(BOOM_OPEN_DEG)
            p1 = p0 + (L - 0.15) * np.array([math.cos(a), 0.0, math.sin(a)])
        else:
            p1 = np.array([L, 0.0, 0.95])
        _boom_tube(mm, p0, p1, 0.05, 0.04, seg)
        mm.tube("steel_painted", [L - 0.1, 0.0, 0.0], [L - 0.1, 0.0, 0.88], 0.04, None, max(4, seg // 2))
        mm.box("steel_painted", [L - 0.1, 0.0, 0.9], 0.08, 0.02, 0.04)
        if seg > 5:
            mm.box("concrete_base", [L - 0.1, 0.0, -0.05], 0.18, 0.18, 0.1)
            mm.tube("lamp_glass", [0, 0.18, 1.0], [0, 0.18, 1.05], 0.05, None, 8)       # flash lamp
    col.box("collision_steel", [0, 0, 0.55], 0.2, 0.175, 0.55)
    return m, l1, col


BOOM_HINGE = (0.0, 0.0, 0.95)      # hinge of barrier_boom in the frame of barrier_base (m)
BOOM_SIDE = 0.235                  # boom axis offset from the housing centre along prototype +y (m)
BOOM_L = 5.85                      # boom length from the hinge (6 m lane clear width class, WORKING_VALUE)


def barrier_base(L=BOOM_L):
    """Housing of an automatic boom barrier WITHOUT the boom (the boom is its own prototype `barrier_boom`, driven in
    the engine by Game.World.DepotBarrier; map audit MA-003): steel cabinet 0.40 x 0.35 x 1.05 m on a concrete
    footing with a base flange, service door with a lock, sloped cap, flashing beacon, boom bracket on the hinge
    shaft, and the rest post with a fork at the far end of the closed boom (+x). Shapes typical of Polish depot
    entrances, no product copied; sizes WORKING_VALUE."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    for mm, lod in ((m, 0), (l1, 1)):
        mm.box("concrete_base", [0, 0, -0.06], 0.30, 0.27, 0.12)      # footing inside the island kerb (gate._island)
        mm.box("barrier_housing", [0, 0, 0.555], 0.20, 0.175, 0.495)
        mm.box("barrier_housing", [0, 0, 1.065], 0.225, 0.20, 0.015)                  # cap overhang
        if lod == 0:
            mm.box("steel_galv", [0, 0, 0.07], 0.24, 0.215, 0.012)                    # base flange
            for sx in (-1, 1):
                for sy in (-1, 1):                                                    # anchor nuts
                    mm.tube("steel_galv", [sx * 0.215, sy * 0.19, 0.08], [sx * 0.215, sy * 0.19, 0.105], 0.014, None, 6)
            mm.box("barrier_housing", [0, -0.179, 0.56], 0.165, 0.004, 0.42)          # service door leaf (proud 4 mm)
            mm.box("steel_galv", [0.12, -0.186, 0.62], 0.012, 0.004, 0.03)            # lock
            mm.box("cabinet_grey", [0, 0, 1.095], 0.19, 0.165, 0.015)                 # top lid
            mm.tube("steel_painted", [0, 0, 1.11], [0, 0, 1.16], 0.03, None, 8)       # beacon base
            mm.tube("lamp_glass_sodium", [0, 0, 1.16], [0, 0, 1.25], 0.045, 0.035, 8)  # flashing beacon
            mm.tube("steel_galv", [0, -0.2, 0.95], [0, 0.26, 0.95], 0.03, None, 8)    # hinge shaft
            mm.box("steel_painted", [0.0, 0.235, 0.95], 0.11, 0.02, 0.07)             # boom bracket plate
            for z in (0.25, 0.85):                                                    # reflective bands on the cabinet
                mm.box("reflector_red", [0, 0, z], 0.202, 0.177, 0.03)
        # rest post with a fork
        # the housing may stand on a raised island (gate.ISLAND_H): the rest post across the lane reaches down to the
        # lane level and its footing sits there (buried when the housing is at ground level)
        mm.tube("steel_galv", [L - 0.25, 0.235, -0.30], [L - 0.25, 0.235, 0.84], 0.035, None, 8 if lod == 0 else 5)
        mm.box("steel_galv", [L - 0.25, 0.235, 0.85], 0.03, 0.075, 0.012)
        for sy in (-1, 1):
            mm.box("steel_galv", [L - 0.25, 0.235 + sy * 0.07, 0.92], 0.03, 0.008, 0.07)
        if lod == 0:
            mm.box("concrete_base", [L - 0.25, 0.235, -0.21], 0.18, 0.18, 0.1)
    col.box("collision_steel", [0, 0, 0.55], 0.2, 0.175, 0.55)
    return m, l1, col


def barrier_boom(L=BOOM_L):
    """Boom of `barrier_base` in the hinge frame: origin = hinge axis, boom along +x (UV u = metres: 0.5 m red/white
    bands of the material), octagonal 100 x 55 mm aluminium profile approximated by a tube, rubber edge underneath,
    red end cap, counter-lever stub behind the hinge. Instances carry "barrier" (L, open_deg, travel) and become a
    DepotBarrier in the engine; other renderers show the closed boom."""
    m, l1 = Mesh(), Mesh()
    y = 0.0                       # the instance is placed BOOM_SIDE to the side of the housing (gate.py)
    for mm, seg in ((m, 10), (l1, 5)):
        _boom_tube(mm, [-0.25, y, 0.0], [L, y, 0.0], 0.05, 0.045, seg)
        if seg > 5:
            mm.box("rubber_black", [L / 2 + 0.2, y, -0.06], L / 2 - 0.5, 0.012, 0.012)   # rubber edge
            mm.tube("reflector_red", [L, y, 0.0], [L + 0.03, y, 0.0], 0.05, None, seg)    # end cap
            mm.box("steel_painted", [-0.12, y, 0.0], 0.16, 0.035, 0.06)                   # clamp at the bracket
    return m, l1, None


def cantilever_gate(L=10.0, H=2.0):
    """Open cantilever sliding gate standing behind the fence: leaf from x=0 to x=-L (tail), steel frame with
    vertical bars and a bottom beam on two roller posts."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    for mm, lod in ((m, 0), (l1, 1)):
        bx(mm, "fence_anthracite", -L, 0, -0.05, 0.05, 0.12, 0.30)                  # bottom beam
        bx(mm, "fence_anthracite", -L, 0, -0.03, 0.03, H - 0.06, H)                 # top rail
        bx(mm, "fence_anthracite", -0.06, 0, -0.03, 0.03, 0.3, H)
        bx(mm, "fence_anthracite", -L, -L + 0.06, -0.03, 0.03, 0.3, H)
        if lod == 0:
            for x in (-L * 0.25, -L * 0.5, -L * 0.75):                               # intermediate uprights
                bx(mm, "fence_anthracite", x - 0.03, x + 0.03, -0.03, 0.03, 0.3, H)
        if True:                                                                       # infill: welded mesh
            mm.add("fence_anthracite_mesh", [[0, 0, 0.3], [-L, 0, 0.3], [-L, 0, H], [0, 0, H]], [(0, 1, 2), (0, 2, 3)],
                   [[0, 0], [L, 0], [L, H], [0, H]])
            mm.add("fence_anthracite_mesh", [[-L, 0, 0.3], [0, 0, 0.3], [0, 0, H], [-L, 0, H]], [(0, 1, 2), (0, 2, 3)],
                   [[L, 0], [0, 0], [0, H], [L, H]])
        for x in (-0.6, -3.4):                                                         # roller posts + concrete
            bx(mm, "fence_anthracite", x - 0.08, x + 0.08, 0.08, 0.24, 0.0, 0.42)
            bx(mm, "concrete_base", x - 0.4, x + 0.4, -0.25, 0.4, -0.2, 0.02)
        bx(mm, "fence_anthracite", 0.25, 0.37, -0.06, 0.06, 0.0, H + 0.1)           # catch post at the opening
        if lod == 0:
            bx(mm, "cabinet_grey", -1.4, -0.9, 0.22, 0.52, 0.0, 0.45)                 # drive motor
    col.box("collision_fence", [-L / 2, 0, H / 2], L / 2, 0.06, H / 2)
    return m, l1, col


def facade_sign(code):
    """Fascia board: 0.06 m deep box, face (+y) carries the lettering texture; width from the text length."""
    w, h = sign_size(code)
    m = Mesh()
    m.box("steel_painted", [0, -0.03, 0], w / 2 + 0.04, 0.03, h / 2 + 0.04)
    m.quad(f"sign_facade_{code}", [-w / 2, 0.002, -h / 2], [w / 2, 0.002, -h / 2], [w / 2, 0.002, h / 2],
           [-w / 2, 0.002, h / 2])
    return m, m, None


def sign_size(code):
    text = SIGNS[code]
    h = 0.9 if code.startswith("hala") else 0.55
    return round(max(1.4, 0.62 * h * len(text) + 0.6 * h), 2), h


def sign_texture(code):
    """Lettering on a plain board (white on graphite for halls, dark on white for offices)."""
    from PIL import Image, ImageDraw
    from .signs import _font
    w, h = sign_size(code)
    px = 64
    W, H = int(round(w / h * px)), px
    if code.startswith("hala"):
        bg, fg = (52, 56, 60), (236, 236, 232)
    else:
        bg, fg = (236, 236, 232), (36, 52, 74)
    S = 4                                          # supersample
    im = Image.new("RGB", (W * S, H * S), bg)
    d = ImageDraw.Draw(im)
    f = _font(int(H * S * 0.62))
    t = SIGNS[code]
    bb = d.textbbox((0, 0), t, font=f)
    d.text(((W * S - (bb[2] - bb[0])) / 2 - bb[0], (H * S - (bb[3] - bb[1])) / 2 - bb[1]), t, font=f, fill=fg)
    return im.resize((W, H), Image.LANCZOS)


def plate_texture():
    """Polish registration plate look-alike (white field, blue EU band, black characters). The character
    string is a fixed non-existent placeholder pattern (not a real registration)."""
    from PIL import Image, ImageDraw
    from .signs import _font
    W, H, S = 256, 54, 4
    im = Image.new("RGB", (W * S, H * S), (238, 238, 234))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 22 * S, H * S], fill=(0, 51, 153))
    d.rectangle([0, 0, W * S - 1, H * S - 1], outline=(30, 30, 30), width=2 * S)
    f = _font(int(H * S * 0.62))
    t = "BI 0X000"
    bb = d.textbbox((0, 0), t, font=f)
    d.text((28 * S + (W * S - 28 * S - (bb[2] - bb[0])) / 2 - bb[0], (H * S - (bb[3] - bb[1])) / 2 - bb[1]), t, font=f,
           fill=(20, 20, 20))
    return im.resize((W, H), Image.LANCZOS)


def build_all():
    P = {}
    for body in CARS:
        for c in CAR_COLOURS:
            P[f"car_{body}_{c}"] = car(body, c)
    for c in VAN_COLOURS:
        P[f"van_{c}"] = van(c)
    for k, c in enumerate(CURTAIN_COLOURS):
        P[f"trailer_curtain_{k}"] = trailer("curtain", c)
    P["trailer_box_0"] = trailer("box", None)
    for c in TRACTOR_COLOURS:
        P[f"tractor_{c}"] = tractor(c)
    for ft in (20, 40):
        for k, c in enumerate(CONTAINER_COLOURS):
            P[f"container_{ft}_{k}"] = container(ft, c)
    P["trailer_reefer_0"] = trailer("reefer", None)
    for n in (4, 8, 12, 16):
        P[f"pallets_empty_{n}"] = pallets_empty(n)
    P["pallet_load"] = pallet_load()
    for c in BIN_COLOURS:
        P[f"bin_1100_{c}"] = bin_1100(c)
    P["skip_kp7"] = skip_kp7()
    P["cone"] = cone()
    P["gatehouse"] = gatehouse()
    P["barrier_arm"] = barrier_arm()
    P["barrier_arm_raised"] = barrier_arm(raised=True)
    P["barrier_base"] = barrier_base()
    P["barrier_boom"] = barrier_boom()
    P["cantilever_gate"] = cantilever_gate()
    for code in SIGNS:
        P[f"facade_sign_{code}"] = facade_sign(code)
    return P


# ------------------------------------------------------------------------------------------- gantries, landmarks
GANTRIES = set()        # (span_m, height_dm) registered by streetscape.landmarks before export
LANDMARKS = {}          # name -> (height, base_d, top_d) registered by streetscape.landmarks


def sign_gantry(span, H):
    """Steel lattice sign gantry: two 0.6 x 0.6 m lattice columns at x = +-span/2 on concrete footings and a
    0.8 m deep lattice beam whose top is at H; +y = front (boards hang there). Typical Polish overhead-sign
    structure (CC0 photo, docs/REFERENCES.md); member sizes WORKING_VALUE."""
    m, l1 = Mesh(), Mesh()
    zb0, zb1 = H - 1.0, H
    for sx in (-1, 1):
        x = sx * span / 2
        for cx in (-0.3, 0.3):
            for cy in (-0.3, 0.3):
                m.tube("gantry_steel", [x + cx, cy, 0.25], [x + cx, cy, H], 0.05, None, 6, cap=False)
        for z in np.arange(0.6, H - 0.3, 1.2):                 # zig-zag lacing on the four faces
            for (a, b) in (((-0.3, -0.3), (0.3, -0.3)), ((0.3, -0.3), (0.3, 0.3)), ((0.3, 0.3), (-0.3, 0.3)),
                           ((-0.3, 0.3), (-0.3, -0.3))):
                m.tube("gantry_steel", [x + a[0], a[1], z], [x + b[0], b[1], z + 0.6], 0.025, None, 4, cap=False)
        bx(l1, "gantry_steel", x - 0.3, x + 0.3, -0.3, 0.3, 0.25, H)
    for cy in (-0.4, 0.4):
        for z in (zb0, zb1):
            m.tube("gantry_steel", [-span / 2, cy, z], [span / 2, cy, z], 0.06, None, 6, cap=False)
        xs = np.arange(-span / 2, span / 2 - 0.5, 1.0)
        for i, x in enumerate(xs):
            za, zb = (zb0, zb1) if i % 2 == 0 else (zb1, zb0)
            m.tube("gantry_steel", [x, cy, za], [x + 1.0, cy, zb], 0.025, None, 4, cap=False)
    bx(l1, "gantry_steel", -span / 2, span / 2, -0.4, 0.4, zb0, zb1)
    # no collider on the gantry itself: the Unity importer makes one box per prototype from its .col below 2.6 m,
    # which for two columns 16 m apart was a wall across the carriageway (route_start s = 1375 m). The columns'
    # colliders come with the separate `gantry_footing` instances (one per column, streetscape.landmarks).
    return m, l1, None


CANTILEVERS = set()     # (column side L/R, reach_m, height_dm) registered by streetscape.landmarks (form: cantilever)


def sign_cantilever(reach, H, mirror=False):
    """Single-column lattice sign cantilever (ADR 0069, Mapillary p37 2020: one 0.6 x 0.6 m lattice column in the
    gore / at the shoulder, a 0.8 m deep lattice arm over the lanes). Column at the origin, arm along local +x (-x when
    `mirror`, column left of travel) to `reach`, top of the arm at H; +y = front (boards hang there). Member sizes
    WORKING_VALUE (read off the photo against the 3.5 m lanes). LOD0: 4 chords + zig-zag lacing; LOD1: two boxes."""
    m, l1 = Mesh(), Mesh()
    d = -1.0 if mirror else 1.0
    zb0, zb1 = H - 0.8, H
    for cx in (-0.3, 0.3):
        for cy in (-0.3, 0.3):
            m.tube("gantry_steel", [cx, cy, 0.25], [cx, cy, H + 0.3], 0.05, None, 6, cap=False)
    for z in np.arange(0.6, H - 0.3, 1.2):
        for (a, b) in (((-0.3, -0.3), (0.3, -0.3)), ((0.3, -0.3), (0.3, 0.3)), ((0.3, 0.3), (-0.3, 0.3)),
                       ((-0.3, 0.3), (-0.3, -0.3))):
            m.tube("gantry_steel", [a[0], a[1], z], [b[0], b[1], z + 0.6], 0.025, None, 4, cap=False)
    bx(l1, "gantry_steel", -0.3, 0.3, -0.3, 0.3, 0.25, H + 0.3)
    x0 = 0.3
    for cy in (-0.35, 0.35):
        for z in (zb0, zb1):
            m.tube("gantry_steel", [d * x0, cy, z], [d * reach, cy, z], 0.055, None, 6, cap=True)
        xs = np.arange(x0, reach - 0.4, 0.9)
        for i, x in enumerate(xs):
            za, zb = (zb0, zb1) if i % 2 == 0 else (zb1, zb0)
            m.tube("gantry_steel", [d * x, cy, za], [d * min(x + 0.9, reach), cy, zb], 0.022, None, 4, cap=False)
    for x in np.arange(x0, reach, 1.8):                       # cross ties between the two arm planes
        m.tube("gantry_steel", [d * x, -0.35, zb1], [d * x, 0.35, zb1], 0.02, None, 4, cap=False)
    bx(l1, "gantry_steel", d * x0, d * reach, -0.35, 0.35, zb0, zb1)
    return m, l1, None


def gantry_footing():
    """Concrete footing of one gantry column (1.2 x 1.2 m, -0.3..0.25 m) with the column's collider (0.7 x 0.7 m up
    to 4 m)."""
    m, l1, col = Mesh(), Mesh(), Mesh()
    bx(m, "concrete_base", -0.6, 0.6, -0.6, 0.6, -0.3, 0.25)
    bx(l1, "concrete_base", -0.6, 0.6, -0.6, 0.6, -0.3, 0.25)
    col.box("collision_steel", [0, 0, 2.0], 0.35, 0.35, 2.0)
    return m, l1, col


def chimney(H, d0, d1):
    """Landmark chimney: tapered concrete shaft; the top third in alternating red / white bands (obstacle
    marking, 7 bands, WORKING_VALUE), a dark top rim."""
    out = []
    for lod, seg in ((0, 28), (1, 12)):
        m = Mesh()
        zt = H * 0.66
        r = lambda z: (d0 + (d1 - d0) * z / H) / 2
        m.tube("chimney_concrete", [0, 0, -1.0], [0, 0, zt], r(0) + 0.01, r(zt), seg, cap=False)
        nb = 7
        for k in range(nb):
            z0 = zt + (H - zt) * k / nb
            z1 = zt + (H - zt) * (k + 1) / nb
            m.tube("chimney_red" if (nb - 1 - k) % 2 == 0 else "chimney_white", [0, 0, z0], [0, 0, z1], r(z0), r(z1),
                   seg, cap=k == nb - 1)
        if lod == 0:
            m.tube("chimney_concrete", [0, 0, H - 0.6], [0, 0, H + 0.2], r(H) + 0.25, r(H) + 0.25, seg, cap=False)
            for z in (zt - 20.0, H - 8.0):                       # service galleries
                m.tube("gantry_steel", [0, 0, z], [0, 0, z + 0.15], r(z) + 0.9, r(z) + 0.9, seg, cap=True)
        out.append(m)
    return out[0], out[1], None


def build_registered():
    P = {}
    for span, hdm in sorted(GANTRIES):
        P[f"sign_gantry_{span}_{hdm}"] = sign_gantry(float(span), hdm / 10.0)
    for side, reach, hdm in sorted(CANTILEVERS):
        P[f"sign_cantilever_{side}{reach}_{hdm}"] = sign_cantilever(float(reach), hdm / 10.0, mirror=side == "L")
    if GANTRIES or CANTILEVERS:
        P["gantry_footing"] = gantry_footing()
    for name, (H, d0, d1) in sorted(LANDMARKS.items()):
        P[name] = chimney(H, d0, d1)
    return P


# ------------------------------------------------------------------------------------------- contact shadow (ADR 0050)
# Parameters of Kamion/World Vehicle Contact per vehicle prototype, in the Unity object frame of the instance
# (x right, z forward = generator +y; all slabs are centred on x = 0). Every value is a WORKING_VALUE read off the
# prototype geometry above: slab = the underside seen from the ground (half sizes grown by ~0.3 x height where sills,
# wheels, tanks or steps close the sides of the gap), tyre = tight contact core at the tread, sun box = the lower body
# that blocks the sun from the ground under / beside it when the instance casts no shadow (LOD1+, Low LOD0 > 12 m).
CONTACT_FADE = 0.30          # m, patch edge fade (the patch outline is never visible)
NO_AXLE = 1.0e4


def _cs(slab0, slab1, strength, tyre, axles, sun_box, sun_z, margin):
    ax = list(axles) + [NO_AXLE] * (4 - len(axles))
    rects = [(slab0[0], slab0[2]), (slab1[0], slab1[2]), (sun_box[0], sun_box[2])] + [(a, tyre[2]) for a in axles]
    hx = max(slab0[1], slab1[1], sun_box[1], tyre[0] + tyre[1]) + margin
    z0 = min(c - h for c, h in rects) - margin
    z1 = max(c + h for c, h in rects) + margin

    def r(v):
        return [round(float(x), 4) for x in v]
    return {"slab0": r(slab0), "slab1": r(slab1), "strength": r(list(strength) + [0.0]), "tyre": r(tyre),
            "axles": r(ax), "sun_box": r(sun_box), "sun_z": r(sun_z),
            "patch": r([(z0 + z1) / 2, hx, (z1 - z0) / 2, CONTACT_FADE])}


def contact_spec(name):
    """Contact-shadow parameters (dict of 4-vectors) for a vehicle prototype name, None for anything else."""
    if name.startswith(("car_", "van_")):
        d = CARS[name.split("_")[1]] if name.startswith("car_") else VAN
        hw, L, sill, r = d["W"] / 2, d["L"], d["sill"], d["r"]
        h = sill + 0.04                                   # floor pan between the sills (sill = lowest body edge)
        yfa = L / 2 - d["foh"]
        return _cs([0.0, hw - 0.05 + 0.1 * h, L / 2 - 0.30, h],            # cabin floor between the sills
                   [0.0, hw - 0.25, L / 2 - 0.02, sill + 0.17],            # overhangs: bumper lower edges (taper)
                   (1.0, 0.75, 0.85),
                   [hw - 0.15, 0.10, 0.30 * r, 0.04],                     # tyre tread contact
                   (yfa, yfa - d["wb"]),
                   [0.0, hw - 0.04, L / 2 - 0.06, 1.0], [sill, d["belt"] - 0.05, 0.06, 0.06], 0.70)
    if name.startswith("tractor_"):
        t = TRACTOR
        hw = t["W"] / 2
        y_ra = -t["fw_ahead"]
        y_fa, y_rear = y_ra + t["wb"], y_ra - t["rear_oh"]
        y_front = y_fa + t["fh"]
        y_tank = y_front - t["cab_l"] - 1.75                # rear end of the tanks / battery box
        return _cs([(y_tank + y_front) / 2, hw + 0.10, (y_front - y_tank) / 2, 0.55],   # cab, steps, tanks, bumper
                   [(y_rear + y_tank) / 2, hw - 0.25, (y_tank - y_rear) / 2, 0.80],    # rails + fifth wheel, duals
                   (0.90, 0.65, 0.90),
                   [hw - 0.26, 0.22, 0.15, 0.05], (y_fa, y_ra),
                   [(y_rear + y_front) / 2, hw - 0.05, (y_front - y_rear) / 2, 0.80], [0.50, 1.20, 0.05, 0.05], 1.20)
    if name.startswith("trailer_"):
        L, hw, zf = TRAILER_L, TRAILER_W / 2, TRAILER_FLOOR
        a0, a1 = TRAILER_AXLES[0] - 0.75, TRAILER_AXLES[-1] + 0.75
        return _cs([L / 2, hw + 0.25, L / 2, zf - 0.20],                    # floor + main beams
                   [(a0 + a1) / 2, hw, (a1 - a0) / 2, 0.55],               # axle group: tyres close the sides
                   (0.90, 0.80, 0.90),
                   # 4th "axle" = the landing gear (r11, review A5: the legs stood "on" the texture): its sand shoes
                   # sit 8 cm inside the tyre line, close enough for the tyre contact core
                   [hw - 0.27, 0.19, 0.16, 0.05], (*TRAILER_AXLES, 11.525),
                   [L / 2, hw, L / 2, 0.95], [zf - 0.30, zf + 0.10, 0.05, 0.05], 1.60)
    # r11 (review A5): static yard props that rest on the ground get the same analytic contact / sun patch. One slab
    # just above the ground (the gap under a container between its corner castings, the plinth edge of the booth,
    # the footing of the barrier cabinet); no tyres.
    if name.startswith("container_"):
        hl, hw = CONTAINER_L[int(name.split("_")[1])] / 2, CONTAINER_W / 2
        return _cs([0.0, hw + 0.04, hl + 0.04, 0.16], [0.0, hw, hl, 0.5], (1.0, 0.35, 0.0),
                   [0.0, 0.01, 0.01, 0.05], (), [0.0, hw, hl, 1.0], [0.1, CONTAINER_H - 0.1, 0.05, 0.05], 1.40)
    if name == "gatehouse":
        return _cs([0.0, 1.9, 1.3, 0.14], [0.0, 1.8, 1.2, 0.5], (1.0, 0.35, 0.0),
                   [0.0, 0.01, 0.01, 0.05], (), [0.0, 1.8, 1.2, 1.0], [0.1, 2.7, 0.05, 0.05], 1.40)
    if name == "barrier_base":
        return _cs([0.0, 0.40, 0.35, 0.10], [0.0, 0.22, 0.2, 0.5], (1.0, 0.5, 0.0),
                   [0.0, 0.01, 0.01, 0.05], (), [0.0, 0.2, 0.175, 1.0], [0.05, 1.05, 0.03, 0.05], 0.60)
    return None


def contact_quad(m, spec):
    """Flat patch (material vehicle_contact) 1 cm over the ground plane covering spec['patch'] (generator frame)."""
    cz, hx, hz, _ = spec["patch"]
    z = 0.01
    m.quad("vehicle_contact", [-hx, cz - hz, z], [hx, cz - hz, z], [hx, cz + hz, z], [-hx, cz + hz, z])
