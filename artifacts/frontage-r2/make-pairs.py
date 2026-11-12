"""ADR 0129 pairs, <= 960 px wide. Usage: make-pairs.py <after-dir> [Tier-Lighting]
  pairs-<after>-<TL>/sbs-g3-b-*.jpg   photo | before (baseline) | after           (SBS photo poses, G3-B)
  pairs-2024-<after>-<TL>/*.jpg       2024 photo | before | after  (control cameras; no photo: before | after)
"""
import json
import os
import subprocess
import sys

here = os.path.dirname(os.path.abspath(__file__))
repo = os.path.normpath(os.path.join(here, '..', '..'))
a = sys.argv[1] if len(sys.argv) > 1 else 'after'
tl = sys.argv[2] if len(sys.argv) > 2 else 'Low-overcast'
REG = os.path.join(repo, 'Data', 'Regions', 'bialystok-industrial-c')


def lab(t):
    return ['-gravity', 'NorthWest', '-fill', 'white', '-undercolor', '#000000a0', '-pointsize', '14', '-annotate', '+4+4', t]


def tile(path, w, h, text):
    return ['(', path, '-resize', f'{w}x{h}!', *lab(text), ')']


out1 = os.path.join(here, f'pairs-{a}-{tl}')
os.makedirs(out1, exist_ok=True)
n = 0
for r in json.load(open(os.path.join(REG, 'sbs_references.json'), encoding='utf-8'))['references']:
    cam = r['camera']
    if 'sbs-g3-b-' not in cam:
        continue
    photo = os.path.join(repo, r['photo'])
    b = os.path.join(here, 'baseline', 'renders', tl, cam + '.png')
    c = os.path.join(here, a, 'renders', tl, cam + '.png')
    if not (os.path.exists(photo) and os.path.exists(b) and os.path.exists(c)):
        continue
    h = int(320 * r['height'] / r['width'])
    subprocess.run(['magick', *tile(photo, 320, h, f"photo {r['captured_at']} {r['author']} CC BY-SA 4.0"),
                    *tile(b, 320, h, 'before (main, ADR 0126)'), *tile(c, 320, h, f'after (ADR 0129) {tl}'),
                    '+append', '-quality', '90', os.path.join(out1, cam + '.jpg')], check=True)
    n += 1
print(n, 'SBS pairs ->', out1)

out2 = os.path.join(here, f'pairs-2024-{a}-{tl}')
os.makedirs(out2, exist_ok=True)
for c in json.load(open(os.path.join(REG, 'g3b_frontage_cameras.json'), encoding='utf-8'))['cameras']:
    b = os.path.join(here, 'baseline', f'control-{tl}', c['id'] + '.png')
    r = os.path.join(here, a, f'control-{tl}', c['id'] + '.png')
    if not os.path.exists(r):
        continue
    parts = []
    if c.get('photo'):
        parts += tile(os.path.join(repo, c['photo']), 320, 240, 'photo 2024 (Mapillary, CC BY-SA 4.0)')
    k = 3 if c.get('photo') else 2
    w = 960 // k
    if os.path.exists(b):
        parts += tile(b, w, w * 3 // 4, 'before (main, ADR 0126)')
    parts += tile(r, w, w * 3 // 4, f'after (ADR 0129) {tl}')
    subprocess.run(['magick', *parts, '+append', '-quality', '90', os.path.join(out2, c['id'] + '.jpg')], check=True)
    # full-width after frame for close reading
    subprocess.run(['magick', r, '-resize', '960x', '-quality', '90', os.path.join(out2, c['id'] + '-after.jpg')], check=True)
    print(os.path.join(out2, c['id'] + '.jpg'))
