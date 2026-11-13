# ADR 0158 — F2: „275 km/h w powietrzu” to spadek przez drogę; kolidery nadwozia w runnerze
Status: Proposed (agent fizyki, s16, gałąź `physics-f2`), 2026-11-13. Decyzje otwarte: lider (kerb 27 cm, F1), właściciel (feel test).

## Kontekst
Fuzz M34 (PR #37, raport `docs/reports/PHYSICS-ROBUSTNESS-2026-11-13-mistral.md` §5, recenzja
`docs/reports/REVIEW-2026-11-13-s16-mistral-r6.md`) znalazł dwa przypadki:
- **F2**: gaz 0,378 + pełny skręt w lewo od 30 km/h, cargo24, sucho. Zestaw przewraca się przy t ≈ 4 s, wszystkie 10 kół
  odrywa się od ziemi, a `max_speed_kmh` dochodzi do **275,37 km/h** (silnik na jałowym). Podejrzenie: więz siodła
  (człon bias) albo ogranicznik przegubu wstrzykuje energię.
- **F1**: przegub wychodzi 0,6–3,3° poza miękki ogranicznik 90°. To pytanie o tolerancję, nie o błąd.

## Przyczyna F2 (zmierzona)
Bilans energii E = KE + PE obu brył, repro `fuzz_shrink_speed_runaway_fulllock` na `main` 4a990b223:

| t [s] | koła w powietrzu | E [kJ] | wysokość CoM ciągnika [m] | prędkość [km/h] | prędkość pozioma [km/h] |
|---|---|---|---|---|---|
| 0,01 | 0 | 2031,0 | 1,05 | 30,0 | 30,0 |
| 4,51 | 10 | 1660,2 | 0,21 | 30,3 | 25,2 |
| 10,01 | 10 | 325,0 | −181 | 218,4 | 21,2 |
| 29,51 | 10 | −252 345 | −2961 | 765,0 | 17,0 |

- E w locie **nigdy nie rośnie**: największy przyrost między krokami bez żadnego kontaktu wynosi 0,000 kJ. E maleje, bo
  zabiera ją opór powietrza. Prędkość pozioma przez cały czas mieści się w 13–30 km/h.
- Rośnie tylko składowa pionowa: CoM spada do **−3070 m**. Pomiar `max_speed_kmh` to `SpeedFwd`, czyli rzut prędkości na
  oś „do przodu” koziołkującego ciągnika. 275 km/h to więc prędkość spadku swobodnego widziana z obróconej ramy.
- Przyczyna: w runnerze .NET jedynymi kontaktami z ziemią są promienie kół. Zastępcza bryła `RigidBody6Dof`
  („stands in for PhysX Rigidbody”) **nie ma koliderów nadwozia**. W Unity ciągnik i naczepa mają BoxCollidery
  (`GrayboxTractorBuilder` „Colliders”: Frame, Cab, Bumper; `GrayboxTrailerBuilder`: Body, Beams, RearUnderrun). Po wywrotce
  nic więc nie trzymało zestawu i spadał przez drogę. Rdzeń (`game/Assets/_Project/Vehicle/Physics/**`) nie jest winny, a więz
  siodła nie odpowiada za F2.

