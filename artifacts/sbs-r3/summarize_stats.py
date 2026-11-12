"""Read every camera and instanced counter separately; never treat editor estimates as device measurements."""
import argparse,csv,json,re
from pathlib import Path
STATIC=re.compile(r'^(sbs-[^:]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)')
INSTANCE=re.compile(r'^\s+(sbs-\S+) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k')
def read(root):
    rows={}
    for path in sorted(root.glob('*/stats-*.txt')):
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            match=STATIC.match(line)
            if match:
                camera,objects,draws,shadow,tris=match.groups();key=(path.parent.name,camera)
                row=rows.setdefault(key,{'state':key[0],'camera':camera})
                row.update(objects=int(objects),draws_static_est=int(draws),shadow_draws_static_est=int(shadow),tris_static_k=int(tris))
            match=INSTANCE.match(line)
            if match:
                camera,draws,instances,tris=match.groups();key=(path.parent.name,camera)
                rows.setdefault(key,{'state':key[0],'camera':camera}).update(draws_instanced_est=int(draws),instances=int(instances),tris_instanced_k=int(tris))
    for row in rows.values():
        if 'draws_static_est' in row and 'draws_instanced_est' in row:
            row['draws_total_est']=row['draws_static_est']+row['draws_instanced_est']
            row['tris_total_k']=row['tris_static_k']+row['tris_instanced_k']
        else: raise ValueError(f'incomplete camera counters: {row}')
    return rows
ap=argparse.ArgumentParser();ap.add_argument('--renders',type=Path,required=True);ap.add_argument('--baseline',type=Path);ap.add_argument('--output',type=Path,required=True)
a=ap.parse_args();rows=read(a.renders);old=read(a.baseline) if a.baseline else {}
for key,row in rows.items():
    if key in old:
        for field in ('draws_static_est','draws_instanced_est','shadow_draws_static_est','tris_static_k','tris_instanced_k','draws_total_est','tris_total_k'):
            row['historical_delta_'+field]=row[field]-old[key][field]
a.output.mkdir(parents=True,exist_ok=True)
data={'note':'Editor CPU estimates before batching, not GPU/phone counters. Historical baseline uses different main and may use different poses; deltas are not isolated SBS cost.','cameras':list(rows.values())}
(a.output/'camera-counters.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
if rows:
    fields=list(dict.fromkeys(k for row in rows.values() for k in row))
    with (a.output/'camera-counters.csv').open('w',newline='',encoding='utf-8-sig') as f:
        writer=csv.DictWriter(f,fieldnames=fields);writer.writeheader();writer.writerows(rows.values())
print('Counter rows:',len(rows))
