# ADR 0170 — horyzont i las (pas 6BC0), zieleń przy kamerze (follow-up recenzji 0163)

Status: PROPOSED na gałęzi `horizon-0170` (2026-11-13, s17); nie scalone. Baza: `main` 3a60019ff, świat bazowy i „po”
zbudowane w tym samym worktree. Telefon: NIE mierzony (lider). Recenzja `visual-critic`: do wykonania przez lidera
(subagent nie uruchamia subagentów).
Źródła: recenzja `docs/reports/visual/REVIEW-2026-11-13-s17-0163.md` (P1 horyzont, P1 karty przy kamerze, P2 tuja,
P2 świerk, P2 `p07_b`), ADR 0163 („Otwarte”), `research/g7-street-greenery/README.md` (G7), D51.

## Problem

1. Pas drzew BDOT `2BE4B432-6BC0` (zadrzewienie, liściaste) na zachód od E ≈ 220 zasłaniał bloki Białostoczka w kadrach
   303305168125936 / 320215796381417 / 454716650857984. Generator dawał klasie domyślne 9–19 m (liściaste) i 8 % sosen
   14–24 m w siatce 6 m; z 200–300 m widać to jako ścianę HLOD z wystającymi płaskimi koronami sosen („pinie”).
2. Korona tuż przy kamerze (`g7_p03_a`, `g7_p07_b`) to płaska ściana jednej karty: na Low wariant lite (2–3 karty, bez
   rdzenia); świerk kitu to trzy karty bez bryły (14 trójkątów).
3. Żywopłot tui 2,0–2,5 m ledwo wystaje nad płoty 1,6–1,8 m (`g7_front_thuja_1/5`).
4. `g7_p07_b`: po 0163 znikł gęsty żywopłot za siatką — regresja?
5. Świerk kitu z daleka czyta się jak blady, półprzezroczysty stożek (s16b P2).

## Decyzja

1. **Nowy rodzaj `authored_overrides`: `kind: forest_stand`** (`vegetation.forest_stands`, klucz = id BDOT bez sufiksu
   części, przeżywa reimport, brak celu → `forest_stands.stale` w `streetscape_qa.json`): `height_m [lo, hi]` drzew
   okapu (zastępuje `HEIGHT[gatunek]`; pas brzegowy zachowuje swój mnożnik 0,6), `mix` (zastępuje `MIX[kategoria]`),
   `spacing_m`, `emergent {share, height_m}` (pojedyncze wyższe drzewa, wybór haszem pozycji; w regionie nieużywane). Strumień losowy innych
   poligonów bez zmian.
2. **`bdot-forest-6bc0-young-broadleaf-stand`** (`overrides.yaml`): okap 6,5–11 m, siatka 4,5 m, brzoza 0,40 / klon 0,28 /
   olsza 0,24 / lipa 0,08, bez drzew wystających. Pomiar: Mapillary 454716650857984 (2024-07-26, ten sam sezon co ortofoto
   2024-05-27): wierzch okapu 0,3–1,0° nad horyzontem w odległości 215–300 m od kamery (z 146,6 m, 39 px/°) =
   147,9–151 m n.p.m. przy gruncie 138–142 m → 7–11 m (± 1,3 m na ± 0,3° horyzontu); bloki wystają górnymi ~60 %.
   Ortofoto (`artifacts/horizon-0170/ortho_belt_all.jpg`): zwarty okap drobnych koron, samosiew liściasty na dawnej
   piaskowni, bez koron iglastych. Udziały gatunków i siatka: WORKING_VALUE (klon zastępuje klon jesionolistny, olsza —
   wierzbę / osikę: biblioteka ich nie ma).
3. **Drzewostany „liściasty” bez sosny** (`vegetation.MIX`, `make_trees.FOREST_MIX`: brzoza 0,36 / olsza 0,26 / klon
   0,22 / lipa 0,16; było 8 % sosny). Sosny 14–24 m stały nad każdym liściastym drzewostanem jako płaskie korony.
   **HLOD `broadleaf` wypieczony ponownie** (`make_trees.py -- --reuse-bakes --rebake-forest broadleaf`, nowa flaga):
   `forest_edge_broadleaf(.png/_n.png)`, `forest_canopy_broadleaf.png`. `trees.glb`, `trees_lod2.glb`, impostory,
   pozostałe miksy i `trees_meta.json` — bit w bit bez zmian (sprawdzone sha1 po wypieku do katalogu roboczego).
   Ściana HLOD skaluje się lokalną wysokością drzew (bez zmian w `forest_hlod.py`), więc pas 6BC0 jest niższy także
   z daleka.
