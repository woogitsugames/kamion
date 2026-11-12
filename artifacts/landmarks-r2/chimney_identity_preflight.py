"""Read-only spatial identity check; this does not establish the painting height."""
import json
import math
from pathlib import Path

from pyproj import Transformer

out = Path(__file__).resolve().parent
metadata = json.loads((out / "chimney-source-correction.json").read_text(encoding="utf-8"))
lat, lon = metadata["camera_gps_lat_lon"]
camera = Transformer.from_crs(4326, 2180, always_xy=True).transform(lon, lat)
points = {"628899553": [778619.25, 595139.04], "628899554": [778713.26, 595089.71]}
records = []
for osm, point in points.items():
    east, north = point[0] - camera[0], point[1] - camera[1]
    records.append(dict(osm_way=osm, epsg2180=point,
                        distance_m=math.hypot(east, north),
                        bearing_clockwise_from_north_deg=math.degrees(math.atan2(east, north)) % 360))
# Around a south-facing camera, increasing clockwise bearing appears farther right.
ordered = sorted(records, key=lambda r: r["bearing_clockwise_from_north_deg"])
result = dict(camera_epsg2180=camera, source_page=metadata["file_page"],
              source_gps_precision_note="Rounded source GPS; not a surveyed camera pose",
              stacks=records, predicted_left_to_right=[r["osm_way"] for r in ordered],
              angular_separation_deg=abs(records[0]["bearing_clockwise_from_north_deg"] - records[1]["bearing_clockwise_from_north_deg"]),
              conclusion="Geometric prediction only. Inspect original photo and compare projected separation before assigning head geometry.")
(out / "chimney-identity-preflight.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
