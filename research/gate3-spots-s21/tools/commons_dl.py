"""Download 1600px thumbs from commons_info.json into dl/commons/ and make 960px view copies in view/.
Usage: commons_dl.py info.json outdir viewdir"""
import json, sys, os, subprocess, time, hashlib, re
from PIL import Image
UA = 'research-client/1.0 (generic)'
info = json.load(open(sys.argv[1]))
out, view = sys.argv[2], sys.argv[3]
os.makedirs(out, exist_ok=True); os.makedirs(view, exist_ok=True)
summary = {}
for title, p in info.items():
    if 'imageinfo' not in p:
        print('MISSING', title); continue
    ii = p['imageinfo'][0]
    slug = re.sub(r'[^A-Za-z0-9]+', '_', title[5:].rsplit('.', 1)[0])[:60]
    f = os.path.join(out, slug + '.jpg')
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        url = ii.get('thumburl') or ii['url']
        for k in range(6):
            r = subprocess.run(['curl', '-sS', '-m', '120', '-A', UA, '-o', f, '-w', '%{http_code}', url], capture_output=True, text=True)
            if r.stdout.strip() == '200':
                break
            print('retry', r.stdout, title, file=sys.stderr); time.sleep(15 * (k + 1))
        time.sleep(3)
    try:
        im = Image.open(f); im.load()
    except Exception as e:
        print('BAD', title, e); continue
    v = os.path.join(view, slug + '.jpg')
    w = 960
    im.convert('RGB').resize((w, round(im.size[1] * w / im.size[0]))).save(v, quality=85)
    em = ii.get('extmetadata', {})
    g = lambda k: re.sub('<[^>]+>', '', em.get(k, {}).get('value', ''))[:200]
    summary[title] = dict(slug=slug, file=f, size=im.size, thumburl=ii.get('thumburl'), url=ii['url'], page=ii.get('descriptionurl'),
                          sha1=ii.get('sha1'), license=g('LicenseShortName'), artist=g('Artist'), date=g('DateTimeOriginal'),
                          coords=p.get('coordinates'), sha256=hashlib.sha256(open(f, 'rb').read()).hexdigest())
    print(slug, im.size, summary[title]['license'], summary[title]['artist'][:30], summary[title]['date'], [ (c.get('type'), c['lat'], c['lon'], c.get('dim')) for c in (p.get('coordinates') or [])])
json.dump(summary, open(os.path.join(out, 'summary.json'), 'w'), ensure_ascii=False, indent=1)
