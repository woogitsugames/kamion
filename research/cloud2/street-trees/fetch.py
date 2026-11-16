#!/usr/bin/env python3
"""Pobiera pliki z manifest.csv (kolumna url_pliku) do files/ (ścieżka z kolumny plik_lokalny) i weryfikuje sha256.
Uruchom: python3 -I fetch.py   (exit 1 przy niezgodności sha256 lub błędzie pobrania pliku o stabilnym sha).
Pomijane: wiersze bez url_pliku (publikacje „tylko cytat”) i ekstrakt OSM PBF (zmienia się codziennie; wyniki w data/osm_*.json).
"""
import csv, hashlib, os, subprocess, sys, time
ROOT = os.path.dirname(os.path.abspath(__file__))
UA = 'research-fetch/1.0 (curl)'
todo = {}
for r in csv.DictReader(open(os.path.join(ROOT, 'manifest.csv'), encoding='utf-8')):
    if r['url_pliku'] and r['plik_lokalny'] and r['sha_stabilny'] == 'tak':
        todo[r['plik_lokalny']] = (r['url_pliku'], r['sha256'])
bad = 0; total = 0
for path, (url, sha) in sorted(todo.items()):
    dst = os.path.join(ROOT, path); os.makedirs(os.path.dirname(dst), exist_ok=True)
    def ok(): return os.path.exists(dst) and hashlib.sha256(open(dst, 'rb').read()).hexdigest() == sha
    for attempt in range(4):
        if ok(): break
        subprocess.run(['curl', '-sSL', '-m', '120', '-A', UA, '-o', dst, url]); time.sleep(1 + 3 * attempt)
    if ok(): total += os.path.getsize(dst); print('OK  ', path)
    else: bad += 1; print('FAIL', path, url)
print(f'{len(todo) - bad}/{len(todo)} plików zgodnych, {total / 1e6:.1f} MB')
sys.exit(1 if bad else 0)
