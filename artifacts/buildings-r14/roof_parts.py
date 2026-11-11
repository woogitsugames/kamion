"""ADR 0107: MultiRoof decomposition dump (parts in the main frame, sizes) for all houses or one id.
    uv run --project tools/worldgen python artifacts/buildings-r14/roof_parts.py [id-substring]"""
import json, sys
from collections import Counter
from pathlib import Path
REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import numpy as np, shapely, yaml
from streetscape import buildings_mesh as BM, facade_kit as FK, roofs as RF
rdir = REPO / "Data" / "Regions" / "bialystok-industrial-c"
reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
fc = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
blds = BM.load(fc, (reg["origin"]["x"], reg["origin"]["y"]), [])
sub = sys.argv[1] if len(sys.argv) > 1 else None
small = Counter()
for b in blds:
    if b["typ"] != "house" or (sub and sub not in b["id"]):
        continue
    poly = b["poly"]
    c, eu, hu, hv = RF._frame(poly)
    ev = np.array([-eu[1], eu[0]])
    parts = RF.decompose(poly, c, eu, ev)
    if not parts or len(parts) < 2:
        continue
    dims = [(round(p[1] - p[0], 2), round(p[3] - p[2], 2)) for p in parts]
    mn = min(min(d) for d in dims[1:])
    small["<1" if mn < 1 else "<1.5" if mn < 1.5 else "<2" if mn < 2 else "<3" if mn < 3 else ">=3"] += 1
    if sub:
        print(b["id"], "area", round(poly.area, 1), "frame", round(2 * hu, 2), round(2 * hv, 2))
        for p, d in zip(parts, dims):
            print("  part", [round(x, 2) for x in p], d)
        ring = np.asarray(poly.exterior.coords)[:-1] - c
        print("  ring uv", np.round(np.column_stack([ring @ eu, ring @ ev]), 2).tolist())
print(dict(small))
