"""Read named Pietrasze features from the pinned local OSM source, without downloads."""
import json
from pathlib import Path

import osmium
from pyproj import Transformer
from shapely import wkb
from shapely import affinity
from shapely.ops import transform

ROOT = Path(__file__).resolve().parents[2]
projection = Transformer.from_crs(4326, 2180, always_xy=True)
factory = osmium.geom.WKBFactory()
features = []


class NamedForest(osmium.SimpleHandler):
    def node(self, node):
        name = node.tags.get("name", "")
        if name.lower() != "las pietrasze" or not node.location.valid():
            return
        e, n = projection.transform(node.location.lon, node.location.lat)
        features.append(dict(kind="node", id=node.id, name=name,
                             tags=dict(node.tags), en=[e - 777995, n - 596223]))

    def area(self, area):
        name = area.tags.get("name", "")
        if name.lower() != "las pietrasze":
            return
        geometry = wkb.loads(factory.create_multipolygon(area), hex=True)
        geometry = transform(projection.transform, geometry)
        bounds = geometry.bounds
        features.append(dict(kind="area", id=area.id, name=name,
                             tags={k: area.tags[k] for k in ("name", "landuse", "leaf_type", "operator") if k in area.tags},
                             geometry_local=affinity.translate(geometry, -777995, -596223).__geo_interface__,
                             bounds_local_m=[bounds[0] - 777995, bounds[1] - 596223,
                                             bounds[2] - 777995, bounds[3] - 596223]))


NamedForest().apply_file(str(ROOT / "Data/raw/osm/podlaskie-261108.osm.pbf"), locations=True)
result = dict(source="podlaskie-261108.osm.pbf (same pinned source as far-field manifest)",
              attribution="OpenStreetMap contributors, ODbL 1.0", features=features)
path = ROOT / "artifacts/edge-far-r2/pietrasze-source-identity.json"
path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(result, ensure_ascii=False, indent=2))
