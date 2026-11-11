"""Measure static and instanced editor estimates, compose the exact before/after pairs."""
import json
from pathlib import Path
import re

from PIL import Image, ImageDraw, ImageOps

ROOT = Path(__file__).resolve().parent
CAMS = ["edge-north", "edge-east", "edge-south", "edge-west", "dk8-dk19-exit",
        "edge-pietrasze-horizon", "edge-pietrasze-overview"]
STATIC = re.compile(r"^(.*?): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)")
INSTANCED = re.compile(r"^  (.*?) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k")


def stats(path):
    result = {}
    for line in path.read_text().splitlines():
        match = STATIC.match(line)
        if match:
            camera, objects, draws, shadows, tris = match.groups()
            result[camera] = dict(objects=int(objects), static_draws=int(draws),
                                  shadow_draws=int(shadows), static_tris_k=int(tris))
        match = INSTANCED.match(line)
        if match:
            camera, draws, instances, tris = match.groups()
            result[camera].update(instanced_draws=int(draws), instances=int(instances),
                                  instanced_tris_k=int(tris))
    return result


rows = []
for tier in ("Low", "High"):
    for lighting in ("clear", "overcast"):
        configuration = f"{tier}-{lighting}"
        paths = {phase: ROOT / phase / configuration for phase in ("before", "after")}
        measurements = {phase: stats(path / "stats.txt") for phase, path in paths.items()}
        sheet = Image.new("RGB", (960, 254 * len(CAMS)), "white")
        draw = ImageDraw.Draw(sheet)
        for index, camera in enumerate(CAMS):
            before, after = (measurements[phase][camera] for phase in ("before", "after"))
            row = dict(configuration=configuration, camera=camera, before=before, after=after)
            row["delta_static_draws"] = after["static_draws"] - before["static_draws"]
            row["delta_instanced_draws"] = after["instanced_draws"] - before["instanced_draws"]
            row["delta_static_tris_k"] = after["static_tris_k"] - before["static_tris_k"]
            rows.append(row)
            for column, phase in enumerate(("before", "after")):
                image = Image.open(paths[phase] / f"{camera}.png").convert("RGB")
                image = ImageOps.contain(image, (480, 224))
                sheet.paste(image, (column * 480, index * 254 + 28))
                draw.text((column * 480 + 4, index * 254 + 4),
                          f"{camera} | {phase} {configuration}", fill="black")
        sheet.save(ROOT / f"compare-{configuration}.jpg", quality=94)
(ROOT / "measurements.json").write_text(json.dumps(rows, indent=2), encoding="utf-8")
low = [row for row in rows if row["configuration"].startswith("Low")]
assert all(row["delta_static_draws"] + row["delta_instanced_draws"] <= 0 for row in low)
assert all(row["after"]["static_tris_k"] + row["after"]["instanced_tris_k"]
           <= 1.02 * (row["before"]["static_tris_k"] + row["before"]["instanced_tris_k"])
           for row in low)
print(f"{len(rows)} paired editor estimates; Low draws +0 and tris <= +2% verified")
