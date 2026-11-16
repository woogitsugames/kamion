# STATUS — hud-redesign-0283 (D40, ADR 0283)

- [krok 1] Czyste modele (Game.Controls/Display): UiPalette+UiContrast (WCAG), HudPreferences (HUD/lusterka), DesktopHudLayout, HudModel (ostrzeżenia, widoczność, teksty PL), MenuCommandMap; akcja HudDetail (I); regulacja lusterek głównych (RenderTextureMirror), graybox celowanie 7,5 %; font Inter SemiBold (OFL); testy EditMode HudRedesign0283Tests. NIEskompilowane w chmurze.
- [krok 2] tools/hud-runner (dotnet 8 + xunit, źródła z gry): 11/11 zielone (20 736 układów HUD na 9 monitorach). CabScreens.LiveClusters.
- [krok 3] DrivingHud.Desktop.cs: pasek na dole (prędkość, bieg, 2 obwody), rząd kontrolek (strzałki, kafle ostrzeżeń), wiersz rozszerzony (I), lusterka wg DesktopHudLayout + regulacja; test PlayMode GC paska. UiFonts.Strong.
- [krok 4] PcSettingsPanel: zakładki Grafika/Sterowanie/Dźwięk/Rozgrywka/Lusterka (Q/E, LB/RB, klik), podgląd układu lusterek, wspólne Zastosuj/Anuluj; BootMenu: jeden przycisk Ustawienia (PC), nagłówki SemiBold, odwrócony wybrany segment; paleta w ControlSettings/InputBindings/About/UiFocus. Składnia Roslyn 26 plików: 0 błędów; hud-runner 11/11.
- NASTĘPNY KROK: ADR 0283 + docs/design/HUD-MENU-PC-0283.md + makiety SVG + LICENSES + JAK-GRAC-PC → PR
