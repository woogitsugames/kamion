# AUDIT-SIGNS-PL-2026-11-12-mistral — znaki pionowe w repo vs przepisy polskie (M9)

Data audytu: 2026-11-12. Gałąź `mistral/9-signs-pl`, PR do `main`. Zakres: definicje znaków pionowych
w `tools/worldgen` i `art-source/world/signs` (definicje kodu; assety LFS nietknięte). Zgodnie
z poleceniem właściciela w tym PR **nie zmieniono generatorów ani danych gry** — tylko ten raport
i test `tests/gis/test_signs_pl_audit.py`; rozbieżności są w raporcie i w `KNOWN_DEVIATIONS` testu.

## Źródła przepisów (czytane 2026-11-12, ELI/ISAP)

- [ZNAKI] Rozporządzenie w sprawie znaków i sygnałów drogowych, t.j. **Dz.U. 2019 poz. 2310**.
- [ZNAKI-Z1] Załącznik nr 1 „Szczegółowe warunki techniczne dla znaków drogowych pionowych i warunki ich
  umieszczania na drogach” do rozporządzenia Ministra Infrastruktury z 2003-07-03, t.j. **Dz.U. 2019
  poz. 2311**, w brzmieniu zmienionym m.in. **Dz.U. 2021 poz. 2066** (Tabela 1.11). Pełny PDF załączników
  z ELI (`api.sejm.gov.pl/eli/acts/DU/2019/2311/text.pdf`, 525 str. PDF); numery stron poniżej to strony
  wydrukowane Dz.U. (strona PDF − 5).
- U-4 (tablice rozdzielające) należy do **załącznika nr 4** (urządzenia BRD), poza przeczytanym zał. 1 —
  pozycje z niego oznaczone **UNVERIFIED**.

## Tabela audytu

