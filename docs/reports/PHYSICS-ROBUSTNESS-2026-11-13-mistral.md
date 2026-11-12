# PHYSICS-ROBUSTNESS-2026-11-13-mistral (M34) — odporność numeryczna, determinizm, soak, fuzz

Gałąź: `mistral/34-physics-robustness`. Cel: docs/04 §6 pkt 12 i 14 — udowodnić liczbami, że symulacja
(`tools/physics-runner` na .NET 8, ten sam kod co Unity) jest stabilna numerycznie i deterministyczna,
i wyłapać przypadki, w których nie jest. **Kodu fizyki w `game/Assets/**` nie ruszano** — znaleziska są
tylko raportowane z plikiem:linią podejrzanej przyczyny.

Środowisko: .NET 8 SDK 8.0.428 (doinstalowany w sandboxie), Debian 13, Release. Wszystkie liczby poniżej
pochodzą z uruchomień na tej gałęzi; komendy odtwarzalne — sekcja „Weryfikacja" na końcu.

## 0. Liczby przed / po (weryfikacja C)

| pakiet | przed (origin/main abe711ad) | po (ta gałąź, PRZED rebase) | po rebase na origin/main 16c6b421 (końcowe) |
|---|---|---|---|
| `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release` | 230 passed, 0 failed | 252 passed, 0 failed | **256 passed, 0 failed** |
| `dotnet run -c Release --project tools/physics-runner/Runner` | 115 scenariuszy, 607 checków, ALL PASSED (63 s) | 123 scenariusze, 675 checków, ALL PASSED, exit 0 | **127 scenariuszy, 707 checków, ALL PASSED, exit 0** |
| `pytest tests/physics` | 12 passed, 14 skipped | 12 passed, 14 skipped | 12 passed, 14 skipped |
| `python3 tests/physics/test_dims_sync.py` | ok | ok | ok |

(Różnica 252→256 testów i 123→127 scenariuszy po rebase to scenariusze/testy dołożone na main przez inne
zadania między abe711ad a 16c6b421 — nie moje; mój wkład to +22 testy i +8 scenariuszy fuzz +
4 expected_fail + rozszerzone soaki.)

Nowe: 8 scenariuszy fuzz w `tests/physics/scenarios/fuzz_*` (inwarianty), 4 pliki w
`tests/physics/scenarios_expected_fail/` (2 znaleziska fuzza + 2 pełne scenariusze fuzz, które złamały
inwariant), rozszerzone checki soak (przez generator `generate_stage2_scenarios.py`, żeby
`test_scenario_strictness.py` został zielony), 22 nowe testy xUnit w `Tests/RobustnessTests.cs`,
tryb runnera `--robustness`.

## 1. Determinizm (s6.12/s6.14)

Ten sam scenariusz 2× — każde pole każdego sampla porównane jako surowe bity IEEE-754
(`Suites.BitIdentical`, `tools/physics-runner/Sim/Suites.cs`):

| scenariusz | wynik |
|---|---|
| launch_0_80_flat ×2 | BIT-IDENTICAL |
| brake_80_0_dry_abs_comb@laden40 ×2 | BIT-IDENTICAL |
| lane_change_80@laden40 ×2 | BIT-IDENTICAL |
| circle_r25_20kmh ×2 | BIT-IDENTICAL |
| slalom_70_comb@laden40 ×2 | BIT-IDENTICAL |
| jackknife_wet_curve_abs_100@laden40 ×2 | BIT-IDENTICAL |
| fuzz_flat_wet_laden40 ×2 (w tym łańcuch dotyku) | BIT-IDENTICAL |

Dodatkowo dwa pełne przebiegi `--robustness` dały **identyczne tabele wszystkich metryk symulacyjnych**
(poza tabelą czasu CPU, która z natury jest wall-clock). Fuzz używa własnego xorshift64* PRNG
(`Sim/Drivers.cs`), więc seed jest odtwarzalny bit-w-bit między uruchomieniami i między runtime'ami
(świadomie nie `System.Random`). Wniosek: w runnerze .NET symulacja jest deterministyczna bit-w-bit;
między urządzeniami PhysX pozostaje „test z tolerancją" (docs/04 §1) — poza zakresem runnera.

## 2. fixedDeltaTime 1/50, 1/60, 1/100, 1/120 + substepy (s6.12) — tabela

Substepy skalowane do ~2,5 ms kroku wewnętrznego (`Suites.DtSweep`):

