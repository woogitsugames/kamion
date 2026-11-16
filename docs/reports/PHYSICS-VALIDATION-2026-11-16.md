# Walidacja fizyki bez Unity — 2026-11-16 (zadanie P7, sesja s23)

Gałąź `physics-validation-s23` z `origin/main` `c5fd93834`. Solver: rdzeń fizyki gry (`game/Assets/_Project/Vehicle/Physics/**`, kompilowany wprost z projektu Unity przez `tools/physics-runner/Sim/Sim.csproj`, ADR 0004) uruchomiony w czystym .NET 8 (SDK 8.0.428, Linux), dt = 0,01 s, 4 podkroki. **Nic z tego nie było uruchamiane w Unity/PhysX ani na Windows player.** Fizyka nie była zmieniana.

## 1. Wynik w skrócie

| Pakiet | Wynik | Dowód |
|---|---|---|
| `dotnet test tools/physics-runner -c Release` (main `c5fd93834`) | **277/277 passed**, 0 failed, 32 s | `artifacts/physics-validation-s23/dotnet-test.log`, `artifacts/physics-validation-s23/tests/tests.trx` |
| to samo po dodaniu scenariusza 50→0 (`e743b4a76`) | **279/279 passed** (+2 warianty w `ValidationTests`) | `artifacts/physics-validation-s23/dotnet-test-after.log` |
| Runner, wszystkie scenariusze (`c5fd93834`) | **135/135 przebiegów PASS, 789/789 kontroli** + powtarzalność, przemiatanie dt/podkroków, bench | `artifacts/physics-validation-s23/run/summary.md`, `run/*.csv`, `artifacts/physics-validation-s23/runner.log` |
| Nowy scenariusz `brake_50_0_dry_abs_comb` (`e743b4a76`) | 2/2 PASS, 16 kontroli | `artifacts/physics-validation-s23/brake50/` |
| Pierścień skrętu 96/53/WE (scenariusz ad hoc, **nie w repo**) | **FAIL o 1–4 cm** (patrz §3) | `artifacts/physics-validation-s23/ring-96-53/` |
| `python tests/physics/test_scenario_strictness.py` | **FAIL już na main** (nie z tej zmiany, patrz §6) | — |

## 2. Skąd są referencje

docs/04 §6 wymienia scenariusze, ale **nie podaje liczb**. Wartości oczekiwane, źródła i tolerancje są w plikach scenariuszy `tests/physics/scenarios/*.json` (generowanych przez `tests/physics/generate_stage2_scenarios.py`), z odwołaniami do źródeł S1–S9 w `docs/VEHICLE_REFERENCE_DATA.md`. Kolumna „status” poniżej to status zapisany w samej kontroli (SOURCED / DERIVED / WORKING_VALUE).

## 3. Tabela: docs/04 §6 vs wynik runnera

Zmierzone = wartość metryki z runnera (CSV + `summary.md`), bez zaokrąglania na korzyść. Ścieżki CSV względem `artifacts/physics-validation-s23/`.

