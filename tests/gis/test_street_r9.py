"""ADR 0069: road furniture after Mapillary references (noise-barrier styles, cantilever gantry, board rows from OSM
destination tags, curved signal mast arms, roadside tree groups). Unit tests (no world build) + checks on the
generated QA when present."""
from __future__ import annotations

import json

import numpy as np
import pytest
import shapely

from conftest import REGION_DIR


def test_noise_wall_tags():
    from streetscape.furniture import is_noise_wall
    assert is_noise_wall({"barrier": "wall", "wall": "noise_barrier"})
    assert is_noise_wall({"barrier": "noise_barrier"})
    assert not is_noise_wall({"barrier": "wall"})            # plot wall stays a concrete panel fence
    assert not is_noise_wall({"barrier": "fence"})


def test_noise_runs_split_by_zone_without_gaps():
    from streetscape import furniture as FU
    P = np.column_stack([np.arange(0, 41, 2.0), np.zeros(21)])
    glazed = dict(FU.NOISE_STYLES["glazed"], name="glazed")
    solid = dict(FU.NOISE_STYLES["solid"], name="solid")
    runs = FU._noise_runs(P, [(np.array([30.0, 0.0]), 6.0, glazed, "z")], solid)
    names = [st["name"] for _, st in runs]
    assert names == ["solid", "glazed", "solid"]
    # consecutive runs share one vertex (no gap at the joint) and cover the whole line
    assert runs[0][0].start == 0 and runs[-1][0].stop == len(P)
    for (a, _), (b, _) in zip(runs, runs[1:]):
        assert a.stop - 1 == b.start


def test_board_rows_from_osm_destination_tags():
    from streetscape.landmarks import _board_rows
    graph = {"edges": [
        {"osm_way": 1, "attrs": {"destination": {"v": "Warszawa;Ełk"}, "destination:ref": {"v": "65"}}},
        {"osm_way": 2, "attrs": {"destination": {"v": "Augustów;Kuźnica PL/BY"}, "destination:ref": {"v": "19"}}},
        {"osm_way": 3, "attrs": {"destination": {"v": "Centrum"}}},
        {"osm_way": 4, "attrs": {"destination": {"v": "Lublin;Bobrowniki PL/BY"}, "destination:ref": {"v": "19;65"}}},
    ]}
    rep = {"stale": []}
    rows = _board_rows(graph, {"from_osm": [{"way": 1, "refs_extra": ["8", "E67"]}, {"way": 2}, {"way": 3},
                                            {"way": 4}, {"way": 99}]}, rep, "x")
    # fewer refs than names: the ref belongs to the last name (Mapillary p37: "65 Ełk", "19 Kuźnica")
    assert rows == [(["8", "E67"], "Warszawa"), (["65"], "Ełk"), ([], "Augustów"), (["19"], "Kuźnica PL/BY"),
                    ([], "Centrum"), (["19"], "Lublin"), (["65"], "Bobrowniki PL/BY")]
    assert rep["stale"] == ["x:way99"]
    assert _board_rows(graph, {"rows": [[["E67"], "Warszawa"]]}, rep, "x") == [(["E67"], "Warszawa")]


def test_cantilever_prototype_reach_and_mirror():
    from streetscape import life_props as LP
    for mirror in (False, True):
        m, l1, col = LP.sign_cantilever(9.0, 7.4, mirror=mirror)
        V = np.concatenate([p["V"] for p in m.out()])
        assert col is None                                  # collider comes with gantry_footing
        assert V[:, 2].max() == pytest.approx(7.4 + 0.3 + 0.05, abs=0.06)
        if mirror:
            assert V[:, 0].min() == pytest.approx(-9.0, abs=0.07) and V[:, 0].max() < 0.4
        else:
            assert V[:, 0].max() == pytest.approx(9.0, abs=0.07) and V[:, 0].min() > -0.4
        n0 = sum(len(p["T"]) for p in m.out())
        n1 = sum(len(p["T"]) for p in l1.out())
        assert n1 <= 24 and n0 < 2500                          # LOD1 = two boxes; LOD0 lattice budget


