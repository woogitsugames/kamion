# ADR 0220 — DK65 kafle `dk65-01…05`: elementy przekroju z K1 (rozstaw linii krawędziowych, linie przerywane, zatoki)
Status: Proposed (chmura C, zadanie C4, gałąź `dk65-k1-0220`; bez Unity i bez `Data/raw`), 2026-11-15. Do scalenia przez lidera.
Powiązane: K1 `research/dk65-knyszyn-refs/README.md` (+ `manifest.csv` K1-001…014), ADR 0203 (plan trasy, pikietaż), 0205
(linie krawędziowe klasy < GP przez override), 0207 (kafle 02–05, sprzeczność 7,6 m), 0212 (7,1 vs 6,8 m), 0215 (PR #80,
Ełcka 6,9 m — nie na main), D65 (`docs/11`).

## Kontekst
K1 zmierzył na ortofoto GUGiK 0,1 m (arkusze 2025-05-25) co 0,5–1 km: rozstaw linii krawędziowych 6,0–6,4 m (mediana 6,2,
n = 14 w kaflach 01–05), linie przerywane i zatoki autobusowe. Generator maluje linie (klasa G, tylko override) 0,20 m od
krawędzi jezdni (`EDGE_LINE_INSET_MINOR`), więc rozstaw = szerokość − 0,40 m.

## Decyzja
1. **Pikietaż** (`tools/worldgen/roads/route_km.py`): „km trasy” K1 = długość wzdłuż `variants.A_old_road.polyline`
   planu 0203 (`docs/reports/map/dk65_route_plan.json`, węzły OSM, EPSG:2180) od węzła 3341716402 (Andersa, kafel C),
   rośnie w stronę Knyszyna; ADR 0205/0207 używają tego samego (`tiles[*].km_in/out`). Strona K1 L/P = lewa/prawa w
   kierunku rosnącego km. `km_to_region(tile, km, side, offset)` → x/z regionu (Unity X = E, Z = N), znak strony, `inside`;
   `RouteKm.locate(x, y)` → (km, odsunięcie). Zgodność z punktami K1 (`data/km_points.json`) < 0,05 m; przystanki OSM
   14067837805 → km 12,985 L, 11243685568 → km 14,478 P (jak K1). DK65 km ≈ 170,05 − km trasy (K1, ESTIMATED).
