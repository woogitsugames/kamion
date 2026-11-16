# ADR 0228 — Przegub: kontakt kabina–naczepa zamiast kątowego ogranicznika 90°, jedno źródło geometrii, tłumione lądowanie

Status: Proposed (agent fizyki, chmura E/E1, gałąź `jackknife-0228`), 2026-11-15. Scalenie i pomiar na telefonie: lider.
Aktualizacja H11 (2026-11-16, chmura H r3): merge `origin/main`, P1 z recenzji s22 #113, zgodność z FFB #132 (ADR 0263) — sekcja
„Aktualizacja H11” na końcu.
Dotyczy: BACKLOG-S21 **B-077** (bramka 2, `docs/03` „jackknife możliwy przy błędzie kierowcy, brak eksplozji solvera”),
ADR 0158 Open 3 (jedno źródło geometrii) i Open 4 (lądowanie prawie sprężyste), ADR 0165 „Otwarte” (brak kontaktu ciągnik–naczepa
przy złożeniu ≥ 90°), ADR 0201b F2 (stopy bez odbicia), D58/D59.

## Kontekst
- Przegub ograniczał **kątowy** miękki stop ±90° w `FifthWheel` (3 Hz, ζ 1). Nie ma tam żadnego ciała: kabina, błotniki i przód
  naczepy nie istniały dla solvera, a w Unity `VehicleBody.ConnectTrailer` wyłącza kolizje PhysX między ciągnikiem a naczepą
  (ADR 0165 pkt 5). W runnerze nie było kontaktu ciągnik–naczepa w ogóle.
- Geometria koliderów była kopiowana: stałe w `BodyGroundContact` (runner) i w builderach graybox (Unity) — ADR 0158 Open 3.
- Zrzut zestawu z 1 m: pierwszy apeks oddaje ~80 % energii spadku (ADR 0158 Open 4). Zmierzone tu: zrzut 0,5 m, 40 t —
  **68 %** energii wraca, zestaw drugi raz odrywa się od ziemi na **0,27 s**.

## Decyzja
1. **Jedno źródło geometrii nadwozia: `bodyBoxes` w danych pojazdu** (`VehicleDefinition.bodyBoxes`,
   `TrailerDefinition.bodyBoxes`; JSON w `game/Assets/_Project/Vehicle/Physics/Definitions/Data/`, ładowane przez JsonUtility w grze
   i System.Text.Json w runnerze). Każde pudełko ma flagi `ground` (kontakt nadwozie–droga runnera = lustro BoxColliderów PhysX)
   i `coupling` (kontakt ciągnik–naczepa). Ciągnik: Frame, Cab, Bumper (tylko `ground`), Mudguard_L/R (tylko `coupling`);
   naczepa: Body, Beams, RearUnderrun. Wartości **DERIVED** z `art-source/truck/dims.json` i stałych builderów graybox:
   `tests/physics/test_dims_sync.py::test_body_boxes_*` przelicza każde pudełko z dims.json, xUnit
   `BodyBoxes_GroundSet_EqualsGrayboxColliderMirror` porównuje je ze starym lustrem z ADR 0158, a EditMode
   `BodyBoxGeometryTests` buduje graybox w edytorze i porównuje BoxCollidery i błotniki z danymi. Runner czyta kolidery z danych;
   formuła z ADR 0158 została tylko jako awaryjna (definicja bez pudełek) i wyrocznia testu.
