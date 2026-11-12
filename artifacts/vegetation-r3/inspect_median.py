"""Small window from the local GUGiK orthophoto; no download or source writes."""
import json
from pathlib import Path
import numpy as np
import rasterio
from rasterio.windows import from_bounds
from PIL import Image, ImageDraw

here = Path(__file__).resolve().parent
root = here.parents[1]
region = root / "Data/Regions/bialystok-industrial-c"
origin = np.array([777995., 596223.])
bbox = (-440., -340., -60., -110.)
source = root / "Data/raw/derived/bialystok-industrial-c/ortho_0p25m.tif"
with rasterio.open(source) as src:
    bounds = [bbox[0]+origin[0], bbox[1]+origin[1], bbox[2]+origin[0], bbox[3]+origin[1]]
    window = from_bounds(*bounds, transform=src.transform).round_offsets().round_lengths()
    a = src.read([1, 2, 3], window=window)
    print("Ortho", src.crs, src.bounds, src.res, "crop", a.shape)
im = Image.fromarray(np.moveaxis(a, 0, -1)).convert("RGB")
im.thumbnail((960, 840))
w, h = im.size
def xy(e, n):
    return ((e-bbox[0])/(bbox[2]-bbox[0])*w, (bbox[3]-n)/(bbox[3]-bbox[1])*h)

cameras = json.loads((region / "sbs_cameras.json").read_text(encoding="utf-8"))["cameras"]
camera = next(c for c in cameras if "297817221966185" in c["id"])
ref = next(r for r in json.loads((region / "sbs_references.json").read_text(encoding="utf-8"))["references"]
           if r["camera"] == camera["id"])
points = json.loads((root / "Data/raw/derived/bialystok-industrial-c/world/preview_trees.json").read_text())["trees"]
for overlay in (False, True):
    frame = im.copy()
    draw = ImageDraw.Draw(frame)
    if overlay:
        for e, n, *_ in points:
            if bbox[0] < e < bbox[2] and bbox[1] < n < bbox[3]:
                x, y = xy(e, n)
                draw.ellipse((x-2, y-2, x+2, y+2), outline="#ff2222", width=1)
    for e in range(-440, -59, 20):
        x, _ = xy(e, bbox[1])
        draw.line((x, 0, x, h), fill=(160, 160, 160), width=1)
        draw.text((x+2, 2), str(e), fill="white", stroke_width=1, stroke_fill="black")
    for n in range(-340, -109, 20):
        _, y = xy(bbox[0], n)
        draw.line((0, y, w, y), fill=(160, 160, 160), width=1)
        draw.text((2, y+2), str(n), fill="white", stroke_width=1, stroke_fill="black")
    p = np.array(camera["pos"][:2])
    direction = np.array(camera["look_at"][:2])-p
    direction /= np.linalg.norm(direction)
    for angle in (-30, 0, 30):
        t = np.radians(angle)
        rot = np.array([[np.cos(t), -np.sin(t)], [np.sin(t), np.cos(t)]])
        draw.line([xy(*p), xy(*(p+120*(rot@direction)))], fill="cyan", width=2)
    x, y = xy(*p)
    draw.ellipse((x-5, y-5, x+5, y+5), fill="cyan")
    draw.text((x+8, y), "B/120 camera WORKING_VALUE", fill="cyan", stroke_width=1, stroke_fill="black")
    frame.save(here / ("median-ortho-trees.png" if overlay else "median-ortho.png"))
(here / "median-source-audit.json").write_text(json.dumps(dict(
    bbox_local=bbox, origin_epsg2180=origin.tolist(), camera=camera,
    photo_date=ref["captured_at"], photo_source=ref["page_url"], photo_author=ref["author"],
    ortho=str(source.relative_to(root)), note="Red points are generated tree centres, not detected crowns; cyan fan is an approximate guide, not pose calibration."
), indent=2)+"\n", encoding="utf-8")
print("Photo date", ref["captured_at"], ref["author"])
