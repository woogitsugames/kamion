"""Procedural tree library for Podlasie roadsides (our own generator, no external assets).

    blender -b --factory-startup -P tools/blender/world/make_trees.py

Species: Scots pine (Pinus sylvestris: tall bare trunk, grey-brown lower / orange upper bark, flat irregular
crown of whorled branches), silver birch (Betula pendula: white bark with black lenticels, drooping twigs),
black alder (Alnus glutinosa: monopodial trunk, conical crown), Norway maple (Acer platanoides: short trunk,
broad round crown), small-leaved linden (Tilia cordata: tall ovate dense crown), shrub (hazel/young birch
undergrowth). 3 variants each. Crowns are made of foliage cards (art-source/world/vegetation/leaves_*.png,
streetscape/leaf_textures.py) on a recursive branch skeleton; card normals point away from the crown centre
(soft crown shading). Per variant three LODs:
  <name>        LOD0  trunk + branches + cards  (High, < 150 m)
  <name>.lod1   LOD1  trunk + main limbs + 1/3 of the cards at 1.6x size  (Low near / High 60-150 m)
  <name>.lod2   impostor: two crossed quads with a baked orthographic render (> 150 m)
Models are built at the reference height HREF[species]; instances scale by h / HREF.
Output: art-source/world/vegetation/trees.glb, trees_meta.json, impostor_<name>.png
"""

import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

REPO = Path(__file__).resolve().parents[3]
VEG = REPO / "art-source" / "world" / "vegetation"
HREF = {"pine": 19.0, "birch": 14.0, "alder": 13.0, "maple": 12.0, "linden": 13.5, "shrub": 2.8}
BARK = {"pine": ["bark_pine_lower", "bark_pine"], "birch": ["bark_birch"], "alder": ["bark_alder"],
        "maple": ["bark_maple"], "linden": ["bark_linden"], "shrub": ["bark_shrub"]}


