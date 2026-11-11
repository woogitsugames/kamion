"""Hero fire station JRG2 (Andersa 46) from a worldgen spec (ADR 0070, override kind: hero_building).

    blender -b --factory-startup -P tools/blender/world/landmarks/make_fire_station.py -- \
        --spec Data/Regions/bialystok-industrial-c/generated/landmarks/fire_station_jrg2.spec.json \
        [--render <abs dir>] [--blend]

Reads the spec written by tools/worldgen/streetscape/hero_building.py (authored dims.json, BDOT footprints, floor
level, ground heights under the fence / shrubs / poles) and writes art-source/world/landmarks/<asset>/<asset>.glb +
<asset>_meta.json:

  nodes  landmark_<asset>, .lod1, .lod2
  frame  vertices relative to the anchor (W corner of the main footprint, floor level); glTF (x, y, z) =
         (-dE, dU, dN) like street_props.glb, so the engine instance (yaw 0) at the anchor puts every vertex on its
         surveyed position
  UV0    fire_station: metres into the 14 x 14 m atlas (atlas_layout.json); fire_station_alpha: 0..1;
         hedge_thuja: metres

Everything is built from the spec (deterministic); nothing is modelled by hand. Building frame: u along the street
facade (to SE), v towards the yard (NE), z above the floor.
"""
import hashlib
import json
import math
import sys
from pathlib import Path

import bmesh
import bpy
import numpy as np

REPO = Path(__file__).resolve().parents[4]
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []


def arg(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default


SPEC_PATH = Path(arg("--spec"))
if not SPEC_PATH.is_absolute():
    SPEC_PATH = REPO / SPEC_PATH
SPEC = json.loads(SPEC_PATH.read_text(encoding="utf-8"))
ASSET = SPEC["asset"]
OUT = REPO / "art-source" / "world" / "landmarks" / ASSET
_lay = json.loads((OUT / "atlas_layout.json").read_text(encoding="utf-8"))
LAY, ALAY = _lay["atlas"], _lay["alpha"]
D = SPEC["dims"]
MAT, ALPHA, HEDGE, SHELL = "fire_station", "fire_station_alpha", "hedge_thuja", "hedge_shell_thuja"
HERO_SHELL = "fire_station_thuja_shell"
ANCHOR = np.array(SPEC["anchor"], float)
AX_O = np.array(D["axis"]["origin_en"], float)
AX_U = np.array(D["axis"]["u"], float)
AX_U /= np.linalg.norm(AX_U)
AX_V = np.array([-AX_U[1], AX_U[0]])
FLOOR = float(ANCHOR[2])
DZ = D.get("lod2_zmin_evrf2007", FLOOR - 0.45) - FLOOR        # LoD2-relative height -> height above the floor
PL_H = D["plinth_h_m"]
UP = np.array([0.0, 0.0, 1.0])


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def zl(z):
    return z + DZ


def h01(*k):
    return int(hashlib.sha1(repr(k).encode()).hexdigest()[:8], 16) / 0xFFFFFFFF


def en_to_uvz(p):
    d = np.array(p[:2], float) - AX_O
    return np.array([d @ AX_U, d @ AX_V, p[2] - FLOOR])


def P3(uv, z):
    return np.array([uv[0], uv[1], z], float)


def rect_uv(r):
    (u0, u1), (v0, v1) = r["u"], r["v"]
    return [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]


# ----------------------------------------------------------------------------------------------------- mesh soup
class MB:
    """Polygon soup in the building frame with per-corner UV and a material per face."""

    def __init__(self):
        self.V, self.F, self.UV, self.M = [], [], [], []
        self.core_normals = {}

    def face(self, P, UV, mat, hint=None, two_sided=False, normals=None):
        P = [np.asarray(p, float) for p in P]
        UV = [tuple(map(float, u)) for u in UV]
        if hint is not None and len(P) >= 3:
            n = np.zeros(3)
            for i in range(1, len(P) - 1):
                n += np.cross(P[i] - P[0], P[i + 1] - P[0])
            if float(np.dot(n, hint)) < 0:
                P, UV = P[::-1], UV[::-1]
                if normals is not None:
                    normals = normals[::-1]
        b = len(self.V)
        self.V += P
        self.F.append(tuple(range(b, b + len(P))))
        self.UV.append(UV)
        self.M.append(mat)
        if normals is not None:
            for i, normal in enumerate(normals):
                self.core_normals[b+i] = np.asarray(normal, float)
        if two_sided:
            self.face(P[::-1], UV[::-1], mat,
                      normals=None if normals is None else [-np.asarray(n) for n in normals[::-1]])

    def box(self, c, ax, hx, hy, z0, z1, mat, uvr, top=True, bottom=False):
        """Vertical box at c (u, v); ax = unit 2D axis; every side mapped to the rect uvr = ((u0, v0), (u1, v1))."""
        c = np.asarray(c, float)
        ax = np.asarray(ax, float)
        ay = np.array([-ax[1], ax[0]])
        cs = [c + ax * sx * hx + ay * sy * hy for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        (u0, v0), (u1, v1) = uvr
        uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        for i in range(4):
            p, q = cs[i], cs[(i + 1) % 4]
            out = np.append((p + q) / 2 - c, 0.0)
            self.face([P3(p, z0), P3(q, z0), P3(q, z1), P3(p, z1)], uv, mat, out)
        if top:
            self.face([P3(p, z1) for p in cs], uv, mat, UP)
        if bottom:
            self.face([P3(p, z0) for p in cs], uv, mat, -UP)

    def tube(self, A, B, r, sides, mat, uvr, r2=None):
        A, B = np.asarray(A, float), np.asarray(B, float)
        d = (B - A) / np.linalg.norm(B - A)
        x = np.cross(d, UP)
        if np.linalg.norm(x) < 1e-6:
            x = np.array([1.0, 0, 0])
        x /= np.linalg.norm(x)
        y = np.cross(x, d)
        r2 = r if r2 is None else r2
        ang = [2 * math.pi * k / sides for k in range(sides + 1)]
        (u0, v0), (u1, v1) = uvr
        for k in range(sides):
            a0, a1 = ang[k], ang[k + 1]
            o0, o1 = x * math.cos(a0) + y * math.sin(a0), x * math.cos(a1) + y * math.sin(a1)
            self.face([A + o0 * r, A + o1 * r, B + o1 * r2, B + o0 * r2],
                      [(u0, v0), (u1, v0), (u1, v1), (u0, v1)], mat, o0 + o1)

    def to_object(self, name, smooth_angle=35.0):
        me = bpy.data.meshes.new(name)
        V = np.array(self.V)
        E = V[:, :1] * AX_U[None, :] + V[:, 1:2] * AX_V[None, :] + (AX_O - ANCHOR[:2])[None, :]
        Vb = np.column_stack([-E[:, 0], -E[:, 1], V[:, 2]])          # Blender (-dE, -dN, dU) -> glTF (-dE, dU, dN)
        me.from_pydata([tuple(v) for v in Vb], [], self.F)
        uvl = me.uv_layers.new(name="UVMap")
        k = 0
        for uvs in self.UV:
            for u in uvs:
                uvl.data[k].uv = u
                k += 1
        names = sorted(set(self.M))
        for n in names:
            me.materials.append(material(n))
        for p, m in zip(me.polygons, self.M):
            p.material_index = names.index(m)
            p.use_smooth = True
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
        me.update()
        if self.core_normals:
            # Blender's documented ZERO vector keeps the automatic normal. Only canopy-core
            # loops receive radial normals; building/roof/trim/cards retain their original auto normals.
            custom = np.zeros((len(me.loops), 3), dtype=float)
            for loop in me.loops:
                normal = self.core_normals.get(loop.vertex_index)
                if normal is None:
                    continue
                en = normal[0]*AX_U + normal[1]*AX_V
                nb = np.array([-en[0], -en[1], normal[2]])
                custom[loop.index] = nb / np.linalg.norm(nb)
            me.normals_split_custom_set(custom.tolist())
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        me.calc_loop_triangles()
        return ob, len(me.loop_triangles)


_MATS = {}
RENDER = "--render" in argv


def material(name):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    bsdf = m.node_tree.nodes["Principled BSDF"]
    if RENDER:
        nt = m.node_tree
        if name == MAT:
            d = REPO / "art-source" / "world" / "materials" / "fire_station" / "Medium"
            uvn = nt.nodes.new("ShaderNodeUVMap")
            mp = nt.nodes.new("ShaderNodeMapping")
            mp.inputs["Scale"].default_value = (1 / LAY["tile_m"][0], 1 / LAY["tile_m"][1], 1)
            nt.links.new(uvn.outputs["UV"], mp.inputs["Vector"])

            def tex(fn, cs):
                t = nt.nodes.new("ShaderNodeTexImage")
                t.image = bpy.data.images.load(str(d / fn))
                t.image.colorspace_settings.name = cs
                nt.links.new(mp.outputs["Vector"], t.inputs["Vector"])
                return t
            tb = tex("T_fire_station_BaseColor.png", "sRGB")
            tn = tex("T_fire_station_Normal.png", "Non-Color")
            tm = tex("T_fire_station_MaskMap.png", "Non-Color")
            nt.links.new(tb.outputs["Color"], bsdf.inputs["Base Color"])
            nm = nt.nodes.new("ShaderNodeNormalMap")
            nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
            nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])
            inv = nt.nodes.new("ShaderNodeMath")
            inv.operation = "SUBTRACT"
            inv.inputs[0].default_value = 1.0
            nt.links.new(tm.outputs["Alpha"], inv.inputs[1])
            nt.links.new(inv.outputs[0], bsdf.inputs["Roughness"])
            sep = nt.nodes.new("ShaderNodeSeparateColor")
            nt.links.new(tm.outputs["Color"], sep.inputs["Color"])
            nt.links.new(sep.outputs["Red"], bsdf.inputs["Metallic"])
        elif name in (ALPHA, SHELL, HERO_SHELL):
            t = nt.nodes.new("ShaderNodeTexImage")
            texture_name = SHELL if name == HERO_SHELL else name
            t.image = bpy.data.images.load(str(REPO / "art-source" / "world" / "textures" / (texture_name + ".png")))
            if name == HERO_SHELL:
                mix = nt.nodes.new("ShaderNodeMixRGB"); mix.blend_type = "MULTIPLY"
                mix.inputs[0].default_value = 1
                mix.inputs[2].default_value = (*LAY["thuja_shell_tint_linear"], 1)
                nt.links.new(t.outputs["Color"], mix.inputs[1]); nt.links.new(mix.outputs[0], bsdf.inputs["Base Color"])
            else:
                nt.links.new(t.outputs["Color"], bsdf.inputs["Base Color"])
            gt = nt.nodes.new("ShaderNodeMath")
            gt.operation = "GREATER_THAN"
            gt.inputs[1].default_value = 0.5
            nt.links.new(t.outputs["Alpha"], gt.inputs[0])
            nt.links.new(gt.outputs[0], bsdf.inputs["Alpha"])
            bsdf.inputs["Roughness"].default_value = 0.97 if name == HERO_SHELL else 0.6
            m.blend_method = "CLIP" if hasattr(m, "blend_method") else m.blend_method
        else:
            n = nt.nodes.new("ShaderNodeTexNoise")
            n.inputs["Scale"].default_value = 9.0
            n.inputs["Detail"].default_value = 8.0
            ramp = nt.nodes.new("ShaderNodeValToRGB")
            ramp.color_ramp.elements[0].color = (0.006, 0.012, 0.005, 1)
            ramp.color_ramp.elements[1].color = (0.030, 0.055, 0.022, 1)
            nt.links.new(n.outputs["Fac"], ramp.inputs["Fac"])
            nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
            bsdf.inputs["Roughness"].default_value = 0.9
    _MATS[name] = m
    return m


