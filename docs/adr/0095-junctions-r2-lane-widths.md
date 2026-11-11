# ADR 0095: Węzły r2 — szerokość i liczba pasów z ortofoto, farba autorska, linia trasy na rondach

Status: przyjęty (world-builder, junctions-r2), 2026-11-11. Wynika z `docs/reports/visual/REVIEW-2026-11-11-s9-0092-0093.md`
(sekcja 0093, „Następna runda (ADR 0095)”) oraz z raportu integracji s9 (`artifacts/integration-s9/REPORT.md`, regresja
swept path). Powiązane: ADR 0074–0077, 0093. Wymaganie właściciela: „drogi dosłownie jak w OSM, żeby mieszkaniec wiedział,
jak jechać”. Dowody: `artifacts/junctions-r2/`.

## Kontekst
- Trzy zarzuty P0-L recenzji 0093 (s 1040–1080, n10015785253, rozdział łącznicy E −782 N 77) miały jedną przyczynę:
  BDOT10k podaje dla Andersa 8,0 m, generator to odrzuca i bierze `lanes` × 3,50 m + 2 × 0,50 m = 11,5 m, wyśrodkowane
  na linii OSM. Pomiar na ortofoto 0,08 m: jezdnie mają 10,5–11,2 m, a linia OSM biegnie 1,1–1,5 m od osi jezdni w
  stronę pasa dzielącego (OSM rysuje ją wzdłuż linii pasów). Skutek: pas dzielący „do zera”, 5 rzędów linii tam, gdzie
  są 3 pasy, latarnie „na pasie”.
- OSM podaje `lanes=3` na wiadukcie DK8 nad rondem Putry (w490398852, w490398851, w173985169, w23844386). Mozaika WMS
  0,08 m i arkusz 0,25 m z 2024-05-27 pokazują zgodnie 2 pasy; trzeci „pas” OSM to łącznica z ronda (osobna linia
  w240542867), którą generator i tak kładzie obok. Pomost był o 3,3 m szerszy od prawdziwego po stronie pasa
  dzielącego — latarnia „na lewym pasie” z filmu właściciela (E −589 N 19,5) stała na linii prawdziwej bariery.
- OSM wprowadza łącznice w oś jezdni głównej (węzeł na osi). `align_forks` przesuwał początek łącznicy pod właściwy
  pas, trzymał przesunięcie 40 m i wygaszał je na 65–100 m, choć sama linia OSM już po 10–40 m biegnie własnym śladem:
  łącznica do ronda Putry leżała 4–4,8 m za prawdziwym krawężnikiem, łącznica przy E −782 zostawiała pas trawy w
  miejscu linii ciągłej i P-21.
- Linia trasy startowej (ADR 0076: środek skrajnego prawego pasa) na rondach biegła przy zewnętrznym krawężniku
  pierścienia i ścinała wewnętrzny narożnik wyjazdu: 7 czerwonych testów `tests/physics/test_swept_path_gate3`.

## Decyzja
1. **Przekrój z pomiaru (`lane_edges`)** — nowy klucz `set:` dla jezdni jednokierunkowych: odległości od LEWEJ krawędzi
   jezdni (w kierunku jazdy) do [początku pasa 1, linii 1|2, …, końca ostatniego pasa]; pierwsza wartość = opaska /
   ściek, ostatnia = szerokość; ostatni przedział < 2 m = prawa opaska (pobocze za linią krawędziową); `width` obok
   `lane_edges` = jezdnia szersza niż pasy (pole wyłączone, wyspa). Pasy nie muszą być równe. `lane_layout`,
   linie przez łaty, trasa, strzałki, UV kolein czytają ten sam układ. `edge_lines: none|left|right|both` — linie
   krawędziowe faktycznie widoczne (domyślnie przy `lane_edges`: brak; reguła P-7b dla klas A/S/GP bez zmian tam, gdzie
   nie ma pomiaru). `turn_lanes` — strzałki tam, gdzie OSM ich nie ma.
