namespace Game.UI.Settings
{
    /// <summary>Polish text table of the PC settings screen (ADR 0270). One place for every visible string, so a later
    /// localisation table replaces this class without touching the layout.</summary>
    public static class PcSettingsTexts
    {
        public const string Title = "USTAWIENIA: EKRAN, GRAFIKA, DŹWIĘK";
        public const string HintClean = "Zmiany działają po „Zastosuj”.";
        public const string HintDirty = "Są niezastosowane zmiany.";
        public const string MenuButton = "Ekran, grafika, dźwięk";

        public const string SectionDisplay = "EKRAN";
        public const string SectionGraphics = "GRAFIKA";
        public const string SectionInterface = "INTERFEJS";
        public const string SectionAudio = "DŹWIĘK";

        public const string Resolution = "Rozdzielczość";
        public const string Native = "natywna";
        public const string WindowMode = "Tryb okna";
        public static readonly string[] WindowModeLabels = { "okno", "bez ramki", "pełny ekran" };
        public const string Vsync = "Synchronizacja pionowa";
        public static readonly string[] OffOn = { "wyłączona", "włączona" };
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

        public const string Defaults = "Przywróć domyślne";
        public const string Cancel = "Anuluj";
        public const string Apply = "Zastosuj";

        public const string ConfirmTitle = "Zachować nowy tryb ekranu?";
        public const string ConfirmCountdown = "Powrót do poprzedniego za {0} s.";
        public const string ConfirmKeep = "Zachowaj";
        public const string ConfirmRevert = "Przywróć";
    }
}
