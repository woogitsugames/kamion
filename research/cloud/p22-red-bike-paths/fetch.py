#!/usr/bin/env python3
"""M65 (cloud p22-red-bike-paths): pobiera wszystkie pliki z manifest.csv (kolumny url_pliku, sha256) do files/ i weryfikuje sha256.
Tylko biblioteka standardowa. Uzycie: python3 -I fetch.py [--out files] [--manifest manifest.csv] [--skip-pdf]
Kod wyjscia: 0 = wszystko pobrane i zgodne; 1 = niezgodnosc sha256 lub blad pobierania.
Plik zapisywany jako files/<pierwsze id wiersza>_<sha256[:12]>.<ext>; ten sam plik (ten sam URL) pobierany jest raz.
Serwery: GUGiK WMS (wycinki ortofotomapy; odpowiedz JPEG jest deterministyczna — sprawdzone 2026-11-14), Panoramax, KartaView,
Wikimedia Commons (limit zapytan: przy HTTP 429 skrypt czeka i ponawia), BIP Bialystok, eli.gov.pl."""
import argparse, csv, hashlib, os, sys, time, urllib.error, urllib.request

UA = 'kamion-research/1.0 (open-data reference collection)'

def get(url, tries=5):
    for a in range(tries):
        try:
            rq = urllib.request.Request(url, headers={'User-Agent': UA})
            return urllib.request.urlopen(rq, timeout=180).read()
        except urllib.error.HTTPError as e:
            wait = int(e.headers.get('Retry-After', '0') or 0) if e.code == 429 else 0
            print('  HTTP %d, proba %d/%d' % (e.code, a + 1, tries), file=sys.stderr)
            time.sleep(min(max(wait, 5 * (a + 1)), 660))
        except Exception as e:  # siec
            print('  blad: %s, proba %d/%d' % (e, a + 1, tries), file=sys.stderr)
            time.sleep(5 * (a + 1))
    return None

def main():
    here = os.path.dirname(os.path.abspath(__file__))
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(here, 'files'))
    ap.add_argument('--manifest', default=os.path.join(here, 'manifest.csv'))
    ap.add_argument('--skip-pdf', action='store_true', help='pomin dokumenty PDF (Dz.U. c2 ma ok. 28 MB)')
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    seen = {}; bad = 0; n = 0; total = 0
    with open(a.manifest, encoding='utf-8', newline='') as f:
        rows = [r for r in csv.DictReader(f) if r.get('url_pliku')]
    for r in rows:
        url, sha = r['url_pliku'], r['sha256'].strip().lower()
        if url in seen:
            if seen[url] != sha:
                print('NIEZGODNE sha256 w manifescie dla tego samego URL: %s' % r['id']); bad += 1
            continue
        seen[url] = sha
        ext = '.pdf' if url.lower().split('?')[0].endswith('.pdf') else '.jpg'
        if ext == '.pdf' and a.skip_pdf:
            continue
        path = os.path.join(a.out, '%s_%s%s' % (r['id'], sha[:12], ext))
        if os.path.exists(path):
            data = open(path, 'rb').read()
        else:
            data = get(url)
            if data is None:
                print('BLAD pobierania %s %s' % (r['id'], url)); bad += 1; continue
            with open(path, 'wb') as o:
                o.write(data)
            time.sleep(1.0)
        got = hashlib.sha256(data).hexdigest()
        n += 1; total += len(data)
        if got != sha:
            print('NIEZGODNE sha256 %s: oczekiwano %s, jest %s (%s)' % (r['id'], sha, got, url)); bad += 1
        else:
            print('OK %s %d B' % (r['id'], len(data)))
    print('plikow: %d, bajtow: %d, bledow: %d' % (n, total, bad))
    sys.exit(1 if bad else 0)

if __name__ == '__main__':
    main()
