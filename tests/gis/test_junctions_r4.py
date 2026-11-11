"""ADR 0110 (junctions r4 + barriers): verge strips behind kerbs, bridge barrier-railing, guardrail terminals,
Douglas-Peucker of long runs, the P-9 guidance arrow, world numbers of the built region."""
import json
import sys
from pathlib import Path

import numpy as np
import pytest
from shapely.geometry import Polygon

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))
from roads import standards as S  # noqa: E402
from roads.geom import dp_keep  # noqa: E402
from roads.markings import arrow_glyph  # noqa: E402
from roads.meshing import MeshBuf, _emit_verge  # noqa: E402
from streetscape import furniture as FU  # noqa: E402

REGION = ROOT / "Data" / "Regions" / "bialystok-industrial-c"


def test_dp_keep_drops_collinear_points_and_keeps_the_tolerance():
    x = np.arange(0.0, 101.0)
    P = np.column_stack([x, np.zeros_like(x), 100.0 + 0.02 * x])          # straight, graded
    assert dp_keep(P, 0.01).sum() == 2
    # arc R = 300 m: the dropped points stay within the tolerance
    a = x / 300.0
    Q = np.column_stack([300.0 * np.sin(a), 300.0 * (1 - np.cos(a)), np.zeros_like(x)])
    k = dp_keep(Q, 0.01)
    assert 2 < k.sum() < len(Q) / 2
    idx = np.where(k)[0]
    for i0, i1 in zip(idx[:-1], idx[1:]):
        ab = Q[i1] - Q[i0]
        for q in Q[i0 + 1:i1]:
            t = np.clip((q - Q[i0]) @ ab / (ab @ ab), 0, 1)
            assert np.linalg.norm(q - Q[i0] - t * ab) <= 0.01 + 1e-9


def _verge(vw, kap=None, n=60):
    buf = MeshBuf()
    G = np.column_stack([np.arange(n, dtype=float), np.zeros(n)])
    OUT = np.tile([0.0, 1.0], (n, 1))
    zg = 100.0 + 0.01 * G[:, 0]
    _emit_verge(buf, G, OUT, zg, np.full(n, S.KERB_HEIGHT), np.asarray(vw, float),
                np.zeros(n) if kap is None else kap, np.full(n, 3.5), False, "c:test:L:vg")
    return buf


def _slopes(p):
    t = p.V[p.T]
    nrm = np.cross(t[:, 1] - t[:, 0], t[:, 2] - t[:, 0])
    return np.abs(nrm[:, 2]) / np.maximum(np.linalg.norm(nrm, axis=1), 1e-12)


def _top_skirt(buf):
    """(flat top strips, battered skirts) of the verge parts: the top rises 2 % outward, the skirt falls 1 : 1.5."""
    top = [p for p in buf.parts if _slopes(p).min() > 0.99]
    return top, [p for p in buf.parts if not any(p is q for q in top)]


def test_verge_strip_sits_at_the_kerb_crown_and_ends_in_a_1_to_1p5_skirt():
    buf = _verge(np.full(60, 1.0))
    top, skirt = _top_skirt(buf)
    assert len(top) == 1 and len(skirt) == 1 and top[0].mat == "verge_grass"
    # straight graded kerb: one quad per strip (Douglas-Peucker), not one per station
    assert len(top[0].T) == 2 and len(skirt[0].T) == 2
    V = top[0].V
    inner = V[np.isclose(V[:, 1], S.KERB_TOP_W)]
    assert np.allclose(inner[:, 2], 100.0 + 0.01 * inner[:, 0] + S.KERB_HEIGHT)          # kerb crown
    assert np.isclose(V[:, 1].max(), S.KERB_TOP_W + 1.0)
    assert _slopes(skirt[0]).min() > 0.80                                                 # 1 : 1.5 = 0.83 (QA wall < 0.80)
    assert np.isclose(skirt[0].V[:, 2].min() - skirt[0].V[:, 2].max() + S.FLANGE_DEPTH, -0.01 * 59 + 0.0, atol=0.62)


def test_verge_strip_runs_out_over_two_metres_without_steep_faces():
    vw = np.full(60, 1.0)
    vw[:20] = 0.0                                   # e.g. a sidewalk starts / a bridge
    buf = _verge(vw)
    for p in buf.parts:
        # as terrain_mesh.conform.terrain_walls: a grass face steeper than ~1:1.33 counts when it is > 0.15 m tall
        tz = p.V[p.T][:, :, 2]
        steep = _slopes(p) < 0.80
        assert not (steep & (tz.max(1) - tz.min(1) > 0.15)).any(), "steep grass face where the strip starts"
        assert p.V[np.unique(p.T)][:, 0].min() >= 19.0 - 1e-6       # nothing before the last station without a strip
    top = _top_skirt(buf)[0][0]
    V = top.V[np.unique(top.T)]
    w_at = lambda x: V[np.isclose(V[:, 0], x)][:, 1].max() - S.KERB_TOP_W   # noqa: E731
    assert np.isclose(w_at(19.0), 0.0, atol=1e-6) and np.isclose(w_at(21.0), 1.0, atol=1e-6)   # 1 m per 2 m


