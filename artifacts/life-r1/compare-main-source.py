from pathlib import Path
import subprocess,json
p=Path('artifacts/life-r1')
blob=subprocess.check_output(['git','cat-file','blob','5f2aa277:Data/Regions/bialystok-industrial-c/generated/world_manifest.json'])
base=json.loads(blob)
(p/'canonical-main-manifest.json').write_bytes(blob)
current=json.loads(Path('Data/Regions/bialystok-industrial-c/generated/world_manifest.json').read_text(encoding='utf-8-sig'))
def index(d):
    out={}
    for c in d['chunks']:
        for e in (c,c['low'],c['instances']):out[e['file']]=e['sha256']
    return out
b,a=index(base),index(current)
diffs=[dict(file=f,before=b.get(f),after=a.get(f)) for f in sorted(b.keys()|a.keys()) if b.get(f)!=a.get(f)]
(p/'raw-vs-main-base.json').write_text(json.dumps(dict(base='5f2aa277',count=len(a),changed=len(diffs),diffs=diffs),indent=2),encoding='utf-8')
print(json.dumps(dict(raw_count=len(a),changed=len(diffs))))
