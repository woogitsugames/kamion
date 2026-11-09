"""Overlay the orthographic road render (Blender, emission-coded, transparent background) on the GUGiK
orthophoto crop of the same footprint, for alignment checks. The orthophoto is used as a reference
only (docs/05 §3), never as a texture.

    uv run --project tools/worldgen tools/worldgen/roads/qa_ortho.py --region bialystok-industrial-c \
        --render artifacts/visual/world-c/ortho_putry.png --out docs/reports/visual/world-c/ortho_putry_overlay.jpg
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from roads import pipeline  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--region", required=True)
    ap.add_argument("--render", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cam", default="ortho_putry")
    ap.add_argument("--px", type=int, default=1200)
    ap.add_argument("--alpha", type=float, default=0.55)
    a = ap.parse_args()
    import rasterio
    from rasterio.windows import from_bounds
    rdir = pipeline.REGIONS / a.region
    cams = json.loads((rdir / "generated/control_cameras.json").read_text(encoding="utf-8"))["cameras"]
    cam = next(c for c in cams if c["id"] == a.cam)
    reg = pipeline.load_region(a.region)
    ox, oy = reg["origin"]["x"], reg["origin"]["y"]
    half = cam["size_m"] / 2
    cx, cy = cam["center"][0] + ox, cam["center"][1] + oy
    ortho = json.loads((rdir / "ortho.json").read_text(encoding="utf-8"))
    with rasterio.open(pipeline.REPO / ortho["file"]) as o:
        img = o.read(window=from_bounds(cx - half, cy - half, cx + half, cy + half, o.transform),
                     out_shape=(3, a.px, a.px), resampling=rasterio.enums.Resampling.bilinear)
    base = Image.fromarray(np.moveaxis(img, 0, -1)).convert("RGBA")
    rnd = Image.open(pipeline.REPO / a.render).convert("RGBA").resize((a.px, a.px), Image.LANCZOS)
    arr = np.array(rnd).astype(np.float32)
    arr[..., 3] *= a.alpha
    over = Image.fromarray(arr.astype(np.uint8))
    comp = Image.alpha_composite(base, over).convert("RGB")
    side = Image.new("RGB", (a.px * 2 + 8, a.px + 40), (20, 20, 20))
    side.paste(base.convert("RGB"), (0, 40))
    side.paste(comp, (a.px + 8, 40))
    d = ImageDraw.Draw(side)
    d.text((10, 12), f"GUGiK orthophoto {ortho.get('source_manifest', '')} (reference only)", fill=(230, 230, 230))
    d.text((a.px + 18, 12), "generated roads overlaid (asphalt dark, kerbs white, sidewalks orange, markings "
           "yellow, bridges blue)", fill=(230, 230, 230))
    out = pipeline.REPO / a.out
    out.parent.mkdir(parents=True, exist_ok=True)
    side = side.resize((side.width * 3 // 4, side.height * 3 // 4), Image.LANCZOS)
    side.save(out, quality=80, optimize=True)
    print(out, out.stat().st_size)


if __name__ == "__main__":
    main()
