"""Fab optional placement must preserve public-clone fallback and physical rules."""
import copy
import json
from types import SimpleNamespace

import numpy as np
from shapely.geometry import Polygon, box

from roads.geom import Polyline
from roads.meshing import MeshBuf
from roads.network import Chain, edge_section, URBAN
from streetscape import fab_details as F
from streetscape.furniture import Placer


def network(length=240, bridge=False):
    sec = edge_section({"id": "e", "attrs": {"highway": {"v": "residential"}}})
    line = Polyline(np.column_stack([np.arange(0, length + 0.1, .5), np.zeros(int(length * 2) + 1)]))
    n = len(line.s)
    c = Chain("test", "a", "b", [], line.p, [])
    c.line = line
    c.hw = np.full(n, sec.width / 2)
    c.dirn = np.zeros(n)
    c.z = np.full(n, 10.)
    c.e = np.full(n, np.nan)
    c.bridge = np.full(n, bridge)
    c.sec_idx = np.zeros(n, int)
    c.side = {s: {"kind": np.full(n, URBAN), "h": np.full(n, .13), "w": np.full(n, 2.),
                  "depth": np.zeros(n), "mat": np.zeros(n, int)} for s in ("L", "R")}
    return SimpleNamespace(chains=[c], sec_list=[sec])


def test_missing_manifest_is_optional(tmp_path):
    assert F.load_ready(tmp_path / 'absent', tmp_path) == {}
    p = tmp_path / 'bad.json'
    p.write_text('{bad', encoding='utf-8')
    assert F.load_ready(p, tmp_path) == {}


def test_manifest_rejects_unreviewed_missing_or_unsafe_output(tmp_path):
    out = tmp_path / 'art-source/world/megascans/_generated'
    out.mkdir(parents=True)
    (out / 'color.png').write_bytes(b'test')
    color = 'art-source/world/megascans/_generated/color.png'
    item = {"status": "ready", "source_sha256": "a" * 64, "textures": {"Low": {"basecolor": color}}}
    p = out / 'manifest.json'
    p.write_text(json.dumps({"schema": 1, "items": {"ok": item,
        "unreviewed": {**item, "status": "pending-review"},
        "missing": {**item, "textures": {"Low": {"basecolor": color + 'missing'}}},
        "unsafe": {**item, "textures": {"Low": {"basecolor": str(p)}}},
        "no-lod2": {**item, "models": [{"lods": [{"lod": 0, "path": color}]}]}}}), encoding='utf-8')
    # The manifest is inside the safe dir too; use external file for unsafe case.
    data = json.loads(p.read_text())
    data['items']['unsafe']['textures']['Low']['basecolor'] = '../escape.png'
    p.write_text(json.dumps(data))
    review = {aid: {"status": "approved", "source_sha256": "a" * 64} for aid in data['items']}
    sources = {aid: {"sha256": "a" * 64} for aid in data['items']}
    assert set(F.load_ready(p, tmp_path, review=review, sources=sources)) == {'ok'}


def test_fallback_leaves_buffers_and_instances_unchanged(monkeypatch):
    monkeypatch.setattr(F, 'load_ready', lambda: {})
    buf = MeshBuf()
    pl = SimpleNamespace(items=[{'p': 'waste_bin', 'e': 0, 'n': 0, 'z': 0}])
    before = copy.deepcopy(pl.items)
    report, logs = {}, []
    F.apply(SimpleNamespace(buf=buf), pl, Polygon(), Polygon(), [], [], None, report,
            lambda *v: logs.append(v))
    assert pl.items == before and not buf.parts
    assert report['megascans']['fallback'] is True
    assert 'retaining existing' in str(logs)


def test_manhole_is_lane_centred_draped_deterministic_and_skips_bridges():
    net = network()
    b1, b2 = MeshBuf(), MeshBuf()
    assets = {'round-manhole-cover': {}}
    r1, r2 = {}, {}
    F.drainage(b1, net, assets, r1)
    F.drainage(b2, net, assets, r2)
    assert r1 == r2 and r1['manholes'] >= 2
    c = net.chains[0]
    for p, q in zip(b1.parts, b2.parts):
        assert np.array_equal(p.V, q.V)
        lat = np.mean(p.V[:, 1])
        assert abs(abs(lat) - net.sec_list[0].lane_w / 2) < .001
        assert np.allclose(p.V[:, 2], c.crossfall_z(p.V[:, 0], p.V[:, 1]) + F.COVER_LIFT)
        assert np.all(np.cross(p.V[p.T][:, 1] - p.V[p.T][:, 0], p.V[p.T][:, 2] - p.V[p.T][:, 0])[:, 2] > 0)
    blocked = MeshBuf()
    F.drainage(blocked, network(bridge=True), assets, {})
    assert not blocked.parts
    from roads.decals import LIFT_PATCH, LIFT_OIL
    from roads.standards import MARKING_LIFT
    assert LIFT_PATCH < LIFT_OIL < F.COVER_LIFT < MARKING_LIFT