def test_signal_mast_curved_arm():
    from roads import standards as S
    from streetscape.props import signal_pole
    m, l1, col = signal_pole(S.SIGNAL_MAST_H, 6.0)
    V = np.concatenate([p["V"] for p in m.out()])
    za = S.SIGNAL_MAST_H - 0.4
    assert V[:, 1].max() == pytest.approx(6.0, abs=0.06)
    assert V[:, 2].max() == pytest.approx(za + 0.11, abs=0.05)       # no vertical stub above the bend
    # the bend: points between the pole and the straight arm lie on the quarter circle
    bend = V[(V[:, 1] > 0.2) & (V[:, 1] < S.SIGNAL_MAST_BEND_R - 0.2)]
    assert len(bend) and (bend[:, 2] < za + 0.12).all() and (bend[:, 2] > za - S.SIGNAL_MAST_BEND_R - 0.15).all()
    assert S.SIGNAL_CANTILEVER_LANES == 2


def test_tree_groups_are_clumps_not_a_row():
    from streetscape.vegetation import TREE_GROUP_DEFAULTS, group_positions
    line = shapely.LineString([(0, 0), (400, 0)])
    P, G = group_positions(line, np.random.default_rng(1), TREE_GROUP_DEFAULTS)
    assert len(P) > 10 and G.max() >= 5
    xs = P[:, 0]
    d = np.diff(xs)
    same = G[1:] == G[:-1]
    assert d[same].max() <= TREE_GROUP_DEFAULTS["in_group_m"][1] + 1e-6
    assert d[~same].min() >= TREE_GROUP_DEFAULTS["gap_m"][0] - 1e-6        # open verge between clumps
    sizes = np.bincount(G)
    assert sizes[:-1].min() >= TREE_GROUP_DEFAULTS["group_size"][0]       # last clump may be cut by the line end
    assert sizes.max() <= TREE_GROUP_DEFAULTS["group_size"][1]
    assert np.abs(P[:, 1]).max() <= TREE_GROUP_DEFAULTS["depth_m"] / 2 + 1e-6


def test_generated_qa_street_r9():
    """After build_world: noise barriers from OSM + BDOT with the authored glazed zones in use, the two Mapillary
    gantries placed, no stale ADR 0069 overrides."""
    p = REGION_DIR / "generated" / "streetscape_qa.json"
    q = json.loads(p.read_text(encoding="utf-8"))
    nb = q["furniture"].get("noise_barriers")
    if nb is None:
        pytest.skip("streetscape_qa.json predates ADR 0069 (run build_world)")
    assert nb["m_by_style"].get("glazed", 0) > 80 and nb["m_by_style"].get("solid", 0) > 500
    assert nb["zones_stale"] == []
    g = {x["id"]: x for x in q["furniture"]["landmarks"]["gantries"]}
    assert g["andersa-putry-cantilever-p37"]["form"] == "cantilever"
    assert g["andersa-putry-portal-p40"]["form"] == "portal"
    rows = [r for b in g["andersa-putry-cantilever-p37"]["boards"] for r in b["rows"]]
    assert [r[1] for r in rows][:2] == ["Warszawa", "Ełk"]
    assert not [s for s in q["furniture"]["landmarks"]["stale"] if "p37" in s or "p40" in s]
    vg = q.get("vegetation", {}).get("tree_groups", {})
    assert vg.get("trees", 0) >= 6, vg              # p26 clumps land on the grass beyond the cycle path (r9c)


def test_zebras_inside_junction_patches():
    """REFS-MAPILLARY #5 (p40 / p42): zebras at signalised mouths were skipped because the OSM crossing node lies
    inside the generated junction patch; r9c drapes them on the patch mesh."""
    p = REGION_DIR / "generated" / "roads_qa.json"
    q = json.loads(p.read_text(encoding="utf-8"))["summary"]
    if "P-10 crossing in junction" not in q["markings"]:
        pytest.skip("roads_qa.json predates r9c (run build_world)")
    assert q["markings"]["P-10 crossing in junction"] >= 8
    assert {2882674819, 2882674820}.isdisjoint(q.get("crossings_skipped", []))
    assert len(q.get("crossings_skipped", [])) <= 6
