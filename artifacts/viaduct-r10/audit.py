"""Repeatable CPU-side budget and raw GLB batching audit; not GPU draw counters."""
import hashlib
import json
import struct
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MAIN = Path('C:/Users/matma/Documents/Claude/kamion')
GEN = ROOT / 'Data/Regions/bialystok-industrial-c/generated'


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def glb(path):
    data = path.read_bytes()
    n = struct.unpack_from('<I', data, 12)[0]
    return json.loads(data[20:20+n]), hashlib.sha256(data).hexdigest()


before = read(OUT / 'baseline-streetscape-qa.json')
after = read(GEN / 'streetscape_qa.json')
old = {r['camera']: r for r in before['mesh_budget']['frame_estimate']}
rows = []
for r in after['mesh_budget']['frame_estimate']:
    b = old[r['camera']]
    rows.append(dict(camera=r['camera'], before=b['tris_low'], after=r['tris_low'],
                     percent=round(100*(r['tris_low']/b['tris_low']-1), 4),
                     materials_delta=r['materials_low']-b['materials_low']))
(OUT / 'generator-budget.json').write_text(json.dumps(rows, indent=1)+'\n', encoding='utf-8')

chunks = []
for c in read(OUT / 'baseline-world-manifest.json')['chunks']:
    b, sha = glb(MAIN / c['low']['file'])
    a, _ = glb(ROOT / c['low']['file'])
    def groups(doc):
        return sorted((nd.get('name', ''), doc['materials'][p['material']]['name'])
                      for nd in doc.get('nodes', []) if 'mesh' in nd
                      for p in doc['meshes'][nd['mesh']]['primitives'])
    bg, ag = groups(b), groups(a)
    chunks.append(dict(id=c['id'], baseline_verified=sha == c['low']['sha256'],
                       before_groups=len(bg), after_groups=len(ag),
                       added=[x for x in ag if x not in bg], removed=[x for x in bg if x not in ag]))
(OUT / 'low-chunk-batching.json').write_text(json.dumps(chunks, indent=1)+'\n', encoding='utf-8')
print('max Low triangle delta:', max(rows, key=lambda r:r['percent']))
print('raw Low groups delta:', sum(c['after_groups']-c['before_groups'] for c in chunks))
print('verified baseline chunks:', sum(c['baseline_verified'] for c in chunks), '/', len(chunks))
print('underdeck:', after['hero_bridges'].get('underdeck', []))
