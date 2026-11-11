"""ADR 0097: run the house roof planner + roof mesh over every house of the region (no terrain: zref = 0) and count
roof kinds, MultiRoof parts, covering gaps / double faces and failures.
    uv run --project tools/worldgen python artifacts/buildings-r13/roof_scan.py [region]"""
import json
import sys
import traceback
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
import shapely  # noqa: E402
import yaml  # noqa: E402
from streetscape import buildings_mesh as BM  # noqa: E402
from streetscape import facade_kit as FK  # noqa: E402
from streetscape import roofs as RF  # noqa: E402

region = sys.argv[1] if len(sys.argv) > 1 else "bialystok-industrial-c"
rdir = REPO / "Data" / "Regions" / region
reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
fc = json.loads((rdir / "buildings.geojson").read_text(encoding="utf-8"))
ovr = yaml.safe_load((rdir / "overrides.yaml").read_text(encoding="utf-8")) or {}
ovr = ovr.get("overrides", ovr) if isinstance(ovr, dict) else ovr
blds = BM.load(fc, (reg["origin"]["x"], reg["origin"]["y"]), [o for o in ovr if isinstance(o, dict)])
tree = shapely.STRtree([b["poly"] for b in blds])
kinds, parts, bad = Counter(), Counter(), []
for b in blds:
    if b["typ"] != "house":
        continue
    key = b["id"]
    poly, p = b["poly"], b["props"]
    near = [blds[j]["poly"] for j in tree.query(poly.buffer(0.6)) if blds[j] is not b]
    try:
        r = RF.plan(poly, p, float(p.get("height_m") or 6.0), 0.0, lambda s: FK.hfloat(key, s), near, False)
        if r is None:
            kinds["flat"] += 1
            continue
        kinds[f"{type(r).__name__}:{r.kind}"] += 1
        if isinstance(r, RF.MultiRoof):
            parts[len(r.parts)] += 1
            cov = RF.covering(poly, r)
            regs = [f[0] for f in r.faces(RF.OVERHANG + 0.05)]
            uni = shapely.unary_union(regs)
            gap, dbl = cov.difference(uni).area, sum(g.area for g in regs) - uni.area
            if gap > 0.05 or dbl > 0.05:
                bad.append((key, round(gap, 3), round(dbl, 3)))
        acc = BM.Acc()
        RF.build(acc, r, poly, "roof_tiles_red", soffit_mat="soffit_boards", fascia_mat="soffit_boards")
    except Exception:
        bad.append((key, "EXC", traceback.format_exc().splitlines()[-1]))
print("kinds", dict(kinds))
print("multi parts", dict(parts))
print("bad", len(bad), bad[:10])
