"""Procedural tree library for Podlasie roadsides (our geometry/leaves, CC0 pine bark).

    blender -b --factory-startup -P tools/blender/world/make_trees.py

Species: Scots pine (Pinus sylvestris: tall bare trunk, grey-brown lower / orange upper bark, flat irregular
crown of whorled branches), silver birch (Betula pendula: white bark with black lenticels, drooping twigs),
black alder (Alnus glutinosa: monopodial trunk, conical crown), Norway maple (Acer platanoides: short trunk,
broad round crown), small-leaved linden (Tilia cordata: tall ovate dense crown), shrub (hazel/young birch
undergrowth). 3 variants each. Crowns are made of foliage cards (art-source/world/vegetation/leaves_*.png,
streetscape/leaf_textures.py) on a recursive branch skeleton; card normals point away from the crown centre
(soft crown shading). Per variant three LODs:
  <name>        LOD0  trunk + branches + cards  (High, < 150 m)
  <name>.lod1   LOD1  trunk/main limbs + capped stable subset of LOD0 cards at 1.4x size
  <name>.lod2   LOD2  one camera-facing quad with six baked orthographic views
Models are built at the reference height HREF[species]; instances scale by h / HREF.
Output: art-source/world/vegetation/trees.glb, trees_meta.json, impostor_<name>.png
"""

import json
import math
import random
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools/worldgen"))
from streetscape.foliage_policy import crown_opening, leaf_lod_indices
VEG = REPO / "art-source" / "world" / "vegetation"
ARGV = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
if "--out" in ARGV:
    VEG = Path(ARGV[ARGV.index("--out") + 1]).resolve()
VEG.mkdir(parents=True, exist_ok=True)
HREF = {"pine": 19.0, "birch": 14.0, "alder": 13.0, "maple": 12.0, "linden": 13.5, "shrub": 2.8}
BARK = {"pine": ["bark_pine_lower", "bark_pine"], "birch": ["bark_birch"], "alder": ["bark_alder"],
        "maple": ["bark_maple"], "linden": ["bark_linden"], "shrub": ["bark_shrub"]}


class Geo:
    def __init__(self):
        self.parts = {}     # mat -> (verts, faces, uvs, normals or None)
        self.crown_height = 0
        self.crown_phase = 0

    def _p(self, mat):
        return self.parts.setdefault(mat, ([], [], [], []))

    def tube(self, mat, pts, radii, seg=6, v0=0.0):
        V, F, UV, N = self._p(mat)
        base = len(V)
        L = 0.0
        frames = []
        for i, p in enumerate(pts):
            t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
            ref = Vector((0, 0, 1)) if abs(t.z) < 0.95 else Vector((1, 0, 0))
            u = t.cross(ref).normalized()
            w = t.cross(u)
            if i:
                L += (pts[i] - pts[i - 1]).length
            for k in range(seg + 1):
                a = 2 * math.pi * k / seg
                dvec = u * math.cos(a) + w * math.sin(a)
                V.append(p + dvec * radii[i])
                UV.append((k / seg, (v0 + L) / 2.0))
                N.append(dvec)
        n = seg + 1
        for i in range(len(pts) - 1):
            for k in range(seg):
                a = base + i * n + k
                F.append((a, a + 1, a + n + 1, a + n))

    def card(self, mat, c, normal, up, size, crown_c):
        if self.crown_height and crown_opening(c, crown_c, self.crown_height, self.crown_phase):
            return
        V, F, UV, N = self._p(mat)
        nrm = normal.normalized()
        r = up.cross(nrm)
        if r.length < 1e-3:
            r = Vector((1, 0, 0))
        r.normalize()
        u = nrm.cross(r).normalized()
        h = size / 2
        base = len(V)
        sn = (c - crown_c)
        sn = (sn.normalized() if sn.length > 1e-3 else Vector((0, 0, 1)))
        sn = (sn + Vector((0, 0, 0.35))).normalized()
        for du, dv, uv in ((-1, -1, (0, 0)), (1, -1, (1, 0)), (1, 1, (1, 1)), (-1, 1, (0, 1))):
            V.append(c + r * du * h + u * dv * h)
            UV.append(uv)
            N.append(sn)
        F.append((base, base + 1, base + 2, base + 3))


def bend_path(p0, d, L, n, rng, wobble, gravity=0.0):
    pts = [p0.copy()]
    dd = d.normalized()
    step = L / n
    for i in range(n):
        dd = (dd + Vector((rng.uniform(-wobble, wobble), rng.uniform(-wobble, wobble), rng.uniform(-wobble, wobble) * 0.5
                           - gravity))).normalized()
        pts.append(pts[-1] + dd * step)
    return pts


