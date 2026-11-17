"""Validate the exported curtainsider trailer FBX files against trailer_manifest.json (same checks as the TRAKT
exterior validator, tools/blender/truck/exterior/check_export.py).

    blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/trailer/check_export.py -- \
        [--manifest art-source/truck/trailer/export/trailer_manifest.json]

Per LOD: file exists; every manifest object is present (FBX round trip) with the same triangle count and material
slots; triangle budget (LOD0 <= 60k, LOD1 <= 25k, LOD2 <= 8k); every mesh with a baked slot has the 'Atlas' UV and the
'Data' UV (light groups); pivots read from the RAW FBX node transforms (Unity = raw with X negated, relative to the
root; 1 mm); flat hierarchy; wheel pivots on the physics axle lines (positionZ, trackWidth / 2, tyre radius) and leg
pivots on the physics landing-gear line. Textures: every path exists, power-of-two square, size as in the manifest.
physics_crosscheck: every row must match except the rows listed in ALLOWED_MISMATCH (documented, owner decision).
Exit code 1 on any failure.
"""
import json
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "exterior")))
from check_export import raw_fbx_globals  # noqa: E402  (raw FBX transform parser of the TRAKT validator)
sys.path.insert(0, HERE)
import uv_wheel_audit as U  # noqa: E402  (UV rasteriser + red threshold, review s23 P1)

REPO = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
TRI_LIMIT = {"LOD0": 90000, "LOD1": 25000, "LOD2": 8000}       # = trailer_export.TRI_LIMIT
BAKED_MATS = ("MI_Trl_Paint", "MI_Trl_Curtain", "MI_Trl_Trim", "MI_Trl_Metal", "MI_Trl_Lights")
ALLOWED_MISMATCH = ("tyre radius: mesh free", "cargo front z", "cargo height", "combination length")