| scenariusz:metryka | 1/50 | 1/60 | 1/100 | 1/120 | max odch. wł. |
|---|---|---|---|---|---|
| launch_0_80_flat:time_to_kmh(80) | 13.6934 | 13.7249 | 13.6004 | 13.6375 | 0.47% |
| brake_80_0_dry:stop_distance_m | 34.574 | 34.668 | 34.689 | 34.785 | 0.31% |
| brake_80_0_dry_abs_comb@laden40:stop_distance_m | 40.569 | 40.735 | 40.797 | 40.834 | 0.41% |
| circle_r25_20kmh:lat_accel_ms2 | 1.2187 | 1.2186 | 1.2183 | 1.2182 | 0.02% |
| lane_change_80@laden40:max_articulation_deg | 0.8277 | 0.8289 | 0.8313 | 0.8319 | 0.27% |
| launch_flat_comb@laden40:time_to_kmh(60) | 28.372 | 28.261 | 28.020 | 28.139 | 0.63% |

Substepy przy stałym dt = 1/100 (`Suites.SubstepSweep`):

| scenariusz:metryka | 1 | 2 | 4 | 8 | max odch. wł. |
|---|---|---|---|---|---|
| brake_80_0_dry:stop_distance_m | 35.446 | 34.675 | 34.689 | 34.665 | 1.65% |
| brake_80_0_dry_abs_comb@laden40:stop_distance_m | 42.289 | 40.914 | 40.797 | 40.886 | 2.59% |
| lane_change_80@laden40:max_articulation_deg | 0.8313 | 0.8313 | 0.8313 | 0.8313 | <0.001% |

Wniosek: wszystkie metryki w tolerancji 5% (WORKING_VALUE, jak w istniejącym `DtVariation_IsConsistent`);
maks. rozrzut 2,6% (substepy przy hamowaniu 40 t). Brak jakościowych różnic między 1/50 a 1/120.

## 3. Soak 30 min (s6.14) — metryki i progi (WORKING_VALUE z rachunkiem)

`soak_30min_cycle@laden40` (20 cykli: rozpędzenie do 80, podwójna zmiana pasa, hamowanie, postój):

| metryka | zmierzone | próg |
|---|---|---|
| nan_detected | 0 | = 0 |
| max_dv_step_ms | 0.187 | ≤ 0.35 (ten sam limit co scenariusze krawężników) |
| max_pos_jump_m | 0.0037 | ≤ 0.01 = 0.5·a·SampleDt² = 0.5·8·0.05² (resztka równomiernie hamującego ciała przy sampleEvery=5; teleport byłby o rzędy większy) |
| max_fifth_wheel_error_mm | 0.018 | ≤ 5 (jak dotąd) |
| articulation_limit_excess_deg | 0 | = 0 (yawLimitDeg=90, `tractor_4x2_generic.vehicle.json:305`) |
| max_tire_friction_ratio | 0.903 | ≤ 1.001 (model combined-slip ogranicza z konstrukcji; margines 0.001 na zaokrąglenia) |
| min_air_all_bar | 8.03 | ≥ 0 |
| energy_drift_j w oknach postoju (6 cykli + ostatni) | 0.34–1.33 J | ≤ 5 J = 6.9e-6 energii 727 kJ (parked baseline) |
| widmo prędkości kątowej kabiny (pitch, ostatnie 60 s) | pik 1.17 Hz, amplituda 0.147 deg/s | amplituda ≤ 1 deg/s |
| widmo (roll) | 0.17 Hz, 0.095 deg/s | raportowane |
| max_cab_pitch_rate_dps / roll | 8.05 / 0.98 | raportowane (przejściowe, przy zmianie pasa) |

`soak_30min_parked@laden40` (30 min postoju, hamulec postojowy):

| metryka | zmierzone | próg |
|---|---|---|
| drift_m [5..1800 s] | 0.0004 | ≤ 0.005 (istniejący check) |
| energy_drift_j [5..1800 s] | 0.57 J (7.8e-7 z 727 kJ) | ≤ 5 J |
| max_speed_after_ms [5..end] | 3.1e-5 | ≤ 0.001 (istniejący) |
| max_pos_jump_m | 2.1e-5 | ≤ 1e-3 |
| max_fifth_wheel_error_mm | 1.1e-6 | ≤ 5 |
| max_dv_step_ms | 0.0013 | ≤ 0.35 |
| max_tire_friction_ratio | 0.0084 | ≤ 1.001 |
| articulation_limit_excess_deg | 0 | = 0 |
| min_air_all_bar | 8.36 | ≥ 0 |
| widmo pitch kabiny (ostatnie 60 s) | amplituda 3.7e-14 deg/s (brak oscylacji) | ≤ 0.01 deg/s |

