"""Drive s24 regressions: real road stage, committed tiles, no raw/Unity/world build."""
import copy

import numpy as np
import pytest
import shapely
from shapely.geometry import LineString, box

from roads import markings as MK
from roads.meshing import MeshBuf
from streetscape import furniture as FU


def rectangle(buf, bounds, z=0., src="road", mat="road_asphalt", layer="road"):
    x0, y0, x1, y1 = bounds
    v = np.array([[x0,y0,z], [x1,y0,z], [x1,y1,z], [x0,y1,z]])
    buf.add(layer, mat, v, v[:, :2], [[0,1,2], [0,2,3]], src=src, UV1=v[:, :2])


def rail(points, z=0.):
    return dict(P=np.asarray(points, float), Z=np.full(len(points), z), key="test",
                tall=np.zeros(len(points), bool), term=(True, True), dense=None, dark=None)


@pytest.mark.unit
def test_rail_segment_crosses_road_even_when_endpoints_clear():
    buf = MeshBuf()
    rectangle(buf, (-.1,-2,.1,2))
    q = [rail([[-2,0], [2,0]])]
    FU._clip_rails_to_pavement(q, buf.parts)
    assert not q


@pytest.mark.unit
def test_rail_cut_does_not_reconnect_and_keeps_attributes():
    buf = MeshBuf()
    rectangle(buf, (14,-1,16,1))
    it = rail([[x,0] for x in range(40)])
    it['dense'] = np.ones(40, bool)
    q = [it]
    FU._clip_rails_to_pavement(q, buf.parts)
    assert len(q) == 2
    for r in q:
        assert LineString(r['P']).distance(box(14,-1,16,1)) >= FU.GUARDRAIL_PAVEMENT_CLEAR_M + FU.GUARDRAIL_ENVELOPE_M
        assert len(r['P']) == len(r['Z']) == len(r['tall']) == len(r['dense'])
        assert r['dense'].all()


@pytest.mark.unit
def test_underpass_preserves_deck_rail():
    buf = MeshBuf()
    rectangle(buf, (0,-2,40,2))
    q = [rail([[x,0] for x in range(40)], 6.)]
    FU._clip_rails_to_pavement(q, buf.parts)
    assert len(q) == 1 and len(q[0]['P']) == 40


@pytest.mark.unit
def test_zebras_clip_overlap_and_island_with_uvs():
    buf = MeshBuf()
    rectangle(buf, (-10,-10,10,10))
    rectangle(buf, (0,-1,1,1), .15, 'island:test', 'paving')
    rectangle(buf, (-3,-2,3,2), .015, 'P-10@a', 'marking_white', 'markings')
    rectangle(buf, (-2,-3,2,3), .015, 'P-10J@b', 'marking_white', 'markings')
    rep = MK.clip_zebras(buf)
    assert rep['removed_m2'] > 0
    parts = [p for p in buf.parts if p.layer == 'markings']
    polys = [shapely.union_all(shapely.polygons(p.V[p.T, :2])) for p in parts]
    assert polys[0].intersection(polys[1]).area < 1e-8
    assert all(p.intersection(box(0,-1,1,1).buffer(.049)).area < 1e-8 for p in polys)
    for p in parts:
        assert np.allclose(p.V[:,2], .015)
        assert np.allclose(p.UV, p.V[:,:2]) and np.allclose(p.UV1, p.V[:,:2])


@pytest.mark.unit
def test_zebra_on_different_deck_is_preserved():
    buf = MeshBuf()
    for z in (0., 6.):
        rectangle(buf, (-10,-10,10,10), z)
        rectangle(buf, (-2,-2,2,2), z+.015, f'P-10@{z}', 'marking_white', 'markings')
    rep = MK.clip_zebras(buf)
    assert rep['removed_m2'] == 0


@pytest.fixture(scope='module', params=['bialystok-kleeberga', 'knyszyn-w', 'knyszyn'])
def tile(request):
    # Reuse the established flat-world road-only QA helper; all inputs in Data/Regions.
    from qa.check_piers_vs_roads import flat_world
    w = flat_world(request.param)
    return request.param, w


def test_tile_rails_clear_all_carriageways(tile, monkeypatch):
    rid, w = tile
    buf = MeshBuf(parts=list(w.buf.parts))
    lin = FU.Lin(buf, lambda e,n: np.zeros(len(np.atleast_1d(e))))
    rep = {}
    original = FU._clip_rails_to_pavement
    baseline = []
    def capture(queue, parts, m=None):
        baseline.extend(copy.deepcopy(queue))
        original(queue, parts, m)
    monkeypatch.setattr(FU, '_clip_rails_to_pavement', capture)
    FU.guardrails(lin, w.net, lambda e,n: np.zeros_like(e), rep)
    from roads.surface_safety import SurfaceIndex, carriageway, island
    road, islands = SurfaceIndex(w.buf.parts, carriageway), SurfaceIndex(w.buf.parts, island)
    segments = 0
    for r in lin.rail_runs:
        for k in range(len(r['P'])-1):
            seg = LineString(r['P'][k:k+2])
            lo, hi = min(r['Z'][k:k+2]), max(r['Z'][k:k+2])
            near = seg.buffer(1.)
            asphalt = road.near(near, lo, hi).difference(islands.near(near, lo, hi))
            assert seg.distance(asphalt) >= FU.GUARDRAIL_PAVEMENT_CLEAR_M + FU.GUARDRAIL_ENVELOPE_M - 1e-7, (rid, r['key'])
            segments += 1
    if rid == 'bialystok-kleeberga':
        assert segments > 0
        assert rep['guardrails_m']['pavement_cut_segments'] > 0
    assert len(w.net.guardrail_built) == sum(not np.all(r['tall']) for r in lin.rail_runs)
    print(rid, 'rail segments', segments, 'cut', rep['guardrails_m'].get('pavement_cut_segments'))


