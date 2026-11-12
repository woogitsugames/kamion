"""Track A6 — neutral, photographic-ish render backdrop for the cab-interior control renders (critic #15).

Render-only, NOT a game asset. Own work (no downloaded HDRI/photos): a plausible Podlasie logistics yard —
worn asphalt with patches, cracks and stains, a concrete apron with slab joints in front of a clad logistics hall with
dock doors and shelters, lamp masts with LED heads, parked curtain-side semi-trailers, a kerb and grass verge, and a
mixed forest edge built from alpha tree cards (Scots pine, spruce, birch, alder; make_textures.tree_cards) in three
staggered rows with aerial haze. Frame as build_interior: Z up, truck faces +Y, origin under the front axle.
"""
import math
import random


import geom as G
import materials as M
from geom import V, box, box_mm, cyl, rod


def _nodes(name):
    m, nt, out = M._new(name)
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    return m, nt, out, b


def _haze(nt, shader_col, strength=1.0):
    """Aerial perspective: mix the colour towards the horizon haze with camera distance (cheap, render-only)."""
    cam = nt.nodes.new("ShaderNodeCameraData")
    k = M._math(nt, "MULTIPLY", cam.outputs["View Distance"], 1.0 / 900.0 * strength)
    f = M._math(nt, "MINIMUM", M._math(nt, "SUBTRACT", 1.0, M._math(nt, "EXPONENT", M._math(nt, "MULTIPLY", k, -1.0))), 0.85)
    return M._mix_rgb(nt, f, shader_col, (0.40, 0.43, 0.46))


