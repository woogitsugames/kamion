# ADR 0272 — Pobocze dróg bez krawężnika jako dane: reguła wg klasy, tagi OSM `shoulder`, nadpisanie per odcinek

Status: Proposed (agent world-builder, chmura D r4, gałąź `rural-xsec-0272`), 2026-11-15. Do scalenia przez lidera.
Powiązane: ADR 0204 (profil szlakowy w kaflu bez chodników), 0205 (linie krawędziowe klasy < GP przez override), 0207
(„Otwarte 5”: krawężnik zamiast pobocza), 0212 („DW671 we wsi z krawężnikami z reguły”), 0214 r3 (asfalt 8,6 m wobec
7,1–7,5 m), 0215 / D66 (Ełcka 6,6 m), 0217 („Otwarte 6”: przejazd DW671), `docs/reports/VERIFY-2026-11-15-pr80-pr82.md`,
`docs/reports/REVIEW-2026-11-15-s22-0217-visual.md` P1-4.

## Kontekst — dwa zgłoszenia
1. **Ełcka / Studzienna (dk65-02…05)**: asfalt w grze 8,6 m = 6,6 m (D66) + 2 × 1,0 m `S.PAVED_SHOULDER`. Pomiary z raportu
   VERIFY (ortofoto 0,1 m, `pr80/ortho/elcka_xsec.json`): **asfalt 6,5–7,1 m, linie krawędziowe 6,1–6,4 m od siebie**; w grze
   linie 6,2 m (dobrze), asfalt o ~1,5–2 m za szeroki.
2. **DW671 przy przejeździe linii 38 (dw671-tykocin-01)**: w grze krawężniki i wpusty, na ortofoto / Mapillary pobocze
   gruntowe, linia krawędziowa, bariery, słupki prowadzące (REVIEW P1-4; kadry `rail-xing-from-ne` nie są w repo —
   `artifacts/` poza gitem; obejrzane zamiast nich ortofoto WMS, niżej).

### Jak było (zbadane w kodzie)
- `network.assign_sides`: krawędź **bez krawężnika** (`kind RURAL`) tylko gdy środkowa sekcja łańcucha ma klasę A/S/GP/G
  **i** `maxspeed ≥ 70` (`S.RURAL_MIN_SPEED`) i nie ma chodnika przy krawężniku; wszystko inne — `URBAN`: krawężnik 0,13 m
  (+ trawnik 1 m albo chodnik). DW671 nie ma w OSM `maxspeed` → graf wpisuje domyślne 50 (`src: default, conf: low`) →
  krawężnik. Drogi gruntowe i wiejskie L/Z też dostają krawężnik (poza zakresem, „Otwarte”).
- `network.side_profile(RURAL)`: zawsze 1,00 m asfaltu (`PAVED_SHOULDER`, WORKING_VALUE) + 0,75 m żwiru (`SHOULDER_W["GP"]`)
  + rów — bez względu na klasę i liczbę jezdni. Stąd 6,6 + 2 × 1,0 = 8,6 m.
- Wpusty (`decals.gullies`): już tylko przy krawężniku (`URBAN`/`ISLAND`, h ≥ 0,08 m). Włazy w jezdni
  (`fab_details.drainage`): co 90 m na każdej jezdni asfaltowej, także bez krawężnika.
- Bariery: tylko reguła nasypu > 2 m i obiekty; słupków prowadzących U-1a generator nie ma. Linie krawędziowe: A/S/GP z
  opaską z reguły, niżej tylko przez `edge_lines` (ADR 0205), oś 0,20 m od krawędzi (`EDGE_LINE_INSET_MINOR`).
- OSM `shoulder*` nie było czytane (K1: na trasie tych tagów nie ma). BDOT10k w grafie: `klasa`, `material`, `width_m`
  (SZEROKOSCNAWIERZCHNI = cała nawierzchnia) — atrybutu pobocza nie ma.

