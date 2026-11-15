#!/usr/bin/env python3
"""Sklada manifest.csv z danych w data/ + opisow kadrow (obejrzanych) + cytatow zrodel."""
import csv, json, hashlib, pathlib, random
ROOT = pathlib.Path(__file__).resolve().parent.parent
COLS = "id,kategoria,przedmiot,wartość,jednostka,status,metoda,cytat,url_źródła,url_pliku,licencja,autor,data_dostępu,sha256,lat,lon,kierunek_deg,opis_co_widać,duplikat_sha256,uwagi,obszar,osm_way".split(",")
rows = []
def add(**k):
    r = {c: "" for c in COLS}; r.update(k); r["id"] = f"R4-{len(rows)+1:03d}"; r["data_dostępu"] = "2026-11-14"; rows.append(r)
def sha(p):
    p = ROOT / "files" / p; return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else ""
PN = {"6fc62548": "Spod estakady: podpory betonowe w kolorze piaskowożółtym, estakada z zielonym pasem gzymsu i barierą. W prześwicie dom jednorodzinny: parter + piętro + poddasze, jasna (biała) elewacja, stromy ciemny dach dwuspadowy, balkon na piętrze. Przed nim ekran akustyczny z przezroczystych tafli na zielonych słupkach. Za nim las; po prawej w głębi budynek z ciemną, przeszkloną elewacją.",
 "844e35c7": "Wlot na rondo z sygnalizacją; po lewej estakada na żółtawych podporach z przezroczystymi ekranami; po prawej ekran akustyczny (ciemny dół, przezroczysta góra). W oddali biało-czerwone kominy i niska zabudowa z czerwonym dachem. Autobus miejski. Elewacji przy jezdni brak.",
 "03ec4841": "Jezdnia wzdłuż estakady (po lewej, przezroczyste ekrany z zielonymi słupkami); pod estakadą widać niski jasny budynek; po prawej ekran akustyczny; w oddali biało-czerwony komin. Autobus miejski.",
 "6248550a": "Łącznica przy węźle: bariery stalowe, po prawej ekran akustyczny (ciemny dół, przezroczysta góra), w głębi wiadukt z tablicami; las na horyzoncie. Budynków w kadrze nie widać.",
 "a228a704": "Droga dwujezdniowa; po prawej ekran akustyczny: jasny betonowy cokół, ciemne szarozielone panele ryflowane, wyżej przezroczyste tafle, zielone słupki. Po lewej za ekranem niski budynek z płaskim dachem i ciemnym pasem attyki. Bramownica nad jezdnią, las.",
 "128187d5": "Droga dwujezdniowa w lesie sosnowym, bariery, latarnie, linie napowietrzne; w oddali ciężarówka. Budynków w kadrze nie widać.",
 "3717771d": "Przejście dla pieszych przed estakadą z przezroczystymi ekranami na ciemnych słupkach; podpory w kolorze piaskowym; młode drzewa. Elewacji budynków nie widać."}
pn = {f["id"][:8]: f for f in json.load(open(ROOT / "data/panoramax_trasa_c.json"))["result"]["features"]}
for k, d in PN.items():
    f = pn[k]; lon, lat = f["geometry"]["coordinates"]
    add(kategoria="kadr", przedmiot="Panoramax, trasa C (rejon ronda Putry / Maczka)", status="SOURCED", metoda="obejrzany plik sd.jpg zmniejszony do 960 px; azymut z API view:azimuth",
        url_źródła=f"https://api.panoramax.xyz/api/collections/{f['collection']}/items/{f['id']}", url_pliku=f["assets"]["sd"]["href"], licencja="CC BY-SA 4.0 (referencja, nie tekstura)", autor="stanton",
        sha256=sha(f"panoramax/{f['id']}.jpg"), lat=f"{lat:.6f}", lon=f"{lon:.6f}", kierunek_deg=f["properties"]["view:azimuth"], opis_co_widać=d, obszar="trasa_c",
        uwagi=f"data zdjęcia {f['properties']['datetime'][:10]}; kamera z samochodu; budynek OSM nieprzypisany", osm_way="")
