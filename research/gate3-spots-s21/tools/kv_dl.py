"""Download KartaView proc images. Usage: kv_dl.py dl_dir view_dir seq:idx ...
Writes dl_dir/kv_summary.json (merged)."""
import json, sys, os, subprocess, hashlib, time
from PIL import Image
out, view = sys.argv[1], sys.argv[2]
os.makedirs(os.path.join(out, 'kv'), exist_ok=True)
sp = os.path.join(out, 'kv_summary.json')
summ = json.load(open(sp)) if os.path.exists(sp) else {}
USER = {'10733': 'telenavdrives', '14055': 'ziozzzzz', '2763230': 'gpsmapper999', '2769366': 'gpsmapper999', '3686129': 'TMishaaa'}
for arg in sys.argv[3:]:
    sid, idx = arg.split(':')
    ph = {x['sequenceIndex']: x for x in json.load(open(os.path.join(out, f'kvseq_{sid}.json')))['result']['data']}
    x = ph[idx]
    name = f'kv_{sid}_{idx}'
    f = os.path.join(out, 'kv', name + '.jpg')
    url = x['fileurlProc']
    if not os.path.exists(f) or os.path.getsize(f) < 5000:
        for k in range(4):
            r = subprocess.run(['curl', '-sSL', '-m', '180', '-o', f, '-w', '%{http_code}', url], capture_output=True, text=True)
            if r.stdout == '200':
                break
            print('retry', name, r.stdout); time.sleep(5 * (k + 1))
            url = x.get('imageProcUrl') or url
    try:
        im = Image.open(f); im.load()
    except Exception as e:
        print('BAD', name, e); continue
    im.convert('RGB').resize((960, round(im.size[1] * 960 / im.size[0]))).save(os.path.join(view, name + '.jpg'), quality=85)
    summ[name] = dict(id=x['id'], seq=sid, idx=idx, file=f, size=im.size, url=url, page=f'https://kartaview.org/details/{sid}/{idx}/track-info',
                      lat=float(x['lat']), lon=float(x['lng']), heading_api=x.get('heading'), shot=x['shotDate'], user=USER.get(sid),
                      sha256=hashlib.sha256(open(f, 'rb').read()).hexdigest())
    print(name, im.size)
json.dump(summ, open(sp, 'w'), indent=1)
