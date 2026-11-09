"""Render setup, backdrops (A3 measuring studio, A4 overcast yard), lighting presets, cameras,
measurements, triangle stats and the driver-visibility analysis (ray casting from the eye point)."""
import json
import math
import os

import bmesh
import bpy
import numpy as np
from mathutils import Matrix, Vector

import geom as G
from geom import EYE, WB, V, link, set_group
import materials as M


# ---------------------------------------------------------------- render
def setup_render(res="1600x900", samples=192):
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
    sc.cycles.samples = samples
    sc.cycles.use_adaptive_sampling = True
    sc.cycles.adaptive_threshold = 0.015
    sc.cycles.use_denoising = True
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
    sc.cycles.sample_clamp_indirect = 8.0
    sc.render.resolution_x, sc.render.resolution_y = (int(v) for v in res.split("x"))
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "JPEG"
    sc.render.image_settings.color_mode = "RGB"
    sc.render.image_settings.quality = 86
    sc.view_settings.view_transform = "AgX"
    sc.view_settings.look = "None"
    sc.render.film_transparent = False


def lighting(kind):
    """overcast: sky gradient (zenith darker/bluer, bright horizon) + weak, very soft sun, full GI.
    urp: URP-like - flat ambient (SH stand-in) + one directional light, no diffuse bounce, 1 glossy
    bounce (reflection probe stand-in). studio: A2/A3 neutral grey + one soft sun."""
    sc = bpy.context.scene
    for o in list(bpy.data.objects):
        if o.type == "LIGHT":
            bpy.data.objects.remove(o)
    w = bpy.data.worlds.get("world_" + kind) or bpy.data.worlds.new("world_" + kind)
    w.use_nodes = True
    nt = w.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg = nt.nodes.new("ShaderNodeBackground")
    nt.links.new(bg.outputs[0], out.inputs[0])
    c = sc.cycles
    if kind == "overcast":
        tc = nt.nodes.new("ShaderNodeTexCoord")
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(tc.outputs["Generated"], sep.inputs[0])
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[0].color = (0.46, 0.47, 0.47, 1)     # ground bounce side
        ramp.color_ramp.elements[1].position = 0.52
        ramp.color_ramp.elements[1].color = (0.86, 0.88, 0.90, 1)     # bright horizon band
        e = ramp.color_ramp.elements.new(1.0)
        e.color = (0.60, 0.64, 0.70, 1)                               # zenith
        mr = nt.nodes.new("ShaderNodeMapRange")
        mr.inputs["From Min"].default_value = -1
        mr.inputs["From Max"].default_value = 1
        nt.links.new(sep.outputs[2], mr.inputs["Value"])
        nt.links.new(mr.outputs[0], ramp.inputs[0])
        nt.links.new(ramp.outputs[0], bg.inputs["Color"])
        bg.inputs["Strength"].default_value = 1.15
        sun_e, sun_a, rot = 0.9, 30.0, (math.radians(50), 0, math.radians(-150))
        c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces = 8, 4, 4, 8
    elif kind == "urp":
        bg.inputs["Color"].default_value = (0.50, 0.55, 0.62, 1)
        bg.inputs["Strength"].default_value = 0.55
        sun_e, sun_a, rot = 3.4, 1.5, (math.radians(48), 0, math.radians(-145))
        c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces = 4, 0, 1, 3
    else:  # studio
        bg.inputs["Color"].default_value = (0.62, 0.64, 0.66, 1)
        bg.inputs["Strength"].default_value = 0.85
        sun_e, sun_a, rot = 2.6, 6.0, (math.radians(42), 0, math.radians(-145))
        c.max_bounces, c.diffuse_bounces, c.glossy_bounces, c.transmission_bounces = 8, 3, 3, 8
    c.transparent_max_bounces = 16
    sc.world = w
    sun = bpy.data.lights.new("sun", "SUN")
    sun.energy = sun_e
    sun.angle = math.radians(sun_a)
    ob = bpy.data.objects.new("sun", sun)
    ob.rotation_euler = rot
    sc.collection.objects.link(ob)