KV = {"1326673481": "Jezdnia z dwoma pasami; po prawej ekran akustyczny z poziomych ryflowanych paneli w kolorze jasnoszarym z zielonym pasem, na betonowym cokole; w głębi niebieska łukowa kładka; po lewej biało-czerwony komin i ciemny ekran. Elewacji budynków nie widać.",
 "1326673549": "Jezdnia, zielona tablica kierunkowa, słup kratowy linii wysokiego napięcia; po lewej za pomarańczowym ogrodzeniem walcowy zbiornik w poziome biało-niebieskie pasy. Budynków przy jezdni nie widać.",
 "1326673601": "Najazd na wiadukt; po prawej za drzewami budynek kilkukondygnacyjny (około 4 rzędów okien, niepewne przy tej rozdzielczości) o beżowożółtej elewacji z poziomymi pasami okien i płaskim dachem z antenami.",
 "1326673629": "Na wiadukcie: bariery stalowe; daleko po lewej wysoki jasny budynek i żuraw budowlany; po prawej w dali niskie obiekty w zieleni i bieli (nierozpoznane). Brak elewacji z bliska.",
 "1326673681": "Jezdnia trzypasowa; po prawej rząd billboardów i pylonów reklamowych, pylon stacji paliw, niskie pawilony handlowe; po lewej drzewa i bramownica. Wysokich budynków brak.",
 "1326673753": "Po lewej przeszklony niski obiekt (szklarnie) i salon samochodowy z flagami: niski pawilon biało-niebieski z czerwonym akcentem; po prawej niskie pawilony w bieli i błękicie z płaskimi dachami. Zabudowa 1–2-kondygnacyjna odsunięta od jezdni.",
 "1326673809": "Po obu stronach ekrany akustyczne (po prawej betonowy dół i przezroczyste tafle na zielonych słupkach), słup wysokiego napięcia, znak rozwidlenia. Budynków nie widać.",
 "1326673897": "Jezdnia w lesie, ekrany akustyczne po obu stronach; po prawej ciężarówka z białą naczepą skrzyniową, przed nią druga. Budynków nie widać.",
 "1326673913": "Las po obu stronach, bramownica z zieloną tablicą, tabliczki numerów dróg, ekran po lewej. Budynków nie widać."}
kv = {p["id"]: p for p in json.load(open(ROOT / "data/kartaview_trasa_c.json"))["photos"]}
for k, d in KV.items():
    p = kv[k]
    add(kategoria="kadr", przedmiot="KartaView sekw. 3686129, ul. gen. Andersa → Maczka (kierunek NW)", status="SOURCED", metoda="obejrzany plik proc zmniejszony do 960 px; azymut = pole heading z API 2.0",
        url_źródła=f"https://kartaview.org/details/{p['sequenceId']}/{p['sequenceIndex']}", url_pliku=p["fileurlProc"], licencja="CC BY-SA 4.0 (referencja, nie tekstura)", autor="użytkownik KartaView (pole API bez nazwy)",
        sha256=sha(f"kartaview/kv_{k}.jpg"), lat=f"{float(p['lat']):.6f}", lon=f"{float(p['lng']):.6f}", kierunek_deg=p["heading"], opis_co_widać=d, obszar="trasa_c",
        uwagi=f"data zdjęcia {p['shotDate'][:10]}; kamera z samochodu; budynek OSM nieprzypisany")
for r in csv.DictReader(open(ROOT / "data/nmpt_sample.csv")):
    cmp_ = f"; LoD1 2024 = {r['lod1_2024']} m (różnica {float(r['h_med'])-float(r['lod1_2024']):+.2f} m)" if r["lod1_2024"] else ""
    add(kategoria="wysokość_budynku", przedmiot=f"{r['grupa']} — OSM building={r['building']}; {r['addr'] or 'bez adresu w OSM'}", wartość=r["h_med"], jednostka="m", status="ESTIMATED",
        metoda="GUGiK WCS: mediana NMPT (0,5 m) w obrysie OSM zwężonym o 1 m minus p10 NMT w pierścieniu 1–4 m; tools/nmpt_heights.py",
        url_źródła="https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel", licencja="GUGiK dane publiczne (WCS: Fees none, AccessConstraints none); obrys OSM ODbL",
        autor="GUGiK / OpenStreetMap contributors", lat=r["lat"], lon=r["lon"], obszar=r["area"], osm_way=r["way"],
        uwagi=f"h_p95={r['h_p95']} m (kalenica/attyka/nadbudówki); rzut {r['dl_m']}×{r['szer_m']} m, {r['area_m2']} m²; building:levels OSM={r['levels_osm'] or 'brak'}; kondygnacje BDOT={r['bdot_storeys'] or 'brak'}{cmp_}")
