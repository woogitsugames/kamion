"""Zapis metadanych obejrzanych referencji; bez zapytań sieciowych."""
import csv, hashlib, json
from pathlib import Path
from PIL import Image

base = Path(__file__).resolve().parents[1]
worktree = base.parents[3]
meta = json.loads((base/'data/candidates-imageinfo.json').read_text(encoding='utf-8'))
pages = {p['title']:p['imageinfo'][0] for p in meta['query']['pages'].values()}
items = [
('03R2-001','File:Dom pogrzebowy w Knyszynie.jpg','Jasne ściany, szary cokół i podwyższony parter; szary dwuspadowy dach z profilowanymi rzędami i dwoma widocznymi ceglanymi kominami. Podniesiony podest, płytkie zadaszenie, schody i metalowe pochwyty. Chodnik szaro-czerwony, trawa, słupy i przewody.','Wariant niskiej fasady i wejścia na podniesionym podeście; otoczenie chodnika.','Metadane wskazują Rynek; numer i położenie UNVERIFIED. Przebieg DK65 nieustalony.'),
('03R2-002','File:Knyszyn Kościelna 2.jpg','Jasnoniebieska fasada z jasnymi ramami okien, czerwonymi obróbkami i ciemnym czerwonobrązowym cokołem. Jasnoszare połacie po bokach podniesionej części z małymi otworami na różnych wysokościach. Większe okno z białą kratą, ogrodzenie prętowe i niska niebieska dobudówka.','Zróżnicowana bryła fasady i kolorystyka; nie upraszczać do dwóch pełnych kondygnacji.','Adres z nazwy pliku UNVERIFIED; liczba pełnych kondygnacji, materiał pokrycia i metryka UNVERIFIED.'),
('03R2-003','File:Knyszyn Kościelna 42.jpg','Biała tabliczka z ciemnozielonym numerem 42 i częściowo zasłoniętą nazwą ulicy, widoczna końcówka OŚCIELNA. Jasnozielony ziarnisty tynk i pnącze. Nie widać całej fasady ani dachu.','Odmienny biało-zielony wariant oznaczenia numeru domu; detal tynku.','Numer 42 odczytany z obrazu; początek nazwy zasłonięty. Pełna nazwa Kościelna z metadanych, pozycja UNVERIFIED.')]
headers=['id','plik_lub_url','źródło','autor','licencja','data zdjęcia','współrzędne','kierunek patrzenia','CO WIDAĆ','do czego w grze','rodzaj rekordu','status','ograniczenia','sha256']
rows=[]
reviews=[]
k1path=worktree/'research/dk65-knyszyn-refs/manifest.csv'
with k1path.open(encoding='utf-8-sig',newline='') as f: k1=list(csv.DictReader(f))
for ident,title,obs,use,limits in items:
    info=pages[title]; ext=info['extmetadata']; local=base/'files'/f'{ident}.jpg'
    digest=hashlib.sha256(local.read_bytes()).hexdigest()
    size=Image.open(local).size
    assert max(size)<=800
    url=info['descriptionurl']
    dup=[r['id'] for r in k1 if r['url_źródła']==url]
    assert not dup
    rows.append([ident,'files/'+local.name,url,'Henryk Borawski','CC BY-SA 3.0; https://creativecommons.org/licenses/by-sa/3.0/',ext['DateTimeOriginal']['value'],'UNVERIFIED — brak w metadanych','UNVERIFIED — brak azymutu geograficznego/magnetycznego',obs,use,'NOWE ŹRÓDŁO względem manifestu K1','SOURCED [obraz i metadane Commons]',limits+' Stan z 2012 r.; aktualność 2026 UNVERIFIED.',digest])
    reviews.append({'id':ident,'individually_viewed':True,'method':'lokalne view_image, pełny kadr miniatury','size_px':size,'sha256':digest,'source_url':url,'k1_exact_source_url_matches':dup,'new_source':True,'source_original_sha1':info['sha1']})
for ident,key,obs,use in [
 ('03R2-R01','K1-P06.jpg','Po prawej drewniana fasada o żółtobrązowych poziomych deskach niżej i ciemnych deskach w podniesionej partii dachu, jasne ramy okien, niski cokół i brązowy płot. Naprzeciw jasnoszara ceglana fasada z wyższym prostokątnym środkowym parapetem/szczytem. Stopnie i słupy zajmują część chodnika; mały ciemny słupek z czerwonym bocznym króćcem wygląda na hydrant (typ UNVERIFIED).','Zróżnicowanie fasad i ciasnego chodnika; nie przypisywać Grodzieńskiej automatycznie do DK65.'),
 ('03R2-R02','K1-P22.jpg','Historyczny wlot drogi z podwójną białą linią osi i liniami krawędziowymi. Czerwone bariery piesze z zaokrąglonymi górnymi narożnikami, szaro-czerwona kostka, niska zieleń w dwóch odcieniach i pasy przejścia po prawej. Drobnych liczb na drogowskazie nie odczytano.','Historyczna forma barier i chodnika; zdjęcie 2009 nie potwierdza dzisiejszego układu ronda.')]:
    old=next(r for r in k1 if r['plik_lokalny'].endswith(key))
    local=worktree/'research/dk65-knyszyn-refs'/old['plik_lokalny']
    digest=hashlib.sha256(local.read_bytes()).hexdigest()
    rows.append([ident,'../../../dk65-knyszyn-refs/'+old['plik_lokalny'],old['url_źródła'],old['autor'],old['licencja'],old['data_zdjęcia'],'UNVERIFIED w tym przeglądzie','UNVERIFIED — brak odczytanego azymutu',obs,use,'PONOWNE OGLĘDZINY istniejącego '+old['id'],'SOURCED [ponownie obejrzany obraz K1]','Bez kopii i nowego pobrania. Współczesna aktualność 2026 UNVERIFIED; gatunki roślin i wymiary UNVERIFIED.',digest])
    reviews.append({'id':ident,'individually_viewed':True,'method':'lokalne view_image istniejącego pliku K1','existing_k1_id':old['id'],'existing_k1_file':old['plik_lokalny'],'new_source':False,'copied':False,'sha256':digest})
with (base/'manifest.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f); writer.writerow(headers);writer.writerows(rows)
(base/'data/review.json').write_text(json.dumps({'reviews':reviews,'counts':{'new_downloaded_photos':3,'new_facade_photos':2,'new_address_detail':1,'k1_rereviews':2,'new_dk65_street_photos':0,'link_only_photos':0},'deduplication':'Dokładne URL nowych źródeł nie występują w manifeście K1. Ponowne oględziny osobno; brak twierdzenia o unikalności obiektu w przestrzeni.','owner_photos_used':False},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
readme=base/'README.md'
readme.write_text(readme.read_text(encoding='utf-8').replace('z metalowym pochwytami','z metalowymi pochwytami'),encoding='utf-8')
print(json.dumps({'rows':len(rows),'new_photos':3,'rereviews':2,'all_thumbnails_le_800':True},ensure_ascii=False))
