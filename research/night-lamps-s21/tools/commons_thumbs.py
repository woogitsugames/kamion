"""Miniatury Commons przez upload.wikimedia.org (ścieżka z md5 nazwy) — bez API. Tryb triage: 330 px, arkusze 4x4.
Użycie: commons_thumbs.py <tools> cands.json outdir seed n"""
import sys, json, hashlib, urllib.parse, os, random, io, time
sys.path.insert(0, sys.argv[1])
from httpc import get  # noqa
from PIL import Image, ImageDraw


def thumb_url(title, w):
    name = title.split(':', 1)[1].replace(' ', '_')
    h = hashlib.md5(name.encode('utf-8')).hexdigest()
    q = urllib.parse.quote(name)
    return 'https://upload.wikimedia.org/wikipedia/commons/thumb/%s/%s/%s/%dpx-%s' % (h[0], h[:2], q, w, q)


if __name__ == '__main__':
    cands, outdir, seed, n = sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5])
    os.makedirs(outdir, exist_ok=True)
    c = json.load(open(cands))
    pri = [x for x in c if not x['title'].split(' ', 3)[-1].startswith(('January', 'February', 'March', 'October', 'November', 'December'))]
    gen = [x for x in c if x not in pri]
    random.Random(seed).shuffle(gen)
    sel = pri + gen[:max(0, n - len(pri))]
    tiles = []
    for k, x in enumerate(sel):
        fn = os.path.join(outdir, 't%03d.jpg' % k)
        if not os.path.exists(fn):
            try:
                b = get(thumb_url(x['title'], 330), tries=2)
                open(fn, 'wb').write(b)
            except Exception as e:  # noqa
                print('fail', x['title'], e, file=sys.stderr)
                continue
            time.sleep(0.3)
        tiles.append((k, x, fn))
    json.dump([{'k': k, **x} for k, x, _ in tiles], open(os.path.join(outdir, 'index.json'), 'w'), ensure_ascii=False, indent=0)
    for s in range(0, len(tiles), 16):
        sh = Image.new('RGB', (960, 4 * 196), (0, 0, 0))
        d = ImageDraw.Draw(sh)
        for j, (k, x, fn) in enumerate(tiles[s:s + 16]):
            im = Image.open(fn).convert('RGB')
            im.thumbnail((240, 180))
            X, Y = (j % 4) * 240, (j // 4) * 196
            sh.paste(im, (X, Y + 16))
            d.text((X + 2, Y + 2), '%03d %s' % (k, x['title'][5:20]), fill=(255, 255, 0))
        sh.save(os.path.join(outdir, 'sheet%02d.jpg' % (s // 16)), quality=85)
    print(len(tiles))