W = "https://pl.wikipedia.org/w/index.php?title=Technologia_wielkop%C5%82ytowa&oldid=79506745"
def src(kat, prz, val, unit, cyt, url, lic, aut, uw="", status="SOURCED"):
    add(kategoria=kat, przedmiot=prz, wartość=val, jednostka=unit, status=status, metoda="cytat ze źródła otwartego 2026-11-14", cytat=cyt, url_źródła=url, licencja=lic, autor=aut, uwagi=uw)
src("wielka_płyta", "OW-T: siatka konstrukcyjna", "540×480; 540×540; 270×480", "cm", "System OW-T oparto na siatce o wymiarach 540 × 480 cm (jako jednostka podstawowa) z uzupełnieniem 540 × 540 cm dla powierzchni mieszkalnych, i 270 × 480 dla traktów komunikacyjnych w budynkach 5-kondygnacyjnych", W, "CC BY-SA 4.0", "Wikipedia PL, sekcja OW-T", "system potwierdzony dla Białegostoku w research/mistral/p3-buildings-2 (Białostoczek OWT-67/OWT-75)")
src("wielka_płyta", "OWT-67 → OWT-75: wysokość kondygnacji", "270 → 280", "cm", "W 1975 opracowano rozwiązanie oznaczone symbolem OWT-75 zwiększając nie tylko metraż typowych mieszkań, ale podniesiono wysokość kondygnacji z 270 do 280 cm.", W, "CC BY-SA 4.0", "Wikipedia PL, sekcja OW-T")
src("wielka_płyta", "wysokość kondygnacji 280 cm = brutto", "280", "cm", "Często podawana w źródłach wysokość kondygnacji równa 280 cm jest wartością brutto, czyli z uwzględnieniem grubości prefabrykowanego stropu.", W, "CC BY-SA 4.0", "Wikipedia PL")
src("wielka_płyta", "W-70: rozstawy ścian nośnych", "240; 360; 480; 600", "cm", "Typowe rozpiętości stropów (rozstawy ścian nośnych) wynosiły: 240, 360, 480 i 600 cm.", W, "CC BY-SA 4.0", "Wikipedia PL, sekcja W-70", "użycie W-70 w Białymstoku: UNVERIFIED (brak źródła w repo i w tym pakiecie)")
src("wielka_płyta", "W-70: wysokość kondygnacji mieszkalnej", "280", "cm", "Wysokość kondygnacji mieszkalnych – 280 cm.", W, "CC BY-SA 4.0", "Wikipedia PL, sekcja W-70", "jw. — Białystok UNVERIFIED")
src("wielka_płyta", "Wk-70: dodatkowa wysokość kondygnacji (szkoły, hotele)", "330", "cm", "W odmianie Wk-70 wprowadzono dodatkową rozpiętość stropów – 300 cm, dodatkową wysokość kondygnacji – 330 cm", W, "CC BY-SA 4.0", "Wikipedia PL, sekcja W-70", "Białystok UNVERIFIED")
src("wielka_płyta", "system szczeciński: siatka", "480×480; 480×240", "cm", "Podstawowe jednostki oparto na siatce 480 × 480 cm i 480 × 240 cm", W, "CC BY-SA 4.0", "Wikipedia PL, sekcja „Szczeciński”", "Białystok UNVERIFIED")
src("wielka_płyta", "OWT-67: wysokość kondygnacji nadziemnej (brutto)", "270", "cm", "nadziemna: 270 cm", "https://pl.wikipedia.org/w/index.php?title=OWT-67&oldid=72638965", "CC BY-SA 4.0", "Wikipedia PL „OWT-67”, sekcja Wysokość kondygnacji (brutto)")
BP = "https://bp2.eu/wp-content/uploads/2023/12/BP2-katalog-techniczny-CORE-PIR-PL.pdf"
src("hala_okładzina", "płyta warstwowa ścienna PIR: szerokość efektywna (moduł podziału elewacji)", "1150 (1000 niestandardowo)", "mm", "Szerokość efektywna [mm] 1150, 1000*", BP, "dokumentacja producenta (dane techniczne)", "producent płyt warstwowych", "tabela parametrów płyty ściennej z mocowaniem widocznym, ok. s. 4–5 PDF (wiersz 171 pdftotext)")
src("hala_okładzina", "płyta warstwowa ścienna PIR: długość maksymalna", "15,0", "m", "Max. długość płyty [mb] 15,0", BP, "dokumentacja producenta (dane techniczne)", "producent płyt warstwowych", "przy układzie poziomym = maks. rozstaw styków pionowych")
src("hala_okładzina", "płyta warstwowa: szerokość efektywna, mocowanie ukryte", "1050", "mm", "Szerokość efektywna [mm] 1050", BP, "dokumentacja producenta (dane techniczne)", "producent płyt warstwowych")
RU = "https://www.ruukki.com/roofing/products/roofing-sheets/roofing-sheets-detail/profiled-sheet-t35"
src("hala_okładzina", "blacha trapezowa T35: wysokość profilu", "34", "mm", "Profile Height 34 mm", RU, "dokumentacja producenta (dane techniczne)", "producent blach")
src("hala_okładzina", "blacha trapezowa T35: szerokość efektywna arkusza", "1035", "mm", "Effective width 1035 mm", RU, "dokumentacja producenta (dane techniczne)", "producent blach")
src("hala_okładzina", "blacha trapezowa T35: długość maksymalna arkusza", "12000", "mm", "Maximum length 12000 mm", RU, "dokumentacja producenta (dane techniczne)", "producent blach")
DH = "https://m.budujemydom.pl/files/anq/15191-przemyslowe-bramy-segmentowe-doorhan-2016-pol-web.pdf"
src("hala_brama", "brama segmentowa przemysłowa: zakres wysokości otworu", "2000–8000", "mm", "Wysokość otworu – od 2000 do 8000 mm.", DH, "dokumentacja producenta (dane techniczne)", "producent bram")
src("hala_brama", "brama segmentowa przemysłowa: zakres szerokości otworu", "1700–8000", "mm", "Szerokość otworu – od 1700 do 8000 mm.", DH, "dokumentacja producenta (dane techniczne)", "producent bram")
src("hala_brama", "sekcja przeszklona bramy: wysokość", "370–650", "mm", "Wysokość — od 370 do 650 mm", DH, "dokumentacja producenta (dane techniczne)", "producent bram", "sekcja „Wymiary oszklonych sekcji”")
AA = "https://www.assaabloyentrance.com/master-blueprint/pl/product-assets/loading-dock-equipment/oh1042p/downloads/product-datasheet/Assa%20Abloy%20OH1042P%20Overhead%20sectional%20door.pdf"
src("hala_brama", "brama segmentowa: wysokość sekcji (rytm poziomych podziałów)", "545", "mm", "Wysokość sekcji: 545 mm", AA, "dokumentacja producenta (dane techniczne)", "producent bram", "p. 1.2.1 karty")
src("hala_brama", "brama segmentowa: rozmiar maksymalny", "8000×6000", "mm", "Rozmiar maks.: (W x H) 8000 x 6000 mm (większe rozmiary na życzenie)", AA, "dokumentacja producenta (dane techniczne)", "producent bram")
add(kategoria="hala_brama", przedmiot="brama segmentowa wjazdowa — wymiar typowy dla generatora", wartość="4000×4500", jednostka="mm", status="WORKING_VALUE", metoda="wartość z zadania; mieści się w zakresach SOURCED (R4 wiersze bram), brak źródła na „typową”", uwagi="do weryfikacji pomiarem na zdjęciach hal w Dojlidach (nie wykonano)")
DK = "https://m.budujemydom.pl/files/ghr/15193-technika-przeladunkowa-doorhan-2016-pol-web.pdf"
src("hala_dok", "śluza uszczelniająca doku: szerokość", "3000 / 3200 / 3400", "mm", "Szerokość [mm] 3000 / 3200 / 3400", DK, "dokumentacja producenta (dane techniczne)", "producent techniki przeładunkowej", "tabela ŚLUZY USZCZELNIAJĄCE, rama składana/sztywna")
src("hala_dok", "śluza uszczelniająca doku: wysokość", "3000 / 3200 / 3400 / 4400", "mm", "Wysokość [mm] 3000 / 3200 / 3400 / 4400", DK, "dokumentacja producenta (dane techniczne)", "producent techniki przeładunkowej")
src("hala_dok", "śluza uszczelniająca: głębokość i kolor profili", "600; białe aluminium", "mm", "Głębokość [mm] 600 (900 na życzenie) … Kolor profili białe aluminium (RAL 9006)", DK, "dokumentacja producenta (dane techniczne)", "producent techniki przeładunkowej")
src("hala_dok", "pomost przeładunkowy: szerokość", "1800 / 2000 / 2200", "mm", "Szerokość [mm] 1800 / 2000 / 2200", DK, "dokumentacja producenta (dane techniczne)", "producent techniki przeładunkowej", "tabela pomostów hydraulicznych, pierwsza kolumna")
HM = "https://heidelbergmaterials.pl/sites/default/files/2024-06/7-40C_Rampy_przeladunkowe_A4.pdf"
src("hala_dok", "prefabrykowany dok: wysokość rampy", "1,1", "m", "gotowe gniazda skrzyniowe są oferowane w wysokości 1,1 m", HM, "dokumentacja producenta (dane techniczne)", "producent prefabrykatów", "wartość 1,2 m z zadania: brak źródła → UNVERIFIED; używać 1,1 m")
src("hala_dok", "prefabrykowany dok: szerokość gniazda", "2070–2560", "mm", "Oferowane głębokości wewnętrzne doku to od 1820 do 4320 mm, a szerokości 2070 - 2560 mm.", HM, "dokumentacja producenta (dane techniczne)", "producent prefabrykatów", "tabela na s. 2 podaje „2160/2560” cm (błąd jednostki w źródle)")
add(kategoria="hala_dok", przedmiot="rampa dokowa: wysokość 1,2 m", wartość="1,2", jednostka="m", status="UNVERIFIED", metoda="wartość z zadania, źródła nie znaleziono", uwagi="patrz wiersz z 1,1 m (SOURCED)")
st = json.load(open(ROOT / "data/stats.json"))
QO = "data/overpass_{}.query.txt + data/overpass_{}.json"
for a in ("trasa_c", "dojlidy"):
    o = st["osm"][a]
    add(kategoria="statystyka_OSM", przedmiot=f"liczba budynków OSM ({a}); z tagiem building:levels / height / roof:shape", wartość=f"{o['n']}; {o['n_levels']} / {o['n_height']} / {o['n_roof_shape']}", jednostka="szt.", status="SOURCED",
        metoda="Overpass, zliczenie tools/stats.py", cytat=QO.format(a, a), url_źródła="https://maps.mail.ru/osm/tools/overpass/api/interpreter", licencja="ODbL", autor="OpenStreetMap contributors", obszar=a, uwagi=f"building=yes: {o['building'].get('yes')}")
    for g, v in o["groups"].items():
        add(kategoria="statystyka_OSM", przedmiot=f"{g}: liczba; rozkład building:levels; rzut dł./szer. p50", wartość=f"n={v['n']}; levels={json.dumps(v['levels'])}; {v['dl_m_p10_p50_p90'][1]}×{v['szer_m_p10_p50_p90'][1]}", jednostka="szt.; m", status="SOURCED",
            metoda="Overpass + minimalny prostokąt obrysu (EPSG:2180), tools/stats.py", cytat=QO.format(a, a), url_źródła="https://maps.mail.ru/osm/tools/overpass/api/interpreter", licencja="ODbL", autor="OpenStreetMap contributors", obszar=a,
            uwagi=f"dł. p10/p50/p90={v['dl_m_p10_p50_p90']}; szer.={v['szer_m_p10_p50_p90']}; pow.={v['pow_m2_p10_p50_p90']}; roof:shape={v['roof_shape']}")