# ---------------------------------------------------------------- backdrops
def _mat_concrete():
    m = bpy.data.materials.new("yard_concrete")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    tc = nt.nodes.new("ShaderNodeTexCoord")
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 0.35
    noise.inputs["Detail"].default_value = 8
    nt.links.new(tc.outputs["Object"], noise.inputs["Vector"])
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.17, 0.17, 0.165, 1)
    ramp.color_ramp.elements[1].color = (0.27, 0.265, 0.255, 1)
    nt.links.new(noise.outputs["Fac"], ramp.inputs[0])
    # slab joints every 5 m (dark lines)
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])
    lines = []
    for ax in (0, 1):
        a = nt.nodes.new("ShaderNodeMath"); a.operation = "DIVIDE"; a.inputs[1].default_value = 5.0
        nt.links.new(sep.outputs[ax], a.inputs[0])
        f = nt.nodes.new("ShaderNodeMath"); f.operation = "PINGPONG"; f.inputs[1].default_value = 0.5
        nt.links.new(a.outputs[0], f.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = 0.003
        nt.links.new(f.outputs[0], lt.inputs[0])
        lines.append(lt)
    mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
    nt.links.new(lines[0].outputs[0], mx.inputs[0]); nt.links.new(lines[1].outputs[0], mx.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    nt.links.new(mx.outputs[0], mix.inputs[0])
    nt.links.new(ramp.outputs[0], mix.inputs[6])
    mix.inputs[7].default_value = (0.06, 0.06, 0.06, 1)
    nt.links.new(mix.outputs[2], b.inputs["Base Color"])
    b.inputs["Roughness"].default_value = 0.88
    return m


def _mat_simple(name, rgb, rough=0.8, rib=0.0):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*rgb, 1)
    b.inputs["Roughness"].default_value = rough
    if rib:
        nt = m.node_tree
        tc = nt.nodes.new("ShaderNodeTexCoord")
        wv = nt.nodes.new("ShaderNodeTexWave")
        wv.wave_type = "BANDS"
        wv.bands_direction = "Z"
        wv.inputs["Scale"].default_value = rib
        nt.links.new(tc.outputs["Object"], wv.inputs["Vector"])
        bump = nt.nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value = 0.3
        nt.links.new(wv.outputs["Fac"], bump.inputs["Height"])
        nt.links.new(bump.outputs["Normal"], b.inputs["Normal"])
    return m


def _plane(name, size, loc, rot, m):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=size / 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    ob.location, ob.rotation_euler = loc, rot
    me.materials.append(m)
    bpy.context.scene.collection.objects.link(ob)
    ob["group"] = "backdrop"
    return ob


def _bx(name, c, s, m):
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1)
    bmesh.ops.scale(bm, vec=Vector(s), verts=bm.verts)
    bmesh.ops.translate(bm, vec=Vector(c), verts=bm.verts)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    ob = bpy.data.objects.new(name, me)
    me.materials.append(m)
    bpy.context.scene.collection.objects.link(ob)
    ob["group"] = "backdrop"
    return ob


