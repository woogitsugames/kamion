"""PBR materials for the A5 cab interior (Cycles renders; maps are the same PNGs the game will use).

Albedo values are linear and kept in physically plausible ranges for automotive interiors
(black/anthracite plastics 0.03-0.06, light headliner 0.25-0.35, white paint ~0.7).
WORKING_VALUE: there is no measured albedo table yet (docs/06 §3) — these are class-typical.
"""
import math
import os

import bpy

from geom import STATE

TEX = None  # set by build_interior: absolute path of art-source/truck/interior/textures
_IMG = {}
PARAMS = {}  # material name -> authoring parameters (A6: consolidation into game material slots)


def img(fname, noncolor=True):
    key = (fname, noncolor)
    if key not in _IMG:
        im = bpy.data.images.load(os.path.join(TEX, fname), check_existing=True)
        im.colorspace_settings.name = "Non-Color" if noncolor else "sRGB"
        _IMG[key] = im
    return _IMG[key]


def _new(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    STATE["mats"][name] = m
    return m, nt, out


def _uv(nt, tile_m, uvmap="UVMap", rot=0.0):
    tc = nt.nodes.new("ShaderNodeUVMap")
    tc.uv_map = uvmap
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0 / tile_m, 1.0 / tile_m, 1.0)
    mp.inputs["Rotation"].default_value = (0, 0, rot)
    nt.links.new(tc.outputs["UV"], mp.inputs["Vector"])
    return mp.outputs["Vector"]


def _tex(nt, vec, fname, noncolor=True):
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img(fname, noncolor)
    t.interpolation = "Cubic" if False else "Linear"
    nt.links.new(vec, t.inputs["Vector"])
    return t


def _math(nt, op, a, b=None, clamp=False):
    n = nt.nodes.new("ShaderNodeMath")
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b)):
        if v is None:
            continue
        if isinstance(v, (int, float)):
            n.inputs[i].default_value = v
        else:
            nt.links.new(v, n.inputs[i])
    return n.outputs[0]


def _mix_rgb(nt, fac, a, b, blend="MIX"):
    n = nt.nodes.new("ShaderNodeMix")
    n.data_type = "RGBA"
    n.blend_type = blend
    for sock, v in ((n.inputs[0], fac), (n.inputs[6], a), (n.inputs[7], b)):
        if isinstance(v, (int, float)):
            sock.default_value = v
        elif isinstance(v, tuple):
            sock.default_value = (*v[:3], 1.0) if len(v) >= 3 else v
        else:
            nt.links.new(v, sock)
    return n.outputs[2]


def _attr(nt, name):
    a = nt.nodes.new("ShaderNodeAttribute")
    a.attribute_name = name
    a.attribute_type = "GEOMETRY"
    return a.outputs["Fac"]