def test_verge_strip_on_the_inside_of_a_curve_keeps_its_slope():
    buf = _verge(np.full(60, 3.0), kap=np.full(60, 1.0 / 5.0))      # R = 5 m, carriageway half width 3.5 m
    for p in buf.parts:
        assert _slopes(p).min() > 0.80
        assert p.V[:, 1].max() <= 0.9 * 5.0 - 3.5 + 1e-6 or p.V[:, 1].max() <= 0.3 + 1e-6 + 1.0


class _Lin(FU.Lin):
    def __init__(self):
        super().__init__(MeshBuf(), lambda e, n: np.zeros(len(np.atleast_1d(e))))


def _rail(n=80, tall=None, term=(True, True)):
    lin = _Lin()
    P = np.column_stack([np.arange(n, dtype=float), np.zeros(n)])
    FU.guardrail(lin, P, np.full(n, 10.0), "c:test:R:bridge", tall, term)
    return lin.buf.parts


def test_guardrail_free_ends_are_turned_down_and_the_beam_is_decimated():
    parts = _rail()
    beam = [p for p in parts if p.layer == "furniture" and p.mat == "barrier_steel"][0]
    z = beam.V[:, 2] - 10.0
    assert np.isclose(z.max(), S.GUARDRAIL_H)
    ends = beam.V[(beam.V[:, 0] < 0.5) | (beam.V[:, 0] > 78.5)]
    assert np.isclose((ends[:, 2] - 10.0).max(), 0.33)                 # top of the beam at the free end
    # 79 m straight: terminals + one straight piece, not 79 cells (5 rows x 4 kept stations at most 6)
    assert len(beam.V) <= 5 * 6
    posts = [p for p in parts if p.mat == "barrier_post"][0]
    assert posts.V[:, 0].min() >= S.GUARDRAIL_TERMINAL_M - 0.2        # no post standing above the turned-down end


def test_bridge_barrier_railing_has_posts_to_the_handrail_and_two_rails_above_the_beam():
    tall = np.zeros(80, bool)
    tall[20:60] = True
    parts = _rail(tall=tall, term=(False, False))
    posts = [p for p in parts if p.mat == "barrier_post"]
    tops = sorted({round(float(p.V[:, 2].max() - 10.0), 2) for p in posts})
    assert tops == [round(S.GUARDRAIL_H - 0.05, 2), S.BRIDGE_BARRIER_H]
    steel = [p for p in parts if p.layer == "furniture" and p.mat == "barrier_steel"]
    zmax = max(float(p.V[:, 2].max()) for p in steel) - 10.0
    assert np.isclose(zmax, S.BRIDGE_BARRIER_H)
    mid = [p for p in steel if np.isclose(p.V[:, 2].max() - 10.0, S.BRIDGE_BARRIER_MID + 0.03)]
    assert mid and all(p.V[:, 0].min() >= 20.0 - 1e-6 and p.V[:, 0].max() <= 59.0 + 1e-6 for p in mid)


@pytest.mark.parametrize("turn,sg", [("guide_left", 1.0), ("guide_right", -1.0)])
def test_p9_guidance_arrow_glyph(turn, sg):
    g = arrow_glyph([turn], False)
    assert isinstance(g, Polygon) and g.is_valid
    x0, y0, x1, y1 = g.bounds
    assert 4.5 < x1 - x0 < 6.0 and 2.4 < y1 - y0 < 3.2       # ~5.1 x 2.75 m (orthophoto read, WORKING_VALUE)
    assert g.area > 3.0                                     # a body, not a needle (r3: 0.15 m shaft)
    tip = max(g.exterior.coords, key=lambda c: c[0])
    assert sg * tip[1] > 2.0                                # the head points across, towards the next lane


def _qa(name):
    return json.load(open(REGION / "generated" / name, encoding="utf-8"))


def test_built_region_has_bridge_structure_and_hero_barriers():
    g = _qa("streetscape_qa.json")["furniture"]["guardrails_m"]
    if "structure" not in g:
        pytest.skip("streetscape_qa.json from before ADR 0110 (rebuild the region)")
    assert g["bridge"] > 1000 and g["structure"] > 100


def test_built_region_verge_strips_do_not_make_walls():
    w = _qa("terrain_walls_qa.json")
    by = w["by_source"]
    if not any(k.endswith("verge_grass") for k in by):
        pytest.skip("terrain_walls_qa.json from before ADR 0110 (rebuild the region)")
    # exposed near-vertical verge faces: a handful of slivers at junction corners (b3: 27), never a wall
    assert by.get("skirt:verge_grass", 0) + by.get("skirt:j:verge_grass", 0) <= 40
    assert w["max_m"] <= 0.65
