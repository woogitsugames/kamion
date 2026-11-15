"""List meshes / materials of a generator chunk GLB (JSON header only)."""
import json, struct, sys
for p in sys.argv[1:]:
    with open(p, "rb") as f:
        magic, ver, ln = struct.unpack("<III", f.read(12)); clen, ctype = struct.unpack("<II", f.read(8)); j = json.loads(f.read(clen))
    mats = [m.get("name") for m in j.get("materials", [])]
    print(p, "nodes", len(j.get("nodes", [])), "extras", {k: j.get("extras", {}).get(k) for k in list(j.get("extras", {}))[:8]})
    for n in j.get("nodes", [])[:60]:
        m = j["meshes"][n["mesh"]] if "mesh" in n else None
        print("  ", n.get("name"), n.get("translation"), [mats[pr["material"]] for pr in m["primitives"]][:6] if m else "")