4. **Korony przy kamerze.** (a) Drzewo ogrodowe lite przy ulicy (`near`, Low / Medium): + ciemny rdzeń i dwie karty
   barków (16 trójkątów; pokroje zwarte, brzoza bez zmian). (b) Świerk kitu: + ciemny stożek-rdzeń 12 trójkątów wewnątrz
   trzech kart (0,36 połowy szerokości karty, okluzja 0,44), obie warstwy. Reguły odsunięcia nie wprowadzono: korony
   nad płotem są na zdjęciach G7 (P07, P11).
5. **Tuja 2,4–3,6 m, narożnik do 4,0 m** (było 2,0–2,5 / 3,0). Ponowny odczyt dwóch zdjęć, na które powołuje się G7 #19:
   G7-P11 — tuje ~2,3 wysokości płotu sztachetowego 1,5 m ≈ 3,5 m; G7-P12 — ściana 2,5 m rosnąca do ~3,0 m na narożniku
   (linia stropu domu za nią). WORKING_VALUE (± 0,5 m). Przekrój High dostał wiersz na 0,21 h (wiersz gałązek atlasu
   nadal ~1 : 1).
6. **Świerk — paleta i alfa** (`plot_kit._spruce_card`): ciemniejsza, bardziej nasycona zieleń niebieskawa (cień
   13/24/19, światło do 46/70/58; G7-P11 / P12: świerki ciemne, nieprzezroczyste), nieprzezroczysty korpus do 0,74
   obrysu (było 0,62 — cienki ząbkowany brzeg tracił pokrycie alfa w mipach).
7. **`g7_p07_b` — nie regresja.** Kwota frontów 0163 dała tej posesji rodzaj z `garden_plan.by_plot` (nowe pole
   raportu) — patrz „Wyniki”; zdjęcie G7-P07 pokazuje po tej stronie niski mur z krzewami do wysokości płotu, nie
   zieloną ścianę 1,8 m sprzed 0163.

## Wyniki

Build 2 = stan gałęzi (build 1 miał 2 % drzew 14–19 m w pasie 6BC0: pojedyncze drzewo podnosiło okap HLOD w „namiot”
w kadrze 303305 — usunięte z override; rdzeń świerka 0,5 / okluzja 0,30 czytał się jak czarny latawiec → 0,36 / 0,44;
rdzeń korony lite 0,26 → 0,42).

- **Pas 6BC0** (`streetscape_qa.json` → `vegetation.forest_stands`): 1078 drzew okapu (było 536 przy siatce 6 m),
  mediana 8,7 m, maks. 11,0 m (było: okap 9–19 m, najwyższe drzewo 23 m), `stale` 0. Kąt elewacji wierzchołków drzew w
  azymucie bloków ≥ 22 m (± 1,5°), p90 per blok, `artifacts/horizon-0170/geom.py` (dachy bloków: 1,3–3,7°):
  454716 — 0,1–0,9° (było 0,2–1,9°); 320215 — 0,2–1,4° (było 0,7–2,4°); 303305 — 1,1–1,8° (było 1,4–3,0°).
- **Sosny w drzewostanach liściastych** regionu: 3785 → 1118 (zostaje tylko podszyt 3–7 m w `las`).
- **Tuja**: 24 posesje, 331 m, wysokości 2,46–3,47 m (było 2,0–2,5 m).
- **`g7_p07_b`**: posesja `bdot:2BE4B431-B201…` ma w `garden_plan.by_plot` rodzaj `low` (pas niskich krzewów 32,3 m za
  siatką) — zgodnie z kwotą 0163 (niskie najpierw za płoty przezierne) i ze zdjęciem G7-P07; nie regresja.
