"""Small metadata-only validation; no geometry build, image decode or test suite."""
import json
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def legacy(path):
    rows = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'([^:]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
        if m:
            rows[m[1]] = dict(zip(('objects', 'worldDraws', 'shadows', 'worldK'), map(int, m.groups()[1:])))
        m = re.match(r'  (.+) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k, cells (\d+), forest HLOD cells (\d+)', line)
        if m:
            rows[m[1]].update(zip(('instanceDraws', 'instances', 'instanceK', 'cells', 'hlodCells'), map(int, m.groups()[1:])))
    return rows


def validate(stage, condition, reference=None):
    folder = ROOT / stage / condition
    inputs = json.loads((ROOT / f'{stage}-inputs.json').read_text(encoding='utf-8-sig'))
    assert inputs['cameras_sha'].lower() == hashlib.sha256((ROOT / 'cameras.json').read_bytes()).hexdigest()
    dump = json.loads((folder / 'exact-stats.json').read_text(encoding='utf-8-sig'))
    assert dump['schema'] == 'kamion/life-exact-cpu/1'
    assert not dump['errors'], dump['errors']
    assert len(dump['models']) == 14
    rows = {r['id']: r for r in dump['rows']}
    assert len(rows) == len(dump['rows']) == 114
    old = legacy(folder / 'stats.txt')
    assert rows.keys() == old.keys()
    if reference:
        assert old == legacy(ROOT / reference / condition / 'stats.txt'), 'Prior capture counters differ'
    for name, r in rows.items():
        expected = old[name]
        for key in ('objects', 'worldDraws', 'instanceDraws', 'instances', 'cells', 'hlodCells'):
            assert r[key] == expected.get(key, 0), (name, key, r[key], expected.get(key, 0))
        assert r['worldTriangles'] // 1000 == expected['worldK'], name
        assert r['instanceTriangles'] // 1000 == expected.get('instanceK', 0), name
        # SceneStats runs after RenderToPixels restores the camera target. Its
        # world frustum can therefore have the editor aspect (4:3 here), whereas
        # WorldInstances.Last is captured during the actual 2340x1080 render.
        # Match that existing contract explicitly; do not call this a GPU count.
        assert 0.1 < r['aspect'] < 10, (name, r['aspect'])
    return rows, dump['models']


if __name__ == '__main__':
    stage = sys.argv[1]
    reference = sys.argv[2] if len(sys.argv) > 2 else None
    result = {}
    for condition in ('Low-clear', 'Low-overcast', 'High-clear', 'High-overcast'):
        rows, models = validate(stage, condition, reference)
        result[condition] = {'rows': len(rows), 'models': models, 'legacy_match': True, 'prior_capture_match': reference}
    (ROOT / f'{stage}-validation.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({c: {k: v for k, v in r.items() if k != 'models'} for c, r in result.items()}, indent=2))