2. **Kontakt ciągnik–naczepa w rdzeniu** (`CouplingContact` w `Components/FifthWheel.cs`, używany przez `CombinationModel`, więc gra
   dostaje go bez zmian w adapterze Unity):
   - wykrywanie w układzie ciągnika: test 2D pudełko–pudełko w płaszczyźnie drogi (osie rozdzielające obu rzutów, ściana
     odniesienia + przycięta krawędź incydentna, jak `b2CollidePolygons` w Box2D), w **dwóch warstwach wysokości** (dół i góra
     wspólnego zakresu wysokości), bo naczepa pochylona na kołysce siodła albo przechylona przesuwa się z wysokością;
     zakres pionowy liczony w układzie naczepy w danym miejscu;
   - **tylko kontakty boczne** (normalna pozioma: ściana boczna albo narożnik przodu naczepy na kabinie). Punkt, w którym pionowe
     nakładanie się jest mniejsze niż poziome wnikanie (pudła spotykają się góra–dół), jest odrzucany: pierwsza wersja z kontaktem
     pionowym „kładła” naczepę na błotnikach przy przechyle 11° w `fuzz_shrink_speed_runaway_fulllock` (69 kN na plastikowym
     błotniku) i usuwała wywrotkę z repro F2. Pudło naczepy graybox jest pełnej szerokości do 1,22 m, a prawdziwa naczepa ma tam
     wąską szyję; błotnik z tworzywa nie niesie naczepy;
   - margines spekulatywny 0,05 m (bez tunelowania przy 55°/s), stałe bufory, **0 B alokacji na krok** (test
     `CombinationStep_WithBodyContact_DoesNotAllocate`, 200 kroków w kontakcie);
   - rozwiązanie w tym samym PGS co przegub siodła (8 iteracji): na punkt jednostronna sprężyna z tłumikiem całkowana niejawnie
     (soft constraint, E. Catto, GDC 2011; ta sama postać co kontakt nadwozie–droga z ADR 0165), k = m (2πf)², c = 2ζ m (2πf).
     Masa `m` = większa z masy punktowej dwóch wolnych brył i bezwładności przegubu widzianej w punkcie (mYaw / ramię²): przy
     samej masie punktowej kontakt w trybie składania był kilka razy miększy niż nominalne f (pierwsza próba: 14 cm wnikania);
   - **bez odbicia**: impuls nie może rozpychać brył szybciej niż `contactRecoverySpeed` 0,05 m/s (zgniatane panele; ten sam
     mechanizm co stopy siodła w ADR 0201b F2); tarcie Coulomba μ 0,3 (stożek kołowy);
   - wynik jako siła i moment względem środka masy każdej bryły (`ContactForceOnTrailer`, `ContactTorqueOn{Trailer,Tractor}`),
     dodawane w `CombinationModel.Step`, także przy rozpiętym siodle (ciągnik cofający w stojącą naczepę).
3. **Kątowy stop przegubu tylko awaryjnie**: działa, gdy ciągnik albo naczepa nie ma pudełek `coupling` (test
   `NoBodyBoxes_FallsBackToAngularStop`: 90°, maks. 91,8°). Metryka `articulation_limit_excess_deg` liczy nadmiar względem
   **geometrycznego** kąta pierwszego kontaktu (`CouplingContact.FirstContactArticulationDeg`), a bez geometrii względem
   `yawLimitDeg`.
4. **Lądowanie: histereza odbojnika przy odciążaniu** (`SuspensionDefinition.bumpStopHysteresis`): gdy odbojnik się rozpręża
   (ḃ < 0), jego siła to k b² (1 + h ḃ), nie mniej niż 0 — postać Hunt–Crossley (K. H. Hunt, F. R. E. Crossley, J. Appl. Mech.
   42(2), 1975, 440–445). Przy ściskaniu odbojnik zostaje sprężysty, więc szczyty Fz na krawężnikach (sufity w
   `test_scenario_strictness.py`) się nie zmieniają. Wersja symetryczna (tłumienie także przy ściskaniu) podnosiła
   `max_fz_ratio` krawężnika 14 cm z 3,66 do 5,76 i 27 cm z 6,02 do 10,7 — odrzucona.