def materials():
    # asphalt: two-tone patch cells, crack network, oil stains, polished wheel paths, fine aggregate bump
    m, nt, out, b = _nodes("yard_asphalt")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    vor = nt.nodes.new("ShaderNodeTexVoronoi")
    vor.inputs["Scale"].default_value = 0.09
    nt.links.new(tc.outputs["Object"], vor.inputs["Vector"])
    cr = nt.nodes.new("ShaderNodeTexVoronoi")
    cr.feature = "DISTANCE_TO_EDGE"
    cr.inputs["Scale"].default_value = 0.22
    nz_w = nt.nodes.new("ShaderNodeTexNoise")
    nz_w.inputs["Scale"].default_value = 0.6
    nt.links.new(tc.outputs["Object"], nz_w.inputs["Vector"])
    warp = M._mix_rgb(nt, 0.35, tc.outputs["Object"], nz_w.outputs["Color"], "LINEAR_LIGHT")
    nt.links.new(warp, cr.inputs["Vector"])
    n1 = nt.nodes.new("ShaderNodeTexNoise")
    n1.inputs["Scale"].default_value = 0.25
    n1.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], n1.inputs["Vector"])
    n2 = nt.nodes.new("ShaderNodeTexNoise")
    n2.inputs["Scale"].default_value = 90
    nt.links.new(tc.outputs["Object"], n2.inputs["Vector"])
    patch = M._math(nt, "GREATER_THAN", vor.outputs["Color"], 0.72)  # Color output -> uses R
    base = M._mix_rgb(nt, patch, (0.105, 0.104, 0.100), (0.060, 0.060, 0.058))
    base = M._mix_rgb(nt, M._math(nt, "MULTIPLY", n1.outputs["Fac"], 0.5), base, (0.14, 0.135, 0.125), "MIX")
    stain = M._math(nt, "GREATER_THAN", n1.outputs["Fac"], 0.66)
    base = M._mix_rgb(nt, M._math(nt, "MULTIPLY", stain, 0.6), base, (0.035, 0.034, 0.033))
    crk_mask = M._math(nt, "GREATER_THAN", n1.outputs["Fac"], 0.55)    # cracks only in some zones
    crack = M._math(nt, "MULTIPLY", M._math(nt, "LESS_THAN", cr.outputs["Distance"], 0.0045), crk_mask)
    base = M._mix_rgb(nt, M._math(nt, "MULTIPLY", crack, 0.7), base, (0.035, 0.035, 0.034))
    base = M._mix_rgb(nt, 0.18, base, n2.outputs["Color"], "OVERLAY")
    nt.links.new(_haze(nt, base, 0.6), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.88
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.3
    nt.links.new(n2.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # concrete apron: 6 x 6 m slabs with dark joints and tonal variation per slab
    m, nt, out, b = _nodes("yard_concrete")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    jx = M._math(nt, "LESS_THAN", M._math(nt, "FRACT", M._math(nt, "MULTIPLY", sep.outputs["X"], 1 / 6.0)), 0.004)
    jy = M._math(nt, "LESS_THAN", M._math(nt, "FRACT", M._math(nt, "MULTIPLY", sep.outputs["Y"], 1 / 6.0)), 0.004)
    nz = nt.nodes.new("ShaderNodeTexNoise")
    nz.inputs["Scale"].default_value = 0.4
    nt.links.new(tc.outputs["Object"], nz.inputs["Vector"])
    c = M._mix_rgb(nt, M._math(nt, "MULTIPLY", nz.outputs["Fac"], 0.7), (0.30, 0.295, 0.28), (0.20, 0.195, 0.185))
    c = M._mix_rgb(nt, M._math(nt, "MAXIMUM", jx, jy), c, (0.06, 0.06, 0.058))
    nt.links.new(_haze(nt, c, 0.6), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.85
    # hall cladding: trapezoidal ribs (bump), vertical rain streaks, darker bottom
    m, nt, out, b = _nodes("yard_cladding")
    tc = nt.nodes.new("ShaderNodeTexCoord")
    wv = nt.nodes.new("ShaderNodeTexWave")
    wv.wave_type = "BANDS"
    wv.bands_direction = "X"
    wv.inputs["Scale"].default_value = 3.0
    nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
    st = nt.nodes.new("ShaderNodeTexNoise")
    st.inputs["Scale"].default_value = 3.0
    mp = nt.nodes.new("ShaderNodeMapping")
    mp.inputs["Scale"].default_value = (1.0, 1.0, 0.08)
    nt.links.new(tc.outputs["Object"], mp.inputs["Vector"])
    nt.links.new(mp.outputs[0], st.inputs["Vector"])
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    low = M._math(nt, "SUBTRACT", 1.0, M._math(nt, "MINIMUM", M._math(nt, "MULTIPLY", sep.outputs["Z"], 0.25), 1.0))
    c = M._mix_rgb(nt, M._math(nt, "MULTIPLY", st.outputs["Fac"], 0.35), (0.33, 0.34, 0.34), (0.24, 0.25, 0.25))
    c = M._mix_rgb(nt, M._math(nt, "MULTIPLY", low, 0.5), c, (0.24, 0.235, 0.22))
    nt.links.new(_haze(nt, c, 0.8), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.55
    b.inputs["Metallic"].default_value = 0.3
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.6
    nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    # tree cards: alpha atlas, slight per-card tint, haze
    m, nt, out = M._new("yard_tree")
    tc = nt.nodes.new("ShaderNodeUVMap")
    tc.uv_map = "UVMap"
    tx = nt.nodes.new("ShaderNodeTexImage")
    tx.image = M.img("tree_cards.png", noncolor=False)
    tx.interpolation = "Closest" if False else "Linear"
    nt.links.new(tc.outputs["UV"], tx.inputs["Vector"])
    b = nt.nodes.new("ShaderNodeBsdfPrincipled")
    col = M._mix_rgb(nt, 1.0, tx.outputs["Color"], (0.55, 0.58, 0.55), "MULTIPLY")
    nt.links.new(_haze(nt, col, 0.55), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.9
    nt.links.new(M._math(nt, "GREATER_THAN", tx.outputs["Alpha"], 0.5), b.inputs["Alpha"])  # hard cut-out
    nt.links.new(b.outputs[0], out.inputs["Surface"])
    m.blend_method = "HASHED"
    try:
        m.surface_render_method = "BLENDED"
        m.use_backface_culling = False
        m.use_transparent_shadow = True
    except AttributeError:
        pass
    # distant forest mass behind the cards
    m, nt, out, b = _nodes("yard_forest_mass")
    nt.links.new(_haze(nt, (0.030, 0.040, 0.032), 0.55), b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.95
    M.simple("yard_dark", (0.03, 0.03, 0.03), rough=0.7)
    M.simple("yard_door", (0.34, 0.35, 0.35), rough=0.5)
    M.simple("yard_kerb", (0.32, 0.31, 0.29), rough=0.9)
    M.simple("yard_curtain", (0.36, 0.38, 0.40), rough=0.7)
    M.simple("yard_curtain2", (0.30, 0.22, 0.17), rough=0.7)
    M.simple("yard_galv", (0.45, 0.46, 0.46), rough=0.45, metal=0.8)
    M.simple("yard_led", (0.15, 0.15, 0.15), rough=0.3)


def card(bm, uvl, pos, h, idx, face_to=V(0, 0, 0)):
    """Vertical alpha card of height h facing the origin, appended to bm; idx = column of the 8-tree atlas."""
    w = h * 0.5 * (0.8 + 0.4 * ((pos.x * 12.9898 + pos.y * 78.233) % 1.0))
    d = (face_to - pos)
    d.z = 0
    d.normalize()
    side = V(-d.y, d.x, 0)
    vs = [bm.verts.new(pos + side * (-w / 2)), bm.verts.new(pos + side * (w / 2)),
          bm.verts.new(pos + side * (w / 2) + V(0, 0, h)), bm.verts.new(pos + side * (-w / 2) + V(0, 0, h))]
    f = bm.faces.new(vs)
    u0, u1 = idx / 8 + 0.002, (idx + 1) / 8 - 0.002
    for lp, t in zip(f.loops, ((u0, 0), (u1, 0), (u1, 1), (u0, 1))):
        lp[uvl].uv = t


def trailer(name, x, y, rot, curtain="yard_curtain"):
    """Parked 13.6 m curtain-side semi-trailer (box body, straps, under-run bar, 3 axles, landing legs)."""
    from mathutils import Matrix
    objs = []
    objs.append(box(name + "_body", (0, 0, 2.6), (2.55, 13.6, 2.85), curtain, bev=0.03))
    objs.append(box(name + "_roofrail", (0, 0, 4.03), (2.56, 13.62, 0.06), "yard_galv"))
    objs.append(box(name + "_floor", (0, 0, 1.12), (2.55, 13.6, 0.14), "yard_dark"))
    for k in range(-15, 16):
        for s in (-1, 1):
            objs.append(box(f"{name}_strap_{k}_{s}", (s * 1.278, k * 0.44, 2.6), (0.006, 0.045, 2.8), "yard_dark"))
    for k in range(3):
        for s in (-1, 1):
            objs.append(cyl(f"{name}_w{k}{s}", (s * 0.98, -4.6 + k * 1.31, 0.48), 0.48, 0.38, "yard_dark", axis="X", seg=20))
    for s in (-1, 1):
        objs.append(box(f"{name}_leg{s}", (s * 0.9, 3.4, 0.55), (0.12, 0.12, 1.1), "yard_galv"))
    objs.append(box(name + "_urb", (0, -6.85, 0.62), (2.3, 0.12, 0.14), "yard_galv"))
    mtx = Matrix.Translation((x, y, 0)) @ Matrix.Rotation(rot, 4, "Z")
    for o in objs:
        o.matrix_world = mtx @ o.matrix_world


def build(group):
    group("backdrop")
    materials()
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=90)
    G.finish("ground_asphalt", bm, "yard_asphalt", smooth=False)
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=1500)
    gr = G.finish("ground_grass", bm, "grass", smooth=False)
    gr.location.z = -0.03
    # kerb along the yard edge (front) + concrete apron in front of the hall
    box_mm("kerb_front", -90, 90, 89.8, 90.1, -0.02, 0.12, "yard_kerb")
    box_mm("apron", -126, -30, 58.0, 70.0, 0.0, 0.006, "yard_concrete")
    # worn bay lines: slightly irregular spacing/width, some missing segments
    rnd = random.Random(11)
    for k in range(-4, 5):
        x = k * 4.05 + 2.0 + rnd.uniform(-0.06, 0.06)
        for seg in range(4):
            if rnd.random() < 0.12:
                continue
            y0 = 6.0 + seg * 4.0
            box_mm(f"bay_line_{k}_{seg}", x - 0.055, x + 0.055, y0, y0 + 4.0 - rnd.uniform(0, 0.4), 0.0, 0.003, "line_paint")
    box_mm("bay_line_front", -18, 18, 22.0, 22.12, 0.0, 0.003, "line_paint")
    # logistics hall: clad walls, dark plinth, roof flashing, 6 dock doors with black shelters
    box_mm("hall", -126, -30, 70, 118, 0, 12.0, "yard_cladding", bev=0.05)
    box_mm("hall_plinth", -126.05, -29.95, 69.95, 118.05, 0, 0.9, "yard_kerb")
    box_mm("hall_flashing", -126.2, -29.8, 69.8, 118.2, 11.8, 12.25, "yard_galv")
    for k in range(6):
        x0 = -118 + k * 14
        box_mm(f"dock_door_{k}", x0, x0 + 3.0, 69.92, 69.96, 1.2, 4.2, "yard_door")
        box_mm(f"dock_shelter_{k}", x0 - 0.45, x0 + 3.45, 69.5, 69.95, 1.0, 4.6, "yard_dark")
        box_mm(f"dock_bumper_{k}", x0 + 0.2, x0 + 2.8, 69.6, 69.92, 1.0, 1.2, "yard_dark")
    # lamp masts with LED heads and arms
    for k, (x, y) in enumerate(((-34.0, 40.0), (-12.0, 46.0), (26.0, 44.0), (44.0, 30.0), (60.0, 60.0))):
        rod(f"mast_{k}", (x, y, 0), (x, y, 12.0), 0.11, "yard_galv", seg=10, r1=0.07)
        rod(f"mast_arm_{k}", (x, y, 11.8), (x + 1.2, y - 0.6, 12.0), 0.04, "yard_galv", seg=6)
        box(f"mast_head_{k}", (x + 1.4, y - 0.7, 11.95), (0.7, 0.35, 0.10), "yard_led", bev=0.02)
    # parked semi-trailers
    trailer("trl_a", 4.4, -7.0, 0.0)
    trailer("trl_b", 16.5, 34.0, math.radians(90), "yard_curtain2")
    trailer("trl_c", -60.0, 58.0, math.radians(2), "yard_curtain")
    # forest edge: dark mass + 3 rows of tree cards (pine-dominated, birch/alder at the edge)
    rnd = random.Random(5)
    bm = bmesh.new()
    N = 720
    ring = []
    for i in range(N):
        a = 2 * math.pi * i / N
        r = 255 + 35 * math.sin(2 * a + 1.3) + 12 * math.sin(5 * a + 0.4)
        ring.append((r, a))
    rows = [(bm.verts.new((r * math.cos(a), r * math.sin(a), -1)), bm.verts.new((r * math.cos(a), r * math.sin(a), 12.5)))
            for r, a in ring]
    for i in range(N):
        a0, b0 = rows[i]
        a1, b1 = rows[(i + 1) % N]
        bm.faces.new((a0, a1, b1, b0))
    G.finish("forest_mass", bm, "yard_forest_mass", smooth=False)
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new("UVMap")
    for row, dr in enumerate((-26, -16, -7, 0)):
        n = 1500 if row < 3 else 1100
        for i in range(n):
            a = 2 * math.pi * (i + rnd.random()) / n
            r = 255 + 35 * math.sin(2 * a + 1.3) + 12 * math.sin(5 * a + 0.4) + dr + rnd.uniform(-4, 4)
            p = V(r * math.cos(a), r * math.sin(a), -0.5)
            if row == 0:
                idx = rnd.choice([5, 6, 7, 0, 1, 2, 3])    # edge: birch / alder mixed with pine and spruce
                h = rnd.uniform(10, 21)
            else:
                idx = rnd.choice([0, 1, 2, 0, 1, 3, 4])    # inside: pine-dominated with spruce
                h = rnd.uniform(15, 27)
            card(bm, uvl, p, h, idx)
    G.finish("tree_cards", bm, "yard_tree", smooth=False, recalc=False)["fixed_uv"] = True
