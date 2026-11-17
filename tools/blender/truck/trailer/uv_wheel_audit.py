"""Audit of the trailer wheel UVs in the exported FBX (review 2026-11-16 s23, P1 'red rims').

    blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/trailer/uv_wheel_audit.py -- \
        [--fbx art-source/truck/trailer/export/SM_Trailer_LOD0.fbx] [--tex <T_Trl_Metal_C.png>] [--json out.json]

Rasterises the 'Atlas' UV of every face per baked material at the texture resolution and reports, for the wheel
objects (WHEEL_*), the texels shared with any non-wheel object, plus the 3D centres of the non-wheel faces that land
on wheel texels (to find the culprit piece), and - with --tex - the wheel texels whose albedo is red (R - G > 0.2,
docs/06 §5: no red / text from other islands on a rim). Exit code 1 if overlap or red texels > 0.
"""
import json
import math
import os
import sys

import bpy
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
RED_DELTA = 0.2


def raster(me, mi, res, uvname="Atlas"):
    """Per loop triangle of material index mi: boolean mask (res x res, row 0 = v 0) and per-face masks list."""
    me.calc_loop_triangles()
    uv = np.empty(len(me.loops) * 2, dtype=np.float32)
    me.uv_layers[uvname].data.foreach_get("uv", uv)
    uv = uv.reshape(-1, 2) * res - 0.5
    m = np.zeros((res, res), dtype=bool)
    tri_px = []
    for lt in me.loop_triangles:
        if lt.material_index != mi:
            continue
        P = uv[list(lt.loops)]
        x0, y0 = np.floor(P.min(axis=0)).astype(int)
        x1, y1 = np.ceil(P.max(axis=0)).astype(int)
        x0, y0, x1, y1 = max(x0, 0), max(y0, 0), min(x1, res - 1), min(y1, res - 1)
        if x1 < x0 or y1 < y0:
            continue
        X, Y = np.meshgrid(np.arange(x0, x1 + 1), np.arange(y0, y1 + 1))
        inside = np.ones(X.shape, dtype=bool)
        area = (P[1, 0] - P[0, 0]) * (P[2, 1] - P[0, 1]) - (P[2, 0] - P[0, 0]) * (P[1, 1] - P[0, 1])
        if abs(area) < 1e-9:
            continue
        sgn = 1.0 if area >= 0 else -1.0
        for i in range(3):
            a, b = P[i], P[(i + 1) % 3]
            ex, ey = b[0] - a[0], b[1] - a[1]
            ln = math.hypot(ex, ey) or 1e-9
            inside &= sgn * (ex * (Y - a[1]) - ey * (X - a[0])) / ln >= 0.0
        m[y0:y1 + 1, x0:x1 + 1] |= inside
        tri_px.append((lt.polygon_index, x0, y0, x1, y1, inside))
    return m, tri_px


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []

    def arg(k, d=None):
        return argv[argv.index(k) + 1] if k in argv else d
    fbx = arg("--fbx", os.path.join(REPO, "art-source", "truck", "trailer", "export", "SM_Trailer_LOD0.fbx"))
    tex = arg("--tex")
    res = int(arg("--res", 1024))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=fbx)
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    out = {"fbx": os.path.relpath(fbx, REPO), "res": res, "slots": {}}
    fail = 0
    img = None
    if tex:
        im = bpy.data.images.load(tex)
        w, h = im.size
        a = np.empty(w * h * 4, dtype=np.float32)
        im.pixels.foreach_get(a)
        img = a.reshape(h, w, 4)
    for mname in ("MI_Trl_Metal", "MI_Trl_Trim"):
        wheel = np.zeros((res, res), dtype=bool)
        others = {}
        tri_cache = {}
        for o in meshes:
            names = [s.material.name.split(".")[0] if s.material else "" for s in o.material_slots]
            if mname not in names:
                continue
            m, tp = raster(o.data, names.index(mname), res)
            if o.name.startswith("WHEEL_"):
                wheel |= m
            else:
                others[o.name] = m
                tri_cache[o.name] = tp
        rep = {"wheel_texels": int(wheel.sum()), "overlap": {}, "culprits": {}}
        for n, m in others.items():
            ov = int((wheel & m).sum())
            if not ov:
                continue
            rep["overlap"][n] = ov
            fail += 1
            o = bpy.data.objects[n]
            cent = {}
            for pi, x0, y0, x1, y1, ins in tri_cache[n]:
                if (ins & wheel[y0:y1 + 1, x0:x1 + 1]).any():
                    c = o.matrix_world @ o.data.polygons[pi].center
                    key = (round(c.x, 1), round(c.y, 1), round(c.z, 1))
                    cent[key] = cent.get(key, 0) + 1
            rep["culprits"][n] = sorted(([list(k), v] for k, v in cent.items()), key=lambda t: -t[1])[:12]
        if img is not None and mname == "MI_Trl_Metal":
            ih = img.shape[0]
            ys, xs = np.nonzero(wheel)
            px = img[(ys * ih // res), (xs * ih // res)]
            red = (px[:, 0] - px[:, 1]) > RED_DELTA
            rep["red_texels"] = int(red.sum())
            fail += int(red.sum() > 0)
        out["slots"][mname] = rep
        print(f"UVAUDIT {mname}: wheel texels {rep['wheel_texels']}, overlap {rep['overlap']}, "
              f"red {rep.get('red_texels', '-')}")
        for n, c in rep["culprits"].items():
            print(f"UVAUDIT   {n} faces on wheel texels at (Blender m, count): {c}")
    if arg("--json"):
        with open(arg("--json"), "w", encoding="utf-8") as f:
            json.dump(out, f, indent=1)
    print("UV WHEEL AUDIT:", "PASS" if not fail else f"FAIL ({fail})")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
