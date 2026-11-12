# Propozycje parametrów fizyki — 2026-11-12 (mistral)

> **Nic nie wdrażać bez weryfikacji źródła.** Statusy źródeł poprawione przy scaleniu (recenzja s14, `docs/reports/REVIEW-2026-11-12-s14-mistral-r2.md`): P2, P3, P5 i P10 są UNVERIFIED, a P8 nie ma źródła dla kabin. Zanim jakakolwiek wartość trafi do JSON-a pojazdu, trzeba znaleźć i zacytować paragraf/tabelę źródła (osobne zadanie vehicle-physics).

Zakres: tylko propozycje. **Żaden JSON pojazdu ani żaden plik kodu fizyki nie został zmieniony w tym PR.**
Wejście: `docs/reports/AUDIT-PHYSICS-SOURCES-2026-11-12-mistral.md` (gałąź `mistral/4-physics-sources`), sekcja 9 „dziesięć najważniejszych rozbieżności".
Zadanie: dla każdej pozycji **ROZBIEŻNE** i **BRAK ŹRÓDŁA** z top 10 — obecna wartość (`plik:klucz`), propozycja, źródło, pewność, przewidywany wpływ na jazdę.

Pozycje 6 (0–80 km/h = 46,2 s, status POTWIERDZONE) i 7 (nadwyżka ogranicznika 94 km/h, status UNVERIFIED) mają inne statusy niż ROZBIEŻNE/BRAK ŹRÓDŁA — poza zakresem tego dokumentu (krótkie notatki na końcu).

Wszystkie liczby „wpływu na jazdę" pochodzą z runnera .NET (`tools/physics-runner`, test `ParamComparisonTests.PhysicsParams_Comparison_2026_11_12`): produkcyjne JSON-y są ładowane i mutowane **w pamięci jako dane testu**, te same scenariusze z `tests/physics/scenarios` przebiegają dla każdego wariantu. Komenda (ta sama co CI): `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release`. Wyniki poniżej z lokalnego uruchomienia tej komendy (pełna tabela w `artifacts/physics/param-comparison-2026-11-12/summary.md`, artefakt CI `physics-results`).

Skala pewności: **wysoka** = norma prawna otwarta w audicie z paragrafem / **średnia** = karta producenta klasy / **niska** = tylko literatura klasowa / **UNVERIFIED** = brak źródła lub brak paragrafu.

---

## P1 (audyt #1, ROZBIEŻNE) — Skok zawieszenia naczepy

- **Obecnie:** `game/Assets/_Project/Vehicle/Physics/Definitions/Data/curtainsider_tridem_13_6.trailer.json` → `axles[0..2].suspension.travel` = **0.20 m**
- **Propozycja:** **0.15 m** (zakres 0.15–0.18 m; 0.15 = „high travel” klasy)
- **Źródło:** broszura Hendrickson HT Series L632 (S8 w audicie), https://www.hendrickson-intl.com/getattachment/36dba227-370f-48b6-8fe3-de02635fec76/L632.pdf — cytat: „up to 5.9 in." (= 150 mm)
- **Pewność:** średnia (karta producenta zawieszenia klasy, nie producenta tej naczepy)
- **Wpływ na jazdę (runner, wariant `p1` vs `current`):** krawężnik 15 cm lewą stroną przy 40 t: najdłuższy „lot” koła `max_wheel_airtime_s` **0.240 → 0.280 s** (wariant 0.15 m daje wynik *gorszy*, bo bump-stop łapie wcześniej); przechył naczepy 3.355° i `max_fz_ratio` 3.126 — bez zmian. Próg 7 cm, hamowanie, przyspieszenie: bez zmian (różnice < 0.001). Wniosek: sama redukcja skoku nie skraca zwisu osi w tym modelu — propozycja ostrożna, do decyzji właściciela razem z ewentualną korektą `bumpStopClearance`.

## P2 (audyt #2, ROZBIEŻNE) — Rearward amplification (RA)

