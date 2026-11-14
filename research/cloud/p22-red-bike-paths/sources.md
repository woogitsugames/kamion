# Źródła — M65 (cloud p22-red-bike-paths)

Data dostępu do wszystkich źródeł: 2026-11-14 (UTC). User-Agent: `kamion-research/1.0 (open-data reference collection)`.

## 1. OpenStreetMap (ODbL 1.0, © autorzy OpenStreetMap)
- Endpoint: `https://maps.mail.ru/osm/tools/overpass/api/interpreter` (POST `data=`), mirror Overpass API 0.7.62.4.
- Zapytanie: plik `overpass-query.ql` (wszystkie `way[highway]` + węzły `highway=crossing|traffic_signals`, `crossing=*`, `barrier=kerb` w obwiedniach WGS84 obu kafli).
- Wykonano: 2026-11-14T16:49:07Z (dwie wcześniejsze próby: HTTP 504); `timestamp_osm_base` = 2026-11-14T16:48:34Z. Surowy wynik: `overpass-result.json` (1 410 318 B).
- Granice regionów: `Data/Regions/bialystok-industrial-c/region.yaml` (EPSG:2180 x 776971–779019, y 595199–597247) i `Data/Regions/bialystok-dojlidy/region.yaml` (x 779019–781067, y 589055–591103). Przeliczenie EPSG:2180↔WGS84: `tools/geo.py` (TM, GRS80; kontrola: przeliczenie tam i z powrotem ±1 mm).

## 2. GUGiK — ortofotomapa (dane publiczne, art. 40a ust. 2 pkt 1 PGiK; „Źródło danych: GUGiK, www.geoportal.gov.pl”)
- WMS: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution` (GetMap 1.1.1, `SRS=EPSG:2180`, `LAYERS=Raster`, JPEG). Piksel żądany 5 cm (wycinki 44×44 m → 880 px; zbiorcze do 77 m → 1400 px).
- Aktualność: WFS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze` (`gugik:SkorowidzOrtofomapy2024/2025`) — punkty kontrolne w obu kaflach pokrywają dwa naloty 5 cm RGB: **2025-04-18** (arkusze N-34-107-C-b-3-2, N-34-107-C-b-1-1) i **2024-03-30** (arkusze 8.193.14.16.4, 8.194.13.20.4). Usługa WMS nie zwraca, który arkusz wyświetla (GetFeatureInfo = tylko RGB piksela) → data kadru podana jako alternatywa. Przesłanka za 2025-04-18: kwitnące drzewa i zielone krzewy na wycinkach.
- Odpowiedź GetMap jest deterministyczna (ten sam URL → to samo sha256; sprawdzone dwukrotnie + pełny przebieg `fetch.py`).
- Zastosowanie: wyłącznie referencja (oględziny, pomiar linijką), nie tekstura.

## 3. Panoramax (CC BY-SA 4.0 — referencja, nie tekstura)
- `https://api.panoramax.xyz/api/search?bbox=23.1437,53.1488,23.1760,53.1683&limit=1000` → 55 kadrów (2 sekwencje, autor „stanton”, 2019-08-15 i 2019-09-01), wszystkie z kabiny samochodu na ciągu Maczka/rondo pod estakadą.
- `…bbox=23.1689,53.0926,23.2012,53.1121` (Dojlidy) → **0 kadrów**.
- Kierunek: `properties.view:azimuth` z API; plik: `assets.hd`.

## 4. KartaView (CC BY-SA 4.0 — referencja, nie tekstura)
- `POST https://api.kartaview.org/1.0/list/nearby-photos/` (lat, lng, radius=250): region C — sekwencje 1155711 (2018-03-23, telenavdrives), 3686129 (2021-06-23, TMishaaa), 2769366 i 2763230 (2019-08, gpsmapper999), 14055, 10733, 25209 (2016); Dojlidy (7 punktów) → **0 kadrów**.
- `GET https://api.kartaview.org/2.0/photo/?tLeft=…` → „Restricted access!” (nieużywane). Pliki: `storage13.openstreetcam.org/.../proc/…`; dla sekwencji z 2018 r. (storage7 zwraca 502) przez `https://cdn.kartaview.org/pr:sharp/<base64 URL>` (odpowiedź deterministyczna — sha256 sprawdzone dwukrotnie).
- Kierunek: pole `heading` (kurs GPS pojazdu).

## 5. Wikimedia Commons — NIEDOSTĘPNE w tej sesji
- `upload.wikimedia.org` i `commons.wikimedia.org/w/api.php` zwracały **HTTP 429** (`retry-after: 600`, „You are making too many requests”) nieprzerwanie od 2026-11-14T16:52Z (próby co ok. 10 min do końca sesji; adres wyjściowy współdzielony). Kadry P11-001 i P11-056 (CC0, autor Rakoon) oraz pozostałe kadry Dojlid z `research/mistral/p11-dojlidy-photos/manifest.csv` **nie zostały pobrane ani obejrzane** — patrz README §9 (luki).
- Adresy oryginałów (do pobrania przez lidera): P11-001 `https://upload.wikimedia.org/wikipedia/commons/8/88/20240623_142113_June_2024_in_Bia%C5%82ystok.jpg`; P11-056: strona `https://commons.wikimedia.org/wiki/File:20230814_175724_August_2023_in_Bia%C5%82ystok.jpg`.
- Openverse API (`api.openverse.org`) — HTTP 504 przy próbie.

## 6. Dokumenty urzędowe (art. 4 pr. aut.)
- **Dz.U. 2019 poz. 2311**, zał. nr 2 (znaki poziome), PDF część c2: `https://eli.gov.pl/api/acts/DU/2019/2311/text/I/D20192311-c2.pdf` (27 996 609 B, sha256 `8abcce24…c5d4`); pkt 4.2.2 „Przejazd dla rowerzystów” — str. Dz.U. 569–571 (= str. 44–46 PDF c2).
- **Wytyczne do projektowania dokumentacji projektowej budowy, rozbudowy i przebudowy ulic w Białymstoku** (wersja „13 lipca 2018 r. / 2025 r.”), BIP Białystok zasób 103311: `https://www.bip.bialystok.pl/resource/103311/Za%C5%82.+nr+5_Wytyczne+do+projektowania.pdf` (1 627 896 B, 21 str., sha256 `11e87d1a…b16b`); rozdz. V (oznakowanie poziome, str. 16) i „Wytyczne projektowania i budowy dróg dla rowerów” (str. 18–21). Tekst z `pdftotext` (znaki diakrytyczne odtworzone ręcznie), rysunek nr 9 obejrzany po rasteryzacji (`pdftoppm -r 110`).
- Projektów/przetargów BIP dla konkretnych odcinków (szerokości DDR „z dokumentu”) nie odnaleziono w tej sesji — szerokości pochodzą z ortofotomapy (ESTIMATED).

## 7. Nieużyte / zakazane
- Mapillary — nie używano (brak tokenu). Google/Bing/Apple/Yandex — nie używano.
