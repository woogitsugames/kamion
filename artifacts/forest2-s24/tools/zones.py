"""forest2-s24: broadleaf share of the canopy trees of the pine stands, inside / in the 30 m edge zone (dry run, no
roads: the edge zone is the forest outline only).  python zones.py dk65-05"""
import collections
import json
import sys
from pathlib import Path

import numpy as np
import shapely
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze as A  # noqa: E402
from streetscape import paved as PV  # noqa: E402
from streetscape import vegetation as VG  # noqa: E402

for rid in sys.argv[1:]:
    res, trees, _ = A.run(rid)
    rdir = A.REPO / "Data" / "Regions" / rid
    reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    org = np.array([float(reg["origin"]["x"]), float(reg["origin"]["y"])])
    src = json.loads((rdir / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
    polys = [shapely.make_valid(PV._poly_local(f["geometry"]["coordinates"], org)) for f in src["bdot10k"]["OT_PTLZ_A"]]
    inner = shapely.union_all(polys).buffer(-VG.CHM_EDGE_ZONE_M)
    for fk in ("conifer", "mixed"):
        can = [t for t in trees if t.get("fk") == fk and A.role(t) == "canopy"]
        if not can:
            continue
        P = np.array([[t["e"], t["n"]] for t in can])
        ins = shapely.contains_xy(inner, P[:, 0], P[:, 1])
        for name, m in (("inside", ins), ("edge zone", ~ins)):
            c = collections.Counter(t["p"][5:] for t, k in zip(can, m) if k)
            n = sum(c.values())
            bl = sum(v for k, v in c.items() if k in ("birch", "alder", "maple", "linden", "birchyoung"))
            print(rid, fk, name, n, "broadleaf", round(bl / max(n, 1), 3), {k: round(v / max(n, 1), 3) for k, v in c.most_common()})
