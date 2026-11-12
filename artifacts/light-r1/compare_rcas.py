"""Measure original PNGs from the controlled RCAS ablation; never measure JPEG previews."""
import json
from pathlib import Path

from PIL import Image, ImageDraw

from measure import measure

ROOT = Path(__file__).resolve().parent
VARIANTS = ("0", "0.25", "0.5", "0.75")


def main():
    result = {}
    for lighting in ("clear", "overcast"):
        result[lighting] = {}
        for sharp in VARIANTS:
            directory = ROOT / "rcas" / f"High-{lighting}-{sharp}"
            if not directory.exists():
                continue
            values = measure(directory)
            result[lighting][sharp] = values
            (directory / "measurements.json").write_text(
                json.dumps(values, indent=2), encoding="utf-8"
            )
        # Each preview is <=960 px. Native crops make the asphalt grain and sky
        # visible without enlarging a full panorama and hiding the filter difference.
        for camera, rect, label in (
            ("driver-andersa-to-putry", (1243, 914, 1316, 1005), "asphalt"),
            ("r10_block_3", (1097, 73, 1389, 183), "sky"),
        ):
            sheet = Image.new("RGB", (960, 300), "#202020")
            draw = ImageDraw.Draw(sheet)
            for i, sharp in enumerate(VARIANTS):
                path = ROOT / "rcas" / f"High-{lighting}-{sharp}" / f"{camera}.png"
                if not path.exists():
                    continue
                with Image.open(path) as im:
                    crop = im.convert("RGB").crop(rect)
                crop.thumbnail((232, 265))
                sheet.paste(crop, (i * 240 + 4, 28))
                draw.text((i * 240 + 4, 7), f"RCAS {sharp} / {label}", fill="white")
            sheet.save(ROOT / f"rcas-{lighting}-{label}.jpg", quality=95)
    (ROOT / "rcas-metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    for lighting, variants in result.items():
        for sharp, values in variants.items():
            asphalt = values.get("driver-andersa-to-putry", {}).get("asphalt_near", {})
            sky = values.get("r10_block_3", {}).get("sky", {})
            print(lighting, sharp, "asphalt HF:", asphalt.get("hf_rms_srgb_levels"),
                  "sky HF:", sky.get("hf_rms_srgb_levels"))


if __name__ == "__main__":
    main()
