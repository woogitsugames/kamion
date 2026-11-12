"""Materials for the TRAKT exterior (A4).

Render materials are many; every one is tagged with a GAME SLOT (<= 6 in Unity, A6 atlases):
  PAINT  - body paint (livery colour, clearcoat)
  TRIM   - textured/satin plastics, rubber seals, chassis black paint, plate, gaps
  METAL  - aluminium, chrome (sparingly), steel, checker plate
  GLASS  - windscreen/side glass, mirror glass
  LIGHTS - lenses, reflectors, LED light guides (emission driven by the game)
  TYRE   - tyre rubber (tread + sidewall lettering)
Values are linear albedo / roughness WORKING_VALUEs (no measured reference table yet, docs/06 s3);
they follow ART_BIBLE: plastics dark grey not tar black (rough >= 0.55), tyre albedo ~0.025 rough ~0.85,
chrome only on the emblem.
"""
import math
import os

import bpy
import numpy as np

from geom import REPO, STATE

TEX_DIR = os.path.join(REPO, "art-source", "truck", "exterior", "textures")
FONT = os.path.join(REPO, "game", "Assets", "_Project", "UI", "Resources", "Fonts", "Inter-Regular.otf")

LIVERIES = {
    # name: (base linear rgb, base roughness, metallic flake, label)
    "white": ((0.78, 0.785, 0.78), 0.32, 0.0, "biel flotowa"),
    "dark": ((0.020, 0.040, 0.034), 0.30, 0.35, "zieleń butelkowa (ciemna)"),
    "clay": ((0.50, 0.50, 0.50), 0.55, 0.0, "clay"),
}
SLOTS = {}
PARAMS = {"dirt": 0.5, "drl": 1.0}


# ---------------------------------------------------------------- node helpers
def _new(name, slot):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    m["game_slot"] = slot
    SLOTS[name] = slot
    STATE["mats"][name] = m
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs[0])
    return m, nt, b


def N(nt, kind, **kw):
    n = nt.nodes.new(kind)
    for k, v in kw.items():
        if k.startswith("_"):
            setattr(n, k[1:], v)
        else:
            n.inputs[k].default_value = v
    return n


def L(nt, a, b):
    nt.links.new(a, b)