def grow(species, variant, lod):
    rng = random.Random(hash((species, variant)) & 0xFFFF if False else (sum(map(ord, species)) * 31 + variant))
    H = HREF[species] * rng.uniform(0.92, 1.08)
    g = Geo()
    g.crown_height = H
    g.crown_phase = variant * 1.73 + sum(map(ord, species)) * .013
    leaf = f"leaves_{species}"
    cards_keep = 1.0 if lod == 0 else (0.6 if species == "birch" else 0.33)
    csize_k = 1.0 if lod == 0 else (1.5 if species == "birch" else 1.6)
    seg = 8 if lod == 0 else 5
    crng = random.Random(variant * 7 + 3)

    def cards_along(pts, size, n, crown_c, droop=0.0, flat=0.0, start=0.3):
        for i in range(n):
            if crng.random() > cards_keep:
                continue
            t = start + (1 - start) * crng.random()
            k = t * (len(pts) - 1)
            a, b = int(k), min(int(k) + 1, len(pts) - 1)
            p = pts[a].lerp(pts[b], k - a) + Vector((crng.uniform(-0.3, 0.3), crng.uniform(-0.3, 0.3),
                                                      crng.uniform(-0.3, 0.3) - droop))
            nrm = Vector((crng.uniform(-1, 1), crng.uniform(-1, 1), crng.uniform(-1, 1) + flat * 3))
            g.card(leaf, p, nrm, Vector((0, 0, 1)), size * csize_k * crng.uniform(0.8, 1.2), crown_c)

    if species == "pine":
        # mature Scots pine: long clean bole, crown in the top ~35 % that is flattened, asymmetric (a light side)
        # and made of sparse foliage clumps at the ends of a few long, irregular, upturned limbs; whorls have
        # missing branches; no regular tiers, no tuft on a pole
        lean = Vector((rng.uniform(-0.05, 0.05), rng.uniform(-0.05, 0.05), 1))
        trunk = bend_path(Vector((0, 0, -0.3)), lean, H * 0.94, 14, rng, 0.035)
        rad = [0.24 * (1 - i / 14) ** 0.8 + 0.025 for i in range(15)]
        g.tube("bark_pine_lower", trunk[:7], rad[:7], seg)
        g.tube("bark_pine", trunk[6:], rad[6:], seg, v0=H * 0.43)
        cc = trunk[13]
        light = rng.uniform(0, 2 * math.pi)            # side of the stand edge / gap: longer limbs there
        # Mature Scots pine has long lateral scaffold limbs, with visible gaps
        # between their needle fans; a tiny dense tuft on a long pole reads as a
        # lollipop. Different variants keep distinct live-crown depth.
        z0 = H * (0.48 + 0.04 * variant + rng.uniform(-0.025, 0.025))
        z = z0
        nlimb = 0
        while z < H * 0.93:
            f = (z - z0) / (H * 0.93 - z0)
            for _ in range(rng.randint(3, 5)):
                if rng.random() < 0.28:                 # missing / broken branch in the whorl
                    continue
                a = rng.uniform(0, 2 * math.pi)
                bias = 0.65 + 0.55 * max(0.0, math.cos(a - light))
                L = H * (0.13 + 0.10 * math.sin(math.pi * min(1.0, 0.12 + f * 0.85))) * bias * rng.uniform(0.75, 1.12)
                up = rng.uniform(0.12, 0.35) + f * 0.22
                d = Vector((math.cos(a), math.sin(a), up))
                k = z / H * 14
                p0 = trunk[min(int(k), 13)].lerp(trunk[min(int(k) + 1, 14)], k - int(k))
                br = bend_path(p0, d, L, 5, rng, 0.22, gravity=-0.04)
                if lod == 0 or L > 1.8:
                    g.tube("bark_twig", br, [0.07 * (1 - f * 0.4) * (1 - i / 6) + 0.012 for i in range(6)],
                           max(3, seg // 2))
                # foliage clumps: 1-3 dense clusters near the limb end (sparse inside the crown)
                for cl in range(rng.randint(2, 4)):
                    t = rng.uniform(0.38, 1.0)
                    kk = t * (len(br) - 1)
                    ia = int(kk)
                    q = br[ia].lerp(br[min(ia + 1, len(br) - 1)], kk - ia)
                    rcl = rng.uniform(0.45, 0.85) * (0.7 + 0.4 * bias)
                    for _ in range(int((5 + 3 * rcl) * (1.0 if lod == 0 else 0.45)) + 1):
                        pc = q + Vector((crng.uniform(-rcl, rcl), crng.uniform(-rcl, rcl), crng.uniform(-0.55, 0.45) * rcl))
                        nrm = Vector((crng.uniform(-1, 1), crng.uniform(-1, 1), crng.uniform(-0.2, 1.4)))
                        g.card(leaf, pc, nrm, Vector((0, 0, 1)), 0.95 * csize_k * crng.uniform(0.8, 1.2), cc)
                nlimb += 1
            z += rng.uniform(0.9, 1.45)
        # leader: the stem ends inside the top clumps (no tuft on a bare pole)
        for _ in range(int(10 * (1.0 if lod == 0 else 0.5))):
            pc = trunk[-1] + Vector((crng.uniform(-1.1, 1.1), crng.uniform(-1.1, 1.1), crng.uniform(-1.2, 0.2)))
            g.card(leaf, pc, Vector((crng.uniform(-1, 1), crng.uniform(-1, 1), 1.2)), Vector((0, 0, 1)), 0.9 * csize_k, cc)
        # dead lower branch stubs
        if lod == 0:
            for _ in range(12):
                zz = rng.uniform(H * 0.25, z0)
                k = zz / H * 14
                p0 = trunk[min(int(k), 14)]
                a = rng.uniform(0, 2 * math.pi)
                g.tube("bark_pine_lower", [p0, p0 + Vector((math.cos(a), math.sin(a), -0.1)) * rng.uniform(0.2, 0.8)],
                       [0.025, 0.008], 3)
        return g, H
    # broadleaf + shrub
    if species == "shrub":
        stems = rng.randint(5, 8)
        cc = Vector((0, 0, H * 0.55))
        for _ in range(stems):
            a = rng.uniform(0, 2 * math.pi)
            d = Vector((math.cos(a) * 0.4, math.sin(a) * 0.4, 1))
            st = bend_path(Vector((0, 0, -0.1)), d, H * rng.uniform(0.8, 1.1), 5, rng, 0.2)
            g.tube("bark_shrub", st, [0.03 * (1 - i / 6) + 0.006 for i in range(6)], 4)
            cards_along(st, 0.9, 10, cc, start=0.25)
        return g, H
    trunk_frac = {"birch": 0.30, "alder": 0.28, "maple": 0.28, "linden": 0.30}[species]
    r0 = {"birch": 0.17, "alder": 0.18, "maple": 0.22, "linden": 0.25}[species]
    top = {"birch": 0.94, "alder": 0.95, "maple": 0.84, "linden": 0.92}[species]
    lean = Vector((rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), 1))
    trunk = bend_path(Vector((0, 0, -0.3)), lean, H * top, 10, rng, 0.04)
    g.tube(BARK[species][0], trunk, [r0 * (1 - i / 10) ** 0.9 + 0.02 for i in range(11)], seg)
    cc = trunk[0] + Vector((0, 0, H * (trunk_frac + 1) / 2))
    nmain = {"birch": 9, "alder": 14, "maple": 8, "linden": 10}[species]
    for b in range(nmain):
        f = trunk_frac + (top - trunk_frac) * (b + rng.uniform(0, 1)) / nmain
        k = f / top * 10
        ia = min(int(k), 9)
        p0 = trunk[ia].lerp(trunk[ia + 1], k - ia)
        a = rng.uniform(0, 2 * math.pi)
        up = {"birch": 0.45, "alder": 0.25, "maple": 0.6, "linden": 0.5}[species]
        rel = (f - trunk_frac) / max(top - trunk_frac, 1e-3)
        profile = max(.25, math.sin(math.pi * (0.10 + rel * .83)) ** .65)
        L = H * {"birch": .27 * profile, "alder": .3 * (1-rel) + .06,
                 "maple": .34 * profile, "linden": .30 * profile}[species]
        L *= rng.uniform(0.75, 1.15)
        d = Vector((math.cos(a), math.sin(a), up))
        br = bend_path(p0, d, L, 5, rng, 0.18)
        g.tube(BARK[species][0] if species != "birch" else "bark_twig", br,
               [r0 * 0.4 * (1 - i / 6) + 0.012 for i in range(6)], max(3, seg // 2))
        nsub = (7 if species == "birch" else 5) if lod == 0 else (5 if species == "birch" else 3)
        for s in range(nsub):
            t = 0.35 + 0.6 * rng.random()
            bi = min(int(t * 5), 4)
            q0 = br[bi].lerp(br[bi + 1], t * 5 - bi)
            a2 = a + rng.uniform(-1.2, 1.2)
            droop = 0.6 if species == "birch" else 0.15
            d2 = Vector((math.cos(a2), math.sin(a2), rng.uniform(-0.2, 0.6)))
            sub = bend_path(q0, d2, L * 0.45, 4, rng, 0.2, gravity=droop * 0.25)
            if lod == 0:
                g.tube("bark_twig", sub, [0.03 * (1 - i / 5) + 0.006 for i in range(5)], 3)
            csz = {"birch": 0.85, "alder": 1.0, "maple": 1.05, "linden": 1.0}[species]
            dens = {"birch": 14, "alder": 12, "maple": 14, "linden": 15}[species]
            cards_along(sub, csz, dens, cc, droop=0.4 if species == "birch" else 0.0, start=0.1)
        cards_along(br, {"birch": .9, "alder": 1.0, "maple": 1.05, "linden": 1.0}[species], 6, cc, start=0.20)
    if species == "birch":
        # v3.1 (REVIEW r2 #7, "birches without crowns"): the white stem ran bare through the open, drooping crown
        # and read as a pole at 60-250 m. Foliage clumps hug the stem over the whole crown height.
        n_st = 24 if lod == 0 else 14
        for i in range(n_st):
            f = trunk_frac + 0.06 + (top - trunk_frac - 0.02) * (i + crng.random()) / n_st
            k = min(f / top * 10, 9.999)
            q = trunk[int(k)].lerp(trunk[int(k) + 1], k - int(k))
            for _ in range(3):
                pc = q + Vector((crng.uniform(-0.9, 0.9), crng.uniform(-0.9, 0.9), crng.uniform(-0.7, 0.3)))
                nrm = Vector((crng.uniform(-1, 1), crng.uniform(-1, 1), crng.uniform(-0.6, 1.0)))
                g.card(leaf, pc, nrm, Vector((0, 0, 1)), 1.0 * csize_k * crng.uniform(0.8, 1.2), cc)
    return g, H


def reuse_leaf_lod(g0, g1, seed):
    """Keep LOD1 leaf centres on the LOD0 branch groups, without new submeshes."""
    for name, (vertices, faces, uv, normals) in g0.parts.items():
        if not name.startswith("leaves_"):
            continue
        out_v, out_f, out_uv, out_n = [], [], [], []
        old_faces = len(g1.parts.get(name, ([], [], [], []))[1])
        for index in leaf_lod_indices(len(faces), seed, maximum=old_faces):
            face = faces[index]
            centre = sum((vertices[i] for i in face), Vector()) / len(face)
            base = len(out_v)
            out_v += [centre + (vertices[i] - centre) * 1.40 for i in face]
            out_uv += [uv[i] for i in face]
            out_n += [normals[i] for i in face]
            out_f.append(tuple(range(base, base + len(face))))
        g1.parts[name] = (out_v, out_f, out_uv, out_n)
    return g1


def to_object(name, g):
    me = bpy.data.meshes.new(name)
    verts, faces, uvs, nrms, mats = [], [], [], [], []
    mat_names = sorted(g.parts)
    for mi, m in enumerate(mat_names):
        V, F, UV, N = g.parts[m]
        off = len(verts)
        verts += [tuple(v) for v in V]
        faces += [tuple(i + off for i in f) for f in F]
        uvs += UV
        nrms += [tuple(n) for n in N]
        mats += [mi] * len(F)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    me.polygons.foreach_set("material_index", mats)
    me.polygons.foreach_set("use_smooth", [True] * len(me.polygons))
    try:
        me.normals_split_custom_set_from_vertices(nrms)
    except Exception:
        pass
    for m in mat_names:
        me.materials.append(material(m))
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


_mats = {}


def material(name):
    if name in _mats:
        return _mats[name]
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    file = name
    if name == "bark_pine_lower" and not (VEG / f"{file}.png").exists():
        file = "bark_alder"  # public fallback for old caches
    tex.image = bpy.data.images.load(str(VEG / f"{file}.png"))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.9
    if name.startswith("leaves"):
        nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
        m.blend_method = "CLIP" if hasattr(m, "blend_method") else None
        try:
            m.alpha_threshold = 0.5
        except AttributeError:
            pass
        m.use_backface_culling = False
        try:
            bsdf.inputs["Subsurface Weight"].default_value = 0.0
        except KeyError:
            pass
    _mats[name] = m
    return m


# ------------------------------------------------------------------------------------------- bakes (v3.4)
# Impostors and forest HLOD textures are baked as three passes (Cycles, orthographic), so the engine lights them
# with the same sun + sky SH as the near trees instead of a lighting baked into the colour (review r3 W1/W2:
# black spots and a beige "camouflage" at low sun; ADR 0023):
#   alb  emission of the materials' base colour (Standard view = the sRGB albedo of the leaf / bark textures, so
#        the far colour equals the near colour under the same light and tone curve, ADR 0016), alpha = coverage
#   nrm  camera-space shading normal (crown-spherical normals of the cards, bark tubes) * 0.5 + 0.5, Raw view
#   occ  white diffuse under a uniform white sky, direct only (Raw): sky visibility of each texel - dark inside the
#        crown and inside the stand, 1 on the sunny outer leaves
# tools/blender/world/pack_vegetation.py (uv, numpy + scipy) then dilates the colour under the alpha, removes isolated
# specks from the silhouette and packs <name>.png (RGB albedo + A coverage) and <name>_n.png (RG normal, B occlusion).
IMP_NF = 6                       # impostor views around the tree (60 degrees apart), blended in the shader
IMP_RES = (256, 384)             # one view
RAW = REPO / "artifacts" / "vegetation-r2" / "raw-bakes"  # raw passes, never tracked
_passmats = {}


def _engine(sc):
    sc.render.engine = "CYCLES"
    sc.cycles.device = "CPU"
    try:                                  # GPU when present (same images, only faster)
        prefs = bpy.context.preferences.addons["cycles"].preferences
        for kind in ("OPTIX", "CUDA", "HIP"):
            try:
                prefs.compute_device_type = kind
            except TypeError:
                continue
            prefs.get_devices()
            if any(d.type == kind for d in prefs.devices):
                for d in prefs.devices:
                    d.use = d.type == kind
                sc.cycles.device = "GPU"
                break
    except Exception:
        pass
    sc.cycles.use_denoising = False
    sc.cycles.seed = 7
    sc.cycles.max_bounces = 0            # occ: direct sky visibility only
    sc.cycles.diffuse_bounces = 0
    sc.cycles.transparent_max_bounces = 128
    sc.cycles.use_adaptive_sampling = False
    sc.cycles.pixel_filter_type = "BLACKMAN_HARRIS"
    sc.cycles.filter_width = 1.2


def bake_setup(transparent=True, res=IMP_RES, samples=24):
    sc = bpy.context.scene
    _engine(sc)
    sc.cycles.samples = samples
    sc.render.film_transparent = transparent
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGBA"
    sc.render.image_settings.color_depth = "16"
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0.0
    if sc.world is None:
        sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    bg = sc.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    cam = bpy.data.objects.get("imp_cam") or bpy.data.objects.new("imp_cam", bpy.data.cameras.new("imp_cam"))
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.clip_start, cam.data.clip_end = 0.1, 500.0
    sc.camera = cam
    return sc, cam


def _pass_material(m, kind):
    """Copy of material m that renders pass `kind` (alb / nrm / occ) with the same coverage (alpha)."""
    key = (m.name, kind)
    if key in _passmats:
        return _passmats[key]
    d = m.copy()
    d.name = f"{m.name}__{kind}"
    nt = d.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    col_src = alpha_src = None
    col_val = (0.5, 0.5, 0.5, 1.0)
    if bsdf is not None:
        lk = [l for l in nt.links if l.to_socket == bsdf.inputs["Base Color"]]
        col_src = lk[0].from_socket if lk else None
        col_val = tuple(bsdf.inputs["Base Color"].default_value)
        la = [l for l in nt.links if l.to_socket == bsdf.inputs["Alpha"]]
        alpha_src = la[0].from_socket if la else None
    for l in [l for l in nt.links if l.to_node == out]:
        nt.links.remove(l)
    if kind == "alb":
        sh = nt.nodes.new("ShaderNodeEmission")
        if col_src is not None:
            nt.links.new(col_src, sh.inputs["Color"])
        else:
            sh.inputs["Color"].default_value = col_val
    elif kind == "nrm":
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        vt = nt.nodes.new("ShaderNodeVectorTransform")
        vt.vector_type, vt.convert_from, vt.convert_to = "NORMAL", "WORLD", "CAMERA"
        ma = nt.nodes.new("ShaderNodeVectorMath")
        ma.operation = "MULTIPLY_ADD"
        ma.inputs[1].default_value = (0.5, 0.5, -0.5)      # Blender camera space looks down -Z: z toward camera
        ma.inputs[2].default_value = (0.5, 0.5, 0.5)
        nt.links.new(geo.outputs["Normal"], vt.inputs["Vector"])
        nt.links.new(vt.outputs["Vector"], ma.inputs[0])
        sh = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(ma.outputs["Vector"], sh.inputs["Color"])
    else:
        sh = nt.nodes.new("ShaderNodeBsdfDiffuse")
        sh.inputs["Color"].default_value = (1.0, 1.0, 1.0, 1.0)
    if alpha_src is not None:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        # hard coverage at the 0.5 cut-off the engine uses (soft alpha would leave grey veils in the occlusion pass)
        mt = nt.nodes.new("ShaderNodeMath")
        mt.operation = "GREATER_THAN"
        mt.inputs[1].default_value = 0.5
        nt.links.new(alpha_src, mt.inputs[0])
        nt.links.new(mt.outputs[0], mix.inputs["Fac"])
        nt.links.new(tr.outputs[0], mix.inputs[1])
        nt.links.new(sh.outputs[0], mix.inputs[2])
        sh = mix
    nt.links.new(sh.outputs[0], out.inputs["Surface"])
    _passmats[key] = d
    return d


def _set_pass(objs, kind):
    """Object-level material override (the mesh data stays shared with the exported trees)."""
    for o in objs:
        for slot in o.material_slots:
            key = f"mat_{slot.slot_index}"
            if key not in o:
                o[key] = o.data.materials[slot.slot_index].name
            slot.link = "OBJECT"
            slot.material = _pass_material(bpy.data.materials[o[key]], kind)


def _clear_pass(objs):
    for o in objs:
        for slot in o.material_slots:
            slot.material = None
            slot.link = "DATA"


def render_passes(objs, path_stem):
    """Renders alb / nrm / occ of the visible objects to RAW/<stem>_<pass>.png."""
    sc = bpy.context.scene
    RAW.mkdir(parents=True, exist_ok=True)
    for kind in ("alb", "nrm", "occ"):
        _set_pass(objs, kind)
        sc.view_settings.view_transform = "Standard" if kind == "alb" else "Raw"
        sc.render.filepath = str(RAW / f"{path_stem}_{kind}.png")
        bpy.ops.render.render(write_still=True)


def bake_impostor(ob, name, H):
    """IMP_NF orthographic views of LOD0 around the tree (frame k: camera at azimuth 2 pi k / IMP_NF from -Y,
    counter-clockwise seen from above), each covering the whole crown. Returns frame height S (model metres)."""
    sc, cam = bake_setup(True, IMP_RES, 24)
    for o in sc.objects:
        o.hide_render = o is not ob and o.type == "MESH"
    ob.hide_render = False
    half_w = max(math.hypot(v[0], v[1]) for v in ob.bound_box)
    S = max(H * 1.05, 2.0 * half_w * 1.04 * IMP_RES[1] / IMP_RES[0])
    cam.data.ortho_scale = S
    for k in range(IMP_NF):
        a = 2 * math.pi * k / IMP_NF
        cam.location = (60 * math.sin(a), -60 * math.cos(a), S / 2 - 0.3)
        cam.rotation_euler = (math.pi / 2, 0, a)
        render_passes([ob], f"impostor_{name}_{k}")
    _clear_pass([ob])
    ob.hide_render = True
    return S


def impostor_object(name, H, png, S):
    """One quad (the engine turns it to the camera and picks / blends the views, Kamion/Vegetation _IMPOSTOR)."""
    m = bpy.data.materials.new(f"impostor_{name}")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(png))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    w = S * (IMP_RES[0] / IMP_RES[1]) / 2       # quad matches one bake view (S = ortho scale, its height)
    verts, faces, uvs = [], [], []
    for k in range(1):
        base = len(verts)
        for x, z, uv in ((-w, 0, (0, 0)), (w, 0, (1, 0)), (w, S, (1, 1)), (-w, S, (0, 1))):
            verts.append((x, 0.0, z - 0.3))
            uvs.append(uv)
        faces.append((base, base + 1, base + 2, base + 3))
    me = bpy.data.meshes.new(name + ".lod2")
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            uvl.data[li].uv = uvs[me.loops[li].vertex_index]
    me.materials.append(m)
    ob = bpy.data.objects.new(name + ".lod2", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------------------------------- forest HLOD bakes
# Forest HLOD (v3.1, streetscape/forest_hlod.py): beyond the switch distance a forest cell is drawn as a canopy
# surface + alpha-tested "edge walls" instead of hundreds of tree instances. Both textures are baked here from
# the same LOD0 trees, so the silhouette (tall bare pine boles, flat clumped pine crowns, white birch stems with
# their own crowns) is the one of the near trees. Species mixes = vegetation.MIX for the BDOT10k forest
# categories (iglasty / mieszany / liściasty).
FOREST_MIX = {"conifer": {"pine": 0.82, "birch": 0.12, "alder": 0.02, "maple": 0.02, "linden": 0.02},
              "mixed": {"pine": 0.45, "birch": 0.25, "alder": 0.10, "maple": 0.10, "linden": 0.10},
              "broadleaf": {"pine": 0.08, "birch": 0.32, "alder": 0.25, "maple": 0.20, "linden": 0.15}}
TREE_H = {"pine": (14, 24), "birch": (9, 19), "alder": (9, 17), "maple": (8, 16), "linden": (9, 18), "shrub": (1.5, 4.0)}
EDGE_W, EDGE_H, EDGE_DEPTH = 48.0, 24.0, 16.0   # edge texture covers 48 m x 24 m of stand (tileable along u)
CANOPY_W = 48.0                                  # canopy texture tile, 48 x 48 m (tileable both ways)


def _stand(mix, seed, w, depth, edge_row, under=True):
    """Tree list (species, variant, x, y, h, yaw) for a w x depth stand; jittered 4.5 m grid like
    vegetation._scatter, an edge row of shrubs / young birch, alder and pine in front when edge_row, and the
    understorey of streetscape/vegetation.py UNDERSTOREY (young pine / birch, hazel), so the boles do not stand in
    an empty hall (review r3 X4 "trunks like a fence")."""
    rng = random.Random(seed)
    sp, wt = zip(*FOREST_MIX[mix].items())
    out = []
    for gx in range(int(w / 4.5)):
        for gy in range(int(depth / 4.5)):
            x = (gx + 0.5) * w / int(w / 4.5) + rng.uniform(-2.0, 2.0)
            y = (gy + 0.5) * 4.5 + rng.uniform(-2.0, 2.0)
            s = rng.choices(sp, wt)[0]
            out.append((s, rng.randrange(3), x % w, y, rng.uniform(*TREE_H[s]), rng.uniform(0, 2 * math.pi)))
    if under:
        names = list(UNDER_SPECIES)
        for _ in range(int(w * depth / UNDER_M2)):
            s = rng.choices(names, [UNDER_SPECIES[n][2] for n in names])[0]
            lo, hi = UNDER_SPECIES[s][:2]
            out.append((s, rng.randrange(3), rng.uniform(0, w), rng.uniform(0, depth), rng.uniform(lo, hi),
                        rng.uniform(0, 2 * math.pi)))
    if edge_row:
        for k in range(int(w / 3.0)):
            x = (k + rng.random()) * 3.0
            s = rng.choices(["shrub", "birch", "alder", "pine"], [0.5, 0.25, 0.1, 0.15])[0]
            h = rng.uniform(*TREE_H[s]) * (0.5 if s != "shrub" else 1.0)
            out.append((s, rng.randrange(3), x % w, rng.uniform(-3.0, 1.0), h, rng.uniform(0, 2 * math.pi)))
    return out


# understorey of a Podlasie pine stand (WORKING_VALUE, same table as streetscape/vegetation.py UNDERSTOREY):
# species -> (h min, h max, weight); one plant per UNDER_M2 square metres
UNDER_SPECIES = {"shrub": (1.2, 3.5, 0.55), "pine": (3.0, 7.0, 0.2), "birch": (3.0, 8.0, 0.25)}
UNDER_M2 = 60.0


def _place_stand(trees, src, href, offsets):
    objs = []
    for s, v, x, y, h, yaw in trees:
        o0 = src[f"tree_{s}_{v}"]
        k = h / href[f"tree_{s}_{v}"]
        for dx, dy in offsets:
            o = bpy.data.objects.new(f"st_{s}", o0.data)
            o.location = (x + dx, y + dy, 0.0)
            o.rotation_euler = (0, 0, yaw)
            o.scale = (k, k, k)
            bpy.context.scene.collection.objects.link(o)
            objs.append(o)
    return objs


def _flat(name, verts, col):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], [(0, 1, 2, 3)])
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1.0)
    b.inputs["Roughness"].default_value = 1.0
    me.materials.append(m)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