def yard():
    """Simple logistics yard: concrete slabs, two sandwich-panel halls with dock doors, a far treeline
    (Podlasie flat horizon), lighting masts. No external assets."""
    _plane("ground", 400, (0, 0, 0), (0, 0, 0), _mat_concrete())
    wall = _mat_simple("hall_panel", (0.42, 0.43, 0.43), 0.6, rib=6.0)
    dock = _mat_simple("hall_dock", (0.10, 0.11, 0.12), 0.5)
    roofm = _mat_simple("hall_roof", (0.22, 0.22, 0.23), 0.7)
    trees = _mat_simple("treeline", (0.035, 0.045, 0.035), 0.9)
    mast = _mat_simple("mast", (0.35, 0.36, 0.37), 0.5)
    _bx("hall_A", (34, -8, 5), (16, 70, 10), wall)
    for k in range(6):
        _bx(f"dock_A{k}", (25.95, -32 + k * 9.5, 1.9), (0.1, 3.0, 3.2), dock)
    _bx("hall_B", (-6, -46, 4.5), (60, 16, 9), wall)
    _bx("hall_B_roof", (-6, -46, 9.05), (60.4, 16.4, 0.2), roofm)
    for k in range(5):
        _bx(f"dock_B{k}", (-28 + k * 10, -37.95, 1.9), (3.0, 0.1, 3.2), dock)
    # treeline ring segments far away (irregular heights)
    rng = np.random.default_rng(7)
    # continuous treeline: one ring mesh with a noisy crown silhouette (pine/birch edge)
    bm = bmesh.new()
    n = 720
    r = 170
    bot, top = [], []
    for k in range(n):
        a = 2 * math.pi * k / n
        h = 11 + 4 * math.sin(a * 7) + 3 * math.sin(a * 23 + 1) + rng.random() * 3.5
        bot.append(bm.verts.new((r * math.cos(a), r * math.sin(a), 0)))
        top.append(bm.verts.new((r * math.cos(a), r * math.sin(a), h)))
    for k in range(n):
        bm.faces.new((bot[k], bot[(k + 1) % n], top[(k + 1) % n], top[k]))
    me = bpy.data.meshes.new("treeline")
    bm.to_mesh(me)
    ob = bpy.data.objects.new("treeline", me)
    me.materials.append(trees)
    bpy.context.scene.collection.objects.link(ob)
    ob["group"] = "backdrop"
    for k, (x, y) in enumerate(((-16, -20), (14, 22), (-22, 18), (18, -26))):
        _bx(f"mast_{k}", (x, y, 7), (0.25, 0.25, 14), mast)
        _bx(f"mast_head_{k}", (x, y, 14), (1.2, 0.5, 0.3), mast)


def studio():
    """A2/A3 measuring studio: 1 m grid floor (5 m major), vertical grid walls for the ortho views."""
    _plane("ground", 120, (0, 0, 0), (0, 0, 0), _grid_material("grid", False))
    for name, loc, rot in (("wall_bok", (9.0, -2, 0), (math.pi / 2, 0, math.pi / 2)),
                           ("wall_przod", (0, -14.0, 0), (math.pi / 2, 0, 0))):
        ob = _plane(name, 60, loc, rot, _grid_material(name, True))
        ob.data.transform(Matrix.Translation((0, 30, 0)))
        ob.visible_shadow = False
        ob.hide_render = True


def _grid_material(name, emissive):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.9
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs[0])

    def line(sock, period, width):
        a = nt.nodes.new("ShaderNodeMath"); a.operation = "DIVIDE"; a.inputs[1].default_value = period
        nt.links.new(sock, a.inputs[0])
        f = nt.nodes.new("ShaderNodeMath"); f.operation = "PINGPONG"; f.inputs[1].default_value = 0.5
        nt.links.new(a.outputs[0], f.inputs[0])
        lt = nt.nodes.new("ShaderNodeMath"); lt.operation = "LESS_THAN"; lt.inputs[1].default_value = width / period
        nt.links.new(f.outputs[0], lt.inputs[0])
        return lt.outputs[0]

    def both(period, width):
        mx = nt.nodes.new("ShaderNodeMath"); mx.operation = "MAXIMUM"
        nt.links.new(line(sep.outputs[0], period, width), mx.inputs[0])
        nt.links.new(line(sep.outputs[1], period, width), mx.inputs[1])
        return mx.outputs[0]

    mix1 = nt.nodes.new("ShaderNodeMix"); mix1.data_type = "RGBA"
    mix1.inputs[6].default_value = (0.42, 0.42, 0.41, 1)
    mix1.inputs[7].default_value = (0.24, 0.24, 0.24, 1)
    nt.links.new(both(1.0, 0.006), mix1.inputs[0])
    mix2 = nt.nodes.new("ShaderNodeMix"); mix2.data_type = "RGBA"
    nt.links.new(mix1.outputs[2], mix2.inputs[6])
    mix2.inputs[7].default_value = (0.12, 0.12, 0.12, 1)
    nt.links.new(both(5.0, 0.01), mix2.inputs[0])
    if emissive:
        em = nt.nodes.new("ShaderNodeEmission")
        mix1.inputs[6].default_value = (0.60, 0.61, 0.62, 1)
        mix1.inputs[7].default_value = (0.47, 0.48, 0.49, 1)
        mix2.inputs[7].default_value = (0.36, 0.37, 0.38, 1)
        nt.links.new(mix2.outputs[2], em.inputs["Color"])
        nt.links.new(em.outputs[0], nt.nodes["Material Output"].inputs["Surface"])
    else:
        nt.links.new(mix2.outputs[2], bsdf.inputs["Base Color"])
    return m