Wniosek soak: **stabilność potwierdzona liczbami** — brak NaN, dryf energii na postoju < 8e-7 względny,
brak dryfu pozycji (0.4 mm / 30 min), błąd więzu siodła ≤ 0.02 mm, widmo kabiny bez oscylacji.

## 4. Fuzz (property-based, seedowane) — niezmienniki i wyniki

Nowy driver `fuzz` (`Sim/Drivers.cs`): co przedział [holdMinS, holdMaxS] losowy zestaw wejść
(steer, gaz/hamulec, selector D/N/R, retarder, hamulec postojowy, ręczne biegi); opcja `touchChain`
przepuszcza kierownicę przez prawdziwy łańcuch gry (TouchSteeringWheel → SteeringColumn). PRNG xorshift64*,
seed w JSON. Niezmienniki jako checki scenariuszy `fuzz_*`: brak NaN, brak teleportacji
(`max_pos_jump_m` = |Δx_com − v·dt|), siły opon ≤ μ·Fz (`max_tire_friction_ratio` ≤ 1.001),
kąt przegubu w ograniczniku (`articulation_limit_excess_deg` = 0), brak ujemnego ciśnienia
(`min_air_all_bar` ≥ 0), `max_dv_step_ms` ≤ 0.35, błąd siodła ≤ 5 mm.

W `tests/physics/scenarios/` zostało 8 zielonych scenariuszy fuzz (dry/wet/concrete/gravel/mud ×
flat/±8% × solo/empty/cargo24/laden40, 2 z łańcuchem dotyku, 1 z krawężnikiem 8 cm; 60 s każdy).
Polowanie: 40 dodatkowych seedów (100–139) × nawierzchnie × nachylenia × masy × wysokości krawężników.

**Wynik polowania: 16/40 seedów złamało inwarianty — wszystkie przez DWA zjawiska (patrz §5):**
brak NaN, brak teleportacji (max 4.1e-14 m), friction ratio ≤ 1.0 we wszystkich 40, brak ujemnego
ciśnienia, błąd siodła ≤ 5 mm we wszystkich.

## 5. Znaleziska (NIE poprawiane — decyduje lider/właściciel)

### F1 — przegub wychodzi poza ogranicznik 90° (articulation_limit_excess_deg > 0)
- Skala: do **3.33°** ponad ogranicznik (hunt), 1.42–2.23° w zminimalizowanym repro.
- Zminimalizowany repro: `tests/physics/scenarios_expected_fail/fuzz_shrink_articulation_stop_fulllock.json`
  — pełny skręt przy 15 km/h na mokrym, pusta naczepa, 12 s → 91.42° (nadmiar 1.42°).
- Pełne fuzz-y łamiące inwariant: `fuzz_grade8_dry_laden40` (1.47°), `fuzz_touch_wet_empty` (0.59°)
  — też w `scenarios_expected_fail/`. Istniejący `jackknife_wet_curve_noabs@laden40` też osiąga 92.14°
  (jego check ma tylko dolny limit, więc został zielony).
- Podejrzana przyczyna: miękki jednostronny ogranicznik sprężyna-tłumik penetruje proporcjonalnie do
  prędkości zbliżania — `game/Assets/_Project/Vehicle/Physics/Components/FifthWheel.cs:223`
  (wywołanie `Limit(...)` dla yaw) i `FifthWheel.cs:280-290` (`err = c - limit`, brak twardego clampa).

### F2 — runaway prędkości podczas wywrotki (energia wstrzykiwana numerycznie)
- Fuzz seed 105 (i 10 innych z 40): przy stałym gazie 0.378 + pełny skręt od 30 km/h zestaw przewraca się
  (t≈4 s, roll −78°, **wszystkie 10 kół w powietrzu**) i dalej przyspiesza z silnikiem na jałowym
  (rpm 600, bieg 1): 1088 km/h w 60 s. Zminimalizowany repro:
  `tests/physics/scenarios_expected_fail/fuzz_shrink_speed_runaway_fulllock.json` — gaz 0.378 + steer −1
  od 30 km/h, cargo24, suche, 30 s → **275.4 km/h** (limit 90 + 0.5), `max_dv_step_ms` 0.678, przegub 92.23°.
