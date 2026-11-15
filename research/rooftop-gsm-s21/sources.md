# Źródła K67 (dostęp 2026-11-15)

## Karty katalogowe (fakty: wymiary, kolor; nazw producentów nie używam w opisach)
- Antena sektorowa 2688 mm: https://es.andrew.com/products/base-station-antennas/antennas/itemrrzzvvq4q4-65dr8 — „Length 2688 mm”, „Light Gray (RAL 7035)”.
- Antena sektorowa 1499 mm: https://www.andrew.com/products/base-station-antennas/antennas/itemffv4q4-65a-r7 — „Length 1499 mm”, „Width 498 mm”, „Depth 197 mm”.
- Antena radioliniowa 0,6 m: https://es.andrew.com/products/microwave/antennas/vhlp2-23-d — „0.6 m | 2 ft”, 6,7 kg.
- Antena radioliniowa 0,3 m: https://es.andrew.com/products/microwave/antennas/vhlp1-23-d — „0.3 m | 1 ft”, 4,08 kg.
- RRU: https://www.hytera.com/en/product-new/4g5g/macro-base-station/rru5800.html — „425 mm × 296 mm ×130 mm”, 18,3 kg, IP65.

## Przepisy
- Prawo budowlane art. 29 — tekst jednolity Dz.U. 2026 poz. 524 (obwieszczenie 27.03.2026), API ELI Sejmu: https://api.sejm.gov.pl/eli/acts/DU/2026/524/text.pdf (sha256 4a33b840883a10aa6f68d3cd85ac673a727b6b822ef092b1b97efbcdfda57826; s. 26 ust. 3 pkt 3 lit. a, s. 27 ust. 4 pkt 3 lit. a); ISAP: https://isap.sejm.gov.pl/isap.nsf/DocDetails.xsp?id=WDU20260000524 (403 dla klienta skryptowego). Lista t.j.: https://api.sejm.gov.pl/eli/acts/DU/1994/414. Wcześniej (r1): standardyprawa.pl (strona wtórna) — zastąpione.
- Rozp. MI z 12.01.2021 (Dz.U. 2021 poz. 264): https://api.sejm.gov.pl/eli/acts/DU/2021/264/text.html — § 22, § 24–26, § 35, § 36, § 46.

## UKE (informacja publiczna)
- Strona: https://bip.uke.gov.pl/pozwolenia-radiowe/wykaz-pozwolen-radiowych-tresci/stacje-gsm-umts-lte-5gnr-oraz-cdma,12,0.html
- Pliki „stan na 2026-10-26” (nie w gicie): lte1800 sha256 00cb34e26bd92fd2eb621b20c0ff67592f7054564013f0c8df9404411662c27a; gsm900 9452817416c635bd34dd5da433d1ff9e43ef8b85b8723372d023b835928f0819; lte800 f21d161cfa89ebf3ce2a8513680edc28e593888fea2305a1095d4bd60541a2d3; 5g3600 e380a8b7d5b375466afa058b2b7b6d44182278210ddf4c96ac1abea8374afa92.

## Ortofoto
- GUGiK WMS `https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WMS/HighResolution`, warstwa Raster, EPSG:4326 (`tools/ortho_crop.py`; URL GetMap = deterministyczny z bbox). sha256 plików w manifeście.

## OSM (ODbL)
- OSM API 0.6 `/map` (kafle z K69, bbox 53.095–53.165 N / 23.120–23.215 E): `roof_masts.json` (22 maszty, 4 w obrysie budynków), budynki ≥ 8 kond.

## LIDAR i skorowidze GUGiK (M67-FIX r2)
- WFS skorowidzy: https://mapy.geoportal.gov.pl/wss/service/PZGIK/ORTO/WFS/Skorowidze (gugik:SkorowidzOrtofomapy2018–2026) i https://mapy.geoportal.gov.pl/wss/service/PZGIK/DanePomiaroweLidarEVRF2007/WFS/Skorowidze (gugik:SkorowidzDanychPomiarowychLIDAR2018–2026) — wynik: out/skorowidz.json (tools/skorowidz.py).
- Chmury LAZ 2025-04-18, 12 p/m² (GUGiK, dane otwarte; pliki NIE w gicie, ~380 MB), sha256:
  - N-34-107-C-b-1-4-4-2 (Skorupska 17): https://opendata.geoportal.gov.pl/NumDaneWys/DanePomiaroweLAZ/83268/83268_1745992_N-34-107-C-b-1-4-4-2.laz — a1396c92014a2351e9f1f818dabe0751e6a988d3dcdfdd337b90a56a0474e42f
  - N-34-107-C-b-1-4-2-4 (Dobra 3): …/83268_1745986_N-34-107-C-b-1-4-2-4.laz — 652b5aa28e37db9aaac618684ea7add9d047b68913167b572ebd0d4327a5164c
  - N-34-107-C-b-3-1-2-4 (Zwierzyniecka 4): …/83268_1746066_N-34-107-C-b-3-1-2-4.laz — c384490810ee05e1fe0d400714bf98efda7fbcc3fb05f97172ac6a44e800ae91
  - N-34-107-C-b-1-1-3-1 (Hallera 19): …/83268_1745939_N-34-107-C-b-1-1-3-1.laz — 26d707559220b3cdc501f2da2b48d473501c3110417242342d404da473dc3b00
  - N-34-107-C-b-3-1-2-1 (Kopernika): …/83268_1746063_N-34-107-C-b-3-1-2-1.laz — e641da1beebbfc22659410b87f3ed2290cecea52c951f53bd20764de630963e2
  - N-34-107-C-b-1-2-3-2 (wieżowiec M57, kontrola): …/83268_1745956_N-34-107-C-b-1-2-3-2.laz — 79509eb8b7b2d1ebea21034235f02aea5b2e3bb975491c2371ee437a3684fe05
- Położenie Słońca: tools/sun.py (równania NOAA Solar Calculator), sprawdzenie: 2025-04-18 09:00 UTC el 44,4° = M64.
- NMPT WCS (https://mapy.geoportal.gov.pl/wss/service/PZGIK/NMPT/GRID1/WCS/DigitalSurfaceModel) — dostępny, nieużyty (LAZ dokładniejszy).

## Commons — pobrane (r2; atrybucja: autor, licencja, strona pliku w manifest.csv kat. kadr_naziemny; log prób out/commons_log.json)

## Do pobrania przy następnej okazji (Commons 429 — lista aktualna w manifest.csv K67-078)
- File:Antenna tower in Białystok (Cieszyńska).jpg, File:Antenna tower in Białystok (Kawaleryjska).jpg (CC BY-SA 4.0, wolnostojące — do katalogu elementów)
- File:Waszyngtona 36 Białystok 2.jpg / 3.jpg, File:Tysiąclecia 10A Białystok 1.jpg / 2.jpg, File:Tysiąclecia 10 Białystok 3a.jpg, File:Apartment buildings in Białystok (Waszyngtona).jpg, File:W Białymstoku 008.jpg
- File:20191110 114106 Zwierzyniecka Street in Bialystok November 2019.jpg, File:20191111 102206 Zwierzyniecka Street in Białystok.jpg, File:20201102 091949 Dobra Street in Białystok.jpg, File:20200509 155354 Kopernika Street in Białystok May 2020.jpg (+ 155417, 155523)
