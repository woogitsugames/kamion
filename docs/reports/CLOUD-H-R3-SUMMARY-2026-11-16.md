# Chmura H — runda 3: podsumowanie dla lidera (2026-11-16)

Wszystkie 4 zadania zakończone. **Nic nie scalone.** W chmurze nie było Unity ani Windows: zero kompilacji Unity, zero EditMode/PlayMode w Unity, zero buildów. Uruchomione były tylko testy poza Unity (dotnet z atrapą UnityEngine, pytest, pwsh 7.4 — parsowanie).

| PR | Gałąź @ sha | Zadanie | Testy poza Unity | Werdykt agenta |
|---|---|---|---|---|
| #113 | `jackknife-0228` @ `a84ad5e14` | H11: merge main, P1 (zaokrąglony przód naczepy, prześwit 7 mm → 4,1 cm), wygładzenie FFB przy kontakcie (skok 4,53 → 0,48 N m/krok) | dotnet 319/319, runner 149 scen. / 915 checków PASS, dims_sync OK | TAK |
| #118 | `perf-loop-0244` @ `ae052e54b` | H12: merge main, testy GC wejścia PC i HUD PC 16:9/21:9 | loop-runner 30/30, physics 277/277 | TAK |
| #117 | `controls-0243` @ `0710168df` | H12: merge main, jedno źródło kąta kierownicy PC (`WheelSettings.rangeDeg`), jedna logika lusterek (`MirrorWindowLayout`), naprawiony test GC | controls-runner 13/13 | TAK |
| #141 | `spawn-safety-0277` @ `cd03fb181` | H13 / ADR 0277: `StartSearch` (do przodu, potem wstecz do zamknięcia wjazdowego), brak miejsca → menu z komunikatem; P2-2…P2-9 (P2-7 pominięte) | spawn-runner 13/13 | TAK (warunkowo) |
| #142 | `pc-polish-0276` @ `746c2fd28` | H10 / ADR 0276: nakładka diag. bez kolizji z menu, skrót zawartości `Kamion_Data` (`build-id.json`, menu, log, zip), `Kamion-<region>.cmd` + `Kamion-okno.cmd`, `-Package`, P2 z recenzji | pytest dist 27, pcperf 27, dotnet 38/38 | TAK |

## Kolejność scalania
1. #113 (osobne pliki fizyki)
2. #118, potem #117 (sprawdzone próbnie w obu kolejnościach — bez konfliktów)
3. #141
4. #142

Możliwe konflikty (łańcuch całości NIE był próbnie scalany): #141 i #142 oba zmieniają `UI/BootMenu.cs`; #141 i #117 oba zmieniają `Gameplay/DrivingLabBootstrap.cs`.

## Uwaga przy scalaniu
- #141 zmienia importer (`World/Import/WorldSceneBuilder.cs`): po ponownym imporcie scen regionów punkt startu będzie liczony nową regułą (`StartSearch.BakedSpawnS`).
- #141 dodaje `tools/spawn-runner/` — nie ma go w CI (propozycja: job jak `physics-runner`).
- #142 zmienia `scripts/build-windows.ps1` (normalizacja `-Regions`, `.cmd`, `-Package`, symbole Burst → `artifacts/win/symbols/`).
- Propozycja asmdef: dodać `Unity.InputSystem` do `Game.Tests.EditMode` (test `PcInputGc0244Tests` z #118 dodaje urządzenia przez refleksję — jeśli nie zadziała, test padnie, nie przejdzie po cichu).

## Komendy
```
pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64
pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64
pwsh scripts/build-windows.ps1 -Slot -Regions d67-full -Package
uv run --no-project --with pytest pytest tests/dist tools/pcperf -q
```
Po buildzie: start w każdym regionie przez `Kamion-<region>.cmd`; dwa buildy → różne skróty w `build-id.json`; menu bez zasłoniętych przycisków; komunikat o braku miejsca na start; cofanie z naczepą pełnym skrętem do ogranicznika + ocena FFB; kierownica 900°; lusterka 16:9/21:9.

## Otwarte
- #113: przy 55–60°, 40 t, hamowaniu z 13–20 km/h zostaje otarcie ≤ 0,61 mm po zatrzymaniu → decyzja: wymiary (odstęp kabiny od sworznia) albo tłumienie kołysania ciągnika. ISO 1726 nieczytane (UNVERIFIED). Stałe wygładzenia FFB 0,5 s = WORKING_VALUE do feel testu.
- #141: komunikatu w menu nikt nie widział; kroki i limity szukania (2 m, 200 m) = WORKING_VALUE.
- #142: przesunięcie menu 87 px przy 1080p wyliczone, nie zmierzone na zrzucie.
- #117/#118: koszt i płynność okien lusterek na PC Low niezmierzone; ustawienia kierownicy dotykowej i gyro widoczne na PC; brak panelu kierownicy PC.
- Niezrobione: P2-3 z recenzji #132 (nazwy producentów w `wheel_profiles.json`) — H10 przekazał do H12, H12 tego nie zrobił.