- Podejrzana przyczyna: więz siodła wykonuje pracę, gdy oba ciała koziołkują bez kontaktu kół —
  człon bias w `lam = Kinv * (-(cdot + bias + P*gammaP))`,
  `game/Assets/_Project/Vehicle/Physics/Components/FifthWheel.cs:214-216`; oraz te same miękkie ograniczniki
  jak w F1 (`FifthWheel.cs:223, 280-290`). Hipoteza alternatywna do sprawdzenia przez lidera: samo wywracanie
  się przy 30 km/h i pełnym skręcie też wygląda na zbyt agresywne (roll −78° w 0.5 s).

## 6. Rozszerzenia

### (a) Profil CPU kroku fizyki (dt = 10 ms, pełny zestaw 40 t, desktop Release)

| substepy | mean µs | p50 | p99 | max |
|---|---|---|---|---|
| 1 | 6.15 | 5.84 | 13.4 | 58.7 |
| 2 | 7.39 | 7.08 | 17.4 | 86.8 |
| 4 | 9.63 | 9.40 | 22.8 | 40.7 |
| 8 | 14.32 | 14.0 | 28.0 | 60.8 |

Koszt rośnie ~liniowo z liczbą substepów; 4 substepy ≈ 10 µs/krok na desktopie (Samsung A będzie wolniejszy —
benchmark na telefonie poza zakresem runnera, docs/04 §6 pkt 12 „obciążenie CPU” częściowo poza runnerem).

### (b) Wrażliwość na środek masy ładunku — siatka 5×5 (s6.7)

Łuk R50 @ 35 km/h, laden40, cogHeight 1.9 m; pełna tabela w `robustness.md`. Wynik: środek (|cogX| ≤ 0.5,
dowolne cogZ): max roll 1.6–10.3°, przegub 8.5–10.2°, brak wheel-lift oprócz kilku przypadków.
**Narożniki ładunku (cogX = ±1.0 m): wywrotka** — roll 79–89°, wheel_lift = 1, przegub do 94.2°,
`lat_accel` do 464 m/s² (objaw niestabilności z F2 podczas koziołkowania, nie fizyczne 0.19 g łuku).
Wniosek: fizyka jest wrażliwa na CoG ładunku (zgodnie z §6 pkt 7), ale skrajne położenia uruchamiają F2.

### (c) Skrajne masy × nawierzchnie (80–0 km/h, ABS) — droga hamowania [m]

| masa całk. | dry | wet | concrete | cobblestone | gravel |
|---|---|---|---|---|---|
| 15 t | 38.7 | 54.6 | 38.6 | 41.2 | 46.8 |
| 20 t | 38.3 | 54.5 | 38.2 | 41.5 | 46.9 |
| 30 t | 39.5 | 55.7 | 39.5 | 42.1 | 47.6 |
| 40 t | 40.8 | 56.8 | 40.8 | 42.9 | 48.7 |
| 44 t | 41.4 | 57.2 | 41.5 | 43.7 | 49.3 |

Monotonicznie rośnie z masą i maleje z μ nawierzchni — spójne fizycznie (μ: dry 1.0, wet 0.625 —
WORKING_VALUE z `docs/VEHICLE_REFERENCE_DATA.md`; cobblestone/gravel/grass/mud dodane w runnerze jako
WORKING_VALUE 0.9/0.75/0.6/0.4, `Sim/AnalyticGround.cs`).

### (d) Fuzz krawężników/progów (s6.11) — 40 seedowanych uderzeń

Wysokość 2–30 cm × prędkość 10–90 km/h × dry/wet × empty/laden40 (seed 20261113, `Robustness.KerbFuzz`):
**0 NaN, 0 teleportacji (max pos_jump 4.1e-14 m), friction ratio ≤ 1.0, max dv_step 0.274 m/s
(< 0.35), przegub ≤ 9.4°, błąd siodła ≤ 0.71 mm**; pik Fz do 11.4× przy 29.6 cm (twardy impakt, bez wybuchu).

## 7. Weryfikacja A–E (dowody)

