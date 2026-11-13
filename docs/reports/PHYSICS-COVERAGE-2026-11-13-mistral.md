# Pokrycie pakietu walidacyjnego fizyki (docs/04 §6) — 2026-11-13 (mistral, M33)

Gałąź: `mistral/33-physics-validation-coverage` od `origin/main` eb827b71. Zakres zmian: tylko
`tests/physics/**` (2 nowe scenariusze + generator + 2 checki z podniesionym statusem źródła) i ten raport.
**Żaden plik w `game/Assets/**` nie został zmieniony** (weryfikacja: `git diff --stat origin/main` w PR).

## 0. Baseline i wynik końcowy (uruchomione, .NET 8 SDK 8.0.428)

| Komenda | Przed (main eb827b71) | Po zmianach |
|---|---|---|
| `dotnet test tools/physics-runner/PhysicsRunner.sln -c Release` | 230/230 passed | **234/234 passed** (+4 = nowe scenariusze × warianty, auto-odkrywane przez ScenarioTests) |
| `dotnet run -c Release --project tools/physics-runner/Runner` | **115 scenariuszy, 607 checków, 0 porażek** | **119 scenariuszy, 639 checków, 0 porażek** |
| `uv run --with pytest --with numpy --with scipy pytest tests/physics/test_scenario_strictness.py tests/physics/test_dims_sync.py -q` | 12 passed | **12 passed** (generator nadal reprodukuje committowane JSON-y; nowe pliki są w generatorze) |
| `tests/physics/test_swept_path_gate3.py` | wymaga zbudowanego świata + ~2–4 min; nie w CI (ci.yml uruchamia tylko `test_dims_sync.py`) — **nie uruchomiony**, poza zakresem |

## 1. Macierz pokrycia — 15 punktów docs/04 §6

Statusy źródeł: **S** = SOURCED (źródło pierwotne zacytowane), **D** = DERIVED (rachunek z S/WORKING), **W** = WORKING_VALUE (uzasadnienie fizyczne w polu `source` JSON-a).

