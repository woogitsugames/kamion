# M51 (p10-greenery-3) — źródła

Data dostępu: **2026-11-13** (UTC), chyba że zaznaczono inaczej. Zakaz Google Maps/Street View/Earth/3D Tiles — zachowany.

## Zdjęcia street-level

### Wikimedia Commons (Rakoon) — CC0 (51 plików), CC BY 3.0 (3 pliki, „referencja, nie tekstura")
- Geosearch API: `https://commons.wikimedia.org/w/api.php?action=query&generator=geosearch&ggscoord=53.153|23.152&ggsradius=1200&ggslimit=500&ggsnamespace=6` (+ `prop=imageinfo&iiprop=url|extmetadata`).
- Metadane autora/licencji: `action=query&prop=imageinfo&iiprop=extmetadata` (Artist, LicenseShortName) — 54 pliki, wszystko: Rakoon; 51× CC0, 3× CC BY 3.0 (seria 2020-07-11).
- Pliki pobrane przez `Special:FilePath?width=1600`, przeskalowane 1920→1600 px (PIL LANCZOS, q88).
- Serie (wszystkie strony pliku w formacie `https://commons.wikimedia.org/wiki/File:<nazwa>`; pełna lista w `manifest.csv`):
  - **2020-07-11 06:51** — wlot Łańcuckiej (3 kadry, CC BY 3.0),
  - **2021-06-08 08:23** — aleja przed przebudową (1 kadr, CC0),
  - **2022-07-25 12:39–13:28** — spacer aleją: wlot Wileńskiej i **wlot Skidelskiej** (44 kadry, CC0; 7 w manifestcie),
  - **2023-07-29 10:53** — aleja (4 kadry, CC0),
  - **2024-06-26 10:33** — aleja przy wlocie Łańcuckiej (5 kadrów, CC0).

### KartaView (OpenStreetCam) — licencja wg zasad serwisu (CC BY 4.0)
- API: POST `https://api.kartaview.org/1.0/list/nearby-photos/` (lat, lng, radius) → `current_page`/`total_items`; POST `https://api.kartaview.org/1.0/sequence/photo-list/` (sequenceId) → pełne metadane (shot_date, Heading, lat/lng, lth_name 1280 px).
- Obrazy: `https://storageN.openstreetcam.org/files/photo/…/lth/…jpg` (1280 px, ~300 KB).
- **storage7.openstreetcam.org → HTTP 502** (outage; test 2026-11-13 14:45 UTC i 15:2x UTC) — dotyczy 142 kadrów sekwencji 1155711 z 23.03.2018 (wloty wszystkich 9 ulic, azymut Heading z API = SOURCED); metadane zachowane (`kv_wloty_test.json`, `seq_1155711.json` w ZIP).
- Letnie sekwencje pobrane (aleja/Andersa, poza osiami 9 ulic): 10733 (2016-07-19), 14055 (2016-08-24), 2763230 (2019-08-04), 2769366 (2019-08-25), 3686129 (2021-06-23) — 51 kadrów JPG w ZIP.

### Panoramax — 0 wyników
- `https://api.panoramax.xyz/api/search?bbox=23.147,53.148,23.156,23.158` — brak zdjęć (zamknięty temat, licencja CC BY-SA 4.0 nieistotna przy 0 wynikach).

### Openverse — bez trafień
- Zapytania po nazwach ulic — brak wyników street-level dla osiedla.

### Mapillary
- **Nie odpytano** — brak tokenu API w środowisku; nie zgadywano kluczy (UNVERIFIED z założenia).

## Ortofotomapa / dane geoprzestrzenne

