# drive-feel-s24 — STATUS (agent vehicle-physics, D93 pkt 3)

Gałąź `drive-feel-s24`, worktree `.claude/worktrees/drive-feel-s24` (z main 9ddebe8ab).

## Krok 1 — walidacja PRZED (2026-11-20)
- Runner .NET: **159 scenariuszy, 987 kontroli, wszystkie PASS** (`artifacts/drive-feel-s24/before/summary.md`, CSV + PNG w `before/png`).
- Kluczowe: 0–80 solo 14,06 s, 40 t 47,6 s; 80→0 ABS 39,0 / 41,4 m; 60→0 23,1 / 24,2 m; lane_change_80 przegub < 1°.
- NASTĘPNY KROK: zestaw `input_feel` w runnerze (klawiatura/pad przez SteeringColumn) →
  `dotnet run -c Release --project tools/physics-runner/Runner -- --input-feel artifacts/drive-feel-s24/input-before`
