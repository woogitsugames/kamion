"""Track A6 (exterior) — validate the exported TRAKT exterior FBX files against truck_exterior_manifest.json.

    blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/exterior/check_export.py -- \
        [--manifest art-source/truck/exterior/export/truck_exterior_manifest.json]

Per LOD (round trip through the FBX importer with the project axis settings): file exists; every manifest object is
present with the same triangle count and material slots; triangle budget (TRI_LIMIT of a6_export.py); every mesh
with a baked slot (Paint/Trim/Metal/Lights) has the 'Atlas' UV; pivots of the rig parts (wheels, steering knuckles,
doors, wipers, mirrors, cab) land where the manifest says, read from the RAW FBX node transforms (Unity = raw with X negated,
relative to the root; tolerance 1 mm) - Blender's FBX importer is not trusted for this; the hierarchy must be flat;
wheel pivots sit on the axle lines (rear z = 0, front z = wheelbase, height = static wheel centre). Textures: every
path exists, is a power-of-two square and has the size the manifest states. Exit code 1 on any failure.
"""
import json
import os
import sys

import math

import bpy
from mathutils import Euler, Matrix, Vector

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
TRI_LIMIT = {"LOD0": 100000, "LOD1": 45000, "LOD2": 15500, "LOD3": 6000}   # = a6_export.TRI_LIMIT
BAKED_MATS = ("MI_Ext_Paint", "MI_Ext_Trim", "MI_Ext_Metal", "MI_Ext_Lights")


def raw_fbx_globals(path):
    """Parse the binary FBX (Blender's own parser) and compose the node transforms exactly as an FBX reader does
    (Lcl Translation * PreRotation * Lcl Rotation (XYZ) * Lcl Scaling, parents via OO connections).
    -> {name: (global 4x4 in raw FBX space, parent name or None)}. Unity = raw with X negated."""
    from io_scene_fbx import parse_fbx
    root, _ver = parse_fbx.parse(path)

    def find(el, name):
        return [e for e in el.elems if e.id == name]

    def props(el):
        out = {}
        for p70 in find(el, b"Properties70"):
            for p in p70.elems:
                out[p.props[0].decode()] = p.props[4:]
        return out
    models = {}
    for e in find(root, b"Objects")[0].elems:
        if e.id == b"Model":
            models[e.props[0]] = (e.props[1].split(b"\x00")[0].decode(), props(e))
    par = {}
    for c in find(root, b"Connections")[0].elems:
        if c.props[0] == b"OO" and c.props[1] in models and c.props[2] in models:
            par[c.props[1]] = c.props[2]

    def local(pr):
        t = Vector(pr.get("Lcl Translation", (0, 0, 0)))
        r = Euler([math.radians(a) for a in pr.get("Lcl Rotation", (0, 0, 0))], "XYZ").to_matrix().to_4x4()
        q = Euler([math.radians(a) for a in pr.get("PreRotation", (0, 0, 0))], "XYZ").to_matrix().to_4x4()
        sc = pr.get("Lcl Scaling", (1, 1, 1))
        return Matrix.Translation(t) @ q @ r @ Matrix.Diagonal((*sc, 1))

    def glob(uid):
        m = local(models[uid][1])
        return glob(par[uid]) @ m if uid in par else m
    return {models[u][0]: (glob(u), models[par[u]][0] if u in par else None) for u in models}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    man = argv[argv.index("--manifest") + 1] if "--manifest" in argv else os.path.join(
        REPO, "art-source", "truck", "exterior", "export", "truck_exterior_manifest.json")
    m = json.load(open(man, encoding="utf-8"))
    wb = -m["origin"]["a2_frame"][1]
    errors, notes = [], []
    for lod, info in sorted(m["lods"].items()):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path = os.path.join(REPO, info["file"])
        if not os.path.exists(path):
            errors.append(f"{lod}: missing {info['file']}")
            continue
        bpy.ops.import_scene.fbx(filepath=path)     # default axes: raw FBX (Y up) -> Blender (x, -z, y)
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
            if o.type == "MESH":
                me = o.data
                me.calc_loop_triangles()
                n = len(me.loop_triangles)
                total += n
                if n != oi["tris"]:
                    errors.append(f"{lod}: {name} has {n} tris, manifest {oi['tris']}")
                mats = [s.material.name.split(".")[0] for s in o.material_slots if s.material]
                if sorted(mats) != sorted(oi["materials"]):
                    errors.append(f"{lod}: {name} materials {mats} != manifest {oi['materials']}")
                if any(x in BAKED_MATS for x in mats) and "Atlas" not in me.uv_layers:
                    errors.append(f"{lod}: {name} has a baked slot but no 'Atlas' UV")
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
                zr = 0.0 if role[6] == "R" else wb
                if abs(u[2] - zr) > 0.002 or abs(u[1] - 0.5) > 0.03:
                    errors.append(f"{lod}: {name} pivot {u} not on the {'rear' if zr == 0 else 'front'} axle")
        if total > TRI_LIMIT.get(lod, 1e9):
            errors.append(f"{lod}: {total} tris > budget {TRI_LIMIT[lod]}")
        if total != info["tris_total"]:
            errors.append(f"{lod}: total {total} != manifest {info['tris_total']}")
        for e in info.get("empties", {}):
            if e not in objs:
                errors.append(f"{lod}: empty {e} missing")
        notes.append(f"{lod}: {total} tris, {len(info['objects'])} objects OK" if total <= TRI_LIMIT.get(lod, 1e9)
                     else f"{lod}: {total} tris")
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
    for n in notes:
        print("CHECK", n)
    for e in errors:
        print("ERROR", e)
    print("EXTERIOR EXPORT CHECK:", "PASS" if not errors else f"FAIL ({len(errors)})")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
