"""QA "vertical terrain wall > 0.15 m" (REVIEW r4 W-H5): no steep verge / yard skirt may stand more than 0.15 m above
the conformed terrain (kerb faces and edgings excluded). Written by build_world.py (terrain_mesh.conform.terrain_walls)."""

from __future__ import annotations

import json

import pytest

from conftest import REGION_DIR

QA = REGION_DIR / "generated" / "terrain_walls_qa.json"
RATCHET = {"skirt:yard_asphalt": 1, "skirt:yard_concrete": 2, "skirt:yard_slabs": 1,   # yard_concrete 3 -> 2: tips trimmed (ADR 0093)
           "steep_grass:verge_grass": 0,     # 8 -> 4 (ADR 0074) -> 0 (ADR 0076: verges of one carriageway lying on
                                             # another are culled, merge branches share one height surface)
           "skirt:j:road_asphalt": 0}        # flush junction corners reach the neighbouring carriageway (ADR 0076;
                                             # j:n10015785253 had a 0.3-0.9 m slot 0.5 m deep)
# 5 points, build of 2026-11-11 (v3.5.2: faces < 0.15 m thick are slivers; ADR 0049: constrained-Delaunay junction
# fill removed j:n1847044961)


def test_no_vertical_terrain_walls():
    if not QA.exists():
        pytest.skip("terrain_walls_qa.json missing: run roads/build_world.py")
    q = json.loads(QA.read_text(encoding="utf-8"))
    assert q["thresh_m"] <= 0.15
    assert "by_source" in q, "old QA format: rebuild the region"
    # ratchet (ADR 0033): target 0; lower these numbers whenever a fix lands, never raise them
    for cat, n in q["by_source"].items():
        assert cat in RATCHET, f"new wall category {cat} ({n} points), worst {q['worst'][:5]}"
        assert n <= RATCHET[cat], f"{cat}: {n} wall points > {q['thresh_m']} m (ratchet {RATCHET[cat]})"
    assert q["count"] <= sum(RATCHET.values())
    # every remaining wall is listed with its exposed face area (real wall vs sliver, ADR 0033 v3.5.2)
    assert "skirt_area" in q and "thin_steep_faces_skipped" in q


def test_marking_paint_is_worn():
    m = json.loads((REGION_DIR / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    mats = m.get("materials", m)
    c = mats["marking_white"]["color"]
    assert 0.55 <= max(c[:3]) <= 0.65
