# Źródła — K63 (M63, hala A i zakład B)

Dostęp: 2026-11-15. Zakaz Google/Bing/Apple/Yandex przestrzegany; Mapillary nieużywany (brak tokenu).

## Wynik bazowy (przegląd)
- P20 (Mistral, częściowy): `origin/research/mistral-p20-plant-gates`, commit `822bfe317`, `research/mistral/p20-plant-gates/` (README, manifest P20-001…075, sources, audit). Każdy przejęty wiersz ma adnotację w kolumnie `p20` manifestu.

## GUGiK (dane PZGiK, bez opłat)
- **Ortofoto:** WMS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution` (Raster, EPSG:2180). Arkusze ze skorowidza `SkorowidzeWgAktualnosci`:
  - hala A: **N-34-107-C-b-4-1**, 2025-04-18, 0,05 m, GK-FOTO.6201.5.2025;
  - zakład B: **N-34-107-C-b-3-2**, 2025-04-18, 0,05 m.
  - Wycinki w `files/ortho_*.jpg`, skrypt GetMap w `tools/ortho.py` (środek WGS84, rozmiar, piksel). Zapisane wycinki:
    - A_NNE: 53.105375 / 23.196035, 90 × 50 m, 0,05 m;
    - A_all: 53.104379 / 23.194936, 340 × 300 m, 0,25 m;
    - B_all: 53.105340 / 23.187329, 260 × 190 m, 0,2 m.
- **NMPT**, lot 2023-09-15, 0,5 m, PL-EVRF2007-NH, `https://opendata.geoportal.gov.pl/NumDaneWys/NMPT/78825/`:
  - `78825_1436510_N-34-107-C-b-3-2.asc` sha256 `82987a061eff781688b359d5442402e79f1b3af56c884edae611ecd61b8b367d`
  - `78825_1436513_N-34-107-C-b-4-1.asc` sha256 `1143abe10516f901fa38c5e935f13b7b3a388f146c38fd2daff523f80b947255`
  - `78825_1436515_N-34-107-C-b-4-3.asc` sha256 `795a6f4d02081ba3ecf7acab3a47c036867709c0b6c4fbd8f3cccfb3c599aba2`
- **NMT 1 m:** WCS `…/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF`, `DTM_PL-KRON86-NH_TIFF`, kafle 500 m dla E 779950–780900, N 590150–590600 (`tools/nmt_fetch.py`).
- **KIEG:** `https://integracja.gugik.gov.pl/cgi-bin/KrajowaIntegracjaEwidencjiGruntow`, GetFeatureInfo (LAYERS=dzialki,budynki) w punktach E 780730 N 590400 (działka 767/20) i E 780175 N 590417 (działka 767/29). Warstwa budynków nie zwróciła identyfikatorów.

## OpenStreetMap (ODbL 1.0)
- `https://api.openstreetmap.org/api/0.6/map?bbox=23.182,53.1025,23.2005,53.1075`, pobrane 2026-11-15 10:18 UTC.
- Kontrola: `/api/0.6/way/471492583/full.json`, wersja 4.

## Karty katalogowe bram (cytaty faktów; nazwy producentów nie trafiają do opisów gry)
- `https://www.assaabloyentrance.com/master-blueprint/pl/product-assets/commercial-industrial-doors/oh1042p/downloads/product-datasheet/product_datasheet_assa_abloy_oh1042p_psdi_pl-pl.pdf`
  - sha256 `5168698126ec90f3cff2121b9640512d554e383d96d9fcc60ff8dcab74a84c86`.
  - Pkt 1.2.1: „Szerokość światła … Wysokość światła … Maks.: 8000 mm 6000 mm”; „Wysokość sekcji: 545 mm”.
- `https://staszynska.pl/wp-content/uploads/2019/02/STASZY%C5%83SKA-Bramy-segmentowe-przemys%C5%82owe-specyfikacja-techniczna.pdf`
  - sha256 `ce1e7b553755c56517780773a0b0ec00d16fed5957f7e0268e7fd2f271b49acc`.
  - „szerokość maksymalna - 4500mm, z kształtownikiem usztywniającym od 4500mm do 8000mm; wysokość maksymalna - 6000mm”.

## Zdjęcia (Wikimedia Commons, CC0, autor Rakoon; miniatury przez `commons.wikimedia.org/w/thumb.php`)
- Wszystkie 45 obejrzanych kadrów (16 przypisanych, 29 odrzuconych) mają w manifeście:
  - stronę pliku i URL oryginału;
  - sha1 oryginału z API;
  - sha256 zapisanej miniatury (tylko dla 16 przypisanych, w `files/`).
- Pozycje kamer pochodzą z geosearch Commons (EXIF GPS); kadry bez GPS mają `UNVERIFIED`.
- Sondy:
  - Panoramax: 0 (3 instancje, bbox 23.150–23.200 × 53.094–53.112);
  - KartaView: 0;
  - Openverse: tylko lustro Commons (sondy wspólne z K64).
