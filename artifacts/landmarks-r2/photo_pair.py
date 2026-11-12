"""Reference comparison at 960 px; pose remains explicitly unverified."""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parent
phase = sys.argv[1] if len(sys.argv) > 1 else "before"
camera = sys.argv[2] if len(sys.argv) > 2 else "dk8-ref7204"
source = root / "reference7204-original.jpg"
with Image.open(source) as opened:
    photo = opened.convert("RGB")
aspect = 2340 / 1080
crop_height = round(photo.width / aspect)
top = (photo.height - crop_height) // 2
box = (0, top, photo.width, top + crop_height)
photo = photo.crop(box)
photo.thumbnail((480, 222))
out = root / "review" / f"photo-{phase}"
out.mkdir(parents=True, exist_ok=True)
records = []
for condition in ("Low-overcast", "Low-clear", "High-overcast", "High-clear"):
    render_path = root / phase / condition / f"{camera}.png"
    if not render_path.exists():
        continue
    with Image.open(render_path) as opened:
        render = opened.convert("RGB")
    render.thumbnail((480, 222))
    sheet = Image.new("RGB", (960, 278), (24, 24, 24))
    draw = ImageDraw.Draw(sheet)
    draw.text((8, 4), f"7204 Rakoon CC0, central crop | {phase} {condition} {camera}", fill="white")
    draw.text((8, 20), "POSE UNVERIFIED: GPS/focal metadata; heading and eye height WORKING_VALUE", fill=(255, 208, 128))
    sheet.paste(photo, ((480 - photo.width) // 2, 46))
    sheet.paste(render, (480 + (480 - render.width) // 2, 46))
    target = out / f"{condition}-{camera}.jpg"
    sheet.save(target, quality=93)
    records.append(dict(condition=condition, render=str(render_path.relative_to(root)),
                        pair=str(target.relative_to(root)), width_px=960))
result = dict(source=str(source.relative_to(root)), source_crop_box=box,
              source_page="https://commons.wikimedia.org/wiki/File:7204_May_2021_in_Bia%C5%82ystok.jpg",
              author="Rakoon", license="CC0", modifications="Central vertical crop and resizing for comparison",
              camera=camera, phase=phase, pose_confidence="UNVERIFIED", pairs=records)
(out / f"source-{camera}.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"Saved {len(records)} reference pairs to {out}")
