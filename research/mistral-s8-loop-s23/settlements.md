# Typologia zabudowy wsi na pętli S8 ↔ DW671 ↔ Tykocin

Źródła: OSM API 0.6 (`raw/osm/manifest.json`, ODbL 1.0, © OpenStreetMap contributors) — liczba budynków OSM i `building:levels`; BDOT10k powiat 2002 (`gugik-bdot10k-2002`, GUGiK open data, PGiK art. 40a ust. 2 pkt 1, pobrany jako `2002_GPKG.zip` z opendata.geoportal.gov.pl w tej sesji, poza gitem) — `FUNKCJAOGOLNABUDYNKU`, `PRZEWAZAJACAFUNKCJABUDYNKU`, `LICZBAKONDYGNACJI` z `OT_BUBD_A`. Wszystkie 15 kafli pętli leży w powiecie 2002 (TERYT w OSM), więc BDOT pokrywa pełny obszar.

Liczby = budynki w promieniu 1500 m od węzła `place` (liczone narzędziowo z geometrii). Typy dachów: BDOT10k ich nie zawiera (są w LoD2, poza zakresem) — UNVERIFIED.

| miejscowość | typ | kafel | węzeł OSM | budynki OSM | budynki BDOT | kondygnacje BDOT (histogram) | główne funkcje BDOT |
|---|---|---|---|---|---|---|---|
| Broniszewo | village | dw671-jezewo-01 | node/31577946 | 260 | 284 | 1: 213, 2: 62, 3: 9 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (207); budynki mieszkalne (75); pozostałe budynki niemieszkalne (2) |
| Kolonia Broniszewo | hamlet | dw671-jezewo-01 | node/3009674177 | 247 | 252 | 1: 186, 2: 56, 3: 10 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (179); budynki mieszkalne (71); pozostałe budynki niemieszkalne (2) |
| Tykocin-Kolonia | neighbourhood | dw671-jezewo-02 | node/692602606 | 164 | 142 | 1: 115, 2: 22, 3: 5 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (104); budynki mieszkalne (38) |
| Zimna Woda | neighbourhood | dw671-jezewo-03 | node/3009680232 | 84 | 85 | 1: 65, 2: 14, 3: 6 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (64); budynki mieszkalne (21) |
| Nowosiółki | neighbourhood | s8-01 | node/3009675761 | 841 | 739 | 1: 330, 2: 316, 3: 22, 4: 9, 5: 6, null: 56 | budynki mieszkalne (453); budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (196); zbiorniki, silosy i budynki magazynowe (38) |
| Żółtki-Kolonia | village | s8-01 | node/692602597 | 535 | 522 | 1: 242, 2: 207, 3: 16, 4: 1, null: 56 | budynki mieszkalne (271); budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (175); zbiorniki, silosy i budynki magazynowe (38) |
| Żółtki | village | s8-02 | node/31568969 | 435 | 404 | 1: 244, 2: 142, 3: 10, null: 8 | budynki mieszkalne (195); budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (193); zbiorniki, silosy i budynki magazynowe (6) |
| Pławuli | hamlet | s8-03 | node/3009678168 | 206 | 192 | 1: 129, 2: 50, 3: 7, null: 6 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (112); budynki mieszkalne (63); zbiorniki, silosy i budynki magazynowe (6) |
| Szulaki | locality | s8-03 | node/13574089261 | 483 | 461 | 1: 300, 2: 143, 3: 12, null: 6 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (250); budynki mieszkalne (200); zbiorniki, silosy i budynki magazynowe (4) |
| Babino | village | s8-04 | node/31578128 | 174 | 170 | 1: 124, 2: 39, 3: 4, null: 3 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (112); budynki mieszkalne (50); zbiorniki, silosy i budynki magazynowe (3) |
| Cegielnia-Złotoria | hamlet | s8-04 | node/3009672357 | 441 | 419 | 1: 306, 2: 96, 3: 11, null: 6 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (256); budynki mieszkalne (144); zbiorniki, silosy i budynki magazynowe (5) |
| Kolonia Babino | hamlet | s8-05 | node/3009674163 | 318 | 317 | 1: 249, 2: 61, 3: 7 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (239); budynki mieszkalne (78) |
| Kolonia Rzędziany | hamlet | s8-07 | node/692602603 | 245 | 232 | 1: 180, 2: 51, null: 1 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (173); budynki mieszkalne (57); zbiorniki, silosy i budynki magazynowe (1) |
| Rzędziany | village | s8-07 | node/31571997 | 297 | 313 | 1: 234, 2: 76, 3: 1, null: 2 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (224); budynki mieszkalne (81); budynki przemysłowe (4) |
| Kolonia Radule | hamlet | s8-08 | node/3009674363 | 235 | 190 | 1: 129, 2: 56, 3: 2, null: 3 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (120); budynki mieszkalne (59); budynki handlowo-usługowe (6) |
| Pajewo | village | s8-11 | node/31573492 | 252 | 221 | 1: 164, 2: 56, 3: 1 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (162); budynki mieszkalne (57); budynki biurowe (1) |
| Jeżewo Nowe | village | s8-12 | node/31576543 | 284 | 316 | 1: 241, 2: 52, 3: 19, null: 4 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (220); budynki mieszkalne (88); zbiorniki, silosy i budynki magazynowe (3) |
| Jeżewo Stare | village | s8-12 | node/31571573 | 301 | 338 | 1: 255, 2: 63, 3: 16, null: 4 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (232); budynki mieszkalne (90); budynki handlowo-usługowe (5) |
| Kolonia Nowe Jeżewo | hamlet | s8-12 | node/3009674315 | 343 | 279 | 1: 213, 2: 47, 3: 17, null: 2 | budynki produkcyjne, usługowe i gospodarcze dla rolnictwa (193); budynki mieszkalne (76); budynki handlowo-usługowe (3) |

