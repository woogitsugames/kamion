"""ADR 0183: red-white blocking posts with chains (streetscape.chain_bollards) and the override `kind: chain_bollards`.

Light tests (no region build, no raw data).
Run: uv run --project tools/worldgen pytest tests/gis/test_chain_bollards_0183.py -q
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools" / "worldgen"))

from streetscape import chain_bollards as CB  # noqa: E402
from streetscape import export as EX  # noqa: E402
from streetscape import materials as MT  # noqa: E402
from streetscape import props as PP  # noqa: E402


class _Placer:
    """Placer stand-in: ground rising 5 % toward the east."""

    def __init__(self):
        self.items = []

    def add(self, proto, p, yaw, z=None, sz=1.0, src="", group=None):
        z = 0.05 * float(p[0])
        self.items.append({"p": proto, "e": float(p[0]), "n": float(p[1]), "z": z, "yaw": float(yaw), "src": src})
        return z


def _tris(mesh):
    return sum(len(p["T"]) for p in mesh.out())


def _V(mesh):
    return np.concatenate([p["V"] for p in mesh.out()])


# ---------------------------------------------------------------------------------------------- prototypes
def test_library_has_both_prototypes_with_one_material():
    P = PP.build_all(set(), {})
    for name in (CB.PROTO_BAY, CB.PROTO_POST):
        lod0, lod1, col = P[name]
        assert {p["mat"] for p in lod0.out()} == {CB.MAT}          # one material = one instanced draw per LOD
        assert {p["mat"] for p in lod1.out()} == {CB.MAT}
        assert col is not None
    assert CB.PROTO_BAY.startswith("bollard") and CB.PROTO_POST.startswith("bollard")   # seated like every bollard


def test_triangle_budget():
    bay0, bay1, _ = CB.bay()
    post0, post1, _ = CB.post()
    assert _tris(bay0) <= 160 and _tris(bay1) <= 40
    assert _tris(post0) <= 80 and _tris(post1) <= 16
    assert _tris(bay1) < _tris(bay0) / 4


def test_post_dimensions():
    V = _V(CB.post()[1])                                            # LOD1: the bare tube
    r = np.hypot(V[:, 0], V[:, 1]).max()
    assert r == pytest.approx(CB.POST_D_M / 2, abs=1e-9)
    assert 0.06 <= CB.POST_D_M <= 0.11                              # task range for the tube
    assert 0.6 <= CB.POST_H_M <= 0.8                                # U-12c (research row M50-043)
    assert CB.BAY_M == pytest.approx(2.0 * CB.POST_H_M)             # P11-063: bay = 2.0 post heights
    assert V[:, 2].max() == pytest.approx(CB.POST_H_M + CB.CAP_RISE_M)
    assert V[:, 2].min() < 0                                        # buried foot: no gap on uneven paving
    assert [b[2] for b in CB.BANDS] == [False, True, False, True, False]      # white at the ground and at the top
    assert CB.BANDS[0][0] == 0.0 and CB.BANDS[-1][1] == pytest.approx(CB.POST_H_M)
    assert all(a[1] == pytest.approx(b[0]) for a, b in zip(CB.BANDS[:-1], CB.BANDS[1:]))


def test_catenary_sags_between_level_supports():
    x, dz, slope, s = CB.catenary(1.9, 0.18, 8)
    assert dz[0] == pytest.approx(0.0, abs=1e-6) and dz[-1] == pytest.approx(0.0, abs=1e-6)
    assert dz.min() == pytest.approx(-0.18, abs=1e-6) and np.argmin(dz) == 4
    assert slope[0] < 0 < slope[-1] and s[0] == pytest.approx(-s[-1])
    assert 2 * s[-1] > 1.9                                          # the chain is longer than the span


@pytest.mark.parametrize("lod", [0, 1])
def test_chains_hang_from_the_eyelets_and_reach_the_next_post(lod):
    bay = CB.bay()[lod]
    V = _V(bay)
    chain = V[V[:, 0] > CB.POST_D_M]                                # everything beyond the post = the two chains
    assert chain[:, 0].max() == pytest.approx(CB.BAY_M - CB.POST_D_M / 2 - CB.EYELET_M[0] + 0.002, abs=0.02)
    assert chain[:, 2].max() == pytest.approx(CB.CHAIN_Z_M[0], abs=0.02)
    lowest = CB.CHAIN_Z_M[1] - CB.CHAIN_SAG_M[1]
    assert chain[:, 2].min() == pytest.approx(lowest, abs=0.02) and lowest > 0.20      # clear of the ground
    mid = chain[np.abs(chain[:, 0] - CB.BAY_M / 2) < 0.02]
    assert mid[:, 2].max() == pytest.approx(CB.CHAIN_Z_M[0] - CB.CHAIN_SAG_M[0], abs=0.02)


def test_chain_uv_stays_inside_its_atlas_column():
    for lod, cols in ((0, CB.U_LINK), (1, CB.U_STRIP)):
        p = CB.bay()[lod].out()[0]
        sel = p["V"][:, 0] > CB.POST_D_M
        u = p["UV"][sel, 0]
        assert u.min() >= min(c[0] for c in cols.values()) and u.max() <= max(c[1] for c in cols.values())
        for red in (True, False):                                   # both paints are used along a bay
            assert np.any((u > cols[red][0]) & (u < cols[red][1]))
    post = CB.post()[0].out()[0]
    assert post["UV"][:, 0].max() <= CB.U_STEEL + 1e-9


# ---------------------------------------------------------------------------------------------- texture / material
def test_atlas_regions():
    im = np.asarray(CB.texture())
    assert im.shape == (CB.ATLAS[1], CB.ATLAS[0], 4)
    h = im.shape[0]
    row = lambda z: int((1 - z / CB.POST_H_M) * h)                  # noqa: E731
    for z0, z1, red in CB.BANDS:
        px = im[row((z0 + z1) / 2), 10:100, :3].astype(float).mean(0)
        assert (px[0] > 1.8 * px[1]) == red                         # red band: R dominates; white: neutral
    assert im[:, :128, 3].min() == 255                              # post + steel are opaque
    for red in (True, False):
        c0 = int(round(CB.U_LINK[red][0] * CB.ATLAS[0]))
        a = im[:, c0:c0 + 32, 3] / 255.0
        assert 0.25 < a.mean() < 0.6 and a.min() == 0 and a.max() == 1     # links with holes
        s0 = int(round(CB.U_STRIP[red][0] * CB.ATLAS[0]))
        assert im[:, s0:s0 + 28, 3].min() == 255                    # LOD1 strip never clips away
    assert np.array_equal(im, np.asarray(CB.texture()))             # deterministic


def test_material_and_export_wiring():
    m = MT.M[CB.MAT]
    assert m["texture"] == CB.MAT and m["alpha_cutoff"] == 0.5
    assert CB.MAT in EX.textures()
    assert EX.glb_materials()[CB.MAT]["texture_png"][:4] == b"\x89PNG"


# ---------------------------------------------------------------------------------------------- rows
def test_walk_keeps_every_bay_at_bay_length_on_the_line():
    from shapely.geometry import LineString, Point
    P = [[0, 0], [7.3, 0], [9.0, 4.0], [9.0, 11.3]]
    Q = CB.walk(P)
    d = np.hypot(*np.diff(Q, axis=0).T)
    assert np.allclose(d, CB.BAY_M)
    line = LineString(P)
    assert all(line.distance(Point(q)) < 1e-6 for q in Q[:-1])
    assert np.hypot(*(Q[-1] - np.array(P[-1]))) < CB.BAY_M / 2 + 1e-9      # the end is off by less than half a bay
    assert np.allclose(Q[0], P[0])


@pytest.mark.parametrize("bays,posts", [(0.2, 2), (1.0, 2), (1.45, 2), (1.55, 3), (7.0, 8)])
def test_walk_rounds_the_row_to_whole_bays(bays, posts):
    assert len(CB.walk([[0, 0], [bays * CB.BAY_M, 0]])) == posts


def test_apply_places_bays_and_a_closing_post():
    o = {"id": "row", "kind": "chain_bollards", "line_epsg2180": [[100.0, 200.0], [100.0, 200.0 + 3 * CB.BAY_M]]}
    pl, rep = _Placer(), {}
    CB.apply(pl, [o, {"id": "x", "kind": "depot_yard"}], (100.0, 200.0), rep)
    assert [i["p"] for i in pl.items] == [CB.PROTO_BAY] * 3 + [CB.PROTO_POST]
    assert np.allclose([(i["e"], i["n"]) for i in pl.items], [(0.0, k * CB.BAY_M) for k in range(4)])
    assert all(i["yaw"] == pytest.approx(math.pi / 2) for i in pl.items)   # local +x (the chain) points north
    assert pl.items[0]["src"] == "override:row:0:0"
    assert rep["chain_bollards"]["applied"] == [
        {"id": "row", "line": 0, "posts": 4, "bays": 3, "length_m": round(3 * CB.BAY_M, 2), "end_shift_m": 0.0, "max_step_m": 0.0}]


def test_apply_lines_posts_only_step_and_stale():
    B = CB.BAY_M
    ov = [{"id": "two", "kind": "chain_bollards", "chain": False,
           "lines": [{"line_epsg2180": [[0, 0], [2 * B, 0]]}, {"line_epsg2180": [[0, 5], [1.5 * B, 5]]}]},
          {"id": "bad", "kind": "chain_bollards", "line_epsg2180": [[1.0, 1.0]]},
          {"id": "none", "kind": "chain_bollards"}]
    pl, rep = _Placer(), {}
    CB.apply(pl, ov, (0.0, 0.0), rep)
    assert {i["p"] for i in pl.items} == {CB.PROTO_POST} and len(pl.items) == 3 + 3
    r = rep["chain_bollards"]
    assert [a["bays"] for a in r["applied"]] == [0, 0]
    assert r["applied"][0]["max_step_m"] == pytest.approx(0.05 * B)  # 5 % ground x one bay
    assert r["applied"][1]["end_shift_m"] == pytest.approx(0.5 * B)   # 1.5 bays of line -> 2 bays, half a bay past the end
    assert len(r["stale"]) == 2 and r["stale"][0].startswith("bad:0") and r["stale"][1].startswith("none")


def test_no_override_no_report():
    rep = {}
    CB.apply(_Placer(), [{"id": "x", "kind": "depot_yard"}], (0.0, 0.0), rep)
    assert rep == {}