| Znak / parametr | Wartość w repo (plik:linia) | Wartość z przepisu (paragraf/załącznik, strona Dz.U.) | Status |
|---|---|---|---|
| Grupa wielkości dla miejskich Z/G/L | grupa „średnie” (S) — `tools/worldgen/roads/standards.py:215-218` | [ZNAKI-Z1] pkt 1.2.1 (str. 2-3): średnie m.in. na jednojezdniowych drogach krajowych/wojewódzkich i dwujezdniowych w zabudowanym z V ≤ 60 km/h | OK |
| A-7 / A-30 wymiar | bok trójkąta 0,90 m — `standards.py:218` (`triangle`), `streetscape/signs.py:308`, `streetscape/gate3_landmarks.py:49` | Tabela 1.1 (str. 4): A średnie = bok 900 mm; pkt 1.2.1 (str. 3): A-7/B-20 nie mniejsze niż średnie | OK |
| B-20 (STOP) wymiar | 0,80 m między narożnikami ośmiokąta → koło wpisane 0,739 m — `standards.py:218` (`octagon`), `signs.py:308` | pkt 3.1.1 (str. 91) + Tabela 3.1 (str. 92): wymiar B-20 = średnica **koła wpisanego** w ośmiokąt, średnie 800 mm (płyta 800/cos(π/8) ≈ 866 mm między narożnikami); B-20 nie w grupie wielkiej, na drogach małych = średni | **ROZBIERZNOŚĆ — do poprawy** (0,739 vs 0,800 m) |
| B-33 / B-1 / B-2 / B-36 wymiar | średnica tarczy 0,80 m — `standards.py:218` (`disc`), `signs.py:308-310` | Tabela 3.1 (str. 92): B średnie = średnica 800 mm, obrzeże s = 0,1·d | OK |
| C-12 / C-9 wymiar | średnica 0,80 m — `standards.py:218`, `signs.py:308` | Tabela 4.1 (str. 152): C średnie = średnica 800 mm (kolumna C Tabeli 1.1 = 600 mm nadpisana opisem szczegółowym pkt 4.1.1) | OK |
| D-1 wymiar | 0,80 m boku rombu — `standards.py:218` (`diamond`), `gate3_landmarks.py:50` | Tabela 5.1 (str. 173): D średnie = długość podstawy 600 mm; pkt 5.2.1.1 (str. 180): D-1 bok 600 mm, powtórzenia 400 mm | **ROZBIERZNOŚĆ — do poprawy** (0,80 vs 0,60 m) |
| D-3 / D-6 (gate3) wymiar | 0,60 × 0,60 m — `gate3_landmarks.py:51-52` | Tabela 5.1 (str. 173): D średnie 600 mm | OK |
| D-6 / D-15 (rule-based) wymiar | 0,80 m — `standards.py:218` (`square`), użyte w `streetscape/furniture.py:494` | Tabela 5.1 (str. 173): 600 mm; pkt 5.2.15 (str. 216): D-15 „takie jak średnie” (poza krajowymi dopuszczalne mini 400 mm) | **ROZBIERZNOŚĆ — do poprawy** (0,80 vs 0,60 m; niespójne wewnętrznie z gate3 0,60 m) |
| U-4a wymiar | 0,75 × 1,35 m — `gate3_landmarks.py:53` | załącznik nr 4 (poza zał. 1) — nieprzeczytany w całości | **UNVERIFIED** |
| U-4a wysokość | `lower_edge_m: 0.9` — `Data/Regions/bialystok-industrial-c/overrides.yaml:347` | Tabela 1.11 (str. 32): znaki na urządzeniach BRD 0,90-1,20 m | OK |
| Wysokość dolnej krawędzi A-D (zabudowany) | 2,00 m / 2,20 m na chodniku — `standards.py:212-213`, użyte w `furniture.py:490` | Tabela 1.11 (str. 32, brzmienie po Dz.U. 2021 poz. 2066): min 2,00 m; na chodniku 2,20 m | OK |
| Wysokość nad jezdnią (bramownice) | 5,00 m (+0,20 margines) — `standards.py:214`, `streetscape/landmarks.py:124` | Tabela 1.11 (str. 32): znaki nad jezdnią min 5,00 m | OK |
| Wysokość tablic E-1/E-2 obok jezdni | 2,00 m — `streetscape/signs_route.py:261-262, 310-311` (`S.SIGN_H_MIN`) | Tabela 1.11 (str. 32): E-1/E-2/E-14 w zabudowanym min 2,00 m (2,20 na chodniku) | OK |
| Odległość od krawędzi jezdni | krawędź tarczy 0,75 m za lico krawężnika — `standards.py:219` (`SIGN_LATERAL`); użyte w `furniture.py:518,574,617`, `signs_route.py:111`, `gate3_landmarks.py:253` | pkt 1.5.3 (str. 25-27): na ulicach 0,50-2,00 m od krawędzi jezdni (wystający krawężnik wlicza się do chodnika); z poboczem ≥ 0,50 m od krawędzi korony/jezdni; w pasie dzielącym ≥ 0,50 m od opaski | OK (0,75 m mieści się w 0,50-2,00 m) |
| Barwy lic znaków | `streetscape/signs.py:25-31`; FLUO `gate3_landmarks.py:44` | Tabela 1.3 (str. 6): pola tolerancji CIE 1931 (x,y) folii odblaskowych typ 1/2. Przeliczone xy: RED (0,600;0,326) czerwona, YELLOW (0,464;0,469) i FLUO (0,444;0,486) żółta, BLUE (0,180;0,168) niebieska, WHITE (0,315;0,332) biała, GREY_BACK (0,311;0,329) szara — wszystkie w polach; GREEN (0,257;0,445) poza polem „zielona” (0,007-0,248; 0,362-0,703) | OK oprócz GREEN: **odchylenie udokumentowane** (in-gamut część pola „zielona” to pojedynczy klin przy narożniku (0,248;0,409); gamut sRGB ledwo zahacza o pole) — UNVERIFIED jako wartość nominalna |
| Folia odblaskowa | brak danych w repo (materiały nie rozróżniają typu folii) | Tabela 1.2 (str. 5): folie typu 1 / typu 2 wg lokalizacji; dla A-7, B-2, B-20, D-6, D-6a, D-6b **obowiązkowo typ 2**; nad jezdnią na A/S folia pryzmatyczna | **BRAK DANYCH w repo** |
| Krój pisma / wysokość liter tablic E | DejaVu Sans Bold (schematyczny) — `streetscape/signs.py:13-14` (docstring); rysunki schematyczne `signs.py:170-330` | pkt 1.4.1-1.4.3 (str. 9-10, 16-19): litery wg wzorów „do kopiowania” (krój komercyjnie „Drogowskaz”); Tabela 1.8 (str. 11): grupy liter I-VII; Tabela 9.5.1 (str. 445): tablice E grupa średnie — wysokość liter dużych d = 210 mm, cyfr numeru drogi d1 = 162 mm | **ODCHYLENIE schematyczne, udokumentowane** (wysokość liter 210 mm nie jest modelowana fizycznie) — UNVERIFIED |
| Słupek znaku | Ø 60,3 mm — `standards.py:220` | poza zakresem rozporządzenia (praktyka katalogowa) | UNVERIFIED (WORKING_VALUE w repo) |
| Tabliczki T (plate) | 0,60 × 0,45 m — `gate3_landmarks.py:54` | rozdział 9 zał. 1 (wymiary tabliczek) — niezweryfikowane szczegółowo | UNVERIFIED |
| Tablica nazwy ulicy (teal) | 1,00 × 0,25 m, TEAL — `gate3_landmarks.py:41,55` | oznaczenia miejskie poza zakresem rozporządzenia o znakach drogowych | poza zakresem, OK |
| Koniec ograniczenia B-33 na skrzyżowaniu | powtórzenie B-33 po każdym skrzyżowaniu — `standards.py:221-223` | [ZNAKI] Dz.U. 2019 poz. 2310 § 27 ust. 1 | OK (cytat już w repo) |

## Test

`tests/gis/test_signs_pl_audit.py` — dane znaków wobec tabeli wymagań: każda pozycja albo zgadza się
z przepisem, albo jest jawnie w `KNOWN_DEVIATIONS` z cytatem (wtedy test dokumentuje rozbieżność).
Test assetów `Data/**/generated` pomija się przez `pytest.skip`, gdy pliki są wskaźnikami LFS.

## Weryfikacja

`uv run --project tools/worldgen pytest tests/gis/test_signs_pl_audit.py tests/gis/test_furniture_signs_0120.py tests/gis/test_gate3_landmarks.py tests/gis/test_streetscape.py -q`
→ wszystkie testy przechodzą (z wyjątkiem pomijanego testu LFS).

## Do zrobienia osobno (poza tym PR)

- Poprawki rozbieżności zaznaczonych „do poprawy”: `SIGN_SIZE["square"]`/`["diamond"]` 0,80 → 0,60 m
  (Tabela 5.1, str. 173; pkt 5.2.1.1) i `SIGN_SIZE["octagon"]` → 0,80/cos(π/8) (pkt 3.1.1, str. 91).
- Klasa folii (typ 1/2, Tabela 1.2, str. 5) jako atrybut materiałów — obowiązkowo typ 2 dla
  A-7, B-2, B-20, D-6.
- Weryfikacja U-4a i tabliczek T wobec załącznika nr 4 / rozdziału 9 (UNVERIFIED).
- Oficjalny krój liter tablic E („Drogowskaz”, pkt 1.4.3) zamiast DejaVu Sans Bold (UNVERIFIED).
