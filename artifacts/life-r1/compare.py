import json, re
from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
ROOT = Path(__file__).resolve().parent
route_path=ROOT/'route-camera-ids.json'
route_ids=set(json.loads(route_path.read_text(encoding='utf-8-sig'))['ids']) if route_path.exists() else set()

def read_stats(path):
    data = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        m = re.match(r'([^:]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
        if m:
            data[m[1]] = dict(zip(('objects','draws','shadows','tris_k'), map(int,m.groups()[1:])))
        m = re.match(r'  (.+) instanced \(props\+trees\): draws (\d+), instances (\d+), triangles (\d+)k, cells (\d+), forest HLOD cells (\d+)', line)
        if m:
            data.setdefault(m[1],{}).update(dict(zip(('instance_draws','instances','instance_tris_k','cells','forest_cells'),map(int,m.groups()[1:]))))
    return data

results = {}
for condition in ('Low-clear','Low-overcast','High-clear','High-overcast'):
    before = read_stats(ROOT/'before'/condition/'stats.txt')
    after = read_stats(ROOT/'after'/condition/'stats.txt')
    if before.keys() != after.keys():
        raise ValueError(f'Camera mismatch: {condition}')
    rows=[]
    for camera, b in before.items():
        a=after[camera]
        delta={k:a[k]-b[k] for k in b}
        total_b=b['tris_k']+b.get('instance_tris_k',0)
        total_a=a['tris_k']+a.get('instance_tris_k',0)
        total_draw_delta=delta['draws']+delta.get('instance_draws',0)
        rows.append(dict(camera=camera,is_route=camera in route_ids,before=b,after=a,delta=delta,total_draw_delta=total_draw_delta,total_tris_percent=100*(total_a-total_b)/max(total_b,1)))
    results[condition]=rows
    out=ROOT/'review'/condition
    out.mkdir(parents=True,exist_ok=True)
    for row in rows:
        camera=row['camera']
        if not camera.startswith(('r10b_','g_dirt_','g_current_','g_r4_','r10_wheel','r10_front','r10_rear')):
            continue
        canvas=Image.new('RGB',(960,250),'#252525')
        draw=ImageDraw.Draw(canvas)
        for x,stage in ((0,'before'),(480,'after')):
            path=ROOT/stage/condition/f'{camera}.png'
            if not path.exists(): continue
            with Image.open(path) as im:
                thumb=ImageOps.contain(im.convert('RGB'),(480,220))
                canvas.paste(thumb,(x,25))
            draw.text((x+5,5),f'{stage} | {camera} | {condition}',fill='white')
        canvas.save(out/f'{camera}.jpg',quality=90)
    # Review pages retain 960 px width and stay below 960 px on both axes.
    pairs=sorted(out.glob('*.jpg'))
    for start in range(0,len(pairs),3):
        page=Image.new('RGB',(960,780),'#252525')
        ImageDraw.Draw(page).text((5,5),f'{condition} | Main 5f2aa277 before / R4 after',fill='white')
        for index,pair in enumerate(pairs[start:start+3]):
            with Image.open(pair) as frame:page.paste(frame,(0,30+index*250))
        page.save(out/f'page-{start//3:02d}.png')
(ROOT/'all-camera-budget.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
summary={}
for condition,rows in results.items():
    present={r['camera'] for r in rows}
    route=[r for r in rows if r['is_route']]
    summary[condition]=dict(cameras=len(rows),route_cameras=len(route),missing_route=sorted(route_ids-present),max_total_tris_percent=max(r['total_tris_percent'] for r in rows),max_draw_delta=max(r['delta']['draws'] for r in rows),max_instance_draw_delta=max(r['delta'].get('instance_draws',0) for r in rows),max_total_draw_delta=max(r['total_draw_delta'] for r in rows),route_over_budget=[r['camera'] for r in route if r['total_draw_delta']>0 or r['total_tris_percent']>2])
(ROOT/'budget-summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(summary,indent=2))
