"""Map audit r9: OSM road-graph edges within R m of a region-local point (E N [R]).

    python scripts/map-audit-near.py -81 -340 30
"""
import json
import sys
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parents[1]
g = json.loads((REPO / "Data/Regions/bialystok-industrial-c/roads.graph.json").read_text(encoding="utf-8"))
ox, oy = 777995.0, 596223.0
e0, n0 = float(sys.argv[1]), float(sys.argv[2])
R = float(sys.argv[3]) if len(sys.argv) > 3 else 30.0
q = np.array([e0, n0])
out = []
for e in g["edges"]:
    P = np.array(e["geometry"]) - [ox, oy]
    best = 1e9
    for a, b in zip(P[:-1], P[1:]):
        ab = b - a
        t = np.clip(np.dot(q - a, ab) / max(ab @ ab, 1e-9), 0, 1)
        best = min(best, float(np.hypot(*(q - (a + t * ab)))))
    if best < R:
        at = e["attrs"]
        out.append((round(best, 1), e["id"], {k: at[k]["v"] for k in ("highway", "name", "lanes", "oneway", "turn:lanes", "width", "layer", "bridge", "junction") if k in at}))
for o in sorted(out, key=lambda x: x[0]):
    print(*o)