### Przepisy (teksty czytane 2026-11-15)
- **Dz.U. 2022 poz. 1518** (rozp. MI z 24.06.2022, przepisy techniczno-budowlane dróg publicznych): **obowiązuje** od
  21.09.2022, **tekstu jednolitego nie ma**; jedna nowelizacja **Dz.U. 2025 poz. 1352** (od 22.10.2025) — w § 23 zmienia
  brzmienie ust. 4 zd. 2 i skreśla w ust. 10 pkt 5 słowa „jeżeli nie zaprojektowano części pobocza o nawierzchni twardej”;
  szerokości bez zmian. Źródło: `api.sejm.gov.pl/eli/acts/DU/2022/1518` (status, „Akty zmieniające”) + `text.html`.
  - § 23 ust. 1: droga zamiejska jednojezdniowa — pobocza po obu stronach. § 4 pkt 3 / 24: droga zamiejska = nie ulica.
  - § 23 ust. 3: A/S pas awaryjny + część gruntowa; GP opaska zewnętrzna + część gruntowa; **G/Z opaska + część gruntowa
    albo w całości gruntowe**; **L/D w całości gruntowe**. Ust. 4: na ulicy jak na zamiejskiej; inne rozwiązania przy
    wyniesionym krawężniku i drodze dla pieszych.
  - § 23 ust. 6: pas awaryjny A 3,00 m (≥ 2,50), S 2,50 m (≤ 3,00). Ust. 7: opaska GP 0,75 m (≥ 0,50; dwujezdniowa do
    1,50), G/Z 0,50 m.
  - § 23 ust. 10: część gruntowa nie węższa niż 1,25 m (≥ 0,75) przy pasie awaryjnym; 0,75 m (≥ 0,50) przy opasce;
    **G bez części twardej 1,25 m (≥ 0,50)**; Z 1,00 m (≥ 0,50); L/D 0,75 m (≥ 0,50).
- **Zał. 2 do rozp. z 3.07.2003 o znakach i sygnałach** (t.j. **Dz.U. 2019 poz. 2311**; nowelizacje po t.j.: Dz.U. 2021
  poz. 438 i 2066, 2022 poz. 2377, 2026 poz. 132 — tej ostatniej nie czytałem, UNVERIFIED czy dotyka pkt 2.2.2),
  **pkt 2.2.2 „Linie krawędziowe”** (s. 544–549): stosuje się „przede wszystkim do wyznaczenia krawędzi jezdni bez
  krawężników ulicznych”; P-7a/P-7b 0,24 m na A/S, drogach z twardym poboczem lub opaską, z numerem międzynarodowym i
  dwujezdniowych; na pozostałych dopuszcza się P-7c/P-7d 0,12 m; ciągłą (P-7b/P-7d, pkt 2.2.2.2) m.in. tam, gdzie
  szerokość pobocza uniemożliwia zatrzymanie pojazdu poza jezdnią, na odcinkach z barierami i z liniami P-4. Położenie
  linii jest tylko na rys. 2.2.2.1 (rysunek, bez liczby w tekście) → **odsunięcie 0,20 m zostaje WORKING_VALUE**; pomiar
  niżej daje 0,25–0,30 m od krawędzi asfaltu do osi linii.

### Pomiary własne (ortofoto GUGiK WMS `StandardResolution`, 15.11; profil ⟂ do osi grafu, mediana z ±6 m, ±0,2 m)
| droga (waye) | przekroje | asfalt [m] | linie krawędziowe [m] | pobocze |
|---|---|---|---|---|
| Ełcka / Studzienna, dk65-04/05 (1024956365, 41533343, 1243220441, 1024956364, 1399803717) | 10 czystych z 21 | 6,2–7,35, **mediana 6,75** | 6,0–6,35, mediana 6,2 | piasek / żwir 0,7–1,2 m, bez krawężnika |
| Szosa Knyszyńska, dk65-01/02 (234919333, 396566354) | 9 | 6,65–7,4, mediana 6,95 | 6,2–6,35 | żwir 0,5–1 m (K1 podawał „asfalt 7,9–8,4” — z jasnym żwirem) |
| DW671, dw671-tykocin-01 (145989268, 286989055) | 10 czystych z 14 (3 w cieniu) | 6,7–7,25, **mediana 6,85** (BDOT 6,5 / 7,0) | 6,85–6,9 przy przejeździe; widoczne w 6 z 10 | trawa / grunt od krawędzi asfaltu, bez krawężnika, bez wpustów; przy przejeździe bariery 0,5–1 m za krawędzią |
Narzędzia i paski: `artifacts/rural-xsec-0272/` (`xsec.py`, `orto_*_strips.jpg`, `*.json`; poza gitem).

