# drive-feel-s24 — STATUS (agent vehicle-physics, D93 pkt 3)

Gałąź `drive-feel-s24`, worktree `.claude/worktrees/drive-feel-s24` (z main 9ddebe8ab).

## Krok 1 — walidacja PRZED (2026-11-20)
- Runner .NET: **159 scenariuszy, 987 kontroli, wszystkie PASS** (`artifacts/drive-feel-s24/before/summary.md`, CSV + PNG w `before/png`).
- Kluczowe: 0–80 solo 14,06 s, 40 t 47,6 s; 80→0 ABS 39,0 / 41,4 m; 60→0 23,1 / 24,2 m; lane_change_80 przegub < 1°.
- NASTĘPNY KROK: zestaw `input_feel` w runnerze (klawiatura/pad przez SteeringColumn) →
  `dotnet run -c Release --project tools/physics-runner/Runner -- --input-feel artifacts/drive-feel-s24/input-before`

## Krok 2 — sterowanie PC (runner --input-feel), 2026-11-20
- Nowy tryb `physics-runner --input-feel <dir> [--feel <json>]` (te same źródła Controls co Unity). PRZED: trzymany klawisz/gałka przewraca 40 t (CoG 2,6 m) przy 30–90 km/h; stuknięcie 0,1 s = 0,70 m przesunięcia.
- Zmiana (ADR 0312): maxLatAccelMs2 4,0→2,5, minAmplitude 0,05→0,02, progresywny start klawisza 0,35/0,4 s. PO: 0 oderwań kół, ay ≤ 2,53, stuknięcie 0,26 m.
- Fizyka bez zmian: runner po 159/987 PASS, wyniki identyczne.

## Krok 3 — lusterka
- `MirrorTrailerVisibilityTests`: bez obrotu koło ostatniej osi wychodzi z klasy II przy przegubie ≥ 25–30°. Obrót wewnętrznego lusterka klasy II 0,7×(przegub−20°), maks. 25°.
- EditMode pełne: 1339 pass / 1 fail (RegionSelectTests routeLengthM stale bialystok-industrial-c — dane katalogu, nie moje).
- NASTĘPNY KROK: wynik PlayMode (`artifacts/drive-feel-s24/pm-full.log`), potem zrzuty lusterek (player build #2 = przed) i koszt:
  `pwsh scripts/build-windows.ps1 -SkipBuild -Run -Exe <win-build exe> -Scene knyszyn-w -Autopilot route -ExtraPlayerArgs '-shot_every','5'`

## Krok 4 — testy Unity, zrzuty (2026-11-20 ~10:50)
- PlayMode #1: 22 fail — wszystkie NRE w VehicleBody.Initialize (brak zbudowanego prefabu TRAKT w _Generated main, „skip (not built)” przy tworzeniu worktree). W toku: TruckAssetBuilder+TrailerAssetBuilder.BuildBatch w worktree i PlayMode ponownie (`artifacts/drive-feel-s24/pm-full2.log`).
- Koszt lusterek (build #2, knyszyn-w High, GTX 1070, DIAG): 2 rendery/klatkę, CPU średnio 0,99 ms (maks. 1,27), GPU nieraportowane.
- Zrzuty build #2 (przed) knyszyn t=25/45/65 s: `artifacts/drive-feel-s24/mirrors-before/` — rondo dopiero przed maską w t=65.
- NASTĘPNY KROK: zrzuty t=75/82/90 s i A/B pc-metrics `-Extra rq_mirror_off=1`.
- 11:00: Truck BuildBatch w worktree (po skopiowaniu SM_CabInterior_LOD0.fbx z main) → **PlayMode 205 pass / 0 fail / 17 skip**. EditMode 1339/1 fail (RegionSelectTests, dane katalogu — niezależne).
- Zrzuty przed (build #2) rondo Knyszyn t=75/82/90: `artifacts/drive-feel-s24/mirrors-before/`. Po = wymaga buildu z tej gałęzi (lider).
- W toku: pc-metrics A/B rq_mirror_off (`artifacts/drive-feel-s24/pc*`).
- 11:20: koszt lusterek GTX 1070 (A/B rq_mirror_off, 2×2 przebiegi): GPU +0,96/+1,19 ms, CPU główny +1,35/+1,72 ms. Dowody skopiowane do main `artifacts/drive-feel-s24/`.
- **GOTOWE do przeglądu.** NASTĘPNY KROK (lider): build Windows z tej gałęzi → zrzuty „po” na rondzie:
  `pwsh scripts/build-windows.ps1 -SkipBuild -Run -Exe <nowy exe> -Scene knyszyn -Tier High -Autopilot route -Speed 25 -RunSeconds 86 -ShotSeconds 82`
