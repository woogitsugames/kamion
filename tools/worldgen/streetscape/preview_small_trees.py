"""Offline preview (software rasteriser of preview_kit) of the small garden trees: 4 views per tree, 3 seeds.
Usage: python tools/worldgen/streetscape/preview_small_trees.py <out_dir> [old] [young] [fruit]"""
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO / "tools" / "worldgen"))
from streetscape import plantings as PG  # noqa: E402
from streetscape import plots as PLT  # noqa: E402
from streetscape import preview_kit as PV  # noqa: E402
from streetscape import small_trees as ST  # noqa: E402

out = Path(sys.argv[1])
out.mkdir(parents=True, exist_ok=True)
S = (360, 420)


def views(k, H, dist=9.0):
    return [PV.render(k, (dist * math.cos(a), dist * math.sin(a), 1.7), (0, 0, H * 0.52), fov=40, size=S, low=False)
            for a in (0.3, 1.6, 2.9, 4.6)]


def tris(k):
    return sum(len(t) for t in k.T)


cases = [("linden", 1.25, 4.7, 1.6), ("maple", 1.5, 4.6, 1.3), ("birch", 1.2, 5.6, 1.3), ("ash", 1.4, 5.0, 1.6), ("maple", 1.0, 4.0, 1.3)]
for mode in sys.argv[2:] or ["young", "fruit"]:
    rows = []
    if mode == "young":
        for sp, r, H, cb in cases:
            for key in ("a", "b", "c"):
                k = PLT.Kit()
                f = ST.young_tree(k, (0, 0), 0.0, r, H, cb, sp, PG.HABIT[sp], (sp, key))
                print(sp, key, f, tris(k))
                rows.append(PV.row(views(k, H)))
    elif mode == "old":
        for sp, r, H, cb in cases[:3]:
            k = PLT.Kit()
            PG.garden_tree(k, (0, 0), 0.0, r, H, cb, sp, (sp, "a"), **({"legacy": True} if "legacy" in PG.garden_tree.__code__.co_varnames else {}))
            rows.append(PV.row(views(k, H)))
        k = PLT.Kit()
        (getattr(PLT, "fruit_tree_legacy", None) or PLT.fruit_tree)(k, np.zeros(2), 0.0, 4.4, ("f", "a"), r=1.8)
        rows.append(PV.row(views(k, 4.4)))
    elif mode == "fruit":
        for h, r in ((3.6, 1.3), (4.4, 1.8), (5.2, 2.2), (3.5, 1.0)):
            for key in ("a", "b", "c"):
                k = PLT.Kit()
                f = ST.orchard_tree(k, (0, 0), 0.0, h, ("f", key), r=r)
                print("fruit", h, r, key, f, tris(k))
                rows.append(PV.row(views(k, h)))
    for i in range(0, len(rows), 6):
        part = rows[i:i + 6]
        sheet = Image.new("RGB", (part[0].width, sum(p.height + 4 for p in part)), (20, 20, 20))
        y = 0
        for p_ in part:
            sheet.paste(p_, (0, y))
            y += p_.height + 4
        sheet.save(out / f"{mode}_{i // 6}.jpg", quality=88)
