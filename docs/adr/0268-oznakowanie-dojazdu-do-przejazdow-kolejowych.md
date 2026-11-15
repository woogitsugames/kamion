# ADR 0268 — oznakowanie dojazdu do przejazdów kolejowych (D71 pkt 3) + poprawki po krytyce wizualnej 0217
Status: Proposed (agent `rail-dk65-s22`, s22, gałąź `rail-dk65-s22`), 2026-11-15. Do scalenia przez lidera.
Powiązane: D71 pkt 3 (docs/11), ADR 0217 (torowisko, przejazd DW671), ADR 0223 (linia 38 w kaflach dk65-01..04),
`docs/reports/REVIEW-2026-11-15-s21-code-102.md` (P1-3), `docs/reports/REVIEW-2026-11-15-s22-0217-visual.md` (FAIL: P0-1, P1-3, P1-5, P2-11, P2-12).

## Kontekst
Przejazdy z ADR 0217/0223 miały tylko urządzenia przy samym torze (G-3/G-4, sygnalizatory, rogatki). Kierowca nie
dostawał żadnego ostrzeżenia przed przejazdem, oś jezdni była przerywana aż do płyt, a krawężnik DW671 biegł przez
płyty i szyny (krytyk wizualny: FAIL). Właściciel (D71 pkt 3) zlecił oznakowanie dojazdu wg Dz.U. 2025 poz. 1105 § 79.

## Źródła (przeczytane 2026-11-15, tekst z PDF, bez pamięci)
1. **Dz.U. 2025 poz. 1105** (rozp. MI z 9.07.2025, skrzyżowania linii kolejowych z drogami),
   `https://api.sejm.gov.pl/eli/acts/DU/2025/1105/text.pdf`, SHA256 `c3caeb070b48…57dd924` (zgodny z ADR 0223), s. 19–20:
   - § 79 pkt 1 lit. a: A-9 przed przejazdem wyposażonym w rogatki, A-10 przed niewyposażonym; T-7 pod A-10 przy
     kat. C i D „szczególnie niebezpiecznych” (kąt < 60°, tor równoległy, łuk);
   - § 79 pkt 3: G-1a–c „po prawej stronie jezdni”, G-1d–f „po lewej stronie jezdni”;
   - § 79 pkt 4: P-2, **P-4** „na dojazdach … i na przejeździe … w celu rozdzielenia przeciwnych kierunków ruchu”
     (lit. b), P-7b, P-12 + P-16, **P-14** „na przejazdach … kategorii A, B, C i D” (lit. e);
   - § 79 pkt 5: słupki prowadzące U-1a lub U-1b — lit. a: „na dojazdach do przejazdów … bez rogatek na odcinku drogi
     o długości od 15 m do 20 m, licząc od skrajnych szyn toru kolejowego, w odstępach co 3 m po obu stronach drogi;
     … słupki … ustawione najbliżej toru znajdują się w odległości 4 m od skrajnych szyn”; lit. b: „na zewnątrz
     rogatek” (bez liczb);
   - § 79 pkt 6: tablica „Sygnalizacja automatyczna” pod A-9 i A-10 przed przejazdami **kat. B i C**;
   - § 80 ust. 1 (G-3/G-4: A bez rogatek, C, D), § 81 ust. 1 (G-2: A–C na maszcie sygnalizatora poniżej głowic,
     D pod G-3/G-4 na jego słupie), § 82 pkt 2 (linie spowalniające / kolorystyka nawierzchni — fakultatywne).
2. **Dz.U. 2019 poz. 2310** (t.j. rozp. w sprawie znaków i sygnałów drogowych),
   `https://api.sejm.gov.pl/eli/acts/DU/2019/2310/text/O/D20192310.pdf`:
   - § 3 ust. 2: „Odległość znaku ostrzegawczego od miejsca niebezpiecznego wynosi od 150 m do 300 m na drogach, na
     których dopuszczalna prędkość pojazdów przekracza 60 km/h, a do 100 m na pozostałych drogach”;
   - § 6 ust. 1–2: A-9 = zapory lub półzapory, A-10 = ani zapory, ani półzapory;
   - § 78 ust. 2: słupek z trzema kreskami pod A-9/A-10, z dwiema „na 2/3 odległości znaku ostrzegawczego od
     przejazdu”, z jedną „na 1/3 tej odległości”; ust. 3: znak bliżej niż w § 3 ust. 2 → pod znakiem słupek z dwiema
     kreskami, z jedną na 1/2; znak „w bezpośredniej bliskości przejazdu” → tylko słupek z jedną kreską pod znakiem;
   - wzory barwne (PDF s. 41: A-9, A-10; s. 51: G-1a–f, G-2, G-3, G-4) — obejrzane jako raster, twarze przerysowane
     z prymitywów (bez kopiowania grafiki).
