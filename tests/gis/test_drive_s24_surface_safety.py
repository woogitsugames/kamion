"""Drive s24 regressions: real road stage, committed tiles, no raw/Unity/world build."""
import copy
from functools import lru_cache
import os
import hashlib
import json
from pathlib import Path

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


@lru_cache(maxsize=3)
def _world(rid):
    # Reuse the established flat-world road-only QA helper; all inputs in Data/Regions.
    from qa.check_piers_vs_roads import flat_world
    nmt_dir = os.environ.get('KAMION_SURFACE_NMT_DIR')
    if not nmt_dir:
        return flat_world(rid)
    from roads import pipeline
    reg = pipeline.load_region(rid)
    meta = json.loads((pipeline.REGIONS/rid/'terrain.json').read_text(encoding='utf-8'))
    data = (Path(nmt_dir)/f'{rid}.r16').read_bytes()
    assert hashlib.sha256(data).hexdigest() == meta['sha256_r16']
    enc = meta['encoding']
    nx, ny = meta['samples']
    z = enc['offset_m'] + np.frombuffer(data,dtype='<u2').reshape(ny,nx).astype(float)*enc['scale_m_per_unit']
    origin = (reg['origin']['x'],reg['origin']['y'])
    return pipeline.build(rid,hf=pipeline.P.Heightfield(z,meta['bbox'],origin))


_PAINT = {}


@pytest.fixture(scope='module', params=['bialystok-kleeberga', 'knyszyn-w', 'knyszyn'])
def tile(request):
    return request.param, _world(request.param)


def test_tile_rails_clear_all_carriageways(tile, monkeypatch):
    rid, w = tile
    buf = MeshBuf(parts=list(w.buf.parts))
    lin = FU.Lin(buf, w.hf.sample)
    rep = {}
    original = FU._clip_rails_to_pavement
    baseline = []
    def capture(queue, parts, m=None):
        baseline.extend(copy.deepcopy(queue))
        original(queue, parts, m)
    monkeypatch.setattr(FU, '_clip_rails_to_pavement', capture)
    FU.guardrails(lin, w.net, w.hf.sample, rep)
    from roads.surface_safety import SurfaceIndex, carriageway, island, own_shoulder
    road, islands = SurfaceIndex(w.buf.parts, carriageway), SurfaceIndex(w.buf.parts, island)
    segments = 0
    for r in lin.rail_runs:
        # c-regress-cli: the flush asphalt shoulder of the side profile a rule run was laid out from is not a lane
        excl = own_shoulder(r['key'])
        for k in range(len(r['P'])-1):
            seg = LineString(r['P'][k:k+2])
            lo, hi = min(r['Z'][k:k+2]), max(r['Z'][k:k+2])
            near = seg.buffer(1.)
            asphalt = road.near(near, lo, hi, exclude=excl).difference(islands.near(near, lo, hi))
            assert asphalt.is_empty or seg.distance(asphalt) >= FU.GUARDRAIL_PAVEMENT_CLEAR_M + FU.GUARDRAIL_ENVELOPE_M - 1e-7, (rid, r['key'])
            segments += 1
    if rid == 'bialystok-kleeberga':
        assert segments > 0
    assert len(w.net.guardrail_built) == sum(not np.all(r['tall']) for r in lin.rail_runs)
    print(rid, 'rail segments', segments, 'cut', rep['guardrails_m'].get('pavement_cut_segments'))
    _plot_rails(rid, w, baseline, lin.rail_runs)


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
    print(rid, 'zebra parts', len(parts), 'baseline overlap m2', round(overlap,4), rep['zebra_safety'])
    _PAINT[rid] = (copy.deepcopy(parts), copy.deepcopy(baseline))
    _plot_zebras(rid, w, old, polys)
    if rid == 'knyszyn':
        _plot(rid, w, old, polys, (-1010., -610.), 'zebra-west-arm')


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


