"""Junction paint from the orthophoto and lines carried through junction patches (ADR 0093).

Reads Data/Regions/<id>/generated/roads_qa.json (roads/build_world.py) and overrides.yaml.
"""
from __future__ import annotations

import json

import pytest
import yaml
from shapely.geometry import Polygon

from conftest import REGION_DIR

QA = REGION_DIR / "generated" / "roads_qa.json"


@pytest.fixture(scope="module")
def qa():
    if not QA.exists():
        pytest.skip("roads_qa.json not built")
    q = json.loads(QA.read_text(encoding="utf-8"))
    if "painted_zones" not in q["summary"]:
        pytest.fail("old roads_qa.json: rebuild the region (ADR 0093)")
    return q


@pytest.fixture(scope="module")
def overrides():
    return yaml.safe_load((REGION_DIR / "overrides.yaml").read_text(encoding="utf-8"))["overrides"]


def test_painted_zone_polygons_are_valid(overrides):
    """Traced polygons: no self-intersection, at least 1 m2, evidence named."""
    zones = [o for o in overrides if o.get("kind") == "painted_zone"]
    assert zones, "no painted zones: s 610 / s 1440 need them"
    for o in zones:
        pg = Polygon(o["polygon_en"])
        assert pg.is_valid, f"{o['id']}: self-intersecting polygon"
        assert pg.area >= 1.0, o["id"]
        assert o.get("reason") and o.get("verify"), o["id"]


def test_authored_islands_with_local_polygons_are_valid(overrides):
    for o in overrides:
        if o.get("kind") == "traffic_island" and o.get("polygon_en"):
            assert Polygon(o["polygon_en"]).is_valid, o["id"]


def test_every_painted_zone_is_built(qa, overrides):
    want = {o["id"] for o in overrides if o.get("kind") == "painted_zone"}
    built = {z["id"] for z in qa["summary"]["painted_zones"] if z["built"]}
    assert want == built, f"not built: {sorted(want - built)}"
    assert not (want & set(qa["summary"]["overrides_stale"]))


def test_painted_zones_lie_on_the_carriageway(qa):
    """Paint triangles off the generated carriageway are dropped; a zone that loses most of its paint is traced on
    something the generator did not build (the NW part of the s 1440 diverge zone is documented as not built)."""
    for z in qa["summary"]["painted_zones"]:
        total = z["tris"] + z["tris_off_carriageway"]
        assert z["tris"] >= 0.55 * total, z


def test_lines_run_through_junction_patches(qa):
    """REVIEW 0076 #1-#5 / 0077 #5, #7, #8: junction patches used to be bare asphalt."""
    t = qa["summary"]["through_lines"]
    assert t["junctions"] >= 40, t
    assert t["lines"].get("lane", 0) >= 80, t
    assert t["lines"].get("P-7b", 0) >= 20, t


def test_no_stacked_crossings(qa):
    assert "crossings_merged" in qa["summary"]