def test_tile_zebras_do_not_overlap_or_paint_islands(tile, monkeypatch):
    rid, w = tile
    buf = copy.deepcopy(w.buf)
    rep = {}
    original = MK.clip_zebras
    baseline = []
    def capture(b):
        baseline.extend(copy.deepcopy([p for p in b.parts if p.layer == 'markings' and p.src.startswith(('P-10@', 'P-10J@'))]))
        return original(b)
    monkeypatch.setattr(MK, 'clip_zebras', capture)
    MK.build_markings(buf, w.net, w.junctions, w.ctx['points'], rep)
    parts = [p for p in buf.parts if p.layer == 'markings' and p.src.startswith(('P-10@', 'P-10J@'))]
    assert parts, rid
    from roads.surface_safety import SurfaceIndex, island
    islands = SurfaceIndex(w.buf.parts, island)
    polys = [shapely.union_all(shapely.polygons(p.V[p.T,:2])) for p in parts]
    for i, (p, pg) in enumerate(zip(parts, polys)):
        assert pg.intersection(islands.near(pg, p.V[:,2].min(), p.V[:,2].max())).area < 1e-7
        for j in range(i):
            if abs(p.V[:,2].mean() - parts[j].V[:,2].mean()) < 1.:
                assert pg.intersection(polys[j]).area < 1e-7, (rid, p.src, parts[j].src)
    old = [shapely.union_all(shapely.polygons(p.V[p.T,:2])) for p in baseline]
    overlap = sum(pg.intersection(old[j]).area for i,pg in enumerate(old) for j in range(i)
                  if abs(baseline[i].V[:,2].mean()-baseline[j].V[:,2].mean()) < 1.)
    if rid == 'knyszyn-w':
        assert overlap > 0.01, 'regression must reproduce overlapping zebras before clipping'
    print(rid, 'zebra parts', len(parts), 'baseline overlap m2', round(overlap,4), rep['zebra_safety'])


@pytest.mark.unit
def test_concave_zebra_cut_preserves_area():
    buf = MeshBuf()
    rectangle(buf, (-10,-10,10,10))
    hole = shapely.Polygon([[3.8318707,2.0409971],[0.0040738,3.3153677],[3.3221084,1.3460476],
                           [2.7192745,.5663346],[.6529519,2.8457301],[2.0397089,2.3557024]]).convex_hull
    tris = shapely.get_parts(shapely.constrained_delaunay_triangles(hole))
    for tri in tris:
        xy = np.asarray(tri.exterior.coords)[:3]
        buf.add('road', 'paving', np.column_stack([xy,np.full(3,.15)]), xy, [[0,1,2]], src='island:concave')
    xyz = np.array([[0,0,.015],[5,0,.015],[0,5,.015]])
    buf.add('markings', 'marking_white', xyz, xyz[:,:2], [[0,1,2]], src='P-10@a')
    expected = shapely.Polygon(xyz[:,:2]).difference(hole.buffer(.05)).area
    rep = MK.clip_zebras(buf)
    paint = [p for p in buf.parts if p.layer == 'markings']
    actual = sum(shapely.area(shapely.polygons(p.V[p.T,:2])).sum() for p in paint)
    assert actual == pytest.approx(expected, abs=1e-8)
    assert actual + rep['removed_m2'] == pytest.approx(12.5, abs=1e-4)


@pytest.mark.unit
def test_direct_pier_path_is_clipped(monkeypatch):
    buf = MeshBuf()
    rectangle(buf, (14,-1,16,1))
    lin = FU.Lin(buf, lambda e,n: np.zeros(len(np.atleast_1d(e))))
    drawn = []
    monkeypatch.setattr(FU, 'guardrail', lambda lin,p,*args,**kwargs: drawn.append(p.copy()))
    built = []
    FU._dedup_guardrail(lin, np.array([[x,0.] for x in range(40)]), np.zeros(40), 'pier:structure', built, {})
    assert len(drawn) == len(built) == 2
    assert all(b.distance(box(14,-1,16,1)) > .47 for b in built)


@pytest.mark.unit
def test_three_identical_zebras_and_unchanged_mesh():
    buf = MeshBuf()
    rectangle(buf, (-10,-10,10,10))
    for k in range(3):
        rectangle(buf, (-2,-2,2,2), .015, f'P-10@{k}', 'marking_white', 'markings')
    first = buf.parts[1]
    original_v, original_t = first.V, first.T
    rep = MK.clip_zebras(buf)
    assert rep['removed_m2'] == 32.
    assert len([p for p in buf.parts if p.layer == 'markings']) == 1
    assert first.V is original_v and first.T is original_t


@pytest.mark.unit
def test_flush_checks_after_join_and_bridge_surface(monkeypatch):
    buf = MeshBuf()
    rectangle(buf, (14,-1,16,1), layer='bridge')
    lin = FU.Lin(buf, lambda e,n: np.zeros(len(np.atleast_1d(e))))
    lin.rail_queue = [rail([[x,4.] for x in range(40)])]
    def unsafe_join(queue, m):
        queue[0]['P'][:,1] = 0.
    monkeypatch.setattr(FU, '_join_free_ends', unsafe_join)
    drawn = []
    monkeypatch.setattr(FU, 'guardrail', lambda lin,p,*args,**kwargs: drawn.append(p.copy()))
    FU._flush_rails(lin, {})
    assert len(drawn) == len(lin.rail_runs) == 2
    assert all(LineString(p).distance(box(14,-1,16,1)) > .47 for p in drawn)
