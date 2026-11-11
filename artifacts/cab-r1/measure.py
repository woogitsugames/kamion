"""Editor before/after metrics and <=960px review sheets. Run from the repo root."""
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent
out = {}
for stage in ("before", "after"):
    for path in sorted((ROOT / stage).glob("*/*.png")):
        with Image.open(path) as im:
            rgb = np.asarray(im.convert("RGB"), dtype=float)
            luma = rgb @ np.array([.2126, .7152, .0722])
            out[str(path.relative_to(ROOT))] = {
                "source": "editor", "size": list(im.size),
                "mean_luma_srgb255": float(luma.mean()),
                "dark_lt_3pct_percent": float((luma < 255 * .03).mean() * 100),
                "clipped_all_channels_ge250_percent": float((rgb.min(axis=2) >= 250).mean() * 100),
                "lower_half_median_luma_srgb255": float(np.median(luma[luma.shape[0] // 2:])),
            }
            preview = im.convert("RGB")
            preview.thumbnail((960, 960))
            dest = ROOT / "review" / stage / path.parent.name / (path.stem + ".jpg")
            dest.parent.mkdir(parents=True, exist_ok=True)
            preview.save(dest, quality=94)
            if stage == "after":
                before = ROOT / "before" / path.parent.name / path.name
                if before.exists():
                    a = np.asarray(Image.open(before).convert("RGB"), dtype=float)
                    if a.shape != rgb.shape:
                        raise ValueError(f"Incompatible capture size: {path}")
                    out[str(path.relative_to(ROOT))]["mean_abs_delta_srgb255"] = float(np.abs(rgb - a).mean())
                    sheet = Image.new("RGB", (960, 250), "#222222")
                    d = ImageDraw.Draw(sheet)
                    for i, src in enumerate((before, path)):
                        p = Image.open(src).convert("RGB")
                        p.thumbnail((480, 225))
                        sheet.paste(p, (i * 480, 22))
                        d.text((i * 480 + 5, 5), f"{('BEFORE', 'AFTER')[i]} {path.parent.name} {path.stem}", fill="white")
                    sheet.save(dest.with_name(path.stem + "-pair.jpg"), quality=94)
for stage in ("before", "after"):
    for folder in sorted((ROOT / stage).glob("*/native-mirrors")):
        paths = sorted(folder.glob("*.png"))
        if not paths:
            continue
        sheet = Image.new("RGB", (960, 450), "#222222")
        d = ImageDraw.Draw(sheet)
        for i, path in enumerate(paths):
            p = Image.open(path).convert("RGB")
            p.thumbnail((150, 400))
            x = i * 160
            d.text((x, 4), path.stem.replace("MirrorCamera_", ""), fill="white")
            sheet.paste(p, (x, 35))
        dest = ROOT / "review" / stage / folder.parent.name / "native-mirrors.jpg"
        dest.parent.mkdir(parents=True, exist_ok=True)
        sheet.save(dest, quality=94)
(ROOT / "image-metrics.json").write_text(json.dumps(out, indent=2))
print(f"Measured {len(out)} matched-resolution editor images; review sheets in {ROOT / 'review'}")