for reg, a in (("bialystok-industrial-c", "trasa_c"), ("bialystok-dojlidy", "dojlidy")):
    for g, v in st["repo"][reg]["groups"].items():
        add(kategoria="statystyka_BDOT_LoD", przedmiot=f"{g}: kondygnacje BDOT10k; wysokość LoD1 2024 p10/p50/p90; typy dachu LoD2 2017", wartość=f"n={v['n']}; kond={json.dumps(v['storeys_bdot'])}; h={v['h_lod1_p10_p50_p90']}", jednostka="szt.; m", status="SOURCED",
            metoda=f"zliczenie z Data/Regions/{reg}/buildings.geojson (repo), tools/stats.py", cytat=f"Data/Regions/{reg}/buildings.geojson", url_źródła="https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD1/2024/20/2061.zip", licencja="GUGiK CC BY 4.0 (wg Data/SourceManifests)", autor="GUGiK", obszar=a,
            uwagi=f"dach LoD2={v['roof_type_lod2']}; kalenica LoD2={v['h_lod2_kalenica_p10_p50_p90']}; okap LoD2={v['okap_lod2_p10_p50_p90']}; h/kond.={v['h_lod1_na_kondygnacje_p10_p50_p90']}; rzut p50 {v['dl_m_p10_p50_p90'][1]}×{v['szer_m_p10_p50_p90'][1]} m")
