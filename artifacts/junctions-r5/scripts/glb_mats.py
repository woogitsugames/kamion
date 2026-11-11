"""glb_mats.py <world dir A> <world dir B> [low]: per chunk, (node, material) primitives added / removed (draw budget)."""
import json, struct, sys, glob, os, collections
def mats(d, low):
    out = {}
    for f in sorted(glob.glob(d + "/chunk_*_*.glb")):
        if f.endswith(".low.glb") != low:
            continue
        b = open(f, "rb").read()
        jl = struct.unpack("<I", b[12:16])[0]
        js = json.loads(b[20:20 + jl])
        s = set()
        for node in js["nodes"]:
            if "mesh" in node:
                for prim in js["meshes"][node["mesh"]]["primitives"]:
                    s.add((node["name"], js["materials"][prim["material"]]["name"] if "material" in prim else "?"))
        out[os.path.basename(f).split(".")[0]] = s
    return out
low = len(sys.argv) > 3
A, B = mats(sys.argv[1], low), mats(sys.argv[2], low)
add, rem = collections.Counter(), collections.Counter()
for k in sorted(B):
    a, b = A.get(k, set()), B[k]
    for x in sorted(b - a):
        add[x] += 1
    for x in sorted(a - b):
        rem[x] += 1
    if b - a or a - b:
        print(k, "+", sorted(b - a), "-", sorted(a - b))
print("added", dict(add)); print("removed", dict(rem))
