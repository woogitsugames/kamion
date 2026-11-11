"""Compose every A/B frame and compare existing CPU-side SceneStats (not device/GPU counters)."""
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent


def stats(path):
    rows = {}
    for line in path.read_text().splitlines():
        m = re.search(r'([^ :]+): objects=\d+ drawsEst=(\d+) shadowDrawsEst=\d+ trisK=(\d+)', line)
        if m:
            rows.setdefault(m[1], {}).update(draws=int(m[2]), tris_k=int(m[3]))
        m = re.search(r'([^ :]+) instanced .*: draws (\d+), instances \d+, triangles (\d+)k', line)
        if m:
            rows.setdefault(m[1], {}).update(instance_draws=int(m[2]), instance_tris_k=int(m[3]))
    return {k: dict(draws=v['draws']+v.get('instance_draws',0),
                    tris_floor=1000*(v['tris_k']+v.get('instance_tris_k',0)),
                    rounding_upper=1998 if 'instance_tris_k' in v else 999) for k,v in rows.items()}


out = ROOT / 'compare'; out.mkdir(exist_ok=True)
budget = []
for tier in ('Low','High'):
    for light in ('overcast','clear'):
        key = f'{tier}-{light}'
        before, after = ROOT/'before'/key, ROOT/'after'/key
        bs, ass = stats(before/'stats.txt'), stats(after/'stats.txt')
        for name,b in bs.items():
            a=ass[name]
            budget.append(dict(tier=tier,lighting=light,camera=name,before=b,after=a,
                               draws_delta=a['draws']-b['draws'],
                               tris_upper_delta_pct=100*((a['tris_floor']+a['rounding_upper'])/b['tris_floor']-1)))
        names = sorted(p.name for p in before.glob('*.png') if not p.stem.endswith(('_mask','_envcube')))
        for group in ('route','detail'):
            sel=[n for n in names if n.startswith('furniture-') == (group=='detail')]
            sheet=Image.new('RGB',(960,250*len(sel)),(30,30,30)); draw=ImageDraw.Draw(sheet)
            for i,name in enumerate(sel):
                draw.text((8,250*i+5),f'{name} | BEFORE (left) / AFTER (right) | {key}',fill='white')
                for j,directory in enumerate((before,after)):
                    with Image.open(directory/name) as im:
                        im.thumbnail((480,222),Image.Resampling.LANCZOS)
                        sheet.paste(im,(480*j,250*i+24))
            sheet.save(out/f'{key}-{group}.jpg',quality=93)
(ROOT/'frame-budget.json').write_text(json.dumps(budget,indent=2)+'\n')
low=[x for x in budget if x['tier']=='Low' and not x['camera'].startswith('furniture-')]
summary=dict(contract='CPU SceneStats + instanced; k-tris quantisation conservatively bounded; not GPU/device',
             route_low_frames=len(low),max_draw_delta=max(x['draws_delta'] for x in low),
             max_tris_upper_delta_pct=max(x['tris_upper_delta_pct'] for x in low))
(ROOT/'frame-budget-summary.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary))
if summary['max_draw_delta']>0 or summary['max_tris_upper_delta_pct']>3:
    raise SystemExit('Low budget regression: inspect frames/stats before accepting')
