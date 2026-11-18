# ADR 0215 — D65: Ełcka/Studzienna 6,9 m i nowa jezdnia DK65 w `dk65-05` jako plac budowy (`construction: true`)
Status: przyjęty (scalony do main 2026-11-15, `f64364ba4`; status zaktualizowany 2026-11-16); pierwotnie: Proposed (agent geo-worldgen, s20, gałąź `dk65-d65-data`, sesja w chmurze: bez Unity i bez `Data/raw`),
2026-11-15. Do scalenia przez lidera. **Numer 0215 do potwierdzenia przez lidera** (HANDOVER: „Ostatni przydzielony
ADR: 0214”; w `docs/adr` najwyższy plik to 0212).
Powiązane: D64, D65 p. 5 i 6 (`docs/11`), ADR 0205 (linie krawędziowe poniżej klasy GP), 0207 (kafle `dk65-02…05`,
otwarte p. 3 i 6), 0150 (graf tras KRTG), 0204 (`lamps: false`).

## Rewizja r2 (2026-11-15, s21, weryfikacja PR #80, gałąź `fix-pr80-s21`) — obowiązuje zamiast p. 1 i 3 „Decyzji”
Powód: D66 (`docs/11`) i decyzja właściciela o jednym mechanizmie placu budowy po scaleniu ADR 0214 (`dk65-06…11`).
1. **Ełcka/Studzienna = 6,6 m (D66), nie 6,9 m**, w `dk65-02…05` **i w `dk65-06`** (D66 wymienia 02…05; way 1560819273
   przechodzi przez szew 05/06, więc `dk65-06` dostaje ten sam `set`, inaczej skok 0,15 m na stronę). Wpis
   `dk65-elcka-xsec`: `set: {width: 6.6, edge_lines: both}`. Generator (klasa G): 2 × 3,05 m + 2 × 0,25 m, linie
   krawędziowe 0,20 m od krawędzi → **6,2 m od siebie**. Pomiar na wycinkach K1 0,1 m (`artifacts/verify-cloud-c/pr80/
   ortho/elcka_xsec.json`, km 11,0–16,0, n = 11): linie 6,1–6,4 m (n = 9), asfalt 6,5–7,1 m (bez km 13,0 / 13,5 — wloty).
2. **Nowa jezdnia DK65 w `dk65-05` = mechanizm ADR 0214, nie `construction: true`.** r1 budowało z wayów 1151531612 /
   1151531613 / 1151531608 wstęgę `road_gravel` 7,5 m z krawężnikiem, która kończyła się na szwie N — w `dk65-06` te
   same waye są wycięte z grafu (`graph_filter.authored.json`) i zamienione w piaszczysty korytarz `construction_site`.
   Teraz w `dk65-05`: `graph_filter.authored.json` (`drop_osm_ways` = te trzy waye) + blok `construction_site`
   wygenerowany przez `tools/worldgen/qa/construction_sites.py --region dk65-05 --ways 1151531612,1151531613,1151531608`
   (3 osie `not_open`, półszerokość 10 m, jak ramię SE ronda w `dk65-06`; w kaflu nie ma osi OSM `highway=construction`).
   `roads.graph.json` po `build_region`: −3 krawędzie, −5 węzłów (4 graniczne + `n4236127178`), nic poza tym.
   Wynik `build_world`: plac 45 515 m², 5 hałd, podniesienie terenu maks. 2,75 m (hałdy), płot wg reguły 0214.
3. **Schemat `set: {construction: true}` zostaje w generatorze** (`roads/closures.py`, `network`, `markings`, `decals`,
   `navgraph`) i w testach syntetycznych, ale żaden region go nie używa. Do decyzji lidera: zostawić dla dróg
   zamkniętych z gotową nawierzchnią albo usunąć (kod w `roads/`, którego ta poprawka nie ruszała).
4. **Piasek na szwie**: `construction_site.ground_colour` rozmywał maskę placu z odbiciem lustrzanym na krawędzi
   kafla; dla korytarza przecinającego szew pod kątem (tu ~41°) waga piasku w tym samym wierszu siatki różniła się
   między kaflami do 0,24, a krawędź piasku (A > 0,5) o 1 m. Teraz maska jest rasteryzowana 6 węzłów poza kafel przed
   rozmyciem (`_soft_mask`); regiony bez placu bez zmian. Test `test_construction_site_sand_is_identical_on_both_sides_of_a_seam`.
5. Kamery: `top_site_seam` i `site_seam_oblique` w `dk65-05` i `dk65-06` (plac przy szwie).
6. Testy: `test_construction_0215.py` (część „dane dk65-05”) sprawdza stan r2 (waye poza grafem, brak wstęgi, jeden
   plac, osie przecinają szew w tym samym x ±0,1 m co w `dk65-06`); `test_dk65_seams_0207.py` 6,6 m;
   `test_dk65_seams_0214.py`: szew 05/06 bez xfail (przekrój, teren, osie placu).
