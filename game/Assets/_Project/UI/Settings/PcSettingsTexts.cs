namespace Game.UI.Settings
{
    /// <summary>Polish text table of the PC settings screen (ADR 0270, tabs ADR 0283). One place for every visible string, so a
    /// later localisation table replaces this class without touching the layout. No brand names.</summary>
    public static class PcSettingsTexts
    {
        public const string Title = "USTAWIENIA";
        public const string HintClean = "Zmiany działają po „Zastosuj”.";
        public const string HintDirty = "Są niezastosowane zmiany.";
        /// <summary>Help line under the tabs (fixed menu layout, MenuCommandMap).</summary>
        public const string HintKeys = "Q / E lub LB / RB: zakładki · Enter / A: wybór · Esc / B: wróć";
        public const string MenuButton = "Ustawienia";

        // ---- tabs (ADR 0283)
        public static readonly string[] Tabs = { "Grafika", "Sterowanie", "Dźwięk", "Rozgrywka", "Lusterka" };
        public const int TabGraphics = 0, TabControls = 1, TabAudio = 2, TabGameplay = 3, TabMirrors = 4;

        public const string SectionDisplay = "EKRAN";
        public const string SectionGraphics = "GRAFIKA";
        public const string SectionInterface = "INTERFEJS";
        public const string SectionHud = "HUD NA MONITORZE";
        public const string SectionAudio = "GŁOŚNOŚĆ";
        public const string SectionControls = "STEROWANIE";
        public const string SectionMirrorWindows = "OKIENKA LUSTEREK";
        public const string SectionMirrorAdjust = "REGULACJA LUSTEREK";

        public const string Resolution = "Rozdzielczość";
        public const string Native = "natywna";
        public const string WindowMode = "Tryb okna";
        public static readonly string[] WindowModeLabels = { "okno", "bez ramki", "pełny ekran" };
        public const string Vsync = "Synchronizacja pionowa";
        public static readonly string[] OffOn = { "wyłączona", "włączona" };
        public static readonly string[] OffOnPlural = { "wyłączone", "włączone" };
        public const string FpsCap = "Limit klatek";
        public const string FpsNoCap = "bez limitu";
        public const string FpsByVsync = "jak monitor";
        public const string Tier = "Jakość grafiki";
        public static readonly string[] TierLabels = { "auto", "niska", "średnia", "wysoka", "ultra" };
        public const string HudScale = "Skala HUD";
        public const string Units = "Jednostki prędkości";
        public const string UnitsMetric = "km/h";
        public const string VolumeMaster = "Głośność ogólna";
        public const string VolumeEngine = "Silnik";
        public const string VolumeAmbient = "Otoczenie";
        public const string VolumeUi = "Sygnały kabiny";

        // ---- gameplay / HUD
        public const string HudDetail = "Szczegóły HUD";
        public static readonly string[] HudDetailLabels = { "minimalne", "rozszerzone" };
        public const string HudDetailNote = "Klawisz I w jeździe przełącza szczegóły (do zmiany w przypisaniach).";
        public const string CabHud = "HUD w widoku z kabiny";
        public static readonly string[] CabHudLabels = { "auto", "pasek", "tylko ostrzeżenia" };
        public const string CabHudNote = "Auto: gdy w kabinie działają zegary, na ekranie zostają tylko ostrzeżenia i kierunkowskazy.";
        public const string TouchControls = "Kontrolki dotykowe";
        public static readonly string[] TouchControlsLabels = { "auto", "zawsze", "nigdy" };

        // ---- controls
        public const string ControlsWheel = "Kierownica, pedały, kamera…";
        public const string ControlsBindings = "Przypisania klawiszy i pada…";
        public const string ControlsNote = "Klawiatura, pad i kierownica działają jednocześnie. Menu ma stały układ: strzałki / krzyżak, Enter / A, Esc / B.";
        public const string ControlsUnavailable = "Ustawienia sterowania otwierasz z menu startowego.";

        // ---- mirrors
        public const string MirrorWindows = "Okienka lusterek";
        public const string MirrorSize = "Rozmiar";
        public const string MirrorDrop = "Położenie w pionie";
        public const string MirrorInset = "Odsunięcie od krawędzi";
        public const string MirrorYaw = "Na zewnątrz / do środka";
        public const string MirrorPitch = "W dół / w górę";
        public const string MirrorNote = "Klawisz L w jeździe włącza i wyłącza okienka. Regulacja obraca widok obu lusterek głównych.";
        public const string Preview = "Podgląd układu (monitor 16:9)";

        public const string Defaults = "Przywróć domyślne";
        public const string Cancel = "Anuluj";
        public const string Apply = "Zastosuj";

        public const string ConfirmTitle = "Zachować nowy tryb ekranu?";
        public const string ConfirmCountdown = "Powrót do poprzedniego za {0} s.";
        public const string ConfirmKeep = "Zachowaj";
        public const string ConfirmRevert = "Przywróć";
    }
}