- **GUGiK**, ortofotomapa 2024-05-27, GSD 0,25 m, RGB, licencja **CC BY 4.0** (via dane.gov.pl): WMS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/StandardResolution` (warstwa Raster); manifest repo: `Data/SourceManifests/gugik-orto-2024-rgb-0p25-bialystok-industrial-c.json` (4 arkusze N-34-107-A-d-3-3/-3-4, N-34-107-C-b-1-1/-1-2, sha256 w repo).
- **OSM (ODbL)** — osie ulic i nazwy: `Data/Regions/bialystok-industrial-c/roads.graph.json` (przekształcone z OSM; licencja ODbL, © OpenStreetMap contributors).
- Transformacja EPSG:2180↔WGS84: implementacja Snydera (PL-1992) — `tools/tm2180.py` (na gałęzi), walidacja roundtrip < 1e-8°.

## BIP / urzędowe (przetarg Al. Tysiąclecia, zad. 4)

- Karta postępowania: `https://www.bip.bialystok.pl/postepowania/zamowienia/rozbudowa-alei-tysiaclecia-panstwa-polskiego-w-bialymstoku-od-ul-wilenskiej-do-terenu-kolejowego-przy-ul-poleskiej-wraz-z-infrastruktura-techniczna.html` (nr ZDM-X.271.16.2018.JZ; 39 załączników).
- SIWZ.pdf (8,79 MB; **skan, 20 stron** — JPG w ZIP `files/bip/siwz_pages/`): `https://www.bip.bialystok.pl/resource/42661/SIWZ.pdf`.
- Załączniki z 22.07.2020 (ZIP; umowa DOCX, kosztorys — skan, postanowienie RDOŚ 17 s. CCITT G4 → PNG w ZIP `files/bip/rdos_pages/`): `https://www.bip.bialystok.pl/resource/69314/Za%C5%82%C4%85czniki+22.07.2020+r..zip`.
- Komunikat UM o otwarciu alei (74 drzewa, 109 krzewów, 20 600 m², ~385 mb ekranów): `https://www.bialystok.pl/pl/aktualnosci/aleja-tysiaclecia-panstwa-polskiego-otwarta.html` (31.01.2022).
- Obwieszczenie MRT (droga wojewódzka 675): `https://www.gov.pl/web/rozwoj-technologia/obwieszczenie-ws-rozbudowy-ulicy-aleja-1000-lecia-panstwa-polskiego-w-bialymstoku-droga-wojewodzka-nr-675-od-ul-wilenskiej-do-terenu-kolejowego-przy-ul-poleskiej-wraz-z-infrastruktura-techniczna`.
- Prasowe (kontekst, nie dane liczbowe): poranny.pl c4-15296431 (Strabag, X 2021); radio.bialystok.pl 209894; podlaskie24.pl 2022/01/31.

## Repo (wcześniejsze badania — nie dublowane)

- `research/g7-street-greenery/` — README, manifest (G7-P01…P12, IV 2024, CC0, Rakoon), 12 kadrów w `files/`.
- `research/gptpro/p10-street-greenery-2/` — README, manifest P10-001…410 (zdjęcia 101…114, odcinki 201…237, młode drzewa 301…313, inne 001…008, 401…410).
- `Data/Regions/bialystok-industrial-c/plot_canopy.json` (3500 koron, metoda produkcji terenowej) — punkt odniesienia porównania.

## Oprogramowanie/metody

- Analiza obrazu (odczyt gatunków/wysokości żywopłotów, treść kadrów): `tools.uploads.analyze_image` (Vibe, model wizyjny), 2026-11-13; odczyty surowe w `obs.json` (ZIP).
- Detekcja koron: `tools/detect_crowns.py` (numpy, scipy, Pillow; skrypt odtwarzalny); porównanie: `tools/compare_with_p10.py`.
- Dekoder CCITT G4 dla skanów RDOŚ: własny (TIFF-wrapper + libtiff/Pillow), skrypt w ZIP (`pdf_ccitt_extract.py`).
- Ekstrakcja JPEG ze skanów SIWZ: własna (`pdftxt.py`/parser strumieni PDF), strony w ZIP.
- Generator manifestu/audytu: `build_manifest.py`, `audit.py` (w ZIP); seed audytu: **20261113**.
