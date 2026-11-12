"""Check actual files after GIS tests, which rewrite region metadata as a side effect."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
REGION = ROOT/'Data/Regions/bialystok-industrial-c/generated'

def walk(obj, trail=''):
    if isinstance(obj,dict):
        if isinstance(obj.get('file'),str) and isinstance(obj.get('sha256'),str):
            yield trail,obj
        for key,value in obj.items():
            yield from walk(value, trail+'/'+key)
    elif isinstance(obj,list):
        for index,value in enumerate(obj):
            yield from walk(value, trail+'/'+str(index))

rows = []
for name in ('world_manifest.json','far_field_qa.json'):
    for trail,entry in walk(json.loads((REGION/name).read_text(encoding='utf-8-sig'))):
        p = ROOT/entry['file']
        actual = hashlib.file_digest(p.open('rb'),'sha256').hexdigest() if p.is_file() else None
        rows.append(dict(manifest=name,key=trail,file=entry['file'],expected=entry['sha256'],actual=actual,
                         match=actual==entry['sha256']))
result = dict(checked=len(rows),mismatches=[r for r in rows if not r['match']],entries=rows)
(OUT/'manifest-file-audit.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(dict(checked=len(rows),mismatches=result['mismatches']),indent=2))
raise SystemExit(1 if result['mismatches'] else 0)