def test_gullies_replace_material_without_duplicate_geometry():
    from roads.decals import gullies
    b = MeshBuf()
    net = network()
    gullies(b, net, {})
    before = [(p.V.copy(), p.T.copy()) for p in b.parts]
    report = {}
    F.drainage(b, net, {'square-rusty-drain': {}}, report)
    assert len(b.parts) == len(before) > 0
    assert report['gully_replacements'] == len(before)
    assert all(p.mat == 'fab_square_rusty_drain' for p in b.parts)
    assert all(np.array_equal(p.V, v) and np.array_equal(p.T, t) for p, (v, t) in zip(b.parts, before))
    centres = sorted(np.mean(p.V[:, 0]) for p in b.parts if np.mean(p.V[:, 1]) > 0)
    assert np.allclose(np.diff(centres), 35.)


def test_prop_support_rejects_steep_or_nonfinite_surface():
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    pl = Placer(flat, flat)
    assert F._ground_height(pl, np.zeros(2), .4) == 0.
    pl.zsurf = lambda e, n: e
    assert F._ground_height(pl, np.zeros(2), .4) is None
    pl.zsurf = lambda e, n: np.full_like(e, np.nan)
    assert F._ground_height(pl, np.zeros(2), .4) is None


def test_natural_props_do_not_enter_road_building_or_paving(monkeypatch):
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    pl = Placer(flat, flat)
    net = network(500)
    assets = {a: {'models': [{'lods': []}]} for a in F.GROUND_IDS}
    road = box(-10, -net.sec_list[0].width / 2, 510, net.sec_list[0].width / 2)
    building = box(100, 5, 200, 15)
    paved = [{'poly': box(250, -20, 350, -5)}]
    report = {}
    monkeypatch.setattr(F, 'MAX_PROPS', 5)
    F.props(pl, net, assets, road, building, paved, [], None, report)
    assert 0 < len(pl.items) <= 5
    for it in pl.items:
        assert not road.buffer(.15).intersects(box(it['e']-.35, it['n']-.35, it['e']+.35, it['n']+.35))
        assert not building.contains(__import__('shapely').geometry.Point(it['e'], it['n']))
        assert it['z'] == 0.


def test_authored_islands_respect_boundaries_decks_and_cap(monkeypatch):
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    assets = {'boxwood': {'models': [{'lods': []}]}}
    net = SimpleNamespace(chains=[])
    island = box(0, 0, 50, 50)
    roads = box(-5, -5, 55, 55).difference(island)
    pl, rep = Placer(flat, flat), {}
    F.props(pl, net, assets, roads, Polygon(), [], [], None, rep,
            islands=[{'id': 'test', 'poly': island, 'assets': ['boxwood']}],
            deck_at=lambda e, n: e > 25)
    assert 0 < len(pl.items) <= 12
    for it in pl.items:
        p = __import__('shapely').geometry.Point(it['e'], it['n'])
        assert island.covers(p.buffer(.65))
        assert not roads.intersects(p.buffer(.65))
        assert it['e'] <= 25


def test_fab_lod_policy_matches_importer():
    from roads.build_world import instance_ends
    assert instance_ends('fab_boxwood', 3) == ([12., 30., 65.], False)
    assert instance_ends('fab_boxwood', 2) == ([12., 65.], False)


def test_fab_materials_use_asset_keys_and_decal_metadata():
    mats = F.materials({'metal-manhole-cover': {}, 'boxwood': {}})
    assert mats['fab_metal_manhole_cover']['fab_asset'] == 'metal-manhole-cover'
    assert mats['fab_metal_manhole_cover']['decal'] is True
    assert 'decal' not in mats['fab_boxwood']



def test_prototype_stats_read_actual_first_variant_counts():
    a = {'boxwood': {'models': [{'lods': [
        {'lod': 0, 'triangles': 997}, {'lod': 1, 'triangles': 301}, {'lod': 2, 'triangles': 95}]}]}}
    assert F.prototype_stats(a) == {'fab_boxwood': {'tris_lod0': 997, 'tris_lod1': 301, 'tris_lod2': 95}}
    assert F.prototype_stats({'unprepared': {}}) == {}


def test_disable_switch_avoids_local_assets(monkeypatch, tmp_path):
    monkeypatch.setenv('KAMION_DISABLE_FAB', '1')
    assert F.load_ready(tmp_path / 'manifest.json') == {}



