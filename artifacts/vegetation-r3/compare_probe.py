"""One-frame B budget check and explicitly colour-based apparent greenery metric."""
import json
import runpy
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

here = Path(__file__).resolve().parent
root = here.parents[1]
sys.path.insert(0, str(root / "tools/worldgen"))
from streetscape.vegetation_metrics import foliage_mask

world = json.loads((here / "world-proof.json").read_text())
if world["orthophoto_qa"].get("new_instances") != 0 or not world["orthophoto_qa"].get("placed"):
    raise SystemExit("No generated B replacement proof yet")
group = "Low-overcast-photo-2048x1536"
camera = "sbs-g3-b-297817221966185"
before_dir, after_dir = here / "before" / group, here / "probe" / group
before_path, after_path = before_dir / (camera+".png"), after_dir / (camera+".png")
if after_path.stat().st_mtime < (here / "world-proof.json").stat().st_mtime:
    raise SystemExit("Probe image predates B world proof")
parse_stats = runpy.run_path(str(here / "review_images.py"))["stats"]
old, new = parse_stats(before_dir / "stats.txt")[camera], parse_stats(after_dir / "stats.txt")[camera]
roi = (0., .35, .45, .66)
metrics, frames = {}, []
for stage, path in (("before", before_path), ("B", after_path)):
    frame = Image.open(path).convert("RGB")
    a = np.array(frame)
    h, w = a.shape[:2]
    x0, y0, x1, y1 = (round(roi[i]*s) for i, s in enumerate((w, h, w, h)))
    mask = foliage_mask(a[y0:y1, x0:x1])
    metrics[stage] = dict(green_like_pixels=int(mask.sum()), roi_pixels=int(mask.size),
                          fraction=float(mask.mean()))
    if stage == "B":
        crop = a[y0:y1, x0:x1]
        crop[mask] = (255, 50, 180)
        annotated = Image.fromarray(a)
        ImageDraw.Draw(annotated).rectangle((x0, y0, x1, y1), outline="magenta", width=2)
    frames.append(frame)
result = dict(camera=camera, group=group, before=old, after=new,
    delta_draws=new["total_draws"]-old["total_draws"],
    delta_triangles_percent=100*(new["total_triangles_k"]/old["total_triangles_k"]-1),
    apparent_greenery=metrics, fixed_roi=roi,
    method="Original 1024x768; fixed ROI and colour threshold, NOT semantic tree segmentation or biomass. Triangles have integer trisK precision. One Low probe does not certify all cameras.")
(here / "probe-b-comparison.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
reference = next(r for r in json.loads((here / "photo-references.json").read_text())["references"] if r["camera"] == camera)
photo = Image.open(root / reference["local_photo"]).convert("RGB")
sheet = Image.new("RGB", (960, 880), "#222222")
draw = ImageDraw.Draw(sheet)
for i, (label, frame) in enumerate(zip(("PRZED", "B", "ZDJECIE", "B: maska koloru, nie semantyka"), frames+[photo, annotated])):
    col, row = i % 2, i // 2
    frame = frame.copy()
    frame.thumbnail((470, 352))
    x, y = col*490, row*390
    draw.text((x+4, y+4), label, fill="white")
    sheet.paste(frame, (x, y+25))
draw.text((5, 790), "zsolt | 2017-07-29 | CC BY-SA 4.0 | poza B WORKING_VALUE", fill="white")
draw.text((5, 810), reference["page_url"], fill="white")
draw.text((5, 830), "Jedna zamiana pozostawia zespol koron B8 otwarty; GPU telefonu UNVERIFIED.", fill="white")
sheet.save(here / "probe-b-sheet.jpg", quality=93)
print(json.dumps(result, indent=2))