def pbr(name, tint, tset, tile_m, rough_mul=1.0, rough_add=0.0, nstr=1.0, metal=0.0, wear=None,
        dust=None, spec=0.5, coat=0.0, sheen=0.0, uv_rot=0.0, perforate=None):
    """Tiled detail-set material. wear = (rough_target, tint_mul) driven by the 'wear' colour attribute.
    dust = (amount, rgb) accumulated in cavities (Cycles AO node; baked to the AO atlas for the game)."""
    m, nt, out = _new(name)
    PARAMS[name] = dict(kind="pbr", tint=tuple(tint), tset=tset, tile=tile_m, rough_mul=rough_mul, rough_add=rough_add,
                        nstr=nstr, metal=metal, perforate=bool(perforate), sheen=sheen)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    vec = _uv(nt, tile_m, rot=uv_rot)
    tv = _tex(nt, vec, f"{tset}_var.png")
    tn = _tex(nt, vec, f"{tset}_nrm.png")
    to = _tex(nt, vec, f"{tset}_orm.png")
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(to.outputs["Color"], sep.inputs[0])
    # albedo = tint * (0.7 + 0.6 var) * mix(1, microAO, .6)
    k = _math(nt, "MULTIPLY_ADD", tv.outputs["Color"], 0.6)
    nt.nodes[k.node.name].inputs[2].default_value = 0.7
    ao = _math(nt, "MULTIPLY_ADD", sep.outputs[0], 0.6)
    ao.node.inputs[2].default_value = 0.4
    kk = _math(nt, "MULTIPLY", k, ao)
    base = _mix_rgb(nt, 1.0, tint, kk, "MULTIPLY")
    rough = _math(nt, "MULTIPLY_ADD", sep.outputs[1], rough_mul)
    rough.node.inputs[2].default_value = rough_add
    if perforate:  # perforated leather centre panels: darker holes, less specular
        pv = _uv(nt, perforate)
        pt = _tex(nt, pv, "perforation_mask.png")
        base = _mix_rgb(nt, 1.0, base, pt.outputs["Color"], "MULTIPLY")
    if wear:
        w = _attr(nt, "wear")
        rough = _mix_rgb(nt, w, rough, (wear[0], wear[0], wear[0]))
        base = _mix_rgb(nt, w, base, _mix_rgb(nt, 1.0, base, (wear[1], wear[1], wear[1]), "MULTIPLY"))
    if dust:
        aon = nt.nodes.new("ShaderNodeAmbientOcclusion")
        aon.inputs["Distance"].default_value = dust[2] if len(dust) > 2 else 0.06
        aon.samples = 8
        inv = _math(nt, "SUBTRACT", 1.0, aon.outputs["AO"])
        fac = _math(nt, "MULTIPLY", inv, dust[0], clamp=True)
        base = _mix_rgb(nt, fac, base, dust[1])
        rough = _mix_rgb(nt, fac, rough, (0.95, 0.95, 0.95))
    nt.links.new(base, b.inputs["Base Color"])
    nt.links.new(rough, b.inputs["Roughness"])
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.uv_map = "UVMap"
    nm.inputs["Strength"].default_value = nstr
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], b.inputs["Normal"])
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    if sheen:
        b.inputs["Sheen Weight"].default_value = sheen
        b.inputs["Sheen Roughness"].default_value = 0.4
    m.diffuse_color = (*tint, 1)
    return m


def simple(name, rgb, rough=0.5, metal=0.0, spec=0.5, coat=0.0, coat_rough=0.05, emit=None, alpha=1.0):
    m, nt, out = _new(name)
    PARAMS[name] = dict(kind="simple", tint=tuple(rgb), rough=rough, metal=metal)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    b.inputs["Specular IOR Level"].default_value = spec
    b.inputs["Coat Weight"].default_value = coat
    b.inputs["Coat Roughness"].default_value = coat_rough
    if emit:
        b.inputs["Emission Color"].default_value = (*emit[0], 1)
        b.inputs["Emission Strength"].default_value = emit[1]
    m.diffuse_color = (*rgb, 1)
    return m


