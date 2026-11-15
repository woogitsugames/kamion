"""ADR 0202: trace the generated kerb and footway edge along the chain row (every 2 m along, 0.25 m across)."""
import runpy
import sys

import numpy as np

sys.argv = ["probe.py"]
g = runpy.run_path("artifacts/dojfix-0202/probe.py")
P, under, t, west = g["P"], g["under"], g["t"], g["west"]
print("t", t.round(3), "west", west.round(3))
for a in np.arange(-30.0, 22.1, 2.0):
    row = []
    base = P[0, :2] + t * a
    prev = None
    for d in np.arange(7.0, -8.01, -0.25):
        q = base + west * d
        u = [x for x in under(q[0], q[1]) if "lod" not in x[1].lower() or "lod0" in x[1].lower()]
        m = u[0][2] if u else "none"
        if m != prev:
            row.append(f"{d:+.2f}:{m}")
            prev = m
    print(f"a={a:+5.1f} E{base[0]:7.2f} N{base[1]:7.2f} | " + "  ".join(row))