| §6 | Scenariusz | Zmierzone | Referencja (źródło, status) | Tolerancja | Wynik | CSV |
|---|---|---|---|---|---|---|
| 5 | Hamowanie 80→0 sucho ABS, **40 t** | **41,31 m**; MFDD 6,885 m/s²; przegub 0°; blokada osi 0 s | R13 zał. 4 typ-0 N3: s ≤ 0,15 v + v²/130 → 61,2 m przy 80 km/h; dm ≥ 5,0 m/s² (S5/S9, GRRF-56-3; **SOURCED** w scenariuszu, ale formuła ma prędkość próby 60 km/h — 80 km/h to ekstrapolacja) | 35–61,2 m; MFDD 5,0–8,0 | PASS | `run/brake_80_0_dry_abs_comb@laden40.csv` |
| 5 | Hamowanie 80→0 sucho ABS, **pusty** zestaw (14,5 t) | **39,19 m**; MFDD 7,422 | jw. | 35–61,2 m; 5,0–8,0 | PASS | `run/brake_80_0_dry_abs_comb@empty.csv` |
| 5 | Hamowanie 80→0 sucho ABS, sam ciągnik | 34,26 m; MFDD 7,722 | WORKING_VALUE (v²/2a + narastanie) | 32–55 m; 5–8 | PASS | `run/brake_80_0_dry.csv` |
| 5 | **Hamowanie 50→0 sucho ABS, 40 t** (nowy) | **17,37 m**; MFDD 6,686 | R13 typ-0 N3 jw. przy 50 km/h: 7,5 + 19,2 = **26,7 m** (ekstrapolacja poniżej 60 km/h); dolna granica v²/(2·0,8 g) = 12,3 m + narastanie (WORKING) | 15–26,7 m; 5,0–8,0 | PASS | `brake50/brake_50_0_dry_abs_comb@laden40.csv` |
| 5 | **Hamowanie 50→0 sucho ABS, pusty** (nowy) | **16,59 m**; MFDD 6,760 | jw. | jw. | PASS | `brake50/brake_50_0_dry_abs_comb@empty.csv` |
| 5 | 80→0 mokro ABS, pusty / 40 t | 55,20 / 56,84 m; MFDD 4,797 / 4,675 | WORKING_VALUE (μ_mokre ≈ 0,5) | 45–95 m; 3,0–5,5 | PASS | `run/brake_80_0_wet_abs_comb@{empty,laden40}.csv` |
| 5 | 80→0 bez ABS sucho / mokro, 40 t | 49,18 / 81,99 m | WORKING_VALUE (blokada kół) | 33–150 / 30–150 m | PASS | `run/brake_80_0_{dry,wet}_noabs_comb@laden40.csv` |
| 5 | Czas reakcji hamulców (postój) | przód 0,25 s, tył 0,31 s, naczepa 0,53 s (40 t) / 0,54 s (pusty) | R13 zał. 4 pkt 4.1.1: ≤ 0,6 s (SOURCED; metoda zał. 6 nieczytana) | ≤ 0,6 s | PASS | `run/brake_response_static@*.csv` |
| 3 | 0–80 km/h, **40 t**, płasko | **47,58 s** (0–60: 28,04 s) | DERIVED (stosunek moc/masa + straty zmian biegów) | 40–95 s (0–60: 25–60 s) | PASS | `run/launch_flat_comb@laden40.csv` |
| 3 | 0–80 km/h, pusty zestaw | 21,14 s (0–60: 13,71 s) | DERIVED | 20–55 s (12–35 s) | PASS (0,14 s nad dolną granicą) | `run/launch_flat_comb@empty.csv` |
| 3 | 0–80 km/h, sam ciągnik | 14,06 s (0–60: 9,688 s) | WORKING_VALUE | 12–32 s (7–20 s) | PASS | `run/launch_0_80_flat.csv` |
| 2 | Ruszanie 6 % pod górę, pusty / 40 t | cofnięcie 2,2 / 2,4 mm; 0–15 km/h 3,11 / 4,94 s; sprzęgło 29 / 37 °C; bez zgaśnięcia | WORKING_VALUE | ≤ 5 cm; ≤ 250 °C | PASS | `run/launch_6pct_uphill_comb@*.csv` |
| 4 | Prędkość maks. (ogranicznik), 40 t | 89,17 km/h | 90 km/h, dyr. 92/6/EWG (S3, SOURCED) | ≤ 90,5; ustala 88–90 | PASS | `run/top_speed_flat_comb@laden40.csv` |
| 4 | Ustalona prędkość 5 %, 40 t | 49,77 km/h (zakres 0,05 km/h, min 1464 rpm) | DERIVED ≈ 54 km/h | 44–60 km/h | PASS | `run/grade_5pct_steady@laden40.csv` |
| 6 | Zjazd 7 % typ IIA, 40 t | średnio 30,0 km/h, hamulec roboczy 0 | R13 zał. 4 pkt 1.8.2 (SOURCED) | 25–35 km/h, bez roboczego | PASS | `run/downhill_7pct_typeIIA@laden40.csv` |
| 6 | Zjazd 8 % retarder, 40 t | 40,0 km/h, zakres 2e-7 km/h, retarder 2193 N m | WORKING_VALUE | 35–45 km/h; ≤ 4000 N m | PASS | `run/downhill_8pct_retarder_comb@laden40.csv` |
| 7 | **Promień skrętu zestawu — pierścień 12,50 / 5,30 m** (ad hoc, 40 t, 5 km/h, oś tylna ciągnika na R = 10,15 m) | ślad zewn. **12,511 m** (narożnik zderzaka), ślad wewn. **5,276 m** (bok naczepy); szerokość pierścienia potrzebna **7,235 m**; pusty: 12,514 / 5,274 m | dyr. 96/53/WE zał. I pkt 1.5: zewn. 12,50 m, wewn. 5,30 m (R3-004, **SOURCED** w `research/cloud2/truck-parameters/manifest.csv`) | zewn. ≤ 12,50; wewn. ≥ 5,30 (szerokość ≤ 7,20) | **FAIL** (o 1,1–1,4 cm na zewnątrz i 2,4–2,6 cm wewnątrz; szerokość o 3,5 cm za duża) | `ring-96-53/ring_96_53_comb@{empty,laden40}.csv` |
| 7 | Łuk R = 50 m, 10 km/h, offtracking 40 t | 0,603 m (pusty 0,609) | DERIVED √(R²+e²) − √(R²+e²−L²) = 0,59 m | 0,4–0,8 m | PASS | `run/circle_r50_10kmh_comb@*.csv` |
| 7 | Próg przewrócenia, 40 t, środek masy wysoko | pierwsze oderwanie koła przy 0,337 g | WORKING (literatura 0,3–0,45 g, UNVERIFIED) | 0,25–0,55 g | PASS | `run/rollover_r50_cog_high@laden40.csv` |
| 8 | Zmiana pasa 80 km/h, 40 t | przegub maks. 0,83°, RA 0,996, bez oderwania kół | WORKING (literatura RA 1,0–1,3, UNVERIFIED) | RA 0,8–1,6; ≤ 6° | PASS | `run/lane_change_80@laden40.csv` |
| 1 | **Postój 12 % w dół, hamulec postojowy, 40 t, 300 s** | pełzanie 1,48 mm (5–300 s), 0,042 mm po 60 s; naczepa 4,55 mm; v maks. 0,48 mm/s | R13 zał. 4 pkt 2.3.2: postojowy ciągnika trzyma zestaw na 12 % (SOURCED); „bez pełzania” WORKING | ≤ 5 mm; ≤ 0,5 mm po 60 s; ≤ 1 mm/s | PASS | `run/park_12pct_down_comb@laden40.csv` |
| 1 | Postój 12 % w dół, **pusty** | pełzanie 2,71 mm; **naczepa 4,688 mm** | jw. | ≤ 5 mm | PASS (blisko granicy: 94 %) | `run/park_12pct_down_comb@empty.csv` |
| 1 | Postój 12 % w górę, pusty / 40 t | pełzanie 1,90 / 0,97 mm; **naczepa 4,972 / 3,26 mm** | jw. | ≤ 5 mm | PASS (pusty: 99,4 % granicy) | `run/park_12pct_up_comb@*.csv` |
| 1 | Postój płasko 5 min, 40 t / 30 min | dryf 0,34 mm; v ≤ 2,4e-5 m/s; KE ≤ 1,0e-5 J przez 30 min; dryf energii 1,07 J | WORKING_VALUE | ≤ 5 mm; ≤ 1 mm/s; ≤ 1e-3 J; ≤ 5 J | PASS | `run/park_flat_5min_comb@laden40.csv`, `run/soak_30min_parked@laden40.csv` |
| 9 | Jackknife, mokro, R = 120 m, 60 km/h, awaria EBS (bez ABS), pusty | przegub **87,45°** | WORKING: złożenie musi być możliwe | ≥ 30° | PASS | `run/jackknife_wet_curve_noabs@empty.csv` |
| 9 | Jackknife, retarder bez ABS, pusty | 92,63° (miękki ogranicznik 90° + 2,6°) | WORKING | ≥ 30° | PASS | `run/jackknife_wet_curve_retarder_noabs@empty.csv` |
| 9 | Hamowanie w łuku z ABS (50 % / 100 % pedału), pusty / 40 t | 7,77 / 4,59° pusty; 5,14 / 5,14° 40 t | WORKING | ≤ 10° | PASS | `run/jackknife_wet_curve_abs_{50,100}@*.csv` |
| 9 | Jackknife wg ADR 0228 / PR #113 | — | ADR 0228 **nie ma w main** (gałąź `origin/jackknife-0228`) | — | **po #113** | — |
| 10 | Cofanie pod rampę (S-manewr) | scenariusz `reverse_dock_s_maneuver_comb` przechodzi (geometria analityczna) | WORKING | — | PASS (tylko solver; rampa/kolizje niesprawdzone) | `run/reverse_dock_s_maneuver_comb@*.csv` |
| 11 | Krawężnik 15 cm lewą stroną, 40 t | Fz maks. 2,95 × statyczne; przechył naczepy 3,39°; skok pozycji 1e-14 m | WORKING | ≤ 4×; ≤ 8°; ≤ 1e-6 m | PASS (tylko kontakt analityczny, nie PhysX) | `run/curb_15cm_left_comb@laden40.csv` |
| 12 | dt 50/60/100/120 Hz | 0–80 solo 14,21/14,21/14,06/14,07 s (0,58 %); 80→0 40 t 40,90/40,99/41,31/41,37 m (0,59 %); przegub 0,28 %; 0–60 40 t 0,63 % | WORKING | ≤ 5 % | PASS | `run/summary.md` (bez CSV) |
| 12 | Podkroki 2/4/8 | 80→0 solo 0,56 %; 80→0 40 t 0,33 % | WORKING | ≤ 5 % | PASS | jw. |
| 3/14 | **Powtarzalność** (3 przebiegi, kurs 0/37/113°) | 0–60: 9,688/9,688/9,688 s; 0–80: 14,055 ×3 — odchyłka 0,00 % | docs/04 §6.3 | — | PASS | `run/repeatability_run{1,2,3}.csv` |
| 14 | Soak 30 min, 20 cykli, 40 t | prędkość przelotowa 73,02 → 72,46 km/h (cykl 1 vs ostatni); dryf energii −2,84 J; powietrze ≥ 11,34 bar | WORKING | 60–82 km/h; ≤ 5 J | PASS | `run/soak_30min_cycle@laden40.csv` |
| 15 | Znak sterowania (przód/tył, solo/zestaw) | np. 40 t w prawo +17,16 °/s | DERIVED | znak | PASS | `run/steer_sign_*.csv` |
| — | Koszt kroku, 40 t (desktop Release, Linux) | średnio 15,5 µs, p99 29,3 µs, maks. 2111 µs | — (to nie jest pomiar telefonu ani Windows) | — | info | `runner.log` |