add(kategoria="dostępność_danych", przedmiot="GUGiK LoD2 powiat 2061", wartość="HTTP 200; 23 454 471 B; Last-Modified 2018-11-14", status="SOURCED", metoda="curl -I", cytat="Content-Length: 23454471", url_źródła="https://opendata.geoportal.gov.pl/InneDane/Budynki3D/LOD2/2061_gml.zip", licencja="GUGiK CC BY 4.0", autor="GUGiK", uwagi="stan 2017 (repo: gugik-lod2-2017-2061); …/LOD2/2024/20/2061.zip → 404")
add(kategoria="dostępność_danych", przedmiot="GUGiK WCS NMPT/NMT GetCoverage", wartość="HTTP 200 dla image/x-aaigrid; image/tiff = RGB 8-bit (nieużyteczne)", status="SOURCED", metoda="curl, patrz sources.md", cytat="<ows:Fees>none", url_źródła="https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModel", licencja="GUGiK dane publiczne", autor="GUGiK", uwagi="CoverageId DSM_PL-EVRF2007-NH / DTM_PL-EVRF2007-NH; SUBSET x=easting, y=northing EPSG:2180")
add(kategoria="walidacja", przedmiot="NMPT−NMT (h_med) vs LoD1 2024, n=20 budynków próbki", wartość="mediana różnicy +0,015; mediana |różnicy| 0,195", jednostka="m", status="ESTIMATED", metoda="data/nmpt_sample.csv, wiersze z lod1_2024", uwagi="h_p95 − LoD1: mediana +0,73 m")
# sha256 kadrow z 2026-11-14 (pliki lokalne mogly zniknac; fetch.py zapisuje je jako files/<zrodlo>/<id>.jpg)
for r in rows:
    if r["kategoria"] == "kadr" and not r["sha256"]: r["sha256"] = json.load(open(ROOT / "data/frames_sha_2026-11-14.json")).get(r["id"], "")
