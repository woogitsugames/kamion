"""TRAKT tractor exterior — Track A3 (scale blockout, eye point, visibility) and A4 (detailed exterior).

Run headless (Blender 4.2 LTS, GPU OptiX if available):
  A3:  blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a3 \
           --out docs/reports/visual/truck-A3
  A4:  blender -b --factory-startup --python tools/blender/truck/exterior/build.py -- --mode a4 \
           --out docs/reports/visual/truck-A4 --lights overcast,urp --liveries white,dark
Options: --views a,b,c  --mirrors classic|camera  --samples N  --res WxH  --blend <path>  --tag <suffix>
Everything is generated from code (no hand-edited .blend). Frame: Z up, +Y forward, driver (LHD) = -X,
origin = ground under the front axle centre; Unity axes are mapped at export (A7).
"""
import argparse
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import geom as G  # noqa: E402
import materials as M  # noqa: E402
import body as B  # noqa: E402
import chassis as C  # noqa: E402
import scene as S  # noqa: E402

LABEL = {
    "34przod": "3/4 przód", "bok": "bok lewy (ortho)", "przod": "przód (ortho)", "34tyl": "3/4 tył (prawa strona)",
    "zbl_reflektor": "zbliżenie: reflektor", "zbl_stopnie": "zbliżenie: nadkole i stopnie",
    "zbl_tyl": "zbliżenie: tył kabiny, siodło, przewody", "zbl_kolo": "zbliżenie: koła tylne, błotnik",
    "top": "widok z góry", "top_kabina": "kabina z góry (ortho)", "tilt": "test uchylania kabiny 50° (ortho)",
    "oko_przod": "z punktu oczu: na wprost", "oko_lewo": "z punktu oczu: szyba lewa",
    "oko_prawo": "z punktu oczu: szyba prawa i lusterka",
}
LIGHT_LABEL = {"overcast": "pochmurno (pełne GI)", "urp": "jak URP (bez odbić rozproszonych)", "studio": "studio", "lowsun": "niskie słońce (~8°)"}


def parse():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--mode", default="a4", choices=["a3", "a4"])
    p.add_argument("--out", required=True)
    p.add_argument("--views", default="")
    p.add_argument("--lights", default="")
    p.add_argument("--liveries", default="white")
    p.add_argument("--mirrors", default="classic", choices=["classic", "camera"])
    p.add_argument("--res", default="1600x900")
    p.add_argument("--samples", type=int, default=192)
    p.add_argument("--blend", default="")
    p.add_argument("--tag", default="")
    p.add_argument("--no-analysis", action="store_true")
    p.add_argument("--beam", default="", choices=["", "low"], help="a4: QA render with the dipped beam lit")
    p.add_argument("--shape", default=B.DEFAULT_SHAPE, choices=["b2", "round", "modern"],
                   help="cab surfacing: b2 = exported cab, round = rounding-pass proposal (owner approval pending)")
    p.add_argument("--rake", type=float, default=None, help="modern only: front plane rake in degrees (default 7)")
    p.add_argument("--vis", action="store_true", help="a4: eye-point views + visibility map (widocznosc_*)")
    return p.parse_args(argv)


def build(a):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    G.STATE["coll"] = bpy.context.scene.collection
    S.setup_render(a.res, a.samples)
    clay = a.mode == "a3"
    M.build_library(a.liveries.split(",")[0], clay=clay)
    if clay:
        for k in ("tyre_steer", "tyre_drive"):
            M.principled(k, "TYRE", (0.03, 0.03, 0.03), 0.85)
    else:
        C.make_tyre_materials()
    subpaths, strokes = G.load_svg_mark(os.path.join(G.REPO, "art-source", "truck", "brand", "trakt.svg"))
    B.set_shape(a.shape, a.rake)
    B.cab_shell()
    B.glazing()
    B.doors_and_gaps()
    B.front_face(subpaths, strokes)
    B.headlamps()
    B.corners_roof_rear()
    B.mirrors("classic", front=True)
    B.mirrors("camera", front=False)
    B.lower_fairing()
    B.interior_proxies()
    C.build_all()
    # functional empties (export points, A7)
    G.set_group("points")
    for name, loc in (("eye_point", G.EYE), ("cab_tilt_pivot", B.PIVOT), ("axle_front", (0, 0, G.WHEEL_Z)),
                      ("axle_rear", (0, -G.WB, G.WHEEL_Z)), ("kingpin", (0, -G.WB + G.FIFTH_LEAD, G.FIFTH_H))):
        e = bpy.data.objects.new(name, None)
        e.location = loc
        e.empty_display_size = 0.15
        G.link(e)
    set_mirrors(a.mirrors)
    if a.beam == "low" and not clay:
        light_low_beam()
    if clay:
        S.studio()
    else:
        S.yard()
    fig = S.mannequin()
    return fig


def light_low_beam(strength=60.0):
    """QA only (--beam low): the two inner projector lenses get an emissive copy of the lens material, the
    emission follows the lens' own refraction gradient (bright below the cut-off line). The bake is unaffected."""
    src = bpy.data.materials.get("projector")
    lit = src.copy()
    lit.name = "projector_lit"
    nt = lit.node_tree
    b = nt.nodes["Principled BSDF"]
    col = b.inputs["Base Color"]
    if col.is_linked:
        nt.links.new(col.links[0].from_socket, b.inputs["Emission Color"])
    else:
        b.inputs["Emission Color"].default_value = (1.0, 0.97, 0.92, 1)
    b.inputs["Emission Strength"].default_value = strength
    for o in bpy.data.objects:
        if o.name.startswith("proj_lens_"):
            for sl in o.material_slots:
                if sl.material == src:
                    sl.material = lit


