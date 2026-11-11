"""Review the photographic sky in all 15 original PNGs, including native banding diagnostics."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw
from measure import measure

ROOT = Path(__file__).resolve().parent
SOURCE = next(folder for folder in ("cloud-photo-v4", "cloud-photo-v3", "cloud-photo-v2", "cloud-photo")
              if (ROOT / folder / "Low-clear-clouds/r10_house_2.png").exists())
VARIANTS = ["High-clear-flat", "High-clear-clouds", "High-clear-with-dither", "Low-clear-flat", "Low-clear-clouds"]
CAMERAS = ["driver-andersa-to-putry", "r10_block_3", "r10_house_2"]
result = {}
for variant in VARIANTS:
    directory = ROOT / SOURCE / variant
    for camera in CAMERAS:
        if not (directory / f"{camera}.png").exists():
            raise FileNotFoundError(directory / f"{camera}.png")
    result[variant] = measure(directory)
for camera in CAMERAS:
    sheet = Image.new("RGB", (960, 735), "#202020")
    draw = ImageDraw.Draw(sheet)
    for i, variant in enumerate(VARIANTS):
        x, y = i%2*480, i//2*245
        with Image.open(ROOT / SOURCE / variant / f"{camera}.png") as im:
            thumb = im.convert("RGB")
            thumb.thumbnail((476, 220))
        sheet.paste(thumb, (x+2, y+23))
        draw.text((x+4, y+5), variant, fill="white")
    sheet.save(ROOT / f"photo-{camera}.jpg", quality=95)
sheet = Image.new("RGB", (960, 520), "#202020")
draw = ImageDraw.Draw(sheet)
for i, variant in enumerate(VARIANTS[:3]):
    with Image.open(ROOT / SOURCE / variant / "r10_block_3.png") as im:
        crop = im.convert("RGB").crop((1097, 73, 1389, 183))
    a = np.asarray(crop, dtype=float)
    stretched = np.uint8(np.clip((a-a.mean((0, 1)))*16+128, 0, 255))
    sheet.paste(crop, (i*320, 30))
    sheet.paste(Image.fromarray(stretched), (i*320, 230))
    draw.text((i*320+3, 5), variant, fill="white")
    draw.text((i*320+3, 205), "16x contrast diagnostic", fill="white")
sheet.save(ROOT / "photo-native-sky-banding.jpg", quality=97)
(ROOT / "photo-metrics.json").write_text(json.dumps({"source_directory": SOURCE, "measurements": result}, indent=2), encoding="utf-8")
for variant, cameras in result.items():
    for camera, rois in cameras.items():
        for label in ("sky", "asphalt_near"):
            if label in rois:
                print(variant, camera, label, "HF1.5", rois[label]["hf_rms_srgb_levels"]["1.5"])
