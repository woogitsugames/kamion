"""ADR 0175: measure the lamps / retro-reflectors / markings / guards / mirrors of the TRAKT tractor and the
curtainsider semi-trailer straight from the generators (source pieces, no bake) and dump them as JSON.

    blender -b --factory-startup --python tools/blender/truck/regs_audit.py -- --out ABS.json [--what tractor|trailer]  (one Blender process per vehicle)

Frames: tractor = A2 frame (origin ground under the FRONT axle, +Y forward, driver -X); trailer = kingpin frame
(origin ground below the kingpin, +Y forward). All values metres, bbox per object: [xmin, xmax, ymin, ymax, zmin, zmax].
The checks against UN R48 / R58 / R70 / R73 / R104 / R46 / 96/53 / WT are evaluated in tools/blender/truck/regs_check.py
(pure Python, also run by pytest), so the numbers and the verdicts stay separate.
"""
import argparse
import json
import os
import sys

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "exterior"))
sys.path.insert(0, os.path.join(HERE, "trailer"))

TRACTOR_PREFIX = ("rear_lens_", "rear_lamp_", "side_marker", "side_repeater", "marker_front", "marker_rear",
                  "indicator_", "pos_led", "lamp_lens_", "plate", "rear_plate", "mirror_", "front_mirror",
                  "work_lamp", "reflex_", "side_reflex", "rear_reflex", "rear_fog", "fog_led", "contour", "r70", "rup", "sideguard",
                  "tri_reflector", "mudflap_")
TRAILER_PREFIX = ("rear_lens_", "rear_lamp_body", "side_marker_lens", "side_marker_reflex", "side_reflector",
                  "front_lamp_lens", "front_pos_", "front_reflex", "stalk_lens", "rear_marker_lens", "plate_",
                  "contour_", "r70_plate", "rup_bar", "sideguard_", "tri_reflector", "leg_", "wheel_1L_tyre",
                  "wheel_3L_tyre", "mudflap")


def bbox(o):
    pts = [o.matrix_world @ Vector(c) for c in o.bound_box]
    return [round(f(p[i] for p in pts), 4) for i in range(3) for f in (min, max)]


def dump(prefixes, skip=()):
    bpy.context.view_layer.update()
    out = {}
    lo, hi = Vector((1e9,) * 3), Vector((-1e9,) * 3)
    for o in bpy.data.objects:
        if o.type != "MESH" or o.get("bake_only") or o.get("group") in skip:
            continue
        b = bbox(o)
        for i in range(3):
            lo[i] = min(lo[i], b[2 * i])
            hi[i] = max(hi[i], b[2 * i + 1])
        if o.name.startswith(prefixes):
            mats = sorted({s.material.name for s in o.material_slots if s.material})
            out[o.name] = {"bbox": b, "mat": mats, "tris": sum(len(p.vertices) - 2 for p in o.data.polygons)}
    tris = 0
    dg = bpy.context.evaluated_depsgraph_get()
    for o in bpy.data.objects:
        if o.type == "MESH" and not o.get("bake_only") and o.get("group") not in skip:
            me = o.evaluated_get(dg).to_mesh()
            tris += sum(len(p.vertices) - 2 for p in me.polygons)
            o.evaluated_get(dg).to_mesh_clear()
    return {"objects": out, "overall": [round(v, 4) for p in zip(lo, hi) for v in p], "source_tris": tris}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--out", required=True)
    p.add_argument("--what", default="trailer", choices=["tractor", "trailer"])
    a = p.parse_args(argv)
    res = {}
    if a.what == "tractor":
        import a6_export as A
        import geom as G
        A.build_source()
        d = dump(TRACTOR_PREFIX, skip=("mirrors_cam", "interior_proxy"))
        d["frame"] = "A2: origin ground under front axle, +Y forward, driver -X"
        d["eye"] = [round(v, 4) for v in G.EYE]
        res["tractor"] = d
    if a.what == "trailer":
        bpy.ops.wm.read_factory_settings(use_empty=True)
        import tempfile
        import geom as G
        import materials as M
        import scene as S
        import trailer_build as T
        M.TEX_DIR = os.path.join(tempfile.gettempdir(), "kamion_trailer_src")
        S.setup_render("1600x900", 16)
        M.PARAMS["dirt"] = 1.0
        T.build(hi=False)
        d = dump(TRAILER_PREFIX)
        d["frame"] = "kingpin frame: origin ground below kingpin, +Y forward"
        d["dims"] = {"y_front": T.Y_FRONT, "y_rear": T.Y_REAR, "half_width": T.HW, "roof": T.ROOF, "floor": T.FLOOR,
                     "axles": list(T.AXLES), "landing_gear_y": T.LG["z"], "tyre_r": T.TYRE_R}
        res["trailer"] = d
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(res, f, indent=1)
    print("WROTE", a.out)


if __name__ == "__main__":
    main()
