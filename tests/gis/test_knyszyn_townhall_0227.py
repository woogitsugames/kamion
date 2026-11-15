"""Contract checks for the authored town hall; this does not replace visual QA."""
import json
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import MultiPoint, Point, Polygon

from streetscape import buildings_mesh as BM
from streetscape import knyszyn_townhall_0227 as townhall

ROOT = Path(__file__).resolve().parents[2]


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, vertices, uv, triangles, src, UV1=None):
        self.parts.append((layer, mat, np.asarray(vertices), np.asarray(triangles), src))


def source():
    fc = json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf-8"))
    return {"features": [f for f in fc["features"] if f["id"] in townhall.IDS]}


def test_targets_are_region_specific_and_all_or_nothing():
    fc = source()
    assert townhall.hero_targets("knyszyn", fc) == {bid: townhall.ASSET_ID for bid in townhall.IDS}
    assert townhall.hero_targets("knyszyn-w", fc) == {}
    assert townhall.hero_targets("knyszyn", {"features": fc["features"][:1]}) == {}


def test_real_footprints_produce_valid_geometry_on_both_lods():
    fc = source()
    blds = BM.load(fc, [761611, 612607], [], hero=townhall.hero_targets("knyszyn", fc))
    buf, report = Buffer(), {}
    result = townhall.build(buf, "knyszyn", blds, lambda e,n: np.zeros_like(e)+125, report)
    assert result["status"] == "applied" and result["column_count"] == 4
    assert {p[0] for p in buf.parts} == set(townhall.LAYERS)
    assert {p[1] for p in buf.parts} == {"plaster_white", "plaster_cream", "plinth_dark", "roof_tiles_red", "glass"}
    for layer, material, v, tris, src in buf.parts:
        assert np.isfinite(v).all() and tris.min() >= 0 and tris.max() < len(v)
        area2 = np.linalg.norm(np.cross(v[tris[:,1]]-v[tris[:,0]], v[tris[:,2]]-v[tris[:,0]]), axis=1)
        assert (area2 > 1e-9).all()
        assert src == townhall.ASSET_ID


def test_generic_geometry_is_not_doubled_if_replacement_not_activated():
    blds = BM.load(source(), [761611, 612607], [])
    buf = Buffer()
    result = townhall.build(buf, "knyszyn", blds, lambda e,n: np.zeros_like(e), {})
    assert result["status"] == "skipped" and not buf.parts


def test_real_roof_and_facades_stay_on_bdot_footprints():
    """Regression: rectangle facade floated 3–5 m and roof exceeded footprint by ~150 m²."""
    fc = source()
    blds = BM.load(fc, [761611, 612607], [], hero=townhall.hero_targets("knyszyn", fc))
    by_id = {b["id"]: b["poly"] for b in blds}
    buf = Buffer()
    assert townhall.build(buf, "knyszyn", blds, lambda e,n: np.zeros_like(e)+125, {})["status"] == "applied"
    allowed = shapely.union_all(list(by_id.values())).buffer(1e-5)
    for layer, mat, vertices, triangles, _ in buf.parts:
        if mat == "roof_tiles_red":
            for tri in triangles:
                shape = MultiPoint(vertices[tri,:2]).convex_hull
                assert allowed.covers(shape), (layer, shape.difference(allowed).area)
        if mat == "glass":
            # Floor windows (not dormers): all vertices sit within 6 cm of an actual source wall.
            lower = vertices[vertices[:,2] < 132.0]
            assert len(lower) > 0
            assert max(min(p.exterior.distance(Point(x,y)) for p in by_id.values()) for x,y in lower[:,:2]) < .06
        if mat == "plaster_cream":
            # Only the portico columns have this material at ground level.
            feet = vertices[np.isclose(vertices[:,2],125.0)]
            assert len(feet) >= 16
            wall = by_id[townhall.CULTURE].exterior
            assert max(wall.distance(Point(x,y)) for x,y in feet[:,:2]) < .71
