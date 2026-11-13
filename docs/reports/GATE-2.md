# Bramka 2 — Naczepa, pneumatyka, pełny układ napędowy (raport)

Data: 2026-11-13 (s19) · Autor: build-qa · Repo: gałąź `gates-s19` od main `75eab9591` · Unity 6000.3.28f1
Definicja: `docs/03_ETAPY_I_BRAMKI.md` (Etap 2). Szkic z 9.11 (co jest w placu, menu „Zestaw…”, sprzęganie, lusterka, render z edytora, lista feel testu): `docs/reports/GATE-2-draft.md`.

## Werdykt: SZKIC — czeka na telefon

Pełny pakiet walidacyjny w symulatorze (pusty zestaw i 40 t) i testy Unity są zielone; golden telemetry w `tests/golden/` przechodzi.
**Z telefonu nie ma pomiaru zestawu** (w `artifacts/device/` żadnego przebiegu z naczepą ani telemetrii) i **nie ma pełnego feel testu właściciela**
z listy bramki (ruszanie pod górę 40 t, hamowanie awaryjne, rondo, cofanie pod rampę). Częściowe opinie właściciela: D55 (kierowanie na Foldzie OK),
D58 i D59 (decyzje projektowe po raporcie fizyki, nie test w dłoniach).

## Kryteria z `docs/03` (Etap 2) — stan

| Kryterium | Stan | Dowód |
|---|---|---|
| Pełny pakiet `docs/04` §6 (pusty i 40 t) | ✅ symulator, ✅ Unity · ❌ telefon | runner 132/132, 750 kontroli; PlayMode `CombinationLabTests` 15/15 |
| Jackknife możliwy przy błędzie kierowcy | ✅ | `jackknife_wet_curve_noabs@empty` 80,6°, `_retarder_noabs@empty` 92,1° (≥ 30°); z ABS 4,7–6,6° (≤ 10°) |
| Brak eksplozji solvera | ✅ symulator | max Δv na krok ≤ 0,35 m/s we wszystkich scenariuszach zestawu (najwyżej: stopień 27 cm 0,325, jackknife z retarderem 0,269; fuzz `fuzz_shrink_speed_runaway_fulllock` 0,715 to test bez tej granicy); `soak_30min_cycle@laden40` NaN 0, dryf energii 1,4 J (≤ 5); `free_fall_drop_comb` bez przyrostu energii |
| Golden telemetry w `tests/golden/` | ✅ | 9 plików CSV + `tolerances.json`; `Stage2Tests.GoldenTelemetry_Matches` w `dotnet test` 266/266 |
| Feel test właściciela na telefonie + lista uwag i realizacja | ⚠️ częściowo | D55 (Fold, kierowanie: „jest spoko, już lepiej się jeździ”, ADR 0149/0151); D58 podatny kontakt nadwozia (ADR 0165), D59 F1 ≤ 3,5° (ADR 0158) — **4 manewry bramki nieocenione** |

## Liczby (13.11; źródła i komendy jak w `GATE-1.md`)

