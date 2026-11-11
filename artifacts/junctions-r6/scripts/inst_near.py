"""inst_near.py E,N,R ...: prop instances of the exported world within R of region-local points (proto, E, N, z, src)."""
import json, sys, glob, math
pts = [tuple(float(v) for v in a.split(",")) for a in sys.argv[1:]]
for f in sorted(glob.glob("Data/raw/derived/bialystok-industrial-c/world/instances_*_*.json")):
    d = json.load(open(f, encoding="utf-8"))
    for it in d["instances"]:
        p = (it["e"], it["n"])
        for e, n, r in pts:
            if p and math.hypot(p[0] - e, p[1] - n) < r:
                print(f[-22:], {k: (v if not isinstance(v, float) else round(v, 2)) for k, v in it.items()})