Pełna lista 789 kontroli: `artifacts/physics-validation-s23/run/summary.md`.

### Pierścień skrętu — szczegóły (FAIL)

- Sposób: scenariusz ad hoc `ring_96_53_comb` (warianty pusty / 40 t, kierowca `circle`, 5 km/h, R osi tylnej ciągnika 10,15 m — dobrane tak, by narożnik zderzaka wypadał na 12,50 m; 240 s, ocena od t = 120 s, stan ustalony). Obwiednia liczona po przebiegu z CSV (`x, z, heading_deg, articulation_deg, trailer_x, trailer_z`) tą samą konwencją ramek co `tests/physics/swept_path_gate3.py`: zderzak 1,45 m przed osią przednią, połowa szerokości 1,245 m; naczepa od +1,60 do −12,00 m od sworznia, połowa szerokości 1,275 m. Środek okręgu dopasowany metodą najmniejszych kwadratów do śladu osi tylnej.
- Wynik 40 t: R osi tylnej 10,226 m (kierowca o 7,6 cm za szeroko), ślad zewnętrzny 12,511 m, wewnętrzny 5,276 m, przegub 47,3°. Pusty: 12,514 / 5,274 m.
- Wynik nie zależy od wyboru promienia: potrzebna szerokość pierścienia to **7,235 m przy dopuszczalnych 7,20 m**. Przesunięcie toru nie pomoże.
  - *Errata (ADR 0280, 2026-11-16): szerokość zależy od promienia, dW/dR = −0,64 m/m. Decyduje promień wewnętrzny przy zewnętrznym = 12,50 m: ≈ 5,25 m, czyli brakuje ok. 5 cm. Przesunięcie toru nie pomoże, wniosek bez zmian. Scenariusze i metryka są już w repo: `ring_96_53_comb` (znana porażka) i `ring_96_53_comb_rwb760`.*