### Wartości
| parametr | wartość | status | uzasadnienie |
|---|---|---|---|
| `contactFrequencyHz` / `contactDampingRatio` | 5 Hz / 0,3 | WORKING_VALUE | brak zmierzonej sztywności zgniotu tylnej ściany kabiny i narożnika naczepy dla tego fikcyjnego zestawu. Ograniczenia: wnikanie przy pchaniu naczepy osią napędową ≤ 7 cm, szarpnięcie `max_dv_step_ms` ≤ 0,35 m/s w `jackknife_wet_curve_retarder_noabs@empty` (prawdziwy jackknife przy ~35 km/h, uderzenie przy ~83°/s). Przegląd niżej |
| `contactRecoverySpeed` | 0,05 m/s | WORKING_VALUE | restytucja ≈ 0 (zgniatane panele, PhysX domyślnie bounciness 0); KE oddawana przez zgnieciony kontakt ≤ ½ m v² |
| `contactFriction` | 0,3 | WORKING_VALUE (UNVERIFIED) | lakierowana stal / GRP po aluminium; brak źródła |
| `contactMargin` | 0,05 m | WORKING_VALUE | przy 55°/s narożnik na promieniu 2,4 m przesuwa się 2,3 cm na krok 10 ms |
| `bumpStopHysteresis` | 4 s/m (wszystkie osie) | WORKING_VALUE | brak pomiaru histerezy odbojników. Przy ḃ = −0,25 m/s siła rozprężania spada do 0 (odbojnik z mikroporowatego PU „martwy” przy szybkim odbiciu). Przegląd niżej |
| `yawLimitDeg` | 90° | WORKING_VALUE, tylko awaryjnie | bez zmian w danych |

Przegląd f/ζ (runner, przed zmianą 4 Hz/ζ 1 → 5/0,3; `max_dv_step_ms` / wnikanie):

| f / ζ | jackknife mokro retarder pusty | to samo 40 t | cofanie S 40 t |
|---|---|---|---|
| 4 / 1 | **0,420 FAIL** / 0,060 m | 0,315 / 0,070 m | 0,191 / 0,032 m |
| 6 / 0,3 | 0,346 / 0,060 m | 0,282 / 0,069 m | 0,170 / 0,027 m |
| **5 / 0,3** | **0,295** / 0,073 m | 0,241 / 0,081 m | 0,142 / 0,034 m |
| 8 / 0,3 | **0,441 FAIL** / 0,042 m | 0,362 / 0,054 m | — |

Przegląd `bumpStopHysteresis` (zrzut 0,5 m, postój; udział energii w pierwszym odbiciu / czas ponownego lotu):

| h [s/m] | pusty | 24 t | 40 t |
|---|---|---|---|
| 0 (przed) | 0,370 / 0 | 0,666 / 0,29 s | 0,677 / 0,27 s |
| 2 | 0,206 / 0 | 0,448 / 0,06 s | 0,461 / 0,02 s |
| **4** | **0,162 / 0** | **0,378 / 0** | **0,389 / 0** |
| 8 | 0,145 / 0 | 0,347 / 0 | 0,358 / 0 |

Powyżej ~4 s/m zysk jest mały: resztę energii oddaje opona (bezstratna sprężyna 1e6 N/m w szeregu). Sprawdzona też strata opony
przy odciążaniu (10 kN s/m): 40 t → 0,35, ale zmienia przebieg nacisku osi w hamowaniu ABS (`GoldenTelemetry_Matches` dla 3 scenariuszy
hamowania) — nie wprowadzona, zostaje w „Otwarte”. Histereza odbojnika zmieniła złotą telemetrię jednego scenariusza:
`brake_80_0_dry_abs_comb@laden40` (przednia oś dobija w hamowaniu 40 t; po zatrzymaniu kołysanie wygasa szybciej). Droga hamowania
41,31 → 41,25 m, MFDD 6,885 → 6,899 m/s². Plik `tests/golden/brake_80_0_dry_abs_comb_laden40.csv` przepisany (`--update-golden`).

### Geometria i kąt kontaktu
Poziomy zestaw dotyka pierwszy raz przy **117,12°**: ściana boczna naczepy (pół szerokości 1,275 m) na tylnym narożniku kabiny
(x 1,245 m, 2,07 m przed sworzniem). Analitycznie 1,245 cos φ + 2,07 sin φ = 1,275 → φ = 180 − 31,02 − 31,86 = 117,1°
(test `FirstContactAngle_FromGeometry`). Przód naczepy (narożnik pudła graybox 1,622 m przed sworzniem, promień 2,063 m) mija
tylną ścianę kabiny (2,07 m) o 7 mm; skrzydła przechodzą 8,5 cm pod podłogą pudła (1,22 vs 1,135 m), więc przy tej geometrii
najpierw kabina. Przy złożeniu ~45–55° i pochyleniu naczepy do przodu o ≥ ~0,2° górny narożnik przodu naczepy ociera o tył kabiny
(zaobserwowane: `jackknife_reverse_countersteer_comb@empty` t ≈ 13,1 s, 20 kN, wnikanie < 1 mm). To zgodne z pudłami, ale
prześwit 7 mm wynika z WORKING_VALUE (pudło graybox z płaską ścianą przednią; model ma zaokrąglony narożnik 2,029 m, limit
96/53/EC 2,04 m) — decyzja w „Otwarte”.

