import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
w = pipeline.build("bialystok-industrial-c")
for cid in sys.argv[1:]:
    c = next(c for c in w.net.chains if cid in c.id)
    print("==", c.id, "L", round(c.length, 1), "t_a", round(c.t_a, 1), "t_b", round(c.t_b, 1), "abreast", c.meta.get("abreast_of"), {k: v for k, v in c.meta.items() if k in ("walled", "hero", "alongside_m", "fork_shift_m")})
    for s in np.arange(0, min(c.length, 200), 10.0):
        i = c.idx(s)
        print(f"  s {s:5.0f} bridge {int(c.bridge[i])} z {float(c.z[i]):.2f} hw {float(c.hw[i]):.2f} e {float(np.nan_to_num(c.e[i])):+.3f} xy {np.round(c.line.p[i],1)}")
print("rejected", [r for r in w.stats.get("gores", {}).get("rejected", []) if abs(r["xy"][0] + 795) < 45 and abs(r["xy"][1] - 77) < 20])