| # | Punkt §6 | Scenariusze (`tests/physics/scenarios/`) | Kluczowe checki (metryka [min,max]) | Źródło progów |
|---|---|---|---|---|
| 1 | Postój płasko/12%, 5 min, bez dryfu i oscylacji | `park_flat_5min_comb`, `park_12pct_up_comb`, `park_12pct_down_comb` (empty, laden40), `standstill_{flat,12pct_uphill,12pct_downhill}_parking` (solo) | `creep_m` ≤ 0.005 m (S: R13 Annex 4 §2.3.2 — 12%), `drift_m` ≤ 0.012, `max_speed_after_ms` ≤ 0.001 (od t=5 s), `max_dv_step_ms` ≤ 0.35, `max_fifth_wheel_error_mm` ≤ 5 | 12% = S (R13), reszta W |
| 2 | Ruszanie pusty/40 t, płasko/6% (12%), bez cofania, realne obroty/sprzęgło | `launch_flat_comb`, `launch_0_80_flat`, `launch_6pct_uphill_comb` (empty, laden40), `launch_6pct_uphill_cargo24_comb`, `launch_6pct_uphill_light_comb`, `launch_6pct_uphill_light_throttle`, `launch_12pct_uphill_comb` | `rollback_m` ≤ 0.02–0.05 m, `stalled` = 0, `min_rpm` ≥ 550, `max_clutch_temp_c` ≤ 250 °C, `time_to_kmh(15)` pasma, `max_dv_step_ms` ≤ 0.35 | W (rachunek sił na wzniesieniu w source) |
| 3 | 0–60 / 0–80 km/h, pusty i 40 t vs dane referencyjne | `launch_flat_comb` (empty/laden40: t60 12–35 / 25–60 s, t80 20–55 / 40–95 s), `launch_0_80_flat` (solo), `launch_flat_comb_part60`; powtarzalność 3× inne headings w Runnerze (`Suites.Repeatability`, max dev 0.00 %) | `time_to_kmh(60/80)` pasma D, `rollback_m`, `stalled` | D: rachunek z mocy/masy (ITE ~176 lb/hp → ~0,5 m/s²; pasma jak w AUDIT §8, 40–95 s @40 t) |
| 4 | Vmax na płaskim (ogranicznik) i ustalona na 5% z 40 t | `top_speed_flat`, `top_speed_flat_comb` (empty, laden40), `grade_5pct_steady`, `grade_6pct_steady_comb` | `max_speed_kmh` ≤ 90.5 (S: 90 km/h + tolerancja), `mean_speed_kmh` ∈ [88, 90], `final_gear` = 12; 5%: `mean_speed_kmh` ∈ [44, 60] (D: 50,2 km/h zmierzone vs ~54 teoria) | 90 km/h = S (S3), reszta D/W |
| 5 | Droga hamowania 80→0: sucho/mokre × pusty/40 t × ABS on/off + czas reakcji | `brake_80_0_dry_abs_comb`, `brake_80_0_dry_noabs_comb`, `brake_80_0_wet_abs_comb`, `brake_80_0_wet_noabs_comb`, `brake_80_0_dry`, `brake_80_0_wet`, `brake_response_static` | `stop_distance_m`: dry ABS ≤ 61.2 m (S: R13 Annex 4 type-0 N3 0,15v+v²/130 przy 80 km/h — status podniesiony z W na S w tym PR, tabela potwierdzona przez GRRF-56-3), wet ≤ 95 m; `mfdd_ms2` ≥ 5.0 (S, R13) / ≤ μg; `brake_response_s` ≤ 0.6 s (S: R13 §4.1.1); `rear_lock_time_s`, `trailer_lock_time_s`, `max_articulation_deg` ≤ 2° | S (R13) + W dla mokrego μ |
| 6 | Zjazd 6–8% retarder/hamulec silnikowy; długie hamowanie roboczym → spadek ciśnienia | `downhill_7pct_typeIIA` (S: R13 Annex 4 §1.8.2 — 7%, 6 km, energia 30 km/h, tylko hamulce ciągłe ±5 km/h), `downhill_7pct_brake_cruise_60`, `downhill_7pct_full_lever`, `downhill_7pct_service_pumping`, `downhill_8pct_retarder_comb`, `limiter_downhill_{2,5}pct_comb`, `air_leak_rear_circuit` (S: hamulec pomocniczy 0,15v+2v²/130 → 64,4 m przy 60 km/h, R13 §2.2) | `mean_speed_kmh` ∈ [25,35] (type-IIA 30 km/h), `max_retarder_torque_nm` ≤ 4000 (S: ZF 4000 Nm/600 kW), `max_service_demand` = 0 (tylko ciągłe), `min_air_service_bar` ≥ 3 + `low_air_warning` = 1 (pumping), `max_engine_brake_torque_nm` ≥ 500 | S (R13, S1/S2) + W |
| 7 | Łuk stałego promienia przy kilku prędkościach; przechył, granica przyczepności, wrażliwość na CoG ładunku | `circle_r25_{10,20}kmh`, `circle_r50_{20,35}kmh`, `circle_r50_{10kmh,35kmh}_comb`, `rollover_r50_cog_{low,high}` (CoG 1,9 vs 2,6 m), `circle_r50_50kmh_comb` → **expected_fail** (`radius_error_m` 1,04/0,83 m vs 0,6 m — przyczyna: regulator śledzenia toru przy 0,39 g, opis w pliku) | `lat_accel_ms2` = v²/R ±10 % (D), `radius_error_m` ≤ 0.5–0.6, `trailer_offtracking_m`, `max_abs_roll_deg`/`max_trailer_roll_deg`, `lat_accel_at_first_lift` ∈ [0,25; 0,55] g (W; pasmo literaturowe 0,3–0,45 g UMTRI/Winkler, UNVERIFIED w repo) | D + W |
| 8 | Zmiana pasa / ISO-like 60–80 km/h — stabilność naczepy | `lane_change_60`, `lane_change_80` (solo/empty/laden40), `slalom_70_comb` | `max_articulation_deg` ≤ 6°, `rearward_amplification` ∈ [0,8; 1,6] (W; FHWA WUS rozdz. VII rys. VII-4: typowo 1,24, ≤ 2,0 akceptowalne), `articulation_settle_deg` ≤ 0,5°, `wheel_lift` = 0, `max_lat_accel_ms2` ≤ 2,5/3,5 | W (FHWA 1,24 jako odniesienie) |
| 9 | Jackknife: gwałtowne hamowanie w łuku na mokrym | `jackknife_wet_curve_noabs`, `jackknife_wet_curve_retarder_noabs` (empty: `max_articulation_deg` ≥ 30° — jackknife musi być możliwy), `jackknife_wet_curve_abs_{50,100}` (≤ 10°) | `max_articulation_deg`, `rear_lock_time_s` (≥ 0,5 s bez ABS / ≤ 0,1 z ABS), `max_dv_step_ms` ≤ 0,35 | W (jakościowo zgodne z FHWA: lock osi napędowej → jackknife) |
| 10 | **Cofanie z naczepą pod rampę, ciasne manewry** — **LUKA ZAŁATANA W TYM PR** | NOWE: `reverse_dock_s_maneuver_comb` (płasko, S-skręt przy ~9 km/h, empty + laden40), `reverse_grade6pct_comb` (wstecz pod 6% rampę z 4 km/h, empty + laden40) | dock: `max_articulation_deg` ∈ [20; 95]° (odboj ±90° miękki), `wheel_lift` = 0, `stalled` = 0, `min_speed_kmh` ≥ −15 (wstecz: SpeedFwd < 0), `final_z_m` ≤ −3; rampa: `drift_m` ≥ 8 m, `final_z_m` ≤ −5, `max_articulation_deg` ≤ 20°, `min_rpm` ≥ 550, `min_speed_kmh` ≥ −12, + stabilność (`max_dv_step_ms` ≤ 0,35, `max_fifth_wheel_error_mm` ≤ 5) | W (rachunek: 4 km/h × 40 s = 44 m teoretyczne; limit prędkości wstecznej = R1 × regulator 2100 rpm ≈ 9,9 km/h) |
| 11 | Krawężnik 8/15 cm, koleiny, próg zwalniający — ciągłość kontaktu | `curb_8cm_both`, `curb_15cm_{both,left,left_comb}`, `curb_strike_{5,14}cm_50kmh_comb`, `kerb_step_27cm_42kmh_comb`, `speed_bump_comb` | `max_pos_jump_m` ≤ 1e-6, `max_dv_step_ms` ≤ 0,35, `max_fz_ratio`, `wheel_off_ground_time_s`, `max_wheel_airtime_s`, `max_cab_heave_mm` ≤ 50 (próg) — **ścianki bezpieczeństwa dodatkowo przypięte w `test_scenario_strictness.py`** | W |
| 12 | Różne fixedDeltaTime, FPS 30/60, obciążenie CPU | **Częściowo runnerem**: Runner wykonuje `Suites.DtSweep` (50/100/120 Hz) i `SubstepSweep` (2/4/8) na 6 scenariuszach + bench kosztu kroku (mean 9,9 µs/krok, p99 23,4 µs, 40 t). **FPS 30/60 i obciążenie CPU telefonu: POZA RUNNEREM** (patrz §3) | max dev przy dt 50–120 Hz ≤ 0,69 % (zmierzone) | W |
| 13 | Floating origin i streaming w jazzie | **POZA RUNNEREM** (runner ma płaską analityczną ziemię i krótkie trasy; floating origin to warstwa Unity) — propozycja PlayMode w §3 | — | — |
| 14 | Soak 30 min — brak dryfu energii/drgań/błędu | `soak_30min_cycle` (20 cykli jazdy), `soak_30min_parked` | `max_kinetic_energy_j` ≤ 0,001 (parkowany), `max_speed_after_ms` ≤ 0,002 (pierwszy vs ostatni cykl), `min_air_service_bar` ≥ 8/10,5, `max_roll_rate_proxy_deg`, `max_dv_step_ms` ≤ 0,35 | W |
| 15 | Spójność kierunku sterowania we wszystkich trybach wejścia | `steer_sign_{forward_left, forward_right, right_comb, reverse_right, reverse_right_comb}` (D: znak yaw = znak skrętu × kierunek jazdy); łańcuch dotyku (TouchSteeringWheel → SteeringColumn) przez `TouchDriver`/`TouchEvidence` (ADR 0149, `--touch-evidence`). **Gyro i haptyka: POZA RUNNEREM** (§3) | `yaw_rate_mean_dps` znak, `lateral_displacement_m` znak, `stalled` = 0 | D |

