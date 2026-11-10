"""r4 W-H4: a quality tier may change detail, never the city. Low draws `buildings_lod1` away from the route, High draws
`buildings` (LOD0); every building must keep its footprint and its facade colour across that switch.

Run: uv run --project tools/worldgen pytest tests/gis/test_world_tiers.py -q   (needs Data/raw/derived world GLBs)
Print-out of the worst buildings: uv run --project tools/worldgen python tests/gis/tier_consistency.py
"""

from __future__ import annotations

import json

import numpy as np
import pytest

from conftest import REGION_DIR, REPO
from tier_consistency import colour_delta, compare_region

WORLD = REPO / "Data" / "raw" / "derived" / "bialystok-industrial-c" / "world"

# Thresholds (WORKING_VALUE, chosen from the v3.5 distribution, see the module docstring of tier_consistency.py):
COVER_MIN = 0.85        # share of the LOD0 footprint core (eroded 2 m) covered by the LOD1 roof
CHROMA_MAX = 0.15       # max |rgb/sum| difference: green vs grey is ~0.1-0.2, red brick with/without glazing 0.14
LUM_RATIO = (0.45, 2.2)  # LOD1 / LOD0 facade luminance (LOD0 dock doors and glazing darken halls; no white / black swap)


@pytest.fixture(scope="module")
def rows():
    if not any(WORLD.glob("chunk_*.glb")):
        pytest.skip("world GLBs not built (Data/raw is not versioned)")
    mats = json.loads((REGION_DIR / "generated" / "world_manifest.json").read_text(encoding="utf-8"))["materials"]
    return compare_region(WORLD, mats)


def test_every_building_has_a_lod1_with_the_same_footprint(rows):
    assert len(rows) > 200
    bad = [r for r in rows if r["cover"] < COVER_MIN]
    assert not bad, f"{len(bad)} buildings change footprint between tiers: {bad[:5]}"


def test_facade_colour_is_kept_across_tiers(rows):
    out = []
    for r in rows:
        assert r["rgb0"] is not None and r["rgb1"] is not None, f"building without facades in one tier: {r}"
        lum, chroma = colour_delta(r["rgb0"], r["rgb1"])
        if chroma > CHROMA_MAX or not LUM_RATIO[0] <= lum <= LUM_RATIO[1]:
            out.append((r["at"], round(lum, 2), round(chroma, 3)))
    assert not out, f"{len(out)} buildings change colour between tiers: {out[:8]}"
    ch = [colour_delta(r["rgb0"], r["rgb1"])[1] for r in rows]
    assert np.percentile(ch, 95) < 0.05