- Przyczyna, którą widać w danych: tridem bez osi skrętnej ma ślad wewnętrzny 6,554 m. Kinematyka sztywnego zestawu z rozstawem 7,70 m do środkowej osi dałaby 6,764 m (√(10,249² − 7,70²)). Model daje więc o 0,21 m większe zachodzenie. Efektywny rozstaw wynosi ≈ 7,88 m: osie 1 i 3 naczepy pracują przeciwnymi siłami bocznymi ±27–29 kN (wykres). To fizycznie rozsądne zachowanie tridemu, ale geometria naczepy (7,70 m, `dims.json`, status WORKING) nie mieści się w 96/53/WE bez osi samoskrętnej albo krótszego rozstawu. Wymaga decyzji, nie poprawki tolerancji.
- Zastrzeżenie: wynik dotyczy jazdy po okręgu w stanie ustalonym. Przepis opisuje też wjazd stycznie i wychylenie tyłu ≤ 0,60 m — tego nie mierzono.

## 4. Wykresy (obejrzane)

PNG z `uv run tools/telemetry/plot.py` (skrypt z repo) w `artifacts/physics-validation-s23/sel/`:

- `brake_80_0_dry_abs_comb@laden40.png`: liniowy spadek prędkości 80→0 w ~4 s. Ciśnienie w komorach przód 8,5 bar, tył ~7,4 bar (korektor). Kabina pochyla się o ~3°, Fz osi przedniej oscyluje 50–75 kN podczas hamowania. **W chwili zatrzymania** pojawia się skok przyspieszenia wzdłużnego +3,5 m/s² i odbicie prędkości 0–2 km/h przez ~1 s (powrót zawieszenia/kabiny). W liczbach mieści się w tolerancji (`max_dv_step` 0,07 m/s), ale do sprawdzenia w feel teście.
- `brake_50_0_dry_abs_comb@laden40.png`: ten sam obraz, zatrzymanie po ~2,8 s. Podczas redukcji 10→8 przy wciśniętym hamulcu obroty silnika skaczą do ~1480 rpm, a moment netto silnika do ~+1300 N m (dopasowanie obrotów AMT przy hamowaniu). Na końcu poślizg naczepy dochodzi do −0,36 w jednej klatce, bez blokady (> 2 m/s).
- `launch_flat_comb@laden40.png`: biegi 4→12, czyste piły obrotów 1300–1750 rpm, ogranicznik ~89 km/h od ~60 s, bez cofnięcia.
- `park_12pct_down_comb@laden40.png`: krótki stan przejściowy < 5 s (v ≤ 0,28 km/h przez ułamek sekundy), potem płasko przez 300 s. Bez oscylacji.
- `jackknife_wet_curve_noabs@empty.png`: oś napędowa zablokowana od t = 6 s (κ = −1 przez ~2,5 s), przegub rośnie do ~87° i zostaje na ograniczniku.
- `jackknife_wet_curve_abs_50@laden40.png`: przegub ≤ 5,1°. **Na starcie scenariusza** (t < 2 s) AMT przełącza 11→N→9→N→11, a silnik dochodzi do 1700 rpm. To przejściowy stan inicjalizacji przy 60 km/h, nie samo hamowanie. Warto sprawdzić, czy to nie artefakt `initial.gear`.
- `ring_96_53_comb@laden40.png`: okrąg zamknięty, stan ustalony od ~50 s, przegub 47°, bieg 1, 5 km/h. Siły boczne tridemu: osie 1 i 3 przeciwnie (scrub), oś 2 ~−5 kN.