## 2. Luki znalezione i co z nimi zrobiono

1. **Punkt 10 (cofanie z naczepą) nie miał żadnego scenariusza** → dodano `reverse_dock_s_maneuver_comb` i `reverse_grade6pct_comb` (oba w generatorze `generate_stage2_scenarios.py`, więc `test_scenario_strictness.py` przechodzi). Nie dodano nowej metryki — istniejące wystarczyły. Pułapka, którą trzeba było ominąć: `max_speed_kmh` przy cofaniu mierzy **max ze znakowanej** prędkości (zawsze ~0), więc check prędkości wstecznej musi iść przez `min_speed_kmh`.
2. **Punkt 5: górny limit drogi hamowania 61,2 m i MFDD ≥ 5,0 m/s² były oznaczone WORKING_VALUE/UNVERIFIED**, choć audyt (AUDIT-PHYSICS-SOURCES §7, źródło A3 = GRRF-56-3 odtwarzający tabelę Annex 4) potwierdził formułę N3 type-0 → status podniesiony na **SOURCED** z pełnym cytatem źródła w `brake_80_0_dry_abs_comb.json`.
3. **Punkt 12**: część „różne fixedDeltaTime / substepy” jest pokryta przez multi-run Runnera (DtSweep/SubstepSweep); FPS i CPU na telefonie — poza runnerem (§3). Nie dodawano sztucznych scenariuszy.
4. **Punkt 13**: poza runnerem (§3).
5. Słabe checki w istniejących scenariuszach: audyt przebiegu (A-b) nie znalazł checków, które przechodzą każdą wartość — najszersze pasma (`rearward_amplification` [0,8; 1,6], `time_to_kmh(80)` @40 t [40, 95] s, `stop_distance_m` no-ABS [30, 150] m) mają uzasadnienie w `source` (FHWA 1,24/≤2,0; ITE ~45 s; fizyka ślizgu blokady) i **łapią mutacje** (por. test mutacyjny dla nowych checków; dla starych — kompaktowe pasma D jak `lat_accel_ms2` = v²/R ±10 % łapią każdą zmianę fizyki łuku).