# --- 2026-11-15: kadry Commons (24 obejrzane; dane z commons_get.py w data/commons_fetched.jsonl, opisy w data/commons_viewed.json)
CV = json.load(open(ROOT / "data/commons_viewed.json"))
for l in open(ROOT / "data/commons_fetched.jsonl"):
    c = json.loads(l); key = next(k for k in CV if not k.startswith("_") and c["title"][5:].startswith(k)); area, typ, d = CV[key]
    p = ROOT / "files" / "commons" / pathlib.Path(c["local"]).name
    add(kategoria="kadr", przedmiot=f"Commons: {c['title'][5:]} — typ: {typ}", status="SOURCED", metoda="MediaWiki imageinfo (extmetadata) → miniatura ≤1600 px → obejrzenie 960 px (Read), 2026-11-15",
        cytat=f"LicenseShortName={c['license']}; Artist={c['artist']}; DateTimeOriginal={c['date']}", url_źródła=c["page"], url_pliku=c["thumb_url"], licencja=c["license"] + " (referencja, nie tekstura)", autor=c["artist"],
        sha256=hashlib.sha256(p.read_bytes()).hexdigest(), lat=f"{float(c['lat']):.6f}" if c["lat"] else "", lon=f"{float(c['lon']):.6f}" if c["lon"] else "", kierunek_deg="UNVERIFIED",
        opis_co_widać=d, obszar=area, uwagi=f"plik files/commons/{p.name} (w repo, ≤1600 px); data zdjęcia {c['date'][:10]}; współrzędne z EXIF/Commons (kamery, nie budynku); budynek OSM nieprzypisany")
    rows[-1]["data_dostępu"] = "2026-11-15"
with open(ROOT / "manifest.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.DictWriter(f, fieldnames=COLS); w.writeheader(); w.writerows(rows)
ids = sorted(r["id"] for r in rows); k = -(-len(ids) // 5)
print(len(rows), "audit:", random.Random(20261114).sample(ids, k))
print([(r["id"], r["url_pliku"][-30:], bool(r["sha256"])) for r in rows if r["kategoria"] == "kadr"])