3. `roads.standards.P14_BEFORE_SIGNAL` = 2,0 m (Dz.U. 2019 poz. 2311 zał. 2 pkt 4.2.5 — cytat już istniejący w kodzie).
4. **Nie przeczytane:** Dz.U. 2019 poz. 2311 cz. 1 (zał. 1, PDF > 10 MB — limit pobierania). Stąd `UNVERIFIED`:
   wymiary G-1, G-2, U-1a, wysokość montażu G-1, warunek stosowania słupków lewostronnych G-1d–f, wygląd tablicy
   „Sygnalizacja automatyczna” (akt 1105 nie podaje wzoru).

## Decyzja
1. **Jedno źródło przejazdów dla trzech odbiorców** (`streetscape/rail_approach.py`). `build_world` planuje przejazdy
   już na geometrii przebiegu 1 (`_rail_plan(w0)`), bo krawężniki i oznakowanie poziome powstają przed etapem rail;
   przebieg 2 musi dać te same przejazdy (różnica > 0,5 m = błąd budowy).
   - `attach(net, plan)` w `side_edit`: krawężnik (URBAN) schodzi do 0 na długości płyt + skos przejazdu + 1,0 m
     (`KERB_CUT_MARGIN_M`, rampa 1,0 m), rów (RURAL) wypełniony jak przy zjeździe → **P0-1 krytyka**; zapisuje stacje
     przejazdu w `chain.meta["rail_xings"]`.
   - `roads/markings.py`: **P-4** (2 × 0,12 m) zamiast P-1 na 50 m każdego dojazdu od skrajnej szyny i przez przejazd
     (§ 79 pkt 4 lit. b; długość `RAIL_P4_LEN_M` = WORKING_VALUE); **P-14** 2,0 m przed urządzeniami przejazdu na
     pasie dojazdu (§ 79 pkt 4 lit. e). Tylko na jezdniach, które w ogóle mają oznakowanie (`highway in MARKED`);
     drogi lokalne przejazdów dk65 są nieoznakowane → licznik „skipped (unmarked road)”, nic nie malujemy.
   - `plan(rail_plan, net)` → `rail.json`: `approach` (markery), `approach_rules` (reguła, podstawa prawna, odległości,
     co odrzucono), `approach_outside_tile`. Instancje stawia `rail_props.place` (generator = spawner).
2. **Reguła jednego wlotu** (`rule()`; odległości wzdłuż drogi od skrajnej szyny):
   | sytuacja | znak / słupki |
   |---|---|
   | rogatki (`half`, `double_half`, `full`, `gate`, `yes`, `chain`) | A-9, inaczej A-10 (§ 79 pkt 1a; 2310 § 6) |
   | kategoria dokładnie B lub C | + tablica „Sygnalizacja automatyczna” (§ 79 pkt 6); `A|B`, `C|D`, brak → bez tablicy |
   | v > 60 km/h | znak 150 m (dolna granica zakresu 150–300 m), G-1a pod znakiem, G-1b 100 m, G-1c 50 m |
   | v ≤ 60 km/h lub brak `maxspeed` (50) | znak 100 m („do 100 m”), G-1b 66,7 m, G-1c 33,3 m; krótsza droga ≥ 60 m: te same proporcje |
   | droga krótsza niż wyżej, ≥ 30 m | § 78 ust. 3: znak na końcu dostępnego odcinka + G-1b, G-1c w 1/2 |
   | < 30 m | § 78 ust. 3: znak + G-1c; mniej niż urządzenia + 5 m → nic, wpis `dropped` |
   | bez rogatek | U-1a po obu stronach: 4, 7, 10, 13, 16, 19 m od skrajnej szyny (§ 79 pkt 5a) |
   | z rogatkami | 6 słupków co 3 m od 1,0 m za urządzeniami (§ 79 pkt 5b; rozstaw WORKING_VALUE) |
   | A-10, kat. C/D, kąt < 60° | `t7_required: true` (tabliczka T-7 jeszcze nie budowana) |
   Droga: łańcuch pod przejazdem, dalej przez skrzyżowania po najprostszym ramieniu (≤ 40°); koniec drogi / krawędź
   kafla skraca dojazd (znaki poza kaflem nie są stawiane — lista). G-1d–f tylko na jezdni jednokierunkowej
   (WORKING_VALUE, warunek z 2311 nieprzeczytany). B-20/P-12 (§ 79 pkt 2, zał. 4 — widoczność) — nie budowane.