## Decyzja
1. **Reguła jako dane: `tools/worldgen/roads/xsec_rules.yaml`** (czyta `roads/xsec.py`). Kolejność dla każdej strony
   sekcji: nadpisanie autorskie → tagi OSM → reguła klasy.
   - `open_road` — dotychczasowy warunek krawędzi bez krawężnika (klasy A/S/GP/G, ≥ 70 km/h), przeniesiony z kodu bez
     zmiany wartości.
   - `shoulder_rules` (pierwsze dopasowanie; klucze `class`, `carriageway: single|dual`, `highway`, `ref` regex):
     | reguła | pobocze | asfalt poza `width` | część gruntowa | status |
     |---|---|---|---|---|
     | G jednojezdniowa | gruntowe | 0,08 m | 1,00 m | MEASURED (Ełcka, Knyszyńska; § 23 ust. 3 pkt 3, ust. 10 pkt 3) |
     | Z jednojezdniowa | gruntowe | 0,05 m | 1,00 m | SOURCED (§ 23 ust. 10 pkt 4), dziś tylko przez override/tag |
     | L, D | gruntowe | 0,05 m | 0,75 m | SOURCED (§ 23 ust. 10 pkt 5), dziś tylko przez override/tag |
     | pozostałe (A, S, GP, G dwujezdniowa) | utwardzone | 1,00 m | 0,75 m | WORKING_VALUE — bez zmiany |
     `width` generatora to cała nawierzchnia (BDOT / ortofoto), dlatego pobocze gruntowe nie dokłada asfaltu; 0,08 m =
     (6,75 − 6,6) / 2 z pomiaru, `min_paved_m` 0,05 m chroni przed zdegenerowanym paskiem.
   - `osm_shoulder`: `shoulder=yes|both|left|right` → strona bez krawężnika; `shoulder:width` (domyślnie 1,00 m,
     WORKING_VALUE); `shoulder:surface` z listy gruntowych → pobocze gruntowe, inaczej utwardzone. Tagi dodane do
     `osm_extract.ROAD_TAGS` i `roadgraph` (trafią do grafu przy następnym `build_region`; zmienia klucz cache OSM).
   - `drainage`: włazy w jezdni nie powstają tam, gdzie obie krawędzie to pobocze gruntowe (część twarda ≤ 0,25 m);
     wpusty były i są tylko przy krawężniku.
2. **Nadpisanie per odcinek** (`overrides.yaml`, przeżywa reimport): `set: {shoulder: ground | paved | kerb}` albo
   `{shoulder: {kind, paved_m, ground_m, ditch_m}}`, także `shoulder_left` / `shoulder_right` (kierunek krawędzi OSM).
   `ground`/`paved` zdejmuje krawężnik także przy 50 km/h, `kerb` zostawia go na drodze szybkiej; `ditch_m: 0` = płaski pas
   zamiast rowu. Chodnik przy krawężniku nadal wygrywa (krawężnik zostaje).
3. **Implementacja bez zmiany topologii siatki**: szerokości pobocza jadą w kodzie `mat` strony (`0` = profil dotychczasowy
   → regiony bez dopasowania mają identyczne tablice stron), `side_profile(RURAL)` czyta je przez `xsec.decode`.
4. **Dane regionów**: `dw671-tykocin-01/overrides.yaml` — `dw671-ground-shoulder` (waye 145989268, 286989055: pobocze
   gruntowe, płytka mulda 0,2 m WORKING_VALUE, linie krawędziowe obustronne) i `dw671-ground-shoulder-crossing` (krawędź
   90 m z przejazdem: to samo, bez muldy). Ełcka (dk65-02…05) nie wymaga nowych wpisów — działa reguła klasy G.
5. **Styk z przejazdem (ADR 0217, nie zmieniam `rail.py` ani wpisu `rail-crossing-dw671-line38`)**: etap toru liczy strefę
   płyt, długość ramion i odsunięcie urządzeń z obrysu drogi. Pobocze i trawa profilu bez krawężnika też są obrysem, więc
   `build_world` przekazuje torowi obrys bez materiałów `shoulder_gravel` / `verge_grass` (`RAIL_ZONE_EXCLUDE_MATS`).
   Drogi z krawężnikiem nie mają tych materiałów w obrysie — ich przejazdy bez zmian. Dla DW671: szerokość drogi na
   przejeździe 7,4 m (jezdnia + 2 krawężniki) → 7,16 m (jezdnia + 2 × 0,08 m), ramiona 4,2 → 4,08 m, płyty nadal
   `panel_margin_m` 1,5 m poza asfalt; krawężnika przez płyty i szyny (REVIEW P0-1) na tym przejeździe już nie ma.
   Urządzenia stoją na pasie pobocza (z = raster drogi), bez rowu w poprzek toru.

## Skutki
- **Ełcka dk65-02…05**: asfalt 8,6 → **6,76 m** (zakres ortofoto 6,5–7,1), żwir 0,75 → 1,00 m, linie bez zmian (6,2 m).
  Trójkąty siatki dróg bez zmian (ta sama topologia; dk65-04 +2 w kolizji); wpusty bez zmian (są przy ulicach wsi).
- **dw671-tykocin-01** (siatka dróg na płaskim NMT, `meshstat.py`): `road` 110 984 → 124 956 (+13 972: krawężnik −6 932,
  asfalt +3 570, żwir +3 570, trawa profilu +13 764), `collision` 40 160 → 45 542, wpusty 490 → 392 (−196 trójkątów
  oznakowania). Czyli **więcej, nie mniej** geometrii — profil bez krawężnika ma 5 pasów zamiast 3. Najcięższa kamera
  kafla ma 1 053 777 trójkątów High (`route_s0489`), więc nawet cały przyrost w jednym kadrze zostaje daleko pod 2 mln.
  Draw calle: materiały `shoulder_gravel` / `verge_grass` już są w kaflu (bez nowych materiałów).
