"""forest2-s24: side elevation of the forest HLOD of one stand (round 1 = KAMION_FOREST_CHM_R2=0 vs round 2) - a quick
look at the top line before the Unity import. No clearance of roads / buildings (as dry_run.py).

    uv run --project tools/worldgen python artifacts/forest2-s24/tools/hlod_profile.py dw671-tykocin-03 165 340 250
"""
import json
import os
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import shapely  # noqa: E402
import yaml  # noqa: E402

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from roads.profile import load_heightfield  # noqa: E402
from streetscape import forest_chm as FCH  # noqa: E402
from streetscape import forest_hlod as FH  # noqa: E402
from streetscape import vegetation as VG  # noqa: E402

rid, ce, cn, r = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), float(sys.argv[4])
rdir = REPO / "Data" / "Regions" / rid
reg = yaml.safe_load((rdir / "region.yaml").read_text(encoding="utf-8"))
org = np.array([float(reg["origin"]["x"]), float(reg["origin"]["y"])])
hf = load_heightfield(json.loads((rdir / "terrain.json").read_text(encoding="utf-8")), REPO, org)
src0 = json.loads((rdir / "generated" / "streetscape_sources.json").read_text(encoding="utf-8"))
half = float(reg["bbox"]["width_m"]) / 2
fig, axes = plt.subplots(2, 1, figsize=(12, 6), dpi=90, sharex=True, sharey=True)
for ax, with_chm in zip(axes, (False, True)):
    src = {"bdot10k": {**{k: [] for k in src0["bdot10k"]}, "OT_PTLZ_A": src0["bdot10k"]["OT_PTLZ_A"]}, "osm": {"nodes": [], "areas": []}}
    os.environ["KAMION_FOREST_CHM_R2"] = "1" if with_chm else "0"
    chm = FCH.load(rid, org)
    rep = {}
    trees, _ = VG.place(src, org, hf, hf.z, np.zeros(hf.z.shape, bool), rep, [], chm=chm, field_plants_on=False)
    cells = FH.build(trees, rep.pop("_forest_mix"), shapely.Polygon(), lambda e, n: hf.sample(e, n), half, {}, chm=chm)
    z0 = float(hf.sample(ce, cn))
    for c in cells.values():
        for k, pr in enumerate(c["prims"]):
            V, T = pr["V"], pr["T"]
            m = (np.abs(V[T][:, :, 0] - ce) < r).all(axis=1) & (np.abs(V[T][:, :, 1] - cn) < r).all(axis=1)
            for tri in V[T[m]]:
                ax.fill(tri[:, 0], tri[:, 2] - z0, color="#2c5a2c" if k == 0 else "#5a8a3a", alpha=0.5 if k else 0.9, lw=0)
    near = [t for t in trees if abs(t["e"] - ce) < r and abs(t["n"] - cn) < r and t.get("fk") and t["h"] > 5]
    ax.scatter([t["e"] for t in near], [t["z"] + t["h"] - z0 for t in near], s=3, color="k", alpha=0.4)
    ax.set_title(("round 2" if with_chm else "round 1 (r5)") + f": HLOD seen from the south, {rid} around ({ce:.0f}, {cn:.0f}); dots = tree tops")
    ax.set_ylim(0, 45)
    ax.set_aspect("equal")
fig.tight_layout()
out = REPO / "artifacts" / "forest2-s24" / f"hlod_profile_{rid}_{ce:.0f}_{cn:.0f}.png"
fig.savefig(out)
print(out)
