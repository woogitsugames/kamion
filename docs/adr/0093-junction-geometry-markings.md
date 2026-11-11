# ADR 0093: Geometria i oznakowanie węzłów z OSM / ortofoto — linie przez łaty, P-21 tylko z odrysowanych wielokątów

Status: przyjęty (world-builder, junctions-r1), 2026-11-11. Wynika z recenzji `docs/reports/visual/REVIEW-2026-11-11-s9-0076.md`
i `REVIEW-2026-11-11-s9-0077.md` (sekcja „Dla ADR 0093”). Powiązane: ADR 0074, 0075, 0076, 0077. Wymaganie właściciela:
„drogi dosłownie jak w OSM, żeby mieszkaniec wiedział, jak jechać”. Dowody: `artifacts/junctions-r1/`.

## Kontekst
- main 8cc25713 był czerwony: `kerb_on_carriageway` 28 > 0 i `skirt:yard_concrete` 4 > 3.
- Oznakowanie powstaje osobno dla każdego łańcucha, między przycięciami skrzyżowań. Łata skrzyżowania (15–45 m przy
  włączeniu łącznicy, cały pierścień ronda między wlotami) była gołym asfaltem — pasy „kończyły się” i „zaczynały”.
- P-21 malowała reguła klinów (ADR 0077) i `hatch: true` na wypełnieniach; kształty nie zgadzały się z ortofoto
  (obła „łza” 17 × 18 m, „muszka”, drabinka 127 m²).
- Wypełnienie 436 m² przy s 610 zalało asfaltem chodnik, trawnik i barierę między ulicą a drogą parkingową.

## Decyzja
0. **Krawężnik pod wypełnieniem jest usuwany z siatki, nie zatapiany.** Przyczyna 28 przypadków: `hero_bridge.apply`
   odbudowuje taśmy łańcuchów wiaduktu Bieżeństwa (z krawężnikami) PO `meshing.cull_sides_on_carriageway`, więc
   krawężniki zatopione 6 cm wracały na oba końce wiaduktu (szare pasy na pasie ruchu s 580–620). Kolejność w
   `pipeline.build` (`GO.build` przed `cull`) jest dobra: `cull` widzi wypełnienie jako jezdnię. Zmiany:
   `build_world` powtarza `cull` po odbudowie taśm hero; `gores.drop_kerbs_in_fills` usuwa każdy trójkąt krawężnika
   (render + kolizja) leżący w obrysie zbudowanego wypełnienia (sam `cull` zostawiał 20 — wymaga jezdni w całym
   pierścieniu 0,30 m); miara `roads_qa.summary.gores.kerb_tris_in_fill` i test `test_no_kerb_under_a_fill` (= 0).
   Wysepki autorskie (`island:`) leżą na jezdni z założenia — `cull` i kontrola `kerb_on_carriageway` je pomijają
   (wcześniej `cull` kasował je w całości), `obstacle_in_lane` nadal pilnuje, że żaden pas w nie nie wjeżdża.
   Ścianki placów: wszystkie przypadki `skirt:yard_*` to ostre szpice wielokąta placu po odjęciu obrysu dróg, węższe niż
   siatka terenu 1 m (bez węzła pod spodem szpic stoi 0,28–0,35 m nad terenem; ich liczba zmieniała się z każdą zmianą
   obrysu dróg). `paved._trim_spikes`: otwarcie morfologiczne 0,5 m z narożnikami „mitre”, tylko szpice ≤ 2 m², cięcie
   nie może rozdzielić placu (numeracja części bez zmian).