def mannequin():
    """1.80 m reference figure (parented to 'figure_root', moved per view)."""
    set_group("figure")
    before = set(bpy.data.objects)
    for s in (-1, 1):
        G.cyl(f"fig_leg{s}", (s * 0.10, 0, 0.45), 0.075, 0.82, "figure", axis="Z", seg=16, bev=0.03)
        G.box(f"fig_foot{s}", (s * 0.10, 0.05, 0.035), (0.10, 0.26, 0.07), "figure", bev=0.02)
        G.rod(f"fig_arm{s}", (s * 0.235, 0, 1.43), (s * 0.27, 0.02, 0.82), 0.045, "figure")
    G.box("fig_torso", (0, 0, 1.17), (0.40, 0.22, 0.62), "figure", bev=0.08, seg=3)
    G.cyl("fig_neck", (0, 0, 1.53), 0.05, 0.10, "figure", axis="Z", seg=16)
    G.sphere("fig_head", (0, 0, 1.68), 0.10, "figure", scale=(0.95, 1.05, 1.2))
    root = link(bpy.data.objects.new("figure_root", None))
    for ob in set(bpy.data.objects) - before:
        if ob is not root:
            ob.parent = root
    return root


# ---------------------------------------------------------------- cameras
def add_camera(name, loc, target=None, lens=45, ortho=None, rot=None, sensor=36):
    cam = bpy.data.cameras.new(name)
    cam.sensor_width = sensor
    cam.clip_start = 0.02
    cam.clip_end = 500
    if ortho:
        cam.type = "ORTHO"
        cam.ortho_scale = ortho
    else:
        cam.lens = lens
    ob = bpy.data.objects.new(name, cam)
    ob.location = loc
    if target is not None:
        ob.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if rot is not None:
        ob.rotation_euler = rot
    bpy.context.scene.collection.objects.link(ob)
    return ob


def eye_dir(yaw_deg, pitch_deg):
    """yaw 0 = straight ahead (+Y), positive = to the left (driver side window), pitch positive = up."""
    y, p = math.radians(yaw_deg), math.radians(pitch_deg)
    return Vector((-math.sin(y) * math.cos(p), math.cos(y) * math.cos(p), math.sin(p)))


CAMS = {
    "34przod": dict(loc=(-8.4, 10.6, 1.65), target=(-0.1, -0.9, 1.72), lens=42, fig=(2.8, 2.4)),
    "bok": dict(loc=(-30, -1.0, 1.95), rot=(math.radians(90), 0, math.radians(-90)), ortho=10.8, fig=(-2.0, 2.4)),
    "przod": dict(loc=(-0.0, 30, 2.05), rot=(math.radians(90), 0, math.radians(180)), ortho=6.6, fig=(-2.4, 2.4)),
    "34tyl": dict(loc=(9.2, -14.6, 2.5), target=(-0.3, -1.7, 1.55), lens=42, fig=(-2.6, -6.2)),
    "zbl_reflektor": dict(loc=(-2.7, 4.5, 1.62), target=(-0.98, 1.45, 1.44), lens=75, fig=None),
    "zbl_stopnie": dict(loc=(-4.4, 1.6, 1.15), target=(-1.2, -0.30, 0.78), lens=45, fig=None),
    "zbl_tyl": dict(loc=(-3.4, -7.6, 3.4), target=(0.0, -2.5, 1.25), lens=38, fig=None),
    "zbl_kolo": dict(loc=(4.2, -2.6, 0.95), target=(1.2, -3.7, 0.55), lens=50, fig=None),
    "top": dict(loc=(0.0, 3.0, 40), rot=(0, 0, 0), ortho=28.0, fig=None),
    "tilt": dict(loc=(-30, -0.4, 2.3), rot=(math.radians(90), 0, math.radians(-90)), ortho=10.0, fig=None),
}
EYE_CAMS = {"oko_przod": (0, -6), "oko_lewo": (72, -8), "oko_prawo": (-48, -6)}


