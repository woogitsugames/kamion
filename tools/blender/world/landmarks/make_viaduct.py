"""Hero viaduct asset from a worldgen spec (ADR 0067, override kind: hero_bridge).

    blender -b --factory-startup -P tools/blender/world/landmarks/make_viaduct.py -- \
        --spec Data/Regions/bialystok-industrial-c/generated/landmarks/viaduct_biezenstwa.spec.json \
        [--render <abs dir>] [--blend]

Reads the spec written by tools/worldgen/streetscape/hero_bridge.py (deck edge rails per station, pier lines, cuts,
dimensions) and writes art-source/world/landmarks/<asset>/<asset>.glb + <asset>_meta.json:

  nodes  landmark_<asset>_<k>, .lod1, .lod2 per segment (both carriageways of one cut), <asset>.collision
  frame  vertices relative to the segment anchor; glTF (x, y, z) = (-dE, dU, dN) like street_props.glb, so the
         engine instance (yaw 0) at the anchor puts every vertex on its generated position
  UV0    viaduct_concrete: metres into the strip atlas (atlas_layout.json); viaduct_steel: 0..1 (railing bay /
         steel swatch)

Geometry is built from the spec only (deterministic); nothing is modelled by hand. LOD0: cornice, edge beam,
cantilever, web, bottom flange, chamfered columns with bearing plinths, abutment faces, railing (posts, handrail,
alpha infill), drainage collector with hangers and downpipes, expansion-joint strips, CCTV housing. LOD1: every
second station, no posts / hangers / plinths, 3-sided pipes. LOD2: silhouette.
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
LAY = json.loads((OUT / "atlas_layout.json").read_text(encoding="utf-8"))
PRM = SPEC["params"]
CONC, STEEL = "viaduct_concrete", "viaduct_steel"
STEEL_UV = ((0.80, 0.15), (0.96, 0.15), (0.96, 0.85), (0.80, 0.85))
# pipes are painted with the concrete atlas (r10, reference frame 201270605169291): grey PVC collector = plain concrete
# swatch, thin red conduit at the cantilever root = cornice paint band (between two plate joints)
_sp = LAY["swatch_plain"]
PIPE_UV = ((_sp["u"][0] + 0.2, _sp["v"][0] + 0.2), (_sp["u"][0] + 1.2, _sp["v"][0] + 0.2),
           (_sp["u"][0] + 1.2, _sp["v"][0] + 0.8), (_sp["u"][0] + 0.2, _sp["v"][0] + 0.8))
_cv = LAY["cornice"]["v0"]
RED_UV = ((0.4, _cv + 0.15), (2.4, _cv + 0.15), (2.4, _cv + 0.42), (0.4, _cv + 0.42))


def sha(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class MB:
    """Quad soup with per-corner UV and a material per face."""

    def __init__(self):
        self.V, self.F, self.UV, self.M = [], [], [], []

    def quad(self, P, UV, mat, hint=None):
        P = [np.asarray(p, float) for p in P]
        if hint is not None:
            n = np.cross(P[1] - P[0], P[-1] - P[0])
            if float(np.dot(n, hint)) < 0:
                P, UV = P[::-1], UV[::-1]
        b = len(self.V)
        self.V += P
        self.F.append(tuple(range(b, b + len(P))))
        self.UV.append([tuple(map(float, u)) for u in UV])
        self.M.append(mat)

    def box(self, c, ax, ay, hx, hy, z0, z1, mat, uvrect, top=True, bottom=False):
        """Vertical box, horizontal axes ax / ay (unit 2D), half sizes hx / hy; every face mapped to uvrect."""
        c = np.asarray(c, float)
        ax, ay = np.asarray(ax, float), np.asarray(ay, float)
        cs = [c + ax * sx * hx + ay * sy * hy for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        (u0, v0), (u1, v1) = uvrect
        uv = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
        for i in range(4):
            p, q = cs[i], cs[(i + 1) % 4]
            out = np.append((p + q) / 2 - c, 0.0)
            self.quad([(*p, z0), (*q, z0), (*q, z1), (*p, z1)], uv, mat, out)
        if top:
            self.quad([(*p, z1) for p in cs], uv, mat, (0, 0, 1))
        if bottom:
            self.quad([(*p, z0) for p in cs], uv, mat, (0, 0, -1))

    def tube(self, A, B, r, sides, mat, up=(0, 0, 1), uv=None):
        uv = uv or STEEL_UV
        A, B = np.asarray(A, float), np.asarray(B, float)
        d = B - A
        d /= np.linalg.norm(d)
        x = np.cross(d, up)
        if np.linalg.norm(x) < 1e-6:
            x = np.array([1.0, 0, 0])
        x /= np.linalg.norm(x)
        y = np.cross(x, d)
        ang = [2 * math.pi * k / sides + math.pi / sides for k in range(sides + 1)]
        ring = [x * math.cos(a) * r + y * math.sin(a) * r for a in ang]
        for k in range(sides):
            o = (ring[k] + ring[k + 1]) / 2
            self.quad([A + ring[k], B + ring[k], B + ring[k + 1], A + ring[k + 1]], uv, mat, o)

    def tris(self):
        return sum(len(f) - 2 for f in self.F)

    def to_object(self, name, anchor, smooth_angle=50.0):   # 50: the 45 deg column chamfers shade round (reference)
        me = bpy.data.meshes.new(name)
        a = np.asarray(anchor, float)
        V = np.array(self.V) - a
        V = np.column_stack([-V[:, 0], -V[:, 1], V[:, 2]])          # Blender (-dE, -dN, dU) -> glTF (-dE, dU, dN)
        me.from_pydata([tuple(v) for v in V], [], self.F)
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
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=5e-4)
        bm.to_mesh(me)
        bm.free()
        me.set_sharp_from_angle(angle=math.radians(smooth_angle))
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        me.calc_loop_triangles()
        return ob, len(me.loop_triangles)


_MATS = {}


def material(name):
    if name in _MATS:
        return _MATS[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85 if name == CONC else 0.5
    tex_root = REPO / "art-source" / "world"
    png = (tex_root / "materials" / CONC / "Medium" / f"T_{CONC}_BaseColor.png") if name == CONC else \
        (tex_root / "textures" / "viaduct_steel.png")
    if png.exists() and "--render" in argv:      # preview only: the GLB carries material names, not textures
        img = nt.nodes.new("ShaderNodeTexImage")
        img.image = bpy.data.images.load(str(png))
        if name == CONC:
            mp = nt.nodes.new("ShaderNodeMapping")
            tc = nt.nodes.new("ShaderNodeTexCoord")
            mp.inputs["Scale"].default_value = (1 / LAY["tile_m"][0], 1 / LAY["tile_m"][1], 1)
            nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
            nt.links.new(mp.outputs["Vector"], img.inputs["Vector"])
        else:
            nt.links.new(img.outputs["Alpha"], bsdf.inputs["Alpha"])
            m.blend_method = "CLIP" if hasattr(m, "blend_method") else m.blend_method
            bsdf.inputs["Metallic"].default_value = 0.6
        nt.links.new(img.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (0.36, 0.35, 0.31, 1) if name == CONC else (0.4, 0.41, 0.42, 1)
    m.use_backface_culling = name == CONC
    _MATS[name] = m
    return m


# ------------------------------------------------------------------------------------------------ section frame
class St:
    def __init__(self, d):
        self.s = d["s"]
        self.L, self.R = np.array(d["l"]), np.array(d["r"])
        self.Lg, self.Rg = np.array(d["lg"]), np.array(d["rg"])
        self.t = np.array(d["t"] + [0.0])
        self.open = d["open"]
        self.zc, self.zl, self.zr = d["zc"], d["zl"], d["zr"]
        dv = self.L[:2] - self.R[:2]
        self.hb = float(np.linalg.norm(dv)) / 2
        self.n = np.append(dv / (2 * self.hb), 0.0)
        self.mid = (self.L + self.R) / 2
        self.slope = (self.L[2] - self.R[2]) / (2 * self.hb)

    def at(self, x, d=0.0):
        """Point at lateral x (towards L +) and d above the cap top line (tilted with the crossfall)."""
        p = self.mid + self.n * x
        p[2] = self.mid[2] + self.slope * x + d
        return p


def profile(st, sgn, lod):
    """Half section on side sgn (+1 = L) as strips [(p_a, p_b, band, coord_a, coord_b)] from the cornice top down to
    the box centre line. band 'c' = cornice (coord = metres above the plate bottom), 'g' = girder strip (coord =
    unrolled metres from the cornice lip)."""
    hb, pr = st.hb, PRM["cornice_proud_m"]
    ch = PRM["cornice_h_m"]
    G = LAY["girder"]
    top = 0.02
    d1 = top - ch
    out = []
    c_top, c_bot = st.at(sgn * (hb + pr), top), st.at(sgn * (hb + pr), d1)
    if lod == 0:
        out.append((st.at(sgn * (hb - 0.04), top), c_top, "c", ch - 0.07, ch))
    out.append((c_top, c_bot, "c", ch, 0.0))
    lip = st.at(sgn * (hb - 0.05), d1)
    if lod < 2:
        out.append((c_bot, lip, "g", 0.0, G["lip"]))
    if not st.open:
        return out
    g = G["lip"]
    beam = st.at(sgn * (hb - 0.05), d1 - PRM["edge_beam_h_m"])
    out.append((lip if lod < 2 else c_bot, beam, "g", g, g + G["beam"]))
    g += G["beam"]
    root = st.at(sgn * PRM["cant_root_m"], -PRM["cant_root_drop_m"])
    out.append((beam, root, "g", g, g + G["cant"]))
    g += G["cant"]
    web = st.at(sgn * PRM["box_bottom_half_m"], -PRM["girder_depth_m"])
    out.append((root, web, "g", g, g + G["web"]))
    g += G["web"]
    out.append((web, st.at(0.0, -PRM["girder_depth_m"]), "g", g, g + G["bottom"]))
    return out


def band_v(band, coord):
    return (LAY["cornice"]["v0"] if band == "c" else LAY["girder"]["v0"]) + coord


def soffit_z(st, x):
    """Height of the cantilever soffit at lateral |x| between the edge beam and the cantilever root."""
    x0, d0 = st.hb - 0.05, 0.02 - PRM["cornice_h_m"] - PRM["edge_beam_h_m"]
    x1, d1 = PRM["cant_root_m"], -PRM["cant_root_drop_m"]
    f = (abs(x) - x1) / (x0 - x1)
    return st.at(x, d1 + (d0 - d1) * f)


def build_cell(mb, deck, di, c0, c1, lod, colmb):
    sts_all = [St(d) for d in deck["stations"] if c0 - 1e-6 <= d["s"] <= c1 + 1e-6]
    if len(sts_all) < 2:
        return
    so = deck["s_open"] or [1e9, -1e9]
    keep_s = {round(c0, 3), round(c1, 3), round(so[0], 3), round(so[1], 3)} | {round(p["s"], 3) for p in deck["piers"]}
    stride = (1, 2, 4)[lod]
    sts = [s_ for i, s_ in enumerate(sts_all) if i % stride == 0 or round(s_.s, 3) in keep_s or i == len(sts_all) - 1]
    ush = LAY["u_shift"]
    low_sgn = 1.0 if sts[len(sts) // 2].slope < 0 else -1.0
    for a, b in zip(sts[:-1], sts[1:]):
        if b.s - a.s < 1e-3:
            continue
        for sgn in (1.0, -1.0):
            u_off = (ush["left"] if sgn > 0 else ush["right"]) + di * ush["deck"]
            ua, ub = a.s + u_off, b.s + u_off
            a_, b_ = St.__new__(St), St.__new__(St)
            a_.__dict__.update(a.__dict__)
            b_.__dict__.update(b.__dict__)
            a_.open = b_.open = a.open and b.open
            pa, pb = profile(a_, sgn, lod), profile(b_, sgn, lod)
            ctr = (a.at(0.0, 0.3) + b.at(0.0, 0.3)) / 2
            for k, ((p0, p1, band, ca, cb), (q0, q1, *_)) in enumerate(zip(pa, pb)):
                uv = [(ua, band_v(band, ca)), (ub, band_v(band, ca)), (ub, band_v(band, cb)), (ua, band_v(band, cb))]
                hint = (p0 + p1 + q0 + q1) / 4 - ctr         # outward from the box centre line
                if k == 0 and lod == 0:
                    hint = (0, 0, 1)
                mb.quad([p0, q0, q1, p1], uv, CONC, hint)
            # ---- railing on the cap edge (ADR 0110: rail_h_m 0 = none, the world generator builds the barrier-railing)
            if PRM["rail_h_m"] < 0.05:
                continue
            xr = sgn * (a.hb - PRM["rail_inset_m"])
            H = PRM["rail_h_m"]
            bay = (PRM["rail_post_m"], PRM["rail_post_m"], 8.0)[lod]
            nb = max(1, int(round((b.s - a.s) / bay)))
            A0, B0 = a.at(xr, 0.0), b.at(xr, 0.0)
            for j in range(nb):
                P0 = A0 + (B0 - A0) * (j / nb)
                P1 = A0 + (B0 - A0) * ((j + 1) / nb)
                up = np.array([0, 0, H - 0.07])
                mb.quad([P0, P1, P1 + up, P0 + up], [(0.004, 0.0), (0.746, 0.0), (0.746, 1.0), (0.004, 1.0)], STEEL)
                if lod == 0:           # post: flat bar seen from both travel directions
                    w = a.n * 0.035
                    mb.quad([P0 - w, P0 + w, P0 + w + (0, 0, H), P0 - w + (0, 0, H)], STEEL_UV, STEEL)
            hz = np.array([0, 0, H])
            hw_ = a.n * 0.03
            if lod == 0:
                for o0, o1 in ((-hw_, hw_ * 0 + (0, 0, 0.05)), (hw_ * 0 + (0, 0, 0.05), hw_)):
                    mb.quad([A0 + hz - (0, 0, 0.05) + o0, B0 + hz - (0, 0, 0.05) + o0, B0 + hz - (0, 0, 0.05) + o1,
                             A0 + hz - (0, 0, 0.05) + o1], STEEL_UV, STEEL)
            elif lod == 1:
                mb.quad([A0 + hz - hw_, B0 + hz - hw_, B0 + hz + hw_, A0 + hz + hw_], STEEL_UV, STEEL)
        # ---- drainage collector under the low cantilever (open spans)
        if a.open and b.open and lod < 2:
            xp = low_sgn * PRM["pipe_offset_m"]
            r = PRM["pipe_d_m"] / 2
            drop = np.array([0, 0, -(r + 0.12)])
            A, B = soffit_z(a, xp) + drop, soffit_z(b, xp) + drop
            mb.tube(A, B, r, 6 if lod == 0 else 3, CONC, uv=PIPE_UV)
            # thin red conduit under the cantilever root of the other side (reference frame: red line along the girder)
            xr_ = -low_sgn * (PRM["cant_root_m"] + 0.25)
            dr_ = np.array([0, 0, -0.10])
            mb.tube(soffit_z(a, xr_) + dr_, soffit_z(b, xr_) + dr_, 0.055, 4 if lod == 0 else 3, CONC, uv=RED_UV)
            if lod == 0:               # hanger strap at the start of every interval
                h0 = soffit_z(a, xp)
                w = a.n * (r + 0.015)
                mb.quad([h0 - w, h0 + w, A + w - (0, 0, r), A - w - (0, 0, r)], STEEL_UV, STEEL)
    # ---- piers of this cell (assigned by station: a pier on a cut belongs to the cell that starts there)
    for pr in deck["piers"]:
        if not (c0 - 1e-6 <= pr["s"] < c1 - 1e-6):
            continue
        st = min(sts_all, key=lambda s_: abs(s_.s - pr["s"]))
        build_pier(mb, st, pr, lod, low_sgn, colmb)
    # ---- abutment faces + expansion joints at the ends of the open range
    for k, s_ab in enumerate(so):
        if not (c0 - 1e-6 <= s_ab <= c1 + 1e-6) or s_ab > 1e8 or s_ab < -1e8:
            continue
        if (k == 0 and abs(s_ab - c1) < 1e-6 and c1 < deck["cuts"][-1] - 1e-6) or (k == 1 and abs(s_ab - c0) < 1e-6 and c0 > deck["cuts"][0] + 1e-6):
            continue                   # an abutment on a cut is built once, by the cell on its open side
        st = min(sts_all, key=lambda s_: abs(s_.s - s_ab))
        build_abutment(mb, st, 1.0 if k == 0 else -1.0, lod, colmb)


def build_pier(mb, st, pr, lod, low_sgn, colmb):
    P = LAY["pier"]
    t2, n2 = st.t[:2], st.n[:2]
    hl, hw, chm = PRM["col_len_m"] / 2, PRM["col_wid_m"] / 2, PRM["col_chamfer_m"]
    gap = PRM["bearing_gap_m"] if lod < 2 else 0.0
    ztop = pr["top"] - gap
    for q in pr["cols"]:
        c = np.array(q[:2])
        z0 = q[2] - 0.5
        # outline, starting at the front face (normal +t), counter-clockwise seen from above
        if lod < 2:
            loc = [(hl, -hw + chm), (hl, hw - chm), (hl - chm, hw), (-hl + chm, hw), (-hl, hw - chm), (-hl, -hw + chm),
                   (-hl + chm, -hw), (hl - chm, -hw)]
        else:
            loc = [(hl, -hw), (hl, hw), (hl, hw), (-hl, hw), (-hl, hw), (-hl, -hw), (-hl, -hw), (hl, -hw)]
        ring = [c + t2 * a + n2 * b for a, b in loc]
        per = [0.0]
        flat = [PRM["col_wid_m"] - 2 * chm, chm * math.sqrt(2), PRM["col_len_m"] - 2 * chm, chm * math.sqrt(2)] * 2
        for f in flat:
            per.append(per[-1] + f)
        for i in range(8):
            p, r_ = ring[i], ring[(i + 1) % 8]
            if np.linalg.norm(p - r_) < 1e-6:
                continue
            out = np.append((p + r_) / 2 - c, 0.0)
            v0, v1 = P["v0"] + per[i], P["v0"] + per[i + 1]
            mb.quad([(*p, z0), (*r_, z0), (*r_, ztop), (*p, ztop)],
                    [(ztop - z0, v0), (ztop - z0, v1), (0.0, v1), (0.0, v0)], CONC, out)
        colmb.box(c, t2, n2, hl, hw, z0, pr["top"], CONC, ((0, 0), (1, 1)), top=True, bottom=True)
        sp, sd = LAY["swatch_plain"], LAY["swatch_dark"]
        if lod == 0:
            mb.box(c, t2, n2, 0.28, 0.36, ztop, ztop + gap * 0.45, CONC, ((sp["u"][0], sp["v"][0]), (sp["u"][0] + 0.6, sp["v"][0] + gap * 0.45)), top=True)
            mb.box(c, t2, n2, 0.20, 0.28, ztop + gap * 0.45, pr["top"], CONC, ((sd["u"][0], sd["v"][0]), (sd["u"][1], sd["v"][1])), top=False)
        elif lod == 1:
            mb.box(c, t2, n2, 0.24, 0.32, ztop, pr["top"], CONC, ((sd["u"][0], sd["v"][0]), (sd["u"][1], sd["v"][1])), top=False)
    # downpipe: from the collector to the outer column, then down its side face
    if lod < 2:
        xp = low_sgn * PRM["pipe_offset_m"]
        r = PRM["pipe_d_m"] / 2 * 0.8
        A = soffit_z(st, xp) + np.array([0, 0, -(PRM["pipe_d_m"] / 2 + 0.12)])
        qc = max(pr["cols"], key=lambda q_: float(np.dot(np.array(q_[:2]) - st.mid[:2], n2)) * low_sgn)
        xc = float(np.dot(np.array(qc[:2]) - st.mid[:2], n2))
        B = st.at(xc + low_sgn * (hw + r + 0.03), -PRM["girder_depth_m"] - 0.30)
        B[:2] = np.array(qc[:2]) + n2 * low_sgn * (hw + r + 0.03) + t2 * 0.0
        C = np.array([B[0], B[1], qc[2] + 0.15])
        sides = 6 if lod == 0 else 3
        mb.tube(A, B, r, sides, CONC, up=st.t, uv=PIPE_UV)
        mb.tube(B, C, r, sides, CONC, up=st.t, uv=PIPE_UV)


def build_abutment(mb, st, inward, lod, colmb):
    """Front wall under the end of the open range; inward = +1 when the open span lies towards +t."""
    W = LAY["wall"]
    zt = st.mid[2] - 0.60
    z0 = min(st.zc, st.zl, st.zr) - 0.5
    hb = st.hb - 0.05
    nstrip = 1 if lod == 2 else max(1, int(round(2 * hb / W["period"])))
    face = st.mid.copy()
    for j in range(nstrip):
        x0 = -hb + 2 * hb * j / nstrip
        x1 = -hb + 2 * hb * (j + 1) / nstrip
        p, q = face + st.n * x0, face + st.n * x1
        za, zb = zt + st.slope * x0, zt + st.slope * x1
        mb.quad([(p[0], p[1], z0), (q[0], q[1], z0), (q[0], q[1], zb), (p[0], p[1], za)],
                [(za - z0, W["v0"]), (zb - z0, W["v0"] + W["period"] - 0.05), (0.0, W["v0"] + W["period"] - 0.05), (0.0, W["v0"])],
                CONC, st.t * inward)
    ctr = st.mid[:2] - st.t[:2] * inward * PRM["abutment_t_m"] / 2
    colmb.box(ctr, st.t[:2], st.n[:2], PRM["abutment_t_m"] / 2, hb, z0, zt, CONC, ((0, 0), (1, 1)), top=True, bottom=True)
    if lod < 2:                        # expansion joint across the carriageway: steel-edged rubber strip
        sd = LAY["swatch_dark"]
        up = np.array([0, 0, 0.012])
        a, b = st.Lg + up, st.Rg + up
        w = st.t * 0.16
        mb.quad([a - w, b - w, b + w, a + w], [(sd["u"][0], sd["v"][0]), (sd["u"][1], sd["v"][0]), (sd["u"][1], sd["v"][1]), (sd["u"][0], sd["v"][1])], CONC, (0, 0, 1))


def build_camera(mb, deck):
    """CCTV housing under the bottom flange near the middle of the open range (reference: frame 1050297706629492)."""
    so = deck["s_open"]
    sts = [St(d) for d in deck["stations"]]
    st = min(sts, key=lambda s_: abs(s_.s - (0.5 * (so[0] + so[1]) + 7.0)))
    sd = LAY["swatch_dark"]
    c = st.at(0.6, -PRM["girder_depth_m"])
    mb.box(c[:2], st.t[:2], st.n[:2], 0.02, 0.02, c[2] - 0.28, c[2], STEEL, (STEEL_UV[0], STEEL_UV[2]), top=False)
    mb.box(c[:2], st.t[:2], st.n[:2], 0.16, 0.09, c[2] - 0.42, c[2] - 0.28, CONC, ((sd["u"][0], sd["v"][0]), (sd["u"][1], sd["v"][1])), top=True, bottom=True)
    return st.s


def main():
    for ob in list(bpy.data.objects):
        bpy.data.objects.remove(ob)
    decks = SPEC["decks"]
    lead = decks[0]
    lsts = [St(d) for d in lead["stations"]]

    def lead_mid(s):
        return min(lsts, key=lambda s_: abs(s_.s - s)).mid

    cells = list(zip(lead["cuts"][:-1], lead["cuts"][1:]))
    centres = [(lead_mid(a)[:2] + lead_mid(b)[:2]) / 2 for a, b in cells]
    segs = []
    cam_s = None
    colmb = MB()
    for k, (c0, c1) in enumerate(cells):
        anchor = (lead_mid(c0) + lead_mid(c1)) / 2
        anchor = [round(float(x), 3) for x in anchor]
        name = f"landmark_{ASSET}_{k:02d}"
        tris = []
        for lod in range(3):
            mb = MB()
            for di, dk in enumerate(decks):
                dsts = [St(d) for d in dk["stations"]]
                for a, b in zip(dk["cuts"][:-1], dk["cuts"][1:]):
                    sa = min(dsts, key=lambda s_: abs(s_.s - a)).mid[:2]
                    sb = min(dsts, key=lambda s_: abs(s_.s - b)).mid[:2]
                    kk = int(np.argmin([np.linalg.norm((sa + sb) / 2 - c) for c in centres]))
                    if kk == k:
                        build_cell(mb, dk, di, a, b, lod, colmb if lod == 0 else MB())
                        so = dk["s_open"]
                        if lod == 0 and di == 0 and so and a <= 0.5 * (so[0] + so[1]) + 7.0 < b:
                            cam_s = build_camera(mb, dk)
            _, n = mb.to_object(name + ("" if lod == 0 else f".lod{lod}"), anchor)
            tris.append(n)
        segs.append({"name": name, "anchor": anchor, "tris": tris, "s_lead": [c0, c1]})
    colmb.to_object(f"{ASSET}.collision", [0.0, 0.0, 0.0])
    bpy.data.objects[f"{ASSET}.collision"].hide_render = True
    OUT.mkdir(parents=True, exist_ok=True)
    glb = OUT / f"{ASSET}.glb"
    if "--render" in argv:
        render(Path(arg("--render")), segs)
        return
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", export_yup=True, export_apply=False,
                              export_texcoords=True, export_normals=True, export_materials="EXPORT",
                              export_image_format="NONE", export_tangents=False, export_animations=False,
                              export_cameras=False, export_lights=False, export_extras=False)
    if "--blend" in argv:
        bpy.ops.wm.save_as_mainfile(filepath=str(OUT / f"{ASSET}.blend"))
    meta = {
        "schema": "truck-sim-pl/hero-bridge-asset/1", "asset": ASSET, "spec": SPEC_PATH.relative_to(REPO).as_posix(),
        "spec_sha256": sha(SPEC), "glb_sha256": hashlib.sha256(glb.read_bytes()).hexdigest(),
        "blender": bpy.app.version_string, "materials": [CONC, STEEL], "segments": segs,
        "tris_total": [int(sum(s_["tris"][k] for s_ in segs)) for k in range(3)],
        "camera_station_m": cam_s,
        "axes": "glTF (x, y, z) = (-dE, dU, dN) relative to the segment anchor (local E, N, U)",
    }
    (OUT / f"{ASSET}_meta.json").write_text(json.dumps(meta, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
    print("VIADUCT_RESULT: OK", glb, meta["tris_total"], len(segs), "segments")


def render(out, segs):
    """Control renders of LOD0 (and a LOD1 / LOD2 strip) in world placement: EEVEE, sun + sky, gravel-grey ground."""
    out.mkdir(parents=True, exist_ok=True)
    sc = bpy.context.scene
    for sg in segs:
        for suf in ("", ".lod1", ".lod2"):
            ob = bpy.data.objects[sg["name"] + suf]
            a = sg["anchor"]
            ob.location = (-a[0], -a[1], a[2])
    ctr = np.array(SPEC["centre"])
    bpy.ops.mesh.primitive_plane_add(size=900, location=(-ctr[0], -ctr[1], ctr[2] - 5.9))
    g = bpy.context.object
    gm = bpy.data.materials.new("ground")
    gm.use_nodes = True
    gm.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.30, 0.29, 0.27, 1)
    gm.node_tree.nodes["Principled BSDF"].inputs["Roughness"].default_value = 0.95
    g.data.materials.append(gm)
    w = bpy.data.worlds.new("w")
    sc.world = w
    w.use_nodes = True
    sky = w.node_tree.nodes.new("ShaderNodeTexSky")
    sky.sky_type = "NISHITA"
    sky.sun_elevation = math.radians(38)
    sky.sun_rotation = math.radians(200)
    w.node_tree.links.new(sky.outputs["Color"], w.node_tree.nodes["Background"].inputs["Color"])
    w.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.25
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(200 + 180)))
    bpy.context.object.data.energy = 3.0
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.view_settings.view_transform = "AgX"
    sc.render.resolution_x, sc.render.resolution_y = 1600, 900
    sc.eevee.use_shadows = True
    try:
        sc.eevee.use_raytracing = True
        sc.eevee.use_gtao = True
    except Exception:      # noqa: BLE001
        pass
    cams = {
        "stretch_04": ((557.025, -691.802, 142.114), (503.599, -667.112, 141.161), 60.0),
        "photo_ground": ((576.9, -676.204, 141.313), (542.607, -738.329, 148.815), 62.0),
        "ring_under": ((566.0, -700.0, 141.6), (520.0, -712.0, 146.0), 75.0),
        "under_soffit": ((548.0, -712.0, 141.5), (500.0, -690.0, 146.5), 70.0),
        "deck": ((600.0, -752.0, 147.6), (520.0, -706.0, 146.3), 60.0),
    }
    lods = {"": "lod0", ".lod1": "lod1", ".lod2": "lod2"}
    for suf, tag in lods.items():
        for sg in segs:
            for s2 in lods:
                bpy.data.objects[sg["name"] + s2].hide_render = s2 != suf
        for cid, (pos, look, fov) in cams.items():
            if tag != "lod0" and cid not in ("stretch_04", "ring_under"):
                continue
            cd = bpy.data.cameras.new(cid)
            cd.sensor_fit = "HORIZONTAL"
            cd.angle = 2 * math.atan(math.tan(math.radians(fov) / 2) * 16 / 9)
            cd.clip_end = 3000
            co = bpy.data.objects.new(cid, cd)
            sc.collection.objects.link(co)
            p = np.array([-pos[0], -pos[1], pos[2]])
            l = np.array([-look[0], -look[1], look[2]])
            co.location = p
            d = l - p
            co.rotation_euler = (math.atan2(math.hypot(d[0], d[1]), -d[2]), 0, math.atan2(d[1], d[0]) - math.pi / 2)
            sc.camera = co
            sc.render.filepath = str(out / f"{cid}__{tag}.png")
            bpy.ops.render.render(write_still=True)
    print("VIADUCT_RENDER: OK", out)


main()
