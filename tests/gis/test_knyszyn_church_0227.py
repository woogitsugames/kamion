"""Contract tests for the opt-in church landmark; visual acceptance is separate."""
import json
from pathlib import Path

import numpy as np

from streetscape import buildings_mesh as BM
from streetscape import knyszyn_church_0227 as church


ROOT = Path(__file__).resolve().parents[2]


class Buffer:
    def __init__(self):
        self.parts = []

    def add(self, layer, mat, vertices, uv, triangles, src, UV1=None):
        self.parts.append((layer, mat, np.asarray(vertices), np.asarray(triangles), src))


def test_region_and_source_are_required():
    fc = {"features": [{"id": church.BUILDING_ID}]}
    assert church.hero_targets("knyszyn", fc) == {church.BUILDING_ID: church.ASSET_ID}
    assert church.hero_targets("knyszyn-w", fc) == {}
    assert church.hero_targets("knyszyn", {"features": []}) == {}


def test_real_footprint_builds_both_tiers_with_lod2_silhouette():
    fc = json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf-8"))
    feature = next(f for f in fc["features"] if f["id"] == church.BUILDING_ID)
    fc = {"features": [feature]}
    blds = BM.load(fc, [761611, 612607], [], hero=church.hero_targets("knyszyn", fc))
    buf, report = Buffer(), {}
    result = church.build(buf, "knyszyn", blds, lambda e, n: np.zeros_like(e) + 127.25, report)
    assert result["status"] == "applied"
    assert result["height_lod2_m"] == feature["properties"]["height_lod2_2017_m"]
    assert {p[0] for p in buf.parts} == set(church.LAYERS)
    assert {p[1] for p in buf.parts} == {"plaster_white", "roof_tiles_red", "glass"}
    for layer, mat, vertices, triangles, src in buf.parts:
        assert np.isfinite(vertices).all()
        assert triangles.min() >= 0 and triangles.max() < len(vertices)
        assert src == church.ASSET_ID
    assert max(float(p[2][:, 2].max()) for p in buf.parts) == 127.25 + result["height_lod2_m"]


def test_without_hero_target_no_duplicate_generic_geometry():
    fc = json.loads((ROOT / "Data/Regions/knyszyn/buildings.geojson").read_text(encoding="utf-8"))
    fc["features"] = [f for f in fc["features"] if f["id"] == church.BUILDING_ID]
    blds = BM.load(fc, [761611, 612607], [])
    buf = Buffer()
    result = church.build(buf, "knyszyn", blds, lambda e, n: np.zeros_like(e), {})
    assert result["status"] == "skipped"
    assert not buf.parts
