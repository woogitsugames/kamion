"""dbg_wall.py: side parameters of chain c:w1101181473 (L) along its first 60 m - the lone wall of r2_fork_link_eye."""
import sys
sys.path.insert(0, "tools/worldgen")
import numpy as np
from roads import pipeline
from roads.network import side_params
w = pipeline.build("bialystok-industrial-c")
c = next(c for c in w.net.chains if c.id == "c:w1101181473:10076968415-1847263305")
wl = c.meta.get("walled")
d = c.side["L"]
print("t_a", c.t_a, "len", c.length, "keys", list(d.keys()))
n_ = len(c.line.s)
print("t_b", c.t_b)
for i in range(max(0, n_ - 150), n_, 4):
    s = c.line.s[i]
    p = c.line.offset_point(s, c.hw[i])
    print(f"s {s:6.1f} xy {p[0]:7.1f} {p[1]:7.1f} z {c.z[i]:.2f} br {int(c.bridge[i])} wl {int(wl[i]) if wl is not None else -1} kind {d['kind'][i]} h {d['h'][i]:.2f} w {d['w'][i]:.2f} depth {d['depth'][i]:.2f} mat {d['mat'][i]} verge {d['verge'][i] if 'verge' in d else None} zg {float(w.hf.sample(np.array([p[0]]), np.array([p[1]]))[0]):.2f}")
