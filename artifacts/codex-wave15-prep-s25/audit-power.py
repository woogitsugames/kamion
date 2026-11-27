"""Compare tracked sources to the proposed OSM power refresh without writing inputs."""
import csv
import json
from pathlib import Path
import subprocess
import types

import yaml

repo = Path.cwd()
path = "tools/worldgen/streetscape/sources.py"
branch = "agy-poles-wires-s25"
commit = subprocess.check_output(["git", "rev-parse", branch], text=True).strip()
src = types.ModuleType("wave15_sources")
src.__file__ = str(repo / path)
code = subprocess.check_output(["git", "show", f"{commit}:{path}"])
exec(compile(code, src.__file__, "exec"), src.__dict__)

tiles = sorted((repo / "Data/Regions").glob("*/region.yaml"))
boxes = {}
for tile in tiles:
    bbox = yaml.safe_load(tile.read_text(encoding="utf-8"))["bbox"]
    boxes[tile.parent.name] = tuple(bbox[k] for k in ("xmin", "ymin", "xmax", "ymax"))
pbf = repo / "Data/raw/osm/podlaskie-261108.osm.pbf"
power = src.extract_osm_power_ways_by_bboxes(boxes, pbf)
out = Path(__file__).with_name("osm-power.csv")
with out.open("w", newline="", encoding="utf-8") as f:
    writer = csv.writer(f, lineterminator="\n")
    writer.writerow(("tile", "schema_before", "schema_after", "power_parts_before",
                     "power_parts_after", "power_content_changed", "other_order_changed"))
    for rid, new in power.items():
        file = repo / "Data/Regions" / rid / "generated/streetscape_sources.json"
        data = json.loads(file.read_text(encoding="utf-8"))
        before = data["osm"]["ways"]
        old = [w for w in before if w["tags"].get("power") in ("line", "minor_line")]
        other = [w for w in before if w["tags"].get("power") not in ("line", "minor_line")]
        other_sorted = sorted(other, key=lambda w: (w.get("osm_type", ""), w.get("osm_way", 0), w.get("part", 0)))
        writer.writerow((rid, data["schema"], src.SCHEMA, len(old), len(new), old != new, other != other_sorted))
print(f"HEAD={subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()}")
print(f"OSM={pbf.name} ({pbf.stat().st_size} bytes), extractor={commit}, tiles={len(tiles)}")
print(out)
