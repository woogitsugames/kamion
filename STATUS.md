# STATUS — hud-redesign-0283 (D40, ADR 0283)

- [krok 1] Czyste modele (Game.Controls/Display): UiPalette+UiContrast (WCAG), HudPreferences (HUD/lusterka), DesktopHudLayout, HudModel (ostrzeżenia, widoczność, teksty PL), MenuCommandMap; akcja HudDetail (I); regulacja lusterek głównych (RenderTextureMirror), graybox celowanie 7,5 %; font Inter SemiBold (OFL); testy EditMode HudRedesign0283Tests. NIEskompilowane w chmurze.
- [krok 2] tools/hud-runner (dotnet 8 + xunit, źródła z gry): 11/11 zielone (20 736 układów HUD na 9 monitorach). CabScreens.LiveClusters.
- NASTĘPNY KROK: DrivingHud desktop (pasek + rząd kontrolek) → `dotnet test tools/hud-runner/Tests/HudTests.csproj`
