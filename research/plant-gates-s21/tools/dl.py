"""Download Commons thumbs (<=1600 px) listed in info.json into outdir; also write 960px view copies."""
import sys, os, json, re, hashlib, time, urllib.parse
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import cget
from PIL import Image

info = json.load(open(sys.argv[1]))
outdir = sys.argv[2]
viewdir = sys.argv[3]
only = set(sys.argv[4:])
os.makedirs(outdir, exist_ok=True)
os.makedirs(viewdir, exist_ok=True)
for t, p in info.items():
    ii = p['imageinfo'][0]
    slug = re.sub(r'[^A-Za-z0-9_-]+', '_', t[5:].rsplit('.', 1)[0]).strip('_')
    if only and slug not in only and t not in only:
        continue
    fn = os.path.join(outdir, slug + '.jpg')
    if not os.path.exists(fn):
        url = ii.get('thumburl') if ii['width'] > 1600 or ii['height'] > 1600 else ii['url']
        url = 'https://commons.wikimedia.org/w/thumb.php?f=' + urllib.parse.quote(t[5:].replace(' ', '_')) + '&w=' + str(min(1600, ii['width']) if ii['width'] >= ii['height'] else int(ii['width'] * 1600 / ii['height']))
        d = cget.get(url, binary=True)
        open(fn, 'wb').write(d)
        time.sleep(2)
    im = Image.open(fn)
    v = im.copy()
    v.thumbnail((960, 960))
    v.save(os.path.join(viewdir, slug + '.jpg'), quality=85)
    print(slug, im.size)
