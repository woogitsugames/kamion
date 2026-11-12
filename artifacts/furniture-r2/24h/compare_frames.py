"""Complete six-variant furniture comparison; exact Low CPU budgets when captures are validated."""
import argparse
import csv
import hashlib
import json
import re
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent
p = argparse.ArgumentParser()
p.add_argument('--metrics-only', action='store_true')
p.add_argument('--label', default='after1')
args = p.parse_args()
assert re.fullmatch(r'[A-Za-z0-9_-]+', args.label)


def stats(path):
    rows = {}
    for line in path.read_text(encoding='utf-8-sig').splitlines():
        m = re.search(r'([^ :]+): objects=(\d+) drawsEst=(\d+) shadowDrawsEst=(\d+) trisK=(\d+)', line)
        if m:
            camera, objects, draws, shadows, tris = m.groups()
            rows[camera] = dict(mesh_objects=int(objects), mesh_draws=int(draws), mesh_shadows=int(shadows), mesh_tris_k=int(tris))
        m = re.search(r'([^ :]+) instanced .*: draws (\d+), instances (\d+), triangles (\d+)k', line)
        if m:
            camera, draws, instances, tris = m.groups()
            rows[camera].update(instance_draws=int(draws), instances=int(instances), instance_tris_k=int(tris))
    assert rows
    for row in rows.values():
        row['total_draws'] = row['mesh_draws'] + row.get('instance_draws', 0)
        row['total_tris_k'] = row['mesh_tris_k'] + row.get('instance_tris_k', 0)
        row['quantisation_upper'] = 1998 if 'instance_tris_k' in row else 999
    return rows


def exact(phase, key, frozen):
    folder = ROOT / f'exact-{phase}' / key
    if not (folder / 'validation.json').exists():
        return None
    proof = json.loads((folder / 'validation.json').read_text(encoding='utf-8-sig'))
    packet_file = folder / 'exact-stats.json'
    assert proof['runner_and_frozen_match'] and proof['unrounded_values_match_every_reported_floor']
    assert proof['frozen_stats_sha256'] == hashlib.sha256((ROOT / phase / key / 'stats.txt').read_bytes()).hexdigest(), 'Revalidate exact counters after a changed capture'
    assert proof['packet_sha256'] == hashlib.sha256(packet_file.read_bytes()).hexdigest()
    packet = json.loads(packet_file.read_text(encoding='utf-8-sig'))
    rows = {row['camera']: row for row in packet['cameras']}
    assert rows.keys() == frozen.keys() and len(rows) == packet['rendered']
    return rows


font = None if args.metrics_only else ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 13)
records = []
variants = []
for tier in ('Low', 'High'):
    for light in ('clear', 'overcast', 'dusk'):
        key = f'{tier}-{light}'
        before, after = ROOT / 'before' / key, ROOT / 'after' / key
        old, new = stats(before / 'stats.txt'), stats(after / 'stats.txt')
        assert old.keys() == new.keys(), ('Missing camera stats', key)
        old_png = {f.stem for f in before.glob('*.png')}
        new_png = {f.stem for f in after.glob('*.png')}
        assert old_png == new_png == old.keys(), ('Missing or extra images', key)
        ex_old, ex_new = exact('before', key, old), exact('after', key, new)
        variants.append(dict(tier=tier, lighting=light, cameras=len(old), exact_before=ex_old is not None, exact_after=ex_new is not None))
        for camera in sorted(old):
            a, b = old[camera], new[camera]
            floor = a['total_tris_k'] * 1000
            upper = 100 * ((b['total_tris_k'] * 1000 + b['quantisation_upper']) / floor - 1) if floor else None
            row = dict(phase=args.label, tier=tier, lighting=light, camera=camera, before=a, after=b,
                mesh_draw_delta=b['mesh_draws'] - a['mesh_draws'],
                instance_draw_delta=b.get('instance_draws', 0) - a.get('instance_draws', 0),
                total_draw_delta=b['total_draws'] - a['total_draws'],
                mesh_shadow_draw_delta=b['mesh_shadows'] - a['mesh_shadows'], tris_delta_upper_percent=upper)
            if ex_old is not None and ex_new is not None:
                ao, bn = ex_old[camera], ex_new[camera]
                total_old = ao['mesh_triangles'] + ao['instance_triangles']
                total_new = bn['mesh_triangles'] + bn['instance_triangles']
                row.update(before_exact_triangles=total_old, after_exact_triangles=total_new,
                    tris_delta_exact_percent=100 * (total_new / total_old - 1) if total_old else None)
            records.append(row)
        if not args.metrics_only:
            out = ROOT / 'compare'
            out.mkdir(exist_ok=True)
            names = sorted(old)
            for start in range(0, len(names), 6):
                chosen = names[start:start + 6]
                sheet = Image.new('RGB', (960, 250 * len(chosen)), '#202020')
                draw = ImageDraw.Draw(sheet)
                for line, name in enumerate(chosen):
                    draw.text((6, line * 250 + 4), f'{name} | PRZED / PO | {key}', font=font, fill='white')
                    for column, folder in enumerate((before, after)):
                        with Image.open(folder / (name + '.png')) as image:
                            image = image.convert('RGB')
                            image.thumbnail((480, 222))
                            sheet.paste(image, (480 * column, line * 250 + 25))
                sheet.save(out / f'{key}-{start // 6 + 1:02}.jpg', quality=92)

(ROOT / 'frame-budget.json').write_text(json.dumps(records, indent=2) + '\n')
(ROOT / 'frame-coverage.json').write_text(json.dumps(variants, indent=2) + '\n')
with (ROOT / 'frame-budget.csv').open('w', newline='', encoding='utf-8-sig') as handle:
    fields = ['phase', 'tier', 'lighting', 'camera', 'mesh_draw_delta', 'instance_draw_delta',
              'total_draw_delta', 'mesh_shadow_draw_delta', 'tris_delta_upper_percent',
              'before_exact_triangles', 'after_exact_triangles', 'tris_delta_exact_percent']
    writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
    writer.writeheader()
    writer.writerows(records)
print(f'Compared every camera: {len(records)} variants, mesh and instance counters separate. CPU estimates, not GPU timings.')
