# 0195 — Autopilot „prosta 0–80–0” (straight080) dla bramek 1–2 + prosta pomiarowa 1300 m

Status: kandydat (gałąź `autopilot-0195`), nie scalone. Data: 2026-11-13. Dotyczy: ADR 0004 (rdzeń fizyki w czystym C#), 0058 (kolumna kierownicy), docs/03 bramki 1–2, docs/04 §6.3/§6.5, `docs/reports/GATE-1.md`/`GATE-2.md` (gates-s19).

## Kontekst
Bramka 1 wymaga „3 przejazdy 0–80 km/h powtarzalne ±3 %” na telefonie, bramka 2 — pakietu §6 dla pustego zestawu i 40 t, w tym hamowania awaryjnego.
Autopilot gry jeździł tylko po okręgu (`circle50/25`), więc `scripts/gate12-phone.ps1` mierzył zastępczo ruszanie 0→30/0→38 km/h na R50 (PROXY).
Pas przyspieszania placu ma 370 m; runner (.NET, te same źródła fizyki) pokazuje drogę start→postój: solo 282 m, pusty zestaw 399 m, **40 t 800 m** — zestaw nie mieści się na placu.

## Decyzja
1. **`StraightRunPilot`** (`game/Assets/_Project/Vehicle/Physics/Pilots/`, czyste C#, bez Unity, zero alokacji na krok): deterministyczny automat faz
   Settle (hamulec 1, 1 s) → Launch (gaz 1 do 80 km/h) → Hold (PI + feed-forward 0,35, 4 s w paśmie ±1,5 km/h) → Brake (pedał 1 do |v| < 0,05 m/s) → Stopped (hamulec).
   Wyjście = wyłącznie polecenia kierowcy (`DriverInput`: gaz, hamulec, wybierak D, postojowy off, kierownica); skrzynia AMT, ABS/EBS, opony — model pojazdu bez skrótów.
   Kierownica: pure pursuit do punktu na linii startu (look-ahead max(10 m, 1,2 v)), + = w prawo. Wyniki liczone online tymi samymi definicjami co runner
   (czas od pierwszego kroku z gazem; droga hamowania od położenia przed narastającym zboczem hamulca; MFDD wg R13 zał. 4 0,8 v0…0,1 v0; max opóźnienie z okna 0,1 s).
2. **Unity**: `DrivingLabBootstrap` — argument `autopilot=straight080` (+ `trailer=solo|empty|24|40`, `speed` domyślnie 80). Pilot krokowany w `FixedUpdate` (kolejność −200,
   przed `VehicleBody`), pisze `vehicle.Input` tuż przed krokiem pojazdu — niezależny od FPS. Na końcu jedna linia logcat `[AUTOPILOT] straight080 done: …` (jedyna alokacja scenariusza).
3. **Prosta pomiarowa** w generatorze placu (`DrivingLabLayout.Straight*`, `DrivingLabSceneBuilder.BuildStraight`): asfalt suchy 1300 × 14 m, z = 300 (na północ od placu, poza strefami),
   jazda na wschód od x = −620; linie krawędziowe, poprzeczki co 50 m, znaki co 100 m, kamera kontrolna `lab-straight`. 40 t staje ~ x = +180 (zapas 470 m).
4. **Runner**: kierowca `straightrun` (ten sam `StraightRunPilot`), scenariusz `tests/physics/scenarios/straight_0_80_0.json` (solo/empty/laden40, pasma jak `launch_*`/`brake_80_0_*`).
   `Metrics.FirstBrake` = pierwsze narastające zbocze pedału (pedał wciśnięty od t = 0 przy Settle nie jest początkiem hamowania; scenariusze `brake_*` zaczynają od 0 — bez zmian).
5. **Telefon**: `gate12-phone.ps1` — przebiegi `s080_solo_1..3` (70 s), `s080_empty` (80 s), `s080_40t` (120 s), walidacja linii `[AUTOPILOT] straight080 done`;
   `gate12_telemetry.py` — analiza `s080_*` z CSV (t 0–60/0–80, s 0–80, prędkość utrzymania, droga/czas hamowania, MFDD, max opóźnienie, max |poślizg| koła i czas blokady,
   odchyłka boczna w hamowaniu, błąd siodła, przegub) + powtarzalność 0–80 ×3 (±3 %, już nie PROXY). Sprawdzone na CSV z runnera: wyniki = runner.

## Budżet
Brak wpływu na render poza placem pomiarowym: +1 płyta asfaltu (12 tri), 28 pasów farby, 14 znaków — tylko scena `DrivingLab`. Fizyka: pilot = kilkadziesiąt operacji na krok, 0 B GC (test EditMode).
Draws/tris A/B na telefonie: nie mierzone (scena placu, nie świat) — lider przy APK.

## Walidacja (EDYTOR / RUNNER, nie telefon)
Runner .NET, dt 0,01 s, 4 sub-kroki (`artifacts/autopilot-0195/runner/`, wykresy PNG obejrzane):

| wariant | 0–60 | 0–80 | droga 0–80 | v przy hamowaniu | droga 80→0 | MFDD | odchyłka |
|---|---|---|---|---|---|---|---|
| solo 7,5 t | 9,93 s | 13,60 s | 157 m | 80,6 km/h | 35,69 m | 7,46 m/s² | < 1 mm |
| pusty 14,5 t | 13,14 s | 20,54 s | 270 m | 80,4 km/h | 39,49 m | 7,49 m/s² | < 1 mm |
| 40 t | 28,02 s | 47,52 s | 670 m | 79,8 km/h | 40,52 m | 7,04 m/s² | < 1 mm |

Pasma: 0–80 solo 12–32 s / pusty 20–55 s / 40 t 40–95 s (WORKING_VALUE/DERIVED jak `launch_*`); 80→0 solo 32–55 m, zestaw 35–61,2 m (R13 typ 0 N3, SOURCED); MFDD 5–8 m/s² — wszystko w tolerancji.
Powtarzalność runnera 0–80 ×3 (kursy 0/37/113°): 0,00 %; dt 1/50…1/120: ≤ 5 %. Testy .NET 274/274 (w tym nowe `StraightRunTests`).

Unity — **EDYTOR, nie telefon** (Unity 6000.3.28f1 batchmode, scena DrivingLab po regeneracji, PhysX + model gry, timeScale 8, fixedDt 0,01 s;
PlayMode `StraightRunAutopilotTests` 3/3 + `DrivingLabSceneTests` 5/5, EditMode `StraightRunPilotTests` 4/4; CSV + PNG `artifacts/autopilot-0195/playmode/`):

| wariant | 0–60 | 0–80 | droga 0–80 | v przy hamowaniu | droga 80→0 | MFDD | max opóźn. | odchyłka | Δ 0–80 / Δ drogi vs runner |
|---|---|---|---|---|---|---|---|---|---|
| solo ×3 | 10,01 s | 13,67 / 13,67 / 13,67 s | 157 m | 80,6 km/h | 35,62 m | 7,45 m/s² | 7,98 m/s² | < 1 mm | +0,5 % / −0,2 % |
| pusty 14,5 t | 13,24 s | 20,68 s | 272 m | 80,4 km/h | 39,45 m | 7,47 m/s² | 7,69 m/s² | < 1 mm | +0,7 % / −0,1 % |
| 40 t | 28,25 s | 47,80 s | 673 m | 79,8 km/h | 40,78 m | 6,91 m/s² | 7,31 m/s² | 4 mm | +0,6 % / +0,6 % |

Powtarzalność 0–80 ×3 w edytorze: 0,00 % (granica bramki 1: ±3 %). Ten sam CSV z Unity przez `gate12_telemetry.py`: wszystkie kontrole PASS
(max |poślizg| koła w hamowaniu 0,23 solo / 0,17 pusty / 0,21 40 t, czas blokady 0 s, max |dv|/krok 0,08 m/s, błąd siodła ≤ 0,17 mm). 40 t staje na x = 183 m (prosta do 650 m).
Wykresy obejrzane: zmiany biegów 4→12 jak w runnerze, AMT redukuje 12→10 przy utrzymaniu 40 t (gaz PI ~0,37), ABS cykluje poślizg −0,05…−0,15 bez blokady,
nurkowanie kabiny ~3° przy hamowaniu, odbicie przy zatrzymaniu. `tools/telemetry/plot.py`: kolumny tylko-runnera (np. `trailer_a_lat`) jako puste serie, żeby CSV z Unity/telefonu się rysowały.

## Otwarte
- **Pomiar na telefonie** (lider): APK z tej gałęzi + `pwsh scripts/gate12-phone.ps1 -Apk <apk> -UseExistingLock -Only s080_solo_1,s080_solo_2,s080_solo_3,s080_empty,s080_40t`,
  potem `uv run --project tools/perf python scripts/gate12_telemetry.py <OutDir>`; liczby z telefonu do GATE-1/GATE-2 (zastąpić PROXY).
- Scena `DrivingLab.unity` regenerowana w tej gałęzi (`build-lab.ps1 -SkipAudio`) — wspólna scena: decyzja lidera przy scalaniu (alternatywa: regeneracja po scaleniu).
- Hamowanie na mokrym / bez ABS jako wariant autopilota (`speed`, nawierzchnia) — poza zakresem; runner ma `brake_80_0_wet*`.