def test_stale_ready_outputs_require_current_approval_and_matching_pins(tmp_path):
    out = tmp_path / 'art-source/world/megascans/_generated'
    out.mkdir(parents=True)
    (out / 'color.png').write_bytes(b'test')
    color = 'art-source/world/megascans/_generated/color.png'
    item = {'status': 'ready', 'source_sha256': 'a' * 64,
            'textures': {'Low': {'basecolor': color}}}
    p = out / 'manifest.json'
    p.write_text(json.dumps({'schema': 1, 'items': {'asset': item}}))
    review = {'asset': {'status': 'approved', 'source_sha256': 'a' * 64}}
    sources = {'asset': {'sha256': 'a' * 64}}
    assert set(F.load_ready(p, tmp_path, review=review, sources=sources)) == {'asset'}
    # No ZIP is required by the consuming loader; only pinned prepared output.
    review['asset']['status'] = 'rejected'
    assert F.load_ready(p, tmp_path, review=review, sources=sources) == {}
    review['asset']['status'] = 'approved'
    review['asset']['source_sha256'] = 'b' * 64
    assert F.load_ready(p, tmp_path, review=review, sources=sources) == {}
    review['asset']['source_sha256'] = 'a' * 64
    sources['asset']['sha256'] = 'c' * 64
    assert F.load_ready(p, tmp_path, review=review, sources=sources) == {}
    assert F.load_ready(p, tmp_path, review=review, sources={}) == {}


def test_production_loader_rereads_review_without_output_rebuild(tmp_path):
    out = tmp_path / 'art-source/world/megascans/_generated'
    out.mkdir(parents=True)
    (out / 'color.png').write_bytes(b'test')
    p = out / 'manifest.json'
    p.write_text(json.dumps({'schema': 1, 'items': {'asset': {
        'status': 'ready', 'source_sha256': 'a' * 64,
        'textures': {'Low': {'basecolor': 'art-source/world/megascans/_generated/color.png'}}}}}))
    review_path = tmp_path / 'tools/worldgen/fab/review.json'
    review_path.parent.mkdir(parents=True)
    source_path = tmp_path / 'Data/SourceManifests/fab-megascans-2026-11-10.json'
    source_path.parent.mkdir(parents=True)
    source_path.write_text(json.dumps({'items': [{'id': 'asset', 'sha256': 'a' * 64}]}))
    review = {'schema': 1, 'items': {'asset': {'status': 'approved', 'source_sha256': 'a' * 64}}}
    review_path.write_text(json.dumps(review))
    assert set(F.load_ready(p, tmp_path)) == {'asset'}
    review['items']['asset']['status'] = 'pending-review'
    review_path.write_text(json.dumps(review))
    assert F.load_ready(p, tmp_path) == {}


def test_drainage_atlas_requires_pins_paths_and_matching_tier_rects(tmp_path):
    out = tmp_path / 'art-source/world/megascans/_generated'
    out.mkdir(parents=True)
    color = 'art-source/world/megascans/_generated/atlas.png'
    (out / 'atlas.png').write_bytes(b'test')
    atlas = {'sources': [{'id': 'square-rusty-drain', 'sha256': 'a'*64}],
             'uv_rects': {'square-rusty-drain': [.02, .02, .48, .48]},
             'textures': {tier: {'basecolor': color} for tier in ('Low', 'High')}}
    p = out / 'drainage_atlas_manifest.json'
    p.write_text(json.dumps({'schema': 1, 'materials': {'fab_drainage': atlas}}))
    assets = {'square-rusty-drain': {'source_sha256': 'a'*64}}
    assert F._atlas(assets, p, tmp_path) is not None
    assert F._atlas({}, p, tmp_path) is None
    assert F._atlas({'square-rusty-drain': {'source_sha256': 'b'*64}}, p, tmp_path) is None
    atlas['uv_rects_by_tier'] = {'High': {'square-rusty-drain': [0, 0, .5, .5]}}
    p.write_text(json.dumps({'schema': 1, 'materials': {'fab_drainage': atlas}}))
    assert F._atlas(assets, p, tmp_path) is None
    atlas.pop('uv_rects_by_tier')
    atlas['textures']['High']['basecolor'] = '../external.png'
    p.write_text(json.dumps({'schema': 1, 'materials': {'fab_drainage': atlas}}))
    assert F._atlas(assets, p, tmp_path) is None


