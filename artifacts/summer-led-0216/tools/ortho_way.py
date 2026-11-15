"""ADR 0216: GUGiK ortho crops (WMS HighResolution, 0.1 m) at fractions along an OSM way of a region graph.
usage: ortho_way.py <region> <osm_way> <outdir> [fractions...]"""
import json, sys, io, os, time, requests
from shapely.geometry import LineString
from shapely.ops import linemerge
from PIL import Image
rid, way, od = sys.argv[1], int(sys.argv[2]), sys.argv[3]; fr = [float(a) for a in sys.argv[4:]] or [0.5]
g = json.load(open(f"Data/Regions/{rid}/roads.graph.json", encoding="utf-8"))
ls = linemerge([LineString(e["geometry"]) for e in g["edges"] if e["osm_way"] == way])
if ls.geom_type != "LineString": ls = max(ls.geoms, key=lambda l: l.length)
os.makedirs(od, exist_ok=True)
for f in fr:
    p = ls.interpolate(f, normalized=True); half = 60
    q = {"SERVICE": "WMS", "VERSION": "1.1.1", "REQUEST": "GetMap", "LAYERS": "Raster", "STYLES": "", "SRS": "EPSG:2180",
         "BBOX": f"{p.x-half},{p.y-half},{p.x+half},{p.y+half}", "WIDTH": 1200, "HEIGHT": 1200, "FORMAT": "image/jpeg"}
    r = requests.get("https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution", params=q,
                     headers={"User-Agent": "research-client/1.0 (generic)"}, timeout=120)
    im = Image.open(io.BytesIO(r.content)).convert("RGB"); name = f"{od}/{rid}_w{way}_f{int(f*100):03d}.jpg"
    im.resize((960, 960), Image.LANCZOS).save(name, quality=88); print(name, round(p.x, 1), round(p.y, 1)); time.sleep(1)