# ------------------------------------------------------------------------------------------- packing (numpy)
def _load(path):
    img = bpy.data.images.load(str(path))
    img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    a = np.empty(w * h * 4, np.float32)
    img.pixels.foreach_get(a)
    bpy.data.images.remove(img)
    return a.reshape(h, w, 4)


def _save(arr, path):
    h, w = arr.shape[:2]
    img = bpy.data.images.new(Path(path).stem, w, h, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    img.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).ravel())
    img.filepath_raw = str(path)
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)


def _shift(a, dy, dx):
    return np.roll(np.roll(a, dy, 0), dx, 1)


N8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]


def _dilate_colour(img, mask, iters=48):
    """Colour under the alpha = mean of the covered neighbours, grown outward (no dark / white fringe when
    coverage-preserving mips or alpha-to-coverage turn a half-covered texel on far away; review r3 W1)."""
    img = img.copy()
    m = mask.astype(np.float32)
    for _ in range(iters):
        if m.min() > 0:
            break
        acc = np.zeros_like(img)
        cnt = np.zeros_like(m)
        for dy, dx in N8:
            acc += _shift(img * m[..., None], dy, dx)
            cnt += _shift(m, dy, dx)
        new = (cnt > 0) & (m == 0)
        img[new] = acc[new] / cnt[new][:, None]
        m[new] = 1.0
    if m.min() == 0 and m.max() > 0:
        img[m == 0] = img[m > 0].mean(0)
    return img