# ------------------------------------------------------------------------------------------------ band mapping
def bands(L, kind, ground=True, lod=0):
    """Split a length L (metres up the wall / up the roof slope from the eave) into pieces mapped into the
    u-periodic band of the atlas: [(t0, t1, v0, v1)]. The bottom zone (splash / eave dirt) sits at t = 0 when
    `ground`, the top zone (run-off / ridge) at t = L, the plain middle zone repeats mirrored in between."""
    b = LAY[kind]
    v0, H = b["v0"], b["h"]
    m0, m1 = b["mid"]
    top = H - m1
    if L <= 1e-6:
        return []
    if lod >= 2:
        return [(0.0, L, v0 + (0.0 if ground else m0), v0 + (min(L, H) if ground else min(m0 + L, H)))]
    out = []
    if ground:
        if L <= m1:
            if L <= top:
                return [(0.0, L, v0, v0 + L)]
            return [(0.0, L - top, v0, v0 + L - top), (L - top, L, v0 + m1, v0 + H)]
        out.append((0.0, m1, v0, v0 + m1))
        t = m1
        Lm = L - H
        n = 0 if Lm <= 1e-6 else 2 * int(math.ceil(Lm / (2 * (m1 - m0)) - 1e-9))
    else:
        if L <= top:
            return [(0.0, L, v0 + H - L, v0 + H)]
        t = 0.0
        Lm = L - top
        n = int(math.ceil(Lm / (m1 - m0) - 1e-9))
    if n:
        ch = Lm / n
        for k in range(n):
            down = (k % 2 == 0) if ground else ((n - k) % 2 == 0)
            # a "down" chunk runs m1 -> m1 - ch going up the wall; an "up" chunk the reverse, so neighbours meet
            out.append((t, t + ch, v0 + (m1 if down else m1 - ch), v0 + (m1 - ch if down else m1)))
            t += ch
    out.append((L - top, L, v0 + m1, v0 + H))
    return out


def clip(poly, lo, hi, axis):
    """Sutherland-Hodgman clip of a convex 2D polygon to lo <= p[axis] <= hi."""
    for bound, keep_above in ((lo, True), (hi, False)):
        out = []
        n = len(poly)
        for i in range(n):
            p, q = poly[i], poly[(i + 1) % n]
            ip = (p[axis] >= bound - 1e-9) if keep_above else (p[axis] <= bound + 1e-9)
            iq = (q[axis] >= bound - 1e-9) if keep_above else (q[axis] <= bound + 1e-9)
            if ip:
                out.append(p)
            if ip != iq:
                t = (bound - p[axis]) / (q[axis] - p[axis])
                out.append((p[0] + (q[0] - p[0]) * t, p[1] + (q[1] - p[1]) * t))
        poly = out
        if len(poly) < 3:
            return []
    return poly


def _area(poly):
    return 0.5 * abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                         for i in range(len(poly))))


def surface(mb, O, S, T, poly, segs, u0, mat, hint, holes=(), t_base=0.0):
    """Planar surface: P = O + S s + T t. poly = convex polygon in (s, t); segs = bands() pieces along t (relative to
    t_base); holes = [(s0, s1, t0, t1)] left open. UV = (u0 + s, band v)."""
    O, S, T = np.asarray(O, float), np.asarray(S, float), np.asarray(T, float)
    smin, smax = min(p[0] for p in poly), max(p[0] for p in poly)
    tmin, tmax = min(p[1] for p in poly), max(p[1] for p in poly)
    tcuts = {tmin, tmax}
    for a, b, _, _ in segs:
        tcuts |= {a + t_base, b + t_base}
    for h in holes:
        tcuts |= {h[2], h[3]}
    tcuts = sorted(x for x in tcuts if tmin - 1e-9 <= x <= tmax + 1e-9)
    for ta, tb in zip(tcuts[:-1], tcuts[1:]):
        if tb - ta < 1e-6:
            continue
        tm = (ta + tb) / 2 - t_base
        seg = next((s_ for s_ in segs if s_[0] - 1e-9 <= tm <= s_[1] + 1e-9), segs[-1] if segs else None)
        if seg is None:
            continue
        hs = [h for h in holes if h[2] < tb - 1e-9 and h[3] > ta + 1e-9]
        scuts = sorted({smin, smax} | {x for h in hs for x in (h[0], h[1]) if smin < x < smax})
        strip = clip(list(poly), ta, tb, 1)
        if not strip:
            continue
        for sa, sb in zip(scuts[:-1], scuts[1:]):
            sm = (sa + sb) / 2
            if any(h[0] - 1e-9 <= sm <= h[1] + 1e-9 for h in hs):
                continue
            cell = clip(list(strip), sa, sb, 0)
            if len(cell) < 3 or _area(cell) < 1e-5:
                continue

            def vmap(t):
                f = (t - t_base - seg[0]) / (seg[1] - seg[0])
                return seg[2] + (seg[3] - seg[2]) * f
            mb.face([O + S * s + T * t for s, t in cell], [(u0 + s, vmap(t)) for s, t in cell], mat, hint)


WIN = {  # opening kind -> (atlas rect, inset m)
    "plain": ("win_plain", 0.11), "ribbon": ("win_ribbon", 0.11), "small": ("win_small", 0.10),
    "arch": ("win_arch", 0.0), "round": ("win_round", 0.0), "door": ("door", 0.22), "entry": ("door_entry", 0.14),
}


def _bar(mb, W, back, nout, p, q, hw, proud, uvr):
    """Glazing bar from p to q (window-local x, y), 2 hw wide, `proud` in front of the glass: front + two sides."""
    p, q = np.asarray(p, float), np.asarray(q, float)
    d = (q - p) / max(np.linalg.norm(q - p), 1e-9)
    n2 = np.array([-d[1], d[0]]) * hw
    (u0, v0), (u1, v1) = uvr
    uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    fr = back + nout * proud
    c = [p - n2, p + n2, q + n2, q - n2]
    mb.face([W(*x) + fr for x in c], uv, MAT, nout)
    for a, b, sgn in ((c[0], c[3], -1.0), (c[1], c[2], 1.0)):
        side = W(*(a + n2 * sgn)) - W(*a)
        mb.face([W(*a) + back, W(*b) + back, W(*b) + fr, W(*a) + fr], uv, MAT, side)


