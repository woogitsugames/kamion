"""Market paving: sourced islands remain open ground and red bands do not overlap."""
import numpy as np
import pytest
import yaml
from pathlib import Path
from types import SimpleNamespace
from shapely.geometry import Point, Polygon, box
from shapely import affinity
from shapely.ops import unary_union

from roads import network, pipeline, standards
from streetscape import paved, stage, vegetation


def _source():
    bdot = {"id": "ground", "props": {"materialnawierzchni": "beton"},
            "geometry": {"coordinates": [list(map(list, box(0, 0, 30, 20).exterior.coords))]}}
    return {"osm": {"areas": []}, "bdot10k": {"OT_PTPL_A": [bdot], "OT_KUKO_A": [], "OT_SKRP_L": []}}


def _area(holes):
    return {"id": "market", "kind": "paved_area", "material": "yard_paving",
            "polygon_epsg2180": [[0, 0], [30, 0], [30, 20], [0, 20]],
            "holes_epsg2180": holes}


def _collect(overrides):
    return paved.collect(_source(), np.zeros(2), overrides, [], Polygon(), None, {})


def test_islands_block_lower_priority_paving_and_band_has_no_overlap():
    island = [[12, 7], [18, 7], [18, 13], [12, 13]]
    band = {"id": "red", "kind": "paved_area", "material": "sidewalk_paving_red",
            "polygon_epsg2180": [[0, 2], [30, 2], [30, 5], [0, 5]]}
    result = _collect([band, _area([island])])
    assert not any(item["poly"].covers(Point(15, 10)) for item in result)
    red = [item["poly"] for item in result if item["mat"] == "sidewalk_paving_red"]
    grey = [item["poly"] for item in result if item["mat"] == "yard_paving"]
    assert red and grey
    assert all(a.intersection(b).area < 1e-7 for a in red for b in grey)
    # The established 5 cm morphological cleanup trims small boundary slivers.
    assert sum(p.area for p in red + grey) == pytest.approx(30 * 20 - 6 * 6, abs=6)


@pytest.mark.parametrize("holes", [
    [[[-1, 1], [2, 1], [2, 3], [-1, 3]]],  # outside outer ring
    [[[0, 1], [2, 1], [2, 3], [0, 3]]],    # touching boundary
    [[[5, 5], [10, 5], [10, 10], [5, 10]], [[8, 8], [12, 8], [12, 12], [8, 12]]],
    [[[4, 4], [8, 8], [4, 8], [8, 4]]],    # self-intersection
])
def test_invalid_islands_are_rejected(holes):
    with pytest.raises(ValueError, match="invalid or overlapping holes"):
        _collect([_area(holes)])


def test_stage_yard_source_preserves_island_and_origin():
    origin = np.array([760000., 613000.])
    override = _area([[[760012, 613007], [760018, 613007], [760018, 613013], [760012, 613013]]])
    override["polygon_epsg2180"] = [[760000, 613000], [760030, 613000], [760030, 613020], [760000, 613020]]
    items = stage._yard_src({"osm": {"areas": []}, "bdot10k": {"OT_PTPL_A": []}}, origin, [override])
    assert len(items) == 1
    assert not items[0].covers(Point(15, 10))
    assert items[0].covers(Point(4, 10))
    assert items[0].area == pytest.approx(30 * 20 - 6 * 6)
    pipeline_footprint = pipeline._authored_paved_polygon(override, origin)
    assert pipeline_footprint.equals(items[0])


