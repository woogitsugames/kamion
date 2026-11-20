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
