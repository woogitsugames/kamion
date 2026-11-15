# ADR 0208: kafel `bialystok-knyszynska` (−3,0, dwa powiaty) i mur z balustradą na pasie niskiego pomostu (maczka)

Status: PROPOSED (2026-11-15, agent `bialystok-t3-0208`, gałąź `bialystok-t3-0208`)

## Kontekst
- D64: trasa ciężarówki Białystok → Knyszyn (wariant A, ADR 0203). Kafle miasta: `bialystok-maczka` (0203),
  `bialystok-kleeberga` (0206), i ostatni — **`bialystok-knyszynska`**, siatka (−3,0), km 5,80–8,76: koniec
  Kleeberga, łącznica, rondo Pamięci Męczeństwa Kresowian (pod wiaduktem), Szosa Ełcka, granica miasta, Szosa
  Knyszyńska. Dalej korytarz `dk65-01` (0205). D63: najpierw przejezdnie i z grubsza.
- Kafel leży w dwóch powiatach: Białystok 2061 (31 %) i białostocki 2002; `Region.teryt_powiat` był jednym kodem.
- ADR 0203 „Otwarte 1”: w `bialystok-maczka` (E 919–926, N 30–31) mur oporowy BDOT10k stał na dodanym pasie
  jezdni przy końcu niskiego pomostu (`furniture_in_lane` na trasie).

## Decyzja
1. **Region** `bialystok-knyszynska`: bbox 770827,595199 – 772875,597247, origin 771851,596223. Nowe pole
   `Region.teryt_powiat_extra` (tu `("2002",)`), właściwość `powiaty`; `build_region`, `ingest`,
   `streetscape/sources.py` i `build_world.preview_trees` czytają BDOT10k / LoD1 / LoD2 każdego powiatu (obiekty z
   obu paczek scalane po id). Puste pole = ścieżka kodu jak wcześniej (14 pozostałych regionów; determinizm regionu C: `test_world_roads`, 15 ok).
   `far_field.py`, `lod2_extract.py` (2061 na sztywno) i `water.py` (jeden powiat) — bez zmian, patrz „Otwarte”.
2. **Dane**: 438 węzłów, 461 krawędzi, 1061 budynków (LoD1 900), NMT 2022, ortofoto 2024 0,25 m.
   Trasa kontrolna `route_start.json`: 2961 m, od szwu z kleeberga (772875; 595511,6) do szwu z dk65-01
   (770827; 597006,8).
3. **Drogi kontra ortofoto** (`junction_checks.authored.json`, 9 punktów, `tools/worldgen/qa/junction_topview.py`):
   przebieg osi, łącznica zjazdowa, rondo pod wiaduktem (pierścień r = 23,7 m, 4 wloty), rozdzielone jezdnie
   Szosy Ełckiej przy rondzie, skrzyżowania boczne i łuk Szosy Knyszyńskiej zgodne topologicznie z ortofoto.
   Różnice — „Otwarte”.
4. **Szwy** (overrides po stronie tego kafla; plików sąsiadów nie ruszam):
   - **W, `dk65-01`** (x = 770827): 6 dróg, te same `osm_way` / klasa / pasy / kierunek. Way 234919333 (Szosa
     Knyszyńska): override `width 6.0 + edge_lines both` jak w dk65-01 (BDOT tu 6,5 m, tam 6,0 m).
   - **E, `bialystok-kleeberga`** (x = 772875): 13 dróg, topologia zgodna. BDOT10k dopasowuje szerokość do
     krawędzi grafu, a krawędź kafla tnie drogi na krawędzie różnej długości — stąd trzy rozbieżności. Sprawdzone
     na ortofoto (paski wyprostowane 0,0625 m/px, `seam-e/strip_*.jpg`):

     | way | tu (BDOT) | kleeberga | ortofoto | override (krawędź przy szwie) |
     |---|---|---|---|---|
     | 561326924 `trunk_link`, 29 m do węzła 2504239797 | 7,5 | 6,0 | **jeden pas 3,4 m przylegający do jezdni** (krawężnik → 1. linia przerywana), dalej 3,9 + ~3 m do bariery; brak zieleni między nimi | 6,0 (`confidence: low`) |
     | 222579345 `service` | brak | 6,0 | plac firmy, asfalt ~12 m, bez krawędzi jezdni | 6,0 (WORKING_VALUE) |
     | 224161424 `service` (y = 596184,5) | 3,0 | 4,0 | plac manewrowy, bez krawędzi jezdni | 4,0 (WORKING_VALUE) |

     Żadna z wartości BDOT dla 561326924 nie jest prawdziwym przekrojem: to trzeci pas jezdni głównej, nie osobna
     jezdnia. 6,0 daje ciągłą krawędź na szwie; właściwy układ wymaga jednej poprawki w obu kaflach („Otwarte 1”).
