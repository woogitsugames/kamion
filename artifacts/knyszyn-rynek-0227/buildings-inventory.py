import json
from shapely.geometry import shape, Point
fc=json.load(open('Data/Regions/knyszyn/buildings.geojson',encoding='utf8'))
p=Point(760943.5,612382.3)
for f in fc['features']:
 g=shape(f['geometry']); d=g.distance(p)
 if d<85:
  q=f['properties']; c=g.centroid
  print(f"{q['id']} | {c.x:.1f},{c.y:.1f} | {d:.1f} m | {q['function']} | {q['storeys']} | {q['height_m']} m {q['height_source']} | roof={q['roof_type_lod2']}")