2. **Położenie i szerokość jako profil wzdłuż krawędzi**: `center_offset: [a, b]` (liniowo) albo `[[t, m], …]`,
   `width: [[t, m], …]` (t = 0…1 w kierunku krawędzi). Gdy autorskie położenie stawia koniec gałęzi pod jej pasem
   (różnica < 0,3 m), `align_forks` nie przesuwa — łącznica idzie śladem z ortofoto, nie śladem „trzymaj 40 m”.
3. **Jedna powierzchnia dla gałęzi biegnącej krawędź w krawędź** (`network._tie_alongside`): gałąź rozwidlenia, której
   pasy sumują się do pasów pnia, a krawędź biegnie < 1 m od sąsiedniej przez ≥ 15 m, dostaje `abreast_of` (wspólna
   wysokość jak dla gałęzi nachodzących, ADR 0076). Bez tego klin przed nosem wyspy miał 0,41 m różnicy profili i był
   odrzucany (ADR 0093, otwarte #2).
4. **Farba autorska z ortofoto** (`roads/authored_paint.py`): `painted_line` (P-1, P-1e, P-2, P-2b, P-7a, P-7b, P-12,
   P-13, P-14; łamana w E/N, wygładzana), `painted_arrow`, `painted_crossing` (P-10 / P-11 po linii przejścia),
   `paint_clear` (wymazanie farby generatora w wielokącie). Wszystko układane na wygenerowanej nawierzchni; nic nie
   zbudowane = `overrides_stale`. `paved_gore` dostał `surface:` (kostka).
5. **P-2a tylko na dojeździe**: na jezdni jednokierunkowej ciągłe linie przed skrzyżowaniem były malowane także 20 m
   ZA skrzyżowaniem (koniec „a” łańcucha).
6. **Trasa** (regresja swept path ze scalenia 0076, zgłoszona przez integrację s9): (a) na pierścieniu ronda i na
   jednokierunkowych ramionach przy nim trasa idzie osią jezdni; oś jest trzymana `RING_HOLD_M` = 12 m od pierścienia
   i przechodzi w środek prawego pasa na `RING_BLEND_M` = 30 m; narożnik przy pierścieniu zaokrąglany na 2 m zamiast
   4–10 m; (b) w ciasnym łuku jezdni jednokierunkowej ≥ 2 pasy, gdy pas leży po wewnętrznej stronie łuku, trasa
   schodzi do osi jezdni (od R 60 m, w pełni przy R 30 m, wyprzedzenie 12 m) — obejście ronda Putry (w237183783 nie
   ma `junction=roundabout`); (c) trasa jadąca na wprost nie używa pasa tylko do skrętu (`turn:lanes` / `turn_lanes`):
   przed n10015785253 prawy pas kończy się na wyspie. Wszystkie progi WORKING_VALUE.
7. **Pasy z pomiaru są prawdą dla fidelity**: `fidelity/run.py` porównuje liczbę pasów z `lane_edges` (z identyfikatorem
   override'u jako źródłem), gdy istnieje; tag OSM `lanes` zostaje w raporcie.
8. **Narzędzia pomiaru**: `artifacts/junctions-r2/scripts/xsec.py`, `xbatch.py` — ortofoto „wyprostowane” wzdłuż łańcucha
   (x = kilometraż, y = odległość poprzeczna, podziałka 1 m, obrys generatora); `sl2en.py` / `en2sl.py` — przeliczenie
   (s, lat) ↔ E/N po surowej linii OSM; `planview.py --route` rysuje trasę. `fidelity/ortho.py`: dodatkowe katalogi
   komórek HR (`ORTHO_HR_EXTRA`), bo `Data/raw/refs` jest w worktree tylko do odczytu (dociągnięte 2 komórki GUGiK WMS
   HighResolution: `artifacts/junctions-r2/ortho_hr/`, manifest z URL / sha256 / licencją — do przeniesienia przez lidera
   do `Data/raw/refs/gugik-ortho-hr/bialystok-industrial-c/`).

9. **Rozwidlenia z położeniem autorskim**: (a) profil położenia odrysowany wzdłuż krawędzi jest bezwzględny —
   `align_forks` go nie przesuwa, a wygładzanie przesunięć w łańcuchu ma dla niego σ 2,5 m zamiast 10 m; (b)
   `profile.shifted_end_heights`: gdy wszystkie końce w węźle są odsunięte od węzła (pień ma położenie autorskie),
   pniem jest najszerszy koniec, a pozostałe startują z jego powierzchni (łącznica do ronda Putry brała wysokość
   węzła, 0,10 m nad powierzchnią pnia 4,9 m w bok — dwa progi po 5 cm w profilu trasy przy s 1411–1413);
   (c) override węzła `nose_max_angle`: nos wysepki tam, gdzie krawężniki się rozchodzą, także gdy pierwsze metry
   linii OSM odchodzą pod kątem > 25° (inaczej zaokrąglenie R 2,5 m dopiero 50 m dalej i łata rozciągnięta między
   łącznicą a wznoszącym się dojazdem wiaduktu: 1,3 m różnicy wysokości w korytarzu trasy).
10. **Dopasowanie profilu do punktów z ortofoto**: `artifacts/junctions-r2/scripts/fit_offset.py` (iteracyjnie, na
   samej sieci; reszta ≤ 0,15 m). Odczyt „na oko” przesunięć względem linii OSM z załamaniem zawodził trzy razy
   (zapis w `reason` override'ów) — przy ostrych załamaniach linii OSM mierzyć punkty w E/N i dopasowywać.

## Override'y (wszystkie z `reason` = pomiar, plik paska w `artifacts/junctions-r2/xsec/`)
- Andersa, obie jezdnie między s 1100 a rozwidleniem do ronda Putry: 9 krawędzi z `lane_edges` + `center_offset`
  (10,8–11,2 m; oś 0,7–1,45 m w prawo od linii OSM). Pas dzielący ciągły, 3,5–4,8 m.
- Zatoka s 1040–1080: w174545870 = kostka 4,9 m (było 4 m asfaltu), wypełnienie między jezdnią a zatoką z kostki,
  pas krawężnikowy 1,35 × 48,5 m jako `traffic_island`, linia krawędziowa ciągła wzdłuż pasa i przerywana P-7a w obu
  otwarciach.
- n10015785253: krawędź 21 m = 2 pasy przelotowe + jezdnia do 11,0 m, wyspa trójkątna z kostki, 3 pola P-21, dwie
  zebry na pasach skrętu (węzły OSM przejść leżą na liniach wchłoniętych przez łatę), linia ciągła 0,24 m przez
  skrzyżowanie, gardziel ulicy bocznej 7,3 → 16 m, `turn_lanes` through|through|right na dojeździe.
- Wiadukt DK8 nad rondem Putry (kier. zach.): 6 krawędzi, 2 pasy 8,0–8,2 m z liniami krawędziowymi; oś do 1,6 m od
  linii OSM (profil). Łącznica z ronda: szerokość 3,9–5,75 m i położenie profilem; klin asfaltowy przed nosem
  (`paved_gore`), wyspa z nosem E −781,9 N 76,5, P-21 jodełka przed nosem (`chevron_axis`) i ukośne po stronie
  łącznicy, linia ciągła i przerywana między łącznicą a jezdnią. Jezdnia 3-pasowa na zachód od węzła: 10,5 m, oś 1,5 m
  w prawo.
- Rozwidlenie Andersa → rondo Putry (s 1410–1480): łącznica w606396463 położeniem i szerokością z ortofoto, pasmo P-21
  po lewej stronie łącznicy (obrys z ADR 0093, wtedy niezbudowany).

## Wynik
Tabela liczb: sekcja „Liczby” niżej (uzupełniana z `roads_qa.json`, `fidelity_qa.json`, `road_consistency_qa.json`,
`terrain_walls_qa.json`, `swept_*/summary.json`; logi `artifacts/junctions-r2/logs/`).

LICZBY_PLACEHOLDER

## Otwarte
Z listy recenzji 0093 zrobiony jest punkt 1 (trzy P0-L) i część punktów 4 i 8; reszta nie została ruszona w tej rundzie.
1. **Zatoka s 1040–1080 — końce**: otwarcia zatoki to nadal łaty skrzyżowania (asfalt, zaokrąglony narożnik „ucho”) zamiast
   klina z kostki o prostej krawędzi. Potrzebny wielokąt autorski nawierzchni z krawężnikiem (`paved_apron`) i wyłączenie
   linii serwisowej z budowy wstęgi; zaprojektowane, nie zrobione. Zatoka zaczyna się w rzeczywistości ok. 45 m przed
   węzłem OSM (linia P-7a jest, kostki pod nią nie ma).
2. **n10015785253**: czerwone przejazdy rowerowe przy obu zebrach (brak materiału farby czerwonej w warstwie oznakowania),
   P-13 / linie warunkowego zatrzymania na pasach skrętu, sygnalizator na wyspie; krawężniki gardzieli to łuki
   generatora, nie odrys.
3. **Rozdział łącznicy E −782**: po wschodniej stronie nosa między wyspą a pasmem P-21 zostaje wąski pas trawy
   (65 trójkątów farby poza jezdnią); bliźniaczy rozdział na jezdni wschodniej (E −825…−790, N 45–62) nie odrysowany.
4. **Rozwidlenie do ronda Putry**: separator z barierą między łącznicą a dojazdem wiaduktu to trawa z krawężnikiem
   generatora (w rzeczywistości kostka / beton z barierą); klin przed nosem buduje reguła `merge` (13 m²), wielokąt
   autorski odrzucony za 0,37 m różnicy profili. Jezdnia SE w560802655:1847044938-12620261936 ma na ortofoto 4 pasy
   (zrobione tylko położenie, WORKING_VALUE).
5. **Punkt 2 recenzji (Putry N)**, **punkt 3 (MA-010, dół pierścienia)**: nie ruszone. Narzędzia z tej rundy
   (`painted_line`, `painted_arrow`, `paint_clear`, `lane_edges`) wystarczą do odrysowania; nawierzchnia przejazdu przez
   pas dzielący i plac z kostki wymagają `paved_apron` (jak w 1).
6. **Punkt 4**: P-21 przy s 610 i `s1440-merge-p21-ramp` — nadal pasy równoległe z ADR 0093 (kąt do kierunku jazdy nie
   zmierzony ponownie); zrobione: jodełka przed nosami E −782 i s 1440, ukośne pasma przy łącznicach. s 610 (pole do
   zach. krawędzi, ramię wsch., droga gruntowa, U-25) — nie ruszone.
7. **Punkty 5–7**: szew łata / jezdnia, krawężniki (odsłona, moduł, tekstura, UV kostki), sprzątanie linii, atlas P-13,
   wzór P-8, P-11 obok P-10 — nie ruszone. Linie krawędziowe P-7b przy krawężnikach na odcinkach BEZ pomiaru są nadal
   malowane z reguły klasy drogi (na ortofoto Andersa ich nie ma).
8. **Kamery**: przestawione `p0_lamp_w1101181473_eye`, `p0_kerb_merge_eye`, `p0_lamp_putry_eye`, `eye_putry_n`; dodane
   `r2_bay_eye`, `r2_n100_eye`, `r2_fork_link_eye`, `r2_kerb_merge_main_eye`. Ocena `visual-critic` i zrzut z telefonu —
   dla lidera (agent nie tworzy subagentów, telefonów nie używa).
9. WORKING_VALUE: szerokości „jedna na krawędź” (łącznica E −782 4,2 m w środku profilu, w266084693 przed rozwidleniem),
   `RING_HOLD_M` 12 m, `RING_BLEND_M` 30 m, `RING_JOINT_ROUND_M` 2 m, `CURVE_R0_M` / `CURVE_R1_M` 60 / 30 m,
   `ALONGSIDE_GAP_M` 1,0 m, `ALONGSIDE_MIN_RUN_M` 15 m, wzór P-1e (0,24 m, 1 / 1 m). UNVERIFIED: data mozaiki WMS
   HighResolution (zgodna z arkuszem 2024-05-27 tam, gdzie sprawdzono: wiadukt DK8).