5. **Mur na pasie pomostu** (`tools/worldgen/streetscape/furniture.py`, zmiana wspólnego kodu):
   `DeckKeepout` — mur / płot wycinany z trójkątów jezdni warstwy `bridge`, gdy jego góra wchodzi w okno QA
   (> nawierzchnia − 0,3 m). `fences()` dostaje `decks` z `streetscape/stage.py`.
   r1 pokazał, że pierwsza wersja nie działała: wycięła 2 m, `furniture_in_lane` zostało 2. Pomiar z chunków GLB:
   mur 128,98–130,54, jezdnia pomostu 131,31–131,88, **balustrada na murze do 131,64**. Mur był pod jezdnią —
   w pas wystawała balustrada, a `_retaining_top` liczył sam mur. Teraz: góra muru + `RAILING_H` (1,10 m).
   Mur pod wysokim pomostem (prześwit większy niż balustrada) zostaje.

## Budżet
| | maczka r1 → r2 | knyszynska r2 |
|---|---|---|
| build_world | 2229 s → 2396 s (2 joby heavy + pytest równolegle) | 933 s (r1: 849 s) |
| import-region | 574 s, 64 chunki, korytarz 32 | 531 s, 64 chunki, korytarz 39 |
| WORLD_MEMORY Low | 153,2 → 153,2 MB | 116,0 MB |
| WORLD_MEMORY High | 420,4 → 420,4 MB | 260,2 MB |
| kamery trasy Low (drawsEst / tris) | 7: 93–586 / 150–387k (bez zmian) | 8: 79–395 / 114–286k |
| kamery place Low | 4: 91–309 / 152–225k | 4 szwy: 53–301 / 72–233k |
| trójkąty furniture (maczka, kafel z murem) | −46 (r1) i dalsze 4 m muru z balustradą | — |

Poprawka muru usuwa geometrię (6 m muru z balustradą), nic nie dodaje. Liczby z edytora (drawsEst przed SRP
batchingiem), bez telefonu — budżet urządzenia nie mierzony w tym zadaniu.

## Walidacja
- `tests/gis/test_knyszynska_0208.py` (10): kafel między kleeberga i dk65-01 zgodny z planem 0203; dwa powiaty,
  pozostałe regiony jednopowiatowe; **oba szwy: te same drogi / klasa / pasy / kierunek** oraz **ta sama szerokość
  jezdni po overrides** (13 dróg E, 6 dróg W); trasa od szwu do szwu, 2900–3000 m; overrides z uzasadnieniem i
  istniejącym celem; punkty kontrolne i kamery w kaflu; `DeckKeepout` na syntetycznym pomoście (mur, którego
  balustrada wchodzi w pas — wycięty; mur pod wysokim pomostem — zostaje; płot na niskim pomoście — wycięty).
- `pytest tests/gis` po scaleniu `origin/main`: **1240 ok, 3 skip, 3 xfail, 1 fail**
  (`pytest-r2.log`) — `test_road_fidelity::test_report_not_stale`: `fidelity_qa.json` regionu C ma stary hash
  `build_world.py` — gałąź zmienia ten plik o 5 linii (`preview_trees`, drugi powiat); na `main` test przechodzi
  (9 ok, 1 xfail). Po `fidelity/run.py --region
  bialystok-industrial-c` w raporcie zmienił się tylko ten jeden hash (metryki regionu C bez zmian) i test
  przechodzi (`test_road_fidelity.py` + `test_knyszynska_0208.py`: 19 ok, 1 xfail). Pełny zestaw powtórzony
  na `524f1b034` bez równoległych buildów: **1241 ok, 3 skip, 3 xfail** (`pytest-final.log`).
- **Maczka r2** (`road_consistency_qa.json`): `furniture_in_lane` 2 → **0**; `cut_on_deck_carriageway_m` 2 → 6.
  Chunki: mur został na E 915,5–920,5 pod pomostem, balustrada do 131,24 < jezdnia 131,33. Kamera
  `deck_end_wall_0208` (`bialystok-maczka-r2/vqa/Low-overcast/deck-end-wall-0208.png`): trzy pasy wjazdu na pomost
  wolne. Pozostałe przypadki QA na trasie (4 `arrow_no_exit`, 2 `lane_blind_end`, 1 `marking_off_carriageway`,
  3 `obstacle_in_lane` verge/shoulder przy E 14–32) są sprzed tego zadania — nie ruszane.
- **Knyszynska r2 — przejezdność bez telefonu** (`route_sweep.py sweep`, `route_sweep_r2.txt`): trasa 2961 m co
  2 m, przesunięcia −1,25 / 0 / +1,25 m, 4437 próbek: **0 bez kolizji jezdni, 0 przeszkód 0,3–4,5 m nad jezdnią**
  (wszystkie materiały LOD0 + `terrain_lod2`), skok kolizji na osi pasa ≤ 0,11 m / 2 m.
  `road_consistency_qa.json`: w paśmie trasy 3 `lane_blind_end` (drogi boczne) i 2 `obstacle_in_lane`
  (`verge_grass` w pasie łańcucha 242989864 przy E 815–817, N −844 — 29,0 m od osi pasa trasy przy s ≈ 247 m,
  czyli inna jezdnia w paśmie trasy; w r1 te same dwa przypadki były liczone jako poza trasą; sweep czysty,
  „Otwarte 9”); poza trasą 3 `obstacle_in_lane`, 2 `marking_off_carriageway`. `terrain_walls_qa`: 11 ścian > 0,15 m, max 0,67 m.
