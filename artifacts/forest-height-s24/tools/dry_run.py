"""forest-height-s24: vegetation + forest HLOD of a tile with and without the canopy height model, without the road /
building clearance (no world build needed) - tree counts, heights, HLOD triangles. Rough numbers for the ADR; the real
ones come from generated/streetscape_qa.json after build_world.py.

    uv run --project tools/worldgen python artifacts/forest-height-s24/tools/dry_run.py dk65-05
"""
import collections
import json
import sys
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


def run(rid, with_chm):
    rdir = REPO / "Data" / "Regions" / rid
    reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
    org = np.array([float(reg["origin"]["x"]), float(reg["origin"]["y"])])
    hf = load_heightfield(json.loads((rdir / "terrain.json").read_text(encoding="utf-8")), REPO, org)
    src = json.loads((rdir / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
    src = {"bdot10k": {**{k: [] for k in src["bdot10k"]}, "OT_PTLZ_A": src["bdot10k"]["OT_PTLZ_A"]}, "osm": {"nodes": [], "areas": []}}
    chm = FCH.load(rid, org) if with_chm else None
    rep = {}
    blocked = np.zeros(hf.z.shape, bool)
    trees, forests = VG.place(src, org, hf, hf.z, blocked, rep, [], chm=chm, field_plants_on=False)
    fm = rep.pop("_forest_mix")
    half = float(reg["bbox"]["width_m"]) / 2
    hrep = {}
    FH.build(trees, fm, shapely.Polygon(), lambda e, n: hf.sample(e, n), half, hrep, chm=chm)
    can = [t for t in trees if t.get("fk") and not str(t["src"]).endswith((":edge", ":under", ":floor"))]
    h = np.array([t["h"] for t in can])
    out = {"trees": len(trees), "canopy_trees": len(can),
           "canopy_h_m": {k: round(float(np.percentile(h, q)), 1) for k, q in (("p10", 10), ("p50", 50), ("p90", 90), ("max", 100))},
           "canopy_species": dict(collections.Counter(t["p"][5:] for t in can).most_common()),
           "forest_area_ha": round(sum(p.area for p in forests) / 1e4, 2),
           "hlod": hrep.get("forest_hlod"), "forest_chm": rep.get("forest_chm")}
    return out


if __name__ == "__main__":
    for rid in sys.argv[1:]:
        res = {"class_rule": run(rid, False), "chm": run(rid, True)}
        out = REPO / "artifacts" / "forest-height-s24" / f"dry_run_{rid}.json"
        out.write_text(json.dumps(res, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(rid, json.dumps(res, indent=1))