def _open(mask, r=1):
    """Morphological opening (3x3, r times): drops 1-2 texel specks and hair-thin twigs that shimmer far away."""
    e = mask.copy()
    for _ in range(r):
        e = e & np.all([_shift(e, dy, dx) for dy, dx in N8], axis=0)
    d = e.copy()
    for _ in range(r):
        d = d | np.any([_shift(d, dy, dx) for dy, dx in N8], axis=0)
    return mask & d


def _components_min(mask, min_px):
    """Removes 8-connected alpha islands smaller than min_px (floating crown specks above the stand silhouette,
    the "lollipops" of review r4 W-H8). Label propagation by repeated min over neighbours."""
    h, w = mask.shape
    big = np.int64(h * w)
    lab = np.where(mask, np.arange(h * w, dtype=np.int64).reshape(h, w), big)
    for _ in range(4 * max(h, w)):
        nb = lab.copy()
        for dy, dx in N8:
            nb = np.minimum(nb, _shift(lab, dy, dx))
        nb = np.where(mask, nb, big)
        if np.array_equal(nb, lab):
            break
        lab = nb
    cnt = np.bincount(lab[mask], minlength=h * w + 1)
    return mask & (cnt[np.minimum(lab, big)] >= min_px)


def _srgb_to_lin(c):
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def _lin_to_srgb(c):
    c = np.clip(c, 0, 1)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * c ** (1 / 2.4) - 0.055)


