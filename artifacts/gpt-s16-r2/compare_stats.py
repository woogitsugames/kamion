"""Every camera: exact CPU triangle counts; estimated scene draws and instance submissions."""
import argparse,json,re,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'gpt-s16-r1'))
from compare_stats import read as legacy_read


def read_exact(path):
    rows=legacy_read(path)
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        scene=re.match(r'(\S+): .*trisExact=(\d+)',line)
        if scene:rows[scene[1]]['scene_tris_exact']=int(scene[2])
        inst=re.match(r'\s+(\S+) instanced .*trianglesExact (\d+)',line)
        if inst:rows[inst[1]]['instance_tris_exact']=int(inst[2])
    for name,row in rows.items():
        if 'scene_tris_exact' not in row or 'instance_tris_exact' not in row:
            raise ValueError('Exact counters absent; rerender required: '+str(path)+'/'+name)
    return rows


def main():
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);args=p.parse_args()
    integrity=json.loads((args.root/'world-integrity.json').read_text())
    if integrity['failures']:raise ValueError(integrity['failures'])
    result={'units':'CPU scene visibility estimate and instanced submission counters; exact submitted-mesh triangle integers, not GPU/device timing or SRP batches','conditions':{}}
    failures=[];lines=['# Każda kamera — przed / po','','Dokładne liczby trójkątów CPU. Draws sceny pozostają estymatą przed SRP; batche instancji to zgłoszenia. GPU i telefon niezmierzone.','']
    for condition in ('Low-clear','Low-overcast','High-clear','High-overcast'):
        before=read_exact(args.root/'before'/condition/'stats.txt');after=read_exact(args.root/'after'/condition/'stats.txt')
        if before.keys()!=after.keys():raise ValueError('Camera sets differ: '+condition)
        rows=[];lines += ['## '+condition,'','| Kamera | Draws sceny | Batche instancji | Shadow draws | Tris sceny | Tris instancji | Δ tris |','|---|---:|---:|---:|---:|---:|---:|']
        for name,b in before.items():
            a=after[name];delta={k:a[k]-b[k] for k in b}
            baseline=b['scene_tris_exact']+b['instance_tris_exact'];total=a['scene_tris_exact']+a['instance_tris_exact']
            percent=100*(total-baseline)/baseline if baseline else (0 if total==0 else float('inf'))
            rows.append({'camera':name,'before':b,'after':a,'delta':delta,'triangle_growth_percent':percent})
            fields=('scene_draws_est','instance_draws','shadow_draws_est','scene_tris_exact','instance_tris_exact')
            lines.append('| '+name+' | '+' | '.join(f'{b[k]} → {a[k]}' for k in fields)+f' | {percent:+.4f}% |')
            if condition.startswith('Low') and (delta['scene_draws_est']+delta['instance_draws']>0 or delta['shadow_draws_est']>0 or delta['instance_draws']!=0 or delta['instances']!=0 or delta['instance_tris_exact']!=0 or percent>2):
                failures.append(condition+'/'+name)
        result['conditions'][condition]=rows;lines.append('')
    result['low_budget_failures']=failures
    (args.root/'camera-counts.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.root/'CAMERAS.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps({'cameras':{k:len(v) for k,v in result['conditions'].items()},'low_budget_failures':failures,'max_low_triangle_growth_percent':max(x['triangle_growth_percent'] for k,v in result['conditions'].items() if k.startswith('Low') for x in v)}))
    if failures:raise SystemExit(1)


if __name__=='__main__':main()
