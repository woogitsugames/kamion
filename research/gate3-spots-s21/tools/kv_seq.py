"""List frames of KartaView sequences near the 4 points with geometric course.
Usage: kv_seq.py outdir seqid... (writes kvseq_<id>.json, kvseq_<id>_meta.json)"""
import json, sys, os, subprocess, time
sys.path.insert(0, os.path.dirname(__file__))
from geo import P, dist, near
out = sys.argv[1]


def get(url, f):
    if os.path.exists(f):
        try:
            return json.load(open(f))
        except Exception:
            pass
    for k in range(5):
        r = subprocess.run(['curl', '-sS', '-m', '90', '-o', f, url], capture_output=True, text=True)
        try:
            return json.load(open(f))
        except Exception:
            time.sleep(5 * (k + 1))


for sid in sys.argv[2:]:
    d = get(f'https://api.kartaview.org/2.0/sequence/{sid}/photos?itemsPerPage=1000', os.path.join(out, f'kvseq_{sid}.json'))
    m = get(f'https://api.kartaview.org/2.0/sequence/{sid}', os.path.join(out, f'kvseq_{sid}_meta.json'))
    md = m['result']['data']
    print('SEQ', sid, md.get('dateAdded'), 'user', md.get('userId'), md.get('countActivePhotos'))
    ph = sorted(d['result']['data'], key=lambda x: int(x['sequenceIndex']))
    for i, x in enumerate(ph):
        a = (float(x['lat']), float(x['lng']))
        if min(dist(a, v)[0] for v in P.values()) > 120:
            continue
        c = None
        for j in (i + 1, i + 2, i - 1):
            if 0 <= j < len(ph):
                b = (float(ph[j]['lat']), float(ph[j]['lng']))
                dd, cc = dist(a, b) if j > i else dist(b, a)
                if dd > 1.5:
                    c = round(cc, 1); break
        print(' ', x['id'], x['sequenceIndex'], x['shotDate'][:19], x['lat'], x['lng'], 'hdg', x.get('heading'), 'course', c, x.get('wayId'), near(*a))
