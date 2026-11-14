"""LOD1 building materials per chunk and per building (who brings which draw). usage: chunkmats.py 6_6 6_7"""
import json, sys
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace
import numpy as np, yaml
from shapely.geometry import box, shape
REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from streetscape import buildings_mesh as BM
R = REPO / "Data" / "Regions" / "bialystok-industrial-c"; ORIGIN = (777995.0, 596223.0); HALF = 1024.0; S = 256.0
import os
LAYER = os.environ.get("LAYER", "buildings_low")
want = set(sys.argv[1:])
fc = json.loads((R / "buildings.geojson").read_text(encoding="utf-8"))
ovr = yaml.safe_load((R / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]
HF = SimpleNamespace(sample=lambda x, y: np.full(np.shape(x), 100.0))
class Buf:
    def __init__(self): self.parts = []
    def add(self, layer, mat, V, UV, T, **kw): self.parts.append((layer, mat, np.asarray(V, float), np.asarray(T).reshape(-1, 3)))
tally = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))
for b in BM.load(fc, ORIGIN, ovr):
    c = b["poly"].centroid
    cs = {f"{int((c.x + dx + HALF) // S)}_{int((HALF - c.y - dy) // S)}" for dx in (-150, 0, 150) for dy in (-150, 0, 150)}
    if not (cs & want): continue
    buf = Buf()
    try: BM.build(buf, [b], HF, None, None, box(-5000, -5000, -4990, -4990), {}, sign_out=[])
    except Exception as e: print("ERR", b["id"], e); continue
    for layer, mat, V, T in buf.parts:
        if layer != LAYER or not len(T): continue
        cen = V[T].mean(1)
        ci = np.floor((cen[:, 0] + HALF) / S).astype(int); cj = np.floor((HALF - cen[:, 1]) / S).astype(int)
        for k in set(zip(ci.tolist(), cj.tolist())):
            tally[f"{k[0]}_{k[1]}"][mat][b["id"] + "/" + b["typ"]] += int(((ci == k[0]) & (cj == k[1])).sum())
for ch in sorted(want):
    print("==", ch, len(tally[ch]), "materials")
    for mat, who in sorted(tally[ch].items()):
        tot = sum(who.values()); top = sorted(who.items(), key=lambda x: -x[1])[:4]
        print(f"  {mat:28} {tot:5} tris, {len(who):2} bldgs: " + ", ".join(f"{k[-28:]}:{v}" for k, v in top))
