"""Read two small OSM API extracts; no PBF scan and no source override edits."""
import json
import math
from datetime import datetime, timezone
from pathlib import Path

from pyproj import Transformer

out = Path(__file__).resolve().parent
transform = Transformer.from_crs(4326, 2180, always_xy=True)
rows = []
for identifier in (628899553, 628899554):
    source = json.loads((out / f"osm-way-{identifier}.json").read_text(encoding="utf-8-sig"))
    nodes = {element["id"]: element for element in source["elements"] if element["type"] == "node"}
    way = next(element for element in source["elements"] if element["type"] == "way" and element["id"] == identifier)
    points = [transform.transform(nodes[node]["lon"], nodes[node]["lat"]) for node in way["nodes"]]
    if points[0] == points[-1]:
        points.pop()
    # Translate first, avoiding cancellation in the metric-coordinate area sum.
    origin = points[0]
    local = [(x - origin[0], y - origin[1]) for x, y in points]
    area = abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(local, local[1:] + local[:1]))) / 2
    rows.append(dict(osm_way=identifier, way_version=way["version"], way_timestamp=way["timestamp"], tags=way.get("tags", {}),
                     point_count=len(points), bbox_size_m=[max(p[k] for p in points) - min(p[k] for p in points) for k in (0, 1)],
                     mean_position_epsg2180=[sum(p[k] for p in points) / len(points) for k in (0, 1)],
                     area_m2=area, equivalent_area_diameter_m=2 * math.sqrt(area / math.pi),
                     maximum_vertex_diameter_m=max(math.dist(a, b) for a in points for b in points),
                     source_url=f"https://api.openstreetmap.org/api/0.6/way/{identifier}/full.json"))
result = dict(retrieved_utc=datetime.now(timezone.utc).isoformat(), attribution="© OpenStreetMap contributors, ODbL",
              copyright_url="https://www.openstreetmap.org/copyright", rows=rows,
              limitation="OSM planar outline alone does not establish whether mapped circle is base or visible crown; top diameter remains unverified")
(out / "chimney-osm-preflight.json").write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps(result, indent=2, ensure_ascii=False))
