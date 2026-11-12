"""Report every captured view, with independent static and instanced budgets."""
import csv
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
MAIN = Path(r'C:\Users\matma\Documents\Claude\kamion')
STATIC = re.compile(r'^(.*?): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)')
INSTANCED = re.compile(r'^  (.*?) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k')

def read_stats(path):
    result = {}
    for line in path.read_text().splitlines():
        if match := STATIC.match(line):
            camera, objects, draws, shadows, tris = match.groups()
            result[camera] = dict(objects=int(objects), static_draws=int(draws),
                                  shadow_draws=int(shadows), static_tris_k=int(tris),
                                  instanced_draws=0, instances=0, instanced_tris_k=0)
        if match := INSTANCED.match(line):
            camera, draws, instances, tris = match.groups()
            result[camera].update(instanced_draws=int(draws), instances=int(instances),
                                  instanced_tris_k=int(tris))
    return result

def pair(left, right, target, titles):
    sheet = Image.new('RGB', (960, 256), 'white')
    draw = ImageDraw.Draw(sheet)
    for column, (path, title) in enumerate(zip((left, right), titles)):
        frame = ImageOps.contain(Image.open(path).convert('RGB'), (480, 222))
        sheet.paste(frame, (column*480, 30))
        draw.text((column*480+3, 5), title[:72], fill='black')
    sheet.save(target, quality=93)

rows = []
if not (HERE/'After.complete').exists():
    raise RuntimeError('After matrix has not completed')
pairs = HERE / 'pairs'
pairs.mkdir(exist_ok=True)
for tier in ('Low', 'High'):
    for lighting in ('clear', 'overcast'):
        config = f'{tier}-{lighting}'
        before = read_stats(HERE / 'before' / config / 'stats.txt')
        after = read_stats(HERE / 'after' / config / 'stats.txt')
        assert before.keys() == after.keys(), (config, before.keys() ^ after.keys())
        for camera in before:
            b, a = before[camera], after[camera]
            draws = a['static_draws']+a['instanced_draws']-b['static_draws']-b['instanced_draws']
            bt = b['static_tris_k']+b['instanced_tris_k']
            at = a['static_tris_k']+a['instanced_tris_k']
            row = dict(configuration=config, camera=camera, before=b, after=a,
                       delta_draws=draws, delta_tris_k=at-bt,
                       low_budget_pass=(draws <= 0 and at <= bt*1.02) if tier == 'Low' else None)
            rows.append(row)
            if camera.startswith('edge-'):
                pair(HERE/'before'/config/f'{camera}.png', HERE/'after'/config/f'{camera}.png',
                     pairs/f'{config}-{camera}.jpg', (f'Przed | {camera} | {config}', f'Po | {camera} | {config}'))
(HERE/'measurements.json').write_text(json.dumps(rows, indent=2), encoding='utf-8')
with (HERE/'all-cameras.csv').open('w', newline='', encoding='utf-8-sig') as stream:
    fields = ['configuration', 'camera', 'delta_draws', 'delta_tris_k', 'low_budget_pass']
    fields += [f'{phase}_{key}' for phase in ('before', 'after') for key in rows[0]['before']]
    writer = csv.DictWriter(stream, fieldnames=fields)
    writer.writeheader()
    for row in rows:
        flat = {key:row[key] for key in fields[:5]}
        flat.update({f'{phase}_{key}':value for phase in ('before','after') for key,value in row[phase].items()})
        writer.writerow(flat)

refs = json.loads((ROOT/'Data/Regions/bialystok-industrial-c/sbs_references.json').read_text())['references']
photo_index = []
excluded = []
for ref in refs:
    camera = ref['camera']
    confidence = ref.get('pose_confidence', 'C')
    if confidence not in ('A','B','C'):
        raise ValueError(f'Unknown pose confidence: {camera} {confidence}')
    if confidence == 'C':
        excluded.append(dict(camera=camera,reason='pose_confidence C'))
        continue
    frozen_photo = HERE/'reference-photos'/f'{camera}.png'
    photo = frozen_photo if frozen_photo.exists() else MAIN/ref.get('comparison_photo', ref['photo'])
    if not photo.exists():
        raise FileNotFoundError(f'Accepted comparison photo unavailable: {photo}')
    expected = ref.get('comparison_sha256') or ref.get('sha256')
    if not expected or hashlib.sha256(photo.read_bytes()).hexdigest() != expected:
        raise RuntimeError(f'Reference photo hash mismatch: {camera}')
    for config in ('Low-clear','High-clear','Low-overcast','High-overcast'):
        render = HERE/'after'/config/f'{camera}.png'
        if not render.exists() or not photo.exists():
            continue
        target = pairs/f'photo-{config}-{camera}.jpg'
        pair(photo, render, target, (f"Zdjecie | {ref['author']} | {ref['license']}", f'Render | {config} | poza {confidence}/WORKING_VALUE'))
        photo_index.append(dict(camera=camera, configuration=config, pair=target.name,
                                photo=str(photo), source=ref['page_url'], author=ref['author'],
                                license=ref['license'], pose=confidence, photometry='UNVERIFIED'))
(HERE/'photo-index.json').write_text(json.dumps(photo_index, indent=2), encoding='utf-8')
(HERE/'excluded-references.json').write_text(json.dumps(excluded,indent=2),encoding='utf-8')
low = [row for row in rows if row['configuration'].startswith('Low')]
summary = dict(pairs=len(rows), photographic_pairs=len(photo_index), low_pairs=len(low),
               low_failures=[row for row in low if not row['low_budget_pass']],
               note='Editor CPU estimates with rounded triangles; no device GPU claim.')
(HERE/'budget-summary.json').write_text(json.dumps(summary, indent=2), encoding='utf-8')
print(json.dumps({key:value for key,value in summary.items() if key != 'low_failures'}))
print('Low budget failures:', len(summary['low_failures']))