## Decyzja
1. **Kontakt nadwozie–ziemia w runnerze** (`tools/physics-runner/Sim/BodyGroundContact.cs`, tylko runner; w Unity robi to
   PhysX):
   - Bierzemy 8 narożników każdego pudełka kolidera i sprawdzamy je pionowym promieniem w `IGroundQuery`. Dla pudełka na
     płaszczyźnie jest to dokładne, bo kontakt zawsze leży w podzbiorze narożników.
   - Impulsy niepenetracji i tarcia Coulomba rozwiązujemy metodą PGS (10 iteracji) ze stożkiem kołowym i akumulacją.
     Liczymy je na prędkości z końca kroku przewidzianej z sił solvera. Restytucja wynosi 0 (jak domyślny materiał PhysX).
     Penetrację usuwa bias Baumgarte'a (β 0,2, slop 5 mm). Narożniki do 10 cm nad ziemią to kontakty spekulatywne, więc
     bryła nie przeleci przez drogę.
   - Wynik oddajemy jako dodatkową siłę i moment (impuls / dt) do niezmienionego `RigidBody6Dof.Integrate`.
   - Zero alokacji na krok (tablice z konstruktora, test `Solve_DoesNotAllocate`). Koszt w benchu 40 t: 7,9 → 8,3–8,4 µs
     na krok, czyli w granicach szumu.
   - Tarcie nadwozia o drogę **0,6 = domyślny PhysicsMaterial Unity** (parytet z koliderami graybox bez materiału).
     Wartość fizyczna (stal i lakier po asfalcie): UNVERIFIED.
   - Geometria jest DERIVED z builderów graybox i domyślnych `TractorDimensions`/`TrailerDimensions`. Rozstaw osi, pozycje
     ładowni i podpór pochodzą z definicji.
   - Kontakt działa wszędzie, gdzie runner całkuje bryły (`ScenarioRunner.StepBodies`: scenariusze, bench, robustness,
     touch evidence, testy).
2. **Niejawny człon żyroskopowy w `RigidBody6Dof`**. Jawne `w × (I w)` dodaje energię koziołkującej bryle: sama naczepa
   obracająca się bez momentu z |ω| = 2,5 rad/s zyskuje **+136 % KE w 30 s** (ciągnik +75 %). Wprowadzamy jeden krok Newtona
   niejawnego Eulera w układzie bryły (Catto, GDC 2015; Bullet `computeGyroscopicImpulseImplicit_Body`). Po zmianie
   przyrost KE na krok wynosi 0 we wszystkich próbach. Koszt to dyssypacja: −5…−53 % KE w 30 s skrajnego koziołkowania,
   przy jeździe pomijalna. Zmiana dotyczy tylko runnera (PhysX ma własny integrator).
3. **Repro F2 przeniesione** z `scenarios_expected_fail/` do `scenarios/` z checkami:
   - nie spada przez drogę: `min_com_height_m` ≥ 0,9, liczone nad gruntem pod CoM;
   - `body_contact_s` ≥ 1;
   - `max_body_penetration_m` ≤ 2 cm;
   - zatrzymuje się: `max_speed_after_ms` ≤ 0,05 od 8 s;
   - `max_speed_kmh` ≤ 90,5;
   - E ≤ E(0) + 5 %;
   - w fazie jazdy (do 3,5 s): `max_dv_step_ms` ≤ 0,35 i siodło ≤ 5 mm;
   - dla całego biegu z uderzeniem bokiem w drogę: `max_dv_step_ms` ≤ 4,2 = √(2 g · 0,89 m), czyli spadek CoM naczepy
     z apeksu wywrotki (2,164 m) do leżenia na boku (1,275 m).
4. **Nowy scenariusz balistyczny** `free_fall_drop_comb`: cargo24 podniesione o 1 m, 30 km/h, bez gazu. W swobodnym locie,
   czyli bez promienia koła, podpory i kolidera w dwóch kolejnych próbkach (metryka `free_flight_s` = 1,04 s), sprawdzamy:
   - `max_free_flight_energy_gain_j` ≤ 1 J (zmierzone: 0);
   - `max_free_flight_accel_error_ms2` ≤ 0,05 m/s². To |a_CoM − g|, a granica wynika z oporu 0,5·1,2·7,5·9²/30 000 =
     0,012 m/s². Zmierzone: 0,0077 m/s².
5. **`kerb_step_27cm_42kmh_comb` tymczasowo bez koliderów** (`overrides.bodyContact = false`, emitowane przez generator). Z
   koliderami prawy dolny narożnik zderzaka (0,35 m nad drogą) uderza w drogę przy t ≈ 2,83 s. Bez kontaktu nachodzi
   na drogę o 11,5 cm. Skutek: `max_dv_step_ms` 0,755 m/s i błąd siodła 7,9 mm, przy przypiętych przez
   `test_scenario_strictness.py` limitach 0,35 i 5. Ten sam event w Unity PlayMode (`KerbStrikeParityTests`, log
   „kerb 27 cm 42 km/h 40 t mesh”) już teraz daje **max |dv| 0,968 m/s i 28 kontaktów nadwozia** (pierwszy: Frame ciągnika ×
   Body naczepy). Strażnicy powstali bez koliderów, a wybór między podniesieniem limitów a zmianą geometrii jest decyzją
   lidera (Open 1).