def pack(stems, out_png, out_n, min_island=0, open_r=1, canopy=False):
    """Packs raw passes (stems laid out left to right) into out_png: RGB albedo (sRGB) + A coverage and
    out_n: R, G normal x, y (camera / view space, 0.5 bias), B sky visibility, A 1 (linear).
    canopy: opaque, albedo x visibility^0.7 in one RGB texture (the canopy stays an opaque URP Lit surface)."""
    cols, nrms, alphas = [], [], []
    for stem in stems:
        alb = _load(RAW / f"{stem}_alb.png")
        nrm = _load(RAW / f"{stem}_nrm.png")
        occ = _load(RAW / f"{stem}_occ.png")
        a = alb[..., 3]
        cov = a > 0.5
        if open_r:
            cov = _open(cov, open_r)
        if min_island:
            cov = _components_min(cov, min_island)
        # the 50 % coverage edge texels mix leaf and background in the pixel filter -> rebuild them (and every
        # transparent texel) from the fully covered interior
        inner = cov & (a > 0.9)
        seed = inner if inner.any() else cov
        rgb = _dilate_colour(alb[..., :3], seed)
        n = _dilate_colour(np.concatenate([nrm[..., :2], occ[..., :1]], -1), seed)
        cols.append(rgb)
        nrms.append(n)
        # outside the kept coverage the alpha is 0 except a one-texel anti-aliasing ring: the soft alpha of removed
        # twigs / specks (0.1-0.45) was raised over the cut-off by the coverage-preserving mips far away and drew
        # dotted arcs along the HLOD wall tops (artifacts/vqa/abl: gone with the edge walls skipped)
        ring = np.any([_shift(cov, dy, dx) for dy, dx in N8], axis=0) & ~cov
        alphas.append(np.where(cov, np.maximum(a, 0.5), np.where(ring, np.minimum(a, 0.45), 0.0)))
    rgb = np.concatenate(cols, 1)
    n = np.concatenate(nrms, 1)
    al = np.concatenate(alphas, 1)
    if canopy:
        lin = _srgb_to_lin(rgb) * np.clip(n[..., 2:3], 0.05, 1) ** 0.7
        _save(np.concatenate([_lin_to_srgb(lin), np.ones_like(al)[..., None]], -1), out_png)
        return
    _save(np.concatenate([rgb, al[..., None]], -1), out_png)
    # normal / visibility at half resolution (smooth crown normals; texture budget, ADR 0023): 2x2 box filter
    h2, w2 = n.shape[0] // 2, n.shape[1] // 2
    n = n[:h2 * 2, :w2 * 2].reshape(h2, 2, w2, 2, 3).mean((1, 3))
    _save(np.concatenate([n, np.ones((h2, w2, 1), np.float32)], -1), out_n)