## 3. Poza runnerem (wymagają Unity/telefonu) — propozycje testów PlayMode (tylko opis)

- **§6.12 (FPS 30/60, obciążenie CPU)**: PlayMode na Samsungu A: `Time.captureFramerate` przy `fixedDeltaTime` 1/100 i renderingu 30/60 FPS przez 90 s jazdy ze scenariuszem `soak_30min_cycle`; asercja: p50 FPS ≥ zadane, brak jakościowych różnic w `stop_distance_m`/`time_to_kmh` między profilami (porównanie z CSV runnera z tolerancją jak w DtSweep).
- **§6.13 (floating origin)**: PlayMode: przejazd trasy > 100 km (lub teleport rzędu 1e5 m co 10 km) z aktywnym streamingiem; asercja: brak skoku sił/prędkości (`max_dv_step_ms`- odpowiednik z telemetrii Unity), brak NaN, fifth-wheel error < 5 mm.
- **§6.15 (gyro, haptyka)**: PlayMode z mockiem `Input.gyro`: ten sam gest skrętu gyro i dotykowy muszą dać ten sam znak `yaw_rate` (jak `steer_sign_*`); haptyka przez abstrakcję platformową — asercja wywołania na krawężniku/ABS (mock rejestrujący wywołania).

## 4. Źródła pierwotne wartości oczekiwanych (cytaty ≤ 25 słów + link; weryfikacja w §5)

