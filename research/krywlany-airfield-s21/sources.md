# Źródła — K64 (M64, lotnisko Krywlany z drogi)

Dostęp: 2026-11-15. Zakaz Google/Bing/Apple/Yandex przestrzegany. Mapillary nie był używany (brak tokenu).

## Dokumenty urzędowe
- **AIP VFR Polska, karta VFR AD 4 EPBK 2-1 (AERODROME CHART)**, data karty 11 JUN 2026, stopka AIRAC AMDT VFR 06/26, wydanie eAIP AIRAC AMDT VFR 11/26 (29 OCT 2026):
  `https://docs.pansa.pl/ais/eaipvfr/AIRAC%20AMDT%20VFR%2011-26_2026_10_29/documents/Root_WePub/AIP%20VFR/AD/EPBK/2/AD_4_EPBK_2-1.pdf`
  - sha256 `6a0bff7c6bf743f34d19234277799deaeffdbfc31b44eef47a9846d004e4046a`, 85 929 B. Karta jest grafiką wektorową bez warstwy tekstu, dlatego odczytałem ją z renderu 150/300 dpi (pdftoppm).
  - Fakty: tabela „09R/27L … 1350 x 30 … CONC/ASPH … TORA 1350 … LDA 900 / 640”, „09L/27R … 840 x 160 … GRASS”; napisy „STRIP 1470 x 150”, „STRIP 900 x 225”; oznaczenia dróg kołowania A, B, C; 2 symbole wiatrowskazu; „AD ELEV 509 ft”.
  - Karty nie kopiuję, zapisuję tylko te fakty.

## GUGiK (dane PZGiK, bez opłat)
- **Ortofotomapa:** WMS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution` (WMS 1.3.0, `LAYERS=Raster`, `CRS=EPSG:2180`, BBOX w kolejności N,E). Adres GetMap każdego wycinka jest w kolumnie `url_pliku`, a skrypt w `tools/urlmap.py`.
  - Arkusze ustaliłem ze skorowidza `…/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci`, warstwa `SkorowidzeOrtofotomapy2025` (GetFeatureInfo, `tools/skor.py`):
    - pas: **N-34-107-C-b-3-4**, 2025-04-18, 0,05 m, RGB, GK-FOTO.6201.5.2025;
    - hangary: **N-34-107-C-b-3-2**, 2025-04-18, 0,05 m.
  - Starsze arkusze: 2024-03-30 0,05 m (8.193.14.16.3, 8.193.14.21.1) i 2024-05-27 0,25 m.
  - Zastrzeżenie (jak w M58): WMS nie mówi, który arkusz renderuje. Za 2025 przemawia zgodność długości cieni z wysokością Słońca dla 2025-04-18 ok. 09:00 UTC.
- **NMPT** (lot 2023-09-15, 0,5 m, PL-EVRF2007-NH), `https://opendata.geoportal.gov.pl/NumDaneWys/NMPT/78825/`:
  - `78825_1436510_N-34-107-C-b-3-2.asc` sha256 `82987a061eff781688b359d5442402e79f1b3af56c884edae611ecd61b8b367d`
  - `78825_1436512_N-34-107-C-b-3-4.asc` sha256 `b175a3cdedadbab0404c33e9651857e99d17fb7c112a578eac6799f911a30502`
  - `78825_1436515_N-34-107-C-b-4-3.asc` sha256 `795a6f4d02081ba3ecf7acab3a47c036867709c0b6c4fbd8f3cccfb3c599aba2`
  - Sumy zgadzają się z M68 (`research/cloud/p25-krywlany-forest/sources.md`). Plików nie ma w gicie (ok. 150 MB każdy).
- **NMT 1 m:** WCS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF?SERVICE=WCS&VERSION=2.0.1&REQUEST=GetCoverage&COVERAGEID=DTM_PL-KRON86-NH_TIFF&FORMAT=image/tiff&SUBSET=x(E1,E2)&SUBSET=y(N1,N2)&SUBSETTINGCRS=http://www.opengis.net/def/crs/EPSG/0/2180`.
  - Pobrany obszar: 15 kafli 500 m, E 778300–780500, N 589300–590700 (`tools/nmt_fetch.py`).
  - Rok pomiaru wg M58: 2018.
- **NMPT z WCS:** `…/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel`, `COVERAGEID=DSM_PL-KRON86-NH`, `FORMAT=image/x-aaigrid`. Użyty tylko do sprawdzenia hali namiotowej (K64-031).

## OpenStreetMap (ODbL 1.0)
- `https://api.openstreetmap.org/api/0.6/map?bbox=23.150,53.095,23.192,53.1075`, pobrane 2026-11-15 09:41 UTC (1,32 MB).
- Kontrola w audycie: `/api/0.6/way/229040230/full.json` (wersja 4) i `/way/304300294/full.json` (wersja 2).
- Użyte obiekty: runway 958211700, 303368859; taxiway 958211699 (+11); apron 616186583, 234838629; hangary 229040230, 304300294; LPR 1234358789; windsock 5920347042, 7437888765, 11436697402; aerodrome 234838628; płot 483199984; bramy 4759528833; drogi 443103344, 538810157, 671082741, 671082746, 631662841, 206333509, 977514047, 1540798842.

## Zdjęcia (Wikimedia Commons; miniatury przez `commons.wikimedia.org/w/thumb.php`)
- **CC0, autor Rakoon:**
  - 2023-08-14: 174527, 174819, 174936, 175446, 175724;
  - 2020-07-26: 082250, 082324;
  - 2024-06-23: 140200, 140411, 140546.
- **CC BY-SA 3.0, z atrybucją w manifeście** (autor wg extmetadata; to „referencja, nie tekstura”): Krywlany Białystok Nowy hangar, Nowy hangar z oddali, Stary hangar, Lotnicze Pogotowie ratunkowe, flota, AN-2 i Wilga (2012-08-04); Lotnisko na Krywlanach, Podlaska Straż Graniczna patrol lotniczy (2011-03-27).
- W manifeście przy każdym zdjęciu jest strona pliku, URL oryginału, sha1 oryginału z API i sha256 zapisanej miniatury (≤ 1600 px, JPEG q82).
- Sondy:
  - Panoramax (`api.panoramax.xyz`, `panoramax.openstreetmap.fr`, `panoramax.ign.fr`; bbox 23.150–23.200 × 53.094–53.112): **0**;
  - KartaView (`api.kartaview.org/2.0/photo`, 10 punktów, r = 500 m): **0**;
  - Openverse (q = Krywlany / Białystok lotnisko): tylko kopie plików Commons.

## Repozytorium (odsyłacze)
- M58: `research/cloud/p15-dojlidy-details/` (README §2–§3, manifest C58-029, C58-056, C58-069) i recenzja `docs/reports/REVIEW-2026-11-14-s20-cloud-m58.md`.
- M68: `research/cloud/p25-krywlany-forest/` (arkusze NMPT, wysokości lasu).
- Kamera gry: `Data/Regions/bialystok-dojlidy/control_cameras_place.authored.json` (`krywlany_runway`), origin regionu EPSG:2180 780043, 590079 (`overrides.yaml`); ADR `docs/adr/0196-dojlidy-zaklad-bramy-zacieki-pas.md`.
