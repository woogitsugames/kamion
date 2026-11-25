"""fields2-s24: lone trees of the open fields - trees / shrubs inside BDOT OT_PTTR_A (>= 2 ha polygons) whose nearest
neighbour stands more than 15 m away, by source. python lone_trees.py <tile> [instances dir]"""
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import yaml
from scipy.spatial import cKDTree

sys.path.insert(0, "tools/worldgen")
from streetscape import sources as SR  # noqa: E402
from streetscape import vegetation as VG  # noqa: E402

tile = sys.argv[1]
idir = sys.argv[2] if len(sys.argv) > 2 else f"Data/raw/derived/{tile}/world"
d = Path("Data/Regions") / tile
r = yaml.safe_load((d / "region.yaml").read_text(encoding="utf-8"))
ox, oy = r["origin"]["x"], r["origin"]["y"]
src = SR.load(tile)
polys = []
for f in (src.get("bdot10k") or {}).get("OT_PTTR_A") or []:
    g = VG.shapely.make_valid(VG.PV._poly_local(f["geometry"]["coordinates"], (ox, oy)))
    if g.area >= VG.FIELD_PLANT_MIN_M2:
        polys.append(g)
area = VG.shapely.union_all(polys)
T = []
for f in glob.glob(f"{idir}/instances_*.json"):
    for i in json.load(open(f, encoding="utf8"))["instances"]:
        if str(i.get("p", "")).startswith("tree_") and i["p"] != "tree_floor":
            T.append((i["e"], i["n"], re.sub(r"\{?[0-9A-Fa-f\-]{8,}\}?|\d+", "#", str(i.get("src", ""))), i["p"]))
P = np.array([(a, b) for a, b, _, _ in T])
ins = VG.shapely.contains_xy(area, P[:, 0], P[:, 1])
dd, _ = cKDTree(P).query(P, k=2)
lone = ins & (dd[:, 1] > 15.0)
print(tile, "fields km2", round(area.area / 1e6, 2), "trees in fields", int(ins.sum()), "lone (> 15 m to the next)", int(lone.sum()),
      "per km2", round(lone.sum() / max(area.area / 1e6, 1e-9), 1))
print(" lone by source", Counter(T[i][2] for i in np.flatnonzero(lone)).most_common(8))
print(" lone by prototype", Counter(T[i][3] for i in np.flatnonzero(lone)).most_common(8))