def wheel_uv_rules(lod, objs, m, errors, notes, res=1024):
    """Review s23 P1 (red rims): (a) every LOD: the 'Atlas' islands of the WHEEL_* objects share no texel (strict
    raster at 1024 px) with any other object in the Metal and Trim slots - the wheels are baked from their own proxy and
    merged only where no static island is; (b) LOD0: no wheel Metal texel is red in T_Trl_Metal_C of any tier
    (R - G > 0.2, docs/06 §5; sampled at the texel under every covered 1024 px cell)."""
    import numpy as np
    for mname in ("MI_Trl_Metal", "MI_Trl_Trim"):
        wheel = np.zeros((res, res), dtype=bool)
        other = np.zeros((res, res), dtype=bool)
        for o in objs.values():
            if o.type != "MESH" or "Atlas" not in o.data.uv_layers:
                continue
            names = [s.material.name.split(".")[0] if s.material else "" for s in o.material_slots]
            if mname not in names:
                continue
            cov, _ = U.raster(o.data, names.index(mname), res)
            if o.name.startswith("WHEEL_"):
                wheel |= cov
            else:
                other |= cov
        ov = int((wheel & other).sum())
        if ov:
            errors.append(f"{lod}: {mname} wheel UV islands share {ov} texels (@{res}) with other objects")
        notes.append(f"{lod}: {mname} wheel texels {int(wheel.sum())} (@{res}), shared with other objects {ov}")
        if lod != "LOD0" or mname != "MI_Trl_Metal":
            continue
        ys, xs = np.nonzero(wheel)
        for tier, t in sorted(m["textures"]["Metal"]["C"].items()):
            im = bpy.data.images.load(os.path.join(REPO, t["path"]))
            w, h = im.size
            a = np.empty(w * h * 4, dtype=np.float32)
            im.pixels.foreach_get(a)
            bpy.data.images.remove(im)
            px = a.reshape(h, w, 4)[(ys * h) // res, (xs * w) // res]
            red = int(((px[:, 0] - px[:, 1]) > U.RED_DELTA).sum())
            if red:
                errors.append(f"LOD0: {red} of {len(ys)} wheel Metal texels red in {t['path']} (R-G > {U.RED_DELTA})")
            notes.append(f"LOD0: wheel Metal texels red in {tier} T_Trl_Metal_C: {red} / {len(ys)}")


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    man = argv[argv.index("--manifest") + 1] if "--manifest" in argv else os.path.join(
        REPO, "art-source", "truck", "trailer", "export", "trailer_manifest.json")
    m = json.load(open(man, encoding="utf-8"))
    phys = json.load(open(os.path.join(REPO, "game", "Assets", "_Project", "Vehicle", "Physics", "Definitions", "Data",
                                       "curtainsider_tridem_13_6.trailer.json"), encoding="utf-8"))
    axles = [a["positionZ"] for a in phys["axles"]]
    half = phys["axles"][0]["trackWidth"] / 2
    lg = phys["landingGear"]
    errors, notes = [], []
    for lod, info in sorted(m["lods"].items()):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path = os.path.join(REPO, info["file"])
        if not os.path.exists(path):
            errors.append(f"{lod}: missing {info['file']}")
            continue
        bpy.ops.import_scene.fbx(filepath=path)
        bpy.context.view_layer.update()
        objs = {o.name: o for o in bpy.data.objects}
        raw = raw_fbx_globals(path)
        if info["root"] not in raw:
            errors.append(f"{lod}: root {info['root']} missing")
            continue
        total = 0
        for name, oi in info["objects"].items():
            o = objs.get(name)
            if o is None:
                errors.append(f"{lod}: object {name} missing")
                continue
            me = o.data
            me.calc_loop_triangles()
            n = len(me.loop_triangles)
            total += n
            if n != oi["tris"]:
                errors.append(f"{lod}: {name} has {n} tris, manifest {oi['tris']}")
            mats = [s.material.name.split(".")[0] for s in o.material_slots if s.material]
            if sorted(mats) != sorted(oi["materials"]):
                errors.append(f"{lod}: {name} materials {mats} != manifest {oi['materials']}")
            if any(x in BAKED_MATS for x in mats) and not {"Atlas", "Data"} <= set(me.uv_layers.keys()):
                errors.append(f"{lod}: {name} lacks the 'Atlas' / 'Data' UV")
            u = oi["pivot_unity_vehicle"]
            g, par = raw.get(name, (None, None))
            if g is None:
                errors.append(f"{lod}: {name} not in the raw FBX node list")
                continue
            if par != info["root"]:
                errors.append(f"{lod}: {name} FBX parent {par}, expected the root (flat hierarchy)")
            t, r0 = g.translation, raw[info["root"]][0].translation
            got = (-(t.x - r0.x), t.y - r0.y, t.z - r0.z)
            d = max(abs(got[i] - u[i]) for i in range(3))
            if d > 0.001:
                errors.append(f"{lod}: {name} pivot (Unity, raw FBX) {tuple(round(c, 4) for c in got)} != manifest "
                              f"{u} ({d:.4f} m)")
            role = oi["role"]
            if role.startswith("WHEEL_"):
                ax = axles[int(role[6]) - 1]
                if abs(u[2] - ax) > 1e-3 or abs(abs(u[0]) - half) > 1e-3 or abs(u[1] - 0.515) > 1e-3:
                    errors.append(f"{lod}: {name} pivot {u} not on axle {role[6]} (z {ax}, x +-{half}, y 0.515)")
            if role.startswith("LEG_"):
                if abs(u[2] - lg["positionZ"]) > 1e-3 or abs(abs(u[0]) - lg["halfTrack"]) > 1e-3 or \
                        abs(u[1] - lg["raisedFootY"]) > 1e-3:
                    errors.append(f"{lod}: {name} pivot {u} not on the landing-gear line")
        wheel_uv_rules(lod, objs, m, errors, notes)
        if total > TRI_LIMIT.get(lod, 1e9):
            errors.append(f"{lod}: {total} tris > budget {TRI_LIMIT[lod]}")
        if total != info["tris_total"]:
            errors.append(f"{lod}: total {total} != manifest {info['tris_total']}")
        for e in info.get("empties", {}):
            if e not in objs:
                errors.append(f"{lod}: empty {e} missing")
        notes.append(f"{lod}: {total} tris (budget {TRI_LIMIT[lod]}), {len(info['objects'])} objects")
    for slot, kinds in m["textures"].items():
        for kind, tiers in kinds.items():
            for tier, t in tiers.items():
                p = os.path.join(REPO, t["path"])
                if not os.path.exists(p):
                    errors.append(f"texture missing: {t['path']}")
                    continue
                im = bpy.data.images.load(p)
                w, h = im.size
                if w != h or w & (w - 1) or w != t["size"]:
                    errors.append(f"texture {t['path']}: {w}x{h}, manifest {t['size']} (need pow2 square)")
                bpy.data.images.remove(im)
    for r in m["physics_crosscheck"].get("rows", []):
        if not r["match"]:
            if r["item"].startswith(ALLOWED_MISMATCH):
                notes.append(f"documented mismatch: {r['item']}: art {r['art']} / physics {r['physics']}")
            else:
                errors.append(f"physics_crosscheck: {r['item']}: art {r['art']} / physics {r['physics']}")
    for n in notes:
        print("CHECK", n)
    for e in errors:
        print("ERROR", e)
    print("TRAILER EXPORT CHECK:", "PASS" if not errors else f"FAIL ({len(errors)})")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