## Scenariusze i kryteria (`tests/physics/generate_jackknife_scenarios.py`)
| scenariusz | warunki | kryteria |
|---|---|---|
| `jackknife_fold_90_reverse_comb` / `_empty` | cofanie, pełny skręt od 30°, hamowanie przy ~95° | maks. przegub 95–112° (za starym stopem 90° + 3,5°, przed kabiną), `coupling_contact_s` 0, wnikanie 0, NaN 0, skok pozycji ≤ 1e-4 m, dv/krok ≤ 0,35 m/s, siodło ≤ 5 mm |
| `jackknife_fold_120_reverse_comb` (pusty, 40 t) | jw., gaz trzymany 3 s po kontakcie („kierowca chce 120°”) | kontakt ≥ 1 s, nadmiar ponad 117,12° ≤ 2,5°, wnikanie ≤ 7 cm, restytucja ≤ 0,1, maks. prędkość kątowa brył ≤ 60°/s + jw. |
| `jackknife_fast_fold_impact_comb` (pusty, 40 t) | pełny gaz na wstecznym, uderzenie przy ≥ 30°/s względnie | jw. + `max_articulation_rate_dps` ≥ 30 |
| `jackknife_reverse_countersteer_comb` (pusty, 40 t) | cofanie, kontra przy ~60–70°, potem jazda w przód ze skrętem w stronę naczepy | nadmiar ≤ 2,5°, wnikanie ≤ 7 cm, końcowy przegub ≤ 15° (nic się nie klei do kabiny) |
| `drop_05m_comb` (pusty, 40 t) | zrzut 0,5 m na postoju | odbicie ≤ 45 % energii spadku, ponowny lot ≤ 0,1 s, wnikanie nadwozia ≤ 5 cm, energia w locie nie rośnie (≤ 1 J), CoM ≥ 0,5 m |

Nowe metryki: `max_coupling_penetration_m`, `max_coupling_contact_force_kn`, `coupling_contact_s`, `coupling_contact_restitution`
(prędkość przegubu od kabiny w 1 s po kontakcie / prędkość dojścia), `max_articulation_rate_dps`, `max_body_rate_dps`,
`drop_rebound_ratio`, `drop_relaunch_s`. Kolumny CSV: `coupling_contacts, coupling_pen_m, coupling_force_kn,
tractor_ang_rate_dps, trailer_ang_rate_dps`.

## Liczby przed / po (runner .NET, dt 10 ms, 4 substepy; „przed” = ten kod z `--no-coupling-contact --elastic-landing`)
| scenariusz | metryka | przed | po | limit |
|---|---|---|---|---|
| fold_90 40 t / pusty | maks. przegub [°] | 91,8 / 91,7 | **108,6 / 105,4** | 95–112 |
| fold_120 40 t / pusty | kontakt [s] | 0 / 0 | **7,47 / 9,32** | ≥ 1 |
| fold_120 40 t / pusty | wnikanie [m] | — | **0,046 / 0,051** | ≤ 0,07 |
| fold_120 40 t / pusty | restytucja | — | **0,032 / 0,030** | ≤ 0,1 |
| fast_fold 40 t / pusty | prędkość przegubu [°/s] | 53,3 / 50,3 | 53,3 / 54,3 | ≥ 30 |
| fast_fold 40 t / pusty | wnikanie [m] / restytucja | — | **0,050 / 0,053**; 0,028 / 0,029 | ≤ 0,07; ≤ 0,1 |
| fast_fold 40 t | dv/krok [m/s] | 0,240 | 0,225 | ≤ 0,35 |
| countersteer pusty / 40 t | maks. przegub, końcowy [°] | 91,9 / 91,9, ~0 | **118,5 / 111,6**, ~0 | ≤ 15 końcowy |
| reverse_dock 40 t / pusty | maks. przegub [°] | 91,7 / 91,4 | **118,2 / 118,1** | nadmiar ≤ 1,5 |
| retarder mokro pusty | maks. przegub [°], dv [m/s] | 92,6, 0,238 | **119,3, 0,295** | dv ≤ 0,35 |
| drop 0,5 m 40 t / pusty | odbicie | **0,677** / 0,370 | **0,389 / 0,162** | ≤ 0,45 |
| drop 0,5 m 40 t | ponowny lot [s] | **0,27** | **0** | ≤ 0,1 |
| `free_fall_drop_comb` (1 m, 24 t, 30 km/h) | odbicie, ponowny lot | 0,782, 0,65 s | 0,296, 0,16 s | — (bez checku) |

