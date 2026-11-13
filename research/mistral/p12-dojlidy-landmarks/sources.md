# P12 — Dojlidy/Krywlany: rejestr źródeł (sources.md)

Stan: 13 listopada 2026. Wszystkie pozycje pobierane/odczytywane w dniu 2026-11-13 (czas UTC+1), chyba że zaznaczono inaczej.
Zakazane źródła (Google Maps / Street View / Earth / 3D Tiles) **nie były używane**. Mapillary — brak tokenu (UNVERIFIED).

## 1. Dane otwarte — geometrie i wysokości

| Źródło | URL / identyfikator | Licencja | Użycie | Data odczytu |
|---|---|---|---|---|
| OpenStreetMap — wyciąg API `/api/0.6/map` (bbox 23.160–23.198, 53.0955–53.118; 23 271 węzłów, 4 179 obiektów) | https://www.openstreetmap.org/ ; timestamp bazy OSM w metadanych wyciągu | ODbL 1.0 © OpenStreetMap contributors | pozycje wszystkich obiektów, drogi, bramy, przystanki, ogrodzenia, przypisanie budynków do adresów | 2026-11-13 10:0x |
| Overpass API (serwer maps.mail.ru — końcówka `/osm/tools/overpass/api/interpreter`) | https://maps.mail.ru/osm/tools/overpass/api/interpreter (zapytania: pas wschodni 10:15, pałace 10:31) | ODbL 1.0 © OpenStreetMap contributors | obiekty poza kaflem (browar, BIAFORM, pałace, kościół), kominy, rondo Hasbacha | 2026-11-13 10:15 / 10:31 |
| GUGiK — ortofoto WMS (PZGiK ORTO StandardResolution) | https://mapy.geoportal.gov.pl/wss/service/PZGiK/ORTO/WMS/StandardResolution?SERVICE=WMS&VERSION=1.1.1&REQUEST=GetMap&LAYERS=Raster&SRS=EPSG:2180&… | otwarte dane (PZGiK; komercyjne użycie dozwolone) | kadry dowodowe 800×800 px (0,5 m/px, 400×400 m) do `files/`; próbki kolorów dachów (mediana RGB w dysku r ≤ 8 m); data nalotu UNVERIFIED (skorowidz WMS niedostępny — HTTP 401) | 2026-11-13 |
| GUGiK — modele LoD1 2024 (measuredHeight) | https://www.geoportal.gov.pl/ | CC BY 4.0 | wysokości 1 189 budynków kafla (mediana 6,81 m; p90 9,72 m; max 24,44 m); `data/matched-with-roads.json` | 2026-11-13 |
| GUGiK — BDOT10k (schemat 2021, powiat 2061, stan 2024-09) | https://www.geoportal.gov.pl/ | otwarte dane | funkcje budynków (1 256 obiektów kafla), kondygnacje, klasy typologii | 2026-11-13 |

## 2. Dokumenty urzędowe i encyklopedyczne

| Źródło | URL | Licencja | Co potwierdza | Data |
|---|---|---|---|---|
| Wikipedia PL — Port lotniczy Białystok-Krywlany | https://pl.wikipedia.org/wiki/Port_lotniczy_Bia%C5%82ystok-Krywlany | CC BY-SA (tekst) | pas 09R/27L asfaltobeton 1350×30 m; pas 09L/27R trawa 840×160 m; ele. ok. 153 m n.p.m.; właściciel Aeroklub Białostocki; zarządca Aero Partner | 2026-11-13 |
| UM Białystok — „Utrudnienia w ruchu na wlotach skrzyżowań ulic" (komunikat ZDM, wymiana tablic 2–5 XII 2025) | https://www.bialystok.pl/pl/wiadomosci/utrudnienia-w-ruchu-na-wlotach-skrzyzowan-ulic.html | dokument urzędowy (art. 4 pkt 2 pr. aut.) — tylko referencja | nowe tablice drogowe na wlotach: Suchowolca/Plażowa/Kuronia, Ciołkowskiego/Mickiewicza, Ciołkowskiego/Dywizjonu 303 | 2026-11-13 |
| UM Białystok — „Zmiany w ruchu wokół ulicy Suchowolca" | https://www.bialystok.pl/pl/wiadomosci/aktualnosci/zmiany-w-ruchu-wokol-ulicy-suchowolca.html | dokument urzędowy — tylko referencja | przekierowanie ruchu ciężarowego > 3,5 t na ciąg Kuronia → Dywizjonu 303 → Ciołkowskiego; zakaz > 8 t na Mickiewicza (Kuronia–Ciołkowskiego) | 2026-11-13 |
| MPZP Dojlidy — rejon Ciołkowskiego/Dywizjonu 303 (uchwała XXI/321/25 z 22.12.2025) | https://www.bip.bialystok.pl/resource/99912/ | dokument urzędowy | plan miejscowy strefy przemysłowej (kontekst zabudowy) | 2026-11-13 |
| UM Białystok — przetarg na halę widowiskowo-sportową | https://www.bialystok.pl/pl/wiadomosci/aktualnosci/przetarg-na-budowe-hali-widowiskowo-sportowej.html | dokument urządowy — tylko referencja | hala 30 tys. m², ~6,4 tys. widzów przy ul. Ciołkowskiego | 2026-11-13 |