2. **Skąd 7,1 m (0212)**: `knyszyn*` mają `set {lanes 2, lane_width 3.4, edge_strip 0.35}` → jezdnia 7,5 m; linia
   0,20 m od krawędzi → ±3,55 m → **7,1 m**. W kaflach 01–05 (main, `pipeline.build_network`): Ełcka 7,6 m → **7,2 m**
   (z PR #80 6,9 m → 6,5 m), Fasty/Szosa Knyszyńska BDOT 6,5 m → 6,1 m, way 234919333 6,0 m → 5,6 m, most 7,5 m → 7,1 m.
   Stałą `EDGE_LINE_INSET_MINOR` dzielą: dk65-01…05, knyszyn, knyszyn-s, knyszyn-w, dk65-monki-01, bialystok-knyszynska
   (+ dk65-06…11 z 0214); dojlidy/C nie. Jedna stała nie da 6,2 m przy szerokościach 6,0–7,6 m, a w Knyszynie zmierzono
   6,8 m (0212, K1 Obozowa) — **wybrano override per kafel**, stałej nie zmieniam.
3. **Generator — nowy klucz `edge_line_spacing`** (`network.py`, `markings.edge_lines`): rozstaw osi linii (klasa < GP,
   symetrycznie wokół osi jezdni), niezależny od szerokości — działa tak samo z 7,6 m (main) i 6,9 m (#80; wtedy 0,35 m
   asfaltu za linią). Linia nie wychodzi poza jezdnię: oś ≥ `EDGE_LINE_MIN_INSET` 0,12 m od krawędzi (WORKING_VALUE).
   Dane: `dk65-k1-edge-line-spacing` `{edge_line_spacing: 6.2}` na wayach trasy z liniami w każdym kaflu (ten sam wpis po
   obu stronach szwu). Paski ADR 0220 (`artifacts/dk65-k1-0220/evidence/lines_*.json`, 488 bloków 10 m): mediana 6,20 m
   (p10 6,0, p90 6,4); per kafel 6,3 / 6,2 / 6,1 / 6,2 / 6,2. **Wyjątki**: way 234919333 (dk65-01, szew z
   `bialystok-knyszynska` 6,0 m — patrz Otwarte 1) i most 41533342 (brak odczytu: piki to balustrady ~7,6 m).
4. **Generator — `kind: edge_line_dashed`** (`markings.edge_dashed_spans`): `line_en` = oś trasy (punkty co ≤ 10 m),
   `side`, `dash_m`; przypisanie próbek do łańcucha (|lat| ≤ hw + 1,5 m, |cos| ≥ 0,8), linia przechodzi przez skrzyżowania
   (każdy łańcuch dostaje swój odcinek), na zewnątrz ciągła; brak trafienia = `overrides_stale`. Rodzaj farby nadal `P-7b`
   (QA `consistency.PAINT`, fidelity bez zmian). Kreska/przerwa **1,0/1,0 m zmierzona** (`dashes.py`, 8 odcinków: 0,9–1,3 /
   0,5–1,1 m) = P-7a; symbol P-7a vs P-7c i szerokość (0,12 vs 0,24) z 0,1 m/px **UNVERIFIED** — szerokość jak linia ciągła.
5. **Dane = tabela + generator** (`docs/reports/map/dk65_k1_elements.json` → `tools/worldgen/qa/dk65_k1_elements.py`,
   blok między znacznikami `# >>> ADR 0220` … `# <<< ADR 0220` na końcu `overrides.yaml`; `--check` w teście). Zasięgi
   odczytane na wyprostowanych paskach ortofoto WMS 0,1 m (`strip.py`, `lines.py`, `meter.py`, `view.py`; ±0,005 km):

   | id | kafel | km | strona | K1 | uwaga |
   |---|---|---|---|---|---|
   | dashed-km8.81 | 01 | 8,808–8,930 | L+P | 001 | K1: „P przerywana na zjeździe”; pasek: obie |
   | dashed-km9.95 | 02 | 9,945–10,160 | P | 003 | 4 łańcuchy (3 wloty Fasty S) |
   | dashed-elcka | 02 → 03 → 04 | 11,085–13,020 L / –13,005 P | L+P | 005–008 | ciągły odcinek przez 3 kafle (szwy +5 m) |
   | bay-km14.44 (linia) | 05 | 14,440–14,506 | P | 011 | wzdłuż zatoki |
   | inlet-km15.51 | 05 | 15,506–15,518 | P | 013 | wlot polny, którego nie ma w grafie OSM |
6. **Zatoki autobusowe** = istniejący `kind: paved_area` (`yard_asphalt`, `polygon_epsg2180`) z tabeli (km od–do, skosy,
   głębokość od krawędzi jezdni 6,9 m − 0,3 m; nakładkę tnie obrys drogi): **km 12,948–13,010 L** (OSM 14067837805,
   wiata; pełna szerokość do ~8,0 m od osi 12,968–12,997; K1 „~4 m”) i **km 14,440–14,506 P** (OSM 11243685568; ~6,4 m od
   osi; K1 „~3 m”). Krawędź zewnętrzna ESTIMATED ±0,5 m. Wiaty stawia reguła `furniture` z węzła OSM (bez zmian).
7. **Bariery**: K1 ma bariery tylko na km 21,0 i 27,0 (poza 01–05) — nic nie dodano. Km 16,0: K1 „równoległe cienkie linie
   −5,2 / +5,9 m (bariera lub ogrodzenie) UNVERIFIED” — na pasku ciągłe cienkie linie z punktami (słupki?) co kilka metrów
   na 15,94–16,06 km (`evidence/dk65-05_km15.94-16.06_parallel-lines.jpg`); rodzaju nie da się rozstrzygnąć z góry → nie
   wpisane (pytanie: zdjęcie właściciela ze Studziennej przed rondem).
8. **Ul. Ełcka — szerokość NIE zmieniana.** Main: 7,6 m (0207); #80/0215: 6,9 m (D65 „~7 m”). K1: rozstaw linii 6,1–6,4 m,
   asfalt z opaskami 7,0–9,0 m; lider (HANDOVER 14:2x) liczy z K1 ~6,5–6,6 m. Rozstaw 6,2 m jest zgodny z każdą z tych
   szerokości (opaska 0,35 m przy 6,9). **Pytanie do właściciela**: czy jezdnia Ełckiej to 6,9 m (D65) czy ~6,5–6,6 m
   (K1, linie + ~0,15 m)? Rozstrzyga taśma od krawędzi do krawędzi asfaltu na jednym przekroju (np. km 13,5).

## Rozbieżności (K1 / ortofoto / dane)
1. **Way 234919333 (dk65-01, km 8,58–9,23)**: K1 6,2–6,3 m i paski 6,2–6,4 m między liniami, asfalt ~7,9–8,4 m (K1) vs
   override 0205 `width 6.0` (ortofoto 2024 0,25 m) → generator 5,6 m. Linii 6,2 m nie da się położyć na 6,0 m, a zmiana
   szerokości wymaga tego samego wpisu w `bialystok-knyszynska` (`knyszynska-seam-w-xsec`, poza zakresem).
2. Linie przerywane są **dłuższe niż punkty K1**: Ełcka 11,085–13,02 to jeden ciągły odcinek (K1 widział go w 4 punktach);
   K1 km 13,00 „P ciągła” — pasek: P przerywana do 13,005, ciągła od 13,012 (okno K1 30 m łapie oba).
3. K1 km 8,80 „L ciągła” — pasek: L przerywana od 8,808 (okno K1 8,785–8,815 w większości ciągłe).
4. K1 km 12,00 „L nieczytelna” — pasek: L przerywana (cień drzew 12,00–12,07).
5. Klasyfikator pasków widzi też **przerywane poza punktami K1 — NIE wpisane** (do decyzji lidera, `evidence/lines_*.json`,
   `*_candidates.jpg`): dk65-01 L 8,97–9,04, L+P 9,09–9,19, rejon pętli Fasty/Mleczarnia 9,22–9,33 (przejście, wyspy,
   przystanki); dk65-04 L+P ~13,24–13,38 (obejrzane), L ~14,24–14,30; dk65-05 L 14,70–14,99, 15,18–15,41, 15,76–15,97
   (nieobejrzane, możliwy cień).
6. Oś OSM vs linia środkowa: K1 C −0,5…+0,6 m (mediana ~−0,2), paski +0,0…+0,4 m — w tolerancji, `center_offset` nie ustawiany.

## Walidacja (chmura, bez `Data/raw`)
- `tests/gis/test_dk65_k1_0220.py` **18/18**: pikietaż (długość planu, 20+ punktów K1 < 0,15 m, kafle K1, szwy, strona
  z przystanków OSM, ramka x/z), generator na syntetycznej drodze (rozstaw 7,6/6,9/6,5/6,0 m, bez klucza = stara reguła,
  odcinek przerywany 20 kresek 1 m tylko po jednej stronie, kierunek `side`, stale), dane (blok = tabela, rozstaw 6,2 ± 0,05
  na ≥ 20 sekcjach trasy, 14 odczytów K1 w ±0,25, 11 odcinków bez stale na łańcuchach trasy, zatoki po stronie przystanku).
- Pokrycie odcinków (`build_network` + `edge_dashed_spans`): 01: 122+122 m, 02: 215 + 711+711 m, 03: 484+484 m,
  04: 740+725 m, 05: 66 + 12 m; 0 stale; overrides 01–05: 0 stale.
- Pełny `pytest tests/gis`: **1280 passed, 48 skipped, 3 xfailed**; jedyny fail `test_road_fidelity::test_report_not_stale` — raport fidelity C ma hash `markings.py`/`network.py` (zmiana kodu) → lider: `fidelity/run.py` (wymaga `Data/raw`). `tools/worldgen/roads/tests` 4/4. Poprawiony `test_edge_lines_0205` (`o.get("set", {})` — wpisy `kind` nie mają `set`).
- **Nie wykonano**: `build_world`, import, kamery kontrolne, pętla wizualna (zasada 4 — do lidera), pomiar telefonu.
  Budżet (policzone z kodu, nie zmierzone): linia ciągła = 2 trójkąty / 2 m, przerywana 1/1 m = 2 trójkąty na kreskę co
  2 m → ta sama liczba trójkątów; części łączone w `build_world.assemble` po (chunk, warstwa, materiał) → draws bez zmian.
  Zatoki: 2 płaty `yard_asphalt` (223 i 179 m² wielokąta przed przycięciem obrysem drogi, materiał już używany w regionach) — draws ±0–1 na chunk, do pomiaru.

## Otwarte
1. Way 234919333: decyzja lidera — szerokość ~6,6 m (= 6,2 + 2 × 0,2) w **obu** kaflach `dk65-01` i `bialystok-knyszynska`
   + `edge_line_spacing 6.2`, albo zostaje 5,6 m.
2. Szew `dk65-05`/`dk65-06` (way 1560819273, gałąź 0214): `dk65-06` musi dostać ten sam wpis `edge_line_spacing: 6.2`,
   inaczej na szwie skok linii 6,2 → 7,2 (6,5 z #80) m. Analogicznie DK65 dalej (6,0–6,4 m w K1 dla 06–11) — osobne zadanie.
3. Kandydaci z Rozbieżności 5; symbol P-7a/P-7c; zatoki: kształt krawędzi (krawężnik? peron?) i materiał — render + zdjęcie.
4. Zatoka jako `paved_area` stoi za poboczem/rowem z reguły wiejskiej — możliwy próg lub pas trawy między jezdnią a zatoką;
   do obejrzenia na renderze (kamera nad km 12,98 L i 14,47 P). Jeśli źle — następny krok: poszerzenie jezdni odcinkowo.
5. Szerokość Ełckiej (Decyzja 8) — pytanie do właściciela.

## Odtworzenie
```
uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/strip.py 12.27 14.37 <out>        # paski WMS 0,1 m
uv run --project tools/worldgen python artifacts/dk65-k1-0220/tools/lines.py <out>/strip_*.npz <out>/lines.json
uv run --project tools/worldgen python tools/worldgen/qa/dk65_k1_elements.py                         # tabela -> overrides
uv run --project tools/worldgen python -m pytest -q tests/gis/test_dk65_k1_0220.py
```