Max prędkość kątowa brył we wszystkich scenariuszach kontaktu ≤ 35,1°/s (przed: ≤ 35,1°/s), NaN 0, skoki pozycji ≤ 1e-14 m.
Uderzenie w swobodnej przestrzeni (`YawImpact_InFreeSpace…`, 40 t, 1 rad/s względnie, bez grawitacji i drogi): energia
KE + sprężyny sprzęgu w oknie uderzenia rośnie o **0,000 J** na krok (kontrola sprężysta: +697 J), przegub 118,27°, wnikanie
0,040 m, prędkość od kabiny po zwolnieniu 0,13 rad/s (dalej to już koziołkowanie pary w próżni).

Pełny pakiet (`artifacts/jackknife-0228/full-runner.log`): **145 scenariuszy, 879 checków, ALL PASSED** (10 nowych przebiegów; main: 135).
`dotnet test tools/physics-runner`: **295/295** (main 277). `--robustness` (`artifacts/jackknife-0228/robustness/robustness.md`):
determinizm BIT-IDENTICAL (6 scenariuszy), 0 biegów z NaN, skoki pozycji ≤ 3,9e-14 m, fuzz krawężników dv ≤ 0,26 m/s,
soak 30 min dv ≤ 0,18 m/s. Koszt kroku (`--bench`, 40 t jazda prosto, desktop Release, 3 × A/B,
`artifacts/jackknife-0228/bench-ab.log`): p50 **13,6–13,7 µs** z kontaktem vs 13,2–13,3 µs bez (+0,4 µs ≈ 3 %: test pudełek
co krok, bo pudło naczepy leży nad ramą i błotnikami); średnie 19–21 µs w obu wariantach (szum). Na telefonie — pomiar lidera.

Wykresy (`tests/physics/plot_jackknife.py`, obejrzane): `artifacts/jackknife-0228/png/` — przegub przed/po z linią 117,12°,
wnikanie, siła kontaktu, prędkości kątowe; zrzut 0,5 m: wysokość, ugięcie, nacisk koła przed/po. CSV 20 Hz (gzip) przed/po:
`artifacts/jackknife-0228/csv/`.

## Konsekwencje
- Gra (Unity) dostaje kontakt automatycznie: `CombinationModel` → `FifthWheel.Solve`, geometria z `VehicleDataAsset` (JSON).
  `Physics.IgnoreCollision` między ciągnikiem i naczepą zostaje (kontakt jest w solverze, nie w PhysX — bez podwójnej siły).
- Złożenie przy cofaniu idzie teraz do ~118° (było 90°). Na telefonie: naczepa może zajść głębiej i „stuknąć” w kabinę
  (szczyt 200–270 kN przez ~0,1 s przy 50°/s), bez odbicia; dalej pchana oś napędowa trzyma ją na kabinie (~100 kN, 3–5 cm).
- Zestaw zrzucony z 0,5 m nie podskakuje drugi raz; widać jeszcze 2 wyraźne kołysania (opona). Hamowanie 40 t: przód po
  zatrzymaniu kołysze krócej.
- Unity, PlayMode: kontakt z PhysX (krawężniki, ściany) bez zmian; `External*Force` nadal nie są podawane (ADR 0165 Otwarte).

