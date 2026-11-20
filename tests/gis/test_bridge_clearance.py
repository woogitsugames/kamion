"""Bridge edges use final carriageways, including the opposite deck (no tile rebuild)."""
import json

import numpy as np
import pytest
import shapely

from roads import meshing as M, network as N, pipeline as P, standards as S
from roads.consistency import CARRIAGEWAY, SurfaceIndex
from roads.geom import Polyline
from streetscape import furniture as F
from streetscape.hero_bridge import _station


def _pair(gap, reverse=True, layer=1):
    sec = N.EdgeSection("w1:a-b", "primary", "G", True, 2, 2, 0, 3., .25, 6.5,
                        "measured", "road_asphalt", True, 1, False, None, None, None)
    from dataclasses import replace
    sections = [sec, replace(sec, edge_id="w2:c-d", layer=layer)]
    chains, nodes = [], {}
    for k, y in enumerate((0., 6.5 + gap)):
        xy = np.column_stack([np.arange(0., 60.01, N.DENSE), np.full(121, y)])
        if k and reverse:
            xy = xy[::-1]
        c = N.Chain(f"c:w{k+1}", f"a{k}", f"b{k}", [], xy, [])
        c.line = Polyline(xy)
        c.hw = np.full(121, 3.25)
        c.sec_idx = np.full(121, k)
        c.dirn = np.ones(121, int)
        c.bridge = np.ones(121, bool)
        c.z, c.e = np.zeros(121), np.zeros(121)
        for side in "LR":
            c.side[side] = {"kind": np.zeros(121, int), "mat": np.zeros(121, int),
                            "raw": {name: np.full(121, val) for name, val in
                                    (("h", .13), ("w", 1.5), ("depth", 1.4))}}
        nodes[c.node_a] = nodes[c.node_b] = {"deg": 1, "boundary": True}
        chains.append(c)
    net = N.Network(nodes, {s.edge_id: s for s in sections}, sections, chains, (0., 0.))
    for c in chains:
        N.structure_sides(c, c.bridge, net)
    return net


def _mesh(net, rails=False):
    buf = M.MeshBuf()
    for c in net.chains:
        M.build_ribbon(buf, net, c)
        M.build_ribbon(buf, net, c, coarse=True)
    if rails:
        F.guardrails(F.Lin(buf, lambda e, n: np.zeros_like(e)), net,
                     lambda e, n: np.zeros_like(e), {})
    return buf


@pytest.mark.parametrize("reverse", [False, True])
@pytest.mark.parametrize("gap", [-.5, 0., .5, 1.5, 3., 8.])
def test_both_decks_keep_raised_edges_outside_carriageways(gap, reverse):
    net = _pair(gap, reverse)
    buf = _mesh(net, rails=True)
    for part in buf.parts:
        if not len(part.T):
            continue
        if part.mat not in {"curb_concrete", "bridge_concrete", "collision_curb", "collision_paving",
                            "barrier_steel", "barrier_post", "collision_steel"}:
            continue
        vertices = part.V[np.unique(part.T)]
        for c in net.chains:
            # Check vertices AND triangle centroids, including vertical faces/posts.
            pts = np.concatenate([vertices, part.V[part.T].mean(1)])
            lat = np.abs(pts[:, 1] - c.line.p[0, 1])
            assert lat.min() >= 3.25 + S.BRIDGE_CLEAR_M - 1e-6, (gap, part.src, part.mat)


def test_other_layer_does_not_shrink_deck_and_hero_uses_same_edges():
    net = _pair(-.5, layer=2)
    for c in net.chains:
        for side in "LR":
            p = N.side_params(c, side, 30.)
            assert p[2] == pytest.approx(M.bridge_cap_w(c))
        st = _station(c, 30.)
        expected = c.hw_at(30.) + S.BRIDGE_CLEAR_M + S.KERB_TOP_W + M.bridge_cap_w(c)
        assert np.linalg.norm(np.array(st['l'][:2]) - st['c'][:2]) == pytest.approx(expected, abs=.002)


