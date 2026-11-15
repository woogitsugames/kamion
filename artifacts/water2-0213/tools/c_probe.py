"""ADR 0213 par. 4 (evaluation only, nothing written to Data/): water sources of tile C as the stage would read them."""
import json, sys
from pathlib import Path
import yaml, shapely, shapely.geometry as G
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools/worldgen"))
from streetscape import water as WT
rid = sys.argv[1] if len(sys.argv) > 1 else "bialystok-industrial-c"
ry = yaml.safe_load((ROOT / "Data/Regions" / rid / "region.yaml").read_text(encoding="utf-8"))
d = WT.extract(ry)
out = ROOT / "artifacts/water2-0213" / f"{rid}-water_sources.probe.json"
out.write_text(json.dumps(d, ensure_ascii=False), encoding="utf-8")
b = ry["bbox"]; tile = shapely.box(b["xmin"], b["ymin"], b["xmax"], b["ymax"])
for f in d["bdot10k"]["OT_PTWP_A"]:
    g = G.shape(f["geometry"]); print("PTWP", f["props"], round(g.intersection(tile).area))
for f in d["bdot10k"]["OT_SWRS_L"]:
    g = G.shape(f["geometry"]); print("SWRS", f["props"], round(g.intersection(tile).length))
for a in d["osm"]["areas"]:
    g = G.shape(a["geometry"]); print("OSMA", a["tags"], round(g.intersection(tile).area))
for a in d["osm"]["lines"]:
    g = G.shape(a["geometry"]); print("OSML", a["tags"], round(g.intersection(tile).length))
