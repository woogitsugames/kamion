"""Licencja/autor/data/współrzędne z HTML strony pliku Commons (API zwraca 429). Wejście: TSV key<TAB>title. Wyjście JSON."""
import sys, json, re, html, time, urllib.parse
sys.path.insert(0, sys.argv[1])
from httpc import get  # noqa
res = {}
for line in open(sys.argv[2]):
    if not line.strip():
        continue
    key, title = line.strip().split('\t')
    url = 'https://commons.wikimedia.org/wiki/' + urllib.parse.quote(title.replace(' ', '_'))
    try:
        s = get(url, tries=3).decode('utf-8', 'replace')
    except Exception as e:  # noqa
        res[key] = {'title': title, 'page': url, 'error': str(e)}
        continue
    lic = sorted(set(re.findall(r'(CC0|CC BY(?:-SA)? [0-9.]+|Public domain)', s)))
    m = re.search(r'id="fileinfotpl_aut"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>', s, re.S)
    aut = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', m.group(1)))).strip()[:120] if m else ''
    m = re.search(r'id="fileinfotpl_date"[^>]*>.*?</td>\s*<td[^>]*>(.*?)</td>', s, re.S)
    dat = re.sub(r'\s+', ' ', html.unescape(re.sub('<[^>]+>', ' ', m.group(1)))).strip()[:80] if m else ''
    geo = re.search(r'data-lat="([0-9.\-]+)"\s+data-lon="([0-9.\-]+)"', s) or re.search(r'params=([0-9.]+)_N_([0-9.]+)_E', s)
    hd = re.search(r'GPSImgDirection|heading:([0-9.]+)', s)
    res[key] = {'title': title, 'page': url, 'licenses': lic, 'author': aut, 'date': dat,
                'lat': float(geo.group(1)) if geo else None, 'lon': float(geo.group(2)) if geo else None,
                'heading': hd.group(1) if hd and hd.groups() and hd.group(1) else None}
    print(key, res[key], flush=True)
    time.sleep(3)
json.dump(res, open(sys.argv[3], 'w'), ensure_ascii=False, indent=1)