1. **Linie przez łaty** (`roads/through_lines.py`, po `drop_overlapping`). Dwa ramiona tworzą parę „na wprost”, gdy ruch
   może wjechać jednym i wyjechać drugim z odchyleniem < 35° (kolejne ramiona pierścienia ronda: < 80°). Linie obu ramion
   na granicy łaty (pasów, osiowa, krawędziowe; goła krawędź jezdni jako kandydat bez farby) są dopasowywane po
   odległości poprzecznej od wspólnej osi (końce łańcuchów spotykają się w węźle OSM; przesunięcia autorskie i z
   `align_forks` liczone z końców łańcuchów), próg 1,9 m, i łączone krzywą trzeciego stopnia ułożoną na siatce jezdni:
   pas ↔ pas — P-1 przerywana; krawędź ↔ pas (pas dochodzi / znika) — P-1; P-4 ↔ P-4 — podwójna ciągła;
   P-7b ↔ P-7b — ciągła 0,24 m, a przerywana P-7a 1/1 m, gdy z tej strony dochodzi ulica boczna (nie rysowana, gdy to
   ramię samo się włącza / odłącza — tam granicą jest klin). Jedno przejście zachłanne na skrzyżowanie: linia ramienia
   ma jedną kontynuację, linia wylotu przyjmuje najwyżej jedną linię pasa i krawędzie klina, połączenia nie mogą się
   przecinać (inaczej dwa wloty rysowały „gwiazdę” kresek). Pary, których osie się krzyżują (prawdziwa tarcza
   skrzyżowania), nie dostają linii, poza pierścieniem ronda.
2. **P-21 wyłącznie z wielokąta odrysowanego z ortofoto**: nowy rodzaj `painted_zone` w `overrides.yaml`
   (`polygon_en` w lokalnych E/N, `stripe_az_deg` albo `chevron_axis`), sama farba: ramka 0,24 m + pasy 0,5 / 1,0 m
   (WORKING_VALUE). Wielokąt samoprzecinający się lub < 1 m² jest odrzucany (`overrides_stale`,
   `tests/gis/test_junction_paint.py`). Reguła klinów nie maluje już nic, klucz `hatch:` usunięty. Farba poza jezdnią
   jest obcinana (liczona w `tris_off_carriageway`); inne oznakowanie w obrysie strefy / wysepki jest wymazywane
   (strzałki i P-13 w całości).
3. **Wysepki i nosy z ortofoto**: `traffic_island` przyjmuje `polygon_en` (ostre nosy tak, jak odrysowane).
   - s 610 (j:n1882887385): usunięte wypełnienia `gore-s610-north-carriageway` (436 m²), `-hatch-north` (144 m², obły
     placek), `-corners` (odrzucane za różnicę wysokości); ramię płn. w537184112 szerokość 9,0 m (pomiar 10,7 m przy
     N −537,6 i −548,2, ~7,5 m przy zebrze N −525; jedna szerokość na krawędź — WORKING_VALUE), między nim a drogą
     parkingową wraca trawnik z krawężnikiem; azyl z kostki z nosem (72 m²) i 4 pola P-21 (53 + 116 + 38 + 38 m²).
   - s 1440 (j:n1847044938, MA-012): pas rozdzielający z kostki z barierą dłuższy o 30 m (nos E −362 N −156 zamiast
     E −388 N −138) jako `traffic_island`; P-21 na lewym pasie łącznicy (159 m²); SE koniec P-21 przed nosem rozjazdu.
4. **Latarnie** (`furniture.clear_narrow_islands`): latarnia z jezdnią w odległości 1,0 m po dwóch przeciwnych stronach
   (przegroda < ~2 m) jest przenoszona na zewnętrzną krawędź jezdni po drugiej stronie wysepki, potem na drugą krawędź
   własnej jezdni, a gdy tam nie ma miejsca (pomost) — usuwana.
5. **Przejścia i strzałki**: przejazd rowerowy (przez węzeł przechodzi tylko `cycleway`) = P-11 (dwa rzędy kwadratów
   0,4 m; wymiary UNVERIFIED względem załącznika nr 2, odczytane z ortofoto), także układany na łacie; dwa węzły
   przejść bliżej niż ich szerokości: ten sam rodzaj → jedno przejście, pieszy + rowerowy → rozsunięte na styk;
   strzałka P-8 tylko w pasie ≥ 2,5 m i gdy mieści się w pasie; linia przycięta przez `drop_overlapping` do < 2 m
   znika, przycięty znak (P-8, P-13) znika w całości.
