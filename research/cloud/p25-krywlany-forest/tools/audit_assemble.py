import csv,json,sys,urllib.request,urllib.error,time,re,collections
D=sys.argv[1]; UA="kamion-research/1.0 (open-data reference collection)"
rows={r['id']:r for r in csv.DictReader(open(D+'/manifest.csv',encoding='utf-8'))}
ids=json.load(open('audit_ids.json')); data={o['id']:o for o in json.load(open('audit_data.json'))}
cache={}
def st(u):
    if u in cache: return cache[u]
    c=None
    for t in range(3):
        try:
            r=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':UA,'Range':'bytes=0-2000'}),timeout=60); c=r.status; break
        except urllib.error.HTTPError as e:
            c=e.code
            if c==429: time.sleep(8); continue
            break
        except Exception as e: c=repr(e)[:60]; time.sleep(2)
    cache[u]=c; time.sleep(0.5); return c
FR={'PX24':'zgodny','PX30':'POPRAWKA: doprecyzowano znak (żółty trójkąt z jeleniem A-18b z tabliczką zamiast „znak ostrzegawczy”)','PX35':'POPRAWKA: dodano świerk w drugim piętrze (widoczny na wycinku z pełnej rozdzielczości)','PX37':'zgodny',
'C149115308':'POPRAWKA: dopisano dwa jasne auta z prawej','C149115310':'zgodny','C151034273':'zgodny','C151034274':'zgodny','C151034276':'zgodny (wycinek 3× znaku: A-18b + tabliczka „1,0 km” potwierdzone)','C151034277':'zgodny',
'C151034278':'POPRAWKA: gatunek krzewu na pierwszym planie zmieniono z „leszczyna (ESTIMATED)” na „leszczyna lub lipa — UNVERIFIED”','C151034280':'zgodny','C151034281':'zgodny','C151034282':'zgodny','C151034286':'zgodny',
'C151034287':'POPRAWKA: skrajne drzewo po prawej ma liście jak dąb (nie klon) — zmieniono opis i pole gatunku','C93999621':'zgodny','C94000148':'zgodny','C94000344':'zgodny'}
out=[]
for i in ids:
    r=rows[i]; o=dict(id=i,kategoria=r['kategoria'],element=r['element'][:90],parametr=r['parametr'][:80])
    o['link_http']=st(r['url_źródła'])
    k=r['wartość'] if r['kategoria']=='kadr' else (re.search(r'\((PX\d+|C\d+)\)',r['uwagi']).group(1) if 'kadr C68' in r['uwagi'] else None)
    if k:
        o['kadr']=k; o['ponowne_obejrzenie']='Read: '+('wycinek z pełnej rozdzielczości' if k in('PX24','PX30','PX35','PX37','C151034276','C151034287') else 'arkusz kontrolny (kafel 760 px)')+' — '+FR[k]
    d=data.get(i,{})
    for kk in ('sprawdzenie','http','odczyt','punkt_EPSG2180','nmpt_2025_wcs_min_max','nmt_wcs_min_max','chm_bezlistny_z_kafli','chm_ulistniony_z_arkusza'):
        if kk in d and not (k and kk=='sprawdzenie'): o[kk]=d[kk]
    nm_fix=('NumDaneWys' in r['url_źródła'])
    o['wynik']='POPRAWIONO' if (k and 'POPRAWKA' in FR[k]) else ('POPRAWIONO (url_źródła)' if nm_fix else 'PASS')
    out.append(o)
summ=dict(seed=20261114,metoda="random.Random(20261114).sample(range(277), 56) po indeksach wierszy manifestu (kolejność z pliku); odtworzenie: tools/audit_sample.py",wierszy_manifestu=len(rows),wylosowano=len(ids),udzial=round(len(ids)/len(rows),3),
  kadry_ponownie_obejrzane=sorted(set(o['kadr'] for o in out if 'kadr' in o)),
  wiersze_poprawione_opis_kadru=[o['id'] for o in out if o['wynik']=='POPRAWIONO'],
  wiersze_poprawione_url=[o['id'] for o in out if o['wynik'].endswith('(url_źródła)')],
  lista_zmian=[f"{k}: {v}" for k,v in FR.items() if 'POPRAWKA' in v]+["url_źródła wierszy CHM (wysokość/krawędź/obszar-krawędź, łącznie 109 wierszy w manifeście, 24 w próbie): wskazywał katalog opendata (HTTP 404) → zmieniono na URL arkusza NMPT N-34-107-C-b-4-3 (HTTP 206); pełna lista arkuszy w sources.md","url_źródła wierszy BDL poza LP: usunięto dopisek tekstowy z pola URL (przeniesiony do uwag)"],
  bdl_ponownie_pobrane=sum(1 for o in out if str(o.get('sprawdzenie','')).startswith('ponowne pobranie opisu')),
  nmpt_ponowne_odczyty=sum(1 for o in out if 'nmpt_2025_wcs_min_max' in o),
  linki_po_poprawce=dict(collections.Counter(str(o['link_http']) for o in out)),
  uwagi=["Ponowny odczyt NMPT: stacja środkowa po tej samej stronie obiektu (dopasowanie po drodze i stronie, nie po wydzieleniu) — C68-075 i C68-079 trafiły w ten sam punkt.","Kod 206 = OK (zapytanie z nagłówkiem Range); 429 przy Commons = limit zapytań Wikimedia dla wspólnego adresu wyjściowego, nie błąd adresu."])
json.dump(dict(podsumowanie=summ,wiersze=out),open(D+'/audit_20_percent.json','w'),ensure_ascii=False,indent=1)
print(summ['linki_po_poprawce'],summ['wiersze_poprawione_opis_kadru'],len(summ['wiersze_poprawione_url']),summ['bdl_ponownie_pobrane'],summ['nmpt_ponowne_odczyty'],len(summ['kadry_ponownie_obejrzane']))
