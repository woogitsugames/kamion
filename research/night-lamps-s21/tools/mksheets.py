"""Arkusze 4x4 z już pobranych miniatur triage (ta sama kolejność co commons_thumbs.py)."""
import sys, json, os, random
from PIL import Image, ImageDraw
d = sys.argv[1]
c = json.load(open(sys.argv[2]))
pri = [x for x in c if not x['title'].split(' ', 3)[-1].startswith(('January', 'February', 'March', 'October', 'November', 'December'))]
gen = [x for x in c if x not in pri]
random.Random(20261115).shuffle(gen)
sel = (pri + gen)[:160]
tiles = [(k, x, os.path.join(d, 't%03d.jpg' % k)) for k, x in enumerate(sel) if os.path.exists(os.path.join(d, 't%03d.jpg' % k))]
json.dump([{'k': k, **x} for k, x, _ in tiles], open(os.path.join(d, 'index.json'), 'w'), ensure_ascii=False, indent=0)
for s in range(0, len(tiles), 16):
    sh = Image.new('RGB', (960, 4 * 196))
    dr = ImageDraw.Draw(sh)
    for j, (k, x, fn) in enumerate(tiles[s:s + 16]):
        try:
            im = Image.open(fn).convert('RGB')
        except Exception:  # noqa
            continue
        im.thumbnail((240, 180))
        X, Y = (j % 4) * 240, (j // 4) * 196
        sh.paste(im, (X, Y + 16))
        dr.text((X + 2, Y + 2), '%03d %s' % (k, x['title'][5:22]), fill=(255, 255, 0))
    sh.save(os.path.join(d, 'sheet%02d.jpg' % (s // 16)), quality=85)
print(len(tiles))