6. **Narzędzie**: `tools/worldgen/fidelity/planview.py` — widok z góry wygenerowanej nawierzchni i farby obok ortofoto
   0,08 m z siatką metrów (tryb `--ortho-only --grid 5` do odrysowywania, `--outline` = obrys jezdni na zdjęciu).
   Kamery: `Data/Regions/bialystok-industrial-c/junctions_cameras.json` (34: każdy węzeł z góry + oko kierowcy, miejsca
   z filmu właściciela `p0_lamp_putry_eye/top` E −589 N 19,5 i `p0_kerb_merge_eye/top` E −782 N 77,5, `top_s1440`).

## Wynik (build 2026-11-11, `bialystok-industrial-c`)
| miara | main 8cc25713 | po |
|---|---|---|
| `kerb_on_carriageway` (kafel) | 28 | **0** |
| trójkąty krawężnika w obrysie wypełnień | 20 (po samym `cull`) | **0** |
| spójność dróg, suma (kafel / trasa) | 93 / 1 | **65** / 1 |
| ścianki > 0,15 m (suma; `skirt:yard_concrete`) | 6 (4) | **4 (2)** |
| skrzyżowania z liniami przez łatę | 0 | **59** (105 linii pasów, 31 P-7b, 12 P-7a) |
| pola P-21 z reguły / z `hatch:` / z wielokąta ortofoto | 4 / 3 / 0 | 0 / 0 / **6** |
| wypełnienia z override (liczba / m²) | 10 / 1083 | 6 / 385 |
| krawężnik schowany przy wypełnieniach | 691 m (zatopiony) | 552 m (usunięty) |
| P-10 / P-11 / przejścia pominięte | 71 / 0 / 0 | 65 / 6 / 0 |
| strzałki P-8 (pominięte: pas za wąski) | 98 (—) | 79 (19) |
| latarnie na przegrodzie < ~2 m | 5 | 0 (3 przeniesione, 2 usunięte) |
| fidelity trasy: wysepki bez pokrycia / pas w wysepkę / krawędź p50, p95 | 1 / 0 / 0,46, 2,52 m | 1 / 0 / 0,46, 2,52 m |

Liczby „po” z `roads_qa.json`, `road_consistency_qa.json`, `terrain_walls_qa.json`, `streetscape_qa.json`,
`fidelity_qa.json` (logi `artifacts/junctions-r1/logs/b4_*.log`). Testy i kontrola wizualna: sekcja niżej.

## Otwarte (nie zrobione w tej rundzie)
1. s 1440 rozjazd (E −366 N −119): pasmo P-21 3,6 m na jezdni łącznicy i pas z kostki z barierą — łącznica generatora
   jest tam węższa, a jezdnia główna leży wyżej (mur rampy), więc wypełnienie jest odrzucane („no carriageway height”).
   Pełny obrys strefy zapisany w `overrides.yaml` (`s1440-diverge-p21`, pole `reason`). Wymaga zmiennej szerokości
   jezdni. Wysepka 373 m² zostaje jako „bez pokrycia” w fidelity.
2. Krawężnik E −782 N 77,5 (kerb_merge, film właściciela): klin 57 m² odrzucany za różnicę wysokości profili 0,41 m
   (> 0,35 m dla override); ortofoto tylko 0,25 m. Bez P-21. Latarnia z E −774,4 N 77,9 trafiła na drugą krawędź
   własnej jezdni (pas dzielący, E −775,3 N 64,5), nie na zewnętrzną krawędź łącznicy.
3. n10015785253: pas dzielący zwęża się do zera, bo jezdnie generatora są za szerokie (liczba pasów OSM × 3,5 m), a
   nie przez łatę; linie przez łatę są, mediana nie. Zatoka z kostki s 1060–1080 i 5 pasów zamiast 3 + zatoka — to samo
   źródło (jedna szerokość na krawędź OSM).
