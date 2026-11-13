"""Garden geometry must preserve gates, existing groups and Low instance identity."""
import sys
from pathlib import Path
import numpy as np
from shapely.geometry import Polygon
root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / 'tools/worldgen'))
from streetscape import plots as PLT
from roads.meshing import MeshBuf
from streetscape.plantings import front_gardens
from streetscape.vegetation import garden_canopies

def fixture():
    key = next((f'qa-{i}' for i in range(1000) if PLT.hfloat(f'qa-{i}', 'hedge') > 0.6 and PLT.hfloat(f'qa-{i}', 'adr0154-front') < 0.7))
    buf = MeshBuf()
    for layer in (PLT.KIT_LAYER, PLT.KIT_LAYER_LOW):
        kit = PLT.Kit()
        for x in (-10, 10):
            for y in (-10, 10):
                kit.box(np.array([x, y]), np.array([1.0, 0.0]), 10.0, 10.0, 139.8, 146.0, [0.0, 0.0])
        o = kit.out()
        buf.add(layer, 'plot_kit', o[0], o[1], o[2], COL=o[3])
    gate = {'m': np.array([0.0, -20.0]), 'n': np.array([0.0, -1.0]), 't': np.array([1.0, 0.0]), 'w': 4.0}
    plot = {'id': 'test', 'key': key, 'age': 'old', 'front_style': 'picket', 'front_h': 1.3, 'house_h': 10.0, 'poly': Polygon([(-20, -20), (20, -20), (20, 20), (-20, 20)]), 'foot': Polygon([(-5, 0), (5, 0), (5, 10), (-5, 10)]), 'hard': Polygon([(-2.5, -20), (2.5, -20), (2.5, 0), (-2.5, 0)]), 'lay': {'runs': [{'a': np.array([-20.0, -20.0]), 'b': np.array([20.0, -20.0]), 'n': np.array([0.0, -1.0]), 'front': True}], 'gate': gate, 'wicket': None, 'wickets': []}}
    return (buf, {'plots': [plot]})

def test_front_hedges_leave_gate_and_protected_geometry_intact():
    buf, rp = fixture()
    original = [x.V.tobytes() + x.T.tobytes() for x in buf.parts]
    out = front_gardens(buf, rp, lambda q: 140.0, {})
    assert out['segments'] == 2 and out['tris_low'] > 0
    assert original == [x.V.tobytes() + x.T.tobytes() for x in buf.parts[:2]]
    for part in buf.parts[2:]:
        assert part.layer in ('plots', 'plots_low') and part.mat == 'plot_kit'
        assert not np.any((np.abs(part.V[:, 0]) < 2.5) & (part.V[:, 1] < -15.0)), 'Gate blocked'

def test_front_geometry_and_leaf_colors_are_deterministic():
    a, rp = fixture()
    b, rp2 = fixture()
    assert front_gardens(a, rp, lambda q: 140.0, {}) == front_gardens(b, rp2, lambda q: 140.0, {})
    for first, second in zip(a.parts, b.parts):
        for field in ('V', 'UV', 'T', 'COL'):
            assert np.array_equal(getattr(first, field), getattr(second, field))

def test_front_budget_is_a_hard_cap():
    for cap in (0, 300):
        buf, rp = fixture()
        out = front_gardens(buf, rp, lambda q: 140.0, {}, triangle_limit=cap)
        assert out['tris_low'] <= cap
        if cap == 0:
            assert len(buf.parts) == 2

def test_front_cannot_create_a_new_renderer_group():
    buf, rp = fixture()
    buf.parts = []
    out = front_gardens(buf, rp, lambda q: 140.0, {})
    assert out['segments'] == 0 and (not buf.parts)
    assert out['skipped']['renderer_bounds'] > 0

def test_existing_high_crowns_change_without_moving_or_adding_trees():
    _, rp = fixture()
    high = {'p': 'tree_maple', 'v': 2, 'h': 11.0, 'e': 0.0, 'n': 0.0, 'z': 140.0, 'src': 'plot:test:canopy', 'tier': 'high'}
    low = {**high, 'tier': 'low'}
    forest = {**high, 'src': 'forest:sample', 'tier': 'high'}
    before = [dict(x) for x in (high, low, forest)]
    result = garden_canopies([high, low, forest], rp, {})
    assert len(result) == 3
    assert result[0]['h'] == 13.5 and result[0]['garden_canopy_width'] == 1.35
    for field in ('p', 'v', 'e', 'n', 'z', 'src', 'tier'):
        assert result[0][field] == high[field]
    assert result[1] == low and result[2] == forest
    assert [high, low, forest] == before

def test_canopy_adjustment_never_shortens_an_existing_mature_tree():
    _, rp = fixture()
    tree = {'p': 'tree_birch', 'v': 1, 'h': 20.0, 'e': 0.0, 'n': 0.0, 'z': 140.0, 'src': 'plot:test:canopy', 'tier': 'high'}
    result = garden_canopies([tree], rp, {})
    assert result[0]['h'] == 20.0


def test_crown_height_reads_nearby_roof_geometry_instead_of_group_first_lod1():
    from types import SimpleNamespace
    _, rp = fixture()
    plot = rp['plots'][0]
    plot['houses'] = ['near-roof', 'distant-roof']
    plot['house_polys'] = [plot['foot'], Polygon([(100, 100), (110, 100), (110, 110), (100, 110)])]
    parts = [SimpleNamespace(layer='buildings', src='near-roof', V=np.array([[0., 0., 156.]])),
             SimpleNamespace(layer='buildings', src='distant-roof', V=np.array([[100., 100., 200.]]))]
    tree = {'p': 'tree_maple', 'v': 2, 'h': 11., 'e': 0., 'n': 0., 'z': 140., 'src': 'plot:test:canopy', 'tier': 'high'}
    report = {}
    result = garden_canopies([tree], rp, report, parts=parts)
    assert result[0]['h'] == 20.5
    assert result[0]['z'] == tree['z']
    assert report['garden_canopies']['list'][0]['nearby_roof_top_evrf2007'] == 156.
