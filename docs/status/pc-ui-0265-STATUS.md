# STATUS pc-ui-0265 (H3, ADR 0265 — HUD i UI na monitor)

Agent chmury (bez Unity/pwsh). Gałąź `pc-ui-0265` od `origin/main` ae372b19c.

- [krok 1] Czyste modele: `Input/Display/HudScaleModel.cs` (skala + content 16:9 na ultrawide), `TouchControlsPolicy.cs` (+ `UiPreferences`: `ui.touchControls`, `ui.hudScale`), `MenuNavGrid.cs`; `Camera/MirrorWindowLayout.cs` (okna lusterek wg wysokości, aspekt tekstury). UI: `UiScale` = fasada, `UiViewport` tryb monitora, `HudLayout.HideTouchControls`, `DrivingHud` ukrywa kontrolki dotykowe + zrzuca selekcję HUD, `UiFocus` (EventSystem, ramka fokusu, kolejność nawigacji, Push/Pop właściciela fokusu), BootMenu/ControlSettingsPanel/AboutPanel nawigacja padem/myszą. Testy EditMode `Tests/EditMode/PcHudLayoutTests.cs`.
  NASTĘPNY KROK: kompilacja czystej logiki dotnet (stub UnityEngine) → ADR 0265 → PR.