class Geo:
    def __init__(self):
        self.parts = {}     # mat -> (verts, faces, uvs, normals or None)

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
        z0 = H * rng.uniform(0.58, 0.68)
        z = z0
        nlimb = 0
        while z < H * 0.93:
            f = (z - z0) / (H * 0.93 - z0)
            for _ in range(rng.randint(3, 5)):
                if rng.random() < 0.28:                 # missing / broken branch in the whorl
                    continue
                a = rng.uniform(0, 2 * math.pi)
                bias = 0.65 + 0.55 * max(0.0, math.cos(a - light))
                L = (1.0 + 2.6 * math.sin(math.pi * min(1.0, 0.25 + f * 0.85))) * bias * rng.uniform(0.6, 1.2)
                up = rng.uniform(0.15, 0.55) + f * 0.3
                d = Vector((math.cos(a), math.sin(a), up))
                k = z / H * 14
                p0 = trunk[min(int(k), 13)].lerp(trunk[min(int(k) + 1, 14)], k - int(k))
                br = bend_path(p0, d, L, 5, rng, 0.22, gravity=-0.04)
                if lod == 0 or L > 1.8:
                    g.tube("bark_twig", br, [0.07 * (1 - f * 0.4) * (1 - i / 6) + 0.012 for i in range(6)],
                           max(3, seg // 2))
                # foliage clumps: 1-3 dense clusters near the limb end (sparse inside the crown)
                for cl in range(rng.randint(2, 4)):
                    t = rng.uniform(0.55, 1.0)
                    kk = t * (len(br) - 1)
                    ia = int(kk)
                    q = br[ia].lerp(br[min(ia + 1, len(br) - 1)], kk - ia)
                    rcl = rng.uniform(0.5, 1.0) * (0.7 + 0.4 * bias)
                    for _ in range(int((7 + 6 * rcl) * (1.0 if lod == 0 else 0.45)) + 1):
                        pc = q + Vector((crng.uniform(-rcl, rcl), crng.uniform(-rcl, rcl), crng.uniform(-0.55, 0.45) * rcl))
                        nrm = Vector((crng.uniform(-1, 1), crng.uniform(-1, 1), crng.uniform(-0.2, 1.4)))
                        g.card(leaf, pc, nrm, Vector((0, 0, 1)), 1.25 * csize_k * crng.uniform(0.8, 1.2), cc)
                nlimb += 1
            z += rng.uniform(0.45, 1.0)
        # leader: the stem ends inside the top clumps (no tuft on a bare pole)
        for _ in range(int(14 * (1.0 if lod == 0 else 0.5))):
            pc = trunk[-1] + Vector((crng.uniform(-1.1, 1.1), crng.uniform(-1.1, 1.1), crng.uniform(-1.2, 0.2)))
            g.card(leaf, pc, Vector((crng.uniform(-1, 1), crng.uniform(-1, 1), 1.2)), Vector((0, 0, 1)), 1.2 * csize_k, cc)
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
    trunk_frac = {"birch": 0.4, "alder": 0.3, "maple": 0.35, "linden": 0.4}[species]
    r0 = {"birch": 0.17, "alder": 0.18, "maple": 0.22, "linden": 0.25}[species]
    top = {"birch": 0.88, "alder": 0.95, "maple": 0.6, "linden": 0.75}[species]
    lean = Vector((rng.uniform(-0.06, 0.06), rng.uniform(-0.06, 0.06), 1))
    trunk = bend_path(Vector((0, 0, -0.3)), lean, H * top, 10, rng, 0.04)
    g.tube(BARK[species][0], trunk, [r0 * (1 - i / 10) ** 0.9 + 0.02 for i in range(11)], seg)
    cc = trunk[0] + Vector((0, 0, H * (trunk_frac + 1) / 2))
    nmain = {"birch": 9, "alder": 14, "maple": 8, "linden": 10}[species]
    for b in range(nmain):
        f = trunk_frac + (top - trunk_frac) * (b + rng.uniform(0, 1)) / nmain
        k = f / top * 10
        p0 = trunk[min(int(k), 10)]
        a = rng.uniform(0, 2 * math.pi)
        up = {"birch": 0.9, "alder": 0.25, "maple": 0.8, "linden": 0.7}[species]
        rel = (f - trunk_frac) / max(top - trunk_frac, 1e-3)
        L = H * {"birch": 0.32, "alder": 0.3 * (1 - rel) + 0.06, "maple": 0.42, "linden": 0.36 * (1 - 0.5 * rel)}[species]
        L *= rng.uniform(0.75, 1.15)
        d = Vector((math.cos(a), math.sin(a), up))
        br = bend_path(p0, d, L, 5, rng, 0.18)
        g.tube(BARK[species][0] if species != "birch" else "bark_twig", br,
               [r0 * 0.4 * (1 - i / 6) + 0.012 for i in range(6)], max(3, seg // 2))
        nsub = (7 if species == "birch" else 5) if lod == 0 else (5 if species == "birch" else 3)
        for s in range(nsub):
            t = 0.35 + 0.6 * rng.random()
            q0 = br[int(t * 5)]
            a2 = a + rng.uniform(-1.2, 1.2)
            droop = 0.6 if species == "birch" else 0.15
            d2 = Vector((math.cos(a2), math.sin(a2), rng.uniform(-0.2, 0.6)))
            sub = bend_path(q0, d2, L * 0.45, 4, rng, 0.2, gravity=droop * 0.25)
            if lod == 0:
                g.tube("bark_twig", sub, [0.03 * (1 - i / 5) + 0.006 for i in range(5)], 3)
            csz = {"birch": 0.95, "alder": 1.15, "maple": 1.35, "linden": 1.3}[species]
            dens = {"birch": 14, "alder": 12, "maple": 14, "linden": 15}[species]
            cards_along(sub, csz, dens, cc, droop=0.4 if species == "birch" else 0.0, start=0.1)
        cards_along(br, {"birch": 1.0, "alder": 1.15, "maple": 1.35, "linden": 1.3}[species], 6, cc, start=0.5)
    return g, H


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
    file = name.replace("bark_pine_lower", "bark_alder")
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


def bake_impostor(ob, name, H):
    """Orthographic side render of LOD0 with transparent background -> impostor texture."""
    sc = bpy.context.scene
    sc.render.engine = "BLENDER_EEVEE_NEXT"
    sc.render.film_transparent = True
    sc.render.resolution_x, sc.render.resolution_y = 256, 384
    sc.eevee.taa_render_samples = 16
    sc.view_settings.view_transform = "Standard"
    for o in sc.objects:
        o.hide_render = o is not ob and o.type == "MESH"
    cam = bpy.data.objects.get("imp_cam") or bpy.data.objects.new("imp_cam", bpy.data.cameras.new("imp_cam"))
    if cam.name not in sc.collection.objects:
        sc.collection.objects.link(cam)
    cam.data.type = "ORTHO"
    cam.data.ortho_scale = H * 1.05
    cam.location = (0, -60, H * 0.5)
    cam.rotation_euler = (math.pi / 2, 0, 0)
    sc.camera = cam
    if not bpy.data.objects.get("imp_sun"):
        s = bpy.data.objects.new("imp_sun", bpy.data.lights.new("imp_sun", "SUN"))
        s.data.energy = 3.0
        s.rotation_euler = (math.radians(50), 0, math.radians(20))
        sc.collection.objects.link(s)
    if sc.world is None:
        sc.world = bpy.data.worlds.new("w")
    sc.world.use_nodes = True
    sc.world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.8
    path = VEG / f"impostor_{name}.png"
    sc.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)
    ob.hide_render = True
    return path


def impostor_object(name, H, png):
    m = bpy.data.materials.new(f"impostor_{name}")
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(str(png))
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(tex.outputs["Alpha"], bsdf.inputs["Alpha"])
    w = H * 1.05 * (256 / 384) / 2       # impostor plane matches the 256 x 384 bake (wide crowns)
    verts, faces, uvs = [], [], []
    for k in range(2):
        a = k * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        base = len(verts)
        hh = H * 1.05                      # bake: ortho_scale = H * 1.05 over the 384 px height
        for x, z, uv in ((-w, 0, (0, 0)), (w, 0, (1, 0)), (w, hh, (1, 1)), (-w, hh, (0, 1))):
            verts.append((x * c, x * s, z - 0.3 + H * 0.5 - hh / 2))
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


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    meta = {}
    objs = []
    for sp in ("pine", "birch", "alder", "maple", "linden", "shrub"):
        for v in range(3):
            name = f"tree_{sp}_{v}"
            g0, H = grow(sp, v, 0)
            o0 = to_object(name, g0)
            g1, _ = grow(sp, v, 1)
            o1 = to_object(name + ".lod1", g1)
            o1.hide_render = True
            png = bake_impostor(o0, name, H)
            o2 = impostor_object(name, H, png)
            o2.hide_render = True
            objs += [o0, o1, o2]
            meta[name] = {"species": sp, "variant": v, "href_m": round(H, 2),
                          "tris_lod0": sum(len(p.vertices) - 2 for p in o0.data.polygons),
                          "tris_lod1": sum(len(p.vertices) - 2 for p in o1.data.polygons), "tris_lod2": 4}
    for fn, sel in (("trees.glb", [o for o in objs if not o.name.endswith(".lod2")]),
                    ("trees_lod2.glb", [o for o in objs if o.name.endswith(".lod2")])):
        for o in bpy.context.scene.objects:
            o.select_set(o in sel)
        bpy.ops.export_scene.gltf(filepath=str(VEG / fn), export_format="GLB", use_selection=True,
                                  export_apply=False, export_yup=True)
    (VEG / "trees_meta.json").write_text(json.dumps({"note": "built at href_m; instance scale = h / href_m",
                                                      "trees": meta}, indent=1, sort_keys=True) + "\n",
                                         encoding="utf-8")
    print("[trees] wrote", VEG / "trees.glb")


main()
