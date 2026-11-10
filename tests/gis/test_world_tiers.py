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


# Silhouette parity (HANDOVER pkt 7, review r6): docks, shelters, gutters, downpipes exist on LOD1 wherever LOD0 has
# them, so Low (LOD1 away from the route) and High show the same buildings; only the detail density may differ.
# LOD0 material -> the LOD1 material that carries the same piece (FK.L1_MAT merges tones to save draws)
SILHOUETTE = {"dock_shelter": "hall_flashing", "dock_door": "dock_door", "downpipe": "downpipe", "gutter": "downpipe",
              "chimney_brick": "chimney_brick"}


def test_lod1_keeps_the_silhouette_pieces():
    from route_corridor import node_triangles, read_glb
    files = sorted(f for f in WORLD.glob("chunk_*.glb") if not f.name.endswith(".low.glb"))
    if not files:
        pytest.skip("world GLBs not built (Data/raw is not versioned)")
    missing, n0, n1 = [], {}, {}
    for f in files:
        doc, data, off = read_glb(f)
        t0 = node_triangles(doc, data, off, "buildings")
        t1 = node_triangles(doc, data, off, "buildings_lod1")
        for m0, m1 in SILHOUETTE.items():
            k0, k1 = len(t0.get(m0, ())), len(t1.get(m1, ()))
            n0[m0] = n0.get(m0, 0) + k0
            n1[m1] = n1.get(m1, 0) + k1
            if k0 and not k1:
                missing.append((f.name, m0, k0))
    assert not missing, f"LOD0-only silhouette pieces: {missing[:8]}"
    assert n1["dock_door"] > 0 and n1["downpipe"] > 0
    # LOD1 stays cheaper than LOD0 (the density may differ, the presence may not)
    assert n1["dock_door"] <= n0["dock_door"] and n1["downpipe"] < n0["downpipe"] + n0["gutter"], (n0, n1)


def test_low_variant_carries_the_lod1_silhouette():
    """chunk_*.low.glb (WorldC, the default APK) has the same LOD1 node as the High chunk."""
    from route_corridor import node_triangles, read_glb
    files = sorted(WORLD.glob("chunk_*.low.glb"))
    if not files:
        pytest.skip("world GLBs not built")
    shelters = 0
    for f in files:
        doc, data, off = read_glb(f)
        shelters += len(node_triangles(doc, data, off, "buildings_lod1").get("dock_door", ()))
    assert shelters > 0