def test_drainage_atlas_remaps_existing_gully_uv_without_geometry_changes(monkeypatch):
    from roads.decals import gullies
    b = MeshBuf()
    net = network()
    gullies(b, net, {})
    geometry = [p.V.copy() for p in b.parts]
    atlas = {'uv_rects': {'square-rusty-drain': [.1, .2, .4, .8],
                         'metal-manhole-cover': [.55, .55, .95, .95]}}
    monkeypatch.setattr(F, '_atlas', lambda assets: atlas)
    report = {}
    F.drainage(b, net, {'square-rusty-drain': {}, 'metal-manhole-cover': {}}, report)
    assert report['drainage_atlas'] is True
    assert all(p.mat == 'fab_drainage' for p in b.parts)
    for p, v in zip(b.parts, geometry):
        assert np.array_equal(p.V, v)
        assert np.allclose(p.UV.min(0), [.1, .2])
        assert np.allclose(p.UV.max(0), [.4, .8])
    for p in b.parts[len(geometry):]:
        assert np.allclose(p.UV.min(0), [.55, .55])
        assert np.allclose(p.UV.max(0), [.95, .95])


def test_yard_and_road_grates_share_atlas_preserving_geometry_and_depth(monkeypatch):
    from roads.decals import gullies
    from streetscape.life import yard_drains
    net, buf = network(), MeshBuf()
    gullies(buf, net, {})
    yard_drains(buf, [{'id': 'yard', 'mat': 'yard_concrete', 'poly': box(0, 10, 100, 110)}],
                Polygon(), lambda e, n: np.full_like(e, 7.125), {})
    before = [(p.V.copy(), p.T.copy(), p.UV.copy(), p.src) for p in buf.parts]
    assert any(src.startswith('drain:') for _, _, _, src in before)
    atlas = {'uv_rects': {'square-rusty-drain': [.1, .2, .4, .8]}}
    monkeypatch.setattr(F, '_atlas', lambda assets: atlas)
    report = {}
    F.drainage(buf, net, {'square-rusty-drain': {}}, report)
    assert report['gully_replacements'] > 0 and report['yard_drain_replacements'] > 0
    assert report['drainage_replacements'] == len(before) == len(buf.parts)
    assert report['drainage_source_counts'] == {'square-rusty-drain': len(before)}
    assert report['added_drainage_triangles'] == 0
    assert {p.mat for p in buf.parts} == {'fab_drainage'}
    for p, (vertices, triangles, uv, src) in zip(buf.parts, before):
        np.testing.assert_array_equal(p.V, vertices)
        np.testing.assert_array_equal(p.T, triangles)
        np.testing.assert_allclose(p.UV, [.1, .2] + uv * [.3, .6])
        assert p.src == src


def test_grate_replacement_skips_trenches_unknown_sources_and_metric_uv(monkeypatch):
    buf = MeshBuf()
    uv, triangles = [[0, 0], [1, 0], [1, 1], [0, 1]], [[0, 1, 2], [0, 2, 3]]
    small = np.array([[0, 0, 4], [.5, 0, 4], [.5, .6, 4], [0, .6, 4]])
    long = small.copy(); long[[1, 2], 0] = 12
    for v, texture_uv, source in ((small, uv, 'unknown:grate'),
                                 (long, uv, 'drain:trench'),
                                 (small, np.asarray(uv) * 4, 'gully:metric')):
        buf.add('markings', 'drain_grate', v, texture_uv, triangles, src=source)
    report = {}
    F.drainage(buf, network(), {'square-rusty-drain': {}}, report)
    assert report['drainage_replacements'] == 0
    assert all(p.mat == 'drain_grate' for p in buf.parts)


def test_apply_reports_overall_placed_source_counts(monkeypatch):
    monkeypatch.setattr(F, 'load_ready', lambda: {'square-rusty-drain': {}})
    monkeypatch.setattr(F, 'drainage', lambda buf, net, assets, rep:
                        rep.update({'drainage_source_counts': {'square-rusty-drain': 4}}))
    monkeypatch.setattr(F, 'props', lambda *args, **kwargs: args[8].update({'props': {'grass-clumps': 3}}))
    report = {}
    F.apply(SimpleNamespace(buf=MeshBuf(), net=network()), SimpleNamespace(items=[]),
            Polygon(), Polygon(), [], [], None, report, lambda *args: None)
    rep = report['megascans']
    assert rep['placed_source_count'] == 2
    assert rep['placed_source_counts'] == {'grass-clumps': 3, 'square-rusty-drain': 4}



def test_props_accepts_exact_stage_numpy_route_and_clears_corridor():
    flat = lambda e, n: np.zeros_like(e, dtype=float)
    net = network(500)
    assets = {a: {'models': [{'lods': []}]} for a in F.GROUND_IDS}
    road = box(-10, -3, 510, 3)
    route = np.column_stack([np.arange(0, 501, 10), np.full(51, 7.), np.zeros(51)])
    pl, report = Placer(flat, flat), {}
    F.props(pl, net, assets, road, Polygon(), [], [], route, report)
    assert pl.items
    corridor = __import__('shapely').geometry.LineString(route[:, :2]).buffer(2.5)
    assert all(not corridor.contains(__import__('shapely').geometry.Point(it['e'], it['n'])) for it in pl.items)
