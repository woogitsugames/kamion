"""Write audit_20_percent.json: sample, URL checks, results per row (results dict passed as JSON file)."""
import sys, os, csv, json, random, re, time, urllib.request, urllib.error
OUT = sys.argv[1]
res = json.load(open(sys.argv[2]))
seed = int(sys.argv[3])
prefix = sys.argv[4]
meta = json.load(open(sys.argv[5])) if len(sys.argv) > 5 else {}
rows = list(csv.DictReader(open(os.path.join(OUT, 'manifest.csv'), encoding='utf-8')))
ids = [r['id'] for r in rows]
k = -(-len(ids) // 5)
sample = sorted(random.Random(seed).sample(ids, k))


def http(u):
    if not u.startswith('http'):
        return None
    u = u.split(' ')[0].split(';')[0]
    for i in range(6):
        try:
            req = urllib.request.Request(u, headers={'User-Agent': 'research-client/1.0 (generic)', 'Range': 'bytes=0-1023'})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.status
        except urllib.error.HTTPError as e:
            if e.code == 429:
                time.sleep(20 * (i + 1)); continue
            return e.code
        except Exception as e:
            time.sleep(5)
    return 'timeout'


out = []
for r in rows:
    if r['id'] not in sample:
        continue
    o = {'id': r['id'], 'kategoria': r.get('kategoria', r.get('obiekt', '')), 'element': r['element'], 'parametr': r['parametr']}
    urls = [u for u in re.findall(r'https?://[^\s;,)]+', r['url_źródła'])][:2]
    if r.get('url_pliku', '').startswith('http'):
        urls.append(r['url_pliku'])
    o['http'] = {u[:120]: http(u) for u in urls}
    o.update(res.get(r['id'], {'sprawdzenie': 'BRAK — uzupełnić', 'wynik': '?'}))
    out.append(o)
summary = {'seed': seed, 'metoda_losowania': f'random.Random({seed}).sample(lista id z manifest.csv, ceil(n/5))', 'n_wierszy': len(ids), 'n_próby': k,
           'próba': sample, 'PASS': sum(1 for o in out if o['wynik'] == 'PASS'), 'FIX': sum(1 for o in out if o['wynik'].startswith('FIX')), **meta, 'wiersze': out}
json.dump(summary, open(os.path.join(OUT, 'audit_20_percent.json'), 'w'), ensure_ascii=False, indent=1)
print(summary['n_próby'], summary['PASS'], summary['FIX'])
for o in out:
    print(o['id'], o['wynik'], o['http'])