- **Budżet** (edytor, clear, 129 kamer, baza i „po” z tego samego worktree; `artifacts/horizon-0170/compare-{Low,High}.tsv`):
  `drawsEst` **+0 na każdej kamerze** Low i High (trasa Low 21 338 → 21 338, High 35 880 → 35 880); trójkąty maks.: trasa
  Low **+0,51 %** (`g3b_rondo_put_above`), High +0,44 % (`putry-above`); kamery G7 Low +0,89 %, High +1,28 %. Draws
  instancjonowane (rekwizyty + drzewa): suma trasy Low 11 561 → 11 563, High 22 172 → 22 154; pojedyncze kamery trasy
  Low +1…+3 (22 kamery w górę, 23 w dół — inne komórki / prototypy instancji po zmianie gatunków i zagęszczeniu pasa,
  nie nowe grupy) — do sprawdzenia na telefonie, jak w 0163.
- Drzewa ogrodowe kitu: High 20 644 trójkąty (0163 build 6: 19 264), Low 12 698 (7366).
- **Testy**: `pytest tests/gis` 1062 passed + 4 dopasowane do tego ADR (rdzeń świerka, wysokość tui, limit trójkątów Low
  12 000 → 13 500, `fidelity_qa` po zmianie `overrides.yaml`) — ponowny przebieg tych plików zielony; nowy
  `tests/gis/test_horizon_0170.py` (7 testów). EditMode 514 / 515 passed, 1 skipped (`artifacts/tests/editmode-20261113-173939.xml`).
- **Pary** (`artifacts/horizon-0170/pairs/`): `horizon_crop_{Low,High}_*` (przed = świat 0163 build 6, render z main
  `artifacts/veg-0163/after6_hz`; „po” = build 2), `horizon_*` (zdjęcie | przed | po), `pair_g7_*` (baza | po, Low i High).
  Uwaga: baza w tym worktree została zaimportowana już z nową teksturą `forest_edge_broadleaf` (kolejność kroków);
  statystyk to nie zmienia, a pary horyzontu „przed” biorą dlatego render z main.

Ocena własna (do weryfikacji przez `visual-critic`): pkt 1 osiągnięty w 454716 i 320215 (bloki nad pasem, okap zwarty,
bez „pinii” w pasie); w 303305 bloki widoczne w ~połowie (kamera niżej i bliżej). Pkt 2 — poprawa częściowa: korona
i świerk mają ciemny środek, ale karta 2 m od kamery nadal jest płaszczyzną (`g7_p07_b` Low: rdzeń widać jako ciemną
bryłę pod kartą). Pkt 3 i 5 — tuja jest ścianą nad płotem (`g7_front_thuja_2/5`), świerk ciemny i kryjący.
Przegląd M51 (`REVIEW-2026-11-13-s17-mistral-r8-p10.md` §5): `crowns.geojson` z PR 49 nie jest tu używany — las to
powierzchnia poligonu BDOT + pomiar ze zdjęcia / ortofoto, nie punkty koron.

## Otwarte / WORKING_VALUE

- Wysokość pasa 6BC0 z jednego zdjęcia (± 1,3 m); GUGiK NMPT / „Modele 3D drzew” nie są pobrane — po ingestii zastąpić
  pomiarem. Pozy kadrów 303305 / 320215 (2019) mają `pose_confidence: B`.
- Prototypy biblioteki (`make_trees.py`: kępy liści na gołym pniu) bez zmian — pojedyncze drzewa przydrożne i pas
  brzegowy lasu nadal je pokazują; pełna przebudowa prototypów to osobne zadanie (budżet trójkątów całego świata).
- Udziały gatunków liściastych po usunięciu sosny: WORKING_VALUE.
- Karta korony ≤ 3 m od kamery pozostaje płaszczyzną (pkt 2 częściowo): pełne rozwiązanie = geometria gałęzi w
  wariancie bliskim albo reguła odsunięcia — osobne zadanie.
- Koniec ulic (`g7_front_broadleaf_1`, `st_skidelska_2`): drzewostany iglaste / mieszane nadal z prototypów sosny.
- Low: przekrój tui rozciąga wiersz gałązek w pionie do ~2,8× (było ~1,9×) — bez dodatkowych trójkątów.
- Telefon (A16 Low): nie mierzony.