def set_mirrors(kind):
    for o in bpy.data.objects:
        if o.get("group") == "mirrors_cam":
            o.hide_render = kind != "camera"
        elif o.get("group") == "mirrors" and not o.name.startswith("front_mirror"):
            o.hide_render = kind != "classic"


def render_view(a, v, light, livery, fig, suffix=""):
    sc = bpy.context.scene
    if v in S.EYE_CAMS:
        yaw, pitch = S.EYE_CAMS[v]
        d = S.eye_dir(yaw, pitch)
        cam = S.add_camera("cam_" + v, G.EYE, G.EYE + d, lens=16)
    else:
        c = S.CAMS[v]
        cam = S.add_camera("cam_" + v, c["loc"], c.get("target"), c.get("lens", 45), c.get("ortho"), c.get("rot"))
    sc.camera = cam
    f = S.CAMS.get(v, {}).get("fig")
    fig.hide_render = f is None
    for ch in fig.children:
        ch.hide_render = f is None
    if f:
        fig.location = (*f, 0)
    for w in ("wall_bok", "wall_przod"):
        ob = bpy.data.objects.get(w)
        if ob:
            ob.hide_render = not (a.mode == "a3" and w == "wall_" + v)
    lv = M.LIVERIES["clay" if a.mode == "a3" else livery][3]
    mode = "A3 blockout w skali (clay)" if a.mode == "a3" else (
        "A4 zewnętrze" + ({"round": " | PROPOZYCJA: zaokrąglenia", "modern": " | PROPOZYCJA: nowy front" + (f" {a.rake:g}°" if a.rake is not None else "")}.get(a.shape, "")))
    S.stamp(f"TRAKT (koncepcja B) | {LABEL.get(v, v)} | {lv} | {LIGHT_LABEL[light]} | {mode}"
            + (" | figura 1,80 m" if f else ""))
    name = f"{v}_{livery}_{light}{suffix}.jpg" if a.mode == "a4" else f"{v}{suffix}.jpg"
    sc.render.filepath = os.path.join(a.out, name)
    bpy.ops.render.render(write_still=True)
    print("WROTE", sc.render.filepath)


def tilt_cab(angle_deg):
    piv = bpy.data.objects.new("tilt_root", None)
    piv.location = B.PIVOT
    G.STATE["coll"].objects.link(piv)
    bpy.context.view_layer.update()
    moved = [o for o in bpy.data.objects if o.get("group") in ("cab", "mirrors", "mirrors_cam", "interior_proxy")
             and o.parent is None]
    for o in moved:
        o.parent = piv
        o.matrix_parent_inverse = piv.matrix_world.inverted()
    piv.rotation_euler = (math.radians(-angle_deg), 0, 0)
    return piv, moved


def main():
    a = parse()
    a.out = os.path.abspath(a.out)
    os.makedirs(a.out, exist_ok=True)
    fig = build(a)
    S.measure(os.path.join(a.out, "wymiary.json"))
    if a.shape == B.DEFAULT_SHAPE and a.rake is None:   # the interior reads this contract: default variant only
        B.door_interface(os.path.join(G.REPO, "art-source", "truck", "exterior", "door_interface.json"))
    else:
        B.door_interface(os.path.join(a.out, f"door_interface_{a.shape}.json"))
    if a.mode == "a4":
        lods = S.lod_estimate()
        S.tri_stats(os.path.join(a.out, "stats.json"), extra={"lod_plan_measured": lods})
    if a.mode == "a3":
        lights = (a.lights or "studio").split(",")
        views = (a.views or "34przod,bok,przod,34tyl").split(",")
        for light in lights:
            S.lighting(light)
            for v in views:
                render_view(a, v, light, "clay", fig)
        if not a.no_analysis:
            S.lighting("overcast")
            for v in ("oko_przod", "oko_lewo", "oko_prawo"):
                render_view(a, v, "overcast", "clay", fig)
            azs, gd, res = S.visibility(a.out)
            S.blind_zone_mesh(azs, gd)
            S.lighting("studio")
            render_view(a, "top", "studio", "clay", fig)
            bz = bpy.data.objects.get("blind_zone")
            if bz:
                bz.hide_render = True
            piv, moved = tilt_cab(50)
            render_view(a, "tilt", "studio", "clay", fig)
    else:
        lights = (a.lights or "overcast").split(",")
        views = (a.views or "34przod,bok,przod,34tyl,zbl_reflektor,zbl_stopnie").split(",")
        for light in lights:
            S.lighting(light)
            for livery in a.liveries.split(","):
                M.build_paint(livery)
                for v in views:
                    render_view(a, v, light, livery, fig, a.tag)
        if a.vis:
            S.lighting("overcast")
            M.build_paint(a.liveries.split(",")[0])
            for v in ("oko_przod", "oko_lewo", "oko_prawo"):
                render_view(a, v, "overcast", a.liveries.split(",")[0], fig, a.tag)
            S.visibility(a.out)
    if a.blend:
        os.makedirs(os.path.dirname(os.path.abspath(a.blend)), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=os.path.abspath(a.blend))


if __name__ == "__main__":
    main()
