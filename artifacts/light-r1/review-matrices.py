"""Review sheets for actual shadow/shoulder ablations; original PNG measurements."""
import json
import os
import runpy
from pathlib import Path

for variable in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[variable] = "1"

from PIL import Image, ImageDraw
from measure import measure

ROOT = Path(__file__).resolve().parent
groups = {
    "shadow": (["legacy", "filter-medium", "filter-high", "filter-high-near-split", "filter-high-4096"],
               ["r10_hall_3", "r10_hall_2", "r10_block_3", "stretch-05-docks"]),
    "shoulder": (["clip-12", "clip-14", "clip-16", "clip-18"],
                 ["r10_hall_1", "r10_hall_4", "r10_house_2", "driver-andersa-to-putry"]),
}
results = {}
for group, (variants, cameras) in groups.items():
    results[group] = {}
    for variant in variants:
        directory = ROOT / group / variant
        for camera in cameras:
            if not (directory / f"{camera}.png").exists():
                raise FileNotFoundError(directory / f"{camera}.png")
        results[group][variant] = measure(directory)
    for camera in cameras:
        sheet = Image.new("RGB", (960, ((len(variants)+1)//2)*245), "#202020")
        draw = ImageDraw.Draw(sheet)
        for i, variant in enumerate(variants):
            x, y = i%2*480, i//2*245
            with Image.open(ROOT / group / variant / f"{camera}.png") as im:
                thumb = im.convert("RGB")
                thumb.thumbnail((476, 220))
            sheet.paste(thumb, (x+2, y+23))
            draw.text((x+4, y+5), variant, fill="white")
        sheet.save(ROOT / f"{group}-{camera}.jpg", quality=95)
    if group == "shadow":
        # Diagnostic crop only; the edge ROI must be validated visually before measuring it.
        sheet = Image.new("RGB", (960, 735), "#202020")
        draw = ImageDraw.Draw(sheet)
        for i, variant in enumerate(variants):
            x, y = i%2*480, i//2*245
            with Image.open(ROOT / group / variant / "r10_hall_3.png") as im:
                crop = im.convert("RGB").crop((800, 600, 1240, 820))
            sheet.paste(crop, (x+4, y+23))
            draw.text((x+4, y+5), variant+" / native crop", fill="white")
        sheet.save(ROOT / "shadow-edge-native.jpg", quality=96)
(ROOT / "shadow-shoulder-metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
for variant, cameras in results["shoulder"].items():
    for camera, rois in cameras.items():
        for label in ("asphalt_near", "sunlit_gable"):
            if label in rois:
                print(variant, camera, label, rois[label]["rgb_p95"], "clip%", rois[label]["clip_ge250_percent"])
if (ROOT / "cloud-photo/Low-clear-clouds/r10_house_2.png").exists():
    runpy.run_path(str(ROOT / "photo-review.py"), run_name="__main__")
if len(list((ROOT / "sbs/after/renders").glob("*/*/*.png"))) == 160:
    runpy.run_path(str(ROOT / "finalize-sbs.py"), run_name="__main__")
if (ROOT / "shadow-metric-v2/policy/shadow-wall-10m.json").exists():
    runpy.run_path(str(ROOT / "measure-shadow.py"), run_name="__main__")