def test_real_market_bands_islands_and_spruce_clearance():
    root = Path(__file__).resolve().parents[2]
    data = yaml.safe_load((root / "Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf8"))["overrides"]
    market = [x for x in data if x.get("id", "").startswith(("market-paving-", "market-landscaping-"))]
    assert len(market) == 8
    outer = next(x for x in market if x["id"] == "market-paving-base-0227")
    assert outer.get("bare_soil_holes") is True
    assert all(x.get("bare_soil") is True for x in market if x["kind"] == "unpaved_area")
    poly = Polygon(outer["polygon_epsg2180"], outer["holes_epsg2180"])
    assert poly.is_valid and 4500 < poly.area < 6000
    assert outer["material"] == "apron_paving_light"
    islands = [Polygon(hole) for hole in outer["holes_epsg2180"]]
    islands += [Polygon(x["polygon_epsg2180"]) for x in market if x["kind"] == "unpaved_area"]
    red = [Polygon(x["polygon_epsg2180"]) for x in market if x.get("material") == "sidewalk_paving_red"]
    assert len(islands) == 8 and len(red) == 4
    assert all(r.is_valid and r.area > 3 for r in red)
    assert all(r.intersection(island).area < .1 for r in red for island in islands)
    assert all(a.intersection(b).area < .1 for i, a in enumerate(red) for b in red[i + 1:])
    # The spruce near the west building stands on a landscaped island, not in
    # the paving hard mask. Position remains an owner-photo estimate.
    spruce = Point(760803.5, 613217.0)
    assert any(island.covers(spruce) for island in islands)
    assert poly.distance(spruce) >= 1.0
    # An overlapping lower-priority source cannot refill the authored islands.
    footprint = box(760740, 613180, 760860, 613370)
    bdot = {"id": "source", "props": {"materialnawierzchni": "beton"},
            "geometry": {"coordinates": [list(map(list, footprint.exterior.coords))]}}
    src = {"osm": {"areas": []}, "bdot10k": {"OT_PTPL_A": [bdot], "OT_KUKO_A": [], "OT_SKRP_L": []}}
    origin = np.array([761611., 612607.])
    results = paved.collect(src, origin, market, [], Polygon(), None, {})
    covered = unary_union([x["poly"] for x in results])
    for island in islands:
        local = affinity.translate(island, -origin[0], -origin[1])
        assert covered.intersection(local.buffer(-.1)).area < .1


def test_light_market_paving_uses_paving_collision():
    class Accumulator:
        def __init__(self):
            self.parts = []

        def add(self, *args, **kwargs):
            self.parts.append((args, kwargs))

    buf = Accumulator()
    hf = SimpleNamespace(x0=0., y1=10.)
    item = {"id": "market", "poly": box(1, 1, 5, 5), "mat": "apron_paving_light", "park_flush": True}
    paved.build_meshes(buf, [item], np.ones((11, 11)), hf)
    assert standards.SURFACE_OF["apron_paving_light"] == "paving"
    assert any(args[0] == "collision" and args[1] == "collision_paving" for args, _ in buf.parts)


def test_bare_soil_opt_in_is_bounded_and_keeps_hard_mask_unchanged():
    hf = SimpleNamespace(z=np.zeros((31, 31)), x0=0., y1=30.)
    col = np.zeros((31, 31, 4), dtype=np.float32)
    col[..., 1] = .2
    hard = np.zeros((31, 31), dtype=bool)
    hard[15, 15] = True
    before_hard = hard.copy()
    island = [[10, 10], [20, 10], [20, 20], [10, 20]]
    unpaved = {"id": "bed", "kind": "unpaved_area", "polygon_en": island, "bare_soil": True}
    without_optin = [{k: v for k, v in unpaved.items() if k != "bare_soil"}]
    assert np.array_equal(vegetation.authored_bare_ground(col, hf, (0, 0), without_optin, hard), col)
    painted = vegetation.authored_bare_ground(col, hf, (0, 0), [unpaved], hard)
    assert painted[16, 14, 3] > 0
    assert np.array_equal(painted[15, 15], col[15, 15])  # road / paving preserved
    assert np.array_equal(painted[0, 0], col[0, 0])    # no spill outside island
    assert np.array_equal(painted[..., :1], col[..., :1])
    assert np.array_equal(painted[..., 2], col[..., 2])
    assert np.array_equal(hard, before_hard)
    assert not col[..., 3].any()
    holes = _area([island])
    holes["bare_soil_holes"] = True
    assert np.array_equal(vegetation.authored_bare_ground(col, hf, (0, 0), [holes], hard), painted)


def test_market_service_overrides_change_only_two_intended_edges():
    import json

    root = Path(__file__).resolve().parents[2]
    graph = json.loads((root / "Data/Regions/knyszyn/roads.graph.json").read_text(encoding="utf8"))
    overrides = yaml.safe_load((root / "Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf8"))["overrides"]
    market = [o for o in overrides if o["id"] in ("market-interior-service-paving-0227", "market-crossing-service-paving-0227")]
    assert len(market) == 2
    net = network.load(graph, (761611., 612607.), market)
    target = ["w498482913:4898870294-4898870293", "w498483028:4898906615-4898870293"]
    untouched = ["w498483028:4898911740-4898906615", "w498483028:4898911741-4898911740"]
    assert all(net.sections[e].surface_mat == "road_paving" for e in target)
    assert all(net.sections[e].surface_mat == "road_gravel" for e in untouched)
