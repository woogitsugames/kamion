# Źródła — M58 (cloud p15-dojlidy-details)

Data dostępu do wszystkich źródeł: 2026-11-14 (UTC). User-Agent: `kamion-research/1.0 (open-data reference collection)`. Google / Bing / Apple / Yandex / Mapillary — nieużywane.

## OpenStreetMap (ODbL 1.0, © autorzy OpenStreetMap)
- Overpass `overpass-api.de` — zablokowany przez proxy; mirror `https://maps.mail.ru/osm/tools/overpass/api/interpreter` — HTTP 504 (2 próby, 16:49–16:51 UTC). Zapytanie, które nie przeszło:
  `[out:json][timeout:90];( nwr["barrier"](53.090,23.150,53.116,23.215); nwr["aeroway"](53.090,23.150,53.116,23.215); way["highway"](53.090,23.150,53.116,23.215); ); out body geom;`
- Użyto: `https://api.openstreetmap.org/api/0.6/map?bbox=23.155,53.094,23.212,53.114` — 2026-11-14 16:51 UTC, 6 532 427 B, sha256 `8ee142099e9219f87e8e5977b7856b0060099fd296d4ce1979a717585c3939d6` (nie w repo).
- Wynik: `aeroway=runway` way 958211700 (09R/27L, asphalt) i 303368859 (09L/27R, grass); `aeroway=aerodrome` way 234838628; `barrier`: fence 99 dróg, wall 11, gate 137 węzłów, lift_gate 17, bollard 4, kerb 2, **chain 0**.
- Ogrodzenie lotniska: way 483199984, 483199985, 542255310. Drogi: Dywizjonu 303 way 443103344 / 671082741, Mickiewicza way 206333509 / 258564446, Kuronia way 275237234 / 1540798842.

## PAŻP — AIP Polska (dokument urzędowy; wykorzystano tylko fakty)
- Strona: `https://ais.pansa.pl/publikacje/aip-polska/` → eAIP VFR `https://docs.pansa.pl/ais/eaipvfr/defaultInt_offline_2026-10-29.html` („Obowiązująca Zmiana: AIRAC AMDT VFR 11/26 (29 OCT 2026)”, publikacja 01 OCT 2026; następna 12/26 — 26 NOV 2026).
- Tekst: `…/AIRAC AMDT VFR 11-26_2026_10_29/eAIP/AD 4 EPBK 1-pl-PL.html` (EPBK AD 4.1–4.13).
- Karta: `…/documents/Root_WePub/AIP VFR/AD/EPBK/2/AD_4_EPBK_2-1.pdf` — „VFR AD 4 EPBK 2-1, 11 JUN 2026”, stopka „AIRAC AMDT VFR 06/26”; 85 929 B; tekst karty jest grafiką wektorową — odczytano z renderu 200 dpi.
- Suplement: `…/eSUP/Sup_A_VFR_2026_002.pdf` — AIRAC VFR SUP 02/26.

## GUGiK (dane PZGiK, otwarte)
- Ortofoto: `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution` (WMS 1.3.0, LAYERS=Raster, CRS=EPSG:2180, BBOX w kolejności N,E; MaxWidth/Height 4096). Dokładne adresy GetMap każdego wycinka — kolumna `url_pliku`.
- Aktualność arkuszy: `…/PZGIK/ORTO/WMS/SkorowidzeWgAktualnosci` (GetFeatureInfo, INFO_FORMAT=text/html): N-34-107-C-b-3-4 i N-34-107-C-b-3-2 — 2025-04-18, 0,05 m, RGB, GK-FOTO.6201.5.2025; wcześniejsze: 2024-03-30 (0,05 m, PL-2000:S8), 2024-05-27 (0,25 m).
- NMT: `…/PZGIK/NMT/GRID1/WCS/DigitalTerrainModelFormatTIFF` (WCS 2.0.1, coverage `DTM_PL-KRON86-NH_TIFF`, siatka 1 m, PL-KRON86-NH); skorowidz `…/PZGIK/NMT/WMS/SkorowidzeUkladKRON86`: 2018-04-12 (1:5000) i 2018-11-30 (1:1000), wcześniej 2011-08-12.
- NMPT WCS: 404 / 401 — niedostępny.
- Przeliczenie WGS84 ↔ PL-1992: własna implementacja odwzorowania Gaussa-Krügera (GRS80, λ0 = 19°, k0 = 0,9993, FE 500 000, FN −5 300 000), kontrola na punkcie 52°N 19°E.

## Dz.U. (akt normatywny)
- Dz.U. 2019 poz. 2311: `https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text/O/D20192311-c2.pdf` — 525 stron, 39 743 815 B; zawiera obwieszczenie, rozporządzenie i zał. 1. Cytat ze s. 79 (zał. 1 pkt 2.2.19).
- `…/D20192311-c1.pdf` — ten sam plik (identyczne sha256); `…/text.pdf` — ten sam rozmiar. `isap.sejm.gov.pl/isap.nsf/download.xsp/WDU20190002311/O/…` — 403 / strona antybotowa. `dziennikustaw.gov.pl`, `gov.pl` — brak połączenia. Dz.U. 2003 nr 220 poz. 2181 w API: 1 strona.

## Wikimedia Commons
- API: `https://commons.wikimedia.org/w/api.php` (`list=geosearch`, 13 punktów × promień 600 m → 316 plików, 16:59–17:08 UTC; `prop=imageinfo` z `iiprop=url|sha1|extmetadata|size`).
- Oglądanie: `https://commons.wikimedia.org/w/thumb.php?f=<nazwa>&width=960` (31 kadrów) i `&width=3840` (13 kadrów → 26 wycinków). `upload.wikimedia.org` — HTTP 429, Retry-After 600 przez całą sesję.
- Autorzy i licencje (z `extmetadata`): 17 plików Rakoon — CC0; `Białystok - budynek WSWFiT 1.jpg` — Henryk Borawski, CC BY-SA 4.0 (referencja, nie tekstura; atrybucja).
- Kadry obejrzane i niewłączone do manifestu (nic nie wnoszą do M58): 20230814_175442, 20230814_174522, 20240623_140941 (brama ogrodów działkowych), 20200726_083529 (brama ogrodów działkowych), 20240623_124718, 20200726_084244, 20230814_182947, 20240623_141702, 20200726_081804, 20200726_081832, 20230814_174221, 20240623_140204, `Lotnisko na Krywlanach.jpg` (wnętrze lotniska — zakres M64).

## Sondaże ujemne
- Panoramax `https://api.panoramax.xyz/api/search?bbox=23.155,53.094,23.212,53.114&limit=1000` → 0 (16:58 UTC; w szerszym bbox 129 zdjęć, wszystkie poza regionem).
- KartaView `https://api.kartaview.org/2.0/photo/?lat=…&lng=…&radius=500` — siatka 4 × 7 punktów → 0 (kontrola w centrum miasta zwraca dane).