| Wartość | Źródło | Cytat | Status weryfikacji |
|---|---|---|---|
| Ogranicznik 90 km/h (N3) | Dyrektywa 92/6/EWG zm. 2002/85/WE, EUR-Lex CELEX 01992L0006-20021204 — <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX%3A01992L0006-20021204> | „categories N2 and N3 … cannot exceed 90 kilometres per hour” | zweryfikowane w audicie (A2) |
| Hamowanie type-0 N3: s ≤ 0,15v + v²/130, dm ≥ 5,0 m/s² | UN R13 Annex 4, tabela via GRRF-56-3 — <https://unece.org/DAM/trans/doc/2004/wp29grrf/TRANS-WP29-GRRF-56-inf03e.pdf> (MLIT UN_R013_02.pdf, S5: komórki tabeli się nie wyekstrahowały) | „0.15v + (v²/130)”, „dm 5.0 m/s²” (N3, 60 km/h, silnik odłączony) | potwierdzone w AUDIT §7 (A3) — status S podniesiony w tym PR |
| Hamulec postojowy zestawu: 12 % | UN R13 (MLIT, S5) §2.3.2 — <https://www.mlit.go.jp/jidosha/un/UN_R013_02.pdf> | „the towing vehicle's parking brake holds the combination on 12 %” | odczytane (S5) |
| Czas reakcji hamowania ≤ 0,6 s | UN R13 (S5) §4.1.1 | „braking force on the least favourably placed axle within 0.6 s” | odczytane (S5) |
| Hamulec pomocniczy N: s ≤ 0,15v + 2v²/130, dm 2,2 m/s² | UN R13 (S5) §2.2 | „s ≤ 0.15 v + 2 v²/130” (N, 60 km/h → 64,4 m) | odczytane (S5) |
| Type-IIA: 7 % zjazd, 6 km, energia = 30 km/h, tylko ciągłe ±5 km/h | UN R13 (S5) Annex 4 §1.8.2 | „energy equivalent to 30 km/h on a 7 % down-gradient over 6 km” | odczytane (S5) |
| RA typowo 1,24, ≤ 2,0 akceptowalne | FHWA Western Uniformity Scenario Analysis, rozdz. VII rys. VII-4 — <https://www.fhwa.dot.gov/policy/otps/truck/wusr/chap07.cfm> | „Figure VII-4 shows that typical tractor-semitrailer combinations have a rearward amplification of 1.24.” | zweryfikowane w PHYSICS-SOURCES-2 (P2) |
| Próg przewrócenia zestawu 0,3–0,45 g | Winkler/UMTRI — <https://deepblue.lib.umich.edu/handle/2027.42/49> | pasmo z pracy (tabela pojazdów) | UNVERIFIED w repo (pasmo, nie pojedyncza liczba) |
| Silnik: 2500 Nm @ 980–1270, 368 kW, 2100 rpm, VEB+ 375 kW @ 2300 | Volvo D13K500 fact sheet (S1) — <https://stpi.it.volvo.com/STPIFiles/Volvo/FactSheet/D13K500_Eng_010_338550297.pdf> | „Max torque at 980–1270 rpm … 2500 Nm”; „Engine braking effect (VEB+) at 2300 rpm … 375 kW” | PDF otwarty 2026-11-09 (S1) |
| Skrzynia: przełożenia 12.92…0.77, R1 12,03; Intarder 4000 Nm/600 kW | ZF TraXon data sheet (S2) — <https://www.zf.com/public/org/Product-data-sheet_TraXon-Torque_71520.pdf> | „ZF-Intarder with up to 4,000 Nm/600 kW braking torque/power” | PDF otwarty 2026-11-09 (S2) |
| DMC 40 t, dł. 16,50 m, szer. 2,55 m, naczepa kingpin–tył 12,00 m, naciski osi 11,5/24/10 t | Dyrektywa 96/53/WE Annex I, EUR-Lex CELEX 31996L0053 — <https://eur-lex.europa.eu/legal-content/en/ALL/?uri=CELEX%3A31996L0053> | „40 tonnes” (2.2.2a); „16,50 m” (1.1); „2,55 m” (1.2a) | zweryfikowane w audicie (A1) |
| Limity PL > 3,5 t: 80/70/50 km/h | Prawo o ruchu drogowym art. 20 — <https://isap.sejm.gov.pl/> (materiały Policji: slupca.policja.gov.pl PDF, A12) | „80 km/h” autostrada, „70 km/h” poza zabudowanym, „50 km/h” zabudowany | zweryfikowane w audicie (A12) |

**WORKING_VALUE z uzasadnieniem fizycznym (rachunek)**: μ suche 0,80 / mokre 0,50 (klasa opon C3, etykieta UE 2020/740 nierozstrzygnięta); prędkość wsteczna max ≈ 9,9 km/h = 2100 rpm × 2π/60 × 0,51 m / (12,03 × 3,40); rampa 6 % przy 40 t wymaga siły m·g·sin6 % ≈ 23,5 kN < dostępne ~90 kN w R1 (dlatego scenariusz rampy przechodzi i łapie mutację „hamulec postojowy”); pasma czasów 0–60/0–80 = rachunek mocy/masy z pasmem ITE.

