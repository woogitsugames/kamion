"""Light-owned proof gallery; source SBS poses/metadata remain untouched.

Integer render heights may differ by <=0.5 pixel from the original aspect.
Pairs are 960px wide. Photometry uses the existing SBS heuristic and is explicitly
WORKING_VALUE, never a gate result. Rejected poses/sunsets are excluded from summary.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
from PIL import Image, ImageDraw
from budget_compare import compare

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('sbs', ROOT/'tools/refs/sbs_gate3.py')
sbs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sbs)
refs = json.loads((ROOT/'Data/Regions/bialystok-industrial-c/sbs_references.json').read_text(encoding='utf-8-sig'))['references']
eligibility = {r['camera']: r for r in json.loads((OUT/'sbs-light-eligibility.json').read_text())}
budgets = {}
for phase in ('before', 'after'):
    metrics = []
    gallery = OUT/'sbs'/phase/'pairs'
    gallery.mkdir(parents=True, exist_ok=True)
    for tier in ('Low', 'High'):
        for light in ('clear', 'overcast'):
            group = f'{tier}-{light}'
            render_root = OUT/'sbs'/phase/'renders'/group
            if phase == 'after':
                for stats in render_root.glob('*/stats.txt'):
                    before = OUT/'sbs/before/renders'/group/stats.parent.name/stats.name
                    budgets[f'{group}/{stats.parent.name}'] = compare(before, stats)
            for ref in refs:
                camera = ref['camera']
                photosrc = ROOT/ref.get('comparison_photo', ref['photo'])
                for key, path in [('sha256', ROOT/ref['photo']), ('comparison_sha256', photosrc)]:
                    if ref.get(key) and hashlib.sha256(path.read_bytes()).hexdigest() != ref[key]:
                        raise ValueError(f'Photo hash mismatch: {camera}/{key}')
                paths = list(render_root.glob(f'*/{camera}.png'))
                if len(paths) != 1:
                    raise ValueError(f'Expected exactly one {phase}/{group}/{camera}: {paths}')
                with Image.open(photosrc) as p, Image.open(paths[0]) as r:
                    photo, render = p.convert('RGB'), r.convert('RGB')
                if abs(render.height-render.width*photo.height/photo.width) > 0.501:
                    raise ValueError(f'Aspect mismatch: {camera}')
                masks = ref.get('authored_overrides', {}).get('masks', {})
                entry = dict(camera=camera, tier=tier, lighting=light,
                             eligible=eligibility[camera]['photometric_use'],
                             pose=ref['pose_status'], photo_sha256=ref.get('comparison_sha256'),
                             render_sha256=hashlib.sha256(paths[0].read_bytes()).hexdigest(),
                             photo=sbs.measurements(photo, ref['horizon_y_fraction'], masks.get('photo')),
                             render=sbs.measurements(render, ref['horizon_y_fraction'], masks.get('render')))
                metrics.append(entry)
                h = round(470*photo.height/photo.width)
                sheet = Image.new('RGB', (960, h+100), '#202020')
                draw = ImageDraw.Draw(sheet)
                draw.text((5, 5), f'{camera} / {group} / {phase} / WORKING_VALUE', fill='white')
                sheet.paste(photo.resize((470, h)), (0, 25))
                sheet.paste(render.resize((470, h)), (490, 25))
                draw.text((5, h+30), f"PHOTO {ref['author']} / {ref['license']} / {ref['captured_at']}", fill='white')
                draw.text((5, h+47), ref['page_url'], fill='white')
                draw.text((5, h+64), 'ROI summary eligible' if entry['eligible'] else 'EXCLUDED: rejected pose and/or sunset', fill='white')
                sheet.save(gallery/f'{group}-{camera}.jpg', quality=94)
    (OUT/'sbs'/phase/'light-metrics.json').write_text(json.dumps(dict(
        status='WORKING_VALUE; heuristic masks, poses unverified; full-frame histograms not scored',
        pairs=metrics), indent=2), encoding='utf-8')
    print(phase, len(metrics), 'pairs')
if not budgets:
    raise ValueError('No SceneStats budget files found')
(OUT/'sbs-budget-all.json').write_text(json.dumps(budgets, indent=2), encoding='utf-8')
print('budget groups', len(budgets), 'camera entries', sum(v['camera_count'] for v in budgets.values()))
