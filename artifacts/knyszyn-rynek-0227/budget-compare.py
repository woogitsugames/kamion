"""Compare editor estimates for common control cameras; not a phone measurement."""
import re, sys
from pathlib import Path

def read(p):
    d={}
    for line in p.read_text(encoding='utf8').splitlines():
        m=re.match(r'^([^:]+): .*?drawsEst=(\d+).*?trisExact=(\d+)',line)
        if m: d[m.group(1)]=[int(m.group(2)),int(m.group(3)),0,0]
        else:
            m=re.match(r'^  (.+?) instanced .*?draws (\d+),.*?trianglesExact (\d+)',line)
            if m and m.group(1) in d: d[m.group(1)][2:]=[int(m.group(2)),int(m.group(3))]
    return d
root=Path('artifacts/knyszyn-rynek-0227'); iteration=sys.argv[1] if len(sys.argv)>1 else 'r2'
for tier in ('Low-clear','High-clear','Low-dusk','High-dusk'):
    a=read(root/'before'/tier/'stats.txt');b=read(root/iteration/tier/'stats.txt');same=a.keys()&b.keys()
    def metrics(v): return (v[0],v[0]+v[2],v[1],v[1]+v[3])
    print(tier,'common',len(same),'new',len(b.keys()-a.keys()))
    for i,label in enumerate(('mesh_draws_est','draws_plus_instanced','mesh_tris','tris_plus_instanced')):
        key=max(same,key=lambda k:metrics(b[k])[i]-metrics(a[k])[i]);
        print(label,'max before',max((metrics(v)[i],k) for k,v in a.items()),'after',max((metrics(v)[i],k) for k,v in b.items()),'max increase',key,metrics(b[key])[i]-metrics(a[key])[i])
