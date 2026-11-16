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


# ------------------------------------------------------------------------------- (d) compact roundabout outer diameter
from roads import compact_roundabout as CR  # noqa: E402

KERB = {"entry_r_m": 6.0, "exit_r_m": 8.0, "splitter_w_m": 2.4, "lane_w_m": 4.0}


def _ring(extra_overrides=(), opts=None):
    ov = T18._ov(True, dict(KERB) if opts is None else opts) + list(extra_overrides)
    net = Nw.load(T18._graph(), (0.0, 0.0), ov)
    Nw.assign_sides(net, [], built_up=True, walkways=[], yards=None)
    juncs = J.build_junctions(net, [])
    T18._flat(net)
    return net, next((j for j in juncs if j.compact is not None), None)


def _d_ov(d):
    return {"id": "d41", "target": {"osm_way": [T18.RING_WAY]}, "set": {"compact_roundabout": {"outer_diameter_m": d}}}


def test_outer_diameter_sets_the_ring_and_keeps_the_kerb_mode_options():
    net, j = _ring([_d_ov(26.0)])
    sp = j.compact
    assert "d41" not in net.overrides_stale
    assert sp.r_out == pytest.approx(13.0, abs=1e-6) and sp.r_axis_fit == pytest.approx(T18.R_AXIS, abs=0.15)
    assert CR.kerb_mode(sp.opts) and sp.opts["entry_r_m"] == 6.0          # merged with the first override, not replaced
    rep = CR.report_one(sp)
    assert rep["r_outer_m"] == 13.0 and rep["r_axis_fit_m"] == pytest.approx(T18.R_AXIS, abs=0.15) and rep["notes"] == []
    # the designed lanes meet the ring on the authored axis circle, not at the mapped (smaller) ring nodes
    ends = []
    for c in sp.feeders:
        e = c.line.p[-1] if np.hypot(*(c.line.p[-1] - sp.center)) < np.hypot(*(c.line.p[0] - sp.center)) else c.line.p[0]
        ends.append(float(np.hypot(*(e - sp.center))))
    assert np.allclose(ends, sp.r_axis, atol=0.05), ends
    assert sp.outline is not None and sp.outline.is_valid
    assert Polygon(sp.outline.exterior).buffer(0).contains(Polygon(
        sp.center + 12.9 * np.column_stack([np.cos(np.linspace(0, 6.283, 64)), np.sin(np.linspace(0, 6.283, 64))])))


def test_without_the_key_the_fitted_radius_stays():
    net, j = _ring()
    assert j.compact.r_axis == pytest.approx(j.compact.r_axis_fit) and j.compact.r_out == pytest.approx(
        T18.R_AXIS + T18.W_RING / 2, abs=0.15)


@pytest.mark.parametrize("bad", [50.0, 10.0, "26", True, float("nan"), -26.0])
def test_outer_diameter_out_of_range_is_stale(bad):
    net, j = _ring([_d_ov(bad)])
    assert "d41" in net.overrides_stale
    assert j.compact.r_axis == pytest.approx(j.compact.r_axis_fit) and CR.kerb_mode(j.compact.opts)


@pytest.mark.parametrize("d", [31.0, 15.0])
def test_outer_diameter_too_far_from_the_mapped_ring_is_stale(d):
    """In range (14-40 m) but more than max(2 m, 40 %) off the fitted axis radius: wrong target or typo."""
    net, j = _ring([_d_ov(d)])
    assert "d41" in net.overrides_stale
    assert j.compact.r_axis == pytest.approx(j.compact.r_axis_fit)
    assert any("rejected" in n for n in j.compact.notes)


def test_knyszyn_override_sets_26_m_working_value():
    import yaml
    ov = yaml.safe_load((ROOT / "Data/Regions/knyszyn/overrides.yaml").read_text(encoding="utf-8"))["overrides"]
    o = next(o for o in ov if o["id"] == "knyszyn-roundabout-outer-diameter-d41")
    assert o["set"] == {"compact_roundabout": {"outer_diameter_m": 26.0}} and "WORKING_VALUE" in o["reason"]
    assert CR.validate(o["set"]["compact_roundabout"]) == {"outer_diameter_m": 26.0}
    ids = [x["id"] for x in ov]
    assert ids.index(o["id"]) > ids.index("knyszyn-roundabout-compact")     # merged after the kerb-mode entry