## Otwarte
1. ~~**Prześwit przodu naczepy do kabiny 7 mm**~~ — H11: obrys kontaktowy = zaokrąglony przód z modelu (2,029 m), prześwit 4,1 cm
   (niżej). Zostaje: zatrzymanie z 13–20 km/h przy 55–60° (głównie 40 t) daje po zatrzymaniu muśnięcie (≤ 0,61 mm, ≤ 1,33 km/h,
   ciągnik kołysze się ~1,2° do tyłu). Pełne usunięcie = decyzja o wymiarach (odstęp tyłu kabiny od sworznia 2,07 m, `fifth_wheel_lead`
   ograniczone długością 16,50 m) albo o tłumieniu kołysania ciągnika — lider/właściciel po feel teście.
2. Brak kontaktu pionowego (naczepa na błotniku/ramie) i brak geometrii podpór naczepy i szyi — świadomie poza zakresem.
3. Strata energii opony (lądowanie z 1 m nadal ma 0,16 s lotu) — zmienia złotą telemetrię hamowania; do decyzji z feel testem.
4. Unity nie było uruchamiane (chmura bez edytora): kompilacja C# 9 sprawdzona tylko kompilatorem .NET 8 z `LangVersion 9`
   (te same źródła). EditMode `BodyBoxGeometryTests`, PlayMode `CombinationLabTests` / `KerbStrikeParityTests` i feel test —
   lider. Po rozpięciu kontakt kabina–naczepa liczy solver; czy `ConnectTrailer` przywraca kolizje PhysX po rozpięciu, nie
   sprawdzano (kod Unity-only, poza własnością fizyki).
5. Feel test właściciela (B-075): cofanie pod rampę z kontrą, „stuk” w kabinę, zrzut/próg; po H11 także kierownica z FFB przy
   „stuku” (wygładzenie 0,5 s — WORKING_VALUE, decyzja feelingu).
6. (H11) `CouplingContact.MaxPoints` = 64 (4 × 4 pudła × 4 punkty); naczepa DLC z większą liczbą pudeł `coupling` zatrzyma się
   wyjątkiem przy `SetGeometry` — trzeba podnieść stałą (bufory solvera rosną liniowo).
7. (H11) Normy wolnej przestrzeni siodła przy pochyleniu naczepy (np. ISO 1726) nie zostały przeczytane — tolerancja 1,13° / 1,44°
   to wynik geometrii WORKING_VALUE, nie wymóg (UNVERIFIED).

## Aktualizacja H11 (2026-11-16)
**Merge `origin/main` (498 commitów od `fc450006c`).** Bez konfliktów tekstowych. Semantycznie: main nie zmienił rdzenia
fizyki (`Vehicle/Physics`, `tools/physics-runner`, `tests/physics`, `tests/golden` poza 1 linią `swept_path_gate3.py`); prefaby
graybox przegenerowane (kolejność fileID), BoxCollidery liczone w builderach — bez wpływu na `bodyBoxes`. Nowe na main i istotne:
FFB kierownicy PC (#132, ADR 0263: `ForceFeedbackModel` czyta `VehicleModel.AligningTorqueTotal` i naciski osi skrętnej),
CI `dist-tests`. Po merge'u przed zmianami: .NET 295/295, runner 145/879 PASS (= przed merge'em).

**P1 recenzji (prześwit 7 mm).** Sondy runnera (skręt w przód 55–60°, pełne hamowanie): stary obrys dawał kontakt kabina–naczepa
0,11–6,8 s, 38–131 kN (przy 20 km/h i 40 t kontakt już w ustalonym skręcie przez przechył naczepy) — „hamowanie” naczepy przez
kabinę. Decyzja o geometrii, nie o parametrach kontaktu: obrys **kontaktowy** przodu naczepy = zaokrąglony przód modelu
(promień 2,0294 m zmierzony w eksporcie Blendera, `trailer_manifest.json` `measured.front_swing`, DERIVED; ≤ 2,04 m z 96/53/EC):
pudła `BodyCoupling` (pełna szerokość do z = 1,578 m) i `Nose` (1,578–1,622 m, szerokość 2,438 m); `Body` zostaje tylko kolizją
z ziemią (lustro PhysX graybox). Prześwit do tyłu kabiny **4,1 cm**; bez kontaktu do 110° przy |pochyleniu| ≤ 1,13° i |przechyle|
≤ 1,44° względem ciągnika. Kąt pierwszego kontaktu bez zmian **117,12°**. Nowe scenariusze `jackknife_tight_turn_forward_comb`
(5 km/h) i `_10_comb` (10 km/h, druga strona), przegub 57–58,5°, pełne hamowanie w 40 s: **0 kontaktu** (pusty i 40 t).
Pozostałość — „Otwarte 1”.