def paint(name, rgb, rough=0.28):
    """Exterior cab paint: base + clear coat, a little orange-peel via fine noise bump."""
    m, nt, out = _new(name)
    PARAMS[name] = dict(kind="simple", tint=tuple(rgb), rough=rough, metal=0.0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Coat Weight"].default_value = 0.6
    b.inputs["Coat Roughness"].default_value = 0.08
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 400
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.02
    nt.links.new(nz.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Coat Normal"])
    m.diffuse_color = (*rgb, 1)
    return m


def display(name, fname, strength=1.6, rough=0.08, fingerprints=0.0):
    """Emissive display under cover glass (anti-glare: slightly rough coat)."""
    m, nt, out = _new(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeUVMap")
    tc.uv_map = "UVMap"
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img(fname, noncolor=False)
    t.extension = "EXTEND"
    nt.links.new(tc.outputs["UV"], t.inputs["Vector"])
    b.inputs["Base Color"].default_value = (0.004, 0.004, 0.005, 1)
    nt.links.new(t.outputs["Color"], b.inputs["Emission Color"])
    b.inputs["Emission Strength"].default_value = strength
    r = rough
    if fingerprints:
        g = _tex(nt, _uv(nt, 0.35), "grime_mask.png")
        r = _math(nt, "MULTIPLY_ADD", g.outputs["Color"], fingerprints)
        r.node.inputs[2].default_value = rough
        nt.links.new(r, b.inputs["Roughness"])
    else:
        b.inputs["Roughness"].default_value = rough
    b.inputs["Specular IOR Level"].default_value = 0.5
    m.diffuse_color = (0.02, 0.02, 0.02, 1)
    return m


def mirror_rt(name, fname, strength=0.7, tint=(1.0, 1.0, 1.0)):
    """Render-only stand-in for a mirror RenderTexture (REVIEW-2026-11-09-r2 A6 #4): the quad shows a blurred 'probe'
    image (make_textures.mirror_placeholders) as emission, plus the weak front-surface reflection of the cover glass.
    The image has the cab flank on its inner edge at u = 1; quads on the right-hand side (world x > 0) read u mirrored.
    Strength/tint are Value/RGB nodes named 'rt_strength'/'rt_tint' so the lighting setup can match the sky level
    (mirror reflectance ~0.55 x sky radiance). In Unity each MIRROR_* quad shows its own camera RT instead."""
    m, nt, out = _new(name)
    PARAMS[name] = dict(kind="simple", tint=(0.85, 0.86, 0.87), rough=0.02, metal=1.0)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeUVMap")
    tc.uv_map = "UVMap"
    su = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["UV"], su.inputs[0])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    sp = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(geo.outputs["Position"], sp.inputs[0])
    right = _math(nt, "GREATER_THAN", sp.outputs["X"], 0.0)
    one_m2u = _math(nt, "MULTIPLY_ADD", su.outputs["X"], -2.0)
    one_m2u.node.inputs[2].default_value = 1.0
    u2 = _math(nt, "MULTIPLY_ADD", right, one_m2u)
    nt.links.new(su.outputs["X"], u2.node.inputs[2])
    cb = nt.nodes.new("ShaderNodeCombineXYZ")
    nt.links.new(u2, cb.inputs[0])
    nt.links.new(su.outputs["Y"], cb.inputs[1])
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img(fname, noncolor=False)
    t.extension = "EXTEND"
    nt.links.new(cb.outputs[0], t.inputs["Vector"])
    rgb = nt.nodes.new("ShaderNodeRGB")
    rgb.name = "rt_tint"
    rgb.outputs[0].default_value = (*tint, 1)
    st = nt.nodes.new("ShaderNodeValue")
    st.name = "rt_strength"
    st.outputs[0].default_value = strength
    col = _mix_rgb(nt, 1.0, t.outputs["Color"], rgb.outputs[0], "MULTIPLY")
    nt.links.new(col, b.inputs["Emission Color"])
    nt.links.new(st.outputs[0], b.inputs["Emission Strength"])
    b.inputs["Base Color"].default_value = (0.01, 0.01, 0.01, 1)
    b.inputs["Roughness"].default_value = 0.03
    b.inputs["Specular IOR Level"].default_value = 0.5
    m.diffuse_color = (0.5, 0.52, 0.55, 1)
    return m


def set_mirror_level(strength, tint=(1.0, 1.0, 1.0)):
    """Match the mirror placeholders to the current sky (see mirror_rt)."""
    for m in bpy.data.materials:
        if m.use_nodes and "rt_strength" in m.node_tree.nodes:
            m.node_tree.nodes["rt_strength"].outputs[0].default_value = strength
            m.node_tree.nodes["rt_tint"].outputs[0].default_value = (*tint, 1)


def decal(name, fname, rgb, rough=0.6, alpha_from="alpha", tile_u=None, emit=None):
    """Alpha-tested decal (stitching, printed labels/icons). UVs come from the strip / quad itself."""
    m, nt, out = _new(name)
    PARAMS[name] = dict(kind="decal", tint=tuple(rgb), rough=rough, tex=fname)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeUVMap")
    tc.uv_map = "UVMap"
    t = nt.nodes.new("ShaderNodeTexImage")
    t.image = img(fname, noncolor=(alpha_from != "alpha"))
    nt.links.new(tc.outputs["UV"], t.inputs["Vector"])
    if alpha_from == "alpha":
        col = _mix_rgb(nt, 1.0, rgb, t.outputs["Color"], "MULTIPLY")
        k = _math(nt, "MULTIPLY", t.outputs["Alpha"], 1.0)
        nt.links.new(col, b.inputs["Base Color"])
        nt.links.new(k, b.inputs["Alpha"])
    else:  # grayscale mask -> alpha, flat colour
        b.inputs["Base Color"].default_value = (*rgb, 1)
        nt.links.new(t.outputs["Color"], b.inputs["Alpha"])
        if emit:
            b.inputs["Emission Color"].default_value = (*emit[0], 1)
            nt.links.new(_math(nt, "MULTIPLY", t.outputs["Color"], emit[1]), b.inputs["Emission Strength"])
    b.inputs["Roughness"].default_value = rough
    m.blend_method = "HASHED"
    m.diffuse_color = (*rgb, 1)
    return m


def thin_glass(name, tint=(0.88, 0.92, 0.90), grime=0.0, sunstrip=None, rough=0.0, film=(0.42, 0.40, 0.36), frit=None):
    """Architectural thin glass (single sheet): shadow rays pass tinted, camera rays see Fresnel reflection.
    sunstrip = (z0, z1, tint) world-Z band at the top of the windscreen.
    grime = amount of dusty film from the grime mask (roughness + slight diffuse)."""
    m, nt, out = _new(name)
    lp = nt.nodes.new("ShaderNodeLightPath")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    gl.inputs["Roughness"].default_value = rough
    fr = nt.nodes.new("ShaderNodeFresnel")
    # Fresnel on a back face uses 1/IOR (-> total internal reflection beyond ~41 deg, a white ellipse on a
    # single-sheet windscreen). Feed 1/1.52 on back faces so both sides behave like an air->glass interface.
    geo_b = nt.nodes.new("ShaderNodeNewGeometry")
    ior = _math(nt, "MULTIPLY_ADD", geo_b.outputs["Backfacing"], 1.0 / 1.52 - 1.52)
    ior.node.inputs[2].default_value = 1.52
    nt.links.new(ior, fr.inputs["IOR"])
    tint_sock = tint
    if sunstrip:
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs[1].default_value = sunstrip[0]
        mr.inputs[2].default_value = sunstrip[1]
        nt.links.new(sep.outputs["Z"], mr.inputs[0])
        sm = nt.nodes.new("ShaderNodeFloatCurve") if False else None
        tint_sock = _mix_rgb(nt, mr.outputs[0], tint, sunstrip[2])
    if isinstance(tint_sock, tuple):
        tr.inputs["Color"].default_value = (*tint_sock, 1)
    else:
        nt.links.new(tint_sock, tr.inputs["Color"])
    mix = nt.nodes.new("ShaderNodeMixShader")
    # A6.1: a single sheet reflects at both faces, R = 2F / (1 + F) (~8 % near normal incidence, was 4 %), so the
    # dash shows faintly in the windscreen against darker parts of the view (critic r2 #7)
    r2 = _math(nt, "DIVIDE", _math(nt, "MULTIPLY", fr.outputs[0], 2.0), _math(nt, "ADD", fr.outputs[0], 1.0))
    nt.links.new(r2, mix.inputs[0])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(gl.outputs[0], mix.inputs[2])
    shader = mix.outputs[0]
    if grime:
        g = _tex(nt, _uv(nt, 1.1), "grime_mask.png")
        f = _math(nt, "MULTIPLY", _math(nt, "POWER", g.outputs["Color"], 2.2), grime, clamp=True)
        dif = nt.nodes.new("ShaderNodeBsdfDiffuse")
        dif.inputs["Color"].default_value = (*film, 1)
        m2 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(f, m2.inputs[0])
        nt.links.new(shader, m2.inputs[1])
        nt.links.new(dif.outputs[0], m2.inputs[2])
        shader = m2.outputs[0]
    sh = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], sh.inputs[0])
    nt.links.new(shader, sh.inputs[1])
    nt.links.new(tr.outputs[0], sh.inputs[2])
    final = sh.outputs[0]
    if frit:  # black ceramic frit border (opaque): bottom z < frit[0], top z > frit[1], sides |x| > frit[2]
        geo = nt.nodes.new("ShaderNodeNewGeometry")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(geo.outputs["Position"], sep.inputs[0])
        lo = _math(nt, "LESS_THAN", sep.outputs["Z"], frit[0])
        hi = _math(nt, "GREATER_THAN", sep.outputs["Z"], frit[1])
        ax = _math(nt, "ABSOLUTE", sep.outputs["X"])
        sd = _math(nt, "GREATER_THAN", ax, frit[2])
        f = _math(nt, "MAXIMUM", _math(nt, "MAXIMUM", lo, hi), sd)
        fb = nt.nodes.new("ShaderNodeBsdfPrincipled")
        fb.inputs["Base Color"].default_value = (0.012, 0.012, 0.012, 1)
        fb.inputs["Roughness"].default_value = 0.35
        m3 = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(f, m3.inputs[0])
        nt.links.new(final, m3.inputs[1])
        nt.links.new(fb.outputs[0], m3.inputs[2])
        final = m3.outputs[0]
    nt.links.new(final, out.inputs["Surface"])
    m.blend_method = "BLEND"
    m.diffuse_color = (0.1, 0.12, 0.12, 0.3)
    return m