- **Szwy — geometria** (`route_sweep.py seam`, `seam_e_r2.txt`, `seam_w_r2.txt`; kolizja jezdni 0,5 m w głąb
  każdego kafla): E z kleeberga (świat z main): 13 dróg, **skok ≤ 0,03 m**; teren (`terrain_lod2`, 32 stacje)
  mediana 0,07 m, max 0,54 m. W z dk65-01 (świat z worktree `dk65-corridor-0205`, w main go nie ma): trasa
  (234919333) **0,07 m**; drogi boczne do 0,31 m (523816940), 0,19 m (196779645); teren mediana 0,15 m, max 1,28 m.
- **Szew E — zbudowana jezdnia** (obecność `road_collision` wzdłuż y, 2 m w głąb każdego kafla): jezdnia
  zachodnia + pas 561326924 razem 13,25 m po obu stronach; jezdnia wschodnia 11,5 m tu i 9,0 m w kleeberga
  (ukośne zakończenie siatki przy krawędzi, pomiar zgrubny co 0,25 m). Szerokości są wyrównane w danych
  wejściowych (test), a zbudowane przekroje zgadzają się w granicach tego pomiaru.
- visual-qa Low overcast r1 + r2, oba regiony (`*-r2/vqa/Low-overcast/`): 8 kamer trasy knyszynska, 4 kamery
  szwów, rondo z góry; pary ortofoto | widok z góry `junctions-r1/`, `junctions-r2/` (9 punktów). Porównanie tylko
  z ortofoto — zdjęć właściciela z tego kafla nie ma w `art-source/world/refs/`.
- visual-critic: NIE uruchomiony (subagent nie tworzy subagentów) — do zlecenia przez lidera. EditMode: nie
  uruchamiany (bez zmian C#). Telefon: nie (zakaz w zadaniu).

## Otwarte
1. **Way 561326924 / 668340275 (oba kafle)**: na ortofoto to trzeci pas jezdni Kleeberga (3,4 m, linia
   przerywana), u nas osobna jezdnia 6,0 m z klinem zieleni do węzła 2504239797 (ADR 0206 „Otwarte 4”). Oś OSM
   leży na linii rozdzielającej pasy (~1,5 m od środka pasa). Poprawka = jeden override w obu kaflach naraz.
2. **Szew W — NMT**: ten kafel ma NMT 2022, dk65-01 według ADR 0205 NMT 2025; skoki 0,19–0,31 m na dwóch drogach
   bocznych i do 1,28 m w terenie. Przyczyny nie sprawdzałem; kandydat: pin rocznika (`sources.authored.json`,
   ADR 0209) + ponowny ingest. Na trasie 0,07 m.
3. Kamera `seam_e_into_tile`: w r2 kadr ze środka naczepy ciężarówki kontrolnej (stoi na pierwszych 20 m trasy);
   pozycja przesunięta na 36 m, `generated/control_cameras.json` odświeży się przy następnym build_world.
4. Szew W, południowa strona jezdni przy krawędzi kafla: łata bruku (zjazd) pognieciona na skarpie
   (`seam-w-back-into-tile.png`), poza jezdnią.
5. Szosa Ełcka / Knyszyńska: linie krawędziowe tylko na ostatnich ~180 m (override szwu); reszta wg reguły —
   nie porównana z ortofoto odcinek po odcinku. Latarnie i znaki z reguł — UNVERIFIED.
6. `far_field.py` i `lod2_extract.py` mają powiat 2061 na sztywno, `water.py` czyta jeden powiat — dla części
   kafla w powiecie 2002 daleki plan / LoD2 / woda nie korzystają z drugiej paczki.
7. Mur maczka: zostało 5 m muru pod pomostem z balustradą 0,09 m pod nawierzchnią — niewidoczne z jezdni,
   ale to geometria wewnątrz konstrukcji pomostu; docelowo ciąć mur na całym rzucie pomostu z niskim prześwitem.
8. `route_endpoints.json`: `start_osm_way` 306609228, a węzeł brzegowy należy do 261104557 (pole opisowe,
   trasa liczona z punktów) — do poprawienia przy okazji.
9. `obstacle_in_lane` ×2 (trawa pobocza w pasie łącznicy 242989864 / 289192230, E 815–817, N −844) i ×3 poza
   trasą, 2× P-7b poza jezdnią (242989866) — zwężenia przy rozjazdach, do szlifu.
