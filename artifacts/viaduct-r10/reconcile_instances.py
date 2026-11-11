"""Remove rejected r3 grass from the local cache ONLY if all hashes equal tested r4 output.

pytest's world fixture writes raw outputs into a temporary directory (cleaned on
success) but writes the canonical manifest to generated/. Never accept a guessed
replacement: verify all 64 resulting instance files and 128 GLBs before writing.
Future CLI builds reproduce these exact bytes with add_grass=false.
"""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REGION = ROOT / 'Data/Regions/bialystok-industrial-c'
assert json.loads((REGION / 'viaduct_underdeck.json').read_text(encoding='utf-8'))['add_grass'] is False
manifest = json.loads((REGION / 'generated/world_manifest.json').read_text(encoding='utf-8'))
pending = []
removed = 0
for chunk in manifest['chunks']:
    for entry in (chunk, chunk['low']):
        path = ROOT / entry['file']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == entry['sha256'], path
    entry = chunk['instances']
    path = ROOT / entry['file']
    assert path.resolve().is_relative_to((ROOT / 'Data/raw/derived/bialystok-industrial-c/world').resolve())
    obj = json.loads(path.read_text(encoding='utf-8'))
    old = obj['instances']
    obj['instances'] = [it for it in old if ':underdeck0105:Megascans:' not in it.get('src', '')]
    removed += len(old)-len(obj['instances'])
    text = json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    assert hashlib.sha256(text.encode('utf-8')).hexdigest() == entry['sha256'], path
    assert len(obj['instances']) == entry['count']
    pending.append((path, text, entry['sha256']))
for path, text, expected in pending:
    path.write_text(text, encoding='utf-8', newline='\n')
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
report = dict(removed_rejected_grass=removed, verified_instances=len(pending), verified_glbs=2*len(pending),
              source='canonical manifest from 377 passed / 1 xfailed r4 test export')
(OUT / 'cache-reconciliation.json').write_text(json.dumps(report, indent=1)+'\n', encoding='utf-8')
print(report)