- **Obecnie:** metryka wynikowa, nie pojedynczy klucz; bieżący wynik `lane_change_80@laden40`: **RA = 0.998** (audyt: 0.96–0.99)
- **Propozycja:** brak zmiany parametru w tym PR; przyjąć jako pasmo walidacji **1.0–1.24** i monitorować metrykę `rearward_amplification`
- **Źródło:** FHWA Truck Size & Weight study (A10), https://www.fhwa.dot.gov/reports/tswstudy/vehiclsaf.htm — „dla tractor-semitrailers około 1,0”. **UNVERIFIED:** górna granica „typowo 1,24” nie ma źródła (audyt l. 161), więc pasmo 1.0–1.24 jest niezweryfikowane
- **Pewność:** UNVERIFIED (wartość 1,24 bez źródła; RA zależy od geometrii i opon, nie da się ustawić jednym kluczem)
- **Wpływ na jazdę (runner):** RA 0.998 przy zmianie pasa 80 km/h @40 t — na dolnej granicy pasma FHWA; `max_articulation_deg` 0.779°. Zmiana pasa 60–80 km/h w symulacji „macha” naczepą minimalnie słabiej niż w danych FHWA — akceptowalne, bez zmiany kodu.

## P3 (audyt #3, ROZBIEŻNE) — Ostrzeżenie niskiego ciśnienia powietrza

- **Obecnie:** `game/Assets/_Project/Vehicle/Physics/Definitions/Data/tractor_4x2_generic.vehicle.json` → `air.lowPressureWarningBar` = **5.5 bar**
- **Propozycja:** **6.5 bar**
- **Źródło:** UN R13 (wersja 02, A4/S5 w audicie), https://www.mlit.go.jp/jidosha/un/UN_R013_02.pdf — **UNVERIFIED: brak paragrafu.** Wartość 6,5 bar nie ma wskazanego paragrafu/załącznika R13 (audyt na `main` l. 164: „bez cytatu”)
- **Pewność:** UNVERIFIED — brak paragrafu R13 (do znalezienia przed zmianą `lowPressureWarningBar`)
- **Wpływ na jazdę (runner, wariant `p3`):** scenariusz `air_leak_rear_circuit@laden40` — ostrzeżenie przy wycieku obwodu tylnego po **10.770 → 9.620 s** (o 1.15 s wcześniej); `min_air_service_bar` 0.0 bar bez zmiany; hamowanie/przyspieszenie bez zmian. Kierowca dostaje ostrzeżenie wcześniej (zgodność z normą UNVERIFIED do czasu znalezienia paragrafu).

## P4 (audyt #4, ROZBIEŻNE) — Średnica opony 315/80 R22.5

- **Obecnie:** `game/Assets/_Project/Vehicle/Physics/Definitions/Data/tire_315_80_r22_5.tire.json` → `radius` = **0.510 m** (promień efektywny; nominalny z rozmiaru 315/80 R22.5 = 1,0755 m średnicy)
- **Propozycja:** **bez zmiany `radius`** (0.510 m = promień statyczny pod obciążeniem 507 mm wg karty — zgodny); dodać tylko dokumentację nominalnej średnicy **1092 mm** obok pola `size`. Wariant testowy `p4` (radius 0.546 m = 1092/2) pokazuje, co *gdyby* zmienić.
- **Źródło:** karta Bridgestone M-STEER 001 (A14/S7), https://www.bigtyres.co.uk/media/landingpages/documents/bridgestone_m-steer-001_datasheet.pdf — tabela: średnica całkowita **1092 mm**, promień statyczny 507 mm
- **Pewność:** wysoka co do faktu rozbieżności (nominalna vs efektywna), niska co do potrzeby zmiany — obie wartości są fizycznie poprawne w swoich rolach
- **Wpływ na jazdę (runner, wariant `p4` vs `current`):** 0–80 km/h @40 t **47.520 → 46.453 s**, 0–50 @40 t 20.428 → 20.571 s, 0–80 @24 t 45.877 → 44.815 s; hamowanie 80→0 @40 t **40.797 → 41.292 m**, 50→0 17.315 → 17.427 m; zmiany biegów bez zmian (8). Większy promień = „wyższe przełożenie” koła: szybciej do 80 km/h, nieco dłuższa droga hamowania.

## P5 (audyt #5, ROZBIEŻNE) — Moment sprzęgła AMT