def math_node(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            L(nt, v, n.inputs[i])
    return n.outputs[0]


def principled(name, slot, rgb, rough, metal=0.0, coat=0.0, spec=0.5, aniso=0.0, transm=0.0, ior=1.5,
               emit=None, emit_s=0.0, alpha=1.0):
    m, nt, b = _new(name, slot)
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Anisotropic"].default_value = aniso
    b.inputs["Transmission Weight"].default_value = transm
    b.inputs["IOR"].default_value = ior
    if emit:
        b.inputs["Emission Color"].default_value = (*emit, 1)
        b.inputs["Emission Strength"].default_value = emit_s
    m.diffuse_color = (*rgb, 1)
    return m, nt, b


def thin_glass(name, slot, tint, rough=0.0, ior=1.52):
    """Thin sheet glass (single-surface glazing/lenses): transparent with Fresnel reflection, no
    refraction - a single-sided Principled transmission surface would act as a solid lens."""
    m, nt, b = _new(name, slot)
    out = nt.nodes["Material Output"]
    nt.nodes.remove(b)
    tr = N(nt, "ShaderNodeBsdfTransparent")
    tr.inputs["Color"].default_value = (*tint, 1)
    gl = N(nt, "ShaderNodeBsdfGlossy", Roughness=rough)
    gl.inputs["Color"].default_value = (1, 1, 1, 1)
    # Layer Weight Fresnel is symmetric front/back; the Fresnel node inverts the IOR on back faces and
    # gives total internal reflection when seen from inside the cab (thin sheets have no inside)
    # B2.1: Layer Weight 'Fresnel' with Blend = 1 - 1/IOR is the dielectric Fresnel curve of that IOR (F0 = 4 % for
    # 1.52 glass, 5.2 % for 1.59 polycarbonate lamp lenses); before it was 0.16/0.10 (weak, 'aquarium' glass)
    fr = N(nt, "ShaderNodeLayerWeight", Blend=1.0 - 1.0 / ior)
    mix = N(nt, "ShaderNodeMixShader")
    L(nt, fr.outputs["Fresnel"], mix.inputs[0])
    L(nt, tr.outputs[0], mix.inputs[1])
    L(nt, gl.outputs[0], mix.inputs[2])
    L(nt, mix.outputs[0], out.inputs[0])
    m.diffuse_color = (*tint, 0.3)
    return m


# ---------------------------------------------------------------- grime (subtle, height + cavity driven)
def grime(nt, b, rgb_sock_default, rough_default, h0=1.0, amount=0.5, cavity=True, dust=(0.16, 0.145, 0.12),
          film=0.0, streak=0.0, back=0.0, cav=0.8):
    """Mix road dust into base colour/roughness: stronger near the ground, in cavities (AO), broken by noise.
    film: extra road-film gradient on the lowest 0.6 m (spray from the own wheels; R2 #11).
    streak: vertical run-down streaks (noise stretched in z) on vertical faces.
    back: rear-wheel spray on rear-facing faces (cab back wall), fading upwards to ~2.2 m."""
    geo = N(nt, "ShaderNodeNewGeometry")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    L(nt, geo.outputs["Position"], sep.inputs[0])
    hz = math_node(nt, "SUBTRACT", h0, sep.outputs[2])
    hz = math_node(nt, "DIVIDE", hz, h0, clamp=True)
    noise = N(nt, "ShaderNodeTexNoise", Scale=3.5, Detail=6.0, Roughness=0.6)
    L(nt, geo.outputs["Position"], noise.inputs["Vector"])
    nmap = N(nt, "ShaderNodeMapRange", **{"From Min": 0.35, "From Max": 0.75})
    L(nt, noise.outputs["Fac"], nmap.inputs["Value"])
    f = math_node(nt, "MULTIPLY", hz, nmap.outputs[0])
    if film > 0:
        lowz = math_node(nt, "SUBTRACT", 0.62, sep.outputs[2])
        lowz = math_node(nt, "DIVIDE", lowz, 0.30, clamp=True)            # 0 above 0.62 m, 1 below 0.32 m
        n2 = N(nt, "ShaderNodeTexNoise", Scale=9.0, Detail=8.0, Roughness=0.65)
        L(nt, geo.outputs["Position"], n2.inputs["Vector"])
        m2 = N(nt, "ShaderNodeMapRange", **{"From Min": 0.30, "From Max": 0.62, "To Min": 0.45})
        L(nt, n2.outputs["Fac"], m2.inputs["Value"])
        f = math_node(nt, "ADD", f, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", lowz, m2.outputs[0]), film))
    if streak > 0:
        sc = N(nt, "ShaderNodeVectorMath", _operation="MULTIPLY")
        sc.inputs[1].default_value = (14.0, 14.0, 0.9)
        L(nt, geo.outputs["Position"], sc.inputs[0])
        n3 = N(nt, "ShaderNodeTexNoise", Scale=1.0, Detail=4.0, Roughness=0.5)
        L(nt, sc.outputs[0], n3.inputs["Vector"])
        m3 = N(nt, "ShaderNodeMapRange", **{"From Min": 0.55, "From Max": 0.75})
        L(nt, n3.outputs["Fac"], m3.inputs["Value"])
        vert = N(nt, "ShaderNodeSeparateXYZ")
        L(nt, geo.outputs["Normal"], vert.inputs[0])
        isv = math_node(nt, "SUBTRACT", 1.0, math_node(nt, "ABSOLUTE", vert.outputs[2]))
        hz2 = math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", 2.4, sep.outputs[2]), 2.4, clamp=True)
        f = math_node(nt, "ADD", f, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", m3.outputs[0], isv),
                                              math_node(nt, "MULTIPLY", hz2, streak)))
    if back > 0:
        nrm = N(nt, "ShaderNodeSeparateXYZ")
        L(nt, geo.outputs["Normal"], nrm.inputs[0])
        rear = math_node(nt, "MULTIPLY", nrm.outputs[1], -1.0, clamp=True)
        hb = math_node(nt, "DIVIDE", math_node(nt, "SUBTRACT", 2.3, sep.outputs[2]), 1.2, clamp=True)
        n4 = N(nt, "ShaderNodeTexNoise", Scale=6.0, Detail=6.0, Roughness=0.6)
        L(nt, geo.outputs["Position"], n4.inputs["Vector"])
        m4 = N(nt, "ShaderNodeMapRange", **{"From Min": 0.3, "From Max": 0.6, "To Min": 0.35})
        L(nt, n4.outputs["Fac"], m4.inputs["Value"])
        f = math_node(nt, "ADD", f, math_node(nt, "MULTIPLY", math_node(nt, "MULTIPLY", rear, hb),
                                              math_node(nt, "MULTIPLY", m4.outputs[0], back)))
    if cavity:
        ao = N(nt, "ShaderNodeAmbientOcclusion", Distance=0.12, _samples=8)
        inv = math_node(nt, "SUBTRACT", 1.0, ao.outputs["AO"])
        inv = math_node(nt, "MULTIPLY", inv, cav)
        f = math_node(nt, "ADD", f, inv)
    f = math_node(nt, "MULTIPLY", f, amount * PARAMS["dirt"], clamp=True)
    mix = N(nt, "ShaderNodeMix", _data_type="RGBA")
    mix.inputs[6].default_value = (*rgb_sock_default, 1) if isinstance(rgb_sock_default, tuple) else (0, 0, 0, 1)
    if not isinstance(rgb_sock_default, tuple):
        L(nt, rgb_sock_default, mix.inputs[6])
    mix.inputs[7].default_value = (*dust, 1)
    mix.label = "grime_mix"          # A6 export: input A = clean colour, factor = dirt mask (baked separately)
    L(nt, f, mix.inputs[0])
    L(nt, mix.outputs[2], b.inputs["Base Color"])
    r = math_node(nt, "MULTIPLY", f, 0.35)
    r = math_node(nt, "ADD", r, rough_default, clamp=True)
    r.node.label = "grime_rough"     # input 1 = clean roughness
    L(nt, r, b.inputs["Roughness"])
    return f


def micro_bump(nt, b, scale, strength, distance=0.0004, kind="noise", target="Normal"):
    tc = N(nt, "ShaderNodeTexCoord")
    if kind == "noise":
        t = N(nt, "ShaderNodeTexNoise", Scale=scale, Detail=8.0, Roughness=0.7)
        L(nt, tc.outputs["Object"], t.inputs["Vector"])
        h = t.outputs["Fac"]
    else:
        t = N(nt, "ShaderNodeTexVoronoi", Scale=scale)
        L(nt, tc.outputs["Object"], t.inputs["Vector"])
        h = t.outputs["Distance"]
    bump = N(nt, "ShaderNodeBump", Strength=strength, Distance=distance)
    L(nt, h, bump.inputs["Height"])
    L(nt, bump.outputs["Normal"], b.inputs[target])
    return bump


# ---------------------------------------------------------------- generated images (numpy)
def _save_image(name, arr, colorspace="Non-Color"):
    """arr: HxWx(1|3|4) float in [0,1], row 0 = bottom (Blender convention)."""
    os.makedirs(TEX_DIR, exist_ok=True)
    h, w = arr.shape[:2]
    if arr.ndim == 2:
        arr = arr[..., None]
    if arr.shape[2] == 1:
        arr = np.repeat(arr, 3, axis=2)
    if arr.shape[2] == 3:
        arr = np.concatenate([arr, np.ones((h, w, 1), dtype=arr.dtype)], axis=2)
    img = bpy.data.images.get(name) or bpy.data.images.new(name, w, h, alpha=False, float_buffer=False)
    if img.size[0] != w or img.size[1] != h:
        img.scale(w, h)
    img.pixels.foreach_set(arr.astype(np.float32).ravel())
    img.filepath_raw = os.path.join(TEX_DIR, name + ".png")
    img.file_format = "PNG"
    img.save()
    img.colorspace_settings.name = colorspace
    return img


def tread_height(kind, w=2048, h=256, pitches=16):
    """Own tread designs, one image = `pitches` pitches around (u), tread width across (v in 0..1).
    steer: 4 zig-zag circumferential grooves (plus modelled straight base grooves), sipes in the ribs.
    drive: closed shoulder blocks with lateral grooves, centre blocks offset half a pitch, sipes."""
    u = (np.arange(w) + 0.5) / w * pitches          # pitch coordinate
    v = (np.arange(h) + 0.5) / h                    # across the tread
    U, Vv = np.meshgrid(u, v)
    hgt = np.ones_like(U)
    fu = U % 1.0
    if kind == "steer":
        tri = np.abs(fu * 2 - 1) * 2 - 1           # -1..1 zig-zag per pitch
        for c in (0.18, 0.39, 0.61, 0.82):
            d = np.abs(Vv - (c + 0.022 * tri))
            hgt = np.minimum(hgt, np.clip((d - 0.020) / 0.012, 0, 1))
        sip = np.abs(((U * 3 + Vv * 1.5) % 1.0) - 0.5) < 0.025
        rib = (Vv > 0.08) & (Vv < 0.92)
        hgt = np.where(sip & rib & (hgt > 0.9), 0.55, hgt)
        shoulder = (Vv < 0.06) | (Vv > 0.94)
        notch = (np.abs(fu - 0.5) < 0.05) & shoulder
        hgt = np.where(notch, 0.4, hgt)
    else:  # drive
        for c in (0.25, 0.50, 0.75):
            d = np.abs(Vv - c)
            hgt = np.minimum(hgt, np.clip((d - 0.026) / 0.012, 0, 1))
        for (a, b_, off) in ((0.0, 0.25, 0.0), (0.25, 0.5, 0.5), (0.5, 0.75, 0.0), (0.75, 1.0, 0.5)):
            band = (Vv >= a) & (Vv < b_)
            slope = 0.25 * (Vv - a) / (b_ - a)
            g = np.abs(((U + off + slope) % 1.0) - 0.5)
            lat = np.clip((0.5 - g - 0.40) / 0.03, 0, 1)   # lateral groove ~20% of pitch
            hgt = np.where(band, np.minimum(hgt, 1 - lat), hgt)
        sip = np.abs(((U * 2 + 0.25) % 1.0) - 0.5) < 0.02
        hgt = np.where(sip & (hgt > 0.9), 0.6, hgt)
    return hgt


def make_tread_images():
    return {k: _save_image(f"tread_{k}", tread_height(k)) for k in ("steer", "drive")}


def checker_plate(n=256):
    """Aluminium tread plate (5-bar pattern), one tile = 0.1 m."""
    y, x = np.mgrid[0:n, 0:n] / n
    hgt = np.zeros((n, n))
    for cx, cy, ang in ((0.25, 0.25, 45), (0.75, 0.75, 45), (0.75, 0.25, -45), (0.25, 0.75, -45)):
        a = math.radians(ang)
        dx, dy = x - cx, y - cy
        along = dx * math.cos(a) + dy * math.sin(a)
        across = -dx * math.sin(a) + dy * math.cos(a)
        bar = (np.abs(across) < 0.035) & (np.abs(along) < 0.17)
        hgt = np.maximum(hgt, bar * np.clip(1 - (np.abs(along) / 0.17) ** 6, 0, 1))
    return _save_image("checker_plate", hgt)


def louver_mask(n=256):
    """Perforated heat shield (round holes, staggered), one tile = 0.05 m."""
    y, x = np.mgrid[0:n, 0:n] / n
    holes = np.zeros((n, n))
    for cx, cy in ((0.25, 0.25), (0.75, 0.25), (0.0, 0.75), (0.5, 0.75), (1.0, 0.75), (0.25, 1.25), (0.75, -0.25)):
        holes = np.maximum(holes, (np.hypot(x - cx, y - cy) < 0.17).astype(float))
    return _save_image("perforation", 1 - holes)


def honeycomb(w=256, strand=0.16):
    """Seamless pointy-top hex mesh: one tile = sqrt(3) x 3 circumradii (two cells). 1 = strand, 0 = hole."""
    h = int(round(w * 3 / math.sqrt(3)))
    a = 1.0
    W, H = math.sqrt(3) * a, 3 * a
    y, x = np.mgrid[0:h, 0:w]
    px, py = (x + 0.5) / w * W, (y + 0.5) / h * H
    d = np.full((h, w), 9.0)
    ap = a * math.sqrt(3) / 2
    for j in range(-1, 4):
        for i in range(-1, 3):
            cx, cy = i * W + (j % 2) * W / 2, j * 1.5 * a
            dx, dy = np.abs(px - cx), np.abs(py - cy)
            d = np.minimum(d, np.maximum(dx, dx * 0.5 + dy * math.sqrt(3) / 2))
    t = (d / ap - (1 - strand)) / 0.05
    return _save_image(f"honeycomb_{w}", np.clip(t, 0, 1))


def honey_material(name, cell, rgb=(0.030, 0.031, 0.033)):
    """Honeycomb grille insert: strands satin dark plastic, holes near-black (depth faked by colour + bump).
    cell = flat-to-flat cell size in metres; box UV (front faces: u = x, v = z)."""
    m, nt, b = principled(name, "TRIM", rgb, 0.45)
    img = STATE.setdefault("honey_img", None) or honeycomb()
    STATE["honey_img"] = img
    a = cell / math.sqrt(3)
    tc = N(nt, "ShaderNodeUVMap", _uv_map="UVMap")
    mp = N(nt, "ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1 / (math.sqrt(3) * a), 1 / (3 * a), 1)
    L(nt, tc.outputs["UV"], mp.inputs["Vector"])
    ti = N(nt, "ShaderNodeTexImage", _image=img, _interpolation="Linear")
    L(nt, mp.outputs[0], ti.inputs[0])
    mix = N(nt, "ShaderNodeMix", _data_type="RGBA")
    mix.inputs[6].default_value = (0.002, 0.002, 0.002, 1)
    mix.inputs[7].default_value = (*rgb, 1)
    L(nt, ti.outputs["Color"], mix.inputs[0])
    L(nt, mix.outputs[2], b.inputs["Base Color"])
    rr = math_node(nt, "ADD", math_node(nt, "MULTIPLY", ti.outputs["Color"], -0.3), 0.75)
    L(nt, rr, b.inputs["Roughness"])
    bump = N(nt, "ShaderNodeBump", Strength=0.8, Distance=cell * 0.25)
    L(nt, ti.outputs["Color"], bump.inputs["Height"])
    L(nt, bump.outputs["Normal"], b.inputs["Normal"])
    return m


# ---------------------------------------------------------------- text rendered to texture (Inter, OFL)
def render_text_texture(name, items, w, h, bg=(0, 0, 0), shapes=None, colorspace="Non-Color"):
    """Render 2D text items into an image with an orthographic Cycles camera in a scratch scene.
    items: [(text, x, y, size, rot_deg, rgb, bold, align)] in pixel coords (origin bottom-left)."""
    sc = bpy.data.scenes.new("texgen_" + name)
    sc.render.engine = "CYCLES"
    sc.cycles.device = bpy.context.scene.cycles.device
    sc.cycles.samples = 16
    sc.cycles.use_denoising = False
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.film_transparent = False
    sc.view_settings.view_transform = "Standard"
    wd = bpy.data.worlds.new("texgen_w")
    wd.use_nodes = True
    wd.node_tree.nodes["Background"].inputs["Color"].default_value = (*bg, 1)
    wd.node_tree.nodes["Background"].inputs["Strength"].default_value = 1.0
    sc.world = wd
    font = bpy.data.fonts.load(FONT, check_existing=True)
    made = []

    def emis(rgb):
        key = "texgen_em_%.2f_%.2f_%.2f" % rgb
        m = bpy.data.materials.get(key)
        if not m:
            m = bpy.data.materials.new(key)
            m.use_nodes = True
            nt = m.node_tree
            for n in list(nt.nodes):
                nt.nodes.remove(n)
            o = nt.nodes.new("ShaderNodeOutputMaterial")
            e = nt.nodes.new("ShaderNodeEmission")
            e.inputs["Color"].default_value = (*rgb, 1)
            nt.links.new(e.outputs[0], o.inputs[0])
        return m

    for (txt, x, y, size, rot, rgb, bold, align) in items:
        cu = bpy.data.curves.new("t", "FONT")
        cu.body = txt
        cu.font = font
        cu.size = size
        cu.align_x = align
        cu.align_y = "CENTER"
        cu.offset = bold
        cu.materials.append(emis(rgb))
        ob = bpy.data.objects.new("t", cu)
        ob.location = (x, y, 0)
        ob.rotation_euler = (0, 0, math.radians(rot))
        sc.collection.objects.link(ob)
        made.append(ob)
    for sh in shapes or []:
        kind, pts, rgb = sh
        import bmesh
        bm = bmesh.new()
        vs = [bm.verts.new((px, py, -0.1)) for px, py in pts]
        bm.faces.new(vs)
        me = bpy.data.meshes.new("s")
        bm.to_mesh(me)
        me.materials.append(emis(rgb))
        ob = bpy.data.objects.new("s", me)
        sc.collection.objects.link(ob)
        made.append(ob)
    cam = bpy.data.cameras.new("texgen_cam")
    cam.type = "ORTHO"
    cam.ortho_scale = w
    co = bpy.data.objects.new("texgen_cam", cam)
    co.location = (w / 2, h / 2, 10)
    sc.collection.objects.link(co)
    sc.camera = co
    os.makedirs(TEX_DIR, exist_ok=True)
    path = os.path.join(TEX_DIR, name + ".png")
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True, scene=sc.name)
    for ob in made + [co]:
        bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.scenes.remove(sc)
    img = bpy.data.images.load(path, check_existing=False)
    img.colorspace_settings.name = colorspace
    return img


def make_sidewall_image(kind):
    """Generic sidewall lettering (no brand): size, load/speed index, construction, M+S, 3PMSF note,
    regroovable, rotation/position, fictional E-mark and DOT code. Text runs along u (circumference)."""
    W, H = 4096, 192
    g = (1, 1, 1)
    pos = "STEER" if kind == "steer" else "DRIVE"
    items = [
        ("315/80 R22.5", 330, 100, 74, 0, g, 0.02, "CENTER"),
        ("156/150L", 900, 100, 46, 0, g, 0.01, "CENTER"),
        ("TUBELESS  RADIAL", 1400, 100, 34, 0, g, 0.0, "CENTER"),
        (pos, 1950, 100, 60, 0, g, 0.02, "CENTER"),
        ("M+S", 2380, 100, 46, 0, g, 0.01, "CENTER"),
        ("REGROOVABLE", 2850, 100, 34, 0, g, 0.0, "CENTER"),
        ("315/80 R22.5", 3420, 100, 74, 0, g, 0.02, "CENTER"),
        ("E20 0217  DOT 4T7R K2Q 3825", 3420, 40, 20, 0, g, 0.0, "CENTER"),
        ("MAX LOAD 4000 kg SINGLE  3350 kg DUAL  AT 900 kPa", 1400, 40, 18, 0, g, 0.0, "CENTER"),
    ]
    # thin raised rim lines (moulding edges) top and bottom
    shapes = [("rect", [(0, 4), (W, 4), (W, 9), (0, 9)], g), ("rect", [(0, H - 9), (W, H - 9), (W, H - 4), (0, H - 4)], g)]
    # 3PMSF mountain + snowflake (simplified, generic regulatory pictogram)
    cx = 2600
    shapes.append(("mtn", [(cx - 40, 62), (cx - 8, 140), (cx + 10, 112), (cx + 22, 128), (cx + 44, 62)], g))
    return render_text_texture(f"sidewall_{kind}", items, W, H, shapes=shapes)


def make_plate_image():
    """Polish-style EU plate (fictional registration; PL plate 520 x 114 mm, WORKING_VALUE: verify the
    PL regulation on number plates). Font is Inter, not the regulatory plate typeface (UNVERIFIED look)."""
    W, H = 1040, 228
    blue = (0.0, 0.06, 0.40)
    yellow = (0.95, 0.75, 0.0)
    items = [("PL", 58, 52, 52, 0, (1, 1, 1), 0.02, "CENTER"),
             ("BI 4K271", 590, 112, 170, 0, (0.01, 0.01, 0.01), 0.035, "CENTER")]
    shapes = [("band", [(8, 8), (110, 8), (110, 220), (8, 220)], blue),
              ("border", [(0, 0), (W, 0), (W, 6), (0, 6)], (0.02, 0.02, 0.02)),
              ("border", [(0, H - 6), (W, H - 6), (W, H), (0, H)], (0.02, 0.02, 0.02)),
              ("border", [(W - 6, 0), (W, 0), (W, H), (W - 6, H)], (0.02, 0.02, 0.02)),
              ("border", [(0, 0), (6, 0), (6, H), (0, H)], (0.02, 0.02, 0.02))]
    for k in range(12):  # EU stars
        a = 2 * math.pi * k / 12
        sx, sy = 59 + 30 * math.cos(a), 150 + 30 * math.sin(a)
        star = []
        for j in range(10):
            r = 6.5 if j % 2 == 0 else 2.6
            aa = math.pi / 2 + j * math.pi / 5
            star.append((sx + r * math.cos(aa), sy + r * math.sin(aa)))
        shapes.append(("star", star, yellow))
    return render_text_texture("plate_front", items, W, H, bg=(0.85, 0.85, 0.84), shapes=shapes, colorspace="sRGB")


# ---------------------------------------------------------------- library
def build_paint(livery, clay=False):
    """(Re)build the body paint for a livery; objects keep the same material datablock."""
    lv = LIVERIES["clay" if clay else livery]
    m, nt, b = principled("paint", "PAINT", lv[0], lv[1], metal=lv[2], coat=0.0 if clay else 1.0)
    b.inputs["Coat Roughness"].default_value = 0.03
    b.inputs["Coat IOR"].default_value = 1.5
    if not clay:
        micro_bump(nt, b, 260.0, 0.03, 0.0002, target="Coat Normal")  # orange peel
        # fleet truck a few days after washing: road film low down, run-down streaks, rear-wheel spray on
        # the cab back wall (R2 #5/#11)
        grime(nt, b, lv[0], lv[1], h0=1.6, amount=0.55, film=1.6, streak=0.35, back=3.2,
              dust=(0.15, 0.135, 0.11), cav=1.8)
    # wordmark: dark satin on light liveries, satin silver on dark ones (R2 #9: it vanished on bottle green)
    if livery == "dark" and not clay:
        principled("wordmark", "METAL", (0.62, 0.63, 0.64), 0.32, metal=1.0)
    else:
        principled("wordmark", "METAL", (0.10, 0.104, 0.11), 0.30, metal=1.0)
    return m


def alu_wheel(clay=False):
    """Forged aluminium wheel, machined (R2 #6: was mirror-like at roughness 0.17): roughness 0.26, turned
    rings along the profile, anisotropy along the circumference, brake dust in the dish and round the nuts."""
    rgb = (0.86, 0.87, 0.88)
    m, nt, b = principled("alu_wheel", "METAL", rgb, 0.26, metal=1.0, aniso=0.45)
    if clay:
        return m
    tg = N(nt, "ShaderNodeTangent", _direction_type="UV_MAP", _uv_map="UVMap")
    L(nt, tg.outputs["Tangent"], b.inputs["Tangent"])
    uvn = N(nt, "ShaderNodeUVMap", _uv_map="UVMap")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    L(nt, uvn.outputs["UV"], sep.inputs[0])
    rings = math_node(nt, "SINE", math_node(nt, "MULTIPLY", sep.outputs[1], 900.0))
    bump = N(nt, "ShaderNodeBump", Strength=0.25, Distance=0.0002)
    L(nt, rings, bump.inputs["Height"])
    L(nt, bump.outputs["Normal"], b.inputs["Normal"])
    grime(nt, b, rgb, 0.26, h0=1.15, amount=1.5, dust=(0.085, 0.068, 0.050), film=0.6)
    return m


def grease(clay=False):
    """Fifth-wheel grease (R2 #5: was flat light grey): dark brown-black, wet sheen where thick, dull brown
    smear where thin, lumpy."""
    m, nt, b = principled("grease", "METAL", (0.020, 0.015, 0.009), 0.12, spec=0.45)
    if clay:
        return m
    tc = N(nt, "ShaderNodeTexCoord")
    nz = N(nt, "ShaderNodeTexNoise", Scale=7.0, Detail=10.0, Roughness=0.7)
    L(nt, tc.outputs["Object"], nz.inputs["Vector"])
    mr = N(nt, "ShaderNodeMapRange", **{"From Min": 0.42, "From Max": 0.62})
    L(nt, nz.outputs["Fac"], mr.inputs["Value"])
    mix = N(nt, "ShaderNodeMix", _data_type="RGBA")
    mix.inputs[6].default_value = (0.026, 0.019, 0.011, 1)     # thin smear
    mix.inputs[7].default_value = (0.009, 0.007, 0.005, 1)     # thick, wet
    L(nt, mr.outputs[0], mix.inputs[0])
    L(nt, mix.outputs[2], b.inputs["Base Color"])
    rough = math_node(nt, "ADD", math_node(nt, "MULTIPLY", mr.outputs[0], -0.45), 0.60)
    L(nt, rough, b.inputs["Roughness"])
    bump = N(nt, "ShaderNodeBump", Strength=0.6, Distance=0.003)
    L(nt, nz.outputs["Fac"], bump.inputs["Height"])
    L(nt, bump.outputs["Normal"], b.inputs["Normal"])
    return m


def tyre_material(name, kind, tread_img, side_img, v_tread, v_side, pitches_around):
    m, nt, b = principled(name, "TYRE", (0.026, 0.026, 0.027), 0.86, spec=0.35)
    uvn = N(nt, "ShaderNodeUVMap", _uv_map="UVMap")
    sep = N(nt, "ShaderNodeSeparateXYZ")
    L(nt, uvn.outputs["UV"], sep.inputs[0])
    u, v = sep.outputs[0], sep.outputs[1]
    # tread mapping: x = u * pitches_around / 16 (image holds 16 pitches), y = (v - vt0)/(vt1 - vt0)
    tx = math_node(nt, "MULTIPLY", u, pitches_around / 16.0)
    vt0, vt1 = v_tread
    ty = math_node(nt, "SUBTRACT", v, vt0)
    ty = math_node(nt, "DIVIDE", ty, vt1 - vt0)
    cmb = N(nt, "ShaderNodeCombineXYZ")
    L(nt, tx, cmb.inputs[0]); L(nt, ty, cmb.inputs[1])
    ti = N(nt, "ShaderNodeTexImage", _image=tread_img, _extension="REPEAT", _interpolation="Cubic")
    L(nt, cmb.outputs[0], ti.inputs[0])
    in_tread = math_node(nt, "MULTIPLY", math_node(nt, "GREATER_THAN", v, vt0), math_node(nt, "LESS_THAN", v, vt1))
    th = math_node(nt, "MULTIPLY", ti.outputs["Color"], in_tread)
    # sidewall: two bands (outer face v_side[0], inner face v_side[1]); text only on the outer one
    vs0, vs1 = v_side
    sy = math_node(nt, "SUBTRACT", v, vs0)
    sy = math_node(nt, "DIVIDE", sy, vs1 - vs0)
    cmb2 = N(nt, "ShaderNodeCombineXYZ")
    sx = math_node(nt, "MULTIPLY", u, 2.0)   # lettering repeats twice around
    L(nt, sx, cmb2.inputs[0]); L(nt, sy, cmb2.inputs[1])
    si = N(nt, "ShaderNodeTexImage", _image=side_img, _extension="CLIP", _interpolation="Cubic")
    L(nt, cmb2.outputs[0], si.inputs[0])
    in_side = math_node(nt, "MULTIPLY", math_node(nt, "GREATER_THAN", v, vs0), math_node(nt, "LESS_THAN", v, vs1))
    sh = math_node(nt, "MULTIPLY", si.outputs["Color"], in_side)
    hsum = math_node(nt, "ADD", math_node(nt, "MULTIPLY", th, 1.0), math_node(nt, "MULTIPLY", sh, 0.55))
    bump = N(nt, "ShaderNodeBump", Strength=1.0, Distance=0.004)
    L(nt, hsum, bump.inputs["Height"])
    L(nt, bump.outputs["Normal"], b.inputs["Normal"])
    # lettering slightly satin (moulded smooth), tread grooves darker/rougher; sidewall dust
    r = math_node(nt, "SUBTRACT", 0.86, math_node(nt, "MULTIPLY", sh, 0.18))
    dust = grime(nt, b, (0.026, 0.026, 0.027), 0.86, h0=0.7, amount=0.45, cavity=False, dust=(0.10, 0.093, 0.08))
    rr = math_node(nt, "ADD", r, math_node(nt, "MULTIPLY", dust, 0.1), clamp=True)
    L(nt, rr, b.inputs["Roughness"])
    return m


def build_library(livery="white", clay=False):
    """Create all materials. clay=True gives the A3 blockout read (paint/trim neutral greys)."""
    build_paint(livery, clay)
    # TRIM
    trim_rgb = (0.20, 0.20, 0.20) if clay else (0.036, 0.037, 0.038)
    m, nt, b = principled("plastic", "TRIM", trim_rgb, 0.62, spec=0.45)
    if not clay:
        micro_bump(nt, b, 900.0, 0.25, 0.0003)
        grime(nt, b, trim_rgb, 0.62, h0=1.4, amount=0.9, film=1.2, streak=0.3)
    principled("mask_gloss", "TRIM", (0.018, 0.018, 0.019) if not clay else (0.2, 0.2, 0.2), 0.09, coat=0.5)   # modern front: gloss-black mask (r6: albedo 0.010 -> 0.018, piano-black plastic is not a black hole; WORKING_VALUE)
    m, nt, b = principled("plastic_satin", "TRIM", (0.028, 0.029, 0.03) if not clay else (0.25, 0.25, 0.25), 0.36)
    principled("rubber", "TRIM", (0.018, 0.018, 0.018), 0.82, spec=0.3)
    # r8 (ADR 0061): wiper arms are matt black powder coat, not satin plastic (0.36 mirrored the sky on the arm). WORKING_VALUE
    # r8 (review r7 E7 / r8): mirror housings, arms, kerb and front mirror heads were satin plastic (0.36): from the
    # seat, at grazing angles, they mirrored the sky like chrome. Grained black ABS, roughness 0.58 (review: 0.5-0.6)
    m, nt, b = principled("mirror_plastic", "TRIM", (0.030, 0.031, 0.032) if not clay else (0.22, 0.22, 0.22), 0.58, spec=0.4)
    if not clay:
        micro_bump(nt, b, 900.0, 0.25, 0.0003)
    principled("wiper_black", "TRIM", (0.022, 0.022, 0.023) if not clay else (0.22, 0.22, 0.22), 0.60, spec=0.4)
    principled("gap", "TRIM", (0.004, 0.004, 0.004), 0.9, spec=0.2)
    ch_rgb = (0.022, 0.022, 0.023) if not clay else (0.16, 0.16, 0.16)
    m, nt, b = principled("chassis", "TRIM", ch_rgb, 0.45)
    if not clay:
        grime(nt, b, ch_rgb, 0.45, h0=1.2, amount=1.2, dust=(0.12, 0.11, 0.09), film=1.0)
    m, nt, b = principled("grille_mesh", "TRIM", (0.012, 0.012, 0.013), 0.55)
    if not clay:
        micro_bump(nt, b, 260.0, 0.6, 0.002, kind="voronoi")
    # graphite trim (grille frame, bumper 'road' frame, thin grille bars): painted plastic with a fine metallic
    # flake, satin - reads as a deliberate dark-silver accent, not chrome
    m, nt, b = principled("trim_graphite", "TRIM", (0.075, 0.077, 0.080) if not clay else (0.3, 0.3, 0.3), 0.34,
                          metal=0.55, coat=0.3)
    if not clay:
        micro_bump(nt, b, 700.0, 0.12, 0.0002)
        grime(nt, b, (0.075, 0.077, 0.080), 0.34, h0=1.9, amount=0.5)
    if clay:
        principled("grille_honey", "TRIM", (0.12, 0.12, 0.12), 0.6)
        principled("grille_honey_coarse", "TRIM", (0.12, 0.12, 0.12), 0.6)
    else:
        honey_material("grille_honey", 0.022)
        honey_material("grille_honey_coarse", 0.034, rgb=(0.026, 0.026, 0.027))
    # spray-suppression brush (EU Reg. 109/2011): dark fibres, very rough, streaky bump
    m, nt, b = principled("brush", "TRIM", (0.020, 0.020, 0.019), 0.92, spec=0.25)
    if not clay:
        micro_bump(nt, b, 1400.0, 0.9, 0.002)
        grime(nt, b, (0.020, 0.020, 0.019), 0.92, h0=1.2, amount=1.4, cavity=False, dust=(0.09, 0.08, 0.065))
    # plate
    m, nt, b = principled("plate", "TRIM", (0.8, 0.8, 0.8), 0.35)
    if not clay:
        img = make_plate_image()
        ti = N(nt, "ShaderNodeTexImage", _image=img)
        L(nt, ti.outputs["Color"], b.inputs["Base Color"])
    # METAL
    m, nt, b = principled("alu_brushed", "METAL", (0.90, 0.91, 0.92), 0.30, metal=1.0, aniso=0.6)
    if not clay:
        grime(nt, b, (0.90, 0.91, 0.92), 0.30, h0=1.1, amount=0.6, film=1.0, streak=0.4)
    alu_wheel(clay)
    principled("chrome", "METAL", (0.95, 0.95, 0.96), 0.06, metal=1.0)
    principled("satin_alu", "METAL", (0.80, 0.81, 0.82), 0.32, metal=1.0)
    m, nt, b = principled("steel", "METAL", (0.42, 0.42, 0.43), 0.45, metal=1.0)
    if not clay:
        grime(nt, b, (0.42, 0.42, 0.43), 0.45, h0=1.3, amount=0.8)
    principled("coupling_red", "TRIM", (0.40, 0.02, 0.02), 0.45)
    principled("coupling_yellow", "TRIM", (0.70, 0.45, 0.02), 0.45)
    principled("adblue_blue", "TRIM", (0.02, 0.10, 0.45), 0.4)
    grease(clay)
    m, nt, b = principled("checker", "METAL", (0.80, 0.80, 0.81), 0.38, metal=1.0)
    if not clay:
        # worn treads: boot grit and mud in the grooves, polished bar tops (roughness lower where it is high)
        grime(nt, b, (0.80, 0.80, 0.81), 0.38, h0=1.4, amount=1.6, dust=(0.11, 0.10, 0.085))
        img = checker_plate()
        tc = N(nt, "ShaderNodeUVMap", _uv_map="UVMap")
        mp = N(nt, "ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (10, 10, 10)
        L(nt, tc.outputs["UV"], mp.inputs["Vector"])
        ti = N(nt, "ShaderNodeTexImage", _image=img)
        L(nt, mp.outputs[0], ti.inputs[0])
        bump = N(nt, "ShaderNodeBump", Strength=1.0, Distance=0.003)
        L(nt, ti.outputs["Color"], bump.inputs["Height"])
        L(nt, bump.outputs["Normal"], b.inputs["Normal"])
    m, nt, b = principled("perforated", "METAL", (0.55, 0.55, 0.56), 0.40, metal=1.0)
    if not clay:
        img = louver_mask()
        tc = N(nt, "ShaderNodeUVMap", _uv_map="UVMap")
        mp = N(nt, "ShaderNodeMapping")
        mp.inputs["Scale"].default_value = (20, 20, 20)
        L(nt, tc.outputs["UV"], mp.inputs["Vector"])
        ti = N(nt, "ShaderNodeTexImage", _image=img)
        L(nt, mp.outputs[0], ti.inputs[0])
        mix = N(nt, "ShaderNodeMix", _data_type="RGBA")
        mix.inputs[6].default_value = (0.01, 0.01, 0.01, 1)
        mix.inputs[7].default_value = (0.55, 0.55, 0.56, 1)
        L(nt, ti.outputs["Color"], mix.inputs[0])
        L(nt, mix.outputs[2], b.inputs["Base Color"])
        L(nt, ti.outputs["Color"], b.inputs["Metallic"])
    # GLASS
    thin_glass("glass", "GLASS", (0.80, 0.86, 0.83))      # laminated windscreen/side glass, slight green
    thin_glass("glass_tint", "GLASS", (0.45, 0.50, 0.48))
    principled("mirror", "GLASS", (0.90, 0.90, 0.90), 0.02, metal=1.0)
    principled("frit", "GLASS", (0.008, 0.008, 0.008), 0.25, spec=0.6)
    principled("interior", "TRIM", (0.035, 0.034, 0.033), 0.7) if not clay else principled(
        "interior", "TRIM", (0.10, 0.10, 0.10), 0.7)
    principled("curtain", "TRIM", (0.06, 0.06, 0.065), 0.9)
    # LIGHTS
    thin_glass("lens_clear", "LIGHTS", (0.95, 0.95, 0.95), 0.0, ior=1.59)      # hard-coated polycarbonate
    principled("lamp_inner", "LIGHTS", (0.025, 0.025, 0.027), 0.35, spec=0.5)
    principled("reflector", "LIGHTS", (0.85, 0.86, 0.88), 0.08, metal=1.0)
    principled("dark_chrome", "LIGHTS", (0.20, 0.205, 0.21), 0.18, metal=1.0)
    # B2.2: headlamp housing / module shrouds = black glossy PC-ABS (moulded, not metallised): a dark chrome shroud
    # mirrored the overcast sky and turned the whole lamp cavity grey
    principled("lamp_housing", "LIGHTS", (0.010, 0.010, 0.011), 0.16, spec=0.45)
    drl = PARAMS["drl"]
    principled("led_drl", "LIGHTS", (0.9, 0.9, 0.9), 0.3, emit=(1.0, 0.97, 0.92), emit_s=14.0 * drl)
    principled("led_off", "LIGHTS", (0.75, 0.75, 0.76), 0.25, spec=0.6)
    # B2.1: amber LED diffuser strip (indicator light guide): orange when off too, satin, no transmission (bakes)
    principled("led_amber", "LIGHTS", (0.80, 0.30, 0.025), 0.30, spec=0.6)
    principled("lens_amber", "LIGHTS", (0.95, 0.42, 0.04), 0.05, transm=0.85, ior=1.49)
    principled("lens_red", "LIGHTS", (0.55, 0.02, 0.015), 0.05, transm=0.85, ior=1.49)
    # r4: smoked projector lens, opaque in the bake (transmission baked the env as a blue cast in the game atlas)
    m, nt, b = principled("projector", "LIGHTS", (0.045, 0.045, 0.048), 0.07, spec=0.35)   # B2.2: AR-coated, less sky
    # B2.2 refraction fake (the game bakes the lens opaque into the Lights atlas): a real LED projector lens shows
    # the inverted image of its chrome reflector - bright lower half, the sharp shield cut-off line just under the
    # middle, a dark upper half with a faint blue cast of the coated optics. Gradient over the lens' own height
    # (Generated z per lens object), baked into the albedo; low roughness keeps the crown highlight on top.
    if not clay:
        tc = N(nt, "ShaderNodeTexCoord")
        sp = N(nt, "ShaderNodeSeparateXYZ")
        cr = N(nt, "ShaderNodeValToRGB")
        L(nt, tc.outputs["Generated"], sp.inputs[0])
        L(nt, sp.outputs["Z"], cr.inputs["Fac"])
        el = cr.color_ramp.elements
        stops = [(0.00, (0.20, 0.205, 0.215)), (0.14, (0.46, 0.47, 0.49)), (0.40, (0.36, 0.37, 0.39)),
                 (0.47, (0.70, 0.71, 0.73)), (0.50, (0.025, 0.025, 0.030)), (0.85, (0.035, 0.040, 0.055)),
                 (1.00, (0.018, 0.018, 0.022))]
        el[0].position, el[0].color = stops[0][0], (*stops[0][1], 1)
        el[1].position, el[1].color = stops[-1][0], (*stops[-1][1], 1)
        for p, c in stops[1:-1]:
            e = el.new(p)
            e.color = (*c, 1)
        L(nt, cr.outputs["Color"], b.inputs["Base Color"])
    if clay:
        for k in ("lens_amber", "lens_red", "projector"):
            b = STATE["mats"][k].node_tree.nodes["Principled BSDF"]
            b.inputs["Transmission Weight"].default_value = 0.0
            b.inputs["Base Color"].default_value = (0.75, 0.76, 0.78, 1) if k == "lens_clear" else b.inputs[
                "Base Color"].default_value
        STATE["mats"]["led_drl"].node_tree.nodes["Principled BSDF"].inputs["Emission Strength"].default_value = 0
    # figure (scale reference)
    principled("figure", "-", (0.33, 0.35, 0.38), 0.7)
    return STATE["mats"]
