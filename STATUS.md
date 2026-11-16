# STATUS — alt-ui-polish-s23 (D85, D87, §7 int-ui-s23)

- [1] D85: migracja `ui.touchControls` zawsze→auto raz na PC bez ekranu dotykowego (`ui.touchControls.migration`=1), testy EditMode w `PcHudLayoutTests` (TouchMigration_D85_*).
- [2] D87: `BootMenu` tło = `Resources.Load("UI/MenuBackground/menu_bg")` (plik: `game/Assets/_Project/UI/Resources/UI/MenuBackground/menu_bg.png` — dostarcza lider), cover bez rozciągania, scrim 50 %, matowy panel 92 % za blokiem (poza SafeArea); brak pliku = ciemne tło `MenuFallback`. Pary kontrastu menu w `UiPalette.Pairs` (najgorszy przypadek: biały kadr; akcent 4,94:1). Stopka idzie za `m_View.Desktop` (§7 p.2). Test PlayMode `Menu_Backdrop_UnderBlock_AndFooterFollowsFormFactor`.
- NASTĘPNY KROK: §7 p.3 nakładka diagnostyczna (`UI/Diagnostics/DiagnosticsOverlay.cs`).
