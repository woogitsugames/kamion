"""Fixed evidence crops, no per-tree alignment, warp or colour correction."""
import hashlib
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

out = Path(__file__).resolve().parent
phase = sys.argv[1]
target = out / "review" / phase
target.mkdir(parents=True, exist_ok=True)
source = out / "reference7197.jpg"
photo = Image.open(source).convert("RGB")
assert photo.size == (3840, 2560)
processed = []
for condition in ("Low-overcast", "Low-clear", "High-overcast", "High-clear"):
    capture = out / phase / condition / "fire-station-ref7197.png"
    if not capture.exists():
        continue
    processed.append(condition)
    render = Image.open(capture).convert("RGB")
    assert render.size == (2340, 1080)
    gable = Image.new("RGB", (960, 370), (24, 24, 24))
    draw = ImageDraw.Draw(gable)
    draw.text((6, 4), "Rakoon CC0 7197 | fixed gable-region crops; pose WORKING_VALUE", fill="white")
    draw.text((6, 20), "No local tree alignment, warp or colour correction; not a surveyed matching pose", fill=(255, 208, 128))
    a = photo.crop((1120, 1000, 2960, 2140))
    b = render.crop((865, 317, 1670, 817))
    a.thumbnail((480, 310)); b.thumbnail((480, 310))
    gable.paste(a, (0, 65)); gable.paste(b, (480, 65))
    draw.text((6, 46), "photo / local resized reference", fill="white")
    draw.text((486, 46), f"{phase} {condition}", fill="white")
    gable.save(target / f"{condition}-photo-gable.jpg", quality=95)
    native = Image.new("RGB", (890, 428), (24, 24, 24))
    draw = ImageDraw.Draw(native)
    draw.text((6, 4), "Different fixed crops / WORKING pose; photo 0.5x, renders native1x", fill=(255, 208, 128))
    draw.text((6, 22), "Rakoon CC0 7197", fill="white")
    draw.text((322, 22), f"before {condition}", fill="white")
    draw.text((606, 22), f"{phase} {condition}", fill="white")
    a = photo.crop((2020, 1400, 2640, 2160)).resize((310, 380))
    before = Image.open(out / "before" / condition / "fire-station-ref7197.png").convert("RGB")
    native.paste(a, (0, 44))
    native.paste(before.crop((1400, 460, 1680, 800)), (316, 44))
    native.paste(render.crop((1400, 460, 1680, 800)), (602, 44))
    native.save(target / f"{condition}-photo-crowns-native.jpg", quality=95)
assert processed, "No reference-camera captures"
(target / "source.json").write_text(json.dumps(dict(
    title="7197 May 2021 in Białystok", author="Rakoon", license="CC0",
    url="https://commons.wikimedia.org/wiki/File:7197_May_2021_in_Białystok.jpg",
    local_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), local_size=[3840, 2560],
    conditions=processed,
    photo_gable_crop=[1120, 1000, 2960, 2140], render_gable_crop=[865, 317, 1670, 817],
    photo_crowns_crop=[2020, 1400, 2640, 2160], render_crowns_crop=[1400, 460, 1680, 800],
    status="Fixed crops reused from baseline; approximate pose, not matched photogrammetry; no per-tree transforms"), indent=2), encoding="utf-8")
print(target)
