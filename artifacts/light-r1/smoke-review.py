"""Contact sheets <=960 px and measurements from original smoke PNGs."""
import json
from pathlib import Path

from PIL import Image, ImageDraw
from measure import measure

ROOT = Path(__file__).resolve().parent
VARIANTS = ["High-clear-flat", "High-clear-clouds", "High-clear-no-dither", "Low-clear-flat", "Low-clear-clouds"]
CAMERAS = ["driver-andersa-to-putry", "r10_block_3", "r10_house_2"]

results = {}
for variant in VARIANTS:
    directory = ROOT / "cloud-smoke" / variant
    for camera in CAMERAS:
        if not (directory / f"{camera}.png").is_file():
            raise FileNotFoundError(directory / f"{camera}.png")
    results[variant] = measure(directory)

for camera in CAMERAS:
    sheet = Image.new("RGB", (960, 735), "#202020")
    draw = ImageDraw.Draw(sheet)
    for i, variant in enumerate(VARIANTS):
        x, y = i % 2 * 480, i // 2 * 245
        with Image.open(ROOT / "cloud-smoke" / variant / f"{camera}.png") as im:
            thumb = im.convert("RGB")
            thumb.thumbnail((476, 220))
        sheet.paste(thumb, (x + 2, y + 23))
        draw.text((x + 4, y + 5), variant, fill="white")
    sheet.save(ROOT / f"smoke-{camera}.jpg", quality=95)

(ROOT / "smoke-metrics.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
for variant, cameras in results.items():
    print(variant)
    for camera, rois in cameras.items():
        for label in ("sky", "asphalt_near", "sunlit_gable"):
            if label in rois:
                roi = rois[label]
                print(camera, label, "mean", roi["rgb_mean"], "HF1.5", roi["hf_rms_srgb_levels"]["1.5"])
