"""QA "vertical terrain wall > 0.15 m" (REVIEW r4 W-H5): no steep verge / yard skirt may stand more than 0.15 m above
the conformed terrain (kerb faces and edgings excluded). Written by build_world.py (terrain_mesh.conform.terrain_walls)."""

from __future__ import annotations

import json

import pytest

from conftest import REGION_DIR

QA = REGION_DIR / "generated" / "terrain_walls_qa.json"


def test_no_vertical_terrain_walls():
    if not QA.exists():
        pytest.skip("terrain_walls_qa.json missing: run roads/build_world.py")
    q = json.loads(QA.read_text(encoding="utf-8"))
    assert q["thresh_m"] <= 0.15
    assert "by_source" in q, "old QA format: rebuild the region"
    assert q["count"] == 0, f"{q['count']} wall points > {q['thresh_m']} m {q['by_source']}, worst {q['worst'][:5]}"


def test_marking_paint_is_worn():
    m = json.loads((REGION_DIR / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    mats = m.get("materials", m)
    c = mats["marking_white"]["color"]
    assert 0.55 <= max(c[:3]) <= 0.65