Liczby szwu z buildu i rendery: `docs/reports/VERIFY-2026-11-15-pr80-pr82.md`.

## Kontekst
ADR 0207 zostawił dwa pytania do właściciela; D65 (2026-11-15) na nie odpowiada:
- p. 5: „Ełcka/Studzienna: wąska ~7 m (zwęzić z 7,6 do ~6,9 m)”. W danych jezdnia miała 7,6 m (odczyt krawędzi asfaltu
  z ortofoto 2024, pewność niska), przy rozstawie linii krawędziowych 6,25–7,0 m z tego samego ortofoto.
- p. 6: „Nowa jezdnia DK65 w dk65-05: nieotwarta — plac budowy, trasa po starej”. OSM (wycinek Geofabrik kafla) ma tam
  trzy waye `highway=primary`, `ref=65`, `oneway=yes`, `lanes=2` (100/70 km/h) — generator zbudował z nich gotowe
  jezdnie z liniami, a graf tras GPS je zawierał. Ortofoto 2024-05-27: nasypy piaskowe.

## Decyzja
1. **Ełcka/Studzienna = 6,9 m** w `dk65-02…05`: istniejący wpis `dk65-elcka-xsec` (ten sam w czterech kaflach, poziom
   way) dostaje `set: {width: 6.9, edge_lines: both}` i pole `source: "D65 właściciel, ~6,9 m"`. Waye:
   716806121, 1024956365 (02); 1024956365 (03); 1024956365, 41533343, 1243220441, 1024956364 (04); 1024956364,
   1399803717 (Studzienna), 1560819273 (przedłużenie Studziennej do szwu N, bez `name` w OSM) (05).
   6,9 m to wartość podana przez właściciela „około”, nie pomiar — `WORKING_VALUE` do zdjęcia ze skalą / pomiaru taśmą;
   zgodna z rozstawem linii 6,25–7,0 m z ortofoto. Wynik w generatorze (klasa G, `pipeline.build_network('dk65-05')`):
   2 pasy × 3,2 m + 2 × 0,25 m. Linie krawędziowe bez zmian (0,12 m, `EDGE_LINE_INSET_MINOR` od krawędzi).
   Zmieniony jest wpis, nie dodany drugi: jeden wpis na przekrój, historia (7,6 m z ortofoto) zostaje w `reason`.
2. **Schemat nadpisania drogi nieotwartej**: `set: {construction: true}` na zwykłym celu krawędziowym
   (`target: {osm_way: [...]}` albo `{edge: "..."}`), z polami `source`, `reason`, `confidence`, `verify` jak każdy
   wpis. Opis i funkcje wspólne: `tools/worldgen/roads/closures.py` (czysty Python). Skutki:
   | etap | zachowanie |
   |---|---|
   | `roads.network` | `EdgeSection.construction = True`, `provenance["construction"] = authored_override:<id>`; `edge_lines = none`, bez `turn:lanes`, `provenance["no_lamps"]` (jak `lamps: false`, ADR 0204); nawierzchnia `road_gravel`, chyba że ten sam `set` podaje `surface` |
   | `roads.markings` | żadnych znaków poziomych na odcinku: linie pasów, osi, krawędziowe, strzałki, przejścia z węzłów OSM |
   | `roads.decals` | bez łat i plam oleju (jezdnia nigdy nie niosła ruchu) |
   | `navgraph` (KRTG) | krawędź i węzły używane tylko przez nią nie trafiają do grafu tras: GPS ani nic, co trasuje po KRTG (ruch AI), jej nie użyje; `t["closed_edges"]` i linia w logu wypisują pominięte |
   Geometria jezdni (oś, szerokość, niweleta) nie zmienia się — zostaje wstęga bez oznakowania.
   Nawierzchnia `road_gravel` to `WORKING_VALUE`: jedyny niezwiązany materiał jezdni w bibliotece; ortofoto pokazuje
   jasny piasek, materiału „piasek / roboty ziemne” nie ma (otwarte p. 2).
3. **`dk65-05`**: wpis `dk65-05-new-carriageway-construction` na wayach **1151531612, 1151531613, 1151531608**
   (krawędzie `w1151531612:10712325680-4236127178` 1214,6 m, `w1151531613:4236127177-10711806890` 1292,0 m,
   `w1151531608:4236127178-10712325628` 47,7 m; długości z `roads.graph.json`). To wszystkie krawędzie `primary`
   kafla. Nie mają wspólnego węzła z otwartą siecią w kaflu (test), więc w `dk65-05` nie ma ramienia skrzyżowania do
   zamknięcia. Trasa kontrolna (`route_start.json`: Ełcka → Studzienna) ich nie używa (test).
   Identyfikacja: ADR 0207 („Nowa jezdnia DK65 w OSM: 3 krawędzie `primary` ref 65”) + tagi w `roads.graph.json`;
   `highway=construction` w grafie kafla nie występuje.
