# STATUS — hud-redesign-0283 (D40, ADR 0283)

- [krok 1-4] Modele czyste (paleta WCAG, DesktopHudLayout, HudModel, HudPreferences, MenuCommandMap), HUD monitora (pasek na dole, rząd kontrolek, tryb rozszerzony I), lusterka (42 %, regulacja, graybox 7,5 %), ustawienia z zakładkami, menu startowe, Inter SemiBold.
- [krok 5] ADR 0283 (tabela kontrastu), docs/design/HUD-MENU-PC-0283.md + 5 makiet SVG (tools/ui/hud_mockups_0283.py), LICENSES (font-inter-semibold), JAK-GRAC-PC.
- Testy w chmurze: tools/hud-runner 11/11 (20 736 układów), tools/licenses 27/27, Roslyn składnia 28 plików 0 błędów. Unity: NIEuruchomione.
- NASTĘPNY KROK (lider): `pwsh scripts/test.ps1 -Platform EditMode -BuildTarget Win64 -Filter HudRedesign0283Tests` → PlayMode `-Filter PcHudGc0244Tests` → build Windows + visual-qa (komendy w opisie PR).
