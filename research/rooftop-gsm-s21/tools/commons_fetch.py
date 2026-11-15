"""M67-FIX: pobranie kadrów naziemnych z Wikimedia Commons (API + upload.wikimedia.org), z przerwami ≥ 5 s,
generyczny User-Agent, bez obcych CDN. Każda próba (także 429) jest zapisywana w out/commons_log.json.

Uruchom: python3 -I tools/commons_fetch.py tools files/ out/commons_log.json
"""
import sys, os, json, time, hashlib, urllib.parse, urllib.request, datetime
TITLES = [
    'File:Antenna tower in Białystok (Cieszyńska).jpg',
    'File:Antenna tower in Białystok (Kawaleryjska).jpg',
    'File:Waszyngtona 36 Białystok 2.jpg',
    'File:Waszyngtona 36 Białystok 3.jpg',
    'File:Tysiąclecia 10A Białystok 1.jpg',
    'File:Tysiąclecia 10A Białystok 2.jpg',
    'File:Tysiąclecia 10 Białystok 3a.jpg',
    'File:Apartment buildings in Białystok (Waszyngtona).jpg',
    'File:W Białymstoku 008.jpg',
    'File:20191110 114106 Zwierzyniecka Street in Bialystok November 2019.jpg',
    'File:20191111 102206 Zwierzyniecka Street in Białystok.jpg',
    'File:20201102 091949 Dobra Street in Białystok.jpg',
    'File:20200509 155354 Kopernika Street in Białystok May 2020.jpg',
    'File:20200509 155417 Kopernika Street in Białystok May 2020.jpg',
    'File:20200509 155523 Kopernika Street in Białystok May 2020.jpg',
]
UA = 'research-client/1.0 (generic; low-rate)'
OUTD, LOG = sys.argv[2], sys.argv[3]
log = json.load(open(LOG)) if os.path.exists(LOG) else []


def req(url):
    r = urllib.request.Request(url, headers={'User-Agent': UA})
    try:
        with urllib.request.urlopen(r, timeout=120) as f:
            return f.status, f.read()
    except urllib.error.HTTPError as e:
        return e.code, e.read()[:300]
    except Exception as e:  # noqa
        return -1, str(e).encode()[:300]


for t in TITLES:
    import unicodedata; slug = ''.join(c if c.isalnum() else '_' for c in unicodedata.normalize('NFKD', t[5:-4].replace('ł', 'l').replace('Ł', 'L')).encode('ascii', 'ignore').decode())[:60]
    out = os.path.join(OUTD, 'commons_%s.jpg' % slug)
    if os.path.exists(out):
        continue
    q = {'action': 'query', 'titles': t, 'prop': 'imageinfo', 'iiprop': 'url|extmetadata|timestamp|user|size',
         'iiurlwidth': '1280', 'format': 'json'}
    api = 'https://commons.wikimedia.org/w/api.php?' + urllib.parse.urlencode(q)
    st, body = req(api)
    rec = {'title': t, 'ts_utc': datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None).isoformat(timespec='seconds'), 'api_status': st}
    time.sleep(6)
    if st == 200:
        d = json.loads(body)
        pg = list(d['query']['pages'].values())[0]
        if 'imageinfo' not in pg:
            rec['note'] = 'brak pliku (missing)'
        else:
            ii = pg['imageinfo'][0]
            md = ii.get('extmetadata', {})
            rec.update({'thumb': ii.get('thumburl'), 'page': ii.get('descriptionurl'), 'user': ii.get('user'),
                        'licencja': md.get('LicenseShortName', {}).get('value'),
                        'autor': md.get('Artist', {}).get('value', '')[:200],
                        'data_zdjecia': md.get('DateTimeOriginal', {}).get('value', '')[:60],
                        'gps': [md.get('GPSLatitude', {}).get('value'), md.get('GPSLongitude', {}).get('value')],
                        'size': [ii.get('width'), ii.get('height')]})
            st2, img = req(ii['thumburl'])
            rec['img_status'] = st2
            if st2 == 200:
                open(out, 'wb').write(img)
                rec['plik'] = out
                rec['sha256'] = hashlib.sha256(img).hexdigest()
            time.sleep(6)
    else:
        rec['body'] = body[:200].decode('utf-8', 'replace')
    log.append(rec)
    json.dump(log, open(LOG, 'w'), ensure_ascii=False, indent=1)
    print(rec.get('title'), rec.get('api_status'), rec.get('img_status'), rec.get('licencja'), rec.get('data_zdjecia'))
    if st == 429 or rec.get('img_status') == 429:
        print('429 — przerwa 60 s')
        time.sleep(60)