- **A. Niezależny przegląd** (bez subagentów — 3 osobne przebiegi od zera):
  1. *liczby i źródła*: dwukrotne pełne `--robustness` — wszystkie tabele metryk identyczne bit-w-bit
     (diff pusty poza tabelą CPU); rachunki progów WORKING_VALUE sprawdzone ręcznie (0.5·8·0.05²=0.01;
     5/727067=6.9e-6; 0.57/727067=7.8e-7); yawLimitDeg=90 z `tractor_4x2_generic.vehicle.json:305`;
     limit 90 km/h + 0.5 jak w `top_speed_flat_comb`.
  2. *czy każdy check coś sprawdza*: każdy nowy check ma twardy próg i został poddany mutacji (tabela B) —
     wszystkie padają; metryki mają testy jednostkowe z syntetycznymi samplami (energia, widmo 2 Hz = pik
     2 Hz, friction, air, NaN, przegub).
  3. *próba złamania*: polowanie 40 seedów fuzz (znalazło F1+F2), 10 mutacji kodu (wszystkie wykryte),
     mutacja seeda z zegara → test determinizmu pada.
- **B. Testy mutacyjne** (mutacja lokalna, niecommitowana, po każdej `git checkout`): M1 friction×2 →
  1.805 FAIL; M2 NaN wymuszony → FAIL; M3 limit przegubu=0 → 2.24° FAIL; M4 AirPark=−1 → FAIL;
  M5 PE rosnąca w czasie → energy_drift 1.795e6 J FAIL; M6 amplituda widma ×10 → 1.47 FAIL;
  M7 pos_jump+1 m → FAIL; M8 dv_step+1 → 1.0004 FAIL; M9 seed z `Environment.TickCount` →
  `SameScenario_Twice_IsBitIdentical` Failed (DIFFERS, 6000 sampli); M10 substepy wymuszone=1 w DtSweep →
  max dev 17.6% > 5%, Failed. **10/10 mutacji → FAIL.** Drzewo po mutacjach czyste (`git status` pusty).
- **C. Pełne uruchomienie**: tabela w §0 (przed/po; końcowe liczby po rebase na origin/main 16c6b421):
  dotnet test 256/0, runner 127 scenariuszy / 707 checków ALL PASSED exit 0, pytest 12/14, dims ok.
- **D. Przed PR**: `git fetch && git rebase origin/main` (fast-forward, bez konfliktów), ponowione C,
  `git diff --name-only origin/main` — wyłącznie `tools/physics-runner/**`, `tests/physics/**`,
  `docs/reports/**`; `game/Assets/**`, `Data/**`, `*.glb`, `*_meta.json`, `ProjectSettings`, `Packages`,
  `.gitattributes`, LFS, `.asmdef` nietknięte.
- **E.** ta lista.

## 8. Co jest poza runnerem (jak w M33)

- s6.12 „obciążenie CPU na Samsungu A”: runner mierzy desktop (tabela §6a); pomiar na telefonie przez
  `scripts/device-metrics.ps1` — poza sandbox.
- s6.13 floating origin: wymaga świata Unity; propozycja testu PlayMode bez zmian w kodzie.
- Determinizm między urządzeniami (PhysX): poza runnerem, nadal „test z tolerancją” (docs/04 §1).

## 9. Pliki zmienione

- `tools/physics-runner/Sim/`: `Metrics.cs` (nowe metryki: nan_detected, energy_drift_j, max_energy_j,
  max_tire_friction_ratio, min_air_all_bar, articulation_limit_excess_deg, max_cab_*_rate_dps,
  cab_spectrum_peak_hz/amp_dps), `Telemetry.cs` (Sample: PotentialEnergy, MaxFrictionRatio),
  `ScenarioRunner.cs` (MakeSample, NaN jako metryka zamiast wyjątku, ArticulationLimitDeg),
  `Drivers.cs` (XorShift, FuzzDriver), `Scenario.cs` (pola fuzz), `Suites.cs` (BitIdentical),
  `AnalyticGround.cs` (nawierzchnie kostka/żwir/trawa/błoto, WORKING_VALUE), `Robustness.cs` (nowy —
  wszystkie tabele), `Runner/Program.cs` (`--robustness`, sweep 1/60).
- `tools/physics-runner/Tests/RobustnessTests.cs` (nowy, 22 testy).
- `tests/physics/scenarios/fuzz_*.json` (8), `tests/physics/scenarios_expected_fail/` (+4),
  `tests/physics/generate_stage2_scenarios.py` (rozszerzone soaki), `soak_30min_*.json` (zregenerowane).