- **C i Dojlidy: bez zmian** — tablice stron identyczne (skrót SHA przed/po: C `b7a4b57000c0f374`, Dojlidy
  `6f57fd627368fde6`), siatka dróg na płaskim NMT identyczna co do trójkąta w każdym materiale, wpusty 772 / 999.
- **Inne regiony przy następnej regeneracji** (reguła G jednojezdniowa ≥ 70 km/h; plików tych kafli nie dotykałem, lista z
  `rways.py` na grafach z gita): dk65-01 i bialystok-knyszynska (Szosa Knyszyńska, way 234919333 — zmierzona wyżej),
  dk65-06…11 (waye 208187096, 27718745: asfalt 8,6 → 6,76 m przy pomiarze 7,1–7,5 m z ADR 0214 r3), knyszyn, knyszyn-s,
  knyszyn-w, dk65-monki-01 (DK65: asfalt węższy o 2 × 0,92 m). bialystok-maczka i bialystok-kleeberga: bez zmian.
- **bialystok-knyszynska, Szosa Ełcka (way 303739903)**: reguła zwęziłaby asfalt z 8,5 do 6,66 m, a ortofoto pokazuje
  ok. 9 m (1 przekrój wolny od zatok, 4 inne 11–14 m) → wpis `szosa-elcka-keep-paved-shoulder` zostawia dotychczasowy
  profil (`confidence: low`, do pomiaru).

## Walidacja
- `tests/gis/test_rural_xsec_0272.py` (30): klasa → pobocze; zakresy § 23 ust. 10; tagi OSM; override; profil bez
  krawężnika o tej samej topologii; sieć syntetyczna (G 90 km/h: asfalt 6,76 m; droga 50 km/h z krawężnikiem do czasu
  override / tagu); Ełcka w dk65-02…05 z grafów w gicie (mediana 6,76 m, w 6,5–7,1); DW671: > 93 % stacji bez krawężnika,
  krawędź przejazdu płaska, żaden wpust przy poboczu, strefa toru = jezdnia + 0,16 m; C i Dojlidy bez zmian; Szosa Ełcka w bialystok-knyszynska bez zmian.
- Podgląd z góry siatki (płaski NMT) obok ortofoto: `artifacts/rural-xsec-0272/xing_triptych.jpg`,
  `elcka_triptych.jpg`. To nie jest render kamer kontrolnych — Unity w chmurze nie ma; kamery do obejrzenia przez lidera
  i `visual-critic` niżej.

## Otwarte
1. Rendery kamer kontrolnych i zrzut z telefonu po regeneracji (lider): `rail_xing_from_ne`, `rail_xing_close_ne`,
   `rail_xing_top`, `dw671_south_junction_approach` (dw671); `top_mid` / `drive_*` (dk65-03…05).
2. Materiał pobocza: `shoulder_gravel` to ciemny żwir; na DW671 ortofoto pokazuje trawę / grunt do samej krawędzi —
   wariant „pobocze trawiaste” do zrobienia w materiałach.
3. Bariery stalowe przy przejeździe (ortofoto: 4 odcinki) i słupki prowadzące U-1a — generator ich nie ma; nie dodawane
   (przy przejeździe to zakres 0217 / #102, U-1a wymaga nowego prototypu).
4. Narożniki skrzyżowań drogi bez krawężnika z ulicą z krawężnikiem zostają krawężnikowe (reguła `_emit_strip`); pas
   żwiru kończy się tam prostopadłym ścięciem (widać na `xing_triptych.jpg` przy wlocie na NE).
5. DW671 way 70329870 (północ kafla, wspólny z knyszyn-w) i ulice wsi / drogi gruntowe z krawężnikiem — bez pomiaru, bez
   zmiany. Drogi gruntowe z betonowym krawężnikiem są w każdym kaflu (także C: 1,97 km stron) — osobne zadanie z
   profilem bez rowu.
6. Pas awaryjny A/S: 1,0 m wobec 2,5–3,0 m z § 23 ust. 6 — bez zmiany (jezdnie S8/S19 mają własne `width`; do pomiaru).
7. `dk65-01`: `width: 6.0` na Knyszyńskiej da asfalt 6,16 m przy pomiarze 6,65–7,4 m (linie 6,2–6,35 m) — do wyrównania
   z D66 (6,6 m) w tym kaflu.
8. Linia wąska ciągła to wg pkt 2.2.2 P-7d; generator nazywa ją nadal `P-7b` (tylko etykieta, szerokość 0,12 m poprawna).