## 3. Prasa i portale (informacyjne — tylko referencja, nie podstawy danych)

| Źródło | URL | Co opisuje | Data |
|---|---|---|---|
| Białystok Online — „Miasto ogranicza tranzyt ciężarówek" (art. 147518) | https://www.bialystokonline.pl/duze-zmiany-na-ulicach-bialegostoku-miasto-ogranicza-tranzyt-ciezarowek,artykul,147518,1,1.html | zmiany 19–20.11.2025: zakazy na Suchowolca/Dojlidy Fabryczne, tranzyt na Kuronia–D303–Ciołkowskiego, nowe tablice na 3 wlotach | 2026-11-13 |
| TVP Białystok | https://bialystok.tvp.pl/90478426 | od stycznia 2026 Dojlidy bez tranzytu ciężarowego | 2026-11-13 |
| Akadera (UM Białystok) — hala widowiskowo-sportowa przy Ciołkowskiego | https://akadera.bialystok.pl/bialystok-wybuduje-hale-widowiskowo-sportowa-nowoczesny-obiekt-powstanie-przy-ulicy-ciolkowskiego/ | 30 tys. m², 6,4 tys. widzów, wykonawca UNIBEP, realizacja do ~poł. 2028 | 2026-11-13 |
| Radio Białystok — wymiana wiat przystankowych (id 262755) | https://www.radio.bialystok.pl/wiadomosci/index/id/262755 | stare wiaty oszklone czerwone „modern"; od 2026 wymiana 90 szt. na antracytowe aluminium z półokrągłym dachem typ „Stare Miasto"; 4,1 mln zł | 2026-11-13 |
| Białystok Online — hala widowiskowa (art. 147234) | https://www.bialystokonline.pl/po-latach-oczekiwan-bialystok-wybuduje-nowoczesna-hale-widowiskowo-sportowa,artykul,147234,1,1.html | jw. (kontekst) | 2026-11-13 |
| investmap.pl (29.10.2026) | wynik wyszukiwania (artykuł o planach lotniska pasażerskiego Krywlany) — tylko referencja | plany lotniska pasażerskiego — kontekst dla D60, NIE dane do kafla | 2026-11-13 |
| jartom.com | wynik wyszukiwania (przetargi SSSE na działki przy BPN-T) — tylko referencja | firmy logistyczna i gastronomiczna wygrały przetargi na działki przy BPN-T; kontekst inwestora hali Spadochroniarzy 2 (UNVERIFIED) | 2026-11-13 |
| monitorfirm.pb.pl / aleo.com | https://monitorfirm.pb.pl/firma/intertex-zalewski-i-wspolnicy/ ; https://aleo.com/pl/firma/intertex-zalewski-i-wspolnicy-spolka-jawna578 | producent wyrobnów tekstylnych przy Hake 9/11 — katalog firm (UNVERIFIED operator hal) | 2026-11-13 |

## 4. Strony firm (adresy i profil działalności; bez logo i znaków towarowych w opisach do odtworzenia)

| Firma | URL | Adres | Data |
|---|---|---|---|
| KAN (centrum logistyczno-produkcyjne) | https://kan-therm.com/pl/kontakt/ | ul. Karpińskiego 5 | 2026-11-13 |
| Masterpress S.A. (druk przemysłowy) | https://masterpress.com/pl/contact/ | ul. Jacka Kuronia 4 | 2026-11-13 |
| Bravilor Bonamat Sp. z o.o. | https://ssse.com.pl/lokalizacja/bravilor-polska/ (lista lokatorów SSSE) | ul. Jacka Kuronia 2 | 2026-11-13 |
| Rosti Poland Sp. z o.o. | https://www.rosti.com/ | ul. Myśliwska 18 (OSM) | 2026-11-13 |
| BPN-T Sp. z o.o. (park naukowo-technologiczny) | https://bpnt.bialystok.pl/kontakt/ | ul. Żurawia 71 | 2026-11-13 |
| PSS „Społem" Białystok (hurtowe centrum magazynowe) | https://www.spolembialystok.eu/ ; https://www.dlahandlu.pl/hurtowe-centrum-magazynowe (art. 119171 — referencja) | ul. Dywizjonu 303 8 | 2026-11-13 |
| Kontri Sp. z o.o. (tekstylia techniczne) | https://kontri.pl/pl/contact.html | ul. Jacka Kuronia 3 | 2026-11-13 |
| Art-Glas (hurtownia szkła budowlanego) | https://artglas.com.pl/ | ul. Wiewiórcza 4 | 2026-11-13 |
| Zintronic (systemy kamer i monitoringu) | https://zintronic.com/monitoring-bialystok | ul. Karola Modzelewskiego 2 | 2026-11-13 |
| Biaform S.A. (producent sklejki) | https://biaform.com.pl/kontakt/ | ul. Dojlidy Fabryczne 24 | 2026-11-13 |
| NIBE-BIAWAR (armatura, kotły) | https://biawar.com.pl/kontakt-2/ | ul. Prof. Andrzeja Kalicińskiego 1 | 2026-11-13 |
| BISON-BIAL (fabryka przyrządów i uchwytów) | https://e-podlasie.pl (artykuł — referencja) | ul. Myśliwska 13 (katalogi) | 2026-11-13 |
| Odlewnia Białystok S.A. | https://www.cylex-polska.pl/ (katalog — referencja) | ul. Myśliwska 11 (katalogi) | 2026-11-13 |
| Browar Dojlidy (operator: ogólnokrajowy producent piwa — marka celowo niepodana w opisach do odtworzenia) | https://www.kp.pl/browary/browar-dojlidy (OSM website) | ul. Dojlidy Fabryczne 28 | 2026-11-13 |
| Parafia pw. Niepokalanego Serca Maryi | https://www.parafiansm.pl | ul. Dojlidy Fabryczne (kościół 1980) | 2026-11-13 |

