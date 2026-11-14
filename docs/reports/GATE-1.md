# Bramka 1 — Laboratorium jazdy: ciągnik (raport)

Data: 2026-11-13 (s19) · Autor: build-qa · Repo: gałąź `gates-s19` od main `75eab9591` · Unity 6000.3.28f1
Definicja: `docs/03_ETAPY_I_BRAMKI.md` (Etap 1). Szkic z 9.11 (opis placu, sterowania, kamer, render z edytora): `docs/reports/GATE-1-draft.md`.

## Werdykt: SZKIC — czeka na telefon

Wszystkie testy w edytorze i w symulatorze fizyki są zielone (liczby niżej, z 13.11). **Z telefonu nie ma żadnego pomiaru bramki 1**:
nie ma przejazdu z autopilotem, telemetrii ani testu postoju na A16. Bramka wymaga „wszystko na telefonie”, więc nie jest zaliczona.
Gotowa jest komenda pomiaru dla lidera (sekcja „Pomiar na telefonie”).

Co jest z telefonu (sprawdzone w `artifacts/device/`): tylko 5 przebiegów sceny DrivingLab **bez autopilota i bez telemetrii**
z 9.11, na buildach `-dirty` (nie są dowodem bramki): A16 Medium `artifacts/device/RFGL34SJYDZ/20261109-154611`, `-154809`, `-155323`, `-155456`
(mean 30,01 FPS, p95 33,45–33,46 ms, p99 33,53–33,54 ms, PSS 332–338 MB) i S24+ High `artifacts/device/RZCX60VE8ZY/20261109-155249`
(29,98 FPS, p95 33,77, p99 34,58 ms, PSS 535 MB). Plus test właściciela na Foldzie (D55, APK `e364975f12`): „jest spoko, już lepiej się jeździ” — ocena kierowania, nie pomiar.

## Kryteria z `docs/03` (Etap 1) — stan

| Kryterium | Symulator fizyki (.NET) | Unity (edytor) | Telefon |
|---|---|---|---|
| Testy `docs/04` §6 dla ciągnika solo zielone w tolerancjach | ✅ 132/132 scenariuszy, 750 kontroli | ✅ PlayMode 155/163 (0 fail, 8 skip) | ❌ brak |
| Brak dryfu na postoju | ✅ (tabela) | ✅ (szkic 9.11: 2–5 mm / 60 s na 12 %) | ❌ brak — w skrypcie: `park_flat_solo` 5 min |
| Brak oscylacji | ✅ `soak_30min_parked`, `straight_after_steer_pulse@solo` | ✅ | ❌ |
| Krawężnik nie teleportuje | ✅ max |Δv| na krok 0,050–0,096 m/s (limit 0,35) | ✅ `KerbStrikeParityTests` w PlayMode | ❌ (ręcznie, plac: krawężnik 8/15 cm) |
| 3 przejazdy 0–80 km/h powtarzalne ±3 % | ✅ 13,600 / 13,600 / 13,600 s (0,00 %) — deterministyczne | — | ❌ brak; autopilot gry jeździ tylko po okręgu → w skrypcie **zastępczo** 3× ruszanie 0→30 i 0→38 km/h na okręgu R50 (oznaczone PROXY) |
| Wszystko na telefonie | — | — | ❌ |

## Liczby (13.11, `dotnet` + Unity w worktree `gates-s19`)

