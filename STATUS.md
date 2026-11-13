# STATUS phys-0165 (ADR 0165 — podatny kontakt nadwozia 4 Hz / ζ 1, limity penetracji, F1 ≤ 3,5°, IgnoreCollision)
Stan: gotowe. Runner 132/132 (750 checks), dotnet test 266/266, polowanie wywrotek 72 biegi: 0 spadków przez drogę, 0 J zysku,
przegub ≤ 2,77°, szczyt penetracji dachu naczepy 0,131 m przy 40–50 km/h (spoczynek ≤ 0,030 m). Unity EditMode 469/495
(8 FAIL wyłącznie z braku zbudowanych assetów w świeżym worktree). ADR: docs/adr/0165-physics-compliant-body-contact.md.
Zadania w tle: brak.
NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform PlayMode -Filter "CombinationLabTests|KerbStrikeParityTests"` (slot Unity), potem scalenie.
.NET: C:\Users\matma\AppData\Local\Microsoft\dotnet, DOTNET_ROLL_FORWARD=Major.
Gotowe do scalenia: TAK (PlayMode po stronie lidera).