# ---------------------------------------------------------------- stamps
def stamp(text):
    r = bpy.context.scene.render
    r.use_stamp = True
    for a in ("date", "time", "render_time", "frame", "frame_range", "memory", "hostname", "camera", "lens",
              "scene", "marker", "filename", "sequencer_strip"):
        if hasattr(r, "use_stamp_" + a):
            setattr(r, "use_stamp_" + a, False)
    r.use_stamp_note = True
    r.stamp_note_text = text
    r.stamp_font_size = 20
    r.stamp_background = (0.08, 0.08, 0.08, 0.85)
    r.stamp_foreground = (0.92, 0.92, 0.92, 1)
    if hasattr(r, "use_stamp_labels"):
        r.use_stamp_labels = False


# ---------------------------------------------------------------- measurement + stats
TRUCK_GROUPS = ("cab", "lower", "frame", "wheels", "mirrors")


def truck_objects(groups=TRUCK_GROUPS):
    return [o for o in bpy.data.objects if o.get("group") in groups and o.type in {"MESH", "CURVE"}
            and not o.hide_render]


def measure(out_path):
    dg = bpy.context.evaluated_depsgraph_get()

    def bbox(obs):
        lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
        for ob in obs:
            for c in ob.evaluated_get(dg).bound_box:
                w = ob.matrix_world @ Vector(c)
                lo = Vector(map(min, lo, w))
                hi = Vector(map(max, hi, w))
        return lo, hi
    allo = truck_objects()
    body = [o for o in allo if o.get("group") != "mirrors" and not o.name.startswith(("front_mirror", "cam_"))]
    lo, hi = bbox(allo)
    blo, bhi = bbox(body)
    fz = max((bpy.data.objects["fifth_plate"].matrix_world @ Vector(c)).z
             for c in bpy.data.objects["fifth_plate"].evaluated_get(dg).bound_box)
    res = {
        "overall_length_m (incl. class VI mirror)": round(hi.y - lo.y, 3),
        "body_length_m (no mirrors)": round(bhi.y - blo.y, 3),
        "front_overhang_m (axle->bumper)": round(bhi.y, 3),
        "rear_overhang_m (axle->rear incl. lamps)": round(-blo.y - WB, 3),
        "overall_height_m": round(hi.z, 3),
        "width_body_m (no mirrors, limit 2.55)": round(bhi.x - blo.x, 3),
        "width_incl_mirrors_m": round(hi.x - lo.x, 3),
        "fifth_wheel_height_m": round(fz, 3),
        "wheelbase_m": WB,
    }
    json.dump(res, open(out_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("MEASURED", json.dumps(res, ensure_ascii=False))
    return res


def tri_stats(out_path, extra=None):
    dg = bpy.context.evaluated_depsgraph_get()
    by_group, by_slot, by_obj = {}, {}, []
    total = 0
    for ob in truck_objects():
        ev = ob.evaluated_get(dg)
        try:
            me = ev.to_mesh()
        except RuntimeError:
            continue
        me.calc_loop_triangles()
        n = len(me.loop_triangles)
        slots = {}
        for t in me.loop_triangles:
            mi = t.material_index
            mname = ob.material_slots[mi].material.name if mi < len(ob.material_slots) and ob.material_slots[
                mi].material else "?"
            sl = M.SLOTS.get(mname, "?")
            slots[sl] = slots.get(sl, 0) + 1
        ev.to_mesh_clear()
        g = ob.get("group")
        by_group[g] = by_group.get(g, 0) + n
        for k, v in slots.items():
            by_slot[k] = by_slot.get(k, 0) + v
        by_obj.append((n, ob.name))
        total += n
    by_obj.sort(reverse=True)
    res = {"lod0_exterior_tris": total, "by_group": by_group, "by_game_slot": by_slot,
           "top_objects": [{"name": n, "tris": t} for t, n in by_obj[:25]],
           "objects": len(by_obj), "render_materials": sorted({k for k in M.SLOTS}),
           "game_slots": sorted({v for v in M.SLOTS.values() if v != "-"})}
    if extra:
        res.update(extra)
    json.dump(res, open(out_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("TRIS", total, by_group)
    return res


def lod_estimate(ratios=(0.45, 0.15)):
    """Planned LOD1/LOD2: Decimate (collapse) per object, measured on the evaluated mesh. Plan only:
    final LODs are authored in A6 (merge into atlases, drop hidden parts first)."""
    dg = bpy.context.evaluated_depsgraph_get()
    out = {}
    obs = [o for o in truck_objects() if o.type == "MESH"]
    for r in ratios:
        for o in obs:
            md = o.modifiers.new("lodtmp", "DECIMATE")
            md.ratio = r
        dg.update()
        n = 0
        for o in obs:
            me = o.evaluated_get(dg).to_mesh()
            me.calc_loop_triangles()
            n += len(me.loop_triangles)
            o.evaluated_get(dg).to_mesh_clear()
        for o in obs:
            o.modifiers.remove(o.modifiers["lodtmp"])
        out[f"decimate_{r}"] = n
    return out


# ---------------------------------------------------------------- driver visibility
TRANSPARENT = {"glass", "glass_tint"}


def _classify(ob, mname):
    n = ob.name
    if n.startswith("ip_wheel"):
        return 4, "kierownica"
    if n.startswith("ip_"):
        return 5, "deska/wnętrze"
    if "mirror" in n or n.startswith("cam_"):
        return 3, "lusterko"
    if ob.get("group") == "cab" and mname in ("paint", "frit", "plastic_satin", "interior", "gap", "rubber"):
        return 2, "słupek/nadwozie"
    if ob.name == "ground" or ob.get("group") == "backdrop":
        return 0, "widoczne"
    return 1, "inne części"


def visibility(out_dir, az=(-110, 110), el=(-50, 30), step=0.5):
    """Ray-cast from the eye point. Image: azimuth (x, left = driver side) x elevation (y).
    Also: nearest visible ground distance per azimuth (blind-zone polygon) and A-pillar widths."""
    sc = bpy.context.scene
    dg = bpy.context.evaluated_depsgraph_get()
    azs = np.arange(az[1], az[0] - 1e-9, -step)   # left-to-right in the image: +yaw (left) first
    els = np.arange(el[0], el[1] + 1e-9, step)
    cat = np.zeros((len(els), len(azs)), dtype=np.int8)
    ground_d = np.full(len(azs), np.inf)
    ev_cache = {}
    for i, e in enumerate(els):
        for j, a in enumerate(azs):
            d = eye_dir(a, e)
            o = EYE.copy()
            hitcat = 0
            for _ in range(8):
                hit, loc, nrm, idx, ob, _m = sc.ray_cast(dg, o, d, distance=300)
                if not hit:
                    hitcat = 0
                    break
                ev = ev_cache.get(ob.name)
                if ev is None:
                    ev = ob.evaluated_get(dg).data
                    ev_cache[ob.name] = ev
                try:
                    mi = ev.polygons[idx].material_index
                    mname = ob.material_slots[mi].material.name
                except Exception:
                    mname = "?"
                if mname in TRANSPARENT:
                    o = loc + d * 1e-3
                    continue
                hitcat, _lbl = _classify(ob, mname)
                if hitcat == 0 and e < 0:
                    hd = math.hypot(loc.x - EYE.x, loc.y - EYE.y)
                    ground_d[j] = min(ground_d[j], hd)
                break
            cat[i, j] = hitcat
    pal = np.array([[0.80, 0.86, 0.92], [0.35, 0.35, 0.35], [0.70, 0.20, 0.15], [0.20, 0.35, 0.75],
                    [0.85, 0.60, 0.15], [0.45, 0.30, 0.20]], dtype=np.float32)
    img = pal[cat]
    # 10-degree grid + horizon
    for j, a in enumerate(azs):
        if abs(a % 10) < 1e-6:
            img[:, j] *= 0.8
    for i, e in enumerate(els):
        if abs(e % 10) < 1e-6:
            img[i, :] *= 0.8 if e else 0.45
    up = np.repeat(np.repeat(img, 4, axis=0), 4, axis=1)
    h, w = up.shape[:2]
    rgba = np.concatenate([up, np.ones((h, w, 1), np.float32)], axis=2)
    im = bpy.data.images.new("visibility_map", w, h)
    im.pixels.foreach_set(rgba.ravel())
    im.filepath_raw = os.path.join(out_dir, "widocznosc_mapa.png")
    im.file_format = "PNG"
    im.save()
    # metrics
    def blocked_span(e_deg, side):
        i = int(round((e_deg - el[0]) / step))
        row = cat[i]
        spans, cur = [], None
        for j, a in enumerate(azs):
            if (side > 0 and a < 0) or (side < 0 and a > 0):
                continue
            if row[j] == 2:
                cur = [a, a] if cur is None else [cur[0], a]
            elif cur is not None:
                spans.append(cur); cur = None
        if cur:
            spans.append(cur)
        return [(round(float(a), 1), round(float(b), 1)) for a, b in spans]
    i0 = int(np.argmin(np.abs(azs - 0)))
    bumper_y = 1.522
    res = {
        "eye_point_m": list(EYE),
        "ground_visible_from_m_ahead_of_bumper_straight_ahead": round(float(ground_d[i0] - (bumper_y - EYE.y)), 2),
        "ground_visible_from_m_ahead_of_bumper_at_passenger_corner": None,
        "pillar_and_body_spans_deg_at_eye_height (left side, +yaw)": blocked_span(0.0, 1),
        "pillar_and_body_spans_deg_at_eye_height (right side, -yaw)": blocked_span(0.0, -1),
        "map_axes": f"x: yaw {az[1]}..{az[0]} deg (left = driver side), y: pitch {el[0]}..{el[1]} deg, 10 deg grid",
        "legend": {"jasnoniebieski": "widoczne (przez szybę)", "szary": "inne części", "czerwony": "słupek/nadwozie",
                   "niebieski": "lusterko", "pomarańczowy": "kierownica", "brązowy": "deska/wnętrze (proxy A3)"},
    }
    # passenger corner: azimuth towards the front-right corner of the bumper
    corner = Vector((1.245, bumper_y, 0))
    ac = -math.degrees(math.atan2(corner.x - EYE.x, corner.y - EYE.y))
    jc = int(np.argmin(np.abs(azs - ac)))
    dist_eye_corner = math.hypot(corner.x - EYE.x, corner.y - EYE.y)
    res["ground_visible_from_m_ahead_of_bumper_at_passenger_corner"] = round(float(ground_d[jc] - dist_eye_corner), 2)
    res["azimuth_to_passenger_corner_deg"] = round(ac, 1)
    json.dump(res, open(os.path.join(out_dir, "widocznosc.json"), "w", encoding="utf-8"), indent=2,
              ensure_ascii=False)
    print("VIS", json.dumps(res, ensure_ascii=False))
    return azs, ground_d, res


def blind_zone_mesh(azs, ground_d, cap=12.0):
    """Ground polygon: area the driver cannot see directly (between the eye and the first visible ground)."""
    set_group("analysis")
    bm = bmesh.new()
    c = bm.verts.new((EYE.x, EYE.y, 0.02))
    ring = []
    for a, d in zip(azs, ground_d):
        d = min(d, cap) if np.isfinite(d) else cap
        dv = eye_dir(a, 0)
        ring.append(bm.verts.new((EYE.x + dv.x * d, EYE.y + dv.y * d, 0.02)))
    for a, b in zip(ring, ring[1:]):
        bm.faces.new((c, a, b))
    m = bpy.data.materials.new("blind_zone")
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (0.75, 0.08, 0.05, 1)
    b.inputs["Alpha"].default_value = 0.55
    G.STATE["mats"]["blind_zone"] = m
    return G.obj_from_bm("blind_zone", bm, "blind_zone", smooth=False)
