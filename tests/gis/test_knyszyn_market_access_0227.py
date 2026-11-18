"""Market access: the authored fence must not block the service-road gate."""
import json
from pathlib import Path

import numpy as np
import yaml
from shapely.geometry import LineString, Polygon

from roads.network import edge_section
from streetscape import knyszyn_market_0227 as market_mesh


ROOT = Path(__file__).resolve().parents[2]
SERVICE_EDGE = "w1473558111:3047498863-4898870292"
LONGITUDINAL_SERVICE_EDGE = "w498482913:4898870294-4898870293"


def test_market_fences_keep_service_road_corridor_clear():
    overrides = yaml.safe_load((ROOT / "Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    market = next(o for o in overrides if o.get("kind") == "market_canopies_0227")
    fences = {f["id"]: LineString(f["points_epsg2180"]) for f in market["fences"]}
    graph = json.loads((ROOT / "Data/Regions/knyszyn/roads.graph.json").read_text(encoding="utf-8"))
    edge = next(e for e in graph["edges"] if e["id"] == SERVICE_EDGE)
    road = LineString(edge["geometry"])
    # Width is generated from class-D defaults, not measured on site.
    assert edge["attrs"]["highway"]["v"] == "service"
    assert "width" not in edge["attrs"]
    assert edge_section(edge).width == 5.0
    # 2.5 m half-width + 1 m provisional clearance to the fence centreline;
    # this is a geometric guard, not a swept-path proof for a truck.
    for fence in fences.values():
        assert fence.distance(road) >= 3.5
    assert fences["north-fence"].distance(fences["south-fence"]) >= 7.0


def test_canopies_and_post_colliders_clear_longitudinal_service_road():
    overrides = yaml.safe_load((ROOT / "Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    market = next(o for o in overrides if o.get("kind") == market_mesh.KIND)
    graph = json.loads((ROOT / "Data/Regions/knyszyn/roads.graph.json").read_text(encoding="utf-8"))
    edge = next(e for e in graph["edges"] if e["id"] == LONGITUDINAL_SERVICE_EDGE)
    assert edge["attrs"]["highway"]["v"] == "service"
    assert "width" not in edge["attrs"]
    # Class-D 5 m is the generator default, NOT a measured width.
    width = edge_section(edge).width
    assert width == 5.0
    road = LineString(edge["geometry"]).buffer(width / 2, cap_style="flat")
    for canopy in market["canopies"]:
        center, axis, across, length, breadth = market_mesh._rect_frame(
            canopy["polygon_epsg2180"], np.zeros(2))
        roof = Polygon([center + axis*a + across*b for a,b in
                        ((-length/2,-breadth/2),(length/2,-breadth/2),
                         (length/2,breadth/2),(-length/2,breadth/2))])
        assert not roof.intersects(road), canopy["id"]
        _, _, points = market_mesh._post_positions(center, axis, across, length, breadth)
        h = market_mesh.POST_HALF_M
        for point in points:
            post = Polygon([point + axis*a + across*b for a,b in
                            ((-h,-h),(h,-h),(h,h),(-h,h))])
            assert not post.intersects(road), canopy["id"]
    # No vehicle swept-path or real-world survey is established here.
