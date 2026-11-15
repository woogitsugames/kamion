#!/usr/bin/env python3
"""Pobiera pliki z manifest.csv (url_pliku) do files/ i weryfikuje sha256. Exit != 0 przy niezgodności."""
import csv,hashlib,os,sys,time,urllib.request
D=os.path.dirname(os.path.abspath(__file__)); os.makedirs(f'{D}/files',exist_ok=True); bad=0; tot=0
for r in csv.DictReader(open(f'{D}/manifest.csv',encoding='utf-8')):
    if not r['url_pliku']: continue
    fn=r['uwagi'].split('plik files/')[1].split(';')[0]; p=f'{D}/files/{fn}'
    if not os.path.exists(p):
        for i in range(4):
            try:
                b=urllib.request.urlopen(urllib.request.Request(r['url_pliku'],headers={'User-Agent':'research-client/1.0'}),timeout=120).read(); open(p,'wb').write(b); break
            except Exception as e: print('retry',fn,e); time.sleep(2**i)
    h=hashlib.sha256(open(p,'rb').read()).hexdigest() if os.path.exists(p) else 'MISSING'
    tot+=os.path.getsize(p) if os.path.exists(p) else 0
    ok=h==r['sha256']; bad+=not ok; print(r['id'],fn,'OK' if ok else f'MISMATCH {h}')
print(f'{tot/1e6:.2f} MB, błędów: {bad}'); sys.exit(1 if bad else 0)