def _plot(rid, w, before, after, center, label):
    out = os.environ.get('KAMION_SURFACE_QA_DIR')
    if not out:
        return
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.collections import PolyCollection
    fig, axes = plt.subplots(1,2,figsize=(12,5))
    for ax, data, title in zip(axes, (before,after), ('przed', 'po')):
        for part in w.buf.parts:
            if part.layer in ('road','bridge'):
                color = '#777777' if part.mat.startswith('road_') else '#c9c5aa'
                tris = part.V[part.T,:2]
                visible = ((tris[:,:,0].min(1) < center[0]+25) & (tris[:,:,0].max(1) > center[0]-25)
                           & (tris[:,:,1].min(1) < center[1]+25) & (tris[:,:,1].max(1) > center[1]-25))
                ax.add_collection(PolyCollection(tris[visible], facecolor=color, edgecolor='none'))
        for shape in data:
            for pg in shapely.get_parts(shape):
                if pg.geom_type == 'Polygon':
                    ax.fill(*pg.exterior.xy, color='white', edgecolor='#b00020', linewidth=.2)
                elif pg.geom_type == 'LineString':
                    ax.plot(*pg.xy, color='#b00020', linewidth=2)
        ax.set(xlim=(center[0]-25,center[0]+25),ylim=(center[1]-25,center[1]+25),title=title,aspect='equal')
        ax.set_xlabel('E [m]'); ax.set_ylabel('N [m]')
    model = 'NMT' if os.environ.get('KAMION_SURFACE_NMT_DIR') else 'plaski model terenu'
    fig.suptitle(f'{rid}: {label}; {model}')
    Path(out).mkdir(parents=True,exist_ok=True)
    fig.savefig(Path(out)/f'{rid}-{label}.png',dpi=80)
    plt.close(fig)


def _plot_rails(rid,w,baseline,after):
    old = [LineString(r['P']) for r in baseline]
    new = [LineString(r['P']) for r in after]
    diff = shapely.union_all(old).difference(shapely.union_all(new).buffer(.01))
    if not diff.is_empty:
        longest = max(shapely.get_parts(diff),key=lambda p:p.length)
        center = longest.interpolate(.5,normalized=True).coords[0]
        print(rid,'rail cut focus EN',center)
        _plot(rid,w,old,new,center,'guardrail')


def _plot_zebras(rid,w,old,new):
    overlaps = [a.intersection(b) for i,a in enumerate(old) for b in old[:i] if a.intersection(b).area > .01]
    if overlaps:
        overlap = max(overlaps,key=lambda p:p.area)
        center = overlap.centroid.coords[0]
        print(rid,'zebra overlap focus EN',center)
        _plot(rid,w,old,new,center,'zebra')


def test_neighbor_tile_zebras_do_not_overlap():
    from shapely.affinity import translate
    worlds = [_world(rid) for rid in ('knyszyn', 'knyszyn-w')]
    global_shapes = []
    for w in worlds:
        rid = w.region['id']
        if rid not in _PAINT:
            buf = copy.deepcopy(w.buf)
            MK.build_markings(buf,w.net,w.junctions,w.ctx['points'],{})
            parts = [p for p in buf.parts if p.layer == 'markings' and p.src.startswith(('P-10@','P-10J@'))]
        else:
            parts = _PAINT[rid][0]
        shapes = [translate(shapely.union_all(shapely.polygons(p.V[p.T,:2])),*w.origin) for p in parts]
        global_shapes.append(shapely.union_all(shapes))
    overlap = global_shapes[0].intersection(global_shapes[1]).area
    print('knyszyn / knyszyn-w seam overlap m2', overlap)
    assert overlap < 1e-7


def test_compact_zebra_paint_above_carriageway():
    w = _world('knyszyn')
    if 'knyszyn' not in _PAINT:
        buf = copy.deepcopy(w.buf)
        MK.build_markings(buf,w.net,w.junctions,w.ctx['points'],{})
        parts = buf.parts
    else:
        parts = _PAINT['knyszyn'][0]
    from roads.surface_safety import SurfaceIndex, carriageway
    road = SurfaceIndex(w.buf.parts,carriageway)
    worst = 0.
    bad = 0
    for p in parts:
        if not p.src.startswith('P-10@cr:'):
            continue
        for xyz in p.V[p.T]:
            pg = shapely.Polygon(xyz[:,:2])
            for k in road.tree.query(pg,predicate='intersects'):
                r = road.xyz[k]
                if abs(r[:,2].mean()-xyz[:,2].mean()) > 1.:
                    continue
                hit = pg.intersection(road.polys[k])
                if hit.area < 1e-10:
                    continue
                xy = shapely.get_coordinates(hit)
                def plane(t):
                    basis = np.vstack([t[:,:2].T,np.ones(3)])
                    weights = np.linalg.solve(basis,np.vstack([xy.T,np.ones(len(xy))])).T
                    return weights@t[:,2]
                under = float((plane(r)-plane(xyz)).max())
                worst = max(worst,under)
                bad += int(under > 1e-5)
    print('knyszyn compact zebra below road: triangles',bad,'max m',worst)
    assert worst < 1e-5