Źródła: symulator `artifacts/physics/20261113-215728/summary.md` (kopia `C:\Users\matma\Documents\Claude\kamion\artifacts\gates-s19\physics-20261113-215728\`),
log `artifacts/gates-s19/runner.log`; testy jednostkowe `artifacts/gates-s19/dotnet-test.log`; Unity `artifacts/tests/editmode-20261113-215718.xml`, `artifacts/tests/playmode-20261113-215823.xml` (w worktree).

Komendy:
```
dotnet test tools/physics-runner -c Release                      # 266/266 (w tym golden telemetry 9/9)
dotnet run -c Release --project tools/physics-runner/Runner      # ALL 132 SCENARIOS PASSED (750 checks)
pwsh scripts/test.ps1 -Platform EditMode                         # 535: 532 pass, 2 fail, 1 skip
pwsh scripts/test.ps1 -Platform PlayMode                         # 163: 155 pass, 0 fail, 8 skip
```
EditMode — 2 faile to znane `CarPaintMaterialTests.DepositionChannel_RequiresScopedYardOptInOrExistingCar` (materiał lakieru, nie fizyka; zgłaszane od s18 w HANDOVER).

Ciągnik solo (symulator, scenariusze `tests/physics/scenarios`, granice i źródła w `summary.md`):

| `docs/04` §6 | Scenariusz | Wynik | Granica |
|---|---|---|---|
| 1. Postój płasko, hamulec postojowy | `standstill_flat_parking` | dryf 2,2e-16 m, v max 1,2e-14 m/s | ≤ 0,012 m, ≤ 0,001 m/s |
| 1. Postój 12 % pod górę / w dół | `standstill_12pct_uphill_parking` / `_downhill_` | dryf 2,8 mm / 4,5 mm | ≤ 12 mm |
| 2. Ruszanie pod górę 6 % | `launch_6pct_uphill` | cofnięcie 1,7 mm, 0–30 km/h 5,82 s, obroty ≥ 600 | ≤ 50 mm, 4–25 s |
| 3. 0–60 / 0–80 km/h płasko | `launch_0_80_flat` | 9,94 s / 13,60 s, bez cofania, bez zgaśnięcia | 7–20 s / 12–32 s (WORKING_VALUE) |
| 3. Powtarzalność 0–80 ×3 | multi-run | 13,600 ×3, odchyłka 0,00 % | ±3 % |
| 4. Prędkość maksymalna (ogranicznik) | `top_speed_flat` | 89,35 km/h | 88–90 (ogranicznik 90 km/h, SOURCED) |
| 5. Hamowanie 80→0 sucho / mokro | `brake_80_0_dry` / `_wet` | 34,69 m / 50,79 m | 32–55 / 45–85 m |
| 7. Okrąg R25/R50 — utrzymanie prędkości | `circle_r25_20kmh`, `circle_r50_35kmh` | 20,0 / 35,0 km/h | ±1,5 km/h |
| 8. Zmiana pasa 80 km/h | `lane_change_80@solo` | a_lat max 0,93 m/s², yaw max 2,44 °/s, bez oderwania koła | ≤ 2,5 / ≤ 10 |
| 11. Krawężnik 8 / 15 cm | `curb_8cm_both`, `curb_15cm_both`, `curb_15cm_left` | max |Δv| 0,062 / 0,096 / 0,049 m/s | ≤ 0,35 |
| 11. Próg zwalniający | `speed_bump_comb@solo` | skok pozycji 1e-14 m, ugięcie kabiny 36 mm | ≤ 1e-6 m, ≤ 50 mm |
| 12. Różne kroki fizyki 50/60/100/120 Hz | dt-sweep | 0–80: 13,69 / 13,73 / 13,60 / 13,64 s (0,47 %); hamowanie 0,31 %; okrąg 0,02 % | jakościowo bez różnic |
| 15. Kierunek skrętu | `steer_sign_forward_left/right`, `steer_sign_reverse_right` | PASS (prawo = yaw w prawo, 10,9 °/s) | znak |
| — Koszt kroku (komputer, Release, zestaw 40 t) | bench | 8,5 µs średnio, p99 18,4 µs | **nie dotyczy telefonu** |

Golden telemetry (`tests/golden/`, 9 plików, tolerancje `tests/golden/tolerances.json`): w testach `Stage2Tests.GoldenTelemetry_Matches` — zielone.

## Pomiar na telefonie (plan; uruchamia lider po integracji)

Warunki: czysty APK (bez `-dirty`), **żaden proces Unity nie działa** (Unity restartuje demona adb i zrywa A16), telefon odblokowany i podłączony,
`artifacts/locks/PHONE_RUN` założony ręcznie przez lidera.

```
# 1) sprawdzenie planu i APK (nic nie uruchamia)
pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -DryRun
# 2) A16 Low 30 FPS (ok. 20–25 min; instalacja, 8 przebiegów, telemetria 100 Hz, logcat, zrzuty, metryki)
pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -UseExistingLock
#    (opcjonalnie + S24+ High 60: start tylko przy baterii >= 40 %, przerwa < 30 %, chłodzenie < 36 °C)
pwsh scripts/gate12-phone.ps1 -Apk artifacts/apk/kamion-0.1.0-<sha>.apk -UseExistingLock -IncludeS24
# 3) analiza -> artifacts/gate12/<ts>/gate12-summary.md
uv run --project tools/perf python scripts/gate12_telemetry.py artifacts/gate12/<ts>
```
Przebiegi A16 (`scripts/gate12-phone.ps1`): `boot_idle` (Boot 75 s, bramka 0), `park_flat_solo` (postój 5 min, dryf ≤ 1 cm), `c50_solo_1..3`
(autopilot okrąg R50, 40 km/h; Δv na krok ≤ 0,35 m/s, utrzymanie prędkości, koszt kroku `step_us`, powtarzalność 0→30 i 0→38 km/h ≤ 3 % — PROXY),
`c25_solo`, `c50_empty`, `c50_40t` (bramka 2). Pomiar odrzucony, gdy telefon zablokowany, w logcacie wyjątek, brak linii `[LAB] DrivingLab ready`, brak CSV albo APK `-dirty`.

**Czego automat nie zmierzy (gra nie ma takiego trybu autopilota; zmiana kodu gry poza zakresem build-qa):**
- 3× 0–80 km/h na prostej — potrzebny tryb autopilota `launch080` (prosty pas przyspieszania) → zadanie dla gameplay-ui; do tego czasu ręcznie z „Nagraj CSV”;
- postój na 12 % z hamulcem postojowym — ręcznie na podjeździe placu z „Nagraj CSV”;
- krawężnik 8/15 cm, próg, koleiny — ręcznie z „Nagraj CSV”;
- kierunek gyro na prawdziwym czujniku — test w dłoniach (lista w `GATE-1-draft.md`, „Test w dłoniach”).
CSV z ręcznej jazdy: `adb pull /sdcard/Android/data/com.woogitsugames.kamion/files/telemetry` → ten sam skrypt analizy (nazwa katalogu przebiegu `park_*` albo `c50_*`).

## Znane braki
1. Brak jakichkolwiek liczb bramki 1 z telefonu (FPS w placu z jazdą, koszt fizyki na A16, dryf, Δv).
2. Powtarzalność 0–80 na telefonie niemierzalna automatycznie (wyżej).
3. Przyczepność kostki, żwiru, trawy — WORKING_VALUE (szkic, ryzyko 3).
4. Decyzja właściciela otwarta z 9.11: domyślny zakres kierownicy 270° czy 900°.

## Pomiar telefonu s20 (2026-11-14, A16 RFGL34SJYDZ, Low/30, APK kamion-0.1.0-77cfd94bf8, czyste drzewo)
Autopilot straight080 (ADR 0195), DrivingLab, prosta 1300 m. Pełna tabela: `docs/reports/GATE12-PHONE-2026-11-14-A16.md`, dane `artifacts/gate12/20261114-062841`.
| przebieg | 0–60 s | 0–80 s | droga 80→0 m | MFDD m/s² | blokada kół | FPS / p99 ms | PSS MB | fizyka |
|---|---|---|---|---|---|---|---|---|
| solo ×3 | 10,00 | 13,66 (rozrzut 0,00 %) | 35,85 | 7,44 | 0 s | 30,0 / 33,5–33,8 | 386–412 | PASS |
| pusty 14,5 t | 13,23 | 20,67 | 39,67 | 7,46 | 0 s | 30,0 / 33,8 | 393 | PASS |
| 40 t | 28,24 | 47,79 | 40,72 | 7,00 | 0 s | 30,0 / 33,6 | 392 | PASS |
Telefon = edytor w granicach < 0,1 % (edytor: solo 13,67 s / 35,6 m, 40 t 47,80 s / 40,8 m). Krok fizyki p50 ≈ 0,6 ms, p99 ≤ 0,99 ms; temperatura 25 °C. Uwaga: ciąg wersji w grze ma znacznik „-dirty” (pliki nieśledzone w katalogu głównym podczas buildu), metadane APK: dirty=False, sha zgodne. S24+ nie mierzony w tej rundzie.
