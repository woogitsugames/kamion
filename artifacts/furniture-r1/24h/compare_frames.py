"""All-camera CPU estimates, preserving mesh and instance counters separately."""
import csv
import json
import re
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent


def read_stats(path):
    rows = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        match = re.search(r'([^ :]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
        if match:
            camera, objects, draws, shadows, triangles = match.groups()
            rows.setdefault(camera, {}).update(mesh_objects=int(objects), mesh_draws=int(draws),
                                               mesh_shadows=int(shadows), mesh_tris_k=int(triangles))
        match = re.search(r'([^ :]+) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k', line)
        if match:
            camera, draws, instances, triangles = match.groups()
            rows.setdefault(camera, {}).update(instance_draws=int(draws), instances=int(instances),
                                               instance_tris_k=int(triangles))
    for row in rows.values():
        assert 'mesh_draws' in row
        row['total_draws'] = row['mesh_draws'] + row.get('instance_draws', 0)
        row['total_tris_k'] = row['mesh_tris_k'] + row.get('instance_tris_k', 0)
        row['quantisation_upper'] = 1998 if 'instance_tris_k' in row else 999
    return rows


records = []
for tier in ('Low', 'High'):
    for light in ('clear', 'overcast'):
        key = f'{tier}-{light}'
        before, after = ROOT/'before'/key, ROOT/'after'/key
        b, a = read_stats(before/'stats.txt'), read_stats(after/'stats.txt')
        assert b.keys() == a.keys(), f'Missing camera statistics: {key}'
        for camera in sorted(b):
            old, new = b[camera], a[camera]
            denominator = old['total_tris_k']*1000
            delta_upper = (100*((new['total_tris_k']*1000+new['quantisation_upper'])/denominator-1)
                           if denominator else None)
            records.append(dict(tier=tier, lighting=light, camera=camera, before=old, after=new,
                                mesh_draw_delta=new['mesh_draws']-old['mesh_draws'],
                                instance_draw_delta=new.get('instance_draws',0)-old.get('instance_draws',0),
                                total_draw_delta=new['total_draws']-old['total_draws'],
                                tris_delta_upper_percent=delta_upper))
        names = {p.name for p in before.glob('*.png')}
        assert names == {p.name for p in after.glob('*.png')}, f'Missing PNG: {key}'
        # Each sheet is at most 960 px wide. All cameras are included, in groups of six.
        names = sorted(n for n in names if not n.endswith(('_mask.png','_envcube.png')))
        out = ROOT/'compare'; out.mkdir(exist_ok=True)
        for page in range(0, len(names), 6):
            chosen = names[page:page+6]
            sheet = Image.new('RGB', (960, 250*len(chosen)), '#202020')
            draw = ImageDraw.Draw(sheet)
            for row, name in enumerate(chosen):
                draw.text((6, row*250+5), f'{name} | BEFORE / AFTER | {key}', fill='white')
                for col, folder in enumerate((before,after)):
                    with Image.open(folder/name) as im:
                        im = im.convert('RGB'); im.thumbnail((480,222))
                        sheet.paste(im, (col*480,row*250+25))
            sheet.save(out/f'{key}-{page//6+1:02}.jpg', quality=92)
(ROOT/'frame-budget.json').write_text(json.dumps(records,indent=2)+'\n')
with (ROOT/'frame-budget.csv').open('w',newline='',encoding='utf-8-sig') as handle:
    fields = ['tier','lighting','camera','mesh_draw_delta','instance_draw_delta','total_draw_delta',
              'tris_delta_upper_percent']
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
    writer.writeheader(); writer.writerows(records)
print(f'Compared {len(records)} camera/tier/lighting combinations; CPU estimates, not GPU measurements.')