- **Obecnie:** `game/Assets/_Project/Vehicle/Physics/Definitions/Data/amt12_od_traxon_class.gearbox.json` → `clutchMaxTorque` = **4000 Nm**
- **Propozycja:** zakres klasy **2600–3400 Nm**, proponowana wartość **3400 Nm** (górna granica klasy sprzęgieł AMT przy 2500 Nm)
- **Źródło:** karta ZF TraXon (A6/S2), https://www.zf.com/public/org/Product-data-sheet_TraXon-Torque_71520.pdf — cytat: „12 TX 2611 SO max. 2,600” Nm (wejście skrzyni); klasa sprzęgieł 2500–3400 Nm
- **Pewność:** UNVERIFIED (karta podaje moment wejściowy skrzyni, nie moment sprzęgła; „klasa sprzęgieł 2500–3400 Nm” bez źródła; 4000 Nm to „bezpieczny nadmiar”, nie błąd fizyki — jak w audicie)
- **Wpływ na jazdę (runner, wariant `p5`):** ruszanie 6% pod górę @40 t — temperatura sprzęgła **36.876 → 36.563 °C**, 0–80 km/h @40 t 47.520 → 47.522 s (różnica zaniedbywalna, bo przy starcie z biegu 4 sprzęgło się nie ślizga). Różnica ujawniłaby się dopiero przy ruszaniu z 1.–2. biegu pod obciążeniem (ślizg) — patrz P10.

## P8 (audyt #8, BRAK ŹRÓDŁA) — Zawieszenie kabiny (częstotliwości, zakresy)

- **Obecnie:** `tractor_4x2_generic.vehicle.json` → `cab.pitchFrequencyHz` = **1.5**, `cab.rollFrequencyHz` = **1.6**, `cab.heaveFrequencyHz` = **1.8**, `cab.dampingRatio` = **0.5**, `cab.maxPitchDeg` = **4**, `cab.maxRollDeg` = **4**, `cab.maxHeaveM` = **0.05**
- **Propozycja:** **bez zmiany wartości** — zaproponować jawne zakresy klasy: częstotliwości **1–2 Hz**, tłumienie **ζ 0.3–0.5**, zakresy ruchu jak obecnie; oznaczyć jako WORKING_VALUE z podanym źródłem klasy
- **Źródło:** brak. Wymieniony wcześniej Gillespie („Fundamentals of Vehicle Dynamics”) bez strony/rozdziału — UNVERIFIED; Pacejka („Tire and Vehicle Dynamics”) usunięty jako źródło, bo dotyczy opon, nie zawieszeń kabin. Pasmo 1–2 Hz, ζ 0.3–0.5 — UNVERIFIED
- **Pewność:** UNVERIFIED (brak źródła; zgodność z „pasmem klasy” niepotwierdzona)
- **Wpływ na jazdę (runner, `current` jako baza):** próg 7 cm @15 km/h — kołysanie kabiny `max_cab_heave_mm` **45.0 mm**, `max_cab_pitch_deg` **1.53°**; hamowanie 80→0 @40 t — pitch kabiny **3.23°** (audyt: ~3° pitch w hamowaniu ABS — zgodne); „oko kierowcy” przy zmianie biegu `max_shift_eye_pitch_swing_deg` **3.40°**.

## P9 (audyt #9, BRAK ŹRÓDŁA) — Brak modelu temperatury hamulców (fade)

- **Obecnie:** brak parametru — `tractor_4x2_generic.vehicle.json` → `brakes.*` i `axles[*].serviceBrakeTorque` nie mają modelu temperatury; hamowanie zależy tylko od ciśnienia powietrza
- **Propozycja:** **poza zakresem tego PR** (wymaga zmiany kodu fizyki, co jest wykluczone) — zgłosić jako osobne zadanie: model fade termicznego EBS (temperatura tarcz → spadek µ) dla długich zjazdów
- **Źródło:** UN R13 typ-IIA (A4) definiuje test 7%/6 km/30 km/h — https://www.mlit.go.jp/jidosha/un/UN_R013_02.pdf; fizyka fade: literatura hamulców (Gillespie) — brak otwartego źródła w repo
- **Pewność:** wysoka co do istnienia luki (norma wymaga odporności na fade; model jej nie ma)
- **Wpływ na jazdę (runner, baza `current`):** hamowanie 80→0 suche @40 t = **40.8 m**, 50→0 = **17.3 m**, MFDD 6.99/6.65 m/s² — stabilne, bo bez fade; w rzeczywistości długi zjazd wydłużyłby drogę. Bez zmiany w tym PR.