def deep_window(mb, O, S, nout, hole, kind, u0, depth=0.20, proud=0.03):
    """LOD0 gable window with real depth (r3; the flat quad read as a sticker from the fence line): render spandrels
    up to the outline, blue trim band `proud` of the wall, reveal `depth` back to the glazing, glazing n-gon mapped
    into the atlas rect, mullions as bars in front of the glass. Shapes from atlas_layout.json (arch / round)."""
    s0, s1, z0, z1 = hole
    R_ = LAY["win_arch" if kind == "arch" else "win_round"]
    f, pv = LAY["fascia"], LAY["pvc_white"]
    pm = LAY["plaster"]["v0"] + LAY["plaster"]["mid"][0]
    back, out = -nout * depth, nout * proud
    H = z1 - z0

    def W(x, y):
        return O + S * (s0 + x) + UP * (z0 + y)

    kx, ky = (R_["u"][1] - R_["u"][0]) / (s1 - s0), (R_["v"][1] - R_["v"][0]) / H      # rect holds the window scaled

    def auv(p):
        return (R_["u"][0] + p[0] * kx, R_["v"][0] + p[1] * ky)

    def blue(a, b, lo=0.10, hi=0.26):
        return [(a, f["v0"] + lo), (b, f["v0"] + lo), (b, f["v0"] + hi), (a, f["v0"] + hi)]
    white = ((pv["u"][0] + 0.2, pv["v"][0] + 0.05), (pv["u"][0] + 0.26, pv["v"][1] - 0.05))
    if kind == "arch":
        g = LAY["arch"]
        w, sp, rise, tr = g["w"], g["spring"], g["rise"], g["trim"]
        rad = ((w / 2) ** 2 + rise ** 2) / (2 * rise)
        cy, ri, n = sp + rise - rad, rad - tr, 10
        ao, ai = math.asin(w / 2 / rad), math.asin(min(w / 2 / ri, 1.0))
        Po = [(w / 2 + rad * math.sin(-ao + 2 * ao * k / n), cy + rad * math.cos(-ao + 2 * ao * k / n)) for k in range(n + 1)]
        Pi = [(w / 2 + ri * math.sin(-ai + 2 * ai * k / n), cy + ri * math.cos(-ai + 2 * ai * k / n)) for k in range(n + 1)]
        Po[0], Po[-1] = (0.0, sp), (w, sp)
        Pi[0], Pi[-1] = (0.0, Pi[0][1]), (w, Pi[-1][1])
        yj = Pi[0][1]
        ctr = W(w / 2, cy)
        for a, b in zip(Po[:-1], Po[1:]):          # render between the arch and the square hole
            q = [a, b, (b[0], H), (a[0], H)]
            mb.face([W(*p) for p in q], [(u0 + 5.0 + p[0], pm + 0.1 + p[1] - sp) for p in q], MAT, nout)
        run = 0.0
        for k in range(n):                          # trim band on the arch head, its reveal and its outer lip
            L = math.dist(Po[k], Po[k + 1])
            mb.face([W(*p) + out for p in (Pi[k], Pi[k + 1], Po[k + 1], Po[k])], blue(run, run + L), MAT, nout)
            a3, b3 = W(*Pi[k]), W(*Pi[k + 1])
            mb.face([a3 + out, b3 + out, b3 + back, a3 + back], blue(run, run + L, 0.08, 0.31), MAT, ctr - (a3 + b3) / 2)
            mb.face([W(*Po[k]) + out, W(*Po[k + 1]) + out, W(*Po[k + 1]), W(*Po[k])], blue(run, run + L, 0.30, 0.33), MAT,
                    (W(*Po[k]) + W(*Po[k + 1])) / 2 - ctr)
            run += L
        for x, hint in ((0.0, S), (w, -S)):         # jamb reveals (render)
            mb.face([W(x, 0), W(x, yj), W(x, yj) + back, W(x, 0) + back],
                    [(u0 + 3.0, pm + 0.05), (u0 + 3.0, pm + 1.3), (u0 + 3.0 + depth, pm + 1.3), (u0 + 3.0 + depth, pm + 0.05)], MAT, hint)
        sl = nout * 0.05                            # sheet sill, 5 cm proud with a drip edge
        pu, pvv = pv["u"][0], pv["v"][0]
        mb.face([W(0, 0) + sl, W(w, 0) + sl, W(w, 0.03) + back, W(0, 0.03) + back],
                [(pu, pvv), (pu + 0.9, pvv), (pu + 0.9, pvv + 0.25), (pu, pvv + 0.25)], MAT, UP)
        mb.face([W(0, -0.03) + sl, W(w, -0.03) + sl, W(w, 0) + sl, W(0, 0) + sl],
                [(pu, pvv), (pu + 0.9, pvv), (pu + 0.9, pvv + 0.03), (pu, pvv + 0.03)], MAT, nout)
        poly = [(0.0, 0.03), (w, 0.03)] + Pi[::-1]
        mb.face([W(*p) + back for p in poly], [auv(p) for p in poly], MAT, nout)

        def top(x):
            return cy + math.sqrt(max(ri * ri - (x - w / 2) ** 2, 0.0))
        k = 1
        while k * g["col"] < w - 0.1:               # mullions on the painted ones
            x = k * g["col"]
            _bar(mb, W, back, nout, (x, 0.03), (x, top(x)), g["bar"] / 2, 0.05, white)
            k += 1
        k = 1
        while k * g["row"] < top(w / 2) - 0.3:
            y = k * g["row"]
            hw_ = w / 2 if y <= yj else math.sqrt(max(ri * ri - (y - cy) ** 2, 0.0))
            _bar(mb, W, back, nout, (w / 2 - hw_, y), (w / 2 + hw_, y), g["bar"] / 2, 0.055, white)
            k += 1
        for x in (0.035, w - 0.035):                # frame stiles
            _bar(mb, W, back, nout, (x, 0.03), (x, yj), 0.035, 0.05, white)
        return
    g = LAY["round"]
    R0, n = g["d"] / 2, 16
    ri = R0 - g["trim"]
    ang = [2 * math.pi * k / n for k in range(n + 1)]
    Po = [(R0 + R0 * math.cos(a), R0 + R0 * math.sin(a)) for a in ang]
    Pi = [(R0 + ri * math.cos(a), R0 + ri * math.sin(a)) for a in ang]

    def sq(a):
        cs, sn = math.cos(a), math.sin(a)
        m = max(abs(cs), abs(sn))
        return (R0 + R0 * cs / m, R0 + R0 * sn / m)
    ctr = W(R0, R0)
    run = 0.0
    for k in range(n):
        q = [Po[k], Po[k + 1], sq(ang[k + 1]), sq(ang[k])]
        if _area(q) > 1e-4:
            mb.face([W(*p) for p in q], [(u0 + 5.0 + p[0], pm + 0.1 + p[1] * 0.5) for p in q], MAT, nout)
        L = math.dist(Po[k], Po[k + 1])
        mb.face([W(*p) + out for p in (Pi[k], Pi[k + 1], Po[k + 1], Po[k])], blue(run, run + L), MAT, nout)
        a3, b3 = W(*Pi[k]), W(*Pi[k + 1])
        mb.face([a3 + out, b3 + out, b3 + back, a3 + back], blue(run, run + L, 0.08, 0.31), MAT, ctr - (a3 + b3) / 2)
        mb.face([W(*Po[k]) + out, W(*Po[k + 1]) + out, W(*Po[k + 1]), W(*Po[k])], blue(run, run + L, 0.30, 0.33), MAT,
                (W(*Po[k]) + W(*Po[k + 1])) / 2 - ctr)
        run += L
    mb.face([W(*p) + back for p in Pi[:-1]], [auv(p) for p in Pi[:-1]], MAT, nout)
    bl = ((0.3, f["v0"] + 0.10), (0.3 + 2 * ri, f["v0"] + 0.26))
    _bar(mb, W, back, nout, (R0 - ri, R0), (R0 + ri, R0), 0.035, 0.05, white)      # r4: thin white transom (photo 7197)
    _bar(mb, W, back, nout, (R0, R0 - ri), (R0, R0 + ri), g["cross"] / 2, 0.07, bl)


