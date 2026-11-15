# pc-fix-s23 (live)
Worktree: .claude/worktrees/pc-fix-s23, gałąź pc-fix-s23 (baza origin/int-pc-s23 cc3e1ee90). Bez Unity.

## Krok 1 — scalenia (ZROBIONE)
- 6797fcf5a merge origin/pc-ui-0265 (#131) — czysto.
- 10f9f236f merge origin/pc-settings-0270 (#136) — konflikt UI/BootMenu.cs rozwiązany: wiersz „Ustawienia sterowania | Informacje” w siatce UiFocus (#131) + przycisk „Ekran, grafika, dźwięk” (#136) dodany do siatki pada (#136 P2-2 część 1).
- NASTĘPNY KROK: #131 P1-1 bramka wejścia w `game/Assets/_Project/Input/DriverInputMixer.cs` + test `Tests/EditMode/MenuInputGateTests.cs`; potem `git -C .claude/worktrees/pc-fix-s23 push`.

## Krok 2 — #131 P1-1 bramka wejścia (ZROBIONE, bez Unity = UNVERIFIED kompilacja)
- `DriverInputMixer.MenuOpen` / `MenuGateActive` (+1 próbka po zamknięciu), `IMenuGatedInput.SampleBlocked` w: GamepadDriverInput, KeyboardBindingsDriverInput, KeyboardDriverInput, HidWheelDriverInput; `UiFocus.HasModal`; `DrivingLabBootstrap.Update` ustawia flagę przed `Sample` (+ C/klakson za bramką).
- Test: `Tests/EditMode/MenuInputGateTests.cs` (9 testów, w tym GC=0).
- NASTĘPNY KROK: #136 P1-1 — `QualityTiers.ClearSavedTier`, polityka auto w `Rendering/Runtime/PcTierChoice.cs`, `PcSettingsRuntime.ApplyTier`; test `Tests/EditMode/PcAutoTierTests.cs`; potem `git -C .claude/worktrees/pc-fix-s23 push`.

## Krok 3 — #136 P1-1 „auto” (ZROBIONE, bez Unity = UNVERIFIED kompilacja)
- `Rendering/Runtime/PcTierChoice.cs` (auto: start = nic, menu = ClearSavedTier + autodetekcja bez zapisu; jawny = zapis), `QualityTiers.ClearSavedTier/HasSavedTier/SavedTierKey`, `PcSettingsRuntime.ApplyTier(choice, startup)`, `AutoTier` = autodetekcja #135; usunięty `IGraphicsTierApplier`.
- Test: `Tests/EditMode/PcAutoTierTests.cs` (10). ADR 0270 dopisany.
- NASTĘPNY KROK: P2 osobnymi commitami: #136 P2-1 (`ApplyHudScale` → `UiPreferences.HudScale`), #136 P2-3 (edytor bez vSyncCount/tier), #131 P2-1 (`InputBindingsPanel` UiFocus), #131 P2-3 (ADR 0265), #131 P2-2 (sekcje dotyk/gyro na PC).

## Krok 4 — P2 (ZROBIONE, osobne commity)
- 17ef06145 #136 P2-1, abd9152cc #136 P2-3, 59040804f #136 P2-2 (fokus panelu), 1ba84e200 #131 P2-1, 1249f6171 #131 P2-3 (ADR 0265).
- Otwarte: #131 P2-2/P2-4/P2-5, #136 P2-2 reszta (PcFocusOutline→UiFocus), P2-4, P2-5 — w raporcie.

## Krok 5 — samokontrola (ZROBIONE)
- Kompilacja Roslyn z edytora (csc.dll, bez Unity) na .rsp z main: 16 asmdef, 0 błędów (edytor/player, Android i definicje Win).
- Znaleziony błąd kompilacji #131/#136: CS0118 `Navigation` = przestrzeń `Game.UI.Navigation` → poprawka 5a86b7335.
- Poza Unity refleksją: MenuInputGateTests 8/8 (bez testu GC), PcAutoTierTests 2/10 (reszta natywna).
- Raport: docs/reports/FIX-2026-11-15-pc-fix-s23.md
- NASTĘPNY KROK (int-pc-s23): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter "Game.Tests.MenuInputGateTests;Game.Tests.PcAutoTierTests"` → potem `git merge --no-ff origin/pc-fix-s23`.
