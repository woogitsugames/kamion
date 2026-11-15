"""Build manifest.csv + files/ for G3 (research/gate3-spots-s21).
Usage: python3 -I tools/build_manifest.py <scratch_g3_dir>
<scratch_g3_dir> holds dl/commons/summary.json, dl/pmx/pmx_summary.json, dl/kv_summary.json, dl/kvseq_*.json, ortho/*.jpg
(downloaded by the fetch steps described in sources.md). Writes files/G3-NNN.jpg (<=1600 px, q82) and manifest.csv."""
import csv, json, math, os, sys, hashlib
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
from rows import ROWS, PTS  # noqa: E402

S = sys.argv[1]
ACCESS = '2026-11-15'
cm = json.load(open(os.path.join(S, 'dl/commons/summary.json')))
pm = json.load(open(os.path.join(S, 'dl/pmx/pmx_summary.json')))
kv = json.load(open(os.path.join(S, 'dl/kv_summary.json')))


def dist(a, b):
    la1, lo1 = a; la2, lo2 = b
    x = (lo2 - lo1) * math.cos(math.radians((la1 + la2) / 2)) * 111320
    y = (la2 - la1) * 110574
    return math.hypot(x, y), math.degrees(math.atan2(x, y)) % 360


def kv_course(seq, idx):
    ph = {int(x['sequenceIndex']): x for x in json.load(open(os.path.join(S, f'dl/kvseq_{seq}.json')))['result']['data']}
    a = ph[idx]
    for j in (idx + 1, idx + 2):
        if j in ph:
            d, c = dist((float(a['lat']), float(a['lng'])), (float(ph[j]['lat']), float(ph[j]['lng'])))
            if d > 1.5:
                return round(c, 1), f'kurs z GPS do klatki {j} ({d:.1f} m)'
    for j in (idx - 1, idx - 2):
        if j in ph:
            d, c = dist((float(ph[j]['lat']), float(ph[j]['lng'])), (float(a['lat']), float(a['lng'])))
            if d > 1.5:
                return round(c, 1), f'kurs z GPS od klatki {j} ({d:.1f} m)'
    return None, ''


def save_img(src, dst):
    if not os.path.isabs(src):
        src = os.path.join(S, src)
    im = Image.open(src).convert('RGB')
    im.thumbnail((1600, 1600))
    im.save(dst, quality=82)
    return hashlib.sha256(open(dst, 'rb').read()).hexdigest()


os.makedirs(os.path.join(OUT, 'files'), exist_ok=True)
cols = ['id', 'punkt', 'kamera_gry', 'kategoria', 'element', 'parametr', 'wartość', 'jednostka', 'lat', 'lon', 'osm_id',
        'kierunek_deg', 'kierunek_status', 'kierunek_metoda', 'odległość_do_punktu_m', 'data_zdjęcia', 'sezon', 'pora_dnia',
        'opis_co_widać', 'url_źródła', 'url_pliku', 'plik_lokalny', 'sha256', 'licencja', 'autor', 'data_dostępu', 'status', 'uwagi']