def asphalt(name):
    """Ground for the backdrop: worn asphalt with patches (procedural, render-only backdrop)."""
    m, nt, out = _new(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.08
    n1.inputs["Detail"].default_value = 6
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 60
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.35
    ramp.color_ramp.elements[0].color = (0.075, 0.075, 0.072, 1)
    ramp.color_ramp.elements[1].position = 0.7
    ramp.color_ramp.elements[1].color = (0.14, 0.135, 0.125, 1)
    nt.links.new(n1.outputs["Fac"], ramp.inputs[0])
    c = _mix_rgb(nt, 0.25, ramp.outputs["Color"], n2.outputs["Color"], "OVERLAY")
    nt.links.new(c, b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.25
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    m.diffuse_color = (0.1, 0.1, 0.1, 1)
    return m


def grass(name):
    m, nt, out = _new(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.05
    n1.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.045, 0.055, 0.025, 1)
    ramp.color_ramp.elements[1].color = (0.11, 0.11, 0.055, 1)
    nt.links.new(n1.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    m.diffuse_color = (0.07, 0.08, 0.04, 1)
    return m


def line_paint(name):
    """Worn road paint: patchy, partly showing the asphalt (render backdrop only)."""
    m, nt, out = _new(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    tc = nt.nodes.new("ShaderNodeTexCoord")
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 1.6
    n1.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = 0.38
    ramp.color_ramp.elements[0].color = (0.11, 0.11, 0.105, 1)
    ramp.color_ramp.elements[1].position = 0.52
    ramp.color_ramp.elements[1].color = (0.42, 0.42, 0.40, 1)
    nt.links.new(n1.outputs["Fac"], ramp.inputs[0])
    nt.links.new(ramp.outputs["Color"], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.8
    m.diffuse_color = (0.4, 0.4, 0.4, 1)
    return m


def blind(name, rgb=(0.16, 0.16, 0.165), trans=0.35):
    """Roller-blind fabric: diffuse + some translucency (lets light glow through)."""
    m, nt, out = _new(name)
    vec = _uv(nt, 0.04)
    tn = _tex(nt, vec, "fabric_nrm.png")
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nm.uv_map = "UVMap"
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    d = nt.nodes.new("ShaderNodeBsdfDiffuse")
    d.inputs["Color"].default_value = (*rgb, 1)
    t = nt.nodes.new("ShaderNodeBsdfTranslucent")
    t.inputs["Color"].default_value = (*rgb, 1)
    nt.links.new(nm.outputs["Normal"], d.inputs["Normal"])
    mx = nt.nodes.new("ShaderNodeMixShader")
    mx.inputs[0].default_value = trans
    nt.links.new(d.outputs[0], mx.inputs[1])
    nt.links.new(t.outputs[0], mx.inputs[2])
    nt.links.new(mx.outputs[0], out.inputs["Surface"])
    m.diffuse_color = (*rgb, 1)
    return m