## 5. Czego nie da się sprawdzić bez Unity (NIESPRAWDZONE)

- Integracja PhysX dwóch ciał z więzem siodła, kontakt koła–podłoże przez kolidery Unity (raycasty w scenie), kolizje nadwozia z otoczeniem i ciągnika z naczepą. Runner ma podłoże analityczne i własny kontakt nadwozia (ADR 0158).
- Krawężniki, progi i koleiny na prawdziwej geometrii świata (`WorldC`): runner sprawdza tylko analityczne bloki. Koleiny nie są modelowane.
- §6.10 cofanie pod rzeczywistą rampę oraz ciasne manewry na placu (geometria sceny, kamera naczepy).
- §6.12 FPS 30/60 i obciążenie CPU w buildzie (runner sprawdza tylko dt i podkroki), §6.13 floating origin i streaming, §6.15 tryby wejścia inne niż bezpośrednia komenda skrętu (kierownica/FFB ADR 0263, gamepad, żyroskop). Dotyk jest sprawdzony w runnerze (ADR 0149).
- Koszt kroku na referencyjnym PC z Windows (bramka) — tu tylko desktop Linux, bez znaczenia dla budżetu.
- Feel test właściciela (docs/PHYSICS_VALIDATION.md §8).

## 6. Rozbieżności i ryzyka