out = []
for r in ROWS:
    p = PTS[r['p']]
    row = {k: '' for k in cols}
    row.update(id=r['id'], punkt=r['p'], kamera_gry=p[0], element=r['el'], opis_co_widać=r['desc'], uwagi=r.get('note', ''),
               sezon=r.get('season', ''), pora_dnia=r.get('tod', ''), data_dostępu=ACCESS, osm_id=r.get('osm', ''),
               parametr=r.get('param', 'kadr — opis'), wartość=r.get('val', ''), jednostka=r.get('unit', ''))
    src = r['src']
    lat = lon = None
    local = None
    if src.startswith('c:'):
        m = cm[src[2:]]
        cc = m['coords'][0]
        lat, lon = cc['lat'], cc['lon']
        row.update(kategoria='kadr', url_źródła=m['page'], url_pliku=m['url'], licencja=m['license'], autor=m['artist'].strip(),
                   data_zdjęcia=m['date'], status='SOURCED')
        local = m['file']
        row['uwagi'] = (row['uwagi'] + f' Pozycja = geotag Commons (camera); plik pobrany jako miniatura 1920 px: {m["thumburl"]}; sha1 oryginału {m["sha1"]}.').strip()
    elif src.startswith('p:'):
        k = [x for x in pm if x.startswith(src[2:])][0]
        m = pm[k]
        lat, lon = m['lat'], m['lon']
        row.update(kategoria='kadr', url_źródła=f'https://api.panoramax.xyz/#focus=pic&pic={k}', url_pliku=m['url'],
                   licencja=m['license'], autor=', '.join(m['providers']) if isinstance(m['providers'], list) else str(m['providers']),
                   data_zdjęcia=m['datetime'][:19], status='SOURCED')
        row['uwagi'] = (row['uwagi'] + f' Panoramax item {k} (kolekcja {m["collection"]}); view:azimuth={m["azimuth"]}.').strip()
        local = m['file']
    elif src.startswith('k:'):
        m = kv['kv_' + src[2:]]
        lat, lon = m['lat'], m['lon']
        row.update(kategoria='kadr', url_źródła=m['page'], url_pliku=m['url'], licencja='CC BY-SA 4.0', autor=m['user'],
                   data_zdjęcia=m['shot'][:19], status='SOURCED')
        row['uwagi'] = (row['uwagi'] + f' KartaView photo id {m["id"]}, sekw. {m["seq"]}, klatka {m["idx"]}; heading API={m["heading_api"]}.').strip()
        local = m['file']
    elif src.startswith('o:'):
        f = src[2:]
        lat, lon = p[1], p[2]
        row.update(kategoria='ortofoto', url_źródła='https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution',
                   url_pliku='WMS GetMap (zapytanie w sources.md)', licencja='GUGiK — dane otwarte (ortofotomapa, PZGiK)', autor='GUGiK',
                   data_zdjęcia='UNVERIFIED (kompozycja HighResolution)')
        local = os.path.join(S, 'ortho', f)
    elif src == 'osm':
        lat, lon = p[1], p[2]
        row.update(kategoria='osm', url_źródła='https://www.openstreetmap.org/way/' + r['osm'].split(';')[0], licencja='ODbL',
                   autor='OpenStreetMap contributors', url_pliku='https://api.openstreetmap.org/api/0.6/map?bbox=… (sources.md)')
    if 'status' in r:
        row['status'] = r['status']
    row['lat'], row['lon'] = f'{lat:.6f}', f'{lon:.6f}'
    d, _ = dist((lat, lon), (p[1], p[2]))
    row['odległość_do_punktu_m'] = f'{d:.0f}'
    az = r.get('az')
    if az == 'course':
        seq, idx = src[2:].split('_')
        c, meth = kv_course(seq, int(idx))
        row.update(kierunek_deg=c, kierunek_status='ESTIMATED', kierunek_metoda=meth + '; kamera skierowana do przodu (droga na wprost w kadrze)')
    elif isinstance(az, tuple):
        row.update(kierunek_deg=az[0], kierunek_status=az[1], kierunek_metoda=az[2])
    elif row['kategoria'] == 'kadr':
        row.update(kierunek_deg='', kierunek_status='UNVERIFIED', kierunek_metoda='źródło nie podaje kierunku geograficznego albo nie da się go potwierdzić z treści')
    if local:
        dst = os.path.join(OUT, 'files', r['id'] + '.jpg')
        row['sha256'] = save_img(local, dst)
        row['plik_lokalny'] = 'files/' + r['id'] + '.jpg'
    out.append(row)
with open(os.path.join(OUT, 'manifest.csv'), 'w', newline='', encoding='utf-8') as fh:
    w = csv.DictWriter(fh, fieldnames=cols)
    w.writeheader()
    w.writerows(out)
print(len(out), 'rows')
for p_ in 'abcd':
    print(p_, sum(1 for x in out if x['punkt'] == p_ and x['kategoria'] == 'kadr'), 'kadrów')
