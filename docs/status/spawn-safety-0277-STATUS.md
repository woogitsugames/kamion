# STATUS — spawn-safety-0277 (H13, ADR 0277: bezpiecznik startu)

Gałąź `spawn-safety-0277` od `origin/main` 639da4e54. Agent w chmurze (bez Unity/pwsh). Kod: `game/Assets/_Project/{Gameplay,UI}`,
`World/Runtime/StartClearance.cs` (sortowanie bez alokacji), `World/Import/WorldSceneBuilder.cs` (spawn regułą stref), testy
`Tests/EditMode/StartSearchTests.cs`, `StartClearanceTests.cs` (+2), `Tests/PlayMode/StartSafetyTests.cs`, runner `tools/spawn-runner`.

## Kroki
- [x] 1. `StartSearch` (czysta: strefy między zamknięciami, do przodu → wstecz → NoSpace, zgięcie trasy), `SpawnSafety` na nim
  (sonda fizyki, przepełnienie bufora), `DrivingLabBootstrap` (NoSpace: zestaw wyłączony, powrót do menu; `RestartFromSceneStart`;
  `SetRouteSpawn` → bool), `StartRequest.SetStartFailure`, `BootMenu.ShowNotice`, `StartSafetyTexts` (PL).
- [x] 2. Importer: `StartSearch.BakedSpawnS`. dotnet `tools/spawn-runner`: **13/13 PASS**.
- [x] 3. Testy EditMode/PlayMode napisane (NIEuruchomione — brak Unity). Roslyn: 0 błędów składni; shim fizyki: kompilacja OK.
- [x] 4. ADR `docs/adr/0277-bezpiecznik-startu.md` (tabela P2-2…P2-9).
- [x] 5. PR #141 do main (nie scalony).

## Następny krok (komenda dla lidera)
`pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64` (filtr `StartSearchTests;StartClearanceTests`), potem
`pwsh scripts/test.ps1 -Platform PlayMode -BuildTarget Win64` (filtr `StartSafetyTests;RouteSpawnTests;StartMenuFlowTests`).
.NET: `cd tools/spawn-runner/Tests; dotnet test`.
