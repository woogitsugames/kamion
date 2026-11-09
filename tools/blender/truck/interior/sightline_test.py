"""Track A6 — automated sightline test: are the key instruments visible from the driver eye point?

    blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/interior/sightline_test.py -- \
        [--report out.json] [--lod 0] [--rake 19]

Builds the same interior as build_interior.py (no render), then casts rays from the eye point (and a small head box
around it) to a dense grid of sample points on every key instrument rectangle. A sample is occluded when the first
hit along the ray is any mesh other than the instrument itself or the glass in front of it (cover glass, windscreen).

Key instruments (the critic's P0, REVIEW-2026-11-09 #4): the whole cluster screen rectangle, and inside it the
safety-critical readouts (speed, gear, both air-pressure circuits, fuel/AdBlue, warning-lamp rows), plus any physical
round gauge that exists in the model. Exit code 1 (FAIL) when any key sample is occluded from the nominal eye point
or when more than MAX_HEAD_OCCLUSION of the samples are occluded from the head-box points (+-20 mm sideways and
vertically: normal posture, not leaning).
"""
import argparse
import json
import os
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import build_interior as BI  # noqa: E402

# Regions inside the cluster screen in normalised screen coordinates (u right, v up), matching the layout drawn by
# make_textures.cluster_display(). Every region listed here is safety- or driving-critical.
CLUSTER_REGIONS = {
    "whole_screen": (0.0, 0.0, 1.0, 1.0),
    "speed": (0.38, 0.30, 0.62, 0.95),
    "gear_cc": (0.38, 0.05, 0.62, 0.32),
    "air_pressure_I_II": (0.76, 0.05, 0.99, 0.48),
    "fuel_adblue": (0.01, 0.05, 0.24, 0.48),
    "tacho": (0.02, 0.45, 0.30, 0.98),
    "telltales_row": (0.0, 0.88, 1.0, 1.0),
}
SEE_THROUGH = ("cluster_glass", "windscreen", "cover_glass", "side_glass")
MAX_HEAD_OCCLUSION = 0.0  # whole-screen samples occluded from the head box (fraction); key regions must be 0 too
HEAD_BOX = [Vector((dx, 0.0, dz)) for dx in (-0.02, 0.0, 0.02) for dz in (-0.02, 0.0, 0.02)]


def world_bvh():
    dg = bpy.context.evaluated_depsgraph_get()
    verts, polys, owner = [], [], []
    for o in bpy.data.objects:
        if o.type != "MESH" or o.users_collection[0].name == "backdrop":
            continue
        if any(o.name.startswith(s) for s in SEE_THROUGH) or o.get("decal"):
            continue
        ev = o.evaluated_get(dg)
        me = ev.to_mesh()
        mw = o.matrix_world
        base = len(verts)
        verts.extend(mw @ v.co for v in me.vertices)
        for p in me.polygons:
            polys.append([base + i for i in p.vertices])
            owner.append(o.name)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, polys, epsilon=0.0), owner


def screen_frame(name):
    """Corners of a single-quad instrument object -> origin, u axis, v axis (world)."""
    o = bpy.data.objects[name]
    me = o.data
    uv = me.uv_layers["UVMap"].data
    # map UV corners to world positions (plane_uv writes uv (0,0),(1,0),(1,1),(0,1) on the 4 loops)
    by_uv = {}
    for p in me.polygons:
        for li in p.loop_indices:
            v = me.loops[li].vertex_index
            by_uv[(round(uv[li].uv.x), round(uv[li].uv.y))] = o.matrix_world @ me.vertices[v].co
    o00, o10, o01 = by_uv[(0, 0)], by_uv[(1, 0)], by_uv[(0, 1)]
    return o00, o10 - o00, o01 - o00


def test(eye_offsets, nu=24, nv=10):
    bvh, owner = world_bvh()
    targets = {}
    if "cluster_screen" in bpy.data.objects:
        o, U, Vv = screen_frame("cluster_screen")
        for reg, (u0, v0, u1, v1) in CLUSTER_REGIONS.items():
            pts = [o + U * (u0 + (u1 - u0) * (i + 0.5) / nu) + Vv * (v0 + (v1 - v0) * (j + 0.5) / nv)
                   for i in range(nu) for j in range(nv)]
            targets[f"cluster:{reg}"] = ("cluster_screen", pts)
    for ob in bpy.data.objects:  # any physical round gauge still in the model
        if ob.name.startswith("gauge_face_"):
            me = ob.data
            pts = [ob.matrix_world @ v.co for v in me.vertices]
            c = sum(pts, Vector()) / len(pts)
            pts = [c.lerp(p, f) for p in pts for f in (0.3, 0.6, 0.9)] + [c]
            targets[f"gauge:{ob.name}"] = (ob.name, pts)
    res = {}
    for key, (tname, pts) in targets.items():
        per_eye = []
        blockers = {}
        for off in eye_offsets:
            eye = BI.EYE + off
            occ = 0
            for p in pts:
                d = p - eye
                L = d.length
                hit = bvh.ray_cast(eye, d.normalized(), L - 0.004)
                if hit[0] is not None and owner[hit[2]] != tname:
                    occ += 1
                    blockers[owner[hit[2]]] = blockers.get(owner[hit[2]], 0) + 1
            per_eye.append(occ / len(pts))
        res[key] = {"samples": len(pts), "occluded_nominal": per_eye[len(eye_offsets) // 2] if len(eye_offsets) > 1 else per_eye[0],
                    "occluded_headbox_max": max(per_eye), "blockers": dict(sorted(blockers.items(), key=lambda kv: -kv[1])[:6])}
    return res


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--report", default="")
    p.add_argument("--lod", type=int, default=0)
    p.add_argument("--rake", type=float, default=None, help="default: exterior glass_interface.json rake")
    a = p.parse_args(argv)
    sys_argv = sys.argv
    sys.argv = [sys_argv[0], "--", "--out", os.path.join(BI.REPO, "artifacts")] +         (["--rake", str(a.rake)] if a.rake is not None else []) + ["--lod", str(a.lod), "--no-backdrop"]
    ba = BI.parse_args()
    sys.argv = sys_argv
    BI.build(ba)
    res = test(HEAD_BOX)
    fail = []
    for k, r in res.items():
        if r["occluded_nominal"] > 0.0 or r["occluded_headbox_max"] > MAX_HEAD_OCCLUSION:
            fail.append(k)
    out = {"eye_point": list(BI.EYE), "head_box_m": 0.02, "lod": a.lod, "rake_deg": BI.RAKE, "results": res,
           "verdict": "FAIL" if fail else "PASS", "failed": fail}
    print("SIGHTLINE", json.dumps(out, indent=1))
    if a.report:
        os.makedirs(os.path.dirname(os.path.abspath(a.report)), exist_ok=True)
        json.dump(out, open(a.report, "w"), indent=2)
    if fail:
        print("SIGHTLINE FAIL:", ", ".join(fail))
        sys.exit(1)
    print("SIGHTLINE PASS")


if __name__ == "__main__":
    main()