1. **docs/04 §6 nie ma wartości referencyjnych.** Żyją w JSON-ach scenariuszy. Zadanie zakładało, że referencje są w §6.
2. **Status R13 typ-0 jest niespójny.** `brake_80_0_dry_abs_comb` ma SOURCED (GRRF-56-3). `brake_80_0_dry` (solo) w swoim `source` nadal pisze „believed … (UNVERIFIED)”. docs/PHYSICS_VALIDATION.md §3 pisze „R13 N3 type-0 figures UNVERIFIED”. VEHICLE_REFERENCE_DATA S5 mówi, że granica 80→0 ≤ 61,2 m to „only an extrapolation” formuły z prędkości próby 60 km/h. To samo dotyczy nowego 26,7 m przy 50 km/h. Bezpośrednio z przepisu wynika tylko granica przy 60 km/h: **36,7 m**. Takiego scenariusza (60→0) nie ma. Proponuję dodać `brake_60_0_dry_abs_comb` jako jedyny w pełni SOURCED punkt drogi hamowania.
3. **docs/PHYSICS_VALIDATION.md §3 jest nieaktualny.** Podaje np. 0–80 solo 13,8 s, 80→0 solo 34,9 m i jackknife 81,4°. Dziś jest 14,06 s, 34,26 m i 87,45°: po ADR 0201b / F2, opisane w §6g, ale tabela §3 nie była odświeżona. Również „141 xUnit tests” — dziś 277.
4. **`tests/physics/test_scenario_strictness.py` nie przechodzi na main `c5fd93834`.** Generator emituje `kerb_step_27cm_42kmh_comb` z `"overrides": {"bodyContact": false}`, a zakomitowany JSON tego nie ma (dryf generator ↔ plik, nie z tej gałęzi). Do decyzji, która wersja jest prawdziwa: runner przechodzi z plikiem zakomitowanym. Przy regeneracji pojawiają się też różnice samej kolejności kluczy w 3 plikach krawężnikowych. Nie komitowałem ich.
5. **Pierścień 96/53/WE: FAIL o kilka cm** (§3). To jedyny niezielony wynik i dotyczy geometrii naczepy, nie solvera. Nie da się tego zapisać jako scenariusz repo bez nowej metryki obwiedni w `tools/physics-runner/Sim/Metrics.cs` (np. `swept_outer_radius_m` / `swept_inner_radius_m`). Zgodnie ze zleceniem nie ruszałem Sim. **Propozycja:** dodać tę metrykę i scenariusz `ring_96_53_comb` (R3-004 już to postuluje). Najpierw właściciel/lider musi zdecydować o geometrii: oś samoskrętna w tridemie, rozstaw sworzeń–oś albo zwis zderzaka.
6. Postój 12 % pusty: pełzanie naczepy 4,97 mm przy granicy 5 mm (99,4 %). Każda drobna zmiana zawieszenia naczepy może to przewrócić.
7. Pusty zestaw 0–80: 21,14 s przy dolnej granicy 20 s (DERIVED). Granica, nie referencja z pomiaru.
8. ADR 0228 / PR #113 (jackknife) nie jest w main. Scenariusze §6.9 w tym raporcie dotyczą stanu przed #113 i po scaleniu trzeba je powtórzyć.

