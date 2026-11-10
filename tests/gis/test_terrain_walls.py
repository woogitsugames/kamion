"""QA "vertical terrain wall > 0.15 m" (REVIEW r4 W-H5): no steep verge / yard skirt may stand more than 0.15 m above
the conformed terrain (kerb faces and edgings excluded). Written by build_world.py (terrain_mesh.conform.terrain_walls)."""

from __future__ import annotations

import json

import pytest

from conftest import REGION_DIR

QA = REGION_DIR / "generated" / "terrain_walls_qa.json"
RATCHET = {"skirt:j": 85, "skirt:yard_asphalt": 1, "skirt:yard_concrete": 8, "skirt:yard_slabs": 1,
           "steep_grass:verge_grass": 8}     # 103 points, build of 2026-11-10 (e81fbfe)


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


def test_marking_paint_is_worn():
    m = json.loads((REGION_DIR / "generated" / "world_manifest.json").read_text(encoding="utf-8"))
    mats = m.get("materials", m)
    c = mats["marking_white"]["color"]
    assert 0.55 <= max(c[:3]) <= 0.65
