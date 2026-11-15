"""Lokalizacje UKE w Białymstoku dopasowane do budynków OSM o building:levels >= 10 (ulica + numer) → kandydaci na stacje dachowe."""
import sys, openpyxl, json, re, unicodedata
files = sys.argv[1].split(',')
tall = json.load(open(sys.argv[2]))


def norm(s):
    s = unicodedata.normalize('NFKD', s.lower())
    return ''.join(c for c in s if not unicodedata.combining(c)).replace('ł', 'l')


locs = {}
ops = {}
for f in files:
    for r in openpyxl.load_workbook(f, read_only=True).active.iter_rows(values_only=True):
        if r and r[6] == 'Białystok':
            ops.setdefault(r[0], 'ABCDEFG'[len(ops)])
            locs.setdefault(str(r[7]), set()).add((ops[r[0]], f.split('uke_')[-1][:-5], r[4], r[5]))
res = []
for t in tall:
    st = t['addr'].rsplit(' ', 1)
    if len(st) < 2 or not st[0].strip():
        continue
    last = norm(st[0].split()[-1]); num = norm(st[1])
    for loc, v in locs.items():
        nl = norm(loc)
        if re.search(r'\b' + re.escape(last) + r'\b\s+' + re.escape(num) + r'\b', nl):
            res.append({'osm_way': t['way'], 'levels': t['levels'], 'height': t['height'], 'addr': t['addr'], 'uke_loc': loc,
                        'operators': sorted({x[0] for x in v}), 'bands': sorted({x[1] for x in v}), 'uke_coords': sorted({(x[2], x[3]) for x in v})[:2],
                        'lat': t['lat'], 'lon': t['lon']})
json.dump(res, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
for r in res:
    print(r['osm_way'], r['levels'], r['height'], r['addr'], '|', r['uke_loc'], r['operators'], r['bands'], '%.6f,%.6f' % (r['lat'], r['lon']))
print(len(res), 'dopasowań z', len(locs), 'lokalizacji UKE')