## 7. Zmiany w repo (gałąź `physics-validation-s23`)

- `e743b4a76` test(physics): `brake_50_0_dry_abs_comb` (generator + JSON, warianty pusty / 40 t, bieg 10 ≈ 1120 rpm przy 50 km/h). Kontrole jak przy 80→0, granica R13 26,7 m. Automatycznie objęty przez `ValidationTests` (277 → 279).
- ten raport.

## 8. Odtworzenie (Windows, PowerShell 7, z katalogu repo)

```powershell
$env:DOTNET_ROOT = "$env:LOCALAPPDATA\Microsoft\dotnet"; $env:PATH = "$env:DOTNET_ROOT;$env:PATH"
git switch physics-validation-s23
dotnet test tools/physics-runner -c Release                                                     # 279 testów
dotnet run -c Release --project tools/physics-runner/Runner -- --out artifacts/physics-validation-s23/run   # 137 przebiegów + multi-run + bench
dotnet run -c Release --project tools/physics-runner/Runner -- --only brake_50_0_dry_abs_comb --out artifacts/physics-validation-s23/brake50
uv run tools/telemetry/plot.py artifacts/physics-validation-s23/run/brake_80_0_dry_abs_comb@laden40.csv --out artifacts/physics-validation-s23/sel
```

Pierścień (scenariusz poza repo): zapisz poniższy JSON jako `artifacts/ring/ring_96_53_comb.json` i uruchom `dotnet run -c Release --project tools/physics-runner/Runner -- --scenarios artifacts/ring --out artifacts/physics-validation-s23/ring-96-53`. Obwiednię policz z CSV jak w §3 (analiza ad hoc w numpy, poza repo).

```json
{"schemaVersion": 1, "id": "ring_96_53_comb", "description": "ad hoc ring test", "spec": "docs/04 s6.7; 96/53/WE zal. I 1.5 (R3-004)",
 "variants": ["empty", "laden40"], "ground": {"gradePercent": 0, "surface": "dry_asphalt"}, "initial": {}, "duration": 240,
 "driver": {"type": "circle", "targetKmh": 5, "radius": 10.15, "direction": 1},
 "checks": [{"metric": "max_dv_step_ms", "status": "WORKING_VALUE", "source": "no solver spikes", "max": 0.35},
            {"metric": "radius_mean_m", "status": "WORKING_VALUE", "source": "observed", "min": 0, "from": 120},
            {"metric": "trailer_offtracking_m", "status": "WORKING_VALUE", "source": "observed", "min": 0, "from": 120}]}
```