Symulator: `artifacts/physics/20261113-215728/summary.md` (kopia `C:\Users\matma\Documents\Claude\kamion\artifacts\gates-s19\physics-20261113-215728\`). Unity: PlayMode 163 → 155 pass, 0 fail, 8 skip (skip = testy z nagraniem obrazów `Capture_*`); EditMode 532/535 (2 faile `CarPaintMaterialTests`, nie fizyka).

| `docs/04` §6 | Scenariusz | Wynik | Granica (źródło w `summary.md`) |
|---|---|---|---|
| 1. Postój płasko 5 min, pusty / 40 t | `park_flat_5min_comb@empty/@laden40` | dryf 0,06 mm / 0,40 mm | ≤ 5 mm |
| 1. Postój 12 %, 40 t (pod górę / w dół) | `park_12pct_up_comb@laden40`, `park_12pct_down_comb@laden40` | dryf w dół 4,65 mm, pełzanie po 60 s 0,04 mm | ≤ 12 mm, ≤ 0,5 mm |
| 2. Ruszanie 6 % 40 t | `launch_6pct_uphill_comb@laden40` | cofnięcie 2,3 mm, 0–15 km/h 4,84 s, 5 zmian biegu, 0 redukcji | ≤ 50 mm; 4,39–5,29 s |
| 2. Ruszanie 12 % 40 t | `launch_12pct_uphill_comb@laden40` | cofnięcie 5,2 mm, 0–15 km/h 9,74 s, 4 zmiany biegu | ≤ 50 mm; 5–15 s |
| 3. 0–60 / 0–80 pusty / 40 t | `launch_flat_comb@empty/@laden40` | 13,14 / 20,53 s; 28,02 / 47,52 s | WORKING_VALUE pasma |
| 4. Podjazd 5 % / 6 % 40 t, prędkość ustalona | `grade_5pct_steady@laden40`, `grade_6pct_steady_comb@laden40` | 50,2 / 42,5 km/h | 44–60 / 38–54 (DERIVED z mocy) |
| 5. Hamowanie 80→0 suche z ABS pusty / 40 t | `brake_80_0_dry_abs_comb@…` | 38,79 / 40,80 m | ≤ 61,2 m (SOURCED: UN R13 zał. 4) |
| 5. Hamowanie 80→0 mokre z ABS / bez ABS 40 t | `brake_80_0_wet_abs_comb@laden40`, `_noabs_` | 56,8 / 81,9 m | 45–95 / 30–150 m |
| 6. Zjazd 7 % 40 t bez hamulca zasadniczego | `downhill_7pct_typeIIA@laden40` | 30,0 km/h średnio | 25–35 (SOURCED: UN R13 zał. 4 §1.8.2) |
| 6. Zjazd 8 % z retarderem | `downhill_8pct_retarder_comb@laden40` | 40,0 km/h | 35–45 |
| 6. Wyciek w obwodzie tylnym | `air_leak_rear_circuit@laden40` | ostrzeżenie niskiego ciśnienia 1, droga 33,0 m | ≤ 64,4 m |
| 7. Łuk R50, środek masy wysoko / nisko | `rollover_r50_cog_high/low@laden40` | oderwanie koła przy 0,34 g / 0,46 g | 0,25–0,55 g |
| 8. Zmiana pasa 80 / slalom 70, 40 t | `lane_change_80@laden40`, `slalom_70_comb@laden40` | przegub max 0,83° / 1,63°, wzmocnienie tylne 0,996 / 0,989, bez oderwania koła | ≤ 6°, 0,8–1,6 |
| 9. Jackknife (mokro, łuk, bez ABS) | `jackknife_wet_curve_noabs@empty` | 80,6° | ≥ 30° |
| 10. Cofanie S pod rampę | `reverse_dock_s_maneuver_comb@laden40` | przegub max 91,7°, bez oderwania koła | 20–95° |
| 11. Krawężnik 15 cm / uderzenie 14 cm @ 50 km/h, 40 t | `curb_15cm_left_comb@laden40`, `curb_strike_14cm_50kmh_comb@laden40` | Δv 0,059 / 0,083 m/s | ≤ 0,35 |
| 11. Stopień 27 cm @ 42 km/h, 40 t (D58) | `kerb_step_27cm_42kmh_comb@laden40` | wgniecenie zderzaka 3,8 cm, skok pozycji 1e-14 m, błąd siodła 2,5 mm | ≤ 5 cm, ≤ 1e-6 m, ≤ 5 mm |
| 12. Kroki 50–120 Hz | dt-sweep | hamowanie 40 t 0,41 %, zmiana pasa 0,27 %, ruszanie 40 t 0,63 % | jakościowo bez różnic |
| 14. Soak 30 min, 40 t | `soak_30min_cycle@laden40`, `soak_30min_parked@laden40` | NaN 0, dryf energii 1,37 J, skok pozycji 3,7 mm; postój: dryf 0,40 mm | ≤ 5 J, ≤ 10 mm, ≤ 5 mm |
| Sprzęganie / odpinanie 40 t | `couple_uncouple@laden40`, `couple_offset_left_18cm@laden40`, `couple_miss_25cm@laden40` | uderzenie 44,7 kN, nacisk 0,97× stat.; przesunięcie 18 cm → sprzęga (102,8 kN); 25 cm → nie sprzęga | ≤ 150 kN |

ADR fizyki od szkicu 9.11 (stan w main): 0134 (feel ciężarówki, D53 domyślnie 24 t), 0149 i 0151 (kierowanie r2/r3, lejek/pełzanie siodła), 0158 (energia w locie, F1/F2), 0165 (podatny kontakt nadwozia, D58), 0176 (synteza retarder/hamulec silnikowy/AMT — audio).
Pozycje 13 (floating origin, streaming) i 15 (kierunek sterowania we wszystkich wejściach) — pozycja 15 zielona w `VehicleLabTests` (7/7 testów pass); 13 sprawdzane tylko pośrednio przejazdami gate3 (`suspiciousLines: 0`), bez osobnego scenariusza.

## Pomiar na telefonie (plan; uruchamia lider po integracji)

Ten sam skrypt co bramka 1 (`scripts/gate12-phone.ps1`, komendy w `GATE-1.md`). Dla bramki 2 liczą się przebiegi `c50_empty` i `c50_40t`
(okrąg R50, 40 km/h, zestaw pusty i 40 t: koszt kroku fizyki zestawu `step_us` na A16, przegub w stanie ustalonym, błąd siodła ≤ 5 mm, Δv ≤ 0,35 m/s,
FPS/PSS/temperatura z lusterkami i kamerą cofania). Skrót dla samego zestawu:
```
pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -UseExistingLock -Only c50_empty,c50_40t
uv run --project tools/perf python scripts/gate12_telemetry.py artifacts/gate12/<ts>
```
**Feel test właściciela** (bez automatu; lista z `GATE-2-draft.md` „Test w dłoniach”, przy każdym punkcie „Nagraj CSV”): ruszanie pod górę z 40 t
(droga 7 % / podjazd 12 %), hamowanie awaryjne 80 km/h pusty i 40 t (suche i mokra płyta), rondo / okrąg R50 30–40 km/h z 40 t, cofanie pod rampę z kamerą naczepy;
dodatkowo zjazd 7 % z retarderem, sprzęganie, scyzoryk z „ABS: USTERKA”, lusterka, dźwięk. Uwagi → lista zadań vehicle-physics/gameplay-ui → realizacja → wpis tutaj.

## Znane braki
1. Brak liczb zestawu z telefonu (koszt fizyki 2 brył, 152 promieni, lusterek i kamery cofania na A16 — nieznany).
2. Brak feel testu 4 manewrów bramki.
3. Przyczepność nawierzchni innych niż asfalt/beton i wiele pasm akceptacji — WORKING_VALUE (źródła w `summary.md`).
4. Decyzja właściciela otwarta z 9.11: lusterka w kabinie jako okienka czy rozglądanie.