4. **Most na Supraśli (way 41533342, `dk65-02`) zostaje 7,5 m.** Wpis `dk65-02-supraslbridge` uzasadniał 7,5 m jako
   „= jezdnia Ełckiej” (`WORKING_VALUE`) przy odczycie ~9 m między pasami krawężników; D65 mówi o Ełckiej/Studziennej,
   nie o moście, więc nie zmieniam (otwarte p. 4).

## Walidacja (chmura: bez Unity, bez `Data/raw`, bez `build_world`)
- `tests/gis/test_construction_0215.py` 15/15: cele (way / edge / nieznany way → stale), sekcja (flaga, provenance,
  brak linii i strzałek, materiał, jawne `surface` wygrywa, geometria bez zmian), oznakowanie na syntetycznej sieci
  (otwarta jezdnia `primary` ma linie pasów i strzałki, zamknięta nic; otwarta droga obok bez zmian; przejście z węzła
  OSM na zamkniętej jezdni nie jest malowane), graf tras (krawędź i osierocone węzły znikają, wspólne węzły zostają,
  serializacja i determinizm), dane `dk65-05` z gita (3 krawędzie, trasa otwarta, graf tras −3 krawędzie).
- `tests/gis/test_dk65_seams_0207.py`: przekrój Ełckiej/Studziennej `(6.9, "both")` w 02–05, szwy 01→…→05 zgodne.
- `pipeline.build_network('dk65-05')` (bez `Data/raw`): 2 nadpisania zastosowane, 0 stale.
- Liczby pełnych testów: `artifacts/dk65-d65-data/PR-BODY.md`.
- **Nie wykonano:** `build_world`, import do Unity, kamery kontrolne, pętla wizualna, pomiar na telefonie — do wykonania
  przez lidera (komendy w `PR-BODY.md`). Zmiana nie jest więc obejrzana na renderze; zasada 4 z `CLAUDE.md`
  pozostaje do spełnienia przed uznaniem za gotowe.

## Otwarte
1. `dk65-06` (agent 0214) dzieli z `dk65-05` waye szwu N: 1560819273 (Studzienna, przekrój 6,9 m) oraz 1151531612 /
   1151531613 / 1151531608 (nowa jezdnia). Te same wpisy trzeba powtórzyć w `dk65-06`, inaczej na szwie będzie skok
   szerokości, a zamknięta jezdnia „otworzy się” za szwem. W `dk65-06` nowa jezdnia dochodzi do ronda DK65 — tam
   potrzebne zamknięcie ramienia (p. 3).
2. Materiał placu budowy (piasek / kruszywo / pierwsza warstwa asfaltu) — `road_gravel` to `WORKING_VALUE`; pytanie do
   właściciela (zdjęcie ze Studziennej). Ogrodzenie, sprzęt, hałdy (D64: „uproszczona strefa”) — niezrobione.
3. Ramię skrzyżowania z drogą otwartą: linie zatrzymania / ustąpienia i przejścia w płycie skrzyżowania
   (`through_lines`, drapowanie w płycie) oraz fizyczne zamknięcie (zapora U-20, bez liter) nie są obsłużone;
   `roads/route.py` i `scripts/export-route.py` (trasa startowa po grafie) nie czytają flagi — w `dk65-05` bez
   znaczenia (jezdnie odłączone), przy pierwszym takim przypadku do zrobienia.
4. Most na Supraśli 7,5 m między 6,5 m (Fasty) i 6,9 m (Ełcka) — do odczytu z ortofoto / zdjęcia właściciela.
5. Znaki pionowe i inne obiekty z reguł przy zamkniętej jezdni (poza latarniami) nie były przeglądane w kodzie
   `streetscape` — sprawdzić na renderze `dk65-05`.
6. Mapa GPS `<region>.bytes` (rysunek dróg, nie graf tras) nie była zmieniana — zamknięta jezdnia może być na niej
   rysowana (UNVERIFIED, nie sprawdzano generatora mapy).
7. `tools/worldgen/navgraph/tests/test_route_graph.py::test_region_file_is_reproducible` nie przechodzi także na
   `origin/main` (`5724a161b`) — plik `.bytes` regionu C nie odpowiada świeżemu buildowi; poza zakresem.

## Odtworzenie
```
uv run --project tools/worldgen python -m pytest -q tests/gis/test_construction_0215.py tests/gis/test_dk65_seams_0207.py tests/gis/test_edge_lines_0205.py
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region dk65-0N --context     # N = 2..5 (roads.graph.json bez zmian: build_region zbędny)
uv run --project tools/worldgen python scripts/export-route.py --region dk65-0N
pwsh scripts/import-region.ps1 -Region dk65-0N
pwsh scripts/visual-qa.ps1 -Scene World_dk65-0N -Tier Low -Lighting clear -Width 1920 -Height 1080 -OutputDir artifacts/dk65-d65-data/dk65-0N/r1/Low-clear
```