3. **Tabliczki i znaki**: A-9/A-10 (`triangle_up`), G-1a–f, G-2, „T-SA” (`rect`) jako zwykłe `plate_<kod>` biblioteki
   znaków (tekstura z `signs.py`, ten sam słupek Ø60, LOD i kolizja co inne znaki; zero zmian w C#). Wymiary
   prostokątów `signs.RECT` (G-1 0,30 × 1,00 m, G-2 0,35 × 0,50 m, tablica 0,90 × 0,36 m) = WORKING_VALUE z proporcji
   wzoru; dolna krawędź G-1 1,0 m (WORKING_VALUE), znak ostrzegawczy nad tablicą/słupkiem ≥ 2,0 m (tab. 1.11).
4. **G-2 (P0-2 recenzji #102)**: marker `sign` `G-2` nie ma już własnej siatki — to `plate_G-2` na maszcie
   sygnalizatora pod tarczami (górna krawędź 2,00 m) albo na słupku G-3 pod krzyżem. Test: każdy `kind/code` z
   `markers()` i z dojazdu ma prototyp albo tabliczkę; kat. B nigdy nie dostaje krzyża (§ 80 ust. 1).
5. **Urządzenia po krytyce**: maszt sygnalizatora w pasy biało-czerwone co 0,40 m (P1-3; Mapillary 1832769196903759);
   szafa napędu rogatki `drive_cabinet_faded` (wyblakły pomarańcz, P2-11); krzyż G-3/G-4 wg wzoru barwnego 2310
   s. 51: białe ramiona z dwoma czerwonymi pasami na każdej połowie (było: biały z czerwoną obwódką — niezgodne ze
   wzorem); słupki dojazdu DW671 `guide_post: red_white` (authored override, widoczne na Mapillary) — domyślnie U-1a.
6. **Kamery** (`artifacts/rail-dk65-s22/tools/cams.py`, authored): na przejazd `rail_x<k>_far_{a,b}` (165 m),
   `_near_{a,b}` (30 m), `_side_eye` (1,6 m, 13 m z boku — skala urządzeń, P2-12), `_top`.

## Budżet (z generatora; pomiar kadrów: sekcja Walidacja)
Na przejazd dwuwlotowy: 6 słupków znaków (2 × [A-x + tablica + G-1a], 2 × G-1b, 2 × G-1c) + do 24 słupków
prowadzących + 2 × G-2. Nowe materiały: `sign_A-9` / `sign_A-10`, `sign_T-SA`, `sign_G-1a..c`, `sign_G-2`
(tekstury 256², jak inne znaki) i `drive_cabinet_faded` (kolor). Słupek prowadzący: 3–4 boksy (≤ 60 tris),
prototyp `signal_rail_guide_*` (klasa LOD urządzeń przejazdu). Oznakowanie poziome: P-4 2 wstęgi × ~100 m, P-14
≤ 4 prostokąty na wlot. WORKING_VALUE do pomiaru w kadrze (niżej).

## Walidacja
(uzupełniane po buildach — patrz koniec pliku)

## Otwarte
1. Dz.U. 2019 poz. 2311 zał. 1 / zał. 4 do przeczytania (wymiary G-1, G-2, U-1a/U-1b, warunek G-1d–f, wysokości) —
   plik > 10 MB; po odczycie zamienić WORKING_VALUE/UNVERIFIED w `signs.RECT`, `rail_approach.py`, `rail_props.py`.
2. Tablica „Sygnalizacja automatyczna”: wygląd UNVERIFIED (brak wzoru w akcie) — zdjęcie właściciela.
3. T-7, B-20/P-12/P-16 (wymagają danych o widoczności — zał. 3/4 do 1105), P-7b na dojeździe, czerwone pasy
   akustyczne DW671 (orto 60 m; § 82 pkt 2), bariery stalowe przy DW671.
4. Przekrój DW671 (pobocze gruntowe zamiast krawężnika i włazów) i **sieć trakcyjna linii 38** — krytyk P1-4, P1-6;
   poza zakresem (generator dróg / osobny etap).
5. Płyty przejazdu bez spoin poprzecznych, tłuczeń „jak bruk”, ostra krawędź skarpy (krytyk P2-8..10) — nie ruszone.
6. Wyposażenie przejazdów dk65 (Dzikowska, Św. Franciszka, Białostocka, droga bez nazwy) nadal z tagów OSM / domyślne
   → A-10 bez tablicy; brak zdjęć referencyjnych (ref w `artifacts/rail-fix-s21/ref/` dotyczy tylko DW671).
