"""Re-level the cloth block of exported cab AO atlases (review r6 C-N5 / C-N6, ADR 0044 addendum r6).

The cloth block (top-right, rows 2..3 blk, last blk columns; uv1 (0.999, 0.9785)) carries the AO of every NO_AO part:
the rotating steering-wheel rim and stitch, curtains and blinds. a6_export.bake_ao filled it with the MEDIAN of the
covered texels, but ~45 % of covered texels are fully occluded faces (backs, undersides; p10 = 0), so the median was
0.04 (8-bit 0.02): the rim had AO 0.02 on every tier (ambient, fill and reflections x 0.02, albedo x 0.4 by the deep-AO
darkening), i.e. black in shade and lit by the warm sun only. a6_export now uses the MEAN of the covered texels (the
average cab ambient, 0.244 on the LOD0 bake; the spokes/hub of the same wheel average 0.20). This script applies the
same rule to atlases already exported, without a Blender re-bake: the mean is taken over the bake's coverage mask
(artifacts/truck-interior/ao_coverage_<res>.npy, written by bake_ao, rows top-down) on the High (full-resolution) PNG,
and written into the cloth block of every tier of that LOD.

Usage: python tools/blender/truck/interior/ao_cloth_block.py <textures dir> [<coverage dir>]
       (textures dir = art-source/truck/interior/export/textures)
"""
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

AO_RES = {0: 4096, 1: 1024, 2: 512}   # a6_export.AO_RES (bake resolution per LOD = High atlas size)
TIERS = ("High", "Medium", "Low")


def block(res, size):
    """(row0, row1, col0) of the cloth block in a saved atlas of `size` px (a6_export: blk = max(4, res // 128))."""
    b = max(4, res // 128) * size / res
    return int(round(2 * b)), int(round(3 * b)), size - max(1, int(round(b)))


def main(tex_dir, cov_dir):
    out = {}
    for lod, res in AO_RES.items():
        hi = tex_dir / "High" / f"T_Cab_AO_LOD{lod}.png"
        a = np.asarray(Image.open(hi).convert("L"), dtype=np.float64) / 255.0
        cov_p = cov_dir / f"ao_coverage_{res}.npy"
        if a.shape[0] != res or not cov_p.exists():
            print(f"LOD{lod}: skipped (High atlas {a.shape[0]} px, coverage {cov_p.name} {'found' if cov_p.exists() else 'missing'})")
            continue
        cov = np.load(cov_p) > 0
        r0, r1, c0 = block(res, res)
        cov[r0:r1, c0:] = False
        cloth = float(a[cov].mean())
        v = int(round(cloth * 255))
        out[f"LOD{lod}"] = {"cloth_mean": round(cloth, 4), "old_median_8bit": int(round(a[(r0 + r1) // 2, -2] * 255)), "new_8bit": v}
        for t in TIERS:
            p = tex_dir / t / f"T_Cab_AO_LOD{lod}.png"
            im = Image.open(p)
            mode = im.mode
            px = np.asarray(im.convert("RGB")).copy()
            s = px.shape[0]
            r0, r1, c0 = block(res, s)
            px[r0:r1, c0:, :] = v
            Image.fromarray(px, "RGB").convert(mode).save(p, optimize=True)
            print(f"LOD{lod} {t} {s}px: cloth block rows {r0}-{r1} cols {c0}-{s} -> {v}/255")
    print(json.dumps(out))


if __name__ == "__main__":
    tex = Path(sys.argv[1])
    cov = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[4] / "artifacts" / "truck-interior"
    main(tex, cov)
