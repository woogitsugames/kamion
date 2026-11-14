#!/usr/bin/env python3
"""Pobiera pliki z manifest.csv (kolumny url_pliku, sha256) do files/ i weryfikuje sha256.
Tylko biblioteka standardowa. Uruchom: python3 -I fetch.py [katalog_docelowy]
Kod wyjścia != 0 przy niezgodności sumy lub błędzie pobrania.
Kadry: files/<id>.jpg; dokumenty (PDF) – files/<nazwa z URL> (jeden plik na URL, wiele wierszy)."""
import csv, hashlib, os, sys, time, urllib.request, urllib.error

UA = 'research-fetch/1.0 (open-data reference collection)'
HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(HERE, 'files')


def get(url, tries=8):
    wait = 3
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=180) as r:
                return r.read()
        except (urllib.error.URLError, OSError) as e:
            if i == tries - 1:
                raise
            print('  ponawiam (%s), czekam %d s' % (str(e)[:50], wait), file=sys.stderr)
            time.sleep(wait)
            wait = min(wait * 2, 60)


def main():
    os.makedirs(DEST, exist_ok=True)
    with open(os.path.join(HERE, 'manifest.csv'), encoding='utf8', newline='') as f:
        rows = list(csv.DictReader(f))
    todo = {}
    for r in rows:
        url, sha = r['url_pliku'].strip(), r['sha256'].strip()
        if not url:
            continue
        name = (r['id'] + '.jpg') if r['kategoria'] == 'kadr' else url.rsplit('/', 1)[-1]
        if url in todo:
            if todo[url][1] != sha:
                print('BŁĄD: różne sha256 dla tego samego URL:', url); return 2
            continue
        todo[url] = (name, sha)
    bad = 0; total = 0
    for url, (name, sha) in todo.items():
        path = os.path.join(DEST, name)
        if os.path.exists(path):
            data = open(path, 'rb').read()
        else:
            try:
                data = get(url)
            except Exception as e:
                print('BŁĄD pobrania', name, str(e)[:80]); bad += 1; continue
            with open(path, 'wb') as o:
                o.write(data)
            time.sleep(1)
        got = hashlib.sha256(data).hexdigest()
        total += len(data)
        if got != sha:
            print('NIEZGODNE sha256', name, got, '!=', sha); bad += 1
        else:
            print('OK', name, len(data))
    print('plików: %d, bajtów: %d, błędów: %d' % (len(todo), total, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