## 5. Weryfikacja (A–D)

- **A. Niezależny przegląd** — trzy osobne przebiegi od zera (bez moich wniosków): (a) każdy cytat i liczba z §4 zestawione z otwartym źródłem (lista pozycji niżej), (b) przegląd wszystkich checków nowych scenariuszy pod kątem „checków, które nic nie sprawdzają” (znaleziono i naprawiono: `max_speed_kmh` przy cofaniu → zastąpione `min_speed_kmh`), (c) próba złamania testów = test mutacyjny (B). Wyniki: patrz §6–7.
- **B. Test mutacyjny** — każdy nowy check pada przy mutacji (tabela w §6); mutacje robione lokalnie (kopia JSON definicji/scenariusza), **niecommitowane** (`git status` czysty poza plikami PR).
- **C. Pełne uruchomienie po zmianach** — tabela w §0 (234/234; 119 scenariuszy / 639 checków / 0 porażek; Python 12 passed).
- **D. Rebase + diff** — `git fetch && git rebase origin/main` przed PR; `git diff --stat origin/main` = tylko `tests/physics/**` + ten raport.

## 6. Tabela testu mutacyjnego (wszystkie nowe checki; każdy daje FAIL)

| Check (scenariusz) | Mutacja (lokalna, niecommitowana) | Wynik |
|---|---|---|
| `max_articulation_deg` ∈ [20; 95]° (dock) | `fifthWheel.yawLimitDeg` 90→100000 (odboj wyłączony) | 179,99° FAIL; przeciwna: steer=0 → 0° FAIL (min) |
| `wheel_lift` = 0 (dock) | `antiRollStiffness` ×100 + pełny skręt | wheel_lift = 1 FAIL |
| `stalled` = 0 (dock + rampa) | `stallRpm` 350→1200 | stalled = 1 FAIL |
| `min_speed_kmh` ≥ −15 (dock) | `maxRpm` 2100→1e6 + pełny gaz | −30,5 km/h FAIL |
| `final_z_m` ≤ −3 (dock) | selector R→D (jedzie do przodu) | z = +62,7 m FAIL |
| `max_dv_step_ms` ≤ 0,35 (dock + rampa) | przeszkoda 27 cm na torze wstecznym + `maxRpm`→1e6 | 0,409 m/s FAIL |
| `max_fifth_wheel_error_mm` ≤ 5 (dock + rampa) | `fifthWheel.iterations` 8→1 | 9,2 mm FAIL |
| `min_speed_kmh` ≥ −12 (rampa) | `maxRpm`→1e6, target 30 km/h | −32,5 km/h FAIL |
| `min_rpm` ≥ 550 (rampa) | `idleRpm` 600→480 | 479,5 rpm FAIL |
| `drift_m` ≥ 8 m (rampa) | hamulec postojowy trzymany (brak jazdy) | 0,005 m FAIL |
| `final_z_m` ≤ −5 (rampa) | jw. | −0,002 m FAIL |
| `max_articulation_deg` ≤ 20° (rampa) | `overrides.articulationDeg` = 30 | 91,1° FAIL |
| `wheel_lift` = 0 (rampa) | `maxRpm`→1e6 + steer 0,9 + target 30 | wheel_lift = 1 FAIL |

## 7. Ustalenia z przebiegów przeglądu (A)

- (a) Cytaty: wszystkie pozycje §4 zweryfikowane przeciwko źródłom otwartym w audicie/PHYSICS-SOURCES-2 (A1, A2, A3, A10, S1, S2, S5) + powtórnie wyrywkowo otwarte w tym zadaniu (EUR-Lex 92/6, GRRF-56-3, FHWA WUS — zgodne). **Nie wyciągano wniosków wykraczających poza cytat** (lekcja #17: np. „przy 40 t start z 1.–2. biegu” to wniosek, nie cytat — nie użyto).
- (b) Puste checki: znaleziono 1 w nowych scenariuszach (`max_speed_kmh` wstecz = max ze znakowanej wartości, zawsze ~0) → zamienione na `min_speed_kmh`. Istniejące scenariusze: brak innych przypadków; najszersze pasma mają uzasadnienie w `source`.
- (c) Próba złamania = §6; dodatkowo `test_scenario_strictness.py` pilnuje, żeby nikt (łącznie ze mną) nie poluzował ścianek krawężników.
