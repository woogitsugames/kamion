"""Overlay PNG per junction / roundabout: orthophoto (reference only) + generated carriageway outline, lane lines,
islands, arrows, stop lines, and the disagreement components. <= 960 px, north up, 20 m scale bar."""
from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

from . import gen as G

COL = {"edge": (0, 255, 255), "lane": (255, 230, 0), "arrow": (255, 140, 0), "stop": (255, 40, 40),
       "island_ok": (255, 0, 255), "island_bad": (255, 0, 0), "gen_only": (255, 60, 60), "ortho_only": (60, 140, 255),
       "missing_island": (0, 255, 80), "det": (255, 255, 255)}
LANE_KINDS = ("lane", "lane-P-2a", "centre", "centre-P-2a", "P-4", "P-7b")
STOP_KINDS = ("P-14", "P-13")


def _outline(m, px):
    return m & ~ndi.binary_erosion(m, iterations=max(1, px))


def render(path, wm, g: G.Generated, title, gen_islands, missing, gen_only, o_only, det_pts=None, notes=None,
           out_px=960):
    res, x0, y1 = wm["res"], wm["x0"], wm["y1"]
    shape = wm["gen"].shape
    base = wm["rgb"].astype(np.float32) * 0.85
    img = base.copy()

    def paint(mask, col, a=1.0):
        img[mask] = img[mask] * (1 - a) + np.array(col, np.float32) * a

    # disagreement fills first (translucent)
    paint(gen_only, COL["gen_only"], 0.35)
    paint(o_only, COL["ortho_only"], 0.35)
    # islands: generated separations, coloured by verdict
    if gen_islands is not None:
        lab = gen_islands
        paint(lab["ok"], COL["island_ok"], 0.25)
        paint(lab["bad"], COL["island_bad"], 0.55)
    if missing is not None:
        paint(missing, COL["missing_island"], 0.45)
    lw = max(1, int(round(0.25 / res)))
    paint(_outline(wm["gen"], lw), COL["edge"])
    for k in LANE_KINDS:
        if k in g.mark_tris:
            paint(G.rasterize(g.mark_tris[k], x0, y1, res, shape), COL["lane"])
    if "P-8" in g.mark_tris:
        paint(G.rasterize(g.mark_tris["P-8"], x0, y1, res, shape), COL["arrow"])
    for k in STOP_KINDS:
        if k in g.mark_tris:
            paint(G.rasterize(g.mark_tris[k], x0, y1, res, shape), COL["stop"])
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    scale = out_px / max(shape)
    im = im.resize((int(shape[1] * scale), int(shape[0] * scale)), Image.LANCZOS)
    d = ImageDraw.Draw(im)
    font = ImageFont.load_default()
    if det_pts:
        for (x, y) in det_pts:
            c = ((x - x0) / res * scale, (y1 - y) / res * scale)
            d.ellipse([c[0] - 1.5, c[1] - 1.5, c[0] + 1.5, c[1] + 1.5], fill=COL["det"])
    for i, isl in enumerate(notes or []):
        x, y = isl["xy"]
        c = ((x - x0) / res * scale, (y1 - y) / res * scale)
        d.text((c[0] + 4, c[1] - 6), isl["label"], fill=(255, 255, 255), font=font, stroke_width=2,
               stroke_fill=(0, 0, 0))
    # header + legend + scale bar
    W = im.width
    head = Image.new("RGB", (W, 54), (18, 18, 18))
    hd = ImageDraw.Draw(head)
    hd.text((6, 4), title, fill=(235, 235, 235), font=font)
    items = [("gen edge", "edge"), ("gen lane lines", "lane"), ("gen arrows", "arrow"), ("gen stop/give-way", "stop"),
             ("gen island ok", "island_ok"), ("gen island = road on ortho", "island_bad"),
             ("gen only", "gen_only"), ("ortho only", "ortho_only"), ("ortho island missing", "missing_island"),
             ("ortho edge", "det")]
    x = 6
    y = 22
    for lab_, k in items:
        tw = int(hd.textlength(lab_, font=font))
        if x + 14 + tw > W - 6:
            x, y = 6, y + 15
        hd.rectangle([x, y + 2, x + 10, y + 10], fill=COL[k])
        hd.text((x + 13, y), lab_, fill=(220, 220, 220), font=font)
        x += 13 + tw + 12
    out = Image.new("RGB", (W, im.height + head.height), (0, 0, 0))
    out.paste(head, (0, 0))
    out.paste(im, (0, head.height))
    d = ImageDraw.Draw(out)
    bar = 20.0 / res * scale
    yb = out.height - 12
    d.rectangle([10, yb - 3, 10 + bar, yb + 1], fill=(255, 255, 255), outline=(0, 0, 0))
    d.text((14 + bar, yb - 8), "20 m", fill=(255, 255, 255), font=font, stroke_width=2, stroke_fill=(0, 0, 0))
    d.text((W - 300, yb - 8), f"ortho: {wm['src']} (GUGiK, reference only)", fill=(255, 255, 255), font=font,
           stroke_width=2, stroke_fill=(0, 0, 0))
    out.save(path, quality=88) if str(path).lower().endswith(".jpg") else out.save(path, optimize=True)
    return path
