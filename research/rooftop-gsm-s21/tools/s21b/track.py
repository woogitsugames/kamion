import json, glob, math, sys
P = {}
for fn in glob.glob('kvs_*.json') + ['kvseq_10733.json']:
    for p in json.load(open(fn)):
        P[p['id']] = p
bySeqIdx = {}
for p in P.values():
    pass


def brg(a, b):
    la = math.radians((a[0] + b[0]) / 2)
    dx = (b[1] - a[1]) * 111320 * math.cos(la); dy = (b[0] - a[0]) * 110574
    return (math.degrees(math.atan2(dx, dy)) + 360) % 360, math.hypot(dx, dy)


ids = sorted(P, key=int)
pos = {i: k for k, i in enumerate(ids)}
for i in sys.argv[1:]:
    p = P[i]
    # sąsiad wg sequenceIndex w tym samym pliku/sekwencji
    idx = int(p['sequenceIndex'])
    nb = [q for q in P.values() if q.get('fileurlProc', '').split('/')[-1].split('_')[0] == p['fileurlProc'].split('/')[-1].split('_')[0] and int(q['sequenceIndex']) in (idx - 1, idx + 1)]
    nb.sort(key=lambda q: int(q['sequenceIndex']))
    if len(nb) >= 1:
        a = nb[0] if int(nb[0]['sequenceIndex']) < idx else p
        b = nb[-1] if int(nb[-1]['sequenceIndex']) > idx else p
        t, d = brg((float(a['lat']), float(a['lng'])), (float(b['lat']), float(b['lng'])))
        print(i, 'heading', p['heading'], 'tor', round(t), 'odc', round(d, 1), p['shotDate'])
    else:
        print(i, 'brak sąsiadów')
