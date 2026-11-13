"""Per-chunk material diff of a layer between two world dirs. usage: primdiff.py baseDir nowDir [node-filter]"""
import json, struct, sys, glob, os
def mats(fn, flt):
    f = open(fn, "rb"); f.read(12); n, _ = struct.unpack("<I4s", f.read(8)); g = json.loads(f.read(n))
    names = [m.get("name") for m in g.get("materials", [])]; out = {}
    for nd in g["nodes"]:
        if "mesh" in nd and flt in nd.get("name", ""):
            for p in g["meshes"][nd["mesh"]]["primitives"]:
                out[(nd["name"], names[p["material"]])] = g["accessors"][p["indices"]]["count"] // 3
    return out
b, n = sys.argv[1], sys.argv[2]; flt = sys.argv[3] if len(sys.argv) > 3 else "building"
tot = 0
for fn in sorted(glob.glob(os.path.join(n, "chunk_*.glb"))):
    base = os.path.join(b, os.path.basename(fn))
    a, c = (mats(base, flt) if os.path.exists(base) else {}), mats(fn, flt)
    add = sorted(k for k in c if k not in a); rem = sorted(k for k in a if k not in c)
    if add or rem:
        tot += len(add) - len(rem)
        print(os.path.basename(fn), "+", [f"{k[0]}/{k[1]}:{c[k]}" for k in add], "-", [f"{k[0]}/{k[1]}:{a[k]}" for k in rem])
print("net prims", tot)