## P10 (audyt #10, BRAK ŹRÓDŁA) — Strategia AMT (bieg startowy)

- **Obecnie:** `amt12_od_traxon_class.gearbox.json` → `maxLaunchGear` = **4**, `upshiftRpmLight/Full` = 1250/1750, `downshiftRpmLight/Full` = 850/1100, `launchRpmLight/Full` = 800/1100 obr/min
- **Propozycja:** `maxLaunchGear` **4 → 2** (zakres 1–2; realne AMT tej klasy startują z 1.–2. biegu); progi zmiany biegów bez zmiany (brak źródła publicznego — design)
- **Źródło:** brak publicznego źródła strategii OEM (stąd BRAK ŹRÓDŁA w audicie); klasa opisana w docs/04 i VEHICLE_REFERENCE_DATA.md
- **Pewność:** UNVERIFIED (brak źródła strategii biegu startowego AMT; twierdzenie „realne AMT tej klasy startują z 1.–2. biegu” niezweryfikowane)
- **Wpływ na jazdę (runner, wariant `p10` vs `current`):** 0–80 km/h @40 t **47.520 → 48.123 s**, 0–50 @40 t 20.428 → 21.030 s, 0–80 @24 t 45.877 → 46.493 s; liczba zmian biegów 0–80: **8 → 9** (także 8 → 9 przy 24 t); ruszanie 6% @40 t: 0–30 km/h 18.978 → 19.923 s, temperatura sprzęgła **36.876 → 32.546 °C**; „oko kierowcy” przy zmianie biegu 3.404 → 3.667°. Start z niższego biegu = wolniejsze 0–80, więcej zmian biegów, mniejsze obciążenie cieplne sprzęgła.

---

## Wyniki runnera (pełna tabela)

Warianty: `current` = produkcyjne JSON-y; `p1`/`p3`/`p4`/`p5`/`p10` = pojedyncza mutacja jak wyżej (dane testu, pliki produkcyjne nietknięte). Źródło: `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release --filter FullyQualifiedName~ParamComparisonTests` (lokalnie; CI: job `physics`).

