"""Track A6 — validate the exported cab-interior FBX files against the import manifest (round trip in Blender).

    blender -b --factory-startup --python-exit-code 1 --python tools/blender/truck/interior/check_export.py -- \
        [--manifest art-source/truck/interior/export/cab_interior_manifest.json]

Checks per LOD: file exists; every manifest object is present with the same triangle count and material slots;
UV sets UVMap/Bake/Data0/Data1 and the 'Col' colour attribute exist on every mesh; LOD0 <= 90k, LOD1 <= 45k,
LOD2 <= 22k triangles; empties (EYE_POINT, ...) land where the manifest says (re-imported with the same axis
settings; compared in raw FBX space = Unity with X negated); the Unity-side check is the A7 importer's job); every texture
path in the manifest exists and has power-of-two square size. Exit code 1 on any failure.
"""
import json
import os
import sys

import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", ".."))
LIMIT = {"LOD0": 90000, "LOD1": 45000, "LOD2": 22000}


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    man = argv[argv.index("--manifest") + 1] if "--manifest" in argv else os.path.join(
        REPO, "art-source", "truck", "interior", "export", "cab_interior_manifest.json")
    m = json.load(open(man, encoding="utf-8"))
    errors = []
    for lod, info in sorted(m["lods"].items()):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        path = os.path.join(REPO, info["file"])
        if not os.path.exists(path):
            errors.append(f"{lod}: missing {info['file']} (regenerate with a6_export.py)")
            continue
        bpy.ops.import_scene.fbx(filepath=path, axis_forward="Z", axis_up="Y")
        objs = {o.name: o for o in bpy.data.objects}
        total = 0
        for name, oi in info["objects"].items():
            o = objs.get(name)
            if o is None or o.type != "MESH":
                errors.append(f"{lod}: object {name} missing")
                continue
            me = o.data
            me.calc_loop_triangles()
            t = len(me.loop_triangles)
            total += t
            if t != oi["tris"]:
                errors.append(f"{lod}: {name} has {t} tris, manifest {oi['tris']}")
            uvs = [u.name for u in me.uv_layers]
            for need in ("UVMap", "Bake", "Data0", "Data1"):
                if need not in uvs:
                    errors.append(f"{lod}: {name} lacks UV set {need} ({uvs})")
            if not me.color_attributes:
                errors.append(f"{lod}: {name} has no vertex colours")
            mats = [x.name.split(".")[0] for x in me.materials]
            if mats != oi["materials"]:
                errors.append(f"{lod}: {name} materials {mats} != {oi['materials']}")
        if total > LIMIT[lod]:
            errors.append(f"{lod}: {total} tris > budget {LIMIT[lod]}")
        root = objs.get(info["root"])
        for e, upos in info["empties_unity_local"].items():
            nm = e if lod == "LOD0" else f"{e}_{lod}"
            o = objs.get(nm)
            if o is None or root is None:
                errors.append(f"{lod}: empty {nm} missing")
                continue
            # FBX space (raw, axis conversion baked at export): (fx, fy, fz) = (-ux, uy, uz), because Unity negates
            # X when it converts the right-handed FBX into its left-handed frame
            loc = root.matrix_world.inverted() @ o.matrix_world.translation   # local to the root = FBX space
            exp = (-upos[0], upos[1], upos[2])
            if max(abs(a - b) for a, b in zip(loc, exp)) > 1e-3:
                errors.append(f"{lod}: {nm} at {tuple(round(v, 4) for v in loc)} expected {exp}")
        print(f"CHECK {lod}: {total} tris, {len(info['objects'])} meshes OK" if not errors else f"CHECK {lod}: done")
    for slot, e in m.get("materials", {}).items():
        for tier, d in e.get("textures", {}).items():
            for k, p in d.items():
                if not isinstance(p, str):
                    continue
                fp = os.path.join(REPO, p)
                if not os.path.exists(fp):
                    errors.append(f"texture missing: {p}")
                    continue
                im = bpy.data.images.load(fp)
                w, h = im.size
                if w != h or w & (w - 1):
                    errors.append(f"texture not a power-of-two square: {p} {w}x{h}")
    if errors:
        print("CHECK FAIL\n  " + "\n  ".join(errors))
        sys.exit(1)
    print("CHECK PASS")


if __name__ == "__main__":
    main()
