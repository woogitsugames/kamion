"""Read-only skyline probe (ADR 0141): for an SBS camera, list what closes the horizon per azimuth bin -
region trees (instances_*.json), region buildings (buildings.geojson) - as elevation angles of their tops.
Usage: skyline_probe.py <camera-id-substring> [bin_deg]"""
import json, math, sys, glob, os
R = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
reg = 'bialystok-industrial-c'
cams = json.load(open(f'{R}/Data/Regions/{reg}/sbs_cameras.json', encoding='utf-8'))['cameras']
cam = next(c for c in cams if sys.argv[1] in c['id'])
binw = float(sys.argv[2]) if len(sys.argv) > 2 else 4.0
pe, pn, pu = cam['pos']; le, ln, lu = cam['look_at']
head = math.atan2(le - pe, ln - pn)
OX, OY, OZ = 777995.0, 596223.0, 131.14
def rel(e, n):
    dx, dy = e - pe, n - pn
    d = math.hypot(dx, dy)
    a = math.degrees((math.atan2(dx, dy) - head + math.pi) % (2 * math.pi) - math.pi)
    return d, a
bins = {}
def put(kind, e, n, top, label):
    d, a = rel(e, n)
    if abs(a) > 45 or d < 5: return
    el = math.degrees(math.atan2(top - pu, d))
    k = (kind, int(math.floor(a / binw)))
    if k not in bins or el > bins[k][0]: bins[k] = (el, d, label)
for f in glob.glob(f'{R}/Data/raw/derived/{reg}/world/instances_*.json'):
    for i in json.load(open(f))['instances']:
        if i.get('fk') or str(i.get('p', '')).startswith('tree'):
            put('tree', i['e'], i['n'], i['z'] + i.get('h', 0), f"{i.get('p')} h{i.get('h')} z{i['z']} {i.get('src','')[:44]}")
for f in json.load(open(f'{R}/Data/Regions/{reg}/buildings.geojson', encoding='utf-8'))['features']:
    p = f['properties']; g = f['geometry']['coordinates'][0][0]
    e = sum(x for x, _ in g) / len(g) - OX; n = sum(y for _, y in g) / len(g) - OY
    if p.get('height_m') is None or p.get('ground_z_evrf2007') is None: continue
    put('bldg', e, n, p['ground_z_evrf2007'] + p['height_m'], f"h{p['height_m']} {p.get('function')}")
print(cam['id'], 'pos', cam['pos'], 'heading', round(math.degrees(head) % 360, 1))
for b in sorted({k[1] for k in bins}):
    t = bins.get(('tree', b)); bl = bins.get(('bldg', b))
    print(f"{b*binw:+6.0f}..{(b+1)*binw:+4.0f}  tree " + (f"el {t[0]:+5.1f} d {t[1]:5.0f} {t[2]}" if t else '-').ljust(96) + ' | bldg ' + (f"el {bl[0]:+5.1f} d {bl[1]:5.0f} {bl[2]}" if bl else '-'))
