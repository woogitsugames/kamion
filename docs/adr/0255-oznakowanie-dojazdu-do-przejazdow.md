# ADR 0255: oznakowanie dojazdu do przejazdów kolejowych (§ 79: A-9/A-10, G-1a–f, „Sygnalizacja automatyczna”, U-1)

**Status:** Proposed. Chmura, s21/s22, 2026-11-15, gałąź `claude/awesome-fermi-3s2wdi` (PR do `rail-fix-s21`). Decyzja właściciela D71 pkt 3: „osobne zadanie teraz”.

**Numer:** 0255 wybrano z odstępem, bo numery od 0247 dostała chmura D r3 (HANDOVER „Ostatni przydzielony ADR: 0246”). Lider może przenumerować.

**Powiązane:**
- ADR 0217: etap toru, opt-in `Region.rail`. Ten ADR rozszerza jego „Otwarte 4”.
- ADR 0223 (#102): linia 38 w kaflach DK65.
- ADR 0125: zestawy znaków `gate3_landmarks` (jeden prototyp i jeden materiał na zestaw).
- Recenzja `docs/reports/REVIEW-2026-11-15-s21-code-102.md`: brak § 79 w obu gałęziach.

## Kontekst
Etap toru stawia przy przejeździe tylko urządzenia „na miejscu”: krzyż G-3/G-4 (§ 80), półrogatki, sygnalizatory i dzwon. Kierowca ciężarówki nie dostaje uprzedzenia. Brakuje znaku ostrzegawczego, słupków wskaźnikowych i słupków prowadzących. Na DW671 (Tykocin, kat. B) i przy linii 38 wzdłuż DK65 ma to znaczenie dla hamowania 40 t zestawu.

## Źródła (pobrane 2026-11-15, przeczytane dosłownie)
- **[R1] Dz.U. 2025 poz. 1105** (rozporządzenie o przejazdach kolejowo-drogowych).
  - URL: `https://api.sejm.gov.pl/eli/acts/DU/2025/1105/text.pdf`, SHA256 `c3caeb070b48af809707db4d3c77cb2b3aa00bebd27d55d3fbfc8cb6857dd924` (ten sam plik co w ADR 0217).
  - § 6 ust. 1: kategorie A–F.
  - § 79 pkt 1 lit. a: A-9 przed przejazdem z rogatkami, A-10 bez rogatek.
  - pkt 3: G-1a–G-1f.
  - pkt 5 lit. a: U-1a lub U-1b na dojazdach bez rogatek, na odcinku 15–20 m od skrajnych szyn, co 3 m, po obu stronach drogi, najbliższe 4 m od skrajnych szyn. Lit. b: przy rogatkach „na zewnątrz rogatek”.
  - pkt 6: tablica „Sygnalizacja automatyczna” pod A-9/A-10 przed kat. B i C.
- **[R2] Dz.U. 2019 poz. 2311**, zał. 1, tekst jednolity szczegółowych warunków technicznych dla znaków.
  - URL: `https://api.sejm.gov.pl/eli/acts/DU/2019/2311/text.pdf`, SHA256 `f94925ec05a75ca8cc1cea478727592a3b1b4c9822cdc76b309420556b550543`.
  - pkt 2.2.10: A-9 dla kat. A i B; G-1a pod tarczą znaku, G-1b na 2/3 odległości, G-1c na 1/3. Tabela 2.2 (I/II/III): powyżej 60 km/h 150–300 / 100–200 / 50–100 m, do 60 km/h 50–100 / 35–70 / 20–35 m. Krótsze dojazdy: kolumna II (G-1b pod znakiem, G-1c w połowie) i kolumna III (G-1c pod znakiem, wtedy A + G-1f także po lewej). Lewa strona (G-1d–f) także na jezdniach jednokierunkowych i przy widoczności przejazdu poniżej 100 m przy prędkości powyżej 60 km/h.
  - pkt 2.2.11: A-10 dla kat. C i D, zasady jak dla A-9.
  - Tabela 1.1: trójkąt grupy S (średnie) 900 mm. Grupa S obowiązuje na jednojezdniowych drogach krajowych i wojewódzkich (pkt 1.2.1 lit. c).
  - Tabela 1.11: znaki G co najmniej 2,00 m.
  - Rys. 9.8.1–9.8.6: G-1 300 × 1000 mm, obrzeże 20 mm.
  - Status aktu w ELI „obowiązujący”, ale istnieją „Nowelizacje po tekście jednolitym”. Nie sprawdzono, czy zmieniają pkt 2.2.10 (UNVERIFIED).

## Decyzja
1. **Planowanie** (`streetscape/rail_approach.py`, czyste dane): dla każdego przejazdu planu toru i każdego dojazdu wylicza pozycję, azymut i kody. Wynik trafia do `rail.json` → `approach` (lista) i `approach_qa` (kategorie, warianty, pominięcia, liczniki, `min_track_distance_m`).
   - **Kategoria** wg § 6 ust. 1 [R1]:
     - A: `crossing:barrier` = full/gate albo `supervision`;
     - B: półrogatki (half/double_half/yes);
     - C: same sygnalizatory (`crossing:light`);
     - D: tylko znaki.
     - Nadpisanie `category` (A–D, walidowane) wygrywa.
   - **Znak:** A-9 przy rogatkach, A-10 bez nich. Pod nim tablica „Sygnalizacja automatyczna” dla kat. B i C. Pod tablicą G-1a, wszystko w jednym zestawie.
   - **Odległości:** `SIGN_DIST_M` = 150 m (powyżej 60 km/h) albo 60 m (do 60 km/h) od skrajnej szyny, mierzone wzdłuż osi drogi. To WORKING_VALUE w kolumnie I. 2/3 i 1/3 tej odległości (100/50 m i 40/20 m) mieszczą się w kolumnach II i III, więc tabela jest spełniona w całości (test).
     - Prędkość: OSM `maxspeed` odcinka drogi (`build_world` przekazuje `road_speeds`) albo nadpisanie `approach_kmh`.
     - Bez `maxspeed` przyjmujemy powyżej 60 km/h (domyślnie poza zabudową, WORKING_VALUE).
   - **Krótki dojazd** (koniec linii drogi: skrzyżowanie albo krawędź kafla, minus `END_CLEAR_M` 5 m):
     - kolumna II albo III wg [R2];
     - poniżej minimum kolumny III nie stawiamy znaku i zapisujemy to w raporcie;
     - wariantów z rys. 2.2.10.8 (znaki na drodze dojazdowej przed skrzyżowaniem) nie modelujemy.
   - **Lewa strona:** G-1d/e/f. Wariant III wymusza ją automatycznie. W pozostałych przypadkach włącza ją nadpisanie `left_side: true`, bo generator nie zna widoczności ani nie odróżnia tu jednokierunkowości.
   - **U-1:**
     - bez rogatek: 4, 7, 10, 13, 16 m od skrajnej szyny (16 m to WORKING_VALUE w przedziale 15–20 m), po obu stronach, oś słupka 0,75 m za krawędzią jezdni (WORKING_VALUE);
     - przy rogatkach: pierwszy słupek 3 m za napędem rogatki (WORKING_VALUE dla „na zewnątrz rogatek”), dalej co 3 m;
     - 4 m liczymy w poprzek toru, więc przy przejeździe skośnym słupek jest dalej wzdłuż drogi (4/sinθ).
   - **Kafel i jezdnia:**
     - element poza kaflem (`tile_local`) albo na jezdni (np. skrzyżowanie) jest pomijany z wpisem w `approach_qa`;
     - gdy nie mieści się znak ostrzegawczy danej strony, nie stawiamy też jej słupków G-1, bo samotny G-1 byłby mylący. Sąsiedni kafel bez przejazdu tych znaków nie postawi (patrz „Otwarte” 3).
   - **Wyłączenie** przy przejeździe: `approach_signs: false`.
2. **Tarcze** (`streetscape/rail_signs.py`): A-9 (płot), A-10 (parowóz), G-1a–f (paski opadające ku jezdni) i tablica. To nasze schematyczne rysunki w PIL, bez cudzych grafik.
   - Wymiary: trójkąt 900 mm (Tabela 1.1) i G-1 300 × 1000 mm (rys. 9.8) — SOURCED.
   - Położenie pasków odczytane z rysunków z dokładnością ok. ±30 mm (grupa pasków wyśrodkowana) — WORKING_VALUE.
   - Kolory G-1 (białe pole, czerwone paski i obrzeże) nie wynikają z czarno-białych rysunków — UNVERIFIED.
   - Tablica 0,90 × 0,30 m, czarne litery na białym — WORKING_VALUE/UNVERIFIED.
   - Rysuje je `gate3_landmarks.draw_face` (dwa haczyki: `FACE_DIM.update`, gałąź w `draw_face`).
3. **Obiekty** (`rail_props.place_approach`, wywołanie w `stage.py` zaraz po `RP.place`):
   - Zestaw znaku to jeden prototyp `sign_g3_<key>` z jednym materiałem (atlas twarzy w `boards`, eksport jak w ADR 0125), czyli 1 draw na znak. Dolna krawędź najniższej tablicy (G-1) jest na 2,00 m (Tabela 1.11).
   - Słupki to prototypy `signal_rail_u1a` / `signal_rail_u1b`, wyłącznie z istniejących materiałów. Wygląd (biały słupek, czarny pas, czerwony prostokątny odblask na U-1a, dwa białe na U-1b), wymiary (1,00 m; 0,12 × 0,10 m) i to, który słupek stoi po której stronie, to UNVERIFIED/WORKING_VALUE. Zał. 4 do [R2] (urządzenia BRD) nie był czytany.
   - Prefiksy `sign_` i `signal_` dają regułę LOD znaków (LOD1 od 50 m, wycięcie na 250 m). Bez zmian w C#.

## Budżet (zmierzone na syntetycznym przejeździe, `tests/gis/test_rail_approach_0255.py`; skrypt `budget.py` w opisie PR)
- Jeden przejazd, 2 dojazdy, wariant I, bez lewej strony: 26 instancji (6 zestawów znaków + 20 słupków).
  - LoD0: 1 252 trójkąty (kat. D) / 1 260 (kat. B).
  - LoD1: 820 / 828.
- Zestaw znaku: 28–34 trójkąty, 1 materiał.
- U-1: 48–60 trójkątów, 2–3 materiały. Na LoD1 bez odblasku: 2 materiały.
- Liczba draw calls zależy od batchowania instancji w Unity (UNVERIFIED): górna granica to 1 na zestaw znaku plus 2–3 na słupek.
- W kadrze widać zwykle 1 zestaw znaku i do 10 słupków jednego przejazdu. To ok. 0,3 % dolnej granicy docs/06 §6 (400 tys. trójkątów). Telefon nie był mierzony.
- Region C nie ma toru, więc zmiana go nie dotyczy.

## Walidacja
- `tests/gis/test_rail_approach_0255.py`, 20 testów, dane syntetyczne, bez Data/raw. Sprawdzają:
  - kategorie A–D i znak A-9/A-10 z tablicą;
  - wszystkie warianty Tabeli 2.2 (obie klasy prędkości i każda odległość w swojej kolumnie);
  - pozycje: prawa strona kierowcy, azymut lica, odległość od skrajnej szyny, z;
  - U-1 (4/3/16 m, za rogatką);
  - prędkość z OSM i z nadpisania;
  - krótki dojazd (wariant III z lewą stroną) i krawędź kafla;
  - `left_side` i `approach_signs: false`;
  - wymiary i paski tarcz;
  - prototypy (1 materiał na zestaw, materiały z `M`) i budżet poniżej 2 500 trójkątów.
- `test_rail_0217.py` bez zmian i zielony. Liczniki urządzeń przejazdu się nie zmieniły, bo znaki dojazdu są w osobnej liście `approach`.
- Pełne `tests/gis` (na `rail-fix-s21` @ `823dd0478` + ta zmiana): 1378 passed, 4 failed, 54 skipped, 5 xfailed.
  - Baza: 1359 passed, 3 failed, 54 skipped, 5 xfailed. Różnica to +20 nowych testów i `test_bed_uvs_address_the_tile`.
  - `test_bed_uvs_address_the_tile` naprawił lokalny agent w `ac928dd32`. Po przeniesieniu na ten commit testy torów dają 52/52.
  - Pozostałe 3 faile są znane z main: `test_report_not_stale`, `forest_0187`, `world_v31` forest_hlod.
- Render tarcz (atlas A-9+SA+G-1a, A-10+G-1a, G-1b/c, G-1d/e/f) obejrzany w chmurze. Sceny nie renderowano (brak Unity).

## Odtworzenie (lider)
```
uv run --project tools/worldgen tools/worldgen/roads/build_world.py --region dw671-tykocin-01
uv run --project tools/worldgen python -m pytest -q tests/gis/test_rail_approach_0255.py tests/gis/test_rail_0217.py
pwsh scripts/import-region.ps1 -Region dw671-tykocin-01 -Build
pwsh scripts/visual-qa.ps1 -Scene World_dw671-tykocin-01 -Tier Low -Lighting clear -OutputDir artifacts/rail-0255/vqa/Low
pwsh scripts/visual-qa.ps1 -Scene World_dw671-tykocin-01 -Tier High -Lighting clear -OutputDir artifacts/rail-0255/vqa/High
```
Do sprawdzenia w `generated/rail.json` → `approach_qa`:
- `category` = B, `warning` = A-9, warianty obu dojazdów;
- pominięcia (DW671 ma skrzyżowania blisko przejazdu: możliwy wariant II/III albo pominięcie z wpisem);
- `min_track_distance_m` > 2,2.

Kamery: istniejące `rail_xing_*` oraz nowa kamera z kabiny 150 m przed przejazdem na każdym dojeździe (do dopisania w `control_cameras_place.authored.json` po pierwszym przebiegu; pozycje są w `approach`).

## Otwarte
1. Oznakowanie poziome z § 79 pkt 4 (P-2 / P-4 / P-7b / P-12 + P-16 / P-14), tabliczka T-7 (kąt poniżej 60°, łuk, równoległy tor), T-10 + A-30, B-20 (załącznik 4 do [R1]) oraz G-2 (§ 81, robi #102).
2. Rys. 2.2.10.8: przejazd blisko skrzyżowania. Znaki na drodze dojazdowej i tablica przeddrogowskazowa z A-9/A-10.
3. Przejazd przy krawędzi kafla: znaki dojazdu w sąsiednim kaflu (dziś pomijane z wpisem). Wymaga wymiany przejazdów między kaflami.
4. Wygląd U-1a/U-1b i wymiary tablicy „Sygnalizacja automatyczna”: odczytać zał. 4 do [R2] i porównać ze zdjęciem z otwartego źródła (Mapillary/Panoramax).
5. Widoczność (dziś nadpisanie `left_side`): policzyć z NMT i zabudowy.
