"""ADR 0227 dopisek D41 (rynek-p1-s23): market canopies, market pavilion, linden crown shape, compact roundabout outer
diameter and the kerb edge of the DK65 south entry. Synthetic data only (no Data/raw, no generated/*).
Run: uv run --project tools/worldgen python -m pytest tests/gis/test_rynek_p1_0227.py -q
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import LineString, Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import test_compact_roundabout_0218 as T18  # noqa: E402
from roads import junctions as J  # noqa: E402
from roads import meshing as M  # noqa: E402
from roads import network as Nw  # noqa: E402


# ------------------------------------------------------------------------------------- (e) kerb edge, mixed corners
def _mixed_roundabout(rural_way=T18.ARM_WAY + 1, extra=None):
    g = T18._graph()
    for e in g["edges"]:
        if e["osm_way"] == rural_way:          # a rural arm (GP-like, 90 km/h, no footway): RURAL side profile
            e["attrs"] = dict(e["attrs"], highway=T18._a("primary"), maxspeed=T18._a(90))
    net = Nw.load(g, (0.0, 0.0), T18._ov(True, extra))
    Nw.assign_sides(net, [], built_up=True, walkways=[], yards=None)
    juncs = J.build_junctions(net, [])
    T18._flat(net)
    return net, next(j for j in juncs if j.compact is not None)


def _corner_kinds(j):
    out = {}
    for i, a in enumerate(j.arms):
        out[i] = int(np.unique(a.chain.side["L"]["kind"])[0])
    return out


def test_mixed_corner_of_a_compact_roundabout_has_grass_behind_the_whole_kerb():
    """The rural half of a corner between a rural and a kerbed arm was a bare kerb (no verge, no footway): the terrain
    conform fell off right behind it (DK65 south entry, 0.5-0.74 m within 1.5 m on the 2022 NMT)."""
    net, j = _mixed_roundabout()
    kinds = _corner_kinds(j)
    assert sorted(set(kinds.values())) == [Nw.URBAN, Nw.RURAL]
    buf = M.MeshBuf()
    M.build_patch(buf, net, j)
    n = len(j.arms)
    for i in range(n):
        mixed = kinds[i] != kinds[(i + 1) % n]
        src = f"{j.id}:corner{i}"
        kerb = [p for p in buf.parts if p.src == src and p.mat == "curb_concrete" and p.footprint]
        top = [p for p in buf.parts if p.src == src + ":vg" and p.footprint]
        assert kerb, src
        if not mixed:
            assert top == [], f"{src}: a kerbed-only corner keeps the ADR 0110 verge (not footprint)"
            continue
        assert len(top) == 1, f"{src}: mixed corner needs a soft-footprint verge top"
        V, T = top[0].V, top[0].T
        area = sum(Polygon(V[t, :2]).area for t in T)
        length = LineString(j.corners[i].arc).length
        assert area / length >= 0.8, (src, round(area, 1), round(length, 1))


def test_other_corners_and_junctions_are_unchanged():
    net, j = _mixed_roundabout(rural_way=-1)                    # no rural arm: all corners kerbed
    assert set(_corner_kinds(j).values()) == {Nw.URBAN}
    buf = M.MeshBuf()
    M.build_patch(buf, net, j)
    assert not [p for p in buf.parts if p.src.endswith(":vg") and p.footprint]