def wall_light(mb, c, d, z, lod, w=0.30):
    """Bulkhead / flood light on the wall (LOD0): dark housing with a pale lens face underneath."""
    if lod > 0:
        return
    dk, pv = LAY["dark"], LAY["pvc_white"]
    c, d = np.asarray(c, float), np.asarray(d, float)
    mb.box(c, d, w / 2, 0.06, z, z + 0.13, MAT, ((dk["u"][0] + 0.1, dk["v"][0] + 0.1), (dk["u"][0] + 0.4, dk["v"][0] + 0.25)), top=True)
    ay = np.array([-d[1], d[0]])
    cs = [c + d * sx * w / 2 + ay * sy * 0.06 for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    mb.face([P3(p, z) for p in cs], [(pv["u"][0] + 0.1, pv["v"][0] + 0.1), (pv["u"][0] + 0.4, pv["v"][0] + 0.1),
                                     (pv["u"][0] + 0.4, pv["v"][0] + 0.2), (pv["u"][0] + 0.1, pv["v"][0] + 0.2)], MAT, -UP)


def wall(mb, p0, p1, z0, z1, lod, openings=(), ground=True, top=None, plinth=None, key=""):
    """Rendered wall from p0 to p1 (u, v); outward = right of the direction. openings: [(s centre, z bottom, w, h,
    kind)]. top: optional [(s, z)] polyline (left to right) replacing the flat top. plinth: default = ground."""
    p0, p1 = np.asarray(p0, float), np.asarray(p1, float)
    L = float(np.linalg.norm(p1 - p0))
    d = (p1 - p0) / L
    nout = np.array([d[1], -d[0], 0.0])
    S = np.array([d[0], d[1], 0.0])
    plinth = ground if plinth is None else plinth
    zb = PL_H if plinth and lod < 2 else z0
    O = P3(p0, 0.0)
    ztop = max([z1] + [z for _, z in (top or [])])
    poly = [(0.0, zb), (L, zb)] + ([(s, z) for s, z in reversed(top)] if top else [(L, z1), (0.0, z1)])
    ops = list(openings)
    if lod >= 2:
        ops = [o for o in ops if o[4] in ("arch", "round", "door")]
    holes = [(o[0] - o[2] / 2, o[0] + o[2] / 2, o[1], o[1] + o[3]) for o in ops]
    segs = bands(ztop - zb, "plaster", ground=ground, lod=lod)
    u0 = round(h01(ASSET, "wall", key) * 13.0, 2)
    surface(mb, O, S, UP, poly, segs, u0, MAT, nout, holes, t_base=zb)
    pm = LAY["plaster"]["v0"] + LAY["plaster"]["mid"][0]
    for o, h in zip(ops, holes):
        if lod == 0 and o[4] in ("arch", "round"):
            deep_window(mb, O, S, nout, h, o[4], u0)
            continue
        if o[4] == "entry":      # bulkhead light over every entrance door
            wall_light(mb, p0 + d * o[0] + np.array([d[1], -d[0]]) * 0.06, d, o[1] + o[3] + 0.22, lod, w=0.24)
        rk, inset = WIN[o[4]]
        inset = inset if lod == 0 else 0.0
        back = -nout * inset
        q = [O + S * h[0] + UP * h[2] + back, O + S * h[1] + UP * h[2] + back,
             O + S * h[1] + UP * h[3] + back, O + S * h[0] + UP * h[3] + back]
        mb.face(q, rect_uv(LAY[rk]), MAT, nout)
        if inset > 0:
            f = [O + S * h[0] + UP * h[2], O + S * h[1] + UP * h[2], O + S * h[1] + UP * h[3], O + S * h[0] + UP * h[3]]
            pv = LAY["pvc_white"]
            for i, hint_ in ((0, UP), (1, -S), (2, -UP), (3, S)):
                a, b = f[i], f[(i + 1) % 4]
                ln = float(np.linalg.norm(b - a))
                if i == 0 and o[4] not in ("door", "entry"):          # sill: white sheet
                    uv = [(pv["u"][0], pv["v"][0]), (pv["u"][0] + min(ln, 0.9), pv["v"][0]),
                          (pv["u"][0] + min(ln, 0.9), pv["v"][0] + inset), (pv["u"][0], pv["v"][0] + inset)]
                else:
                    uv = [(u0 + 3.0, pm), (u0 + 3.0 + ln, pm), (u0 + 3.0 + ln, pm + inset), (u0 + 3.0, pm + inset)]
                mb.face([a, b, b + back, a + back], uv, MAT, hint_)
    if plinth and lod < 2:
        strip(mb, [p0, p1], -1.0, PL_H, 0.04, lod, key)


def strip(mb, pts, z0, z1, proud, lod, key=""):
    """Concrete plinth along a polyline (outward = right), 4 cm proud, with a sloped top ledge at LOD0."""
    pl = LAY["plinth"]
    u0 = round(h01(ASSET, "plinth", key) * 9.0, 2)
    run = 0.0
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = np.asarray(a, float), np.asarray(b, float)
        L = float(np.linalg.norm(b - a))
        d = (b - a) / L
        n2 = np.array([d[1], -d[0]]) * proud
        nout = np.array([d[1], -d[0], 0.0])
        zm = z1 - pl["h"]
        A, B = a + n2, b + n2
        ua, ub = u0 + run, u0 + run + L
        mb.face([P3(A, zm), P3(B, zm), P3(B, z1 - 0.03), P3(A, z1 - 0.03)],
                [(ua, pl["v0"]), (ub, pl["v0"]), (ub, pl["v0"] + pl["h"] - 0.03), (ua, pl["v0"] + pl["h"] - 0.03)], MAT, nout)
        if z0 < zm:
            mb.face([P3(A, z0), P3(B, z0), P3(B, zm), P3(A, zm)],
                    [(ua, pl["v0"]), (ub, pl["v0"]), (ub, pl["v0"] + 0.04), (ua, pl["v0"] + 0.04)], MAT, nout)
        mb.face([P3(A, z1 - 0.03), P3(B, z1 - 0.03), P3(b, z1 + 0.01), P3(a, z1 + 0.01)],
                [(ua, pl["v0"] + pl["h"] - 0.05), (ub, pl["v0"] + pl["h"] - 0.05), (ub, pl["v0"] + pl["h"]), (ua, pl["v0"] + pl["h"])],
                MAT, UP)
        run += L


def roof(mb, pts, lod, key="", sheet="roof"):
    """Planar roof face; pts = 3D polygon (convex), the first edge is the eave. Bands run up the slope."""
    pts = [np.asarray(p, float) for p in pts]
    S = pts[1] - pts[0]
    S /= np.linalg.norm(S)
    n = np.zeros(3)
    for i in range(1, len(pts) - 1):
        n += np.cross(pts[i] - pts[0], pts[i + 1] - pts[0])
    n /= np.linalg.norm(n)
    if n[2] < 0:
        n = -n
    T = np.cross(n, S)
    if T[2] < 0:
        T = -T
    poly = [(float((p - pts[0]) @ S), float((p - pts[0]) @ T)) for p in pts]
    tmin = min(p[1] for p in poly)
    Ls = max(p[1] for p in poly) - tmin
    u0 = round(h01(ASSET, "roof", key) * 13.0 / 0.25) * 0.25
    surface(mb, pts[0], S, T, poly, bands(Ls, sheet, lod=lod), u0, MAT, n, t_base=tmin)


def swatch_face(mb, pts, rk, hint, key="", two_sided=False, scale=1.0):
    """Planar polygon mapped into a swatch rect: local metres wrapped (mirrored) into the rect."""
    r = LAY[rk]
    pts = [np.asarray(p, float) for p in pts]
    S = pts[1] - pts[0]
    S /= np.linalg.norm(S)
    n = np.cross(S, pts[-1] - pts[0])
    n /= max(np.linalg.norm(n), 1e-9)
    T = np.cross(n, S)
    w, h = r["u"][1] - r["u"][0], r["v"][1] - r["v"][0]
    s = [float((p - pts[0]) @ S) * scale for p in pts]
    t = [float((p - pts[0]) @ T) * scale for p in pts]
    ks, kt = max(1.0, (max(s) - min(s)) / w), max(1.0, (max(t) - min(t)) / h)
    uv = [(r["u"][0] + (a - min(s)) / ks, r["v"][0] + (b - min(t)) / kt) for a, b in zip(s, t)]
    mb.face(pts, uv, MAT, hint, two_sided=two_sided)


def fascia(mb, a, b, outward, lod, h=0.38, soffit=0.0, key="", gutter=False):
    """Blue fascia board hanging below the roof edge a-b (3D), facing `outward`; optional soffit back to the wall;
    gutter = coated steel box gutter in front of the fascia (LOD0, r3)."""
    if lod >= 2:
        return
    if gutter and lod == 0:
        f_ = LAY["fascia"]
        a_, b_ = np.asarray(a, float), np.asarray(b, float)
        o_ = np.asarray(outward, float)
        o_ = o_ / np.linalg.norm(o_)
        Lg = float(np.linalg.norm(b_ - a_))
        prof = [(0.005, -0.035), (0.025, -0.125), (0.105, -0.125), (0.130, -0.025)]
        for i, ((xa, za), (xb, zb)) in enumerate(zip(prof[:-1], prof[1:])):
            va = f_["v0"] + 0.05 + 0.09 * i
            mb.face([a_ + o_ * xa + UP * za, b_ + o_ * xa + UP * za, b_ + o_ * xb + UP * zb, a_ + o_ * xb + UP * zb],
                    [(1.0, va), (1.0 + Lg, va), (1.0 + Lg, va + 0.09), (1.0, va + 0.09)], MAT, None, two_sided=True)
    f = LAY["fascia"]
    a, b = np.asarray(a, float), np.asarray(b, float)
    L = float(np.linalg.norm(b - a))
    u0 = round(h01(ASSET, "fascia", key) * 11.0, 2)
    dn = np.array([0, 0, -h])
    mb.face([a + dn, b + dn, b, a], [(u0, f["v0"]), (u0 + L, f["v0"]), (u0 + L, f["v0"] + f["h"]), (u0, f["v0"] + f["h"])], MAT, outward)
    if soffit > 0 and lod == 0:
        o = np.asarray(outward, float)
        o = o / np.linalg.norm(o) * soffit
        mb.face([a + dn - o, b + dn - o, b + dn, a + dn],
                [(u0, f["v0"] + 0.1), (u0 + L, f["v0"] + 0.1), (u0 + L, f["v0"] + 0.1 + min(soffit, 0.25)), (u0, f["v0"] + 0.1 + min(soffit, 0.25))],
                MAT, -UP)


def mono_roof(mb, ua, ub, v_eave, z_eave, v_top, z_top, lod, key, oh=0.25, ends=(True, True)):
    """Mono-pitch sheet roof between u = ua..ub from the eave line (v_eave, z_eave) up to (v_top, z_top), eave
    overhang oh, fascia + soffit at the eave and fascia at the open ends."""
    sgn = 1.0 if v_top > v_eave else -1.0
    k = (z_top - z_eave) / abs(v_top - v_eave)
    ve, ze = v_eave - sgn * oh, z_eave - k * oh
    e0, e1 = (ua, ub) if sgn > 0 else (ub, ua)
    roof(mb, [P3((e0, ve), ze), P3((e1, ve), ze), P3((e1, v_top), z_top), P3((e0, v_top), z_top)], lod, key)
    fascia(mb, P3((e0, ve), ze), P3((e1, ve), ze), np.array([0, -sgn, 0.0]), lod, soffit=oh, key=key, gutter=True)
    for flag, uu, o in ((ends[0], ua, -1.0), (ends[1], ub, 1.0)):
        if flag:
            fascia(mb, P3((uu, ve), ze), P3((uu, v_top), z_top), np.array([o, 0, 0.0]), lod, h=0.30, key=key + "e")


def hip_cap(mb, a, b, lod, w=0.16):
    """Folded ridge / hip cap sheet along a-b, 4 cm above the roof planes (LOD0)."""
    if lod > 0:
        return
    f = LAY["fascia"]
    a, b = np.asarray(a, float), np.asarray(b, float)
    d = (b - a) / np.linalg.norm(b - a)
    side = np.cross(d, UP)
    side /= np.linalg.norm(side)
    L = float(np.linalg.norm(b - a))
    up = np.cross(side, d) * 0.05
    for sgn in (-1.0, 1.0):
        o = side * w * sgn - up * 0.6
        mb.face([a + up, b + up, b + up + o, a + up + o],
                [(0.0, f["v0"] + 0.12), (L, f["v0"] + 0.12), (L, f["v0"] + 0.12 + w), (0.0, f["v0"] + 0.12 + w)], MAT, UP)


def downpipe(mb, p, nout, z0, z1, lod):
    if lod > 0:
        return
    r = LAY["pvc_white"]
    c = np.asarray(p, float) + np.asarray(nout, float) * 0.09
    mb.tube(P3(c, z0), P3(c, z1), 0.05, 6, MAT, ((r["u"][0] + 0.1, r["v"][0]), (r["u"][0] + 0.4, r["v"][1])))


def chimney(mb, c, z0, z1, lod, w=0.62):
    if lod >= 2:
        return
    b = LAY["brick"]
    hh = min(z1 - z0, b["v"][1] - b["v"][0])
    mb.box(c, (1, 0), w / 2, w / 2, z0, z1, MAT, ((b["u"][0] + 0.12, b["v"][1] - hh - 0.3), (b["u"][0] + 0.12 + w, b["v"][1] - 0.3)), top=False)
    p = LAY["plinth"]
    mb.box(c, (1, 0), w / 2 + 0.05, w / 2 + 0.05, z1, z1 + 0.08, MAT, ((0.5, p["v0"] + 0.3), (1.3, p["v0"] + 0.38)), top=True, bottom=lod == 0)


# -------------------------------------------------------------------------------------------------- the building
def build_garage(mb, lod):
    g = D["garage"]
    (u0, u1), (v0, v1) = g["u"], g["v"]
    ze, zr, ur = zl(g["eave_z"]), zl(g["ridge_z"]), g["ridge_u"]
    n, dw, dh = g["doors"], g["door_w"], g["door_h"]
    pier = (u1 - u0 - n * dw) / (n + 1)
    b = LAY["brick"]
    pm = LAY["plinth"]
    for side, (pa, pb) in (("sw", ((u0, v0), (u1, v0))), ("ne", ((u1, v1), (u0, v1)))):
        doors = [(pier + dw / 2 + k * (dw + pier), 0.0, dw, dh, "door") for k in range(n)]
        s_r = (ur - u0) if side == "sw" else (u1 - ur)
        wall(mb, pa, pb, 0.0, ze, lod, doors, ground=False, plinth=False,
             top=[(0.0, ze), (s_r, zr), (u1 - u0, ze)], key="g" + side)
        d = np.array(pb, float) - np.array(pa, float)
        d /= np.linalg.norm(d)
        nout2 = np.array([d[1], -d[0]])
        nout = np.append(nout2, 0.0)
        # threshold / foundation strip under the door wall
        A, B = np.array(pa, float), np.array(pb, float)
        mb.face([P3(A, -1.0), P3(B, -1.0), P3(B, 0.0), P3(A, 0.0)],
                [(0, pm["v0"]), (u1 - u0, pm["v0"]), (u1 - u0, pm["v0"] + 0.3), (0, pm["v0"] + 0.3)], MAT, nout)
        if lod < 2:      # clinker piers, proud of the wall
            for k in range(n + 1):
                c = A + d * (k * (dw + pier) + pier / 2) + nout2 * (g["pier_proud"] / 2 - 0.02)
                mb.box(c, d, pier / 2, g["pier_proud"] / 2 + 0.02, -0.4, dh + 0.0, MAT,
                       ((b["u"][0] + 0.09, b["v"][0]), (b["u"][0] + 0.09 + pier, b["v"][0] + dh + 0.0)), top=True)
            for k in range(1, n):          # flood lights over the inner piers (r3)
                wall_light(mb, A + d * (k * (dw + pier) + pier / 2) + nout2 * 0.07, d, dh + 0.62, lod)
            # lintel band: blue flashing over the doors
            fascia(mb, P3(A + nout2 * 0.06, dh + 0.26), P3(B + nout2 * 0.06, dh + 0.26), nout, lod, h=0.26, key="lint" + side)
        # rake flashing
        for (sa, za), (sb, zb) in (((0.0, ze), (s_r, zr)), ((s_r, zr), (u1 - u0, ze))):
            fascia(mb, P3(A + d * sa + nout2 * 0.10, za + 0.06), P3(A + d * sb + nout2 * 0.10, zb + 0.06), nout, lod, h=0.34, soffit=0.10, key="rake" + side)
    # NW long wall with high ribbon windows (yard side, WORKING_VALUE), SE stub beyond the wing
    Lw = v1 - v0
    wins = [(s + ds, 3.3, 1.2, 0.8, "ribbon") for s in np.linspace(3.6, Lw - 3.6, 5) for ds in (-0.6, 0.6)]
    wall(mb, (u0, v1), (u0, v0), 0.0, ze, lod, wins, key="gnw")
    vne = D["middle"]["v_ne"]
    wall(mb, (u1, vne), (u1, v1), 0.0, ze, lod, [(3.0, 0.0, 1.1, 2.2, "entry")], key="gse")
    wall(mb, (u1, v0), (u1, D["middle"]["v_sw"]), 0.0, ze, lod, key="gse0")
    # membrane roof: two shallow planes, split in strips of the swatch length
    oh = 0.12
    m = LAY["membrane"]
    wl = m["u"][1] - m["u"][0]
    nst = 1 if lod else int(math.ceil((v1 - v0 + 2 * oh) / wl))
    for ua, za, ub, zb in ((u0 - oh, ze, ur, zr), (u1 + oh, ze, ur, zr)):
        for k in range(nst):
            va = v0 - oh + k * (v1 - v0 + 2 * oh) / nst
            vb = v0 - oh + (k + 1) * (v1 - v0 + 2 * oh) / nst
            uvs = [(m["u"][0], m["v"][0]), (m["u"][1], m["v"][0]), (m["u"][1], m["v"][1]), (m["u"][0], m["v"][1])]
            if k % 2:
                uvs = [uvs[1], uvs[0], uvs[3], uvs[2]]
            mb.face([P3((ua, va), za), P3((ua, vb), za), P3((ub, vb), zb), P3((ub, va), zb)], uvs, MAT, UP)
    fascia(mb, P3((u0 - oh, v1 + oh), ze), P3((u0 - oh, v0 - oh), ze), np.array([-1.0, 0, 0]), lod, h=0.34, soffit=oh, key="geave", gutter=True)
    fascia(mb, P3((u1 + oh, vne), ze), P3((u1 + oh, v1 + oh), ze), np.array([1.0, 0, 0]), lod, h=0.34, soffit=oh, key="geave2", gutter=True)
    downpipe(mb, (u0, v0 + 0.5), (-1, 0), PL_H, ze - 0.3, lod)
    downpipe(mb, (u0, v1 - 0.5), (-1, 0), PL_H, ze - 0.3, lod)


def build_middle(mb, lod):
    m, t, lk, g, hl = D["middle"], D["tower"], D["link"], D["garage"], D["hall"]
    ua, ub = m["u"]
    us, vs, vr, vn = m["u_step"], m["v_sw"], m["v_sw_recess"], m["v_ne"]
    zs, zn = zl(m["eave_sw_z"]), zl(m["eave_ne_z"])
    (tu0, tu1), (tv0, tv1) = t["u"], t["v"]
    tu0 = ua
    zts, ztn, zte = zl(t["roof_foot_sw_z"]), zl(t["roof_foot_ne_z"]), zl(t["eave_z"])
    k_sw = (zts - zs) / (tv0 - vs)
    zs2 = zs + k_sw * (vr - vs)                       # eave height of the recessed part (same roof plane)
    zrd, vrd = zl(lk["ridge_z"]), lk["ridge_v"]
    sh = m["storey_h"]
    # street walls: two storeys of windows
    L1 = us - ua
    w1 = [(s, z, 1.5, 1.5, "plain") for s in np.linspace(1.7, L1 - 1.7, 3) for z in (0.95, 0.95 + sh)]
    wall(mb, (ua, vs), (us, vs), 0.0, zs, lod, w1, key="m1")
    wall(mb, (us, vs), (us, vr), 0.0, zs2, lod, key="m1s", top=[(0.0, zs), (vr - vs, zs2)])
    L2 = ub - us
    w2 = [(1.6, 0.0, 1.1, 2.2, "entry")] + [(s, 0.95, 1.5, 1.5, "plain") for s in (4.2, 6.9)] + \
         [(s + ds, 0.95 + sh + 0.75, 1.2, 0.8, "ribbon") for s in (1.9, 4.6, 7.0) for ds in (-0.6, 0.6)]
    wall(mb, (us, vr), (ub, vr), 0.0, zs2, lod, w2, key="m2")
    # yard wall
    Ln = ub - ua
    wn = [(s, 0.95, 1.5, 1.5, "plain") for s in np.linspace(2.0, Ln - 2.0, 6)] + \
         [(s, 4.25, 1.2, 0.8, "ribbon") for s in np.linspace(2.0, Ln - 2.0, 6)]
    wn[1] = (wn[1][0], 0.0, 1.1, 2.2, "entry")
    wn[4] = (wn[4][0], 0.0, 1.1, 2.2, "entry")
    wall(mb, (ub, vn), (ua, vn), 0.0, zn, lod, wn, key="mn")
    # sheet roofs rising to the tower / to the link ridge
    mono_roof(mb, ua, us, vs, zs, tv0, zts, lod, "rsw1", ends=(True, False))
    mono_roof(mb, us, tu1, vr, zs2, tv0, zts, lod, "rsw2", ends=(False, False))
    mono_roof(mb, tu1, ub, vr, zs2, vrd, zrd, lod, "rsw3", ends=(False, False))
    mono_roof(mb, ua, tu1, vn, zn, tv1, ztn, lod, "rne1", ends=(True, False))
    mono_roof(mb, tu1, ub, vn, zn, vrd, zrd, lod, "rne2", ends=(False, False))
    # wall above the garage roof (west side of the wing and the tower)
    zg = zl(g["eave_z"]) - 0.1
    for (va, za), (vb, zb), kk in (((vs, zs), (tv0, zts), "a"), ((tv1, ztn), (vn, zn), "c")):
        wall(mb, (ua, vb), (ua, va), zg, max(za, zb), lod, ground=False, plinth=False,
             top=[(0.0, zb), (abs(vb - va), za)], key="mw" + kk)
    wall(mb, (ua, tv1), (ua, tv0), zg, zte, lod, [(s, zts + 0.55, 0.9, 0.9, "small") for s in (2.4, 7.4)],
         ground=False, plinth=False, key="tw")
    # tower: street and yard faces with small windows, east face down to the link roof
    Lt = tu1 - tu0
    wall(mb, (tu0, tv0), (tu1, tv0), zts - 0.05, zte, lod, [(s, zts + 0.55, 0.9, 0.9, "small") for s in np.linspace(1.6, Lt - 1.6, 4)],
         ground=False, plinth=False, key="ts")
    wall(mb, (tu1, tv1), (tu0, tv1), ztn - 0.05, zte, lod, [(s, ztn + 0.6, 0.9, 0.9, "small") for s in np.linspace(1.6, Lt - 1.6, 4)],
         ground=False, plinth=False, key="tn")
    k_ne = (zrd - zn) / (vn - vrd)
    z_e0 = zs2 + (zrd - zs2) * (tv0 - vr) / (vrd - vr)
    z_e1 = zrd - k_ne * (tv1 - vrd)
    for va, vb, za, zb, kk in ((tv0, vrd, z_e0, zrd, "a"), (vrd, tv1, zrd, z_e1, "b")):
        mb_poly = [(0.0, za - 0.05), (vb - va, zb - 0.05), (vb - va, zte), (0.0, zte)]
        segs = bands(zte - min(za, zb) + 0.05, "plaster", ground=False, lod=lod)
        surface(mb, P3((tu1, va), 0.0), np.array([0, 1.0, 0]), UP, mb_poly, segs, 3.0 + (va - tv0), MAT, np.array([1.0, 0, 0]),
                t_base=min(za, zb) - 0.05)
    # hipped tower roof with overhang
    oh = 0.30
    ap = P3(t["apex_uv"], zl(t["apex_z"]))
    c = [(tu0 - oh, tv0 - oh), (tu1 + oh, tv0 - oh), (tu1 + oh, tv1 + oh), (tu0 - oh, tv1 + oh)]
    kz = (zl(t["apex_z"]) - zte) / (t["apex_uv"][1] - tv0)
    zc = zte - kz * oh * 0.8
    outs = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    for i in range(4):
        a, b = c[i], c[(i + 1) % 4]
        roof(mb, [P3(a, zc), P3(b, zc), ap], lod, "troof%d" % i)
        fascia(mb, P3(a, zc), P3(b, zc), np.array([outs[i][0], outs[i][1], 0.0]), lod, h=0.36, soffit=oh, key="tf%d" % i, gutter=True)
        hip_cap(mb, P3(a, zc), ap, lod)
    # chimneys (clinker) and the radio mast
    chimney(mb, (tu0 + 2.6, tv0 - 0.75), zts - 0.5, zts + 1.25, lod)
    chimney(mb, (tu1 - 3.2, tv0 - 0.75), zts - 0.5, zts + 1.25, lod)
    chimney(mb, (tu1 + 2.4, vrd - 1.6), zrd - 0.6, zrd + 0.95, lod)
    chimney(mb, (t["apex_uv"][0] - 1.9, t["apex_uv"][1] + 1.4), zte + 0.4, zl(t["apex_z"]) + 0.75, lod)
    sg = LAY["steel_galv"]
    if lod < 2:
        base = P3((t["apex_uv"][0] + 1.5, t["apex_uv"][1] + 0.4), zte + 0.8)
        mb.tube(base, base + UP * t["mast_h"], 0.045, 4 if lod else 6, MAT,
                ((sg["u"][0] + 0.1, sg["v"][0]), (sg["u"][0] + 0.3, sg["v"][1])), r2=0.02)
    downpipe(mb, (ua + 0.4, vs), (0, -1), PL_H, zs - 0.4, lod)
    downpipe(mb, (us - 0.3, vs), (0, -1), PL_H, zs - 0.4, lod)
    downpipe(mb, (ub - 0.4, vr), (0, -1), PL_H, zs2 - 0.4, lod)
    downpipe(mb, (ua + 0.4, vn), (0, 1), PL_H, zn - 0.4, lod)
    # yard canopy on posts
    cn = D["canopy"]
    if lod < 2:
        (cu0, cu1), (cv0, cv1) = cn["u"], cn["v"]
        z0, z1 = zl(cn["z"][0]), zl(cn["z"][0]) + 0.22
        cc = ((cu0 + cu1) / 2, (cv0 + cv1) / 2)
        f = LAY["fascia"]
        mb.box(cc, (1, 0), (cu1 - cu0) / 2, (cv1 - cv0) / 2, z0, z1, MAT, ((0.2, f["v0"] + 0.08), (0.2 + 3.0, f["v0"] + 0.30)), top=True, bottom=True)
        for uu in np.linspace(cu0 + 0.3, cu1 - 0.3, 4):
            mb.tube(P3((uu, cv1 - 0.2), -0.3), P3((uu, cv1 - 0.2), z0), 0.05, 4 if lod else 6, MAT,
                    ((sg["u"][0] + 0.1, sg["v"][0]), (sg["u"][0] + 0.4, sg["v"][1])))


def build_hall(mb, lod):
    h, m, lk = D["hall"], D["middle"], D["link"]
    (u0, u1), (v0, v1) = h["u"], h["v"]
    ze, zc = zl(h["eave_z"]), zl(h["crown_z"])
    half = (u1 - u0) / 2
    rise = zc - ze
    R = (half ** 2 + rise ** 2) / (2 * rise)
    cz = zc - R
    a_max = math.asin(half / R)
    nseg = {0: 12, 1: 8, 2: 4}[lod]

    def arc(s):                       # s = 0..(u1-u0) along the gable
        return cz + math.sqrt(max(R * R - (s - half) ** 2, 0.0))
    ss = [half + R * math.sin(-a_max + 2 * a_max * k / nseg) for k in range(nseg + 1)]
    ss[0], ss[-1] = 0.0, u1 - u0
    top = [(s, arc(s)) for s in ss]
    rw, lt, nb = h["round_window"], h["lettering"], h["number"]
    ga = LAY["arch"]
    assert abs(rw["d"] - LAY["round"]["d"]) < 1e-6, "dims.json round_window.d != atlas_layout round.d"
    ops = [(uu - u0, h["arch_window_sill_z"], ga["w"], ga["spring"] + ga["rise"], "arch") for uu in h["arch_windows_u"]]
    ops.append((rw["u"] - u0, rw["z"] - rw["d"] / 2, rw["d"], rw["d"], "round"))
    wall(mb, (u0, v0), (u1, v0), 0.0, ze, lod, ops, top=top, key="hsw")
    opn = [(3.0, 0.0, 1.1, 2.2, "entry"), (9.0, 0.0, 1.1, 2.2, "entry")] + [(s, 5.6, 1.5, 1.5, "plain") for s in (3.0, 6.0, 9.0)]
    wall(mb, (u1, v1), (u0, v1), 0.0, ze, lod, opn, top=top, key="hne")
    # side walls: SE full height (bays of windows, WORKING_VALUE), NW above the link roofs + the projecting stub
    Ls = v1 - v0
    wse = [(s, 0.95, 1.5, 1.5, "plain") for s in np.linspace(2.6, Ls - 2.6, 5)] + \
          [(s + ds, 6.2, 1.2, 0.8, "ribbon") for s in np.linspace(2.6, Ls - 2.6, 5) for ds in (-0.6, 0.6)]
    wall(mb, (u1, v0), (u1, v1), 0.0, ze, lod, wse, key="hse")
    vr, vn = m["v_sw_recess"], m["v_ne"]
    wall(mb, (u0, vr), (u0, v0), 0.0, ze, lod, key="hnw0")
    zs2 = zl(m["eave_sw_z"]) + (zl(D["tower"]["roof_foot_sw_z"]) - zl(m["eave_sw_z"])) / (D["tower"]["v"][0] - m["v_sw"]) * (vr - m["v_sw"])
    zrd, vrd, zn = zl(lk["ridge_z"]), lk["ridge_v"], zl(m["eave_ne_z"])
    for va, vb, za, zb in ((vr, vrd, zs2, zrd), (vrd, v1, zrd, zrd - (zrd - zn) * (v1 - vrd) / (vn - vrd))):
        poly = [(0.0, zb - 0.05), (vb - va, za - 0.05), (vb - va, ze), (0.0, ze)]       # s runs from vb down to va
        segs = bands(ze - min(za, zb) + 0.05, "roof", ground=False, lod=lod)
        surface(mb, P3((u0, vb), 0.0), np.array([0, -1.0, 0]), UP, poly, segs, 5.0 + round(va), MAT, np.array([-1.0, 0, 0]),
                t_base=min(za, zb) - 0.05)
    # barrel roof: strips along the arc, cut at the band boundaries; ribs follow the arc
    oh = 0.25
    arc_len = R * a_max
    cuts = {0.0, arc_len}
    for t0, t1, _, _ in bands(arc_len, "roof", lod=lod):
        cuts |= {t0, t1}
    step = arc_len / {0: 6, 1: 4, 2: 2}[lod]
    cuts |= {k * step for k in range(1, int(arc_len / step))}
    cuts = sorted(cuts)
    segs = bands(arc_len, "roof", lod=lod)
    uo = round(h01(ASSET, "barrel") * 13.0 / 0.25) * 0.25
    for side in (-1.0, 1.0):
        for ta, tb in zip(cuts[:-1], cuts[1:]):
            if tb - ta < 1e-4:
                continue
            seg = next(s_ for s_ in segs if s_[0] - 1e-9 <= (ta + tb) / 2 <= s_[1] + 1e-9)

            def pt(t, vv):
                ang = side * (a_max - t / R)
                ext = 0.0 if t > 1e-6 else oh * 0.6      # the eave edge reaches out over the wall
                return P3((u0 + half + (R + 0.02) * math.sin(ang) + side * ext, vv), cz + (R + 0.02) * math.cos(ang) - ext * math.tan(a_max))

            def vm(t):
                return seg[2] + (seg[3] - seg[2]) * (t - seg[0]) / (seg[1] - seg[0])
            mb.face([pt(ta, v0 - oh), pt(ta, v1 + oh), pt(tb, v1 + oh), pt(tb, v0 - oh)],
                    [(uo, vm(ta)), (uo + Ls + 2 * oh, vm(ta)), (uo + Ls + 2 * oh, vm(tb)), (uo, vm(tb))], MAT, UP)
    if lod < 2:
        # arched verge trim on both gables, eave fascias along the sides
        f = LAY["fascia"]
        for vv, o in ((v0 - oh, -1.0), (v1 + oh, 1.0)):
            run = 0.0
            for (sa, za), (sb, zb) in zip(top[:-1], top[1:]):
                a, b = P3((u0 + sa, vv), za + 0.03), P3((u0 + sb, vv), zb + 0.03)
                L = float(np.linalg.norm(b - a))
                dn = np.array([0, 0, -0.22])      # r4: 0.42 -> 0.22 m, the verge flashing is a thin line on photo 7197 (~0.15 m)
                mb.face([a + dn, b + dn, b, a], [(run, f["v0"] + 0.09), (run + L, f["v0"] + 0.09), (run + L, f["v0"] + 0.31), (run, f["v0"] + 0.31)],
                        MAT, np.array([0, o, 0.0]))
                if lod == 0:      # soffit of the verge
                    back = np.array([0, -o * oh, 0.0])
                    mb.face([a + dn, b + dn, b + dn + back, a + dn + back],
                            [(run, f["v0"] + 0.1), (run + L, f["v0"] + 0.1), (run + L, f["v0"] + 0.3), (run, f["v0"] + 0.3)], MAT, -UP)
                run += L
        ez = ze - oh * 0.6 * math.tan(a_max)
        fascia(mb, P3((u1 + oh * 0.6, v0 - oh), ez), P3((u1 + oh * 0.6, v1 + oh), ez), np.array([1.0, 0, 0]), lod, h=0.36, soffit=oh * 0.6, key="he", gutter=True)
        fascia(mb, P3((u0 - oh * 0.6, v1 + oh), ez), P3((u0 - oh * 0.6, v0 - oh), ez), np.array([-1.0, 0, 0]), lod, h=0.36, soffit=oh * 0.6, key="hw", gutter=True)
        # lettering (alpha test), 3 cm proud of the gable
        for r, a in ((lt, ALAY["lettering"]), (nb, ALAY["number"])):
            q = [P3((r["u"][0], v0 - 0.03), r["z"][0]), P3((r["u"][1], v0 - 0.03), r["z"][0]),
                 P3((r["u"][1], v0 - 0.03), r["z"][1]), P3((r["u"][0], v0 - 0.03), r["z"][1])]
            mb.face(q, [(a["u"][0], a["v"][0]), (a["u"][1], a["v"][0]), (a["u"][1], a["v"][1]), (a["u"][0], a["v"][1])],
                    ALPHA, np.array([0, -1.0, 0]))
    if lod == 0 and "vents" in h:               # r4: ochre vent squares under the verge (photo 7197), 2 cm proud
        oc, vt = LAY["ochre"], h["vents"]
        hs_ = vt["size"] / 2
        for uu in vt["u"]:
            q = [P3((uu - hs_, v0 - 0.02), vt["z"] - hs_), P3((uu + hs_, v0 - 0.02), vt["z"] - hs_),
                 P3((uu + hs_, v0 - 0.02), vt["z"] + hs_), P3((uu - hs_, v0 - 0.02), vt["z"] + hs_)]
            ou, ov = oc["u"][0] + 0.2, oc["v"][0] + 0.9
            mb.face(q, [(ou, ov), (ou + vt["size"], ov), (ou + vt["size"], ov + vt["size"]), (ou, ov + vt["size"])], MAT, np.array([0, -1.0, 0]))
    downpipe(mb, (u1, v0 + 0.4), (1, 0), PL_H, ze - 0.5, lod)
    downpipe(mb, (u1, v1 - 0.4), (1, 0), PL_H, ze - 0.5, lod)
    downpipe(mb, (u0 + 0.35, v0), (0, -1), PL_H, ze - 0.5, lod)


def build_outbuilding(mb, lod):
    o = D["outbuilding"]
    R_ = [np.array(p, float) for p in o["ring_uv"]]
    P0 = R_[0]
    a = (R_[1] - R_[0])
    La = float(np.linalg.norm(a))
    a /= La
    b = np.array([-a[1], a[0]])
    Lb = float((R_[3] - R_[0]) @ b)
    dz = DZ + o.get("lod2_zmin_offset_m", 0.0)
    ze, zr = o["eave_z"] + dz, o["ridge_z"] + dz
    zte, zta = o["turret_eave_z"] + dz, o["turret_apex_z"] + dz
    yr = Lb / 2

    def q(x, y):
        return P0 + a * x + b * y
    a3, b3 = np.append(a, 0.0), np.append(b, 0.0)
    sh = 2.9
    rows = (0.95, 0.95 + sh, 0.95 + 2 * sh)
    ws = [(s, z, 1.5, 1.5, "plain") for s in np.linspace(2.4, La - 2.4, 5) for z in rows[:2]]
    ws[0] = (ws[0][0], 0.0, 1.1, 2.2, "entry")
    wall(mb, q(0, 0), q(La, 0), 0.0, ze, lod, ws, key="osw")
    wn = [(s, z, 1.5, 1.5, "plain") for s in np.linspace(2.2, La - 2.2, 5) for z in rows[:2]]
    wall(mb, q(La, Lb), q(0, Lb), 0.0, ze, lod, wn, key="one")
    gt = [(0.0, ze), (yr, zr), (Lb, ze)]
    wall(mb, q(La, 0), q(La, Lb), 0.0, ze, lod, [(Lb / 2, z, 1.5, 1.5, "plain") for z in rows[:2]], top=gt, key="ose")
    wall(mb, q(0, Lb), q(0, 0), 0.0, ze, lod, [(Lb / 2, rows[0], 1.5, 1.5, "plain")], top=gt, key="onw")
    if lod < 2:      # blue sheet band under the eaves (as on the turret)
        bh = 1.15
        for i, (p, r) in enumerate(((q(0, 0), q(La, 0)), (q(La, 0), q(La, Lb)), (q(La, Lb), q(0, Lb)), (q(0, Lb), q(0, 0)))):
            d2 = (r - p) / np.linalg.norm(r - p)
            L = float(np.linalg.norm(r - p))
            nout = np.array([d2[1], -d2[0], 0.0])
            surface(mb, P3(p + nout[:2] * 0.025, 0.0), np.append(d2, 0.0), UP, [(0, ze - bh), (L, ze - bh), (L, ze), (0, ze)],
                    bands(bh, "roof", ground=False, lod=lod), round(i * 2.75, 2), MAT, nout, t_base=ze - bh)
    oh = 0.3
    k = (zr - ze) / yr
    for sgn, y_e, key in ((1.0, 0.0, "a"), (-1.0, Lb, "b")):
        ye = y_e - sgn * oh
        zee = ze - k * oh
        e0, e1 = (-oh, La + oh) if sgn > 0 else (La + oh, -oh)
        roof(mb, [P3(q(e0, ye), zee), P3(q(e1, ye), zee), P3(q(e1, yr), zr), P3(q(e0, yr), zr)], lod, "o" + key)
        fascia(mb, P3(q(e0, ye), zee), P3(q(e1, ye), zee), -b3 * sgn, lod, h=0.36, soffit=oh, key="of" + key, gutter=True)
        for xx, oo in ((-oh, -1.0), (La + oh, 1.0)):
            fascia(mb, P3(q(xx, ye), zee), P3(q(xx, yr), zr), a3 * oo, lod, h=0.30, key="og" + key)
    # turret over the rear NW part: blue sheet cladding, pyramid roof
    tx0, tx1 = o["turret_along"]
    ty0, ty1 = Lb * 0.36, Lb
    c = [q(tx0, ty0), q(tx1, ty0), q(tx1, ty1), q(tx0, ty1)]
    zb_ = ze - 0.2
    for i in range(4):
        p, r = c[i], c[(i + 1) % 4]
        d2 = (r - p) / np.linalg.norm(r - p)
        L = float(np.linalg.norm(r - p))
        nout = np.array([d2[1], -d2[0], 0.0])
        segs = bands(zte - zb_, "roof", lod=lod)
        surface(mb, P3(p, 0.0), np.append(d2, 0.0), UP, [(0, zb_), (L, zb_), (L, zte), (0, zte)], segs,
                round(i * 3.25, 2), MAT, nout, t_base=zb_)
    cc = (c[0] + c[2]) / 2
    ap = P3(cc, zta)
    oh2 = 0.25
    ce = [cc + (p - cc) + np.sign((p - cc) @ a) * a * oh2 + np.sign((p - cc) @ b) * b * oh2 for p in c]
    zce = zte - 0.08
    for i in range(4):
        p, r = ce[i], ce[(i + 1) % 4]
        d2 = (r - p) / np.linalg.norm(r - p)
        roof(mb, [P3(p, zce), P3(r, zce), ap], lod, "ot%d" % i)
        fascia(mb, P3(p, zce), P3(r, zce), np.array([d2[1], -d2[0], 0.0]), lod, h=0.34, soffit=oh2, key="otf%d" % i)
        hip_cap(mb, P3(p, zce), ap, lod)
    chimney(mb, q(La * 0.62, yr + 1.6), zr - 0.7, zr + 0.8, lod)
    downpipe(mb, q(0.4, 0), -b, PL_H, ze - 0.4, lod)
    downpipe(mb, q(La - 0.4, 0), -b, PL_H, ze - 0.4, lod)


THUJA_HABITS = (
    ((0,.50),(.08,.90),(.35,1),(.72,.91),(.90,.65),(.975,.29),(1,.06)),
    ((0,.80),(.10,1),(.32,.83),(.56,.58),(.79,.34),(.96,.15),(1,.03)),
    ((0,.38),(.12,.74),(.40,1),(.66,.91),(.84,.64),(.96,.29),(1,.07)),
)


def foliage_uv(key=0, level=0):
    """Own atlas leaf palette for BOTH runtime geometry LODs, with a safe gutter."""
    r = LAY["thuja_far"]
    u = r["u"][0] + .08 + (key % 3) * .30
    v = r["v"][0] + .08 + (level % 3) * .20
    return [(u,v),(u+.48,v),(u+.48,v+.38),(u,v+.38)]


def build_thuja(mb, c, height, radius, key, lod):
    habit = key % 3
    profile = THUJA_HABITS[habit]
    if lod:
        profile = (profile[0],profile[2],profile[3],profile[-1])
        if habit == 1:
            profile = (profile[0],profile[1],profile[-1])
    sides = 8 if lod == 0 else 4
    lean = np.array([h01(key,"lx")-.5,h01(key,"ly")-.5]) * .3
    for layer,grow,mat in ((0,0,MAT),(1,.07,HERO_SHELL)):
        if layer and lod:
            continue
        rings = []
        for j,(f,rr) in enumerate(profile):
            ring = []
            for i in range(sides):
                angle = i*2*math.pi/sides + key + .24*math.sin(j)
                rad = radius*rr*(.86+.28*h01(key,j,i)) + grow
                ring.append(c + np.r_[lean*f*f + np.array([math.cos(angle),math.sin(angle)])*rad,
                                      height*f + (grow if j == len(profile)-1 else 0)])
            rings.append(ring)
        for j in range(1 if layer else 0,len(rings)-1):
            for i in range(sides):
                ii = (i+1)%sides
                uv = foliage_uv(key+i,j)
                if layer:
                    per = 2*math.pi*radius/sides/.6
                    u0,u1 = (i*per+key*.37),(i+1)*per+key*.37
                    v0,v1 = profile[j][0]*height/.6,profile[j+1][0]*height/.6
                    uv = [(u0,v0),(u1,v0),(u1,v1),(u0,v1)]
                mb.face([rings[j][i],rings[j][ii],rings[j+1][ii],rings[j+1][i]],uv,mat,
                        np.append((rings[j][i]+rings[j][ii])[:2]/2-c[:2],.15))


def build_conifer(mb, c, height, radius, key, lod):
    """Root-attached short-needle boughs; Low36cards fits the original whole-plant budget.

    The scan is fir/conifer, NOT a verified Picea. Existing fire_station_alpha is already
    CullOff: one quad per bough, no mirrored duplicate and no extra Low material/batch.
    """
    u0,v0,u1,v1 = ALAY["conifer_bough"]["inner_uv"]
    for j,base_f in enumerate((.08,.17,.27,.36,.45,.55,.65,.76,.87)):
        count = 6 if lod == 0 else 4
        for i in range(count):
            angle = key*.63+j*1.69+i*2*math.pi/count+.35*(h01(key,j,i,"azimuth")-.5)
            f = base_f+.04*(h01(key,j,i,"level")-.5)
            direction = np.array([math.cos(angle),math.sin(angle)])
            root = c + np.array([0,0,height*f])
            length = radius*(1-f)**.7*(1.03+.30*h01(key,j,i))
            tip = c + np.r_[direction*length,height*(f-.04)]
            roll = .50*(h01(key,j,i,"roll")-.5)
            side = (UP*math.cos(roll)+np.r_[-direction[1],direction[0],0]*math.sin(roll))*min(length*.65,height*f*.90)
            mb.face([root-side,root+side,tip+side,tip-side],[(u0,v0),(u1,v0),(u1,v1),(u0,v1)],ALPHA)
    # Continuous inner mass instead of four isolated diamonds. The broader lower third
    # and asymmetric radii carry the envelope; clipped outer sprays keep branch gaps.
    fill = D["spruce"].get("inner_core_fill_r_WORKING_VALUE", .55)
    profile = ((.055,.42),(.27,1.0),(.60,.58),(.975,.03))
    sides = 8 if lod == 0 else 6
    rings, normals = [], []
    for j,(f,shape) in enumerate(profile):
        ring, nr = [], []
        lo, hi = max(0,j-1), min(len(profile)-1,j+1)
        slope = -radius*fill*(profile[hi][1]-profile[lo][1])/(height*(profile[hi][0]-profile[lo][0]))
        for i in range(sides):
            angle = i*2*math.pi/sides+key*.63+.12*math.sin(j*1.4+key)
            rr = max(radius*.025,radius*fill*shape*(.86+.28*h01(key,j,i,"inner")))
            level = f+.014*(h01(key,j,i,"z")-.5)*(j<len(profile)-1)
            ring.append(c+np.array([math.cos(angle)*rr,math.sin(angle)*rr,height*level]))
            nr.append(np.array([math.cos(angle),math.sin(angle),slope]))
        rings.append(ring); normals.append(nr)
    for j in range(len(rings)-1):
        for i in range(sides):
            ii = (i+1)%sides
            mb.face([rings[j][i],rings[j][ii],rings[j+1][ii],rings[j+1][i]],foliage_uv(key+i,j),MAT,
                    np.r_[(rings[j][i]+rings[j][ii])[:2]/2-c[:2],.15],
                    normals=[normals[j][i],normals[j][ii],normals[j+1][ii],normals[j+1][i]])
    # A plain dark atlas swatch is a WORKING_VALUE trunk colour, not a claimed bark scan.
    r = LAY["dark"]; uv = [((r["u"][0]+r["u"][1])/2,(r["v"][0]+r["v"][1])/2)]*3
    pts = [c+[-.045,-.045,0],c+[.045,-.045,0],c+[0,.045,0],c+[0,0,height]]
    for face in ((0,2,1),(0,1,3),(0,3,2),(1,2,3)):
        mb.face([pts[i] for i in face],uv,MAT)


def build_site(mb, lod):
    """Fence with posts and concrete footing, parked sliding gate, thuja row, flag poles (all on the spec ground)."""
    if lod >= 2:
        return
    G = SPEC["ground"]
    fh = D["fence"]["h"]
    ph = D["fence"]["plinth_h"]
    sw = ALAY["swatch_blue"]
    sw_uv = ((sw["u"][0], sw["v"][0]), (sw["u"][1], sw["v"][1]))
    pl = LAY["plinth"]

    def bay(p, q, rect, y_off=0.0, foot=True):
        p, q = en_to_uvz(p), en_to_uvz(q)
        L = float(np.linalg.norm(q[:2] - p[:2]))
        if L < 0.05:
            return
        d2 = (q[:2] - p[:2]) / L
        n2 = np.array([-d2[1], d2[0]])
        f = min(L / rect["size_m"][0], 1.0)
        ua, ub = rect["u"][0], rect["u"][0] + (rect["u"][1] - rect["u"][0]) * f
        za, zb = p[2] + ph + y_off, q[2] + ph + y_off
        mb.face([P3(p[:2], za), P3(q[:2], zb), P3(q[:2], zb + fh), P3(p[:2], za + fh)],
                [(ua, rect["v"][0]), (ub, rect["v"][0]), (ub, rect["v"][1]), (ua, rect["v"][1])], ALPHA, np.append(-n2, 0.0))
        # r4: ONE face per bay, normal towards the street. The alpha material is double sided in the engine (Cull Off);
        # the mirrored duplicate (two_sided) rendered the bars pale grey in Unity (r3 / r4 frames: 141,146,161 over a
        # dark thuja = environment reflection at Fresnel 1, i.e. a degenerate shading normal on the coincident pair).
        if foot:
            for sgn in (-1.0, 1.0):
                o2 = n2 * 0.10 * sgn
                mb.face([P3(p[:2] + o2, p[2] - 0.5), P3(q[:2] + o2, q[2] - 0.5), P3(q[:2] + o2, q[2] + ph), P3(p[:2] + o2, p[2] + ph)],
                        [(p[0], pl["v0"]), (p[0] + L, pl["v0"]), (p[0] + L, pl["v0"] + 0.5 + ph), (p[0], pl["v0"] + 0.5 + ph)],
                        MAT, np.append(o2, 0.0))
            mb.face([P3(p[:2] - n2 * 0.10, p[2] + ph), P3(q[:2] - n2 * 0.10, q[2] + ph), P3(q[:2] + n2 * 0.10, q[2] + ph), P3(p[:2] + n2 * 0.10, p[2] + ph)],
                    [(p[0], pl["v0"] + 0.4), (p[0] + L, pl["v0"] + 0.4), (p[0] + L, pl["v0"] + 0.6), (p[0], pl["v0"] + 0.6)], MAT, UP)

    def post(p, hh, w=0.04):
        if lod > 0:
            return
        p = en_to_uvz(p)
        mb.box(p[:2], (1, 0), w, w, p[2] + ph - 0.02, p[2] + ph + hh, ALPHA, sw_uv, top=True)

    for ln in G["fence"]:
        for p, q in zip(ln[:-1], ln[1:]):
            bay(p, q, ALAY["fence_bay"])
        for p in ln:
            post(p, fh + 0.06)
    if G["gate"]:
        for p, q in zip(G["gate"][:-1], G["gate"][1:]):
            bay(p, q, ALAY["gate_bay"], y_off=-ph + 0.12, foot=False)
        for p in (G["gate"][0], G["gate"][-1]):
            post([p[0], p[1], p[2] - ph + 0.1], fh + 0.15, w=0.05)
    # r7: all plants remain inside this existing hero node/LOD/material batching contract.
    for e,n,z,height,radius,key in G["thuja"]:
        build_thuja(mb,en_to_uvz([e,n,z])-[0,0,.05],height,radius,key,lod)
    for e,n,z,height,radius,key in G.get("spruce",[]):
        build_conifer(mb,en_to_uvz([e,n,z]),height,radius,key,lod)
    # flag poles with the national flag
    sg, fl = LAY["steel_galv"], LAY["flag"]
    for i, p in enumerate(G["flagpoles"]):
        c = en_to_uvz(p)
        hp = D["flagpoles"]["h"]
        mb.tube(P3(c[:2], c[2] - 0.1), P3(c[:2], c[2] + hp), 0.05, 6 if lod == 0 else 3, MAT,
                ((sg["u"][0] + 0.1, sg["v"][0]), (sg["u"][0] + 0.4, sg["v"][1])), r2=0.03)
        if i == 0:
            z1 = c[2] + hp - 0.15
            pts = [(0.03, 0.0), (0.55, 0.10), (1.05, 0.02), (1.55, 0.14)]
            for (xa, ya), (xb, yb) in zip(pts[:-1], pts[1:]):
                A_, B_ = c[:2] + np.array([xa, ya]), c[:2] + np.array([xb, yb])
                fa, fb = xa / 1.6, xb / 1.6
                ua, ub = fl["u"][0] + fa * 1.6, fl["u"][0] + fb * 1.6
                drop_a, drop_b = 0.10 * fa, 0.10 * fb
                mb.face([P3(A_, z1 - 1.0 - drop_a), P3(B_, z1 - 1.0 - drop_b), P3(B_, z1 - drop_b), P3(A_, z1 - drop_a)],
                        [(ua, fl["v"][0]), (ub, fl["v"][0]), (ub, fl["v"][1]), (ua, fl["v"][1])], MAT, None, two_sided=True)


def build(lod):
    mb = MB()
    build_garage(mb, lod)
    build_middle(mb, lod)
    build_hall(mb, lod)
    build_outbuilding(mb, lod)
    build_site(mb, lod)
    return mb


def main():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    name = f"landmark_{ASSET}"
    tris = []
    for lod in range(3):
        _, n = build(lod).to_object(name + ("" if lod == 0 else f".lod{lod}"))
        tris.append(n)
    OUT.mkdir(parents=True, exist_ok=True)
    glb = OUT / f"{ASSET}.glb"
    if RENDER:
        render(Path(arg("--render")), name)
        print("FIRE_STATION_RENDER: OK", tris)
        return
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_yup=True, export_apply=False,
                              export_texcoords=True, export_normals=True, export_materials="EXPORT",
                              export_image_format="NONE", export_tangents=False, export_animations=False,
                              export_cameras=False, export_lights=False, export_extras=False)
    if "--blend" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{ASSET}.blend"))
    meta = {
        "schema": "truck-sim-pl/hero-building-asset/1", "asset": ASSET, "prototype": name,
        "spec": SPEC_PATH.relative_to(REPO).as_posix(), "spec_sha256": sha(SPEC),
        "glb_sha256": hashlib.sha256(glb.read_bytes()).hexdigest(), "blender": bpy.app.version_string,
        "materials": [MAT, ALPHA, HERO_SHELL], "anchor": SPEC["anchor"], "tris": tris,
        "lod_ends_m": SPEC.get("lod_ends_m"),
        "conifer_foliage": json.loads((OUT / "conifer_foliage_meta.json").read_text()) if (OUT / "conifer_foliage_meta.json").exists() else {"applied": False},
        "axes": "glTF (x, y, z) = (-dE, dU, dN) relative to the anchor (local E, N, U)",
    }
    (OUT / f"{ASSET}_meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("FIRE_STATION_RESULT: OK", glb, tris)


def render(out, name):
    """Control renders in world placement (EEVEE): fixed cameras in the building frame, overcast + sun."""
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    gz = SPEC["ground"]["footprint_min"] - FLOOR

    def bl(u, v, z):
        e = AX_U * u + AX_V * v + (AX_O - ANCHOR[:2])
        return np.array([-e[0], -e[1], z])
    bpy.ops.mesh.primitive_plane_add(size=900, location=tuple(bl(30, 0, gz - 0.02)))
    g = bpy.context.object
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.11, 0.13, 0.075, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    g.data.materials.append(gm)
    # asphalt apron in front of the garage (approximation of the paved yard, for the control renders only)
    bpy.ops.mesh.primitive_plane_add(size=1, location=tuple(bl(9, -13, gz + 0.0)))
    ap = bpy.context.object
    ap.scale = (26, 28, 1)
    ap.rotation_euler = (0, 0, math.atan2(-AX_U[1], -AX_U[0]))
    am = bpy.data.materials.new("apron")
    am.use_nodes = True
    am.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.09, 0.09, 0.09, 1)
    am.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.9
    ap.data.materials.append(am)
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    sky = w.node_tree.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    w.node_tree.links.new(sky.outputs["Color"], w.node_tree.nodes["Background"].inputs["Color"])
    bpy.ops.object.light_add(type="SUN")
    sun = bpy.context.object
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.view_settings.view_transform = "AgX"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.eevee.use_shadows = True
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_gtao = True
    except Exception:      # noqa: BLE001
        pass
    cams = {      # (u, v, z) eye, (u, v, z) target, horizontal FOV
        "route_s1335": ((24.0, -52.3, gz + 2.5), (30.0, 0.0, 5.0), 60.0),
        "route_approach": ((75.0, -58.0, gz + 2.5), (36.0, 0.0, 5.0), 60.0),
        "ref_7197": ((36.0, -82.0, gz + 1.7), (39.0, 0.0, 6.5), 34.0),
        "ref_garage": ((-28.0, -66.0, gz + 2.2), (13.0, 0.0, 4.0), 30.0),
        "ref_strudel": ((-45.0, -64.0, gz + 2.0), (28.0, 2.0, 5.5), 30.0),
        "gable_close": ((43.0, -24.0, gz + 1.7), (42.0, 0.0, 6.0), 55.0),
        "yard_ne": ((20.0, 75.0, gz + 8.0), (30.0, 20.0, 4.0), 55.0),
        "aerial": ((-35.0, -70.0, 48.0), (35.0, 12.0, 3.0), 50.0),
    }
    lights = {"overcast": (1.0, math.radians(55), 200.0, 0.6), "sun": (0.22, math.radians(40), 215.0, 3.5)}
    only_light = arg("--light")
    lods = {"": "lod0", ".lod1": "lod1", ".lod2": "lod2"}
    bg = w.node_tree.nodes["Background"]
    for lname, (wstr, elev, az, energy) in lights.items():
        if only_light and lname != only_light:
            continue
        for l in list(bg.inputs["Color"].links):
            w.node_tree.links.remove(l)
        if lname == "overcast":
            bg.inputs["Color"].default_value = (0.74, 0.79, 0.86, 1)
        else:
            sky.sun_elevation = elev
            sky.sun_rotation = math.radians(az)
            w.node_tree.links.new(sky.outputs["Color"], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = wstr
        # sun azimuth az (from north, clockwise) in E/N -> Blender (-E, -N)
        sdir = np.array([math.sin(math.radians(az)) * math.cos(elev), math.cos(math.radians(az)) * math.cos(elev), math.sin(elev)])
        d = -np.array([-sdir[0], -sdir[1], sdir[2]])
        sun.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
        sun.data.energy = energy
        sun.data.angle = math.radians(40 if lname == "overcast" else 1.0)
        for suf, tag in lods.items():
            for s2 in lods:
                bpy.data.objects[name + s2].hide_render = s2 != suf
            for cid, (pos, look, fov) in cams.items():
                if tag != "lod0" and (cid not in ("route_s1335", "aerial") or lname != "overcast"):
                    continue
                cd = bpy.data.cameras.new(cid)
                cd.sensor_fit = "HORIZONTAL"
                cd.angle = math.radians(fov)
                cd.clip_end = 3000
                co = bpy.data.objects.new(cid, cd)
                sc.collection.objects.link(co)
                p, l = bl(*pos), bl(*look)
                co.location = p
                dd = l - p
                co.rotation_euler = (math.atan2(math.hypot(dd[0], dd[1]), -dd[2]), 0, math.atan2(dd[1], dd[0]) - math.pi / 2)
                sc.camera = co
                sc.render.filepath = str(out / f"{cid}__{lname}__{tag}.png")
                bpy.ops.render.render(write_still=True)


main()