**Zgodność z FFB #132.** Ścieżka: siła kontaktu → bryły ciągnika i naczepy (nie do `AligningTorqueTotal` wprost) → kontakt w ~0,1 s
odwraca odchylanie ciągnika i przeciąga oś skrętną w bok → moment samonastawności opon (ślad × Fy) przechodzi przez szczyt
(40 t, wjazd w kabinę: −0,9 → +2,3 kN m w 80 ms) → `ForceFeedbackModel` (domyślne, slew 20/s) przerzucał wyjście −0,75 → +1,0
w ~0,1 s = szarpnięcie; to samo trafia do powrotu kierownicy dotykowej. Poprawka w rdzeniu: `CombinationModel` zgłasza kontakt
(`VehicleModel.NotifyBodyContact`), a `AligningTorqueTotal` jest wtedy i 0,5 s po nim opóźnieniem 1. rzędu (0,5 s) surowej wartości
(`AligningTorqueRaw`), po czym zbiega i oddaje surową (skok < 1 N m na kołach); siły opon na pojazd bez zmian.
`steering.contactFeedbackLagS` / `contactFeedbackHoldS` = 0,5 / 0,5 s, WORKING_VALUE (decyzja feelingu).

| miara (krok 10 ms, moment na wieńcu) | bez wygładzenia | H11 | odniesienie |
|---|---|---|---|
| zmiana celu FFB w oknie kontaktu, fold_120 40 t / pusty | 4,53 / 3,29 N m | **0,48 / 0,34** | zmiana pasa 80 km/h 0,03; krawężnik 15 cm 1,69; uderzenie w krawężnik 14 cm 50 km/h 3,77 (człon „road feel”) |
| to samo, fast_fold 40 t / pusty; countersteer pusty | 5,50 / 3,52; 3,81 | **0,49 / 0,38; 0,36** | limit testu 0,6 N m (7,5 % pełnej skali) |
| zmiana wyjścia FFB na krok (maks.) | 0,200 (= limit slew) | **≤ 0,061** | slew 0,2 |

Testy: xUnit `JackknifeForceFeedbackTests` (prawdziwy `ForceFeedbackModel` + `WheelAxis` kompilowane z `game/Assets/_Project/Input`
w projekcie testów, krok jak `DrivingLabBootstrap`), mutacja bez wygładzenia łapie kopnięcie (4,53 N m), powrót do surowej wartości po
kontakcie (countersteer: 0 N m różnicy na końcu). `JackknifeContactTests`: obrys przodu (2,029 m, ≥ 4 cm), brak kontaktu do 110°
przy ±0,5°, tolerancja pochylenia/przechyłu, odrzucenie zbyt wielu pudeł (P2 recenzji: `CouplingContact.MaxPoints` 64 +
`FormatException` w `SetGeometry`). EditMode `BodyBoxGeometryTests.TrailerCouplingOutline_AndFeedbackSmoothing_FromParsedDefinitions`
(ścieżka JsonUtility) — napisany, NIEuruchomiony.

Wyniki: .NET **319/319**; runner **149 scenariuszy / 915 checków PASS** (względem stanu przed H11 zmienił się tylko
`jackknife_reverse_countersteer_comb@laden40`: wnikanie 1,3 mm → 0); `test_dims_sync.py` OK (pudła `BodyCoupling`/`Nose` liczone z
manifestu); bench p50 13,4–14,3 µs vs 13,9–14,0 µs (szum, 16 zamiast 12 par pudeł). Brak alokacji na krok
(`CombinationStep_WithBodyContact_DoesNotAllocate` zielony). Wykresy (obejrzane): `artifacts/jackknife-0228/h11/png/` — `ffb_*`
(siła kontaktu, moment samonastawności, wyjście FFB przed/po), `turn_*` (skręt + hamowanie przed/po); CSV 20 Hz
`artifacts/jackknife-0228/h11/{before,after}/`, sondy `h11/probe_scenarios/`.