def test_reapplying_structure_sides_cannot_restore_cap_across_shared_lane():
    net = _pair(-.5)
    for c in net.chains:
        N.structure_sides(c, c.bridge, net)
        inside = "L"  # the reversed second chain also faces the median on its left
        p = N.side_params(c, inside, 30.)
        assert p[4] == N.MAT_FLUSH_ROAD
        assert {row[4] for row in N.side_profile(*p)} == {"road_asphalt"}


def test_tapered_width_and_cap_transitions_do_not_cross_either_lane():
    net = _pair(3.)
    # A smooth widening towards the other carriageway, then back out. Exercise
    # the raised/flush run boundaries as well as different render/collision steps.
    for c in net.chains:
        c.hw = 3.25 + 1.8 * np.sin(np.pi * c.line.s / c.length) ** 2
        N.structure_sides(c, c.bridge, net)
    buf = _mesh(net, rails=True)
    road = shapely.union_all([shapely.Polygon(tri[:, :2]) for p in buf.parts
                             if p.src in {c.id for c in net.chains} and p.mat == 'road_asphalt'
                             for tri in p.V[p.T]])
    for part in buf.parts:
        if part.mat not in {'curb_concrete', 'bridge_concrete', 'collision_curb',
                            'collision_paving', 'barrier_steel', 'barrier_post', 'collision_steel'}:
            continue
        for tri in part.V[part.T]:
            poly = shapely.Polygon(tri[:, :2])
            if poly.area > 1e-8:
                assert road.intersection(poly).area < 1e-7, (part.src, part.mat, tri)


@pytest.mark.parametrize("rid", ["dk8-wasilkow-01", "dk8-wasilkow-03", "bialystok-porosly", "bialystok-bojary"])
@pytest.mark.parametrize("widen", [0., .25])
def test_reported_bridge_lane_points_from_existing_tile_data(rid, widen, monkeypatch):
    monkeypatch.setattr(S, "GAMEPLAY_LANE_WIDEN_M", widen)
    d = P.REGIONS / rid
    qa = json.loads((d / "generated/road_consistency_qa.json").read_text(encoding="utf-8"))
    cases = [c for c in qa['cases'] if c.get('what') == 'bridge_kerb']
    assert cases
    graph = json.loads((d / 'roads.graph.json').read_text(encoding='utf-8'))
    ways = {str(w) for case in cases for w in case['osm_ways']}
    # Keep the complete reported chains and all elevated neighbours, without
    # terrain, junction meshing, Blender, build_world, or writing generated files.
    r = P.load_region(rid)
    net = N.load(graph, (r['origin']['x'], r['origin']['y']), P.load_overrides(rid))
    N.taper_forks(net, [])
    N.align_forks(net, [])
    N.abreast_forks(net, [])
    net.chains = [c for c in net.chains if c.bridge.any()
                  or any(str(e).split(':')[0].lstrip('w') in ways for e, _ in c.edges)]
    N.assign_sides(net, [], walkways=[])
    for c in net.chains:
        c.z, c.e = np.zeros(len(c.hw)), np.zeros(len(c.hw))
    buf = _mesh(net)
    # Isolate the cap class so a coincident verge/sidewalk cannot win the QA
    # classifier's obstacle priority and conceal a concrete cap intrusion.
    def cap_index(parts):
        return SurfaceIndex([p for p in parts if p.mat in CARRIAGEWAY or p.mat == 'bridge_concrete'])
    idx = cap_index(buf.parts)
    samples = np.array([[case['e'], case['n'], 0.] for case in cases])
    classifications = idx.classify(samples)
    assert not np.any(classifications == 'bridge_kerb'), [(case, str(k)) for case, k in zip(cases, classifications)
                                                         if k == 'bridge_kerb'][:5]
    # Prove the replay includes actual bridge caps, rather than passing on an empty mesh.
    assert any(p.layer == 'bridge' and p.mat == 'bridge_concrete' for p in buf.parts)
    # Replay the old unconditional URBAN cap using the same widths and samples.
    for c in net.chains:
        for side in 'LR':
            c.side[side]['kind'][c.bridge] = N.URBAN
    old = cap_index(_mesh(net).parts).classify(samples)
    old_hits = int(np.sum(old == 'bridge_kerb'))
    assert old_hits > 0, 'regression must reproduce the former cap intrusion'
    print(f'{rid} D94={widen}: saved={len(cases)}, old_caps={old_hits}, new_caps=0')