## 5. Zdjęcia z wolnymi licencjami (pliki w `files/`, NIE w gicie)

| Plik | Źródło | Autor | Licencja | URL |
|---|---|---|---|---|
| P12-P01-browar-panorama.jpg | Wikimedia Commons (curid 30474259) | Henryk Borawski | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Browar_Dojlidy_w_Bia%C5%82ymstoku_panorama_1.jpg |
| P12-P02-browar-fasada.jpg | Wikimedia Commons (curid 52199842) | Kompania Piwowarska | CC BY-SA 4.0 | https://commons.wikimedia.org/wiki/File:Browar_Dojlidy_fasada_budynku.jpg |
| P12-P03-lotnisko.jpg | Wikimedia Commons (curid 20463837) | SilverTree | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Lotnisko_na_Krywlanach.jpg |
| P12-P04-sad.jpg | Wikimedia Commons (curid 30730935) | Henryk Borawski | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:S%C4%85d_Rejonowy_w_Bia%C5%82ymstoku_(Mickiewicza_103)_1.jpg |
| P12-P05-palac-hasbacha.jpg | Wikimedia Commons (curid 21441453) | Mariag36 | CC BY-SA 3.0 | https://commons.wikimedia.org/wiki/File:Bia%C5%82ystok_Dojlidy_Fabryczne_23,_Pa%C5%82ac_Hasbacha.jpg |
| P12-A01..P12-A26.jpg | ortofoto GUGiK (WMS) | GUGiK | otwarte dane (komercyjne OK) | https://mapy.geoportal.gov.pl/wss/service/PZGiK/ORTO/WMS/StandardResolution |

Kadry ortofoto: 25 szt. (P12-A01…A26 bez A20), 800×800 px (0,5 m/px, obszar 400×400 m), JPEG. Zdjęcia Commons przeskalowane do ≤ 1600 px przy pobieraniu (Openverse/Commons API, 2026-11-13; Commons API ograniczał liczbę zapytań — HTTP 429).

## 6. Zdjęcia uliczne — dostępność

| Serwis | Status | Uwagi |
|---|---|---|
| Panoramax | **brak pokrycia** — 0 kadrów w bbox kafla | zapytanie API 2026-11-13 |
| KartaView | API publiczne zwróciło 404 | UNVERIFIED |
| Mapillary | **brak tokenu** — UNVERIFIED | zgodnie z zasadami zadania |
| Google Street View / Earth / 3D Tiles | **ZAKAZANE — nie używane** | — |

## 7. Narzędzia (reprodukowalność)

- `tools/epsg2180.py` — transformacja WGS84 ↔ EPSG:2180 (Strefa 18, GRS80, k0=0,9993, λ0=19°E), skalibrowana na kafel `bialystok-industrial-c`.
- `tools/parse_osm.py` — parsowanie wyciągu OSM do `data/*.json` (region-summary, road-geom, osm-pois).
- `tools/parse_lod1.py`, `tools/match_buildings.py` — LoD1/BDOT10k → przypisanie budynków do dróg i klas (`data/matched-with-roads.json`).
- `tools/frames_colors.py` — kadry ortofoto WMS + próbki kolorów dachów (mediana RGB w dysku; paleta nazw). Dla P12-039 (Pałac Hasbacha) próbka pobrana dodatkowo metodą PNG-probe (mały PNG 16×16 px dekodowany czystym Pythonem, zlib) — tożsama metoda dysku r ≤ 8 m.
- `tools/typologia_colors.py` — rozkład barw dachów klas typologii (`data/typologia-colors.json`).
- `tools/gen_manifest.py` — generuje `manifest.csv` (95 wierszy) z danych `data/`.
- `tools/gen_audit.py` — losowanie warstwowe 20% (seed 20261113) + kontrola → `audit_20_percent.json`.