## Liczby przed/po
- Runner (wszystkie scenariusze):
  - przed: **127 scenariuszy / 707 checków, ALL PASSED**;
  - po: **129 / 730, ALL PASSED**;
  - 707 dotychczasowych wartości: z samymi koliderami wszystkie identyczne co do znaku. Po zmianie żyroskopowej zmieniło
    się 33, z czego największe istotne to `max_dv_step_ms` w `jackknife_wet_curve_retarder_noabs` o −0,14 % i −0,11 %,
    a reszta mieści się w ≤ 0,01 % albo na poziomie zaokrągleń (`max_pos_jump_m`, roll ~1e-14).
- `dotnet test`: 263/263 (258 dotychczasowych + 5 nowych w `BodyContactTests`).
- `pytest tests/physics`: 26/26 (z `uv run --with pytest --with matplotlib --with numpy --with scipy`).
- Repro F2:

  | wersja | max_speed_kmh | min CoM [m] | max_dv_step | siodło | nadmiar przegubu |
  |---|---|---|---|---|---|
  | przed | 275,37 | −3070 | 0,678 | 2,13 mm | 2,23° |
  | po | 30,26 | 1,047 | 0,103 (jazda) / 2,04 (uderzenie) | 0,78 mm (jazda) / 24,5 mm (uderzenie; 9 mm w leżeniu) | 0 |

  Po zmianie zestaw ląduje na boku (roll −89,7°), sunie i stoi od t ≈ 5 s.
- Polowanie na wywrotki: 72 biegi po 30 s (empty/cargo24/laden40 × gaz 0,2/0,4/0,6 × skręt ±1 × 20/30/40/50 km/h), 36 z nich
  się przewraca:

  | wariant | spadki przez drogę | > 90,5 km/h | prędkość maks. | biegi z zyskiem E w locie > 1 J | nadmiar przegubu (maks.) |
  |---|---|---|---|---|---|
  | main | 36 | 8 | 290,6 km/h | 18 (do 773 J/krok) | 72 biegi (3,82°) |
  | ta gałąź | 0 | 0 | 50,6 km/h | 0 | 36 biegów (2,77°) |

  Ta gałąź: max dv 2,71 m/s przy uderzeniach (≤ 4,2), siodło maks. 36,9 mm przy wywrotce, penetracja ≤ 0,4 mm.
- Fuzz 8 zielonych szablonów × 40 seedów (100–139) = 320 biegów: wynik identyczny przed i po. Nie ma wywrotek, jest 14 ×
  F1 (maks. 1,35°) i 1 × 95,1 km/h na zjeździe 8 %. To jazda z górki ponad limiter, a nie F2.
- Wykresy (`tools/telemetry/plot.py`, obejrzane): `artifacts/physics-f2/png/before|after/` (kopia dowodów w głównym katalogu repo: logi Runnera przed/po, CSV repro, dotnet-test, pytest).

## F1 — rekomendacja (bez zmiany ogranicznika)
Wrażliwość na `yawStopFrequencyHz` (obecnie 3 Hz, WORKING_VALUE):

| f [Hz] | nadmiar repro F1 / grade8 / touch_wet | jackknife_retarder_noabs empty / laden40: nadmiar, max dv |
|---|---|---|
| 3 | 1,40 / 1,47 / 0,59° | 2,13° / 2,27°, dv 0,221 / 0,269 m/s |
| 4,5 | 0,90 / 0,66 / 0,38° | 1,35° / 1,59°, dv 0,309 / **0,402** m/s |
| 6 | 0,67 / 0,37 / 0,28° | 0,97° / 1,25°, dv 0,386 / **0,524** m/s |
| 10 | 0,39 / 0,18 / 0,16° | 0,53° / 0,87°, dv **0,550 / 0,802** m/s |

