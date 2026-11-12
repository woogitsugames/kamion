"""Small pose diagnostic: four NMT samples, two known 120 m tops, no world build."""
import json
import math
from pathlib import Path

import numpy as np

out = Path(__file__).resolve().parent
root = out.parents[1]
identity = json.loads((out / "chimney-identity-preflight.json").read_text(encoding="utf-8"))
terrain = json.loads((root / "Data/Regions/bialystok-industrial-c/terrain.json").read_text(encoding="utf-8"))
encoding = terrain["encoding"]
data = np.memmap(root / encoding["file"], dtype="<u2", mode="r", shape=tuple(terrain["samples"]))
east, north = identity["camera_epsg2180"]
bbox = terrain["bbox"]
x = (east - bbox[0]) * (data.shape[1] - 1) / (bbox[2] - bbox[0])
y = (bbox[3] - north) * (data.shape[0] - 1) / (bbox[3] - bbox[1])
i, j = int(x), int(y)
dx, dy = x - i, y - j
q = float(data[j, i]) * (1-dx) * (1-dy) + float(data[j, i+1]) * dx * (1-dy) + float(data[j+1, i]) * (1-dx) * dy + float(data[j+1, i+1]) * dx * dy
ground = q * encoding["scale_m_per_unit"] + encoding["offset_m"]
eye = ground + 1.65
heading = sum(identity["inferred_heading_from_each_stack_deg"]) / 2
focal_pixels = 27 * 3840 / 36
rows = []
for way, base_z, top_y in (("628899554", 137.243, 320), ("628899553", 137.262, 22)):
    stack = next(row for row in identity["stacks"] if row["osm_way"] == way)
    depth = stack["distance_m"] * math.cos(math.radians(stack["bearing_clockwise_from_north_deg"] - heading))
    angle_world = math.degrees(math.atan2(base_z + 120 - eye, depth))
    angle_image = math.degrees(math.atan2(1080 - top_y, focal_pixels))
    rows.append(dict(osm_way=way, head_top_y_WORKING_VALUE=top_y, world_top_angle_deg=angle_world,
                     image_top_angle_deg=angle_image, implied_camera_pitch_deg=angle_world-angle_image))
result = dict(camera_ground_NMT_m=ground, eye_height_WORKING_VALUE_m=1.65, focal_pixels_assuming_equivalent_width=focal_pixels,
              height_m=120, rows=rows,
              pitch_disagreement_deg=abs(rows[0]["implied_camera_pitch_deg"] - rows[1]["implied_camera_pitch_deg"]),
              assumptions="Source GPS, approximate head pixels, no roll, equivalent width 36 mm, both heights 120 m",
              decision="A common camera pitch must explain both known tops. This unsolved pose cannot calibrate stripe heights or justify widening/shortening the shafts.")
(out / "chimney-pose-consistency.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
