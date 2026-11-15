"""Pobiera miniatury 960 px wskazanych plików Commons (upload.wikimedia.org, bez API), zapisuje + sha256."""
import sys, hashlib, time, os
sys.path.insert(0, sys.argv[1])
from httpc import get  # noqa
from commons_thumbs import thumb_url  # noqa
outdir = sys.argv[2]
os.makedirs(outdir, exist_ok=True)
for line in open(sys.argv[3]):
    if not line.strip():
        continue
    key, title = line.strip().split('\t')
    fn = os.path.join(outdir, key + '_v.jpg')
    if os.path.exists(fn):
        continue
    try:
        b = get(thumb_url(title, 960), tries=4)
    except Exception as e:  # noqa
        print('FAIL', key, e)
        continue
    open(fn, 'wb').write(b)
    print(key, len(b), hashlib.sha256(b).hexdigest(), thumb_url(title, 960), flush=True)
    time.sleep(8)