Sztywniejszy ogranicznik zmniejsza nadmiar, ale już od 4,5 Hz przebija limit szarpnięcia 0,35 m/s (dv). Na telefonie
byłoby to twarde stuknięcie przy złożeniu zestawu. **Rekomendacja:** zostawić 3 Hz i przyjąć niezmiennik
`articulation_limit_excess_deg ≤ 3,5°` (WORKING_VALUE) w scenariuszach fuzz. Uzasadnienie liczbowe:
- maks. 3,33° w polowaniu M34;
- 2,77° w polowaniu wywrotek po tej zmianie;
- 2,27° w jackknife;
- 1,47° w repro.

Pliki F1 w `scenarios_expected_fail/` zostają bez zmian, bo zdjęcie ich z listy należy do lidera. Uwaga: `jackknife_wet_curve_retarder_noabs`
osiąga 92,27°, a ma tylko dolny limit.

## Konsekwencje
- Runner lepiej odwzorowuje Unity po wywrotce: zestaw leży na boku zamiast spadać. Fuzz przestaje zgłaszać fałszywe
  przekroczenia prędkości.
- Kolidery są skopiowane z builderów graybox. Zmiana `TractorDimensions`/`TrailerDimensions` lub builderów wymaga
  aktualizacji `BodyGroundContact.TractorColliders/TrailerColliders` (Open 3).
- `Scenario.initial.dropHeight`, `overrides.bodyContact`, `RunOptions.DisableBodyContact/ExplicitGyroscopic` (przełączniki
  mutacyjne do testów) i nowe metryki: `free_flight_s`, `max_free_flight_energy_gain_j`, `max_free_flight_accel_error_ms2`,
  `max_body_penetration_m`, `min_com_height_m`, `body_contact_s`.

## Open
1. **Kerb 27 cm (lider/właściciel):** zderzak uderza w drogę, w runnerze dv 0,755 m/s, w Unity 0,968 m/s. Opcje:
   (a) przyjąć uderzenie i podnieść limity tego scenariusza do zmierzonych wartości Unity po feel teście;
   (b) sprawdzić wysokość zderzaka / FUP graybox (UN R93 dopuszcza ≤ 0,40 m, więc 0,35 m jest realne);
   (c) podatny kontakt „crush” zamiast sztywnego PhysX.
   Do tego czasu `bodyContact = false` w tym jednym scenariuszu.
2. **Samokolizja w Unity:** w tym samym evencie Frame ciągnika × Body naczepy (pierwszy kontakt, 639 N s). Siodło jest
   modelowane więzem, więc warto rozważyć `Physics.IgnoreCollision` między koliderami ciągnika i naczepy. To kod
   Unity-only, poza moją własnością.
3. Jedno źródło geometrii koliderów (dane zamiast kopii w builderze i runnerze).
4. **Lądowanie z dużej wysokości:** po zrzucie z 1 m zestaw odbija się prawie sprężyście, pierwszy apeks oddaje ~80 %
   energii spadku (0,3 m → ~60 %). E maleje, więc nie ma wstrzykiwania, ale tłumienie przy dobijaniu zawieszenia i opon
   wygląda na za małe. Do sprawdzenia osobno, poza zakresem F2.
5. **Siodło w koziołkowaniu:** bez koliderów i przy niejawnym żyroskopie miękki więz siodła wykonuje do ~0,7 kJ pracy na
   krok, czyli ~0,03 % KE na krok, przy |ω| ≈ 2 rad/s. Z koliderami w polowaniu: 0 J. Nie jest to przyczyna F2.
6. **Feel test na telefonie (właściciel):** wywrotka i kerb 27 cm z koliderami Unity. Zmiana dotyczy tylko runnera, więc
   na telefonie nic się nie zmienia, ale decyzja z Open 1 będzie się czuć.