| Bieg | Metryka | Jedn. | current | p1 | p3 | p4 | p5 | p10 |
|---|---|---|---|---|---|---|---|---|
| 0-50/0-80 km/h, 24 t, płasko | time_to_kmh(50) | s | 19.836 | 19.836 | 19.836 | 19.970 | 19.839 | 20.453 |
| 0-50/0-80 km/h, 24 t, płasko | time_to_kmh(80) | s | 45.877 | 45.877 | 45.877 | 44.815 | 45.879 | 46.493 |
| 0-50/0-80 km/h, 24 t, płasko | shift_count | - | 8.000 | 8.000 | 8.000 | 8.000 | 8.000 | 9.000 |
| 0-50/0-80 km/h, 40 t, płasko | time_to_kmh(50) | s | 20.428 | 20.428 | 20.428 | 20.571 | 20.430 | 21.030 |
| 0-50/0-80 km/h, 40 t, płasko | time_to_kmh(80) | s | 47.520 | 47.520 | 47.520 | 46.453 | 47.522 | 48.123 |
| 0-50/0-80 km/h, 40 t, płasko | shift_count | - | 8.000 | 8.000 | 8.000 | 8.000 | 8.000 | 9.000 |
| 0-50/0-80 km/h, 40 t, płasko | max_shift_eye_pitch_swing_deg | deg | 3.404 | 3.404 | 3.404 | 3.018 | 3.404 | 3.667 |
| ruszanie 6% pod górę, 40 t | time_to_kmh(30) | s | 18.978 | 18.978 | 18.978 | 16.837 | 18.967 | 19.923 |
| ruszanie 6% pod górę, 40 t | max_clutch_temp_c | °C | 36.876 | 36.876 | 36.876 | 38.312 | 36.563 | 32.546 |
| ruszanie 6% pod górę, 40 t | stalled | 0/1 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| ruszanie 6% pod górę, 40 t | shift_count | - | 5.000 | 5.000 | 5.000 | 5.000 | 5.000 | 6.000 |
| hamowanie 80-0 suche, solo | stop_distance_m | m | 34.689 | 34.689 | 34.689 | 34.972 | 34.689 | 34.689 |
| hamowanie 80-0 suche, solo | mfdd_ms2 | m/s² | 7.414 | 7.414 | 7.414 | 7.468 | 7.414 | 7.414 |
| hamowanie 80-0 suche, solo | max_cab_pitch_deg | deg | 3.440 | 3.440 | 3.440 | 3.398 | 3.440 | 3.440 |
| hamowanie 80-0 suche ABS, 40 t | stop_distance_m | m | 40.797 | 40.797 | 40.797 | 41.292 | 40.797 | 40.797 |
| hamowanie 80-0 suche ABS, 40 t | mfdd_ms2 | m/s² | 6.985 | 6.985 | 6.985 | 6.910 | 6.985 | 6.985 |
| hamowanie 80-0 suche ABS, 40 t | max_articulation_deg | deg | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| hamowanie 80-0 suche ABS, 40 t | max_cab_pitch_deg | deg | 3.233 | 3.233 | 3.233 | 3.162 | 3.233 | 3.233 |
| hamowanie 50-0 suche ABS, 40 t | stop_distance_m | m | 17.315 | 17.315 | 17.315 | 17.427 | 17.317 | 17.315 |
| hamowanie 50-0 suche ABS, 40 t | mfdd_ms2 | m/s² | 6.651 | 6.651 | 6.651 | 6.649 | 6.650 | 6.651 |
| zmiana pasa 80 km/h, 40 t | rearward_amplification | - | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 | 0.998 |
| zmiana pasa 80 km/h, 40 t | max_articulation_deg | deg | 0.779 | 0.779 | 0.779 | 0.779 | 0.779 | 0.779 |
| próg 7 cm @15 km/h, 40 t | max_cab_heave_mm | mm | 45.037 | 45.037 | 45.037 | 44.731 | 45.037 | 45.037 |
| próg 7 cm @15 km/h, 40 t | max_cab_pitch_deg | deg | 1.529 | 1.529 | 1.529 | 1.473 | 1.529 | 1.529 |
| próg 7 cm @15 km/h, 40 t | max_wheel_airtime_s | s | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| krawężnik 15 cm lewą stroną, 40 t | max_wheel_airtime_s | s | 0.240 | 0.280 | 0.240 | 0.240 | 0.240 | 0.240 |
| krawężnik 15 cm lewą stroną, 40 t | max_trailer_roll_deg | deg | 3.355 | 3.355 | 3.355 | 3.334 | 3.355 | 3.355 |
| krawężnik 15 cm lewą stroną, 40 t | max_fz_ratio | - | 3.126 | 3.126 | 3.126 | 3.105 | 3.126 | 3.126 |
| wyciek obwodu tylnego, 40 t | time_low_air_warning | s | 10.770 | 10.770 | 9.620 | 10.860 | 10.770 | 10.770 |
| wyciek obwodu tylnego, 40 t | min_air_service_bar | bar | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

## Notatki o pozycjach top 10 poza zakresem statusów

- **#6 (0–80 km/h @40 t):** status POTWIERDZONE — runner mierzy 47.520 s (audyt 46.2 s dla innego przebiegu), oba w paśmie walidacji 40–95 s. Bez propozycji zmiany.
- **#7 (nadwyżka ogranicznika do 94 km/h):** `driveline.overrunBrakeOffsetKmh` = 4.0, status UNVERIFIED — polski limit drogowy 80 km/h (A12) jest już osobnym parametrem świata, nie pojazdu. Bez propozycji w tym PR.

## Pliki w tym PR

- `docs/proposals/PHYSICS-PARAMS-2026-11-12-mistral.md` (ten dokument)
- `tools/physics-runner/Tests/ParamComparisonTests.cs` (nowy test porównawczy; parametry jako dane testu)
- `tools/physics-runner/Sim/ScenarioRunner.cs` (opcjonalny parametr `DefinitionSet` w `Setup`/`Run`/`CargoFor`, żeby test mógł podać wariantowe definicje; domyślnie nadal produkcyjne JSON-y)

Weryfikacja lokalna: `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release` — 156/156 passed; `dotnet run -c Release --project tools/physics-runner/Runner` — ALL 107 SCENARIOS PASSED (550 checks).