Razem (zliczenia w promieniu 1500 m od węzłów, mogą się nakładać między sąsiednimi miejscowościami): OSM 6145, BDOT 5876. BDOT w całym bbox pętli + 2 km: 14 616 budynków.

## Wnioski (dla D63 „najpierw przejezdne”)

- Typowa zabudowa pętli to **wieś zagrodowa / rozproszona**: przewaga budynków 1-kondygnacyjnych (BDOT: ~72% 1 kondygnacji, ~25% 2 kondygnacje, pojedyncze 3+) — domy jednorodzinne + budynki gospodarcze (BDOT `PRZEWAZAJACAFUNKCJABUDYNKU`: budynek jednorodzinny i budynek gospodarczy dominują).
- Największe skupiska zabudowy przy dk65-01: **Nowosiółki** (739 BDOT w 1,5 km) i **Żółtki-Kolonia** (522) — tam też przechodzi granica miasta (DK65/D64), więc tam D-42/D-43.
- Wzdłuż S8 między węzłami (s8-04…s8-10) zabudowa tylko przy drogach poprzecznych (Babino, Rzędziany, Pajewo) — pas drogowy S8 wolny od zabudowy (zgodne z klasą S).
- Jeżewo Stare/Nowe przy węźle Jeżewo (s8-12): ~330/316 budynków BDOT w 1,5 km, w tym 3-kondygnacyjne (16/19) — zabudowa miejska jak na miasteczko.
- Strefa przemysłowa przy s8-01 (dk65-01): patrz `destinations.json` (tereny `industrial` + hale) — tam budynki przemysłowe/magazynowe, nie mieszkalne.

## UNVERIFIED
- Typy dachów i wysokości budynków (LoD1/LoD2 GUGiK CC BY 4.0) — nie pobrane w tej sesji; do ingest przy budowie kafli.
- `building:levels` w OSM jest rzadkie na wsi (histogramy w tabeli) — BDOT `LICZBAKONDYGNACJI` jest źródłem autorytatywnym.