def bake_forest(mix, src, href, seed):
    """Edge wall (side view, 1024 x 512, tileable in u) and canopy (top view, 512 x 512, tileable): alb / nrm / occ
    passes packed into forest_edge_<mix>.png + forest_edge_<mix>_n.png and forest_canopy_<mix>.png."""
    sc = bpy.context.scene
    for o in sc.objects:
        if o.type == "MESH":
            o.hide_render = True
    info = {}
    # edge: the outermost 16 m of a stand seen from outside, the stand interior behind it (16-52 m) and a dark
    # backdrop at 56 m. The interior is no longer darkened by hand (the v3.1 copies at x0.3 were the black spots of
    # review r3 W1): its darkness is the sky visibility of the occlusion pass, lit by the engine.
    trees = _stand(mix, seed, EDGE_W, EDGE_DEPTH, True)
    objs = _place_stand(trees, src, href, [(-EDGE_W, 0), (0, 0), (EDGE_W, 0)])
    hs = sorted(t[4] for t in trees if t[0] != "shrub" and t[4] > 8)
    h_med = hs[len(hs) // 2]
    deep = [(s, v, x, y + EDGE_DEPTH, h, yaw) for s, v, x, y, h, yaw in _stand(mix, seed + 7, EDGE_W, 36.0, False)]
    objs += _place_stand(deep, src, href, [(-EDGE_W, 0), (0, 0), (EDGE_W, 0)])
    back = _flat("st_back", [(-60, 56, -0.5), (EDGE_W + 60, 56, -0.5), (EDGE_W + 60, 56, h_med * 0.6),
                             (-60, 56, h_med * 0.6)], (0.030, 0.032, 0.022))
    floor = _flat("st_floor", [(-60, -6, -0.05), (EDGE_W + 60, -6, -0.05), (EDGE_W + 60, 60, -0.05),
                               (-60, 60, -0.05)], (0.045, 0.040, 0.026))
    sc, cam = bake_setup(True, (1024, 512), 24)
    cam.data.ortho_scale = EDGE_W
    cam.location = (EDGE_W / 2, -120, EDGE_H / 2 - 0.3)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    render_passes(objs + [back, floor], f"forest_edge_{mix}")
    for o in objs + [back, floor]:
        bpy.data.objects.remove(o, do_unlink=True)
    pack([f"forest_edge_{mix}"], VEG / f"forest_edge_{mix}.png", VEG / f"forest_edge_{mix}_n.png", min_island=600)
    info["edge"] = {"png": f"forest_edge_{mix}.png", "normal_png": f"forest_edge_{mix}_n.png", "w_m": EDGE_W,
                    "h_m": EDGE_H, "z0_m": -0.3, "h_median_m": round(h_med, 2), "trees": len(trees)}
    # canopy: 48 x 48 m tile from above over the forest floor, wrapped copies at the borders
    trees = _stand(mix, seed + 1, CANOPY_W, CANOPY_W, False)
    off = [(dx, dy) for dx in (-CANOPY_W, 0, CANOPY_W) for dy in (-CANOPY_W, 0, CANOPY_W)]
    objs = _place_stand(trees, src, href, off)
    floor = _flat("st_floor", [(-60, -60, 0), (110, -60, 0), (110, 110, 0), (-60, 110, 0)], (0.045, 0.040, 0.026))
    sc, cam = bake_setup(False, (512, 512), 24)
    cam.data.ortho_scale = CANOPY_W
    cam.location = (CANOPY_W / 2, CANOPY_W / 2, 120)
    cam.rotation_euler = (0, 0, 0)
    render_passes(objs + [floor], f"forest_canopy_{mix}")
    for o in objs + [floor]:
        bpy.data.objects.remove(o, do_unlink=True)
    pack([f"forest_canopy_{mix}"], VEG / f"forest_canopy_{mix}.png", None, open_r=0, canopy=True)
    info["canopy"] = {"png": f"forest_canopy_{mix}.png", "w_m": CANOPY_W}
    return info


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    meta = {}
    objs = []
    src = {}
    # --quick <name>: bake one tree's impostor only (look development), nothing exported
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    quick = argv[argv.index("--quick") + 1] if "--quick" in argv else None
    cached = {}
    if "--reuse-bakes" in argv and (VEG / "trees_meta.json").exists():
        cached = json.loads((VEG / "trees_meta.json").read_text(encoding="utf-8"))
    for sp in ("pine", "birch", "alder", "maple", "linden", "shrub"):
        for v in range(3):
            name = f"tree_{sp}_{v}"
            if quick and name != quick:
                continue
            g0, H = grow(sp, v, 0)
            o0 = to_object(name, g0)
            g1, _ = grow(sp, v, 1)
            g1 = reuse_leaf_lod(g0, g1, sum(map(ord, sp)) * 31 + v)
            o1 = to_object(name + ".lod1", g1)
            o1.hide_render = True
            png = VEG / f"impostor_{name}.png"
            prior = cached.get("trees", {}).get(name)
            if prior and png.exists() and (VEG / f"impostor_{name}_n.png").exists():
                half_w = max(math.hypot(v[0], v[1]) for v in o0.bound_box)
                S = max(H * 1.05, 2.0 * half_w * 1.04 * IMP_RES[1] / IMP_RES[0])
            else:
                S = bake_impostor(o0, name, H)
                pack([f"impostor_{name}_{k}" for k in range(IMP_NF)], png, VEG / f"impostor_{name}_n.png")
            o2 = impostor_object(name, H, png, S)
            o2.hide_render = True
            objs += [o0, o1, o2]
            src[name] = o0
            meta[name] = {"species": sp, "variant": v, "href_m": round(H, 2), "impostor_frame_m": round(S, 2),
                          "impostor_views": IMP_NF, "impostor_aspect": round(IMP_RES[0] / IMP_RES[1], 4),
                          "tris_lod0": sum(len(p.vertices) - 2 for p in o0.data.polygons),
                          "tris_lod1": sum(len(p.vertices) - 2 for p in o1.data.polygons), "tris_lod2": 2}
    if quick:
        return
    href = {k: v["href_m"] for k, v in meta.items()}
    forest = cached.get("forest_hlod") or {mix: bake_forest(mix, src, href, 1000 + i) for i, mix in enumerate(FOREST_MIX)}
    for fn, sel in (("trees.glb", [o for o in objs if not o.name.endswith(".lod2")]),
                    ("trees_lod2.glb", [o for o in objs if o.name.endswith(".lod2")])):
        for o in bpy.context.scene.objects:
            o.select_set(o in sel)
        bpy.ops.export_scene.gltf(filepath=str(VEG / fn), export_format="GLB", use_selection=True,
                                  export_apply=False, export_yup=True)
    (VEG / "trees_meta.json").write_text(json.dumps({"note": "built at href_m; instance scale = h / href_m",
                                                      "trees": meta, "forest_hlod": forest},
                                                     indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print("[trees] wrote", VEG / "trees.glb")


if __name__ == "__main__":
    main()
