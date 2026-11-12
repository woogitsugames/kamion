"""Snapshot generated truck/trailer bytes and semantic prefab poses; no files outside artifacts are written."""
from pathlib import Path
import hashlib
import json
import re
import sys
import yaml

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[1]
label = sys.argv[1]
if not re.fullmatch(r'[a-z0-9-]+', label):
    raise ValueError('Invalid label')

def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()

def prefab(path):
    text = path.read_text(encoding='utf-8-sig')
    text = re.sub(r'^%.*\n', '', text, flags=re.M)
    text = re.sub(r'^--- !u!(\d+) &(\d+)(?: stripped)?\s*$', lambda m: '---\n__type: '+m[1]+'\n__id: '+m[2], text, flags=re.M)
    docs = [d for d in yaml.safe_load_all(text) if d]
    gos = {d['__id']: d['GameObject'] for d in docs if d['__type'] == 1}
    transforms = {d['__id']: d['Transform'] for d in docs if d['__type'] == 4 and 'm_LocalPosition' in d['Transform']}
    cache = {}
    def name(i):
        if not i:
            return ''
        if i not in transforms:
            return '@external:' + str(i)
        if i not in cache:
            t = transforms[i]
            cache[i] = name(t['m_Father']['fileID']) + '/' + gos[t['m_GameObject']['fileID']]['m_Name']
        return cache[i]
    poses = {name(i): {key: t[key] for key in ('m_LocalPosition','m_LocalRotation','m_LocalScale')} for i,t in transforms.items()}
    names = {t['m_GameObject']['fileID']: name(i) for i,t in transforms.items()}
    renderers = {}
    for doc in docs:
        if doc['__type'] == 23 and 'm_GameObject' in doc['MeshRenderer']:
            r = doc['MeshRenderer']
            key = names.get(r['m_GameObject']['fileID'])
            if key:
                renderers[key] = {field: r.get(field) for field in ('m_Enabled','m_RenderingLayerMask','m_CastShadows','m_ReceiveShadows','m_Materials')}
    return {'poses': poses, 'renderers': renderers}

state = {'files': {}, 'prefabs': {}}
for domain in ('Truck','Trailer'):
    for path in sorted((ROOT / 'game/Assets/_Generated' / domain).rglob('*')):
        if not path.is_file():
            continue
        relative = path.relative_to(ROOT).as_posix()
        state['files'][relative] = {'sha256': digest(path), 'bytes': path.stat().st_size}
        if path.suffix == '.prefab':
            state['prefabs'][relative] = prefab(path)
target = OUT / ('fixture-' + label + '.json')
target.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf8')
summary = {'snapshot': label, 'files': len(state['files']), 'prefabs': len(state['prefabs'])}
if len(sys.argv) > 2:
    old = json.loads((OUT / ('fixture-' + sys.argv[2] + '.json')).read_text(encoding='utf8'))
    changed = [p for p in sorted(old['files'].keys() | state['files'].keys()) if old['files'].get(p) != state['files'].get(p)]
    summary.update(changed_files=changed,
                   mesh_or_fbx_changes=[p for p in changed if '/Meshes/' in p or p.lower().endswith('.fbx')],
                   semantic_prefab_changes=[p for p in sorted(old['prefabs'].keys() | state['prefabs'].keys()) if old['prefabs'].get(p) != state['prefabs'].get(p)])
    (OUT / ('fixture-' + label + '-comparison.json')).write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding='utf8')
print(json.dumps(summary, indent=2, ensure_ascii=False))
