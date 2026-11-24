"""forest2-s24 (ADR 0339 round 2): vegetation + forest HLOD of a tile from the canopy height model without the road /
building clearance (no world build) - species shares by stand category and role, prototype scales, HLOD triangles.

    uv run --project tools/worldgen python artifacts/forest2-s24/tools/analyze.py dk65-05 [--out name]
"""
import collections
import json
import sys
import time
from pathlib import Path

import numpy as np
import shapely
import yaml

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from roads.profile import load_heightfield  # noqa: E402
from streetscape import forest_chm as FCH  # noqa: E402
from streetscape import forest_hlod as FH  # noqa: E402
from streetscape import vegetation as VG  # noqa: E402

META = json.loads((REPO / "art-source/world/vegetation/trees_meta.json").read_text(encoding="utf-8"))["trees"]


def role(t):
    s = str(t.get("src", ""))
    return "edge" if s.endswith(":edge") else "under" if s.endswith(":under") else "floor" if s.endswith(":floor") else "canopy"


def run(rid):
    rdir = REPO / "Data" / "Regions" / rid
    reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    org = np.array([float(reg["origin"]["x"]), float(reg["origin"]["y"])])
    hf = load_heightfield(json.loads((rdir / "terrain.json").read_text(encoding="utf-8")), REPO, org)
    src = json.loads((rdir / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
    src = {"bdot10k": {**{k: [] for k in src["bdot10k"]}, "OT_PTLZ_A": src["bdot10k"]["OT_PTLZ_A"]}, "osm": {"nodes": [], "areas": []}}
    chm = FCH.load(rid, org)
    rep = {}
    t0 = time.time()
    trees, forests = VG.place(src, org, hf, hf.z, np.zeros(hf.z.shape, bool), rep, [], chm=chm, field_plants_on=False)
    t1 = time.time()
    fm = rep.pop("_forest_mix")
    hrep = {}
    cells = FH.build(trees, fm, shapely.Polygon(), lambda e, n: hf.sample(e, n), float(reg["bbox"]["width_m"]) / 2, hrep, chm=chm)
    t2 = time.time()
    ft = [t for t in trees if t.get("fk")]
    out = {"region": rid, "seconds": {"place": round(t1 - t0, 1), "hlod": round(t2 - t1, 1)}, "trees": len(trees),
           "hlod": hrep.get("forest_hlod"), "forest_chm": rep.get("forest_chm"), "by_category": {}}
    for fk in ("conifer", "mixed", "broadleaf"):
        can = [t for t in ft if t["fk"] == fk and role(t) == "canopy"]
        if not can:
            continue
        d = {"canopy_trees": len(can)}
        for r in ("canopy", "edge", "under"):
            c = collections.Counter(t["p"][5:] for t in ft if t["fk"] == fk and role(t) == r)
            n = sum(c.values())
            d[r + "_share"] = {k: round(v / max(n, 1), 3) for k, v in c.most_common()}
        sc = collections.defaultdict(list)
        for t in can:
            sc[t["p"][5:]].append(t["h"] / META[f"{t['p']}_{t['v']}"]["href_m"])
        d["canopy_scale"] = {k: {"p50": round(float(np.median(v)), 2), "p99": round(float(np.percentile(v, 99)), 2),
                                 "max": round(float(np.max(v)), 2), "share_gt_1.45": round(float(np.mean(np.array(v) > 1.45)), 3)}
                             for k, v in sc.items()}
        h = np.array([t["h"] for t in can])
        d["canopy_h_m"] = {k: round(float(np.percentile(h, q)), 1) for k, q in (("p10", 10), ("p50", 50), ("p90", 90), ("max", 100))}
        out["by_category"][fk] = d
    return out, trees, cells


if __name__ == "__main__":
    args = sys.argv[1:]
    name = args[args.index("--out") + 1] if "--out" in args else "analyze"
    for rid in [a for a in args if not a.startswith("--") and a != name]:
        res, _, _ = run(rid)
        p = REPO / "artifacts" / "forest2-s24" / f"{name}_{rid}.json"
        p.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(res, indent=1))