4. Pierścień MA-010: linie pasów przez łaty są, ale liczba pasów (OSM) < 3 z ortofoto; strzałki, linie zatrzymań w
   pierścieniu, P-21 przy wlotach — nie odrysowane. Przejazd przez pas dzielący Putry N jako osobna nawierzchnia — nie.
5. U-25 (separatory) na s 610 — brak rekwizytu; wzór strzałki kombinowanej P-8 i atlas P-13 — nie ruszane;
   pasy P-21 jako jodełka (`chevron_axis` jest w kodzie, nieużyte) — wszystkie pola ukośne.
6. Farba z reguły klinów przy E 773 N −847, E 792 N −836, E 313 N −597, E −228 N −1006: wyłączona, nie sprawdzona na
   ortofoto (po sprawdzeniu — `painted_zone`).
7. WORKING_VALUE: `MATCH_MAX_M` 1,9 m, `THROUGH_DEG` 35°, `RING_DEG` 80°, pasy P-21 0,5 / 1,0 m, `NARROW_ISLAND_R`
   1,0 m, `SPIKE_OPEN_M` 0,5 m, `FRAGMENT_MIN_M` 2,0 m, szerokość ramienia płn. s 610 9,0 m. UNVERIFIED: wymiary P-11.

## Testy i kontrola wizualna (2026-11-11)
- `pytest tests/gis`: **337 passed, 2 xfailed** (main: 328 passed, 2 failed; +9 testów: `test_junction_paint.py` 7,
  `test_no_kerb_under_a_fill`, `test_no_paint_from_the_gore_rule` zamiast testu `hatch`). Ratchet
  `skirt:yard_concrete` 3 → 2. `route_corridor`: 2394,5 m, 4790 stacji, **0 uskoków, 0 przeszkód**, 0 bez nawierzchni.
- Unity 6000.3.28f1: `import-region` OK (Low 109,7 MB, High 235,6 MB). PlayMode `WorldCRouteTests|WorldCBarrierTests`
  i EditMode: wynik w `artifacts/junctions-r1/STATUS.md` (logi `logs/playmode.log`, `logs/editmode.log`).
- Kamery (34, WorldC, Medium overcast `renders_after/`, Low overcast `renders_after_low/`); pary przed / po z tej samej
  kamery w `artifacts/junctions-r1/pairs/`. „Przed”: dla 13 kamer ADR 0077 — rendery końcowe 0077
  (`artifacts/islands-r10/renders/`); dla pozostałych — `renders_before/`, czyli `_Generated` skopiowany z main na
  starcie zadania, który okazał się importem STARSZYM niż 0077 (pierścień MA-010 jeszcze bez przesunięcia), więc te pary
  nie są dokładnym stanem 8cc25713.
- Obejrzane obok ortofoto (widoki z góry `plan_after/*.jpg` = ortofoto | generator, wycinki `trace/*.jpg`):
  `top_s610`, `au_f_s0600`, `au_f_s0620` (bez szarych pasów krawężnika, jedna linia ciągła, azyl i pola P-21 jak na
  zdjęciu, trawnik między ulicą a parkingiem), `top_s1440`, `au_r_s1380` (pas z kostki do nosa E −362 N −156, P-21 na
  lewym pasie łącznicy, linie przez łatę zamiast 45 m gołego asfaltu), `top_ma010` (linie pierścienia przez łaty,
  P-11 przy zebrze), `top_putry_n`, `p0_kerb_merge_eye`, `p0_lamp_putry_eye` (brak krawężnika / latarni na pasie —
  bez zmian względem 0076), widoki z góry n10015785253 i s 1060 (linie ciągną się przez łatę; mediana i zatoka — otwarte).
- Nie zrobione: ocena `visual-critic` (agent bez prawa tworzenia subagentów) i zrzut z telefonu — dla lidera.
